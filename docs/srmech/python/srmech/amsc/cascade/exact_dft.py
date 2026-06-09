"""Exact discrete Fourier transform — integer arithmetic, one FPU lift.

The substrate-native answer to "don't use floats for bit-exact math": a DFT's
twiddle factors ``e^{-2πi·j/N}`` are *roots of unity* — algebraic integers in the
cyclotomic ring ``ℤ[ζ_N]``. So the DFT of an integer (or Gaussian-integer)
substrate signal is **exact integer arithmetic**: every spectral coefficient is
an exact ``ℤ[ζ_N]`` element (an integer vector in the cyclotomic power basis),
computed with **no floating-point at all**. Floats appear exactly **once**, at
the very end, in the FPU *lift* (:func:`lift`) that rotates ``ℤ[ζ_N] → ℂ`` by
evaluating ``ζ_N = e^{-2πi/N}`` — the projection from the discrete substrate to
the continuous observable (per ``[[user_stance_epicycle_via_gear_plus_pin]]``:
floats are for the FPU lift, not the math).

For a power-of-two ``N`` the cyclotomic polynomial is ``Φ_N(x) = x^{N/2} + 1``,
so ``ζ^{N/2} = -1`` and the ring collapses to the **negacyclic** integers
``ℤ[x]/(x^{N/2}+1)`` — a length-``N/2`` integer vector with the single reduction
rule ``ζ^j = -ζ^{j-N/2}`` for ``j ≥ N/2`` (a **Class K** pin-slot sign-flip, NOT
``abs``). The transform is then pure integer add/subtract: bit-for-bit
deterministic, platform-independent, and *more* faithful than a float FFT (which
accumulates rounding at every butterfly) because it rounds exactly once.

Public surface (v0.7.5rc29):

- :func:`exact_dft` / :func:`exact_idft` — return the **exact** ``ℤ[ζ_N]``
  integer spectrum (an :data:`ExactSpectrum`: one ``(real_vec, imag_vec)``
  integer pair per output bin) of a power-of-two integer / Gaussian-integer
  signal. No floats. The native-C twin ``srmech_exact_dft_i64`` runs the int64
  fast path; arbitrary-precision magnitudes fall back to the Python bignum path.
- :func:`lift` — the single FPU lift ``ℤ[ζ_N] → ℂ`` (the *only* float producer).

The public ops are also the **internal engine** behind
:mod:`srmech.amsc.cascade.spectral_cascades` ``dft`` / ``fft``, which route an
all-integer power-of-two signal through :func:`_exact_transform`
(exact-until-rotation) and keep the float ``cexp`` path only for genuinely
floating-point signals or non-power-of-two lengths. General-``N``
(non-power-of-two) cyclotomic reduction is a follow-up; until then
:func:`exact_dft` raises on non-power-of-two and ``dft`` / ``fft`` keep the float
fallback there.

Class chain: **Class I** (cyclic index ``nk mod N``) ∘ **Class K** (the
``ζ^{N/2}=-1`` pin-slot sign-flip = cyclotomic reduction) ∘ **Class M** (the
integer bundle/accumulate) ∘ a final **Class C** rotation (the FPU lift).
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

__all__ = ["exact_dft", "exact_idft", "lift", "ExactSpectrum"]

# A spectrum lives in the cyclotomic ring as (real-part, imag-part) integer
# coefficient vectors of length h = N/2 in the basis {1, ζ, …, ζ^{h-1}}.
ExactSpectrum = List[Tuple[List[int], List[int]]]

# Headroom under int64 (2^63): the largest exact coefficient is bounded by
# N·max|signal|, so we dispatch to the C int64 twin only when that bound is
# comfortably inside int64; larger magnitudes take the Python bignum path.
_INT64_SAFE = 1 << 62


def _try_int_pairs(signal: Sequence) -> Optional[Tuple[List[int], List[int]]]:
    """Split ``signal`` into integer ``(real, imag)`` component lists, or ``None``.

    Returns ``None`` if any element is non-integral. Accepts Python ``int`` /
    ``float`` / ``complex`` and numpy scalars uniformly via their ``.real`` /
    ``.imag`` attributes (an ``int`` has ``.real == self`` and ``.imag == 0``).
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


