"""rc153 (BATCH B7 — modulation).

The 3 NUMERIC signal-processing modulation ops —
``closed_form_ops.fsk`` / ``ofdm`` / ``psk_qam`` — move ``python_only_debt →
composition_of_c`` over the EXISTING C foundations ``srmech_dense_matmul_complex``
(the FSK correlator matvec), ``srmech_fft_c128`` (the OFDM IFFT/FFT), and the
byte-exact Class-N ``rational.{cos,sin,sqrt}`` integer-cascade C ports (the FSK
tones + PSK/QAM constellation). NO new C symbol; ABI stays 3. This suite proves:

1. **VALUE oracles** — each op computes the mathematically-correct result,
   independent of the C-vs-pure question:
     • fsk — a modulated single symbol is a pure tone at ``f_s``; with orthogonal
       (DFT-bin) tones the correlator-bank demod recovers the symbol stream
       exactly (modulate → demodulate round-trip is the identity).
     • ofdm — modulate → demodulate round-trip (no channel) recovers the
       subcarrier symbols to FFT round-off.
     • psk_qam — mapping symbols → constellation → nearest-neighbour demod
       recovers the symbols exactly (PSK M∈{2,4,8}; square QAM M∈{4,16,64}).
2. **WITHIN-TOL native == pure** — each op's native path matches its own
   forced-pure fallback (native OFF via monkeypatch) to reldiff ≤ 1e-9. This is
   a **differential NUMERIC** contract (float DSP), **NOT** byte-identity: an FFT
   butterfly / complex matmul accumulation can FMA-fuse ~1 ULP on some platforms
   (macOS clang), the SAME classification as the F1 FFT / F2 SVD / B4 / B9
   numeric batches. (The FSK / PSK-QAM DECISION indices are additionally exact
   native == pure — the ~1e-15 correlator/distance shift never flips a well-
   separated argmax/argmin.)

This module is **numpy-free** (a test for a numpy-free surface must itself be
numpy-free) — the reference maths is stdlib ``math`` / ``cmath`` / ``random``.
"""

from __future__ import annotations

import cmath
import math
import random

import pytest

from srmech.amsc import _native
from srmech.signal_processing.closed_form_ops import fsk, ofdm, psk_qam

# native availability (the differential tests run regardless — with native
# absent, forced-pure == default so reldiff is trivially 0; they still guard the
# pure path is complete + the dispatch wiring does not change the value).
_HAS_MATMUL = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dense_matmul_complex")
)
_HAS_FFT = _native.has_native_fft_c128()


# ----------------------------------------------------------------------
# helpers (numpy-free)
# ----------------------------------------------------------------------

def _reldiff(a, b):
    """max|a-b| / max|a| — the relative sup-norm error over complex/real seqs."""
    a = [complex(z) for z in a]
    b = [complex(z) for z in b]
    scale = max((abs(z) for z in a), default=1.0) or 1.0
    worst = max((abs(za - zb) for za, zb in zip(a, b)), default=0.0)
    return worst / scale


def _rand_symbols(n, M, seed):
    rng = random.Random(seed)
    return [rng.randrange(M) for _ in range(n)]


# ======================================================================
# fsk — value oracles + native == pure
# ======================================================================

# Orthogonal FSK tones = DFT bins: f_k = m_k / n over n samples at fs = 1, so the
# correlator-bank inner products are exactly n·δ_{k,s} (clean demod).
_FSK_N = 8
_FSK_FREQS = [1.0 / _FSK_N, 2.0 / _FSK_N, 3.0 / _FSK_N]  # M = 3 tones


def test_fsk_single_symbol_is_pure_tone():
    """A modulated single symbol s is the pure tone e^{i·2π·f_s·t} over the
    symbol period (the FSK tone-at-correct-frequency oracle)."""
    for s, f in enumerate(_FSK_FREQS):
        samples = fsk.op([s], frequencies=_FSK_FREQS,
                         samples_per_symbol=_FSK_N, fs=1.0)
        ref = [cmath.exp(2j * math.pi * f * j) for j in range(_FSK_N)]
        assert len(samples) == _FSK_N
        assert _reldiff(ref, samples) < 1e-9, f"fsk tone drift symbol={s}"


