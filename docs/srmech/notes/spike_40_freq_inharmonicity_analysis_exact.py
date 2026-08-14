"""Spike #40 EXACT PORT of ``spike_40_freq_inharmonicity_analysis.py`` (2026-07-30).

This is the port where the three generating forms genuinely differ in KIND,
and the exact carriers make the difference visible instead of flattening it
into one float array:

  piano   f_n = n*f0*sqrt(1 + B*n^2), B rational
          -> ALGEBRAIC IRRATIONAL. For each n, f_n/f0 lives in the quadratic
             field Q(sqrt((1+B n^2)(1+B))) and is carried exactly in
             ``srmech.amsc.qalg.Qalg``; the port PROVES the field membership
             (alpha^2 == the rational) before lifting to a Class-N rational
             sqrt for the log-domain K-test.
  bell    canonical ratios (0.5, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.4, 6.0)
          -> RATIONAL. Exact in ``Q``; note 1.2 = 6/5 and 5.4 = 27/5, neither
             of which is a double.
  drum    f_n = the m-th positive zero of J_n
          -> NEITHER. GAP-2: no srmech peer, and whether these are
             transcendental or algebraic-irrational is an OPEN Tier-3
             question in this project. They are handled as rationals of
             DECLARED PRECISION and no exactness claim is made.

Original imports removed: ``numpy``, ``scipy.special``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path as _Path
from typing import Dict, List, Tuple

OUT_DIR = str(_Path(__file__).resolve().parent)
sys.path.insert(0, OUT_DIR)

from spike_40_exact_primitives import (  # noqa: E402
    ONE, ZERO, Q, Qalg,
    bessel_zero_table, bessel_zero_verification, clean_for_json, mag,
    provenance_records, qfrom_decimal, qsqrt, strict_kepler_test, write_ndjson,
)


# ===========================================================================
# piano — the ALGEBRAIC-IRRATIONAL leg
# ===========================================================================

def piano_partial_exact(n: int, b_stiff: Q) -> Tuple[Qalg, Q, dict]:
    """``f_n / f0 = n*sqrt(1 + B n^2)`` as an exact algebraic number.

    ``1 + B n^2`` is rational, call it ``r = p/q``. Then
    ``sqrt(r) = sqrt(p*q)/q``, so ``f_n/f0`` lies in ``Q(sqrt(p*q))`` — the
    quadratic field ``Q[x]/(x^2 - p*q)``. The element is built in ``Qalg``
    and its defining identity ``alpha^2 = p*q`` is CHECKED (element-to-element,
    per DEFECT-1: ``Qalg.__eq__`` will not coerce an ``int`` or a ``Q``).

    Returns ``(qalg_element, rational_lift, provenance)``. The rational lift
    is srmech's Class-N ``sqrt`` and is what the log-domain K-test consumes,
    because ``log`` has no ``Qalg`` surface (a further gap, noted below).
    """
    r = ONE + b_stiff * Q(n * n, 1)
    p, q = r.numerator, r.denominator
    m = (-(p * q), 0, 1)                        # x^2 - p*q
    alpha = Qalg.alpha(list(m))                 # alpha = sqrt(p*q)
    elem = alpha * Qalg.rational(Q(n, q), m)    # n*sqrt(p*q)/q = n*sqrt(r)
    identity_holds = (alpha * alpha) == Qalg.rational(Q(p * q, 1), m)
    lift = Q(n, 1) * qsqrt(r)
    return elem, lift, {
        "n": n,
        "radicand_1_plus_B_n2": f"{p}/{q}",
        "min_poly": f"x^2 - {p * q}",
        "field": f"Q(sqrt({p * q}))",
        "degree_over_Q": alpha.degree,
        "alpha_squared_identity_verified": bool(identity_holds),
        "is_rational": bool(_is_perfect_square(p * q)),
    }


def _is_perfect_square(k: int) -> bool:
    if k < 0:
        return False
    r = int(k ** 0.5)
    while r * r > k:
        r -= 1
    while (r + 1) * (r + 1) <= k:
        r += 1
    return r * r == k


def piano_freq_sequence(b_stiff: Q, n_partials: int = 16):
    """The 16 piano partials: exact Qalg elements + their Class-N rational lifts."""
    elems, lifts, prov = [], [], []
    for n in range(1, n_partials + 1):
        e, lift, p = piano_partial_exact(n, b_stiff)
        elems.append(e)
        lifts.append(lift)
        prov.append(p)
    return elems, lifts, prov


# ===========================================================================
# bell — the RATIONAL leg
# ===========================================================================

BELL_RATIOS_EXACT: List[Q] = [
    Q(1, 2), Q(1, 1), Q(6, 5), Q(3, 2), Q(2, 1),
    Q(3, 1), Q(4, 1), Q(27, 5), Q(6, 1),
]


def bell_freq_ratios() -> List[Q]:
    """Canonical bell modes (Fletcher & Rossing 1998 Sec 21.3), exact rationals."""
    return list(BELL_RATIOS_EXACT)


# ===========================================================================
# drum — the GAP-2 leg
# ===========================================================================

def drum_freq_ratios(n_max_modes: int = 20):
    """Sorted Bessel-zero ratios to the lowest mode. Returns ``(ratios, verification)``."""
    zeros = bessel_zero_table(6, 5)
    freqs = sorted(zeros.values(), key=lambda q: q.as_float())
    if len(freqs) > n_max_modes:
        freqs = freqs[:n_max_modes]
    return [f / freqs[0] for f in freqs], bessel_zero_verification(zeros)


# ===========================================================================
# the frequency-axis K-test
# ===========================================================================

def test_freq_sequence_for_K(freq_sequence: List[Q], name: str,
                             extra: dict | None = None) -> dict:
    """Deviation-from-perfect-harmonicity K-test, exact through to readout.

    ``s[k] = f_k/f_1 - k``; the Class-K magnitudes of those deviations are
    padded with a leading zero and fed to the strict K-test — identical
    decision procedure to the 2026-05-17 original.
    """
    f0 = freq_sequence[0]
    deviations = [f / f0 - Q(i + 1, 1) for i, f in enumerate(freq_sequence)]
    coeffs = [ZERO] + [mag(d) for d in deviations]
    K = strict_kepler_test(coeffs, k_max=6)
    rec = {
        "kind": "freq_inharmonicity_K_test",
        "substrate": name,
        "n_partials": len(freq_sequence),
        "freq_ratios_first_5": [(f / f0).as_float() for f in freq_sequence[:5]],
        "deviations_first_5": [d.as_float() for d in deviations[:5]],
        "k_test_on_deviations": K,
    }
    if extra:
        rec.update(extra)
    return rec


def main() -> None:
    print("=" * 78)
    print("Spike #40 EXACT PORT - frequency-axis inharmonicity K-test")
    print("=" * 78)
    records: List[dict] = provenance_records(
        "spike_40_freq_inharmonicity_analysis_exact.py")

    records.append({
        "kind": "carrier_note",
        "note": (
            "GAP-8 (Class N): srmech's exact log/exp/sqrt cascade accepts float "
            "and Q but has NO Qalg surface. So an algebraic-irrational partial "
            "must be lifted from Qalg to a Class-N rational sqrt before the "
            "log-domain K-test can touch it. The Qalg element is still built and "
            "its defining identity verified, so the ALGEBRAIC FACT is shipped "
            "even though the numeric path goes through Q. A Qalg-native log would "
            "close this."
        ),
    })

    for b_text in ["1e-05", "0.0001", "0.0005", "0.001", "0.005"]:
        b = qfrom_decimal(b_text)
        _elems, lifts, prov = piano_freq_sequence(b)
        rec = test_freq_sequence_for_K(
            lifts, f"piano_freq_axis_B_{float(b_text)}",
            extra={
                "B_stiff_exact": f"{b.numerator}/{b.denominator}",
                "generating_form": "f_n = n*f0*sqrt(1 + B*n^2)",
                "exactness": "ALGEBRAIC IRRATIONAL (quadratic); per-partial field "
                             "membership proved in qalg_fields",
                "qalg_fields": prov,
                "all_qalg_identities_verified": all(
                    p["alpha_squared_identity_verified"] for p in prov),
                "n_partials_that_are_actually_rational": sum(
                    1 for p in prov if p["is_rational"]),
            })
        records.append(rec)
        K = rec["k_test_on_deviations"]
        print(f"  piano (B={b_text:8s}) freq_axis K: eps_fit={K['eps_fit']:.4f} "
              f"r2={K['r2']:.4f} mono={K['monotonic_decreasing']} "
              f"K_present={K['kepler_signature_present']}")

    drum_ratios, drum_verif = drum_freq_ratios()
    rec = test_freq_sequence_for_K(drum_ratios, "drum_freq_axis", extra={
        "generating_form": "f_n = j_{n,m}, the positive zeros of J_n (Rayleigh 1894 §200)",
        "exactness": "UNRESOLVED KIND. GAP-2: no srmech Bessel-zero op. These are "
                     "rationals of declared 2**-256 precision. Whether the true "
                     "zeros are transcendental or algebraic-irrational is an OPEN "
                     "Tier-3 question in this project (DLMF 10.21 makes no "
                     "transcendence statement) and NOTHING here asserts either.",
        "bessel_zero_verification": drum_verif,
    })
    records.append(rec)
    K = rec["k_test_on_deviations"]
    print(f"  drum 2D                  freq_axis K: eps_fit={K['eps_fit']:.4f} "
          f"r2={K['r2']:.4f} mono={K['monotonic_decreasing']} "
          f"K_present={K['kepler_signature_present']}")

    rec = test_freq_sequence_for_K(bell_freq_ratios(), "bell_freq_axis", extra={
        "generating_form": "canonical bell tuning (Fletcher & Rossing 1998 §21.3)",
        "exactness": "EXACT RATIONAL",
        "ratios_exact": [f"{r.numerator}/{r.denominator}" for r in BELL_RATIOS_EXACT],
        "note": "1.2 = 6/5 and 5.4 = 27/5 — read as the decimals they denote, "
                "not as the nearest doubles.",
    })
    records.append(rec)
    K = rec["k_test_on_deviations"]
    print(f"  bell 9-mode              freq_axis K: eps_fit={K['eps_fit']:.4f} "
          f"r2={K['r2']:.4f} mono={K['monotonic_decreasing']} "
          f"K_present={K['kepler_signature_present']}")

    harmonic = [Q(n, 1) for n in range(1, 17)]
    rec = test_freq_sequence_for_K(harmonic, "REF_pure_harmonic_freq_axis", extra={
        "generating_form": "f_n = n (perfectly harmonic)",
        "exactness": "EXACT INTEGER — every deviation is identically 0, so the "
                     "K-test correctly refuses (n_harmonics_used = 0).",
    })
    records.append(rec)
    K = rec["k_test_on_deviations"]
    print(f"  pure harmonic            freq_axis K: eps_fit={K['eps_fit']} "
          f"r2={K['r2']:.4f} K_present={K['kepler_signature_present']}")

    out = os.path.join(OUT_DIR, "spike_40_freq_inharmonicity_records_exact.ndjson")
    write_ndjson(out, records)
    print(f"\nWrote {len(records)} records to {out}")


if __name__ == "__main__":
    main()
