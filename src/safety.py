"""Command safety policy for NetSage AI.

NetSage never executes commands itself. This module only checks proposed
remediation text before it reaches the human approval gate.
"""
from __future__ import annotations

import re
from typing import Iterable, Dict, Any

BLOCKED_PATTERNS = [
    r"^\s*reload\b",
    r"^\s*write\s+erase\b",
    r"^\s*erase\s+startup-config\b",
    r"^\s*format\b",
    r"^\s*delete\b",
    r"^\s*crypto\s+key\s+zeroize\b",
]


def validate_commands(commands: Iterable[str]) -> Dict[str, Any]:
    """Return a conservative safety decision for proposed CLI lines."""
    blocked = []
    checked = []
    for command in commands:
        line = str(command).strip()
        if not line:
            continue
        checked.append(line)
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in BLOCKED_PATTERNS):
            blocked.append(line)

    return {
        "safe": not blocked,
        "blocked_commands": blocked,
        "checked_commands": checked,
    }
