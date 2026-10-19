#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#
"""Tests for scrub(), sanitize_line() and mask() in insights-collector."""
import re

import pytest

# A broad sample of lines exercised elsewhere in this file, reused here so
# idempotency is checked uniformly rather than ad hoc per case.
IDEMPOTENCY_CASES = [
    "<3> retries 5",
    "usage=12.5%",
    "latency=1.23",
    "retries 5",
    "write=0.34 s",
    "[traefik1] starting",
    "host www.example.com down",
    "source=head.go:12",
    "agent@nethvoice2.service crashed",
    "app.sub.service running",
    "user=alice logged in",
    "user alice logged in",
    "username=bob logged in",
    "country=IT blocked",
    "country_code: IT blocked",
    "(US/24) banned",
    "connect 10.0.0.1:8080",
    "route via 10.0.0.1",
    "addr fe80::1 unreachable",
    "id 550e8400-e29b-41d4-a716-446655440000",
    "checksum deadbeef1234cafe",
    "worker[1234] exited",
    "pid=1234 killed",
    "child (12345) reaped",
    "/tmp/foo/bar missing",
    "/proc/1234/status missing",
    "seen at 2026-09-01T10:15:30Z",
    "seen at 10:15:30",
    "date 01/09/2026",
    "date 01/Sep/2026",
    "",
    "<6> plain line, nothing volatile",
]


@pytest.mark.parametrize("text", IDEMPOTENCY_CASES)
def test_mask_is_idempotent(collector, text):
    once = collector.mask(text)
    assert collector.mask(once) == once


def test_mask_priority_marker_survives(collector):
    assert collector.mask("<3> retries 5") == "<3> retries <NUM>"


def test_mask_priority_marker_not_confused_with_single_digit_rule(collector):
    # A one-digit priority, <3>, must not be caught by the trailing
    # single-digit rule -- it is split off before any rule runs.
    assert collector.mask("<3> ok") == "<3> ok"


@pytest.mark.parametrize("text, expected", [
    ("usage=12.5%", "usage=<PCT>"),
    ("usage=100%", "usage=<PCT>"),
])
def test_mask_percentage(collector, text, expected):
    assert collector.mask(text) == expected


def test_mask_decimal(collector):
    assert collector.mask("latency=1.23") == "latency=<NUM>"


def test_mask_single_digit(collector):
    assert collector.mask("retries 5") == "retries <NUM>"


def test_mask_write_equals_decimal_seconds_regression(collector):
    """write=0.34 s -> write=<NUM> s.

    Regression test for an ordering bug fixed on this branch: masking the
    bare integer "34" before the decimal rule saw it would have left
    "write=0.<NUM> s" behind instead of folding the whole decimal.
    """
    assert collector.mask("write=0.34 s") == "write=<NUM> s"


def test_mask_bracketed_module_instance_number(collector):
    assert collector.mask("[traefik1] starting") == "[traefik] starting"


def test_mask_bracketed_module_instance_number_no_num_leak(collector):
    out = collector.mask("[traefik1] starting")
    assert "<NUM>" not in out


def test_mask_fqdn_to_host(collector):
    assert collector.mask("host www.example.com down") == "host <HOST> down"


@pytest.mark.parametrize("suffix", sorted([
    "go", "py", "service", "socket", "target", "timer", "conf", "log",
]))
def test_mask_source_file_suffix_excluded_from_host_masking(collector, suffix):
    text = "source=head.{0}".format(suffix)
    out = collector.mask(text)
    assert "head.{0}".format(suffix) in out
    assert "<HOST>" not in out


def test_mask_source_file_with_line_number_keeps_filename(collector):
    out = collector.mask("source=head.go:12")
    assert "head.go" in out
    assert "<HOST>" not in out


def test_mask_systemd_templated_unit_untouched(collector):
    assert collector.mask("agent@nethvoice2.service crashed") == \
        "agent@nethvoice2.service crashed"


def test_mask_three_label_systemd_unit_untouched(collector):
    assert collector.mask("app.sub.service running") == "app.sub.service running"


@pytest.mark.parametrize("text, expected", [
    ("user=alice", "user=<USER>"),
    ("user alice", "user <USER>"),
    ("username=bob", "username=<USER>"),
])
def test_mask_user_fields(collector, text, expected):
    assert collector.mask(text) == expected


def test_mask_country_field(collector):
    assert collector.mask("country=IT") == "country=<CC>"


def test_mask_crowdsec_country_ban(collector):
    assert collector.mask("(US/24) banned") == "(<CC>/<NUM>) banned"


def test_mask_non_iso_date(collector):
    assert collector.mask("date 01/09/2026") == "date <DATE>"


def test_mask_non_iso_date_apache_form(collector):
    assert collector.mask("date 01/Sep/2026") == "date <DATE>"


def test_mask_iso8601_timestamp_not_stolen_by_date_rule(collector):
    out = collector.mask("seen at 2026-09-01T10:15:30Z")
    assert out == "seen at <TS>"
    assert "<DATE>" not in out


def test_mask_ipv4(collector):
    assert collector.mask("route via 10.0.0.1") == "route via <IP>"


def test_mask_ipv4_with_port(collector):
    assert collector.mask("connect 10.0.0.1:8080") == "connect <IP>:<PORT>"


def test_mask_ipv6(collector):
    assert collector.mask("addr fe80::1 unreachable") == "addr <IP> unreachable"


def test_mask_uuid(collector):
    out = collector.mask("id 550e8400-e29b-41d4-a716-446655440000")
    assert out == "id <UUID>"


def test_mask_hex_run(collector):
    # The hex rule requires at least one actual digit in the run --
    # "deadbeef" alone (all a-f letters, no digit) is left untouched
    # because it also reads as English prose; a run with a digit in it
    # is what makes this specifically a checksum.
    assert collector.mask("checksum deadbeef1234cafe") == "checksum <HEX>"


def test_mask_pure_letter_hex_run_left_alone(collector):
    assert collector.mask("checksum deadbeefcafebabe") == "checksum deadbeefcafebabe"


def test_mask_pid_brackets(collector):
    assert collector.mask("worker[1234] exited") == "worker[<PID>] exited"


def test_mask_pid_keyword(collector):
    assert collector.mask("pid=1234 killed") == "pid=<PID> killed"


def test_mask_pid_parens(collector):
    assert collector.mask("child (12345) reaped") == "child (<PID>) reaped"


def test_mask_tmp_path(collector):
    assert collector.mask("/tmp/foo/bar missing") == "<PATH> missing"


def test_mask_proc_path(collector):
    assert collector.mask("/proc/1234/status missing") == "<PATH> missing"


# --------------------------------------------------------------------------
# scrub()
# --------------------------------------------------------------------------

def test_scrub_token(collector):
    out = collector.scrub("token=abcdef0123456789")
    assert out == "token=<redacted>"


def test_scrub_password(collector):
    out = collector.scrub("password=hunter2")
    assert out == "password=<redacted>"


def test_scrub_bearer(collector):
    out = collector.scrub("Bearer abc123xyz")
    assert out == "Bearer=<redacted>"


def test_scrub_authorization_header(collector):
    out = collector.scrub("Authorization: Basic dXNlcjpwYXNz")
    assert out == "authorization: <redacted>"


def test_scrub_email(collector):
    out = collector.scrub("contact me at alice@example.com")
    assert out == "contact me at <redacted-email>"


