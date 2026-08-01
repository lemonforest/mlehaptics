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

**Exact-rational, numpy-free.** Every component is a :class:`srmech.amsc.q.Q`
(#845: srmech's C-native exact-rational carrier, not stdlib ``fractions``);
the construction needs only ``+``, ``−``, ``×`` and the Class-K sign-flip (never
``abs()`` — sign is the Class-K pin-slot per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``). The integer
**structural core** — the basis-unit cocycle ``e_i·e_j = ±e_{i⊕j}`` — is
:func:`cd_basis_product`, attested bit-exact against the JPL-clean C peer
``srmech_cd_basis_product`` by ``tests/test_cascade_cayley_dickson_parity.py``
(the Rosetta pair). The exact-ℚ VECTOR ops :func:`cd_basis` / :func:`cd_conjugate`
/ :func:`cd_add` / :func:`cd_norm_sq` also dispatch to JPL-clean C peers
(``srmech_cd_q{basis,conjugate,add,norm_sq}`` — the ``srmech_cd_qvec`` exact-ℚ
vector carrier, the 1-D sibling of ``srmech_qmat`` over the caller-arena
``srmech_bigint``; rc159/Qalg Batch 3), byte-identical reduced ``(num, den)`` at
any magnitude — so a bare-C host CONSTRUCTS + HOLDS + MANIPULATES a CD ℚ-vector
with no Python (there IS a bignum rational in libsrmech now). The arbitrary-
rational PRODUCT :func:`cd_mult` (the recursive doubling) is the remaining
Python-only rung (its C peer is the next Qalg batch); the pure-Python bodies stay
the Pyodide / no-native fallback + the byte-identical parity oracle throughout.

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

import ctypes
from itertools import combinations
from typing import Any, Dict, List, Sequence, Set, Tuple

from srmech.amsc.cascade.atoms import (      # Class-K pin-slot / Class-C reorient
    pin_slot_at_zero as _pin_slot_at_zero,
    reorient as _reorient,
)
from srmech.math.cyclic import gcd as _gcd   # Class-I gcd (native); NOT stdlib math
from srmech.amsc.q import Q, to_q            # #845: the CD element carrier is Q

from srmech.amsc import _native  # rc10: native srmech_cd_basis_product dispatch

#: Hard ceiling on the algebra dimension (the C peer shares this bound —
#: ``SRMECH_CD_MAX_DIM``). dim must be a power of two ``≤`` this.
#:
#: rc298 (`#933`): **64 → 256**, four doublings past the Hurwitz wall. The old
#: 64 was a TOOLING bound, not a mathematical one — PR #687 named it as the
#: thing stopping the rung sweep. Every scratch buffer on the addressing path
#: (both projections) is LINEAR in this cap; the single quadratic buffer in the
#: library is on the *dense* path and keeps its own smaller ceiling
#: (:data:`CD_DENSE_MAX_DIM`). The remaining limit above 256 is verification
#: time — proving a rung costs ``O(dim²)`` basis products — not memory.
CD_MAX_DIM = 256

#: Ceiling on the **dense** ``dim × dim`` native path — the modular-rank gate
#: ``srmech_sedenion_is_navigable`` (``SRMECH_CD_DENSE_MAX_DIM``). Its matrix is
#: the one quadratic buffer in the C library: 32 KB at 64, but 2 MB at 512,
#: which overruns MSVC's 1 MB default thread stack. Decoupled from
#: :data:`CD_MAX_DIM` so raising the addressing cap costs nothing here.
#:
#: This is a **performance** boundary, not a capability one:
#: :func:`left_mult_is_invertible` past this dim routes to the exact-rational
#: nullspace oracle (the same fallback it already used beyond int64 magnitude)
#: and stays correct at every dim ``≤`` :data:`CD_MAX_DIM` — just slower.
CD_DENSE_MAX_DIM = 64

#: **ADDRESS ceiling — the honest one** (rc339, `#T967`): the highest rung at
#: which the index lane ``e_i·e_j = ±e_{i XOR j}`` has been EXHAUSTIVELY
#: verified. 0 failures / 4096 pairs at 64 (generating code:
#: ``docs/srmech/notes/carrier_capability_ontology_rc339.py``). Distinct from
#: :data:`CD_MAX_DIM` (what the build ADMITS, 256) and from
#: :data:`CD_DENSE_MAX_DIM` (which happens to share the value 64 for an
#: unrelated reason — MSVC's 1 MB stack against a quadratic buffer). Three
#: different facts; three names, so none of them can stand in for another.
CD_ADDRESS_VERIFIED_DIM = 64

#: The normed **division** algebras (Hurwitz 1898) — the reversible interior.
DIVISION_ALGEBRA_DIMS: Tuple[int, int, int, int] = (1, 2, 4, 8)

#: The **ASSOCIATIVE** rungs — the sub-ladder on which a TURN COMPOSES
#: (rc339, `#T967`). ``ℝ ↪ ℂ ↪ ℍ`` and no further: at dim 8 the octonions are
#: alternative but not associative, so ``L_x ∘ L_y == L_{x·y}`` stops holding
#: in general. Strictly inside :data:`DIVISION_ALGEBRA_DIMS` — a rung can be a
#: division algebra (dim 8) and still not compose its turns.
ASSOCIATIVE_ALGEBRA_DIMS: Tuple[int, int, int] = (1, 2, 4)

#: **COMPOSE ceiling** (rc339, `#T967`): the largest dim at which the product
#: has NO ZERO DIVISORS — a normed composition algebra. ``max
#: DIVISION_ALGEBRA_DIMS``; Hurwitz (1898) says 1, 2, 4, 8 and nothing else.
#: Past it (dim 16, 𝕊) there exist ``x ≠ 0``, ``y ≠ 0`` with ``x·y == 0``, which
#: is why :func:`left_mult_is_invertible` has something to answer at all.
#:
#: This is the SECOND of srmech's three carrier ceilings and it is NOT the
#: addressing one: :data:`CD_MAX_DIM` = 256 bounds ADDRESSING and says nothing
#: about composition. Reporting only the permissive ceiling is what rc339 came
#: to remove — see :func:`srmech.introspect.describe`.
CD_COMPOSE_MAX_DIM = 8

#: **TURN ceiling** (rc339, `#T967`): the largest dim at which NON-COMMUTING
#: turn composition survives **ON THE CAYLEY–DICKSON LADDER** —
#: ``max ASSOCIATIVE_ALGEBRA_DIMS`` = 4 (ℍ).
#:
#: **SCOPE (rc343, `#T972`) — this is a CD fact, not a universal one.** rc339
#: published this number in ``describe()["limits"]`` with no carrier attached,
#: and as a GLOBAL statement it is false: any ASSOCIATIVE carrier keeps folding
#: non-commuting turns at any dim. srmech's own :class:`~srmech.amsc.mat.Mat`
#: (product ``mat_matmul``) was MEASURED over the matrix units of ``M_n(ℝ)`` at
#: 81/81 turn-composing pairs for ``n=3`` (algebra dim 9), 42 of them
#: non-commuting, and 256/256 for ``n=4`` (dim 16), 108 non-commuting — both
#: above 4. The ceiling is therefore **PER-CARRIER**: each capability row in
#: :mod:`srmech.amsc.carrier_schema` publishes its own ``max_dim`` /
#: ``bounded_by``, and the ``limits`` row carries ``family`` =
#: ``"cayley_dickson"`` plus a derived ``exceeded_by``.
#:
#: **WHY it stops here, on this ladder — the index/sign split.** NOT
#: "associativity": turn composition IS associativity, so that reason restates
#: the definition and nothing could contradict it. The CD product FACTORS into
#: an XOR on the INDEX and a COCYCLE on the SIGN, measured over
#: :func:`cd_basis_product`::
#:
#:     dim | index == a XOR b | negative signs (C(d,2)) | SIGN COCYCLE assoc
#:       2 |       4/4        |        1  (1)           |     8/8      100%
#:       4 |      16/16       |        6  (6)           |    64/64     100%
#:       8 |      64/64       |       28  (28)          |   344/512     67%
#:      16 |     256/256      |      120  (120)         |  2248/4096    55%
#:      32 |    1024/1024     |      496  (496)         | 16808/32768   51%
#:
#: The index lane is exact at EVERY rung; the SIGN is what stops being
#: associative, abruptly, at dim 8. **Addressing is unbounded because XOR is
#: associative at every dim forever; turns and composition break because the
#: SIGN COCYCLE stops being associative.** That is why rc298 (`#T933`) could
#: lift :data:`CD_MAX_DIM` 64 → 256 by DECOUPLING the caps — the wall was never
#: in the addressing. (``index == XOR`` is close to DEFINITIONAL for a CD basis,
#: so that column is a CHECK, not a discovery; the READING it supports — a free
#: index and a load-bearing sign — is the part that is not definitional.)
#:
#: A "turn" composes iff left multiplication is a representation::
#:
#:     L_x ∘ L_y == L_{x·y}          i.e.   x·(y·z) == (x·y)·z  for all z
#:
#: MEASURED over the basis of every rung (generating code:
#: ``docs/srmech/notes/carrier_capability_ontology_rc339.py``; NDJSON beside
#: it)::
#:
#:     dim  1: 1/1     dim  2: 4/4     dim  4: 16/16
#:     dim  8: 22/64   dim 16: 46/256  dim 32: 94/1024
#:
#: The largest power-of-two SUB-rung all of whose turns compose is **4 at dim 8
#: AND at dim 16 AND at dim 32** — it saturates and never grows again.
#:
#: The precise statement about dim 8 is NOT "turns stop at ℍ". Turns **DEGRADE
#: TO ABELIAN-ONLY** at 𝕆: measured as SETS (not merely as counts), the
#: turn-composing basis pairs and the commuting basis pairs are THE SAME SET at
#: dim 8, 16 and 32 — both set differences empty. At dim 4 they are NOT: 16
#: pairs compose but only 10 commute, so 6 non-commuting pairs still compose.
#: What dies at the octonion rung is specifically **non-commuting turn
#: composition**. The 22 dim-8 survivors are exactly ``{anything paired with
#: e₀} ∪ {every element with itself}`` (power-associativity, which every rung
#: keeps), and 22 basis pairs × 4 sign combinations = the 88/256 measured on
#: the signed octonion loop — two independent routes, one number.
CD_TURN_MAX_DIM = 4

#: **MATERIALISATION ceiling** (rc352, `#T997`): the largest dim
#: :func:`algebra_table` will BUILD a table at. Strictly below
#: :data:`CD_MAX_DIM` (256) and below the elimination's own
#: ``SRMECH_ALGEBRA_INERTIA_MAX_DIM`` (also 256) because the object here is the
#: rank-3 tensor itself — ``dim³`` coefficients, so 262144 at 64 and 16.7 M at
#: 256. A FOURTH ceiling with a FOURTH name, for the same reason the other
#: three have their own: it bounds MATERIALISATION, not addressing
#: (:data:`CD_MAX_DIM`), not composition (:data:`CD_COMPOSE_MAX_DIM`), and not
#: turn-folding (:data:`CD_TURN_MAX_DIM`). The gamma cocycle underneath is
#: exact at every dim :func:`cd_basis_product` accepts; only the dense tensor
#: stops here.
ALGEBRA_TABLE_MAX_DIM = 64

#: The Cayley–Dickson ladder up to the demonstrator ceiling.
CD_DIMS: Tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64, 128, 256)

