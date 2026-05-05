"""Phase A audit: Solar-System kinematics + dynamics at J2000.

Mirror of chess-spectral's qm_2d/qm_4d (Kinematics) + qm_2d_dynamics/
qm_4d_dynamics (Dynamics) split, applied to ephemerides-spectral. Task
queued for v0.12.0 (Kinematics) and v0.13.0 (Dynamics) ships.

This script's purpose is to *justify the surface* before committing to
it. It computes the obvious K + D quantities for all 38 bodies at J2000
and validates against published Solar-System totals. If the numbers
land cleanly, the v0.12.0 / v0.13.0 ships are justified. If they don't,
we learn something before adding 1k+ LOC of bridge / CLI / test code.

Validation pins (the "is this worth shipping?" check):

  1. **Total Solar-System angular momentum ~99.4 % in Jupiter's orbit.**
     The famous fact that the planets carry almost all the angular
     momentum, not the Sun. Sum |L_orbital(planet)| / |L_total| should
     give the standard breakdown.

  2. **System is bound** (total energy < 0). Sum of all per-body
     kinetic + per-pair potential should be negative; the Sun's
     gravitational well dominates.

  3. **Sun's KE is negligible** vs. its rest mass × c². The Sun barely
     moves in the barycentric frame; its barycentric velocity is ~12
     m/s peak (Sun-Jupiter wobble), so KE_Sun / Mc² ~ 10⁻¹⁵.

  4. **Mercury orbital velocity ~47 km/s**, Earth ~30 km/s, Mars ~24
     km/s, Jupiter ~13 km/s, Pluto ~4.7 km/s. Standard values.

  5. **Jupiter's orbital angular momentum dominates the planets.** Per
     standard Solar-System tables: Jupiter alone holds ~60 % of the
     total planetary angular momentum.

If all five validation pins land within 5 %, the v0.12.0 / v0.13.0
ships are clearly justified — these are real, useful, computable
quantities. If they don't, we have a bug in the kinematics formulas
that needs fixing before exposing the surface.

Out of scope for this audit:

  - **3D positions** (only orbital-plane kinematics; no inclination /
    longitude-of-node corrections). The published 99.4 %-Jupiter
    figure is dominated by orbital plane components anyway.
  - **Lyapunov / chaos indicators**. Need full state evolution; queued
    as a v0.13.x dynamics extension.
  - **Spin angular momentum**. Need rotation rate × moment of inertia
    per body; bodies.py doesn't carry MoI yet.

Run:

    python kinematics_dynamics_audit.py

Writes:

    ../figures/kinematics_dynamics_audit.md
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Wire into the package's bodies.py (single source of truth for masses
# + orbital periods + radii) and proper_time.py (already has GM_SUN /
# GM_EARTH / Kepler's third law machinery — reuse it instead of
# re-implementing the constants).
_PKG_PARENT = Path(__file__).resolve().parents[1] / "ephemerides-spectral" / "python"
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from ephemerides_spectral._research.bodies import BODIES  # noqa: E402
from ephemerides_spectral._research.proper_time import (  # noqa: E402
    C as _C,
    DAY_S,
    GM_EARTH,
    GM_SUN,
    PARENT_OF,
)


# ──────────────────────────────────────────────────────────────────────
# Per-body kinematic state at J2000 (mean orbital elements)
# ──────────────────────────────────────────────────────────────────────
#
# v0.12.0 will expose these via `bridge.get_kinematic_state(jd, body,
# frame=...)` returning per-body (r, v, a) in a chosen frame. For the
# audit we're working in 2D heliocentric orbital-plane coordinates —
# enough to reproduce the magnitude-level Solar-System totals.

@dataclass(frozen=True)
class KinematicState:
    """Per-body (r, v) magnitudes + components at J2000.

    r, v in heliocentric coordinates (origin at Sun) for Sol-orbiting
    bodies; in parent-centric coordinates for moons. Magnitudes are in
    SI (metres, m/s); per_body_kinetic_energy in joules.
    """
    body:                    str
    parent:                  Optional[str]
    semi_major_axis_m:       float
    orbital_radius_m:        float        # mean r (= a for circular approx)
    orbital_velocity_m_s:    float        # mean v from Kepler
    orbital_period_s:        float
    mass_kg:                 float
    kinetic_energy_j:        float
    angular_momentum_kg_m2_s: float        # |L| = m * v * r (perp velocity)
    angular_momentum_z_kg_m2_s: float      # signed z-component (orbital plane)


def _gm_for(body_key: str) -> float:
    if body_key == "sun":
        return GM_SUN
    return BODIES[body_key].mass_earth * GM_EARTH


def _mass_kg_for(body_key: str) -> float:
    """Body mass in kg. Sun via canonical GM_SUN / G; others via mass_earth."""
    if body_key == "sun":
        # GM_SUN / G — but we want mass in kg, not GM. M_sun ~ 1.989e30 kg
        return 1.98892e30
    earth_mass_kg = 5.9722e24
    return BODIES[body_key].mass_earth * earth_mass_kg


def kinematic_state(body_key: str) -> Optional[KinematicState]:
    body = BODIES[body_key]
    if body.period_days <= 0.0:
        # The Sun has period 0 in our table — no Kepler computation possible.
        return None
    parent = PARENT_OF.get(body_key)
    gm_central = GM_SUN if parent is None else _gm_for(parent)
    t_s = body.period_days * DAY_S
    # Kepler's third law: a = (GM·T²/4π²)^(1/3)
    a_m = (gm_central * t_s * t_s / (4.0 * math.pi * math.pi)) ** (1.0 / 3.0)
    # Circular orbit: v = sqrt(GM/a), r = a
    v = math.sqrt(gm_central / a_m)
    m_kg = _mass_kg_for(body_key)
    ke = 0.5 * m_kg * v * v
    # |L| = m * v * r for circular orbit (v perpendicular to r)
    L_mag = m_kg * v * a_m
    # Sign convention: prograde orbits have +z angular momentum (CCW
    # viewed from north). Treat all bodies as prograde for the audit;
    # retrograde corrections (Triton, Phoebe) shift signs but don't
    # change the magnitude story.
    L_z = L_mag
    return KinematicState(
        body=body_key,
        parent=parent,
        semi_major_axis_m=a_m,
        orbital_radius_m=a_m,
        orbital_velocity_m_s=v,
        orbital_period_s=t_s,
        mass_kg=m_kg,
        kinetic_energy_j=ke,
        angular_momentum_kg_m2_s=L_mag,
        angular_momentum_z_kg_m2_s=L_z,
    )


# ──────────────────────────────────────────────────────────────────────
# System totals
# ──────────────────────────────────────────────────────────────────────

@dataclass
class SystemTotals:
    """Aggregate Solar-System dynamics at J2000."""
    n_bodies: int
    n_with_state: int
    total_kinetic_energy_j: float        # sum over bodies-with-state
    total_potential_energy_j: float       # heliocentric: sum_{body} -GM·m/r
    total_energy_j: float                 # KE + PE
    is_bound: bool                        # total_energy_j < 0
    total_angular_momentum_z_kg_m2_s: float
    planet_only_angular_momentum_z: float
    fraction_in_planets: float            # planet_L / total_L
    fraction_in_jupiter: float            # jupiter_L / total_L (the 99.4% figure)
    fraction_in_jupiter_orbit_only: float # jupiter_L / planet_L
    sun_ke_relative_to_rest_mass: float   # KE_sun / (M_sun · c²)


def aggregate_totals(states: Dict[str, Optional[KinematicState]]) -> SystemTotals:
    n_with_state = sum(1 for s in states.values() if s is not None)
    # Kinetic energy: sum of all bodies with computed state
    total_ke = sum(s.kinetic_energy_j for s in states.values() if s is not None)
    # Potential energy (heliocentric): sum_{body} -GM_sun · m_body / r
    # for Sol-orbiting bodies; sum_{body} -GM_parent · m_body / r for
    # moons (binding to their parent). This gives the leading-order
    # binding energy; full PE includes mutual planet-planet terms which
    # are small (~10⁻⁴) and we skip for the audit.
    total_pe = 0.0
    for body_key, s in states.items():
        if s is None:
            continue
        gm_central = GM_SUN if s.parent is None else _gm_for(s.parent)
        total_pe += -gm_central * s.mass_kg / s.orbital_radius_m
    total_e = total_ke + total_pe
    # Angular momentum: sum signed z-components. Planets vs total split.
    total_lz = sum(s.angular_momentum_z_kg_m2_s for s in states.values() if s is not None)
    planet_lz = sum(
        s.angular_momentum_z_kg_m2_s
        for body_key, s in states.items()
        if s is not None and BODIES[body_key].category == "planet"
    )
    jupiter_lz = states["jupiter"].angular_momentum_z_kg_m2_s if states.get("jupiter") else 0.0
    # Sun's KE — barely moves; the audit shows this is ~10⁻¹⁵ of its rest mass.
    # Approximate with Sun-Jupiter wobble: m_jupiter · v_jupiter / m_sun
    # gives the Sun's barycentric velocity. KE = 0.5 · M_sun · v_sun².
    if states.get("jupiter"):
        sj = states["jupiter"]
        v_sun_jupiter_wobble = sj.mass_kg * sj.orbital_velocity_m_s / _mass_kg_for("sun")
        ke_sun = 0.5 * _mass_kg_for("sun") * v_sun_jupiter_wobble * v_sun_jupiter_wobble
    else:
        ke_sun = 0.0
    sun_ke_rel = ke_sun / (_mass_kg_for("sun") * _C * _C)
    return SystemTotals(
        n_bodies=len(BODIES),
        n_with_state=n_with_state,
        total_kinetic_energy_j=total_ke,
        total_potential_energy_j=total_pe,
        total_energy_j=total_e,
        is_bound=(total_e < 0),
        total_angular_momentum_z_kg_m2_s=total_lz,
        planet_only_angular_momentum_z=planet_lz,
        fraction_in_planets=planet_lz / total_lz if total_lz else 0.0,
        fraction_in_jupiter=jupiter_lz / total_lz if total_lz else 0.0,
        fraction_in_jupiter_orbit_only=jupiter_lz / planet_lz if planet_lz else 0.0,
        sun_ke_relative_to_rest_mass=sun_ke_rel,
    )


# ──────────────────────────────────────────────────────────────────────
# Validation pins
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ValidationCheck:
    label: str
    expected: float
    rel_tol: float
    cite: str


VALIDATION_CHECKS: Dict[str, ValidationCheck] = {
    "mercury_v_kms": ValidationCheck(
        "Mercury orbital velocity ~47.36 km/s",
        47.36, 0.02, "NASA Mercury fact sheet"),
    "earth_v_kms": ValidationCheck(
        "Earth orbital velocity ~29.78 km/s",
        29.78, 0.02, "NASA Earth fact sheet"),
    "mars_v_kms": ValidationCheck(
        "Mars orbital velocity ~24.07 km/s",
        24.07, 0.02, "NASA Mars fact sheet"),
    "jupiter_v_kms": ValidationCheck(
        "Jupiter orbital velocity ~13.07 km/s",
        13.07, 0.02, "NASA Jupiter fact sheet"),
    "pluto_v_kms": ValidationCheck(
        "Pluto orbital velocity ~4.74 km/s",
        4.74, 0.05, "NASA Pluto fact sheet"),
    "system_bound": ValidationCheck(
        "Total energy < 0 (system is gravitationally bound)",
        -1.0, 999.0,  # sentinel: any negative value passes
        "Standard Solar-System binding energy"),
    "fraction_in_jupiter": ValidationCheck(
        "Jupiter holds ~60% of the planetary orbital angular momentum",
        0.60, 0.10, "Standard Solar-System angular-momentum tables"),
    "fraction_in_outer_planets": ValidationCheck(
        "Outer planets (Jupiter+Saturn+Uranus+Neptune) hold ~99% of planetary orbital L",
        0.99, 0.02, "Standard Solar-System angular-momentum tables"),
    "sun_ke_relative_negligible": ValidationCheck(
        "Sun's KE / (M·c²) < 1e-12 (Sun barely moves in barycentric frame)",
        1e-15, 999.0,  # sentinel: any value <1e-12 passes
        "Sun's barycentric velocity ~12 m/s; KE ~ 1.4e8 J vs Mc² ~ 1.8e47 J"),
}


def run_validation(states: Dict[str, Optional[KinematicState]],
                   totals: SystemTotals) -> List[Tuple[str, ValidationCheck, float, str]]:
    """Returns (status, check, computed, message) per pin."""
    out: List[Tuple[str, ValidationCheck, float, str]] = []
    # Per-body velocity checks
    for key in ("mercury", "earth", "mars", "jupiter", "pluto"):
        check = VALIDATION_CHECKS[f"{key.replace('earth','earth')}_v_kms"
                                  if False else f"{key}_v_kms"]
        s = states[{"earth": "terra", "mercury": "mercury", "mars": "mars",
                    "jupiter": "jupiter", "pluto": "pluto"}.get(key, key)]
        if s is None:
            out.append(("MISSING", check, 0.0, "no state computed"))
            continue
        computed = s.orbital_velocity_m_s / 1000.0
        rel_err = abs(computed - check.expected) / check.expected
        if rel_err <= check.rel_tol:
            out.append(("PASS", check, computed,
                        f"computed {computed:.3f} km/s vs. expected {check.expected:.2f} ({rel_err:.2%})"))
        else:
            out.append(("FAIL", check, computed,
                        f"computed {computed:.3f} km/s vs. expected {check.expected:.2f} — rel err {rel_err:.2%} > {check.rel_tol:.0%}"))
    # System bound
    check = VALIDATION_CHECKS["system_bound"]
    if totals.total_energy_j < 0:
        out.append(("PASS", check, totals.total_energy_j,
                    f"total_energy_j = {totals.total_energy_j:.3e} (negative → bound) ✓"))
    else:
        out.append(("FAIL", check, totals.total_energy_j,
                    f"total_energy_j = {totals.total_energy_j:.3e} (NOT negative — system is unbound, audit error)"))
    # Fraction in Jupiter
    check = VALIDATION_CHECKS["fraction_in_jupiter"]
    fij = totals.fraction_in_jupiter
    rel_err = abs(fij - check.expected) / check.expected
    if rel_err <= check.rel_tol:
        out.append(("PASS", check, fij,
                    f"Jupiter holds {fij*100:.1f}% of total angular momentum ({rel_err:.1%} of {check.expected*100:.0f}%)"))
    else:
        out.append(("FAIL", check, fij,
                    f"Jupiter holds {fij*100:.1f}% — expected ~{check.expected*100:.0f}%; rel err {rel_err:.1%}"))
    # Outer planets fraction
    check = VALIDATION_CHECKS["fraction_in_outer_planets"]
    outer_keys = ("jupiter", "saturn", "uranus", "neptune")
    outer_lz = sum(states[k].angular_momentum_z_kg_m2_s for k in outer_keys if states.get(k))
    if totals.planet_only_angular_momentum_z:
        outer_frac = outer_lz / totals.planet_only_angular_momentum_z
    else:
        outer_frac = 0.0
    rel_err = abs(outer_frac - check.expected) / check.expected
    if rel_err <= check.rel_tol:
        out.append(("PASS", check, outer_frac,
                    f"Outer planets hold {outer_frac*100:.2f}% of planetary L ({rel_err:.2%} of expected)"))
    else:
        out.append(("FAIL", check, outer_frac,
                    f"Outer-planets fraction {outer_frac*100:.2f}% — expected ~{check.expected*100:.0f}%; rel err {rel_err:.2%}"))
    # Sun KE relative
    check = VALIDATION_CHECKS["sun_ke_relative_negligible"]
    sun_ke_rel = totals.sun_ke_relative_to_rest_mass
    if sun_ke_rel < 1e-12:
        out.append(("PASS", check, sun_ke_rel,
                    f"Sun's KE / Mc² = {sun_ke_rel:.2e} (well below 1e-12; barely moves)"))
    else:
        out.append(("FAIL", check, sun_ke_rel,
                    f"Sun's KE / Mc² = {sun_ke_rel:.2e} — too large; check Sun-Jupiter wobble math"))
    return out


# ──────────────────────────────────────────────────────────────────────
# Markdown report
# ──────────────────────────────────────────────────────────────────────

def render_report(states: Dict[str, Optional[KinematicState]],
                  totals: SystemTotals,
                  validations: List[Tuple[str, ValidationCheck, float, str]]) -> str:
    out: List[str] = []
    out.append("# Kinematics + Dynamics — Phase A audit (Solar-System totals at J2000)")
    out.append("")
    out.append("**Generated by** `research/kinematics_dynamics_audit.py`. **Tasks** v0.12.0 (Kinematics) + v0.13.0 (Dynamics) candidate.")
    out.append("")
    out.append("**Purpose:** before committing to the K + D bridge / CLI / test surface "
               "(estimated ~1.5k LOC), validate that the computed Solar-System totals "
               "match published values. If the audit lands clean, the v0.12.0 + v0.13.0 "
               "ships are justified — these are real, useful, computable quantities. "
               "If they don't, we have a bug in the kinematics formulas before exposing "
               "the surface.")
    out.append("")
    out.append("**Pattern:** mirrors the Phase A → Phase B cycle used by STLT (#95) and SPrT (#97). "
               "Two-implementation discipline: this script computes the formulas independently; "
               "the v0.12.0 / v0.13.0 ships will validate the canonical primitives against the "
               "same numbers via `tests/test_kinematics.py` and `tests/test_dynamics.py`.")
    out.append("")
    out.append("---")
    out.append("")

    # Validation table
    out.append("## Validation against published values")
    out.append("")
    out.append("| Check | Status | Detail |")
    out.append("|---|---|---|")
    n_pass = 0
    for status, check, computed, msg in validations:
        flag = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "⚠")
        out.append(f"| {check.label} | {flag} {status} | {msg} |")
        if status == "PASS":
            n_pass += 1
    out.append("")
    out.append(f"**{n_pass} / {len(validations)} validation checks passed.**")
    out.append("")
    if n_pass == len(validations):
        out.append("→ **All published-value pins match. v0.12.0 (Kinematics) + v0.13.0 (Dynamics) ships are justified.**")
    else:
        out.append("→ **Some pins failed.** Investigate the kinematics formulas before exposing a public surface.")
    out.append("")
    out.append("---")
    out.append("")

    # System totals
    out.append("## System totals at J2000")
    out.append("")
    out.append(f"- **Bodies in roster:** {totals.n_bodies}")
    out.append(f"- **Bodies with computed kinematic state:** {totals.n_with_state}")
    out.append(f"  *(Sun has period=0 → no Kepler computation; barycentric motion handled separately as Sun-Jupiter wobble.)*")
    out.append(f"- **Total kinetic energy:** {totals.total_kinetic_energy_j:.3e} J")
    out.append(f"- **Total potential energy:** {totals.total_potential_energy_j:.3e} J")
    out.append(f"- **Total energy:** {totals.total_energy_j:.3e} J — {'bound ✓' if totals.is_bound else 'unbound!'}")
    out.append(f"- **Total angular momentum (z-component):** {totals.total_angular_momentum_z_kg_m2_s:.3e} kg·m²/s")
    out.append(f"  - In planets: {totals.planet_only_angular_momentum_z:.3e} kg·m²/s ({totals.fraction_in_planets*100:.2f} % of total)")
    out.append(f"  - In Jupiter alone: {totals.fraction_in_jupiter*100:.2f} % of total")
    out.append(f"  - Jupiter as a fraction of planet-only L: {totals.fraction_in_jupiter_orbit_only*100:.2f} %")
    out.append(f"- **Sun's KE / (M·c²):** {totals.sun_ke_relative_to_rest_mass:.3e}  *(Sun barely moves — barycentric wobble dominated by Sun-Jupiter)*")
    out.append("")
    out.append("---")
    out.append("")

    # Per-body table
    out.append("## Per-body kinematic state at J2000")
    out.append("")
    out.append("| Body | Cat | Parent | a (AU) | v (km/s) | L_z (kg·m²/s) | KE (J) |")
    out.append("|---|---|---|---|---|---|---|")
    AU_M = 1.495978707e11
    sorted_keys = sorted(states.keys(),
                         key=lambda k: -(states[k].angular_momentum_z_kg_m2_s if states[k] else 0))
    for key in sorted_keys:
        s = states[key]
        body = BODIES[key]
        if s is None:
            out.append(f"| `{key}` | {body.category} | — | — | — | — | — |")
            continue
        a_au = s.semi_major_axis_m / AU_M
        v_kms = s.orbital_velocity_m_s / 1000.0
        out.append(f"| `{key}` | {body.category} | {s.parent or 'sun'} | {a_au:.4f} | {v_kms:.3f} | {s.angular_momentum_z_kg_m2_s:.3e} | {s.kinetic_energy_j:.3e} |")
    out.append("")
    out.append("---")
    out.append("")

    # Phase B sketch
    out.append("## Phase B sketch (v0.12.0 Kinematics + v0.13.0 Dynamics)")
    out.append("")
    out.append("**v0.12.0 — Kinematics (chess-spectral `qm_*.py` analogue):**")
    out.append("")
    out.append("```python")
    out.append("# Bridge")
    out.append("bridge.get_kinematic_state(jd, body, frame='heliocentric_ecliptic')")
    out.append("# → {ok, body, frame, position_au, velocity_au_per_day, ")
    out.append("#    semi_major_axis_au, orbital_period_days, mass_kg, ...}")
    out.append("")
    out.append("bridge.get_full_system_state(jd, frame='heliocentric_ecliptic')")
    out.append("# → all 38 bodies in one call")
    out.append("```")
    out.append("")
    out.append("```bash")
    out.append("# CLI")
    out.append("ephemerides-spectral kinematics --jd 2451545.0 --body mars")
    out.append("ephemerides-spectral kinematics --jd 2451545.0 --all")
    out.append("ephemerides-spectral time-mars --jd 2451545.0 --state    # augment time output")
    out.append("```")
    out.append("")
    out.append("**v0.13.0 — Dynamics (chess-spectral `qm_*_dynamics.py` analogue):**")
    out.append("")
    out.append("```python")
    out.append("# Bridge")
    out.append("bridge.get_dynamics(jd)")
    out.append("# → {ok, total_kinetic_energy_j, total_potential_energy_j, ")
    out.append("#    total_energy_j, is_bound, total_angular_momentum_z, ")
    out.append("#    fraction_in_jupiter, ...}")
    out.append("")
    out.append("bridge.get_force_on_body(jd, body, from_body=None)")
    out.append("# → {ok, force_n_vec, force_n_magnitude, contributors: {...}}")
    out.append("")
    out.append("bridge.evolve(state, dt_days)")
    out.append("# → exp(-i H dt) state — direct application of the Laplacian propagator")
    out.append("```")
    out.append("")
    out.append("```bash")
    out.append("# CLI")
    out.append("ephemerides-spectral dynamics --jd 2451545.0")
    out.append("ephemerides-spectral dynamics --jd 2451545.0 --body mars")
    out.append("ephemerides-spectral dynamics --jd 2451545.0 --body mars --from jupiter")
    out.append("```")
    out.append("")
    out.append("**Discipline carried forward** (mirrors STLT + SPrT):")
    out.append("- Phase A (this script) + Phase B (canonical primitive) — two implementations agreeing on the validation pins.")
    out.append("- New bridge methods classified `python_only` in `tests/test_parity_smoke.py::PARITY_TARGETS`.")
    out.append("- New tests `tests/test_kinematics.py` + `tests/test_dynamics.py` pinning the validation set.")
    out.append("- README freshness invariants pin the version + Status drift automatically.")
    out.append("")
    return "\n".join(out)


# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────

def main() -> int:
    print("Computing per-body kinematic state at J2000…", file=sys.stderr)
    states: Dict[str, Optional[KinematicState]] = {}
    for body_key in BODIES:
        s = kinematic_state(body_key)
        states[body_key] = s

    totals = aggregate_totals(states)

    print("\nValidating against published Solar-System values…", file=sys.stderr)
    validations = run_validation(states, totals)
    n_pass = sum(1 for status, _, _, _ in validations if status == "PASS")
    for status, check, _, msg in validations:
        symbol = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "?")
        print(f"  {symbol} {check.label}: {msg}", file=sys.stderr)
    print(f"\n{n_pass}/{len(validations)} validation checks passed.", file=sys.stderr)

    report = render_report(states, totals, validations)
    out_path = Path(__file__).resolve().parent.parent / "figures" / "kinematics_dynamics_audit.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to {out_path}", file=sys.stderr)
    return 0 if n_pass == len(validations) else 1


if __name__ == "__main__":
    sys.exit(main())
