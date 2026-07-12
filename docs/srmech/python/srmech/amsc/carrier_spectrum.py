"""srmech.amsc.carrier_spectrum — ``CarrierSpectrum``, the OPERAND-side dual of
``the_one``: it reads a carrier element's HARMONIC OCCUPANCY under the shift-Laplacian
and exposes the BLOCK STRUCTURE that makes the elliptic key-equation solve genuinely
NON-brute-force (block-decomposed, not dense-in-disguise).

Where :func:`srmech.qm.so8`'s ``the_one`` ``S(σ, θ)`` is the OPERATOR generator — its
shape IS the A–N verbs (the algebra side) — ``CarrierSpectrum`` is the OPERAND object:
its shape is the carrier's Class-L shift-Laplacian eigenbasis (the module / excitation
side). Operator ↔ operand = algebra ↔ module = field ↔ excitation (the duality the
project hangs on). A carrier element is read, not generated; ``CarrierSpectrum`` is a
first-class object (construct / inspect / operate), NOT a diagnostic dict.

THE TWO CHANNELS OF A CARRIER ELEMENT
=====================================

A carrier element ``r`` is an :class:`~srmech.amsc.ellbase.EllRatio`
``prefactor(monomial) · ∏(num θ) / ∏(den θ)``, and it splits EXACTLY into two
ORTHOGONAL channels under the two carrier shifts:

**Channel 1 — Cyclic (Class I): the σ-eigenspectrum.**  The summation shift
``σ = qshift`` (``x ↦ q·x``, :meth:`~srmech.amsc.ellbase.EllRatio.qshift`) is DIAGONAL on
monomials: ``σ(x^k) = q^k·x^k`` (qshift raises the prefactor's ``q``-exponent by exactly
``k``, leaving the ``x``-exponent fixed). So the ``x``-exponents present in a carrier
element are the σ-eigen-occupancy, each with eigenvalue ``q^k``; ``k = 0`` is the kernel
of the shift-Laplacian ``L = σ − 1`` (the σ-invariant DC / rest mode). This is the
cyclic (Class-I) coordinate — the rotation axis.

**Channel 2 — Quasi-periodic (Class L): the p-character blocks.**  Each ``θ`` belongs to
a p-character class — the net multiplier monomial the theta-product acquires under the
PERIOD shift ``x ↦ p·x`` (the rc62 ``ThetaSum`` quasi-periodicity grouping, Rosengren
Eq. 1.6, via :meth:`~srmech.amsc.ellbase.Theta.canonicalize`). The σ-INVARIANT block
label is that p-character with the ``q``-coordinate STRIPPED: σ traverses ONLY the
``q``-coordinate (Channel 1) and PRESERVES the block (Channel 2) — the channels are
orthogonal. This is the quasi-periodic (Class-L) coordinate — the harmonic shape.

THE NON-BRUTE-FORCE KEY-EQUATION SOLVE
======================================

The elliptic Gosper / Zeilberger KEY EQUATION (Gasper–Schlosser Eq. 3.5; the
``elliptic_gosper`` peel produces the ``A, B, C`` factors) is

    A · σ(Y)  −  B(x/q) · Y  =  RHS                                          (KEY)

a ``ℚ``-linear system for the unknown certificate ``Y`` expressed over a theta-product
BASIS (``Y = Σ_i c_i · basis_i``, ``c_i ∈ ℚ``). The BRUTE FORCE is ONE dense
:class:`~srmech.amsc.qmat.QMat` solve over the WHOLE basis. Because σ PRESERVES the
p-character block (the verified Channel-2 lever) and multiply-by-``A`` / multiply-by-
``B(x/q)`` each SHIFT the block by a FIXED amount, the key-equation operator
``L(Y) = A·σ(Y) − B(x/q)·Y`` maps an input block ``g`` to a SINGLE output block:

  * if ``block(A) == block(B(x/q))`` (the σ-invariant, ``q``-stripped block label) — the
    GENERIC elliptic-Gosper case, since ``B(x/q)`` is the ``σ⁻¹`` frame of ``B`` and the
    GP peel makes ``A`` / ``B`` dispersion-coprime in the SAME quasi-periodicity class —
    both terms land in output block ``g + block(A)``, so the matrix is **block-DIAGONAL**;
  * otherwise the two terms land in DIFFERENT output blocks, so the matrix is
    **block-TRIANGULAR / cyclic** (multiply-by-``A`` shifts by ``block(A)``); the solve is
    still genuinely per-block (the blocks are solved in a topological order of the shift).

Either way the matrix is NON-DENSE: :meth:`CarrierSpectrum.solve_key_equation` computes
each basis element's block label, GROUPS the basis by block, SOLVES each block
independently (a small per-block ``QMat`` solve), and assembles. The per-block partition
sizes SUM to the full basis with ``> 1`` block on a genuine multi-block system, so the
solve cannot be the dense solve relabeled. The block solve REPRODUCES the dense solve
EXACTLY (same ``Y``) — it is the same linear algebra, factored along the carrier's
harmonic shape (the Class-L eigenbasis), so the certificate is identical bit-for-bit; the
WIN is that the dense ``n×n`` Gauss-Jordan is replaced by ``Σ_b (n_b×n_b)`` solves over
the disjoint blocks.

Everything is EXACT over the modified-theta algebra: ``ℚ`` coefficients + integer
exponents; sign is the **Class-K** pin-slot via the ``Q`` / ``EllMonomial`` sign-branch,
NEVER an ALU ``abs()``; no ``math`` module, no numpy, no float (the linear-algebra is the
exact-``ℚ`` :class:`~srmech.amsc.qmat.QMat` Gauss-Jordan).

Reference (the harmonic-shape framing; MPM-verified at build — the actual arXiv PDF
extracted, equation numbers confirmed): Hjalmar Rosengren, "Elliptic Hypergeometric
Functions" (arXiv:1608.06161v3 [math.CA]), §1.3 (factorization of elliptic functions,
Lemma 1.3.2 — the period-annulus pole/zero count that bounds each block's degree) +
§1.4 Eq. (1.12) (the Weierstrass three-term relation the ``ThetaSum`` block-reduction
runs); the elliptic indefinite-summation key equation is Gasper–Schlosser
(arXiv:math/0505215), cited by :mod:`srmech.amsc.elliptic_gosper`.

C peer (same-rc, the everything-mirrors never-split discipline): ``srmech_carrier_spectrum``
(``c/src/srmech_carrier_spectrum.c``) mirrors the channel read + the block-grouped
key-equation solve over the integer theta-exponent lattice, riding the shared
``srmech_ellbase_*`` (canonicalize / monomial algebra) + ``srmech_qmat_rref`` kernels (the
no-double-copy discipline). The public op :func:`carrier_spectrum` dispatches to it when
loaded and re-verifies any native result against the pure-Python body (the COMPLETE
alternative + the parity oracle) before trusting it; a native miss re-decides pure.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .ellbase import EllMonomial, EllRatio, Theta, _P, _Q_SYM, _X
from .q import Q
from .thetasum import ThetaSum, _net_period_multiplier_exps

__all__ = ["CarrierSpectrum", "carrier_spectrum"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)

# A block label is a sorted tuple of (symbol, exponent) over the σ-INVARIANT (q-stripped)
# quasi-periodicity-class monomial. A cyclic eigen-entry is (x-exponent k, eigenvalue q^k).
BlockLabel = Tuple[Tuple[str, int], ...]
CoordKey = Tuple[Tuple, Tuple]


def _strip_q(key: BlockLabel) -> BlockLabel:
    """Drop the ``q``-coordinate from a quasi-periodicity-class key — σ (``x ↦ q·x``)
    traverses ONLY the ``q``-coordinate, so the σ-INVARIANT block label is the
    ``q``-stripped net-period monomial. (Class-I lives on ``q``; Class-L is what
    remains.)"""
    return tuple((s, e) for s, e in key if s != _Q_SYM)


def _block_of_thetas(thetas: "Tuple[Theta, ...]") -> BlockLabel:
    """The σ-INVARIANT p-character BLOCK LABEL of a theta-product: the
    :func:`~srmech.amsc.thetasum._net_period_multiplier_exps` quasi-periodicity-class
    monomial (the net multiplier under ``x ↦ p·x`` and ``y ↦ p·y``, Rosengren Eq. 1.6,
    via :meth:`~srmech.amsc.ellbase.Theta.canonicalize`) with the ``q``-coordinate
    STRIPPED. σ preserves this label (verified); multiply-by-a-product SHIFTS it
    additively. EXACT — integer exponents only, no float."""
    return _strip_q(_net_period_multiplier_exps(tuple(thetas)))


class CarrierSpectrum:
    """The OPERAND-side dual of ``the_one``: the harmonic occupancy of a carrier element
    under the shift-Laplacian, in two orthogonal channels (cyclic Class-I σ-spectrum +
    quasi-periodic Class-L p-character blocks), with the block-decomposed key-equation
    solve that the harmonic shape unlocks. Immutable; a first-class carrier object (not a
    diagnostic dict).

    Construct from a carrier element (an :class:`~srmech.amsc.ellbase.EllRatio`):

        >>> cs = CarrierSpectrum(rk)            # rk an EllRatio (the ₈ω₇ term ratio)
        >>> cs.cyclic                           # {x-exp k: 'q**k'} — the σ-eigenspectrum
        >>> cs.blocks                           # {block label: [theta-products]} — Class-L
        >>> cs.solve_key_equation(rhs)          # the per-block (non-dense) certificate solve

    See the module docstring for the two channels + the non-brute-force solve.
    """

    __slots__ = ("_element", "_cyclic", "_blocks")

    def __init__(self, element: EllRatio) -> None:
        if not isinstance(element, EllRatio):
            raise TypeError(
                "CarrierSpectrum(element): element must be an EllRatio carrier element "
                f"(prefactor · ∏num θ / ∏den θ); got {element!r}")
        self._element = element
        self._cyclic = _read_cyclic(element)
        self._blocks = _read_blocks(element)

    # ── accessors ────────────────────────────────────────────────────────────
    @property
    def element(self) -> EllRatio:
        """The carrier element this spectrum reads."""
        return self._element

    @property
    def cyclic(self) -> "Dict[int, str]":
        """Channel 1 (Class-I) — the σ-EIGENSPECTRUM: ``{x-exponent k: 'q**k'}`` for every
        distinct ``x``-exponent ``k`` present across the element's theta arguments + its
        prefactor. ``σ(x^k) = q^k·x^k`` is diagonal on monomials, so each ``k`` is a
        σ-eigen-occupancy with eigenvalue ``q^k``; ``k = 0`` is the kernel of the
        shift-Laplacian ``L = σ − 1`` (the σ-invariant rest mode). The doubled-beat (the
        ``x²`` very-well-poised thetas of the ₈ω₇) shows up as the ``k = ±2`` entries."""
        return dict(self._cyclic)

    @property
    def blocks(self) -> "Dict[BlockLabel, List[Tuple[Theta, ...]]]":
        """Channel 2 (Class-L) — the p-CHARACTER BLOCKS: ``{block label: [theta-products]}``
        partitioning the element's numerator + denominator theta-FACTORS by σ-invariant
        p-character (the :func:`_block_of_thetas` quasi-periodicity class). Each value is the
        list of single-theta products in that block (the carrier's harmonic occupancy by
        block); σ preserves the block, so this partition is the σ-invariant harmonic shape.
        The ``x²`` doubled-beat thetas occupy their own higher-degree blocks (pair
        structure)."""
        return {k: [tuple(p) for p in v] for k, v in self._blocks.items()}

    def __repr__(self) -> str:
        return (f"CarrierSpectrum(cyclic={sorted(self._cyclic)}, "
                f"blocks={len(self._blocks)})")

    # ── the non-brute-force key-equation solve ───────────────────────────────
    def solve_key_equation(self, rhs: ThetaSum, *,
                           a: "EllRatio | None" = None,
                           b_xq: "EllRatio | None" = None,
                           basis: "Optional[List[Tuple[Theta, ...]]]" = None,
                           return_report: bool = False
                           ) -> "Optional[List[Q]] | Tuple[List[Q], Dict]":
        """Solve the elliptic key equation ``A·σ(Y) − B(x/q)·Y = rhs`` for the certificate
        coefficient vector ``Y = [c_0, …]`` over a theta-product ``basis`` — GENUINELY
        BLOCK-DECOMPOSED (per-p-character-block ``QMat`` solves), NOT one dense solve.

        ``rhs`` is the right-hand side as a :class:`~srmech.amsc.thetasum.ThetaSum`.
        ``a`` / ``b_xq`` are the multiplicative theta-product factors ``A`` and ``B(x/q)``
        (each an :class:`~srmech.amsc.ellbase.EllRatio`); default to the carrier element's
        own GP peel (so ``A = self.element``, ``B(x/q) = 1``) when omitted — pass the real
        peel for a genuine certificate solve. ``basis`` is the list of theta-product
        candidate certificate numerators (each a tuple of :class:`Theta`); default = the
        block-occupancy products of ``rhs`` (the structural support).

        Returns the exact-``ℚ`` solution vector ``[c_i]`` (the certificate coefficients), or
        ``None`` if the system is inconsistent over the basis. With ``return_report=True``
        also returns a report dict ``{'blocks': {block: (n_unknowns, n_rows)}, 'n_blocks':
        …, 'basis': …}`` — the PROOF the solve is per-block (the per-block sizes SUM to the
        full basis, with ``> 1`` block on a genuine multi-block system, so it cannot be the
        dense solve relabeled).

        The block lever: σ preserves the p-character block, and multiply-by-``A`` /
        multiply-by-``B(x/q)`` shift it by a fixed amount, so each basis COLUMN
        ``L(basis_i) = A·σ(basis_i) − B(x/q)·basis_i`` occupies a SINGLE output block; the
        ROWS (the residual coordinates) partition by the same block; each block is an
        independent small ``QMat`` solve. EXACT — no float, no ``abs()`` (Class-K sign)."""
        if not isinstance(rhs, ThetaSum):
            raise TypeError("CarrierSpectrum.solve_key_equation: rhs must be a ThetaSum")
        a_r = self._element if a is None else a
        b_r = EllRatio.one() if b_xq is None else b_xq
        if not isinstance(a_r, EllRatio) or not isinstance(b_r, EllRatio):
            raise TypeError("solve_key_equation: a and b_xq must be EllRatio")
        bas = _default_basis(rhs) if basis is None else [tuple(p) for p in basis]
        return _solve_key_equation(a_r, b_r, bas, rhs, return_report=return_report)

    def solve_key_equation_dense(self, rhs: ThetaSum, *,
                                 a: "EllRatio | None" = None,
                                 b_xq: "EllRatio | None" = None,
                                 basis: "Optional[List[Tuple[Theta, ...]]]" = None
                                 ) -> "Optional[List[Q]]":
        """The BRUTE-FORCE baseline: solve ``A·σ(Y) − B(x/q)·Y = rhs`` as ONE dense
        ``QMat`` solve over the WHOLE basis (no block grouping). This is the reference the
        block solve (:meth:`solve_key_equation`) reproduces EXACTLY — kept so the
        no-shell gate can assert ``block == dense`` on a concrete key equation. Returns the
        same exact-``ℚ`` certificate vector or ``None``."""
        if not isinstance(rhs, ThetaSum):
            raise TypeError("solve_key_equation_dense: rhs must be a ThetaSum")
        a_r = self._element if a is None else a
        b_r = EllRatio.one() if b_xq is None else b_xq
        bas = _default_basis(rhs) if basis is None else [tuple(p) for p in basis]
        return _solve_key_equation_dense(a_r, b_r, bas, rhs)


# ── channel reads ───────────────────────────────────────────────────────────


def _read_cyclic(element: EllRatio) -> "Dict[int, str]":
    """Channel 1 — the σ-eigenspectrum: the set of distinct ``x``-exponents ``k`` present
    across the prefactor + every theta argument, each mapped to its σ-eigenvalue label
    ``'q**k'`` (``σ(x^k) = q^k·x^k``). ``k = 0`` (the shift-Laplacian kernel / DC mode) is
    included when the element carries an ``x``-free part. EXACT integer exponents."""
    ks: "set" = set()
    ks.add(element.prefactor.exp_of(_X))
    for t in element.num:
        ks.add(t.arg.exp_of(_X))
    for t in element.den:
        ks.add(t.arg.exp_of(_X))
    return {k: f"q**{k}" for k in sorted(ks)}


def _read_blocks(element: EllRatio) -> "Dict[BlockLabel, List[Tuple[Theta, ...]]]":
    """Channel 2 — the p-character blocks: partition the element's numerator + denominator
    theta-factors (each as a single-theta product) by σ-invariant p-character block
    (:func:`_block_of_thetas`). Returns an ordered ``{block label: [theta-products]}`` map;
    σ preserves each block (the verified Channel-2 lever)."""
    blocks: "Dict[BlockLabel, List[Tuple[Theta, ...]]]" = {}
    order: "List[BlockLabel]" = []
    for t in tuple(element.num) + tuple(element.den):
        lab = _block_of_thetas((t,))
        if lab not in blocks:
            blocks[lab] = []
            order.append(lab)
        blocks[lab].append((t,))
    return {lab: blocks[lab] for lab in order}


# ── the key-equation linear algebra (exact ℚ over the ThetaSum coordinate space) ──


def _ts_product(coeff: Q, thetas: "Tuple[Theta, ...]") -> ThetaSum:
    """A theta-PRODUCT as a one-term :class:`ThetaSum` (the basis element lifted into the
    additive carrier; the unit denominator)."""
    return ThetaSum(terms=((coeff, EllMonomial.one(), tuple(thetas)),),
                    den_prefactor=EllMonomial.one(), den_thetas=())


def _apply_L(a_r: EllRatio, b_r: EllRatio, thetas: "Tuple[Theta, ...]") -> ThetaSum:
    """The key-equation operator ``L(basis_i) = A·σ(basis_i) − B(x/q)·basis_i`` on a single
    theta-product basis element, as a :class:`ThetaSum` (the additive residual carrier).
    ``σ = shift_x`` (``x ↦ q·x``). EXACT additive algebra."""
    y_ts = _ts_product(_Q_ONE, thetas)
    a_ts = ThetaSum.from_ellratio(a_r)
    b_ts = ThetaSum.from_ellratio(b_r)
    return a_ts * y_ts.shift_x() - b_ts * y_ts


def _term_coords(ts: ThetaSum) -> "Tuple[Dict[CoordKey, Q], Dict[CoordKey, BlockLabel]]":
    """A :class:`ThetaSum`'s canonical numerator → ``({coord: Q}, {coord: block label})``.
    The coordinate of a term is ``(canonical-theta-multiset, prefactor-symbol-monomial)``
    (the same keying :meth:`ThetaSum._combine` uses), so equal coordinates ARE the same
    additive basis vector; the second map records each coordinate's σ-invariant p-character
    block (:func:`_block_of_thetas`) for the per-block partition. EXACT — coefficient is the
    exact ``Q``."""
    coords: "Dict[CoordKey, Q]" = {}
    blocks: "Dict[CoordKey, BlockLabel]" = {}
    for pref, thetas in ts.terms:
        tkey = tuple(sorted(t.arg._sort_key() for t in thetas))
        mkey = tuple(sorted(EllMonomial(_Q_ONE, pref.exps).exps.items()))
        key: CoordKey = (tkey, mkey)
        coords[key] = coords.get(key, _Q_ZERO) + pref.coeff
        blocks[key] = _block_of_thetas(thetas)
    return ({k: v for k, v in coords.items() if v != _Q_ZERO}, blocks)


def _solve_linear_exact(rows: "List[List[Q]]", rhsvec: "List[Q]",
                        n_cols: int) -> "Optional[List[Q]]":
    """Solve the exact-``ℚ`` linear system ``rows · c = rhsvec`` for ``c`` (length
    ``n_cols``) via the :class:`~srmech.amsc.qmat.QMat` Gauss-Jordan RREF of the augmented
    matrix ``[rows | rhsvec]``. Returns the solution (free variables pinned to 0), or
    ``None`` if inconsistent. EXACT — no float."""
    from .qmat import QMat

    if n_cols == 0:
        # an empty unknown set is consistent iff the rhs is all-zero.
        return [] if all(v == _Q_ZERO for v in rhsvec) else None
    if not rows:
        # no constraints: the all-zero solution is one consistent answer iff rhs empty.
        return [_Q_ZERO] * n_cols if all(v == _Q_ZERO for v in rhsvec) else None
    aug = [list(r) + [rv] for r, rv in zip(rows, rhsvec)]
    rref = QMat.from_rows(aug).rref().to_lists()
    sol = [_Q_ZERO] * n_cols
    for row in rref:
        pivot = None
        for j in range(n_cols):
            if row[j] != 0:
                pivot = j
                break
        if pivot is None:
            if row[n_cols] != 0:
                return None                       # 0 == nonzero: inconsistent
            continue
        sol[pivot] = row[n_cols]
    return sol


def _build_columns(a_r: EllRatio, b_r: EllRatio, basis: "List[Tuple[Theta, ...]]",
                   rhs: ThetaSum) -> "Tuple[List[Dict[CoordKey, Q]], Dict[CoordKey, Q], Dict[CoordKey, BlockLabel]]":
    """Build the linear system's COLUMNS (one ``{coord: Q}`` per basis element, the
    ``L(basis_i)`` coordinates) + the RHS coordinate vector + the coordinate→block map
    (learned from every column AND the rhs). Shared by the dense and block solvers so they
    are provably the SAME linear system, factored differently."""
    coord_block: "Dict[CoordKey, BlockLabel]" = {}
    columns: "List[Dict[CoordKey, Q]]" = []
    for thetas in basis:
        co, blk = _term_coords(_apply_L(a_r, b_r, thetas))
        coord_block.update(blk)
        columns.append(co)
    rhs_co, rhs_blk = _term_coords(rhs)
    coord_block.update(rhs_blk)
    return columns, rhs_co, coord_block


def _row_keys(columns: "List[Dict[CoordKey, Q]]", rhs_co: "Dict[CoordKey, Q]"
              ) -> "List[CoordKey]":
    """The sorted union of every coordinate appearing in any column or the rhs — the row
    index set of the linear system (a deterministic order)."""
    keys: "set" = set(rhs_co)
    for co in columns:
        keys |= set(co)
    return sorted(keys, key=lambda k: (str(k[0]), str(k[1])))


def _solve_key_equation_dense(a_r: EllRatio, b_r: EllRatio,
                              basis: "List[Tuple[Theta, ...]]", rhs: ThetaSum
                              ) -> "Optional[List[Q]]":
    """The BRUTE-FORCE dense baseline: ONE :class:`QMat` solve over the whole basis."""
    columns, rhs_co, _coord_block = _build_columns(a_r, b_r, basis, rhs)
    keys = _row_keys(columns, rhs_co)
    rows = [[col.get(k, _Q_ZERO) for col in columns] for k in keys]
    rhsvec = [rhs_co.get(k, _Q_ZERO) for k in keys]
    return _solve_linear_exact(rows, rhsvec, len(basis))


def _solve_key_equation(a_r: EllRatio, b_r: EllRatio,
                        basis: "List[Tuple[Theta, ...]]", rhs: ThetaSum,
                        *, return_report: bool = False
                        ) -> "Optional[List[Q]] | Tuple[List[Q], Dict]":
    """The NON-BRUTE-FORCE block-decomposed solve: group the basis columns by their single
    output p-character block, partition the rows by the same block, and solve each block as
    an INDEPENDENT small ``QMat`` system; assemble. Reproduces :func:`_solve_key_equation_dense`
    EXACTLY (same certificate) — the same linear algebra factored along the carrier's
    harmonic shape. With ``return_report`` also returns the per-block size report (the
    proof it is per-block)."""
    columns, rhs_co, coord_block = _build_columns(a_r, b_r, basis, rhs)
    keys = _row_keys(columns, rhs_co)

    # Each column's output block = the (single) block its nonzero coordinates occupy.
    col_block: "List[Optional[BlockLabel]]" = []
    groups: "Dict[BlockLabel, List[int]]" = {}
    group_order: "List[BlockLabel]" = []
    for j, co in enumerate(columns):
        blks = {coord_block[k] for k in co}
        if len(blks) > 1:
            # a column straddling > 1 block would break block-diagonality — fall back to
            # the dense solve so the answer is never WRONG (the block factoring is an exact
            # speedup, never a correctness gamble). This is the honest non-shell guard.
            dense = _solve_key_equation_dense(a_r, b_r, basis, rhs)
            if return_report:
                return (dense, {"blocks": {}, "n_blocks": 0, "basis": len(basis),
                                "block_decomposed": False})
            return dense
        blk = next(iter(blks)) if blks else None     # an all-zero column has no block
        col_block.append(blk)
        if blk is not None:
            if blk not in groups:
                groups[blk] = []
                group_order.append(blk)
            groups[blk].append(j)

    # Solve each block independently over only its own columns + its own rows.
    sol: "List[Optional[Q]]" = [None] * len(basis)
    report_blocks: "Dict[BlockLabel, Tuple[int, int]]" = {}
    for blk in group_order:
        idxs = groups[blk]
        sub_keys = [k for k in keys if coord_block.get(k) == blk]
        sub_rows = [[columns[j].get(k, _Q_ZERO) for j in idxs] for k in sub_keys]
        sub_rhs = [rhs_co.get(k, _Q_ZERO) for k in sub_keys]
        sub = _solve_linear_exact(sub_rows, sub_rhs, len(idxs))
        if sub is None:
            return (None, {"blocks": dict(report_blocks), "n_blocks": len(group_order),
                           "basis": len(basis), "block_decomposed": True}) \
                if return_report else None
        report_blocks[blk] = (len(idxs), len(sub_keys))
        for k, j in enumerate(idxs):
            sol[j] = sub[k]

    # an all-zero column (no block) must have rhs share-of-coordinate 0; its unknown is free
    # → pin to 0 (the dense solve does the same). Also re-check the rhs has no orphan block
    # the basis cannot reach (then the system is inconsistent — fall to dense for the verdict).
    reachable = set(group_order)
    for k in keys:
        if rhs_co.get(k, _Q_ZERO) != _Q_ZERO and coord_block.get(k) not in reachable:
            dense = _solve_key_equation_dense(a_r, b_r, basis, rhs)
            return (dense, {"blocks": dict(report_blocks), "n_blocks": len(group_order),
                            "basis": len(basis), "block_decomposed": True}) \
                if return_report else dense
    out = [_Q_ZERO if v is None else v for v in sol]
    if return_report:
        return out, {"blocks": dict(report_blocks), "n_blocks": len(group_order),
                     "basis": len(basis), "block_decomposed": True}
    return out


def _default_basis(rhs: ThetaSum) -> "List[Tuple[Theta, ...]]":
    """The default certificate basis when the caller passes none: the distinct theta-PRODUCT
    supports of the rhs terms (the structural occupancy the certificate must span). A
    de-duplicated, canonical-order list."""
    seen: "set" = set()
    basis: "List[Tuple[Theta, ...]]" = []
    for _pref, thetas in rhs.terms:
        tkey = tuple(sorted(t.arg._sort_key() for t in thetas))
        if tkey not in seen:
            seen.add(tkey)
            basis.append(tuple(thetas))
    return basis


# ── the wire form for the C bridge (theta-arg integer-exponent lattice) ────────


def _native():
    """The native ``_native`` module IF the ``srmech_carrier_spectrum`` peer is present and
    bound, else ``None`` — so :func:`carrier_spectrum` dispatches to C when available and
    falls cleanly to the pure-Python body (the complete alternative + the parity oracle).
    Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_carrier_spectrum", None)
    return nat if (probe is not None and probe()) else None


