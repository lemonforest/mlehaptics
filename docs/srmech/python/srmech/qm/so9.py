"""The so(9)/Spin(9) rung — one Cayley-Dickson step above so(8)/triality.

The tower-traversal companion of :mod:`srmech.qm.so8` /
:mod:`srmech.qm.triality` (v0.9.0rc323, task #945). Where so(8) is the
28-dim adjoint acting on the octonions ``O`` (dim 8), ``so(9)`` is the
**36-dim** adjoint (``36 = C(9, 2)``) and its **16-dim real spinor**
``Δ₉`` acts on ``O ⊕ O = R^16`` — the ``Spin(9)`` isotropy group of the
octonionic projective plane. This module builds, all bit-exact and
numpy-free on the framework-native :class:`~srmech.amsc.mat.Mat` carrier:

1. **so(9) adjoint** — the 36 antisymmetric ``9x9`` ``E_{pq}`` generators
   (the vector / defining representation); rank exactly 36 (EXACT over ℚ,
   :func:`_q_rank`).
2. **The 16-dim real spinor** ``Δ₉`` — 9 real symmetric ``16x16`` Clifford
   generators ``Γ_a`` built from the octonion left-multiplications
   (:func:`srmech.qm.octonion.octonion_left_mult`), satisfying
   ``{Γ_a, Γ_b} = 2 δ_{ab} I`` (Clifford, exact-integer); the 36 spin(9)
   generators ``Σ_{ab} = ¼[Γ_a, Γ_b]`` are antisymmetric ``16x16``, rank 36,
   and obey the SAME ``so(9)`` structure constants as the ``E_{pq}``.
3. **The Spin(8) ⊂ Spin(9) branching** ``16 = 8_s ⊕ 8_c`` — the 28 generators
   ``Σ_{ab}`` with ``a, b ∈ {0..7}`` are block-diagonal, so the chirality
   operator ``Γ_8 = diag(I_8, −I_8)`` splits ``Δ₉`` into the two 8-dim
   Spin(8) half-spinors ``8_s`` (top block) and ``8_c`` (bottom block); the
   projectors ``P_± = ½(I ± Γ_8)`` commute with the whole Spin(8) subalgebra
   (branching residual bit-exact 0). This is the spinor face of the same
   ``8_v / 8_s / 8_c`` triality the so(8) engine reads on the vector side.

Per ``[[feedback_science_is_ssot_not_project]]`` — the SSoT is the math:
the octonion / Clifford / Spin(9) parent facts are cited to Baez (2002);
the specific 9-Γ construction, the rank-36, the Clifford relation, and the
``16 = 8_s ⊕ 8_c`` branching are this module's own bit-exact self-attesting
COMPUTATION (DERIVED — the arithmetic is shown), NOT a transcription. The
honesty split follows :func:`srmech.qm.so8.an_embedding`.

**The associator ↔ Spin(9)-holonomy conjecture** (research;
:func:`sedenion_holonomy_conjecture`) is tiered HONESTLY, respecting the
given bound **Spin(9) ≠ Aut(𝕊)** and
``[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`` (FORM,
not identity). Verdict **PARTIAL** — the octonion associator's symmetry
algebra ``g₂ = Der(O)`` DOES persist to the sedenion rung
(``Der(𝕊) = g₂``, dim 14, bit-exact) and DOES embed in ``spin(9)`` (as the
triality-diagonal ``g₂``, acting on ``Δ₉ = 𝕊`` as ``diag(D, D)`` with
sedenion-Leibniz residual 0), BUT it does NOT expand to fill ``Spin(9)``:
``dim(spin(9) ∩ Der(𝕊)) = 14 ≪ 36 = dim spin(9)``. So the "holonomy" the
associator generates at ``𝕊`` is valued in the SAME ``g₂`` (dim 14), not in
all of ``Spin(9)`` — nothing new appears at the ``𝕊`` rung. See
:func:`sedenion_holonomy_conjecture` for the full tiered arithmetic.

A-N placement (per ``[[feedback_no_privileged_primitive_classes]]``):

- ``so9_adjoint_basis`` / ``spin9_gamma_matrices`` / ``spin9_spinor_generators``
  — **Class M** (Clifford / HDC binding: the ``Γ_a`` bind the 16-dim spinor;
  the octonion ``L``-blocks are the Class-M binders, exactly as so(8)'s
  ``g2`` / ``L`` / ``R`` are).
- ``spin8_in_spin9_branching`` — **Class C** (chirality: the ``8_s / 8_c``
  chiral split is the ``Γ_8 = diag(I, −I)`` chirality operator; the ``½(I ±
  Γ_8)`` projectors) ∘ **Class L** (the block / eigenspace decomposition).
- ``sedenion_holonomy_conjecture`` — **Class D** (pattern-detect: the
  derivation-residual search + the ``spin(9) ∩ Der(𝕊)`` intersection) ∘
  **Class L** (the exact-ℚ rank / nullspace) ∘ **Class K** (the residual
  magnitude via :func:`srmech.amsc.cascade.magnitude`; **never** ``abs()``).

DETERMINISM: every construction is a fixed integer / dyadic build off the
attested octonion table + the Cayley-Dickson cocycle — **no RNG, no scipy,
no numpy**. All ranks are EXACT over ℚ (:func:`_q_rank`); all residuals are
exact-integer reduced to a scalar Frobenius norm through the Class-N
:func:`srmech.math.laplacian.mat_norm` then the scalar Class-K
:func:`srmech.amsc.cascade.magnitude` (never ``abs()``).

Canonical SSoT:

- Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145-205
  (arXiv:math/0105155) — the octonions, the Clifford algebras of ``O``,
  ``Spin(8)`` triality, and ``Spin(9)`` as the isometry group of ``OP²``
  (§2.4, §3.4). Cited for the PARENT facts only; the explicit build is this
  module's own computation.
- Schafer, R.D. (1954) *On the algebras formed by the Cayley-Dickson process*,
  Amer. J. Math. 76, 435-446 — flexibility + conjugation survive every rung;
  the derivation algebra ``Der(𝔸_n) = g₂`` for ``n ≥ 3`` (so ``Der(𝕊) = g₂``).
- Cartan, E. (1925) *Le principe de dualite ...*, Bull. Sci. Math. 49,
  361-374 — triality (the ``8_v / 8_s / 8_c`` context).
"""

from __future__ import annotations

import functools
from array import array
from typing import Dict, List, Sequence, Tuple

from srmech.amsc.q import Q                      # exact-ℚ rank carrier
from srmech.amsc.cascade import magnitude as _magnitude
from srmech.amsc.cascade.cayley_dickson import cd_basis_product as _cd_basis_product
from srmech.amsc.format import sha256_bytes as _sha256_bytes
from srmech.math.laplacian import mat_norm
from srmech.amsc.mat import Mat
from srmech.qm.octonion import octonion_left_mult
from srmech.qm.so8 import g2_subalgebra

