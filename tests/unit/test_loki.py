#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#
"""Tests for _filter_stages() and the Loki Client in insights-collector.

No network calls: a Client is built with a fake base URL and its _get()
method is monkeypatched to return canned payloads and record what it was
called with.
"""
import datetime
import re

import pytest

UTC = datetime.timezone.utc


def make_client(collector):
    return collector.Client("http://loki.example", "user", "pass")


# --------------------------------------------------------------------------
# _filter_stages()
# --------------------------------------------------------------------------

def test_filter_stages_basic(collector):
    stages = collector._filter_stages([], "loki1/insights-collector")
    assert stages == [
        '| json priority="PRIORITY", identifier="SYSLOG_IDENTIFIER"',
        '| identifier != "loki1/insights-collector"',
        '| priority=~"[0-4]" or category="security"',
    ]


def test_filter_stages_never_convert_the_priority(collector):
    """A numeric comparison fails on a record with no PRIORITY field, and
    Loki then rejects the whole metric query with a 400."""
    for stage in collector._filter_stages(["a"], "id", include_message=True):
        assert not re.search(r"priority\s*[<>]", stage)


def test_filter_stages_denylist_appended_only_when_non_empty(collector):
    stages = collector._filter_stages(["a", "b"], "id")
    assert stages[-1] == '!~ "a|b"'
    assert len(stages) == 4

    stages_empty = collector._filter_stages([], "id")
    assert not any(stage.startswith("!~") for stage in stages_empty)


def test_filter_stages_include_message(collector):
    without = collector._filter_stages([], "id", include_message=False)
    with_msg = collector._filter_stages([], "id", include_message=True)
    assert 'message="MESSAGE"' not in without[0]
    assert 'message="MESSAGE"' in with_msg[0]


# --------------------------------------------------------------------------
# Client.tail()
# --------------------------------------------------------------------------

def _record_tail(collector, monkeypatch, result=()):
    recorded = {}

    def fake_get(path, params):
        recorded["path"] = path
        recorded["params"] = params
        return {"data": {"result": list(result)}}

    client = make_client(collector)
    monkeypatch.setattr(client, "_get", fake_get)
    out = client.tail(1_000_000, 3_000_000, [], "self-id")
    return recorded, out


def test_tail_reads_module_id_and_category_and_sorts(collector, monkeypatch):
    _, out = _record_tail(collector, monkeypatch, [
        {"stream": {"module_id": "loki1", "category": "security", "node_id": "2"},
         "values": [["3000000", "first"], ["1000000", "second"]]},
        {"stream": {"module_id": "traefik1", "node_id": "1"},
         "values": [["2000000", "third"]]},
    ])
    assert out == [
        (1000000, "second", "loki1", "security", 2),
        (2000000, "third", "traefik1", "", 1),
        (3000000, "first", "loki1", "security", 2),
    ]


def test_tail_reads_the_node_id_label(collector, monkeypatch):
    """node_id sits in the same per-series label map module_id and category
    come from, so node attribution costs no extra query -- it was being
    aggregated away, not fetched."""
    _, out = _record_tail(collector, monkeypatch, [
        {"stream": {"module_id": "loki1", "node_id": "3"},
         "values": [["1000000", "line"]]},
    ])
    assert out[0][4] == 3


@pytest.mark.parametrize("raw", [None, "", "0", "-1", "leader", "1.5"])
def test_tail_rejects_an_unusable_node_id(collector, monkeypatch, raw):
    """NS8 numbers nodes from 1, so 0 is a missing field rather than a
    machine and anything unparseable is not attribution at all."""
    stream = {"module_id": "loki1"}
    if raw is not None:
        stream["node_id"] = raw
    _, out = _record_tail(collector, monkeypatch, [
        {"stream": stream, "values": [["1000000", "line"]]},
    ])
    assert out[0][4] is None


def test_tail_keeps_nanoseconds(collector, monkeypatch):
    """The cursor is nanosecond-exact, so tail() must not round to
    milliseconds the way the old per-family lines() did."""
    _, out = _record_tail(collector, monkeypatch, [
        {"stream": {"module_id": "loki1"},
         "values": [["1757000000123456789", "line"]]},
    ])
    assert out[0][0] == 1757000000123456789


def test_tail_missing_module_id_label_is_the_host_bucket(collector, monkeypatch):
    """Host records (sshd, systemd, runagent) carry no module_id label at
    all, and they are the majority of security-relevant traffic."""
    _, out = _record_tail(collector, monkeypatch, [
        {"stream": {}, "values": [["1000000", "sshd line"]]},
    ])
    assert out[0][2] == collector.HOST_BUCKET


def test_tail_selector_carries_no_module_matcher(collector, monkeypatch):
    """One query for every module and the host bucket: a module matcher
    here would put the per-family fan-out back."""
    recorded, _ = _record_tail(collector, monkeypatch)
    query = recorded["params"]["query"]
    assert query.startswith('{node_id=~".+"}')
    assert "module_id" not in query.split("|")[0]


def test_tail_renders_the_same_line_format_as_before(collector, monkeypatch):
    """mask() must keep seeing byte-identical text, or every template on
    the fleet goes novel at once."""
    recorded, _ = _record_tail(collector, monkeypatch)
    assert recorded["params"]["query"].endswith(
        '| line_format "<{{.priority}}> [{{.identifier}}] {{.message}}"')


def test_tail_request_is_a_forward_bounded_page(collector, monkeypatch):
    recorded, _ = _record_tail(collector, monkeypatch)
    assert recorded["path"] == "/loki/api/v1/query_range"
    assert recorded["params"]["direction"] == "forward"
    assert recorded["params"]["start"] == "1000000"
    assert recorded["params"]["end"] == "3000000"
    assert recorded["params"]["limit"] == str(collector.TAIL_LIMIT)


def test_tail_propagates_loki_errors(collector, monkeypatch):
    """A failed tail must NOT look like an empty one: the caller has to
    leave its cursor where it was."""
    def fake_get(path, params):
        raise collector.LokiError("boom")

    client = make_client(collector)
    monkeypatch.setattr(client, "_get", fake_get)
    with pytest.raises(collector.LokiError):
        client.tail(0, 1, [], "self-id")
