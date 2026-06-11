"""Phase 2 Path A baseline acceptance tests for ``srmech.signal_processing``.

Verifies the 38 closed-form-op modules per the implementation plan
``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md`` Phase 2.

Coverage:

1. All 38 modules import successfully.
2. Each module has the required Path A contract metadata constants:
   ``OPERATION_NAME`` (str), ``CLASS_COMPOSITION`` (tuple of class names),
   ``PERFORMANCE_HINT`` (str), ``SSOT_CITATION`` (str).
3. Each module has a callable ``op`` that accepts standard inputs and
   returns a non-trivial result.
4. ``OPERATION_NAME`` matches the module name.
5. ``CLASS_COMPOSITION`` entries are all valid 14 A-N class identifiers.

This test does NOT exercise the cascade dispatcher (Phase 1 work; deferred to
post-merge integration) and does NOT exercise Path B implementations (Phase 4
work; not yet present in this worktree).
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pytest


PATH_A_OP_MODULES = (
    "fft",
    "stft",
    "dct",
    "wavelet",
    "spectrogram",
    "cross_spectral",
    "multitaper",
    "matched_filter",
    "wiener",
    "fir",
    "iir",
    "allpass",
    "sign_quantise",
    "heat_kernel",
    "spectral_subtraction",
    "huffman",
    "arithmetic_coding",
    "lz77",
    "rle",
    "jpeg",
    "hdc_truncation",
    "vector_quantisation",
    "psk_qam",
    "fsk",
    "ofdm",
    "mimo_svd",
    "viterbi",
    "mlse",
    "multirate",
    "polyphase",
    "farrow",
    "sinc_interp",
    "beamforming_fixed",
    "ica_jade",
    "music",
    "esprit",
    "lmmse",
    "map_ml",
)

VALID_CLASSES = set("ABCDEFGHIJKLMN")
REQUIRED_CONSTANTS = (
    "OPERATION_NAME",
    "CLASS_COMPOSITION",
    "PERFORMANCE_HINT",
    "SSOT_CITATION",
)


# ---------------------------------------------------------------------------
# Import + metadata coverage
# ---------------------------------------------------------------------------


def test_phase_2_ships_38_ops():
    """Phase 2 ships exactly 38 Path A op modules per the implementation plan."""
    assert len(PATH_A_OP_MODULES) == 38, (
        f"Phase 2 expects 38 ops; got {len(PATH_A_OP_MODULES)}"
    )


@pytest.mark.parametrize("op_name", PATH_A_OP_MODULES)
def test_module_imports_successfully(op_name: str):
    """Each of 38 Path A op modules imports cleanly."""
    mod = importlib.import_module(
        f"srmech.signal_processing.closed_form_ops.{op_name}"
    )
    assert mod is not None


@pytest.mark.parametrize("op_name", PATH_A_OP_MODULES)
def test_module_has_required_constants(op_name: str):
    """Each module exposes the Path A contract metadata constants."""
    mod = importlib.import_module(
        f"srmech.signal_processing.closed_form_ops.{op_name}"
    )
    for const in REQUIRED_CONSTANTS:
        assert hasattr(mod, const), (
            f"module {op_name} missing required constant {const!r}"
        )


@pytest.mark.parametrize("op_name", PATH_A_OP_MODULES)
def test_operation_name_matches_module_name(op_name: str):
    """``OPERATION_NAME`` matches the module's filename."""
    mod = importlib.import_module(
        f"srmech.signal_processing.closed_form_ops.{op_name}"
    )
    assert mod.OPERATION_NAME == op_name, (
        f"module {op_name}: OPERATION_NAME = {mod.OPERATION_NAME!r}"
    )


@pytest.mark.parametrize("op_name", PATH_A_OP_MODULES)
def test_class_composition_valid(op_name: str):
    """``CLASS_COMPOSITION`` is a tuple of valid 14 A-N class identifiers."""
    mod = importlib.import_module(
        f"srmech.signal_processing.closed_form_ops.{op_name}"
    )
    cc = mod.CLASS_COMPOSITION
    assert isinstance(cc, tuple), (
        f"module {op_name}: CLASS_COMPOSITION must be tuple; got {type(cc)}"
    )
    assert len(cc) >= 1, (
        f"module {op_name}: CLASS_COMPOSITION must be non-empty"
    )
    for c in cc:
        assert c in VALID_CLASSES, (
            f"module {op_name}: invalid class {c!r}; must be in A-N"
        )


