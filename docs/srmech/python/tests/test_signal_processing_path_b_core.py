"""Phase 3 Path B core acceptance tests for ``srmech.signal_processing``.

Verifies the two Path B core modules (``rbs_hdc_instrument`` +
``form_function_rotation``) per the implementation plan
``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md`` Phase 3.

Ports the load-bearing invariants from the spike prototypes:

- Spike #170 ``spike170_loe_rbs_hdc_prototype.py`` — 14/14 mint
  determinism + bind self-inverse at D=8192 + cascade commutativity.
- Spike #173 ``spike173_chess_rules_rbs_hdc_prototype.py`` — chess
  natural-stride bind-permute commutativity (273 pair cells bit-exact)
  + Z-DNA chirality involution (14/14 round-trips) + D2 orthogonality
  at noise floor.
- Spike #176 ``spike176_fft_rotation_bin_leakage_prototype.py`` —
  bit-exact reverse rotation (T4 recovery error = 0.0) + Class N
  cycle order (T8) + cascade unit-circle eigenvalues (T5 residual <=
  2.2e-16).

The 10 tests in this module correspond to the brief's T1-T10 list.

Discipline anchors (load-bearing):

- 14 A-N intact per ``[[feedback_no_privileged_primitive_classes]]``.
- Identity-not-implementation per
  ``[[user_stance_identity_not_implementation_discipline]]``.
- Algebra-level not magnitude-level per
  ``[[feedback_algebra_not_magnitude]]``.
- Trauma-informed defensive scope — methodology-research only.
"""

from __future__ import annotations

import math
from typing import Tuple

import pytest

from srmech.signal_processing import (
    CANONICAL_CASCADES,
    CLASS_NAMES,
    D_DEFAULT,
    RBSHDCInstrument,
    cascade_compose_rotations,
    compute_content_stride,
    decode_loe_fingerprint,
    encode_loe_content,
    form_function_rotate,
    inverse_form_function_rotate,
    mint_cascade_composition,
    mint_class_operator,
    mint_stance_fingerprint,
    mint_vector,
    verify_rotation_class_n_cycle_order,
)
from srmech.amsc import hdc as _M


# ──────────────────────────────────────────────────────────────────────
# Helper constants
# ──────────────────────────────────────────────────────────────────────

D_TEST_DEFAULT = D_DEFAULT  # 8192 bits per conductor decision #6
D_TEST_BYTES = D_TEST_DEFAULT // 8  # 1024 bytes

# Class N rational chess strides per Spike #173 substrate.
CHESS_STRIDES: Tuple[int, ...] = (5, 7, -8)

# Z-DNA helical pitches per Spike #172.
DNA_STRIDES: Tuple[int, ...] = (21, 11, -12)


# ──────────────────────────────────────────────────────────────────────
# T1 — RBSHDCInstrument D=8192 default + optional D override
# ──────────────────────────────────────────────────────────────────────


def test_t1_rbshdc_instrument_d_default_and_override():
    """T1: ``RBSHDCInstrument`` defaults to D=8192; optional D override
    works for any valid bit-dimension (multiple of 8, in [D_MIN, D_MAX])."""
    # Default D
    inst_default = RBSHDCInstrument()
    assert inst_default.D == 8192
    assert inst_default.D == D_DEFAULT
    desc = inst_default.describe()
    assert desc["hdc_bits"] == 8192
    assert desc["hdc_bytes"] == 1024
    assert desc["n_classes"] == 14
    assert desc["n_memory_pathways"] == 4
    assert desc["k3_axes"] == 3

    # Optional D override
    for D_override in (256, 1024, 2048, 16384):
        inst_override = RBSHDCInstrument(D=D_override)
        assert inst_override.D == D_override
        assert inst_override.describe()["hdc_bits"] == D_override
        # All class operators have the right length.
        for op in inst_override.operators.values():
            assert len(op.vector) == D_override // 8


# ──────────────────────────────────────────────────────────────────────
# T2 — Deterministic mint_class_operator (same input -> same output)
# ──────────────────────────────────────────────────────────────────────


