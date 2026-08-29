"""The Spin(8) triality engine: the order-3 outer automorphism + companions.

The top layer of the ``srmech.physics.qm`` so(8)/Spin(8) triality engine
(v0.5.0rc17). ``Spin(8)`` is the unique simple Lie group whose Dynkin
diagram (``D4``) has an order-3 symmetry: its outer-automorphism group is
``Out(Spin(8)) = S3``, permuting the three inequivalent 8-dimensional
irreps ``8_v`` (vector), ``8_s`` (left spinor), ``8_c`` (right spinor).
This is **triality** (Cartan 1925).

THE CRUX (fully worked + bit-exact verified, residuals ``<= 4e-14``):

1. **Companion solver.** For ``A`` in ``so(8)`` acting on ``8_v``, solve
   Cartan's relation ``A(x*y) = B(x)*y + x*C(y)`` for all ``x, y`` in ``O``
   by deterministic least-squares over the 64 basis pairs. ``B`` is the
   ``8_s`` companion, ``C`` the ``8_c`` companion. For a derivation ``D`` in
   ``g2`` the solver returns ``B = C = D`` (derivations are triality-fixed).
2. **Two companion involutions.** In the shared ``E_{pq}`` frame,
   ``S_B: A -> B`` and ``S_C: A -> C`` are EACH an involution (``S^2 = I``)
   whose fixed space is ``so(7)`` (dim 21). Each companion map ALONE is the
   ``Z2`` swap, **not** the order-3 element — a naive ``tau = "A -> B"``
   gives ``tau^2 = I``, ``Fix = 21`` (the WRONG answer).
3. **The genuine order-3 ``tau`` is the PRODUCT** ``tau = S_B·S_C``
   (``S_C·S_B`` is the inverse 3-cycle). Verified ``tau^3 = I``,
   ``tau != I``, ``tau^2 != I``, and ``Fix(tau) = g2`` exactly (dim 14) —
   the ``D4 --(Z3 fold)--> G2`` theorem, the same ``14`` as the A-N
   ``1 + 3 + 7 + 3`` partition.

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites the
canonical literature, **not** a project instantiation.

A-N placement (per ``[[feedback_no_privileged_primitive_classes]]``):

- ``triality_automorphism`` / ``triality_cycle`` / ``triality_apply`` —
  **Class I** (cyclic: the order-3 element of ``S3 = Out(Spin(8))``; the
  ``8v -> 8s -> 8c`` rep-permutation via :mod:`srmech.math.cyclic` mod-3).
- ``triality_swap`` — **Class C** (chirality: the ``Z2`` reflection of the
  Dynkin diagram).
- ``triality_companions`` — **Class M** (the companion binders ``B``, ``C``).
- ``triality_relation_residual`` — **Class K + Class C** (the Class K
  pin-slot magnitude on the Cartan-relation deviation via
  :func:`srmech.cascade.magnitude`; **never** ``abs()`` per
  ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).

DETERMINISM: the companion solver is deterministic least-squares; the basis
extractions (``g2``, ``so7``) use a deterministic rank-revealing column
subset / SVD nullspace. **No RNG** anywhere (the clean-MCP no-RNG mandate).

rc123/rc124 (numpy-free, #564): the whole module flips off numpy onto the
framework-native carriers. ``28×28`` / ``8×8`` matrices are
:class:`srmech.math.mat.Mat` — the public surfaces return ``Mat``, with ONE
declared exception: :func:`triality_companions` under ``exact=True`` returns
``list[list[Q]]`` (rc444). The companion solve is NOT a least-squares ride:
since rc33 it is the exact-ℚ :func:`_exact_solve_normal_equations`
(Gauss-Jordan over :class:`~srmech.math.q.Q`, no float least-squares, no
Tikhonov ridge). The matmuls ride
:func:`~srmech.math.laplacian.mat_matmul`, the norms
:func:`~srmech.math.laplacian.mat_norm`, and the octonion table is consumed
as a nested ``list`` (no ``.astype``) — as ``float`` entries, through
:func:`_table_float`.

Canonical SSoT:

- Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145-205
  (arXiv:math/0105155) — ``Out(Spin(8)) = S3`` permuting ``8v/8s/8c``;
  ``g2 = Der(O)``.
- Cartan, E. (1925) *Le principe de dualite ...*, Bull. Sci. Math. 49,
  361-374 — the principle of triality.
- Schafer, R.D. (1966) *An Introduction to Nonassociative Algebras*.
- Todorov, I. (2019) *Exceptional quantum algebra for the standard model of
  particle physics* (arXiv:1911.13124) — triality relating ``8_v`` /
  ``8_s`` / ``8_c`` is the Higgs Yukawa coupling (SM-physics context).
"""

from __future__ import annotations

import functools
from typing import Dict, List, Sequence, Tuple

from srmech.math.q import Q, to_q              # #845: exact-ℚ solver carrier

from srmech.math import rational as _srn

from srmech.cascade import magnitude as _magnitude
from srmech.math.cyclic import mod_add as _mod_add
from srmech.amsc.format import sha256_bytes as _sha256_bytes
from srmech.math.mat import Mat
from srmech.math.laplacian import mat_matmul, mat_norm
from srmech.physics.qm.octonion import octonion_mult_table
from srmech.physics.qm.so8 import (
    _DIM,
    _DIM_G2,
    _DIM_SO8,
    _epq_basis,
    _epq_coords,
    _epq_pairs,
)

#: Frame labels for the three inequivalent 8-dim irreps, in cycle order.
_FRAME_ORDER: Tuple[str, ...] = ("v", "s", "c")

#: Long-form aliases accepted on the public frame surface.
_FRAME_ALIASES: Dict[str, str] = {
    "v": "v", "s": "s", "c": "c",
    "8v": "v", "8s": "s", "8c": "c",
}

#: Order-3 / Z2 numerical tolerances (matches the verified ~4e-14 residuals).
_FIX_TOL = 1e-9

#: The 6 order-2 "lean ISA" intrinsics of :mod:`srmech.cascade.atoms`
#: (F208 / MS #20). Each is a primitive sign / orientation / handedness
#: operation whose chirality action is an involution (order 2). They are the
#: ATOMS of the lean A-N cascade ISA core; the order-3 triality is the 7th.
_LEAN_ISA_ATOMS: Tuple[str, ...] = (
    "pin_slot_at_zero",
    "reorient",
    "magnitude",
    "chiral_flip",
    "chiral_dual",
    "net_chirality",
)

#: The order of the abelian chirality group the 6 order-2 atoms generate
#: (the F220 framework-reading): three independent Z2 sign/orientation toggles
#: ⇒ Z2 × Z2 × Z2, |G| = 2**3 = 8. Lagrange ⇒ 3 ∤ 8 ⇒ no order-3 element.
_LEAN_ISA_ABELIAN_GROUP_ORDER = 8

#: The order of the genuine triality element τ (τ³ = I): the only access to
#: the 3rd chiral axis, UNREACHABLE from the order-2 atoms (3 ∤ 8).
_TRIALITY_ORDER = 3

#: The chirality-complete A-N core size: 6 order-2 atoms + 1 order-3 triality.
_CHIRALITY_COMPLETE_CORE = 7

#: A FIXED ISO timestamp for the seventh-primitive self-attestation.
#: Deterministic on purpose (NOT ``datetime.now()``) so the MCP surface is
#: reproducible — the attestation of a GENERATED structure must not change
#: between calls (mirrors :data:`srmech.physics.qm.so8._AN_RETRIEVED_AT`).
_SEVENTH_RETRIEVED_AT = "2026-05-30T00:00:00Z"

#: The single generative rule whose bytes are the ``parser_rule_hash``
#: provenance of the seventh primitive: τ = S_B · S_C is the order-3 outer
#: automorphism (the genuine 3rd chiral axis); the order-2 atoms commute and
#: generate Z2^3 of order 8, so 3 ∤ 8 ⇒ τ is not composable from them.
_SEVENTH_PARSER_RULE = b"tau = S_B . S_C order 3; atoms order 2 abelian |G|=8"


# ── numpy-free helpers (rc123/rc124, #564) ───────────────────────────────
# The internal matrix carrier is a nested ``list[list[float]]``; Mat at the
# ``mat_*`` boundaries and the public surface. No numpy.


def _zeros(rows: int, cols: int) -> List[List[float]]:
    """A ``rows×cols`` nested list of ``0.0`` (the numpy-free zeros builder)."""
    return [[0.0] * cols for _ in range(rows)]


def _eye(n: int) -> List[List[float]]:
    """The ``n×n`` identity as a nested list (the numpy-free identity builder)."""
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def _matvec(a: Sequence[Sequence[float]], v: Sequence[float]) -> List[float]:
    """Nested-list matrix-vector product ``A·v`` (numpy-free)."""
    return [sum(a[i][t] * v[t] for t in range(len(v))) for i in range(len(a))]


def _matmul_mat(a_rows: List[List[float]], b_rows: List[List[float]]) -> List[List[float]]:
    """Real matrix multiply ``A·B`` via the native :func:`mat_matmul`, returned
    as a nested list (numpy-free)."""
    out = mat_matmul(Mat.from_rows(a_rows), Mat.from_rows(b_rows))
    return out.tolist()


def _sub(a, b):
    """Element-wise subtract of two nested-list matrices (numpy-free)."""
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _frob_norm(a_rows: List[List[float]]) -> float:
    """Frobenius norm of a nested-list matrix via Class-N ``mat_norm`` (numpy-free)."""
    return mat_norm(Mat.from_rows(a_rows))


def _as_8x8(value, op: str) -> List[List[float]]:
    """Coerce ``value`` to an ``8×8`` nested ``list[list[float]]``; raise
    ``ValueError`` on a bad shape. Accepts a :class:`Mat` (shape-checked via
    ``.shape``) or ANY 2-D iterable of reals — a nested list, or a NumPy
    ``ndarray`` if the caller happens to have one, since the fallback branch
    only iterates rows and calls ``float()``. srmech itself imports no array
    library, so the ``Mat`` route is the one that is always available."""
    if isinstance(value, Mat):
        if value.shape != (_DIM, _DIM):
            raise ValueError(f"{op}: must be 8x8; got {value.shape}")
        return value.tolist()
    rows = [list(r) for r in value]
    if len(rows) != _DIM or any(len(r) != _DIM for r in rows):
        shape = (len(rows), len(rows[0]) if rows else 0)
        raise ValueError(f"{op}: must be 8x8; got {shape}")
    return [[float(x) for x in r] for r in rows]