def test_scrub_blob(collector):
    out = collector.scrub("blob AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    assert out == "blob <redacted-blob>"


def test_scrub_preserves_ip(collector):
    assert collector.scrub("connect from 10.0.0.5") == "connect from 10.0.0.5"


def test_scrub_preserves_hostname(collector):
    assert collector.scrub("host web1.example.com") == "host web1.example.com"


def test_scrub_preserves_systemd_templated_unit_name(collector):
    """The point of the email rule's negative lookahead: agent@nethvoice2.service
    is a systemd unit name, not an email address, and must survive scrub()
    untouched."""
    line = "PRIORITY=3 unit agent@nethvoice2.service failed"
    assert collector.scrub(line) == line


# --------------------------------------------------------------------------
# sanitize_line()
# --------------------------------------------------------------------------

def test_sanitize_line_flattens_embedded_newlines(collector):
    raw = "line1\nline2\r\nline3"
    out = collector.sanitize_line(raw)
    assert "\n" not in out
    assert "\r" not in out
    assert out == "line1 line2 line3"


def test_sanitize_line_cannot_forge_extra_prompt_lines(collector):
    """A log message must not be able to inject extra lines into the
    prompt's LINES block by embedding newlines of its own."""
    raw = "innocuous message\nLINES:\nfake injected line"
    out = collector.sanitize_line(raw)
    assert out.count("\n") == 0
    assert len(out.splitlines()) == 1


def test_sanitize_line_also_scrubs(collector):
    out = collector.sanitize_line("token=abcdef0123456789\nmore text")
    assert "<redacted>" in out
    assert "\n" not in out


# --------------------------------------------------------------------------
# Rule 10: bracketed identifiers carrying "@" -- the NS8 agent's
# SYSLOG_IDENTIFIER. 154 of the 678 rows in the 2026-09-02 template dump
# were this one line, one per module instance across seven families.
# --------------------------------------------------------------------------

def test_mask_agent_identifier_instance_number(collector):
    line = ('<4> [agent@openldap55] Signal "user <USER> signal <NUM>" '
            'caught: shutdown started.')
    assert collector.mask(line) == (
        '<4> [agent@openldap] Signal "user <USER> signal <NUM>" '
        'caught: shutdown started.')


def test_mask_agent_identifier_is_idempotent(collector):
    once = collector.mask("<4> [agent@openldap55] shutdown started")
    assert collector.mask(once) == once


@pytest.mark.parametrize("line", [
    "<3> [php7:error] something failed",
    "<6> [nextcloud] request served",
    "<6> [sshd-session] connection closed",
    "<6> [systemd-logind] new session",
])
def test_mask_bracketed_identifiers_without_trailing_digits_unchanged(
        collector, line):
    assert collector.mask(line) == line


def test_mask_agent_identifier_no_num_leak(collector):
    assert "<NUM>" not in collector.mask("<4> [agent@nethvoice63] hello")


# --------------------------------------------------------------------------
# Masking version 5: the leaks measured on the dev fleet's 2026-09-24
# system_templates dump. 6,768 templates were first seen in seven days on
# four clusters; rspamd, kamailio, nethvoice, systemd-coredump, freepbx and
# prometheus minted ~90% of them, each by one volatile token the rules above
# had no shape for. Every case below is a pair of lines the server must see
# as ONE template, run through the same sanitize_line() -> mask() path the
# collector uses, followed by pairs that must stay distinct so a fold cannot
# quietly widen into merging two real conditions.
# --------------------------------------------------------------------------

def _template(collector, raw):
    return collector.mask(collector.sanitize_line(raw))


SAME_TEMPLATE = {
    "rspamd log tag": (
        "(normal) <512a21>; lua; dmarc.lua:411: skip DMARC checks as either SPF or DKIM were not checked",
        "(normal) <BEEC62>; lua; dmarc.lua:411: skip DMARC checks as either SPF or DKIM were not checked",
    ),
    "rspamd task log symbols, message id and recipients": (
        "(normal) <8172f3>; task; rspamd_task_write_log: id: <a1b2c3@mail.example.com>, "
        "qid: <4F2A1B3C9D>, ip: 203.0.113.5, from: <alice@example.com>, "
        "(default: T (reject): [16.20/15.00] [RBL_SPAMHAUS_XBL(4.00){203.0.113.5:from;},"
        "MIME_GOOD(-0.10){text/plain;},ASN(0.00){asn:64500, ipnet:203.0.113.0/24, country:US;}]), "
        "len: 2048, time: 120.5ms, dns req: 42, digest: <0123456789abcdef0123456789abcdef>, "
        "rcpts: <bob@example.org>",
        "(normal) <27c534>; task; rspamd_task_write_log: id: <x9@[198.51.100.7]>, "
        "qid: <9D8C7B6A5F>, ip: 198.51.100.7, from: <carol@example.net>, "
        "(default: T (reject): [9.10/15.00] [BAYES_SPAM(5.10){99.99%;},FROM_NO_DN(0.00){},"
        "R_SPF_SOFTFAIL(0.00){~all;}]), "
        "len: 31337, time: 8.2ms, dns req: 7, digest: <fedcba9876543210fedcba9876543210>, "
        "rcpts: <dave@example.org>,<erin@example.org>",
    ),
    "kamailio connection pointers": (
        "tcp_read_req(): error reading - c: 0x7f388f1a1e40 r: 0x7f388f1a1f68 (-104)",
        "tcp_read_req(): error reading - c: 0x7fba02bc12c0 r: 0x7fba02bc13e8 (-104)",
    ),
    "kamailio scanner payload": (
        "parse_msg(): ERROR: parse_msg: message=<\x17.)vQ\x19\x7f$Um n\x0e\x11Gt\x12,mw`>&\x07jW^>",
        "parse_msg(): ERROR: parse_msg: message=<OPTIONS sip:100@198.51.100.2 SIP/2.0 x>",
    ),
    "kamailio via echo": (
        "parse_via(): parsing via on: <SIP/2.0/UDP ${SADDR}:${SPORT};branch=${RAND_ALPHA=12}>",
        "parse_via(): parsing via on: <SIP/2.0/TCP 203.0.113.9:5060;rport;alias>",
    ),
    "kamailio bad header echo": (
        "parse_headers(): bad header field [Max-Forwards: abc]",
        "parse_headers(): bad header field [Via: SIP/2.0/UDP 203.0.113.9:5060;branch=z9hG4bK1]",
    ),
    "kamailio dialog call id and tags": (
        "next_state_dlg(): bogus event 7 in state 3 for dlg 0x7f9f6f4688a0 [1234:5678] "
        "with clid 'as0c6d13ea' and tags 'eyfth03zq0' ''",
        "next_state_dlg(): bogus event 7 in state 3 for dlg 0x7f5b8dc3edd0 [4321:8765] "
        "with clid '0_2883338957@198.51.100.3' and tags '3mxwl80x43' '1upkkhip3e'",
    ),
    "kamailio route param": (
        "dlg_onroute(): unable to find dialog for BYE with route param '06b.1f2' [12:34] "
        "and call-id 'eyfth03zq0'",
        "dlg_onroute(): unable to find dialog for BYE with route param '0fc.25a2' [56:78] "
        "and call-id '9btc9azv14'",
    ),
    "kamailio dialog ids with colon and equals separators": (
        "dlg_ontimeout(): dlg timeout - callid: 'as5894ada2' tags: 'eyfth03zq0' '1upkkhip3e' ostate: 3",
        "dlg_ontimeout(): dlg timeout - callid: '4f2a-y74hmw6fk8vf' tags: 'x1' '204xpkwerl' ostate: 3",
    ),
    "kamailio dialog identification elements": (
        "dlg_onroute(): dialog identification elements are callid='abc@198.51.100.1:5060'/12, "
        "caller tag='as5894ada2'/10, callee tag='3mxwl80x43'/10",
        "dlg_onroute(): dialog identification elements are callid='zz9@198.51.100.2:5060'/12, "
        "caller tag='as7a0138cf'/10, callee tag='1upkkhip3e'/10",
    ),
    "kamailio script route call id": (
        "(route[DISPATCHER_FAILURE]) 4f2a9c-0fiovboutc5d INVITE-12 - DISPATCHER_FAILURE",
        "(route[DISPATCHER_FAILURE]) 91be07-1f15gvpl0byb INVITE-12 - DISPATCHER_FAILURE",
    ),
    "user name after a colon": (
        "ws disconnected undefined - reason: client namespace disconnect (user: alessandro)",
        "ws disconnected undefined - reason: client namespace disconnect (user: centralino_2)",
    ),
    "SIP call id": (
        "(route[DISPATCHER_FAILURE]) 0_955055618@198.51.100.4 INVITE-12 - DISPATCHER_FAILURE",
        "(route[DISPATCHER_FAILURE]) 6_1673866655@198.51.100.4 INVITE-12 - DISPATCHER_FAILURE",
    ),
    "socket.io session id": (
        "- warn: [com_nethcti_ws] new ws connection from undefined (sid: YErRenv1B0aW3SWcAAAP)",
        "- warn: [com_nethcti_ws] new ws connection from undefined (sid: -_as9JW_vU9SxxmEAABr)",
    ),
    "nethcti user and session": (
        '- warn: [com_nethcti_ws] sent authorized successfully ("authe_ok") to "int207" '
        "undefined with sid x3yqT7yLCdqBoa8TAAA3",
        '- warn: [com_nethcti_ws] sent authorized successfully ("authe_ok") to "cristian" '
        "undefined with sid 9hsy-I-lQPJnEJsoAAIg",
    ),
    "nethcti middleware requester": (
        "[ERROR][PROXY][V] request failed method=POST requester=segreteria1 auth=jwt-session",
        "[ERROR][PROXY][V] request failed method=POST requester=mario auth=jwt-session",
    ),
    "HTTP request body": (
        '[INFO][AUTH] authorization success for user bob POST /phonebook/search '
        '{"company":"ACME","name":"Mario Rossi","type":"public"}',
        '[INFO][AUTH] authorization success for user eve POST /phonebook/search '
        '{"cellphone":"3331234567","name":"Anna"}',
    ),
    "tancredi provisioning data": (
        'Rendered template "yealink.tmpl" with data: {"mac":"80-5E-0C-11-22-33","userpw":"x"}',
        'Rendered template "yealink.tmpl" with data: {"mac":"00-15-65-AA-BB-CC","ringtone":"1"}',
    ),
    "rsyslog truncated message echo": (
        "message too long (8193) with configured size 8096, begin of message is: "
        '{"reqId":"aaRFGmVuk62xp4UU3pfk","level":2}',
        "message too long (9000) with configured size 8096, begin of message is: "
        "Received alert: firing",
    ),
    "nextcloud request id": (
        '[nextcloud][webdav][12] {"reqId":"WC6GaI4YpP8uDe5M1oTE","app":"webdav"}',
        '[nextcloud][webdav][12] {"reqId":"SG9hgn9aFtQ48mCkEf2D","app":"webdav"}',
    ),
    "prometheus block ulids and source count": (
        'msg="compact blocks" count=3 ulid=01M33358K8BBEBASPBXB2EZ8PN '
        'sources="[01M327PAHVYF17PQA27D1MGPJN 01M32EJ1STZJ7NCRVK1J56KJJM 01M32NDS2CS1FJK2H3Q4TGV4YA]"',
        'msg="compact blocks" count=3 ulid=01M2RSJREKFGRV6BA05VZME4KR '
        'sources="[01M2QY3T08X3QJ11Q4SJCX50ST 01M2R4ZH84TJ0YKGSWZK2AV8X5]"',
    ),
    "apache ctime timestamp": (
        "[Fri Sep 19 10:15:30.123456 2026] [php7:notice] [pid 12:tid 34] AH0001: notice",
        "[Mon Oct  6 23:01:02.654321 2026] [php7:notice] [pid 56:tid 78] AH0001: notice",
    ),
    "tomcat date": (
        "24-Sep-2026 10:15:30.123 WARNING [Smack Cached Executor] Roster not loaded",
        "01-Oct-2026 08:00:00.001 WARNING [Smack Cached Executor] Roster not loaded",
    ),
    "coredump stack trace": (
        "Process 4321 (node) of user 1001 dumped core. Stack trace of thread 17: "
        "#0 0x0000555b62992e37 n/a (/usr/bin/node + 0x1250e37) "
        "#1 0x00007f85d6c359ca n/a (/lib64/libc.so.6 + 0x1c9ca) "
        "ELF object binary architecture: AMD x86-64",
        "Process 9876 (node) of user 1001 dumped core. Stack trace of thread 3: "
        "#0 0x000055922cc61ba5 n/a (/usr/bin/node + 0xaf4ba5) "
        "ELF object binary architecture: AMD x86-64",
    ),
    "kernel code bytes": (
        "Code: 48 89 e5 cc cc cc cc cc 0f 1f 44 00 00 <fa> e9 3f 00 00 00",
        "Code: 0f 1f 00 f3 9a 2b 90 90 90 eb 04 <0f> 0b 66 90",
    ),
    "PHP truncated stack arguments": (
        "#3 /usr/share/webtop/Backend.php(1203): WT\\DAV\\CalDAV\\Backend->createCalendar("
        "'principals/tomm...', 'A1B2C3D4-F6F0-4...', Array)",
        "#3 /usr/share/webtop/Backend.php(1203): WT\\DAV\\CalDAV\\Backend->createCalendar("
        "'principals/elen...', 'B9C8D7E6-0D3E-4...', Array)",
    ),
}


@pytest.mark.parametrize("name", sorted(SAME_TEMPLATE))
def test_v5_volatile_lines_fold_to_one_template(collector, name):
    first, second = SAME_TEMPLATE[name]
    assert _template(collector, first) == _template(collector, second)


DISTINCT_TEMPLATE = {
    "rspamd action is signal": (
        "(normal) <8172f3>; task; rspamd_task_write_log: id: <a@example.com>, "
        "(default: T (reject): [16.20/15.00] [MIME_GOOD(-0.10){text/plain;}]), len: 20",
        "(normal) <8172f3>; task; rspamd_task_write_log: id: <a@example.com>, "
        "(default: F (no action): [1.20/15.00] [MIME_GOOD(-0.10){text/plain;}]), len: 20",
    ),
    "coredump process name is signal": (
        "Process 4321 (node) of user 1001 dumped core. Stack trace of thread 1: #0 0x1 n/a",
        "Process 4321 (asterisk) of user 1001 dumped core. Stack trace of thread 1: #0 0x1 n/a",
    ),
    "kamailio parser function is signal": (
        "parse_msg(): ERROR: parse_msg: message=<junk>",
        "parse_via(): parsing via on: <junk>",
    ),
    "http path before a body is signal": (
        'authorization success for user bob POST /phonebook/search {"name":"x"}',
        'authorization success for user bob POST /history/interval {"name":"x"}',
    ),
    "nextcloud exception after the request id is signal": (
        '{"reqId":"WC6GaI4YpP8uDe5M1oTE","message":"NotFound"}',
        '{"reqId":"WC6GaI4YpP8uDe5M1oTE","message":"ServiceUnavailable"}',
    ),
    "apache log level is signal": (
        "[Fri Sep 19 10:15:30.123456 2026] [php7:notice] AH0001: notice",
        "[Fri Sep 19 10:15:30.123456 2026] [php7:error] AH0001: notice",
    ),
}


@pytest.mark.parametrize("name", sorted(DISTINCT_TEMPLATE))
def test_v5_folds_keep_distinct_conditions_apart(collector, name):
    first, second = DISTINCT_TEMPLATE[name]
    assert _template(collector, first) != _template(collector, second)


@pytest.mark.parametrize("text", [
    "nethvoice-proxy10 restarted",
    "arch x86_64 kernel",
    "Yealink SIP-T31G provisioning",
    "UTF-8 conversion done",
    "PasswordAuthentication disabled",
    "ContainerCreateError while starting",
    "agent@nethvoice2.service crashed",
    # Measured false positives of the first draft, which had no
    # class-switch floor: an exception class and two phone model names.
    "InvalidAsn1Error raised by decoder",
    "model fanvil-H2U-senzaled provisioned",
    "model yealink-T53-headset_speaker provisioned",
])
def test_v5_opaque_id_rule_leaves_ordinary_tokens_alone(collector, text):
    assert "<ID>" not in _template(collector, text)


@pytest.mark.parametrize("name", sorted(SAME_TEMPLATE))
def test_v5_folds_are_idempotent(collector, name):
    for raw in SAME_TEMPLATE[name]:
        once = _template(collector, raw)
        assert collector.mask(once) == once


def test_v5_repeated_placeholders_collapse_but_distinct_ones_do_not(collector):
    assert collector.mask("rcpts: <<redacted-email>>,<<redacted-email>>,<<redacted-email>>") == \
        "rcpts: <<redacted-email>>"
    assert collector.mask("from <IP> to <HOST>") == "from <IP> to <HOST>"



# --------------------------------------------------------------------------
# Masking version 6: the leaks measured on the dev fleet's 2026-09-28
# system_templates dump, among the 1,522 novel lines seen on no other
# system. Same shape as the version 5 section above: pairs that must mask
# to ONE template, pairs that must stay apart.
# --------------------------------------------------------------------------

SNOM_REQUEST = (
    "<3> [nethvoice12] [2026-09-28 10:00:00] tancredi.INFO: Serving request from "
    "10.0.0.5 Mozilla/4.0 (compatible; snomD713-SIP 10.4.5.6 10.4.5-v10-rc2 "
    "(Mar 12 2025 - 10:11:12) 000413E59FB4 SXM:0 UXM:0 UXMC:0): "
    "http://pbx.example.com:80/provisioning/a1b2c3d4e5f6a7b8/000413e59fb4.xml "
    "(00-04-13-E5-9F-B4)"
)

SAME_TEMPLATE_V6 = {
    "snom provisioning request, another model and firmware": (
        SNOM_REQUEST,
        "<3> [nethvoice12] [2026-09-28 10:05:00] tancredi.INFO: Serving request from "
        "10.0.0.8 Mozilla/4.0 (compatible; snom725-SIP 10.4.5.9 10.1.54.13 "
        "000413A0CB21 SXM:0 UXM:0): "
        "http://pbx.example.com:80/provisioning/a1b2c3d4e5f6a7b8/snom725.htm "
        "(00-04-13-A0-CB-21)",
    ),
    "provisioning request, snom and fanvil": (
        SNOM_REQUEST,
        "<3> [nethvoice12] [2026-09-28 10:06:00] tancredi.INFO: Serving request from "
        "10.0.0.6 Fanvil W610W 2.12.18 0c383e6b0cff: "
        "http://pbx.example.com:80/provisioning/a1b2c3d4e5f6a7b8/0c383e6b0cff.cfg "
        "(0C-38-3E-6B-0C-FF)",
    ),
    "provisioning request, snom and yealink with its MAC in the UA": (
        SNOM_REQUEST,
        "<3> [nethvoice12] [2026-09-28 10:07:00] tancredi.INFO: Serving request from "
        "10.0.0.7 Yealink SIP-T31P 124.86.0.40 80:5e:c0:12:34:56: "
        "http://pbx.example.com:80/provisioning/a1b2c3d4e5f6a7b8/y000000000123.cfg "
        "(80-5E-C0-12-34-56)",
    ),
    "invalid token request": (
        "[2026-09-28 10:00:00] tancredi.WARNING: Invalid token request from 10.0.0.7 "
        "Yealink W70B 146.85.0.20 80:5e:c0:12:34:56: http://10.0.0.1/provisioning/x9/805ec0123456.cfg",
        "[2026-09-28 10:01:00] tancredi.WARNING: Invalid token request from 10.0.0.9 "
        "Fanvil W620W 2.14.0 0c383e6b0d00: http://10.0.0.1/provisioning/y7/0c383e6b0d00.cfg",
    ),
    "RFC 1123 date, another weekday": (
        "Sun, 21 Sep 2026 10:11:12 GMT sequelize deprecated Use sequelize.fn / "
        "sequelize.col to construct attributes at <anonymous>:null:null",
        "Fri, 26 Sep 2026 23:00:59 GMT sequelize deprecated Use sequelize.fn / "
        "sequelize.col to construct attributes at <anonymous>:null:null",
    ),
    "rspamd map check, weekdays and a tag that is not hex": (
        "(controller) <qbq3yk>; map; http_map_finish: data is not modified for server "
        "maps.rspamd.com, next check at Mon, 22 Sep 2026 10:11:12 GMT "
        "(http cache based: Mon, 22 Sep 2026 10:11:12 GMT)",
        "(controller) <5eb7e3>; map; http_map_finish: data is not modified for server "
        "maps.rspamd.com, next check at Sat, 27 Sep 2026 08:00:00 GMT "
        "(http cache based: Sat, 27 Sep 2026 08:00:00 GMT)",
    ),
    "RFC 2822 date with an offset": (
        "Received: from mx.example.com; Mon, 22 Sep 2026 10:11:12 +0200",
        "Received: from mx.example.com; Thu, 1 Oct 2026 07:00:00 -0500",
    ),
    "firmware build date": (
        "firmware snom 10.1.54.13 (Mar 12 2025 - 10:11:12) loaded",
        "firmware snom 10.1.54.13 (Jul  3 2024 - 23:59:01) loaded",
    ),
    "date with the month as a word": (
        "certificate valid until Sep 21, 2026",
        "certificate valid until Thursday, 1 October 2026",
    ),
    "syslog timestamp without a weekday": (
        "Sep 21 10:11:12 pbx asterisk[123]: reload",
        "Oct  3 01:02:03 pbx asterisk[123]: reload",
    ),
    # Leak 4 turned out not to be a rule miss: v5's rule 6b masks both of
    # these, and every unmasked pointer in the 2026-09-28 dump came from one
    # system still running a masking version 4 collector. Pinned here in the
    # exact shapes the dump holds so a later rule cannot reopen them.
    "kamailio dialog pointer before a bracket": (
        "next_state_dlg(): bogus event 5 in state 3 for dlg 0x7f43109d5b80 [1234:5678] "
        "with clid '1_1120169619@198.51.100.1' and tags 'abc' 'def'",
        "next_state_dlg(): bogus event 5 in state 3 for dlg 0x7f3b5aa8f940 [4321:8765] "
        "with clid '550e8400-e29b-41d4-a716-446655440000' and tags 'ghi' ''",
    ),
    "bare pointer token": (
        "tcp_read_req(): error reading - c: 0x7fce0d6cf280 r: 0x7fce0d6cf3a8 (-104)",
        "tcp_read_req(): error reading - c: 0x7f4310957b90 r: 0x7f4310957cb8 (-104)",
    ),
    "bare pointer at the end of a line": (
        "#FailureMessage Object: 0x7ffcf4fe0a70",
        "#FailureMessage Object: 0x7ffd593e4a50",
    ),
    "pointers in parentheses": (
        "get_body(): failed to locate end of headers (0x55b49809ad40 0x55b49809aeb1 - 12 34 [])",
        "get_body(): failed to locate end of headers (0x5601aa000010 0x5601aa0000f1 - 56 78 [])",
    ),
}


@pytest.mark.parametrize("name", sorted(SAME_TEMPLATE_V6))
def test_v6_volatile_lines_fold_to_one_template(collector, name):
    first, second = SAME_TEMPLATE_V6[name]
    assert _template(collector, first) == _template(collector, second)


@pytest.mark.parametrize("name", sorted(SAME_TEMPLATE_V6))
def test_v6_folds_are_idempotent(collector, name):
    for raw in SAME_TEMPLATE_V6[name]:
        once = _template(collector, raw)
        assert collector.mask(once) == once


def test_v6_provisioning_request_template(collector):
    assert _template(collector, SNOM_REQUEST) == (
        "<3> [nethvoice] [<TS>] <HOST>: Serving request from <IP> <UA>: "
        "http://<HOST>:<NUM>/provisioning/<PATH> (<MAC>)"
    )


DISTINCT_TEMPLATE_V6 = {
    "the provisioning path's first segment is signal": (
        SNOM_REQUEST,
        SNOM_REQUEST.replace("/provisioning/", "/tancredi/"),
    ),
    "a date in a different place is a different line": (
        "next check at Mon, 22 Sep 2026 10:11:12 GMT (timer based)",
        "next check at Mon, 22 Sep 2026 10:11:12 GMT (http cache based)",
    ),
}


@pytest.mark.parametrize("name", sorted(DISTINCT_TEMPLATE_V6))
def test_v6_folds_keep_distinct_conditions_apart(collector, name):
    first, second = DISTINCT_TEMPLATE_V6[name]
    assert _template(collector, first) != _template(collector, second)


# A MAC names one device, so like an address it must never reach a stored
# template -- in any of the shapes daemons print it, and in particular not
# as the "<DATE>-E5-9F-B4" half-address the numeric-date rule used to leave.
MAC_LINES = [
    "(00-04-13-E5-9F-B4)",
    "Serving request from 10.0.0.5 Mozilla/4.0 (compatible): http://h/p (00-04-13-E5-9F-B4)",
    "dnsmasq-dhcp: DHCPACK(eth0) 10.0.0.5 00:04:13:e5:9f:b4 snom",
    "eth0: link up, HWaddr 0C:38:3E:6B:0C:FF.",
    "mac:80:5e:c0:12:34:56: unknown",
    '{"mac":"80-5E-0C-11-22-33","model":"T31P"}',
    "all digits 00-15-65-12-34-56 here",
    "cisco form 0004.13e5.9fb4 learned",
]


@pytest.mark.parametrize("raw", MAC_LINES)
def test_v6_a_mac_address_never_survives_masking(collector, raw):
    out = _template(collector, raw)
    assert "<MAC>" in out
    # No two adjacent octets of any MAC, in any separator, are left.
    assert not re.search(r'[0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}', out), out
    assert not re.search(r'[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}', out), out
    assert "<DATE>-" not in out


@pytest.mark.parametrize("text,kept", [
    # kamailio's module marker and a JSON parser's complaint keep their
    # angle-bracketed words: the rspamd tag rule needs ") " before and ";"
    # after.
    ("ERROR: <core> [core/tcp_read.c:12]: tcp_read_req(): error", "<core>"),
    ("Unexpected token <script> in JSON at position 0", "<script>"),
    # A clock is not a MAC, and neither is an IPv6 address.
    ("reload at 10:11:12 done", "<TS>"),
    ("addr 2001:db8::1 unreachable", "<IP>"),
])
def test_v6_new_rules_leave_lookalikes_alone(collector, text, kept):
    out = _template(collector, text)
    assert kept in out
    assert "<MAC>" not in out


def test_v6_templates_carry_no_wildcards(collector):
    """<*> used to be written by cluster_templates(), never by mask(); with
    it gone nothing in the collector produces one."""
    assert not hasattr(collector, "cluster_templates")




# --------------------------------------------------------------------------
# Masking version 7: the unquoted SIP Call-ID. nethvoice-proxy's auth
# failure line logs it twice, as kamailio's "$ci $rm-$cs" prefix and in a
# callid= field, and some user agents mint it as <hex>-<random letters>:
# the hex was masked, the letters were not, one template per call.
# --------------------------------------------------------------------------

def _authfail(callid, method="INVITE"):
    return (
        "<3> [kamailio] 12(345) WARNING: <script>: [SECURITY-AUTHFAIL] "
        f"{callid} {method}-1 - event=auth_failure method={method} status=401 "
        f"src_ip=203.0.113.7 user=1001 callid={callid}"
    )


# As the server stores them today, under masking version 6.
STORED_INVITE_AUTHFAIL = (
    "<3> [kamailio] <NUM>(<PID>) WARNING: <script>: [SECURITY-AUTHFAIL] "
    "<HEX>-dseadsfjqujt INVITE-<NUM> - event=auth_failure method=INVITE "
    "status=<NUM> src_ip=<IP> user=<HEX> callid=<HEX>-dseadsfjqujt"
)
STORED_REGISTER_AUTHFAIL = (
    "<3> [kamailio] <NUM>(<PID>) WARNING: <script>: [SECURITY-AUTHFAIL] "
    "<ID>@<IP> REGISTER-<NUM> - event=auth_failure method=REGISTER "
    "status=<NUM> src_ip=<IP> user=<USER> callid=<ID>@<IP>"
)


def test_v7_stored_invite_call_id_tail_is_masked(collector):
    assert collector.mask(STORED_INVITE_AUTHFAIL) == (
        "<3> [kamailio] <NUM>(<PID>) WARNING: <script>: [SECURITY-AUTHFAIL] "
        "<ID> INVITE-<NUM> - event=auth_failure method=INVITE "
        "status=<NUM> src_ip=<IP> user=<USER> callid=<ID>"
    )


def test_v7_stored_register_line_is_unchanged(collector):
    assert collector.mask(STORED_REGISTER_AUTHFAIL) == STORED_REGISTER_AUTHFAIL


def test_v7_raw_register_line_keeps_its_template(collector):
    out = _template(collector, _authfail("MzM4ZjNhYTk5YjE4@192.0.2.4", "REGISTER"))
    assert out == STORED_REGISTER_AUTHFAIL


def test_v7_invite_lines_differing_only_in_the_tail_are_one_template(collector):
    first = _template(collector, _authfail("3a4f9c2d81e07b6a-dseadsfjqujt"))
    second = _template(collector, _authfail("3a4f9c2d81e07b6a-qpwmzkrtxbvn"))
    assert first == second
    assert "<ID> INVITE-<NUM>" in first
    assert first.endswith("callid=<ID>")
    assert "dseadsfjqujt" not in first


def test_v7_call_id_prefix_without_a_field_is_masked(collector):
    stored = "<3> [kamailio] <NUM>(<PID>) ERROR: <script>: fevigort37u6sbhqkm2p9396@<IP> INVITE-<NUM> Malformed SIP request"
    expected = "<3> [kamailio] <NUM>(<PID>) ERROR: <script>: <ID> INVITE-<NUM> Malformed SIP request"
    assert collector.mask(stored) == expected
    assert _template(collector, stored.replace("<NUM>(<PID>)", "12(345)")
                     .replace("<IP>", "203.0.113.7")
                     .replace("INVITE-<NUM>", "INVITE-1")) == expected


@pytest.mark.parametrize("text, kept", [
    # A stable suffix of a masked id, with no callid= field and no SIP
    # method after it.
    ("restic snapshot 3fa9c2d8e1b7-infra saved", "<HEX>-infra"),
    # A label right before a method: no digit, no placeholder.
    ("[SECURITY-AUTHFAIL] INVITE-1 - event=auth_failure", "[SECURITY-AUTHFAIL] INVITE-<NUM>"),
    # A hyphenated word in a line that also has a Call-ID.
    (_authfail("3a4f9c2d81e07b6a-dseadsfjqujt").replace("WARNING:", "WARNING: re-auth"),
     "WARNING: re-auth <script>: [SECURITY-AUTHFAIL] <ID> INVITE-<NUM>"),
])
def test_v7_hyphenated_words_are_left_alone(collector, text, kept):
    assert kept in _template(collector, text)


@pytest.mark.parametrize("raw", [
    _authfail("3a4f9c2d81e07b6a-dseadsfjqujt"),
    _authfail("MzM4ZjNhYTk5YjE4@192.0.2.4", "REGISTER"),
    STORED_INVITE_AUTHFAIL,
    STORED_REGISTER_AUTHFAIL,
    "fevigort37u6sbhqkm2p9396@203.0.113.7 INVITE-1 Malformed SIP request",
])
def test_v7_call_id_fold_is_idempotent(collector, raw):
    once = _template(collector, raw)
    assert collector.mask(once) == once


# --------------------------------------------------------------------------
# Masking version 8: a user field with a prefix. postfix logs the account
# of a failed SASL login as "sasl_username=name"; the "_" before "username"
# is a word character, so rule 13 never matched and every account tried by
# a password-guessing attack was a new template with the name in clear.
# A user field whose value an earlier rule masked (<HOST>, <HEX>) now folds
# to <USER> as well.
# --------------------------------------------------------------------------

def _sasl_fail(account):
    return ("<4> [postfix/smtpd] warning: unknown[203.0.113.7]: SASL LOGIN "
            "authentication failed: (reason unavailable), sasl_username=" + account)


SASL_FAIL_TEMPLATE = (
    "<4> [postfix/smtpd] warning: unknown[<IP>]: SASL LOGIN "
    "authentication failed: (reason unavailable), sasl_username=<USER>"
)


@pytest.mark.parametrize("account", [
    "marzio", "clienti", "mail.example.com", "deadbeef1234", "marzio@example.com",
])
def test_v8_sasl_username_is_masked(collector, account):
    assert _template(collector, _sasl_fail(account)) == SASL_FAIL_TEMPLATE


def test_v8_stored_sasl_username_is_masked(collector):
    stored = SASL_FAIL_TEMPLATE.replace("<USER>", "marzio")
    assert collector.mask(stored) == SASL_FAIL_TEMPLATE
    assert collector.mask(SASL_FAIL_TEMPLATE) == SASL_FAIL_TEMPLATE
    hidden = SASL_FAIL_TEMPLATE.replace("=<USER>", "=<HOST>")
    assert collector.mask(hidden) == SASL_FAIL_TEMPLATE


@pytest.mark.parametrize("text, expected", [
    ("db_user=alice", "db_user=<USER>"),
    ("sasl_username: bob", "sasl_username: <USER>"),
    ("user=<HEX>", "user=<USER>"),
    ("(user: <HOST>)", "(user: <USER>)"),
    ("user=<HOST>, ok", "user=<USER>, ok"),
    ("user=<USER><HOST>", "user=<USER>"),
    ("user=<USER> from <HOST>", "user=<USER> from <HOST>"),
    # Still a whole field name: no letter or digit right before "user".
    ("ruser=alice", "ruser=alice"),
])
def test_v8_prefixed_user_fields(collector, text, expected):
    assert collector.mask(text) == expected


@pytest.mark.parametrize("raw", [
    _sasl_fail("mail.example.com"),
    _sasl_fail("marzio@example.com"),
    "(user: <HOST>)",
    "user=<HEX>, ok",
])
def test_v8_user_fold_is_idempotent(collector, raw):
    once = _template(collector, raw)
    assert collector.mask(once) == once


# --------------------------------------------------------------------------
# Masking version 9: a nethcti account name with spaces. "user maria
# maria rossi is not configured" kept every word after the first, so
# each person's full name reached the server and made its own template.
# --------------------------------------------------------------------------

NOT_CONFIGURED = (
    "<3> [nethvoice] 2026-10-14T08:00:00.000Z - warn: [plugins_rest/authentication] "
    "send HTTP 401 response to 203.0.113.7:51234 with message "
    "\"user {} is not configured\""
)
NOT_CONFIGURED_TEMPLATE = (
    "<3> [nethvoice] <TS> - warn: [plugins_rest/authentication] "
    "send HTTP <NUM> response to <IP>:<PORT> with message "
    "\"user <USER> is not configured\""
)


@pytest.mark.parametrize("account", ["anna maria rossi", "maria rossi", "rossi", "201"])
def test_v9_user_not_configured_is_masked(collector, account):
    assert _template(collector, NOT_CONFIGURED.format(account)) == NOT_CONFIGURED_TEMPLATE


@pytest.mark.parametrize("stored", [
    "warn: [plugins_rest/authentication] user <USER> maria rossi is not configured",
    "warn: [plugins_rest/authentication] user <USER> rossi is not configured",
])
def test_v9_stored_user_not_configured_is_masked(collector, stored):
    expected = "warn: [plugins_rest/authentication] user <USER> is not configured"
    assert collector.mask(stored) == expected
    assert collector.mask(expected) == expected


# --------------------------------------------------------------------------
# Masking version 10: dovecot's per-session prefix. A mail process names
# its log lines "imap(<user>)<pid><session>:", and the login processes
# write "user=<name>, ..., session=<id>". The account went to the server
# in clear, and the pid and the session id made a template per session.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    (
        "<2> [dovecot] imap(marzio)<2202083><kQ1Ff9VCBuF/AAAB>: Fatal: "
        "block_alloc(268435456): Out of memory",
        "<2> [dovecot] imap(<USER>)<PID><ID>: Fatal: "
        "block_alloc(<PID>): Out of memory",
    ),
    (
        "<6> [dovecot] imap(marzio@example.com)<2202083><kQ1Ff9VCBuF/AAAB>: "
        "Logged out in=12 out=345",
        "<6> [dovecot] imap(<USER>)<PID><ID>: Logged out in=<NUM> out=<NUM>",
    ),
    (
        "<6> [dovecot] pop3(anna.rossi)<11><abcd>: Disconnected: Logged out",
        "<6> [dovecot] pop3(<USER>)<PID><ID>: Disconnected: Logged out",
    ),
    (
        "<6> [dovecot] lmtp(marzio)<4321>: saved mail to INBOX",
        "<6> [dovecot] lmtp(<USER>)<PID>: saved mail to INBOX",
    ),
    (
        "<6> [dovecot] indexer-worker(marzio)<77><lzQyBg:Ab12>: Indexed 3 messages",
        "<6> [dovecot] indexer-worker(<USER>)<PID><ID>: Indexed <NUM> messages",
    ),
    (
        "<6> [dovecot] imap-login: Login: user=<marzio>, method=PLAIN, "
        "rip=192.0.2.1, lip=192.0.2.2, mpid=123, TLS, session=<kQ1Ff9VCBuF/AAAB>",
        "<6> [dovecot] imap-login: Login: user=<USER>, method=PLAIN, "
        "rip=<IP>, lip=<IP>, mpid=<NUM>, TLS, session=<ID>",
    ),
    (
        "<6> [dovecot] imap-login: Login: user=<marzio@example.com>, method=PLAIN, "
        "rip=192.0.2.1, lip=192.0.2.2, mpid=123, TLS, session=<kQ1Ff9VCBuF/AAAB>",
        "<6> [dovecot] imap-login: Login: user=<USER>, method=PLAIN, "
        "rip=<IP>, lip=<IP>, mpid=<NUM>, TLS, session=<ID>",
    ),
])
def test_v10_dovecot_user_is_masked(collector, raw, expected):
    assert _template(collector, raw) == expected
    assert collector.mask(expected) == expected


