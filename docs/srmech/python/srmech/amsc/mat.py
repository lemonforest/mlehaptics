"""srmech.amsc.mat — the framework-native 2-D matrix carrier (numpy-free).

The 2-D peer of :class:`srmech.amsc.hv.HV`. Where ``HV`` carries a 1-D
hypervector over ``array('B')``, :class:`Mat` carries a dense 2-D matrix over a
flat ``array('d')`` — the carrier the numpy-using ``qm`` / ``signal_processing``
modules hold their working matrices in *once they are converted off numpy*
(the carrier-removal arc, task #564).

Why a framework-native handle and not ``numpy.ndarray``: a numpy-typed value
invites ``np.linalg`` / ``@`` on it; a ``Mat`` handle **forces the srmech
cascade** (``laplacian.dense_matmul`` / ``dense_solve`` /
``hermitian_eigendecompose`` and the native C kernels) and keeps the value
inside the framework until you convert out *on purpose* — the same boundary-type
lever ``HV`` applies in 1-D (UPSTREAM_NOTES §22 / §22b).

Layout (the load-bearing design choice): **row-major, flat** ``array('d')``.

* real: element ``(i, j)`` lives at flat index ``i * n_cols + j``;
* complex: **interleaved** ``(re, im)`` — ``(i, j)`` real at ``2*(i*n_cols+j)``,
  imag at the next slot. This is exactly C99 ``double _Complex`` memory layout,
  so :attr:`buffer` is **directly ``ctypes``-castable** to the buffer the native
  dense kernels read/write — no copy, no numpy, on the HAS_NATIVE path.

This module imports **no numpy at load time** (numpy-free core — the "runs
embedded without numpy/LAPACK" identity). Convert out explicitly:

* :meth:`tolist` / :meth:`tobytes` — stdlib, always available;
* :meth:`to_numpy` — the opt-in numpy bridge (lazy import; clear message if
  numpy is absent — the numpy-free path is :meth:`tolist`).
"""
from __future__ import annotations

from array import array
from typing import List, Sequence, Tuple, Union

__all__ = ["Mat"]

Number = Union[int, float, complex]
RowsLike = Sequence[Sequence[Number]]