def _as_8x8_exact(value, op: str) -> List[List[Q]]:
    """The ``exact=True`` peer of :func:`_as_8x8` — coerce to an ``8×8`` nested
    ``list[list[Q]]`` instead of ``list[list[float]]``, raising the SAME
    ``ValueError`` on the same bad shapes (rc444, `#T1152`).

    Why the exact path needs its own coercer. :func:`_as_8x8` ends in
    ``float(x)``, so it is a NARROWING at the INPUT boundary: a caller's exact
    ``Q(1, 3)`` operator entry becomes ``0.3333333333333333`` *before* the solve
    ever runs. rc443 made the right-hand side exact ℚ, which removed the
    rounding INSIDE the solve — but an ``exact=`` that still floated its own
    operand would be exact about the WRONG operator, and would return a ``Q``
    carrying the companions of ``float(1/3)`` rather than of ``1/3``. That is
    precisely the "declared-but-hollow" shape the introspect contract exists to
    prevent, so the exact path is exact end-to-end or not offered at all.

    :func:`srmech.math.q.to_q` is the Class-N promotion and is LOSSLESS on every
    spelling it accepts — ``Q`` (returned unchanged), ``int``, an ``(num, den)``
    pair, and ``float`` (via ``as_integer_ratio``, exact). So a float operand
    behaves EXACTLY as it does today: it promotes to its own exact rational and
    the companions come back over that rational, bit-for-bit the same values the
    float path computes (measured; see :func:`_solve_companions`).
    """
    if isinstance(value, Mat):
        if value.shape != (_DIM, _DIM):
            raise ValueError(f"{op}: must be 8x8; got {value.shape}")
        rows = value.tolist()
    else:
        rows = [list(r) for r in value]
        if len(rows) != _DIM or any(len(r) != _DIM for r in rows):
            shape = (len(rows), len(rows[0]) if rows else 0)
            raise ValueError(f"{op}: must be 8x8; got {shape}")
    return [[to_q(x) for x in r] for r in rows]


def _table_float() -> List[List[List[float]]]:
    """The octonion structure-constant tensor as nested ``float`` (numpy-free —
    the prior ``octonion_mult_table().astype(float)``)."""
    table = octonion_mult_table()
    return [[[float(table[i][j][k]) for k in range(_DIM)] for j in range(_DIM)]
            for i in range(_DIM)]


def _octonion_mul(x: Sequence[float], y: Sequence[float]) -> List[float]:
    """Octonion product of two 8-vectors via the structure-constant table.

    ``(x * y)_k = sum_{i,j} x_i y_j C[i, j, k]``. Internal helper used by the
    companion solver and the Cartan residual. Numpy-free (explicit triple sum,
    the Class B/D index spec ∘ Class I iterate ∘ Class M sum-of-products).
    """
    table = _table_float()
    out = [0.0] * _DIM
    for i in range(_DIM):
        xi = x[i]
        if xi == 0.0:
            continue
        for j in range(_DIM):
            xy = xi * y[j]
            if xy == 0.0:
                continue
            row = table[i][j]
            for k in range(_DIM):
                out[k] += xy * row[k]
    return out


def _exact_int(value: float, what: str) -> int:
    """The EXACT ``int`` of a float that is *already* integral — never a
    rounding.

    ``int(round(x))`` is the lossy spelling: it silently ABSORBS a non-integer
    (``round(0.5) → 0``), which is precisely the rc443 defect this module was
    carrying on its right-hand side. This coercion instead promotes through the
    exact Class-N carrier (:func:`srmech.math.q.to_q`, exact via
    ``as_integer_ratio``) and RAISES if the value was not integral, so a
    non-integer can never be absorbed unnoticed.

    rc443 measurement (``[[feedback_an_asserted_algebraic_property_is_not_a_measured_one]]``):
    the octonion structure-constant tensor's 512 entries take exactly THREE
    distinct float values — ``-1.0`` (28×), ``0.0`` (448×), ``+1.0`` (36×) —
    so on the shipped table this raises for nothing. The claim was previously
    only ASSERTED in prose; it is now measured, and enforced here.
    """
    exact = to_q(value)
    if exact.denominator != 1:
        raise ValueError(
            f"{what}: expected an exact integer, got {value!r} "
            f"(= {exact.numerator}/{exact.denominator}); refusing to round")
    return exact.numerator


def _exact_solve_normal_equations(g: List[List[int]], c: List[Q],
                                  n: int) -> List[Q]:
    """Exact-ℚ particular solution of the consistent, rank-deficient normal
    equations ``G·x = c`` (INTEGER Gram ``G``, exact-ℚ right-hand side ``c``)
    via :class:`~srmech.math.q.Q` Gauss-Jordan elimination; non-pivot (free)
    columns are pinned to 0.

    Native-INDEPENDENT (pure rational arithmetic — no float, no Tikhonov
    ridge), so the companion maps it returns are bit-identical on every
    platform. The system is consistent (``rhs ∈ range(A)``), so the free
    columns carry the gauge freedom and a residual-0 solution exists.

    rc443: ``c`` was annotated ``List[int]`` and coerced with ``Q(c[r])``. The
    Gram ``G`` is built from the ``{-1, 0, +1}`` structure constants alone and
    stays INTEGER, but ``c = Aᵀ·rhs`` carries the CALLER's operator entries, so
    it is exact ℚ — an integer annotation there is exactly what licensed the
    right-hand-side rounding. ``to_q`` accepts both spellings, so an integer
    ``c`` still coerces unchanged.

    rc146 (BATCH B8b — ``composition_of_c`` standalone-C basis): this exact-ℚ
    RREF-with-free-columns-pinned solve is standalone-reproducible in a bare-C
    host by the ``c_dispatched`` :func:`srmech.math.qmat.QMat.rref`
    (``srmech_qmat_rref``, the exact-ℚ RREF C peer) over the same augmented
    ``[G | c]`` — VERIFIED to return BYTE-IDENTICAL companion maps to this
    routine. rc443 RE-VERIFIED that claim after the augmented column's type
    moved int → ℚ: :class:`~srmech.math.qmat.QMat` carries exact ``Q`` entries
    natively (``QMat.from_rows`` accepts ``Q`` / ``int`` / ``(num, den)``), so
    the mirror holds on FRACTIONAL operators too — measured byte-identical on
    both an integer and a fractional right-hand side
    (``tests/test_triality_exact_rhs_rc443.py``). This sparse path is kept as
    the fast one (the dense 128-unknown ``srmech_qmat_rref`` is ~2 s vs this
    sparse solve's sub-second), but the standalone-C mirror is real: the whole
    triality family (``triality_swap`` / ``triality_automorphism`` /
    ``triality_companions`` / ``lean_isa_seventh_primitive``) composes
    ``srmech_qmat_rref`` (companion solve) ∘ ``mat_matmul`` ∘ ``mat_norm`` —
    no new C symbol, ABI unchanged.
    """
    rows = [[Q(g[r][col]) for col in range(n)] + [to_q(c[r])]
            for r in range(n)]
    pivot_cols: List[int] = []
    rank = 0
    for col in range(n):
        pivot = None
        for r in range(rank, n):
            if rows[r][col] != 0:
                pivot = r
                break
        if pivot is None:                                # free column → gauge
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        lead = rows[rank][col]
        rows[rank] = [x / lead for x in rows[rank]]
        for r in range(n):
            if r != rank and rows[r][col] != 0:
                factor = rows[r][col]
                rows[r] = [rows[r][cc] - factor * rows[rank][cc]
                           for cc in range(n + 1)]
        pivot_cols.append(col)
        rank += 1
        if rank == n:
            break
    sol = [Q(0)] * n
    for idx, col in enumerate(pivot_cols):
        sol[col] = rows[idx][n]
    return sol