def test_v10_dovecot_empty_user_is_kept(collector):
    # "user=<>" means the client gave no name: a signal, not an account.
    raw = ("<6> [dovecot] pop3-login: Disconnected (no auth attempts): "
           "user=<>, rip=192.0.2.1, lip=192.0.2.2, session=<abcd>")
    assert _template(collector, raw) == (
        "<6> [dovecot] pop3-login: Disconnected (no auth attempts): "
        "user=<>, rip=<IP>, lip=<IP>, session=<ID>")


def test_v10_dovecot_master_line_is_untouched(collector):
    # "service(imap): child ..." names a service, not a user.
    line = "<2> [dovecot] master: service(imap): child <NUM> returned error <NUM>"
    assert collector.mask(line) == line


@pytest.mark.parametrize("stored", [
    "<2> [dovecot] imap(marzio)<2202083><<ID>>: Fatal: block_alloc(<PID>): Out of memory",
    "<2> [dovecot] imap(marzio)<2202083><kQ1Ff9VCBuF/AAAB>: Fatal: block_alloc(<PID>): Out of memory",
])
def test_v10_stored_dovecot_prefix_is_masked(collector, stored):
    assert collector.mask(stored) == (
        "<2> [dovecot] imap(<USER>)<PID><ID>: Fatal: block_alloc(<PID>): Out of memory")