#: Human names of the rungs (the exterior names ≥ 32 are non-standard; C7).
ALGEBRA_NAMES: Dict[int, str] = {
    1: "R (real)",
    2: "C (complex)",
    4: "H (quaternion)",
    8: "O (octonion)",
    16: "S (sedenion)",
    32: "trigintaduonion",
    64: "(64-ion)",
    128: "(128-ion)",
    256: "(256-ion)",
}


# ──────────────────────────────────────────────────────────────────────
# Element coercion (exact rational; numpy-free).
# ──────────────────────────────────────────────────────────────────────

def _is_pow2(n: int) -> bool:
    return n >= 1 and (n & (n - 1)) == 0


def _coerce_frac(x: Any) -> Q:
    """Coerce one scalar to an exact :class:`~srmech.amsc.q.Q` — the CD element
    carrier (#845: srmech's C-native exact rational, not stdlib ``fractions``).
    A ``Q`` passes through unchanged; every other exact-rational scalar (``int`` /
    ``float`` / a stdlib ``fractions.Fraction`` / another ``as_integer_ratio``-able
    carrier / a ``(num, den)`` pair) rides :func:`srmech.amsc.q.to_q`, so the
    ``hypercomplex_exp`` Q-twiddle and a plain ``Fraction`` both feed straight into
    ``cd_mult``. (``float`` becomes its EXACT ratio via ``to_q`` → ``Q.from_float``
    — byte-identical to the old ``Fraction(float)``.)"""
    if type(x) is Q:
        return x
    return to_q(x)


def _as_elem(seq: Sequence[Any]) -> Tuple[Q, ...]:
    """Coerce a sequence to a power-of-two-length tuple of exact Qs."""
    el = tuple(_coerce_frac(x) for x in seq)
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

def _conj(a: Tuple[Q, ...]) -> Tuple[Q, ...]:
    n = len(a)
    if n == 1:
        return a
    m = n >> 1
    return _conj(a[:m]) + tuple(-x for x in a[m:])   # Class K sign-flip; no abs()


def _mult(a: Tuple[Q, ...], b: Tuple[Q, ...]) -> Tuple[Q, ...]:
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


def cd_conjugate(a: Sequence[Any]) -> Tuple[Q, ...]:
    """Cayley–Dickson conjugation — negate the imaginary part (Class K).

    Defined at **every** rung (the chirality persists, §VII.6.23.3); ``x·x̄`` is
    always the real scalar ``N(x)·1``, even where the product loses its inverse.
    """
    el = _as_elem(a)
    # rc159: the imaginary-half sign-flip dispatches to srmech_cd_qconjugate
    # (the exact-ℚ vector C peer). Byte-identical reduced (num, den) to the pure
    # _conj below, which stays the Pyodide / no-native fallback.
    native = _native.cd_qconjugate_c([(f.numerator, f.denominator) for f in el])
    if native is not None:
        return tuple(Q(n, d) for n, d in native)
    return _conj(el)


def cd_mult(a: Sequence[Any], b: Sequence[Any]) -> Tuple[Q, ...]:
    """Exact-rational Cayley–Dickson product of two equal-dimension elements."""
    a = _as_elem(a)
    b = _as_elem(b)
    if len(a) != len(b):
        raise ValueError(
            f"cd_mult: operands must share dimension; got {len(a)} and {len(b)}"
        )
    # rc160 (Qalg TAIL Batch 4): the arbitrary-rational CD product dispatches to
    # srmech_cd_mult — the C kernel that composes the srmech_cd_basis_product
    # cocycle with the qmat exact-ℚ arithmetic ((x·y)_{i⊕j} += x_i·y_j·sign). It
    # is the BILINEAR form of the recursive _mult below, so byte-identical reduced
    # (num, den) at any magnitude; _mult stays the Pyodide / no-native fallback.
    native = _native.cd_mult_c(
        [(f.numerator, f.denominator) for f in a],
        [(f.numerator, f.denominator) for f in b])
    if native is not None:
        return tuple(Q(n, d) for n, d in native)
    return _mult(a, b)


def cd_add(a: Sequence[Any], b: Sequence[Any]) -> Tuple[Q, ...]:
    """Component-wise sum of two equal-dimension elements."""
    a = _as_elem(a)
    b = _as_elem(b)
    if len(a) != len(b):
        raise ValueError(f"cd_add: dimension mismatch {len(a)} vs {len(b)}")
    # rc159: component-wise exact-ℚ addition dispatches to srmech_cd_qadd (the
    # exact-ℚ vector C peer). Byte-identical reduced (num, den) to the pure
    # Q sum below, which stays the Pyodide / no-native fallback.
    native = _native.cd_qadd_c(
        [(f.numerator, f.denominator) for f in a],
        [(f.numerator, f.denominator) for f in b])
    if native is not None:
        return tuple(Q(n, d) for n, d in native)
    return tuple(p + q for p, q in zip(a, b))


def cd_norm_sq(a: Sequence[Any], gammas: Any = None) -> Q:
    """The norm form ``N(x) = Re(x·x̄)`` of a Cayley–Dickson algebra
    (exact rational; ``x·x̄ = N(x)·1`` at every rung).

    **``gammas`` DECLARES WHICH ALGEBRA, and the declaration is load-bearing**
    (rc352, `#T1001`). ``None`` — the default — is the DEFINITE ladder
    ℝ → ℂ → ℍ → 𝕆 → 𝕊 …, on which ``N(x)`` collapses to the coordinate sum
    ``Σ x_i²``: positive-definite, ``N(x) = 0`` iff ``x = 0``. A supplied
    ``gammas`` (per-doubling ±1 in LADDER order — see :func:`algebra_table`)
    names a **generalised** twist, and on a SPLIT twist the coordinate sum is
    simply the wrong function.

    **The defect this parameter removes, MEASURED.** Before rc352 this op was
    ``Σ x_i²`` unconditionally while its docstring asserted positive-definiteness
    "at every rung". On split-ℂ it answers ``N([1, −1]) = 2`` for an element
    that is a **genuine null vector** — ``(1+j)(1−j) = 0``, so ``N`` must be 0
    — and it cannot see isotropy at all. That was dormant only because the
    module could not construct a split algebra; :func:`algebra_table` makes one
    reachable in the same rc, so the gate ships with it rather than after it.
    ``cd_norm_sq([1, -1])`` still returns ``2`` (the definite ℂ answer, and the
    right one for the algebra the default declares); ``cd_norm_sq([1, -1],
    gammas=(+1,))`` returns ``0``.

    **How the twisted read is computed — no table, no ``O(dim³)``.** The
    generalised product is monomial with index ``i⊕j``, so the real part of
    ``x·x̄`` picks up exactly the diagonal ``i == j`` terms::

        N(x) = Σ_i  x_i · x̄_i · sign_γ(i, i)

    with ``x̄`` the standard conjugation (``x̄_0 = x_0``, ``x̄_i = −x_i``) and
    ``sign_γ`` the γ-parameterised cocycle. That is ``O(dim)`` — the same cost
    as the coordinate form, and exact. Verified against the full
    :func:`table_product` read of ``Re(x·x̄)`` over every γ-twist at dims 1–32
    (1110/1110), and against the shipped coordinate path on the definite ladder
    at dims 1–32 (0 mismatches).

    Args:
        a: the element, ``dim`` exact-rational components.
        gammas: ``None`` for the definite ladder (the C-dispatched fast path,
            unchanged), or the per-doubling ±1 vector in LADDER order.

    Returns:
        The exact ``N(x)``. **On a split twist this can be negative or zero for
        a nonzero element** — that is the whole point; the form is indefinite
        there, and reading ``_sq`` as "non-negative" is the trap the parameter
        exists to remove.

    Note:
        The composition identity ``N(x·y) = N(x)·N(y)`` holds for dims ≤ 8 and
        **fails** at 16 on the definite ladder. ``gammas=None`` dispatches to
        ``srmech_cd_qnorm_sq`` exactly as before — bit-identical, no new
        arithmetic on the default path. Never ``abs()``: the conjugation is the
        Class-K sign-flip and the cocycle sign is the Class-K pin-slot.
    """
    a = _as_elem(a)
    if gammas is not None:
        g = _normalise_gammas(len(a), gammas)
        if any(v > 0 for v in g):
            # A SPLIT twist: the coordinate sum is the wrong function here, so
            # read the norm through the algebra's own cocycle instead. The
            # DEFINITE case falls through to the fast path below — proven
            # identical, not assumed (the γ = −1 diagonal is +1 at e₀ and −1
            # elsewhere, which is exactly Σ x_i² after the conjugation sign).
            s = Q(0)
            for i, x in enumerate(a):
                conj_i = x if i == 0 else -x       # Class-K sign-flip; no abs()
                _idx, sign = _gamma_basis_product(len(a), g, i, i)
                s += Q(sign) * x * conj_i
            return s
    # rc159: the sum-of-squares Σ x_i² dispatches to srmech_cd_qnorm_sq (the
    # exact-ℚ vector C peer). Byte-identical reduced (num, den) to the pure
    # Q accumulate below, which stays the Pyodide / no-native fallback.
    native = _native.cd_qnorm_sq_c([(f.numerator, f.denominator) for f in a])
    if native is not None:
        n, d = native
        return Q(n, d)
    s = Q(0)
    for x in a:
        s += x * x
    return s


