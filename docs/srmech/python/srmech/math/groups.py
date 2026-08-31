"""``srmech.math.groups`` — the REPRESENTATION stratum over finite Cayley
tables (rc456 tiers 1–2; rc457 tier 3; rc458 tier 4).

THE GAP THIS CLOSES
===================
A shipped workflow claimed "products of cycles are abelian, hence carry no
irrep of dimension > 1".  That is TRUE of the DIRECT product and FALSE of the
SEMIDIRECT product — measured at the same order 21, built from the same two
cycles::

    C7 x C3  (direct)      abelian      degrees [1]*21          max dim 1
    C7 : C3  (semidirect)  NON-abelian  degrees [1,1,1,3,3]     max dim 3
    Cn : C2 by INVERSION   NON-abelian  = dihedral              max dim 2

— and the tree could not state any of it about itself: measured coverage of
the representation stratum via ``srmech.introspect.resolve`` was **0 of 10**
(``character_table`` / ``conjugacy_classes`` / ``irrep_dimensions`` /
``semidirect_product`` / ``abelianization`` / ``derived_subgroup`` /
``cayley_graph`` and kin, ALL absent).  An external oracle had to be reached
for.  This module is the closure of that gap: tiers 1–2 are integer /
permutation combinatorics (the constructors and the subgroup / quotient /
graph reads) plus EXACT cyclotomic character tables; tier 3 (rc457) is the
readout layer over the tier-2 payload — :func:`frobenius_schur_indicator`,
:func:`fusion_multiplicities` and :func:`central_idempotents`, each consuming
a :func:`character_table` payload dict VERBATIM rather than re-running the
split-and-lift.

THE READING THE MODULE EQUIPS THE TREE TO TEST
==============================================
Class **K** (pin-slot / sign-flip / phase boundary) acting on Class **I**
(cycle) IS the non-abelianiser: ``Cn : C2`` by inversion is literally a
Class-K sign flip acting on a Class-I cycle, and it is dihedral.  The A–N
alphabet already contains its own non-abelianiser; earlier work used K as a
sign INSIDE an op and never as the COUPLING BETWEEN ops.
:func:`semidirect_product` is that coupling made into an operand.

DIVISION OF LABOUR WITH ``srmech.cascade.conjugacy_census``
===========================================================
The census is the **guarded magma instrument**: it answers "is this even a
group, and what would classes mean if it is not" — both bracketings, the
class-equation disagreement, the 5/8 read.  :func:`conjugacy_classes` here is
the **group-only** peer: it REFUSES a non-group (``ValueError``), takes the
census's class partition VERBATIM as its single SSoT, and returns the maps
the census does not (``class_of`` / ``representatives`` / ``inverse_class`` /
``square_class`` / ``inverses``) — the exact payload the character table and
the tier-3 ops (fusion / Frobenius–Schur) consume.  There is no second
union-find in this module.

THE VALUE CARRIER (tier 2), STATED ONCE
=======================================
Character values are algebraic INTEGERS in the cyclotomic ring ``ℤ[ζ_e]``
(``e`` = the group exponent).  Every table value ships as a plain integer
coordinate vector of length ``φ(e)`` in the ``ζ_e`` power basis, reduced mod
``Φ_e`` — the SAME representation :mod:`srmech.cascade.exact_dft` runs its
exact spectra on.  ALL values are vectors, including the rational ones
(``χ(1) = d`` appears as ``(d, 0, …, 0)``); scalars and vectors are never
mixed, so the silent-wrong-answer analogue of a mixed carrier is
unrepresentable.  A caller wanting DIVISION lifts into
:class:`srmech.math.qalg.Qalg` over ``m = Φ_e`` — two lines, shown in
:func:`character_table`'s docstring — but the table itself never needs a
rational.

TIER 4 (rc458) — THE REPRESENTATION ITSELF
==========================================
Tiers 1–3 stop at CHARACTERS: every value is a trace, and rc457's
``central_idempotents`` docstring records exactly why the module-subspace
isotypic projector could not ship — no ``rho: G -> GL(V)`` existed anywhere
in the tree.  Tier 4 is that object.  :func:`permutation_representation`
mints a REP PAYLOAD dict (``rho(g)`` as actual matrices over an exact field,
element-indexed by the SAME Cayley-table indexing — that indexing IS the
composition contract), :func:`character_of` is the bridge back to tier 2/3
(trace readout), :func:`decompose_representation` projects onto the irrep
eigenbasis (multiplicities), :func:`isotypic_projector` is the op rc457
declined — the evaluation ``rho(e_chi)`` that ``central_idempotents``'
docstring promised the caller would perform, now shipped —
:func:`tensor_product_representation` / :func:`direct_sum_representation`
close the payload under ⊗ / ⊕, and :func:`intertwiner_space` is the Schur
readout ``Hom_G(V1, V2)`` over the exact-ℚ :class:`srmech.math.qmat.QMat`
nullspace.  :func:`zeta_mul` is the public promotion of the private
``_zeta_mul`` ring kernel (rc456 promised it, rc457 deferred it, this tier
delivers it).

The rep-payload carrier, stated once: matrices are plain 0/1 ints
(``kind="permutation"``) or CANONICAL ``(num, den)`` plain-int pairs with
``gcd == 1``, ``den >= 1`` (``kind="general"``) — canonicality is
load-bearing because ``matrices_sha256`` is a content address, so two
spellings of one rep must be one hash.  The pinned matrix convention:
``matrices[g] · e_j = e_{action[g][j]}`` (column ``j`` carries its 1 in row
``action[g][j]``); vectorization everywhere is ROW-MAJOR (the
``qmat._row_major_pairs`` house form).  The ζ-vector ops (decompose /
isotypic) keep the tier-2 value carrier: integer numerator vectors in the
``ζ_e`` power basis over ONE explicit denominator, division never performed
(the ``central_idempotents`` deferred-division shape).

TIER 4, THE ζ DIALECT (rc462, `#T1179`)
=======================================
Through rc461 a rep payload could only be exact-ℚ, and the tier-2 character
table could not be reached by a rep whose entries were not rational — which
excluded exactly the interesting reps: the ones whose Frobenius–Schur
indicator is ``0`` or ``-1``.  ``kind == "cyclotomic"`` is the ``ℚ(ζ_e)``
widening, and it ships WITH ITS FIRST PRODUCER because a checker widened
alone mints a dialect no producer can write and no consumer can read.

* the CELL is a length-``φ(e)`` tuple of canonical ``(num, den)`` plain-int
  pairs — coordinates in the ``ζ_e`` power basis low→high, the SAME
  convention :func:`zeta_mul` and the character table already use;
* the PAYLOAD gains ``e`` and ``phi_e``, and ``field`` becomes
  ``"Q(zeta_<e>)"``; the two are COUPLED in both directions so the dialect
  cannot be half-declared;
* the CONTENT ADDRESS takes a third serializer branch with a ``zeta{e}``
  prefix.  Not a widened general branch: a third branch leaves both
  existing branches untaken, so no shipped ℚ digest can move *by
  construction*, and the prefix separates ``φ(3) == φ(4) == φ(6) == 2``
  rings that would otherwise share a body;
* :func:`induced_representation` is the producer (monomial ``Ind_H^G`` of a
  linear character) and :func:`zeta_conjugate` is the ``Gal(ℚ(ζ_e)/ℚ)``
  action on it;
* FOUR consumers read the dialect — the trace path, :func:`character_of`,
  :func:`decompose_representation`, :func:`isotypic_projector` — and THREE
  REFUSE it with a named law: :func:`tensor_product_representation` and
  :func:`direct_sum_representation` (dialect law) and
  :func:`intertwiner_space` (carrier law: its engine is
  :meth:`srmech.math.qmat.QMat.nullspace`, exact-ℚ only, and no exact
  ``ℚ(ζ_e)``-matrix carrier ships anywhere in :mod:`srmech.math`).  A
  refusal that NAMES its law is a complete state; a consumer that crashes
  on what the checker admits is the dialect defect relocated.

Exact arithmetic ONLY: no float, no ``abs`` — the sign-handling sites are
:func:`_small_lift` (the named Class-K pin-slot at the ``p/2`` phase
boundary with Class-C re-application) and :func:`_pair_magnitude` (the
Class-K pin-slot at zero the canonical-pair law reads through).  All
content addresses route through :func:`srmech.amsc.format.sha256_bytes`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from srmech.amsc.format import sha256_bytes
from srmech.cascade import conjugacy_census
from srmech.math.cyclic import gcd, mod_add, mod_inv, mod_pow
from srmech.math.modular_linalg import gf_nullspace, gf_solve
from srmech.math.poly import cyclotomic_polynomial
from srmech.math.primes import factor, is_prime
from srmech.math.qmat import QMat

__all__ = [
    "abelianization",
    "cayley_graph",
    "central_idempotents",
    "character_of",
    "character_table",
    "conjugacy_classes",
    "cyclic_group",
    "decompose_representation",
    "derived_subgroup",
    "direct_sum_representation",
    "frobenius_schur_indicator",
    "fusion_multiplicities",
    "induced_representation",
    "intertwiner_space",
    "irrep_dimensions",
    "isotypic_projector",
    "permutation_representation",
    "quotient_group",
    "semidirect_product",
    "tensor_product_representation",
    "zeta_conjugate",
    "zeta_mul",
]


# ──────────────────────────────────────────────────────────────────────
# private helpers — table validation / scans (NO cross-import of the
# census's private ``_coerce_table``: constructors validate their own
# outputs by construction, and census-routed ops ride the census guard)
# ──────────────────────────────────────────────────────────────────────


def _check_table(op: str, cayley_table: Sequence[Sequence[int]]) -> List[List[int]]:
    """Validate an ``n x n`` Cayley table of element indices."""
    rows = [list(r) for r in cayley_table]
    n = len(rows)
    if n == 0:
        raise ValueError(f"{op}: cayley_table must be non-empty")
    for i, row in enumerate(rows):
        if len(row) != n:
            raise ValueError(
                f"{op}: cayley_table must be square; row {i} has "
                f"{len(row)} cells, expected {n}")
        for j, v in enumerate(row):
            if not isinstance(v, int) or isinstance(v, bool):
                raise TypeError(
                    f"{op}: cayley_table[{i}][{j}] must be int; "
                    f"got {type(v).__name__}")
            if not 0 <= v < n:
                raise ValueError(
                    f"{op}: cayley_table[{i}][{j}] = {v} outside [0, {n})")
    return rows


def _identity_of(tbl: List[List[int]]) -> Optional[int]:
    """The two-sided identity index, or ``None``."""
    n = len(tbl)
    for e in range(n):
        if all(tbl[e][x] == x and tbl[x][e] == x for x in range(n)):
            return e
    return None


def _inverse_scan(tbl: List[List[int]], e: int) -> Optional[List[int]]:
    """Two-sided inverses against identity ``e`` by an O(n²) table scan —
    a scan, not a second union-find.  ``None`` when any element lacks a
    unique two-sided inverse."""
    n = len(tbl)
    inv: List[int] = []
    for x in range(n):
        found = [y for y in range(n)
                 if tbl[x][y] == e and tbl[y][x] == e]
        if len(found) != 1:
            return None
        inv.append(found[0])
    return inv


def _check_associative(op: str, label: str, tbl: List[List[int]]) -> None:
    """Raise ``ValueError`` naming the first failing triple if the table is
    not associative (the operand-group half of the semidirect guard)."""
    n = len(tbl)
    for a in range(n):
        for b in range(n):
            for c in range(n):
                if tbl[tbl[a][b]][c] != tbl[a][tbl[b][c]]:
                    raise ValueError(
                        f"{op}: {label} is not associative - "
                        f"({a}*{b})*{c} != {a}*({b}*{c})")


def _table_bytes(table: List[List[int]]) -> bytes:
    """Canonical bytes of an integer table: rows newline-joined, cells
    comma-joined (the ``conjugacy_census`` partition canonicalisation)."""
    return "\n".join(
        ",".join(str(v) for v in row) for row in table).encode("utf-8")


def _small_lift(residue: int, p: int) -> int:
    """The Dixon small-representative lift ``GF(p) → ℤ``: residues in
    ``[0, p)`` map to ``(−p/2, p/2)``.

    This is the module's ONE sign-handling site, and it is a named
    **Class K pin-slot** at the ``p/2`` phase boundary with **Class C**
    re-application — the same shape as ``exact_dft``'s ``ζ^{N/2} = −1``
    negacyclic reduction (a residue past the boundary re-enters with its
    orientation flipped).  Never an ALU magnitude call.
    """
    if 2 * residue > p:
        return residue - p          # Class K flip at p/2, Class C re-entry
    return residue


# ──────────────────────────────────────────────────────────────────────
# cyclotomic power-basis arithmetic.  _zeta_mul is the PRIVATE kernel;
# its public registered spelling is :func:`zeta_mul` (tier 4, rc458 —
# the promotion rc456 promised and rc457 deliberately deferred).  The
# internal hot paths (fusion_multiplicities, isotypic_projector) keep
# calling the kernel directly — the public op adds the plain-int /
# monic-Φ_e guards a wire crossing needs, and guards cost per call.
# The ADR-0009 dispatch question the rc457 deferral named is RESOLVED
# as a RECORDED PROJECTION GAP (see zeta_mul's docstring): the C
# near-peer srmech_riemann_theta_cyc_mul speaks a different wire
# (ζ-power-table reduction, deg <= 16, int64 fast path) under a foreign
# namespace, and the table-based wire adapter from phi_e is deliberately
# deferred per the stay-the-course-with-Python ruling.
# ──────────────────────────────────────────────────────────────────────


def _reduce_mod_phi(vec: List[int], phi: Sequence[int]) -> Tuple[int, ...]:
    """Reduce an integer coefficient vector (powers of ``ζ``, low→high) mod
    the monic ``Φ_e`` given by ``phi`` (low→high) to length ``φ(e)``.
    Exact integer polynomial division — no rationals ever appear because
    ``Φ_e`` is monic and character values are algebraic integers."""
    deg = len(phi) - 1
    work = list(vec)
    if len(work) < deg:
        work.extend([0] * (deg - len(work)))
    for idx in range(len(work) - 1, deg - 1, -1):
        c = work[idx]
        if c:
            base = idx - deg
            for t in range(deg + 1):
                work[base + t] -= c * phi[t]
    return tuple(work[:deg])


def _zeta_mul(u: Sequence[int], v: Sequence[int],
              phi: Sequence[int]) -> Tuple[int, ...]:
    """The exact ``ℤ[ζ_e]`` ring product of two power-basis integer vectors,
    reduced mod the monic ``Φ_e`` whose low→high coefficients are ``phi``
    (the ``phi_e`` field of a :func:`character_table` payload).  Integer
    convolution then :func:`_reduce_mod_phi`; exact, no float."""
    out = [0] * (len(u) + len(v) - 1 if (u and v) else 1)
    for i, ui in enumerate(u):
        if ui:
            for j, vj in enumerate(v):
                if vj:
                    out[i + j] += ui * vj
    return _reduce_mod_phi(out, phi)


def _zeta_power_table(phi: Sequence[int], e: int) -> List[Tuple[int, ...]]:
    """``T[j] = ζ_e^j`` reduced to the power basis ``{1, ζ, …, ζ^{φ(e)−1}}``
    — the same table shape ``exact_dft``'s general-N reduction builds, here
    derived from the public :func:`srmech.math.poly.cyclotomic_polynomial`
    coefficients rather than a private cross-import."""
    deg = len(phi) - 1
    red_top = [-phi[i] for i in range(deg)]
    table: List[Tuple[int, ...]] = []
    cur = [0] * deg
    cur[0] = 1
    for _ in range(e):
        table.append(tuple(cur))
        carry = cur[deg - 1]
        nxt = [0] * deg
        for i in range(deg - 1, 0, -1):
            nxt[i] = cur[i - 1]
        if carry:
            for i in range(deg):
                nxt[i] += carry * red_top[i]
        cur = nxt
    return table


# ──────────────────────────────────────────────────────────────────────
# tier 1 — constructors
# ──────────────────────────────────────────────────────────────────────


def cyclic_group(n: int) -> Dict[str, Any]:
    """The cyclic group ``C_n`` as a Cayley table — the Class-I producer.

    Args:
        n: the order, ``>= 1``.

    Returns:
        ``{"n", "order", "elements", "cayley_table", "identity",
        "inverses"}`` — the same table shape :func:`dihedral_group` and
        :func:`srmech.cascade.unit_loop` hand back, so every census and
        every op in this module eats it interchangeably.
        ``cayley_table[i][j]`` is ``(i + j) mod n`` via the c_dispatched
        :func:`srmech.math.cyclic.mod_add`; ``inverses[i]`` is the additive
        inverse ``(n − i) mod n``.

    **Why it ships.** ``srmech.cascade.finite_group`` documents the exact
    reachability gap: ``unit_loop`` yields only power-of-two orders and
    ``group_algebra_table`` raises on 3, 5, 12, 24 — so no bare cycle of
    general order ``n`` was reachable at all, which made the order-``n``
    cyclic character tables (and every semidirect operand) unreachable.
    This op closes that gap on the cyclic side; it is the operand producer
    :func:`semidirect_product` composes.

    Note:
        Exact integers; Class I throughout.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError(f"cyclic_group: n must be int; got {type(n).__name__}")
    if n < 1:
        raise ValueError(f"cyclic_group requires n >= 1; got {n}")
    table = [[mod_add(i, j, n) for j in range(n)] for i in range(n)]
    return {
        "n": n,
        "order": n,
        "elements": list(range(n)),
        "cayley_table": table,
        "identity": 0,
        "inverses": [(n - i) % n for i in range(n)],
    }


