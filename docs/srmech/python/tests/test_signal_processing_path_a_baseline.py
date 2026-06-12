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

import cmath
import importlib
import math
import random
from typing import Any

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

    x = [float(i) for i in range(16)]
    X = m.op(x)
    # rc62: fft.op is numpy-free now — returns a list of complex.
    assert isinstance(X, list) and len(X) == 16
    assert all(isinstance(z, complex) for z in X)


def test_stft_smoke():
    from srmech.signal_processing.closed_form_ops import stft as m

    rng = random.Random(0)
    x = [rng.gauss(0, 1) for _ in range(256)]
    Y = m.op(x, frame_size=64, hop_size=32)
    # rc89: stft.op is numpy-free now — returns a list of per-frame lists.
    assert isinstance(Y, list) and isinstance(Y[0], list)
    assert len(Y[0]) == 64


def test_dct_smoke():
    from srmech.signal_processing.closed_form_ops import dct as m

    x = [float(i) for i in range(8)]
    X = m.op(x)
    assert isinstance(X, list) and len(X) == 8  # rc104: numpy-free list return


def test_wavelet_smoke():
    from srmech.signal_processing.closed_form_ops import wavelet as m

    x = [float(i) for i in range(16)]
    approx, details = m.op(x, levels=2)
    assert isinstance(details, list)
    assert len(details) == 2


def test_spectrogram_smoke():
    from srmech.signal_processing.closed_form_ops import spectrogram as m

    rng = random.Random(0)
    x = [rng.gauss(0, 1) for _ in range(256)]
    S = m.op(x, frame_size=64, hop_size=32)
    # rc89: spectrogram.op is numpy-free now — list of per-frame lists of
    # real |z|^2 energy density.
    assert isinstance(S, list) and isinstance(S[0], list)
    assert len(S[0]) == 64
    assert all(v >= 0 for row in S for v in row)


def test_cross_spectral_smoke():
    from srmech.signal_processing.closed_form_ops import cross_spectral as m

    rng = random.Random(0)
    x = [rng.gauss(0, 1) for _ in range(256)]
    y = [rng.gauss(0, 1) for _ in range(256)]
    freqs, S = m.op(x, y, frame_size=64)
    assert len(freqs) == 64
    assert len(S) == 64


def test_multitaper_smoke():
    from srmech.signal_processing.closed_form_ops import multitaper as m

    rng = random.Random(0)
    x = [rng.gauss(0, 1) for _ in range(64)]
    psd = m.op(x, n_tapers=3, nw=2.0)
    # rc91: multitaper.op is numpy-free now — returns a list of float.
    assert isinstance(psd, list) and len(psd) == 64
    assert all(v >= 0 for v in psd)


def test_matched_filter_smoke():
    from srmech.signal_processing.closed_form_ops import matched_filter as m

    x = [0.0, 0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0, 0.0]
    h = [1.0, 2.0, 1.0]
    y = m.op(x, h)
    # rc80: matched_filter is numpy-free now (list carrier per #564) -> len
    assert len(y) == len(x) + len(h) - 1


def test_wiener_smoke():
    from srmech.signal_processing.closed_form_ops import wiener as m

    rng = random.Random(0)
    x = [rng.gauss(0, 1) for _ in range(64)]
    noise_psd = [0.1] * 64
    y = m.op(x, noise_psd)
    assert len(y) == 64


def test_fir_smoke():
    from srmech.signal_processing.closed_form_ops import fir as m

    x = [float(i) for i in range(16)]
    b = [0.5, 0.5]
    y = m.op(x, b)
    # rc80: fir is numpy-free now (list carrier per #564) -> len, not .shape
    assert len(y) == 17  # full convolution


def test_iir_smoke():
    from srmech.signal_processing.closed_form_ops import iir as m

    x = [float(i) for i in range(16)]
    b = [1.0, 0.0]
    a = [1.0, -0.5]
    y = m.op(x, b, a)
    # rc82: iir is numpy-free now (list carrier per #564) -> len, not .shape
    assert len(y) == 16


def test_allpass_smoke():
    from srmech.signal_processing.closed_form_ops import allpass as m

    rng = random.Random(0)
    x = [rng.gauss(0, 1) for _ in range(16)]
    y = m.op(x, 0.5, order=1)
    # rc77 carrier-flip: numpy-free list carrier (was np.ndarray).
    assert len(y) == 16


def test_sign_quantise_smoke():
    from srmech.signal_processing.closed_form_ops import sign_quantise as m

    x = [-1.0, 0.0, 1.0, 0.1, -0.1]
    y = m.op(x, threshold=0.0, dead_band=0.05)
    # rc77 carrier-flip: numpy-free list carrier (was np.ndarray).
    assert len(y) == 5
    # exact Class-K threshold values: 0.0 lands in the dead-band [-0.05, 0.05].
    assert list(y) == [-1, 0, 1, 1, -1]


