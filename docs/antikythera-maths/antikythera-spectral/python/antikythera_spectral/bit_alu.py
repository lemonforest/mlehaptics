"""Bit-packed binary HDC ALU — the "ALU only" encoder backend.

Curated public re-export of ``_research.bit_alu``: a binary
hypervector implementation where every operation reduces to
integer bit-ops (XOR, popcount, shift) on packed ``uint64`` words.
No floating point, no complex arithmetic, no matrix multiplies.

This is a SECOND HDC backend alongside the existing ``complex128``
encoder in ``antikythera_spectral.encoder`` / ``encode_ant``.  Both
implement the same algebraic structure (cyclic-group representation
of the Antikythera dials); they trade precision for memory + speed.

Memory: a D=940 hypervector is 120 bytes as bit-packed ``uint64[15]``
vs 15 KB as ``complex128[940]`` — 125× smaller.  Per-op speed is
2-10× faster for ``bind`` (XOR vs complex multiply) and competitive
or faster for ``bundle`` at D=13 440.  See [bit_alu_findings.md](
https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/figures/bit_alu_findings.md)
for the full benchmark.

Operations
----------

::

    bind          a ⊕ b                  XOR
    bundle        majority(...)          bitwise majority threshold
    permute       rotate(v, n)           cyclic bit-rotation in [0, D)
    hamming       popcount(a ⊕ b)        bit-distance in [0, D]
    similarity    1 − 2H/D               bipolar-equivalent in [-1, 1]

Plus an encoder analogue and a per-dial decoder:

::

    encode_ant_bit(jd, D)                bit-packed analogue of
                                         ``encode_ant.encode_ant_callippic``
    decode_dial_bit(state, D, idx, mod)  argmax of similarity over
                                         candidate residues

Cycle alignment
---------------

``permute(v, 1, D)`` advances the hypervector by ONE position,
corresponding to ONE Julian day = ONE mean solar day = ONE turn of
the Antikythera mechanism's hand-crank.  After ``D`` permutations,
``v`` returns to itself: ``D = 940`` (Callippic) ↔ 940 Julian days ↔
2.575 mean-solar years.  Sidereal-day framing is *not* the natural
choice for this encoder; see
[`research/cycle_alignment_investigation.py`](
https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/research/cycle_alignment_investigation.py)
for the empirical comparison.

Status
------

v0.3.0 first run: research scaffold + benchmark + cycle-alignment
investigation landed; the public surface is this facade.  Permute
and similarity have known optimisation paths (numpy bit-pack/unpack,
``np.bitwise_count``) deferred to v0.4.x.  The "ALU only" semantics
hold throughout — every op is bitwise — even where numpy's
hand-tuned routines for the float reference are faster than this
first-run Python implementation.

References
----------

- Kanerva (2009). *Cognitive Computation* 1:139 — HDC introduction.
- Plate (2003).  *Holographic Reduced Representation*. CSLI.
- Schlegel et al. (2022). *Artif. Intell. Rev.* 55:4523. (BSC variant
  survey; this module implements BSC.)
"""

from __future__ import annotations

from antikythera_spectral._research.bit_alu import (
    BitChannelBasis,
    bind,
    bundle_majority,
    decode_dial_bit,
    encode_ant_bit,
    get_bit_channel_basis,
    hamming_distance,
    n_words,
    ones_hv,
    permute,
    random_hv,
    similarity,
    zeros_hv,
)

__all__ = [
    # Helpers
    "n_words",
    # Constructors
    "random_hv",
    "zeros_hv",
    "ones_hv",
    # Core HDC operations
    "bind",
    "bundle_majority",
    "permute",
    "hamming_distance",
    "similarity",
    # Encoder analogue
    "BitChannelBasis",
    "get_bit_channel_basis",
    "encode_ant_bit",
    "decode_dial_bit",
]
