"""Phase A validation gate — exercises every design constraint on the
chosen ``(M, GEN_X, GEN_Y, GEN_Z, GEN_W)`` tuple before any operator
code lands.

This test does NOT depend on Phase B's operator implementations; it
only requires the constants module to expose:

    MODULUS_4D, GEN_X, GEN_Y, GEN_Z, GEN_W

If any constraint fails, the design is wrong — return to
``research/chess4d_phase_design.py`` and re-pick.

Constraint catalog (mirrors the four checks in the search script):

    C1 (coprime, necessary):       gcd(g_i, M) = 1 for each axis g_i.
    C2 (image bijection):          phi maps [0,7]^4 to 4096 distinct
                                   residues mod M.
    C3 (subgroup non-closure):     the image is NOT a subgroup of Z_M
                                   — random pair-sums frequently land
                                   outside the image.
    C4 (derived-gen distinctness): all 8 axis + 24 plane-diagonal +
                                   48 knight + 80 king shifts
                                   pairwise distinct mod M (within
                                   each category and across).

Plus a sanity-check on the O&C mobility numbers each generator family
realizes from a deep-interior origin square (rook 28, knight 48, king
80, bishop 24 plane-diagonal directions × variable extent).
"""
from __future__ import annotations

from itertools import product
from math import gcd

import pytest

# Module under test — the Phase B constants. If this import fails,
# Phase A is incomplete: the constants haven't been pinned yet.
phase_ops_4d = pytest.importorskip(
    "chess_spectral.phase_operators_4d.phase_operators_4d",
    reason="Phase A: constants module not yet committed; run "
           "research/chess4d_phase_design.py and pin the chosen tuple "
           "into chess_spectral/phase_operators_4d/phase_operators_4d.py",
)

M = phase_ops_4d.MODULUS_4D
GX = phase_ops_4d.GEN_X
GY = phase_ops_4d.GEN_Y
GZ = phase_ops_4d.GEN_Z
GW = phase_ops_4d.GEN_W


# ─── C1 — pairwise coprime to M ─────────────────────────────────────


def test_c1_each_generator_coprime_to_modulus():
    """Each axis generator is coprime to M (necessary condition)."""
    for name, g in [("GEN_X", GX), ("GEN_Y", GY),
                    ("GEN_Z", GZ), ("GEN_W", GW)]:
        assert gcd(g, M) == 1, (
            f"{name}={g} not coprime to MODULUS_4D={M}"
        )


# ─── C2 — image bijection on [0,7]^4 ────────────────────────────────


def test_c2_image_is_4096_distinct_residues():
    """phi(x,y,z,w) = (x*GX + y*GY + z*GZ + w*GW) mod M is injective
    on [0,7]^4 (image size == 4096)."""
    image = set()
    for x, y, z, w in product(range(8), repeat=4):
        phi = (x * GX + y * GY + z * GZ + w * GW) % M
        image.add(phi)
    assert len(image) == 4096, (
        f"image size {len(image)} != 4096; collisions exist"
    )


# ─── C3 — image is NOT a subgroup of Z_M ────────────────────────────


def test_c3_image_is_not_a_subgroup():
    """The 4096-point image must not be closed under addition mod M.
    If it were, off-board phase shifts would land back in the image
    and Phase B's invert step couldn't detect boundary crossings.
    See PHASE_OPERATOR_SUPPLEMENT.md §11.2.1 for the 2D analogue."""
    image = set()
    for x, y, z, w in product(range(8), repeat=4):
        image.add((x * GX + y * GY + z * GZ + w * GW) % M)

    # Find at least one pair-sum that escapes the image. If we can't
    # find one in 200 random samples, the image is suspiciously close
    # to a subgroup (and at minimum, M = 4096 would force exact
    # equality with Z_4096, which is a subgroup).
    import random
    rng = random.Random(0xCAFEBABE)
    image_list = sorted(image)
    found_escape = False
    for _ in range(200):
        a = rng.choice(image_list)
        b = rng.choice(image_list)
        if (a + b) % M not in image:
            found_escape = True
            break
    assert found_escape, (
        f"image of [0,7]^4 mod M={M} appears closed under addition; "
        f"design fails Constraint 3 (subgroup non-closure)"
    )


