"""
checker.py — NetSage AI deterministic rule engine.

Scans captured Cisco IOS `show` command output for well-known fault
signatures using regular expressions. Each rule maps to a specific OSI
layer and a suggested remediation.

Design note: this engine is intentionally conservative. It only flags a
fault when it matches a known, high-confidence pattern. Anything it
doesn't recognize falls through to the LLM reasoning path in engine.py —
the checker never guesses, and it never executes anything itself.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List


def _rule(check_id: str, module: str, osi_layer: str, pattern: str, issue: str, remediation: str) -> Dict[str, Any]:
    return {
        "check_id": check_id,
        "module": module,
        "osi_layer": osi_layer,
        "pattern": re.compile(pattern, re.IGNORECASE | re.MULTILINE),
        "issue": issue,
        "remediation": remediation,
    }


# Each rule is checked in order against the full show_output block for a
# case. The first rule to match a case "wins" for that case's primary
# diagnosis; every match is still recorded in flagged_issues.
RULES: List[Dict[str, Any]] = [
    _rule(
        "CHK_INT_ADMIN_DOWN",
        "Physical / Link Layer",
        "Layer 1 / Layer 2",
        r"(?P<intf>\S+) is administratively down, line protocol is down",
        "Interface {intf} is administratively shut down.",
        "configure terminal\ninterface {intf}\nno shutdown",
    ),
    _rule(
        "CHK_LINE_PROTOCOL_DOWN",
        "Physical / Link Layer",
        "Layer 1 / Layer 2",
        r"(?P<intf>\S+) is up, line protocol is down",
        "Interface {intf} is enabled but line protocol is down (possible encapsulation, clocking, or duplex mismatch on the peer).",
        "show controllers {intf}\nVerify encapsulation and duplex/speed match the remote peer",
    ),
    _rule(
        "CHK_DUPLICATE_IP",
        "Network Layer (IP Addressing)",
        "Layer 3",
        r"%IP-4-DUPADDR:\s*Duplicate address\s+(?P<ip>\d+\.\d+\.\d+\.\d+)\s+on\s+(?P<intf>\S+),\s+sourced by\s+(?P<mac>[0-9a-fA-F\.]+)",
        "Duplicate IP address {ip} detected on {intf} conflicting with MAC {mac}.",
        "configure terminal\ninterface {intf}\nshutdown  # reassign unique IP address before bringing interface up\nip address <new-unique-ip> <subnet-mask>\nno shutdown",
    ),
    _rule(
        "CHK_NATIVE_VLAN_MISMATCH",
        "Data Link Layer (Trunking)",
        "Layer 2",
        r"native vlan mismatch",
        "Native VLAN mismatch detected on a trunk link.",
        "switchport trunk native vlan <id>  # apply matching ID on both trunk ends",
    ),
    _rule(
        "CHK_VLAN_NOT_IN_DATABASE",
        "Data Link Layer (VLAN)",
        "Layer 2",
        r"vlan\s+(?P<vlan>\d+)\s+not found in current vlan database",
        "VLAN {vlan} is referenced but does not exist in the VLAN database.",
        "configure terminal\nvlan {vlan}\nname VLAN{vlan}",
    ),
    _rule(
        "CHK_TRUNK_VLAN_NOT_ALLOWED",
        "Data Link Layer (Trunking)",
        "Layer 2",
        r"vlan\s+(?P<vlan>\d+)\s+(?:is\s+)?not\s+allowed\s+on\s+(?:this\s+)?trunk",
        "VLAN {vlan} is pruned from the trunk's allowed list.",
        "switchport trunk allowed vlan add {vlan}",
    ),
    _rule(
        "CHK_OSPF_NO_NEIGHBORS",
        "Network Layer (Routing)",
        "Layer 3",
        r"show ip ospf neighbor\s*\n\s*(?:\n|$)",
        "No OSPF neighbors are listed on the expected interface.",
        "show running-config | section router ospf\nVerify area IDs and network statements match on both routers",
    ),
    _rule(
        "CHK_NETWORK_UNREACHABLE",
        "Network Layer (Routing)",
        "Layer 3",
        r"% network is unreachable|destination host unreachable",
        "Destination network is unreachable; the routing table is likely missing a route.",
        "show ip route\nAdd the missing static route or routing protocol advertisement",
    ),
    _rule(
        "CHK_NAT_NO_TRANSLATIONS",
        "Network Layer (NAT)",
        "Layer 3",
        r"show ip nat translations\s*\n\s*Pro\s+Inside\s+global[^\n]*\n(?![^\n]*\d+\.\d+\.\d+\.\d+)",
        "No active NAT translations exist; inside/outside interface roles or the NAT ACL may be misconfigured.",
        "show ip nat statistics\nConfirm 'ip nat inside'/'ip nat outside' are applied on the correct interfaces",
    ),
    _rule(
        "CHK_DHCP_POOL_EXHAUSTED",
        "Application / Service Layer (DHCP)",
        "Layer 7 (Service)",
        r"0 leases? available|pool.*exhausted",
        "The DHCP pool has no available leases remaining.",
        "show ip dhcp pool\nExpand the pool range or remove stale 'ip dhcp excluded-address' entries",
    ),
    _rule(
        "CHK_PORT_ERR_DISABLED",
        "Data Link Layer (Port Security)",
        "Layer 2",
        r"err-disabled|%PM-4-ERR_DISABLE",
        "The port has been placed into err-disabled state, most likely from a port-security violation.",
        "configure terminal\ninterface <port>\nshutdown\nno shutdown  # only after confirming and removing the offending device/MAC",
    ),
    _rule(
        "CHK_DUPLEX_MISMATCH",
        "Physical Layer (Duplex/Speed)",
        "Layer 1",
        r"%CDP-4-DUPLEX_MISMATCH|duplex mismatch",
        "A duplex mismatch was detected between two connected interfaces.",
        "Set matching duplex/speed (or 'auto' on both ends) on the affected link",
    ),
    _rule(
        "CHK_IP_ROUTING_DISABLED",
        "Network Layer (Multilayer Switching)",
        "Layer 3",
        r"ip routing:?\s+is\s+disabled|ip routing\s*:\s*disabled",
        "IP routing is globally disabled on this multilayer switch, so SVIs cannot route between VLANs.",
        "configure terminal\nip routing",
    ),
    _rule(
        "CHK_BAD_MASK_OR_OVERLAP",
        "Network Layer (IP Addressing)",
        "Layer 3",
        r"% (?:Bad mask|Inconsistent address and mask|Overlapping subnet)",
        "Subnet mask mismatch or invalid address-mask combination configured.",
        "Verify correct subnet prefix length and reconfigure interface with valid subnet mask",
    ),
    _rule(
        "CHK_DNS_LOOKUP_FAILED",
        "Application / Service Layer (DNS)",
        "Layer 7 (Service)",
        r"(?:% (?:Unrecognized host|Unknown host)|domain server \(255\.255\.255\.255\)|name server not responding)",
        "DNS resolution failed. Domain lookup is disabled or the configured DNS server IP is unreachable.",
        "show running-config | include ip name-server|ip domain\nconfigure terminal\nip domain lookup\nip name-server <valid-dns-ip>",
    ),
]


def run_checks(show_output: str) -> Dict[str, Any]:
    """
    Run every deterministic rule against a block of captured `show`
    command output.

    Returns a dict matching NetSage AI's structured schema:
        {
          "status": "ERRORS_DETECTED" | "NO_ERRORS_DETECTED",
          "flagged_issues": [ {check_id, module, issue, osi_layer, remediation}, ... ]
        }
    """
    show_output = show_output or ""
    flagged: List[Dict[str, str]] = []

    for rule in RULES:
        match = rule["pattern"].search(show_output)
        if not match:
            continue
        groups = {k: (v or "") for k, v in match.groupdict().items()}
        flagged.append(
            {
                "check_id": rule["check_id"],
                "module": rule["module"],
                "issue": rule["issue"].format(**groups),
                "osi_layer": rule["osi_layer"],
                "remediation": rule["remediation"].format(**groups),
            }
        )

    return {
        "status": "ERRORS_DETECTED" if flagged else "NO_ERRORS_DETECTED",
        "flagged_issues": flagged,
    }


if __name__ == "__main__":
    print("=" * 70)
    print("NetSage AI — Deterministic Rule Checker CLI Smoke Test")
    print("=" * 70)
    
    samples = [
        (
            "Test 1: Interface Administratively Down",
            "GigabitEthernet0/0.10 is up, line protocol is up\n"
            "GigabitEthernet0/0.30 is administratively down, line protocol is down\n"
        ),
        (
            "Test 2: Duplicate IP Address Conflict",
            "%IP-4-DUPADDR: Duplicate address 192.168.10.1 on GigabitEthernet0/0.10, sourced by 0001.96a2.bc01\n"
        ),
        (
            "Test 3: DNS Name Resolution Failure",
            "Translating \"server.lab.local\"...domain server (255.255.255.255)\n"
            "% Unknown host or address, or name server not responding\n"
        ),
    ]

    for title, text in samples:
        print(f"\n--- {title} ---")
        res = run_checks(text)
        print(json.dumps(res, indent=2))
    print("\n" + "=" * 70)
