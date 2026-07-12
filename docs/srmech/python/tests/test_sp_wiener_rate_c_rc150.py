"""rc150 (BATCH B4c — sp_transform part 3, wiener / rate-conversion / polyphase).

The 5 NUMERIC DSP ops — ``closed_form_ops.wiener`` / ``path_b_ops.wiener`` /
``closed_form_ops.multirate`` / ``closed_form_ops.polyphase.op`` /
``closed_form_ops.polyphase.decompose`` — move ``python_only_debt →``
``composition_of_c`` (the 4 compute ops, over the EXISTING C foundations
``srmech_fft_c128`` (wiener) and ``srmech_dense_matmul_complex`` (multirate /
polyphase, via a Toeplitz matvec)) / ``non_compute`` (``polyphase.decompose``,
a pure integer reindex). This suite proves:

1. **VALUE oracles** — each op computes the mathematically-correct result,
   independent of the C-vs-pure question:
     • Wiener recovers a clean signal (zero-noise passthrough + averaged
       MSE improvement of a tone buried in broadband noise, true per-bin PSDs)
       and Path A ≡ Path B (identity, not implementation).
     • multirate up-then-down by the same factor ≈ identity (interior) +
       interpolating a constant reproduces the constant + exact length laws.
     • polyphase interpolation reconstruction == the direct FIR filter on the
       zero-stuffed input (the EXACT Type-1 polyphase identity) + decompose is
       an exact reindex round-trip (recompose == the zero-padded taps).
2. **WITHIN-TOL native == pure** — each compute op's native path matches its own
   forced-pure fallback (native OFF via monkeypatch) to reldiff ≤ 1e-9. This is
   a **differential NUMERIC** contract (float DSP), **NOT** byte-identity: an FFT
   butterfly / convolution matmul can FMA-fuse ~1 ULP on some platforms (macOS
   clang), so byte-equality is not claimed — the SAME classification as the F1
   FFT / F2 SVD / B4a / B4b numeric batches.

This module is **numpy-free** (a test for a numpy-free surface must itself be
numpy-free) — the reference maths is stdlib ``math`` / ``cmath`` / ``random``.
"""

from __future__ import annotations

import cmath
import math
import random

import pytest

from srmech.amsc import _native
from srmech.signal_processing.closed_form_ops import multirate, polyphase, wiener
from srmech.signal_processing.path_b_ops import wiener as wiener_b

# native availability (the differential tests run regardless — with native
# absent, forced-pure == default so reldiff is trivially 0; they still guard
# the pure path is complete + the dispatch wiring does not change the value).
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


def _rand_real(n, seed):
    rng = random.Random(seed)
    return [rng.uniform(-3.0, 3.0) for _ in range(n)]


def _naive_dft(x):
    """Independent naive DFT ``X_k = Σ_n x_n e^{-2πi kn/N}`` (no numpy, no srmech)."""
    n = len(x)
    out = []
    for k in range(n):
        acc = 0j
        for j in range(n):
            acc += x[j] * cmath.exp(-2j * math.pi * k * j / n)
        out.append(acc)
    return out


def _ref_convolve_full(x, h):
    """Independent naive full linear convolution (no numpy, no srmech)."""
    nx, nh = len(x), len(h)
    out = [0.0] * (nx + nh - 1)
    for i in range(nx):
        for j in range(nh):
            out[i + j] += x[i] * h[j]
    return out


def _upsample(x, L):
    """Insert ``L-1`` zeros between samples (numpy-free)."""
    u = [0.0] * (len(x) * L)
    for i, v in enumerate(x):
        u[i * L] = v
    return u


# ======================================================================
# Wiener — value oracles + native == pure
# ======================================================================

@pytest.mark.parametrize("path", ["a", "b"])
def test_wiener_zero_noise_is_passthrough(path):
    """With a (near-)zero noise PSD the Wiener gain H≈1 in every bin, so the
    filter passes the signal through unchanged (a clean deterministic oracle)."""
    x = _rand_real(32, seed=3)
    op = wiener.op if path == "a" else wiener_b.op
    y = op(x, [0.0] * len(x))
    assert _reldiff(x, y) < 1e-6, f"wiener path={path} zero-noise != passthrough"


