"""Catalog wrapper for the attested collector framework.

Bridge surfaces are universal — they iterate descriptors at module
load and surface row content / attestation / descriptor metadata
without per-source code paths. The whole point of v0.25.0 is that
adding a source is a CONFIG change (descriptor + schema + NDJSON);
no per-source ``*_catalog.py`` module needed.

Reproducibility tiers (notebook §18.1)
---------------------------------------
* **T0** — committed NDJSON under ``_research/attested/<source>/``.
  Byte-identical across all installs of a given version.
* **T1** — CI-baked extension (auto-PR refresh via the collect
  workflow). Byte-identical at the next ship.
* **T2** — *(v0.25.1+)* user runtime kernel. Local NDJSON cache
  registered via :func:`use_local_kernel`. Byte-identical *within*
  a user's local cache state; the cache hash documents the state
  for paper appendices.
* **T3** — *(v0.25.2+)* live query.

When a T2 overlay is registered, queries merge T0+T1 baseline rows
with T2 overlay rows on a per-source-and-table basis. Default
policy is **replace**: an overlay file at
``<overlay>/<source>/<table>.ndjson`` REPLACES the baseline file
for that source. Future v0.25.x ships may add an explicit append
policy.

Surfaces
--------
* :func:`list_attested_sources` — every registered source's
  rendered metadata (name, purpose, license, cite_as, gap_targeting).
* :func:`get_attested_dataset` — paginated row content for one
  source, with full attestation + rendering blocks. Honours T2
  overlay when registered.
* :func:`get_attested_descriptor` — full parsed descriptor for one
  source (UI / pre-fetch).
* :func:`attestation_audit` — per-row attestation metadata, **no
  data payload** (cheap, paper-appendix-ready).
* :func:`use_local_kernel` — register a T2 user-runtime-kernel
  overlay. *(v0.25.1+)*
* :func:`clear_local_kernel` — remove the T2 overlay. *(v0.25.1+)*
* :func:`get_local_kernel_state` — return current T2 state +
  per-source cache-hash so a paper can replay exactly which rows
  were used. *(v0.25.1+)*

References
----------
* Notebook §18 — full normative format spec.
* `attested_collector_format` — MPR record format.
* `attested_collector_descriptor` — descriptor TOML schema.
"""

from __future__ import annotations

import hashlib
import json
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
    """Resolve the baseline NDJSON file path for a descriptor.

    Resolution order:

    1. **Explicit** ``[fetch].ndjson_path`` field if set in the
       descriptor. This is the load-bearing field — every existing
       descriptor authors it deliberately, and it's the field whose
       comment (in saturn_rings, mercury_dynamical_spectrum, etc.)
       documents the intent. Resolved relative to the descriptor's
       directory.
    2. **Fallback**: derive the filename stem from
       ``[schema].data_schema_id``'s middle part — e.g.
       ``earthref_sc.seamount.v1`` → ``seamount.ndjson``. This
       fallback exists for descriptors that omit the explicit
       field; if both are present, the explicit field wins.

    Pre-this-fix the resolver ignored the explicit field and used
    only the schema-id derivation, which silently disagreed when
    the two conventions diverged (the symptom: a descriptor with
    ``[fetch].ndjson_path = "foo.ndjson"`` but
    ``[schema].data_schema_id = "src.row.v1"`` would look for
    ``row.ndjson``, not ``foo.ndjson``, returning empty rows with
    the misleading ``"no committed NDJSON; first T1 collection
    pending"`` note even though the file existed at the documented
    path).
    """
    explicit = descriptor.fetch.get("ndjson_path")
    if explicit:
        return descriptor.path.parent / str(explicit)
    schema_id = str(descriptor.schema["data_schema_id"])
    parts = schema_id.split(".")
    # Convention: <source_key>.<table>.<version>
    table = parts[1] if len(parts) >= 3 else parts[-1]
    return descriptor.path.parent / f"{table}.ndjson"


def _table_name(descriptor: Descriptor) -> str:
    """Resolve the table-name part of the descriptor's data_schema_id.
    Mirrors :func:`_ndjson_path` filename stem."""
    schema_id = str(descriptor.schema["data_schema_id"])
    parts = schema_id.split(".")
    return parts[1] if len(parts) >= 3 else parts[-1]