@pytest.mark.parametrize("seed", [1, 2, 7, 19])
def test_fsk_modulate_demodulate_roundtrip(seed):
    """With orthogonal tones the correlator-bank demod recovers the symbols."""
    syms = _rand_symbols(12, len(_FSK_FREQS), seed)
    tx = fsk.op(syms, frequencies=_FSK_FREQS, samples_per_symbol=_FSK_N, fs=1.0)
    rx = fsk.op(tx, frequencies=_FSK_FREQS, samples_per_symbol=_FSK_N, fs=1.0,
                demodulate=True)
    assert rx == syms, f"fsk round-trip lost symbols seed={seed}"


def test_fsk_rejects_out_of_range_symbol():
    with pytest.raises(ValueError):
        fsk.op([len(_FSK_FREQS)], frequencies=_FSK_FREQS, samples_per_symbol=_FSK_N)


@pytest.mark.parametrize("seed", [3, 11, 23])
def test_fsk_modulate_native_matches_pure(monkeypatch, seed):
    """Modulate (the C-backed rational.cos/sin tone cascade) native == pure."""
    syms = _rand_symbols(10, len(_FSK_FREQS), seed)
    disp = fsk.op(syms, frequencies=_FSK_FREQS, samples_per_symbol=_FSK_N, fs=1.0)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    pure = fsk.op(syms, frequencies=_FSK_FREQS, samples_per_symbol=_FSK_N, fs=1.0)
    assert _reldiff(pure, disp) < 1e-9, f"fsk modulate native!=pure seed={seed}"


@pytest.mark.parametrize("seed", [5, 13, 29])
def test_fsk_demod_native_matches_pure(monkeypatch, seed):
    """Demodulate — the C-dispatched correlator matvec (mat_matvec ∘ mat_matmul)
    reaches the SAME argmax decision as the forced-pure triple-loop cascade
    (the ~1e-15 correlator shift never flips a well-separated argmax)."""
    syms = _rand_symbols(16, len(_FSK_FREQS), seed)
    tx = fsk.op(syms, frequencies=_FSK_FREQS, samples_per_symbol=_FSK_N, fs=1.0)
    disp = fsk.op(tx, frequencies=_FSK_FREQS, samples_per_symbol=_FSK_N, fs=1.0,
                  demodulate=True)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure matvec
    pure = fsk.op(tx, frequencies=_FSK_FREQS, samples_per_symbol=_FSK_N, fs=1.0,
                  demodulate=True)
    assert disp == pure == syms, f"fsk demod native!=pure seed={seed}"


# ======================================================================
# ofdm — value oracles + native == pure
# ======================================================================

@pytest.mark.parametrize("n_sc,cp", [(8, 2), (16, 4), (32, 8)])
@pytest.mark.parametrize("n_ofdm", [1, 3])
def test_ofdm_modulate_demodulate_roundtrip(n_sc, cp, n_ofdm):
    """Modulate → demodulate (no channel) recovers the subcarrier symbols to FFT
    round-off — the OFDM round-trip ≈ identity oracle."""
    rng = random.Random(100 + n_sc + n_ofdm)
    X = [complex(rng.uniform(-1, 1), rng.uniform(-1, 1))
         for _ in range(n_sc * n_ofdm)]
    tx = ofdm.op(X, n_subcarriers=n_sc, cp_length=cp)
    rx = ofdm.op(tx, n_subcarriers=n_sc, cp_length=cp, demodulate=True)
    # rx is (n_ofdm, n_sc) rows -> flatten and compare
    flat = [v for row in rx for v in row]
    assert len(flat) == len(X)
    assert _reldiff(X, flat) < 1e-9, f"ofdm round-trip drift n_sc={n_sc} cp={cp}"


def test_ofdm_rejects_ragged_symbol_block():
    with pytest.raises(ValueError):
        ofdm.op([1 + 0j] * 7, n_subcarriers=4, cp_length=1)  # 7 % 4 != 0


