"""Mirror research/attested/ → _research/attested/ byte-exactly.

Unlike emit_research_modules (which copies .py files with LF
normalisation), this emitter is **byte-exact**: every NDJSON,
JSON Schema, TOML descriptor, and __init__.py is copied verbatim.

Why byte-exact: the per-row attestation block in MPR NDJSON
records carries ``response_sha256`` computed at fetch time over
the upstream response bytes. If we LF-normalised the committed
NDJSON on Windows checkouts, the SHA-256 in the manifest would
drift from the SHA-256 in the attestation block. Byte-exact
copy preserves the canonical bytes the attestation documents.

References
----------
* Notebook §18 — Mathematical Provenance Record format.
* `_paths.ATTESTED_SRC` / `_paths.ATTESTED_DST` — directory roots.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from _paths import ATTESTED_DST, ATTESTED_SRC


def emit() -> List[Path]:
    """Byte-exact recursive mirror of research/attested/ tree.

    Returns the list of written destination paths so the manifest
    can include their SHA-256 sums.
    """
    if ATTESTED_DST.exists():
        shutil.rmtree(ATTESTED_DST)
    ATTESTED_DST.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []
    if not ATTESTED_SRC.exists():
        return written

    for src in sorted(ATTESTED_SRC.rglob("*")):
        if src.is_dir():
            continue
        # Skip transient files that shouldn't ship.
        if src.name.startswith(".") or src.suffix == ".pyc":
            continue
        rel = src.relative_to(ATTESTED_SRC)
        dst = ATTESTED_DST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        # NDJSON files must stay byte-exact: per-row attestation
        # blocks carry response_sha256 computed at fetch time over
        # upstream bytes; LF↔CRLF conversion would silently
        # invalidate every row's attestation. For other text files
        # (TOML descriptors, JSON Schemas, __init__.py) we normalise
        # CRLF→LF so manifest SHA-256s are stable across platforms
        # regardless of the source-of-truth file's checkout EOL.
        raw = src.read_bytes()
        if src.suffix != ".ndjson":
            raw = raw.replace(b"\r\n", b"\n")
        dst.write_bytes(raw)
        written.append(dst)

    return written


if __name__ == "__main__":
    paths = emit()
    print(
        f"copied {len(paths)} attested-collection files into {ATTESTED_DST}"
    )
