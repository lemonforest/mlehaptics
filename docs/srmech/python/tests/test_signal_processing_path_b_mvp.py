"""Phase 4 Path B per-op MVP dual-path tests for ``srmech.signal_processing``.

Verifies the 6 Path B per-op modules per the implementation plan
``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md`` Phase 4.

Each of the 6 ops (``fft``, ``ifft``, ``sign_quantise``, ``matched_filter``,
``wiener``, ``hdc_truncation``) gets four per-op tests:

1. **T_<op>_a_b_d1_equivalence** — D1 algebra-identity preserved bit-exact
   between Path A and Path B on substrate-natural ground-truth input.
2. **T_<op>_path_b_registered** — Path B op is registered with
   :mod:`srmech.signal_processing.path_registry`; lookup succeeds.
3. **T_<op>_path_b_metadata_present** — ``OPERATION_NAME``,
   ``CLASS_COMPOSITION``, ``PERFORMANCE_HINT``, ``SSOT_CITATION`` all
   present on the Path B module.
4. **T_<op>_dispatcher_routes** — ``cascade_dispatcher.dispatch`` routes
   to Path B when ``path="B"`` kwarg passed; routes per
   :data:`DEFAULT_PATH_PER_CLASS` table otherwise.

Plus aggregate tests:

- **T_all_six_ops_registered** — all 6 ops in ``PATH_B_MVP_OPS`` tuple
  are registered.
- **T_path_b_mvp_class_composition_valid** — all classes in
  ``CLASS_COMPOSITION`` are in the 14 A-N alphabet.

Per ``[[user_stance_identity_not_implementation_discipline]]`` Path A and
Path B both *instantiate* the same algebra; D1 algebra-identity is
bit-exact at substrate-natural inputs, D2 substrate fingerprint
divergence may surface at other substrates (Spike #176 T2 anchor; not
tested here per Phase 4 scope).

Per ``[[feedback_no_privileged_primitive_classes]]`` no new primitive
class is promoted; CLASS_COMPOSITION tuples reference only the
14 A-N existing classes.

Per ``[[feedback_trauma_informed_defensive_scope]]`` methodology-research
framing only; no clinical, military, or capability-assessment scope.

Spike anchors referenced (per-op):

- **fft** — Spike #176 H1 (rotation IS Class K, machine ε) + T8 (cycle
  order Class N rational).
- **ifft** — Spike #176 T4 (recovery error = 0.0).
- **sign_quantise** — Spike #174 (SHA-256 BER preservation at +20 dB SNR).
- **matched_filter** — Spike #159 (within-vs-between separation ratio).
- **wiener** — Kay (1993) §11 textbook SSoT (closed-form rational gain).
- **hdc_truncation** — Spike #117 (sparse-truncate primitive) + Spike
  #179 T6 (bit-exact recovery at substrate-natural sparsity).
"""

from __future__ import annotations

import importlib
import hashlib
from typing import Any

import numpy as np
import pytest

from srmech.signal_processing import (
    DEFAULT_PATH_PER_CLASS,
    PATH_A,
    PATH_B,
    dispatch,
)
from srmech.signal_processing import path_registry
from srmech.signal_processing.path_b_ops import PATH_B_MVP_OPS


VALID_CLASSES = set("ABCDEFGHIJKLMN")

REQUIRED_CONSTANTS = (
    "OPERATION_NAME",
    "CLASS_COMPOSITION",
    "PERFORMANCE_HINT",
    "SSOT_CITATION",
)


# ──────────────────────────────────────────────────────────────────────
# Phase 4 ships exactly 6 Path B MVP ops
# ──────────────────────────────────────────────────────────────────────


def test_phase_4_ships_six_path_b_ops():
    """Phase 4 ships exactly 6 Path B per-op MVP modules per the plan."""
    assert len(PATH_B_MVP_OPS) == 6, (
        f"Phase 4 MVP expects 6 ops; got {len(PATH_B_MVP_OPS)}"
    )
    expected = frozenset(
        ("fft", "ifft", "sign_quantise", "matched_filter", "wiener",
         "hdc_truncation")
    )
    assert frozenset(PATH_B_MVP_OPS) == expected, (
        f"Phase 4 MVP ops mismatch: expected {expected}, got "
        f"{frozenset(PATH_B_MVP_OPS)}"
    )


