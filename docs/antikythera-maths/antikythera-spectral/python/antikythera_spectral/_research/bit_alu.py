"""Bit-packed binary hypervector ALU — pure-bitwise HDC primitives.

Every operation reduces to integer bit-ops (XOR, popcount, shift) on
packed uint64 words.  No floating point, no complex arithmetic, no
matrix multiplies.  The point: an "ALU only" backend for the
Antikythera HDC encoder, implementing the same algebraic structure
(cyclic-group representation of the dials) at a fraction of the
memory and arithmetic-op cost vs the complex128 reference in
``encode_ant.py``.

Representation
--------------

A D-dimensional binary hypervector is a numpy ``uint64`` array of
length ``n_words(D) = ceil(D / 64)``.  Bit ``i`` of the hypervector
is bit ``(i % 64)`` of word ``(i // 64)``, i.e. little-endian within
each word, with words laid out from low-index bits to high-index
bits.  Unused bits in the top word are masked to zero.

Operations
----------

::

    bind         a ⊕ b              XOR (involutive: a ⊕ a = 0)
    bundle       majority(...)      bitwise majority threshold
    permute      rotate(v, n)       cyclic bit-rotation across words
    hamming      popcount(a ⊕ b)    bit-distance
    similarity   1 − 2H/D           bipolar-equivalent in [-1, 1]

The complete set is closed under bitwise operations only — no
floating-point, no integer multiplication, no division.  An "ALU
only" HDC backend.

Cycle alignment of permute
--------------------------

``permute(v, 1)`` advances the hypervector by ONE position.  For the
Antikythera encoder, position increments correspond to one **Julian
day** (the time unit of ``REFERENCE_JD``; SI 86400 s = mean solar
day to within Earth's rotation-rate variation).  After ``D``
permutations, ``v`` returns to itself: ``D = 940`` (Callippic) ↔ 940
Julian days ↔ 2.575 mean-solar years.  See
``cycle_alignment_investigation.py`` for the solar-vs-sidereal-day
framing analysis (TL;DR: solar/Julian is correct for the calendar
dials, which is what the existing encoder uses).

Compatibility with `encode_ant.py`
----------------------------------

The bit ALU is a SECOND HDC backend alongside the existing
complex128 encoder in ``encode_ant.py``.  Both implement the same
algebraic structure; they trade precision for speed.  Bit-packed:

* 940 bits = 120 B per hypervector vs 15 KB for complex128 (125×
  smaller).
* One bind = 15 uint64 XOR ops vs 940 complex multiplies (~63× fewer
  primitive ops; vectorised XOR on 15 uint64s is one numpy call).
* One permute = one Python big-int shift + mask vs ``np.roll`` on
  complex128 (similar order of magnitude, see benchmark).
* One similarity = popcount of XOR (uint64-vectorised) vs complex
  inner product + abs (much faster).

The bit ALU is faithful to HDC algebraic identities (XOR-bind is
self-inverse; majority-bundle is approximately associative; permute
is a cyclic-shift representation of ℤ/Dℤ).  It is NOT bit-for-bit
identical to the complex128 encoder's output — different basis
vectors, different bundle semantics.  Comparison is at the level of
"can both encoders correctly represent the dial state?"

Tests live in ``antikythera-spectral/python/tests/test_bit_alu.py``;
benchmark in ``research/bit_alu_benchmark.py``.

References
----------

- Kanerva (2009).  "Hyperdimensional Computing: An Introduction to
  Computing in Distributed Representation with High-Dimensional
  Random Vectors."  *Cognitive Computation* 1:139.
- Plate (2003).  *Holographic Reduced Representation: Distributed
  Representation for Cognitive Structures.*  CSLI Publications.
- Schlegel et al. (2022).  "A Comparison of Vector Symbolic
  Architectures."  *Artif. Intell. Rev.* 55:4523. (Compares BSC /
  HRR / FHRR; this module implements the BSC / Binary Spatter
  Code variant.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Packed-bitvector helpers
# ---------------------------------------------------------------------------

def n_words(D: int) -> int:
    """Number of uint64 words required to hold ``D`` bits."""
    if D < 0:
        raise ValueError(f"D must be non-negative, got {D}")
    return (D + 63) // 64


def _top_mask(D: int) -> np.uint64:
    """Bitmask for the top word of a D-bit hypervector.  Returns a
    uint64 with exactly ``D mod 64`` low bits set, or all-ones if
    ``D % 64 == 0``."""
    used_in_top = D - 64 * (n_words(D) - 1)
    if used_in_top >= 64:
        return np.uint64(0xFFFFFFFFFFFFFFFF)
    return np.uint64((1 << used_in_top) - 1)


def _mask(v: np.ndarray, D: int) -> np.ndarray:
    """Zero out unused bits in the top word of ``v``.  In-place safe;
    returns ``v`` for chaining."""
    if len(v) == 0:
        return v
    v[-1] = v[-1] & _top_mask(D)
    return v


def random_hv(D: int, rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """Random uniform binary hypervector of dimension ``D``, packed.

    Each bit is i.i.d. Bernoulli(0.5).  Top-word unused bits masked to 0.
    """
    if rng is None:
        rng = np.random.default_rng()
    nw = n_words(D)
    arr = rng.integers(
        np.iinfo(np.uint64).min,
        np.iinfo(np.uint64).max,
        size=nw, dtype=np.uint64, endpoint=True,
    )
    return _mask(arr, D)


def zeros_hv(D: int) -> np.ndarray:
    """All-zeros hypervector (the additive identity of bind/XOR)."""
    return np.zeros(n_words(D), dtype=np.uint64)


def ones_hv(D: int) -> np.ndarray:
    """All-ones hypervector (within the D-bit window)."""
    arr = np.full(n_words(D), np.uint64(0xFFFFFFFFFFFFFFFF), dtype=np.uint64)
    return _mask(arr, D)


# ---------------------------------------------------------------------------
# Core HDC operations — all bitwise
# ---------------------------------------------------------------------------

def bind(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Bind: XOR.  Self-inverse (``bind(a, a)`` is the zero vector).

    For BSC (Binary Spatter Code) HDC, bind is XOR — it preserves the
    distance between bound vectors and is a permutation on the
    hypervector space.  ``bind(bind(a, b), b) == a`` (involution).
    """
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    return a ^ b