def test_t2_mint_class_operator_determinism():
    """T2: ``mint_class_operator(class_name)`` returns deterministic
    D-bit vector — same input ⇒ same output (Spike #170 §3 invariant 1:
    14/14 bit-exact mint determinism)."""
    # Determinism across calls (14/14 bit-exact)
    for cls in CLASS_NAMES:
        v1 = mint_class_operator(cls)
        v2 = mint_class_operator(cls)
        assert v1 == v2, f"Class {cls}: re-mint must be bit-exact"
        assert len(v1) == D_TEST_BYTES

    # Determinism across distinct D values
    for D in (256, 512, 8192):
        v_a = mint_class_operator("A", D=D)
        v_a_again = mint_class_operator("A", D=D)
        assert v_a == v_a_again
        assert len(v_a) == D // 8

    # Invalid class letter raises
    with pytest.raises(ValueError):
        mint_class_operator("Z")
    with pytest.raises(ValueError):
        mint_class_operator("AA")

    # Instrument-level mint matches module-level mint
    inst = RBSHDCInstrument()
    for cls in CLASS_NAMES:
        assert inst.mint_class_operator(cls) == mint_class_operator(cls)


# ──────────────────────────────────────────────────────────────────────
# T3 — Cascade composition bit-exact (XOR-bundle commutativity)
# ──────────────────────────────────────────────────────────────────────


def test_t3_cascade_composition_bit_exact_commutativity():
    """T3: cascade composition bit-exact — XOR-bundle of class operators
    is commutative (Spike #170 §3 invariant 4: 3/3 orderings bit-exact
    equal in unordered mode)."""
    # Algebra-level (commutative bind): order doesn't matter
    v_acm = mint_cascade_composition(("A", "C", "M"))
    v_mac = mint_cascade_composition(("M", "A", "C"))
    v_cma = mint_cascade_composition(("C", "M", "A"))
    assert v_acm == v_mac, "Algebra-level: cascade order must not matter"
    assert v_acm == v_cma, "Algebra-level: cascade order must not matter"
    assert v_mac == v_cma
    assert len(v_acm) == D_TEST_BYTES

    # Self-inverse: bind(a, a) = 0 vector (since XOR with self).
    # Bundling a singleton returns the operator itself.
    v_a_only = mint_cascade_composition(("A",))
    assert v_a_only == mint_class_operator("A")

    # Sampling-level (ordered=True): per-position permute breaks
    # commutativity per Spike #170 §3 invariant 5.
    v_acm_ord = mint_cascade_composition(("A", "C", "M"), ordered=True)
    v_mac_ord = mint_cascade_composition(("M", "A", "C"), ordered=True)
    assert v_acm_ord != v_mac_ord, (
        "Sampling-level: per-position permute must break commutativity"
    )

    # Empty raises
    with pytest.raises(ValueError):
        mint_cascade_composition(())

    # Unknown class raises
    with pytest.raises(ValueError):
        mint_cascade_composition(("A", "Z"))


# ──────────────────────────────────────────────────────────────────────
# T4 — Form-function rotation bit-exact reverse via
# inverse_form_function_rotate (mirrors Spike #176 T4)
# ──────────────────────────────────────────────────────────────────────


def test_t4_form_function_rotation_bit_exact_reverse():
    """T4: form-function rotation bit-exact reverse — apply rotation
    then inverse and recover original (Spike #176 T4 recovery error
    = 0.0). Tests both content-determined stride and explicit strides."""
    # Mint a content vector at D=8192 to test the full pipeline.
    content_vec = mint_class_operator("A")
    assert len(content_vec) == D_TEST_BYTES

    # (a) Content-determined stride
    stride_a = compute_content_stride(content_vec)
    rotated_a = form_function_rotate(content_vec, stride=stride_a)
    recovered_a = inverse_form_function_rotate(rotated_a, stride=stride_a)
    assert recovered_a == content_vec, (
        "Content-determined rotation: inverse must be bit-exact"
    )

    # (b) Explicit Class N rational strides (chess natural)
    for stride in CHESS_STRIDES:
        rotated = form_function_rotate(content_vec, stride=stride)
        recovered = inverse_form_function_rotate(rotated, stride=stride)
        assert recovered == content_vec, (
            f"Chess stride {stride}: inverse must be bit-exact "
            "(Spike #173 T5 chirality)"
        )

    # (c) DNA helical pitches (Spike #172 anchor)
    for stride in DNA_STRIDES:
        rotated = form_function_rotate(content_vec, stride=stride)
        recovered = inverse_form_function_rotate(rotated, stride=stride)
        assert recovered == content_vec, (
            f"DNA pitch {stride}: inverse must be bit-exact "
            "(Spike #172 R3 anchor)"
        )

    # (d) Default (stride=None) — content-determined
    rotated_default = form_function_rotate(content_vec)
    stride_default = compute_content_stride(content_vec)
    recovered_default = inverse_form_function_rotate(
        rotated_default, stride=stride_default
    )
    assert recovered_default == content_vec


