"""
app.py — NetSage AI Streamlit Operations Dashboard.

Enterprise Infrastructure Troubleshooting & Human Oversight Gate.
Provides:
  - Live scenario inspection and hybrid diagnosis (deterministic first, LLM fallback second).
  - Human-in-the-Loop (HITL) review gate (Approve, Edit, Reject).
  - Visual analytics dashboard: issue types, severity, OSI layers, and agreement rates.
  - Interactive scenario dataset explorer.
  - Real-time audit trail and responsible AI log.
  - Step-by-step Cisco Packet Tracer demo walkthrough.

Run with:  streamlit run src/app.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Dict, Any, List

import pandas as pd
import streamlit as st

from engine import diagnose_case
from safety import validate_commands

BASE_DIR = Path(__file__).resolve().parent.parent
CASES_PATH = BASE_DIR / "data" / "cases.csv"
AUDIT_LOG_PATH = BASE_DIR / "docs" / "model_audit_log.md"
RESPONSIBLE_AI_LOG_PATH = BASE_DIR / "docs" / "responsible_ai_log.md"

ACTIONS = ("Approve & Deploy (Manual)", "Edit Commands", "Reject")

st.set_page_config(
    page_title="NetSage AI — Automated Network Diagnostic Platform",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_cases() -> pd.DataFrame:
    if not CASES_PATH.exists():
        st.error(f"Dataset not found at {CASES_PATH}")
        return pd.DataFrame()
    return pd.read_csv(CASES_PATH)


def parse_audit_log() -> pd.DataFrame:
    if not AUDIT_LOG_PATH.exists():
        return pd.DataFrame(columns=["Timestamp (UTC)", "Case ID", "Action", "Root Cause", "Engineer Note"])
    
    raw_lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    table_lines = [l.strip() for l in raw_lines if l.strip().startswith("|")]
    
    if len(table_lines) < 3:
        return pd.DataFrame(columns=["Timestamp (UTC)", "Case ID", "Action", "Root Cause", "Engineer Note"])
    
    rows = []
    for line in table_lines[2:]:  # skip header and divider
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 5:
            rows.append({
                "Timestamp (UTC)": cols[0],
                "Case ID": cols[1],
                "Action": cols[2],
                "Root Cause": cols[3],
                "Engineer Note": cols[4],
            })
    return pd.DataFrame(rows)


def append_audit_entry(case_id: str, action: str, root_cause: str, engineer_note: str = "") -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    root_cause = (root_cause or "").replace("|", "/").replace("\n", " ")
    engineer_note = (engineer_note or "").replace("|", "/").replace("\n", " ")
    line = f"| {timestamp} | {case_id} | {action} | {root_cause} | {engineer_note} |\n"
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    load_audit_metrics.clear()


@st.cache_data
def load_audit_metrics() -> Dict[str, Any]:
    df = parse_audit_log()
    if df.empty:
        return {
            "total_decisions": 0,
            "approved": 0,
            "edited": 0,
            "rejected": 0,
            "approval_rate": 0.0,
            "override_rate": 0.0,
            "rejection_rate": 0.0,
        }
    
    total = len(df)
    approved = len(df[df["Action"].str.contains("Approve", case=False, na=False)])
    edited = len(df[df["Action"].str.contains("Edit", case=False, na=False)])
    rejected = len(df[df["Action"].str.contains("Reject", case=False, na=False)])
    
    return {
        "total_decisions": total,
        "approved": approved,
        "edited": edited,
        "rejected": rejected,
        "approval_rate": round(approved / total * 100, 1) if total > 0 else 0.0,
        "override_rate": round(edited / total * 100, 1) if total > 0 else 0.0,
        "rejection_rate": round(rejected / total * 100, 1) if total > 0 else 0.0,
    }


# ==========================================
# Sidebar Controls & System Status
# ==========================================
with st.sidebar:
    st.image("https://raw.githubusercontent.com/feathericons/feather/master/icons/activity.svg", width=42)
    st.title("NetSage AI")
    st.caption("v1.0.1 Enterprise Infrastructure Diagnostic Engine")
    
    st.markdown("---")
    st.markdown("### 🛡️ System Operating Rules")
    st.info(
        "**Hybrid Architecture:**\n"
        "1. Static regex checker runs first.\n"
        "2. LLM reasoning used as fallback.\n"
        "3. Confidence threshold: **≥ 0.75**.\n"
        "4. **HITL Gate Mandatory:** Human must approve all remediation."
    )
    
    st.markdown("---")
    metrics = load_audit_metrics()
    st.markdown("### 📈 Live Audit Metrics")
    st.metric("Total Decisions Logged", metrics["total_decisions"])
    st.metric("Human Approval Rate", f"{metrics['approval_rate']}%")
    st.metric("Engineer Overrides (Edits)", metrics["edited"])
    st.metric("False Positives (Rejections)", metrics["rejected"])


# ==========================================
# Main Header
# ==========================================
st.title("🌐 NetSage AI: Automated Network Diagnostic Platform")
st.markdown(
    "**Applied AI & Human-in-the-Loop Network Troubleshooting for Cisco Packet Tracer Labs**"
)

cases_df = load_cases()
total_cases = len(cases_df)

# Top KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Active Scenarios", total_cases, help="Total multi-layer test scenarios in cases.csv")
kpi2.metric("Deterministic Rules", "13 Active", help="Regex signatures in checker.py")
kpi3.metric("Human Approval Rate", f"{metrics['approval_rate']}%", help="Approvals / Total Decisions")
kpi4.metric("Safety Guardrails", "Active", help="Destructive command policy enforced")

st.markdown("---")

# ==========================================
# Application Navigation Tabs
# ==========================================
tab_diag, tab_analytics, tab_dataset, tab_audit, tab_demo = st.tabs([
    "🔬 Diagnostic Lab & HITL Gate",
    "📊 Analytics & Agreement Dashboard",
    "📋 Case Dataset Explorer",
    "🛡️ Responsible AI & Audit Trail",
    "🧪 Packet Tracer Demo Walkthrough",
])

# ----------------------------------------------------
# TAB 1: Diagnostic Lab & Human-in-the-Loop Review Gate
# ----------------------------------------------------
with tab_diag:
    st.subheader("🔍 Scenario Inspection & Human Review Gate")
    st.caption("Select a scenario, inspect captured show-command output, run diagnostics, and review remediation.")

    col_select, col_filter = st.columns([2, 1])
    with col_filter:
        concepts = ["All Concepts"] + sorted(cases_df["concept_tag"].unique().tolist())
        selected_concept = st.selectbox("Filter by Domain:", concepts)

    filtered_cases = cases_df if selected_concept == "All Concepts" else cases_df[cases_df["concept_tag"] == selected_concept]
    
    with col_select:
        case_id = st.selectbox(
            "Select Case ID for Verification:",
            filtered_cases["case_id"].tolist(),
            format_func=lambda cid: f"{cid} — {filtered_cases[filtered_cases['case_id'] == cid]['symptom'].iloc[0][:60]}...",
        )

    case = cases_df[cases_df["case_id"] == case_id].iloc[0]

    if st.session_state.get("active_case_id") != case_id:
        st.session_state["active_case_id"] = case_id
        st.session_state.pop("last_result", None)
        st.session_state["editing"] = False

    # Scenario Details Card
    with st.expander("📌 Scenario Context & Captured Evidence", expanded=True):
        sc_col1, sc_col2 = st.columns([3, 1])
        with sc_col1:
            st.markdown(f"**Symptom:** {case['symptom']}")
            st.markdown(f"**Topology Note:** {case['topology_note']}")
        with sc_col2:
            st.markdown(f"**Domain:** `{case['concept_tag']}`")
            st.markdown(f"**OSI Layer:** `{case.get('osi_layer', 'Layer 2 / Layer 3')}`")
            st.markdown(f"**Severity:** `{'🔴 ' if case['severity'] == 'High' else '🟡 '}{case['severity']}`")

        st.markdown("**Captured Cisco IOS Show Output:**")
        st.code(case["show_outputs"], language="text")

    # Diagnostic Trigger
    run_col1, run_col2 = st.columns([1, 4])
    with run_col1:
        run_btn = st.button("▶ Run Diagnostic", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Analyzing captured telemetry with hybrid engine..."):
            try:
                result = diagnose_case(case.to_dict())
                st.session_state["last_result"] = result
            except Exception as e:
                st.session_state.pop("last_result", None)
                st.error(f"Diagnosis failed: {e}")

    # Display Diagnostic Results
    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        source = result.get("source", "unknown")
        confidence = result.get("confidence", 0.0)
        approval_allowed = result.get("approval_allowed", False)
        safety = result.get("safety", {"safe": True, "blocked_commands": []})

        st.markdown("---")
        st.subheader("💡 NetSage AI Diagnostic Recommendation")

        # Source badge
        if source == "deterministic_checker":
            st.success("⚡ **Fast-Path Deterministic Match**: Verified by static regex rule engine (100% confidence)")
        else:
            st.info("🧠 **LLM Reasoning Fallback**: Inferred via structured Claude prompt engine")

        # Key Diagnostic Fields
        dcol1, dcol2, dcol3 = st.columns([2, 1, 1])
        dcol1.markdown(f"**Root Cause:**\n> {result.get('root_cause', 'N/A')}")
        dcol2.metric("Target OSI Layer", result.get("osi_layer", "N/A"))
        dcol3.metric("Model Confidence", f"{confidence * 100:.0f}%")

        if not approval_allowed:
            if source == "llm_reasoning" and confidence < result.get("confidence_threshold", 0.75):
                st.warning(
                    f"⚠️ Low confidence diagnosis ({confidence:.2f} < {result.get('confidence_threshold', 0.75):.2f}). "
                    "Run additional verification commands before approving remediation."
                )
            if not safety.get("safe", True):
                st.error(
                    f"🚫 Safety policy blocked destructive commands: {', '.join(safety.get('blocked_commands', []))}. "
                    "Do not deploy these commands."
                )

        st.markdown(f"**Evidence Quoted from Show Output:**\n`{result.get('evidence', '')}`")
        st.markdown(f"**Recommended Next Verification Command:** `{result.get('next_command', '')}`")

        st.markdown("**Proposed Remediation CLI Commands:**")
        fix_text = "\n".join(result.get("fix_steps", []))
        st.code(fix_text, language="cisco")

        st.caption(f"Ground-Truth Reference Label: {case['expected_fault']}")

        # HITL Decision Gate
        st.markdown("---")
        st.subheader("🛡️ Engineer Verification & Human-in-the-Loop Gate")
        st.markdown("Select your operational decision before applying changes to Cisco Packet Tracer:")

        hcol1, hcol2, hcol3 = st.columns(3)
        with hcol1:
            approve = st.button(
                "✅ Approve & Deploy (Manual)",
                disabled=not approval_allowed,
                help="Requires confidence ≥ 0.75 and safe commands." if not approval_allowed else "Log approved fix for manual Packet Tracer entry.",
                use_container_width=True,
            )
        with hcol2:
            edit = st.button("✏️ Edit Commands", use_container_width=True)
        with hcol3:
            reject = st.button("❌ Reject (False Positive)", use_container_width=True)

        if approve:
            append_audit_entry(case_id, "Approve & Deploy (Manual)", result.get("root_cause", ""), "Approved by engineer for Packet Tracer lab execution")
            st.success(f"✅ Approval recorded in audit trail for {case_id}. NetSage does not execute commands directly.")
            st.rerun()

        if edit:
            st.session_state["editing"] = True

        if st.session_state.get("editing"):
            st.markdown("#### ✏️ Engineer Command Override")
            edited = st.text_area(
                "Modify CLI commands before deploying:",
                value="\n".join(result.get("fix_steps", [])),
                height=150,
            )
            note = st.text_input("Engineer Reason / Note:", placeholder="e.g. Corrected wildcard mask to 0.0.0.255")
            
            if st.button("💾 Confirm Edited Commands"):
                edited_commands = [line.strip() for line in edited.splitlines() if line.strip()]
                edit_safety = validate_commands(edited_commands)
                if not edit_safety["safe"]:
                    st.error(f"Blocked destructive command in edit: {', '.join(edit_safety['blocked_commands'])}")
                else:
                    append_audit_entry(
                        case_id,
                        "Edit Commands",
                        result.get("root_cause", ""),
                        engineer_note=f"Override: {note} | Commands: {edited.replace(chr(10), '; ')}",
                    )
                    st.session_state["editing"] = False
                    st.success(f"✏️ Edited remediation recorded for {case_id}.")
                    st.rerun()

        if reject:
            reason = st.text_input("Rejection Feedback / Root Cause Correction:", placeholder="e.g. AI misdiagnosed Layer 3 issue instead of encapsulation mismatch")
            if st.button("Confirm Rejection"):
                append_audit_entry(
                    case_id,
                    "Reject",
                    result.get("root_cause", ""),
                    engineer_note=f"False positive rejected: {reason}" if reason else "Flagged as false positive",
                )
                st.warning(f"❌ Rejection recorded in audit log for {case_id}.")
                st.rerun()

    else:
        st.info("👆 Click **'▶ Run Diagnostic'** to initiate deterministic verification and LLM reasoning.")


# ----------------------------------------------------
# TAB 2: Analytics & Agreement Dashboard
# ----------------------------------------------------
with tab_analytics:
    st.subheader("📊 Network Diagnostic Analytics & Agreement Metrics")
    st.caption("Comprehensive breakdown of issue domains, severity distribution, OSI layers, and human oversight agreement.")

    a_col1, a_col2 = st.columns(2)
    
    with a_col1:
        st.markdown("#### 🏷️ Scenarios by Network Domain (Concept Tags)")
        concept_counts = cases_df["concept_tag"].value_counts().reset_index()
        concept_counts.columns = ["Domain / Theme", "Case Count"]
        st.bar_chart(data=concept_counts.set_index("Domain / Theme"))

    with a_col2:
        st.markdown("#### 🎯 Scenarios by OSI Layer")
        osi_counts = cases_df["osi_layer"].value_counts().reset_index()
        osi_counts.columns = ["OSI Layer", "Case Count"]
        st.bar_chart(data=osi_counts.set_index("OSI Layer"))

    st.markdown("---")

    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.markdown("#### ⚠️ Scenarios by Severity Level")
        sev_counts = cases_df["severity"].value_counts().reset_index()
        sev_counts.columns = ["Severity", "Count"]
        st.dataframe(sev_counts, use_container_width=True, hide_index=True)

    with b_col2:
        st.markdown("#### 🛡️ Human-in-the-Loop Decision Breakdown")
        audit_df = parse_audit_log()
        if not audit_df.empty:
            action_counts = audit_df["Action"].value_counts().reset_index()
            action_counts.columns = ["Decision Action", "Count"]
            st.dataframe(action_counts, use_container_width=True, hide_index=True)
            st.metric("Human Approval Rate", f"{metrics['approval_rate']}%")
        else:
            st.info("No audit decisions recorded yet.")


# ----------------------------------------------------
# TAB 3: Case Dataset Explorer
# ----------------------------------------------------
with tab_dataset:
    st.subheader("📋 Cisco Packet Tracer Troubleshooting Dataset")
    st.caption(f"Total structured lab cases: **{total_cases}**")

    search_query = st.text_input("🔍 Search cases by symptom, concept, or fault:", placeholder="e.g. VLAN, DHCP, NAT, OSPF, ACL")
    
    view_df = cases_df.copy()
    if search_query:
        mask = (
            view_df["symptom"].str.contains(search_query, case=False, na=False)
            | view_df["concept_tag"].str.contains(search_query, case=False, na=False)
            | view_df["expected_fault"].str.contains(search_query, case=False, na=False)
            | view_df["case_id"].str.contains(search_query, case=False, na=False)
        )
        view_df = view_df[mask]

    st.dataframe(
        view_df[["case_id", "concept_tag", "osi_layer", "severity", "symptom", "expected_fault"]],
        use_container_width=True,
        hide_index=True,
    )

    csv_data = cases_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Complete cases.csv",
        data=csv_data,
        file_name="cases.csv",
        mime="text/csv",
    )


# ----------------------------------------------------
# TAB 4: Responsible AI & Audit Trail
# ----------------------------------------------------
with tab_audit:
    st.subheader("🛡️ Responsible AI Framework & Operational Audit Trail")
    st.caption("Immutable record of all engineer approvals, command overrides, and false positive flags.")

    audit_df = parse_audit_log()
    
    st.markdown("#### 📜 Live Human-in-the-Loop Audit Log")
    if not audit_df.empty:
        action_filter = st.selectbox("Filter Decisions:", ["All Actions"] + list(audit_df["Action"].unique()))
        display_audit = audit_df if action_filter == "All Actions" else audit_df[audit_df["Action"] == action_filter]
        st.dataframe(display_audit, use_container_width=True, hide_index=True)
    else:
        st.info("Audit log is currently empty.")

    st.markdown("---")
    st.markdown("#### 📚 Documented Human Correction Case Studies")
    st.caption("Key examples where human review intercepted AI mistakes to protect network stability:")

    with st.expander("Case 1: Destructive Command Safety Override (NET-009)", expanded=False):
        st.markdown(
            "**Symptom:** Port-security violation placed Fa0/5 in `err-disabled` state.\n"
            "**AI Proposal:** Proposed `write erase` and `reload`.\n"
            "**Human Review:** Safety policy blocked the commands. Engineer rejected the proposal and applied targeted `shutdown` / `no shutdown`.\n"
            "**Takeaway:** Safety guardrails must proactively block high-blast-radius commands."
        )

    with st.expander("Case 2: ACL Subnet Mask vs. Wildcard Mask Correction (NET-014)", expanded=False):
        st.markdown(
            "**Symptom:** ACL 101 blocking HTTP traffic due to `deny ip 192.168.10.0 255.255.255.0 any`.\n"
            "**AI Proposal:** Proposed `no ip access-group 101 in` (removing security controls completely).\n"
            "**Human Review:** Engineer edited the ACE to replace `255.255.255.0` with wildcard mask `0.0.0.255` without dropping security.\n"
            "**Takeaway:** Human expertise prevents AI from blindly disabling security features to restore connectivity."
        )

    with st.expander("Case 3: Static NAT Role Reversal vs. Hallucinated Routing (NET-020)", expanded=False):
        st.markdown(
            "**Symptom:** Static NAT server unreachable from the Internet due to reversed `ip nat inside/outside` interfaces.\n"
            "**AI Proposal:** AI hallucinated a missing ISP default route.\n"
            "**Human Review:** Engineer rejected false positive and corrected interface NAT assignments.\n"
            "**Takeaway:** Interface role semantics require human domain verification."
        )

    with st.expander("Case 4: Serial WAN Encapsulation Mismatch (NET-026)", expanded=False):
        st.markdown(
            "**Symptom:** Serial link shows `up/up` but drops all IP traffic (PPP vs HDLC).\n"
            "**AI Proposal:** AI saw line protocol 'up' and falsely inferred Layer 3 IP addressing error.\n"
            "**Human Review:** Engineer edited commands to standardize `encapsulation ppp` on both ends.\n"
            "**Takeaway:** Surface status indicators can mislead pure statistical reasoning."
        )

    with st.expander("Case 5: Guest Wi-Fi Isolation Failure (NET-031)", expanded=False):
        st.markdown(
            "**Symptom:** Guest Wi-Fi users in VLAN 50 can access internal corporate servers in VLAN 20.\n"
            "**AI Proposal:** AI suggested modifying DHCP DNS servers.\n"
            "**Human Review:** Engineer edited commands to apply `ip access-group GUEST-RESTRICT in` to sub-interface Gi0/0.50.\n"
            "**Takeaway:** Multi-symptom environments require human oversight to enforce security boundaries."
        )


# ----------------------------------------------------
# TAB 5: Packet Tracer Demo Walkthrough
# ----------------------------------------------------
with tab_demo:
    st.subheader("🧪 Cisco Packet Tracer Submission Demo: Scenario NET-001")
    st.markdown("**Inter-VLAN Routing Failure Reproduction, Diagnosis, Approval, and Manual Verification**")

    st.markdown("""
    ### 1. Scenario Context
    - **Topology:** PC1 (VLAN 10) ── SW1 (Trunk) ── R1 (Router-on-a-Stick: `Gi0/0.10` & `Gi0/0.30`) ── Server1 (VLAN 30)
    - **Addressing:**
      - PC1: `192.168.10.10/24` (Gateway `192.168.10.1`)
      - Server1: `192.168.30.10/24` (Gateway `192.168.30.1`)
      - R1 `Gi0/0.10`: `192.168.10.1/24` (Up/Up)
      - R1 `Gi0/0.30`: `192.168.30.1/24` (**Administratively Down**)
    """)

    st.markdown("### 2. Pre-Fix Verification (Failure State in Packet Tracer)")
    st.code("""PC1> ping 192.168.30.10
