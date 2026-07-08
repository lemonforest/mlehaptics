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
* `srmech.amsc.format` — MPR record format.
* `srmech.amsc.descriptor` — descriptor TOML schema.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .descriptor import (
    Descriptor,
    discover_descriptors,
)
from .format import MPRRecord, read_ndjson


# ──────────────────────────────────────────────────────────────────────
# rc172 — the catalog REGISTRY / KERNEL-STATE / AUDIT logic dispatches to C
# (the ORCHESTRATION→C spine, batch 2). Each native peer COMPOSES the
# existing kernels (the srmech_json parser+writer+builder + srmech_sha256_hex
# for the kernel cache_hash); a bare-C host runs the catalog registry/kernel/
# audit surface with no json.dumps. STATE is caller-owned — Python passes its
# module globals (registered roots / kernel path+class / the FS-derived
# overlay set + NDJSON bytes) in per call. Every dispatch is hasattr-guarded
# (a stale ABI-3 lib keeps the COMPLETE pure path) and returns ``None`` on any
# missing symbol / serialisation issue / non-OK status so the caller runs the
# pure path (value-parity, never a rescue).
# ──────────────────────────────────────────────────────────────────────


def _catalog_lib(*symbols: str):
    """Return the native LIB iff HAS_NATIVE and every named rc172 symbol is
    bound (a stale ABI-3 lib missing them → ``None`` → pure path)."""
    from . import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    lib = _native.LIB
    for sym in symbols:
        if not hasattr(lib, sym):
            return None
    return lib


def _opt_bytes(s: Optional[str]) -> Optional[bytes]:
    """UTF-8 encode an optional string (``None`` → ``None`` → a C NULL)."""
    return s.encode("utf-8") if s is not None else None


