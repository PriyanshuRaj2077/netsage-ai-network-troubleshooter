import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from safety import validate_commands


class TestSafetyPolicy(unittest.TestCase):
    def test_safe_commands_pass(self):
        result = validate_commands(["configure terminal", "interface Gi0/0.30", "no shutdown"])
        self.assertTrue(result["safe"])
        self.assertEqual(result["blocked_commands"], [])

    def test_destructive_commands_are_blocked(self):
        result = validate_commands(["reload", "write erase", "show ip route"])
        self.assertFalse(result["safe"])
        self.assertIn("reload", result["blocked_commands"])
        self.assertIn("write erase", result["blocked_commands"])


if __name__ == "__main__":
    unittest.main()