Pinging 192.168.30.10 with 32 bytes of data:
Request timed out.
Request timed out.
Request timed out.
Ping statistics for 192.168.30.10: Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)""", language="text")

    st.markdown("### 3. NetSage AI Automated Diagnosis")
    st.info("""
    - **Status:** `ERRORS_DETECTED` (Deterministic rule `CHK_INT_ADMIN_DOWN` matched)
    - **Root Cause:** Interface GigabitEthernet0/0.30 is administratively shut down.
    - **OSI Layer:** Layer 1 / Layer 2
    - **Confidence:** 1.0 (100%)
    - **Proposed Fix:**
      ```text
      configure terminal
      interface GigabitEthernet0/0.30
      no shutdown
      ```
    """)

    st.markdown("### 4. Human Approval Gate")
    st.success("✅ Operator reviews evidence in NetSage AI dashboard and clicks **'Approve & Deploy (Manual)'**. Decision is logged in `docs/model_audit_log.md`.")

    st.markdown("### 5. Manual Application in Cisco Packet Tracer")
    st.code("""R1# configure terminal
R1(config)# interface GigabitEthernet0/0.30
R1(config-subif)# no shutdown
R1(config-subif)# end
R1#
%LINK-5-CHANGED: Interface GigabitEthernet0/0.30, changed state to up
%LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/0.30, changed state to up""", language="cisco")

    st.markdown("### 6. Post-Fix Verification (Success)")
    st.code("""PC1> ping 192.168.30.10
Pinging 192.168.30.10 with 32 bytes of data:
Reply from 192.168.30.10: bytes=32 time<1ms TTL=127
Reply from 192.168.30.10: bytes=32 time<1ms TTL=127
Reply from 192.168.30.10: bytes=32 time<1ms TTL=127
Reply from 192.168.30.10: bytes=32 time<1ms TTL=127
Ping statistics for 192.168.30.10: Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)""", language="text")
