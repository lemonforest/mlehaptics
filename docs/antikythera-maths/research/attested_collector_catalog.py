"""Catalog wrapper for the attested collector framework.

Bridge surfaces are universal — they iterate descriptors at module
load and surface row content / attestation / descriptor metadata
without per-source code paths. The whole point of v0.25.0 is that
adding a source is a CONFIG change (descriptor + schema + NDJSON);
no per-source ``*_catalog.py`` module needed.

Surfaces
--------
* :func:`list_attested_sources` — every registered source's
  rendered metadata (name, purpose, license, cite_as, gap_targeting).
* :func:`get_attested_dataset` — paginated row content for one
  source, with full attestation + rendering blocks.
* :func:`get_attested_descriptor` — full parsed descriptor for one
  source (UI / pre-fetch).
* :func:`attestation_audit` — per-row attestation metadata, **no
  data payload** (cheap, paper-appendix-ready).

References
----------
* Notebook §18 — full normative format spec.
* `attested_collector_format` — MPR record format.
* `attested_collector_descriptor` — descriptor TOML schema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .attested_collector_descriptor import (
    Descriptor,
    discover_descriptors,
)
from .attested_collector_format import MPRRecord, read_ndjson


# ──────────────────────────────────────────────────────────────────────
# Discovery — cached at module load
# ──────────────────────────────────────────────────────────────────────


def _attested_root() -> Path:
    """Resolve the attested-tree root for the current install.

    Looks for ``attested/`` next to this module. Works for both the
    research-tree source (``docs/antikythera-maths/research/``) and
    the mirrored package (``ephemerides_spectral/_research/``).
    """
    return Path(__file__).resolve().parent / "attested"


_DESCRIPTORS_CACHE: Optional[Dict[str, Descriptor]] = None


def _descriptors() -> Dict[str, Descriptor]:
    """Lazy-load + cache the descriptor map for this install."""
    global _DESCRIPTORS_CACHE
    if _DESCRIPTORS_CACHE is None:
        _DESCRIPTORS_CACHE = discover_descriptors(_attested_root())
    return _DESCRIPTORS_CACHE


def _ndjson_path(descriptor: Descriptor) -> Path:
    """Resolve the NDJSON file path for a descriptor.

    The descriptor's ``[schema].data_schema_id`` is used as the
    filename stem; e.g. ``earthref_sc.seamount.v1`` →
    ``seamount.ndjson`` (we strip the source-prefix and version
    suffix, taking the middle as the table name).
    """
    schema_id = str(descriptor.schema["data_schema_id"])
    parts = schema_id.split(".")
    # Convention: <source_key>.<table>.<version>
    table = parts[1] if len(parts) >= 3 else parts[-1]
    return descriptor.path.parent / f"{table}.ndjson"


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def list_attested_sources() -> Dict[str, Any]:
    """Enumerate every registered attested source.

    Returns a dict with each source's rendered metadata: human-
    readable name, purpose, license, citation template, adapter,
    and gap-targeting regime labels. Useful for UI source-pickers
    and for the v0.26.x schema-gap-driven trigger.
    """
    descriptors = _descriptors()
    sources: List[Dict[str, Any]] = []
    for key in sorted(descriptors.keys()):
        d = descriptors[key]
        sources.append({
            "key": key,
            "human_readable_name": str(d.source.get("human_readable_name", key)),
            "purpose": str(d.source.get("purpose", "")),
            "license": str(d.source.get("license", "")),
            "homepage": str(d.source.get("homepage", "")),
            "canonical_doi": str(d.source.get("canonical_doi", "")),
            "adapter": d.adapter_name,
            "cite_as_template": str(d.rendering.get("cite_as_template", "")),
            "gap_targeting": dict(d.gap_targeting),
            "data_schema_id": str(d.schema.get("data_schema_id", "")),
        })
    return {
        "ok": True,
        "n_sources": len(sources),
        "sources": sources,
    }


def get_attested_dataset(
    source_key: str,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
) -> Dict[str, Any]:
    """Return paginated row content for a registered source.

    Each row carries its full ``data`` + ``attestation`` +
    ``rendering`` blocks. Use :func:`attestation_audit` for the
    cheap data-block-free variant.

    Returns
    -------
    dict
        ``{ok, source_key, total, offset, limit, next_offset, rows}``
        where ``rows`` is a list-of-dict slice of the source's
        committed NDJSON. ``next_offset`` is ``None`` when the
        slice extends through end-of-file.
    """
    descriptors = _descriptors()
    if source_key not in descriptors:
        return {
            "ok": False,
            "error": f"unknown source_key {source_key!r}",
            "available": sorted(descriptors.keys()),
        }
    descriptor = descriptors[source_key]
    ndjson = _ndjson_path(descriptor)
    if not ndjson.exists():
        return {
            "ok": True,
            "source_key": source_key,
            "total": 0,
            "offset": offset,
            "limit": limit,
            "next_offset": None,
            "rows": [],
            "note": "no committed NDJSON; first T1 collection pending",
        }

    rows: List[Dict[str, Any]] = []
    total = 0
    for record in read_ndjson(ndjson):
        total += 1
        if total - 1 < offset:
            continue
        if limit is not None and len(rows) >= limit:
            continue
        rows.append({
            "data": dict(record.data),
            "attestation": dict(record.attestation),
            "rendering": dict(record.rendering),
            "data_schema_id": record.data_schema_id,
            "mpr_version": record.mpr_version,
        })

    next_offset: Optional[int]
    if limit is None:
        next_offset = None
    else:
        end = offset + len(rows)
        next_offset = end if end < total else None

    return {
        "ok": True,
        "source_key": source_key,
        "total": total,
        "offset": offset,
        "limit": limit,
        "next_offset": next_offset,
        "rows": rows,
    }


def get_attested_descriptor(source_key: str) -> Dict[str, Any]:
    """Return the full parsed descriptor for one source.

    Used by UI code that wants to render the descriptor's
    ``[rendering]``, ``[source]``, ``[gap_targeting]`` content
    without iterating row data first.
    """
    descriptors = _descriptors()
    if source_key not in descriptors:
        return {
            "ok": False,
            "error": f"unknown source_key {source_key!r}",
            "available": sorted(descriptors.keys()),
        }
    descriptor = descriptors[source_key]
    return {
        "ok": True,
        "source_key": source_key,
        "descriptor": descriptor.to_dict(),
    }


def attestation_audit(source_key: str) -> Dict[str, Any]:
    """Return per-row attestation metadata (no data payload).

    Cheap; paper-appendix-ready. Each row returns its
    ``response_sha256``, ``retrieved_at``, ``parser_version``,
    ``parser_rule_hash``, ``collector_descriptor_hash`` so a
    downstream consumer can reproduce the row's provenance trail.
    """
    descriptors = _descriptors()
    if source_key not in descriptors:
        return {
            "ok": False,
            "error": f"unknown source_key {source_key!r}",
            "available": sorted(descriptors.keys()),
        }
    descriptor = descriptors[source_key]
    ndjson = _ndjson_path(descriptor)
    if not ndjson.exists():
        return {
            "ok": True,
            "source_key": source_key,
            "n_rows": 0,
            "rows": [],
            "note": "no committed NDJSON; first T1 collection pending",
        }

    rows: List[Dict[str, str]] = []
    for record in read_ndjson(ndjson):
        attestation = dict(record.attestation)
        rows.append({
            "data_schema_id": record.data_schema_id,
            "response_sha256": attestation.get("response_sha256", ""),
            "retrieved_at": attestation.get("retrieved_at", ""),
            "parser_version": attestation.get("parser_version", ""),
            "parser_rule_hash": attestation.get("parser_rule_hash", ""),
            "collector_descriptor_hash": attestation.get(
                "collector_descriptor_hash", ""
            ),
        })
    return {
        "ok": True,
        "source_key": source_key,
        "n_rows": len(rows),
        "rows": rows,
    }


# ──────────────────────────────────────────────────────────────────────
# Streaming — Python-only, NOT bridge-exposed (Pyodide-incompatible)
# ──────────────────────────────────────────────────────────────────────


def iter_attested_dataset(source_key: str) -> Iterator[MPRRecord]:
    """Stream MPRRecords from a registered source's NDJSON.

    NOT bridge-exposed (returns a Python iterator, not JSON-serialisable).
    Use this from Python consumers that need to process large rosters
    (e.g. the eventual ~1,800-row EarthRef SC seamount catalog) without
    materialising the full list.
    """
    descriptors = _descriptors()
    if source_key not in descriptors:
        raise KeyError(f"unknown source_key {source_key!r}")
    descriptor = descriptors[source_key]
    ndjson = _ndjson_path(descriptor)
    if not ndjson.exists():
        return iter(())
    return read_ndjson(ndjson)


__all__ = [
    "list_attested_sources",
    "get_attested_dataset",
    "get_attested_descriptor",
    "attestation_audit",
    "iter_attested_dataset",
]