def cd_basis(dim: int, i: int) -> Tuple[Q, ...]:
    """The ``i``-th unit basis element ``e_i`` of the dim-``D`` algebra."""
    if not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(f"dim must be a power of two ≤ {CD_MAX_DIM}; got {dim}")
    if not (0 <= i < dim):
        raise ValueError(f"basis index {i} out of range [0, {dim})")
    # rc159: the unit basis vector dispatches to srmech_cd_qbasis (the exact-ℚ
    # vector C peer). Byte-identical [(0,1), …, (1,1) at i, …] to the pure
    # construction below, which stays the Pyodide / no-native fallback.
    native = _native.cd_qbasis_c(dim, i)
    if native is not None:
        return tuple(Q(n, d) for n, d in native)
    e = [Q(0)] * dim
    e[i] = Q(1)
    return tuple(e)


def is_division_algebra_dim(dim: int) -> bool:
    """``True`` iff the dim-``D`` algebra is a normed division algebra (Hurwitz):
    the reversible interior is exactly dims 1, 2, 4, 8."""
    return dim in DIVISION_ALGEBRA_DIMS


# ──────────────────────────────────────────────────────────────────────
# The Hurwitz (Cayley–Dickson) conversion LADDER (rc116; #1248 / F1038):
# promote / project between adjacent rungs ℝ ↪ ℂ ↪ ℍ ↪ 𝕆 ↪ 𝕊 …, the algebra-
# one-level-up analog of the srmech.amsc.carrier_ladder variable ladder.
#
# PROMOTE is the SUBALGEBRA EMBEDDING — zero-pad the higher (imaginary-doubling)
# half, so ``x ↦ (x, 0)``; the element is unchanged, it merely gains higher
# components it does not use. This is exactly the embedding the qm.octonion /
# qm.quaternion restriction tests exercise (a quaternion q₄ sits in 𝕆 as
# ``q₄ ⊕ 0₄``, and octonion left/right-mult on it matches quaternion left/right-
# mult on the top-left 4×4 block — ℍ IS the top-4 of 𝕆 under this SAME
# cd_basis_product cocycle). PROJECT is its inverse — realify DOWN one doubling
# IFF the higher half vanishes, else a coherency error NAMING the genuinely-
# present higher component (never a silent truncation). ROUND-TRIP:
# ``cd_project(cd_promote(x, 2·dim)) == x`` EXACT at every rung.
# ──────────────────────────────────────────────────────────────────────

def cd_promote(x: Sequence[Any], dim: int) -> Tuple[Q, ...]:
    """Promote a Cayley–Dickson element UP to a higher rung by the trivial
    SUBALGEBRA EMBEDDING (zero-pad the higher imaginary half) — TOTAL.

    ``x`` is a power-of-two-length element (dim ``d``); ``dim`` is the TARGET
    power-of-two dimension (``dim ≥ d``, ``dim ≤ CD_MAX_DIM``). Returns ``x``
    with ``dim − d`` trailing zeros appended (the higher components all zero):
    ``ℝ ↪ ℂ ↪ ℍ ↪ 𝕆 ↪ 𝕊``. When ``dim == d`` the element is returned
    unchanged (promote is defined for every input). The element is unchanged as
    a number — it merely gains higher components it does not use. Its inverse is
    :func:`cd_project` (one doubling at a time), so
    ``cd_project(cd_promote(x, 2·d)) == x`` EXACT.

    Exact-rational; the padding is the exact ``Q(0)``. No float, no
    ``abs()``, no numpy / ``math``."""
    el = _as_elem(x)
    d = len(el)
    if not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(
            f"cd_promote: dim must be a power of two ≤ {CD_MAX_DIM}; got {dim}")
    if dim < d:
        raise ValueError(
            f"cd_promote: target dim {dim} is below the element's dim {d}; "
            f"promote only zero-pads UP the Cayley–Dickson ladder — use "
            f"cd_project to descend")
    if dim == d:
        return el
    return el + (Q(0),) * (dim - d)