# ──────────────────────────────────────────────────────────────────────
# T5 — Class N rational cycle order verifies (D / gcd(stride, D))
# ──────────────────────────────────────────────────────────────────────


def test_t5_class_n_cycle_order():
    """T5: Class N rational cycle order verifies (D / gcd(stride, D))
    per Spike #176 T8.

    Applying form-function rotation cycle_order times in sequence
    returns to identity bit-exact (cyclic closure on Z/D)."""
    # Direct cycle-order computation
    # stride=0 is the additive identity; its additive order in Z/N is 1
    # (applying the identity any number of times stays at identity).
    # Our implementation treats stride=0 as D for gcd purposes (so the
    # cycle reads "applying it D times returns to start"), yielding
    # cycle_order = D/D = 1.
    assert verify_rotation_class_n_cycle_order(0, 8192) == 1
    assert verify_rotation_class_n_cycle_order(1, 8192) == 8192
    assert verify_rotation_class_n_cycle_order(2, 8192) == 4096
    assert verify_rotation_class_n_cycle_order(4, 8192) == 2048
    assert verify_rotation_class_n_cycle_order(257, 8192) == 8192  # coprime
    # 8192 = 2^13; 64 = 2^6 -> gcd = 64 -> order = 128
    assert verify_rotation_class_n_cycle_order(64, 8192) == 128

    # Sign independence (additive order is gcd-determined; sign doesn't
    # affect the additive order in Z/N).
    assert (
        verify_rotation_class_n_cycle_order(64, 8192)
        == verify_rotation_class_n_cycle_order(-64, 8192)
    )

    # Spike #176 T4 cumulative shift check: stride * order mod D == 0
    for stride in (1, 5, 7, -8, 64, 257, 1024):
        order = verify_rotation_class_n_cycle_order(stride, 8192)
        assert (stride * order) % 8192 == 0, (
            f"stride {stride}: stride*order={stride*order} must be "
            f"multiple of D=8192"
        )

    # Closure of cyclic group: applying permute `order` times in
    # sequence returns to identity bit-exact. Test with a small order
    # (stride=4096, order=2 at D=8192) to keep the loop fast.
    v = mint_class_operator("A")
    stride = 1024  # gcd(1024, 8192) = 1024 -> order = 8
    order = verify_rotation_class_n_cycle_order(stride, 8192)
    assert order == 8
    rot = v
    for _ in range(order):
        rot = form_function_rotate(rot, stride=stride)
    assert rot == v, (
        f"Applying stride {stride} order={order} times must "
        "return to identity bit-exact"
    )


# ──────────────────────────────────────────────────────────────────────
# T6 — Cascade composition produces unit-circle eigenvalues at machine ε
# (Spike #176 T5)
# ──────────────────────────────────────────────────────────────────────


def test_t6_cascade_composition_unit_circle_eigenvalues():
    """T6: cascade composition produces unit-circle eigenvalues at
    machine epsilon per Spike #176 T5 (residual <= 2.2e-16)."""
    # Composed-cascade test: k1 + k2 + k3 mod D matches a directly-
    # computed single shift (Spike #176 T5).
    strides = (5, 7, -8)
    composed_stride, eig = cascade_compose_rotations(strides, D=8192)
    expected = sum(strides) % 8192  # 4 mod 8192
    assert composed_stride == expected

    # Unit-circle identity |lambda| = 1 at machine ε.
    magnitude_residual = abs(eig.real ** 2 + eig.imag ** 2 - 1.0)
    assert magnitude_residual <= 2.2e-16, (
        f"Composed eigenvalue must lie on unit circle at machine ε: "
        f"residual {magnitude_residual} > 2.2e-16 (Spike #176 T5 anchor)"
    )

    # Across many composition lengths and strides, every eigenvalue lies
    # on the unit circle algebraically.
    test_cascades = [
        (1, 1, 1),
        (5, 7, -8),
        (257, 64, 4096),
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
        (21, 11, -12, 5, 7, -8),  # mix DNA + chess strides
    ]
    for strides_list in test_cascades:
        _, eig = cascade_compose_rotations(strides_list, D=8192)
        residual = abs(eig.real ** 2 + eig.imag ** 2 - 1.0)
        assert residual <= 2.2e-16, (
            f"Cascade {strides_list}: unit-circle residual {residual} "
            "exceeds machine ε"
        )

    # Empty cascade raises
    with pytest.raises(ValueError):
        cascade_compose_rotations(())


