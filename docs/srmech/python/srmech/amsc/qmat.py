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


def _native():
    """The native ``_native`` module IF the rc40 ``srmech_qmat_*`` peer is present,
    else ``None`` — so the carrier dispatches to C when available and falls cleanly
    to the pure-Python Gauss-Jordan body (the complete alternative + the parity
    oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    return nat if nat.has_native_qmat() else None


def _row_major_pairs(rows) -> List[Tuple[int, int]]:
    """Flatten a tuple-of-tuples of ``Q`` to a ROW-MAJOR ``(num, den)`` int-pair
    list (the C qmat marshalling house form)."""
    return [(q._n, q._d) for r in rows for q in r]


def _qmat_from_flat(pairs, n_rows: int, n_cols: int) -> "QMat":
    """Rebuild a ``QMat`` from a flat row-major ``(num, den)`` pair list."""
    rows = tuple(
        tuple(Q(pairs[r * n_cols + c][0], pairs[r * n_cols + c][1])
              for c in range(n_cols))
        for r in range(n_rows))
    return QMat.__new__(QMat)._init_from(rows)


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
                f"QMat matmul inner-dim mismatch: {self.shape} · {other.shape}")
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
        nat = _native()
        if nat is not None and self.n_rows and self.n_cols:
            try:
                res = nat.qmat_rref_c(_row_major_pairs(self._rows),
                                      self.n_rows, self.n_cols)
                if res is not None:
                    pairs, _rank, _piv = res
                    return _qmat_from_flat(pairs, self.n_rows, self.n_cols)
            except (RuntimeError, OverflowError, ValueError):
                pass                                 # fall to the pure path
        R, _piv, _prc = _rref_augmented(self._rows, self.n_cols)
        return QMat.__new__(QMat)._init_from(tuple(tuple(r) for r in R))

    def rref_crt(self):
        """The EXACT reduced row-echelon form via **CRT re-fibration** — byte-
        identical to :meth:`rref` but at *bounded* memory instead of the dense
        Gauss-Jordan's Hadamard-envelope arena.

        The dense :meth:`rref` grows numerators + denominators at every pivot, so
        its malloc-free arena must reserve the worst-case fraction envelope (the
        rc44 measurement: ~1.5 GB for a 17-bit answer on the order-2 Franel
        484x154 system). This method instead re-fibrates the solve onto the
        Chinese Remainder Theorem (Class I modular fibers / Class J primes /
        Class N rational reconstruction):

        1. **Reduce per prime.** For an odd prime ``p`` (``2 < p < 2**31``) reduce
           each entry ``num/den`` to ``(num * den^{-1}) mod p`` via the Class-I
           :func:`srmech.amsc.cyclic.mod_inv`. A prime dividing ANY denominator is
           *skipped* (the modular image of that entry is undefined).
        2. **Eliminate (swell-free).** Run the bounded machine-int
           :func:`srmech.amsc.modular_linalg.gf_rref` over GF(p) -> the RREF mod
           ``p`` + its rank + pivot columns. No fraction growth, no bignum.
        3. **Consensus rank / unlucky-prime discard.** The true rank is the
           CONSENSUS = the maximum ``(rank, pivots)`` seen (a prime that drops a
           pivot reduces the modular rank; it never raises it). Any prime whose
           ``(rank, pivots)`` disagrees with the running consensus is an *unlucky
           prime* and is discarded from the CRT (the genuine ``p=7`` Franel drop).
        4. **Combine + reconstruct once.** For each entry position
           :func:`srmech.amsc.modular_linalg.crt_combine` the per-prime residues
           -> a residue mod ``prod(good primes)``; then the Class-N
           :func:`srmech.amsc.rational.rational_reconstruct` recovers the exact
           ``Q`` entry.
        5. **Early termination (stabilization).** Keep adding good primes until the
           reconstructed rational matrix is IDENTICAL across two consecutive good-
           prime additions (the standard CRT early-termination). The dense
           Hadamard bound is not needed — stabilization is the stop.

        Returns the same shape as :meth:`rref` (the exact-Q RREF as a ``QMat``).
        Pure-int / pure-Q, bigint, no ``abs()`` (Class-K), no float, no numpy, no
        ``math``. Composes the C-backed ``gf_rref`` / ``crt_combine`` /
        ``rational_reconstruct`` / ``next_prime`` ops (``composition_of_c``)."""
        return _rref_crt(self)

    def rank(self, *, method: str = "auto") -> int:
        """The EXACT rank = the pivot count of the RREF (exact over ℚ).

        ``method`` selects the solve path (rc47): ``"auto"`` (default — CRT for a
        large system, dense for a small one), ``"dense"``, or ``"crt"``. All three
        give the identical exact rank; ``"crt"`` runs at bounded memory."""
        nat = _native()
        if nat is not None and method != "crt" and self.n_rows and self.n_cols:
            try:
                rk = nat.qmat_rank_c(_row_major_pairs(self._rows),
                                     self.n_rows, self.n_cols)
                if rk is not None:
                    return rk
            except (RuntimeError, OverflowError, ValueError):
                pass
        if (self.n_rows and self.n_cols
                and _use_crt(self.n_rows, self.n_cols, method)):
            out = _rref_crt_rows(self._rows, self.n_rows, self.n_cols, self.n_cols)
            if out is not None:
                return len(out[1])                # CRT pivot count = exact rank
        _R, pivot_cols, _prc = _rref_augmented(self._rows, self.n_cols)
        return len(pivot_cols)

    def det(self, *, method: str = "auto") -> Q:
        """The EXACT determinant as a ``Q`` (square only) via Gauss elimination
        with explicit pivoting. The pivot-swap sign is the **Class-K** pin-slot
        (an integer ``±1`` flipped on each row swap), never an ALU ``abs()``; the
        determinant is ``sign · ∏ pivots`` — exact, bigint, no float.

        ``method`` selects the solve path (rc47): ``"auto"`` (default — CRT for a
        large matrix, dense for a small one), ``"dense"``, or ``"crt"``. The CRT
        path computes ``det mod p`` over the descending prime field (each a
        swell-free GF(p) elimination), CRT-combines the modular determinants, and
        rational-reconstructs ONCE — byte-identical to the dense determinant at
        bounded memory."""
        if self.n_rows != self.n_cols:
            raise ValueError(
                f"QMat.det requires a square matrix; got {self.shape}")
        n = self.n_rows
        if n and _use_crt(n, n, method):
            crt = _det_crt(self._rows, n)
            if crt is not None:
                return crt
        nat = _native()
        if nat is not None and method != "crt" and n:
            try:
                pair = nat.qmat_det_c(_row_major_pairs(self._rows), n)
                if pair is not None:
                    return Q(pair[0], pair[1])
            except (RuntimeError, OverflowError, ValueError):
                pass
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

    def inverse(self, *, method: str = "auto") -> "QMat":
        """The EXACT inverse (square nonsingular) via ``[A | I]`` Gauss-Jordan:
        row-reduce the augmented matrix; the left half becomes ``I`` iff ``A`` is
        invertible, and the right half is then ``A⁻¹``. Raises ``ValueError`` on a
        singular matrix. Exact, bigint, no float.

        ``method`` selects the solve path (rc47): ``"auto"`` (default — CRT for a
        large matrix, dense for a small one), ``"dense"``, or ``"crt"``. The CRT
        path reduces ``[A|I]`` at bounded memory; byte-identical to the dense
        inverse."""
        if self.n_rows != self.n_cols:
            raise ValueError(
                f"QMat.inverse requires a square matrix; got {self.shape}")
        n = self.n_rows
        ident = [[_Q_ONE if i == j else _Q_ZERO for j in range(n)]
                 for i in range(n)]
        aug = [list(self._rows[i]) + ident[i] for i in range(n)]
        if n and _use_crt(n, 2 * n, method):
            out = _rref_crt_rows(tuple(tuple(r) for r in aug), n, 2 * n, n)
            if out is not None:
                R, pivot_cols, _prc = out
                if pivot_cols != list(range(n)):
                    raise ValueError(
                        "QMat.inverse: matrix is singular (not invertible)")
                inv_rows = tuple(tuple(R[i][n:]) for i in range(n))
                return QMat.__new__(QMat)._init_from(inv_rows)
        nat = _native()
        if nat is not None and method != "crt" and n:
            try:
                res = nat.qmat_inverse_c(_row_major_pairs(self._rows), n)
                if res is not None:
                    pairs, singular = res
                    if singular:
                        raise ValueError(
                            "QMat.inverse: matrix is singular (not invertible)")
                    return _qmat_from_flat(pairs, n, n)
            except (RuntimeError, OverflowError):
                pass
        R, pivot_cols, _prc = _rref_augmented(aug, n)
        if pivot_cols != list(range(n)):
            raise ValueError("QMat.inverse: matrix is singular (not invertible)")
        inv_rows = tuple(tuple(R[i][n:]) for i in range(n))
        return QMat.__new__(QMat)._init_from(inv_rows)

    def solve(self, b, *, method: str = "auto") -> "QMat":
        """Solve ``A · x = b`` EXACTLY (``A`` = ``self``). ``b`` is a ``QMat``
        column (or RHS block) or a nested/flat sequence coerced to one. Returns
        ``x`` as a ``QMat`` of shape ``(n_cols, b_cols)``. Raises ``ValueError`` if
        ``A`` is not square, the shapes do not conform, or the system is singular /
        inconsistent. Exact ``[A | b]`` Gauss-Jordan, bigint, no float.

        ``method`` selects the solve path (rc47): ``"auto"`` (default — CRT for a
        large system, dense for a small one), ``"dense"``, or ``"crt"``. The CRT
        path reduces ``[A|b]`` at bounded memory; byte-identical to the dense
        solve."""
        if self.n_rows != self.n_cols:
            raise ValueError(
                f"QMat.solve requires a square A; got {self.shape}")
        n = self.n_rows
        B = _as_column_block(b, n)
        b_cols = B.n_cols
        if n and _use_crt(n, n + b_cols, method):
            aug = [list(self._rows[i]) + list(B._rows[i]) for i in range(n)]
            out = _rref_crt_rows(tuple(tuple(r) for r in aug), n, n + b_cols, n)
            if out is not None:
                R, pivot_cols, _prc = out
                if pivot_cols != list(range(n)):
                    raise ValueError(
                        "QMat.solve: A is singular — no unique solution (use "
                        "nullspace / lstsq for the rank-deficient case).")
                x_rows = tuple(tuple(R[i][n:n + b_cols]) for i in range(n))
                return QMat.__new__(QMat)._init_from(x_rows)
        nat = _native()
        if nat is not None and method != "crt" and n:
            try:
                res = nat.qmat_solve_c(_row_major_pairs(self._rows), n,
                                       _row_major_pairs(B._rows), b_cols)
                if res is not None:
                    pairs, singular = res
                    if singular:
                        raise ValueError(
                            "QMat.solve: A is singular — no unique solution (use "
                            "nullspace / lstsq for the rank-deficient case).")
                    return _qmat_from_flat(pairs, n, b_cols)
            except (RuntimeError, OverflowError):
                pass
        aug = [list(self._rows[i]) + list(B._rows[i]) for i in range(n)]
        R, pivot_cols, _prc = _rref_augmented(aug, n)
        if pivot_cols != list(range(n)):
            raise ValueError(
                "QMat.solve: A is singular — no unique solution (use nullspace / "
                "lstsq for the rank-deficient case).")
        x_rows = tuple(tuple(R[i][n:n + b_cols]) for i in range(n))
        return QMat.__new__(QMat)._init_from(x_rows)

    def nullspace(self, *, method: str = "auto") -> List["QMat"]:
        """An EXACT basis of ``ker(A)`` (``A`` = ``self``) — a ``list`` of ``QMat``
        COLUMN vectors (each ``n_cols × 1``) spanning the kernel exactly, one per
        free column of the RREF (the classical free-variable construction). The
        list is empty iff ``A`` has full column rank. Exact over ℚ, bigint.

        ``method`` selects the solve path (rc47): ``"auto"`` (default — CRT for a
        large system, dense for a small one), ``"dense"``, or ``"crt"``. The CRT
        path reduces ``A`` to RREF at bounded memory; the kernel basis is
        byte-identical to the dense one."""
        nat = _native()
        if (nat is not None and method != "crt"
                and not (self.n_rows and self.n_cols
                         and _use_crt(self.n_rows, self.n_cols, method))
                and self.n_rows and self.n_cols):
            try:
                cols = nat.qmat_nullspace_c(_row_major_pairs(self._rows),
                                            self.n_rows, self.n_cols)
                if cols is not None:
                    basis: List["QMat"] = []
                    for vec in cols:
                        col = tuple((Q(p[0], p[1]),) for p in vec)
                        basis.append(QMat.__new__(QMat)._init_from(col))
                    return basis
            except (RuntimeError, OverflowError, ValueError):
                pass
        R, pivot_cols, pivot_row_of_col = _nullspace_rref(self, method)
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


# ── the CRT re-fibration of the exact-ℚ RREF (rc46) ─────────────────────────
# rref_crt's body: solve mod several bounded primes (each a swell-free gf_rref),
# CRT-combine + rational-reconstruct once → the exact-ℚ RREF byte-identical to the
# dense rref but at bounded memory (no Hadamard-envelope arena). Composes the
# C-backed gf_rref / crt_combine / rational_reconstruct / next_prime ops.

# The GF(p) field ceiling: gf_rref requires 2 < p < 2**31 (so a*b fits uint64).
_GF_P_CEILING: int = 1 << 31
# Seed for the descending prime walk — the largest odd value below the ceiling.
# We walk DOWNWARD from here so every emitted prime is a valid GF(p) modulus.
_GF_P_SEED: int = _GF_P_CEILING - 1

# Auto-by-size dispatch threshold (rc47). The dense exact-ℚ Gauss-Jordan grows the
# numerators + denominators at EVERY pivot, so its malloc-free arena must reserve
# the Hadamard worst-case fraction envelope — GB-scale on the order-2 Franel
# 484x154 / order-3 2790x780 Zeilberger systems. CRT solves mod several bounded
# primes (zero coefficient swell) and reconstructs once → bounded memory. For
# small systems the dense path is faster (no per-prime overhead, no Wang-bound
# stabilization loop), so the `method="auto"` default uses CRT only once a system
# is large enough that the dense fraction-swell is the bottleneck. The crossover
# is cell-count based: below the threshold the dense pivot growth is cheap; above
# it the bounded CRT path wins decisively. Opt in / out explicitly with
# `method="crt"` / `method="dense"`.
_CRT_AUTO_CELL_THRESHOLD: int = 4096


def _use_crt(n_rows: int, n_cols: int, method: str) -> bool:
    """Decide the solve path for the size-`method` dispatch (rc47).

    ``method="dense"`` → always the dense Gauss-Jordan; ``method="crt"`` → always
    the bounded CRT re-fibration; ``method="auto"`` (the default) → CRT once the
    cell count ``n_rows·n_cols`` exceeds :data:`_CRT_AUTO_CELL_THRESHOLD` (where the
    dense Hadamard fraction-swell is the wall), dense below it (faster there).
    Either path is EXACT and byte-identical — this only trades memory for speed."""
    if method == "dense":
        return False
    if method == "crt":
        return True
    if method == "auto":
        return n_rows * n_cols > _CRT_AUTO_CELL_THRESHOLD
    raise ValueError(
        f"QMat: method must be 'auto' / 'dense' / 'crt'; got {method!r}")


def _gf_primes():
    """Yield distinct odd primes ``p`` with ``2 < p < 2**31`` (valid ``gf_rref``
    moduli), largest-first. Composes the Class-J primality test (via
    :func:`srmech.amsc.primes.is_prime`) over the descending odd candidates — the
    same primitive ``next_prime`` rides, walked downward to stay inside the field
    ceiling (``next_prime`` walks UP and would immediately exceed ``2**31``)."""
    from . import primes as _primes
    cand = _GF_P_SEED
    if cand % 2 == 0:
        cand -= 1
    while cand > 2:
        if _primes.is_prime(cand):
            yield cand
        cand -= 2


def _entries_mod_p(rows, p: int):
    """Reduce every exact-``Q`` entry ``num/den`` to ``(num · den⁻¹) mod p`` over
    GF(p), or ``None`` if ``p`` divides any denominator (an *undefined* modular
    image — the prime must be skipped). Class-I ``mod_inv`` composition; the
    residues land in ``[0, p)``. Returns a list-of-lists of ``int`` residues."""
    from . import cyclic as _cyclic
    out = []
    for r in rows:
        rr = []
        for q in r:
            num, den = q._n, q._d                 # exact reduced (num, den)
            dmod = den % p
            if dmod == 0:
                return None                       # p | den ⇒ skip this prime
            inv = _cyclic.mod_inv(dmod, p)        # Class-I modular inverse
            rr.append((num % p) * inv % p)
        out.append(rr)
    return out


def _rref_crt(self) -> "QMat":
    """See :meth:`QMat.rref_crt`. Bounded-memory exact-ℚ RREF via CRT."""
    n_rows, n_cols = self.n_rows, self.n_cols
    if n_rows == 0 or n_cols == 0:
        # Degenerate: nothing to reduce — the dense rref is already trivial.
        return self.rref()
    # rc48: dispatch the WHOLE CRT solve to the single C symbol
    # srmech_qmat_rref_crt when present (one malloc-free, caller-arena,
    # answer-sized call orchestrating gf_rref / crt_combine /
    # rational_reconstruct / the descending prime walk). Byte-identical to the
    # pure path below; a non-OK C status (OVERFLOW / absent symbol) falls cleanly
    # to the pure-Python CRT body — the complete alternative + the parity oracle.
    nat = _native()
    if nat is not None and getattr(nat, "has_native_qmat_rref_crt", None) \
            and nat.has_native_qmat_rref_crt():
        try:
            res = nat.qmat_rref_crt_c(_row_major_pairs(self._rows),
                                      n_rows, n_cols)
            if res is not None:
                pairs, _rank, _piv = res
                return _qmat_from_flat(pairs, n_rows, n_cols)
        except (RuntimeError, OverflowError, ValueError):
            pass                                  # fall to the pure CRT path
    out = _rref_crt_rows(self._rows, n_rows, n_cols, n_cols)
    if out is None:
        # Exhausted the prime field without stabilizing — should not happen for a
        # finite exact-ℚ answer; fall back to the dense exact rref (still correct).
        return self.rref()                        # pragma: no cover
    rows, _piv, _prc = out
    return QMat.__new__(QMat)._init_from(rows)


def _rref_crt_rows(src_rows, n_rows: int, n_cols: int, n_cols_left: int):
    """The shared CRT-re-fibration kernel — the engine under :meth:`QMat.rref_crt`
    AND the augmented det/inverse/solve/nullspace CRT paths.

    Reduces the ``Q`` matrix ``src_rows`` (``n_rows × n_cols``) to its exact RREF
    at bounded memory, pivoting only on the leading ``n_cols_left`` columns (the
    rest — the ``I`` of ``[A|I]`` for inverse, the ``b`` of ``[A|b]`` for solve —
    ride along but are never pivoted on). Mirrors the dense :func:`_rref_augmented`
    pivot contract exactly (first nonzero ``Q != 0`` at or below the current row),
    so the returned RREF rows + pivot structure are byte-identical to the dense
    path.

    Returns ``(rows, pivot_cols, pivot_row_of_col)`` — the same triple
    :func:`_rref_augmented` returns, with ``rows`` a tuple-of-tuples of exact
    ``Q`` — or ``None`` if the prime field exhausts without stabilizing (the
    caller then falls back to the dense path; not hit for a finite exact-ℚ
    answer). Composes the Class-I ``gf_rref`` / ``crt_combine`` over the Class-J
    descending prime field, with the Class-N ``rational_reconstruct`` closing each
    entry; Class-K consensus + sign throughout. No float, no numpy, no ``math``."""
    from . import modular_linalg as _ml
    from . import rational as _rational

    n_cells = n_rows * n_cols
    consensus = None                              # (rank, tuple(pivots))
    good_residues = [[] for _ in range(n_cells)]  # per-cell residue list
    good_moduli: List[int] = []
    prev_matrix = None                            # the last reconstructed QMat rows

    for p in _gf_primes():
        residues = _entries_mod_p(src_rows, p)
        if residues is None:
            continue                              # p | some denominator — skip

        # gf_rref pivots on ALL columns; restrict the pivot search to the leading
        # n_cols_left so the RREF support matches the dense _rref_augmented (the
        # appended block carries along but never sources a pivot).
        res = _gf_rref_left(residues, p, n_cols_left, _ml)
        key = (res["rank"], tuple(res["pivots"]))

        if consensus is None:
            consensus = key
        elif key != consensus:
            # Class-K compare: a strictly-larger (rank, pivots) supersedes; an
            # equal-or-smaller disagreement is the unlucky prime → discard it.
            if _key_dominates(key, consensus):
                # A better consensus appeared: every accumulated prime so far was
                # itself unlucky relative to this one — restart the CRT on it.
                consensus = key
                good_residues = [[] for _ in range(n_cells)]
                good_moduli = []
                prev_matrix = None
            else:
                continue                          # genuine unlucky prime: discard

        # This prime agrees with the consensus — fold its RREF residues into CRT.
        flat = [res["rref"][r][c] for r in range(n_rows) for c in range(n_cols)]
        for i in range(n_cells):
            good_residues[i].append(flat[i])
        good_moduli.append(p)

        # Need >= 2 good primes before stabilization can be observed.
        if len(good_moduli) < 2:
            continue

        matrix = _reconstruct_matrix(good_residues, good_moduli, n_rows, n_cols,
                                     _ml, _rational)
        if matrix is None:
            # Reconstruction not yet within bounds for some entry — add more primes.
            continue
        if prev_matrix is not None and matrix == prev_matrix:
            # Stabilized across two consecutive good-prime additions: done.
            pivot_cols = list(consensus[1])
            pivot_row_of_col = {c: r for r, c in enumerate(pivot_cols)}
            return matrix, pivot_cols, pivot_row_of_col
        prev_matrix = matrix

    return None                                   # pragma: no cover


def _gf_rref_left(residues, p: int, n_cols_left: int, _ml):
    """A GF(p) RREF that pivots ONLY on the leading ``n_cols_left`` columns (the
    appended ``[A|I]`` / ``[A|b]`` block rides along, never sourcing a pivot) —
    the modular mirror of the dense :func:`_rref_augmented` pivot contract.

    When ``n_cols_left`` spans every column this is just :func:`gf_rref`; for a
    genuine augmentation we reduce the leading block alone to read its pivot
    support, then apply the SAME row operations to the full augmented matrix by
    reducing the whole matrix and trusting that a leading-block pivot set is
    unaffected by the trailing columns (Gauss-Jordan on ``[A|B]`` reduces ``A`` to
    its RREF regardless of ``B``). Concretely: run the full ``gf_rref`` but report
    only the pivots that fall in ``[0, n_cols_left)`` — for the augmented det /
    inverse / solve / nullspace shapes the trailing block never introduces a NEW
    leading-block pivot, so the full-matrix RREF restricted to ``A`` equals the
    dense ``_rref_augmented`` result."""
    n_total = len(residues[0]) if residues else 0
    if n_cols_left >= n_total:
        return _ml.gf_rref(residues, p)
    full = _ml.gf_rref(residues, p)
    pivots_left = [c for c in full["pivots"] if c < n_cols_left]
    return {"rref": full["rref"], "rank": len(pivots_left), "pivots": pivots_left}


def _nullspace_rref(self, method: str):
    """The RREF + pivot structure backing :meth:`QMat.nullspace` — the dense
    :func:`_rref_augmented` for a small system / ``method="dense"``, the
    bounded-memory CRT :func:`_rref_crt_rows` for a large one / ``method="crt"``.
    Returns the same ``(R, pivot_cols, pivot_row_of_col)`` triple either way (the
    CRT path is byte-identical to the dense RREF), so the free-variable kernel
    construction in the caller is unchanged."""
    if (self.n_rows and self.n_cols
            and _use_crt(self.n_rows, self.n_cols, method)):
        out = _rref_crt_rows(self._rows, self.n_rows, self.n_cols, self.n_cols)
        if out is not None:
            rows, pivot_cols, pivot_row_of_col = out
            return [list(r) for r in rows], pivot_cols, pivot_row_of_col
    return _rref_augmented(self._rows, self.n_cols)


# ── the CRT determinant (det mod p over the descending prime field) ──────────
def _det_mod_p(residues, n: int, p: int, _ml) -> int:
    """``det(A) mod p`` of the ``n×n`` residue matrix over GF(p), via a swell-free
    GF(p) Gaussian elimination tracking the pivot product + the Class-K swap sign
    (an integer ``±1`` flipped on each row swap, never an ALU ``abs()``). Returns
    the determinant residue in ``[0, p)`` (``0`` iff ``A`` is singular mod ``p``).
    Class-I modular arithmetic composing the cyclic-group primitives."""
    from .cyclic import mod_inv as _mi
    from .cyclic import mod_mul as _mm
    m = [[v % p for v in row] for row in residues]
    sign = 1                                       # Class-K pin-slot (±1)
    prod = 1
    for c in range(n):
        sel = None
        for r in range(c, n):
            if m[r][c] != 0:                       # Class-K compare-to-0
                sel = r
                break
        if sel is None:
            return 0                               # a zero column ⇒ singular mod p
        if sel != c:
            m[c], m[sel] = m[sel], m[c]
            sign = -sign                           # Class-K sign-flip on swap
        pivot = m[c][c]
        prod = _mm(prod, pivot, p)
        inv = _mi(pivot, p)
        for r in range(c + 1, n):
            if m[r][c] == 0:
                continue
            factor = _mm(m[r][c], inv, p)
            for j in range(c, n):
                sub = _mm(m[c][j], factor, p)
                m[r][j] = (m[r][j] + (p - sub)) % p
    det = _mm(prod, sign % p, p)                   # fold the ±1 sign into [0,p)
    return det


def _det_crt(src_rows, n: int):
    """The exact-ℚ determinant via CRT (rc47, the bounded-memory ``method="crt"``
    path). Computes ``det mod p`` over the descending GF(p) prime field (each a
    swell-free :func:`_det_mod_p`), CRT-combines the modular determinants
    (:func:`crt_combine`), and rational-reconstructs ONCE
    (:func:`rational_reconstruct`) — byte-identical to the dense determinant at
    bounded memory. Returns the exact :class:`~srmech.amsc.q.Q`, or ``None`` if the
    prime field exhausts without stabilizing (not hit for a finite answer)."""
    from . import modular_linalg as _ml
    from . import rational as _rational

    good_residues: List[int] = []
    good_moduli: List[int] = []
    prev = None
    for p in _gf_primes():
        residues = _entries_mod_p(src_rows, p)
        if residues is None:
            continue                               # p | some denominator — skip
        good_residues.append(_det_mod_p(residues, n, p, _ml))
        good_moduli.append(p)
        if len(good_moduli) < 2:
            continue
        combined = _ml.crt_combine(good_residues, good_moduli)
        pq = _rational.rational_reconstruct(combined["residue"], combined["modulus"])
        if pq is None:
            continue                               # not yet within the Wang bound
        cur = Q(pq[0], pq[1])
        if prev is not None and cur == prev:
            return cur                             # stabilized across two primes
        prev = cur
    return None                                    # pragma: no cover


def _key_dominates(key, other) -> bool:
    """Class-K comparison of two ``(rank, pivots)`` consensus keys: ``key``
    dominates ``other`` iff its rank is strictly larger (a higher-rank modular
    image is the truer one; a lucky prime sees full rank, an unlucky one drops a
    pivot). Ties on rank with differing pivots cannot both be the true RREF
    support, so the larger rank is the sole tie-break used here."""
    return key[0] > other[0]


def _reconstruct_matrix(good_residues, good_moduli, n_rows, n_cols,
                        _ml, _rational):
    """CRT-combine each cell's residue list (mod ∏ good_moduli) then
    rational-reconstruct the exact ``Q`` entry. Returns the tuple-of-tuples of
    ``Q`` (the candidate RREF rows), or ``None`` if any cell does not reconstruct
    within the Wang bound at the current modulus (signal: add more primes)."""
    cells: List[Q] = []
    for reslist in good_residues:
        combined = _ml.crt_combine(reslist, good_moduli)
        pq = _rational.rational_reconstruct(combined["residue"], combined["modulus"])
        if pq is None:
            return None
        cells.append(Q(pq[0], pq[1]))
    rows = tuple(tuple(cells[r * n_cols + c] for c in range(n_cols))
                 for r in range(n_rows))
    return rows


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