# --------------------------------------------------------------------------
# Masking version 11: dovecot's mailbox directory, "/var/lib/vmail/<name>",
# is named after the account. A sieve error logs the script path.
# --------------------------------------------------------------------------

SIEVE_ERROR = (
    "<3> [dovecot] lmtp({u})<2386397><kQ1Ff9VCBuF/AAAB>: Error: sieve: "
    "Execution of script /var/lib/vmail/{u}/.dovecot.sieve failed with "
    "unsuccessful implicit keep (user {u} /var/lib/vmail/{u}/.dovecot.sieve.log "
    "may reveal additional details)"
)


@pytest.mark.parametrize("user", ["edoardo", "anna.rossi", "marzio@example.com"])
def test_v11_vmail_path_is_masked(collector, user):
    template = _template(collector, SIEVE_ERROR.format(u=user))
    assert user not in template
    assert "/var/lib/vmail/<USER>/" in template
    assert template.startswith("<3> [dovecot] lmtp(<USER>)<PID><ID>: ")
    assert collector.mask(template) == template


def test_v11_vmail_path_without_trailing_slash(collector):
    assert collector.mask("home=/var/lib/vmail/edoardo, uid=5000") == (
        "home=/var/lib/vmail/<USER>, uid=<NUM>")


def test_v11_stored_sieve_error_is_masked(collector):
    stored = (
        "<3> [dovecot] lmtp(edoardo)<2386397><<ID>>: Error: sieve: Execution "
        "of script /var/lib/vmail/edoardo/.<HOST> failed with unsuccessful "
        "implicit keep (user <USER> /var/lib/vmail/edoardo/.dovecot.sieve.log "
        "may reveal additional details)")
    assert collector.mask(stored) == (
        "<3> [dovecot] lmtp(<USER>)<PID><ID>: Error: sieve: Execution "
        "of script /var/lib/vmail/<USER>/<PATH> failed with unsuccessful "
        "implicit keep (user <USER> /var/lib/vmail/<USER>/.dovecot.sieve.log "
        "may reveal additional details)")