def test_wiener_recovers_tone_from_noise():
    """Wiener with the TRUE per-bin signal / noise PSDs reduces the mean-square
    error of a tone buried in broadband noise (the MMSE recovery property).

    Averaged over several noise realizations so the statistical optimum is a
    deterministic pass, not a per-seed coin-flip."""
    n = 32
    clean = [2.0 * math.sin(2.0 * math.pi * 3.0 * k / n) for k in range(n)]
    clean_psd = [abs(z) ** 2 for z in _naive_dft(clean)]
    improved = 0
    trials = 8
    for seed in range(trials):
        rng = random.Random(100 + seed)
        noise = [rng.gauss(0.0, 1.0) for _ in range(n)]
        noisy = [clean[k] + noise[k] for k in range(n)]
        noise_psd = [abs(z) ** 2 for z in _naive_dft(noise)]
        est = wiener.op(noisy, noise_psd, signal_psd=clean_psd)
        mse_noisy = sum((noisy[k] - clean[k]) ** 2 for k in range(n)) / n
        mse_est = sum((est[k] - clean[k]) ** 2 for k in range(n)) / n
        if mse_est < mse_noisy:
            improved += 1
    # The MMSE filter with true PSDs improves the vast majority of realizations.
    assert improved >= trials - 1, f"wiener improved only {improved}/{trials}"


def test_wiener_paths_agree():
    """Path A and Path B compute the same Wiener estimate (identity, not
    implementation) — value-identical to round-off."""
    x = _rand_real(24, seed=41)
    n_psd = [0.5 + 0.1 * k for k in range(len(x))]
    a = wiener.op(x, n_psd)
    b = wiener_b.op(x, n_psd)
    assert _reldiff(a, b) < 1e-12, "wiener path A != path B"


@pytest.mark.parametrize("path", ["a", "b"])
@pytest.mark.parametrize("n", [16, 24, 31])
def test_wiener_native_matches_pure(monkeypatch, path, n):
    """The C-dispatched Wiener (FFT via srmech_fft_c128) matches the forced-pure
    cexp-cascade FFT within-tol — NOT byte-identical."""
    x = _rand_real(n, seed=500 + n)
    n_psd = [0.3 + 0.05 * ((k * 7) % 5) for k in range(n)]
    op = wiener.op if path == "a" else wiener_b.op
    disp = op(x, n_psd)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure FFT cascade
    pure = op(x, n_psd)
    assert _reldiff(pure, disp) < 1e-9, f"wiener native!=pure path={path} n={n}"


# ======================================================================
# multirate — value oracles + native == pure
# ======================================================================

@pytest.mark.parametrize("L,M", [(2, 1), (3, 1), (1, 2), (3, 2), (2, 3)])
def test_multirate_length_laws(L, M):
    """Up-sample by L multiplies the length by L; down-sample by M keeps every
    M-th sample — the exact (integer) length laws. A single-tap identity filter
    is passed so the ``mode="same"`` length is the up-sampled length (decoupled
    from the 41-tap default, whose length would dominate a short signal)."""
    x = _rand_real(30, seed=10 * L + M)
    y = multirate.op(x, up=L, down=M, filter_taps=[1.0])
    expected = len(range(0, len(x) * L, M))
    assert len(y) == expected, f"multirate length up={L} down={M}"


def test_multirate_constant_interpolation_is_constant():
    """Interpolating a constant reproduces the constant in the interior (the
    windowed-sinc low-pass has unity DC gain; the ×up scaling restores level)."""
    c = 1.5
    L = 3
    x = [c] * 60
    y = multirate.op(x, up=L, down=1)  # length 180 (60·3), 41-tap default filter
    # skip the filter transient (~one tap-length) at each edge.
    guard = 44
    interior = y[guard:len(y) - guard]
    assert interior, "interior slice empty"
    worst = max(abs(v - c) for v in interior)
    assert worst < 5e-2, f"constant interpolation drifted by {worst}"


