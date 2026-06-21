"""No-stdlib-``math`` ratchet (v0.9.0rc13).

srmech is its own maths library: every continuous-math primitive is a cascade of
the 14 A–N classes over the numpy-free carriers, and the integer primitives are
native C ops. The package therefore borrows **nothing** from the stdlib ``math``
module — when a maths primitive is missing we find its cascade and ADD it to
srmech (native C + Python), we never ``import math``
(``[[feedback_missing_math_is_added_to_srmech_as_cascade_never_imported]]`` /
``[[feedback_numpy_free_means_zero_numpy_no_bridges]]`` generalised to ALL math).

rc13 purged the last residue (``math.isqrt`` → native ``srmech_isqrt`` +
arbitrary-precision integer-Newton; ``math.isfinite`` / ``math.isinf`` →
comparison; ``math.fsum`` → Neumaier compensated sum; ``math.pi`` → the Class-N
``atan`` cascade ``4·atan(1)``). This ratchet keeps it gone: it AST-walks every
``srmech/`` source module and fails on any ``import math`` / ``from math import``
statement OR any executable ``math.<attr>`` access. Prose mentions of ``math.x``
in docstrings / comments are fine (the AST never sees them), so the framework can
still *describe* what it replaced. Pure stdlib (``ast`` / ``pathlib``); numpy-free.
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


def _math_violations(path: Path):
    """Return human-readable violations for one module (empty list = clean)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return []                                  # unreadable → not our concern
    out = []
    rel = path.relative_to(_PKG_ROOT)
    for node in ast.walk(tree):
        # `import math` / `import math as m`
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "math" or alias.name.startswith("math."):
                    out.append(f"{rel}:{node.lineno}: import {alias.name}")
        # `from math import ...`
        elif isinstance(node, ast.ImportFrom):
            if node.module == "math" or (node.module or "").startswith("math."):
                names = ", ".join(a.name for a in node.names)
                out.append(f"{rel}:{node.lineno}: from {node.module} import {names}")
        # executable `math.<attr>` (base is the bare name `math`)
        elif isinstance(node, ast.Attribute):
            base = node.value
            if isinstance(base, ast.Name) and base.id == "math":
                out.append(f"{rel}:{node.lineno}: math.{node.attr}")
    return out


def test_no_stdlib_math_anywhere_in_source():
    violations = []
    for path in _iter_source_files():
        violations.extend(_math_violations(path))
    assert not violations, (
        "srmech borrows from the stdlib `math` module — it must not. Find the "
        "cascade for the missing primitive and ADD it to srmech (native C + "
        "Python), per the math-purge discipline; never `import math`:\n  "
        + "\n  ".join(violations)
    )
