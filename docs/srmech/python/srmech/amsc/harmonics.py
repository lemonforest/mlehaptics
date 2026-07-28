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

Pure-Python (numpy-free, #564); no new C surface (harmonic classification is
framework-level composition over the existing A–N primitives). Class-L
(spectral) read of the chirality structure, carried on the **exact Class-N
rational** :class:`~srmech.amsc.q.Q` since rc354 — see `_spectral_scores`.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from . import cyclic as _cyclic
from .q import Q, to_q

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


#: the exact Class-N zero — the score of a vector with no power in it.
_Q_ZERO = Q(0)


def _flat_scalars(hv) -> List:
    """Flatten a ``Vec`` / ``Mat`` / nested-or-flat sequence to plain scalars.

    A :class:`~srmech.amsc.mat.Mat` iterates ROW-WISE (``mat.py:192`` yields
    lists), so a rank-2 carrier has to be descended one level; a
    :class:`~srmech.amsc.vec.Vec` (``vec.py:127``) already yields scalars.
    Numpy-free; ``.tolist()`` is a carrier convert, not an ndarray hop.

    rc354 defect note: before this helper existed the module read ``[float(v)
    for v in hv]`` directly, so the docstring's advertised ``Mat`` input raised
    ``TypeError: float() argument must be … not 'list'``. The claim is now true.
    """
    seq = hv.tolist() if hasattr(hv, "tolist") else hv
    flat: List = []
    for elem in seq:
        if isinstance(elem, (list, tuple)):
            flat.extend(elem)
        else:
            flat.append(elem)
    return flat


def _common_denominator(xs) -> int:
    """The Class-I lcm of the exact denominators: the ONE scale on which the
    whole vector becomes integers with nothing rounded away.

    Every ``Q`` is already reduced, so ``lcm(a, b) = a // gcd(a, b) * b`` over
    ``cyclic.gcd`` (``srmech/amsc/cyclic.py:114``) is exact and never overflows
    intermediate. For a vector of ``float``s every denominator is a power of two
    and this collapses to the largest of them.
    """
    scale = 1
    for q in xs:
        den = q.denominator
        scale = scale // _cyclic.gcd(scale, den) * den
    return scale