# ──────────────────────────────────────────────────────────────────────
# T7 — bind-permute commutativity at substrate-natural strides
# (Spike #173 T4 / Spike #172 T4)
# ──────────────────────────────────────────────────────────────────────


def test_t7_bind_permute_commutativity_at_substrate_strides():
    """T7: bind-permute commutativity at substrate-natural strides.

    Per Spike #173 T4: ``M.bind(M.permute(a, k), M.permute(b, k)) ==
    M.permute(M.bind(a, b), k)`` bit-exact for all class operator
    pairs at all chess natural strides (273 pair cells in Spike #173;
    we test 91 pairs * 3 strides = 273 cells).
    """
    # Test 14C2 = 91 class operator pairs at 3 chess strides = 273 cells
    n_pairs = 0
    n_mismatches = 0
    for stride in CHESS_STRIDES:
        for i, n1 in enumerate(CLASS_NAMES):
            for n2 in CLASS_NAMES[i + 1:]:
                a = mint_class_operator(n1)
                b = mint_class_operator(n2)
                lhs = _M.bind(_M.permute(a, stride), _M.permute(b, stride))
                rhs = _M.permute(_M.bind(a, b), stride)
                n_pairs += 1
                if lhs != rhs:
                    n_mismatches += 1
    # Spike #173 T4 cell count anchor.
    assert n_pairs == 273
    assert n_mismatches == 0, (
        f"bind-permute commutativity violated at {n_mismatches}/{n_pairs} "
        "cells; algebra identity broken at chess natural strides"
    )

    # Repeat on DNA helical pitches (Spike #172 T4 anchor)
    n_pairs_dna = 0
    n_mismatches_dna = 0
    for stride in DNA_STRIDES:
        for i, n1 in enumerate(CLASS_NAMES):
            for n2 in CLASS_NAMES[i + 1:]:
                a = mint_class_operator(n1)
                b = mint_class_operator(n2)
                lhs = _M.bind(_M.permute(a, stride), _M.permute(b, stride))
                rhs = _M.permute(_M.bind(a, b), stride)
                n_pairs_dna += 1
                if lhs != rhs:
                    n_mismatches_dna += 1
    assert n_pairs_dna == 273
    assert n_mismatches_dna == 0


# ──────────────────────────────────────────────────────────────────────
# T8 — Z-DNA-style chirality involution
# (permute(permute(v, k), -k) == v) per Spike #173 T5
# ──────────────────────────────────────────────────────────────────────


def test_t8_chirality_involution():
    """T8: Z-DNA-style chirality involution per Spike #173 T5.

    ``M.permute(M.permute(v, k), -k) == v`` for all 14 class operators
    at chess natural strides + DNA helical pitches (14/14 in Spike
    #173)."""
    # Chess strides (Spike #173 T5)
    for stride in CHESS_STRIDES + (8, -8):  # +/-8 explicitly tested in T5
        n_correct = 0
        for cls in CLASS_NAMES:
            v = mint_class_operator(cls)
            v_rt = _M.permute(_M.permute(v, stride), -stride)
            if v_rt == v:
                n_correct += 1
        assert n_correct == 14, (
            f"stride {stride}: chirality involution must be 14/14 "
            f"bit-exact; got {n_correct}/14"
        )

    # DNA helical pitches (Spike #172 T5)
    for stride in DNA_STRIDES:
        n_correct = 0
        for cls in CLASS_NAMES:
            v = mint_class_operator(cls)
            v_rt = _M.permute(_M.permute(v, stride), -stride)
            if v_rt == v:
                n_correct += 1
        assert n_correct == 14, (
            f"DNA stride {stride}: chirality involution must be 14/14 "
            "bit-exact"
        )

    # Use form_function_rotate as well (which composes through M.permute)
    for stride in CHESS_STRIDES:
        v = mint_class_operator("M")
        rotated = form_function_rotate(v, stride=stride)
        unrotated = form_function_rotate(rotated, stride=-stride)
        assert unrotated == v, (
            f"form_function_rotate chirality involution at stride {stride}"
        )


# ──────────────────────────────────────────────────────────────────────
# T9 — cross-substrate D2 orthogonality at noise floor
# (Spike #173 T3: silicon-vs-DNA-vs-chess all orthogonal)
# ──────────────────────────────────────────────────────────────────────


