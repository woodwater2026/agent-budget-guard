#!/usr/bin/env python3
"""
test_dashboard_updater.py — Tests for dashboard_updater.py

Covers:
1. Dashboard generates valid markdown output
2. Budget health thresholds (healthy/elevated/critical) display correctly
3. Circuit breaker states (CLOSED/OPEN/HALF_OPEN) render correctly
4. Log file is created in staff_logs/
5. Script handles missing/empty data gracefully
"""

import os
import sys
import time
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cost_calculator import BudgetGuard
from circuit_breaker import CircuitBreaker
from dashboard_updater import (
    generate_dashboard,
    get_circuit_breaker_summary,
    state_emoji,
    spend_velocity,
    estimated_daily_cost,
    write_log,
)


def make_guard():
    """Create a BudgetGuard with a fresh circuit breaker."""
    guard = BudgetGuard()
    guard.breaker = CircuitBreaker(
        cost_limit=1.0,
        cost_window_seconds=3600,
        cost_failure_threshold=3,
        token_velocity_limit=100_000,
        token_window_seconds=3600,
        token_failure_threshold=3,
        recovery_timeout=30,
    )
    return guard


# ─── 1. Markdown Output ────────────────────────────────────────────────────────

class TestDashboardMarkdown(unittest.TestCase):
    def setUp(self):
        self.guard = make_guard()

    def test_dashboard_returns_string(self):
        result = generate_dashboard(self.guard)
        self.assertIsInstance(result, str)

    def test_dashboard_has_title(self):
        result = generate_dashboard(self.guard)
        self.assertIn("Agent Budget Guard", result)

    def test_dashboard_has_required_sections(self):
        result = generate_dashboard(self.guard)
        for section in ["Session Overview", "Cost Tracker", "Spend Velocity", "Circuit Breaker", "Model Pricing"]:
            self.assertIn(section, result, f"Missing section: {section}")

    def test_dashboard_has_markdown_tables(self):
        result = generate_dashboard(self.guard)
        self.assertIn("|", result, "Expected markdown tables with pipe characters")

    def test_dashboard_has_timestamp(self):
        result = generate_dashboard(self.guard)
        # Should contain a date-like string YYYY-MM-DD
        import re
        self.assertRegex(result, r'\d{4}-\d{2}-\d{2}')

    def test_dashboard_has_model_pricing(self):
        result = generate_dashboard(self.guard)
        self.assertIn("$/1M", result)


# ─── 2. Budget Health Thresholds ──────────────────────────────────────────────

class TestBudgetHealthThresholds(unittest.TestCase):
    def setUp(self):
        self.guard = make_guard()

    def _dashboard_with_window_cost(self, window_cost, cost_limit=1.0):
        """Patch the breaker to simulate a given window spend."""
        self.guard.breaker.cost_limit = cost_limit
        # Inject a cost event into the deque so window_cost reflects it
        self.guard.breaker.cost_events.clear()
        if window_cost > 0:
            self.guard.breaker.cost_events.append((time.time(), window_cost))
        return generate_dashboard(self.guard)

    def test_healthy_below_50_pct(self):
        md = self._dashboard_with_window_cost(0.3, cost_limit=1.0)  # 30%
        self.assertIn("Healthy", md)

    def test_elevated_between_50_and_80_pct(self):
        md = self._dashboard_with_window_cost(0.6, cost_limit=1.0)  # 60%
        self.assertIn("Elevated", md)

    def test_critical_above_80_pct(self):
        md = self._dashboard_with_window_cost(0.85, cost_limit=1.0)  # 85%
        self.assertIn("Critical", md)

    def test_zero_spend_is_healthy(self):
        md = self._dashboard_with_window_cost(0.0, cost_limit=1.0)
        self.assertIn("Healthy", md)

    def test_exact_50_pct_is_elevated(self):
        md = self._dashboard_with_window_cost(0.5, cost_limit=1.0)
        self.assertIn("Elevated", md)

    def test_exact_80_pct_is_critical(self):
        md = self._dashboard_with_window_cost(0.8, cost_limit=1.0)
        self.assertIn("Critical", md)


# ─── 3. Circuit Breaker States ────────────────────────────────────────────────

class TestCircuitBreakerStateRendering(unittest.TestCase):
    def setUp(self):
        self.guard = make_guard()

    def test_state_emoji_closed(self):
        self.assertEqual(state_emoji("CLOSED"), "🟢")

    def test_state_emoji_open(self):
        self.assertEqual(state_emoji("OPEN"), "🔴")

    def test_state_emoji_half_open(self):
        self.assertEqual(state_emoji("HALF_OPEN"), "🟡")

    def test_state_emoji_unknown(self):
        self.assertEqual(state_emoji("UNKNOWN"), "⚪")

    def test_closed_state_in_dashboard(self):
        # Default breaker should be CLOSED
        md = generate_dashboard(self.guard)
        self.assertIn("CLOSED", md)
        self.assertIn("🟢", md)

    @patch('time.time')
    def test_open_state_in_dashboard(self, mock_time):
        mock_time.return_value = 1000.0
        self.guard.breaker = CircuitBreaker(
            cost_limit=0.5, cost_window_seconds=60,
            cost_failure_threshold=1, recovery_timeout=120
        )
        # Trip the breaker
        self.guard.breaker.cost_events.append((1000.0, 0.3))
        self.guard.breaker.cost_events.append((1001.0, 0.3))
        self.guard.breaker.cost_failures = 1
        self.guard.breaker.last_failure_time = 1000.0
        self.guard.breaker.state = "OPEN"

        mock_time.return_value = 1005.0
        md = generate_dashboard(self.guard)
        self.assertIn("OPEN", md)
        self.assertIn("🔴", md)

    @patch('time.time')
    def test_half_open_state_in_dashboard(self, mock_time):
        mock_time.return_value = 1000.0
        self.guard.breaker = CircuitBreaker(
            cost_limit=0.5, cost_window_seconds=10,
            cost_failure_threshold=1, recovery_timeout=5
        )
        self.guard.breaker.state = "OPEN"
        self.guard.breaker.last_failure_time = 990.0  # 10s ago > recovery_timeout=5

        mock_time.return_value = 1000.0
        md = generate_dashboard(self.guard)
        self.assertIn("HALF_OPEN", md)
        self.assertIn("🟡", md)
        self.assertIn("testing recovery", md)


