"""Spectral commensurability — the tier tag and a verdict that CAN say
"inharmonic".

⚠️ **Two different words spelled "harmonic".** Everywhere else in this tree,
"harmonic" means **chirality order** — ``harmonics.classify_harmonic`` maps an
A–N class letter to its position in ``HARMONIC_PARTITION``, and has nothing to
do with sound. This module is the ACOUSTIC sense: a partial, an overtone, a
frequency ratio. The two never meet, and nothing here imports or extends the
chirality-order surface. Names in this package are chosen so they cannot be
mistaken for it.

WHY A NEW VERDICT WAS NEEDED
============================
The tree could already gauge commensurability two ways, and **neither can
return "inharmonic"**:

* **Class-I gcd / lcm** structurally cannot. A finite set of rational ratios
  ALWAYS has an lcm, so a period always exists. The instrument has one needle.
* **Class-N ``best_rational``** is worse than silent: it does not *approximate*
  an inharmonic spectrum, it **CONVERTS** it into a harmonic one. Measured — an
  irrational target read at ``max_den`` 10²/10⁴/10⁶ returns 22/7, 355/113,
  2917129/928551, i.e. finite periods of ``T₀·7``, ``T₀·113``, ``T₀·928551``.
  A finite period IS commensurability IS harmonicity. Raising ``max_den`` never
  reaches a verdict; it only buys a longer false period. (The convergent
  denominators of an irrational diverge monotonically — 1, 2, 5, 12, 29, 70, …,
  195025 — and never close, which is the tell.)

THE RIGHT INVARIANT IS FIELD DEGREE / RATIONAL RANK, NOT A PERIOD
=================================================================
``Qalg`` already supplies a decidable oracle, and it is a genuine invariant:
membership in ℚ inside ℚ[x]/(m) is field-theoretic — ℚ is the unique degree-1
subfield of ℚ(α) — so it survives any change of ℚ-basis. It is not a
presentation count.

Measured, in ℚ[x]/(x¹²−2): ``s⁰`` rational **True**, ``s¹…s¹¹`` **all False**,
``s¹²`` **True**. Twelve-tone equal temperament is exactly represented AND
provably incommensurable with the octave except *at* the octave. No threshold,
no denominator ceiling, no approximation — a decision.

THE THREE TIERS
===============
============ ======================================= ==================
Tier         carrier                                  decidable?
============ ======================================= ==================
1 rational   ``Q`` / ``int``                           yes — exactly
2 algebraic  ``Qalg`` (``α²==2`` holds *in the field*) yes — exactly
3 open       none                                      **no**
============ ======================================= ==================

Tier 3 has no exact carrier by construction: ``Qalg.alpha`` REJECTS a
non-integer minimal polynomial (``ValueError``), so a transcendental cannot be
smuggled in as if it were exact. It follows that **Tier 3 must be DECLARED, not
inferred** — a rational of declared precision standing in for a transcendental
is indistinguishable, from the carrier alone, from a rational. Only the
constructor knows the provenance, so only the constructor can declare it. That
asymmetry is the honesty layer, not a gap in it.

The precedent is already in the tree: ``coupling.fractal_spectrum`` returns a
``spectrum_open`` string rather than a list, because no finite exact carrier
decides Julia-set membership. Its peer ``coupling.resonant_spectrum`` gauges
commensurability with ``best_rational`` + a Class-J lock **only inside ℚ** —
which is the silent-harmonisation bug above. The gap was a missing TIER TAG,
not a missing idea.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

from srmech.amsc.q import Q
from srmech.amsc.qalg import Qalg

__all__ = ["spectrum_tier", "commensurability_verdict", "common_period"]

#: Tier 1 — an exact rational carrier (``Q`` / ``int``). Commensurability with
#: the fundamental is decided by inspection.
TIER_RATIONAL: int = 1
#: Tier 2 — an exact ALGEBRAIC-IRRATIONAL carrier (``Qalg``). Still exact, still
#: decidable: ``α² == 2`` holds *in the field*, and rationality is the
#: field-theoretic ℚ-membership test.
TIER_ALGEBRAIC: int = 2
#: Tier 3 — no exact carrier exists. Transcendence UNRESOLVED or known-absent;
#: any number present is a rational of DECLARED precision, and every verdict
#: over such a spectrum is ``"open"``.
TIER_OPEN: int = 3

_TIER_NAMES = {
    TIER_RATIONAL: "rational",
    TIER_ALGEBRAIC: "algebraic",
    TIER_OPEN: "open",
}

_OPEN_REASON = (
    "at least one partial is Tier 3: no finite exact carrier holds its value, "
    "so its ℚ-membership is UNDECIDED. The number present is a rational of "
    "DECLARED PRECISION standing in for it — reading a period off that rational "
    "would report the precision's period, not the spectrum's."
)

_CLASS_I_NOTE = (
    "Class-I gcd/lcm cannot produce this verdict: a finite set of rational "
    "ratios always has an lcm, so it always yields a finite period and can "
    "never return 'inharmonic'. The invariant here is FIELD DEGREE / RATIONAL "
    "RANK — ℚ-membership inside ℚ[x]/(m), which is basis-free."
)

_CLASS_N_WARNING = (
    "Class-N best_rational must NOT be used to gauge this. It does not "
    "approximate an inharmonic spectrum — it CONVERTS it into a harmonic one: "
    "every anchor p/q is a finite period T0*q. Raising max_den only buys a "
    "longer false period, never a verdict."
)


def _coerce_ratio(value, index: int):
    """Normalise one partial-to-fundamental ratio to ``Q`` or ``Qalg``.

    ``int`` / ``Q`` pass to ``Q``; a ``(num, den)`` pair is accepted; ``Qalg``
    passes through. A ``float`` is REFUSED on purpose — a float has already lost
    the distinction this module exists to make (every float IS a rational, so a
    float spectrum is unconditionally Tier 1 and unconditionally "harmonic",
    which is exactly the silent harmonisation being fixed).
    """
    if isinstance(value, Qalg):
        return value
    if isinstance(value, Q):
        return value
    if isinstance(value, bool):
        raise TypeError(
            f"partial[{index}]: bool is not a frequency ratio")
    if isinstance(value, int):
        return Q(value, 1)
    if (isinstance(value, (tuple, list)) and len(value) == 2
            and isinstance(value[0], int) and isinstance(value[1], int)
            and value[1] != 0):
        return Q(value[0], value[1])
    if isinstance(value, float):
        raise TypeError(
            f"partial[{index}]: float ratios are refused. Every float IS a "
            "rational, so a float spectrum is unconditionally Tier 1 and "
            "unconditionally commensurable — the exact silent harmonisation "
            "this op exists to make impossible. Pass Q for an exact rational "
            "or Qalg for an exact algebraic irrational.")
    raise TypeError(
        f"partial[{index}]: expected Q, Qalg, int or an (int, int) pair; "
        f"got {type(value).__name__}")


def _normalise_open(open_partials: Iterable[int], n: int) -> Tuple[int, ...]:
    out: List[int] = []
    for idx in open_partials:
        if not isinstance(idx, int) or isinstance(idx, bool):
            raise TypeError(
                f"open_partials must be integer indices; got {idx!r}")
        if idx < 0 or idx >= n:
            raise ValueError(
                f"open_partials index {idx} out of range for {n} partials")
        if idx not in out:
            out.append(idx)
    return tuple(sorted(out))


def _read(partials: Sequence, open_partials: Iterable[int]):
    """Shared read: coerce every ratio, classify each, return the per-partial
    records plus the declared-open index set. One source of truth for
    :func:`spectrum_tier`, :func:`commensurability_verdict` and
    :func:`common_period`, so the three can never disagree."""
    if isinstance(partials, (str, bytes)) or not isinstance(partials, Sequence):
        raise TypeError(
            "partials must be a sequence of frequency ratios (Q / Qalg / int)")
    if len(partials) == 0:
        raise ValueError("partials must be a non-empty sequence")
    opened = _normalise_open(open_partials, len(partials))
    rows: List[Dict[str, object]] = []
    for i, raw in enumerate(partials):
        value = _coerce_ratio(raw, i)
        if isinstance(value, Qalg):
            rational = value.is_rational()
            degree = value.degree
            carrier = "Qalg"
        else:
            rational = True
            degree = 1
            carrier = "Q"
        if i in opened:
            tier = TIER_OPEN
            rational = None          # UNDECIDED, not False
        elif rational:
            tier = TIER_RATIONAL
        else:
            tier = TIER_ALGEBRAIC
        rows.append({
            "index": i,
            "carrier": carrier,
            "tier": tier,
            "tier_name": _TIER_NAMES[tier],
            "field_degree": degree,
            "in_rationals": rational,
            "value": value,
        })
    return rows, opened


def spectrum_tier(partials: Sequence,
                  *,
                  open_partials: Iterable[int] = ()) -> Dict[str, object]:
    """TIER-TAG a spectrum — the honesty layer over any spectrum-carrying value.

    Reports which of the three exactness tiers a spectrum actually sits in, so a
    downstream reader can never mistake "a rational of declared precision" for
    "an exact rational". The spectrum's tier is the WEAKEST of its partials'.

    Tier 1 and Tier 2 are INFERRED from the carrier (``Q``/``int`` vs a ``Qalg``
    that is not in ℚ). Tier 3 must be **DECLARED** via ``open_partials``,
    because it cannot be inferred: a rational standing in for a transcendental
    is, as a carrier, just a rational. Only the constructor knows.

    Args:
        partials: a non-empty sequence of partial-to-fundamental frequency
            RATIOS, each ``Q``, ``Qalg``, ``int`` or an ``(int, int)`` pair.
            ``float`` is refused — see the type error for why.
        open_partials: indices whose true value has NO exact carrier
            (transcendental, or transcendence unresolved). Declared by the
            constructor that produced them.

    Returns:
        A dict with ``"tier"`` / ``"tier_name"`` (the spectrum's, i.e. the
        weakest), ``"exact"`` (False only at Tier 3), ``"n_partials"``,
        ``"per_partial"`` (one record each: index, carrier, tier, field_degree,
        in_rationals — ``None`` at Tier 3 meaning UNDECIDED), ``"open_indices"``
        and ``"open_reason"`` (``None`` unless Tier 3).

    Raises:
        TypeError: a float ratio, or an unsupported carrier.
        ValueError: an empty spectrum, or an out-of-range open index.
    """
    rows, opened = _read(partials, open_partials)
    tier = max(int(r["tier"]) for r in rows)
    per_partial = [{k: v for k, v in r.items() if k != "value"} for r in rows]
    return {
        "tier": tier,
        "tier_name": _TIER_NAMES[tier],
        "exact": tier != TIER_OPEN,
        "n_partials": len(rows),
        "per_partial": per_partial,
        "open_indices": opened,
        "open_reason": _OPEN_REASON if tier == TIER_OPEN else None,
    }


def commensurability_verdict(partials: Sequence,
                             *,
                             open_partials: Iterable[int] = ()) -> Dict[str, object]:
    """Decide whether a spectrum is commensurable with its fundamental — a
    verdict that **can** return ``"inharmonic"``.

    The invariant is RATIONAL RANK: how many partial-to-fundamental ratios lie
    in ℚ. Every ratio in ℚ ⇒ every pairwise ratio in ℚ ⇒ a common period exists
    (``"harmonic"``). Any ratio provably NOT in ℚ ⇒ that partial shares no
    period with the fundamental at any multiple, ever (``"inharmonic"``). This
    is decided, not estimated: ℚ-membership inside ℚ[x]/(m) is field-theoretic
    and basis-free. No ``best_rational``, no denominator ceiling and no
    threshold is consulted anywhere in the decision.

    **Two senses of "harmonic", kept apart.** ``"verdict"`` answers
    *commensurable?*; ``"integer_series"`` answers the classical acoustics
    question *are the ratios the plain integer series 1, 2, 3, …?*. They come
    apart, and the split is the point — a tuned bell's canonical partials
    (½, 1, 6/5, 3/2, 2) are called *inharmonic* by acousticians because they are
    not the integer series, yet they are all rational, hence exactly
    commensurable, hence ``verdict == "harmonic"`` with ``integer_series ==
    False``. Reporting one number for both questions is what hides the
    distinction.

    Args:
        partials: partial-to-fundamental frequency ratios (see
            :func:`spectrum_tier`).
        open_partials: indices declared Tier 3 by their constructor.

    Returns:
        A dict with ``"verdict"`` (``"harmonic"`` / ``"inharmonic"`` /
        ``"open"``), ``"integer_series"``, ``"rational_rank"``,
        ``"n_partials"``, ``"field_degrees"``, ``"incommensurable"`` (indices
        provably outside ℚ), ``"open_indices"``, ``"tier"`` / ``"tier_name"``,
        ``"period_multiplier"`` (the integer ``k`` with common period ``k·T₀``,
        present only when harmonic — otherwise ``None``), plus the two standing
        notes ``"class_i_note"`` and ``"class_n_warning"`` that record WHY the
        two pre-existing gauges cannot answer this.

    Raises:
        TypeError / ValueError: as :func:`spectrum_tier`.
    """
    rows, opened = _read(partials, open_partials)
    tier = max(int(r["tier"]) for r in rows)
    incommensurable = tuple(int(r["index"]) for r in rows
                            if r["in_rationals"] is False)
    rational_rank = sum(1 for r in rows if r["in_rationals"] is True)

    if opened:
        verdict = "open"
    elif incommensurable:
        verdict = "inharmonic"
    else:
        verdict = "harmonic"

    integer_series = (
        verdict == "harmonic"
        and all(_as_q(r["value"]).denominator == 1 for r in rows))

    period = _period_multiplier(rows) if verdict == "harmonic" else None

    return {
        "verdict": verdict,
        "integer_series": integer_series,
        "rational_rank": rational_rank,
        "n_partials": len(rows),
        "field_degrees": tuple(int(r["field_degree"]) for r in rows),
        "incommensurable": incommensurable,
        "open_indices": opened,
        "tier": tier,
        "tier_name": _TIER_NAMES[tier],
        "period_multiplier": period,
        "class_i_note": _CLASS_I_NOTE,
        "class_n_warning": _CLASS_N_WARNING,
    }


def _as_q(value) -> "Q":
    """The exact ``Q`` of a ratio already known to lie in ℚ."""
    if isinstance(value, Qalg):
        return value.as_rational()
    return value


def _period_multiplier(rows) -> int:
    """The integer ``k`` such that ``k·T₀`` is the common period — ``lcm`` of
    the reduced ratio denominators (Class-I). A partial at ``p/q`` completes a
    whole number of cycles in ``k·T₀`` exactly when ``q | k``."""
    from srmech.math import cyclic as _cyclic
    k = 1
    for r in rows:
        k = _cyclic.lcm(k, _as_q(r["value"]).denominator)
    return int(k)


def common_period(partials: Sequence,
                  *,
                  open_partials: Iterable[int] = ()) -> int:
    """The common period of a spectrum, as an integer multiple of ``T₀`` — and
    the GUARD that makes silent harmonisation impossible.

    Returns ``k`` with common period ``k·T₀`` (``T₀ = 1/f₀``) when, and only
    when, :func:`commensurability_verdict` says ``"harmonic"``. For an
    ``"inharmonic"`` or ``"open"`` spectrum it **raises** — there is no period
    to return, and returning a ``best_rational`` anchor instead would silently
    convert the spectrum into a harmonic one. That conversion is the corruption
    this op exists to make unreachable: the only way to obtain a period from
    this module is to have earned the verdict first.

    Args:
        partials: partial-to-fundamental frequency ratios.
        open_partials: indices declared Tier 3 by their constructor.

    Returns:
        The integer period multiplier ``k`` (Class-I ``lcm`` of the reduced
        ratio denominators).

    Raises:
        ValueError: the spectrum is ``"inharmonic"`` or ``"open"`` — the message
            names the offending partial indices and why no period exists.
        TypeError: as :func:`spectrum_tier`.
    """
    rows, opened = _read(partials, open_partials)
    incommensurable = tuple(int(r["index"]) for r in rows
                            if r["in_rationals"] is False)
    if opened:
        raise ValueError(
            f"common_period: spectrum is OPEN at partial indices {list(opened)} "
            f"(Tier 3). {_OPEN_REASON} No period is returned. {_CLASS_N_WARNING}")
    if incommensurable:
        raise ValueError(
            f"common_period: spectrum is INHARMONIC — partial indices "
            f"{list(incommensurable)} are provably NOT in the rationals "
            f"(field-degree oracle), so they share no period with the "
            f"fundamental at any multiple. {_CLASS_N_WARNING}")
    return _period_multiplier(rows)