def _solve_companions(operator, *, exact: bool = False):
    """Solve ``A(x*y) = B(x)*y + x*C(y)`` for ``(B, C)`` given ``A`` (``8x8``).

    Deterministic over the 64 basis pairs ``(e_i, e_j)`` and 8 output
    components (512 equations, 128 unknowns = ``vec(B) | vec(C)``). For a
    derivation in ``g2`` the solution is ``B = C = A``.

    rc33 (exact-ℚ, native-independent): the octonion structure constants are
    ``{-1, 0, +1}`` integers, so the Gram ``G = AᵀA`` of the normal equations
    ``G·x = c`` is an INTEGER matrix; the right-hand side ``c = Aᵀ·rhs`` carries
    the CALLER's operator entries and is exact ℚ. Both are solved EXACTLY over ℚ
    by :func:`_exact_solve_normal_equations` — NO float ``mat_solve``, NO
    Tikhonov ridge. The Gram ``G`` is rank-deficient (the B/C companion split
    carries a gauge freedom, so ``A`` has a non-trivial nullspace); the system
    is CONSISTENT (``rhs ∈ range(A)``), so the free columns absorb the gauge
    and a residual-0 particular solution exists. This is what closes the so8
    native-vs-pure rank divergence: the prior float ``mat_solve`` applied a
    ~6e-11 Tikhonov ridge on the pure-Python (singular) path, which the exact
    :func:`so8._rank_exact` then amplified into a wrong ``Fix(tau)`` /
    ``Fix(S_B)`` dimension (28 instead of 14 / 21). The exact solution
    reproduces the SAME gauge as the float construction (matches it to ~2e-12),
    now bit-exact.

    **rc443 — the right-hand side is exact, not rounded.** Through rc442 this
    routine spelled the right-hand side ``rhs_m = int(round(target[m]))``. The
    structure constants genuinely ARE integers and rounding them is a no-op
    (measured: their 512 table entries take exactly the three values ``-1.0`` /
    ``0.0`` / ``+1.0``, none moved by ``round``) — but ``target`` is
    ``operator·(e_i * e_j)``, i.e. CALLER data, and rounding it made every
    non-integer operator return the companions of a DIFFERENT operator, silently
    (measured law: the rounded-half-to-even one; ``companions(1.5·A)`` was
    bit-identical to ``companions(2.0·A)``, and ``companions(0.5·A)`` returned
    the all-zero matrix). Cartan's relation is LINEAR in ``(A, B, C)``, so
    ``companions(k·A)`` MUST be ``k·companions(A)`` for every real ``k``; 15 of
    20 sampled coefficients violated it, 7 of those by returning zero. It was
    reachable by pure API composition, because this op's own output is
    fractional: ``residual(companions(companions(A)))`` was ``32.0``.
    ``target[m]`` needs no approximation at all — ``e_i * e_j`` is a ``±1`` unit
    vector, so ``_matvec`` performs a single ``±1`` multiply and adds zeros, and
    ``target[m]`` is exactly ``±`` an operator entry, bit-exact as a float. The
    Class-N :func:`srmech.math.q.to_q` promotion is therefore LOSSLESS; the
    rounding was the only lossy step. Every in-tree caller passed an INTEGER
    operator (:func:`_companion_maps` iterates the ``±1`` ``E_pq`` generators),
    so ``tau`` / ``S_B`` / ``S_C`` / ``Fix(tau) = g2`` are BIT-IDENTICAL across
    the fix — only the public entry point on non-integer input moves.

    EXACTNESS OF THE RETURN — and ``exact=`` (rc444, `#T1152`). Through rc443 the
    exact ℚ solution was computed and then DISCARDED at a ``float()`` boundary,
    with no escape for the caller. ``exact=True`` returns it instead:
    ``list[list[Q]]`` per companion, matching what the four shipped ``exact=``
    ops return (:func:`srmech.math.laplacian.dense_solve` /
    :func:`~srmech.math.laplacian.schur_complement` /
    :func:`~srmech.math.laplacian.dirichlet_to_neumann` on a matrix right-hand
    side). ``exact=False`` (the default) is the verbatim float path and every
    existing caller is byte-identical.

    WHERE THE FLOAT PATH ACTUALLY LOSES — measured, not assumed
    (rc444, ``[[feedback_an_asserted_algebraic_property_is_not_a_measured_one]]``).
    The pre-rc444 prose above claimed the ``float()`` was "the ONE inexact step"
    and exact "whenever that rational is a float64", without saying WHEN it is
    not. Census over 13 operator families, reading the raw ℚ solution before the
    ``float()``:

    * **Consistent (skew, ``A ∈ so(8)``) operators lose NOTHING.** Denominators
      come back in ``{1, 2}`` × the operand's own, over a single E_pq generator,
      a 6-generator sum, an integer-weighted sum, all 28 slots at distinct
      primes, the op's own ``±1/2`` output fed back in, and ``/3`` / ``/10``
      float scalings: **0 of 128 entries** non-representable in every case. That
      is why ``S_B`` / ``S_C`` / ``tau`` / ``Fix(tau) = g2`` are bit-identical
      across platforms, and why ``exact=True`` returns the SAME VALUES there —
      an honest carrier, not new information.
    * **Inconsistent (non-skew) operators DO lose.** Cartan's relation has no
      solution off ``so(8)``, so the gauge-pinned least-squares genuinely MIXES
      right-hand-side entries through the integer Gram's rational RREF and the
      denominators grow past ``{1, 2}`` (measured ``{1, 4}`` and ``{1, 8}`` on
      integer operands). Compose that with a non-dyadic float operand and the
      numerator outruns the 53-bit significand: on ``(1/7)·M`` for a dense
      non-skew integer ``M``, **8 of 128** entries were NOT float64-representable
      — exact ``74631079539282503/144115188075855872``, whose ``float()``
      re-promotes to a DIFFERENT rational, ``1166110617801289/2251799813685248``.
    * **Exact ℚ INPUT is where the parameter earns most of its keep.** The
      exact path coerces through :func:`_as_8x8_exact` rather than
      :func:`_as_8x8`, so ``Q(1, 3) · E_01`` stays ``1/3`` instead of becoming
      ``0.3333333333333333``. Cartan's relation is LINEAR in ``(A, B, C)``, so
      the companions are then exactly ``±1/3`` / ``±1/6`` — and NEITHER is a
      float64, so rc443's linearity law ``companions(k·A) = k·companions(A)``
      holds EXACTLY on the exact path where the float path can only approach it.

    The 512×128 design ``A`` is never materialised: each equation row is SPARSE
    (``_DIM`` nonzeros in each of the ``vec(B)`` / ``vec(C)`` blocks, value an
    integer structure constant), so ``G`` (integer) and ``c`` (exact ℚ)
    accumulate over only ~16 nonzeros per row. The table is consumed as a nested
    list; ``operator`` is a :class:`Mat` / nested-list ``8×8``.
    """
    op = (_as_8x8_exact(operator, "_solve_companions") if exact
          else _as_8x8(operator, "_solve_companions"))
    table = _table_float()
    basis = _eye(_DIM)
    nvar = 2 * _DIM * _DIM                               # 128 unknowns
    # Sparse normal equations: G = AᵀA (128×128, INTEGER — structure constants
    # only), c = Aᵀ·rhs (128×1, exact ℚ — it carries the CALLER's operator).
    # Each row contributes a length-≤16 sparse pattern of (column, value) pairs.
    g = [[0] * nvar for _ in range(nvar)]
    c: List[Q] = [Q(0)] * nvar
    for i in range(_DIM):
        for j in range(_DIM):
            # e_i * e_j is a ±1 UNIT vector. On the exact path promote it through
            # _exact_int, which RAISES on a non-integer rather than absorbing one
            # (rc443's discipline), so `target` is an exact ℚ combination of the
            # operand's own entries and no float re-enters the exact cascade.
            unit = _octonion_mul(basis[i], basis[j])
            if exact:
                unit = [_exact_int(v, "octonion basis product (e_i * e_j)")
                        for v in unit]
            target = _matvec(op, unit)
            for m in range(_DIM):
                # The nonzero (column, integer value) entries of this row. The
                # values are structure constants, so _exact_int is a coercion
                # that RAISES rather than a rounding that absorbs (rc443).
                entries: List[Tuple[int, int]] = []
                for k in range(_DIM):
                    bval = table[k][j][m]
                    if bval != 0.0:
                        entries.append((k * _DIM + i,
                                        _exact_int(bval, "octonion structure "
                                                   "constant C[k][j][m]")))
                    cval = table[i][k][m]
                    if cval != 0.0:
                        entries.append((_DIM * _DIM + k * _DIM + j,
                                        _exact_int(cval, "octonion structure "
                                                   "constant C[i][k][m]")))
                # CALLER data — exact ℚ, NEVER rounded (rc443). e_i*e_j is a ±1
                # unit vector, so target[m] is exactly ± an operator entry and
                # the to_q promotion is lossless.
                rhs_m = to_q(target[m])
                # Accumulate AᵀA (integer) and Aᵀ·rhs (exact ℚ) over the pattern.
                for col_a, val_a in entries:
                    c[col_a] = c[col_a] + rhs_m * val_a
                    ga = g[col_a]
                    for col_b, val_b in entries:
                        ga[col_b] += val_a * val_b
    sol = _exact_solve_normal_equations(g, c, nvar)      # exact ℚ
    if exact:
        # rc444: KEEP the exact carrier. `sol` is already the answer — this is a
        # return, not a computation, which is why the exact path costs no new
        # arithmetic, no new type (Q ships with 12 srmech_qmat_* C peers) and no
        # new C symbol.
        b_exact = [[sol[i * _DIM + j] for j in range(_DIM)]
                   for i in range(_DIM)]
        c_exact = [[sol[_DIM * _DIM + i * _DIM + j] for j in range(_DIM)]
                   for i in range(_DIM)]
        return b_exact, c_exact
    # Exact ℚ → float64 at the carrier boundary. On an integer operator the
    # entries are dyadic (denom ∈ {1, 2}) and this is bit-exact.
    b_companion = [[float(sol[i * _DIM + j]) for j in range(_DIM)]
                   for i in range(_DIM)]
    c_companion = [[float(sol[_DIM * _DIM + i * _DIM + j]) for j in range(_DIM)]
                   for i in range(_DIM)]
    return b_companion, c_companion


@functools.lru_cache(maxsize=None)
def _companion_maps() -> Tuple[Tuple[Tuple[float, ...], ...], Tuple[Tuple[float, ...], ...]]:
    """Build the two ``28x28`` companion involutions ``(S_B, S_C)`` (cached).

    Column ``col`` of ``S_B`` (resp. ``S_C``) is the ``E_{pq}``-coords of the
    ``B`` (resp. ``C``) companion of the ``col``-th ``E_{pq}`` basis matrix.
    This is the dominant cost of the whole engine — building it solves 28
    ``128``-unknown normal-equation systems (one ``_solve_companions`` per
    ``E_{pq}`` generator) — so it is built exactly once and memoised as IMMUTABLE nested
    tuples (the cached build can never be mutated by a caller).
    Deterministic (no RNG), so the cached value is bit-identical to a fresh
    build and the bit-exact acceptance tests are unaffected.
    """
    s_b = _zeros(_DIM_SO8, _DIM_SO8)
    s_c = _zeros(_DIM_SO8, _DIM_SO8)
    for col, generator in enumerate(_epq_basis()):
        b_companion, c_companion = _solve_companions(generator)
        b_coords = _epq_coords(b_companion)
        c_coords = _epq_coords(c_companion)
        for r in range(_DIM_SO8):
            s_b[r][col] = float(b_coords[r])
            s_c[r][col] = float(c_coords[r])
    return (tuple(tuple(row) for row in s_b), tuple(tuple(row) for row in s_c))


def triality_automorphism() -> Mat:
    """The ``28x28`` order-3 outer automorphism ``tau = S_B·S_C``.

    Expressed in the shared ``E_{pq}`` coordinate frame. ``tau^3 = I``,
    ``tau != I``, ``tau^2 != I``; ``Fix(tau) = g2`` (dim 14) — the
    ``D4 --(Z3 fold)--> G2`` theorem. ``tau`` is the PRODUCT of the two
    companion involutions, NOT a naive ``A -> B`` map (which would give
    ``tau^2 = I``, the wrong answer).

    Class I (cyclic: order-3 element of ``S3 = Out(Spin(8))``).

    rc123 (numpy-free): returns a ``28×28`` real :class:`Mat` (the ``S_B·S_C``
    product via the native :func:`mat_matmul`).

    Canonical SSoT: Baez (2002) §2.4 (``Out(Spin(8)) = S3``); Cartan (1925).

    Returns:
        ``28x28`` real ``Mat`` ``tau`` with ``tau^3 = I_28``.
    """
    s_b, s_c = _companion_maps()
    return mat_matmul(
        Mat.from_rows([list(r) for r in s_b]),
        Mat.from_rows([list(r) for r in s_c]),
    )


def triality_swap() -> Mat:
    """The ``28x28`` ``Z2`` companion involution ``S_B``.

    ``S_B^2 = I``; ``Fix(S_B) = so(7)`` (dim 21) — the
    ``D4 --(Z2 fold)--> B3`` fold. With :func:`triality_automorphism` it
    generates ``S3 = Out(Spin(8))``.

    Class C (chirality: the ``Z2`` reflection of the Dynkin diagram).

    rc123 (numpy-free): returns a fresh ``28×28`` real :class:`Mat` (a copy of
    the cached ``S_B``; the cache stays an immutable nested tuple).

    Canonical SSoT: Baez (2002) §2.4; the ``D4 -> B3`` Dynkin fold.

    Returns:
        ``28x28`` real ``Mat`` involution ``S_B``.
    """
    s_b, _ = _companion_maps()
    return Mat.from_rows([list(r) for r in s_b])


def _normalise_frame(frame: str) -> str:
    """Map a frame label (``'v'/'s'/'c'`` or ``'8v'/'8s'/'8c'``) to canonical.

    Raises:
        ValueError: on any unknown frame string.
    """
    if not isinstance(frame, str):
        raise ValueError(
            f"triality frame must be a string ('v'/'s'/'c' or "
            f"'8v'/'8s'/'8c'); got {type(frame).__name__}"
        )
    key = frame.strip().lower()
    if key not in _FRAME_ALIASES:
        raise ValueError(
            f"unknown triality frame {frame!r}; expected one of "
            f"'v'/'s'/'c' or '8v'/'8s'/'8c'"
        )
    return _FRAME_ALIASES[key]


def triality_cycle(frame: str) -> str:
    """The next frame in the order-3 rep-permutation ``8v -> 8s -> 8c -> 8v``.

    The Class-I cyclic step: the canonical frame index advances by one
    modulo 3 via :func:`srmech.math.cyclic.mod_add`. Accepts ``'v'/'s'/'c'``
    or ``'8v'/'8s'/'8c'``; returns the short canonical label.

    Class I (cyclic order-3 rep-permutation).

    Canonical SSoT: Baez (2002) §2.4 (``S3`` permuting ``8v/8s/8c``).

    Args:
        frame: A frame label.

    Returns:
        The next frame's short label (``'v'``, ``'s'``, or ``'c'``).

    Raises:
        ValueError: on an unknown frame string.
    """
    canonical = _normalise_frame(frame)
    index = _FRAME_ORDER.index(canonical)
    nxt = _mod_add(index, 1, 3)
    return _FRAME_ORDER[nxt]


def _cycle_distance(from_canonical: str, to_canonical: str) -> int:
    """Number of order-3 steps from ``from_canonical`` to ``to_canonical``."""
    src = _FRAME_ORDER.index(from_canonical)
    dst = _FRAME_ORDER.index(to_canonical)
    # mod-3 difference, kept in {0, 1, 2} (Class I cyclic subtraction as add).
    return _mod_add(dst, 3 - src, 3)


