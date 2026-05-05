"""Lazy JPL DE-kernel loader — shared infrastructure for E-H1, E-H2, E-H4.

The Antikythera-maths research scaffold validates the encoder against
JPL's DE-series ephemeris files.  Different eras of validation need
different kernels:

    de421         1899 - 2053         (~16 MB)   Modern control only.
    de422         3001 BCE - 3000 CE  (~660 MB)  Antikythera-era OK.
    de441         13201 BCE - 17191 CE (~3 GB)   JPL current best.
    de441_part1   13201 BCE - 1550 CE  (~1.5 GB) Hellenistic-only subset.
    de441_part2   1550 CE - 17191 CE   (~1.5 GB) Modern+future subset.

The Hellenistic anchor band (200 BCE - 100 CE) sits comfortably inside
DE422 and inside DE441_part1; the entire two-millennium era is invisible
to DE421 (which only reaches back to 1899).  This module:

- Imports ``skyfield`` lazily (the module top is import-safe even if
  skyfield is unavailable; failure mode is ``load_ephemeris() -> None``).
- Caches loaded bundles per kernel name so a long H-battery run pays
  the disk I/O once.
- Never auto-downloads.  ``download_kernel(name)`` is the explicit
  on-ramp; it prompts y/N with the expected size before fetching, since
  DE441 alone is ~3 GB.
- Returns an ``EphemerisBundle`` NamedTuple keyed by body name (earth,
  sun, moon, mars, ...) so callers never see the raw skyfield handle.

Citations
---------
Park, R. S. et al. (2021).  The JPL Planetary and Lunar Ephemerides
    DE440 and DE441.  Astron. J. 161:105.
Folkner, W. M. et al. (2014).  The Planetary and Lunar Ephemerides
    DE430 and DE431.  IPN Progress Report 42-196.

Skyfield documentation: https://rhodesmill.org/skyfield/
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Kernel catalog
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KernelSpec:
    name: str
    filename: str
    coverage_jd: Tuple[float, float]
    coverage_iso: Tuple[str, str]
    size_mb: int
    description: str


KERNEL_CATALOG: Dict[str, KernelSpec] = {
    "de421": KernelSpec(
        name="de421",
        filename="de421.bsp",
        coverage_jd=(2414992.5, 2471184.5),
        coverage_iso=("1899-07-29", "2053-10-09"),
        size_mb=16,
        description=("DE421: small modern-era kernel, fast download. "
                     "MODERN-ERA control test only; cannot validate "
                     "Hellenistic anchors."),
    ),
    "de422": KernelSpec(
        name="de422",
        filename="de422.bsp",
        coverage_jd=(625296.5, 2816848.5),
        coverage_iso=("-3001-02-23", "+3000-05-06"),
        size_mb=660,
        description=("DE422: long-coverage kernel covering the entire "
                     "Antikythera era at moderate disk cost.  Recommended "
                     "for low-bandwidth Hellenistic validation."),
    ),
    "de441": KernelSpec(
        name="de441",
        filename="de441.bsp",
        coverage_jd=(-3027215.5, 8000016.5),
        coverage_iso=("-13201-04-21", "+17191-03-15"),
        size_mb=3000,
        description=("DE441: JPL current best (Park et al. 2021, "
                     "AJ 161:105).  Default for production validation."),
    ),
    "de441_part1": KernelSpec(
        name="de441_part1",
        filename="de441_part-1.bsp",
        coverage_jd=(-3027215.5, 2287184.5),
        coverage_iso=("-13201-04-21", "+1550-01-01"),
        size_mb=1500,
        description=("DE441 Part 1: pre-1550-CE half of DE441.  Sufficient "
                     "for Antikythera-era validation; saves ~1.5 GB vs "
                     "the full DE441."),
    ),
    "de441_part2": KernelSpec(
        name="de441_part2",
        filename="de441_part-2.bsp",
        coverage_jd=(2287184.5, 8000016.5),
        coverage_iso=("+1550-01-01", "+17191-03-15"),
        size_mb=1500,
        description=("DE441 Part 2: post-1550-CE half of DE441.  Not "
                     "useful for Antikythera-era anchors; included for "
                     "completeness."),
    ),
    "de440": KernelSpec(
        name="de440",
        filename="de440.bsp",
        coverage_jd=(2287184.5, 2688976.5),
        coverage_iso=("+1550-01-01", "+2650-01-01"),
        size_mb=114,
        description="JPL DE440: Modern high-precision standard (1550-2650).",
    ),
    "de442": KernelSpec(
        name="de442",
        filename="de442.bsp",
        coverage_jd=(2287184.5, 2688976.5),
        coverage_iso=("+1550-01-01", "+2650-01-01"),
        size_mb=114,
        description="JPL DE442: High-precision standard (Released 2025).",
    ),
}


def available_kernels() -> List[str]:
    """List kernel names this module knows about."""
    return sorted(KERNEL_CATALOG.keys())


# ---------------------------------------------------------------------------
# Bundle: what a caller actually gets
# ---------------------------------------------------------------------------

@dataclass
class EphemerisBundle:
    """Skyfield ephemeris handles bundled by body name.

    The fields are typed as ``Any`` so this module imports without
    skyfield installed.  Callers that touch the fields require skyfield
    to be present at runtime; if it is not, ``load_ephemeris`` returns
    ``None`` upstream.

    v0.5.2: ``extra_ephs`` is a list of supplementary skyfield SPK
    objects loaded alongside the main planetary kernel — typically
    moon-satellite kernels (mar099s, jup365, sat441) so the
    de441_error_spectrum sweep can validate the new Galilean / Saturnian
    moons against ephemeris truth. The ``lookup`` method searches the
    main ``eph`` first, then each ``extra_ephs`` in order.
    """

    kernel_name: str
    eph: Any
    ts: Any
    earth: Any
    sun: Any
    moon: Any
    mars: Any
    venus: Any
    mercury: Any
    jupiter: Any
    saturn: Any
    extra_ephs: List[Any] = None  # type: ignore[assignment]
    extra_kernel_names: List[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # Normalise mutable defaults so callers that didn't pass
        # the lists still get sane attributes.
        if self.extra_ephs is None:
            object.__setattr__(self, "extra_ephs", [])
        if self.extra_kernel_names is None:
            object.__setattr__(self, "extra_kernel_names", [])

    def lookup(self, target_key: str) -> Any:
        """Return the skyfield target for `target_key`, searching the
        main `eph` first, then each `extra_ephs` in order.

        Raises `KeyError` if no loaded kernel has a target with that
        name. Used by `_truth_longitude` in `de441_error_spectrum.py`
        to look up moon barycenters that DE441 doesn't carry but
        `mar099s` / `jup365` / `sat441` do.
        """
        for src in [self.eph] + (self.extra_ephs or []):
            try:
                return src[target_key]
            except (KeyError, ValueError):
                continue
        raise KeyError(
            f"target {target_key!r} not in main kernel "
            f"{self.kernel_name!r} or any of "
            f"{self.extra_kernel_names!r}"
        )


# ---------------------------------------------------------------------------
# Lazy loader
# ---------------------------------------------------------------------------

_BUNDLE_CACHE: Dict[Tuple[str, Optional[str]], Optional[EphemerisBundle]] = {}


def _resolve_kernel_name(kernel: str) -> KernelSpec:
    if kernel not in KERNEL_CATALOG:
        names = ", ".join(available_kernels())
        raise ValueError(
            f"Unknown kernel {kernel!r}.  Available: {names}."
        )
    return KERNEL_CATALOG[kernel]


def load_ephemeris(
    kernel: str = "de441",
    kernel_file: Optional[str] = None,
    data_dir: Optional[str] = None,
    auxiliary_kernels: Optional[List[str]] = None,
) -> Optional[EphemerisBundle]:
    """Load (or fetch from cache) a JPL DE-series kernel via skyfield.

    Parameters
    ----------
    kernel : str
        Catalog name (see ``available_kernels()``).  Default ``'de441'``.
    kernel_file : Optional[str]
        Direct filesystem path to a pre-downloaded ``.bsp`` file.  When
        given, the catalog ``kernel`` is honoured only for naming /
        metadata; the bytes are loaded from ``kernel_file``.
    data_dir : Optional[str]
        Skyfield Loader directory.  Default ``./skyfield_data`` relative
        to the project root (matches the existing scaffold's gitignore).

    Returns
    -------
    Optional[EphemerisBundle]
        ``None`` on any failure (skyfield missing, file absent, bad
        format).  Never raises — callers downstream emit ``UNDETERMINED``.
    """
    aux_tuple = tuple(auxiliary_kernels or ())
    cache_key = (kernel, kernel_file, aux_tuple)  # type: ignore[assignment]
    if cache_key in _BUNDLE_CACHE:
        return _BUNDLE_CACHE[cache_key]

    spec = _resolve_kernel_name(kernel)
    try:
        from skyfield.api import Loader
    except ImportError:
        _BUNDLE_CACHE[cache_key] = None
        return None

    try:
        if data_dir is None:
            data_dir = "./skyfield_data"
        loader = Loader(data_dir, verbose=False)
        ts = loader.timescale()
        if kernel_file is not None:
            eph = (loader(kernel_file) if str(kernel_file).endswith(".bsp")
                   else loader(kernel_file))
        else:
            eph = loader(spec.filename)
        def _get(key_list):
            for k in key_list:
                try: return eph[k]
                except KeyError: continue
            return None

        # Load auxiliary moon kernels alongside the main planetary
        # kernel. Each is a separate skyfield SpiceKernel; the
        # EphemerisBundle.lookup() method searches them in order.
        # Files are taken to be filenames (in data_dir) — same
        # convention as the main kernel's `spec.filename`.
        extra_ephs: List[Any] = []
        extra_kernel_names: List[str] = []
        for aux_name in (auxiliary_kernels or []):
            try:
                if aux_name.endswith(".bsp"):
                    aux_eph = loader(aux_name)
                else:
                    aux_eph = loader(aux_name + ".bsp")
                extra_ephs.append(aux_eph)
                extra_kernel_names.append(aux_name)
            except Exception as exc:
                # Don't fail the whole load on a single missing aux
                # kernel — log and continue. The bundle will still
                # work for whatever bodies the main kernel + remaining
                # aux kernels cover.
                print(f"DEBUG: auxiliary kernel {aux_name!r} failed to "
                      f"load: {exc}; continuing without it.")

        bundle = EphemerisBundle(
            kernel_name=kernel,
            eph=eph,
            ts=ts,
            earth=_get(["earth", "EARTH", 399, 3]),
            sun=_get(["sun", "SUN", 10]),
            moon=_get(["moon", "MOON", 301]),
            mars=_get(["mars", "MARS", 499, 4]),
            venus=_get(["venus", "VENUS", 299, 2]),
            mercury=_get(["mercury", "MERCURY", 199, 1]),
            jupiter=_get(["jupiter barycenter", "JUPITER BARYCENTER", 5]),
            saturn=_get(["saturn barycenter", "SATURN BARYCENTER", 6]),
            extra_ephs=extra_ephs,
            extra_kernel_names=extra_kernel_names,
        )
        _BUNDLE_CACHE[cache_key] = bundle
        return bundle
    except Exception as exc:
        print(f"DEBUG: load_ephemeris failed: {exc}")
        _BUNDLE_CACHE[cache_key] = None
        return None


def is_available(kernel: str = "de441",
                 kernel_file: Optional[str] = None) -> bool:
    """True iff ``load_ephemeris(kernel, kernel_file)`` succeeds."""
    return load_ephemeris(kernel, kernel_file) is not None


def covers_jd(kernel: str, jd: float) -> bool:
    """True iff ``kernel``'s coverage band includes Julian Day ``jd``."""
    spec = _resolve_kernel_name(kernel)
    return spec.coverage_jd[0] <= jd <= spec.coverage_jd[1]


def kernel_for_jd_range(jd_lo: float, jd_hi: float) -> Optional[str]:
    """Smallest kernel that fully covers [jd_lo, jd_hi], or None."""
    candidates = sorted(KERNEL_CATALOG.values(), key=lambda s: s.size_mb)
    for spec in candidates:
        if spec.coverage_jd[0] <= jd_lo and jd_hi <= spec.coverage_jd[1]:
            return spec.name
    return None


# ---------------------------------------------------------------------------
# Explicit downloader (opt-in only)
# ---------------------------------------------------------------------------

def download_kernel(
    kernel: str,
    data_dir: Optional[str] = None,
    yes: bool = False,
) -> Optional[Path]:
    """Fetch a kernel via skyfield's Loader; prompts y/N with size first.

    Returns the local path on success, or ``None`` if the user declined,
    skyfield is missing, or the fetch failed.  Never auto-confirms unless
    ``yes=True``.
    """
    spec = _resolve_kernel_name(kernel)
    print(
        f"About to fetch {spec.filename} (~{spec.size_mb} MB).  "
        f"Coverage: {spec.coverage_iso[0]} to {spec.coverage_iso[1]}."
    )
    if not yes:
        try:
            answer = input("Proceed? [y/N] ").strip().lower()
        except EOFError:
            answer = ""
        if answer not in ("y", "yes"):
            print("Cancelled.")
            return None

    try:
        from skyfield.api import Loader
    except ImportError:
        print("ERROR: skyfield not installed.  pip install skyfield first.")
        return None

    if data_dir is None:
        data_dir = "./skyfield_data"
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    loader = Loader(data_dir, verbose=True)
    try:
        loader(spec.filename)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        return None
    return Path(data_dir) / spec.filename


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # List known kernels and their coverage:
  python -m research.ephemeris_loader --list-kernels

  # Probe whether a kernel is locally loadable:
  python -m research.ephemeris_loader --probe de421

  # Pre-fetch the DE441 Hellenistic-era half (1.5 GB, prompts y/N):
  python -m research.ephemeris_loader --download de441_part1

  # Suggest the smallest kernel that covers a JD range:
  python -m research.ephemeris_loader --kernel-for-range 1637860 1789535

Notes
-----
- This module never auto-downloads.  --download is opt-in.
- Failure modes return None / non-zero exit; never raise.
- Anchored to the Hellenistic-eclipse anchor band -382 .. +125 (~JD
  1637860 .. 1789535), which sits inside DE422 and DE441_part1.
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m research.ephemeris_loader",
        description=(
            "Lazy JPL DE-kernel loader for skyfield.  Module-level "
            "imports never fail even if skyfield is unavailable; the "
            "CLI degrades gracefully with non-zero exit."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list-kernels", action="store_true",
        help="Print the kernel catalog and exit.",
    )
    parser.add_argument(
        "--probe", metavar="KERNEL", default=None,
        help="Try loading KERNEL and report success/failure.",
    )
    parser.add_argument(
        "--download", metavar="KERNEL", default=None,
        help="Fetch KERNEL into ./skyfield_data; prompts y/N with size.",
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="Skip the y/N prompt for --download (use with care).",
    )
    parser.add_argument(
        "--data-dir", default=None,
        help="Skyfield Loader directory (default: ./skyfield_data).",
    )
    parser.add_argument(
        "--kernel-for-range", nargs=2, type=float,
        metavar=("JD_LO", "JD_HI"), default=None,
        help="Suggest the smallest kernel covering [JD_LO, JD_HI].",
    )
    parser.add_argument(
        "--ephemeris-path", dest="ephemeris_bsp", default=None,
        help="Direct path to a .bsp file (overrides kernel name lookup).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)

    if args.list_kernels:
        print(f"{'kernel':<14} {'size MB':>9}  {'coverage':<28}  description")
        print("-" * 92)
        for spec in sorted(KERNEL_CATALOG.values(), key=lambda s: s.size_mb):
            cov = f"{spec.coverage_iso[0]} .. {spec.coverage_iso[1]}"
            desc = spec.description.split(".  ")[0]
            print(f"{spec.name:<14} {spec.size_mb:>9d}  {cov:<28}  {desc}")
        return 0

    if args.kernel_for_range is not None:
        lo, hi = args.kernel_for_range
        kernel = kernel_for_jd_range(lo, hi)
        if kernel is None:
            print(f"No kernel covers [{lo}, {hi}].")
            return 1
        print(kernel)
        return 0

    if args.probe is not None:
        ok = is_available(args.probe, kernel_file=args.ephemeris_bsp)
        print(f"{args.probe}: {'AVAILABLE' if ok else 'unavailable'}")
        return 0 if ok else 1

    if args.download is not None:
        downloaded = download_kernel(args.download, data_dir=args.data_dir,
                                     yes=args.yes)
        return 0 if downloaded is not None else 1

    # Default: print quick status
    print("ephemeris_loader -- pass --help for full options.")
    print(f"Known kernels: {', '.join(available_kernels())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