def semidirect_product(n_table: Sequence[Sequence[int]],
                       h_table: Sequence[Sequence[int]],
                       action: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """The semidirect product ``N ⋊ H`` from two Cayley tables and an action
    — the rc456 thesis op: **Class K coupling BETWEEN two Class-I operands**,
    the non-abelianiser the A–N alphabet already contained.

    Args:
        n_table: the Cayley table of ``N`` (a group; validated).
        h_table: the Cayley table of ``H`` (a group; validated).
        action: ``action[h]`` is a permutation TABLE of ``range(|N|)``
            giving ``φ_h`` — a table, not a callable, because a callable
            cannot cross JSON-RPC and these operands ARE the semantics
            (the ``conjugacy_census`` discipline).

    **The three pinned conventions** (all three load-bearing for the
    dihedral-equivalence test):

    * element index ``idx(a, h) = a·|H| + h``;
    * product ``(a1, h1)·(a2, h2) = (n_table[a1][action[h1][a2]],
      h_table[h1][h2])`` — ``φ`` applied to the LEFT factor's partner,
      i.e. a LEFT action;
    * homomorphism law ``action[h_table[h1][h2]][a] ==
      action[h1][action[h2][a]]``.

    Validation, each failure a ``ValueError`` naming the law: the operand
    tables are square, in-range, associative, with a two-sided identity and
    unique two-sided inverses; each ``action[h]`` is a bijection of
    ``range(|N|)``; each ``action[h]`` is an automorphism of ``N``
    (``action[h][n_table[a][b]] == n_table[action[h][a]][action[h][b]]``);
    the action is a homomorphism (the law above); the identity of ``H``
    acts as the identity permutation.  Together these laws mathematically
    entail associativity of the product — the validation IS the guard (the
    rc456 tests additionally run the shipped census as an independent
    oracle).

    The DIRECT product is the trivial action (every ``action[h]`` the
    identity permutation) — that is how ``C7 × C3`` is built; there is no
    separate op.  ``Cn ⋊ C2`` by the inversion action is dihedral, which is
    the founding measurement this op exists to let the tree make.

    Returns:
        ``{"order", "elements" ([[a, h] …]), "cayley_table", "identity",
        "inverses", "n_order", "h_order", "table_sha256"}`` — the table is
        census-ready and Class-A content-addressed.

    Note:
        Exact integers; no ``abs``; the coupling is the operand, not a sign
        inside an op.
    """
    nt = _check_table("semidirect_product", n_table)
    ht = _check_table("semidirect_product", h_table)
    nn, nh = len(nt), len(ht)

    e_n = _identity_of(nt)
    if e_n is None:
        raise ValueError(
            "semidirect_product: n_table has no two-sided identity "
            "(operand-group law)")
    e_h = _identity_of(ht)
    if e_h is None:
        raise ValueError(
            "semidirect_product: h_table has no two-sided identity "
            "(operand-group law)")
    if _inverse_scan(nt, e_n) is None:
        raise ValueError(
            "semidirect_product: n_table lacks unique two-sided inverses "
            "(operand-group law)")
    if _inverse_scan(ht, e_h) is None:
        raise ValueError(
            "semidirect_product: h_table lacks unique two-sided inverses "
            "(operand-group law)")
    _check_associative("semidirect_product", "n_table", nt)
    _check_associative("semidirect_product", "h_table", ht)

    act = [list(r) for r in action]
    if len(act) != nh:
        raise ValueError(
            f"semidirect_product: action must have one permutation row per "
            f"H element; got {len(act)} rows for |H| = {nh}")
    for h, row in enumerate(act):
        if len(row) != nn or sorted(row) != list(range(nn)):
            raise ValueError(
                f"semidirect_product: action[{h}] is not a bijection of "
                f"range({nn}) (bijection law)")
    if act[e_h] != list(range(nn)):
        raise ValueError(
            "semidirect_product: the identity of H must act as the identity "
            "permutation (identity-action law)")
    for h in range(nh):
        for a in range(nn):
            for b in range(nn):
                if act[h][nt[a][b]] != nt[act[h][a]][act[h][b]]:
                    raise ValueError(
                        f"semidirect_product: action[{h}] is not an "
                        f"automorphism of N - it breaks the "
                        f"product ({a}, {b}) (automorphism law)")
    for h1 in range(nh):
        for h2 in range(nh):
            composed = ht[h1][h2]
            for a in range(nn):
                if act[composed][a] != act[h1][act[h2][a]]:
                    raise ValueError(
                        f"semidirect_product: action is not a homomorphism "
                        f"- action[{h1}*{h2}][{a}] != "
                        f"action[{h1}][action[{h2}][{a}]] "
                        f"(homomorphism law)")

    order = nn * nh
    table: List[List[int]] = [[0] * order for _ in range(order)]
    for a1 in range(nn):
        for h1 in range(nh):
            r = a1 * nh + h1
            row = table[r]
            for a2 in range(nn):
                for h2 in range(nh):
                    row[a2 * nh + h2] = (
                        nt[a1][act[h1][a2]] * nh + ht[h1][h2])
    identity = e_n * nh + e_h
    inverses: List[int] = []
    for x in range(order):
        for y in range(order):
            if table[x][y] == identity and table[y][x] == identity:
                inverses.append(y)
                break
    return {
        "order": order,
        "elements": [[a, h] for a in range(nn) for h in range(nh)],
        "cayley_table": table,
        "identity": identity,
        "inverses": inverses,
        "n_order": nn,
        "h_order": nh,
        "table_sha256": sha256_bytes(_table_bytes(table)),
    }


# ──────────────────────────────────────────────────────────────────────
# tier 1 — group-only reads
# ──────────────────────────────────────────────────────────────────────


def conjugacy_classes(cayley_table: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """The conjugacy-class maps of a finite GROUP — the group-only peer of
    :func:`srmech.cascade.conjugacy_census`, and the class-data SSoT every
    tier-2/tier-3 op in this module reads.

    Division of labour: the census is the **guarded magma instrument** — it
    answers "is this even a group, and what would classes mean if it is
    not" (both bracketings, the class-equation disagreement).  THIS op is
    group-only: it delegates the partition to the census, REFUSES a
    non-group with ``ValueError``, and returns the maps the census does not
    — ``class_of``, ``representatives``, ``inverse_class``,
    ``square_class``, ``inverses``.  The class index order is the census's
    ``class_partition`` order VERBATIM (one SSoT; never re-sorted), so a
    ``character_table`` column and a census block never disagree.

    Args:
        cayley_table: the ``n × n`` table; must be a group (associative,
            two-sided identity, unique two-sided inverses) or the op
            refuses.  The non-associative unit loops (M16, M32) are the
            worked negatives.

    Returns:
        ``{"order", "k", "classes", "class_of", "representatives",
        "class_sizes", "identity", "inverses", "inverse_class",
        "square_class", "class_partition_sha256"}``.  ``inverse_class[j]``
        is the class of ``rep_j⁻¹`` (conjugation-as-permutation — this is
        what makes ``χ̄(g) = χ(g⁻¹)`` computable with no Galois machinery);
        ``square_class[j]`` is the class of ``rep_j²`` (well defined since
        ``(hgh⁻¹)² = hg²h⁻¹``), shipped now because the Frobenius–Schur
        indicator in tier 3 is exactly a weighted sum over it.

    Note:
        The inverses are an O(n²) table scan — a scan, not a second
        union-find.  Exact integers; no ``abs``.
    """
    census = conjugacy_census(cayley_table)
    if not census["is_group"]:
        raise ValueError(
            "conjugacy_classes: the table is not a group "
            f"(is_associative={census['is_associative']}, "
            f"has_identity={census['has_identity']}, "
            f"has_inverses={census['has_inverses']}); "
            "conjugacy_census is the guarded magma instrument for this "
            "operand - classes on a loop depend on an undeclared bracketing")
    tbl = [list(r) for r in cayley_table]
    n = census["order"]
    e = census["identity"]
    inv = _inverse_scan(tbl, e)
    blocks = census["class_partition"]
    k = len(blocks)
    class_of = [0] * n
    for ci, block in enumerate(blocks):
        for x in block:
            class_of[x] = ci
    reps = [block[0] for block in blocks]
    return {
        "order": n,
        "k": k,
        "classes": blocks,
        "class_of": class_of,
        "representatives": reps,
        "class_sizes": [len(block) for block in blocks],
        "identity": e,
        "inverses": inv,
        "inverse_class": [class_of[inv[r]] for r in reps],
        "square_class": [class_of[tbl[r][r]] for r in reps],
        "class_partition_sha256": census["class_partition_sha256"],
    }


def derived_subgroup(cayley_table: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """The derived (commutator) subgroup ``[G, G]`` — Class E closure over
    Class C witnesses.

    Bracket convention, pinned: ``[g, h] = g⁻¹·h⁻¹·g·h``.  The op requires
    a group (the guard is one :func:`srmech.cascade.conjugacy_census` call,
    reused rather than re-derived), collects every commutator, then closes
    the set under the table product to a fixpoint (a finite group's
    subgroup closure needs no separate inverse pass — powers reach the
    inverse).

    Args:
        cayley_table: the ``n × n`` group table (``ValueError`` otherwise).

    Returns:
        ``{"order"`` (of G), ``"elements"`` (sorted indices),
        ``"subgroup_order", "index"`` (``order // subgroup_order``),
        ``"elements_sha256"}``.

    ``[G, G]`` is trivial exactly on the abelian carriers, whole exactly on
    the perfect ones, and in between it is the datum
    :func:`abelianization` quotients by — the number of degree-1 rows of
    :func:`character_table` equals ``order // subgroup_order``, which the
    rc456 tests execute as a cross-op identity.

    Note:
        Exact integers; no ``abs``.
    """
    census = conjugacy_census(cayley_table)
    if not census["is_group"]:
        raise ValueError(
            "derived_subgroup: the table is not a group "
            f"(is_associative={census['is_associative']}, "
            f"has_identity={census['has_identity']}, "
            f"has_inverses={census['has_inverses']})")
    tbl = [list(r) for r in cayley_table]
    n = census["order"]
    e = census["identity"]
    inv = _inverse_scan(tbl, e)
    elements = {e}
    for g in range(n):
        for h in range(n):
            elements.add(tbl[tbl[inv[g]][inv[h]]][tbl[g][h]])
    frontier = list(elements)
    while frontier:
        x = frontier.pop()
        for y in list(elements):
            for z in (tbl[x][y], tbl[y][x]):
                if z not in elements:
                    elements.add(z)
                    frontier.append(z)
    subgroup = sorted(elements)
    body = ",".join(str(x) for x in subgroup).encode("utf-8")
    return {
        "order": n,
        "elements": subgroup,
        "subgroup_order": len(subgroup),
        "index": n // len(subgroup),
        "elements_sha256": sha256_bytes(body),
    }


def quotient_group(cayley_table: Sequence[Sequence[int]],
                   normal_elements: Sequence[int]) -> Dict[str, Any]:
    """The quotient group ``G / N`` as a Cayley table over cosets.

    Args:
        cayley_table: the ``n × n`` table of ``G``.
        normal_elements: the element indices of the normal subgroup ``N``.

    Validation, each failure a ``ValueError`` naming the law: the table is
    square and in-range with a two-sided identity and unique two-sided
    inverses; ``normal_elements`` contains the identity and is closed under
    product and inverse (else ``not a subgroup``); ``∀g:
    {g·n·g⁻¹} ⊆ N`` (else ``not normal`` — the S3-mod-⟨reflection⟩
    negative).  The coset table is then checked WELL-DEFINED over all
    ``n²`` products (every ``x ∈ A, y ∈ B`` lands in the same coset), which
    is the guard that catches a non-associative operand this op does not
    otherwise probe — a coset product that depends on the representative is
    refused, never averaged.

    Cosets are indexed by minimal element (ascending first-encounter order,
    which coincides).  Returns
    ``{"order" (=|G|/|N|), "cayley_table" (the coset table), "elements"
    (coset min-representatives), "coset_of" (element → coset index),
    "identity", "inverses", "coset_partition_sha256"}``.

    This op is public rather than private machinery because
    :func:`abelianization` needs the quotient internally regardless, and a
    public quotient removes a hole no other op covers (S3 / rotations is
    the two-element quotient a reader would otherwise hand-roll).

    Note:
        Exact integers; no ``abs``.
    """
    tbl = _check_table("quotient_group", cayley_table)
    n = len(tbl)
    e = _identity_of(tbl)
    if e is None:
        raise ValueError("quotient_group: cayley_table has no two-sided "
                         "identity")
    inv = _inverse_scan(tbl, e)
    if inv is None:
        raise ValueError("quotient_group: cayley_table lacks unique "
                         "two-sided inverses")
    sub: List[int] = []
    seen_sub = set()
    for v in normal_elements:
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError(
                f"quotient_group: normal_elements entries must be int; "
                f"got {type(v).__name__}")
        if not 0 <= v < n:
            raise ValueError(
                f"quotient_group: normal_elements entry {v} outside "
                f"[0, {n})")
        if v in seen_sub:
            raise ValueError(
                f"quotient_group: normal_elements entry {v} duplicated")
        seen_sub.add(v)
        sub.append(v)
    if e not in seen_sub:
        raise ValueError(
            "quotient_group: not a subgroup - the identity is missing")
    for x in sub:
        if inv[x] not in seen_sub:
            raise ValueError(
                f"quotient_group: not a subgroup - not closed under "
                f"inverse at element {x}")
        for y in sub:
            if tbl[x][y] not in seen_sub:
                raise ValueError(
                    f"quotient_group: not a subgroup - not closed under "
                    f"product at ({x}, {y})")
    for g in range(n):
        for x in sub:
            if tbl[tbl[g][x]][inv[g]] not in seen_sub:
                raise ValueError(
                    f"quotient_group: not normal - conjugating {x} by {g} "
                    f"leaves the subgroup")

    coset_of = [-1] * n
    coset_members: List[List[int]] = []
    for g in range(n):
        if coset_of[g] != -1:
            continue
        members = sorted(tbl[g][x] for x in sub)
        ci = len(coset_members)
        for m in members:
            if coset_of[m] != -1:
                raise ValueError(
                    "quotient_group: cosets do not partition the table "
                    "(the operand is not a group)")
            coset_of[m] = ci
        coset_members.append(members)
    q = len(coset_members)
    reps = [members[0] for members in coset_members]
    qtable = [[coset_of[tbl[reps[a]][reps[b]]] for b in range(q)]
              for a in range(q)]
    for x in range(n):
        for y in range(n):
            if coset_of[tbl[x][y]] != qtable[coset_of[x]][coset_of[y]]:
                raise ValueError(
                    "quotient_group: the coset product is not well defined "
                    "- the operand is not a group, or the subgroup is not "
                    "normal under its full closure")
    identity_coset = coset_of[e]
    qinv: List[int] = []
    for a in range(q):
        for b in range(q):
            if (qtable[a][b] == identity_coset
                    and qtable[b][a] == identity_coset):
                qinv.append(b)
                break
    partition = "\n".join(
        ",".join(str(x) for x in members)
        for members in coset_members).encode("utf-8")
    return {
        "order": q,
        "cayley_table": qtable,
        "elements": reps,
        "coset_of": coset_of,
        "identity": identity_coset,
        "inverses": qinv,
        "coset_partition_sha256": sha256_bytes(partition),
    }


def _table_pow(tbl: List[List[int]], x: int, k: int, e: int) -> int:
    """``x^k`` off a group table by square-and-multiply (Class I)."""
    result = e
    base = x
    while k:
        if k & 1:
            result = tbl[result][base]
        base = tbl[base][base]
        k >>= 1
    return result


def _p_adic_log(c: int, p: int, where: str) -> int:
    """The exact p-adic log of a pure prime power ``c = p^s`` (Class J —
    repeated integer division; no float).  A non-pure-power input is an
    internal-consistency ``ValueError`` — a guard that fires is evidence."""
    s = 0
    while c % p == 0:
        c //= p
        s += 1
    if c != 1:
        raise ValueError(
            f"{where}: a subgroup count that must be a pure power of {p} "
            f"is not — internal inconsistency (a guard that fires is "
            f"evidence)")
    return s


def abelianization(cayley_table: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """The abelianization ``G / [G, G]`` with its invariant factors — a
    Class-I result reached through a Class-E quotient, the splits by
    Class-J exact counting.

    Composition (each stage a shipped public op): :func:`derived_subgroup`
    → :func:`quotient_group` → invariant factors of the abelian quotient by
    exact counting.  For each prime ``p`` dividing ``|Q|`` (via the
    c_dispatched :func:`srmech.math.primes.factor`), ``c_k = #{x : x^{p^k}
    = e}`` is counted off the quotient table; the p-type partition ``λ``
    satisfies ``c_k = p^{Σ_i min(λ_i, k)}`` and is recovered by exact
    integer p-adic logs of successive counts (repeated integer division —
    never a float log).  Prime powers interleave largest-with-largest into
    the invariant-factor chain ``d_1 | d_2 | …``.

    Args:
        cayley_table: the ``n × n`` group table (``ValueError`` otherwise,
            via the derived-subgroup guard).

    Returns:
        ``{"invariant_factors"`` (ascending divisibility, ``∏ d_i =``
        quotient order), ``"order"`` (of the quotient), ``"quotient"`` (the
        full :func:`quotient_group` payload), ``"projection"`` (the
        quotient's ``coset_of`` — element → coset)``}``.

    Worked anchors the rc456 tests execute: S3 → ``[2]``; Q8 → ``[2, 2]``;
    C7⋊C3 → ``[3]``; C7×C3 → ``[21]``; D4 → ``[2, 2]``.  The count of
    degree-1 rows of :func:`character_table` equals ``∏ d_i`` — the linear
    characters ARE the characters of this quotient.

    Note:
        Exact integers; no ``abs``; no float.  (No TOML cascade-catalog
        descriptor ships this rc — a deliberate deferral recorded in the
        build report, not a stub.)
    """
    ds = derived_subgroup(cayley_table)
    quotient = quotient_group(cayley_table, ds["elements"])
    qt = quotient["cayley_table"]
    qn = quotient["order"]
    qe = quotient["identity"]
    primes_list: List[int] = []
    per_prime: List[List[int]] = []
    for p, _exp in factor(qn):
        parts_ge: List[int] = []
        s_prev = 0
        k = 1
        while True:
            pk = p ** k
            c = 0
            for x in range(qn):
                if _table_pow(qt, x, pk, qe) == qe:
                    c += 1
            s = _p_adic_log(c, p, "abelianization")
            m = s - s_prev
            if m == 0:
                break
            parts_ge.append(m)
            s_prev = s
            k += 1
        r = parts_ge[0] if parts_ge else 0
        lam = [sum(1 for m in parts_ge if m >= i) for i in range(1, r + 1)]
        primes_list.append(p)
        per_prime.append(lam)          # descending parts
    width = 0
    for lam in per_prime:
        if len(lam) > width:
            width = len(lam)
    invariant: List[int] = []
    for j in range(width):             # j = 0 → the LARGEST factor
        d = 1
        for p, lam in zip(primes_list, per_prime):
            if j < len(lam):
                d *= p ** lam[j]
        invariant.append(d)
    invariant.reverse()                # ascending: d_1 | d_2 | …
    return {
        "invariant_factors": invariant,
        "order": qn,
        "quotient": quotient,
        "projection": quotient["coset_of"],
    }


def cayley_graph(cayley_table: Sequence[Sequence[int]],
                 generators: Sequence[int],
                 convention: str) -> Dict[str, Any]:
    """The directed Cayley graph of a group under a generating set — Class L
    mints the graph object; the generator DIRECTION is the Class-C datum
    the ``convention`` parameter pins.

    Args:
        cayley_table: the ``n × n`` group table (``ValueError`` otherwise —
            the guard is one census call).
        generators: non-empty, in-range, duplicate-free element indices.
        convention: ``"right"`` (edges ``(x, table[x][g])``) or ``"left"``
            (``(x, table[g][x])``) — REQUIRED, caller-must-say, for the
            same reason :func:`srmech.cascade.dihedral_group`'s
            ``convention`` is: on a non-abelian group the two graphs are
            genuinely different edge sets and only the caller knows which
            multiplication it means.

    Emits ALL ``|G|·|generators|`` directed edges in element-major,
    generator-minor order.  An involution generator produces both
    orientations naturally — no special-casing, no dedup, so the edge
    count is exact and predictable.

    Returns:
        ``{"n", "edges"`` (2-tuples — the shipped laplacian edge contract,
        so ``dense_laplacian`` / ``magnetic_laplacian`` eat the list
        directly), ``"edge_generator"`` (parallel to ``edges``),
        ``"is_connected"`` (reachability from the identity — ``True`` iff
        the generators generate G), ``"edges_sha256"}``.

    This surface is EXACT-ONLY: it does NOT return a ``Mat`` and does NOT
    compute spectra.  The Class-L float boundary stays where it already
    lives (the ``dense_adjacency`` / ``dense_laplacian`` /
    ``magnetic_laplacian`` consumers); this op hands them the exact edge
    combinatorics.

    Note:
        Exact integers; no ``abs``.
    """
    if convention not in ("right", "left"):
        raise ValueError(
            f"cayley_graph: convention must be 'right' or 'left'; "
            f"got {convention!r}")
    census = conjugacy_census(cayley_table)
    if not census["is_group"]:
        raise ValueError(
            "cayley_graph: the table is not a group "
            f"(is_associative={census['is_associative']}, "
            f"has_identity={census['has_identity']}, "
            f"has_inverses={census['has_inverses']})")
    tbl = [list(r) for r in cayley_table]
    n = census["order"]
    gens: List[int] = []
    seen = set()
    for g in generators:
        if not isinstance(g, int) or isinstance(g, bool):
            raise TypeError(
                f"cayley_graph: generators entries must be int; "
                f"got {type(g).__name__}")
        if not 0 <= g < n:
            raise ValueError(
                f"cayley_graph: generator {g} outside [0, {n})")
        if g in seen:
            raise ValueError(f"cayley_graph: generator {g} duplicated")
        seen.add(g)
        gens.append(g)
    if not gens:
        raise ValueError("cayley_graph: generators must be non-empty")

    edges: List[Tuple[int, int]] = []
    edge_generator: List[int] = []
    for x in range(n):
        for g in gens:
            target = tbl[x][g] if convention == "right" else tbl[g][x]
            edges.append((x, target))
            edge_generator.append(g)

    succ: List[List[int]] = [[] for _ in range(n)]
    for a, b in edges:
        succ[a].append(b)
    e = census["identity"]
    visited = {e}
    queue = [e]
    while queue:
        x = queue.pop()
        for y in succ[x]:
            if y not in visited:
                visited.add(y)
                queue.append(y)
    body = "\n".join(f"{a},{b}" for a, b in edges).encode("utf-8")
    return {
        "n": n,
        "edges": edges,
        "edge_generator": edge_generator,
        "is_connected": len(visited) == n,
        "edges_sha256": sha256_bytes(body),
    }


# ──────────────────────────────────────────────────────────────────────
# tier 2 — exact cyclotomic character theory
# ──────────────────────────────────────────────────────────────────────


def _abelian_rows(tbl: List[List[int]], n: int, e_idx: int, expo: int,
                  reps: List[int],
                  zeta_pow: List[Tuple[int, ...]]
                  ) -> List[Tuple[int, List[Tuple[int, ...]]]]:
    """All ``n`` characters of an ABELIAN group table, built directly as
    ``ζ_e``-power products by iterative extension over a subgroup chain —
    pure Class I, no prime-field detour.  Characters are exponent maps
    ``element → ℤ/e``; each extension step picks the ``t`` solutions of
    ``t·x ≡ a (mod e)``, whose count is exactly the index ``t`` (guarded)."""
    subgroup = [e_idx]
    in_subgroup = {e_idx}
    chars: List[Dict[int, int]] = [{e_idx: 0}]
    while len(subgroup) < n:
        g = min(x for x in range(n) if x not in in_subgroup)
        t = 1
        x = g
        while x not in in_subgroup:
            x = tbl[x][g]
            t += 1
        anchor = x                      # g^t, inside the subgroup
        extended: List[Dict[int, int]] = []
        for chi in chars:
            a = chi[anchor]
            sols = [s for s in range(expo) if (t * s - a) % expo == 0]
            if len(sols) != t:
                raise ValueError(
                    "character_table: an abelian character extension did "
                    "not split into exactly [H<g> : H] branches - internal "
                    "inconsistency (a guard that fires is evidence)")
            for s in sols:
                nc = dict(chi)
                power = e_idx
                for step in range(1, t):
                    power = tbl[power][g]
                    for h in subgroup:
                        nc[tbl[h][power]] = (chi[h] + step * s) % expo
                extended.append(nc)
        grown = list(subgroup)
        power = e_idx
        for step in range(1, t):
            power = tbl[power][g]
            for h in subgroup:
                grown.append(tbl[h][power])
        subgroup = grown
        in_subgroup = set(subgroup)
        chars = extended
    return [(1, [zeta_pow[chi[rep]] for rep in reps]) for chi in chars]


def _dixon_rows(tbl: List[List[int]], n: int, e_idx: int, expo: int,
                orders: List[int], cc: Dict[str, Any],
                class_algebra: List[List[List[int]]],
                phi: List[int]
                ) -> List[Tuple[int, List[Tuple[int, ...]]]]:
    """The prime-field split-and-lift for a NON-abelian table: common
    eigenvectors of the commuting class matrices over GF(p), degrees and
    characters mod p, then the exact root-of-unity-multiplicity lift into
    ``ℤ[ζ_e]``.  See :func:`character_table` for the derivation chain."""
    k = cc["k"]
    class_of = cc["class_of"]
    reps = cc["representatives"]
    sizes = cc["class_sizes"]
    inverse_class = cc["inverse_class"]

    # The split prime: p ≡ 1 (mod e) so GF(p)* contains e-th roots of
    # unity, and p² > 4|G| — the exact-integer spelling of p > 2√|G|
    # (never a square root, never a float) — so a degree is unique in
    # (0, p/2).  p cannot divide |G|: p = e·m + 1 with p | |G| would force
    # an element of order p (Cauchy), hence p | e, contradicting p ≡ 1.
    m = 1
    while True:
        p = expo * m + 1
        if p * p > 4 * n and is_prime(p):
            break
        m += 1

    cls_e = class_of[e_idx]
    subspaces: List[List[List[int]]] = [
        [[1 if c == r else 0 for c in range(k)] for r in range(k)]]
    for i in range(k):
        if i == cls_e:
            continue                    # M_identity = I splits nothing
        refined: List[List[List[int]]] = []
        for basis in subspaces:
            r = len(basis)
            if r == 1:
                refined.append(basis)
                continue
            images = []
            for vec in basis:
                img = [0] * k
                for j in range(k):
                    acc = 0
                    row = class_algebra[i][j]
                    for l in range(k):
                        if row[l] and vec[l]:
                            acc += row[l] * vec[l]
                    img[j] = acc % p
                images.append(img)
            # coordinates of each image in the subspace basis
            a_mat = [[basis[s][j] for s in range(r)] for j in range(k)]
            coeff = [[0] * r for _ in range(r)]
            for t, img in enumerate(images):
                sol = gf_solve(a_mat, img, p)
                if not sol["consistent"]:
                    raise ValueError(
                        "character_table: a class matrix left its invariant "
                        "subspace — internal inconsistency (a guard that "
                        "fires is evidence)")
                part = sol["particular"]
                for s in range(r):
                    coeff[s][t] = part[s]
            found_dim = 0
            for lam in range(p):
                shifted = [[(coeff[a][b] - (lam if a == b else 0)) % p
                            for b in range(r)] for a in range(r)]
                kernel = gf_nullspace(shifted, p)
                if not kernel:
                    continue
                found_dim += len(kernel)
                new_basis = []
                for w in kernel:
                    vec = [0] * k
                    for s in range(r):
                        if w[s]:
                            for j in range(k):
                                vec[j] = (vec[j] + w[s] * basis[s][j]) % p
                    new_basis.append(vec)
                refined.append(new_basis)
            if found_dim != r:
                raise ValueError(
                    "character_table: eigenspace dimensions do not sum to "
                    "the subspace dimension over GF(p) — internal "
                    "inconsistency (a guard that fires is evidence)")
        subspaces = refined
    for basis in subspaces:
        if len(basis) != 1:
            raise ValueError(
                "character_table: the class matrices did not separate the "
                "central characters — internal inconsistency (a guard that "
                "fires is evidence)")

    # ω → d → χ mod p per common eigenvector
    chars_modp: List[Tuple[int, List[int]]] = []
    for basis in subspaces:
        vec = basis[0]
        ve = vec[cls_e]
        if ve == 0:
            raise ValueError(
                "character_table: a central character vanishes on the "
                "identity class — internal inconsistency (a guard that "
                "fires is evidence)")
        scale = mod_inv(ve, p)
        omega = [(vec[j] * scale) % p for j in range(k)]
        ssum = 0
        for j in range(k):
            ssum = (ssum + omega[j] * omega[inverse_class[j]]
                    * mod_inv(sizes[j] % p, p)) % p
        d_squared = (n % p) * mod_inv(ssum, p) % p
        d = 0
        cand = 1
        while cand * cand <= n:
            if (cand * cand - d_squared) % p == 0:
                d = cand
                break
            cand += 1
        if d == 0:
            raise ValueError(
                "character_table: no degree d with d*d <= |G| matches the "
                "orthogonality sum mod p - internal inconsistency (a guard "
                "that fires is evidence)")
        chi = [omega[j] * d % p * mod_inv(sizes[j] % p, p) % p
               for j in range(k)]
        chars_modp.append((d, chi))

    # a generator of GF(p)*, certified against every prime factor of p−1
    pm1 = p - 1
    pm1_primes = [q for q, _ in factor(pm1)]
    w = 2
    while True:
        if all(mod_pow(w, pm1 // q, p) != 1 for q in pm1_primes):
            break
        w += 1

    rows: List[Tuple[int, List[Tuple[int, ...]]]] = []
    for d, chi in chars_modp:
        values: List[Tuple[int, ...]] = []
        for j in range(k):
            g = reps[j]
            g_ord = orders[g]
            z = mod_pow(w, pm1 // g_ord, p)
            chi_pows = []
            x = e_idx
            for _t in range(g_ord):
                chi_pows.append(chi[class_of[x]])
                x = tbl[x][g]
            ord_inv = mod_inv(g_ord % p, p)
            vec = [0] * expo
            for jj in range(g_ord):
                acc = 0
                for t in range(g_ord):
                    back = (g_ord - (jj * t) % g_ord) % g_ord
                    acc = (acc + chi_pows[t] * mod_pow(z, back, p)) % p
                mult = _small_lift(acc * ord_inv % p, p)
                if mult < 0 or mult > d:
                    raise ValueError(
                        "character_table: a lifted root-of-unity "
                        "multiplicity fell outside [0, d] — internal "
                        "inconsistency (a guard that fires is evidence)")
                if mult:
                    vec[(expo // g_ord) * jj] += mult
            values.append(_reduce_mod_phi(vec, phi))
        rows.append((d, values))
    return rows


def character_table(cayley_table: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """The EXACT complex character table of a finite group, values in the
    cyclotomic ring ``ℤ[ζ_e]`` — Class L, the spectral decomposition of the
    class algebra, with every value an exact integer vector.

    **The carrier.** ``e`` is the group exponent (lcm of element orders).
    Every table value is an integer coordinate vector of length ``φ(e)`` in
    the ``ζ_e`` power basis ``{1, ζ, …, ζ^{φ(e)−1}}``, reduced mod ``Φ_e``
    — character values are algebraic INTEGERS, so no rational ever appears
    in the table.  ALL values are vectors, including the rational ones
    (``χ(1) = d`` ships as ``(d, 0, …, 0)``); scalars and vectors are never
    mixed.  A caller wanting division lifts into
    :class:`srmech.math.qalg.Qalg` over the shipped modulus::

        from srmech.math.qalg import Qalg
        ct = character_table(table)
        value = Qalg(list(ct["phi_e"]), ct["table"][i][j])

    Conjugation needs NO machinery: ``χ̄(g) = χ(g⁻¹)``, and the payload
    ships ``inverse_class`` — conjugation is a column permutation.

    **Row and column order, pinned.** Rows sort by ``(degree,
    lexicographic value-vector tuple)``; columns are the
    :func:`conjugacy_classes` order VERBATIM (one SSoT — the same census
    partition every sibling op reads).

    **The algorithm** — the classical prime-field split-and-lift (commonly
    attributed to J. D. Dixon, 'High speed computation of group
    characters', *Numer. Math.* 10 (1967) 446–450, DOI 10.1007/BF02162877
    (Crossref); that venue is paywalled, so per the paywalled-DOI
    discipline NO attestation is claimed for it and the derivation is
    carried inline instead — every step below is checkable from first
    principles):

    1. one :func:`conjugacy_classes` call (the class-data SSoT);
    2. the exponent ``e`` (element orders off the table, lcm via the
       c_dispatched :func:`srmech.math.cyclic.gcd`);
    3. ``Φ_e`` via :func:`srmech.math.poly.cyclotomic_polynomial`;
    4. class-algebra structure constants ``a_{ijl} = #{(x, y) ∈ C_i × C_j :
       xy = z_l}`` by integer counting off the table;
    5. ABELIAN FAST PATH (``k == |G|``): the table is its own dual — the
       characters are built directly as ``ζ_e``-power products by
       iterative subgroup extension, pure Class I, no prime field;
    6. otherwise the split prime ``p = e·m + 1`` with ``p² > 4|G|`` (the
       exact-integer spelling of ``p > 2√|G|`` — never a square root,
       never a float);
    7. common eigenvectors of the commuting class matrices over GF(p) by
       λ-scan with :func:`srmech.math.modular_linalg.gf_nullspace` /
       :func:`~srmech.math.modular_linalg.gf_solve` (the c_dispatched
       ``gf_rref`` underneath).  Cost is honest: O(p·k⁴) worst case — the
       op targets small-order groups; a large exponent makes it SLOW,
       never wrong;
    8. central characters ``ω_i = |C_i|·χ(g_i)/d mod p``, the degree ``d``
       recovered from ``Σ_i ω_i ω_{ī} / |C_i| ≡ |G|/d² (mod p)`` — unique
       in ``(0, p/2)`` because ``p > 2√|G| ≥ 2d``;
    9. the lift: for a class rep of order ``m``, the multiplicity of each
       ``m``-th root of unity in ``χ(g)`` is ``n_j = (1/m) Σ_t χ(g^t)
       z^{−jt} mod p`` (``z`` an order-``m`` element of GF(p)*, from a
       certified generator), each lifted through :func:`_small_lift` (the
       named Class-K/Class-C sign site) and bounds-checked ``0 ≤ n_j ≤ d``
       — an out-of-bounds lift raises, a guard that fires is evidence;
       then ``χ(g) = Σ_j n_j ζ_e^{(e/m)j}`` reduced mod ``Φ_e``.

    In-op self-checks before returning: ``Σ d² = |G|`` and every ``d``
    divides ``|G|``.  (The degree-1-count = abelianization-order identity
    is deliberately a TEST, not an in-op check — it crosses ops.)

    Args:
        cayley_table: the ``n × n`` group table (``ValueError`` otherwise).

    Returns:
        ``{"order", "exponent", "zeta_order" (= exponent), "phi_e" (monic
        ``Φ_e`` coefficients low→high), "degree" (= φ(e), the vector
        length), "k", "class_sizes", "representatives", "class_of",
        "inverse_class", "square_class" (verbatim from ONE
        conjugacy_classes call), "degrees" (ascending), "table" (k × k of
        int tuples), "class_algebra" (the k × k × k structure constants),
        "table_sha256", "cayley_sha256"}`` — every field is load-bearing
        for tier 3
        (fusion multiplicities read ``inverse_class`` / ``phi_e``; the
        Frobenius–Schur indicator reads ``square_class``;
        ``class_algebra`` no tier-3 op computes from — the shared payload
        validator requires it present, and it is the operand of the
        test-side idempotent oracle.  This line said fusion "read
        ``class_algebra``" until the rc457 repair pass measured the
        fusion body against it: 0 reads).

    **``cayley_sha256`` is the GROUP BIND (rc460).**  ``table_sha256``
    addresses the CHARACTER MATRIX body and is not a group identity by
    construction; ``cayley_sha256`` is the Class-A content address of the
    OPERAND Cayley table, the same address
    :func:`permutation_representation` mints.  Its absence was a
    replicated SILENT WRONG ANSWER: the regular character is ``(|G|, 0,
    …, 0)`` for EVERY group, so a rep payload and a character table from
    two DIFFERENT groups of equal order passed every shipped law.
    Measured over 11 constructible groups, every ordered same-order pair
    of regular / coset reps: 60 pairs, 9 raised, **42 returned a
    different answer with no signal** (``decompose_representation(regular
    rep of C21, character_table of F21)`` returned ``(1, 1, 1, 3, 3)`` —
    C21 is ABELIAN, so a 3-dimensional constituent is impossible).  With
    this field present the tier-4 consumers bind, and all 42 are caught.

    Note:
        Exact integers end to end; no float; no ``abs``.
    """
    cc = conjugacy_classes(cayley_table)
    tbl = [list(r) for r in cayley_table]
    n = cc["order"]
    e_idx = cc["identity"]
    k = cc["k"]
    class_of = cc["class_of"]
    reps = cc["representatives"]
    inv = cc["inverses"]

    orders: List[int] = []
    for g in range(n):
        x = g
        m = 1
        while x != e_idx:
            x = tbl[x][g]
            m += 1
        orders.append(m)
    expo = 1
    for m in orders:
        expo = expo // gcd(expo, m) * m

    phi_entry = cyclotomic_polynomial(expo)
    phi = list(phi_entry["coefficients"])
    deg = phi_entry["degree"]

    class_algebra = [[[0] * k for _ in range(k)] for _ in range(k)]
    for l in range(k):
        z = reps[l]
        for x in range(n):
            y = tbl[inv[x]][z]
            class_algebra[class_of[x]][class_of[y]][l] += 1

    if k == n:
        zeta_pow = _zeta_power_table(phi, expo)
        rows = _abelian_rows(tbl, n, e_idx, expo, reps, zeta_pow)
    else:
        rows = _dixon_rows(tbl, n, e_idx, expo, orders, cc,
                           class_algebra, phi)

    rows.sort(key=lambda row: (row[0], tuple(row[1])))
    degrees = [row[0] for row in rows]
    if sum(d * d for d in degrees) != n:
        raise ValueError(
            "character_table: sum of squared degrees != |G| - internal "
            "inconsistency (a guard that fires is evidence)")
    for d in degrees:
        if n % d != 0:
            raise ValueError(
                f"character_table: degree {d} does not divide |G| = {n} - "
                "internal inconsistency (a guard that fires is evidence)")
    table = [list(row[1]) for row in rows]
    body = "\n".join(
        ";".join(",".join(str(c) for c in cell) for cell in row)
        for row in table).encode("utf-8")
    return {
        "order": n,
        "exponent": expo,
        "zeta_order": expo,
        "phi_e": tuple(phi),
        "degree": deg,
        "k": k,
        "class_sizes": cc["class_sizes"],
        "representatives": reps,
        "class_of": class_of,
        "inverse_class": cc["inverse_class"],
        "square_class": cc["square_class"],
        "degrees": degrees,
        "table": table,
        "class_algebra": class_algebra,
        "table_sha256": sha256_bytes(body),
        "cayley_sha256": sha256_bytes(_table_bytes(tbl)),
    }


def irrep_dimensions(cayley_table: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """The irreducible-representation dimension multiset of a finite group
    — the Class-L readout of :func:`character_table`, and the direct
    instrument for the rc456 founding question ("does this order-21 table
    carry an irrep of dimension 3, or only lines?").

    One delegation, one SSoT: ``degrees`` here IS
    ``character_table(table)["degrees"]`` — never re-derived, so the two
    ops cannot disagree.

    Args:
        cayley_table: the ``n × n`` group table (``ValueError`` otherwise).

    Returns:
        ``{"degrees"`` (ascending), ``"k"`` (= #classes = #irreps),
        ``"order", "num_linear"`` (count of degree-1 rows — the
        abelianization order), ``"sum_of_squares"`` (returned, and equal to
        ``order`` by the table's own guard)``}``.

    The founding measurement, restated as data: C7×C3 (direct) →
    ``degrees == [1]*21``; C7⋊C3 (semidirect, mult-by-2 action) →
    ``[1, 1, 1, 3, 3]``.  Same order, same two cycles — the coupling, not
    the size, decides whether dimension > 1 is pronounceable.

    Note:
        Exact integers; no ``abs``.
    """
    ct = character_table(cayley_table)
    degrees = ct["degrees"]
    return {
        "degrees": degrees,
        "k": ct["k"],
        "order": ct["order"],
        "num_linear": degrees.count(1),
        "sum_of_squares": sum(d * d for d in degrees),
    }


# ──────────────────────────────────────────────────────────────────────
# tier 3 — readouts over the character-table payload (rc457).  Each op
# consumes the :func:`character_table` payload dict VERBATIM (that is
# what "rc456 shaped its payloads so tier 3 composes" means
# operationally): no re-run of the split-and-lift, no second class
# census, and each body's only registered-op call is the Class-A
# content address.
# ──────────────────────────────────────────────────────────────────────


#: The payload keys every tier-3 op requires — the exact field list
#: :func:`character_table` returns (``zeta_order`` is a documented alias
#: of ``exponent`` and is deliberately not required).  ``cayley_sha256``
#: joined the list at rc460: it is the GROUP BIND the tier-4 consumers
#: compare against a rep payload's own address, and a key that is
#: optional cannot be a bind.
_CHAR_TABLE_KEYS = (
    "table", "degrees", "class_sizes", "class_of", "inverse_class",
    "square_class", "class_algebra", "phi_e", "degree", "k", "order",
    "exponent", "representatives", "table_sha256", "cayley_sha256",
)


def _plain_int(value: Any) -> bool:
    """True for a plain ``int`` — a ``bool`` is REJECTED (True == 1 would
    otherwise ride every integer lane silently)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _check_char_table_payload(op: str, ct: Mapping[str, Any]) -> None:
    """Validate a :func:`character_table` payload ONCE, raising
    ``ValueError`` NAMING the failing law (the :func:`semidirect_product`
    convention).  Shared by every tier-3 op so a malformed or hand-edited
    payload is refused identically everywhere."""
    missing = [key for key in _CHAR_TABLE_KEYS if key not in ct]
    if missing:
        raise ValueError(
            f"{op}: char_table payload is missing {missing} - pass the "
            f"character_table(cayley_table) dict verbatim (payload-key law)")
    for label in ("k", "order", "exponent", "degree"):
        if not _plain_int(ct[label]) or ct[label] < 1:
            raise ValueError(
                f"{op}: {label} must be a positive plain int, not "
                f"{ct[label]!r} (payload-scalar law)")
    k = ct["k"]
    deg = ct["degree"]
    if deg != len(ct["phi_e"]) - 1:
        raise ValueError(
            f"{op}: degree {deg} != len(phi_e) - 1 = "
            f"{len(ct['phi_e']) - 1} (carrier-width law)")
    for i, coefficient in enumerate(ct["phi_e"]):
        if not _plain_int(coefficient):
            raise ValueError(
                f"{op}: phi_e[{i}] carries a "
                f"{type(coefficient).__name__} coefficient; the modulus "
                f"is plain-int coefficients only (plain-int law)")
    for label in ("table", "degrees", "class_sizes", "inverse_class",
                  "square_class", "representatives", "class_algebra"):
        if len(ct[label]) != k:
            raise ValueError(
                f"{op}: len({label}) = {len(ct[label])} != k = {k} "
                f"(class-count law)")
    for i, row in enumerate(ct["table"]):
        if len(row) != k:
            raise ValueError(
                f"{op}: table row {i} has {len(row)} cells, expected {k} "
                f"(class-count law)")
        for j, cell in enumerate(row):
            if len(cell) != deg:
                raise ValueError(
                    f"{op}: table[{i}][{j}] has length {len(cell)}, "
                    f"expected phi(e) = {deg} (carrier-width law)")
            for coordinate in cell:
                if not _plain_int(coordinate):
                    raise ValueError(
                        f"{op}: table[{i}][{j}] carries a "
                        f"{type(coordinate).__name__} coordinate; the "
                        f"carrier is plain-int vectors only "
                        f"(plain-int law)")
    for label in ("degrees", "class_sizes"):
        for i, value in enumerate(ct[label]):
            if not _plain_int(value) or value < 1:
                raise ValueError(
                    f"{op}: {label}[{i}] = {value!r} is not a positive "
                    f"plain int (payload-scalar law)")
    if sum(ct["class_sizes"]) != ct["order"]:
        raise ValueError(
            f"{op}: class_sizes sum to {sum(ct['class_sizes'])} != order "
            f"= {ct['order']} (class-equation law)")
    degree_square_sum = sum(d * d for d in ct["degrees"])
    if degree_square_sum != ct["order"]:
        raise ValueError(
            f"{op}: sum of squared degrees = {degree_square_sum} != "
            f"order = {ct['order']} - the degrees do not cohere with the "
            f"group order (degree-square law)")
    for label in ("inverse_class", "square_class"):
        for i, value in enumerate(ct[label]):
            if not _plain_int(value) or not 0 <= value < k:
                raise ValueError(
                    f"{op}: {label}[{i}] = {value!r} is not a class index "
                    f"in [0, {k}) (class-index law)")
    if len(ct["class_of"]) != ct["order"]:
        raise ValueError(
            f"{op}: len(class_of) = {len(ct['class_of'])} != order = "
            f"{ct['order']} (element-count law)")
    for g, value in enumerate(ct["class_of"]):
        if not _plain_int(value) or not 0 <= value < k:
            raise ValueError(
                f"{op}: class_of[{g}] = {value!r} is not a class index "
                f"in [0, {k}) (class-index law)")
    for label in ("table_sha256", "cayley_sha256"):
        value = ct[label]
        if (not isinstance(value, str) or len(value) != 64
                or not set(value) <= _SHA256_HEX):
            raise ValueError(
                f"{op}: {label} = {value!r} is not a 64-hex content "
                f"address (content-address-shape law)")


def _same_group_bind(op: str, rep: Mapping[str, Any],
                     ct: Mapping[str, Any]) -> None:
    """The GROUP BIND between a tier-4 rep payload and a tier-2 character
    table (rc460): both carry the Class-A ``cayley_sha256`` of the SAME
    operand Cayley table, so equality of the content address is the
    executable form of "these two objects describe one group".

    **Why a bind rather than a detector.**  Through rc459 the only
    cross-object check was the class-constancy law inside
    :func:`character_of`, and its docstring called that "a DETECTOR, not
    a proof" while saying a mismatch "usually" breaks it.  Measured over
    a 60-pair census: it fires on **15%**.  "Usually" was false in the
    other direction — it usually does NOT fire, and 42 of the 60 pairs
    returned a DIFFERENT answer with no raise and no warning.  The
    payloads already carried both addresses side by side; nothing
    compared them.  This does.

    The strictness is correctness, not conservatism: a relabelled but
    isomorphic table has different class indexing, so decomposing a rep
    against it IS mathematically wrong.  ``table_sha256`` cannot serve —
    it addresses the character-matrix body, which is not a group
    identity by construction (D4 and Q8 share a character matrix)."""
    if rep["cayley_sha256"] != ct["cayley_sha256"]:
        raise ValueError(
            f"{op}: the rep payload and the char_table carry different "
            f"cayley_sha256 content addresses - a representation is "
            f"decomposed only against the character table of ITS OWN "
            f"group with the SAME element indexing (group-bind law; a "
            f"guard that fires is evidence)")


def _identity_class(op: str, ct: Mapping[str, Any]) -> int:
    """The identity class of a :func:`character_table` payload, located
    PAYLOAD-ONLY: the UNIQUE column where every row equals its degree
    vector ``(d_i, 0, …, 0)`` — unique because only the identity acts
    trivially in every irrep.  Hoisted at rc458 from the
    :func:`central_idempotents` body (tier-4 ``character_of`` needs the
    same location and a second copy would drift).  Raises ``ValueError``
    naming the identity-location law when the payload does not carry
    exactly one such column — a guard that fires is evidence."""
    k = ct["k"]
    deg = ct["degree"]
    table = ct["table"]
    degrees = ct["degrees"]
    identity_columns = [
        j for j in range(k)
        if all(tuple(table[i][j]) == (degrees[i],) + (0,) * (deg - 1)
               for i in range(k))]
    if len(identity_columns) != 1:
        raise ValueError(
            f"{op}: expected exactly ONE identity-class "
            f"column (every row equal to its degree vector); found "
            f"{len(identity_columns)} (identity-location law; a guard "
            f"that fires is evidence)")
    return identity_columns[0]


def _exact_div(op: str, numerator: int, denominator: int, what: str) -> int:
    """Exact integer division via ``divmod`` with a remainder-must-be-zero
    guard — THE corruption detector of the tier-3 ops: every character-sum
    these ops take is |G|-divisible on a true character table, so a nonzero
    remainder means the payload does not cohere as one.  Raises; never
    rounds."""
    quotient, remainder = divmod(numerator, denominator)
    if remainder != 0:
        raise ValueError(
            f"{op}: {what} = {numerator} is not divisible by "
            f"{denominator} - the payload does not cohere as a character "
            f"table (divisibility law; a guard that fires is evidence)")
    return quotient


def frobenius_schur_indicator(
        char_table: Mapping[str, Any]) -> Dict[str, Any]:
    """The Frobenius–Schur indicator of every irreducible character —
    **Class K**, the three-point pin at the reality phase boundary.

    ``nu_i = (1/|G|) * sum_g chi_i(g^2)``, computed off the payload as the
    class-weighted sum over the shipped ``square_class`` column gather —
    pure integer vector arithmetic, NO cyclotomic multiplication.  The
    result is EXACTLY ``+1`` (real / orthogonal: the invariant bilinear
    form is symmetric — the ℝ rung), ``0`` (complex: no invariant form;
    the character and its conjugate are a chirality PAIR, the Class-C
    datum), or ``-1`` (quaternionic / symplectic: the form is
    antisymmetric — the ℍ rung).

    **The Class-K argument, stated rather than assumed.**  The op's entire
    pronouncement is a position at a phase boundary: which Hurwitz rung
    ``End_G(V)`` occupies.  Honest counter: the computing cascade is a
    class-weighted sum over the Class-I squaring map, and
    ``signed_laplacian`` resolved a similar tension toward L — but unlike
    that op, the indicator has NO other payload; the three-state sign
    classification IS the whole answer, so the readout class is the op's
    class.  Composition: Class I (x → x² via the ``square_class`` gather)
    → Class I (class-weighted integer sum) → **Class K three-point pin
    readout**, the 0 branch carrying the Class-C chirality read.  The pin
    is implemented as exact set membership in {-1, 0, +1} — never a
    sign or magnitude call.  Module precedent: :func:`_small_lift` is the
    named K pin-slot; :func:`semidirect_product` is K-as-coupling.

    ⚠️ **Row order**: payload rows sort by (degree, lexicographic value
    tuple) — the trivial character is NOT at index 0 in general (measured:
    C7⋊C3 carries it at index 2; S4 carries the sign character at row 0).
    Locate rows by CONTENT, never by index.

    Args:
        char_table: a :func:`character_table` payload dict, passed
            VERBATIM (``ValueError`` naming the failing law otherwise).

    Returns:
        ``{"k", "order", "indicators"`` (tuple of len k, payload row
        order, each exactly -1 / 0 / +1), ``"num_real", "num_complex",
        "num_quaternionic", "square_roots_of_identity"`` (= Σ nu_i·d_i,
        the Frobenius–Schur count of solutions of g² = e — an identity the
        tests read character-free off the Cayley table),
        ``"table_sha256"`` (echoed), ``"indicators_sha256"}``.

    In-op guards, each a raise: every weighted sum lands exactly
    ``(s, 0, …, 0)`` (rationality); ``order | s`` (divisibility — the
    corruption detector); ``s // order`` in {-1, 0, +1} (the three-point
    pin).  Corruption of a table cell OUTSIDE the square-class image is
    mathematically invisible to nu — the counting identity above is the
    paired detector for that.

    Note:
        Exact integers end to end; no ALU magnitude call anywhere.
    """
    _check_char_table_payload("frobenius_schur_indicator", char_table)
    k = char_table["k"]
    order = char_table["order"]
    deg = char_table["degree"]
    sizes = char_table["class_sizes"]
    square = char_table["square_class"]
    table = char_table["table"]
    degrees = char_table["degrees"]

    indicators: List[int] = []
    for i in range(k):
        acc = [0] * deg
        for j in range(k):
            cell = table[i][square[j]]
            weight = sizes[j]
            for t in range(deg):
                acc[t] += weight * cell[t]
        if any(acc[1:]):
            raise ValueError(
                f"frobenius_schur_indicator: the weighted square-class sum "
                f"of row {i} keeps nonzero zeta coordinates {tuple(acc)} - "
                f"a Frobenius-Schur sum is rational (rationality law; a "
                f"guard that fires is evidence)")
        nu = _exact_div("frobenius_schur_indicator", acc[0], order,
                        f"the weighted square-class sum of row {i}")
        if nu not in (-1, 0, 1):
            raise ValueError(
                f"frobenius_schur_indicator: row {i} pinned to {nu}, "
                f"outside the three-point pin -1 / 0 / +1 (Class-K pin "
                f"law; a guard that fires is evidence)")
        indicators.append(nu)

    square_roots = 0
    for nu, d in zip(indicators, degrees):
        square_roots += nu * d
    body = ",".join(str(v) for v in indicators).encode("utf-8")
    return {
        "k": k,
        "order": order,
        "indicators": tuple(indicators),
        "num_real": indicators.count(1),
        "num_complex": indicators.count(0),
        "num_quaternionic": indicators.count(-1),
        "square_roots_of_identity": square_roots,
        "table_sha256": char_table["table_sha256"],
        "indicators_sha256": sha256_bytes(body),
    }


def fusion_multiplicities(char_table: Mapping[str, Any]) -> Dict[str, Any]:
    """The full fusion tensor ``N_abc = <chi_a · chi_b, chi_c>`` — exact
    non-negative integers, **Class L**: projection of each pointwise
    character product onto the irrep eigenbasis of the class algebra, the
    same stratum slot :func:`character_table` (the spectral decomposition)
    and :func:`irrep_dimensions` (its readout) occupy.

    Internal stages, named: Class I — the exact ``ℤ[ζ_e]`` pointwise
    product ``chi_a(g)·chi_b(g)`` via the module's private ring multiply;
    Class C — conjugation of ``chi_c`` as the shipped ``inverse_class``
    column permutation (``chi̅(g) = chi(g⁻¹)``; no Galois machinery);
    Class I — the class-weighted integer sum.  The pointwise product is
    deliberately NOT claimed as a Class-M bind: an M-bind claim implies an
    unbind (character division), which is neither shipped nor measured.

    ⚠️ **Row order**: payload rows sort by (degree, lexicographic value
    tuple) — the trivial character is NOT at index 0 in general.  Locate
    rows by CONTENT (degree + value vector), never by index.

    Args:
        char_table: a :func:`character_table` payload dict, passed
            VERBATIM (``ValueError`` naming the failing law otherwise).

    Returns:
        ``{"k", "order", "degrees"`` (echoed), ``"multiplicities"`` —
        k × k × k nested int tuples, a-major, then b, then c —
        ``"table_sha256"`` (echoed), ``"multiplicities_sha256"}``.

    In-op guards, each a raise: every entry lands exactly
    ``(N·order, 0, …, 0)`` (integrality), is ``order``-divisible (the
    corruption detector) and non-negative; plus the dimension law
    ``Σ_c N_abc·d_c = d_a·d_b`` for ALL pairs — an O(k³) check, free
    relative to the O(k⁴·φ(e)²) compute.  Cost honest: the op targets the
    same small-order groups :func:`character_table` does; a large exponent
    makes it SLOW, never wrong.

    Note:
        Exact integers end to end; no ALU magnitude call anywhere.
    """
    _check_char_table_payload("fusion_multiplicities", char_table)
    k = char_table["k"]
    order = char_table["order"]
    deg = char_table["degree"]
    phi = char_table["phi_e"]
    sizes = char_table["class_sizes"]
    invc = char_table["inverse_class"]
    table = char_table["table"]
    degrees = char_table["degrees"]

    rows_out: List[Tuple[Tuple[int, ...], ...]] = []
    for a in range(k):
        row_a = table[a]
        cols_out: List[Tuple[int, ...]] = []
        for b in range(k):
            row_b = table[b]
            pointwise = [_zeta_mul(row_a[j], row_b[j], phi)
                         for j in range(k)]
            cell_out: List[int] = []
            for c in range(k):
                row_c = table[c]
                acc = [0] * deg
                for j in range(k):
                    prod = _zeta_mul(pointwise[j], row_c[invc[j]], phi)
                    weight = sizes[j]
                    for t in range(deg):
                        acc[t] += weight * prod[t]
                if any(acc[1:]):
                    raise ValueError(
                        f"fusion_multiplicities: <chi_{a}*chi_{b}, chi_{c}> "
                        f"keeps nonzero zeta coordinates {tuple(acc)} - a "
                        f"fusion inner product is a rational integer "
                        f"(integrality law; a guard that fires is evidence)")
                n_abc = _exact_div(
                    "fusion_multiplicities", acc[0], order,
                    f"the <chi_{a}*chi_{b}, chi_{c}> numerator")
                if n_abc < 0:
                    raise ValueError(
                        f"fusion_multiplicities: <chi_{a}*chi_{b}, chi_{c}> "
                        f"= {n_abc} is negative - fusion multiplicities "
                        f"count irrep constituents (non-negativity law; a "
                        f"guard that fires is evidence)")
                cell_out.append(n_abc)
            cols_out.append(tuple(cell_out))
        rows_out.append(tuple(cols_out))
    multiplicities = tuple(rows_out)

    for a in range(k):
        for b in range(k):
            total = 0
            for c in range(k):
                total += multiplicities[a][b][c] * degrees[c]
            if total != degrees[a] * degrees[b]:
                raise ValueError(
                    f"fusion_multiplicities: sum_c N[{a}][{b}][c]*d_c = "
                    f"{total} != d_{a}*d_{b} = "
                    f"{degrees[a] * degrees[b]} (dimension law; a guard "
                    f"that fires is evidence)")

    body = "\n".join(
        ";".join(",".join(str(n) for n in cell) for cell in row)
        for row in multiplicities).encode("utf-8")
    return {
        "k": k,
        "order": order,
        "degrees": degrees,
        "multiplicities": multiplicities,
        "table_sha256": char_table["table_sha256"],
        "multiplicities_sha256": sha256_bytes(body),
    }


def central_idempotents(char_table: Mapping[str, Any]) -> Dict[str, Any]:
    """The primitive central idempotents of the group algebra, in the
    class-sum basis — **Class L**: the rank-1 spectral-projector family of
    the class algebra, :func:`character_table`'s decomposition made into
    an operand.

    **The scope ruling this op's name carries.**  Two objects wear the
    name "isotypic projector": (a) the primitive central idempotents
    ``e_chi = (d/|G|) · Σ_g chi(g⁻¹)·g`` of ``Z(ℂ[G])`` — these need ONLY
    characters, and everything they need ships; (b) the projector onto an
    isotypic SUBSPACE of a caller's module, which needs the actual
    representation matrices ``rho(g)``.  This op ships object (a) under
    the name of what it actually is.  The elements returned ARE the
    isotypic projectors of the REGULAR module.  *(This ruling said
    "srmech has NO representation object" when it shipped at rc457, and
    that was true then.  Since rc458 it is no longer true:
    :func:`permutation_representation` mints ``rho: G -> GL(V)`` as a rep
    payload, and :func:`isotypic_projector` IS the evaluation
    ``rho(e_chi) = (d/|G|) · Σ_g chi(g⁻¹)·rho(g)`` this paragraph used to
    assign to the caller.  The group-algebra element here stays universal;
    reach for :func:`isotypic_projector` when a module is in hand.)*

    **The denominator, and why it is explicit.**  The coefficients
    ``d·chi(g⁻¹)/|G|`` are NOT algebraic integers (the trivial idempotent
    alone has every coefficient ``1/|G|``), so this is the stratum's first
    genuinely rational object.  It ships as integer NUMERATOR vectors over
    one explicit common ``denominator = order`` — the deferred-division
    shape of ``exact_dft``'s inverse — never a decimal carrier, never a
    ``Qalg`` in the payload (the ``Qalg`` lift stays the caller's two-line
    move, exactly as :func:`character_table` documents it).

    Internals, named: Class C — conjugation as the ``inverse_class``
    column permutation; Class I — plain integer scaling by the degree.

    Args:
        char_table: a :func:`character_table` payload dict, passed
            VERBATIM (``ValueError`` naming the failing law otherwise).

    Returns:
        ``{"k", "order", "degrees"`` (echoed), ``"denominator"`` (= order),
        ``"numerators"`` — k × k × φ(e) int tuples, irrep-major,
        class-minor: ``numerators[i][j] = degrees[i] ·
        table[i][inverse_class[j]]``, the coefficient numerator of the
        class sum ``K_j`` in ``e_i`` — ``"class_of"`` (echoed: expands
        per-class coefficients to per-element ones), ``"phi_e"`` (echoed:
        the ring the vectors live in), ``"table_sha256"`` (echoed),
        ``"idempotents_sha256"}``.

    In-op guards, each a raise: the identity class is located
    payload-only as the UNIQUE column where every row equals its degree
    vector (unique because only the identity acts trivially in every
    irrep), then the column sums are checked — ``Σ_i numerators[i][j]``
    equals ``(order, 0, …, 0)`` at the identity class and the zero vector
    elsewhere (``Σ e_chi = δ_e``, column orthogonality against the
    identity column).  Per-idempotent ``e·e = e`` stays test-side (two
    independent routes there; a disagreement is a finding).

    Note:
        Exact integers over one explicit denominator; no decimal carrier
        anywhere.
    """
    _check_char_table_payload("central_idempotents", char_table)
    k = char_table["k"]
    order = char_table["order"]
    deg = char_table["degree"]
    invc = char_table["inverse_class"]
    table = char_table["table"]
    degrees = char_table["degrees"]

    numerators = tuple(
        tuple(tuple(degrees[i] * coordinate
                    for coordinate in table[i][invc[j]])
              for j in range(k))
        for i in range(k))

    identity_class = _identity_class("central_idempotents", char_table)

    for j in range(k):
        for t in range(deg):
            total = 0
            for i in range(k):
                total += numerators[i][j][t]
            want = order if (j == identity_class and t == 0) else 0
            if total != want:
                raise ValueError(
                    f"central_idempotents: column {j} coordinate {t} sums "
                    f"to {total}, expected {want} - the idempotents do not "
                    f"sum to the identity-class delta (column-orthogonality "
                    f"law; a guard that fires is evidence)")

    body = "\n".join(
        ";".join(",".join(str(c) for c in cell) for cell in row)
        for row in numerators).encode("utf-8")
    return {
        "k": k,
        "order": order,
        "degrees": degrees,
        "denominator": order,
        "numerators": numerators,
        "class_of": char_table["class_of"],
        "phi_e": char_table["phi_e"],
        "table_sha256": char_table["table_sha256"],
        "idempotents_sha256": sha256_bytes(body),
    }


# ──────────────────────────────────────────────────────────────────────
# tier 4 — the representation itself (rc458).  rho: G -> GL(V) as a REP
# PAYLOAD dict over an exact field, element-indexed by the SAME
# Cayley-table indexing the whole stratum uses — that indexing IS the
# composition contract.  The homomorphism law is checkable only at
# CONSTRUCTION (the payload carries the table's HASH, not the table);
# downstream, the corruption detectors are the coherence laws exactly
# as tier 3's _exact_div is the character-payload one.
# ──────────────────────────────────────────────────────────────────────


#: The payload keys every rep-eating tier-4 op requires.  ``action`` is
#: additionally required when ``kind == "permutation"`` (and is what the
#: matrix-action coherence law reads against); ``e`` / ``phi_e`` are
#: additionally required when ``kind == "cyclotomic"`` (rc462 — they name
#: the RING, and a ring a payload does not name is a ring nothing can
#: domain-separate).
_REP_KEYS = ("order", "degree", "field", "kind", "matrices",
             "cayley_sha256", "matrices_sha256")

#: The extra keys the ζ dialect requires on top of :data:`_REP_KEYS`.
_CYCLOTOMIC_REP_KEYS = ("e", "phi_e")

#: The ℚ(ζ_e) field spelling, parameterised by the conductor.  ONE
#: spelling per ring — the coupling law makes ``field`` and ``kind``
#: mutually determined, so a payload cannot say ``Q`` in one place and
#: ``cyclotomic`` in another.
_ZETA_FIELD_PREFIX = "Q(zeta_"


def _zeta_field(e: int) -> str:
    """The canonical ``field`` spelling of ``ℚ(ζ_e)``."""
    return f"{_ZETA_FIELD_PREFIX}{e})"


_SHA256_HEX = frozenset("0123456789abcdef")


def _pair_magnitude(value: int) -> int:
    """The magnitude read of a plain int — tier 4's Class-K pin-slot at
    the zero phase boundary with Class-C re-entry (the :func:`_small_lift`
    precedent): an explicit sign-branch, never an ALU magnitude call.  The
    canonical-pair law reads numerator magnitudes through this so the
    Class-I :func:`srmech.math.cyclic.gcd` (non-negative domain) sees only
    magnitudes while the orientation stays on the pair."""
    if value < 0:
        return -value          # Class K flip at 0, Class C re-entry
    return value


def _canonical_pair(num: int, den: int) -> Tuple[int, int]:
    """Reduce an integer pair to the CANONICAL ``(num, den)`` spelling:
    ``gcd == 1``, ``den >= 1``, sign on the numerator, zero as ``0/1``.
    Exact integers; the sign read is the :func:`_pair_magnitude` Class-K
    pin-slot."""
    if den < 0:
        num, den = -num, -den  # Class-K flip: the sign lives on num
    g = gcd(_pair_magnitude(num), den)
    if g > 1:
        num //= g
        den //= g
    if num == 0:
        den = 1                # the canonical zero is 0/1
    return (num, den)


def _rep_matrices_bytes(kind: str, matrices, e: Optional[int] = None) -> bytes:
    """Canonical bytes of a rep's matrix family for the Class-A content
    address: elements blank-line-joined, rows newline-joined, cells
    comma-joined; a general-kind cell is spelled ``num/den``; a
    cyclotomic-kind cell is its ``φ(e)`` coordinates ``;``-joined, each
    spelled ``num/den``, and the WHOLE body carries a ``zeta{e}\\n``
    prefix.  The validator's canonical-pair law is what makes two
    spellings of one rep ONE hash — canonicality is load-bearing, not
    cosmetic.

    **Why a THIRD branch and not a widened general branch** (rc462).  The
    ζ dialect had two acceptance requirements that read as contradictory:
    *no shipped ℚ digest may move*, and *no ℚ/ζ body may collide*.  Both
    horns are properties of designs that EDIT the general branch — a
    shape-detected unification leaves ``b'3/4'`` as the body of both a ℚ
    cell ``(3, 4)`` and a ``φ(e) == 1`` ζ cell ``((3, 4),)``, while every
    by-construction separator moves the ℚ bodies.  A third branch keyed on
    ``kind`` leaves BOTH existing branches untaken, so the ℚ bytes are
    unmoved *by construction*, and the ``zeta{e}`` prefix separates the
    domains unconditionally — including the cross-conductor case, where
    ``φ(3) == φ(4) == φ(6) == 2`` makes the bodies alone coincide.

    ``e`` is REQUIRED on the cyclotomic branch and is refused when absent
    rather than defaulted: a serialization that silently dropped its
    conductor would content-address two different rings to one digest.
    The ℚ branches never take it, which is why the four ℚ-only call sites
    do not thread it."""
    if kind == "permutation":
        return "\n\n".join(
            "\n".join(",".join(str(v) for v in row) for row in mat)
            for mat in matrices).encode("utf-8")
    if kind == "cyclotomic":
        if not _plain_int(e):
            raise ValueError(
                f"_rep_matrices_bytes: a cyclotomic serialization needs "
                f"its conductor e as a plain int, not {e!r} - the domain "
                f"prefix IS the ring separation (domain-separation law)")
        body = "\n\n".join(
            "\n".join(
                ",".join(
                    ";".join(f"{coordinate[0]}/{coordinate[1]}"
                             for coordinate in cell)
                    for cell in row)
                for row in mat)
            for mat in matrices)
        return f"zeta{e}\n{body}".encode("utf-8")
    return "\n\n".join(
        "\n".join(",".join(f"{cell[0]}/{cell[1]}" for cell in row)
                  for row in mat)
        for mat in matrices).encode("utf-8")


def _check_canonical_pair(op: str, where: str, cell: Any) -> None:
    """The CANONICAL-PAIR law, hoisted at rc462 so it has ONE spelling.
    A general-kind matrix ENTRY and a cyclotomic-kind entry's per-``ζ``
    COORDINATE are the same object — a 2-pair of plain ints, ``den >= 1``,
    ``gcd == 1``, zero as ``0/1`` — and a second copy of the law would
    drift.  ``where`` is the caller's index path, so the message names the
    failing cell exactly as it did before the hoist."""
    if not isinstance(cell, (tuple, list)) or len(cell) != 2:
        raise ValueError(
            f"{op}: {where} = {cell!r} is not a (num, den) pair "
            f"(canonical-pair law)")
    num, den = cell
    if not _plain_int(num) or not _plain_int(den):
        raise ValueError(
            f"{op}: {where} carries a non-plain-int coordinate "
            f"({type(num).__name__}, {type(den).__name__}) "
            f"(canonical-pair law)")
    if den < 1:
        raise ValueError(
            f"{op}: {where} = ({num}, {den}) has den < 1; the sign lives "
            f"on the numerator (canonical-pair law)")
    if gcd(_pair_magnitude(num), den) != 1 or (num == 0 and den != 1):
        raise ValueError(
            f"{op}: {where} = ({num}, {den}) is not reduced - a content-"
            f"addressed carrier needs ONE spelling per value "
            f"(canonical-pair law)")


def _check_rep_payload(op: str, rep: Mapping[str, Any]) -> None:
    """Validate a REP PAYLOAD dict ONCE, raising ``ValueError`` NAMING the
    failing law (the :func:`_check_char_table_payload` sibling; the
    :func:`semidirect_product` convention).  Shared by every rep-eating
    tier-4 op so a malformed or hand-edited payload is refused identically
    everywhere.

    **What this validator can and cannot check, stated plainly.**  The
    homomorphism law ``rho(g·h) == rho(g)·rho(h)`` is checkable only at
    CONSTRUCTION — the payload carries the Cayley table's HASH
    (``cayley_sha256``), not the table — exactly as a tier-3 op cannot
    re-verify that a character table is one.  Downstream the corruption
    detectors are the coherence laws: here the matrix-action coherence /
    one-1-per-row-and-column / canonical-pair / content-address laws; in
    the consumers the divisibility, non-scalar ζ-sum, dimension and trace
    laws (the :func:`_exact_div` shape — a guard that fires is evidence).

    Laws, in checking order: payload-key, payload-scalar, field, kind,
    coupling, ring (cyclotomic only), shape (element-count /
    rectangularity), then per kind — permutation: action shape, plain-int,
    bijection, matrix-entry (0/1 — which with the bijection law IS
    one-1-per-row-and-column), matrix-action coherence; general:
    canonical-pair (a 2-pair of plain ints, ``den >= 1``, ``gcd == 1`` —
    bool REJECTED on every integer lane); cyclotomic: ring-width (a cell
    is a length-``φ(e)`` tuple of coordinates) then the SAME canonical-pair
    law per coordinate — and LAST the content-address law
    (``matrices_sha256`` recomputed over the canonical serialization must
    match; ``cayley_sha256`` is shape-checked only, since the table is not
    in the payload).

    **The ζ dialect (rc462, `#T1179`).**  ``kind == "cyclotomic"`` admits a
    rep over ``ℚ(ζ_e)``: a cell is a length-``φ(e)`` tuple of canonical
    ``(num, den)`` plain-int pairs — coordinates in the ``ζ_e`` power
    basis, low→high, the SAME convention :func:`zeta_mul` and the tier-2
    character table already use — and the payload additionally carries
    ``e`` (the conductor) and ``phi_e`` (the monic ``Φ_e`` coefficients).
    Three laws couple the dialect so it cannot be half-declared:

    * **coupling law** — ``kind == "cyclotomic"`` iff ``field`` is a
      ``Q(zeta_N)`` spelling, BOTH directions.  A payload saying ``field:
      'Q'`` with ``kind: 'cyclotomic'`` (or the reverse) is refused;
    * **ring law** — ``e`` is a plain int ``>= 3`` (``ℚ(ζ₁) = ℚ(ζ₂) = ℚ``,
      which the general kind already spells, so a conductor of 1 or 2 is a
      ℚ payload wearing the ζ dialect), ``field == f"Q(zeta_{e})"``, and
      ``phi_e`` is a MONIC plain-int modulus of degree ``φ(e) >= 2``.  The
      IDENTITY of ``phi_e`` (that it really is ``Φ_e``) is checked at the
      producer — :func:`induced_representation` derives it from
      :func:`srmech.math.poly.cyclotomic_polynomial` — and at every
      consumer by the compatible-ring law, so this validator stays free of
      the branch-only compose edge (the :func:`_exact_trace` precedent);
    * **ring-width law** — every cell is exactly ``φ(e)`` coordinates."""
    missing = [key for key in _REP_KEYS if key not in rep]
    if missing:
        raise ValueError(
            f"{op}: rep payload is missing {missing} - pass a "
            f"permutation_representation(...) payload dict verbatim "
            f"(payload-key law)")
    for label in ("order", "degree"):
        if not _plain_int(rep[label]) or rep[label] < 1:
            raise ValueError(
                f"{op}: {label} must be a positive plain int, not "
                f"{rep[label]!r} (payload-scalar law)")
    field = rep["field"]
    zeta_field = (isinstance(field, str)
                  and field.startswith(_ZETA_FIELD_PREFIX)
                  and field.endswith(")")
                  and field[len(_ZETA_FIELD_PREFIX):-1].isdigit())
    if field != "Q" and not zeta_field:
        raise ValueError(
            f"{op}: field must be 'Q' or a 'Q(zeta_N)' spelling, not "
            f"{field!r} - tier 4 reps are exact-rational or exact "
            f"cyclotomic (field law)")
    kind = rep["kind"]
    if kind not in ("permutation", "general", "cyclotomic"):
        raise ValueError(
            f"{op}: kind must be 'permutation', 'general' or "
            f"'cyclotomic', not {kind!r} (kind law)")
    if (kind == "cyclotomic") != zeta_field:
        raise ValueError(
            f"{op}: kind {kind!r} and field {field!r} do not couple - the "
            f"cyclotomic kind carries a 'Q(zeta_N)' field and no other "
            f"kind may (coupling law)")
    zeta_width = 0
    if kind == "cyclotomic":
        missing_ring = [key for key in _CYCLOTOMIC_REP_KEYS if key not in rep]
        if missing_ring:
            raise ValueError(
                f"{op}: a cyclotomic payload is missing {missing_ring} - "
                f"the ζ dialect names its RING (payload-key law)")
        e = rep["e"]
        if not _plain_int(e) or e < 3:
            raise ValueError(
                f"{op}: e must be a plain int >= 3, not {e!r} - "
                f"Q(zeta_1) = Q(zeta_2) = Q, which the general kind "
                f"already spells (ring law)")
        if field != _zeta_field(e):
            raise ValueError(
                f"{op}: field {field!r} != {_zeta_field(e)!r} for e = {e} "
                f"- one spelling per ring (ring law)")
        phi_e = rep["phi_e"]
        for i, coefficient in enumerate(phi_e):
            if not _plain_int(coefficient):
                raise ValueError(
                    f"{op}: phi_e[{i}] carries a "
                    f"{type(coefficient).__name__} coefficient; the "
                    f"modulus is plain-int coefficients only "
                    f"(plain-int law)")
        zeta_width = len(phi_e) - 1
        if zeta_width < 2 or phi_e[-1] != 1:
            raise ValueError(
                f"{op}: phi_e must be a MONIC modulus of degree "
                f"phi(e) >= 2; got degree {zeta_width} with leading "
                f"coefficient {phi_e[-1] if phi_e else None!r} (ring law)")
    order = rep["order"]
    degree = rep["degree"]
    matrices = rep["matrices"]
    if len(matrices) != order:
        raise ValueError(
            f"{op}: len(matrices) = {len(matrices)} != order = {order} - "
            f"one matrix per element, Cayley-indexed (element-count law)")
    for g, mat in enumerate(matrices):
        if len(mat) != degree:
            raise ValueError(
                f"{op}: matrices[{g}] has {len(mat)} rows, expected "
                f"{degree} (shape law)")
        for r, row in enumerate(mat):
            if len(row) != degree:
                raise ValueError(
                    f"{op}: matrices[{g}][{r}] has {len(row)} cells, "
                    f"expected {degree} (shape law)")
    if kind == "permutation":
        if "action" not in rep:
            raise ValueError(
                f"{op}: a permutation-kind payload must carry its action "
                f"table (payload-key law)")
        action = rep["action"]
        if len(action) != order:
            raise ValueError(
                f"{op}: len(action) = {len(action)} != order = {order} "
                f"(element-count law)")
        for g, arow in enumerate(action):
            if len(arow) != degree:
                raise ValueError(
                    f"{op}: action[{g}] has {len(arow)} cells, expected "
                    f"{degree} (shape law)")
            for x, val in enumerate(arow):
                if not _plain_int(val):
                    raise ValueError(
                        f"{op}: action[{g}][{x}] carries a "
                        f"{type(val).__name__}; the action is plain-int "
                        f"points only (plain-int law)")
            if sorted(arow) != list(range(degree)):
                raise ValueError(
                    f"{op}: action[{g}] is not a bijection of "
                    f"range({degree}) (bijection law)")
        for g, mat in enumerate(matrices):
            arow = action[g]
            for r, row in enumerate(mat):
                for c, val in enumerate(row):
                    if not _plain_int(val) or val not in (0, 1):
                        raise ValueError(
                            f"{op}: matrices[{g}][{r}][{c}] = {val!r} is "
                            f"not a plain 0/1 int (matrix-entry law)")
                    want = 1 if arow[c] == r else 0
                    if val != want:
                        raise ValueError(
                            f"{op}: matrices[{g}][{r}][{c}] = {val} but "
                            f"action[{g}][{c}] = {arow[c]} - the pinned "
                            f"convention is matrices[g][action[g][j]][j] "
                            f"== 1 (matrix-action coherence law)")
    elif kind == "general":
        for g, mat in enumerate(matrices):
            for r, row in enumerate(mat):
                for c, cell in enumerate(row):
                    _check_canonical_pair(
                        op, f"matrices[{g}][{r}][{c}]", cell)
    else:
        for g, mat in enumerate(matrices):
            for r, row in enumerate(mat):
                for c, cell in enumerate(row):
                    if (not isinstance(cell, (tuple, list))
                            or len(cell) != zeta_width):
                        raise ValueError(
                            f"{op}: matrices[{g}][{r}][{c}] = {cell!r} is "
                            f"not a length-{zeta_width} tuple of zeta_"
                            f"{rep['e']} power-basis coordinates "
                            f"(ring-width law)")
                    for t, coordinate in enumerate(cell):
                        _check_canonical_pair(
                            op, f"matrices[{g}][{r}][{c}][{t}]", coordinate)
    for label in ("cayley_sha256", "matrices_sha256"):
        value = rep[label]
        if (not isinstance(value, str) or len(value) != 64
                or not set(value) <= _SHA256_HEX):
            raise ValueError(
                f"{op}: {label} = {value!r} is not a 64-hex content "
                f"address (content-address-shape law)")
    recomputed = sha256_bytes(
        _rep_matrices_bytes(kind, matrices, rep.get("e")))
    if recomputed != rep["matrices_sha256"]:
        raise ValueError(
            f"{op}: matrices_sha256 does not match the canonical "
            f"serialization of the matrices carried in the same payload - "
            f"the payload does not cohere (content-address law; a guard "
            f"that fires is evidence)")


def zeta_mul(u: Sequence[int], v: Sequence[int],
             phi_e: Sequence[int]) -> Tuple[int, ...]:
    """The exact ``ℤ[ζ_e]`` ring product of two ζ-power-basis integer
    vectors, reduced mod the monic ``Φ_e`` — **Class I**, the first
    registered exact ζ-vector atom, and the public promotion of the
    private kernel every tier-2/3/4 ζ contraction already rides
    (:func:`fusion_multiplicities`, :func:`decompose_representation`,
    :func:`isotypic_projector` all multiply in exactly this ring).

    rc456 promised this promotion, rc457 deliberately deferred it (its
    CHANGELOG records why), and this rc delivers it: integer convolution
    of ``u`` and ``v`` (any lengths), then exact monic polynomial
    reduction to length ``φ(e) = len(phi_e) - 1``.  No rational ever
    appears — ``Φ_e`` is monic and the operands are algebraic integers.

    Args:
        u: integer coordinates in the ``ζ_e`` power basis, low→high.
        v: same carrier as ``u``.
        phi_e: the monic ``Φ_e`` coefficients low→high — the ``phi_e``
            field of a :func:`character_table` payload, verbatim.

    Returns:
        The product as a length-``φ(e)`` tuple of plain ints.

    Guards, each a raise: every coordinate of all three vectors is a
    plain int — bool REJECTED (plain-int law); ``len(phi_e) >= 2`` and
    ``phi_e[-1] == 1`` (monic-modulus law).

    Worked example (``Φ_4 = x² + 1`` is ``(1, 0, 1)``)::

        zeta_mul((0, 1), (0, 1), (1, 0, 1))   # ζ₄ · ζ₄ = i·i
        # -> (-1, 0)                          # = -1, reduced mod Φ₄

    The caller wanting DIVISION lifts into
    :class:`srmech.math.qalg.Qalg` over ``m = Φ_e`` — the two-line move
    :func:`character_table` documents; this op stays in the ring.

    Internal hot paths keep calling the private kernel directly (guards
    cost per call and their operands are already validated payloads);
    this public spelling adds the wire-crossing guards.  It is also the
    one op legitimately ``[[cascade.chain]]``-declarable in a LATER rc —
    not this one (the ``cyclic_mod_pow.toml`` delegation precedent).

    C-parity (ADR-0009, recorded): no ``srmech_zeta_mul`` symbol exists.
    The near-peer ``srmech_riemann_theta_cyc_mul`` (srmech.h) is a
    ``ℤ[ζ]`` ring multiply speaking a DIFFERENT wire — ζ-power-table
    reduction, deg ≤ 16, int64 fast path — under a foreign namespace.
    The table-based wire adapter from ``phi_e`` (pure-bignum fallback)
    is deliberately deferred per the STAY-THE-COURSE-WITH-PYTHON ruling;
    recorded, not hidden.

    Note:
        Exact integers end to end; no float; no ``abs``.
    """
    for label, vec in (("u", u), ("v", v), ("phi_e", phi_e)):
        for i, coordinate in enumerate(vec):
            if not _plain_int(coordinate):
                raise ValueError(
                    f"zeta_mul: {label}[{i}] carries a "
                    f"{type(coordinate).__name__} coordinate; the carrier "
                    f"is plain-int vectors only (plain-int law)")
    phi = list(phi_e)
    if len(phi) < 2:
        raise ValueError(
            f"zeta_mul: phi_e must have degree >= 1 (len >= 2); got "
            f"len {len(phi)} (monic-modulus law)")
    if phi[-1] != 1:
        raise ValueError(
            f"zeta_mul: phi_e must be MONIC (leading coefficient 1); got "
            f"{phi[-1]} (monic-modulus law)")
    return _zeta_mul(list(u), list(v), phi)


def permutation_representation(
        cayley_table: Sequence[Sequence[int]],
        action: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """The permutation representation ``rho: G -> GL(V)`` of a group
    acting on a finite point set — **Class L** (mints the operator
    family, the :func:`cayley_graph` precedent) over Class-I action-law
    validation.  THE op that gives the stratum a representation OBJECT:
    everything before tier 4 stops at characters.

    Args:
        cayley_table: the ``n × n`` group table — validated as a group
            (associative, two-sided identity, unique two-sided inverses;
            ``ValueError`` naming the operand-group law otherwise).
        action: ``action[g]`` is a permutation TABLE of the point set
            ``range(degree)`` — a table, not a callable, because a
            callable cannot cross JSON-RPC and these operands ARE the
            semantics (the :func:`semidirect_product` convention).

    Validation, each failure a ``ValueError`` naming the law: one action
    row per element; every row a plain-int bijection of the point set;
    the identity acts as the identity permutation (identity-action law);
    and the LEFT-action law ``action[table[g][h]][x] ==
    action[g][action[h][x]]`` over ALL g, h, x — which for the pinned
    matrix convention IS the homomorphism law ``rho(g·h) = rho(g)·rho(h)``
    executed at construction (the one place it is checkable; the payload
    carries the table's hash, not the table).

    **The pinned matrix convention** (stated once, used by every tier-4
    op): ``matrices[g] · e_j = e_{action[g][j]}`` — column ``j`` carries
    its 1 in row ``action[g][j]``.  Vectorization everywhere is
    ROW-MAJOR.

    **The regular representation is** ``permutation_representation(tbl,
    tbl)`` — the left-multiplication action IS the Cayley table (the
    left-action law reduces to associativity); there is no separate op
    (the direct-product precedent: the special case is a call pattern,
    not a sibling).

    Returns:
        The REP PAYLOAD dict ``{"order", "degree", "field": "Q",
        "kind": "permutation", "matrices"`` (0/1 ints, Cayley-indexed),
        ``"action"`` (echoed, validated), ``"cayley_sha256"``
        (Class-A bind of the operand table), ``"matrices_sha256"``
        (Class-A bind of the canonical matrices serialization)``}`` —
        what :func:`character_of` / :func:`decompose_representation` /
        :func:`isotypic_projector` / :func:`tensor_product_representation`
        / :func:`direct_sum_representation` / :func:`intertwiner_space`
        all eat.

    C-parity (ADR-0009, recorded): this op has no C peer; the
    representation stratum ships Python-first under the noted-disparity
    ruling.

    Note:
        Exact integers; no float; no ``abs``.
    """
    tbl = _check_table("permutation_representation", cayley_table)
    n = len(tbl)
    e_idx = _identity_of(tbl)
    if e_idx is None:
        raise ValueError(
            "permutation_representation: cayley_table has no two-sided "
            "identity (operand-group law)")
    if _inverse_scan(tbl, e_idx) is None:
        raise ValueError(
            "permutation_representation: cayley_table lacks unique "
            "two-sided inverses (operand-group law)")
    _check_associative("permutation_representation", "cayley_table", tbl)

    act = [list(r) for r in action]
    if len(act) != n:
        raise ValueError(
            f"permutation_representation: action must have one "
            f"permutation row per element; got {len(act)} rows for "
            f"|G| = {n}")
    degree = len(act[0]) if act else 0
    if degree < 1:
        raise ValueError(
            "permutation_representation: the point set must be "
            "non-empty (shape law)")
    for g, row in enumerate(act):
        if len(row) != degree:
            raise ValueError(
                f"permutation_representation: action[{g}] has "
                f"{len(row)} cells, expected {degree} (shape law)")
        for x, val in enumerate(row):
            if not _plain_int(val):
                raise ValueError(
                    f"permutation_representation: action[{g}][{x}] "
                    f"carries a {type(val).__name__}; the action is "
                    f"plain-int points only (plain-int law)")
        if sorted(row) != list(range(degree)):
            raise ValueError(
                f"permutation_representation: action[{g}] is not a "
                f"bijection of range({degree}) (bijection law)")
    if act[e_idx] != list(range(degree)):
        raise ValueError(
            "permutation_representation: the identity must act as the "
            "identity permutation (identity-action law)")
    for g in range(n):
        for h in range(n):
            composed = tbl[g][h]
            for x in range(degree):
                if act[composed][x] != act[g][act[h][x]]:
                    raise ValueError(
                        f"permutation_representation: "
                        f"action[table[{g}][{h}]][{x}] != "
                        f"action[{g}][action[{h}][{x}]] "
                        f"(left-action law)")

    matrices: List[List[List[int]]] = []
    for g in range(n):
        mat = [[0] * degree for _ in range(degree)]
        for j in range(degree):
            mat[act[g][j]][j] = 1      # matrices[g]·e_j = e_{action[g][j]}
        matrices.append(mat)

    return {
        "order": n,
        "degree": degree,
        "field": "Q",
        "kind": "permutation",
        "matrices": matrices,
        "action": act,
        "cayley_sha256": sha256_bytes(_table_bytes(tbl)),
        "matrices_sha256": sha256_bytes(
            _rep_matrices_bytes("permutation", matrices)),
    }


def _exact_zeta_trace(op: str, g: int, mat, degree: int,
                      width: int) -> Tuple[int, ...]:
    """The exact ``ℤ[ζ_e]`` trace of one CYCLOTOMIC rep matrix (rc462):
    the diagonal summed COORDINATE-WISE over exact rationals, each
    coordinate then forced onto the integer lane by the same divmod-raise
    the ℚ branch uses.

    The integrality law generalises for a stated reason, not by analogy:
    ``ℤ[ζ_e]`` IS the ring of integers of ``ℚ(ζ_e)``, so an algebraic
    integer of that field has INTEGER power-basis coordinates.  The trace
    of a finite-group rep is a sum of roots of unity, hence an algebraic
    integer, hence integer-coordinate — and a nonzero remainder on ANY
    coordinate is corruption exactly as it is over ℚ.

    Kept as a SEPARATE function rather than a widening of
    :func:`_exact_trace`: merging them would put the ℚ path's
    divmod-raise behind a branch, and that raise is a live corruption
    detector on the shipped rational lane."""
    numerators = [0] * width
    denominators = [1] * width
    for i in range(degree):
        cell = mat[i][i]
        for t in range(width):
            num, den = cell[t]
            numerators[t] = numerators[t] * den + num * denominators[t]
            denominators[t] = denominators[t] * den
            shrink = gcd(_pair_magnitude(numerators[t]), denominators[t])
            if shrink > 1:
                numerators[t] //= shrink
                denominators[t] //= shrink
    out: List[int] = []
    for t in range(width):
        quotient, remainder = divmod(numerators[t], denominators[t])
        if remainder != 0:
            raise ValueError(
                f"{op}: trace of matrices[{g}] carries the non-integer "
                f"zeta coordinate {numerators[t]}/{denominators[t]} at "
                f"index {t} - the trace of a finite-group rep is a sum of "
                f"roots of unity, so it is an algebraic integer and "
                f"Z[zeta_e] is the ring of integers of Q(zeta_e) "
                f"(integrality law; a guard that fires is evidence)")
        out.append(quotient)
    return tuple(out)


def _exact_trace(op: str, g: int, kind: str, mat, degree: int) -> int:
    """The exact integer trace of one rep matrix: a diagonal 0/1 count
    for a permutation kind; an exact rational diagonal sum for a general
    kind, with the integrality law enforced by divmod-raise (the
    eigenvalues of a true finite-group rep are roots of unity, so its
    rational trace is an integer; a remainder is corruption).  Private so
    the Class-I ``gcd`` reduction stays a helper edge — it runs on the
    general-kind branch only, and a composes tuple cannot be true of both
    branches (the rc437 regular-representation precedent).

    The CYCLOTOMIC lane has its own :func:`_exact_zeta_trace` — see there
    for why it is not folded in."""
    if kind == "permutation":
        return sum(mat[i][i] for i in range(degree))
    t_num, t_den = 0, 1
    for i in range(degree):
        num, den = mat[i][i]
        t_num = t_num * den + num * t_den
        t_den = t_den * den
        shrink = gcd(_pair_magnitude(t_num), t_den)
        if shrink > 1:
            t_num //= shrink
            t_den //= shrink
    quotient, remainder = divmod(t_num, t_den)
    if remainder != 0:
        raise ValueError(
            f"{op}: trace of matrices[{g}] is "
            f"{t_num}/{t_den}, not an integer - the eigenvalues "
            f"of a true finite-group rep are roots of unity, so "
            f"its rational trace is an integer (integrality law; "
            f"a guard that fires is evidence)")
    return quotient


def character_of(rep: Mapping[str, Any],
                 char_table: Mapping[str, Any]) -> Dict[str, Any]:
    """The character of a representation — **Class L** (the trace
    readout), and the bridge from the tier-4 rep object back to the
    tier-2/3 character stratum; the free consistency oracle (on the
    regular representation the result must be ``(|G|, 0, …, 0)`` in
    class order, and per irreducible content it must match the shipped
    :func:`character_table` rows — the tests execute both).

    Args:
        rep: a tier-4 REP PAYLOAD dict, passed VERBATIM (``ValueError``
            naming the failing law otherwise).
        char_table: a :func:`character_table` payload dict, passed
            VERBATIM.  Only its CLASS-PARTITION fields are read
            (``class_of`` / ``k`` / ``order`` / ``degrees`` / ``table``
            for the identity location) — the character VALUES are not
            consulted; this op measures the rep, the payload supplies
            the partition.

    The trace of every element's matrix is computed exactly (an integer
    count of fixed points for a permutation kind; an exact rational
    diagonal sum for a general kind).  Guards, each a raise:

    * **order law** — ``rep["order"] == char_table["order"]``;
    * **integrality law** — each trace is a plain integer via a
      divmod-raise (the eigenvalues of ``rho(g)`` are roots of unity, so
      a rational trace of a true ℚ-rep is a rational algebraic integer,
      i.e. an integer; a remainder is corruption);
    * **group-bind law** — ``rep["cayley_sha256"] ==
      char_table["cayley_sha256"]``, the rc460 :func:`_same_group_bind`.
      This is the law that makes "same group" a PROOF rather than a
      hope, and :func:`decompose_representation` /
      :func:`isotypic_projector` inherit it by composing this op (the
      one place both operands are in hand, so a second copy could only
      drift);
    * **class-constancy law** — the trace is equal across each conjugacy
      class.  ⚠️ This line said, through rc459, that a rep and a char
      table from different groups of equal order "usually break
      class-constancy … it is a DETECTOR, not a proof".  **Measured over
      a 60-pair census: it fires on 15%.**  "Usually" was false in the
      other direction, and the remaining 42 pairs returned a different
      answer silently.  Class-constancy is a corruption detector for a
      payload that has ALREADY passed the group bind — it was never the
      same-group instrument, and the rc460 bind above is;
    * **identity-trace law** — ``character[identity_class] == degree``,
      the identity class located payload-only via the shared
      :func:`_identity_class` (the :func:`central_idempotents`
      unique-column technique, hoisted at this rc).

    **The ζ lane (rc462).**  A ``kind == "cyclotomic"`` rep's trace is a
    ``ℤ[ζ_e]`` VECTOR, not a scalar, so on that lane ``character`` is a
    length-k tuple of length-``φ(e)`` integer tuples — the SAME carrier
    :func:`character_table` already stores its own values in, which is
    why no new output type appears anywhere.  Two extra facts hold there:
    the **compatible-ring law** (``rep["phi_e"] == char_table["phi_e"]``
    — the group bind proves ONE GROUP and says nothing about the ring,
    and ``φ(3) == φ(4) == φ(6) == 2`` makes a width check no separation
    at all), and the integrality law reading per COORDINATE via
    :func:`_exact_zeta_trace`.  ``kind`` is echoed precisely so a consumer
    can tell the two lanes apart without re-deriving them.

    ⚠️ **The compatible-ring law is an EQUALITY, and that is a SCOPE
    BOUNDARY rather than a claim about the mathematics.**  A rep over a
    proper SUBFIELD of the table's ring is perfectly well-formed:
    ``F21 = C7⋊C3`` has exponent 21, so its character table lives over
    ``ℚ(ζ₂₁)`` while ``Ind_{C7}^{F21}`` of a faithful ``C7`` character
    lives over ``ℚ(ζ₇)``, and ``ζ₇ = ζ₂₁³`` embeds the one in the other.
    This rc REFUSES that pairing instead of performing the embedding —
    re-expanding ``ℤ[ζ₇]`` coordinates in the ``ζ₂₁`` power basis is new
    machinery, and a width-only check would happily multiply mod the WRONG
    modulus and answer silently (``φ(7) == 6 != 12 == φ(21)`` catches this
    ONE case, but ``φ(3) == φ(4) == φ(6)`` shows width is no separation in
    general).  So the readable stratum is exactly the reps whose conductor
    IS the group exponent; the refusal names its law and is MEASURED on
    F21 in ``tests/test_groups_zeta_dialect_rc462.py``, and lifting it is
    a later rc's work rather than an oversight.

    Returns:
        ``{"k", "order", "degree", "kind", "character"`` (length-k tuple,
        CLASS-ordered: plain ints on the ℚ lanes — the ``ℤ[ζ_e]`` lift of
        an integer ``t`` is ``(t, 0, …, 0)`` and is done by consumers
        internally — or length-``φ(e)`` integer tuples on the cyclotomic
        lane), ``"cayley_sha256"`` (echoed from the rep),
        ``"table_sha256"`` (echoed from the char table),
        ``"character_sha256"}``.

    C-parity (ADR-0009, recorded): this op has no C peer; the
    representation stratum ships Python-first under the noted-disparity
    ruling.

    Note:
        Exact integers; no float; no ``abs``.
    """
    _check_rep_payload("character_of", rep)
    _check_char_table_payload("character_of", char_table)
    if rep["order"] != char_table["order"]:
        raise ValueError(
            f"character_of: rep order {rep['order']} != char_table order "
            f"{char_table['order']} (order law)")
    # The escalation is deliberate: shape, then SIZE, then IDENTITY.  The
    # bind subsumes the order law mathematically (different orders imply
    # different tables imply different addresses), so putting it first
    # would make the order law unreachable with real operands and leave
    # the caller a coarser message for the coarser mistake.
    _same_group_bind("character_of", rep, char_table)
    order = rep["order"]
    degree = rep["degree"]
    kind = rep["kind"]
    matrices = rep["matrices"]
    k = char_table["k"]
    class_of = char_table["class_of"]

    width = 0
    if kind == "cyclotomic":
        # The COMPATIBLE-RING law (rc462).  The group bind proves the two
        # payloads describe one group; it says nothing about the ring.
        # A rep over Q(zeta_4) contracted against a table over Q(zeta_6)
        # would multiply length-2 vectors mod two DIFFERENT moduli and
        # answer silently — the phi_e vectors are the same LENGTH there,
        # since phi(3) == phi(4) == phi(6) == 2.
        if tuple(rep["phi_e"]) != tuple(char_table["phi_e"]):
            raise ValueError(
                f"character_of: the rep is over the modulus "
                f"{tuple(rep['phi_e'])} and the char_table over "
                f"{tuple(char_table['phi_e'])} - a cyclotomic rep is read "
                f"only against the character table of its OWN ring "
                f"(compatible-ring law; a guard that fires is evidence)")
        width = len(char_table["phi_e"]) - 1

    traces: List[Any] = []
    for g in range(order):
        if kind == "cyclotomic":
            traces.append(_exact_zeta_trace(
                "character_of", g, matrices[g], degree, width))
        else:
            traces.append(
                _exact_trace("character_of", g, kind, matrices[g], degree))

    character: List[Any] = [None] * k
    for g, trace in enumerate(traces):
        j = class_of[g]
        if character[j] is None:
            character[j] = trace
        elif character[j] != trace:
            raise ValueError(
                f"character_of: elements of class {j} carry unequal "
                f"traces {character[j]} and {trace} - a character is a "
                f"class function (class-constancy law; a guard that "
                f"fires is evidence.  The DIFFERENT-groups case is "
                f"caught upstream by the group-bind law, which this "
                f"law was wrongly documented as detecting)")
    empty = [j for j, v in enumerate(character) if v is None]
    if empty:
        raise ValueError(
            f"character_of: class_of names no element of class(es) "
            f"{empty} - every conjugacy class is non-empty "
            f"(class-coverage law; a guard that fires is evidence)")
    values = [v for v in character if v is not None]

    identity = _identity_class("character_of", char_table)
    want_identity: Any = degree
    if kind == "cyclotomic":
        want_identity = (degree,) + (0,) * (width - 1)
    if values[identity] != want_identity:
        raise ValueError(
            f"character_of: character at the identity class is "
            f"{values[identity]}, expected the degree {want_identity} "
            f"(identity-trace law; a guard that fires is evidence)")

    if kind == "cyclotomic":
        # Domain-separated exactly as _rep_matrices_bytes is: a ζ-vector
        # character and a rational one must not share a content address,
        # and str() on a tuple would emit Python repr with spaces.
        body = ("zeta{0}\n{1}".format(
            rep["e"],
            ";".join(",".join(str(c) for c in vec) for vec in values))
        ).encode("utf-8")
    else:
        body = ",".join(str(v) for v in values).encode("utf-8")
    return {
        "k": k,
        "order": order,
        "degree": degree,
        "kind": kind,
        "character": tuple(values),
        "cayley_sha256": rep["cayley_sha256"],
        "table_sha256": char_table["table_sha256"],
        "character_sha256": sha256_bytes(body),
    }


def decompose_representation(
        rep: Mapping[str, Any],
        char_table: Mapping[str, Any]) -> Dict[str, Any]:
    """The irrep multiplicities of a representation — **Class L**, the
    projection of the rep's character onto the irrep eigenbasis of the
    class algebra (the fusion slot: :func:`fusion_multiplicities` does
    this for a product of two CHARACTERS; this op does it for an actual
    REP).

    The body composes :func:`character_of` (a real composes-ledger row,
    not decoration), then contracts::

        m_i · |G| = Σ_j class_sizes[j] · character[j] ·
                    table[i][inverse_class[j]]

    — pure integer ζ-vector arithmetic (``χ_i(g⁻¹)`` is the shipped
    ``inverse_class`` column permutation, no Galois machinery; the
    integer character lifts as ``(t, 0, …, 0)`` internally).

    Guards, each a raise: the **non-scalar-sum law** (each summed
    ζ-vector must land exactly ``(M, 0, …, 0)`` — a nonzero higher
    coordinate is corruption); :func:`_exact_div` by ``|G|`` (the
    divisibility corruption detector); **non-negativity** (a
    multiplicity counts irrep constituents); and the **dimension law**
    ``Σ m_i·d_i == degree``.

    Args:
        rep: a tier-4 REP PAYLOAD dict, passed VERBATIM.
        char_table: a :func:`character_table` payload dict, passed
            VERBATIM (both validated inside :func:`character_of`, which
            is also where the rc460 :func:`_same_group_bind` fires — a
            rep and a char table from two DIFFERENT groups of equal
            order RAISE here, where through rc459 they returned a
            different answer silently).

    Returns:
        ``{"k", "order", "degree", "multiplicities"`` (length-k tuple of
        plain ints, payload row order), ``"norm"`` (= Σ m² = ⟨χ, χ⟩),
        ``"is_irreducible"`` (a bool as a BOOL FIELD — never riding an
        integer lane), ``"character"`` (echoed from
        :func:`character_of`), ``"degrees"`` (echoed), ``"table_sha256"``
        / ``"cayley_sha256"`` (echoed), ``"multiplicities_sha256"}``.

    ⚠️ Row order: payload rows sort (degree, lex) — the trivial
    character is NOT at index 0 in general; locate rows by CONTENT.

    C-parity (ADR-0009, recorded): this op has no C peer; the
    representation stratum ships Python-first under the noted-disparity
    ruling.

    Note:
        Exact integers end to end; no float; no ``abs``.
    """
    chi = character_of(rep, char_table)
    k = char_table["k"]
    order = char_table["order"]
    deg = char_table["degree"]
    sizes = char_table["class_sizes"]
    invc = char_table["inverse_class"]
    table = char_table["table"]
    degrees = char_table["degrees"]
    character = chi["character"]

    zeta_lane = chi["kind"] == "cyclotomic"
    phi = list(char_table["phi_e"])

    multiplicities: List[int] = []
    for i in range(k):
        acc = [0] * deg
        if zeta_lane:
            # The character is a ζ-VECTOR, so the contraction is a RING
            # product, not a scalar scale.  ⚠️ The scalar spelling below
            # is not merely wrong here, it is SILENTLY wrong:
            # ``sizes[j] * character[j]`` on a tuple REPEATS the tuple,
            # raises nothing, and dies two lines later on a shape that no
            # longer names its cause.
            for j in range(k):
                value = character[j]
                if any(value):
                    product = _zeta_mul(value, table[i][invc[j]], phi)
                    size = sizes[j]
                    for t in range(deg):
                        acc[t] += size * product[t]
        else:
            for j in range(k):
                weight = sizes[j] * character[j]
                if weight:
                    cell = table[i][invc[j]]
                    for t in range(deg):
                        acc[t] += weight * cell[t]
        if any(acc[1:]):
            raise ValueError(
                f"decompose_representation: <chi, chi_{i}> keeps nonzero "
                f"zeta coordinates {tuple(acc)} - a multiplicity is a "
                f"rational integer (non-scalar-sum law; a guard that "
                f"fires is evidence)")
        m_i = _exact_div("decompose_representation", acc[0], order,
                         f"the <chi, chi_{i}> numerator")
        if m_i < 0:
            raise ValueError(
                f"decompose_representation: <chi, chi_{i}> = {m_i} is "
                f"negative - multiplicities count irrep constituents "
                f"(non-negativity law; a guard that fires is evidence)")
        multiplicities.append(m_i)

    dimension_total = 0
    for m_i, d_i in zip(multiplicities, degrees):
        dimension_total += m_i * d_i
    if dimension_total != chi["degree"]:
        raise ValueError(
            f"decompose_representation: sum m_i*d_i = {dimension_total} "
            f"!= degree = {chi['degree']} (dimension law; a guard that "
            f"fires is evidence)")

    norm = sum(m_i * m_i for m_i in multiplicities)
    body = ",".join(str(m) for m in multiplicities).encode("utf-8")
    return {
        "k": k,
        "order": order,
        "degree": chi["degree"],
        "multiplicities": tuple(multiplicities),
        "norm": norm,
        "is_irreducible": norm == 1,
        "character": character,
        "degrees": degrees,
        "table_sha256": chi["table_sha256"],
        "cayley_sha256": chi["cayley_sha256"],
        "multiplicities_sha256": sha256_bytes(body),
    }


def isotypic_projector(rep: Mapping[str, Any],
                       char_table: Mapping[str, Any]) -> Dict[str, Any]:
    """The isotypic projector family of a MODULE — **Class L**, the op
    rc457 declined for want of a representation object, now buildable:
    the evaluation ``rho(e_chi) = (d_i/|G|) · Σ_g chi_i(g⁻¹)·rho(g)``
    that :func:`central_idempotents`' own docstring promises the caller
    performs ("for any other module the caller evaluates rho(e_chi)") —
    THIS op is that evaluation, shipped.

    ``chi_i(g⁻¹)`` is payload-resident — ``table[i][inverse_class[
    class_of[g]]]`` — so no element inverses are ever computed
    (measured: the contraction groups by class, ``P_i = d_i · Σ_j
    chi_i(j⁻¹) · S_j`` with ``S_j = Σ_{g ∈ C_j} rho(g)`` the class
    sums).

    **The deferred-division carrier** (the :func:`central_idempotents`
    precedent): integer ζ-vector NUMERATORS over ONE explicit
    ``denominator`` — ``|G|`` for a permutation kind; ``|G| · L`` for a
    general or cyclotomic kind, ``L`` = lcm of every entry denominator
    (each entry numerator scaled by ``L / den`` — DERIVED per entry, not
    asserted; on the cyclotomic lane the lcm runs over every ζ
    COORDINATE denominator).  Division is never performed; the caller
    lifts into :class:`srmech.math.qalg.Qalg` when a rational is wanted.

    **The ζ lane (rc462).**  The output carrier does not move: the
    projectors were ALREADY ζ-vectors, because ``chi_i(g⁻¹)`` always was.
    What changes is one multiplication — a cyclotomic entry is itself a
    ζ-vector, so ``chi_i(j⁻¹) · S_j`` becomes a RING product through the
    same ``_zeta_mul`` kernel :func:`zeta_mul` promotes, where the ℚ lanes
    scale a vector by an integer.  Both guards below are unchanged in
    statement and both execute on the new lane.

    In-op guards (cheap, ``O(k·d²·φ(e))``), each a raise:

    * **completeness law** — ``Σ_i P_i == denominator · I`` as
      ζ-vectors (column orthogonality against the identity, executed);
    * **trace law** — ``trace(P_i)`` lands on the scalar lane and equals
      ``denominator · m_i · d_i`` (the multiplicities are the internal
      :func:`decompose_representation` contraction, echoed).

    Idempotence ``P_i·P_i == denominator·P_i``, mutual orthogonality
    ``P_i·P_j == 0`` and equivariance ``P_i·rho(g) == rho(g)·P_i`` are
    TEST-side by two independent routes (the rc457 ``e·e = e`` ruling,
    restated here next to the guards that stay in-op): route (i)
    contracts via :func:`zeta_mul`'s kernel; route (ii), on the regular
    representation, the family must equal :func:`central_idempotents`'
    numerators expanded per element via ``class_of`` — the shipped
    universal element meeting its promised evaluation; a disagreement
    between routes is a finding.

    Args:
        rep: a tier-4 REP PAYLOAD dict, passed VERBATIM.
        char_table: a :func:`character_table` payload dict, passed
            VERBATIM (both validated inside the internal
            :func:`decompose_representation` composition, which is also
            where the rc460 :func:`_same_group_bind` reaches this op).

    Returns:
        ``{"k", "order", "degree", "degrees"`` (echoed),
        ``"multiplicities"`` (the internal decompose contraction,
        echoed), ``"denominator"``, ``"projectors"`` — k × d × d × φ(e)
        nested int tuples, irrep-major — ``"phi_e"`` (echoed),
        ``"table_sha256"`` / ``"cayley_sha256"`` / ``"matrices_sha256"``
        (echoed), ``"projectors_sha256"}``.

    Cost honest: ``O(|G|·d² + k²·d²·φ(e))`` — the op targets the same
    small-order stratum every sibling does; a large order or degree
    makes it SLOW, never wrong.

    C-parity (ADR-0009, recorded): this op has no C peer; the
    representation stratum ships Python-first under the noted-disparity
    ruling.

    Note:
        Exact integers over one explicit denominator; no float; no
        ``abs``.
    """
    decomposition = decompose_representation(rep, char_table)
    k = char_table["k"]
    order = char_table["order"]
    deg = char_table["degree"]
    invc = char_table["inverse_class"]
    table = char_table["table"]
    degrees = char_table["degrees"]
    class_of = char_table["class_of"]
    d = rep["degree"]
    kind = rep["kind"]
    matrices = rep["matrices"]
    multiplicities = decomposition["multiplicities"]

    zeta_lane = kind == "cyclotomic"
    phi = list(char_table["phi_e"])
    if kind == "permutation":
        scale_lcm = 1
        scaled = matrices
    elif kind == "general":
        scale_lcm = 1
        for mat in matrices:
            for row in mat:
                for cell in row:
                    den = cell[1]
                    shrink = gcd(scale_lcm, den)
                    scale_lcm = scale_lcm // shrink * den
        scaled = [[[cell[0] * (scale_lcm // cell[1]) for cell in row]
                   for row in mat] for mat in matrices]
    else:
        scale_lcm = 1
        for mat in matrices:
            for row in mat:
                for cell in row:
                    for coordinate in cell:
                        den = coordinate[1]
                        shrink = gcd(scale_lcm, den)
                        scale_lcm = scale_lcm // shrink * den
        scaled = [[[tuple(coordinate[0] * (scale_lcm // coordinate[1])
                          for coordinate in cell) for cell in row]
                   for row in mat] for mat in matrices]
    denominator = order * scale_lcm

    if zeta_lane:
        zeta_sums = [[[[0] * deg for _ in range(d)] for _ in range(d)]
                     for _ in range(k)]
        for g in range(order):
            target = zeta_sums[class_of[g]]
            source = scaled[g]
            for r in range(d):
                target_row = target[r]
                source_row = source[r]
                for c in range(d):
                    cell_out = target_row[c]
                    cell_in = source_row[c]
                    for t in range(deg):
                        cell_out[t] += cell_in[t]
        class_sums = []
    else:
        zeta_sums = []
        class_sums = [[[0] * d for _ in range(d)] for _ in range(k)]
        for g in range(order):
            target = class_sums[class_of[g]]
            source = scaled[g]
            for r in range(d):
                target_row = target[r]
                source_row = source[r]
                for c in range(d):
                    target_row[c] += source_row[c]

    projectors: List[Tuple[Tuple[Tuple[int, ...], ...], ...]] = []
    for i in range(k):
        d_i = degrees[i]
        chi_inv = [table[i][invc[j]] for j in range(k)]
        rows_out: List[Tuple[Tuple[int, ...], ...]] = []
        for r in range(d):
            row_out: List[Tuple[int, ...]] = []
            for c in range(d):
                acc = [0] * deg
                if zeta_lane:
                    for j in range(k):
                        s_vec = zeta_sums[j][r][c]
                        if any(s_vec):
                            product = _zeta_mul(s_vec, chi_inv[j], phi)
                            for t in range(deg):
                                acc[t] += product[t]
                else:
                    for j in range(k):
                        s = class_sums[j][r][c]
                        if s:
                            vec = chi_inv[j]
                            for t in range(deg):
                                acc[t] += s * vec[t]
                row_out.append(tuple(d_i * x for x in acc))
            rows_out.append(tuple(row_out))
        projectors.append(tuple(rows_out))

    for r in range(d):
        for c in range(d):
            for t in range(deg):
                total = 0
                for i in range(k):
                    total += projectors[i][r][c][t]
                want = denominator if (r == c and t == 0) else 0
                if total != want:
                    raise ValueError(
                        f"isotypic_projector: sum_i P_i[{r}][{c}] "
                        f"coordinate {t} is {total}, expected {want} - "
                        f"the projector family must sum to "
                        f"denominator * I (completeness law; a guard "
                        f"that fires is evidence)")
    for i in range(k):
        acc = [0] * deg
        for r in range(d):
            cell = projectors[i][r][r]
            for t in range(deg):
                acc[t] += cell[t]
        if any(acc[1:]):
            raise ValueError(
                f"isotypic_projector: trace(P_{i}) keeps nonzero zeta "
                f"coordinates {tuple(acc)} - an isotypic dimension is a "
                f"rational integer (trace law; a guard that fires is "
                f"evidence)")
        want = denominator * multiplicities[i] * degrees[i]
        if acc[0] != want:
            raise ValueError(
                f"isotypic_projector: trace(P_{i}) = {acc[0]}, expected "
                f"denominator * m_{i} * d_{i} = {want} (trace law; a "
                f"guard that fires is evidence)")

    body = "\n\n".join(
        "\n".join(
            ";".join(",".join(str(x) for x in cell) for cell in row)
            for row in proj)
        for proj in projectors).encode("utf-8")
    return {
        "k": k,
        "order": order,
        "degree": d,
        "degrees": degrees,
        "multiplicities": multiplicities,
        "denominator": denominator,
        "projectors": tuple(projectors),
        "phi_e": char_table["phi_e"],
        "table_sha256": char_table["table_sha256"],
        "cayley_sha256": rep["cayley_sha256"],
        "matrices_sha256": rep["matrices_sha256"],
        "projectors_sha256": sha256_bytes(body),
    }


def _entry_pair(kind: str, cell) -> Tuple[int, int]:
    """A matrix entry as a canonical ``(num, den)`` pair: a permutation
    kind's 0/1 int rides as ``(v, 1)``; a general kind's pair is already
    canonical (the validator's canonical-pair law)."""
    if kind == "permutation":
        return (cell, 1)
    return (cell[0], cell[1])


def _refuse_zeta_dialect(op: str, law: str, verb: str, *operands) -> None:
    """The DIALECT / CARRIER law (rc462): a named refusal of the ζ dialect
    by the three tier-4 consumers this rc does not widen.  ``law`` is the
    name the raise ends with — ⊗ / ⊕ refuse on the DIALECT (the dialect is
    unbuilt), :func:`intertwiner_space` on the CARRIER (no exact
    ``ℚ(ζ_e)``-matrix carrier exists to build it on), and the two are
    different facts.

    **Why a refusal is a complete state and not a gap.**  Each of these
    ops would need real new mathematics — a ζ-ring product per entry for
    ⊗ / ⊕, and for :func:`intertwiner_space` an exact ``ℚ(ζ_e)``-matrix
    nullspace, which NO carrier in :mod:`srmech.math` provides (the engine
    is :meth:`srmech.math.qmat.QMat.nullspace`, exact-ℚ only).  Silently
    ℚ-restricting the operand would not be a smaller answer, it would be
    a WRONG one: ``dim Hom`` over ``ℚ(ζ_e)`` and over ``ℚ`` differ by a
    factor of ``φ(e)`` on exactly the reps the widening admits.

    **Why it must fire HERE and not earlier.**  The refusal is placed
    AFTER :func:`_check_rep_payload`, so the payload it refuses is one the
    validator ACCEPTS — an instrument that could only ever be reached by
    an already-invalid operand is not a measurement.

    It is also the reason :func:`_same_group_guard` needs no dialect
    clause of its own: a ℚ payload and a ζ payload OF THE SAME GROUP carry
    EQUAL ``cayley_sha256``, so the same-group law passes a mixed pair
    happily; this law is what stops it."""
    for label, operand in operands:
        if operand["kind"] == "cyclotomic":
            raise ValueError(
                f"{op}: {label} is a cyclotomic-dialect payload over "
                f"{operand['field']}; {verb} ({law})")


def _same_group_guard(op: str, rep1: Mapping[str, Any],
                      rep2: Mapping[str, Any]) -> None:
    """The same-group law: two rep operands compose only over ONE group
    with ONE element indexing, and the payloads carry that bind as the
    Class-A ``cayley_sha256``.  Equality of the content address is the
    executable form of "same table, same indexing"."""
    if rep1["cayley_sha256"] != rep2["cayley_sha256"]:
        raise ValueError(
            f"{op}: the two rep payloads carry different cayley_sha256 "
            f"content addresses - representations compose only over ONE "
            f"group with ONE Cayley indexing (same-group law)")
    if rep1["order"] != rep2["order"]:
        raise ValueError(
            f"{op}: rep orders {rep1['order']} != {rep2['order']} "
            f"(same-group law)")


def tensor_product_representation(
        rep1: Mapping[str, Any],
        rep2: Mapping[str, Any]) -> Dict[str, Any]:
    """The tensor product ``rho1 ⊗ rho2`` of two representations of ONE
    group — **Class M**, argued rather than adopted: the M-bind claim is
    honest now by fusion's own criterion.  :func:`fusion_multiplicities`
    declined Class M because "an M-bind claim implies an unbind
    (character division), which is neither shipped nor measured" —
    :func:`decompose_representation` and :func:`isotypic_projector` ARE
    that unbind for the rep object (the bound module splits back into
    its constituents), shipped and measured in this same rc, so the bind
    half may finally say its name.

    Kronecker per element, the ROW-MAJOR pair index pinned once:
    ``(x1, x2) ↦ x1·d2 + x2`` — the same convention
    :meth:`srmech.math.qmat.QMat.kron` and :func:`intertwiner_space`
    use; ONE convention, stated once, executed by the tests via
    ``(A⊗B)(C⊗D) == AC⊗BD``.

    ``perm ⊗ perm`` stays ``kind="permutation"`` with the constructed
    pair action — and the output payload is RE-VALIDATED by
    :func:`_check_rep_payload` before it is returned (never trusted by
    construction: bijection, matrix-entry, matrix-action coherence and
    content-address laws all execute on the op's OWN output).  Any
    general operand makes a general output, entries as canonical pairs.

    Args:
        rep1: a tier-4 REP PAYLOAD dict, passed VERBATIM.
        rep2: a second rep payload OF THE SAME GROUP — the same-group
            law checks ``cayley_sha256`` equality (same table, same
            indexing) and raises otherwise.

    Returns:
        A full REP PAYLOAD dict of degree ``d1·d2`` — it eats anywhere a
        constructor payload does (:func:`character_of` /
        :func:`decompose_representation` / :func:`isotypic_projector` /
        :func:`intertwiner_space`); the tests execute
        ``decompose(rho_a ⊗ rho_b)`` against the SHIPPED
        :func:`fusion_multiplicities` tensor.

    C-parity (ADR-0009, recorded): this op has no C peer; the
    representation stratum ships Python-first under the noted-disparity
    ruling.

    Note:
        Exact integers / canonical pairs; no float; no ``abs``.
    """
    _check_rep_payload("tensor_product_representation", rep1)
    _check_rep_payload("tensor_product_representation", rep2)
    _refuse_zeta_dialect(
        "tensor_product_representation", "dialect law",
        "⊗ ships for the exact-ℚ dialect only - the Kronecker entry "
        "product over Q(zeta_e) is a RING multiply per cell, deliberately "
        "deferred to its own rc rather than half-built here",
        ("rep1", rep1), ("rep2", rep2))
    _same_group_guard("tensor_product_representation", rep1, rep2)
    order = rep1["order"]
    d1 = rep1["degree"]
    d2 = rep2["degree"]
    degree = d1 * d2

    if rep1["kind"] == "permutation" and rep2["kind"] == "permutation":
        a1 = rep1["action"]
        a2 = rep2["action"]
        action = [
            [a1[g][x1] * d2 + a2[g][x2]
             for x1 in range(d1) for x2 in range(d2)]
            for g in range(order)]
        matrices = []
        for g in range(order):
            mat = [[0] * degree for _ in range(degree)]
            for j in range(degree):
                mat[action[g][j]][j] = 1
            matrices.append(mat)
        out: Dict[str, Any] = {
            "order": order,
            "degree": degree,
            "field": "Q",
            "kind": "permutation",
            "matrices": matrices,
            "action": action,
            "cayley_sha256": rep1["cayley_sha256"],
            "matrices_sha256": sha256_bytes(
                _rep_matrices_bytes("permutation", matrices)),
        }
    else:
        k1 = rep1["kind"]
        k2 = rep2["kind"]
        m1 = rep1["matrices"]
        m2 = rep2["matrices"]
        matrices = []
        for g in range(order):
            mat = []
            for r1 in range(d1):
                for r2 in range(d2):
                    row = []
                    for c1 in range(d1):
                        n1, e1 = _entry_pair(k1, m1[g][r1][c1])
                        for c2 in range(d2):
                            n2, e2 = _entry_pair(k2, m2[g][r2][c2])
                            row.append(_canonical_pair(n1 * n2, e1 * e2))
                    mat.append(row)
            matrices.append(mat)
        out = {
            "order": order,
            "degree": degree,
            "field": "Q",
            "kind": "general",
            "matrices": matrices,
            "cayley_sha256": rep1["cayley_sha256"],
            "matrices_sha256": sha256_bytes(
                _rep_matrices_bytes("general", matrices)),
        }
    _check_rep_payload("tensor_product_representation", out)
    return out


def direct_sum_representation(
        rep1: Mapping[str, Any],
        rep2: Mapping[str, Any]) -> Dict[str, Any]:
    """The direct sum ``rho1 ⊕ rho2`` of two representations of ONE
    group — **Class B** (TLV shape: the blocks are RECOVERABLE — the
    leading ``d1 × d1`` block is ``rho1(g)`` verbatim and the trailing
    ``d2 × d2`` block is ``rho2(g)`` verbatim, a claim the tests execute
    rather than assert).

    Block-diagonal per element; degree ``d1 + d2``.  ``perm ⊕ perm``
    stays ``kind="permutation"`` with the disjoint-union action
    (``j < d1 ↦ a1[g][j]``; else ``d1 + a2[g][j-d1]``), and the output
    payload is RE-VALIDATED by :func:`_check_rep_payload` before return
    (never trusted by construction).  Any general operand makes a
    general output, entries as canonical pairs (off-block zeros as
    ``(0, 1)``).

    Args:
        rep1: a tier-4 REP PAYLOAD dict, passed VERBATIM.
        rep2: a second rep payload OF THE SAME GROUP (same-group law:
            ``cayley_sha256`` equality, raise otherwise).

    Returns:
        A full REP PAYLOAD dict of degree ``d1 + d2`` — characters ADD
        and multiplicities ADD, both executed by the tests.

    C-parity (ADR-0009, recorded): this op has no C peer; the
    representation stratum ships Python-first under the noted-disparity
    ruling.

    Note:
        Exact integers / canonical pairs; no float; no ``abs``.
    """
    _check_rep_payload("direct_sum_representation", rep1)
    _check_rep_payload("direct_sum_representation", rep2)
    _refuse_zeta_dialect(
        "direct_sum_representation", "dialect law",
        "⊕ ships for the exact-ℚ dialect only - a block-diagonal sum over "
        "Q(zeta_e) needs the ζ zero cell and the ζ entry lift, "
        "deliberately deferred to its own rc rather than half-built here",
        ("rep1", rep1), ("rep2", rep2))
    _same_group_guard("direct_sum_representation", rep1, rep2)
    order = rep1["order"]
    d1 = rep1["degree"]
    d2 = rep2["degree"]
    degree = d1 + d2

    if rep1["kind"] == "permutation" and rep2["kind"] == "permutation":
        a1 = rep1["action"]
        a2 = rep2["action"]
        action = [
            [a1[g][j] for j in range(d1)]
            + [d1 + a2[g][j] for j in range(d2)]
            for g in range(order)]
        matrices = []
        for g in range(order):
            mat = [[0] * degree for _ in range(degree)]
            for j in range(degree):
                mat[action[g][j]][j] = 1
            matrices.append(mat)
        out: Dict[str, Any] = {
            "order": order,
            "degree": degree,
            "field": "Q",
            "kind": "permutation",
            "matrices": matrices,
            "action": action,
            "cayley_sha256": rep1["cayley_sha256"],
            "matrices_sha256": sha256_bytes(
                _rep_matrices_bytes("permutation", matrices)),
        }
    else:
        k1 = rep1["kind"]
        k2 = rep2["kind"]
        m1 = rep1["matrices"]
        m2 = rep2["matrices"]
        zero = (0, 1)
        matrices = []
        for g in range(order):
            mat = []
            for r in range(d1):
                row = [_canonical_pair(*_entry_pair(k1, m1[g][r][c]))
                       for c in range(d1)] + [zero] * d2
                mat.append(row)
            for r in range(d2):
                row = [zero] * d1 + [
                    _canonical_pair(*_entry_pair(k2, m2[g][r][c]))
                    for c in range(d2)]
                mat.append(row)
            matrices.append(mat)
        out = {
            "order": order,
            "degree": degree,
            "field": "Q",
            "kind": "general",
            "matrices": matrices,
            "cayley_sha256": rep1["cayley_sha256"],
            "matrices_sha256": sha256_bytes(
                _rep_matrices_bytes("general", matrices)),
        }
    _check_rep_payload("direct_sum_representation", out)
    return out


def intertwiner_space(rep1: Mapping[str, Any],
                      rep2: Mapping[str, Any]) -> Dict[str, Any]:
    """The intertwiner space ``Hom_G(V1, V2)`` — **Class L**, the Schur
    readout: an exact basis of the ``d2 × d1`` matrices ``X`` with
    ``rho2(g) · X == X · rho1(g)`` for EVERY ``g``.  Schur's lemma made
    an operand: between inequivalent irreducible constituents the
    dimension is 0, and ``dimension == Σ_i m_i(rho1) · m_i(rho2) ==
    ⟨χ1, χ2⟩`` — the tests execute that identity by a SECOND independent
    route (the cyclotomic :func:`decompose_representation` contraction)
    and a disagreement is a finding.

    The engine is the shipped exact-ℚ carrier: the equivariance system
    is vectorized ROW-MAJOR — ``vec(rho2(g)·X - X·rho1(g)) =
    (rho2(g) ⊗ I_{d1} - I_{d2} ⊗ rho1(g)ᵀ) · vec(X)`` via
    :meth:`srmech.math.qmat.QMat.kron` (the carrier method this rc
    adds) — stacked over ALL ``|G|`` elements (rep payloads carry no
    generator set; the small-order stratum contract), and the kernel is
    :meth:`srmech.math.qmat.QMat.nullspace` (exact Gauss-Jordan over ℚ,
    C-backed via ``srmech_qmat_nullspace``).

    **The zero-dimension case is a CLASSIFIED RETURN, not a failure** —
    an instrument that cannot return otherwise is not a measurement:
    ``dimension == 0`` with ``basis == []`` IS the Schur verdict for
    disjoint irreducible content.

    Args:
        rep1: a tier-4 REP PAYLOAD dict, passed VERBATIM.
        rep2: a second rep payload OF THE SAME GROUP (same-group law:
            ``cayley_sha256`` equality, raise otherwise).

    Returns:
        ``{"dimension"`` (plain int), ``"basis"`` — a list of ``d2 × d1``
        matrices of canonical ``(num, den)`` pairs, one per kernel basis
        vector, row-major de-vectorized — ``"cayley_sha256"`` (echoed),
        ``"basis_sha256"}``.  Every returned basis element's equivariance
        is re-executed test-side against the raw matrix products (the
        independent route — a Kronecker-convention defect inside this op
        would survive an in-op recheck that used the same convention).

    Cost honest: the stacked system is ``(|G|·d1·d2) × (d1·d2)`` over
    exact ℚ — a large order or degree makes it SLOW, never wrong (the
    fusion wording; same stratum contract).

    C-parity (ADR-0009, recorded): C-backed THROUGH its carrier only —
    the nullspace kernel dispatches to ``srmech_qmat_nullspace``; the
    system builder is Python, honestly stated.

    Note:
        Exact rationals end to end; no float; no ``abs``.
    """
    _check_rep_payload("intertwiner_space", rep1)
    _check_rep_payload("intertwiner_space", rep2)
    _refuse_zeta_dialect(
        "intertwiner_space", "carrier law",
        "the Schur kernel is QMat.nullspace, an exact-ℚ Gauss-Jordan, and "
        "NO exact Q(zeta_e)-matrix carrier ships anywhere in srmech.math - "
        "restricting the operand to its rational part would change "
        "dim Hom by a factor of phi(e), so this op REFUSES rather than "
        "answering a different question",
        ("rep1", rep1), ("rep2", rep2))
    _same_group_guard("intertwiner_space", rep1, rep2)
    order = rep1["order"]
    d1 = rep1["degree"]
    d2 = rep2["degree"]
    k1 = rep1["kind"]
    k2 = rep2["kind"]

    def _as_qmat(kind: str, mat) -> QMat:
        if kind == "permutation":
            return QMat.from_rows(mat)
        return QMat.from_rows(
            [[(cell[0], cell[1]) for cell in row] for row in mat])

    eye1 = QMat.identity(d1)
    eye2 = QMat.identity(d2)
    stacked: List[List[Any]] = []
    for g in range(order):
        rho1_t = _as_qmat(k1, rep1["matrices"][g]).transpose()
        rho2 = _as_qmat(k2, rep2["matrices"][g])
        block = rho2.kron(eye1) - eye2.kron(rho1_t)
        for row in block:
            stacked.append(list(row))
    kernel = QMat.from_rows(stacked).nullspace()

    basis = []
    for vec in kernel:
        mat = [[vec[r * d1 + c, 0].as_pair() for c in range(d1)]
               for r in range(d2)]
        basis.append(mat)
    body = "\n\n".join(
        "\n".join(",".join(f"{cell[0]}/{cell[1]}" for cell in row)
                  for row in mat)
        for mat in basis).encode("utf-8")
    return {
        "dimension": len(basis),
        "basis": basis,
        "cayley_sha256": rep1["cayley_sha256"],
        "basis_sha256": sha256_bytes(body),
    }


# ──────────────────────────────────────────────────────────────────────
# tier 4, the ζ dialect (rc462, `#T1179`) — the widening ships WITH ITS
# FIRST PRODUCER.  A checker widened alone mints a dialect no producer
# can write and no consumer can read; induced_representation is the
# producer (monomial Ind_H^G of a linear character, the smallest
# construction that forces every component of the package: cell grammar,
# ring keys, domain-separated serializer, ζ-vector trace, ring-product
# contraction) and zeta_conjugate is the Galois action on it.
# ──────────────────────────────────────────────────────────────────────


def _subgroup_scan(op: str, tbl: List[List[int]], subgroup: Sequence[int],
                   e_idx: int, inv: List[int]) -> List[int]:
    """Validate ``subgroup`` as a genuine subgroup of the table, returning
    its ASCENDING element list.  Each failure a ``ValueError`` naming the
    law: plain-int indices in range, no repeats, the identity present,
    closed under the product, closed under inverses."""
    n = len(tbl)
    seen: List[int] = []
    for i, h in enumerate(subgroup):
        if not _plain_int(h) or not 0 <= h < n:
            raise ValueError(
                f"{op}: subgroup[{i}] = {h!r} is not an element index in "
                f"[0, {n}) (subgroup law)")
        if h in seen:
            raise ValueError(
                f"{op}: subgroup lists element {h} twice - a subgroup is "
                f"a SET (subgroup law)")
        seen.append(h)
    if not seen:
        raise ValueError(
            f"{op}: subgroup is empty; every subgroup contains the "
            f"identity (subgroup law)")
    if e_idx not in seen:
        raise ValueError(
            f"{op}: subgroup {sorted(seen)} does not contain the identity "
            f"{e_idx} (subgroup law)")
    members = set(seen)
    for a in seen:
        if inv[a] not in members:
            raise ValueError(
                f"{op}: subgroup is not closed under inverses - {a} is in "
                f"it and {inv[a]} is not (subgroup law)")
        for b in seen:
            if tbl[a][b] not in members:
                raise ValueError(
                    f"{op}: subgroup is not closed - {a}*{b} = "
                    f"{tbl[a][b]} is outside it (subgroup law)")
    return sorted(seen)


def induced_representation(cayley_table: Sequence[Sequence[int]],
                           subgroup: Sequence[int],
                           character: Sequence[Sequence[int]],
                           e: int) -> Dict[str, Any]:
    """The induced representation ``Ind_H^G χ`` of a LINEAR character of a
    subgroup — **Class L** (mints the operator family, the
    :func:`permutation_representation` verb) over Class-I coset
    arithmetic, and THE FIRST PRODUCER of the ``ℚ(ζ_e)`` rep dialect
    (rc462, `#T1179`).

    Every rep the tier-4 stratum could mint before this op was defined
    over ℚ, so the whole ζ half of the payload grammar had no writer.
    Induction is the smallest construction that forces all of it: the
    matrices are MONOMIAL over ``ℤ[ζ_e]``, so a single op exercises the
    cell grammar, the ring keys, the domain-separated content address,
    the ζ-vector trace and the ring-product contraction at once.

    **The construction.**  With ``t_1, …, t_m`` the left-coset
    representatives of ``H`` in ``G`` (``m = [G:H]``, each coset's
    SMALLEST element index, cosets ordered by that element — a
    deterministic choice, since a content address cannot depend on an
    iteration order)::

        rho(g)[i][j] = chi(t_i⁻¹ · g · t_j)   if  t_i⁻¹ · g · t_j ∈ H
                     = 0                       otherwise

    Exactly one ``i`` is nonzero per column ``j`` (``g·t_j`` lies in ONE
    coset), which is the pinned tier-4 convention ``matrices[g] · e_j =
    <unit> · e_{sigma_g(j)}`` — and for the TRIVIAL character it reduces
    EXACTLY to :func:`permutation_representation` on the coset set, a
    claim the tests execute rather than assert.

    **The homomorphism law, executed at construction.**  ``rho`` is
    stored internally as its monomial data ``(sigma_g, c_g)`` and the law
    ``rho(g)·rho(h) == rho(g·h)`` is checked over ALL ``|G|²`` pairs on
    that data — ``sigma_g(sigma_h(j))`` with value ``c_g[sigma_h(j)] ·
    c_h[j]`` in ``ℤ[ζ_e]``.  That is the matrix law and not a proxy for
    it, because the matrices are BUILT from exactly this data (one
    nonzero per column, at ``sigma_g(j)``, of value ``c_g[j]``); doing it
    monomially costs ``O(|G|²·m)`` ring products where the dense form
    costs ``O(|G|²·m³)``.  The tests re-execute the DENSE matrix products
    independently on both shipped witnesses.

    Args:
        cayley_table: the ``n × n`` group table (validated as a group —
            two-sided identity, unique two-sided inverses, associative;
            ``ValueError`` naming the operand-group law otherwise).
        subgroup: the element indices of ``H`` — a table-indexed SET,
            validated closed under the product and under inverses and to
            contain the identity (subgroup law).  ``H = G`` is legal and
            gives ``Ind_G^G χ == χ`` at degree 1.
        character: ``character[i]`` is ``χ`` at ``sorted(subgroup)[i]``,
            a length-``φ(e)`` plain-int vector in the ``ζ_e`` power basis
            low→high — the SAME carrier :func:`zeta_mul` and
            :func:`character_table` use.  A linear character's values are
            roots of unity, hence algebraic integers, hence integer
            coordinates; the op refuses anything else (plain-int law) and
            executes ``χ(a·b) == χ(a)·χ(b)`` over all of ``H × H``
            (character-homomorphism law) plus ``χ(1) == 1`` (unital law).
        e: the conductor, a plain int ``>= 3``.  ``ℚ(ζ₁) = ℚ(ζ₂) = ℚ``,
            which the ``general`` kind already spells, so a smaller
            conductor is refused (cyclotomic-conductor law) rather than
            silently minting a ℚ rep wearing the ζ dialect.  ``Φ_e``
            comes from :func:`srmech.math.poly.cyclotomic_polynomial`,
            never from the caller — the modulus is DERIVED here, which is
            what lets every consumer trust ``phi_e`` after one equality
            check.

    Returns:
        A full REP PAYLOAD dict in the ζ dialect — ``{"order", "degree"``
        (= the index ``m``), ``"field": "Q(zeta_<e>)", "kind":
        "cyclotomic", "e", "phi_e", "matrices"`` (m × m of length-``φ(e)``
        coordinate tuples of canonical ``(num, den)`` pairs),
        ``"subgroup"`` (echoed, ascending), ``"coset_representatives"``,
        ``"cayley_sha256", "matrices_sha256"}`` — and it is RE-VALIDATED
        by :func:`_check_rep_payload` before return (never trusted by
        construction, the ⊗/⊕ precedent).  It eats in
        :func:`character_of` / :func:`decompose_representation` /
        :func:`isotypic_projector`; :func:`tensor_product_representation`
        / :func:`direct_sum_representation` / :func:`intertwiner_space`
        REFUSE it with a named law in this rc.

    ⚠️ **Scope, stated where a caller meets it.**  The op will happily
    mint a rep whose conductor is SMALLER than the group exponent — e.g.
    ``Ind_{C7}^{F21}`` over ``ℚ(ζ₇)`` when ``F21`` has exponent 21 — and
    that rep is well-formed and passes the validator, but
    :func:`character_of` and its two composites REFUSE it under the
    compatible-ring law, because this rc does not embed ``ℤ[ζ₇]`` into the
    ``ζ₂₁`` power basis.  Choose ``e`` = the group exponent if the rep is
    to be read; the refusal is named and measured, not silent.

    Cost honest: ``O(|G|²·m)`` ring products for the homomorphism law and
    ``O(|H|²)`` for the character law — the same small-order stratum
    contract every sibling carries; a large order makes it SLOW, never
    wrong.

    C-parity (ADR-0009, recorded): this op has no C peer; the
    representation stratum ships Python-first under the noted-disparity
    ruling, and the ζ cells cross as plain-int tuples so no carrier TYPE
    reaches the wire and the ABI does not move.

    Note:
        Exact integers end to end; no float; no ``abs``.
    """
    tbl = _check_table("induced_representation", cayley_table)
    n = len(tbl)
    e_idx = _identity_of(tbl)
    if e_idx is None:
        raise ValueError(
            "induced_representation: cayley_table has no two-sided "
            "identity (operand-group law)")
    inv = _inverse_scan(tbl, e_idx)
    if inv is None:
        raise ValueError(
            "induced_representation: cayley_table lacks unique two-sided "
            "inverses (operand-group law)")
    _check_associative("induced_representation", "cayley_table", tbl)

    if not _plain_int(e) or e < 3:
        raise ValueError(
            f"induced_representation: e must be a plain int >= 3, not "
            f"{e!r} - Q(zeta_1) = Q(zeta_2) = Q, which the general kind "
            f"already spells (cyclotomic-conductor law)")
    phi_entry = cyclotomic_polynomial(e)
    phi = list(phi_entry["coefficients"])
    width = phi_entry["degree"]

    members = _subgroup_scan(
        "induced_representation", tbl, subgroup, e_idx, inv)
    if len(character) != len(members):
        raise ValueError(
            f"induced_representation: character has {len(character)} "
            f"values for |H| = {len(members)} elements - one value per "
            f"subgroup element, in ASCENDING element order "
            f"(element-count law)")
    chi: Dict[int, Tuple[int, ...]] = {}
    for i, h in enumerate(members):
        value = character[i]
        if len(value) != width:
            raise ValueError(
                f"induced_representation: character[{i}] has length "
                f"{len(value)}, expected phi({e}) = {width} "
                f"(carrier-width law)")
        for t, coordinate in enumerate(value):
            if not _plain_int(coordinate):
                raise ValueError(
                    f"induced_representation: character[{i}][{t}] carries "
                    f"a {type(coordinate).__name__} coordinate; a linear "
                    f"character's values are roots of unity, so the "
                    f"carrier is plain-int zeta vectors (plain-int law)")
        chi[h] = tuple(value)
    one = (1,) + (0,) * (width - 1)
    if chi[e_idx] != one:
        raise ValueError(
            f"induced_representation: chi at the identity is "
            f"{chi[e_idx]}, expected {one} - a character of a group sends "
            f"1 to 1 (unital law; a guard that fires is evidence)")
    for a in members:
        for b in members:
            if _zeta_mul(chi[a], chi[b], phi) != chi[tbl[a][b]]:
                raise ValueError(
                    f"induced_representation: chi({a})·chi({b}) != "
                    f"chi({a}*{b} = {tbl[a][b]}) in Z[zeta_{e}] - the "
                    f"operand is a LINEAR CHARACTER of H "
                    f"(character-homomorphism law; a guard that fires is "
                    f"evidence)")

    member_set = set(members)
    reps: List[int] = []
    covered: set = set()
    for x in range(n):
        if x in covered:
            continue
        reps.append(x)
        for h in members:
            covered.add(tbl[x][h])
    degree = len(reps)

    sigma: List[List[int]] = []
    values: List[List[Tuple[int, ...]]] = []
    for g in range(n):
        perm: List[int] = []
        val: List[Tuple[int, ...]] = []
        for j in range(degree):
            landed = tbl[g][reps[j]]
            target = -1
            for i in range(degree):
                probe = tbl[inv[reps[i]]][landed]
                if probe in member_set:
                    target = i
                    val.append(chi[probe])
                    break
            if target < 0:
                raise ValueError(
                    f"induced_representation: g = {g} sends coset "
                    f"representative {reps[j]} outside every coset - the "
                    f"coset system does not cover G (coset-cover law; a "
                    f"guard that fires is evidence)")
            perm.append(target)
        sigma.append(perm)
        values.append(val)

    for g in range(n):
        for h in range(n):
            composed = tbl[g][h]
            for j in range(degree):
                mid = sigma[h][j]
                if sigma[g][mid] != sigma[composed][j]:
                    raise ValueError(
                        f"induced_representation: the monomial "
                        f"permutations fail sigma_{g}(sigma_{h}({j})) == "
                        f"sigma_{{{g}*{h}}}({j}) (homomorphism law; a "
                        f"guard that fires is evidence)")
                if _zeta_mul(values[g][mid], values[h][j],
                             phi) != values[composed][j]:
                    raise ValueError(
                        f"induced_representation: the monomial values "
                        f"fail c_{g}[sigma_{h}({j})]·c_{h}[{j}] == "
                        f"c_{{{g}*{h}}}[{j}] in Z[zeta_{e}] "
                        f"(homomorphism law; a guard that fires is "
                        f"evidence)")

    zero_cell = ((0, 1),) * width
    matrices: List[List[List[Tuple[Tuple[int, int], ...]]]] = []
    for g in range(n):
        mat = [[zero_cell] * degree for _ in range(degree)]
        for j in range(degree):
            mat[sigma[g][j]][j] = tuple(
                _canonical_pair(coordinate, 1)
                for coordinate in values[g][j])
        matrices.append([list(row) for row in mat])

    out: Dict[str, Any] = {
        "order": n,
        "degree": degree,
        "field": _zeta_field(e),
        "kind": "cyclotomic",
        "e": e,
        "phi_e": tuple(phi),
        "matrices": matrices,
        "subgroup": members,
        "coset_representatives": reps,
        "cayley_sha256": sha256_bytes(_table_bytes(tbl)),
        "matrices_sha256": sha256_bytes(
            _rep_matrices_bytes("cyclotomic", matrices, e)),
    }
    _check_rep_payload("induced_representation", out)
    return out


def zeta_conjugate(rep: Mapping[str, Any], t: int) -> Dict[str, Any]:
    """The Galois conjugate ``σ_t(rho)`` of a cyclotomic representation —
    **Class C** (cascade-orientation / chirality: the
    :func:`frobenius_schur_indicator` docstring already names a character
    and its conjugate "a chirality PAIR, the Class-C datum"; this op is
    the operator-level form of that pairing).

    ``Gal(ℚ(ζ_e)/ℚ) ≅ (ℤ/e)^×`` acts by ``σ_t: ζ_e ↦ ζ_e^t``, and it acts
    on a REP by acting on every matrix entry.  Concretely, coordinate by
    coordinate::

        σ_t( Σ_j (n_j / d_j) · ζ^j )  =  Σ_j (n_j / d_j) · ζ^{j·t mod e}

    with each ``ζ^{j·t mod e}`` re-expanded in the power basis
    ``{1, ζ, …, ζ^{φ(e)−1}}`` — so the output is a rep over the SAME ring
    and eats everywhere its operand does.  The re-expansion table is
    built from ``Φ_e``, which is re-derived here from
    :func:`srmech.math.poly.cyclotomic_polynomial` and compared with the
    payload's own ``phi_e``: the checker's ring law can only see that
    ``phi_e`` is a monic modulus of the right degree, and this op is the
    one place the modulus's IDENTITY is load-bearing (a wrong ``Φ`` would
    give a wrong power table and a wrong, silent answer).

    **What it is for.**  For ``e = 4`` this is complex conjugation, and
    ``σ_3`` is the involution that exchanges a conjugate PAIR of complex
    irreps — the smallest executable form of "it swaps ``3`` and ``3̄``",
    since no shipped group has a conjugate pair of 3-dimensional irreps
    over ``ℚ(ζ₄)``.  Two identities the tests execute:
    ``zeta_conjugate(zeta_conjugate(rho, t), t) == rho`` whenever
    ``t² ≡ 1 (mod e)``, and the COMMUTING SQUARE ``zeta_conjugate(Ind χ,
    t) == Ind(σ_t ∘ χ)`` — conjugating the induced rep and inducing the
    conjugated character are the same object, compared by content
    address.

    Args:
        rep: a CYCLOTOMIC tier-4 REP PAYLOAD dict, passed VERBATIM.  A
            permutation- or general-kind payload is REFUSED (dialect law)
            rather than returned unchanged: the Galois action on ℚ is the
            identity, and an op that can only ever answer "the same thing
            back" is not a measurement.
        t: the Galois exponent, a plain int with ``gcd(t mod e, e) == 1``
            (Galois law).  It is reduced mod ``e``; ``t`` and ``t + e``
            name one automorphism.

    Returns:
        A full REP PAYLOAD dict over the same ring, degree and group —
        ``{"order", "degree", "field", "kind": "cyclotomic", "e",
        "phi_e", "matrices", "cayley_sha256"`` (echoed — a Galois twist
        does not change the GROUP), ``"matrices_sha256"}`` — RE-VALIDATED
        by :func:`_check_rep_payload` before return.

    C-parity (ADR-0009, recorded): this op has no C peer; the
    representation stratum ships Python-first under the noted-disparity
    ruling.

    Note:
        Exact integers / canonical pairs; no float; no ``abs`` — the sign
        read is :func:`_canonical_pair`'s Class-K pin-slot at zero.
    """
    _check_rep_payload("zeta_conjugate", rep)
    if rep["kind"] != "cyclotomic":
        raise ValueError(
            f"zeta_conjugate: the operand is a {rep['kind']!r}-kind "
            f"payload over {rep['field']!r}; Gal(Q/Q) is trivial, so a "
            f"rational rep has no Galois twist to take and this op "
            f"REFUSES rather than handing back its operand (dialect law)")
    e = rep["e"]
    phi = list(rep["phi_e"])
    width = len(phi) - 1
    derived = cyclotomic_polynomial(e)
    if tuple(derived["coefficients"]) != tuple(phi):
        raise ValueError(
            f"zeta_conjugate: the payload carries the modulus "
            f"{tuple(phi)} where Phi_{e} is "
            f"{tuple(derived['coefficients'])} - the power table this op "
            f"builds is only correct for the TRUE cyclotomic modulus "
            f"(cyclotomic-modulus law; a guard that fires is evidence)")
    if not _plain_int(t):
        raise ValueError(
            f"zeta_conjugate: t must be a plain int, not {t!r} "
            f"(Galois law)")
    exponent = t % e
    if gcd(exponent, e) != 1:
        raise ValueError(
            f"zeta_conjugate: t = {t} reduces to {exponent} mod {e}, "
            f"which is not a unit - Gal(Q(zeta_{e})/Q) is (Z/{e})^*, so "
            f"only exponents coprime to {e} name an automorphism "
            f"(Galois law)")
    powers = _zeta_power_table(phi, e)

    matrices: List[List[List[Tuple[Tuple[int, int], ...]]]] = []
    for mat in rep["matrices"]:
        rows_out = []
        for row in mat:
            row_out = []
            for cell in row:
                common = 1
                for coordinate in cell:
                    den = coordinate[1]
                    shrink = gcd(common, den)
                    common = common // shrink * den
                acc = [0] * width
                for j, coordinate in enumerate(cell):
                    num = coordinate[0]
                    if num:
                        scaled = num * (common // coordinate[1])
                        image = powers[(j * exponent) % e]
                        for c in range(width):
                            acc[c] += scaled * image[c]
                row_out.append(tuple(
                    _canonical_pair(acc[c], common) for c in range(width)))
            rows_out.append(row_out)
        matrices.append(rows_out)

    out: Dict[str, Any] = {
        "order": rep["order"],
        "degree": rep["degree"],
        "field": rep["field"],
        "kind": "cyclotomic",
        "e": e,
        "phi_e": tuple(phi),
        "matrices": matrices,
        "cayley_sha256": rep["cayley_sha256"],
        "matrices_sha256": sha256_bytes(
            _rep_matrices_bytes("cyclotomic", matrices, e)),
    }
    _check_rep_payload("zeta_conjugate", out)
    return out
