#!/usr/bin/env python3
"""chess_spectral_4d.cli — argparse CLI for the 4D chess-spectral encoder.

Every subcommand exposes `--help`. This is the discovery contract for the
4D tooling: run `--help` first, always.

Subcommands (v1 skeleton):

    tables-verify   Run validation gates from each implementation phase.
                    --phase 1 checks piece mobility on Z_8^4 (rook=28,
                    king=80, knight=48, bishop 2 components).
    encode-fen4     Encode a single 4D position literal to a v3 .spectralz.
                    (stubbed; needs encoder_4d + frame_4d)
    encode-moves4   Encode a JSONL move log to v3 .spectralz.
                    Schema: one JSON object per line with fields
                    {ply, from:[x,y,z,w], to:[x,y,z,w], promo, flags}.
                    (stubbed; needs encoder_4d + frame_4d)
    corpus-gen      Wrap N JSONL move logs into a corpus folder mirroring
                    the 2D `spectral_py corpus` layout. (stubbed)
    version         Print version + v3 magic/format info.

Exit codes:
    0   success
    2   argument / usage error (also the argparse default)
    3   runtime error (I/O, validation failure, etc.)
    4   not implemented yet in this build
"""
from __future__ import annotations

import argparse
import os
import sys

# Make sibling `chess_spectral` importable when this CLI is run from any cwd.
HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.abspath(os.path.join(HERE, os.pardir))
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from chess_spectral_4d import (  # noqa: E402
    VERSION,
    ENCODING_DIM_4D,
    BOARD_SIDE_4D,
    N_DIMENSIONS_4D,
)

SPECTRALZ_V3_MAGIC = "LARTPSEC"
SPECTRALZ_VERSION = 3


# --- stub helper ---------------------------------------------------------

def _not_implemented(cmd: str, what: str) -> int:
    print(
        f"{cmd}: {what} is not yet implemented in this build.\n"
        f"       See plan file when-we-need-to-spicy-seahorse.md "
        f"for phase order.",
        file=sys.stderr,
    )
    return 4


# --- tables-verify -------------------------------------------------------

def cmd_tables_verify(args: argparse.Namespace) -> int:
    """Run one (or all) phase validation gates. Each gate prints a single
    pass/fail line. Return 0 iff every requested gate passes."""
    phases = ["1", "2", "3", "4"] if args.phase == "all" else [args.phase]

    overall = 0
    for p in phases:
        if p == "1":
            rc = _run_phase_gate("1", "verify_phase1", verbose=args.verbose)
        elif p == "2":
            rc = _run_phase_gate("2", "verify_phase2", verbose=args.verbose)
        elif p == "3":
            rc = _run_phase_gate("3", "verify_phase3", verbose=args.verbose)
        elif p == "4":
            rc = _run_phase_gate("4", "verify_phase4", verbose=args.verbose)
        else:
            print(f"tables-verify: unknown phase {p!r}", file=sys.stderr)
            rc = 2
        sys.stdout.flush()
        if rc != 0 and overall == 0:
            overall = rc

    return overall


def _run_phase_gate(phase: str, fn_name: str, verbose: bool) -> int:
    """Generic phase-gate runner: import `fn_name` from
    chess_spectral.tables_4d, call it with verbose=..., print report
    lines, return 0 on success / 3 on AssertionError or ImportError."""
    try:
        from chess_spectral import tables_4d
        fn = getattr(tables_4d, fn_name)
    except (ImportError, AttributeError) as e:
        print(f"tables-verify phase {phase}: import error ({e})",
              file=sys.stderr)
        return 3

    try:
        report = fn(verbose=verbose)
    except AssertionError as e:
        print(f"tables-verify phase {phase}: FAIL -- {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"tables-verify phase {phase}: ERROR -- {type(e).__name__}: {e}",
              file=sys.stderr)
        return 3

    for line in report:
        print(f"  {line}")
    print(f"tables-verify phase {phase}: PASS")
    return 0


# --- encode-fen4 ---------------------------------------------------------

def cmd_encode_fen4(args: argparse.Namespace) -> int:
    return _not_implemented("encode-fen4", "4D FEN encoder")


# --- encode-moves4 -------------------------------------------------------

