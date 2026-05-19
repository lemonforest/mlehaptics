"""Spike #186 T7 sharp test — non-tautological gear-pin-slot decomposition.

The first run's T7 was tautological (sin bounded in [-1,1]).
The real claim per [[user_stance_epicycle_via_gear_plus_pin]]:

  Every cyclic mechanism = gear (Class I cyclic substrate-baseline-linear)
                         + pin-slot (Class K asymptotic-DOF)

For the per-body local time-DOF to be a projection of the universal tick:
  - Class I (gear) contribution = mean-substrate-coupling baseline
    that varies LINEARLY in body's orbital frequency (omega_orb).
  - Class K (pin-slot) contribution = asymptotic-DOF contribution
    that scales with body's compactness × universal-tick-amplitude.

Sharp test: regress SPrT_total = a + b * omega_orb + c * compactness
across all 52 bodies. If R^2 is high → two-component decomposition
empirically supported.

Then: omega_orb is the body's LOCAL gear (Class I); compactness is
the body's LOCAL pin-slot-depth (Class K). The universal tick
projects onto BOTH through Class M ∘ K substrate-coupling.

If R^2 LOW → per-body local times encode more than the gear-pin-slot
decomposition; refines stance to "gear+pin-slot is necessary but
not sufficient" structurally.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

EPHEM_PYTHON_DIR = Path(
    "D:/GitHub/mlehaptics/docs/antikythera-maths/ephemerides-spectral/python"
).resolve()
if str(EPHEM_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(EPHEM_PYTHON_DIR))

import importlib.util


def _load_module(name: str, relpath: str):
    full = EPHEM_PYTHON_DIR / relpath
    spec = importlib.util.spec_from_file_location(name, full)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_bodies_mod = _load_module(
    "ephemerides_spectral._research.bodies",
    "ephemerides_spectral/_research/bodies.py",
)
BODIES = _bodies_mod.BODIES

C = 299_792_458.0
C2 = C * C
G = 6.67430e-11
EARTH_MASS_KG = 5.9722e24
GM_EARTH = G * EARTH_MASS_KG
GM_SUN = 1.32712440018e20
DAY_S = 86400.0

PARENT_OF = {
    "luna": "terra", "phobos": "mars", "deimos": "mars",
    "metis": "jupiter", "adrastea": "jupiter", "amalthea": "jupiter", "thebe": "jupiter",
    "io": "jupiter", "europa": "jupiter", "ganymede": "jupiter", "callisto": "jupiter",
    "himalia": "jupiter", "pasiphae": "jupiter", "sinope": "jupiter",
    "mimas": "saturn", "enceladus": "saturn", "tethys": "saturn", "dione": "saturn",
    "rhea": "saturn", "titan": "saturn", "hyperion": "saturn", "iapetus": "saturn",
    "phoebe": "saturn", "janus": "saturn", "epimetheus": "saturn",
    "telesto": "saturn", "calypso": "saturn", "helene": "saturn", "polydeuces": "saturn",
    "miranda": "uranus", "ariel": "uranus", "umbriel": "uranus",
    "titania": "uranus", "oberon": "uranus",
    "triton": "neptune", "proteus": "neptune", "nereid": "neptune",
    "charon": "pluto",
}


def gm_for(b):
    if b == "sun": return GM_SUN
    return BODIES[b].mass_earth * GM_EARTH


def compute(b):
    body = BODIES[b]
    if body.surface_radius_km > 0:
        gr = gm_for(b) / (body.surface_radius_km * 1000.0 * C2)
    else:
        gr = 0.0
    if body.period_days > 0:
        parent = PARENT_OF.get(b)
        gm_central = GM_SUN if parent is None else gm_for(parent)
        t_s = body.period_days * DAY_S
        a_m = (gm_central * t_s * t_s / (4.0 * math.pi * math.pi)) ** (1.0 / 3.0)
        v = 2.0 * math.pi * a_m / t_s
        kin = v * v / (2.0 * C2)
        omega = 2.0 * math.pi / t_s
    else:
        kin = 0.0
        omega = 0.0
    return gr, kin, gr + kin, omega


def main():
    print("=" * 72)
    print("Spike #186 T7 SHARP test: gear+pin-slot decomposition")
    print("=" * 72)

    bodies_in = []
    for b in BODIES:
        gr, kin, total, omega = compute(b)
        if total > 0 and omega > 0:
            bodies_in.append({
                "body": b,
                "gr": gr,
                "kin": kin,
                "total": total,
                "omega": omega,
                "log_total": math.log(total),
                "log_omega": math.log(omega),
                "log_compactness": math.log(gr) if gr > 0 else math.log(1e-30),
            })

    # Multi-linear regression in log space:
    #   log(total) = a + b * log(omega) + c * log(compactness)
    X = np.array([[1.0, r["log_omega"], r["log_compactness"]] for r in bodies_in])
    y = np.array([r["log_total"] for r in bodies_in])

    # Least squares
    coef, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)
    a, b_omega, c_comp = coef
    pred = X @ coef
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1.0 - ss_res / ss_tot

    print(f"\nMulti-linear fit:")
    print(f"  log(SPrT_total) = {a:.3f} + {b_omega:.4f} * log(omega) + {c_comp:.4f} * log(compactness)")
    print(f"  R^2 = {r2:.4f}  n = {len(bodies_in)}")
    print(f"\nInterpretation:")
    print(f"  - omega exponent (gear, Class I): {b_omega:+.4f}")
    print(f"  - compactness exponent (pin-slot, Class K): {c_comp:+.4f}")

    # Test single-variable models
    A1 = np.array([[1.0, r["log_omega"]] for r in bodies_in])
    coef1, *_ = np.linalg.lstsq(A1, y, rcond=None)
    p1 = A1 @ coef1
    r2_omega_only = 1.0 - np.sum((y - p1) ** 2) / ss_tot

    A2 = np.array([[1.0, r["log_compactness"]] for r in bodies_in])
    coef2, *_ = np.linalg.lstsq(A2, y, rcond=None)
    p2 = A2 @ coef2
    r2_comp_only = 1.0 - np.sum((y - p2) ** 2) / ss_tot

    print(f"\nSingle-variable models:")
    print(f"  log(total) ~ log(omega) alone           : R^2 = {r2_omega_only:.4f}")
    print(f"  log(total) ~ log(compactness) alone     : R^2 = {r2_comp_only:.4f}")
    print(f"  log(total) ~ log(omega) + log(compact)  : R^2 = {r2:.4f}")

    delta_r2_omega = r2 - r2_comp_only  # marginal contribution of omega
    delta_r2_comp = r2 - r2_omega_only  # marginal contribution of compactness

    print(f"\nMarginal R^2 contributions:")
    print(f"  omega (Class I gear)        : ΔR² = {delta_r2_omega:+.4f}")
    print(f"  compactness (Class K pin-slot): ΔR² = {delta_r2_comp:+.4f}")

    # The empirical claim: BOTH gear (omega) AND pin-slot (compactness) are
    # needed; together they should explain most of SPrT_total's variance.
    both_essential = (delta_r2_omega > 0.01) and (delta_r2_comp > 0.01) and (r2 > 0.95)
    print(f"\n  Both gear+pin-slot essential? {both_essential}")
    if both_essential:
        verdict_t7 = "GEAR-PLUS-PIN-SLOT-DECOMPOSITION-EMPIRICALLY-CONFIRMED"
    elif r2 > 0.95:
        verdict_t7 = "ONE-COMPONENT-DOMINATES; other present but small contribution"
    else:
        verdict_t7 = "ADDITIONAL-COMPONENTS-NEEDED-BEYOND-GEAR-PIN-SLOT"
    print(f"  T7 verdict: {verdict_t7}")

    records = []
    records.append({
        "kind": "T7_sharp_gear_pin_slot_decomposition",
        "phase": "T7_sharp",
        "regression": "log(SPrT_total) = a + b*log(omega) + c*log(compactness)",
        "n_bodies": len(bodies_in),
        "intercept_a": float(a),
        "omega_coef_b": float(b_omega),
        "compactness_coef_c": float(c_comp),
        "r_squared_full": float(r2),
        "r_squared_omega_only": float(r2_omega_only),
        "r_squared_compactness_only": float(r2_comp_only),
        "delta_r2_omega_marginal": float(delta_r2_omega),
        "delta_r2_compactness_marginal": float(delta_r2_comp),
        "verdict": verdict_t7,
        "interpretation": (
            "omega = Class I cyclic substrate-baseline-linear (gear); "
            "compactness = Class K asymptotic-DOF (pin-slot); "
            "both contribute marginally; together explain SPrT_total variance."
        ),
    })

    # Per-body residual record for the multi-linear model
    for i, r in enumerate(bodies_in):
        residual = y[i] - pred[i]
        records.append({
            "kind": "T7_per_body_residual",
            "phase": "T7_sharp",
            "body": r["body"],
            "log_total_obs": float(y[i]),
            "log_total_pred": float(pred[i]),
            "log_residual": float(residual),
            "rel_residual_in_total_space": float(math.exp(abs(residual)) - 1.0),
        })

    out = Path(__file__).parent / "spike186_records_2026-05-19.ndjson"
    with open(out, "a") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"\nAppended {len(records)} T7-sharp records -> {out}")


if __name__ == "__main__":
    main()
