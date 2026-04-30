"""``antikythera-spectral`` console script — entry point for the CLI.

Subcommand-driven; each subcommand maps to one or two bridge methods
and prints the resulting JSON to stdout (compact or pretty-formatted).

The CLI is intentionally thin: it does input parsing + subcommand
dispatch + JSON serialization. Numerical work happens in the bridge /
facade layer.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import Any, Dict, List, Optional

from antikythera_spectral import bridge
from antikythera_spectral.ephemeris import ALLOWED_KERNELS
from antikythera_spectral.version import __version__
from antikythera_spectral.visibility import SUPPORTED_PLANETS

# Frozen choice lists for argparse. Keeping them out of the parser
# helpers so the lists are easy to grep for.
_KERNEL_CHOICES = list(ALLOWED_KERNELS)
_PLANET_CHOICES = list(SUPPORTED_PLANETS)
_BODY_CHOICES = list(SUPPORTED_PLANETS) + ["sun", "moon"]
_FRAGMENT_CHOICES = ["A", "B", "C", "D", "reconstructed", "all"]


# ──────────────────────────────────────────────────────────────────────
# Output helpers
# ──────────────────────────────────────────────────────────────────────

def _emit(result: Dict[str, Any], *, pretty: bool = True) -> int:
    """Print result JSON; return 0 on ok, 1 on caller-side error."""
    if pretty:
        sys.stdout.write(json.dumps(result, indent=2, sort_keys=True))
    else:
        sys.stdout.write(json.dumps(result, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return 0 if result.get("ok") is not False else 1


def _emit_csv(rows: List[Dict[str, Any]], fieldnames: List[str]) -> int:
    w = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    for row in rows:
        w.writerow(row)
    return 0


# ──────────────────────────────────────────────────────────────────────
# Subcommand implementations
# ──────────────────────────────────────────────────────────────────────

def _cmd_version(args: argparse.Namespace) -> int:
    return _emit(bridge.get_version())


def _cmd_encode(args: argparse.Namespace) -> int:
    out = bridge.get_dial_state(args.jd, D=args.D)
    if args.dial and out.get("ok"):
        # Filter to one dial.
        d = out["dials"].get(args.dial)
        if d is None:
            return _emit({"ok": False, "error": f"unknown dial {args.dial!r}"})
        return _emit({"ok": True, "jd_tdb": out["jd_tdb"], "D": out["D"],
                       "dial": args.dial, **d})
    return _emit(out)


def _cmd_angle(args: argparse.Namespace) -> int:
    return _emit(bridge.get_dial_angle(args.jd, args.dial))


def _cmd_decode(args: argparse.Namespace) -> int:
    import numpy as np
    state = np.load(args.state).get("state") if args.state.endswith(".npz") \
        else np.load(args.state)
    return _emit(bridge.decode_dial(state, args.dial, D=args.D))


def _cmd_date_jd_to_gregorian(args: argparse.Namespace) -> int:
    return _emit(bridge.jd_to_gregorian(args.jd))


def _cmd_date_gregorian_to_jd(args: argparse.Namespace) -> int:
    return _emit(bridge.gregorian_to_jd(
        args.year, args.month, args.day,
        args.hour, args.minute, args.second, args.era,
    ))


def _cmd_date_jd_to_julian(args: argparse.Namespace) -> int:
    return _emit(bridge.jd_to_julian_calendar(args.jd))


def _cmd_date_jd_to_athenian(args: argparse.Namespace) -> int:
    return _emit(bridge.jd_to_athenian(args.jd))


def _cmd_date_jd_to_olympiad(args: argparse.Namespace) -> int:
    return _emit(bridge.jd_to_olympiad(args.jd))


def _cmd_visibility(args: argparse.Namespace) -> int:
    return _emit(bridge.get_visibility_windows(
        args.from_jd, args.to_jd, args.planet,
        precise=args.precise, kernel=args.kernel,
    ))


def _cmd_heliacal(args: argparse.Namespace) -> int:
    return _emit(bridge.get_next_heliacal_rising(
        args.jd, args.planet, precise=args.precise, kernel=args.kernel,
    ))


def _cmd_elongation(args: argparse.Namespace) -> int:
    return _emit(bridge.get_solar_elongation(
        args.jd, args.planet, precise=args.precise, kernel=args.kernel,
    ))


def _cmd_eclipses_search(args: argparse.Namespace) -> int:
    return _emit(bridge.find_eclipses(
        args.from_jd, args.to_jd, kind=args.kind,
        precise=args.precise, kernel=args.kernel,
    ))


def _cmd_eclipses_anchors(args: argparse.Namespace) -> int:
    return _emit(bridge.get_eclipse_anchors(era=args.era))


def _cmd_periods(args: argparse.Namespace) -> int:
    return _emit(bridge.get_period_relations(source=args.source))


def _cmd_compare_ephemerides(args: argparse.Namespace) -> int:
    return _emit(bridge.compare_ephemerides(
        args.jd, args.body, args.kernel_a, args.kernel_b,
    ))


def _cmd_compare_models(args: argparse.Namespace) -> int:
    return _emit(bridge.compare_models(
        args.jd, args.body, args.model_a, args.model_b, args.kernel,
    ))


def _cmd_compare_reconstructions(args: argparse.Namespace) -> int:
    return _emit(bridge.compare_reconstructions(args.jd))


def _cmd_whatif_encode(args: argparse.Namespace) -> int:
    return _emit(bridge.encode_with_custom_train(
        args.jd, args.dial, args.p, args.q,
    ))


def _cmd_fragment(args: argparse.Namespace) -> int:
    return _emit(bridge.get_fragment_inventory(args.id))


def _cmd_goalyear_predict(args: argparse.Namespace) -> int:
    return _emit(bridge.goalyear_predict(args.planet, args.jd, source=args.source))


def _cmd_goalyear_compare(args: argparse.Namespace) -> int:
    return _emit(bridge.goalyear_compare(args.planet, args.jd))


def _cmd_animate(args: argparse.Namespace) -> int:
    out = bridge.export_animation(
        args.from_jd, args.to_jd, args.step_days,
        format=args.format, D=args.D,
    )
    if args.out and out.get("ok"):
        import base64
        with open(args.out, "wb") as f:
            f.write(base64.b64decode(out["payload_b64"]))
        return _emit({"ok": True, "format": out["format"],
                       "n_bytes": out["n_bytes"], "wrote": args.out})
    return _emit(out)


def _cmd_hypotheses(args: argparse.Namespace) -> int:
    out = bridge.run_hypothesis_battery()
    if not out.get("ok"):
        return _emit(out)
    if args.csv_out is not None:
        # Output to stdout as CSV (Othello-compatible 6-field format).
        if args.csv_out == "-":
            return _emit_csv(out["rows"],
                              ["id", "statement", "computed_value",
                               "threshold", "status", "notes"])
        with open(args.csv_out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["id", "statement", "computed_value",
                                                "threshold", "status", "notes"],
                               extrasaction="ignore")
            w.writeheader()
            for row in out["rows"]:
                w.writerow(row)
        return _emit({"ok": True, "wrote": args.csv_out, "n_rows": out["n_rows"]})
    return _emit(out)


def _cmd_hypothesis(args: argparse.Namespace) -> int:
    return _emit(bridge.get_hypothesis(args.id))


def _cmd_kernel_list(args: argparse.Namespace) -> int:
    from antikythera_spectral.ephemeris import (
        ALLOWED_KERNELS, available_kernels, is_available,
    )
    out: Dict[str, Any] = {
        "ok": True,
        "allowed": list(ALLOWED_KERNELS),
        "available_local": list(available_kernels()),
    }
    return _emit(out)


# ──────────────────────────────────────────────────────────────────────
# Parser construction
# ──────────────────────────────────────────────────────────────────────

_TOPLEVEL_EPILOG = """\
Examples
--------

    # Encode a date and read the Mars dial.
    antikythera-spectral encode --jd 1684500.0 --dial Mars_synodic_period_relation

    # Convert REFERENCE_JD to Olympiad coordinates (Antikythera back-dial format).
    antikythera-spectral date jd-to-olympiad 1684595.0

    # When does Mars next emerge from solar glare? (needs DE421 on disk)
    antikythera-spectral heliacal --planet mars --jd 1684500.0

    # Compare DE421 vs DE441 on Mars at J2000 (both kernels needed locally).
    antikythera-spectral compare ephemerides --jd 2451545.0 --body mars \\
                          --kernel-a de421 --kernel-b de441_part1

    # What if we used Venus 5/8 instead of Freeth's 289/462?
    antikythera-spectral whatif encode --jd 1684500.0 \\
                          --dial Venus_synodic_period_relation --p 5 --q 8

    # Run the full 31-row H-battery, emit CSV.
    antikythera-spectral hypotheses --csv-out -

    # Export an animation (10 yr at 30-day step) for a web viewer.
    antikythera-spectral animate --from-jd 1684500 --to-jd 1688150 \\
                          --step-days 30 --format json -o animation.json

