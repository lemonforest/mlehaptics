"""Unit tests for chess_spectral.qm_4d_dynamics — Phase 4 milestone B3a.

Covers the STD4_X / STD4_Y / STD4_Z / STD4_W channel move-as-unitary
lifts (the four std-rep coord channels per ADR-003 §3.1 channels 1-4).

  1. Sub-unitarity within each STD4_<axis> subspace, **same-B_4-orbit
     pairs that ALSO have matching ``|coord_resid|``** (the strict-
     unitary regime per the empirical B3a finding). For each axis x
     ~10 pairs: ``U_std4^H U_std4 == P_STD4_axis`` within 1e-10.
  2. Cross-B_4-orbit pairs: ``u_move_std4`` returns a marker dict
     pointing at measurement-only re-encode (per the ADR-003
     amendment Option (a)). NOT an operator.
  3. STD4 channel evolution matches direct re-encoding (same-orbit
     non-capture). For valid same-orbit moves where the operator is
     returned: ``U_std4 @ psi_pre[STD4_axis_block]`` agrees with the
     STD4_axis block of the post-move encoding (up to the ADR-001
     phase factor).
  4. ADR-001 phase formula sanity. For 4 sample moves with known
     displacement vectors, verify the applied phase matches
     ``e^{i * (pi/4) * delta_axis}`` to 1e-12.
  5. ADR-003 strict-unitary tier sparsity / shape / dtype invariants.
  6. ADR-004 §3.4 amendment compliance: ``U_std4`` does NOT
     anti-commute with J_op (sector-flip-via-state_to_psi).
  7. Cross-orbit returns marker dict (verified in test 2).
  8. Per-axis isolation: ``u_move_std4(... 'X')`` only changes the
     STD4_X block, not STD4_Y / STD4_Z / STD4_W.
  9. Same-orbit BUT |coord_resid| mismatch: documented xfail-strict
     marker recording the structural sub-unitarity gap.
 10. Capture / not-implemented / input-coercion sanity (mirroring B1).

B3a empirical findings hard-coded into the spec
-----------------------------------------------

* **Same-B_4-orbit + matching |coord_resid|**: ~9-12% of same-orbit
  pairs (29 611 pairs per axis empirically). Sub-unitarity at machine
  precision (1e-14); encoder match at machine precision.
* **Same-B_4-orbit + mismatched |coord_resid|**: ~88-91% of
  same-orbit pairs. Sub-unitarity residual ~1e-1 to 1e0; encoder
  match still works (the operator is constructed to match the
  encoder formula). Marked xfail-strict for the sub-unitarity claim.
* **Cross-B_4-orbit**: ``u_move_std4`` returns a marker dict, NOT a
  matrix. Tests assert the marker shape and content.

Run with ``pytest tests/test_qm_4d_dynamics_b3a.py -v`` from python/.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Dict, List, Tuple

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


def _frob(M):
    """Frobenius norm. Works on both sparse and dense matrices."""
    if sp.issparse(M):
        return float(sp.linalg.norm(M))
    return float(np.linalg.norm(np.asarray(M)))


# ---- Orbit / pair fixtures -----------------------------------------


@pytest.fixture(scope='module')
def orbit_partition() -> Tuple[List[int], List[int]]:
    """B_4 orbit partition: (orbit_id_of_sq, orbit_sizes).

    Same construction as B1's fixture; module-cached so we pay the
    closure-construction cost once per test session.
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


@pytest.fixture(scope='module')
def coord_resid() -> np.ndarray:
    """The encoder's (4, 4096) coord_resid table — used to filter
    same-orbit pairs by |coord_resid| matching.
    """
    return _enc4._load_tables()['coord_resid']


