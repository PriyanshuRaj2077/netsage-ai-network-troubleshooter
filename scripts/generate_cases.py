"""
generate_cases.py — NetSage AI dataset generator.

Generates data/cases.csv with comprehensive multi-layer Cisco IOS / Packet Tracer
troubleshooting scenarios covering VLAN, Gateway/HSRP, DHCP, DNS, Routing, ACL,
NAT, and Wireless networks.

Each case record contains:
- case_id: Unique scenario identifier (NET-001 through NET-033)
- symptom: User-reported network failure symptom
- topology_note: Contextual network topology and addressing information
- osi_layer: Primary OSI layer associated with the failure
- concept_tag: Core network engineering domain tag
- severity: Incident severity level (High / Medium / Low)
- show_outputs: Captured Cisco IOS show command outputs
- expected_fault: Ground-truth root cause description
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_PATH = BASE_DIR / "data" / "cases.csv"

FIELDS = [
    "case_id",
    "symptom",
    "topology_note",
    "osi_layer",
    "concept_tag",
    "severity",
    "show_outputs",
    "expected_fault",
]

CASES = [
    dict(
        case_id="NET-001",
        symptom="PC1 cannot reach Server1 in VLAN 30",
        topology_note="PC1 on Fa0/1 (VLAN 10); Server1 on Fa0/2 (VLAN 30); R1 uses Gi0/0.10 and Gi0/0.30 as router-on-a-stick gateways.",
        osi_layer="Layer 1 / Layer 2",
        concept_tag="Inter-VLAN Routing",
        severity="High",
        show_outputs=(
            "GigabitEthernet0/0.10 is up, line protocol is up\n"
            "GigabitEthernet0/0.30 is administratively down, line protocol is down\n"
        ),
        expected_fault="Sub-interface administratively down",
    ),
    dict(
        case_id="NET-002",
        symptom="Hosts on VLAN 1 intermittently lose connectivity across the SW1-SW2 uplink",
        topology_note="SW1 Fa0/1 and SW2 Fa0/2 form the inter-switch trunk",
        osi_layer="Layer 2",
        concept_tag="VLAN Trunking",
        severity="Medium",
        show_outputs=(
            "SW1#show interfaces trunk\n"
            "Port        Mode         Encapsulation  Status        Native vlan\n"
            "Fa0/1       on           802.1q         trunking      1\n"
            "%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on FastEthernet0/1 (1), with SW2 FastEthernet0/2 (99)\n"
        ),
        expected_fault="Native VLAN mismatch on trunk link",
    ),
    dict(
        case_id="NET-003",
        symptom="Two PCs that should both be on VLAN 10 cannot reach each other after a new access switch was added",
        topology_note="New switch SW3 connects to SW1 via a trunk; PCs are on SW3 Fa0/2 and Fa0/3",
        osi_layer="Layer 2",
        concept_tag="VLAN Configuration",
        severity="High",
        show_outputs=(
            "SW3(config)#interface fastEthernet 0/2\n"
            "SW3(config-if)#switchport access vlan 10\n"
            "%% VLAN 10 not found in current VLAN database. Trying to create VLAN.\n"
        ),
        expected_fault="VLAN not present in VLAN database on SW3",
    ),
    dict(
        case_id="NET-004",
        symptom="PC on VLAN 30 can reach its own subnet but cannot reach hosts on VLAN 40 across the SW2-SW3 trunk",
        topology_note="VLAN 40 was recently added; trunk between SW2 and SW3 predates it",
        osi_layer="Layer 2",
        concept_tag="VLAN Trunking",
        severity="Medium",
        show_outputs=(
            "SW2#show interfaces gi0/1 switchport\n"
            "Name: Gi0/1\n"
            "Administrative Mode: trunk\n"
            "Trunking VLANs Enabled: 1,10,20,30\n"
            "VLAN 40 is not allowed on this trunk\n"
        ),
        expected_fault="VLAN 40 pruned from trunk allowed list",
    ),
    dict(
        case_id="NET-005",
        symptom="R1 and R2 are not exchanging any routes over the shared WAN link",
        topology_note="R1 Gi0/1 and R2 Gi0/1 share the 172.16.0.0/30 transit link, both configured for OSPF area 0",
        osi_layer="Layer 3",
        concept_tag="Dynamic Routing (OSPF)",
        severity="High",
        show_outputs=(
            "R1#show ip ospf neighbor\n"
            "\n"
            "R1#\n"
        ),
        expected_fault="No OSPF neighbor relationship formed (area/network statement mismatch)",
    ),
    dict(
        case_id="NET-006",
        symptom="A branch-office PC cannot reach the HQ file server",
        topology_note="Branch router R2 connects to HQ router R1 over a point-to-point serial link; no dynamic routing protocol is running",
        osi_layer="Layer 3",
        concept_tag="Static Routing",
        severity="High",
        show_outputs=(
            "R2#ping 10.0.50.10\n"
            "Type escape sequence to abort.\n"
            "Sending 5, 100-byte ICMP Echos to 10.0.50.10, timeout is 2 seconds:\n"
            "UUUUU\n"
            "Success rate is 0 percent (0/5)\n"
            "% Network is unreachable\n"
        ),
        expected_fault="Missing static route to HQ subnet on branch router",
    ),
    dict(
        case_id="NET-007",
        symptom="Internal hosts can ping each other but cannot reach any Internet address",
        topology_note="R1 Gi0/0 faces the internal LAN, Gi0/1 faces the ISP; NAT overload is intended on Gi0/1",
        osi_layer="Layer 3",
        concept_tag="NAT",
        severity="High",
        show_outputs=(
            "R1#show ip nat translations\n"
            "Pro Inside global      Inside local       Outside local      Outside global\n"
            "R1#\n"
        ),
        expected_fault="No active NAT translations (inside/outside interface roles likely misapplied)",
    ),
    dict(
        case_id="NET-008",
        symptom="New laptops added to the VLAN 10 lab are not receiving IP addresses",
        topology_note="Router-based DHCP pool DHCP-VLAN10 serves the lab; pool was sized for the original 20 devices",
        osi_layer="Layer 7 (Service)",
        concept_tag="DHCP",
        severity="Medium",
        show_outputs=(
            "R1#show ip dhcp pool DHCP-VLAN10\n"
            "Pool DHCP-VLAN10 :\n"
            " Utilization mark (high/low)    : 100 / 0\n"
            " Subnet size (first/last)       : 0 / 0\n"
            " Total addresses                : 20\n"
            " Leased addresses               : 20\n"
            " 0 leases available\n"
        ),
        expected_fault="DHCP pool exhausted",
    ),
    dict(
        case_id="NET-009",
        symptom="A lab PC lost all network access immediately after being swapped out for a different laptop",
        topology_note="Port Fa0/5 on SW1 has port security configured with a single sticky MAC allowed",
        osi_layer="Layer 2",
        concept_tag="Port Security",
        severity="Medium",
        show_outputs=(
            "SW1#show interfaces fastEthernet 0/5 status\n"
            "Port      Name               Status       Vlan       Duplex  Speed Type\n"
            "Fa0/5                        err-disabled 10           auto   auto 10/100BaseTX\n"
            "%PM-4-ERR_DISABLE: psecure-violation error detected on Fa0/5, putting Fa0/5 in err-disable state\n"
        ),
        expected_fault="Port security violation placed Fa0/5 in err-disabled state",
    ),
    dict(
        case_id="NET-010",
        symptom="File transfers between SW1 and SW2 are extremely slow and show interface errors",
        topology_note="SW1 Gi0/1 connects directly to SW2 Gi0/1 with a single copper link",
        osi_layer="Layer 1",
        concept_tag="Physical Layer",
        severity="Low",
        show_outputs=(
            "SW1#show interfaces gi0/1\n"
            "GigabitEthernet0/1 is up, line protocol is up\n"
            "  Full-duplex, 100Mb/s\n"
            "%CDP-4-DUPLEX_MISMATCH: duplex mismatch discovered on GigabitEthernet0/1 (not full duplex), with SW2 GigabitEthernet0/1 (full duplex)\n"
        ),
        expected_fault="Duplex mismatch between SW1 and SW2 uplink ports",
    ),
    dict(
        case_id="NET-011",
        symptom="A multilayer switch with correctly configured SVIs is not routing between any VLANs",
        topology_note="SW-CORE has SVIs for VLAN 10, 20, and 30, each with a valid IP address",
        osi_layer="Layer 3",
        concept_tag="Inter-VLAN Routing",
        severity="High",
        show_outputs=(
            "SW-CORE#show ip protocols\n"
            "IP routing: is disabled\n"
            "SW-CORE#show ip interface brief | include Vlan\n"
            "Vlan10                  10.0.10.1       YES manual up                    up\n"
            "Vlan20                  10.0.20.1       YES manual up                    up\n"
        ),
        expected_fault="IP routing globally disabled on the multilayer switch",
    ),
    dict(
        case_id="NET-012",
        symptom="PC4 has a valid IP address but cannot reach anything outside its own subnet",
        topology_note="PC4 connects through SW2 Fa0/3 to R1 Fa0/0, a directly connected point-to-point link (no switch in between)",
        osi_layer="Layer 1 / Layer 2",
        concept_tag="IP Addressing",
        severity="Medium",
        show_outputs=(
            "R1#show interfaces fastEthernet 0/0\n"
            "FastEthernet0/0 is up, line protocol is down\n"
            "  Encapsulation ARPA, loopback not set\n"
        ),
        expected_fault="Line protocol down, likely encapsulation or Layer 2 mismatch with the connected switch port",
    ),
    dict(
        case_id="NET-013",
        symptom="PC1 experiences intermittent connection dropouts and IP conflict warnings",
        topology_note="PC1 (192.168.10.50) on VLAN 10; Gateway on R1 Gi0/0.10 (192.168.10.1)",
        osi_layer="Layer 3",
        concept_tag="IP Addressing",
        severity="High",
        show_outputs=(
            "R1#show logging\n"
            "%IP-4-DUPADDR: Duplicate address 192.168.10.50 on GigabitEthernet0/0.10, sourced by 0001.96a2.bc01\n"
        ),
        expected_fault="Duplicate IP address conflict detected on the subnet",
    ),
    dict(
        case_id="NET-014",
        symptom="ACL 101 is blocking legitimate HTTP traffic from the 192.168.10.0/24 subnet to Server1",
        topology_note="ACL 101 is applied inbound on R1 Gi0/0, which faces the 192.168.10.0/24 subnet",
        osi_layer="Layer 3 / Layer 4",
        concept_tag="Access Control Lists",
        severity="High",
        show_outputs=(
            "R1#show access-lists 101\n"
            "Extended IP access list 101\n"
            "    10 deny ip 192.168.10.0 255.255.255.0 any\n"
            "    20 permit ip any any\n"
        ),
        expected_fault="ACL uses a subnet mask (255.255.255.0) instead of a wildcard mask (0.0.0.255), so it matches only one host instead of the intended /24 — combined with an implicit early deny, legitimate traffic is blocked",
    ),
    dict(
        case_id="NET-015",
        symptom="The redundant links between SW1 and SW2 are not bundling into an EtherChannel",
        topology_note="Two Gi links (Gi0/1, Gi0/2) connect SW1 and SW2 directly, intended to form Port-channel1",
        osi_layer="Layer 2",
        concept_tag="EtherChannel",
        severity="Medium",
        show_outputs=(
            "SW1#show etherchannel summary\n"
            "Group  Port-channel  Protocol    Ports\n"
            "1      Po1(SD)       LACP        Gi0/1(D)  Gi0/2(D)\n"
            "SW1#show running-config interface range gi0/1 - 2 | include channel-group\n"
            " channel-group 1 mode active\n"
            "SW2#show running-config interface range gi0/1 - 2 | include channel-group\n"
            " channel-group 1 mode on\n"
        ),
        expected_fault="Channel-group mode mismatch — SW1 uses LACP 'active', SW2 uses static 'on', which are incompatible negotiation modes",
    ),
    dict(
        case_id="NET-016",
        symptom="When the active router fails, the standby router never takes over the virtual IP",
        topology_note="R1 (priority 150) and R2 (priority 100) share HSRP group 1 on the 10.0.1.0/24 LAN, virtual IP 10.0.1.1",
        osi_layer="Layer 3",
        concept_tag="First Hop Redundancy (HSRP)",
        severity="Medium",
        show_outputs=(
            "R2#show standby brief\n"
            "                     P indicates configured to preempt.\n"
            "Interface   Grp  Pri P State    Active          Standby         Virtual IP\n"
            "Gi0/0       1    100   Standby  10.0.1.2        local           10.0.1.1\n"
        ),
        expected_fault="Preempt is not enabled on the HSRP group, so R2 never reclaims active role even after R1 recovers or fails permanently",
    ),
    dict(
        case_id="NET-017",
        symptom="Remote PCs on VLAN 50 receive a valid IP address from DHCP but cannot leave the subnet",
        topology_note="Router-based DHCP pool DHCP-VLAN50 serves 10.0.50.0/24; SVI Vlan50 has address 10.0.50.1",
        osi_layer="Layer 3 / Layer 7",
        concept_tag="IP Addressing",
        severity="Medium",
        show_outputs=(
            "R1#show ip dhcp pool DHCP-VLAN50\n"
            "Pool DHCP-VLAN50 :\n"
            " Network                        : 10.0.50.0 /24\n"
            " Default router                 : 10.0.50.254\n"
            " Lease time                     : 1 days\n"
        ),
        expected_fault="DHCP pool advertises the wrong default-router address (10.0.50.254 instead of the SVI's actual address 10.0.50.1)",
    ),
    dict(
        case_id="NET-018",
        symptom="R1 and R3 sit on the same LAN segment but are not learning routes from each other via RIP",
        topology_note="R1 and R3 both run 'router rip' on the shared 10.0.99.0/24 segment",
        osi_layer="Layer 3",
        concept_tag="RIP",
        severity="Medium",
        show_outputs=(
            "R1#show ip protocols | include version\n"
            "  Sending updates every 30 seconds, next due in 24 seconds\n"
            "  Invalid after 180 seconds, hold down 180, flushed after 240\n"
            "  Default version control: send version 1, receive version 1\n"
            "R3#show ip protocols | include version\n"
            "  Default version control: send version 2, receive version 2\n"
        ),
        expected_fault="RIP version mismatch between R1 (v1) and R3 (v2) prevents updates from being processed",
    ),
    dict(
        case_id="NET-019",
        symptom="A VLAN created on SW1 is not appearing in the VLAN database of any other switch in the domain",
        topology_note="SW1, SW2, and SW3 are all connected via trunks and share VTP domain 'CAMPUS'",
        osi_layer="Layer 2",
        concept_tag="VTP",
        severity="Medium",
        show_outputs=(
            "SW1#show vtp status | include Mode|Domain\n"
            "VTP Operating Mode                : Server\n"
            "VTP Domain Name                    : CAMPUS\n"
            "SW2#show vtp status | include Mode|Domain\n"
            "VTP Operating Mode                : Transparent\n"
            "VTP Domain Name                    : CAMPUS\n"
        ),
        expected_fault="SW2 is in VTP transparent mode, so it does not learn or forward VLAN database updates from SW1",
    ),
    dict(
        case_id="NET-020",
        symptom="A web server with a static NAT entry is unreachable from outside the network",
        topology_note="Server1 (10.0.10.10) has a static NAT mapping to public IP 203.0.113.10 on R1",
        osi_layer="Layer 3",
        concept_tag="NAT",
        severity="High",
        show_outputs=(
            "R1#show running-config | include ip nat|interface Gi\n"
            "interface GigabitEthernet0/0\n"
            " ip nat outside\n"
            "interface GigabitEthernet0/1\n"
            " ip nat inside\n"
            "ip nat inside source static 10.0.10.10 203.0.113.10\n"
        ),
        expected_fault="Inside/outside NAT roles are reversed — Gi0/0 (the internal LAN interface) is marked 'ip nat outside' and Gi0/1 (the ISP-facing interface) is marked 'ip nat inside'",
    ),
    dict(
        case_id="NET-021",
        symptom="PCs in the newly created VLAN 60 receive a self-assigned 169.254.x.x address",
        topology_note="DHCP for VLAN 60 is centrally hosted on R1; SVI Vlan60 lives on multilayer switch SW-CORE",
        osi_layer="Layer 3 / Layer 7",
        concept_tag="DHCP Relay",
        severity="High",
        show_outputs=(
            "SW-CORE#show running-config interface vlan 60\n"
            "interface Vlan60\n"
            " ip address 10.0.60.1 255.255.255.0\n"
        ),
        expected_fault="Missing 'ip helper-address' on the Vlan60 SVI, so DHCP DISCOVER broadcasts never reach the centralized DHCP server",
    ),
    dict(
        case_id="NET-022",
        symptom="Hosts intermittently see duplicate or looping routes between the OSPF core and the RIP-based branch network",
        topology_note="R1 redistributes RIP routes into OSPF and OSPF routes into RIP on the boundary router",
        osi_layer="Layer 3",
        concept_tag="Route Redistribution",
        severity="High",
        show_outputs=(
            "R1#show running-config | section router\n"
            "router ospf 1\n"
            " redistribute rip subnets\n"
            "router rip\n"
            " redistribute ospf 1 metric 1\n"
        ),
        expected_fault="Two-way redistribution with no route filtering or tagging creates a feedback loop between the OSPF and RIP domains",
    ),
    dict(
        case_id="NET-023",
        symptom="One host on SW1 can reach the file server, but its neighbor on the same switch cannot",
        topology_note="Both hosts are on SW1 VLAN 20; the file server ACL is applied on the SW1 SVI",
        osi_layer="Layer 3 / Layer 4",
        concept_tag="Access Control Lists",
        severity="High",
        show_outputs=(
            "SW1#show ip access-lists\n"
            "Extended IP access list FILESERVER-ACL\n"
            "    10 permit ip host 10.0.20.11 host 10.0.20.100\n"
            "    20 deny ip any host 10.0.20.100\n"
            "SW1#show running-config interface vlan 20 | include access-group\n"
            " ip access-group FILESERVER-ACL in\n"
        ),
        expected_fault="ACL only permits a single host (10.0.20.11) to reach the file server; every other host in VLAN 20 is caught by the explicit deny",
    ),
    dict(
        case_id="NET-024",
        symptom="A specific host (10.0.77.5) is unreachable even though R1 has a working default route",
        topology_note="R1's default route points to the ISP; 10.0.77.0/24 is a newly added internal subnet behind R2",
        osi_layer="Layer 3",
        concept_tag="Routing",
        severity="Medium",
        show_outputs=(
            "R1#show ip route | include Gateway|0.0.0.0/0\n"
            "Gateway of last resort is 198.51.100.1 to network 0.0.0.0\n"
            "S*   0.0.0.0/0 [1/0] via 198.51.100.1\n"
        ),
        expected_fault="No specific route to the new 10.0.77.0/24 subnet exists, so traffic to it is sent to the default route (ISP) instead of toward R2",
    ),
    dict(
        case_id="NET-025",
        symptom="Two devices with static IPs on what should be the same subnet cannot communicate at all",
        topology_note="PC-A and PC-B are both cabled to SW1 VLAN 30 with static IP addresses in the 10.0.30.0/24 range",
        osi_layer="Layer 3",
        concept_tag="IP Addressing",
        severity="Medium",
        show_outputs=(
            "PC-A> show ip\n"
            "IP Address......................: 10.0.30.11\n"
            "Subnet Mask......................: 255.255.255.0\n"
            "PC-B> show ip\n"
            "IP Address......................: 10.0.30.12\n"
            "Subnet Mask......................: 255.255.255.128\n"
        ),
        expected_fault="Subnet mask mismatch between PC-A (/24) and PC-B (/25) places them in different logical subnets despite being on the same VLAN",
    ),
    dict(
        case_id="NET-026",
        symptom="The serial link between R1 and R2 shows up/up on both ends but no traffic passes across it",
        topology_note="R1 Se0/0/0 and R2 Se0/0/0 form a leased-line point-to-point WAN link",
        osi_layer="Layer 2",
        concept_tag="WAN / Layer 2",
        severity="High",
        show_outputs=(
            "R1#show interfaces serial 0/0/0 | include line protocol|Encapsulation\n"
            "Serial0/0/0 is up, line protocol is up\n"
            "  Encapsulation PPP, loopback not set\n"
            "R2#show interfaces serial 0/0/0 | include line protocol|Encapsulation\n"
            "Serial0/0/0 is up, line protocol is up\n"
            "  Encapsulation HDLC, loopback not set\n"
        ),
        expected_fault="Encapsulation mismatch between the two ends of the serial link (PPP on R1 vs HDLC on R2) — this can leave the link nominally 'up/up' while dropping all higher-layer traffic",
    ),
    dict(
        case_id="NET-027",
        symptom="Devices plugged into VLAN 20 are being handed IP addresses from the VLAN 30 pool",
        topology_note="DHCP-VLAN20 and DHCP-VLAN30 are configured as separate pools on R1",
        osi_layer="Layer 3 / Layer 7",
        concept_tag="DHCP",
        severity="Medium",
        show_outputs=(
            "R1#show running-config | section ip dhcp pool\n"
            "ip dhcp pool DHCP-VLAN20\n"
            " network 10.0.20.0 255.255.254.0\n"
            "ip dhcp pool DHCP-VLAN30\n"
            " network 10.0.30.0 255.255.255.0\n"
        ),
        expected_fault="DHCP-VLAN20's network statement uses a /23 mask, overlapping into the 10.0.21.0/24 range and effectively also covering addresses meant for VLAN 30's neighboring segment",
    ),
    dict(
        case_id="NET-028",
        symptom="The spanning-tree root bridge keeps flapping between the two core switches, causing brief outages",
        topology_note="SW-CORE1 and SW-CORE2 are both connected redundantly at the distribution layer",
        osi_layer="Layer 2",
        concept_tag="Spanning Tree",
        severity="Medium",
        show_outputs=(
            "SW-CORE1#show spanning-tree vlan 1 | include Priority|Address\n"
            "             Priority    32768\n"
            "             Address     0011.2233.4455\n"
            "SW-CORE2#show spanning-tree vlan 1 | include Priority|Address\n"
            "             Priority    32768\n"
            "             Address     0011.2233.aabb\n"
        ),
        expected_fault="Neither core switch has an explicit spanning-tree priority set, so both use the default 32768 and the root bridge election falls back to the lowest MAC address, which can shift the perceived root as the topology changes",
    ),
    dict(
        case_id="NET-029",
        symptom="A link between SW1 and SW2 intermittently behaves like an access port instead of carrying multiple VLANs",
        topology_note="SW1 Gi0/2 and SW2 Gi0/2 connect the two switches and are expected to trunk all VLANs",
        osi_layer="Layer 2",
        concept_tag="Layer 2 Misconfiguration",
        severity="Low",
        show_outputs=(
            "SW1#show interfaces gi0/2 switchport | include Administrative Mode|Operational Mode\n"
            "Administrative Mode: dynamic desirable\n"
            "Operational Mode: trunk\n"
            "SW2#show interfaces gi0/2 switchport | include Administrative Mode|Operational Mode\n"
            "Administrative Mode: dynamic auto\n"
            "Operational Mode: static access\n"
        ),
        expected_fault="Both ends are left in DTP negotiation modes (desirable/auto) instead of hard-set 'trunk', and SW2 negotiated down to access mode",
    ),
    dict(
        case_id="NET-030",
        symptom="PC on VLAN 10 can ping internal IP 192.168.10.1 but cannot resolve intranet URL 'server.corp.local'",
        topology_note="DNS server is at 192.168.10.250; DHCP pool DHCP-VLAN10 provides IP configuration",
        osi_layer="Layer 7 (Service)",
        concept_tag="DNS",
        severity="High",
        show_outputs=(
            "PC1> ipconfig /all\n"
            "IP Address......................: 192.168.10.15\n"
            "Default Gateway.................: 192.168.10.1\n"
            "DNS Servers.....................: 192.168.99.254\n"
            "R1#show running-config | section ip dhcp pool DHCP-VLAN10\n"
            "ip dhcp pool DHCP-VLAN10\n"
            " network 192.168.10.0 255.255.255.0\n"
            " default-router 192.168.10.1\n"
            " dns-server 192.168.99.254\n"
        ),
        expected_fault="DHCP pool advertises non-existent DNS server IP (192.168.99.254 instead of actual DNS server 192.168.10.250)",
    ),
    dict(
        case_id="NET-031",
        symptom="Guest Wi-Fi users can ping and open web services on internal accounting servers in VLAN 20",
        topology_note="Guest Wi-Fi is mapped to VLAN 50; Corporate servers live in VLAN 20; Guest isolation ACL intended on R1 Gi0/0.50",
        osi_layer="Layer 3 / Layer 4",
        concept_tag="Wireless & Security",
        severity="High",
        show_outputs=(
            "R1#show ip interface GigabitEthernet0/0.50 | include Inbound access list\n"
            "  Inbound access list is not set\n"
            "R1#show access-lists GUEST-RESTRICT\n"
            "Standard IP access list GUEST-RESTRICT\n"
            "    10 deny 192.168.20.0 0.0.0.255\n"
            "    20 permit any\n"
        ),
        expected_fault="Guest isolation ACL 'GUEST-RESTRICT' is defined on R1 but was never applied inbound on sub-interface GigabitEthernet0/0.50",
    ),
    dict(
        case_id="NET-032",
        symptom="SSH connections to R2 are refused even though VTY lines are configured for SSH",
        topology_note="R2's VTY 0 4 lines specify 'transport input ssh'",
        osi_layer="Layer 7 (Service)",
        concept_tag="Remote Access (SSH)",
        severity="Low",
        show_outputs=(
            "R2#show ip ssh\n"
            "%SSH has not been enabled\n"
            "SSH Disabled - version 1.99\n"
        ),
        expected_fault="SSH was never actually enabled on R2, most likely because 'ip domain-name' was never set and RSA keys were never generated with 'crypto key generate rsa'",
    ),
    dict(
        case_id="NET-033",
        symptom="Telnet to SW1 from the management PC is immediately refused",
        topology_note="SW1 has a management VLAN 99 SVI reachable from the management PC",
        osi_layer="Layer 7 (Service)",
        concept_tag="Remote Access / Security",
        severity="Low",
        show_outputs=(
            "SW1#telnet 10.0.99.5\n"
            "Trying 10.0.99.5 ...\n"
            "% Connection refused by remote host\n"
            "SW1#show running-config | section line vty\n"
            "line vty 0 4\n"
            " transport input telnet\n"
        ),
        expected_fault="VTY lines have no 'password' or 'login' configuration, so Cisco IOS refuses incoming connections by default rather than allowing unauthenticated access",
    ),
]


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for case in CASES:
            writer.writerow(case)
    print(f"Wrote {len(CASES)} cases to {OUT_PATH}")


if __name__ == "__main__":
    main()
