"""srmech.amsc.cascade.spectral_cascades — DFT / FFT + Kronecker as A-N cascades.

Per ``docs/srmech/notes/continuous_math_as_14_class_cascade.md``: the DFT, the
FFT and the Kronecker product are not numpy primitives, they are compositions
of the 14 A-N class operations. This module ships them as **pure-Python
(numpy-free)** cascades built on the rc34 substrate-native ``cexp``.

- :func:`dft` / :func:`idft` — the **discrete Fourier transform is the
  Antikythera epicycle-sum** (``[[user_stance_epicycle_via_gear_plus_pin]]``):
  ``X_k = Σ_n x_n · e^(∓2πi·(k·n mod N)/N)``. **Class I** (the cyclic index
  ``k·n mod N`` on ℤ/N) ∘ **Class N** (the twiddle cos/sin) ∘ **Class C** (the
  imaginary unit = 90° rotation) ∘ **Class M** (the bundle/superposition sum).
  A direct ``O(N²)`` transform — value-faithful to ``NumPy fft`` to
  round-off.
- :func:`fft` / :func:`ifft` — the **radix-2 Cooley–Tukey** butterfly: the SAME
  value as :func:`dft`, but ``O(N log N)`` when ``N`` is a power of two, by
  adding **Class J** (the radix ``N = 2·(N/2)`` factorization) + **Class K**
  (the butterfly recursion depth) on top of the DFT cascade. For non-power-of-2
  ``N`` it falls back to :func:`dft`, so it is a drop-in for ``NumPy fft``
  at ANY length.
- :func:`kron` — the Kronecker product ``(A⊗B)`` = **Class I** (the mixed-radix
  index ``i·p+k``) ∘ **Class M** (the element products).
"""
from __future__ import annotations

from typing import List, Sequence

from srmech.amsc.rational import cexp, pi_cascade_digits

from .exact_dft import _exact_transform

__all__ = ["dft", "idft", "fft", "ifft", "kron"]

# π as a float, drawn ONCE from the Class-N π-cascade (no math.pi anywhere in
# the call graph). 30 digits is far below the float64 floor.
_PI_FLOAT: "float | None" = None


def _pi() -> float:
    global _PI_FLOAT
    if _PI_FLOAT is None:
        decimal = pi_cascade_digits(30)
        int_part, _, frac_part = decimal.partition(".")
        _PI_FLOAT = int(int_part + frac_part) / (10 ** len(frac_part))
    return _PI_FLOAT


def _native_fft(samples: List[complex], inverse: bool) -> "List[complex] | None":
    """The rc139 native numeric FFT fast path (srmech_fft_c128) for the FLOAT
    branch of :func:`dft` / :func:`fft`, or ``None`` when the native lib is
    absent (caller runs the pure ``cexp`` cascade). NOT taken for the
    integer / Gaussian-integer power-of-two signals that :func:`_exact_transform`
    already handled bit-exactly upstream — this is only the continuous (float)
    substrate, where an FPU-tol numeric transform IS the value (radix-2 for a
    power-of-two length, Bluestein chirp-z for arbitrary / prime length)."""
    try:
        from srmech.amsc import _native
    except Exception:
        return None
    return _native.fft_c128_c(samples, inverse)


def dft(x: Sequence[complex], *, inverse: bool = False) -> List[complex]:
    """Discrete Fourier transform via the Antikythera epicycle-sum.

    ``X_k = Σ_n x_n · e^(∓2πi·(k·n mod N)/N)`` (``+`` and a ``1/N`` scale when
    ``inverse=True``). Pure-Python; substrate-native replacement for
    ``NumPy fft`` / ``ifft`` on a 1-D sequence. ``O(N²)``.

    For an all-integer / Gaussian-integer power-of-two signal this runs the
    **exact-until-rotation** cyclotomic-integer engine (``ℤ[ζ_N]`` integer math,
    one FPU lift — *don't use floats for bit-exact math*); float signals (already
    continuous) and non-power-of-two lengths run the float ``cexp`` path.
    """
    x = list(x)
    if len(x) == 0:
        return []
    exact = _exact_transform(x, inverse=inverse)
    if exact is not None:
        return exact
    samples = [complex(v) for v in x]
    native = _native_fft(samples, inverse)     # rc139 C fast path (float)
    if native is not None:
        return native
    n = len(samples)
    sign = 1.0 if inverse else -1.0
    two_pi = 2.0 * _pi()
    out: List[complex] = []
    for k in range(n):
        acc = 0j
        for idx in range(n):
            m = (k * idx) % n                       # Class I: cyclic index
            angle = sign * two_pi * m / n           # Class N twiddle angle
            acc += samples[idx] * cexp(angle)       # Class C rotation, Class M bundle
        out.append(acc / n if inverse else acc)
    return out


