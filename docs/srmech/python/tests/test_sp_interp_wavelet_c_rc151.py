"""rc151 (BATCH B4d — sp_transform part 4, CLOSES B4: interpolators / wavelet /
spectral-subtraction).

The last 4 NUMERIC DSP ops — ``closed_form_ops.farrow`` / ``sinc_interp`` /
``wavelet`` / ``spectral_subtraction`` — move ``python_only_debt →
composition_of_c`` over the EXISTING C foundations ``srmech_dense_matmul_complex``
(the farrow Toeplitz-matvec convolution + the sinc / Haar matvecs) and
``srmech_fft_c128`` (spectral_subtraction). NO new C symbol; ABI stays 3. This
suite proves:

1. **VALUE oracles** — each op computes the mathematically-correct result,
   independent of the C-vs-pure question:
     • farrow ``mu=0`` == exact integer-delay passthrough; a general ``mu``
       matches the independent per-sample cubic-Lagrange reference.
     • sinc_interp with ``target_indices == sample_indices`` recovers the samples
       exactly (the sinc matrix is the identity), and a band-limited tone is
       reconstructed at intermediate points to tol.
     • wavelet Haar analysis is perfectly reconstructed by the orthonormal
       synthesis (``inverse ∘ forward ≈ identity``).
     • spectral_subtraction of a clean signal with a (near-)zero noise floor
       passes the signal through unchanged.
2. **WITHIN-TOL native == pure** — each op's native path matches its own
   forced-pure fallback (native OFF via monkeypatch) to reldiff ≤ 1e-9. This is
   a **differential NUMERIC** contract (float DSP), **NOT** byte-identity: an FFT
   butterfly / convolution matmul can FMA-fuse ~1 ULP on some platforms (macOS
   clang), so byte-equality is not claimed — the SAME classification as the F1
   FFT / F2 SVD / B4a / B4b / B4c numeric batches.

This module is **numpy-free** (a test for a numpy-free surface must itself be
numpy-free) — the reference maths is stdlib ``math`` / ``cmath`` / ``random``.
"""

from __future__ import annotations

import cmath
import math
import random

import pytest

from srmech.amsc import _native
from srmech.signal_processing.closed_form_ops import (
    farrow,
    sinc_interp,
    spectral_subtraction,
    wavelet,
)

# native availability (the differential tests run regardless — with native
# absent, forced-pure == default so reldiff is trivially 0; they still guard the
# pure path is complete + the dispatch wiring does not change the value).
_HAS_MATMUL = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dense_matmul_complex")
)
_HAS_FFT = _native.has_native_fft_c128()

# Cubic-Lagrange Farrow sub-filters (mirror of the op's constant table).
_C = (
    (0.0, 1.0, 0.0, 0.0),
    (-1 / 6, -1 / 2, 1.0, -1 / 3),
    (0.0, 1 / 2, -1.0, 1 / 2),
    (1 / 6, -1 / 2, 1 / 2, -1 / 6),
)


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


def _farrow_ref(sig, mu):
    """Independent per-sample cubic-Lagrange Farrow reference (no srmech)."""
    n = len(sig)
    padded = [0.0] + list(sig) + [0.0, 0.0]
    out = []
    for i in range(n):
        x = padded[i:i + 4]
        y = 0.0
        for k in range(4):
            c = _C[k]
            dot = c[0] * x[0] + c[1] * x[1] + c[2] * x[2] + c[3] * x[3]
            y += (mu ** k) * dot
        out.append(y)
    return out


def _haar_inverse(approx, details):
    """Orthonormal Haar synthesis: reconstruct from (approx_coarsest,
    [detail_coarsest, ..., detail_finest]) — e=(a+d)/√2, o=(a-d)/√2."""
    inv = 1.0 / math.sqrt(2.0)
    cur = list(approx)
    for detail in details:  # coarsest -> finest
        h = len(detail)
        new = [0.0] * (2 * h)
        for m in range(h):
            a = cur[m] if m < len(cur) else 0.0
            d = detail[m]
            new[2 * m] = (a + d) * inv
            new[2 * m + 1] = (a - d) * inv
        cur = new
    return cur


# ======================================================================
# farrow — value oracles + native == pure
# ======================================================================

@pytest.mark.parametrize("n", [1, 4, 16, 31])
def test_farrow_mu_zero_is_integer_delay_passthrough(n):
    """mu=0 -> h_eff = C[0] = (0,1,0,0) -> the output is the input unchanged."""
    x = _rand_real(n, seed=17 + n)
    y = farrow.op(x, mu=0.0)
    assert len(y) == n
    assert _reldiff(x, y) < 1e-12, "farrow mu=0 != integer-delay passthrough"