def test_heat_kernel_smoke():
    from srmech.signal_processing.closed_form_ops import heat_kernel as m

    # Path Laplacian on a 4-node chain.
    L = [
        [1 + 0j, -1 + 0j, 0 + 0j, 0 + 0j],
        [-1 + 0j, 2 + 0j, -1 + 0j, 0 + 0j],
        [0 + 0j, -1 + 0j, 2 + 0j, -1 + 0j],
        [0 + 0j, 0 + 0j, -1 + 0j, 1 + 0j],
    ]
    x = [1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j]
    y = m.op(x, L, t=0.5)
    assert isinstance(y, list) and len(y) == 4  # rc100: numpy-free list return


def test_spectral_subtraction_smoke():
    from srmech.signal_processing.closed_form_ops import spectral_subtraction as m

    rng = random.Random(0)
    x = [rng.gauss(0, 1) for _ in range(64)]
    npsd = [0.1] * 64
    y = m.op(x, npsd)
    # rc90: spectral_subtraction.op is numpy-free now — returns a list of float.
    assert isinstance(y, list) and len(y) == 64


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

    rng = random.Random(0)
    img = [[rng.random() * 255.0 - 128.0 for _ in range(16)] for _ in range(16)]
    quant_blocks, shape, qt = m.op(img, quality=75)
    assert len(quant_blocks) == 4  # 16/8 * 16/8


def test_hdc_truncation_smoke():
    from srmech.signal_processing.closed_form_ops import hdc_truncation as m

    rng = random.Random(0)
    vectors = [bytes(rng.randrange(256) for _ in range(16)) for _ in range(3)]
    bundled = m.op(vectors)
    assert len(bundled) == 16


def test_vector_quantisation_smoke():
    from srmech.signal_processing.closed_form_ops import vector_quantisation as m

    rng = random.Random(0)
    cb = [[rng.gauss(0, 1) for _ in range(4)] for _ in range(8)]
    vecs = [[rng.gauss(0, 1) for _ in range(4)] for _ in range(10)]
    idx = m.op(vecs, cb)
    assert isinstance(idx, list) and len(idx) == 10  # rc105: numpy-free list return


def test_psk_qam_smoke():
    from srmech.signal_processing.closed_form_ops import psk_qam as m

    syms = [0, 1, 2, 3]
    points = m.op(syms, modulation="psk", M=4)
    # rc106: numpy-free list return
    assert isinstance(points, list) and len(points) == 4
    assert all(isinstance(z, complex) for z in points)
    recovered = m.op(points, modulation="psk", M=4, demodulate=True)
    assert isinstance(recovered, list)
    assert list(recovered) == syms


def test_fsk_smoke():
    from srmech.signal_processing.closed_form_ops import fsk as m

    syms = [0, 1, 0, 1]
    waveform = m.op(syms, frequencies=[0.1, 0.2], samples_per_symbol=8, fs=1.0)
    assert isinstance(waveform, list) and len(waveform) == 4 * 8  # rc103: numpy-free list return


def test_ofdm_smoke():
    from srmech.signal_processing.closed_form_ops import ofdm as m

    n_sub = 16
    n_sym = 2
    rng = random.Random(0)
    syms = [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n_sub * n_sym)]
    waveform = m.op(syms, n_subcarriers=n_sub, cp_length=4)
    assert len(waveform) == n_sym * (n_sub + 4)


def test_mimo_svd_smoke():
    from srmech.signal_processing.closed_form_ops import mimo_svd as m

    rng = random.Random(0)
    H = [[complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(2)] for _ in range(3)]
    U, S, Vh = m.op(H)
    # rc109: mimo_svd is numpy-free now (mat_svd Mat foundation) — returns lists.
    assert isinstance(U, list) and len(U) == 3 and len(U[0]) == 3
    assert isinstance(S, list) and len(S) == 2
    assert isinstance(Vh, list) and len(Vh) == 2 and len(Vh[0]) == 2


def test_viterbi_smoke():
    from srmech.signal_processing.closed_form_ops import viterbi as m

    # 2-state, 2-symbol HMM: sticky preference (log-domain transition/emission).
    A = [[math.log(0.9), math.log(0.1)], [math.log(0.1), math.log(0.9)]]
    B = [[math.log(0.8), math.log(0.2)], [math.log(0.2), math.log(0.8)]]
    pi = [math.log(0.5), math.log(0.5)]
    obs = [0, 0, 1, 1, 1]
    path = m.op(obs, A, B, pi)
    # rc83: viterbi is numpy-free now (list carrier per #564) -> len, not .shape
    assert len(path) == 5
    # Expected: states track observations.
    assert list(path) == [0, 0, 1, 1, 1]


def test_mlse_smoke():
    from srmech.signal_processing.closed_form_ops import mlse as m

    # Simple BPSK with no ISI (single tap).
    taps = [1.0 + 0j]
    alphabet = [-1 + 0j, 1 + 0j]
    obs = [0.9, -0.95, 1.1, -0.85]
    syms = m.op(obs, taps, alphabet)
    # rc107: mlse is numpy-free now — op returns a plain list of int.
    assert isinstance(syms, list) and len(syms) == 4


def test_multirate_smoke():
    from srmech.signal_processing.closed_form_ops import multirate as m

    x = [float(i) for i in range(32)]
    # Up 2 down 3 -> length ~ 32 * 2 / 3 ≈ 21
    y = m.op(x, up=2, down=3)
    # rc92: multirate is numpy-free now — op returns a plain list of float.
    assert isinstance(y, list) and len(y) >= 1


