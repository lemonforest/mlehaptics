"""Historical prime-spectrum cross-references (Track 5, H-H1 / H-H2).

The Antikythera mechanism's gear-tooth counts have a distinctive prime-
factor fingerprint: small primes {2, 3, 5, 7} dominate, with a sparse
tail of celestially-FORCED large primes (47, 53, 127, 223, 251).
This module asks whether the same fingerprint appears in two
neighbouring traditions:

    MUL.APIN          ~1000 BCE (predates the mechanism by ~800 yr)
    Almagest          ~150 CE   (postdates the mechanism by ~350 yr)

If MUL.APIN already shows the same fingerprint, the Antikythera
inherits a much older Babylonian factorisation tradition.  If Almagest
shows different primes, Ptolemy's later mathematical synthesis took a
divergent path.

Three comparison metrics are reported (all on the prime-frequency
histograms):

    top-k overlap    Jaccard index of top-K most-frequent primes.
                     Cheap, intuitive, good headline number.
    chi2             Pearson chi-square test of "are the spectra
                     drawn from the same distribution?"  Bins low-
                     expectation primes into a tail bin.  Reports
                     statistic, p-value, dof, Cramer's V effect size.
                     Lazy ``scipy.stats`` import.
    kl-divergence    D_KL(observed || reference) with Laplace
                     smoothing.  Asymmetric; report both directions.

H-H1: Antikythera prime spectrum and Almagest period spectrum are
      statistically indistinguishable (chi2 p > 0.05).  Expected
      PARTIAL or FAIL -- Almagest emphasises 7, 19 strongly via
      Mars 79/151 and Metonic 235/19, but Almagest lacks the
      mechanism-specific large primes (127, 251) that come from
      gear discretisation rather than period relations.

H-H2: MUL.APIN top-3 primes overlap with the Antikythera by >= 2.
      Expected PASS -- 2, 3, 5, 7 dominate calendrical numerology
      across both eras.

References
----------
Hunger, H. & Pingree, D. (1989).  MUL.APIN: An Astronomical
    Compendium in Cuneiform.  Archiv fuer Orientforschung Beiheft 24.
Toomer, G. J. (1984).  Ptolemy's Almagest.  Princeton.
Britton, J. P. (2010).  Studies in Babylonian lunar theory III.
    Arch. Hist. Exact Sci. 64:617-663.
Cramer, H. (1946).  Mathematical Methods of Statistics.  Princeton.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


VALID_SOURCES: Tuple[str, ...] = ("antikythera", "mulapin", "almagest", "all")
VALID_METRICS: Tuple[str, ...] = ("top-k-overlap", "chi2", "kl-divergence", "all")


# ---------------------------------------------------------------------------
# Spectrum producers
# ---------------------------------------------------------------------------

def antikythera_spectrum(
    reconstruction: str = "Freeth2021",
    include_planetary: bool = True,
) -> Dict[int, int]:
    """Antikythera prime-factor spectrum from gear teeth."""
    from .packing_analysis import prime_spectrum
    return prime_spectrum(reconstruction, include_planetary=include_planetary)


def historical_spectrum(source: str,
                        include_disputed: bool = False) -> Dict[int, int]:
    """Prime spectrum from a historical period-relation corpus."""
    from .historical_periods import (
        periods_by_source, prime_spectrum_of_periods, filter_by_confidence,
    )
    periods = periods_by_source(source)
    if not include_disputed:
        periods = filter_by_confidence(periods, include_disputed=False)
    return prime_spectrum_of_periods(periods)


def get_spectrum(source: str, **kwargs) -> Dict[int, int]:
    """Dispatch by source name."""
    s = source.lower()
    if s == "antikythera":
        return antikythera_spectrum(
            reconstruction=kwargs.get("reconstruction", "Freeth2021"),
            include_planetary=kwargs.get("include_planetary", True),
        )
    if s in ("mulapin", "almagest", "all"):
        return historical_spectrum(
            s, include_disputed=kwargs.get("include_disputed", False),
        )
    raise ValueError(f"source must be one of {VALID_SOURCES}, got {source!r}")


# ---------------------------------------------------------------------------
# Comparison metrics
# ---------------------------------------------------------------------------

def top_k_primes(spec: Dict[int, int], k: int = 5) -> List[int]:
    """The k most-frequent primes in the spectrum.  Ties broken by prime
    value (smaller first)."""
    items = sorted(spec.items(), key=lambda kv: (-kv[1], kv[0]))
    return [p for p, _ in items[:k]]


def top_k_prime_overlap(
    spec_a: Dict[int, int],
    spec_b: Dict[int, int],
    k: int = 5,
) -> Tuple[Set[int], float]:
    """Return (overlap_set, jaccard_index) of top-k primes in each spectrum."""
    top_a = set(top_k_primes(spec_a, k))
    top_b = set(top_k_primes(spec_b, k))
    overlap = top_a & top_b
    union = top_a | top_b
    jaccard = (len(overlap) / len(union)) if union else 0.0
    return overlap, jaccard


def _bin_low_expectation(
    obs_a: Dict[int, int],
    obs_b: Dict[int, int],
    min_expected: float = 5.0,
) -> Tuple[List[float], List[float]]:
    """Bin primes whose expected count under either distribution is
    below ``min_expected`` into a single tail bin so chi-square's
    expected-cell minimum is satisfied.

    Returns (counts_a_binned, counts_b_binned) parallel lists.
    """
    sum_a = float(sum(obs_a.values())) or 1.0
    sum_b = float(sum(obs_b.values())) or 1.0
    primes = sorted(set(obs_a.keys()) | set(obs_b.keys()))
    high_a, high_b = [], []
    tail_a, tail_b = 0.0, 0.0
    for p in primes:
        a = obs_a.get(p, 0)
        b = obs_b.get(p, 0)
        # Joint table expected: row marginal * col marginal / total.  We
        # use a simpler heuristic: keep prime if both counts >= 1 AND
        # the joint sum >= min_expected.
        joint = a + b
        if joint >= min_expected:
            high_a.append(float(a))
            high_b.append(float(b))
        else:
            tail_a += float(a)
            tail_b += float(b)
    if tail_a + tail_b >= 1.0:
        high_a.append(tail_a)
        high_b.append(tail_b)
    return high_a, high_b


def chi2_test(
    spec_a: Dict[int, int],
    spec_b: Dict[int, int],
    min_expected: float = 5.0,
) -> Dict[str, float]:
    """Pearson chi-square of "spec_a and spec_b are drawn from the same
    distribution".  Returns dict with chi2, p_value, dof, cramers_v, n.

    Lazy ``scipy.stats`` import.  If scipy is unavailable, returns
    ``{"available": False, ...}``.
    """
    try:
        from scipy.stats import chi2_contingency  # type: ignore
    except ImportError:
        return {"available": False}

    a, b = _bin_low_expectation(spec_a, spec_b, min_expected=min_expected)
    if len(a) < 2 or sum(a) == 0 or sum(b) == 0:
        return {
            "available": True,
            "chi2": float("nan"),
            "p_value": float("nan"),
            "dof": 0,
            "cramers_v": float("nan"),
            "n_bins": len(a),
            "note": "insufficient data after binning",
        }

    table = [a, b]
    chi2, p, dof, expected = chi2_contingency(table, correction=True)
    n = sum(a) + sum(b)
    # Cramer's V for 2 x k table:  V = sqrt(chi2 / (n * (k-1)))
    k = max(2, len(a))
    cramers_v = float((chi2 / (n * (k - 1))) ** 0.5) if n > 0 else float("nan")
    return {
        "available": True,
        "chi2": float(chi2),
        "p_value": float(p),
        "dof": int(dof),
        "cramers_v": cramers_v,
        "n_bins": len(a),
        "n": float(n),
    }


def kl_divergence(
    spec_a: Dict[int, int],
    spec_b: Dict[int, int],
    smoothing: float = 0.5,
) -> Dict[str, float]:
    """Symmetric K-L pair: D(A||B) and D(B||A) with Laplace smoothing.

    smoothing: alpha added to every prime in the support union, so
    nothing has zero probability.  Default 0.5 (Krichevsky-Trofimov).
    """
    import math
    primes = sorted(set(spec_a.keys()) | set(spec_b.keys()))
    n = len(primes)
    if n == 0:
        return {"d_ab": float("nan"), "d_ba": float("nan"), "n_primes": 0}

    sum_a = float(sum(spec_a.values())) + smoothing * n
    sum_b = float(sum(spec_b.values())) + smoothing * n

    d_ab = 0.0
    d_ba = 0.0
    for p in primes:
        pa = (spec_a.get(p, 0) + smoothing) / sum_a
        pb = (spec_b.get(p, 0) + smoothing) / sum_b
        d_ab += pa * math.log(pa / pb)
        d_ba += pb * math.log(pb / pa)
    return {
        "d_ab": float(d_ab),
        "d_ba": float(d_ba),
        "n_primes": n,
        "smoothing": smoothing,
    }


# ---------------------------------------------------------------------------
# Hypothesis evaluators
# ---------------------------------------------------------------------------

def evaluate_H_H1(
    p_threshold: float = 0.05,
) -> Tuple[str, str, str, Dict[str, object]]:
    """H-H1: Antikythera vs Almagest spectra are statistically indistinguishable."""
    spec_ant = antikythera_spectrum()
    spec_alm = historical_spectrum("almagest")
    chi2 = chi2_test(spec_ant, spec_alm)
    if not chi2.get("available", False):
        return ("UNDETERMINED",
                "scipy unavailable",
                "scipy.stats not installed; chi-square test cannot run.",
                {"chi2_available": False})
    p = chi2["p_value"]
    if p > p_threshold:
        status = "PASS"
    elif p > p_threshold / 5.0:
        status = "PARTIAL"
    else:
        status = "FAIL"
    overlap, jaccard = top_k_prime_overlap(spec_ant, spec_alm, k=5)
    notes = (
        f"chi2 = {chi2['chi2']:.3f}, p = {chi2['p_value']:.4f}, "
        f"dof = {chi2['dof']}, Cramer V = {chi2['cramers_v']:.3f}.  "
        f"Top-5 prime overlap: {sorted(overlap)} "
        f"(Jaccard = {jaccard:.2f}).  "
        f"Threshold p > {p_threshold} for PASS."
    )
    computed = (
        f"chi2 p = {chi2['p_value']:.4f}; "
        f"top-5 Jaccard = {jaccard:.2f}"
    )
    detail = {
        "antikythera_top5": top_k_primes(spec_ant, 5),
        "almagest_top5": top_k_primes(spec_alm, 5),
        "top5_overlap": sorted(overlap),
        "top5_jaccard": jaccard,
        "chi2": chi2,
        "kl": kl_divergence(spec_ant, spec_alm),
    }
    return status, computed, notes, detail


def evaluate_H_H2(
    top_n: int = 3,
    min_overlap: int = 2,
) -> Tuple[str, str, str, Dict[str, object]]:
    """H-H2: MUL.APIN top-3 primes overlap with Antikythera by >= 2."""
    spec_ant = antikythera_spectrum()
    spec_mul = historical_spectrum("mulapin")
    top_a = set(top_k_primes(spec_ant, top_n))
    top_m = set(top_k_primes(spec_mul, top_n))
    overlap = top_a & top_m
    n_overlap = len(overlap)
    if n_overlap >= min_overlap:
        status = "PASS"
    elif n_overlap >= 1:
        status = "PARTIAL"
    else:
        status = "FAIL"
    jaccard = (n_overlap / len(top_a | top_m)) if (top_a | top_m) else 0.0
    notes = (
        f"Antikythera top-{top_n} = {sorted(top_a)}; "
        f"MUL.APIN top-{top_n} = {sorted(top_m)}; "
        f"overlap = {sorted(overlap)} ({n_overlap} primes, "
        f"Jaccard = {jaccard:.2f}).  Threshold: >= {min_overlap}."
    )
    computed = (
        f"top-{top_n} overlap = {n_overlap} primes "
        f"(Jaccard {jaccard:.2f})"
    )
    detail = {
        "antikythera_top_n": sorted(top_a),
        "mulapin_top_n": sorted(top_m),
        "overlap": sorted(overlap),
        "jaccard": jaccard,
        "n_overlap": n_overlap,
        "top_n": top_n,
        "min_overlap_threshold": min_overlap,
        "kl": kl_divergence(spec_ant, spec_mul),
    }
    return status, computed, notes, detail


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Antikythera vs Almagest, top-5 primes:
  python -m research.historical_cross_reference --source almagest \\
        --metric top-k-overlap

  # Full comparison (all three metrics, all sources):
  python -m research.historical_cross_reference --source all --metric all

  # Chi-square test only (needs scipy):
  python -m research.historical_cross_reference --source mulapin \\
        --metric chi2

  # Run the H-H1 / H-H2 evaluators:
  python -m research.historical_cross_reference --evaluate

Notes
-----
- chi-square requires scipy; degrades to UNDETERMINED if absent.
- Sample sizes are small (~20 historical entries); report Cramer's V
  alongside p-values.
- MUL.APIN entries are scholarly interpretations of cuneiform; see
  ``research/historical_periods.py`` for per-entry confidence flags.

Citations
---------
Hunger & Pingree (1989) MUL.APIN.  Toomer (1984) Almagest.
Britton (2010) AHES 64:617.  Cramer (1946) Math. Methods of Statistics.
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m research.historical_cross_reference",
        description=(
            "Cross-reference the Antikythera prime spectrum against "
            "Babylonian (MUL.APIN) and Greek (Almagest) period relations."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source", choices=VALID_SOURCES, default="all",
        help="Comparison source(s) (default: all).",
    )
    parser.add_argument(
        "--metric", choices=VALID_METRICS, default="all",
        help="Comparison metric (default: all).",
    )
    parser.add_argument(
        "--top-k", type=int, default=5,
        help="Top-K primes to compare (default: 5).",
    )
    parser.add_argument(
        "--smoothing", type=float, default=0.5,
        help="Laplace smoothing alpha for KL (default: 0.5).",
    )
    parser.add_argument(
        "--include-disputed", action="store_true",
        help="Include DISPUTED period relations.",
    )
    parser.add_argument(
        "--include-planetary", action="store_true", default=True,
        help="Include planetary gears in Antikythera spectrum (default: yes).",
    )
    parser.add_argument(
        "--reconstruction", default="Freeth2021",
        help="Antikythera reconstruction for the spectrum (default: Freeth2021).",
    )
    parser.add_argument(
        "--evaluate", action="store_true",
        help="Run H-H1 / H-H2 evaluators and print PASS/FAIL.",
    )
    parser.add_argument(
        "--csv-out", default=None,
        help="Write summary CSV to this path.",
    )
    return parser


def _print_overlap(name_a: str, spec_a: Dict[int, int],
                   name_b: str, spec_b: Dict[int, int],
                   k: int) -> None:
    overlap, jaccard = top_k_prime_overlap(spec_a, spec_b, k=k)
    top_a = top_k_primes(spec_a, k)
    top_b = top_k_primes(spec_b, k)
    print(f"  {name_a:<14} top-{k}: {top_a}")
    print(f"  {name_b:<14} top-{k}: {top_b}")
    print(f"  overlap = {sorted(overlap)} ({len(overlap)} primes; "
          f"Jaccard = {jaccard:.3f})")


def _print_chi2(spec_a: Dict[int, int],
                spec_b: Dict[int, int]) -> None:
    res = chi2_test(spec_a, spec_b)
    if not res.get("available"):
        print("  chi2: scipy unavailable")
        return
    print(f"  chi2 = {res['chi2']:.3f}  p = {res['p_value']:.4f}  "
          f"dof = {res['dof']}  Cramer V = {res['cramers_v']:.3f}  "
          f"n_bins = {res['n_bins']}")


def _print_kl(spec_a: Dict[int, int],
              spec_b: Dict[int, int],
              alpha: float = 0.5) -> None:
    res = kl_divergence(spec_a, spec_b, smoothing=alpha)
    print(f"  D_KL(A||B) = {res['d_ab']:.4f}  "
          f"D_KL(B||A) = {res['d_ba']:.4f}  "
          f"(alpha = {alpha}, n_primes = {res['n_primes']})")


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)

    if args.evaluate:
        print("--- H-H1: Antikythera vs Almagest ---")
        status, computed, notes, _ = evaluate_H_H1()
        print(f"  status: {status}")
        print(f"  computed: {computed}")
        print(f"  notes: {notes}")
        print()
        print("--- H-H2: Antikythera vs MUL.APIN ---")
        status, computed, notes, _ = evaluate_H_H2()
        print(f"  status: {status}")
        print(f"  computed: {computed}")
        print(f"  notes: {notes}")
        return 0

    spec_ant = antikythera_spectrum(
        reconstruction=args.reconstruction,
        include_planetary=args.include_planetary,
    )
    sources = (("mulapin", "almagest") if args.source == "all"
               else (args.source,))
    print(f"Antikythera spectrum: {len(spec_ant)} primes; "
          f"top-{args.top_k} = {top_k_primes(spec_ant, args.top_k)}")
    print()
    for src in sources:
        if src == "antikythera":
            continue
        spec_b = historical_spectrum(src, include_disputed=args.include_disputed)
        print(f"=== Antikythera vs {src.upper()} ===")
        if args.metric in ("top-k-overlap", "all"):
            _print_overlap("Antikythera", spec_ant, src, spec_b, args.top_k)
        if args.metric in ("chi2", "all"):
            _print_chi2(spec_ant, spec_b)
        if args.metric in ("kl-divergence", "all"):
            _print_kl(spec_ant, spec_b, args.smoothing)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