@pytest.mark.parametrize("op_name", PATH_A_OP_MODULES)
def test_performance_hint_is_string(op_name: str):
    mod = importlib.import_module(
        f"srmech.signal_processing.closed_form_ops.{op_name}"
    )
    assert isinstance(mod.PERFORMANCE_HINT, str)
    assert len(mod.PERFORMANCE_HINT) > 0


@pytest.mark.parametrize("op_name", PATH_A_OP_MODULES)
def test_ssot_citation_is_string(op_name: str):
    mod = importlib.import_module(
        f"srmech.signal_processing.closed_form_ops.{op_name}"
    )
    assert isinstance(mod.SSOT_CITATION, str)
    assert len(mod.SSOT_CITATION) > 30  # non-trivial citation


@pytest.mark.parametrize("op_name", PATH_A_OP_MODULES)
def test_module_has_callable_op(op_name: str):
    mod = importlib.import_module(
        f"srmech.signal_processing.closed_form_ops.{op_name}"
    )
    assert hasattr(mod, "op")
    assert callable(mod.op)


# ---------------------------------------------------------------------------
# Smoke tests — each op accepts canonical inputs and returns a result
# ---------------------------------------------------------------------------


def test_fft_smoke():
    from srmech.signal_processing.closed_form_ops import fft as m

    x = np.arange(16, dtype=np.float64)
    X = m.op(x)
    assert X.shape == (16,)
    assert np.iscomplexobj(X)


def test_stft_smoke():
    from srmech.signal_processing.closed_form_ops import stft as m

    x = np.random.RandomState(0).randn(256)
    Y = m.op(x, frame_size=64, hop_size=32)
    assert Y.ndim == 2
    assert Y.shape[1] == 64


def test_dct_smoke():
    from srmech.signal_processing.closed_form_ops import dct as m

    x = np.arange(8, dtype=np.float64)
    X = m.op(x)
    assert X.shape == (8,)


def test_wavelet_smoke():
    from srmech.signal_processing.closed_form_ops import wavelet as m

    x = np.arange(16, dtype=np.float64)
    approx, details = m.op(x, levels=2)
    assert isinstance(details, list)
    assert len(details) == 2


def test_spectrogram_smoke():
    from srmech.signal_processing.closed_form_ops import spectrogram as m

    x = np.random.RandomState(0).randn(256)
    S = m.op(x, frame_size=64, hop_size=32)
    assert S.ndim == 2
    assert np.all(S >= 0)


def test_cross_spectral_smoke():
    from srmech.signal_processing.closed_form_ops import cross_spectral as m

    rs = np.random.RandomState(0)
    x = rs.randn(256)
    y = rs.randn(256)
    freqs, S = m.op(x, y, frame_size=64)
    assert len(freqs) == 64
    assert len(S) == 64


def test_multitaper_smoke():
    from srmech.signal_processing.closed_form_ops import multitaper as m

    x = np.random.RandomState(0).randn(64)
    psd = m.op(x, n_tapers=3, nw=2.0)
    assert psd.shape == (64,)
    assert np.all(psd >= 0)


def test_matched_filter_smoke():
    from srmech.signal_processing.closed_form_ops import matched_filter as m

    x = np.array([0, 0, 1, 2, 3, 2, 1, 0, 0], dtype=np.float64)
    h = np.array([1, 2, 1], dtype=np.float64)
    y = m.op(x, h)
    # rc80: matched_filter is numpy-free now (list carrier per #564) -> len
    assert len(y) == x.shape[0] + h.shape[0] - 1


def test_wiener_smoke():
    from srmech.signal_processing.closed_form_ops import wiener as m

    x = np.random.RandomState(0).randn(64)
    noise_psd = np.ones(64) * 0.1
    y = m.op(x, noise_psd)
    assert len(y) == 64


