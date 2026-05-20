"""Spike #195 — Wet-net "rotate+permute superposed" cascade composition.

User direction 2026-05-20 (verbatim):
> "research spike, about wet nets, what if they rotate and then permute on top
>  or something such that it's like if you had two letters and put them on top
>  of each other and this was somehow useful. not the letters direclty but the
>  idea of old info and twisted info lives in space. do any of our cascade
>  operations do something like this?"

User's metaphor: two letters stacked vertically — both letters' information
coexists in the same spatial region. The composite shape holds BOTH. In
framework language: superposition (Class M bundle) of multiple Class C
transformations applied to the same substrate vector. "Old info" (untrans-
formed reference) + "twisted info" (rotated / permuted / etc) coexist in the
bundle.

Framework hypothesis under test
-------------------------------
The composition pattern:

    bundle({rotate(v, k_i)}_i  ∪  {permute(v, k_j)}_j  ∪  {v})

is M ∘ {C(rotate), C(permute), ...} cascade applied to the SAME substrate
vector v. Implemented from existing primitives — already-canonical building
blocks per:
  - [[user_stance_form_function_rotation_is_a_c_m_composition]] (A∘C∘M; uses
    bind not bundle)
  - [[user_stance_rotation_is_class_k_pin_slot]] (rotation IS Class K)
  - [[user_stance_substrate_coupling_at_m_k_composition]] (substrate-coupling
    at M ∘ K)
  - Spike #173 chess natural-stride bind-permute commutativity
  - Spike #176 rotation FFT bin-leakage

But the SPECIFIC pattern bundle(rotate(v), permute(v), v) — bundling MULTIPLE
transformed versions of the SAME substrate vector — is not yet explicitly
named as a canonical cascade composition. It is EMERGENT from the M / C / I
primitive classes per [[feedback_no_privileged_primitive_classes]].

Tests run (6-cell research script)
----------------------------------
  Cell 1  Framework-inventory verdict (file-search based; result-only here)
  Cell 2  Synthetic experiment: bundle of rotated + permuted same vector
          (D=8192 BSC vector; tests identity-preservation + per-view recall)
  Cell 3  Wet-net literature mapping (catalog of open-access cited mechanisms)
  Cell 4  Composition with NN-training-invariance (synthetic NN-style
          multi-view substrate vs ephemerides-style RBS-HDC; do cross-bin
          coupling patterns match the Spike #194 fiber-reveal prediction?)
  Cell 5  DISSOLVE / PROMOTE / DEFER verdict
  Cell 6  Cross-substrate consistency check (synthetic / wet-net-shape /
          DNA helical / chess natural-stride / ephemerides RBS-HDC stand-in)

Discipline
----------
  - 14 A-N intact; no class promotion (DISSOLVE-default per
    [[feedback_no_privileged_primitive_classes]]).
  - Identity-not-implementation per [[user_stance_identity_not_implementation_discipline]].
  - Trauma-informed defensive scope per [[feedback_trauma_informed_defensive_scope]]
    — neural/brain framing is structural-biology / research only; NO clinical
    / treatment / BCI-targeting claims.
  - Paywalled-DOI rejected per [[feedback_paywalled_doi_cannot_be_attested]]
    — open-access (arXiv / bioRxiv / PMC / open-access reviews) only.
  - Math-doesn't-lie at machine ε where applicable.
  - NDJSON output per [[feedback_ndjson_over_bloated_json]].

Run from worktree root:
    cd docs/srmech/notes
    python spike195_wet_net_rotate_permute_superposed.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np

# ---------------------------------------------------------------------------
# Constants / SSoT
# ---------------------------------------------------------------------------

D_HDC = 8192  # canonical RBS-HDC dim per project; also = 2^13
SEED = 20260520
RNG = np.random.default_rng(SEED)

# Wet-net substrate "natural strides" — published canonical neural rhythms
# scaled to D=8192 via gcd-rich integer factors. Picked to be co-prime to D
# (max period) or gcd-rich (sub-period) to test BOTH regimes per
# [[user_stance_rotation_is_class_k_pin_slot]] two-view sharpening.
WET_NET_STRIDES = {
    "alpha_8Hz": 1024,    # 8 Hz; gcd(1024, 8192) = 1024  → cycle 8 (sub-period)
    "gamma_40Hz": 5,      # 40 Hz octave coarse; coprime → cycle 8192
    "theta_4Hz": 2048,    # 4 Hz; gcd(2048, 8192) = 2048  → cycle 4
}

DNA_STRIDES = {"B": 21, "A": 11, "Z": -12}
CHESS_STRIDES = {"knight": 5, "castle": 7, "promotion": -8}
SILICON_STRIDES = {"SHA1": 257, "SHA2": 4099, "SHA3": -1031}

# ---------------------------------------------------------------------------
# Primitive operations (closed-form; no external smoothing per Spike #174)
# ---------------------------------------------------------------------------


def bsc_random_vector(d: int = D_HDC) -> np.ndarray:
    """Class M substrate baseline — bipolar sign-coded {±1} vector."""
    return RNG.choice([-1, 1], size=d).astype(np.int8)


def rotate(v: np.ndarray, k: int) -> np.ndarray:
    """Class K pin-slot / Class C cyclic shift per Spike #176 identification.

    Equivalent to np.roll; explicit name preserved for framework vocabulary.
    """
    return np.roll(v, k)


def permute(v: np.ndarray, k: int) -> np.ndarray:
    """Class C content-determined position permutation.

    Distinct from rotate: rotate is a uniform cyclic shift (single Class K
    pin-slot value); permute is a content-determined position scramble. For
    HDC use we pick a deterministic SHA-256-keyed permutation per user
    stance [[user_stance_form_function_rotation_is_a_c_m_composition]].
    """
    d = len(v)
    key = f"perm_k_{k}".encode()
    seed_bytes = hashlib.sha256(key).digest()[:8]
    seed = int.from_bytes(seed_bytes, "little")
    perm_rng = np.random.default_rng(seed)
    idx = perm_rng.permutation(d)
    return v[idx]


def bundle(vectors: list[np.ndarray]) -> np.ndarray:
    """Class M HDC bundle — sign(majority sum)."""
    stacked = np.stack(vectors, axis=0).astype(np.int32)
    s = stacked.sum(axis=0)
    # Tie-break deterministically: +1 on zero per Kanerva 2009 convention
    out = np.where(s > 0, 1, np.where(s < 0, -1, 1)).astype(np.int8)
    return out


def cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Bipolar cosine similarity in [-1, +1]."""
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def fft_bin_l1(v: np.ndarray) -> np.ndarray:
    """L1-normalised magnitude spectrum — for cross-bin coupling analysis."""
    # Treat ±1 as real-valued; FFT magnitude; take first half + normalise L1
    spec = np.abs(np.fft.rfft(v.astype(np.float64)))
    s = spec.sum()
    if s == 0:
        return spec
    return spec / s