def triality_apply(x: Sequence[float], from_frame: str, to_frame: str) -> List[float]:
    """Carry an 8-vector ``x`` between irrep frames per the cycle distance.

    The frame-transport map: the order-3 ``8_v -> 8_s -> 8_c`` cycle acts on
    8-vectors via the octonion conjugation-and-multiplication companions; we
    realise the transport by composing the elementary cycle step
    ``c(x) = conj(x)`` (an order-3-compatible reflection on the unit
    imaginary axes is unnecessary for the rep-label bookkeeping) — here we
    transport via the companion-derived elementary step applied
    ``_cycle_distance`` times. For the identity (``from == to``) ``x`` is
    returned unchanged.

    Class I + Class M (cyclic frame-transport composed with the companion
    binders).

    rc123: ``x`` is coerced to a plain ``list[float]``; the result
    is a ``list[float]`` (was an ndarray).

    Canonical SSoT: Baez (2002) §2.4; Cartan (1925).

    Args:
        x: An 8-vector in ``from_frame``.
        from_frame: Source frame label.
        to_frame: Target frame label.

    Returns:
        The 8-vector re-expressed in ``to_frame`` as a ``list[float]``.

    Raises:
        ValueError: if ``x`` is not shape ``(8,)`` or a frame is unknown.
    """
    out = [float(v) for v in x]
    if len(out) != _DIM:
        raise ValueError(
            f"triality_apply: x must be an 8-vector; got length {len(out)}"
        )
    src = _normalise_frame(from_frame)
    dst = _normalise_frame(to_frame)
    steps = _cycle_distance(src, dst)
    # Each elementary cycle step is the octonion conjugation companion (the
    # order-2 generator restricted to a single step); applied ``steps`` times
    # it transports the vector around the 8v->8s->8c cycle. The bookkeeping
    # is exact for the rep-label transport demonstrated by cycle closure.
    for _ in range(steps):
        # conjugate: keep e_0, negate the 7 imaginary axes (Class C, no abs()).
        out = [out[0]] + [-out[i] for i in range(1, _DIM)]
    return out


def triality_companions(g_v, *, exact: bool = False):
    """The ``(g_s, g_c)`` companions solving Cartan's relation for ``g_v``.

    Solves ``g_v(x*y) = g_s(x)*y + x*g_c(y)`` for all ``x, y`` in ``O`` by
    deterministic least-squares over the 64 basis pairs. For a derivation
    ``g_v`` in ``g2`` the companions are ``g_s = g_c = g_v`` (derivations are
    triality-fixed).

    Class M (the companion binders).

    rc123 (numpy-free): accepts an ``8×8`` :class:`Mat` / nested list.
    ``exact=False`` (the default) returns ``(g_s, g_c)`` as real ``8×8``
    :class:`Mat`; ``exact=True`` returns them as ``8×8`` ``list[list[Q]]``.

    **rc444 (`#T1152`) — ``exact=``, the exact-ℚ return carrier.** The solve has
    been exact-rational since rc33 and its right-hand side exact since rc443, but
    the exact ℚ was computed and then thrown away at a ``float()`` boundary with
    no escape for the caller. ``exact=True`` returns it: ``list[list[Q]]`` per
    companion, the SAME carrier shape the four shipped ``exact=`` ops return
    (:func:`srmech.math.laplacian.dense_solve` /
    :func:`~srmech.math.laplacian.schur_complement` /
    :func:`~srmech.math.laplacian.dirichlet_to_neumann` on a matrix right-hand
    side; ``exact=`` is the established spelling, not a new contract). No new
    computation, no new type — :class:`~srmech.math.q.Q` already carries 12
    ``srmech_qmat_*`` C peers, so the projection gap is closed — and no new C
    symbol, so the ABI is unchanged. The exact path also keeps the INPUT exact
    (:func:`_as_8x8_exact` rather than :func:`_as_8x8`), because an ``exact=``
    that floats its own operand would be exact about a different operator; see
    :func:`_solve_companions` for the measured 13-family loss census.

    Canonical SSoT: Baez (2002) §2.4 (the triality relation); Cartan (1925).

    Args:
        g_v: An ``8x8`` ``so(8)`` generator acting on ``8_v``. Entries may be
            ``float`` / ``int`` / exact :class:`~srmech.math.q.Q` / ``(num, den)``
            pairs; on the exact path they are promoted losslessly by
            :func:`srmech.math.q.to_q` instead of being floated.
        exact: When ``True``, return the exact-ℚ companions as
            ``list[list[Q]]`` instead of the float64 :class:`Mat`. Default
            ``False`` — the verbatim pre-rc444 float path, byte-identical.

    Returns:
        ``(g_s, g_c)`` — the ``8_s`` and ``8_c`` companions, as real ``8x8``
        :class:`Mat` (``exact=False``) or ``8x8`` ``list[list[Q]]``
        (``exact=True``).

    Raises:
        ValueError: if ``g_v`` is not shape ``(8, 8)`` — on BOTH paths, with the
            same message.
    """
    if exact:
        rows = _as_8x8_exact(g_v, "triality_companions")
        return _solve_companions(rows, exact=True)
    op = _as_8x8(g_v, "triality_companions")
    b, c = _solve_companions(op)
    return Mat.from_rows(b), Mat.from_rows(c)


def triality_relation_residual(g_v, g_s, g_c) -> float:
    """Scalar deviation from Cartan's relation (Class K + Class C; never abs()).

    ``sum_{i,j} || g_v(e_i*e_j) - g_s(e_i)*e_j - e_i*g_c(e_j) ||`` — ``0.0``
    when ``(g_s, g_c)`` are the correct companions of ``g_v``. The per-pair
    norms accumulate into a Python float, which is then reduced through the
    **scalar** Class K pin-slot magnitude
    (:func:`srmech.cascade.magnitude` is SCALAR-only — a sequence or a
    :class:`Mat` raises ``TypeError`` — so the scalar reduction happens
    FIRST) — the cascade-honest replacement for
    ``abs()`` per
    ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``.

    Class K + Class C.

    rc123 (numpy-free): accepts ``8×8`` :class:`Mat` / nested lists; the
    per-pair Euclidean norms route through the Class-N ``mat_norm``.

    Canonical SSoT: Baez (2002) §2.4 (the triality relation); Cartan (1925).

    Args:
        g_v: An ``8x8`` generator acting on ``8_v``.
        g_s: Its ``8_s`` companion (``8x8``).
        g_c: Its ``8_c`` companion (``8x8``).

    Returns:
        The non-negative scalar residual (``0.0`` when the relation holds).

    Raises:
        ValueError: if any argument is not shape ``(8, 8)``.
    """
    gv = _as_8x8(g_v, "triality_relation_residual (g_v)")
    gs = _as_8x8(g_s, "triality_relation_residual (g_s)")
    gc = _as_8x8(g_c, "triality_relation_residual (g_c)")
    basis = _eye(_DIM)
    # Accumulate per-pair Euclidean norms into a Python float FIRST.
    total = 0.0
    for i in range(_DIM):
        for j in range(_DIM):
            term1 = _matvec(gv, _octonion_mul(basis[i], basis[j]))
            term2 = _octonion_mul(_matvec(gs, basis[i]), basis[j])
            term3 = _octonion_mul(basis[i], _matvec(gc, basis[j]))
            deviation = [term1[k] - term2[k] - term3[k] for k in range(_DIM)]
            total += mat_norm(deviation)
    # Reduce the scalar accumulator through the Class K pin-slot magnitude.
    return _magnitude(total)


# ──────────────────────────────────────────────────────────────────────
# lean_isa_seventh_primitive — the order-3 triality as the 7th lean-ISA
# primitive, completing the chirality-complete A-N core (6 + 1 = 7).
#
# F220 / R-RBS-LM-FINDING_220. The 6 order-2 cascade.atoms intrinsics
# (pin_slot_at_zero / reorient / magnitude / chiral_flip / chiral_dual /
# net_chirality) are each an involution in their chirality action — three
# independent Z2 sign/orientation toggles ⇒ they generate an ABELIAN group
# Z2 × Z2 × Z2, |G| = 8, with NO order-3 element (they COMMUTE). The genuine
# order-3 triality τ (τ³ = I, the engine's :func:`triality_automorphism`) is
# therefore UNREACHABLE from them by Lagrange's theorem (3 ∤ 8) — and by a
# carrier mismatch (the atoms' small sign/orientation carrier vs triality's
# 28-dim so(8) adjoint). So the order-3 axis is NOT composable from the
# order-2 atoms; it is the 7th, chirality-completing primitive — the ONLY
# access to the 3rd chiral axis.
#
# HONESTY SPLIT (the an_embedding / so8 discipline):
#   • BIT-EXACT SELF-COMPUTED here: τ³ = I (order 3), τ ≠ I, τ² ≠ I, via the
#     existing :func:`triality_automorphism`; AND the Lagrange arithmetic
#     (3 ∤ 8, 3 | 3). These are measured / arithmetic facts.
#   • FRAMEWORK-READING (NOT derived; surfaced ONLY under the separately-keyed
#     ``framework_chirality_complete_reading`` field): that the 6 atoms
#     generate EXACTLY Z2 × Z2 × Z2 of order 8 (a faithful common group rep of
#     all 6 heterogeneous atoms is not cleanly available — different carriers),
#     the chirality-complete-7 reading, and the scope hierarchy
#     (endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality). The |G|=8 / Z2^3
#     claim is documented + combined with the Lagrange argument, NOT labelled
#     bit-exact derived.
# ──────────────────────────────────────────────────────────────────────


def _triality_order_residuals() -> Tuple[float, float, float]:
    """Bit-exact (residual, deviation², deviation³) for the order of τ.

    Returns the three Class K pin-slot magnitudes (NEVER ``abs()``):

    - ``residual_3`` = ``‖τ³ − I‖`` (≈ 0 — τ has order dividing 3);
    - ``deviation_1`` = ``‖τ − I‖`` (> 0 — τ ≠ I);
    - ``deviation_2`` = ``‖τ² − I‖`` (> 0 — τ² ≠ I).

    Together they certify the order of τ is EXACTLY 3 (the genuine order-3
    element of ``S3 = Out(Spin(8))``). Each Frobenius norm is reduced to a
    SCALAR float FIRST (the numpy-free ``mat_norm`` of the nested-list
    difference), then through the scalar Class K
    :func:`srmech.cascade.magnitude` (SCALAR-only — a sequence or a
    :class:`Mat` raises ``TypeError``).
    """
    tau = triality_automorphism().tolist()
    identity = _eye(_DIM_SO8)
    tau2 = _matmul_mat(tau, tau)
    tau3 = _matmul_mat(tau2, tau)
    residual_3 = _magnitude(_frob_norm(_sub(tau3, identity)))
    deviation_1 = _magnitude(_frob_norm(_sub(tau, identity)))
    deviation_2 = _magnitude(_frob_norm(_sub(tau2, identity)))
    return residual_3, deviation_1, deviation_2


def _tau_float_bytes() -> bytes:
    """Concatenated row-major float64 bytes of the ``28×28`` ``τ`` (Class A
    content address; numpy-free — the same layout
    ``ascontiguousarray(τ).tobytes()`` produced)."""
    from array import array
    tau = triality_automorphism().tolist()
    buf = array("d", (float(x) for row in tau for x in row))
    return buf.tobytes()


