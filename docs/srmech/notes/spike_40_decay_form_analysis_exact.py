"""Spike #40 EXACT PORT of ``spike_40_decay_form_analysis.py`` (2026-07-30).

Four-model decay-form best fit per substrate:

  M1 power-law   a_n = A / n^p         (Fletcher / sawtooth family)
  M2 geometric   a_n = A * eps^n       (Kepler / FM-small-beta family)
  M3 Bessel      a_n = |J_n(beta)|     (FM-canonical, NOT Kepler)
  M4 Kepler      a_n = A * eps^n / n   (Kepler-canonical EOC)

All four fits run in exact ``Q``: the log-domain design solves through
GAP-3 (exact-rational degree-1 least squares) and the M3 grid evaluates
GAP-1 (the exact Bessel series) at the 100 exact grid rationals
``beta_i = (99 + 49 i) / 990`` — which is what ``linspace(0.1, 5.0, 100)``
denotes. Floats appear only at the record readout.

Original imports removed: ``numpy``, ``scipy.linalg``, ``scipy.special``.

ONE DELIBERATE STRUCTURAL SIMPLIFICATION
----------------------------------------
The original computes ``A = math.exp(intercept)`` and then immediately
``np.log(A)`` again inside the prediction. That round trip is a pure
float-noise generator; the ports use the intercept directly, which is the
value the round trip is trying to recover. Difference is below 1e-16 and
is reported by the oracle harness like any other divergence.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path as _Path
from typing import Dict, List, Tuple

OUT_DIR = str(_Path(__file__).resolve().parent)
sys.path.insert(0, OUT_DIR)

from spike_40_exact_primitives import (  # noqa: E402
    ONE, ZERO, Q,
    bessel_j, lstsq_line, mag, provenance_records, qexp, qfrom_decimal, qlog,
    qsqrt, write_ndjson,
)
from spike_40_musical_epicycle_analysis_exact import (  # noqa: E402
    beat_pattern, bell_modes_3_mode, clarinet_open_closed, drum_membrane_2d,
    flute_open_open, piano_inharmonic_partials, pure_am_signal,
    pure_fm_signal, pure_harmonic_1over_n, pure_kepler_reference,
    trumpet_lip_buzz, violin_helmholtz, voice_glottal_source_filter,
    white_noise_flat_amplitude,
)

MODEL_NAMES = ["M1_power_law", "M2_geometric", "M3_bessel", "M4_kepler"]

# linspace(0.1, 5.0, 100) EXACTLY: 0.1 = 99/990 and the step 4.9/99 = 49/990,
# so beta_i = (99 + 49 i)/990 and beta_99 = 4950/990 = 5 exactly.
BETA_GRID: List[Q] = [Q(99 + 49 * i, 990) for i in range(100)]
FLOOR_1E15 = Q(1, 10 ** 15)


def _rms(values: List[Q]) -> Q:
    n = Q(len(values), 1)
    return qsqrt(sum((v * v for v in values), ZERO) / n)


# ===========================================================================
# EXACT DEGENERACY DETECTOR  (the finding this port exists to expose)
# ===========================================================================
#
# M1 (A/n^p) and M4 (A eps^n / n) are the SAME curve at p = 1, eps = 1.  On a
# 1/n spectrum BOTH fit with residual EXACTLY ZERO, so "which model is best"
# is decided by whatever ~1e-17 arithmetic noise the log cascade happens to
# leave behind — not by the data.  The 2026-05-17 records report
# best_model = M1_power_law with margin_log_rms = 0.0 on six substrates; that
# 0.0 margin IS the tell.  These predicates decide the same question in exact
# rational arithmetic instead, so the verdict never rides on a float round.

def _fits_power_law_exactly(cs: List[Q], ks: List[Q]) -> str | None:
    """Exact test: is ``c_n = A * n^-p`` for a rational ``p = s/t``?

    Bounded search over ``p in {0, 1/2, 1, 3/2, 2, 5/2, 3}`` — the range the
    substrate library actually spans (flat, 1/sqrt(n), 1/n, 1/n^2). The test
    is the exact integer identity ``c_n^t * n^s == c_1^t * k_1^s``.
    """
    for t in (1, 2):
        for s in range(0, 7):
            p_num, p_den = s, t
            ref = None
            ok = True
            for c, k in zip(cs, ks):
                lhs = (c ** t) * Q(k.numerator ** s, k.denominator ** s)
                if ref is None:
                    ref = lhs
                elif lhs != ref:
                    ok = False
                    break
            if ok and ref is not None:
                return f"{p_num}/{p_den}"
    return None


def _fits_geometric_exactly(vals: List[Q]) -> bool:
    """Exact test: is the sequence geometric? ``v_{i+1} * v_{i-1} == v_i^2``."""
    if len(vals) < 3:
        return False
    for i in range(1, len(vals) - 1):
        if vals[i + 1] * vals[i - 1] != vals[i] * vals[i]:
            return False
    return True


def exact_degeneracy(cs: List[Q], ks: List[Q], best_beta: Q) -> dict:
    """Which of the four models fit with residual EXACTLY zero, decided in Q."""
    m1_p = _fits_power_law_exactly(cs, ks)
    m2 = _fits_geometric_exactly(cs)
    m4 = _fits_geometric_exactly([c * k for c, k in zip(cs, ks)])
    m3 = all(mag(bessel_j(int(k.numerator), best_beta)) == c
             for c, k in zip(cs, ks))
    exact = []
    if m1_p is not None:
        exact.append("M1_power_law")
    if m2:
        exact.append("M2_geometric")
    if m3:
        exact.append("M3_bessel")
    if m4:
        exact.append("M4_kepler")
    return {
        "models_that_fit_EXACTLY": exact,
        "M1_exact_p": m1_p,
        "n_exact_fits": len(exact),
        "verdict_is_degenerate": len(exact) > 1,
        "caveat": (
            "The predicates test the CARRIED RATIONALS. A substrate whose true "
            "amplitudes are ALGEBRAIC IRRATIONAL (trumpet, a_n = n^-1/2, which is "
            "an exact power law with p = 1/2 over Q(sqrt(n))) reads as NUMERIC "
            "here, because what the cascade carries is the Class-N rational lift "
            "of that irrational, not the algebraic number itself. So 'NUMERIC' "
            "means 'not exact IN Q', not 'not exact'."
        ),
        "note": (
            "M1(p=1) and M4(eps=1) are the SAME curve A/n, so any exact-1/n "
            "spectrum makes the M1-vs-M4 comparison undecidable on the data. "
            "Where verdict_is_degenerate is true, the 2026-05-17 best_model is a "
            "coin flip on ~1e-17 arithmetic noise and carries no information."
            if len(exact) > 1 else
            "single exact fit (or none) — the best_model verdict is real."
        ),
    }


def fit_decay_models(coeffs: List[Q], n_max: int = 8) -> dict:
    abs_c = [mag(c) for c in coeffs]
    if len(abs_c) <= n_max:
        n_max = len(abs_c) - 1
    cs = abs_c[1:n_max + 1]
    cmax = max(abs_c) if abs_c else ZERO
    floor = max(FLOOR_1E15, cmax * Q(1, 10 ** 12))
    keep = [i for i, c in enumerate(cs) if c > floor]
    if len(keep) < 3:
        return {"best_model": "INSUFFICIENT", "n_used": len(keep)}
    ks = [Q(i + 1, 1) for i in keep]
    cs_used = [cs[i] for i in keep]
    log_c = [qlog(c) for c in cs_used]
    log_k = [qlog(k) for k in ks]

    results: Dict[str, dict] = {}

    # M1: log(a_n) = log(A) - p log(n)
    s1, i1 = lstsq_line(log_k, log_c)
    p_pow = ZERO - s1
    pred1 = [i1 - p_pow * lk for lk in log_k]
    res1 = _rms([a - b for a, b in zip(log_c, pred1)])
    results["M1_power_law"] = {"p": p_pow, "A": qexp(i1), "log_rms_residual": res1}

    # M2: log(a_n) = log(A) + n log(eps)
    s2, i2 = lstsq_line(ks, log_c)
    pred2 = [i2 + k * s2 for k in ks]
    res2 = _rms([a - b for a, b in zip(log_c, pred2)])
    results["M2_geometric"] = {"eps": qexp(s2), "A": qexp(i2), "log_rms_residual": res2}

    # M3: Bessel — grid search over the 100 exact linspace rationals (GAP-1)
    best_res3 = None
    best_beta = None
    best_a3 = None
    n_used_q = Q(len(ks), 1)
    for beta in BETA_GRID:
        jk = [mag(bessel_j(int(k.numerator), beta)) for k in ks]
        jk_safe = [v if v > FLOOR_1E15 else FLOOR_1E15 for v in jk]
        log_j = [qlog(v) for v in jk_safe]
        diff = [a - b for a, b in zip(log_c, log_j)]
        log_a = sum(diff, ZERO) / n_used_q
        res3 = _rms([d - log_a for d in diff])
        if best_res3 is None or res3 < best_res3:
            best_res3, best_beta, best_a3 = res3, beta, qexp(log_a)
    results["M3_bessel"] = {"beta": best_beta, "A": best_a3,
                            "log_rms_residual": best_res3}

    # M4: log(a_n) = log(A) + n log(eps) - log(n)
    y4 = [a + b for a, b in zip(log_c, log_k)]
    s4, i4 = lstsq_line(ks, y4)
    pred4 = [i4 + k * s4 - lk for k, lk in zip(ks, log_k)]
    res4 = _rms([a - b for a, b in zip(log_c, pred4)])
    results["M4_kepler"] = {"eps": qexp(s4), "A": qexp(i4), "log_rms_residual": res4}

    res_vals = [results[m]["log_rms_residual"] for m in MODEL_NAMES]
    order = sorted(range(4), key=lambda i: (res_vals[i].as_float(), i))
    best_idx, second_idx = order[0], order[1]
    degen = exact_degeneracy(cs_used, ks, best_beta)
    return {
        "best_model": MODEL_NAMES[best_idx],
        "second_model": MODEL_NAMES[second_idx],
        "margin_log_rms": res_vals[second_idx] - res_vals[best_idx],
        "models": results,
        "n_used": len(ks),
        "exact_degeneracy": degen,
        "verdict": (
            "DEGENERATE — " + " == ".join(degen["models_that_fit_EXACTLY"]) +
            " all fit with residual EXACTLY zero; the numeric best_model above is "
            "noise and MUST NOT be read as a substrate fingerprint"
            if degen["verdict_is_degenerate"] else
            ("EXACT — " + degen["models_that_fit_EXACTLY"][0] +
             " fits with residual exactly zero"
             if degen["n_exact_fits"] == 1 else
             "NUMERIC — no model fits exactly; best_model is a genuine comparison")
        ),
    }


def build_substrates():
    subs = []
    for beta_s in ["0.5", "1.5", "3.0"]:
        c, _m = pure_fm_signal(qfrom_decimal(beta_s))
        subs.append((f"pure_fm_beta_{float(beta_s)}", c))
    c, _m = pure_am_signal(qfrom_decimal("0.5"))
    subs.append(("pure_am", c))
    c, _m = beat_pattern()
    subs.append(("beat_pattern", c))
    for b_s in ["1e-4", "5e-4", "1e-3"]:
        c, _m = piano_inharmonic_partials(qfrom_decimal(b_s))
        subs.append((f"piano_B_{float(b_s)}", c))
    c, _m = violin_helmholtz()
    subs.append(("violin_helmholtz", c))
    c, _m = clarinet_open_closed()
    subs.append(("clarinet_open_closed", c))
    c_d, _m_d, _ev = drum_membrane_2d()
    subs.append(("drum_membrane_2d_amp_baseline", c_d))
    c, _m = bell_modes_3_mode()
    subs.append(("bell_5mode", c))
    c, _m = voice_glottal_source_filter()
    subs.append(("voice_vowel_a", c))
    c, _m = flute_open_open()
    subs.append(("flute_open_open", c))
    c, _m = trumpet_lip_buzz()
    subs.append(("trumpet_lip_buzz", c))
    for e_s in ["0.01", "0.05", "0.1", "0.2", "0.4"]:
        c, _m = pure_kepler_reference(qfrom_decimal(e_s))
        subs.append((f"REF_pure_kepler_eps_{float(e_s)}", c))
    c, _m = pure_harmonic_1over_n()
    subs.append(("REF_pure_harmonic_1_over_n", c))
    c, _m = white_noise_flat_amplitude()
    subs.append(("REF_white_noise_flat", c))
    return subs


def main() -> None:
    print("=" * 78)
    print("Spike #40 EXACT PORT - decay-form-best-fit per substrate")
    print("=" * 78)
    records: List[dict] = provenance_records("spike_40_decay_form_analysis_exact.py")

    print(f"\n  {'INSTRUMENT':32s} {'best':>18s} {'second':>18s} {'margin':>8s} "
          f"{'M1.p':>7s} {'M2.eps':>7s} {'M3.beta':>8s} {'M4.eps':>7s}")
    print("  " + "-" * 110)

    for name, coeffs in build_substrates():
        f = fit_decay_models(coeffs)
        if f["best_model"] == "INSUFFICIENT":
            print(f"  {name:32s} INSUFFICIENT (sparse spectrum)")
            records.append({"kind": "decay_form_fit", "substrate": name,
                            "best_model": "INSUFFICIENT", "n_used": f["n_used"]})
            continue
        mods = f["models"]
        m1p = mods["M1_power_law"]["p"].as_float()
        m2e = mods["M2_geometric"]["eps"].as_float()
        m3b = mods["M3_bessel"]["beta"].as_float()
        m4e = mods["M4_kepler"]["eps"].as_float()
        print(f"  {name:32s} {f['best_model']:>18s} {f['second_model']:>18s} "
              f"{f['margin_log_rms'].as_float():8.3f} {m1p:7.3f} {m2e:7.3f} "
              f"{m3b:8.3f} {m4e:7.3f}")
        records.append({
            "kind": "decay_form_fit",
            "substrate": name,
            "best_model": f["best_model"],
            "second_model": f["second_model"],
            "margin_log_rms": f["margin_log_rms"].as_float(),
            "M1_power_law_p": m1p,
            "M1_log_rms_resid": mods["M1_power_law"]["log_rms_residual"].as_float(),
            "M2_geometric_eps": m2e,
            "M2_log_rms_resid": mods["M2_geometric"]["log_rms_residual"].as_float(),
            "M3_bessel_beta": m3b,
            "M3_bessel_beta_exact": (
                f"{mods['M3_bessel']['beta'].numerator}/"
                f"{mods['M3_bessel']['beta'].denominator}"),
            "M3_log_rms_resid": mods["M3_bessel"]["log_rms_residual"].as_float(),
            "M4_kepler_eps": m4e,
            "M4_log_rms_resid": mods["M4_kepler"]["log_rms_residual"].as_float(),
            "n_used": f["n_used"],
            "exact_degeneracy": f["exact_degeneracy"],
            "verdict": f["verdict"],
        })
        if f["exact_degeneracy"]["verdict_is_degenerate"]:
            print(f"  {'':32s} ^^ DEGENERATE: "
                  f"{f['exact_degeneracy']['models_that_fit_EXACTLY']} all EXACT")

    out = os.path.join(OUT_DIR, "spike_40_decay_form_records_exact.ndjson")
    write_ndjson(out, records)
    print(f"\nWrote {len(records)} decay-form records to {out}")


if __name__ == "__main__":
    main()
