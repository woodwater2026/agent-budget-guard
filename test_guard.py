import unittest
from cost_calculator import BudgetGuard

class TestBudgetGuard(unittest.TestCase):
    def setUp(self):
        # BudgetGuard now loads from config.json by default
        self.guard = BudgetGuard()

    def test_cost_estimation(self):
        # Claude 3.5 Sonnet: $3.00/1M in, $15.00/1M out
        # 100k in, 10k out = (0.1 * 3.0) + (0.01 * 15.0) = 0.3 + 0.15 = 0.45
        cost = self.guard.estimate_cost("claude-3-5-sonnet", 100_000, 10_000)
        self.assertAlmostEqual(cost, 0.45)

    def test_budget_check_pass(self):
        ok, msg = self.guard.check_budget(0.04, "routine")
        self.assertTrue(ok)
        self.assertEqual(msg, "Budget OK.")

    def test_budget_check_fail(self):
        ok, msg = self.guard.check_budget(0.06, "routine")
        self.assertFalse(ok)
        self.assertIn("ALERT", msg)

if __name__ == "__main__":
    unittest.main()