# ── dimensions (the numbers the whole rung turns on) ──────────────────────
_DIM9 = 9                     #: so(9) acts on R^9 (the vector rep).
_DIM_SO9 = 36                 #: dim so(9) = C(9, 2).
_DIM8 = 8                     #: the octonion / so(8) dimension.
_DIM_SO8 = 28                 #: dim so(8) = C(8, 2) (the Spin(8) subalgebra).
_N_GAMMA = 9                  #: the 9 Clifford generators Γ_0 .. Γ_8.
_DIM_SPINOR = 16              #: dim Δ₉ = 2^⌊9/2⌋ (the real spinor) = dim_R 𝕊.
_DIM_HALF_SPINOR = 8          #: dim 8_s = dim 8_c (the Spin(8) half-spinors).
_DIM_G2 = 14                  #: dim g₂ = Der(O).
_DIM_DER_SEDENION = 14        #: dim Der(𝕊) = g₂ (Schafer 1954).
_SEDENION_DIM = 16            #: the sedenion real dimension.
_CHIRAL_INDEX = 8             #: the index of the chirality generator Γ_8.

#: Bit-exact residual tolerance (every structural residual here is EXACTLY 0
#: — the entries are integers / dyadic halves, so no float drift).
_TOL = 1e-12

#: A FIXED ISO timestamp for the self-attestations (deterministic on purpose,
#: NOT ``datetime.now()`` — the attestation of a GENERATED structure must be
#: reproducible; mirrors :data:`srmech.qm.so8._AN_RETRIEVED_AT`).
_RETRIEVED_AT = "2026-07-24T00:00:00Z"

#: The generative rules whose bytes are the ``parser_rule_hash`` provenance.
_GAMMA_RULE = (
    b"Gamma_a = [[0, L_{e_a}], [L_{e_a}^T, 0]] (a=0..7); "
    b"Gamma_8 = diag(I_8, -I_8); Sigma_ab = (1/4)[Gamma_a, Gamma_b]"
)
_BRANCHING_RULE = b"Spin(8) subset Spin(9): 16 = 8_s (+Gamma_8) + 8_c (-Gamma_8)"
_CONJECTURE_RULE = (
    b"spin(9) cap Der(S) = g2 (dim 14); Der(S)=g2 acts diag(D,D) on Delta_9=S"
)


# ──────────────────────────────────────────────────────────────────────
# Numpy-free integer linear algebra (the internal carrier is a nested
# ``list[list[int]]``; every so(9)/Spin(9) generator is exact-integer or
# exact-dyadic, so integer arithmetic is bit-exact. Mat only at the public
# boundary). No numpy.
# ──────────────────────────────────────────────────────────────────────

def _zeros(rows: int, cols: int) -> List[List[int]]:
    """A ``rows×cols`` nested list of ``0`` (numpy-free zeros builder)."""
    return [[0] * cols for _ in range(rows)]


def _eye(n: int) -> List[List[int]]:
    """The ``n×n`` integer identity as a nested list (numpy-free)."""
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def _transpose(a: Sequence[Sequence[int]]) -> List[List[int]]:
    """Nested-list transpose (numpy-free)."""
    return [[a[j][i] for j in range(len(a))] for i in range(len(a[0]))]


def _matmul(a: Sequence[Sequence[int]], b: Sequence[Sequence[int]]) -> List[List[int]]:
    """Integer nested-list matrix multiply ``A·B`` (numpy-free triple loop)."""
    n, k, m = len(a), len(b), len(b[0])
    out = [[0] * m for _ in range(n)]
    for i in range(n):
        ai = a[i]
        for t in range(k):
            v = ai[t]
            if v == 0:
                continue
            bt = b[t]
            oi = out[i]
            for j in range(m):
                oi[j] += v * bt[j]
    return out


def _sub(a, b) -> List[List[int]]:
    """Element-wise ``A − B`` (numpy-free)."""
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _scal(a, s: int) -> List[List[int]]:
    """Scalar-multiply a nested-list matrix by an int (numpy-free)."""
    return [[s * x for x in row] for row in a]


def _commutator(x, y) -> List[List[int]]:
    """Integer matrix commutator ``[X, Y] = XY − YX`` (numpy-free)."""
    return _sub(_matmul(x, y), _matmul(y, x))


def _block16(tl, tr, bl, br) -> List[List[int]]:
    """Assemble a ``16x16`` from four ``8x8`` integer blocks (numpy-free)."""
    out = _zeros(_DIM_SPINOR, _DIM_SPINOR)
    for i in range(_DIM8):
        for j in range(_DIM8):
            out[i][j] = tl[i][j]
            out[i][j + _DIM8] = tr[i][j]
            out[i + _DIM8][j] = bl[i][j]
            out[i + _DIM8][j + _DIM8] = br[i][j]
    return out


def _is_zero(a) -> bool:
    """True iff every entry of a nested-list matrix is exactly ``0``."""
    return all(x == 0 for row in a for x in row)


def _frob_scalar(a) -> float:
    """Frobenius-norm deviation of an integer matrix, reduced to a scalar
    FIRST through the Class-N numpy-free :func:`mat_norm`, then the scalar
    Class-K pin-slot :func:`magnitude` — NEVER ``abs()`` (per
    ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``)."""
    return _magnitude(mat_norm(Mat.from_rows([[float(x) for x in row] for row in a])))


def _vec_norm_scalar(v: Sequence[int]) -> float:
    """Euclidean norm of a flat integer vector via the Class-N ``mat_norm``,
    reduced through the scalar Class-K ``magnitude`` (never ``abs()``)."""
    return _magnitude(mat_norm([float(x) for x in v]))


