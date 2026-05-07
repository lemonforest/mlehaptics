"""Always-on C/Python parity smoke test.

Every encoder-touching bridge method must have a C equivalent.

This test is the **scaffolding** that pins that discipline. The
``PARITY_TARGETS`` table below is the spec: every Python bridge
method gets one entry classifying its parity status. Adding a new
encoder-touching method requires either:

  * a paired C entry point (preferred — produces matching output via
    ``backend="c"``), or
  * an explicit ``python_only`` entry justifying why C parity isn't
    needed (pure-Python time scales, validation helpers, etc.)

Status values
=============

  ``parity``       both backends present; outputs must match within
                   tolerance. Test runs both and asserts equality.
  ``python_only``  Python-only by design (pure-Python formula,
                   validation, etc.). Test asserts the Python path
                   works; no C path expected.
  ``tier1_skip``   C port pending in the Tier 1 parity ship. Test
                   skips with the tier marker; flips to ``parity``
                   when the C entry point lands.
  ``tier2_skip``   C port pending in the Tier 2 (HD-state)
                   parity ship. Same flow.

Discipline
==========

  * **Never delete** an entry from this table. Entries flip status as
    work lands; their absence would lose the parity guarantee.
  * **Never silently downgrade** a passing ``parity`` entry to
    ``tier{1,2}_skip``. That hides real regressions. If parity
    breaks, fix the underlying drift, don't reclassify.
  * Skips render in CI as "S" (single-letter), so a glance at the
    pytest summary line shows how many parity targets are still
    pending.

Spec drift detection
====================

The ``test_parity_smoke_spec_covers_bridge_surface`` smoke test
walks every public function in ``ephemerides_spectral.bridge`` and
asserts that the function name appears either in PARITY_TARGETS or
in the explicit allowlist of non-parity-relevant names (validators,
metadata getters, etc.). If you add a new bridge method, this test
forces you to declare its parity status here before CI passes.
"""

from __future__ import annotations

import inspect
import math
from typing import Callable, Dict, Optional

import pytest

from ephemerides_spectral import _native_bip, bridge


