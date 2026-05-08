"""``ephemerides-spectral`` console script — entry point for the CLI.

Subcommand-driven; each subcommand maps to one or two bridge methods
and prints the resulting JSON to stdout (compact or pretty-formatted).

The CLI is intentionally thin: it does input parsing + subcommand
dispatch + JSON serialisation. Numerical work happens in the bridge
layer (``ephemerides_spectral.bridge``).

Subcommands
-----------

* ``version`` — package version + frozen-data manifest
* ``bodies`` — list every body in the Sol Star System Laplacian
* ``kernel list`` — list allowed JPL DE-kernels
* ``resolution`` — temporal resolution (sec/residue) for a body
* ``encode`` — encode a JD as a system state (BIP or complex128)
* ``local-view`` — topocentric observer-bound view
* ``eclipse`` — syzygy probability via spectral alignment
* ``couplings`` — list off-diagonal Laplacian fiber couplings
* ``adaptive`` — Phase 9 state-dependent (adaptive / "breathing")
  coupling LUT modulation at a JD. ``breathing`` is an accepted
  hidden synonym for users who prefer the visual metaphor.

Use ``ephemerides-spectral <command> --help`` for per-subcommand detail.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from ephemerides_spectral import bridge
from ephemerides_spectral.bridge import (
    ALLOWED_KERNELS,
    DEFAULT_BACKEND,
    SUPPORTED_BACKENDS,
    SUPPORTED_BODIES,
)
from ephemerides_spectral.version import __version__

_KERNEL_CHOICES = list(ALLOWED_KERNELS)
_BACKEND_CHOICES = list(SUPPORTED_BACKENDS)
_BODY_CHOICES = list(SUPPORTED_BODIES)


# ──────────────────────────────────────────────────────────────────────
# Output helpers
# ──────────────────────────────────────────────────────────────────────

def _emit(result: Dict[str, Any], *, pretty: bool = True) -> int:
    if pretty:
        sys.stdout.write(json.dumps(result, indent=2, sort_keys=True))
    else:
        sys.stdout.write(json.dumps(result, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return 0 if result.get("ok") is not False else 1


def _emit_proper(result: Dict[str, Any], args: argparse.Namespace) -> int:
    """Emit a Sol Time bridge result, optionally applying ``--proper``.

    When ``args.proper`` is set, the result is augmented in place with
    proper-time-corrected count fields (`<field>_proper`) and a
    `proper_time` metadata block, transparently to the user. The
    correction body and count-field set are looked up from the
    canonical map in `bridge.apply_proper_correction`, keyed by
    ``args.subcommand_name`` (set via `set_defaults(...)` on each
    time-* subparser).
    """
    if getattr(args, "proper", False):
        result = bridge.apply_proper_correction(
            result, args.subcommand_name,
            lat=getattr(args, "lat", None),
            lon=getattr(args, "lon", None),
            reference=getattr(args, "reference", "tcb"),
        )
    if getattr(args, "state", False):
        result = bridge.apply_state_correction(
            result, args.subcommand_name,
            frame=getattr(args, "frame", "heliocentric_ecliptic"),
        )
    if getattr(args, "dynamics", False):
        result = bridge.apply_dynamics_correction(
            result, args.subcommand_name,
            frame=getattr(args, "frame", "heliocentric_ecliptic"),
        )
    return _emit(result, pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# Subcommand implementations
# ──────────────────────────────────────────────────────────────────────

def _cmd_version(args: argparse.Namespace) -> int:
    return _emit(bridge.get_version(), pretty=args.pretty)


def _cmd_bodies(args: argparse.Namespace) -> int:
    return _emit(bridge.list_bodies(), pretty=args.pretty)


def _cmd_kernel_list(args: argparse.Namespace) -> int:
    return _emit(bridge.list_kernels(), pretty=args.pretty)


def _cmd_resolution(args: argparse.Namespace) -> int:
    return _emit(bridge.get_resolution(args.body, D=args.D),
                 pretty=args.pretty)


def _cmd_encode(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_system_state(
            args.jd, backend=args.backend, kernel=args.kernel,
            force_high_res=args.force_high_res, D=args.D,
        ),
        pretty=args.pretty,
    )


def _cmd_local_view(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_local_view(args.jd, args.body, args.lat, args.lon,
                              kernel=args.kernel),
        pretty=args.pretty,
    )


def _cmd_eclipse(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_eclipse_probability(args.jd, kernel=args.kernel),
        pretty=args.pretty,
    )


def _cmd_couplings(args: argparse.Namespace) -> int:
    return _emit(bridge.list_couplings(), pretty=args.pretty)


def _cmd_adaptive(args: argparse.Namespace) -> int:
    """Phase 9 state-dependent (adaptive) coupling modulation.

    Also reachable via the hidden ``breathing`` subcommand for users
    who prefer the visual metaphor — same handler, identical output.
    """
    return _emit(
        bridge.get_breathing_modulation(
            args.jd, pair=(args.pair_a, args.pair_b),
            n_lobes=(args.n_a, args.n_b), kernel=args.kernel,
        ),
        pretty=args.pretty,
    )


# Backwards-compatible synonym kept so test fixtures and callers that
# import _cmd_breathing keep working. Equivalent to _cmd_adaptive.
_cmd_breathing = _cmd_adaptive


def _cmd_time_mars(args: argparse.Namespace) -> int:
    if args.msd is not None:
        return _emit(
            bridge.mars_time_to_jd(args.msd, leap_seconds=args.leap_seconds),
            pretty=args.pretty,
        )
    return _emit_proper(
        bridge.jd_to_mars_time(args.jd, leap_seconds=args.leap_seconds),
        args,
    )


def _cmd_time_lunar(args: argparse.Namespace) -> int:
    return _emit_proper(bridge.get_lunar_phase(args.jd), args)


def _cmd_time_uranus(args: argparse.Namespace) -> int:
    if args.usd is not None:
        return _emit(bridge.sol_uranian_time_to_jd(args.usd), pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_uranian_time(args.jd), args)


# ── v0.8.0 Sol Symphony Times: Venus, Mercury, Pluto, Sol, Jupiter, Saturn

def _cmd_time_venus(args: argparse.Namespace) -> int:
    if args.vsd_solar is not None:
        return _emit(bridge.sol_venus_time_to_jd(args.vsd_solar),
                     pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_venus_time(args.jd), args)


def _cmd_time_mercury(args: argparse.Namespace) -> int:
    if args.mer_sd_solar is not None:
        return _emit(bridge.sol_mercury_time_to_jd(args.mer_sd_solar),
                     pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_mercury_time(args.jd), args)


def _cmd_time_pluto(args: argparse.Namespace) -> int:
    if args.psd is not None:
        return _emit(bridge.sol_pluto_time_to_jd(args.psd),
                     pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_pluto_time(args.jd), args)


def _cmd_time_sol(args: argparse.Namespace) -> int:
    if args.crn is not None:
        return _emit(bridge.sol_sol_time_to_jd(args.crn), pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_sol_time(args.jd), args)


def _cmd_time_jupiter(args: argparse.Namespace) -> int:
    if args.jsd is not None:
        return _emit(bridge.sol_jovian_time_to_jd(args.jsd),
                     pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_jovian_time(args.jd), args)


def _cmd_time_saturn(args: argparse.Namespace) -> int:
    if args.ssd is not None:
        return _emit(bridge.sol_saturnian_time_to_jd(args.ssd),
                     pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_saturnian_time(args.jd), args)


def _cmd_time_neptune(args: argparse.Namespace) -> int:
    if args.nsd is not None:
        return _emit(bridge.sol_neptunian_time_to_jd(args.nsd),
                     pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_neptunian_time(args.jd), args)


def _cmd_time_terra(args: argparse.Namespace) -> int:
    if args.tsd_solar is not None:
        return _emit(bridge.sol_terra_time_to_jd(args.tsd_solar),
                     pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_terra_time(args.jd), args)


def _cmd_time_luna(args: argparse.Namespace) -> int:
    if args.lsd_solar is not None:
        return _emit(bridge.sol_luna_time_to_jd(args.lsd_solar),
                     pretty=args.pretty)
    return _emit_proper(bridge.jd_to_sol_luna_time(args.jd), args)


def _cmd_time_terra_luna(args: argparse.Namespace) -> int:
    """v0.10.0 Sol Terra-Luna Time (STLT) — anchored Lunar time, synodic-month count.

    Default epoch is Meton's summer solstice (27 June 432 BCE) — the
    foundational Greek lunar-solar reconciliation anchor. Pass
    ``--epoch <name>`` to switch to one of the other historical anchors:
    ``antikythera`` (205 BCE solar eclipse), ``hipparchus`` (141 BCE
    lunar eclipse), ``mardokempad`` (721 BCE Babylonian lunar eclipse),
    or ``j2000`` (modern Terra-borrowed reference).
    """
    if args.synodic_count is not None:
        return _emit(
            bridge.sol_terra_luna_time_to_jd(args.synodic_count, epoch=args.epoch),
            pretty=args.pretty,
        )
    return _emit_proper(
        bridge.jd_to_sol_terra_luna_time(args.jd, epoch=args.epoch),
        args,
    )


# ── v0.14.0 Sol Moon Times — Galileans (Io / Europa / Ganymede / Callisto)
#
# Per the moons-stuck-to-parent naming convention (v0.9.1):
#   time-jupiter-io       → Sol Jupiter-Io Time (SJIT)
#   time-jupiter-europa   → Sol Jupiter-Europa Time (SJET)
#   time-jupiter-ganymede → Sol Jupiter-Ganymede Time (SJGT)
#   time-jupiter-callisto → Sol Jupiter-Callisto Time (SJCT)
#
# Each is a thin wrapper around the bridge primitive — the bridge
# closure-helpers handle the actual math.

def _cmd_time_jupiter_io(args: argparse.Namespace) -> int:
    """Sol Jupiter-Io Time (SJIT) — anchored sidereal-cycle count for Io."""
    if args.sidereal_count is not None:
        return _emit(
            bridge.sol_jupiter_io_time_to_jd(args.sidereal_count),
            pretty=args.pretty,
        )
    return _emit_proper(bridge.jd_to_sol_jupiter_io_time(args.jd), args)


def _cmd_time_jupiter_europa(args: argparse.Namespace) -> int:
    """Sol Jupiter-Europa Time (SJET) — anchored sidereal-cycle count for Europa."""
    if args.sidereal_count is not None:
        return _emit(
            bridge.sol_jupiter_europa_time_to_jd(args.sidereal_count),
            pretty=args.pretty,
        )
    return _emit_proper(bridge.jd_to_sol_jupiter_europa_time(args.jd), args)


def _cmd_time_jupiter_ganymede(args: argparse.Namespace) -> int:
    """Sol Jupiter-Ganymede Time (SJGT) — anchored sidereal-cycle count for Ganymede."""
    if args.sidereal_count is not None:
        return _emit(
            bridge.sol_jupiter_ganymede_time_to_jd(args.sidereal_count),
            pretty=args.pretty,
        )
    return _emit_proper(bridge.jd_to_sol_jupiter_ganymede_time(args.jd), args)


def _cmd_time_jupiter_callisto(args: argparse.Namespace) -> int:
    """Sol Jupiter-Callisto Time (SJCT) — anchored sidereal-cycle count for Callisto."""
    if args.sidereal_count is not None:
        return _emit(
            bridge.sol_jupiter_callisto_time_to_jd(args.sidereal_count),
            pretty=args.pretty,
        )
    return _emit_proper(bridge.jd_to_sol_jupiter_callisto_time(args.jd), args)


# ── v0.14.2 Sol Moon Times — 8 moons across 4 families.
#
# All four sub-families (Mars, Jupiter inner regulars, Uranus, Neptune)
# share the same simple shape: --jd / --sidereal-count mutex; the four
# v0.14.0/v0.14.1-style closure factories below produce the per-family
# subcommand handlers. Subparser registration uses generic helpers
# below the `setup_parser` function.

def _make_moon_cmd(jd_to_fn, to_jd_fn):
    """Generic factory for time-<parent>-<moon> CLI handlers."""
    def _impl(args):
        if args.sidereal_count is not None:
            return _emit(to_jd_fn(args.sidereal_count), pretty=args.pretty)
        return _emit_proper(jd_to_fn(args.jd), args)
    return _impl


# ── v0.11.0 Sol Proper Time (SPrT) — standalone rate-only query

def _cmd_time_proper(args: argparse.Namespace) -> int:
    """v0.11.0 Sol Proper Time — gravitational + kinematic time-dilation rate.

    Standalone "just give me the rate" surface, complementary to the
    ``--proper`` flag on every other ``time-*`` subcommand. With
    ``--compare-to <body>``, returns the rate ratio + drift per
    Earth-year between two bodies — the most intuitive number for
    human comparison.
    """
    if args.compare_to is not None:
        return _emit(
            bridge.compare_proper_times(args.body, args.compare_to,
                                        reference=args.reference),
            pretty=args.pretty,
        )
    return _emit(
        bridge.get_proper_time_rate(
            args.body, lat=args.lat, lon=args.lon, reference=args.reference,
        ),
        pretty=args.pretty,
    )


# ── v0.12.0 Sol Kinematics — orbital state queries

def _cmd_kinematics(args: argparse.Namespace) -> int:
    """v0.12.0 Sol Kinematics — per-body or full-system orbital state.

    Standalone "give me the orbital state" surface, complementary to
    the ``--state`` flag on every ``time-*`` subcommand. With
    ``--all``, dumps every body in the 52-body roster + system totals
    (Jupiter angular-momentum fraction, etc.).
    """
    if args.all:
        return _emit(
            bridge.get_full_system_state(jd_tdb=args.jd, frame=args.frame),
            pretty=args.pretty,
        )
    if args.body is None:
        return _emit(
            {"ok": False,
             "error": "must specify --body <name> or --all"},
            pretty=args.pretty,
        )
    return _emit(
        bridge.get_kinematic_state(
            args.body, jd_tdb=args.jd, frame=args.frame,
        ),
        pretty=args.pretty,
    )


# ── v0.13.0 Sol Dynamics — system energy / forces / per-body energy budgets

def _cmd_dynamics(args: argparse.Namespace) -> int:
    """v0.13.0 Sol Dynamics — system aggregate, per-body energies, or pair forces.

    Three query modes:
      - default: system-level aggregate (KE / PE / total / L partitions)
      - --body X: that body's energy budget (KE + PE + total)
      - --body X --from Y: gravitational force on X from Y
    """
    if args.from_body is not None:
        if args.body is None:
            return _emit(
                {"ok": False,
                 "error": "--from <Y> requires --body <X>"},
                pretty=args.pretty,
            )
        return _emit(
            bridge.get_force_between(
                args.body, args.from_body,
                jd_tdb=args.jd, frame=args.frame,
            ),
            pretty=args.pretty,
        )
    if args.body is not None:
        return _emit(
            bridge.get_body_energies(
                args.body, jd_tdb=args.jd, frame=args.frame,
            ),
            pretty=args.pretty,
        )
    return _emit(
        bridge.get_dynamics(jd_tdb=args.jd, frame=args.frame),
        pretty=args.pretty,
    )


def _cmd_find_tubes(args: argparse.Namespace) -> int:
    return _emit(
        bridge.find_itn_pathways(
            args.from_jd, args.to_jd,
            departure=args.departure, target=args.target,
            threshold=args.threshold, max_candidates=args.max_candidates,
        ),
        pretty=args.pretty,
    )


def _cmd_find_chains(args: argparse.Namespace) -> int:
    intermediates = None
    if args.intermediates is not None:
        # Empty string ⇒ "[]" (force single-leg direct chain).
        intermediates = (
            [b.strip() for b in args.intermediates.split(",") if b.strip()]
            if args.intermediates
            else []
        )
    return _emit(
        bridge.find_itn_chains(
            args.from_jd, args.to_jd,
            departure=args.departure, target=args.target,
            intermediates=intermediates,
            max_legs=args.max_legs,
            dv_budget_kms=args.dv_budget_kms,
            tof_budget_days=args.tof_budget_days,
            threshold=args.threshold,
            max_chains=args.max_chains,
            max_intermediate_windows=args.max_intermediate_windows,
        ),
        pretty=args.pretty,
    )


def _cmd_body_architecture(args: argparse.Namespace) -> int:
    return _emit(
        bridge.body_architecture(target=args.target),
        pretty=args.pretty,
    )


def _cmd_predict_itn_accessibility(args: argparse.Namespace) -> int:
    return _emit(
        bridge.predict_itn_accessibility(args.departure, args.target),
        pretty=args.pretty,
    )


def _cmd_em_state(args: argparse.Namespace) -> int:
    return _emit(bridge.get_em_state(args.jd_tdb), pretty=args.pretty)


def _cmd_em_couplings(args: argparse.Namespace) -> int:
    return _emit(bridge.list_em_couplings(), pretty=args.pretty)


def _cmd_em_architecture(args: argparse.Namespace) -> int:
    return _emit(
        bridge.em_architecture(target=args.target), pretty=args.pretty
    )


def _cmd_geodetic_state(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_geodetic_state(body=args.body), pretty=args.pretty
    )


def _cmd_geodetic_models(args: argparse.Namespace) -> int:
    return _emit(bridge.list_geodetic_models(), pretty=args.pretty)


def _cmd_geodetic_architecture(args: argparse.Namespace) -> int:
    return _emit(
        bridge.geodetic_architecture(target=args.target), pretty=args.pretty
    )


def _cmd_magnetic_multipoles(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_magnetic_multipoles(body=args.body, crustal=args.crustal),
        pretty=args.pretty,
    )


def _cmd_magnetic_field(args: argparse.Namespace) -> int:
    return _emit(
        bridge.evaluate_magnetic_field(
            body=args.body,
            r_km=args.r_km,
            lat_deg=args.lat_deg,
            lon_deg=args.lon_deg,
            jd_tdb=args.jd_tdb,
        ),
        pretty=args.pretty,
    )


def _cmd_solar_synoptic(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_solar_synoptic_state(jd_tdb=args.jd_tdb),
        pretty=args.pretty,
    )


def _cmd_magnetic_models(args: argparse.Namespace) -> int:
    return _emit(bridge.list_magnetic_multipoles(), pretty=args.pretty)


def _cmd_magnetic_architecture(args: argparse.Namespace) -> int:
    return _emit(
        bridge.magnetic_architecture(target=args.target), pretty=args.pretty,
    )


def _cmd_fluid_state(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_fluid_state(
            body=args.body, jd_tdb=args.jd_tdb,
            lat=args.lat, lon=args.lon,
        ),
        pretty=args.pretty,
    )


def _cmd_fluid_archives(args: argparse.Namespace) -> int:
    return _emit(bridge.list_fluid_archives(), pretty=args.pretty)


def _cmd_fluid_architecture(args: argparse.Namespace) -> int:
    return _emit(
        bridge.fluid_architecture(target=args.target), pretty=args.pretty,
    )


def _cmd_spherical_harmonics(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_spherical_harmonics(body=args.body, channel=args.channel),
        pretty=args.pretty,
    )


def _cmd_spherical_harmonic_models(args: argparse.Namespace) -> int:
    return _emit(
        bridge.list_spherical_harmonic_models(), pretty=args.pretty,
    )


def _cmd_convert_normalisation(args: argparse.Namespace) -> int:
    return _emit(
        bridge.convert_spherical_harmonic_normalisation(
            coefficient_value=args.value,
            n=args.n, m=args.m,
            from_convention=getattr(args, "from"),
            to_convention=args.to,
        ),
        pretty=args.pretty,
    )


def _cmd_admittance(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_topography_gravity_admittance(body=args.body),
        pretty=args.pretty,
    )


def _cmd_admittance_spectra(args: argparse.Namespace) -> int:
    return _emit(bridge.list_admittance_spectra(), pretty=args.pretty)


def _cmd_dynamo_region(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_dynamo_region(body=args.body), pretty=args.pretty,
    )


def _cmd_dynamo_regions(args: argparse.Namespace) -> int:
    return _emit(bridge.list_dynamo_regions(), pretty=args.pretty)


def _cmd_orographic_forcing(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_orographic_forcing(body=args.body), pretty=args.pretty,
    )


def _cmd_orographic_forcings(args: argparse.Namespace) -> int:
    return _emit(bridge.list_orographic_forcings(), pretty=args.pretty)


def _cmd_rotational_constraint(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_rotational_constraint(body=args.body), pretty=args.pretty,
    )


def _cmd_rotational_constraints(args: argparse.Namespace) -> int:
    return _emit(bridge.list_rotational_constraints(), pretty=args.pretty)


def _cmd_auroral_coupling(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_auroral_coupling(body=args.body), pretty=args.pretty,
    )


def _cmd_auroral_couplings(args: argparse.Namespace) -> int:
    return _emit(bridge.list_auroral_couplings(), pretty=args.pretty)


def _cmd_tidal_migration(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_tidal_migration(pair=args.pair), pretty=args.pretty,
    )


def _cmd_tidal_migrations(args: argparse.Namespace) -> int:
    return _emit(bridge.list_tidal_migrations(), pretty=args.pretty)


def _cmd_atmospheric_escape(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_atmospheric_escape(body=args.body), pretty=args.pretty,
    )


def _cmd_atmospheric_escapes(args: argparse.Namespace) -> int:
    return _emit(bridge.list_atmospheric_escapes(), pretty=args.pretty)


def _cmd_heat_flow(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_heat_flow(body=args.body), pretty=args.pretty,
    )


def _cmd_heat_flows(args: argparse.Namespace) -> int:
    return _emit(bridge.list_heat_flows(), pretty=args.pretty)


def _cmd_volcanic_outgassing(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_volcanic_outgassing(body=args.body), pretty=args.pretty,
    )


def _cmd_volcanic_outgassings(args: argparse.Namespace) -> int:
    return _emit(bridge.list_volcanic_outgassings(), pretty=args.pretty)


def _cmd_thermal_balance(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_thermal_balance(body=args.body), pretty=args.pretty,
    )


def _cmd_thermal_balances(args: argparse.Namespace) -> int:
    return _emit(bridge.list_thermal_balances(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# v0.22.0 — Trajectory + Sensing Layer CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_ballistic_trajectory(args: argparse.Namespace) -> int:
    return _emit(
        bridge.compute_ballistic_trajectory(
            body=args.body,
            v_m_s=args.v,
            angle_deg=args.angle,
            altitude_m=args.altitude,
            with_drag=args.with_drag,
            ballistic_coefficient=args.bc,
        ),
        pretty=args.pretty,
    )


def _cmd_ballistic_atmosphere(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_ballistic_atmosphere(body=args.body), pretty=args.pretty,
    )


def _cmd_ballistic_atmospheres(args: argparse.Namespace) -> int:
    return _emit(bridge.list_ballistic_atmospheres(), pretty=args.pretty)


def _cmd_icbm_trajectory(args: argparse.Namespace) -> int:
    return _emit(
        bridge.compute_icbm_trajectory(
            burnout_velocity_m_s=args.burnout_v,
            burnout_flight_path_angle_deg=args.burnout_gamma,
            burnout_altitude_m=args.burnout_alt,
            ballistic_coefficient_kg_m2=args.bc,
        ),
        pretty=args.pretty,
    )


def _cmd_icbm_reference_profile(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_icbm_reference_profile(profile_name=args.profile),
        pretty=args.pretty,
    )


def _cmd_icbm_reference_profiles(args: argparse.Namespace) -> int:
    return _emit(bridge.list_icbm_reference_profiles(), pretty=args.pretty)


def _cmd_visibility_geometry(args: argparse.Namespace) -> int:
    return _emit(
        bridge.compute_visibility_geometry(
            sat_ecef_m=(args.sat_x, args.sat_y, args.sat_z),
            target_lat_deg=args.lat,
            target_lon_deg=args.lon,
            target_altitude_m=args.alt,
            minimum_elevation_deg=args.min_elev,
        ),
        pretty=args.pretty,
    )


def _cmd_sgp4_state(args: argparse.Namespace) -> int:
    return _emit(
        bridge.compute_sgp4_state(
            line1=args.line1,
            line2=args.line2,
            minutes_since_epoch=args.minutes,
        ),
        pretty=args.pretty,
    )


def _cmd_orbital_reference(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_orbital_reference(label=args.label), pretty=args.pretty,
    )


def _cmd_orbital_references(args: argparse.Namespace) -> int:
    return _emit(bridge.list_orbital_references(), pretty=args.pretty)


def _cmd_bc_differential(args: argparse.Namespace) -> int:
    return _emit(
        bridge.compute_bc_differential(
            bc_heavy_kg_m2=args.bc_heavy,
            bc_light_kg_m2=args.bc_light,
            entry_velocity_m_s=args.v_entry,
            entry_flight_path_angle_deg=args.gamma_entry,
            altitude_band_lower_km=args.lower_km,
            altitude_band_upper_km=args.upper_km,
        ),
        pretty=args.pretty,
    )


def _cmd_discrimination_altitude(args: argparse.Namespace) -> int:
    return _emit(
        bridge.compute_discrimination_altitude(
            bc_heavy_kg_m2=args.bc_heavy,
            bc_light_kg_m2=args.bc_light,
            entry_velocity_m_s=args.v_entry,
            entry_flight_path_angle_deg=args.gamma_entry,
            delta_v_threshold_m_s=args.threshold,
        ),
        pretty=args.pretty,
    )


def _cmd_bc_reference_class(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_bc_reference_class(class_name=args.class_name),
        pretty=args.pretty,
    )


def _cmd_bc_reference_classes(args: argparse.Namespace) -> int:
    return _emit(bridge.list_bc_reference_classes(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# v0.23.0 — Spin-orbit resonance CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_spin_orbit_resonance(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_spin_orbit_resonance(body=args.body), pretty=args.pretty,
    )


def _cmd_spin_orbit_resonances(args: argparse.Namespace) -> int:
    return _emit(bridge.list_spin_orbit_resonances(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# v0.24.0 — Mercury Dynamical Spectrum CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_mercury_dynamical_spectrum(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_mercury_dynamical_spectrum(), pretty=args.pretty,
    )


def _cmd_mercury_precession_decomposition(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_mercury_precession_decomposition(), pretty=args.pretty,
    )


def _cmd_mercury_dynamical_spectrum_full(args: argparse.Namespace) -> int:
    return _emit(
        bridge.list_mercury_dynamical_spectrum(), pretty=args.pretty,
    )


# ──────────────────────────────────────────────────────────────────────
# v0.24.1 — Luna Dynamical Spectrum CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_luna_dynamical_spectrum(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_luna_dynamical_spectrum(), pretty=args.pretty,
    )


def _cmd_luna_saros_commensurability(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_luna_saros_commensurability(), pretty=args.pretty,
    )


def _cmd_luna_dynamical_spectrum_full(args: argparse.Namespace) -> int:
    return _emit(
        bridge.list_luna_dynamical_spectrum(), pretty=args.pretty,
    )


# ──────────────────────────────────────────────────────────────────────
# v0.24.2 — Mars Dynamical Spectrum CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_mars_dynamical_spectrum(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_mars_dynamical_spectrum(), pretty=args.pretty,
    )


def _cmd_mars_secular_resonance_overlap(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_mars_secular_resonance_overlap(), pretty=args.pretty,
    )


def _cmd_mars_dynamical_spectrum_full(args: argparse.Namespace) -> int:
    return _emit(
        bridge.list_mars_dynamical_spectrum(), pretty=args.pretty,
    )


# ──────────────────────────────────────────────────────────────────────
# v0.24.3 — Sun Dynamical Spectrum CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_sun_dynamical_spectrum(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_sun_dynamical_spectrum(), pretty=args.pretty,
    )


def _cmd_helioseismic_asymptotic_relation(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_helioseismic_asymptotic_relation(), pretty=args.pretty,
    )


def _cmd_sun_dynamical_spectrum_full(args: argparse.Namespace) -> int:
    return _emit(
        bridge.list_sun_dynamical_spectrum(), pretty=args.pretty,
    )


# ──────────────────────────────────────────────────────────────────────
# v0.24.4 — Per-body Toroidal-Residual J₂ Catalog CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_toroidal_residual(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_toroidal_residual(body=args.body), pretty=args.pretty,
    )


def _cmd_chandrasekhar_sequence(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_chandrasekhar_sequence_thresholds(),
        pretty=args.pretty,
    )


def _cmd_toroidal_residuals(args: argparse.Namespace) -> int:
    return _emit(bridge.list_toroidal_residuals(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# v0.24.5 — Hawaiian-Emperor Chain Spectral Catalog CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_hawaii_chain(args: argparse.Namespace) -> int:
    return _emit(bridge.get_hawaii_chain(), pretty=args.pretty)


def _cmd_hawaii_emperor_bend(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_hawaii_emperor_bend_signature(), pretty=args.pretty,
    )


def _cmd_hawaii_chain_full(args: argparse.Namespace) -> int:
    return _emit(bridge.list_hawaii_chain(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# v0.24.6 — Yarkovsky/YORP CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_yarkovsky_yorp(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_yarkovsky_yorp(body=args.body), pretty=args.pretty,
    )


def _cmd_yorp_attractor_thresholds(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_yorp_attractor_thresholds(), pretty=args.pretty,
    )


def _cmd_yarkovsky_yorps(args: argparse.Namespace) -> int:
    return _emit(bridge.list_yarkovsky_yorp(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# v0.24.7 — Mars Tharsis Volcanic Chain CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_mars_tharsis_chain(args: argparse.Namespace) -> int:
    return _emit(bridge.get_mars_tharsis_chain(), pretty=args.pretty)


def _cmd_tharsis_fiedler_signature(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_tharsis_fiedler_signature(), pretty=args.pretty,
    )


def _cmd_mars_tharsis_chain_full(args: argparse.Namespace) -> int:
    return _emit(bridge.list_mars_tharsis_chain(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# v0.24.8 — Axial Seamount Eruption Chronology CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_axial_seamount_chronology(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_axial_seamount_chronology(), pretty=args.pretty,
    )


def _cmd_axial_inflation_cycle_signature(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_axial_inflation_cycle_signature(), pretty=args.pretty,
    )


def _cmd_axial_seamount_full(args: argparse.Namespace) -> int:
    return _emit(bridge.list_axial_seamount(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# v0.24.9 — Dynamical-Regime Classifier CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_regime_eigenbasis(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_dynamical_regime_eigenbasis(
            n_components=args.n_components,
        ),
        pretty=args.pretty,
    )


def _cmd_regime_classify(args: argparse.Namespace) -> int:
    feature_vector = (
        args.time_scale_log_s,
        args.spatial_scale_log_km,
        args.stability_index,
        args.has_commensurability,
        args.prediction_track_signal,
        args.dimensionality,
        args.forcing_class_index,
    )
    return _emit(
        bridge.classify_dynamical_regime(
            feature_vector=feature_vector,
            n_components=args.n_components,
        ),
        pretty=args.pretty,
    )


def _cmd_regime_list(args: argparse.Namespace) -> int:
    return _emit(bridge.list_dynamical_regimes(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# v0.24.10 — OOS probe + calibration-metric CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_regime_probes(args: argparse.Namespace) -> int:
    return _emit(
        bridge.run_dynamical_regime_probes(
            n_components=args.n_components,
            ood_threshold=args.ood_threshold,
        ),
        pretty=args.pretty,
    )


def _cmd_regime_probes_list(args: argparse.Namespace) -> int:
    return _emit(
        bridge.list_dynamical_regime_probes(), pretty=args.pretty,
    )


# ──────────────────────────────────────────────────────────────────────
# v0.24.11 — Pluto-Charon Dynamical Spectrum CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_pluto_charon_dynamical_spectrum(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_pluto_charon_dynamical_spectrum(), pretty=args.pretty,
    )


def _cmd_double_synchronous_signature(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_double_synchronous_signature(), pretty=args.pretty,
    )


def _cmd_pluto_charon_dynamical_spectrum_full(args: argparse.Namespace) -> int:
    return _emit(
        bridge.list_pluto_charon_dynamical_spectrum(),
        pretty=args.pretty,
    )


# ──────────────────────────────────────────────────────────────────────
# v0.24.12 — Loki Patera (Io) Eruption Cycle CLI handlers
# ──────────────────────────────────────────────────────────────────────


def _cmd_loki_patera_eruption_cycle(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_loki_patera_eruption_cycle(), pretty=args.pretty,
    )


def _cmd_loki_galilean_laplace_signature(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_loki_galilean_laplace_signature(), pretty=args.pretty,
    )


def _cmd_loki_patera_eruption_cycle_full(args: argparse.Namespace) -> int:
    return _emit(
        bridge.list_loki_patera_eruption_cycle(), pretty=args.pretty,
    )


# v0.25.0a — Attested Multi-Source Collector framework

def _cmd_attested_list(args: argparse.Namespace) -> int:
    return _emit(bridge.list_attested_sources(), pretty=args.pretty)


def _cmd_attested_dataset(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_attested_dataset(
            args.source,
            limit=args.limit,
            offset=args.offset,
        ),
        pretty=args.pretty,
    )


def _cmd_attested_descriptor(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_attested_descriptor(args.source), pretty=args.pretty,
    )


def _cmd_attested_audit(args: argparse.Namespace) -> int:
    return _emit(
        bridge.attestation_audit(args.source), pretty=args.pretty,
    )


def _cmd_lunar_kernels(args: argparse.Namespace) -> int:
    return _emit(bridge.list_lunar_kernels(), pretty=args.pretty)


def _cmd_natural_group(args: argparse.Namespace) -> int:
    return _emit(bridge.get_natural_resonance_group(), pretty=args.pretty)


def _cmd_find_syzygies(args: argparse.Namespace) -> int:
    return _emit(
        bridge.find_syzygies(
            args.from_jd, args.to_jd,
            kind=args.kind, threshold=args.threshold,
        ),
        pretty=args.pretty,
    )


def _cmd_patches_catalog(args: argparse.Namespace) -> int:
    return _emit(bridge.list_catalog_patches(), pretty=args.pretty)


def _cmd_patches_active(args: argparse.Namespace) -> int:
    return _emit(bridge.list_active_patches(), pretty=args.pretty)


def _cmd_patches_apply(args: argparse.Namespace) -> int:
    return _emit(bridge.apply_patch(args.name), pretty=args.pretty)


def _cmd_patches_clear(args: argparse.Namespace) -> int:
    return _emit(bridge.clear_patches(), pretty=args.pretty)


# ──────────────────────────────────────────────────────────────────────
# Parser construction
# ──────────────────────────────────────────────────────────────────────

_TOPLEVEL_DESCRIPTION = """\
Ephemerides Spectral — high-precision HDC reference instrument for the
Sol Star System.

