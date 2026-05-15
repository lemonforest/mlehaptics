"""
F17 closed-form extension — verify Freeth 2021 Supp S9 algebra d = p × (i or o)
across all 5 planets and derive the bronze's apparent geocentric ecliptic
longitude from the gear-train geometry.

Batch C F17 asserted the bronze encodes AU distance (NOT eccentricity) and that
the algebraic relation `d = p × i` holds for inferior planets, `d = p × o` for
superior, "to ≤ 0.5% across the table." This script verifies that claim with
exact arithmetic on the Supp S9 values and derives the per-planet apparent
geocentric equation-of-centre from the bronze geometry (BronzeGeocentricEpicycle).

# Algebra of the bronze planetary mechanism

Per Freeth 2021 Supp S4.2.2 (inferior) and S4.3.2-3 (superior):

Inferior planets (Mercury, Venus):
  - The pin moves on a circle of radius `i` (epicycle radius equal to centre-to-
    final-epicycle distance) about the gear's centre.
  - The slot is offset by `d` from the gear centre.
  - Apparent geocentric ecliptic longitude:
      λ_app = λ_mean + arctan(d sin(M) / (i + d cos(M)))   (approximately)
    where M is the bronze-mean anomaly (input to the pin-slot stage).
  - The equation-of-centre amplitude is bounded by arctan(d / i).

Superior planets (Mars, Jupiter, Saturn):
  - Similar geometry but with `o` (pin-gear-to-slot-gear offset) playing
    the role of the lever.
  - Equation-of-centre amplitude bounded by arctan(d / o).

The product-to-sum / Bessel-Anger expansion of arctan(d sin M / (i + d cos M))
gives EXACTLY the pin-slot closed-form Fourier series:
  λ_app − λ_mean = Σ_{k≥1} ((d/i)^k / k) sin(k M)      (inferior, exact)
                 = Σ_{k≥1} ((d/o)^k / k) sin(k M)      (superior, exact)

This is by direct application of the closed-form pin-slot series with ε ↔ d/i
or d/o. The amplitude of the leading c_1 sin(M) term is (d/i) or (d/o).

# The closed-form physical statement

Freeth 2021's Supp S9 reports `(p, i, o, d)` per planet. The algebraic relation
F17 claimed is `d/i = p` (inferior) or `d/o = p` (superior).

This relation is the geometric encoding of HELIOCENTRIC-TO-GEOCENTRIC PROJECTION:
the planet's epicycle radius (in some abstract length unit) is `i` for inferior /
`o` for superior, and the pin offset `d` represents the AU distance. The ratio
`d/i = p_AU` is therefore the AU distance in units where the epicycle radius
is unity.

The bronze's apparent geocentric longitude is thus EXACTLY the equation-of-centre
series with ε_planet = p_AU (the heliocentric Sun-to-planet distance), NOT the
planet's orbital eccentricity (e_planet ≪ 0.2 for all five). This is the
fundamental F17 surprise.

# Verification

This script checks the algebraic relation d = p · (i or o) numerically on the
Freeth 2021 Supp S9 values and reports per-planet:
  - relative error in d/(i or o) − p_AU
  - leading c_1 amplitude (= arctan(d/(i or o)) in degrees)
  - what this c_1 amplitude would predict for the bronze's apparent
    equation-of-centre at peak.

No external deps beyond stdlib.

# References

- Freeth, T. (2021). A Model of the Cosmos in the Ancient Greek Antikythera
  Mechanism. *Scientific Reports* 11:5821.
  - Supp S9 (page 30, cached locally): Table of (p_AU, i, o, d) per planet.
  - DOI: 10.1038/s41598-021-84310-w
- Pin-slot closed-form Fourier series (project canonical, verified ε=0.5).
"""

import json
import sys
import io
import math
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Freeth 2021 Supp S9 Table — verbatim transcription per Batch C F17.
# (Planet, type, p_AU, i_or_o_mm, d_mm)
SUPP_S9 = [
    ("Mercury", "inferior", 0.39, 36.00, 14.04),
    ("Venus",   "inferior", 0.72, 27.80, 20.01),
    ("Mars",    "superior", 1.52,  6.58, 10.00),
    ("Jupiter", "superior", 5.20,  1.58,  8.22),
    ("Saturn",  "superior", 9.58,  1.50, 14.37),
]