def test_fir_smoke():
    from srmech.signal_processing.closed_form_ops import fir as m

    x = np.arange(16, dtype=np.float64)
    b = np.array([0.5, 0.5])
    y = m.op(x, b)
    # rc80: fir is numpy-free now (list carrier per #564) -> len, not .shape
    assert len(y) == 17  # full convolution


def test_iir_smoke():
    from srmech.signal_processing.closed_form_ops import iir as m

    x = np.arange(16, dtype=np.float64)
    b = [1.0, 0.0]
    a = [1.0, -0.5]
    y = m.op(x, b, a)
    # rc82: iir is numpy-free now (list carrier per #564) -> len, not .shape
    assert len(y) == 16


def test_allpass_smoke():
    from srmech.signal_processing.closed_form_ops import allpass as m

    x = np.random.RandomState(0).randn(16)
    y = m.op(x, 0.5, order=1)
    # rc77 carrier-flip: numpy-free list carrier (was np.ndarray).
    assert len(y) == 16


def test_sign_quantise_smoke():
    from srmech.signal_processing.closed_form_ops import sign_quantise as m

    x = np.array([-1.0, 0.0, 1.0, 0.1, -0.1])
    y = m.op(x, threshold=0.0, dead_band=0.05)
    # rc77 carrier-flip: numpy-free list carrier (was np.ndarray).
    assert len(y) == 5
    # exact Class-K threshold values: 0.0 lands in the dead-band [-0.05, 0.05].
    assert list(y) == [-1, 0, 1, 1, -1]


def test_heat_kernel_smoke():
    from srmech.signal_processing.closed_form_ops import heat_kernel as m

    # Path Laplacian on a 4-node chain.
    L = np.array(
        [
            [1.0, -1.0, 0.0, 0.0],
            [-1.0, 2.0, -1.0, 0.0],
            [0.0, -1.0, 2.0, -1.0],
            [0.0, 0.0, -1.0, 1.0],
        ],
        dtype=np.complex128,
    )
    x = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
    y = m.op(x, L, t=0.5)
    assert y.shape == (4,)


def test_spectral_subtraction_smoke():
    from srmech.signal_processing.closed_form_ops import spectral_subtraction as m

    x = np.random.RandomState(0).randn(64)
    npsd = np.ones(64) * 0.1
    y = m.op(x, npsd)
    assert y.shape == (64,)


def test_huffman_smoke():
    from srmech.signal_processing.closed_form_ops import huffman as m

    data = b"abracadabra"
    bits, codes = m.op(data)
    assert isinstance(bits, str)
    assert all(c in "01" for c in bits)
    recovered = m.op(bits, decode=True, codes=codes)
    assert recovered == data


def test_arithmetic_coding_smoke():
    from srmech.signal_processing.closed_form_ops import arithmetic_coding as m

    data = b"abc"
    freq = {ord("a"): 3, ord("b"): 2, ord("c"): 1}
    lo, hi, freq_used = m.op(data, freq=freq)
    assert lo < hi


def test_lz77_smoke():
    from srmech.signal_processing.closed_form_ops import lz77 as m

    data = b"abcabcabc"
    tokens = m.op(data, window_size=16, lookahead_size=8)
    recovered = m.op(tokens, decode=True)
    assert recovered == data


def test_rle_smoke():
    from srmech.signal_processing.closed_form_ops import rle as m

    data = b"aaabbbcccc"
    tokens = m.op(data)
    recovered = m.op(tokens, decode=True)
    assert recovered == data


def test_jpeg_smoke():
    from srmech.signal_processing.closed_form_ops import jpeg as m

    img = np.random.RandomState(0).rand(16, 16) * 255.0 - 128.0
    quant_blocks, shape, qt = m.op(img, quality=75)
    assert len(quant_blocks) == 4  # 16/8 * 16/8


def test_hdc_truncation_smoke():
    from srmech.signal_processing.closed_form_ops import hdc_truncation as m

    rs = np.random.RandomState(0)
    vectors = [bytes(rs.randint(0, 256, 16, dtype=np.uint8).tolist()) for _ in range(3)]
    bundled = m.op(vectors)
    assert len(bundled) == 16


