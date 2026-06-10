"""Path A OFDM — closed-form orthogonal frequency-division multiplexing.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational civilian-comms textbook reference only (WiFi-class baseband OFDM).

Identity per the implementation plan §1: OFDM IS a Class I (IFFT for the
modulation; cyclic group of subcarrier frequencies) ∘ Class L (per-subcarrier
eigenvalue handle ``g(lambda_k)`` for the equaliser) ∘ Class K (cyclic-prefix
guard interval as a Class K time-domain projection) decomposition.

Path B dual in Phase 6 (Path B IFFT/FFT with subcarrier bundle).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Bingham
(1990) + Cimini (1985) + Proakis & Salehi (2008, 5th ed.) §11.5.
"""

from __future__ import annotations

import numpy as np

from srmech.amsc.laplacian import elementwise_hypot
from srmech.amsc.cascade import spectral_cascades as _sc

OPERATION_NAME = "ofdm"
CLASS_COMPOSITION = ("I", "L", "K")
PERFORMANCE_HINT = "shallow-cascade-subcarrier-amortise"
SSOT_CITATION = (
    "Bingham (1990), 'Multicarrier modulation for data transmission: An "
    "idea whose time has come', IEEE Commun. Mag. 28(5), 5-14. DOI 10.1109/"
    "35.54342 (Crossref). Cimini (1985), 'Analysis and simulation of a "
    "digital mobile channel using orthogonal frequency division multiplexing'"
    ", IEEE Trans. Commun. 33(7), 665-675. Proakis & Salehi (2008, 5th ed.),"
    " 'Digital Communications', McGraw-Hill, §11.5."
)


def op(
    symbols,
    *,
    n_subcarriers: int = 64,
    cp_length: int = 16,
    demodulate: bool = False,
    channel: np.ndarray = None,
    D: int = 8192,
):
    """OFDM modulate complex subcarrier symbols or demodulate baseband OFDM samples.

    Parameters
    ----------
    symbols:
        Modulate: complex array of length ``n_symbols * n_subcarriers``
        (sequential subcarrier values per OFDM symbol).
        Demodulate: complex baseband sample stream.
    n_subcarriers:
        Number of subcarriers (FFT size).
    cp_length:
        Cyclic-prefix length (samples).
    demodulate:
        If True, return demodulated subcarrier symbols.
    channel:
        Optional frequency-domain channel response of length n_subcarriers
        for equalisation (Class L eigenvalue handles).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    Modulate: complex baseband sample stream.
    Demodulate: ``(n_symbols, n_subcarriers)`` complex subcarrier matrix.
    """
    n = n_subcarriers
    if demodulate:
        rx = np.asarray(symbols, dtype=np.complex128)
        samples_per_ofdm = n + cp_length
        n_symbols = rx.shape[0] // samples_per_ofdm
        out = np.zeros((n_symbols, n), dtype=np.complex128)
        for i in range(n_symbols):
            start = i * samples_per_ofdm + cp_length  # skip CP
            frame = rx[start : start + n]
            X = np.asarray(_sc.fft(frame))
            if channel is not None:
                # Class L equaliser: one-tap per subcarrier divide by H_k.
                # |z| = hypot(real,imag) (no abs())
                X = X / np.where(elementwise_hypot(channel.real, channel.imag) > 1e-12, channel, 1.0)
            out[i] = X
        return out

    syms = np.asarray(symbols, dtype=np.complex128)
    if syms.shape[0] % n != 0:
        raise ValueError(
            f"symbols length {syms.shape[0]} not multiple of n_subcarriers {n}"
        )
    n_symbols = syms.shape[0] // n
    out = np.zeros(n_symbols * (n + cp_length), dtype=np.complex128)
    for i in range(n_symbols):
        block = syms[i * n : (i + 1) * n]
        # Class I IFFT
        time_block = np.asarray(_sc.ifft(block))
        # Class K cyclic-prefix (Class K guard-interval projection)
        prefix = time_block[-cp_length:] if cp_length > 0 else np.array([], dtype=time_block.dtype)
        out[
            i * (n + cp_length) : (i + 1) * (n + cp_length)
        ] = np.concatenate([prefix, time_block])
    return out