def _q_rank(rows: Sequence[Sequence[int]]) -> int:
    """EXACT matrix rank of an integer ``rows`` matrix via RREF over ℚ.

    The numpy-free, float-free rank: every entry this module forms is an
    exact integer (the generators) or an exact dyadic (``¼[Γ, Γ]`` scaled
    back to integer for ranking), so a :class:`~srmech.amsc.q.Q` Gaussian
    elimination is exact and the rank is the pivot count — the same discipline
    as :func:`srmech.qm.so8._rank_exact`, but taking integer ROWS directly (no
    float snap needed; these entries ARE exact). Rank is scale-invariant, so a
    dyadic generator is ranked via its integer ``×4`` form.
    """
    m = [[Q(int(x)) for x in row] for row in rows]
    n_rows = len(m)
    n_cols = len(m[0]) if n_rows else 0
    rank = 0
    for col in range(n_cols):
        pivot = None
        for r in range(rank, n_rows):
            if m[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            continue
        m[rank], m[pivot] = m[pivot], m[rank]
        lead = m[rank][col]
        m[rank] = [x / lead for x in m[rank]]
        for r in range(n_rows):
            if r != rank and m[r][col] != 0:
                f = m[r][col]
                m[r] = [m[r][c] - f * m[rank][c] for c in range(n_cols)]
        rank += 1
        if rank == n_rows:
            break
    return rank


def _flatten(m: Sequence[Sequence[int]]) -> List[int]:
    """Row-major flatten of a nested-list matrix (numpy-free)."""
    return [x for row in m for x in row]


def _gen_bytes(mats: Sequence[Sequence[Sequence[int]]]) -> bytes:
    """Concatenated float64 bytes of integer matrices (Class A content
    address; the same row-major IEEE-754 little-endian layout
    :func:`srmech.qm.so8._gen_bytes` produces)."""
    out = bytearray()
    for m in mats:
        buf = array("d", (float(x) for row in m for x in row))
        out.extend(buf.tobytes())
    return bytes(out)


# ──────────────────────────────────────────────────────────────────────
# The octonion left-multiplication blocks + the 9 Clifford generators.
# ──────────────────────────────────────────────────────────────────────

def _lmat(i: int) -> List[List[int]]:
    """The ``8x8`` octonion left-multiplication ``L_{e_i}`` as an integer
    nested list (entries in ``{−1, 0, +1}``; ``L_{e_0} = I``). Built from the
    attested :func:`srmech.qm.octonion.octonion_left_mult` — the SAME
    Cayley-Dickson-from-H convention the whole so(8) engine uses.
    """
    e_i = [1 if k == i else 0 for k in range(_DIM8)]
    return [[int(round(x)) for x in row] for row in octonion_left_mult(e_i).tolist()]


@functools.lru_cache(maxsize=1)
def _gamma_lists() -> Tuple[Tuple[Tuple[int, ...], ...], ...]:
    """The 9 real symmetric ``16x16`` Clifford generators ``Γ_a`` (cached).

    ``Γ_a = [[0, L_{e_a}], [L_{e_a}^T, 0]]`` for ``a = 0..7`` (block
    off-diagonal, symmetric because the two blocks are transposes) and
    ``Γ_8 = diag(I_8, −I_8)``. They satisfy ``{Γ_a, Γ_b} = 2 δ_{ab} I_16``
    exactly (verified in :func:`spin9_gamma_matrices`). Memoised as an
    IMMUTABLE nested tuple; the public surface copies out a fresh ``Mat``.
    """
    z8 = _zeros(_DIM8, _DIM8)
    i8 = _eye(_DIM8)
    gammas: List[List[List[int]]] = []
    for a in range(_DIM8):
        la = _lmat(a)
        gammas.append(_block16(z8, la, _transpose(la), z8))
    gammas.append(_block16(i8, z8, z8, _scal(i8, -1)))   # Γ_8 = diag(I, −I)
    return tuple(tuple(tuple(row) for row in g) for g in gammas)


def _gamma_int() -> List[List[List[int]]]:
    """The 9 ``Γ_a`` as fresh mutable integer nested lists (numpy-free)."""
    return [[list(row) for row in g] for g in _gamma_lists()]


def _so9_index_pairs() -> Tuple[Tuple[int, int], ...]:
    """The 36 index pairs ``(a, b)``, ``0 <= a < b <= 8`` — the shared frame
    for both the ``9x9`` ``E_{pq}`` and the ``16x16`` ``Σ_{ab}`` (identical
    ordering so the two reps' structure constants line up)."""
    return tuple((a, b) for a in range(_N_GAMMA) for b in range(a + 1, _N_GAMMA))


@functools.lru_cache(maxsize=1)
def _s4_lists() -> Tuple[Tuple[Tuple[int, ...], ...], ...]:
    """The 36 integer commutators ``[Γ_a, Γ_b] = 4·Σ_{ab}`` (cached, ordered
    by :func:`_so9_index_pairs`). Kept as the ``×4`` integer form so ranks /
    brackets are exact-integer; the public :func:`spin9_spinor_generators`
    divides by 4 to the dyadic ``Σ_{ab}``."""
    gammas = _gamma_int()
    out = [_commutator(gammas[a], gammas[b]) for (a, b) in _so9_index_pairs()]
    return tuple(tuple(tuple(row) for row in m) for m in out)


def _s4_int() -> List[List[List[int]]]:
    """The 36 ``[Γ_a, Γ_b]`` as fresh mutable integer nested lists."""
    return [[list(row) for row in m] for m in _s4_lists()]


def _epq9(a: int, b: int) -> List[List[int]]:
    """The antisymmetric ``9x9`` ``E_{ab} = e_a e_b^T − e_b e_a^T``."""
    m = _zeros(_DIM9, _DIM9)
    m[a][b] = 1
    m[b][a] = -1
    return m


# ──────────────────────────────────────────────────────────────────────
# Public surface (1): the so(9) adjoint (vector rep) — 36 antisym 9x9.
# ──────────────────────────────────────────────────────────────────────

def so9_adjoint_basis() -> Tuple[Mat, ...]:
    """The 36 ``so(9)`` generators — antisymmetric ``9x9`` ``E_{pq}`` (the
    vector / defining representation), ``0 <= p < q <= 8``.

    ``dim so(9) = C(9, 2) = 36``; the rank of the 36 ``E_{pq}`` is verified
    EXACTLY 36 over ℚ (:func:`_q_rank`). This is the rung above
    :func:`srmech.qm.so8.so8_adjoint_basis` (dim 28 = ``C(8, 2)``): so(9)
    contains so(8) as the ``E_{pq}`` with ``p, q <= 7``.

    Class M (the antisymmetric-matrix binders of the vector rep).

    Canonical SSoT: Baez (2002) §2 (the rotation algebras ``so(n)``); the
    dim-36 rank is this op's own bit-exact computation.

    Returns:
        Tuple of 36 antisymmetric ``9x9`` real ``Mat`` spanning ``so(9)``.
    """
    gens = [_epq9(a, b) for (a, b) in _so9_index_pairs()]
    rank = _q_rank([_flatten(g) for g in gens])
    assert rank == _DIM_SO9, f"so(9) vector rep rank expected 36; got {rank}"
    return tuple(Mat.from_rows([[float(x) for x in row] for row in g]) for g in gens)


# ──────────────────────────────────────────────────────────────────────
# Public surface (2): the 9 Clifford Γ generators of Δ₉ (16-dim spinor).
# ──────────────────────────────────────────────────────────────────────

def _clifford_max_residual() -> float:
    """Max ``‖{Γ_a, Γ_b} − 2 δ_{ab} I‖`` over all pairs (exact-integer; 0)."""
    gammas = _gamma_int()
    ident2 = _scal(_eye(_DIM_SPINOR), 2)
    worst = 0.0
    for a in range(_N_GAMMA):
        for b in range(_N_GAMMA):
            anti = _sub(_matmul(gammas[a], gammas[b]), _scal(_matmul(gammas[b], gammas[a]), -1))
            expected = ident2 if a == b else _zeros(_DIM_SPINOR, _DIM_SPINOR)
            worst = max(worst, _frob_scalar(_sub(anti, expected)))
    return worst


def spin9_gamma_matrices() -> Tuple[Mat, ...]:
    """The 9 real symmetric ``16x16`` Clifford generators ``Γ_a`` of ``Δ₉``.

    ``Δ₉`` is the 16-dim REAL spinor representation of ``Spin(9)`` (``dim =
    2^⌊9/2⌋ = 16``); it acts on ``O ⊕ O = R^16``. The 9 generators are

    - ``Γ_a = [[0, L_{e_a}], [L_{e_a}^T, 0]]`` for ``a = 0..7`` (built from the
      octonion left-multiplications :func:`srmech.qm.octonion.octonion_left_mult`),
    - ``Γ_8 = diag(I_8, −I_8)`` (the chirality operator),

    and they satisfy the Clifford relation ``{Γ_a, Γ_b} = 2 δ_{ab} I_16``
    EXACTLY — verified bit-exact (max residual ``0.0``; the entries are
    integers in ``{−1, 0, +1}``). Because the ``Γ_a`` are real ``16x16``, this
    construction is itself the proof that ``Δ₉`` is a 16-dim REAL rep (the
    Clifford algebra ``Cl(9, 0)`` has a 16-dim real irreducible module).

    Class M (Clifford binding — the octonion ``L``-blocks bind the spinor).

    Canonical SSoT: Baez (2002) §2.3-2.4 + §3.4 (the octonionic ``Spin(9)`` /
    the Cayley plane); the explicit 9-Γ build + the Clifford verification are
    this op's own bit-exact computation.

    Returns:
        Tuple of 9 real symmetric ``16x16`` ``Mat`` with
        ``{Γ_a, Γ_b} = 2 δ_{ab} I``.
    """
    residual = _clifford_max_residual()
    assert residual < _TOL, f"Clifford {{Γ,Γ}}=2δI residual expected 0; got {residual}"
    gammas = _gamma_int()
    for g in gammas:                                  # symmetric (Γ_a^T = Γ_a)
        assert _is_zero(_sub(g, _transpose(g))), "a Γ generator is not symmetric"
    return tuple(Mat.from_rows([[float(x) for x in row] for row in g]) for g in gammas)


# ──────────────────────────────────────────────────────────────────────
# Public surface (3): the 36 spin(9) generators in the 16-dim spinor rep.
# ──────────────────────────────────────────────────────────────────────

def _so9_bracket_max_residual(gens: List[List[List[int]]], scale: int) -> float:
    """Max residual of the ``so(9)`` structure constants over all ordered
    pairs of the ``36`` generators ``gens`` (indexed by :func:`_so9_index_pairs`).

    ``[G_{ab}, G_{cd}] = δ_{bc} G_{ad} − δ_{ac} G_{bd} − δ_{bd} G_{ac} +
    δ_{ad} G_{bc}`` (the ``so(n)`` bracket, in the shared ``E_{pq}`` ordering).
    ``scale`` is the generator normalisation (``1`` for the ``E_{pq}`` vector
    rep; ``4`` for the ``×4``-integer ``S4 = 4Σ`` spinor rep, whose commutator
    carries an extra ``scale`` factor). Exact-integer; reduced through the
    scalar Class-K magnitude (never ``abs()``).
    """
    pairs = _so9_index_pairs()
    index = {p: i for i, p in enumerate(pairs)}

    def g_of(i: int, j: int) -> List[List[int]]:
        if i == j:
            return _zeros(len(gens[0]), len(gens[0][0]))
        s = 1 if i < j else -1
        return _scal(gens[index[(min(i, j), max(i, j))]], s)

    worst = 0.0
    for (a, b) in pairs:
        for (c, d) in pairs:
            lhs = _commutator(gens[index[(a, b)]], gens[index[(c, d)]])
            rhs = _zeros(len(gens[0]), len(gens[0][0]))
            if b == c:
                rhs = _sub(_scal(rhs, 1), _scal(g_of(a, d), -1))
            if a == c:
                rhs = _sub(rhs, g_of(b, d))
            if b == d:
                rhs = _sub(rhs, g_of(a, c))
            if a == d:
                rhs = _sub(_scal(rhs, 1), _scal(g_of(b, c), -1))
            rhs = _scal(rhs, scale)
            worst = max(worst, _frob_scalar(_sub(lhs, rhs)))
    return worst


def spin9_spinor_generators() -> Tuple[Mat, ...]:
    """The 36 ``spin(9)`` generators ``Σ_{ab} = ¼[Γ_a, Γ_b]`` in ``Δ₉``.

    Antisymmetric real ``16x16``, ordered by ``0 <= a < b <= 8``. They span
    ``spin(9)`` in the 16-dim real spinor representation: rank EXACTLY 36
    (verified over ℚ), and they obey the SAME ``so(9)`` structure constants as
    the ``9x9`` vector generators :func:`so9_adjoint_basis` (bracket residual
    bit-exact 0) — so ``Δ₉`` is a genuine ``spin(9) ≅ so(9)`` representation.
    Entries are dyadic (``{0, ±½, ±1}``), hence bit-exact in float64.

    Class M (Clifford binding — ``Σ_{ab}`` are the spinor-rep generators).

    Canonical SSoT: Baez (2002) §2.4 (the spinor reps of the octonionic
    Clifford algebras); the rank + structure-constant verification are this
    op's own bit-exact computation.

    Returns:
        Tuple of 36 antisymmetric real ``16x16`` ``Mat`` spanning ``spin(9)``.
    """
    s4 = _s4_int()                                    # 4·Σ, exact integer
    for m in s4:                                      # antisymmetric
        assert _is_zero(_sub(m, _scal(_transpose(m), -1))), "Σ is not antisymmetric"
    rank = _q_rank([_flatten(m) for m in s4])
    assert rank == _DIM_SO9, f"spin(9) spinor rank expected 36; got {rank}"
    bracket = _so9_bracket_max_residual(s4, scale=4)
    assert bracket < _TOL, f"spin(9) so(9)-bracket residual expected 0; got {bracket}"
    # divide the ×4 integer form down to the dyadic Σ = ¼[Γ, Γ] (exact halves).
    return tuple(
        Mat.from_rows([[x / 4.0 for x in row] for row in m]) for m in s4
    )


# ──────────────────────────────────────────────────────────────────────
# Public surface (4): the Spin(8) ⊂ Spin(9) branching 16 = 8_s ⊕ 8_c.
# ──────────────────────────────────────────────────────────────────────

def _spin8_pairs() -> List[Tuple[int, int]]:
    """The 28 index pairs ``(a, b)`` with ``a < b <= 7`` — the Spin(8)
    subalgebra generators (those NOT involving the chirality index 8)."""
    return [(a, b) for (a, b) in _so9_index_pairs() if b <= 7]


def _top_block(m: List[List[int]]) -> List[List[int]]:
    """The top-left ``8x8`` block of a ``16x16`` (the ``8_s`` action)."""
    return [[m[i][j] for j in range(_DIM8)] for i in range(_DIM8)]


def _bot_block(m: List[List[int]]) -> List[List[int]]:
    """The bottom-right ``8x8`` block of a ``16x16`` (the ``8_c`` action)."""
    return [[m[i + _DIM8][j + _DIM8] for j in range(_DIM8)] for i in range(_DIM8)]


def _branching_attestation(gammas, s4, extra: Dict[str, object]) -> Dict[str, object]:
    """MPR v1 self-attestation for the computed ``16 = 8_s ⊕ 8_c`` branching
    (Class A content-address over the Γ + Σ float64 bytes)."""
    response_sha256 = _sha256_bytes(_gen_bytes(list(gammas) + list(s4)))
    parser_rule_hash = _sha256_bytes(_BRANCHING_RULE)
    descriptor_hash = _sha256_bytes(b"srmech/qm/so9.py::spin8_in_spin9_branching")
    return {
        "mpr_version": "1.0",
        "data": dict(extra),
        "data_schema_id": "srmech://schema/spin8_in_spin9_branching",
        "attestation": {
            "source_doi": None,
            "source_url": "https://arxiv.org/abs/math/0105155",
            "license": "CC0",
            "retrieved_at": _RETRIEVED_AT,
            "response_sha256": response_sha256,
            "parser_version": "srmech 0.9.0",
            "parser_rule_hash": parser_rule_hash,
            "collector_descriptor_path": "srmech/qm/so9.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        "rendering": {
            "name": "Spin(8) ⊂ Spin(9): 16 = 8_s ⊕ 8_c branching",
            "purpose": (
                "Bit-exact branching of the 16-dim Spin(9) spinor Δ₉ under "
                "Spin(8): the 28 Σ_ab (a,b≤7) are block-diagonal, Γ_8=diag(I,−I) "
                "splits Δ₉ into the two Spin(8) half-spinors 8_s / 8_c"
            ),
            "cite_as": (
                "Baez, J.C. (2002) The Octonions, Bull. Amer. Math. Soc. 39, "
                "145-205 (arXiv:math/0105155) — for the octonionic Spin(9) / "
                "Spin(8) triality (the parent facts only); the branching is "
                "this op's own bit-exact computation"
            ),
        },
    }


@functools.lru_cache(maxsize=1)
def _branching_certificate() -> Dict[str, object]:
    """The cached bit-exact ``16 = 8_s ⊕ 8_c`` certificate (dims + residuals)."""
    gammas = _gamma_int()
    s4 = _s4_int()
    g8 = gammas[_CHIRAL_INDEX]
    sp8 = _spin8_pairs()
    index = {p: i for i, p in enumerate(_so9_index_pairs())}

    # (a) the 28 Spin(8) generators are block-diagonal (no off-block terms).
    off_block_worst = 0.0
    for p in sp8:
        m = s4[index[p]]
        tr = [[m[i][j + _DIM8] for j in range(_DIM8)] for i in range(_DIM8)]
        bl = [[m[i + _DIM8][j] for j in range(_DIM8)] for i in range(_DIM8)]
        off_block_worst = max(off_block_worst, _frob_scalar(tr), _frob_scalar(bl))

    # (b) Γ_8 (and so P_± = ½(I ± Γ_8)) commutes with the whole Spin(8) block.
    proj_worst = 0.0
    for p in sp8:
        proj_worst = max(proj_worst, _frob_scalar(_commutator(g8, s4[index[p]])))

    # (c) the two 8-dim blocks each carry a full FAITHFUL so(8) (rank 28) — the
    #     two Spin(8) half-spinors 8_s (top) and 8_c (bottom). Since dim so(8) =
    #     28, each block's 28 generators span ALL of so(8) (surjective).
    top_rank = _q_rank([_flatten(_top_block(s4[index[p]])) for p in sp8])
    bot_rank = _q_rank([_flatten(_bot_block(s4[index[p]])) for p in sp8])

    # (d) the two blocks carry DIFFERENT actions: for at least one generator
    #     index the top-block 8×8 ≠ the bottom-block 8×8 (so Δ₉ splits into two
    #     DISTINCT half-spinors, not two copies of one rep). The full
    #     inequivalence 8_s ≇ 8_c is the recognized rep-theory fact (Baez); the
    #     distinct-action witness below is the bit-exact support. (A stacked
    #     top+bottom span-rank check would be vacuous: both blocks span all 28
    #     dims of so(8), so a stacked rank is necessarily 28, NOT a distinguisher.)
    action_diff_worst = 0.0
    for p in sp8:
        m = s4[index[p]]
        action_diff_worst = max(
            action_diff_worst, _frob_scalar(_sub(_top_block(m), _bot_block(m)))
        )

    assert off_block_worst < _TOL, "Spin(8) generators are not block-diagonal"
    assert proj_worst < _TOL, "Γ_8 does not commute with the Spin(8) subalgebra"
    assert top_rank == _DIM_SO8 and bot_rank == _DIM_SO8, (
        f"half-spinor so(8) rank expected 28+28; got {top_rank}+{bot_rank}"
    )
    assert action_diff_worst > _TOL, (
        "the two half-spinor blocks carry the SAME action (expected distinct "
        "8_s / 8_c)"
    )

    return {
        "spinor_rep": {
            "spinor_dim": _DIM_SPINOR,
            "spin9_dim": _DIM_SO9,
            "clifford_max_residual": _clifford_max_residual(),
            "spinor_rank": _q_rank([_flatten(m) for m in s4]),
            "so9_bracket_max_residual": _so9_bracket_max_residual(s4, scale=4),
        },
        "branching": {
            "spinor_dim": _DIM_SPINOR,
            "spin8_generators": _DIM_SO8,
            "branch": (_DIM_HALF_SPINOR, _DIM_HALF_SPINOR),
            "branch_labels": ("8_s", "8_c"),
            "chirality_operator": "Gamma_8 = diag(I_8, -I_8)",
            "off_block_max_residual": off_block_worst,
            "projector_commutator_max_residual": proj_worst,
            "half_spinor_ranks": (top_rank, bot_rank),
            "half_spinor_action_difference": action_diff_worst,
            "half_spinors_distinct_actions": action_diff_worst > _TOL,
        },
    }


def spin8_in_spin9_branching() -> dict:
    """The bit-exact ``Spin(8) ⊂ Spin(9)`` embedding + the ``16 = 8_s ⊕ 8_c``
    spinor branching (with the ``Δ₉`` Clifford / spinor certificate).

    The 28 spinor generators ``Σ_{ab}`` with ``a, b ∈ {0..7}`` (i.e. NOT
    involving the chirality index 8) are all BLOCK-DIAGONAL on ``Δ₉ = O ⊕ O``
    (off-block residual bit-exact 0), so the chirality operator
    ``Γ_8 = diag(I_8, −I_8)`` commutes with the whole Spin(8) subalgebra and
    its eigenprojectors ``P_± = ½(I ± Γ_8)`` split ``Δ₉`` into two invariant
    8-dim subspaces:

        ``16 = 8_s (the +Γ_8 / top block) ⊕ 8_c (the −Γ_8 / bottom block)``,

    the two inequivalent Spin(8) HALF-SPINORS. Each block carries a full
    FAITHFUL ``so(8)`` (rank 28 — since ``dim so(8) = 28``, each block's
    generators span ALL of ``so(8)``), and the two blocks carry DIFFERENT
    actions (some generator's top block ≠ its bottom block, bit-exact) — so
    ``Δ₉`` splits into two DISTINCT half-spinors, not two copies of one rep.
    The full ``8_s ≇ 8_c`` inequivalence is the recognized representation-theory
    fact (Baez 2002); the distinct-action witness is this op's bit-exact
    support. This is the spinor-side face of the same ``8_v / 8_s / 8_c``
    triality the so(8) engine (:mod:`srmech.qm.triality`) reads on the vector
    side: ``8_v`` is the ``so(9)`` vector rep restricted to Spin(8), ``8_s`` /
    ``8_c`` are the two halves of ``Δ₉`` here.

    HONESTY: the branching ``16 → 8_s ⊕ 8_c`` under ``Spin(8) ⊂ Spin(9)`` is a
    standard representation-theory fact (Baez 2002 §2.4/§3.4 for the parent
    context); the specific block structure, the projector commutation, and the
    ``28 + 28`` half-spinor ranks are this op's OWN bit-exact self-attesting
    computation (DERIVED), NOT a transcription.

    Class C (chirality: the ``Γ_8`` chiral split / the ``½(I ± Γ_8)``
    projectors) ∘ Class L (the block / eigenspace decomposition).

    Canonical SSoT: Baez (2002) §2.4 + §3.4 (octonionic ``Spin(9)`` /
    ``Spin(8)`` triality).

    Returns:
        A ``dict`` with keys:

        - ``spinor_rep`` — the ``Δ₉`` certificate: ``{spinor_dim: 16,
          spin9_dim: 36, clifford_max_residual (≈0), spinor_rank: 36,
          so9_bracket_max_residual (≈0)}``.
        - ``branching`` — ``{spinor_dim: 16, spin8_generators: 28,
          branch: (8, 8), branch_labels: ("8_s", "8_c"), chirality_operator,
          off_block_max_residual (≈0), projector_commutator_max_residual (≈0),
          half_spinor_ranks: (28, 28), half_spinors_distinct_actions: True,
          half_spinor_action_difference (>0)}``.
        - ``attestation`` — the MPR v1 self-attestation (Class A content-address
          of the computed ``Γ`` + ``Σ`` structure).
    """
    cert = _branching_certificate()
    gammas = _gamma_int()
    s4 = _s4_int()
    attestation = _branching_attestation(
        gammas, s4,
        {
            "structure": "spin8_in_spin9_16_eq_8s_plus_8c",
            "spinor_dim": _DIM_SPINOR,
            "spin9_dim": _DIM_SO9,
            "spin8_generators": _DIM_SO8,
            "branch": [_DIM_HALF_SPINOR, _DIM_HALF_SPINOR],
        },
    )
    return {
        "spinor_rep": dict(cert["spinor_rep"]),
        "branching": dict(cert["branching"]),
        "attestation": attestation,
    }


# ──────────────────────────────────────────────────────────────────────
# The sedenion multiplication (Cayley-Dickson dim 16) — for the conjecture.
# ──────────────────────────────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def _sedenion_cocycle() -> Tuple[Tuple[Tuple[int, int], ...], ...]:
    """The sedenion basis cocycle ``e_i · e_j = SGN·e_IDX`` as a ``16x16`` grid
    of ``(index, sign)`` pairs, from :func:`srmech.amsc.cascade.cayley_dickson.cd_basis_product`
    — the SAME Cayley-Dickson convention as the octonion table (so the first
    ``O``-block of ``𝕊`` IS the octonions the ``Γ`` / ``g₂`` are built from)."""
    return tuple(
        tuple(_cd_basis_product(_SEDENION_DIM, i, j) for j in range(_SEDENION_DIM))
        for i in range(_SEDENION_DIM)
    )


def _sedenion_leibniz_terms(x: List[List[int]]) -> List[int]:
    """The integer sedenion-Leibniz residual of a ``16x16`` map ``X`` over all
    basis pairs ``(e_i, e_j)``: ``R_ij = X(e_i·e_j) − (X e_i)·e_j − e_i·(X e_j)``.

    ``X`` is a derivation of ``𝕊`` iff every component is 0. Flat list of length
    ``16·16·16``. Exact-integer (the cocycle signs are ``±1``, ``X`` integer)."""
    coc = _sedenion_cocycle()
    n = _SEDENION_DIM
    cols = [[x[r][c] for r in range(n)] for c in range(n)]   # column c = X·e_c
    res: List[int] = []
    for i in range(n):
        ci = cols[i]
        for j in range(n):
            idx, s = coc[i][j]
            t1 = [s * x[r][idx] for r in range(n)]            # X(e_i·e_j)
            t2 = [0] * n                                      # (X e_i)·e_j
            for a in range(n):
                va = ci[a]
                if va:
                    aidx, asgn = coc[a][j]
                    t2[aidx] += va * asgn
            t3 = [0] * n                                      # e_i·(X e_j)
            cj = cols[j]
            for b in range(n):
                wb = cj[b]
                if wb:
                    bidx, bsgn = coc[i][b]
                    t3[bidx] += wb * bsgn
            for k in range(n):
                res.append(t1[k] - t2[k] - t3[k])
    return res


def _g2_diag_int() -> List[List[List[int]]]:
    """The 14 ``g₂ = Der(O)`` derivations lifted DIAGONALLY to ``𝕊 = O ⊕ O``
    as ``diag(D, D)`` (``16x16`` integer). This is the ``Der(𝕊)`` action
    (Schafer 1954: ``Der(𝕊) = g₂``)."""
    z8 = _zeros(_DIM8, _DIM8)
    out: List[List[List[int]]] = []
    for m in g2_subalgebra():
        d = [[int(round(x)) for x in row] for row in m.tolist()]
        out.append(_block16(d, z8, z8, d))
    return out


@functools.lru_cache(maxsize=1)
def _intersection_dim() -> int:
    """``dim(spin(9) ∩ Der(𝕊))`` — the honest bound (cached).

    A general ``spin(9)`` element is ``Σ_p c_p Σ_{ab}`` (36 params); the
    sedenion-Leibniz condition on ``Δ₉ = 𝕊`` is a linear system in the ``c_p``.
    Its nullspace dimension (``36 − rank``) is the dimension of the ``spin(9)``
    directions that ARE sedenion derivations. Computed EXACTLY over ℚ via the
    distinct nonzero constraint rows (the ``4096`` rows collapse to ``60``
    distinct)."""
    s4 = _s4_int()
    gen_terms = [_sedenion_leibniz_terms(m) for m in s4]      # 36 vectors
    n_rows = len(gen_terms[0])
    seen = set()
    rowset: List[List[int]] = []
    for r in range(n_rows):
        row = tuple(gen_terms[c][r] for c in range(_DIM_SO9))
        if any(row) and row not in seen:
            seen.add(row)
            rowset.append(list(row))
    rank = _q_rank(rowset) if rowset else 0
    return _DIM_SO9 - rank


def _conjecture_attestation(extra: Dict[str, object]) -> Dict[str, object]:
    """MPR v1 self-attestation for the conjecture verdict (Class A
    content-address over the 36 spin(9) generators + 14 g₂-diagonals)."""
    response_sha256 = _sha256_bytes(_gen_bytes(_s4_int() + _g2_diag_int()))
    parser_rule_hash = _sha256_bytes(_CONJECTURE_RULE)
    descriptor_hash = _sha256_bytes(b"srmech/qm/so9.py::sedenion_holonomy_conjecture")
    return {
        "mpr_version": "1.0",
        "data": dict(extra),
        "data_schema_id": "srmech://schema/sedenion_holonomy_conjecture",
        "attestation": {
            "source_doi": None,
            "source_url": "https://arxiv.org/abs/math/0105155",
            "license": "CC0",
            "retrieved_at": _RETRIEVED_AT,
            "response_sha256": response_sha256,
            "parser_version": "srmech 0.9.0",
            "parser_rule_hash": parser_rule_hash,
            "collector_descriptor_path": "srmech/qm/so9.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        "rendering": {
            "name": "associator ↔ Spin(9)-holonomy conjecture (PARTIAL)",
            "purpose": (
                "Honest tiered test of whether the octonion associator "
                "curvature (g₂ = Der O) reappears as a Spin(9) holonomy at the "
                "sedenion rung; verdict PARTIAL (g₂ persists + embeds, but does "
                "NOT fill Spin(9): dim(spin(9) ∩ Der(𝕊)) = 14 ≪ 36)"
            ),
            "cite_as": (
                "Baez (2002) arXiv:math/0105155 (octonionic Spin(9)); Schafer "
                "(1954) Amer. J. Math. 76, 435-446 (Der(𝕊) = g₂). The tiered "
                "verdict is this op's own bit-exact computation."
            ),
        },
    }


def sedenion_holonomy_conjecture() -> dict:
    """HONEST tiered test: does the octonion associator curvature reappear as a
    ``Spin(9)`` holonomy at the sedenion (``𝕊``, dim 16) rung?

    THE CONJECTURE. The non-associativity of ``O`` is measured by the
    associator ``[a, b, c] = (ab)c − a(bc)``, whose infinitesimal symmetry
    algebra is ``g₂ = Der(O)`` (dim 14). The next Cayley-Dickson rung ``𝕊``
    (:mod:`srmech.amsc.cascade.cayley_dickson`) has real dimension 16 — the
    SAME as the ``Spin(9)`` spinor ``Δ₉`` (both are ``O ⊕ O``). Does the
    associator's ``g₂`` "curvature" show up at ``𝕊`` as a holonomy valued in
    ``Spin(9)``?

    THE HONEST BOUND (load-bearing): ``Spin(9) ≠ Aut(𝕊)``. ``Aut(𝕊) ≅ G₂ ⋊ S₃``
    (dim 14; ``G₂``-flavored) and ``Der(𝕊) = g₂`` (dim 14, Schafer 1954) —
    both FAR smaller than ``dim Spin(9) = 36``. So the strong "the associator
    fills a Spin(9) holonomy" reading is expected to FAIL. Per
    ``[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`` (FORM,
    not identity) and ``[[feedback_cross_substrate_transfers_the_algorithm_not_the_constant]]``,
    the verdict is tiered honestly — a NULL/PARTIAL counts.

    THE TIERED VERDICT — **PARTIAL** (each tier bit-exact, arithmetic shown):

    - **RECOGNIZED** (a carrier coincidence, NOT an identity): ``dim Δ₉ = 16 =
      dim_R 𝕊``. Both the Spin(9) spinor and the sedenions ARE ``O ⊕ O``; the
      shared 16-dim carrier is what makes the question askable. It is NOT
      evidence of a Spin(9) action by sedenion automorphisms.
    - **DERIVED** (bit-exact positive): ``Der(𝕊) = g₂`` (dim 14) — the
      associator's symmetry algebra PERSISTS to ``𝕊`` — AND it embeds in
      ``spin(9)`` as the triality-diagonal ``g₂``, acting on ``Δ₉ = 𝕊`` as
      ``diag(D, D)``: all 14 such lifts have sedenion-Leibniz residual EXACTLY
      0 (they are genuine sedenion derivations), and they lie in ``span(spin(9))``.
      Bit-exact: ``dim(spin(9) ∩ Der(𝕊)) = 14``.
    - **NULL** (bit-exact, the honest bound): the strong conjecture FAILS. Of
      the 36 ``spin(9)`` directions only a 14-dim subspace (the ``g₂`` above)
      preserves ``𝕊`` multiplication — the other 22 (the block-mixing
      ``Σ_{a,8}`` and the ``8_s ≠ 8_c`` half-spinor directions) have NONZERO
      sedenion-Leibniz residual; 0 of the 36 individual generators are
      derivations. So the associator's "holonomy" at ``𝕊`` is valued in ``g₂``
      (dim 14), NOT in ``Spin(9)`` (dim 36) — ``Spin(9) ⊋ Der(𝕊)``, confirming
      ``Spin(9) ≠ Aut(𝕊)`` constructively. Nothing NEW appears at the ``𝕊``
      rung: the symmetry is the same ``G₂ = Aut(O)`` it already was.

    So the associator curvature does NOT reappear as a *Spin(9)* holonomy; it
    reappears as the SAME ``g₂ ⊂ Spin(9)`` holonomy it already was on ``O``.
    The dimension coincidence ``16 = 16`` is a shared carrier, not a shared
    symmetry. (References: the shipped ``O``-side no-frame-free-invariant
    result and :mod:`srmech.amsc.cascade.cayley_dickson`'s ``𝕆``-reversible /
    ``𝕊``-not tower + :func:`~srmech.amsc.cascade.cayley_dickson.sedenion_zero_divisor_witness`.)

    Class D (the derivation-residual detection + the intersection) ∘ Class L
    (the exact-ℚ rank / nullspace) ∘ Class K (the residual magnitude; never
    ``abs()``).

    Canonical SSoT: Baez (2002) arXiv:math/0105155 (octonionic ``Spin(9)``);
    Schafer (1954) Amer. J. Math. 76, 435-446 (``Der(𝔸_n) = g₂``, ``n ≥ 3``).
    The tiered verdict is this op's own bit-exact self-attesting computation.

    Returns:
        A ``dict`` with keys:

        - ``verdict`` — ``"PARTIAL"``.
        - ``dimensions`` — ``{spinor_delta9: 16, sedenion_real: 16,
          spin9: 36, g2: 14, der_sedenion: 14, spin9_cap_der_sedenion: 14,
          aut_sedenion_approx: 14}``.
        - ``certificate`` — the bit-exact facts:
          ``{g2_diag_all_derivations: True, n_g2_diag: 14,
          g2_diag_max_leibniz_residual (≈0), block_mixer_is_derivation: False,
          block_mixer_leibniz_residual (>0), n_individual_spin9_derivations: 0,
          spin9_cap_der_sedenion_dim: 14, g2_diag_in_spin9_span: True,
          spin9_gg_dim: 36}``.
        - ``tiers`` — the ``{RECOGNIZED, DERIVED, NULL}`` one-line readings.
        - ``framework_reading`` — the substrate-blind FORM-not-identity label
          (tagged "framework-reading, not derived").
        - ``attestation`` — the MPR v1 self-attestation (Class A content-address).
    """
    g2_diag = _g2_diag_int()
    # DERIVED: every diag(D, D) is a sedenion derivation (residual exactly 0).
    g2_worst = 0.0
    for x in g2_diag:
        g2_worst = max(g2_worst, _vec_norm_scalar(_sedenion_leibniz_terms(x)))
    all_g2_derivations = g2_worst < _TOL

    # NULL: a block-mixing spin(9) generator Σ_{0,8} is NOT a derivation.
    s4 = _s4_int()
    index = {p: i for i, p in enumerate(_so9_index_pairs())}
    block_mixer = s4[index[(0, _CHIRAL_INDEX)]]
    mixer_residual = _vec_norm_scalar(_sedenion_leibniz_terms(block_mixer))
    n_individual = sum(
        1 for m in s4 if _vec_norm_scalar(_sedenion_leibniz_terms(m)) < _TOL
    )

    # the honest bound: dim(spin(9) ∩ Der(𝕊)) = 14 (≪ 36).
    cap_dim = _intersection_dim()

    # g2_diag ⊆ span(spin(9)) and dim spin(9) = 36.
    spin_span = [_flatten(m) for m in s4]
    r0 = _q_rank(spin_span)
    r1 = _q_rank(spin_span + [_flatten(x) for x in g2_diag])
    g2_in_span = (r0 == r1)

    assert all_g2_derivations, "some diag(D,D) is not a sedenion derivation"
    assert mixer_residual > _TOL, "block-mixer Σ_{0,8} wrongly reads as a derivation"
    assert cap_dim == _DIM_DER_SEDENION, (
        f"dim(spin(9) ∩ Der(𝕊)) expected 14; got {cap_dim}"
    )
    assert r0 == _DIM_SO9 and g2_in_span, "g₂-diag not inside span(spin(9))"

    dimensions = {
        "spinor_delta9": _DIM_SPINOR,
        "sedenion_real": _SEDENION_DIM,
        "spin9": _DIM_SO9,
        "g2": _DIM_G2,
        "der_sedenion": _DIM_DER_SEDENION,
        "spin9_cap_der_sedenion": cap_dim,
        "aut_sedenion_approx": _DIM_G2,   # Aut(𝕊) ≅ G₂ ⋊ S₃ (dim 14; S₃ discrete)
    }
    certificate = {
        "g2_diag_all_derivations": all_g2_derivations,
        "n_g2_diag": len(g2_diag),
        "g2_diag_max_leibniz_residual": g2_worst,
        "block_mixer_is_derivation": mixer_residual < _TOL,
        "block_mixer_leibniz_residual": mixer_residual,
        "n_individual_spin9_derivations": n_individual,
        "spin9_cap_der_sedenion_dim": cap_dim,
        "g2_diag_in_spin9_span": g2_in_span,
        "spin9_gg_dim": r0,
    }
    tiers = {
        "RECOGNIZED": (
            "dim Δ₉ = 16 = dim_R 𝕊 (both are O ⊕ O) — a shared carrier, "
            "NOT a Spin(9) action by sedenion automorphisms"
        ),
        "DERIVED": (
            "Der(𝕊) = g₂ (dim 14) persists to 𝕊 and embeds in spin(9) as the "
            "triality-diagonal diag(D, D); all 14 lifts are exact sedenion "
            "derivations; dim(spin(9) ∩ Der(𝕊)) = 14 (bit-exact)"
        ),
        "NULL": (
            "the strong conjecture fails: only 14 of the 36 spin(9) directions "
            "preserve 𝕊 multiplication (the other 22 have nonzero Leibniz "
            "residual; 0/36 individual generators are derivations) — the "
            "associator holonomy is valued in g₂, NOT Spin(9); Spin(9) ≠ Aut(𝕊)"
        ),
    }
    attestation = _conjecture_attestation({
        "verdict": "PARTIAL",
        "dimensions": dimensions,
        "spin9_cap_der_sedenion": cap_dim,
    })
    return {
        "verdict": "PARTIAL",
        "dimensions": dimensions,
        "certificate": certificate,
        "tiers": tiers,
        "framework_reading": {
            "note": "framework-reading, not derived",
            "form_not_identity": (
                "the 16 = 16 carrier match is FORM (a shared O⊕O carrier), not "
                "IDENTITY (Spin(9) does not act by sedenion automorphisms); the "
                "cross-substrate match transfers the g₂ ALGORITHM, not a Spin(9) "
                "constant"
            ),
            "associator_symmetry_is_stable_at_g2": True,
            "spin9_is_not_aut_sedenion": True,
        },
        "attestation": attestation,
    }


__all__ = [
    "sedenion_holonomy_conjecture",
    "so9_adjoint_basis",
    "spin8_in_spin9_branching",
    "spin9_gamma_matrices",
    "spin9_spinor_generators",
]