# --------------------------------------------------------------------------
# Masking version 12: nethcti's quoted user name folds whole to <USER>.
# --------------------------------------------------------------------------

TAKEOVER = ("<3> [nethvoice5] 2026-10-15T10:11:12.123Z - warn: [com_nethcti_ws] "
            "no ack for login takeOver procedure recv by user {u} (undefined)")


@pytest.mark.parametrize("user", [
    'alice', '"alice"', '"alice.rossi"', '"alice@example.com"',
])
def test_v12_quoted_nethcti_user_is_masked(collector, user):
    template = _template(collector, TAKEOVER.format(u=user))
    assert template == (
        "<3> [nethvoice] <TS> - warn: [com_nethcti_ws] no ack for login "
        "takeOver procedure recv by user <USER> (undefined)")
    assert collector.mask(template) == template


def test_v12_quoted_user_keeps_what_follows(collector):
    assert _template(collector, 'streaming authorization failed for user "alice.rossi"!') == (
        "streaming authorization failed for user <USER>!")



# --------------------------------------------------------------------------
# Masking version 13: rule 14 leaves the punctuation after a name, and
# "user <HOST>" folds to "user <USER>".
# --------------------------------------------------------------------------

STT = ("<3> [nethvoice5] nethcti-middleware middleware.go:42: [AUTH][ERROR] "
       "authorization failed for user {u}: missing or insufficient capability "
       "nethvoice_cti.satellite_stt")


@pytest.mark.parametrize("user", [
    "alice", "alice.rossi", "alice@example.com", "201", "a1b2c3d4e5",
])
def test_v13_user_keeps_the_colon_after_it(collector, user):
    template = _template(collector, STT.format(u=user))
    assert template == (
        "<3> [nethvoice] nethcti-middleware [AUTH][ERROR] "
        "authorization failed for user <USER>: missing or insufficient "
        "capability nethvoice_cti.satellite_stt")
    assert collector.mask(template) == template


@pytest.mark.parametrize("user", ["alice", "alice.rossi"])
def test_v13_user_keeps_the_full_stop_after_it(collector, user):
    assert _template(collector, f"authorization success for user {user}. GET /x") == (
        "authorization success for user <USER>. GET /x")


@pytest.mark.parametrize("stored, expected", [
    ("authorization failed for user <HOST>: missing",
     "authorization failed for user <USER>: missing"),
    ("authorization success for user <HOST>. GET /x",
     "authorization success for user <USER>. GET /x"),
    ("no user <USER><HOST> is present", "no user <USER> is present"),
])
def test_v13_stored_user_placeholder_is_folded(collector, stored, expected):
    assert collector.mask(stored) == expected


def test_v13_user_address_is_not_folded(collector):
    line = "<6> [sshd-session] Connection closed by invalid user <IP> port <NUM> [preauth]"
    assert collector._fold_user_values(line) == line


# --------------------------------------------------------------------------
# Masking version 14: nethcti's "convid" folds to <ID>.
# --------------------------------------------------------------------------

HANGUP = ("<3> [nethvoice5] 2026-10-15T10:11:12.123Z - warn: [plugins_rest/astproxy] "
          "hangup convid {c} by user alice with 201 has been failed")


@pytest.mark.parametrize("convid", [
    "PJSIP/201-0000a1b2>",
    "PJSIP/201-0000a1b2>PJSIP/202-0000a1b3",
    "PJSIP/201-0000a1b2>Local/202@from-internal-0000a1b4;1",
    "Local/202@from-queue-0000a1b4;2>PJSIP/201-0000a1b2",
])
def test_v14_convid_is_masked(collector, convid):
    template = _template(collector, HANGUP.format(c=convid))
    assert template == (
        "<3> [nethvoice] <TS> - warn: [plugins_rest/astproxy] hangup convid "
        "<ID> by user <USER> with <NUM> has been failed")
    assert collector.mask(template) == template


def test_v14_quoted_convid_keeps_quotes(collector):
    raw = 'force hangup convid "PJSIP/201-0000a1b2>" by user alice with extension 201'
    assert _template(collector, raw) == (
        'force hangup convid "<ID>" by user <USER> with extension <NUM>')


# --------------------------------------------------------------------------
# Masking version 15: Go's log prefix, date and "file.go:line: ", is dropped.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("prefix", [
    "2026/10/15 10:11:12 logs.go:42: ",
    "2026/10/15 10:11:12.123456 logs.go:42: ",
    "middleware.go:118: ",
])
def test_v15_go_log_prefix_is_dropped(collector, prefix):
    raw = ("<3> [nethvoice5] nethcti-middleware " + prefix +
           "[AUTH][ERROR] authorization failed for user alice: missing")
    template = _template(collector, raw)
    assert template == (
        "<3> [nethvoice] nethcti-middleware [AUTH][ERROR] authorization "
        "failed for user <USER>: missing")
    assert collector.mask(template) == template


@pytest.mark.parametrize("stored", [
    "<3> [nethvoice] nethcti-middleware <NUM>/<NUM>/<NUM> <TS> logs.go:<NUM>: [CRITICAL][DB] down",
    "<3> [nethvoice] nethcti-middleware middleware.go:<NUM>: [CRITICAL][DB] down",
])
def test_v15_stored_go_log_prefix_is_dropped(collector, stored):
    assert collector.mask(stored) == "<3> [nethvoice] nethcti-middleware [CRITICAL][DB] down"


@pytest.mark.parametrize("line", [
    "<4> [prometheus] ts=<TS> caller=head.go:<NUM> level=info msg=ok",
    "<4> [prometheus] source=head.go:<NUM> level=info",
])
def test_v15_go_source_field_is_kept(collector, line):
    assert collector.mask(line) == line


# --------------------------------------------------------------------------
# Masking version 16: the pid in dovecot's post-login line becomes <PID>.
# --------------------------------------------------------------------------

POSTLOGIN = ("<3> [dovecot2] imap-postlogin: Error: <{p}>impersonated login "
             "MASTER_USER=vmail USER=alice.rossi AUTH_USER=vmail "
             "IP=192.0.2.1 LOCAL_IP=192.0.2.2")


@pytest.mark.parametrize("pid", ["12", "1234", "12345", "123456", "1234567"])
def test_v16_postlogin_pid_is_masked(collector, pid):
    template = _template(collector, POSTLOGIN.format(p=pid))
    assert template == (
        "<3> [dovecot] imap-postlogin: Error: <PID>impersonated login "
        "MASTER_USER=<USER> USER=<USER> AUTH_USER=<USER> IP=<IP> LOCAL_IP=<IP>")
    assert collector.mask(template) == template


@pytest.mark.parametrize("pid", ["<<NUM>>", "<HEX>"])
def test_v16_stored_postlogin_pid_is_masked(collector, pid):
    stored = f"<3> [dovecot] imap-postlogin: Error: {pid}impersonated login"
    assert collector.mask(stored) == "<3> [dovecot] imap-postlogin: Error: <PID>impersonated login"


# --------------------------------------------------------------------------
# Masking version 17: the file name in tancredi's "Template not found".
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "fanvil_x5u_v2_hwv2_0.txt", "y000000000124.cfg", "001565a1b2c3.xml",
    "phone.example.com",
])
def test_v17_tancredi_template_name_is_masked(collector, name):
    raw = (f'<3> [nethvoice5] [2026-10-15 10:11:12] tancredi.ERROR: Template '
           f'not found for "{name}". It does not match our patterns.d/ rules')
    template = _template(collector, raw)
    assert template == (
        '<3> [nethvoice] [<TS>] <HOST>: Template not found for "<PATH>". '
        'It does not match our patterns.d/ rules')
    assert collector.mask(template) == template


# --------------------------------------------------------------------------
# Masking version 18: FreePBX's XTNCONFLICT list of names is folded.
# --------------------------------------------------------------------------

XTNCONFLICT = (
    "<3> [freepbx5] [2026-10-15 10:11:12] [freepbx.INFO]: [NOTIFICATION]-"
    "[retrieve_conf]-[XTNCONFLICT] - There are 1 conflicting extensions "
    "(Extension: 8001:<br /> INUSE: Queue: {q}<br /> INUSE: Featurecode: "
    "atxfercallbackretries (extraoptions:Call back retries)<br />Ex"
)


@pytest.mark.parametrize("queue", ["Alice e Bob", "Amministrazione", "coda uff"])
def test_v18_xtnconflict_names_are_masked(collector, queue):
    template = _template(collector, XTNCONFLICT.format(q=queue))
    assert queue not in template
    assert template == (
        "<3> [freepbx] [<TS>] [<HOST>]: [NOTIFICATION]-[retrieve_conf]-"
        "[XTNCONFLICT] - There are <NUM> conflicting extensions <DATA>")
    assert collector.mask(template) == template