# ──────────────────────────────────────────────────────────────────────
# T2 — User runtime kernel (v0.25.1+)
# ──────────────────────────────────────────────────────────────────────


_LOCAL_KERNEL_PATH: Optional[Path] = None
"""Currently registered T2 overlay root (or None for T0+T1 only)."""

_LOCAL_KERNEL_ADAPTER_CLASS: Optional[str] = None
"""Currently registered T2 overlay's adapter-class scope (or None for
all-classes). When set, only sources whose adapter matches this class
consult the overlay; sources outside the class fall through to the
T0+T1 baseline regardless of whether the overlay has a file for them.
See ADAPTER_CLASSES."""


def use_local_kernel(
    path: Optional[Path | str],
    *,
    adapter_class: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a user-runtime-kernel overlay (T2).

    Parameters
    ----------
    path
        Filesystem path to a directory shaped like
        ``<source_key>/<table>.ndjson``. When None, clears any
        registered overlay (equivalent to :func:`clear_local_kernel`).
    adapter_class
        Optional scope for the overlay. When set, the overlay only
        applies to sources whose adapter matches the class:

        * ``None`` (default) — overlay applies to all sources.
        * ``"fetched"`` — overlay applies only to live-fetched
          sources (html_scraper / json_api / csv_bulk / netcdf_grid /
          geotiff_bbox). Useful for "patch the live archives but
          leave curated literature alone."
        * ``"curated"`` — overlay applies only to literature-curated
          sources. Useful for "augment my literature catalogue with
          a private supplement, leave fetched data on the baseline."
        * A specific adapter name — overlay applies only to that
          adapter's sources.

        Validated against the same taxonomy as
        ``list_attested_sources(adapter_class=...)``; unknown class
        names raise ``ValueError``.

    Behaviour
    ---------
    Once registered, queries (``get_attested_dataset`` /
    ``attestation_audit``) consult the overlay directory FIRST when
    the source's adapter matches the registered class. For each
    in-scope source, if the overlay contains a matching
    ``<source>/<table>.ndjson`` file, it REPLACES the baseline
    NDJSON for that source. Out-of-scope sources, and in-scope
    sources without an overlay file, fall through to the T0+T1
    baseline.

    Returns the new local-kernel state for confirmation, including
    ``adapter_class`` echo.
    """
    global _LOCAL_KERNEL_PATH, _LOCAL_KERNEL_ADAPTER_CLASS
    if path is None:
        _LOCAL_KERNEL_PATH = None
        _LOCAL_KERNEL_ADAPTER_CLASS = None
        return {
            "ok": True,
            "active": False,
            "path": None,
            "adapter_class": None,
            "message": "T2 overlay cleared; queries return T0+T1 baseline only",
        }
    # Validate adapter_class up-front so a typo doesn't silently
    # register an unreachable overlay.
    if adapter_class is not None:
        try:
            _adapter_matches_class("html_scraper", adapter_class)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        return {
            "ok": False,
            "error": f"local kernel path does not exist: {resolved}",
        }
    if not resolved.is_dir():
        return {
            "ok": False,
            "error": f"local kernel path is not a directory: {resolved}",
        }
    _LOCAL_KERNEL_PATH = resolved
    _LOCAL_KERNEL_ADAPTER_CLASS = adapter_class
    scope_msg = (
        f" (scope: adapter_class={adapter_class!r})"
        if adapter_class else ""
    )
    return {
        "ok": True,
        "active": True,
        "path": str(resolved),
        "adapter_class": adapter_class,
        "message": f"T2 overlay registered at {resolved}{scope_msg}",
    }


def clear_local_kernel() -> Dict[str, Any]:
    """Remove the registered T2 overlay. Equivalent to
    ``use_local_kernel(None)``."""
    return use_local_kernel(None)


def get_local_kernel_state() -> Dict[str, Any]:
    """Return the current T2 state and per-source cache-hash.

    The cache-hash is SHA-256 over the canonical-serialised list of
    ``(source_key, ndjson_sha256)`` pairs. Used in paper appendices
    to document exactly which rows were used at runtime — papers
    can replay the cache state by recomputing this hash against the
    archived overlay tree.
    """
    descriptors = _descriptors()
    per_source: List[Dict[str, str]] = []
    for key in sorted(descriptors.keys()):
        descriptor = descriptors[key]
        overlay = _overlay_path_for(descriptor)
        if overlay is None or not overlay.exists():
            continue
        per_source.append({
            "source_key": key,
            "table": _table_name(descriptor),
            "overlay_path": str(overlay),
            "overlay_sha256": _file_sha256(overlay),
        })

    canonical = "\n".join(
        f"{e['source_key']}\t{e['overlay_sha256']}" for e in per_source
    )
    cache_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return {
        "ok": True,
        "active": _LOCAL_KERNEL_PATH is not None,
        "path": str(_LOCAL_KERNEL_PATH) if _LOCAL_KERNEL_PATH else None,
        "adapter_class": _LOCAL_KERNEL_ADAPTER_CLASS,
        "n_overlay_sources": len(per_source),
        "per_source": per_source,
        "cache_hash": cache_hash,
    }


def _overlay_path_for(descriptor: Descriptor) -> Optional[Path]:
    """Resolve the T2 overlay NDJSON path for a descriptor (or
    None when no overlay is registered, or when the overlay's
    registered adapter_class scope excludes this descriptor's
    adapter)."""
    if _LOCAL_KERNEL_PATH is None:
        return None
    if _LOCAL_KERNEL_ADAPTER_CLASS is not None:
        if not _adapter_matches_class(
            descriptor.adapter_name, _LOCAL_KERNEL_ADAPTER_CLASS
        ):
            return None
    return _LOCAL_KERNEL_PATH / descriptor.key / f"{_table_name(descriptor)}.ndjson"


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolved_ndjson_path(descriptor: Descriptor) -> Path:
    """Resolve the NDJSON path actually consumed at query time —
    T2 overlay if registered + present, else T0+T1 baseline."""
    overlay = _overlay_path_for(descriptor)
    if overlay is not None and overlay.exists():
        return overlay
    return _ndjson_path(descriptor)


def _iter_records_for_descriptor(
    descriptor: Descriptor, ndjson: Path
) -> Iterator[MPRRecord]:
    """Yield MPRRecords for a descriptor's committed NDJSON.

    Two on-disk formats are recognised, dispatched on adapter type:

    * **Live-fetcher adapters** (html_scraper, json_api, csv_bulk,
      netcdf_grid, geotiff_bbox) — committed NDJSON is the byte-exact
      output of a prior ``_base.run()`` invocation: full MPRRecord
      shape per line (data + attestation + rendering). Read via
      ``read_ndjson()``.
    * **literature_curated** — committed NDJSON is curator-friendly
      data-only (one row's data block per line; no attestation /
      rendering). Synthesise the full MPRRecord at read time using
      the descriptor's metadata + per-row data hash. This keeps the
      curator's authoring experience light (hand-edit one JSON
      object per line) while preserving the runtime invariant that
      ``get_attested_dataset()`` returns full attestation + rendering
      blocks.

    For unknown adapter names, falls back to read_ndjson() — same
    behaviour as before this dispatch was introduced.
    """
    adapter_name = descriptor.adapter_name
    if adapter_name == "literature_curated":
        yield from _iter_literature_curated_records(descriptor, ndjson)
    else:
        yield from read_ndjson(ndjson)


def _iter_literature_curated_records(
    descriptor: Descriptor, ndjson: Path
) -> Iterator[MPRRecord]:
    """Read a literature_curated descriptor's data-only NDJSON and
    synthesise full MPRRecords at read time.

    Attestation block fields synthesised per-row:

    * ``source_doi`` — from the row's ``data.source_doi`` (per-row
      DOI; the descriptor's ``canonical_doi`` is the catalogue-wide
      fallback for live-fetcher adapters but each literature-curated
      row carries its own paper-level DOI).
    * ``source_url`` — descriptor's ``[source].homepage``.
    * ``license`` — descriptor's ``[source].license``.
    * ``retrieved_at`` — the row's ``data.entered_locally_at``,
      converted to an ISO 8601 datetime at midnight UTC. This is
      deterministic per-row (curator-supplied) and stable across
      reads, so ``response_sha256`` stays byte-stable.
    * ``response_sha256`` — SHA-256 over canonical JSON encoding of
      the row's data block. Each row is its own attestation unit
      since rows are independently authored.
    * ``parser_version`` — ``"literature_curated/v1"`` (constant).
    * ``parser_rule_hash`` — adapter base hash of the descriptor's
      ``[parse]`` section (same as live-fetcher adapters).
    * ``collector_descriptor_path`` + ``collector_descriptor_hash``
      — descriptor file name + canonical-serialisation SHA.
    """
    from .attested_adapters import literature_curated as _lc
    from .attested_adapters._base import parser_rule_hash as _rule_hash
    from .attested_collector_descriptor import descriptor_hash as _desc_hash
    from .attested_collector_format import sha256_bytes as _sha256

    raw = ndjson.read_bytes()
    rule_hash = _rule_hash(descriptor.parse)
    desc_hash = _desc_hash(descriptor.path)
    data_schema_id = str(descriptor.schema["data_schema_id"])
    license_val = str(descriptor.source["license"])
    homepage = str(descriptor.source.get("homepage", ""))

    for row_index, data in enumerate(_lc.parse(raw, descriptor), start=1):
        # Canonical-JSON encoding for byte-stable response_sha256.
        row_bytes = json.dumps(
            data, sort_keys=True, ensure_ascii=False
        ).encode("utf-8")
        row_sha256 = _sha256(row_bytes)

        # entered_locally_at is YYYY-MM-DD; convert to a midnight-UTC
        # ISO 8601 stamp for retrieved_at compatibility.
        entered = str(data.get("entered_locally_at", ""))
        retrieved_at = (
            f"{entered}T00:00:00Z" if entered else "1970-01-01T00:00:00Z"
        )

        attestation = {
            "source_doi": str(data.get("source_doi", "")),
            "source_url": homepage,
            "license": license_val,
            "retrieved_at": retrieved_at,
            "response_sha256": row_sha256,
            "parser_version": "literature_curated/v1",
            "parser_rule_hash": rule_hash,
            "collector_descriptor_path": str(descriptor.path.name),
            "collector_descriptor_hash": desc_hash,
        }

        rendering = {
            "human_readable_name": (
                f"{descriptor.source['human_readable_name']} — row {row_index}"
            ),
            "cite_as": str(
                descriptor.rendering.get("cite_as_template", "")
            ).replace("{retrieved_at:%Y-%m-%d}", entered or "unknown"),
            "purpose": (
                f"ground-proof row for "
                f"{data.get('regime_label', 'unspecified')} regime "
                f"(literature-curated, source DOI: "
                f"{data.get('source_doi', '<missing>')})"
            ),
        }

        yield MPRRecord(
            mpr_version="1.0",
            data=data,
            data_schema_id=data_schema_id,
            attestation=attestation,
            rendering=rendering,
        )


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


# Adapter-class taxonomy. Two natural classes plus the option to
# filter by a specific adapter name. The classes are an interpretive
# overlay on the adapter set — they let consumers say "give me only
# offline-safe sources" or "give me only live-archive sources" without
# enumerating individual adapter names. See notebook §18.9 for the
# user-facing framing of this discipline.
ADAPTER_CLASSES: Dict[str, frozenset] = {
    # Network-fetching adapters. Require live archive + a `requests`-
    # style dep at fetch time; T1 CI workflow auto-PRs refreshed
    # NDJSON; useful for evolving upstream archives.
    "fetched": frozenset({
        "html_scraper",
        "json_api",
        "csv_bulk",
        "netcdf_grid",
        "geotiff_bbox",
    }),
    # Literature-curated adapters. No network fetch; rows committed
    # directly with per-row source DOI; useful for offline-first
    # workflows and per-body literature catalogues.
    "curated": frozenset({"literature_curated"}),
}


def _adapter_matches_class(
    adapter_name: str, adapter_class: Optional[str]
) -> bool:
    """Return True if the adapter belongs to the requested class.

    `adapter_class` accepts:
      - None — match any (no filter; default).
      - "fetched" / "curated" — match the named class (see
        ADAPTER_CLASSES).
      - a specific adapter name (e.g., "literature_curated",
        "html_scraper") — exact match.

    Unknown class names raise ValueError so consumers see the typo
    instead of a silently empty result.
    """
    if adapter_class is None:
        return True
    if adapter_class in ADAPTER_CLASSES:
        return adapter_name in ADAPTER_CLASSES[adapter_class]
    # Treat as specific adapter name; validate against KNOWN_ADAPTERS
    # to surface typos.
    from .attested_collector_descriptor import KNOWN_ADAPTERS
    if adapter_class in KNOWN_ADAPTERS:
        return adapter_name == adapter_class
    raise ValueError(
        f"unknown adapter_class {adapter_class!r}; "
        f"valid classes: {sorted(ADAPTER_CLASSES.keys())}; "
        f"or a specific adapter name from {sorted(KNOWN_ADAPTERS)}"
    )


def list_attested_sources(
    *, adapter_class: Optional[str] = None
) -> Dict[str, Any]:
    """Enumerate registered attested sources, optionally filtered by
    adapter class.

    Parameters
    ----------
    adapter_class
        Optional filter on adapter type. Accepts:

        * ``None`` (default) — return all sources.
        * ``"fetched"`` — only network-fetching adapters
          (html_scraper / json_api / csv_bulk / netcdf_grid /
          geotiff_bbox). Useful when a consumer wants only sources
          that the T1 CI workflow can auto-refresh against live
          archives.
        * ``"curated"`` — only literature-curated adapters
          (literature_curated). Useful for offline-first workflows
          and consumers who want only peer-reviewed-DOI-attested
          rows.
        * A specific adapter name (e.g., ``"literature_curated"``,
          ``"html_scraper"``) — exact-match filter on that adapter.

        Unknown class names raise ``ValueError`` to surface typos.

    Returns a dict with each source's rendered metadata: human-
    readable name, purpose, license, citation template, adapter,
    and gap-targeting regime labels. Useful for UI source-pickers
    and for the v0.26.x schema-gap-driven trigger.

    The response carries an ``adapter_class`` echo field for
    downstream consumers that want to log which filter was applied;
    this is None when no filter was passed.
    """
    descriptors = _descriptors()
    sources: List[Dict[str, Any]] = []
    for key in sorted(descriptors.keys()):
        d = descriptors[key]
        if not _adapter_matches_class(d.adapter_name, adapter_class):
            continue
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
        "adapter_class": adapter_class,
        "sources": sources,
    }


def get_attested_dataset(
    source_key: str,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    live: bool = False,
) -> Dict[str, Any]:
    """Return paginated row content for a registered source.

    Each row carries its full ``data`` + ``attestation`` +
    ``rendering`` blocks. Use :func:`attestation_audit` for the
    cheap data-block-free variant.

    Parameters
    ----------
    source_key
        The descriptor's ``[source].key`` string.
    limit, offset
        Pagination over the result set.
    live
        *(v0.25.2+)* When ``True``, fetch the source's rows from
        its upstream archive at call time (T3 reproducibility tier)
        instead of reading the committed NDJSON. The fetch uses
        the descriptor's declared adapter; each row is stamped
        with retrieval-time + response checksum + collector-
        descriptor-hash, just like a T1 collector run, plus a
        ``"_tier": "T3"`` discriminator on the returned envelope.
        Defaults to ``False`` (T0+T1+T2 baseline).

    Returns
    -------
    dict
        ``{ok, source_key, total, offset, limit, next_offset, rows}``
        where ``rows`` is a list-of-dict slice. ``next_offset`` is
        ``None`` when the slice extends through end-of-file. T3
        responses also carry ``tier="T3"`` + ``retrieved_at`` +
        ``upstream_response_sha256`` for paper-appendix replay.
    """
    descriptors = _descriptors()
    if source_key not in descriptors:
        return {
            "ok": False,
            "error": f"unknown source_key {source_key!r}",
            "available": sorted(descriptors.keys()),
        }
    descriptor = descriptors[source_key]

    if live:
        return _get_attested_dataset_live(
            descriptor, limit=limit, offset=offset
        )

    ndjson = _resolved_ndjson_path(descriptor)
    if not ndjson.exists():
        return {
            "ok": True,
            "source_key": source_key,
            "tier": "T0+T1+T2",
            "total": 0,
            "offset": offset,
            "limit": limit,
            "next_offset": None,
            "rows": [],
            "note": "no committed NDJSON; first T1 collection pending",
        }

    rows: List[Dict[str, Any]] = []
    total = 0
    record_iter = _iter_records_for_descriptor(descriptor, ndjson)
    for record in record_iter:
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
        "tier": "T0+T1+T2",
        "total": total,
        "offset": offset,
        "limit": limit,
        "next_offset": next_offset,
        "rows": rows,
    }


# ──────────────────────────────────────────────────────────────────────
# T3 — Live query (v0.25.2+)
# ──────────────────────────────────────────────────────────────────────


def _get_attested_dataset_live(
    descriptor: Descriptor,
    *,
    limit: Optional[int],
    offset: int,
) -> Dict[str, Any]:
    """Fetch a source's rows live from upstream (T3 tier).

    Runs the descriptor's declared adapter at call time. The
    composer in ``attested_adapters._base.run`` handles fetch +
    parse + per-row attestation; this function paginates the
    resulting MPRRecord stream and adds the T3 envelope fields.

    Reproducibility: weakest tier. Each row's attestation block
    carries the response_sha256 + retrieved_at the upstream
    *currently* serves; replaying requires re-running the live
    fetch against an unchanged upstream OR archiving the response
    bytes alongside the recorded retrieved_at + sha256.
    """
    import datetime as _dt

    # Lazy-import to keep regenerate.py off the network path.
    from . import attested_adapters as _adapters

    package_version = _read_package_version()
    parser_version = f"ephemerides-spectral {package_version}"
    retrieved_at = _dt.datetime.now(_dt.timezone.utc)

    rows: List[Dict[str, Any]] = []
    total = 0
    upstream_hashes: List[str] = []

    try:
        for record in _adapters.run(
            descriptor,
            parser_version=parser_version,
            retrieved_at=retrieved_at,
        ):
            total += 1
            sha = record.attestation.get("response_sha256", "")
            if sha and sha not in upstream_hashes:
                upstream_hashes.append(sha)
            if total - 1 < offset:
                continue
            if limit is not None and len(rows) >= limit:
                # Keep iterating to compute total when no limit
                # would be respected — but break early on limit
                # to avoid pulling the whole upstream just to
                # count when the consumer only wants `limit`
                # rows. Trade-off: total reflects only the
                # partial fetch consumed.
                continue
            rows.append({
                "data": dict(record.data),
                "attestation": dict(record.attestation),
                "rendering": dict(record.rendering),
                "data_schema_id": record.data_schema_id,
                "mpr_version": record.mpr_version,
            })
    except Exception as exc:  # noqa: BLE001 — surface adapter errors
        return {
            "ok": False,
            "source_key": descriptor.key,
            "tier": "T3",
            "error": f"live fetch failed: {exc}",
            "retrieved_at": retrieved_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    next_offset: Optional[int]
    if limit is None:
        next_offset = None
    else:
        end = offset + len(rows)
        next_offset = end if end < total else None

    return {
        "ok": True,
        "source_key": descriptor.key,
        "tier": "T3",
        "retrieved_at": retrieved_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "upstream_response_sha256s": upstream_hashes,
        "total": total,
        "offset": offset,
        "limit": limit,
        "next_offset": next_offset,
        "rows": rows,
    }


def _read_package_version() -> str:
    """Read the running package's version string. Used in T3
    attestation blocks so consumers can replay against the same
    parser_version that produced the row."""
    try:
        from .. import version as _ver  # type: ignore
        return str(_ver.__version__)
    except Exception:
        return "unknown"


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
    ndjson = _resolved_ndjson_path(descriptor)
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
    ndjson = _resolved_ndjson_path(descriptor)
    if not ndjson.exists():
        return iter(())
    return _iter_records_for_descriptor(descriptor, ndjson)


__all__ = [
    "list_attested_sources",
    "get_attested_dataset",
    "get_attested_descriptor",
    "attestation_audit",
    "iter_attested_dataset",
    "use_local_kernel",
    "clear_local_kernel",
    "get_local_kernel_state",
]
