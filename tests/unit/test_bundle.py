#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#
"""Tests for bundle assembly in insights-collector: is_quiet,
build_bundle, compute_window, ms and flush."""
import datetime

import pytest

from conftest import FakeLokiClient

UTC = datetime.timezone.utc


# --------------------------------------------------------------------------
# ms()
# --------------------------------------------------------------------------

def test_ms(collector):
    when = datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=UTC)
    assert collector.ms(when) == 1000


# --------------------------------------------------------------------------
# compute_window()
# --------------------------------------------------------------------------

def test_compute_window_snaps_to_15_minute_boundary(collector):
    now = datetime.datetime(2026, 9, 1, 10, 7, 23, 500000, tzinfo=UTC)
    start, end = collector.compute_window(now, minutes=15)
    assert end == datetime.datetime(2026, 9, 1, 10, 0, 0, tzinfo=UTC)
    assert start == datetime.datetime(2026, 9, 1, 9, 45, 0, tzinfo=UTC)


def test_compute_window_length_is_exactly_minutes(collector):
    now = datetime.datetime(2026, 9, 1, 10, 59, 59, tzinfo=UTC)
    start, end = collector.compute_window(now, minutes=15)
    assert (end - start) == datetime.timedelta(minutes=15)
    assert end.second == 0 and end.microsecond == 0
    assert end.minute % 15 == 0


def test_compute_window_already_on_boundary(collector):
    now = datetime.datetime(2026, 9, 1, 10, 0, 0, tzinfo=UTC)
    start, end = collector.compute_window(now, minutes=15)
    assert end == now
    assert start == now - datetime.timedelta(minutes=15)


# --------------------------------------------------------------------------
# is_quiet()
# --------------------------------------------------------------------------

def test_is_quiet_true_for_no_templates(collector):
    payload = {"templates": [], "digest": [{"observed": 5}]}
    assert collector.is_quiet(payload) is True


def test_is_quiet_false_when_templates_exist(collector):
    payload = {"templates": [{"template": "x", "count": 1}], "digest": []}
    assert collector.is_quiet(payload) is False


# --------------------------------------------------------------------------
# build_bundle()
# --------------------------------------------------------------------------

def test_build_bundle_carries_expected_fields(collector):
    digest_rows = [{"module_id": "loki1", "priority": 3, "observed": 5}]
    templates = [{"template": "x", "count": 1}]
    budget = {"max_lines": 500, "lines_seen": 10, "lines_kept": 3}
    bundle = collector.build_bundle(
        "system-123", "2.0.0", (1000, 2000), digest_rows, templates, budget)

    assert bundle["schema_version"] == collector.SCHEMA_VERSION
    assert bundle["masking_version"] == collector.MASKING_VERSION
    assert bundle["system_id"] == "system-123"
    assert bundle["collector_version"] == "2.0.0"
    assert bundle["window"] == {"start": 1000, "end": 2000}
    assert bundle["digest"] is digest_rows
    assert bundle["templates"] is templates
    assert bundle["budget"] is budget


# --------------------------------------------------------------------------
# flush(): templates[] carries module families while digest[] still
# carries instances.
# --------------------------------------------------------------------------

FLEET_LINES = [
    (1000, "<3> [{0}] disk full".format(module_id or "sshd"), module_id, "")
    for module_id in ["nethvoice1", "nethvoice2", "nethvoice3",
                      "openldap1", "openldap2", ""]
]


def test_flush_templates_carry_families(flush_lines):
    bundle = flush_lines(FLEET_LINES)
    assert {t["module_id"] for t in bundle["templates"]} == {
        "nethvoice", "openldap", ""}


def test_flush_digest_still_carries_instances(flush_lines):
    """Deliberate asymmetry: one instance flooding stays visible instead of
    being averaged out across its siblings."""
    bundle = flush_lines(FLEET_LINES)
    assert {row["module_id"] for row in bundle["digest"]} == {
        "nethvoice1", "nethvoice2", "nethvoice3",
        "openldap1", "openldap2", ""}


def test_flush_counts_every_ingested_line_in_the_digest(flush_lines):
    bundle = flush_lines(FLEET_LINES)
    assert sum(row["observed"] for row in bundle["digest"]) == len(FLEET_LINES)
    assert bundle["budget"]["lines_seen"] == len(FLEET_LINES)


def test_flush_digest_rows_carry_only_observed(flush_lines):
    """The 168-hour baseline behind `expected` is gone: per window it ran
    past the client timeout on a live cluster and loaded Loki for the tail
    it shares, and the server never read the result."""
    bundle = flush_lines(FLEET_LINES)
    for row in bundle["digest"]:
        assert set(row) == {"module_id", "priority", "observed"}


# --------------------------------------------------------------------------
# drain_range(): the catch-up paging loop.
# --------------------------------------------------------------------------

def _page(collector, count, first_ns=1000):
    return [(first_ns + i, "<6> [sshd] line {0}".format(i), "", "", 1)
            for i in range(count)]


def test_drain_range_stops_on_a_short_page(collector):
    client = FakeLokiClient(pages=[_page(collector, 3)])
    store = collector.TemplateStore()
    cursor = collector.drain_range(client, store, 0, 9999, "self-id")
    assert len(client.tail_calls) == 1
    assert cursor == 9999
    assert store.lines_seen == 3


def test_drain_range_keeps_reading_after_a_full_page(collector):
    """A full page means Loki had more to give. Advancing one page per tick
    would leave a busy node permanently behind."""
    full = _page(collector, collector.TAIL_LIMIT, first_ns=1000)
    client = FakeLokiClient(pages=[full, _page(collector, 2, first_ns=90000)])
    store = collector.TemplateStore()
    cursor = collector.drain_range(client, store, 0, 999999, "self-id")

    assert len(client.tail_calls) == 2
    # The second page resumes one nanosecond past the first page's last line.
    assert client.tail_calls[1][0] == full[-1][0] + 1
    assert cursor == 999999
    assert store.lines_seen == collector.TAIL_LIMIT + 2


def test_drain_range_leaves_the_cursor_alone_on_a_loki_error(collector):
    """The caller keeps its cursor, so the next tick re-reads the same
    range: a transient Loki restart costs a duplicate count, not a hole."""
    class Failing(FakeLokiClient):
        def tail(self, *args, **kwargs):
            raise collector.LokiError("boom")

    store = collector.TemplateStore()
    with pytest.raises(collector.LokiError):
        collector.drain_range(Failing(), store, 1234, 9999, "self-id")


def test_drain_range_honours_the_stop_flag(collector):
    full = _page(collector, collector.TAIL_LIMIT)
    client = FakeLokiClient(pages=[full, full])
    store = collector.TemplateStore()
    stop = {"flag": True}
    cursor = collector.drain_range(client, store, 500, 9999, "self-id", stop)
    assert client.tail_calls == []
    assert cursor == 500
