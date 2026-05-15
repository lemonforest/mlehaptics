"""
Spike #24 Phase 3a — analytical predicted residual signatures.

Derives the predicted residual signature for each ephemerides-spectral body
under the assumption that Class K (equation-of-centre / pin-slot algebra) is
absent from the encoder, while DE441 truth carries it via integrated orbital
dynamics. Per user_stance_kepler_shape_universal, the gap should leak as
sinusoidal signal at the body's anomalistic frequency with amplitude near
ε ≈ 2·e (Greek-frame doubling per user_stance_pi_as_projection).

ANALYTICAL PASS — no numerical integration, no skyfield, no DE441 read.
Pure closed-form derivation from known orbital eccentricities + periods.

Phase 3b (numerical validation against actual DE441 + ephemerides-spectral
encoder) is deferred to a follow-up; the analytical predictions here are
what 3b will validate against.

Phase 3c (real-coupling subtraction) is also deferred — for the analytical
pass we predict the *raw* residual signature assuming the encoder
implements ONLY the bare mean-motion (cyclic-group period ratios) and is
missing equation-of-centre. Real-coupling subtraction would refine this
estimate downward; for now we predict the upper bound on the missing-
primitive signature per body.

Stdlib only. NDJSON output.
"""

import io
import json
import math
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Modern eccentricities and sidereal periods for major bodies.
# Sources: NASA Planetary Fact Sheet (NSSDC), JPL HORIZONS, IAU minor-body
# database. Eccentricities are mean values rounded to 4 decimals.
# Period values in sidereal days for the heliocentric or planet-centric
# orbit as appropriate.
BODY_DATA = [
    # name, period_days_sidereal, e (modern), category, parent_body_for_anomalistic
    # Planets (heliocentric)
    ("Mercury",     87.96925980,  0.2056,  "planet",   "sun"),
    ("Venus",      224.70079922,  0.0068,  "planet",   "sun"),
    ("Terra",      365.25636300,  0.0167,  "planet",   "sun"),
    ("Mars",       686.97970000,  0.0934,  "planet",   "sun"),
    ("Jupiter",   4332.58900000,  0.0484,  "planet",   "sun"),
    ("Saturn",   10759.22000000,  0.0541,  "planet",   "sun"),
    ("Uranus",   30688.50000000,  0.0472,  "planet",   "sun"),
    ("Neptune",  60182.00000000,  0.0086,  "planet",   "sun"),
    ("Pluto",    90560.00000000,  0.2488,  "planet",   "sun"),
    # Earth's moon (geocentric orbit; eccentricity drives lunar anomaly)
    ("Luna",        27.32166156,  0.0549,  "moon",     "terra"),
    # Mars moons (low e, but ε still observable in residual)
    ("Phobos",       0.31891023,  0.0151,  "moon",     "mars"),
    ("Deimos",       1.26244000,  0.0002,  "moon",     "mars"),
    # Galilean moons (Laplace 4:2:1 resonance; Io's e is forced by Europa)
    ("Io",           1.76913786,  0.0041,  "moon",     "jupiter"),
    ("Europa",       3.55118100,  0.0090,  "moon",     "jupiter"),
    ("Ganymede",     7.15455296,  0.0013,  "moon",     "jupiter"),
    ("Callisto",    16.68901840,  0.0074,  "moon",     "jupiter"),
    # Classical Saturnian moons
    ("Mimas",        0.94242196,  0.0196,  "moon",     "saturn"),
    ("Enceladus",    1.37021785,  0.0047,  "moon",     "saturn"),
    ("Tethys",       1.88780216,  0.0001,  "moon",     "saturn"),
    ("Dione",        2.73691500,  0.0022,  "moon",     "saturn"),
    ("Rhea",         4.51821200,  0.0010,  "moon",     "saturn"),
    ("Titan",       15.94542100,  0.0288,  "moon",     "saturn"),
    ("Hyperion",    21.27660925,  0.1230,  "moon",     "saturn"),
    ("Iapetus",     79.32150000,  0.0286,  "moon",     "saturn"),
    # Uranian classical moons
    ("Miranda",      1.41347925,  0.0013,  "moon",     "uranus"),
    ("Ariel",        2.52037935,  0.0012,  "moon",     "uranus"),
    ("Umbriel",      4.14417700,  0.0039,  "moon",     "uranus"),
    ("Titania",      8.70586730,  0.0011,  "moon",     "uranus"),
    ("Oberon",      13.46323900,  0.0014,  "moon",     "uranus"),
    # Neptunian
    ("Triton",       5.87685400,  0.0000,  "moon",     "neptune"),
    # Pluto-Charon (mutual tidal lock; near-zero e but the system has unique dynamics)
    ("Charon",       6.38723000,  0.0022,  "moon",     "pluto"),
]


def predicted_residual_signature(name, period_days, e, n_harmonics=4):
    """Compute per-body predicted residual signature under Class K absence.

    Returns a dict with predicted (frequency, amplitude) per harmonic, plus
    metadata. ε is the Greek-frame eccentricity per pi-as-projection: at
    small e, ε ≈ 2·e; the more accurate relation comes from the Kepler
    equation-of-centre series where c₁ = ε in the eccentric-anomaly form
    and ε relates to the focal-frame e via ε ≈ 2·e + higher-order terms.

    For the analytical-pass we use ε = 2·e directly (Greek convention).
    """
    eps = 2.0 * e
    # Frequency in cycles per day (one full orbit per period_days)
    f_fundamental_per_day = 1.0 / period_days if period_days > 0 else 0.0
    harmonics = []
    for k in range(1, n_harmonics + 1):
        c_k_rad = (eps ** k) / k  # Bessel-Anger leading term; ε^k / k coefficient
        c_k_deg = math.degrees(c_k_rad)
        harmonics.append({
            "harmonic": k,
            "frequency_per_day": k * f_fundamental_per_day,
            "amplitude_radians": c_k_rad,
            "amplitude_degrees": c_k_deg,
        })
    return {
        "body": name,
        "period_sidereal_days": period_days,
        "e_modern": e,
        "eps_greek": eps,
        "fundamental_frequency_per_day": f_fundamental_per_day,
        "harmonics": harmonics,
        "leading_c1_amplitude_degrees": math.degrees(eps),
    }


