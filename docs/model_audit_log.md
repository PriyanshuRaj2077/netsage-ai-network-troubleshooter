# NetSage AI — Model Audit Log

This log records every decision made at the Human-in-the-Loop (HITL)
gate: approvals, manual command edits, and rejections (false
positives). `app.py` appends one row per decision automatically.

The **Human Approval Rate** shown on the dashboard is computed
from this table as approved decisions divided by all recorded decisions.
Approval here means the engineer accepted the proposed fix for manual
execution in Packet Tracer; NetSage AI does not execute Cisco commands.

| Timestamp (UTC) | Case ID | Action | Root Cause | Engineer Note |
|---|---|---|---|---|
| 2026-08-23 18:15 UTC | NET-001 | Approve & Deploy (Manual) | Interface GigabitEthernet0/0.30 is administratively shut down. | Verified in Packet Tracer: no shutdown restored VLAN 30 connectivity. |
| 2026-08-23 18:22 UTC | NET-002 | Approve & Deploy (Manual) | Native VLAN mismatch detected on a trunk link. | switchport trunk native vlan 1 applied to SW2 Fa0/2. |
| 2026-08-23 18:30 UTC | NET-003 | Approve & Deploy (Manual) | VLAN 10 is referenced but does not exist in the VLAN database. | Created vlan 10 on SW3. |
| 2026-08-23 18:41 UTC | NET-004 | Approve & Deploy (Manual) | VLAN 40 is pruned from the trunk's allowed list. | Added VLAN 40 to Gi0/1 allowed trunk list. |
| 2026-08-23 18:50 UTC | NET-005 | Approve & Deploy (Manual) | No OSPF neighbors are listed on the expected interface. | Corrected area ID mismatch on transit link. |
| 2026-08-23 19:05 UTC | NET-006 | Approve & Deploy (Manual) | Destination network is unreachable; the routing table is likely missing a route. | Added static route to HQ subnet on R2. |
| 2026-08-23 19:18 UTC | NET-007 | Approve & Deploy (Manual) | No active NAT translations exist; inside/outside interface roles or the NAT ACL may be misconfigured. | Applied ip nat inside/outside to correct interfaces. |
| 2026-08-23 19:30 UTC | NET-008 | Approve & Deploy (Manual) | The DHCP pool has no available leases remaining. | Expanded DHCP pool address range. |
| 2026-08-23 19:42 UTC | NET-009 | Reject | Switchport state corrupted; full reload proposed by AI. | Blocked destructive reload; manual recovery with shut/no-shut applied. |
| 2026-08-23 19:55 UTC | NET-010 | Approve & Deploy (Manual) | A duplex mismatch was detected between two connected interfaces. | Configured speed/duplex auto on both ends. |
| 2026-08-23 20:10 UTC | NET-011 | Approve & Deploy (Manual) | IP routing is globally disabled on this multilayer switch, so SVIs cannot route between VLANs. | Enabled ip routing globally on SW-CORE. |
| 2026-08-23 20:25 UTC | NET-014 | Edit Commands | ACL 101 uses subnet mask instead of wildcard mask. | Replaced 255.255.255.0 with wildcard mask 0.0.0.255 instead of removing ACL. |
| 2026-08-23 20:40 UTC | NET-020 | Reject | AI falsely diagnosed missing ISP default route. | Flagged as false positive; corrected inside/outside NAT interface roles. |
| 2026-08-23 21:00 UTC | NET-026 | Edit Commands | AI misdiagnosed Layer 3 addressing error on up/up serial interface. | Edited remediation to set encapsulation ppp on both routers. |
| 2026-08-23 21:20 UTC | NET-031 | Edit Commands | AI proposed changing DHCP DNS server for guest Wi-Fi isolation. | Edited commands to apply ip access-group GUEST-RESTRICT in to sub-interface Gi0/0.50. |
| 2026-08-23 19:09 UTC | NET-001 | Approve & Deploy (Manual) | Interface GigabitEthernet0/0.30 is administratively shut down. | Approved by engineer for Packet Tracer lab execution |
| 2026-08-23 20:19 UTC | NET-001 | Approve & Deploy (Manual) | Interface GigabitEthernet0/0.30 is administratively shut down. | Approved by engineer for Packet Tracer lab execution |
| 2026-08-23 20:19 UTC | NET-001 | Approve & Deploy (Manual) | Interface GigabitEthernet0/0.30 is administratively shut down. | Approved by engineer for Packet Tracer lab execution |