def bundle_majority(
    stack: List[np.ndarray] | np.ndarray, D: int,
    tie_break: str = "round_up",
) -> np.ndarray:
    """Bundle by bitwise majority: bit i of output is 1 iff a strict
    majority of inputs have bit i set.

    ``stack`` is either a list of M hypervectors (each ``n_words(D)``
    long) or a 2D array of shape ``(M, n_words(D))``.

    Tie-breaking when M is even: ``round_up`` (default) sets the bit
    on a tie; ``round_down`` clears it.  For the Antikythera encoder
    where M = number of dials (typically 4-13), this matters at the
    one-bit level; with a known M, callers can also XOR an
    odd-tie-breaker hypervector before bundling to guarantee
    odd-parity inputs.
    """
    if isinstance(stack, list):
        if len(stack) == 0:
            return zeros_hv(D)
        stack = np.stack(stack)
    if stack.ndim != 2:
        raise ValueError(
            f"stack must be 2D (M, n_words); got shape {stack.shape}"
        )
    M, nw = stack.shape
    if nw != n_words(D):
        raise ValueError(
            f"stack n_words={nw} doesn't match D={D} (n_words={n_words(D)})"
        )

    # Per-bit count via per-word unpack.  np.unpackbits operates on
    # uint8 with bitorder 'little' to get LSB-first; reshape so each
    # uint64 word produces 64 bits.
    # stack: (M, nw) uint64 -> bytes_view (M, nw*8) uint8
    bytes_view = stack.view(np.uint8).reshape(M, nw * 8)
    # Unpack each byte to 8 bits (little-endian within byte).
    bits = np.unpackbits(bytes_view, axis=1, bitorder="little")  # (M, nw*64)
    # Crop to D bits to be safe (top-word padding shouldn't matter
    # since it's masked, but explicit is better).
    bits = bits[:, :D]
    counts = bits.sum(axis=0)  # (D,)
    if tie_break == "round_up":
        threshold = (M + 1) // 2
    elif tie_break == "round_down":
        threshold = M // 2 + 1
    else:
        raise ValueError(
            f"tie_break must be 'round_up' or 'round_down'; got "
            f"{tie_break!r}"
        )
    out_bits = (counts >= threshold).astype(np.uint8)
    # Pad back to multiple of 8 then pack.
    pad = (8 - D % 8) % 8
    if pad:
        out_bits = np.concatenate([out_bits, np.zeros(pad, dtype=np.uint8)])
    out_bytes = np.packbits(out_bits, bitorder="little")
    # Pad bytes to nw*8 if needed (top-word zeros).
    needed = nw * 8
    if len(out_bytes) < needed:
        out_bytes = np.concatenate([
            out_bytes,
            np.zeros(needed - len(out_bytes), dtype=np.uint8),
        ])
    out = out_bytes.view(np.uint64).copy()
    return _mask(out, D)


