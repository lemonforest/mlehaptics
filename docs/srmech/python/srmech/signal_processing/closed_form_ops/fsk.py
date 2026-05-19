"""Path A FSK — closed-form frequency-shift-keying modulator / demodulator.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational civilian-comms textbook reference only.

Identity per the implementation plan §1: FSK IS a Class N (rational
frequency choices ``f_k = f_0 + k*delta_f``) ∘ Class I (cyclic time-base ℤ/N
for the symbol-period quantisation) composition.

The closed-form reference synthesises a complex baseband FSK waveform
with rational frequency-ratio shifts.

Path B dual in Phase 6 (Path B Class N rational frequency).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Proakis &
Salehi (2008, 5th ed.) *Digital Communications* §4.5 (FSK).
"""

from __future__ import annotations

import numpy as np

OPERATION_NAME = "fsk"
CLASS_COMPOSITION = ("N", "I")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Proakis & Salehi (2008, 5th ed.), 'Digital Communications', McGraw-Hill, "
    "§4.5 (FSK modulation). Educational civilian-comms textbook reference."
)


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
    Modulate: complex baseband waveform of length ``len(symbols) *
    samples_per_symbol``.
    Demodulate: integer symbol-index array of length ``len(samples) /
    samples_per_symbol``.
    """
    freqs = np.asarray(frequencies, dtype=np.float64)
    M = freqs.shape[0]
    n = samples_per_symbol
    t = np.arange(n) / fs

    if demodulate:
        signal = np.asarray(symbols, dtype=np.complex128)
        n_syms = signal.shape[0] // n
        out = np.zeros(n_syms, dtype=np.int64)
        # Class I: correlator bank over the M tones.
        tones = np.array(
            [np.exp(1j * 2.0 * np.pi * fk * t) for fk in freqs],
            dtype=np.complex128,
        )
        for i in range(n_syms):
            window = signal[i * n : (i + 1) * n]
            corrs = np.abs(tones @ np.conj(window))
            out[i] = np.argmax(corrs)
        return out

    syms = np.asarray(symbols, dtype=np.int64)
    if np.any(syms < 0) or np.any(syms >= M):
        raise ValueError(f"symbols must be in [0, {M})")
    out = np.zeros(syms.shape[0] * n, dtype=np.complex128)
    for i, s in enumerate(syms):
        out[i * n : (i + 1) * n] = np.exp(1j * 2.0 * np.pi * freqs[s] * t)
    return out