def _scores_exact(xs) -> Tuple[Q, Q, Q]:
    """The three scores over an ALREADY-coerced list of :class:`Q` (no re-coerce).

    Split out from :func:`_spectral_scores` so the classifier converts the input
    exactly ONCE — rc353 and earlier converted twice (``classify_chirality_harmonic``
    floated the vector, then ``_spectral_scores`` floated the result again).
    """
    n = len(xs)
    if n == 0:
        return (_Q_ZERO, _Q_ZERO, _Q_ZERO)

    # Put the vector on one common denominator D. Every score below is a RATIO
    # of two sums taken on that same D (dc: both linear in D; mirror/three: both
    # quadratic), so D cancels identically and each score is an exact ratio of
    # two INTEGERS — the whole probe runs in bignum integers, no rational
    # arithmetic in the loop, and the Class-N Q is formed once per score.
    scale = _common_denominator(xs)
    m = [q.numerator * (scale // q.denominator) for q in xs]

    energy = sum(mi * mi for mi in m)  # Class-L inner product ⟨x, x⟩ × D²
    if energy == 0:
        # Exactly the all-zero vector, and ONLY that: an integer square-sum is
        # zero iff every term is. rc353's float test ``energy == 0.0`` also
        # fired on underflow — ``[1e-200] * 3`` (a CONSTANT vector, the flagship
        # harmonic-1 shape) squared to 0.0 and misclassified as harmonic 2.
        return (_Q_ZERO, _Q_ZERO, _Q_ZERO)

    # Σ|x_i| (L1 norm) via the explicit Class-K sign-branch, not sqrt(x²).
    # energy > 0 ⟹ some m_i ≠ 0 ⟹ total_mag > 0, so no zero-divisor guard is
    # reachable here; rc353 carried one because floats made the implication
    # non-exact. A dead branch would only be a place for a false green to hide.
    total_mag = sum(mi if mi >= 0 else -mi for mi in m)
    s = sum(m)
    dc = Q(s if s >= 0 else -s, total_mag)

    d_mirror = sum(m[i] * m[n - 1 - i] for i in range(n))  # ⟨x, reverse(x)⟩
    mirror = Q(d_mirror if d_mirror >= 0 else -d_mirror, energy)

    if n % 3 == 0:
        k = n // 3
        # roll(x, k): rolled[i] = x[(i - k) mod n]; ⟨x, roll(x, n/3)⟩.
        d_three = sum(m[i] * m[(i - k) % n] for i in range(n))
        three = Q(d_three if d_three >= 0 else -d_three, energy)
    else:
        three = _Q_ZERO
    return (dc, mirror, three)


def _spectral_scores(hv) -> Tuple[Q, Q, Q]:
    """Three EXACT symmetry scores (dc, mirror, three_cycle) in [0, 1].

    - dc: DC-dominance = |Σx| / Σ|x| — a constant / chirality-invariant signal
      concentrates all power at the zero-frequency bin (→ harmonic 1).
    - mirror: even/odd reflection self-agreement = |⟨x, reverse(x)⟩| / ⟨x, x⟩ —
      a mirror-symmetric (period-2) signal scores high (→ harmonic 2).
    - three_cycle: 3-fold rotational self-agreement = |⟨x, roll(x, n/3)⟩| /
      ⟨x, x⟩ for n divisible by 3 — a 3-periodic signal scores high
      (→ harmonic 3). 0 when n is not divisible by 3.

    **rc354 — the scores are exact Class-N rationals, not floats.** Each input
    element is promoted to the exact :class:`~srmech.amsc.q.Q` of its own value
    (``to_q``: a float's ``as_integer_ratio`` is EXACT, so nothing is
    approximated on the way in), and each score comes back as a ``Q``. Call
    ``float(score)`` for a rendering. Every magnitude is an EXPLICIT Class-K
    sign-branch (pin-slot: ``x where x >= 0 else -x``) — never an ALU ``abs()``
    and never the ``sqrt(·²)`` stealth-abs; ``⟨x, x⟩`` energy is a Class-L
    inner product; numpy-free (#564), libm-free.
    """
    return _scores_exact([to_q(v) for v in _flat_scalars(hv)])


def classify_chirality_harmonic(hv, dc_threshold=0.5) -> int:
    """Classify an encoded hypervector into chirality-harmonic 1/2/3 by its
    spectral symmetry signature (F150 §6.2).

    ``hv`` may be a :class:`~srmech.amsc.vec.Vec` / :class:`~srmech.amsc.mat.Mat`
    / any flat or nested ``Sequence`` (rc129; the ``Mat`` path is real as of
    rc354 — see :func:`_flat_scalars`). ``dc_threshold`` accepts an ``int``, a
    ``float`` or an exact :class:`~srmech.amsc.q.Q`; a float is promoted by its
    EXACT ``as_integer_ratio`` (the 0.5 default is exactly ``Q(1, 2)``), so the
    comparison at the boundary is decided in the rationals, never in binary.

    Procedure: compute three symmetry scores (DC-dominance, mirror reflection,
    3-fold rotation). A DC-dominant signal (score ≥ `dc_threshold`) is
    harmonic 1 (chirality-invariant). Otherwise the larger of the mirror /
    3-fold self-agreement scores decides harmonic 2 vs 3 (ties → 2, the
    mirror/self-inverse default). Works on any encoded vector regardless of
    provenance — the spectral generalisation of the surface-form token-name
    classifier (R-RBS-NN-14a).
    """
    # rc154 (BATCH B10, ``composition_of_c``): the classifier is a pure
    # composition of primitive-class ops over the vector — **Class-L** inner
    # products (⟨x,x⟩, ⟨x,rev(x)⟩, ⟨x,roll(x)⟩), **Class-K** magnitude pin-slots
    # (the explicit ``x if x >= 0 else -x`` L1 / DC branches — no ``abs()``, no
    # ``sqrt(·²)`` stealth-abs), and **Class-N** exact ratios; the verdict is a
    # discrete 1/2/3 label. Reaches no non-standalone leaf → C-portable /
    # standalone-ready over the ``srmech_bigint`` / ``srmech_q`` peers (the C
    # projection must carry the SAME exact arithmetic, not a naive double fold
    # — see the rc354 parity note below). No new C symbol.
    #
    # rc354 — WHY EXACT, MEASURED. rc353 read the vector as ``float`` and the
    # "Class-N exact ratios" claim above was false of the code. Three reachable
    # defect families, each reproduced against the shipped rc353 op:
    #   (i)  entries past 2⁵³ — ``[3*(2**53-1), -(2**53-1)]`` has exact
    #        dc = 1/2 → harmonic 1, and returned 2 on every interpreter,
    #        because the loss is in ``float(v)`` BEFORE any summing;
    #   (ii) INTERPRETER-DEPENDENT verdicts — CPython ≥ 3.12 made built-in
    #        ``sum()`` Neumaier-compensated, so an all-double vector with exact
    #        dc = 1/2 classified 2 on 3.10/3.11 and 1 on 3.12+, while
    #        ``requires-python`` is ``>=3.10`` (``pyproject.toml:43``). A C
    #        projection does a naive fold, so it tracked 3.11 — a live
    #        multi-implementation parity break (ADR-0009), not a hypothetical;
    #   (iii) UNDERFLOW — ``[1e-200] * 3``, a CONSTANT vector (exact dc = 1),
    #        squared to ``energy == 0.0`` and returned harmonic 2 at no
    #        boundary at all, on every interpreter.
    # THE HONEST NULL: the documented ±1-hypervector domain was NEVER at risk,
    # and that is provable rather than merely unobserved — ``Σx`` and ``Σ|x|``
    # are exact small integers for n < 2⁵³ and IEEE division is correctly
    # rounded, so an exact 1/2 renders as exactly 0.5. Exhaustive over every
    # dc == 1/2 partition for n = 2..20: zero differentials. This is a
    # correctness repair at the edges, NOT "the classifier was returning wrong
    # harmonics" on its own worked domain.
    xs = [to_q(v) for v in _flat_scalars(hv)]
    if len(xs) == 0:
        raise ValueError("classify_chirality_harmonic: empty vector")
    threshold = to_q(dc_threshold)
    dc, mirror, three = _scores_exact(xs)
    if dc >= threshold:
        return 1
    return 3 if three > mirror else 2


#: F150 chirality-harmonic ladder coverage. rc12 shipped the harmonic-2 mirror
#: variants for Classes D/E/G and the harmonic-3 three-cycle variants for I/L
#: (+ classify_harmonic + the spectral classifier). The ladder is now FULLY
#: CLOSED — NO class remains open (the §74 / F923 capstone; no encode blind
#: spots left). The closure record:
#:   - Harmonic 2 (C, K): CLOSED at 0.9.0rc31 (F924 / UPSTREAM §74). The exact
#:     POLAR accessors on the ``Qi`` carrier ship both: ``Qi.arg()`` is the
#:     Class-C orientation (which-way; ``atan2`` quadrant logic) and
#:     ``Qi.modulus()`` the Class-K magnitude (``√(re²+im²)``, never ``abs()``).
#:     The magnetic-Laplacian read (θ_fwd+θ_rev=0, direction-blind modulus) is
#:     the closure demonstration. Class M's harmonic-2 had already shipped as
#:     ``srmech.amsc.hdc.klein4_*`` (F132).
#:   - Harmonic 3 (J): CLOSED at 0.9.0rc32 (F923 / UPSTREAM §74, the CAPSTONE).
#:     The exact prime-coordinate carrier ``srmech.amsc.qprime.Qprime`` ships the
#:     Class-J multiplicative-period structure: multiply=add-exponents
#:     (==``factor(a·b)``), gcd=min, lcm=max, exact cosine² similarity, and the
#:     multiplicative-order ``Qprime.period(m)`` (the 1/m repeating-period lens,
#:     ``ord₇(10)==6``) over ``primes.factor`` + ``primes.cyclic_period``.
#: ALL ENCODE RUNGS CLOSED: C/K via Qi (rc31), J via Qprime (rc32). The ladder
#: is empty — every A–N class is reachable, no harmonic blind spot remains.
HARMONIC_LADDER_OPEN_RUNGS = {
    2: (),           # CLOSED rc31 — Qi.arg() (Class C) + Qi.modulus() (Class K), F924
    3: (),           # CLOSED rc32 — Qprime (Class J multiplicative-period), F923 §74 CAPSTONE
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