Encodes celestial bodies (planets, moons, asteroids) as resonant phases
in a high-dimensional cyclic-group space (Z_{2^32} for the BIP backend
at D=65536). Two interchangeable backends:

  * 'bip' (default)    — bit-serialised integer ALU, 305x speedup,
                         pure-integer cyclic-group reduction via uint32
                         overflow. Phase 9 adaptive couplings (Jupiter-
                         Saturn 5:2 resonance) — also called "breathing"
                         couplings in the visual / informal register —
                         handled with an integer cosine LUT, no FPU in
                         the hot path.
  * 'complex128'       — FPU complex128 reference encoder; same
                         algebraic structure, used for regression and
                         the Syzygy / observer-binding operators.

The system Laplacian decomposes as:

  * Diagonal       — Newtonian mean motions (2pi / period_days).
  * Diagonal (PN)  — Mercury 43"/century relativistic precession.
  * Off-diagonal   — gravitational fiber couplings (planet-sun,
                     moon-planet, J-S resonance, asteroid-Jupiter).

Phase 9 (adaptive / "breathing") modulates the off-diagonal weights
with the resonant phase difference cos(n_a*phi_a - n_b*phi_b) via a
1024-entry int32 cosine LUT (Q1.14 amplitude, 4 KB). The construction
is a state-dependent (non-autonomous) graph Laplacian — adaptive in
the network-science sense (Gross & Blasius 2008, adaptive Kuramoto)
and informally "breathing" because the couplings inhale/exhale with
the relative resonant phase.
"""

_TOPLEVEL_EPILOG = """\
Examples
--------

    # Package version + frozen-data manifest
    ephemerides-spectral version

    # All 26 bodies in the Sol Star System Laplacian
    ephemerides-spectral bodies

    # Terra temporal resolution at the default D=65536
    ephemerides-spectral resolution --body terra

    # Encode J2000 with the integer ALU backend (default)
    ephemerides-spectral encode --jd 2451545.0

    # Same JD with the FPU complex128 reference encoder
    ephemerides-spectral encode --jd 2451545.0 --backend complex128

    # Topocentric view from London at J2000
    ephemerides-spectral local-view --jd 2451545.0 --body terra \\
                          --lat 51.5 --lon -0.1

    # Syzygy alignment probability at a JD
    ephemerides-spectral eclipse --jd 2451545.0

    # Off-diagonal couplings (Laplacian fiber bundle)
    ephemerides-spectral couplings

    # Phase 9 adaptive modulation for Jupiter-Saturn 5:2 at +20 yr
    ephemerides-spectral adaptive --jd 2458850.0

    # Override resonance: 3:2 Neptune-Pluto
    ephemerides-spectral adaptive --jd 2451545.0 \\
                          --pair-a neptune --pair-b pluto --n-a 3 --n-b 2

    # `breathing` is an accepted hidden synonym (same handler):
    ephemerides-spectral breathing --jd 2458850.0

References
----------

* Research notebook:    ../ephemerides_spectral_research_notebook.md
* RBS-HDC evaluation:   ../research/resonant_bit_serialized_hdc_evaluation.md
* Cross-pollination:    chess-spectral notebook §20.13-§20.17
                        (Z_{640} vs Z_{2^32} group-theoretic isomorphism)
* Companion project:    antikythera-spectral (sibling research notebook)

Reference time
--------------