def cd_project(x: Sequence[Any]) -> Tuple[Q, ...]:
    """Project a Cayley–Dickson element DOWN one doubling (dim ``d`` → ``d/2``)
    by REALIFYING IFF the higher (imaginary-doubling) half all vanish — the
    inverse of :func:`cd_promote`.

    ``x`` is a power-of-two-length element (dim ``d ≥ 2``). If the top half
    ``x[d/2:]`` is all zero, returns the bottom half ``x[:d/2]`` (the element
    genuinely lives in the ``d/2`` subalgebra: e.g. a complex ``(a, 0)`` IS the
    real ``a``). If any higher component is genuinely present, raises a
    coherency ``ValueError`` NAMING the first such component (never a silent
    truncation — the rc104 lesson; dropping a present component would change the
    number). A real (dim 1) element has no higher half → ``ValueError``.

    ``cd_project(cd_promote(x, 2·d)) == x`` EXACT (promote zero-pads exactly the
    half this drops). Exact-rational; the vanishing test is a ``Q != 0``
    Class-K comparison. No float, no ``abs()``, no numpy / ``math``."""
    el = _as_elem(x)
    d = len(el)
    if d == 1:
        raise ValueError(
            "cd_project: a real (dim 1) element is already at the base rung ℝ; "
            "there is no higher (imaginary-doubling) half to drop")
    half = d >> 1
    for i in range(half, d):
        if el[i] != 0:                        # Class-K nonzero test; no abs()
            lo_name = ALGEBRA_NAMES.get(half, f"(dim {half})")
            hi_name = ALGEBRA_NAMES.get(d, f"(dim {d})")
            raise ValueError(
                f"cd_project: cannot realify {hi_name} → {lo_name} — the higher "
                f"(imaginary-doubling) component e{i} = {el[i]} is genuinely "
                f"present; dropping it would TRUNCATE the element, not project a "
                f"trivial embedding. Component e{i} is the genuinely non-trivial "
                f"coordinate. (Promote only zero-pads, so a promoted element's "
                f"higher half is all zero.)")
    return el[:half]


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
    # rc10: dispatch the integer cocycle to the C peer when present (native,
    # JPL-clean iterative doubling; bit-identical integer (index, sign) to the
    # pure-Python loop below, which remains the Pyodide / no-native fallback).
    if (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_cd_basis_product")):
        out_index = ctypes.c_int()
        out_sign = ctypes.c_int()
        rc = _native.LIB.srmech_cd_basis_product(
            int(dim), int(i), int(j),
            ctypes.byref(out_index), ctypes.byref(out_sign))
        if rc == _native.SRMECH_OK:
            return int(out_index.value), int(out_sign.value)
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
# The GAMMA-PARAMETERISED doubling — the CONTROL constructor (rc352, `#T997`).
#
# The generalised Cayley–Dickson product carries one parameter per rung:
#
#     (a1, a2)(b1, b2) = (a1·b1 + γ·conj(b2)·a2,  b2·a1 + a2·conj(b1))
#
# and the ``−`` hard-wired into :func:`_mult` above IS that γ, pinned to −1 at
# every level. γ = −1 everywhere is the DEFINITE ladder ℝ → ℂ → ℍ → 𝕆 → 𝕊 …
# that this module has always built; a ``+1`` anywhere makes the algebra SPLIT
# from that rung up.
#
# WHY IT SHIPS: **controls, not capability.** Every negative control the
# split-algebra work has needed — split-𝕆, split-ℂ, split-ℍ, Cl(0,7), 100+
# random tables — was hand-rolled in a test file because no constructor
# existed, and `[[feedback_negative_controls_for_carrier_claims_split_octonion
# _and_random_anticommutative]]` makes those controls mandatory. The capability
# argument was MEASURED and is dead: the whole 8-member γ-family at dim 8 is
# sign-cocycle-degenerate in the same 344/512 way (see :data:`CD_TURN_MAX_DIM`),
# and the associative twists are matrix algebras
# :mod:`srmech.amsc.carrier_schema` already publishes ``Mat`` for.
#
# WHY IT IS NOT A ``twist=`` PARAMETER ON ``cd_mult`` / ``cd_basis_product``:
# those two are ABI-exported and content-addressed. ``cd_basis_product`` is a C
# export, three ``lru_cache(maxsize=1)`` tables downstream assume ONE twist by
# construction, and ``octonion_table_attestation()`` content-addresses THE one
# 512-byte table — a twist parameter would silently change what that Class-A
# content-address means. The table is the honest carrier of a second algebra.
# ──────────────────────────────────────────────────────────────────────

def _normalise_gammas(dim: int, gammas: Any) -> Tuple[int, ...]:
    """Validate a per-doubling γ vector against ``dim`` → a tuple of ±1.

    ``None`` is the DEFINITE ladder (γ = −1 at every level) and normalises to
    ``(-1,) * log2(dim)``. A supplied vector is in **LADDER order**:
    ``gammas[0]`` is the ℝ→ℂ doubling, ``gammas[1]`` is ℂ→ℍ, and so on — the
    order the rungs are named in, not the order the recursion meets them.
    """
    if not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(f"dim must be a power of two ≤ {CD_MAX_DIM}; got {dim}")
    n_levels = dim.bit_length() - 1
    if gammas is None:
        return (-1,) * n_levels
    g = tuple(gammas)
    if len(g) != n_levels:
        raise ValueError(
            f"a dim-{dim} generalised Cayley–Dickson algebra has {n_levels} "
            f"doubling(s), so gammas needs {n_levels} entries in LADDER order "
            f"(gammas[0] = ℝ→ℂ); got {len(g)}")
    for k, v in enumerate(g):
        if isinstance(v, bool) or v not in (1, -1):
            raise ValueError(
                f"gammas[{k}] = {v!r}; each γ is exactly +1 (SPLIT at that "
                f"doubling) or −1 (definite). The Cayley–Dickson parameter is "
                f"a sign, not a scale")
    return g


def _gamma_basis_product(dim: int, gammas: Tuple[int, ...],
                         i: int, j: int) -> Tuple[int, int]:
    """``e_i·e_j = sign·e_{i⊕j}`` for the γ-parameterised doubling — the single
    engine behind :func:`algebra_table`, and the generalisation of
    :func:`cd_basis_product` (which is this with γ = −1 at every level).

    γ touches EXACTLY ONE branch: the ``(ph, qh) == (1, 1)`` cross term, where
    ``conj(b2)`` contributes ``+1`` at ``ql == 0`` and ``−1`` otherwise. γ = −1
    flips the sign exactly when ``ql == 0``; γ = +1 flips it exactly when it
    does not. Class-K sign composition throughout — never ``abs()``.
    """
    sign = 1
    index = 0
    p, q = i, j
    cur = dim
    while cur > 1:
        m = cur >> 1
        gamma = gammas[cur.bit_length() - 2]   # ladder index of THIS doubling
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
        else:                                   # (γ b2* a2) in first — swap
            top, p, q = 0, ql, pl
            if (ql == 0) if gamma < 0 else (ql != 0):
                sign = -sign
        if top:
            index += m
        cur = m
    return index, sign


def algebra_table(dim: int, gammas: Any = None) -> List[List[List[int]]]:
    """The rank-3 structure-constant table of the **generalised**
    Cayley–Dickson algebra — the CONTROL constructor (rc352, `#T997`).

    ``table[i][j][k]`` is the coefficient of ``e_k`` in ``e_i·e_j`` — the exact
    shape :func:`srmech.qm.octonion.octonion_mult_table` returns and
    :func:`inertia_signature` reads. The table is MONOMIAL by construction
    (``e_i·e_j = ±e_{i⊕j}``), so ``dim²`` of the ``dim³`` cells are nonzero.

    Args:
        dim: a power of two in ``[1, ALGEBRA_TABLE_MAX_DIM]``.
        gammas: the per-doubling parameter, in **LADDER order** —
            ``gammas[0]`` is the ℝ→ℂ doubling, ``gammas[1]`` is ℂ→ℍ, and so on.
            Each entry is ``+1`` (SPLIT at that rung) or ``−1`` (definite).
            ``None`` — the default — is ``−1`` everywhere.

    **The default is the shipped algebra, bit-identically.** ``gammas=None``
    reproduces :func:`cd_basis_product` at every ``(dim, i, j)`` up to dim 64
    (4096 pairs at 64, 0 disagreements), ``algebra_table(8)`` IS
    ``octonion_mult_table()`` and ``algebra_table(4)`` IS
    ``quaternion_mult_table()`` — element-for-element, not merely equivalent —
    and :func:`table_product` over it reproduces :func:`cd_mult` 300/300 on
    random dim-8 integer pairs and 200/200 on random exact-ℚ pairs. That is not
    a coincidence of two implementations agreeing: the C peer
    ``srmech_cd_basis_product`` and ``srmech_algebra_table`` are the SAME
    cocycle engine, called with and without a γ vector.

    **What a ``+1`` buys, MEASURED (dim 8, all eight γ-triples).** Exactly two
    answers appear::

        gammas (ladder)   trace inertia   norm inertia   algebra
        (−1, −1, −1)      (1, 7, 0)       (8, 0, 0)      𝕆
        every other       (5, 3, 0)       (4, 4, 0)      split-𝕆

    — one definite algebra and one split algebra, seven ways. The split answer
    matches rc349's ``inertia_signature`` differential, reached there through a
    third, independent construction.

    **SCOPE — this is a CONTROL constructor, not a substrate extension.** A
    split algebra is not a new carrier: the sign cocycle is degenerate in the
    same 344/512 way at dim 8 for every member of the family, and every
    associative twist is a matrix algebra ``Mat`` already publishes. Nothing in
    the closed simulation is built on a γ ≠ −1 rung.

    Returns:
        ``dim × dim × dim`` nested ``list[int]``.

    Raises:
        ValueError: ``dim`` not a power of two in range, or ``gammas`` the
            wrong length / not all ±1.

    Note:
        Exact integers end to end — no float, no ``abs()`` (the sign is the
        Class-K pin-slot composition inside :func:`_gamma_basis_product`).
        Rosetta peer ``srmech_algebra_table``. Class K ∘ C ∘ A.

    Canonical SSoT:
    - Schafer, R.D. (1966), *An Introduction to Nonassociative Algebras*, §III.4
      — the Cayley–Dickson process with a general scalar parameter.
    - Springer, T.A. & Veldkamp, F.D. (2000), *Octonions, Jordan Algebras and
      Exceptional Groups*, §1.5–1.7 — the split composition algebras.
    - ``[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]``
    """
    if not _is_pow2(dim) or dim > ALGEBRA_TABLE_MAX_DIM:
        raise ValueError(
            f"algebra_table: dim must be a power of two ≤ "
            f"ALGEBRA_TABLE_MAX_DIM={ALGEBRA_TABLE_MAX_DIM}; got {dim}. That "
            f"ceiling bounds MATERIALISING the dim³ tensor, not the cocycle — "
            f"cd_basis_product answers to CD_MAX_DIM={CD_MAX_DIM}")
    g = _normalise_gammas(dim, gammas)
    # rc352: the integer cocycle + table fill dispatch to srmech_algebra_table
    # (the same C engine srmech_cd_basis_product rides, with the γ vector
    # threaded). Bit-identical integers to the pure loop below, which stays the
    # Pyodide / no-native fallback.
    native = _native.algebra_table_c(dim, None if gammas is None else list(g))
    if native is not None:
        return [[[native[(i * dim + j) * dim + k] for k in range(dim)]
                 for j in range(dim)] for i in range(dim)]
    table = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            idx, sign = _gamma_basis_product(dim, g, i, j)
            table[i][j][idx] = sign
    return table


def table_product(table: Any, x: Sequence[Any], y: Sequence[Any]
                  ) -> Tuple[Q, ...]:
    """The product of two elements read off a **structure-constant table** —
    exact, table-sensitive, and defined for algebras srmech has no hard-wired
    product for (rc352, `#T997`)::

        (x·y)_k = Σ_{i,j} table[i][j][k] · x_i · y_j

    This is :func:`cd_mult`'s table-driven sibling. ``cd_mult`` computes the
    ONE Cayley–Dickson product its recursion is wired for; this computes the
    product of whatever algebra the caller hands it — a split twist from
    :func:`algebra_table`, ``octonion_mult_table()``, or a random table with no
    algebraic structure at all. **Two table-driven products already existed in
    this tree and neither shipped** (a private dim-8-hardcoded loop in
    :mod:`srmech.math.laplacian` with one caller, and a test-local oracle that
    existed *because* no shipped product took a table); this is the one both
    now route through.

    **It agrees with the shipped product where both are defined.**
    ``table_product(algebra_table(dim), x, y) == cd_mult(x, y)`` — 300/300 on
    random dim-8 integer pairs and 200/200 on random exact-ℚ pairs. The two
    routes are genuinely different (a triple loop over a materialised tensor
    versus a recursive doubling / a cocycle call), which is what makes the
    agreement a differential rather than a tautology.

    Args:
        table: the ``dim × dim × dim`` structure-constant tensor of exact
            ``int``. ``table[i][j][k]`` is the coefficient of ``e_k`` in
            ``e_i·e_j``; the dimension is ``len(table)`` and nothing else
            supplies it.
        x, y: ``dim``-length elements. Every exact-rational scalar
            :func:`cd_mult` accepts is accepted here (``int`` / ``Q`` /
            ``fractions.Fraction`` / ``float`` → its EXACT ratio /
            ``(num, den)``).

    Returns:
        A ``dim``-tuple of exact :class:`~srmech.amsc.q.Q` — the same carrier
        :func:`cd_mult` returns, so the two are directly comparable.

    Raises:
        ValueError: ragged / empty table, or an element whose length is not
            ``len(table)``.
        TypeError: a structure constant that is not an exact ``int``.

    Note:
        Exact end to end: no float, no epsilon, no ``abs()``. Cost is
        ``O(dim³)`` exact-rational operations (the zero coefficients are
        skipped, so a MONOMIAL table costs ``O(dim²)``). Rosetta peer
        ``srmech_algebra_table_product`` — the SAME exact-ℚ element domain as
        ``srmech_cd_mult``, so there is no int64 element ceiling and no
        decline. Class M ∘ K ∘ N.
    """
    tbl = _structure_table(table)
    dim = len(tbl)
    ex = tuple(_coerce_frac(v) for v in x)
    ey = tuple(_coerce_frac(v) for v in y)
    if len(ex) != dim or len(ey) != dim:
        raise ValueError(
            f"table_product: the table is dim {dim}; got operands of length "
            f"{len(ex)} and {len(ey)}")
    # rc352: the bilinear accumulation dispatches to srmech_algebra_table_
    # product (the exact-ℚ table kernel beside srmech_cd_mult, sharing the same
    # qmat ℚ scalar arithmetic). Byte-identical reduced (num, den) to the pure
    # accumulation below at any magnitude; the pure body stays the Pyodide /
    # no-native fallback and the parity oracle.
    flat = [tbl[i][j][k] for i in range(dim) for j in range(dim)
            for k in range(dim)]
    native = _native.algebra_table_product_c(
        flat, dim,
        [(f.numerator, f.denominator) for f in ex],
        [(f.numerator, f.denominator) for f in ey])
    if native is not None:
        return tuple(Q(n, d) for n, d in native)
    out = [Q(0)] * dim
    for i in range(dim):
        if ex[i] == 0:
            continue
        for j in range(dim):
            if ey[j] == 0:
                continue
            coeff = ex[i] * ey[j]
            cell = tbl[i][j]
            for k in range(dim):
                if cell[k]:
                    out[k] += Q(cell[k]) * coeff
    return tuple(out)


def associator(x: Sequence[Any], y: Sequence[Any], z: Sequence[Any],
               table: Any = None) -> Tuple[Q, ...]:
    """``(x·y)·z − x·(y·z)`` — the ASSOCIATIVITY DEFECT, exact ℚ, any rung
    (rc360, `#T1032`).

    The zero tuple ⟺ the ordered triple associates. This is the quantity the
    Cayley–Dickson notes have been re-deriving inline at every measurement: the
    per-rung associativity census pinned at :data:`CD_TURN_MAX_DIM` and at four
    other sites (``carrier_schema`` / ``introspect`` / the rc343 ceiling test /
    the C header) is exactly ``count(associator(e_i, e_j, e_k) == 0)`` over the
    ordered basis triples::

        dim  2:      8/8       dim  4:     64/64      dim  8:    344/512
        dim 16:   2248/4096    dim 32:  16808/32768

    — MEASURED through this op on the definite ladder, reproducing the shipped
    fill exactly. It does NOT move those numbers; it is the named home for
    computing them.

    Args:
        x, y, z: equal-length elements. With ``table=None`` the length must be
            a power of two ``≤ CD_MAX_DIM`` (the definite ladder, via
            :func:`cd_mult`); with a ``table`` the length must be
            ``len(table)``. Every exact-rational scalar :func:`cd_mult` accepts
            is accepted here.
        table: an optional rank-3 structure-constant tensor —
            :func:`algebra_table` (the definite ladder, or a split γ-twist
            when ``gammas=`` is given: the STRUCTURED negative control), or any
            table :func:`table_product` reads. ``None`` — the default — is the
            definite Cayley–Dickson ladder ℝ→ℂ→ℍ→𝕆→𝕊…

    Returns:
        A ``dim``-tuple of exact :class:`~srmech.amsc.q.Q`.

    Raises:
        ValueError: operands of unequal length; a non-power-of-two length when
            ``table is None``; a ``table`` whose dim disagrees with the
            operands.

    Note:
        Exact end to end — no float, no epsilon, no ``abs()``. Two routes, both
        already C-backed: ``table=None`` composes ``srmech_cd_mult``, a
        ``table`` composes ``srmech_algebra_table_product``. NO new C symbol —
        the associator IS the composition, so a dedicated kernel would only
        re-spell ``a·b`` twice. ``composition_of_c``. Class M ∘ K.

    Canonical SSoT:
    - Schafer, R.D. (1966), *An Introduction to Nonassociative Algebras*, §III.1
      — the associator ``(x, y, z)`` as the trilinear defect measuring
      departure from associativity.
    - Baez, J.C. (2002), *The Octonions*, Bull. AMS **39** 145–205,
      arXiv:math/0105155, §1–§2 — the octonion associator and alternativity.
    """
    ex = tuple(_coerce_frac(v) for v in x)
    ey = tuple(_coerce_frac(v) for v in y)
    ez = tuple(_coerce_frac(v) for v in z)
    if not (len(ex) == len(ey) == len(ez)):
        raise ValueError(
            f"associator: the three operands must share dimension; got "
            f"{len(ex)}, {len(ey)} and {len(ez)}")
    if table is None:
        ex, ey, ez = _as_elem(ex), _as_elem(ey), _as_elem(ez)
        left = cd_mult(cd_mult(ex, ey), ez)
        right = cd_mult(ex, cd_mult(ey, ez))
    else:
        tbl = _structure_table(table)
        if len(tbl) != len(ex):
            raise ValueError(
                f"associator: the table is dim {len(tbl)}; got operands of "
                f"length {len(ex)}")
        left = table_product(tbl, table_product(tbl, ex, ey), ez)
        right = table_product(tbl, ex, table_product(tbl, ey, ez))
    return tuple(a - b for a, b in zip(left, right))


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
    # rc158: the integer cycle dispatches to srmech_cd_left_orbit (composes the
    # cocycle C peer). Byte-identical cycle order to the pure walk below, which
    # remains the Pyodide / no-native fallback.
    native = _native.cd_left_orbit_c(dim, start_idx, gen_idx)
    if native is not None:
        return native
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
    gens = list(generator_idxs)
    for g in gens:
        if not (0 <= g < dim):
            raise ValueError(f"generator index {g} out of range [0, {dim})")
    # rc158: the integer sub-loop fixpoint dispatches to srmech_cd_closure
    # (composes the cocycle C peer). The C set is element-identical to the pure
    # fixpoint below (a set — order-independent), which stays the no-native
    # fallback.
    native = _native.cd_closure_c(dim, gens)
    if native is not None:
        return native
    elems: Set[Tuple[int, int]] = {(1, 0)}
    elems.update((1, g) for g in gens)
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
    # rc158: dispatch the subset search to srmech_cd_min_generating_set (which
    # composes srmech_cd_closure). Returns k>0 (found), 0 (no spanning subset →
    # the ValueError below), or None (no-native / bounded-search overflow → the
    # complete pure oracle). Same minimal k as the pure loop (order-independent).
    native = _native.cd_min_generating_set_c(dim, units)
    if native is not None:
        if native > 0:
            return native
        raise ValueError(
            f"no subset of {units} generates the full loop of {full} signed "
            f"units in dim {dim}"
        )
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


def _terms_to_elem(dim: int, terms) -> Tuple[Q, ...]:
    e = [Q(0)] * dim
    for a, s in terms:
        e[a] += Q(s)
    return tuple(e)


def _build_zero_divisor_dict(i: int, j: int, k: int, l: int, s: int
                             ) -> Dict[str, Any]:
    """Assemble the witness dict from the found basis indices (shared by the
    native + pure paths so both emit a byte-identical result)."""
    dim = 16
    terms_x = [(i, 1), (j, 1)]
    terms_y = [(k, 1), (l, s)]
    is_zero, prod = _basis_sum_terms_zero(dim, terms_x, terms_y)
    assert is_zero, "witness (i,j,k,l,s) does not annihilate — broken convention"
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
        "product": tuple(Q(v) for v in prod),
        "product_is_zero": True,
    }


