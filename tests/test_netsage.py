import csv
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checker import run_checks
from engine import LLM_OUTPUT_SCHEMA, _validate_llm_result, load_config


class TestNetSageEngine(unittest.TestCase):
    def test_all_cases_route_as_designed(self):
        with open(ROOT / "data" / "cases.csv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertGreaterEqual(len(rows), 30)
        # Deterministic cases NET-001 through NET-013
        for row in rows[:13]:
            res = run_checks(row["show_outputs"])
            self.assertEqual(res["status"], "ERRORS_DETECTED", f"Expected error detected in {row['case_id']}")
        # LLM fallback cases NET-014 through NET-033
        for row in rows[13:]:
            res = run_checks(row["show_outputs"])
            self.assertEqual(res["status"], "NO_ERRORS_DETECTED", f"Expected clean pass to LLM in {row['case_id']}")

    def test_llm_schema_and_confidence_gate(self):
        config = load_config()
        self.assertNotIn("temperature", config["llm"])
        self.assertFalse(LLM_OUTPUT_SCHEMA["additionalProperties"])
        result = _validate_llm_result(
            {
                "root_cause": "Insufficient routing evidence.",
                "osi_layer": "Layer 3",
                "confidence": 0.5,
                "evidence": "The captured output does not contain a route to the destination.",
                "next_command": "show ip route",
                "fix_steps": ["Run the diagnostic command before changing configuration."],
            },
            config,
        )
        self.assertFalse(result["approval_allowed"])
        self.assertEqual(result["confidence_threshold"], 0.75)

    def test_llm_high_confidence_can_reach_hitl_gate(self):
        config = load_config()
        result = _validate_llm_result(
            {
                "root_cause": "The route is missing.",
                "osi_layer": "Layer 3",
                "confidence": 0.9,
                "evidence": "The destination prefix is absent from the routing table.",
                "next_command": "show ip route",
                "fix_steps": ["Verify the expected route source."],
            },
            config,
        )
        self.assertTrue(result["approval_allowed"])


if __name__ == "__main__":
    unittest.main()
