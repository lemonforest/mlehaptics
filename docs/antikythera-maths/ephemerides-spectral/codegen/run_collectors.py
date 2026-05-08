"""T1 collector runner — invoked by the v0.25.0b CI workflow.

For one or all registered attested sources, runs the descriptor's
declared adapter against the live upstream archive and writes the
resulting MPRRecords to ``research/attested/<source>/<table>.ndjson``.

This script is the **only** code path in the project that performs
network I/O at codegen time. ``regenerate.py`` does not import this
module — running collectors is an explicit, opt-in CI step (the
``ephemerides-spectral-collect.yml`` workflow). Local developers can
invoke it manually:

    python codegen/run_collectors.py --source earthref_sc

After a run, the workflow opens an auto-PR with the diff against
the previously-committed NDJSON. Maintainers review citation
provenance before merging.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import List

from _paths import ATTESTED_SRC, ensure_research_importable

ensure_research_importable()

from research.attested_adapters._base import run as adapter_run  # noqa: E402
from research.attested_collector_descriptor import (  # noqa: E402
    discover_descriptors,
)
from research.attested_collector_format import (  # noqa: E402
    write_ndjson,
)


def _table_path_from_descriptor(descriptor) -> Path:
    """Resolve the on-disk NDJSON path for a descriptor (mirrors the
    catalog wrapper's _ndjson_path)."""
    schema_id = str(descriptor.schema["data_schema_id"])
    parts = schema_id.split(".")
    table = parts[1] if len(parts) >= 3 else parts[-1]
    return descriptor.path.parent / f"{table}.ndjson"


def collect(source_key: str | None) -> List[Path]:
    """Run collectors for one source (or all). Returns the list of
    NDJSON paths written.
    """
    descriptors = discover_descriptors(ATTESTED_SRC)
    if not descriptors:
        print("no attested descriptors found; nothing to collect", flush=True)
        return []

    if source_key and source_key != "all":
        if source_key not in descriptors:
            raise SystemExit(
                f"unknown source_key {source_key!r}; "
                f"registered: {sorted(descriptors.keys())}"
            )
        descriptors = {source_key: descriptors[source_key]}

    package_version = _read_package_version()
    parser_version = f"ephemerides-spectral {package_version}"
    written: List[Path] = []

    for key, descriptor in sorted(descriptors.items()):
        print(f"collecting {key} ...", flush=True)
        retrieved_at = dt.datetime.now(dt.timezone.utc)
        records = list(adapter_run(
            descriptor,
            parser_version=parser_version,
            retrieved_at=retrieved_at,
        ))
        ndjson_path = _table_path_from_descriptor(descriptor)
        n = write_ndjson(ndjson_path, records)
        print(f"  wrote {n} rows -> {ndjson_path}", flush=True)
        written.append(ndjson_path)

    return written


def _read_package_version() -> str:
    """Read [project].version from pyproject.toml so the parser_version
    field in attestation blocks tracks the current build."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover
        import tomli as tomllib  # type: ignore
    pyproject = Path(__file__).resolve().parents[1] / "python" / "pyproject.toml"
    return str(tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run T1 collectors against live upstream archives "
            "(network I/O). Writes per-source NDJSON to "
            "research/attested/<source>/<table>.ndjson."
        )
    )
    parser.add_argument(
        "--source",
        default="all",
        help="source_key to collect (or 'all' for every registered source)",
    )
    args = parser.parse_args()
    written = collect(args.source)
    print(f"done; {len(written)} NDJSON file(s) written.", flush=True)


if __name__ == "__main__":
    main()