def main():
    out_path = Path(__file__).with_name(
        "spike_24_phase_3a_predicted_residuals_2026-05-15.ndjson"
    )

    records = []

    # Header record
    records.append({
        "record_kind": "header",
        "spike": "Spike #24",
        "phase": "Phase 3a — analytical predicted residual (Class K absent)",
        "date": "2026-05-15",
        "method": ("Per body, predict the residual signature from the missing "
                   "equation-of-centre / pin-slot primitive. ε = 2e (Greek "
                   "convention per pi-as-projection); harmonic series c_k = ε^k / k "
                   "at k * f_fundamental. No real-coupling subtraction; this is "
                   "the upper-bound prediction. Phase 3b numerically validates."),
        "n_bodies_analytical": len(BODY_DATA),
        "load_bearing": ("ephemerides-spectral encoder is predicted to leak the "
                         "equation-of-centre signature at the body's anomalistic "
                         "frequency with leading amplitude ε = 2e (degrees), per "
                         "user_stance_kepler_shape_universal."),
    })

    # Per-body predictions
    for name, period, e, category, parent in BODY_DATA:
        sig = predicted_residual_signature(name, period, e)
        sig["record_kind"] = "predicted_residual"
        sig["category"] = category
        sig["parent_body"] = parent
        records.append(sig)

    # Summary: rank bodies by predicted c_1 amplitude (highest signal expected first)
    bodies_ranked = sorted(
        [r for r in records if r.get("record_kind") == "predicted_residual"],
        key=lambda r: r["leading_c1_amplitude_degrees"],
        reverse=True,
    )

    records.append({
        "record_kind": "ranked_summary",
        "ranking_metric": "leading_c1_amplitude_degrees",
        "top_5": [
            {"body": r["body"], "c1_deg": round(r["leading_c1_amplitude_degrees"], 3)}
            for r in bodies_ranked[:5]
        ],
        "bottom_5": [
            {"body": r["body"], "c1_deg": round(r["leading_c1_amplitude_degrees"], 3)}
            for r in bodies_ranked[-5:]
        ],
        "median_c1_deg": round(
            bodies_ranked[len(bodies_ranked) // 2]["leading_c1_amplitude_degrees"], 3
        ),
    })

    # Closing record: methodology notes for Phase 3b/3c
    records.append({
        "record_kind": "phase_3b_3c_pointer",
        "phase_3b_numerical_validation": (
            "Run ephemerides-spectral encoder forward-sweep vs JPL DE441 over "
            "design epoch; FFT-inverse the per-body residual; verify c_1 peak "
            "amplitude matches predicted value here within fabrication noise."
        ),
        "phase_3c_real_coupling_subtraction": (
            "Before claiming the residual confirms Class K absence, subtract "
            "contributions from real couplings: mean-motion resonances "
            "(Sol Resonance Graph), secular precession (Laskar tables), tidal "
            "(Moon especially), J2 (J2 affects close satellites), solar tides "
            "(Moon evection 2(D-l) per F15). The post-subtraction residual is "
            "what should match the Phase 3a prediction."
        ),
        "expected_concordance_per_body": (
            "Inner planets (Mercury 23.6°, Pluto 28.5° leading c_1) are strongest "
            "signals; outer planets and low-e moons are below 10° leading c_1. "
            "Saturn moons Hyperion (14.1°) and Titan (3.3°) are notable; Tethys "
            "(0.012°) and Triton (0.0°) are at or below detection threshold."
        ),
    })

    # Write NDJSON
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Console output
    print("=" * 70)
    print("Spike #24 Phase 3a — analytical predicted residual signatures")
    print("=" * 70)
    print()
    print(f"{'Body':<12} {'Period (d)':>12} {'e':>8} {'eps':>8} {'c_1 (deg)':>11}")
    print("-" * 60)
    for name, period, e, _cat, _par in BODY_DATA:
        eps = 2.0 * e
        c1_deg = math.degrees(eps)
        print(f"{name:<12} {period:>12.4f} {e:>8.4f} {eps:>8.4f} {c1_deg:>11.4f}")

    print()
    print(f"NDJSON output: {out_path}")
    print(f"  Records: {len(records)} (1 header + {len(BODY_DATA)} per-body + "
          f"1 ranked summary + 1 phase_3b_3c pointer)")
    print()
    print("Top 5 expected signals (largest c_1):")
    for r in bodies_ranked[:5]:
        print(f"  {r['body']:<12} c_1 = {r['leading_c1_amplitude_degrees']:>8.3f} deg")
    print()
    print("Bottom 5 expected signals (smallest c_1):")
    for r in bodies_ranked[-5:]:
        print(f"  {r['body']:<12} c_1 = {r['leading_c1_amplitude_degrees']:>8.3f} deg")


if __name__ == "__main__":
    main()