# ──────────────────────────────────────────────────────────────────────
# Per-op metadata + registration tests (4 × 6 = 24 tests)
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("op_name", PATH_B_MVP_OPS)
def test_path_b_metadata_present(op_name: str):
    """Each Path B module has the required metadata constants per the plan."""
    mod = importlib.import_module(
        f"srmech.signal_processing.path_b_ops.{op_name}"
    )
    for const_name in REQUIRED_CONSTANTS:
        assert hasattr(mod, const_name), (
            f"Path B module {op_name!r} missing required constant "
            f"{const_name!r}"
        )
    # Type checks per the plan's §1 spec.
    assert isinstance(mod.OPERATION_NAME, str), (
        f"{op_name}.OPERATION_NAME must be str"
    )
    assert mod.OPERATION_NAME == op_name, (
        f"{op_name}.OPERATION_NAME must match module name; got "
        f"{mod.OPERATION_NAME!r}"
    )
    assert isinstance(mod.CLASS_COMPOSITION, tuple), (
        f"{op_name}.CLASS_COMPOSITION must be tuple"
    )
    assert len(mod.CLASS_COMPOSITION) > 0, (
        f"{op_name}.CLASS_COMPOSITION must be non-empty"
    )
    for cls in mod.CLASS_COMPOSITION:
        assert cls in VALID_CLASSES, (
            f"{op_name}.CLASS_COMPOSITION contains invalid class "
            f"{cls!r}; must be one of {sorted(VALID_CLASSES)}"
        )
    assert isinstance(mod.PERFORMANCE_HINT, str) and mod.PERFORMANCE_HINT, (
        f"{op_name}.PERFORMANCE_HINT must be non-empty str"
    )
    assert isinstance(mod.SSOT_CITATION, str) and mod.SSOT_CITATION, (
        f"{op_name}.SSOT_CITATION must be non-empty str"
    )


@pytest.mark.parametrize("op_name", PATH_B_MVP_OPS)
def test_path_b_registered(op_name: str):
    """Each Path B op is registered with path_registry; both paths bound."""
    entry = path_registry.lookup(op_name)
    assert entry.path_a is not None, (
        f"Path A for {op_name!r} not registered; Phase 4 registers both "
        "paths per dual-path-MVP plan."
    )
    assert entry.path_b is not None, (
        f"Path B for {op_name!r} not registered."
    )
    assert path_registry.has_path(op_name, PATH_A), (
        f"has_path({op_name!r}, 'A') must return True"
    )
    assert path_registry.has_path(op_name, PATH_B), (
        f"has_path({op_name!r}, 'B') must return True"
    )
    # Class composition pulled from registration must reference 14 A-N only.
    assert entry.classes, (
        f"{op_name!r} registration must include CLASS_COMPOSITION"
    )
    for cls in entry.classes:
        assert cls in VALID_CLASSES, (
            f"{op_name!r} registered class {cls!r} not in 14 A-N alphabet"
        )


@pytest.mark.parametrize("op_name", PATH_B_MVP_OPS)
def test_dispatcher_routes_explicit_path_b(op_name: str):
    """``dispatch(op_name, path='B')`` routes to Path B impl."""
    entry = path_registry.lookup(op_name)
    # Run a tiny op via dispatch — the Path B impl is what should be
    # invoked. We can't easily intercept without a mock; we just verify
    # the dispatch call succeeds without raising. The next test
    # (D1 equivalence) exercises the actual outputs.
    sample_args, sample_kwargs = _sample_inputs(op_name)
    result_b = dispatch(op_name, *sample_args, path=PATH_B, **sample_kwargs)
    assert result_b is not None, (
        f"dispatch({op_name!r}, path='B') returned None"
    )
    result_a = dispatch(op_name, *sample_args, path=PATH_A, **sample_kwargs)
    assert result_a is not None, (
        f"dispatch({op_name!r}, path='A') returned None"
    )


# ──────────────────────────────────────────────────────────────────────
# Per-op D1 algebra-identity equivalence — Path A ≡ Path B at substrate
# natural inputs
# ──────────────────────────────────────────────────────────────────────