References
----------

- Bridge API contract: docs/bridge_api.md
- Hypothesis battery: notebook §11 (../antikythera_spectral_research_notebook.md)
- Plan + ADRs: docs/adr/
"""


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="antikythera-spectral",
        description=(
            "Hyperdimensional-computing model of the Antikythera mechanism. "
            "Encode any date as a state vector across the mechanism's dials, "
            "decode states back to dates, run the 31-row hypothesis battery, "
            "and compare ephemeris kernels / Greek planetary models / "
            "reconstructions side-by-side."
        ),
        epilog=_TOPLEVEL_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version",
                   version=f"antikythera-spectral {__version__}")

    sub = p.add_subparsers(dest="cmd", required=True)

    # version
    v_p = sub.add_parser(
        "version",
        help="Print version + manifest info",
        description="Prints the package version + the codegen manifest.",
    )
    v_p.set_defaults(func=_cmd_version)

    # encode / angle / decode
    e = sub.add_parser(
        "encode",
        help="Encode a JD as the per-dial state",
        description="Build the HDC state vector and per-dial residues for a date.",
    )
    e.add_argument("--jd", type=float, required=True, help="Julian Day in TDB")
    e.add_argument("--D", type=int, default=940, choices=[940, 13440],
                   help="Encoder dimension (default 940)")
    e.add_argument("--dial", type=str, default=None,
                   help="If set, output only this dial's state")
    e.set_defaults(func=_cmd_encode)

    a = sub.add_parser(
        "angle",
        help="Continuous dial angle at a JD",
        description="D-independent dial angle in degrees.",
    )
    a.add_argument("--jd", type=float, required=True, help="Julian Day in TDB")
    a.add_argument("--dial", type=str, required=True, help="dial name")
    a.set_defaults(func=_cmd_angle)

    d = sub.add_parser(
        "decode",
        help="Decode a saved state file",
        description="Recover the residue of a dial from an .npy / .npz state vector.",
    )
    d.add_argument("--state", type=str, required=True,
                   help="Path to .npy or .npz state file")
    d.add_argument("--dial", type=str, required=True, help="dial name")
    d.add_argument("--D", type=int, default=940, choices=[940, 13440],
                   help="Encoder dimension that produced the state (default 940)")
    d.set_defaults(func=_cmd_decode)

    # date subcommands
    date = sub.add_parser(
        "date",
        help="Calendar conversion (Gregorian / Julian / Athenian / Olympiad)",
        description="Convert between Julian Day and four calendar systems.",
    )
    date_sub = date.add_subparsers(dest="date_cmd", required=True)
    djg = date_sub.add_parser(
        "jd-to-gregorian",
        help="Convert JD to proleptic Gregorian date",
        description="Proleptic Gregorian calendar date (year, month, day, time, era).",
    )
    djg.add_argument("jd", type=float, help="Julian Day in TDB")
    djg.set_defaults(func=_cmd_date_jd_to_gregorian)
    dgj = date_sub.add_parser(
        "gregorian-to-jd",
        help="Convert proleptic Gregorian date to JD",
        description="Reverse direction: build a Julian Day from a Gregorian date.",
    )
    dgj.add_argument("year", type=int, help="positive ordinal; era=BCE for pre-1 CE")
    dgj.add_argument("month", type=int, help="1..12")
    dgj.add_argument("day", type=int, help="1..31")
    dgj.add_argument("--hour", type=int, default=0)
    dgj.add_argument("--minute", type=int, default=0)
    dgj.add_argument("--second", type=int, default=0)
    dgj.add_argument("--era", choices=["CE", "BCE"], default="CE")
    dgj.set_defaults(func=_cmd_date_gregorian_to_jd)
    djj = date_sub.add_parser(
        "jd-to-julian",
        help="Convert JD to Julian-calendar date (pre-1582 historical sources)",
        description="Julian calendar (in use 45 BCE -- 1582-10-15 CE).",
    )
    djj.add_argument("jd", type=float, help="Julian Day in TDB")
    djj.set_defaults(func=_cmd_date_jd_to_julian)
    dja = date_sub.add_parser(
        "jd-to-athenian",
        help="Convert JD to Attic month + day (Athenian, archon=null in v0.1.0)",
        description=(
            "Attic-month structure (Hekatombaion .. Skirophorion). Archon "
            "name pending v0.2.0; see ADR 0007 for the discipline."
        ),
    )
    dja.add_argument("jd", type=float, help="Julian Day in TDB")
    dja.set_defaults(func=_cmd_date_jd_to_athenian)
    djo = date_sub.add_parser(
        "jd-to-olympiad",
        help="Convert JD to Olympiad year (Antikythera back-dial format)",
        description=(
            "Olympiad number + year-in-Olympiad. Olympiad I.1 = 776 BCE. "
            "Freeth, Jones, Steele & Bitsakis 2008 reconstruct the back dial."
        ),
    )
    djo.add_argument("jd", type=float, help="Julian Day in TDB")
    djo.set_defaults(func=_cmd_date_jd_to_olympiad)

    # astronomy
    vis = sub.add_parser(
        "visibility",
        help="Heliacal-visibility windows for a planet over a JD range",
        description="Returns (heliacal_rising, heliacal_setting) JD pairs.",
    )
    vis.add_argument("--planet", required=True, choices=_PLANET_CHOICES)
    vis.add_argument("--from-jd", dest="from_jd", type=float, required=True,
                     help="Lower bound of the JD range (TDB)")
    vis.add_argument("--to-jd", dest="to_jd", type=float, required=True,
                     help="Upper bound of the JD range (TDB)")
    vis.add_argument("--kernel", default="de421", choices=_KERNEL_CHOICES,
                     help="JPL DE-kernel (only used when --precise)")
    vis.add_argument("--precise", action="store_true",
                     help=("Use skyfield + JPL DE-kernel (sub-arcsec; needs "
                           "[ephemeris] extras). Default uses algebraic "
                           "synodic-cycle propagation (±1 day, no kernel needed)."))
    vis.set_defaults(func=_cmd_visibility)

    h = sub.add_parser(
        "heliacal",
        help="Next heliacal rising of a planet after a JD",
        description="When the planet next emerges from solar glare.",
    )
    h.add_argument("--planet", required=True, choices=_PLANET_CHOICES)
    h.add_argument("--jd", type=float, required=True,
                   help="Search start JD (TDB)")
    h.add_argument("--kernel", default="de421", choices=_KERNEL_CHOICES,
                   help="JPL DE-kernel (only used when --precise)")
    h.add_argument("--precise", action="store_true",
                   help="Use skyfield (default: closed-form algebraic propagation)")
    h.set_defaults(func=_cmd_heliacal)

    el = sub.add_parser(
        "elongation",
        help="Solar elongation at a JD",
        description="Angular separation (degrees) between the Sun and the target body.",
    )
    el.add_argument("--planet", required=True, choices=_PLANET_CHOICES)
    el.add_argument("--jd", type=float, required=True, help="Julian Day in TDB")
    el.add_argument("--kernel", default="de421", choices=_KERNEL_CHOICES,
                    help="JPL DE-kernel (only used when --precise)")
    el.add_argument("--precise", action="store_true",
                    help="Use skyfield (default: sinusoidal phase model, ±5°)")
    el.set_defaults(func=_cmd_elongation)

    es = sub.add_parser(
        "eclipses",
        help="Eclipse search over a JD band (sky-driven syzygy enumeration)",
        description="Scans DE-kernel ephemeris for new-moon and full-moon syzygies.",
    )
    es.add_argument("--from-jd", dest="from_jd", type=float, required=True)
    es.add_argument("--to-jd", dest="to_jd", type=float, required=True)
    es.add_argument("--kind", choices=["lunar", "solar", "all"], default="all",
                    help="Eclipse kind filter")
    es.add_argument("--kernel", default="de421", choices=_KERNEL_CHOICES,
                    help="JPL DE-kernel (only used when --precise)")
    es.add_argument("--precise", action="store_true",
                    help=("Use skyfield sky-driven syzygy enumeration. Default uses "
                          "Saros-cycle propagation from frozen anchors (±1-2 days)."))
    es.set_defaults(func=_cmd_eclipses_search)

    ea = sub.add_parser(
        "eclipse-anchors",
        help="List frozen Hellenistic / modern Saros anchors",
        description="Reads research.hellenistic_eclipses' SSOT (no kernel needed).",
    )
    ea.add_argument("--era", choices=["hellenistic", "modern", "all"],
                    default="hellenistic", help="Anchor era filter")
    ea.set_defaults(func=_cmd_eclipses_anchors)

    pr = sub.add_parser(
        "periods",
        help="MUL.APIN / Almagest period relations",
        description="Babylonian + Greek period-relation corpus with confidence tags.",
    )
    pr.add_argument("--source", choices=["mulapin", "almagest", "all"],
                    default="almagest", help="Source corpus filter")
    pr.set_defaults(func=_cmd_periods)

    # compare
    cmp = sub.add_parser(
        "compare",
        help="Side-by-side comparators",
        description="DE-kernel / Greek-model / reconstruction comparators.",
    )
    cmp_sub = cmp.add_subparsers(dest="compare_cmd", required=True)
    ce = cmp_sub.add_parser(
        "ephemerides",
        help="Position delta between two JPL kernels at the same JD/body",
        description="Reports the delta in arcseconds, kilometers, AU.",
    )
    ce.add_argument("--jd", type=float, required=True)
    ce.add_argument("--body", required=True, choices=_BODY_CHOICES)
    ce.add_argument("--kernel-a", required=True, choices=_KERNEL_CHOICES)
    ce.add_argument("--kernel-b", required=True, choices=_KERNEL_CHOICES)
    ce.set_defaults(func=_cmd_compare_ephemerides)
    cm = cmp_sub.add_parser(
        "models",
        help="uniform / Hipparchus epicycle / Ptolemy equant residuals (Mars-only in v0.1.0)",
        description="Compare Greek planetary models against ephemeris truth.",
    )
    cm.add_argument("--jd", type=float, required=True)
    cm.add_argument("--body", required=True, choices=["mars"],
                    help="v0.1.0 supports 'mars' only")
    cm.add_argument("--model-a", required=True,
                    choices=["uniform", "epicycle", "equant"])
    cm.add_argument("--model-b", required=True,
                    choices=["uniform", "epicycle", "equant"])
    cm.add_argument("--kernel", default="de421", choices=_KERNEL_CHOICES)
    cm.set_defaults(func=_cmd_compare_models)
    cr = cmp_sub.add_parser(
        "reconstructions",
        help="Freeth / Wright / Price-1974 dial-reading disagreements",
        description="Lists every gear where reconstructions disagree on tooth count.",
    )
    cr.add_argument("--jd", type=float, required=True)
    cr.set_defaults(func=_cmd_compare_reconstructions)

    # what-if
    wi = sub.add_parser(
        "whatif",
        help="What-if encoder (alternative gear ratios)",
        description=(
            "Re-encode a dial with an arbitrary p/q ratio. Inputs gated by "
            "ADR 0008: p, q in [1, 500], gcd(p, q) = 1, dial in DIAL_SPECS."
        ),
    )
    wi_sub = wi.add_subparsers(dest="whatif_cmd", required=True)
    we = wi_sub.add_parser(
        "encode",
        help="Encode a date with a custom p/q gear ratio",
        description="Outputs residue + angle for the alternative ratio.",
    )
    we.add_argument("--jd", type=float, required=True)
    we.add_argument("--dial", required=True)
    we.add_argument("--p", type=int, required=True)
    we.add_argument("--q", type=int, required=True)
    we.set_defaults(func=_cmd_whatif_encode)

    # fragment
    fr = sub.add_parser(
        "fragment",
        help="Archaeological gear inventory (per Antikythera fragment)",
        description="Lists gears attested in fragments A/B/C/D + reconstructed.",
    )
    fr_sub = fr.add_subparsers(dest="frag_cmd", required=True)
    fi = fr_sub.add_parser(
        "inventory",
        help="List gears keyed by fragment",
        description="Reads _data/fragments.json (codegen-emitted from gear_database).",
    )
    fi.add_argument("--id", default="all", choices=_FRAGMENT_CHOICES,
                    help="Fragment letter (A/B/C/D/reconstructed) or 'all'")
    fi.set_defaults(func=_cmd_fragment)

    # goal-year
    gy = sub.add_parser(
        "goalyear",
        help="Babylonian Goal-Year overlay (Mars 47-yr, Saturn 59-yr, etc.)",
        description="What a Babylonian astronomer would have predicted via the N-year cycle.",
    )
    gy_sub = gy.add_subparsers(dest="gy_cmd", required=True)
    gp = gy_sub.add_parser(
        "predict",
        help="Look up the JD that the Goal-Year cycle directs you to query",
        description="Returns the lookup-JD = jd_query - cycle_days.",
    )
    gp.add_argument("--planet", required=True, choices=_PLANET_CHOICES)
    gp.add_argument("--jd", type=float, required=True)
    gp.add_argument("--source", choices=["mulapin", "almagest"], default="mulapin")
    gp.set_defaults(func=_cmd_goalyear_predict)
    gc = gy_sub.add_parser(
        "compare",
        help="Goal-Year prediction + encoder reading side-by-side",
        description="Returns Babylonian-cycle prediction and the encoder's dial angle for comparison.",
    )
    gc.add_argument("--planet", required=True, choices=_PLANET_CHOICES)
    gc.add_argument("--jd", type=float, required=True)
    gc.set_defaults(func=_cmd_goalyear_compare)

    # animation
    an = sub.add_parser("animate", help="Time-series state export")
    an.add_argument("--from-jd", dest="from_jd", type=float, required=True)
    an.add_argument("--to-jd", dest="to_jd", type=float, required=True)
    an.add_argument("--step-days", dest="step_days", type=float, default=10.0)
    an.add_argument("--format", choices=["json", "npz"], default="json")
    an.add_argument("--D", type=int, default=940, choices=[940, 13440])
    an.add_argument("-o", "--out", default=None,
                    help="Write payload to file (else base64 JSON)")
    an.set_defaults(func=_cmd_animate)

    # hypotheses
    hy = sub.add_parser("hypotheses", help="Run all 31 H-battery rows")
    hy.add_argument("--csv-out", dest="csv_out", default=None,
                     help="Write CSV ('-' = stdout, else filename)")
    hy.set_defaults(func=_cmd_hypotheses)

    h1 = sub.add_parser("hypothesis", help="Single-hypothesis lookup")
    h1.add_argument("id", help="Hypothesis ID, e.g. B-H1, E-H1b, G-H8")
    h1.set_defaults(func=_cmd_hypothesis)

    # kernel
    kn = sub.add_parser(
        "kernel",
        help="JPL DE-kernel utilities",
        description="List or check JPL DE-series ephemeris kernels.",
    )
    kn_sub = kn.add_subparsers(dest="kernel_cmd", required=True)
    kn_sub.add_parser(
        "list",
        help="List allowed + locally-available kernels",
        description=(
            "Prints the ALLOWED_KERNELS allowlist (per ADR 0003) plus any "
            "kernels currently on disk in the local skyfield cache."
        ),
    ).set_defaults(func=_cmd_kernel_list)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _make_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