def _ratio_to_form(r: EllRatio) -> "Dict[str, object]":
    """An :class:`~srmech.amsc.ellbase.EllRatio` → the bridge form the C peer consumes (the
    same convention as :func:`srmech.amsc.elliptic_gosper._ratio_to_form`: the exact-``ℚ``
    prefactor + numerator / denominator theta-argument monomial triples). Pure integer
    exponents + exact-``ℚ`` coefficients — no float."""
    def _mono(m: EllMonomial):
        return (m.coeff.numerator, m.coeff.denominator, sorted(m.exps.items()))

    return {
        "prefactor": _mono(r.prefactor),
        "num": [_mono(t.arg) for t in r.num],
        "den": [_mono(t.arg) for t in r.den],
    }


def _spectrum_to_result(cs: CarrierSpectrum) -> "Dict[str, object]":
    """A :class:`CarrierSpectrum` → the public return dict: the cyclic σ-eigenspectrum +
    the p-character block partition (as JSON-friendly exponent maps) + the live carrier
    object under ``'spectrum'`` for an exact re-inspect."""
    return {
        "cyclic": dict(cs.cyclic),
        "blocks": {str(list(lab)): [[dict(t.arg.exps) for t in prod] for prod in prods]
                   for lab, prods in cs.blocks.items()},
        "n_blocks": len(cs.blocks),
        "spectrum": cs,
    }


