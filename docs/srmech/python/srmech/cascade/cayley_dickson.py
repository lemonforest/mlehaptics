"""Cayley–Dickson construction — the **open-exterior boundary-demonstrator**
(#915 / MFO §VII.6.23; the far side of the Hurwitz wall).

``the_one`` (:mod:`srmech.cascade.one`) and ``hypercomplex_couple``
(:mod:`srmech.cascade.hypercomplex_dft`) live entirely in the **reversible
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

* **Zero divisors first appear at dim 16 and never heal.** :func:`cd_zero_divisor_witness`
  exhibits a concrete pair ``x, y`` (both nonzero) with ``x·y = 0`` at any rung
  ``dim ≥ 16``, and :func:`cd_zero_divisor_witnesses` enumerates the WHOLE
  basis-pair set (168 at dim 16) — found from *our own* multiplication table via
  the GF(2) support solve, not transcribed from a paper. Division algebras
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

**Exact-rational, numpy-free.** Every component is a :class:`srmech.math.q.Q`
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

from .atoms import (      # Class-K pin-slot / Class-C reorient
    pin_slot_at_zero as _pin_slot_at_zero,
    reorient as _reorient,
)
from srmech.math.cyclic import (              # Class-I cyclic (native); NOT stdlib
    gcd as _gcd,
    mod_add as _mod_add,                      # (i+j) mod n — the group-ring lane
)
from srmech.math.q import Q, to_q            # #845: the CD element carrier is Q
from srmech.math.modular_linalg import gf_rref  # Class-I GF(2) solve — the zero-
#                                          divisor support system (rc395, `#T1000`)
from srmech.math.qmat import QMat             # rc437 (`#T1142`): the exact-ℚ solve
#          the division pair inverts its operator with — srmech_qmat_solve's carrier

from srmech import _native  # rc10: native srmech_cd_basis_product dispatch

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
#: non-commuting turns at any dim. srmech's own :class:`~srmech.math.mat.Mat`
#: (product ``mat_matmul``) was MEASURED over the matrix units of ``M_n(ℝ)`` at
#: 81/81 turn-composing pairs for ``n=3`` (algebra dim 9), 42 of them
#: non-commuting, and 256/256 for ``n=4`` (dim 16), 108 non-commuting — both
#: above 4. The ceiling is therefore **PER-CARRIER**: each capability row in
#: :mod:`srmech.introspect.carrier_schema` publishes its own ``max_dim`` /
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
    """Coerce one scalar to an exact :class:`~srmech.math.q.Q` — the CD element
    carrier (#845: srmech's C-native exact rational, not stdlib ``fractions``).
    A ``Q`` passes through unchanged; every other exact-rational scalar (``int`` /
    ``float`` / a stdlib ``fractions.Fraction`` / another ``as_integer_ratio``-able
    carrier / a ``(num, den)`` pair) rides :func:`srmech.math.q.to_q`, so the
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
        if any(v != -1 for v in g):
            # NOT the definite ladder: the coordinate sum is the wrong function
            # here, so read the norm through the algebra's own cocycle instead.
            # The DEFINITE case (γ = −1 at every rung) falls through to the fast
            # path below — proven identical, not assumed (the γ = −1 diagonal is
            # +1 at e₀ and −1 elsewhere, which is exactly Σ x_i² after the
            # conjugation sign).
            #
            # rc462 (`#T1179`): this predicate was ``any(v > 0 for v in g)``,
            # which names the SPLIT twists rather than the non-definite ones.
            # The two sets coincide only while γ ∈ {+1, −1}. It is the same
            # dichotomy-for-a-trichotomy defect as the cocycle's own branch, and
            # it is the one that would have SURVIVED that fix: with the kernel
            # correct at zero, γ = 0 says N(e₁) = 0 (the cocycle sign is 0)
            # while ``any(v > 0)`` routes it to Σ x_i² = 1. LATENT today —
            # _normalise_gammas above refuses γ = 0 — but stating the law the
            # fast path actually needs ("all γ are −1") is what keeps it latent.
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
# one-level-up analog of the srmech.math.carrier_ladder variable ladder.
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
    ``abs()``, no ``math``."""
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
    Class-K comparison. No float, no ``abs()``, no ``math``."""
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
# :mod:`srmech.introspect.carrier_schema` already publishes ``Mat`` for.
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

    **This is the PUBLIC CONTRACT, not input hygiene** (rc462, `#T1179`).
    :func:`_gamma_basis_product` is *defined* at γ = 0 — the degenerate rung,
    where the cross term vanishes and ``e₁·e₁ = 0`` — and this function is the
    only thing that keeps that rung out of :func:`algebra_table`,
    :func:`cd_norm_sq` and everything downstream of them. Peer of the C
    ``cd_check_gammas``, which refuses the same value at the same two sites.
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

    γ touches EXACTLY ONE branch: the ``(ph, qh) == (1, 1)`` cross term, whose
    first component is ``γ·conj(b2)·a2``. ``conj`` contributes ``+1`` at
    ``ql == 0`` and ``−1`` otherwise, so the coefficient this level composes in
    is exactly ``γ`` at ``ql == 0`` and ``−γ`` otherwise — a MULTIPLICATION by
    the parameter, not a decision about it. Class-K sign composition throughout
    — never ``abs()``.

    **Why the multiplicative form, and what it fixed (rc462, `#T1179`).** Until
    rc462 this line read ``if (ql == 0) if gamma < 0 else (ql != 0): sign =
    -sign`` — a *dichotomy* standing in for a parameter with three values in its
    natural domain. γ = 0 fails ``gamma < 0``, so it fell through the ``else``
    and was computed as γ = +1: MEASURED, the γ = 0 table came back
    **bit-identical to the SPLIT table** at dims 2, 4 and 8 and on the mixed
    ``(0, −1)`` vector. Nothing was ever wrong on the shipped surface —
    :func:`_normalise_gammas` refuses γ = 0 at every public entry, so the arm
    was LATENT, never live — but the validator was doing correctness work while
    presenting as input hygiene, and the next change to this module is exactly
    "open γ = 0". The form above cannot alias, because it is the coefficient
    itself: at γ = 0 the cross term VANISHES and the sign is ``0``, which is the
    dual-number/degenerate rung (``e₁·e₁ = 0`` at dim 2), and it is absorbing so
    a zero at any level survives to the result. On ±1 it is a no-op — VERIFIED
    over 127 γ vectors / 299 593 cells at dims 1–64, 0 mismatches.

    **The public contract did NOT open.** :func:`_normalise_gammas` (and its C
    peer ``cd_check_gammas``) still refuse γ = 0, so ``sign == 0`` is
    unreachable from :func:`algebra_table`, :func:`cd_norm_sq` or any other
    public callable — the C peer's ``assert(sign == 1 || sign == -1)`` is the
    tripwire that says so, and it fires the moment that contract is opened
    without revisiting the table's monomial claim. rc462 makes the kernel
    honest at zero; it does not make zero reachable.
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
            # The coefficient γ·conj(b2) contributes, verbatim: γ at ql == 0,
            # −γ otherwise. Class-K sign composition (a multiply, not an abs).
            sign = sign * (gamma if ql == 0 else -gamma)
        if top:
            index += m
        cur = m
    return index, sign


def algebra_table(dim: int, gammas: Any = None) -> List[List[List[int]]]:
    """The rank-3 structure-constant table of the **generalised**
    Cayley–Dickson algebra — the CONTROL constructor (rc352, `#T997`).

    ``table[i][j][k]`` is the coefficient of ``e_k`` in ``e_i·e_j`` — the exact
    shape :func:`srmech.physics.qm.octonion.octonion_mult_table` returns and
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


def flip_pair(dim: int, i: int, j: int) -> List[List[List[int]]]:
    """The definite Cayley–Dickson ladder table with ``e_i·e_j`` **and**
    ``e_j·e_i`` NEGATED — the ONE-NAMED-BIT flexibility control (rc387,
    ``#T1037``; the STRUCTURED residual ``#T1032`` declared at rc360).

    A sibling of :func:`algebra_table` / :func:`group_algebra_table`: it returns
    the same ``dim × dim × dim`` rank-3 structure-constant tensor
    (``table[i][j][k]`` = coefficient of ``e_k`` in ``e_i·e_j``) that
    :func:`table_product`, :func:`associator` and :func:`inertia_signature`
    read. The base is :func:`algebra_table` ``(dim)`` — the definite ladder
    ℝ→ℂ→ℍ→𝕆→𝕊…, C-dispatched bit-for-bit — and the ONLY change is a single
    Class-C sign reorientation applied at the two off-diagonal cells ``(i, j)``
    and ``(j, i)``, both on the shared index lane ``i ⊕ j`` (the CD product is
    monomial, ``e_i·e_j = ±e_{i⊕j}``, so each cell has exactly one nonzero
    coefficient).

    **WHY IT SHIPS: it is the ONLY control that breaks FLEXIBILITY, and by a
    CONSTANT.** The flexible law ``(x, y, x) = 0`` (equivalently the linearised
    ``(x, y, z) + (z, y, x) = 0``) holds on every rung of the definite ladder
    and on every γ-twist :func:`algebra_table` builds — the whole γ-family is
    flexible, so none of them can be the flexibility negative control. One
    named sign flip breaks it at **exactly 4 of the ``dim³`` ordered basis
    triples, uniformly over every admissible pair** — 4/64 at dim 4, 4/512 at
    dim 8, 4/4096 at dim 16 — MEASURED through :func:`associator` in
    ``docs/srmech/notes/cd_controls_rc387.py``. The constant is the control's
    signature: it isolates a flexibility defect with no dependence on which
    pair was flipped.

    **The inertia signature is UNCHANGED, by construction — and that is what
    makes the attribution clean.** :func:`inertia_signature` reads the TRACE
    form ``Re(x·x)``, which sees only the DIAGONAL cells ``(k, k)``; a flip
    touches only the strictly off-diagonal ``(i, j)`` / ``(j, i)`` with
    ``i ≠ j``, so the diagonal — and therefore the signature ``(1, 1, 0)`` /
    ``(1, 3, 0)`` / ``(1, 7, 0)`` / ``(1, 15, 0)`` at dim 2/4/8/16 — is
    identical to the definite ladder's. So this control moves the FLEXIBILITY
    law while holding the METRIC fixed; its complement
    :func:`group_algebra_table` does the exact opposite.

    Args:
        dim: a power of two in ``[1, ALGEBRA_TABLE_MAX_DIM]`` (the
            :func:`algebra_table` materialisation ceiling — it bounds the
            ``dim³`` tensor, not the cocycle).
        i, j: the two DISTINCT imaginary basis indices to flip, each in
            ``(0, dim)``. ``i == j`` is rejected — the flip is defined on an
            off-diagonal pair (a same-index flip would move the diagonal and
            so change the signature, defeating the control).

    Returns:
        ``dim × dim × dim`` nested ``list[int]`` — the definite ladder table
        with the two named cells negated.

    Raises:
        ValueError: ``dim`` not a power of two in range, ``i`` or ``j`` outside
            ``(0, dim)``, or ``i == j``.

    Note:
        ``composition_of_c`` — NO new C symbol. The heavy lift is
        :func:`algebra_table` (the C-dispatched ``srmech_algebra_table``
        cocycle engine); the sign flip is :func:`srmech.cascade.reorient`, the
        C-dispatched Class-C reorientation (``srmech_cascade_reorient_i64``),
        never ``abs()`` and never a bare negation. Exact integers throughout.
        Class C ∘ ``algebra_table``.

    Canonical SSoT:
    - Schafer, R.D. (1966), *An Introduction to Nonassociative Algebras*, §III.5
      — the flexible law and its linearisation.
    - ``[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]``
    """
    if not _is_pow2(dim) or dim > ALGEBRA_TABLE_MAX_DIM:
        raise ValueError(
            f"flip_pair: dim must be a power of two ≤ "
            f"ALGEBRA_TABLE_MAX_DIM={ALGEBRA_TABLE_MAX_DIM}; got {dim}")
    if not (0 < i < dim and 0 < j < dim):
        raise ValueError(
            f"flip_pair: i and j must be imaginary basis indices in (0, {dim}); "
            f"got i={i}, j={j}")
    if i == j:
        raise ValueError(
            f"flip_pair: i and j must be DISTINCT — a same-index flip moves the "
            f"diagonal (the trace form) and so changes the inertia signature, "
            f"which is exactly the control this op is built NOT to disturb; "
            f"got i == j == {i}")
    table = [[list(row) for row in plane] for plane in algebra_table(dim)]
    lane = i ^ j                              # the monomial index lane i⊕j
    # Class-C sign reorientation at the two off-diagonal cells — never a bare
    # magnitude strip (`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`).
    table[i][j][lane] = _reorient(table[i][j][lane], orientation=-1)
    table[j][i][lane] = _reorient(table[j][i][lane], orientation=-1)
    return table


def group_algebra_table(dim: int) -> List[List[List[int]]]:
    """The structure-constant table of the group ring ``ℝ[ℤ/dim]`` — the
    WRONG-QUOTIENT control (rc387, ``#T1037``; the STRUCTURED residual
    ``#T1032`` declared at rc360).

    A sibling of :func:`algebra_table` / :func:`flip_pair`: same
    ``dim × dim × dim`` rank-3 tensor, consumable by :func:`table_product`,
    :func:`associator` and :func:`inertia_signature`. Where
    :func:`algebra_table` builds the Cayley–Dickson cocycle on the index lane
    ``e_i·e_j = ±e_{i⊕j}`` (the XOR group ``(ℤ/2)^k``), this builds the CYCLIC
    group ring instead: lane ``(i + j) mod dim`` and **all signs +1**. It is
    the SAME dimension carrying a DIFFERENT group — for ``dim ≥ 4`` the cyclic
    ``ℤ/dim`` and the XOR ``(ℤ/2)^k`` are genuinely different quotients (they
    coincide only at ``dim = 2``), which is what "wrong quotient" names.

    **WHY IT SHIPS: it is the METRIC control, the complement of
    :func:`flip_pair`.** The group ring is commutative and associative with a
    trivial (all +1) cocycle, so it has **zero bite on the associativity laws**
    — flexible and fully associative at every rung, unlike the octonion ladder.
    Its bite is entirely on the METRIC: :func:`inertia_signature` reads the
    TRACE form as ``(2, 0, 0)`` / ``(3, 1, 0)`` / ``(5, 3, 0)`` / ``(9, 7, 0)``
    at dim 2/4/8/16 — versus the definite ladder's ``(1, 1, 0)`` /
    ``(1, 3, 0)`` / ``(1, 7, 0)`` / ``(1, 15, 0)`` — because ``e_i·e_i =
    +e_{2i mod dim}`` places the real-part diagonal on a different set of
    indices. MEASURED through the shipped ops in
    ``docs/srmech/notes/cd_controls_rc387.py``.

    **The tautology this control invites, LABELLED as one.** "The wrong-quotient
    associator differs from the ladder's on ``dim³ − assoc`` triples" (168/512
    at dim 8, 1848/4096 at dim 16) is a FORCED IDENTITY, not a finding: the
    group ring's OWN associator is identically zero (it is associative), so it
    differs from the ladder EXACTLY where the ladder fails to associate. That
    count IS the ladder's non-associating census (``512 − 344 = 168``) wearing
    a different name; it carries no information about the control. Use the group
    ring for the METRIC contrast (the signatures above), never for a "differs
    from the ladder" count.

    Args:
        dim: a power of two in ``[1, ALGEBRA_TABLE_MAX_DIM]`` — mirrors
            :func:`algebra_table`, so the control sits beside the ladder at
            matched rungs (``dim = 2, 4, 8, 16``) where the two quotients are
            most sharply the same dimension and a different group.

    Returns:
        ``dim × dim × dim`` nested ``list[int]`` — the monomial cyclic-convolution
        tensor, ``table[i][j][(i+j) mod dim] = 1``.

    Raises:
        ValueError: ``dim`` not a power of two in range.

    Note:
        ``composition_of_c`` — NO new C symbol. The lane ``(i + j) mod dim`` is
        :func:`srmech.math.cyclic.mod_add`, the C-dispatched Class-I modular add
        (``srmech_mod_add``); hand-rolling ``(i + j) % dim`` would make the op a
        Python-only kernel with no C twin, which the standalone-C ledger
        forbids. Exact integers; no float, no ``abs()``. Class I (cyclic).

    Canonical SSoT:
    - Lang, S. (2002), *Algebra* (3rd ed., GTM 211), §II.3 — the group ring
      ``R[G]`` and its structure constants.
    - Springer, T.A. & Veldkamp, F.D. (2000), *Octonions, Jordan Algebras and
      Exceptional Groups*, §1.5–1.7 — why a composition algebra is NOT a group
      ring (the contrast this control draws).
    - ``[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]``
    """
    if not _is_pow2(dim) or dim > ALGEBRA_TABLE_MAX_DIM:
        raise ValueError(
            f"group_algebra_table: dim must be a power of two ≤ "
            f"ALGEBRA_TABLE_MAX_DIM={ALGEBRA_TABLE_MAX_DIM}; got {dim}")
    table = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            lane = _mod_add(i, j, dim)        # Class-I cyclic (i+j) mod dim
            table[i][j][lane] = 1
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
        A ``dim``-tuple of exact :class:`~srmech.math.q.Q` — the same carrier
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
        A ``dim``-tuple of exact :class:`~srmech.math.q.Q`.

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
    - Schafer, R.D. (1966), *An Introduction to Nonassociative Algebras*,
      **ch. II eqn (11)** — the associator ``(x, y, z) = (xy)z - x(yz)`` as the
      trilinear defect measuring departure from associativity.
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


# rc436 (`#T1141`): the associator's SUPPORT as a first-class SET, not another
# count. The COUNT 168 was already pinned at five sites before this op existed
# (`associator`'s own census 512 - 344, `cd_cycle_holonomy`'s 168/512,
# `oct_mult`'s 168/343, `octonion_frame_read`'s seam read, and
# `group_algebra_table`'s labelled tautology). What was NOT shipped anywhere is
# the SET those counts count, nor the closed-form PREDICATE that reproduces it.
def octonion_associator_support() -> Dict[str, Any]:
    """The 168 ordered imaginary triples on which 𝕆's associator is NONZERO —
    as a SET, with the Fano predicate that reproduces it (rc436, `#T1141`).

    Class **A** (a content-addressed invariant: the set is fixed, so it is
    hashed once and carried with its digest) ∘ Class **E** (the catalog read —
    the seven Fano lines come from :func:`_octonion_fano_lines`, which DERIVES
    them from :func:`cd_basis_product` rather than tabulating them).

    **The count is not the contribution; the SET and the PREDICATE are.**
    ``168`` was already pinned at five sites in this tree before this op
    existed, and this op REPRODUCES it rather than moving it — the same
    discipline :func:`associator` states for the per-rung census. What no
    surface shipped was the set itself, or a closed form for membership.

    **The predicate, MEASURED to reproduce the support as a SET (not merely as
    a count)**::

        nonzero associator  ⟺  the three indices are distinct imaginary units
                               AND do not all lie on one Fano line

        7·6·5 − 7·3! = 210 − 42 = 168

    Ordered triples of distinct imaginary units number ``7·6·5 = 210``; each of
    the 7 Fano lines contributes ``3! = 6`` orderings that DO associate (a line
    spans an ℍ subalgebra, which is associative), and 210 − 42 = 168 remain.
    Set equality against the measured support is asserted by
    ``tests/test_octonion_associator_support_rc436.py``, not assumed here.

    **Why the three published denominators all give the same 168.** 𝕆 is an
    ALTERNATIVE algebra, so its associator is alternating: it vanishes whenever
    any two arguments coincide, and it vanishes whenever any argument is ``e₀``.
    Hence the support over all ``8³ = 512`` ordered basis triples, over the
    ``7³ = 343`` imaginary ones with repeats allowed, and over the ``210``
    distinct imaginary ones is **literally the same set of 168 triples** —
    measured, and the reason "168 of 512", "168 of 343" and "168 of 210" are
    three readings of one object rather than three coincidences.

    ⚠️ **COLLISION NOTE — ``168`` means at least two different things in this
    tree, and they are not related.** Check which one a number is before
    comparing:

    * **this op** — the 168 ordered imaginary triples where 𝕆's associator is
      nonzero (dimension **8**, the octonion rung, a NON-ASSOCIATIVITY census);
    * :func:`cd_zero_divisor_witnesses` at ``dim=16`` — the 168 basis-pair
      zero-divisor witnesses ``(eᵢ + eⱼ)(e_k + s·e_l) = 0`` (dimension **16**,
      the SEDENION rung, a ZERO-DIVISOR census). This is the sense
      :func:`inertia_signature`'s docstring uses when it writes "168 at dim 16".

    Same integer, different rung, different phenomenon, no derivation connecting
    them. A cross-reference between the two would be a numerology error.

    **NUMERICAL ADJACENCY, stated and NOT used.** ``|Aut(Fano)| = |PGL(3,2)| =
    |PSL(2,7)| = 168`` as well, and standard finite geometry says that group
    acts simply transitively on the ordered non-collinear point-triples — which
    would make this support a torsor under it. That is DERIVED FROM THE
    LITERATURE, **not measured here**, and nothing in this op depends on it. It
    is recorded so the coincidence is not re-discovered as a finding.

    Returns:
        A ``dict``:

        * ``dim`` — 8.
        * ``count`` — 168, the size of the support.
        * ``ordered_distinct_imaginary`` — 210, the population it sits in.
        * ``triples`` — the SET: a sorted tuple of 168 ``(i, j, k)`` int
          triples. This is the payload; the digest below is a convenience, not
          a replacement for it.
        * ``fano_lines`` — the 7 lines read from :func:`cd_basis_product`.
        * ``associating`` — the sorted 42 ordered triples that DO associate
          (the Fano-line orderings), so both halves of the partition ship.
        * ``predicate`` — the membership rule as prose.
        * ``arithmetic`` — ``"7*6*5 - 7*3! = 210 - 42 = 168"``.
        * ``sha256`` — Class-A content address over the canonical serialisation
          of ``triples`` (``"i,j,k"`` joined by ``";"``, ASCII), via
          :func:`srmech.amsc.format.sha256_bytes` so native dispatch is picked
          up transparently.
        * ``collision_note`` — the two-sense warning above, as a string, so a
          caller reading the dict alone still meets it.

    Note:
        No new C symbol and none is owed: this COMPOSES the already
        c_dispatched :func:`associator` (which is itself ``composition_of_c``
        over ``srmech_cd_mult``) and :func:`srmech.amsc.format.sha256_bytes`.
        ``composition_of_c``. Exact end to end — no float, no ``abs()``.

    Canonical SSoT:
    - Baez, J.C. (2002), *The Octonions*, Bull. AMS **39** 145–205,
      arXiv:math/0105155, **§2.1** — the Fano plane and its seven lines as the
      ℍ subalgebras of 𝕆.
    - Baez, *op. cit.*, arXiv:math/0105155, **§1.1** — alternativity, hence that
      the associator is alternating. rc436 repointed this locator: it read
      **§2.1**, which carries the Fano plane but contains the term ZERO times,
      while §1.1 carries it 6 times (`srmech/amsc/attested/literature_claims`,
      verdict VERIFIED). The claim was right and its address was wrong.
    - Schafer, R.D. (1966), *An Introduction to Nonassociative Algebras*,
      **ch. III** — the textbook treatment of alternative algebras.
    """
    from srmech.amsc.format import sha256_bytes  # Class A; native-dispatched

    lines = _octonion_fano_lines()
    line_sets = {frozenset(line) for line in lines}
    basis = [cd_basis(8, i) for i in range(8)]

    support: List[Tuple[int, int, int]] = []
    associating: List[Tuple[int, int, int]] = []
    for i in range(1, 8):
        for j in range(1, 8):
            if j == i:
                continue
            for k in range(1, 8):
                if k == i or k == j:
                    continue
                defect = associator(basis[i], basis[j], basis[k])
                if any(v != 0 for v in defect):
                    support.append((i, j, k))
                else:
                    associating.append((i, j, k))

    support_t = tuple(sorted(support))
    payload = ";".join("%d,%d,%d" % t for t in support_t).encode("ascii")
    return {
        "dim": 8,
        "count": len(support_t),
        "ordered_distinct_imaginary": 7 * 6 * 5,
        "triples": support_t,
        "fano_lines": lines,
        "associating": tuple(sorted(associating)),
        "predicate": ("distinct imaginary indices, not all three on one "
                      "Fano line"),
        "arithmetic": "7*6*5 - 7*3! = 210 - 42 = 168",
        "sha256": sha256_bytes(payload),
        "collision_note": (
            "168 has TWO unrelated senses in srmech: (a) THIS op -- the "
            "ordered imaginary triples where the dim-8 octonion associator is "
            "nonzero (a non-associativity census); (b) "
            "cd_zero_divisor_witnesses(16) -- the basis-pair zero-divisor "
            "witnesses at the dim-16 sedenion rung (a zero-divisor census), "
            "which is the sense inertia_signature's docstring uses. Different "
            "rung, different phenomenon, no derivation connects them. "
            "|Aut(Fano)| = 168 as well, which is literature-derived adjacency "
            "and is NOT measured or used here."),
        "line_membership_reproduces_support": (
            tuple(sorted(t for t in support_t if frozenset(t) not in line_sets))
            == support_t),
    }


def cd_commutator(x: Sequence[Any], y: Sequence[Any],
                  table: Any = None) -> Tuple[Q, ...]:
    """``x·y − y·x`` — the COMMUTATIVITY DEFECT, exact ℚ, any rung (rc380,
    `#T1055`).

    The k=2 "square-loop" sibling of :func:`associator` (the k=3 triangle loop):
    the two are the first two rungs of the Cayley–Dickson property-loss ladder,
    each a loop-defect that turns on one rung LATER than the last. The zero tuple
    ⟺ the ordered pair ``(x, y)`` commutes. It turns on at ℍ — the associator
    still 0 there — which is exactly what makes the two ops a ladder and not a
    restatement::

        dim  1 (ℝ):   0 / 1        noncommuting ordered basis pairs
        dim  2 (ℂ):   0 / 4
        dim  4 (ℍ):   6 / 16       ← turn-on rung
        dim  8 (𝕆):  42 / 64
        dim 16 (𝕊): 210 / 256

    — the closed form is ``(dim − 1)(dim − 2)`` (e₀ commutes with everything and
    each unit commutes with itself; every other distinct imaginary pair
    anticommutes, so ``[eᵢ, eⱼ] = 2·eᵢ·eⱼ ≠ 0``). MEASURED through this op on the
    definite ladder; it is the named home for computing those counts, not a mover
    of them.

    Args:
        x, y: equal-length elements. With ``table=None`` the length must be a
            power of two ``≤ CD_MAX_DIM`` (the definite ladder, via
            :func:`cd_mult`); with a ``table`` the length must be ``len(table)``
            (via :func:`table_product`). Every exact-rational scalar
            :func:`cd_mult` accepts is accepted here.
        table: an optional rank-3 structure-constant tensor —
            :func:`algebra_table` (the definite ladder, or a split γ-twist when
            ``gammas=`` is given: the STRUCTURED negative control), or any table
            :func:`table_product` reads. ``None`` — the default — is the definite
            Cayley–Dickson ladder ℝ→ℂ→ℍ→𝕆→𝕊…

    Returns:
        A ``dim``-tuple of exact :class:`~srmech.math.q.Q` — the all-zero tuple
        iff the ordered pair ``(x, y)`` commutes.

    Raises:
        ValueError: operands of unequal length; a non-power-of-two length when
            ``table is None``; a ``table`` whose dim disagrees with the operands.

    Note:
        Exact end to end — no float, no epsilon, no ``abs()``. Two routes, both
        already C-backed: ``table=None`` composes ``srmech_cd_mult``, a ``table``
        composes ``srmech_algebra_table_product``. NO new C symbol — the
        commutator IS the composition, so a dedicated kernel would only re-spell
        ``a·b`` twice (``composition_of_c``, exactly as :func:`associator`).
        Class C (operand-order which-way) ∘ M (bilinear bind) ∘ K (sign-flip
        difference; no ``abs()``).

    Canonical SSoT:
    - Baez, J.C. (2002), *The Octonions*, Bull. AMS **39** 145–205,
      arXiv:math/0105155, §2 — the Cayley–Dickson ladder and where
      commutativity (ℂ→ℍ) and associativity (ℍ→𝕆) are each lost.
    """
    ex = tuple(_coerce_frac(v) for v in x)
    ey = tuple(_coerce_frac(v) for v in y)
    if len(ex) != len(ey):
        raise ValueError(
            f"cd_commutator: the two operands must share dimension; got "
            f"{len(ex)} and {len(ey)}")
    if table is None:
        ex, ey = _as_elem(ex), _as_elem(ey)
        left = cd_mult(ex, ey)
        right = cd_mult(ey, ex)
    else:
        tbl = _structure_table(table)
        if len(tbl) != len(ex):
            raise ValueError(
                f"cd_commutator: the table is dim {len(tbl)}; got operands of "
                f"length {len(ex)}")
        left = table_product(tbl, ex, ey)
        right = table_product(tbl, ey, ex)
    return tuple(a - b for a, b in zip(left, right))


def cd_cycle_holonomy(x: Sequence[Any], y: Sequence[Any], z: Sequence[Any],
                      table: Any = None) -> Dict[str, Any]:
    """The loop-holonomy accumulated around a **3-cycle** of Cayley–Dickson
    edges — the general-dim, any-rung peer of
    :func:`srmech.physics.qm.quaternion.quaternion_cycle_holonomy` (rc380, `#T1055`).

    A directed triangle ``0 →ˣ 1 →ʸ 2 →ᶻ 0`` carries a CD gain on each edge; the
    holonomy is the ordered product walked around the loop back to base. Where
    the algebra is ASSOCIATIVE (ℝ / ℂ / ℍ) that walk is a single well-defined
    value — the loop CLOSES independently of how the three edges are bracketed —
    so the quaternion peer, which lives at ℍ, never has to choose. Past the
    Hurwitz wall at 𝕆 it does: the two bracketings of the same walk disagree, and
    that disagreement IS the holonomy the triangle now carries. So this op walks
    the loop BOTH ways and returns the pair plus their defect::

        holonomy_left  = (x·y)·z     the left-nested walk around the triangle
        holonomy_right = x·(y·z)     the right-nested walk
        defect         = holonomy_left − holonomy_right   ( = associator(x,y,z) )
        closed         = (defect is the all-zero tuple)

    ``closed`` is the turn-on read, and it is a property of the RUNG, not of the
    particular gains: on an associative rung EVERY triangle closes, and at 𝕆 the
    basis triangles fail to close on exactly the non-associating triples
    (168 / 512 at 𝕆, 1848 / 4096 at 𝕊). This is the k=3 loop defect made a
    holonomy; :func:`associator` is the same defect as a bare trilinear tuple,
    :func:`cd_commutator` is the k=2 square-loop one rung below.

    ⚠️ EPISTEMIC CEILING (`[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`):
    this reads the FORM of a 3-cycle holonomy over the CD carrier — the ordered
    triangle walk and whether it closes. It does not classify the holonomy into
    SU(2)-style conjugacy classes the way the ℍ-only quaternion peer can (that
    read is a scalar-part level set special to unit quaternions); the general CD
    rung has no single such invariant, so only the bracketing-defect / ``closed``
    read is claimed here.

    Args:
        x, y, z: the three directed edge-gains, equal-length elements. With
            ``table=None`` the length must be a power of two ``≤ CD_MAX_DIM`` (the
            definite ladder, via :func:`cd_mult`); with a ``table`` the length
            must be ``len(table)`` (via :func:`table_product`). Every
            exact-rational scalar :func:`cd_mult` accepts is accepted here.
        table: an optional rank-3 structure-constant tensor —
            :func:`algebra_table` (the definite ladder, or a split γ-twist), or
            any table :func:`table_product` reads. ``None`` — the default — is
            the definite Cayley–Dickson ladder ℝ→ℂ→ℍ→𝕆→𝕊…

    Returns:
        ``dict`` with ``dim`` (int), ``holonomy_left`` / ``holonomy_right`` /
        ``defect`` (each a ``dim``-tuple of exact :class:`~srmech.math.q.Q`), and
        ``closed`` (bool — the loop is bracketing-independent ⟺ the defect
        vanishes; always ``True`` on an associative rung).

    Raises:
        ValueError: operands of unequal length; a non-power-of-two length when
            ``table is None``; a ``table`` whose dim disagrees with the operands.

    Note:
        Exact end to end — no float, no epsilon, no ``abs()``. Both walks compose
        the same C-backed products :func:`associator` uses (``srmech_cd_mult`` /
        ``srmech_algebra_table_product``); NO new C symbol (``composition_of_c``).
        Class M (bilinear bind) ∘ C (loop orientation) ∘ K (sign-flip defect; no
        ``abs()``).

    Canonical SSoT:
    - Schafer, R.D. (1966), *An Introduction to Nonassociative Algebras*,
      **ch. II eqn (11)** — the associator as the trilinear defect measuring
      departure from associativity.
    - Baez, J.C. (2002), *The Octonions*, Bull. AMS **39** 145–205,
      arXiv:math/0105155, §1–§2 — associativity is lost only at ℍ→𝕆.
    """
    ex = tuple(_coerce_frac(v) for v in x)
    ey = tuple(_coerce_frac(v) for v in y)
    ez = tuple(_coerce_frac(v) for v in z)
    if not (len(ex) == len(ey) == len(ez)):
        raise ValueError(
            f"cd_cycle_holonomy: the three edge-gains must share dimension; got "
            f"{len(ex)}, {len(ey)} and {len(ez)}")
    if table is None:
        ex, ey, ez = _as_elem(ex), _as_elem(ey), _as_elem(ez)
        left = cd_mult(cd_mult(ex, ey), ez)
        right = cd_mult(ex, cd_mult(ey, ez))
    else:
        tbl = _structure_table(table)
        if len(tbl) != len(ex):
            raise ValueError(
                f"cd_cycle_holonomy: the table is dim {len(tbl)}; got operands "
                f"of length {len(ex)}")
        left = table_product(tbl, table_product(tbl, ex, ey), ez)
        right = table_product(tbl, ex, table_product(tbl, ey, ez))
    defect = tuple(a - b for a, b in zip(left, right))
    return {
        "dim": len(ex),
        "holonomy_left": tuple(left),
        "holonomy_right": tuple(right),
        "defect": defect,
        "closed": all(v == 0 for v in defect),
    }


def cd_three_form(x: Sequence[Any], y: Sequence[Any], z: Sequence[Any],
                  *, table: Any = None) -> Q:
    """The G₂ ASSOCIATIVE 3-FORM ``φ(x, y, z) = Re(x̄·(y·z))``, a scalar, exact ℚ,
    any rung (rc386, `#T1062`) — the regrouping-INVARIANT SCALAR twin of the
    vector :func:`associator`.

    Where :func:`associator` is the pure-IMAGINARY associativity DEFECT
    ``(x·y)·z − x·(y·z)`` (the part regrouping DOES move), this reads the
    complementary REAL shadow that regrouping does NOT move. ``Re(associator)``
    is identically 0, so::

        φ(x, y, z) = Re(x̄·(y·z)) = Re((x̄·y)·z)   — the two bracketings agree

    is the single regrouping-safe scalar both ``(x̄·y)·z`` and ``x̄·(y·z)`` share.
    Equivalently ``φ(x, y, z) = ⟨x, y·z⟩`` — the exact Euclidean inner product of
    ``x`` with the product ``y·z`` (``Re(x̄·w) = Σ x_i·w_i``).

    On the IMAGINARY octonions ``Im 𝕆 = ℝ⁷`` this is exactly the Harvey–Lawson
    associative calibration 3-form ``⟨x, y × z⟩`` (the scalar triple product on
    the 7-D cross product ``cross7``): fully antisymmetric, ``±1`` on precisely
    the 7 Fano associative 3-planes and 0 on the other 28 of the ``C(7,3)=35``
    basis triples::

        {123, 145, 246, 257, 347} = +1        {167, 356} = −1

    — MEASURED through this op, reproducing the shipped FLOAT peer
    :func:`srmech.math.hdc.g2_three_form` bit-for-bit on all 35 unordered (and
    343 ordered) imaginary basis triples. It is the exact-ℚ companion to that
    float form; the sign / orientation convention is the one the Cayley–Dickson
    product itself fixes (not imposed externally), and ``stab(φ) = G₂ = Der(𝕆)``
    — every :func:`srmech.physics.qm.so8.g2_subalgebra` derivation annihilates it.

    Args:
        x, y, z: equal-length elements. With ``table=None`` the length must be a
            power of two ``≤ CD_MAX_DIM`` (the definite ladder, via
            :func:`cd_mult`); with a ``table`` the length must be ``len(table)``
            (via :func:`table_product`). Every exact-rational scalar
            :func:`cd_mult` accepts is accepted here.
        table: an optional dim × dim × dim structure-constant tensor —
            :func:`algebra_table` (the definite ladder, or a split γ-twist when
            ``gammas=`` is given: the STRUCTURED negative control), or any table
            :func:`table_product` reads. ``None`` — the default — is the definite
            Cayley–Dickson ladder ℝ→ℂ→ℍ→𝕆→𝕊…  Conjugation is table-independent
            (it only negates the imaginary part), so only the two products follow
            the table.

    Returns:
        A single exact :class:`~srmech.math.q.Q` — the scalar ``φ(x, y, z)``.

    Raises:
        ValueError: operands of unequal length; a non-power-of-two length when
            ``table is None``; a ``table`` whose dim disagrees with the operands.

    Note:
        Exact end to end — no float, no epsilon, no ``abs()``. NO new C symbol:
        φ IS the composition ``Re(cd_conjugate(x) · cd_mult(y, z))``, so a
        dedicated kernel would only re-spell ``a·b`` and a conjugation already in
        the library — ``composition_of_c`` over the c_dispatched
        ``srmech_cd_mult`` / ``srmech_cd_qconjugate`` (or
        ``srmech_algebra_table_product`` with a ``table``). Class M (bilinear
        bind) ∘ C (conjugation which-way), then a real-part read (the e₀ scalar
        component). It is the Re-companion to :func:`associator`'s Im defect.

    Canonical SSoT:
    - Harvey, R. & Lawson, H.B. (1982), *Calibrated geometries*, Acta Math.
      **148** 47–157 — the associative calibration 3-form φ on Im 𝕆 = ℝ⁷.
    - Baez, J.C. (2002), *The Octonions*, Bull. AMS **39** 145–205,
      arXiv:math/0105155, §4.1 — the associative 3-form ``φ(x,y,z) = ⟨x,yz⟩``
      on Im 𝕆 and G₂ = Aut(𝕆) as exactly the stabiliser of φ; §2.1 — the
      Fano-plane multiplication table φ takes its values on.

    ⚠️ ATTESTATION FIX, rc428 (`#T1126`). Through rc427 this cited **§4.1**
    for "φ, its Fano-plane values and G₂ = Aut(𝕆)". The φ half and the G₂ half
    are correct — §4.1 states both verbatim — but **"Fano" occurs 0 times in
    §4.1**; the Fano plane is §2.1, which is where the multiplication table
    lives. One locator, two claims, one of them false: the citation was
    SPLIT rather than deleted, because deleting the Fano half would convert a
    mislocated citation into an unsourced claim, which is a change of defect
    class and not a fix. Positive control on the same extraction: "Cayley–
    Dickson" occurs 22× in that paper (18 en-dash, 4 ASCII), so the zero is a
    measurement rather than silence. Found by
    ``tests/test_citation_manifest_rc428.py``.
    """
    ex = tuple(_coerce_frac(v) for v in x)
    ey = tuple(_coerce_frac(v) for v in y)
    ez = tuple(_coerce_frac(v) for v in z)
    if not (len(ex) == len(ey) == len(ez)):
        raise ValueError(
            f"cd_three_form: the three operands must share dimension; got "
            f"{len(ex)}, {len(ey)} and {len(ez)}")
    if table is None:
        ex, ey, ez = _as_elem(ex), _as_elem(ey), _as_elem(ez)
        yz = cd_mult(ey, ez)
        w = cd_mult(cd_conjugate(ex), yz)
    else:
        tbl = _structure_table(table)
        if len(tbl) != len(ex):
            raise ValueError(
                f"cd_three_form: the table is dim {len(tbl)}; got operands of "
                f"length {len(ex)}")
        yz = table_product(tbl, ey, ez)
        w = table_product(tbl, cd_conjugate(ex), yz)
    return w[0]


#: The Cayley–Dickson property-loss ladder, RUNG-indexed (rc383, `#T1054`).
#: Maps each loop-defect NAME :func:`defect_ladder` returns to the CD doubling
#: rung at which the corresponding property first turns off — each one rung
#: LATER than the last. ``None`` is the FLOOR (``flexibility`` — ``[x,y,x]`` is
#: structurally zero at every rung, so it never turns on). Read by
#: :func:`_defect_admitted`, the per-rung projector mask.
#:
#: NOTE the rung is the CD DOUBLING DEPTH (``dim.bit_length() - 1``): ℝ=0, ℂ=1,
#: ℍ=2, 𝕆=3, 𝕊=4. The ``left_alternator`` turn-on at rung 4 (𝕊) is **not
#: basis-visible** — see :func:`defect_ladder`'s docstring for the seam-crossing
#: crux.
_DEFECT_TURN_ON_RUNG: Dict[str, Any] = {
    "commutator": 2,        # COMMUTATIVITY lost at ℍ (rung 2)
    "associator": 3,        # ASSOCIATIVITY lost at 𝕆 (rung 3)
    "left_alternator": 4,   # ALTERNATIVITY + ZERO-DIVISORS lost at 𝕊 (rung 4)
    "flexibility": None,    # FLOOR — [x,y,x] = 0 never turns on
}


def _defect_admitted(name: str, rung: int) -> bool:
    """Is the named loop-defect STRUCTURALLY meaningful at this CD ``rung``? —
    the per-rung projector mask behind :func:`defect_ladder`.

    A defect is admitted iff it turns on at or below ``rung``
    (:data:`_DEFECT_TURN_ON_RUNG`). The FLOOR (``flexibility``, turn-on
    ``None``) is NEVER admitted — it is structurally zero at every rung, so it
    is never part of the "meaningful subset" the projector returns. Pure
    integer comparison; no ``abs()``.
    """
    turn_on = _DEFECT_TURN_ON_RUNG[name]
    return turn_on is not None and rung >= turn_on


def defect_ladder(x: Sequence[Any], y: Sequence[Any], z: Sequence[Any],
                  table: Any = None) -> Dict[str, Any]:
    """The Cayley–Dickson property-loss ladder read as ONE parallel pass plus a
    per-rung PROJECTOR (rc383, `#T1054`) — the composition that names, in a
    single call over the SAME three inputs, which algebraic property each rung of
    ℝ→ℂ→ℍ→𝕆→𝕊… has already lost, and returns ONLY the loop-defects that are
    MEANINGFUL at the operands' rung.

    The property loss is **RUNG-indexed, not arity-indexed**: each defect turns
    on exactly one doubling LATER than the last, and each is a loop of a
    different order measured in parallel here::

        property lost         turn-on rung   this op's field        basis-visible?
        TOTAL ORDER           1  (ℂ)         — (admits flag only)   n/a (metric)
        COMMUTATIVITY         2  (ℍ)         commutator   [x,y]     yes
        ASSOCIATIVITY         3  (𝕆)         associator   [x,y,z]   yes
        ALTERNATIVITY /       4  (𝕊)         left_alternator [x,x,y] NO — seam-only
          ZERO-DIVISORS
        FLEXIBILITY (floor)   never          flexibility  [x,y,x]≡0 —

    **The parallel read + projector.** Every rung's defect is computed on the
    one call — :func:`cd_commutator` ``[x,y]``, :func:`associator` ``[x,y,z]``,
    the left alternator ``[x,x,y]`` and the flexibility floor ``[x,y,x]``, plus
    the :func:`cd_cycle_holonomy` closed-read — so the whole ladder is present at
    once (the "declared parallel eq-set"). The ``rung_admits`` mask and the
    ``projected`` view are the PROJECTOR: given the operands' rung they select
    the subset of defects that can be structurally nonzero there, masking the
    ones that are zero by rung alone. This is the general instrument —
    *declared-parallel-state ⊗ projector-excitation → the rung-meaningful
    subset* — with the CD rung playing the projector; see the srmech notebook
    §3.29 for the QM-measurement / genome-chromatin / music-fingerboard peers
    that instantiate the SAME instrument-FORM in other domains.

    **RUNG 4 IS NOT BASIS-VISIBLE — the 𝕊 seam-crossing crux.** Alternativity
    and the zero-divisors both first fail at the sedenions (dim 16, rung 4), but
    NOT on any single basis triple: over the ordered basis the alternator
    ``[e_i, e_i, e_j]`` is identically zero at 𝕊 just as it is at 𝕆, so a
    basis-only probe FALSELY reports 𝕊 as alternative. The failure needs
    DOUBLING-SEAM-CROSSING inputs — an element spanning both halves of the last
    doubling, e.g. ``a = e1 + e10``: then ``[a, a, e4] = 2·e15 ≠ 0`` and
    ``(e1 + e10)(e4 − e15) = 0`` (a genuine zero divisor). So to see rung 4
    turn on you must FEED the op a seam-crosser (pass ``x = y = e1 + e10``,
    ``z = e4``); the returned ``associator`` field then carries ``2·e15`` and
    ``rung_admits["alt_zero_div@4"]`` is ``True``. Zero-divisor / composition
    loss is the cleaner NAME for this rung than "alternativity"; the two arrive
    together at the same seam.

    **Arity-4 was REFUTED.** A conjectured arity-4 "square-loop" holonomy does
    NOT open a fifth, arity-indexed rung: it turns on at 𝕆 (rung 3) with the
    same 1848/4096 count as the associator and is INHERITED from it, not a new
    property. The ladder is rung-indexed; there is no arity-4 rung.

    ⚠️ EPISTEMIC CEILING — FORM, not identity
    (`[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`). The
    ``k=3`` here is the **arity-3 associator** of the Hurwitz/Cayley–Dickson
    construction. It MUST NOT be fused with CLAUDE.md's substrate signature
    "every catalogued k=3 is a B/H/N language-translation event" — those are
    DIFFERENT k=3's. This op reads the FORM of the loop-defect ladder over the
    CD carrier; it makes no claim that the CD k=3 and the substrate k=3 are the
    same object. Cross-substrate reading transfers the ALGORITHM (the
    parallel-declared ⊗ projector instrument), never the constant.

    Args:
        x, y, z: equal-length elements. With ``table=None`` the length must be a
            power of two ``≤ CD_MAX_DIM`` (the definite ladder, via
            :func:`cd_mult`); with a ``table`` the length must be
            ``len(table)``. Every exact-rational scalar :func:`cd_mult` accepts
            is accepted here.
        table: an optional rank-3 structure-constant tensor —
            :func:`algebra_table` (the definite ladder, or a split γ-twist:
            the STRUCTURED negative control), or any table :func:`table_product`
            reads. ``None`` — the default — is the definite Cayley–Dickson
            ladder ℝ→ℂ→ℍ→𝕆→𝕊…

    Returns:
        ``dict`` with:

        * ``dim`` (int) and ``rung`` (int, the CD doubling depth
          ``dim.bit_length() - 1``) and ``algebra`` (the human rung name);
        * ``defects`` — the four loop-defect tuples in ONE call
          (``commutator`` ``[x,y]``, ``associator`` ``[x,y,z]``,
          ``left_alternator`` ``[x,x,y]``, ``flexibility`` ``[x,y,x]``), each a
          ``dim``-tuple of exact :class:`~srmech.math.q.Q`;
        * ``nonzero`` — ``{name: bool}``, whether each defect is nonzero for
          THESE operands;
        * ``holonomy_closed`` (bool) — the :func:`cd_cycle_holonomy` ``closed``
          read of the ``x → y → z`` triangle;
        * ``rung_admits`` — the STRUCTURAL projector mask
          ``{"order@1", "commutativity@2", "associativity@3",
          "alt_zero_div@4"}`` → bool, purely a function of the rung;
        * ``projected`` — the projector VIEW: only the ``defects`` that are
          rung-admitted (structurally able to be nonzero at this rung), i.e.
          "the values meaningful to the projection space".

    Raises:
        ValueError: operands of unequal length; a non-power-of-two length when
            ``table is None``; a ``table`` whose dim disagrees with the operands
            (surfaced by the composed :func:`cd_commutator` / :func:`associator`
            / :func:`cd_cycle_holonomy`).

    Note:
        Exact end to end — no float, no epsilon, no ``abs()`` (sign is the
        Class-K pin-slot; operand-order which-way is Class C). ``composition_of_c``:
        it composes the already-C-backed :func:`associator`,
        :func:`cd_commutator` and :func:`cd_cycle_holonomy` (which in turn ride
        ``srmech_cd_mult`` / ``srmech_algebra_table_product``); NO new C symbol,
        so ``SRMECH_ABI_VERSION`` is unchanged. Class M (bilinear bind) ∘ C
        (operand-order / loop orientation) ∘ K (sign-flip defect).

    Canonical SSoT:
    - Schafer, R.D. (1966), *An Introduction to Nonassociative Algebras*,
      **ch. II eqn (11)** — the associator ``(x, y, z)``; **ch. III eqns
      (1)–(2)** the alternative laws, and **(6′)** flexibility as the identity
      ``(xy)x = x(yx)``, i.e. ``(x, y, x) = 0``, that survives every rung.
    - Baez, J.C. (2002), *The Octonions*, Bull. AMS **39** 145–205,
      arXiv:math/0105155, §1–§2 — commutativity lost at ℂ→ℍ, associativity at
      ℍ→𝕆, alternativity + the division property at 𝕆→𝕊.
    """
    dim = len(x)
    rung = dim.bit_length() - 1
    comm = cd_commutator(x, y, table=table)
    assoc = associator(x, y, z, table=table)
    flex = associator(x, y, x, table=table)          # flexibility FLOOR [x,y,x]
    left_alt = associator(x, x, y, table=table)       # left alternator [x,x,y]
    holo = cd_cycle_holonomy(x, y, z, table=table)
    defects = {
        "commutator": comm,
        "associator": assoc,
        "flexibility": flex,
        "left_alternator": left_alt,
    }
    nonzero = {k: not all(v == 0 for v in t) for k, t in defects.items()}
    rung_admits = {
        "order@1": rung >= 1,
        "commutativity@2": rung >= 2,
        "associativity@3": rung >= 3,
        "alt_zero_div@4": rung >= 4,
    }
    # PROJECTOR: keep only the defects meaningful at this rung (mask the ones
    # structurally zero by rung alone; the flexibility floor is never admitted).
    projected = {k: defects[k] for k in defects if _defect_admitted(k, rung)}
    return {
        "dim": dim,
        "rung": rung,
        "algebra": ALGEBRA_NAMES.get(dim, f"(dim {dim})"),
        "defects": defects,
        "nonzero": nonzero,
        "holonomy_closed": holo["closed"],
        "rung_admits": rung_admits,
        "projected": projected,
    }


#: The Cayley–Dickson doubling seam for the octonions — ``ℓ = e₄``. The default
#: splitting unit of :func:`octonion_frame_read`: 𝕆 = ℍ ⊕ ℍℓ with the ℍ base
#: ``{e₀, e₁, e₂, e₃}`` and the seam half ``{e₄, e₅, e₆, e₇}``.
OCTONION_FRAME_SEAM = 4

#: The Fano line whose ℍ subalgebra is the DEFAULT base of
#: :func:`octonion_frame_read` — ``span{e₀, e₁, e₂, e₃}``. A bare-``int``
#: ``frame=`` names a splitting unit on THIS line; the explicit
#: ``(i, j, k, ℓ)`` form selects another of the seven.
OCTONION_FRAME_LINE = (1, 2, 3)

#: How many well-posed frames 𝕆 admits — **MEASURED**, not asserted (rc421,
#: `#T1122`; ``docs/srmech/notes/octonion_frame_ell_within_line_rc421.py``):
#: **7** Fano lines × **4** valid splitting units each. All 28 reads of one
#: generic octonion are DISTINCT, so the frame is the ``(line, ℓ)`` **pair**,
#: not the line. (Contrast rc388's 28 seams, which DO collapse to 7 — that
#: count is over the seam *set*, and ``T`` is always ``H``'s set-complement.
#: ``ℓ`` fixes the seam half's *identification* with ℍ, ``x = q₀ + q₁·ℓ``, not
#: merely its span, which is why the READ does not collapse with the SET.)
OCTONION_FRAME_COUNT = 28


def _octonion_fano_lines() -> Tuple[Tuple[int, ...], ...]:
    """The 7 Fano lines of 𝕆, DERIVED from :func:`cd_basis_product`.

    Each line ``(i, j, k)`` is a triple of imaginary units closed under
    multiplication, so ``span{e₀, e_i, e_j, e_k}`` is an ℍ subalgebra. Nothing
    is tabulated: the lines are read off srmech's own cocycle, so if the
    multiplication table ever moved, these would move with it rather than
    silently disagreeing. Used only to ENUMERATE the seven in an error message —
    the fast path decides membership with a single product.
    """
    lines: Set[Tuple[int, ...]] = set()
    for i in range(1, 8):
        for j in range(i + 1, 8):
            index, _sign = cd_basis_product(8, i, j)
            if index != 0:
                lines.add(tuple(sorted((i, j, index))))
    return tuple(sorted(lines))


def _frame_embed(base: Sequence[int], p: Sequence[Q]) -> Tuple[Q, ...]:
    """Lift a 4-vector in the frame's base coordinates to a full 8-vector 𝕆."""
    x = [Q(0, 1)] * 8
    for slot, b in enumerate(base):
        x[b] = p[slot]
    return tuple(x)


def _frame_extract(base: Sequence[int], x: Sequence[Q]) -> Tuple[Q, ...]:
    """Read the frame's base coordinates back out of a full 8-vector 𝕆."""
    return tuple(x[b] for b in base)


def _frame_h_mult(base: Sequence[int], p: Sequence[Q],
                  q: Sequence[Q]) -> Tuple[Q, ...]:
    """The frame's ℍ product — :func:`cd_mult` itself, restricted to the base.

    Deliberately NOT a 4-vector `cd_mult` on the base coordinates: that would
    silently assume ``e_i·e_j = +e_k`` for the *sorted* line, which is a
    convention this module refuses to hard-code. Embedding into 𝕆 and
    extracting makes the structure constants — signs included — come from
    :func:`cd_mult`. On the default base ``(0,1,2,3)`` the two agree exactly,
    because ``(a,0)·(b,0) = (ab,0)`` under Cayley–Dickson doubling.
    """
    return _frame_extract(base, cd_mult(_frame_embed(base, p),
                                        _frame_embed(base, q)))


def _frame_h_conj(base: Sequence[int], p: Sequence[Q]) -> Tuple[Q, ...]:
    """The frame's ℍ conjugation — :func:`cd_conjugate` restricted to the base."""
    return _frame_extract(base, cd_conjugate(_frame_embed(base, p)))


def _octonion_frame_spec(frame: Any) -> Dict[str, Any]:
    """Resolve a ``frame=`` argument to its ``(base, ℓ, seam, chart)`` split.

    Accepts either form :func:`octonion_frame_read` documents — a bare ``int``
    (a splitting unit on the default line :data:`OCTONION_FRAME_LINE`) or an
    explicit 4-sequence ``(i, j, k, ℓ)``. Everything is derived from
    :func:`cd_basis_product`; every rejection says WHY the input is not a
    well-posed frame, and what to pass instead.
    """
    # ── shape: which of the two spellings is this? ────────────────────────
    if isinstance(frame, bool):     # bool is an int subclass; never a frame
        raise ValueError(
            "octonion_frame_read: frame must be an int (a splitting unit on "
            f"the default Fano line {OCTONION_FRAME_LINE}) or a 4-sequence "
            "(i, j, k, ℓ) naming a line and its splitting unit; got a bool.")
    if isinstance(frame, int):
        line, ell = tuple(OCTONION_FRAME_LINE), int(frame)
        spelling = "int"
    else:
        if isinstance(frame, (str, bytes, bytearray)):
            # A str IS iterable, and "1234" would otherwise coerce to a valid
            # 4-sequence — a text frame must never be read as basis indices.
            raise ValueError(
                "octonion_frame_read: frame must be an int (a splitting unit "
                f"on the default Fano line {OCTONION_FRAME_LINE}) or a "
                "4-sequence (i, j, k, ℓ) naming a Fano line and its splitting "
                f"unit; got the text value {frame!r}. Basis indices are ints, "
                "not characters.")
        try:
            raw = list(frame)
            items = [int(v) for v in raw]
        except (TypeError, ValueError):
            raise ValueError(
                "octonion_frame_read: frame must be an int (a splitting unit "
                f"on the default Fano line {OCTONION_FRAME_LINE}) or a "
                "4-sequence (i, j, k, ℓ) naming a Fano line and its splitting "
                f"unit; got {frame!r}, whose entries are not all basis "
                "indices.") from None
        # A basis index is an INTEGER. Truncating 1.5 → 1 would hand back a
        # perfectly well-formed read of a frame the caller never asked for.
        if any(a != b for a, b in zip(items, raw)):
            raise ValueError(
                "octonion_frame_read: frame entries must be exact basis "
                f"indices, but {frame!r} carries a non-integral value. A basis "
                "index names a unit e_k, so it is never rounded or truncated.")
        if len(items) != 4:
            raise ValueError(
                "octonion_frame_read: an explicit frame is the 4-sequence "
                "(i, j, k, ℓ) — the three imaginary units of a Fano line, then "
                f"the splitting unit — but got length {len(items)}: "
                f"{items!r}. 𝕆 admits {OCTONION_FRAME_COUNT} well-posed frames "
                f"({len(_octonion_fano_lines())} lines × 4 splitting units).")
        line, ell = tuple(items[:3]), items[3]
        spelling = "tuple"

    # ── the line: three DISTINCT imaginary units, closed under cd_mult ────
    if len(set(line)) != 3 or any(not (1 <= v <= 7) for v in line):
        raise ValueError(
            f"octonion_frame_read: frame line {tuple(line)} is not three "
            "distinct IMAGINARY basis indices in [1, 7]. e₀ is the real unit "
            "and belongs to every ℍ base, so it is never named in the line. "
            f"The {len(_octonion_fano_lines())} Fano lines of this "
            f"multiplication table are {_octonion_fano_lines()}.")
    i, j, k = sorted(line)
    index, _sign = cd_basis_product(8, i, j)
    if index != k:
        raise ValueError(
            f"octonion_frame_read: frame line {tuple(sorted(line))} is not a "
            f"Fano line of this multiplication table — cd_mult gives "
            f"e{i}·e{j} = ±e{index}, not ±e{k}, so span{{e₀, e{i}, e{j}, e{k}}} "
            "is NOT closed and is not an ℍ subalgebra. The "
            f"{len(_octonion_fano_lines())} lines of this table are "
            f"{_octonion_fano_lines()} (derived from cd_basis_product, not "
            "tabulated).")
    base = (0, i, j, k)
    seam = tuple(m for m in range(1, 8) if m not in base)

    # ── the splitting unit: an imaginary unit OUTSIDE the base ────────────
    if not (0 <= ell <= 7):
        raise ValueError(
            f"octonion_frame_read: splitting unit ℓ = e{ell} is not a basis "
            "index of 𝕆; expected 1 ≤ ℓ ≤ 7.")
    if ell == 0:
        raise ValueError(
            "octonion_frame_read: frame=0 names e₀, the REAL unit. e₀ lies in "
            "every ℍ base, so 𝕆 = ℍ ⊕ ℍe₀ is not a splitting — ℍe₀ is ℍ "
            f"itself. The splitting unit must be one of this frame's seam "
            f"units {seam}.")
    if ell in base:
        if spelling == "int":
            raise ValueError(
                f"octonion_frame_read: frame={ell} — e{ell} lies INSIDE the ℍ "
                f"base {{e0, e{i}, e{j}, e{k}}} of the default Fano line "
                f"{OCTONION_FRAME_LINE}, so it cannot split 𝕆 = ℍ ⊕ ℍℓ (ℍℓ "
                "would re-enter the base). The bare-int spelling always uses "
                "that base; its four valid splitting units are "
                f"{seam}. To put e{ell} in the SEAM instead, name a line that "
                "does not contain it with the explicit 4-sequence spelling, "
                f"e.g. frame=({_a_line_without(ell)}, {ell}). 𝕆 admits "
                f"{OCTONION_FRAME_COUNT} well-posed frames in all "
                f"({len(_octonion_fano_lines())} lines × 4 splitting units).")
        raise ValueError(
            f"octonion_frame_read: frame=({i}, {j}, {k}, {ell}) — the "
            f"splitting unit e{ell} lies INSIDE its own ℍ base "
            f"{{e0, e{i}, e{j}, e{k}}}, so 𝕆 = ℍ ⊕ ℍℓ is not a splitting (ℍℓ "
            f"would re-enter the base). This line's four valid splitting units "
            f"are {seam}.")

    # ── the chart: e_m = s·e_σ(m)·e_ℓ, read off cd_basis_product ──────────
    # Class K reads the pin-slot sign off the product; Class C re-applies it
    # onto the coefficient. No abs() — the sign is a carried channel.
    chart: List[Tuple[int, int, int]] = []
    reached: Set[int] = set()
    for b in base:
        index, sign = cd_basis_product(8, b, ell)
        chart.append((index, b, sign))
        reached.add(index)
    if reached != set(seam):
        raise ValueError(
            f"octonion_frame_read: frame=({i}, {j}, {k}, {ell}) — e{ell} does "
            f"not carry the ℍ base ONTO the seam {seam}; the base·e{ell} "
            f"images are {tuple(sorted(reached))}, so 𝕆 = ℍ ⊕ ℍℓ is not a "
            "splitting of 𝕆 into two ℍ halves.")
    chart.sort()
    return {"base": base, "ell": ell, "seam": seam,
            "chart": tuple(chart), "line": (i, j, k)}


def _a_line_without(ell: int) -> str:
    """A Fano line not containing ``e_ell`` — for the 'pass this instead' hint."""
    for cand in _octonion_fano_lines():
        if ell not in cand:
            return ", ".join(str(v) for v in cand)
    return "i, j, k"    # unreachable for 𝕆: every unit misses 4 of the 7 lines


def octonion_frame_read(x: Sequence[Any], *,
                        frame: "int | Sequence[int]" = 4) -> Dict[str, Any]:
    """Read an octonion on a COMMITTED frame as a frame-free quaternionic-Hopf
    base ⊕ an ℍ-valued writhe — the FRAME-COMMITTED coherence read of 𝕆 (rc384,
    `#T957`).

    §3.41 measured that 𝕆 has "no FRAME-FREE invariant" (F1301/F1302) — but that
    is an **ℝ-SCALAR** question asked of a rung whose coherence is **ℍ-shaped**.
    MEASURED (this op's generating script,
    ``docs/srmech/notes/octonion_frame_read_rc384.py``): ``{e₀, e₁, e₂, e₃}`` is
    a genuine ℍ subalgebra of 𝕆 and is FULLY coherent — ``0`` of its ``64``
    ordered basis-triple associators is nonzero — while ALL ``168`` of the
    octonion's nonzero associators (of ``512`` ordered basis triples) CROSS the
    doubling seam ``ℍℓ = {e₄, e₅, e₆, e₇}`` (``0`` non-seam nonzero). So 𝕆's
    coherence is **frame-COMMITTED**: pick a splitting unit ``ℓ`` and
    ``𝕆 = ℍ ⊕ ℍℓ`` splits into a coherent ℍ base and the seam that carries every
    non-closure. The geometry is the **quaternionic Hopf fibration**
    ``S³ ↪ S⁷ ↠ S⁴`` — read 𝕆 = ``(q₀, q₁) ∈ ℍ²`` as a point of the frame-free
    base ``ℍP¹ ≅ S⁴`` plus the ``S³`` fiber it sits over.

    **There are 28 frames, and the count was MEASURED** (rc421, `#T1122`;
    ``docs/srmech/notes/octonion_frame_{seven_frames,generalised_read,
    ell_within_line}_rc421.py``). Through rc420 this op accepted only
    ``frame=4``, on the argument that ``e₁/e₂/e₃`` lie inside the ℍ base and
    ``e₅/e₆/e₇`` "are not independent seam generators". The first half is right;
    **the conclusion was not** — measured against ``cd_mult``, the standard base
    ``{e₀,e₁,e₂,e₃}`` admits **four** valid splitting units ``{e₄,e₅,e₆,e₇}``,
    not one. And a frame is properly a choice of ℍ *subalgebra*, of which 𝕆 has
    **seven** (one per Fano line), each with four valid ``ℓ``:

    * all seven bases are closed under ``cd_mult``, and all ``64`` ordered
      base-triple associators vanish for each (they are genuinely associative,
      not merely closed);
    * the four ``ℓ`` of a line do **not** agree — all ``7 × 4 = 28`` reads of one
      generic octonion are DISTINCT, so the frame is the ``(line, ℓ)`` **pair**;
    * within a line they are related by an exactly predictable **right action**:
      if ``e_ℓ' = u·e_ℓ`` for a signed base unit ``u``, then
      ``base_H' = base_H·u`` and ``canonical_affine' = canonical_affine·u``
      (``28/28`` each), a signed permutation of the four coordinates, while
      ``q₀``, ``base_R`` and ``norm_sq`` are ``ℓ``-INVARIANT;
    * ``norm_sq`` is shared by all 28 — the frame-independent scale.

    Do not confuse this 28 with rc388's ``oct_torsor_act`` 28, which DOES
    collapse to 7: that count is over the seam **set**, and ``T`` is always
    ``H``'s set-complement, so all four ``ℓ`` of a line share it. ``ℓ`` fixes the
    seam half's *identification* with ℍ (``x = q₀ + q₁·ℓ``), not merely its span
    — which is why the READ does not collapse with the SET.

    **The split, derived not tabulated.** For a frame with base
    ``{e₀, e_i, e_j, e_k}`` and splitting unit ``e_ℓ``, every seam unit satisfies
    ``e_m = s·e_σ(m)·e_ℓ`` for a unique base index ``σ(m)`` and sign
    ``s ∈ {+1,−1}``, so ``x = q₀ + q₁·ℓ`` with ``q₀`` the base part and ``q₁``
    the seam part pulled back along ``ℓ``. That signed permutation ``(σ, s)`` is
    read off :func:`cd_basis_product` — no Fano convention is hard-coded here —
    and it is returned as ``seam_chart``. On the default frame it is the
    identity, so ``q₀ = x[:4]`` and ``q₁ = x[4:]`` exactly as before.

    **The Hopf base — the coherent note, frame-FREE UNDER THE FIBER.** The
    quaternionic Hopf map sends ``(q₀, q₁)`` to the point of ``S⁴ ⊂ ℍ ⊕ ℝ``::

        base_H = 2·q₀·conj(q₁)         (4 comps, the ℍ off-diagonal)
        base_R = |q₀|² − |q₁|²          (1 scalar, the ℝ diagonal)

    Under the ``S³`` fiber — right-multiplication of BOTH halves by a UNIT
    quaternion ``λ`` (``|λ|² = 1``), ``(q₀, q₁) → (q₀·λ, q₁·λ)`` — the base is
    UNCHANGED (``2·(q₀λ)·conj(q₁λ) = 2·q₀·|λ|²·conj(q₁) = base_H``, using ℍ
    associativity and ``λ·conj(λ) = |λ|²``; likewise ``base_R``). That invariance
    IS the coherent note that survives once a frame is committed. It is
    NON-TAUTOLOGICAL: a NON-fiber move (e.g. right-multiplying only ``q₀``) DOES
    change the base — the instrument can return otherwise. The base lies on the
    radius-``|x|²`` four-sphere: ``|base_H|² + base_R² == norm_sq²`` exactly
    (``norm_sq = |q₀|² + |q₁|² = |x|²``).

    **The writhe — the S³ fiber DOF.** ``writhe`` is the fiber generator ``q₁``:
    its unit direction ``q₁/√|q₁|²`` is the ``S³`` fiber coordinate (relative to
    the "``q₁`` real-positive" section), carried UN-NORMALISED so the read stays
    exact-ℚ (normalisation would need a square root). Unlike the base, the writhe
    is EQUIVARIANT — it changes under the fiber (``q₁ → q₁·λ``) — which is exactly
    what makes it the fiber DOF rather than part of the invariant. The canonical
    fiber-FIXED representative is ``(canonical_affine, 1)`` where
    ``canonical_affine = q₀·q₁⁻¹`` (``q₁⁻¹ = conj(q₁)/|q₁|²``, exact-ℚ) — the
    inhomogeneous ``ℍP¹`` coordinate, itself frame-free-under-fiber. When
    ``q₁ == 0`` the fiber is degenerate (the ``ℍP¹`` point at infinity,
    ``base_R = +norm_sq``): ``writhe`` and ``canonical_affine`` are ``None``.

    ⚠️ **EPISTEMIC CEILING — this is the ℍ-shaped FRAME-COMMITTED read; it does
    NOT contradict §3.41.** §3.41's "no frame-free invariant" (F1301/F1302) is
    the **ℝ-SCALAR** statement, and it stands: there is no frame-free ℝ-scalar
    that is also a *gauge*-invariant — the companion :func:`octonion_laplacian`
    MEASURES that the octonion gain-Laplacian spectrum is NOT gauge-invariant at
    𝕆 (deviation ``~0.1``, versus ℍ's ``~1e-15`` Sp(1)-invariance). This op reads
    a DIFFERENT thing: the coherence that survives ONCE A FRAME IS COMMITTED
    (pick ``ℓ = e₄``), which is ℍ-VALUED, not an ℝ-scalar, and frame-free only
    UNDER THE FIBER, not under an arbitrary gauge. FORM, not identity
    (`[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`) — the
    quaternionic-Hopf ``S³/S⁴`` split is the FORM of 𝕆's frame-committed
    coherence; the op makes no claim that this ``S³`` and any other substrate's
    fiber are the same object.

    Args:
        x: An 8-vector octonion. Every exact-rational scalar :func:`cd_mult`
            accepts (``Q`` / ``int`` / ``float`` / ``Fraction`` / ``(num, den)``)
            is accepted; coerced to exact :class:`~srmech.math.q.Q`.
        frame: Which of the ``28`` well-posed frames to read on. Two spellings:

            * a bare **int** ``ℓ`` — the splitting unit, on the DEFAULT Fano
              line :data:`OCTONION_FRAME_LINE` = ``(1,2,3)`` (ℍ base
              ``{e₀,e₁,e₂,e₃}``). Valid: ``4, 5, 6, 7``. **The default ``4`` is
              the Cayley–Dickson doubling seam and is unchanged in meaning and
              in value.**
            * an explicit **4-sequence** ``(i, j, k, ℓ)`` — the three imaginary
              units of a Fano line, then its splitting unit. ``(1,2,3,4)`` is
              the default; ``(2,4,6,1)`` reads on a different ℍ subalgebra.

            Rejected with a message naming the specific defect: an ``ℓ`` inside
            its own base (``e₀`` always, and ``1/2/3`` under the bare-int
            spelling, which cannot change the base), a triple that is not a Fano
            line of this multiplication table, or an ``ℓ`` that fails to carry
            the base onto the seam.

    Returns:
        A ``dict`` with:

        * ``frame`` (int) — the splitting unit ``ℓ`` actually used (``4`` by
          default), and ``dim`` (int, ``8``);
        * ``base`` (4 ints, ``(0,1,2,3)`` by default) and ``seam`` (4 ints,
          ``(4,5,6,7)`` by default) — the basis indices of the two halves.
          ``frame`` alone cannot name one of 28 frames, so ``base`` is what
          makes the returned read self-describing; the pair ``(base, frame)``
          identifies the frame exactly;
        * ``seam_chart`` (4 triples ``(m, σ(m), s)``, ascending in ``m``) — the
          signed permutation ``e_m = s·e_σ(m)·e_ℓ`` the split was derived from.
          This is the channel the ``ℓ``-dependence lives in: within a line, it
          is the ONLY thing that changes;
        * ``q0`` / ``q1`` — the ℍ base half and the ℍℓ seam half, each a
          4-tuple of exact :class:`~srmech.math.q.Q`, in ``base`` order;
        * ``base_H`` (4 ``Q``) and ``base_R`` (``Q``) — the quaternionic-Hopf
          base, FRAME-FREE UNDER THE FIBER (the coherent note);
        * ``norm_sq`` (``Q``) — ``|q₀|² + |q₁|² = |x|²``; the base lies on the
          radius-``norm_sq`` ``S⁴`` (``|base_H|² + base_R² == norm_sq²``);
        * ``writhe`` (4 ``Q`` or ``None``) — the ``S³`` fiber generator ``q₁``,
          equivariant (changes under the fiber); ``None`` iff ``q₁ == 0``;
        * ``writhe_norm_sq`` (``Q``) — ``|q₁|²``, the exact scale (unit fiber =
          ``writhe / √writhe_norm_sq``);
        * ``canonical_affine`` (4 ``Q`` or ``None``) — ``q₀·q₁⁻¹``, the
          fiber-FIXED ``ℍP¹`` inhomogeneous coordinate; ``None`` iff ``q₁ == 0``.

    Raises:
        ValueError: ``x`` is not an 8-vector; ``frame`` is not one of the 28
            well-posed frames (see the ``frame`` argument for the four distinct
            rejection reasons, each named separately in the message).

    Note:
        Exact end to end — no float, no epsilon, no ``abs()`` (the ``base_R``
        sign is the Class-K pin-slot difference; the conjugation is Class C).
        ``composition_of_c``: it composes the already-C-backed :func:`cd_mult`
        (``srmech_cd_mult``), :func:`cd_conjugate` (``srmech_cd_qconjugate``) and
        :func:`cd_norm_sq`; NO new C symbol, so ``SRMECH_ABI_VERSION`` is
        unchanged. Class M (bilinear bind) ∘ C (conjugation / which-way) ∘ K
        (sign-flip difference).

    Canonical SSoT:
    - Baez, J.C. (2002), *The Octonions*, Bull. AMS **39** 145–205,
      arXiv:math/0105155, §2 — the Cayley–Dickson doubling ``𝕆 = ℍ ⊕ ℍℓ``, the
      octonion norm form, and the bimodule structure; §2.3 the associator whose
      seam-confinement (0/64 on the ℍ base, 168/168 seam-crossing) this op reads.
    - The quaternionic Hopf fibration ``S³ ↪ S⁷ ↠ S⁴`` (``ℍP¹ ≅ S⁴``) — the
      geometry of the ``(q₀, q₁) ∈ ℍ²`` doubling coordinate.
    """
    ex = _as_elem(tuple(_coerce_frac(v) for v in x))
    dim = len(ex)
    if dim != 8:
        raise ValueError(
            f"octonion_frame_read: x must be an 8-vector octonion; got "
            f"length {dim}")
    spec = _octonion_frame_spec(frame)
    base, ell = spec["base"], spec["ell"]
    seam, chart = spec["seam"], spec["chart"]
    # The split, DERIVED: q₀ is the base half; q₁ is the seam half pulled back
    # along ℓ, since e_m = s·e_σ(m)·e_ℓ ⟹ the coefficient of e_σ(m) in q₁ is
    # s·x_m. Class K reads the pin-slot sign off cd_basis_product, Class C
    # re-applies it — never abs().
    q0 = _frame_extract(base, ex)
    slots = [Q(0, 1)] * 4
    for m, b, sign in chart:
        slots[base.index(b)] = _reorient(ex[m], orientation=sign)
    q1 = tuple(slots)
    # The quaternionic Hopf base — frame-free UNDER the S³ fiber (the coherent
    # note). base_H is the ℍ off-diagonal 2·q₀·conj(q₁); base_R the ℝ diagonal
    # |q₀|² − |q₁|² (Class-K pin-slot difference; NO abs()).
    base_H = tuple(Q(2, 1) * c
                   for c in _frame_h_mult(base, q0, _frame_h_conj(base, q1)))
    n0 = cd_norm_sq(q0)
    n1 = cd_norm_sq(q1)
    base_R = n0 - n1
    norm_sq = n0 + n1
    # The S³ fiber generator (the writhe). Un-normalised to stay exact-ℚ; the
    # canonical fiber-fixed representative right-divides by q₁ (→ (q₀·q₁⁻¹, 1)).
    if all(v == 0 for v in q1):
        writhe: Any = None
        writhe_norm_sq = Q(0, 1)
        canonical_affine: Any = None
    else:
        writhe = q1
        writhe_norm_sq = n1
        inv1 = Q(1, 1) / writhe_norm_sq             # 1/|q₁|² (exact ℚ)
        q1_inv = tuple(c * inv1 for c in _frame_h_conj(base, q1))
        canonical_affine = _frame_h_mult(base, q0, q1_inv)
    return {
        "frame": ell,
        "dim": dim,
        "base": base,
        "seam": seam,
        "seam_chart": chart,
        "q0": q0,
        "q1": q1,
        "base_H": base_H,
        "base_R": base_R,
        "norm_sq": norm_sq,
        "writhe": writhe,
        "writhe_norm_sq": writhe_norm_sq,
        "canonical_affine": canonical_affine,
    }


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
# The octonion MOUFANG LOOP — rc398 (`#T1064`).
#
# 𝕆 is a Moufang loop, and srmech already ships that loop TWICE with C
# parity — this module's exact-ℚ Cayley–Dickson product and the float
# loop-bind family in ``srmech.math.hdc`` — but only as octonion
# ARITHMETIC. The three Moufang identities were proven ONLY inside
# ``tests/test_loop_bind_moufang.py``, the Mal'cev-not-Lie tangent fact
# likewise, and the 16-element unit loop M16 existed only as the DATA
# ``closure(8, [1..7])`` with no name and no invariants. The ops below
# promote that latent, proven machinery to first-class QUERYABLE checkers.
# They are exact-ℚ, table-generic siblings of :func:`associator` /
# :func:`cd_commutator`: each is a composition of the already-c_dispatched
# products ``cd_mult`` / ``table_product`` — NO new C symbol, ABI unchanged
# — Class-K clean throughout (zero-tests via ⟨v,v⟩, never ``abs()``).
#
# SSoT: Schafer, R.D. (1966), *An Introduction to Nonassociative Algebras*,
# ch. III eqns (7)–(9), which ARE the three Moufang identities, read verbatim
# from the public-domain text (Project Gutenberg #25156). The associator
# itself is ch. II eqn (11), not ch. III — and the book has NO sections at
# all, so the "§III.1" this block carried through rc427 named a structure
# that does not exist (re-measured against the Gutenberg TeX: five chapters,
# zero `\section`; the associator is defined in ch. II):
#
#     (7)  (xax)y   = x[a(xy)]
#     (8)  y(xax)   = [(yx)a]x
#     (9)  (xy)(ax) = x(ya)x        for all x, y, a in an alternative algebra
#
# Conway, J.H. & Smith, D.A. (2003), *On Quaternions and Octonions*, A K
# Peters, ch. 6 (the unit-octonion Moufang loop and its Cayley table).
#
# ⚠️ ATTESTATION FIX, rc427 (`#T1130`). Through rc426 this block cited
# "Baez, J.C. (2002), *The Octonions*, arXiv:math/0105155, §2 (the octonion
# Moufang identities, alternativity, and the Mal'cev tangent algebra)" — and
# that attestation was FALSE in two independent ways, on prose that had
# already shipped inside published wheels:
#
#   * §2 is titled "Constructing the Octonions" and states no Moufang
#     identity. "Moufang" occurs 5 times in that paper and NONE of them is in
#     §2: three are in §3, where it names Ruth Moufang and the Moufang
#     (non-Desarguesian) projective plane 𝕆P² — a different object entirely —
#     and two are in the bibliography ([50] Gündaydin/Piron/Ruegg, [74] Ruth
#     Moufang 1933). The cayley_plane.py citations of Baez §3 / §4.2 for 𝕆P²
#     are therefore CORRECT and were left alone; only the
#     §2-for-Moufang-identities claim was wrong. Do not batch-convert.
#   * "Mal'cev" does not occur in that paper in ANY spelling. Positive
#     control on the same instrument: "Cayley–Dickson" occurs 22 times (18
#     with the en-dash the paper actually sets, 4 with an ASCII hyphen), so
#     the search can return otherwise.
#
# ⚠️ The control count read "7 times" when this block first shipped at rc427
# and was corrected to 22 in the same rc. BOTH wrong readings came from the
# same broken instrument, and the failure mode is worth keeping: `pdftotext`
# emits Latin-1 by DEFAULT, so decoding its output as UTF-8 mangles every
# en-dash and a "Cayley-Dickson" search then matches only the 4 ASCII-hyphen
# spellings. Extract with `pdftotext -enc UTF-8`, and count each dash variant
# SEPARATELY — a single count over a hyphen spelling silently under-reports a
# paper that sets the name with an en-dash. This is a positive control; a
# control that under-reports by 5× is not doing its job.
#
# The Mal'cev verdict is accordingly DERIVED-AND-MEASURED here, not cited;
# no replacement citation is asserted for it, because an unverified
# substitute would be the same defect wearing a different name.
# ──────────────────────────────────────────────────────────────────────

def _norm_sq(v: Sequence[Q]) -> Q:
    """⟨v, v⟩ = Σ vᵢ² — the exact-ℚ Class-K magnitude², never ``abs()`` (a
    square is nonnegative by construction). The all-zero tuple ⟺ 0."""
    return sum((c * c for c in v), _coerce_frac(0))


def _loop_products(table: Any, *elems: Sequence[Any]):
    """Coerce ``elems`` and return ``(mul, coerced)`` on associator's two
    routes: ``cd_mult`` on the definite ladder (``table=None``) or
    ``table_product`` on any structure table (``table=``). Raises on a
    dimension mismatch, exactly as :func:`associator`."""
    coerced = [tuple(_coerce_frac(v) for v in e) for e in elems]
    n = len(coerced[0])
    if any(len(e) != n for e in coerced):
        raise ValueError("Moufang op: all operands must share dimension")
    if table is None:
        if not (_is_pow2(n) and n <= CD_MAX_DIM):
            raise ValueError(
                f"table=None needs a power-of-two length ≤ {CD_MAX_DIM}; "
                f"got {n}")
        coerced = [_as_elem(e) for e in coerced]
        return cd_mult, coerced
    tbl = _structure_table(table)
    if len(tbl) != n:
        raise ValueError(
            f"table is dim {len(tbl)}; got operands of length {n}")
    return (lambda a, b: table_product(tbl, a, b)), coerced


def _loop_basis(table: Any, dim: int) -> "Tuple[int, List[Tuple[Q, ...]]]":
    """The ordered basis ``[e_0, …, e_{d-1}]`` of the algebra — the definite
    Cayley–Dickson ladder rung ``dim`` (``table=None``) or the algebra a
    structure ``table`` names (``d = len(table)``)."""
    if table is None:
        return dim, [cd_basis(dim, i) for i in range(dim)]
    tbl = _structure_table(table)
    d = len(tbl)
    z, one = _coerce_frac(0), _coerce_frac(1)
    return d, [tuple(one if t == i else z for t in range(d)) for i in range(d)]


def moufang_residue(x: Sequence[Any], y: Sequence[Any], z: Sequence[Any],
                    table: Any = None) -> Q:
    """The MOUFANG DEFECT of the ordered triple ``(x, y, z)`` — the max, over
    the three Moufang identities, of the exact-ℚ ⟨·,·⟩ magnitude² by which
    each fails (rc398, `#T1064`).

    The three identities (with ``·`` the algebra product)::

        M1:  x·(y·(x·z))  =  ((x·y)·x)·z
        M2:  y·(x·(z·x))  =  ((y·x)·z)·x
        M3:  (y·z)·(x·y)  =  y·((z·x)·y)

    Each is the all-zero tuple ⟺ that identity holds at ``(x, y, z)``; the
    return is ``max ⟨mᵢ, mᵢ⟩`` over the three residual tuples ``mᵢ = lhsᵢ −
    rhsᵢ``. It is EXACTLY 0 for every octonion triple (𝕆 is a Moufang loop —
    alternative, hence Moufang) and a real nonzero residual on a non-Moufang
    control: ``moufang_residue(e₁, e₂, e₁₂, table=algebra_table(16))`` on the
    sedenion rung 𝕊 returns 4, because 𝕊 is not even alternative and so not
    Moufang. Whole-loop verdict: :func:`is_moufang`.

    Args:
        x, y, z: equal-length elements — exact-rational components (int / Q /
            Fraction / float → its EXACT ratio / (num, den)). With
            ``table=None`` the length is a power of two ``≤ CD_MAX_DIM``.
        table: an optional dim × dim × dim structure tensor
            (:func:`algebra_table` — including its ``gammas=`` split controls
            — or any table :func:`table_product` reads); ``None`` — the
            default — is the definite Cayley–Dickson ladder ℝ→ℂ→ℍ→𝕆→𝕊….

    Returns:
        A single exact :class:`~srmech.math.q.Q` — 0 ⟺ all three Moufang
        identities hold at ``(x, y, z)``.

    Note:
        Exact end to end — no float, no epsilon, no ``abs()`` (the residue is
        the Class-K ⟨v,v⟩ magnitude²). NO new C symbol — ``composition_of_c``
        over the c_dispatched ``srmech_cd_mult`` / ``srmech_algebra_table_product``.
        Class M ∘ K.

    Provenance (rc429, `#T1128`):
        SSoT for the three identities: Schafer, R.D. (1966), *An Introduction
        to Nonassociative Algebras*, ch. III eqns (7)–(9), read verbatim from
        the public-domain text (Project Gutenberg #25156); Conway, J.H. &
        Smith, D.A. (2003), *On Quaternions and Octonions*, ch. 6.
        RE-VERIFIED at rc429 by extracting that TeX source directly
        (226,706 chars, sha256 25ff18d3…): "Moufang" occurs 3×, and eqn (7)
        is introduced with the words *"the Moufang identities"* — the
        locator is correct as cited. Positive controls on the same
        extraction: Schafer 15, alternative 44, Jordan 127; negative
        controls 0; no U+FFFD.

        ⚠️ This attribution shipped only in the registry ``summary`` through
        rc428 while three other emitted fields carried the claim bare. A
        verdict that reaches one artifact and not the others is the rc429
        defect class; gated per FIELD by
        ``tests/test_citation_manifest_rc428.py`` arm S6.

        ATTESTATION FIX rc427 (`#T1130`), restated here so it travels with
        the claim: Baez, *The Octonions*, arXiv:math/0105155 §2 was cited
        for the Moufang identities through rc426 and does NOT state them.
    """
    mul, (a, b, c) = _loop_products(table, x, y, z)

    def sub(u: Tuple[Q, ...], v: Tuple[Q, ...]) -> Tuple[Q, ...]:
        return tuple(p - q for p, q in zip(u, v))

    m1 = sub(mul(a, mul(b, mul(a, c))), mul(mul(mul(a, b), a), c))
    m2 = sub(mul(b, mul(a, mul(c, a))), mul(mul(mul(b, a), c), a))
    m3 = sub(mul(mul(b, c), mul(a, b)), mul(b, mul(mul(c, a), b)))
    return max(_norm_sq(m1), _norm_sq(m2), _norm_sq(m3))


def is_moufang(table: Any = None, dim: int = 8) -> bool:
    """Is the algebra a MOUFANG LOOP? — the whole-loop boolean: every ordered
    basis triple has :func:`moufang_residue` 0 (rc398, `#T1064`).

    True for the definite ladder up to 𝕆 (``dim`` 1/2/4/8 — ℝ/ℂ/ℍ/𝕆 are all
    Moufang) and FALSE from the sedenion rung up (``dim`` 16 — 𝕊 is not
    alternative, so not Moufang). Returns on the FIRST nonzero residue, so the
    False verdict is cheap; the True verdict is the full ``dim³`` basis-triple
    census. Reads any algebra a ``table`` names, so the ``gammas=`` split
    controls of :func:`algebra_table` go through it unchanged.

    Args:
        table: an optional structure tensor (:func:`algebra_table` or any
            table :func:`table_product` reads); ``None`` — the default — is the
            definite Cayley–Dickson ladder, whose rung is ``dim``.
        dim: the ladder rung when ``table is None`` (a power of two ``≤
            CD_MAX_DIM``); ignored when ``table`` is given (``len(table)`` wins).

    Returns:
        ``True`` ⟺ all three Moufang identities hold on every ordered basis
        triple of the algebra.

    Note:
        Exact, no ``abs()``. NO new C symbol — ``composition_of_c`` over
        :func:`moufang_residue`. Class M ∘ K.
    """
    d, basis = _loop_basis(table, dim)
    for i in range(d):
        for j in range(d):
            for k in range(d):
                if moufang_residue(basis[i], basis[j], basis[k],
                                   table=table) != 0:
                    return False
    return True


def malcev_defect(x: Sequence[Any], y: Sequence[Any], z: Sequence[Any],
                  table: Any = None) -> "Dict[str, Q]":
    """The loop's TANGENT-ALGEBRA check: the Jacobi (Lie) defect and the
    Mal'cev defect of the ordered triple ``(x, y, z)`` (rc398, `#T1064`).

    The tangent algebra of a Moufang loop is a **Mal'cev algebra**: the
    commutator bracket ``[x, y] = x·y − y·x`` is anticommutative but the
    Jacobi identity FAILS — it is replaced by the weaker Mal'cev identity.
    This op returns both defects as exact-ℚ ⟨·,·⟩ magnitude²::

        jacobi = ⟨J, J⟩,           J(x,y,z) = [[x,y],z]+[[y,z],x]+[[z,x],y]
        malcev = ⟨D, D⟩,           D = J(x,y,[x,z]) − [J(x,y,z), x]

    On the octonions ``jacobi`` is NONZERO on a generic imaginary triple
    (e.g. ``malcev_defect(e₁, e₂, e₄)`` → ``jacobi = 144`` since ``J = 12·e₇``)
    — the tangent algebra is **not Lie** — while ``malcev`` is EXACTLY 0 — it
    **is Mal'cev**. That pair, ``jacobi ≠ 0`` and ``malcev = 0``, is the
    Mal'cev-not-Lie signature of 𝔤 = Im 𝕆 under the commutator bracket.

    Args:
        x, y, z: equal-length elements (as :func:`moufang_residue`).
        table: an optional structure tensor; ``None`` is the definite ladder.

    Returns:
        ``{"jacobi": Q, "malcev": Q}`` — the Jacobi and Mal'cev magnitude²
        defects. ``jacobi > 0`` witnesses not-Lie; ``malcev == 0`` witnesses
        Mal'cev.

    Note:
        Exact, no ``abs()``. NO new C symbol — ``composition_of_c`` over the
        c_dispatched ``srmech_cd_mult`` / ``srmech_algebra_table_product``.
        Class C (bracket order) ∘ M ∘ K.

    Provenance — **DERIVED-AND-MEASURED, not cited** (rc428, `#T1126`):
        rc427 verified that Baez, *The Octonions*, arXiv:math/0105155 —
        cited here through rc426 for "the Mal'cev tangent algebra" —
        contains **no occurrence of "Mal'cev" in any spelling**, across nine
        spellings including the Cyrillic. Positive control on the same
        extraction: "Cayley–Dickson" occurs 22× (18 en-dash, 4 ASCII), so
        that zero is a measurement rather than silence. **No attestation is
        claimed for the Mal'cev verdict and none is substituted unverified**
        — an unverified replacement would be the same defect wearing a
        different name. The verdict is DERIVED-AND-MEASURED because srmech
        computes it and a named test EXECUTES the claim:
        ``tests/test_moufang_loop_rc398.py`` calls ``malcev_defect`` and
        asserts ``d["malcev"] == 0`` on every octonion basis triple.

        ⚠️ rc428 repair: this line named ``tests/test_loop_bind_moufang.py``,
        which contains **zero** occurrences of ``malcev_defect``. That file
        does verify the Mal'cev identity on 𝕆 through the HDC loop-bind path,
        so the substantive claim was true — but it does not exercise THIS op,
        and a DERIVED-AND-MEASURED verdict is a claim about what the named
        test measures. Arm S3 asserted only that the named file EXISTS, so a
        correct-looking path to a real file passed a check that was never
        reading it; S3 now requires the named test to reference the op.

        ⚠️ rc427 removed the false citation and recorded that reasoning in a
        ``#`` comment above this function. A comment does not ship — the
        claim below reaches users through ``help()``, ``describe()``, the
        MCP tool list and the compiled-in C registry, and it reached them
        with no verdict attached. Removing a false citation without moving
        its verdict into the SAME artifact as the claim converts a false
        citation into an unsourced one: a change of defect class, not a fix.
        Gated by ``tests/test_citation_manifest_rc428.py`` arm S3.

        SSoT for the ambient algebra: Schafer, R.D. (1966), *An Introduction
        to Nonassociative Algebras*, ch. III (Project Gutenberg #25156).

        ⚠️ rc429 (`#T1128`) — **the paragraph above carries TWO claims and
        they do not share a verdict.** One DERIVED-AND-MEASURED stamp over
        both would launder the general one on the specific one's evidence:

        **A. "The tangent algebra of a Moufang loop IS a Mal'cev algebra"
        — UNSOURCED in this tree; standard background, retained
        deliberately.** It is a general theorem over ALL Moufang loops, and
        executing ``malcev_defect(e₁,e₂,e₄)`` establishes an INSTANCE on 𝕆,
        not the theorem. It is kept because deleting it impoverishes the
        docstring for the why-asker, and it is marked rather than removed
        because an unsourced claim wearing a measured claim's verdict is the
        defect this rc exists to close. **The Schafer line above is NOT
        widened to cover it, and that was decided by extraction rather than
        by preference**: the Project Gutenberg #25156 TeX source
        (226,706 chars, sha256 25ff18d3…) contains **0** occurrences of
        "Mal'cev" in any spelling, 0 of "Kuzmin", 0 of "tangent algebra" and
        0 of "Moufang loop", on an extraction whose live positive controls
        read Schafer 15 / alternative 44 / Moufang 3 / Jordan 127, whose
        negative controls read 0, and which carries no U+FFFD — so those
        zeroes are MEASUREMENTS, not silence. Schafer ch. III is alternative
        algebras; the Moufang-tangent-algebra result is Mal'cev/Kuzmin, and
        the only trace in that volume is a bibliography line ("A note on
        Moufang-Lie rings", Proc. Amer. Math. Soc. **9** (1958)), which
        states no theorem. No second citation is substituted.

        **B. "jacobi = 144 at (e₁,e₂,e₄) … malcev is EXACTLY 0" —
        DERIVED-AND-MEASURED**, per the verdict block above: these are the
        two keys this op RETURNS, and ``tests/test_moufang_loop_rc398.py``
        calls it and asserts them.

        The same extraction independently VERIFIED the sibling citation on
        :func:`moufang_residue`: the three Moufang identities really are
        Schafer's eqns (7)–(9), quoted there verbatim.
    """
    mul, (a, b, c) = _loop_products(table, x, y, z)

    def sub(u: Tuple[Q, ...], v: Tuple[Q, ...]) -> Tuple[Q, ...]:
        return tuple(p - q for p, q in zip(u, v))

    def comm(p: Tuple[Q, ...], q: Tuple[Q, ...]) -> Tuple[Q, ...]:
        return sub(mul(p, q), mul(q, p))

    def jac(p: Tuple[Q, ...], q: Tuple[Q, ...],
            r: Tuple[Q, ...]) -> Tuple[Q, ...]:
        t1, t2, t3 = comm(comm(p, q), r), comm(comm(q, r), p), comm(comm(r, p), q)
        return tuple(u + v + w for u, v, w in zip(t1, t2, t3))

    jabc = jac(a, b, c)
    mal = sub(jac(a, b, comm(a, c)), comm(jac(a, b, c), a))
    return {"jacobi": _norm_sq(jabc), "malcev": _norm_sq(mal)}


#: Standard names for the unit Moufang loop by ORDER (= 2·dim signed units).
_UNIT_LOOP_NAMES: "Dict[int, str]" = {2: "C2", 4: "C4", 8: "Q8", 16: "M16",
                                      32: "M32"}


def _monomial_cocycle(table: Any) -> "Tuple[int, Dict[Tuple[int, int], Tuple[int, int]]]":
    """``(d, cocycle)`` for a MONOMIAL structure table, where
    ``cocycle[(i, j)] == (index, sign)`` means ``e_i·e_j = sign·e_index``.

    A signed BASIS-UNIT loop exists only when every product of two basis units
    is again ±a basis unit, i.e. when the table is monomial — the property
    :func:`algebra_table` has by construction and an arbitrary table need not.
    Raising here rather than silently returning a partial loop is deliberate:
    a non-monomial table has no unit loop to return.
    """
    tbl = _structure_table(table)
    d = len(tbl)
    coc: Dict[Tuple[int, int], Tuple[int, int]] = {}
    for i in range(d):
        for j in range(d):
            nz = [(k, v) for k, v in enumerate(tbl[i][j]) if v != 0]
            if len(nz) != 1 or nz[0][1] not in (1, -1):
                raise ValueError(
                    f"table= needs a MONOMIAL table (e_i·e_j = ±e_k); cell "
                    f"({i}, {j}) has {len(nz)} nonzero coefficient(s)")
            coc[(i, j)] = (nz[0][0], nz[0][1])
    for i in range(d):
        if coc[(0, i)] != (i, 1) or coc[(i, 0)] != (i, 1):
            raise ValueError(
                "table= needs e_0 to be the two-sided identity of the "
                f"structure table; e_0·e_{i} or e_{i}·e_0 is not e_{i}")
    return d, coc


def _ordered_loop(dim: int, table: Any = None) -> "List[Tuple[int, int]]":
    """The full unit loop as an ORDERED list ``[+e₀,…,+e_{d-1},−e₀,…,−e_{d-1}]``,
    tied to the actual :func:`closure` result (positives-then-negatives read).

    ``table=None`` is the definite Cayley–Dickson ladder rung ``dim``; a
    supplied monomial structure table names its own algebra and ``dim`` is
    ignored in favour of ``len(table)``."""
    if table is None:
        spanned = closure(dim, list(range(1, dim)))
        d = dim
    else:
        d, coc = _monomial_cocycle(table)
        spanned = {(1, 0)}
        spanned.update((1, g) for g in range(1, d))
        changed = True
        while changed:
            changed = False
            for a in list(spanned):
                for b in list(spanned):
                    k, s = coc[(a[1], b[1])]
                    prod = (a[0] * b[0] * s, k)
                    if prod not in spanned:
                        spanned.add(prod)
                        changed = True
    canonical = [(1, i) for i in range(d)] + [(-1, i) for i in range(d)]
    return [su for su in canonical if su in spanned]


def _loop_mult_any(dim: int, table: Any,
                   a: "Tuple[int, int]", b: "Tuple[int, int]",
                   coc: "Any" = None) -> "Tuple[int, int]":
    """Signed-unit product on either route — the definite ladder cocycle
    (``table=None``) or a monomial structure table.

    ``coc`` is the ALREADY-RESOLVED cocycle for ``table``, as returned by
    :func:`_monomial_cocycle`.  Pass it whenever more than one product is
    taken against the same table: this function is called once per CELL of a
    ``2·d × 2·d`` Cayley table, and :func:`_monomial_cocycle` is an O(d²)
    full-table scan, so resolving it per call made the table build O(d⁴).
    Measured at ``dim=16``: ``unit_loop(table=)`` **1.07 s → 0.003 s**, output
    verified bit-identical (sha256 over the full result, all of dim 2/4/8/16,
    both routes).  ``None`` keeps the self-contained behaviour for a one-off
    call.

    ⚠️ This hoist does NOT speed up :func:`loop_invariants`, and the honest
    reason is that its cost was never here: measured 19.0 s → 17.6 s at
    ``dim=16``.  The residual is the O(order³) ``associator`` /
    ``cd_commutator`` sweep over ``nucleus`` / ``commutant``, where each call
    re-runs :func:`_structure_table` — an O(d³) validate-and-copy — on the
    same table.  Fixing that means threading a pre-validated table through
    those PUBLIC, c_dispatched ops, which changes their signatures and is its
    own rc; it is deliberately not smuggled in here.  Do not read the number
    above as covering ``loop_invariants``.
    """
    if table is None:
        return _loop_mult(dim, a, b)
    if coc is None:
        _d, coc = _monomial_cocycle(table)
    index, sign = coc[(a[1], b[1])]
    return (a[0] * b[0] * sign, index)


def unit_loop(dim: int = 8, table: Any = None) -> "Dict[str, Any]":
    """The UNIT MOUFANG LOOP of the Cayley–Dickson rung ``dim`` — the named
    handle for the 16 signed octonion units **M16** (rc398, `#T1064`).

    The ``2·dim`` signed basis units ``{±e₀, …, ±e_{dim-1}}`` close under
    Cayley–Dickson multiplication into a loop (a quasigroup with identity).
    At ``dim=8`` that is **M16**, the octonion unit Moufang loop — the object
    that has lived in the tree only as the DATA ``closure(8, [1..7])``; this op
    NAMES it and hands back its Cayley table. At ``dim=4`` it is the quaternion
    group **Q8** (associative — a group, the degenerate Moufang loop); at
    ``dim=16`` the sedenion unit loop **M32** (not Moufang; see
    :func:`is_moufang`). The data is not duplicated — ``elements`` is the
    ordered :func:`closure` result.

    Args:
        dim: the ladder rung — a power of two ``≤ CD_MAX_DIM``.
        table: an optional rank-3 MONOMIAL structure-constant table (e.g. from
            :func:`algebra_table`, including its ``gammas=`` SPLIT members).
            ``None`` — the default — is the shipped Cayley–Dickson product and
            reproduces every previous result bit-identically; a supplied table
            names its own algebra and its length supersedes ``dim``.  Added
            rc427 (`#T1130`): ``unit_loop`` and :func:`loop_invariants` were
            the only two members of the twelve-op cascade loop family without
            it, so any caller wanting the unit loop of a split or γ-twisted
            algebra had to hand-roll the closure through
            :func:`table_product`.  The parameter carries **no new A–N class**
            — it is carrier plumbing, not content-addressing.

    Returns:
        ``{"dim", "order" (= 2·dim), "name", "elements", "cayley_table"}``
        where ``elements`` is the ordered signed units ``[(sign, index), …]``
        (``[+e₀,…, −e₀,…]``) and ``cayley_table[a][b]`` is the ``elements``
        index of ``element_a · element_b`` — a Latin square (every row and
        column a permutation), the defining loop property.

    Note:
        Wraps :func:`closure`; the products are the integer cocycle
        ``srmech_cd_basis_product`` — ``composition_of_c``, no new C symbol.
        With ``table=`` the products come from the table instead and the
        native cocycle is not consulted.
    """
    elements = _ordered_loop(dim, table)
    coc = None
    if table is not None:
        dim, coc = _monomial_cocycle(table)
    idx = {su: n for n, su in enumerate(elements)}
    cayley = [[idx[_loop_mult_any(dim, table, a, b, coc)] for b in elements]
              for a in elements]
    order = len(elements)
    return {
        "dim": dim,
        "order": order,
        "name": _UNIT_LOOP_NAMES.get(order, f"L{order}"),
        "elements": elements,
        "cayley_table": cayley,
    }


def loop_invariants(dim: int = 8, table: Any = None) -> "Dict[str, Any]":
    """The loop-theory INVARIANTS of the unit Moufang loop, plus the
    generators of its multiplication group Mlt(L) (rc398, `#T1064`).

    Over the ordered unit loop ``L`` (:func:`unit_loop`) it returns:

    * **nucleus** — the associative centre ``{a : (a,x,y) = 0 ∀ x, y}`` (the
      elements that associate with everything; :func:`associator` is the
      instrument). For M16 the nucleus is exactly ``{±1} = {±e₀}`` — the loop
      is as-non-associative as a Moufang loop gets.
    * **commutant** — ``{a : [a, x] = 0 ∀ x}`` (:func:`cd_commutator`), the
      elements that commute with everything; for M16 also ``{±1}``.
    * **center** — nucleus ∩ commutant (associates AND commutes); ``{±1}``.
    * **left_translations / right_translations** — the generators of the
      multiplication group **Mlt(L) = ⟨Lₐ, Rₐ⟩**, each a permutation of the
      loop given as an ``elements``-index list (``Lₐ = a·x``, ``Rₐ = x·a``).
      These ARE the discrete restrictions of ``srmech.math.hdc``'s
      :func:`loop_left_op` / :func:`loop_right_op`, and they surface the
      identity ``associator(a, x, b) = −[Lₐ, R_b]·x`` (the commutator of a
      left and a right translation IS the associator, up to sign).

    Args:
        dim: the ladder rung — a power of two ``≤ CD_MAX_DIM``.
        table: an optional rank-3 MONOMIAL structure-constant table, exactly
            as :func:`unit_loop` takes it.  ``None`` — the default — is the
            shipped Cayley–Dickson product, unchanged.  Added rc427
            (`#T1130`) as the other half of the same gap; carrier plumbing,
            **no new A–N class**.  :func:`associator` and
            :func:`cd_commutator` already took ``table=``, so the invariants
            themselves needed no new mathematics — only a way to say which
            algebra they are invariants OF.

    Returns:
        ``{"nucleus", "commutant", "center"}`` (each a list of signed units
        ``[(sign, index), …]``) and ``{"left_translations",
        "right_translations"}`` (each a list of ``elements``-index
        permutations).

    Note:
        ``composition_of_c`` over :func:`associator` / :func:`cd_commutator`
        and the integer loop cocycle — no new C symbol, no ``abs()``.
    """
    elements = _ordered_loop(dim, table)
    coc = None
    if table is not None:
        dim, coc = _monomial_cocycle(table)
    idx = {su: n for n, su in enumerate(elements)}
    vecs = {}
    for s, i in elements:
        v = [0] * dim
        v[i] = s
        vecs[(s, i)] = tuple(_coerce_frac(c) for c in v)

    nucleus = [a for a in elements
               if all(_norm_sq(associator(vecs[a], vecs[u], vecs[w], table)) == 0
                      for u in elements for w in elements)]
    commutant = [a for a in elements
                 if all(_norm_sq(cd_commutator(vecs[a], vecs[u], table)) == 0
                        for u in elements)]
    center = [a for a in nucleus if a in commutant]
    left = [[idx[_loop_mult_any(dim, table, a, x, coc)] for x in elements]
            for a in elements]
    right = [[idx[_loop_mult_any(dim, table, x, a, coc)] for x in elements]
             for a in elements]
    return {
        "nucleus": nucleus,
        "commutant": commutant,
        "center": center,
        "left_translations": left,
        "right_translations": right,
    }


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


def _build_zero_divisor_dict(i: int, j: int, k: int, l: int, s: int,
                             dim: int = 16) -> Dict[str, Any]:
    """Assemble the witness dict from the found basis indices. ``dim`` defaults
    to 16 (the sedenion rung) so the rc158→rc394 dim-16 payload is reproduced
    byte-for-byte; :func:`cd_zero_divisor_witness` passes the actual rung for the
    general instrument (rc395, `#T1000`)."""
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


def _zd_support_solutions(d: int, n_bits: int) -> List[Tuple[int, int]]:
    """Every ``(k, l)`` with ``k ⊕ l = d`` over ``(ℤ/2)^n_bits``, obtained by
    SOLVING the affine GF(2) system ``[I | I | d]`` through the shipped Class-I
    :func:`~srmech.math.modular_linalg.gf_rref` — not by enumerating pairs and
    filtering.

    The unknowns are the ``n_bits`` bits of ``k`` then the ``n_bits`` bits of
    ``l``; row ``b`` is ``k_b + l_b = d_b (mod 2)``. ``gf_rref`` returns the RREF,
    its rank and its pivot columns; the free columns parametrise the affine
    solution set, read back by back-substitution from that RREF.
    """
    n_unk = 2 * n_bits
    rows: List[List[int]] = []
    for b in range(n_bits):
        row = [0] * (n_unk + 1)
        row[b] = 1
        row[n_bits + b] = 1
        row[n_unk] = (d >> b) & 1
        rows.append(row)
    out = gf_rref(rows, 2)                       # ← the shipped Class-I GF(2) solve
    rref, pivots = out["rref"], out["pivots"]
    free = [c for c in range(n_unk) if c not in pivots]
    solutions: List[Tuple[int, int]] = []
    for mask in range(1 << len(free)):
        x = [0] * n_unk
        for t, c in enumerate(free):
            x[c] = (mask >> t) & 1
        for row_i, pivot_col in enumerate(pivots):    # back-substitute
            acc = rref[row_i][n_unk]
            for c in free:
                acc ^= rref[row_i][c] & x[c]
            x[pivot_col] = acc
        k = sum(bit << b for b, bit in enumerate(x[:n_bits]))
        l = sum(bit << b for b, bit in enumerate(x[n_bits:]))
        solutions.append((k, l))
    return solutions


def _cd_zero_divisor_tuples(dim: int) -> List[Tuple[int, int, int, int, int]]:
    """The COMPLETE, deterministically ordered set of basis-pair zero-divisor
    witnesses ``(i, j, k, l, s)`` — ``(e_i + e_j)·(e_k + s·e_l) = 0`` — of the
    Cayley–Dickson algebra of dimension ``dim``, with NO search over the sign
    and NO search over ``(k, l)``.

    Derivation. ``e_a·e_b = σ(a,b)·e_{a⊕b}``, so the product expands to four
    terms with indices ``i⊕k, i⊕l, j⊕k, j⊕l``. With ``i ≠ j`` and ``k ≠ l`` the
    only pairing that can cancel forces the single GF(2) condition
    ``i ⊕ j ⊕ k ⊕ l = 0`` — the affine system solved by
    :func:`_zd_support_solutions`. Given a surviving support the first pair
    cancels iff ``σ(i,k) + s·σ(j,l) = 0``, so ``s = −σ(i,k)·σ(j,l)`` is
    **determined** (a Class-K sign pin re-applied by Class-C); the witness is
    admitted iff the second pair then also cancels. Signs come from the
    C-dispatched :func:`cd_basis_product`.

    Ordering is total: outer ``(i, j)`` ascending, and within each pair the
    admitted supports sorted by ``(k, l)`` — so ``[0]`` is the first witness.
    Empty for every ``dim ≤ 8`` (ℝ / ℂ / ℍ / 𝕆 are division algebras). O(dim³),
    tractable to :data:`CD_MAX_DIM` — NOT the exponential product sweep.
    """
    if not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(f"dim must be a power of two ≤ {CD_MAX_DIM}; got {dim}")
    if dim <= 8:
        return []                               # division algebras: no zero divisor
    n_bits = dim.bit_length() - 1
    witnesses: List[Tuple[int, int, int, int, int]] = []
    for i in range(1, dim):
        for j in range(i + 1, dim):
            admitted: List[Tuple[int, int, int, int, int]] = []
            for (k, l) in _zd_support_solutions(i ^ j, n_bits):
                if k == 0 or l == 0 or k >= l:
                    continue                    # e_0 = 1; (k, l) unordered
                _idx, s_ik = cd_basis_product(dim, i, k)
                _idx, s_jl = cd_basis_product(dim, j, l)
                _idx, s_il = cd_basis_product(dim, i, l)
                _idx, s_jk = cd_basis_product(dim, j, k)
                s = -s_ik * s_jl                # DETERMINED, not searched
                if s * s_il + s_jk == 0:
                    admitted.append((i, j, k, l, s))
            admitted.sort(key=lambda w: (w[2], w[3]))
            witnesses.extend(admitted)
    return witnesses


def cd_zero_divisor_witnesses(dim: int = 16
                              ) -> List[Tuple[int, int, int, int, int]]:
    """The COMPLETE set of basis-pair zero-divisor witnesses of the
    Cayley–Dickson algebra of dimension ``dim`` — every ``(i, j, k, l, s)`` with
    ``(e_i + e_j)·(e_k + s·e_l) = 0``, both factors nonzero. The dim-general
    successor of the rc158 hardwired sedenion witness: it EXHIBITS the whole
    boundary, not one point of it.

    A ``composition_of_c`` op — it solves the ``i ⊕ j ⊕ k ⊕ l = 0`` support
    system with the C-dispatched Class-I :func:`~srmech.math.modular_linalg.gf_rref`
    and reads every sign off the C-dispatched cocycle :func:`cd_basis_product`;
    the second-factor sign is DETERMINED, never searched, so the cost is O(dim³)
    (tractable to :data:`CD_MAX_DIM` = 256), not the exponential product sweep.
    Deterministic order (``(i, j, k, l)`` ascending), so ``[0]`` is the first
    witness. Empty for every ``dim ≤ 8`` — ℝ / ℂ / ℍ / 𝕆 are division algebras
    and provably have none (§VII.6.23: zero divisors first appear at 16 and
    never heal). At dim 16 there are exactly 168.
    """
    return _cd_zero_divisor_tuples(dim)


def cd_zero_divisor_witness(dim: int = 16) -> "Dict[str, Any] | None":
    """The FIRST basis-pair zero divisor (deterministic order) of the
    Cayley–Dickson algebra of dimension ``dim`` — ``x = e_i + e_j`` and
    ``y = e_k + s·e_l`` with ``x·y = 0``, both nonzero — returned as a dict with
    the two elements (Q tuples), their ``e_i ± e_j`` forms, their (nonzero)
    squared norms, and the (all-zero) product.

    The dim-general successor of the removed hardwired ``sedenion_zero_divisor_
    witness``: at ``dim = 16`` it returns the IDENTICAL payload (``x = e1 + e10``,
    ``y = e4 − e15``) — the dim-16 answer is unchanged, only the name and the
    generality moved. ``None`` for every ``dim ≤ 8`` (the division algebras have
    no zero divisor). Shares the :func:`cd_zero_divisor_witnesses` enumeration —
    it is ``[0]`` of that set, so a ``composition_of_c`` over the same
    C-dispatched :func:`~srmech.math.modular_linalg.gf_rref` + :func:`cd_basis_product`.
    """
    tuples = _cd_zero_divisor_tuples(dim)
    if not tuples:
        return None
    return _build_zero_divisor_dict(*tuples[0], dim=dim)


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
    :class:`~srmech.math.q.Q`, which no numpy dtype can hold without rounding.
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


def right_mult_matrix(x: Sequence[Any], table: Any = None) -> List[List[Q]]:
    """The ``n×n`` rational matrix of the linear map ``u ↦ u·x`` (column ``c`` is
    ``e_c·x``), row-major — the **right-regular** representation.

    rc437 (`#T1142`): the peer :func:`left_mult_matrix` has had since rc160, and
    the reason it was missing is worth stating. ``octonion_right_mult`` and
    ``quaternion_right_mult`` (:mod:`srmech.physics.qm.octonion` /
    :mod:`~srmech.physics.qm.quaternion`) ship the same object at dims 8 and 4
    ONLY, over the fixed physics tables; nothing on the Cayley–Dickson ladder
    built ``R(x)`` at all, so :func:`cd_right_divide` had no operator to invert.
    Verified before building: ``grep -rn "right_mult_matrix"`` over ``srmech/``
    at rc436 returned zero definitions.

    **It is NOT ``left_mult_matrix`` transposed, and it is not its conjugate.**
    Past ℝ the two representations are genuinely different maps — measured at
    rc437, ``R(x) == L(x)`` on **0 of 40** random elements at every dim 4…32,
    and ``R(x) == L(x)ᵀ`` on **0 of 40** as well. They coincide only where the
    algebra is commutative (dims 1 and 2, where ``R(x) == L(x)`` on 40/40). That
    non-coincidence IS the Class-C which-way content of division: it is why
    ``a\\c`` and ``c/b`` are two ops rather than one op with a flag.

    Same ``composition_of_c`` shape as its left peer: each column ``e_c·x`` is a
    :func:`cd_mult` (the CD product) over the C-dispatched :func:`cd_basis` unit
    vector, or a :func:`table_product` when ``table`` names a different algebra.
    """
    x = _as_elem(x)
    n = len(x)
    if table is None:
        cols = [cd_mult(cd_basis(n, c), x) for c in range(n)]
    else:
        tbl = _structure_table(table)
        if len(tbl) != n:
            raise ValueError(
                f"right_mult_matrix: the table is dim {len(tbl)} but the "
                f"element has {n} components")
        cols = [table_product(tbl, cd_basis(n, c), x) for c in range(n)]
    return [[cols[c][r] for c in range(n)] for r in range(n)]


def _divide_by_operator(mat: List[List[Q]], c: Tuple[Q, ...],
                        op: str, den: str, side: str) -> Tuple[Q, ...]:
    """Solve ``M·q = c`` exactly over ℚ and return ``q``, or raise with the
    quasigroup-shaped message. Shared by both division halves — the ONLY
    difference between them is which operator matrix arrives here.

    The raise is the point of the op (rc437, `#T1142`): a singular operator
    means the divisor kills a nonzero direction, so the quotient either does
    not exist or is not unique, and either way there is no answer to return.
    The rival closed form returns a number here."""
    n = len(mat)
    try:
        sol = QMat.from_rows(mat).solve([[v] for v in c])
    except ValueError as exc:
        raise ValueError(
            f"{op}: the divisor `{den}` is a {side} zero divisor (or zero) at "
            f"dim {n} — the map u ↦ {'{den}·u'.format(den=den) if side == 'left' else 'u·{den}'.format(den=den)} "
            f"is not invertible, so there is no unique quotient to return. "
            f"This op REFUSES rather than answering; the conjugate closed form "
            f"conj·c/N would have returned a non-solution here. Use "
            f"left_mult_kernel / left_mult_is_invertible to see the failure "
            f"directly. Underlying: {exc}") from exc
    return tuple(sol[r, 0] for r in range(n))


def cd_left_divide(a: Sequence[Any], c: Sequence[Any],
                   table: Any = None) -> Tuple[Q, ...]:
    """``a \\ c`` — the unique ``q`` with ``a·q = c``. Exact over ℚ at every
    Cayley–Dickson rung; raises ``ValueError`` when ``a`` is a left zero divisor.

    **Class C.** Left-versus-right IS the which-way choice, so this ships as two
    named ops (:func:`cd_right_divide` is the other) and never as one op with a
    ``side=`` flag. The quasigroup literature makes the identical move: defining
    a quasigroup equationally requires ``\\`` and ``/`` as separate primitives,
    because past commutativity neither one determines the other.

    🔴 **NOT the conjugate formula, and the difference is a wrong ANSWER, not a
    slower one.** The tempting closed form is ``conj(a)·c / N(a)``, justified by
    ``conj(a)·(a·b) = b``. That justification is false as stated: the real
    identity is ``conj(a)·(a·b) = N(a)·b``, so the un-normalised form is off by
    the whole norm — MEASURED at rc437, it fails on **40/40** generic elements
    at *every* dim 4/8/16/32 (worked instance: ``a = (1,2,0,0,3,0,0,1)`` has
    ``N(a) = 15`` and returns ``15·b``). Normalising by ``N(a)`` fixes dims ≤ 8
    and **nothing above**: with the division performed, the failure count is
    0/40 at dims 2/4/8 and **40/40 at dims 16 and 32**, because the step
    ``conj(a)·(a·b) = N(a)·b`` needs ALTERNATIVITY, which dies at 𝕊.

    ⚠️ And it fails SILENTLY. On the shipped dim-16 zero-divisor witness
    ``x = e₁+e₁₀`` (``N(x) = 2 ≠ 0``, left-kernel dim 4) the normalised
    conjugate form divides by a perfectly good norm and RETURNS — a value which
    then fails ``x·q == c``. This op raises instead. That is the whole reason it
    is built on the operator rather than the norm.

    ⚠️ A probe of the form ``a = 1 + eᵢ`` CANNOT see any of this: those elements
    are near-unit and alternative enough that the normalised conjugate form
    scores **0 failures out of 992** at dim 32. Any future re-measurement must
    use GENERIC elements.

    **The route.** ``q`` is read off the left-regular operator
    :func:`left_mult_matrix` — ``L(a)·q = c`` — by the exact-ℚ
    :meth:`~srmech.math.qmat.QMat.solve`. Measured exact (``q == b``) on
    **20/20** random NONZERO pairs at each of dims 2/4/8/16/32/64, and it
    REFUSES on the zero divisor rather than answering. ``composition_of_c``:
    ``srmech_qmat_solve`` over the C-composed ``L(a)`` (``srmech_cd_mult`` /
    ``srmech_cd_qbasis``) — verified present in ``c/include/srmech.h`` at rc437,
    NO new C symbol, ABI stays 14.

    ``table`` (the rc352 argument :func:`left_mult_matrix` already takes) names a
    DIFFERENT algebra, so division on a split twist or a hand-built table is
    reachable — and split-𝕆 refuses at dim 8, which the ladder's own wall does
    not.

    SSoT: Bruck, *A Survey of Binary Systems* (1958) §I.1 (a quasigroup's two
    division operations as separate primitives); Schafer, *An Introduction to
    Nonassociative Algebras* (1966) ch. III (alternativity, and its loss at 𝕊).
    """
    a_el = _as_elem(a)
    c_el = _as_elem(c)
    if len(a_el) != len(c_el):
        raise ValueError(
            f"cd_left_divide: a has {len(a_el)} components but c has "
            f"{len(c_el)}; both operands must live in the same algebra")
    return _divide_by_operator(left_mult_matrix(a_el, table), c_el,
                               "cd_left_divide", "a", "left")


def cd_right_divide(c: Sequence[Any], b: Sequence[Any],
                    table: Any = None) -> Tuple[Q, ...]:
    """``c / b`` — the unique ``q`` with ``q·b = c``. Exact over ℚ at every
    Cayley–Dickson rung; raises ``ValueError`` when ``b`` is a right zero divisor.

    The Class-C mirror of :func:`cd_left_divide`, and **not** obtainable from it:
    the two answer different questions the moment the algebra stops commuting.
    MEASURED at rc437, feeding this op the LEFT question — ``cd_right_divide(a·b,
    a)``, asking whether it returns ``b`` — scores **0/40** at each of dims 4, 8
    and 16, while its own question scores 20/20 there. The two can agree only
    where the algebra commutes (dims 1–2, where they score 40/40 on the nonzero
    draws). Handing one op a ``side=`` flag would hide that behind a default.

    It solves against :func:`right_mult_matrix` — ``R(b)·q = c`` — which rc437
    had to build first: nothing on the CD ladder held the right-regular
    representation (``octonion_right_mult`` / ``quaternion_right_mult`` are
    dim-8 / dim-4 physics-table ops, not ladder ops). Everything else — the
    exact-ℚ solve, the zero-divisor refusal, the ``table`` argument, the
    ``composition_of_c`` classification — is identical to the left half.

    ⚠️ The refusal condition is the RIGHT zero-divisor one, which is a different
    predicate from ``left_mult_is_invertible``. This op does not claim the two
    coincide; it asks its own operator.
    """
    c_el = _as_elem(c)
    b_el = _as_elem(b)
    if len(c_el) != len(b_el):
        raise ValueError(
            f"cd_right_divide: c has {len(c_el)} components but b has "
            f"{len(b_el)}; both operands must live in the same algebra")
    return _divide_by_operator(right_mult_matrix(b_el, table), c_el,
                               "cd_right_divide", "b", "right")


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
# dim 16 they are EXHIBITED (:func:`cd_zero_divisor_witness`), never
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
# (:func:`srmech.cascade.cd_basis_product` commuting-pair counts;
# ``hdc.loop_associator`` / ``genome_octonion_associator``;
# :func:`cd_zero_divisor_witness` / :func:`left_mult_is_invertible`).
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
    shape :func:`srmech.physics.qm.octonion.octonion_mult_table` and
    :func:`srmech.physics.qm.quaternion.quaternion_mult_table` already return. The
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
    shape :func:`srmech.physics.qm.octonion.octonion_mult_table` and
    :func:`srmech.physics.qm.quaternion.quaternion_mult_table` already return. The
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
    :func:`left_mult_is_invertible`; :func:`cd_zero_divisor_witnesses` does take a
    dimension argument, but it enumerates only the discrete BASIS-PAIR witnesses
    ``(e_i + e_j)(e_k + s·e_l) = 0`` (168 at dim 16), not the rational isotropy
    cone of the norm form, so it is not a general isotropy surface either.
    **This gap is open, not closed.**

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
    ``srmech.biology.genome.genome_octonion_associator``, and
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
