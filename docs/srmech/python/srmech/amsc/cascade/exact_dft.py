"""Exact discrete Fourier transform engine — integer arithmetic, one FPU lift.

The substrate-native answer to "don't use floats for bit-exact math": a DFT's
twiddle factors ``e^{-2πi·j/N}`` are *roots of unity* — algebraic integers in the
cyclotomic ring ``ℤ[ζ_N]``. So the DFT of an integer (or Gaussian-integer)
substrate signal is **exact integer arithmetic**: every spectral coefficient is
an exact ``ℤ[ζ_N]`` element (an integer vector in the cyclotomic power basis),
computed with **no floating-point at all**. Floats appear exactly **once**, at
the very end, in the FPU *lift* that rotates ``ℤ[ζ_N] → ℂ`` by evaluating
``ζ_N = e^{-2πi/N}`` — the projection from the discrete substrate to the
continuous observable (per ``[[user_stance_epicycle_via_gear_plus_pin]]``:
floats are for the FPU lift, not the math).

For a power-of-two ``N`` the cyclotomic polynomial is ``Φ_N(x) = x^{N/2} + 1``,
so ``ζ^{N/2} = -1`` and the ring collapses to the **negacyclic** integers
``ℤ[x]/(x^{N/2}+1)`` — a length-``N/2`` integer vector with the single reduction
rule ``ζ^j = -ζ^{j-N/2}`` for ``j ≥ N/2`` (a **Class K** pin-slot sign-flip, NOT
``abs``). The transform is then pure integer add/subtract: bit-for-bit
deterministic, platform-independent, and *more* faithful than a float FFT (which
accumulates rounding at every butterfly) because it rounds exactly once.

This module is the **internal engine** behind :mod:`srmech.amsc.cascade.spectral_cascades`
``dft`` / ``fft``: those public cascades route an all-integer / Gaussian-integer
power-of-two signal through :func:`_exact_transform` (exact-until-rotation), and
fall back to the float ``cexp`` path only for genuinely floating-point signals
(already in the continuous/observable domain) or non-power-of-two lengths. The
functions here are deliberately **private** (underscore-prefixed): exposing the
exact ``ℤ[ζ_N]`` spectrum as a public introspected callable belongs with its
native-C twin (so it lands ``c_dispatched``, not as ``python_only_irreducible``
debt) — that is the tracked follow-up. General-``N`` (non-power-of-two)
cyclotomic reduction is also a follow-up.

Class chain: **Class I** (cyclic index ``nk mod N``) ∘ **Class K** (the
``ζ^{N/2}=-1`` pin-slot sign-flip = cyclotomic reduction) ∘ **Class M** (the
integer bundle/accumulate) ∘ a final **Class C** rotation (the FPU lift).
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

# A spectrum lives in the cyclotomic ring as (real-part, imag-part) integer
# coefficient vectors of length h = N/2 in the basis {1, ζ, …, ζ^{h-1}}.
_ExactSpectrum = List[Tuple[List[int], List[int]]]


def _try_int_pairs(signal: Sequence) -> Optional[Tuple[List[int], List[int]]]:
    """Split ``signal`` into integer ``(real, imag)`` component lists, or ``None``.

    Returns ``None`` (caller falls back to the float path) if any element is
    non-integral. Accepts Python ``int`` / ``float`` / ``complex`` and numpy
    scalars uniformly via their ``.real`` / ``.imag`` attributes (an ``int`` has
    ``.real == self`` and ``.imag == 0``). Bit-exact math takes integers, not
    floats — the substrate signal must already live on the integer grid.
    """
    re: List[int] = []
    im: List[int] = []
    for v in signal:
        vr = v.real if hasattr(v, "real") else v
        vi = v.imag if hasattr(v, "imag") else 0
        try:
            ir = int(vr)
            ii = int(vi)
        except (TypeError, ValueError):
            return None
        if ir != vr or ii != vi:          # non-integral component → not exact-eligible
            return None
        re.append(ir)
        im.append(ii)
    return re, im


def _is_pow2(n: int) -> bool:
    """True iff ``n`` is a positive power of two (the Class-J radix test)."""
    return n >= 1 and (n & (n - 1)) == 0


def _exact_dft_core(re: List[int], im: List[int], *, inverse: bool = False) -> _ExactSpectrum:
    """The exact integer DFT: ``X[k] = Σ_n signal[n] · ζ^{±nk mod N}``.

    Pure integer add/subtract — no floats. ``ζ = e^{-2πi/N}``, ``ζ^{N/2} = -1``
    (the only "trig" is a sign flip, Class K). Forward uses ``ζ^{nk}``; inverse
    uses ``ζ^{-nk}`` (the caller applies the ``1/N`` scale at lift time, keeping
    this core integer). Returns ``N`` cyclotomic-integer coefficients, each a
    ``(real_vec, imag_vec)`` pair of length ``N/2``. Bit-for-bit deterministic.
    """
    n = len(re)
    h = n // 2
    spectrum: _ExactSpectrum = []
    for k in range(n):
        xr = [0] * h
        xi = [0] * h
        for idx in range(n):
            j = ((idx * k) % n) if not inverse else ((-idx * k) % n)
            sign = 1
            if j >= h:                    # Class K: ζ^{N/2} = -1 → ζ^j = -ζ^{j-h}
                j -= h
                sign = -1
            xr[j] += sign * re[idx]
            xi[j] += sign * im[idx]
        spectrum.append((xr, xi))
    return spectrum


def _lift_spectrum(spectrum: _ExactSpectrum, n: int, *, scale: int = 1) -> List[complex]:
    """The single FPU lift: rotate ``ℤ[ζ_N] → ℂ`` at ``ζ_N = e^{-2πi/N}``.

    The *only* place a float is produced — the projection from the exact discrete
    substrate to the continuous observable. ``scale`` divides the result (use
    ``scale=N`` for a normalised inverse). The root-of-unity table reuses the
    Class-N substrate-native ``cexp`` (same twiddle the float ``dft`` uses), so
    the lift is consistent with the legacy path. Imported lazily so the exact
    core above carries no float dependency (numpy-absent-safe; ``cexp`` /
    ``pi_cascade_digits`` are pure-Python Class-N, no numpy).
    """
    from srmech.amsc.rational import cexp, pi_cascade_digits

    h = n // 2
    two_pi = 2.0 * float(pi_cascade_digits(40))
    roots = [cexp(-two_pi * j / n) for j in range(h)]  # e^{-2πi·j/N}
    out: List[complex] = []
    for (xr, xi) in spectrum:
        acc = 0j
        for j in range(h):
            acc += complex(xr[j], xi[j]) * roots[j]
        out.append(acc / scale if scale != 1 else acc)
    return out


def _exact_transform(signal: Sequence, *, inverse: bool = False) -> Optional[List[complex]]:
    """Exact-until-rotation DFT/iDFT of ``signal``, or ``None`` if ineligible.

    Returns the lifted ``List[complex]`` (exact integer spectrum + one FPU lift)
    when ``signal`` is an all-integer / Gaussian-integer power-of-two sequence of
    length ``N ≥ 2``; otherwise ``None`` (caller runs the float ``cexp`` path).
    ``inverse=True`` applies the ``1/N`` normalisation at lift time.
    """
    pairs = _try_int_pairs(signal)
    if pairs is None:
        return None
    re, im = pairs
    n = len(re)
    if n < 2 or not _is_pow2(n):          # N=1 has no cyclotomic basis; non-pow2 is a follow-up
        return None
    spectrum = _exact_dft_core(re, im, inverse=inverse)
    return _lift_spectrum(spectrum, n, scale=(n if inverse else 1))
