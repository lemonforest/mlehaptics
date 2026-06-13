"""Sedenion-addressable hyper-loop RBS-HDC instrument (UPSTREAM §31; F465 + F468).

The **sedenion shaped box made into an RBS-HDC instrument.** The user's CS
reframing (2026-06-06): *addressable* = a larger NAMED structure that contains
the pieces you are working with — exactly as bit-exact binary coding does. So the
sedenion (dim 16, the §VII.6.23 open-exterior box) is an **address space** of 16
named slots ``e0..e15``:

* ``e0..e7`` — the **octonion working block**: the reversible working set
  (anchor + 7), bound by :func:`hypercomplex_couple` and recovered bit-exactly
  (≤𝕆 by Hurwitz; the F459 coupler).
* ``e8..e15`` — the **EC / carry block**: past the reversibility horizon, held by
  a Hamming GF(2) code (:func:`hamming_encode`; the §30 CARRY half).

The instrument runs **HDC ops instead of ALU** — random-access-by-name
(:func:`~srmech.amsc.hdc.bind` + nearest-codebook clean), a reversible coupler
working word, a GF(2) carry block — getting associative superposition
**classically** (no quantum cost).

**This is NOT a substrate extension and adds NO new algebra** — it is the
ergonomic *wrapper* that composes shipped v0.7.3 primitives into one named-register
object (`[[feedback_no_privileged_primitive_classes]]`). The one genuinely-new
piece is the **address↔Cayley–Dickson homomorphism**: :meth:`SedenionRegister.navigate`
right-multiplies every slot *name* by ``e_j`` so addressing *respects*
``e_i·e_j = ±e_k`` (the :func:`cd_basis_product` cocycle), and
:meth:`SedenionRegister.is_navigable` is the reversibility gate
(:func:`left_mult_is_invertible`): single-basis navigation is always a signed
permutation (reversible at every dim), but **composite-direction** navigation is
reversible **only ≤𝕆** — the sedenion zero-divisor directions break it. The
operational hyper-loop's horizon IS the Hurwitz wall.

Composes (no new primitive class):

- :func:`srmech.amsc.hdc.bind` / ``bundle`` / ``similarity`` — Class **M** register
  read/write (associative superposition; storage capacity is ``D``-bounded).
- :func:`srmech.amsc.cascade.hypercomplex_couple` — the ≤7 reversible working word
  (Class **M** ∘ **C** ∘ **N**; §29).
- :func:`srmech.amsc.cascade.hamming_encode` / ``hamming_decode_correct`` — the
  EC/carry block (Class **B** ∘ **I** ∘ **A**; §30).
- :func:`srmech.amsc.cascade.cayley_dickson.cd_basis_product` /
  ``left_mult_is_invertible`` — the 16-slot address algebra + the navigability gate.
- :func:`srmech.amsc.cascade.chiral_flip` — the Class **C** sign on a hypervector
  (never ``abs()`` / negate).

Two distinct boundaries, kept distinct (F465): the register's **associative**
capacity is ``D``-bounded (HDC crosstalk), separate from the **reversible** working
set (≤7, the coupler). Real-coefficient EC stays out (the §30 GF(2)-only fence).

numpy-FREE (#564): the WHOLE instrument is numpy-free. The minter + HDC storage
(:meth:`write` / :meth:`read` / :meth:`materialize`) route through
:func:`srmech.signal_processing.mint_vector` + the Class-M
:func:`srmech.amsc.hdc.bind` / ``bundle`` / ``similarity`` cascades; the ≤7
working word (:meth:`couple_working`) routes through
:func:`hypercomplex_couple`; :meth:`navigate` / :meth:`is_navigable` /
:meth:`carry` / :meth:`correct` are pure address-algebra. Nothing imports numpy.

SSoT / provenance: UPSTREAM_NOTES §31 (RBS-LM, PR #687); F465
(`R-RBS-LM-SEDENION_addressable_hdc_instrument`) + F468
(`R-RBS-LM-SEDENION_operational_hyperloop`). Hurwitz (1898); Baez arXiv:math/0105155;
Kanerva (2009) *Hyperdimensional Computing* (the RBS-HDC associative-register form).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from .cayley_dickson import (
    cd_basis_product,
    left_mult_is_invertible,
    CD_MAX_DIM,
)
from .hamming import hamming_encode, hamming_decode_correct
from . import chiral_flip

#: The sedenion is the 16-slot address space (the open-exterior box, §VII.6.23).
NUM_SLOTS = 16
#: ``e0..e7`` — the octonion working block (the reversible working set, ≤𝕆).
OCT_BLOCK = tuple(range(0, 8))
#: ``e8..e15`` — the EC / carry block (past the reversibility horizon).
EC_BLOCK = tuple(range(8, 16))
#: Default hypervector width (bits) — the RBS-HDC associative-register dimension.
DEFAULT_D = 8192
#: The reversible working-word cap (the octonion's 7 imaginary slots; Hurwitz).
WORKING_WORD_CAP = 7


def _lazy_hdc():
    """Import the Class-M HDC byte ops on demand (numpy-free; defers the import
    so the module loads without touching signal_processing)."""
    from ..hdc import bind, bundle, similarity
    return bind, bundle, similarity


def _lazy_mint():
    """Import the RBS-HDC minter on demand (numpy-free cascade; deferred import)."""
    from ...signal_processing import mint_vector
    return mint_vector


class SedenionRegister:
    """A sedenion (dim-16) addressable RBS-HDC instrument — 16 named slots, an
    octonion reversible working word, a Hamming EC/carry block, and a
    CD-respecting ``navigate``. Composes shipped v0.7.3 primitives; no new algebra.

    Storage is content-keyed: :meth:`write` records ``slot → (key, sign)`` and
    materialises the associative bundle on demand; :meth:`read` unbinds by the
    slot's sedenion address and cleans against the codebook.
    """

    def __init__(self, D: int = DEFAULT_D, codebook: Optional[Dict[str, bytes]] = None,
                 minter=None):
        self.D = int(D)
        self.codebook: Dict[str, bytes] = dict(codebook or {})
        self._minter = minter
        self._addr_cache: Dict[int, bytes] = {}
        self._slots: Dict[int, Tuple[str, int]] = {}   # slot -> (key, sign∈{+1,-1})

    # ── address + codebook minting (numpy-free cascade; deferred import) ──
    def _mint(self, name: str) -> bytes:
        if self._minter is None:
            self._minter = _lazy_mint()
        return self._minter(name, D=self.D)

    def _addr(self, slot: int) -> bytes:
        if slot not in self._addr_cache:
            self._addr_cache[slot] = self._mint(f"SEDENION:e{slot}")
        return self._addr_cache[slot]

    def _value_vec(self, key: str, sign: int) -> bytes:
        if key not in self.codebook:
            self.codebook[key] = self._mint(f"VAL:{key}")
        vec = self.codebook[key]
        return vec if sign >= 0 else chiral_flip(vec)   # Class C sign; never abs()

    @staticmethod
    def _check_slot(slot: int) -> int:
        if type(slot) is not int or not (0 <= slot < NUM_SLOTS):
            raise ValueError(
                f"slot must be an int in [0, {NUM_SLOTS}) (the sedenion address "
                f"space e0..e{NUM_SLOTS - 1}); got {slot!r}"
            )
        return slot

    # ── associative storage (Class M; D-bounded capacity) ─────────────────
    def write(self, slot: int, key: str, *, sign: int = 1) -> None:
        """Store ``key`` (a content name) at sedenion slot ``e{slot}`` with a
        Class-C ``sign``. ``bind(ADDR[slot], value)`` enters the bundle on
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
            # Bit-identical to ``abs(s)`` for every float; the polarity that
            # wins is carried separately as ``best_sign`` (Class C).
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

    # ── the ≤7 reversible working word (the octonion block; §29) ──────────
    def couple_working(self, vals: Sequence[float]) -> List[float]:
        """Bind ≤7 values into one octonion working word (bit-exact reversible
        ≤𝕆). Raises if more than 7 values are given — the 8th must spill to the
        EC/carry block (:meth:`carry`)."""
        if len(vals) > WORKING_WORD_CAP:
            raise ValueError(
                f"the reversible working word holds ≤{WORKING_WORD_CAP} values "
                f"(the octonion's imaginary slots; Hurwitz cap). Got {len(vals)} — "
                f"spill the overflow to the EC/carry block via .carry()."
            )
        from . import hypercomplex_couple
        return hypercomplex_couple(list(vals), axis="diagonal")

    def uncouple_working(self, octonion: Sequence[float]) -> List[float]:
        """Inverse of :meth:`couple_working` — recover the ≤7 streams bit-exactly.
        Returns the 7 working-word values (the coupler's anchor slot is dropped)."""
        from . import hypercomplex_couple
        rec = hypercomplex_couple(list(octonion), axis="diagonal", inverse=True)
        return list(rec)[1:8]

    # ── the EC / carry block (>7; Hamming GF(2); §30) ─────────────────────
    def carry(self, overflow_bits: Sequence[int], n: int = 3) -> List[int]:
        """Encode overflow bits (past the ≤7 working set) into a Hamming(2ⁿ−1)
        codeword living in the ``e8..e15`` EC block. Single-error-correcting."""
        return hamming_encode(overflow_bits, n)

    def correct(self, codeword: Sequence[int]) -> Dict[str, Any]:
        """Locate + correct a single-bit error in an EC-block codeword and recover
        the carried payload (delegates to :func:`hamming_decode_correct`)."""
        return hamming_decode_correct(codeword)

    # ── the operational hyper-loop: address↔CD homomorphism (F468) ────────
    def navmap(self, j: int) -> Dict[int, Tuple[int, int]]:
        """The pointer-advance permutation for right-multiply-by-``e_j``: maps each
        slot ``i`` to ``(k, sign)`` where ``e_i·e_j = sign·e_k`` (the
        :func:`cd_basis_product` cocycle over the sedenion). Always a signed
        permutation (reversible at every dim for a single basis direction)."""
        if not (0 <= j < NUM_SLOTS):
            raise ValueError(f"navigation basis j must be in [0, {NUM_SLOTS}); got {j}")
        return {i: cd_basis_product(NUM_SLOTS, i, j) for i in range(NUM_SLOTS)}

    def navigate(self, j: int) -> "SedenionRegister":
        """Walk the hyper-loop: right-multiply every slot *name* by ``e_j`` so
        content at slot ``i`` moves to slot ``k`` with sign ``s``, ``e_i·e_j =
        s·e_k`` (the address↔Cayley–Dickson homomorphism). Returns a NEW register
        with the routed assignment (shares the codebook). Single-basis navigation
        is exactly reversible — ``navigate(j).navigate(j)`` is the global ``−1``
        (``e_j² = −1``), recoverable as a Class-C sign."""
        m = self.navmap(j)
        out = SedenionRegister(D=self.D, codebook=self.codebook, minter=self._minter)
        out._addr_cache = dict(self._addr_cache)
        for i, (key, sgn) in self._slots.items():
            k, s = m[i]
            out._slots[k] = (key, sgn * s)      # compose the Class-C signs
        return out

    def is_navigable(self, direction: Sequence[Any]) -> bool:
        """``True`` iff navigation along ``direction`` is reversible — i.e. left-
        multiplication by ``direction`` is invertible (:func:`left_mult_is_invertible`).
        A single basis ``e_j`` (a length-16 one-hot) is always navigable; a
        **composite** direction is navigable **only ≤𝕆** — a sedenion
        zero-divisor direction is NOT (the operational hyper-loop's Hurwitz horizon)."""
        return left_mult_is_invertible(direction)