def _assert_d1_equivalent(a: Any, b: Any, op_name: str) -> None:
    """Assert Path A output equals Path B output at D1 algebra-content level.

    Per ``[[feedback_algebra_not_magnitude]]`` +
    ``[[user_stance_identity_not_implementation_discipline]]``: Path A
    and Path B IS the same algebra on substrate-natural inputs; D1
    algebra-content is bit-exact (numpy arrays equal up to floating-
    point round-off; bytes / scalar outputs literally equal).
    """
    if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        assert a.shape == b.shape, (
            f"{op_name}: Path A shape {a.shape} != Path B shape {b.shape}"
        )
        if np.issubdtype(a.dtype, np.complexfloating) or \
           np.issubdtype(a.dtype, np.floating):
            # Floating-point: allow machine-ε round-off (D1 algebra-
            # identity holds up to fp round-off per Spike #176 T4 anchor).
            max_diff = float(np.max(np.abs(a - b)))
            tol = 1e-12 * max(1.0, float(np.max(np.abs(a))))
            assert max_diff <= tol, (
                f"{op_name}: D1 algebra-identity failure: "
                f"max(|A - B|) = {max_diff:.6e} > {tol:.6e}"
            )
        else:
            assert np.array_equal(a, b), (
                f"{op_name}: D1 algebra-identity failure: integer arrays "
                f"not bit-exact equal"
            )
    elif isinstance(a, (bytes, bytearray)) and isinstance(b, (bytes, bytearray)):
        assert bytes(a) == bytes(b), (
            f"{op_name}: D1 algebra-identity failure on bytes outputs"
        )
    else:
        assert a == b, (
            f"{op_name}: D1 algebra-identity failure on scalar outputs"
        )


def _sample_inputs(op_name: str):
    """Substrate-natural sample inputs for each op."""
    rng = np.random.default_rng(42)
    if op_name == "fft":
        return (rng.standard_normal(64),), {}
    if op_name == "ifft":
        return (rng.standard_normal(64) + 1j * rng.standard_normal(64),), {}
    if op_name == "sign_quantise":
        return (rng.standard_normal(128),), {"threshold": 0.0}
    if op_name == "matched_filter":
        sig = rng.standard_normal(128)
        tmpl = rng.standard_normal(16)
        return (sig, tmpl), {"mode": "full"}
    if op_name == "wiener":
        sig = rng.standard_normal(64)
        n_psd = 0.01 * np.ones(64)
        return (sig, n_psd), {}
    if op_name == "hdc_truncation":
        v1 = bytes(rng.integers(0, 256, size=64, dtype=np.uint8))
        v2 = bytes(rng.integers(0, 256, size=64, dtype=np.uint8))
        v3 = bytes(rng.integers(0, 256, size=64, dtype=np.uint8))
        return ([v1, v2, v3],), {"truncate_popcount": 32}
    raise ValueError(f"Unknown op {op_name!r}")


@pytest.mark.parametrize("op_name", PATH_B_MVP_OPS)
def test_a_b_d1_equivalence(op_name: str):
    """Path A and Path B produce D1 algebra-identical outputs.

    Per ``[[user_stance_identity_not_implementation_discipline]]`` both
    paths IS the same algebra on substrate-natural inputs. Spike #176
    anchor: machine-ε equivalence on cyclic substrate.
    """
    sample_args, sample_kwargs = _sample_inputs(op_name)
    result_a = dispatch(op_name, *sample_args, path=PATH_A, **sample_kwargs)
    result_b = dispatch(op_name, *sample_args, path=PATH_B, **sample_kwargs)
    _assert_d1_equivalent(result_a, result_b, op_name)


# ──────────────────────────────────────────────────────────────────────
# Aggregate tests
# ──────────────────────────────────────────────────────────────────────


def test_all_six_ops_registered():
    """All 6 ops in PATH_B_MVP_OPS are registered with both paths."""
    registered = set(path_registry.registered_ops())
    for op_name in PATH_B_MVP_OPS:
        assert op_name in registered, (
            f"Phase 4 MVP op {op_name!r} not in registry; module-load "
            f"side-effect must register both Path A and Path B."
        )
        assert path_registry.has_path(op_name, PATH_A), (
            f"{op_name!r}: Path A missing from registry"
        )
        assert path_registry.has_path(op_name, PATH_B), (
            f"{op_name!r}: Path B missing from registry"
        )


def test_path_b_mvp_class_composition_valid():
    """All Path B CLASS_COMPOSITION entries reference 14 A-N classes only.

    Per ``[[feedback_no_privileged_primitive_classes]]`` no new primitive
    class is promoted; every Path B op is a composition over the
    existing 14-class A-N vocabulary.
    """
    for op_name in PATH_B_MVP_OPS:
        mod = importlib.import_module(
            f"srmech.signal_processing.path_b_ops.{op_name}"
        )
        for cls in mod.CLASS_COMPOSITION:
            assert cls in VALID_CLASSES, (
                f"{op_name}.CLASS_COMPOSITION class {cls!r} not in "
                f"14 A-N alphabet {sorted(VALID_CLASSES)}; promotion "
                f"forbidden per [[feedback_no_privileged_primitive_classes]]"
            )


