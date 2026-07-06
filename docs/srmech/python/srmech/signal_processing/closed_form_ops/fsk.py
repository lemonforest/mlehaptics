"""Path A FSK — closed-form frequency-shift-keying modulator / demodulator.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational civilian-comms textbook reference only.

Identity per the implementation plan §1: FSK IS a Class N (rational
frequency choices ``f_k = f_0 + k*delta_f``) ∘ Class I (cyclic time-base ℤ/N
for the symbol-period quantisation) composition.

The closed-form reference synthesises a complex baseband FSK waveform
with rational frequency-ratio shifts.

Carrier-removal #564 (rc103): numpy-FREE — the per-symbol tone phases
``e^{i·2π·f·t}`` route through the Class-N ``rational.cos`` / ``rational.sin``
cascade over the substrate-native ``_PI`` source (``_exp_i``, native
libm-free), and the demodulator correlator bank's nearest-tone decision is
``argmax|corr|²`` (monotone in ``|corr|``, so no ``sqrt`` and no ``abs()``).
No top-level ``import numpy``.

rc153 (BATCH B7) classification: ``composition_of_c``. Modulate is the
C-backed ``rational.cos`` / ``rational.sin`` tone cascade. Demodulate's
correlator-bank inner product ``corr_k = Σ_j tones[k][j]·conj(window[j])`` IS
the matvec ``corr = Tones · conj(window)`` — routed through the c_dispatched
``laplacian.mat_matvec`` ∘ ``mat_matmul`` (``srmech_dense_matmul_complex``)
when the native lib is present, else its numpy-free pure fallback. NUMERIC
within-tol (native == pure to reldiff ≤ 1e-9, NOT byte-identical).

Path B dual in Phase 6 (Path B Class N rational frequency).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Proakis &
Salehi (2008, 5th ed.) *Digital Communications* §4.5 (FSK).
"""

from __future__ import annotations

from typing import List

from srmech.amsc import rational as _srn

OPERATION_NAME = "fsk"
CLASS_COMPOSITION = ("N", "I")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Proakis & Salehi (2008, 5th ed.), 'Digital Communications', McGraw-Hill, "
    "§4.5 (FSK modulation). Educational civilian-comms textbook reference."
)

# Class-N π cascade (Archimedes hexagon-doubling, Spike #32) — the substrate-
# native π source for the FSK tone phases; NOT math.pi / np.pi.
_PI = float(_srn.pi_cascade_digits(30))


def _exp_i(theta: float) -> complex:
    """``e^{iθ} = cos θ + i·sin θ`` via the Class-N rational trig cascade.

    Bit-faithful to the prior ``elementwise_transcendental(·, 'exp_i')`` path
    (both run the same native libm-free ``rational.cos`` / ``rational.sin``
    range-reduced cascade); numpy-free.
    """
    return complex(_srn.cos(theta), _srn.sin(theta))


def _as_list(v) -> list:
    """Coerce an array-like to a plain Python list (numpy-free)."""
    return v.tolist() if hasattr(v, "tolist") else list(v)


def op(
    symbols,
    *,
    frequencies,
    samples_per_symbol: int = 16,
    fs: float = 1.0,
    demodulate: bool = False,
    D: int = 8192,
):
    """FSK modulate symbol indices or demodulate baseband samples.

    Parameters
    ----------
    symbols:
        Modulate: array of integer symbol indices in ``[0, M)``.
        Demodulate: complex baseband sample array.
    frequencies:
        Sequence of M frequencies (Hz, Class N rational over fs).
    samples_per_symbol:
        Number of samples per symbol period.
    fs:
        Sample rate (Hz).
    demodulate:
        If True, return nearest-frequency symbol indices via correlator bank.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    Modulate: ``list`` of complex baseband samples of length ``len(symbols) *
    samples_per_symbol``.
    Demodulate: ``list`` of integer symbol indices of length ``len(samples) /
    samples_per_symbol``.
    """
    freqs = [float(f) for f in _as_list(frequencies)]
    M = len(freqs)
    n = int(samples_per_symbol)
    t = [k / fs for k in range(n)]

    if demodulate:
        # composition_of_c (rc153 / B7): the correlator-bank inner product
        # corr_k = Σ_j tones[k][j]·conj(window[j]) IS the matvec
        # ``corr = Tones · conj(window)`` (M×n complex matrix times a length-n
        # vector) — route the accumulation through the c_dispatched
        # laplacian.mat_matvec ∘ mat_matmul (srmech_dense_matmul_complex) when the
        # native lib is present, else its numpy-free pure triple-loop fallback.
        # The tone matrix rows are the byte-exact Class-N rational.cos/sin cascade
        # (C-backed via _exp_i). Class-C conj is a carrier transform on the window
        # (NOT an abs()); the argmax is a Class-K decision. NUMERIC within-tol
        # (native == pure to reldiff ≤ 1e-9 — the complex matmul may FMA-fuse
        # ~1 ULP, so NOT byte-identical).
        from srmech.amsc.laplacian import mat_matvec  # lazy: avoid import cycle

        signal = [complex(z) for z in _as_list(symbols)]
        n_syms = len(signal) // n
        # Class I: correlator bank over the M tones (M × n) — the tone matrix.
        tones = [[_exp_i(2.0 * _PI * fk * tk) for tk in t] for fk in freqs]
        out: List[int] = []
        for i in range(n_syms):
            window = signal[i * n : (i + 1) * n]
            # Class-C conjugate carrier transform on the window (no abs()).
            conj_window = [w.conjugate() for w in window]
            corr = list(mat_matvec(tones, conj_window))
            # Class-K decision: argmax|corr_k|² (monotone in |corr|, so no sqrt /
            # no abs()); strict > keeps the first-maximum index.
            best_k = 0
            best_mag2 = -1.0
            for k in range(M):
                ck = corr[k]
                mag2 = ck.real * ck.real + ck.imag * ck.imag
                if mag2 > best_mag2:
                    best_mag2 = mag2
                    best_k = k
            out.append(best_k)
        return out

    syms = [int(s) for s in _as_list(symbols)]
    for s in syms:
        if s < 0 or s >= M:
            raise ValueError(f"symbols must be in [0, {M})")
    out_c: List[complex] = []
    for s in syms:
        fk = freqs[s]
        out_c.extend(_exp_i(2.0 * _PI * fk * tk) for tk in t)
    return out_c
