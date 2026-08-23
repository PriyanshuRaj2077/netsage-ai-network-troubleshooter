# NetSage AI — Submission Notes

## Demonstration scenario

NET-001 demonstrates inter-VLAN routing diagnosis. PC1 in VLAN 10 cannot reach Server1 in VLAN 30 because R1's `GigabitEthernet0/0.30` sub-interface is administratively down.

## What NetSage does

1. Loads the captured Cisco IOS output.
2. Runs deterministic checks first.
3. Detects the administratively-down sub-interface.
4. Produces structured root cause, OSI layer, confidence, evidence and remediation.
5. Presents the remediation to a human operator.
6. Records the operator decision in the audit log.

## Safety boundary

NetSage AI in this submission does **not** directly execute Cisco commands. The operator applies the approved command manually in Cisco Packet Tracer. This keeps the human-in-the-loop gate genuine and avoids claiming an integration that is not implemented.

## Packet Tracer artifact

The `.pkt` file must be created and saved using Cisco Packet Tracer. The `packet_tracer/` directory contains the exact topology, addressing and CLI configuration needed to create it.


## Final submission claim

Do not claim automatic Cisco deployment. The submission demonstrates automated diagnosis and remediation proposal, followed by human approval and manual application in Cisco Packet Tracer.

## Final demo sequence

1. Open `packet_tracer/NetSage_AI_NET001.pkt` after creating it in Cisco Packet Tracer.
2. Verify PC1 cannot reach Server1 while `Gi0/0.30` is administratively down.
3. Run NET-001 in the Streamlit dashboard.
4. Show the deterministic diagnosis and proposed `no shutdown` remediation.
5. Approve the fix in NetSage AI; the approval is recorded, not executed.
6. Apply `no shutdown` manually on R1 in Packet Tracer.
7. Verify `Gi0/0.30` is up/up and ping Server1 from PC1.
8. Show the new audit-log entry.