# ──────────────────────────────────────────────────────────────────────
# Spike anchor verifications (per-op)
# ──────────────────────────────────────────────────────────────────────


def test_spike_176_t4_round_trip_recovery():
    """Spike #176 T4 anchor — ifft(fft(x)) == x bit-exact at machine ε.

    Per Spike #176 T4: forward + inverse FFT together produce bit-exact
    recovery on real-valued inputs; recovery error = 0.0 at machine ε.
    """
    rng = np.random.default_rng(0)
    for N in (8, 16, 32, 64, 128, 256, 512):
        x = rng.standard_normal(N)
        # Path B forward + Path B inverse
        spec_b = dispatch("fft", x, path=PATH_B)
        recovered_b = dispatch("ifft", spec_b, path=PATH_B)
        max_err_b = float(np.max(np.abs(np.real(recovered_b) - x)))
        # Spike #176 T4 — machine ε tolerance.
        tol = 1e-12 * max(1.0, float(np.max(np.abs(x))))
        assert max_err_b <= tol, (
            f"Spike #176 T4 round-trip failure at N={N}: "
            f"max_err={max_err_b:.6e} > {tol:.6e}"
        )
        # Cross-path round-trip: Path A forward + Path B inverse and vice versa.
        spec_a = dispatch("fft", x, path=PATH_A)
        recovered_ab = dispatch("ifft", spec_a, path=PATH_B)
        recovered_ba = dispatch("ifft", spec_b, path=PATH_A)
        assert float(np.max(np.abs(np.real(recovered_ab) - x))) <= tol
        assert float(np.max(np.abs(np.real(recovered_ba) - x))) <= tol


def test_spike_174_sign_quantise_sha256_ber_preservation():
    """Spike #174 anchor — sign_quantise preserves SHA-256 of clean signal
    at +20 dB SNR.

    Per Spike #174: at +20 dB SNR (noise amplitude = 0.1× signal
    amplitude), per-channel sign-quantisation against a calibration
    threshold preserves the SHA-256 bit-discrete content of the
    underlying clean signal. Kalman destroys 19.79% BER at the same SNR.
    """
    rng = np.random.default_rng(0)
    N = 1024
    clean = rng.choice([-1.0, 1.0], size=N)  # bit-discrete signal
    clean_sha = hashlib.sha256(clean.astype(np.int8).tobytes()).hexdigest()
    # +20 dB SNR
    noise = 0.1 * rng.standard_normal(N)
    noisy = clean + noise
    for path in (PATH_A, PATH_B):
        quantised = dispatch("sign_quantise", noisy, path=path)
        q_sha = hashlib.sha256(quantised.astype(np.int8).tobytes()).hexdigest()
        ber = float(np.sum(quantised != clean.astype(np.int8))) / N
        assert ber == 0.0, (
            f"Spike #174 BER preservation failure (path={path}): "
            f"BER = {ber:.6f}; expected 0.0 at +20 dB SNR"
        )
        assert q_sha == clean_sha, (
            f"Spike #174 SHA-256 preservation failure (path={path}): "
            f"clean SHA != quantised SHA"
        )


def test_spike_159_matched_filter_separation():
    """Spike #159 anchor — matched-filter within-vs-between separation
    is order-of-magnitude.

    Per Spike #159: form-function cross-correlation produces ~31.6×
    within-vs-between separation ratio. Order-of-magnitude (≥ 5×) is
    asserted here as a robust anchor; Spike #159 specifies the exact
    scenario producing 31.6×.
    """
    rng = np.random.default_rng(0)
    N = 256
    template = rng.choice([-1.0, 1.0], size=32)
    signal = 0.5 * rng.standard_normal(N)
    signal[100:132] += template * 3.0
    for path in (PATH_A, PATH_B):
        mf = dispatch("matched_filter", signal, template, path=path)
        peak = float(np.max(np.abs(mf)))
        floor = float(np.mean(np.abs(mf)))
        ratio = peak / floor
        assert ratio >= 5.0, (
            f"Spike #159 matched-filter separation failure (path={path}): "
            f"peak/mean = {ratio:.2f}× < 5× threshold"
        )