def test_multirate_up_then_down_is_near_identity():
    """Up-sample by L then down-sample by L (with the low-pass on each stage)
    ≈ the identity for a band-limited signal, in the interior (loose tol — the
    hard gate is the native==pure reldiff ≤ 1e-9 below)."""
    n = 48
    L = 2
    x = [math.sin(2.0 * math.pi * 2.0 * k / n) for k in range(n)]
    up = multirate.op(x, up=L, down=1)
    back = multirate.op(up, up=1, down=L)
    m = min(len(x), len(back))
    guard = 12
    worst = max(abs(x[k] - back[k]) for k in range(guard, m - guard))
    assert worst < 1e-1, f"up-then-down deviated by {worst}"


@pytest.mark.parametrize("L,M", [(2, 1), (3, 2), (1, 3)])
def test_multirate_native_matches_pure(monkeypatch, L, M):
    """The C-dispatched multirate (Toeplitz-matvec convolution) matches the
    forced-pure convolution within-tol — NOT byte-identical."""
    x = _rand_real(40, seed=333 + 10 * L + M)
    disp = multirate.op(x, up=L, down=M)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure convolve
    pure = multirate.op(x, up=L, down=M)
    assert _reldiff(pure, disp) < 1e-9, f"multirate native!=pure up={L} down={M}"


# ======================================================================
# polyphase — value oracles + native == pure
# ======================================================================

@pytest.mark.parametrize("L", [2, 3, 4])
def test_polyphase_decompose_is_exact_reindex_roundtrip(L):
    """decompose splits h into L phase branches E_k[n]=h[k+nL]; recomposing them
    (interleave) returns h zero-padded to a multiple of L — an EXACT (byte-
    identical) integer reindex, no float compute."""
    h = [float(v) for v in _rand_real(11, seed=90 + L)]
    comps = polyphase.decompose(h, L)
    assert len(comps) == L
    pad = (-len(h)) % L
    padded = h + [0.0] * pad
    recomposed = [0.0] * len(padded)
    for k, e_k in enumerate(comps):
        for i, v in enumerate(e_k):
            recomposed[k + i * L] = v
    assert recomposed == padded, f"decompose reindex round-trip L={L}"


@pytest.mark.parametrize("L", [2, 3])
def test_polyphase_interpolation_reconstructs_direct_filter(L):
    """The EXACT Type-1 polyphase identity: interpolation-mode output equals the
    direct FIR filter of the zero-stuffed input,
    ``polyphase(x, h, L, "interpolation") == conv(upsample(x, L), h_padded)``."""
    x = _rand_real(9, seed=55 + L)
    h = _rand_real(7, seed=66 + L)
    got = polyphase.op(x, h, L=L, mode="interpolation")
    pad = (-len(h)) % L
    h_padded = h + [0.0] * pad
    ref = _ref_convolve_full(_upsample(x, L), h_padded)
    m = min(len(got), len(ref))
    assert m > 0
    assert _reldiff(ref[:m], got[:m]) < 1e-9, f"polyphase interp reconstruction L={L}"
    # trailing entries beyond the shared prefix must be ~0 (zero-pad tail).
    for v in got[m:]:
        assert abs(v) < 1e-9
    for v in ref[m:]:
        assert abs(v) < 1e-9


@pytest.mark.parametrize("mode", ["decimation", "interpolation"])
@pytest.mark.parametrize("L", [2, 3])
def test_polyphase_native_matches_pure(monkeypatch, mode, L):
    """The C-dispatched polyphase (per-component Toeplitz-matvec convolution)
    matches the forced-pure convolution within-tol — NOT byte-identical."""
    x = _rand_real(20, seed=700 + 10 * L + (1 if mode == "decimation" else 2))
    h = _rand_real(9, seed=800 + L)
    disp = polyphase.op(x, h, L=L, mode=mode)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure convolve
    pure = polyphase.op(x, h, L=L, mode=mode)
    assert _reldiff(pure, disp) < 1e-9, f"polyphase native!=pure mode={mode} L={L}"


# ======================================================================
# dispatch presence (informational — the value/parity oracles above are the
# real gate; these just record whether the native path was exercised)
# ======================================================================

def test_native_paths_available_report():
    """Not a hard gate: records which C paths back this batch (srmech_fft_c128 for
    wiener, srmech_dense_matmul_complex for multirate/polyphase). When absent the
    pure path is the complete alternative and every test above still passes."""
    assert isinstance(_HAS_FFT, bool)
    assert isinstance(_HAS_MATMUL, bool)
