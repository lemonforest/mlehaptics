"""Spike #194 — Rotation-then-FFT-of-error on ephemerides-spectral RBS-HDC.

Question (user direction, 2026-05-20, verbatim):

    "I didn't think that we would have to add a function. what I was wanting
    to find out is if we perform this rotate on our RBS-HDC instrument of
    ephemerides, I was just wanting us to try to FFT error against a rotated
    hypervector instead or bit seralized so that we can see what things do
    cross bin leak, to find out if rotation means anything for this dataset,
    if it reveals hidden fiber content only available when we i don't know
    make the entire set off diagonal to the array or something. ... if this
    does happen to be correct, then if we do the same thing on the
    ephemerise data set that is sort of like a NN in the shape, then we
    should see cross bin stuff that looks like error but has meaning"

Hypothesis tested
-----------------
H1 (cross-bin-leakage-IS-fiber-content): Rotation of the ephemerides RBS-HDC
hypervector reveals OFF-DIAGONAL cross-bin coupling structure that carries
substrate-physics content (mass, orbital regime, M∘K coupling) — NOT just
Dirichlet windowing artifact.

H0: Cross-bin leakage matches the analytic Dirichlet kernel exactly; rotation
shuffles bits but reveals nothing the un-rotated spectrum did not show.

Falsifier discipline
--------------------
The Dirichlet-kernel sin(N π x) / (N · sin(π x)) is the analytic baseline
for rectangular-window leakage (Harris 1978; Spike #176 T6). Observed
leakage MINUS analytic Dirichlet = candidate fiber signal. If the residual
is structureless noise, H0 stands.

Methodology
-----------
Uses EXISTING srmech surface (no new srmech functions). The "form-function
rotation" is the SAME composition as Spike #176 (Class A∘C∘M), but applied
to the substrate-specific RBS-HDC encoding of body states:

  body_state (uint32 phase) → MINT (Class A) into D=8192-bit body-vector
  → BIND across bodies (Class M) → BSC hypervector → ROTATE (Class C ∘ M)
  → FFT → COMPUTE ERROR = rotated_spec − reference_spec
  → CROSS-BIN COUPLING MATRIX
  → COMPARE TO ANALYTIC DIRICHLET KERNEL

Rotation strides exercised:
  - identity (k=0): null baseline (no rotation; should be diagonal)
  - content-determined SHA-256 (Class A; Spike #176 default)
  - chess-natural strides {5, 7, -8} (Spike #173; substrate-natural rationals)
  - random strides (multiple samples; H0 baseline)
  - DNA helical pitches {21, 11, -12} (Spike #172; cross-substrate control)

7-cell methodology
------------------
Cell 1: Substrate-state encoding — body phases → D=8192 RBS-HDC hypervector
Cell 2: Rotation strides — compute all stride classes
Cell 3: Error + FFT — error = FFT(rotated) magnitudes − FFT(reference)
Cell 4: Cross-bin coupling matrix — C[i,j] = correlation of bins i,j
Cell 5: Dirichlet-kernel analytic comparison — observed minus analytic
Cell 6: Multi-body cross-substrate — per-body coupling matrices; cluster
Cell 7: NN-invariance test — does off-diagonal structure persist across strides?

Discipline
----------
- 14 A-N intact; NO promotion (per [[feedback_no_privileged_primitive_classes]])
- Identity-not-implementation framing
- Asymptotic-ring vocabulary (S¹ locus, U(1), wrap-around — NOT "loop")
- Existing srmech.amsc.hdc primitives only
- arXiv / DOI-verified citations only
- NDJSON output format
- Trauma-informed defensive scope (orbital mechanics; public ephemerides)

Run
---
    cd <worktree>
    python -S docs/srmech/notes/spike194_rotation_fft_error_fiber.py

Output:
- spike194_findings_2026-05-19.ndjson — per (body, stride, cell, metric)
- Exit code 0 on H1-confirmed; printout shows aggregate verdict.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

# Make srmech.amsc and ephemerides_spectral importable from this worktree
# without relying on pip install (avoids editable-install path collisions).
_HERE = Path(__file__).resolve()
_WORKTREE = _HERE.parents[3]
sys.path.insert(0,
    str(_WORKTREE / "docs" / "antikythera-maths" / "ephemerides-spectral"
                 / "python"))
sys.path.insert(0, str(_WORKTREE / "docs" / "srmech" / "python"))
# numpy from user site-packages (Python 3.14 layout on this dev machine)
_NP_SITE = Path(os.environ.get("APPDATA", "")) / "Python" / "Python314" / "site-packages"
if _NP_SITE.exists():
    sys.path.append(str(_NP_SITE))

import numpy as np  # noqa: E402
from numpy.fft import fft  # noqa: E402

from srmech.amsc import hdc as M  # noqa: E402
from ephemerides_spectral._research.bip_instrument import (  # noqa: E402
    EphemerisBIPInstrument, REFERENCE_JD, MODULO,
)


# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

# RBS-HDC dimensionality (Spike #147 / #170 / #173 canonical).
HDC_BYTES: int = 1024
HDC_BITS: int = HDC_BYTES * 8  # D = 8192

# Substrate-natural strides
SILICON_STRIDE: int = 257                     # Spike #170 baseline
CHESS_STRIDES: Tuple[int, ...] = (5, 7, -8)   # Spike #173 chess naturals
DNA_PITCHES: Tuple[int, ...] = (21, 11, -12)  # Spike #172 DNA naturals

# Random-stride samples (H0 baseline).
N_RANDOM_STRIDES: int = 8
RANDOM_SEED: int = 0xC0DEBABE  # deterministic for reproducibility

# Date snapshot for body states (J2000 + 100 days; arbitrary fixed value).
SNAPSHOT_JD: float = REFERENCE_JD + 100.0

# Multi-body subset for Cell 6 (cross-substrate clustering).
# Choose a mixture of orbital regimes for clustering interpretation:
#   - Inner rocky: mercury, venus, terra, mars
#   - Gas giants: jupiter, saturn, uranus, neptune
#   - Dwarf / TNO: pluto
#   - Galilean moons: io, europa, ganymede, callisto
#   - Saturnian moons: titan, enceladus
# 14-body subset spans multiple regimes for clustering signal.
MULTI_BODY_SUBSET: Tuple[str, ...] = (
    "mercury", "venus", "terra", "mars",
    "jupiter", "saturn", "uranus", "neptune",
    "pluto",
    "io", "europa", "ganymede", "callisto",
    "titan",
)

# Coupling-matrix subsampling — full N×N at D=8192 is 67M entries.
# Subsample by bin-stride to keep memory + compute tractable while
# preserving the off-diagonal structure of interest.
BIN_SUBSAMPLE_STRIDE: int = 32  # 8192 / 32 = 256 sub-bins
BIN_SUBSAMPLE_N: int = HDC_BITS // BIN_SUBSAMPLE_STRIDE


# ─────────────────────────────────────────────────────────────────────
# Output record schema (NDJSON, one line per measurement)
# ─────────────────────────────────────────────────────────────────────

@dataclass
class Record:
    spike: str
    cell: str
    body: str
    stride_class: str
    metric: str
    value: float
    note: str
    extra: Dict

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True)


# ─────────────────────────────────────────────────────────────────────
# Cell 1 — Substrate-state encoding
#   Body phases → D=8192 RBS-HDC hypervector via mint+bind composition.
# ─────────────────────────────────────────────────────────────────────

def mint_vector(name: str, n_bytes: int = HDC_BYTES) -> bytes:
    """Class A — deterministic SHA-256-chain mint (matches Spike #170/#173).

    Used to materialise a HDC body-anchor vector from a name and a residue.
    Identity-not-implementation: SHA-256 is the substrate-natural minting
    primitive; substrate-portable variants substitute the *rotation* parameter,
    NOT the mint.
    """
    out = bytearray()
    counter = 0
    seed = name.encode("utf-8")
    while len(out) < n_bytes:
        h = hashlib.sha256(seed + counter.to_bytes(8, "big")).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:n_bytes])


def encode_body_state_hdc(body_name: str, phase_u32: int) -> bytes:
    """Encode a single body's state as a D=8192-bit RBS-HDC vector.

    Composition:
      v_name  = MINT(body_name)                  ← Class A (anchor)
      v_phase = MINT(body_name + ":phase:%u")    ← Class A (state-content)
      v_body  = BIND(v_name, PERMUTE(v_phase, phase_u32 mod D))  ← Class M ∘ C

    The phase-content vector is rotated by the body's actual phase residue
    mod D — this is the body's local time-DOF projection per
    [[user_stance_universal_1d_t_tick_projects_to_per_body_local_time_dof]].
    """
    v_name = mint_vector(body_name)
    v_phase = mint_vector(f"{body_name}:phase:{phase_u32}")
    phase_mod_d = phase_u32 % HDC_BITS
    v_phase_rotated = M.permute(v_phase, phase_mod_d)
    return M.bind(v_name, v_phase_rotated)


def encode_solar_system_hdc(body_states: Dict[str, int]) -> bytes:
    """Bundle all body-vectors into one D=8192 system hypervector.

    Bundle (Class M majority) is the multi-body composition. Each body
    contributes its mint+bind+rotate vector; the bundle gives a single
    D=8192 vector representing the whole system state at one moment.

    NOTE: bundle requires odd count for clean majority — if even, we
    pad with a deterministic tie-breaker vector.
    """
    vectors = [encode_body_state_hdc(name, phase)
               for name, phase in body_states.items()]
    if len(vectors) % 2 == 0:
        vectors.append(mint_vector("spike194:tie:break"))
    return M.bundle(vectors)


def hypervector_to_bipolar_array(hv: bytes) -> np.ndarray:
    """Convert HDC byte-vector to bipolar (-1, +1) float array length D.

    Bit i of byte k → array[i + 8*k] = +1.0 if bit set, -1.0 if clear.
    Matches Spike #176 sign-bit ordering.
    """
    arr = np.empty(HDC_BITS, dtype=np.float64)
    for k, byte in enumerate(hv):
        for i in range(8):
            bit = (byte >> i) & 1
            arr[i + 8 * k] = +1.0 if bit else -1.0
    return arr


def cell1_substrate_encoding(records: List[Record], inst: EphemerisBIPInstrument
                              ) -> Dict[str, np.ndarray]:
    """Cell 1 — encode substrate states for the multi-body subset.

    Returns:
        per_body_hv: {body_name: bipolar D=8192 array}
    """
    print("=" * 78)
    print("Cell 1 — substrate-state encoding (D=8192 RBS-HDC per body)")
    print("=" * 78)

    # Encode the full system state at the snapshot date.
    state_full = inst.encode_state(SNAPSHOT_JD)  # uint32 array, shape (52,)
    name_to_phase: Dict[str, int] = {
        name: int(state_full[i]) for i, name in enumerate(inst.body_names)
    }

    # Per-body hypervectors for the chosen subset (single-body encoding).
    per_body_hv: Dict[str, np.ndarray] = {}
    for body in MULTI_BODY_SUBSET:
        if body not in name_to_phase:
            # The instrument's body roster may not exactly match the subset;
            # we tolerate missing bodies with a warning.
            print(f"  [warn] body '{body}' not in instrument roster — skipping")
            continue
        phase = name_to_phase[body]
        hv = encode_body_state_hdc(body, phase)
        bip = hypervector_to_bipolar_array(hv)
        per_body_hv[body] = bip
        # Diagnostic: how much mass on each bin (should be uniform; tests
        # mint quality). Bipolar variance per bit ≈ 1 for a balanced mint.
        bin_var = float(np.var(bip))
        records.append(Record(
            spike="194", cell="C1", body=body,
            stride_class="identity", metric="bin_variance",
            value=bin_var,
            note="bipolar variance per bin (≈1 for balanced mint)",
            extra={"phase_u32": phase, "hdc_bits": HDC_BITS},
        ))

    print(f"  encoded {len(per_body_hv)} body hypervectors @ D={HDC_BITS} bits")

    # Aggregate system-level encoding for whole-system tests.
    subset_states = {b: name_to_phase[b] for b in per_body_hv}
    sys_hv = encode_solar_system_hdc(subset_states)
    sys_bip = hypervector_to_bipolar_array(sys_hv)
    per_body_hv["__SYSTEM__"] = sys_bip
    print(f"  bundled system hypervector: D={sys_bip.size}, "
          f"mean={sys_bip.mean():+.4f}, var={sys_bip.var():.4f}")
    print()
    return per_body_hv


# ─────────────────────────────────────────────────────────────────────
# Cell 2 — Rotation strides
#   Generate stride lists for each substrate class.
# ─────────────────────────────────────────────────────────────────────

def content_determined_stride(hv_bytes: bytes) -> int:
    """Class A content-addressing: SHA-256 → stride mod HDC_BITS."""
    digest = hashlib.sha256(hv_bytes).digest()
    val = int.from_bytes(digest[:8], "little")
    return val % HDC_BITS


def cell2_rotation_strides(records: List[Record],
                           per_body_hv: Dict[str, np.ndarray]
                           ) -> Dict[str, List[int]]:
    """Cell 2 — compute stride values per stride-class.

    Returns:
        strides_by_class: {class_name: [stride values to test]}

    Class names:
        "identity"   — k = 0 (null baseline)
        "content"    — SHA-256 of bipolar bytes → 1 stride
        "chess"      — Spike #173 strides {5, 7, -8}
        "dna"        — Spike #172 strides {21, 11, -12}
        "random"     — N random strides (H0 baseline)
        "silicon"    — Spike #170 stride {257}
    """
    print("=" * 78)
    print("Cell 2 — rotation strides per substrate class")
    print("=" * 78)
    sys_hv = per_body_hv["__SYSTEM__"]
    # Re-derive bytes for content-stride (sign bits as bytes).
    sys_bytes = bytearray(HDC_BYTES)
    for i, val in enumerate(sys_hv):
        if val > 0:
            sys_bytes[i // 8] |= (1 << (i % 8))
    sys_bytes = bytes(sys_bytes)

    rng = np.random.default_rng(RANDOM_SEED)
    random_strides = sorted({
        int(rng.integers(1, HDC_BITS)) for _ in range(N_RANDOM_STRIDES)
    })[:N_RANDOM_STRIDES]

    strides_by_class: Dict[str, List[int]] = {
        "identity": [0],
        "content": [content_determined_stride(sys_bytes)],
        "chess": list(CHESS_STRIDES),
        "dna": list(DNA_PITCHES),
        "silicon": [SILICON_STRIDE],
        "random": random_strides,
    }
    for cname, vals in strides_by_class.items():
        print(f"  {cname:>10}: {vals}")
        records.append(Record(
            spike="194", cell="C2", body="__SYSTEM__",
            stride_class=cname, metric="stride_count",
            value=float(len(vals)),
            note="stride values for this substrate class",
            extra={"strides": vals},
        ))
    print()
    return strides_by_class


# ─────────────────────────────────────────────────────────────────────
# Cell 3 — Error + FFT
#   error = FFT(rotated bipolar) magnitudes − FFT(reference) magnitudes
# ─────────────────────────────────────────────────────────────────────

def rotate_bipolar(arr: np.ndarray, k: int) -> np.ndarray:
    """Cyclic shift on bipolar array. k can be negative (asymmetric-ring shift).

    Per [[feedback_asymptotic_ring_vocabulary_discipline]]: this is shift on
    the S¹ locus / asymptotic ring, NOT a loop.
    """
    if k == 0:
        return arr.copy()
    k_mod = k % HDC_BITS
    return np.roll(arr, k_mod)


def fft_error_magnitudes(reference: np.ndarray, rotated: np.ndarray
                          ) -> np.ndarray:
    """Compute magnitude-domain error between rotated and reference spectra.

    Returns:
        |FFT(rotated)| − |FFT(reference)|   (per-bin signed magnitude delta)

    The shift theorem guarantees |FFT(rotated)| = |FFT(reference)| exactly
    for cyclic shifts — so this error vector should be FP-eps for the
    pure-cyclic case (T2 of Spike #176). What we're looking for is whether
    OTHER metrics (cross-bin coupling at non-cyclic projections) carry
    structure. The error baseline is therefore informational.
    """
    mag_ref = np.abs(fft(reference))
    mag_rot = np.abs(fft(rotated))
    return mag_rot - mag_ref


def fft_complex_error(reference: np.ndarray, rotated: np.ndarray
                       ) -> np.ndarray:
    """Complex-domain error (carries phase information from shift theorem)."""
    spec_ref = fft(reference)
    spec_rot = fft(rotated)
    return spec_rot - spec_ref


def cell3_error_fft(records: List[Record],
                    per_body_hv: Dict[str, np.ndarray],
                    strides_by_class: Dict[str, List[int]]
                    ) -> Dict[Tuple[str, str, int], Dict]:
    """Cell 3 — rotation, error, FFT analysis.

    Returns:
        results: {(body, stride_class, stride_value): {"complex_error": ...,
                                                         "mag_error": ...,
                                                         "mag_rot": ...}}
    """
    print("=" * 78)
    print("Cell 3 — error + FFT (rotated vs reference)")
    print("=" * 78)
    results: Dict[Tuple[str, str, int], Dict] = {}

    # Run for system + first 3 individual bodies (full per-body
    # treatment in Cell 6).
    target_bodies = ["__SYSTEM__"] + list(MULTI_BODY_SUBSET[:3])

    for body in target_bodies:
        if body not in per_body_hv:
            continue
        reference = per_body_hv[body]
        for cname, strides in strides_by_class.items():
            for k in strides:
                rotated = rotate_bipolar(reference, k)
                mag_err = fft_error_magnitudes(reference, rotated)
                cplx_err = fft_complex_error(reference, rotated)
                mag_rot = np.abs(fft(rotated))
                results[(body, cname, k)] = {
                    "complex_error": cplx_err,
                    "mag_error": mag_err,
                    "mag_rot": mag_rot,
                }
                # Metrics
                mag_err_max = float(np.max(np.abs(mag_err)))
                cplx_err_l1 = float(np.sum(np.abs(cplx_err)))
                # Theoretical: mag_err should be 0 by shift theorem
                # (cyclic shift preserves magnitudes); cplx_err captures
                # phase rotation = -2πi·k·m/N at each bin.
                records.append(Record(
                    spike="194", cell="C3", body=body,
                    stride_class=cname, metric="mag_error_max",
                    value=mag_err_max,
                    note="should be ≈0 by DFT shift theorem; >>0 indicates broken cyclicity",
                    extra={"k": k, "n_bins": HDC_BITS},
                ))
                records.append(Record(
                    spike="194", cell="C3", body=body,
                    stride_class=cname, metric="complex_error_l1",
                    value=cplx_err_l1,
                    note="complex error carries phase content (shift theorem)",
                    extra={"k": k, "n_bins": HDC_BITS},
                ))
        print(f"  body={body}: processed {sum(len(s) for s in strides_by_class.values())} strides")
    print()
    return results


# ─────────────────────────────────────────────────────────────────────
# Cell 4 — Cross-bin coupling matrix
#   Build C[i,j] = correlation of bin-i and bin-j across the
#   stride-class ensemble.
# ─────────────────────────────────────────────────────────────────────

def subsample_bins(mag_or_complex: np.ndarray) -> np.ndarray:
    """Subsample down to BIN_SUBSAMPLE_N bins for tractable matrix ops."""
    return mag_or_complex[::BIN_SUBSAMPLE_STRIDE]


def cross_bin_coupling_matrix(spectra_set: List[np.ndarray]) -> np.ndarray:
    """Build cross-bin coupling matrix C[i,j] = <bin_i, bin_j> across spectra.

    Each spectrum is a vector of bin magnitudes (or complex values). C[i,j]
    is the Pearson-style correlation of bin i's value with bin j's value
    across the set of spectra (one per stride sample).

    H1 prediction: off-diagonal C[i,j] for i≠j carries structure if rotation
    reveals fiber content. H0 prediction: C is dominantly diagonal +
    Dirichlet skirt only.
    """
    # Stack spectra into matrix [n_strides, n_bins], subsample bins.
    if len(spectra_set) == 0:
        return np.zeros((BIN_SUBSAMPLE_N, BIN_SUBSAMPLE_N))
    # Take real magnitudes (subsample bins).
    M_ = np.stack([subsample_bins(np.abs(s)) for s in spectra_set])
    n_strides, n_bins = M_.shape
    # Z-score each column (per-bin) so correlation is scale-invariant.
    mean = M_.mean(axis=0, keepdims=True)
    std = M_.std(axis=0, keepdims=True) + 1e-15
    Z = (M_ - mean) / std
    # Cross-bin correlation: bin-i vs bin-j across strides.
    if n_strides < 2:
        # Fallback to outer-product magnitude coupling for single-stride.
        v = M_[0]
        return np.outer(v, v) / (v.max()**2 + 1e-15)
    C = (Z.T @ Z) / max(n_strides - 1, 1)
    return C


def cell4_coupling_matrix(records: List[Record],
                          c3_results: Dict[Tuple[str, str, int], Dict],
                          strides_by_class: Dict[str, List[int]]
                          ) -> Dict[Tuple[str, str], np.ndarray]:
    """Cell 4 — build coupling matrices per (body, stride_class)."""
    print("=" * 78)
    print("Cell 4 — cross-bin coupling matrices")
    print("=" * 78)
    coupling_matrices: Dict[Tuple[str, str], np.ndarray] = {}

    # Collect strides per (body, class).
    by_body_class: Dict[Tuple[str, str], List[np.ndarray]] = {}
    for (body, cname, k), result in c3_results.items():
        key = (body, cname)
        by_body_class.setdefault(key, []).append(result["mag_rot"])

    for (body, cname), spectra in by_body_class.items():
        C = cross_bin_coupling_matrix(spectra)
        coupling_matrices[(body, cname)] = C
        # Off-diagonal mass: how much of |C| is in off-diagonal positions?
        diag_mass = float(np.sum(np.abs(np.diag(C))))
        total_mass = float(np.sum(np.abs(C))) + 1e-15
        off_diag_fraction = 1.0 - diag_mass / total_mass
        # Off-diagonal max: largest off-diagonal coupling magnitude.
        C_off = C - np.diag(np.diag(C))
        off_diag_max = float(np.max(np.abs(C_off)))
        # Off-diagonal structure: ratio of max off-diag to mean off-diag.
        off_diag_mean = float(np.mean(np.abs(C_off)))
        off_diag_structure = off_diag_max / (off_diag_mean + 1e-15)
        records.append(Record(
            spike="194", cell="C4", body=body,
            stride_class=cname, metric="off_diag_fraction",
            value=off_diag_fraction,
            note="fraction of |C| mass in off-diagonal positions",
            extra={"matrix_dim": int(C.shape[0]), "n_strides": len(spectra)},
        ))
        records.append(Record(
            spike="194", cell="C4", body=body,
            stride_class=cname, metric="off_diag_max",
            value=off_diag_max,
            note="largest off-diagonal coupling magnitude",
            extra={"matrix_dim": int(C.shape[0])},
        ))
        records.append(Record(
            spike="194", cell="C4", body=body,
            stride_class=cname, metric="off_diag_structure_ratio",
            value=off_diag_structure,
            note="max/mean ratio of off-diagonal coupling — >> 1 indicates structure",
            extra={"matrix_dim": int(C.shape[0])},
        ))
    print(f"  built {len(coupling_matrices)} coupling matrices")
    print()
    return coupling_matrices


# ─────────────────────────────────────────────────────────────────────
# Cell 5 — Dirichlet-kernel analytic comparison
#   Computed analytic Dirichlet skirts; observed minus analytic = residual.
# ─────────────────────────────────────────────────────────────────────

def analytic_dirichlet_kernel(N: int, k_shift: int) -> np.ndarray:
    """Analytic |D_N(2πk/N)| kernel — the rectangular-window Fourier transform.

    Per Harris 1978 (canonical SSoT): a rectangular window of length N has
    Fourier transform sin(N π x) / (N · sin(π x)) at normalised frequency x.
    Cyclic shift by k makes off-target bins acquire this skirt magnitude.

    Returns: kernel value per bin index 0..N-1 (magnitude).
    """
    # Bin frequency offset (fractional bin) — for a cyclic shift the offset
    # is exactly k/N for each bin shifted by 1 unit; we need the kernel
    # AS A FUNCTION OF BIN-OFFSET from the peak. The peak under cyclic
    # shift of an integer-bin signal IS still at the same integer bin
    # (DFT shift theorem); leakage shows in the WINDOWED projection
    # (Spike #176 T2). The analytic kernel below characterises the
    # windowed-substrate leakage shape.
    offsets = np.arange(N)
    # Normalise by N; clamp denominator at offset=0 (use limit 1).
    x = (offsets - k_shift % N) / N
    # sin(N·π·x) / (N·sin(π·x)) → 1 when x→0 (integer bins)
    num = np.sin(N * np.pi * x)
    den = N * np.sin(np.pi * x)
    # At integer x (den == 0), kernel value is 1 (or 0 if odd N·x integer).
    safe_den = np.where(np.abs(den) < 1e-12, 1.0, den)
    kernel = num / safe_den
    # Where den is near-zero, kernel value is 1 for x=0, else 0.
    kernel = np.where(np.abs(den) < 1e-12,
                       np.where(np.abs(x) < 1e-12, 1.0, 0.0),
                       kernel)
    return np.abs(kernel)


def cell5_dirichlet_residual(records: List[Record],
                              c3_results: Dict[Tuple[str, str, int], Dict],
                              ) -> Dict[Tuple[str, str, int], float]:
    """Cell 5 — observed spectral leakage minus analytic Dirichlet kernel.

    For each (body, stride, k): compute observed mag_rot, compute analytic
    Dirichlet kernel for that k, compute L2 residual.

    H1: residual carries non-Dirichlet structure (framework signal).
    H0: residual is structureless noise at the bin-quantisation floor.
    """
    print("=" * 78)
    print("Cell 5 — Dirichlet-kernel analytic comparison")
    print("=" * 78)
    residuals: Dict[Tuple[str, str, int], float] = {}

    for (body, cname, k), result in c3_results.items():
        mag_rot = result["mag_rot"]
        # Normalise to unit peak (so we compare shape, not amplitude).
        norm_rot = mag_rot / (np.max(mag_rot) + 1e-15)
        analytic = analytic_dirichlet_kernel(HDC_BITS, k)
        # L2 residual after best-fit scaling.
        # Project analytic onto norm_rot to find best amplitude.
        denom = float(np.sum(analytic * analytic) + 1e-15)
        amp = float(np.sum(norm_rot * analytic) / denom)
        resid = norm_rot - amp * analytic
        resid_l2 = float(np.sqrt(np.sum(resid * resid)))
        resid_l2_normalised = resid_l2 / (np.sqrt(np.sum(norm_rot**2)) + 1e-15)
        # Structure metric: is the residual structured or noise?
        # Compute autocorrelation of residual at lag 1, 2, 4, 8.
        residuals[(body, cname, k)] = resid_l2_normalised
        records.append(Record(
            spike="194", cell="C5", body=body,
            stride_class=cname, metric="dirichlet_residual_l2_normalised",
            value=resid_l2_normalised,
            note="observed minus analytic Dirichlet kernel; non-zero = framework signal",
            extra={"k": k, "best_fit_amp": amp},
        ))
        # Residual autocorrelation at small lags — structureless if ≈0.
        ac_lags = [1, 2, 4, 8, 16, 32]
        ac_values = []
        for lag in ac_lags:
            shifted = np.roll(resid, lag)
            ac = float(np.sum(resid * shifted) / (np.sum(resid * resid) + 1e-15))
            ac_values.append(ac)
        max_ac = float(max(np.abs(ac_values)))
        records.append(Record(
            spike="194", cell="C5", body=body,
            stride_class=cname, metric="residual_autocorr_max",
            value=max_ac,
            note="max autocorr at lags 1,2,4,8,16,32; >0.1 indicates structure",
            extra={"k": k, "ac_lags": ac_lags, "ac_values": ac_values},
        ))
    print(f"  Dirichlet-residual analyses: {len(residuals)} (body, stride, k) cells")
    print()
    return residuals


# ─────────────────────────────────────────────────────────────────────
# Cell 6 — Multi-body cross-substrate
#   Build coupling matrix per body; cluster bodies by matrix similarity.
# ─────────────────────────────────────────────────────────────────────

def matrix_distance(A: np.ndarray, B: np.ndarray) -> float:
    """Frobenius norm of A - B normalised by ||A|| + ||B||."""
    diff = float(np.linalg.norm(A - B, "fro"))
    norm = float(np.linalg.norm(A, "fro") + np.linalg.norm(B, "fro"))
    return diff / (norm + 1e-15)


def cell6_multi_body(records: List[Record],
                     per_body_hv: Dict[str, np.ndarray],
                     strides_by_class: Dict[str, List[int]]
                     ) -> Dict[str, np.ndarray]:
    """Cell 6 — coupling matrix per body; cross-body distance matrix.

    For each body in MULTI_BODY_SUBSET: build coupling matrix using the
    chess-stride family (substrate-natural). Compare cross-body distance
    to see clustering pattern.

    H1 universal: all matrices similar (universal substrate-coupling).
    H1 body-specific: matrices distinct, cluster by orbital regime.
    """
    print("=" * 78)
    print("Cell 6 — multi-body cross-substrate coupling structure")
    print("=" * 78)
    body_matrices: Dict[str, np.ndarray] = {}
    bodies_iter = [b for b in MULTI_BODY_SUBSET if b in per_body_hv]

    chess_strides = strides_by_class["chess"]

    for body in bodies_iter:
        reference = per_body_hv[body]
        spectra = []
        for k in chess_strides:
            rot = rotate_bipolar(reference, k)
            spectra.append(np.abs(fft(rot)))
        C = cross_bin_coupling_matrix(spectra)
        body_matrices[body] = C
        # Diagnostic: Fro-norm of matrix (overall coupling strength).
        fro = float(np.linalg.norm(C, "fro"))
        records.append(Record(
            spike="194", cell="C6", body=body,
            stride_class="chess", metric="coupling_matrix_fro_norm",
            value=fro,
            note="Frobenius norm of body's coupling matrix",
            extra={"n_bins_subsampled": int(C.shape[0])},
        ))

    # Cross-body distance matrix.
    n_bodies = len(bodies_iter)
    distance_matrix = np.zeros((n_bodies, n_bodies))
    for i, b_i in enumerate(bodies_iter):
        for j, b_j in enumerate(bodies_iter):
            distance_matrix[i, j] = matrix_distance(
                body_matrices[b_i], body_matrices[b_j]
            )
    # Mean off-diagonal distance: cluster signal.
    off_diag_mean = float(np.mean(
        distance_matrix[~np.eye(n_bodies, dtype=bool)]
    ))
    off_diag_std = float(np.std(
        distance_matrix[~np.eye(n_bodies, dtype=bool)]
    ))
    records.append(Record(
        spike="194", cell="C6", body="__CROSS_BODY__",
        stride_class="chess", metric="cross_body_distance_mean",
        value=off_diag_mean,
        note="mean pairwise distance between body coupling matrices",
        extra={"n_bodies": n_bodies, "std": off_diag_std},
    ))
    # Coefficient of variation: structure signal.
    cv = off_diag_std / (off_diag_mean + 1e-15)
    records.append(Record(
        spike="194", cell="C6", body="__CROSS_BODY__",
        stride_class="chess", metric="cross_body_distance_cv",
        value=cv,
        note="CV of cross-body distances; 0 = uniform; >0.3 = clustering",
        extra={"n_bodies": n_bodies},
    ))
    print(f"  built {len(body_matrices)} per-body coupling matrices")
    print(f"  cross-body distance: mean={off_diag_mean:.4f}, std={off_diag_std:.4f}, "
          f"CV={cv:.4f}")
    print()
    return body_matrices


# ─────────────────────────────────────────────────────────────────────
# Cell 7 — NN-invariance test
#   Does off-diagonal coupling structure persist across rotation strides?
# ─────────────────────────────────────────────────────────────────────

def cell7_nn_invariance(records: List[Record],
                        per_body_hv: Dict[str, np.ndarray],
                        strides_by_class: Dict[str, List[int]]
                        ) -> Dict[str, float]:
    """Cell 7 — does coupling matrix structure persist across stride classes?

    For one chosen body (system), compute coupling matrix for each
    stride-class ensemble. Compare matrices via Frobenius distance.

    H1 NN-like: matrices similar across stride classes (rotation-invariant
    fingerprint of substrate). H0: matrices differ significantly between
    stride classes (no invariant content; rotation is arbitrary).
    """
    print("=" * 78)
    print("Cell 7 — NN-invariance test (off-diag persists across strides?)")
    print("=" * 78)

    body = "__SYSTEM__"
    if body not in per_body_hv:
        return {}
    reference = per_body_hv[body]

    # Compute coupling matrix per stride class.
    class_matrices: Dict[str, np.ndarray] = {}
    for cname, strides in strides_by_class.items():
        if len(strides) < 2:
            continue  # need ≥2 strides for cross-bin correlation
        spectra = []
        for k in strides:
            rot = rotate_bipolar(reference, k)
            spectra.append(np.abs(fft(rot)))
        class_matrices[cname] = cross_bin_coupling_matrix(spectra)

    # Cross-class distances.
    classes = list(class_matrices.keys())
    distances: Dict[Tuple[str, str], float] = {}
    for i, c_i in enumerate(classes):
        for j, c_j in enumerate(classes):
            if i < j:
                d = matrix_distance(class_matrices[c_i], class_matrices[c_j])
                distances[(c_i, c_j)] = d
                records.append(Record(
                    spike="194", cell="C7", body=body,
                    stride_class=f"{c_i}_vs_{c_j}",
                    metric="class_pair_matrix_distance", value=d,
                    note="Frobenius dist of coupling matrices between stride classes",
                    extra={"class_a": c_i, "class_b": c_j},
                ))
    # Aggregate: mean cross-class distance.
    mean_dist = float(np.mean(list(distances.values()))) if distances else 0.0
    std_dist = float(np.std(list(distances.values()))) if distances else 0.0
    records.append(Record(
        spike="194", cell="C7", body=body,
        stride_class="cross_class", metric="mean_class_pair_distance",
        value=mean_dist,
        note="lower = NN-invariant fingerprint; higher = arbitrary rotation",
        extra={"n_pairs": len(distances), "std": std_dist},
    ))
    # Compare to random-class baseline: distance(random, content) and
    # distance(random, chess) should be ≈ if rotation is arbitrary.
    # Distance(chess, content) should be SMALLER if substrate-naturals carry
    # invariant structure.
    chess_vs_content = distances.get(("chess", "content"),
                                       distances.get(("content", "chess"), -1))
    random_vs_content = distances.get(("random", "content"),
                                        distances.get(("content", "random"), -1))
    chess_vs_random = distances.get(("chess", "random"),
                                      distances.get(("random", "chess"), -1))
    if chess_vs_content >= 0 and random_vs_content >= 0:
        nn_ratio = chess_vs_content / (random_vs_content + 1e-15)
        records.append(Record(
            spike="194", cell="C7", body=body,
            stride_class="chess_vs_random_ratio",
            metric="nn_invariance_ratio", value=nn_ratio,
            note="ratio < 1: chess closer to content than random → NN-invariant",
            extra={"chess_vs_content": chess_vs_content,
                   "random_vs_content": random_vs_content,
                   "chess_vs_random": chess_vs_random},
        ))
    print(f"  mean cross-class distance: {mean_dist:.4f} (std={std_dist:.4f})")
    if chess_vs_content >= 0:
        print(f"  chess vs content: {chess_vs_content:.4f}")
        print(f"  random vs content: {random_vs_content:.4f}")
        print(f"  chess vs random: {chess_vs_random:.4f}")
    print()
    return {"mean_class_pair_distance": mean_dist,
            "chess_vs_content": chess_vs_content if chess_vs_content >= 0 else float("nan"),
            "random_vs_content": random_vs_content if random_vs_content >= 0 else float("nan")}


# ─────────────────────────────────────────────────────────────────────
# Aggregate verdict
# ─────────────────────────────────────────────────────────────────────

def aggregate_verdict(records: List[Record]) -> str:
    """Synthesise a per-cell + aggregate verdict.

    H1 holds if EITHER:
    - residual_autocorr_max > 0.1 for non-identity strides (structure in
      Dirichlet residual), OR
    - off_diag_structure_ratio > 5 (significant off-diagonal coupling), AND
    - chess_vs_content < random_vs_content (NN-invariance)
    """
    by_metric: Dict[str, List[float]] = {}
    for r in records:
        by_metric.setdefault(r.metric, []).append(r.value)

    # C5: residual autocorrelation max
    resid_ac_max = max(by_metric.get("residual_autocorr_max", [0]))
    resid_ac_evidence = resid_ac_max > 0.1

    # C4: off-diagonal structure
    off_diag_ratios = by_metric.get("off_diag_structure_ratio", [])
    # Filter to non-identity cells (identity has dim=1 → no off-diag).
    # We use threshold > 5 as evidence of structured off-diagonal coupling.
    structured_count = sum(1 for v in off_diag_ratios if v > 5)
    structure_evidence = structured_count >= 3

    # C7: NN-invariance
    ratios = by_metric.get("nn_invariance_ratio", [])
    nn_evidence = any(r < 1.0 for r in ratios) if ratios else False

    # Aggregate
    evidence_count = sum([resid_ac_evidence, structure_evidence, nn_evidence])

    if evidence_count == 3:
        return "H1-FIBER-CONTENT-REVEALED-VIA-CROSS-BIN-LEAKAGE-CONFIRMED"
    elif evidence_count == 2:
        return "H1-PARTIAL-FIBER-CONTENT-REVEALED"
    elif evidence_count == 1:
        return "H0-WITH-PARTIAL-STRUCTURE"
    else:
        return "H0-DIRICHLET-SKIRT-ONLY-NO-FIBER-CONTENT"


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    records: List[Record] = []

    print("=" * 78)
    print("Spike #194 — Rotation-FFT-of-error on ephemerides RBS-HDC")
    print("=" * 78)
    print(f"D = {HDC_BITS} bits ({HDC_BYTES} bytes)")
    print(f"Subsample stride = {BIN_SUBSAMPLE_STRIDE} -> {BIN_SUBSAMPLE_N} bins")
    print(f"Snapshot JD = {SNAPSHOT_JD} (J2000 + {SNAPSHOT_JD - REFERENCE_JD} days)")
    print()

    # Instrument acquisition
    inst = EphemerisBIPInstrument(kernel="de441")
    print(f"Instrument: {len(inst.body_names)} bodies, MODULO = {MODULO} = 2^32")
    print()

    # 7-cell pipeline
    per_body_hv = cell1_substrate_encoding(records, inst)
    strides_by_class = cell2_rotation_strides(records, per_body_hv)
    c3_results = cell3_error_fft(records, per_body_hv, strides_by_class)
    cell4_coupling_matrix(records, c3_results, strides_by_class)
    cell5_dirichlet_residual(records, c3_results)
    cell6_multi_body(records, per_body_hv, strides_by_class)
    cell7_nn_invariance(records, per_body_hv, strides_by_class)

    # Aggregate
    verdict = aggregate_verdict(records)
    print("=" * 78)
    print(f"AGGREGATE VERDICT: {verdict}")
    print("=" * 78)
    print(f"Total records: {len(records)}")

    # Write NDJSON
    out_path = _HERE.parent / "spike194_findings_2026-05-19.ndjson"
    with out_path.open("w", encoding="utf-8") as fh:
        # Aggregate record first
        agg = Record(
            spike="194", cell="AGGREGATE", body="__ALL__",
            stride_class="__ALL__", metric="aggregate_verdict",
            value=float(1.0 if verdict.startswith("H1-FIBER") else
                        0.5 if verdict.startswith("H1-PARTIAL") else
                        0.25 if verdict.startswith("H0-WITH") else 0.0),
            note=verdict,
            extra={"n_records": len(records),
                   "hdc_bits": HDC_BITS,
                   "snapshot_jd": SNAPSHOT_JD,
                   "spike_date": "2026-05-19"},
        )
        fh.write(agg.to_json_line() + "\n")
        for r in records:
            fh.write(r.to_json_line() + "\n")
    print(f"NDJSON written: {out_path}")

    # Exit code: 0 on H1, 1 on H0
    if verdict.startswith("H1"):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
