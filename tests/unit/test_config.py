#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#
import pytest


LOKI_ENV = {
    "LOKI_ADDR": "10.5.4.1",
    "LOKI_HTTP_PORT": "20003",
    "LOKI_API_AUTH_USERNAME": "loki",
    "LOKI_API_AUTH_PASSWORD": "s3cret",
    "LOKI_RETENTION_PERIOD": "365",
}


def test_loki_endpoint_uses_published_address(collector):
    assert collector.loki_endpoint(LOKI_ENV) == (
        "http://10.5.4.1:20003", "loki", "s3cret")


@pytest.mark.parametrize("missing", [
    "LOKI_ADDR", "LOKI_HTTP_PORT",
    "LOKI_API_AUTH_USERNAME", "LOKI_API_AUTH_PASSWORD",
])
def test_loki_endpoint_names_the_missing_variable(collector, missing):
    env = dict(LOKI_ENV)
    del env[missing]
    with pytest.raises(KeyError) as excinfo:
        collector.loki_endpoint(env)
    assert excinfo.value.args[0] == missing


def test_loki_endpoint_of_empty_environment_fails(collector):
    with pytest.raises(KeyError):
        collector.loki_endpoint({})


@pytest.mark.parametrize("environ,expected", [
    ({"INSIGHTS_ENABLED": "1"}, True),
    ({"INSIGHTS_ENABLED": "0"}, False),
    ({"INSIGHTS_ENABLED": ""}, False),
    ({}, False),
])
def test_is_enabled(collector, environ, expected):
    assert collector.is_enabled(environ) is expected


def test_disabled_daemon_exits_before_touching_loki(collector, monkeypatch):
    monkeypatch.delenv("INSIGHTS_ENABLED", raising=False)

    def boom():
        raise AssertionError("Loki must not be resolved when disabled")

    monkeypatch.setattr(collector, "read_loki_environment", boom)
    assert collector.main(["--daemon"]) == 0


def test_missing_loki_fails_cleanly(collector, monkeypatch, capsys):
    monkeypatch.setenv("INSIGHTS_ENABLED", "1")
    monkeypatch.setattr(collector, "read_loki_environment", lambda: {})
    assert collector.main(["--daemon"]) == 1
    assert "LOKI_ADDR" in capsys.readouterr().err