def sedenion_zero_divisor_witness() -> Dict[str, Any]:
    """Exhibit a concrete sedenion (dim 16) zero divisor: ``x, y`` both nonzero
    with ``x·y = 0``. Found by searching basis-unit pairs with **our own**
    multiplication table (own-work-first, not a literature transcription).

    Returns a dict with the two elements (as Q tuples), their human
    ``e_i ± e_j`` forms, their (nonzero) squared norms, and the (all-zero)
    product — the executable form of "zero divisors first appear at 16."
    """
    dim = 16
    # rc158: dispatch the integer basis-pair search to srmech_cd_zero_divisor_
    # witness (composes the cocycle C peer). It returns the SAME first witness
    # (same nested search order) as the pure loop below — byte-identical dict.
    native = _native.cd_zero_divisor_witness_c()
    if native is not None:
        return _build_zero_divisor_dict(*native)
    units = range(1, dim)                       # imaginary units e_1 … e_15
    for i in units:
        for j in range(i + 1, dim):
            terms_x = [(i, 1), (j, 1)]
            for k in units:
                for l in range(k + 1, dim):
                    for s in (1, -1):
                        terms_y = [(k, 1), (l, s)]
                        is_zero, _prod = _basis_sum_terms_zero(
                            dim, terms_x, terms_y)
                        if is_zero:
                            return _build_zero_divisor_dict(i, j, k, l, s)
    raise RuntimeError(                         # unreachable: 𝕊 has zero divisors
        "no basis-pair zero divisor found in the sedenions — the convention is "
        "inconsistent with Cayley–Dickson (this should be impossible)"
    )


def left_mult_matrix(x: Sequence[Any], table: Any = None) -> List[List[Q]]:
    """The ``n×n`` rational matrix of the linear map ``u ↦ x·u`` (column ``c`` is
    ``x·e_c``), row-major.

    rc160 (Qalg TAIL Batch 4): each column ``x·e_c`` is a :func:`cd_mult` (the
    C-dispatched CD product) over the C-dispatched :func:`cd_basis` unit vector —
    so this is a ``composition_of_c`` (a Python loop over the C multiplication
    building the matrix, the ``mat_dot`` precedent). Byte-identical to the pure
    recursive doubling either way.

    **``table`` names a DIFFERENT algebra** (rc352, `#T997`). ``None`` — the
    default — is the shipped Cayley–Dickson product, unchanged. A rank-3
    structure-constant table (from :func:`algebra_table`, or hand-built) routes
    the columns through :func:`table_product` instead, so the left-regular
    representation of a split twist or a control table is reachable — and with
    it :func:`left_mult_kernel`'s zero-divisor witness on those algebras.

    **This is also the differential that keeps ``table_product`` honest.**
    Contracting ``L(x)`` against ``y`` — ``Σ_c L[r][c]·y_c`` — reproduces
    ``cd_mult(x, y)``, MEASURED 200/200 on random dim-8 pairs; building a matrix
    column-by-column and then contracting it is a genuinely different route from
    a triple loop over a tensor. So contracting ``left_mult_matrix(x, table)``
    against ``y`` versus ``table_product(table, x, y)`` is a real two-route
    check with **zero duplicated code** — which is the reason this argument
    exists here rather than a second table-driven product existing somewhere as
    a test oracle.

    The contraction is written out as an exact-ℚ sum, NOT as a matmul: this
    module is numpy-free by construction (see the module docstring), and matrix
    contraction is a **carrier op** (:func:`srmech.math.laplacian.mat_matmul` /
    ``mat_matvec``) rather than an operator to reach for — numpy is a carrier,
    never the math engine, and ``L(x)`` here is a nested list of exact
    :class:`~srmech.amsc.q.Q`, which no numpy dtype can hold without rounding.
    """
    x = _as_elem(x)
    n = len(x)
    if table is None:
        cols = [cd_mult(x, cd_basis(n, c)) for c in range(n)]
    else:
        tbl = _structure_table(table)
        if len(tbl) != n:
            raise ValueError(
                f"left_mult_matrix: the table is dim {len(tbl)} but the element "
                f"has {n} components")
        cols = [table_product(tbl, x, cd_basis(n, c)) for c in range(n)]
    return [[cols[c][r] for c in range(n)] for r in range(n)]


def _rational_nullspace(matrix: List[List[Q]]) -> List[Tuple[Q, ...]]:
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
    basis: List[Tuple[Q, ...]] = []
    for fc in free_cols:
        vec = [Q(0)] * n
        vec[fc] = Q(1)
        for i, pc in enumerate(pivot_cols):
            vec[pc] = -a[i][fc]
        basis.append(tuple(vec))
    return basis


def left_mult_kernel(x: Sequence[Any], table: Any = None) -> List[Tuple[Q, ...]]:
    """Kernel basis of ``u ↦ x·u``. **Nonempty ⟺ ``x`` is a left zero divisor ⟺
    multiply-by-``x`` has no inverse map** — the "no backward direction to point"
    of §VII.6.23.4. Empty for every nonzero element of a division algebra (≤𝕆).

    rc160 (Qalg TAIL Batch 4): the exact-ℚ nullspace of ``L(x)`` dispatches to
    the C peer ``srmech_qmat_nullspace`` (the classical free-variable basis over
    plain ℚ) — so this is a ``composition_of_c`` (``srmech_qmat_nullspace`` over
    the C-composed :func:`left_mult_matrix`). The pure :func:`_rational_nullspace`
    is the byte-identical fallback: both build the SAME classical free-variable
    basis (leading-1 RREF, free variables set to a unit column), so the basis is
    element-for-element identical.

    **``table``** (rc352, `#T997`) routes ``L(x)`` through
    :func:`table_product`, so this becomes a zero-divisor **witness** on any
    algebra a table can express — split-𝕆 at dim 8, where the shipped ladder
    has none. It is the witness half only: zero divisors are measure-zero
    (``left_mult_is_invertible`` returned True on 300/300 random dim-16
    elements), so FINDING a candidate is a separate problem and this op does
    not solve it.
    """
    mat = left_mult_matrix(x, table)
    n = len(mat)
    native = _native.qmat_nullspace_c(
        [(mat[r][c].numerator, mat[r][c].denominator)
         for r in range(n) for c in range(n)], n, n)
    if native is not None:
        return [tuple(Q(p[0], p[1]) for p in vec) for vec in native]
    return _rational_nullspace(mat)


