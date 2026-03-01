#!/usr/bin/env python3
"""
test_api_server.py — Unit tests for api_server.py

Uses stdlib http.server via threading so tests run without Flask dependency.
"""

import sys
import os
import json
import time
import threading
import unittest
import urllib.request
import urllib.error

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# Import server internals without starting it
import api_server


def _start_test_server(port=18765):
    """Start the stdlib test server in a daemon thread."""
    from http.server import HTTPServer
    import api_server as srv

    # Force stdlib path for testing predictability
    server = HTTPServer(("127.0.0.1", port), srv._Handler if not srv.USING_FLASK else _make_stdlib_handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)  # brief settle
    return server


def _make_stdlib_handler():
    """Return stdlib handler even when Flask is available."""
    from http.server import BaseHTTPRequestHandler
    import json as _json

    class _H(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _send_json(self, data, status=200):
            body = _json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_text(self, text, status=200):
            body = text.encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._send_json({"ok": True})
            elif self.path == "/status":
                self._send_json(api_server._get_status_data())
            elif self.path == "/dashboard":
                self._send_text(api_server._read_dashboard())
            else:
                self._send_json({"error": "not found"}, 404)

        def do_POST(self):
            if self.path == "/reset":
                self._send_json(api_server._reset_circuit_breaker())
            else:
                self._send_json({"error": "not found"}, 404)

    return _H


PORT = 18765
BASE = f"http://127.0.0.1:{PORT}"

# Start once for all tests
_server = _start_test_server(PORT)


def _get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return r.status, r.read().decode(), r.headers.get("Content-Type", "")


def _post(path, data=b""):
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, r.read().decode(), r.headers.get("Content-Type", "")


class TestHealth(unittest.TestCase):
    def test_health_ok(self):
        status, body, ct = _get("/health")
        self.assertEqual(status, 200)
        self.assertIn("application/json", ct)
        data = json.loads(body)
        self.assertTrue(data.get("ok"))


class TestStatus(unittest.TestCase):
    def test_status_200(self):
        status, body, ct = _get("/status")
        self.assertEqual(status, 200)
        self.assertIn("application/json", ct)

    def test_status_keys(self):
        _, body, _ = _get("/status")
        data = json.loads(body)
        self.assertIn("circuit_breaker", data)
        self.assertIn("budget", data)
        self.assertIn("spend_velocity", data)
        self.assertIn("timestamp", data)

    def test_circuit_breaker_state(self):
        _, body, _ = _get("/status")
        data = json.loads(body)
        self.assertIn(data["circuit_breaker"]["state"], ("CLOSED", "OPEN", "HALF_OPEN"))

    def test_spend_velocity_keys(self):
        _, body, _ = _get("/status")
        sv = json.loads(body)["spend_velocity"]
        for key in ("window_cost_usd", "window_tokens", "cost_limit_usd", "token_velocity_limit"):
            self.assertIn(key, sv)


class TestDashboard(unittest.TestCase):
    def test_dashboard_200(self):
        status, body, ct = _get("/dashboard")
        self.assertEqual(status, 200)
        self.assertIn("text/plain", ct)
        self.assertIsInstance(body, str)
        self.assertGreater(len(body), 0)


class TestReset(unittest.TestCase):
    def test_reset_returns_state(self):
        status, body, ct = _post("/reset")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data.get("reset"))
        self.assertIn(data.get("state"), ("CLOSED", "HALF_OPEN", "OPEN"))

    def test_reset_closes_open_breaker(self):
        # Force breaker open
        api_server._breaker.state = "OPEN"
        _, body, _ = _post("/reset")
        data = json.loads(body)
        self.assertEqual(data["state"], "CLOSED")


class TestNotFound(unittest.TestCase):
    def test_unknown_route(self):
        try:
            _get("/nonexistent")
            self.fail("Expected 404")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)


class TestBusinessLogic(unittest.TestCase):
    def test_get_status_data_structure(self):
        data = api_server._get_status_data()
        self.assertIsInstance(data["budget"]["total_window_spending"], (int, float))

    def test_read_dashboard_returns_string(self):
        result = api_server._read_dashboard()
        self.assertIsInstance(result, str)

    def test_reset_circuit_breaker(self):
        api_server._breaker.state = "OPEN"
        result = api_server._reset_circuit_breaker()
        self.assertTrue(result["reset"])
        self.assertEqual(result["state"], "CLOSED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