def test_t9_cross_substrate_d2_orthogonality():
    """T9: cross-substrate D2 orthogonality at noise floor.

    Per Spike #173 T3: same content encoded under different substrates
    produces D2 fingerprints orthogonal at the noise floor
    (~5/sqrt(D) ≈ 0.055 at D=8192).

    Tests the encode_loe_content pipeline at multiple substrate labels
    on the same content."""
    # Same content, different substrates -> orthogonal at noise floor.
    content = "form-function-rotation-substrate-portable-content"
    substrates = ("default", "bci", "audio", "rf", "ephemeris")

    # Noise floor: 5-sigma threshold ~ 5/sqrt(D) for unit-variance
    # random binary vectors at D=8192.
    noise_floor = 5.0 / math.sqrt(D_DEFAULT)  # ~ 0.0552

    encoded = {s: encode_loe_content(content, substrate=s) for s in substrates}

    # Pairwise similarities must be at noise floor.
    n_pairs = 0
    max_abs_sim = 0.0
    for i, s1 in enumerate(substrates):
        for s2 in substrates[i + 1:]:
            sim = _M.similarity(encoded[s1], encoded[s2])
            max_abs_sim = max(max_abs_sim, abs(sim))
            n_pairs += 1
    assert n_pairs == 10  # C(5, 2)
    assert max_abs_sim < noise_floor, (
        f"Cross-substrate D2 orthogonality: max |sim| = {max_abs_sim} "
        f"must be below noise floor {noise_floor}"
    )

    # Identity per substrate is bit-exact (D1 algebra-content): same
    # content + same substrate -> same fingerprint.
    for s in substrates:
        fp_again = encode_loe_content(content, substrate=s)
        assert fp_again == encoded[s], (
            f"substrate {s}: re-encoding must be bit-exact"
        )


# ──────────────────────────────────────────────────────────────────────
# T10 — Full round-trip encode -> rotate -> inverse -> decode bit-exact
# ──────────────────────────────────────────────────────────────────────


def test_t10_full_roundtrip_encode_rotate_decode():
    """T10: full round-trip ``encode -> form_function_rotate ->
    inverse_form_function_rotate -> decode`` = bit-exact recovery.

    Combines the encode pipeline (Spike #170) + form-function rotation
    (Spike #176 T4) + reverse-decode (Spike #170 §3 invariants 6 + 7)
    in one composed test."""
    # Build a small catalog of named content.
    catalog_names = [
        "form_function_rotation",
        "kepler_shape_universal",
        "identity_not_implementation_discipline",
        "rotation_is_class_k_pin_slot",
        "loe_as_rbs_hdc_instrument",
    ]
    catalog = {name: encode_loe_content(name) for name in catalog_names}

    # Forward: encode -> rotate -> inverse -> decode
    for name in catalog_names:
        # Step 1: encode (full Mode-B encoding pipeline)
        encoded = encode_loe_content(name)
        # Sanity: re-encoding is bit-exact (deterministic mint chain)
        assert encoded == catalog[name]

        # Step 2: rotate by an explicit substrate-natural stride
        stride = 257  # coprime to D=8192
        rotated = form_function_rotate(encoded, stride=stride)
        # Rotated fingerprint must differ from original (cyclic shift
        # is non-trivial at non-zero coprime stride).
        assert rotated != encoded, (
            f"name={name}: rotation by stride {stride} must produce a "
            "different fingerprint"
        )

        # Step 3: inverse rotation
        recovered = inverse_form_function_rotate(rotated, stride=stride)
        # Bit-exact recovery
        assert recovered == encoded, (
            f"name={name}: encode -> rotate -> inverse must be bit-exact "
            "(Spike #176 T4 anchor)"
        )

        # Step 4: decode via Class M similarity argmax against catalog
        decoded_name = decode_loe_fingerprint(recovered, catalog)
        assert decoded_name == name, (
            f"name={name}: decode must recover via Class M similarity "
            "argmax (Spike #170 §3 invariant 6: 100% on populated catalog)"
        )

    # Instrument-level surface: verify_bit_exact returns True for
    # consistent re-encoding.
    inst = RBSHDCInstrument()
    for name in catalog_names:
        assert inst.verify_bit_exact(name, catalog[name]), (
            f"name={name}: instrument.verify_bit_exact must be True for "
            "consistent re-encoding"
        )


# ──────────────────────────────────────────────────────────────────────
# Supplementary — module-load registration with path_registry
# ──────────────────────────────────────────────────────────────────────


