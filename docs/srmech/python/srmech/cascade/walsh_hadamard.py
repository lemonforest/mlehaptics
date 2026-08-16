"""Walsh–Hadamard transform on the boolean cube **(ℤ/2)ⁿ** — Class L ∘ Class I.

rc437 (`#T1142`). srmech has had an exact spectrum since rc29, and it is the
**wrong group** for a large family of questions.

**What already shipped.** :func:`~srmech.cascade.exact_dft.exact_dft` returns a
genuinely exact ``ℤ[ζ_N]`` spectrum — MEASURED, not asserted: at ``N = 8`` the
basis degree is φ(8) = 4, at ``N = 12`` it is φ(12) = 4, at ``N = 7`` it is
φ(7) = 6, and no float appears anywhere in the answer. So the framing "an exact
spectrum needs a degree-φ(N) extension that has to be actually implemented" is
**not a gap in this package**; that work is done.

**What did not.** ``exact_dft`` covers the **cyclic** group ℤ/N. Nothing covered
the **cube** (ℤ/2)ⁿ. Verified by execution at rc436 — ``walsh``, ``hadamard``,
``wht``, ``fwht``, ``sylvester``, ``paley``, ``sign_transform``, ``cube_spectrum``
and ``parity_transform`` scored **zero hits** across every public callable in
the package. The only "Hadamard" in the tree is the elementwise product (which
is a different thing wearing the same name) and the Hadamard *bound* in
``modular_linalg`` / ``qmat`` (a determinant envelope, a different thing again).

**Why the cube is the cheaper object, not the more expensive one.** The whole
reason ``exact_dft`` needs a ring extension is that the characters of ℤ/N are
Nth roots of unity. The characters of (ℤ/2)ⁿ are

    χ_k(j) = (−1)^{popcount(j & k)}

which take the values **+1 and −1 and nothing else**. So this transform is exact
in *whole numbers*: no roots of unity, no cyclotomic field, no extension ring,
no vector-valued coefficient. Add, subtract, and a Class-K sign-flip. For a
float-free package that is not a convenience — it is the reason the op belongs
here at all.

**Why the butterfly and not the dense matrix.** ``kron(kron(H2, H2), H2)``
composes today and is already exact in ℤ, so a dense form is *reachable*
without this module. It is still the wrong thing to ship: it materialises an
N×N sign matrix to carry an operator whose actual content is N·log2(N)
add/subtracts. That is precisely the "container declares more degrees of freedom
than the object has" defect, so shipping the dense form would reproduce the
defect this work sits next to. ``H_{2ⁿ} = H_2 ⊗ H_2 ⊗ … ⊗ H_2`` is exactly what
licenses the factorisation into log2(N) passes, and the mixed-radix index
arithmetic those passes walk **is** the cube's group structure — that is the
Class-I half of the classification, and it is not decoration.

**NON-CLAIM, and it matters.** The index law here is XOR: ``χ_k · χ_l =
χ_{k⊕l}``. That is *not* offered as evidence the transform is correct. A census
run in this project measured **200/200** random sign tables on the XOR lane
satisfying every structural predicate while **0/200** were associative — "the
index law is XOR" is a valid **refuter** and an invalid **certifier**.
Correctness here rests on the character values being ±1, and is verified by
round-trip (``H·H = N·I``) and by differential test against the dense character
sum. See ``tests/test_walsh_hadamard_rc437.py``.

SSoT: Walsh, "A closed set of normal orthogonal functions", *Amer. J. Math.* **45**
(1923) 5–24; Fino & Algazi, "Unified matrix treatment of the fast
Walsh-Hadamard transform", *IEEE Trans. Computers* **C-25** (1976) 1142–1146.
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

__all__ = ["walsh_hadamard_transform"]

#: The int64 magnitude ceiling the native kernel is safe within. One butterfly
#: pass can double a coefficient, so the bound is on ``N·max|x|``. Above it the
#: pure-Python bignum body runs — the SAME values, arbitrary precision.
_INT64_SAFE = 1 << 62


def _is_pow2(n: int) -> bool:
    """Class-I: ``n`` is a power of two (and ``≥ 1``)."""
    return n >= 1 and (n & (n - 1)) == 0


def _as_ints(signal: Sequence[Any]) -> Optional[List[int]]:
    """Coerce to a plain ``list[int]``, or ``None`` when any entry is not an
    exact integer. ``bool`` is accepted (it IS an int in Python and a cube
    signal is very often a truth table); ``float`` is NOT, even when integral —
    the same refusal ``exact_dft`` makes, and for the same reason."""
    out: List[int] = []
    for v in signal:
        if isinstance(v, bool):
            out.append(1 if v else 0)
            continue
        if isinstance(v, int):
            out.append(v)
            continue
        num = getattr(v, "numerator", None)
        den = getattr(v, "denominator", None)
        if num is not None and den == 1:      # exact Q at integer value
            out.append(int(num))
            continue
        return None
    return out


def _wht_pure(data: List[int]) -> List[int]:
    """The butterfly, pure Python, arbitrary precision. ``log2(N)`` passes over
    a doubling stride; the ``a - b`` IS the Class-K sign-flip (the −1 character
    value is never stored and never multiplied by)."""
    n = len(data)
    out = list(data)
    half = 1
    while half < n:
        width = half * 2
        for base in range(0, n, width):
            for j in range(base, base + half):
                a = out[j]
                b = out[j + half]
                out[j] = a + b
                out[j + half] = a - b
        half = width
    return out


def _wht_native(data: List[int]) -> Optional[List[int]]:
    """The C peer ``srmech_walsh_hadamard_i64``, or ``None`` when the library is
    absent / lacks the symbol / the magnitude could leave the int64 domain.
    Magnitude is read by a Class-K sign branch, never ``abs``."""
    try:
        from srmech import _native
    except Exception:
        return None
    if not getattr(_native, "HAS_NATIVE", False):
        return None
    lib = getattr(_native, "LIB", None)
    if lib is None or not hasattr(lib, "srmech_walsh_hadamard_i64"):
        return None
    n = len(data)
    maxabs = 0
    for v in data:
        a = v if v >= 0 else -v
        if a > maxabs:
            maxabs = a
    if maxabs * n >= _INT64_SAFE:        # bignum is load-bearing → pure path
        return None
    import ctypes

    buf = (ctypes.c_int64 * n)(*data)
    rc = lib.srmech_walsh_hadamard_i64(ctypes.c_uint32(n), buf)
    if rc != 0:
        return None
    return [int(buf[i]) for i in range(n)]


def walsh_hadamard_transform(signal: Sequence[Any]) -> List[int]:
    """The exact Walsh–Hadamard transform of an integer signal on **(ℤ/2)ⁿ**.

    ``signal`` is a length-``N = 2ⁿ`` sequence of exact integers (``bool`` and
    integer-valued exact ``Q`` are accepted; ``float`` is refused). Returns the
    length-N list of **exact integers**

        ``X[k] = Σ_j signal[j] · (−1)^{popcount(j & k)}``

    in **natural (Sylvester / Hadamard) order** — the order in which the
    character index law is XOR and the transform is literally the character
    table of the cube. No floats, no roots of unity, no ring extension: the
    cube's characters are ±1, so the whole answer is add/subtract plus the
    Class-K sign-flip.

    **Cost.** ``N·log2(N)`` add/subtracts and ZERO multiplies, computed as
    ``log2(N)`` in-place butterfly passes. The dense ``N×N`` sign matrix is
    deliberately NOT materialised — ``kron(kron(H2,H2),H2)`` composes today and
    would give the same values, but it declares ``N²`` degrees of freedom for
    an operator that has ``N·log2(N)``.

    **Involution, not a second op.** ``H·H = N·I`` exactly, so this function is
    its own inverse up to the scale::

        walsh_hadamard_transform(walsh_hadamard_transform(x)) == [N*v for v in x]

    gated as an equality at every dim in ``tests/test_walsh_hadamard_rc437.py``.
    There is deliberately **no** ``inverse=`` flag and no ``inverse_walsh_
    hadamard_transform`` peer: the forward and inverse maps are the SAME map,
    and minting a second name for it would assert a which-way distinction the
    mathematics does not have. (Contrast ``cd_left_divide`` / ``cd_right_divide``
    in the same release, which ARE two ops precisely because there the two
    directions are genuinely different maps.) The ``1/N`` is left to the caller
    for the same reason ``exact_idft`` leaves its ``1/N`` to lift time: dividing
    inside an integer kernel is exact only when ``N`` divides every coefficient.

    **Refusal.** A non-power-of-two length raises ``ValueError`` rather than
    zero-padding silently — padding would answer for a DIFFERENT group than the
    one asked about. Non-integral input raises ``ValueError`` too. Both match
    ``exact_dft``'s shipped refusal style.

    **Ordering scope.** Natural/Sylvester order only. Sequency (Walsh) order and
    dyadic (Paley) order are output permutations of this and are NOT shipped;
    nothing here claims to provide them.

    ``c_dispatched`` — the same-rc C peer ``srmech_walsh_hadamard_i64``
    (in-place, no scratch, no arena) computes byte-identical values inside the
    int64 domain; above ``N·max|x| ≥ 2⁶²`` the arbitrary-precision Python body
    runs, which is the COMPLETE alternative implementation and not a fallback.
    ABI-additive: new symbol, ``SRMECH_ABI_VERSION`` stays 14.

    Class **L** (a spectral read — the eigenbasis of the cube's translation
    action) ∘ Class **I** (the butterfly's stride/index arithmetic IS the cube's
    group structure).

    SSoT: Walsh, *Amer. J. Math.* **45** (1923) 5–24; Fino & Algazi, *IEEE
    Trans. Computers* **C-25** (1976) 1142–1146.
    """
    data = _as_ints(signal)
    if data is None:
        raise ValueError(
            "walsh_hadamard_transform: exact-integer signal required (the "
            "cube's characters are ±1, so the transform is exact in whole "
            "numbers; a float operand would throw that away). Use "
            "srmech.cascade.spectral_cascades.dft for floating-point signals.")
    n = len(data)
    if not _is_pow2(n):
        raise ValueError(
            f"walsh_hadamard_transform: length must be a power of two "
            f"(the order of (Z/2)^n); got N={n}. This op REFUSES rather than "
            f"zero-padding to {1 << max(0, (n - 1).bit_length())}, because "
            f"padding would answer for a different group than the one asked "
            f"about.")
    native = _wht_native(data)
    if native is not None:
        return native
    return _wht_pure(data)
