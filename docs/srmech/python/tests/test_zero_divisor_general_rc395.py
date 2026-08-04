"""rc395 (`#T1000`) — the DIM-GENERAL zero-divisor witness ops.

``cd_zero_divisor_witness(dim)`` / ``cd_zero_divisor_witnesses(dim)`` REPLACE the
removed hardwired ``sedenion_zero_divisor_witness()`` (a dim-16-only c_dispatched
op). Both are now ``composition_of_c`` over the C-dispatched
``srmech.math.modular_linalg.gf_rref`` (the GF(2) support solve) + the C-dispatched
``cayley_dickson.cd_basis_product`` (the sign cocycle) — no dedicated C symbol,
which is why removing ``srmech_cd_zero_divisor_witness`` bumped the C ABI 10 -> 11.

WHAT THIS PINS
==============
1. The COMPLETE basis-pair set at dim 16 is exactly the rc350 GF(2) set — 168
   witnesses, containing the pinned ``(1, 10, 4, 15, -1)``.
2. CO-EQUAL DUAL CONSTRUCTION (the consistency oracle,
   `[[user_stance_co_equal_dual_construction_is_a_consistency_oracle]]`): the
   shipped op's witness SET equals an INDEPENDENT recompute driven straight
   through the raw C symbols ``srmech_gf_rref`` + ``srmech_cd_basis_product`` at
   dim 16 AND dim 32, and the pure path equals the native path. A set MISMATCH
   is the finding — it is asserted, never papered over.
3. CONTINUITY: ``cd_zero_divisor_witness(16)`` is the exact dim-16 payload the
   removed sedenion op returned (``e1 + e10`` / ``e4 − e15``) — the answer is
   unchanged, only the name and the generality moved.
4. NEGATIVE CONTROLS: empty at dim 4 and dim 8 (ℍ / 𝕆 are division algebras).
5. NO FALSE NEGATIVE: exact brute-force products on a deterministic ``(i, j)``
   subset reproduce the criterion's answer restricted to that subset.

Numpy-free; the C-path assertions are native-guarded via
``tests._native_gate.require_native`` (`#T843`: a parity claim with no native
behind it is a failure, not a quiet pass).
"""
from __future__ import annotations

import ctypes

import pytest

from srmech import _native
from srmech.math import modular_linalg as ml
from srmech.cascade import (
    cd_basis_product,
    cd_mult,
    cd_zero_divisor_witness,
    cd_zero_divisor_witnesses,
)
from tests._native_gate import require_native

PINNED = (1, 10, 4, 15, -1)          # x = e1 + e10, y = e4 − e15, the first witness


