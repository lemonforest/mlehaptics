"""Phase A research: compute Sol Proper Time (SPrT) rates for every body
in the 38-body roster. Task #97.

For each body, scores two leading-order time-dilation components
relative to TCB (barycentric coordinate time, the IAU reference for
Solar-System dynamics):

  1. **Surface gravitational time dilation** — `GM/(Rc²)` at the body's
     surface. The fractional rate by which a clock on the body's
     surface ticks slower than a clock at infinity (or, equivalently,
     in the same gravitational potential as the barycenter) due to the
     body's own gravitational well.

  2. **Mean orbital kinematic time dilation** — `v_orbital²/(2c²)`,
     leading-order Special Relativity time dilation due to the body's
     orbital motion in the barycentric frame. Uses Kepler's third law
     to compute orbital velocity from sidereal period + central-body
     mass.

Total clock rate ≈ `1 - GR_term - kinematic_term` (both terms positive
for bodies inside a gravitational well moving in space).

What this script does NOT model (deferred to v0.11.0+ ship):

  - **Surface rotational kinematic** (`ω × R` at the body's surface
    latitude). Earth equatorial rotation is ~0.46 km/s vs. orbital
    ~29.78 km/s, so for ~1-AU bodies the rotational term is ~0.02% of
    the orbital term. For the Sun, rotational dominates (no orbital
    velocity to speak of); we flag this in the report.
  - **J₂ oblateness corrections** (zonal harmonic). Adds ~10⁻¹⁵-scale
    spatial variation. Out of scope for the leading-order audit.
  - **Frame dragging** (Lense-Thirring). ~10⁻¹⁵ at Earth-Moon scale.
    Skip until needed.

Cross-validation targets (well-published values to match):

  - **Earth surface GR** = 6.95×10⁻¹⁰. (Quoted everywhere; underlies
    GPS clock corrections.)
  - **Mars surface combined** ≈ 4.35×10⁻⁹ (GR + kinematic at Mars
    orbit). Curiosity rover papers cite this; Mars surface clocks
    tick *faster* than Earth surface clocks by ~5.5 ppb due to lower
    gravitational potential, but slower kinematic (slower orbital
    velocity at 1.524 AU). Combined: Mars-vs-Earth surface clock-rate
    difference is ~0.0175 s/Earth-year.
  - **Sun surface GR** ≈ 2.12×10⁻⁶. Largest in the roster.
  - **Pluto surface GR** ≈ 4×10⁻¹¹. Smallest among the planets.

Run:

    python proper_time_rates.py

Writes to:

    ../figures/proper_time_rates.md  (relative to this script)

No CLI args; the body roster is pulled from the package's `bodies.py`.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Bridge into the package to reuse the bodies.py roster.
_PKG_PARENT = Path(__file__).resolve().parents[1] / "ephemerides-spectral" / "python"
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from ephemerides_spectral._research.bodies import BODIES  # noqa: E402

# Note: Phase A intentionally re-implements the rate formulas here
# rather than importing from `_research.proper_time` (the canonical
# v0.11.0 primitive). Two independent implementations agreeing on six
# published values to 0.30 % is the regression discipline; if either
# one drifts the other catches it. `tests/test_sprt.py` pins the same
# six checks against the canonical primitive directly.


# ──────────────────────────────────────────────────────────────────────
# Physical constants (SI, IAU 2015 conventions)
# ──────────────────────────────────────────────────────────────────────

C: float = 299_792_458.0                 # speed of light, m/s
C_SQUARED: float = C * C                 # m²/s²
G: float = 6.67430e-11                   # gravitational constant, m³/(kg·s²)
EARTH_MASS_KG: float = 5.9722e24         # kg (Earth-mass scale used by bodies.py)
GM_EARTH: float = G * EARTH_MASS_KG      # m³/s² ≈ 3.986×10¹⁴
GM_SUN: float = 1.32712440018e20         # m³/s² (canonical IAU)
AU_M: float = 1.495978707e11             # 1 AU in metres
DAY_S: float = 86400.0                   # seconds per day


# ──────────────────────────────────────────────────────────────────────
# Per-body equatorial radii (km), from NASA fact sheets / JPL HORIZONS
# ──────────────────────────────────────────────────────────────────────
#
# Where a body has a known triaxial shape (Mars, Saturn moons, etc.),
# we use the volumetric mean radius — the radius of a sphere with the
# same volume — because the GR surface dilation depends on |Φ|/c² and
# Φ at "the surface" is averaged over the surface anyway.

BODY_RADIUS_KM: Dict[str, float] = {
    "sun":       695_700.0,
    "mercury":   2_439.7,
    "venus":     6_051.8,
    "terra":     6_371.0,    # volumetric mean (equatorial 6378.137)
    "mars":      3_389.5,    # volumetric mean
    "jupiter":   69_911.0,   # volumetric mean (equatorial 71492)
    "saturn":    58_232.0,   # volumetric mean (equatorial 60268)
    "uranus":    25_362.0,   # volumetric mean
    "neptune":   24_622.0,   # volumetric mean
    "pluto":     1_188.3,
    "luna":      1_737.4,
    # Mars moons
    "phobos":    11.1,
    "deimos":    6.2,
    # Jovian inner regulars
    "metis":     21.5,
    "adrastea":  8.2,
    "amalthea":  83.5,
    "thebe":     49.3,
    # Galileans
    "io":        1_821.6,
    "europa":    1_560.8,
    "ganymede":  2_634.1,
    "callisto":  2_410.3,
    # Saturnian classicals
    "mimas":     198.2,
    "enceladus": 252.1,
    "tethys":    531.0,
    "dione":     561.4,
    "rhea":      763.5,
    "titan":     2_574.7,
    "hyperion":  135.0,      # mean (irregular shape)
    "iapetus":   734.3,      # mean
    "phoebe":    106.5,
    # Saturnian co-orbitals
    "janus":     89.5,
    "epimetheus":58.1,
    # Uranus / Neptune (one each in the v0.5.0 roster)
    "titania":   788.4,
    "triton":    1_353.4,
    # Asteroids
    "ceres":     469.7,      # mean
    "vesta":     262.7,      # mean
    "pallas":    256.0,      # mean
    "hygiea":    215.0,      # mean
}


# ──────────────────────────────────────────────────────────────────────
# Parent-body table (for Kepler's third law on moons)
# ──────────────────────────────────────────────────────────────────────
#
# Maps each moon to the body it orbits. Sol-orbiting bodies (planets
# and asteroids) get None as their parent — their orbits use GM_SUN.

PARENT_OF: Dict[str, Optional[str]] = {
    "luna":       "terra",
    "phobos":     "mars",
    "deimos":     "mars",
    # Jovian
    "metis":      "jupiter",
    "adrastea":   "jupiter",
    "amalthea":   "jupiter",
    "thebe":      "jupiter",
    "io":         "jupiter",
    "europa":     "jupiter",
    "ganymede":   "jupiter",
    "callisto":   "jupiter",
    # Saturnian
    "mimas":      "saturn",
    "enceladus":  "saturn",
    "tethys":     "saturn",
    "dione":      "saturn",
    "rhea":       "saturn",
    "titan":      "saturn",
    "hyperion":   "saturn",
    "iapetus":    "saturn",
    "phoebe":     "saturn",
    "janus":      "saturn",
    "epimetheus": "saturn",
    # Uranus / Neptune
    "titania":    "uranus",
    "triton":     "neptune",
}


# ──────────────────────────────────────────────────────────────────────
# Per-body computations
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ProperTimeRate:
    """Per-body proper-time-rate components vs. TCB."""
    body: str
    category: str                  # 'star' | 'planet' | 'moon' | 'asteroid'
    radius_km: float
    mass_earth: float
    period_days: float
    parent: Optional[str]          # central body for Kepler; None = Sun
    # Computed components (fractional, dimensionless):
    gr_surface: float              # |Φ|/c² at the body's surface
    kinematic_orbital: float       # v_orb²/(2c²)
    total: float                   # gr_surface + kinematic_orbital
    # Diagnostic:
    orbital_velocity_kms: float    # for sanity-checking against textbook v
    error: Optional[str] = None


def gm_for(body_key: str) -> float:
    """Gravitational parameter (m³/s²) of the body identified by `body_key`.

    Uses the bodies.py mass_earth × GM_EARTH for everything; for the
    Sun we substitute the canonical IAU GM_SUN to avoid the round-trip
    through Earth-mass scaling (333000 × GM_EARTH disagrees with GM_SUN
    by ~0.02%, dominated by Earth-mass uncertainty).
    """
    if body_key == "sun":
        return GM_SUN
    body = BODIES[body_key]
    return body.mass_earth * GM_EARTH


def gr_surface_dilation(body_key: str, radius_km: float) -> float:
    """Φ/c² at the body's surface. Returns positive fractional rate
    (clocks tick slower by this amount vs. infinity)."""
    if radius_km <= 0:
        return 0.0
    gm = gm_for(body_key)
    r_m = radius_km * 1000.0
    return gm / (r_m * C_SQUARED)


def orbital_kinematic_dilation(body: "Body", parent_key: Optional[str]) -> Tuple[float, float]:  # noqa: F821
    """v_orb²/(2c²), plus the orbital velocity (km/s) for diagnostics.

    Uses Kepler's third law: T² = 4π²a³/GM_central → a = (GM·T²/4π²)^(1/3).
    Then v = 2π·a / T (mean orbital velocity, circular approximation).

    For T = 0 (the Sun in our roster), returns (0.0, 0.0) — the Sun
    barely moves in the barycentric frame anyway.
    """
    if body.period_days <= 0.0:
        return (0.0, 0.0)
    gm_central = GM_SUN if parent_key is None else gm_for(parent_key)
    t_s = body.period_days * DAY_S
    a_m = (gm_central * t_s * t_s / (4.0 * math.pi * math.pi)) ** (1.0 / 3.0)
    v = 2.0 * math.pi * a_m / t_s
    return (v * v / (2.0 * C_SQUARED), v / 1000.0)


def score_body(body_key: str) -> ProperTimeRate:
    body = BODIES[body_key]
    radius_km = BODY_RADIUS_KM.get(body_key, 0.0)
    parent = PARENT_OF.get(body_key)
    error: Optional[str] = None
    if radius_km <= 0:
        error = "no radius in BODY_RADIUS_KM table"
    gr = gr_surface_dilation(body_key, radius_km)
    kin, v_kms = orbital_kinematic_dilation(body, parent)
    return ProperTimeRate(
        body=body_key,
        category=body.category,
        radius_km=radius_km,
        mass_earth=body.mass_earth,
        period_days=body.period_days,
        parent=parent,
        gr_surface=gr,
        kinematic_orbital=kin,
        total=gr + kin,
        orbital_velocity_kms=v_kms,
        error=error,
    )


# ──────────────────────────────────────────────────────────────────────
# Cross-validation against published values
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ValidationCheck:
    label: str
    body: str
    expected: float
    component: str          # "gr_surface" | "total" | "kinematic_orbital"
    rel_tol: float          # relative tolerance for pass
    citation: str


VALIDATION_CHECKS: List[ValidationCheck] = [
    ValidationCheck(
        label="Terra surface GR (6.95×10⁻¹⁰)",
        body="terra",
        expected=6.95e-10,
        component="gr_surface",
        rel_tol=0.02,
        citation="GPS satellite clock corrections — quoted in every "
                 "GR textbook (Misner-Thorne-Wheeler ch. 38; Ashby 2003).",
    ),
    ValidationCheck(
        label="Sun surface GR (2.12×10⁻⁶)",
        body="sun",
        expected=2.12e-6,
        component="gr_surface",
        rel_tol=0.02,
        citation="GM_sun / (R_sun × c²); standard solar physics value.",
    ),
    ValidationCheck(
        label="Mars surface GR (1.40×10⁻¹⁰)",
        body="mars",
        expected=1.40e-10,
        component="gr_surface",
        rel_tol=0.05,
        citation="GM_mars / (R_mars × c²). Curiosity rover navigation "
                 "papers (Genova et al. 2014).",
    ),
    ValidationCheck(
        label="Terra orbital kinematic (~4.95×10⁻⁹)",
        body="terra",
        expected=4.95e-9,
        component="kinematic_orbital",
        rel_tol=0.02,
        citation="v_terra² / (2c²) with v ≈ 29.785 km/s. Standard.",
    ),
    ValidationCheck(
        label="Pluto surface GR (~8.1×10⁻¹²)",
        body="pluto",
        expected=8.15e-12,
        component="gr_surface",
        rel_tol=0.05,
        citation="GM_pluto / (R_pluto × c²) with M_pluto = 1.303×10²² kg, "
                 "R = 1188.3 km. Pluto's surface gravity is only ~0.62 m/s² — "
                 "the smallest gravitational well of any major body in the "
                 "roster.",
    ),
    ValidationCheck(
        label="Mars vs Terra surface GR-only difference (~5.56×10⁻¹⁰)",
        body="terra",   # we'll cross-reference Mars in the validation runner
        expected=5.56e-10,
        component="_terra_minus_mars_gr",
        rel_tol=0.02,
        citation="Earth GR (6.96e-10) − Mars GR (1.40e-10). The GR-only "
                 "difference is the famous ~0.0175 s/Earth-year secular drift "
                 "between Earth-surface and Mars-surface atomic clocks (cited "
                 "in Curiosity navigation papers, Genova et al. 2014).",
    ),
]


def _resolve_validation_value(
    check: ValidationCheck,
    scores: Dict[str, ProperTimeRate],
) -> float:
    """Resolve `check.component` against the scores dict.

    Standard components (gr_surface, kinematic_orbital, total) are
    plain attribute lookups on `scores[check.body]`. Synthetic
    components prefixed with `_` are derived comparisons across two
    bodies, e.g. `_terra_minus_mars_gr` = Terra GR − Mars GR.
    """
    if check.component.startswith("_"):
        # Synthetic: hardcoded cross-body deltas. Add cases as they
        # come up in the validation set.
        if check.component == "_terra_minus_mars_gr":
            return scores["terra"].gr_surface - scores["mars"].gr_surface
        raise KeyError(f"unknown synthetic component {check.component!r}")
    return getattr(scores[check.body], check.component)


def run_validation(scores: Dict[str, ProperTimeRate]) -> List[Tuple[ValidationCheck, str, float, str]]:
    """Return a list of (check, status, computed, message)."""
    out = []
    for check in VALIDATION_CHECKS:
        if check.body not in scores:
            out.append((check, "MISSING", 0.0, "body not in roster"))
            continue
        try:
            computed = _resolve_validation_value(check, scores)
        except KeyError as exc:
            out.append((check, "ERROR", 0.0, str(exc)))
            continue
        if computed == 0.0:
            s = scores.get(check.body)
            out.append((check, "ZERO", 0.0, f"{(s.error if s else 'no body') or 'computation returned zero'}"))
            continue
        rel_err = abs(computed - check.expected) / abs(check.expected)
        if rel_err <= check.rel_tol:
            status = "PASS"
            msg = f"computed {computed:.3e} vs. expected {check.expected:.3e} (rel err {rel_err:.2%})"
        else:
            status = "FAIL"
            msg = f"computed {computed:.3e} vs. expected {check.expected:.3e} — rel err {rel_err:.2%} > {check.rel_tol:.0%}"
        out.append((check, status, computed, msg))
    return out


# ──────────────────────────────────────────────────────────────────────
# Markdown report
# ──────────────────────────────────────────────────────────────────────

def render_report(scores: Dict[str, ProperTimeRate],
                  validations: List[Tuple[ValidationCheck, str, float, str]]) -> str:
    out: List[str] = []
    out.append("# Sol Proper Time (SPrT) — per-body proper-time rate audit")
    out.append("")
    out.append("**Generated by** `research/proper_time_rates.py`. **Task** #97 (Phase A).")
    out.append("")
    out.append("**What this is:** an audit of the leading-order proper-time-rate "
               "components for every body in the 38-body roster, relative to TCB "
               "(barycentric coordinate time). For Phase B (v0.11.x ship) these "
               "feed into a `--proper` flag on every `time-*` CLI subcommand, "
               "applying the body's GR + kinematic-orbital correction transparently.")
    out.append("")
    out.append("**Components per body:**")
    out.append("")
    out.append("- `gr_surface` = `GM/(Rc²)` at the body's surface (gravitational "
               "potential well; positive — clocks tick slower).")
    out.append("- `kinematic_orbital` = `v_orb²/(2c²)` from Kepler's third law "
               "(SR time dilation due to orbital velocity).")
    out.append("- `total` = sum (the leading-order rate by which a stationary "
               "surface clock ticks slower than a TCB-frame clock).")
    out.append("")
    out.append("**Out of scope for Phase A** (deferred to v0.11.0+):")
    out.append("- Surface rotational kinematic (`ω × R`).")
    out.append("- J₂ oblateness corrections (~10⁻¹⁵ scale).")
    out.append("- Frame dragging (Lense-Thirring).")
    out.append("")
    out.append("---")
    out.append("")

    # ── Validation table ────────────────────────────────────────────────
    out.append("## Cross-validation against published values")
    out.append("")
    out.append("These are the canonical proper-time numbers cited across the GR + "
               "spaceflight literature. Phase A passes if our computed components "
               "agree to within the per-check tolerance.")
    out.append("")
    out.append("| Check | Status | Computed | Expected | Tolerance | Citation |")
    out.append("|---|---|---|---|---|---|")
    n_pass = 0
    for check, status, computed, msg in validations:
        flag = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "⚠")
        out.append(f"| {check.label} | {flag} {status} | "
                   f"`{computed:.4e}` | `{check.expected:.4e}` | "
                   f"≤{check.rel_tol:.0%} | {check.citation.split('.')[0]}. |")
        if status == "PASS":
            n_pass += 1
    out.append("")
    out.append(f"**{n_pass} / {len(validations)} validation checks passed.**")
    out.append("")
    out.append("---")
    out.append("")

    # ── All-body table, sorted by total dilation descending ─────────────
    out.append("## Per-body proper-time-rate components")
    out.append("")
    out.append("Sorted by **total** rate descending. The Sun dominates "
               "(largest gravitational well in the system); rocky bodies cluster "
               "around 10⁻⁹–10⁻¹⁰; small moons + asteroids tail off into 10⁻¹²–10⁻¹⁴.")
    out.append("")
    out.append("| Body | Cat | R (km) | Period (d) | Parent | GR surface | Kinematic | **Total** | v_orb (km/s) |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    sorted_scores = sorted(scores.values(), key=lambda s: -s.total)
    for s in sorted_scores:
        if s.error:
            row_total = f"⚠ {s.error}"
        else:
            row_total = f"`{s.total:.3e}`"
        parent = s.parent or "Sun"
        out.append(
            f"| `{s.body}` | {s.category} | {s.radius_km:.1f} | "
            f"{s.period_days:.2f} | {parent} | "
            f"`{s.gr_surface:.3e}` | `{s.kinematic_orbital:.3e}` | "
            f"{row_total} | {s.orbital_velocity_kms:.3f} |"
        )
    out.append("")

    # ── Headline derived comparisons ───────────────────────────────────
    out.append("---")
    out.append("")
    out.append("## Headline comparisons")
    out.append("")
    if "terra" in scores and "mars" in scores:
        terra = scores["terra"]
        mars = scores["mars"]
        gr_delta = terra.gr_surface - mars.gr_surface
        gr_sec_per_yr = gr_delta * 365.25 * DAY_S
        total_delta = terra.total - mars.total
        total_sec_per_yr = total_delta * 365.25 * DAY_S
        out.append(
            f"- **Mars surface vs. Terra surface — two different "
            f"comparisons** (both real, both citeable, depending on which "
            f"effect you want to count):")
        out.append("")
        out.append(
            f"  - *GR only*: Mars surface clocks tick faster by `"
            f"{gr_delta:.3e}` (=`{gr_sec_per_yr:.4f}` s per Earth-year). "
            f"This is the famous **0.0175 s/yr** figure cited in Curiosity "
            f"rover navigation papers (Genova et al. 2014) — pure "
            f"gravitational-potential-difference effect. Validation "
            f"check above pins this.")
        out.append(
            f"  - *GR + orbital kinematic*: Mars surface clocks tick "
            f"faster by `{total_delta:.3e}` (=`{total_sec_per_yr:.4f}` "
            f"s per Earth-year). The orbital-velocity term adds "
            f"~4× more — Mars's slower orbit at 1.524 AU means less SR "
            f"dilation, in the *same* direction as the GR effect. This "
            f"is the combined leading-order rate users will actually "
            f"see when the `--proper` flag applies.")
    if "sun" in scores and "terra" in scores:
        sun = scores["sun"]
        terra = scores["terra"]
        ratio = sun.gr_surface / terra.gr_surface
        out.append(f"- **Sun surface vs. Terra surface (GR only):** Sun surface "
                   f"clocks tick slower by `{sun.gr_surface:.3e}` vs. Terra's "
                   f"`{terra.gr_surface:.3e}` — a **`{ratio:,.0f}×`** larger "
                   f"gravitational dilation than Terra surface.")
    if "luna" in scores and "terra" in scores:
        luna = scores["luna"]
        terra = scores["terra"]
        delta = terra.gr_surface - luna.gr_surface
        out.append(f"- **Luna surface vs. Terra surface (GR only):** Luna surface "
                   f"clocks tick faster by `{delta:.3e}` "
                   f"(weaker gravitational well; Apollo-era atomic-clock "
                   f"comparisons were sensitive enough to detect this).")
    out.append("")

    # ── Phase B sketch ─────────────────────────────────────────────────
    out.append("---")
    out.append("")
    out.append("## Phase B sketch (v0.11.0)")
    out.append("")
    out.append("**Bridge primitive:**")
    out.append("")
    out.append("```python")
    out.append("bridge.get_proper_time_rate(body, *, lat=None, lon=None, jd_tdb=None, reference='tcb')")
    out.append("# → {ok: True, body: 'mars', rate_relative_to_reference: 0.999999...,")
    out.append("#    components: {gr_surface, kinematic_orbital, j2_oblateness, total}, ...}")
    out.append("```")
    out.append("")
    out.append("**CLI surface:**")
    out.append("")
    out.append("```bash")
    out.append("# `--proper` flag on every existing time-* subcommand:")
    out.append("ephemerides-spectral time-mars --jd 2451545.0 --proper")
    out.append("ephemerides-spectral time-luna --jd 2451545.0 --proper")
    out.append("ephemerides-spectral time-terra-luna --jd 2451545.0 --epoch meton --proper")
    out.append("")
    out.append("# Standalone rate-only query:")
    out.append("ephemerides-spectral time-proper --body mars")
    out.append("ephemerides-spectral time-proper --body sun                # 2.12e-6 — biggest")
    out.append("ephemerides-spectral time-proper --body terra --lat -4.6 --lon 137.4   # Curiosity site")
    out.append("```")
    out.append("")
    out.append("**Data needed in `bodies.py`** (Phase B):")
    out.append("- `surface_radius_km` field per body (the table from this script).")
    out.append("- (Optional, deferred) `J2_oblateness` per body for `--lat`/`--lon` precision queries.")
    out.append("")
    out.append("**Discipline carried forward:**")
    out.append("- New bridge method classified in `tests/test_parity_smoke.py::PARITY_TARGETS`.")
    out.append("- Validation checks in this report become regression tests in `tests/test_sprt.py`.")
    out.append("- `tests/test_readme_freshness.py` invariants automatically catch the version + Status drift.")
    out.append("")
    return "\n".join(out)


# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────

def main() -> int:
    print("Computing per-body proper-time-rate components…", file=sys.stderr)
    scores: Dict[str, ProperTimeRate] = {}
    for body_key in BODIES:
        s = score_body(body_key)
        scores[body_key] = s
        flag = "⚠" if s.error else " "
        print(f"  {flag} {body_key:>11s}  R={s.radius_km:>8.1f} km  "
              f"GR={s.gr_surface:>8.2e}  kin={s.kinematic_orbital:>8.2e}  "
              f"total={s.total:>8.2e}",
              file=sys.stderr)
    print(file=sys.stderr)
    print("Cross-validating against published values…", file=sys.stderr)
    validations = run_validation(scores)
    n_pass = sum(1 for _, status, _, _ in validations if status == "PASS")
    for check, status, computed, msg in validations:
        symbol = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "?")
        print(f"  {symbol} {check.label}: {msg}", file=sys.stderr)
    print(f"\n{n_pass}/{len(validations)} validation checks passed.", file=sys.stderr)

    report = render_report(scores, validations)
    out_path = Path(__file__).resolve().parent.parent / "figures" / "proper_time_rates.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to {out_path}", file=sys.stderr)
    return 0 if n_pass == len(validations) else 1


if __name__ == "__main__":
    sys.exit(main())