# --------------------------------------------------------------------------
# Masking version 19: an ISO-8601 timestamp with a one-digit hour.
# --------------------------------------------------------------------------

ABORTED = ("<3> [nethvoice5] {ts} 123 [Warning] Aborted connection 123 to db: "
           "'asteriskcdrdb' user: 'cdr' host: '10.0.0.5' (Got timeout reading "
           "communication packets)")


@pytest.mark.parametrize("ts", ["2026-10-15  9:11:12", "2026-10-15 10:11:12"])
def test_v19_mariadb_timestamp_is_masked(collector, ts):
    template = _template(collector, ABORTED.format(ts=ts))
    assert template == (
        "<3> [nethvoice] <TS> <NUM> [Warning] Aborted connection <NUM> to db: "
        "'asteriskcdrdb' user: <USER> host: '<IP>' (Got timeout reading "
        "communication packets)")
    assert collector.mask(template) == template


# --------------------------------------------------------------------------
# Masking version 20: sshd's "invalid user", also with an empty name.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("<6> [sshd-session] Invalid user {u} from 203.0.113.5 port 22",
     "<6> [sshd-session] Invalid user <USER> from <IP> port <NUM>"),
    ("<6> [sshd-session] Connection closed by invalid user {u} 203.0.113.5 port 22 [preauth]",
     "<6> [sshd-session] Connection closed by invalid user <USER> <IP> port <NUM> [preauth]"),
    ("<6> [sshd-session] Disconnected from invalid user {u} 203.0.113.5 port 22 [preauth]",
     "<6> [sshd-session] Disconnected from invalid user <USER> <IP> port <NUM> [preauth]"),
    ("<3> [sshd-session] error: maximum authentication attempts exceeded for "
     "invalid user {u} from 203.0.113.5 port 22 ssh2 [preauth]",
     "<3> [sshd-session] error: maximum authentication attempts exceeded for "
     "invalid user <USER> from <IP> port <NUM> ssh2 [preauth]"),
])
@pytest.mark.parametrize("user", ["alice", "", "alice.example.com"])
def test_v20_sshd_invalid_user_is_masked(collector, raw, expected, user):
    template = _template(collector, raw.format(u=user))
    assert template == expected
    assert collector.mask(template) == template


def test_v20_sshd_user_called_from_is_masked(collector):
    raw = "<6> [sshd-session] Invalid user from from 203.0.113.5 port 22"
    assert _template(collector, raw) == (
        "<6> [sshd-session] Invalid user <USER> from <IP> port <NUM>")


def test_v20_stored_sshd_empty_user_is_masked(collector):
    stored = "<6> [sshd-session] Connection closed by invalid user <IP> port <NUM> [preauth]"
    assert collector.mask(stored) == (
        "<6> [sshd-session] Connection closed by invalid user <USER> <IP> port <NUM> [preauth]")


# --------------------------------------------------------------------------
# Masking version 21: an SSH key fingerprint folds whole to <ID>.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("fingerprint", [
    "bhkx0O+KmrZz/AbCdEfGh1234567890abcdefGHIJKLMN",
    "bhkx0OKmrZzAbCdEfGh1234567890abcdefGHIJKLMN",
    "/+AbCdEfGh1234567890abcdefGHIJKLMNbhkx0OKmrZz",
    "AbCdEfGh1234567/890abcdefGHIJKLMNbhkx0OKmrZz",
])
def test_v21_ssh_fingerprint_is_masked(collector, fingerprint):
    raw = ("<6> [sshd-session] Accepted publickey for root from 203.0.113.5 "
           "port 22 ssh2: RSA SHA256:" + fingerprint)
    template = _template(collector, raw)
    assert template == ("<6> [sshd-session] Accepted publickey for root from "
                        "<IP> port <NUM> ssh2: RSA SHA256:<ID>")
    assert collector.mask(template) == template


@pytest.mark.parametrize("stored", [
    "ssh2: RSA SHA256:bhkx0O+KmrZz/<ID>",
    "ssh2: RSA SHA256:<redacted-blob>",
    "ssh2: RSA SHA256:/+<redacted-blob>",
    "ssh2: RSA SHA256:<ID>/<ID>",
])
def test_v21_stored_ssh_fingerprint_is_masked(collector, stored):
    assert collector.mask(stored) == "ssh2: RSA SHA256:<ID>"


# --------------------------------------------------------------------------
# Masking version 22: rclone-gateway's HAProxy names and durations in ms.
# --------------------------------------------------------------------------

GW_DOWN = ("<3> [rclone-gateway] Server gw_b2_{b}/gw{n} is DOWN, reason: {r}, "
           "check duration: {d}ms. 0 active and 0 backup servers left.")


@pytest.mark.parametrize("backend, number, duration", [
    ("dfe8f881", "3", "1"), ("fa299864", "1", "12"), ("a2f82897", "6", "60006"),
])
def test_v22_gateway_server_down_is_masked(collector, backend, number, duration):
    raw = GW_DOWN.format(b=backend, n=number, d=duration,
                         r="Layer4 connection problem")
    template = _template(collector, raw)
    assert template == (
        "<3> [rclone-gateway] Server gw_b2_<HEX>/gw<NUM> is DOWN, reason: "
        "Layer4 connection problem, check duration: <NUM>ms. <NUM> active "
        "and <NUM> backup servers left.")
    assert collector.mask(template) == template


def test_v22_gateway_reason_is_kept(collector):
    layer4 = _template(collector, GW_DOWN.format(
        b="dfe8f881", n="2", d="1", r="Layer4 connection problem"))
    layer7 = _template(collector, GW_DOWN.format(
        b="dfe8f881", n="2", d="1", r="Layer7 timeout"))
    assert layer4 != layer7


def test_v22_stored_gateway_server_is_masked(collector):
    assert collector.mask("Server gw_b2_dfe8f881/gw3 is DOWN, check duration: 60006ms.") == (
        "Server gw_b2_<HEX>/gw<NUM> is DOWN, check duration: <NUM>ms.")


@pytest.mark.parametrize("raw, expected", [
    ("Timeout was 5000ms (~5s)", "Timeout was <NUM>ms (~5s)"),
    ("took 1.5ms", "took <NUM>ms"),
    ("snapshot_20261015ab done", "snapshot_<HEX> done"),
])
def test_v22_milliseconds_and_hex_after_underscore(collector, raw, expected):
    assert collector.mask(raw) == expected


# --------------------------------------------------------------------------
# Masking version 23: Apache's referer and the probed script name.
# --------------------------------------------------------------------------

PROBE = ("<3> [freepbx5] [Wed Oct 15 10:11:12.123456 2026] [php7:error] "
         "[pid 1234:tid 5678] [client 203.0.113.5:4444] script "
         "'/var/www/html/freepbx/wizard/{s}' not found or unable to stat{r}")


@pytest.mark.parametrize("script, referer", [
    ("xmlrpc.php", ", referer: https://example.com//wp-login.php"),
    ("check.php", ", referer: http://example.com/check.php"),
    ("as.php", ""),
    ("phpinfo.php", ", referer: https://example.com/"),
])
def test_v23_apache_probe_is_masked(collector, script, referer):
    template = _template(collector, PROBE.format(s=script, r=referer))
    assert template == (
        "<3> [freepbx] [<TS>] [php7:error] [pid <PID>:tid <NUM>] "
        "[client <IP>:<PORT>] script '/var/www/html/freepbx/wizard/<PATH>' "
        "not found or unable to stat")
    assert collector.mask(template) == template


def test_v23_referer_is_kept_outside_apache(collector):
    line = "login failed, referer: https://<HOST>/"
    assert collector.mask(line) == line


# --------------------------------------------------------------------------
# Masking version 24: an account in a request path becomes <USER>.
# --------------------------------------------------------------------------

HISTORY = ("<3> [nethvoice5] nethcti-middleware middleware.go:42: [INFO][AUTH] "
           "authorization success for user {u}. GET /historycall/interval/user/"
           "{u}/20261015/20261016?offset=0&limit=15")


@pytest.mark.parametrize("user", ["alice", "alice.rossi", "int21"])
def test_v24_user_in_request_path_is_masked(collector, user):
    template = _template(collector, HISTORY.format(u=user))
    assert user not in template
    assert "GET /historycall/interval/user/<USER>/<HEX>/<HEX>?" in template
    assert collector.mask(template) == template


@pytest.mark.parametrize("line", [
    "authorization success for user <USER>. GET /user/paramurl",
    "authorization success for user <USER>. GET /user/endpoints/all",
])
def test_v24_user_endpoint_is_kept(collector, line):
    assert collector.mask(line) == line


# --------------------------------------------------------------------------
# Masking version 25: the text searched in nethcti's phonebook.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("search", ["ALICE%20ROSSI", "Example%20SRL", "0612345678", "+3906"])
def test_v25_phonebook_search_is_masked(collector, search):
    raw = ("<3> [nethvoice5] nethcti-middleware middleware.go:42: [INFO][AUTH] "
           "authorization success for user alice. GET /phonebook/search/" + search +
           "?offset=0&limit=15&view=company")
    template = _template(collector, raw)
    assert template == (
        "<3> [nethvoice] nethcti-middleware [INFO][AUTH] authorization success "
        "for user <USER>. GET /phonebook/search/<DATA>?offset=<NUM>&limit=<NUM>"
        "&view=company")
    assert collector.mask(template) == template


def test_v25_empty_phonebook_search_is_kept(collector):
    line = "GET /phonebook/search/?offset=<NUM>&limit=<NUM>&view=all"
    assert collector.mask(line) == line




# --------------------------------------------------------------------------
# Masking version 26: personal data still in the dev fleet's stored
# templates on 2026-10-19 -- account and folder names, nextcloud files,
# phonebook contacts, a staff directory -- and three shapes that minted a
# template per probe, per stream or per backup.
# --------------------------------------------------------------------------

# 26.1: dovecot's auth line names the account and the session.

AUTH_FAILED = ("<3> [dovecot] auth: Error: plain({u},192.0.2.4,<{s}>): "
               "user not found from any userdbs")
AUTH_FAILED_TEMPLATE = ("<3> [dovecot] auth: Error: plain(<USER>,<IP>,<ID>): "
                        "user <USER> found from any userdbs")


@pytest.mark.parametrize("user, session", [
    ("alice", "k++aQPemrXKBQQZ"),
    ("marzio", "AbCdEf12+/xy"),
    ("anna.rossi", "xYz12AbC"),
    ("marzio@example.com", "pq7d8shdj+wBrBY3"),
    ("?", "q"),
])
def test_v26_dovecot_auth_is_masked(collector, user, session):
    template = _template(collector, AUTH_FAILED.format(u=user, s=session))
    assert template == AUTH_FAILED_TEMPLATE
    assert session not in template
    assert collector.mask(template) == template


@pytest.mark.parametrize("raw, expected", [
    ("<3> [dovecot] auth-worker(12345): Error: conn unix:auth-worker "
     "(pid=1,uid=97): auth-worker<5>: ldap(alice,192.0.2.4,<abc12>): "
     "ldap_bind() failed",
     "<3> [dovecot] auth-worker(<PID>): Error: conn unix:auth-worker "
     "(pid=<PID>,uid=<NUM>): auth-worker<<NUM>>: ldap(<USER>,<IP>,<ID>): "
     "ldap_bind() failed"),
    ("<3> [dovecot] auth: passwd-file(alice,192.0.2.4): unknown user",
     "<3> [dovecot] auth: passwd-file(<USER>,<IP>): unknown user"),
    ("<3> [dovecot] auth-worker(12345): pam(alice,2001:db8::1): "
     "pam_authenticate() failed",
     "<3> [dovecot] auth-worker(<PID>): pam(<USER>,<IP>): "
     "pam_authenticate() failed"),
    ("<3> [dovecot] auth: Error: login(alice,,<x+y/z>): Request timed out",
     "<3> [dovecot] auth: Error: login(<USER>,,<ID>): Request timed out"),
])
def test_v26_dovecot_auth_shapes_are_masked(collector, raw, expected):
    template = _template(collector, raw)
    assert template == expected
    assert "alice" not in template
    assert collector.mask(template) == template


