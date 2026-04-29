"""Unit tests for chess_spectral.qm_4d_dynamics — Phase 4 milestone B1.

Covers the A_1 channel move-as-unitary lift (the simplest of the five
strict-unitary-tier channels per ADR-003 §3.1):

  1. Sub-unitarity within the A_1 subspace: ``U_a1.conj().T @ U_a1
     == P_A1`` for the projector-sandwich construction. Holds at
     machine precision when the underlying swap commutes with P_A1
     (i.e., for moves whose endpoints lie in the same B_4 orbit).
     Cross-orbit moves are documented as a B1 finding and exercised
     via xfail (see TestSubUnitarityCrossOrbit).
  2. Channel evolution matches direct re-encoding for same-orbit
     non-capture moves. (ADR-003 §3.1 verification claim.)
  3. ADR-001 phase formula sanity (A_1 phase ≡ 1.0 always).
  4. ADR-003 strict-unitary tier sparsity pattern.
  5. ADR-004 §3.4 amendment compliance: ``U_a1`` is NOT required to
     anti-commute with J_op (the Phase 3.5 Probe-4 amendment moved the
     Z_2 sector flip to ``state_to_psi``'s sign multiplier).
  6. Capture-move ``NotImplementedError`` (B5 deferral).

Phase 3.5 Probe-Result Amendments hard-coded into the spec:

  * ADR-001 §3.1 — A_1 phase = 0; phase factor = 1.0.
  * ADR-003 §3.1 — strict-unitary path uses the projector-sandwich
    ``U_a1 = P_A1 @ swap @ P_A1`` (not the bare swap on C^4096). The
    sandwich form is sub-unitary on ``range(P_A1)``; the bare swap is
    unitary on the full 4096-dim space but does not preserve
    ``range(P_A1)``.
  * ADR-004 §3.4 — sector-flip-via-state_to_psi (Probe-4 amendment).
    Operator-level anti-commutation ``{U_move, J_op} = 0`` is **not**
    required.

Findings discovered during B1 implementation
--------------------------------------------

The projector-sandwich ``U_a1 = P_A1 @ swap @ P_A1`` is **sub-unitary
on range(P_A1) iff the underlying swap commutes with P_A1**. This
holds exactly when ``sq_from`` and ``sq_to`` lie in the same B_4
orbit (35 orbits on the 4096-square lattice, sizes
{16, 64, 96, 192, 384}). For typical chess moves (cross-orbit), the
sub-unitarity gap (``||U_a1.conj().T @ U_a1 - P_A1||_F``) is
non-trivial — sample values are ~1e-2 to ~3e-1, NOT 1e-10.

This is a B1-level finding for ADR-003 §3.1, where "Pi_0 is the swap
operator" is sketched without the projector sandwich. The two
candidate fixes are:

  (a) restrict the strict-unitary claim to same-orbit moves and ship
      cross-orbit as a measurement-only re-encode (analogous to the
      FIB_SYM Phase-3.5 amendment), or
  (b) redesign the lift to use the orbit-quotient picture
      (range(P_A1) is naturally 35-dimensional; on this quotient a
      move induces a deterministic but non-unitary translation
      m_a -> m_a - v/n_a, m_b -> m_b + v/n_b — a partial isometry
      with explicit norm loss).

The current B1 ships the projector-sandwich and documents this
finding here; ADR-003 §3.1 needs an amendment in v1.5 to either
restrict scope or refactor.

Run with ``pytest tests/test_qm_4d_dynamics_b1.py -v`` from python/.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Tuple

import numpy as np
import pytest
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import encoder_4d as _enc4    # noqa: E402
from chess_spectral import qm_4d                  # noqa: E402
from chess_spectral import qm_4d_dynamics as dyn  # noqa: E402
from chess_spectral import tables_4d as _t4       # noqa: E402


# ---- Frobenius helper ----------------------------------------------


def _frob(M: sp.spmatrix | np.ndarray) -> float:
    """Frobenius norm. Works on both sparse and dense matrices."""
    if sp.issparse(M):
        # scipy.sparse.linalg.norm with no parameters defaults to
        # Frobenius and avoids a full toarray().
        return float(sp.linalg.norm(M))
    return float(np.linalg.norm(np.asarray(M)))


# ---- Orbit partition (cached at module level) -----------------------

@pytest.fixture(scope='module')
def orbit_partition() -> Tuple[List[int], List[int]]:
    """Compute the 35-orbit B_4 partition of the 4096 squares.

    Returns
    -------
    orbit_id_of_sq : list[int] of length 4096
        Orbit index for each square (0..34).
    orbit_sizes : list[int] of length 35
        Size of each orbit.
    """
    closure = _t4.b4_closure()
    orbit_id_of_sq = [-1] * _t4.N_SQUARES
    orbit_sizes: List[int] = []
    for s in range(_t4.N_SQUARES):
        if orbit_id_of_sq[s] >= 0:
            continue
        x, y, z, w = _t4.rc4(s)
        orb = set()
        for g in closure:
            x2, y2, z2, w2 = _t4._apply_b4_to_square(g, x, y, z, w)
            orb.add(_t4.sq4(x2, y2, z2, w2))
        oid = len(orbit_sizes)
        orbit_sizes.append(len(orb))
        for t in orb:
            orbit_id_of_sq[t] = oid
    return orbit_id_of_sq, orbit_sizes


# ---- Position fixtures ----------------------------------------------


@pytest.fixture(scope='module')
def imbalanced_position():
    """A position with non-zero A_1 channel (asymmetric color
    distribution; the seeded-walker positions have antipodal piece
    pairs that make the A_1 orbit-mean trivially zero).

    Returns the position dict in linear-square form.
    """
    coords = {
        (0, 0, 0, 0): 'K', (5, 5, 5, 5): 'k',
        (1, 2, 3, 4): 'Q',
        (3, 1, 2, 3): 'B',
        (2, 5, 0, 1): 'N',
        (4, 3, 1, 2): 'R',
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


@pytest.fixture(scope='module')
def imbalanced_position_b():
    """Second imbalanced position to vary the test sample. Different
    occupancy pattern + different occupied B_4 orbits."""
    coords = {
        (3, 3, 3, 3): 'K', (4, 4, 4, 4): 'k',
        (0, 1, 2, 3): 'Q', (7, 6, 5, 4): 'N',
        (5, 2, 0, 6): 'B', (1, 6, 7, 0): 'R',
        (2, 0, 4, 1): 'B',
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


def _gen_same_orbit_pairs(orbit_id_of_sq, orbit_sizes,
                           position_keys, *, n_pairs: int,
                           rng: np.random.Generator,
                           ) -> List[Tuple[int, int]]:
    """Generate non-capture (from, to) pairs where from and to lie
    in the same B_4 orbit and to is empty in the position."""
    occupied = set(position_keys)
    # Bucket orbit elements
    orbit_members: List[List[int]] = [[] for _ in orbit_sizes]
    for s, oid in enumerate(orbit_id_of_sq):
        orbit_members[oid].append(s)
    pairs: List[Tuple[int, int]] = []
    # Strategy: pick an occupied square, find an empty same-orbit target.
    occ_list = sorted(occupied)
    # Bound the loop iterations: at most 4 * n_pairs candidate from-squares.
    max_attempts = max(64, 4 * n_pairs)
    attempts = 0
    while len(pairs) < n_pairs and attempts < max_attempts:
        attempts += 1
        s = int(rng.choice(occ_list))
        oid = orbit_id_of_sq[s]
        candidates = [t for t in orbit_members[oid]
                      if t != s and t not in occupied]
        if not candidates:
            continue
        t = int(rng.choice(candidates))
        if (s, t) in pairs:
            continue
        pairs.append((s, t))
    return pairs


def _gen_cross_orbit_pairs(orbit_id_of_sq, position_keys, *,
                            n_pairs: int,
                            rng: np.random.Generator,
                            ) -> List[Tuple[int, int]]:
    """Generate non-capture (from, to) pairs where from and to lie
    in DIFFERENT B_4 orbits."""
    occupied = set(position_keys)
    occ_list = sorted(occupied)
    pairs: List[Tuple[int, int]] = []
    max_attempts = max(64, 4 * n_pairs)
    attempts = 0
    while len(pairs) < n_pairs and attempts < max_attempts:
        attempts += 1
        s = int(rng.choice(occ_list))
        t = int(rng.integers(0, _t4.N_SQUARES))
        if t in occupied:
            continue
        if orbit_id_of_sq[s] == orbit_id_of_sq[t]:
            continue
        if (s, t) in pairs:
            continue
        pairs.append((s, t))
    return pairs


# ====================================================================
#  Test 1: Sub-unitarity within A_1 subspace
# ====================================================================
#
# The user-spec says U_a1.conj().T @ U_a1 == P_A1 within 1e-10. This
# holds at machine precision iff the underlying swap commutes with
# P_A1, which in turn holds iff the swap endpoints share a B_4 orbit.
#
# Test 1a (passes strictly): exercise 50 SAME-orbit non-capture moves
# and assert sub-unitarity at 1e-10.
#
# Test 1b (xfail; Phase 3.5-style finding): same construction on
# CROSS-orbit moves, where the sub-unitarity claim does NOT hold. The
# xfail marker keeps the suite green while flagging the discovery —
# if a later refactor makes cross-orbit work, the test "unexpectedly
# passes" and pytest XPASSES, which the developer must acknowledge.

def test_b1_subunitarity_same_orbit_50(
    orbit_partition, imbalanced_position, imbalanced_position_b,
):
    """Sub-unitarity of U_a1 holds exactly for same-orbit
    non-capture swaps (50 sampled pairs across two positions).

    For each pair: build U_a1; compute residual =
    ||U_a1^dagger @ U_a1 - P_A1||_F; assert below 1e-10.
    """
    orbit_id_of_sq, orbit_sizes = orbit_partition
    P_A1 = dyn._get_P_A1()
    rng = np.random.default_rng(0xB1_AAA_5A)

    # Build a 50-sample mix from the two positions (25 each).
    pos_a = imbalanced_position
    pos_b = imbalanced_position_b
    pairs_a = _gen_same_orbit_pairs(
        orbit_id_of_sq, orbit_sizes, list(pos_a.keys()),
        n_pairs=25, rng=rng,
    )
    pairs_b = _gen_same_orbit_pairs(
        orbit_id_of_sq, orbit_sizes, list(pos_b.keys()),
        n_pairs=25, rng=rng,
    )
    cases = [(pos_a, p) for p in pairs_a] + [(pos_b, p) for p in pairs_b]
    assert len(cases) >= 30, (
        f"only {len(cases)} same-orbit cases generated; expected >= 30 "
        "(if the fixtures changed and same-orbit empty squares became "
        "scarce, broaden the position fixtures)"
    )

    residuals: List[float] = []
    for (pos, (s, t)) in cases:
        U = dyn.u_move_a1(pos, (s, t))
        prod = U.conj().T @ U
        diff = prod - P_A1
        diff.eliminate_zeros()
        r = _frob(diff)
        residuals.append(r)
        assert r < 1e-10, (
            f"sub-unitarity residual {r:.3e} > 1e-10 for same-orbit "
            f"swap ({s}, {t}); orbits "
            f"({orbit_id_of_sq[s]}, {orbit_id_of_sq[t]})"
        )

    # Sanity: the worst case should still be modest.
    assert max(residuals) < 1e-10, (
        f"worst same-orbit residual = {max(residuals):.3e}"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "B1 finding: U_a1.conj().T @ U_a1 == P_A1 does NOT hold for "
        "cross-orbit swaps. The projector-sandwich is sub-unitary on "
        "range(P_A1) only when the swap commutes with P_A1, which in "
        "turn requires sq_from and sq_to to lie in the same B_4 orbit. "
        "ADR-003 §3.1 needs a v1.5 amendment to either restrict the "
        "strict-unitary claim to same-orbit moves or refactor the "
        "lift."
    ),
)
def test_b1_subunitarity_cross_orbit_xfail(
    orbit_partition, imbalanced_position,
):
    """Cross-orbit sub-unitarity (EXPECTED FAIL).

    Documents the B1 finding that for cross-orbit non-capture
    moves the sub-unitarity claim fails by 1e-2 to 1e-1 in
    Frobenius norm. Marked xfail-strict so an unexpected pass would
    surface (e.g., if the lift is later redesigned).
    """
    orbit_id_of_sq, _ = orbit_partition
    P_A1 = dyn._get_P_A1()
    rng = np.random.default_rng(0xB1_BBB_5A)
    pairs = _gen_cross_orbit_pairs(
        orbit_id_of_sq, list(imbalanced_position.keys()),
        n_pairs=25, rng=rng,
    )
    assert len(pairs) >= 5
    for (s, t) in pairs:
        U = dyn.u_move_a1(imbalanced_position, (s, t))
        prod = U.conj().T @ U
        diff = prod - P_A1
        diff.eliminate_zeros()
        # The strict-unitary form fails here — by xfail we declare it
        # so. We assert tightly (< 1e-10) and rely on xfail to convert
        # the natural failure into a green "expected fail" pytest
        # outcome.
        assert _frob(diff) < 1e-10


# ====================================================================
#  Test 2: A_1 channel evolution matches direct re-encoding
# ====================================================================
#
# For non-capture, same-orbit moves, the equation
#   U_a1 @ ((P_A1 @ sig_pre) / N_pre) ==
#       (P_A1 @ sig_post) / N_post
# holds because:
#   - swap @ sig_pre == sig_post  (swap permutation matches the
#     non-capture move)
#   - swap @ P_A1 == P_A1 @ swap  (swap commutes with P_A1 on
#     same-orbit endpoints, so (P_A1 @ swap @ P_A1) @ sig_pre =
#     P_A1 @ swap @ sig_pre = P_A1 @ sig_post)
#   - the normalization factor cancels at machine precision when
#     the move stays inside the A_1 subspace's contribution to the
#     full encoder norm.
#
# As above, cross-orbit moves are xfail.

def test_b1_re_encoding_match_same_orbit(
    orbit_partition, imbalanced_position, imbalanced_position_b,
):
    """For same-orbit non-capture moves, U_a1 @ psi_pre[A_1] equals
    psi_post[A_1] within 1e-10."""
    orbit_id_of_sq, orbit_sizes = orbit_partition
    rng = np.random.default_rng(0xB1_222_5A)
    pos_a = imbalanced_position
    pos_b = imbalanced_position_b
    pairs_a = _gen_same_orbit_pairs(
        orbit_id_of_sq, orbit_sizes, list(pos_a.keys()),
        n_pairs=20, rng=rng,
    )
    pairs_b = _gen_same_orbit_pairs(
        orbit_id_of_sq, orbit_sizes, list(pos_b.keys()),
        n_pairs=20, rng=rng,
    )
    cases = [(pos_a, p) for p in pairs_a] + [(pos_b, p) for p in pairs_b]
    assert len(cases) >= 20

    n_passed = 0
    for (pos, (s, t)) in cases:
        # Apply the move classically.
        post = dict(pos)
        piece = post.pop(s)
        post[t] = piece

        # Encode pre and post.
        enc_pre = _enc4.encode_4d(pos).astype(np.complex128)
        enc_post = _enc4.encode_4d(post).astype(np.complex128)
        n_pre = float(np.linalg.norm(enc_pre))
        n_post = float(np.linalg.norm(enc_post))
        # Skip degenerate (zero) cases — should not happen for
        # imbalanced fixtures, but guard.
        if n_pre == 0.0 or n_post == 0.0:
            continue

        # Extract A_1 block (channel 0; first 4096 entries).
        psi_a1_pre = enc_pre[:dyn.CHANNEL_DIM] / n_pre
        psi_a1_post = enc_post[:dyn.CHANNEL_DIM] / n_post

        # Apply the unitary lift.
        U = dyn.u_move_a1(pos, (s, t))
        psi_a1_via = U @ psi_a1_pre

        diff = float(np.linalg.norm(psi_a1_via - psi_a1_post))
        assert diff < 1e-10, (
            f"A_1 evolution mismatch for same-orbit ({s}, {t}): "
            f"diff = {diff:.3e}; orbits "
            f"({orbit_id_of_sq[s]}, {orbit_id_of_sq[t]})"
        )
        n_passed += 1

    assert n_passed >= 10, (
        f"only {n_passed} non-degenerate same-orbit cases passed; "
        f"expected >= 10. Adjust fixtures or selection."
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "B1 finding: A_1 evolution does NOT match direct re-encoding "
        "for cross-orbit non-capture moves. swap @ P_A1 != P_A1 @ swap "
        "on cross-orbit endpoints, so P_A1 @ swap @ P_A1 @ sig_pre "
        "differs from P_A1 @ sig_post. ADR-003 §3.1's verification "
        "claim is correct only for same-orbit moves."
    ),
)
def test_b1_re_encoding_match_cross_orbit_xfail(
    orbit_partition, imbalanced_position,
):
    """Cross-orbit re-encoding match (EXPECTED FAIL)."""
    orbit_id_of_sq, _ = orbit_partition
    rng = np.random.default_rng(0xB1_222_BB)
    pairs = _gen_cross_orbit_pairs(
        orbit_id_of_sq, list(imbalanced_position.keys()),
        n_pairs=10, rng=rng,
    )
    assert len(pairs) >= 5

    pos = imbalanced_position
    for (s, t) in pairs:
        post = dict(pos)
        piece = post.pop(s)
        post[t] = piece
        enc_pre = _enc4.encode_4d(pos).astype(np.complex128)
        enc_post = _enc4.encode_4d(post).astype(np.complex128)
        n_pre = float(np.linalg.norm(enc_pre))
        n_post = float(np.linalg.norm(enc_post))
        if n_pre == 0 or n_post == 0:
            continue
        psi_a1_pre = enc_pre[:dyn.CHANNEL_DIM] / n_pre
        psi_a1_post = enc_post[:dyn.CHANNEL_DIM] / n_post
        U = dyn.u_move_a1(pos, (s, t))
        psi_a1_via = U @ psi_a1_pre
        diff = float(np.linalg.norm(psi_a1_via - psi_a1_post))
        assert diff < 1e-10


# ====================================================================
#  Test 3: ADR-001 phase formula sanity (A_1 phase ≡ 1.0)
# ====================================================================

def test_b1_adr001_phase_a1_is_unity_per_move(imbalanced_position):
    """For two distinct non-capture moves on the same starting
    state, the phase factor applied to the A_1 channel is identically
    1.0+0j (per ADR-001 §3.1 row "A1": theta_0 = 0).

    Internal check using the private helper to make sure the
    factorisation `phase * Pi_c` (which scales to B2-B5's non-trivial
    phases) is correctly hard-coded to unity for A_1.
    """
    move_1 = ((1, 2, 3, 4), (1, 2, 3, 5))
    move_2 = ((3, 1, 2, 3), (3, 1, 2, 4))
    f1, t1 = dyn._coerce_move(move_1)
    f2, t2 = dyn._coerce_move(move_2)
    p1 = dyn._channel_phase_a1(f1, t1)
    p2 = dyn._channel_phase_a1(f2, t2)
    # Exact equality: theta_0 = 0 -> e^(i*0) = (1.0, 0.0).
    assert p1 == complex(1.0, 0.0), f"move_1 phase = {p1}, expected 1+0j"
    assert p2 == complex(1.0, 0.0), f"move_2 phase = {p2}, expected 1+0j"
    # And they should be identical (move-independent for A_1).
    assert p1 == p2

    # Second leg: U_a1 should be the same as the un-phased projector
    # sandwich (phase=1 means no scaling). This is a regression check
    # that no accidental phase shift is being applied.
    P_A1 = dyn._get_P_A1()
    U_swap = dyn._build_swap_4096(f1, t1)
    U_expected = (P_A1 @ U_swap @ P_A1).tocsr()
    U_actual = dyn.u_move_a1(imbalanced_position, move_1)
    diff = U_expected - U_actual
    diff.eliminate_zeros()
    assert _frob(diff) < 1e-15, (
        "U_a1 differs from un-phased projector-sandwich; "
        "phase factor accidentally non-unit?"
    )


# ====================================================================
#  Test 4: ADR-003 strict-unitary tier sparsity pattern
# ====================================================================

def test_b1_sparsity_pattern_within_p_a1_support(
    orbit_partition, imbalanced_position,
):
    """U_a1 = P_A1 @ swap @ P_A1 has the expected sparsity pattern.

    Two regimes (analytically derived from the sandwich form):

      Same-orbit move (swap commutes with P_A1):
        U_a1.nnz == P_A1.nnz  (exactly — no fill-in)

      Cross-orbit move:
        U_a1.nnz <= P_A1.nnz + 2 * |orbit(from)| * |orbit(to)|
        (the extra structure comes from columns `from` and `to` of
        P_A1 @ swap, which are P_A1's `to` and `from` columns
        respectively, then re-sandwiched by P_A1 on the right —
        producing fill-in confined to the (orbit(from), orbit(to))
        block).

    This is a structural regression check that the sandwich form is
    being built correctly — a bare swap (no sandwich) would have
    nnz = 4096 with one entry per row, NOT bounded by P_A1's pattern
    in either regime.
    """
    P_A1 = dyn._get_P_A1()
    P_A1_csr = P_A1.tocsr()
    orbit_id_of_sq, orbit_sizes = orbit_partition

    # Same-orbit cases (n=3): nnz must equal P_A1.nnz exactly.
    rng = np.random.default_rng(0xB1_5A_4)
    same = _gen_same_orbit_pairs(
        orbit_id_of_sq, orbit_sizes, list(imbalanced_position.keys()),
        n_pairs=3, rng=rng,
    )
    for (f_idx, t_idx) in same:
        U = dyn.u_move_a1(imbalanced_position, (f_idx, t_idx))
        # Shape / dtype / format invariants.
        assert U.shape == P_A1_csr.shape
        assert U.dtype == np.complex128
        assert sp.isspmatrix_csr(U)
        # Sparsity: same-orbit moves preserve P_A1's nnz pattern
        # (the sandwich is identical to P_A1 on the support).
        assert U.nnz == P_A1_csr.nnz, (
            f"same-orbit move ({f_idx}, {t_idx}): U.nnz {U.nnz} != "
            f"P_A1.nnz {P_A1_csr.nnz}"
        )

    # Cross-orbit cases (n=2): nnz bounded by closed-form upper bound.
    cross = _gen_cross_orbit_pairs(
        orbit_id_of_sq, list(imbalanced_position.keys()),
        n_pairs=2, rng=rng,
    )
    assert len(cross) == 2
    for (f_idx, t_idx) in cross:
        U = dyn.u_move_a1(imbalanced_position, (f_idx, t_idx))
        assert U.shape == P_A1_csr.shape
        assert U.dtype == np.complex128
        assert sp.isspmatrix_csr(U)
        size_from = orbit_sizes[orbit_id_of_sq[f_idx]]
        size_to = orbit_sizes[orbit_id_of_sq[t_idx]]
        bound = P_A1_csr.nnz + 2 * size_from * size_to
        assert U.nnz <= bound, (
            f"cross-orbit move ({f_idx}, {t_idx}) [orbit sizes "
            f"{size_from}, {size_to}]: U.nnz {U.nnz} > bound {bound}"
        )


def test_b1_shape_and_dtype(imbalanced_position):
    """Output shape and dtype invariants for direct (most common)
    callers."""
    move = ((1, 2, 3, 4), (1, 2, 3, 5))
    U = dyn.u_move_a1(imbalanced_position, move)
    assert U.shape == (4096, 4096)
    assert U.dtype == np.complex128
    assert sp.isspmatrix_csr(U)


# ====================================================================
#  Test 5: ADR-004 §3.4 amendment compliance
# ====================================================================
#
# The Phase 3.5 Probe-4 amendment to ADR-004 §3.4 dropped the
# operator-anti-commutation requirement. The Z_2 sector flip is
# implemented by ``state_to_psi``'s side-to-move sign multiplier, NOT
# by U_move's algebraic relationship to J_op. This test asserts the
# anti-commutator residual is non-zero (which it is, automatically,
# for the swap-permutation construction) — a regression check that
# nobody accidentally re-introduced the rejected requirement.

def test_b1_no_anti_commutation_with_J_op(imbalanced_position):
    """U_a1 does NOT anti-commute with J_op as algebraic operators
    (Phase 3.5 Probe-4 amendment to ADR-004 §3.4).

    Builds J_op as the central-inversion permutation matrix on
    C^4096; computes the anti-commutator
    ``{J_op, U_a1} = J_op @ U_a1 + U_a1 @ J_op``; asserts its
    Frobenius norm is non-zero.

    This is NOT a strict-unitary test — it is an explicit check that
    the discarded ADR-004 §3.4 requirement has not been re-introduced
    by a future refactor. The Z_2 grading lives at the state-vector
    level (state_to_psi sign), not the operator level.
    """
    # Build J_op (central inversion on the 4096-dim board).
    rows = np.empty(_t4.N_SQUARES, dtype=np.int64)
    cols = np.empty(_t4.N_SQUARES, dtype=np.int64)
    for s in range(_t4.N_SQUARES):
        x, y, z, w = _t4.rc4(s)
        rows[s] = _t4.sq4(7 - x, 7 - y, 7 - z, 7 - w)
        cols[s] = s
    data = np.ones(_t4.N_SQUARES, dtype=np.complex128)
    J_op = sp.csr_matrix(
        (data, (rows, cols)),
        shape=(_t4.N_SQUARES, _t4.N_SQUARES),
    )
    # Sanity: J_op^2 = I.
    JJ = (J_op @ J_op).tocsr()
    I = sp.eye(_t4.N_SQUARES, format='csr', dtype=np.complex128)
    JJ_minus_I = (JJ - I)
    JJ_minus_I.eliminate_zeros()
    assert JJ_minus_I.nnz == 0, "J_op is not order-2"

    # Sample a generic move (cross-orbit, since J-symmetric same-orbit
    # moves are rare and would zero the anti-commutator trivially).
    move = ((1, 2, 3, 4), (1, 2, 3, 5))
    U = dyn.u_move_a1(imbalanced_position, move)

    AC = (U @ J_op + J_op @ U).tocsr()
    AC.eliminate_zeros()
    ac_residual = _frob(AC)
    assert ac_residual > 1e-3, (
        f"anti-commutator residual = {ac_residual:.3e}; if this is "
        "near zero, the rejected ADR-004 §3.4 requirement has been "
        "accidentally re-imposed. Phase 3.5 Probe-4 amendment "
        "dropped the operator-anti-commutation requirement; the Z_2 "
        "sector flip happens at state_to_psi (sign multiplier), not "
        "at U_move."
    )


# ====================================================================
#  Test 6: Capture-move NotImplementedError
# ====================================================================

def test_b1_capture_move_raises_not_implemented(imbalanced_position):
    """``u_move_a1(state, capture_move, assume_non_capture=False)``
    raises ``NotImplementedError`` with a B5 pointer."""
    pos = imbalanced_position
    # Pick any two occupied squares; from -> to is therefore a capture.
    occ = sorted(pos.keys())
    assert len(occ) >= 2
    from_idx, to_idx = occ[0], occ[1]

    # Without the safety check (assume_non_capture=True / default),
    # u_move_a1 builds the unitary anyway — capture detection is
    # opt-in for B1 (the bridge can rely on upstream filtering).
    U = dyn.u_move_a1(pos, (from_idx, to_idx))
    assert U.shape == (4096, 4096)

    # With assume_non_capture=False, the call MUST refuse.
    with pytest.raises(NotImplementedError) as excinfo:
        dyn.u_move_a1(pos, (from_idx, to_idx), assume_non_capture=False)
    msg = str(excinfo.value)
    # The error message should point at the B5 milestone.
    assert "B5" in msg, (
        f"capture-move NotImplementedError should reference B5; got: {msg}"
    )
    assert ("ADR-002" in msg or "ADR-003" in msg), (
        f"capture-move NotImplementedError should reference an ADR; "
        f"got: {msg}"
    )


def test_b1_apply_move_qm_returns_assembled_dict(imbalanced_position):
    """After B3d/e the bridge no longer raises NotImplementedError
    for non-capture moves; it returns the assembled per-channel dict
    with all 11 channel entries (A_1 + STD4_* + FA_PAWN_* + FIB_SYM_*
    + FD_DIAG). This test verifies the A_1 entry is present and is a
    csr_matrix (the strict path; A_1 always returns an operator,
    never a marker dict).
    """
    move = ((1, 2, 3, 4), (1, 2, 3, 5))
    result = dyn.apply_move_qm(imbalanced_position, move)
    assert isinstance(result, dict), (
        f"apply_move_qm should return a dict; got "
        f"{type(result).__name__}"
    )
    # A_1 entry: always a csr_matrix (the projector-sandwich
    # construction, regardless of orbit dichotomy).
    assert 'A1' in result, (
        f"A1 entry missing from bridge dict; got keys "
        f"{sorted(result.keys())}"
    )
    a1_entry = result['A1']
    assert sp.isspmatrix_csr(a1_entry), (
        f"A_1 should be csr_matrix; got {type(a1_entry).__name__}"
    )
    assert a1_entry.shape == (4096, 4096)


# ====================================================================
#  Test 7: input-coercion / TypeError surface
# ====================================================================

def test_b1_move_accepts_tuple_and_int_endpoints(imbalanced_position):
    """Both 4-tuple coords and linear int indices are accepted."""
    move_tuple = ((1, 2, 3, 4), (1, 2, 3, 5))
    move_int = (_t4.sq4(1, 2, 3, 4), _t4.sq4(1, 2, 3, 5))
    U_tuple = dyn.u_move_a1(imbalanced_position, move_tuple)
    U_int = dyn.u_move_a1(imbalanced_position, move_int)
    diff = U_tuple - U_int
    diff.eliminate_zeros()
    assert _frob(diff) < 1e-15


def test_b1_move_4d_object_accepted(imbalanced_position):
    """Move4D-style objects with .from_sq / .to_sq attributes are
    accepted by duck typing (no hard import dependency)."""

    class _FakeMove4D:
        def __init__(self, fr, to):
            self.from_sq = fr
            self.to_sq = to

    move = _FakeMove4D((1, 2, 3, 4), (1, 2, 3, 5))
    U = dyn.u_move_a1(imbalanced_position, move)
    assert U.shape == (4096, 4096)


def test_b1_invalid_move_type_raises(imbalanced_position):
    """Bad move shapes should TypeError-out."""
    with pytest.raises(TypeError):
        dyn.u_move_a1(imbalanced_position, "not a move")
    with pytest.raises(TypeError):
        dyn.u_move_a1(imbalanced_position, (1, 2, 3))  # 3-tuple


def test_b1_invalid_endpoint_raises(imbalanced_position):
    """Out-of-range linear index raises ValueError."""
    with pytest.raises(ValueError):
        dyn.u_move_a1(imbalanced_position, (-1, 0))
    with pytest.raises(ValueError):
        dyn.u_move_a1(imbalanced_position, (0, 4096))


# ====================================================================
#  Test 8: integration with chess_spectral_4d.apply_move (v1.4)
# ====================================================================

def test_b1_with_chess_spectral_4d_apply_move(imbalanced_position):
    """End-to-end: build a GameState4D, generate a Move4D via
    chess_spectral_4d.apply_move, hand it to u_move_a1.

    This is a smoke test of the bridge surface — confirms that the
    Move4D record's .from_sq / .to_sq attributes plug straight into
    u_move_a1 without explicit conversion code.
    """
    from chess_spectral_4d.move_history import GameState4D
    from chess_spectral_4d import apply_move as cs_apply_move
    from chess_spectral import fen_4d

    pos = imbalanced_position
    fen4 = fen_4d.serialize(pos)
    state = GameState4D.from_fen4(fen4)
    # Pick a same-orbit non-capture move for clean numerics.
    # Queen at (1,2,3,4) -> a same-orbit empty square.
    from_coord = (1, 2, 3, 4)
    closure = _t4.b4_closure()
    f_sq = _t4.sq4(*from_coord)
    occ = set(state.position.keys())
    target = None
    for g in closure:
        x, y, z, w = _t4._apply_b4_to_square(g, *from_coord)
        candidate = _t4.sq4(x, y, z, w)
        if candidate != f_sq and candidate not in occ:
            target = (x, y, z, w)
            break
    assert target is not None, "no same-orbit empty square found"

    # apply_move mutates state and returns Move4D.
    rec = cs_apply_move(state, from_coord, target)
    # rec.from_sq and rec.to_sq are 4-tuples; u_move_a1 should accept
    # them via the Move4D duck-type path.
    U = dyn.u_move_a1(pos, rec)
    assert U.shape == (4096, 4096)
    assert U.dtype == np.complex128


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