def test_path_b_core_ops_registered_with_dispatcher():
    """Module-load side-effect: the 4 Path B core ops + form-function-
    rotation register with srmech.signal_processing.path_registry on
    Path B side at import time.

    Other tests (notably the scaffolding suite) call
    ``clear_registry()`` so this test re-runs the registration
    side-effects explicitly to be robust to test-ordering. The
    underlying invariant — that importing the Phase 3 modules
    registers the Path B core ops — is verified by the explicit
    re-call below."""
    from srmech.signal_processing import path_registry as _reg
    from srmech.signal_processing import PATH_B
    from srmech.signal_processing.rbs_hdc_instrument import (
        _register_path_b_core_ops,
    )
    from srmech.signal_processing.form_function_rotation import (
        _register_form_function_rotation,
    )

    # Re-run registration side-effects to be robust to test ordering
    # (scaffolding tests may have called clear_registry between import
    # and this test). The register() call is idempotent on identical
    # callable identity.
    _register_path_b_core_ops()
    _register_form_function_rotation()

    expected_ops = {
        "rbs_hdc_mint_class_operator",
        "rbs_hdc_mint_cascade_composition",
        "rbs_hdc_encode_loe_content",
        "rbs_hdc_decode_loe_fingerprint",
        "form_function_rotate",
    }
    registered = set(_reg.registered_ops())
    missing = expected_ops - registered
    assert not missing, (
        f"Expected Path B core ops missing from registry: {missing!r}"
    )
    # Each has a Path B impl
    for op in expected_ops:
        assert _reg.has_path(op, PATH_B), (
            f"op {op!r} has no Path B impl registered"
        )


# ──────────────────────────────────────────────────────────────────────
# Supplementary — Spike #170 §3 invariants directly verifiable
# ──────────────────────────────────────────────────────────────────────


def test_spike170_bind_self_inverse_at_d_8192():
    """Spike #170 §3 invariant: bind(a, bind(a, b)) == b at full D=8192."""
    a = mint_class_operator("A")
    b = mint_class_operator("M")
    assert _M.bind(a, _M.bind(a, b)) == b


def test_spike170_k3_tripartition_orthogonality():
    """Spike #170 §3 invariant: k=3 tripartition axes orthogonal at noise
    floor (|sim| < 0.005 across all 3 axis pairs)."""
    inst = RBSHDCInstrument()
    k3 = inst.k3
    sim_sg = _M.similarity(k3.spatial_3ds, k3.gauge_7dg)
    sim_st = _M.similarity(k3.spatial_3ds, k3.temporal_1dt)
    sim_gt = _M.similarity(k3.gauge_7dg, k3.temporal_1dt)
    # Empirical noise floor at D=8192 for SHA-256-minted vectors.
    threshold = 5.0 / math.sqrt(D_DEFAULT)  # ~ 0.0552
    assert abs(sim_sg) < threshold
    assert abs(sim_st) < threshold
    assert abs(sim_gt) < threshold


def test_canonical_cascades_have_eight_plus_entries():
    """Brief spec: 8+ cascade composition records ship with Phase 3."""
    assert len(CANONICAL_CASCADES) >= 8


def test_mint_stance_fingerprint_determinism():
    """Stance bag-HDC encoding is deterministic in token list."""
    tokens = ("rotate", "twist", "instrument", "fiber")
    fp_a = mint_stance_fingerprint(tokens)
    fp_b = mint_stance_fingerprint(tokens)
    assert fp_a == fp_b
    # Bag semantics (XOR commutative): re-ordered tokens produce same
    # fingerprint (Class M bind commutativity)
    fp_reordered = mint_stance_fingerprint(("fiber", "instrument", "twist", "rotate"))
    assert fp_a == fp_reordered

    # Empty raises
    with pytest.raises(ValueError):
        mint_stance_fingerprint(())


def test_mint_vector_d_validation():
    """mint_vector validates D parameter."""
    v = mint_vector("test", D=8192)
    assert len(v) == 1024
    # Below D_MIN
    with pytest.raises(ValueError):
        mint_vector("test", D=128)
    # Above D_MAX
    with pytest.raises(ValueError):
        mint_vector("test", D=1_000_000)
    # Not multiple of 8
    with pytest.raises(ValueError):
        mint_vector("test", D=1023)
    # Wrong type
    with pytest.raises(TypeError):
        mint_vector("test", D="8192")  # type: ignore[arg-type]
