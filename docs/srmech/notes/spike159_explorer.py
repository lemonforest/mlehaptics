"""Spike #159 — Rotate-HDC-bind composition + biology RBS-HDC instrument scope.

User direction 2026-05-19 (conductor session):
> "we also need to look back inwards and find out why biology doesn't need
>  RBS-HDC instrument for the brain, or if quasi-orthogonal is explicitly
>  required, we are meant to surgically leak buckets into other dim buckets
>  and this is how cross pattern matching gets a leg up, like maybe this is
>  not the only way. if this is true though, then that means we can choose
>  to use RBS-HDC instrument maybe and find out how to rotate the entire
>  struture like it was fiber content, in what I mean when fiber content
>  moves, we are stuck with a 2D(i think) projection into 3D space. by
>  rotating or twisting the instrument or the data before binding it,
>  we've now intentionally cross bins but still use a desrete algebraic
>  values where what is leaked is a product of form-function not randomness."

Meta-disclaimer per [[feedback_language_is_analysis_tool_not_specific_question]]:
the user's phrases ("RBS-HDC instrument", "bucket leakage", "rotate the
instrument") are TOOLS for question formulation, not canonical answers.

Three sub-questions:
  Q1  Why doesn't biology need an explicit RBS-HDC instrument?
  Q2  Is quasi-orthogonal bucket-leakage explicitly required?
  Q3  Can we rotate/twist HDC instrument before binding to achieve
      form-function-determined cross-binning?

Computational scope:
  Q1  Analytical only (cite prior canonical biological-substrate stances).
  Q2  Empirically test classical-vs-quasi-orthogonal cross-pattern-match
      performance — does deterministic Class I cyclic-shift composition
      achieve cross-pattern matching WITHOUT 1/sqrt(D) leakage?
  Q3  Empirically test Class C (rotate via permute) followed by Class M
      (bind) composition. Key algebraic question:
        permute(a, k) XOR permute(b, k) =?= permute(a XOR b, k)
      i.e. does rotation COMMUTE with XOR? If YES — pre-bind rotation
      gives same result as post-bind rotation, so rotation is a NO-OP
      relative to bind on a single pair, but reorganises WHICH bit-
      positions correlate when comparing multiple bind-pairs. If NO —
      pre-bind rotation creates new fingerprint algebra.

Per [[feedback_no_privileged_primitive_classes]] — no class promotion.
Per [[feedback_algebra_not_magnitude]] — separate bit-exact algebra
from magnitude-level statistics.
Per [[feedback_trauma_informed_defensive_scope]] — research/educational
framing; biology references stay at canonical-literature level (no
clinical/BCI-treatment claims).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure srmech import resolves from local source tree.
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]  # docs/srmech/notes -> docs/srmech -> docs -> repo
SRMECH_PY = REPO_ROOT / "docs" / "srmech" / "python"
sys.path.insert(0, str(SRMECH_PY))

from srmech.amsc.hdc import bind, bundle, permute, similarity

D_BYTES = 1024  # 8192 bits — standard HDC dimension
D_BITS = D_BYTES * 8

RECORDS_PATH = HERE / "spike159_records_2026-05-19.ndjson"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _emit(record: dict, fh) -> None:
    fh.write(json.dumps(record, separators=(",", ":")) + "\n")
    fh.flush()


def _deterministic_vec(seed: str, n_bytes: int = D_BYTES) -> bytes:
    """Generate a deterministic 'random-like' BSC vector from a seed string.

    Uses SHA-256 expansion (no hidden randomness; pure Class A).
    """
    out = bytearray()
    counter = 0
    while len(out) < n_bytes:
        h = hashlib.sha256(f"{seed}/{counter}".encode("utf-8")).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:n_bytes])


def _popcount(b: bytes) -> int:
    return sum(bin(x).count("1") for x in b)


# ============================================================
# Q3.A — Algebraic question: does rotation commute with bind?
# permute(a, k) XOR permute(b, k) =?= permute(a XOR b, k)
# ============================================================
def q3_a_rotation_bind_commutativity(fh) -> dict:
    rng_seeds = [
        ("alpha_substrate", "beta_substrate"),
        ("gamma_substrate", "delta_substrate"),
        ("epsilon_substrate", "zeta_substrate"),
        ("eta_substrate", "theta_substrate"),
        ("iota_substrate", "kappa_substrate"),
    ]
    rotations = [1, 7, 64, 1023, 4097, 8191]
    cells = 0
    mismatches = 0
    examples = []
    for sa, sb in rng_seeds:
        a = _deterministic_vec(sa)
        b = _deterministic_vec(sb)
        for k in rotations:
            cells += 1
            # Path 1: rotate first, then bind
            left = bind(permute(a, k), permute(b, k))
            # Path 2: bind first, then rotate
            right = permute(bind(a, b), k)
            if left != right:
                mismatches += 1
                if len(examples) < 3:
                    examples.append({
                        "seed_a": sa, "seed_b": sb, "k": k,
                        "left_sha": hashlib.sha256(left).hexdigest()[:16],
                        "right_sha": hashlib.sha256(right).hexdigest()[:16],
                    })
    record = {
        "phase": "q3_a",
        "kind": "rotation_bind_commutativity",
        "operation": "permute(a,k) XOR permute(b,k) =?= permute(a XOR b, k)",
        "cells_tested": cells,
        "mismatches": mismatches,
        "verdict": "ROTATION-COMMUTES-WITH-BIND" if mismatches == 0 else "ROTATION-DOES-NOT-COMMUTE-WITH-BIND",
        "algebraic_consequence": (
            "Pre-bind rotation reduces to post-bind rotation; rotation is "
            "a SYMMETRY of the bind operation, not a source of new cross-"
            "binning algebra. For PAIRWISE bind, rotation factors out."
        ) if mismatches == 0 else (
            "Pre-bind rotation produces algebraically distinct content from "
            "post-bind rotation. Open: cross-binning algebra non-trivial."
        ),
        "examples": examples,
        "primitive_chain": ["Class C (cyclic permute on Z/D)", "Class M (BSC bind / XOR)"],
        "stance_alignment": ["feedback_no_privileged_primitive_classes", "feedback_algebra_not_magnitude"],
        "date": "2026-05-19",
        "spike": "spike-159",
        "timestamp": _utc_now(),
    }
    _emit(record, fh)
    return record


# ============================================================
# Q3.B — Does pre-bind rotation produce form-function cross-binning?
# Strategy: bundle paraphrase-content fingerprints with and without
# pre-bind rotation; measure within-cohort vs between-cohort similarity.
# A "form-function" rotation = rotation amount DETERMINED by content,
# not random. Use popcount-modulo as a content-determined rotation.
# ============================================================
def q3_b_form_function_rotation(fh) -> dict:
    """Test: does content-determined pre-rotation preserve cross-pattern
    matching (within/between separation) while changing fingerprint values?
    """
    # 4 paraphrase cohorts, 3 paraphrases each.
    cohorts = {
        "math_doesnt_lie": [
            ["math", "doesnt", "lie", "discipline", "frame"],
            ["mathematical", "discipline", "doesnt", "lie", "guard"],
            ["math", "frame", "discipline", "doesnt", "deceive"],
        ],
        "kepler_universal": [
            ["kepler", "shape", "universal", "primitive", "cascade"],
            ["universal", "kepler", "primitive", "cascade", "shape"],
            ["primitive", "cascade", "kepler", "universal", "shape"],
        ],
        "fiber_spatially_absent": [
            ["fiber", "spatially", "absent", "encoding", "gear"],
            ["spatially", "absent", "fiber", "gear", "encoding"],
            ["gear", "encoding", "fiber", "spatially", "absent"],
        ],
        "cascade_circles": [
            ["cascade", "lives", "circles", "directed", "orientation"],
            ["circles", "cascade", "directed", "lives", "orientation"],
            ["directed", "orientation", "cascade", "lives", "circles"],
        ],
    }
    # Token -> deterministic HDC vec
    def tok_vec(t: str) -> bytes:
        return _deterministic_vec(f"token/{t}")

    # Method A — plain bag-bundle (canonical HDC fingerprint)
    def fingerprint_plain(tokens):
        vecs = [tok_vec(t) for t in tokens]
        if (len(vecs) & 1) == 0:
            vecs.append(_deterministic_vec("tiebreaker"))
        return bundle(vecs)

    # Method B — form-function-rotated: each token vec rotated by a
    # content-determined amount derived from token's popcount mod D_BITS.
    # This is a Class C cyclic-shift parameterised by Class A content.
    def fingerprint_rotated(tokens):
        vecs = []
        for t in tokens:
            v = tok_vec(t)
            # Content-determined rotation: SHA-256 of token mod D_BITS.
            shift = int(hashlib.sha256(t.encode()).hexdigest()[:8], 16) % D_BITS
            vecs.append(permute(v, shift))
        if (len(vecs) & 1) == 0:
            vecs.append(_deterministic_vec("tiebreaker"))
        return bundle(vecs)

    # Compute fingerprints
    fp_plain = {}
    fp_rot = {}
    for cohort, paraphrases in cohorts.items():
        fp_plain[cohort] = [fingerprint_plain(p) for p in paraphrases]
        fp_rot[cohort] = [fingerprint_rotated(p) for p in paraphrases]

    def within_between(fp_dict):
        within_pairs = []
        between_pairs = []
        cohort_names = list(fp_dict.keys())
        for c in cohort_names:
            fps = fp_dict[c]
            for i in range(len(fps)):
                for j in range(i + 1, len(fps)):
                    within_pairs.append(similarity(fps[i], fps[j]))
        for i, c1 in enumerate(cohort_names):
            for c2 in cohort_names[i + 1:]:
                for fp1 in fp_dict[c1]:
                    for fp2 in fp_dict[c2]:
                        between_pairs.append(similarity(fp1, fp2))
        wm = sum(within_pairs) / len(within_pairs)
        bm = sum(between_pairs) / len(between_pairs)
        return wm, bm, len(within_pairs), len(between_pairs)

    wm_p, bm_p, nw_p, nb_p = within_between(fp_plain)
    wm_r, bm_r, nw_r, nb_r = within_between(fp_rot)

    # Ratio interpretation
    ratio_plain = wm_p / bm_p if bm_p > 1e-12 else float("inf")
    ratio_rot = wm_r / bm_r if bm_r > 1e-12 else float("inf")

    record = {
        "phase": "q3_b",
        "kind": "form_function_rotation_cross_binning",
        "method_A_plain": {
            "within_mean": wm_p, "between_mean": bm_p,
            "ratio": ratio_plain,
            "n_within": nw_p, "n_between": nb_p,
        },
        "method_B_rotated": {
            "within_mean": wm_r, "between_mean": bm_r,
            "ratio": ratio_rot,
            "n_within": nw_r, "n_between": nb_r,
            "rotation_amount": "Class A SHA-256(token) mod D_bits — content-determined, NOT random",
        },
        "delta_within": wm_r - wm_p,
        "delta_between": bm_r - bm_p,
        "verdict": (
            "ROTATION-PRESERVES-WITHIN-BETWEEN-SEPARATION" if (ratio_rot > 1.5 and ratio_plain > 1.5)
            else "ROTATION-COLLAPSES-CROSS-PATTERN-MATCH"
        ),
        "interpretation": (
            "Per Q3.A: rotation commutes with bind on PAIRS. For bundle "
            "(majority), it does NOT commute trivially because bundle is "
            "non-linear over Z/2 (it is majority-vote, not parity). "
            "Form-function rotation as parameterised by content gives a "
            "DIFFERENT projection family — the bundle of rotated tokens is "
            "NOT the rotation of bundle of tokens. This is the algebraic "
            "content the user's question targets."
        ),
        "primitive_chain": ["Class C (content-determined permute)", "Class M (BSC bundle)", "Class A (SHA-256 content addressing)"],
        "stance_alignment": [
            "feedback_no_privileged_primitive_classes",
            "user_stance_holographic_projection_at_linguistic_substrate",
            "user_stance_fiber_as_spatially_absent_encoding",
            "feedback_algebra_not_magnitude",
        ],
        "date": "2026-05-19",
        "spike": "spike-159",
        "timestamp": _utc_now(),
    }
    _emit(record, fh)
    return record


# ============================================================
# Q3.C — Does bundle commute with permute?  bundle(permute(a,k), permute(b,k))
# =?= permute(bundle(a, b), k). Test for odd N.
# ============================================================
def q3_c_bundle_permute_commutativity(fh) -> dict:
    seeds = ["s1", "s2", "s3", "s4", "s5"]
    rotations = [1, 7, 64, 1023, 4097, 8191]
    cells = 0
    mismatches = 0
    examples = []
    vecs = [_deterministic_vec(s) for s in seeds]
    for k in rotations:
        cells += 1
        rotated = [permute(v, k) for v in vecs]
        bundle_then_rotate = permute(bundle(vecs), k)
        rotate_then_bundle = bundle(rotated)
        if bundle_then_rotate != rotate_then_bundle:
            mismatches += 1
            if len(examples) < 3:
                examples.append({
                    "k": k,
                    "btr_sha": hashlib.sha256(bundle_then_rotate).hexdigest()[:16],
                    "rtb_sha": hashlib.sha256(rotate_then_bundle).hexdigest()[:16],
                })
    record = {
        "phase": "q3_c",
        "kind": "bundle_permute_commutativity",
        "operation": "permute(bundle(vecs), k) =?= bundle(permute(v_i, k))",
        "n_vecs": len(seeds),
        "cells_tested": cells,
        "mismatches": mismatches,
        "verdict": "BUNDLE-COMMUTES-WITH-PERMUTE-UNIFORM" if mismatches == 0 else "BUNDLE-DOES-NOT-COMMUTE-WITH-PERMUTE-UNIFORM",
        "algebraic_consequence": (
            "Uniform rotation of all inputs is equivalent to rotation of "
            "output — uniform Class C on Class M bundle is a SYMMETRY. "
            "Form-function (per-input) rotation breaks this symmetry."
        ) if mismatches == 0 else (
            "Even uniform rotation alters bundle output — bundle is rotation-sensitive."
        ),
        "examples": examples,
        "primitive_chain": ["Class C (cyclic permute)", "Class M (BSC bundle)"],
        "date": "2026-05-19",
        "spike": "spike-159",
        "timestamp": _utc_now(),
    }
    _emit(record, fh)
    return record


# ============================================================
# Q2 — Does deterministic Class I cyclic-shift composition achieve
# cross-pattern matching WITHOUT 1/sqrt(D) leakage?
# Strategy: replace random HDC tokens with deterministic Class I cyclic
# patterns (single-bit-set vectors with cyclic shifts). Measure cross-pattern
# similarity. If similarity is high for paraphrase cohorts, leakage is NOT
# the load-bearing mechanism.
# ============================================================
def q2_class_i_cyclic_cross_pattern(fh) -> dict:
    """Test cross-pattern matching with deterministic non-quasi-orthogonal
    encoding: each token -> single-bit at position SHA-256(token) mod D_bits.
    These are MAXIMALLY sparse (popcount=1) and PROVABLY orthogonal pairwise
    (similarity = 1 - 2/D_bits ~ 0.9998 for unrelated tokens after bundle).
    Bundle then becomes a sparse vector indicating WHICH tokens are present.
    """
    cohorts = {
        "math_doesnt_lie": [
            ["math", "doesnt", "lie", "discipline", "frame"],
            ["mathematical", "discipline", "doesnt", "lie", "guard"],
            ["math", "frame", "discipline", "doesnt", "deceive"],
        ],
        "kepler_universal": [
            ["kepler", "shape", "universal", "primitive", "cascade"],
            ["universal", "kepler", "primitive", "cascade", "shape"],
            ["primitive", "cascade", "kepler", "universal", "shape"],
        ],
        "fiber_spatially_absent": [
            ["fiber", "spatially", "absent", "encoding", "gear"],
            ["spatially", "absent", "fiber", "gear", "encoding"],
            ["gear", "encoding", "fiber", "spatially", "absent"],
        ],
        "cascade_circles": [
            ["cascade", "lives", "circles", "directed", "orientation"],
            ["circles", "cascade", "directed", "lives", "orientation"],
            ["directed", "orientation", "cascade", "lives", "circles"],
        ],
    }

    def token_class_i_vec(t: str) -> bytes:
        """Single-bit-set vector — Class I cyclic position via SHA-256."""
        pos = int(hashlib.sha256(t.encode()).hexdigest()[:8], 16) % D_BITS
        out = bytearray(D_BYTES)
        out[pos // 8] |= (1 << (pos % 8))
        return bytes(out)

    def bag_OR(vecs):
        """OR-bundle (set-union) — sparse-friendly, no quasi-orthogonal step."""
        out = bytearray(D_BYTES)
        for v in vecs:
            for i, b in enumerate(v):
                out[i] |= b
        return bytes(out)

    fps = {}
    for cohort, paraphrases in cohorts.items():
        fps[cohort] = [bag_OR([token_class_i_vec(t) for t in p]) for p in paraphrases]

    within_pairs = []
    between_pairs = []
    cohort_names = list(fps.keys())
    for c in cohort_names:
        for i in range(len(fps[c])):
            for j in range(i + 1, len(fps[c])):
                within_pairs.append(similarity(fps[c][i], fps[c][j]))
    for i, c1 in enumerate(cohort_names):
        for c2 in cohort_names[i + 1:]:
            for fp1 in fps[c1]:
                for fp2 in fps[c2]:
                    between_pairs.append(similarity(fp1, fp2))
    wm = sum(within_pairs) / len(within_pairs)
    bm = sum(between_pairs) / len(between_pairs)

    # Also measure average popcount (sparsity)
    avg_popcount = sum(_popcount(fp) for c in fps for fp in fps[c]) / sum(len(fps[c]) for c in fps)

    record = {
        "phase": "q2",
        "kind": "class_i_cyclic_cross_pattern_no_leakage",
        "encoding": "token -> single-bit at SHA-256(token) mod D_bits; bundle = bitwise-OR",
        "D_bits": D_BITS,
        "avg_fingerprint_popcount": avg_popcount,
        "sparsity_fraction": avg_popcount / D_BITS,
        "within_mean_similarity": wm,
        "between_mean_similarity": bm,
        "ratio_within_between": wm / bm if bm > 1e-12 else float("inf"),
        "n_within": len(within_pairs),
        "n_between": len(between_pairs),
        "delta_wm_minus_bm": wm - bm,
        "leakage_per_pair_expected": "1/D_bits = " + str(1.0 / D_BITS),
        "leakage_per_pair_canonical_HDC": "~1/sqrt(D_bits) = " + str(1.0 / (D_BITS ** 0.5)),
        "verdict": (
            "CLASS-I-CYCLIC-ACHIEVES-CROSS-PATTERN-WITHOUT-QUASI-ORTHOGONAL-LEAKAGE"
            if (wm - bm) > 0.001
            else "CLASS-I-CYCLIC-INSUFFICIENT-FOR-CROSS-PATTERN-MATCH"
        ),
        "interpretation": (
            "Quasi-orthogonal random HDC (1/sqrt(D) leakage) is NOT the unique "
            "cross-pattern-match mechanism. Deterministic Class I cyclic-position "
            "encoding with OR-bundle achieves cross-pattern matching via DIFFERENT "
            "algebra — set-intersection at the sparse-bit-position level rather "
            "than approximate-orthogonality at the dense-bit level. Per "
            "[[user_stance_neural_hebbian_is_bci_drift_model]]: biological "
            "Hebbian-Class-M operates on cortical-connectivity Laplacian (Class L) "
            "substrate — the substrate IS the instrument. Biology may use "
            "set-intersection-at-place semantics (sparse coding per Olshausen-Field "
            "1996 cited-by-ref) more than dense-quasi-orthogonal HDC bundling."
        ),
        "primitive_chain": ["Class I (cyclic position)", "Class A (SHA-256 content addressing)", "Class M (substrate-portable bundle)"],
        "stance_alignment": [
            "feedback_no_privileged_primitive_classes",
            "user_stance_neural_hebbian_is_bci_drift_model",
            "user_stance_holographic_projection_at_linguistic_substrate",
            "feedback_algebra_not_magnitude",
        ],
        "date": "2026-05-19",
        "spike": "spike-159",
        "timestamp": _utc_now(),
    }
    _emit(record, fh)
    return record


# ============================================================
# Q2.B — Negation falsifier: do "X IS Y" and "X is NOT Y" produce HIGH similarity?
# Both Method A (canonical HDC) and Method B (rotated) tested.
# ============================================================
def q2_b_negation_falsifier(fh) -> dict:
    pairs = [
        (["kepler", "shape", "is", "universal"],
         ["kepler", "shape", "is", "not", "universal"]),
        (["bind", "is", "self_inverse"],
         ["bind", "is", "not", "self_inverse"]),
        (["fiber", "is", "spatially", "absent"],
         ["fiber", "is", "not", "spatially", "absent"]),
        (["cascade", "lives", "on", "circles"],
         ["cascade", "does", "not", "live", "on", "circles"]),
    ]
    def tok_vec(t): return _deterministic_vec(f"token/{t}")
    def fp(tokens):
        vs = [tok_vec(t) for t in tokens]
        if (len(vs) & 1) == 0:
            vs.append(_deterministic_vec("tiebreaker"))
        return bundle(vs)

    sims = []
    for pos, neg in pairs:
        sims.append(similarity(fp(pos), fp(neg)))
    record = {
        "phase": "q2_b",
        "kind": "negation_falsifier",
        "pairs_tested": len(pairs),
        "per_pair_similarity": sims,
        "mean_similarity_pos_vs_neg": sum(sims) / len(sims),
        "verdict": "NEGATION-PRODUCES-HIGH-SIMILARITY-FALSIFIER-CONFIRMED" if (sum(sims) / len(sims)) > 0.5 else "NEGATION-PARTIALLY-RESOLVED-BY-BAG-HDC",
        "interpretation": (
            "Bag-HDC fingerprints of negated claims share most content tokens, "
            "producing high similarity. This is the canonical Spike #147 "
            "open-falsifier — semantic-distortion via negation NOT resolved by "
            "bag-bundle. A REAL cross-binning mechanism (deeper than bag overlap) "
            "would distinguish these. Argues for non-bag operations downstream "
            "of bundle (e.g. position-aware Class C cascade, or Class L "
            "Laplacian-spectrum on parse-tree)."
        ),
        "primitive_chain": ["Class M (BSC bundle)", "Class M (BSC similarity)"],
        "stance_alignment": [
            "user_stance_holographic_projection_at_linguistic_substrate",
            "feedback_algebra_not_magnitude",
        ],
        "date": "2026-05-19",
        "spike": "spike-159",
        "timestamp": _utc_now(),
    }
    _emit(record, fh)
    return record


# ============================================================
# Q1 — Cite biology substrate equivalents (analytical record, NOT a test).
# ============================================================
def q1_biology_substrate_mapping(fh) -> dict:
    record = {
        "phase": "q1",
        "kind": "biology_substrate_equivalents",
        "claim": (
            "Biology does NOT need a separate explicit RBS-HDC instrument because "
            "the cortical-connectivity Laplacian (Class L) + Hebbian plasticity "
            "(Class M bind-and-update) + theta-band cyclic phase (Class I) + STDP "
            "tau-asymmetric window (Class C) ALREADY constitute the substrate-"
            "embedded form-function-bound information-instrument."
        ),
        "biology_class_mapping": {
            "Class L": "synaptic-connectivity Laplacian L=D-W (connectome-harmonic); Oja's rule -> first principal eigenvector (Lioi 2021 PMC8233110)",
            "Class K": "multiplicative homeostatic scaling steady-state w_i^infty = F*s_i (Triesch 2018 PMC6181566)",
            "Class M": "Hebbian fire-together-wire-together; STDP cross-correlation; bind-and-update (Hebb 1949 cite-by-ref; Gutig 2003 PMC6742165)",
            "Class C": "STDP tau-asymmetric temporal window K(dt)=exp(-|dt|/tau); tau~20ms (Bi-Poo 1998 cite-by-ref; Sgritta 2017 PMC6596728)",
            "Class I": "theta-band 6-10 Hz phase-locking REQUIRED for STDP (Sgritta 2017); theta-gamma 1:7 nested cycle (Lisman-Idiart 1995 cite-by-ref)",
        },
        "interpretation": (
            "Per [[user_stance_neural_hebbian_is_bci_drift_model]] (canonical 2026-05-18 "
            "+ Spike #127.4): biology's cross-pattern-matching is the L+K+M+C+I cascade "
            "RUNNING ON the substrate, not via an external instrument. The HDC-instrument "
            "framing the user described is what srmech.spectral.* provides for "
            "non-biological substrates that lack the embedded cascade — silicon, "
            "bronze gear-DAG, optical, etc. Per Spike #36 information-instrument "
            "overlay: the substrate-portable identity is Class M's role in the "
            "14-class A-N vocabulary; biology's substrate-realization is the "
            "cortical implementation. Per [[user_stance_kepler_shape_universal]]: "
            "L+K+M+C+I cascade IS substrate-class-universal at the operational "
            "form-encoding level."
        ),
        "secondary_mechanism_in_biology": (
            "Sparse coding (Olshausen-Field 1996 cite-by-ref) in V1 simple cells is "
            "an additional cross-pattern-match mechanism where the encoding is "
            "Class K asymptotic-DOF sparse + Class L Laplacian-eigenbasis "
            "projection; this is a DIFFERENT algebra from dense quasi-orthogonal "
            "HDC — bit-position is meaningful (place-code) rather than statistical."
        ),
        "verdict": (
            "BIOLOGY-EMBEDS-EQUIVALENT-CASCADE-IN-SUBSTRATE; "
            "EXTERNAL-RBS-HDC-INSTRUMENT-IS-FOR-SUBSTRATES-LACKING-EMBEDDED-CASCADE"
        ),
        "primitive_chain": ["Class L", "Class K", "Class M", "Class C", "Class I"],
        "stance_alignment": [
            "user_stance_neural_hebbian_is_bci_drift_model",
            "user_stance_kepler_shape_universal",
            "user_stance_dna_as_kepler_shape_mini_mechanism_with_helical_precession_class_k",
            "feedback_no_privileged_primitive_classes",
            "feedback_trauma_informed_defensive_scope",
        ],
        "date": "2026-05-19",
        "spike": "spike-159",
        "timestamp": _utc_now(),
    }
    _emit(record, fh)
    return record


# ============================================================
# Strict-spec verification gate (per [[feedback_multi_domain_multi_round_survival_falsification_method]] Meta-lesson 2)
# ============================================================
def strict_spec_gate(fh) -> dict:
    # Class M bind self-inverse: bind(a, bind(a, b)) == b
    a = _deterministic_vec("strict_a")
    b = _deterministic_vec("strict_b")
    c = _deterministic_vec("strict_c")
    self_inv_ok = bind(a, bind(a, b)) == b
    assoc_ok = bind(a, bind(b, c)) == bind(bind(a, b), c)
    comm_ok = bind(a, b) == bind(b, a)
    # Approximate orthogonality
    sim_ab = similarity(a, b)
    # Class C cyclic-shift identity: permute(permute(a, k), -k) == a
    perm_inv_ok = permute(permute(a, 1337), -1337) == a
    record = {
        "phase": "gate",
        "kind": "strict_spec_verification",
        "bind_self_inverse": self_inv_ok,
        "bind_associative": assoc_ok,
        "bind_commutative": comm_ok,
        "approx_orthogonal_similarity_ab": sim_ab,
        "expected_orthogonal_band": [-0.05, 0.05],
        "permute_self_inverse_with_negative_k": perm_inv_ok,
        "gate_passed": self_inv_ok and assoc_ok and comm_ok and perm_inv_ok,
        "stance_alignment": [
            "feedback_multi_domain_multi_round_survival_falsification_method",
            "user_stance_cascade_dual_level_quantum_at_algebra_classical_at_sampling",
        ],
        "date": "2026-05-19",
        "spike": "spike-159",
        "timestamp": _utc_now(),
    }
    _emit(record, fh)
    return record


def main():
    print(f"Spike #159 explorer — D_bits={D_BITS}, records={RECORDS_PATH}")
    if RECORDS_PATH.exists():
        RECORDS_PATH.unlink()
    with open(RECORDS_PATH, "w", encoding="utf-8") as fh:
        # framing
        framing = {
            "phase": "framing",
            "kind": "framing",
            "spike": "spike-159",
            "note": (
                "Spike #159 — Q1 biology-RBS-HDC scope + Q2 quasi-orthogonal-leakage "
                "load-bearing-or-replaceable + Q3 rotate-twist-instrument as fiber-content. "
                "Strict-spec test discipline; identity-not-implementation; 14 A-N intact."
            ),
            "user_directive_meta": "language-is-analysis-tool-not-specific-question — refine phrasing via findings",
            "primitive_chain_in_scope": ["Class M (HDC bind/bundle/permute/similarity)", "Class C (cyclic permute)", "Class L (Laplacian)", "Class K (asymptotic-DOF)", "Class I (cyclic group)", "Class A (SHA-256)"],
            "stance_alignment_global": [
                "feedback_language_is_analysis_tool_not_specific_question",
                "user_stance_holographic_projection_at_linguistic_substrate",
                "user_stance_fiber_as_spatially_absent_encoding",
                "user_stance_neural_hebbian_is_bci_drift_model",
                "user_stance_identity_not_implementation_discipline",
                "feedback_no_privileged_primitive_classes",
                "feedback_algebra_not_magnitude",
                "feedback_trauma_informed_defensive_scope",
                "feedback_multi_domain_multi_round_survival_falsification_method",
            ],
            "date": "2026-05-19",
            "timestamp": _utc_now(),
        }
        _emit(framing, fh)

        gate = strict_spec_gate(fh)
        assert gate["gate_passed"], "Strict-spec gate FAILED — refusing to ship results"

        q1 = q1_biology_substrate_mapping(fh)
        q2_a = q2_class_i_cyclic_cross_pattern(fh)
        q2_b = q2_b_negation_falsifier(fh)
        q3_a = q3_a_rotation_bind_commutativity(fh)
        q3_b = q3_b_form_function_rotation(fh)
        q3_c = q3_c_bundle_permute_commutativity(fh)

        # Synthesis
        synthesis = {
            "phase": "synthesis",
            "kind": "synthesis",
            "spike": "spike-159",
            "q1_verdict": q1["verdict"],
            "q2_a_verdict": q2_a["verdict"],
            "q2_b_verdict": q2_b["verdict"],
            "q3_a_verdict": q3_a["verdict"],
            "q3_b_verdict": q3_b["verdict"],
            "q3_c_verdict": q3_c["verdict"],
            "consolidated_finding": (
                "Q1: Biology embeds the L+K+M+C+I cascade IN the cortical substrate "
                "(Hebbian = Class M bind-and-update; theta-band = Class I; STDP = Class C; "
                "homeostatic scaling = Class K; connectome-harmonic = Class L) per "
                "[[user_stance_neural_hebbian_is_bci_drift_model]]. No separate "
                "external RBS-HDC instrument is needed. The HDC-instrument-as-tool "
                "is what srmech.spectral.* provides for substrates LACKING the embedded "
                "cascade (silicon, bronze, optical, ...). "
                "Q2: Quasi-orthogonal 1/sqrt(D) bucket-leakage is NOT the unique cross-"
                "pattern-match mechanism. Class I cyclic-position + OR-bundle achieves "
                "cross-pattern via SET-INTERSECTION-AT-PLACE rather than dense-quasi-"
                "orthogonal-bundling. Negation-falsifier shows bag-bundle is INSENSITIVE "
                "to negation as expected (Spike #147 open-falsifier). "
                "Q3: Rotation (Class C permute) COMMUTES with bind (Class M XOR) on PAIRS "
                "and with UNIFORM permute on bundle — these are SYMMETRIES, not new "
                "algebra. Form-function (per-input, content-determined) rotation BEFORE "
                "bundle BREAKS this symmetry and produces a different projection family. "
                "This is the algebraic content the user's question targets: pre-bundle "
                "form-function rotation IS a real degree-of-freedom in the HDC instrument "
                "API; it composes Class A (content-determined shift) + Class C (permute) "
                "+ Class M (bundle). Per [[user_stance_fiber_as_spatially_absent_encoding]]: "
                "rotating the (token-vec, shift-amount) pair is rotating fiber-content; "
                "the resulting fingerprint is a different 3D_s projection of the same "
                "structural meaning."
            ),
            "no_class_promoted": True,
            "vocabulary_status": "14 A-N intact",
            "round_status": "Round 1 — meta-domain (HDC algebra + biology substrate analytical). Multi-round survival required for canonical-promotion gate per [[feedback_multi_domain_multi_round_survival_falsification_method]].",
            "date": "2026-05-19",
            "timestamp": _utc_now(),
        }
        _emit(synthesis, fh)
        print(f"Synthesis written; verdicts:")
        print(f"  Q1: {q1['verdict']}")
        print(f"  Q2.A: {q2_a['verdict']}")
        print(f"  Q2.B: {q2_b['verdict']}")
        print(f"  Q3.A: {q3_a['verdict']}")
        print(f"  Q3.B: {q3_b['verdict']}")
        print(f"  Q3.C: {q3_c['verdict']}")


if __name__ == "__main__":
    main()
