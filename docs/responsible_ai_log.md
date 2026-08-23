# NetSage AI — Responsible AI & Human Review Log

## Executive Summary & Responsible AI Framework

In enterprise networking and mission-critical infrastructure, **autonomous AI execution is unacceptably dangerous**. Direct deployment of AI-generated configuration commands carries catastrophic risks:
1. **Destructive Command Execution**: Accidental reboots, startup configuration erasures, or key zeroization causing enterprise-wide outages.
2. **Security Degradation**: AI removing ACLs or firewall rules entirely to "fix connectivity" rather than correcting precise wildcard masks or port definitions.
3. **Hallucinated Parameters**: Generating non-existent interface names, wrong IP subnets, or invalid next-hop gateways.
4. **Superficial Status Misinterpretation**: Misinterpreting "up/up" status while missing encapsulation or MTU mismatches.

To enforce responsible AI practices, **NetSage AI** mandates:
- **Deterministic-First Validation**: Known fault signatures are validated deterministically via static regex rules before any LLM inference.
- **Command Safety Policy Gate**: Proactive blocking of destructive commands (`reload`, `write erase`, `delete`, `format`, `crypto key zeroize`).
- **Confidence Gating**: LLM diagnoses with confidence below 0.75 are flagged with warnings and blocked from one-click approval.
- **Mandatory Human-in-the-Loop (HITL) Gate**: Every remediation is strictly a proposal requiring engineer review (Approve & Deploy, Edit Commands, or Reject).
- **Append-Only Model Audit Trail**: Logging all approvals, overrides, and false-positive rejections.

---

## Documented Human Correction Case Studies (5 Key Scenarios)

The following 5 cases demonstrate real-world scenarios where human review caught, corrected, or rejected AI output to protect network stability and security:

---

### Case 1: Destructive Command Safety Override & Blast-Radius Mitigation
- **Case ID**: `NET-009` / `NET-SAFETY-01`
- **Symptom**: Port Fa0/5 entered `err-disabled` status due to a sticky MAC port-security violation after swapping a user laptop.
- **AI Diagnosis & Proposal**:
  - *AI Root Cause*: Switchport state corrupted; full reload recommended.
  - *AI Proposed Commands*:
    ```text
    write erase
    reload
    ```
- **Why the AI Erred**: The LLM lacked domain blast-radius awareness and proposed resetting the entire switch to recover a single port.
- **Human Review Action**: **REJECTED & BLOCKED BY SAFETY GATE**.
  - NetSage AI's `safety.py` policy immediately flagged and blocked `write erase` and `reload`.
  - The engineer rejected the destructive proposal and applied the safe, targeted port recovery:
    ```text
    configure terminal
    interface FastEthernet0/5
    shutdown
    no shutdown
    ```
- **Responsible AI Lesson**: Automated safety policies must intercept destructive commands before they can ever reach production execution.

---

### Case 2: ACL Subnet Mask vs. Wildcard Mask Correction
- **Case ID**: `NET-014`
- **Symptom**: ACL 101 blocking legitimate HTTP traffic from 192.168.10.0/24 subnet to Server1.
- **Show Output Evidence**:
  ```text
  Extended IP access list 101
      10 deny ip 192.168.10.0 255.255.255.0 any
      20 permit ip any any
  ```
- **AI Diagnosis & Proposal**:
  - *AI Root Cause*: ACL 101 is blocking traffic.
  - *AI Proposed Commands*:
    ```text
    configure terminal
    interface GigabitEthernet0/0
    no ip access-group 101 in
    ```
- **Why the AI Erred**: The AI recognized that ACL 101 was blocking traffic, but instead of fixing the malformed wildcard mask, it proposed removing the entire access group, completely eliminating network security filtering.
- **Human Review Action**: **EDITED COMMANDS**.
  - The engineer utilized the "Edit Commands" interface to fix the exact Cisco wildcard mask without compromising security:
    ```text
    configure terminal
    ip access-list extended 101
    no 10
    10 deny ip host 192.168.10.0 any  # or correct to 10 deny ip 192.168.10.0 0.0.0.255 any
    end
    ```
- **Responsible AI Lesson**: AI frequently chooses the "path of least resistance" (removing all security rules). Human domain expertise is essential to preserve intended security policies.

---

