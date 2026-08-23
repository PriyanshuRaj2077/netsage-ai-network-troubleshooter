# NetSage AI: Automated Network Diagnostic Platform

Enterprise-grade AI troubleshooting assistant for Cisco IOS / Packet Tracer lab environments. Combines a high-confidence deterministic regex rule engine with an LLM reasoning fallback, strictly gated behind a mandatory **Human-in-the-Loop (HITL)** verification step before any fix is accepted.

Built from the official technical documentation specification: hybrid diagnostics, strict JSON output schema, command safety guardrails, visual analytics dashboard, and responsible AI auditability.

---

## 🏗️ System Architecture & Workflow

```
Captured Show Telemetry / Symptom
               │
               ▼
┌────────────────────────────────────────┐
│  Tier 1: Deterministic Rule Checker    │ (checker.py - Fast, zero-cost, 100% confidence)
└──────────────────┬─────────────────────┘
                   │
         Match? ───┴───► YES ──┐
                   │           │
                   ▼ NO        │
┌──────────────────────────────┴─────────┐
│  Tier 2: LLM Reasoning Orchestrator   │ (engine.py + diagnose_prompt.md)
│  (Structured JSON + Confidence Gate)   │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│  Tier 3: Safety Guardrails & HITL Gate │ (app.py + safety.py)
│  [Approve & Deploy | Edit | Reject]    │ (Blocks reload, write erase, format, etc.)
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│  Tier 4: Model Audit & Responsible AI  │ (docs/model_audit_log.md)
└────────────────────────────────────────┘
```

The rule checker always executes first. The LLM acts purely as a semantic fallback for complex misconfigurations that static signatures cannot capture. **NetSage AI never directly executes commands on network hardware**; it generates verified proposals for human operator review and manual application in Cisco Packet Tracer.

---

## 📁 Project Structure

```
netsage-ai/
├── data/
│   ├── cases.csv                 33 multi-layer test cases (VLAN, DHCP, DNS, OSPF, ACL, NAT, Wireless)
│   └── system_config.json        Model, threshold, and safety configuration
├── prompts/
│   └── diagnose_prompt.md        System prompt: strict JSON schema, rules, 3 worked few-shot examples
├── src/
│   ├── app.py                    Streamlit operations & analytics dashboard (5 multi-view tabs)
│   ├── checker.py                Deterministic regex rule engine (13 active fault signatures)
│   ├── engine.py                 Diagnostic orchestrator (hybrid routing + JSON schema validator)
│   └── safety.py                 Command safety validator (blocks high-blast-radius commands)
├── docs/
│   ├── responsible_ai_log.md     5 in-depth case studies of human review corrections & AI failures
│   ├── model_audit_log.md        Append-only HITL audit log of approvals, edits, and rejections
│   ├── SUBMISSION.md             Demonstration flow and submission notes
│   └── FINAL_TEST_REPORT.md      Automated verification report
├── packet_tracer/
│   ├── README.md                 Step-by-step NET-001 topology and manual build specification
│   ├── router_config.txt         Cisco IOS router-on-a-stick initial configuration
│   ├── switch_config.txt         Cisco IOS switch trunking/access configuration
│   ├── verification_commands.txt Pre-fix and post-fix CLI validation outputs
│   └── submission_checklist.md   Submission verification checklist
├── scripts/
│   └── generate_cases.py         Dataset generator script for data/cases.csv
├── tests/
│   ├── test_netsage.py           Integration tests for case routing and confidence gates
│   ├── test_safety.py            Unit tests for destructive command blocking
│   ├── test_app_policy.py        Unit tests for manual edit safety policy
│   └── test_llm_request.py       Contract test for Claude structured schema
└── requirements.txt
```

---

## 🚀 Quickstart & Setup

### 1. Environment Setup
```bash
# Clone or navigate to the repository
cd netsage-ai

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows PowerShell / CMD
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Optional: Set LLM API Key (For LLM Fallback Cases)
Cases NET-001 through NET-013 run on the fast deterministic rule engine with **zero API key required**. To run the LLM fallback for cases NET-014 through NET-033, set your Anthropic API key:
```bash
setx ANTHROPIC_API_KEY "your-anthropic-api-key"   # Windows
# export ANTHROPIC_API_KEY="your-anthropic-api-key" # macOS/Linux
```

### 3. Run the Operations Dashboard
```bash
streamlit run src/app.py
```
Access the interactive dashboard at `http://localhost:8501`.

---

## 🧪 Automated Testing

Run the full automated test suite using Python's standard `unittest` or `pytest`:

```bash
# Run with Python standard library unittest
python -m unittest discover -s tests -v

# Or run with pytest
python -m pytest -v
```

All 7 test suites validate:
1. Deterministic vs LLM case routing across all 33 dataset scenarios.
2. Anthropic Structured Outputs JSON schema adherence.
3. Enforcement of the 0.75 confidence threshold.
4. Active blocking of destructive commands (`reload`, `write erase`, `delete`, `format`, `crypto key zeroize`).
5. Safe command validation during manual engineer overrides.

---

## 🛡️ Responsible AI & Human Oversight

NetSage AI is engineered specifically to prevent hallucinated or dangerous configuration changes:
- **Destructive Command Interception**: Commands with large blast radiuses are automatically blocked.
- **Confidence Gating**: LLM outputs with confidence < 0.75 require manual review before approval is unlocked.
- **Auditability**: Every operator action is permanently recorded with timestamps and engineer override notes in `docs/model_audit_log.md`.
- **Documented Corrections**: See `docs/responsible_ai_log.md` for 5 detailed case studies analyzing where AI erred and how human intervention prevented outages.

---

## 🎓 Packet Tracer Lab Demo (Scenario NET-001)

1. **Topology**: PC1 (VLAN 10) ── SW1 (Trunk) ── R1 (Router-on-a-Stick) ── Server1 (VLAN 30).
2. **Failure**: Sub-interface `GigabitEthernet0/0.30` is administratively down. Ping from PC1 to Server1 fails.
3. **NetSage Diagnosis**: Detects `CHK_INT_ADMIN_DOWN` deterministically; recommends `interface Gi0/0.30` → `no shutdown`.
4. **HITL Gate**: Operator approves fix in NetSage AI dashboard.
5. **Packet Tracer Fix**: Operator applies `no shutdown` on R1 in Packet Tracer.
6. **Verification**: PC1 pings Server1 with 100% success rate.