@pytest.mark.parametrize("n_sc,cp", [(8, 2), (16, 4)])
def test_ofdm_native_matches_pure(monkeypatch, n_sc, cp):
    """Modulate + demodulate (FFT via srmech_fft_c128) native == pure within-tol."""
    rng = random.Random(500 + n_sc)
    X = [complex(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(n_sc * 2)]
    tx_d = ofdm.op(X, n_subcarriers=n_sc, cp_length=cp)
    rx_d = ofdm.op(tx_d, n_subcarriers=n_sc, cp_length=cp, demodulate=True)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure FFT cascade
    tx_p = ofdm.op(X, n_subcarriers=n_sc, cp_length=cp)
    rx_p = ofdm.op(tx_p, n_subcarriers=n_sc, cp_length=cp, demodulate=True)
    assert _reldiff(tx_p, tx_d) < 1e-9, f"ofdm modulate native!=pure n_sc={n_sc}"
    fd = [v for row in rx_d for v in row]
    fp = [v for row in rx_p for v in row]
    assert _reldiff(fp, fd) < 1e-9, f"ofdm demod native!=pure n_sc={n_sc}"


# ======================================================================
# psk_qam — value oracles + native == pure
# ======================================================================

@pytest.mark.parametrize("mod,M", [("psk", 2), ("psk", 4), ("psk", 8),
                                   ("qam", 4), ("qam", 16), ("qam", 64)])
def test_psk_qam_map_demap_recovers_symbols(mod, M):
    """symbols → constellation → nearest-neighbour demod recovers the symbols."""
    syms = list(range(M))
    pts = psk_qam.op(syms, modulation=mod, M=M)
    assert len(pts) == M
    rec = psk_qam.op(pts, modulation=mod, M=M, demodulate=True)
    assert rec == syms, f"psk_qam demap lost symbols mod={mod} M={M}"


def test_psk_constellation_is_unit_circle():
    """M-PSK points lie on the unit circle at exp(i·2π·k/M) — the constellation
    value oracle (the C-backed rational.cos/sin phases)."""
    M = 8
    pts = psk_qam.op(list(range(M)), modulation="psk", M=M)
    for k, z in enumerate(pts):
        ref = cmath.exp(2j * math.pi * k / M)
        assert abs(z - ref) < 1e-9, f"psk point {k} off unit circle"


def test_qam_requires_square_order():
    with pytest.raises(ValueError):
        psk_qam.op([0, 1], modulation="qam", M=8)  # 8 is not a perfect square


def test_psk_qam_rejects_unknown_modulation_and_range():
    with pytest.raises(ValueError):
        psk_qam.op([0], modulation="fsk", M=4)
    with pytest.raises(ValueError):
        psk_qam.op([4], modulation="psk", M=4)  # symbol out of [0, M)


@pytest.mark.parametrize("mod,M", [("psk", 8), ("qam", 16), ("qam", 64)])
def test_psk_qam_native_matches_pure(monkeypatch, mod, M):
    """The constellation build (C-backed rational.cos/sin/sqrt) + nearest-
    neighbour demod native == pure — the map is within-tol, the demap indices
    are exact (the ~1e-15 distance shift never flips a well-separated argmin)."""
    syms = _rand_symbols(20, M, seed=700 + M)
    pts_d = psk_qam.op(syms, modulation=mod, M=M)
    rec_d = psk_qam.op(pts_d, modulation=mod, M=M, demodulate=True)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure rational cascade
    pts_p = psk_qam.op(syms, modulation=mod, M=M)
    rec_p = psk_qam.op(pts_p, modulation=mod, M=M, demodulate=True)
    assert _reldiff(pts_p, pts_d) < 1e-9, f"psk_qam map native!=pure mod={mod} M={M}"
    assert rec_d == rec_p == syms, f"psk_qam demap native!=pure mod={mod} M={M}"


# ======================================================================
# dispatch presence (informational — the value/parity oracles above are the
# real gate; these just record whether the native path was exercised)
# ======================================================================

def test_native_paths_available_report():
    """Not a hard gate: records which C paths back this batch
    (srmech_dense_matmul_complex for the fsk correlator, srmech_fft_c128 for
    ofdm, the rational.* ports for the psk_qam constellation). When absent the
    pure path is the complete alternative and every test above still passes."""
    assert isinstance(_HAS_FFT, bool)
    assert isinstance(_HAS_MATMUL, bool)