@pytest.mark.parametrize("mu", [0.1, 0.25, 0.5, 0.73])
def test_farrow_matches_lagrange_reference(mu):
    """A general mu matches the independent per-sample cubic-Lagrange reference."""
    x = _rand_real(20, seed=int(mu * 100) + 3)
    got = farrow.op(x, mu=mu)
    ref = _farrow_ref(x, mu)
    assert _reldiff(ref, got) < 1e-9, f"farrow != lagrange reference mu={mu}"


def test_farrow_empty_and_bounds():
    """Empty input -> []; mu out of [0,1) rejected."""
    assert farrow.op([], mu=0.3) == []
    with pytest.raises(ValueError):
        farrow.op([1.0, 2.0], mu=1.0)
    with pytest.raises(ValueError):
        farrow.op([1.0, 2.0], mu=-0.1)


@pytest.mark.parametrize("mu", [0.2, 0.5, 0.9])
@pytest.mark.parametrize("n", [12, 17, 32])
def test_farrow_native_matches_pure(monkeypatch, mu, n):
    """The C-dispatched farrow (Toeplitz-matvec correlation) matches the
    forced-pure convolution cascade within-tol — NOT byte-identical."""
    x = _rand_real(n, seed=400 + n)
    disp = farrow.op(x, mu=mu)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure correlate
    pure = farrow.op(x, mu=mu)
    assert _reldiff(pure, disp) < 1e-9, f"farrow native!=pure mu={mu} n={n}"


# ======================================================================
# sinc_interp — value oracles + native == pure
# ======================================================================

def test_sinc_interp_identity_at_sample_points():
    """target_indices == sample_indices -> the sinc matrix is the identity
    (sinc of nonzero integers is 0), so the samples are recovered exactly."""
    t_s = [float(i) for i in range(10)]
    y = [math.sin(0.4 * t) + 0.5 * math.cos(0.2 * t) for t in t_s]
    got = sinc_interp.op(y, t_s, t_s)
    assert len(got) == len(t_s)
    assert _reldiff([complex(v) for v in y], got) < 1e-9, "sinc identity failed"


def test_sinc_interp_recovers_bandlimited_tone():
    """A tone well below Nyquist is reconstructed at intermediate points."""
    n = 24
    t_s = [float(i) for i in range(n)]
    f = 0.1  # cycles/sample, << 0.5 Nyquist
    y = [math.sin(2.0 * math.pi * f * t) for t in t_s]
    t_q = [2.5, 5.5, 9.5, 13.5]
    got = sinc_interp.op(y, t_s, t_q)
    truth = [math.sin(2.0 * math.pi * f * t) for t in t_q]
    worst = max(abs(complex(g).real - t) for g, t in zip(got, truth))
    assert worst < 2e-2, f"sinc bandlimited tone recovery drifted by {worst}"


def test_sinc_interp_scalar_target():
    """A scalar target returns a single complex value (not a list)."""
    t_s = [float(i) for i in range(6)]
    y = [float(i) for i in range(6)]
    v = sinc_interp.op(y, t_s, 2.0)
    assert isinstance(v, complex)
    assert abs(v - complex(2.0)) < 1e-9  # target == a sample -> exact recover


@pytest.mark.parametrize("nq", [1, 3, 7])
def test_sinc_interp_native_matches_pure(monkeypatch, nq):
    """The C-dispatched sinc_interp (mat_matvec) matches the forced-pure
    triple-loop cascade within-tol — NOT byte-identical."""
    n = 20
    t_s = [float(i) for i in range(n)]
    y = [math.sin(0.3 * t) for t in t_s]
    rng = random.Random(900 + nq)
    t_q = [rng.uniform(0.0, n - 1) for _ in range(nq)]
    disp = sinc_interp.op(y, t_s, t_q)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure matmul
    pure = sinc_interp.op(y, t_s, t_q)
    assert _reldiff(pure, disp) < 1e-9, f"sinc native!=pure nq={nq}"


# ======================================================================
# wavelet — value oracles + native == pure
# ======================================================================

@pytest.mark.parametrize("levels", [1, 2, 3, 4])
def test_wavelet_perfect_reconstruction(levels):
    """The orthonormal Haar synthesis inverts the analysis exactly (perfect
    reconstruction): inverse(forward(x)) == x for a power-of-two length."""
    n = 2 ** (levels + 1)
    x = _rand_real(n, seed=50 + levels)
    approx, details = wavelet.op(x, levels=levels)
    assert len(details) == levels
    recon = _haar_inverse(approx, details)
    assert len(recon) == n
    assert _reldiff(x, recon) < 1e-9, f"wavelet not perfect-reconstruction levels={levels}"