REFERENCE_JD = 2451545.0 (J2000.0). The BIP int64 envelope tolerates
|jd - REFERENCE_JD| up to ~1.86 Myr, well beyond the DE441 epoch
(-13200 BCE .. +17200 CE).
"""


def _add_proper_flags(parser: argparse.ArgumentParser) -> None:
    """Add the v0.11.0 ``--proper``/``--lat``/``--lon``/``--reference`` flag set.

    Called on every ``time-*`` subparser so every Sol Time gets a
    transparent proper-time-correction option without ceremony.
    """
    grp = parser.add_argument_group(
        "proper-time correction (v0.11.0)",
        "Apply gravitational + orbital-kinematic time dilation for the "
        "body's surface (no-op without --proper). Implementation lives "
        "in `bridge.apply_proper_correction`; output gains "
        "`<count>_proper` sibling fields and a `proper_time` block.",
    )
    grp.add_argument(
        "--proper", action="store_true",
        help="Apply Sol Proper Time (SPrT) correction. Augments the "
             "result with proper-time-corrected count fields and a "
             "`proper_time` metadata block. v0.11.0 captures GR surface + "
             "orbital kinematic; J2 oblateness deferred.",
    )
    grp.add_argument(
        "--lat", type=float, default=None,
        help="Surface latitude in degrees (forward-compat for J2 "
             "oblateness; v0.11.0 ignores).",
    )
    grp.add_argument(
        "--lon", type=float, default=None,
        help="Surface longitude in degrees (forward-compat for J2 "
             "oblateness; v0.11.0 ignores).",
    )
    grp.add_argument(
        "--reference", choices=("tcb", "tdb"), default="tcb",
        help="Reference time scale (default 'tcb', barycentric "
             "coordinate time per IAU 2000).",
    )
    # v0.12.0 — Sol Kinematics --state flag, added uniformly to every
    # time-* subcommand the same way --proper is. When set, augments
    # the time output with a `kinematic_state` block (orbital velocity,
    # semi-major axis, kinetic energy, angular momentum) for the
    # subcommand's canonical body.
    state_grp = parser.add_argument_group(
        "kinematic state (v0.12.0)",
        "Augment the result with a Sol Kinematics block for the "
        "subcommand's canonical body (no-op without --state). "
        "Implementation lives in `bridge.apply_state_correction`; "
        "output gains a `kinematic_state` block.",
    )
    state_grp.add_argument(
        "--state", action="store_true",
        help="Apply Sol Kinematics augmentation. Adds a "
             "`kinematic_state` block with orbital velocity, "
             "semi-major axis, kinetic energy, angular momentum.",
    )
    state_grp.add_argument(
        "--frame", choices=("heliocentric_ecliptic", "parent_centric"),
        default="heliocentric_ecliptic",
        help="Reference frame for the kinematic state (default "
             "'heliocentric_ecliptic'). v0.12.0 ships circular Kepler "
             "approximation; both frames produce the same elements.",
    )
    # v0.13.0 — Sol Dynamics --dynamics flag, added uniformly to every
    # time-* subcommand the same way --proper and --state are. When
    # set, augments the time output with a `dynamics` block (KE, PE,
    # total energy, is_bound) for the subcommand's canonical body.
    dyn_grp = parser.add_argument_group(
        "kinematic dynamics (v0.13.0)",
        "Augment the result with a Sol Dynamics block for the "
        "subcommand's canonical body (no-op without --dynamics). "
        "Implementation lives in `bridge.apply_dynamics_correction`; "
        "output gains a `dynamics` block with KE / PE / total energy.",
    )
    dyn_grp.add_argument(
        "--dynamics", action="store_true",
        help="Apply Sol Dynamics augmentation. Adds a `dynamics` "
             "block with kinetic energy, potential energy, total "
             "energy, and is_bound flag. Same body as --state and "
             "--proper.",
    )


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ephemerides-spectral",
        description=_TOPLEVEL_DESCRIPTION,
        epilog=_TOPLEVEL_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version",
                   version=f"ephemerides-spectral {__version__}")
    p.add_argument("--no-pretty", dest="pretty", action="store_false",
                   default=True,
                   help="Emit compact (single-line) JSON instead of pretty-printed.")

    sub = p.add_subparsers(dest="cmd", required=True, title="Commands",
                           metavar="<command>")

    # version
    v = sub.add_parser(
        "version",
        help="Print package version + frozen-data manifest",
        description=(
            "Emits {package, version, manifest} where manifest is the "
            "codegen-stamped table of frozen research-module SHAs."
        ),
    )
    v.set_defaults(func=_cmd_version)

    # bodies
    b = sub.add_parser(
        "bodies",
        help="List the 26 bodies in the Sol Star System Laplacian",
        description=(
            "Star + 9 planets (incl. Pluto) + 12 major moons + 4 main-belt "
            "asteroids. Each row carries period_days and mass_earth used "
            "by the Laplacian construction."
        ),
    )
    b.set_defaults(func=_cmd_bodies)

    # kernel list
    kn = sub.add_parser(
        "kernel",
        help="JPL DE-kernel utilities",
        description="List allowed JPL DE-series ephemeris kernels.",
    )
    kn_sub = kn.add_subparsers(dest="kernel_cmd", required=True)
    kn_list = kn_sub.add_parser(
        "list",
        help="List the allowed DE-kernel set",
        description=(
            "Prints the ALLOWED_KERNELS allowlist (de421/de440/de441/"
            "de442). Actual on-disk availability is determined when an "
            "instrument is constructed; the loader falls back to de421 "
            "if a higher-resolution kernel is missing (unless "
            "force_high_res)."
        ),
    )
    kn_list.set_defaults(func=_cmd_kernel_list)

    # resolution
    r = sub.add_parser(
        "resolution",
        help="Seconds per residue shift for a body at a given D",
        description=(
            "Returns sec/residue and min/residue for one body. At "
            "D=65536, Earth ≈ 481.4 s/residue (~8 min). Resolution "
            "scales linearly with D — bump to D=2^25 for ~1 s/residue."
        ),
        epilog="Example: ephemerides-spectral resolution --body mars --D 65536",
    )
    r.add_argument("--body", default="terra", choices=_BODY_CHOICES,
                   help="Body name (default 'terra')")
    r.add_argument("--D", type=int, default=65536,
                   help="Hypervector dimension (default 65536)")
    r.set_defaults(func=_cmd_resolution)

    # encode
    e = sub.add_parser(
        "encode",
        help="Encode a JD as the system state vector",
        description=(
            "Build the HDC system state for a Julian Date. The default "
            "'bip' backend returns per-body uint32 phase residues from "
            "the integer-ALU encoder; 'complex128' returns the FPU "
            "reference's interleaved-Float32 complex state."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral encode --jd 2451545.0\n"
            "  ephemerides-spectral encode --jd 2451545.0 --backend complex128\n"
            "  ephemerides-spectral encode --jd 2451545.0 --kernel de441 --force-high-res"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    e.add_argument("--jd", type=float, required=True,
                   help="Julian Date in TDB")
    e.add_argument("--backend", choices=_BACKEND_CHOICES, default=DEFAULT_BACKEND,
                   help=f"HDC backend (default {DEFAULT_BACKEND!r})")
    e.add_argument("--kernel", choices=_KERNEL_CHOICES, default="de441",
                   help="JPL DE-kernel for calibration (default 'de441')")
    e.add_argument("--force-high-res", dest="force_high_res", action="store_true",
                   help="Abort if the requested kernel is missing (no de421 fallback)")
    e.add_argument("--D", type=int, default=65536,
                   help="Hypervector dimension; must be a power of 2 (default 65536)")
    e.set_defaults(func=_cmd_encode)

    # local-view
    lv = sub.add_parser(
        "local-view",
        help="Topocentric view bound to a body + (lat, lon)",
        description=(
            "Extracts a 'Local View' hypervector by binding a unitary "
            "Observer Operator to the global system state. Encodes the "
            "perspective of an observer at (lat, lon) on body."
        ),
        epilog=(
            "Example: ephemerides-spectral local-view --jd 2451545.0 \\\n"
            "                --body terra --lat 51.5 --lon -0.1"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    lv.add_argument("--jd", type=float, required=True, help="Julian Date in TDB")
    lv.add_argument("--body", required=True, choices=_BODY_CHOICES,
                    help="Body name")
    lv.add_argument("--lat", type=float, required=True,
                    help="Geographic latitude (-90 .. 90)")
    lv.add_argument("--lon", type=float, required=True,
                    help="Geographic longitude (-180 .. 360)")
    lv.add_argument("--kernel", choices=_KERNEL_CHOICES, default="de441",
                    help="JPL DE-kernel (default 'de441')")
    lv.set_defaults(func=_cmd_local_view)

    # eclipse
    ec = sub.add_parser(
        "eclipse",
        help="Syzygy probability at a JD via spectral alignment",
        description=(
            "Inner product of the system state with the Syzygy Operator "
            "(Sun + Moon + lunar Node basis). Returns a magnitude in "
            "[0, 1]; high values indicate a syzygy (eclipse / "
            "conjunction) is spectrally close."
        ),
    )
    ec.add_argument("--jd", type=float, required=True, help="Julian Date in TDB")
    ec.add_argument("--kernel", choices=_KERNEL_CHOICES, default="de441",
                    help="JPL DE-kernel (default 'de441')")
    ec.set_defaults(func=_cmd_eclipse)

    # couplings
    cp = sub.add_parser(
        "couplings",
        help="Off-diagonal Laplacian couplings (gravitational fibers)",
        description=(
            "Lists every off-diagonal weight in the static Laplacian, "
            "categorised as planet-sun / moon-planet / asteroid-jupiter "
            "/ resonance. Output includes both the rad/day weight and "
            "the residues/day fixed-point conversion (Q-format)."
        ),
    )
    cp.set_defaults(func=_cmd_couplings)

    # adaptive (primary) + breathing (hidden synonym)
    #
    # Phase 9 modulates the off-diagonal Laplacian weights with the
    # resonant phase difference cos(n_a*phi_a - n_b*phi_b). This is a
    # state-dependent (non-autonomous) graph Laplacian — adaptive in
    # the network-science sense (Gross & Blasius 2008, adaptive Kuramoto
    # coupling). Informally we call it "breathing" because the couplings
    # inhale/exhale with the relative resonant phase. `adaptive` is the
    # primary subcommand; `breathing` is preserved as a hidden synonym
    # for users who prefer the visual metaphor — same handler, same args.

    def _add_adaptive_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--jd", type=float, required=True,
                       help="Julian Date in TDB")
        p.add_argument("--pair-a", dest="pair_a", default="jupiter",
                       choices=_BODY_CHOICES, help="First body of the pair")
        p.add_argument("--pair-b", dest="pair_b", default="saturn",
                       choices=_BODY_CHOICES, help="Second body of the pair")
        p.add_argument("--n-a", dest="n_a", type=int, default=5,
                       help="Resonance multiplier on phi_a (default 5)")
        p.add_argument("--n-b", dest="n_b", type=int, default=2,
                       help="Resonance multiplier on phi_b (default 2)")
        p.add_argument("--kernel", choices=_KERNEL_CHOICES, default="de441",
                       help="JPL DE-kernel (default 'de441')")
        p.set_defaults(func=_cmd_adaptive)

    ad = sub.add_parser(
        "adaptive",
        help="Phase 9 adaptive (a.k.a. 'breathing') coupling LUT at a JD",
        description=(
            "Computes the resonant phase n_a*phi_a - n_b*phi_b (mod "
            "2^32) for a body pair at a JD, then evaluates the integer "
            "cosine LUT (Q1.14, 1024 entries). Returns both the LUT "
            "value and a float reference for calibration. The "
            "construction is a state-dependent (non-autonomous) graph "
            "Laplacian — adaptive in the adaptive-networks / adaptive-"
            "Kuramoto sense (Gross & Blasius 2008). The visual / "
            "informal name is 'breathing' couplings; the `breathing` "
            "subcommand is an accepted hidden synonym (same handler)."
        ),
        epilog=(
            "Examples:\n"
            "  # Default Jupiter-Saturn 5:2 resonance\n"
            "  ephemerides-spectral adaptive --jd 2451545.0\n\n"
            "  # Neptune-Pluto 3:2 resonance\n"
            "  ephemerides-spectral adaptive --jd 2451545.0 \\\n"
            "         --pair-a neptune --pair-b pluto --n-a 3 --n-b 2\n\n"
            "  # Io-Europa 1:2 (note ordering: smaller multiplier first)\n"
            "  ephemerides-spectral adaptive --jd 2451545.0 \\\n"
            "         --pair-a europa --pair-b io --n-a 1 --n-b 2\n\n"
            "  # `breathing` is an accepted hidden synonym:\n"
            "  ephemerides-spectral breathing --jd 2451545.0"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_adaptive_args(ad)

    # Hidden synonym: invisible in `--help` (help=argparse.SUPPRESS) but
    # fully functional when typed. Kept for visual-metaphor users and
    # backwards compatibility with v0.9.1 and earlier scripts.
    br = sub.add_parser(
        "breathing",
        help=argparse.SUPPRESS,
        description=(
            "Hidden synonym for `adaptive`. Phase 9 state-dependent "
            "coupling modulation. See `ephemerides-spectral adaptive "
            "--help` for the canonical help text."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_adaptive_args(br)

    # time-mars
    tm = sub.add_parser(
        "time-mars",
        help="Mars Sol Date + Mars Coordinated Time at a JD (or invert)",
        description=(
            "Convert UTC Julian Date to Mars Sol Date (MSD) + Mars "
            "Coordinated Time (MTC) per Allison & McEwen 2000. "
            "Use --msd to invert (MSD -> JD_UTC). The default leap-"
            "second offset (37 s) is the IERS Bulletin C value from "
            "Jan 2017, unchanged through 2026."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-mars --jd 2451549.5    # MSD reference\n"
            "  ephemerides-spectral time-mars --jd 2461165.0    # today-ish\n"
            "  ephemerides-spectral time-mars --msd 50000       # MSD -> JD"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tm_group = tm.add_mutually_exclusive_group(required=True)
    tm_group.add_argument("--jd", type=float, default=None,
                          help="UTC Julian Date to convert to MSD + MTC")
    tm_group.add_argument("--msd", type=float, default=None,
                          help="Mars Sol Date to invert back to JD_UTC")
    tm.add_argument("--leap-seconds", dest="leap_seconds", type=int,
                    default=37,
                    help="TAI - UTC offset, seconds (default 37)")
    _add_proper_flags(tm)
    tm.set_defaults(func=_cmd_time_mars, subcommand_name="time-mars")

    # time-lunar
    tl = sub.add_parser(
        "time-lunar",
        help="Mean synodic + sidereal lunar age/phase at a JD",
        description=(
            "Returns mean lunar synodic and sidereal age (days since "
            "the J2000-anchored reference new moon) and phase ([0,1)). "
            "These are the bronze-dial primitives — fixed-period "
            "approximations sufficient for HDC encoding and Saros-"
            "class navigation. For arc-second-class precision use "
            "the JPL ephemeris path via `encode --jd ...` and read "
            "the moon residue."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-lunar --jd 2451545.0   # J2000\n"
            "  ephemerides-spectral time-lunar --jd 2461165.0   # today-ish"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tl.add_argument("--jd", type=float, required=True,
                    help="Julian Date in TDB")
    _add_proper_flags(tl)
    tl.set_defaults(func=_cmd_time_lunar, subcommand_name="time-lunar")

    # time-uranus (v0.5.4)
    tu = sub.add_parser(
        "time-uranus",
        help="Sol Uranian Time (USD + SUT) + orbital season at a JD (or invert)",
        description=(
            "Convert JD (TDB) to Sol Uranian Time. The third planetary "
            "time system in the package alongside Mars (MSD/MTC) and "
            "lunar synodic/sidereal phase. Three independent cycles:\n"
            "  - USD (Uranian Sol Date): Uranian sidereal days since the "
            "    SUT epoch (2007-12-16 northern equinox). 1 USD ~= 17.24 h.\n"
            "  - SUT (Sol Uranian Time): time-of-day at Uranus's prime "
            "    meridian, 0-24 hours. 1 Uranian hour ~= 43.1 Earth-min.\n"
            "  - Orbital phase + season: Uranus's 84.02-yr orbit is "
            "    partitioned into 4 ~21-yr seasons. Anchored at the 2007 "
            "    northern equinox. Uranus rotates retrograde (the rotation "
            "    direction is backwards relative to its orbital motion); "
            "    the result carries `retrograde=True`.\n"
            "Use --usd to invert (USD -> JD_TDB)."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-uranus --jd 2451545.0    # J2000\n"
            "  ephemerides-spectral time-uranus --jd 2454451.0    # SUT epoch (2007 equinox)\n"
            "  ephemerides-spectral time-uranus --jd 2461165.0    # today-ish\n"
            "  ephemerides-spectral time-uranus --usd 4046.45     # USD -> JD_TDB\n\n"
            "Sol Uranian Time and Mars Sol Date are independent: their cyclic\n"
            "groups don't share natural-coprime structure (Uranus does not\n"
            "sit in a clean integer mean-motion resonance with anything in\n"
            "the Sol Star System). See research notebook §7 for the\n"
            "natural-harmonic discussion + the 4-season geometry."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tu_group = tu.add_mutually_exclusive_group(required=True)
    tu_group.add_argument("--jd", type=float, default=None,
                          help="JD (TDB) to convert to Sol Uranian Time")
    tu_group.add_argument("--usd", type=float, default=None,
                          help="Uranian Sol Date to invert back to JD_TDB")
    _add_proper_flags(tu)
    tu.set_defaults(func=_cmd_time_uranus, subcommand_name="time-uranus")

    # ── v0.8.0 Sol Symphony Times: Venus, Mercury, Pluto, Sol, Jupiter, Saturn

    # time-venus
    tv = sub.add_parser(
        "time-venus",
        help="Sol Venusian Time at a JD (sidereal + solar day phase)",
        description=(
            "Convert JD (TDB) to Sol Venusian Time. Venus's sidereal day\n"
            "(243.0 Earth-days) is LONGER than its 224.7-day year, so the\n"
            "sidereal vs. solar day distinction matters: the result\n"
            "carries both. Solar day = 116.75 Earth-days = the natural\n"
            "answer to 'what time is it on Venus' (one sunrise to next).\n"
            "Venus rotates retrograde; the result carries `retrograde=True`.\n"
            "Use --vsd-solar to invert (Venus solar-day count -> JD_TDB)."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-venus --jd 2451545.0     # J2000 (anchor)\n"
            "  ephemerides-spectral time-venus --vsd-solar 100    # 100 solar days past J2000\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tv_g = tv.add_mutually_exclusive_group(required=True)
    tv_g.add_argument("--jd", type=float, default=None,
                       help="JD (TDB) to convert to Sol Venusian Time")
    tv_g.add_argument("--vsd-solar", dest="vsd_solar", type=float, default=None,
                       help="Venus solar-day count to invert back to JD_TDB")
    _add_proper_flags(tv)
    tv.set_defaults(func=_cmd_time_venus, subcommand_name="time-venus")

    # time-mercury
    tm2 = sub.add_parser(
        "time-mercury",
        help="Sol Mercurian Time at a JD (3:2 spin-orbit resonance)",
        description=(
            "Convert JD (TDB) to Sol Mercurian Time. Mercury is in 3:2\n"
            "spin-orbit resonance: the solar day = 2 Mercury years exactly.\n"
            "Sidereal day = 58.65 Earth-days, solar day = 175.98 Earth-days,\n"
            "year = 87.97 Earth-days. The result carries both sidereal-day\n"
            "and solar-day phase coordinates.\n"
            "Use --mer-sd-solar to invert."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-mercury --jd 2451545.0       # J2000 (anchor)\n"
            "  ephemerides-spectral time-mercury --mer-sd-solar 50    # 50 solar days past J2000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tm2_g = tm2.add_mutually_exclusive_group(required=True)
    tm2_g.add_argument("--jd", type=float, default=None,
                        help="JD (TDB) to convert to Sol Mercurian Time")
    tm2_g.add_argument("--mer-sd-solar", dest="mer_sd_solar",
                        type=float, default=None,
                        help="Mercury solar-day count to invert back to JD_TDB")
    _add_proper_flags(tm2)
    tm2.set_defaults(func=_cmd_time_mercury, subcommand_name="time-mercury")

    # time-pluto
    tp = sub.add_parser(
        "time-pluto",
        help="Sol Plutonian Time at a JD (Pluto-Charon system rotation)",
        description=(
            "Convert JD (TDB) to Sol Plutonian Time. Pluto sidereal day =\n"
            "6.39 Earth-days; year = 248 Earth-years. The Pluto-Charon\n"
            "system is mutually tidally locked — Charon's orbital period\n"
            "equals Pluto's rotation period exactly. IAU-2015 anchors the\n"
            "prime meridian at the sub-Charon point. Pluto's tilt of 122.5°\n"
            "puts it in the retrograde-rotation regime (similar to Uranus).\n"
            "Use --psd to invert."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-pluto --jd 2457217.0    # New Horizons closest approach (anchor)\n"
            "  ephemerides-spectral time-pluto --jd 2451545.0    # J2000\n"
            "  ephemerides-spectral time-pluto --psd 365         # 365 Pluto-sols past anchor"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tp_g = tp.add_mutually_exclusive_group(required=True)
    tp_g.add_argument("--jd", type=float, default=None,
                       help="JD (TDB) to convert to Sol Plutonian Time")
    tp_g.add_argument("--psd", type=float, default=None,
                       help="Pluto sol-date count to invert back to JD_TDB")
    _add_proper_flags(tp)
    tp.set_defaults(func=_cmd_time_pluto, subcommand_name="time-pluto")

    # time-sol (the Sun's own time, Carrington system)
    ts = sub.add_parser(
        "time-sol",
        help="Sol Sol Time — the Sun's own time, Carrington rotation system",
        description=(
            "Convert JD (TDB) to Sol Sol Time. The Sun has no IAU prime\n"
            "meridian (no solid surface), so the Carrington Rotation Number\n"
            "(CRN) is the conventional reference: integer counter starting\n"
            "at CRN 1 on 1853-11-09, each rotation = 25.38 Earth-days at\n"
            "~16° solar latitude. The Sun has differential rotation (equator\n"
            "~24.47 d, poles ~38 d); 25.38 d is the Carrington reference.\n"
            "Use --crn to invert (CRN -> JD_TDB)."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-sol --jd 2398167.4    # CRN 1 epoch (anchor)\n"
            "  ephemerides-spectral time-sol --jd 2451545.0    # J2000 (~CRN 1956)\n"
            "  ephemerides-spectral time-sol --jd 2461165.0    # today-ish\n"
            "  ephemerides-spectral time-sol --crn 2300        # CRN -> JD_TDB"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ts_g = ts.add_mutually_exclusive_group(required=True)
    ts_g.add_argument("--jd", type=float, default=None,
                       help="JD (TDB) to convert to Sol Sol Time")
    ts_g.add_argument("--crn", type=float, default=None,
                       help="Carrington Rotation Number to invert back to JD_TDB")
    _add_proper_flags(ts)
    ts.set_defaults(func=_cmd_time_sol, subcommand_name="time-sol")

    # time-jupiter
    tj = sub.add_parser(
        "time-jupiter",
        help="Sol Jovian Time at a JD (Jupiter System III magnetic-field rotation)",
        description=(
            "Convert JD (TDB) to Sol Jovian Time using System III rotation\n"
            "(magnetic-field axis, 9h 55m 30s — the IAU standard). System I\n"
            "(equatorial cloud features) and System II (mid-latitude clouds)\n"
            "have different rates and are not exposed here. Year = 11.86\n"
            "Earth-years.\n"
            "Use --jsd to invert."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-jupiter --jd 2444000.5   # System III 1965.0 (anchor)\n"
            "  ephemerides-spectral time-jupiter --jd 2451545.0   # J2000\n"
            "  ephemerides-spectral time-jupiter --jsd 1000       # 1000 Jovian sols past anchor"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tj_g = tj.add_mutually_exclusive_group(required=True)
    tj_g.add_argument("--jd", type=float, default=None,
                       help="JD (TDB) to convert to Sol Jovian Time")
    tj_g.add_argument("--jsd", type=float, default=None,
                       help="Jupiter sol-date count (System III) to invert back to JD_TDB")
    _add_proper_flags(tj)
    tj.set_defaults(func=_cmd_time_jupiter, subcommand_name="time-jupiter")

    # time-saturn
    tsat = sub.add_parser(
        "time-saturn",
        help="Sol Saturnian Time at a JD (Cassini-revised System III)",
        description=(
            "Convert JD (TDB) to Sol Saturnian Time using the Cassini-revised\n"
            "System III rotation period (10h 32m 35s, Mankovich et al. 2019\n"
            "ApJ 871:1 — supersedes the older Voyager value of 10h 39m 22.4s).\n"
            "Saturn's rotation rate was determined via ring seismology, not\n"
            "moon orbits — Sol Saturnian Time is fully independent of any\n"
            "Saturnian moon set. Year = 29.46 Earth-years.\n"
            "Use --ssd to invert."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-saturn --jd 2451545.0   # J2000 (anchor)\n"
            "  ephemerides-spectral time-saturn --jd 2461165.0   # today-ish\n"
            "  ephemerides-spectral time-saturn --ssd 5000       # 5000 Saturnian sols past J2000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tsat_g = tsat.add_mutually_exclusive_group(required=True)
    tsat_g.add_argument("--jd", type=float, default=None,
                         help="JD (TDB) to convert to Sol Saturnian Time")
    tsat_g.add_argument("--ssd", type=float, default=None,
                         help="Saturn sol-date count to invert back to JD_TDB")
    _add_proper_flags(tsat)
    tsat.set_defaults(func=_cmd_time_saturn, subcommand_name="time-saturn")

    # time-neptune
    tn = sub.add_parser(
        "time-neptune",
        help="Sol Neptunian Time at a JD (Voyager 2 magnetic-field rotation)",
        description=(
            "Convert JD (TDB) to Sol Neptunian Time. Neptune's System III\n"
            "rotation period (16h 6m 36s ± 3s) was measured by Voyager 2\n"
            "in 1989 from magnetic-field tilt-tracking; still the canonical\n"
            "value (no Cassini-equivalent ring seismology mission to Neptune\n"
            "yet). Prograde rotation, axial tilt 28.32°, year = 164.79 Earth-\n"
            "years. Anchor: J2000.0.\n"
            "Use --nsd to invert."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-neptune --jd 2451545.0   # J2000 (anchor)\n"
            "  ephemerides-spectral time-neptune --jd 2461165.0   # today-ish\n"
            "  ephemerides-spectral time-neptune --nsd 5000       # 5000 Neptunian sols past J2000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tn_g = tn.add_mutually_exclusive_group(required=True)
    tn_g.add_argument("--jd", type=float, default=None,
                       help="JD (TDB) to convert to Sol Neptunian Time")
    tn_g.add_argument("--nsd", type=float, default=None,
                       help="Neptune sol-date count to invert back to JD_TDB")
    _add_proper_flags(tn)
    tn.set_defaults(func=_cmd_time_neptune, subcommand_name="time-neptune")

    # time-terra (v0.9.1) — Sol Terra Time (STT)
    tt = sub.add_parser(
        "time-terra",
        help="Sol Terra Time (STT) at a JD — Earth's surface clock",
        description=(
            "Convert JD (TDB) to Sol Terra Time. Terra's surface clock\n"
            "anchored at J2000.0 with Greenwich as the prime meridian.\n"
            "  sidereal day = 23h 56m 4s = 0.99726957 Earth-days\n"
            "  solar day    = 24h        = 1.0 Earth-day (by definition)\n"
            "  year         = 365.256 Earth-days\n"
            "Use --tsd-solar to invert."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-terra --jd 2451545.0   # J2000 (anchor)\n"
            "  ephemerides-spectral time-terra --jd 2461165.0   # today-ish\n"
            "  ephemerides-spectral time-terra --tsd-solar 5000 # 5000 Terra solar days past J2000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tt_g = tt.add_mutually_exclusive_group(required=True)
    tt_g.add_argument("--jd", type=float, default=None,
                       help="JD (TDB) to convert to Sol Terra Time")
    tt_g.add_argument("--tsd-solar", dest="tsd_solar", type=float, default=None,
                       help="Terra solar-day count to invert back to JD_TDB")
    _add_proper_flags(tt)
    tt.set_defaults(func=_cmd_time_terra, subcommand_name="time-terra")

    # time-luna (v0.9.1) — Sol Luna Time (SLT)
    tl2 = sub.add_parser(
        "time-luna",
        help="Sol Luna Time (SLT) at a JD — Luna's surface clock",
        description=(
            "Convert JD (TDB) to Sol Luna Time. Luna's surface clock,\n"
            "tidally locked to Terra so sidereal day = orbital period.\n"
            "  sidereal day = orbital period = 27.32 Earth-days\n"
            "  solar day    = synodic month  = 29.53 Earth-days\n"
            "Anchored at J2000.0 with the IAU 2015 prime meridian at\n"
            "the sub-Terra point.\n"
            "\n"
            "DISTINCT FROM Sol Lunar Time (`time-lunar`), which returns\n"
            "Luna's synodic + sidereal phase as observed from Terra.\n"
            "Same body, different observer frame.\n"
            "Use --lsd-solar to invert."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral time-luna --jd 2451545.0     # J2000 (anchor)\n"
            "  ephemerides-spectral time-luna --jd 2461165.0     # today-ish\n"
            "  ephemerides-spectral time-luna --lsd-solar 100    # 100 Luna synodic days past J2000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tl2_g = tl2.add_mutually_exclusive_group(required=True)
    tl2_g.add_argument("--jd", type=float, default=None,
                        help="JD (TDB) to convert to Sol Luna Time")
    tl2_g.add_argument("--lsd-solar", dest="lsd_solar", type=float, default=None,
                        help="Luna solar (synodic) day count to invert back to JD_TDB")
    _add_proper_flags(tl2)
    tl2.set_defaults(func=_cmd_time_luna, subcommand_name="time-luna")

    # time-terra-luna (v0.10.0) — Sol Terra-Luna Time (STLT)
    #
    # Anchored Lunar time using the synodic month — primary lunar-time
    # entry per the moons-stuck-to-parent `Sol <Parent>-<Body> Time`
    # convention. First Sol Time member
    # whose default epoch is NOT J2000.0 / Terra-borrowed: ships with
    # Meton's summer solstice (27 Jun 432 BCE) as the default house
    # epoch, with four other Greek-historical alternatives via --epoch.
    from ephemerides_spectral.bridge import STLT_EPOCHS, STLT_DEFAULT_EPOCH
    _STLT_EPOCH_CHOICES = sorted(STLT_EPOCHS)

    ttl = sub.add_parser(
        "time-terra-luna",
        help="Sol Terra-Luna Time (STLT) at a JD — anchored Lunar time, synodic-month count",
        description=(
            "Convert JD (TDB) to Sol Terra-Luna Time (STLT) — anchored\n"
            "Lunar time using the synodic month (29.530589 days) as\n"
            "the natural unit. The 'Terra-Luna' in the name follows the\n"
            "moons-stuck-to-parent `Sol <Parent>-<Body> Time` convention.\n"
            "Saros (18.03 yr) and Metonic (19.00 yr) cycle counts come\n"
            "along for free.\n"
            "\n"
            "First Sol Time in the package whose DEFAULT epoch is not\n"
            "J2000.0 / Terra-borrowed. Default is Meton of Athens's\n"
            "summer solstice (27 June 432 BCE) — the calibration\n"
            "anchor of the Metonic cycle (235 synodic months ≈ 19\n"
            "tropical years). Greek mathematical astronomy's center of\n"
            "mass: the Hipparchus-Babylonian eclipse-archive midpoint\n"
            "lands within +240 days of Meton's solstice (same year).\n"
            "\n"
            "Available epochs (--epoch <name>):\n"
            "  meton        Meton's summer solstice 432 BCE  (default)\n"
            "  antikythera  Antikythera Saros eclipse 205 BCE\n"
            "  hipparchus   Hipparchus's lunar eclipse 141 BCE\n"
            "  mardokempad  Babylonian lunar eclipse 721 BCE\n"
            "  j2000        Modern reference (Terra-borrowed)\n"
            "\n"
            "DISTINCT from SLT (Luna's surface clock), Sol Lunar Time\n"
            "(Luna's phase observed from Terra), and STT (Terra's\n"
            "surface clock). STLT is the *system-level* (Sun-Terra-\n"
            "Luna pair) clock — natural home for eclipses, conjunctions,\n"
            "and Saros / Metonic cycle counts.\n"
            "\n"
            "House-epoch design choice; not a claim to be NASA's\n"
            "eventual LCT (Lunar Coordinated Time) standard.\n"
            "\n"
            "Use --synodic-count to invert."
        ),
        epilog=(
            "Examples:\n"
            "  # Default Meton epoch — synodic count from 432 BCE solstice\n"
            "  ephemerides-spectral time-terra-luna --jd 2451545.0\n\n"
            "  # Antikythera Saros anchor (Freeth & Jones 2012)\n"
            "  ephemerides-spectral time-terra-luna --jd 2451545.0 --epoch antikythera\n\n"
            "  # Modern J2000 reference\n"
            "  ephemerides-spectral time-terra-luna --jd 2451545.0 --epoch j2000\n\n"
            "  # Inverse: synodic count back to JD_TDB (Meton epoch)\n"
            "  ephemerides-spectral time-terra-luna --synodic-count 27294.31"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ttl_g = ttl.add_mutually_exclusive_group(required=True)
    ttl_g.add_argument("--jd", type=float, default=None,
                       help="JD (TDB) to convert to Sol Terra-Luna Time")
    ttl_g.add_argument("--synodic-count", dest="synodic_count", type=float, default=None,
                       help="Synodic-month count (since the chosen epoch) "
                            "to invert back to JD_TDB")
    ttl.add_argument("--epoch", choices=_STLT_EPOCH_CHOICES,
                     default=STLT_DEFAULT_EPOCH,
                     help=f"Historical anchor (default {STLT_DEFAULT_EPOCH!r})")
    _add_proper_flags(ttl)
    ttl.set_defaults(func=_cmd_time_terra_luna, subcommand_name="time-terra-luna")

    # time-jupiter-{io,europa,ganymede,callisto} (v0.14.0) — Galilean Sol Moon Times.
    #
    # Per the moons-stuck-to-parent naming convention (v0.9.1). Each is
    # an anchored sidereal-cycle count from J2000 — no historical-epoch
    # menu like STLT (Galileans don't have a Greek-astronomy archive;
    # Galileo's 1610 telescopic discovery is a candidate non-default for
    # a future ship).
    #
    # The four near-identical subparsers are built via a shared helper
    # to keep them consistent — same CLI shape, same --jd/--sidereal-count
    # mutex, same help-block format.
    def _add_galilean_subparser(name: str, body_label: str, abbrev: str,
                                period_days: float, handler):
        p = sub.add_parser(
            f"time-jupiter-{name}",
            help=f"Sol Jupiter-{body_label} Time ({abbrev}) at a JD — anchored sidereal-cycle count",
            description=(
                f"Convert JD (TDB) to Sol Jupiter-{body_label} Time ({abbrev}) —\n"
                f"anchored sidereal-cycle count for {body_label} since J2000.0.\n"
                f"\n"
                f"{body_label} is tidally locked to Jupiter, so:\n"
                f"\n"
                f"  sidereal day = orbital period = rotation period\n"
                f"               = {period_days:.6f} days\n"
                f"\n"
                f"Naming follows the moons-stuck-to-parent convention\n"
                f"(v0.9.1): the 'Jupiter-{body_label}' in the name signals\n"
                f"that this is *the moon's* clock as a member of the\n"
                f"Jovian system, not Jupiter's surface clock (= SJT).\n"
                f"\n"
                f"Use --sidereal-count to invert."
            ),
            epilog=(
                f"Examples:\n"
                f"  # Sidereal-cycle count for {body_label} at J2000\n"
                f"  ephemerides-spectral time-jupiter-{name} --jd 2451545.0\n\n"
                f"  # Inverse: 100 sidereal cycles back to JD_TDB\n"
                f"  ephemerides-spectral time-jupiter-{name} --sidereal-count 100"
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--jd", type=float, default=None,
                       help=f"JD (TDB) to convert to Sol Jupiter-{body_label} Time")
        g.add_argument("--sidereal-count", dest="sidereal_count",
                       type=float, default=None,
                       help="Sidereal-cycle count (since J2000) to invert back to JD_TDB")
        _add_proper_flags(p)
        p.set_defaults(func=handler, subcommand_name=f"time-jupiter-{name}")
        return p

    _add_galilean_subparser("io",       "Io",       "SJuIoT",  1.76913786, _cmd_time_jupiter_io)
    _add_galilean_subparser("europa",   "Europa",   "SJuEuT",  3.55118100, _cmd_time_jupiter_europa)
    _add_galilean_subparser("ganymede", "Ganymede", "SJuGaT",  7.15455296, _cmd_time_jupiter_ganymede)
    _add_galilean_subparser("callisto", "Callisto", "SJuCaT", 16.68901840, _cmd_time_jupiter_callisto)

    # ── v0.14.1 Saturnian Sol Moon Times — 11 moons.
    #
    # Per the v0.14.1 abbreviation policy switch (4-letter → 6-letter),
    # all moons across the package use S<Planet2><Moon2>T pattern. The
    # CLI subcommand naming follows time-saturn-<moon>; same shared
    # helper as the Galileans for consistency.
    def _cmd_time_saturn_make(jd_to_fn, to_jd_fn):
        """Closure factory — same handler shape as the four explicit
        time-jupiter-<moon> handlers above. All 11 Saturnians use this
        single helper (eliminates the per-moon `def _cmd_*` boilerplate).
        """
        def _impl(args):
            if args.sidereal_count is not None:
                return _emit(to_jd_fn(args.sidereal_count), pretty=args.pretty)
            return _emit_proper(jd_to_fn(args.jd), args)
        return _impl

    def _add_saturnian_subparser(name: str, body_label: str, abbrev: str,
                                  period_days: float, jd_to_fn, to_jd_fn):
        p = sub.add_parser(
            f"time-saturn-{name}",
            help=f"Sol Saturn-{body_label} Time ({abbrev}) at a JD — anchored sidereal-cycle count",
            description=(
                f"Convert JD (TDB) to Sol Saturn-{body_label} Time ({abbrev}) —\n"
                f"anchored sidereal-cycle count for {body_label} since J2000.0.\n"
                f"\n"
                f"{body_label} is tidally locked to Saturn"
                + (" (rotation chaotic — orbital period referenced for cycle count)"
                   if name == "hyperion" else "") + ", so:\n"
                f"\n"
                f"  sidereal day = orbital period{' (= rotation period)' if name != 'hyperion' else ''}\n"
                f"               = {period_days:.6f} days\n"
                f"\n"
                f"Naming follows the moons-stuck-to-parent convention\n"
                f"(v0.9.1) with the v0.14.1 6-letter S<Planet2><Moon2>T\n"
                f"abbreviation pattern.\n"
                f"\n"
                f"Use --sidereal-count to invert."
            ),
            epilog=(
                f"Examples:\n"
                f"  ephemerides-spectral time-saturn-{name} --jd 2451545.0\n\n"
                f"  ephemerides-spectral time-saturn-{name} --sidereal-count 100"
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--jd", type=float, default=None,
                       help=f"JD (TDB) to convert to Sol Saturn-{body_label} Time")
        g.add_argument("--sidereal-count", dest="sidereal_count",
                       type=float, default=None,
                       help="Sidereal-cycle count (since J2000) to invert back to JD_TDB")
        _add_proper_flags(p)
        p.set_defaults(
            func=_cmd_time_saturn_make(jd_to_fn, to_jd_fn),
            subcommand_name=f"time-saturn-{name}",
        )
        return p

    _add_saturnian_subparser("mimas",      "Mimas",      "SSaMiT",   0.94242196,
                              bridge.jd_to_sol_saturn_mimas_time,
                              bridge.sol_saturn_mimas_time_to_jd)
    _add_saturnian_subparser("enceladus",  "Enceladus",  "SSaEnT",   1.37021785,
                              bridge.jd_to_sol_saturn_enceladus_time,
                              bridge.sol_saturn_enceladus_time_to_jd)
    _add_saturnian_subparser("tethys",     "Tethys",     "SSaTeT",   1.88780216,
                              bridge.jd_to_sol_saturn_tethys_time,
                              bridge.sol_saturn_tethys_time_to_jd)
    _add_saturnian_subparser("dione",      "Dione",      "SSaDiT",   2.73691500,
                              bridge.jd_to_sol_saturn_dione_time,
                              bridge.sol_saturn_dione_time_to_jd)
    _add_saturnian_subparser("rhea",       "Rhea",       "SSaRhT",   4.51821200,
                              bridge.jd_to_sol_saturn_rhea_time,
                              bridge.sol_saturn_rhea_time_to_jd)
    _add_saturnian_subparser("titan",      "Titan",      "SSaTiT",  15.94542100,
                              bridge.jd_to_sol_saturn_titan_time,
                              bridge.sol_saturn_titan_time_to_jd)
    _add_saturnian_subparser("hyperion",   "Hyperion",   "SSaHyT",  21.27660925,
                              bridge.jd_to_sol_saturn_hyperion_time,
                              bridge.sol_saturn_hyperion_time_to_jd)
    _add_saturnian_subparser("iapetus",    "Iapetus",    "SSaIaT",  79.32150000,
                              bridge.jd_to_sol_saturn_iapetus_time,
                              bridge.sol_saturn_iapetus_time_to_jd)
    _add_saturnian_subparser("phoebe",     "Phoebe",     "SSaPhT", 550.56463600,
                              bridge.jd_to_sol_saturn_phoebe_time,
                              bridge.sol_saturn_phoebe_time_to_jd)
    _add_saturnian_subparser("janus",      "Janus",      "SSaJaT",   0.69458200,
                              bridge.jd_to_sol_saturn_janus_time,
                              bridge.sol_saturn_janus_time_to_jd)
    _add_saturnian_subparser("epimetheus", "Epimetheus", "SSaEpT",   0.69423500,
                              bridge.jd_to_sol_saturn_epimetheus_time,
                              bridge.sol_saturn_epimetheus_time_to_jd)

    # ── v0.14.2 Sol Moon Times — 8 moons across 4 parent families.
    #
    # Generic helper for any moon under any parent — supersedes the
    # family-specific Galilean / Saturnian helpers above for the v0.14.2
    # additions. (The four pre-v0.14.2 helpers are kept to avoid
    # mass-rewriting existing PRs that didn't introduce the policy switch.)
    def _add_moon_subparser(parent_name: str, moon_name: str,
                             body_label: str, abbrev: str,
                             period_days: float,
                             jd_to_fn, to_jd_fn,
                             extra_note: str = ""):
        sub_name = f"time-{parent_name}-{moon_name}"
        parent_label = parent_name.capitalize()
        p = sub.add_parser(
            sub_name,
            help=f"Sol {parent_label}-{body_label} Time ({abbrev}) at a JD — anchored sidereal-cycle count",
            description=(
                f"Convert JD (TDB) to Sol {parent_label}-{body_label} Time ({abbrev}) —\n"
                f"anchored sidereal-cycle count for {body_label} since J2000.0.\n"
                f"\n"
                f"{body_label} is tidally locked to {parent_label}, so:\n"
                f"\n"
                f"  sidereal day = orbital period = rotation period\n"
                f"               = {period_days:.6f} days\n"
                f"\n"
                + (extra_note + "\n\n" if extra_note else "")
                + f"Naming follows the v0.14.1 6-letter S<Planet2><Moon2>T\n"
                f"convention; abbreviations are globally distinct across all\n"
                f"Sol Moon Times.\n"
                f"\n"
                f"Use --sidereal-count to invert."
            ),
            epilog=(
                f"Examples:\n"
                f"  ephemerides-spectral {sub_name} --jd 2451545.0\n\n"
                f"  ephemerides-spectral {sub_name} --sidereal-count 100"
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--jd", type=float, default=None,
                       help=f"JD (TDB) to convert to Sol {parent_label}-{body_label} Time")
        g.add_argument("--sidereal-count", dest="sidereal_count",
                       type=float, default=None,
                       help="Sidereal-cycle count (since J2000) to invert back to JD_TDB")
        _add_proper_flags(p)
        p.set_defaults(func=_make_moon_cmd(jd_to_fn, to_jd_fn),
                        subcommand_name=sub_name)
        return p

    # Mars (Phobos, Deimos)
    _add_moon_subparser(
        "mars", "phobos", "Phobos", "SMaPhT", 0.31891023,
        bridge.jd_to_sol_mars_phobos_time, bridge.sol_mars_phobos_time_to_jd,
        extra_note="Likely a captured asteroid (C/D-type spectral match).\n"
                   "Phobos's sidereal period is SHORTER than Mars's solar day,\n"
                   "so from Mars's surface Phobos rises in the WEST.",
    )
    _add_moon_subparser(
        "mars", "deimos", "Deimos", "SMaDeT", 1.26244000,
        bridge.jd_to_sol_mars_deimos_time, bridge.sol_mars_deimos_time_to_jd,
        extra_note="Likely a captured asteroid (C/D-type spectral match);\n"
                   "companion to Phobos. NOT in 4:1 mean-motion resonance\n"
                   "with Phobos despite the period ratio being ~3.96.",
    )

    # Jupiter inner regulars (Metis, Adrastea, Amalthea, Thebe)
    _add_moon_subparser(
        "jupiter", "metis", "Metis", "SJuMeT", 0.29478000,
        bridge.jd_to_sol_jupiter_metis_time, bridge.sol_jupiter_metis_time_to_jd,
        extra_note="Innermost known Jovian moon; ring-shepherd of Jupiter's\n"
                   "main ring (with Adrastea). Discovered in Voyager 2 imagery (1979).",
    )
    _add_moon_subparser(
        "jupiter", "adrastea", "Adrastea", "SJuAdT", 0.29826000,
        bridge.jd_to_sol_jupiter_adrastea_time, bridge.sol_jupiter_adrastea_time_to_jd,
        extra_note="Second ring-shepherd of Jupiter's main ring (with Metis).\n"
                   "Smallest Jovian inner regular by mean radius (~8 km).\n"
                   "Discovered in Voyager 2 imagery (1979).",
    )
    _add_moon_subparser(
        "jupiter", "amalthea", "Amalthea", "SJuAmT", 0.49817905,
        bridge.jd_to_sol_jupiter_amalthea_time, bridge.sol_jupiter_amalthea_time_to_jd,
        extra_note="Largest Jovian inner regular (radius ~84 km); distinctly\n"
                   "reddish color. Discovered by E. E. Barnard 1892 — the last\n"
                   "solar-system moon discovered by direct visual observation.",
    )
    _add_moon_subparser(
        "jupiter", "thebe", "Thebe", "SJuThT", 0.67451400,
        bridge.jd_to_sol_jupiter_thebe_time, bridge.sol_jupiter_thebe_time_to_jd,
        extra_note="Outermost Jovian inner regular; orbits between Amalthea and Io.\n"
                   "Discovered in Voyager 1 imagery (S. Synnott, 1979).",
    )

    # Uranus (Titania)
    _add_moon_subparser(
        "uranus", "titania", "Titania", "SUrTiT", 8.70586900,
        bridge.jd_to_sol_uranus_titania_time, bridge.sol_uranus_titania_time_to_jd,
        extra_note="Largest moon of Uranus (radius ~789 km); discovered by\n"
                   "William Herschel 1787. Currently the only Uranian moon in\n"
                   "the BODIES roster; Oberon, Umbriel, Ariel, Miranda are\n"
                   "queued for a future ship.\n"
                   "\n"
                   "NOTE: SUrTiT (Titania) and SSaTiT (Saturn's Titan) share\n"
                   "the `Ti` moon prefix — disambiguated by the parent prefix\n"
                   "(`Ur` vs `Sa`). Exactly the disambiguation the v0.14.1\n"
                   "6-letter abbreviation policy was designed to provide.",
    )

    # Neptune (Triton)
    _add_moon_subparser(
        "neptune", "triton", "Triton", "SNeTrT", 5.87685400,
        bridge.jd_to_sol_neptune_triton_time, bridge.sol_neptune_triton_time_to_jd,
        extra_note="Largest Neptunian moon (radius ~1353 km — bigger than\n"
                   "Pluto). RETROGRADE orbit — the only large moon in the\n"
                   "solar system that orbits its planet backward; strong\n"
                   "evidence Triton is a captured Kuiper Belt object.\n"
                   "\n"
                   "Tidal deceleration (because of the retrograde orbit) is\n"
                   "spiralling Triton INWARD; in ~3.6 Gyr it will cross\n"
                   "Neptune's Roche limit and become a ring system.\n"
                   "\n"
                   "Encoder convention: BODIES['triton'].period_days is\n"
                   "positive (omega = +2π/P for ALL bodies regardless of\n"
                   "prograde/retrograde direction; retrograde is metadata,\n"
                   "not a sign flip). Sol Time count proceeds positive-monotonically.",
    )

    # ── v0.15.0 — Remaining Uranian moons + Pluto-Charon ───────────────
    # Closes task `#86` (Sol Moon Times completion) for the IAU-major
    # roster: every classical moon now has a Sol Time wrapper.

    _add_moon_subparser(
        "uranus", "miranda", "Miranda", "SUrMiT", 1.41347925,
        bridge.jd_to_sol_uranus_miranda_time, bridge.sol_uranus_miranda_time_to_jd,
        extra_note="Smallest of Uranus's five major moons (radius ~236 km).\n"
                   "Discovered by Gerard Kuiper, 1948 — the only one of the\n"
                   "five not discovered in the 1700s-1800s. Voyager 2 (1986)\n"
                   "imaged 20 km cliffs (Verona Rupes — tallest known in the\n"
                   "solar system) and chaotic ridge-and-groove terrain.\n"
                   "\n"
                   "NOTE: SUrMiT (Miranda) vs SSaMiT (Saturn's Mimas) share\n"
                   "the `Mi` moon prefix — disambiguated by parent prefix.",
    )

    _add_moon_subparser(
        "uranus", "ariel", "Ariel", "SUrArT", 2.52037935,
        bridge.jd_to_sol_uranus_ariel_time, bridge.sol_uranus_ariel_time_to_jd,
        extra_note="Innermost classical Uranian moon (radius ~579 km).\n"
                   "Discovered by William Lassell, 1851. Brightest surface\n"
                   "(highest albedo) of the Uranian moons — extensive rift\n"
                   "valleys; possible cryovolcanic resurfacing.",
    )

    _add_moon_subparser(
        "uranus", "umbriel", "Umbriel", "SUrUmT", 4.14417500,
        bridge.jd_to_sol_uranus_umbriel_time, bridge.sol_uranus_umbriel_time_to_jd,
        extra_note="Second classical Uranian moon (radius ~585 km).\n"
                   "Discovered by William Lassell, 1851 (same night as\n"
                   "Ariel). Darkest surface (lowest albedo) of the Uranian\n"
                   "moons — primordial ice/rock without cryovolcanic refresh.",
    )

    _add_moon_subparser(
        "uranus", "oberon", "Oberon", "SUrObT", 13.46323907,
        bridge.jd_to_sol_uranus_oberon_time, bridge.sol_uranus_oberon_time_to_jd,
        extra_note="Outermost (and second-largest) Uranian classical moon\n"
                   "(radius ~761 km). Discovered by William Herschel, 1787\n"
                   "— same night as Titania. Heavily cratered surface; dark\n"
                   "patches on crater floors may be cryovolcanic deposits.\n"
                   "Longest sidereal period (13.463 d) of the major Uranian\n"
                   "roster.",
    )

    _add_moon_subparser(
        "pluto", "charon", "Charon", "SPlChT", 6.38723000,
        bridge.jd_to_sol_pluto_charon_time, bridge.sol_pluto_charon_time_to_jd,
        extra_note="Pluto's largest moon (radius ~606 km). Discovered by\n"
                   "Jim Christy, 1978. MUTUALLY tidally locked with Pluto —\n"
                   "both bodies show the same face to each other forever, the\n"
                   "only such 1:1:1 spin-orbit lock in the solar system.\n"
                   "\n"
                   "Mass ratio (Charon:Pluto ≈ 0.12) is the highest of any\n"
                   "moon-planet pair; the Pluto-Charon barycentre lies\n"
                   "OUTSIDE Pluto, which makes the pair more like a *binary\n"
                   "planet* than a planet-with-moon.\n"
                   "\n"
                   "Sidereal period = mutual rotation period = 6.387 d (the\n"
                   "synchronous lock collapses these into a single timescale).",
    )

    # ── v0.16.0 Tier-1 BODIES expansion (43 → 52) ────────────────────
    # Saturnian Lagrange trojans (4) — first L4/L5 entries in BODIES.

    _add_moon_subparser(
        "saturn", "telesto", "Telesto", "SSaTeT2", 1.88780216,
        bridge.jd_to_sol_saturn_telesto_time, bridge.sol_saturn_telesto_time_to_jd,
        extra_note="TETHYS L4 TROJAN. Discovered Smith / Reitsema /\n"
                   "Larson / Fountain 1980. Period IDENTICAL to Tethys's\n"
                   "(1.88780216 d) — the first L4 entry in BODIES. The\n"
                   "body-graph Laplacian acquires a multiplicity-2\n"
                   "eigenvalue at 2π/1.88780216 d⁻¹.\n"
                   "\n"
                   "NOTE: SSaTeT2 carries the suffix '2' to distinguish\n"
                   "from Tethys's existing SSaTeT (both share 'Te' as\n"
                   "the moon-prefix). First invocation of the suffix-\n"
                   "disambiguation policy from v0.14.1's roadmap.",
    )

    _add_moon_subparser(
        "saturn", "calypso", "Calypso", "SSaCaT", 1.88780216,
        bridge.jd_to_sol_saturn_calypso_time, bridge.sol_saturn_calypso_time_to_jd,
        extra_note="TETHYS L5 TROJAN. Discovered Pascu / Seidelmann /\n"
                   "Baum / Currie 1980. Period IDENTICAL to Tethys's;\n"
                   "forms an L4/L5 pair with Telesto.\n"
                   "\n"
                   "Mass ~10⁻¹² Earth — the trojan slot is a Lagrange-\n"
                   "point identity, not a mass argument.",
    )

    _add_moon_subparser(
        "saturn", "helene", "Helene", "SSaHeT", 2.73691500,
        bridge.jd_to_sol_saturn_helene_time, bridge.sol_saturn_helene_time_to_jd,
        extra_note="DIONE L4 TROJAN. Discovered Laques / Lecacheux 1980\n"
                   "(visually from the Pic du Midi during a Saturn ring-\n"
                   "plane crossing). Period IDENTICAL to Dione's\n"
                   "(2.73691500 d). Largest of the four Saturnian trojans\n"
                   "(radius ~17.5 km).",
    )

    _add_moon_subparser(
        "saturn", "polydeuces", "Polydeuces", "SSaPoT", 2.73691500,
        bridge.jd_to_sol_saturn_polydeuces_time, bridge.sol_saturn_polydeuces_time_to_jd,
        extra_note="DIONE L5 TROJAN. Discovered Murray et al. 2004\n"
                   "(Cassini imagery). Period IDENTICAL to Dione's; forms\n"
                   "an L4/L5 pair with Helene.\n"
                   "\n"
                   "Smallest body in the v0.16.0 ship (radius ~1.3 km) —\n"
                   "a 'moonlet' by most categorisations. Notable for an\n"
                   "unusually wide libration amplitude around L5 (~32°).",
    )

    # Jovian irregular moons (3).
    _add_moon_subparser(
        "jupiter", "himalia", "Himalia", "SJuHiT", 250.5662000,
        bridge.jd_to_sol_jupiter_himalia_time, bridge.sol_jupiter_himalia_time_to_jd,
        extra_note="Largest Jovian irregular moon (radius ~85 km).\n"
                   "Discovered C. D. Perrine 1904. Prograde, sits between\n"
                   "Callisto (16.7 d) and the long-period retrograde\n"
                   "captures Pasiphae/Sinope (743 / 759 d).\n"
                   "\n"
                   "Eponym of the Himalia group of irregular Jovian\n"
                   "satellites (Lysithea, Elara, Leda, Dia all share\n"
                   "similar orbital characteristics).",
    )

    _add_moon_subparser(
        "jupiter", "pasiphae", "Pasiphae", "SJuPaT", 743.6300000,
        bridge.jd_to_sol_jupiter_pasiphae_time, bridge.sol_jupiter_pasiphae_time_to_jd,
        extra_note="Jovian RETROGRADE irregular (inclination ~141°).\n"
                   "Discovered P. J. Melotte 1908. Eponym of the Pasiphae\n"
                   "group of retrograde captures.\n"
                   "\n"
                   "Encoder convention: BODIES['pasiphae'].period_days is\n"
                   "positive (omega = +2π/P for ALL bodies regardless of\n"
                   "orbital direction; retrograde-ness is metadata, not\n"
                   "a sign flip). Same convention as Triton (v0.14.2).",
    )

    _add_moon_subparser(
        "jupiter", "sinope", "Sinope", "SJuSiT", 758.9000000,
        bridge.jd_to_sol_jupiter_sinope_time, bridge.sol_jupiter_sinope_time_to_jd,
        extra_note="Jovian RETROGRADE irregular (inclination ~153°).\n"
                   "Discovered S. B. Nicholson 1914. Member of the\n"
                   "Pasiphae group; near-resonant with Pasiphae itself\n"
                   "(orbital periods differ by ~2%).\n"
                   "\n"
                   "Encoder convention same as Pasiphae: positive\n"
                   "period_days, retrograde metadata-only.",
    )

    # Neptunian sub-graph completion (2).
    _add_moon_subparser(
        "neptune", "proteus", "Proteus", "SNePrT", 1.12231500,
        bridge.jd_to_sol_neptune_proteus_time, bridge.sol_neptune_proteus_time_to_jd,
        extra_note="Neptune's SECOND-largest moon (radius ~210 km, near-\n"
                   "spherical despite sitting below the canonical\n"
                   "hydrostatic-equilibrium threshold for icy bodies).\n"
                   "Discovered Voyager 2 imagery 1989. Period 1.122 d —\n"
                   "fills the Neptune sub-graph between Triton (5.88 d)\n"
                   "and the inner-Neptunian close-packed cluster.\n"
                   "\n"
                   "Surface dominated by the giant Pharos crater (radius\n"
                   "~75 km, ~13× the moon's radius — a near-fatal impact).",
    )

    _add_moon_subparser(
        "neptune", "nereid", "Nereid", "SNeNeT", 360.13619000,
        bridge.jd_to_sol_neptune_nereid_time, bridge.sol_neptune_nereid_time_to_jd,
        extra_note="Neptune's THIRD-largest moon (radius ~170 km).\n"
                   "Discovered G. P. Kuiper 1949. Period 360.13 d —\n"
                   "almost exactly one terrestrial year (numerical\n"
                   "coincidence, not a resonance).\n"
                   "\n"
                   "Eccentricity 0.749, the HIGHEST of any major moon in\n"
                   "the solar system. Likely captured asteroid/KBO with\n"
                   "post-capture orbit pumped by chaotic libration with\n"
                   "Triton. The 360-day period extends Neptune's low-\n"
                   "frequency tail dramatically (before v0.16.0 the\n"
                   "longest Neptunian period was Triton's 5.88 d).",
    )

    # time-proper (v0.11.0) — Sol Proper Time standalone rate-only query
    _SPRT_BODY_CHOICES = sorted(SUPPORTED_BODIES)
    tprop = sub.add_parser(
        "time-proper",
        help="Sol Proper Time (SPrT) rate at a body, vs. TCB / TDB",
        description=(
            "Compute the leading-order proper-time rate for a body's\n"
            "surface clock relative to TCB (barycentric coordinate time).\n"
            "\n"
            "Two components, both positive (clocks tick slower):\n"
            "  - gr_surface       = GM/(R*c²)         (gravitational well)\n"
            "  - kinematic_orbital = v_orb²/(2c²)     (SR time dilation)\n"
            "\n"
            "rate = 1 - gr_surface - kinematic_orbital\n"
            "\n"
            "With --compare-to <body>, returns the rate ratio + drift per\n"
            "Earth-year between two bodies — the most intuitive number for\n"
            "human comparison.\n"
            "\n"
            "Complementary to the --proper flag on every other time-*\n"
            "subcommand (which APPLIES the correction to a Sol Time count).\n"
            "Same physics, different surface."
        ),
        epilog=(
            "Examples:\n"
            "  # Mars surface vs. TCB — 3.38e-9 fractional rate (clocks slower).\n"
            "  ephemerides-spectral time-proper --body mars\n\n"
            "  # Sun surface — biggest dilation in the roster.\n"
            "  ephemerides-spectral time-proper --body sun\n\n"
            "  # Compare two bodies — Mars vs Terra: ~0.071 s/Earth-year.\n"
            "  ephemerides-spectral time-proper --body mars --compare-to terra\n\n"
            "  # With (lat, lon) — forward-compat for J2 oblateness (v0.11.0 ignores).\n"
            "  ephemerides-spectral time-proper --body terra --lat 51.5 --lon -0.1"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tprop.add_argument("--body", required=True, choices=_SPRT_BODY_CHOICES,
                       help="Body to query.")
    tprop.add_argument("--compare-to", dest="compare_to", default=None,
                       choices=_SPRT_BODY_CHOICES,
                       help="If set, return the rate ratio + drift "
                            "between --body and this body.")
    tprop.add_argument("--lat", type=float, default=None,
                       help="Surface latitude in degrees (forward-compat; "
                            "v0.11.0 ignores).")
    tprop.add_argument("--lon", type=float, default=None,
                       help="Surface longitude in degrees (forward-compat; "
                            "v0.11.0 ignores).")
    tprop.add_argument("--reference", choices=("tcb", "tdb"), default="tcb",
                       help="Reference time scale (default 'tcb').")
    tprop.set_defaults(func=_cmd_time_proper)

    # kinematics (v0.12.0) — Sol Kinematics standalone subcommand
    kine = sub.add_parser(
        "kinematics",
        help="Sol Kinematics — orbital state for one body or the full system",
        description=(
            "Compute mean orbital kinematic state — semi-major axis,\n"
            "orbital velocity, kinetic energy, angular momentum — for a\n"
            "single body or the full 52-body roster.\n"
            "\n"
            "v0.12.0 implements the circular-orbit Kepler-mean approximation\n"
            "from Kepler's third law (same math as `proper_time.py`'s\n"
            "kinematic-dilation term). Eccentricity / inclination corrections\n"
            "ship as v0.12.x refinements; per-JD evolution + force vectors +\n"
            "energy budgets ship as v0.13.0 *Dynamics*.\n"
            "\n"
            "Mirror of chess-spectral's `qm_2d.py`/`qm_4d.py` *kinematics*\n"
            "layer — static observables, no time-evolution.\n"
            "\n"
            "Validated against published NASA fact-sheet velocities for\n"
            "Mercury / Earth / Mars / Jupiter / Pluto to within 0.02-1.1 %\n"
            "and the Solar-System angular-momentum decomposition (Jupiter\n"
            "holds ~61 %; outer planets hold ~99.84 % of planet total)."
        ),
        epilog=(
            "Examples:\n"
            "  # Mars's mean orbital state\n"
            "  ephemerides-spectral kinematics --body mars\n\n"
            "  # Full system at J2000 with totals\n"
            "  ephemerides-spectral kinematics --all\n\n"
            "  # Specific JD (currently no-op — v0.12.0 uses mean elements)\n"
            "  ephemerides-spectral kinematics --body terra --jd 2451545.0\n\n"
            "  # Pair-centric frame (moons; v0.12.0 same elements as default)\n"
            "  ephemerides-spectral kinematics --body luna --frame parent_centric"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    kine.add_argument("--body", choices=_BODY_CHOICES, default=None,
                      help="Body to query (omit if using --all).")
    kine.add_argument("--all", action="store_true",
                      help="Return state for every body in the 38-body "
                           "roster, plus system-level totals.")
    kine.add_argument("--jd", type=float, default=None,
                      help="JD (TDB) — accepted for forward compat; "
                           "v0.12.0 uses mean orbital elements regardless.")
    kine.add_argument("--frame",
                      choices=("heliocentric_ecliptic", "parent_centric"),
                      default="heliocentric_ecliptic",
                      help="Reference frame (default 'heliocentric_ecliptic').")
    kine.set_defaults(func=_cmd_kinematics)

    # dynamics (v0.13.0) — Sol Dynamics standalone subcommand
    dyn = sub.add_parser(
        "dynamics",
        help="Sol Dynamics — system energy budget, per-body energies, or pair forces",
        description=(
            "Three query modes selected by which flags you pass:\n"
            "\n"
            "  default       System aggregate: total KE + PE + total E,\n"
            "                is_bound, angular-momentum partitions\n"
            "                (Jupiter holds ~61.5%, outer planets ~99.84%).\n"
            "\n"
            "  --body X      That body's energy budget: KE + PE + total E.\n"
            "                Heliocentric PE for Sol-orbiting bodies;\n"
            "                parent-centric PE for moons.\n"
            "\n"
            "  --body X --from Y\n"
            "                Newtonian gravitational force ON body X FROM body Y.\n"
            "                v0.13.0 reports magnitude only; 3D vectors\n"
            "                queued for v0.13.x with the position decoder.\n"
            "\n"
            "Mirror of chess-spectral's `qm_*_dynamics.py` *dynamics*\n"
            "layer — Hamiltonian + evolution + force / energy queries.\n"
            "Counterpart to v0.12.0's Sol Kinematics.\n"
            "\n"
            "Validated against published Solar-System totals: total\n"
            "energy < 0 (system bound), Earth-Sun force ≈ 3.54e22 N at\n"
            "1 AU, Sun KE / Mc² ≈ 8.6e-16."
        ),
        epilog=(
            "Examples:\n"
            "  # System totals\n"
            "  ephemerides-spectral dynamics\n\n"
            "  # Mars's energy budget\n"
            "  ephemerides-spectral dynamics --body mars\n\n"
            "  # Force on Mars from Jupiter\n"
            "  ephemerides-spectral dynamics --body mars --from jupiter\n\n"
            "  # Earth-Sun force (validation reference)\n"
            "  ephemerides-spectral dynamics --body terra --from sun"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    dyn.add_argument("--body", choices=_BODY_CHOICES, default=None,
                     help="Body to query (omit for system aggregate).")
    dyn.add_argument("--from", dest="from_body",
                     choices=_BODY_CHOICES, default=None,
                     help="If set with --body, return force on body from this body.")
    dyn.add_argument("--jd", type=float, default=None,
                     help="JD (TDB) — accepted for forward compat; v0.13.0 "
                          "uses mean orbital elements regardless.")
    dyn.add_argument("--frame",
                     choices=("heliocentric_ecliptic", "parent_centric"),
                     default="heliocentric_ecliptic",
                     help="Reference frame (default 'heliocentric_ecliptic').")
    dyn.set_defaults(func=_cmd_dynamics)

    # find-tubes (v0.8.1) — ITN pathway / Lagrange-tube query
    ft = sub.add_parser(
        "find-tubes",
        help="ITN pathway query: enumerate Hohmann transfer windows in a JD range",
        description=(
            "Enumerate launch windows in [from-jd, to-jd] (TDB) for a\n"
            "Hohmann transfer from `--departure` to `--target`. Mirrors\n"
            "find-syzygies's discipline: closed-form synodic-period\n"
            "enumeration anchored at the Hohmann launch geometry, no\n"
            "encoder calls.\n"
            "\n"
            "First-cut implementation. Future versions add low-energy /\n"
            "heteroclinic-tube candidates under the same surface; the\n"
            "transfer_kind field reserves room for them ('hohmann' for\n"
            "now). The user-friendly framing: 'surfing the perturbations'\n"
            "via the Solar System's natural cyclic structure.\n"
            "\n"
            "References:\n"
            "  - Koon, Lo, Marsden, Ross 2011 (the canonical ITN text)\n"
            "  - Lo's Genesis spacecraft trajectory work (1997)"
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral find-tubes --from-jd 2451545.0 --to-jd 2470000.0 \\\n"
            "      --departure terra --target mars\n"
            "  # All Mars windows in J2000 + 50yr at default tight (3.6deg) threshold\n"
            "\n"
            "  ephemerides-spectral find-tubes --from-jd 2452000.0 --to-jd 2456000.0 \\\n"
            "      --departure terra --target jupiter --threshold 0.05\n"
            "  # Terra->Jupiter windows, looser 9deg threshold"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ft.add_argument("--from-jd", dest="from_jd", type=float, required=True,
                    help="Window start in JD (TDB)")
    ft.add_argument("--to-jd", dest="to_jd", type=float, required=True,
                    help="Window end in JD (TDB)")
    ft.add_argument("--departure", required=True,
                    help="Departure body name (e.g. terra, mars)")
    ft.add_argument("--target", required=True,
                    help="Target body name (e.g. mars, jupiter)")
    ft.add_argument("--threshold", type=float, default=0.02,
                    help="Phase residual cutoff in (0, 1]; |residual|/pi. "
                         "0.02 = ~3.6 deg tight; 0.05 = ~9 deg looser. "
                         "Default 0.02.")
    ft.add_argument("--max-candidates", dest="max_candidates",
                    type=int, default=1000,
                    help="Max candidates returned (safety cap)")
    ft.set_defaults(func=_cmd_find_tubes)

    # find-chains (v0.17.0) — multi-leg ITN chain search
    fc = sub.add_parser(
        "find-chains",
        help="Multi-leg ITN chain search: Dijkstra graph search over Hohmann legs",
        description=(
            "Enumerate optimal-Δv multi-leg chains from `--departure`\n"
            "to `--target` in [from-jd, to-jd] (TDB), using closed-form\n"
            "Hohmann windows from find-tubes as edges in a graph search\n"
            "over the (body, epoch) state space. Each leg carries a\n"
            "small-integer (p, q) gear-ratio resonance signature -- the\n"
            "cross-pollination point with the BIP cyclic-group encoder.\n"
            "\n"
            "Closed-form throughout (no CR3BP integrator). Stays in the\n"
            "integer-ALU + FPU pipeline discipline. The search is\n"
            "Dijkstra-style with cumulative Δv as the priority metric,\n"
            "so the first chain emitted is the optimal-Δv chain.\n"
            "\n"
            "Pass --intermediates to constrain the allowed via-bodies\n"
            "(comma-separated list of body names). Empty string forces\n"
            "a single-leg direct chain (which should match find-tubes\n"
            "exactly for the same threshold). Default: all heliocentric\n"
            "bodies in BODIES.\n"
            "\n"
            "Cassini's V-V-E-J-S sequence has 5 legs; default --max-legs 4\n"
            "covers most named missions. Apollo-class direct transfers\n"
            "are 1 leg; Voyager grand tour is 4 legs; Galileo V-E-E-J\n"
            "is 4 legs.\n"
            "\n"
            "References:\n"
            "  - Koon, Lo, Marsden, Ross 2011 (canonical ITN text)\n"
            "  - Murray & Dermott 1999 §3 (resonance dynamics)\n"
            "  - Chirikov 1979 (resonance overlap)"
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral find-chains --from-jd 2451545.0 \\\n"
            "      --to-jd 2470000.0 --departure terra --target jupiter\n"
            "  # Find all multi-leg paths to Jupiter, default budgets\n"
            "\n"
            "  ephemerides-spectral find-chains --from-jd 2451545.0 \\\n"
            "      --to-jd 2480000.0 --departure terra --target pluto \\\n"
            "      --dv-budget-kms 25 --max-legs 5\n"
            "  # Earth->Pluto under 25 km/s, allow up to 5 legs\n"
            "\n"
            "  ephemerides-spectral find-chains --from-jd 2451545.0 \\\n"
            "      --to-jd 2470000.0 --departure terra --target jupiter \\\n"
            "      --intermediates venus,mars\n"
            "  # Restrict via-bodies to Venus + Mars (Galileo-class)\n"
            "\n"
            "  ephemerides-spectral find-chains --from-jd 2451545.0 \\\n"
            "      --to-jd 2470000.0 --departure terra --target mars \\\n"
            "      --intermediates ''\n"
            "  # Force single-leg direct chain (same as find-tubes)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    fc.add_argument("--from-jd", dest="from_jd", type=float, required=True,
                    help="Start of search window in JD (TDB)")
    fc.add_argument("--to-jd", dest="to_jd", type=float, required=True,
                    help="End of search window in JD (TDB)")
    fc.add_argument("--departure", type=str, required=True,
                    help="Departure body name (e.g. terra)")
    fc.add_argument("--target", type=str, required=True,
                    help="Target body name (e.g. jupiter, pluto)")
    fc.add_argument("--intermediates", type=str, default=None,
                    help="Comma-separated allowed via-bodies. "
                         "Default: all heliocentric bodies. "
                         "Empty string ('') forces single-leg direct chain.")
    fc.add_argument("--max-legs", dest="max_legs", type=int, default=4,
                    help="Hard cap on legs per chain. Default 4 "
                         "(Cassini V-V-E-J-S = 5; Voyager grand tour = 4).")
    fc.add_argument("--dv-budget-kms", dest="dv_budget_kms",
                    type=float, default=30.0,
                    help="Cumulative-Δv ceiling in km/s. Default 30.0 "
                         "(loose; Earth->Pluto direct ~25 km/s leaves "
                         "room for one assist).")
    fc.add_argument("--tof-budget-days", dest="tof_budget_days",
                    type=float, default=365.25 * 20.0,
                    help="Cumulative time-of-flight ceiling in days. "
                         "Default 7305 (20 yr).")
    fc.add_argument("--threshold", type=float, default=0.05,
                    help="Per-leg phase residual cutoff in (0, 1]. "
                         "Default 0.05 (~9 deg, looser than find-tubes "
                         "default since multi-leg search wants more "
                         "candidate windows per node).")
    fc.add_argument("--max-chains", dest="max_chains", type=int, default=200,
                    help="Cap on chains returned (Dijkstra emits "
                         "lowest-Δv first)")
    fc.add_argument("--max-intermediate-windows",
                    dest="max_intermediate_windows", type=int, default=8,
                    help="Per-(body, epoch) cap on enumerated next-leg "
                         "windows. Keeps multi-decade horizons tractable.")
    fc.set_defaults(func=_cmd_find_chains)

    # body-architecture (v0.18.0) — resonance-weighted gateway-graph
    # Laplacian Fiedler partition (inner/outer system classification).
    ba = sub.add_parser(
        "body-architecture",
        help="Inner/outer architectural classification of heliocentric bodies",
        description=(
            "Computes the Fiedler partition of the resonance-weighted\n"
            "gateway-graph Laplacian on the v0.16.0 13-body heliocentric\n"
            "Tier-1 roster (planets + main-belt asteroids). The partition\n"
            "cleanly bipartitions the roster on the asteroid-belt\n"
            "boundary: outer 5 = jupiter / saturn / uranus / neptune /\n"
            "pluto; inner 8 = mercury / venus / terra / mars / vesta /\n"
            "ceres / pallas / hygiea. The cyclic-group encoder discovers\n"
            "the canonical inner/outer system division without being\n"
            "told it exists -- Pluto and Neptune share the deepest\n"
            "negative Fiedler entry via their well-known 2:3 mean-motion\n"
            "lock. Background: research notebook section 13.8.\n"
            "\n"
            "Examples:\n"
            "  # Full partition (all 13 bodies)\n"
            "  ephemerides-spectral body-architecture\n"
            "\n"
            "  # Single-body class lookup\n"
            "  ephemerides-spectral body-architecture --target terra\n"
            "  ephemerides-spectral body-architecture --target pluto"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ba.add_argument(
        "--target", default=None,
        help="Body name (lower-case). If omitted, returns the full "
             "inner/outer partition; if given, returns just that "
             "body's record."
    )
    ba.set_defaults(func=_cmd_body_architecture)

    # predict-itn-accessibility (v0.18.1) — closed-form spectral Δv
    # estimate from the §13.9 hybrid Fiedler distance.
    pa = sub.add_parser(
        "predict-itn-accessibility",
        help="Closed-form spectral Δv estimate (fast first-pass triage)",
        description=(
            "Predicts the minimum cumulative Δv for a multi-leg ITN\n"
            "chain between two heliocentric bodies. Uses the §13.9\n"
            "hybrid (inv_dv x resonance) gateway-graph Laplacian\n"
            "Fiedler distance, calibrated against ground truth from\n"
            "v0.17.0 find-chains via OLS linear regression\n"
            "(Spearman rho = +0.857; LOOCV MAE ~ 4.2 km/s).\n"
            "\n"
            "Use case: fast first-pass TRIAGE before calling the\n"
            "costly find-chains Dijkstra. Microseconds vs ~1.5 s for\n"
            "the full search.\n"
            "\n"
            "DO NOT use for trajectory design -- the absolute MAE is\n"
            "~4 km/s on a 2-28 km/s domain, useful for ranking pairs\n"
            "but too coarse for mission-budget purposes. For mission\n"
            "design, call find-chains for the full Dijkstra answer.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral predict-itn-accessibility \\\n"
            "    --departure terra --target mars\n"
            "\n"
            "  # Pretty-print\n"
            "  ephemerides-spectral predict-itn-accessibility \\\n"
            "    --departure terra --target jupiter --pretty\n"
            "\n"
            "Reference: research notebook section 13.9."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pa.add_argument("--departure", required=True,
                    help="Departure body (lower-case heliocentric name).")
    pa.add_argument("--target", required=True,
                    help="Target body (lower-case heliocentric name).")
    pa.set_defaults(func=_cmd_predict_itn_accessibility)

    # em-state (v0.19.0) — Sol Electromagnetic Instrument: per-body
    # state-at-epoch query (rotation phase, intrinsic dipole, etc.).
    es = sub.add_parser(
        "em-state",
        help="Per-body EM state at JD (rotation phase + dipole moment + ...)",
        description=(
            "Returns the per-body EM observables (intrinsic dipole\n"
            "moment, rotation phase advanced from J2000, synchrotron\n"
            "power, plasma source rate, photoelectric potential) for\n"
            "the 16-body Sol Electromagnetic roster at the requested JD.\n"
            "\n"
            "The Sol EM Instrument is a state-at-epoch query surface,\n"
            "not a BIP encoder — EM clocks (rotational, Carrington,\n"
            "solar cycle) don't form a low-order rational lattice with\n"
            "orbital periods, so the cyclic-group encoder discipline\n"
            "doesn't transplant. See research notebook section 16.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral em-state --jd-tdb 2451545.0 --pretty\n"
            "  ephemerides-spectral em-state --jd-tdb 2470000.0"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    es.add_argument("--jd-tdb", dest="jd_tdb", type=float, required=True,
                    help="Julian Date in TDB.")
    es.set_defaults(func=_cmd_em_state)

    # em-couplings (v0.19.0) — static catalog of pairwise EM couplings.
    ec = sub.add_parser(
        "em-couplings",
        help="Static catalog of pairwise EM couplings (Io flux tube etc.)",
        description=(
            "Returns the 7-entry catalog of significant pairwise EM\n"
            "couplings: Jupiter-Io flux tube (10^12 W headliner);\n"
            "Saturn-Enceladus plasma mass loading; Saturn-Titan\n"
            "induced magnetosphere; Sun-Earth IMF reconnection;\n"
            "Jupiter-Europa / Jupiter-Ganymede; Sun-asteroid radiation\n"
            "pressure. Each entry carries a source_key pointing into\n"
            "_research.em_instrument_data.SOURCES for citation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ec.set_defaults(func=_cmd_em_couplings)

    # em-architecture (v0.19.0) — magnetised/induced/unmagnetised partition.
    ea = sub.add_parser(
        "em-architecture",
        help="Magnetised / induced / unmagnetised classification of EM-roster bodies",
        description=(
            "Partitions the 16-body Sol EM roster into\n"
            "  magnetised   (intrinsic dipole significant; e.g. Earth, Jupiter)\n"
            "  induced      (subsurface ocean / ionosphere; e.g. Europa, Titan)\n"
            "  unmagnetised (negligible field; e.g. Mars, Luna)\n"
            "  star         (the Sun)\n"
            "\n"
            "Different partition than body_architecture (which classifies\n"
            "by orbital position via the resonance Fiedler partition).\n"
            "This partition is by intrinsic-field presence (lookup, not\n"
            "eigendecomposition).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral em-architecture --pretty\n"
            "  ephemerides-spectral em-architecture --target jupiter"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ea.add_argument("--target", default=None,
                    help="Body name (lower-case). If omitted, return the "
                         "full partition; if given, return just that body's "
                         "record.")
    ea.set_defaults(func=_cmd_em_architecture)

    # geodetic-state (v0.20.0) — Sol Geodetic Catalog: per-body
    # gravity + topography + interior records.
    gs = sub.add_parser(
        "geodetic-state",
        help="Per-body geodetic state (gravity multipoles + topography + interior)",
        description=(
            "Returns the per-body geodetic records for the Sol Geodetic\n"
            "Catalog roster: gravity multipole expansion (full Stokes\n"
            "coefficients for terrestrial bodies + the Moon; zonal-only\n"
            "J_n series for the gas + ice giants), topography / shape\n"
            "model metadata (DEMs / SARTopo / polyhedral models), and\n"
            "interior structure (radial density profiles, layered models,\n"
            "moment-of-inertia constraints).\n"
            "\n"
            "The Sol Geodetic Catalog is a state-lookup query surface,\n"
            "not a BIP encoder — solid-body geodetic observables are\n"
            "static parameters with no native rhythm (per section 17.4.1\n"
            "the rhythm-mismatch finding generalises across solid-body\n"
            "geodesy alongside magnetic multipoles and fluid-envelope\n"
            "channels). The cyclic-group encoder discipline does not\n"
            "transplant. See research notebook section 17.\n"
            "\n"
            "Every numeric value carries a source_key pointing into\n"
            "_research.geodetic_catalog_data.SOURCES for citation.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral geodetic-state --pretty\n"
            "  ephemerides-spectral geodetic-state --body mars --pretty\n"
            "  ephemerides-spectral geodetic-state --body jupiter"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gs.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, return the "
                         "full per-body catalog; if given, return just "
                         "that body's records.")
    gs.set_defaults(func=_cmd_geodetic_state)

    # geodetic-models (v0.20.0) — full catalog enumeration across all
    # three channels (gravity / topography / interior).
    gm = sub.add_parser(
        "geodetic-models",
        help="Full Sol Geodetic Catalog enumeration (every model in every channel)",
        description=(
            "Returns the full catalog enumeration: every gravity model,\n"
            "every topography model, every interior model across the\n"
            "complete body roster. Each entry carries a source_key\n"
            "pointing into _research.geodetic_catalog_data.SOURCES for\n"
            "citation, so users can verify the provenance of every\n"
            "numeric value."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gm.set_defaults(func=_cmd_geodetic_models)

    # geodetic-architecture (v0.20.0) — data-quality-tier partition
    # (HIGH / MEDIUM / LOW / NONE per section 17.1.6 convention).
    ga = sub.add_parser(
        "geodetic-architecture",
        help="Per-body data-quality tier (HIGH / MEDIUM / LOW / NONE)",
        description=(
            "Per-body data-quality-tier partition over the Sol Geodetic\n"
            "Catalog. Each body lands in HIGH / MEDIUM / LOW / NONE based\n"
            "on the median precision flag across its three channels\n"
            "(gravity / topography / interior). A body with HIGH gravity\n"
            "but LOW interior is summarised as MEDIUM.\n"
            "\n"
            "Different partition than body_architecture (orbital position\n"
            "via resonance Fiedler) and em_architecture (intrinsic-field\n"
            "presence). The geodetic partition classifies by published-\n"
            "data quality, not by physical body class.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral geodetic-architecture --pretty\n"
            "  ephemerides-spectral geodetic-architecture --target mars"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ga.add_argument("--target", default=None,
                    help="Body name (lower-case). If omitted, return the "
                         "full partition; if given, return just that body's "
                         "tier and per-channel flags.")
    ga.set_defaults(func=_cmd_geodetic_architecture)

    # magnetic-multipoles (v0.20.1) — Sol Magnetic Multipole Catalog:
    # per-body Schmidt-quasi-normalised internal-field expansion.
    mm = sub.add_parser(
        "magnetic-multipoles",
        help="Per-body internal-field spherical-harmonic expansion (Schmidt g_n^m / h_n^m, geomagnetic convention)",
        description=(
            "Returns the per-body internal-field Schmidt coefficients\n"
            "for the Sol Magnetic Multipole Catalog roster: Earth\n"
            "IGRF-13 (deg 13), Jupiter JRM33 (deg 18), Saturn Cao 2020\n"
            "(deg 14, axisymmetric), Mercury Thebault 2018 (deg 5,\n"
            "offset dipole), Uranus Holme & Bloxham AH5 (deg 3, Voyager-\n"
            "only), Neptune Holme & Bloxham O8 (deg 3, Voyager-only),\n"
            "Ganymede Kivelson 2002 (dipole-only -- the only solar-\n"
            "system moon with a confirmed intrinsic dipole).\n"
            "\n"
            "The Sol Magnetic Multipole Catalog is a state-lookup\n"
            "query surface, not a BIP encoder -- per section 17.4.1\n"
            "the rhythm-mismatch finding generalises across magnetic\n"
            "multipoles alongside solid-body geodesy and fluid-envelope\n"
            "channels: internal-field Schmidt coefficients are static\n"
            "at their epoch, so the cyclic-group encoder discipline\n"
            "does not transplant. See research notebook section 17.\n"
            "\n"
            "Every numeric value carries a source_key pointing into\n"
            "_research.magnetic_multipole_catalog_data.SOURCES for\n"
            "citation.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral magnetic-multipoles --pretty\n"
            "  ephemerides-spectral magnetic-multipoles --body terra --crustal --pretty\n"
            "  ephemerides-spectral magnetic-multipoles --body jupiter"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mm.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, return the "
                         "full per-body catalog.")
    mm.add_argument("--crustal", action="store_true",
                    help="Include crustal anomaly model where available "
                         "(Earth EMM2017 only in v0.20.1; ~30 MB lazy-load).")
    mm.set_defaults(func=_cmd_magnetic_multipoles)

    # magnetic-field (v0.20.1) — vector field at (r, lat, lon).
    mf = sub.add_parser(
        "magnetic-field",
        help="Vector magnetic field at (r, lat, lon) via Schmidt dipole synthesis",
        description=(
            "Closed-form Schmidt-quasi-normalised dipole synthesis from\n"
            "the per-body multipole expansion. Returns spherical\n"
            "components (B_r, B_theta, B_phi) and total magnitude in nT.\n"
            "\n"
            "v0.20.1 ships dipole-only synthesis (synthesis_degree=1),\n"
            "the dominant contribution beyond a few body-radii for every\n"
            "body in the roster. Higher-degree synthesis is left for a\n"
            "future minor version.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral magnetic-field --body terra \\\n"
            "    --r-km 7000 --lat-deg 0 --lon-deg 0 --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mf.add_argument("--body", required=True,
                    help="Body name (lower-case; must be in the "
                         "magnetic multipole roster).")
    mf.add_argument("--r-km", dest="r_km", type=float, required=True,
                    help="Radial distance from body centre, km. Must be > 0.")
    mf.add_argument("--lat-deg", dest="lat_deg", type=float, required=True,
                    help="Geocentric latitude, degrees, [-90, 90].")
    mf.add_argument("--lon-deg", dest="lon_deg", type=float, required=True,
                    help="Body-fixed longitude, degrees.")
    mf.add_argument("--jd-tdb", dest="jd_tdb", type=float, default=None,
                    help="Reserved for forward compatibility (secular "
                         "variation handling in a future minor version).")
    mf.set_defaults(func=_cmd_magnetic_field)

    # solar-synoptic (v0.20.1) — Sun pointer surface.
    ss = sub.add_parser(
        "solar-synoptic",
        help="Sun synoptic-state archive pointer (Stanford HMI / WSO)",
        description=(
            "Returns pointers into the published synoptic-magnetogram\n"
            "archives for the Sun (Stanford HMI / Wilcox Solar\n"
            "Observatory). The Sun's internal field is time-varying\n"
            "with a ~22-yr Hale cycle modulated by the ~11-yr sunspot\n"
            "cycle; a single static set of Schmidt coefficients is not\n"
            "the right representation, so the package ships pointers\n"
            "into Carrington-rotation-cadence external archives instead.\n"
            "\n"
            "If --jd-tdb is given, the response includes a\n"
            "coverage_status field: in_coverage / before_archive / future.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral solar-synoptic --pretty\n"
            "  ephemerides-spectral solar-synoptic --jd-tdb 2451545.0"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ss.add_argument("--jd-tdb", dest="jd_tdb", type=float, default=None,
                    help="Julian Date in TDB; if given, response carries "
                         "coverage_status flag relative to archive start year.")
    ss.set_defaults(func=_cmd_solar_synoptic)

    # magnetic-models (v0.20.1) — full catalog enumeration.
    mml = sub.add_parser(
        "magnetic-models",
        help="Full Sol Magnetic Multipole Catalog enumeration",
        description=(
            "Returns the full catalog enumeration: every main-field\n"
            "multipole model + every crustal field model + every solar\n"
            "synoptic reference. Each entry carries a source_key\n"
            "pointing into _research.magnetic_multipole_catalog_data.\n"
            "SOURCES for citation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mml.set_defaults(func=_cmd_magnetic_models)

    # magnetic-architecture (v0.20.1) — data-quality tier partition.
    mar = sub.add_parser(
        "magnetic-architecture",
        help="Per-body magnetic-channel data-quality tier (HIGH/MEDIUM/LOW/NONE)",
        description=(
            "Per-body data-quality-tier partition over the Sol Magnetic\n"
            "Multipole Catalog. Voyager-only models (Uranus, Neptune)\n"
            "are LOW; current-best models (Earth IGRF-13, Jupiter JRM33,\n"
            "Saturn Cao 2020) are HIGH; single-mission limited-coverage\n"
            "models (Mercury Thebault 2018, Ganymede Kivelson 2002)\n"
            "are MEDIUM. Bodies with a published crustal anomaly model\n"
            "carry a has_crustal flag (Earth EMM2017 only in v0.20.1).\n"
            "\n"
            "Different partition than geodetic-architecture (which\n"
            "tracks gravity + topography + interior). This one tracks\n"
            "the magnetic channel specifically.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral magnetic-architecture --pretty\n"
            "  ephemerides-spectral magnetic-architecture --target jupiter"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mar.add_argument("--target", default=None,
                     help="Body name (lower-case). If omitted, return the "
                          "full partition; if given, return just that "
                          "body's tier.")
    mar.set_defaults(func=_cmd_magnetic_architecture)

    # fluid-state (v0.20.2) — Sol Fluid Instrument: per-body climatology
    # + archive index + state-at-epoch coverage triage.
    fs = sub.add_parser(
        "fluid-state",
        help="Per-body fluid-envelope climatology + archive pointers + state-at-epoch coverage",
        description=(
            "Returns the per-body climatology summary + archive-pointer\n"
            "index + state-at-epoch coverage triage for the requested\n"
            "body. Earth (ERA5) and Mars (MCD v6.1) have full state-at-\n"
            "epoch coverage; all other bodies fall back to the\n"
            "climatological summary with explicit out-of-coverage notes.\n"
            "\n"
            "**No outbound network calls.** The package ships pointers +\n"
            "the climatological-summary fallback in a self-contained dict;\n"
            "consumers fetch the actual reanalysis field via the archive's\n"
            "own API (CDS-API for ERA5, the Python wrapper for MCD).\n"
            "\n"
            "The Sol Fluid Instrument is a state-lookup query surface,\n"
            "not a BIP encoder -- per section 17.4.1 the rhythm-mismatch\n"
            "finding generalises across fluid-envelope channels alongside\n"
            "solid-body geodesy and magnetic multipoles. See research\n"
            "notebook section 17.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral fluid-state --pretty\n"
            "  ephemerides-spectral fluid-state --body terra --pretty\n"
            "  ephemerides-spectral fluid-state --body mars --jd-tdb 2451545.0\n"
            "  ephemerides-spectral fluid-state --body terra --lat 45 --lon 0"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    fs.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, return the "
                         "full per-body catalog.")
    fs.add_argument("--jd-tdb", dest="jd_tdb", type=float, default=None,
                    help="Julian Date in TDB; if given, response carries "
                         "coverage_status flag (in_coverage / before_archive / "
                         "future / no_state_at_epoch).")
    fs.add_argument("--lat", type=float, default=None,
                    help="Latitude (degrees). Reserved for spatial query "
                         "interface; currently passed through unchanged.")
    fs.add_argument("--lon", type=float, default=None,
                    help="Longitude (degrees). Same.")
    fs.set_defaults(func=_cmd_fluid_state)

    # fluid-archives (v0.20.2) — full archive enumeration.
    fa = sub.add_parser(
        "fluid-archives",
        help="Full Sol Fluid Instrument archive enumeration",
        description=(
            "Returns the full archive enumeration: every climatology\n"
            "entry, every archive pointer, every state-at-epoch coverage\n"
            "record. Each entry carries a source_key pointing into\n"
            "_research.fluid_instrument_data.SOURCES for citation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    fa.set_defaults(func=_cmd_fluid_archives)

    # fluid-architecture (v0.20.2) — data-quality tier partition.
    far = sub.add_parser(
        "fluid-architecture",
        help="Per-body fluid-channel data-quality tier (HIGH/MEDIUM/LOW/NONE)",
        description=(
            "Per-body data-quality-tier partition over the Sol Fluid\n"
            "Instrument. Bodies with state-at-epoch coverage carry a\n"
            "has_state_at_epoch flag (Earth ERA5 + Mars MCD only in\n"
            "v0.20.2); bodies with archive holdings carry an n_archives\n"
            "count.\n"
            "\n"
            "This is the fluid-channel sibling of geodetic-architecture\n"
            "(v0.20.0) and magnetic-architecture (v0.20.1) -- a fourth\n"
            "orthogonal data-quality classification axis.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral fluid-architecture --pretty\n"
            "  ephemerides-spectral fluid-architecture --target mars"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    far.add_argument("--target", default=None,
                     help="Body name (lower-case). If omitted, return the "
                          "full partition; if given, return just that "
                          "body's tier.")
    far.set_defaults(func=_cmd_fluid_architecture)

    # spherical-harmonics (v0.21.0) — unified gravity + magnetic query.
    sh = sub.add_parser(
        "spherical-harmonics",
        help="Unified per-body spherical-harmonic query (gravity + magnetic)",
        description=(
            "Per-body spherical-harmonic query, unified across the\n"
            "v0.20.0 gravity sector (Stokes coefficients in 4pi-norm)\n"
            "and the v0.20.1 magnetic sector (Schmidt-quasi-normalised\n"
            "g_n^m / h_n^m). Each returned record carries a\n"
            "normalisation_convention field so consumers know which\n"
            "convention to apply.\n"
            "\n"
            "This is a unification refactor, not a new data store --\n"
            "the v0.20.0 / v0.20.1 surfaces (geodetic-state /\n"
            "magnetic-multipoles) continue to work unchanged. Use this\n"
            "surface when you need both channels in one call.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral spherical-harmonics --body terra --pretty\n"
            "  ephemerides-spectral spherical-harmonics --body jupiter --channel magnetic\n"
            "  ephemerides-spectral spherical-harmonics --body mars --channel gravity"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sh.add_argument("--body", required=True,
                    help="Body name (lower-case).")
    sh.add_argument("--channel", default="both",
                    choices=["gravity", "magnetic", "both"],
                    help="Channel selector. Default 'both' returns "
                         "gravity + magnetic if available.")
    sh.set_defaults(func=_cmd_spherical_harmonics)

    # spherical-harmonic-models (v0.21.0) — full unified enumeration.
    shm = sub.add_parser(
        "spherical-harmonic-models",
        help="Full Sol Spherical Harmonic Catalog enumeration (gravity + magnetic merged)",
        description=(
            "Returns every gravity model + every magnetic model in the\n"
            "unified shape, plus the merged body union, the both-channels\n"
            "intersection subset, and the merged citation dict.\n"
            "\n"
            "Underlying canonical SOURCES dicts remain in\n"
            "_research.geodetic_catalog_data and\n"
            "_research.magnetic_multipole_catalog_data; this surface\n"
            "merges them for consumer convenience."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    shm.set_defaults(func=_cmd_spherical_harmonic_models)

    # convert-normalisation (v0.21.0) — Schmidt <-> 4pi-Stokes conversion helper.
    cn = sub.add_parser(
        "convert-normalisation",
        help="Convert one spherical-harmonic coefficient between 4pi-Stokes and Schmidt-quasi-norm",
        description=(
            "Per Winch et al. (2005) Geomagnetic Reference Spectra:\n"
            "\n"
            "  C_bar_nm = g_n^m / sqrt((2 - delta_0m) * (2n + 1))\n"
            "\n"
            "where delta_0m = 1 if m = 0 else 0.\n"
            "\n"
            "Schmidt -> 4pi-Stokes: divide by sqrt((2 - delta_0m)(2n+1))\n"
            "4pi-Stokes -> Schmidt: multiply.\n"
            "\n"
            "The conversion is purely algebraic; it does NOT cross\n"
            "between physical channels. For users who need to feed a\n"
            "gravity-side coefficient table into geomagnetic-convention\n"
            "software, or vice versa.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral convert-normalisation --value 0.001 \\\n"
            "    --n 2 --m 0 --from 4pi-Stokes --to Schmidt-quasi-norm\n"
            "  ephemerides-spectral convert-normalisation --value 30000 \\\n"
            "    --n 1 --m 0 --from Schmidt-quasi-norm --to 4pi-Stokes"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    cn.add_argument("--value", type=float, required=True,
                    help="Coefficient value to convert.")
    cn.add_argument("--n", type=int, required=True,
                    help="Spherical-harmonic degree (>= 0).")
    cn.add_argument("--m", type=int, required=True,
                    help="Spherical-harmonic order (0 <= m <= n).")
    cn.add_argument("--from", dest="from", required=True,
                    choices=["4pi-Stokes", "Schmidt-quasi-norm"],
                    help="Source convention.")
    cn.add_argument("--to", required=True,
                    choices=["4pi-Stokes", "Schmidt-quasi-norm"],
                    help="Target convention.")
    cn.set_defaults(func=_cmd_convert_normalisation)

    # admittance (v0.21.1) — topography <-> gravity admittance summary.
    ad = sub.add_parser(
        "admittance",
        help="Per-body topography <-> gravity admittance summary (cross-channel coupling)",
        description=(
            "Returns the published topography-gravity spectral\n"
            "admittance Z(n) summary for a body. For a body with both\n"
            "a gravity multipole expansion (v0.20.0) and a topography\n"
            "model (v0.20.0), Z(n) constrains crustal density and\n"
            "thickness via isostatic compensation theory.\n"
            "\n"
            "v0.21.1 ships the integrated Z summary published in the\n"
            "refereed literature; per-degree Z(n) tables remain in\n"
            "the cited paper's supplementary materials. Roster:\n"
            "terra (Wieczorek 2007), luna (Wieczorek 2013), mars\n"
            "(Genova 2016), mercury (James 2015), venus (Anderson 2002).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral admittance --pretty\n"
            "  ephemerides-spectral admittance --body luna --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ad.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, return "
                         "full catalog.")
    ad.set_defaults(func=_cmd_admittance)

    # admittance-spectra (v0.21.1) — full enumeration.
    ads = sub.add_parser(
        "admittance-spectra",
        help="Full topography-gravity admittance catalog enumeration",
        description=(
            "Returns every body's AdmittanceSpectrum record + the\n"
            "merged SOURCES citation dict so consumers can verify\n"
            "the provenance of every Z(n) value."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ads.set_defaults(func=_cmd_admittance_spectra)

    # dynamo-region (v0.21.2) — magnetic-multipole-derived dynamo radius.
    dr = sub.add_parser(
        "dynamo-region",
        help="Per-body dynamo-region constraint (cross-channel coupling)",
        description=(
            "Returns the per-body magnetic-multipole-derived\n"
            "dynamo-region constraint. For a body with a published\n"
            "spherical-harmonic magnetic-field expansion (v0.20.1),\n"
            "the Lowes-Mauersberger spectrum log-slope inverts\n"
            "directly for the dynamo radius:\n"
            "\n"
            "  R(n) ~ (R_dynamo / R_surface)^(2n + 4)\n"
            "\n"
            "For Earth this gives the canonical CMB depth ~2891 km\n"
            "(matches seismology to better than 1%). For Jupiter +\n"
            "Saturn it gives deep metallic-H dynamos. For Mercury, the\n"
            "standard inversion fails because of stable stratification;\n"
            "the depth comes from the Christensen 2006 weak-field model.\n"
            "\n"
            "5-body roster: terra (Lowes 1974), mercury (Christensen\n"
            "2006), jupiter (Connerney 2022), saturn (Cao 2020),\n"
            "ganymede (Schubert 1996).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral dynamo-region --pretty\n"
            "  ephemerides-spectral dynamo-region --body jupiter --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    dr.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, full "
                         "catalog.")
    dr.set_defaults(func=_cmd_dynamo_region)

    # dynamo-regions (v0.21.2) — full enumeration.
    drs = sub.add_parser(
        "dynamo-regions",
        help="Full dynamo-region catalog enumeration",
        description=(
            "Returns every body's DynamoRegion record + citation dict\n"
            "so consumers can verify the provenance of every dynamo-\n"
            "radius value."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    drs.set_defaults(func=_cmd_dynamo_regions)

    # orographic-forcing (v0.21.3) — topography -> atmospheric standing waves.
    of_ = sub.add_parser(
        "orographic-forcing",
        help="Per-body orographic-forcing summary (cross-channel coupling)",
        description=(
            "Returns the per-body topography -> atmospheric standing-\n"
            "wave forcing summary. For a body with both a topography\n"
            "model (v0.20.0) and an atmosphere (v0.20.2), surface\n"
            "topography acts as a lower-boundary forcing on the global\n"
            "circulation, generating downstream stationary Rossby\n"
            "waves with zero phase speed in the body-rotating frame.\n"
            "\n"
            "v0.21.3 ships the published GCM-derived decompositions;\n"
            "underlying spectral tables remain in the cited papers'\n"
            "supplementary materials. 4-body roster: terra (Tibetan\n"
            "Plateau forcer at k=2), mars (Tharsis bulge at k=2 to\n"
            "the mesopause -- the headline planetary case), venus\n"
            "(super-rotation suppresses classic stationary waves),\n"
            "titan (super-rotation; analogous to venus).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral orographic-forcing --pretty\n"
            "  ephemerides-spectral orographic-forcing --body mars --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    of_.add_argument("--body", default=None,
                     help="Body name (lower-case). If omitted, full "
                          "catalog.")
    of_.set_defaults(func=_cmd_orographic_forcing)

    # orographic-forcings (v0.21.3) — full enumeration.
    ofs = sub.add_parser(
        "orographic-forcings",
        help="Full orographic-forcing catalog enumeration",
        description=(
            "Returns every body's OrographicForcing record + citation\n"
            "dict so consumers can verify the provenance of every\n"
            "stationary-wave decomposition."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ofs.set_defaults(func=_cmd_orographic_forcings)

    # rotational-constraint (v0.21.4) — interior <-> rotation coupling.
    rc = sub.add_parser(
        "rotational-constraint",
        help="Per-body interior <-> rotation cross-channel constraint",
        description=(
            "Returns the per-body interior <-> rotation constraint.\n"
            "For a body with a published interior model (v0.20.0),\n"
            "the constraint connects interior structure (moment-of-\n"
            "inertia, core size, tidal viscosity) to observed\n"
            "rotational behaviour: free-core nutation (terra), InSight\n"
            "nutation (mars), zonal-wind depth (jupiter), ring-\n"
            "seismology rotation revision (saturn -- the headline:\n"
            "10h 39 -> 10h 33 from Mankovich & Fuller 2021), tidal\n"
            "dissipation Q (io/europa/ganymede via Lainey 2009/2020).\n"
            "\n"
            "v0.21.4 ships published constraint values; per-degree\n"
            "spectra remain in the cited papers' supplementary\n"
            "materials. 7-body roster.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral rotational-constraint --pretty\n"
            "  ephemerides-spectral rotational-constraint --body saturn --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    rc.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, full "
                         "catalog.")
    rc.set_defaults(func=_cmd_rotational_constraint)

    # rotational-constraints (v0.21.4) — full enumeration.
    rcs = sub.add_parser(
        "rotational-constraints",
        help="Full rotational-constraint catalog enumeration",
        description=(
            "Returns every body's RotationalConstraint record + the\n"
            "citation dict so consumers can verify the provenance of\n"
            "every constraint value."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    rcs.set_defaults(func=_cmd_rotational_constraints)

    # auroral-coupling (v0.21.5) — magnetic <-> atmosphere coupling.
    ac = sub.add_parser(
        "auroral-coupling",
        help="Per-body magnetic <-> atmosphere auroral coupling (cross-channel)",
        description=(
            "Returns the per-body magnetic <-> atmosphere auroral-\n"
            "coupling summary. Aurorae are the visible signature of\n"
            "magnetic-field-line topology mapping into the upper\n"
            "atmosphere; oval morphology traces internal-field geometry.\n"
            "\n"
            "6-body roster: terra (solar-wind reconnection, 10^11 W),\n"
            "jupiter (JRM33 + Io footprint; corotation-driven, 10^14 W\n"
            "-- the headline), saturn (annular oval traces Cao 2020\n"
            "axisymmetry), uranus (partial oval / extreme tilt),\n"
            "neptune (patchy time-variable, weakest in catalog),\n"
            "ganymede (only intrinsic-moon-dynamo aurora; subsurface\n"
            "ocean diagnostic via auroral rocking).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral auroral-coupling --pretty\n"
            "  ephemerides-spectral auroral-coupling --body jupiter --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ac.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, full "
                         "catalog.")
    ac.set_defaults(func=_cmd_auroral_coupling)

    # auroral-couplings (v0.21.5) — full enumeration.
    acs = sub.add_parser(
        "auroral-couplings",
        help="Full auroral-coupling catalog enumeration",
        description=(
            "Returns every body's AuroralCoupling record + the\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    acs.set_defaults(func=_cmd_auroral_couplings)

    # tidal-migration (v0.21.6) — tidal dissipation <-> orbital migration.
    tm = sub.add_parser(
        "tidal-migration",
        help="Per-pair tidal-dissipation <-> orbital-migration constraint",
        description=(
            "Returns per-pair tidal-migration rate. A satellite's\n"
            "tidal interaction with its parent body dissipates\n"
            "mechanical energy and transfers angular momentum; the\n"
            "secular semi-major-axis drift is the observable signature.\n"
            "\n"
            "6-pair roster: terra-luna (3.83 cm/yr outward, LLR), \n"
            "mars-phobos (-1.9 cm/yr inward, ~50 Myr Roche deadline),\n"
            "jupiter-io (3.6 cm/yr outward, Galilean Laplace 1:2:4\n"
            "EXPANDING -- Lainey 2009), saturn-titan (11 cm/yr outward,\n"
            "100x older estimates -- THE HEADLINE; Lainey 2020),\n"
            "neptune-triton (-0.5 cm/yr inward, retrograde + ~3.6 Gyr\n"
            "Roche), pluto-charon (locked, dual-synchronous binary --\n"
            "unique).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral tidal-migration --pretty\n"
            "  ephemerides-spectral tidal-migration --pair saturn-titan --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tm.add_argument("--pair", default=None,
                    help="Canonical 'parent-satellite' pair (e.g. "
                         "'saturn-titan'). If omitted, full catalog.")
    tm.set_defaults(func=_cmd_tidal_migration)

    # tidal-migrations (v0.21.6) — full enumeration.
    tms = sub.add_parser(
        "tidal-migrations",
        help="Full tidal-migration catalog enumeration",
        description=(
            "Returns every pair's TidalMigration record + the\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tms.set_defaults(func=_cmd_tidal_migrations)

    # atmospheric-escape (v0.21.7) — escape rate <-> magnetic shielding.
    ae = sub.add_parser(
        "atmospheric-escape",
        help="Per-body atmospheric escape <-> magnetic-shielding constraint",
        description=(
            "Returns per-body atmospheric escape rate + dominant\n"
            "mechanism + magnetic-shielding flag. Atmospheric escape\n"
            "depends critically on magnetic-field shielding: Earth +\n"
            "Jupiter deflect solar wind at magnetopause, retaining\n"
            "atmospheres; Mars + Venus are exposed and lose\n"
            "atmosphere over Gyr.\n"
            "\n"
            "6-body roster: terra (3 kg/s thermal, IGRF-shielded),\n"
            "mars (2 kg/s pickup-ion, NO shielding -- THE HEADLINE:\n"
            "lost 50%% of primordial CO2 over 4 Gyr; Jakosky 2018\n"
            "MAVEN), venus (0.4 kg/s pickup-ion despite no shield),\n"
            "mercury (0.01 kg/s sputtering exosphere), titan (30 kg/s\n"
            "hydrodynamic; highest absolute rate), jupiter (1000 kg/s\n"
            "Io plasma torus injection).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral atmospheric-escape --pretty\n"
            "  ephemerides-spectral atmospheric-escape --body mars --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ae.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, full "
                         "catalog.")
    ae.set_defaults(func=_cmd_atmospheric_escape)

    # atmospheric-escapes (v0.21.7) — full enumeration.
    aes = sub.add_parser(
        "atmospheric-escapes",
        help="Full atmospheric-escape catalog enumeration",
        description=(
            "Returns every body's AtmosphericEscape record + the\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    aes.set_defaults(func=_cmd_atmospheric_escapes)

    # heat-flow (v0.21.8) — heat flow <-> tidal heating coupling.
    hf = sub.add_parser(
        "heat-flow",
        help="Per-body surface heat-flow <-> tidal-heating decomposition",
        description=(
            "Returns per-body total surface heat flow + decomposition\n"
            "into tidal / radiogenic / primordial-cooling contributions.\n"
            "\n"
            "Cross-channel: v0.21.4 (tidal Q) + v0.21.6 (orbital\n"
            "migration) + v0.21.8 (heat flow) close the tidal-energy-\n"
            "budget loop. For Io, Q~80 + +3.6 cm/yr migration -> tidal\n"
            "power ~100 TW = observed surface heat flow.\n"
            "\n"
            "6-body roster: terra (47 TW radiogenic-dominated), mars\n"
            "(0.1 TW radiogenic-dominated, InSight), io (THE HEADLINE:\n"
            "100 TW = 99% tidal; most volcanically active body in solar\n"
            "system), europa (0.5 TW tidal-dominated; maintains\n"
            "subsurface ocean), enceladus (10 GW SP plumes; tidal-\n"
            "dominated; drives geyser system), titan (~2 TW; modest\n"
            "tidal contribution).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral heat-flow --pretty\n"
            "  ephemerides-spectral heat-flow --body io --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hf.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, full "
                         "catalog.")
    hf.set_defaults(func=_cmd_heat_flow)

    # heat-flows (v0.21.8) — full enumeration.
    hfs = sub.add_parser(
        "heat-flows",
        help="Full heat-flow catalog enumeration",
        description=(
            "Returns every body's HeatFlow record + the citation\n"
            "dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hfs.set_defaults(func=_cmd_heat_flows)

    # volcanic-outgassing (v0.21.9) — outgassing <-> atmosphere coupling.
    vo = sub.add_parser(
        "volcanic-outgassing",
        help="Per-body volcanic outgassing <-> atmospheric composition coupling",
        description=(
            "Returns per-body volcanic outgassing rate + dominant\n"
            "outgassed species + source mechanism.\n"
            "\n"
            "Cross-channel: v0.21.7 (escape) + v0.21.9 (outgassing)\n"
            "form the supply-and-demand sides of atmospheric mass\n"
            "balance. v0.21.8 (heat flow) provides the energy budget.\n"
            "\n"
            "6-body roster: terra (3 kg/s CO2 subaerial+submarine,\n"
            "balanced by silicate weathering NOT escape), mars\n"
            "(dormant; ~0 outgassing while v0.21.7 says 2 kg/s\n"
            "escape -> dead-planet story), venus (0.5 kg/s SO2 active\n"
            "hotspots), io (THE HEADLINE: 1 ton/s SO2 from tidal-\n"
            "driven volcanism, cross-references v0.21.8 100 TW),\n"
            "enceladus (200 kg/s H2O plume venting -> Saturn E-ring),\n"
            "jupiter (1000 kg/s S+/O+ via Io magnetospheric injection,\n"
            "matches v0.21.7 escape rate downstream).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral volcanic-outgassing --pretty\n"
            "  ephemerides-spectral volcanic-outgassing --body io --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    vo.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, full "
                         "catalog.")
    vo.set_defaults(func=_cmd_volcanic_outgassing)

    # volcanic-outgassings (v0.21.9) — full enumeration.
    vos = sub.add_parser(
        "volcanic-outgassings",
        help="Full volcanic-outgassing catalog enumeration",
        description=(
            "Returns every body's VolcanicOutgassing record + the\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    vos.set_defaults(func=_cmd_volcanic_outgassings)

    # thermal-balance (v0.21.10) — radiative equilibrium <-> observed T.
    tb = sub.add_parser(
        "thermal-balance",
        help="Per-body radiative-equilibrium <-> observed-temperature decomposition",
        description=(
            "Returns per-body Stefan-Boltzmann T_eq + observed T +\n"
            "decomposition into greenhouse / tidal / internal-heat\n"
            "contributions.\n"
            "\n"
            "T_eq = ((1 - A) * S / (4 * sigma))^(1/4) where S = solar\n"
            "flux and A = Bond albedo (v0.20.2 BodyClimatology).\n"
            "\n"
            "6-body roster: terra (+33.5 K greenhouse, canonical case),\n"
            "mars (~0 K, naked planet), venus (+505 K RUNAWAY GREENHOUSE),\n"
            "mercury (0 K, no atmosphere -> pure radiative balance),\n"
            "titan (+11 K CH4/N2 + tidal), jupiter (+45 K internal-heat\n"
            "dominated -- Jupiter radiates 1.7x what it absorbs).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral thermal-balance --pretty\n"
            "  ephemerides-spectral thermal-balance --body venus --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tb.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, full "
                         "catalog.")
    tb.set_defaults(func=_cmd_thermal_balance)

    # thermal-balances (v0.21.10) — full enumeration.
    tbs = sub.add_parser(
        "thermal-balances",
        help="Full thermal-balance catalog enumeration",
        description=(
            "Returns every body's ThermalBalance record + the\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tbs.set_defaults(func=_cmd_thermal_balances)

    # ──────────────────────────────────────────────────────────────────
    # v0.22.0 — Trajectory + Sensing Layer
    # ──────────────────────────────────────────────────────────────────

    # ballistic-trajectory (v0.22.0 Layer A)
    bt = sub.add_parser(
        "ballistic-trajectory",
        help="Per-body short-range ballistic-projectile propagator",
        description=(
            "v0.22.0 Layer A. Per-body short-range ballistic flight\n"
            "with optional exponential-atmosphere drag. Vacuum case\n"
            "is the textbook closed form (Vallado §8.6.2):\n"
            "  range = v² · sin(2θ) / g\n"
            "  apex  = v² · sin²(θ) / (2g)\n"
            "  T     = 2 v · sin(θ) / g\n"
            "\n"
            "With-drag case integrates RK4 under exponential\n"
            "atmosphere (BC = m/(C_d·A) parameterization).\n"
            "\n"
            "7-body roster: terra, mars, venus, titan (atmospheric);\n"
            "luna, mercury (vacuum); jupiter (1-bar reference).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral ballistic-trajectory --body terra "
            "--v 700 --angle 45 --pretty\n"
            "  ephemerides-spectral ballistic-trajectory --body mars "
            "--v 1000 --angle 30 --with-drag --bc 200 --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    bt.add_argument("--body", required=True,
                    help="Body name (lower-case): terra/mars/venus/titan/"
                         "luna/mercury/jupiter")
    bt.add_argument("--v", type=float, required=True,
                    help="Initial speed (m/s)")
    bt.add_argument("--angle", type=float, required=True,
                    help="Launch angle above local horizontal (deg, 0-90)")
    bt.add_argument("--altitude", type=float, default=0.0,
                    help="Initial altitude above surface (m). Default 0.")
    bt.add_argument("--with-drag", action="store_true",
                    help="Integrate with exponential-atmosphere drag.")
    bt.add_argument("--bc", type=float, default=None,
                    help="Ballistic coefficient BC=m/(C_d·A) (kg/m²). "
                         "Required when --with-drag.")
    bt.set_defaults(func=_cmd_ballistic_trajectory)

    # ballistic-atmosphere (v0.22.0 Layer A)
    ba = sub.add_parser(
        "ballistic-atmosphere",
        help="Per-body ballistic-atmosphere parameter lookup",
        description=(
            "Returns per-body surface gravity + radius +\n"
            "exponential-atmosphere parameters (ρ₀, H, top) used by\n"
            "the Layer A propagator."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ba.add_argument("--body", default=None,
                    help="Body name. If omitted, full catalog.")
    ba.set_defaults(func=_cmd_ballistic_atmosphere)

    # ballistic-atmospheres (v0.22.0 Layer A)
    bas = sub.add_parser(
        "ballistic-atmospheres",
        help="Full ballistic-atmosphere catalog enumeration",
        description=(
            "Returns every body's BallisticAtmosphere record + the\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    bas.set_defaults(func=_cmd_ballistic_atmospheres)

    # icbm-trajectory (v0.22.0 Layer B)
    it = sub.add_parser(
        "icbm-trajectory",
        help="Earth 3-regime ICBM trajectory (boost boundary + Kepler "
             "midcourse + Allen-Eggers re-entry)",
        description=(
            "v0.22.0 Layer B. Earth 3-regime ballistic missile\n"
            "trajectory propagator. Boost is a boundary condition\n"
            "(user supplies burnout state v, γ, h). Midcourse uses\n"
            "Kepler-ellipse (Bate-Mueller-White Ch. 6). Re-entry uses\n"
            "Allen-Eggers closed-form (NACA Report 1381, 1958).\n"
            "\n"
            "**Boost is intentionally not modelled** — vehicle-specific\n"
            "Isp/thrust/gravity-turn cross into operationally-sensitive\n"
            "territory; publishable Layer B starts from burnout state.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral icbm-trajectory --burnout-v 7000 "
            "--burnout-gamma 23 --bc 10000 --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    it.add_argument("--burnout-v", type=float, required=True,
                    help="Burnout velocity (m/s)")
    it.add_argument("--burnout-gamma", type=float, required=True,
                    help="Burnout flight-path angle above horizon (deg)")
    it.add_argument("--burnout-alt", type=float, default=200_000.0,
                    help="Burnout altitude (m). Default 200000.")
    it.add_argument("--bc", type=float, default=10000.0,
                    help="Re-entry ballistic coefficient (kg/m²). "
                         "Default 10000 (heavy compact RV).")
    it.set_defaults(func=_cmd_icbm_trajectory)

    # icbm-reference-profile (v0.22.0 Layer B)
    irp = sub.add_parser(
        "icbm-reference-profile",
        help="Textbook ICBM reference profile lookup (SRBM/MRBM/ICBM)",
        description=(
            "Returns canonical SRBM / MRBM / ICBM range-class profiles\n"
            "from Wilkening 2000 + Sessler/UCS 2000 — open-literature\n"
            "baselines, NOT operational parameters."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    irp.add_argument("--profile", default=None,
                     help="Profile name (srbm_300km/mrbm_1500km/"
                          "icbm_10000km). If omitted, full catalog.")
    irp.set_defaults(func=_cmd_icbm_reference_profile)

    # icbm-reference-profiles (v0.22.0 Layer B)
    irps = sub.add_parser(
        "icbm-reference-profiles",
        help="Full ICBM reference profile enumeration",
        description=(
            "Returns every reference profile + citations."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    irps.set_defaults(func=_cmd_icbm_reference_profiles)

    # visibility-geometry (v0.22.0 Layer C(a))
    vg = sub.add_parser(
        "visibility-geometry",
        help="Slant-range + look-angle + Earth-limb occlusion test",
        description=(
            "v0.22.0 Layer C(a). Geometric 'can a sensor see it?' from\n"
            "satellite ECEF position + target lat/lon. Returns slant\n"
            "range, elevation above target horizon, azimuth, and\n"
            "Earth-limb occlusion. Vallado Ch. 11."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    vg.add_argument("--sat-x", type=float, required=True,
                    help="Satellite ECEF x (m)")
    vg.add_argument("--sat-y", type=float, required=True,
                    help="Satellite ECEF y (m)")
    vg.add_argument("--sat-z", type=float, required=True,
                    help="Satellite ECEF z (m)")
    vg.add_argument("--lat", type=float, required=True,
                    help="Target geodetic latitude (deg)")
    vg.add_argument("--lon", type=float, required=True,
                    help="Target geodetic longitude (deg, east-positive)")
    vg.add_argument("--alt", type=float, default=0.0,
                    help="Target altitude above WGS-84 ellipsoid (m)")
    vg.add_argument("--min-elev", type=float, default=5.0,
                    help="Minimum elevation for visibility (deg). "
                         "Default 5.")
    vg.set_defaults(func=_cmd_visibility_geometry)

    # sgp4-state (v0.22.0 Layer C(a))
    s4 = sub.add_parser(
        "sgp4-state",
        help="SGP4/SDP4 TLE → ECI state vector",
        description=(
            "v0.22.0 Layer C(a). Propagate a TLE to the requested\n"
            "minutes-since-epoch using SGP4/SDP4. Requires\n"
            "ephemerides-spectral[ephemeris] for the sgp4 dependency."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    s4.add_argument("--line1", required=True, help="TLE line 1")
    s4.add_argument("--line2", required=True, help="TLE line 2")
    s4.add_argument("--minutes", type=float, default=0.0,
                    help="Minutes past TLE epoch. Default 0.")
    s4.set_defaults(func=_cmd_sgp4_state)

    # orbital-reference (v0.22.0 Layer C(a))
    orf = sub.add_parser(
        "orbital-reference",
        help="Reference TLE lookup (textbook samples; NOT a live catalog)",
        description=(
            "Returns reference TLEs for textbook orbit classes (LEO\n"
            "sun-sync, ISS, GEO, Molniya HEO, Tundra HEO, IRIDIUM-NEXT,\n"
            "Sentinel-1A, JPSS-1, Landsat-9). For operational use,\n"
            "fetch fresh TLEs from CelesTrak / Space-Track."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    orf.add_argument("--label", default=None,
                     help="Reference label. If omitted, full catalog.")
    orf.set_defaults(func=_cmd_orbital_reference)

    # orbital-references (v0.22.0 Layer C(a))
    orfs = sub.add_parser(
        "orbital-references",
        help="Full orbital reference TLE enumeration + IR window constants",
        description=(
            "Returns every reference TLE + atmospheric IR transmission\n"
            "windows (VIS / NIR / MWIR / LWIR) + citations."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    orfs.set_defaults(func=_cmd_orbital_references)

    # bc-differential (v0.22.0 Layer C(b))
    bd = sub.add_parser(
        "bc-differential",
        help="BC-differential velocity separation (decoy discrimination)",
        description=(
            "v0.22.0 Layer C(b). The only physics-based midcourse-\n"
            "surviving discriminator: heavy compact RV decelerates\n"
            "slowly in the upper atmosphere; light decoys decelerate\n"
            "rapidly. Allen-Eggers closed-form (NACA Report 1381,\n"
            "1958). Reference: Sessler/UCS Countermeasures 2000.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral bc-differential --bc-heavy 10000 "
            "--bc-light 50 --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    bd.add_argument("--bc-heavy", type=float, required=True,
                    help="Heavy object BC (kg/m²). Typical: 5000-15000")
    bd.add_argument("--bc-light", type=float, required=True,
                    help="Light object BC (kg/m²). Typical: 10-50")
    bd.add_argument("--v-entry", type=float, default=7000.0,
                    help="Re-entry velocity (m/s). Default 7000.")
    bd.add_argument("--gamma-entry", type=float, default=23.0,
                    help="Re-entry flight-path angle (deg). Default 23.")
    bd.add_argument("--lower-km", type=float, default=60.0,
                    help="Discrimination band lower altitude (km). "
                         "Default 60.")
    bd.add_argument("--upper-km", type=float, default=100.0,
                    help="Upper altitude (km). Default 100 (Karman line).")
    bd.set_defaults(func=_cmd_bc_differential)

    # discrimination-altitude (v0.22.0 Layer C(b))
    da = sub.add_parser(
        "discrimination-altitude",
        help="Find altitude where Δv exceeds threshold (BC pair)",
        description=(
            "Sweeps the discrimination band downward from re-entry\n"
            "interface and returns the highest altitude at which the\n"
            "BC-differential velocity gap exceeds the threshold."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    da.add_argument("--bc-heavy", type=float, required=True,
                    help="Heavy object BC (kg/m²)")
    da.add_argument("--bc-light", type=float, required=True,
                    help="Light object BC (kg/m²)")
    da.add_argument("--v-entry", type=float, default=7000.0,
                    help="Re-entry velocity (m/s). Default 7000.")
    da.add_argument("--gamma-entry", type=float, default=23.0,
                    help="Re-entry flight-path angle (deg). Default 23.")
    da.add_argument("--threshold", type=float, default=100.0,
                    help="Δv threshold (m/s). Default 100.")
    da.set_defaults(func=_cmd_discrimination_altitude)

    # bc-reference-class (v0.22.0 Layer C(b))
    brc = sub.add_parser(
        "bc-reference-class",
        help="Reference BC class lookup (heavy_rv/light_rv/replica/chaff)",
        description=(
            "Returns canonical BC class baselines from Sessler/UCS 2000\n"
            "Table 8.1. NOT specific weapon-system parameters."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    brc.add_argument("--class-name", default=None,
                     help="Class name (heavy_rv/light_rv/replica_decoy/"
                          "chaff_decoy). If omitted, full catalog.")
    brc.set_defaults(func=_cmd_bc_reference_class)

    # bc-reference-classes (v0.22.0 Layer C(b))
    brcs = sub.add_parser(
        "bc-reference-classes",
        help="Full BC reference-class enumeration + citations",
        description=(
            "Returns every reference BC class + citations."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    brcs.set_defaults(func=_cmd_bc_reference_classes)

    # ──────────────────────────────────────────────────────────────────
    # v0.23.0 — Spin-orbit resonance ↔ rotation lock
    # ──────────────────────────────────────────────────────────────────

    # spin-orbit-resonance (v0.23.0)
    sor = sub.add_parser(
        "spin-orbit-resonance",
        help="Per-body spin-orbit resonance ratio + libration amplitude",
        description=(
            "v0.23.0 — eleventh cross-channel coupling surface\n"
            "(resumed after v0.22.0 trajectory pivot). Returns the\n"
            "integer (p, q) spin-orbit ratio + rotation period +\n"
            "orbital period + libration amplitude for each body.\n"
            "\n"
            "Mercury is the only non-1:1 spin-orbit resonance in the\n"
            "Solar System: 3:2 (Pettengill 1965 / Margot 2007). All\n"
            "other entries are 1:1 tidal locks (Luna canonical;\n"
            "Galileans; Titan with anomalous libration -> subsurface\n"
            "ocean; Triton retrograde; Pluto-Charon dual-synchronous).\n"
            "\n"
            "Closes the tidal-physics triple with v0.21.4 (Q-factor)\n"
            "+ v0.21.6 (orbital migration).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral spin-orbit-resonance --pretty\n"
            "  ephemerides-spectral spin-orbit-resonance --body mercury "
            "--pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sor.add_argument("--body", default=None,
                     help="Body name (lower-case). If omitted, full "
                          "catalog.")
    sor.set_defaults(func=_cmd_spin_orbit_resonance)

    # spin-orbit-resonances (v0.23.0)
    sors = sub.add_parser(
        "spin-orbit-resonances",
        help="Full spin-orbit resonance catalog enumeration",
        description=(
            "Returns every body's SpinOrbitResonance record + the\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sors.set_defaults(func=_cmd_spin_orbit_resonances)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.0 — Mercury Dynamical Spectrum
    # ──────────────────────────────────────────────────────────────────

    # mercury-dynamical-spectrum
    mds = sub.add_parser(
        "mercury-dynamical-spectrum",
        help="Mercury's full action-angle dynamical-mode catalog",
        description=(
            "v0.24.0 — first per-body dynamical-spectrum surface.\n"
            "Decomposes Mercury's dynamical state into angle variables\n"
            "(orbital phase, spin phase, perihelion longitude,\n"
            "ascending node) and action variables (semi-major axis,\n"
            "eccentricity, inclination, obliquity).\n"
            "\n"
            "Mercury chosen as cleanest first target: no moon, no\n"
            "atmosphere, no ocean; in the historically richest\n"
            "dynamical-test position (Le Verrier 1859 -> Einstein 1915\n"
            "-> Clemence 1947 -> Margot 2007 -> Park 2017).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral mercury-dynamical-spectrum --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mds.set_defaults(func=_cmd_mercury_dynamical_spectrum)

    # mercury-precession-decomposition (THE headline)
    mpd = sub.add_parser(
        "mercury-precession-decomposition",
        help="Mercury perihelion-precession contribution-by-perturber breakdown",
        description=(
            "v0.24.0 headline. Total observed 574.10 arcsec/century\n"
            "(Clemence 1947) decomposes as:\n"
            "  Newtonian planetary perturbations  531.63\n"
            "    Venus           277.42\n"
            "    Jupiter         153.58\n"
            "    Earth            90.04\n"
            "    Saturn            7.30\n"
            "    Mars + other      3.29\n"
            "  General relativity (Einstein 1915)  42.98\n"
            "  Solar quadrupole J2 (Park 2017)      0.025\n"
            "  Sum                                ~574.6  matches\n"
            "\n"
            "The Le Verrier / Einstein test of GR; one of the most\n"
            "precise quantitative confirmations in physics.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral mercury-precession-decomposition --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mpd.set_defaults(func=_cmd_mercury_precession_decomposition)

    # mercury-dynamical-spectrum-full (full enumeration)
    mdsf = sub.add_parser(
        "mercury-dynamical-spectrum-full",
        help="Full Mercury dynamical-spectrum enumeration (modes + precession + citations)",
        description=(
            "Returns all dynamical modes + precession decomposition +\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mdsf.set_defaults(func=_cmd_mercury_dynamical_spectrum_full)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.1 — Luna Dynamical Spectrum
    # ──────────────────────────────────────────────────────────────────

    # luna-dynamical-spectrum
    lds = sub.add_parser(
        "luna-dynamical-spectrum",
        help="Luna's full action-angle dynamical-mode catalog (LLR-anchored)",
        description=(
            "v0.24.1 — second per-body dynamical-spectrum surface.\n"
            "Decomposes Luna's dynamical state into 8 angle modes\n"
            "(sidereal / synodic / anomalistic / draconitic mean\n"
            "motions; spin 1:1 locked; forced libration ~7.9 arcsec;\n"
            "apsidal precession 8.85 yr; nodal precession 18.61 yr)\n"
            "plus 3 action modes (eccentricity, inclination, obliquity\n"
            "to orbit; Cassini state 2).\n"
            "\n"
            "LLR (Lunar Laser Ranging) is the ground-truth source:\n"
            "50+ years of millimetre-precision ranging from McDonald,\n"
            "Apache Point, OCA, Matera observatories.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral luna-dynamical-spectrum --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    lds.set_defaults(func=_cmd_luna_dynamical_spectrum)

    # luna-saros-commensurability (THE headline)
    lsc = sub.add_parser(
        "luna-saros-commensurability",
        help="Saros cycle integer-commensurability closure invariant",
        description=(
            "v0.24.1 headline. Luna's three distinct months admit an\n"
            "exact small-integer commensurability:\n"
            "\n"
            "  223 x synodic     = 6585.32 d\n"
            "  239 x anomalistic = 6585.54 d\n"
            "  242 x draconitic  = 6585.36 d\n"
            "   19 x eclipse-yr  = 6585.78 d\n"
            "\n"
            "All four products agree within ~0.5 day. This is the\n"
            "~18.03-yr Saros eclipse-recurrence cycle -- a textbook\n"
            "small-denominator phenomenon and exactly the structure\n"
            "the project's BIP encoder is built to detect.\n"
            "\n"
            "Cross-strand: the Antikythera mechanism's Saros dial is\n"
            "literally a hardware implementation of this triple.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral luna-saros-commensurability --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    lsc.set_defaults(func=_cmd_luna_saros_commensurability)

    # luna-dynamical-spectrum-full
    ldsf = sub.add_parser(
        "luna-dynamical-spectrum-full",
        help="Full Luna dynamical-spectrum enumeration (modes + Saros + citations)",
        description=(
            "Returns all dynamical modes + Saros commensurability +\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ldsf.set_defaults(func=_cmd_luna_dynamical_spectrum_full)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.2 — Mars Dynamical Spectrum (chaotic obliquity / Laskar)
    # ──────────────────────────────────────────────────────────────────

    # mars-dynamical-spectrum
    mads = sub.add_parser(
        "mars-dynamical-spectrum",
        help="Mars's full action-angle dynamical-mode catalog (chaos contrast case)",
        description=(
            "v0.24.2 -- third per-body dynamical-spectrum surface.\n"
            "Mars is the CONTRAST case to Mercury (clean Le Verrier\n"
            "closure) and Luna (clean Saros commensurability): the\n"
            "canonical chaotic-dynamics example in the Solar System.\n"
            "\n"
            "8-mode catalog (5 angles + 3 actions): orbital mean\n"
            "motion, spin frequency (no spin-orbit lock), spin-axis\n"
            "precession (~171 kyr -- the chaos-driver), apsidal +\n"
            "nodal precession, eccentricity, inclination, OBLIQUITY\n"
            "(present 25.19 deg, Gyr excursion 0-60 deg per Laskar 2004).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral mars-dynamical-spectrum --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mads.set_defaults(func=_cmd_mars_dynamical_spectrum)

    # mars-secular-resonance-overlap (THE headline)
    msro = sub.add_parser(
        "mars-secular-resonance-overlap",
        help="Mars secular-resonance overlap (the chaos driver)",
        description=(
            "v0.24.2 headline. Mars's spin-axis precession frequency\n"
            "(~7.58 arcsec/yr) overlaps with inner-Solar-System\n"
            "secular orbital fundamentals s_3 (~-18.86) and s_4\n"
            "(~-17.74 arcsec/yr). The overlap drives chaotic\n"
            "obliquity wandering on Gyr timescales (Laskar 1993/2004;\n"
            "Touma-Wisdom 1993).\n"
            "\n"
            "This is the OBSERVABLE SIGNATURE of KAM-theory small-\n"
            "denominator failure in our Solar System -- the regime\n"
            "where the action-angle quasi-periodic torus structure\n"
            "breaks down.\n"
            "\n"
            "Cross-channel: without Earth's stabilising Moon (v0.24.1\n"
            "LLR-constrained), Earth would be subject to similar chaos.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral mars-secular-resonance-overlap --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    msro.set_defaults(func=_cmd_mars_secular_resonance_overlap)

    # mars-dynamical-spectrum-full
    madsf = sub.add_parser(
        "mars-dynamical-spectrum-full",
        help="Full Mars dynamical-spectrum enumeration (modes + resonances + citations)",
        description=(
            "Returns all dynamical modes + secular resonances +\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    madsf.set_defaults(func=_cmd_mars_dynamical_spectrum_full)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.3 — Sun Dynamical Spectrum (helioseismic p-modes)
    # ──────────────────────────────────────────────────────────────────

    # sun-dynamical-spectrum
    sds = sub.add_parser(
        "sun-dynamical-spectrum",
        help="Sun's helioseismic p-mode catalog + asymptotic-relation constants",
        description=(
            "v0.24.3 -- fourth per-body dynamical-spectrum surface,\n"
            "and the FIRST stellar entry. Methodology extension from\n"
            "rigid-body action-angle (Mercury/Luna/Mars) to stellar\n"
            "continuum normal-mode spectrum (helioseismology).\n"
            "\n"
            "Headlines:\n"
            "  Delta-nu = 135.1 uHz  (large frequency separation)\n"
            "  delta-nu = 9.0 uHz    (small separation; He-core diag.)\n"
            "  nu_max  = 3090 uHz    (peak amplitude)\n"
            "\n"
            "20-mode sample p-mode catalog (n=18-25, l=0-2) from\n"
            "BiSON 30-yr dataset (Davies 2014).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral sun-dynamical-spectrum --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sds.set_defaults(func=_cmd_sun_dynamical_spectrum)

    # helioseismic-asymptotic-relation (THE headline)
    har = sub.add_parser(
        "helioseismic-asymptotic-relation",
        help="Tassoul 1980 asymptotic-relation closure invariant",
        description=(
            "v0.24.3 headline. The Tassoul 1980 asymptotic relation\n"
            "predicts the entire p-mode comb from just three\n"
            "constants:\n"
            "\n"
            "  v_{n,l} ~ Delta-nu * (n + l/2 + eps)\n"
            "         - delta-nu * l(l+1) / (n + l/2 + eps)\n"
            "\n"
            "Closure: agreement of prediction vs BiSON measurements\n"
            "for the catalog modes to ~1 uHz precision.\n"
            "\n"
            "Cross-channel parallel: stellar-oscillation analogue of\n"
            "v0.24.1 Saros integer-commensurability. Three constants\n"
            "-> entire mode spectrum.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral helioseismic-asymptotic-relation --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    har.set_defaults(func=_cmd_helioseismic_asymptotic_relation)

    # sun-dynamical-spectrum-full
    sdsf = sub.add_parser(
        "sun-dynamical-spectrum-full",
        help="Full Sun dynamical-spectrum enumeration (modes + citations)",
        description=(
            "Returns all helioseismic modes + asymptotic-relation\n"
            "constants + citation dict so consumers can verify the\n"
            "provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sdsf.set_defaults(func=_cmd_sun_dynamical_spectrum_full)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.4 — Per-body Toroidal-Residual J₂ Catalog
    # ──────────────────────────────────────────────────────────────────

    # toroidal-residual
    tr = sub.add_parser(
        "toroidal-residual",
        help="Per-body classification on the Chandrasekhar 1969 sequence",
        description=(
            "v0.24.4 -- per-body shape classification on the\n"
            "Maclaurin -> Jacobi -> bar -> ring/torus rotating-fluid\n"
            "equilibrium sequence. Codifies the insight that rotation\n"
            "forces the body toward the toroidal end of the sequence,\n"
            "self-gravity restores it toward the spherical end, and\n"
            "J2 is the quantitative measure of where in the sequence\n"
            "the body sits.\n"
            "\n"
            "Headlines:\n"
            "  Saturn closest to Maclaurin-Jacobi bifurcation\n"
            "  (q=0.155 vs threshold 0.187; most oblate Solar-System\n"
            "  body, 1/10 flattening).\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral toroidal-residual --pretty\n"
            "  ephemerides-spectral toroidal-residual --body saturn --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tr.add_argument("--body", default=None,
                    help="Body name (lower-case). If omitted, full "
                         "catalog.")
    tr.set_defaults(func=_cmd_toroidal_residual)

    # chandrasekhar-sequence
    cs = sub.add_parser(
        "chandrasekhar-sequence",
        help="Chandrasekhar 1969 sequence bifurcation thresholds",
        description=(
            "Returns the bifurcation-threshold constants for the\n"
            "rotating-fluid equilibrium sequence:\n"
            "  q_Maclaurin_Jacobi = 0.187 (sequence bifurcation)\n"
            "  q_Jacobi_bar       = 0.27  (bar instability)\n"
            "  q_Roche_fission    = 0.36  (equatorial unbinding)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    cs.set_defaults(func=_cmd_chandrasekhar_sequence)

    # toroidal-residuals
    trs = sub.add_parser(
        "toroidal-residuals",
        help="Full toroidal-residual catalog enumeration",
        description=(
            "Returns every body's ToroidalResidual record + the\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    trs.set_defaults(func=_cmd_toroidal_residuals)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.5 — Hawaiian-Emperor Chain Spectral Catalog
    # ──────────────────────────────────────────────────────────────────

    # hawaii-chain
    hc = sub.add_parser(
        "hawaii-chain",
        help="Hawaiian-Emperor chain seamount catalog + Fiedler embedding",
        description=(
            "v0.24.5 -- bounded-local-Laplacian application to a\n"
            "hotspot track on Earth's surface. First time the\n"
            "project's graph-Laplacian eigenbasis is applied to\n"
            "physical features on a single body's surface rather\n"
            "than to orbital relationships between bodies.\n"
            "\n"
            "18-seamount roster spanning ~85 Myr (Meiji oldest -> Big\n"
            "Island youngest). Each seamount with K-Ar/Ar-Ar age,\n"
            "lat/lon, arc-length from present-day hotspot, Fiedler\n"
            "vector coordinate.\n"
            "\n"
            "Plate-velocity reconstruction from age-vs-arc-length\n"
            "slope (post-bend Hawaiian arc): ~10 cm/yr Pacific Plate\n"
            "northwest motion.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral hawaii-chain --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hc.set_defaults(func=_cmd_hawaii_chain)

    # hawaii-emperor-bend (THE headline)
    heb = sub.add_parser(
        "hawaii-emperor-bend",
        help="Hawaiian-Emperor bend signature (Fiedler-eigenvalue gap at ~47.5 Myr)",
        description=(
            "v0.24.5 headline. The graph-Laplacian Fiedler partition\n"
            "surfaces the famous Hawaiian-Emperor bend at ~47.5 Myr\n"
            "automatically: Emperor seamounts and Hawaiian seamounts\n"
            "fall on opposite signs of the Fiedler vector, with\n"
            "Daikakuji at the transition. The eigenvalue gap\n"
            "(lambda_3 - lambda_2) measures how cleanly the chain\n"
            "bisects.\n"
            "\n"
            "Cross-strand observation: same algebraic machinery\n"
            "(Fiedler partition) as v0.18.0 body_architecture's\n"
            "inner-vs-outer Solar-System split -- applied to a\n"
            "finite physical-feature graph on Earth's surface\n"
            "rather than an orbital graph. The chess-board analogy\n"
            "made explicit.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral hawaii-emperor-bend --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    heb.set_defaults(func=_cmd_hawaii_emperor_bend)

    # hawaii-chain-full
    hcf = sub.add_parser(
        "hawaii-chain-full",
        help="Full Hawaiian-Emperor chain catalog enumeration + citations",
        description=(
            "Returns every seamount + arc-length + citation dict so\n"
            "consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hcf.set_defaults(func=_cmd_hawaii_chain_full)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.6 — Small-body Yarkovsky/YORP
    # ──────────────────────────────────────────────────────────────────

    # yarkovsky-yorp
    yy = sub.add_parser(
        "yarkovsky-yorp",
        help="Per-asteroid Yarkovsky drift + YORP spin-state evolution",
        description=(
            "v0.24.6 -- per-asteroid thermal-radiation orbital +\n"
            "spin-state drift. 10-asteroid roster including Bennu\n"
            "(OSIRIS-REx; first imaged Yarkovsky), 2000 PH5 (first\n"
            "YORP detection; lent its name to the effect), Apophis,\n"
            "Ryugu, Itokawa, Apollo, Geographos, 1950 DA, Golevka,\n"
            "Eger.\n"
            "\n"
            "Yarkovsky: thermal-emission asymmetry produces a force\n"
            "that drifts the semi-major axis. Prograde rotators\n"
            "outward, retrograde inward.\n"
            "\n"
            "YORP: same mechanism on irregular shapes produces a\n"
            "torque that changes spin rate + obliquity.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral yarkovsky-yorp --body bennu --pretty\n"
            "  ephemerides-spectral yarkovsky-yorp --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    yy.add_argument("--body", default=None,
                    help="Asteroid short name (e.g., bennu, apophis, "
                         "itokawa). If omitted, full catalog.")
    yy.set_defaults(func=_cmd_yarkovsky_yorp)

    # yorp-attractor-thresholds
    yat = sub.add_parser(
        "yorp-attractor-thresholds",
        help="YORP physical-regime threshold constants",
        description=(
            "Returns the bifurcation-threshold constants for the\n"
            "small-body YORP sequence: rotational-fission limit\n"
            "(~2.2 h), observability diameter (~30 km), YORP\n"
            "obliquity attractors (~55 deg + ~125 deg)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    yat.set_defaults(func=_cmd_yorp_attractor_thresholds)

    # yarkovsky-yorps
    yys = sub.add_parser(
        "yarkovsky-yorps",
        help="Full Yarkovsky/YORP catalog enumeration",
        description=(
            "Returns every asteroid's YarkovskyYorpEntry record +\n"
            "the citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    yys.set_defaults(func=_cmd_yarkovsky_yorps)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.7 — Mars Tharsis Volcanic Chain Catalog
    # ──────────────────────────────────────────────────────────────────

    # mars-tharsis-chain
    mtc = sub.add_parser(
        "mars-tharsis-chain",
        help="Mars Tharsis volcanic-chain catalog + Fiedler embedding",
        description=(
            "v0.24.7 -- Mars Tharsis volcanic chain: 5-volcano roster\n"
            "(Olympus Mons, Arsia / Pavonis / Ascraeus Montes,\n"
            "Alba Mons) on a body WITHOUT plate tectonics. Direct\n"
            "no-plate-tectonics counterpart to v0.24.5 Hawaii hotspot\n"
            "track. Same eigendecomposition machinery; cogenetic-\n"
            "family structure surfaces instead of trajectory.\n"
            "\n"
            "Each volcano carries surface age (crater-count), summit\n"
            "position (MOLA), elevation, edifice diameter, structural\n"
            "role, and a Fiedler-eigenvector coordinate from the\n"
            "Gaussian-proximity Laplacian.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral mars-tharsis-chain --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mtc.set_defaults(func=_cmd_mars_tharsis_chain)

    # tharsis-fiedler-signature
    tfs = sub.add_parser(
        "tharsis-fiedler-signature",
        help="Mars Tharsis Fiedler-partition signature (the headline)",
        description=(
            "Returns the eigenvalue gap, Fiedler clusters, and\n"
            "Olympus / Alba ridge-residual offsets for the Tharsis\n"
            "system. Unlike Hawaii (v0.24.5), there is no directional\n"
            "'bend' because there is no plate motion: the Fiedler\n"
            "partition surfaces structural cogenetic-family geometry\n"
            "rather than chronological trajectory."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tfs.set_defaults(func=_cmd_tharsis_fiedler_signature)

    # mars-tharsis-chain-full
    mtcf = sub.add_parser(
        "mars-tharsis-chain-full",
        help="Full Mars Tharsis volcano catalog + citations",
        description=(
            "Returns every volcano's TharsisVolcano record + the\n"
            "citation dict so consumers can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mtcf.set_defaults(func=_cmd_mars_tharsis_chain_full)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.8 — Axial Seamount Eruption Chronology Catalog
    # ──────────────────────────────────────────────────────────────────

    # axial-seamount-chronology
    asc = sub.add_parser(
        "axial-seamount-chronology",
        help="Axial Seamount eruption chronology + inflation phases + forecasts",
        description=(
            "v0.24.8 -- temporal-spectrum eruption-cycle observable\n"
            "on Axial Seamount (Juan de Fuca Ridge submarine\n"
            "volcano). 3-eruption roster (1998 / 2011 / 2015) +\n"
            "4 inflation phases (pre-1998, 1998-2011, 2011-2015,\n"
            "post-2015) + 2 Chadwick-Nooner forecasts (1 HIT in\n"
            "2015 + 1 MISS in 2024-2025 as of catalog reference\n"
            "year 2026).\n"
            "\n"
            "Cross-channel: where v0.24.5 Hawaii (with plate\n"
            "tectonics) -> spatial trajectory and v0.24.7 Mars\n"
            "Tharsis (no plate tectonics) -> spatial cogenetic\n"
            "family, v0.24.8 Axial Seamount -> temporal quasi-\n"
            "periodic cycle. Same v0.24.x algebraic discipline;\n"
            "different observable axis; the first explicit\n"
            "prediction-reliability ship.\n"
            "\n"
            "Examples:\n"
            "  ephemerides-spectral axial-seamount-chronology --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    asc.set_defaults(func=_cmd_axial_seamount_chronology)

    # axial-inflation-cycle-signature
    aics = sub.add_parser(
        "axial-inflation-cycle-signature",
        help="Axial Seamount inflation-cycle signature (the headline)",
        description=(
            "Returns the inter-eruption interval distribution + the\n"
            "rate-period product (Chadwick-Nooner conserved observable)\n"
            "+ Chadwick forecast track-record (1 HIT 2015, 1 MISS\n"
            "2024-2025). The HIT/MISS asymmetry is the v0.24.2-style\n"
            "spectral-stability failure mode applied at decade /\n"
            "cm-per-year timescales -- same algebraic structure as\n"
            "Mars's secular-resonance obliquity chaos, on a wildly\n"
            "different observational scale."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    aics.set_defaults(func=_cmd_axial_inflation_cycle_signature)

    # axial-seamount-full
    asf = sub.add_parser(
        "axial-seamount-full",
        help="Full Axial Seamount catalog + citations",
        description=(
            "Returns every eruption record + inflation-phase record +\n"
            "Chadwick forecast record + the citation dict so consumers\n"
            "can verify the provenance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    asf.set_defaults(func=_cmd_axial_seamount_full)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.9 — Dynamical-Regime Classifier
    # ──────────────────────────────────────────────────────────────────

    # regime-eigenbasis
    re_eb = sub.add_parser(
        "regime-eigenbasis",
        help="Dynamical-regime classifier eigenbasis (top PCs over v0.24.x ships)",
        description=(
            "v0.24.9 -- the eigenbasis-projection version of the\n"
            "v0.24.x if/else chain. 9 labelled training examples\n"
            "(one per v0.24.0-v0.24.8 ship), 7 features per example,\n"
            "principal-component decomposition over the standardised\n"
            "feature matrix. Top 3 PCs explain ~83 percent of variance.\n"
            "\n"
            "Returns the eigenvalues + per-feature loadings + every\n"
            "training example's projected coordinates."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    re_eb.add_argument(
        "--n-components", type=int, default=3,
        help="Number of top PCs to project onto (default 3; max 7).",
    )
    re_eb.set_defaults(func=_cmd_regime_eigenbasis)

    # regime-classify
    re_cl = sub.add_parser(
        "regime-classify",
        help="Classify a 7-feature vector against the v0.24.x training examples",
        description=(
            "Project a 7-feature vector into the dynamical-regime\n"
            "eigenbasis and return the nearest-neighbour regime label\n"
            "+ distances to every training example.\n"
            "\n"
            "Feature schema (all required):\n"
            "  --time-scale-log-s         log10(period in seconds)\n"
            "  --spatial-scale-log-km     log10(length in km)\n"
            "  --stability-index          0..1 Diophantine-stability\n"
            "  --has-commensurability     0/1 integer-resonance present\n"
            "  --prediction-track-signal  -1/0/+1 (MISS/none/HIT-only)\n"
            "  --dimensionality           0/1/2/3 (point/chain/surface/volume)\n"
            "  --forcing-class-index      0..4 (gravitational..volcanic)\n"
            "\n"
            "Example (Enceladus probe):\n"
            "  ephemerides-spectral regime-classify \\\n"
            "    --time-scale-log-s 5.08 --spatial-scale-log-km 2.40 \\\n"
            "    --stability-index 1.0 --has-commensurability 1 \\\n"
            "    --prediction-track-signal 0 --dimensionality 0 \\\n"
            "    --forcing-class-index 0 --pretty"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    re_cl.add_argument("--time-scale-log-s", type=float, required=True)
    re_cl.add_argument("--spatial-scale-log-km", type=float, required=True)
    re_cl.add_argument("--stability-index", type=float, required=True)
    re_cl.add_argument("--has-commensurability", type=int, required=True,
                       choices=[0, 1])
    re_cl.add_argument("--prediction-track-signal", type=int, required=True,
                       choices=[-1, 0, 1])
    re_cl.add_argument("--dimensionality", type=int, required=True,
                       choices=[0, 1, 2, 3])
    re_cl.add_argument("--forcing-class-index", type=int, required=True,
                       choices=[0, 1, 2, 3, 4])
    re_cl.add_argument("--n-components", type=int, default=3)
    re_cl.set_defaults(func=_cmd_regime_classify)

    # regime-list
    re_ls = sub.add_parser(
        "regime-list",
        help="Full enumeration of v0.24.x regime training examples",
        description=(
            "Returns every v0.24.0-v0.24.8 labelled training example,\n"
            "its regime label, its 7-feature signature vector, the\n"
            "catalog module that implements it, and the citation\n"
            "pointer back to the source ship."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    re_ls.set_defaults(func=_cmd_regime_list)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.10 — OOS probe roster + classifier calibration-ratio metric
    # ──────────────────────────────────────────────────────────────────

    # regime-probes
    re_probes = sub.add_parser(
        "regime-probes",
        help="Run the curated OOS probe roster through the classifier",
        description=(
            "v0.24.10 -- run every curated out-of-sample probe\n"
            "(Yellowstone, Reunion, Pluto-Charon, Enceladus, Io,\n"
            "Phobos, Ceres, Alpha Centauri B, Vesta, magnetar)\n"
            "through the v0.24.9 classifier and return a results\n"
            "table with calibration ratios + OOD flags + match-vs-\n"
            "expected status.\n"
            "\n"
            "The probes are NOT training data -- they're test\n"
            "vectors. The classifier's eigenbasis is computed only\n"
            "from the 9 v0.24.0-v0.24.8 training examples; probes\n"
            "are projected into that basis without ever altering it."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    re_probes.add_argument(
        "--n-components", type=int, default=3,
        help="Number of top PCs to use (default 3; max 7).",
    )
    re_probes.add_argument(
        "--ood-threshold", type=float, default=0.85,
        help="Calibration-ratio cutoff for OOD flagging (default 0.85).",
    )
    re_probes.set_defaults(func=_cmd_regime_probes)

    # regime-probes-list
    re_probes_ls = sub.add_parser(
        "regime-probes-list",
        help="Full enumeration of OOS probe roster (no classifier run)",
        description=(
            "Pure data-side enumerator. Returns every curated OOS\n"
            "probe's identity + feature vector + expected regime /\n"
            "OOD status + citation -- without paying the\n"
            "eigendecomposition cost of running the classifier."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    re_probes_ls.set_defaults(func=_cmd_regime_probes_list)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.11 — Pluto-Charon Dynamical Spectrum
    # ──────────────────────────────────────────────────────────────────

    # pluto-charon-dynamical-spectrum
    pcds = sub.add_parser(
        "pluto-charon-dynamical-spectrum",
        help="Pluto-Charon binary action-angle catalog + small-moon resonances",
        description=(
            "v0.24.11 -- Pluto-Charon dynamical spectrum. Fourth\n"
            "per-body ship in the v0.24.x action-angle sequence\n"
            "(after Mercury/Luna/Mars); the FIRST binary mutual-\n"
            "tidal-lock entry. Pluto + Charon both tidally locked\n"
            "to each other simultaneously (mutual orbital period =\n"
            "both spin periods = 6.387 d). The Solar System's only\n"
            "known double-synchronous binary planet.\n"
            "\n"
            "Includes 12 modes (3 angle-locked at 6.387 d, 1 slow\n"
            "apsidal libration, 4 actions, 4 small-moon near-3:4:5:6\n"
            "near-resonances) + binary geometry (mass ratio 0.122,\n"
            "barycenter ~940 km outside Pluto's surface) + small-\n"
            "moon orbital periods.\n"
            "\n"
            "Path-B response to v0.24.10 schema-gap: populates the\n"
            "binary-mutual-lock regime that the v0.24.9 classifier\n"
            "couldn't see."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pcds.set_defaults(func=_cmd_pluto_charon_dynamical_spectrum)

    # double-synchronous-signature
    dss = sub.add_parser(
        "double-synchronous-signature",
        help="Pluto-Charon double-synchronous lock signature (the headline)",
        description=(
            "Returns the triple-lock invariant (P_orb = P_spin_pluto\n"
            "= P_spin_charon = 6.387 d) + companion observables\n"
            "(eccentricity 5e-5, mutual obliquity 0.0006 deg, mass\n"
            "ratio 0.122, barycenter offset 940 km above Pluto's\n"
            "surface) + small-moon near-3:4:5:6 commensurabilities\n"
            "with the mutual orbital period (Showalter-Hamilton 2015\n"
            "chaotic in libration on Myr timescales)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    dss.set_defaults(func=_cmd_double_synchronous_signature)

    # pluto-charon-dynamical-spectrum-full
    pcdsf = sub.add_parser(
        "pluto-charon-dynamical-spectrum-full",
        help="Full Pluto-Charon mode catalog + citations",
        description=(
            "Returns every Pluto-Charon dynamical mode + the\n"
            "citation dict so consumers can verify the provenance\n"
            "(Brozovic 2015 post-New-Horizons orbital fit; Stern 2015\n"
            "*Science*; Showalter-Hamilton 2015 *Nature* small-moon\n"
            "chaos; Tholen-Buie 1990 mutual events)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pcdsf.set_defaults(func=_cmd_pluto_charon_dynamical_spectrum_full)

    # ──────────────────────────────────────────────────────────────────
    # v0.24.12 — Loki Patera (Io) Eruption Cycle
    # ──────────────────────────────────────────────────────────────────

    # loki-patera-eruption-cycle
    lpec = sub.add_parser(
        "loki-patera-eruption-cycle",
        help="Loki Patera eruption-cycle catalog (Io tidal-heating cousin to Axial)",
        description=(
            "v0.24.12 -- Loki Patera (Io) eruption cycle. The Solar\n"
            "System's most active volcano (~200 km lava lake on\n"
            "Jupiter's moon Io, accounting for 5-15% of Io's\n"
            "globally-integrated ~10^14 W tidal-heating output).\n"
            "\n"
            "~540-day quasi-periodic resurfacing cycle (Rathbun 2002\n"
            "*GRL* canonical paper); cousin to v0.24.8 Axial Seamount\n"
            "in the temporal-quasi-periodic-cycle regime, with\n"
            "fundamentally different forcing physics (tidal heating\n"
            "from Galilean Laplace 4:2:1 commensurability vs Axial's\n"
            "mantle-plume-over-spreading-ridge magma supply).\n"
            "\n"
            "6 cycle-peak observations (1990-2017) + 6 action-angle\n"
            "modes (cycle period, brightening / resurfacing /\n"
            "cooling phases, Io orbital, Galilean Laplace 4:2:1)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    lpec.set_defaults(func=_cmd_loki_patera_eruption_cycle)

    # loki-galilean-laplace-signature
    lgls = sub.add_parser(
        "loki-galilean-laplace-signature",
        help="Galilean Laplace 4:2:1 commensurability signature (the headline)",
        description=(
            "Returns the 4*P_Io ≈ 2*P_Europa ≈ P_Ganymede\n"
            "commensurability check + the forced-eccentricity 0.0041\n"
            "consequence + the ~10^14 W tidal-heating budget that\n"
            "makes Loki Patera exist + the Loki cycle / Io orbital\n"
            "ratio. Cross-references v0.24.11 Pluto-Charon's\n"
            "near-3:4:5:6 small-moon commensurability (binary-system\n"
            "analogue of the same algebraic structure)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    lgls.set_defaults(func=_cmd_loki_galilean_laplace_signature)

    # loki-patera-eruption-cycle-full
    lpecf = sub.add_parser(
        "loki-patera-eruption-cycle-full",
        help="Full Loki Patera cycle catalog + citations",
        description=(
            "Returns every cycle peak + mode + the citation dict so\n"
            "consumers can verify the provenance (Rathbun 2002 *GRL*\n"
            "canonical period; Veeder 1994 KAO; de Kleer 2017\n"
            "adaptive-optics; de Kleer 2019 multi-phase resurfacing;\n"
            "Peale-Cassen-Reynolds 1979 deep-mechanism forcing)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    lpecf.set_defaults(func=_cmd_loki_patera_eruption_cycle_full)

    # ──────────────────────────────────────────────────────────────────
    # v0.25.0a — Attested Multi-Source Collector framework
    # ──────────────────────────────────────────────────────────────────

    # attested-list
    al = sub.add_parser(
        "attested-list",
        help="List every registered attested source (descriptor metadata)",
        description=(
            "v0.25.0a -- enumerate every attested source registered\n"
            "in research/attested/<source>/descriptor.toml. Returns\n"
            "rendered metadata: human-readable name, purpose,\n"
            "license, citation template, adapter, gap-targeting\n"
            "regime labels.\n"
            "\n"
            "Source-of-truth lives in the descriptor TOML. Adding a\n"
            "new source is a CONFIG change, not a CODE change."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    al.set_defaults(func=_cmd_attested_list)

    # attested-dataset
    ad = sub.add_parser(
        "attested-dataset",
        help="Return paginated rows for one attested source",
        description=(
            "v0.25.0a -- emit paginated MPR (Mathematical Provenance\n"
            "Record) rows for one source. Each row carries data +\n"
            "attestation + rendering blocks.\n"
            "\n"
            "Use --limit / --offset for pagination over large\n"
            "rosters. The cheap data-block-free variant is\n"
            "`attested-audit` (provenance metadata only)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ad.add_argument("--source", required=True, help="source key (e.g. earthref_sc)")
    ad.add_argument("--limit", type=int, default=None, help="max rows to return")
    ad.add_argument("--offset", type=int, default=0, help="row offset")
    ad.set_defaults(func=_cmd_attested_dataset)

    # attested-descriptor
    adesc = sub.add_parser(
        "attested-descriptor",
        help="Return the parsed descriptor for one attested source",
        description=(
            "v0.25.0a -- return the full parsed descriptor TOML for\n"
            "one source ([source], [fetch], [parse], [schema],\n"
            "[rendering], [attestation], [gap_targeting]). Useful\n"
            "for UI source-pickers + the v0.26.x schema-gap-driven\n"
            "trigger that consumes [gap_targeting] declarations."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    adesc.add_argument("--source", required=True, help="source key")
    adesc.set_defaults(func=_cmd_attested_descriptor)

    # attested-audit
    aa = sub.add_parser(
        "attested-audit",
        help="Return per-row attestation metadata (no data payload)",
        description=(
            "v0.25.0a -- per-row attestation metadata for one\n"
            "source: response_sha256, retrieved_at, parser_version,\n"
            "parser_rule_hash, collector_descriptor_hash. No data\n"
            "block — cheap; paper-appendix-ready.\n"
            "\n"
            "Use this when you need to document the provenance trail\n"
            "of a source's row content without materialising the\n"
            "data payload itself."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    aa.add_argument("--source", required=True, help="source key")
    aa.set_defaults(func=_cmd_attested_audit)

    # lunar-kernels
    lk = sub.add_parser(
        "lunar-kernels",
        help="Lunar-time / lunar-orientation kernel metadata (LTE440, etc.)",
        description=(
            "v0.3.0 ships *awareness* of LTE440 (Lin et al. 2025) "
            "— SPICE-format Lunar Time Ephemeris on DE440, accuracy "
            "0.15 ns through 2050. The kernel must be staged "
            "separately (github.com/xlucn/LTE440 releases); "
            "ephemerides-spectral does not auto-download. When LTC "
            "(Lunar Coordinated Time) is finalised by NASA + "
            "international agencies, this command becomes the "
            "runtime surface for LTC <-> UTC <-> JD_TDB."
        ),
    )
    lk.set_defaults(func=_cmd_lunar_kernels)

    # natural-group
    ng = sub.add_parser(
        "natural-group",
        help="Resonance-derived natural cyclic group (LCM, CRT prime factorisation)",
        description=(
            "Reads the Phase 9 RESONANCES table and returns the natural "
            "cyclic group the resonances themselves demand — distinct "
            "from the encoder's architectural Z_{2^32} modulus. For "
            "each pair (n_a, m_b) the per-pair natural cycle is "
            "lcm(n_a, m_b); the aggregate is LCM across pairs. By CRT "
            "the aggregate factors into prime cyclic groups: those are "
            "the natural coprimes the resonance topology lives in. "
            "See research notebook §6 for the full discussion + the "
            "connection to chess-spectral's non-Markovian sheaf."
        ),
        epilog=(
            "On the v0.3.0 four-resonance set:\n"
            "  J-S 5:2 -> lcm(5,2)=10\n"
            "  N-P 3:2 -> lcm(3,2)=6\n"
            "  Io-Eu 2:1 -> lcm(2,1)=2\n"
            "  Eu-Ga 2:1 -> lcm(2,1)=2\n"
            "  Aggregate: lcm(10, 6, 2, 2) = 30 = 2 x 3 x 5"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ng.set_defaults(func=_cmd_natural_group)

    # find-syzygies (v0.3.1)
    fs = sub.add_parser(
        "find-syzygies",
        help="Spectral-native syzygy window search (HDC-native; not encode-then-check)",
        description=(
            "Enumerates candidate syzygies in a JD window in closed "
            "form by walking new/full moon multiples of the synodic "
            "month + confirming against the draconic-month phase. "
            "Replaces the v0.3.0 point-evaluation `eclipse --jd` "
            "pattern for window searches: cost goes from O(window_days "
            "× encode) to O(n_syzygies × confirmation), typically "
            "100-1000× faster for multi-decade windows since syzygies "
            "are rare events on the calendar (~5/yr combined solar+lunar)."
        ),
        epilog=(
            "Example: find solar/lunar syzygies in 2024 (UTC ≈ JD 2460311 to 2460676):\n"
            "  ephemerides-spectral find-syzygies --from-jd 2460311 --to-jd 2460676\n\n"
            "For arc-second-class precision (totality, location, partial-vs-total)\n"
            "confirm each returned candidate against a JPL ephemeris via skyfield."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    fs.add_argument("--from-jd", dest="from_jd", type=float, required=True,
                    help="Window lower bound in JD (TDB)")
    fs.add_argument("--to-jd", dest="to_jd", type=float, required=True,
                    help="Window upper bound in JD (TDB)")
    fs.add_argument("--kind", choices=["solar", "lunar", "all"], default="all",
                    help="Syzygy kind filter (default 'all')")
    fs.add_argument("--threshold", type=float, default=0.05,
                    help=("Score cutoff [0, 0.5]; 0.05 ≈ total-class "
                          "(default), 0.1 ≈ partial-class"))
    fs.set_defaults(func=_cmd_find_syzygies)

    # patches (v0.4.0+) — runtime kernel-patching surface
    pp = sub.add_parser(
        "patches",
        help="Diagnosed-fiber runtime overlay (v0.4.0+). Apply / list / clear "
             "Fourier corrections without mutating the published kernel.",
        description=(
            "Diagnosed-fiber patches are runtime overlays on the spectral "
            "kernel: DATA, not code edits, summed onto the encoded phases "
            "AFTER the base encode loop. The published kernel bytes never "
            "change.\n\n"
            "Both backends apply the overlay (v0.4.1 native ABI v2 + "
            "Python BIP). With v0.5.2's CATALOG_V2 (LS-fit, vindicated), "
            "Mars/Mercury/Jupiter-Saturn patches drop their targeted FFT "
            "residual peak by >=96%. Six total patches in the bundled "
            "catalogs (3 v0.4.0 magnitude-only + 3 v0.5.2 LS-fit `-v2`)."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral patches catalog\n"
            "  ephemerides-spectral patches apply --name jupiter-saturn-9.56yr-coupled-v2\n"
            "  ephemerides-spectral patches active\n"
            "  ephemerides-spectral patches clear\n\n"
            "Use `patches <op> --help` for sub-command detail."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pp_sub = pp.add_subparsers(dest="patch_cmd", required=True,
                                title="Patch operations", metavar="<op>")

    pp_catalog = pp_sub.add_parser(
        "catalog",
        help="List the bundled diagnosed-fiber patch catalog.",
        description=(
            "Each entry includes name + kind + targeted body / coupling, "
            "amplitude (deg), period (days), phase (rad), and free-text "
            "notes describing the suspected missing physics + (for v0.5.2 "
            "`-v2` entries) the measured shrinkage% of the targeted FFT "
            "residual peak."
        ),
        epilog=(
            "Example:\n"
            "  ephemerides-spectral patches catalog\n\n"
            "The combined catalog has 6 entries:\n"
            "  v0.4.0 (magnitude-only authoring; superseded):\n"
            "    mars-7.96yr-diagonal\n"
            "    mercury-10.69yr-diagonal\n"
            "    jupiter-saturn-9.56yr-coupled\n"
            "  v0.5.2 (LS-fit, measured-vindicated):\n"
            "    mars-7.96yr-diagonal-v2              99.2% shrinkage\n"
            "    mercury-10.69yr-diagonal-v2          99.9% shrinkage\n"
            "    jupiter-saturn-9.56yr-coupled-v2     97.6% / 96.0% (J / S)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pp_catalog.set_defaults(func=_cmd_patches_catalog)

    pp_active = pp_sub.add_parser(
        "active",
        help="List the currently-active runtime patches.",
        description=(
            "Patches are an in-process registry; they don't persist "
            "across interpreter restarts. Each fresh `python` invocation "
            "starts with no active patches."
        ),
        epilog=(
            "Example:\n"
            "  ephemerides-spectral patches active"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pp_active.set_defaults(func=_cmd_patches_active)

    pp_apply = pp_sub.add_parser(
        "apply",
        help="Load a named CATALOG patch into the overlay registry.",
        description=(
            "Same patch cannot be applied twice — clear first if you mean "
            "to replace it. The patch is mirrored into both the Python "
            "BIP registry and the C-side native registry (ABI v2); "
            "byte-for-byte identical phases on both backends."
        ),
        epilog=(
            "Examples:\n"
            "  ephemerides-spectral patches apply --name mars-7.96yr-diagonal-v2\n"
            "  ephemerides-spectral patches apply --name jupiter-saturn-9.56yr-coupled-v2\n\n"
            "Use `patches catalog` to see all available patch names."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pp_apply.add_argument("--name", required=True,
                          help="Catalog patch name (use `patches catalog` to list)")
    pp_apply.set_defaults(func=_cmd_patches_apply)

    pp_clear = pp_sub.add_parser(
        "clear",
        help="Remove every active runtime patch.",
        description=(
            "Wipes both the Python BIP registry and the C-side native "
            "registry. After this the encoder is byte-identical to the "
            "published kernel (no overlay deltas applied)."
        ),
        epilog=(
            "Example:\n"
            "  ephemerides-spectral patches clear"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pp_clear.set_defaults(func=_cmd_patches_clear)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _make_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
