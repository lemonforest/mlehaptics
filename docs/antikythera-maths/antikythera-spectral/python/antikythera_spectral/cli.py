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
from antikythera_spectral.version import __version__


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
        args.from_jd, args.to_jd, args.planet, args.kernel,
    ))


def _cmd_heliacal(args: argparse.Namespace) -> int:
    return _emit(bridge.get_next_heliacal_rising(args.jd, args.planet, args.kernel))


def _cmd_elongation(args: argparse.Namespace) -> int:
    return _emit(bridge.get_solar_elongation(args.jd, args.planet, args.kernel))


def _cmd_eclipses_search(args: argparse.Namespace) -> int:
    return _emit(bridge.find_eclipses(
        args.from_jd, args.to_jd, kind=args.kind, kernel=args.kernel,
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version",
                   version=f"antikythera-spectral {__version__}")

    sub = p.add_subparsers(dest="cmd", required=True)

    # version
    sub.add_parser("version", help="Print version + manifest info").set_defaults(func=_cmd_version)

    # encode / angle / decode
    e = sub.add_parser("encode", help="Encode a JD as the per-dial state")
    e.add_argument("--jd", type=float, required=True, help="Julian Day in TDB")
    e.add_argument("--D", type=int, default=940, choices=[940, 13440])
    e.add_argument("--dial", type=str, default=None,
                   help="If set, output only this dial's state")
    e.set_defaults(func=_cmd_encode)

    a = sub.add_parser("angle", help="Continuous dial angle at a JD")
    a.add_argument("--jd", type=float, required=True)
    a.add_argument("--dial", type=str, required=True)
    a.set_defaults(func=_cmd_angle)

    d = sub.add_parser("decode", help="Decode a saved state file")
    d.add_argument("--state", type=str, required=True,
                   help="Path to .npy or .npz state file")
    d.add_argument("--dial", type=str, required=True)
    d.add_argument("--D", type=int, default=940, choices=[940, 13440])
    d.set_defaults(func=_cmd_decode)

    # date subcommands
    date = sub.add_parser("date", help="Calendar conversion")
    date_sub = date.add_subparsers(dest="date_cmd", required=True)
    djg = date_sub.add_parser("jd-to-gregorian")
    djg.add_argument("jd", type=float)
    djg.set_defaults(func=_cmd_date_jd_to_gregorian)
    dgj = date_sub.add_parser("gregorian-to-jd")
    dgj.add_argument("year", type=int)
    dgj.add_argument("month", type=int)
    dgj.add_argument("day", type=int)
    dgj.add_argument("--hour", type=int, default=0)
    dgj.add_argument("--minute", type=int, default=0)
    dgj.add_argument("--second", type=int, default=0)
    dgj.add_argument("--era", choices=["CE", "BCE"], default="CE")
    dgj.set_defaults(func=_cmd_date_gregorian_to_jd)
    djj = date_sub.add_parser("jd-to-julian")
    djj.add_argument("jd", type=float)
    djj.set_defaults(func=_cmd_date_jd_to_julian)
    dja = date_sub.add_parser("jd-to-athenian")
    dja.add_argument("jd", type=float)
    dja.set_defaults(func=_cmd_date_jd_to_athenian)
    djo = date_sub.add_parser("jd-to-olympiad")
    djo.add_argument("jd", type=float)
    djo.set_defaults(func=_cmd_date_jd_to_olympiad)

    # astronomy
    v = sub.add_parser("visibility", help="Heliacal-visibility windows")
    v.add_argument("--planet", required=True)
    v.add_argument("--from-jd", dest="from_jd", type=float, required=True)
    v.add_argument("--to-jd", dest="to_jd", type=float, required=True)
    v.add_argument("--kernel", default="de421")
    v.set_defaults(func=_cmd_visibility)

    h = sub.add_parser("heliacal", help="Next heliacal rising of a planet")
    h.add_argument("--planet", required=True)
    h.add_argument("--jd", type=float, required=True)
    h.add_argument("--kernel", default="de421")
    h.set_defaults(func=_cmd_heliacal)

    el = sub.add_parser("elongation", help="Solar elongation at a JD")
    el.add_argument("--planet", required=True)
    el.add_argument("--jd", type=float, required=True)
    el.add_argument("--kernel", default="de421")
    el.set_defaults(func=_cmd_elongation)

    es = sub.add_parser("eclipses", help="Eclipse search over a JD band")
    es.add_argument("--from-jd", dest="from_jd", type=float, required=True)
    es.add_argument("--to-jd", dest="to_jd", type=float, required=True)
    es.add_argument("--kind", choices=["lunar", "solar", "all"], default="all")
    es.add_argument("--kernel", default="de421")
    es.set_defaults(func=_cmd_eclipses_search)

    ea = sub.add_parser("eclipse-anchors",
                          help="List frozen Hellenistic / modern Saros anchors")
    ea.add_argument("--era", choices=["hellenistic", "modern", "all"],
                    default="hellenistic")
    ea.set_defaults(func=_cmd_eclipses_anchors)

    pr = sub.add_parser("periods",
                         help="MUL.APIN / Almagest period relations")
    pr.add_argument("--source", choices=["mulapin", "almagest", "all"],
                    default="almagest")
    pr.set_defaults(func=_cmd_periods)

    # compare
    cmp = sub.add_parser("compare", help="Side-by-side comparators")
    cmp_sub = cmp.add_subparsers(dest="compare_cmd", required=True)
    ce = cmp_sub.add_parser("ephemerides")
    ce.add_argument("--jd", type=float, required=True)
    ce.add_argument("--body", required=True)
    ce.add_argument("--kernel-a", required=True)
    ce.add_argument("--kernel-b", required=True)
    ce.set_defaults(func=_cmd_compare_ephemerides)
    cm = cmp_sub.add_parser("models")
    cm.add_argument("--jd", type=float, required=True)
    cm.add_argument("--body", required=True)
    cm.add_argument("--model-a", required=True,
                    choices=["uniform", "epicycle", "equant"])
    cm.add_argument("--model-b", required=True,
                    choices=["uniform", "epicycle", "equant"])
    cm.add_argument("--kernel", default="de421")
    cm.set_defaults(func=_cmd_compare_models)
    cr = cmp_sub.add_parser("reconstructions")
    cr.add_argument("--jd", type=float, required=True)
    cr.set_defaults(func=_cmd_compare_reconstructions)

    # what-if
    wi = sub.add_parser("whatif", help="What-if encoder")
    wi_sub = wi.add_subparsers(dest="whatif_cmd", required=True)
    we = wi_sub.add_parser("encode")
    we.add_argument("--jd", type=float, required=True)
    we.add_argument("--dial", required=True)
    we.add_argument("--p", type=int, required=True)
    we.add_argument("--q", type=int, required=True)
    we.set_defaults(func=_cmd_whatif_encode)

    # fragment
    fr = sub.add_parser("fragment", help="Archaeological gear inventory")
    fr_sub = fr.add_subparsers(dest="frag_cmd", required=True)
    fi = fr_sub.add_parser("inventory")
    fi.add_argument("--id", default="all",
                    help="Fragment letter (A/B/C/D/reconstructed) or 'all'")
    fi.set_defaults(func=_cmd_fragment)

    # goal-year
    gy = sub.add_parser("goalyear", help="Babylonian Goal-Year overlay")
    gy_sub = gy.add_subparsers(dest="gy_cmd", required=True)
    gp = gy_sub.add_parser("predict")
    gp.add_argument("--planet", required=True)
    gp.add_argument("--jd", type=float, required=True)
    gp.add_argument("--source", choices=["mulapin", "almagest"], default="mulapin")
    gp.set_defaults(func=_cmd_goalyear_predict)
    gc = gy_sub.add_parser("compare")
    gc.add_argument("--planet", required=True)
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
    kn = sub.add_parser("kernel", help="JPL DE-kernel utilities")
    kn_sub = kn.add_subparsers(dest="kernel_cmd", required=True)
    kn_sub.add_parser("list",
                       help="List allowed + locally-available kernels"
                       ).set_defaults(func=_cmd_kernel_list)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _make_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