def test_wavelet_energy_preservation():
    """Parseval: the Haar transform is orthonormal, so total energy is conserved
    across the (approx + all detail) coefficients."""
    x = _rand_real(16, seed=7)
    approx, details = wavelet.op(x, levels=3)
    e_in = sum(v * v for v in x)
    e_out = sum(v * v for v in approx) + sum(v * v for d in details for v in d)
    assert abs(e_in - e_out) < 1e-9 * (e_in + 1.0), "wavelet energy not preserved"


def test_wavelet_rejects_non_haar_and_nested():
    with pytest.raises(NotImplementedError):
        wavelet.op([1.0, 2.0, 3.0, 4.0], wavelet="db2")
    with pytest.raises(ValueError):
        wavelet.op([[1.0, 2.0], [3.0, 4.0]])


@pytest.mark.parametrize("levels", [1, 2, 3])
@pytest.mark.parametrize("n", [16, 24, 32])
def test_wavelet_native_matches_pure(monkeypatch, levels, n):
    """The C-dispatched wavelet (banded matvec) matches the forced-pure matmul
    cascade within-tol — NOT byte-identical."""
    x = _rand_real(n, seed=600 + n + levels)
    a_d, det_d = wavelet.op(x, levels=levels)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure matmul
    a_p, det_p = wavelet.op(x, levels=levels)
    flat_d = list(a_d) + [v for d in det_d for v in d]
    flat_p = list(a_p) + [v for d in det_p for v in d]
    assert _reldiff(flat_p, flat_d) < 1e-9, f"wavelet native!=pure levels={levels} n={n}"


# ======================================================================
# spectral_subtraction — value oracles + native == pure
# ======================================================================

def test_spectral_subtraction_clean_signal_passthrough():
    """With a (near-)zero noise floor the subtraction leaves every bin's
    magnitude unchanged, so a clean signal passes through to round-off."""
    x = _rand_real(32, seed=11)
    y = spectral_subtraction.op(x, [0.0] * len(x), alpha=1.0, beta=0.0)
    assert isinstance(y, list) and len(y) == len(x)
    assert _reldiff(x, y) < 1e-6, "spectral_subtraction clean != passthrough"


def test_spectral_subtraction_reduces_a_noise_floor():
    """Subtracting the true broadband noise floor lowers total output energy
    versus the noisy observation (the denoising direction)."""
    n = 32
    clean = [2.0 * math.sin(2.0 * math.pi * 3.0 * k / n) for k in range(n)]
    rng = random.Random(5)
    noise = [rng.gauss(0.0, 1.0) for _ in range(n)]
    noisy = [clean[k] + noise[k] for k in range(n)]
    # true per-bin noise PSD
    npsd = [abs(sum(noise[j] * cmath.exp(-2j * math.pi * k * j / n)
                    for j in range(n))) ** 2 for k in range(n)]
    out = spectral_subtraction.op(noisy, npsd, alpha=1.0, beta=0.01)
    e_noisy = sum(v * v for v in noisy)
    e_out = sum(v * v for v in out)
    assert e_out < e_noisy, "spectral_subtraction did not reduce energy"


@pytest.mark.parametrize("n", [16, 31, 32])
def test_spectral_subtraction_native_matches_pure(monkeypatch, n):
    """The C-dispatched spectral_subtraction (FFT via srmech_fft_c128) matches
    the forced-pure cexp-cascade FFT within-tol — NOT byte-identical."""
    x = _rand_real(n, seed=300 + n)
    npsd = [0.2 + 0.05 * ((k * 3) % 4) for k in range(n)]
    disp = spectral_subtraction.op(x, npsd, alpha=1.0, beta=0.01)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure FFT cascade
    pure = spectral_subtraction.op(x, npsd, alpha=1.0, beta=0.01)
    assert _reldiff(pure, disp) < 1e-9, f"spectral_subtraction native!=pure n={n}"


# ======================================================================
# dispatch presence (informational — the value/parity oracles above are the
# real gate; these just record whether the native path was exercised)
# ======================================================================

def test_native_paths_available_report():
    """Not a hard gate: records which C paths back this batch
    (srmech_dense_matmul_complex for farrow/sinc/wavelet, srmech_fft_c128 for
    spectral_subtraction). When absent the pure path is the complete alternative
    and every test above still passes."""
    assert isinstance(_HAS_FFT, bool)
    assert isinstance(_HAS_MATMUL, bool)