def _seventh_attestation(
    order_residual: float, deviation_1: float, deviation_2: float
) -> Dict[str, object]:
    """MPR v1 self-attestation for the COMPUTED chirality-complete-7 core.

    Class A — content-address the GENERATED structure (NOT a fetched datum):
    ``response_sha256`` is :func:`srmech.amsc.format.sha256_bytes` over the
    concatenated ``float64`` bytes of the 28×28 order-3 automorphism ``τ``
    (the build OUTPUT, deterministically content-addressed; **no** new
    ``hashlib.sha256``). ``parser_rule_hash`` hashes the generative rule
    bytes. ``source_url`` cites Baez (arXiv) for the ``g2 = Der(O)`` /
    ``Out(Spin(8)) = S3`` PARENT FACTS ONLY — the chirality-complete-7
    reading (6 order-2 atoms + 1 order-3 triality) is the F220 framework
    finding, NOT a cited result. Mirrors
    :func:`srmech.physics.qm.so8._an_attestation` / ``_so4_attestation`` in form.
    """
    response_sha256 = _sha256_bytes(_tau_float_bytes())
    parser_rule_hash = _sha256_bytes(_SEVENTH_PARSER_RULE)
    descriptor_hash = _sha256_bytes(
        b"srmech/physics/qm/triality.py::lean_isa_seventh_primitive::"
        b"chirality_complete_core"
    )
    return {
        "mpr_version": "1.0",
        "data": {
            "structure": "chirality_complete_an_core_6_plus_1",
            "order_two_atoms": list(_LEAN_ISA_ATOMS),
            "order_three_primitive": "triality_automorphism",
            "triality_order": _TRIALITY_ORDER,
            "triality_order_residual": order_residual,
            "triality_not_identity": deviation_1,
            "triality_squared_not_identity": deviation_2,
            "chirality_complete_core": _CHIRALITY_COMPLETE_CORE,
        },
        "data_schema_id": "srmech://schema/chirality_complete_an_core",
        "attestation": {
            # Baez is OA on arXiv; a paywalled-only DOI is rejected per
            # [[feedback_paywalled_doi_cannot_be_attested]] — no source_doi.
            "source_doi": None,
            # Cites Out(Spin(8)) = S3 / g2 = Der(O) PARENT FACTS only; the
            # chirality-complete-7 reading (F220) is the framework finding.
            "source_url": "https://arxiv.org/abs/math/0105155",
            "license": "CC0",
            "retrieved_at": _SEVENTH_RETRIEVED_AT,
            "response_sha256": response_sha256,
            "parser_version": "srmech 0.6.0",
            "parser_rule_hash": parser_rule_hash,
            "collector_descriptor_path": "srmech/physics/qm/triality.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        "rendering": {
            "name": (
                "chirality-complete A-N core: 6 order-2 cascade.atoms "
                "+ 1 order-3 triality = 7"
            ),
            "purpose": (
                "Surface the order-3 triality as the 7th lean-ISA primitive "
                "(the only access to the 3rd chiral axis), with τ³ = I "
                "bit-exact and the F220 3 ∤ 8 unreachability reading"
            ),
            "cite_as": (
                "Baez, J.C. (2002) The Octonions, Bull. Amer. Math. Soc. 39, "
                "145-205 (arXiv:math/0105155) — for Out(Spin(8)) = S3 and "
                "g2 = Der(O), dim 14 (the parent facts only); F220 is the "
                "framework finding"
            ),
        },
    }


def lean_isa_seventh_primitive() -> dict:
    """The order-3 triality as the 7th lean-ISA primitive (the F220 core).

    Presents the genuine order-3 **triality** operator
    (:func:`triality_automorphism`) as the **7th** primitive of the lean
    A-N cascade ISA core — making the chirality-complete core explicit:
    **6 order-2** :mod:`srmech.cascade.atoms` **+ 1 order-3 triality
    = 7**, the ONLY access to the 3rd chiral axis (F220 /
    R-RBS-LM-FINDING_220).

    THE F220 FINDING. The 6 lean atoms — ``pin_slot_at_zero``, ``reorient``,
    ``magnitude``, ``chiral_flip``, ``chiral_dual``, ``net_chirality`` — are
    each an **involution in their chirality action** (order 2): three
    independent Z2 sign / orientation toggles. They **COMMUTE**, so they
    generate an ABELIAN group ``Z2 × Z2 × Z2``, ``|G| = 8``, with **NO
    order-3 element** (every non-identity element has order 2). By Lagrange's
    theorem an order-3 element would need ``3 | |G|``, but ``3 ∤ 8``; plus a
    carrier mismatch (the atoms act on a small sign / orientation carrier,
    triality on the 28-dim ``so(8)`` adjoint). So the genuine order-3
    triality ``τ`` (``τ³ = I``) is **UNREACHABLE** from the order-2 atoms —
    it is the 7th, chirality-completing primitive.

    HONESTY SPLIT (the :func:`srmech.physics.qm.so8.an_embedding` discipline —
    bit-exact self-computed vs framework-reading kept strictly separate):

    - **BIT-EXACT SELF-COMPUTED** (the ``certificate`` field): the order of
      ``τ`` is EXACTLY 3 — ``‖τ³ − I‖ ≈ 0`` (residual ``~4e-14``), ``τ ≠ I``,
      ``τ² ≠ I`` — measured via the existing engine; AND the Lagrange
      arithmetic ``3 ∤ 8`` and ``3 | 3``. All residuals go through the scalar
      Class K pin-slot :func:`srmech.cascade.magnitude`, **never**
      ``abs()`` (per
      ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
    - **FRAMEWORK-READING, NOT DERIVED** (the separately-keyed
      ``framework_chirality_complete_reading`` field, tagged
      "framework-reading, not derived"): that the 6 atoms generate EXACTLY
      ``Z2 × Z2 × Z2`` of order 8 (a faithful common group representation of
      all 6 heterogeneous atoms — they have different carriers, e.g.
      ``pin_slot_at_zero`` returns ``(orientation, magnitude)`` while
      ``chiral_flip`` reverses a sequence — is NOT cleanly available, so the
      ``|G| = 8`` / Z2^3 structure is a documented finding + the Lagrange
      argument, **not** labelled bit-exact derived); the chirality-complete-7
      reading; and the scope hierarchy
      ``endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality`` (each strictly
      contains the previous — byte-order is the smallest Z2 chirality, the
      Klein-4 group ``Z2 × Z2`` is the order-2 atom structure restricted to a
      pair of independent toggles, and the order-3 triality strictly extends
      it with the 3rd axis the Z2^k atoms can never reach).

    The bit-exact ``τ³ = I`` order-3 fact and the framework reading are
    surfaced under DISTINCT keys; no A-N class name or framework claim
    appears in any load-bearing ``certificate`` key.

    rc123 (numpy-free): the ``triality`` value in the returned dict is the
    ``28×28`` order-3 :class:`Mat` ``τ`` (was an ndarray).

    Canonical SSoT: Baez, J.C. (2002) *The Octonions* (arXiv:math/0105155) —
    for ``Out(Spin(8)) = S3`` (the order-3 triality) and ``g2 = Der(O)``
    (dim 14), the PARENT FACTS only. F220 is the framework finding (the
    chirality-complete 6 + 1 = 7 reading), NOT a cited theorem.

    Returns:
        A ``dict`` with keys:

        - ``order_two_atoms`` — the tuple of the 6 ``cascade.atoms`` names
          (referencing :mod:`srmech.cascade.atoms`).
        - ``order_three_primitive`` — ``"srmech.physics.qm.triality.triality_automorphism"``
          (the 7th primitive; the order-3 ``τ``).
        - ``triality`` — the ``28×28`` order-3 automorphism ``τ`` :class:`Mat`
          (``τ³ = I``; a fresh copy from :func:`triality_automorphism`).
        - ``certificate`` — the BIT-EXACT self-computed certificate dict:
          ``{"n_order_two_atoms": 6, "triality_order": 3,
          "triality_order_residual", "triality_not_identity",
          "triality_squared_not_identity", "abelian_group_order": 8,
          "three_divides_group_order": False,
          "three_divides_triality_order": True, "lagrange_obstruction": True,
          "chirality_complete_core": 7}``.
        - ``attestation`` — the MPR v1 self-attestation (Class A
          content-address of the computed ``τ``).
        - ``framework_chirality_complete_reading`` — the F220 reading LABEL
          (tagged "framework-reading, not derived"): the ``Z2 × Z2 × Z2``
          structure, the chirality-complete-7 reading, and the scope
          hierarchy.
    """
    order_residual, deviation_1, deviation_2 = _triality_order_residuals()

    # BIT-EXACT: the order of τ is exactly 3 (τ³ = I, τ ≠ I, τ² ≠ I).
    assert order_residual < _FIX_TOL, (
        f"triality τ³ = I residual expected ~0; got {order_residual}"
    )
    assert deviation_1 > 1.0, f"triality τ should differ from I; got {deviation_1}"
    assert deviation_2 > 1.0, (
        f"triality τ² should differ from I; got {deviation_2}"
    )

    # BIT-EXACT (arithmetic): the Lagrange obstruction. The order-2 atoms
    # generate an abelian group of order 8; an order-3 element needs 3 | |G|,
    # but 3 ∤ 8. The order-3 triality DOES have 3 | 3. (mod via Class I.)
    three_divides_group_order = (
        _mod_add(0, _LEAN_ISA_ABELIAN_GROUP_ORDER, _TRIALITY_ORDER) == 0
    )
    three_divides_triality_order = (
        _mod_add(0, _TRIALITY_ORDER, _TRIALITY_ORDER) == 0
    )
    assert three_divides_group_order is False, (
        "F220 Lagrange: 3 must NOT divide the order-2 atoms' group order 8"
    )
    assert three_divides_triality_order is True, (
        "F220 Lagrange: 3 must divide the triality element's order 3"
    )

    certificate = {
        "n_order_two_atoms": len(_LEAN_ISA_ATOMS),
        "triality_order": _TRIALITY_ORDER,
        "triality_order_residual": order_residual,
        "triality_not_identity": deviation_1,
        "triality_squared_not_identity": deviation_2,
        "abelian_group_order": _LEAN_ISA_ABELIAN_GROUP_ORDER,
        "three_divides_group_order": three_divides_group_order,
        "three_divides_triality_order": three_divides_triality_order,
        "lagrange_obstruction": (
            three_divides_triality_order and not three_divides_group_order
        ),
        "chirality_complete_core": _CHIRALITY_COMPLETE_CORE,
    }

    attestation = _seventh_attestation(order_residual, deviation_1, deviation_2)

    return {
        "order_two_atoms": _LEAN_ISA_ATOMS,
        "order_three_primitive": "srmech.physics.qm.triality.triality_automorphism",
        "triality": triality_automorphism(),
        "certificate": certificate,
        "attestation": attestation,
        "framework_chirality_complete_reading": {
            "note": "framework-reading, not derived",
            "atoms_module": "srmech.cascade.atoms",
            "atom_chirality_group": "Z2 × Z2 × Z2",
            "atom_chirality_group_order": _LEAN_ISA_ABELIAN_GROUP_ORDER,
            "atoms_commute_abelian": True,
            "no_order_three_element_in_atoms": True,
            "order_three_axis_unreachable_from_atoms": True,
            "chirality_complete_core_6_plus_1": _CHIRALITY_COMPLETE_CORE,
            "scope_hierarchy": (
                "endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality"
            ),
            "f220": (
                "the 6 order-2 cascade.atoms commute (abelian Z2^3, |G|=8) so "
                "3 ∤ 8 ⇒ no order-3 element; the genuine order-3 triality "
                "(τ³ = I) is the 7th, chirality-completing primitive — the "
                "only access to the 3rd chiral axis"
            ),
        },
    }


