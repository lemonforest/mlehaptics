"""Spectrum constructors, each with its exactness TIER DECLARED.

Four closed-form partial spectra, spanning all three tiers, so the tier tag and
the commensurability verdict have something real to decide on:

============================ ====== =========================================
constructor                  tier   carrier
============================ ====== =========================================
``bell_partials``            1      ``Q`` — small-integer ratios, exactly
``equal_temperament_partials`` 2    ``Qalg`` in ℚ[x]/(xᴺ−c)
``stiff_string_partials``    2      ``Qalg`` in ℚ[x]/(x²−r), r ∈ ℚ
``membrane_partials``        3      declared OPEN (Bessel zeros)
============================ ====== =========================================

Every ratio is returned relative to the fundamental ``f₀``, so partial ``n``'s
frequency is ``ratio[n] · f₀``. Nothing here takes a frequency in Hz: the
commensurability question is scale-free, and carrying a unit would only invite
a float.

⚠️ "harmonic" below is always the ACOUSTIC sense (partials, overtones), never
the chirality-order sense that ``harmonics.classify_harmonic`` uses elsewhere in
this tree.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from srmech.amsc.q import Q
from srmech.amsc.qalg import Qalg

__all__ = ["bell_partials", "equal_temperament_partials",
           "stiff_string_partials", "membrane_partials"]

#: Fletcher & Rossing, *The Physics of Musical Instruments* (2nd ed., Springer
#: 1998) §21.3 — the five named partials a bell founder tunes. The ratios are
#: the tuning TARGETS (exact small rationals), not measurements of a cast bell.
_BELL_PROFILE: Tuple[Tuple[str, int, int], ...] = (
    ("hum", 1, 2),        # 1/2
    ("prime", 1, 1),      # 1     (the "fundamental" / strike-note partial)
    ("tierce", 6, 5),     # 6/5   (a minor third — why a bell sounds minor)
    ("quint", 3, 2),      # 3/2
    ("nominal", 2, 1),    # 2
)


def _int_root(value: int, degree: int) -> int:
    """Floor ``degree``-th root of a non-negative int, by pure-integer binary
    search (no float, no math module).

    PRIMITIVE GAP (Class N): the package ships a private ``_integer_sqrt``
    (native ``srmech_isqrt``) but NO public integer ``k``-th root for ``k > 2``,
    so the irreducibility test below has to hand-roll one.
    """
    if value < 2 or degree == 1:
        return value
    lo, hi = 1, 1
    while hi ** degree <= value:
        hi *= 2
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid ** degree <= value:
            lo = mid
        else:
            hi = mid - 1
    return lo


def _is_perfect_power(value: int, degree: int) -> bool:
    """True when ``value`` is an exact ``degree``-th power of an integer."""
    root = _int_root(value, degree)
    return root ** degree == value


def _prime_divisors(n: int) -> List[int]:
    """The distinct primes dividing ``n`` (Class J), via the shipped factoriser."""
    from srmech.math import primes as _primes
    return [p for p, _e in _primes.factor(n)]


def _q_is_square(q: "Q") -> bool:
    """True when the reduced rational ``q >= 0`` is the square of a rational.

    Uses the private native-backed integer sqrt. PRIMITIVE GAP (Class N): there
    is no PUBLIC exact integer-square-root op — ``rational.sqrt`` returns a
    truncated ``Q`` at a declared precision, which cannot decide exactness.
    """
    from srmech.math.rational import _integer_sqrt
    num, den = q.numerator, q.denominator
    if num < 0:
        return False
    rn, rd = _integer_sqrt(num), _integer_sqrt(den)
    return rn * rn == num and rd * rd == den


def _pure_radical_is_irreducible(coeff: int, degree: int) -> bool:
    """Is ``x^degree − coeff`` irreducible over ℚ, for an integer ``coeff ≥ 2``?

    Lang, *Algebra* (3rd ed., Springer 2002) VI §9 Thm 9.1: over a field ``K``,
    ``xⁿ − a`` is irreducible iff ``a`` is not a ``p``-th power in ``K`` for
    every prime ``p | n``, and — when ``4 | n`` — ``a ∉ −4K⁴``. For an integer
    ``a ≥ 2`` the second clause cannot fire (``−4k⁴`` is negative), so the
    prime-power test is the whole test.
    """
    for p in _prime_divisors(degree):
        if _is_perfect_power(coeff, p):
            return False
    return True


def bell_partials() -> Dict[str, object]:
    """The five tuned partials of a bell — **Tier 1** (exact rationals).

    Returns the bell founder's tuning targets from Fletcher & Rossing, *The
    Physics of Musical Instruments* (2nd ed., Springer 1998) §21.3: hum ½,
    prime 1, tierce **6/5**, quint 3/2, nominal 2. Exact small rationals, so the
    carrier is ``Q`` and the spectrum is Tier 1.

    **The finding this constructor exists to expose.** Acousticians call a bell
    *inharmonic* because its partials are not the integer series 1, 2, 3, …. By
    the field-degree invariant it is nothing of the sort: every ratio is
    rational, so the spectrum is exactly COMMENSURABLE — ``verdict ==
    "harmonic"`` with ``integer_series == False``, and a genuine common period
    of ``10·T₀`` (``lcm(2, 1, 5, 2, 1)``). Two different questions wear the same
    word, and separating them is the whole point of the verdict's two fields.

    Returns:
        ``{"ratios": tuple[Q, …], "names": tuple[str, …], "tier": 1,
        "open_partials": (), "profile": "fletcher_rossing_1998_sec_21_3",
        "cite_as": …}``. ``names`` carries the founder's vocabulary in partial
        order — hum, prime, tierce, quint, nominal.
    """
    return {
        "ratios": tuple(Q(n, d) for _name, n, d in _BELL_PROFILE),
        "names": tuple(name for name, _n, _d in _BELL_PROFILE),
        "tier": 1,
        "open_partials": (),
        "profile": "fletcher_rossing_1998_sec_21_3",
        "cite_as": ("Fletcher & Rossing, The Physics of Musical Instruments, "
                    "2nd ed., Springer 1998, sec. 21.3 (tuned-bell partials)"),
    }


def equal_temperament_partials(divisions: int = 12,
                               octave: int = 2,
                               degrees: Sequence[int] = None) -> Dict[str, object]:
    """Equal temperament as EXACT algebraic numbers — **Tier 2**.

    Builds the field ℚ[x]/(x^``divisions`` − ``octave``) and returns the
    requested scale degrees as exact ``Qalg`` powers of its generator ``s``. The
    step ratio ``s`` is the ``divisions``-th root of the octave — irrational,
    and carried EXACTLY rather than approximated.

    This is the verified worked case for the whole module. In ℚ[x]/(x¹²−2):
    ``s⁰`` is rational (1), ``s¹…s¹¹`` are **all** irrational, ``s¹²`` is
    rational (2). Twelve-tone equal temperament is therefore exactly
    representable AND provably incommensurable with the octave except *at* the
    octave — decided by ℚ-membership, with no threshold and no denominator
    ceiling anywhere.

    Args:
        divisions: steps per octave (``>= 1``). Default 12.
        octave: the integer octave ratio (``>= 2``). Default 2.
        degrees: which scale degrees to return; default ``0 … divisions``
            inclusive, i.e. a full octave plus its closing point.

    Returns:
        ``{"ratios": tuple[Qalg, …], "degrees": tuple[int, …], "tier": 2,
        "open_partials": (), "minimal_polynomial": tuple[int, …],
        "field_degree": int}``.

    Raises:
        ValueError: bad ``divisions`` / ``octave`` / ``degrees``, or a
            ``x^divisions − octave`` that is REDUCIBLE — in which case the
            quotient ring is not a field and the ℚ-membership oracle would be
            meaningless, so the constructor refuses rather than answering from a
            broken carrier.
    """
    if not isinstance(divisions, int) or isinstance(divisions, bool) or divisions < 1:
        raise ValueError(
            f"equal_temperament_partials: divisions must be an int >= 1; "
            f"got {divisions!r}")
    if not isinstance(octave, int) or isinstance(octave, bool) or octave < 2:
        raise ValueError(
            f"equal_temperament_partials: octave must be an int >= 2; "
            f"got {octave!r}")
    if divisions > 1 and not _pure_radical_is_irreducible(octave, divisions):
        raise ValueError(
            f"equal_temperament_partials: x^{divisions} - {octave} is REDUCIBLE "
            f"over the rationals, so the quotient ring is not a field and the "
            f"rational-membership oracle would be meaningless. Choose an octave "
            f"that is not a perfect p-th power for any prime p dividing "
            f"{divisions} (e.g. octave=2).")
    if degrees is None:
        degrees = tuple(range(divisions + 1))
    else:
        degrees = tuple(degrees)
        for d in degrees:
            if not isinstance(d, int) or isinstance(d, bool) or d < 0:
                raise ValueError(
                    f"equal_temperament_partials: degrees must be ints >= 0; "
                    f"got {d!r}")
        if not degrees:
            raise ValueError(
                "equal_temperament_partials: degrees must be non-empty")

    m = [-octave] + [0] * (divisions - 1) + [1]     # x^divisions - octave
    step = Qalg.alpha(m)
    ratios: List["Qalg"] = []
    for d in degrees:
        ratios.append(step ** d)
    return {
        "ratios": tuple(ratios),
        "degrees": degrees,
        "tier": 2,
        "open_partials": (),
        "minimal_polynomial": tuple(m),
        "field_degree": divisions,
    }


def stiff_string_partials(inharmonicity, n_partials: int = 8) -> Dict[str, object]:
    """A stiff (piano) string's partials — **Tier 2**, exactly carriable today.

    The textbook closed form is ``f_n = n·f₀·√(1 + B·n²)`` (Fletcher & Rossing,
    *The Physics of Musical Instruments*, 2nd ed., Springer 1998, §2.18 —
    bending stiffness sharpens each partial). With ``B`` rational the ratio to
    the fundamental is ``√(rational)``:

        ``r_n = n·√(1 + B n²) = √(n²(1 + B n²))``

    so each partial is a QUADRATIC SURD and lives exactly in ℚ[x]/(x² − rₙ). No
    approximation is needed anywhere — this whole family was already exactly
    carriable by the shipped ``Qalg``; what was missing was the tier tag and a
    verdict that could read it.

    Each partial gets its OWN quadratic field (the radicands differ), which is
    correct and harmless: commensurability with the fundamental is a per-partial
    ℚ-membership question, and ℚ-membership is field-theoretic in each field
    separately.

    **Built-in control.** At ``inharmonicity == 0`` the radicand collapses to
    ``n²``, a perfect square, so every ratio degenerates to the integer ``n``:
    the constructor returns Tier 1 and the verdict returns ``"harmonic"`` with
    ``integer_series == True`` — the ideal flexible string, recovered exactly.
    A partial whose radicand happens to be a rational square likewise comes back
    as a ``Q``; the tier reported is the honest per-spectrum weakest.

    Args:
        inharmonicity: the stiffness coefficient ``B >= 0``, as ``Q``, ``int``
            or an ``(int, int)`` pair. Must be EXACT — a float would silently
            make every radicand a float-rational and collapse the whole
            distinction, so floats are refused.
        n_partials: how many partials to return, ``n = 1 … n_partials``
            (``>= 1``). Default 8.

    Returns:
        ``{"ratios": tuple[Qalg | Q, …], "orders": tuple[int, …], "tier": 1|2,
        "open_partials": (), "inharmonicity": Q, "radicands": tuple[Q, …],
        "cite_as": …}``.

    Raises:
        TypeError: a float ``inharmonicity``.
        ValueError: negative ``inharmonicity`` or ``n_partials < 1``.
    """
    if isinstance(inharmonicity, float):
        raise TypeError(
            "stiff_string_partials: inharmonicity must be EXACT (Q, int or an "
            "(int, int) pair), not a float — a float B makes every radicand a "
            "float-rational and collapses the Tier-1/Tier-2 distinction this "
            "constructor exists to expose.")
    if isinstance(inharmonicity, bool):
        raise TypeError("stiff_string_partials: inharmonicity must not be bool")
    if isinstance(inharmonicity, int):
        b = Q(inharmonicity, 1)
    elif isinstance(inharmonicity, Q):
        b = inharmonicity
    elif (isinstance(inharmonicity, (tuple, list)) and len(inharmonicity) == 2
            and isinstance(inharmonicity[0], int)
            and isinstance(inharmonicity[1], int) and inharmonicity[1] != 0):
        b = Q(inharmonicity[0], inharmonicity[1])
    else:
        raise TypeError(
            f"stiff_string_partials: inharmonicity must be Q, int or an "
            f"(int, int) pair; got {type(inharmonicity).__name__}")
    if b < Q(0, 1):
        raise ValueError(
            f"stiff_string_partials: inharmonicity B must be >= 0; got {b!r}")
    if not isinstance(n_partials, int) or isinstance(n_partials, bool) or n_partials < 1:
        raise ValueError(
            f"stiff_string_partials: n_partials must be an int >= 1; "
            f"got {n_partials!r}")

    ratios: List[object] = []
    radicands: List["Q"] = []
    tier = 1
    for n in range(1, n_partials + 1):
        radicand = Q(n * n, 1) * (Q(1, 1) + b * Q(n * n, 1))
        radicands.append(radicand)
        if _q_is_square(radicand):
            # The surd degenerates: the ratio IS rational. Emit it as such
            # rather than dressing it in a reducible quadratic "field".
            from srmech.math.rational import _integer_sqrt
            ratios.append(Q(_integer_sqrt(radicand.numerator),
                            _integer_sqrt(radicand.denominator)))
            continue
        tier = 2
        # x^2 - radicand, cleared to monic ℤ[x]: the surd √(p/q) equals
        # √(p·q)/q, so carry the integer radicand p·q and scale by 1/q.
        p, q = radicand.numerator, radicand.denominator
        m = [-(p * q), 0, 1]
        ratios.append(Qalg.alpha(m) * Q(1, q))
    return {
        "ratios": tuple(ratios),
        "orders": tuple(range(1, n_partials + 1)),
        "tier": tier,
        "open_partials": (),
        "inharmonicity": b,
        "radicands": tuple(radicands),
        "cite_as": ("Fletcher & Rossing, The Physics of Musical Instruments, "
                    "2nd ed., Springer 1998, sec. 2.18 (stiff-string partials)"),
    }


def membrane_partials(n_orders: int = 3,
                      m_zeros: int = 3,
                      *,
                      scale_bits: int = 128) -> Dict[str, object]:
    """A circular membrane's partials — **Tier 3, DECLARED OPEN**.

    The modal frequencies of an ideal circular membrane are proportional to the
    zeros of the Bessel functions: ``f_{n,m} ∝ j_{n,m}``, so the ratio to the
    fundamental is ``j_{n,m} / j_{0,1}`` (Fletcher & Rossing, *The Physics of
    Musical Instruments*, 2nd ed., Springer 1998, §3.2). That is why a drum has
    no pitch in the way a string does.

    **Every partial is declared Tier 3, and nothing is asserted about why.**
    The returned ratios are exact rationals *of declared precision* computed
    from ``bessel_zero_fixed`` — they are NOT claimed to be the true values, and
    the true values are NOT claimed to be transcendental, algebraic-irrational,
    or rational. DLMF 10.21 was fetched and contains no transcendence statement;
    Siegel's theorem was never fetched. The honest position is that the
    field-theoretic status is **UNRESOLVED**, so the tier is declared open and
    every commensurability verdict over this spectrum returns ``"open"`` — never
    ``"harmonic"``, which is exactly what reading a ``best_rational`` anchor off
    these rationals would have produced.

    Args:
        n_orders: how many Bessel orders ``n = 0 … n_orders−1`` (``>= 1``).
        m_zeros: how many zeros per order, ``m = 1 … m_zeros`` (``>= 1``).
        scale_bits: the DECLARED fixed-point precision of the zeros. Default
            128 (the modal ratios need far less than the Bessel default, and a
            lower scale keeps the Newton refinement cheap).

    Returns:
        ``{"ratios": tuple[Q, …], "modes": tuple[(n, m), …], "tier": 3,
        "open_partials": tuple(all indices), "scale_bits": int,
        "declared_precision_only": True, "transcendence_claim": "NONE …",
        "cite_as": …}``. Pass ``open_partials`` straight through to
        ``spectrum_tier`` / ``commensurability_verdict``.

    Raises:
        ValueError: ``n_orders < 1``, ``m_zeros < 1``, or a bad ``scale_bits``.
    """
    if not isinstance(n_orders, int) or isinstance(n_orders, bool) or n_orders < 1:
        raise ValueError(
            f"membrane_partials: n_orders must be an int >= 1; got {n_orders!r}")
    if not isinstance(m_zeros, int) or isinstance(m_zeros, bool) or m_zeros < 1:
        raise ValueError(
            f"membrane_partials: m_zeros must be an int >= 1; got {m_zeros!r}")
    from ._bessel import bessel_zero_fixed

    base_num, base_den = bessel_zero_fixed(0, 1, scale_bits=scale_bits)
    base = Q(base_num, base_den)
    modes: List[Tuple[int, int]] = []
    ratios: List["Q"] = []
    for n in range(n_orders):
        for mm in range(1, m_zeros + 1):
            num, den = bessel_zero_fixed(n, mm, scale_bits=scale_bits)
            modes.append((n, mm))
            ratios.append(Q(num, den) / base)
    return {
        "ratios": tuple(ratios),
        "modes": tuple(modes),
        "tier": 3,
        "open_partials": tuple(range(len(ratios))),
        "scale_bits": scale_bits,
        "declared_precision_only": True,
        "transcendence_claim": (
            "NONE. Whether Bessel zeros are transcendental or "
            "algebraic-irrational is OPEN in this project. DLMF 10.21 states "
            "nothing on it and Siegel's theorem was never fetched, so no claim "
            "either way is made here. These are rationals of declared "
            "precision only."),
        "cite_as": ("Fletcher & Rossing, The Physics of Musical Instruments, "
                    "2nd ed., Springer 1998, sec. 3.2 (circular-membrane "
                    "modes); DLMF 10.21 (Bessel zeros)"),
    }