def test_vector_quantisation_smoke():
    from srmech.signal_processing.closed_form_ops import vector_quantisation as m

    rs = np.random.RandomState(0)
    cb = rs.randn(8, 4)
    vecs = rs.randn(10, 4)
    idx = m.op(vecs, cb)
    assert idx.shape == (10,)


def test_psk_qam_smoke():
    from srmech.signal_processing.closed_form_ops import psk_qam as m

    syms = np.array([0, 1, 2, 3], dtype=np.int64)
    points = m.op(syms, modulation="psk", M=4)
    assert points.shape == (4,)
    assert np.iscomplexobj(points)
    recovered = m.op(points, modulation="psk", M=4, demodulate=True)
    assert np.array_equal(recovered, syms)


def test_fsk_smoke():
    from srmech.signal_processing.closed_form_ops import fsk as m

    syms = np.array([0, 1, 0, 1], dtype=np.int64)
    waveform = m.op(syms, frequencies=[0.1, 0.2], samples_per_symbol=8, fs=1.0)
    assert waveform.shape == (4 * 8,)


def test_ofdm_smoke():
    from srmech.signal_processing.closed_form_ops import ofdm as m

    n_sub = 16
    n_sym = 2
    syms = (np.random.RandomState(0).randn(n_sub * n_sym) +
            1j * np.random.RandomState(1).randn(n_sub * n_sym))
    waveform = m.op(syms, n_subcarriers=n_sub, cp_length=4)
    assert len(waveform) == n_sym * (n_sub + 4)


def test_mimo_svd_smoke():
    from srmech.signal_processing.closed_form_ops import mimo_svd as m

    H = np.random.RandomState(0).randn(3, 2) + 1j * np.random.RandomState(1).randn(3, 2)
    U, S, Vh = m.op(H)
    assert U.shape == (3, 3)
    assert S.shape == (2,)
    assert Vh.shape == (2, 2)


def test_viterbi_smoke():
    from srmech.signal_processing.closed_form_ops import viterbi as m

    # 2-state, 2-symbol HMM: sticky preference.
    A = np.log(np.array([[0.9, 0.1], [0.1, 0.9]]))
    B = np.log(np.array([[0.8, 0.2], [0.2, 0.8]]))
    pi = np.log(np.array([0.5, 0.5]))
    obs = np.array([0, 0, 1, 1, 1])
    path = m.op(obs, A, B, pi)
    # rc83: viterbi is numpy-free now (list carrier per #564) -> len, not .shape
    assert len(path) == 5
    # Expected: states track observations.
    assert np.array_equal(path, np.array([0, 0, 1, 1, 1]))


def test_mlse_smoke():
    from srmech.signal_processing.closed_form_ops import mlse as m

    # Simple BPSK with no ISI (single tap).
    taps = np.array([1.0 + 0j])
    alphabet = np.array([-1 + 0j, 1 + 0j])
    obs = np.array([0.9, -0.95, 1.1, -0.85])
    syms = m.op(obs, taps, alphabet)
    assert syms.shape == (4,)


def test_multirate_smoke():
    from srmech.signal_processing.closed_form_ops import multirate as m

    x = np.arange(32, dtype=np.float64)
    # Up 2 down 3 -> length ~ 32 * 2 / 3 ≈ 21
    y = m.op(x, up=2, down=3)
    assert y.ndim == 1


def test_polyphase_smoke():
    from srmech.signal_processing.closed_form_ops import polyphase as m

    x = np.arange(32, dtype=np.float64)
    taps = np.array([0.25, 0.5, 0.25])
    y = m.op(x, taps, L=2, mode="decimation")
    assert isinstance(y, list) and len(y) >= 1


def test_farrow_smoke():
    from srmech.signal_processing.closed_form_ops import farrow as m

    x = np.arange(16, dtype=np.float64)
    y = m.op(x, mu=0.25)
    # rc78: farrow is numpy-free now (plain-list carrier per #564) -> len, not .shape
    assert len(y) == 16