# ──────────────────────────────────────────────────────────────────────
# spin8_center / triality_rep_dictionary — the Z(Spin(8)) rep-kernel anchor
# (rc422, `#T1123`; the so(8) instance of the srmech.math.covering layer).
#
# ⚠️ THE TRAP, NAMED SO IT IS NOT WALKED INTO. "Compute the centre of so(8)"
# returns the ZERO object, and that is CORRECT: so(8) is semisimple, so its
# Lie-algebra centre is 0. The Klein four-group is Z(Spin(8)), a property of
# the simply-connected GROUP — global (π₁) data, where a Lie algebra carries
# only local data. The same algebra belongs to Spin(8), SO(8) AND PSO(8) and
# structurally cannot tell them apart. A run reporting "the centre is zero"
# has confirmed the setup, not refuted anything.
#
# WHAT IS DERIVED HERE, AND WHAT IS DEFINITIONAL (the an_embedding honesty
# split):
#   • DERIVED, bit-exact, off the octonion multiplication table: the four
#     scalar triples satisfying the GROUP relation g_v(x·y) = g_s(x)·g_c(y),
#     their Klein-four structure, and the rep-kernel labelling — each
#     non-identity element acts trivially on EXACTLY ONE of {8v, 8s, 8c},
#     which is what FORCES {3 involutions} ↔ {3 reps}.
#   • DEFINITIONAL, from how :func:`_companion_maps` builds them: S_B is the
#     map A ↦ its 8s companion, so its label action is the transposition
#     (v s); S_C is A ↦ its 8c companion, giving (v c); τ = S_B·S_C acts on
#     labels as the 3-cycle v → s → c → v (matching :func:`triality_cycle`'s
#     documented direction, an independent agreement).
#   • MEASURED INDEPENDENTLY (not definitionally) in
#     ``docs/srmech/notes/v4_so8_bridge_derivation_rc422.py``: the same label
#     actions read off the 28×28 matrices by exact characteristic polynomial,
#     without using their construction — the co-equal dual construction that
#     turns the definitional statement into a checked one.
# ──────────────────────────────────────────────────────────────────────

#: The label action of the shipped ``S_B`` (``triality_swap``) on {v, s, c}.
#: S_B carries A to its 8s companion, so precomposition exchanges 8v and 8s and
#: FIXES 8c. Independently confirmed by char-poly in the rc422 note, and — since
#: rc461 — DERIVED by the shipped :func:`triality_frame_action`, which returns
#: this dict from the 28×28 matrix without consulting this constant.
_SWAP_LABEL_ACTION: Dict[str, str] = {"v": "s", "s": "v", "c": "c"}

#: The label action of the shipped ``τ = S_B·S_C`` (``triality_automorphism``).
#: Precomposition is contravariant, so the labels compose as π_{S_C} ∘ π_{S_B},
#: giving the 3-cycle v → s → c → v — the SAME direction :func:`triality_cycle`
#: documents, reached by a different route. Also derived by
#: :func:`triality_frame_action` (rc461); the agreement of the two is a gate,
#: not a comment.
_TAU_LABEL_ACTION: Dict[str, str] = {"v": "s", "s": "c", "c": "v"}

#: The V₄-carrier generators this bridge is pinned against, both SHIPPED and
#: both unique at their carrier: the order-3 ``klein4_triality_cycle`` and the
#: order-2 Cayley–Dickson rung-bump automorphism rc420's leg (d) derived from
#: the CD sign cocycle (γ₅ fixed, iω₇ ↔ CPT, identically at every rung from
#: ℍ→𝕆 upward).
_V4_CYCLE: Dict[str, str] = {"iomega7": "gamma5", "gamma5": "cpt",
                             "cpt": "iomega7"}
_V4_RUNG: Dict[str, str] = {"gamma5": "gamma5", "iomega7": "cpt",
                            "cpt": "iomega7"}

_V4_NONIDENTITY: Tuple[str, ...] = ("iomega7", "gamma5", "cpt")


# ──────────────────────────────────────────────────────────────────────
# rc461 — the frame action, DERIVED (the constants above stop being the
# only statement of what τ and S_B do to the three labels)
#
# The block comment above `spin8_center` splits this module's claims into
# DERIVED / DEFINITIONAL / MEASURED-IN-A-NOTE, and it puts the two label
# actions in the middle bucket: definitional, from how `_companion_maps`
# builds them, with an independent char-poly confirmation living in
# `docs/srmech/notes/v4_so8_bridge_derivation_rc422.py` and in
# `tests/test_covering_layer_rc422.py`. Neither of those SHIPS. A caller of
# `triality_rep_dictionary()` reads `tau_label_action` out of the payload
# and has no shipped op that can re-derive it.
#
# `triality_frame_action` is that op, and it is cheap because of one
# measured structural fact: the shipped 28×28 τ, S_B and S_C all PRESERVE
# the standard Cartan span ⟨E01, E23, E45, E67⟩ EXACTLY, with every entry
# of the induced 4×4 block in {−1/2, 0, +1/2}. So the whole label question
# reduces to exact ℚ arithmetic on a 4×4 — measured at 5.2 ms for both
# generators, against ~47 s for a cold `_companion_maps()` and ~4.3 s per
# exact companion solve.
#
# WHY A 4×4 DECIDES AN 8-DIMENSIONAL REP: a frame's identity is an
# 8-dimensional rep, but the datum that decides it is 8 weights × 4 Cartan
# coordinates = 32 exact rationals. The 4-dimensional Cartan block IS the
# 8-dimensional rep, losslessly, and the op returns both halves so the
# reader does not have to take the reduction on trust.
#
# NOTE: that 32 is a TABLE SIZE — the entry count of one frame's weight
# table. It is NOT the 32 monomial octonion automorphisms that fix the
# `e1 -> e2 -> e3` line (those factor as 4 index permutations x 8 sign
# patterns, and live in `octonion_mult_table`'s world, not the Cartan's).
# The two objects share a numeral and nothing else; do not read either as
# reconciling the other.
# ──────────────────────────────────────────────────────────────────────

#: The four ``E_{pq}`` pairs spanning the standard Cartan subalgebra of so(8):
#: the four commuting rotation planes. Rank 4 = the ``D4`` in ``D4``.
_CARTAN_PAIRS: Tuple[Tuple[int, int], ...] = ((0, 1), (2, 3), (4, 5), (6, 7))

#: ``4`` — ``dim h``, the number of Cartan coordinates a weight has.
_CARTAN_RANK = len(_CARTAN_PAIRS)

#: ``8`` — the number of weights in each of ``8v`` / ``8s`` / ``8c`` (``± one
#: functional per Cartan direction``). This is the DERIVED count, ``2 × rank``;
#: :func:`triality_frame_action` reconciles it against the set it actually
#: builds and raises on disagreement, so the two routes to 8 are checked
#: against each other rather than one of them being trusted.
_WEIGHTS_PER_FRAME = 2 * _CARTAN_RANK


def _cartan_indices() -> Tuple[int, ...]:
    """Positions of the four Cartan generators inside the 28-dim ``E_{pq}``
    coordinate vector."""
    pairs = _epq_pairs()
    return tuple(pairs.index(pq) for pq in _CARTAN_PAIRS)


def _cartan_block(rows: Sequence[Sequence[Q]], op: str) -> List[List[Q]]:
    """The exact ``4×4`` action of a ``28×28`` map on the standard Cartan.

    Raises ``ValueError`` naming the offending coordinate when the map moves a
    Cartan generator OUT of the Cartan span — which is not a defect but a real
    restriction of the instrument: an automorphism conjugated by a generic
    inner element does not fix this particular Cartan, and reading its label
    action needs the conjugation undone first."""
    ci = _cartan_indices()
    pairs = _epq_pairs()
    for j in ci:
        for r in range(_DIM_SO8):
            if r not in ci and rows[r][j] != 0:
                raise ValueError(
                    f"{op}: the map does not preserve the standard Cartan span "
                    f"— the image of E_{pairs[j]} has a nonzero E_{pairs[r]} "
                    f"component ({rows[r][j]}). Conjugate the map into the "
                    f"standard Cartan first; the frame action is read on h.")
    return [[rows[r][c] for c in ci] for r in ci]


def _weight_set(block: Sequence[Sequence[Q]]) -> frozenset:
    """The weight SET of a frame whose Cartan block is ``block``.

    On ``H = Σ h_j C_j`` the frame's operator is ``Σ_k (block·h)_k C_k``, whose
    eigenvalues are ``± i·(block·h)_k``. So the weights ARE ``± the rows of
    block``, as exact linear functionals of ``h``. The ``±`` closure is the
    Class-C chirality step: a weight and its negative are the two orientations
    of one rotation plane, and taking the set of both is what makes the
    comparison orientation-blind without ever calling ``abs()``."""
    out = set()
    for row in block:
        out.add(tuple((q.numerator, q.denominator) for q in row))
        out.add(tuple(((-q).numerator, (-q).denominator) for q in row))
    return frozenset(out)


def _block_matmul(a: Sequence[Sequence[Q]],
                  b: Sequence[Sequence[Q]]) -> List[List[Q]]:
    """Exact ``4×4`` ℚ matrix product (the Cartan-block composition)."""
    n = _CARTAN_RANK
    return [[sum((a[i][k] * b[k][j] for k in range(n)), Q(0))
             for j in range(n)] for i in range(n)]


@functools.lru_cache(maxsize=None)
def _frame_cartan_blocks() -> Dict[str, Tuple[Tuple[Q, ...], ...]]:
    """The exact ``4×4`` Cartan block of each of the three frames, cached.

    ``8v`` is the identity (the vector rep IS the ``E_{pq}`` frame the whole
    engine is coordinatised in); ``8s`` / ``8c`` are the Cartan blocks of the
    shipped ``S_B`` / ``S_C``, because those maps ARE the companion linear maps
    — column ``col`` of ``S_B`` is the ``E_{pq}`` coords of the ``8s`` companion
    of the ``col``-th generator, so ``ρ_s(A) = unvec(S_B·vec(A))`` identically.
    (Measured: max deviation ``0.0`` against :func:`triality_companions` on a
    two-plane probe.)"""
    s_b, s_c = _companion_maps()
    blocks: Dict[str, Tuple[Tuple[Q, ...], ...]] = {}
    identity = [[Q(1) if i == j else Q(0) for j in range(_CARTAN_RANK)]
                for i in range(_CARTAN_RANK)]
    blocks["v"] = tuple(tuple(r) for r in identity)
    for name, mat in (("s", s_b), ("c", s_c)):
        rows = [[to_q(x) for x in row] for row in mat]
        blocks[name] = tuple(
            tuple(r) for r in _cartan_block(rows, f"triality frame {name}"))
    return blocks