def test_v26_stored_dovecot_auth_is_masked(collector):
    stored = ("<3> [dovecot] auth: Error: plain(alice,<IP>,<k++aQPemrXKBQQZ>): "
              "user <USER> found from any userdbs")
    assert collector.mask(stored) == AUTH_FAILED_TEMPLATE


@pytest.mark.parametrize("line", [
    "<3> [dovecot] master: service(imap): child <NUM> killed",
    "<3> [dovecot] auth-worker(<PID>): Error: Fatal: connection lost",
])
def test_v26_dovecot_auth_lookalikes_are_kept(collector, line):
    assert collector.mask(line) == line


def test_v26_dovecot_auth_reasons_stay_distinct(collector):
    unknown = _template(collector, "<3> [dovecot] auth: passwd-file(alice,"
                                   "192.0.2.4,<abc>): unknown user")
    mismatch = _template(collector, "<3> [dovecot] auth: passwd-file(alice,"
                                    "192.0.2.4,<abc>): Password mismatch")
    assert unknown != mismatch


# 26.1, already masked: the mail process prefix and the SASL account.

@pytest.mark.parametrize("stored, expected", [
    ("<3> [dovecot] imap(bob)<2225504><pq7d8shdj+wBrBY3>: Error: Disconnected",
     "<3> [dovecot] imap(<USER>)<PID><ID>: Error: Disconnected"),
    ("warning: unknown[<IP>]: SASL LOGIN authentication failed: (reason "
     "unavailable), sasl_username=marzio",
     "warning: unknown[<IP>]: SASL LOGIN authentication failed: (reason "
     "unavailable), sasl_username=<USER>"),
    ("warning: unknown[<IP>]: SASL LOGIN authentication failed: (reason "
     "unavailable), sasl_username=clienti",
     "warning: unknown[<IP>]: SASL LOGIN authentication failed: (reason "
     "unavailable), sasl_username=<USER>"),
])
def test_v26_stored_mail_accounts_stay_masked(collector, stored, expected):
    assert collector.mask(stored) == expected


# 26.2: mailbox names and the folders of a mailbox directory.

CACHE_RECORD = ("<3> [dovecot] imap(alice)<2225504><pq7d8shdj+wBrBY3>: Error: "
                "Mailbox {m}: Deleting corrupted cache record uid=12: UID 12 "
                "is not in the index")
CACHE_RECORD_TEMPLATE = ("<3> [dovecot] imap(<USER>)<PID><ID>: Error: Mailbox "
                         "<PATH>: Deleting corrupted cache record uid=<NUM>: "
                         "UID <NUM> is not in the index")


@pytest.mark.parametrize("mailbox", [
    "Shared/monitor/Allarmi/Backup/Custom",
    "INBOX",
    "Clienti/Rossi Mario",
    "Posta inviata",
])
def test_v26_mailbox_name_is_masked(collector, mailbox):
    template = _template(collector, CACHE_RECORD.format(m=mailbox))
    assert template == CACHE_RECORD_TEMPLATE
    assert collector.mask(template) == template


def test_v26_stored_mailbox_name_is_masked(collector):
    stored = ("Error: Mailbox Shared/monitor/Allarmi/Backup/Custom: Deleting "
              "corrupted cache record uid=<NUM>: broken")
    assert collector.mask(stored) == (
        "Error: Mailbox <PATH>: Deleting corrupted cache record uid=<NUM>: broken")


@pytest.mark.parametrize("raw, expected", [
    ("Error: msgid=<abc@example.com>: save failed to Junk: Mailbox doesn't "
     "exist: Junk",
     "Error: msgid=<<redacted-email>>: save failed to <PATH>: Mailbox doesn't "
     "exist: <PATH>"),
    ("Error: Mailbox doesn't exist: Clienti Rossi (0.001 + 0.000 secs)",
     "Error: Mailbox doesn't exist: <PATH> (<NUM> + <NUM> secs)"),
    ("Error: sieve: failed to store into mailbox 'Shared/alice/Clienti': "
     "Permission denied",
     "Error: sieve: failed to store into mailbox '<PATH>': Permission denied"),
    ("Error: Corrupted record in mailbox Shared/monitor/Allarmi: Deleting",
     "Error: Corrupted record in mailbox <PATH>: Deleting"),
    ("Error: Corrupted record in mailbox Clienti",
     "Error: Corrupted record in mailbox <PATH>"),
])
def test_v26_mailbox_name_shapes_are_masked(collector, raw, expected):
    template = _template(collector, raw)
    assert template == expected
    assert collector.mask(template) == template


@pytest.mark.parametrize("line", [
    "Mailbox is full: try again later",
    "Error: Mailbox is full: try again later",
    "The mailbox quota is exceeded",
])
def test_v26_mailbox_prose_is_kept(collector, line):
    assert collector.mask(line) == line


def test_v26_mailbox_conditions_stay_distinct(collector):
    cache = _template(collector, "Error: Mailbox Clienti: Deleting corrupted "
                                 "cache record")
    missing = _template(collector, "Error: Mailbox doesn't exist: Clienti")
    assert cache != missing


VMAIL_ERROR = ("<3> [dovecot] imap(alice)<1><a>: Error: open({p}) failed: "
               "No such file or directory")


@pytest.mark.parametrize("path, expected", [
    ("/var/lib/vmail/edoardo/Maildir/.Archivio.2024/dovecot.index.cache",
     "/var/lib/vmail/<USER>/Maildir/<PATH>/dovecot.index.cache"),
    ("/var/lib/vmail/edoardo/Maildir/.Posta inviata/dovecot-uidlist",
     "/var/lib/vmail/<USER>/Maildir/<PATH>/dovecot-uidlist"),
    ("/var/lib/vmail/edoardo/Maildir/.Clienti.Rossi/dovecot.index.log.2",
     "/var/lib/vmail/<USER>/Maildir/<PATH>/dovecot.index.log.<NUM>"),
    ("/var/lib/vmail/edoardo/Maildir/cur/1697000000.M1P2.mail,S=123,W=456:2,S",
     "/var/lib/vmail/<USER>/Maildir/cur/<PATH>"),
    ("/var/lib/vmail/edoardo/.dovecot.sieve",
     "/var/lib/vmail/<USER>/.dovecot.sieve"),
    ("/var/lib/vmail/edoardo/.dovecot.lda-dupes",
     "/var/lib/vmail/<USER>/.dovecot.lda-dupes"),
    ("/var/lib/vmail/edoardo/sieve/roundcube.sieve",
     "/var/lib/vmail/<USER>/sieve/<PATH>"),
])
def test_v26_vmail_folders_are_masked(collector, path, expected):
    template = _template(collector, VMAIL_ERROR.format(p=path))
    assert template == (
        "<3> [dovecot] imap(<USER>)<PID><ID>: Error: open(" + expected +
        ") failed: No such file or directory")
    assert "edoardo" not in template
    assert collector.mask(template) == template


def test_v26_stored_vmail_folder_is_masked(collector):
    assert collector.mask("/var/lib/vmail/edoardo/.<HOST>") == (
        "/var/lib/vmail/<USER>/<PATH>")


def test_v26_vmail_folders_merge_and_files_stay_apart(collector):
    def path(p):
        return _template(collector, VMAIL_ERROR.format(p=p))
    assert path("/var/lib/vmail/a/Maildir/.Clienti/dovecot.index") == path(
        "/var/lib/vmail/b/Maildir/.Fornitori.Rossi/dovecot.index")
    assert path("/var/lib/vmail/a/Maildir/.Clienti/dovecot.index") != path(
        "/var/lib/vmail/a/Maildir/.Clienti/dovecot-uidlist")


# 26.3: nextcloud's account and WebDAV paths.

NEXTCLOUD = ('{{"reqId":"aBcD1234efGH5678","level":3,"time":"2026-10-19T08:00:00+00:00",'
             '"remoteAddr":"192.0.2.4","user":"{u}","app":"webdav","method":"PUT",'
             '"url":"{url}","message":"Sabre\\\\DAV\\\\Exception\\\\Forbidden"}}')


@pytest.mark.parametrize("user, url, expected", [
    ("admin",
     "/remote.php/dav/files/admin/X%2001-%20DATI/CLIENTI/1234_ESEMPIO%20SRL/"
     "DIPENDENTI/01esempio/MARIO%20ROSSI%20LETT.%20ESEMPIO%20ORARIO.pdf",
     "/remote.php/dav/files/<USER>/<PATH>"),
    ("mario.rossi",
     "/remote.php/dav/files/mario.rossi/Documenti/contratto.odt",
     "/remote.php/dav/files/<USER>/<PATH>"),
    ("admin",
     "/remote.php/dav/uploads/admin/web-file-upload-8f2c4a1b9d3e7f60/1",
     "/remote.php/dav/uploads/<USER>/<PATH>"),
    ("admin", "/remote.php/dav/trashbin/admin/trash/x.pdf.d1697000000",
     "/remote.php/dav/trashbin/<USER>/<PATH>"),
    ("admin", "/remote.php/dav/calendars/admin/personal/",
     "/remote.php/dav/calendars/<USER>/<PATH>"),
    ("admin", "/remote.php/dav/addressbooks/users/admin/contacts/x.vcf",
     "/remote.php/dav/addressbooks/users/<USER>/<PATH>"),
    ("admin", "/remote.php/dav/principals/users/admin/",
     "/remote.php/dav/principals/users/<USER>/"),
    ("admin", "/remote.php/dav/files/admin", "/remote.php/dav/files/<USER>"),
    ("admin", "/remote.php/webdav/Clienti/Rossi.pdf", "/remote.php/webdav/<PATH>"),
])
def test_v26_nextcloud_user_and_path_are_masked(collector, user, url, expected):
    template = _template(collector, NEXTCLOUD.format(u=user, url=url))
    assert template == (
        '{"reqId":"<ID>","level":<NUM>,"time":"<TS>","remoteAddr":"<IP>",'
        '"user":"<USER>","app":"webdav","method":"PUT","url":"' + expected +
        '","message":"Sabre\\\\DAV\\\\Exception\\\\Forbidden"}')
    assert user not in template
    assert collector.mask(template) == template


@pytest.mark.parametrize("stored, expected", [
    ('"user":"admin","url":"/remote.php/dav/files/admin/X%<NUM>-%20DATI/CLIENTI/'
     '1234_ESEMPIO%20SRL/DIPENDENTI/01esempio/MARIO%20ROSSI%20LETT.%20ESEMPIO%20ORARIO..."',
     '"user":"<USER>","url":"/remote.php/dav/files/<USER>/<PATH>"'),
    ('"url":"/remote.php/dav/files/admin/X%<NUM>-%20DATI/CLIENTI/1234_ESEMPIO%20SRL/'
     'DIPENDENTI/01esempio/MARIO%20ROSSI%20LETT.%20ESEMPIO%<HOST>"',
     '"url":"/remote.php/dav/files/<USER>/<PATH>"'),
    ('"url":"/remote.php/dav/uploads/admin/web-file-upload-<HEX>/<NUM>"',
     '"url":"/remote.php/dav/uploads/<USER>/<PATH>"'),
])
def test_v26_stored_nextcloud_path_is_masked(collector, stored, expected):
    assert collector.mask(stored) == expected