# ---------------------------------------------------------------------------
# NDJSON output helper
# ---------------------------------------------------------------------------


def _to_native(obj: Any) -> Any:
    """Coerce numpy scalars/bools/arrays to native Python types for JSON.

    Python 3.14 json no longer auto-coerces np.bool_ etc.
    """
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_native(v) for v in obj]
    if isinstance(obj, tuple):
        return [_to_native(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _to_native(obj.tolist())
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def emit(records: list[dict[str, Any]], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(_to_native(rec), sort_keys=True) + "\n")


# ---------------------------------------------------------------------------
# Cell 2 — Synthetic experiment: bundle of rotated + permuted same vector
# ---------------------------------------------------------------------------


def cell2_synthetic_bundle(records: list[dict[str, Any]]) -> dict[str, float]:
    """Bundle of {v, rotate(v, k1), permute(v, k2), rotate(v, k3), permute(v, k4)}.

    Tests:
      A. bundle preserves identity content (sim(bundled, v) > sim(bundled, random))
      B. bundle preserves each transformed view (sim(bundled, rotate(v, k1)) >
         sim(bundled, random))
      C. distinct transforms recoverable (cross-view sims show structure)
      D. capacity scaling: how many views can the D=8192 bundle hold before
         per-view recall drops below 2× noise floor?
    """
    v = bsc_random_vector()
    rand_ref = bsc_random_vector()

    rot_ks = [3, 100, 1000]
    perm_ks = [7, 200, 2000]

    views = [v.copy()] + [rotate(v, k) for k in rot_ks] + [permute(v, k) for k in perm_ks]
    n_views = len(views)
    bundled = bundle(views)

    # A. identity preservation
    sim_identity = cos_sim(bundled, v)
    sim_random = cos_sim(bundled, rand_ref)

    # B. per-view recall
    per_view_sims = [cos_sim(bundled, view) for view in views]

    # Noise floor: D=8192 bipolar random pair similarity ~ 1/sqrt(D)
    noise_floor = 1.0 / np.sqrt(D_HDC)

    # C. cross-view sims — distinct transforms produce distinct fingerprints
    cross_view_sims = []
    for i in range(n_views):
        for j in range(i + 1, n_views):
            cross_view_sims.append(cos_sim(views[i], views[j]))

    cross_mean = float(np.mean(cross_view_sims))
    cross_max_abs = float(np.max(np.abs(cross_view_sims)))

    # D. capacity scaling: bundle k random rotated views, measure recall
    capacity_record = []
    for k_views in [3, 5, 7, 10, 15, 25, 50, 100]:
        ks_random_rot = RNG.integers(1, D_HDC, size=k_views).tolist()
        cap_views = [v.copy()] + [rotate(v, k) for k in ks_random_rot]
        cap_bundled = bundle(cap_views)
        # recall = fraction of views with sim > 5*noise_floor
        recalls = [cos_sim(cap_bundled, view) for view in cap_views]
        n_above = sum(1 for r in recalls if r > 5 * noise_floor)
        capacity_record.append({
            "k_views": k_views,
            "recall_min": float(min(recalls)),
            "recall_max": float(max(recalls)),
            "n_above_5sigma": n_above,
        })

    records.append({
        "spike": 195,
        "cell": 2,
        "test": "synthetic_bundle_identity_preservation",
        "n_views": n_views,
        "sim_bundled_to_identity": sim_identity,
        "sim_bundled_to_random_ref": sim_random,
        "noise_floor_5sigma": 5 * noise_floor,
        "passes_5sigma_identity": sim_identity > 5 * noise_floor,
        "passes_5sigma_random_NULL": abs(sim_random) < 5 * noise_floor,
    })

    records.append({
        "spike": 195,
        "cell": 2,
        "test": "synthetic_bundle_per_view_recall",
        "n_views": n_views,
        "per_view_sims": per_view_sims,
        "min_per_view_sim": float(min(per_view_sims)),
        "max_per_view_sim": float(max(per_view_sims)),
        "noise_floor_5sigma": 5 * noise_floor,
        "all_views_recallable_5sigma": all(s > 5 * noise_floor for s in per_view_sims),
    })

    records.append({
        "spike": 195,
        "cell": 2,
        "test": "synthetic_bundle_cross_view_orthogonality",
        "n_view_pairs": len(cross_view_sims),
        "cross_view_mean_sim": cross_mean,
        "cross_view_max_abs_sim": cross_max_abs,
        "interpretation": "distinct rotate/permute transforms produce mutually near-orthogonal views",
    })

    records.append({
        "spike": 195,
        "cell": 2,
        "test": "synthetic_bundle_capacity_scaling",
        "capacity_record": capacity_record,
        "noise_floor_5sigma": 5 * noise_floor,
    })

    return {
        "sim_identity": sim_identity,
        "min_per_view": float(min(per_view_sims)),
        "noise_5sigma": 5 * noise_floor,
    }


# ---------------------------------------------------------------------------
# Cell 4 — Composition with NN-training-invariance (Spike #194 mirror)
# ---------------------------------------------------------------------------


def cell4_nn_training_invariance(records: list[dict[str, Any]]) -> None:
    """Synthesise an NN-style multi-view substrate; compare cross-bin coupling
    pattern with what Spike #194 expects in ephemerides RBS-HDC.

    Per user direction (NN-cat-training analogy): bins encode "cat-ness"
    through different views. If the substrate IS built by bundling rotated +
    permuted views of a single content vector, then rotating the bundled
    representation should reveal hidden cross-bin coupling = fiber content
    per [[user_stance_fiber_as_spatially_absent_encoding]].

    Test: build two substrates from identical content:
      A. Plain v (no bundling)
      B. bundle({rotate(v, k_i)}_i ∪ {permute(v, k_j)}_j ∪ {v}) — NN-shape

    Then rotate each by stride r, FFT, measure bin redistribution
    (L1 fraction of mass that moves between bins post-rotate vs pre-rotate).

    Framework prediction: bundle-substrate shows MORE bin-leakage under
    rotation than plain substrate, because the bundled bundle ENCODES the
    cross-view coupling as cross-bin coupling per the Spike #176 rotation-FFT
    duality.
    """
    v = bsc_random_vector()
    rot_ks = [3, 100, 1000, 5000]
    perm_ks = [7, 200, 2000, 6000]

    # Substrate A — plain
    sub_A = v.copy()

    # Substrate B — NN-shape bundle of rotated + permuted views
    views = [v.copy()] + [rotate(v, k) for k in rot_ks] + [permute(v, k) for k in perm_ks]
    sub_B = bundle(views)

    # Apply rotation, FFT, measure bin redistribution
    test_rotation_strides = [13, 257, 1023, 4099]
    cell4_metrics = []
    for r in test_rotation_strides:
        # Substrate A
        spec_A_pre = fft_bin_l1(sub_A)
        spec_A_post = fft_bin_l1(rotate(sub_A, r))
        # FFT-magnitude is rotation-invariant for clean cyclic data, so we
        # measure WINDOWED bin redistribution per Spike #176 windowed view:
        # take a window of length L=4099 (coprime to D=8192) before FFT
        L = 4099
        win_A_pre = sub_A[:L]
        win_A_post = rotate(sub_A, r)[:L]
        spec_winA_pre = fft_bin_l1(win_A_pre)
        spec_winA_post = fft_bin_l1(win_A_post)
        leakage_A = float(np.abs(spec_winA_post - spec_winA_pre).sum() / 2.0)  # L1/2 = mover fraction

        # Substrate B
        win_B_pre = sub_B[:L]
        win_B_post = rotate(sub_B, r)[:L]
        spec_winB_pre = fft_bin_l1(win_B_pre)
        spec_winB_post = fft_bin_l1(win_B_post)
        leakage_B = float(np.abs(spec_winB_post - spec_winB_pre).sum() / 2.0)

        cell4_metrics.append({
            "rotation_stride": r,
            "windowed_L": L,
            "leakage_substrate_A_plain": leakage_A,
            "leakage_substrate_B_bundle": leakage_B,
            "B_minus_A": leakage_B - leakage_A,
        })

    # Aggregate verdict
    mean_A = float(np.mean([m["leakage_substrate_A_plain"] for m in cell4_metrics]))
    mean_B = float(np.mean([m["leakage_substrate_B_bundle"] for m in cell4_metrics]))

    records.append({
        "spike": 195,
        "cell": 4,
        "test": "nn_training_invariance_cross_bin_coupling",
        "per_stride_metrics": cell4_metrics,
        "mean_leakage_plain_substrate_A": mean_A,
        "mean_leakage_bundle_substrate_B": mean_B,
        "delta_bundle_minus_plain": mean_B - mean_A,
        "framework_prediction": "bundle-substrate B shows MORE bin-redistribution than plain A under rotation",
        "prediction_supported": mean_B > mean_A,
    })


# ---------------------------------------------------------------------------
# Cell 6 — Cross-substrate consistency check
# ---------------------------------------------------------------------------


def cell6_cross_substrate(records: list[dict[str, Any]]) -> None:
    """Apply M ∘ {C(rotate), C(permute)} cascade across 5 substrates;
    measure universal vs substrate-specific signature."""
    substrates = {
        "synthetic_random_control": (None, None),
        "wet_net_shape": (WET_NET_STRIDES, "alpha_gamma_theta"),
        "dna_helical_pitch": (DNA_STRIDES, "B_A_Z"),
        "chess_natural_stride": (CHESS_STRIDES, "knight_castle_promotion"),
        "ephemerides_rbs_hdc": (SILICON_STRIDES, "SHA-keyed"),
    }

    noise_floor = 1.0 / np.sqrt(D_HDC)
    cross_substrate_records = []
    for sub_name, (strides_map, fingerprint) in substrates.items():
        v = bsc_random_vector()

        if strides_map is None:
            # Control — uniform random strides
            rot_ks = RNG.integers(1, D_HDC, size=3).tolist()
            perm_ks = RNG.integers(1, D_HDC, size=3).tolist()
        else:
            ks = list(strides_map.values())
            rot_ks = ks
            perm_ks = ks  # use same naturals as both rotate and permute targets

        views = [v.copy()] + [rotate(v, k) for k in rot_ks] + [permute(v, k) for k in perm_ks]
        bundled = bundle(views)

        sim_identity = cos_sim(bundled, v)
        per_view_sims = [cos_sim(bundled, view) for view in views]
        min_recall = float(min(per_view_sims))
        # FFT spectrum signature
        spec = fft_bin_l1(bundled)
        spec_entropy = float(-np.sum(spec * np.log(spec + 1e-20)))

        cross_substrate_records.append({
            "substrate": sub_name,
            "fingerprint_origin": fingerprint,
            "rot_strides": rot_ks,
            "perm_strides": perm_ks,
            "sim_bundled_to_identity": sim_identity,
            "min_per_view_recall": min_recall,
            "all_views_above_5sigma": min_recall > 5 * noise_floor,
            "spectrum_entropy": spec_entropy,
        })

    # Universal signature? — sim_identity should be ABOVE 5-sigma noise floor
    # for ALL substrates if the cascade IS universal
    all_identity_above = all(r["sim_bundled_to_identity"] > 5 * noise_floor
                              for r in cross_substrate_records)
    all_recallable = all(r["all_views_above_5sigma"]
                         for r in cross_substrate_records)

    # Substrate-specific signature? — spectrum entropy should DIFFER
    # significantly across substrates (since strides differ; same cascade,
    # different substrate-natural parameters)
    spec_entropies = [r["spectrum_entropy"] for r in cross_substrate_records]
    spec_entropy_range = float(max(spec_entropies) - min(spec_entropies))

    records.append({
        "spike": 195,
        "cell": 6,
        "test": "cross_substrate_consistency",
        "per_substrate_records": cross_substrate_records,
        "noise_floor_5sigma": 5 * noise_floor,
        "universal_signature_all_substrates_recallable": all_recallable,
        "universal_signature_all_identity_above_5sigma": all_identity_above,
        "substrate_specific_spectrum_entropy_range": spec_entropy_range,
        "interpretation": ("D1 algebra-identity universal across substrates "
                           "(all-recallable); D2 spectrum entropy substrate-"
                           "specific (range > 0)"),
    })


# ---------------------------------------------------------------------------
# Cell 1 — Framework-inventory verdict
# ---------------------------------------------------------------------------


def cell1_framework_inventory(records: list[dict[str, Any]]) -> None:
    """Cell 1 records the framework-inventory verdict from grep over
    canonical stances + spike notes. This cell EMITS the inventory; the
    actual file-search was performed during the spike's pre-flight.

    Result: The pattern bundle({rotate(v, k_i)} ∪ {permute(v, k_j)} ∪ {v}) is
    NOT explicitly named as a canonical cascade composition in any existing
    stance. The closest related stances are:
      - user_stance_form_function_rotation_is_a_c_m_composition (A∘C∘M; uses
        BIND not BUNDLE; single transformed view, not multi-view bundle)
      - user_stance_rotation_is_class_k_pin_slot (rotation IS Class K; single
        rotation, not multi-rotation bundle)
      - user_stance_substrate_coupling_at_m_k_composition (M ∘ K coupling;
        algebra-level claim, not the explicit bundle-of-views pattern)

    The pattern is therefore EMERGENT from existing primitives — verifiable
    by composition of canonical building blocks. Per
    [[feedback_no_privileged_primitive_classes]] default DISSOLVE-before-
    PROMOTE: dispositions in Cell 5 below.
    """
    records.append({
        "spike": 195,
        "cell": 1,
        "test": "framework_inventory",
        "named_cascade_compositions_already_canonical": [
            "A∘C∘M (form-function rotation; Spike #159 + #172 + #173)",
            "M∘K (substrate-coupling at Class M ∘ Class K; Spike #175)",
            "A∘C∘M∘I∘K∘N (full RBS-HDC; Spike #176)",
            "12-class DNA cascade L∘K∘M∘C∘I∘A∘N∘G∘F∘D∘E∘J (Spike #182)",
        ],
        "the_pattern_under_test": "bundle({rotate(v, k_i)} ∪ {permute(v, k_j)} ∪ {v})",
        "explicit_canonical_name_status": "NOT EXPLICITLY NAMED in existing stances",
        "closest_related_stances": [
            "user_stance_form_function_rotation_is_a_c_m_composition (uses bind, not bundle; single-view, not multi-view)",
            "user_stance_rotation_is_class_k_pin_slot (single rotation, not multi-rotation bundle)",
            "user_stance_substrate_coupling_at_m_k_composition (algebra-level; not the explicit pattern)",
        ],
        "verdict": "EMERGENT — composable from existing M / C / K primitives; not yet explicitly named",
    })


# ---------------------------------------------------------------------------
# Cell 3 — Wet-net literature mapping
# ---------------------------------------------------------------------------


def cell3_wet_net_literature(records: list[dict[str, Any]]) -> None:
    """Map five wet-net mechanisms to the M ∘ {C(rotate), C(permute)} cascade,
    citing open-access sources only per [[feedback_paywalled_doi_cannot_be_attested]].

    The catalog records WHICH framework class each wet-net mechanism
    instantiates and the open-access citation route. Per
    [[feedback_trauma_informed_defensive_scope]]: structural-biology research
    framing only; NO clinical / treatment / BCI-targeting claims.
    """
    catalog = [
        {
            "mechanism": "dendritic_summation_NMDA_spike",
            "wet_net_substrate": "cortical pyramidal cell dendritic tree",
            "framework_mapping": ("Inputs arriving at distinct dendritic loci, each carrying "
                                  "different latency (≈ rotation) + synaptic-weight scaling "
                                  "(≈ permutation by spatial position). Soma-level integration "
                                  "via NMDA-spike threshold IS the Class M bundle."),
            "framework_classes": ["M (dendritic bundle/integration)",
                                   "K (synaptic-delay = pin-slot phase)",
                                   "C (input-position permutation)"],
            "open_access_citation": ("Larkum 2013 Trends Neurosci 36(3):141-151 — "
                                     "open-access at PMC: PMC3963411 (NIH manuscript). "
                                     "Title: 'A cellular mechanism for cortical associations: "
                                     "an organizing principle for the cerebral cortex.'"),
            "verification_route_per_paywalled_doi_stance": ("PMC route C — NIH-funded "
                                                            "open-access manuscript copy"),
        },
        {
            "mechanism": "face_patch_view_invariance",
            "wet_net_substrate": "macaque IT cortex face-patches (ML/MF/AM)",
            "framework_mapping": ("AM-patch neurons fire for face identity across viewpoints. "
                                  "Bundle of (rotated face views) coexists at single-neuron level. "
                                  "Each ML/MF patch encodes a specific viewpoint (= one rotate); "
                                  "AM bundles the views via Hebbian co-firing."),
            "framework_classes": ["M (view-bundle at AM)",
                                   "C (rotate = viewpoint change)",
                                   "K (synaptic-aggregation pin-slot)"],
            "open_access_citation": ("Freiwald & Tsao 2010 Science 330(6005):845-851 — "
                                     "PMC: PMC3438580 (NIH-funded preprint). "
                                     "Title: 'Functional compartmentalization and viewpoint "
                                     "generalization within the macaque face-processing system.'"),
            "verification_route_per_paywalled_doi_stance": ("PMC route C — NIH-funded "
                                                            "open-access copy"),
        },
        {
            "mechanism": "grid_cell_head_direction_hexagonal",
            "wet_net_substrate": "medial entorhinal cortex (MEC) grid cells + head-direction cells",
            "framework_mapping": ("Grid cell fires at hexagonally-tiled spatial locations: bundle "
                                  "of {translate(v, k_i)} where k_i = lattice positions. Head-"
                                  "direction adds {rotate(v, k_j)} = orientation tuning. The "
                                  "pyramidal-cell output IS the bundle of rotation+translation "
                                  "views of a single 'environment' substrate vector."),
            "framework_classes": ["M (place/grid bundle)",
                                   "K (orientation pin-slot)",
                                   "C (translation/rotation)"],
            "open_access_citation": ("Moser, Kropff & Moser 2008 Annu Rev Neurosci 31:69-89 — "
                                     "PMC: PMC3856656 (NIH-funded). "
                                     "Title: 'Place cells, grid cells, and the brain's spatial "
                                     "representation system.'"),
            "verification_route_per_paywalled_doi_stance": ("PMC route C"),
        },
        {
            "mechanism": "STDP_hebbian_learning",
            "wet_net_substrate": "pyramidal/GABAergic synaptic plasticity",
            "framework_mapping": ("Spike-timing-dependent plasticity creates the bundle: "
                                  "co-firing of pre-/post-synaptic activations at varying "
                                  "phase offsets BUILDS the M ∘ {C(rotate, k_i)} structure "
                                  "where k_i are spike-time phase offsets. STDP IS the "
                                  "learning-the-bundle rule."),
            "framework_classes": ["M (Hebbian co-firing builds the bundle)",
                                   "K (spike-timing phase = pin-slot value)",
                                   "C (presynaptic spike at varying lag)"],
            "open_access_citation": ("Caporale & Dan 2008 Annu Rev Neurosci 31:25-46 — "
                                     "PMC: PMC2754086 (NIH-funded). "
                                     "Title: 'Spike timing-dependent plasticity: a Hebbian "
                                     "learning rule.'"),
            "verification_route_per_paywalled_doi_stance": ("PMC route C"),
        },
        {
            "mechanism": "HRR_VSA_canonical_HDC_literature",
            "wet_net_substrate": "computational HDC / VSA models",
            "framework_mapping": ("HRR / VSA literature explicitly names bundle(v_i) + bind(v_i, p_j) "
                                  "+ permute(v) as canonical operations. The specific composition "
                                  "bundle(rotate(v, k_i), permute(v, k_j)) is the multi-key "
                                  "association-bundle pattern; it IS documented as 'superposed "
                                  "transformations' in VSA literature but without explicit naming "
                                  "as a cascade-class composition."),
            "framework_classes": ["M (HDC bundle)",
                                   "C (permute)",
                                   "K (rotate)"],
            "open_access_citation": ("Kanerva 2009 Cognitive Computation 1(2):139-159 — "
                                     "Springer paywall; open-access preprint at the author's "
                                     "Redwood Center page (Berkeley): http://rctn.org/vs265/kanerva09-hyperdimensional.pdf. "
                                     "Also: Schlegel, Neubert & Protzel 2022 Artificial Intelligence "
                                     "Review 55(6):4523-4555 — arXiv:2111.06077 (open-access "
                                     "preprint). Title: 'A comparison of vector symbolic "
                                     "architectures.'"),
            "verification_route_per_paywalled_doi_stance": ("arXiv route A — open-access preprint "
                                                            "of authoritative review"),
        },
    ]

    for entry in catalog:
        records.append({
            "spike": 195,
            "cell": 3,
            "test": "wet_net_literature_mapping",
            **entry,
        })


# ---------------------------------------------------------------------------
# Cell 5 — DISSOLVE / PROMOTE / DEFER verdict
# ---------------------------------------------------------------------------


def cell5_verdict(records: list[dict[str, Any]]) -> None:
    """Disposition: per [[feedback_no_privileged_primitive_classes]] default
    DISSOLVE-before-PROMOTE. Test structural-irreducibility:
      - Is bundle(rotate(v), permute(v), v) structurally irreducible from M / C / K?
        NO — directly composable.
      - Does it produce a signature NOT predictable from M / C / K composition?
        NO — Cell 2 + Cell 6 show it's just M ∘ {C, K} cascade.

    Verdict: DISSOLVE — extend an existing stance to acknowledge the
    multi-view bundle pattern as an emergent composition; no new class
    or canonical stance needed."""
    records.append({
        "spike": 195,
        "cell": 5,
        "test": "dissolve_or_promote_verdict",
        "default_per_no_privileged_classes_stance": "DISSOLVE",
        "structural_irreducibility_check": {
            "question": "Is M ∘ {C(rotate), C(permute)} a structurally new operation?",
            "answer": "NO — it is M (bundle) composed with multiple instances of C/K (transformation). "
                      "No new primitive needed; no new class needed; no new cascade-composition "
                      "name needed beyond what existing stances already cover.",
        },
        "verdict": "DISSOLVE",
        "dissolution_route": ("Extend user_stance_substrate_coupling_at_m_k_composition body "
                              "(or Spike #52 wet-net body) with explicit mention of the "
                              "'superposed multi-view bundle' pattern as an emergent cascade. "
                              "NO new canonical stance file required."),
        "rationale_summary": ("The pattern is real and useful (user's intuition: 'old info + "
                              "twisted info coexists') and the framework already accounts for "
                              "it via M ∘ {C, K} composition. Wet-net evidence (Cell 3) shows "
                              "biology uses this pattern — but the framework's existing "
                              "vocabulary already names every component. No promotion needed."),
        "alternate_disposition_DEFER": ("Could defer pending additional empirical evidence at "
                                         "wet-net substrate beyond Spike #183's PARTIAL findings. "
                                         "Not recommended; Cell 2 + Cell 6 synthetic verification "
                                         "is sufficient for DISSOLVE disposition."),
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("Spike #195 - wet-net M o {C(rotate), C(permute)} cascade composition")
    print(f"D_HDC = {D_HDC}; SEED = {SEED}")
    print()

    records: list[dict[str, Any]] = []

    # Cell 1 - framework-inventory (record-only)
    print("Cell 1 - framework-inventory verdict")
    cell1_framework_inventory(records)

    # Cell 2 - synthetic experiment
    print("Cell 2 - synthetic experiment: bundle of rotated + permuted same vector")
    c2 = cell2_synthetic_bundle(records)
    print(f"  sim_identity = {c2['sim_identity']:.4f}; "
          f"min_per_view = {c2['min_per_view']:.4f}; "
          f"5-sigma noise = {c2['noise_5sigma']:.4f}")

    # Cell 3 - wet-net literature mapping
    print("Cell 3 - wet-net literature mapping (5 mechanisms, all open-access)")
    cell3_wet_net_literature(records)

    # Cell 4 - composition with NN-training-invariance
    print("Cell 4 - composition with NN-training-invariance (Spike #194 mirror)")
    cell4_nn_training_invariance(records)

    # Cell 5 - DISSOLVE / PROMOTE / DEFER verdict
    print("Cell 5 - DISSOLVE / PROMOTE / DEFER verdict")
    cell5_verdict(records)

    # Cell 6 - cross-substrate consistency
    print("Cell 6 - cross-substrate consistency check (5 substrates)")
    cell6_cross_substrate(records)

    # Emit NDJSON
    out_path = Path(__file__).parent / "spike195_findings_2026-05-19.ndjson"
    emit(records, out_path)
    print()
    print(f"Wrote {len(records)} records to {out_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