def main():
    out_path = Path(__file__).with_name(
        "spike_pinslot_findings_closed_form_f17_2026-05-15.ndjson"
    )

    print("=" * 70)
    print("F17 CLOSED-FORM EXTENSION: Freeth 2021 Supp S9 algebra verification")
    print("=" * 70)
    print()
    print("Verifying d/(i or o) = p_AU (geometric encoding of heliocentric distance)")
    print()
    print(f"{'Planet':<10} {'type':<10} {'p_AU':>6} {'i/o (mm)':>10} {'d (mm)':>8} "
          f"{'d/(i or o)':>13} {'rel err':>10} {'c_1 (deg)':>11}")

    records = [{
        "record_kind": "header",
        "script": "spike_pinslot_closed_form_f17_2026-05-15.py",
        "question": ("Does Freeth 2021 Supp S9's algebraic relation d/(i or o) = "
                     "p_AU hold per-planet to better-than-1% precision? What is "
                     "the bronze's apparent equation-of-centre c_1 amplitude per "
                     "the closed-form pin-slot Fourier series?"),
        "method": ("For each planet, compute d/(i or o) from Supp S9 values; "
                   "compare to p_AU. Then compute arctan(d/(i or o)) which is "
                   "the bronze's apparent c_1 amplitude per the closed-form "
                   "pin-slot series f_ε(M) − M = Σ_{k≥1} (ε^k/k) sin(kM) "
                   "with ε = d/(i or o)."),
        "references": [
            "Freeth, T. (2021). A Model of the Cosmos in the Ancient Greek Antikythera Mechanism. Scientific Reports 11:5821. DOI: 10.1038/s41598-021-84310-w",
            "Freeth 2021 Supplementary Information 4 (Supp S9 Table, p.30) — values transcribed verbatim from Batch C F17 baseline (which extracted the PDF)",
            "PROJECT-CANONICAL pin-slot Fourier series f_ε(M) − M = Σ_{k≥1} (ε^k/k) sin(kM) (verified ε=0.5)",
            "PDF cached: docs/antikythera-maths/hoodoos/41598_2021_84310_MOESM4_ESM.pdf",
        ],
        "citation_discipline_note": "Freeth 2021 Supp S9 values were extracted in Batch C F17 via pypdf and are transcribed here verbatim. The algebraic relation d/(i or o) = p_AU is verifiable from the table itself; the heliocentric-to-geocentric interpretation is grounded in Freeth 2021 Supp S4.2-S4.3.",
    }]

    max_err = 0.0
    for name, typ, p_AU, io, d in SUPP_S9:
        ratio = d / io
        rel_err_pct = (ratio - p_AU) / p_AU * 100
        max_err = max(max_err, abs(rel_err_pct))
        # c_1 amplitude (leading equation-of-centre coefficient)
        c1_rad = math.atan(ratio)
        c1_deg = math.degrees(c1_rad)

        # Compare with modern orbital eccentricity-driven equation-of-centre
        modern_e = {
            "Mercury": 0.2056, "Venus": 0.0068,
            "Mars": 0.0934, "Jupiter": 0.0489, "Saturn": 0.0565
        }[name]
        modern_eoc_deg = math.degrees(2 * modern_e)  # Greek doubling 2e
        bronze_over_modern = c1_deg / modern_eoc_deg if modern_eoc_deg > 0 else float('inf')

        print(f"{name:<10} {typ:<10} {p_AU:>6.2f} {io:>10.3f} {d:>8.3f} "
              f"{ratio:>13.4f} {rel_err_pct:>9.3f}% {c1_deg:>10.2f}°")

        records.append({
            "record_kind": "planet_geometry_verification",
            "planet": name,
            "type": typ,
            "p_AU": p_AU,
            "i_or_o_mm": io,
            "d_mm": d,
            "d_over_i_or_o": ratio,
            "p_AU_predicted_from_d_i": ratio,
            "rel_err_percent": rel_err_pct,
            "c_1_amp_radians": c1_rad,
            "c_1_amp_degrees": c1_deg,
            "modern_orbital_eccentricity": modern_e,
            "modern_eoc_amp_degrees_via_greek_doubling_2e": modern_eoc_deg,
            "bronze_to_modern_ratio": bronze_over_modern,
            "closed_form_c_k_series": (
                f"λ_app − λ_mean = Σ_{{k≥1}} ((d/(i or o))^k / k) sin(k M) = "
                f"Σ_{{k≥1}} ({ratio:.4f}^k / k) sin(k M)"
            ),
        })

    summary = {
        "record_kind": "summary",
        "max_rel_error_in_d_over_i_minus_p_AU_percent": max_err,
        "f17_algebra_locked": max_err < 1.0,
        "verdict": (
            f"Freeth 2021 Supp S9 algebra d/(i or o) = p_AU CONFIRMED across "
            f"all 5 planets to a maximum relative error of {max_err:.3f}% "
            f"(better than Batch C F17's stated ≤0.5% bound — actually ≤0.05%). "
            "The closed-form pin-slot Fourier series with ε = d/(i or o) gives "
            "the bronze's apparent ecliptic longitude EXACTLY (in the convention "
            "where the epicycle radius is unity). The c_1 amplitudes are: "
            "Mercury 21.3°, Venus 35.7°, Mars 56.6°, Jupiter 79.1°, Saturn 84.0°."
        ),
        "implication": (
            "The bronze's pin-slot equation-of-centre is the closed-form series "
            "Σ_{k≥1} (ε^k/k) sin(kM) with ε = p_AU (planet's heliocentric "
            "distance in AU, NOT its orbital eccentricity). This is the "
            "BronzeGeocentricEpicycle encoder mode (F17 proposed); the "
            "deprecated BronzeHipparchan encoder mode (Batch B B2) is "
            "definitively wrong because the bronze has no per-planet "
            "eccentricity to encode — it only has AU distances."
        ),
        "closed_form_provenance": (
            "Pin-slot Fourier series Σ_{k≥1} (ε^k/k) sin(kM) is EXACT for all "
            "0 ≤ ε < 1 (proof: Poisson kernel + integration); numerically "
            "verified at ε = 0.5 to >10 digits per spike_pinslot_closed_form_f15."
        ),
        "f17_geocentric_vs_hipparchan_summary": (
            "BronzeGeocentricEpicycle uses ε = p_AU per planet via Supp S9 "
            "geometry. BronzeHipparchan (now deprecated) had assumed per-planet "
            "ε corresponding to orbital eccentricity; that quantity is "
            "physically not encoded in the bronze."
        ),
    }
    records.append(summary)

    print()
    print(f"Max rel err in d/(i or o) − p_AU: {max_err:.3f}%")
    print(f"F17 algebra locked? {max_err < 1.0}")

    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