def test_polyphase_smoke():
    from srmech.signal_processing.closed_form_ops import polyphase as m

    x = [float(i) for i in range(32)]
    taps = [0.25, 0.5, 0.25]
    y = m.op(x, taps, L=2, mode="decimation")
    assert isinstance(y, list) and len(y) >= 1


def test_farrow_smoke():
    from srmech.signal_processing.closed_form_ops import farrow as m

    x = [float(i) for i in range(16)]
    y = m.op(x, mu=0.25)
    # rc78: farrow is numpy-free now (plain-list carrier per #564) -> len, not .shape
    assert len(y) == 16


def test_sinc_interp_smoke():
    from srmech.signal_processing.closed_form_ops import sinc_interp as m

    t_s = [float(i) for i in range(8)]
    y = [math.sin(0.5 * t) for t in t_s]
    t_q = [0.5, 1.5, 2.5]
    y_q = m.op(y, t_s, t_q)
    # rc93: sinc_interp is numpy-free now — op returns a list of complex.
    assert isinstance(y_q, list) and len(y_q) == 3


def test_beamforming_fixed_smoke():
    from srmech.signal_processing.closed_form_ops import beamforming_fixed as m

    rng = random.Random(0)
    arr = [[rng.gauss(0, 1) for _ in range(32)] for _ in range(4)]
    delays = [0, 1, 2, 1]
    y = m.op(arr, delays_samples=delays)
    assert isinstance(y, list)
    assert len(y) == 32 - 2  # 32 - max_delay


def test_ica_jade_smoke():
    # rc126: ica_jade is numpy-free, so its test is too — no numpy as the
    # input-builder or oracle (per the numpy-free-test discipline).
    import random

    from srmech.signal_processing.closed_form_ops import ica_jade as m

    # 2 independent uniform-distributed sources, mixed (X = S @ A.T).
    rng = random.Random(0)
    n = 200
    s_true = [[rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)] for _ in range(n)]
    a_mix = [[1.0, 0.5], [0.3, 1.0]]  # rows = sensors
    X = [[s[0] * a_mix[r][0] + s[1] * a_mix[r][1] for r in range(2)] for s in s_true]
    S_hat, W = m.op(X, n_components=2, max_iter=10)
    assert type(S_hat).__name__ == "Mat" and type(W).__name__ == "Mat"
    assert S_hat.shape == (n, 2)
    assert W.shape == (2, 2)


def test_music_smoke():
    from srmech.signal_processing.closed_form_ops import music as m

    M = 4
    # Build a covariance matrix with one strong eigenvalue: R = 0.1·I + a·aᴴ.
    a = [cmath.exp(1j * math.pi * i * 0.3) for i in range(M)]
    R = [
        [(0.1 if i == j else 0.0) + a[i] * a[j].conjugate() for j in range(M)]
        for i in range(M)
    ]
    # Steering vectors over angle bins (rows = sensors, cols = angle bins).
    angles = [-0.5 + k * (1.0 / 63) for k in range(64)]
    A = [[cmath.exp(1j * math.pi * i * ang) for ang in angles] for i in range(M)]
    psd = m.op(R, A, n_sources=1)
    assert isinstance(psd, list) and len(psd) == 64  # rc99: numpy-free list return
    assert all(v > 0 for v in psd)


def test_esprit_smoke():
    from srmech.signal_processing.closed_form_ops import esprit as m

    M = 4
    a = [cmath.exp(1j * math.pi * i * 0.3) for i in range(M)]
    R = [
        [(0.1 if i == j else 0.0) + a[i] * a[j].conjugate() for j in range(M)]
        for i in range(M)
    ]
    eigs = m.op(R, n_sources=1)
    assert isinstance(eigs, list) and len(eigs) == 1  # rc98: numpy-free list return


def test_lmmse_smoke():
    from srmech.signal_processing.closed_form_ops import lmmse as m

    y = [1.0, 2.0]
    R_yy = [[1.0, 0.0], [0.0, 1.0]]
    R_xy = [[1.0, 0.5]]
    x_hat = m.op(y, R_yy, R_xy)
    assert isinstance(x_hat, list) and len(x_hat) == 1  # rc101: numpy-free list return


def test_map_ml_smoke():
    from srmech.signal_processing.closed_form_ops import map_ml as m

    y = [1.0, 2.0, 3.0]
    A = [[1.0, 0.0], [1.0, 1.0], [1.0, 2.0]]
    R_noise = [[0.1 if i == j else 0.0 for j in range(3)] for i in range(3)]
    x_hat = m.op(y, A, R_noise)
    assert isinstance(x_hat, list) and len(x_hat) == 2  # rc102: numpy-free list return
    # MAP with prior
    R_prior = [[1.0, 0.0], [0.0, 1.0]]
    x_hat_map = m.op(y, A, R_noise, R_prior=R_prior)
    assert isinstance(x_hat_map, list) and len(x_hat_map) == 2  # rc102: numpy-free list return


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