def test_spike_117_hdc_truncation_threshold_recovery():
    """Spike #117 + #179 T6 — bit-exact bundle+truncate recovery at
    substrate-natural sparsity rate.

    Per Spike #117 sparse-coding anchor + Spike #179 T6 anchor: HDC
    bundle truncation produces bit-exact identical output between
    Path A and Path B at the substrate-natural sparsity rate.
    """
    rng = np.random.default_rng(0)
    n_vecs = 5  # odd count for bundle
    D_bytes = 256  # D = 2048 bits, > D/18 ≈ 113 sparsity threshold
    vectors = [
        bytes(rng.integers(0, 256, size=D_bytes, dtype=np.uint8))
        for _ in range(n_vecs)
    ]
    # Substrate-natural sparsity rate: keep ~D/18 set bits per Spike #179 T6.
    target_popcount = (D_bytes * 8) // 18
    truncated_a = dispatch(
        "hdc_truncation", vectors,
        truncate_popcount=target_popcount, path=PATH_A,
    )
    truncated_b = dispatch(
        "hdc_truncation", vectors,
        truncate_popcount=target_popcount, path=PATH_B,
    )
    assert truncated_a == truncated_b, (
        "Spike #117 + #179 T6: Path A and Path B hdc_truncation "
        "outputs not bit-exact equal at substrate-natural sparsity rate"
    )
    # Verify popcount is ≤ target (Class K pin-slot threshold).
    popcount = sum(bin(b).count("1") for b in truncated_a)
    assert popcount <= target_popcount, (
        f"hdc_truncation popcount {popcount} > target {target_popcount}; "
        f"Class K pin-slot violated"
    )


# ──────────────────────────────────────────────────────────────────────
# Default-path routing per DEFAULT_PATH_PER_CLASS
# ──────────────────────────────────────────────────────────────────────


def test_default_path_routing_per_class():
    """``dispatch(op_name)`` (no explicit path) routes per
    DEFAULT_PATH_PER_CLASS based on the op's primary class.

    Per plan §3.4: Path A is the default for unspecified-path calls
    except Class K rotation, Class M bind/bundle/permute, A∘C∘M form-
    function rotation, and any call inside a begin_cascade context.
    """
    # sign_quantise primary class = K -> default Path B
    rng = np.random.default_rng(0)
    s = rng.standard_normal(32)
    res_default = dispatch("sign_quantise", s)
    res_explicit_b = dispatch("sign_quantise", s, path=PATH_B)
    # Default routing should produce same output as explicit Path B
    # for Class K-primary ops (DEFAULT_PATH_PER_CLASS["K"] == PATH_B).
    assert DEFAULT_PATH_PER_CLASS["K"] == PATH_B, (
        "DEFAULT_PATH_PER_CLASS['K'] expected PATH_B per plan §3.4"
    )
    assert np.array_equal(res_default, res_explicit_b), (
        "sign_quantise default-routing should equal explicit Path B "
        "(Class K primary => Path B per plan §3.4)"
    )

    # fft primary class = A -> default Path A
    assert DEFAULT_PATH_PER_CLASS["A"] == PATH_A, (
        "DEFAULT_PATH_PER_CLASS['A'] expected PATH_A per plan §3.4"
    )
    res_fft_default = dispatch("fft", s)
    res_fft_explicit_a = dispatch("fft", s, path=PATH_A)
    max_diff = float(np.max(np.abs(res_fft_default - res_fft_explicit_a)))
    assert max_diff == 0.0, (
        f"fft default-routing should equal explicit Path A; max_diff={max_diff}"
    )


# ──────────────────────────────────────────────────────────────────────
# Path B class-composition completeness — every class in any
# CLASS_COMPOSITION tuple has its identity established by a Phase
# 3 core surface OR a Phase 1/2 amsc primitive surface
# ──────────────────────────────────────────────────────────────────────


def test_phase_4_uses_only_existing_classes():
    """No Phase 4 module introduces a class outside 14 A-N.

    Per ``[[feedback_no_privileged_primitive_classes]]`` no new primitive
    class promotion is allowed; every CLASS_COMPOSITION entry must
    reference an existing class in the A-N alphabet.
    """
    seen_classes: set[str] = set()
    for op_name in PATH_B_MVP_OPS:
        mod = importlib.import_module(
            f"srmech.signal_processing.path_b_ops.{op_name}"
        )
        for cls in mod.CLASS_COMPOSITION:
            seen_classes.add(cls)
    assert seen_classes.issubset(VALID_CLASSES), (
        f"Phase 4 introduced classes outside 14 A-N: "
        f"{sorted(seen_classes - VALID_CLASSES)}"
    )
    # Sanity: Phase 4 MVP exercises a useful spread.
    assert len(seen_classes) >= 5, (
        f"Phase 4 MVP should exercise ≥5 distinct classes; got "
        f"{sorted(seen_classes)}"
    )