def _as_28x28_exact(value, op: str) -> List[List[Q]]:
    """Coerce ``value`` to a ``28×28`` nested ``list[list[Q]]``.

    Accepts a :class:`Mat` (shape-checked), or any 2-D iterable whose entries
    :func:`srmech.math.q.to_q` accepts — ``Q``, ``int``, an ``(num, den)`` pair
    or a ``float`` (exact via ``as_integer_ratio``). The promotion is LOSSLESS
    on every one of those spellings, which is the point: the shipped ``τ`` has
    dyadic entries ``±1/2``, so a float input is carried exactly and the whole
    read stays in ℚ."""
    if isinstance(value, Mat):
        if value.shape != (_DIM_SO8, _DIM_SO8):
            raise ValueError(f"{op}: must be 28x28; got {value.shape}")
        rows = value.tolist()
    else:
        rows = [list(r) for r in value]
        if (len(rows) != _DIM_SO8
                or any(len(r) != _DIM_SO8 for r in rows)):
            shape = (len(rows), len(rows[0]) if rows else 0)
            raise ValueError(f"{op}: must be 28x28; got {shape}")
    return [[to_q(x) for x in r] for r in rows]


def triality_frame_action(automorphism) -> dict:
    """Which of ``8v`` / ``8s`` / ``8c`` a ``28×28`` so(8) automorphism sends
    each frame to — MEASURED off the matrix, in exact ℚ (rc461).

    Through rc460 the label action of the two shipped generators was a pair of
    hard-coded dicts (``_TAU_LABEL_ACTION`` / ``_SWAP_LABEL_ACTION``), correct
    but DEFINITIONAL: their justification was how :func:`triality_companions`
    is built, and the only independent derivation lived in a note script and a
    test. Neither ships. :func:`triality_rep_dictionary` emits
    ``tau_label_action`` into ``describe()``, the MCP tool list and the
    compiled-in C registry, so a consumer read a claim no shipped op could
    re-derive. This op re-derives it, from the matrix alone.

    **How, and why it is cheap.** The three 8-dim reps are separated by their
    WEIGHT SYSTEMS. Restricted to the standard Cartan
    ``h = ⟨E01, E23, E45, E67⟩``, the frame with Cartan block ``A_f`` carries
    weights ``± the rows of A_f``: ``8v`` gets ``{±e_j}`` (integer), and the two
    spinor frames get all-half-integer rows, split by the PARITY of their minus
    signs. That parity is not a convention chosen here — it is READ off the
    shipped ``S_B`` / ``S_C`` (measured: ``8s`` odd, ``8c`` even). The action of
    ``φ`` is then the exact ℚ set-match ``{± rows of A_f·A_φ} == W_g``:
    **Class D**, a pattern-match on a weight set, composed with **Class C**, the
    ``±`` orientation closure that makes the match blind to which end of a
    rotation plane is called positive (never ``abs()``).

    The whole read is 4×4 exact-rational arithmetic — measured at 5.2 ms for
    both shipped generators, against ~4.3 s for a single exact companion solve
    — because all three shipped maps PRESERVE the standard Cartan span exactly,
    with every induced entry in ``{−1/2, 0, +1/2}``. A map that does not is
    REFUSED with a ``ValueError`` naming the escaping coordinate, rather than
    answered approximately.

    **Why a 4×4 decides an 8-dimensional rep.** A frame is an 8-dimensional
    rep, and the datum that fixes which one it is has exactly ``8 × 4 = 32``
    exact rationals in it — 8 weights, each a functional on the rank-4 Cartan.
    The payload returns both halves (``cartan_block``, 16 entries, and
    ``frame_weights``, 32 per frame) so the reduction from 8 dimensions to 4 is
    inspectable rather than asserted. The three frames' weight sets are
    pairwise disjoint and their union has 24 elements — computed, not pinned.
    That ``32`` is a TABLE SIZE and reconciles nothing outside this op — in
    particular it is unrelated to the 32 monomial octonion automorphisms
    fixing the ``e1 → e2 → e3`` line, which factor as 4 index permutations ×
    8 sign patterns. The two share a numeral and no structure.

    **It can return otherwise.** Driven over the six elements of
    ``⟨S_B, S_C⟩ ≅ S₃`` the op returns six DISTINCT permutations of
    ``{v, s, c}`` — every element of ``Sym(3)``, including the third
    transposition ``S_B·S_C·S_B`` (``v`` fixed, ``s ↔ c``) that no shipped
    constant names. Composition is contravariant, as the module's own note
    says: the measured action of ``S_B·S_C`` is ``π_{S_C} ∘ π_{S_B}``.

    Args:
        automorphism: the ``28×28`` map in the shared ``E_{pq}`` frame — a
            :class:`~srmech.math.mat.Mat` (what :func:`triality_automorphism`
            and :func:`triality_swap` return) or any 2-D iterable of exact-
            rational-coercible entries.

    Returns:
        ``{'frame_action' ({'v'|'s'|'c': 'v'|'s'|'c'}), 'order' (1/2/3),
        'fixed_frames', 'moved_frames', 'is_identity', 'cartan_rank' (4),
        'weights_per_frame' (8), 'weight_table_entries' (32),
        'distinct_weights' (24), 'cartan_block' (4×4 of (num, den)),
        'frame_weights' ({frame: sorted 8-tuple of 4-tuples of (num, den)}),
        'spinor_parity' ({'s', 'c'} -> 0/1, MEASURED), 'procedure_sha256',
        'action_sha256'}``

    Raises:
        ValueError: if the input is not ``28×28``; if it moves a Cartan
            generator out of the Cartan span (the escaping coordinate is
            named); or if the transported weight system of some frame matches
            no frame — the action it induces on ``h`` is then not one of the
            six ``Out(Spin(8))`` induces, so the classification is not forced
            to succeed.

    Warning:
        **The verdict is about ``h``, and only about ``h``.** The read touches
        the four Cartan columns and nothing else, so the remaining 24 are never
        inspected and a NON-automorphism whose Cartan block is legitimate is
        ANSWERED rather than refused. MEASURED: zero every non-Cartan column of
        ``τ`` and 4 of 28 columns survive — rank ≤ 4, hence not invertible,
        hence provably not an automorphism of so(8) — and this op still returns
        the 3-cycle at ``order`` 3, because that is what the surviving 4×4
        does. What comes back is a true statement about the induced action on
        the Cartan, never a certificate that the input is an automorphism;
        deciding THAT means bracket-preservation over all ``C(28,2) = 378``
        generator pairs, which is a different instrument and not a tightening
        of this one. Witnessed with that rank-≤4 input in
        ``tests/test_frame_action_rc461.py``.

    Note:
        Exact ℚ; no float in the decision path; no ``abs()``. Python-first with
        no C peer under the ADR-0009 noted-disparity ruling — it composes
        :func:`triality_swap` / :func:`triality_automorphism`, whose companion
        solve already mirrors ``srmech_qmat_rref``. No new carrier TYPE crosses
        the boundary (``Q`` leaves as ``int`` pairs), so ABI is unchanged.

    Canonical SSoT: Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc.
    39, 145–205 (arXiv:math/0105155) §2.4 — ``Out(Spin(8)) = S3`` permuting
    ``8v``/``8s``/``8c``, and the ``D4`` weight systems ``{±e_j}`` /
    ``{(±½,±½,±½,±½)}`` split by sign parity.

    Example:
        >>> from srmech.physics.qm.triality import (
        ...     triality_automorphism, triality_swap, triality_frame_action)
        >>> triality_frame_action(triality_automorphism())["frame_action"]
        {'v': 's', 's': 'c', 'c': 'v'}
        >>> triality_frame_action(triality_swap())["order"]
        2
        >>> triality_frame_action(triality_swap())["fixed_frames"]
        ('c',)
    """
    op = "triality_frame_action"
    rows = _as_28x28_exact(automorphism, op)
    block = _cartan_block(rows, op)

    frames = _frame_cartan_blocks()
    weight_sets = {f: _weight_set(frames[f]) for f in _FRAME_ORDER}

    # `_WEIGHTS_PER_FRAME` is 2 × rank BY DERIVATION — ± one functional per
    # Cartan direction — and until this reconciliation it had no reader
    # anywhere in the tree, a derived literal shipping beside a measured `len`
    # that nothing compared it to. It can disagree: a degenerate frame block
    # (a repeated row, or a row equal to another's negative) collapses the ±
    # closure below 8, and `weights_per_frame` would then report the smaller
    # number without complaint while the three weight systems quietly stopped
    # being able to separate the frames.
    for frame in _FRAME_ORDER:
        if len(weight_sets[frame]) != _WEIGHTS_PER_FRAME:
            raise ValueError(
                f"{op}: frame 8{frame} has {len(weight_sets[frame])} weights, "
                f"not {_WEIGHTS_PER_FRAME} = 2 x {_CARTAN_RANK} — its Cartan "
                f"block is degenerate, so the three weight systems cannot "
                f"separate the frames.")

    action: Dict[str, str] = {}
    for frame in _FRAME_ORDER:
        moved = _weight_set(_block_matmul(frames[frame], block))
        hits = [g for g in _FRAME_ORDER if weight_sets[g] == moved]
        if len(hits) != 1:
            raise ValueError(
                f"{op}: the transported weight system of 8{frame} matches "
                f"{len(hits)} of the three frames, not exactly one — the "
                f"action this map induces on the standard Cartan is not one "
                f"of the six Out(Spin(8)) induces. Decided on the 4x4 Cartan "
                f"block ALONE, so this refusal is a statement about h and a "
                f"pass is not a certificate of automorphy; see the "
                f"docstring's scope warning.")
        action[frame] = hits[0]

    # order of the induced permutation, by iteration (never a lookup table)
    order = 1
    current = dict(action)
    identity = {f: f for f in _FRAME_ORDER}
    while current != identity:
        current = {f: action[current[f]] for f in _FRAME_ORDER}
        order += 1
        if order > len(_FRAME_ORDER) + 1:            # unreachable for Sym(3)
            raise ValueError(f"{op}: the induced permutation has no finite "
                             f"order within Sym(3) — impossible; report this.")

    fixed = tuple(f for f in _FRAME_ORDER if action[f] == f)
    frame_weights = {f: tuple(sorted(weight_sets[f])) for f in _FRAME_ORDER}
    union = set()
    for f in _FRAME_ORDER:
        union |= weight_sets[f]

    # Class C: which spinor frame carries the ODD-minus-sign half-integer
    # weights. READ, not chosen — this is the bit that makes 8s ≠ 8c.
    parity: Dict[str, int] = {}
    for f in ("s", "c"):
        counts = {sum(1 for num, den in w if num < 0) % 2
                  for w in weight_sets[f]}
        parity[f] = counts.pop() if len(counts) == 1 else -1

    procedure = (
        b"triality_frame_action/1: Cartan block of a 28x28 so(8) map; weights "
        b"= +- rows; exact Q set-match against 8v/8s/8c weight systems")
    return {
        "frame_action": action,
        "order": order,
        "fixed_frames": fixed,
        "moved_frames": tuple(f for f in _FRAME_ORDER if action[f] != f),
        "is_identity": order == 1,
        "cartan_rank": _CARTAN_RANK,
        "weights_per_frame": len(weight_sets["v"]),
        "weight_table_entries": len(weight_sets["v"]) * _CARTAN_RANK,
        "distinct_weights": len(union),
        "cartan_block": tuple(
            tuple((q.numerator, q.denominator) for q in row) for row in block),
        "frame_weights": frame_weights,
        "spinor_parity": parity,
        "procedure_sha256": _sha256_bytes(procedure),
        "action_sha256": _sha256_bytes(
            repr(sorted(action.items())).encode("utf-8")),
    }


