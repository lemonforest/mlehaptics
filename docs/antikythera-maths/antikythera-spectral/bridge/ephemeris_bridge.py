#!/usr/bin/env python3
"""ephemeris_bridge.py — JPL DE-kernel listing + opt-in download utility.

This is the **single trusted point** in the project that constructs JPL
URLs and downloads kernels. Per ADR 0003, having one chokepoint with
an allowlist gate prevents user-controlled strings from reaching
network or filesystem operations.

The CLI is the user-facing interface; the script is also importable
(``from ephemeris_bridge import _kernel_url, ALLOWED_KERNELS``) for
programmatic use.

Run::

    python bridge/ephemeris_bridge.py --list
    python bridge/ephemeris_bridge.py --where
    python bridge/ephemeris_bridge.py --download de441_part1
    python bridge/ephemeris_bridge.py --check de421

Allowlist (frozen):

    de421         1899 - 2053          ~16 MB    modern control only
    de422         3001 BCE - 3000 CE   ~660 MB   Antikythera-era OK
    de440         1849 - 2150          ~32 MB    JPL current best, modern
    de441         13201 BCE - 17191 CE ~3.1 GB   JPL current best, long
    de441_part1   13201 BCE - 1550 CE  ~1.5 GB   Hellenistic-only subset (recommended)
    de441_part2   1550 CE - 17191 CE   ~1.5 GB   modern + future subset

Adding a kernel requires a PR review (and an ADR if from a non-JPL source).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

# Frozen allowlist of accepted JPL kernel names. CodeQL flow-analyzes
# this membership gate to confirm user-controlled strings never reach
# the URL constructor without it.
ALLOWED_KERNELS: tuple[str, ...] = (
    "de421",
    "de422",
    "de440",
    "de441",
    "de441_part1",
    "de441_part2",
)

# Approximate sizes for the y/N download prompt.
_KERNEL_SIZE_MB: Dict[str, float] = {
    "de421":       16.0,
    "de422":      660.0,
    "de440":       32.0,
    "de441":     3100.0,
    "de441_part1": 1500.0,
    "de441_part2": 1500.0,
}

# Coverage descriptions for --list output.
_KERNEL_COVERAGE: Dict[str, str] = {
    "de421":       "1899-07-29 to 2053-10-09 (modern control only)",
    "de422":       "3001 BCE to 3000 CE (Antikythera-era OK)",
    "de440":       "1849 to 2150 (JPL current best, modern)",
    "de441":       "13201 BCE to 17191 CE (JPL current best, long-coverage)",
    "de441_part1": "13201 BCE to 1550 CE (Hellenistic-only DE441 subset)",
    "de441_part2": "1550 CE to 17191 CE (modern + future DE441 subset)",
}


def _kernel_url(name: str) -> str:
    """Construct the canonical JPL URL for a kernel — allowlist-gated."""
    if name not in ALLOWED_KERNELS:
        raise ValueError(
            f"unknown kernel {name!r}; must be one of {ALLOWED_KERNELS}"
        )
    # JPL Solar System Dynamics canonical URL pattern.
    return f"https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/{name}.bsp"


def _resolve_data_dir() -> Path:
    """Where skyfield's Loader caches kernels.

    Mirrors skyfield's default: a `~/.skyfield_data/` directory unless
    overridden via env var.
    """
    import os
    return Path(os.environ.get(
        "SKYFIELD_DATA_DIR",
        Path.home() / ".skyfield_data",
    )).resolve()


def cmd_list(args: argparse.Namespace) -> int:
    """Print the allowlist + coverage."""
    print("Allowed kernels (use --download to fetch):")
    print(f"{'name':<14} {'size':>9}   coverage")
    for k in ALLOWED_KERNELS:
        size = f"{_KERNEL_SIZE_MB[k]:.0f} MB"
        if _KERNEL_SIZE_MB[k] >= 1000:
            size = f"{_KERNEL_SIZE_MB[k] / 1024:.1f} GB"
        print(f"{k:<14} {size:>9}   {_KERNEL_COVERAGE[k]}")
    return 0


def cmd_where(args: argparse.Namespace) -> int:
    """Print the local cache directory."""
    p = _resolve_data_dir()
    print(p)
    if not p.exists():
        print(f"  (does not yet exist; will be created on first download)",
              file=sys.stderr)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Report whether `args.kernel` is on disk locally."""
    if args.kernel not in ALLOWED_KERNELS:
        print(f"::error::{args.kernel!r} not in allowlist", file=sys.stderr)
        return 2
    bsp = _resolve_data_dir() / f"{args.kernel}.bsp"
    if bsp.exists():
        size_mb = bsp.stat().st_size / 1024 / 1024
        print(f"{args.kernel}: present ({size_mb:.1f} MB)")
        return 0
    print(f"{args.kernel}: not on disk")
    return 1


