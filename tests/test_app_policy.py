import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from safety import validate_commands


class TestAppPolicy(unittest.TestCase):
    def test_manual_edit_cannot_contain_destructive_commands(self):
        result = validate_commands(["configure terminal", "reload"])
        self.assertFalse(result["safe"])
        self.assertEqual(result["blocked_commands"], ["reload"])


if __name__ == "__main__":
    unittest.main()
