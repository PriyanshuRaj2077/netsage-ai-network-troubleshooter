# Packet Tracer Submission Checklist

- [ ] Create the topology in Cisco Packet Tracer.
- [ ] Configure SW1 with VLAN 10, VLAN 30 and the trunk.
- [ ] Configure R1 router-on-a-stick.
- [ ] Configure PC1 as `192.168.10.10/24`, gateway `192.168.10.1`.
- [ ] Configure Server1 as `192.168.30.10/24`, gateway `192.168.30.1`.
- [ ] Leave `G0/0.30` administratively down for the initial fault state.
- [ ] Verify PC1 cannot ping Server1.
- [ ] Capture the `show` output containing `G0/0.30 is administratively down`.
- [ ] Run NET-001 in NetSage AI.
- [ ] Review evidence and proposed commands.
- [ ] Record the approval in NetSage.
- [ ] Manually execute `no shutdown` in Packet Tracer.
- [ ] Verify PC1 can ping Server1.
- [ ] Save the final file as `NetSage_AI_NET001.pkt`.
- [ ] Take screenshots of topology, fault, diagnosis, approval/audit, and successful remediation.