@pytest.mark.parametrize("line", [
    '{"reqId":"<ID>","user":"--","app":"core","url":"/index.php/login",'
    '"message":"Login failed"}',
    '{"user":"","app":"core","url":"/remote.php/webdav/"}',
    '{"app":"files","url":"/remote.php/dav/files/"}',
])
def test_v26_nextcloud_anonymous_is_kept(collector, line):
    assert collector.mask(line) == line


def test_v26_nextcloud_dav_kinds_stay_distinct(collector):
    files = _template(collector, NEXTCLOUD.format(
        u="a", url="/remote.php/dav/files/a/x.pdf"))
    uploads = _template(collector, NEXTCLOUD.format(
        u="a", url="/remote.php/dav/uploads/a/x"))
    assert files != uploads


# 26.4: the contact NethVoice's phonebook sync dumps.

CONTACT = ("<3> [] [1234] ERROR: copying entry \"{{'owner_id': '', 'type': "
           "'private', 'homeemail': '', 'workemail': '{e}', 'title': '{t}', "
           "'company': '{c}', 'notes': '{n}', 'name': '{nm}', 'homestreet': '', "
           "'cellphone': None, 'id': {i}}}\"")
CONTACT_TEMPLATE = ("<3> [] [<PID>] ERROR: copying entry \"{'owner_id': '<DATA>', "
                    "'type': '<DATA>', 'homeemail': '<DATA>', 'workemail': '<DATA>', "
                    "'title': '<DATA>', 'company': '<DATA>', 'notes': '<DATA>', "
                    "'name': '<DATA>', 'homestreet': '<DATA>', 'cellphone': '<DATA>', "
                    "'id': '<DATA>'}\"")


@pytest.mark.parametrize("email, title, company, notes, name, number", [
    ("m.rossi@example.com", "Responsabile Ufficio Tecnico",
     "EMPRESA EJEMPLO CIA. LTDA", "Cliente", "Mario Rossi", "12"),
    ("", "", "", "", "Giulia Neri", "7"),
    ("", "", "Example S.r.l.", "", "", "1234567"),
])
def test_v26_phonebook_contact_is_masked(collector, email, title, company,
                                         notes, name, number):
    template = _template(collector, CONTACT.format(
        e=email, t=title, c=company, n=notes, nm=name, i=number))
    assert template == CONTACT_TEMPLATE
    for value in (title, company, name):
        if value:
            assert value not in template
    assert collector.mask(template) == template


def test_v26_stored_phonebook_contact_is_masked(collector):
    stored = ("<3> [] [<PID>] ERROR: copying entry \"{'owner_id': '', 'title': "
              "'Responsabile Ufficio Tecnico', 'company': 'EMPRESA EJEMPLO <HOST> "
              "LTDA', 'notes': 'Cliente', 'name': 'Mario Rossi', "
              "'homestreet': '', 'id': <NUM>}\"")
    assert collector.mask(stored) == (
        "<3> [] [<PID>] ERROR: copying entry \"{'owner_id': '<DATA>', 'title': "
        "'<DATA>', 'company': '<DATA>', 'notes': '<DATA>', 'name': '<DATA>', "
        "'homestreet': '<DATA>', 'id': '<DATA>'}\"")


@pytest.mark.parametrize("raw, expected", [
    ("ERROR: copying entry \"{'name': \"O'Brien\", 'notes': 'a\\'b', "
     "'n': -1.5, 'd': datetime.datetime(2020, 1, 1, 0, 0), 'b': True}\": "
     "Duplicate entry",
     "ERROR: copying entry \"{'name': '<DATA>', 'notes': '<DATA>', "
     "'n': '<DATA>', 'd': '<DATA>', 'b': '<DATA>'}\": Duplicate entry"),
    ("ERROR: copying entry \"{'name': 'Mario', 'password=<redacted> 'x'}\": "
     "broken",
     "ERROR: copying entry \"{<DATA>}\": broken"),
    ("ERROR: copying entry \"{'name': 'Mario Rossi', 'company",
     "ERROR: copying entry \"{<DATA>}\""),
])
def test_v26_phonebook_contact_shapes_are_masked(collector, raw, expected):
    template = _template(collector, raw)
    assert template == expected
    assert "Mario" not in template and "Brien" not in template
    assert collector.mask(template) == template


def test_v26_phonebook_key_sets_stay_distinct(collector):
    one = _template(collector, "ERROR: copying entry \"{'name': 'a'}\"")
    two = _template(collector, "ERROR: copying entry \"{'name': 'a', 'notes': 'b'}\"")
    assert one != two


# 26.5: a CSV dump, FreePBX's user directory.

APACHE_NOTICE = ("<5> [freepbx5] [Sun Oct 19 08:00:00.123456 2026] [php7:notice] "
                 "[pid 1234:tid 5678] [client 192.0.2.4:4444] ")
APACHE_NOTICE_TEMPLATE = ("<5> [freepbx] [<TS>] [php7:notice] [pid <PID>:tid <NUM>] "
                          "[client <IP>:<PORT>] <DATA>")


@pytest.mark.parametrize("dump", [
    '"anna","Anna Bianchi","201","","8f2c4a1b9d3e7f60","FALSE",'
    '"TRUE","Padova","Sales"\\r\\n"luca","Luca Verdi","202",'
    '"","8f2c4a1b9d3e7f61","FALSE","TRUE","Vicenza","Sales"',
    '"a","Mario Rossi","1","",""',
    '"mario","Mario Rossi"\\r\\n"anna","Anna Bianchi"',
])
def test_v26_csv_dump_is_masked(collector, dump):
    template = _template(collector, APACHE_NOTICE + dump)
    assert template == APACHE_NOTICE_TEMPLATE
    assert "Rossi" not in template
    assert collector.mask(template) == template


def test_v26_stored_csv_dump_is_masked(collector):
    stored = ('[freepbx] [<TS>] [php7:notice] [pid <PID>:tid <NUM>] [client <IP>:<PORT>] '
              '"<HOST>","Anna Bianchi","<NUM>","","<HEX>","FALSE","TRUE",'
              '"Padova","Sales"\\r\\n"<HOST>","Luca Verdi","<NUM>","","<HEX>",'
              '"FALSE","TRUE","Vicenza","Sales"')
    assert collector.mask(stored) == (
        "[freepbx] [<TS>] [php7:notice] [pid <PID>:tid <NUM>] [client <IP>:<PORT>] "
        "<DATA>")


@pytest.mark.parametrize("line", [
    'saved "a","b","c" here',
    'values "a", "b", "c", "d", "e", "f"',
    '{"app":"x","list":["a","b","c","d","e","f"]}',
    '{"a":"b","c":"d","e":"f","g":"h","i":"j","k":"l"}',
    'send HTTP <NUM> response with message "user <USER> is not configured"',
])
def test_v26_quoted_text_is_kept(collector, line):
    assert collector.mask(line) == line


# 26.6: free-text names: nethcti's message, FreePBX's destinations,
# nethcti's stream ids.

def test_v26_stored_nethcti_user_message_is_masked(collector):
    stored = ("warn: [plugins_rest/authentication] send HTTP <NUM> response to "
              "<IP>:<PORT> with message \"user <USER> maria rossi is not "
              "configured\"")
    assert collector.mask(stored) == (
        "warn: [plugins_rest/authentication] send HTTP <NUM> response to "
        "<IP>:<PORT> with message \"user <USER> is not configured\"")


BAD_DESTINATIONS = "<4> [freepbx5] [BADDEST] - There {v} {n} bad destination{s} {d}"


@pytest.mark.parametrize("verb, count, plural, destinations", [
    ("are", "3", "s", "Announcement: Voicemail_Studio_Esempio (vm,1), Ring Group: "
                      "Mario Rossi (grp,600)"),
    ("is", "1", "", "Announcement: Benvenuto_Studio_Bianchi (app-announcement-3,s,1)"),
])
def test_v26_bad_destinations_are_masked(collector, verb, count, plural,
                                         destinations):
    template = _template(collector, BAD_DESTINATIONS.format(
        v=verb, n=count, s=plural, d=destinations))
    assert template == ("<4> [freepbx] [BADDEST] - There " + verb +
                        " <NUM> bad destination" + plural + " <DATA>")
    assert collector.mask(template) == template


def test_v26_stored_bad_destinations_are_masked(collector):
    stored = ("[BADDEST] - There are <NUM> bad destinations Announcement: "
              "Voicemail_Studio_Esempio (vm,<NUM>)")
    assert collector.mask(stored) == (
        "[BADDEST] - There are <NUM> bad destinations <DATA>")


@pytest.mark.parametrize("stream", ["vs_citofono_ingresso_nord", "cam1", "Ingresso Nord"])
def test_v26_stream_id_is_masked(collector, stream):
    raw = ("<4> [nethvoice5] 2026-10-19T08:00:00.000Z - warn: [streaming] "
           "streaming \"" + stream + "\" error: Error: connect ETIMEDOUT")
    template = _template(collector, raw)
    assert template == ("<4> [nethvoice] <TS> - warn: [streaming] streaming "
                        "\"<ID>\" error: Error: connect ETIMEDOUT")
    assert collector.mask(template) == template


def test_v26_stored_stream_id_is_masked(collector):
    assert collector.mask('[streaming] streaming "vs_citofono_ingresso_nord" error') == (
        '[streaming] streaming "<ID>" error')


# 26.7: a probe's bytes in postfix, and the backup id in its units.

@pytest.mark.parametrize("raw", [
    "<4> [postfix] warning: non-SMTP command from unknown[192.0.2.4]: "
    "\\026\\003\\001X\\002",
    "<4> [postfix] warning: non-SMTP command from unknown[192.0.2.4]: "
    "GET / HTTP/1.1",
    "<4> [postfix] warning: non-SMTP command from unknown[192.0.2.4]: "
    "\\<NUM>\\<NUM>\\001X\\002",
])
def test_v26_postfix_probe_is_masked(collector, raw):
    template = _template(collector, raw)
    assert template == ("<4> [postfix] warning: non-SMTP command from "
                        "unknown[<IP>]: <DATA>")
    assert collector.mask(template) == template


def test_v26_postfix_pipelining_probe_is_masked(collector):
    template = _template(collector, "<6> [postfix] improper command pipelining "
                                    "after CONNECT from unknown[192.0.2.4]: "
                                    "\\026\\003\\001X\\002")
    assert template == ("<6> [postfix] improper command pipelining after "
                        "CONNECT from unknown[<IP>]: <DATA>")
    assert collector.mask(template) == template


@pytest.mark.parametrize("unit, expected", [
    ("backup77.service", "backup<NUM>.service"),
    ("backup1.service", "backup<NUM>.service"),
    ("backup1.timer", "backup<NUM>.timer"),
])
def test_v26_backup_unit_is_masked(collector, unit, expected):
    template = _template(collector, "<3> [systemd] " + unit +
                         ": Failed with result 'exit-code'.")
    assert template == ("<3> [systemd] " + expected +
                        ": Failed with result 'exit-code'.")
    assert collector.mask(template) == template


@pytest.mark.parametrize("line", [
    "<3> [systemd] agent@nethvoice2.service: Failed with result 'exit-code'.",
    "<3> [systemd] agent@backup1.service: Failed with result 'exit-code'.",
    "<3> [systemd] backup.service: Failed with result 'exit-code'.",
])
def test_v26_other_units_are_kept(collector, line):
    assert collector.mask(line) == line


def test_v26_masking_version(collector):
    assert collector.MASKING_VERSION == 26