def sedenion_register(D: int = DEFAULT_D,
                      codebook: Optional[Dict[str, bytes]] = None) -> SedenionRegister:
    """Construct a :class:`SedenionRegister` — the sedenion-addressable RBS-HDC
    instrument (UPSTREAM §31; F465 + F468). 16 named slots ``e0..e15``: the
    octonion block ``e0..e7`` is the reversible working set, ``e8..e15`` the
    EC/carry block. Composes shipped v0.7.3 primitives; no new algebra. The
    genuinely-new surface is :meth:`SedenionRegister.navigate` (the address↔CD
    homomorphism) + :meth:`SedenionRegister.is_navigable` (the reversibility gate).
    """
    return SedenionRegister(D=D, codebook=codebook)


# ──────────────────────────────────────────────────────────────────────
# Flat cascade-op adapters — the make_class two-layer binding surface for
# ``sedenion_register.toml`` (the ``[class] SedenionRegister``; #564 /
# [[feedback_prefer_config_driven_toml_classes]]).
#
# The declarative class state is ``D`` (int) / ``codebook`` (dict) / ``slots``
# (dict) — the private ``_minter`` / ``_addr_cache`` caches are DROPPED (minting
# is deterministic from ``(name, D)``, so the declarative form recomputes; the
# cache was a perf-only memo). Each adapter rehydrates a transient
# :class:`SedenionRegister` from those fields and calls the existing method (no
# logic duplication), so the TOML class is byte-identical to the Python class.
# The class TOML routes: ``write`` -> ``mutates=["slots","codebook"]``;
# ``read`` -> a 2-stage **chain** (``sed_read_unbind`` -> ``sed_clean``: the
# unbound "noisy" vector is the visible intermediate, cleaned against the
# codebook); ``navigate`` -> ``returns="self"`` (a new register); the rest a
# single flat op. Reachable ONLY via the make_class class surface (structured
# ``slots``/``codebook`` args have no MCP coercer) — exempt in the tool-schema
# coverage gate exactly like the ``one.*`` accessors.
# ──────────────────────────────────────────────────────────────────────

