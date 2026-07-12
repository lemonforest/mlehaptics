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

**The per-op CARRIER CONTRACT** (rc120; issue #1254 / F1041): the descriptor's
``"ops"`` view makes the per-op carrier RUNG machine-readable — which rung each
op CONSUMES and PRODUCES — so a driver (siona's result register, F1024) routes a
carrier to a consumer WITHOUT a hardcoded op→rung name-map or a register-length
heuristic. Before rc120 the operand dimension lived only in a param SUMMARY
(``octonion_conjugate``'s "8" was PROSE), and ``qm.*`` / ``cd`` ops carried no
DSL descriptor at all, so a driver had to INFER the rung from the op NAME. The
``ops`` map closes that last hardcode: ``ops["octonion_conjugate"]["consumes"]``
reads ``{"ladder": "cayley_dickson", "rung": 8}`` directly; ``ops["cd_promote"]``
reads a ``"any"`` (variadic) consume and an ``"arg:dim"`` (rung-from-argument)
produce. This makes the DSL/schema the SSoT for carrier ROUTING (the third leg
alongside chaining ``dsl.Chain`` and composition ``dsl.make_class``). It is pure
metadata — no op behaviour changes, no ABI impact, no new public callable
(``carrier_ladder_descriptor`` gains a key; tools.total is unchanged).
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


# ── the per-op CARRIER CONTRACT map (rc120; #1254 / F1041) ────────────────────
#
# Machine-readable per-op carrier RUNG: which rung each op CONSUMES / PRODUCES,
# so a driver routes a carrier to a consumer WITHOUT a hardcoded op→rung
# name-map or a register-length heuristic. Extends the ladder descriptor from
# "which ladders exist + their promote/project paths" to "which rung each op
# sits at" — the per-op leg of the F1041 declarative-routing ask.
#
# Each entry is keyed by the op's BARE LEAF name and maps to
#   {"tool": <full ToolEntry name>, "consumes": <slot>, "produces": <slot>}.
# A SLOT is one of:
#   * a LADDER slot     {"ladder": <ladder name>, "rung": <rung-value>}
#   * a non-ladder slot {"ladder": None, "type": <typename>}  — a carrier OUTSIDE
#                       the promote/project ladders (Mat / float / bool / list /
#                       dict / scalars), routing-irrelevant but declared honestly.
#
# A rung-value is one of:
#   * an int          a FIXED rung — a power-of-two dim {1,2,4,8,16} on
#                     cayley_dickson; {1,2,3} on variable; {1,2} on variable_q.
#   * "any"           VARIADIC — the op works at ANY rung of its ladder (the
#                     consume side of promote / project / mult + the cd predicates).
#   * "same"          (produce) the SAME rung it consumed — a ladder endomorphism
#                     (cd_mult / cd_conjugate).
#   * "arg:<param>"   (produce) the rung equals the int value of the call argument
#                     <param> (cd_promote → "arg:dim"; {poly,qpoly}_promote →
#                     "arg:n_vars").
#   * "step_down"     (produce) one rung DOWN the ladder from the consumed rung,
#                     per the ladder's sorted `rungs` values (cd_project halves
#                     the dim; {poly,qpoly}_project drop one variable).
#
# SELF-CONSISTENCY: every INT rung an op references MUST appear in
# carrier_ladder_descriptor()'s `ladders[<ladder>].rungs` values — a
# cayley_dickson rung-8 op references the SAME 8 the octonion 'O' rung declares.
# The rc120 test enforces this so the two surfaces cannot drift.

# reusable non-ladder slots (produce/consume carriers off the ladders)
_MAT = {"ladder": None, "type": "Mat"}
_FLOAT = {"ladder": None, "type": "float"}
_SCALARS = {"ladder": None, "type": "scalars"}


def _cd(rung: Any) -> Dict[str, Any]:
    """A Cayley–Dickson ladder slot at ``rung``."""
    return {"ladder": "cayley_dickson", "rung": rung}


def _var(rung: Any) -> Dict[str, Any]:
    """An ordinary variable-ladder slot at ``rung``."""
    return {"ladder": "variable", "rung": rung}


def _varq(rung: Any) -> Dict[str, Any]:
    """A q variable-ladder slot at ``rung``."""
    return {"ladder": "variable_q", "rung": rung}


_OP_CONTRACTS: Dict[str, Dict[str, Any]] = {
    # ── Cayley–Dickson: qm.octonion (FIXED rung 8) ────────────────────────────
    "octonion_conjugate": {
        "tool": "srmech.qm.octonion.octonion_conjugate",
        "consumes": _cd(8), "produces": _cd(8)},
    "octonion_norm": {
        "tool": "srmech.qm.octonion.octonion_norm",
        "consumes": _cd(8), "produces": _FLOAT},
    "octonion_left_mult": {
        "tool": "srmech.qm.octonion.octonion_left_mult",
        "consumes": _cd(8), "produces": _MAT},
    "octonion_right_mult": {
        "tool": "srmech.qm.octonion.octonion_right_mult",
        "consumes": _cd(8), "produces": _MAT},
    "octonion_exp": {
        "tool": "srmech.qm.octonion.octonion_exp",
        "consumes": _SCALARS, "produces": _cd(8)},
    "octonion_exp_series_truncate": {
        "tool": "srmech.qm.octonion.octonion_exp_series_truncate",
        "consumes": _SCALARS, "produces": _cd(8)},
    "octonion_twiddle": {
        "tool": "srmech.qm.octonion.octonion_twiddle",
        "consumes": _SCALARS, "produces": _cd(8)},
    # ── Cayley–Dickson: qm.quaternion (FIXED rung 4) ──────────────────────────
    "quaternion_conjugate": {
        "tool": "srmech.qm.quaternion.quaternion_conjugate",
        "consumes": _cd(4), "produces": _cd(4)},
    "quaternion_norm": {
        "tool": "srmech.qm.quaternion.quaternion_norm",
        "consumes": _cd(4), "produces": _FLOAT},
    "quaternion_left_mult": {
        "tool": "srmech.qm.quaternion.quaternion_left_mult",
        "consumes": _cd(4), "produces": _MAT},
    "quaternion_right_mult": {
        "tool": "srmech.qm.quaternion.quaternion_right_mult",
        "consumes": _cd(4), "produces": _MAT},
    "quaternion_exp": {
        "tool": "srmech.qm.quaternion.quaternion_exp",
        "consumes": _SCALARS, "produces": _cd(4)},
    "quaternion_exp_series_truncate": {
        "tool": "srmech.qm.quaternion.quaternion_exp_series_truncate",
        "consumes": _SCALARS, "produces": _cd(4)},
    "quaternion_twiddle": {
        "tool": "srmech.qm.quaternion.quaternion_twiddle",
        "consumes": _SCALARS, "produces": _cd(4)},
    # ── Cayley–Dickson: generic cascade.cd_* (VARIADIC "any" rung) ────────────
    "cd_mult": {
        "tool": "srmech.amsc.cascade.cd_mult",
        "consumes": _cd("any"), "produces": _cd("same")},
    "cd_conjugate": {
        "tool": "srmech.amsc.cascade.cd_conjugate",
        "consumes": _cd("any"), "produces": _cd("same")},
    "cd_norm_sq": {
        "tool": "srmech.amsc.cascade.cd_norm_sq",
        "consumes": _cd("any"), "produces": {"ladder": None, "type": "Fraction"}},
    "left_mult_kernel": {
        "tool": "srmech.amsc.cascade.left_mult_kernel",
        "consumes": _cd("any"), "produces": {"ladder": None, "type": "list"}},
    "left_mult_is_invertible": {
        "tool": "srmech.amsc.cascade.left_mult_is_invertible",
        "consumes": _cd("any"), "produces": {"ladder": None, "type": "bool"}},
    # ── the Cayley–Dickson PROMOTE / PROJECT (variadic + rung-from-arg) ───────
    "cd_promote": {
        "tool": "srmech.amsc.cascade.cd_promote",
        "consumes": _cd("any"), "produces": _cd("arg:dim")},
    "cd_project": {
        "tool": "srmech.amsc.cascade.cd_project",
        "consumes": _cd("any"), "produces": _cd("step_down")},
    # ── the ordinary variable ladder PROMOTE / PROJECT ────────────────────────
    "poly_promote": {
        "tool": "srmech.amsc.carrier_ladder.poly_promote",
        "consumes": _var("any"), "produces": _var("arg:n_vars")},
    "poly_project": {
        "tool": "srmech.amsc.carrier_ladder.poly_project",
        "consumes": _var("any"), "produces": _var("step_down")},
    # ── the q variable ladder PROMOTE / PROJECT ───────────────────────────────
    "qpoly_promote": {
        "tool": "srmech.amsc.carrier_ladder.qpoly_promote",
        "consumes": _varq("any"), "produces": _varq("arg:n_vars")},
    "qpoly_project": {
        "tool": "srmech.amsc.carrier_ladder.qpoly_project",
        "consumes": _varq("any"), "produces": _varq("step_down")},
    # ── the PROSE-SIDE constructors (produce a FIXED rung from raw ints) ──────
    "bipoly_from_coeffs": {
        "tool": "srmech.amsc.zeilberger.bipoly_from_coeffs",
        "consumes": {"ladder": None, "type": "list[list[int]]"},
        "produces": _var(2)},
    "tripoly_from_coeffs": {
        "tool": "srmech.amsc.tripoly.tripoly_from_coeffs",
        "consumes": {"ladder": None, "type": "list[list[list[int]]]"},
        "produces": _var(3)},
    "qpoly_from_coeffs": {
        "tool": "srmech.amsc.qpoly.qpoly_from_coeffs",
        "consumes": {"ladder": None, "type": "list"},
        "produces": _varq(1)},
    "qbipoly_from_coeffs": {
        "tool": "srmech.amsc.qbipoly.qbipoly_from_coeffs",
        "consumes": {"ladder": None, "type": "list"},
        "produces": _varq(2)},
}


def _op_contracts() -> Dict[str, Dict[str, Any]]:
    """Fresh (mutation-safe) copies of :data:`_OP_CONTRACTS` for the descriptor's
    ``"ops"`` view — the same rebuild-fresh-each-call discipline the rest of
    :func:`carrier_ladder_descriptor` follows."""
    return {
        leaf: {
            "tool": spec["tool"],
            "consumes": dict(spec["consumes"]),
            "produces": dict(spec["produces"]),
        }
        for leaf, spec in _OP_CONTRACTS.items()
    }


# ── the declarative coherency map (the driver's routing table) ────────────────

def carrier_ladder_descriptor() -> Dict[str, Any]:
    """The declarative CARRIER-LADDER coherency map (rc116; #1248 / F1038) — a
    small, static descriptor a driver (e.g. siona's result register, F1024)
    reads to auto-route a lower-rung carrier UP to any consumer that accepts a
    higher rung.

    Returns a plain ``dict`` with THREE views:

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
    - ``"ops"`` (rc120; #1254 / F1041): the per-op CARRIER CONTRACT — for each
      op leaf name, ``{"tool": <full ToolEntry name>, "consumes": <slot>,
      "produces": <slot>}``. A slot is a LADDER slot ``{"ladder", "rung"}`` or a
      non-ladder slot ``{"ladder": None, "type"}``. The rung is a fixed int, or
      ``"any"`` (variadic), ``"same"`` (endomorphism), ``"arg:<param>"`` (from a
      call argument), or ``"step_down"`` (one rung down). This lets a driver read
      ``ops["octonion_conjugate"]["consumes"]["rung"] == 8`` and
      ``ops["cd_promote"]["produces"]["rung"] == "arg:dim"`` DIRECTLY — no
      op→rung name-map, no register-length heuristic. Every int rung agrees with
      the ``ladders`` rungs table (a rung-8 op references the octonion ``'O'``).

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
        "ops": _op_contracts(),
    }