def test_sinc_interp_smoke():
    from srmech.signal_processing.closed_form_ops import sinc_interp as m

    t_s = np.arange(8, dtype=np.float64)
    y = np.sin(0.5 * t_s)
    t_q = np.array([0.5, 1.5, 2.5])
    y_q = m.op(y, t_s, t_q)
    assert y_q.shape == (3,)


def test_beamforming_fixed_smoke():
    from srmech.signal_processing.closed_form_ops import beamforming_fixed as m

    arr = np.random.RandomState(0).randn(4, 32)
    delays = [0, 1, 2, 1]
    y = m.op(arr, delays_samples=delays)
    assert isinstance(y, list)
    assert len(y) == 32 - 2  # 32 - max_delay


def test_ica_jade_smoke():
    from srmech.signal_processing.closed_form_ops import ica_jade as m

    rs = np.random.RandomState(0)
    # 2 independent uniform-distributed sources, mixed.
    n = 200
    S_true = rs.uniform(-1, 1, (n, 2))
    A_mix = np.array([[1.0, 0.5], [0.3, 1.0]])
    X = S_true @ A_mix.T
    S_hat, W = m.op(X, n_components=2, max_iter=10)
    assert S_hat.shape == (n, 2)
    assert W.shape == (2, 2)


def test_music_smoke():
    from srmech.signal_processing.closed_form_ops import music as m

    M = 4
    # Build a covariance matrix with one strong eigenvalue.
    rs = np.random.RandomState(0)
    R = np.eye(M, dtype=np.complex128) * 0.1
    a = np.exp(1j * np.pi * np.arange(M) * 0.3)
    R += np.outer(a, a.conj())
    # Steering vectors over angle bins.
    angles = np.linspace(-0.5, 0.5, 64)
    A = np.exp(1j * np.pi * np.arange(M)[:, None] * angles[None, :])
    psd = m.op(R, A, n_sources=1)
    assert psd.shape == (64,)
    assert np.all(psd > 0)


def test_esprit_smoke():
    from srmech.signal_processing.closed_form_ops import esprit as m

    M = 4
    rs = np.random.RandomState(0)
    R = np.eye(M, dtype=np.complex128) * 0.1
    a = np.exp(1j * np.pi * np.arange(M) * 0.3)
    R += np.outer(a, a.conj())
    eigs = m.op(R, n_sources=1)
    assert eigs.shape == (1,)


def test_lmmse_smoke():
    from srmech.signal_processing.closed_form_ops import lmmse as m

    y = np.array([1.0, 2.0])
    R_yy = np.eye(2)
    R_xy = np.array([[1.0, 0.5]])
    x_hat = m.op(y, R_yy, R_xy)
    assert x_hat.shape == (1,)


def test_map_ml_smoke():
    from srmech.signal_processing.closed_form_ops import map_ml as m

    y = np.array([1.0, 2.0, 3.0])
    A = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 2.0]])
    R_noise = np.eye(3) * 0.1
    x_hat = m.op(y, A, R_noise)
    assert x_hat.shape == (2,)
    # MAP with prior
    R_prior = np.eye(2)
    x_hat_map = m.op(y, A, R_noise, R_prior=R_prior)
    assert x_hat_map.shape == (2,)


# ---------------------------------------------------------------------------
# Aggregate registry check
# ---------------------------------------------------------------------------


def test_path_a_op_modules_constant():
    """The PATH_A_OP_MODULES constant in __init__ matches local list."""
    from srmech.signal_processing.closed_form_ops import PATH_A_OP_MODULES as pkg_list

    assert set(pkg_list) == set(PATH_A_OP_MODULES)
    assert len(pkg_list) == 38


def test_no_class_promotion():
    """No op claims a class outside 14 A-N (per [[feedback_no_privileged_primitive_classes]])."""
    for op_name in PATH_A_OP_MODULES:
        mod = importlib.import_module(
            f"srmech.signal_processing.closed_form_ops.{op_name}"
        )
        for c in mod.CLASS_COMPOSITION:
            assert c in VALID_CLASSES, (
                f"module {op_name} claims invalid class {c!r}; vocabulary is 14 A-N"
            )