@pytest.fixture(scope='module')
def imbalanced_position():
    """A position with non-zero STD4 channel content (asymmetric
    occupancy on the lattice). Returns a position dict in linear-square
    form. Re-using B1's fixture style.
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
    """Second imbalanced position to vary the test sample."""
    coords = {
        (3, 3, 3, 3): 'K', (4, 4, 4, 4): 'k',
        (0, 1, 2, 3): 'Q', (7, 6, 5, 4): 'N',
        (5, 2, 0, 6): 'B', (1, 6, 7, 0): 'R',
        (2, 0, 4, 1): 'B',
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


def _gen_strict_pairs(
    orbit_id_of_sq, orbit_sizes, coord_resid: np.ndarray,
    axis: str, position_keys, *, n_pairs: int,
    rng: np.random.Generator,
) -> List[Tuple[int, int]]:
    """Generate non-capture (from, to) pairs that are:
      1) same B_4 orbit, AND
      2) |coord_resid[axis_idx, from]| == |coord_resid[axis_idx, to]|, AND
      3) ``coord_resid[axis_idx, *]`` non-zero on both endpoints
         (otherwise sub-unitarity is on the "outside support" trivial
         regime), AND
      4) ``to`` not occupied (non-capture).

    These are the "strict-unitary regime" pairs per the B3a empirical
    finding.
    """
    occupied = set(position_keys)
    a_idx = dyn._STD4_AXIS_INDEX[axis]
    cr_a = coord_resid[a_idx]

    # Bucket orbit elements
    orbit_members: Dict[int, List[int]] = {}
    for s, oid in enumerate(orbit_id_of_sq):
        orbit_members.setdefault(oid, []).append(s)

    occ_list = sorted(occupied)
    pairs: List[Tuple[int, int]] = []
    seen: set = set()
    max_attempts = max(256, 16 * n_pairs)
    attempts = 0
    while len(pairs) < n_pairs and attempts < max_attempts:
        attempts += 1
        s = int(rng.choice(occ_list))
        if cr_a[s] == 0:
            continue
        oid = orbit_id_of_sq[s]
        # Filter same-orbit candidates by |coord_resid| match and not
        # occupied.
        candidates = [
            t for t in orbit_members[oid]
            if t != s
            and t not in occupied
            and abs(cr_a[t]) == abs(cr_a[s])
        ]
        if not candidates:
            continue
        t = int(rng.choice(candidates))
        key = (s, t)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(key)
    return pairs


def _gen_cross_orbit_pairs(
    orbit_id_of_sq, position_keys, *, n_pairs: int,
    rng: np.random.Generator,
) -> List[Tuple[int, int]]:
    """Generate non-capture cross-B_4-orbit pairs.

    Same shape as B1's helper.
    """
    occupied = set(position_keys)
    occ_list = sorted(occupied)
    pairs: List[Tuple[int, int]] = []
    seen: set = set()
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
        key = (s, t)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(key)
    return pairs


def _gen_same_orbit_mismatch_pairs(
    orbit_id_of_sq, orbit_sizes, coord_resid: np.ndarray,
    axis: str, position_keys, *, n_pairs: int,
    rng: np.random.Generator,
) -> List[Tuple[int, int]]:
    """Generate non-capture same-B_4-orbit pairs where
    ``|coord_resid[axis, from]| != |coord_resid[axis, to]|`` — the
    structural-sub-unitarity-gap regime. Used by xfail-strict tests.
    """
    occupied = set(position_keys)
    a_idx = dyn._STD4_AXIS_INDEX[axis]
    cr_a = coord_resid[a_idx]

    orbit_members: Dict[int, List[int]] = {}
    for s, oid in enumerate(orbit_id_of_sq):
        orbit_members.setdefault(oid, []).append(s)

    occ_list = sorted(occupied)
    pairs: List[Tuple[int, int]] = []
    seen: set = set()
    max_attempts = max(256, 16 * n_pairs)
    attempts = 0
    while len(pairs) < n_pairs and attempts < max_attempts:
        attempts += 1
        s = int(rng.choice(occ_list))
        if cr_a[s] == 0:
            continue
        oid = orbit_id_of_sq[s]
        candidates = [
            t for t in orbit_members[oid]
            if t != s
            and t not in occupied
            and cr_a[t] != 0
            and abs(cr_a[t]) != abs(cr_a[s])
        ]
        if not candidates:
            continue
        t = int(rng.choice(candidates))
        key = (s, t)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(key)
    return pairs


# ====================================================================
#  Test 1: Sub-unitarity within each STD4_<axis> subspace, strict regime
# ====================================================================
#
# Per the B3a empirical finding (B3a docstring): the strict regime is
# same-B_4-orbit + matching |coord_resid|. ~9-12% of same-orbit pairs
# qualify, so the fixture has plenty of test material.

@pytest.mark.parametrize('axis', ['X', 'Y', 'Z', 'W'])
def test_b3a_subunitarity_strict_regime(
    axis, orbit_partition, coord_resid,
    imbalanced_position, imbalanced_position_b,
):
    """For each STD4 axis: 10+ same-orbit |coord_resid|-matching pairs,
    sub-unitarity ``U^H U == P_STD4_axis`` within 1e-10."""
    orbit_id_of_sq, orbit_sizes = orbit_partition
    P_axis = dyn._get_p_std4(axis)
    rng = np.random.default_rng(0xB3A_500 + ord(axis))

    pos_a = imbalanced_position
    pos_b = imbalanced_position_b
    pairs_a = _gen_strict_pairs(
        orbit_id_of_sq, orbit_sizes, coord_resid, axis,
        list(pos_a.keys()), n_pairs=8, rng=rng,
    )
    pairs_b = _gen_strict_pairs(
        orbit_id_of_sq, orbit_sizes, coord_resid, axis,
        list(pos_b.keys()), n_pairs=8, rng=rng,
    )
    cases = [(pos_a, p) for p in pairs_a] + [(pos_b, p) for p in pairs_b]
    assert len(cases) >= 10, (
        f"axis {axis}: only {len(cases)} strict-regime cases generated; "
        "expected >= 10. Either the fixture batched too restrictively "
        "or the |coord_resid|-matching subset is smaller than expected "
        "for this axis."
    )

    residuals: List[float] = []
    for (pos, (s, t)) in cases:
        result = dyn.u_move_std4(pos, (s, t), axis)
        # Strict regime: must return a CSR matrix (same-orbit dispatch).
        assert sp.isspmatrix_csr(result), (
            f"axis {axis} pair ({s}, {t}): expected csr_matrix, got "
            f"{type(result).__name__}"
        )
        prod = result.conj().T @ result
        diff = (prod - P_axis).tocsr()
        diff.eliminate_zeros()
        r = _frob(diff)
        residuals.append(r)
        assert r < 1e-10, (
            f"axis {axis} pair ({s}, {t}): sub-unitarity residual "
            f"{r:.3e} > 1e-10; orbits "
            f"({orbit_id_of_sq[s]}, {orbit_id_of_sq[t]})"
        )

    assert max(residuals) < 1e-10


# ====================================================================
#  Test 2: Cross-orbit returns marker dict
# ====================================================================
#
# Per the ADR-003 amendment Option (a), cross-orbit moves do not
# receive a strict-unitary lift; they route to measurement-only
# re-encode. ``u_move_std4`` returns a marker dict; the bridge layer
# (v1.5) consumes it.

@pytest.mark.parametrize('axis', ['X', 'Y', 'Z', 'W'])
def test_b3a_cross_orbit_returns_marker(
    axis, orbit_partition, imbalanced_position,
):
    """Cross-B_4-orbit moves return ``{'strict_unitary': False, ...}``.
    """
    orbit_id_of_sq, _ = orbit_partition
    rng = np.random.default_rng(0xB3A_C0 + ord(axis))
    pairs = _gen_cross_orbit_pairs(
        orbit_id_of_sq, list(imbalanced_position.keys()),
        n_pairs=10, rng=rng,
    )
    assert len(pairs) >= 5
    for (s, t) in pairs:
        result = dyn.u_move_std4(imbalanced_position, (s, t), axis)
        assert isinstance(result, dict), (
            f"axis {axis} cross-orbit pair ({s}, {t}): expected marker "
            f"dict, got {type(result).__name__}"
        )
        # Marker schema spec.
        assert result['strict_unitary'] is False
        assert result['reason'] == 'cross-orbit'
        assert 'measurement-only' in result['recommendation']
        assert result['channel'] == f'STD4_{axis}'
        assert result['sq_from'] == s
        assert result['sq_to'] == t
        assert orbit_id_of_sq[s] == result['orbit_from']
        assert orbit_id_of_sq[t] == result['orbit_to']
        assert result['orbit_from'] != result['orbit_to']


# ====================================================================
#  Test 3: STD4 channel evolution matches direct re-encoding
# ====================================================================
#
# The similarity-transform construction matches the encoder formula
# by design: psi_pre[s] = coord_resid[axis, s] * sig_pre[s] and
# psi_post[s] = coord_resid[axis, s] * sig_post[s]; for non-capture
# o -> d the operator U = D @ swap @ D^+ produces psi_post from
# psi_pre exactly (up to the ADR-001 phase factor, which the test
# strips by comparing magnitudes).

@pytest.mark.parametrize('axis', ['X', 'Y', 'Z', 'W'])
def test_b3a_re_encoding_match_strict_regime(
    axis, orbit_partition, coord_resid,
    imbalanced_position, imbalanced_position_b,
):
    """For same-orbit non-capture moves (strict regime),
    ``|U_std4 @ psi_pre[STD4_axis_block]|`` == ``|psi_post[STD4_axis_block]|``
    within 1e-10."""
    orbit_id_of_sq, orbit_sizes = orbit_partition
    rng = np.random.default_rng(0xB3A_222_500 + ord(axis))
    pos_a = imbalanced_position
    pos_b = imbalanced_position_b
    pairs_a = _gen_strict_pairs(
        orbit_id_of_sq, orbit_sizes, coord_resid, axis,
        list(pos_a.keys()), n_pairs=8, rng=rng,
    )
    pairs_b = _gen_strict_pairs(
        orbit_id_of_sq, orbit_sizes, coord_resid, axis,
        list(pos_b.keys()), n_pairs=8, rng=rng,
    )
    cases = [(pos_a, p) for p in pairs_a] + [(pos_b, p) for p in pairs_b]
    assert len(cases) >= 10

    n_passed = 0
    chan_idx = dyn._STD4_CHANNEL_IDX[axis]
    for (pos, (s, t)) in cases:
        # Apply the move classically.
        post = dict(pos)
        piece = post.pop(s)
        post[t] = piece

        enc_pre = _enc4.encode_4d(pos).astype(np.complex128)
        enc_post = _enc4.encode_4d(post).astype(np.complex128)
        n_pre = float(np.linalg.norm(enc_pre))
        n_post = float(np.linalg.norm(enc_post))
        if n_pre == 0 or n_post == 0:
            continue

        # Extract STD4_axis block.
        start = chan_idx * dyn.CHANNEL_DIM
        end = start + dyn.CHANNEL_DIM
        psi_pre_block = enc_pre[start:end] / n_pre
        psi_post_block = enc_post[start:end] / n_post

        result = dyn.u_move_std4(pos, (s, t), axis)
        # Phase factor is included in the operator itself; the
        # re-encoding match holds for |psi_via| vs |psi_post_block|
        # (channel marginals are phase-equivalent).
        psi_via = result @ psi_pre_block
        diff_mag = float(
            np.linalg.norm(np.abs(psi_via) - np.abs(psi_post_block))
        )
        assert diff_mag < 1e-10, (
            f"axis {axis} pair ({s}, {t}): re-encoding magnitude "
            f"mismatch = {diff_mag:.3e}"
        )
        n_passed += 1

    assert n_passed >= 8, (
        f"axis {axis}: only {n_passed} non-degenerate cases passed; "
        "expected >= 8"
    )


# ====================================================================
#  Test 4: ADR-001 phase formula sanity
# ====================================================================
#
# Per ADR-001 §3.1 row "STD4_a": theta_a = (pi/4) * (axis_to - axis_from).
# Test 4+ sample moves with explicit coordinate displacements and
# check the phase factor matches at 1e-12 tolerance.

def test_b3a_adr001_phase_formula():
    """Direct numeric check of the phase formula for known moves and
    axes."""
    cases = [
        # (move, axis, expected_delta)
        # axis 'X' = coord index 0
        (((0, 0, 0, 0), (3, 0, 0, 0)), 'X', 3),
        (((5, 1, 2, 3), (5, 4, 2, 3)), 'X', 0),     # X unchanged
        (((5, 0, 0, 0), (2, 0, 0, 0)), 'X', -3),    # negative X displacement
        # axis 'Y' = coord index 1
        (((1, 2, 3, 4), (1, 5, 3, 4)), 'Y', 3),
        # axis 'Z' = coord index 2
        (((1, 2, 3, 4), (1, 2, 7, 4)), 'Z', 4),
        # axis 'W' = coord index 3
        (((0, 0, 0, 1), (0, 0, 0, 6)), 'W', 5),
    ]
    for ((from_c, to_c), axis, expected_delta) in cases:
        f = _t4.sq4(*from_c)
        t = _t4.sq4(*to_c)
        phase = dyn._channel_phase_std4(f, t, axis)
        expected_theta = (math.pi / 4.0) * expected_delta
        expected_phase = complex(math.cos(expected_theta),
                                 math.sin(expected_theta))
        diff = abs(phase - expected_phase)
        assert diff < 1e-12, (
            f"axis {axis} move {from_c}->{to_c} (delta={expected_delta}): "
            f"phase {phase} differs from expected {expected_phase} by "
            f"{diff:.3e}"
        )


def test_b3a_phase_zero_when_axis_orthogonal():
    """When the move doesn't displace along the relevant axis, the
    phase factor is exactly 1.0+0j."""
    # Move displaces only along Y axis.
    f = _t4.sq4(1, 2, 3, 4)
    t = _t4.sq4(1, 5, 3, 4)
    # X, Z, W axes orthogonal -> phase = 1+0j exactly
    for axis in ['X', 'Z', 'W']:
        phase = dyn._channel_phase_std4(f, t, axis)
        assert phase == complex(1.0, 0.0), (
            f"axis {axis}: phase {phase} != 1+0j (axis is orthogonal "
            "to the move displacement)"
        )
    # Y axis: delta=3, theta = 3*pi/4, phase != 1
    phase_y = dyn._channel_phase_std4(f, t, 'Y')
    assert abs(phase_y - 1.0) > 0.5  # cos(3pi/4) = -sqrt(2)/2


# ====================================================================
#  Test 5: ADR-003 strict-unitary tier sparsity / shape / dtype
# ====================================================================

@pytest.mark.parametrize('axis', ['X', 'Y', 'Z', 'W'])
def test_b3a_shape_dtype_format(
    axis, orbit_partition, coord_resid, imbalanced_position,
):
    """Same-orbit operator: shape (4096, 4096), dtype complex128, CSR.
    """
    orbit_id_of_sq, orbit_sizes = orbit_partition
    rng = np.random.default_rng(0xB3A_500 + ord(axis))
    pairs = _gen_strict_pairs(
        orbit_id_of_sq, orbit_sizes, coord_resid, axis,
        list(imbalanced_position.keys()), n_pairs=3, rng=rng,
    )
    assert len(pairs) >= 1
    for (s, t) in pairs:
        U = dyn.u_move_std4(imbalanced_position, (s, t), axis)
        assert sp.isspmatrix_csr(U)
        assert U.shape == (4096, 4096)
        assert U.dtype == np.complex128


@pytest.mark.parametrize('axis', ['X', 'Y', 'Z', 'W'])
def test_b3a_nnz_matches_p_std4(
    axis, orbit_partition, coord_resid, imbalanced_position,
):
    """The similarity-transform U = D @ swap @ D^+ has exactly
    P_STD4_axis.nnz nonzeros for the same-orbit case where both
    endpoints are in support — one nonzero per in-support row from
    the swap permutation × diagonal multiplication.
    """
    orbit_id_of_sq, orbit_sizes = orbit_partition
    rng = np.random.default_rng(0xB3A_5C + ord(axis))
    pairs = _gen_strict_pairs(
        orbit_id_of_sq, orbit_sizes, coord_resid, axis,
        list(imbalanced_position.keys()), n_pairs=3, rng=rng,
    )
    P_axis = dyn._get_p_std4(axis)
    for (s, t) in pairs:
        U = dyn.u_move_std4(imbalanced_position, (s, t), axis)
        # Sanity bound: U has at most one nonzero per row (similarity
        # of a permutation by a diagonal). Total nnz <= 4096.
        assert U.nnz <= _t4.N_SQUARES
        # Strict regime: nnz == P_STD4.nnz (in-support rows only).
        assert U.nnz == P_axis.nnz, (
            f"axis {axis} pair ({s}, {t}): U.nnz {U.nnz} != "
            f"P_STD4_{axis}.nnz {P_axis.nnz}"
        )


# ====================================================================
#  Test 6: ADR-004 §3.4 amendment compliance
# ====================================================================

@pytest.mark.parametrize('axis', ['X', 'Y', 'Z', 'W'])
def test_b3a_no_anti_commutation_with_J_op(
    axis, orbit_partition, coord_resid, imbalanced_position,
):
    """U_std4 does NOT anti-commute with J_op as algebraic operators.
    """
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
    # J_op^2 = I sanity.
    JJ = (J_op @ J_op).tocsr()
    I_op = sp.eye(_t4.N_SQUARES, format='csr', dtype=np.complex128)
    JJ_diff = (JJ - I_op)
    JJ_diff.eliminate_zeros()
    assert JJ_diff.nnz == 0

    orbit_id_of_sq, orbit_sizes = orbit_partition
    rng = np.random.default_rng(0xB3A_AA + ord(axis))
    pairs = _gen_strict_pairs(
        orbit_id_of_sq, orbit_sizes, coord_resid, axis,
        list(imbalanced_position.keys()), n_pairs=3, rng=rng,
    )
    assert len(pairs) >= 1
    s, t = pairs[0]
    U = dyn.u_move_std4(imbalanced_position, (s, t), axis)
    AC = (U @ J_op + J_op @ U).tocsr()
    AC.eliminate_zeros()
    ac_residual = _frob(AC)
    assert ac_residual > 1e-3, (
        f"axis {axis}: anti-commutator residual {ac_residual:.3e} "
        "near zero — the rejected ADR-004 §3.4 operator-anti-commutation "
        "requirement appears to be re-introduced."
    )


# ====================================================================
#  Test 7: Same-orbit + |coord_resid| mismatch — xfail-strict gap
# ====================================================================

@pytest.mark.xfail(
    strict=True,
    reason=(
        "B3a finding: U_std4^H U_std4 == P_STD4_axis at machine "
        "precision requires same-B_4-orbit AND matching |coord_resid|. "
        "For same-orbit pairs with mismatched |coord_resid|, the "
        "similarity transform produces a non-trivial sub-unitarity "
        "residual (~1e-1 to 1e0); per the ADR-003 amendment Option "
        "(a) these still take the strict-unitary path (operator is "
        "constructed and returned) but the unitarity claim is "
        "documented-not-strict for them."
    ),
)
@pytest.mark.parametrize('axis', ['X', 'Y', 'Z', 'W'])
def test_b3a_subunitarity_same_orbit_mismatch_xfail(
    axis, orbit_partition, coord_resid, imbalanced_position,
):
    """Same-orbit + |coord_resid| mismatch: sub-unitarity claim fails.
    """
    orbit_id_of_sq, orbit_sizes = orbit_partition
    rng = np.random.default_rng(0xB3A_DD + ord(axis))
    pairs = _gen_same_orbit_mismatch_pairs(
        orbit_id_of_sq, orbit_sizes, coord_resid, axis,
        list(imbalanced_position.keys()), n_pairs=10, rng=rng,
    )
    assert len(pairs) >= 5, (
        f"axis {axis}: need >= 5 mismatch pairs, got {len(pairs)}"
    )
    P_axis = dyn._get_p_std4(axis)
    for (s, t) in pairs:
        result = dyn.u_move_std4(imbalanced_position, (s, t), axis)
        assert sp.isspmatrix_csr(result)  # same-orbit -> operator
        diff = (result.conj().T @ result - P_axis).tocsr()
        diff.eliminate_zeros()
        # The strict-unitary form fails for these pairs; assert tightly
        # so xfail-strict converts the natural failure into a green
        # expected-fail outcome.
        assert _frob(diff) < 1e-10


# ====================================================================
#  Test 8: Per-axis isolation
# ====================================================================
#
# Applying U_std4_X must only update the STD4_X channel block of the
# psi vector, not STD4_Y / STD4_Z / STD4_W.

@pytest.mark.parametrize('axis', ['X', 'Y', 'Z', 'W'])
def test_b3a_per_axis_isolation(
    axis, orbit_partition, coord_resid, imbalanced_position,
):
    """U_std4 only changes its own channel block."""
    orbit_id_of_sq, orbit_sizes = orbit_partition
    rng = np.random.default_rng(0xB3A_FF + ord(axis))
    pairs = _gen_strict_pairs(
        orbit_id_of_sq, orbit_sizes, coord_resid, axis,
        list(imbalanced_position.keys()), n_pairs=2, rng=rng,
    )
    assert len(pairs) >= 1
    s, t = pairs[0]
    U = dyn.u_move_std4(imbalanced_position, (s, t), axis)
    chan_idx = dyn._STD4_CHANNEL_IDX[axis]

    # Build a full encoded vector for the position
    enc = _enc4.encode_4d(imbalanced_position).astype(np.complex128)
    enc_norm = float(np.linalg.norm(enc))
    if enc_norm > 0:
        enc = enc / enc_norm

    # Apply U on only its own block; copy other blocks through.
    out = enc.copy()
    start = chan_idx * dyn.CHANNEL_DIM
    end = start + dyn.CHANNEL_DIM
    out[start:end] = U @ enc[start:end]

    # Other 10 channels should be unchanged.
    for c in range(dyn.N_CHANNELS):
        if c == chan_idx:
            continue
        cs = c * dyn.CHANNEL_DIM
        ce = cs + dyn.CHANNEL_DIM
        diff = float(np.linalg.norm(out[cs:ce] - enc[cs:ce]))
        assert diff < 1e-15, (
            f"axis {axis} channel {c}: per-axis isolation broken; "
            f"diff = {diff:.3e}"
        )


# ====================================================================
#  Test 9: Capture-move NotImplementedError
# ====================================================================

@pytest.mark.parametrize('axis', ['X', 'Y', 'Z', 'W'])
def test_b3a_capture_raises_not_implemented(
    axis, imbalanced_position,
):
    """`u_move_std4(state, capture_move, axis, assume_non_capture=False)`
    raises NotImplementedError pointing at B5."""
    pos = imbalanced_position
    occ = sorted(pos.keys())
    # Pick two occupied squares -> capture
    from_idx, to_idx = occ[0], occ[1]
    # Default (assume_non_capture=True) should still build OR return marker
    result = dyn.u_move_std4(pos, (from_idx, to_idx), axis)
    # Either a CSR matrix (same-orbit) or a marker dict (cross-orbit) —
    # both are valid in the assume_non_capture=True fast path.
    assert sp.isspmatrix_csr(result) or isinstance(result, dict)

    # With assume_non_capture=False, must refuse for capture moves.
    with pytest.raises(NotImplementedError) as excinfo:
        dyn.u_move_std4(
            pos, (from_idx, to_idx), axis, assume_non_capture=False,
        )
    msg = str(excinfo.value)
    assert "B5" in msg
    assert ("ADR-002" in msg or "ADR-003" in msg)


# ====================================================================
#  Test 10: Input coercion / validation
# ====================================================================


def test_b3a_invalid_axis_raises():
    """An axis outside {'X','Y','Z','W'} raises ValueError."""
    pos = {0: 'Q'}
    with pytest.raises(ValueError):
        dyn.u_move_std4(pos, (0, 1), 'Q')
    with pytest.raises(ValueError):
        dyn.u_move_std4(pos, (0, 1), 'x')  # lowercase rejected


def test_b3a_invalid_endpoint_raises():
    """Out-of-range endpoint raises ValueError."""
    pos = {0: 'Q'}
    with pytest.raises(ValueError):
        dyn.u_move_std4(pos, (-1, 0), 'X')
    with pytest.raises(ValueError):
        dyn.u_move_std4(pos, (0, 4096), 'X')


def test_b3a_phase_invalid_axis_raises():
    """The internal phase helper rejects unknown axis names."""
    with pytest.raises(ValueError):
        dyn._channel_phase_std4(0, 1, 'Q')


def test_b3a_invalid_move_type_raises(imbalanced_position):
    """Bad move shapes TypeError-out."""
    with pytest.raises(TypeError):
        dyn.u_move_std4(imbalanced_position, "not a move", 'X')
    with pytest.raises(TypeError):
        dyn.u_move_std4(imbalanced_position, (1, 2, 3), 'X')


def test_b3a_move_accepts_tuple_and_int_endpoints(imbalanced_position):
    """4-tuple coords and linear int indices are interchangeable."""
    move_tuple = ((1, 2, 3, 4), (1, 2, 3, 5))
    move_int = (_t4.sq4(1, 2, 3, 4), _t4.sq4(1, 2, 3, 5))
    result_tuple = dyn.u_move_std4(imbalanced_position, move_tuple, 'X')
    result_int = dyn.u_move_std4(imbalanced_position, move_int, 'X')
    # Both inputs route to the same dispatch (operator or marker).
    if sp.isspmatrix_csr(result_tuple):
        assert sp.isspmatrix_csr(result_int)
        diff = result_tuple - result_int
        diff.eliminate_zeros()
        assert _frob(diff) < 1e-15
    else:
        assert isinstance(result_tuple, dict)
        assert isinstance(result_int, dict)
        assert result_tuple == result_int


# ====================================================================
#  Test 11: bridge integration — STD4 channels populate the dict
# ====================================================================
#
# The bridge stub assembles the per-channel skeleton; with B3a shipped,
# all four STD4_axis entries should be present (either operator or
# marker). The stub still raises NotImplementedError because B3b/B3c-e
# + B5 are pending.

def test_b3a_bridge_lists_std4_channels_as_shipped(imbalanced_position):
    """Bridge stub claims STD4_X/Y/Z/W are shipped (alongside A1)."""
    move = ((1, 2, 3, 4), (1, 2, 3, 5))
    with pytest.raises(NotImplementedError) as excinfo:
        dyn.apply_move_qm(imbalanced_position, move)
    msg = str(excinfo.value)
    # Verify the shipped list contains STD4_*. (The exact phrasing of
    # the message is bridge-internal but the channel names are pinned.)
    assert 'STD4_X' in msg
    assert 'STD4_Y' in msg
    assert 'STD4_Z' in msg
    assert 'STD4_W' in msg


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
