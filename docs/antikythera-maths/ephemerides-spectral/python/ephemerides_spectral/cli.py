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
* ``breathing`` — Phase 9 breathing-coupling LUT modulation at a JD

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


def _cmd_breathing(args: argparse.Namespace) -> int:
    return _emit(
        bridge.get_breathing_modulation(
            args.jd, pair=(args.pair_a, args.pair_b),
            n_lobes=(args.n_a, args.n_b), kernel=args.kernel,
        ),
        pretty=args.pretty,
    )


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
                         overflow. Phase 9 breathing couplings (Jupiter-
                         Saturn 5:2 resonance) handled with an integer
                         cosine LUT — no FPU in the hot path.
  * 'complex128'       — FPU complex128 reference encoder; same
                         algebraic structure, used for regression and
                         the Syzygy / observer-binding operators.

The system Laplacian decomposes as:

  * Diagonal       — Newtonian mean motions (2pi / period_days).
  * Diagonal (PN)  — Mercury 43"/century relativistic precession.
  * Off-diagonal   — gravitational fiber couplings (planet-sun,
                     moon-planet, J-S resonance, asteroid-Jupiter).

Phase 9 (breathing) modulates the off-diagonal weights with the
resonant phase difference cos(n_a*phi_a - n_b*phi_b) via a 1024-entry
int32 cosine LUT (Q1.14 amplitude, 4 KB).
"""

_TOPLEVEL_EPILOG = """\
Examples
--------

    # Package version + frozen-data manifest
    ephemerides-spectral version

    # All 26 bodies in the Sol Star System Laplacian
    ephemerides-spectral bodies

    # Earth temporal resolution at the default D=65536
    ephemerides-spectral resolution --body earth

    # Encode J2000 with the integer ALU backend (default)
    ephemerides-spectral encode --jd 2451545.0

    # Same JD with the FPU complex128 reference encoder
    ephemerides-spectral encode --jd 2451545.0 --backend complex128

    # Topocentric view from London at J2000
    ephemerides-spectral local-view --jd 2451545.0 --body earth \\
                          --lat 51.5 --lon -0.1

    # Syzygy alignment probability at a JD
    ephemerides-spectral eclipse --jd 2451545.0

    # Off-diagonal couplings (Laplacian fiber bundle)
    ephemerides-spectral couplings

    # Phase 9 breathing modulation for Jupiter-Saturn 5:2 at +20 yr
    ephemerides-spectral breathing --jd 2458850.0

    # Override resonance: 3:2 Neptune-Pluto
    ephemerides-spectral breathing --jd 2451545.0 \\
                          --pair-a neptune --pair-b pluto --n-a 3 --n-b 2

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
    r.add_argument("--body", default="earth", choices=_BODY_CHOICES,
                   help="Body name (default 'earth')")
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
            "                --body earth --lat 51.5 --lon -0.1"
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

    # breathing
    br = sub.add_parser(
        "breathing",
        help="Phase 9 breathing-coupling LUT modulation at a JD",
        description=(
            "Computes the resonant phase n_a*phi_a - n_b*phi_b (mod "
            "2^32) for a body pair at a JD, then evaluates the integer "
            "cosine LUT (Q1.14, 1024 entries). Returns both the LUT "
            "value and a float reference for calibration."
        ),
        epilog=(
            "Examples:\n"
            "  # Default Jupiter-Saturn 5:2 resonance\n"
            "  ephemerides-spectral breathing --jd 2451545.0\n\n"
            "  # Neptune-Pluto 3:2 resonance\n"
            "  ephemerides-spectral breathing --jd 2451545.0 \\\n"
            "         --pair-a neptune --pair-b pluto --n-a 3 --n-b 2\n\n"
            "  # Io-Europa 1:2 (note ordering: smaller multiplier first)\n"
            "  ephemerides-spectral breathing --jd 2451545.0 \\\n"
            "         --pair-a europa --pair-b io --n-a 1 --n-b 2"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    br.add_argument("--jd", type=float, required=True, help="Julian Date in TDB")
    br.add_argument("--pair-a", dest="pair_a", default="jupiter",
                    choices=_BODY_CHOICES, help="First body of the pair")
    br.add_argument("--pair-b", dest="pair_b", default="saturn",
                    choices=_BODY_CHOICES, help="Second body of the pair")
    br.add_argument("--n-a", dest="n_a", type=int, default=5,
                    help="Resonance multiplier on phi_a (default 5)")
    br.add_argument("--n-b", dest="n_b", type=int, default=2,
                    help="Resonance multiplier on phi_b (default 2)")
    br.add_argument("--kernel", choices=_KERNEL_CHOICES, default="de441",
                    help="JPL DE-kernel (default 'de441')")
    br.set_defaults(func=_cmd_breathing)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _make_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