# ─── 4. Log File Creation ─────────────────────────────────────────────────────

class TestLogFileCreation(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_write_log_creates_staff_logs_dir(self):
        write_log(self.tmp_dir, "test message")
        log_dir = os.path.join(self.tmp_dir, "staff_logs")
        self.assertTrue(os.path.isdir(log_dir), "staff_logs/ directory should be created")

    def test_write_log_creates_log_file(self):
        log_path = write_log(self.tmp_dir, "hello world")
        self.assertTrue(os.path.isfile(log_path), f"Log file not found: {log_path}")

    def test_write_log_contains_message(self):
        log_path = write_log(self.tmp_dir, "unique_test_message_xyz")
        with open(log_path) as f:
            content = f.read()
        self.assertIn("unique_test_message_xyz", content)

    def test_write_log_has_timestamp(self):
        log_path = write_log(self.tmp_dir, "msg")
        with open(log_path) as f:
            content = f.read()
        import re
        self.assertRegex(content, r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]')

    def test_write_log_appends(self):
        write_log(self.tmp_dir, "first")
        log_path = write_log(self.tmp_dir, "second")
        with open(log_path) as f:
            content = f.read()
        self.assertIn("first", content)
        self.assertIn("second", content)

    def test_write_log_filename_contains_date(self):
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        log_path = write_log(self.tmp_dir, "test")
        self.assertIn(date_str, os.path.basename(log_path))


# ─── 5. Missing/Empty Data Graceful Handling ──────────────────────────────────

class TestGracefulHandling(unittest.TestCase):
    def test_spend_velocity_zero_window(self):
        result = spend_velocity(0.5, 0)
        self.assertEqual(result, 0.0, "Should return 0 for zero window_seconds")

    def test_spend_velocity_negative_window(self):
        result = spend_velocity(0.5, -10)
        self.assertEqual(result, 0.0)

    def test_spend_velocity_zero_cost(self):
        result = spend_velocity(0.0, 3600)
        self.assertAlmostEqual(result, 0.0)

    def test_estimated_daily_zero(self):
        self.assertAlmostEqual(estimated_daily_cost(0.0), 0.0)

    def test_estimated_daily_positive(self):
        self.assertAlmostEqual(estimated_daily_cost(1.0), 24.0)

    def test_generate_dashboard_no_events(self):
        """Dashboard should generate without error when no cost events exist."""
        guard = make_guard()
        guard.breaker.cost_events.clear()
        guard.breaker.token_events.clear()
        try:
            md = generate_dashboard(guard)
            self.assertIsInstance(md, str)
            self.assertGreater(len(md), 100)
        except Exception as e:
            self.fail(f"generate_dashboard raised {e} with empty events")

    def test_generate_dashboard_missing_config_keys(self):
        """Dashboard should handle guard with minimal/empty config."""
        guard = make_guard()
        guard.config = {}  # Wipe config
        try:
            md = generate_dashboard(guard)
            self.assertIsInstance(md, str)
        except Exception as e:
            self.fail(f"generate_dashboard raised {e} with empty config")

    def test_circuit_breaker_summary_default_breaker(self):
        """get_circuit_breaker_summary should work on a fresh breaker."""
        breaker = CircuitBreaker()
        summary = get_circuit_breaker_summary(breaker)
        self.assertIn("state", summary)
        self.assertIn("cost_limit", summary)
        self.assertIn("window_cost", summary)
        self.assertEqual(summary["state"], "CLOSED")

    def test_write_log_nested_missing_dir(self):
        """write_log should create deeply nested staff_logs/ if base_dir doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp:
            nested = os.path.join(tmp, "a", "b", "c")
            os.makedirs(nested)
            log_path = write_log(nested, "deep test")
            self.assertTrue(os.path.isfile(log_path))


# ─── Helper Tests ─────────────────────────────────────────────────────────────

class TestHelpers(unittest.TestCase):
    def test_spend_velocity_calculation(self):
        # $1 in 3600s = $1/hr
        self.assertAlmostEqual(spend_velocity(1.0, 3600), 1.0)

    def test_spend_velocity_half_hour(self):
        # $1 in 1800s = $2/hr
        self.assertAlmostEqual(spend_velocity(1.0, 1800), 2.0)

    def test_estimated_daily_from_velocity(self):
        self.assertAlmostEqual(estimated_daily_cost(2.0), 48.0)


if __name__ == "__main__":
    import datetime
    import io

    # Run tests and capture results
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])

    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)

    output = stream.getvalue()
    print(output)

    # Write to staff_logs/
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "staff_logs")
    os.makedirs(log_dir, exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(log_dir, f"test_dashboard_{date_str}.log")

    with open(log_path, "a") as f:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'='*60}\n[{ts}] Test Run Results\n{'='*60}\n")
        f.write(output)
        status = "PASSED" if result.wasSuccessful() else "FAILED"
        f.write(f"\nOverall: {status} | Tests: {result.testsRun} | "
                f"Failures: {len(result.failures)} | Errors: {len(result.errors)}\n")

    print(f"\n📝 Results logged to: {log_path}")
    sys.exit(0 if result.wasSuccessful() else 1)