def _registered_roots_native(
    root_path: str, root_source: str, ext_pairs: List[List[str]]
) -> Optional[List[Dict[str, str]]]:
    """Native ``list_registered_roots``: build the [{path, source}, ...] array
    (host root first, then the external pairs) in the C canonical writer."""
    lib = _catalog_lib("srmech_catalog_registered_roots",
                       "srmech_catalog_registered_roots_arena_bytes")
    if lib is None:
        return None
    import ctypes
    from . import _native
    rp = root_path.encode("utf-8")
    rs = root_source.encode("utf-8")
    ext = json.dumps(ext_pairs, ensure_ascii=False).encode("utf-8")
    ws_bytes = int(lib.srmech_catalog_registered_roots_arena_bytes(
        len(rp), len(rs), len(ext)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = 2 * len(ext) + len(rp) + len(rs) + 4096
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = lib.srmech_catalog_registered_roots(
        rp, len(rp), rs, len(rs), ext, len(ext),
        ws, ws_bytes, out, out_cap, ctypes.byref(out_len))
    if rc != _native.SRMECH_OK:
        return None
    return json.loads(out.raw[:out_len.value].decode("utf-8"))


def _local_kernel_state_native(
    active: bool, path: Optional[str], adapter_class: Optional[str],
    per_source: List[Dict[str, str]],
) -> Optional[Dict[str, Any]]:
    """Native ``get_local_kernel_state``: assemble the state envelope + the
    Class-A cache_hash = sha256("\\n".join(f"{source_key}\\t{overlay_sha256}"))
    over the caller-provided (FS-derived) per_source set."""
    lib = _catalog_lib("srmech_catalog_local_kernel_state",
                       "srmech_catalog_local_kernel_state_arena_bytes")
    if lib is None:
        return None
    import ctypes
    from . import _native
    ps = json.dumps(per_source, ensure_ascii=False).encode("utf-8")
    pb = _opt_bytes(path)
    ab = _opt_bytes(adapter_class)
    pl = len(pb) if pb is not None else 0
    al = len(ab) if ab is not None else 0
    ws_bytes = int(lib.srmech_catalog_local_kernel_state_arena_bytes(
        pl, al, len(ps)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = len(ps) + pl + al + 4096
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = lib.srmech_catalog_local_kernel_state(
        1 if active else 0, pb, pl, ab, al, ps, len(ps),
        ws, ws_bytes, out, out_cap, ctypes.byref(out_len))
    if rc != _native.SRMECH_OK:
        return None
    return json.loads(out.raw[:out_len.value].decode("utf-8"))


def _use_local_kernel_native(
    *, clear: bool, resolved: Optional[str] = None,
    adapter_class: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Native ``use_local_kernel`` / ``clear_local_kernel`` HAPPY-PATH response
    (the clear response, or the success response for an already-validated
    overlay). Error responses (invalid class / missing / not-a-dir) stay in
    Python (their repr-formatted messages are host presentation)."""
    lib = _catalog_lib("srmech_catalog_use_local_kernel",
                       "srmech_catalog_use_local_kernel_arena_bytes")
    if lib is None:
        return None
    import ctypes
    from . import _native
    pb = _opt_bytes(resolved)
    ab = _opt_bytes(adapter_class)
    pl = len(pb) if pb is not None else 0
    al = len(ab) if ab is not None else 0
    ws_bytes = int(lib.srmech_catalog_use_local_kernel_arena_bytes(pl, al))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = pl + al + 4096
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = lib.srmech_catalog_use_local_kernel(
        1 if clear else 0, pb, pl, ab, al,
        ws, ws_bytes, out, out_cap, ctypes.byref(out_len))
    if rc != _native.SRMECH_OK:
        return None
    return json.loads(out.raw[:out_len.value].decode("utf-8"))


def _attestation_audit_native(
    source_key: str, ndjson: Path
) -> Optional[Dict[str, Any]]:
    """Native ``attestation_audit``: iterate the NDJSON bytes + project the
    per-row attestation metadata (composes the srmech_json parser). Returns
    ``None`` on any read / parse issue so the caller runs the pure path
    (which raises MPRValidationError on a genuinely malformed line)."""
    lib = _catalog_lib("srmech_catalog_attestation_audit",
                       "srmech_catalog_attestation_audit_arena_bytes")
    if lib is None:
        return None
    import ctypes
    from . import _native
    try:
        nd = ndjson.read_bytes()
    except OSError:
        return None
    sk = source_key.encode("utf-8")
    ws_bytes = int(lib.srmech_catalog_attestation_audit_arena_bytes(
        len(nd), len(sk)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = 2 * len(nd) + 4096
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = lib.srmech_catalog_attestation_audit(
        sk, len(sk), nd, len(nd), ws, ws_bytes, out, out_cap,
        ctypes.byref(out_len))
    if rc != _native.SRMECH_OK:
        return None
    return json.loads(out.raw[:out_len.value].decode("utf-8"))


# ──────────────────────────────────────────────────────────────────────
# Discovery — cached at module load
# ──────────────────────────────────────────────────────────────────────
#
# Cross-package design (srmech AMSC framework hosted in `srmech.amsc`,
# but consumed by downstream packages whose catalog SSOTs live elsewhere
# — e.g. ephemerides-spectral's `_research/attested/` subtree):
#
# `_attested_root()` returns srmech's own `amsc/attested/` directory,
# which is the SSOT for any srmech-primary catalogs (e.g. the future
# `citations_curated/`). Downstream packages PUSH their catalog roots
# via `register_attested_root(path, *, source)` — typically called at
# package-import time (one line of bootstrap per consumer).
#
# `_descriptors()` walks the union of srmech's own root + every
# externally-registered root, returning a single source_key -> Descriptor
# map. Conflict policy: first-registered wins; duplicate source_key logs
# a warning. Order is deterministic (registration order is preserved
# via list semantics).


def _attested_root() -> Path:
    """Resolve srmech's own attested-tree root.

    Returns the ``attested/`` directory next to this module. Downstream
    packages with their own catalog SSOTs register via
    :func:`register_attested_root` rather than overriding this.
    """
    return Path(__file__).resolve().parent / "attested"


_REGISTERED_ROOTS: List[tuple[Path, str]] = []
"""External catalog roots registered by downstream packages.

Each entry is ``(path, source)``. Insertion order is preserved (list
semantics), which is the conflict-resolution order for duplicate
source_keys: first-registered wins.
"""

_DESCRIPTORS_CACHE: Optional[Dict[str, Descriptor]] = None


def register_attested_root(
    path: Path | str, *, source: str
) -> Dict[str, Any]:
    """Register an external catalog root with the AMSC framework.

    Downstream packages (e.g. ephemerides-spectral) whose catalog SSOTs
    live outside ``srmech/amsc/attested/`` call this at package-import
    time so :func:`list_attested_sources` / :func:`get_attested_dataset`
    / etc. enumerate the union of srmech's own catalogs plus the
    registered roots.

    Parameters
    ----------
    path
        Filesystem path to the external attested-root directory
        (shaped like ``<source_key>/descriptor.toml``).
    source
        Human-readable identifier for the registering package
        (e.g. ``"ephemerides-spectral"``). Used in conflict-warning
        messages and for introspection.

    Returns
    -------
    dict
        ``{ok, path, source, total_registered}`` for confirmation.
        Idempotent: re-registering the same ``(path, source)`` pair
        is a no-op; the registration list does not grow.

    Conflict policy
    ---------------
    If two registered roots contain descriptors with the same
    ``source.key``, the FIRST-REGISTERED root wins and a warning is
    logged. srmech's own ``amsc/attested/`` root is treated as
    "registered first" implicitly.
    """
    global _DESCRIPTORS_CACHE
    resolved = Path(path).expanduser().resolve()
    entry = (resolved, str(source))
    if entry in _REGISTERED_ROOTS:
        # Idempotent re-registration.
        return {
            "ok": True,
            "path": str(resolved),
            "source": str(source),
            "total_registered": len(_REGISTERED_ROOTS),
            "note": "already registered (idempotent re-call)",
        }
    _REGISTERED_ROOTS.append(entry)
    # Invalidate cache so the next _descriptors() call enumerates the
    # newly-registered root.
    _DESCRIPTORS_CACHE = None
    return {
        "ok": True,
        "path": str(resolved),
        "source": str(source),
        "total_registered": len(_REGISTERED_ROOTS),
    }


def list_registered_roots() -> List[Dict[str, str]]:
    """Return introspection metadata for all registered roots.

    Includes srmech's own ``amsc/attested/`` (as the implicit
    first-registered root) plus every externally-registered root in
    registration order. Used by downstream consumers for diagnostic
    output and by tests for registration-order verification.
    """
    ext_pairs = [[str(path), src] for path, src in _REGISTERED_ROOTS]
    native = _registered_roots_native(
        str(_attested_root()), "srmech.amsc", ext_pairs)
    if native is not None:
        return native
    rows: List[Dict[str, str]] = [
        {"path": str(_attested_root()), "source": "srmech.amsc"},
    ]
    for path, src in _REGISTERED_ROOTS:
        rows.append({"path": str(path), "source": src})
    return rows


def _clear_registered_roots() -> None:
    """Clear all externally-registered roots. Test-only.

    Used by ``tests/test_register_attested_root.py`` to reset state
    between tests. Not part of the public API; consumers should never
    need this.
    """
    global _DESCRIPTORS_CACHE
    _REGISTERED_ROOTS.clear()
    _DESCRIPTORS_CACHE = None


def _descriptors() -> Dict[str, Descriptor]:
    """Lazy-load + cache the descriptor map for this install.

    Walks the union of srmech's own ``amsc/attested/`` root and every
    externally-registered root (in registration order). For duplicate
    source_keys, first-registered wins and a warning is emitted via
    ``warnings.warn`` (visible to test runners; not noisy in
    production).
    """
    global _DESCRIPTORS_CACHE
    if _DESCRIPTORS_CACHE is not None:
        return _DESCRIPTORS_CACHE

    import warnings as _warnings

    # Walk srmech's own root first (implicit "first-registered").
    merged: Dict[str, Descriptor] = {}
    srmech_root = _attested_root()
    if srmech_root.exists():
        for key, desc in discover_descriptors(srmech_root).items():
            merged[key] = desc

    # Then external roots in registration order.
    for ext_path, ext_source in _REGISTERED_ROOTS:
        if not ext_path.exists():
            continue
        external = discover_descriptors(ext_path)
        for key, desc in external.items():
            if key in merged:
                _warnings.warn(
                    f"register_attested_root: duplicate source_key {key!r} "
                    f"from {ext_source!r} at {ext_path}; first-registered "
                    f"({merged[key].path}) wins.",
                    stacklevel=2,
                )
                continue
            merged[key] = desc

    _DESCRIPTORS_CACHE = merged
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
        native = _use_local_kernel_native(clear=True)
        if native is not None:
            return native
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
    native = _use_local_kernel_native(
        clear=False, resolved=str(resolved), adapter_class=adapter_class)
    if native is not None:
        return native
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

    active = _LOCAL_KERNEL_PATH is not None
    path_str = str(_LOCAL_KERNEL_PATH) if _LOCAL_KERNEL_PATH else None
    native = _local_kernel_state_native(
        active, path_str, _LOCAL_KERNEL_ADAPTER_CLASS, per_source)
    if native is not None:
        return native

    canonical = "\n".join(
        f"{e['source_key']}\t{e['overlay_sha256']}" for e in per_source
    )
    from .format import sha256_bytes as _sha256
    cache_hash = _sha256(canonical.encode("utf-8"))

    return {
        "ok": True,
        "active": active,
        "path": path_str,
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
    """SHA-256 of an arbitrary file's bytes.

    Phase B5: for files small enough to fit in memory (the only
    callsite is overlay attestation, where NDJSON ground-proof
    files run a few KB to a few MB), we just slurp + route through
    ``sha256_bytes`` to get the native C dispatch. Streaming
    hashlib would require a multi-update C API (not yet ported)
    and we don't have files large enough to justify it.
    """
    from .format import sha256_bytes
    return sha256_bytes(path.read_bytes())


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
    from .adapters import literature_curated as _lc
    from .adapters._base import parser_rule_hash as _rule_hash
    from .descriptor import descriptor_hash as _desc_hash
    from .format import sha256_bytes as _sha256

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
    from .descriptor import KNOWN_ADAPTERS
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
    composer in ``adapters._base.run`` handles fetch +
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
    from . import adapters as _adapters

    package_version = _read_package_version()
    parser_version = f"srmech {package_version}"
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
        try:
            from .. import __version__ as _v  # type: ignore
            return str(_v)
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

    native = _attestation_audit_native(source_key, ndjson)
    if native is not None:
        return native

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


# ──────────────────────────────────────────────────────────────────────
# ADR-0002 Phase 2 — Operator-chain bridge surfaces (v0.4.1rc5)
# ──────────────────────────────────────────────────────────────────────


def _load_catalog_chains(source_key: str) -> List[Any]:
    """Parse all ``[[catalog.operator_chain]]`` entries from a descriptor.

    Returns a list of :class:`srmech.amsc.compose.ChainSpec`. Empty
    list when the descriptor declares no chains. Raises
    ``ChainSpecError`` on a malformed declaration.
    """
    descriptors = _descriptors()
    if source_key not in descriptors:
        raise KeyError(f"unknown source_key {source_key!r}")
    descriptor = descriptors[source_key]
    import sys
    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover
        import tomli as tomllib  # type: ignore
    raw = descriptor.path.read_bytes()
    toml_dict = tomllib.loads(raw.decode("utf-8"))
    # Lazy import to avoid circular bootstrap.
    from . import compose as _compose
    return _compose.parse_catalog_chains(toml_dict)


def list_catalog_chains(source_key: str) -> Dict[str, Any]:
    """Enumerate operator chains declared by a catalog.

    Returns a dict with the chain catalog: each chain's ``name``,
    ``summary``, ``returns``, and ``n_steps``. Useful for tool-schema
    introspection (auto-derived ToolEntry registration is Phase 3
    scope).

    Parameters
    ----------
    source_key
        The descriptor's ``[source].key`` string.

    Returns
    -------
    dict
        ``{ok, source_key, n_chains, chains}`` where each chain has
        ``{name, summary, returns, on_error, n_steps, classes}``
        (``classes`` is the per-step class_id sequence).
    """
    try:
        chains = _load_catalog_chains(source_key)
    except KeyError:
        return {
            "ok": False,
            "error": f"unknown source_key {source_key!r}",
            "available": sorted(_descriptors().keys()),
        }
    return {
        "ok": True,
        "source_key": source_key,
        "n_chains": len(chains),
        "chains": [
            {
                "name": c.name,
                "summary": c.summary,
                "returns": c.returns,
                "on_error": c.on_error,
                "n_steps": len(c.steps),
                "classes": [s.class_id for s in c.steps],
            }
            for c in chains
        ],
    }


def run_catalog_chain(
    source_key: str,
    chain_name: str,
    *,
    row_index: Optional[int] = None,
    inputs: Optional[Dict[str, Any]] = None,
) -> Any:
    """Execute a declared chain on a catalog row.

    Parameters
    ----------
    source_key
        The descriptor's ``[source].key`` string.
    chain_name
        The chain's ``name`` field.
    row_index
        Zero-based index into the catalog's rows for ``@row.*``
        binding. May be ``None`` if the chain references no
        ``@row.*`` fields; raises ``RuntimeError`` if a chain that
        needs a row is invoked with ``row_index=None``.
    inputs
        Runtime ``@input.*`` parameters; defaults to empty dict.

    Returns
    -------
    Any
        Output of the final step (chain's ``returns`` type).
    """
    chains = _load_catalog_chains(source_key)
    spec = None
    for c in chains:
        if c.name == chain_name:
            spec = c
            break
    if spec is None:
        raise KeyError(
            f"catalog {source_key!r} has no chain named {chain_name!r}; "
            f"available: {[c.name for c in chains]}"
        )
    row = None
    if row_index is not None:
        ds = get_attested_dataset(source_key,
                                  limit=row_index + 1, offset=row_index)
        rows = ds.get("rows", [])
        if not rows:
            raise IndexError(
                f"catalog {source_key!r}: row_index {row_index} out of "
                f"range (total={ds.get('total', 0)})"
            )
        # `row` binding exposes the row's MPR record's `data` block
        # plus the descriptor's rendering attestation for context.
        row = dict(rows[0].get("data", {}))
    from . import compose as _compose
    return _compose.run_chain(spec, row=row, inputs=inputs or {})


__all__ = [
    "list_attested_sources",
    "get_attested_dataset",
    "get_attested_descriptor",
    "attestation_audit",
    "iter_attested_dataset",
    "use_local_kernel",
    "clear_local_kernel",
    "get_local_kernel_state",
    "register_attested_root",
    "list_registered_roots",
    "list_catalog_chains",
    "run_catalog_chain",
]
