"""Adapter protocol + shared infrastructure for the attested
collector framework.

Each adapter module in this package exposes ``ADAPTER_NAME`` plus
``fetch(descriptor) -> Iterator[bytes]`` and
``parse(raw, descriptor) -> Iterator[dict]`` callables. The
attestation step (``attest``) is shared — every adapter computes
the same SHA-256 fingerprint over upstream response bytes plus
descriptor hash plus retrieval timestamp.

The ``run`` composer turns a descriptor into an ``MPRRecord``
iterator: fetch → parse → attest → emit. This is the single entry
point invoked by collector workflows + ad-hoc collector runs.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any, Callable, Dict, Iterator, Mapping, Protocol

from ..descriptor import (
    Descriptor,
    descriptor_hash,
    render_template,
)
from ..format import (
    MPR_SCHEMA_VERSION,
    MPRRecord,
    sha256_bytes,
)


class AdapterError(RuntimeError):
    """Raised when an adapter fails to fetch or parse a source."""


class AdapterProtocol(Protocol):
    """Structural type for adapter modules.

    Each adapter module satisfies this protocol implicitly via duck
    typing; we don't use nominal inheritance because the five
    modules differ structurally and inheritance would over-couple.
    """

    ADAPTER_NAME: str

    def fetch(self, descriptor: Descriptor) -> Iterator[bytes]: ...

    def parse(
        self, raw: bytes, descriptor: Descriptor
    ) -> Iterator[Dict[str, Any]]: ...


# ──────────────────────────────────────────────────────────────────────
# Adapter registry
# ──────────────────────────────────────────────────────────────────────


ADAPTERS: Dict[str, "Callable[..., Any]"] = {}
"""Adapter-name → adapter-module mapping. Populated by each
adapter module at import time via `register`."""


def register(adapter_name: str, module: Any) -> None:
    """Register an adapter module under its ADAPTER_NAME. Called by
    each adapter module at import time."""
    ADAPTERS[adapter_name] = module


def get_adapter(adapter_name: str) -> Any:
    """Look up an adapter module by name. Raises AdapterError if
    not registered."""
    if adapter_name not in ADAPTERS:
        raise AdapterError(
            f"unknown adapter {adapter_name!r}; "
            f"registered: {sorted(ADAPTERS.keys())}"
        )
    return ADAPTERS[adapter_name]


# ──────────────────────────────────────────────────────────────────────
# Attestation (shared by all adapters)
# ──────────────────────────────────────────────────────────────────────


def attest(
    raw: bytes,
    descriptor: Descriptor,
    *,
    parser_version: str,
    parser_rule_hash: str,
    retrieved_at: dt.datetime,
) -> Dict[str, str]:
    """Compute the attestation block for upstream response bytes.

    Identical for every adapter: SHA-256 over response + descriptor
    hash + retrieved_at + the parser metadata. Yields a dict of
    string fields suitable for an `MPRRecord.attestation`.
    """
    return {
        "source_doi": str(descriptor.source.get("canonical_doi", "")),
        "source_url": str(descriptor.fetch.get("endpoint", descriptor.source.get("homepage", ""))),
        "license": str(descriptor.source["license"]),
        "retrieved_at": retrieved_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "response_sha256": sha256_bytes(raw),
        "parser_version": parser_version,
        "parser_rule_hash": parser_rule_hash,
        "collector_descriptor_path": str(descriptor.path.name),
        "collector_descriptor_hash": descriptor_hash(descriptor.path),
    }


def parser_rule_hash(parse_section: Mapping[str, Any]) -> str:
    """SHA-256 fingerprint of the descriptor's [parse] section.

    Documents which parsing rules produced a row's data block.
    Changes to the parse section invalidate every row's
    parser_rule_hash on next collection — explicit drift.
    """
    import json as _json

    canonical = _json.dumps(
        dict(parse_section), sort_keys=True, ensure_ascii=False
    ).encode("utf-8")
    # Route through sha256_bytes so the native C dispatch (Task #201
    # Phase B3) handles the hash when available. Pure-Python falls
    # back to hashlib transparently.
    return sha256_bytes(canonical)


# ──────────────────────────────────────────────────────────────────────
# The composer — descriptor → MPRRecord iterator
# ──────────────────────────────────────────────────────────────────────


def render_per_row(
    descriptor: Descriptor,
    *,
    retrieved_at: dt.datetime,
    data_schema_id: str,
    row_index: int,
) -> Dict[str, str]:
    """Build the rendering dict for one row using the descriptor's
    [rendering] templates.

    Context exposed to templates:
    * ``retrieved_at`` (datetime)
    * ``schema.regime_label`` (first regime in [gap_targeting]; "" if absent)
    * ``source.*`` (every field in the [source] table)
    * ``data_schema_id``
    * ``row_index``
    """
    context: Dict[str, Any] = {
        "retrieved_at": retrieved_at,
        "schema": {
            "regime_label": (
                descriptor.gap_targeting.get("regime_labels", [""])[0]
                if descriptor.gap_targeting else ""
            ),
        },
        "source": dict(descriptor.source),
        "data_schema_id": data_schema_id,
        "row_index": row_index,
    }
    cite_as = render_template(
        str(descriptor.rendering["cite_as_template"]), context
    )
    purpose = render_template(
        str(descriptor.rendering["purpose_template"]), context
    )
    name = render_template(
        str(descriptor.source["human_readable_name"]) + " — row {row_index}",
        context,
    )
    return {
        "human_readable_name": name,
        "cite_as": cite_as,
        "purpose": purpose,
    }


def run(
    descriptor: Descriptor,
    *,
    parser_version: str,
    retrieved_at: dt.datetime,
) -> Iterator[MPRRecord]:
    """Compose fetch → parse → attest → emit MPRRecords.

    The collector workflow + ad-hoc runs both call this. ``raw_iter``
    is materialised once (one upstream response per fetch call); the
    parse step then iterates rows from those bytes.

    Each row gets its own attestation block but the
    ``response_sha256`` is identical for all rows from the same
    upstream response — that's correct: those rows came from those
    bytes, and the hash documents that.
    """
    adapter = get_adapter(descriptor.adapter_name)
    rule_hash = parser_rule_hash(descriptor.parse)
    data_schema_id = str(descriptor.schema["data_schema_id"])

    row_index = 0
    for raw in adapter.fetch(descriptor):
        attestation = attest(
            raw,
            descriptor,
            parser_version=parser_version,
            parser_rule_hash=rule_hash,
            retrieved_at=retrieved_at,
        )
        for data in adapter.parse(raw, descriptor):
            row_index += 1
            rendering = render_per_row(
                descriptor,
                retrieved_at=retrieved_at,
                data_schema_id=data_schema_id,
                row_index=row_index,
            )
            yield MPRRecord(
                mpr_version=MPR_SCHEMA_VERSION,
                data=data,
                data_schema_id=data_schema_id,
                attestation=dict(attestation),
                rendering=rendering,
            )


__all__ = [
    "AdapterError",
    "AdapterProtocol",
    "ADAPTERS",
    "attest",
    "get_adapter",
    "parser_rule_hash",
    "register",
    "render_per_row",
    "run",
]
