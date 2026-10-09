# ns8-insights

NethServer 8 module that analyzes the cluster logs and reports the
problems found by the Nethesis insights service.

## Install

Instantiate the module with:

    add-module ghcr.io/nethserver/insights:latest 1

The output of the command will return the instance name.
Output example:

    {"module_id": "insights1", "image_name": "insights", "image_url": "ghcr.io/nethserver/insights:latest"}

## Requirements

- A cluster **subscription**. The insights server accepts data only from
  subscribed machines: the collector authenticates with the `system_id` and
  `auth_token` of the `cluster/subscription` Redis hash. Without a
  subscription the module cannot be enabled, and the Settings page says so.
- A Loki instance. The collector reads the cluster default Loki instance
  (`loki@cluster`), on any node.

## One instance per cluster

The collector reads the logs of the whole cluster, so two enabled instances
would send everything twice. The core can only limit modules per node
(`org.nethserver.max-per-node=1`), so `configure-module` adds the
cluster-wide rule: it refuses to enable an instance while another insights
instance is enabled. `get-configuration` returns the id of that instance in
`active_elsewhere`.

## How it works

The `insights-collector` service follows the cluster log stream from Loki.
It removes likely secrets, masks variable text and folds each line into
counted templates as it arrives. Every 15 minutes it sends what it has
collected to the Nethesis insights service
(`POST <base_url>/logs/v1/bundles`, gzip JSON), where the analysis happens.
The node does no analysis and holds no LLM credential. Quiet windows are not
sent.

The service reads its configuration once at start: `configure-module`
restarts it. When the default Loki instance changes, the collector restarts
and follows the new instance from now.

## Configure

Let's assume that the instance is named `insights1`.

    api-cli run module/insights1/configure-module --data '{
      "enabled": true,
      "base_url": "https://insights.nethesis.it",
      "verify_tls": true
    }'

- `enabled`: run the collector. Required. Refused (validation error
  `subscription_required` or `active_elsewhere`) when the rules above are
  not met.
- `base_url`: root URL of the insights server, with no path. If omitted,
  the current value is kept. Initially
  `https://insights.nethesis.it`.
- `verify_tls`: verify the server TLS certificate. If omitted, the current
  value is kept. Initially `true`. Turn it
  off only for a test server with a self-signed certificate.

Disable it again (the server settings are kept):

    api-cli run module/insights1/configure-module --data '{"enabled": false}'

Read the configuration:

    api-cli run module/insights1/get-configuration

```json
{
  "enabled": true,
  "base_url": "https://insights.nethesis.it",
  "verify_tls": true,
  "status": "active",
  "subscription_configured": true,
  "active_elsewhere": "",
  "last_run": "2026-10-09T12:15:42+00:00"
}
```

`last_run` is the time of the last bundle accepted by the server.

When the subscription ends, the collector is disabled. Enable it again after
a new subscription.

## Findings

The server reviews and publishes findings; this module only reads them:

    api-cli run module/insights1/list-findings --data '{"status": "open"}'

`status` is `open` (default), `stale` or `all`. The action calls
`GET <base_url>/logs/v1/findings` on the node, so the subscription secret
never reaches the browser. The Insights page of the module shows the same
list. New kinds of findings appear only after Nethesis has reviewed them, so
the list can stay empty for a while after the first install.

## Manual execution

The collector is also a plain command. `runagent` runs it in the module
state directory, hence the `../bin/` prefix:

    # See exactly what would leave the node. Nothing is sent.
    runagent -m insights1 ../bin/insights-collector --print

| Flag | Effect |
|------|--------|
| `--print` | build the bundle and write it to stdout instead of sending it; needs no subscription |
| `--max-lines N` | cap on the templates a bundle may carry, divided between module families. Default `500` |
| `--minutes N` | bundle window in minutes. Default `15` |
| `--daemon` | follow the log stream and send a bundle every `--minutes`; this is how the service runs it, only when `INSIGHTS_ENABLED=1` |

Without `--daemon`, a run reads one closed window, sends it and exits.

Check the collector health with:

    runagent -m insights1 journalctl --user -u insights-collector

## Privacy

What leaves the node is masked, deduplicated log templates plus per-module
counts. A template keeps the fixed text of the log messages it stands for,
but variable parts are replaced and identical events collapse into one
counted entry, so no line is sent verbatim. Two passes run as each line is
read: `scrub()` removes likely secrets (`password=`, `token=`, `api_key=`,
`Authorization` headers, long base64 runs, email addresses) and `mask()`
replaces variable text (timestamps, PIDs, addresses, UUIDs and similar).
Each template carries at most two example lines, truncated to 512
characters. This is defence in depth, not a guarantee.

One piece of identifying data is sent on purpose: the **node roster**
(`{node_id, fqdn}` for each node), so a finding can name the machine it
concerns. The FQDN comes from each node's `ns8_node_info` metric, not from
the logs; hostnames inside log lines are still masked.

The module is disabled by default.

## Tests

Collector unit tests:

    pip install -r tests/unit/requirements.txt
    python -m pytest tests/unit

## Uninstall

To uninstall the instance:

    remove-module --no-preserve insights1

## Running tests locally

This module uses the NS8 standard testing infrastructure. For instructions on how to run the test suite locally, refer to the [Running tests locally](https://github.com/NethServer/ns8-github-actions/blob/v1/README.md#running-tests-locally) section of the ns8-github-actions README.

## UI translation

Translated with [Weblate](https://hosted.weblate.org/projects/ns8/).

To setup the translation process:

- add [GitHub Weblate app](https://docs.weblate.org/en/latest/admin/code-hosting.html#code-hosting-github-notifications) to your repository
- add your repository to [hosted.weblate.org](https://hosted.weblate.org) or ask a NethServer developer to add it to ns8 Weblate project