def _force(has_native: bool, fn, *args):
    """Run ``fn(*args)`` with ``_native.HAS_NATIVE`` pinned, then restore."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args)
    finally:
        _native.HAS_NATIVE = saved


# ── the INDEPENDENT direct-C recompute (the other half of the oracle) ────────

def _support_solutions_via_c(d: int, n_bits: int):
    """All ``(k, l)`` with ``k ⊕ l = d``, solved through the RAW native GF(2)
    RREF ``srmech_gf_rref`` (via ``ml._gf_rref_c``) — not the shipped op."""
    n_unk = 2 * n_bits
    rows = []
    for b in range(n_bits):
        row = [0] * (n_unk + 1)
        row[b] = 1
        row[n_bits + b] = 1
        row[n_unk] = (d >> b) & 1
        rows.append(row)
    flat = [v for r in rows for v in r]
    res = ml._gf_rref_c(flat, n_bits, n_unk + 1, 2)
    assert res is not None, "native srmech_gf_rref refused a GF(2) support system"
    rref_flat, pivots, _rank = res
    ncols = n_unk + 1
    rref = [rref_flat[r * ncols:(r + 1) * ncols] for r in range(n_bits)]
    free = [c for c in range(n_unk) if c not in pivots]
    sols = []
    for mask in range(1 << len(free)):
        x = [0] * n_unk
        for t, c in enumerate(free):
            x[c] = (mask >> t) & 1
        for ri, pc in enumerate(pivots):
            acc = rref[ri][n_unk]
            for c in free:
                acc ^= rref[ri][c] & x[c]
            x[pc] = acc
        k = sum(bit << b for b, bit in enumerate(x[:n_bits]))
        l = sum(bit << b for b, bit in enumerate(x[n_bits:]))
        sols.append((k, l))
    return sols


def _sign_via_c(dim: int, a: int, b: int) -> int:
    """The cocycle sign σ(a, b) straight from ``srmech_cd_basis_product``."""
    oidx = ctypes.c_int()
    osign = ctypes.c_int()
    rc = _native.LIB.srmech_cd_basis_product(
        int(dim), int(a), int(b), ctypes.byref(oidx), ctypes.byref(osign))
    assert rc == _native.SRMECH_OK, rc
    return int(osign.value)


def _witnesses_via_c(dim: int):
    """The complete basis-pair witness SET recomputed ENTIRELY through the raw C
    symbols — an independent construction of what the shipped op returns."""
    n_bits = dim.bit_length() - 1
    out = set()
    for i in range(1, dim):
        for j in range(i + 1, dim):
            for (k, l) in _support_solutions_via_c(i ^ j, n_bits):
                if k == 0 or l == 0 or k >= l:
                    continue
                s = -_sign_via_c(dim, i, k) * _sign_via_c(dim, j, l)
                if s * _sign_via_c(dim, i, l) + _sign_via_c(dim, j, k) == 0:
                    out.add((i, j, k, l, s))
    return out


# ── 1. the complete set at dim 16 ────────────────────────────────────────────

def test_complete_set_at_16_is_the_168_gf2_witnesses():
    ws = cd_zero_divisor_witnesses(16)
    assert len(ws) == 168
    assert len(set(ws)) == 168, "the enumeration emitted a duplicate"
    assert PINNED in set(ws)
    assert ws[0] == PINNED, "deterministic order: [0] must be the first witness"
    assert all(len(w) == 5 for w in ws)


def test_set_equals_rc350_independent_gf2_criterion():
    """The rc350 test file carries its OWN GF(2) construction. The shipped op's
    set must equal it exactly."""
    from test_gf2_modular_linalg_rc350 import _zero_divisor_witnesses_via_gf2
    rc350_set, n_candidates = _zero_divisor_witnesses_via_gf2(16)
    assert n_candidates == 735
    assert set(cd_zero_divisor_witnesses(16)) == set(rc350_set)


# ── 2. the CO-EQUAL DUAL CONSTRUCTION consistency oracle ─────────────────────

@pytest.mark.parametrize("dim", [16, 32])
def test_op_set_equals_independent_composed_c_recompute(dim):
    """The shipped op's witness SET == an independent recompute driven straight
    through ``srmech_gf_rref`` + ``srmech_cd_basis_product``. A mismatch is the
    finding (co-equal dual construction certifies mutual realizability)."""
    require_native(f"cd_zero_divisor_witnesses composed-C recompute at dim {dim}")
    op_set = set(cd_zero_divisor_witnesses(dim))
    c_set = _witnesses_via_c(dim)
    assert op_set == c_set, (
        f"dim {dim}: op vs direct-C recompute disagree — "
        f"only-op {sorted(op_set - c_set)[:6]}, only-C {sorted(c_set - op_set)[:6]}")


@pytest.mark.parametrize("dim", [16, 32])
def test_pure_path_equals_native_path(dim):
    """Pure Python == native dispatch, order-identical (the two projections of
    the same composition_of_c op are consistent)."""
    require_native(f"cd_zero_divisor_witnesses pure-vs-native at dim {dim}")
    pure = _force(False, cd_zero_divisor_witnesses, dim)
    nat = _force(True, cd_zero_divisor_witnesses, dim)
    assert pure == nat


def test_shape_check_at_64():
    """Shape only at dim 64 (the full recompute is reserved for 16/32): a
    non-empty set of 5-tuples, deterministically first."""
    ws = cd_zero_divisor_witnesses(64)
    assert len(ws) > 0
    assert all(len(w) == 5 for w in ws)
    assert ws == sorted(ws, key=lambda w: (w[0], w[1], w[2], w[3]))


# ── 3. continuity with the removed dim-16 op ─────────────────────────────────

def test_witness_16_is_the_removed_sedenion_op_answer():
    """CONTINUITY (`#T1000` item 7). ``cd_zero_divisor_witness(16)`` returns the
    exact payload the removed ``sedenion_zero_divisor_witness()`` returned: the
    dim-16 answer is unchanged, only the name and the generality moved."""
    w = cd_zero_divisor_witness(16)
    assert w["dim"] == 16
    assert w["x_form"] == "e1 + e10"
    assert w["y_form"] == "e4 - e15"
    assert w["x_norm_sq"] == 2 and w["y_norm_sq"] == 2
    assert w["product_is_zero"] is True
    assert all(c == 0 for c in w["product"])
    assert all(c == 0 for c in cd_mult(w["x"], w["y"]))
    # the singular is exactly the [0] of the plural enumeration
    first = cd_zero_divisor_witnesses(16)[0]
    assert first == PINNED
    assert w["x_form"] == f"e{first[0]} + e{first[1]}"


# ── 4. negative controls — the division algebras ─────────────────────────────

@pytest.mark.parametrize("dim", [4, 8])
def test_division_algebras_have_no_basis_pair_witness(dim):
    assert cd_zero_divisor_witnesses(dim) == []
    assert cd_zero_divisor_witness(dim) is None


# ── 5. no false NEGATIVE — exact brute force on a subset ─────────────────────

def test_no_false_negative_against_brute_force_subset():
    """Brute force over a deterministic ``(i, j)`` subset — every ``(k, l, s)``
    tested with the shipped ``cd_mult`` — must equal the op's set restricted to
    that subset (no false negatives AND no false positives). Same pattern as
    ``test_gf2_modular_linalg_rc350.py``'s brute-force oracle."""
    dim = 16
    subset = [(1, 10), (2, 5), (3, 12), (6, 9), (7, 14), (11, 13)]
    op_subset = {w for w in cd_zero_divisor_witnesses(dim)
                 if (w[0], w[1]) in subset}
    brute = set()
    for (i, j) in subset:
        x = [0] * dim
        x[i] += 1
        x[j] += 1
        for k in range(1, dim):
            for l in range(k + 1, dim):
                for s in (1, -1):
                    y = [0] * dim
                    y[k] += 1
                    y[l] += s
                    if all(c == 0 for c in cd_mult(x, y)):
                        brute.add((i, j, k, l, s))
    assert brute == op_subset
    assert len(brute) > 0, "the subset must actually contain witnesses"


# ── 6. the enumeration really uses the shipped C leaves ──────────────────────

def test_op_composes_the_shipped_gf_rref_and_cd_basis_product():
    """It is a composition_of_c: the sign criterion reads exactly the shipped
    cd_basis_product cocycle. Spot-check the determined sign of the pinned
    witness against cd_basis_product directly."""
    i, j, k, l, s = PINNED
    _, s_ik = cd_basis_product(16, i, k)
    _, s_jl = cd_basis_product(16, j, l)
    _, s_il = cd_basis_product(16, i, l)
    _, s_jk = cd_basis_product(16, j, k)
    assert s == -s_ik * s_jl                  # DETERMINED, not searched
    assert s * s_il + s_jk == 0               # second pair also cancels
