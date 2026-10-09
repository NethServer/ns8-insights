#!/usr/bin/env python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

#
# Canned insights server for the Robot suite.
# No real server in CI: no network egress, no cost, deterministic.
#
#   python3 insights-stub.py [PORT] [RECORD_FILE]
#

import gzip
import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

RECORD_FILE = sys.argv[2] if len(sys.argv) > 2 else "/tmp/insights-stub.jsonl"

FINDINGS = [
    {
        "id": "01J8Z1K2M3N4P5Q6R7S8T9V0W1",
        "system_id": "robot",
        "fingerprint": "9f2b7e1c4a",
        "severity": "high",
        "title": "Robot open finding",
        "summary": "robot synthetic error logged far above baseline.",
        "suggested_action": "Nothing: this finding comes from the test stub.",
        "modules": ["robot-noise"],
        "evidence": ["<3> robot synthetic error <NUM>"],
        "status": "open",
        "occurrence_count": 1,
        "first_seen": 1754380811000,
        "last_seen": 1754381690000,
        "llm_model": "stub",
        "prompt_version": "v1",
        "security": False,
    },
    {
        "id": "01J8Z1K2M3N4P5Q6R7S8T9V0W2",
        "system_id": "robot",
        "fingerprint": "1c4a9f2b7e",
        "severity": "low",
        "title": "Robot stale finding",
        "summary": "An old finding.",
        "suggested_action": "Nothing.",
        "modules": ["robot-noise"],
        "evidence": [],
        "status": "stale",
        "occurrence_count": 3,
        "first_seen": 1754000000000,
        "last_seen": 1754100000000,
        "llm_model": "stub",
        "prompt_version": "v1",
        "security": False,
    },
]


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/logs/v1/bundles':
            self._send(404, b'not found')
            return
        length = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(length)
        if self.headers.get('Content-Encoding') == 'gzip':
            body = gzip.decompress(body)
        try:
            bundle = json.loads(body.decode())
        except ValueError:
            bundle = {}
        record = dict(bundle) if isinstance(bundle, dict) else {"bundle": bundle}
        record["auth"] = self.headers.get('Authorization', '')
        with open(RECORD_FILE, 'a') as handle:
            handle.write(json.dumps(record) + "\n")
        payload = json.dumps({"status": "accepted"}).encode()
        self._send(202, payload)

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        if url.path == '/logs/v1/findings':
            if not self.headers.get('Authorization', '').startswith('Basic '):
                self._send(401, b'{"error": "unauthorized"}')
                return
            status = urllib.parse.parse_qs(url.query).get('status', [None])[0]
            findings = [f for f in FINDINGS if status in (None, f['status'])]
            self._send(200, json.dumps({"findings": findings}).encode())
            return
        if url.path != '/':
            self._send(404, b'not found')
            return
        self._send(200, b'ok')

    def _send(self, status, body):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("insights-stub: " + (fmt % args) + "\n")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9099
    HTTPServer(('127.0.0.1', port), Handler).serve_forever()
