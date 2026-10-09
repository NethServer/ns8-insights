*** Settings ***
Library     SSHLibrary
Suite Setup       Start the stub insights server
Suite Teardown    Tear down insights

*** Variables ***
# 9100 is node_exporter's port and it already runs on every NS8 test
# node: stay clear of the Prometheus port neighborhood.
${STUB_PORT}        19100
${STUB_URL}         http://127.0.0.1:${STUB_PORT}
${RECORD_FILE}      /tmp/insights-stub.jsonl
${FAKE_SUBSCRIPTION}    ${FALSE}

*** Keywords ***
Start the stub insights server
    Put File    ${CURDIR}/insights-stub.py    /tmp/insights-stub.py
    Execute Command    rm -f ${RECORD_FILE}
    Execute Command
    ...    setsid nohup python3 /tmp/insights-stub.py ${STUB_PORT} ${RECORD_FILE} </dev/null >/tmp/insights-stub.log 2>&1 &
    Wait Until Keyword Succeeds    30s    2s    The stub insights server answers

The stub insights server answers
    ${output}    ${rc} =    Execute Command
    ...    curl -sf http://127.0.0.1:${STUB_PORT}/    return_rc=${True}
    Should Be Equal As Integers    ${rc}    0
    Should Be Equal As Strings     ${output}    ok

Tear down insights
    Execute Command    api-cli run module/${module_id}/configure-module --data '{"enabled":false}'
    IF    ${FAKE_SUBSCRIPTION}
        Execute Command    runagent redis-exec DEL cluster/subscription
    END
    Execute Command    pkill -f insights-stub.py

Run module action
    [Arguments]    ${action}    ${data}=${EMPTY}
    IF    '${data}' == '${EMPTY}'
        ${output}    ${rc} =    Execute Command
        ...    api-cli run module/${module_id}/${action}    return_rc=${True}
    ELSE
        ${output}    ${rc} =    Execute Command
        ...    api-cli run module/${module_id}/${action} --data '${data}'    return_rc=${True}
    END
    Should Be Equal As Integers    ${rc}    0    action ${action} failed: ${output}
    RETURN    ${output}

The collector service is
    [Arguments]    ${expected}
    ${output}    ${rc} =    Execute Command
    ...    runagent -m ${module_id} systemctl --user is-active insights-collector.service
    ...    return_rc=${True}
    Should Be Equal As Strings    ${output}    ${expected}

The injected noise reached Loki
    ${output}    ${rc} =    Execute Command
    ...    logcli query --since 15m --limit 10 --forward --no-labels -q -o raw '{node_id=~".+"} |= "robot synthetic error"'
    ...    return_rc=${True}
    Should Be Equal As Integers    ${rc}    0    logcli failed: ${output}
    Should Contain    ${output}    robot synthetic error

The stub recorded a bundle from the collector
    ${output}    ${rc} =    Execute Command    cat ${RECORD_FILE}    return_rc=${True}
    Should Be Equal As Integers    ${rc}    0    ${RECORD_FILE} was not created: ${output}
    Should Not Be Empty    ${output}
    Should Match Regexp    ${output}    "system_id":\\s*"(?!unknown")[^"]+"
    Should Match Regexp    ${output}    "auth":\\s*"Basic [^"]+"
    # The digit in "error ${i}" masks to <NUM>, but the fixed prefix survives
    # in the template, so the injected noise is still recognisable here.
    Should Contain    ${output}    robot synthetic error

*** Test Cases ***
The collector starts disabled with the default server
    ${output} =    Run module action    get-configuration
    Should Contain    ${output}    "enabled": false
    Should Contain    ${output}    "base_url": "https://insights.nethesis.it"
    Should Contain    ${output}    "active_elsewhere": ""

Enabling without a subscription is refused
    ${rc} =    Execute Command    runagent redis-exec EXISTS cluster/subscription
    Skip If    '${rc}' != '0'    the cluster already has a subscription
    ${output}    ${rc} =    Execute Command
    ...    api-cli run module/${module_id}/configure-module --data '{"enabled":true}'
    ...    return_rc=${True}    return_stderr=${False}
    Should Not Be Equal As Integers    ${rc}    0
    Should Contain    ${output}    subscription_required

Provide a subscription for the test
    ${exists} =    Execute Command    runagent redis-exec EXISTS cluster/subscription
    IF    '${exists}' == '0'
        Execute Command
        ...    runagent redis-exec HSET cluster/subscription provider nsent system_id robot auth_token robot-token
        Set Suite Variable    ${FAKE_SUBSCRIPTION}    ${TRUE}
    END

Inject synthetic noise for the window
    FOR    ${i}    IN RANGE    5
        Execute Command    logger -p daemon.err -t robot-noise robot synthetic error ${i}
    END
    Wait Until Keyword Succeeds    90s    10s    The injected noise reached Loki

Configure insights against the stub
    Run module action    configure-module
    ...    {"enabled":true,"base_url":"${STUB_URL}","verify_tls":false}
    Wait Until Keyword Succeeds    20s    2s    The collector service is    active

get-configuration reports the enabled collector
    ${output} =    Run module action    get-configuration
    Should Contain    ${output}    "enabled": true
    Should Contain    ${output}    "base_url": "${STUB_URL}"
    Should Contain    ${output}    "verify_tls": false
    Should Contain    ${output}    "subscription_configured": true

A single run ships a bundle authenticated with the subscription
    # The daemon may or may not have sent its first window yet: run one
    # collection directly rather than racing it.
    ${output}    ${rc} =    Execute Command
    ...    runagent -m ${module_id} ../bin/insights-collector
    ...    return_rc=${True}
    Should Be Equal As Integers    ${rc}    0    single run failed: ${output}
    Wait Until Keyword Succeeds    60s    5s    The stub recorded a bundle from the collector

--print emits a bundle without shipping
    ${output}    ${rc} =    Execute Command
    ...    runagent -m ${module_id} ../bin/insights-collector --print | python3 -m json.tool
    ...    return_rc=${True}
    Should Be Equal As Integers    ${rc}    0    --print did not emit parseable JSON: ${output}
    Should Contain    ${output}    schema_version
    Should Contain    ${output}    templates

list-findings returns the open findings by default
    ${output} =    Run module action    list-findings
    Should Contain    ${output}    Robot open finding
    Should Not Contain    ${output}    Robot stale finding

list-findings filters by status
    ${output} =    Run module action    list-findings    {"status":"stale"}
    Should Contain    ${output}    Robot stale finding
    Should Not Contain    ${output}    Robot open finding
    ${output} =    Run module action    list-findings    {"status":"all"}
    Should Contain    ${output}    Robot open finding
    Should Contain    ${output}    Robot stale finding

Disabling stops the collector and keeps the server settings
    Run module action    configure-module
    ...    {"enabled":false,"base_url":"${STUB_URL}","verify_tls":false}
    The collector service is    inactive
    ${output} =    Run module action    get-configuration
    Should Contain    ${output}    "enabled": false
    Should Contain    ${output}    "base_url": "${STUB_URL}"
