"""A-N cascade ratchet — the down-only guard that flags continuous math NOT yet
reduced to the 14 A-N class cascades (user direction 2026-06-08: "add another code
sweep to check for math that has not been reduced to cyclic algebra ... A-N
cascades might be the right way to put it").

This is the **bare-Python-tier sibling** of two existing ratchets:

  * the **C-transpile libm ratchet** (``tests/test_c_cascade_coherence.py`` walks
    ``*.c`` / ``*.h`` and drove ``libsrmech``'s libm calls 23 → 0 — every
    continuous-math op in C is now a cascade of the 14, no ``<math.h>``); and
  * the **numpy-math ratchet** (``tests/test_numpy_math_ratchet.py`` — the
    numpy-tier residue: ``np.linalg`` / ``np.fft`` / ``@`` / the transcendental
    ufuncs).

What this one guards is the **third tier**: bare-Python ``math.*`` / ``cmath.*``
float transcendentals, ``math.pi`` / ``math.tau`` float constants, and fractional
``** <float>`` powers — the continuous-math that has an EXACT A-N cascade
replacement in ``srmech.amsc.rational`` (``sin`` / ``cos`` / ``atan`` / ``atan2``
/ ``exp`` / ``log`` / ``sqrt`` / ``hypot`` the Class-N rational primitives;
``pi_cascade_digits`` the Class-N π; integer ``**`` the exact power). Per the
user's deepest principle — *"don't use floats for bit-exact math, that's what ints
and complex are for; floats are for FPU lift"* — every such bare-Python call where
a cascade belongs is a **defect**, the same class the C-transpile arc drove out.

WHY AST, not regex (unlike the numpy-math ratchet): the ``srmech`` source is dense
with *descriptive* mentions — ``rational.py`` and ``tool_schema.py`` alone carry
~39 docstring / summary-string references like "Substrate-native replacement for
``math.cos``" and "no ``math.cos`` in the call graph". A text regex would count
every one as debt. So this walks the **AST** and counts only genuine ``Call`` /
``Attribute`` / ``BinOp`` nodes — string literals, comments and docstrings are
invisible to it (the same reason the no-abs scanner in
``test_matrix_cascades_rc38.py`` is AST-based). The AST walk is also identical
across CPython 3.10–3.14.

Three down-only categories, each pinned TIGHT (``== ceiling``, not ``<=``) for the
same reason the Rosetta + numpy-math ledgers are — a count *below* ceiling means a
site was reduced without lowering the ledger; *above* means continuous-math was
added where a cascade belongs (the regression this guard forbids):

  * ``transcendental`` — a ``Call`` to ``math.{sin,cos,tan,exp,log,sqrt,hypot,
    atan,atan2,…}`` or ANY ``cmath.*``. Reduce by routing through the matching
    ``srmech.amsc.rational`` cascade, then lower ``CEIL_TRANSCENDENTAL``.
  * ``math_const``    — an ``Attribute`` read of ``math.{pi,tau,e}``. Reduce by
    using ``pi_cascade_digits`` (the Class-N π), then lower ``CEIL_MATH_CONST``.
  * ``float_pow``     — a ``BinOp`` ``a ** <float-constant>`` (e.g. ``x ** 0.5``
    — the ``math.sqrt`` cousin). Reduce via ``rational.sqrt`` / integer power.

EXCLUDED, by design (documented so the exclusions aren't silent gaming):

  * **Integer primitives** — ``math.{isqrt,gcd,comb,factorial,floor,ceil,trunc,
    perm}``: these are exact Class-I / J / N integer ops, not continuous math.
  * **IEEE / sign primitives** — ``math.{copysign,fabs,isfinite,isinf,isnan,
    ldexp,frexp,modf,nextafter}`` and ``math.{inf,nan}``: sign-transfer and
    special-value handling at the FPU-lift boundary. These are the Class-K sign
    family (``copysign`` at an IEEE ±0 / signed-Inf limit is the *correct* idiom,
    not a transcendental); the builtin ``abs()`` is governed separately by the
    no-abs scanner. ``math.fabs`` carries no current sites; if one appears it is
    a Class-K sign-branch question, not an A-N-reduction one.
  * **String / comment mentions** — invisible to the AST walk by construction.

No module is carved out: the walk covers the WHOLE ``srmech`` tree, including
``rational.py`` (the cascade-primitive home itself) — which has ZERO genuine
transcendental *calls*, only docstring references + the excluded ``copysign`` /
``isqrt``. A stray ``math.sin`` ANYWHERE — even there — fails the ledger.

Baseline (v0.7.5rc32): the single ``transcendental`` site is the ``cmath.sqrt``
Wilkinson-shift discriminant in the FLOAT ``eigvals`` (the complex-spectrum
shifted-QR path in ``matrix_cascades.py``). It is eliminated when complex-
eigenvalue exact isolation lands — the rc31 ``eigvals_exact`` follow-up; the real
spectrum is already exact (no transcendental). ``math_const`` and ``float_pow``
are both at zero: the π-cascade discipline fully holds (no float ``math.pi`` in
any compute path) and there are no fractional float powers.
"""
from __future__ import annotations

import ast
from pathlib import Path

# ---------------------------------------------------------------------------
# The srmech source tree. Tests live in a sibling dir and are NOT scanned.
# ---------------------------------------------------------------------------
SRMECH_PKG = Path(__file__).resolve().parent.parent / "srmech"