def _native_is_invertible(el: Tuple[Q, ...]):
    """The invertibility decision via the native modular-rank gate
    ``srmech_sedenion_is_navigable`` (rc12; bignum-free, exact — see
    ``c/src/srmech_sedenion.c``). Returns the bool, or ``None`` when there is no
    native lib OR the integer-cleared direction exceeds the C domain (dim past
    :data:`CD_DENSE_MAX_DIM` / int64 magnitude / the certainty prime table) — in
    which case the caller routes to the exact-rational kernel. Singularity is
    scale-invariant, so clearing denominators to integer numerators is exact."""
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_sedenion_is_navigable")):
        return None
    # rc298 (`#933`): the dense n×n C path stops at CD_DENSE_MAX_DIM (its
    # modular-rank matrix is the library's one quadratic buffer). Decline HERE
    # rather than marshalling a vector the callee will reject — the exact
    # oracle below is the complete answer at every dim ≤ CD_MAX_DIM.
    if len(el) > CD_DENSE_MAX_DIM:
        return None
    den = 1
    for v in el:
        den = den * v.denominator // _gcd(den, v.denominator)
    int64_max = (1 << 63) - 1
    nums = []
    for v in el:
        num = int(v * den)
        if num > int64_max or num < -int64_max - 1:
            return None                      # beyond int64 → exact oracle
        nums.append(num)
    n = len(nums)
    arr = (ctypes.c_int64 * n)(*nums)
    out = ctypes.c_int()
    rc = _native.LIB.srmech_sedenion_is_navigable(arr, n, ctypes.byref(out))
    if rc != _native.SRMECH_OK:
        return None                          # absurd magnitude → exact oracle
    return out.value == 1


def left_mult_is_invertible(x: Sequence[Any], table: Any = None) -> bool:
    """``True`` iff ``u ↦ x·u`` is a bijection (a backward direction exists).

    Always ``True`` for nonzero ``x`` at dims ≤ 8 on the DEFINITE ladder;
    ``False`` for a zero divisor at dim ≥ 16 — the reversibility that ends at
    the Hurwitz wall. Hand it a SPLIT table and ``False`` appears at dim 2
    already, which is the honest answer and the ladder's own wall is not it.

    rc12: dispatches the decision to the native modular-rank gate
    ``srmech_sedenion_is_navigable`` when present (NO bignum: the n×n signed
    XOR-circulant L(x) is decided by integer rank over word-size primes, bit-
    identical bool to the kernel-emptiness test below). The exact-rational
    kernel is the complete alternative for no-C environments and the
    unbounded-magnitude tail.

    **``table``** (rc352, `#T997`) answers for the algebra the table names.
    That gate is Cayley–Dickson-specific by construction — it rebuilds the
    signed XOR-circulant from the shipped cocycle — so it does not apply, and
    the op takes the exact-kernel route instead. That route is NOT a
    degradation: ``srmech_qmat_nullspace`` over the ``srmech_algebra_table_
    product``-composed ``L(x)`` is C the whole way down and exact at any
    magnitude, so a bare-C host answers this identically (ADR-0009 — a
    different C route, not a decline).
    """
    el = _as_elem(x)
    if table is None:
        native = _native_is_invertible(el)
        if native is not None:
            return native
    return len(left_mult_kernel(el, table)) == 0


# ──────────────────────────────────────────────────────────────────────
# The ℝ→ℂ rung instrument — ORDERABILITY, read off a multiplication table.
#
# rc349 (`#T987`, consolidating `#T968`); CORRECTED rc358 (`#T1032`) — the old
# wording ("loses ONE capability per doubling: … 𝕆→𝕊 composition") named the
# WRONG PROPERTY at the fourth rung, not the wrong SHAPE. It IS one loss per
# doubling: ℝ→ℂ ordering, ℂ→ℍ commutativity, ℍ→𝕆 associativity, 𝕆→𝕊
# ALTERNATIVITY. Composition is not a second casualty. Every Cayley–Dickson
# algebra is quadratic (x² − 2Re(x)x + N(x) = 0) and its conjugation is the
# ADJOINT of left multiplication (⟨xy,w⟩ = ⟨y, x̄w⟩ — measured here with ZERO
# violations over all 16³ and all 32³ basis triples), so L_x* = L_x̄ makes
# T = L_x̄∘L_x − N(x)·Id SELF-ADJOINT and, for a FIXED x,
#     [x,x,y] = 0 for all y   ⟺   T = 0   ⟺   N(xy) = N(x)·N(y) for all y.
# The two are the same condition per element; the classical rung name states
# the CONSEQUENCE. (Per PAIR they separate, the weak way round: x = e₁+e₁₀,
# y = e₄ has [x,x,y] = 2·e₁₅ ≠ 0 while N(xy) = 2 = N(x)·N(y).)
# ZERO-DIVISOR-FREENESS is a ONE-WAY corollary and needs a hypothesis the
# ladder never states: composition AND AN ANISOTROPIC NORM ⟹ no zero divisors.
# Bare "composition ⟹ no zero divisors" is FALSE — split-𝕆 is a composition
# algebra (exact, all seven γ-twists) WITH zero divisors: (e₀+e₁)(e₀−e₁) = 0,
# gated cd_norm_sq(e₀+e₁, gammas=γ) = 0, left-multiplication kernel dim 4.
# Losing composition therefore does not by itself PRODUCE zero divisors: at
# dim 16 they are EXHIBITED (:func:`sedenion_zero_divisor_witness`), never
# inferred — and :func:`left_mult_is_invertible` returns True on 200/200 random
# dim-16 elements, so the wall is invisible to sampling at dim 16 AND at
# split-𝕆 dim 8. Exhibit, do not sample.
# The ladder is BOUNDED because the law that never dies is FLEXIBILITY: the
# linearised [a,b,c] + [c,b,a] has ZERO violations on EVERY basis triple at
# dim 1…64 (exhaustive — 262 144 triples at dim 64 — and on all 16 γ-families
# at dim 16 and all 32 at dim 32), while the linearised [a,b,c] + [b,a,c] has
# 0 / 0 / 672 / 10 080 / 104 160 violations at dim 4 / 8 / 16 / 32 / 64.
# A linearised identity checked on a basis is a PROOF for all elements, not a
# sample (char ≠ 2). Schafer (1954), already cited above: flexibility and
# conjugation survive every rung — and they are the same fact, since
# [a,b,c] = −[c,b,a] IS the reversal anti-automorphism.
# ⚠️ NEVER instrument this with the DIAGONAL BASIS SHAPES. (a,a,b), (a,b,b)
# and (a,b,a) have ZERO nonzero associators at every dim measured INCLUDING 64,
# so a basis-shape count reports alternativity ALIVE at dim 64. The
# random-anticommutative control has aba_nonzero = 0 while failing flexibility
# outright. Only the linearised identity decides. The three rungs after the
# first already had instruments in this tree
# (:func:`srmech.amsc.cascade.cd_basis_product` commuting-pair counts;
# ``hdc.loop_associator`` / ``genome_octonion_associator``;
# :func:`sedenion_zero_divisor_witness` / :func:`left_mult_is_invertible`).
# The FIRST rung had none. This is it.
# ──────────────────────────────────────────────────────────────────────

def _pin_magnitude(v: int) -> int:
    """Class K pin-slot ∘ Class C re-orientation → the exact integer magnitude.

    ``pin_slot_at_zero`` (Class K) splits ``v`` at the zero-crossing into an
    orientation; ``reorient`` (Class C) re-applies that orientation to ``v``
    itself, which lands the magnitude. NEVER ``abs()`` — sign-flip IS the
    canonical Class-K phase-boundary per
    ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``, and this op
    is entirely about sign, so the discipline is load-bearing here rather than
    decorative. Type-preserving on Python ``int`` (arbitrary precision), so the
    whole cascade below stays exact integers — no float, no epsilon.
    """
    orientation, _slot = _pin_slot_at_zero(v)
    return _reorient(v, orientation=orientation)


def _pin_orientation(v: int) -> int:
    """Class K pin-slot → the orientation alone, in ``{-1, 0, +1}``."""
    orientation, _slot = _pin_slot_at_zero(v)
    return orientation


def _structure_table(table: Any) -> List[List[List[int]]]:
    """Validate + normalise a rank-3 structure-constant table to nested ints.

    ``table[i][j][k]`` is the coefficient of ``e_k`` in ``e_i·e_j`` — the SAME
    shape :func:`srmech.qm.octonion.octonion_mult_table` and
    :func:`srmech.qm.quaternion.quaternion_mult_table` already return. The
    dimension is ``len(table)``; NOTHING else supplies it.
    """
    rows = [list(r) for r in table]
    dim = len(rows)
    if dim < 1:
        raise ValueError("structure table: the table must have dimension ≥ 1")
    out: List[List[List[int]]] = []
    for i, row in enumerate(rows):
        cells = [list(c) for c in row]
        if len(cells) != dim:
            raise ValueError(
                f"structure table: row {i} has {len(cells)} columns; a "
                f"structure-constant table is dim × dim × dim (dim={dim})")
        for j, cell in enumerate(cells):
            if len(cell) != dim:
                raise ValueError(
                    f"structure table: cell ({i}, {j}) has {len(cell)} "
                    f"coefficients; expected dim={dim}")
            for k, v in enumerate(cell):
                if isinstance(v, bool) or not isinstance(v, int):
                    raise TypeError(
                        f"structure table: structure constant ({i}, {j}, {k}) "
                        f"is {type(v).__name__}; exact integers only (this op is "
                        f"float-free by contract)")
        out.append(cells)
    return out


#: The two quadratic forms this op can read off a table. They are DIFFERENT
#: reads with complementary signatures, and naming which one a number belongs
#: to is load-bearing: the literature quotes split-𝕆 as ``(4, 4)``, and that is
#: the NORM form — the TRACE form answers ``(5, 3, 0)`` for the same algebra.
INERTIA_FORMS: Tuple[str, str] = ("trace", "norm")