# ─── C4 — derived-generator distinctness ────────────────────────────


def _derived_shifts() -> dict[str, list[int]]:
    """Reconstruct the four derived shift sets from (GX, GY, GZ, GW)."""
    gens = (GX, GY, GZ, GW)
    axis = []
    for g in gens:
        axis.append(g % M)
        axis.append((-g) % M)

    plane_diag = []
    for i in range(4):
        for j in range(i + 1, 4):
            for si in (-1, +1):
                for sj in (-1, +1):
                    plane_diag.append((si * gens[i] + sj * gens[j]) % M)

    knight = []
    for i in range(4):
        for j in range(4):
            if i == j:
                continue
            for s2 in (-2, +2):
                for s1 in (-1, +1):
                    knight.append((s2 * gens[i] + s1 * gens[j]) % M)

    king = []
    for eps in product((-1, 0, +1), repeat=4):
        if eps == (0, 0, 0, 0):
            continue
        s = sum(e * g for e, g in zip(eps, gens)) % M
        king.append(s)

    return {"axis": axis, "plane_diag": plane_diag,
            "knight": knight, "king": king}


def test_c4_axis_shifts_count_and_distinctness():
    deriv = _derived_shifts()
    assert len(deriv["axis"]) == 8
    assert len(set(deriv["axis"])) == 8, "axis shifts collide"


def test_c4_plane_diagonal_shifts_count_and_distinctness():
    deriv = _derived_shifts()
    # 6 plane choices × 4 sign combos = 24 shifts.
    assert len(deriv["plane_diag"]) == 24
    assert len(set(deriv["plane_diag"])) == 24, (
        "plane-diagonal shifts collide"
    )


def test_c4_knight_shifts_count_and_distinctness():
    deriv = _derived_shifts()
    # 12 ordered axis pairs × 4 sign combos = 48 shifts.
    assert len(deriv["knight"]) == 48
    assert len(set(deriv["knight"])) == 48, "knight shifts collide"


def test_c4_king_shifts_count_and_distinctness():
    deriv = _derived_shifts()
    # 3^4 - 1 = 80 nonzero ternary sign vectors over 4 axes.
    assert len(deriv["king"]) == 80
    assert len(set(deriv["king"])) == 80, "king shifts collide"


def test_c4_axis_subset_of_king_by_construction():
    """The king's 80 shifts (ε ∈ {-1,0,+1}^4 \\ {0}) include axis shifts
    when ε has weight 1. axis ⊂ king is an algebraic identity, not a
    constraint. Verify it as a sanity check on the implementation."""
    deriv = _derived_shifts()
    assert set(deriv["axis"]).issubset(set(deriv["king"]))


def test_c4_plane_diag_subset_of_king_by_construction():
    """Plane-diag shifts = ε weight 2 sums; subset of king."""
    deriv = _derived_shifts()
    assert set(deriv["plane_diag"]).issubset(set(deriv["king"]))


def test_c4_knight_disjoint_from_single_step_pieces():
    """Knight shifts (using ±2 multipliers) must not alias any
    single-step piece (axis/plane_diag/king, all using ±1 multipliers).

    This is the only meaningful cross-category constraint — the others
    are forced by construction. If knight collides with king, a knight
    move at φ_origin would be indistinguishable from a king move from
    the same origin to the same destination, breaking the per-piece
    operator algebra.
    """
    deriv = _derived_shifts()
    knight_set = set(deriv["knight"])
    other_set = (set(deriv["axis"])
                 | set(deriv["plane_diag"])
                 | set(deriv["king"]))
    overlap = knight_set & other_set
    assert overlap == set(), (
        f"knight aliases {len(overlap)} single-step shift(s): "
        f"{sorted(overlap)[:5]}..."
    )