def idft(x: Sequence[complex]) -> List[complex]:
    """Inverse DFT — :func:`dft` with the conjugate twiddle and a ``1/N`` scale."""
    return dft(x, inverse=True)


def _is_power_of_two(n: int) -> bool:
    """True iff ``n`` is a positive power of two (1, 2, 4, 8, …) — the
    **Class J** radix test ``N = 2^k`` (``n & (n-1) == 0``)."""
    return n > 0 and (n & (n - 1)) == 0


def _radix2(samples: List[complex], sign: float) -> List[complex]:
    """Recursive radix-2 Cooley–Tukey on a power-of-two-length list
    (decimation-in-time; in-order input → in-order output). ``sign`` is
    ``-1.0`` forward / ``+1.0`` inverse; NO ``1/N`` normalisation here (the
    caller applies it once). **Class J** = the parity split ``N = 2·(N/2)``;
    **Class K** = the recursion depth; the twiddle = **Class N** ∘ **Class C**;
    the butterfly = **Class M** add ∘ **Class K** sign-flip subtract.
    """
    n = len(samples)
    if n == 1:
        return [samples[0]]
    even = _radix2(samples[0::2], sign)   # Class J: even-index sub-transform
    odd = _radix2(samples[1::2], sign)    # Class J: odd-index sub-transform
    two_pi = 2.0 * _pi()
    half = n // 2
    out: List[complex] = [0j] * n
    for k in range(half):
        # twiddle e^(∓2πi·k/N) = Class N (cos/sin) ∘ Class C (i-rotation)
        t = cexp(sign * two_pi * k / n) * odd[k]
        out[k] = even[k] + t              # Class M: butterfly bundle
        out[k + half] = even[k] - t       # Class K: pin-slot sign flip
    return out


def fft(x: Sequence[complex], *, inverse: bool = False) -> List[complex]:
    """Fast Fourier transform — the radix-2 Cooley–Tukey butterfly.

    Bit-for-bit the same MATHEMATICS as :func:`dft` (and value-faithful to
    ``NumPy fft`` / ``ifft`` to round-off), but ``O(N log N)`` when ``N``
    is a power of two, via the radix-2 split. For every other ``N`` this falls
    back to the direct ``O(N²)`` :func:`dft`, so :func:`fft` is a drop-in for
    ``NumPy fft`` at ANY length. The fast path adds **Class J** (the radix
    ``N = 2·(N/2)`` factorization) + **Class K** (the butterfly recursion
    depth) on top of the rc36 DFT cascade.

    An all-integer / Gaussian-integer power-of-two signal takes the
    **exact-until-rotation** cyclotomic-integer engine (``ℤ[ζ_N]`` integer math,
    one FPU lift), so ``fft`` and ``dft`` agree bit-for-bit on integer input.
    """
    x = list(x)
    n = len(x)
    if n == 0:
        return []
    exact = _exact_transform(x, inverse=inverse)
    if exact is not None:
        return exact
    samples = [complex(v) for v in x]
    native = _native_fft(samples, inverse)     # rc139 C fast path (float)
    if native is not None:
        return native
    if not _is_power_of_two(n):
        return dft(samples, inverse=inverse)  # full-coverage fallback (all N)
    sign = 1.0 if inverse else -1.0
    spectrum = _radix2(samples, sign)
    if inverse:
        return [c / n for c in spectrum]      # single 1/N normalisation
    return spectrum


def ifft(x: Sequence[complex]) -> List[complex]:
    """Inverse FFT — :func:`fft` with the conjugate twiddle and a ``1/N`` scale."""
    return fft(x, inverse=True)


def kron(a: Sequence[Sequence[complex]],
         b: Sequence[Sequence[complex]]) -> List[List[complex]]:
    """Kronecker product ``A ⊗ B`` of two 2-D matrices (lists of rows).

    ``(A⊗B)[i·p+k, j·q+l] = A[i,j]·B[k,l]`` — **Class I** (the mixed-radix row/
    column index) ∘ **Class M** (the element products). Pure-Python.
    """
    A = [list(row) for row in a]
    B = [list(row) for row in b]
    ma, na = len(A), (len(A[0]) if A else 0)
    mb, nb = len(B), (len(B[0]) if B else 0)
    out: List[List[complex]] = [[0 for _ in range(na * nb)] for _ in range(ma * mb)]
    for i in range(ma):
        for j in range(na):
            aij = A[i][j]
            for k in range(mb):
                for ell in range(nb):
                    out[i * mb + k][j * nb + ell] = aij * B[k][ell]  # Class M
    return out
