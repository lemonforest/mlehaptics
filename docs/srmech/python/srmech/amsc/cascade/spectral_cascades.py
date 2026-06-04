"""srmech.amsc.cascade.spectral_cascades — DFT + Kronecker as A-N cascades.

Per ``docs/srmech/notes/continuous_math_as_14_class_cascade.md``: the DFT and
the Kronecker product are not numpy primitives, they are compositions of the
14 A-N class operations. This module ships them as **pure-Python (numpy-free)**
cascades built on the rc34 substrate-native ``cexp``.

- :func:`dft` / :func:`idft` — the **discrete Fourier transform is the
  Antikythera epicycle-sum** (``[[user_stance_epicycle_via_gear_plus_pin]]``):
  ``X_k = Σ_n x_n · e^(∓2πi·(k·n mod N)/N)``. **Class I** (the cyclic index
  ``k·n mod N`` on ℤ/N) ∘ **Class N** (the twiddle cos/sin) ∘ **Class C** (the
  imaginary unit = 90° rotation) ∘ **Class M** (the bundle/superposition sum).
  A direct ``O(N²)`` transform — value-faithful to ``numpy.fft.fft`` to
  round-off; the radix-2 ``O(N log N)`` butterfly (adds **Class J** radix
  factorization + **Class K** recursion depth) is the follow-on.
- :func:`kron` — the Kronecker product ``(A⊗B)`` = **Class I** (the mixed-radix
  index ``i·p+k``) ∘ **Class M** (the element products).
"""
from __future__ import annotations

from typing import List, Sequence

from srmech.amsc.rational import cexp, pi_cascade_digits

__all__ = ["dft", "idft", "kron"]

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


def dft(x: Sequence[complex], *, inverse: bool = False) -> List[complex]:
    """Discrete Fourier transform via the Antikythera epicycle-sum.

    ``X_k = Σ_n x_n · e^(∓2πi·(k·n mod N)/N)`` (``+`` and a ``1/N`` scale when
    ``inverse=True``). Pure-Python; substrate-native replacement for
    ``numpy.fft.fft`` / ``ifft`` on a 1-D sequence. ``O(N²)``.
    """
    samples = [complex(v) for v in x]
    n = len(samples)
    if n == 0:
        return []
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