# ─────────────────────────────────────────────────────────────────────
# PARITY_TARGETS — the spec.
# ─────────────────────────────────────────────────────────────────────
#
# Each entry maps a bridge function name to a dict describing how to
# exercise it and whether it has a C twin.
#
# Schema:
#   {
#     "status":    one of {"parity", "python_only", "tier1_skip", "tier2_skip"},
#     "kwargs_py": dict of kwargs to call the Python path with,
#     "kwargs_c":  dict for the C path (typically same as kwargs_py
#                  with backend="c" added; only meaningful for
#                  status="parity"),
#     "compare":   callable(py_result, c_result) -> bool, default is
#                  exact-equality on the dict; override for float
#                  tolerance ops,
#     "tier":      Tier number (1, 2) for tier-N-skip statuses; used
#                  in the skip reason,
#     "rationale": one-line explanation for python_only entries,
#   }
#
PARITY_TARGETS: Dict[str, Dict] = {
    # ── Encoder hot path (already at full byte-identical parity) ──────
    "get_system_state": {
        "status": "parity",
        "kwargs_py": {"jd_tdb": 2451545.0, "backend": "bip"},
        "kwargs_c": {"jd_tdb": 2451545.0, "backend": "c"},
        # phases_uint32 is the byte-identical 38 × uint32 state.
        # `backend` differs (literal "bip" vs "c") which is correct;
        # only compare the encoded state.
        "compare": lambda a, b: a["phases_uint32"] == b["phases_uint32"],
    },
    # ── Tier 1 ports (v0.6.0): C twin shipped ────────────────────────
    # ── v0.8.1 ITN pathway (find-tubes): Python BIP only; C twin queued ─
    "find_itn_pathways": {
        "status": "tier1_skip",
        "tier": 1,
        "kwargs_py": {"jd_lo": 2451545.0, "jd_hi": 2451545.0 + 5*365.25,
                      "departure": "terra", "target": "mars",
                      "threshold": 0.05},
    },
    # ── v0.17.0 multi-leg ITN chain search (find-chains): Dijkstra-style
    # graph search over (body, epoch) state space. Pure-Python addition
    # built on top of find_itn_pathways. No C twin planned -- the
    # priority-queue search is structurally Pythonic and bound by the
    # same closed-form synodic enumeration as find_itn_pathways.
    "find_itn_chains": {
        "status": "python_only",
        "kwargs_py": {"jd_lo": 2451545.0, "jd_hi": 2451545.0 + 5*365.25,
                      "departure": "terra", "target": "mars",
                      "intermediates": []},
    },
    # ── v0.18.0 Body Architecture (resonance-weighted gateway-graph
    # Laplacian Fiedler partition; inner/outer system classification).
    # Pure-Python; no C twin planned -- the eigendecomposition runs on
    # numpy.linalg.eigh and the call cost is microseconds, well below
    # any threshold where a C twin would be useful. See notebook §13.8.
    "body_architecture": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.19.0 Sol Electromagnetic Instrument (state-at-epoch query
    # surface for the EM sector). Per notebook §16.9.1 the EM clocks
    # don't form a low-order rational lattice with orbital periods, so
    # the cyclic-group encoder discipline doesn't transplant. Three
    # bridge surfaces, all pure-Python lookups + linear rotation phase
    # advance; no C twin makes sense.
    "get_em_state": {
        "status": "python_only",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "list_em_couplings": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "em_architecture": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.20.0 Sol Geodetic Catalog (state-lookup query surface for
    # the solid-body geodetic stack: gravity multipoles + topography +
    # interior). Per notebook §17.4.1 the rhythm-mismatch finding
    # generalises across solid-body geodesy alongside magnetic
    # multipoles and fluid-envelope channels — solid-body geodetic
    # observables are static parameters with no native rhythm, so the
    # cyclic-group encoder discipline does not transplant. Three bridge
    # surfaces, all pure-Python static lookups; no C twin makes sense.
    "get_geodetic_state": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_geodetic_models": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "geodetic_architecture": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.20.1 Sol Magnetic Multipole Catalog (state-lookup query
    # surface for the per-body internal-field roster + Earth crustal
    # + Sun synoptic pointer). Per notebook §17.4.1 the rhythm-mismatch
    # finding generalises across magnetic multipoles alongside solid-
    # body geodesy and fluid-envelope channels — internal-field
    # Schmidt coefficients are static at their epoch, so the cyclic-
    # group encoder discipline does not transplant. Five bridge
    # surfaces, all pure-Python static lookups + dipole synthesis;
    # no C twin makes sense.
    "get_magnetic_multipoles": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "evaluate_magnetic_field": {
        "status": "python_only",
        "kwargs_py": {
            "body": "terra", "r_km": 7000.0,
            "lat_deg": 0.0, "lon_deg": 0.0,
        },
    },
    "get_solar_synoptic_state": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_magnetic_multipoles": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "magnetic_architecture": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.20.2 Sol Fluid Instrument (state-lookup query surface for
    # the fluid envelope: climatology + archive index + state-at-epoch
    # coverage triage). Per notebook §17.4.1 the rhythm-mismatch finding
    # generalises across fluid-envelope channels alongside solid-body
    # geodesy and magnetic multipoles. Three bridge surfaces, all pure-
    # Python static lookups (no live HTTP calls); no C twin makes sense.
    "get_fluid_state": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_fluid_archives": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "fluid_architecture": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.0 Sol Spherical Harmonic Catalog (unification refactor —
    # NOT a new data store; reuses v0.20.0 geodetic_catalog_data +
    # v0.20.1 magnetic_multipole_catalog_data underneath). Three new
    # bridge surfaces, all pure-Python query / refactor / arithmetic
    # helpers; no C twin makes sense. Per notebook §17.4.2.
    "get_spherical_harmonics": {
        "status": "python_only",
        "kwargs_py": {"body": "terra"},
    },
    "list_spherical_harmonic_models": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "convert_spherical_harmonic_normalisation": {
        "status": "python_only",
        "kwargs_py": {
            "coefficient_value": 1.0, "n": 1, "m": 0,
            "from_convention": "Schmidt-quasi-norm",
            "to_convention": "4pi-Stokes",
        },
    },
    # ── v0.21.1 Sol Topography-Gravity Admittance Catalog (first
    # cross-channel coupling surface in the §17.4.2 v0.21.x sequence;
    # 5-body roster: terra/luna/mars/mercury/venus). Pure-Python static
    # lookup of published Z(n) summaries; no C twin makes sense.
    "get_topography_gravity_admittance": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_admittance_spectra": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.2 Sol Dynamo Region Catalog (second cross-channel
    # coupling surface; magnetic-multipole-derived dynamo radii for
    # 5 bodies). Pure-Python static lookup; no C twin makes sense.
    "get_dynamo_region": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_dynamo_regions": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.3 Sol Orographic Forcing Catalog (third cross-channel
    # coupling surface; topography → atmospheric standing waves; 4-body
    # roster). Pure-Python static lookup; no C twin makes sense.
    "get_orographic_forcing": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_orographic_forcings": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.4 Sol Rotational Constraint Catalog (fourth cross-channel
    # coupling surface; interior <-> rotation; 7-body roster). Pure-
    # Python static lookup; no C twin makes sense.
    "get_rotational_constraint": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_rotational_constraints": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.5 Sol Auroral Coupling Catalog (fifth cross-channel
    # coupling surface; magnetic <-> atmosphere via aurorae; 6-body
    # roster). Pure-Python static lookup; no C twin makes sense.
    "get_auroral_coupling": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_auroral_couplings": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.6 Sol Tidal Migration Catalog (sixth cross-channel
    # coupling surface; tidal dissipation <-> orbital migration; 6-pair
    # roster). Pure-Python static lookup; no C twin makes sense.
    "get_tidal_migration": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_tidal_migrations": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.7 Sol Atmospheric Escape Catalog (seventh cross-channel
    # coupling surface; atmospheric escape <-> magnetic-field shielding;
    # 6-body roster). Pure-Python static lookup; no C twin makes sense.
    "get_atmospheric_escape": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_atmospheric_escapes": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.8 Sol Heat Flow Catalog (eighth cross-channel coupling
    # surface; heat flow <-> tidal heating energy budget; 6-body
    # roster). Pure-Python static lookup; no C twin makes sense.
    "get_heat_flow": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_heat_flows": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.9 Sol Volcanic Outgassing Catalog (ninth cross-channel
    # coupling surface; volcanic outgassing <-> atmospheric composition;
    # 6-body roster). Pure-Python static lookup; no C twin makes sense.
    "get_volcanic_outgassing": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_volcanic_outgassings": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.21.10 Sol Thermal Balance Catalog (tenth cross-channel
    # coupling surface; radiative equilibrium <-> observed temperature
    # decomposition; 6-body roster). Pure-Python static lookup; no C
    # twin makes sense.
    "get_thermal_balance": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_thermal_balances": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.22.0 Trajectory + Sensing Layer A (per-body short-range
    # ballistic propagator; 7-body roster). Pure-Python; no C twin
    # planned -- propagator is RK4 with body-specific atmosphere
    # parameters from the static catalog.
    "compute_ballistic_trajectory": {
        "status": "python_only",
        "kwargs_py": {"body": "terra", "v_m_s": 700.0, "angle_deg": 45.0},
    },
    "get_ballistic_atmosphere": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_ballistic_atmospheres": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.22.0 Trajectory + Sensing Layer B (Earth ICBM 3-regime
    # propagator; boost boundary + Kepler midcourse + Allen-Eggers
    # re-entry). Pure-Python; no C twin planned.
    "compute_icbm_trajectory": {
        "status": "python_only",
        "kwargs_py": {
            "burnout_velocity_m_s": 7000.0,
            "burnout_flight_path_angle_deg": 23.0,
        },
    },
    "get_icbm_reference_profile": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_icbm_reference_profiles": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.22.0 Trajectory + Sensing Layer C(a) (sensor access:
    # SGP4 + look-angle geometry + Earth-limb occlusion). Pure-Python;
    # no C twin planned. SGP4 is an optional dep (sgp4 / Skyfield).
    "compute_visibility_geometry": {
        "status": "python_only",
        "kwargs_py": {
            "sat_ecef_m": (7178137.0, 0.0, 0.0),
            "target_lat_deg": 0.0,
            "target_lon_deg": 0.0,
        },
    },
    "compute_sgp4_state": {
        "status": "tier2_skip",  # depends on optional sgp4 install
        "tier": 2,
    },
    "get_orbital_reference": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_orbital_references": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.22.0 Trajectory + Sensing Layer C(b) (decoy
    # discrimination: BC-differential velocity separation). Pure-Python
    # closed-form (Allen-Eggers, NACA Report 1381, 1958); no C twin.
    "compute_bc_differential": {
        "status": "python_only",
        "kwargs_py": {
            "bc_heavy_kg_m2": 10000.0,
            "bc_light_kg_m2": 50.0,
        },
    },
    "compute_discrimination_altitude": {
        "status": "python_only",
        "kwargs_py": {
            "bc_heavy_kg_m2": 10000.0,
            "bc_light_kg_m2": 10.0,
        },
    },
    "get_bc_reference_class": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_bc_reference_classes": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.23.0 Sol Spin-Orbit Resonance Catalog (eleventh cross-channel
    # coupling surface; spin-orbit resonance ↔ rotation lock; 8-body
    # roster). Pure-Python static lookup; no C twin makes sense.
    "get_spin_orbit_resonance": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_spin_orbit_resonances": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.24.0 Sol Mercury Dynamical Spectrum (first per-body
    # dynamical-spectrum surface; action-angle decomposition + Le
    # Verrier/Einstein perihelion-precession contribution-by-perturber
    # decomposition). Pure-Python static lookup; no C twin makes sense.
    "get_mercury_dynamical_spectrum": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "get_mercury_precession_decomposition": {
        "status": "python_only",
        "kwargs_py": {},
    },
    "list_mercury_dynamical_spectrum": {
        "status": "python_only",
        "kwargs_py": {},
    },
    # ── v0.18.1 predict_itn_accessibility (closed-form spectral Δv
    # estimate from the §13.9 hybrid Fiedler-distance regression). Pure-
    # Python; no C twin planned -- the eigendecomposition is memoised at
    # module load on a 13×13 symmetric matrix and per-query cost is a
    # dict lookup + linear evaluation. See notebook §13.9.
    "predict_itn_accessibility": {
        "status": "python_only",
        "kwargs_py": {"departure": "terra", "target": "mars"},
    },
    "find_syzygies": {
        "status": "parity",
        "kwargs_py": {"jd_lo": 2451545.0, "jd_hi": 2451545.0 + 365.25,
                      "kind": "all", "threshold": 0.05, "backend": "bip"},
        "kwargs_c":  {"jd_lo": 2451545.0, "jd_hi": 2451545.0 + 365.25,
                      "kind": "all", "threshold": 0.05, "backend": "c"},
        # Compare candidate list (length + each entry's jd/kind/score)
        # within float tolerance. The `backend` field differs by design.
        "compare": lambda a, b: (
            a["n_candidates"] == b["n_candidates"]
            and all(
                pa["kind"] == pc["kind"]
                and abs(pa["jd_tdb"] - pc["jd_tdb"]) < 1e-9
                and abs(pa["score"] - pc["score"]) < 1e-12
                for pa, pc in zip(a["candidates"], b["candidates"])
            )
        ),
    },
    "get_breathing_modulation": {
        "status": "parity",
        "kwargs_py": {"jd_tdb": 2451545.0, "pair": ("jupiter", "saturn"),
                      "n_lobes": (5, 2), "backend": "bip"},
        "kwargs_c":  {"jd_tdb": 2451545.0, "pair": ("jupiter", "saturn"),
                      "n_lobes": (5, 2), "backend": "c"},
        # `phase_residue` + `cos_lut_q14` must be byte-identical
        # (integer ops on both sides). `modulation_factor` must agree
        # within float64 ULP.
        "compare": lambda a, b: (
            a["phase_residue"] == b["phase_residue"]
            and a["cos_lut_q14"] == b["cos_lut_q14"]
            and abs(a["modulation_factor"] - b["modulation_factor"]) < 1e-15
        ),
    },
    # ── Tier 2b ports (v0.7.0): HD pipeline in C ─────────────────────
    "get_local_view": {
        "status": "parity",
        "kwargs_py": {"jd_tdb": 2451545.0, "body": "mars",
                      "lat": 0.0, "lon": 0.0, "backend": "bip", "D": 4096},
        "kwargs_c":  {"jd_tdb": 2451545.0, "body": "mars",
                      "lat": 0.0, "lon": 0.0, "backend": "c", "D": 4096},
        # Compare interleaved state vector within float-tolerance.
        # Float32 round-off + 38-body sum accumulation gives a worst-
        # case ULP order around 1e-5; the tolerance is generous.
        "compare": lambda a, b: (
            len(a["state_interleaved_f32"]) == len(b["state_interleaved_f32"])
            and max(
                abs(x - y) for x, y in zip(
                    a["state_interleaved_f32"], b["state_interleaved_f32"]
                )
            ) < 1e-5
        ),
    },
    "get_eclipse_probability": {
        "status": "parity",
        "kwargs_py": {"jd_tdb": 2451545.0, "backend": "bip", "D": 4096},
        "kwargs_c":  {"jd_tdb": 2451545.0, "backend": "c", "D": 4096},
        "compare": lambda a, b: abs(a["probability"] - b["probability"]) < 1e-7,
    },
    # ── Pure-Python by design (no C path warranted) ──────────────────
    "get_resolution": {
        "status": "python_only",
        "rationale": "pure analytic; (body, D) → seconds-per-residue, no encoder calls",
        "kwargs_py": {"body": "terra", "D": 65536},
    },
    "get_lunar_phase": {
        "status": "python_only",
        "rationale": "fixed-period synodic + sidereal arithmetic; no encoder calls",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "jd_to_mars_time": {
        "status": "python_only",
        "rationale": "Allison & McEwen 2000 closed-form; no encoder calls",
        "kwargs_py": {"jd_utc": 2451549.5},
    },
    "mars_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_mars_time",
        "kwargs_py": {"msd": 44795.999817},
    },
    "jd_to_sol_uranian_time": {
        "status": "python_only",
        "rationale": "v0.5.4 Sol Uranian Time, sidereal-day arithmetic",
        "kwargs_py": {"jd_tdb": 2454451.0},
    },
    "sol_uranian_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_uranian_time",
        "kwargs_py": {"usd": 0.0},
    },
    # v0.8.0 Sol Symphony Times — pure-Python sidereal/solar arithmetic.
    "jd_to_sol_venus_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Venusian Time (retrograde, sidereal+solar day)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_venus_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_venus_time",
        "kwargs_py": {"vsd_solar": 0.0},
    },
    "jd_to_sol_mercury_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Mercurian Time (3:2 spin-orbit resonance)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_mercury_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_mercury_time",
        "kwargs_py": {"mer_sd_solar": 0.0},
    },
    "jd_to_sol_pluto_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Plutonian Time (Pluto-Charon system)",
        "kwargs_py": {"jd_tdb": 2457217.0},
    },
    "sol_pluto_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_pluto_time",
        "kwargs_py": {"psd": 0.0},
    },
    "jd_to_sol_sol_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Sol Time (Carrington rotation system)",
        "kwargs_py": {"jd_tdb": 2398167.4},
    },
    "sol_sol_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_sol_time",
        "kwargs_py": {"crn": 1.0},
    },
    "jd_to_sol_jovian_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Jovian Time (Jupiter System III magnetic-field rotation)",
        "kwargs_py": {"jd_tdb": 2444000.5},
    },
    "sol_jovian_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jovian_time",
        "kwargs_py": {"jsd": 0.0},
    },
    "jd_to_sol_saturnian_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Saturnian Time (Cassini-revised System III)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturnian_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturnian_time",
        "kwargs_py": {"ssd": 0.0},
    },
    "jd_to_sol_neptunian_time": {
        "status": "python_only",
        "rationale": "v0.8.0 Sol Neptunian Time (Voyager 2 System III)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_neptunian_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_neptunian_time",
        "kwargs_py": {"nsd": 0.0},
    },
    "jd_to_sol_terra_time": {
        "status": "python_only",
        "rationale": "v0.9.1 Sol Terra Time (STT) — Terra's surface clock",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_terra_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_terra_time",
        "kwargs_py": {"tsd_solar": 0.0},
    },
    "jd_to_sol_luna_time": {
        "status": "python_only",
        "rationale": "v0.9.1 Sol Luna Time (SLT) — Luna's surface clock; distinct from Sol Lunar Time (which gives synodic+sidereal phase observed from Terra)",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_luna_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_luna_time",
        "kwargs_py": {"lsd_solar": 0.0},
    },
    "jd_to_sol_terra_luna_time": {
        "status": "python_only",
        "rationale": "v0.10.0 Sol Terra-Luna Time (STLT) — anchored Lunar time using the synodic month as the natural unit (the 'Terra-Luna' in the name follows the moons-stuck-to-parent `Sol <Parent>-<Body> Time` convention). Default epoch = Meton's 432 BCE summer solstice. First Sol Time member with non-J2000 default anchor. Pure-Python time-scale formula; C twin queued.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_terra_luna_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_terra_luna_time",
        "kwargs_py": {"synodic_count": 0.0},
    },
    # v0.14.0 Sol Moon Times — Galileans (Io / Europa / Ganymede / Callisto).
    # Pure-Python time-scale formulae using each moon's sidereal period
    # from BODIES; no C twin (same status as the rest of the Sol Time
    # series). Tidally locked, so sidereal day = orbital period =
    # rotation period. See test_galilean_sol_moon_times.py.
    "jd_to_sol_jupiter_io_time": {
        "status": "python_only",
        "rationale": "v0.14.0 Sol Jupiter-Io Time (SJIT) — anchored sidereal-cycle count for Io since J2000. Pure-Python time-scale formula; C twin queued. Innermost Galilean; participates in 4:2:1 Laplace resonance with Europa + Ganymede.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_io_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_io_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_europa_time": {
        "status": "python_only",
        "rationale": "v0.14.0 Sol Jupiter-Europa Time (SJET) — anchored sidereal-cycle count for Europa since J2000. Pure-Python time-scale formula; C twin queued.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_europa_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_europa_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_ganymede_time": {
        "status": "python_only",
        "rationale": "v0.14.0 Sol Jupiter-Ganymede Time (SJGT) — anchored sidereal-cycle count for Ganymede since J2000. Pure-Python time-scale formula; C twin queued. Largest moon in the solar system.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_ganymede_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_ganymede_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_callisto_time": {
        "status": "python_only",
        "rationale": "v0.14.0 Sol Jupiter-Callisto Time (SJCT) — anchored sidereal-cycle count for Callisto since J2000. Pure-Python time-scale formula; C twin queued. Outermost Galilean; the only one NOT in the Laplace resonance.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_callisto_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_callisto_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    # v0.14.1 Sol Moon Times — Saturnians (11 moons). All same shape as
    # Galileans (anchored sidereal-cycle count from J2000); pure-Python
    # time-scale formulae using each moon's sidereal period from BODIES.
    # Abbreviations follow the v0.14.1 6-letter S<Planet2><Moon2>T pattern
    # (collision-triggered policy switch when Tethys/Titan and
    # Enceladus/Epimetheus would have collided under the v0.14.0 4-letter form).
    "jd_to_sol_saturn_mimas_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Mimas Time (SSaMiT). Innermost classical Saturnian; Mimas-Tethys 4:2 resonance opens the Cassini Division.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_mimas_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_mimas_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_enceladus_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Enceladus Time (SSaEnT). Cryovolcanic moon with subsurface ocean; Enceladus-Dione 2:1 resonance powers tidal heating.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_enceladus_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_enceladus_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_tethys_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Tethys Time (SSaTeT). Outer member of the 4:2 Mimas-Tethys resonance.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_tethys_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_tethys_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_dione_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Dione Time (SSaDiT). Outer member of the 2:1 Enceladus-Dione resonance.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_dione_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_dione_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_rhea_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Rhea Time (SSaRhT). Second-largest Saturnian; not in any major resonance.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_rhea_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_rhea_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_titan_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Titan Time (SSaTiT). Largest Saturnian; outer member of the 4:3 Titan-Hyperion resonance.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_titan_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_titan_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_hyperion_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Hyperion Time (SSaHyT). Chaotically rotating Saturnian; orbital period referenced for the cycle count (rotation phase non-trivially decoupled).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_hyperion_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_hyperion_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_iapetus_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Iapetus Time (SSaIaT). Outermost classical Saturnian; famous two-tone albedo.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_iapetus_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_iapetus_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_phoebe_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Phoebe Time (SSaPhT). Retrograde irregular Saturnian; long ~550-day orbit.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_phoebe_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_phoebe_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_janus_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Janus Time (SSaJaT). Co-orbital with Epimetheus (~4-yr horseshoe-orbit swap).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_janus_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_janus_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_epimetheus_time": {
        "status": "python_only",
        "rationale": "v0.14.1 Sol Saturn-Epimetheus Time (SSaEpT). Co-orbital with Janus (~4-yr horseshoe-orbit swap).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_epimetheus_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_epimetheus_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    # v0.14.2 Sol Moon Times — remaining 8 moons across 4 parent
    # families. Same shape as Galileans (v0.14.0) and Saturnians (v0.14.1):
    # anchored sidereal-cycle count from J2000; pure-Python time-scale
    # formulae using each moon's sidereal period from BODIES.
    "jd_to_sol_mars_phobos_time": {
        "status": "python_only",
        "rationale": "v0.14.2 Sol Mars-Phobos Time (SMaPhT). Inner Martian moon (likely captured asteroid). Sidereal period < Mars solar day → rises in the west.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_mars_phobos_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_mars_phobos_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_mars_deimos_time": {
        "status": "python_only",
        "rationale": "v0.14.2 Sol Mars-Deimos Time (SMaDeT). Outer Martian moon (likely captured asteroid). NOT in 4:1 mean-motion resonance with Phobos.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_mars_deimos_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_mars_deimos_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_metis_time": {
        "status": "python_only",
        "rationale": "v0.14.2 Sol Jupiter-Metis Time (SJuMeT). Innermost known Jovian moon; ring-shepherd of Jupiter's main ring (with Adrastea).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_metis_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_metis_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_adrastea_time": {
        "status": "python_only",
        "rationale": "v0.14.2 Sol Jupiter-Adrastea Time (SJuAdT). Second ring-shepherd of Jupiter's main ring (with Metis).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_adrastea_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_adrastea_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_amalthea_time": {
        "status": "python_only",
        "rationale": "v0.14.2 Sol Jupiter-Amalthea Time (SJuAmT). Largest Jovian inner regular (~84 km); the only one discovered before Voyager (Barnard 1892, last solar-system moon discovered visually).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_amalthea_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_amalthea_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_thebe_time": {
        "status": "python_only",
        "rationale": "v0.14.2 Sol Jupiter-Thebe Time (SJuThT). Outermost Jovian inner regular; orbits between Amalthea and Io.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_thebe_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_thebe_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_uranus_titania_time": {
        "status": "python_only",
        "rationale": "v0.14.2 Sol Uranus-Titania Time (SUrTiT). Largest Uranian moon. SUrTiT and SSaTiT (Saturn's Titan) share `Ti` moon prefix; disambiguated by parent prefix (`Ur` vs `Sa`) — exactly the v0.14.1 6-letter policy's intent.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_uranus_titania_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_uranus_titania_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_neptune_triton_time": {
        "status": "python_only",
        "rationale": "v0.14.2 Sol Neptune-Triton Time (SNeTrT). Largest Neptunian moon; RETROGRADE orbit (only large moon in solar system to do so) → captured Kuiper Belt object; tidally decaying → ring system in ~3.6 Gyr. Encoder convention: BODIES['triton'].period_days is positive (omega = +2π/P for ALL bodies regardless of orbital direction; retrograde is metadata).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_neptune_triton_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_neptune_triton_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    # v0.15.0 — remaining classical Uranian moons (Miranda/Ariel/Umbriel/Oberon)
    # complete the major-Uranian roster. Pluto-Charon adds the binary-planet
    # case (mutual tidal lock; barycentre outside Pluto). Closes task `#86`
    # for the IAU-major roster: every classical moon now has a Sol Time wrapper.
    "jd_to_sol_uranus_miranda_time": {
        "status": "python_only",
        "rationale": "v0.15.0 SUrMiT — smallest Uranian major moon (Kuiper 1948). SUrMiT vs SSaMiT disambiguation per the v0.14.1 6-letter policy.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_uranus_miranda_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_uranus_miranda_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_uranus_ariel_time": {
        "status": "python_only",
        "rationale": "v0.15.0 SUrArT — innermost classical Uranian moon (Lassell 1851). Brightest surface (highest albedo) of the Uranian moons; possible cryovolcanic resurfacing.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_uranus_ariel_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_uranus_ariel_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_uranus_umbriel_time": {
        "status": "python_only",
        "rationale": "v0.15.0 SUrUmT — second classical Uranian moon (Lassell 1851, same night as Ariel). Darkest surface (lowest albedo) of the Uranian moons.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_uranus_umbriel_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_uranus_umbriel_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_uranus_oberon_time": {
        "status": "python_only",
        "rationale": "v0.15.0 SUrObT — outermost (and second-largest) classical Uranian moon (Herschel 1787, same night as Titania). Longest sidereal period (13.463 d) of the major-Uranian roster.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_uranus_oberon_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_uranus_oberon_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_pluto_charon_time": {
        "status": "python_only",
        "rationale": "v0.15.0 SPlChT — Pluto's largest moon (Christy 1978). MUTUALLY tidally locked with Pluto (the only such 1:1:1 spin-orbit lock in the solar system). Mass ratio Charon:Pluto ≈ 0.12 — barycentre OUTSIDE Pluto, more like a binary planet than a planet-with-moon.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_pluto_charon_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_pluto_charon_time (mutual tidal lock; sidereal period = mutual rotation period)",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    # v0.16.0 — Tier-1 BODIES expansion (43 → 52). Saturnian Lagrange
    # trojans (4): first L4/L5 entries in BODIES, period IDENTICAL to
    # host moon's. Jovian irregulars (3): Himalia + Pasiphae/Sinope
    # retrogrades. Neptunian sub-graph completion (2): Proteus + Nereid.
    "jd_to_sol_saturn_telesto_time": {
        "status": "python_only",
        "rationale": "v0.16.0 SSaTeT2 — Tethys L4 trojan, period IDENTICAL to Tethys's. First invocation of v0.14.1 suffix-disambiguation policy (SSaTeT vs SSaTeT2).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_telesto_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_telesto_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_calypso_time": {
        "status": "python_only",
        "rationale": "v0.16.0 SSaCaT — Tethys L5 trojan, period IDENTICAL to Tethys's; forms L4/L5 pair with Telesto.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_calypso_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_calypso_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_helene_time": {
        "status": "python_only",
        "rationale": "v0.16.0 SSaHeT — Dione L4 trojan, period IDENTICAL to Dione's. Largest of the four Saturnian trojans (radius ~17.5 km).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_helene_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_helene_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_saturn_polydeuces_time": {
        "status": "python_only",
        "rationale": "v0.16.0 SSaPoT — Dione L5 trojan, period IDENTICAL to Dione's; forms L4/L5 pair with Helene. Smallest body in v0.16.0 ship (~1.3 km radius); wide libration amplitude (~32°).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_saturn_polydeuces_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_saturn_polydeuces_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_himalia_time": {
        "status": "python_only",
        "rationale": "v0.16.0 SJuHiT — largest Jovian irregular moon (radius ~85 km); prograde, P=250.6 d. Eponym of the Himalia group.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_himalia_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_himalia_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_pasiphae_time": {
        "status": "python_only",
        "rationale": "v0.16.0 SJuPaT — Jovian retrograde irregular (i~141°, P=743.6 d). Second retrograde marker beyond Triton. Eponym of the Pasiphae group. Encoder convention: positive period_days; retrograde-ness is metadata.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_pasiphae_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_pasiphae_time (retrograde; period encoded positive per encoder convention)",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_jupiter_sinope_time": {
        "status": "python_only",
        "rationale": "v0.16.0 SJuSiT — Jovian retrograde irregular (i~153°, P=758.9 d). Pasiphae-group member, near-resonant with Pasiphae (period ratio ~1.02).",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_jupiter_sinope_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_jupiter_sinope_time (retrograde; period encoded positive per encoder convention)",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_neptune_proteus_time": {
        "status": "python_only",
        "rationale": "v0.16.0 SNePrT — Neptune's second-largest moon (~210 km, near-spherical despite small size). Voyager 2 1989. Period 1.122 d fills sub-graph between Triton (5.88 d) and the inner-Neptunian close-packed cluster.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_neptune_proteus_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_neptune_proteus_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "jd_to_sol_neptune_nereid_time": {
        "status": "python_only",
        "rationale": "v0.16.0 SNeNeT — Neptune's third-largest moon (~170 km). Most eccentric major-moon orbit in the solar system (e=0.749). Period 360.13 d extends Neptune's low-frequency tail dramatically.",
        "kwargs_py": {"jd_tdb": 2451545.0},
    },
    "sol_neptune_nereid_time_to_jd": {
        "status": "python_only",
        "rationale": "inverse of jd_to_sol_neptune_nereid_time",
        "kwargs_py": {"sidereal_count": 0.0},
    },
    "get_proper_time_rate": {
        "status": "python_only",
        "rationale": "v0.11.0 Sol Proper Time (SPrT) — leading-order GR + orbital kinematic dilation per body. Pure-Python time-scale formula; C twin queued. The same physics as Mercury's existing 43\"/century PN diagonal correction, applied per-body.",
        "kwargs_py": {"body": "terra"},
    },
    "compare_proper_times": {
        "status": "python_only",
        "rationale": "v0.11.0 SPrT — ratio of two bodies' proper-time rates plus 'drift per Earth-year' diagnostic for human comparison.",
        "kwargs_py": {"body_a": "terra", "body_b": "mars"},
    },
    "apply_proper_correction": {
        "status": "python_only",
        "rationale": "v0.11.0 SPrT post-processor — augments a Sol Time bridge result with proper-time-corrected count fields. CLI-layer concern; tested end-to-end via test_sprt.py.",
        "kwargs_py": {"result": {"ok": True, "msd": 1000.0}, "subcommand": "time-mars"},
    },
    "get_kinematic_state": {
        "status": "python_only",
        "rationale": "v0.12.0 Sol Kinematics — per-body mean orbital state from Kepler's third law. Pure-Python time-scale formula; C twin queued. Mirrors chess-spectral's qm_*.py (kinematics) layer.",
        "kwargs_py": {"body": "mars"},
    },
    "get_full_system_state": {
        "status": "python_only",
        "rationale": "v0.12.0 Sol Kinematics — full 38-body roster + system totals (Jupiter L fraction, etc.).",
        "kwargs_py": {},
    },
    "apply_state_correction": {
        "status": "python_only",
        "rationale": "v0.12.0 Sol Kinematics post-processor — augments a Sol Time bridge result with a kinematic_state block via the CLI's --state flag. Mirrors apply_proper_correction.",
        "kwargs_py": {"result": {"ok": True, "msd": 1000.0}, "subcommand": "time-mars"},
    },
    "get_dynamics": {
        "status": "python_only",
        "rationale": "v0.13.0 Sol Dynamics — system-level KE / PE / total energy + angular momentum partitions. Pure-Python; mirrors chess-spectral's qm_*_dynamics.py *dynamics* layer.",
        "kwargs_py": {},
    },
    "get_force_between": {
        "status": "python_only",
        "rationale": "v0.13.0 Sol Dynamics — Newtonian gravitational force between two bodies. Validated against the textbook 3.54e22 N Earth-Sun figure.",
        "kwargs_py": {"body_a": "terra", "body_b": "sun"},
    },
    "get_body_energies": {
        "status": "python_only",
        "rationale": "v0.13.0 Sol Dynamics — per-body KE + PE + total energy budget.",
        "kwargs_py": {"body": "mars"},
    },
    "apply_dynamics_correction": {
        "status": "python_only",
        "rationale": "v0.13.0 Sol Dynamics post-processor — augments a Sol Time bridge result with a dynamics block (KE/PE/total_E/is_bound) via the CLI's --dynamics flag. Mirrors apply_state_correction and apply_proper_correction.",
        "kwargs_py": {"result": {"ok": True, "msd": 1000.0}, "subcommand": "time-mars"},
    },
    "get_natural_resonance_group": {
        "status": "python_only",
        "rationale": "metadata about the RESONANCES table; pure-Python",
        "kwargs_py": {},
    },
    # ── Patch registry (kept in sync via _mirror_patch_to_native) ────
    # These don't return encoder output directly; they manage state.
    # Their parity is verified end-to-end by get_system_state with
    # patches active (covered by test_native_parity.py + the v0.5.5
    # immolation tests).
    "list_catalog_patches": {
        "status": "python_only",
        "rationale": "metadata over CATALOG/CATALOG_V2 dicts; not encoder I/O",
        "kwargs_py": {},
    },
    "list_active_patches": {
        "status": "python_only",
        "rationale": "registry inspection; both Py + C registries kept in sync via _mirror_patch_to_native",
        "kwargs_py": {},
    },
    "clear_patches": {
        "status": "python_only",
        "rationale": "registry mutation; sync to C via _native_clear_patches",
        "kwargs_py": {},
    },
    # ── Catalog / metadata ───────────────────────────────────────────
    "list_bodies": {
        "status": "python_only",
        "rationale": "metadata over BODIES table; SSOT lives in research/bodies.py",
        "kwargs_py": {},
    },
    "list_kernels": {
        "status": "python_only",
        "rationale": "metadata over KERNELS table",
        "kwargs_py": {},
    },
    "list_lunar_kernels": {
        "status": "python_only",
        "rationale": "metadata over LUNAR_KERNELS table",
        "kwargs_py": {},
    },
    "list_couplings": {
        "status": "python_only",
        "rationale": "metadata over RESONANCES + Laplacian.L_static; not encoder runtime",
        "kwargs_py": {},
    },
    "get_version": {
        "status": "python_only",
        "rationale": "package metadata",
        "kwargs_py": {},
    },
}


# Bridge function names that legitimately do NOT need a parity entry
# (they're plumbing, not encoder ops). Used by the spec-drift smoke.
_NON_PARITY_BRIDGE_NAMES = frozenset({
    # apply_patch / apply_custom_patch are state mutators; their
    # encoder-side correctness is pinned via subsequent
    # get_system_state(backend="c") agreement (covered by
    # test_native_parity + test_runtime_patches).
    "apply_patch",
    "apply_custom_patch",
})


# ─────────────────────────────────────────────────────────────────────
# Driver tests
# ─────────────────────────────────────────────────────────────────────


def _exact_dict_eq(a: Dict, b: Dict) -> bool:
    """Default comparator for parity entries — recursive exact equality."""
    return a == b


@pytest.mark.parametrize("name", sorted(PARITY_TARGETS.keys()))
def test_parity_smoke(name: str) -> None:
    """For each entry in PARITY_TARGETS, exercise its declared parity status."""
    spec = PARITY_TARGETS[name]
    status = spec["status"]
    fn = getattr(bridge, name, None)
    if fn is None:
        pytest.fail(
            f"PARITY_TARGETS lists {name!r} but bridge has no such "
            "attribute; remove the stale entry or restore the function."
        )

    if status == "tier1_skip":
        if not _native_bip.HAS_NATIVE:
            pytest.skip("native library not loaded; tier-1 parity test deferred")
        # Try the Python path; if it works, mark explicit tier-skip.
        # This catches the case where the Python path itself broke.
        kwargs = spec["kwargs_py"]
        out = fn(**kwargs)
        assert out["ok"] is True, (
            f"{name!r} Python path is broken (ok=False): {out.get('error')}; "
            "fix Python first, then port to C."
        )
        pytest.skip(f"tier-1 C port pending; Python path is healthy ({name})")

    if status == "tier2_skip":
        if not _native_bip.HAS_NATIVE:
            pytest.skip("native library not loaded; tier-2 parity test deferred")
        kwargs = spec["kwargs_py"]
        out = fn(**kwargs)
        assert out["ok"] is True, (
            f"{name!r} Python path is broken (ok=False): {out.get('error')}; "
            "fix Python first, then port to C."
        )
        pytest.skip(f"tier-2 C port pending (HD state lift); Python path is healthy ({name})")

    if status == "python_only":
        kwargs = spec["kwargs_py"]
        out = fn(**kwargs)
        # The minimum bar: the call must complete and return ok=True
        # (or be the error-handling Sol-Mars t→JD inverse case which
        # returns positive on success too). All bridge ops in this
        # bucket return ok=True on success.
        assert out.get("ok") is True, (
            f"{name!r} (python_only) returned ok={out.get('ok')!r}: "
            f"{out.get('error')!r}"
        )
        return

    if status == "parity":
        if not _native_bip.HAS_NATIVE:
            pytest.skip("native library not loaded; parity test requires C path")
        py_out = fn(**spec["kwargs_py"])
        c_out = fn(**spec["kwargs_c"])
        assert py_out.get("ok") is True, f"{name!r} BIP path failed: {py_out.get('error')}"
        assert c_out.get("ok") is True, f"{name!r} C path failed: {c_out.get('error')}"
        compare = spec.get("compare", _exact_dict_eq)
        assert compare(py_out, c_out), (
            f"{name!r} parity broken between BIP and C paths.\n"
            f"  BIP: {py_out!r}\n"
            f"  C:   {c_out!r}"
        )
        return

    pytest.fail(f"{name!r} has unknown status {status!r}; fix PARITY_TARGETS schema.")


def test_parity_smoke_spec_covers_bridge_surface() -> None:
    """Drift detection: every public function in bridge must be classified.

    If you add a new bridge method, this test forces you to declare
    its parity status in PARITY_TARGETS (or add it to the explicit
    non-parity allowlist) before CI passes. That keeps the parity
    spec from silently rotting.
    """
    public_fns = [
        name for name, obj in inspect.getmembers(bridge, inspect.isfunction)
        if not name.startswith("_")
        and obj.__module__ == bridge.__name__
    ]
    classified = set(PARITY_TARGETS.keys()) | _NON_PARITY_BRIDGE_NAMES
    unclassified = sorted(set(public_fns) - classified)
    assert not unclassified, (
        f"unclassified bridge functions: {unclassified!r}. Add each to "
        "PARITY_TARGETS (with a parity / python_only / tier1_skip / "
        "tier2_skip status) or to _NON_PARITY_BRIDGE_NAMES with a "
        "rationale. The parity smoke test is the SSOT for which "
        "Python ops have C twins."
    )


def test_parity_smoke_no_orphan_targets() -> None:
    """Reverse drift detection: every PARITY_TARGETS entry must
    correspond to a real bridge function.

    Catches the case where a function got renamed or deleted but the
    PARITY_TARGETS entry stayed.
    """
    public_names = {
        name for name, _ in inspect.getmembers(bridge, inspect.isfunction)
        if not name.startswith("_")
    }
    orphans = sorted(set(PARITY_TARGETS.keys()) - public_names)
    assert not orphans, (
        f"PARITY_TARGETS entries with no corresponding bridge function: "
        f"{orphans!r}. Either restore the function or remove the stale entry."
    )
