"""srmech.amsc.qmat — the framework-native EXACT-rational matrix carrier (``QMat``).

The 2-D peer of the scalar exact carrier :class:`srmech.amsc.q.Q`, and the exact
(bigint) cousin of the float64 :class:`srmech.amsc.mat.Mat`. Where ``Mat`` carries
a dense matrix over a flat ``array('d')`` (float64 — the display boundary for
genuinely-irrational entries), ``QMat`` carries a dense matrix whose every entry
is an exact :class:`~srmech.amsc.q.Q` rational — a reduced ``(num, den)`` integer
pair, each integer a Python ``int`` (so **arbitrary precision, no magnitude
ceiling**: an entry numerator or denominator may freely exceed ``2⁶⁴``, unlike
the native int64 Q61 fixed-point path). It completes the array-carrier family the
way ``Qi``/``Qalg``/``Qprime`` complete the scalar family: ``Q`` is the exact
real scalar, ``Mat`` the float matrix, and ``QMat`` the **exact** matrix that was
the gap — exact dense linear algebra without the ad-hoc nested
``Fraction``/``Qalg`` lists exact eigenwork rode before.

Why a carrier and not nested ``Q`` lists (mirrors the ``Q`` / ``Mat`` rationale):

- **The stay-rational discipline** (F868). An exactly-rational matrix — an
  integer adjacency, a Markov stochastic matrix, the ``[A|I]`` of an exact
  inverse — must stay two integers per entry the whole way and collapse to
  float64 **only at the display boundary** (:meth:`to_mat`). A ``float64`` ``Mat``
  is just ``best_rational`` at ``max_d ≈ 2⁵²`` with the provenance thrown away —
  a strictly worse version of the rational we already hold.
- Like a ``Mat`` handle forces the srmech Class-L cascade instead of inviting
  ``np.linalg``, a ``QMat`` handle forces **exact** rational linear algebra
  (Gauss-Jordan over ``Q``, pivot by ``Q != 0`` / ``Q`` comparison — never a
  float tolerance) and keeps every intermediate attestable.

Everything stays exact: ``+`` / ``−`` / ``−x`` / scalar ``*`` are entrywise over
the Class-N ``Q`` arithmetic; ``@`` is the exact bilinear contraction; the
headline linear algebra — :meth:`rref` / :meth:`rank` / :meth:`det` /
:meth:`inverse` / :meth:`solve` / :meth:`nullspace` — is exact Gauss-Jordan over
ℚ on a shared :func:`_rref_augmented` kernel (the same elimination as
``srmech.qm.triality`` and ``matrix_cascades._qalg_rref``, but over plain ``Q``).
Sign in pivoting / determinant is the **Class-K** pin-slot via an explicit ``Q``
sign-branch, never an ALU ``abs()``. There is exactly ONE place a ``float``
appears — :meth:`to_mat`, the terminal ALU→FPU rotation that lifts to a float64
``Mat`` (like ``Qalg.to_complex`` / ``Q.__float__``). No ``math`` module, no
numpy; a future ``QiMat`` would carry Gaussian-rational (``Qi``) entries.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Sequence, Tuple

from .q import Q

__all__ = ["QMat"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)


def _to_q(value, *, allow_float: bool = False):
    """Coerce ``value`` to an exact :class:`~srmech.amsc.q.Q`, or ``None`` if it
    is not an exact-rational-coercible entry (mirrors ``qi``/``qalg`` ``_to_q``).

    A ``float`` is REJECTED by default (returns ``None``) — a QMat entry must be
    exact, so a float must enter through the explicit :meth:`QMat.from_float_rows`
    boundary, never silently. ``allow_float=True`` (used only inside that
    boundary) promotes the float to its exact ratio via :meth:`Q.from_float`."""
    if isinstance(value, Q):
        return value
    if isinstance(value, bool):
        return Q(int(value), 1)
    if isinstance(value, int):
        return Q(value, 1)
    if isinstance(value, Fraction):
        return Q(value.numerator, value.denominator)
    if isinstance(value, float):
        if not allow_float:
            return None
        try:
            return Q.from_float(value)               # exact ratio of the float
        except (OverflowError, ValueError):
            return None
    if (isinstance(value, (tuple, list)) and len(value) == 2
            and isinstance(value[0], int) and isinstance(value[1], int)
            and value[1] != 0):
        return Q(value[0], value[1])
    pair = getattr(value, "as_pair", None) or getattr(value, "as_integer_ratio", None)
    if pair is not None:
        try:
            n, d = pair()
            return Q(int(n), int(d))
        except (TypeError, ValueError, ZeroDivisionError):
            return None
    return None


def _coerce_rows(rows, *, allow_float: bool = False) -> Tuple[Tuple[Q, ...], ...]:
    """Coerce a nested sequence to a rectangular tuple-of-tuples of exact ``Q``.

    Raises ``TypeError`` on a non-exact entry (e.g. a float when ``allow_float``
    is ``False``) and ``ValueError`` on ragged rows."""
    out_rows: List[Tuple[Q, ...]] = []
    n_cols = None
    for r in rows:
        row = list(r)
        if n_cols is None:
            n_cols = len(row)
        elif len(row) != n_cols:
            raise ValueError(
                f"QMat rows must be rectangular; row 0 has {n_cols} cols, "
                f"row {len(out_rows)} has {len(row)}")
        cells: List[Q] = []
        for x in row:
            q = _to_q(x, allow_float=allow_float)
            if q is None:
                if isinstance(x, float):
                    raise TypeError(
                        "QMat entries must be EXACT (Q / int / (num, den) / "
                        "Fraction); a float must enter via QMat.from_float_rows / "
                        f"from_mat, never silently — got float {x!r}")
                raise TypeError(
                    "QMat entries must be exact-rational (Q / int / (num, den) / "
                    f"Fraction); got {type(x).__name__}")
            cells.append(q)
        out_rows.append(tuple(cells))
    return tuple(out_rows)


class QMat:
    """A numpy-free EXACT-rational dense matrix: a tuple-of-tuples of exact ``Q``
    + ``(n_rows, n_cols)``, immutable. The bigint exact peer of the float64
    :class:`srmech.amsc.mat.Mat`. Collapses to a float64 ``Mat`` only via
    :meth:`to_mat`. See the module docstring."""

    __slots__ = ("_rows", "n_rows", "n_cols")

    def __init__(self, rows) -> None:
        coerced = _coerce_rows(rows)
        self._rows = coerced
        self.n_rows = len(coerced)
        self.n_cols = len(coerced[0]) if coerced else 0

    # ── construction ───────────────────────────────────────────────────────
    @classmethod
    def from_rows(cls, rows) -> "QMat":
        """Build a ``QMat`` from a nested sequence (the canonical constructor,
        mirrors :meth:`srmech.amsc.mat.Mat.from_rows`). Each entry is coerced to
        an exact ``Q`` (``Q`` / ``int`` / ``(num, den)`` pair / ``Fraction``); a
        ``float`` is rejected — use :meth:`from_float_rows`."""
        return cls(rows)

    @classmethod
    def from_float_rows(cls, rows, *, max_denominator=None) -> "QMat":
        """Lift a nested sequence of FLOATS into the exact carrier — the explicit
        float→rational boundary (the one place a float legitimately enters).

        ``max_denominator is None`` promotes each float to its EXACT ratio
        (:meth:`Q.from_float` — no precision lost vs the float, possibly a large
        power-of-two denominator). A ``max_denominator`` instead SNAPS each entry
        to the best rational with denominator ≤ that bound (Class-N
        :func:`srmech.amsc.rational.best_rational`), de-noising the float64
        round-off (e.g. ``0.1 → 1/10``)."""
        if max_denominator is None:
            return cls.__new__(cls)._init_from(
                _coerce_rows(rows, allow_float=True))
        from . import rational as _rational
        snapped: List[List[Q]] = []
        n_cols = None
        for r in rows:
            row = list(r)
            if n_cols is None:
                n_cols = len(row)
            elif len(row) != n_cols:
                raise ValueError("QMat.from_float_rows: rows must be rectangular")
            out: List[Q] = []
            for x in row:
                exact = _to_q(x, allow_float=True)
                if exact is None:
                    raise TypeError(
                        f"QMat.from_float_rows: entry not float-coercible: {x!r}")
                num, den = exact.as_pair()
                # Class-N best-rational snap of the exact float ratio to ≤ max_den.
                p, q = _rational.best_rational(num, den, int(max_denominator))
                # best_rational returns (0, 1) when no nontrivial convergent fits;
                # keep the exact ratio in that degenerate case (no worse snap).
                out.append(Q(p, q) if (p, q) != (0, 1) or exact == 0 else exact)
            snapped.append(out)
        return cls.from_rows(snapped)

    def _init_from(self, coerced: Tuple[Tuple[Q, ...], ...]) -> "QMat":
        """Internal: populate slots from an already-coerced tuple-of-tuples."""
        self._rows = coerced
        self.n_rows = len(coerced)
        self.n_cols = len(coerced[0]) if coerced else 0
        return self

    @classmethod
    def from_mat(cls, mat, *, max_denominator=None) -> "QMat":
        """Lift a float64 :class:`srmech.amsc.mat.Mat` to an exact ``QMat`` (the
        exact-promotion bridge). Rejects a COMPLEX ``Mat`` with a clear error —
        ``QMat`` is real-rational; a Gaussian-rational matrix would be a future
        ``QiMat``. ``max_denominator`` snaps the entries (see
        :meth:`from_float_rows`)."""
        if getattr(mat, "is_complex", False):
            raise ValueError(
                "QMat.from_mat: cannot lift a COMPLEX Mat — QMat is "
                "real-rational; a Gaussian-rational matrix would be a future "
                "QiMat. Take .real first, or carry the entries as Qi.")
        rows = mat.tolist() if hasattr(mat, "tolist") else [list(r) for r in mat]
        return cls.from_float_rows(rows, max_denominator=max_denominator)

    @classmethod
    def identity(cls, n: int) -> "QMat":
        """The exact ``n×n`` identity (``1`` on the diagonal, ``0`` off it)."""
        if not isinstance(n, int) or n < 0:
            raise ValueError(f"QMat.identity: n must be a non-negative int; got {n!r}")
        rows = [[_Q_ONE if i == j else _Q_ZERO for j in range(n)] for i in range(n)]
        return cls.__new__(cls)._init_from(tuple(tuple(r) for r in rows))

    @classmethod
    def zeros(cls, n_rows: int, n_cols: int) -> "QMat":
        """The exact ``n_rows × n_cols`` zero matrix."""
        if not (isinstance(n_rows, int) and isinstance(n_cols, int)
                and n_rows >= 0 and n_cols >= 0):
            raise ValueError("QMat.zeros: dims must be non-negative ints")
        rows = tuple(tuple(_Q_ZERO for _ in range(n_cols)) for _ in range(n_rows))
        return cls.__new__(cls)._init_from(rows)

    # ── accessors ──────────────────────────────────────────────────────────
    @property
    def shape(self) -> Tuple[int, int]:
        return (self.n_rows, self.n_cols)

    def __len__(self) -> int:
        return self.n_rows

    def _norm_row(self, i: int) -> int:
        if i < 0:
            i += self.n_rows
        if not 0 <= i < self.n_rows:
            raise IndexError("QMat row index out of range")
        return i

    def _norm_col(self, j: int) -> int:
        if j < 0:
            j += self.n_cols
        if not 0 <= j < self.n_cols:
            raise IndexError("QMat column index out of range")
        return j

    def __getitem__(self, idx):
        """``m[i, j]`` → the exact ``Q`` entry (negative-aware); ``m[i]`` → row
        ``i`` as a tuple of ``Q``."""
        if isinstance(idx, tuple):
            if len(idx) != 2:
                raise IndexError("QMat index must be (i, j) or a single row int")
            i, j = idx
            return self._rows[self._norm_row(int(i))][self._norm_col(int(j))]
        return self._rows[self._norm_row(int(idx))]

    def __iter__(self):
        return iter(self._rows)

    def to_lists(self) -> List[List[Q]]:
        """List-of-rows copy, each entry an exact ``Q`` (the numpy-free read-out;
        the exact analogue of :meth:`srmech.amsc.mat.Mat.tolist`)."""
        return [list(r) for r in self._rows]

    def __eq__(self, other) -> bool:
        """Exact entrywise equality. Accepts another ``QMat`` or a nested sequence
        (coerced to ``Q`` for the compare); shape must match."""
        if other is self:
            return True
        if isinstance(other, QMat):
            return self._rows == other._rows
        try:
            o = QMat.from_rows(other)
        except (TypeError, ValueError):
            return NotImplemented
        return self._rows == o._rows

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else (not result)

    def __hash__(self) -> int:
        # Immutable (tuple-of-tuples of Q); hash the rows like Qi/Qalg hash their
        # coords. Equal QMats hash equal.
        return hash(self._rows)

    def __repr__(self) -> str:
        return f"QMat({self.n_rows}x{self.n_cols}, exact-rational)"

    # ── exact arithmetic (entrywise over Q; Class-K sign) ───────────────────
    def _same_shape(self, other: "QMat", what: str) -> None:
        if self.shape != other.shape:
            raise ValueError(
                f"QMat {what} shape mismatch {self.shape} vs {other.shape}")

    def __add__(self, other):
        if not isinstance(other, QMat):
            return NotImplemented
        self._same_shape(other, "+")
        rows = tuple(tuple(a + b for a, b in zip(ra, rb))
                     for ra, rb in zip(self._rows, other._rows))
        return QMat.__new__(QMat)._init_from(rows)

    def __sub__(self, other):
        if not isinstance(other, QMat):
            return NotImplemented
        self._same_shape(other, "-")
        rows = tuple(tuple(a - b for a, b in zip(ra, rb))
                     for ra, rb in zip(self._rows, other._rows))
        return QMat.__new__(QMat)._init_from(rows)

    def __neg__(self) -> "QMat":
        # The Class-K sign-flip over every entry (Q.__neg__, no ALU abs).
        rows = tuple(tuple(-a for a in r) for r in self._rows)
        return QMat.__new__(QMat)._init_from(rows)

    def __mul__(self, other):
        """Scalar multiply by a ``Q`` / ``int`` / ``Fraction`` / ``(num, den)``
        (the numpy ``*`` over a scalar). Matrix product is ``@``."""
        q = _to_q(other)
        if q is None:
            return NotImplemented
        rows = tuple(tuple(a * q for a in r) for r in self._rows)
        return QMat.__new__(QMat)._init_from(rows)

    __rmul__ = __mul__

    def __matmul__(self, other):
        """``A·B`` — the EXACT matrix product (the numpy ``@`` idiom over ``Q``).
        Shape-checked (``self.n_cols == other.n_rows``)."""
        if not isinstance(other, QMat):
            return NotImplemented
        return self.matmul(other)

    def matmul(self, other: "QMat") -> "QMat":
        """The exact matrix product ``self · other`` over ``Q`` (the named form of
        ``@``). Raises ``ValueError`` on an inner-dimension mismatch."""
        if not isinstance(other, QMat):
            raise TypeError("QMat.matmul requires another QMat")
        if self.n_cols != other.n_rows:
            raise ValueError(
                f"QMat matmul inner-dim mismatch: {self.shape} @ {other.shape}")
        bt = other.transpose()._rows                 # columns of `other` as rows
        out_rows: List[Tuple[Q, ...]] = []
        for ra in self._rows:
            row: List[Q] = []
            for col in bt:
                acc = _Q_ZERO
                for a, b in zip(ra, col):
                    acc = acc + a * b
                row.append(acc)
            out_rows.append(tuple(row))
        return QMat.__new__(QMat)._init_from(tuple(out_rows))

    def transpose(self) -> "QMat":
        """The transpose as a new ``QMat`` (numpy-free; exact, no conjugation)."""
        rows = tuple(tuple(self._rows[i][j] for i in range(self.n_rows))
                     for j in range(self.n_cols))
        return QMat.__new__(QMat)._init_from(rows)

    @property
    def T(self) -> "QMat":
        return self.transpose()

    # ── exact linear algebra over ℚ (Gauss-Jordan; bigint; no float) ────────
    def rref(self) -> "QMat":
        """The EXACT reduced row-echelon form (Gauss-Jordan over ℚ). Pivots on the
        first nonzero ``Q`` in each column (``Q != 0``, never a float tolerance);
        every pivot row is scaled to a leading ``1`` and cleared above + below.
        Bigint exact — no magnitude ceiling."""
        R, _piv, _prc = _rref_augmented(self._rows, self.n_cols)
        return QMat.__new__(QMat)._init_from(tuple(tuple(r) for r in R))

    def rank(self) -> int:
        """The EXACT rank = the pivot count of the RREF (exact over ℚ)."""
        _R, pivot_cols, _prc = _rref_augmented(self._rows, self.n_cols)
        return len(pivot_cols)

    def det(self) -> Q:
        """The EXACT determinant as a ``Q`` (square only) via Gauss elimination
        with explicit pivoting. The pivot-swap sign is the **Class-K** pin-slot
        (an integer ``±1`` flipped on each row swap), never an ALU ``abs()``; the
        determinant is ``sign · ∏ pivots`` — exact, bigint, no float."""
        if self.n_rows != self.n_cols:
            raise ValueError(
                f"QMat.det requires a square matrix; got {self.shape}")
        n = self.n_rows
        R = [list(r) for r in self._rows]
        sign = 1                                      # Class-K pin-slot (±1)
        prod = _Q_ONE
        for c in range(n):
            piv = None
            for rr in range(c, n):
                if R[rr][c] != 0:
                    piv = rr
                    break
            if piv is None:
                return _Q_ZERO                        # a zero column ⇒ singular
            if piv != c:
                R[c], R[piv] = R[piv], R[c]
                sign = -sign                          # Class-K sign-flip on swap
            pivot = R[c][c]
            prod = prod * pivot
            for rr in range(c + 1, n):
                if R[rr][c] != 0:
                    f = R[rr][c] / pivot
                    R[rr] = [R[rr][j] - f * R[c][j] for j in range(n)]
        return prod * Q(sign, 1)

    def inverse(self) -> "QMat":
        """The EXACT inverse (square nonsingular) via ``[A | I]`` Gauss-Jordan:
        row-reduce the augmented matrix; the left half becomes ``I`` iff ``A`` is
        invertible, and the right half is then ``A⁻¹``. Raises ``ValueError`` on a
        singular matrix. Exact, bigint, no float."""
        if self.n_rows != self.n_cols:
            raise ValueError(
                f"QMat.inverse requires a square matrix; got {self.shape}")
        n = self.n_rows
        ident = [[_Q_ONE if i == j else _Q_ZERO for j in range(n)]
                 for i in range(n)]
        aug = [list(self._rows[i]) + ident[i] for i in range(n)]
        R, pivot_cols, _prc = _rref_augmented(aug, n)
        if pivot_cols != list(range(n)):
            raise ValueError("QMat.inverse: matrix is singular (not invertible)")
        inv_rows = tuple(tuple(R[i][n:]) for i in range(n))
        return QMat.__new__(QMat)._init_from(inv_rows)

    def solve(self, b) -> "QMat":
        """Solve ``A · x = b`` EXACTLY (``A`` = ``self``). ``b`` is a ``QMat``
        column (or RHS block) or a nested/flat sequence coerced to one. Returns
        ``x`` as a ``QMat`` of shape ``(n_cols, b_cols)``. Raises ``ValueError`` if
        ``A`` is not square, the shapes do not conform, or the system is singular /
        inconsistent. Exact ``[A | b]`` Gauss-Jordan, bigint, no float."""
        if self.n_rows != self.n_cols:
            raise ValueError(
                f"QMat.solve requires a square A; got {self.shape}")
        n = self.n_rows
        B = _as_column_block(b, n)
        b_cols = B.n_cols
        aug = [list(self._rows[i]) + list(B._rows[i]) for i in range(n)]
        R, pivot_cols, _prc = _rref_augmented(aug, n)
        if pivot_cols != list(range(n)):
            raise ValueError(
                "QMat.solve: A is singular — no unique solution (use nullspace / "
                "lstsq for the rank-deficient case).")
        x_rows = tuple(tuple(R[i][n:n + b_cols]) for i in range(n))
        return QMat.__new__(QMat)._init_from(x_rows)

    def nullspace(self) -> List["QMat"]:
        """An EXACT basis of ``ker(A)`` (``A`` = ``self``) — a ``list`` of ``QMat``
        COLUMN vectors (each ``n_cols × 1``) spanning the kernel exactly, one per
        free column of the RREF (the classical free-variable construction). The
        list is empty iff ``A`` has full column rank. Exact over ℚ, bigint."""
        R, pivot_cols, pivot_row_of_col = _rref_augmented(self._rows, self.n_cols)
        n = self.n_cols
        free_cols = [c for c in range(n) if c not in pivot_row_of_col]
        basis: List["QMat"] = []
        for fc in free_cols:
            v = [_Q_ZERO] * n
            v[fc] = _Q_ONE
            for c in pivot_cols:
                pr = pivot_row_of_col[c]
                v[c] = -R[pr][fc]
            col = tuple((v[i],) for i in range(n))    # n×1 column QMat
            basis.append(QMat.__new__(QMat)._init_from(col))
        return basis

    # ── the boundary collapse — the ONE rotation (ALU → FPU) ────────────────
    def to_mat(self):
        """Collapse to a float64 :class:`srmech.amsc.mat.Mat` — the single
        ALU→FPU rotation / "rotation last" (the body stayed exact ``Q`` until
        here). This is the ONLY place ``float()`` appears in the carrier, the
        exact analogue of :meth:`srmech.amsc.q.Q.__float__` /
        :meth:`srmech.amsc.qalg.Qalg.to_complex` — the opt-in display boundary."""
        from .mat import Mat
        return Mat.from_rows(
            [[float(q) for q in r] for r in self._rows], is_complex=False)


# ── the shared exact Gauss-Jordan kernel (rref / rank / inverse / solve /
#    nullspace all build on it; same elimination as qm.triality /
#    matrix_cascades._qalg_rref, but over plain Q) ───────────────────────────
def _rref_augmented(rows, n_cols_left: int):
    """Exact reduced row-echelon form of a (possibly augmented) ``Q`` matrix.

    ``rows`` is a sequence of equal-length sequences of ``Q``; ``n_cols_left`` is
    how many LEADING columns participate in the pivot search (the rest are an
    appended block — the ``I`` of ``[A|I]`` for inverse, the ``b`` of ``[A|b]`` for
    solve — carried along but never pivoted on). Returns
    ``(R, pivot_cols, pivot_row_of_col)``: the reduced rows (``list[list[Q]]``),
    the pivot columns (in increasing order), and the column→pivot-row map.

    Pivot selection is exact (``Q != 0`` — the first nonzero entry at or below the
    current row), never a float tolerance. Bigint exact; no magnitude ceiling."""
    R = [list(r) for r in rows]
    n_rows = len(R)
    total_cols = len(R[0]) if R else 0
    pivot_cols: List[int] = []
    pivot_row_of_col = {}
    r = 0
    for c in range(n_cols_left):
        piv = None
        for rr in range(r, n_rows):
            if R[rr][c] != 0:                         # exact pivot, Class-K nonzero
                piv = rr
                break
        if piv is None:
            continue
        R[r], R[piv] = R[piv], R[r]
        pivot = R[r][c]
        inv = _Q_ONE / pivot                          # exact rational reciprocal
        R[r] = [R[r][j] * inv for j in range(total_cols)]
        for rr in range(n_rows):
            if rr != r and R[rr][c] != 0:
                f = R[rr][c]
                R[rr] = [R[rr][j] - f * R[r][j] for j in range(total_cols)]
        pivot_cols.append(c)
        pivot_row_of_col[c] = r
        r += 1
        if r == n_rows:
            break
    return R, pivot_cols, pivot_row_of_col


def _as_column_block(b, n: int) -> "QMat":
    """Coerce a ``solve`` RHS ``b`` to an ``n × k`` ``QMat`` block. Accepts a
    ``QMat`` (``n × k``), a nested sequence (``n × k``), or a FLAT sequence of
    length ``n`` (treated as a single column ``n × 1``)."""
    if isinstance(b, QMat):
        if b.n_rows != n:
            raise ValueError(
                f"QMat.solve: b has {b.n_rows} rows, expected {n}")
        return b
    seq = list(b)
    if seq and isinstance(seq[0], (list, tuple)):
        block = QMat.from_rows(seq)
    else:
        block = QMat.from_rows([[x] for x in seq])    # flat → column
    if block.n_rows != n:
        raise ValueError(
            f"QMat.solve: b has {block.n_rows} rows, expected {n}")
    return block