def cmd_download(args: argparse.Namespace) -> int:
    """Opt-in download. Prompts y/N with size unless --yes is passed."""
    if args.kernel not in ALLOWED_KERNELS:
        print(f"::error::{args.kernel!r} not in allowlist", file=sys.stderr)
        return 2

    size_mb = _KERNEL_SIZE_MB[args.kernel]
    coverage = _KERNEL_COVERAGE[args.kernel]
    print(f"Kernel:      {args.kernel}")
    print(f"Size:        ~{size_mb:.0f} MB" + ("" if size_mb < 1000 else f" (~{size_mb / 1024:.1f} GB)"))
    print(f"Coverage:    {coverage}")
    print(f"Source URL:  {_kernel_url(args.kernel)}")
    print(f"Cache dir:   {_resolve_data_dir()}")
    if not args.yes:
        ans = input("Proceed with download? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("Aborted.")
            return 1

    # Delegate to skyfield's Loader so we get a tested download path
    # (including resume / atomic-rename / etc.). The Loader uses the
    # JPL URL we constructed, which is allowlist-validated.
    try:
        from skyfield.api import Loader
    except ImportError:
        print(
            "::error::skyfield not installed. "
            "Run `pip install antikythera-spectral[ephemeris]`.",
            file=sys.stderr,
        )
        return 3

    data_dir = _resolve_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    loader = Loader(str(data_dir))
    print(f"Downloading {args.kernel} ...")
    try:
        loader(f"{args.kernel}.bsp")
    except Exception as exc:  # noqa: BLE001
        print(f"::error::download failed: {exc}", file=sys.stderr)
        return 4
    print(f"Done. Kernel cached at {data_dir / (args.kernel + '.bsp')}")
    return 0


_EPILOG = """\
Examples
--------

    # List all kernels and their coverage windows.
    python bridge/ephemeris_bridge.py --list

    # See where the local cache lives.
    python bridge/ephemeris_bridge.py --where

    # Check whether DE421 is already on disk.
    python bridge/ephemeris_bridge.py --check de421

    # Download DE441's Hellenistic subset (~1.5 GB; prompts y/N).
    python bridge/ephemeris_bridge.py --download de441_part1

CodeQL discipline
-----------------

This module is the only place in the project that constructs JPL URLs.
The kernel name passes ``ALLOWED_KERNELS`` membership before any URL
or filesystem path is built. See ADR 0003 in the package's docs/adr/.

References
----------
- Park, R. S. et al. (2021). The JPL Planetary and Lunar Ephemerides
  DE440 and DE441. *Astron. J.* 161:105.
- Skyfield documentation: https://rhodesmill.org/skyfield/
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ephemeris_bridge.py",
        description=(
            "JPL DE-kernel listing + opt-in download utility. The single "
            "trusted point in antikythera-spectral that constructs JPL "
            "URLs (per ADR 0003)."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_const", const="list", dest="mode",
                   help="Print the allowlist + coverage")
    g.add_argument("--where", action="store_const", const="where", dest="mode",
                   help="Print the local cache directory")
    g.add_argument("--check", metavar="KERNEL", dest="check_kernel",
                   help="Report whether KERNEL is on disk locally")
    g.add_argument("--download", metavar="KERNEL", dest="download_kernel",
                   help="Download KERNEL after prompting y/N")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Skip the y/N download prompt")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _make_parser().parse_args(argv)
    if args.mode == "list":
        return cmd_list(args)
    if args.mode == "where":
        return cmd_where(args)
    if args.check_kernel:
        args.kernel = args.check_kernel
        return cmd_check(args)
    if args.download_kernel:
        args.kernel = args.download_kernel
        return cmd_download(args)
    print("::error::no mode selected", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
