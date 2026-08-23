"""
engine.py — NetSage AI orchestrator.

Pipeline for a single case:
  1. Run the deterministic rule checker first.
  2. If a known high-confidence pattern is found, return a deterministic
     diagnosis without calling the LLM.
  3. Otherwise, call Claude with Structured Outputs so the LLM response is
     guaranteed to match the expected JSON shape.
  4. Validate application-level constraints (especially confidence) before
     returning the result to the HITL dashboard.

No function in this module executes Cisco commands. It only proposes
remediation for a human engineer to review.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from checker import run_checks
from safety import validate_commands

try:
    import anthropic
except ImportError:
    anthropic = None

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_PATH = BASE_DIR / "prompts" / "diagnose_prompt.md"
CONFIG_PATH = BASE_DIR / "data" / "system_config.json"

# Anthropic Structured Outputs schema. This prevents malformed JSON and
# missing/wrongly-typed fields from reaching the dashboard.
LLM_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "root_cause": {"type": "string"},
        "osi_layer": {"type": "string"},
        "confidence": {"type": "number"},
        "evidence": {"type": "string"},
        "next_command": {"type": "string"},
        "fix_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "root_cause",
        "osi_layer",
        "confidence",
        "evidence",
        "next_command",
        "fix_steps",
    ],
    "additionalProperties": False,
}


def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt_template() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _checker_result_to_schema(case: Dict[str, Any], checker_result: Dict[str, Any]) -> Dict[str, Any]:
    """Format a deterministic checker hit into NetSage AI's structured output schema."""
    primary = checker_result["flagged_issues"][0]
    fix_steps = [line for line in primary["remediation"].splitlines() if line.strip()]
    safety = validate_commands(fix_steps)
    return {
        "source": "deterministic_checker",
        "status": checker_result["status"],
        "root_cause": primary["issue"],
        "osi_layer": primary["osi_layer"],
        "confidence": 1.0,
        "evidence": str(case.get("show_outputs", "")).strip(),
        "next_command": fix_steps[-1] if fix_steps else "",
        "fix_steps": fix_steps,
        "flagged_issues": checker_result["flagged_issues"],
        "approval_allowed": safety["safe"],
        "safety": safety,
    }


def _validate_llm_result(parsed: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate fields and apply the configured confidence gate."""
    required = ("root_cause", "osi_layer", "confidence", "evidence", "next_command", "fix_steps")
    missing = [field for field in required if field not in parsed]
    if missing:
        raise RuntimeError(f"LLM response is missing required fields: {', '.join(missing)}")

    if not isinstance(parsed["root_cause"], str) or not parsed["root_cause"].strip():
        raise RuntimeError("LLM field 'root_cause' must be a non-empty string")
    if not isinstance(parsed["osi_layer"], str) or not parsed["osi_layer"].strip():
        raise RuntimeError("LLM field 'osi_layer' must be a non-empty string")
    if not isinstance(parsed["evidence"], str):
        raise RuntimeError("LLM field 'evidence' must be a string")
    if not isinstance(parsed["next_command"], str):
        raise RuntimeError("LLM field 'next_command' must be a string")
    if not isinstance(parsed["fix_steps"], list) or not all(isinstance(step, str) for step in parsed["fix_steps"]):
        raise RuntimeError("LLM field 'fix_steps' must be a list of strings")

    try:
        confidence = float(parsed["confidence"])
    except (TypeError, ValueError) as exc:
        raise RuntimeError("LLM field 'confidence' must be a number") from exc

    if not 0.0 <= confidence <= 1.0:
        raise RuntimeError("LLM field 'confidence' must be between 0.0 and 1.0")

    threshold = float(config.get("thresholds", {}).get("min_confidence_for_auto_flag", 0.75))
    parsed["confidence"] = confidence
    safety = validate_commands(parsed["fix_steps"])
    parsed["safety"] = safety
    parsed["approval_allowed"] = confidence >= threshold and safety["safe"]
    parsed["confidence_threshold"] = threshold
    return parsed


def diagnose_with_llm(case: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback path: ask Claude to reason about a case the deterministic checker
    didn't recognize. Requires ANTHROPIC_API_KEY in the environment.
    """
    if anthropic is None:
        raise RuntimeError("The 'anthropic' package isn't installed. Run: pip install -r requirements.txt")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it before running the LLM fallback path."
        )

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = load_prompt_template()

    user_content = (
        f"Symptom: {case.get('symptom', '')}\n"
        f"Topology Note: {case.get('topology_note', '')}\n"
        f"Captured show output:\n{case.get('show_outputs', '')}\n\n"
        "Diagnose this case using only the supplied evidence."
    )

    # Claude Sonnet 5 rejects non-default sampling parameters such as
    # temperature. Structured Outputs is the supported way to guarantee the
    # JSON contract, so temperature is intentionally omitted here.
    response = client.messages.create(
        model=config["llm"]["model"],
        max_tokens=config["llm"]["max_tokens"],
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": LLM_OUTPUT_SCHEMA,
            }
        },
    )

    raw_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()
    if not raw_text:
        raise RuntimeError("LLM returned an empty response")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM returned invalid JSON despite Structured Outputs: {exc}") from exc

    parsed = _validate_llm_result(parsed, config)
    parsed["source"] = "llm_reasoning"
    parsed["status"] = "LLM_INFERRED"
    parsed["flagged_issues"] = []
    return parsed


def diagnose_case(case: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run deterministic checks first, then the LLM fallback when needed."""
    checker_result = run_checks(case.get("show_outputs", ""))

    if checker_result["status"] == "ERRORS_DETECTED":
        return _checker_result_to_schema(case, checker_result)

    config = config or load_config()
    return diagnose_with_llm(case, config)


if __name__ == "__main__":
    sample_case = {
        "case_id": "NET-001",
        "symptom": "PC1 cannot reach Server1 in VLAN 30",
        "topology_note": "PC1 on Fa0/1 (VLAN 10); Gateway on Router Sub-interface Gi0/0.10",
        "show_outputs": (
            "GigabitEthernet0/0.10 is up, line protocol is up\n"
            "GigabitEthernet0/0.30 is administratively down, line protocol is down\n"
        ),
    }
    print(json.dumps(diagnose_case(sample_case), indent=2))
