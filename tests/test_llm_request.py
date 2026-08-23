"""Offline contract test: verifies the Claude request omits temperature and uses Structured Outputs."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import engine


class FakeBlock:
    type = "text"
    text = '{"root_cause":"Test","osi_layer":"Layer 3","confidence":0.9,"evidence":"Test evidence","next_command":"show ip route","fix_steps":["Verify route"]}'


class FakeMessages:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return type("Response", (), {"content": [FakeBlock()]})()


class FakeAnthropic:
    def __init__(self, api_key):
        self.messages = FakeMessages()
        self.last = None


class TestLLMRequestContract(unittest.TestCase):
    def test_llm_request_contract(self):
        fake = FakeAnthropic("test")
        with patch.object(engine, "anthropic", type("AnthropicModule", (), {"Anthropic": lambda *args, **kwargs: fake})()):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
                result = engine.diagnose_with_llm(
                    {"symptom": "test", "topology_note": "test", "show_outputs": "test"},
                    engine.load_config(),
                )
                kwargs = fake.messages.kwargs
                self.assertNotIn("temperature", kwargs)
                self.assertEqual(kwargs["output_config"]["format"]["type"], "json_schema")
                self.assertEqual(result["source"], "llm_reasoning")


if __name__ == "__main__":
    unittest.main()