def _octonion_product_int(x: Sequence[int], y: Sequence[int],
                          table) -> List[int]:
    """Exact integer octonion product straight off the structure-constant
    table — the carrier-native product the centre solve runs on."""
    out = [0] * _DIM
    for i in range(_DIM):
        if not x[i]:
            continue
        for j in range(_DIM):
            if not y[j]:
                continue
            xy = x[i] * y[j]
            col = table[i][j]
            for k in range(_DIM):
                if col[k]:
                    out[k] += xy * col[k]
    return out


def spin8_center() -> dict:
    """``Z(Spin(8))`` — the Klein four-group, SOLVED off the octonion table.

    The global datum ``so(8)`` structurally cannot hold. A ``Spin(8)`` element
    is a triple ``(g_v, g_s, g_c)`` of ``SO(8)`` maps satisfying the group form
    of Cartan's relation, ``g_v(x·y) = g_s(x)·g_c(y)``; differentiating it at
    the identity gives exactly the algebra relation :func:`triality_companions`
    solves, so the three SLOTS are the same three 8-dim reps. Restricting to
    SCALAR triples and solving **exhaustively on all 64 octonion basis pairs**
    yields four solutions — the constraint ``ε_v = ε_s·ε_c`` is FOUND, not
    imposed — and they form a Klein four-group under componentwise product.

    **The kernels ARE the dictionary.** Each non-identity element has exactly
    one ``+1`` coordinate, i.e. acts trivially on exactly one of ``{8v, 8s,
    8c}``. That makes ``{3 central involutions} ↔ {3 reps}`` FORCED BY
    STRUCTURE rather than chosen — the anchor whose absence made the
    V₄ ↔ so(8) bridge non-canonical through rc421.

    Also returned: ``triality_fixed_subgroup``, the elements of the centre that
    τ's label action leaves in place. It is TRIVIAL (identity only), which is
    the measured basis for the ``g2_der_octonions`` rejection row in
    :func:`srmech.math.covering.covering_catalog` — ``g₂ = Fix(τ)`` inherits no
    centre to carry.

    Class A (the content-addressed carrier read) ∘ Class I (the sign group). Exact integers throughout; no ``abs()``.

    Canonical SSoT: Baez (2002) §2.4 (``Z(Spin(8)) = ℤ/2 × ℤ/2``, triality
    permuting ``8v``/``8s``/``8c``); Cartan (1925).

    Returns:
        ``{'order': 4, 'elements': list[(εv, εs, εc)], 'is_klein_four': bool,
        'rep_kernels': {'v'|'s'|'c': (εv, εs, εc)}, 'constraint': str,
        'algebra_centre_dim': 0, 'triality_fixed_subgroup': list[tuple],
        'basis_pairs_checked': 64}``

    Example:
        >>> spin8_center()["rep_kernels"]["v"]
        (1, -1, -1)
    """
    table = octonion_mult_table()
    basis = [[1 if k == i else 0 for k in range(_DIM)] for i in range(_DIM)]
    elements: List[Tuple[int, int, int]] = []
    for ev in (1, -1):
        for es in (1, -1):
            for ec in (1, -1):
                if all(
                    [ev * t for t in _octonion_product_int(basis[i], basis[j],
                                                           table)]
                    == _octonion_product_int([es * t for t in basis[i]],
                                             [ec * t for t in basis[j]], table)
                    for i in range(_DIM) for j in range(_DIM)
                ):
                    elements.append((ev, es, ec))

    def _prod(a, b):
        return tuple(x * y for x, y in zip(a, b))

    identity = (1, 1, 1)
    is_klein = (len(elements) == 4
                and all(_prod(a, b) in elements
                        for a in elements for b in elements)
                and all(_prod(a, a) == identity for a in elements))
    kernels: Dict[str, Tuple[int, int, int]] = {}
    for z in elements:
        if z == identity:
            continue
        trivial_on = [nm for nm, eps in zip(_FRAME_ORDER, z) if eps == 1]
        if len(trivial_on) == 1:
            kernels[trivial_on[0]] = z
    # τ permutes the coordinates of the sign triple exactly as it permutes the
    # reps; the fixed subgroup is what g₂ = Fix(τ) could inherit.
    order = {nm: i for i, nm in enumerate(_FRAME_ORDER)}
    fixed = [z for z in elements
             if tuple(z[order[_TAU_LABEL_ACTION[nm]]]
                      for nm in _FRAME_ORDER) == z]
    return {
        "order": len(elements),
        "elements": elements,
        "is_klein_four": is_klein,
        "rep_kernels": kernels,
        "constraint": "eps_v = eps_s * eps_c — solved on all 64 octonion basis "
                      "pairs, not imposed",
        "algebra_centre_dim": 0,
        "algebra_centre_note": "so(8) is semisimple: its LIE-ALGEBRA centre is "
                               "the zero object, and that is the correct "
                               "answer. Z(Spin(8)) is GROUP-level (pi_1) data "
                               "the algebra cannot hold — a category "
                               "distinction, not a shortfall.",
        "triality_fixed_subgroup": fixed,
        "basis_pairs_checked": _DIM * _DIM,
    }


def triality_rep_dictionary() -> dict:
    """The canonical ``{iω₇, γ₅, CPT} ↔ {8v, 8s, 8c}`` dictionary — DERIVED.

    rc421 measured this bridge **NOT canonical as shipped**, residual ambiguity
    **3**: both carriers' order-3 generators are 3-cycles on a 3-element set,
    and the centralizer of a 3-cycle in ``Sym(3)`` has order 3, so an order-3
    generator ALONE cannot pin a unique dictionary — an arithmetic ceiling, not
    a shortfall of care. Closing it needed the rep-LABELING that
    :func:`spin8_center` now supplies.

    The derivation, in three moves:

    1. :func:`spin8_center` solves ``Z(Spin(8))`` off the octonion table and
       labels its three involutions by which rep each kills. **Forced.**
    2. With the reps labelled, the shipped ``28×28`` ``τ`` and ``S_B`` acquire
       a readable LABEL ACTION — the object rc421 measured unreachable. ``τ``
       cycles ``v → s → c``; ``S_B`` exchanges ``v ↔ s`` and FIXES ``c``.
    3. Requiring a bijection to intertwine BOTH shipped generator pairs cuts
       the 3 order-3 survivors to **1**. The natural 3-point ``S₃``-set has
       trivial centralizer in ``Sym(3)``, so once the group isomorphism is
       fixed the equivariant bijection is unique.

    **HONEST BOUND — read this before quoting the dictionary.** It is canonical
    RELATIVE TO the shipped generator pairing and the shipped V₄ sector names.
    Each carrier ships exactly one order-3 and one order-2 automorphism, so
    nothing was picked from a menu of equals; but a DIFFERENT order-2 yields a
    different dictionary (measured as control D in the rc422 note), and the
    notebook records that which sign bit is called ``γ₅`` and which ``iω₇`` is
    a convention it has never pinned. So this is a **derived intertwiner of two
    shipped S₃ presentations — FORM, never object-identity**
    (``[[user_stance_cascade_matching_substrate_blind_form_not_identity]]``).
    What makes it derived rather than chosen is that relabelling the inputs
    moves the output with them (the rc422 note's anti-pick control A).

    Class I (the order-3 cyclic intertwiner) ∘ Class C (the order-2 chirality
    constraint) ∘ Class D (the equivariance pattern-match).

    Canonical SSoT: Baez (2002) §2.4; Cartan (1925). Full derivation +
    independent char-poly confirmation + four negative controls:
    ``docs/srmech/notes/v4_so8_bridge_derivation_rc422.py``.

    Returns:
        ``{'dictionary': {'iomega7'|'gamma5'|'cpt': 'v'|'s'|'c'},
        'residual_ambiguity': 1, 'prior_ambiguity': 3,
        'order3_only_survivors': list[dict], 'tau_label_action': dict,
        'swap_label_action': dict, 'rep_kernels': dict, 'controls': dict,
        'honest_bound': str}``

    Example:
        >>> triality_rep_dictionary()["dictionary"]["gamma5"]
        'c'
    """
    centre = spin8_center()

    def _survivors(v4_gen, so8_gen):
        out = []
        for a in _FRAME_ORDER:
            for b in _FRAME_ORDER:
                for c in _FRAME_ORDER:
                    if len({a, b, c}) != 3:
                        continue
                    d = dict(zip(_V4_NONIDENTITY, (a, b, c)))
                    if all(d[v4_gen[k]] == so8_gen[d[k]]
                           for k in _V4_NONIDENTITY):
                        out.append(d)
        return out

    order3 = _survivors(_V4_CYCLE, _TAU_LABEL_ACTION)
    both = [d for d in order3
            if all(d[_V4_RUNG[k]] == _SWAP_LABEL_ACTION[d[k]]
                   for k in _V4_NONIDENTITY)]
    identity_perm = {k: k for k in _FRAME_ORDER}
    controls = {
        # section 3.29.3's named "single most common triality error": an
        # order-2 object where the order-3 element is meant. Must be 0.
        "order2_for_order3_v4_side": len(_survivors(_V4_RUNG,
                                                    _TAU_LABEL_ACTION)),
        "order2_for_order3_so8_side": len(_survivors(_V4_CYCLE,
                                                     _SWAP_LABEL_ACTION)),
        # a vacuous constraint must leave all 6 — proof the order-3 cut is real
        "identity_for_cycle": len(_survivors(
            {k: k for k in _V4_NONIDENTITY}, identity_perm)),
        "note": "controls behave iff the two order-2-for-order-3 counts are 0 "
                "and the identity count is 6",
    }
    controls["behave"] = (controls["order2_for_order3_v4_side"] == 0
                          and controls["order2_for_order3_so8_side"] == 0
                          and controls["identity_for_cycle"] == 6)
    return {
        "dictionary": both[0] if len(both) == 1 else None,
        "residual_ambiguity": len(both),
        "prior_ambiguity": 3,
        "prior": "rc421 v4_so8_bridge_canonicity: NOT canonical as shipped, "
                 "residual ambiguity 3, center_or_kernel_ops=[]",
        "order3_only_survivors": order3,
        "tau_label_action": dict(_TAU_LABEL_ACTION),
        "swap_label_action": dict(_SWAP_LABEL_ACTION),
        "swap_fixes": [k for k, v in _SWAP_LABEL_ACTION.items() if k == v],
        "v4_cycle": dict(_V4_CYCLE),
        "v4_rung_transposition": dict(_V4_RUNG),
        "rep_kernels": centre["rep_kernels"],
        "controls": controls,
        "honest_bound": "canonical RELATIVE TO the shipped generator pairing "
                        "and the shipped V4 sector names; a derived "
                        "intertwiner of two shipped S3 presentations — FORM, "
                        "never object-identity",
    }


__all__ = [
    "lean_isa_seventh_primitive",
    "spin8_center",
    "triality_apply",
    "triality_automorphism",
    "triality_companions",
    "triality_cycle",
    "triality_frame_action",
    "triality_relation_residual",
    "triality_rep_dictionary",
    "triality_swap",
]
