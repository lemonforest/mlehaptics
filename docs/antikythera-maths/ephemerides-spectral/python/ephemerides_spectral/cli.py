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
