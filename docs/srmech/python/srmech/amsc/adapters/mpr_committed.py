"""MPR-committed adapter — the NDJSON on disk is ALREADY the attestation
of record, so nothing is synthesised at read time.

**Why this adapter exists, stated as the defect it closes.** srmech has two
committed-NDJSON shapes and, until v0.9.0rc418, only one adapter name for
them:

* the **data-only curator shape** (``literature_curated``) — one row's
  ``data`` block per line, no attestation, no rendering. srmech
  SYNTHESISES the full MPR at read time from the descriptor's metadata plus
  the row's own per-row DOI. Nothing true is discarded because nothing
  attestation-shaped was ever committed.
* the **committed-envelope shape** (this adapter) — each line is a whole
  MPR v1 record: ``mpr_version`` + ``data`` + ``data_schema_id`` +
  ``attestation`` + ``rendering``, exactly what a live-fetcher adapter's
  ``_base.run()`` emits. The attestation on disk is REAL: its
  ``response_sha256`` is the hash of the verbatim upstream response the row
  captured, its ``retrieved_at`` is when that response was taken, its
  ``parser_version`` names the srmech build that wrote it.

Declaring the second shape as ``literature_curated`` is not a cosmetic
mislabel. The curated reader would take the whole envelope as the row's
``data`` block, find no top-level ``source_doi``, and either raise or
manufacture a fresh attestation whose ``response_sha256`` is a hash of the
row's own JSON rather than of the upstream response — **synthesising over a
true value**, which is the read-side mirror of the write-side defect
``#T1108`` exists to close. ``srmech/amsc/attested/genetic_code`` was
declared that way and consequently RAISED from
:func:`srmech.amsc.catalog.get_attested_dataset` while
:func:`~srmech.amsc.catalog.attestation_audit` reported it correctly only
because the audit happened to bypass the adapter dispatch entirely.

**What the adapter does, and what it deliberately does not do.**

* ``fetch`` does no network I/O — it reads the committed
  ``[fetch].ndjson_path`` and yields its bytes verbatim, exactly like
  ``literature_curated``'s.
* ``parse`` decodes each non-comment line and requires it to be a
  well-formed MPR v1 envelope. It **yields the whole envelope**, not a
  ``data`` block, because the envelope IS the record. The catalog reader
  (:func:`srmech.amsc.catalog._iter_records_for_descriptor`) reads this
  shape through :func:`srmech.amsc.format.read_ndjson`, which validates it
  against the MPR v1 schema; ``parse`` here is the adapter-protocol peer
  for callers that go through ``_base.run()``.
* There is **no attestation synthesis**. That is the whole point: a
  committed envelope's attestation is the attestation of record and is
  passed through unaltered. Compare
  :func:`srmech.amsc.catalog._iter_literature_curated_records`, which
  synthesises nine fields.

T1 CI re-bake does not apply — there is no live upstream to refresh from.
A row is amended by a curator PR that also updates the row's own
``attestation`` (including ``response_sha256`` over the new response
bytes), which is precisely the property that makes the amendment
re-verifiable.

References
----------
* Notebook §18.4 — descriptor TOML schema (``[fetch].adapter``).
* ``srmech.amsc.adapters.literature_curated`` — the data-only sibling this
  adapter is the envelope-shaped peer of.
* ADR-0009 — the two projections are co-equal; the C ``attestation_audit``
  peer reads the same two shapes through the same dispatch.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Iterator

from ..descriptor import Descriptor
from . import _base
from srmech import _json as _srmech_json

ADAPTER_NAME = "mpr_committed"

#: The five MPR v1 envelope keys every committed row must carry. Checked by
#: :func:`parse` so a data-only row declared under this adapter fails LOUDLY
#: at the adapter boundary rather than reaching the reader as an envelope
#: with an empty attestation.
_ENVELOPE_KEYS = ("mpr_version", "data", "data_schema_id", "attestation")


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    """Read the committed NDJSON file declared by the descriptor.

    ``[fetch].ndjson_path`` is resolved relative to the descriptor's own
    directory. Yields the file's bytes once. No network I/O — the rows were
    attested when they were committed, not when they are read.
    """
    rel_path = str(descriptor.fetch.get("ndjson_path", ""))
    if not rel_path:
        raise _base.AdapterError(
            f"mpr_committed: descriptor {descriptor.path.name!r} is missing "
            f"required [fetch].ndjson_path"
        )
    target = descriptor.path.parent / rel_path
    if not target.is_file():
        raise _base.AdapterError(
            f"mpr_committed: NDJSON file not found at {str(target)!r}"
        )
    yield target.read_bytes()


def parse(raw: bytes, descriptor: Descriptor) -> Iterator[Dict[str, Any]]:
    """Decode NDJSON bytes line-by-line into whole MPR v1 envelopes.

    Empty lines and lines starting with ``#`` are skipped (curator
    commentary). Every remaining line must decode to an object carrying the
    four structural MPR keys and a NON-EMPTY ``attestation`` object — a
    row committed under this adapter that carries no attestation is a
    declaration error, not a row to be quietly patched up, because the
    adapter's entire contract is *"the attestation is already here"*.
    """
    text = raw.decode("utf-8")
    for line_index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            row = _srmech_json.loads(stripped)
        except _srmech_json.JSONDecodeError as exc:
            raise _base.AdapterError(
                f"mpr_committed: NDJSON parse error at line {line_index} in "
                f"{descriptor.path.name!r}: {exc}"
            ) from exc
        if not isinstance(row, dict):
            raise _base.AdapterError(
                f"mpr_committed: NDJSON line {line_index} in "
                f"{descriptor.path.name!r} did not decode to an object "
                f"(got {type(row).__name__})"
            )
        missing = [k for k in _ENVELOPE_KEYS if k not in row]
        if missing:
            raise _base.AdapterError(
                f"mpr_committed: row at line {line_index} in "
                f"{descriptor.path.name!r} is not an MPR v1 envelope — "
                f"missing {missing!r}. This adapter is for NDJSON whose rows "
                f"are already whole MPR records; for data-only curator rows "
                f"use the literature_curated adapter, which synthesises the "
                f"attestation at read time"
            )
        attestation = row.get("attestation")
        if not isinstance(attestation, dict) or not attestation:
            raise _base.AdapterError(
                f"mpr_committed: row at line {line_index} in "
                f"{descriptor.path.name!r} has an empty or non-object "
                f"'attestation'. The adapter's contract is that the committed "
                f"attestation IS the attestation of record; there is nothing "
                f"here to preserve"
            )
        yield row


_base.register(ADAPTER_NAME, sys.modules[__name__])

__all__ = ["ADAPTER_NAME", "fetch", "parse"]
