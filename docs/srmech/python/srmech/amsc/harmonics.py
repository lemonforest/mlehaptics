"""srmech.amsc.harmonics — per-operator chirality-harmonic classification (F150).

The 14 A–N class operators do NOT carry uniform chirality. Per Finding 150
(RBS-LM research subtree, 2026-05-28) they partition into a **1-2-3 harmonic**
order — refining F132's Klein-4 4-sector structure (`srmech.amsc.hdc.klein4_*`)
with a per-operator harmonic period:

| Harmonic | Chirality behaviour                    | Operators        | n |
|----------|----------------------------------------|------------------|---|
| **1**    | chirality-INVARIANT (no-op pass)       | A B F H N        | 5 |
| **2**    | chiral inverse / self-inverse (mirror) | C D E G K M      | 6 |
| **3**    | chiral rotation (3-cycle)              | I J L            | 3 |

- **Harmonic 1** operators are chirality-blind by construction — content
  addressing (A), TLV framing (B), template render (F), introspection (H),
  rational anchor (N). Applying a chirality flip is the identity; no variant
  is needed.
- **Harmonic 2** operators have a period-2 mirror: applying the chiral mirror
  twice returns the original (the existing `klein4_*` ops are harmonic-2). The
  mirror variants live alongside their base op — `dispatch.mirror_pattern`
  (D), `catalog.reverse_order` (E), `search.byte_search_backward` (G).
- **Harmonic 3** operators have a period-3 rotation (the order-3 triality /
  Z₃ structure) — `cyclic.three_cycle` (I), `laplacian.three_fold_eigvec_groups`
  (L). J's 3-cycle is the open framework question (F150 §6.3); not exposed.

This module exposes the static partition + `classify_harmonic(letter)` (the
operator→harmonic map) and `classify_chirality_harmonic(hv)` — a SPECTRAL
classifier that reads the harmonic order directly off an encoded hypervector's
symmetry signature, generalising the surface-form token-name classifier
(R-RBS-NN-14a) to work on any encoded vector regardless of provenance.

Pure-Python + numpy; no new C surface (harmonic classification is framework-
level composition over the existing A–N primitives). Class-L (spectral) read
of the chirality structure.
"""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

# F150 operator → chirality-harmonic partition (the 1-2-3 reading of the 14).
HARMONIC_1: Tuple[str, ...] = ("A", "B", "F", "H", "N")
HARMONIC_2: Tuple[str, ...] = ("C", "D", "E", "G", "K", "M")
HARMONIC_3: Tuple[str, ...] = ("I", "J", "L")

#: harmonic-order -> the operator letters carrying it.
HARMONIC_PARTITION: Dict[int, Tuple[str, ...]] = {
    1: HARMONIC_1,
    2: HARMONIC_2,
    3: HARMONIC_3,
}

#: operator letter -> harmonic order (the inverse map).
_LETTER_TO_HARMONIC: Dict[str, int] = {
    letter: order
    for order, letters in HARMONIC_PARTITION.items()
    for letter in letters
}

ALL_CLASS_LETTERS: Tuple[str, ...] = tuple(sorted(_LETTER_TO_HARMONIC))


def classify_harmonic(class_letter: str) -> int:
    """Return the chirality-harmonic order (1, 2, or 3) of an A–N class operator.

    `class_letter` is a single letter A–N (case-insensitive). Harmonic 1 =
    chirality-invariant (A B F H N), 2 = chiral inverse / mirror (C D E G K M),
    3 = chiral rotation / 3-cycle (I J L). F150.
    """
    if not isinstance(class_letter, str) or len(class_letter) != 1:
        raise ValueError(
            "classify_harmonic: class_letter must be a single A–N letter; "
            f"got {class_letter!r}"
        )
    upper = class_letter.upper()
    if upper not in _LETTER_TO_HARMONIC:
        raise ValueError(
            f"classify_harmonic: {class_letter!r} is not an A–N class letter "
            f"(valid: {''.join(ALL_CLASS_LETTERS)})"
        )
    return _LETTER_TO_HARMONIC[upper]


