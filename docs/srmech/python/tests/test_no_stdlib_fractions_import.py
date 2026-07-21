"""No-stdlib-``fractions`` ratchet (v0.9.0rc263, #845).

srmech carries its exact rationals in its OWN C-native carrier
:class:`srmech.amsc.q.Q` — a reduced ``(num, den)`` integer pair whose reduce /
multiply ride the native ``srmech_rational_*`` / ``srmech_bigint`` symbols. It
therefore borrows **nothing** from the stdlib ``fractions`` module: rc263 purged
the last residue (the Cayley–Dickson element carrier, the exact-LA
``dense_solve`` / ``schur_complement`` boundary, ``cycle_holonomy``'s exact
holonomies, the Sturm / complex-isolation interval oracles, the arithmetic-coder,
the MCP charge wire, and every ``_coerce`` accept-branch), so a bare-C host with
no Python stdlib carries the same exact-rational math. The former registered
``"Fraction"`` interchange carrier was removed — ``Q`` subsumed it
(``[[feedback_prefer_carrier_native_arithmetic_over_downcast_decline]]`` /
``[[feedback_missing_math_is_added_to_srmech_as_cascade_never_imported]]``
generalised from ``math`` to ``fractions``).

A stdlib ``fractions.Fraction`` is still ACCEPTED on INPUT everywhere (``Q``'s
arithmetic + ``to_q`` speak the ``numbers.Rational`` / ``as_integer_ratio``
numeric protocol), and prose mentions of ``fractions.Fraction`` in docstrings /
comments are fine (the AST never sees them) — the framework can still *describe*
the interchange it accepts and the type it replaced. What is banned is srmech
*importing* ``fractions`` for its own math: this ratchet AST-walks every
``srmech/`` source module and fails on any ``import fractions`` /
``from fractions import`` statement (module or function scope). Pure stdlib
(``ast`` / ``pathlib``); numpy-free.
"""
from __future__ import annotations

import ast
from pathlib import Path

import srmech

# The installed/edited package source root (…/srmech/). Walk every .py under it.
_PKG_ROOT = Path(srmech.__file__).resolve().parent


def _iter_source_files():
    for path in sorted(_PKG_ROOT.rglob("*.py")):
        # _native/ holds only compiled libs in a wheel; nothing to scan there.
        if "_native" in path.parts and path.name != "_native.py":
            continue
        yield path


def _fractions_violations(path: Path):
    """Return human-readable violations for one module (empty list = clean)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return []                                  # unreadable → not our concern
    out = []
    rel = path.relative_to(_PKG_ROOT)
    for node in ast.walk(tree):
        # `import fractions` / `import fractions as F`
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "fractions" or alias.name.startswith("fractions."):
                    out.append(f"{rel}:{node.lineno}: import {alias.name}")
        # `from fractions import ...`
        elif isinstance(node, ast.ImportFrom):
            if node.module == "fractions" or (node.module or "").startswith("fractions."):
                names = ", ".join(a.name for a in node.names)
                out.append(f"{rel}:{node.lineno}: from {node.module} import {names}")
    return out


def test_no_stdlib_fractions_import_anywhere_in_source():
    violations = []
    for path in _iter_source_files():
        violations.extend(_fractions_violations(path))
    assert not violations, (
        "srmech imports the stdlib `fractions` module for its own math — it must "
        "not (#845). Carry the exact rational in srmech's own `Q` carrier "
        "(`from srmech.amsc.q import Q, to_q`); a stdlib Fraction is still "
        "accepted on INPUT via the numeric protocol, never imported:\n  "
        + "\n  ".join(violations)
    )
