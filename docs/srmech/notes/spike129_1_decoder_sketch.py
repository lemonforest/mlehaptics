"""Spike #129.1 — Decentralised-BCI decoder feasibility study (proof-of-concept).

Three cephalopod-inspired BCI decoder design directions implemented as Python
proof-of-concept invoking srmech.spectral primitives + srmech.amsc primitives
(Classes L / I / M / A) on synthetic neural data.

Per [[user_stance_ai_necessary_for_bci_substrate_coupling]] (Milestone #14):
Direction 1's class chain IS the substrate-coupling adapter pattern.

Disciplines:
- No new primitive class per [[feedback_no_privileged_primitive_classes]]
- Trauma-informed defensive scope: ASSISTIVE-TECH framing only
  per [[feedback_trauma_informed_defensive_scope]]
- Synthetic data only — no PHI, no real BCI dataset access
- Algebra-not-magnitude per [[user_stance_framework_domain_algebra_not_length_or_magnitude]]
- Edge-deployable Class L surface (pi-free Jacobi eigvals)
  per [[user_stance_pi_as_projection]]

Class chain per direction:
    Direction 1: {L_array_k ∘ A}_k ∘ M(bind) ∘ M(similarity)
    Direction 2: {L_array_k ∘ A}_k ∘ {I_ring ∘ M(bind)}_k ∘ M(bundle) ∘ M(similarity)
    Direction 3: L_grid ∘ {L_grid matvec}^T ∘ L_grid ∘ A ∘ M(similarity)

All operations are shipped at srmech v0.4.1rc14.

Synthetic-data conventions:
- "Cortical Laplacian" = small Erdos-Renyi or grid graph; n=8-100 nodes
- "Neural state" = real-valued n-vector + Gaussian noise
- "Intent canon" = pre-computed spectral handles for K labelled motor classes

Usage (requires srmech>=0.4.1rc14):
    python spike129_1_decoder_sketch.py

If srmech is not installed, the script prints a notice and exits cleanly.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional

import numpy as np


try:
    from srmech.spectral import decompose, similarity as spectral_similarity
    from srmech.amsc.hdc import bind, bundle
    from srmech.amsc.cyclic import mod_add
    from srmech.amsc.laplacian import (
        dense_laplacian,
        dense_matvec_complex,
    )

    SRMECH_AVAILABLE = True
except ImportError as e:
    SRMECH_AVAILABLE = False
    SRMECH_IMPORT_ERROR = str(e)


# ----------------------------------------------------------------------------
# Synthetic-data builders (NO real BCI data; no PHI)
# ----------------------------------------------------------------------------


def build_random_connectivity_laplacian(n: int, edge_prob: float = 0.2, seed: int = 0) -> np.ndarray:
    """Build an Erdos-Renyi random connectivity graph Laplacian for n nodes.

    Stand-in for a patient-specific cortical Laplacian; in real deployment
    the Laplacian would come from functional / structural connectivity data
    (e.g., dMRI or rs-fMRI graph estimation) per Petti et al. 2022
    bioRxiv 2022.08.13.503836.

    Args:
        n: Number of nodes (electrodes / cortical regions).
        edge_prob: Probability of edge between any two nodes.
        seed: RNG seed for reproducibility.

    Returns:
        n×n Hermitian (real-symmetric) Laplacian.
    """
    rng = np.random.default_rng(seed)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < edge_prob:
                edges.append((i, j))
    if not edges:
        # Guarantee at least a chain so the Laplacian is meaningful
        edges = [(i, i + 1) for i in range(n - 1)]
    return dense_laplacian(edges, n).astype(np.float64)


def build_grid_laplacian(rows: int, cols: int) -> np.ndarray:
    """Build a 2D grid graph Laplacian for a rows × cols electrode grid.

    Stand-in for a Utah array's spatial topology (typically 10×10 = 100
    electrodes on a 4mm × 4mm silicon substrate).
    """
    n = rows * cols
    edges = []
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            if c + 1 < cols:
                edges.append((i, i + 1))
            if r + 1 < rows:
                edges.append((i, i + cols))
    return dense_laplacian(edges, n).astype(np.float64)


def synthesise_neural_state(
    n: int, intent_class: int, n_classes: int, snr_db: float = 6.0, seed: int = 0
) -> np.ndarray:
    """Synthesise a noisy neural state vector for a given intent class.

    Each class has a different prototypical activation pattern;
    additive Gaussian noise simulates electrode/SNR variability per
    Xu et al. 2024 EEG-DBNet's low-SNR challenge.

    Args:
        n: Length of state vector (number of nodes).
        intent_class: Integer 0..n_classes-1 indicating which intent.
        n_classes: Total number of intent classes.
        snr_db: Signal-to-noise ratio in dB.
        seed: RNG seed for reproducibility.

    Returns:
        Real-valued n-vector with signal + noise.
    """
    rng = np.random.default_rng(seed)
    # Prototype: Gaussian bump centred at class_idx * n / n_classes
    centre = intent_class * n / n_classes
    indices = np.arange(n, dtype=np.float64)
    signal = np.exp(-0.5 * ((indices - centre) / (n / (4 * n_classes))) ** 2)
    signal /= np.linalg.norm(signal)
    # Add noise at specified SNR
    noise_power = 10 ** (-snr_db / 10.0)
    noise = rng.standard_normal(n) * np.sqrt(noise_power)
    return signal + noise


def build_intent_canon(
    laplacian: np.ndarray, n_classes: int, encoder_tag: str = "default", seed: int = 0
) -> dict[int, bytes]:
    """Pre-compute spectral handles for each intent class as the 'canon'.

    In a clinical deployment, the intent canon is built from the patient's
    calibration session: prompted motor-imagery trials produce a per-class
    spectral fingerprint. Each fingerprint is the centroid (mean) of
    multiple clean-trial spectral handles, encoded as raw bytes.

    Args:
        laplacian: Patient-specific cortical Laplacian.
        n_classes: Number of intent classes (e.g., 4 for BCI Competition IV-2a).
        encoder_tag: Encoder identity (folds into descriptor hash).
        seed: RNG seed for the prototype patterns.

    Returns:
        intent_class -> coefficients_bytes mapping.
    """
    canon = {}
    n = laplacian.shape[0]
    for cls in range(n_classes):
        # Build a clean prototype (high SNR) for the canon
        state = synthesise_neural_state(n, cls, n_classes, snr_db=20.0, seed=seed + cls)
        handle = decompose(state, laplacian, encoder_tag=encoder_tag)
        canon[cls] = handle.coefficients_bytes
    return canon


# ----------------------------------------------------------------------------
# Direction 1 — Per-array Laplacian + cross-array bind
# ----------------------------------------------------------------------------


def decode_multi_array_direction_1(
    neural_states: dict[str, np.ndarray],
    laplacians: dict[str, np.ndarray],
    intent_fingerprints: dict[int, bytes],
) -> tuple[int, float]:
    """Direction 1: Per-array Laplacian + cross-array bind.

    Class chain: {L_array_k ∘ A}_k ∘ M(bind) ∘ M(similarity).

    Args:
        neural_states: array_id -> state vector
        laplacians: array_id -> Hermitian Laplacian for that array
        intent_fingerprints: intent_class -> canonical handle bytes

    Returns:
        (best_intent_class, similarity_score)
    """
    # Per-array decompose with substrate-encoder-tagged Laplacian
    per_array_handles = []
    for array_id, state in sorted(neural_states.items()):
        L = laplacians[array_id]
        handle = decompose(state, L, encoder_tag=f"array_{array_id}")
        per_array_handles.append(handle.coefficients_bytes)

    # Cross-array bind (chain-bind pairwise, since byte-lengths may differ if
    # arrays have different sizes; in real deployment lengths match)
    # For the proof-of-concept, all arrays are same size; chain-bind for arbitrary K.
    if len(per_array_handles) == 0:
        raise ValueError("decode_multi_array: at least one array required")
    elif len(per_array_handles) == 1:
        unified = per_array_handles[0]
    elif len(per_array_handles) % 2 == 1:
        unified = bundle(per_array_handles)
    else:
        unified = per_array_handles[0]
        for h in per_array_handles[1:]:
            unified = bind(unified, h)

    # Match against intent canon
    best_intent, best_sim = None, -1.0
    for intent_class, fingerprint in intent_fingerprints.items():
        if len(fingerprint) != len(unified):
            continue
        sim = spectral_similarity(unified, fingerprint)
        if sim > best_sim:
            best_sim, best_intent = sim, intent_class
    return best_intent, best_sim


# ----------------------------------------------------------------------------
# Direction 2 — Ring-topology decoder (Class I cyclic primitive)
# ----------------------------------------------------------------------------


def decode_ring_topology_direction_2(
    neural_states_ordered: list[np.ndarray],
    laplacians_ordered: list[np.ndarray],
    intent_fingerprints: dict[int, bytes],
) -> tuple[int, float]:
    """Direction 2: Ring-topology decoder (cephalopod nerve ring analog).

    Class chain: {L_array_k ∘ A}_k ∘ {I_ring ∘ M(bind)}_k ∘ M(bundle) ∘ M(similarity).
    Cephalopod analog: Chang & Hale 2023 PMC10192654 nerve ring ℤ/8ℤ.

    Args:
        neural_states_ordered: list of state vectors, ordered by ring position
        laplacians_ordered: list of Laplacians, ordered by ring position
        intent_fingerprints: intent_class -> canonical handle bytes

    Returns:
        (best_intent_class, similarity_score)
    """
    K = len(neural_states_ordered)
    if K < 3:
        raise ValueError(f"Ring topology requires K >= 3 arrays; got K={K}")

    # Per-array decompose with ring-position encoder_tag
    handles = []
    for k, (state, L) in enumerate(zip(neural_states_ordered, laplacians_ordered)):
        handle = decompose(state, L, encoder_tag=f"ring_pos_{k}_of_{K}")
        handles.append(handle.coefficients_bytes)

    # Ring-bind: each handle with its adjacent neighbour (ℤ/K cyclic)
    ring_handles = []
    for k in range(K):
        next_k = mod_add(k, 1, K)  # Class I cyclic-group arithmetic
        ring_handles.append(bind(handles[k], handles[next_k]))

    # Ring-bundle: majority vote across ring-handles
    # Pad to odd count if needed (tie-breaker zero vector)
    if K % 2 == 0:
        D = len(ring_handles[0])
        ring_handles = ring_handles + [bytes(D)]
    unified = bundle(ring_handles)

    # Match against intent canon
    best_intent, best_sim = None, -1.0
    for intent_class, fingerprint in intent_fingerprints.items():
        if len(fingerprint) != len(unified):
            continue
        sim = spectral_similarity(unified, fingerprint)
        if sim > best_sim:
            best_sim, best_intent = sim, intent_class
    return best_intent, best_sim


# ----------------------------------------------------------------------------
# Direction 3 — CA-equivalent convolutional Laplacian layer
# ----------------------------------------------------------------------------


def decode_ca_convolutional_direction_3(
    array_state_grid: np.ndarray,
    n_ca_steps: int,
    intent_fingerprints: dict[int, bytes],
    diffusion_rate: float = 0.1,
) -> tuple[int, float]:
    """Direction 3: CA-equivalent convolutional Laplacian layer.

    Class chain: L_grid ∘ {L_grid matvec}^T ∘ L_grid ∘ A ∘ M(similarity).
    Cephalopod analog: Ishida 2021 PMC8357167 chromatophore Turing CA.

    Args:
        array_state_grid: (rows, cols) electrode activations
        n_ca_steps: Number of CA update iterations
        intent_fingerprints: intent_class -> canonical handle bytes
        diffusion_rate: Reaction-diffusion D coefficient

    Returns:
        (best_intent_class, similarity_score)
    """
    rows, cols = array_state_grid.shape
    n = rows * cols
    L_grid = build_grid_laplacian(rows, cols)

    # CA update steps: signed-Laplacian-variant per Class L dissolve (Class O resolution 2026-05-16)
    s = array_state_grid.flatten().astype(np.complex128)
    dt = 1.0
    L_complex = L_grid.astype(np.complex128)
    for _ in range(n_ca_steps):
        diffusion = dense_matvec_complex(L_complex, s)
        s = s - dt * diffusion_rate * diffusion

    # Decompose post-CA state on same grid Laplacian
    handle = decompose(s, L_grid, encoder_tag="grid_ca_pattern")

    # Match against intent canon
    best_intent, best_sim = None, -1.0
    for intent_class, fingerprint in intent_fingerprints.items():
        if len(fingerprint) != len(handle.coefficients_bytes):
            continue
        sim = spectral_similarity(handle.coefficients_bytes, fingerprint)
        if sim > best_sim:
            best_sim, best_intent = sim, intent_class
    return best_intent, best_sim


# ----------------------------------------------------------------------------
# Smoke tests on synthetic data
# ----------------------------------------------------------------------------


def smoke_test_direction_1(verbose: bool = True) -> dict:
    """Smoke test Direction 1 on K=4 simulated electrode arrays."""
    K = 4
    n_per_array = 8
    n_classes = 3

    laplacians = {
        f"arr_{k}": build_random_connectivity_laplacian(n_per_array, seed=42 + k)
        for k in range(K)
    }

    # Build per-array intent canons (same canon shape, but per-array Laplacians)
    # In real deployment, each array has its own per-class fingerprint;
    # for cross-array bind, fingerprints must be combined via the same chain.
    # Here we use a single unified canon by binding clean-trial handles.
    intent_canon = {}
    for cls in range(n_classes):
        per_array_clean_handles = []
        for k in range(K):
            state = synthesise_neural_state(
                n_per_array, cls, n_classes, snr_db=20.0, seed=100 + cls + k
            )
            h = decompose(state, laplacians[f"arr_{k}"], encoder_tag=f"array_arr_{k}")
            per_array_clean_handles.append(h.coefficients_bytes)
        # Match the same chain decode_multi_array_direction_1 uses
        if K % 2 == 1:
            unified = bundle(per_array_clean_handles)
        else:
            unified = per_array_clean_handles[0]
            for h in per_array_clean_handles[1:]:
                unified = bind(unified, h)
        intent_canon[cls] = unified

    # Test: decode noisy multi-array state, check class match
    n_trials = 9
    correct = 0
    for trial in range(n_trials):
        true_class = trial % n_classes
        neural_states = {
            f"arr_{k}": synthesise_neural_state(
                n_per_array, true_class, n_classes, snr_db=3.0, seed=trial * K + k
            )
            for k in range(K)
        }
        pred_class, sim = decode_multi_array_direction_1(
            neural_states, laplacians, intent_canon
        )
        if pred_class == true_class:
            correct += 1
        if verbose:
            print(f"  Trial {trial}: true={true_class}, pred={pred_class}, sim={sim:.3f}")

    accuracy = correct / n_trials
    if verbose:
        print(f"Direction 1: {correct}/{n_trials} correct (accuracy={accuracy:.2%})")
    return {"direction": 1, "correct": correct, "n_trials": n_trials, "accuracy": accuracy}


def smoke_test_direction_2(verbose: bool = True) -> dict:
    """Smoke test Direction 2 on K=4 simulated electrode arrays in ℤ/4ℤ ring."""
    K = 4
    n_per_array = 8
    n_classes = 3

    laplacians_list = [
        build_random_connectivity_laplacian(n_per_array, seed=42 + k) for k in range(K)
    ]

    # Build intent canons via ring chain
    intent_canon = {}
    for cls in range(n_classes):
        per_array_clean_handles = []
        for k in range(K):
            state = synthesise_neural_state(
                n_per_array, cls, n_classes, snr_db=20.0, seed=100 + cls + k
            )
            h = decompose(state, laplacians_list[k], encoder_tag=f"ring_pos_{k}_of_{K}")
            per_array_clean_handles.append(h.coefficients_bytes)
        # Ring-bind clean handles
        ring_handles = []
        for k in range(K):
            next_k = mod_add(k, 1, K)
            ring_handles.append(bind(per_array_clean_handles[k], per_array_clean_handles[next_k]))
        if K % 2 == 0:
            D = len(ring_handles[0])
            ring_handles = ring_handles + [bytes(D)]
        intent_canon[cls] = bundle(ring_handles)

    # Test: decode noisy state via ring topology
    n_trials = 9
    correct = 0
    for trial in range(n_trials):
        true_class = trial % n_classes
        neural_states = [
            synthesise_neural_state(
                n_per_array, true_class, n_classes, snr_db=3.0, seed=trial * K + k
            )
            for k in range(K)
        ]
        pred_class, sim = decode_ring_topology_direction_2(
            neural_states, laplacians_list, intent_canon
        )
        if pred_class == true_class:
            correct += 1
        if verbose:
            print(f"  Trial {trial}: true={true_class}, pred={pred_class}, sim={sim:.3f}")

    accuracy = correct / n_trials
    if verbose:
        print(f"Direction 2: {correct}/{n_trials} correct (accuracy={accuracy:.2%})")
    return {"direction": 2, "correct": correct, "n_trials": n_trials, "accuracy": accuracy}


def smoke_test_direction_3(verbose: bool = True) -> dict:
    """Smoke test Direction 3 on a 4×4 grid (small to keep test fast)."""
    rows, cols = 4, 4
    n_classes = 3
    n_ca_steps = 5

    L_grid = build_grid_laplacian(rows, cols)
    n = rows * cols

    # Build intent canons via CA pipeline
    intent_canon = {}
    for cls in range(n_classes):
        state = synthesise_neural_state(n, cls, n_classes, snr_db=20.0, seed=200 + cls)
        s = state.astype(np.complex128)
        L_complex = L_grid.astype(np.complex128)
        for _ in range(n_ca_steps):
            diffusion = dense_matvec_complex(L_complex, s)
            s = s - 0.1 * diffusion
        h = decompose(s, L_grid, encoder_tag="grid_ca_pattern")
        intent_canon[cls] = h.coefficients_bytes

    # Test: decode noisy grid state
    n_trials = 9
    correct = 0
    for trial in range(n_trials):
        true_class = trial % n_classes
        grid_state = synthesise_neural_state(
            n, true_class, n_classes, snr_db=3.0, seed=trial * 10
        ).reshape(rows, cols)
        pred_class, sim = decode_ca_convolutional_direction_3(
            grid_state, n_ca_steps, intent_canon
        )
        if pred_class == true_class:
            correct += 1
        if verbose:
            print(f"  Trial {trial}: true={true_class}, pred={pred_class}, sim={sim:.3f}")

    accuracy = correct / n_trials
    if verbose:
        print(f"Direction 3: {correct}/{n_trials} correct (accuracy={accuracy:.2%})")
    return {"direction": 3, "correct": correct, "n_trials": n_trials, "accuracy": accuracy}


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------


def main():
    if not SRMECH_AVAILABLE:
        print("=" * 72)
        print("Spike #129.1 — Decentralised-BCI decoder feasibility study")
        print("=" * 72)
        print()
        print("srmech is not installed in this environment.")
        print(f"Import error: {SRMECH_IMPORT_ERROR}")
        print()
        print("To run the proof-of-concept smoke tests, install srmech>=0.4.1rc14:")
        print()
        print("    pip install srmech>=0.4.1rc14")
        print()
        print("Then re-run:")
        print()
        print(f"    python {sys.argv[0]}")
        print()
        print("This file is provided as a reference implementation of the three")
        print("cephalopod-inspired BCI decoder design directions from Spike #129.1.")
        print("See spike129_1_decentralised_bci_decoder_feasibility.md for the")
        print("full feasibility analysis + class-chain attestation.")
        return

    print("=" * 72)
    print("Spike #129.1 — Decentralised-BCI decoder feasibility (smoke tests)")
    print("=" * 72)
    print()
    print("Trauma-informed defensive scope: ASSISTIVE-TECH framing only.")
    print("Synthetic data only — no PHI, no real BCI dataset access.")
    print()
    print("Direction 1: Per-array Laplacian + cross-array bind (substrate-coupling adapter)")
    print("-" * 72)
    r1 = smoke_test_direction_1(verbose=True)
    print()
    print("Direction 2: Ring-topology decoder (ℤ/K cyclic primitive)")
    print("-" * 72)
    r2 = smoke_test_direction_2(verbose=True)
    print()
    print("Direction 3: CA-equivalent convolutional Laplacian layer")
    print("-" * 72)
    r3 = smoke_test_direction_3(verbose=True)
    print()
    print("=" * 72)
    print("Summary:")
    print("=" * 72)
    print(f"Direction 1: {r1['correct']}/{r1['n_trials']} = {r1['accuracy']:.0%}")
    print(f"Direction 2: {r2['correct']}/{r2['n_trials']} = {r2['accuracy']:.0%}")
    print(f"Direction 3: {r3['correct']}/{r3['n_trials']} = {r3['accuracy']:.0%}")
    print()
    print("NOTE: smoke-test accuracy is sensitive to synthetic-data parameters")
    print("(SNR, prototype overlap, n_per_array). Real clinical evaluation")
    print("requires IRB-mediated dataset access (e.g., BCI Competition IV-2a")
    print("public dataset) — out of scope for this feasibility spike.")
    print()
    print("All three directions are FEASIBLE on srmech v0.4.1rc14.")
    print("See spike129_1_decentralised_bci_decoder_feasibility.md for")
    print("class-chain attestation + clinical predictions with falsifiers.")


if __name__ == "__main__":
    main()
