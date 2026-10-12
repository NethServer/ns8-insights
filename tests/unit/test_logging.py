#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#
import logging
import selectors
import subprocess
import sys
import time

import pytest

from conftest import SCRIPT

# Loads the collector in a child whose stdout and stderr are pipes, as under
# systemd, logs one line and then blocks on stdin until the test lets go.
CHILD = """
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("insights_collector", sys.argv[1])
spec = importlib.util.spec_from_loader("insights_collector", loader)
collector = importlib.util.module_from_spec(spec)
loader.exec_module(collector)
collector.setup_logging({"INSIGHTS_LOG_LEVEL": "info"})
collector.ship_bundle({"window": {"start": 0, "end": 900}, "templates": []},
                      "system-123", "secret", "http://127.0.0.1:9", True)
sys.stdin.read()
"""


def first_line_while_running(tmp_path, timeout=5.0):
    """(stream name, first line) the child writes, read before it exits, or
    None if nothing arrives within `timeout`."""
    child = subprocess.Popen(
        [sys.executable, "-c", CHILD, str(SCRIPT)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=tmp_path)
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ, "stdout")
    selector.register(child.stderr, selectors.EVENT_READ, "stderr")
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for key, _ in selector.select(deadline - time.monotonic()):
                line = key.fileobj.readline()
                if line:
                    return key.data, line.decode()
            assert child.poll() is None, "child exited before the test did"
        return None
    finally:
        child.stdin.close()
        child.wait(timeout=10)
        child.stdout.close()
        child.stderr.close()
        selector.close()


def test_status_line_reaches_a_pipe_while_running(tmp_path):
    # With stdout a pipe, a print() to stdout sits in the block buffer until
    # exit: the journal saw nothing for an hour, then every line at once,
    # stamped with the stop time.
    stream, line = first_line_while_running(tmp_path)
    assert stream == "stderr"
    assert "quiet, suppressed" in line


@pytest.fixture
def setup(collector):
    """setup_logging(), bound to pytest's captured stderr; conftest undoes
    it after the test."""
    return collector.setup_logging


@pytest.mark.parametrize("value,expected", [
    (None, ("warning", True)),
    ("", ("warning", True)),
    ("debug", ("debug", True)),
    (" INFO ", ("info", True)),
    ("Error", ("error", True)),
    ("verbose", ("warning", False)),
])
def test_log_level(collector, value, expected):
    environ = {} if value is None else {"INSIGHTS_LOG_LEVEL": value}
    assert collector.log_level(environ) == expected


def test_default_level_hides_info(collector, setup, capsys):
    setup({})
    collector.log.info("shipped")
    collector.log.warning("tail failed")
    err = capsys.readouterr().err
    assert "shipped" not in err
    assert "WARNING tail failed" in err


def test_debug_level_shows_everything(collector, setup, capsys):
    setup({"INSIGHTS_LOG_LEVEL": "debug"})
    collector.log.debug("tailed")
    collector.log.info("shipped")
    err = capsys.readouterr().err
    assert "DEBUG tailed" in err
    assert "INFO shipped" in err


def test_invalid_level_is_reported(collector, setup, capsys):
    setup({"INSIGHTS_LOG_LEVEL": "verbose"})
    assert "INSIGHTS_LOG_LEVEL=verbose is not one of" in capsys.readouterr().err
    assert collector.log.level == logging.WARNING


def test_journal_gets_priority_prefixes(collector):
    formatter = collector.JournalFormatter("%(message)s")
    record = logging.LogRecord("x", logging.ERROR, "", 0, "ship failed",
                               None, None)
    assert formatter.format(record) == "<3>ship failed"
    record.levelno = logging.DEBUG
    assert formatter.format(record) == "<7>ship failed"


def test_stderr_is_journal_needs_a_matching_stream(collector):
    assert not collector.stderr_is_journal({})
    assert not collector.stderr_is_journal({"JOURNAL_STREAM": "1:2"})


def test_main_sets_up_logging(collector, setup, monkeypatch, capsys):
    monkeypatch.delenv("INSIGHTS_ENABLED", raising=False)
    monkeypatch.setenv("INSIGHTS_LOG_LEVEL", "error")
    assert collector.main(["--daemon"]) == 0
    assert capsys.readouterr().err == ""
    assert collector.log.level == logging.ERROR