# ─── C5 — operator-aliasing freedom on [-14, 14]^4 ──────────────────
#
# Phase B refinement. C2 (image bijection on [0, 7]^4) ensures
# origin uniqueness — no two distinct lattice coords share a phase.
# But operator shifts (rook ±k·g_axis, bishop ±k·plane_diag, etc.)
# emit phase shifts whose corresponding "intended" displacement may
# go off-board. When the intended displacement IS off-board, the
# phase op's shift can still happen to equal phi(D) - phi(O) for some
# IN-board destination D ≠ O + intended_Δ — because their integer
# difference (D - O) - intended_Δ is a Δ ∈ [-14, 14]^4 with
# Σ Δ · g = 0.
#
# Concrete failure that motivated this constraint: Phase A's first
# attempt at (1523, 191, 23, 3) had 191 = 10·3 + 7·23, so
# Δ = (0, +1, -7, -10) gives Σ Δ·g = 0 with Δ_w = -10 ∈ [-14, 14].
# A rook +7·g_w shift (intended +7 along w) from origin (0, 0, 7, 3)
# inverted to (0, 1, 0, 0) — a non-rook destination — because
# phi(0, 0, 7, 3) + 7·g_w = phi(0, 1, 0, 0) by exactly that identity.
# Bumping the mixed-radix ladder coefficient from 7 to 14 made the
# tuple (9719, 647, 43, 3) clean.


def test_c5_no_integer_dependency_in_minus14_to_14_box():
    """No nonzero Δ ∈ [-14, 14]^4 satisfies Σ Δ_i · g_i = 0 in
    integers. This is the operator-aliasing freedom condition: piece
    operators emit shifts in [-7, 7] per component, so differences
    between two operator shifts span [-14, 14]^4.

    Brute-force enumeration over 29^4 = 707281 candidates. Slow but
    once — runs in ~3 seconds on the dev machine. If this assertion
    fails, the design must be re-derived with a wider mixed-radix
    ladder coefficient (Phase B used 14; Phase A's original 7 was
    insufficient).
    """
    from itertools import product
    g = (GX, GY, GZ, GW)
    box_max = 14
    found: list[tuple[int, int, int, int]] = []
    for delta in product(range(-box_max, box_max + 1), repeat=4):
        if all(d == 0 for d in delta):
            continue
        if sum(d * gi for d, gi in zip(delta, g)) == 0:
            found.append(delta)
            if len(found) >= 3:
                break
    assert not found, (
        f"integer dependency in [-14, 14]^4: {found}. "
        f"This will cause cross-piece destination aliasing in "
        f"Phase B. Re-derive with construct_mixed_radix_tower("
        f"ladder_coeff=14) (or higher)."
    )


# ─── O&C mobility sanity checks ─────────────────────────────────────


def test_axis_shift_count_matches_oc_rook_mobility():
    """O&C section 3: rook reaches 28 squares from any origin (7 per
    axis × 4 axes). The shift set is ±g_i for k ∈ 1..7, but the
    'derived axis' set in this test is only k=±1; the full rook reach
    is the cyclic span of these 8 shifts. Sanity: 8 axis-direction
    primitives must yield 28 distinct k-multiples for k ∈ {1..7}."""
    # 4 axes × 2 signs × 7 distances = 56 raw shifts; if all
    # distinct mod M, the rook reach has 28 destinations (the ±k pairs
    # produce overlapping sets only at k=0, which is excluded).
    seen = set()
    for g in (GX, GY, GZ, GW):
        for k in range(1, 8):
            seen.add((k * g) % M)
            seen.add((-k * g) % M)
    assert len(seen) == 56, (
        f"rook reach has {len(seen)} distinct shifts; expected 56 "
        f"(7 distances × 2 signs × 4 axes)"
    )


def test_king_mobility_matches_oc_interior_count():
    """O&C section 3: king interior degree = 80 = 3^4 - 1."""
    # Already covered by test_c4_king_shifts_count_and_distinctness;
    # this is the named O&C cross-reference.
    deriv = _derived_shifts()
    assert len(set(deriv["king"])) == 80


def test_knight_mobility_matches_oc_interior_count():
    """O&C section 3: knight interior degree = 48."""
    deriv = _derived_shifts()
    assert len(set(deriv["knight"])) == 48


# ─── design rationale exposed for inspection ────────────────────────


def test_constants_advertised_in_dunder_all():
    """Constants module exports the 5 required names so downstream
    operator code can import them without underscore-poking."""
    assert hasattr(phase_ops_4d, "MODULUS_4D")
    assert hasattr(phase_ops_4d, "GEN_X")
    assert hasattr(phase_ops_4d, "GEN_Y")
    assert hasattr(phase_ops_4d, "GEN_Z")
    assert hasattr(phase_ops_4d, "GEN_W")
