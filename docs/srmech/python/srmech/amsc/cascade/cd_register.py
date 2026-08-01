"""The GENERAL N-slot Cayley–Dickson addressable RBS-HDC register (rc297; `#934`).

srmech shipped exactly one addressable register — :class:`~srmech.amsc.cascade.
sedenion_register.SedenionRegister`, hard-wired to the sedenion's 16 slots. Research
that needed 32 slots therefore had to write its own, and correctly flagged that as a
confound: *"a register I wrote could just be easier."* This module removes the
confound by bringing the general register in-tree.

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
full exact-rational :func:`~srmech.amsc.cascade.cayley_dickson.cd_mult` — so the
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
irreducible COHOMOLOGICAL datum, not a representational one.

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
:func:`~srmech.amsc.cascade.chiral_flip`. It is also why
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
mechanism, and exposing ``namespace`` is what lets the general register **reproduce
the shipped one bit-exactly**::

    CDRegister(dim=16, namespace="SEDENION")   ==   SedenionRegister()

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
:func:`~srmech.amsc.cascade.chiral_flip`
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
from srmech.amsc import _native
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
    from ...math.hdc import bind, bundle, similarity
    return bind, bundle, similarity


def _lazy_mint():
    """Import the RBS-HDC minter on demand (numpy-free cascade; deferred import)."""
    from ...signal_processing import mint_vector
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
            f"algebra dimension: 1 ℝ / 2 ℂ / 4 ℍ / 8 𝕆 / 16 𝕊 / 32 𝕋 / 64); "
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

    The general-rung form of :meth:`SedenionRegister.navmap`; at ``dim=16`` it is
    bit-identical to it. Always a signed permutation — reversible at **every**
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
    (cocycle shortcut vs full :func:`~srmech.amsc.cascade.cayley_dickson.cd_mult`,
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
# These are the dim-scaled generalisations of the four SedenionRegister value-
# operations, mirroring how cd_navmap(dim, j) generalises the 16-slot navmap.
# They compose the already-C-backed hypercomplex_couple / hamming primitives — no
# new algebra, no new C symbol (composition_of_c, exactly like the sed_* peers).

def cd_couple_working(vals: Sequence[float], dim: int = WORKING_BLOCK_DIM) -> List[float]:
    """Bind ``≤ min(dim, 8) − 1`` real streams into one reversible working word —
    the canonical Class-M **bind** on the Cayley–Dickson register (rc301, `#T938`).

    The dim-scaled generalisation of :meth:`SedenionRegister.couple_working`: the
    cap is read from :func:`_working_cap` (``min(dim, 8) − 1``), never a hardcoded
    7. dim 2 couples 1 imaginary slot, dim 4 couples 3, dim 8/16/…/256 couple 7
    (the octonion sub-block; Hurwitz). dim 1 (ℝ) couples nothing — the degenerate
    base — so an empty ``vals`` returns ``[]`` and any value raises.

    Composes :func:`~srmech.amsc.cascade.hypercomplex_couple` (``axis="diagonal"``,
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
    list[float]
        The coupled working word — a 4-component quaternion (≤3 streams) or
        8-component octonion (4–7 streams); ``[]`` when nothing is coupled.
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


def cd_uncouple_working(word: Sequence[float]) -> List[float]:
    """Recover the streams bound by :func:`cd_couple_working` — the exact inverse
    (the Class-M **unbind**; rc301, `#T938`).

    Applies the conjugate twiddle (``inverse=True``) and drops the anchor slot,
    returning the carrier's imaginary components (``word[1:]``): 7 for an octonion
    word, 3 for a quaternion word. Empty in → empty out (the dim-1 boundary).
    Recovery is exact to float round-off (the division-algebra identity
    ``T̄·(T·q) = ‖T‖²·q``, F437), matching the shipped register's tolerance."""
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
    count. Composes :func:`~srmech.amsc.cascade.hamming_encode` (the
    ``srmech_hamming_encode`` C peer). Lean-ALU XOR; no float, no ``abs()``."""
    return hamming_encode(overflow_bits, n)


def cd_correct(codeword: Sequence[int]) -> Dict[str, Any]:
    """Locate + correct a single-bit error in an EC-block codeword and recover the
    carried payload — the EC/carry layer's read (rc301, `#T938`).

    Composes :func:`~srmech.amsc.cascade.hamming_decode_correct` (the syndrome
    dispatches to ``srmech_hamming_syndrome``). Returns
    ``{"data", "error_position", "corrected_codeword"}``. Single-error-correcting
    (minimum distance 3). Lean-ALU XOR; no float, no ``abs()``."""
    return hamming_decode_correct(codeword)


class CDRegister:
    """A general **N-slot** Cayley–Dickson addressable RBS-HDC register — the
    :class:`~srmech.amsc.cascade.sedenion_register.SedenionRegister` generalised
    from 16 slots to ``dim`` slots (any power of two in ``[1, CD_MAX_DIM]``).

    Storage is content-keyed exactly as in the 16-slot register: :meth:`write`
    records ``slot → (key, sign)`` and materialises the associative bundle on
    demand; :meth:`read` unbinds by the slot's address and cleans against the
    codebook.

    ``namespace`` selects the address-mint namespace (default ``f"CD{dim}"``).
    Setting ``namespace="SEDENION"`` at ``dim=16`` reproduces the shipped
    :class:`SedenionRegister` **bit-exactly at every** ``D`` — that is the
    faithfulness gate this class is held to, and it is why the parameter exists.

    Three layers (rc301, `#T938`): the CORE **addressing** layer is always on and
    content-AGNOSTIC — ``navmap`` is a pure function of ``dim``, storage holds
    anything, KIND is dimension-invariant. Alongside it (rc330, `#948`) the CORE
    **carrier-arithmetic** surface is likewise always on: :meth:`element` /
    :meth:`norm` / :meth:`conjugate` / :meth:`multiply` / :meth:`add` read the
    signed-basis element ``Σ sign_i·e_i`` a register holds and DELEGATE to the
    exact-``Q`` :mod:`~srmech.amsc.cascade.cayley_dickson` ops over it (the
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

    def couple_working(self, vals: Sequence[float]) -> List[float]:
        """Bind ``≤ len(working_block()) − 1`` values into one reversible working
        word — THE canonical Class-M bind (rc301). Reads the dim-scaled cap
        (``min(dim, 8) − 1``), never a hardcoded 7: dim 2 couples 1, dim 4 couples
        3, dim 8/16/…/256 couple 7, dim 1 couples nothing. Requires ``coupling=True``.

        Delegates to :func:`cd_couple_working` — at dim 16 this is bit-exact with
        the shipped :meth:`SedenionRegister.couple_working` (the faithfulness gate)."""
        self._require_coupling()
        return cd_couple_working(vals, self.dim)

    def uncouple_working(self, word: Sequence[float]) -> List[float]:
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
            # faithfulness gate is bit-identity with the shipped SedenionRegister,
            # and magnitude() carries a NaN→0.0 dead-band that the shipped
            # register's branch does not. Unreachable for a byte-vector
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
        :func:`~srmech.amsc.cascade.cayley_dickson.cd_norm_sq`. Since every occupied
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
        :func:`~srmech.amsc.cascade.cayley_dickson.cd_conjugate` (negate the
        imaginary part; Class-K sign-flip, no ``abs()``). The conjugate of a
        signed-basis element is ALWAYS signed-basis — it only flips imaginary-slot
        signs — so this one *could* round-trip into a register; it is returned
        uniform with ``cd_conjugate`` as a ``Q``-tuple."""
        return cd_conjugate(self.element())

    def multiply(self, other: "CDRegister") -> Tuple[Q, ...]:
        """The Cayley–Dickson product ``x·y`` of this register's slot-held element
        with ``other``'s, as a raw ``Q``-tuple CD element (rc330, `#948`).
        Delegates to :func:`~srmech.amsc.cascade.cayley_dickson.cd_mult` (Class-M
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
        :func:`~srmech.amsc.cascade.cayley_dickson.cd_add`. ``other`` is another
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
        shipped :class:`SedenionRegister` behaves identically; its docstring's
        "shares the codebook" is imprecise about the mapping and is corrected
        alongside this one.

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
    """Construct a :class:`CDRegister` — the **general N-slot** Cayley–Dickson
    addressable RBS-HDC register (rc297; `#934`). ``dim`` named slots
    ``e0..e{dim-1}`` for any power of two in ``[1, CD_MAX_DIM]``; ``e0..e7`` is the
    octonion reversible working block at every rung and the remainder is the
    carry/EC block.

    The CORE **addressing** layer (``write`` / ``read`` / ``navmap`` / ``navigate``
    / ``is_navigable``) is always on and content-agnostic. The two OPTIONAL layers
    are off by default: ``coupling=True`` enables the reversible working word
    (``couple_working`` / ``uncouple_working``, Class M, capped at ``min(dim, 8) −
    1`` by Hurwitz); ``error_correction=True`` enables the Hamming EC block
    (``carry`` / ``correct``, a separate axis from ``dim``). A bare register is a
    pure signed-pointer addressing object.

    Generalises the 16-slot
    :func:`~srmech.amsc.cascade.sedenion_register.sedenion_register` — the slot
    bound is the only difference; every sign and index rule is shared through
    :func:`cd_basis_product`. ``namespace="SEDENION"`` at ``dim=16`` reproduces the
    shipped register bit-exactly at every ``D`` (the faithfulness gate).

    Legitimate past the Hurwitz wall because addressing rides on the basis product
    being a signed permutation, which zero divisors (built from *sums* of basis
    elements) do not touch — see :func:`cd_navmap_is_signed_permutation`.
    """
    return CDRegister(dim=dim, D=D, codebook=codebook, namespace=namespace,
                      coupling=coupling, error_correction=error_correction)


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
]
