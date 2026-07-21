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
:func:`~srmech.amsc.hdc.bind` / ``bundle`` / ``similarity`` cascades; the sign
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
    CD_MAX_DIM,
)
from . import chiral_flip
from srmech.amsc import _native

#: Default hypervector width (bits) — the RBS-HDC associative-register dimension.
DEFAULT_D = 8192
#: The reversible working-word cap (the octonion's 7 imaginary slots; Hurwitz).
WORKING_WORD_CAP = 7
#: The octonion working block is always the first 8 slots, at every rung.
WORKING_BLOCK_DIM = 8


def _lazy_hdc():
    """Import the Class-M HDC byte ops on demand (numpy-free; defers the import
    so the module loads without touching signal_processing)."""
    from ..hdc import bind, bundle, similarity
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

    Capacity note: the associative capacity is ``D``-bounded, and **more slots
    need more** ``D``. A dim-32 shortfall at a ``D`` adequate for dim-16 is a
    capacity fact, not an algebra fact. Sweep ``D``; never report a single point.
    """

    def __init__(self, dim: int, D: int = DEFAULT_D,
                 codebook: Optional[Dict[str, bytes]] = None,
                 minter=None, namespace: Optional[str] = None):
        self.dim = _check_dim(dim)
        self.D = int(D)
        self.namespace = str(namespace) if namespace is not None else f"CD{self.dim}"
        self.codebook: Dict[str, bytes] = dict(codebook or {})
        self._minter = minter
        self._addr_cache: Dict[int, bytes] = {}
        self._slots: Dict[int, Tuple[str, int]] = {}   # slot -> (key, sign∈{±1})

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
        """``e8..e{dim-1}`` — everything past the reversibility horizon. Compose
        the shipped :func:`~srmech.amsc.cascade.hamming_encode` /
        ``hamming_decode_correct`` (the GF(2) EC half) over this block; it is not
        duplicated here."""
        return tuple(range(WORKING_BLOCK_DIM, self.dim))

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
                         minter=self._minter, namespace=self.namespace)
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
                namespace: Optional[str] = None) -> CDRegister:
    """Construct a :class:`CDRegister` — the **general N-slot** Cayley–Dickson
    addressable RBS-HDC register (rc297; `#934`). ``dim`` named slots
    ``e0..e{dim-1}`` for any power of two in ``[1, CD_MAX_DIM]``; ``e0..e7`` is the
    octonion reversible working block at every rung and the remainder is the
    carry/EC block.

    Generalises the 16-slot
    :func:`~srmech.amsc.cascade.sedenion_register.sedenion_register` — the slot
    bound is the only difference; every sign and index rule is shared through
    :func:`cd_basis_product`. ``namespace="SEDENION"`` at ``dim=16`` reproduces the
    shipped register bit-exactly at every ``D`` (the faithfulness gate).

    Legitimate past the Hurwitz wall because addressing rides on the basis product
    being a signed permutation, which zero divisors (built from *sums* of basis
    elements) do not touch — see :func:`cd_navmap_is_signed_permutation`.
    """
    return CDRegister(dim=dim, D=D, codebook=codebook, namespace=namespace)


__all__ = [
    "DEFAULT_D",
    "WORKING_WORD_CAP",
    "WORKING_BLOCK_DIM",
    "CDRegister",
    "cd_register",
    "cd_navmap",
    "cd_navigate",
    "cd_navmap_is_signed_permutation",
]
