"""``srmech.math.groups`` — the REPRESENTATION stratum over finite Cayley
tables (rc456 tiers 1–2; rc457 tier 3).

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

Exact arithmetic ONLY: no float, no ``abs`` — the single sign-handling site
is :func:`_small_lift`, the named Class-K pin-slot at the ``p/2`` phase
boundary with Class-C re-application.  All content addresses route through
:func:`srmech.amsc.format.sha256_bytes`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from srmech.amsc.format import sha256_bytes
from srmech.cascade import conjugacy_census
from srmech.math.cyclic import gcd, mod_add, mod_inv, mod_pow
from srmech.math.modular_linalg import gf_nullspace, gf_solve
from srmech.math.poly import cyclotomic_polynomial
from srmech.math.primes import factor, is_prime

__all__ = [
    "abelianization",
    "cayley_graph",
    "central_idempotents",
    "character_table",
    "conjugacy_classes",
    "cyclic_group",
    "derived_subgroup",
    "frobenius_schur_indicator",
    "fusion_multiplicities",
    "irrep_dimensions",
    "quotient_group",
    "semidirect_product",
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
# cyclotomic power-basis arithmetic (private).  Public promotion of
# _zeta_mul was considered at tier 3 (rc457) and DELIBERATELY DEFERRED:
# fusion_multiplicities composes on the private helper and needs no
# public spelling, and an honest promotion is not a one-line move — it
# drags in the ADR-0009 dispatch ruling against the existing C ring
# multiply srmech_riemann_theta_cyc_mul, a peer speaking a DIFFERENT
# wire (zeta-power-table reduction, deg <= 16, int64 fast path) under a
# foreign namespace, so the promotion rc must either ship a table-based
# wire adapter from phi_e (with the pure-bignum fallback recorded) or
# record an explicit projection gap.  Bundling that here would be the
# unexpected-coupling shape rc456 declined on the exact_dft refactor.
# Recorded in the rc457 CHANGELOG "deliberately deferred" section.
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
        "table_sha256"}`` — every field is load-bearing for tier 3
        (fusion multiplicities read ``class_algebra`` / ``inverse_class``;
        the Frobenius–Schur indicator reads ``square_class``).

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
#: of ``exponent`` and is deliberately not required).
_CHAR_TABLE_KEYS = (
    "table", "degrees", "class_sizes", "class_of", "inverse_class",
    "square_class", "class_algebra", "phi_e", "degree", "k", "order",
    "exponent", "representatives", "table_sha256",
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

    **The scope ruling this op's name carries (final).**  Two objects wear
    the name "isotypic projector": (a) the primitive central idempotents
    ``e_chi = (d/|G|) · Σ_g chi(g⁻¹)·g`` of ``Z(ℂ[G])`` — these need ONLY
    characters, and everything they need ships; (b) the projector onto an
    isotypic SUBSPACE of a caller's module, which needs the actual
    representation matrices ``rho(g)`` — and srmech has NO representation
    object (the ``physics.qm`` matrices are fixed Lie generators, not
    G → GL(V); the CD ``left_mult_matrix`` / ``right_mult_matrix`` are
    algebra regular representations, not group-element-keyed).  This op
    ships object (a) under the name of what it actually is.  The elements
    returned ARE the isotypic projectors of the REGULAR module; for any
    other module the caller evaluates ``rho(e_chi) = (d/|G|) ·
    Σ_g chi(g⁻¹)·rho(g)`` — the group-algebra element is universal, the
    matrix projector is its evaluation at a module srmech does not carry.
    Shipping (a) under the bare name "isotypic_projector" would be a
    silent wrong answer waiting for a caller with a module in hand.

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

    identity_columns = [
        j for j in range(k)
        if all(tuple(table[i][j]) == (degrees[i],) + (0,) * (deg - 1)
               for i in range(k))]
    if len(identity_columns) != 1:
        raise ValueError(
            f"central_idempotents: expected exactly ONE identity-class "
            f"column (every row equal to its degree vector); found "
            f"{len(identity_columns)} (identity-location law; a guard "
            f"that fires is evidence)")
    identity_class = identity_columns[0]

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
