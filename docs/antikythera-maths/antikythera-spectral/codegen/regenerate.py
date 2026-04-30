"""Orchestrator — run all codegen emitters, write provenance manifest.

Usage::

    python codegen/regenerate.py            # run all emitters
    python codegen/regenerate.py --quiet    # suppress per-emitter output
    python codegen/regenerate.py --skip-research   # data only, no _research/
    python codegen/regenerate.py --skip-data       # _research/ only, no _data/

Side effects:

- runs every ``emit_*.py`` script in this directory,
- writes ``_data/manifest.json`` carrying:
    - the package version (parsed from ``../python/pyproject.toml``),
    - the source-commit hash (from ``git rev-parse HEAD``; falls back
      to ``"unknown"`` if git is unavailable),
    - per-file SHA-256 sums of every output, so a downstream consumer
      can verify the wheel's data hasn't been tampered with,
- prints a one-line summary per emitter,
- exits non-zero if any emitter fails.

The orchestrator is deterministic: re-running it on the same source
state must produce byte-identical output. ``test_data_freshness.py``
asserts this by re-running the orchestrator into a temp directory and
comparing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Dict

from _paths import DATA_DIR

import emit_anchors
import emit_basis_vectors
import emit_cycles
import emit_fragment_inventory
import emit_gears
import emit_periods
import emit_research_modules


def _git_commit() -> str:
    """Return the current HEAD commit hash, or ``'unknown'`` on failure.

    Wrapped in try/except because:

    - some CI runners do shallow checkouts where ``git`` works but
      certain rev-parses fail,
    - someone might run codegen from a release tarball with no .git.
    """
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        return out or "unknown"
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return "unknown"


def _package_version() -> str:
    """Read the package version from pyproject.toml.

    Single source of truth for ``manifest.version``.
    """
    pyproject = Path(__file__).resolve().parents[1] / "python" / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    return str(data["project"]["version"])


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


_EPILOG = """\
What this writes
----------------

    _data/cycles.json                 from research.astronomical_cycles
    _data/gears.json                  from research.gear_database
    _data/anchors.json                from research.hellenistic_eclipses
    _data/periods.json                from research.historical_periods
    _data/fragments.json              from research.gear_database (grouped by fragment)
    _data/basis_vectors_d940.npz      deterministic HDC channel basis (D=940)
    _data/basis_vectors_d13440.npz    deterministic HDC channel basis (D=13440)
    _data/manifest.json               version + source-commit + per-file SHA-256
    _research/*.py                    23 curated research modules, byte-identical copy

Determinism
-----------

Re-running with the same source state produces byte-identical output.
``test_data_freshness.py`` asserts this; CI runs it on every PR.

ADR cross-reference
-------------------

- ADR 0004: frozen data as JSON / NPZ, never pickle
- ADR 0005: codegen yes / C no in v0.1.0
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codegen/regenerate.py",
        description=(
            "Regenerate _data/*.json + _data/basis_*.npz + _research/*.py "
            "from research/*.py (the SSOT). Writes _data/manifest.json with "
            "package version + git commit + per-file SHA-256 sums."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress per-emitter output (only print the final summary)",
    )
    parser.add_argument(
        "--skip-research", action="store_true",
        help="Skip the _research/ module copy step (regenerate _data/ only)",
    )
    parser.add_argument(
        "--skip-data", action="store_true",
        help="Skip the _data/ JSON+NPZ emit (regenerate _research/ only)",
    )
    return parser


def main(argv=None) -> int:
    args = _make_parser().parse_args(argv)
    quiet = args.quiet

    def _say(msg: str) -> None:
        if not quiet:
            print(msg)

    _say("--- antikythera-spectral codegen ---")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    written: Dict[str, Path] = {}

    # Manifest keys are paths relative to the package root
    # (antikythera_spectral/), so callers can resolve them as
    # `PKG_ROOT / key` regardless of subdir.
    if not args.skip_data:
        _say("emitting cycles ...")
        written["_data/cycles.json"] = emit_cycles.emit()

        _say("emitting gears ...")
        written["_data/gears.json"] = emit_gears.emit()

        _say("emitting anchors ...")
        written["_data/anchors.json"] = emit_anchors.emit()

        _say("emitting periods ...")
        written["_data/periods.json"] = emit_periods.emit()

        _say("emitting fragments ...")
        written["_data/fragments.json"] = emit_fragment_inventory.emit()

        _say("emitting basis vectors ...")
        basis_paths = emit_basis_vectors.emit()
        for D, p in basis_paths.items():
            # Manifest keys use paths relative to the package root so the
            # test can resolve them uniformly with PKG_ROOT / key.
            written[f"_data/{p.name}"] = p

    if not args.skip_research:
        _say("copying research modules into _research/ ...")
        research_paths = emit_research_modules.emit()
        for p in research_paths:
            written[f"_research/{p.name}"] = p

    if args.skip_research or args.skip_data:
        # Partial regeneration: the manifest covers both halves, so
        # writing it now would lose SHAs for the un-regenerated portion.
        # Bail out with a warning so the user knows to run the full
        # cycle before committing.
        print(
            f"--- partial run (skip_data={args.skip_data} "
            f"skip_research={args.skip_research}); manifest NOT updated ---"
        )
        print(f"--- {len(written)} files written ---")
        print(
            "warning: manifest.json is now stale; "
            "run `python regenerate.py` (full) before committing.",
            file=sys.stderr,
        )
        return 0

    _say("writing manifest ...")
    manifest = {
        "schema_version": 2,
        "package": "antikythera-spectral",
        "version": _package_version(),
        "source_commit": _git_commit(),
        "files": {
            name: {
                "size_bytes": p.stat().st_size,
                "sha256": _sha256(p),
            }
            for name, p in sorted(written.items())
        },
    }
    manifest_path = DATA_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"--- done; {len(written)} files + manifest in {DATA_DIR} ---")
    print(f"package version: {manifest['version']}")
    print(f"source commit:   {manifest['source_commit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
