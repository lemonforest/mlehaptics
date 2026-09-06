"""THE addressable RBS-HDC register srmech ships (rc297; `#934`. rc464: preferred).

**Reach for :class:`CDRegister` whenever you want an addressable register.** It is
the register shape — ``dim`` is a constructor parameter, so one object serves every
rung from ℝ to 256 slots, and the 16-slot sedenion instrument is the spelling
``CDRegister(16, namespace="SEDENION", coupling=True, error_correction=True)``
rather than a second class. That subsumption is not asserted: it is gated
byte-for-byte in ``tests/test_cd_register_golden_rc464.py`` against 1157 recorded
outcomes of the class it replaced (``tests/sedenion_register_golden_rc464.ndjson``),
including the materialised bundle's SHA-256 at three widths.

How it got here. srmech shipped exactly one addressable register — hard-wired to
the sedenion's 16 slots. Research that needed 32 slots therefore had to write its
own, and correctly flagged that as a confound: *"a register I wrote could just be
easier."* rc297 removed the confound by bringing the general register in-tree;
rc464 makes it the PREFERRED shape and moves the dim-16 faithfulness gate off
the live 16-slot class onto a digest-pinned recording of it, so the oracle can
no longer drift with the subject it grades.

**The slot count is the ONLY thing that generalises.** Every sign rule, every index
rule, the minter, the bind/bundle/similarity storage, the odd-N pad, the Class-C
chiral sign and the nearest-codebook clean are shared verbatim with the 16-slot
register. There is no second algebra here and no new primitive class.

Why a general register is SOUND above the Hurwitz wall (F1274 / F1275)
---------------------------------------------------------------------
Addressing does not need the division property. It needs only that a basis product
be a **signed permutation**, ``e_i · e_j = ±e_k``. Zero divisors — what the Hurwitz
boundary introduces at dim 16 and worsens at 32 — are built from **sums** of basis
elements (``e1 + e10``), never from a single basis pair. The two properties are
therefore **disjoint**, and the boundary that destroys composition leaves addressing
untouched::

    dim   composition (norm-multiplicative)   addressing (signed permutation)
    ---   ---------------------------------   -------------------------------
      8   holds                               holds
     16   FAILS (zero divisors appear)        holds
     32   FAILS for ~95% of generic pairs     holds
     64   FAILS                               holds  (4096/4096 basis pairs)

:func:`cd_navmap_is_signed_permutation` makes that premise **checkable at runtime**
rather than assumed, and ``tests/test_cd_register_rc297.py`` enforces it against a
full exact-rational :func:`~srmech.cascade.cayley_dickson.cd_mult` — so the
property is a gate, not a comment.

The sign is not a function of the labels, and that is the whole join
------------------------------------------------------------------
``e_i · e_j = ±e_k`` pins ``k = i ⊕ j`` at every rung — that is the INDEX
lane, and it is free. It does NOT pin the ``±``. Ask the sharp version: is
the sign a COBOUNDARY? I.e. does some per-index ``t: {0..dim-1} → GF(2)``
exist with ``t(i) + t(j) + t(i⊕j) = ε(i, j)``, where ``ε`` is 0 for ``+1``
and 1 for ``-1``? Solved through the shipped
:func:`~srmech.math.modular_linalg.gf_rref` over GF(2), one row per ordered
basis pair, columns ``t(0..dim-1)``::

    dim                     2     4     8    16     32     64
    rank(A) / rank([A|b])  1/2   2/3   5/6  12/13  27/28  58/59
    nullity(A)              1     2     3     4      5      6   = log2(dim)

``rank([A|b]) = rank(A) + 1`` at EVERY rung: the system is inconsistent
everywhere, so no such ``t`` exists at any dim. The sign is therefore an
IRREDUCIBLE datum, not a representational one.

⚠️ **It read "an irreducible COHOMOLOGICAL datum" through rc464; corrected
rc465 (`#T1188`), and the measurement above is untouched.** What is measured is
that ε is not a COBOUNDARY at any rung, which is exactly what "no such ``t``
exists" says. Being cohomological additionally requires ε to be a COCYCLE, and
it is one only at ℝ/ℂ/ℍ: the committed census has ``δε ≠ 0`` from 𝕆 up (168
failing triples at 𝕆, 1848 at 𝕊). So above the Hurwitz wall the invariant is
ε's class in ``C²/B²`` — a cochain modulo coboundaries — and not a class in
``H²``. Nor is there a nonzero obstruction class one rung up: the associator
sign φ = δε is a coboundary BY CONSTRUCTION, so ``[φ] = 0`` in ``H³`` at every
rung, which the source states outright (Albuquerque & Majid, arXiv:math/9802116
§1 — for the octonions the cocycle is a coboundary, identified as the twisting
of a group algebra by a 2-cochain). What turns on at 𝕆 and degrades at 𝕊 is the
COCHAIN'S VALUES, not a class. ⚠️ That is a correction of NAMING and must not be
read as "nothing is frame-independent": the rank pair, ``nullity = log2(dim)``,
the associator support ladder (0, 0, 168, 1848, 15960) and the diagonal
``q(x) = ε(x, x)`` are all measured and all invariant. There IS frame-independent
content; it is not a cohomology class.

Two encoding notes, because the raw ranks are not self-describing and a
half-quoted table is not reproducible:

* ``nullity(A) = log2(dim)`` exactly. The homogeneous solutions are precisely
  the GF(2)-LINEAR functionals on ``(ℤ/2)^d``, so ``rank(A) = dim - log2(dim)``
  in closed form. That is the invariant worth quoting; the rank pair is the
  frame-relative shadow of it.
* **There is no gauge freedom here to fix.** ``t(e₀) = 0`` is a THEOREM of the
  system, not a convention imposed on it: ``e₀·e₀ = +e₀``, so the ``(i, j) =
  (0, 0)`` row IS literally ``t(e₀) = 0``. Adding it as an extra constraint
  changes no rank (measured). Eliminating the variable instead — substituting
  ``t(e₀) = 0`` and dropping column 0 — shifts BOTH ranks down by exactly one
  (0/1, 1/2, 4/5, 11/12, 26/27, 57/58) because that redundant row leaves with
  it. Same system, same conclusion, different matrix. The ``+1`` defect that
  carries the result is invariant under both.

This is why this module carries the sign explicitly — :func:`cd_navmap`
returns ``(k, sign)`` per slot rather than an index alone, and the sign branch
is a Class-K pin-slot composed with the Class-C
:func:`~srmech.cascade.chiral_flip`. It is also why
:func:`~srmech.math.hdc.bind` — a component-wise XOR, the index lane with the
sign channel absent — is commutative, associative and self-inverse at every
width while Cayley–Dickson turn-composition is none of those above dim 4.
``bind`` is the coboundary-free shadow of the same product.

The address namespace is a PARAMETER, and that is load-bearing
--------------------------------------------------------------
A register's minted addresses are content-derived from a **name**:
``mint_vector(f"{namespace}:e{slot}", D=D)``. Different namespaces mint different
address hypervectors, which at capacity-starved ``D`` produce different crosstalk —
and therefore different read-collision patterns. This is not a nuisance; it is the
mechanism, and exposing ``namespace`` is what lets this register **reproduce the
16-slot instrument bit-exactly** rather than merely resemble it::

    CDRegister(dim=16, namespace="SEDENION")   ==   the 16-slot register, byte-for-byte

byte-for-byte on every read, at **every** ``D`` including the starved regime where
both fall short of 120/120. That is a strictly stronger gate than "agrees once
capacity is adequate", and it is the reason the low-``D`` divergence reported by the
out-of-tree research register (119/120 vs the shipped 116/120 at ``D=256``) is fully
explained: it was the address-name mint and nothing else. The ordering even
**reverses** at ``D=320``/``D=384`` (shipped 120/120, ``CD16`` 118–119/120), and a
sweep of twelve arbitrary namespaces at ``D=256`` spans 116..120 with ``SEDENION``
inside the spread — so "the research register scored better" was never a property of
that register. It was which minted address set happened to collide less at one
starved capacity. See ``tests/test_cd_register_rc297.py::test_low_d_divergence_is_
entirely_the_address_name_mint``.

Two distinct boundaries, kept distinct (inherited from F465): the register's
**associative** capacity is ``D``-bounded (HDC crosstalk, and 32 slots need more
capacity than 16 do), separate from the **reversible working set** (≤7, the
octonion coupler). A shortfall at fixed ``D`` is a capacity fact, never an algebra
fact — always sweep ``D``.

numpy-FREE, and no ``abs()``: storage routes through
:func:`~srmech.signal_processing.mint_vector` + the Class-M
:func:`~srmech.math.hdc.bind` / ``bundle`` / ``similarity`` cascades; the sign
branch is an explicit **Class-K pin-slot** composed with a **Class-C**
:func:`~srmech.cascade.chiral_flip`
(``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).

SSoT / provenance: UPSTREAM_NOTES §31; F465 / F468 (the 16-slot instrument);
F1273 (addressing intact at 𝕊); F1274 (the involution mechanism — reversibility runs
on involution + a Class-C sign, never on division); F1275 (addressing survives
completely at 𝕋(32)). Hurwitz (1898); Baez arXiv:math/0105155; Kanerva (2009)
*Hyperdimensional Computing*.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from .cayley_dickson import (
    cd_basis_product,
    left_mult_is_invertible,
    cd_norm_sq,
    cd_conjugate,
    cd_mult,
    cd_add,
    CD_MAX_DIM,
)
from .hamming import hamming_encode, hamming_decode_correct
from . import chiral_flip
from srmech import _native
from srmech.math.q import Q

#: Default hypervector width (bits) — the RBS-HDC associative-register dimension.
DEFAULT_D = 8192
#: The reversible working-word cap (the octonion's 7 imaginary slots; Hurwitz).
WORKING_WORD_CAP = 7
#: The octonion working block is always the first 8 slots, at every rung.
WORKING_BLOCK_DIM = 8


def _lazy_hdc():
    """Import the Class-M HDC byte ops on demand (numpy-free; defers the import
    so the module loads without touching signal_processing)."""
    from ..math.hdc import bind, bundle, similarity
    return bind, bundle, similarity


def _lazy_mint():
    """Import the RBS-HDC minter on demand (numpy-free cascade; deferred import)."""
    from ..signal_processing import mint_vector
    return mint_vector


def _is_pow2(n: int) -> bool:
    return n >= 1 and (n & (n - 1)) == 0


def _check_dim(dim: int) -> int:
    """A register's slot count is a Cayley–Dickson algebra dimension: a power of
    two in ``[1, CD_MAX_DIM]``. ``CD_MAX_DIM`` is a TOOLING bound, not a
    mathematical one — the CD construction defines ``e_i·e_j = ±e_k`` at every
    rung; srmech simply does not build tables above it."""
    if type(dim) is not int or not _is_pow2(dim) or dim > CD_MAX_DIM:
        raise ValueError(
            f"dim must be a power of two in [1, {CD_MAX_DIM}] (a Cayley–Dickson "
            f"algebra dimension: 1 ℝ / 2 ℂ / 4 ℍ / 8 𝕆 / 16 𝕊 / 32 𝕋 / 64 / "
            f"128 / 256); "
            f"got {dim!r}"
        )
    return dim


def _working_cap(dim: int) -> int:
    """The reversible working-word capacity at ``dim`` — the number of values that
    can be bound into one reversible working word.

    ``min(WORKING_BLOCK_DIM, dim) − 1`` = ``min(dim, 8) − 1``: the imaginary-slot
    count of the largest normed-division-algebra block that fits. It is the
    DERIVED, dim-scaled form of the sedenion's flat ``WORKING_WORD_CAP = 7``.
    Hurwitz (1898): division algebras exist only at dim 1/2/4/8 (imaginary units
    0/1/3/7). Below 8 the cap is the algebra's own imaginary count (dim 2 → 1,
    dim 4 → 3); at/above 8 it PINS at 7 because ``e0..e7`` is an octonion
    subalgebra of every higher rung — a reversible word survives there but cannot
    grow. dim 1 (ℝ) → 0 = the degenerate pure-addressing base (no coupling)."""
    return min(WORKING_BLOCK_DIM, _check_dim(dim)) - 1


def cd_navmap(dim: int, j: int) -> Dict[int, Tuple[int, int]]:
    """The signed pointer-advance permutation for right-multiply-by-``e_j`` over
    ``dim`` slots: maps each slot ``i`` to ``(k, sign)`` where ``e_i·e_j =
    sign·e_k`` (the :func:`cd_basis_product` cocycle).

    The general-rung form of the removed 16-slot register's ``navmap``; at
    ``dim=16`` it is bit-identical to its RECORD
    (``tests/sedenion_register_golden_rc464.ndjson``). Always a signed permutation — reversible at **every**
    rung for a single basis direction, including past the Hurwitz wall (F1275).

    Dispatches to the ``srmech_cd_navmap`` C peer when ``HAS_NATIVE``; the pure
    :func:`cd_basis_product` loop below is the fallback + parity oracle.
    """
    _check_dim(dim)
    if type(j) is not int or not (0 <= j < dim):
        raise ValueError(f"navigation basis j must be an int in [0, {dim}); got {j!r}")
    native = _native.cd_navmap_c(dim, j)
    if native is not None:
        return native
    return {i: cd_basis_product(dim, i, j) for i in range(dim)}


def cd_navigate(dim: int, j: int,
                slots: Sequence[int],
                signs: Sequence[int]) -> Tuple[List[int], List[int]]:
    """Route occupied ``(slot, sign)`` records through the ``×e_j`` permutation at
    ``dim`` slots, composing the **Class-C** signs: returns
    ``(out_slots, out_signs)`` with ``out_signs[m] = signs[m] * s`` where
    ``e_{slots[m]}·e_j = s·e_{out_slots[m]}``.

    The numeric core of :meth:`CDRegister.navigate` (the key strings ride
    alongside in the caller). Dispatches to the ``srmech_cd_navigate`` C peer when
    ``HAS_NATIVE``; the pure loop is the fallback + parity oracle.
    """
    _check_dim(dim)
    if type(j) is not int or not (0 <= j < dim):
        raise ValueError(f"navigation basis j must be an int in [0, {dim}); got {j!r}")
    sl = [int(s) for s in slots]
    sg = [int(g) for g in signs]
    if len(sl) != len(sg):
        raise ValueError(
            f"slots and signs must be the same length; got {len(sl)} and {len(sg)}")
    for s, g in zip(sl, sg):
        if not (0 <= s < dim):
            raise ValueError(f"slot {s} is outside the e0..e{dim - 1} address space")
        if g not in (1, -1):
            raise ValueError(f"sign must be +1 or -1 (Class C); got {g}")
    native = _native.cd_navigate_c(dim, j, sl, sg)
    if native is not None:
        return native
    out_slots: List[int] = []
    out_signs: List[int] = []
    for s, g in zip(sl, sg):
        k, sign = cd_basis_product(dim, s, j)
        out_slots.append(k)
        out_signs.append(g * sign)          # compose the Class-C signs
    return (out_slots, out_signs)


def cd_navmap_is_signed_permutation(dim: int) -> bool:
    """**The structural invariant addressing rides on**, checked rather than
    assumed (F1274 / F1275): for *every* direction ``j`` in ``[0, dim)``, is
    ``i → (dest, sign)`` a bijection on ``[0, dim)`` with every sign in
    ``{+1, -1}``?

    This is the property that makes a general N-slot register legitimate past the
    Hurwitz boundary. Composition (norm-multiplicativity) fails at ``dim ≥ 16``
    and fails for ~95% of generic pairs at ``dim = 32``; addressing is untouched,
    because zero divisors are built from **sums** of basis elements while this
    property is about a **single** basis pair. The two are disjoint.

    **Scope, stated so it is not over-read:** this verifies the bijection +
    sign-domain property of the navmap *as computed by the*
    :func:`cd_basis_product` *cocycle*. It does not independently re-derive
    ``e_i·e_j`` from a full Cayley–Dickson multiplication — that cross-path check
    (cocycle shortcut vs full :func:`~srmech.cascade.cayley_dickson.cd_mult`,
    4096/4096 basis pairs at ``dim=64``) is enforced in
    ``tests/test_cd_register_rc297.py``.

    Dispatches to the ``srmech_cd_navmap_is_signed_permutation`` C peer when
    ``HAS_NATIVE``; the pure loop is the fallback + parity oracle.
    """
    _check_dim(dim)
    native = _native.cd_navmap_is_signed_permutation_c(dim)
    if native is not None:
        return native
    for j in range(dim):
        seen = set()
        for i in range(dim):
            k, sign = cd_basis_product(dim, i, j)
            if not (0 <= k < dim) or sign not in (1, -1):
                return False
            if k in seen:
                return False                # a collision — not a bijection
            seen.add(k)
    return True


# ── the OPT layers as pure functions: reversible coupling + Hamming EC ─────────
# These are the dim-scaled generalisations of the four value-operations the
# removed 16-slot register carried, mirroring how cd_navmap(dim, j) generalises the 16-slot navmap.
# They compose the already-C-backed hypercomplex_couple / hamming primitives — no
# new algebra, no new C symbol (composition_of_c, exactly like the sed_* peers).

def cd_couple_working(vals: Sequence, dim: int = WORKING_BLOCK_DIM) -> "List[float] | List[Q] | list":
    """Bind ``≤ min(dim, 8) − 1`` real streams into one reversible working word —
    the canonical Class-M **bind** on the Cayley–Dickson register (rc301, `#T938`).

    The dim-scaled generalisation of the removed 16-slot register's ``couple_working``: the
    cap is read from :func:`_working_cap` (``min(dim, 8) − 1``), never a hardcoded
    7. dim 2 couples 1 imaginary slot, dim 4 couples 3, dim 8/16/…/256 couple 7
    (the octonion sub-block; Hurwitz). dim 1 (ℝ) couples nothing — the degenerate
    base — so an empty ``vals`` returns ``[]`` and any value raises.

    Composes :func:`~srmech.cascade.hypercomplex_couple` (``axis="diagonal"``,
    the F436 coupling axis) — the reversible ``(σ, θ, μ)`` coupler whose octonion
    multiply already dispatches to the standalone-C
    ``srmech_hypercomplex_couple_q61``. Reversed exactly by
    :func:`cd_uncouple_working`. No ``abs()``; the coupler's sign is Class-K ∘
    Class-C internally.

    Parameters
    ----------
    vals : sequence of float
        ``≤ min(dim, 8) − 1`` real streams to fold into the working word.
    dim : int
        The register rung (a power of two in ``[1, CD_MAX_DIM]``); sets the cap.
        Default 8 (the octonion working word — cap 7).

    Returns
    -------
    list[float] | list[Q] | list[Qalg]
        The coupled working word — a 4-component quaternion (≤3 streams) or
        8-component octonion (4–7 streams); ``[]`` when nothing is coupled.
        A pass-through of :func:`hypercomplex_couple`, so its carrier rule and
        its accuracy statement ARE the contract here (rc466 / rc468, `#T1188`).
        This op fixes ``axis='diagonal'`` and takes the coupler's DEFAULT phase,
        which since rc468 is the exact rational quarter turn rather than
        ``fl(π/2)`` — so exact ``vals`` (``int`` / ``Q`` leaves) return
        ``list[Qalg]`` over ``ℚ(ζ₁₂)``, EXACT, with the diagonal axis's
        ``1/√3`` carried in the field instead of rounded onto the ``2**-61``
        grid. Float ``vals`` return ``list[float]`` on the fixed-point route,
        **accurate to round-off** — whose phase is now exact too, leaving the
        irrational axis as its one remaining bound.
    """
    cap = _working_cap(dim)
    if len(vals) > cap:
        raise ValueError(
            f"the reversible working word at dim {dim} holds ≤{cap} values "
            f"(min(dim, 8) − 1; the largest division-algebra block's imaginary "
            f"slots, capped by Hurwitz). Got {len(vals)} — spill the overflow to "
            f"the EC/carry block via cd_carry()."
        )
    if not vals:                    # dim 1, or an empty request: couple nothing
        return []
    from . import hypercomplex_couple
    return hypercomplex_couple(list(vals), axis="diagonal")


def cd_uncouple_working(word: Sequence) -> "List[float] | List[Q] | list":
    """Recover the streams bound by :func:`cd_couple_working` — the inverse
    twiddle (the Class-M **unbind**; rc301, `#T938`).

    Applies the conjugate twiddle (``inverse=True``) and drops the anchor slot,
    returning the carrier's imaginary components (``word[1:]``): 7 for an octonion
    word, 3 for a quaternion word. Empty in → empty out (the dim-1 boundary).

    **Accuracy (rc466 / rc468, `#T1188`) — two routes, stated separately.** The
    word's own leaves pick the carrier (a pass-through of
    :func:`hypercomplex_couple`): an EXACT word (``int`` / ``Q`` / ``Qalg``
    leaves) returns ``list[Qalg]`` over ``ℚ(ζ₁₂)``; a float word returns
    ``list[float]``.

    ✅ **The exact round trip is now BIT-EXACT at the DEFAULT phase** (rc468).
    Through rc467 it was exact only at ``theta = 0.0``, because the op ran the
    default ``fl(π/2)`` fold on the ``'diagonal'`` axis and the recovery carried
    the twiddle-norm residue ``‖T‖² − 1`` of the identity ``T̄·(T·q) = ‖T‖²·q``
    (F437). **That residue was the AXIS, not the trig** (rc466 review fix):
    ``‖T‖² = cos² + sin²·‖μ‖²``, the Q61 ``cos²+sin²`` sat within one grid
    unit of the unit, and the equal-weight axis ``(i+j+k)/√3`` was normalised
    in float64 before its projection to Q61 — measured ``‖μ_q61‖² − 1 =
    2.7e-16 = 620`` grid units, so ``uncouple(couple([2**60+1, 2, 3]))[0] −
    (2**60+1)`` was ``309.8``. On the exact carrier the axis is no longer
    normalised in float at all — ``1/√3`` is carried in the field — so
    ``‖T‖² == 1`` exactly and that same expression is now exactly ``0``.

    On the FLOAT carrier both statements above still hold as written: the axis
    is still float-normalised onto the ``2**-61`` grid and the recovery is
    **accurate to round-off**. What changed there is the PHASE, which is now the
    exact quarter turn in both projections (``srmech_hypercomplex_couple_turn_q61``)
    rather than ``cos``/``sin`` of ``fl(π/2)``. Through rc465 this docstring said
    "exact to float round-off"; the float half of that sentence was the whole
    story."""
    if not word:                    # the dim-1 empty-coupling boundary
        return []
    from . import hypercomplex_couple
    rec = hypercomplex_couple(list(word), axis="diagonal", inverse=True)
    return list(rec)[1:]            # drop the anchor; keep the imaginary slots


def cd_carry(overflow_bits: Sequence[int], n: int = 3) -> List[int]:
    """Encode overflow bits (past the reversible working set) into a Hamming(2ⁿ−1)
    single-error-correcting GF(2) codeword — the EC/carry layer (rc301, `#T938`).

    The EC axis is INDEPENDENT of the register's ``dim``: the block size is set by
    ``n`` (parity-bit count; codeword ``2ⁿ−1``, data ``2ⁿ−1−n``), not by the slot
    count. Composes :func:`~srmech.cascade.hamming_encode` (the
    ``srmech_hamming_encode`` C peer). Lean-ALU XOR; no float, no ``abs()``."""
    return hamming_encode(overflow_bits, n)


def cd_correct(codeword: Sequence[int]) -> Dict[str, Any]:
    """Locate + correct a single-bit error in an EC-block codeword and recover the
    carried payload — the EC/carry layer's read (rc301, `#T938`).

    Dispatches to the ``srmech_hamming_decode_correct`` C peer when HAS_NATIVE —
    the whole locate + correct + extract in ONE C call. The pure
    :func:`~srmech.cascade.hamming_decode_correct` (whose syndrome dispatches to
    ``srmech_hamming_syndrome``) is the fallback AND the parity oracle, and it is
    what raises the exact ``ValueError`` for a codeword whose length is not
    2ⁿ−1 — the native wrapper returns ``None`` for that input rather than
    guessing, so the error text comes from one place either way.

    ⚠️ rc464 (`#T1188`): this probe is NOT new behaviour, it is RESTORED. The
    16-slot register's ``sed_correct`` carried it from rc199, and subsuming that
    op into this one dropped it — leaving ``srmech_hamming_decode_correct``
    exported with a live ctypes wrapper and ZERO Python claimants, which is the
    dead-exported-surface shape this rc removed three other symbols to avoid.
    Rosetta kept reading ``composition_of_c`` throughout, because the syndrome
    call underneath is genuinely C, so nothing gated the loss of the whole-op
    route.

    Returns ``{"data", "error_position", "corrected_codeword"}``.
    Single-error-correcting (minimum distance 3). Lean-ALU XOR; no float, no
    ``abs()``."""
    native = _native.hamming_decode_correct_c(codeword)
    if native is not None:
        return native
    return hamming_decode_correct(codeword)


class CDRegister:
    """**THE** addressable RBS-HDC register (rc464: the preferred shape) — an
    **N-slot** Cayley–Dickson register over ``dim`` slots, any power of two in
    ``[1, CD_MAX_DIM]``. The slot count is a CONSTRUCTOR PARAMETER, so there is
    one register object for every rung instead of one class per rung.

    Storage is content-keyed: :meth:`write` records ``slot → (key, sign)`` and
    materialises the associative bundle on demand; :meth:`read` unbinds by the
    slot's address and cleans against the codebook.

    ``namespace`` selects the address-mint namespace (default ``f"CD{dim}"``).
    Setting ``namespace="SEDENION"`` at ``dim=16`` reproduces the 16-slot
    sedenion instrument srmech shipped before this class **bit-exactly at every**
    ``D`` — that is the faithfulness gate this class is held to (against that
    register's RECORD, ``tests/sedenion_register_golden_rc464.ndjson``), and it
    is why the parameter exists. The full subsuming spelling adds the two OPT
    layers, which the 16-slot class carried unconditionally:
    ``CDRegister(16, namespace="SEDENION", coupling=True, error_correction=True)``.

    Three layers (rc301, `#T938`): the CORE **addressing** layer is always on and
    content-AGNOSTIC — ``navmap`` is a pure function of ``dim``, storage holds
    anything, KIND is dimension-invariant. Alongside it (rc330, `#948`) the CORE
    **carrier-arithmetic** surface is likewise always on: :meth:`element` /
    :meth:`norm` / :meth:`conjugate` / :meth:`multiply` / :meth:`add` read the
    signed-basis element ``Σ sign_i·e_i`` a register holds and DELEGATE to the
    exact-``Q`` :mod:`~srmech.cascade.cayley_dickson` ops over it (the
    method-form of ``cd_norm_sq`` / ``cd_conjugate`` / ``cd_mult`` / ``cd_add``,
    no new algebra). Two OPT layers are off by default:
    ``coupling=True`` adds the reversible working word (:meth:`couple_working` /
    :meth:`uncouple_working`, Class M, capped at ``min(dim, 8) − 1`` by Hurwitz);
    ``error_correction=True`` adds the Hamming EC block (:meth:`carry` /
    :meth:`correct`, an axis independent of ``dim``). A bare register (both off) is
    a pure signed-pointer addressing object and raises on the value-operations.

    Capacity note: the associative capacity is ``D``-bounded, and **more slots
    need more** ``D``. A dim-32 shortfall at a ``D`` adequate for dim-16 is a
    capacity fact, not an algebra fact. Sweep ``D``; never report a single point.
    """

    def __init__(self, dim: int, D: int = DEFAULT_D,
                 codebook: Optional[Dict[str, bytes]] = None,
                 minter=None, namespace: Optional[str] = None,
                 coupling: bool = False, error_correction: bool = False):
        self.dim = _check_dim(dim)
        self.D = int(D)
        self.namespace = str(namespace) if namespace is not None else f"CD{self.dim}"
        self.codebook: Dict[str, bytes] = dict(codebook or {})
        self._minter = minter
        self._addr_cache: Dict[int, bytes] = {}
        self._slots: Dict[int, Tuple[str, int]] = {}   # slot -> (key, sign∈{±1})
        # The two OPTIONAL layers, off by default (a bare register is pure
        # signed-pointer addressing — the CORE layer only). Opting in EXPOSES the
        # value-operations; a bare register raises on them (they are gated, not
        # merely unused). The flags allocate no per-instance state — the coupling /
        # EC ops are pure functions of their arguments, not of the slot-map.
        self._coupling = bool(coupling)
        self._error_correction = bool(error_correction)

    # ── address + codebook minting (numpy-free cascade; deferred import) ──
    def _mint(self, name: str) -> bytes:
        if self._minter is None:
            self._minter = _lazy_mint()
        return self._minter(name, D=self.D)

    def _addr(self, slot: int) -> bytes:
        if slot not in self._addr_cache:
            self._addr_cache[slot] = self._mint(f"{self.namespace}:e{slot}")
        return self._addr_cache[slot]

    def _value_vec(self, key: str, sign: int) -> bytes:
        if key not in self.codebook:
            self.codebook[key] = self._mint(f"VAL:{key}")
        vec = self.codebook[key]
        return vec if sign >= 0 else chiral_flip(vec)   # Class C sign; never abs()

    def _check_slot(self, slot: int) -> int:
        if type(slot) is not int or not (0 <= slot < self.dim):
            raise ValueError(
                f"slot must be an int in [0, {self.dim}) (the e0..e{self.dim - 1} "
                f"address space); got {slot!r}"
            )
        return slot

    # ── the block structure, at every rung ────────────────────────────────
    def working_block(self) -> Tuple[int, ...]:
        """``e0..e7`` — the octonion reversible working block, truncated if
        ``dim < 8``. The Hurwitz cap is 7 imaginary slots at EVERY rung: going to
        32 or 64 slots buys address space, never a longer reversible word."""
        return tuple(range(0, min(WORKING_BLOCK_DIM, self.dim)))

    def carry_block(self) -> Tuple[int, ...]:
        """``e8..e{dim-1}`` — everything past the reversibility horizon. The
        Hamming GF(2) EC half rides over this block via :meth:`carry` / :meth:`correct`
        (opt in with ``error_correction=True``)."""
        return tuple(range(WORKING_BLOCK_DIM, self.dim))

    # ── OPT layer 1: the reversible working word (Class M; opt-in coupling) ────
    def _require_coupling(self) -> None:
        """Gate the coupling layer — a bare register is pure addressing."""
        if not self._coupling:
            raise ValueError(
                "this CDRegister was constructed for pure addressing "
                "(coupling=False). Reconstruct with coupling=True to bind values "
                "into the reversible working word (couple_working / uncouple_working)."
            )

    def couple_working(self, vals: Sequence) -> "List[float] | List[Q]":
        """Bind ``≤ len(working_block()) − 1`` values into one reversible working
        word — THE canonical Class-M bind (rc301). Reads the dim-scaled cap
        (``min(dim, 8) − 1``), never a hardcoded 7: dim 2 couples 1, dim 4 couples
        3, dim 8/16/…/256 couple 7, dim 1 couples nothing. Requires ``coupling=True``.

        Delegates to :func:`cd_couple_working` — at dim 16 this is bit-exact with
        the removed 16-slot register's ``couple_working`` as RECORDED in
        ``tests/sedenion_register_golden_rc464.ndjson`` (the faithfulness gate)."""
        self._require_coupling()
        return cd_couple_working(vals, self.dim)

    def uncouple_working(self, word: Sequence) -> "List[float] | List[Q]":
        """The exact inverse of :meth:`couple_working` — recover the streams
        (Class-M unbind; rc301). Requires ``coupling=True``. Delegates to
        :func:`cd_uncouple_working`."""
        self._require_coupling()
        return cd_uncouple_working(word)

    # ── OPT layer 2: the Hamming EC / carry block (opt-in error_correction) ────
    def _require_error_correction(self) -> None:
        """Gate the EC layer — a bare register is pure addressing."""
        if not self._error_correction:
            raise ValueError(
                "this CDRegister was constructed for pure addressing "
                "(error_correction=False). Reconstruct with error_correction=True "
                "to use the Hamming EC/carry block (carry / correct)."
            )

    def carry(self, overflow_bits: Sequence[int], n: int = 3) -> List[int]:
        """Encode overflow bits into a Hamming(2ⁿ−1) EC codeword (rc301). The EC
        block size is set by ``n`` (default 3) INDEPENDENT of ``dim``. Requires
        ``error_correction=True``. Delegates to :func:`cd_carry`."""
        self._require_error_correction()
        return cd_carry(overflow_bits, n=n)

    def correct(self, codeword: Sequence[int]) -> Dict[str, Any]:
        """Locate + correct a single-bit error in an EC codeword and recover the
        payload (rc301). Requires ``error_correction=True``. Delegates to
        :func:`cd_correct`."""
        self._require_error_correction()
        return cd_correct(codeword)

    # ── associative storage (Class M; D-bounded capacity) ─────────────────
    def write(self, slot: int, key: str, *, sign: int = 1) -> None:
        """Store ``key`` (a content name) at slot ``e{slot}`` with a Class-C
        ``sign``. ``bind(ADDR[slot], value)`` enters the bundle on
        materialisation."""
        self._check_slot(slot)
        self._value_vec(str(key), 1 if sign >= 0 else -1)   # ensure minted
        self._slots[slot] = (str(key), 1 if sign >= 0 else -1)

    def materialize(self) -> bytes:
        """The associative superposition — ``bundle_k bind(ADDR[k], value_k)``."""
        bind, bundle, _ = _lazy_hdc()
        parts = [bind(self._addr(k), self._value_vec(key, sgn))
                 for k, (key, sgn) in sorted(self._slots.items())]
        if not parts:
            raise ValueError("register is empty — write at least one slot first")
        if len(parts) == 1:
            return parts[0]
        if len(parts) % 2 == 0:                 # bundle needs odd N (no tie)
            parts = parts + [self._mint("__pad__")]
        return bundle(parts)

    def read(self, slot: int) -> Tuple[Optional[str], int]:
        """Unbind slot ``e{slot}`` from the bundle and nearest-codebook clean.
        Returns ``(key, sign)`` — the recovered content name + its Class-C sign
        (``(None, +1)`` if the register is empty / nothing matches)."""
        self._check_slot(slot)
        bind, _, similarity = _lazy_hdc()
        if not self.codebook or not self._slots:
            return (None, 1)
        noisy = bind(self._addr(slot), self.materialize())
        best_key, best_sign, best_mag = None, 1, -1.0
        for key, vec in self.codebook.items():
            if key == "__pad__":
                continue
            s_pos = similarity(noisy, vec)
            s_neg = similarity(noisy, chiral_flip(vec))
            # Class-K magnitude — the explicit pin-slot sign-branch, never
            # ``abs()`` (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
            # Deliberately the INLINE branch rather than cascade.magnitude: the
            # faithfulness gate is bit-identity with the removed 16-slot
            # register's RECORDED branch, and magnitude() carries a NaN→0.0
            # dead-band that that branch did not. Unreachable for a byte-vector
            # similarity, but the gate is bit-identity, not
            # identity-in-practice. The winning polarity rides separately as
            # ``best_sign`` (Class C).
            mag_pos = s_pos if s_pos >= 0.0 else -s_pos
            mag_neg = s_neg if s_neg >= 0.0 else -s_neg
            if mag_pos >= best_mag:
                best_key, best_sign, best_mag = key, 1, mag_pos
            if mag_neg > best_mag:
                best_key, best_sign, best_mag = key, -1, mag_neg
        return (best_key, best_sign)

    def slots(self) -> Dict[int, Tuple[str, int]]:
        """A copy of the current ``slot → (key, sign)`` assignment."""
        return dict(self._slots)

    # ── CORE carrier-arithmetic surface: the slot-held CD element (rc330; `#948`) ─
    # A register slot holds a content NAME + a Class-C sign, magnitude implicit 1,
    # so the natural Cayley–Dickson element a register HOLDS is the signed-basis-
    # unit sum  x = Σ_{i occupied} sign_i·e_i  (coefficients in {-1, 0, +1}). These
    # read-only methods DELEGATE the exact-rational CD arithmetic to the already-
    # C-backed cayley_dickson.cd_* ops over that element — no new algebra, no new
    # C symbol, no ToolEntry (composition_of_c, exactly like couple_working is the
    # method-form of cd_couple_working). Always on (CORE), content-agnostic: the
    # KEY (content name) is orthogonal to the carrier reading — the arithmetic
    # reads only (index, sign) via slots().

    def element(self) -> Tuple[Q, ...]:
        """The slot-held Cayley–Dickson element as a length-``dim`` exact-``Q``
        tuple: ``v[i] = Q(sign_i)`` at occupied slots, ``Q(0)`` elsewhere (rc330,
        `#948`). The accessor the other carrier methods read; the register's KEY
        strings are orthogonal to it — only ``(index, sign)`` enters the carrier."""
        v = [Q(0)] * self.dim
        for slot, (_key, sign) in self._slots.items():
            v[slot] = Q(int(sign))
        return tuple(v)

    def norm(self) -> Q:
        """The squared norm ``N(x) = Σ xᵢ²`` of the slot-held element, as an exact
        ``Q`` scalar (rc330, `#948`). Delegates to
        :func:`~srmech.cascade.cayley_dickson.cd_norm_sq`. Since every occupied
        coefficient is ``±1``, this equals the number of occupied slots. Returns a
        ``Q``, not a register — a norm is a real scalar, not a CD element.

        **SCOPE (rc352, `#T1001`):** the register addresses the DEFINITE
        Cayley–Dickson ladder — its navmap is ``cd_basis_product``'s cocycle,
        with no γ parameter — so ``Σ xᵢ²`` IS ``Re(x·x̄)`` here. It is not the
        norm of a split twist; ``cd_norm_sq(x, gammas=…)`` is."""
        return cd_norm_sq(self.element())

    def conjugate(self) -> Tuple[Q, ...]:
        """The Cayley–Dickson conjugate ``x̄`` of the slot-held element as a
        ``Q``-tuple (rc330, `#948`). Delegates to
        :func:`~srmech.cascade.cayley_dickson.cd_conjugate` (negate the
        imaginary part; Class-K sign-flip, no ``abs()``). The conjugate of a
        signed-basis element is ALWAYS signed-basis — it only flips imaginary-slot
        signs — so this one *could* round-trip into a register; it is returned
        uniform with ``cd_conjugate`` as a ``Q``-tuple."""
        return cd_conjugate(self.element())

    def multiply(self, other: "CDRegister") -> Tuple[Q, ...]:
        """The Cayley–Dickson product ``x·y`` of this register's slot-held element
        with ``other``'s, as a raw ``Q``-tuple CD element (rc330, `#948`).
        Delegates to :func:`~srmech.cascade.cayley_dickson.cd_mult` (Class-M
        bind ∘ Class-C ∘ Class-K; no ``abs()``). ``other`` is another
        :class:`CDRegister` of the same ``dim`` (symmetric operands).

        Returns a ``Q``-tuple, NOT a register: the product of two signed-basis sums
        is GENERALLY NOT signed-basis (``e_i ⊕ e_j`` collisions make ``|coeff| >
        1``), so it cannot round-trip into a coefficient-free slot register. Past
        the Hurwitz wall this is a well-defined product even where norm-
        multiplicativity fails — at ``dim=16`` a zero-divisor pair (both nonzero)
        multiplies to the all-zero element, an object the ≤7 octonion coupler
        :meth:`couple_working` structurally cannot even accept, let alone produce."""
        if not isinstance(other, CDRegister):
            raise TypeError(
                f"multiply expects another CDRegister (symmetric operands); "
                f"got {type(other).__name__}")
        if self.dim != other.dim:
            raise ValueError(
                f"dim mismatch: {self.dim} vs {other.dim} — carrier multiply is "
                f"defined only between equal-rung elements")
        return cd_mult(self.element(), other.element())

    def add(self, other: "CDRegister") -> Tuple[Q, ...]:
        """The component-wise sum ``x + y`` of this register's slot-held element
        with ``other``'s, as a ``Q``-tuple (rc330, `#948`). Delegates to
        :func:`~srmech.cascade.cayley_dickson.cd_add`. ``other`` is another
        :class:`CDRegister` of the same ``dim`` (symmetric operands). Returned as a
        ``Q``-tuple: co-occupied slots sum to ``±2`` / ``0``, off the signed-basis
        set a register can round-trip, so the raw carrier element is returned."""
        if not isinstance(other, CDRegister):
            raise TypeError(
                f"add expects another CDRegister (symmetric operands); "
                f"got {type(other).__name__}")
        if self.dim != other.dim:
            raise ValueError(
                f"dim mismatch: {self.dim} vs {other.dim} — carrier add is defined "
                f"only between equal-rung elements")
        return cd_add(self.element(), other.element())

    # ── the operational hyper-loop: address↔CD homomorphism ───────────────
    def navmap(self, j: int) -> Dict[int, Tuple[int, int]]:
        """The pointer-advance permutation for right-multiply-by-``e_j`` over this
        register's ``dim`` slots (see :func:`cd_navmap`)."""
        return cd_navmap(self.dim, j)

    def navigate(self, j: int) -> "CDRegister":
        """Walk the hyper-loop: right-multiply every slot *name* by ``e_j`` so
        content at slot ``i`` moves to slot ``k`` with sign ``s``, ``e_i·e_j =
        s·e_k``. Returns a NEW register with the routed assignment, carrying the
        same ``dim`` / ``D`` / ``namespace``.

        The codebook is **copied, not aliased** — the constructor takes
        ``dict(codebook)``, so the minted value-vectors (immutable ``bytes``) are
        shared but later writes to the parent do NOT appear in the child. The
        removed 16-slot register behaved identically; its docstring's "shares
        the codebook" was imprecise about the mapping, and this one is the
        corrected wording that outlived it.

        ``navigate(j).navigate(j)`` is the global ``−1``
        (``e_j² = −1``), recoverable as a Class-C sign — the **involution**, which
        needs no norm and is therefore rung-independent (F1274)."""
        items = sorted(self._slots.items())
        out_slots, out_signs = cd_navigate(
            self.dim, j,
            [s for s, _ in items],
            [sgn for _, (_k, sgn) in items])
        out = CDRegister(dim=self.dim, D=self.D, codebook=self.codebook,
                         minter=self._minter, namespace=self.namespace,
                         coupling=self._coupling,
                         error_correction=self._error_correction)
        out._addr_cache = dict(self._addr_cache)
        keys = [k for _, (k, _sgn) in items]
        for m in range(len(items)):
            out._slots[out_slots[m]] = (keys[m], out_signs[m])
        return out

    def is_navigable(self, direction: Sequence[Any]) -> bool:
        """``True`` iff navigation along ``direction`` is reversible — i.e. left-
        multiplication by ``direction`` is invertible
        (:func:`left_mult_is_invertible`). A single basis ``e_j`` (a length-``dim``
        one-hot) is always navigable at every rung; a **composite** direction is
        navigable only ``≤𝕆`` — a zero-divisor direction is not."""
        return left_mult_is_invertible(direction)

    def __repr__(self) -> str:                              # pragma: no cover
        return (f"CDRegister(dim={self.dim}, D={self.D}, "
                f"namespace={self.namespace!r}, occupied={len(self._slots)})")


def cd_register(dim: int, D: int = DEFAULT_D,
                codebook: Optional[Dict[str, bytes]] = None,
                namespace: Optional[str] = None,
                coupling: bool = False,
                error_correction: bool = False) -> CDRegister:
    """Construct a :class:`CDRegister` — **the** addressable RBS-HDC register
    (rc297; `#934`. rc464: the preferred shape, and the only one). ``dim`` named
    slots ``e0..e{dim-1}`` for any power of two in ``[1, CD_MAX_DIM]``; ``e0..e7``
    is the octonion reversible working block at every rung and the remainder is
    the carry/EC block.

    The CORE **addressing** layer (``write`` / ``read`` / ``navmap`` / ``navigate``
    / ``is_navigable``) is always on and content-agnostic. The two OPTIONAL layers
    are off by default: ``coupling=True`` enables the reversible working word
    (``couple_working`` / ``uncouple_working``, Class M, capped at ``min(dim, 8) −
    1`` by Hurwitz); ``error_correction=True`` enables the Hamming EC block
    (``carry`` / ``correct``, a separate axis from ``dim``). A bare register is a
    pure signed-pointer addressing object.

    Subsumes the 16-slot sedenion instrument srmech shipped before it — the slot
    bound was the only difference; every sign and index rule is shared through
    :func:`cd_basis_product`. ``cd_register(16, namespace="SEDENION",
    coupling=True, error_correction=True)`` reproduces that register bit-exactly
    at every ``D``, gated against its record in
    ``tests/sedenion_register_golden_rc464.ndjson``.

    Legitimate past the Hurwitz wall because addressing rides on the basis product
    being a signed permutation, which zero divisors (built from *sums* of basis
    elements) do not touch — see :func:`cd_navmap_is_signed_permutation`.
    """
    return CDRegister(dim=dim, D=D, codebook=codebook, namespace=namespace,
                      coupling=coupling, error_correction=error_correction)


# ──────────────────────────────────────────────────────────────────────
# Flat cascade-op adapters — the make_class two-layer binding surface for
# ``cd_register.toml`` (the ``[class] CDRegister``; rc464, `#T1188` /
# [[feedback_prefer_config_driven_toml_classes]]).
#
# WHY THESE EXIST AND WHY THE PREFIX IS ``cdr_``. The module already exports
# eight FREE FUNCTIONS spelled ``cd_*`` (``cd_navmap`` / ``cd_navigate`` /
# ``cd_navmap_is_signed_permutation`` / the four OPT-layer ops / the
# ``cd_register`` constructor). Those are the general-rung cascade ops; they are
# NOT class-shaped — none of them takes or returns the declarative field-state
# a ``[class]`` method binds. The adapters below ARE class-shaped: each
# rehydrates a transient :class:`CDRegister` from the declarative fields and
# calls the existing method, so the TOML class is byte-identical to the Python
# class with no logic duplication (the genome / 16-slot-register two-layer
# pattern). A single ``cd_`` prefix would make the C vtable's ``strncmp`` branch
# match both families, which is why the two carry different prefixes rather
# than the same one at different arities.
#
# DECLARATIVE STATE = the seven fields ``dim`` / ``D`` / ``namespace`` /
# ``codebook`` / ``slots`` / ``coupling`` / ``error_correction``. The private
# ``_minter`` / ``_addr_cache`` caches are DROPPED exactly as the 16-slot
# descriptor drops them: minting is deterministic from ``(name, D)``, so the
# declarative form recomputes and the cache was a perf-only memo.
#
# DEFAULTS ARE APPLIED AT USE TIME, NOT AT DECLARATION. The ``[class]`` contract
# has no scalar field default — ``_field_default`` yields ``None`` for any type
# string that is not ``list*`` / ``dict*`` — so a class constructed with
# ``dim=`` alone arrives here with ``D=None``, ``namespace=None`` and both flags
# ``None``. :func:`_cdr_defaults` resolves them to ``DEFAULT_D`` / ``f"CD{dim}"``
# / ``False`` — the SAME rule the Python constructor applies, spelled once here
# so the two projections cannot drift. The FIELD itself passes through
# unchanged; only the USE is defaulted, so a round-tripped instance still
# reports the state it was constructed with.
#
# GATING IS PRESERVED, WHICH IS WHY THE FLAGS ARE BOUND. ``couple_working`` /
# ``uncouple_working`` / ``carry`` / ``correct`` are the two OPT layers, and the
# Python class RAISES on a bare register. The four existing free ops
# (``cd_couple_working`` etc.) are UNGATED pure functions by design, so binding
# the TOML methods straight to them would make the declarative class silently
# not raise where the Python class does — a behaviour fork wearing the name
# "conversion". The adapters below therefore bind ``coupling`` /
# ``error_correction`` from the fields and let the class's own ``_require_*``
# gate fire.
#
# THEY ARE REGISTERED, not allowlisted. Their 16-slot predecessors (``sed_*``)
# sit in the registry-completeness allowlist as OPEN_REGISTRATION rows on the
# stated ground that they are "reachable ONLY via the make_class class surface";
# copying that here was arithmetically unavailable (``CEIL_OPEN_REGISTRATION``
# is down-only and equality-asserted), and hiding them from ``__all__`` instead
# is the blind spot rc407 recorded — a shipped descriptor naming ops no census
# can see.
#
# The inherited "not wire-reachable" claim was also MEASURED rather than
# repeated, and it does not hold for this family: all fourteen answer through
# ``invoke_tool`` when the state is passed in its WIRE form — a slot map crosses
# JSON and the ``srmech_mval_t`` DICT as STR keys with LIST pairs, which is
# exactly what :func:`_cdr_rehydrate` normalises, and a codebook can cross EMPTY
# because the register mints value vectors on demand. So an empty codebook with
# an occupied slot map is a fully wire-expressible NON-EMPTY register.
# ``tests/test_wire_invocability_rc464.py`` drives every one of them that way
# and compares each answer against the same call made directly.
# ──────────────────────────────────────────────────────────────────────

def _cdr_defaults(dim, D, namespace, coupling, error_correction):
    """Resolve the declarative field values to constructor arguments — the ONE
    place the scalar defaults live for the TOML projection.

    ``dim`` is required (there is no sensible default rung). ``D`` →
    ``DEFAULT_D``, ``namespace`` → ``f"CD{dim}"``, and both OPT flags →
    ``False``, mirroring :meth:`CDRegister.__init__` exactly."""
    d = _check_dim(int(dim))
    return (
        d,
        DEFAULT_D if D is None else int(D),
        f"CD{d}" if namespace is None else str(namespace),
        bool(coupling),
        bool(error_correction),
    )


def _cdr_rehydrate(dim, D=None, namespace=None, codebook=None, slots=None,
                   coupling=None, error_correction=None) -> "CDRegister":
    """Build a transient :class:`CDRegister` from the declarative fields.

    Slot int-keys ride the ``srmech_mval_t`` DICT as STR ``"0".."255"`` one
    layer up (and a TOML table's keys are strings by construction), so
    ``int(k)`` normalises them here before anything numeric sees them."""
    d, dd, ns, cp, ec = _cdr_defaults(dim, D, namespace, coupling,
                                      error_correction)
    r = CDRegister(dim=d, D=dd, codebook=dict(codebook or {}), namespace=ns,
                   coupling=cp, error_correction=ec)
    r._slots = {int(k): (str(v[0]), int(v[1]))
                for k, v in dict(slots or {}).items()}
    return r


def cdr_write(slot, key, dim, D, namespace, codebook, slots, *, sign: int = 1):
    """``write`` (mutates): store content name ``key`` at slot ``e{slot}`` with a
    Class-C ``sign``. Returns ``(None, {"slots": ..., "codebook": ...})`` —
    minting the value vec grows the codebook, the slot-map records the
    assignment."""
    r = _cdr_rehydrate(dim, D, namespace, codebook, slots)
    r.write(slot, key, sign=sign)
    return (None, {"slots": dict(r._slots), "codebook": dict(r.codebook)})


def cdr_materialize(dim, D, namespace, codebook, slots):
    """``materialize``: the associative superposition bytes — ``bundle_k
    bind(ADDR[k], value_k)`` (Class-M; raises if the register is empty)."""
    return _cdr_rehydrate(dim, D, namespace, codebook, slots).materialize()


def cdr_read_unbind(slot, dim, D, namespace, codebook, slots):
    """``read`` CHAIN stage 1: unbind slot ``e{slot}``'s address from the bundle
    → the noisy vector (``None`` if the register is empty — the read
    short-circuit, which stage 2 turns into ``(None, +1)``)."""
    r = _cdr_rehydrate(dim, D, namespace, codebook, slots)
    r._check_slot(slot)
    if not r.codebook or not r._slots:
        return None
    bind, _, _ = _lazy_hdc()
    return bind(r._addr(slot), r.materialize())


def cdr_clean(noisy, codebook):
    """``read`` CHAIN stage 2: nearest-codebook clean → ``(key, sign)``.
    ``(None, +1)`` when ``noisy`` is absent (empty register).

    Class-K magnitude via an explicit pin-slot sign-branch, never ``abs()``; the
    winning polarity rides separately as the Class-C ``sign``. The branch is
    written INLINE rather than through ``cascade.magnitude`` for the same reason
    :meth:`CDRegister.read` writes it inline — ``magnitude()`` carries a NaN→0.0
    dead-band the register's branch does not, and the gate here is bit-identity,
    not identity-in-practice."""
    if noisy is None:
        return (None, 1)
    _, _, similarity = _lazy_hdc()
    best_key, best_sign, best_mag = None, 1, -1.0
    for key, vec in dict(codebook or {}).items():
        if key == "__pad__":
            continue
        s_pos = similarity(noisy, vec)
        s_neg = similarity(noisy, chiral_flip(vec))
        mag_pos = s_pos if s_pos >= 0.0 else -s_pos
        mag_neg = s_neg if s_neg >= 0.0 else -s_neg
        if mag_pos >= best_mag:
            best_key, best_sign, best_mag = key, 1, mag_pos
        if mag_neg > best_mag:
            best_key, best_sign, best_mag = key, -1, mag_neg
    return (best_key, best_sign)


def cdr_slots(slots):
    """``slots``: a copy of the ``slot → (key, sign)`` assignment, with the
    STR-keyed wire form normalised back to int keys. A pure reshape — it does
    NOT validate the slot domain, because :meth:`CDRegister.slots` does not
    either, and the contract here is byte-identity with that method rather than
    with a stricter one."""
    return {int(k): (str(v[0]), int(v[1]))
            for k, v in dict(slots or {}).items()}


def cdr_working_block(dim):
    """``working_block``: ``e0..e7`` — the octonion reversible working block,
    truncated when ``dim < 8``. The Hurwitz cap is 7 imaginary slots at EVERY
    rung; more slots buy address space, never a longer reversible word."""
    return _cdr_rehydrate(dim).working_block()


def cdr_carry_block(dim):
    """``carry_block``: ``e8..e{dim-1}`` — everything past the reversibility
    horizon, the block the Hamming EC half rides over."""
    return _cdr_rehydrate(dim).carry_block()


def cdr_couple_working(vals, dim, coupling):
    """``couple_working`` (GATED on ``coupling``): bind ``<= min(dim, 8) - 1``
    values into one reversible working word — the canonical Class-M bind. Raises
    the register's own ``ValueError`` when the class was constructed for pure
    addressing (``coupling`` false / absent). The carrier is the operand's
    (rc466 / rc468, `#T1188`): exact ``vals`` return ``list[Qalg]`` — EXACT
    over ``ℚ(ζ₁₂)`` at the default quarter turn on the diagonal axis — and
    float ``vals`` return ``list[float]`` **accurate to round-off** — see
    :func:`cd_couple_working`."""
    return _cdr_rehydrate(dim, coupling=coupling).couple_working(vals)


def cdr_uncouple_working(word, dim, coupling):
    """``uncouple_working`` (GATED on ``coupling``): the inverse twiddle of
    :func:`cdr_couple_working` — recover the streams (Class-M unbind). The
    carrier is the operand's (rc466 / rc468, `#T1188`). On the EXACT carrier the
    round trip is now bit-exact at the DEFAULT phase, not only at
    ``theta = 0.0``: the quarter turn and the diagonal axis's ``1/√3`` are both
    carried in ``ℚ(ζ₁₂)``, so ``uncouple(couple([2**60+1, 2, 3]))`` returns the
    operand with residue exactly ``0`` where the pre-rc468 default missed it by
    ``309.8``. On the FLOAT carrier the ``'diagonal'`` axis is still normalised
    in float64 before its Q61 projection (``‖μ_q61‖² − 1 = 2.7e-16``, ~620 grid
    units) and the recovery is **accurate to round-off**. See
    :func:`cd_uncouple_working`."""
    return _cdr_rehydrate(dim, coupling=coupling).uncouple_working(word)


def cdr_carry(overflow_bits, dim, error_correction, *, n: int = 3):
    """``carry`` (GATED on ``error_correction``): Hamming(2^n - 1)-encode
    overflow bits into the EC block. ``n`` is an axis INDEPENDENT of ``dim`` and
    rides as a pass-through call kwarg, not a bind — a bind would make it
    mandatory."""
    return _cdr_rehydrate(dim, error_correction=error_correction).carry(
        overflow_bits, n=n)


def cdr_correct(codeword, dim, error_correction):
    """``correct`` (GATED on ``error_correction``): locate + correct a single-bit
    error in an EC codeword and recover the payload."""
    return _cdr_rehydrate(
        dim, error_correction=error_correction).correct(codeword)


def cdr_element(slots, dim):
    """``element``: the slot-held Cayley–Dickson element as a length-``dim``
    exact-``Q`` tuple — ``v[i] = Q(sign_i)`` at occupied slots, ``Q(0)``
    elsewhere. The accessor the carrier chains read; the register's KEY strings
    are orthogonal to it, only ``(index, sign)`` enters the carrier."""
    return _cdr_rehydrate(dim, slots=slots).element()


def cdr_element_of(other, dim, *, verb: str = "multiply"):
    """The OTHER operand's slot-held element, for the symmetric carrier chains
    (``multiply`` / ``add``).

    The ``[class]`` contract resolves a bind from a call kwarg or a field and
    nothing else — there is no dotted operand-field resolution — so a same-class
    operand arrives as an opaque kwarg and this adapter is what reads it.
    Accepts a :class:`CDRegister`, a ``CatalogClass`` declaring the same fields,
    or a bare ``{"dim": ..., "slots": ...}`` state dict off the wire.

    ``verb`` is a STATIC stage kwarg supplied by the descriptor so the raised
    messages match :meth:`CDRegister.multiply` / :meth:`CDRegister.add`
    word-for-word; the dim check lives here, ahead of ``cd_mult`` / ``cd_add``,
    for the same reason it lives in those methods — an unequal-rung product is
    not a defined operation, and letting the length mismatch surface out of the
    algebra would report it as a different fault."""
    if isinstance(other, CDRegister):
        other_dim, other_slots = other.dim, other.slots()
    else:
        fields = getattr(other, "fields", None)
        if fields is None and isinstance(other, dict):
            fields = other
        if not isinstance(fields, dict) or "dim" not in fields:
            raise TypeError(
                f"{verb} expects another CDRegister (symmetric operands); "
                f"got {type(other).__name__}")
        other_dim, other_slots = fields["dim"], fields.get("slots")
    if int(other_dim) != int(dim):
        raise ValueError(
            f"dim mismatch: {int(dim)} vs {int(other_dim)} — carrier {verb} is "
            f"defined only between equal-rung elements")
    return cdr_element(other_slots, other_dim)


def cdr_navigate(j, dim, D, namespace, codebook, slots, coupling,
                 error_correction):
    """``navigate`` (returns="self"): walk the hyper-loop — right-multiply every
    slot name by ``e_j`` (the address <-> Cayley–Dickson homomorphism) → the NEW
    register's full seven-field state-dict. ``self`` is untouched.

    ALL SEVEN fields are emitted, not just the ones that move.
    ``_apply_returns`` constructs a FRESH instance from exactly this dict, and
    any field omitted from it resets to the contract's default — ``None`` for
    every scalar here — so a navigate that returned only ``{slots}`` would
    silently drop ``dim`` / ``D`` / ``namespace`` and both OPT flags off the
    routed register. That is also why this method sits at eight binds against
    ``MC_MAX_BINDS = 8`` in the C engine: seven fields plus ``j``, exactly at
    the cap, which the engine test asserts by requiring DISPATCH (an over-cap
    method silently DEFERS)."""
    r = _cdr_rehydrate(dim, D, namespace, codebook, slots, coupling,
                       error_correction)
    out = r.navigate(j)
    return {
        "dim": out.dim,
        "D": out.D,
        "namespace": out.namespace,
        "codebook": dict(out.codebook),
        "slots": dict(out._slots),
        "coupling": out._coupling,
        "error_correction": out._error_correction,
    }


__all__ = [
    "DEFAULT_D",
    "WORKING_WORD_CAP",
    "WORKING_BLOCK_DIM",
    "CDRegister",
    "cd_register",
    "cd_navmap",
    "cd_navigate",
    "cd_navmap_is_signed_permutation",
    "cd_couple_working",
    "cd_uncouple_working",
    "cd_carry",
    "cd_correct",
    # flat cascade-op adapters -- the cd_register.toml [class] binding surface
    "cdr_write",
    "cdr_materialize",
    "cdr_read_unbind",
    "cdr_clean",
    "cdr_slots",
    "cdr_working_block",
    "cdr_carry_block",
    "cdr_couple_working",
    "cdr_uncouple_working",
    "cdr_carry",
    "cdr_correct",
    "cdr_element",
    "cdr_element_of",
    "cdr_navigate",
]
