"""srmech.amsc.vec — the framework-native 1-D vector carrier (numpy-free).

The 1-D peer of :class:`srmech.amsc.mat.Mat`. Where :class:`Mat` carries a dense
2-D matrix over a flat ``array('d')``, :class:`Vec` carries a dense 1-D vector
over the same flat ``array('d')`` buffer — the carrier the numpy-free Class-L
ops (``fiedler_vector`` / ``dense_matvec_*`` / ``jacobi_eigvals`` eigenvalues /
the eigenVALUES of the Hermitian/symmetric eigendecompose) return their working
vectors in *once they are converted off numpy* (the carrier-removal arc, #564).

Why a framework-native handle and not a bare Python ``list``: a ``list`` loses
``.shape``, the 1-D structure, AND has **no honest C representation** — a `Vec`
*is* something in C (a contiguous ``double`` / interleaved ``double _Complex``
buffer), exactly like :class:`Mat`. The rc127 numpy-removal regressed ~17 ops to
bare lists/tuples; rc129 restores the numpy-carrier FORMAT by returning the
2-D :class:`Mat` / the 1-D :class:`Vec` instead (both with ``.shape`` + a native
C interleaved-buffer wire form).

Layout (mirroring :class:`Mat`): a flat ``array('d')``.

* real: element ``i`` lives at flat index ``i`` (``n`` doubles total);
* complex: **interleaved** ``(re, im)`` — element ``i`` real at ``2*i``, imag at
  ``2*i+1`` (``2n`` doubles total). This is exactly C99 ``double _Complex``
  memory layout, so :attr:`buffer` is **directly ``ctypes``-castable** to the
  buffer the native dense kernels read/write — no copy, no numpy.

This module imports **no numpy at load time** (numpy-free core). Convert out
explicitly via :meth:`tolist` / :meth:`tobytes`.
"""
from __future__ import annotations

from array import array
from typing import List, Sequence, Tuple, Union

__all__ = ["Vec"]

Number = Union[int, float, complex]
SeqLike = Sequence[Number]