### Case 3: Static NAT Interface Role Reversal vs. Hallucinated Routing Error
- **Case ID**: `NET-020`
- **Symptom**: Server1 (10.0.10.10) static NAT to public IP 203.0.113.10 is unreachable from the Internet.
- **Show Output Evidence**:
  ```text
  interface GigabitEthernet0/0 (LAN) -> ip nat outside
  interface GigabitEthernet0/0 (WAN) -> ip nat inside
  ```
- **AI Diagnosis & Proposal**:
  - *AI Root Cause*: ISP default route missing on R1.
  - *AI Proposed Commands*:
    ```text
    configure terminal
    ip route 0.0.0.0 0.0.0.0 203.0.113.1
    ```
- **Why the AI Erred**: The LLM hallucinated a missing default route because ping from the outside failed, failing to correlate that `ip nat outside` was mistakenly assigned to the internal interface.
- **Human Review Action**: **REJECTED (False Positive)**.
  - The engineer rejected the routing hypothesis and corrected the NAT interface assignments:
    ```text
    configure terminal
    interface GigabitEthernet0/0
    no ip nat outside
    ip nat inside
    interface GigabitEthernet0/1
    no ip nat inside
    ip nat outside
    ```
- **Responsible AI Lesson**: Correlation does not equal causation. Engineers must verify interface role semantics that models often misinterpret.

---

### Case 4: Serial WAN Encapsulation Mismatch Masked by Up/Up Status
- **Case ID**: `NET-026`
- **Symptom**: Leased line between R1 and R2 passes zero IP packets despite interface reporting `up/up`.
- **Show Output Evidence**:
  ```text
  R1: Serial0/0/0 is up, line protocol is up (Encapsulation PPP)
  R2: Serial0/0/0 is up, line protocol is up (Encapsulation HDLC)
  ```
- **AI Diagnosis & Proposal**:
  - *AI Root Cause*: Layer 3 IP address conflict or missing static route.
  - *AI Proposed Commands*:
    ```text
    configure terminal
    interface Serial0/0/0
    ip address 10.0.0.2 255.255.255.252
    ```
- **Why the AI Erred**: The LLM saw `line protocol is up` and prematurely ruled out Layer 2 issues, assuming the fault must be at Layer 3.
- **Human Review Action**: **EDITED COMMANDS**.
  - The engineer identified that Cisco HDLC keepalives can hold line protocol up temporarily while PPP LCP negotiations fail. The engineer edited the fix to standardize Layer 2 encapsulation:
    ```text
    configure terminal
    interface Serial0/0/0
    encapsulation ppp
    end
    ```
- **Responsible AI Lesson**: Multi-layer protocols can exhibit counterintuitive symptoms that confuse pure statistical reasoning.

---

### Case 5: Guest Wi-Fi Isolation Failure (Missing Interface ACL Binding)
- **Case ID**: `NET-031`
- **Symptom**: Guest Wi-Fi users in VLAN 50 can ping and open web consoles on internal accounting servers in VLAN 20.
- **Show Output Evidence**:
  ```text
  R1#show ip interface GigabitEthernet0/0.50 | include Inbound access list
    Inbound access list is not set
  R1#show access-lists GUEST-RESTRICT
  Standard IP access list GUEST-RESTRICT
      10 deny 192.168.20.0 0.0.0.255
      20 permit any
  ```
- **AI Diagnosis & Proposal**:
  - *AI Root Cause*: DHCP pool in VLAN 50 is handing out incorrect DNS server IP.
  - *AI Proposed Commands*:
    ```text
    ip dhcp pool GUEST-POOL
    dns-server 8.8.8.8
    ```
- **Why the AI Erred**: The AI confused a security isolation failure with a service discovery problem and proposed modifying the DHCP pool.
- **Human Review Action**: **EDITED COMMANDS**.
  - The engineer identified that the `GUEST-RESTRICT` ACL was defined in global config but never bound to the sub-interface. The engineer applied:
    ```text
    configure terminal
    interface GigabitEthernet0/0.50
    ip access-group GUEST-RESTRICT in
    end
    ```
- **Responsible AI Lesson**: Human review ensures that critical security isolation policies are actively enforced rather than misdiagnosed as routine service errors.

---

## Summary of Human Oversight Metrics

| Category | Count | Percentage |
|---|---|---|
| Total Human Decisions Logged | 15 | 100% |
| Approved & Deployed (Accurate AI Proposal) | 10 | 66.7% |
| Edited Commands (Refined by Engineer) | 3 | 20.0% |
| Rejected (False Positives / Blocked Destructive) | 2 | 13.3% |
| **Overall Human Agreement Rate** | **66.7%** | *(Healthy HITL gate filtering)* |
