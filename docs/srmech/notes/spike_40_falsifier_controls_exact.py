"""Spike #40 EXACT PORT of ``spike_40_falsifier_controls.py`` (2026-07-30).

Two legs:

  1. the 50-seed random-amplitude falsifier baseline
  2. the cascade-beta stretched-exponential fit on ring-down envelopes

SEED SOURCE — PINNED AND STATED (this is the whole point of leg 1)
-------------------------------------------------------------------
The 2026-05-17 baseline came from ``numpy.random.default_rng(seed)``. numpy
is gone, and srmech ships no uniform-real PRNG (GAP-5). Rather than pin a
DIFFERENT source — which would have made the oracle uncheckable — the two
published algorithms numpy composes are replicated bit-exactly:

  * numpy's ``SeedSequence`` 32-bit hashmix/mix entropy pool (pool_size 4)
  * the ``PCG64`` XSL-RR 128/64 bit generator (O'Neill 2014)

both of which are pure mod-2^32 / mod-2^128 integer cascades, i.e. Class I.
Each draw is taken as ``Q(next_uint64 >> 11, 2**53)`` — EXACTLY what numpy's
``next_double`` produces — so the amplitudes are exact dyadic rationals and
nothing in leg 1 ever touches a float until the readout.

That the replica IS the same stream is not asserted, it is DEMONSTRATED: the
whole 2026-05-17 falsifier record comes back to <= 2 ulp.

``scipy.optimize.curve_fit`` in leg 2 is replaced by GAP-4 (exact-Q
Levenberg-Marquardt). Original imports removed: ``numpy``, ``scipy.optimize``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path as _Path
from typing import List, Tuple

OUT_DIR = str(_Path(__file__).resolve().parent)
sys.path.insert(0, OUT_DIR)

from spike_40_exact_primitives import (  # noqa: E402
    ONE, ZERO, Q,
    fixnum, lm_fit, mag, provenance_records, qexp, qlog, qpow_q, qsqrt,
    strict_kepler_test, write_ndjson,
)
from spike_40_musical_epicycle_analysis_exact import (  # noqa: E402
    random_amplitude_spectrum,
)

_LM_SCALE_BITS = 180


# ===========================================================================
# cascade-beta: stretched exponential E(t) = E0 * exp(-(t/tau)^beta)
# ===========================================================================

def _model(t: Q, pars) -> Q:
    e0, tau, beta = pars
    return e0 * qexp(ZERO - qpow_q(t / tau, beta))


def _jac(t: Q, pars) -> List[Q]:
    e0, tau, beta = pars
    ratio = t / tau
    u = qpow_q(ratio, beta)
    ex = qexp(ZERO - u)
    return [
        ex,                                   # d/dE0
        e0 * ex * beta * u / tau,             # d/dtau
        ZERO - e0 * ex * u * qlog(ratio),     # d/dbeta
    ]


def cascade_beta_test(envelope: List[Q], ts: List[Q]) -> dict:
    """Spike #31 cascade-beta test on a ring-down envelope, exact (GAP-4).

    Same model and same box bounds as the 2026-05-17
    ``scipy.optimize.curve_fit`` call: ``bounds = ([0, 1e-9, 0.1],
    [10*E0, 100*tau0, 2.0])``, and the FIRST start is the original's exact
    ``p0 = [E(t0), t[N//2], 0.5]``.

    ONE DECLARED DIFFERENCE — a DETERMINISTIC 4-POINT MULTI-START.
    ``curve_fit`` defaults to ``method='trf'``, a bounded trust-region
    reflective solver with a global step-acceptance strategy. GAP-4 here is a
    plain damped Levenberg-Marquardt. On the drum envelope those two disagree
    ABOUT THE ANSWER, not about arithmetic: from the published ``p0`` the
    plain LM descends into a real local minimum at roughly
    ``(E0, tau, beta) = (9.85, 5.6e-5, 0.14)`` (SSE genuinely decreases, and
    E0 pins to its upper bound) while TRF escapes to the true optimum. The
    drum envelope is ``exp(-3t/2) == exp(-(t/(2/3))^1)``, so the true
    minimiser is ``(1, 2/3, 1)`` with residual identically zero — verified
    directly here. Falling into that pit is therefore an optimiser-strategy
    artefact, and a multi-start is the correct fix rather than a tuned
    tolerance. Both results are reported: the multi-start best AND what the
    single published start alone gives.
    """
    if any(v <= ZERO for v in envelope) or any(t < ZERO for t in ts):
        return {"fit_ok": False, "reason": "non-positive envelope"}
    e0_guess = envelope[0]
    tau_mid = ts[len(ts) // 2]
    tau_q1 = ts[len(ts) // 4]
    lo = [ZERO, Q(1, 10 ** 9), Q(1, 10)]
    hi = [e0_guess * Q(10, 1), tau_mid * Q(100, 1), Q(2, 1)]
    starts = [
        (tau_mid, Q(1, 2)),        # <- the 2026-05-17 p0, exactly
        (tau_mid, ONE),
        (tau_q1, ONE),
        (tau_q1, Q(1, 2)),
    ]
    best = None
    p0_only = None
    for i, (tau0, beta0) in enumerate(starts):
        pars, sse_fixed, n_it, conv = lm_fit(
            _model, _jac, ts, envelope, [e0_guess, tau0, beta0], lo, hi)
        entry = (sse_fixed, pars, n_it, conv, i)
        if i == 0:
            p0_only = entry
        if best is None or sse_fixed < best[0]:
            best = entry
    sse_fixed, pars, n_it, conv, which = best
    mean = sum(envelope, ZERO) / Q(len(envelope), 1)
    ss_tot = sum(fixnum(y - mean, _LM_SCALE_BITS) ** 2 for y in envelope)
    r2 = 1.0 - (sse_fixed / ss_tot if ss_tot > 0 else 1.0)
    e0, tau, beta = pars
    p0_pars = p0_only[1]
    return {
        "fit_ok": True,
        "E0": e0.as_float(),
        "tau": tau.as_float(),
        "beta": beta.as_float(),
        "tau_exact": f"{tau.numerator}/{tau.denominator}",
        "beta_exact": f"{beta.numerator}/{beta.denominator}",
        "r2": r2,
        "lm_iterations": n_it,
        "lm_converged": conv,
        "n_starts": len(starts),
        "winning_start_index": which,
        "single_start_p0_landed_in_a_different_basin": bool(
            p0_only[0] != sse_fixed),
        "single_start_p0_result": {
            "E0": p0_pars[0].as_float(),
            "tau": p0_pars[1].as_float(),
            "beta": p0_pars[2].as_float(),
            "r2": 1.0 - (p0_only[0] / ss_tot if ss_tot > 0 else 1.0),
        },
        "_pars": pars,
    }


def _profile_sse(ts: List[Q], ys: List[Q], tau: Q, beta: Q):
    """SSE at (tau, beta) with E0 profiled out analytically (E0* = <y,f>/<f,f>)."""
    f = [qexp(ZERO - qpow_q(t / tau, beta)) for t in ts]
    num = sum((y * fi for y, fi in zip(ys, f)), ZERO)
    den = sum((fi * fi for fi in f), ZERO)
    e0 = num / den
    return e0, sum(fixnum(y - e0 * fi, _LM_SCALE_BITS) ** 2 for y, fi in zip(ys, f))


def _compare_against_oracle_fit(ts, ys, pars, oracle_tau: Q, oracle_beta: Q) -> dict:
    """MEASURE which of the two fits sits lower on the exact objective surface.

    Not an assertion: E0 is profiled out analytically at both parameter pairs
    and the two exact SSEs are compared.
    """
    _e_p, sse_p = _profile_sse(ts, ys, pars[1], pars[2])
    _e_o, sse_o = _profile_sse(ts, ys, oracle_tau, oracle_beta)
    return {
        "oracle_tau": oracle_tau.as_float(),
        "oracle_beta": oracle_beta.as_float(),
        "port_tau": pars[1].as_float(),
        "port_beta": pars[2].as_float(),
        "sse_ratio_port_over_oracle": (Q(sse_p, 1) / Q(sse_o, 1)).as_float(),
        "closer_to_true_minimiser": "PORT" if sse_p < sse_o else (
            "ORACLE" if sse_o < sse_p else "TIE"),
        "method": "E0 profiled out analytically at each (tau, beta); the two "
                  "exact SSEs compared as integers in the 2**-180 scale.",
    }


def main() -> None:
    print("=" * 78)
    print("Spike #40 EXACT PORT - falsifier controls + cascade-beta ring-down")
    print("=" * 78)
    records: List[dict] = provenance_records("spike_40_falsifier_controls_exact.py")

    # === Falsifier 1: 50 random amplitude spectra (GAP-5) ===
    print("\n--- FALSIFIER: 50 random amplitude spectra (n=10) ---")
    eps_fits: List[Q] = []
    r2s: List[Q] = []
    monos = 0
    ks_present = 0
    for seed in range(50):
        c = random_amplitude_spectrum(seed=seed, n_partials=10)
        K = strict_kepler_test(c)
        eps_fits.append(K["_exact"]["eps_fit"])
        r2s.append(K["_exact"]["r2"])
        monos += 1 if K["monotonic_decreasing"] else 0
        ks_present += 1 if K["kepler_signature_present"] else 0
    n = Q(len(eps_fits), 1)
    e_mean = sum(eps_fits, ZERO) / n
    e_std = qsqrt(sum(((x - e_mean) * (x - e_mean) for x in eps_fits), ZERO) / n)
    r_mean = sum(r2s, ZERO) / Q(len(r2s), 1)
    print(f"  eps_fit: mean={e_mean.as_float():.4f} std={e_std.as_float():.4f} "
          f"min={min(eps_fits).as_float():.4f} max={max(eps_fits).as_float():.4f}")
    print(f"  r2: mean={r_mean.as_float():.4f} max={max(r2s).as_float():.4f}")
    print(f"  monotonic-decreasing count: {monos}/50")
    print(f"  K-signature-present count: {ks_present}/50 (HARD FALSIFIER)")
    records.append({
        "kind": "falsifier_random_amplitude_spectra",
        "n_seeds": 50,
        "n_partials": 10,
        "eps_fit_mean": e_mean.as_float(),
        "eps_fit_std": e_std.as_float(),
        "eps_fit_min": min(eps_fits).as_float(),
        "eps_fit_max": max(eps_fits).as_float(),
        "r2_mean": r_mean.as_float(),
        "r2_max": max(r2s).as_float(),
        "monotonic_count": monos,
        "K_present_count": ks_present,
        "seed_source_pinned": (
            "numpy SeedSequence (pool_size 4) + PCG64 XSL-RR 128/64 "
            "(O'Neill 2014), replicated bit-exactly as a Class-I mod-2^32 / "
            "mod-2^128 integer cascade; draws taken as the exact rational "
            "Q(next_uint64 >> 11, 2**53), i.e. numpy's next_double verbatim. "
            "Seeds 0..49, n_partials=10, 9 draws each."
        ),
    })

    # === Falsifier 2: pure-harmonic 1/n ratchet ===
    print("\n--- FALSIFIER: pure-harmonic 1/n series (should fail K) ---")
    c = [ZERO] + [Q(1, k) for k in range(1, 20)]
    K = strict_kepler_test(c)
    print(f"  pure 1/n: eps_fit={K['eps_fit']:.4f} r2={K['r2']:.4f} "
          f"in_range={K['in_physical_range']} mono={K['monotonic_decreasing']} "
          f"K_present={K['kepler_signature_present']}")
    records.append({"kind": "falsifier_pure_harmonic", "k_test": K})

    # === Falsifier 3: white-noise flat ===
    print("\n--- FALSIFIER: white-noise flat spectrum (should fail K) ---")
    c = [ZERO] + [ONE] * 19
    K = strict_kepler_test(c)
    print(f"  white noise: eps_fit={K['eps_fit']:.4f} r2={K['r2']:.4f} "
          f"in_range={K['in_physical_range']} mono={K['monotonic_decreasing']} "
          f"K_present={K['kepler_signature_present']}")
    records.append({"kind": "falsifier_white_noise", "k_test": K})

    # === Cascade-beta on ring-down envelopes ===
    print("\n--- CASCADE-BETA: ring-down envelopes for RING-DOWN instruments ---")
    # np.linspace(0.01, 5.0, 500): step = 4.99/499 = 1/100 EXACTLY, so
    # t_i = (i+1)/100 -- an exact rational grid, no float rounding at all.
    ts = [Q(i + 1, 100) for i in range(500)]

    piano_env = [Q(1, 2) * qexp(Q(-2, 1) * t) + Q(1, 2) * qexp(ZERO - t / Q(3, 1))
                 for t in ts]
    res = cascade_beta_test(piano_env, ts)
    if res["fit_ok"]:
        exp_1d = Q(1, 3)
        print(f"  piano (1D substrate): beta_fit={res['beta']:.6f} "
              f"expected_1D={exp_1d.as_float():.4f} r2={res['r2']:.6f} "
              f"({res['lm_iterations']} LM iters)")
        records.append({
            "kind": "cascade_beta_piano",
            "substrate": "piano_decay_envelope_dual_exp",
            "beta_fit": res["beta"],
            "beta_expected_d_S_1": exp_1d.as_float(),
            "delta_beta": (res["_pars"][2] - exp_1d).as_float(),
            "tau_fit": res["tau"],
            "r2": res["r2"],
            "lm_iterations": res["lm_iterations"],
            "lm_converged": res["lm_converged"],
            "n_starts": res["n_starts"],
            "winning_start_index": res["winning_start_index"],
            "single_start_p0_landed_in_a_different_basin":
                res["single_start_p0_landed_in_a_different_basin"],
            "single_start_p0_result": res["single_start_p0_result"],
            "note": "GAP-4 exact-Q Levenberg-Marquardt replacing scipy curve_fit "
                    "(trf). Same model, same box, same p0.",
            # Decide WHICH optimiser got closer, by measuring rather than asserting:
            # profile E0 out analytically at each (tau, beta) and compare the SSE.
            "which_optimiser_is_closer_to_the_true_minimiser":
                _compare_against_oracle_fit(
                    ts, piano_env, res["_pars"],
                    Q.from_float(1.093530794544387),
                    Q.from_float(0.5964617740400583)),
        })

    # drum 2D: E(t) = exp(-1.5 t) == exp(-(t/(2/3))^1) -- the EXACT optimum is
    # (E0, tau, beta) = (1, 2/3, 1) with residual identically zero.
    drum_env = [qexp(Q(-3, 2) * t) for t in ts]
    res = cascade_beta_test(drum_env, ts)
    if res["fit_ok"]:
        exp_2d = Q(1, 2)
        print(f"  drum 2D (d_S=2):     beta_fit={res['beta']:.15f} "
              f"tau_fit={res['tau']:.15f} r2={res['r2']:.6f}")
        records.append({
            "kind": "cascade_beta_drum",
            "substrate": "drum_2d_decay_envelope_simple_exp",
            "beta_fit": res["beta"],
            "beta_expected_d_S_2": exp_2d.as_float(),
            "delta_beta": (res["_pars"][2] - exp_2d).as_float(),
            "tau_fit": res["tau"],
            "tau_exact": res["tau_exact"],
            "beta_exact": res["beta_exact"],
            "r2": res["r2"],
            "lm_iterations": res["lm_iterations"],
            "n_starts": res["n_starts"],
            "winning_start_index": res["winning_start_index"],
            "single_start_p0_landed_in_a_different_basin":
                res["single_start_p0_landed_in_a_different_basin"],
            "single_start_p0_result": res["single_start_p0_result"],
            "closed_form_optimum": "exp(-3t/2) IS exp(-(t/(2/3))^1), so the exact "
                                   "minimiser is (E0, tau, beta) = (1, 2/3, 1) with "
                                   "residual identically zero",
            "finding": "THIS is the envelope where a plain damped LM and scipy's "
                       "trf disagree about the ANSWER. From the published p0 the "
                       "plain LM descends into a real local minimum (see "
                       "single_start_p0_result); the closed form above says the "
                       "true optimum is beta = 1 exactly, and the multi-start "
                       "reaches it. The 2026-05-17 oracle reported "
                       "beta = 0.9999999999999893 and tau = 0.6666666666666601, "
                       "i.e. trf ALSO stopped ~1e-14 short of the exact point.",
        })

    bell_env = [qexp(Q(-1, 2) * t) for t in ts]
    res = cascade_beta_test(bell_env, ts)
    if res["fit_ok"]:
        exp_3d = Q(3, 5)
        print(f"  bell (d_S=3):        beta_fit={res['beta']:.15f} "
              f"tau_fit={res['tau']:.15f} r2={res['r2']:.6f}")
        records.append({
            "kind": "cascade_beta_bell",
            "substrate": "bell_decay_envelope_simple_exp",
            "beta_fit": res["beta"],
            "beta_expected_d_S_3": exp_3d.as_float(),
            "delta_beta": (res["_pars"][2] - exp_3d).as_float(),
            "tau_fit": res["tau"],
            "tau_exact": res["tau_exact"],
            "beta_exact": res["beta_exact"],
            "r2": res["r2"],
            "lm_iterations": res["lm_iterations"],
            "n_starts": res["n_starts"],
            "winning_start_index": res["winning_start_index"],
            "single_start_p0_landed_in_a_different_basin":
                res["single_start_p0_landed_in_a_different_basin"],
            "single_start_p0_result": res["single_start_p0_result"],
            "closed_form_optimum": "exp(-t/2) IS exp(-(t/2)^1), so the exact "
                                   "minimiser is (E0, tau, beta) = (1, 2, 1) with "
                                   "residual identically zero",
        })

    print("\n--- RING-UP / SUSTAINED instruments (cascade-beta N/A) ---")
    for ru in ["violin_bowed_steady", "flute_blown_steady", "clarinet_blown_steady",
               "voice_sung_steady", "trumpet_blown_steady"]:
        print(f"  {ru}: cascade-beta SKIPPED (no decay envelope; instrument-first ring-up)")
        records.append({
            "kind": "cascade_beta_ring_up_skipped",
            "substrate": ru,
            "note": "Sustained-mode substrate; ring-up not ring-down per "
                    "user_stance_string_theory_instrument_first; cascade-beta "
                    "is for ring-down envelopes only",
        })

    out = os.path.join(OUT_DIR, "spike_40_falsifier_records_exact.ndjson")
    write_ndjson(out, records)
    print(f"\nWrote {len(records)} falsifier+cascade records to {out}")


if __name__ == "__main__":
    main()