def permute(v: np.ndarray, n: int, D: int) -> np.ndarray:
    """Cyclic bit-rotation of ``v`` by ``n`` positions in [0, D).

    Output bit ``i`` = input bit ``(i - n) mod D``.  Equivalent to
    ``np.roll`` on the conceptual D-bit array but written as integer
    shifts so it's pure-ALU.  Implementation: pack to a single Python
    big-int, rotate within the D-bit window with shift+mask, unpack.
    Big-int ops are ~O(D) but constant-factor cheap and have no
    floating-point; this is the canonical "ALU only" rotation.
    """
    if D <= 0:
        return v.copy()
    n = int(n) % D
    if n == 0:
        return v.copy()
    nw = len(v)
    if nw != n_words(D):
        raise ValueError(
            f"v has {nw} words but D={D} requires {n_words(D)}"
        )
    # Pack to single big-int (little-endian word order).
    big = 0
    for w_idx in range(nw):
        big |= int(v[w_idx]) << (64 * w_idx)
    # Rotate within the D-bit window.
    mask = (1 << D) - 1
    big = ((big << n) | (big >> (D - n))) & mask
    # Unpack back to uint64 array.
    word_mask = (1 << 64) - 1
    out = np.zeros(nw, dtype=np.uint64)
    for w_idx in range(nw):
        out[w_idx] = np.uint64((big >> (64 * w_idx)) & word_mask)
    return out


def hamming_distance(a: np.ndarray, b: np.ndarray) -> int:
    """Number of bits where ``a`` and ``b`` differ.

    Range: [0, D].  Random pair: ~D/2.  Identical: 0.  Anti-pair: D.
    """
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    diff = a ^ b
    # Python 3.10+ has int.bit_count(); equivalent to popcount.
    return int(sum(int(w).bit_count() for w in diff))


def similarity(a: np.ndarray, b: np.ndarray, D: int) -> float:
    """Bipolar-equivalent similarity in [-1, 1].

    1.0 = identical; 0.0 = uncorrelated (random); −1.0 = anti-correlated.

    Computed as ``1 − 2 · hamming_distance(a, b) / D``.  This is the
    bipolar inner-product analogue: maps each binary bit to {+1, −1}
    and computes the normalised dot product.
    """
    if D <= 0:
        return 0.0
    h = hamming_distance(a, b)
    return 1.0 - 2.0 * h / D


# ---------------------------------------------------------------------------
# Encoder analogue of `encode_ant._encode_dense` for the bit-ALU backend
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BitChannelBasis:
    """A binary channel basis for a single dial at dimension D.

    The bit-ALU analogue of ``encode_ant._make_channel_basis``: a
    deterministic random binary hypervector seeded from
    ``base_seed + dial_idx``.  Used by ``encode_ant_bit`` as the
    per-dial "label" the dial's residue rotates.
    """
    D: int
    dial_idx: int
    base_seed: int
    basis: np.ndarray  # uint64 array of length n_words(D)


_BIT_BASES_CACHE: dict[Tuple[int, int, int], BitChannelBasis] = {}


def get_bit_channel_basis(
    D: int, dial_idx: int, base_seed: int = 42,
) -> BitChannelBasis:
    """Return the cached or freshly-built bit channel basis for
    ``(D, dial_idx)`` under ``base_seed``.

    Independent of the complex128 channel basis in ``encode_ant.py``;
    the two backends use different seeds and different distributions
    (binary vs complex Gaussian).  Both implement the same role:
    a per-dial random hypervector that the dial's residue rotates.
    """
    key = (D, dial_idx, base_seed)
    cached = _BIT_BASES_CACHE.get(key)
    if cached is not None:
        return cached
    rng = np.random.default_rng(base_seed + dial_idx)
    basis = random_hv(D, rng)
    out = BitChannelBasis(
        D=D, dial_idx=dial_idx, base_seed=base_seed, basis=basis,
    )
    _BIT_BASES_CACHE[key] = out
    return out