def cmd_encode_moves4(args: argparse.Namespace) -> int:
    return _not_implemented("encode-moves4", "JSONL move-log encoder")


# --- corpus-gen ----------------------------------------------------------

def cmd_corpus_gen(args: argparse.Namespace) -> int:
    return _not_implemented("corpus-gen", "4D corpus builder")


# --- version -------------------------------------------------------------

def cmd_version(args: argparse.Namespace) -> int:
    print(f"chess_spectral_4d {VERSION}")
    print(f"  spectralz magic:    {SPECTRALZ_V3_MAGIC!r}")
    print(f"  spectralz version:  {SPECTRALZ_VERSION}")
    print(f"  encoding_dim:       {ENCODING_DIM_4D}")
    print(f"  board_dim_side:     {BOARD_SIDE_4D}")
    print(f"  n_dimensions:       {N_DIMENSIONS_4D}")
    return 0


# --- parser --------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="chess_spectral_4d.cli",
        description=(
            "CLI for the 4D chess-spectral encoder "
            "(B4 symmetry, Z_8^4 lattice). v1 is Python-only; C port "
            "is v1.1."
        ),
    )
    # Optional subcommand so bare invocation prints full help, matching
    # the 2D spectral_py CLI.
    sub = ap.add_subparsers(dest="cmd")

    # tables-verify
    p_tv = sub.add_parser(
        "tables-verify",
        help="Run phase-N validation gates (pre-flight before encoding)",
        description=(
            "Run validation gates from each implementation phase. "
            "--phase 1 covers piece mobility on the Z_8^4 lattice and "
            "cross-checks against Oana & Chiru (AppliedMath 6(3):48, "
            "2026) section 3."
        ),
    )
    p_tv.add_argument(
        "--phase", choices=("1", "2", "3", "4", "all"), default="all",
        help="which phase gate(s) to run (default: all)",
    )
    p_tv.add_argument(
        "-v", "--verbose", action="store_true",
        help="print per-check details (sample squares, degrees, etc.)",
    )
    p_tv.set_defaults(func=cmd_tables_verify)

    # encode-fen4
    p_fen = sub.add_parser(
        "encode-fen4",
        help="Encode a single 4D position literal to a v3 .spectralz",
    )
    p_fen.add_argument("--fen", required=True,
                       help="4D position literal (format TBD in v1.1)")
    p_fen.add_argument("-o", "--output", help="output path")
    p_fen.add_argument("-z", "--compress", action="store_true",
                       help="gzip the output")
    p_fen.set_defaults(func=cmd_encode_fen4)

    # encode-moves4
    p_mv = sub.add_parser(
        "encode-moves4",
        help="Encode a JSONL move log to a v3 .spectralz",
        description=(
            "Encode a JSONL move log (schema cs4d-moves/v1) to a v3 "
            ".spectralz. One JSON object per line: "
            "{ply, from:[x,y,z,w], to:[x,y,z,w], promo, flags}."
        ),
    )
    p_mv.add_argument("--moves", required=True,
                      help="path to .jsonl move log")
    p_mv.add_argument("-o", "--output", help="output path")
    p_mv.add_argument("-z", "--compress", action="store_true",
                      help="gzip the output")
    p_mv.add_argument("--start", type=int, default=0,
                      help="skip to ply N (0-indexed) before encoding")
    p_mv.add_argument("--count", type=int, default=0,
                      help="encode at most K plies (0 = no limit)")
    p_mv.set_defaults(func=cmd_encode_moves4)

    # corpus-gen
    p_cor = sub.add_parser(
        "corpus-gen",
        help="Wrap N JSONL move logs into a viewer-ready corpus folder",
    )
    p_cor.add_argument("--games", required=True, nargs="+",
                       help="one or more JSONL move-log paths")
    p_cor.add_argument("--run-id",
                       help="output folder name under --results-root")
    p_cor.add_argument("--results-root",
                       help="parent directory for the run folder")
    p_cor.add_argument("--limit", type=int, default=None,
                       help="max total games to process (default: no limit)")
    p_cor.set_defaults(func=cmd_corpus_gen)

    # version
    p_ver = sub.add_parser("version", help="Print version + format info")
    p_ver.set_defaults(func=cmd_version)

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if getattr(args, "func", None) is None:
        ap.print_help(sys.stderr)
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
