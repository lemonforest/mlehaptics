"""Mathematical Provenance Record (MPR) v1 — canonical NDJSON format
for attested ground-proof rows from external archives.

The format is the on-disk crystallisation of The Mathematical
Provenance Method (notebook §0.0). Every row carries a mandatory
attestation block — the same provenance discipline the v0.24.x
hand-coded `_research/<topic>_data.py` modules encoded inline,
formalised so it survives a thousand sources.

Format
------
Each row is one JSON line (NDJSON). A row has five top-level keys:

* ``mpr_version`` — schema version. v0.25.0 ships ``"1.0"``.
  Consumers MUST refuse to load an unrecognised version.
* ``data`` — domain payload. Per-source schema; resolved against
  ``data_schema_id``.
* ``data_schema_id`` — opaque identifier resolved at codegen-time
  to a JSON Schema under ``research/attested/<source>/*.schema.json``.
* ``attestation`` — mandatory provenance block (see §18.2). Every
  field of this block is required and non-empty; a row missing any
  field is invalid.
* ``rendering`` — self-describing verbiage (human-readable name,
  citation, purpose) sourced from the descriptor's ``[rendering]``
  block. Lets the program take its language from the attestation
  data — new sources require no code change to render their
  provenance text.

Reproducibility
---------------
NDJSON is committed verbatim under ``research/attested/<source>/``;
the codegen mirror copies these files **byte-exactly** (no LF
normalisation) into ``_research/attested/<source>/``. The
``response_sha256`` field in each attestation block is computed at
*fetch* time over the upstream response bytes; we trust the
committed bytes at runtime and never recompute. T1 (CI re-bake)
regenerates against live sources; the auto-PR commits the new
NDJSON; the maintainer reviews before merging.

Schema validation runs at codegen-time (collector run), not at
runtime read. Per the Mathematical Provenance Method discipline,
ground-proof rows in the wheel are trusted; runtime is read-only.

References
----------
* Notebook §18 — full normative format spec.
* `srmech.amsc.descriptor` — sister module for the source descriptor
  TOML schema.
* `srmech.amsc.adapters` — shared adapter core that produces
  MPRRecords from descriptors + upstream archives.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────
# Format-level constants
# ──────────────────────────────────────────────────────────────────────

MPR_SCHEMA_VERSION: str = "1.0"
"""Current MPR schema version. v0.25.0 ships v1.0; future bumps go
to v1.1 / v2 with explicit migration story. Consumers MUST refuse
unrecognised versions."""

MANDATORY_ATTESTATION_FIELDS: Tuple[str, ...] = (
    "source_doi",
    "source_url",
    "license",
    "retrieved_at",
    "response_sha256",
    "parser_version",
    "parser_rule_hash",
    "collector_descriptor_path",
    "collector_descriptor_hash",
)
"""Every MPR row's `attestation` block MUST carry all of these
fields, non-empty. Per §18.2 a row missing any field is *not a
valid MPR* — the format does not allow attestation to be partial."""

MANDATORY_RENDERING_FIELDS: Tuple[str, ...] = (
    "human_readable_name",
    "cite_as",
    "purpose",
)
"""Self-describing rendering verbiage required for every row. The
descriptor's `[rendering]` block produces these via template
substitution at collector run-time."""


# ──────────────────────────────────────────────────────────────────────
# In-memory representation
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MPRRecord:
    """A single ground-proof row in the canonical MPR format.

    Frozen + hashable so records can be used as dict keys and
    deduplicated. Attestation + rendering are dicts (not nested
    dataclasses) to round-trip cleanly through JSON without bespoke
    serialisers.
    """

    mpr_version: str
    data: Dict[str, Any]
    data_schema_id: str
    attestation: Dict[str, str]
    rendering: Dict[str, str]

    def to_json_line(self) -> str:
        """Serialise as one NDJSON line (no trailing newline).

        Uses ``sort_keys=True`` so the same record always serialises
        to the same bytes — preserves byte-level reproducibility.
        """
        payload: Dict[str, Any] = {
            "mpr_version": self.mpr_version,
            "data": self.data,
            "data_schema_id": self.data_schema_id,
            "attestation": dict(self.attestation),
            "rendering": dict(self.rendering),
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> "MPRRecord":
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError("MPR line is not a JSON object")
        return cls(
            mpr_version=str(payload.get("mpr_version", "")),
            data=dict(payload.get("data", {})),
            data_schema_id=str(payload.get("data_schema_id", "")),
            attestation=dict(payload.get("attestation", {})),
            rendering=dict(payload.get("rendering", {})),
        )


# ──────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────


class MPRValidationError(ValueError):
    """Raised when an MPR record fails schema validation."""


def validate_mpr_record(
    record: MPRRecord,
    *,
    data_schemas: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    """Validate an MPR record against the v1 spec.

    Parameters
    ----------
    record
        The MPRRecord to validate.
    data_schemas
        Optional mapping ``data_schema_id -> JSON Schema``. When
        provided, the record's ``data`` block is validated against
        the matching schema (uses ``jsonschema`` if available; logs
        a warning if not). When None, only the MPR-level structure
        is checked.

    Raises
    ------
    MPRValidationError
        If any required structure is missing or malformed.
    """
    if record.mpr_version != MPR_SCHEMA_VERSION:
        raise MPRValidationError(
            f"unrecognised mpr_version {record.mpr_version!r}; "
            f"this build supports {MPR_SCHEMA_VERSION!r} only"
        )

    if not record.data_schema_id:
        raise MPRValidationError("data_schema_id must be non-empty")

    if not isinstance(record.data, dict):
        raise MPRValidationError("data must be a JSON object")

    for field_name in MANDATORY_ATTESTATION_FIELDS:
        value = record.attestation.get(field_name)
        if not value or not isinstance(value, str):
            raise MPRValidationError(
                f"attestation.{field_name} is required and must be "
                f"a non-empty string (got {value!r})"
            )

    for field_name in MANDATORY_RENDERING_FIELDS:
        value = record.rendering.get(field_name)
        if not value or not isinstance(value, str):
            raise MPRValidationError(
                f"rendering.{field_name} is required and must be "
                f"a non-empty string (got {value!r})"
            )

    # Per-source data-block schema validation (optional; used at
    # codegen-time, not at runtime).
    if data_schemas is not None:
        schema = data_schemas.get(record.data_schema_id)
        if schema is None:
            raise MPRValidationError(
                f"unknown data_schema_id {record.data_schema_id!r}"
            )
        _validate_data_against_schema(record.data, schema)


def _validate_data_against_schema(
    data: Dict[str, Any], schema: Dict[str, Any]
) -> None:
    """Validate a data block against its JSON Schema.

    Uses ``jsonschema`` if importable. When jsonschema is not
    available we fall back to a minimal required-fields check.
    The full library is in the ``collector`` optional-dependency
    extra; runtime read paths don't need it.
    """
    try:
        import jsonschema  # type: ignore
    except ImportError:
        # Minimal fallback: enforce `required` only.
        required: List[str] = list(schema.get("required", []))
        for key in required:
            if key not in data:
                raise MPRValidationError(
                    f"data block missing required field {key!r}"
                )
        return

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        raise MPRValidationError(
            f"data block fails schema: {exc.message}"
        ) from exc


# ──────────────────────────────────────────────────────────────────────
# NDJSON I/O
# ──────────────────────────────────────────────────────────────────────


def read_ndjson(path: Path) -> Iterator[MPRRecord]:
    """Stream MPRRecords line-by-line from an NDJSON file.

    Skips empty lines (NDJSON allows them by convention) and lines
    beginning with ``#`` (project-convention comment headers — see the
    leading ``# Each line below is one MPR row data block (NDJSON).``
    block at the top of every ``research/attested/<source>/row.ndjson``
    file in the spectral-research portfolio). The skip discipline
    matches the comment-aware reader used by
    :func:`catalog.get_attested_dataset`; without it, callers like
    :func:`catalog.attestation_audit` choke on the comment headers
    that the catalog-discovery path quietly tolerates.

    Raises ``MPRValidationError`` on a malformed (non-comment,
    non-empty) line, with the line number for diagnostics.

    Task #201 Phase B4 — when the native library is available, the
    file-IO + line tokenisation runs in C (``srmech_ndjson_iter``)
    and JSON parsing stays in Python. Byte-exact output equivalence
    with the pure-Python path is pinned by
    ``tests/test_native_ndjson.py``.
    """
    from . import _native
    if _native.HAS_NATIVE:
        # Native path: C reads + tokenises, Python parses JSON.
        try:
            lines = _native.ndjson_lines_c(str(path))
        except _native.NativeNDJsonError as exc:
            # Re-raise as a plain OSError so callers that previously
            # caught Python's FileNotFoundError / IsADirectoryError
            # see consistent behaviour. The .__cause__ chain keeps
            # the underlying SRMECH_ERR_* status visible.
            raise OSError(str(exc)) from exc
        for lineno, line_bytes in lines:
            text = line_bytes.decode("utf-8").lstrip()
            if not text or text.startswith("#"):
                continue
            try:
                yield MPRRecord.from_json_line(text)
            except (json.JSONDecodeError, ValueError) as exc:
                raise MPRValidationError(
                    f"{path}:{lineno}: malformed MPR line: {exc}"
                ) from exc
        return

    # Pure-Python streaming path.
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                yield MPRRecord.from_json_line(line)
            except (json.JSONDecodeError, ValueError) as exc:
                raise MPRValidationError(
                    f"{path}:{lineno}: malformed MPR line: {exc}"
                ) from exc


def write_ndjson(
    path: Path,
    records: Iterable[MPRRecord],
    *,
    sort_key: Optional[str] = None,
) -> int:
    """Write MPRRecords to an NDJSON file with deterministic ordering.

    Parameters
    ----------
    path
        Output file path. Created if it does not exist; truncated
        if it does.
    records
        Iterable of MPRRecord. Materialised in memory so we can
        sort.
    sort_key
        Optional dotted-path into each record's ``data`` block to
        sort by (e.g. ``"name"``). When None, records are written
        in input order.

    Returns
    -------
    int
        Number of records written.
    """
    materialised: List[MPRRecord] = list(records)
    if sort_key is not None:
        materialised.sort(key=lambda r: _resolve_sort_key(r, sort_key))

    path.parent.mkdir(parents=True, exist_ok=True)
    # NDJSON is byte-stable — write LF line endings explicitly so
    # Windows checkouts produce identical SHA-256 to Linux.
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in materialised:
            f.write(record.to_json_line())
            f.write("\n")
    return len(materialised)


def _resolve_sort_key(record: MPRRecord, dotted: str) -> Any:
    """Resolve a dotted path inside a record (data.field or
    attestation.field). Returns ``""`` if the path is missing so
    sort-by-key never crashes."""
    parts = dotted.split(".")
    head, tail = parts[0], parts[1:]
    if head == "data":
        cursor: Any = record.data
    elif head == "attestation":
        cursor = record.attestation
    elif head == "rendering":
        cursor = record.rendering
    else:
        cursor = record.data
        tail = parts
    for key in tail:
        if not isinstance(cursor, dict):
            return ""
        cursor = cursor.get(key, "")
    return cursor


# ──────────────────────────────────────────────────────────────────────
# Hash helpers (used by adapters to compute response_sha256 +
# parser_rule_hash + collector_descriptor_hash)
# ──────────────────────────────────────────────────────────────────────


def sha256_bytes(data: bytes) -> str:
    """SHA-256 over raw input bytes; returns the 64-char lowercase hex
    digest as a ``str`` (NOT the raw 32-byte digest). The ``_bytes`` in
    the name names the INPUT type (the raw bytes hashed), not the return
    type — this is the Python parity of C ``srmech_sha256_hex`` and of
    ``hashlib.sha256(data).hexdigest()``. Used by every adapter's
    ``attest()`` step to fingerprint upstream response bytes.

    Task #201 Phase B3 — dispatches to the native C implementation
    (``srmech.amsc._native.sha256_hex_c``) when the shared library
    is available, otherwise uses stdlib ``hashlib``. The two paths
    are byte-identical (pinned by ``tests/test_native_sha256.py``).

    Returns:
        A ``str`` of exactly 64 lowercase hex characters (the Class A
        content-address), NOT raw ``bytes``. A caller wanting the digest
        as an integer should parse the hex string with
        ``int(h, 16)`` (full 256-bit value) or
        ``int(h[:8], 16)`` (a truncated 32-bit tag), NOT
        ``int.from_bytes(...)`` — the return is already hex text, so there
        are no raw digest bytes to feed ``int.from_bytes``.
    """
    # Lazy import to keep srmech.amsc.format importable on platforms
    # where _native fails to load — the module always exposes a
    # HAS_NATIVE flag, even when the .so is absent.
    from . import _native
    if _native.HAS_NATIVE:
        return _native.sha256_hex_c(data)
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_batch(datas: "list[bytes]") -> "list[str]":
    """SHA-256 over MANY messages at once; returns one 64-char lowercase
    hex digest per input (a ``list[str]``, parallel to ``datas``). Each
    digest is byte-identical to ``sha256_bytes(d)`` /
    ``hashlib.sha256(d).hexdigest()`` — this is purely a THROUGHPUT surface
    for the bulk-attestation case (fingerprinting a whole catalog of
    upstream response bytes at once), not a new content-address shape.

    v0.7.0rc10 (F292 graft #1) — dispatches to the native **N-way SIMD**
    peer (``srmech.amsc._native.sha256_batch_c``; AVX2 8-way / SSE2 4-way
    on x86, scalar elsewhere) when the shared library carries the rc10
    symbol, otherwise a stdlib ``hashlib`` loop. The two paths are
    byte-identical (pinned by ``tests/test_sha256_batch.py``).

    Args:
        datas: the messages to hash (each a ``bytes``-like object).

    Returns:
        ``list[str]`` of 64-char lowercase hex digests, one per input.
    """
    from . import _native
    if (_native.HAS_NATIVE and getattr(_native, "LIB", None) is not None
            and hasattr(_native.LIB, "srmech_sha256_batch")):
        return _native.sha256_batch_c(list(datas))
    return [hashlib.sha256(bytes(d)).hexdigest() for d in datas]


__all__ = [
    "MPR_SCHEMA_VERSION",
    "MANDATORY_ATTESTATION_FIELDS",
    "MANDATORY_RENDERING_FIELDS",
    "MPRRecord",
    "MPRValidationError",
    "validate_mpr_record",
    "read_ndjson",
    "write_ndjson",
    "sha256_bytes",
    "sha256_batch",
]