def _rehydrate(D: int, codebook, slots) -> SedenionRegister:
    """Build a transient SedenionRegister from the declarative fields."""
    r = SedenionRegister(D=int(D), codebook=dict(codebook or {}))
    r._slots = {int(k): (str(v[0]), int(v[1]))
                for k, v in dict(slots or {}).items()}
    return r


def sed_write(slot, key, slots, codebook, D, *, sign: int = 1):
    """``write`` (mutates): store ``key`` at sedenion slot ``e{slot}`` with a
    Class-C ``sign``. Returns ``(None, {"slots": …, "codebook": …})`` — minting
    the value vec grows the codebook, the slot-map records the assignment."""
    r = _rehydrate(D, codebook, slots)
    r.write(slot, key, sign=sign)
    return (None, {"slots": dict(r._slots), "codebook": dict(r.codebook)})


def sed_materialize(slots, codebook, D):
    """``materialize``: the associative superposition bytes (raises if empty)."""
    return _rehydrate(D, codebook, slots).materialize()


def sed_read_unbind(slot, slots, codebook, D):
    """``read`` CHAIN stage 1: unbind slot ``e{slot}`` from the bundle → the
    noisy vector (``None`` if the register is empty — the read short-circuit)."""
    r = _rehydrate(D, codebook, slots)
    r._check_slot(slot)
    if not r.codebook or not r._slots:
        return None
    bind, _, _ = _lazy_hdc()
    return bind(r._addr(slot), r.materialize())