class Vec:
    """A numpy-free dense vector: a flat ``array('d')`` + a length ``n``.

    ``is_complex`` selects the buffer layout: real (one ``double`` per element)
    or interleaved-complex (two ``double``\\ s — ``re``, ``im`` — per element,
    C99 ``double _Complex`` order). The 1-D analogue of :class:`Mat`.
    """

    __slots__ = ("_buf", "_n", "_complex")

    def __init__(self, buf: "array", n: int, *, is_complex: bool = False) -> None:
        assert isinstance(buf, array) and buf.typecode == "d", (
            "Vec buffer must be array('d') (float64)"
        )
        assert isinstance(n, int), "Vec length must be a plain int"
        assert n >= 0, "Vec length must be non-negative"
        stride = 2 if is_complex else 1
        assert len(buf) == stride * n, (
            f"Vec buffer length {len(buf)} != {stride}*{n}"
        )
        self._buf = buf
        self._n = n
        self._complex = bool(is_complex)

    # ── construction ──────────────────────────────────────────────────────
    @classmethod
    def from_sequence(cls, seq: SeqLike, *, is_complex: bool = None) -> "Vec":
        """Build a ``Vec`` from a flat sequence of numbers.

        ``is_complex`` defaults to auto-detect (any ``complex`` element with a
        non-zero imaginary part forces the complex layout); pass it explicitly
        to pin the layout regardless of the sampled values."""
        items = list(seq)
        n = len(items)
        if is_complex is None:
            is_complex = any(
                isinstance(x, complex) and x.imag != 0.0 for x in items
            )
        buf = array("d")
        if is_complex:
            for x in items:
                z = complex(x)
                buf.append(z.real)
                buf.append(z.imag)
        else:
            for x in items:
                buf.append(float(x.real if isinstance(x, complex) else x))
        return cls(buf, n, is_complex=bool(is_complex))

    @classmethod
    def from_flat(
        cls, buf: Sequence[float], n: int, *, is_complex: bool = False
    ) -> "Vec":
        """Build from an already-flat buffer (copied; the Vec owns it).

        ``buf`` holds ``n`` doubles (real) or ``2n`` interleaved ``(re, im)``
        doubles (complex) — the same on-disk shape :meth:`buffer` exposes."""
        return cls(array("d", (float(x) for x in buf)), n, is_complex=is_complex)

    # ── numpy-free access ─────────────────────────────────────────────────
    @property
    def shape(self) -> Tuple[int]:
        """A 1-tuple ``(n,)`` — like a 1-D ``numpy.ndarray``'s ``.shape``."""
        return (self._n,)

    @property
    def is_complex(self) -> bool:
        return self._complex

    def __len__(self) -> int:
        return self._n

    def __getitem__(self, i):
        """``vec[i]`` → a PLAIN ``float`` / ``complex`` scalar (negatives OK);
        ``vec[a:b]`` → a sub-:class:`Vec` (the rc133 slice idiom — so ``v[:2]`` /
        ``v[-1]`` route through srmech instead of bailing to numpy)."""
        if isinstance(i, slice):
            return Vec.from_sequence(
                [self[k] for k in range(*i.indices(self._n))], is_complex=self._complex)
        i = int(i)
        if i < 0:
            i += self._n
        assert 0 <= i < self._n, "Vec index out of range"
        if self._complex:
            return complex(self._buf[2 * i], self._buf[2 * i + 1])
        return float(self._buf[i])

    def __iter__(self):
        """Yields SCALARS (plain ``float`` / ``complex``), not rows."""
        return (self[i] for i in range(self._n))

    def conj(self) -> "Vec":
        """Element-wise complex conjugate as a new ``Vec`` (real → copy)."""
        if not self._complex:
            return Vec(array("d", self._buf), self._n)
        out = array("d", self._buf)
        for k in range(1, len(out), 2):  # negate every imaginary slot (Class K sign)
            out[k] = -out[k]
        return Vec(out, self._n, is_complex=True)

    # ── matmul (the numpy ``@`` idiom, routed onto the Class-L cascade) ───
    def __matmul__(self, other):
        """``v·B`` — the numpy ``@`` matmul idiom, routed onto the srmech Class-L
        cascade (``laplacian.dense_dot_*`` / ``dense_matvec_*``), **never**
        numpy's own contraction. ``Vec·Vec`` (or a flat 1-D sequence) → a scalar
        inner product ``Σ aᵢ bᵢ``; ``Vec·Mat`` (row-vector · matrix) →
        :class:`Vec`. Format-preserving (rc130)."""
        from . import laplacian as _L  # lazy (avoid import cycle)
        from .mat import Mat, _is_matrix_like, _carrier_is_complex
        cplx = self._complex or _carrier_is_complex(other)
        if _is_matrix_like(other):
            M = other if isinstance(other, Mat) else Mat.from_rows(
                [list(r) for r in other], is_complex=cplx
            )
            # row-vector · matrix = (Mᵀ · v): the vector contracts the rows.
            return (_L.dense_matvec_complex if cplx else _L.dense_matvec_real)(M.transpose(), self)
        return (_L.dense_dot_complex if cplx else _L.dense_dot_real)(self, other)

    def __rmatmul__(self, other):
        """``B·v`` for a non-:class:`Vec` left operand: a 2-D sequence →
        ``M·v`` (a :class:`Vec`); a flat 1-D sequence → the scalar inner
        product. (``Mat·Vec`` is served by :meth:`Mat.__matmul__`.)"""
        from . import laplacian as _L  # lazy (avoid import cycle)
        from .mat import _is_matrix_like, _carrier_is_complex
        cplx = self._complex or _carrier_is_complex(other)
        if _is_matrix_like(other):
            return (_L.dense_matvec_complex if cplx else _L.dense_matvec_real)(other, self)
        return (_L.dense_dot_complex if cplx else _L.dense_dot_real)(other, self)

    # ── elementwise / scalar arithmetic (the numpy ``+ - * /`` reflex sink) ───
    def _elementwise(self, other, op, *, reflected: bool = False):
        """``self ⊙ other`` (or ``other ⊙ self`` when reflected), elementwise,
        for ``other`` a scalar (numpy-broadcast), a :class:`Vec`, or a flat
        sequence of the SAME length. Numpy-free; format-preserving; no ``abs()``
        (Class-K sign lives in the values)."""
        if isinstance(other, (int, float, complex)):
            cplx = self._complex or (isinstance(other, complex) and other.imag != 0.0)
            items = [(op(other, self[k]) if reflected else op(self[k], other))
                     for k in range(self._n)]
            return Vec.from_sequence(items, is_complex=cplx)
        if isinstance(other, Vec):
            o = other
        elif hasattr(other, "shape") and len(getattr(other, "shape")) >= 2:
            return NotImplemented  # a Mat / 2-D — cross-rank broadcast unsupported
        elif hasattr(other, "__len__") and not isinstance(other, (str, bytes)):
            o = Vec.from_sequence(other.tolist() if hasattr(other, "tolist") else list(other))
        else:
            return NotImplemented
        if o._n != self._n:
            raise ValueError(f"Vec elementwise length mismatch {self._n} vs {o._n}")
        cplx = self._complex or o._complex
        items = [(op(o[k], self[k]) if reflected else op(self[k], o[k]))
                 for k in range(self._n)]
        return Vec.from_sequence(items, is_complex=cplx)

    def __add__(self, other):
        return self._elementwise(other, lambda a, b: a + b)

    def __radd__(self, other):
        return self._elementwise(other, lambda a, b: a + b)

    def __sub__(self, other):
        return self._elementwise(other, lambda a, b: a - b)

    def __rsub__(self, other):
        return self._elementwise(other, lambda a, b: a - b, reflected=True)

    def __mul__(self, other):
        return self._elementwise(other, lambda a, b: a * b)

    def __rmul__(self, other):
        return self._elementwise(other, lambda a, b: a * b)

    def __truediv__(self, other):
        return self._elementwise(other, lambda a, b: a / b)

    def __rtruediv__(self, other):
        return self._elementwise(other, lambda a, b: a / b, reflected=True)

    def __neg__(self):  # the Class-K sign-flip over every element
        return Vec.from_sequence([-self[k] for k in range(self._n)], is_complex=self._complex)

    def __eq__(self, other) -> bool:
        """Value-equality → a scalar ``bool`` (never an elementwise array).

        Accepts another ``Vec`` or a flat sequence of numbers. Never imports
        numpy; an object exposing ``tolist`` (e.g. an ndarray-like) is coerced
        via that method (a carrier convert, not a numpy import)."""
        if other is self:
            return True
        if isinstance(other, Vec):
            return (
                self._n == other._n
                and self._complex == other._complex
                and list(self._buf) == list(other._buf)
            )
        if hasattr(other, "tolist"):  # ndarray-like and friends
            other = other.tolist()
        try:
            other_items = list(other)
        except TypeError:
            return NotImplemented
        if len(other_items) != self._n:
            return False
        return self.tolist() == [
            complex(x) if self._complex else float(x) for x in other_items
        ]

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else (not result)

    __hash__ = None  # mutable buffer → unhashable (like list / Mat)

    def __repr__(self) -> str:
        kind = "complex" if self._complex else "real"
        return f"Vec({self._n}, {kind})"

    # ── explicit conversions out ──────────────────────────────────────────
    def tolist(self) -> List[Number]:
        """Flat ``list`` copy of plain numbers (numpy-free)."""
        return [self[i] for i in range(self._n)]

    def tobytes(self) -> bytes:
        """Raw ``bytes`` copy of the flat buffer (numpy-free)."""
        return self._buf.tobytes()

    @property
    def buffer(self) -> "array":
        """The underlying flat ``array('d')`` (contiguous, buffer-protocol — the
        handle the native C dense kernels read/write in place; interleaved
        ``(re, im)`` for complex). Mutating it mutates the ``Vec``; use
        :meth:`tolist` / :meth:`tobytes` for a copy."""
        return self._buf