class Mat:
    """A numpy-free dense matrix: a flat ``array('d')`` + ``(n_rows, n_cols)``.

    ``is_complex`` selects the buffer layout: real (one ``double`` per element)
    or interleaved-complex (two ``double``\\ s — ``re``, ``im`` — per element,
    C99 ``double _Complex`` order).
    """

    __slots__ = ("_buf", "n_rows", "n_cols", "_complex")

    def __init__(
        self, buf: "array", n_rows: int, n_cols: int, *, is_complex: bool = False
    ) -> None:
        assert isinstance(buf, array) and buf.typecode == "d", (
            "Mat buffer must be array('d') (float64)"
        )
        assert isinstance(n_rows, int) and isinstance(n_cols, int), (
            "Mat dims must be plain ints"
        )
        assert n_rows >= 0 and n_cols >= 0, "Mat dims must be non-negative"
        stride = 2 if is_complex else 1
        assert len(buf) == stride * n_rows * n_cols, (
            f"Mat buffer length {len(buf)} != {stride}*{n_rows}*{n_cols}"
        )
        self._buf = buf
        self.n_rows = n_rows
        self.n_cols = n_cols
        self._complex = bool(is_complex)

    # ── construction ──────────────────────────────────────────────────────
    @classmethod
    def from_rows(cls, rows: RowsLike, *, is_complex: bool = None) -> "Mat":
        """Build a ``Mat`` from a list-of-rows (each row a sequence of numbers).

        ``is_complex`` defaults to auto-detect (any ``complex`` element with a
        non-zero imaginary part forces the complex layout); pass it explicitly
        to pin the layout regardless of the sampled values."""
        rows = [list(r) for r in rows]
        n_rows = len(rows)
        n_cols = len(rows[0]) if n_rows else 0
        for r in rows:
            assert len(r) == n_cols, "Mat.from_rows: ragged rows not allowed"
        if is_complex is None:
            is_complex = any(
                isinstance(x, complex) and x.imag != 0.0 for r in rows for x in r
            )
        buf = array("d")
        if is_complex:
            for r in rows:
                for x in r:
                    z = complex(x)
                    buf.append(z.real)
                    buf.append(z.imag)
        else:
            for r in rows:
                for x in r:
                    buf.append(float(x.real if isinstance(x, complex) else x))
        return cls(buf, n_rows, n_cols, is_complex=bool(is_complex))

    @classmethod
    def from_flat(
        cls, buf: Sequence[float], n_rows: int, n_cols: int, *, is_complex: bool = False
    ) -> "Mat":
        """Build from an already-flat row-major buffer (copied; the Mat owns it)."""
        return cls(array("d", (float(x) for x in buf)), n_rows, n_cols, is_complex=is_complex)

    # ── numpy-free access ─────────────────────────────────────────────────
    @property
    def shape(self) -> Tuple[int, int]:
        return (self.n_rows, self.n_cols)

    @property
    def is_complex(self) -> bool:
        return self._complex

    def __len__(self) -> int:
        return self.n_rows  # number of rows, like numpy's 2-D len

    def _flat_index(self, i: int, j: int) -> int:
        assert 0 <= i < self.n_rows and 0 <= j < self.n_cols, "Mat index out of range"
        return i * self.n_cols + j

    def __getitem__(self, idx):
        """``mat[i, j]`` → a PLAIN ``float`` / ``complex`` scalar (never a numpy
        scalar); ``mat[i]`` (a single int) → row ``i`` as a :class:`~srmech.amsc.vec.Vec`
        — the numpy single-index idiom, format-preserving (a ``Vec``, not a bare
        list). For an explicit stdlib list use :meth:`row`."""
        if isinstance(idx, tuple):
            assert len(idx) == 2, "Mat index must be (i, j) or a single row int"
            i, j = idx
            flat = self._flat_index(i, j)
            if self._complex:
                return complex(self._buf[2 * flat], self._buf[2 * flat + 1])
            return float(self._buf[flat])
        from .vec import Vec  # local: vec.py is a sibling carrier, avoid import cycle
        i = int(idx)
        assert -self.n_rows <= i < self.n_rows, "Mat row index out of range"
        if i < 0:
            i += self.n_rows
        return Vec.from_sequence(self.row(i), is_complex=self._complex)

    def row(self, i: int) -> List[Number]:
        """Row ``i`` as a stdlib ``list`` of plain numbers (numpy-free)."""
        return [self[i, j] for j in range(self.n_cols)]

    def __iter__(self):
        return (self.row(i) for i in range(self.n_rows))

    def transpose(self) -> "Mat":
        """The transpose as a new ``Mat`` (numpy-free; no conjugation)."""
        out = [[self[i, j] for i in range(self.n_rows)] for j in range(self.n_cols)]
        return Mat.from_rows(out, is_complex=self._complex)

    @property
    def T(self) -> "Mat":
        return self.transpose()

    def conj(self) -> "Mat":
        """Element-wise complex conjugate as a new ``Mat`` (real → copy)."""
        if not self._complex:
            return Mat(array("d", self._buf), self.n_rows, self.n_cols)
        out = array("d", self._buf)
        for k in range(1, len(out), 2):  # negate every imaginary slot (Class K sign)
            out[k] = -out[k]
        return Mat(out, self.n_rows, self.n_cols, is_complex=True)

    # ── matmul (the numpy ``@`` idiom, routed onto the Class-L cascade) ───
    def __matmul__(self, other):
        """``A·B`` — the numpy ``@`` matmul idiom, routed onto the srmech Class-L
        cascade (``laplacian.dense_matmul_*`` / ``dense_matvec_*``), **never**
        numpy's own contraction. ``Mat·Mat`` → :class:`Mat`; ``Mat·Vec`` (or a
        flat 1-D sequence) → :class:`~srmech.amsc.vec.Vec`. Format-preserving
        (rc130): real ⊗ real → real carrier, complex anywhere → complex carrier."""
        from . import laplacian as _L  # lazy: laplacian imports Mat (avoid cycle)
        cplx = self._complex or _carrier_is_complex(other)
        if _is_matrix_like(other):
            return (_L.dense_matmul_complex if cplx else _L.dense_matmul_real)(self, other)
        return (_L.dense_matvec_complex if cplx else _L.dense_matvec_real)(self, other)

    def __rmatmul__(self, other):
        """``other·A`` for a non-:class:`Mat` left operand (a left-side flat
        sequence / :class:`~srmech.amsc.vec.Vec` → ``Vec·Mat``; a left-side
        2-D sequence → ``M·A``). Routes onto the Class-L cascade."""
        from . import laplacian as _L  # lazy (avoid cycle)
        cplx = self._complex or _carrier_is_complex(other)
        if _is_matrix_like(other):
            return (_L.dense_matmul_complex if cplx else _L.dense_matmul_real)(other, self)
        # row-vector · matrix = (Aᵀ · v): the left flat vector contracts rows.
        return (_L.dense_matvec_complex if cplx else _L.dense_matvec_real)(self.transpose(), other)

    def __eq__(self, other) -> bool:
        """Value-equality → a scalar ``bool`` (never an elementwise array).

        Accepts another ``Mat``, a list-of-rows, or a 2-D ``numpy.ndarray`` (so
        a research-side ``np.array_equal(a, b)`` migrates to ``a == b``)."""
        if other is self:
            return True
        if isinstance(other, Mat):
            return (
                self.shape == other.shape
                and self._complex == other._complex
                and list(self._buf) == list(other._buf)
            )
        if hasattr(other, "tolist"):  # numpy.ndarray and friends
            other = other.tolist()
        try:
            other_rows = [list(r) for r in other]
        except TypeError:
            return NotImplemented
        return self.tolist() == [
            [complex(x) if self._complex else float(x) for x in r] for r in other_rows
        ]

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else (not result)

    __hash__ = None  # mutable buffer → unhashable (like list / HV)

    def __repr__(self) -> str:
        kind = "complex" if self._complex else "real"
        return f"Mat({self.n_rows}x{self.n_cols}, {kind})"

    # ── explicit conversions out ──────────────────────────────────────────
    def tolist(self) -> List[List[Number]]:
        """List-of-rows copy of plain numbers (numpy-free)."""
        return [self.row(i) for i in range(self.n_rows)]

    def tobytes(self) -> bytes:
        """Raw ``bytes`` copy of the flat row-major buffer (numpy-free)."""
        return self._buf.tobytes()

    @property
    def buffer(self) -> "array":
        """The underlying flat ``array('d')`` (contiguous, buffer-protocol — the
        handle the native C dense kernels read/write in place; interleaved
        ``(re, im)`` for complex). Mutating it mutates the ``Mat``; use
        :meth:`tolist` / :meth:`tobytes` for a copy."""
        return self._buf


