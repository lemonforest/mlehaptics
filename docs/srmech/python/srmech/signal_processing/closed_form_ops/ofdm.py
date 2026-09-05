"""Path A OFDM — closed-form orthogonal frequency-division multiplexing.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational civilian-comms textbook reference only (WiFi-class baseband OFDM).

Identity per the implementation plan §1: OFDM IS a Class I (IFFT for the
modulation; cyclic group of subcarrier frequencies) ∘ Class L (per-subcarrier
eigenvalue handle ``g(lambda_k)`` for the equaliser) ∘ Class K (cyclic-prefix
guard interval as a Class K time-domain projection) decomposition.

Path B dual in Phase 6 (Path B IFFT/FFT with subcarrier bundle).

Carrier-free since v0.7.5rc84 (#564): plain Python ``list`` / ``list``-of-
``list`` carriers; ``_sc.fft`` / ``_sc.ifft`` already return ``List[complex]``;
the per-subcarrier ``|H_k|`` equaliser guard uses the numpy-free Class-N
``rational.hypot`` and an explicit Class-K pin-slot sign-branch (no ``abs()``).

rc153 (BATCH B7) classification: ``composition_of_c``. Modulate's IFFT and
demodulate's FFT funnel through ``spectral_cascades.ifft`` / ``.fft`` → the
c_dispatched numeric FFT foundation ``srmech_fft_c128`` (rc139); the
per-subcarrier equaliser ``|H_k|`` rides the composition_of_c ``rational.hypot``
and the cyclic-prefix / one-tap divide are numpy-free elementwise / integer
glue. NUMERIC within-tol (native == pure to reldiff ≤ 1e-9, NOT byte-identical).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Bingham
(1990) + Cimini (1985) + Proakis & Salehi (2008, 5th ed.) §11.5.
"""

from __future__ import annotations

from srmech.math.rational import hypot as _rhypot
from srmech.cascade import spectral_cascades as _sc

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
    channel=None,
    D: int = 8192,
):
    """OFDM modulate complex subcarrier symbols or demodulate baseband OFDM samples.

    Parameters
    ----------
    symbols:
        Modulate: complex sequence of length ``n_symbols * n_subcarriers``
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
    Modulate: complex baseband sample stream as a ``list``.
    Demodulate: ``(n_symbols, n_subcarriers)`` complex subcarrier matrix as a
    ``list`` of ``list`` (rows are subcarrier values per OFDM symbol).

    Accuracy (rc466, `#T1188`)
    --------------------------
    ``symbols`` are used AS GIVEN (through rc465 ``[complex(v) for v in
    symbols]`` rounded an exact symbol stream before the transform). An
    integer / Gaussian-integer block rides the cascade's exact-until-rotation
    IFFT / FFT (:func:`srmech.cascade.spectral_cascades.ifft`, with the ``1/N``
    scale applied at the lift) and the cyclic-prefix copy is exact glue, so
    each returned ``complex`` sample is the engine's single **terminal float
    lift** — exact wherever float-representable, **accurate to round-off**
    (~1 ULP) otherwise. A float stream is transformed on the float64 carrier,
    **accurate to round-off**. The ``channel=`` equaliser on the demodulate
    path is a per-subcarrier float64 divide of the lifted bins (the Class-N
    ``hypot`` guard at ``1e-12``), **accurate to round-off** — never exact.
    """
    n = n_subcarriers
    if demodulate:
        rx = list(symbols)
        samples_per_ofdm = n + cp_length
        n_symbols = len(rx) // samples_per_ofdm
        out = []
        ch = list(channel) if channel is not None else None
        for i in range(n_symbols):
            start = i * samples_per_ofdm + cp_length  # skip CP
            frame = rx[start : start + n]
            X = list(_sc.fft(frame))
            if ch is not None:
                # Class L equaliser: one-tap per subcarrier divide by H_k.
                # |H_k| = hypot(real, imag) (Class N sqrt cascade, no abs()).
                # Class K pin-slot: the > 1e-12 guard is the phase-boundary;
                # the conditional divisor select is the Class C reorientation.
                X = [
                    X[k]
                    / (ch[k] if _rhypot(ch[k].real, ch[k].imag) > 1e-12 else complex(1.0))
                    for k in range(n)
                ]
            out.append(X)
        return out

    syms = list(symbols)
    if len(syms) % n != 0:
        raise ValueError(
            f"symbols length {len(syms)} not multiple of n_subcarriers {n}"
        )
    n_symbols = len(syms) // n
    out = [0] * (n_symbols * (n + cp_length))   # rc466: the exact zero pad
    for i in range(n_symbols):
        block = syms[i * n : (i + 1) * n]
        # Class I IFFT
        time_block = list(_sc.ifft(block))
        # Class K cyclic-prefix (Class K guard-interval projection)
        prefix = time_block[-cp_length:] if cp_length > 0 else []
        frame = prefix + time_block
        start = i * (n + cp_length)
        out[start : start + (n + cp_length)] = frame
    return out