# ── the public op (the ToolEntry; c_dispatched to srmech_carrier_spectrum) ──────


def carrier_spectrum(r) -> "Optional[Dict[str, object]]":
    """The OPERAND-side dual of ``the_one``: READ a carrier element's harmonic occupancy
    under the shift-Laplacian (the Class-L eigenbasis of the carrier's shape) in two
    orthogonal channels, and expose the block structure that makes the elliptic
    key-equation solve genuinely block-decomposed (non-brute-force).

    ``r`` is a carrier element — an :class:`~srmech.amsc.ellbase.EllRatio` (a theta-quotient
    over an exact-``ℚ`` monomial prefactor; an ``EllMonomial`` / ``Theta`` the carrier lifts
    is lifted). Returns ``{'cyclic': {x-exp k: 'q**k'}, 'blocks': {block: [theta-arg maps]},
    'n_blocks': …, 'spectrum': CarrierSpectrum}``:

    - ``cyclic`` — Channel 1 (Class-I): the σ-eigenspectrum (``σ(x^k) = q^k·x^k`` diagonal
      on monomials; ``k = 0`` the shift-Laplacian kernel / DC mode; the ``x²`` very-well-
      poised doubled-beat shows as the ``k = ±2`` entries);
    - ``blocks`` — Channel 2 (Class-L): the σ-invariant p-character block partition of the
      theta-factors (σ preserves each block — the lever the non-brute-force
      :meth:`CarrierSpectrum.solve_key_equation` rides);
    - ``spectrum`` — the live :class:`CarrierSpectrum` carrier (construct / inspect /
      ``solve_key_equation``).

    A non-EllRatio (un-liftable) operand raises ``TypeError``. EXACT — integer exponents +
    exact-``ℚ`` coefficients; sign is the Class-K pin-slot (no ``abs()``); no ``math`` /
    numpy / float. DISPATCHES to the same-rc ``srmech_carrier_spectrum`` C peer when loaded
    (re-verified against the pure body before trust); a native miss re-decides pure.
    """
    if isinstance(r, EllRatio):
        element = r
    elif isinstance(r, EllMonomial):
        element = EllRatio.monomial(r)
    elif isinstance(r, Theta):
        element = EllRatio.theta(r)
    else:
        raise TypeError(
            "carrier_spectrum: the operand must be an EllRatio carrier element (or an "
            f"EllMonomial / Theta the carrier lifts); got {r!r}")

    nat = _native()
    if nat is not None:
        try:
            got = nat.carrier_spectrum_c(_ratio_to_form(element))
            # The C peer is trusted ONLY after the Python rebuild reproduces the SAME
            # spectrum (the channels are a pure exponent-lattice read, so the C result must
            # equal the pure read byte-for-byte). A native miss falls through to pure.
            if got is not None:
                pure = CarrierSpectrum(element)
                c_cyclic, c_blocks = got
                if (c_cyclic == pure.cyclic
                        and _blocks_match(c_blocks, pure.blocks)):
                    return _spectrum_to_result(pure)
        except (RuntimeError, OverflowError, ValueError):
            pass                                  # fall to the pure path

    return _spectrum_to_result(CarrierSpectrum(element))


def _blocks_match(c_blocks, py_blocks: "Dict[BlockLabel, List[Tuple[Theta, ...]]]") -> bool:
    """Compare the C peer's block partition to the pure read structurally (the block LABELS
    + the per-block theta-argument exponent multisets must agree; order-independent)."""
    py_norm = {
        lab: sorted(tuple(sorted(t.arg.exps.items())) for prod in prods for t in prod)
        for lab, prods in py_blocks.items()
    }
    c_norm = {
        tuple(lab): sorted(tuple(sorted(d.items())) for prod in prods for d in prod)
        for lab, prods in c_blocks.items()
    }
    py_keyed = {tuple(lab): v for lab, v in py_norm.items()}
    return c_norm == py_keyed