def _real_gram(table: List[List[List[int]]],
               form: str = "trace") -> List[List[int]]:
    """The exact integer Gram of the chosen quadratic form. Table-only.

    * ``form="trace"`` — ``q(x) = Re(x·x)``, the SQUARES read. Since
      ``q(x) = Σ_ij x_i x_j c_ij0``, its symmetric Gram is
      ``G_ij = c_ij0 + c_ji0``.
    * ``form="norm"`` — ``N(x) = Re(x·x̄)`` under the standard conjugation
      ``x̄ = x₀e₀ − Σ_{i>0} x_i e_i``, giving ``G_ij = σ_j c_ij0 + σ_i c_ji0``
      with ``σ_k = +1`` for ``k = 0`` and ``−1`` otherwise. The conjugation is
      a NAMED CONVENTION, not something the table determines — a bare
      structure-constant tensor carries no conjugation — so the norm read is
      only meaningful where that convention is the intended one.

    ``xᵀGx = 2·f(x)`` in both cases; the factor 2 is positive and moves no
    sign, so the inertia of ``G`` IS the inertia of ``f``. Reads ONLY the
    ``k = 0`` (real-part) slice of the table.
    """
    if form not in INERTIA_FORMS:
        raise ValueError(
            f"inertia form must be one of {INERTIA_FORMS}; got {form!r}")
    dim = len(table)
    if form == "trace":
        return [[table[i][j][0] + table[j][i][0] for j in range(dim)]
                for i in range(dim)]
    sigma = [1] + [-1] * (dim - 1)
    return [[sigma[j] * table[i][j][0] + sigma[i] * table[j][i][0]
             for j in range(dim)] for i in range(dim)]


def _first_nonzero_diagonal(mat: List[List[int]], alive: List[int]):
    """The first still-live index carrying a nonzero diagonal entry, or None."""
    for c in alive:
        if mat[c][c] != 0:
            return c
    return None


def _first_nonzero_offdiagonal(mat: List[List[int]], alive: List[int]):
    """The first still-live ``(k, l)``, ``k ≠ l``, with ``mat[k][l] ≠ 0``."""
    for a in range(len(alive)):
        for b in range(a + 1, len(alive)):
            if mat[alive[a]][alive[b]] != 0:
                return alive[a], alive[b]
    return None


def _hyperbolic_fold(mat: List[List[int]], cong: List[List[int]],
                     k: int, l: int) -> None:
    """The zero-diagonal escape: ``e_k ← e_k + e_l`` as a unimodular congruence.

    When every live diagonal entry vanishes but some off-diagonal ``mat[k][l]``
    does not, the form restricted to ``span(e_k, e_l)`` is a hyperbolic plane.
    Adding column/row ``l`` into ``k`` makes ``mat[k][k] = 2·mat[k][l] ≠ 0``
    (both diagonals being zero in this branch) without changing the form — a
    determinant-1 congruence, so Sylvester's law leaves the inertia alone.
    """
    dim = len(mat)
    for r in range(dim):
        cong[r][k] = cong[r][k] + cong[r][l]
    for c in range(dim):
        mat[k][c] = mat[k][c] + mat[l][c]
    for r in range(dim):
        mat[r][k] = mat[r][k] + mat[r][l]


def _strip_common_factor(mat: List[List[int]], alive: List[int]) -> None:
    """Divide the live block by its positive gcd — inertia-invariant, in place.

    Scaling a symmetric matrix by a POSITIVE rational leaves every eigenvalue's
    sign alone, so the signature is untouched; it exists purely to keep the
    exact integers small (measured: it holds the returned witness entries to
    2 bits at every dim probed, and keeps the C peer inside int64 to dim 16).
    Uses the Class-I cyclic gcd, not ``math.gcd``.
    """
    g = 0
    for i in alive:
        for j in alive:
            g = _gcd(g, _pin_magnitude(mat[i][j]))
    if g > 1:
        for i in alive:
            for j in alive:
                mat[i][j] //= g


