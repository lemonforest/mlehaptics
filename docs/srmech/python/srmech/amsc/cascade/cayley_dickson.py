"""Cayley–Dickson construction — the **open-exterior boundary-demonstrator**
(#915 / MFO §VII.6.23; the far side of the Hurwitz wall).

``the_one`` (:mod:`srmech.amsc.cascade.one`) and ``hypercomplex_couple``
(:mod:`srmech.amsc.cascade.hypercomplex_dft`) live entirely in the **reversible
interior** ℝ/ℂ/ℍ/𝕆 (dims 1, 2, 4, 8) — the normed division algebras, where
``multiply by x`` is a bijection you can run forward *and* backward. That ceiling
is not an omission; it **is** the physics claim (Hurwitz 1898: 1, 2, 4, 8 are the
only normed division algebras; the 11D = 1+3+7 ladder is its imaginary part).

This module is the deliberately **non-reversible** object on the *other* side of
that wall: the generic Cayley–Dickson doubling ℝ → ℂ → ℍ → 𝕆 → 𝕊(sedenion,16)
→ trigintaduonion(32) → … . It exists to convert MFO §VII.6.23's open-exterior
claims from *literature-only* (Moreno arXiv:q-alg/9710013) to **own-code-attested**
(`[[feedback_own_work_is_primary_attestation]]`): the section's falsifier, made
re-runnable.

**It is NOT a substrate extension.** The closed simulation stays at ≤𝕆 by design
(`[[user_stance_two_substrate_native_math_languages_11d_quantum_and_cyclic_algebra]]`).
Past 𝕆 there is no division-algebra substrate to be native *to* — so there is no
``qm.*`` peer, no DSL wiring, no claim of substrate-nativeness. This is the wall
the sim does not cross, exhibited so the wall is provable in our own code.

What it attests (each a bit-exact, exact-rational witness):

* **Zero divisors first appear at dim 16 and never heal.** :func:`sedenion_zero_divisor_witness`
  exhibits a concrete pair ``x, y`` (both nonzero) with ``x·y = 0`` — found from
  *our own* multiplication table, not transcribed from a paper. Division algebras
  (dims 1, 2, 4, 8) provably have none.
* **The norm stops being multiplicative at 16.** A zero-divisor pair has
  ``N(x·y) = N(0) = 0`` while ``N(x)·N(y) ≠ 0`` (composition holds for 𝕆, fails
  on 𝕆 → 𝕊; §VII.6.23 claim C3).
* **Chirality persists; its reversing power does not.** :func:`cd_conjugate` and
  ``x·x̄ = N(x)·1`` are defined at *every* rung (the conjugation never dies), yet
  for a zero divisor the *product* has no inverse (§VII.6.23.3).
* **"No backward direction to point."** :func:`left_mult_kernel` builds the linear
  map ``u ↦ x·u`` and returns its kernel: nonempty ⟺ ``x`` is a left zero divisor
  ⟺ multiply-by-``x`` is non-injective ⟺ **no inverse map exists**. This is the
  associativity-free statement of §VII.6.23.4 ("anything past and unobserved is
  lost") — exact-rational, no float, no ``abs()``.

**Exact-rational, numpy-free.** Every component is a :class:`fractions.Fraction`;
the construction needs only ``+``, ``−``, ``×`` and the Class-K sign-flip (never
``abs()`` — sign is the Class-K pin-slot per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``). The integer
**structural core** — the basis-unit cocycle ``e_i·e_j = ±e_{i⊕j}`` — is
:func:`cd_basis_product`, attested bit-exact against the JPL-clean C peer
``srmech_cd_basis_product`` by ``tests/test_cascade_cayley_dickson_parity.py``
(the Rosetta pair; the arbitrary-rational product stays Python by the same
vendoring-scope decision that keeps TOML parsing in Python — there is no bignum
rational in libsrmech).

**No new primitive class** — a composition of A–N: the doubling product is
**Class M** (the bilinear bind) ∘ **Class C** (the conjugation-ordered cross
terms) ∘ **Class K** (the sign-flip in conjugation); the norm is a sum-reduce of
squares (**Class N** rational anchor); the zero-divisor search is **Class D**
(pattern-detect) over **Class A** (the attested CD basis convention); the kernel
is **Class L** (linear-algebra rank). Scoped to the open exterior — past the
1+3+7+3 = 14 substrate, not part of it.

Canonical SSoT:
- Hurwitz (1898), *Über die Composition der quadratischen Formen* — 1, 2, 4, 8 are
  the only normed division algebras.
- Schafer, R.D. (1954), *On the algebras formed by the Cayley–Dickson process*,
  *Amer. J. Math.* 76:435–446 — flexibility + conjugation survive every rung.
- Moreno, G. (1998), *The zero divisors of the Cayley–Dickson algebras over the
  reals*, arXiv:q-alg/9710013 — the structure of sedenion zero divisors.
- Baez, J.C. (2002), *The Octonions*, Bull. Amer. Math. Soc. 39:145–205
  (arXiv:math/0105155) §2 — the Cayley–Dickson doubling convention.
- ``[[user_stance_two_substrate_native_math_languages_11d_quantum_and_cyclic_algebra]]``
- ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``
- ``[[feedback_own_work_is_primary_attestation]]``
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from typing import Any, Dict, List, Sequence, Set, Tuple

#: Hard ceiling on the algebra dimension (the demonstrator is not unbounded; the
#: C peer shares this bound). 64 = the 6th doubling — enough to show the open
#: exterior persists well past dim 16. dim must be a power of two ``≤`` this.
CD_MAX_DIM = 64

#: The normed **division** algebras (Hurwitz 1898) — the reversible interior.
DIVISION_ALGEBRA_DIMS: Tuple[int, int, int, int] = (1, 2, 4, 8)

#: The Cayley–Dickson ladder up to the demonstrator ceiling.
CD_DIMS: Tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64)

#: Human names of the rungs (the exterior names ≥ 32 are non-standard; C7).
ALGEBRA_NAMES: Dict[int, str] = {
    1: "R (real)",
    2: "C (complex)",
    4: "H (quaternion)",
    8: "O (octonion)",
    16: "S (sedenion)",
    32: "trigintaduonion",
    64: "(64-ion)",
}


# ──────────────────────────────────────────────────────────────────────
# Element coercion (exact rational; numpy-free).
# ──────────────────────────────────────────────────────────────────────

def _is_pow2(n: int) -> bool:
    return n >= 1 and (n & (n - 1)) == 0


def _as_elem(seq: Sequence[Any]) -> Tuple[Fraction, ...]:
    """Coerce a sequence to a power-of-two-length tuple of exact Fractions."""
    el = tuple(x if type(x) is Fraction else Fraction(x) for x in seq)
    n = len(el)
    if not _is_pow2(n):
        raise ValueError(
            f"a Cayley–Dickson element has power-of-two dimension "
            f"(1, 2, 4, 8, 16, …); got length {n}"
        )
    if n > CD_MAX_DIM:
        raise ValueError(f"dimension {n} exceeds CD_MAX_DIM={CD_MAX_DIM}")
    return el


# ──────────────────────────────────────────────────────────────────────
# Core algebra — recursive Cayley–Dickson doubling (operates on raw tuples).
# Convention (Wikipedia / Baez §2):  (a,b)(c,d) = (a c − d* b,  d a + b c*)
# and conjugation  (a,b)* = (a*, −b),  base case  conj(real) = real.
# ──────────────────────────────────────────────────────────────────────

def _conj(a: Tuple[Fraction, ...]) -> Tuple[Fraction, ...]:
    n = len(a)
    if n == 1:
        return a
    m = n >> 1
    return _conj(a[:m]) + tuple(-x for x in a[m:])   # Class K sign-flip; no abs()


def _mult(a: Tuple[Fraction, ...], b: Tuple[Fraction, ...]) -> Tuple[Fraction, ...]:
    n = len(a)
    if n == 1:
        return (a[0] * b[0],)
    m = n >> 1
    a1, a2 = a[:m], a[m:]
    b1, b2 = b[:m], b[m:]
    # (a1 b1 − b2* a2 , b2 a1 + a2 b1*)
    left = tuple(p - q for p, q in zip(_mult(a1, b1), _mult(_conj(b2), a2)))
    right = tuple(p + q for p, q in zip(_mult(b2, a1), _mult(a2, _conj(b1))))
    return left + right


def cd_conjugate(a: Sequence[Any]) -> Tuple[Fraction, ...]:
    """Cayley–Dickson conjugation — negate the imaginary part (Class K).

    Defined at **every** rung (the chirality persists, §VII.6.23.3); ``x·x̄`` is
    always the real scalar ``N(x)·1``, even where the product loses its inverse.
    """
    return _conj(_as_elem(a))


def cd_mult(a: Sequence[Any], b: Sequence[Any]) -> Tuple[Fraction, ...]:
    """Exact-rational Cayley–Dickson product of two equal-dimension elements."""
    a = _as_elem(a)
    b = _as_elem(b)
    if len(a) != len(b):
        raise ValueError(
            f"cd_mult: operands must share dimension; got {len(a)} and {len(b)}"
        )
    return _mult(a, b)


def cd_add(a: Sequence[Any], b: Sequence[Any]) -> Tuple[Fraction, ...]:
    """Component-wise sum of two equal-dimension elements."""
    a = _as_elem(a)
    b = _as_elem(b)
    if len(a) != len(b):
        raise ValueError(f"cd_add: dimension mismatch {len(a)} vs {len(b)}")
    return tuple(p + q for p, q in zip(a, b))


def cd_norm_sq(a: Sequence[Any]) -> Fraction:
    """The squared norm ``N(x) = Σ x_i²`` (exact rational; ``x·x̄ = N(x)·1``).

    Positive-definite at every rung: ``N(x) = 0`` iff ``x = 0``. The composition
    identity ``N(x·y) = N(x)·N(y)`` holds for dims ≤ 8 and **fails** at 16.
    """
    a = _as_elem(a)
    s = Fraction(0)
    for x in a:
        s += x * x
    return s


def cd_basis(dim: int, i: int) -> Tuple[Fraction, ...]:
    """The ``i``-th unit basis element ``e_i`` of the dim-``D`` algebra."""
    if not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(f"dim must be a power of two ≤ {CD_MAX_DIM}; got {dim}")
    if not (0 <= i < dim):
        raise ValueError(f"basis index {i} out of range [0, {dim})")
    e = [Fraction(0)] * dim
    e[i] = Fraction(1)
    return tuple(e)


def is_division_algebra_dim(dim: int) -> bool:
    """``True`` iff the dim-``D`` algebra is a normed division algebra (Hurwitz):
    the reversible interior is exactly dims 1, 2, 4, 8."""
    return dim in DIVISION_ALGEBRA_DIMS


# ──────────────────────────────────────────────────────────────────────
# Integer structural core — the basis-unit cocycle e_i·e_j = sign·e_{i⊕j}.
# This is the Fano/structure content; the JPL-clean C peer computes the
# identical (index, sign) by the same iterative doubling (no recursion).
# ──────────────────────────────────────────────────────────────────────

def cd_basis_product(dim: int, i: int, j: int) -> Tuple[int, int]:
    """Product of two unit basis elements: ``e_i · e_j = sign · e_index``.

    Returns ``(index, sign)`` with ``index`` in ``[0, dim)`` and ``sign`` in
    ``{+1, -1}`` — the integer cocycle of the Cayley–Dickson algebra (the result
    index is always ``i ⊕ j``; the sign carries the Fano/orientation structure).
    Integer-only; the C peer ``srmech_cd_basis_product`` returns the identical
    pair (the Rosetta-attested structural core).
    """
    if not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(f"dim must be a power of two ≤ {CD_MAX_DIM}; got {dim}")
    if not (0 <= i < dim and 0 <= j < dim):
        raise ValueError(f"basis indices {i}, {j} out of range [0, {dim})")
    sign = 1
    index = 0
    p, q = i, j
    cur = dim
    # One recursive doubling-step per level; unrolled to a loop (the C peer is
    # loop-only for JPL Rule 1 / no recursion). At most log2(CD_MAX_DIM) levels.
    while cur > 1:
        m = cur >> 1
        ph = 1 if p >= m else 0
        qh = 1 if q >= m else 0
        pl = p - m if ph else p
        ql = q - m if qh else q
        if ph == 0 and qh == 0:                 # (a1 b1) in first half
            top, p, q = 0, pl, ql
        elif ph == 0 and qh == 1:               # (b2 a1) in second half — swap
            top, p, q = 1, ql, pl
        elif ph == 1 and qh == 0:               # (a2 b1*) in second half
            top, p, q = 1, pl, ql
            if ql != 0:                         # conj(b1) sign-flip (Class K)
                sign = -sign
        else:                                   # (− b2* a2) in first half — swap
            top, p, q = 0, ql, pl
            if ql == 0:                         # −conj(b2) → flip only when ql==0
                sign = -sign
        if top:
            index += m
        cur = m
    return index, sign


# ──────────────────────────────────────────────────────────────────────
# Loop navigation — the combinatorial layer over the basis cocycle.
#
# (W15 / RBS-LM bugfix wishlist; the loop analogues of the cyclic-group
# orbit machinery, built ENTIRELY on :func:`cd_basis_product` — no new
# multiplication code.) A "loop element" is a SIGNED basis unit
# ``(sign, index)`` with ``sign ∈ {+1, -1}`` and ``index ∈ [0, dim)`` —
# the ``2·dim`` elements of the Moufang loop ±e_0 … ±e_{D-1}. These are the
# named home the loop-shelf arc (F541/F544/F546) re-derived each time:
# the sub-loop a generator set spans, a single left-multiplication cycle,
# and the loop's minimum generating cardinality.
# ──────────────────────────────────────────────────────────────────────

def _loop_mult(dim: int,
               a: Tuple[int, int],
               b: Tuple[int, int]) -> Tuple[int, int]:
    """Product of two signed basis units ``(s_a, i)·(s_b, j)`` → ``(sign, index)``,
    via the :func:`cd_basis_product` cocycle (note its return order is
    ``(index, sign)``)."""
    index, sign = cd_basis_product(dim, a[1], b[1])
    return (a[0] * b[0] * sign, index)


def left_orbit(dim: int,
               start_idx: int,
               gen_idx: int) -> List[Tuple[int, int]]:
    """The left-multiplication orbit of ``e_{start_idx}`` under repeated left
    multiplication by ``e_{gen_idx}``: ``[e_s, e_g·e_s, e_g·(e_g·e_s), …]``,
    in cycle order, until it returns to a signed unit already visited.

    Returns a list of signed basis units ``(sign, index)`` (the cycle; the
    closing repeat is NOT included). For a nonzero generator ``e_g·e_g = -e_0``
    so left-mult-by-``e_g`` has order 4 — e.g. ``left_orbit(8, 1, 1)`` →
    ``[(1, 1), (-1, 0), (-1, 1), (1, 0)]`` (length 4).
    """
    if not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(f"dim must be a power of two ≤ {CD_MAX_DIM}; got {dim}")
    if not (0 <= start_idx < dim and 0 <= gen_idx < dim):
        raise ValueError(
            f"indices {start_idx}, {gen_idx} out of range [0, {dim})")
    gen = (1, gen_idx)
    cur: Tuple[int, int] = (1, start_idx)
    orbit: List[Tuple[int, int]] = []
    seen: Set[Tuple[int, int]] = set()
    while cur not in seen:
        seen.add(cur)
        orbit.append(cur)
        cur = _loop_mult(dim, gen, cur)
    return orbit


def closure(dim: int,
            generator_idxs: Sequence[int]) -> Set[Tuple[int, int]]:
    """The sub-loop generated by ``{e_g : g in generator_idxs}`` under
    Cayley–Dickson multiplication: a fixpoint over signed basis units,
    seeded with the identity ``(+1, 0)`` and each generator ``(+1, g)``,
    closed under all pairwise products until no new unit appears.

    Returns the set of signed basis units ``(sign, index)`` spanned — its
    cardinality is the order of the sub-loop. A single octonion generator
    spans 4 (``{±e_0, ±e_g}``); all 7 imaginary units span the full loop 16.
    """
    if not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(f"dim must be a power of two ≤ {CD_MAX_DIM}; got {dim}")
    for g in generator_idxs:
        if not (0 <= g < dim):
            raise ValueError(f"generator index {g} out of range [0, {dim})")
    elems: Set[Tuple[int, int]] = {(1, 0)}
    elems.update((1, g) for g in generator_idxs)
    changed = True
    while changed:
        changed = False
        for a in list(elems):
            for b in list(elems):
                prod = _loop_mult(dim, a, b)
                if prod not in elems:
                    elems.add(prod)
                    changed = True
    return elems


def min_generating_set(dim: int,
                       unit_idxs: Sequence[int]) -> int:
    """The smallest ``k`` such that some ``k``-subset of ``{e_u : u in
    unit_idxs}`` has a :func:`closure` equal to the FULL loop (all ``2·dim``
    signed basis units) — the loop's navigation dimensionality.

    Returns that minimum ``k``. For the octonions (``dim=8``, the 7 imaginary
    units ``[1..7]``) this is 3; for the quaternions (``dim=4``, units
    ``[1, 2, 3]``) it is 2. Raises ``ValueError`` if NO subset of
    ``unit_idxs`` spans the full loop.
    """
    if not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(f"dim must be a power of two ≤ {CD_MAX_DIM}; got {dim}")
    units = list(dict.fromkeys(unit_idxs))           # de-dup, preserve order
    for u in units:
        if not (0 <= u < dim):
            raise ValueError(f"unit index {u} out of range [0, {dim})")
    full = 2 * dim
    for k in range(1, len(units) + 1):
        for subset in combinations(units, k):
            if len(closure(dim, subset)) == full:
                return k
    raise ValueError(
        f"no subset of {units} generates the full loop of {full} signed "
        f"units in dim {dim}"
    )


# ──────────────────────────────────────────────────────────────────────
# Demonstrators — the §VII.6.23 open-exterior falsifiers, in our own code.
# ──────────────────────────────────────────────────────────────────────

def _basis_sum_terms_zero(dim: int, terms_x, terms_y) -> Tuple[bool, List[int]]:
    """Is ``(Σ s·e_a)·(Σ t·e_b)`` the zero element? Integer accumulation via the
    cocycle (fast path for the witness search)."""
    acc = [0] * dim
    for a, sa in terms_x:
        for b, sb in terms_y:
            idx, sign = cd_basis_product(dim, a, b)
            acc[idx] += sa * sb * sign
    return all(v == 0 for v in acc), acc


def _terms_to_elem(dim: int, terms) -> Tuple[Fraction, ...]:
    e = [Fraction(0)] * dim
    for a, s in terms:
        e[a] += Fraction(s)
    return tuple(e)


def sedenion_zero_divisor_witness() -> Dict[str, Any]:
    """Exhibit a concrete sedenion (dim 16) zero divisor: ``x, y`` both nonzero
    with ``x·y = 0``. Found by searching basis-unit pairs with **our own**
    multiplication table (own-work-first, not a literature transcription).

    Returns a dict with the two elements (as Fraction tuples), their human
    ``e_i ± e_j`` forms, their (nonzero) squared norms, and the (all-zero)
    product — the executable form of "zero divisors first appear at 16."
    """
    dim = 16
    units = range(1, dim)                       # imaginary units e_1 … e_15
    for i in units:
        for j in range(i + 1, dim):
            terms_x = [(i, 1), (j, 1)]
            for k in units:
                for l in range(k + 1, dim):
                    for s in (1, -1):
                        terms_y = [(k, 1), (l, s)]
                        is_zero, prod = _basis_sum_terms_zero(dim, terms_x, terms_y)
                        if is_zero:
                            x = _terms_to_elem(dim, terms_x)
                            y = _terms_to_elem(dim, terms_y)
                            return {
                                "dim": dim,
                                "x": x,
                                "y": y,
                                "x_form": f"e{i} + e{j}",
                                "y_form": f"e{k} {'+' if s > 0 else '-'} e{l}",
                                "x_norm_sq": cd_norm_sq(x),
                                "y_norm_sq": cd_norm_sq(y),
                                "product": tuple(Fraction(v) for v in prod),
                                "product_is_zero": True,
                            }
    raise RuntimeError(                         # unreachable: 𝕊 has zero divisors
        "no basis-pair zero divisor found in the sedenions — the convention is "
        "inconsistent with Cayley–Dickson (this should be impossible)"
    )


def left_mult_matrix(x: Sequence[Any]) -> List[List[Fraction]]:
    """The ``n×n`` rational matrix of the linear map ``u ↦ x·u`` (column ``c`` is
    ``x·e_c``), row-major."""
    x = _as_elem(x)
    n = len(x)
    cols = [_mult(x, cd_basis(n, c)) for c in range(n)]
    return [[cols[c][r] for c in range(n)] for r in range(n)]


def _rational_nullspace(matrix: List[List[Fraction]]) -> List[Tuple[Fraction, ...]]:
    """Exact-rational kernel basis of a square matrix via reduced row echelon."""
    n = len(matrix)
    a = [row[:] for row in matrix]
    pivot_cols: List[int] = []
    r = 0
    for c in range(n):
        piv = None
        for rr in range(r, n):
            if a[rr][c] != 0:
                piv = rr
                break
        if piv is None:
            continue
        a[r], a[piv] = a[piv], a[r]
        inv = a[r][c]
        a[r] = [v / inv for v in a[r]]
        for rr in range(n):
            if rr != r and a[rr][c] != 0:
                f = a[rr][c]
                a[rr] = [u - f * w for u, w in zip(a[rr], a[r])]
        pivot_cols.append(c)
        r += 1
        if r == n:
            break
    free_cols = [c for c in range(n) if c not in pivot_cols]
    basis: List[Tuple[Fraction, ...]] = []
    for fc in free_cols:
        vec = [Fraction(0)] * n
        vec[fc] = Fraction(1)
        for i, pc in enumerate(pivot_cols):
            vec[pc] = -a[i][fc]
        basis.append(tuple(vec))
    return basis


def left_mult_kernel(x: Sequence[Any]) -> List[Tuple[Fraction, ...]]:
    """Kernel basis of ``u ↦ x·u``. **Nonempty ⟺ ``x`` is a left zero divisor ⟺
    multiply-by-``x`` has no inverse map** — the "no backward direction to point"
    of §VII.6.23.4. Empty for every nonzero element of a division algebra (≤𝕆)."""
    return _rational_nullspace(left_mult_matrix(x))


def left_mult_is_invertible(x: Sequence[Any]) -> bool:
    """``True`` iff ``u ↦ x·u`` is a bijection (a backward direction exists).

    Always ``True`` for nonzero ``x`` at dims ≤ 8; ``False`` for a zero divisor
    at dim ≥ 16 — the reversibility that ends at the Hurwitz wall.
    """
    return len(left_mult_kernel(x)) == 0