def encode_ant_bit(date_jd: float, D: int = 940,
                   base_seed: int = 42) -> np.ndarray:
    """Bit-ALU analogue of ``encode_ant.encode_ant_callippic``.

    For each supported dial at this ``D``, compute the integer
    residue (0..D-1) and rotate the dial's bit channel basis by that
    residue.  Bundle the per-dial rotated bases into a single
    hypervector via bitwise majority.

    Returns a packed uint64 hypervector of length ``n_words(D)``.

    This is the same algebraic structure as ``_encode_dense`` in
    ``encode_ant.py`` (sum of rolled bases) but implemented in the
    bit ALU: ``np.roll`` → ``permute``, ``+`` → ``bundle_majority``,
    complex Gaussian basis → binary Bernoulli basis.
    """
    # Lazy-imported to keep this module's import dependencies thin.
    from .encode_ant import DIAL_SPECS

    rolled = []
    for i, spec in enumerate(DIAL_SPECS):
        if not spec.is_supported(D):
            continue
        residue = spec.residue(date_jd, D)
        cb = get_bit_channel_basis(D, i, base_seed)
        rolled.append(permute(cb.basis, residue, D))
    if not rolled:
        return zeros_hv(D)
    return bundle_majority(rolled, D)


# ---------------------------------------------------------------------------
# Decode: read a single dial's residue from a bit-encoded state.
# ---------------------------------------------------------------------------

def decode_dial_bit(state: np.ndarray, D: int, dial_idx: int,
                    modulus: int, base_seed: int = 42,
                    ) -> Tuple[int, float]:
    """Read off ``dial_idx``'s residue from a bit-encoded state.

    Tries every candidate residue in ``range(modulus)``, computes
    similarity between the state and the dial's basis rotated by
    that residue, and returns the argmax.

    Returns ``(best_residue, best_similarity)``.  Note this scans
    ``modulus`` candidates and is therefore O(modulus · n_words);
    for the Antikythera dials with modulus ≤ 940, this is ~14k
    uint64-popcount ops per decode.

    The argmax ties to the closest dial under bipolar similarity;
    for the Callippic encoder with M ~ 4-13 dials, decode quality
    depends on how cleanly the bundle preserves each summand —
    measured by ``test_bit_alu.test_round_trip``.
    """
    cb = get_bit_channel_basis(D, dial_idx, base_seed)
    best_r = 0
    best_sim = -2.0
    for r in range(modulus):
        rotated = permute(cb.basis, r, D)
        s = similarity(state, rotated, D)
        if s > best_sim:
            best_sim = s
            best_r = r
    return best_r, best_sim


# ---------------------------------------------------------------------------
# Round-trip self-test (no external test framework needed)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """Smoke test the primitives — invoked from ``__main__`` for
    quick sanity-check during development."""
    rng = np.random.default_rng(0)
    D = 940

    # bind: self-inverse
    a = random_hv(D, rng)
    b = random_hv(D, rng)
    ab = bind(a, b)
    assert hamming_distance(bind(ab, b), a) == 0, "bind is not self-inverse"

    # permute: rotates by D and returns to start
    v = random_hv(D, rng)
    rotated = v
    for _ in range(D):
        rotated = permute(rotated, 1, D)
    assert hamming_distance(rotated, v) == 0, "permute by D is not identity"

    # bundle_majority: of identical inputs returns the input
    bun = bundle_majority([a, a, a], D)
    assert hamming_distance(bun, a) == 0, "majority bundle of clones != input"

    # similarity: identical = 1.0, complement = -1.0
    assert abs(similarity(a, a, D) - 1.0) < 1e-12, "self-similarity != 1"
    not_a = a.copy()
    for w in range(len(not_a)):
        not_a[w] = ~not_a[w] & np.uint64(0xFFFFFFFFFFFFFFFF)
    _mask(not_a, D)
    assert abs(similarity(a, not_a, D) - (-1.0)) < 1e-12, (
        "complement similarity != -1"
    )

    print("bit_alu self-test: PASS")


if __name__ == "__main__":
    _self_test()
