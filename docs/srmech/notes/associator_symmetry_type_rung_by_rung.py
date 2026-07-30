#!/usr/bin/env python3
"""LANE 1 — the ASSOCIATOR's symmetry type, rung by rung (2026-07-29).

MEASURES, exactly, for dims 4 / 8 / 16 / 32 / 64: the symmetry type of the
associator ``[a,b,c] = (a·b)·c − a·(b·c)`` under the 6 permutations of a,b,c,
over ALL ordered triples of basis elements.

SUBJECT (shipped srmech ops, no hand-rolled algebra):
  - ``srmech.amsc.cascade.cayley_dickson.algebra_table(dim, gammas)``  — rc352
  - ``srmech.amsc.cascade.cayley_dickson.table_product(table, x, y)``  — rc352
  - ``srmech.amsc.cascade.cayley_dickson.cd_add`` / ``cd_basis``
  - ``srmech.amsc.format.sha256_bytes``  (Class A) — the deterministic byte
    source for the random-table controls; no ``random``, no seed drift.

The associator is assembled as a COMPOSITION of those ops:
    lhs = table_product(t, table_product(t, a, b), c)
    rhs = table_product(t, a, table_product(t, b, c))
    neg = table_product(t, MINUS_E0, rhs)        # Class-K sign flip, via the
                                                 # algebra's own −e₀ (identity
                                                 # is e₀ in every table here)
    assoc = cd_add(lhs, neg)
No ``abs()``, no float, no epsilon, no numpy, no stdlib ``fractions``.

FAST PATH: every table used here is MONOMIAL (e_i·e_j = ±e_k, one nonzero per
(i,j) cell), so the associator on BASIS triples is read off the table as an
exact integer sparse vector. The fast path is DIFFERENTIALLY VERIFIED against
the shipped ``table_product`` composition above — full sweep at dim 4/8, and a
sha256-drawn sample at dim 16/32/64. Any disagreement aborts.

CONTROLS (mandatory per
``[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]``):
  - every SPLIT γ-twist at each dim (``algebra_table(dim, gammas)``);
  - RAND-SIGN: the CD index lane (i⊕j) kept, the sign cocycle randomised;
  - RAND-FULL: index lane AND sign randomised.
Both random flavours are anticommutative (e_i·e_j = −e_j·e_i, i≠j≥1),
unital (e₀ = 1) and imaginary-square-negative (e_i² = −e₀, i≥1).

Run:  python3 associator_symmetry_type_rung_by_rung.py > <name>.ndjson
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    ALGEBRA_NAMES,
    CD_COMPOSE_MAX_DIM,
    DIVISION_ALGEBRA_DIMS,
    ASSOCIATIVE_ALGEBRA_DIMS,
    algebra_table,
    table_product,
    cd_add,
    cd_basis,
)
from srmech.amsc.format import sha256_bytes

# ── the 6 position-permutations of (a,b,c), with parity and MIDDLE slot ──
#    arrangement            parity   middle
PERMS = (
    ((0, 1, 2), +1, 1),   # (a,b,c)  even   middle = b
    ((1, 2, 0), +1, 2),   # (b,c,a)  even   middle = c
    ((2, 0, 1), +1, 0),   # (c,a,b)  even   middle = a
    ((0, 2, 1), -1, 2),   # (a,c,b)  odd    middle = c
    ((2, 1, 0), -1, 1),   # (c,b,a)  odd    middle = b
    ((1, 0, 2), -1, 0),   # (b,a,c)  odd    middle = a
)


# ──────────────────────────────────────────────────────────────────────
# Deterministic byte source — Class A (sha256_bytes), NOT `random`.
# ──────────────────────────────────────────────────────────────────────
class ClassAStream:
    """A deterministic integer stream from ``sha256_bytes`` (Class A)."""

    def __init__(self, label: str) -> None:
        self._label = label.encode("utf-8")
        self._n = 0
        self._buf = b""

    def _refill(self) -> None:
        # sha256_bytes returns the 64-char HEX digest (str); take its bytes.
        digest = sha256_bytes(self._label + b":" + str(self._n).encode())
        self._buf += bytes.fromhex(digest)
        self._n += 1

    def byte(self) -> int:
        if not self._buf:
            self._refill()
        b = self._buf[0]
        self._buf = self._buf[1:]
        return b

    def below(self, n: int) -> int:
        """Uniform-enough integer in [0, n) for n ≤ 256 (rejection sampling)."""
        assert 1 <= n <= 256
        lim = (256 // n) * n
        while True:
            v = self.byte()
            if v < lim:
                return v % n

    def sign(self) -> int:
        """A ±1 — the Class-K pin-slot draw. No abs()."""
        return 1 if (self.byte() & 1) == 0 else -1


# ──────────────────────────────────────────────────────────────────────
# Monomial extraction + the fast exact associator.
# ──────────────────────────────────────────────────────────────────────
def monomial_map(table):
    """``mono[i][j] = (k, s)`` for a MONOMIAL table (exactly one nonzero cell).

    Raises if the table is not monomial — the fast path is only licensed on a
    monomial table, and every table in this probe is monomial by construction.
    """
    dim = len(table)
    mono = [[None] * dim for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            nz = [(k, table[i][j][k]) for k in range(dim) if table[i][j][k] != 0]
            if len(nz) != 1:
                raise ValueError(
                    f"monomial_map: table[{i}][{j}] has {len(nz)} nonzeros; "
                    f"the fast path requires exactly 1")
            mono[i][j] = nz[0]
    return mono


def assoc_fast(mono, i, j, k):
    """[e_i, e_j, e_k] as a canonical sparse tuple ``((idx, coeff), …)``.

    Exact integers throughout. ``(e_i·e_j)·e_k`` and ``e_i·(e_j·e_k)`` are each
    a single signed basis element; the associator is their difference.
    """
    p, s1 = mono[i][j]
    q, s2 = mono[p][k]           # (ab)c = s1*s2 · e_q
    r, t1 = mono[j][k]
    u, t2 = mono[i][r]           # a(bc) = t1*t2 · e_u
    acc = {}
    acc[q] = acc.get(q, 0) + s1 * s2
    acc[u] = acc.get(u, 0) - t1 * t2
    return tuple(sorted((idx, c) for idx, c in acc.items() if c != 0))


def assoc_shipped(table, minus_e0, i, j, k):
    """[e_i, e_j, e_k] via the SHIPPED ops only — the differential oracle.

    ``table_product`` ∘ ``table_product`` ∘ ``cd_add``; the negation is a
    left-multiply by −e₀ (Class-K sign flip through the algebra's own unit).
    """
    dim = len(table)
    a, b, c = cd_basis(dim, i), cd_basis(dim, j), cd_basis(dim, k)
    lhs = table_product(table, table_product(table, a, b), c)
    rhs = table_product(table, a, table_product(table, b, c))
    neg = table_product(table, minus_e0, rhs)
    out = cd_add(lhs, neg)
    sparse = []
    for idx, v in enumerate(out):
        if v.numerator != 0:
            if v.denominator != 1:
                raise ValueError("basis associator must be integral")
            sparse.append((idx, v.numerator))
    return tuple(sparse)


def magnitude_class(sp):
    """The value UP TO SIGN — Class K (locate the pin at the first nonzero) ∘
    Class C (re-apply the orientation). Never ``abs()``."""
    if not sp:
        return ()
    lead = sp[0][1]
    if lead < 0:                       # Class C: re-orient, do not magnitude
        return tuple((idx, -c) for idx, c in sp)
    return sp


# ──────────────────────────────────────────────────────────────────────
# Control-table constructors (LABELLED controls, not shipped ops —
# see the FINDING on the missing random-anticommutative constructor).
# ──────────────────────────────────────────────────────────────────────
def rand_anticommutative_table(dim, label, keep_xor_lane):
    """A random ANTICOMMUTATIVE monomial table.

    e₀ = 1;  e_i² = −e₀ (i ≥ 1);  e_i·e_j = −e_j·e_i (i ≠ j ≥ 1).
    ``keep_xor_lane`` keeps the Cayley–Dickson index lane ``i⊕j`` and
    randomises ONLY the sign cocycle (RAND-SIGN); otherwise the target index is
    drawn too (RAND-FULL).
    """
    st = ClassAStream(f"{label}:dim{dim}:xor{int(keep_xor_lane)}")
    t = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        t[0][i][i] = 1
        t[i][0][i] = 1
    for i in range(1, dim):
        t[i][i][0] = -1
    for i in range(1, dim):
        for j in range(i + 1, dim):
            if keep_xor_lane:
                k = i ^ j
            else:
                k = st.below(dim)
            s = st.sign()
            t[i][j][k] = s
            t[j][i][k] = -s
    return t


# ──────────────────────────────────────────────────────────────────────
# The measurement.
# ──────────────────────────────────────────────────────────────────────
def measure(table, name, dim, verify_full, verify_sample):
    """Full ordered-triple sweep. Returns one NDJSON-ready record."""
    mono = monomial_map(table)
    minus_e0 = tuple([-1] + [0] * (dim - 1))

    # ── DIFFERENTIAL: the fast path vs the SHIPPED table_product composition ──
    checked = 0
    if verify_full:
        for i, j, k in itertools.product(range(dim), repeat=3):
            if assoc_fast(mono, i, j, k) != assoc_shipped(table, minus_e0, i, j, k):
                raise AssertionError(f"{name}: fast/shipped disagree at {i},{j},{k}")
            checked += 1
    else:
        st = ClassAStream(f"verify:{name}:{dim}")
        for _ in range(verify_sample):
            i, j, k = st.below(dim), st.below(dim), st.below(dim)
            if assoc_fast(mono, i, j, k) != assoc_shipped(table, minus_e0, i, j, k):
                raise AssertionError(f"{name}: fast/shipped disagree at {i},{j},{k}")
            checked += 1

    n_alt = n_sym = n_neither = 0          # ordered-triple counts
    n_zero = n_alt_nonzero = 0
    hist_values = {}                       # #distinct values → ordered count
    hist_mag = {}                          # #distinct magnitude classes → count
    n_middle_observable = 0                # ordered triples where the MIDDLE
    n_middle_group_split = 0               # ... group is itself sign-incoherent
    first_middle_witness = None
    first_neither_witness = None
    max_distinct = 0

    for base in itertools.combinations_with_replacement(range(dim), 3):
        vals = []
        for perm, parity, mid in PERMS:
            tri = (base[perm[0]], base[perm[1]], base[perm[2]])
            vals.append((assoc_fast(mono, *tri), parity, mid, tri))
        orbit = len(set(itertools.permutations(base)))   # ordered multiplicity

        ident = vals[0][0]
        alternating = all(
            v == (ident if p == 1 else
                  tuple((idx, -c) for idx, c in ident))
            for v, p, _m, _t in vals)
        symmetric = all(v == ident for v, _p, _m, _t in vals)

        distinct_values = {v for v, _p, _m, _t in vals}
        distinct_mag = {magnitude_class(v) for v, _p, _m, _t in vals}
        nd = len(distinct_values)
        nm = len(distinct_mag)
        max_distinct = max(max_distinct, nd)

        # per-MIDDLE-slot magnitude classes
        by_mid = {}
        for v, _p, m, _t in vals:
            by_mid.setdefault(m, set()).add(magnitude_class(v))
        mid_split = any(len(s) > 1 for s in by_mid.values())
        mid_classes = {next(iter(s)) for s in by_mid.values() if len(s) == 1}
        middle_observable = mid_split or len(mid_classes) > 1

        if alternating:
            n_alt += orbit
            if ident == ():
                n_zero += orbit
            else:
                n_alt_nonzero += orbit
        if symmetric and not alternating:
            n_sym += orbit
        if not alternating and not symmetric:
            n_neither += orbit
            if first_neither_witness is None:
                first_neither_witness = {
                    "triple": list(base),
                    "values": [[list(map(list, v)), p, m] for v, p, m, _t in vals],
                }
        hist_values[nd] = hist_values.get(nd, 0) + orbit
        hist_mag[nm] = hist_mag.get(nm, 0) + orbit
        if middle_observable:
            n_middle_observable += orbit
            if first_middle_witness is None:
                first_middle_witness = {
                    "triple": list(base),
                    "per_middle": {
                        str(m): sorted([list(map(list, x)) for x in s])
                        for m, s in by_mid.items()},
                }
        if mid_split:
            n_middle_group_split += orbit

    total = dim ** 3
    assert n_alt + n_sym + n_neither == total, "class partition must be exact"
    return {
        "record": "associator_symmetry_type",
        "algebra": name,
        "dim": dim,
        "algebra_name": ALGEBRA_NAMES.get(dim),
        "ordered_triples": total,
        "differential_checks_fast_vs_table_product": checked,
        "differential_disagreements": 0,
        "alternating": n_alt,
        "alternating_identically_zero": n_zero,
        "alternating_nonzero": n_alt_nonzero,
        "symmetric_not_alternating": n_sym,
        "neither": n_neither,
        "distinct_value_histogram": {str(k): v for k, v in sorted(hist_values.items())},
        "distinct_magnitude_histogram": {str(k): v for k, v in sorted(hist_mag.items())},
        "max_distinct_values_over_6_perms": max_distinct,
        "middle_observable_ordered_triples": n_middle_observable,
        "middle_group_sign_incoherent_ordered_triples": n_middle_group_split,
        "first_middle_witness": first_middle_witness,
        "first_neither_witness": first_neither_witness,
    }


def emit(rec, out):
    out.append(rec)
    print(json.dumps(rec, separators=(",", ":"), sort_keys=True), flush=True)


def main() -> int:
    out = []
    dims = [4, 8, 16, 32]
    if "--with64" in sys.argv:
        dims.append(64)

    for dim in dims:
        full = dim <= 8
        # the shipped-op differential is O(dim³) per call; sample-size shrinks
        # with dim so the ORACLE stays affordable without shrinking the SWEEP
        # (the sweep itself is always exhaustive over all dim³ ordered triples).
        nsamp = {16: 120, 32: 40, 64: 12}.get(dim, 0)
        # ── SUBJECT: the definite Cayley–Dickson ladder ──
        emit(measure(algebra_table(dim), "CD-definite", dim, full, nsamp * 3), out)
        # ── CONTROL 1: every SPLIT γ-twist at this dim (capped at 8 draws) ──
        n_lv = dim.bit_length() - 1
        twists = [g for g in itertools.product((-1, 1), repeat=n_lv)
                  if not all(v == -1 for v in g)]
        if len(twists) > 7:
            # keep the single-rung splits (the canonical split algebras) plus
            # the all-+1 extreme — enough to cover every rung independently.
            twists = [g for g in twists if sum(1 for v in g if v == 1) == 1] + \
                     [tuple([1] * n_lv)]
        for g in twists:
            emit(measure(algebra_table(dim, list(g)),
                         "CD-split-gammas" + "".join(
                             "+" if v == 1 else "-" for v in g),
                         dim, full, nsamp), out)
        # ── CONTROL 2/3: random anticommutative tables ──
        for lab in ("A", "B", "C"):
            emit(measure(
                rand_anticommutative_table(dim, "randsign" + lab, True),
                f"RAND-SIGN-{lab}", dim, full, nsamp), out)
            emit(measure(
                rand_anticommutative_table(dim, "randfull" + lab, False),
                f"RAND-FULL-{lab}", dim, full, nsamp), out)

    # ── the ceiling cross-check, as its own record ──
    firsts = {}
    for rec in out:
        if rec["algebra"] == "CD-definite":
            firsts[rec["dim"]] = rec["max_distinct_values_over_6_perms"]
    first_obs = min((d for d, m in sorted(firsts.items()) if m > 2), default=None)
    print(json.dumps({
        "record": "ceiling_cross_check",
        "CD_COMPOSE_MAX_DIM": CD_COMPOSE_MAX_DIM,
        "DIVISION_ALGEBRA_DIMS": list(DIVISION_ALGEBRA_DIMS),
        "ASSOCIATIVE_ALGEBRA_DIMS": list(ASSOCIATIVE_ALGEBRA_DIMS),
        "max_distinct_values_by_dim": {str(k): v for k, v in sorted(firsts.items())},
        "first_dim_with_more_than_2_distinct_values": first_obs,
        "coincides_with_first_dim_above_compose_ceiling":
            first_obs == 2 * CD_COMPOSE_MAX_DIM,
    }, separators=(",", ":"), sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