def _exact_dft_core_native(re: List[int], im: List[int], n: int,
                           inverse: bool) -> Optional[ExactSpectrum]:
    """Native-C int64 fast path for :func:`_exact_dft_core`, or ``None``.

    Returns ``None`` (caller runs the Python bignum path) when the native lib is
    absent / lacks the symbol, or when the exact coefficients could exceed the
    int64-safe bound ``N·max|signal|`` (arbitrary precision is then load-bearing).
    Magnitude is a Class-K sign-branch read, never ``abs``.
    """
    try:
        from srmech.amsc import _native
    except Exception:
        return None
    if not getattr(_native, "HAS_NATIVE", False):
        return None
    lib = getattr(_native, "LIB", None)
    if lib is None or not hasattr(lib, "srmech_exact_dft_i64"):
        return None
    maxabs = 0
    for v in re:
        a = v if v >= 0 else -v
        if a > maxabs:
            maxabs = a
    for v in im:
        a = v if v >= 0 else -v
        if a > maxabs:
            maxabs = a
    if maxabs * n >= _INT64_SAFE:         # coefficient magnitude could overflow int64
        return None
    import ctypes

    h = n // 2
    total = n * h
    c_re = (ctypes.c_int64 * n)(*re)
    c_im = (ctypes.c_int64 * n)(*im)
    out_re = (ctypes.c_int64 * total)()
    out_im = (ctypes.c_int64 * total)()
    rc = lib.srmech_exact_dft_i64(
        ctypes.c_uint32(n),
        ctypes.c_int(1 if inverse else 0),
        c_re, c_im, out_re, out_im,
    )
    if rc != 0:
        return None
    spectrum: ExactSpectrum = []
    for k in range(n):
        base = k * h
        spectrum.append(([int(out_re[base + j]) for j in range(h)],
                         [int(out_im[base + j]) for j in range(h)]))
    return spectrum


def _exact_dft_core(re: List[int], im: List[int], *, inverse: bool = False) -> ExactSpectrum:
    """The exact integer DFT: ``X[k] = Σ_n signal[n] · ζ^{±nk mod N}``.

    Pure integer add/subtract — no floats. ``ζ = e^{-2πi/N}``, ``ζ^{N/2} = -1``
    (the only "trig" is a sign flip, Class K). Dispatches to the native-C int64
    twin when available and int64-safe, else runs the arbitrary-precision Python
    bignum loop. Returns ``N`` cyclotomic-integer coefficients, each a
    ``(real_vec, imag_vec)`` pair of length ``N/2``. Bit-for-bit deterministic.
    """
    n = len(re)
    native = _exact_dft_core_native(re, im, n, inverse)
    if native is not None:
        return native
    h = n // 2
    spectrum: ExactSpectrum = []
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


def _lift_spectrum(spectrum: ExactSpectrum, n: int, *, scale: int = 1) -> List[complex]:
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


def exact_dft(signal: Sequence, *, inverse: bool = False) -> ExactSpectrum:
    """Exact ``ℤ[ζ_N]`` integer spectrum of an integer / Gaussian-integer signal.

    ``signal`` must be an all-integer (or Gaussian-integer) sequence of
    **power-of-two** length ``N ≥ 2``. Returns the spectrum as ``N``
    cyclotomic-integer coefficients (an :data:`ExactSpectrum`), each a
    ``(real_vec, imag_vec)`` integer pair of length ``N/2`` — **no floats**.
    ``inverse=True`` uses ``ζ^{-nk}`` (apply the ``1/N`` scale at :func:`lift`
    time). Bit-for-bit deterministic; rides the native-C int64 twin when present.

    Raises ``ValueError`` for non-integral input (use
    :func:`~srmech.amsc.cascade.spectral_cascades.dft` for float signals) or
    non-power-of-two length (general-``N`` is a follow-up).
    """
    pairs = _try_int_pairs(signal)
    if pairs is None:
        raise ValueError(
            "exact_dft: integer / Gaussian-integer signal required (bit-exact "
            "math takes ints, not floats); use dft() for floating-point signals."
        )
    re, im = pairs
    n = len(re)
    if n < 2 or not _is_pow2(n):
        raise ValueError(
            f"exact_dft: power-of-two length >= 2 required (cyclotomic Φ_N = "
            f"x^(N/2)+1); got N={n}. General-N is a follow-up; use dft()."
        )
    return _exact_dft_core(re, im, inverse=inverse)


def exact_idft(signal: Sequence) -> ExactSpectrum:
    """Inverse exact DFT — :func:`exact_dft` with the conjugate twiddle ``ζ^{-nk}``.

    Unnormalised: the ``1/N`` scale is a Class-N rational applied at :func:`lift`
    time (``lift(exact_idft(x), scale=N)``), keeping this core integer.
    """
    return exact_dft(signal, inverse=True)


def lift(spectrum: ExactSpectrum, *, scale: int = 1) -> List[complex]:
    """The single FPU lift: rotate an exact ``ℤ[ζ_N]`` spectrum to ``ℂ``.

    This is the **only** place a float is produced — the projection from the
    exact discrete substrate (:func:`exact_dft`) to the continuous observable, at
    ``ζ_N = e^{-2πi/N}``. ``scale`` divides the result (use ``scale=N`` for a
    normalised inverse). Pure-Python / numpy-absent-safe.
    """
    return _lift_spectrum(spectrum, len(spectrum), scale=scale)


def _exact_transform(signal: Sequence, *, inverse: bool = False) -> Optional[List[complex]]:
    """Exact-until-rotation DFT/iDFT of ``signal``, or ``None`` if ineligible.

    The routing helper behind ``dft`` / ``fft``: returns the lifted
    ``List[complex]`` (exact integer spectrum + one FPU lift) when ``signal`` is
    an all-integer / Gaussian-integer power-of-two sequence of length ``N ≥ 2``;
    otherwise ``None`` (caller runs the float ``cexp`` path). ``inverse=True``
    applies the ``1/N`` normalisation at lift time.
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
