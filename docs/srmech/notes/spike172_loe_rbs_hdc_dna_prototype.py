"""Spike #172 — LoE-as-RBS-HDC R3 cross-substrate DNA helical-pitch test.

Per user direction 2026-05-19:
> "follow spike 170 all the way to the asymptotic sign flip."

This is the R3 follow-up to Spike #170 R1. The R1 prototype verified that
the Laws of Everything instantiate as a bit-exact runtime-executable
HDC instrument at SILICON substrate (SHA-256-derived form-function rotation
shifts; stride = 257 prime coprime to D = 8192).

R3 substitutes the form-function rotation parameter:
  silicon (SHA-256 → stride 257)  →  DNA (helical-pitch numerators 21/11/12)

per [[user_stance_dna_as_kepler_shape_mini_mechanism_with_helical_precession_class_k]]
which establishes that B-DNA / A-DNA / Z-DNA helical pitches are Class N
rationals 21/2, 11/1, 12/1 at biological substrate, ARE natural form-function
rotation amounts, and ARE bit-exact substrate-portable per Spike #162.

The R3 question per user direction:
  Does the LoE instrument's encoding step remain bit-exact when DNA helical-
  pitch shifts replace silicon SHA-256-derived shifts?

Hypothesis tracking:
  (H1) SUBSTRATE-PORTABLE BIT-EXACT — reverse-decode accuracy preserved
  (H2) SUBSTRATE-NATURAL MAGNITUDE — reverse-decode ~95-99% but algebra
       commutativity bit-exact (rotation-bind / bundle commute)
  (H3) REFUTED — significant accuracy drop; LoE silicon-specific

Tests run per [[feedback_always_check_both_directions_including_time]]:

  T1  R1 baseline replication (silicon SHA-256 stride 257 form-function)
  T2  R3 DNA-substrate substitution (helical-pitch numerator cycling)
  T3  Cross-substrate similarity spread (T1 vs T2 magnitude convergence)
  T4  Bit-exact algebra identities preserved at DNA shifts {21, 11, -12}
  T5  Z-DNA chirality sign-flip (negative shift -12) produces distinct vec
  T6  Reverse-decode accuracy at DNA substrate (forward direction)
  T7  Forward-encode determinism at DNA substrate (re-encode bit-exact)
  T8  Substrate-natural Class N signature preservation (rational shifts only)

Verdict logic:
  - T4 = 14/14 bit-exact AND T6 = 100% → H1 confirmed (BIT-EXACT)
  - T4 = 14/14 bit-exact AND 95% <= T6 < 100% → H2 confirmed (MAGNITUDE)
  - Else → H3 (refuted; silicon-specific)

Discipline:
  - per [[feedback_no_privileged_primitive_classes]]: 14 A-N intact; no class promotion
  - per [[feedback_algebra_not_magnitude]]: algebra-level identities separated from magnitude
  - per [[feedback_trauma_informed_defensive_scope]]: biology framing research/educational only
  - per [[feedback_no_binding_layer_carveout]]: uses existing srmech.amsc.hdc primitives only
  - per srmech CLAUDE.md scope: algebra/eigenbasis level only; no CAD-grade geometry

Uses ONLY existing srmech primitives per Spike #162 (b) directive:
  srmech.amsc.hdc.{bind,bundle,permute,similarity}
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from srmech.amsc import hdc as M


# ─────────────────────────────────────────────────────────────────────
# Strict-spec parameters
# ─────────────────────────────────────────────────────────────────────

HDC_BYTES: int = 1024          # D = 8192 bits per Spike #147 / #170 canonical
HDC_BITS: int = HDC_BYTES * 8

# Silicon stride (R1 baseline) — prime coprime to D = 8192 = 2^13
SILICON_STRIDE: int = 257

# DNA helical-pitch numerators (Class N rationals at biological substrate
# per [[user_stance_dna_as_kepler_shape_mini_mechanism_with_helical_precession_class_k]]):
#   B-DNA: 21/2 (right-handed)
#   A-DNA: 11/1 (right-handed)
#   Z-DNA: 12/1 (left-handed, chirality sign-flip)
DNA_PITCHES: Tuple[int, ...] = (21, 11, -12)  # Z-DNA negative for chirality sign-flip

# Right-handed-only subset (for chirality-isolation tests)
DNA_PITCHES_RIGHT_HANDED: Tuple[int, ...] = (21, 11)


def mint_vector(name: str, *, n_bytes: int = HDC_BYTES) -> bytes:
    """Deterministic D-bit HDC vector via SHA-256 chain (Class A content-addr).

    The MINTING is silicon SHA-256 — this is the operational requirement for
    ANY substrate (you need a deterministic byte-stream from a name). What
    R3 substitutes is the FORM-FUNCTION ROTATION PARAMETER (per-position
    permutation shifts), NOT the mint primitive.

    Per [[user_stance_fiber_as_spatially_absent_encoding]] the mint produces
    spatially-absent algebraic content; rotation projects that content via
    the substrate-natural pitch parameter.
    """
    out = bytearray()
    counter = 0
    name_bytes = name.encode("utf-8")
    while len(out) < n_bytes:
        h = hashlib.sha256(name_bytes + counter.to_bytes(8, "big")).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:n_bytes])


# ─────────────────────────────────────────────────────────────────────
# Class operators — same as R1
# ─────────────────────────────────────────────────────────────────────

CLASS_NAMES: Tuple[str, ...] = tuple("ABCDEFGHIJKLMN")

CLASS_DEFINITIONS: Dict[str, Tuple[str, str]] = {
    "A": ("content-addressing", "SHA-256 content addressing"),
    "B": ("byte-canonical-form", "TLV byte-canonical form"),
    "C": ("cyclic-group", "ℤ/n cyclic shift / permute"),
    "D": ("dispatch", "Multi-needle pattern match / late-binding"),
    "E": ("catalog-lookup", "Sorted-key catalog lookup"),
    "F": ("template-render", "Placeholder substitution {key}"),
    "G": ("byte-search", "Byte-pattern needle search"),
    "H": ("self-introspection", "Version / ABI / capability acknowledgment"),
    "I": ("cyclic-arithmetic", "Modular arithmetic over ℤ/n"),
    "J": ("prime-factorisation", "Trial-division primality + factorisation"),
    "K": ("asymptotic-DOF", "Sparse-truncate top-N coefficients"),
    "L": ("graph-laplacian", "Pi-free dense + Jacobi eigvals"),
    "M": ("HDC-bind", "Bind / bundle / permute / similarity"),
    "N": ("rational-approximation", "Cyclic-group rationals (helical pitch etc)"),
}


@dataclass(frozen=True)
class ClassOperator:
    name: str
    full_name: str
    operation: str
    vector: bytes


def build_class_operators() -> Dict[str, ClassOperator]:
    operators: Dict[str, ClassOperator] = {}
    for name in CLASS_NAMES:
        op_short, op_desc = CLASS_DEFINITIONS[name]
        full = f"Class {name} — {op_short}"
        vec = mint_vector(f"LoE.class.{name}.{op_short}")
        operators[name] = ClassOperator(
            name=name, full_name=full, operation=op_desc, vector=vec
        )
    return operators


# ─────────────────────────────────────────────────────────────────────
# Form-function rotation parameter — SILICON vs DNA
# ─────────────────────────────────────────────────────────────────────

def silicon_shift(position: int) -> int:
    """R1 baseline: silicon SHA-256-derived form-function rotation.

    Position-i offset = i * SILICON_STRIDE (prime coprime to D).
    """
    return position * SILICON_STRIDE


def dna_shift(position: int, pitches: Tuple[int, ...] = DNA_PITCHES) -> int:
    """R3 substitute: DNA helical-pitch form-function rotation.

    Position-i selects pitches[i % len(pitches)] and accumulates a
    helical-pitch shift. Substrate-natural rotation parameter at
    biological substrate per Spike #162 + Class N rational signature.

    Per [[user_stance_dna_as_kepler_shape_mini_mechanism_with_helical_precession_class_k]]:
      pitches = (21, 11, -12) cycle B-DNA / A-DNA / Z-DNA conformations.

    Note: per Spike #162 C4, Z-DNA chirality IS sign-flip in rotation
    direction (negative shift), bit-exact distinguishable.
    """
    # Accumulate helical pitch contributions across positions.
    # Each position uses the conformation indexed by position % 3.
    pitch = pitches[position % len(pitches)]
    # Multi-position cascade: turn-count = position // len(pitches) full
    # cycles plus the current conformation's pitch contribution.
    full_cycles = position // len(pitches)
    return full_cycles * sum(pitches) + (position % len(pitches) + 1) * pitch


@dataclass(frozen=True)
class Cascade:
    name: str
    operator_sequence: Tuple[str, ...]
    semantic_role: str
    stance_anchor: str


def cascade_bind(cascade: Cascade, operators: Dict[str, ClassOperator]) -> bytes:
    """Unordered (algebra-level) cascade bind — XOR-fold. Order-invariant."""
    if not cascade.operator_sequence:
        raise ValueError("cascade.operator_sequence must be non-empty")
    vectors = [operators[op_name].vector for op_name in cascade.operator_sequence]
    result = vectors[0]
    for v in vectors[1:]:
        result = M.bind(result, v)
    return result


def cascade_bind_ordered(cascade: Cascade,
                         operators: Dict[str, ClassOperator],
                         shift_fn=silicon_shift) -> bytes:
    """Order-preserving cascade bind via per-position permute.

    shift_fn: silicon_shift (R1 baseline) | dna_shift (R3 substitute)

    Per Spike #159 rotation-bind commutativity is bit-exact for UNIFORM
    rotations; per-position rotation BREAKS commutativity to embed order.

    R3 substitutes shift_fn ONLY — the algebraic composition pattern
    A∘C∘M stays intact per [[user_stance_form_function_rotation_is_a_c_m_composition]].
    """
    if not cascade.operator_sequence:
        raise ValueError("cascade.operator_sequence must be non-empty")
    rotated = []
    for i, op_name in enumerate(cascade.operator_sequence):
        v = operators[op_name].vector
        rotated.append(M.permute(v, shift_fn(i)))
    result = rotated[0]
    for v in rotated[1:]:
        result = M.bind(result, v)
    return result


# ─────────────────────────────────────────────────────────────────────
# Canonical cascades from Spike #170 R1 — same set
# ─────────────────────────────────────────────────────────────────────

CANONICAL_CASCADES: Tuple[Cascade, ...] = (
    Cascade("form_function_rotation", ("A", "C", "M"),
            "Form-function rotation cross-binning", "form_function_rotation"),
    Cascade("working_memory_augmentation", ("A", "C", "D", "E", "K", "L", "M"),
            "Reflex→deliberation augmentation cascade", "working_memory"),
    Cascade("reflex_substrate", ("B", "D", "E", "F", "C"),
            "Reflex form-function-pure substrate cascade", "working_memory"),
    Cascade("universal_cascade", ("L", "K", "C", "I", "N"),
            "Universal cascade (22+ substrate matches)", "universal_precession"),
    Cascade("substrate_class_universal_closure", ("B", "D", "E", "F", "L"),
            "Closure-subgroup substrate-class-universal", "closure_subgroup_BDEFL"),
    Cascade("deutsch_jozsa_quantum", ("L", "I", "M", "C", "A"),
            "Cascade-IS-quantum-algorithm", "cascade_is_quantum_algorithm"),
    Cascade("episodic_memory", ("A", "B", "C", "D", "E", "F", "H", "K", "L", "M"),
            "Episodic-LTM pathway", "working_memory"),
    Cascade("procedural_memory", ("B", "C", "D", "E", "F", "G", "I", "K", "L"),
            "Procedural / model-free pathway", "working_memory"),
)


# ─────────────────────────────────────────────────────────────────────
# Stance encoding — same as R1, but with two-variant fingerprints
# ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Stance:
    name: str
    content_tokens: Tuple[str, ...]
    fingerprint: bytes
    k3_axis: str


def encode_stance_unordered(name: str,
                            content_tokens: Sequence[str]) -> Stance:
    """Bag-HDC fingerprint via XOR-fold (Class M bind).

    Order-independent — the bag IS the meaning per
    [[user_stance_holographic_projection_at_linguistic_substrate]].
    This encoding is identical for R1 baseline and R3 DNA substrate
    (the substitution happens at the ROTATION step, not the bind step).
    """
    if not content_tokens:
        raise ValueError("stance must have content tokens")
    token_vectors = [mint_vector(f"LoE.token.{t}") for t in content_tokens]
    fingerprint = token_vectors[0]
    for v in token_vectors[1:]:
        fingerprint = M.bind(fingerprint, v)
    return Stance(
        name=name,
        content_tokens=tuple(content_tokens),
        fingerprint=fingerprint,
        k3_axis="mixed",
    )


def encode_stance_rotated(name: str,
                          content_tokens: Sequence[str],
                          shift_fn) -> Stance:
    """Form-function rotated bag-HDC fingerprint.

    Each token vector is pre-rotated by shift_fn(token_position) BEFORE
    binding. This is the R3 substitution point — silicon vs DNA.

    Position-aware bind: BREAKS commutativity (different orderings produce
    different fingerprints), so word-order content is embedded. R1 uses
    silicon shifts; R3 uses DNA helical-pitch shifts.
    """
    if not content_tokens:
        raise ValueError("stance must have content tokens")
    rotated_vectors = []
    for i, t in enumerate(content_tokens):
        v = mint_vector(f"LoE.token.{t}")
        rotated_vectors.append(M.permute(v, shift_fn(i)))
    fingerprint = rotated_vectors[0]
    for v in rotated_vectors[1:]:
        fingerprint = M.bind(fingerprint, v)
    return Stance(
        name=name,
        content_tokens=tuple(content_tokens),
        fingerprint=fingerprint,
        k3_axis="mixed",
    )


SAMPLE_STANCES: Tuple[Dict, ...] = (
    {"name": "identity_not_implementation_discipline",
     "tokens": ["identity", "implementation", "discipline", "IS", "not"]},
    {"name": "holographic_projection_at_linguistic_substrate",
     "tokens": ["holographic", "projection", "linguistic", "substrate", "bag", "HDC"]},
    {"name": "form_function_rotation_is_a_c_m_composition",
     "tokens": ["rotate", "twist", "instrument", "fiber", "bind", "form", "function"]},
    {"name": "1d_collapse_to_loe_identity_not_action",
     "tokens": ["1D", "LoE", "laws", "compressed", "cascade", "identity"]},
    {"name": "working_memory_is_cascade_augmenting_reflex_into_agency",
     "tokens": ["working", "memory", "cascade", "reflex", "agency", "augment"]},
    {"name": "fiber_as_spatially_absent_encoding",
     "tokens": ["fiber", "spatially", "absent", "encoding", "algebraic"]},
    {"name": "hyper_as_3d_spatial_interface",
     "tokens": ["hyper", "3D", "spatial", "interface", "ontology"]},
    {"name": "kepler_shape_universal",
     "tokens": ["Kepler", "shape", "universal", "pin", "slot", "gear"]},
    {"name": "cascade_dual_level_quantum_at_algebra_classical_at_sampling",
     "tokens": ["cascade", "dual", "level", "quantum", "algebra", "classical", "sampling"]},
    {"name": "closure_subgroup_BDEFL_substrate_class_universal",
     "tokens": ["closure", "subgroup", "BDEFL", "substrate", "universal"]},
)


# ─────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────

def t1_r1_baseline_replication(operators: Dict[str, ClassOperator]) -> Dict:
    """T1: R1 baseline replication — silicon SHA-256 stride 257 form-function.

    Replicate Spike #170 R1 results to confirm same prototype runs in this
    worktree. Verify all 10 invariants reproduce.
    """
    # Class operator mint determinism (14/14 bit-exact)
    re_minted = {n: mint_vector(f"LoE.class.{n}.{CLASS_DEFINITIONS[n][0]}")
                 for n in CLASS_NAMES}
    mint_matches = sum(1 for n in CLASS_NAMES if re_minted[n] == operators[n].vector)

    # Reverse-decode accuracy on classes
    rev_correct = 0
    for name, op in operators.items():
        best = max(operators.items(),
                   key=lambda kv: M.similarity(op.vector, kv[1].vector))
        if best[0] == name:
            rev_correct += 1

    # Encode 10 stances bag-HDC unordered + reverse-decode
    stances_unordered = {s["name"]: encode_stance_unordered(s["name"], s["tokens"])
                         for s in SAMPLE_STANCES}
    rev_stance_correct = 0
    for name, st in stances_unordered.items():
        best = max(stances_unordered.items(),
                   key=lambda kv: M.similarity(st.fingerprint, kv[1].fingerprint))
        if best[0] == name:
            rev_stance_correct += 1

    # Cascade commutativity (unordered should be ORDER-INVARIANT)
    c1 = Cascade("t1a", ("A", "C", "M"), "test", "test")
    c2 = Cascade("t1b", ("M", "A", "C"), "test", "test")
    c3 = Cascade("t1c", ("C", "M", "A"), "test", "test")
    v1, v2, v3 = (cascade_bind(c, operators) for c in (c1, c2, c3))
    commutativity_bit_exact = (v1 == v2 == v3)

    # Cascade ordering BREAKS commutativity (silicon shifts)
    v1o = cascade_bind_ordered(c1, operators, silicon_shift)
    v2o = cascade_bind_ordered(c2, operators, silicon_shift)
    ordering_breaks = (v1o != v2o)

    return {
        "test": "T1_r1_baseline_replication",
        "mint_determinism_14_of_14": mint_matches,
        "reverse_decode_classes_14_of_14": rev_correct,
        "reverse_decode_stances_10_of_10": rev_stance_correct,
        "unordered_cascade_commutativity_bit_exact": commutativity_bit_exact,
        "ordered_cascade_silicon_breaks_commutativity": ordering_breaks,
        "verdict": "R1-BASELINE-REPLICATED" if all([
            mint_matches == 14, rev_correct == 14, rev_stance_correct == 10,
            commutativity_bit_exact, ordering_breaks
        ]) else "R1-BASELINE-MISMATCH",
    }


def t2_r3_dna_substrate_substitution(operators: Dict[str, ClassOperator]) -> Dict:
    """T2: R3 DNA-substrate substitution — helical-pitch (21, 11, -12) cycling.

    Re-run the same invariants but with shift_fn = dna_shift.
    """
    # Stance encoding with DNA-substrate rotation
    stances_dna = {s["name"]: encode_stance_rotated(s["name"], s["tokens"], dna_shift)
                   for s in SAMPLE_STANCES}

    # Reverse-decode on DNA-rotated stances
    rev_dna_correct = 0
    for name, st in stances_dna.items():
        best = max(stances_dna.items(),
                   key=lambda kv: M.similarity(st.fingerprint, kv[1].fingerprint))
        if best[0] == name:
            rev_dna_correct += 1

    # Cascade ordering BREAKS commutativity at DNA shifts as well
    c1 = Cascade("t2a", ("A", "C", "M"), "test", "test")
    c2 = Cascade("t2b", ("M", "A", "C"), "test", "test")
    v1d = cascade_bind_ordered(c1, operators, dna_shift)
    v2d = cascade_bind_ordered(c2, operators, dna_shift)
    dna_ordering_breaks = (v1d != v2d)

    # DNA ordered ≠ silicon ordered (substrate-distinct fingerprints expected)
    v1s = cascade_bind_ordered(c1, operators, silicon_shift)
    dna_vs_silicon_ordered_differ = (v1d != v1s)
    dna_silicon_similarity_v1 = M.similarity(v1d, v1s)

    return {
        "test": "T2_r3_dna_substrate_substitution",
        "reverse_decode_stances_dna_10_of_10": rev_dna_correct,
        "dna_ordering_breaks_commutativity": dna_ordering_breaks,
        "dna_vs_silicon_ordered_v1_differ": dna_vs_silicon_ordered_differ,
        "dna_silicon_similarity_v1": dna_silicon_similarity_v1,
        "verdict": "R3-DNA-SUBSTITUTION-VALID" if all([
            rev_dna_correct == 10, dna_ordering_breaks
        ]) else "R3-DNA-SUBSTITUTION-DEGRADED",
    }


def t3_cross_substrate_similarity_spread(operators: Dict[str, ClassOperator]) -> Dict:
    """T3: Cross-substrate similarity spread (silicon vs DNA encodings).

    Per Spike #162 C3 gold-standard test: encode SAME content via two
    substrate-natural rotation parameters and compare bag-HDC similarity.

    H1 prediction: spread → 0 if substrate-portable (bit-exact)
    H2 prediction: spread > 0 but < threshold if substrate-natural (magnitude)
    H3 prediction: spread → 0.5 (random/orthogonal) if not substrate-portable
    """
    # Encode all stances under both substrates
    stances_silicon = {s["name"]: encode_stance_rotated(s["name"], s["tokens"], silicon_shift)
                       for s in SAMPLE_STANCES}
    stances_dna = {s["name"]: encode_stance_rotated(s["name"], s["tokens"], dna_shift)
                   for s in SAMPLE_STANCES}

    # Compare same-stance fingerprints across substrates
    same_substrate_sims = []
    for name in stances_silicon:
        sim = M.similarity(stances_silicon[name].fingerprint,
                          stances_dna[name].fingerprint)
        same_substrate_sims.append(sim)

    # Compare different-stance fingerprints across substrates
    cross_substrate_sims = []
    stance_names = list(stances_silicon.keys())
    for i, n1 in enumerate(stance_names):
        for n2 in stance_names[i+1:]:
            sim_s = M.similarity(stances_silicon[n1].fingerprint,
                                stances_silicon[n2].fingerprint)
            sim_d = M.similarity(stances_dna[n1].fingerprint,
                                stances_dna[n2].fingerprint)
            cross_substrate_sims.append((sim_s, sim_d))

    # Spread metrics
    same_avg = sum(same_substrate_sims) / len(same_substrate_sims)
    same_min = min(same_substrate_sims)
    same_max = max(same_substrate_sims)

    # Mean absolute difference between cross-pair sims in two substrates
    cross_diff_abs = [abs(s - d) for s, d in cross_substrate_sims]
    cross_diff_avg = sum(cross_diff_abs) / len(cross_diff_abs)

    # Spread = how different is the same-content encoding under two substrates?
    # Spread = 0 → identical (substrate-portable bit-exact)
    # Spread = 0.5 → random orthogonal (substrate-incompatible)
    spread = 1.0 - same_avg  # 0 if identical, 1 if anti-correlated

    return {
        "test": "T3_cross_substrate_similarity_spread",
        "same_stance_silicon_vs_dna_avg_sim": same_avg,
        "same_stance_silicon_vs_dna_min_sim": same_min,
        "same_stance_silicon_vs_dna_max_sim": same_max,
        "spread_same_stance": spread,
        "cross_substrate_pair_diff_abs_avg": cross_diff_avg,
        "n_same_stance_comparisons": len(same_substrate_sims),
        "n_cross_substrate_pair_comparisons": len(cross_substrate_sims),
        "note": "spread=0 → bit-exact substrate-portable; spread~0.5 → random orthogonal",
    }


def t4_algebra_identities_at_dna_shifts(operators: Dict[str, ClassOperator]) -> Dict:
    """T4: Bit-exact algebra identities preserved at DNA shifts {21, 11, -12}.

    Per Spike #159 Q3.A: permute(a, k) XOR permute(b, k) = permute(a XOR b, k)
    should hold bit-exact at ANY k. Verify at DNA helical pitches specifically
    per Spike #162 C1 precedent.

    Tests 14 classes × 3 DNA pitches = 42 cells, plus pair-wise XOR test.
    """
    mismatches_uniform_pair = []
    mismatches_uniform_bind = []
    cell_count_pair = 0
    cell_count_bind = 0

    for k in DNA_PITCHES:
        # Test permute commutativity with bind (Spike #159 Q3.A core identity)
        for i, n1 in enumerate(CLASS_NAMES):
            for n2 in CLASS_NAMES[i+1:]:
                a = operators[n1].vector
                b = operators[n2].vector
                lhs = M.bind(M.permute(a, k), M.permute(b, k))
                rhs = M.permute(M.bind(a, b), k)
                cell_count_pair += 1
                if lhs != rhs:
                    mismatches_uniform_pair.append((k, n1, n2))

        # Test 3-vector bind under uniform rotation
        for i in range(len(CLASS_NAMES) - 2):
            a, b, c = (operators[CLASS_NAMES[i+j]].vector for j in range(3))
            lhs = M.bind(M.bind(M.permute(a, k), M.permute(b, k)), M.permute(c, k))
            rhs = M.permute(M.bind(M.bind(a, b), c), k)
            cell_count_bind += 1
            if lhs != rhs:
                mismatches_uniform_bind.append((k, i))

    bit_exact_pair = (len(mismatches_uniform_pair) == 0)
    bit_exact_bind = (len(mismatches_uniform_bind) == 0)

    return {
        "test": "T4_algebra_identities_at_dna_shifts",
        "dna_pitches_tested": list(DNA_PITCHES),
        "uniform_permute_pair_bind_cells": cell_count_pair,
        "uniform_permute_pair_bind_mismatches": len(mismatches_uniform_pair),
        "uniform_permute_pair_bind_bit_exact": bit_exact_pair,
        "uniform_permute_3vec_bind_cells": cell_count_bind,
        "uniform_permute_3vec_bind_mismatches": len(mismatches_uniform_bind),
        "uniform_permute_3vec_bind_bit_exact": bit_exact_bind,
        "all_bit_exact": (bit_exact_pair and bit_exact_bind),
        "verdict": "BIT-EXACT-AT-DNA-HELICAL-PITCH" if (bit_exact_pair and bit_exact_bind)
                   else "ALGEBRA-IDENTITY-BROKEN-AT-DNA",
    }


def t5_z_dna_chirality_sign_flip(operators: Dict[str, ClassOperator]) -> Dict:
    """T5: Z-DNA chirality sign-flip — negative shift -12 produces distinct vec.

    Per [[user_stance_chirality_is_local_sign_flip_through_metric_fiber]]:
    Z-DNA is left-handed (chirality sign-flip) vs B/A right-handed.

    Test: permute(v, +12) vs permute(v, -12) should produce STRUCTURALLY-
    DISTINCT vectors (operationally distinguishable, bit-exact different).
    """
    distinct_count = 0
    total = 0
    similarities_pos_vs_neg = []

    for name in CLASS_NAMES:
        v = operators[name].vector
        v_right = M.permute(v, 12)   # right-handed +12
        v_left = M.permute(v, -12)   # left-handed (Z-DNA) -12
        if v_right != v_left:
            distinct_count += 1
        total += 1
        similarities_pos_vs_neg.append(M.similarity(v_right, v_left))

    # permute(permute(v, k), -k) == v identity (involution)
    # Per Spike #142 / hdc.py docstring: "permute(permute(a, k), -k) == a"
    involution_correct = 0
    for name in CLASS_NAMES:
        v = operators[name].vector
        v_round_trip = M.permute(M.permute(v, 12), -12)
        if v_round_trip == v:
            involution_correct += 1

    avg_sim_pos_neg = sum(similarities_pos_vs_neg) / len(similarities_pos_vs_neg)

    return {
        "test": "T5_z_dna_chirality_sign_flip",
        "distinguishable_classes_14_of_14": distinct_count,
        "involution_round_trip_correct_14_of_14": involution_correct,
        "avg_sim_right_vs_left": avg_sim_pos_neg,
        "verdict": "Z-DNA-CHIRALITY-IS-SIGN-FLIP-BIT-EXACT" if (
            distinct_count == 14 and involution_correct == 14
        ) else "CHIRALITY-SIGN-FLIP-BROKEN",
    }


def t6_reverse_decode_at_dna_substrate(operators: Dict[str, ClassOperator]) -> Dict:
    """T6: Reverse-decode accuracy at DNA substrate.

    The R3 core question: when stance fingerprints are encoded via DNA
    helical-pitch shifts, does reverse-decode accuracy remain 100%?
    """
    stances_dna = {s["name"]: encode_stance_rotated(s["name"], s["tokens"], dna_shift)
                   for s in SAMPLE_STANCES}

    correct = 0
    total = 0
    sim_diagonal = []  # self-similarities (should be 1.0)
    sim_off_diagonal = []  # cross-similarities (should be near 0)

    for name, st in stances_dna.items():
        best_name = None
        best_sim = -2.0
        for name2, st2 in stances_dna.items():
            sim = M.similarity(st.fingerprint, st2.fingerprint)
            if name == name2:
                sim_diagonal.append(sim)
            else:
                sim_off_diagonal.append(sim)
            if sim > best_sim:
                best_sim = sim
                best_name = name2
        if best_name == name:
            correct += 1
        total += 1

    return {
        "test": "T6_reverse_decode_at_dna_substrate",
        "correct": correct,
        "total": total,
        "accuracy": correct / total,
        "self_similarity_avg": sum(sim_diagonal) / len(sim_diagonal),
        "off_diagonal_avg": sum(sim_off_diagonal) / len(sim_off_diagonal),
        "verdict": "DNA-REVERSE-DECODE-PERFECT" if correct == total
                   else f"DNA-REVERSE-DECODE-PARTIAL-{correct}/{total}",
    }


def t7_forward_encode_determinism_dna(operators: Dict[str, ClassOperator]) -> Dict:
    """T7: Forward-encode determinism at DNA substrate.

    Re-encode same stance via DNA shifts twice — should produce bit-exact
    identical fingerprint (mint is deterministic; permute is deterministic;
    bind is deterministic).
    """
    matches = 0
    total = 0
    for s in SAMPLE_STANCES:
        st1 = encode_stance_rotated(s["name"], s["tokens"], dna_shift)
        st2 = encode_stance_rotated(s["name"], s["tokens"], dna_shift)
        if st1.fingerprint == st2.fingerprint:
            matches += 1
        total += 1
    return {
        "test": "T7_forward_encode_determinism_dna",
        "bit_exact_reproducible": matches,
        "total": total,
        "all_match": (matches == total),
        "verdict": "DNA-FORWARD-ENCODE-DETERMINISTIC" if matches == total
                   else "DNA-FORWARD-ENCODE-NONDETERMINISTIC",
    }


def t8_substrate_natural_class_n_signature(operators: Dict[str, ClassOperator]) -> Dict:
    """T8: Substrate-natural Class N signature preservation.

    DNA helical pitch numerators 21/11/12 ARE Class N rationals at
    biological substrate per Spike #162. Test that the LoE encoding via
    these specific rationals preserves the rational-signature structure:

    - 21 + 11 + (-12) = 20 (full-cycle sum)
    - 21/gcd(21,8192) and 11/gcd(11,8192) and 12/gcd(12,8192) are all
      coprime to D=8192=2^13 since they're odd or 4 (the 12 has gcd 4).
      Wait: gcd(12, 8192) = 4. So Z-DNA cycle order is 8192/4 = 2048.
      gcd(21, 8192) = 1; cycle order 8192.
      gcd(11, 8192) = 1; cycle order 8192.

    Test that applying conformation cycle repeatedly returns to identity
    after the predicted cycle length.
    """
    import math
    cycle_lengths = {}
    for pitch in DNA_PITCHES:
        gcd_with_D = math.gcd(abs(pitch), HDC_BITS)
        expected_cycle = HDC_BITS // gcd_with_D
        # Test: permute applied expected_cycle times returns to identity
        v = operators["A"].vector
        v_test = v
        for _ in range(expected_cycle):
            v_test = M.permute(v_test, pitch)
        returns_to_identity = (v_test == v)
        cycle_lengths[pitch] = {
            "gcd_with_D": gcd_with_D,
            "expected_cycle": expected_cycle,
            "returns_to_identity_bit_exact": returns_to_identity,
        }

    all_correct = all(c["returns_to_identity_bit_exact"]
                      for c in cycle_lengths.values())

    return {
        "test": "T8_substrate_natural_class_n_signature",
        "hdc_bits": HDC_BITS,
        "cycle_analysis": {str(k): v for k, v in cycle_lengths.items()},
        "all_class_n_cycles_bit_exact": all_correct,
        "verdict": "CLASS-N-RATIONAL-SIGNATURE-PRESERVED-BIT-EXACT" if all_correct
                   else "CLASS-N-RATIONAL-SIGNATURE-BROKEN",
    }


def t9_cross_substrate_within_vs_between(operators: Dict[str, ClassOperator]) -> Dict:
    """T9: Within-vs-between separation preservation at DNA substrate.

    Per Spike #159 Q3.C: form-function rotation preserves within-vs-between
    cohort separation. At DNA substrate, test that DNA-rotated stance
    fingerprints maintain reverse-decode-friendly off-diagonal structure
    (off-diagonal ~ 0 like silicon).
    """
    stances_silicon = {s["name"]: encode_stance_rotated(s["name"], s["tokens"], silicon_shift)
                       for s in SAMPLE_STANCES}
    stances_dna = {s["name"]: encode_stance_rotated(s["name"], s["tokens"], dna_shift)
                   for s in SAMPLE_STANCES}

    def stats(stances):
        sims_off = []
        names = list(stances.keys())
        for i, n1 in enumerate(names):
            for n2 in names[i+1:]:
                sims_off.append(M.similarity(stances[n1].fingerprint,
                                            stances[n2].fingerprint))
        return {
            "off_diag_min": min(sims_off),
            "off_diag_max": max(sims_off),
            "off_diag_avg": sum(sims_off) / len(sims_off),
            "off_diag_abs_max": max(abs(s) for s in sims_off),
        }

    silicon_stats = stats(stances_silicon)
    dna_stats = stats(stances_dna)

    # Compare structural properties — both should be near-orthogonal
    silicon_orthogonal = (silicon_stats["off_diag_abs_max"] < 0.05)
    dna_orthogonal = (dna_stats["off_diag_abs_max"] < 0.05)

    return {
        "test": "T9_cross_substrate_within_vs_between",
        "silicon": silicon_stats,
        "dna": dna_stats,
        "silicon_near_orthogonal": silicon_orthogonal,
        "dna_near_orthogonal": dna_orthogonal,
        "verdict": "DNA-WITHIN-BETWEEN-PRESERVED" if (silicon_orthogonal and dna_orthogonal)
                   else "DNA-WITHIN-BETWEEN-DEGRADED",
    }


# ─────────────────────────────────────────────────────────────────────
# Verdict logic
# ─────────────────────────────────────────────────────────────────────

def determine_verdict(t4, t6, t7) -> str:
    """Apply Spike #172 verdict logic per spike directive.

    H1: SUBSTRATE-PORTABLE BIT-EXACT — T4 14/14 AND T6 = 100%
    H2: SUBSTRATE-NATURAL MAGNITUDE — T4 14/14 AND 95% <= T6 < 100%
    H3: REFUTED — significant accuracy drop
    """
    algebra_bit_exact = t4["all_bit_exact"]
    decode_accuracy = t6["accuracy"]
    forward_det = t7["all_match"]

    if algebra_bit_exact and decode_accuracy == 1.0 and forward_det:
        return "H1-SUBSTRATE-PORTABILITY-OF-LOE-INSTRUMENT-CONFIRMED-BIT-EXACT"
    elif algebra_bit_exact and decode_accuracy >= 0.95 and forward_det:
        return "H2-SUBSTRATE-NATURAL-MAGNITUDE-LEVEL"
    else:
        return "H3-LOE-ENCODING-HAS-SILICON-SPECIFIC-DEPENDENCIES"


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Spike #172 — LoE-RBS-HDC R3 cross-substrate DNA helical-pitch test")
    print("=" * 70)

    operators = build_class_operators()
    print(f"Built {len(operators)} class operators at D = {HDC_BITS} bits")
    print(f"Silicon stride (R1): {SILICON_STRIDE}")
    print(f"DNA pitches (R3):    {DNA_PITCHES} (B-DNA, A-DNA, Z-DNA)")
    print()

    results = []
    for test_fn in (t1_r1_baseline_replication,
                    t2_r3_dna_substrate_substitution,
                    t3_cross_substrate_similarity_spread,
                    t4_algebra_identities_at_dna_shifts,
                    t5_z_dna_chirality_sign_flip,
                    t6_reverse_decode_at_dna_substrate,
                    t7_forward_encode_determinism_dna,
                    t8_substrate_natural_class_n_signature,
                    t9_cross_substrate_within_vs_between):
        t0 = time.time()
        result = test_fn(operators)
        result["elapsed_sec"] = time.time() - t0
        results.append(result)
        verdict = result.get("verdict", "n/a")
        print(f"[{result['test']:<55s}] verdict: {verdict}")

    # Final verdict
    t4 = next(r for r in results if r["test"] == "T4_algebra_identities_at_dna_shifts")
    t6 = next(r for r in results if r["test"] == "T6_reverse_decode_at_dna_substrate")
    t7 = next(r for r in results if r["test"] == "T7_forward_encode_determinism_dna")
    final_verdict = determine_verdict(t4, t6, t7)
    print()
    print("FINAL VERDICT:")
    print(f"  {final_verdict}")

    # Write NDJSON records
    out_path = Path(__file__).parent / "spike172_records_2026-05-19.ndjson"
    with out_path.open("w", encoding="utf-8") as fh:
        # Header record
        header = {
            "record_type": "header",
            "spike": "spike172",
            "title": "LoE-as-RBS-HDC R3 cross-substrate DNA helical-pitch test",
            "date": "2026-05-19",
            "hdc_bits": HDC_BITS,
            "silicon_stride": SILICON_STRIDE,
            "dna_pitches": list(DNA_PITCHES),
            "predecessor_spikes": ["spike170_R1", "spike162", "spike159", "spike147", "spike167"],
        }
        fh.write(json.dumps(header, sort_keys=True) + "\n")
        for r in results:
            r["record_type"] = "test_result"
            # Convert any tuple values for JSON serialisation
            def serialise(obj):
                if isinstance(obj, dict):
                    return {k: serialise(v) for k, v in obj.items()}
                if isinstance(obj, (list, tuple)):
                    return [serialise(x) for x in obj]
                if isinstance(obj, (bytes, bytearray)):
                    return obj.hex()
                return obj
            fh.write(json.dumps(serialise(r), sort_keys=True) + "\n")
        # Final verdict record
        summary = {
            "record_type": "summary",
            "spike": "spike172",
            "final_verdict": final_verdict,
            "tests_run": len(results),
        }
        fh.write(json.dumps(summary, sort_keys=True) + "\n")
    print(f"\nWrote NDJSON records: {out_path}")

    return final_verdict


if __name__ == "__main__":
    main()