# Float transcendentals with an exact A-N cascade replacement in
# srmech.amsc.rational. (Integer ops — isqrt/gcd/comb/factorial/floor/ceil/trunc —
# and IEEE/sign primitives — copysign/fabs/isfinite/isinf/isnan/ldexp/frexp — are
# deliberately absent: see the module docstring's EXCLUDED list.)
_TRANSCENDENTAL = frozenset({
    "sin", "cos", "tan", "exp", "expm1", "log", "log1p", "log2", "log10",
    "sqrt", "cbrt", "asin", "acos", "atan", "atan2", "sinh", "cosh", "tanh",
    "asinh", "acosh", "atanh", "pow", "hypot", "erf", "erfc", "gamma",
    "lgamma", "degrees", "radians", "dist",
})
# Float constants with an exact Class-N π-cascade replacement. (inf / nan are
# IEEE specials used in finite-domain guards, NOT π-cascade-able — excluded.)
_MATH_CONST = frozenset({"pi", "tau", "e"})


def _scan() -> tuple[dict[str, int], list[tuple[str, int, str]]]:
    """Walk the AST of every ``srmech/**/*.py`` and tally the three categories.

    Returns ``(counts, sites)`` where ``sites`` is a flat ``(relpath, lineno,
    what)`` list for an actionable failure breakdown.
    """
    counts = {"transcendental": 0, "math_const": 0, "float_pow": 0}
    sites: list[tuple[str, int, str]] = []
    for path in sorted(SRMECH_PKG.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = str(path.relative_to(SRMECH_PKG))
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            # math.<transcendental>(...) / cmath.<anything>(...)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in ("math", "cmath")
                and (node.func.value.id == "cmath" or node.func.attr in _TRANSCENDENTAL)
            ):
                counts["transcendental"] += 1
                sites.append((rel, node.lineno, f"{node.func.value.id}.{node.func.attr}()"))
            # math.pi / math.tau / math.e  (an Attribute read, not a call)
            elif (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "math"
                and node.attr in _MATH_CONST
            ):
                counts["math_const"] += 1
                sites.append((rel, node.lineno, f"math.{node.attr}"))
            # a ** <float-constant>  (fractional power — the math.sqrt cousin)
            elif (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Pow)
                and isinstance(node.right, ast.Constant)
                and isinstance(node.right.value, float)
            ):
                counts["float_pow"] += 1
                sites.append((rel, node.lineno, f"** {node.right.value}"))
    return counts, sites


# ---------------------------------------------------------------------------
# DOWN-ONLY ceilings. Lower (never raise) the matching one when a site is routed
# through an A-N cascade. Baseline pinned at v0.7.5rc32 (the ratchet's
# introduction): transcendental = 1 (the cmath.sqrt Wilkinson-shift discriminant
# in the FLOAT eigvals complex-spectrum path). rc33 CLOSED IT: that `cmath.sqrt`
# was routed through `matrix_cascades._complex_sqrt` — the principal complex root
# rebuilt from the Class-N `hypot`/`sqrt` real cascades + a Class-K sign-branch,
# no libm `cmath`. So transcendental → 0: the bare-Python tier now joins the C
# tier (libm 23 → 0) at ZERO continuous-math residue. math_const = 0 (the
# π-cascade discipline fully holds — no float math.pi in any compute path);
# float_pow = 0. All three categories at zero — the ratchet is closed.
# ---------------------------------------------------------------------------
CEIL_TRANSCENDENTAL = 0
CEIL_MATH_CONST = 0
CEIL_FLOAT_POW = 0


def _breakdown(sites: list[tuple[str, int, str]]) -> str:
    return "\n".join(
        f"    {rel}:{ln}  {what}" for rel, ln, what in sorted(sites)
    ) or "    (none)"


def test_an_cascade_ledger_is_tight():
    """Each continuous-math category count equals its down-only ceiling.

    ABOVE ceiling → bare-Python continuous math was added where an A-N cascade
    belongs (route it through ``srmech.amsc.rational`` / ``pi_cascade_digits``).
    BELOW ceiling → a site was reduced but the ceiling wasn't lowered — lower the
    matching ``CEIL_*`` to the new exact count.
    """
    counts, sites = _scan()
    ceilings = {
        "transcendental": CEIL_TRANSCENDENTAL,
        "math_const": CEIL_MATH_CONST,
        "float_pow": CEIL_FLOAT_POW,
    }
    mismatches = {k: (counts[k], ceilings[k]) for k in ceilings if counts[k] != ceilings[k]}
    assert not mismatches, (
        "A-N cascade ledger drift "
        + ", ".join(f"{k}: live={live} ceiling={ceil}" for k, (live, ceil) in mismatches.items())
        + ".\n  ABOVE ceiling → reduce the new continuous-math site to an A-N "
        "cascade (rational.{sin,cos,exp,log,sqrt,…} / pi_cascade_digits / integer "
        "power); floats are for the FPU lift only.\n  BELOW ceiling → you reduced "
        "a site; lower the matching CEIL_* to the new exact count.\n"
        "  Current continuous-math sites:\n" + _breakdown(sites)
    )


def test_an_cascade_total_is_down_only():
    """The grand total is at or below the pinned sum (a coarse safety net)."""
    counts, sites = _scan()
    total = sum(counts.values())
    ceil_total = CEIL_TRANSCENDENTAL + CEIL_MATH_CONST + CEIL_FLOAT_POW
    assert total <= ceil_total, (
        f"A-N cascade total {total} exceeds pinned {ceil_total}; continuous math "
        "regressed to bare-Python floats where a cascade belongs. Sites:\n"
        + _breakdown(sites)
    )
