"""srmech.amsc.carrier_ladder — the CARRIER CONVERSION LADDER (rc116; issue
#1248 / F1038): promote / project between adjacent rungs of the exact-``ℚ``
polynomial carriers, plus the declarative coherency map a driver reads to
auto-route a carrier UP to a higher-rung consumer.

The exact-``ℚ`` polynomial carriers form two **variable ladders** — the number
of shift variables the carrier tracks IS its rung:

  * the **ordinary** ladder ``Poly(k) → BiPoly(n,k) → TriPoly(n,j,k)`` (rungs
    1 / 2 / 3), consumed by ``gosper`` (Poly) / ``zeilberger`` +
    ``wz_certificate`` (BiPoly) / ``apagodu_zeilberger`` (TriPoly);
  * the **q** ladder ``QPoly(x=qⁿ) → QBiPoly(X=qⁿ, Y=qᵏ)`` (rungs 1 / 2),
    consumed by ``q_gosper`` (QPoly) / ``q_zeilberger`` + ``q_wz_certificate``
    (QBiPoly).

**PROMOTE** is the *trivial embedding* — it adds a degree-0 variable, so the
polynomial is unchanged as a function; it merely gains a formal variable it
does NOT depend on. It is TOTAL (defined for every input; a no-op when the
target rung equals the current rung). The ordinary ladder's promote adds ``n``
(``Poly(k) ↪ BiPoly(n,k)`` via :meth:`BiPoly.from_k_poly`) then ``j``
(``BiPoly(n,k) ↪ TriPoly(n,j,k)`` via :meth:`TriPoly.from_bipoly`); the q
ladder's promote adds ``Y = qᵏ`` (``QPoly ↪ QBiPoly`` via
:meth:`QBiPoly.from_x_qpoly`).

**PROJECT** is the *inverse* — it drops the highest-rung variable IFF that
variable is genuinely trivial (the carrier has degree 0 in it). If the variable
is genuinely PRESENT, project raises a **coherency error that NAMES the
obstruction** (which variable is genuinely non-trivial) — it NEVER silently
truncates (the rc104 lesson: a dropped-but-present variable is a lie, not a
projection). This is the diagnostic style of the beat-relation residue: say
exactly what blocks the reduction.

**ROUND-TRIP LAW** (tested at every rung): ``project(promote(x)) == x``,
EXACT. Promote adds a degree-0 variable; project (the variable being trivial by
construction) drops exactly it, recovering ``x`` bit-for-bit.

**No new compute.** Promote is a re-wrap (embed), project is a trivial-check +
drop — pure carrier restructuring, no numerical kernel. So these ship
**non_compute** (the ``coupling.from_bodies`` / ``text.cooccurrence_edges``
precedent; no dedicated C peer — the data movement is a trivial
embedding/dropping). Exact-``ℚ`` throughout; no float, no ``abs()`` (sign is
the Class-K pin-slot on the underlying carriers), no numpy / ``math``.

The **Hurwitz (Cayley–Dickson) ladder** ℝ↪ℂ↪ℍ↪𝕆↪𝕊 has the same shape one
level of algebra up; its promote / project ship next to the ``cd_*`` family as
:func:`srmech.amsc.cascade.cd_promote` / :func:`srmech.amsc.cascade.cd_project`.
:func:`carrier_ladder_descriptor` maps ALL THREE ladders.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .poly import Poly
from .qbipoly import QBiPoly
from .qpoly import QPoly
from .tripoly import TriPoly
from .zeilberger import BiPoly

__all__ = [
    "poly_promote",
    "poly_project",
    "qpoly_promote",
    "qpoly_project",
    "carrier_ladder_descriptor",
]

# The ordinary variable ladder — the carrier at each rung (Poly / BiPoly /
# TriPoly = rung 1 / 2 / 3); the q ladder (QPoly / QBiPoly) is handled inline.
_ORDINARY_RUNG = {Poly: 1, BiPoly: 2, TriPoly: 3}


def _ordinary_rung(p: Any) -> int:
    """The ordinary-ladder rung of ``p`` (1 Poly / 2 BiPoly / 3 TriPoly), or a
    ``TypeError`` when ``p`` is not an ordinary-ladder carrier."""
    for cls, rung in _ORDINARY_RUNG.items():
        if isinstance(p, cls):
            return rung
    raise TypeError(
        "poly ladder ops take a Poly / BiPoly / TriPoly (the ordinary variable "
        f"ladder); got {type(p).__name__}")


# ── the ordinary variable ladder: Poly ↔ BiPoly ↔ TriPoly ─────────────────────

def poly_promote(p: Any, n_vars: Optional[int] = None) -> Any:
    """Promote an ordinary-ladder carrier UP the variable ladder ``Poly(k) →
    BiPoly(n,k) → TriPoly(n,j,k)`` by the *trivial embedding* (rc116; #1248 /
    F1038).

    ``p`` is a :class:`~srmech.amsc.poly.Poly` (rung 1, a polynomial in ``k``),
    a :class:`~srmech.amsc.zeilberger.BiPoly` (rung 2, in ``(n,k)``), or a
    :class:`~srmech.amsc.tripoly.TriPoly` (rung 3, in ``(n,j,k)``). ``n_vars``
    is the TARGET rung (1, 2, or 3); it must be ≥ the current rung. When
    ``n_vars is None`` the default is one rung up. When ``n_vars`` equals the
    current rung the input is returned unchanged (TOTAL — promote is defined for
    every input).

    Each single-rung step is the trivial embedding that adds a degree-0
    variable: ``Poly(k) ↪ BiPoly(n,k)`` adds ``n``
    (:meth:`BiPoly.from_k_poly`); ``BiPoly(n,k) ↪ TriPoly(n,j,k)`` adds ``j``
    (:meth:`TriPoly.from_bipoly`). The polynomial is unchanged as a function —
    this is exactly the "a univariate IS trivially bivariate" fact that lets a
    ``Poly`` feed ``zeilberger``. Its inverse is :func:`poly_project`, so
    ``poly_project(poly_promote(x)) == x`` EXACT at every rung.

    Exact-``ℚ``; no float, no ``abs()``, no numpy / ``math``."""
    cur = _ordinary_rung(p)
    if n_vars is None:
        n_vars = min(cur + 1, 3)
    if isinstance(n_vars, bool) or not isinstance(n_vars, int):
        raise TypeError(
            "poly_promote: n_vars must be an int rung target (1, 2, or 3); got "
            f"{n_vars!r}")
    if not (1 <= n_vars <= 3):
        raise ValueError(
            "poly_promote: n_vars must be 1, 2, or 3 (Poly / BiPoly / TriPoly); "
            f"got {n_vars}")
    if n_vars < cur:
        raise ValueError(
            f"poly_promote: n_vars={n_vars} is below the current rung {cur}; "
            f"promote only lifts UP the ladder — use poly_project to descend")
    obj = p
    rung = cur
    while rung < n_vars:
        if rung == 1:                                # Poly(k) ↪ BiPoly(n,k) [+n]
            obj = BiPoly.from_k_poly(obj)
        else:                                        # BiPoly ↪ TriPoly(n,j,k) [+j]
            obj = TriPoly.from_bipoly(obj)
        rung += 1
    return obj


def poly_project(p: Any) -> Any:
    """Project an ordinary-ladder carrier DOWN one rung ``TriPoly → BiPoly →
    Poly`` — the inverse of :func:`poly_promote` (rc116; #1248 / F1038).

    Drops the highest-rung variable IFF the carrier is genuinely trivial in it
    (degree 0): ``TriPoly(n,j,k) → BiPoly(n,k)`` drops ``j`` iff the
    ``j``-degree is ≤ 0; ``BiPoly(n,k) → Poly(k)`` drops ``n`` iff every
    ``k``-coefficient is constant in ``n``. When the variable is genuinely
    PRESENT, raises a coherency ``ValueError`` that NAMES it (never a silent
    truncation — the rc104 lesson). A rung-1 ``Poly`` has no higher variable to
    drop → ``ValueError``.

    ``poly_project(poly_promote(x)) == x`` EXACT at every rung. Exact-``ℚ``; no
    float, no ``abs()``, no numpy / ``math``."""
    if isinstance(p, TriPoly):
        if p.j_degree <= 0:                          # trivial in j → drop it
            return p.block(0)                        # the j**0 BiPoly (zero-safe)
        raise ValueError(
            "poly_project: cannot drop the variable 'j' — the TriPoly is "
            f"genuinely j-dependent (j_degree = {p.j_degree} ≥ 1); projecting "
            "TriPoly(n,j,k) → BiPoly(n,k) would TRUNCATE the j-dependence, not "
            "drop a trivial variable. 'j' is the genuinely non-trivial variable.")
    if isinstance(p, BiPoly):
        n_degree = max((kp.degree for kp in p.terms), default=-1)
        if n_degree <= 0:                            # trivial in n → drop it
            return Poly.from_coeffs([kp[0] for kp in p.terms])
        raise ValueError(
            "poly_project: cannot drop the variable 'n' — the BiPoly is "
            f"genuinely n-dependent (n_degree = {n_degree} ≥ 1); projecting "
            "BiPoly(n,k) → Poly(k) would TRUNCATE the n-dependence, not drop a "
            "trivial variable. 'n' is the genuinely non-trivial variable.")
    if isinstance(p, Poly):
        raise ValueError(
            "poly_project: a Poly is already at the base rung (rung 1, the "
            "single variable k); there is no higher variable to drop")
    raise TypeError(
        "poly_project expects a Poly / BiPoly / TriPoly (the ordinary variable "
        f"ladder); got {type(p).__name__}")


# ── the q variable ladder: QPoly ↔ QBiPoly ────────────────────────────────────

def qpoly_promote(p: Any, n_vars: Optional[int] = None) -> Any:
    """Promote a q-ladder carrier UP the variable ladder ``QPoly(x=qⁿ) →
    QBiPoly(X=qⁿ, Y=qᵏ)`` by the trivial embedding (rc116; #1248 / F1038).

    ``p`` is a :class:`~srmech.amsc.qpoly.QPoly` (rung 1) or a
    :class:`~srmech.amsc.qbipoly.QBiPoly` (rung 2). ``n_vars`` is the TARGET
    rung (1 or 2; default one rung up). ``QPoly ↪ QBiPoly`` adds the degree-0
    variable ``Y = qᵏ`` (:meth:`QBiPoly.from_x_qpoly` — a single ``Y**0``
    cell). TOTAL; the q-analog of :func:`poly_promote`. Its inverse is
    :func:`qpoly_project`. Exact over ``ℚ[q]``; no float, no ``abs()``, no
    numpy / ``math``."""
    if isinstance(p, QBiPoly):
        cur = 2
    elif isinstance(p, QPoly):
        cur = 1
    else:
        raise TypeError(
            "qpoly_promote expects a QPoly / QBiPoly (the q variable ladder); got "
            f"{type(p).__name__}")
    if n_vars is None:
        n_vars = min(cur + 1, 2)
    if isinstance(n_vars, bool) or not isinstance(n_vars, int):
        raise TypeError(
            "qpoly_promote: n_vars must be an int rung target (1 or 2); got "
            f"{n_vars!r}")
    if not (1 <= n_vars <= 2):
        raise ValueError(
            "qpoly_promote: n_vars must be 1 or 2 (QPoly / QBiPoly); got "
            f"{n_vars}")
    if n_vars < cur:
        raise ValueError(
            f"qpoly_promote: n_vars={n_vars} is below the current rung {cur}; "
            "promote only lifts UP the ladder — use qpoly_project to descend")
    if cur == 1 and n_vars == 2:                     # QPoly(x) ↪ QBiPoly(X,Y) [+Y]
        return QBiPoly.from_x_qpoly(p)
    return p


def qpoly_project(p: Any) -> Any:
    """Project a q-ladder carrier DOWN one rung ``QBiPoly → QPoly`` — the
    inverse of :func:`qpoly_promote` (rc116; #1248 / F1038).

    Drops the variable ``Y = qᵏ`` IFF the ``QBiPoly`` is genuinely trivial in it
    (``Y``-degree ≤ 0 — only the ``Y**0`` cell); returns that cell (a
    ``QPoly`` in ``X = qⁿ``). When ``Y`` is genuinely present, raises a
    coherency ``ValueError`` that NAMES it (never a silent truncation). A
    rung-1 ``QPoly`` has no higher variable to drop → ``ValueError``.

    ``qpoly_project(qpoly_promote(x)) == x`` EXACT. Exact over ``ℚ[q]``; no
    float, no ``abs()``, no numpy / ``math``."""
    if isinstance(p, QBiPoly):
        if p.y_degree <= 0:                          # trivial in Y → drop it
            return p.coeff(0)                        # the Y**0 QPoly (zero-safe)
        raise ValueError(
            "qpoly_project: cannot drop the variable 'Y = qᵏ' — the QBiPoly is "
            f"genuinely Y-dependent (y_degree = {p.y_degree} ≥ 1); projecting "
            "QBiPoly(X,Y) → QPoly(X) would TRUNCATE the Y-dependence, not drop a "
            "trivial variable. 'Y' is the genuinely non-trivial variable.")
    if isinstance(p, QPoly):
        raise ValueError(
            "qpoly_project: a QPoly is already at the base rung (rung 1, the "
            "single variable x = qⁿ); there is no higher variable to drop")
    raise TypeError(
        "qpoly_project expects a QPoly / QBiPoly (the q variable ladder); got "
        f"{type(p).__name__}")


# ── the declarative coherency map (the driver's routing table) ────────────────

def carrier_ladder_descriptor() -> Dict[str, Any]:
    """The declarative CARRIER-LADDER coherency map (rc116; #1248 / F1038) — a
    small, static descriptor a driver (e.g. siona's result register, F1024)
    reads to auto-route a lower-rung carrier UP to any consumer that accepts a
    higher rung.

    Returns a plain ``dict`` with two views:

    - ``"carriers"``: for each carrier type name, ``{"ladder": <name>, "rung":
      <int>}`` — the required per-carrier shape (``Poly`` → ``{"ladder":
      "variable", "rung": 1}``, …). A driver holding a ``Poly`` and facing a
      ``zeilberger`` (BiPoly, rung 2) consumer reads ``rung 1 < 2`` on the same
      ``"variable"`` ladder → promote.
    - ``"ladders"``: for each ladder, its ``{name: rung}`` rungs, the variable
      each rung ADDS on the way up, and the dotted ``promote`` / ``project`` op
      names to call. The three ladders are ``"variable"`` (Poly/BiPoly/TriPoly),
      ``"variable_q"`` (QPoly/QBiPoly), and ``"cayley_dickson"`` (ℝ/ℂ/ℍ/𝕆/𝕊,
      keyed by algebra dimension — the ``dim`` arg :func:`cd_promote` takes).

    Pure data (a fixed table); ships **non_compute**. No float, no numpy /
    ``math``."""
    return {
        "carriers": {
            "Poly": {"ladder": "variable", "rung": 1},
            "BiPoly": {"ladder": "variable", "rung": 2},
            "TriPoly": {"ladder": "variable", "rung": 3},
            "QPoly": {"ladder": "variable_q", "rung": 1},
            "QBiPoly": {"ladder": "variable_q", "rung": 2},
        },
        "ladders": {
            "variable": {
                "rungs": {"Poly": 1, "BiPoly": 2, "TriPoly": 3},
                # the variable each rung ADDS going up (rung 1 is the base var k)
                "adds_variable": {"1": "k", "2": "n", "3": "j"},
                "promote": "srmech.amsc.carrier_ladder.poly_promote",
                "project": "srmech.amsc.carrier_ladder.poly_project",
            },
            "variable_q": {
                "rungs": {"QPoly": 1, "QBiPoly": 2},
                "adds_variable": {"1": "x=qⁿ", "2": "Y=qᵏ"},
                "promote": "srmech.amsc.carrier_ladder.qpoly_promote",
                "project": "srmech.amsc.carrier_ladder.qpoly_project",
            },
            "cayley_dickson": {
                # keyed by algebra DIMENSION (the cd_promote `dim` target)
                "rungs": {"R": 1, "C": 2, "H": 4, "O": 8, "S": 16},
                "adds_variable": {
                    "1": "(real)", "2": "i", "4": "j,k", "8": "e4..e7",
                    "16": "e8..e15",
                },
                "promote": "srmech.amsc.cascade.cd_promote",
                "project": "srmech.amsc.cascade.cd_project",
            },
        },
    }
