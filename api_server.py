#!/usr/bin/env python3
"""
api_server.py — Lightweight HTTP API for Agent Budget Guard.

Endpoints:
  GET  /health     — {"ok": true}
  GET  /status     — budget status, circuit breaker state, spend velocity
  GET  /dashboard  — contents of dashboard.md as plain text
  POST /reset      — reset circuit breaker

Port: 8765 (env BUDGET_GUARD_PORT or --port arg)
Logs: staff_logs/api_YYYYMMDD.log
"""

import sys
import os
import json
import argparse
import logging
from datetime import datetime

# ── Resolve project root (file lives in project dir) ──────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from cost_calculator import BudgetGuard
from circuit_breaker import CircuitBreaker
from dashboard_updater import get_circuit_breaker_summary

# ── Logging setup ─────────────────────────────────────────────────────────────
def _setup_logger():
    log_dir = os.path.join(PROJECT_DIR, "staff_logs")
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(log_dir, f"api_{today}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("api_server")

logger = _setup_logger()

# ── Shared state (module-level singletons) ─────────────────────────────────────
_guard = BudgetGuard(config_path=os.path.join(PROJECT_DIR, "config.json"))
_breaker = _guard.breaker
_dashboard_path = os.path.join(PROJECT_DIR, "dashboard.md")

# ── Business logic helpers ────────────────────────────────────────────────────

def _get_status_data() -> dict:
    summary = get_circuit_breaker_summary(_breaker)
    # Compute total window spending directly from cost_events (avoids broken get_meter_data)
    _breaker._clean_old_events(_breaker.cost_events, _breaker.cost_window_seconds)
    total_window_spending = _breaker._get_current_sum(_breaker.cost_events)
    return {
        "circuit_breaker": summary,
        "budget": {
            "default_threshold": _guard.default_threshold,
            "thresholds": _guard.thresholds,
            "total_window_spending": total_window_spending,
            "window_seconds": _breaker.cost_window_seconds,
        },
        "spend_velocity": {
            "window_cost_usd": summary["window_cost"],
            "window_tokens": summary["window_tokens"],
            "cost_limit_usd": summary["cost_limit"],
            "token_velocity_limit": summary["token_velocity_limit"],
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def _reset_circuit_breaker() -> dict:
    _breaker.record_success()
    _breaker.cost_failures = 0
    _breaker.token_failures = 0
    _breaker.failures = 0
    _breaker.state = "CLOSED"
    logger.info("Circuit breaker reset via API")
    return {"reset": True, "state": _breaker.check_state()}


def _read_dashboard() -> str:
    if not os.path.exists(_dashboard_path):
        return "# Dashboard\n\n(No data yet — run dashboard_updater.py to generate.)\n"
    with open(_dashboard_path, "r") as f:
        return f.read()


# ── Try Flask first, fall back to stdlib http.server ─────────────────────────

try:
    from flask import Flask, jsonify, request, Response
    USING_FLASK = True
except ImportError:
    USING_FLASK = False

if USING_FLASK:
    # ── Flask implementation ───────────────────────────────────────────────────
    app = Flask(__name__)

    @app.before_request
    def _log_request():
        logger.info("REQUEST  %s %s from %s", request.method, request.path,
                    request.remote_addr)

    @app.after_request
    def _log_response(response):
        logger.info("RESPONSE %s %s → %s", request.method, request.path,
                    response.status_code)
        return response

    @app.route("/health")
    def health():
        return jsonify({"ok": True})

    @app.route("/status")
    def status():
        return jsonify(_get_status_data())

    @app.route("/dashboard")
    def dashboard():
        return Response(_read_dashboard(), mimetype="text/plain")

    @app.route("/reset", methods=["POST"])
    def reset():
        return jsonify(_reset_circuit_breaker())

    def run_server(port: int):
        logger.info("Starting Flask API server on port %d", port)
        app.run(host="0.0.0.0", port=port)

else:
    # ── stdlib http.server fallback ────────────────────────────────────────────
    import json as _json
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            logger.info("REQUEST  %s %s", self.command, self.path)

        def _send_json(self, data: dict, status: int = 200):
            body = _json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            logger.info("RESPONSE %s %s → %d", self.command, self.path, status)

        def _send_text(self, text: str, status: int = 200):
            body = text.encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            logger.info("RESPONSE %s %s → %d", self.command, self.path, status)

        def do_GET(self):
            if self.path == "/health":
                self._send_json({"ok": True})
            elif self.path == "/status":
                self._send_json(_get_status_data())
            elif self.path == "/dashboard":
                self._send_text(_read_dashboard())
            else:
                self._send_json({"error": "not found"}, 404)

        def do_POST(self):
            if self.path == "/reset":
                self._send_json(_reset_circuit_breaker())
            else:
                self._send_json({"error": "not found"}, 404)

    def run_server(port: int):
        logger.info("Starting stdlib http.server API on port %d (Flask not available)", port)
        server = HTTPServer(("0.0.0.0", port), _Handler)
        server.serve_forever()


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agent Budget Guard API Server")
    parser.add_argument(
        "--port", type=int,
        default=int(os.environ.get("BUDGET_GUARD_PORT", 8765)),
        help="Port to listen on (default 8765; env BUDGET_GUARD_PORT)",
    )
    args = parser.parse_args()
    run_server(args.port)


if __name__ == "__main__":
    main()
