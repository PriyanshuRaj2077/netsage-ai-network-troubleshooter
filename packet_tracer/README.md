# NetSage AI — Cisco Packet Tracer Submission Lab

This folder contains the manual build specification for the `.pkt` file used with the NetSage AI demo. Cisco Packet Tracer itself must be used to create and save the binary `.pkt` file.

## Goal

Reproduce the documented NET-001 scenario:

> PC1 cannot reach Server1 in VLAN 30 because Router sub-interface `GigabitEthernet0/0.30` is administratively down.

NetSage should detect the fault from the captured IOS output and propose:

```text
configure terminal
interface GigabitEthernet0/0.30
no shutdown
```

## Topology

```text
PC1 ---------------- SW1 ---------------- R1 ---------------- (VLAN 30 gateway)
Fa0/1                 Fa0/24              G0/0 trunk
VLAN 10               trunk               router-on-a-stick
  |                                         |
  |                                         +-- G0/0.10 = 192.168.10.1/24
  |                                         +-- G0/0.30 = 192.168.30.1/24
  |
  +------------------------------------- Server1 (VLAN 30 via SW1 Fa0/2)
```

Physical topology should be:

- 1 × Router (e.g. Cisco 2911)
- 1 × 2960 switch
- 1 × PC
- 1 × Server

Use copper straight-through links:

- PC1 `FastEthernet0` → SW1 `FastEthernet0/1`
- Server1 `FastEthernet0` → SW1 `FastEthernet0/2`
- SW1 `FastEthernet0/24` → R1 `GigabitEthernet0/0`

## Addressing

| Device | VLAN | IP | Gateway |
|---|---:|---|---|
| PC1 | 10 | 192.168.10.10/24 | 192.168.10.1 |
| Server1 | 30 | 192.168.30.10/24 | 192.168.30.1 |
| R1 G0/0.10 | 10 | 192.168.10.1/24 | — |
| R1 G0/0.30 | 30 | 192.168.30.1/24 | — |

## Build sequence

1. Place the four devices.
2. Cable them as described above.
3. Configure SW1 using `switch_config.txt`.
4. Configure R1 using `router_config.txt`.
5. Configure PC1 and Server1 with the addresses above.
6. Verify that VLAN 10 and VLAN 30 exist and the trunk is up.
7. **Before testing the fault, make sure R1 `G0/0.30` is shut down.** The supplied router configuration intentionally includes `shutdown` under the VLAN 30 sub-interface.
8. From PC1, ping `192.168.30.10`. It should fail.
9. Capture the output in `verification_commands.txt`.
10. Paste the relevant output into NetSage AI and run NET-001.
11. NetSage should identify the administratively-down sub-interface.
12. Manually apply the proposed fix in Packet Tracer:

```text
configure terminal
interface GigabitEthernet0/0.30
no shutdown
end
```

13. Ping `192.168.30.10` again. It should succeed.
14. Save the Packet Tracer file as `NetSage_AI_NET001.pkt`.

## Submission evidence

Recommended screenshots:

1. Complete Packet Tracer topology.
2. Failed PC1 → Server1 ping before remediation.
3. `show ip interface brief` showing `G0/0.30` administratively down.
4. NetSage diagnosis showing root cause, evidence, confidence and fix.
5. Human approval screen/audit entry.
6. Successful ping after `no shutdown`.
7. `show ip interface brief` showing the corrected interface state.