# ── shared carrier shape/dtype detectors (the ``@`` operands may be Mat / Vec /
#    raw sequences; Vec reuses these too — numpy-free, no laplacian import) ────
def _is_matrix_like(x) -> bool:
    """``True`` if ``x`` is 2-D matrix-like (a :class:`Mat` or a nested
    sequence), ``False`` if it is a 1-D vector-like (a ``Vec`` / flat sequence /
    scalar). The disambiguator the carrier ``@`` uses to pick matmul vs matvec."""
    if isinstance(x, Mat):
        return True
    if hasattr(x, "shape"):  # Vec / ndarray-like — trust the rank
        return len(x.shape) >= 2
    try:
        first = x[0]
    except (TypeError, IndexError, KeyError):
        return False
    return isinstance(first, (list, tuple)) or (
        hasattr(first, "__len__") and not isinstance(first, (str, bytes))
    )


def _carrier_is_complex(x) -> bool:
    """``True`` if any element of ``x`` carries a non-zero imaginary part (or its
    carrier is complex-typed) — the dtype gate the carrier ``@`` uses to choose
    the real vs complex Class-L peer. Numpy-free."""
    if hasattr(x, "is_complex"):
        return bool(x.is_complex)
    try:
        flat = []
        for el in x:
            if isinstance(el, (list, tuple)):
                flat.extend(el)
            else:
                flat.append(el)
    except TypeError:
        return False
    return any(isinstance(v, complex) and v.imag != 0.0 for v in flat)