def sed_clean(noisy, codebook):
    """``read`` CHAIN stage 2: nearest-codebook clean → ``(key, sign)``.
    ``(None, +1)`` if ``noisy`` is absent (empty register). Class-K magnitude via
    an explicit sign-branch (never ``abs()``); the winning polarity is the
    Class-C ``sign`` carried separately."""
    if noisy is None:
        return (None, 1)
    _, _, similarity = _lazy_hdc()
    best_key, best_sign, best_mag = None, 1, -1.0
    for key, vec in dict(codebook).items():
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


def sed_slots(slots):
    """``slots``: a copy of the ``slot → (key, sign)`` assignment."""
    return {int(k): (str(v[0]), int(v[1]))
            for k, v in dict(slots or {}).items()}


def sed_couple_working(vals):
    """``couple_working``: bind ≤7 values into one octonion working word."""
    return SedenionRegister().couple_working(vals)


def sed_uncouple_working(octonion):
    """``uncouple_working``: recover the ≤7 streams from the working word."""
    return SedenionRegister().uncouple_working(octonion)


def sed_carry(overflow_bits, *, n: int = 3):
    """``carry``: Hamming(2ⁿ−1)-encode overflow bits into the EC block."""
    return SedenionRegister().carry(overflow_bits, n=n)


def sed_correct(codeword):
    """``correct``: locate + correct a single-bit error in an EC codeword."""
    return SedenionRegister().correct(codeword)


def sed_navmap(j):
    """``navmap``: the signed pointer-advance permutation for ×e_j."""
    return SedenionRegister().navmap(j)


def sed_navigate(j, D, codebook, slots):
    """``navigate`` (returns="self"): walk the hyper-loop — right-multiply every
    slot name by ``e_j`` → a NEW register's ``{D, codebook, slots}`` state-dict
    (shares the codebook; composes the Class-C signs)."""
    out = _rehydrate(D, codebook, slots).navigate(j)
    return {"D": out.D, "codebook": dict(out.codebook), "slots": dict(out._slots)}


def sed_is_navigable(direction):
    """``is_navigable``: True iff navigation along ``direction`` is reversible."""
    return SedenionRegister().is_navigable(direction)


__all__ = [
    "NUM_SLOTS",
    "OCT_BLOCK",
    "EC_BLOCK",
    "DEFAULT_D",
    "WORKING_WORD_CAP",
    "SedenionRegister",
    "sedenion_register",
    # flat cascade-op adapters — the sedenion_register.toml binding surface
    "sed_write",
    "sed_materialize",
    "sed_read_unbind",
    "sed_clean",
    "sed_slots",
    "sed_couple_working",
    "sed_uncouple_working",
    "sed_carry",
    "sed_correct",
    "sed_navmap",
    "sed_navigate",
    "sed_is_navigable",
]