def _primitive(vec: List[int]) -> List[int]:
    """Divide a witness by the positive gcd of its entries.

    ``(λx)ᵀG(λx) = λ²·xᵀGx`` and ``λ² > 0`` for every ``λ ≠ 0``, so rescaling a
    witness by a nonzero rational cannot change the sign it witnesses. The
    primitive representative is the canonical one.
    """
    g = 0
    for v in vec:
        g = _gcd(g, _pin_magnitude(v))
    if g > 1:
        return [v // g for v in vec]
    return list(vec)


def _congruence_inertia(gram: List[List[int]]):
    """Exact integer congruence diagonalisation → ``(n₊, n₋, n₀, witness)``.

    Symmetric Gaussian elimination over ℤ. The invariant carried is
    ``A_ij = c · (P_i)ᵀ G (P_j)`` for one scalar ``c`` shared by the whole live
    block, of tracked sign ``s``; the pivot-scaled Schur step
    ``A_ij ← p·A_ij − A_ik·A_jk`` keeps every entry an exact integer and
    multiplies ``c`` by ``1/p``, which is why ``s`` flips exactly when the
    pivot is negative. The true sign at pivot ``k`` is therefore ``s · sign(p)``
    — that is the number counted, and when it is negative, column ``k`` of
    ``P`` is a genuine witness (``P_kᵀ G P_k`` has that sign by the invariant).

    No division except the inertia-invariant positive-gcd strip; no rationals;
    no float; no tolerance. Sylvester's law of inertia is what makes the answer
    independent of every pivot choice made along the way.
    """
    dim = len(gram)
    mat = [list(row) for row in gram]
    cong = [[1 if i == j else 0 for j in range(dim)] for i in range(dim)]
    alive = list(range(dim))
    scale_orientation = 1
    n_plus = n_minus = n_zero = 0
    witness = None
    while alive:
        k = _first_nonzero_diagonal(mat, alive)
        if k is None:
            pair = _first_nonzero_offdiagonal(mat, alive)
            if pair is None:
                n_zero += len(alive)       # the live block is identically zero
                break
            _hyperbolic_fold(mat, cong, pair[0], pair[1])
            continue
        pivot = mat[k][k]
        pivot_orientation = _pin_orientation(pivot)
        true_orientation = scale_orientation * pivot_orientation
        if true_orientation > 0:
            n_plus += 1
        else:
            n_minus += 1
            if witness is None:
                witness = [cong[r][k] for r in range(dim)]
        alive.remove(k)
        pivot_col = [mat[i][k] for i in range(dim)]
        cong_col = [cong[r][k] for r in range(dim)]
        for i in alive:
            for r in range(dim):
                cong[r][i] = pivot * cong[r][i] - pivot_col[i] * cong_col[r]
        stepped = {(i, j): pivot * mat[i][j] - pivot_col[i] * pivot_col[j]
                   for i in alive for j in alive}
        for (i, j), v in stepped.items():
            mat[i][j] = v
        scale_orientation = scale_orientation * pivot_orientation
        _strip_common_factor(mat, alive)
    return n_plus, n_minus, n_zero, witness


def _full_square(table: List[List[List[int]]],
                 x: Sequence[int]) -> List[int]:
    """``x·x`` in FULL, recomputed straight from the table.

    Not just the real part: whether the square is a negative real MULTIPLE OF
    THE IDENTITY is the difference between a witness that certifies
    non-orderability and one that merely marks a negative direction of the
    trace form. Both are real facts; only one of them is the classical
    argument, so the op has to be able to tell them apart.
    """
    dim = len(table)
    out = [0] * dim
    for i in range(dim):
        if x[i] == 0:
            continue
        for j in range(dim):
            if x[j] == 0:
                continue
            coeff = x[i] * x[j]
            cell = table[i][j]
            for k in range(dim):
                if cell[k]:
                    out[k] += coeff * cell[k]
    return out


def _native_inertia(table: List[List[List[int]]], form: str = "trace"):
    """The signature + witness from the C peer ``srmech_algebra_inertia_signature``.

    Returns the same 4-tuple as :func:`_congruence_inertia`, or ``None`` when
    there is no native library, the dimension exceeds the C domain, or an exact
    intermediate would leave int64 (the C peer reports ``SRMECH_ERR_OVERFLOW``
    rather than wrapping) — in every one of those cases the caller routes to the
    ceiling-free pure-Python path above, which is exact at any magnitude.
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_algebra_inertia_signature")):
        return None
    if form not in INERTIA_FORMS:
        return None
    dim = len(table)
    int64_max = (1 << 63) - 1
    flat = []
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                v = table[i][j][k]
                if v > int64_max or v < -int64_max - 1:
                    return None
                flat.append(v)
    buf = (ctypes.c_int64 * len(flat))(*flat)
    out_plus = ctypes.c_int()
    out_minus = ctypes.c_int()
    out_zero = ctypes.c_int()
    out_has = ctypes.c_int()
    out_witness = (ctypes.c_int64 * dim)()
    ws_len = _native.LIB.srmech_algebra_inertia_ws_bound(ctypes.c_size_t(dim))
    if ws_len == 0:
        return None
    ws = ctypes.create_string_buffer(int(ws_len))
    rc = _native.LIB.srmech_algebra_inertia_signature(
        buf, ctypes.c_size_t(dim), ctypes.c_int(INERTIA_FORMS.index(form)),
        ws, ctypes.c_size_t(int(ws_len)),
        ctypes.byref(out_plus), ctypes.byref(out_minus), ctypes.byref(out_zero),
        ctypes.byref(out_has), out_witness)
    if rc != _native.SRMECH_OK:
        return None
    if out_has.value:
        return (int(out_plus.value), int(out_minus.value), int(out_zero.value),
                [int(out_witness[i]) for i in range(dim)])
    return (int(out_plus.value), int(out_minus.value), int(out_zero.value), None)


def inertia_signature(table: Any) -> Dict[str, Any]:
    """Sylvester inertia of the TRACE form ``q(x) = Re(x·x)``, read off a
    multiplication table — exactly, and with a negative direction attached.

    **What this measures, stated so it cannot be over-read: the inertia of the
    trace form, and nothing else.** ``q(x) = Re(x·x)`` is a quadratic form, so
    its complete invariant is the signature ``(n₊, n₋, n₀)``. The op computes
    that from the table. It does **not** certify composition, alternativity,
    associativity or division, and it cannot — see the measured ceiling below.

    **It reads the TABLE, never a declared dimension, and never a coordinate
    shortcut.** The input is the rank-3 structure-constant tensor
    ``table[i][j][k] = `` the coefficient of ``e_k`` in ``e_i·e_j`` — the exact
    shape :func:`srmech.qm.octonion.octonion_mult_table` and
    :func:`srmech.qm.quaternion.quaternion_mult_table` already return. The
    dimension is ``len(table)``; nothing consults ``CD_DIMS``,
    ``DIVISION_ALGEBRA_DIMS`` or any imaginary-dimension constant. In
    particular ``Re(x·x)`` is summed **from the structure constants**, never as
    the coordinate form ``a² − |v|²``: that substitution is input-blind, agrees
    with the real read 4000/4000 on 𝕆 but only 854/4000 on split-𝕆, and stays
    wrong at infinite precision. Reaching for it is the exact failure this op
    exists to avoid.

    **TWO FORMS, and which one a number belongs to is load-bearing.** The trace
    form ``q(x) = Re(x·x)`` and the norm form ``N(x) = Re(x·x̄)`` are different
    reads with complementary signatures. **The literature quotes split-𝕆 as
    (4, 4) — that is the NORM form.** Both ship, named:

    ==================  =====  ==============  ==============
    algebra             dim    trace ``q``     norm ``N``
    ==================  =====  ==============  ==============
    ℝ                   1      (1, 0, 0)       (1, 0, 0)
    ℂ                   2      (1, 1, 0)       (2, 0, 0)
    ℍ                   4      (1, 3, 0)       (4, 0, 0)
    𝕆                   8      (1, 7, 0)       (8, 0, 0)
    𝕊 (sedenion)        16     (1, 15, 0)      (16, 0, 0)
    **split-𝕆**         8      **(5, 3, 0)**   **(4, 4, 0)**
    split-ℍ             4      (3, 1, 0)       (2, 2, 0)
    split-ℂ             2      (2, 0, 0)       (1, 1, 0)
    dual numbers        2      (1, 0, 1)       (1, 0, 1)
    ==================  =====  ==============  ==============

    The norm read uses the standard conjugation ``x̄ = x₀e₀ − Σ_{i>0} x_i e_i``,
    which is a NAMED CONVENTION rather than something a bare structure tensor
    determines.

    **"ORDERED" DOES THREE JOBS AND THIS READS ONE — the FIELD sense.** ℂ is
    orderable as a *set* (trivially) and, measured on srmech's own ops, as an
    *additive group* (lexicographic order is compatible with ``cd_add``
    3954/3954); ``cd_norm_sq`` is even multiplicative 3000/3000, though not
    total — every magnitude class has ties and the ties are chirality orbits.
    What fails is compatibility with the *product* (``(0,1)·(0,1) = (−1,0)``
    breaks lex-order compatibility 1200/1600). So a negative-square direction
    means **not orderable AS A FIELD**, and says nothing about the additive or
    set senses. The returned ``order_sense`` names this permanently.

    **``n₋ == 0`` DOES NOT MEAN ORDERABLE EVEN IN THE FIELD SENSE, and that is
    why no orderability key is returned.** Split-ℂ answers ``(2, 0, 0)`` with
    no negative direction, yet ``(1+j)(1−j) = 0``: it has zero divisors, so a
    compatible total order is impossible (in an ordered ring ``a·b = 0`` is
    unreachable from ``a ≠ 0``, ``b ≠ 0``). The observable would therefore
    certify as "ordered" something provably not orderable, one rung above ℝ. It
    is also uncorrelated with being a division algebra: it flags 𝕊
    ``(1, 15, 0)`` and misses split-ℂ. The honest reading of ``n₋ == 0`` is
    **"no negative-square direction in the trace form"** — nothing more.

    **AND THE NORM SIGNATURE DOES NOT REPAIR THAT — measured.** The obvious fix
    is "test isotropy of the norm to separate split-ℂ from ℚ(√2)". It does not
    work at this resolution: **split-ℂ and ℚ(√2) return IDENTICAL answers in
    both forms** — trace ``(2, 0, 0)``, norm ``(1, 1, 0)`` — because a
    signature is a REAL-PLACE statement and ``a² − 2b²`` is isotropic over ℝ
    while anisotropic over ℚ. Separating them needs a RATIONAL zero of the norm
    form, which this op does not compute. Zero divisors are
    :func:`left_mult_is_invertible`; :func:`sedenion_zero_divisor_witness`
    takes no dimension argument and is sedenion-specific, so it is not a
    general isotropy surface either. **This gap is open, not closed.**

    **The witness, and exactly what it certifies.** ``witness`` is the negative
    pivot direction from the congruence diagonalisation: ``w`` with
    ``Re(w·w) < 0``. When ``w·w`` is additionally a negative real MULTIPLE OF
    THE IDENTITY — reported as ``witness_certifies_nonorderable`` — it is the
    classical argument outright: ``e_i² = −1`` ⇒ ``−1`` is a square ⇒ no
    compatible order. That is the case on the whole ladder. A merely negative
    ``Re(w·w)`` (e.g. ``[3,−5]`` in ℂ, whose square is ``−16 − 30i``) marks a
    negative direction of the trace form and does **not** contradict
    orderability on its own, so the two are reported separately rather than
    conflated.

    **THE CEILING, measured, not conceded under pressure.** For any table whose
    off-diagonal real parts cancel, ``Re(x·x) = Σ_i ε_i x_i²`` exactly, with
    ``ε_i = Re(e_i·e_i)``. So **200/200 random tables with the diagonal pinned
    to −1 and the off-diagonal fully scrambled return (1, 7, 0) — bit-identical
    to 𝕆 — while being 0/200 associative, 0/200 alternative and 0/200
    composition.** The op reads the inertia of the trace form and nothing else.
    For the off-diagonal structure use the complementary instruments already in
    this tree: ``srmech.math.hdc.loop_associator`` / ``g2_three_form``,
    ``srmech.amsc.genome.genome_octonion_associator``, and
    :func:`left_mult_is_invertible`.

    **What genuinely discriminates.** Split-𝕆 ``(5, 3, 0)`` against 𝕆
    ``(1, 7, 0)`` on identically-shaped tables, and 240 random tables spreading
    over 22 distinct signatures with 𝕆's answer occurring 0 times. An
    input-blind mechanism cannot produce that spread.

    Args:
        table: The structure-constant tensor, ``dim × dim × dim`` of exact
            ``int``. ``table[i][j][k]`` is the coefficient of ``e_k`` in
            ``e_i·e_j``. Basis element ``0`` is the real direction.

    Returns:
        ``{"dim", "form" ("trace"), "order_sense" ("field" — the sense in which
        a negative direction denies an order; NOT the additive or set senses),
        "signature" (n₊, n₋, n₀), "n_plus",
        "n_minus", "n_zero", "norm_signature" (the ``N`` read),
        "has_negative_direction" (bool — n₋ > 0; True PROVES a negative
        square direction exists, False proves nothing about orderability),
        "witness" (list[int] | None), "witness_real_square" (int | None —
        Re(w·w) < 0), "witness_square" (list[int] | None — the full w·w from
        the table), "witness_certifies_nonorderable" (bool — w·w is a negative
        real multiple of the identity)}``.

    Raises:
        ValueError: If the table is not ``dim × dim × dim``, or is empty.
        TypeError: If any structure constant is not an exact ``int``.

    Note:
        Exact and float-free end to end: the verdict is a comparison of two
        integer sums. There is deliberately NO float fast path. Cost is
        ``O(dim³)`` integer operations. Sign handling is the named Class K
        pin-slot ∘ Class C re-orientation composition (:func:`_pin_magnitude`)
        — never ``abs()``.

    **Grading (rc349).** The loss ladder — ℝ→ℂ ordering, ℂ→ℍ commutativity,
    ℍ→𝕆 associativity — is the classical Hurwitz result: DEFINITIONAL,
    textbook, forced. On the shipped ladder specifically ``n₋`` is exactly
    ``dim − 1`` (0/1/3/7/15 at dim 1/2/4/8/16), so **reading the shipped ladder
    is reading the dimension** — grade those rows DEFINITIONAL. The claim worth
    making is narrower and survives measurement: *the inertia of the trace form
    separates the Hurwitz ladder from its split forms and from random tables*
    — table-sensitive, exact, float-free.

    Canonical SSoT:
    - Sylvester, J.J. (1852), *A demonstration of the theorem that every
      homogeneous quadratic polynomial is reducible by real orthogonal
      substitutions to the form of a sum of positive and negative squares*,
      *Philos. Mag.* **4**:138–142 — the law of inertia.
    - Hurwitz, A. (1898), *Über die Composition der quadratischen Formen von
      beliebig vielen Variablen* — 1, 2, 4, 8.
    - Springer, T.A. & Veldkamp, F.D. (2000), *Octonions, Jordan Algebras and
      Exceptional Groups*, §1.7 — the split composition algebras and their
      quadratic-form signatures (the ``(4, 4)`` is the NORM form).
    - ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``
    - ``[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]``
    """
    tbl = _structure_table(table)
    result = _native_inertia(tbl, "trace")
    if result is None:
        result = _congruence_inertia(_real_gram(tbl, "trace"))
    n_plus, n_minus, n_zero, witness = result
    norm = _native_inertia(tbl, "norm")
    if norm is None:
        norm = _congruence_inertia(_real_gram(tbl, "norm"))
    real_square = None
    square = None
    certifies = False
    if witness is not None:
        witness = _primitive(list(witness))
        square = _full_square(tbl, witness)
        real_square = square[0]
        if real_square >= 0:                 # never observed; a live self-check
            raise AssertionError(
                f"inertia_signature: produced a witness {witness} whose "
                f"Re(w·w) = {real_square} is not negative — the instrument "
                f"must certify its own answer")
        # The STRONG certificate: w·w is a negative real multiple of e₀, so −1
        # is a square and no compatible order can exist. Strictly rarer than a
        # negative Re(w·w), which is why it is reported separately.
        certifies = all(v == 0 for v in square[1:])
    return {
        "dim": len(tbl),
        "form": "trace",
        # "ordered" does three jobs; a negative square direction denies only
        # the FIELD one. Named in the payload so a consumer cannot silently
        # widen it to the additive or set senses (both of which ℂ satisfies).
        "order_sense": "field",
        "signature": (n_plus, n_minus, n_zero),
        "n_plus": n_plus,
        "n_minus": n_minus,
        "n_zero": n_zero,
        "norm_signature": (norm[0], norm[1], norm[2]),
        "has_negative_direction": n_minus > 0,
        "witness": witness,
        "witness_real_square": real_square,
        "witness_square": square,
        "witness_certifies_nonorderable": certifies,
    }