def _spectral_scores(hv: np.ndarray) -> Tuple[float, float, float]:
    """Three symmetry scores (dc, mirror, three_cycle) in [0, 1] for a vector.

    - dc: DC-dominance = |Σx| / Σ|x| — a constant / chirality-invariant signal
      concentrates all power at the zero-frequency bin (→ harmonic 1).
    - mirror: even/odd reflection self-agreement = |⟨x, reverse(x)⟩| / ⟨x, x⟩ —
      a mirror-symmetric (period-2) signal scores high (→ harmonic 2).
    - three_cycle: 3-fold rotational self-agreement = |⟨x, roll(x, n/3)⟩| /
      ⟨x, x⟩ for n divisible by 3 — a 3-periodic signal scores high
      (→ harmonic 3). 0 when n is not divisible by 3.
    Pure real-arithmetic symmetry probes. Every magnitude is an EXPLICIT
    Class-K sign-branch (pin-slot: ``x where x >= 0 else -x``) — never an ALU
    ``abs()`` and never the ``sqrt(·²)`` stealth-abs; ``⟨x, x⟩`` energy is a
    Class-L inner product.
    """
    x = np.asarray(hv, dtype=float).reshape(-1)
    n = x.size
    energy = float(np.dot(x, x))
    if n == 0 or energy == 0.0:
        return (0.0, 0.0, 0.0)
    # Σ|x_i| (L1 norm) via the explicit Class-K sign-branch, not sqrt(x²).
    total_mag = float(np.sum(np.where(x >= 0.0, x, -x)))
    s = float(np.sum(x))
    dc = (s if s >= 0.0 else -s) / total_mag if total_mag > 0.0 else 0.0
    d_mirror = float(np.dot(x, x[::-1]))
    mirror = (d_mirror if d_mirror >= 0.0 else -d_mirror) / energy
    if n % 3 == 0:
        rolled = np.roll(x, n // 3)
        d_three = float(np.dot(x, rolled))
        three = (d_three if d_three >= 0.0 else -d_three) / energy
    else:
        three = 0.0
    return (dc, mirror, three)


def classify_chirality_harmonic(hv: np.ndarray, dc_threshold: float = 0.5) -> int:
    """Classify an encoded hypervector into chirality-harmonic 1/2/3 by its
    spectral symmetry signature (F150 §6.2).

    Procedure: compute three symmetry scores (DC-dominance, mirror reflection,
    3-fold rotation). A DC-dominant signal (score ≥ `dc_threshold`) is
    harmonic 1 (chirality-invariant). Otherwise the larger of the mirror /
    3-fold self-agreement scores decides harmonic 2 vs 3 (ties → 2, the
    mirror/self-inverse default). Works on any encoded vector regardless of
    provenance — the spectral generalisation of the surface-form token-name
    classifier (R-RBS-NN-14a).
    """
    x = np.asarray(hv, dtype=float).reshape(-1)
    if x.size == 0:
        raise ValueError("classify_chirality_harmonic: empty vector")
    dc, mirror, three = _spectral_scores(x)
    if dc >= dc_threshold:
        return 1
    return 3 if three > mirror else 2


#: F150 chirality-harmonic ladder coverage. rc12 ships the harmonic-2 mirror
#: variants for Classes D/E/G and the harmonic-3 three-cycle variants for I/L
#: (+ classify_harmonic + the spectral classifier). The ladder is NOT yet
#: complete — these rungs remain OPEN so it finishes rather than silently
#: capping at the rc12 subset (no-silent-caps discipline):
#:   - Harmonic 2 (C, K): explicit chiral-mirror variants for Class C
#:     (cascade-orientation IS chirality) + Class K (pin-slot) — TBD. Class M's
#:     harmonic-2 ALREADY ships as ``srmech.amsc.hdc.klein4_*`` (F132).
#:   - Harmonic 3 (J): ``primes.three_cycle_factor`` is SPECULATIVE — an open
#:     framework question (F150 §6.3), not yet a concrete op.
HARMONIC_LADDER_OPEN_RUNGS = {
    2: ("C", "K"),   # Class M's harmonic-2 already shipped via hdc.klein4_*
    3: ("J",),       # primes.three_cycle_factor — speculative, F150 §6.3
}

__all__ = [
    "HARMONIC_1",
    "HARMONIC_LADDER_OPEN_RUNGS",
    "HARMONIC_2",
    "HARMONIC_3",
    "HARMONIC_PARTITION",
    "ALL_CLASS_LETTERS",
    "classify_harmonic",
    "classify_chirality_harmonic",
]
