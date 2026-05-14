"""Source descriptors for the attested collector framework.

Each attested source is one TOML descriptor file under
``research/attested/<source>/descriptor.toml``. Adding a source is a
CONFIG change, not a CODE change — the collector framework's whole
escape from the v0.24.x hand-coding pattern.

A descriptor declares:

* ``[source]`` — identity (key, name, license, DOI, homepage).
* ``[fetch]`` — adapter selection + endpoint + pagination + rate-
  limit policy.
* ``[parse]`` — field map (canonical key → source-specific selector
  + type).
* ``[schema]`` — pointer to the per-source JSON Schema for the data
  block.
* ``[rendering]`` — self-describing verbiage templates (citation,
  purpose) so the program takes its language for describing rows
  from the descriptor itself, not from hard-coded code paths.
* ``[attestation]`` — provenance-block requirements (which hash
  algorithm, mandatory fields).
* ``[gap_targeting]`` — regime labels this source is relevant to.
  v0.25.0 just stores; v0.26.x consumes (schema-gap-driven trigger
  closes the MPM loop). Ratchet: every label declared here must
  exist in the regime classifier's roster.

References
----------
* Notebook §18.4 — full TOML descriptor schema sketch.
* `srmech.amsc.format` — sister module for the on-disk MPR record
  format (NDJSON).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore


# ──────────────────────────────────────────────────────────────────────
# Section + field requirements
# ──────────────────────────────────────────────────────────────────────


REQUIRED_TOP_LEVEL_SECTIONS: Tuple[str, ...] = (
    "source",
    "fetch",
    "parse",
    "schema",
    "rendering",
    "attestation",
)
"""Every descriptor must declare these top-level TOML tables. The
``[gap_targeting]`` table is optional in v0.25.0 (will become
mandatory in v0.26.x once the schema-gap-driven trigger consumes
it)."""

REQUIRED_SOURCE_FIELDS: Tuple[str, ...] = (
    "key",
    "human_readable_name",
    "purpose",
    "license",
    "homepage",
)
"""The ``[source]`` table must carry these. ``canonical_doi`` is
optional but strongly recommended for citable provenance."""

REQUIRED_FETCH_FIELDS: Tuple[str, ...] = ("adapter",)
"""The ``[fetch]`` table must declare which adapter handles it.
Other fields (endpoint, pagination, rate_limit_rps) are adapter-
specific and validated by the adapter's own schema."""

REQUIRED_RENDERING_FIELDS: Tuple[str, ...] = (
    "cite_as_template",
    "purpose_template",
)
"""Templates that produce per-row rendering verbiage. Substituted
at attestation time using `render_template`."""

KNOWN_ADAPTERS: Tuple[str, ...] = (
    "html_scraper",
    "json_api",
    "csv_bulk",
    "netcdf_grid",
    "geotiff_bbox",
    "literature_curated",
)
"""Adapter categories. The first five shipped in v0.25.0. The sixth
(``literature_curated``) shipped after v0.26.0 to support per-body
catalogues whose ground-proof rows come from peer-reviewed
literature with stable DOIs rather than from a live archive (no
network fetch; NDJSON committed directly; per-row ``source_doi``
mandatory in each row's data block). New adapter types require a
new module under ``srmech/amsc/adapters/`` + entry here."""


# ──────────────────────────────────────────────────────────────────────
# In-memory representation
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Descriptor:
    """Parsed source descriptor.

    Sub-tables are stored as plain dicts because their internal
    structure varies per-adapter; the framework only enforces the
    top-level invariants.
    """

    path: Path
    source: Dict[str, Any]
    fetch: Dict[str, Any]
    parse: Dict[str, Any]
    schema: Dict[str, Any]
    rendering: Dict[str, Any]
    attestation: Dict[str, Any]
    gap_targeting: Dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return str(self.source["key"])

    @property
    def adapter_name(self) -> str:
        return str(self.fetch["adapter"])

    def to_dict(self) -> Dict[str, Any]:
        """Materialise the parsed descriptor as a plain dict, used
        by ``bridge.get_attested_descriptor`` to surface descriptor
        contents to consumers."""
        return {
            "source": dict(self.source),
            "fetch": dict(self.fetch),
            "parse": dict(self.parse),
            "schema": dict(self.schema),
            "rendering": dict(self.rendering),
            "attestation": dict(self.attestation),
            "gap_targeting": dict(self.gap_targeting),
        }


class DescriptorValidationError(ValueError):
    """Raised when a descriptor TOML fails the v0.25.0 schema."""


# ──────────────────────────────────────────────────────────────────────
# Loading + validating
# ──────────────────────────────────────────────────────────────────────


def load_descriptor(
    path: Path,
    *,
    valid_regime_labels: Optional[Mapping[str, Any]] = None,
) -> Descriptor:
    """Parse and validate a descriptor TOML file.

    Parameters
    ----------
    path
        Path to ``descriptor.toml``.
    valid_regime_labels
        Optional set/dict of valid regime labels (e.g. the keys of
        the dynamical-regime classifier's known regimes). When
        provided, every label in ``[gap_targeting].regime_labels``
        is checked against it. When None, gap-targeting labels are
        accepted as-is (codegen-time validation only).

    Returns
    -------
    Descriptor

    Raises
    ------
    DescriptorValidationError
        If any required structure or field is missing.
    """
    if not path.exists():
        raise DescriptorValidationError(
            f"descriptor file not found: {path}"
        )

    raw = path.read_bytes()
    try:
        parsed = tomllib.loads(raw.decode("utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise DescriptorValidationError(
            f"{path}: TOML parse error: {exc}"
        ) from exc

    for section in REQUIRED_TOP_LEVEL_SECTIONS:
        if section not in parsed:
            raise DescriptorValidationError(
                f"{path}: missing required section [{section}]"
            )

    source = parsed["source"]
    for field_name in REQUIRED_SOURCE_FIELDS:
        if field_name not in source or not source[field_name]:
            raise DescriptorValidationError(
                f"{path}: [source].{field_name} is required"
            )

    fetch = parsed["fetch"]
    for field_name in REQUIRED_FETCH_FIELDS:
        if field_name not in fetch or not fetch[field_name]:
            raise DescriptorValidationError(
                f"{path}: [fetch].{field_name} is required"
            )
    if fetch["adapter"] not in KNOWN_ADAPTERS:
        raise DescriptorValidationError(
            f"{path}: unknown adapter {fetch['adapter']!r}; "
            f"known: {KNOWN_ADAPTERS}"
        )

    rendering = parsed["rendering"]
    for field_name in REQUIRED_RENDERING_FIELDS:
        if field_name not in rendering or not rendering[field_name]:
            raise DescriptorValidationError(
                f"{path}: [rendering].{field_name} is required"
            )

    gap_targeting = dict(parsed.get("gap_targeting", {}))
    if valid_regime_labels is not None and gap_targeting:
        labels: List[str] = list(gap_targeting.get("regime_labels", []))
        unknown = [
            lab for lab in labels if lab not in valid_regime_labels
        ]
        if unknown:
            raise DescriptorValidationError(
                f"{path}: [gap_targeting].regime_labels contains "
                f"unknown labels {unknown}"
            )

    return Descriptor(
        path=path,
        source=dict(source),
        fetch=dict(fetch),
        parse=dict(parsed["parse"]),
        schema=dict(parsed["schema"]),
        rendering=dict(rendering),
        attestation=dict(parsed["attestation"]),
        gap_targeting=gap_targeting,
    )


# ──────────────────────────────────────────────────────────────────────
# Template rendering — the self-describing verbiage step
# ──────────────────────────────────────────────────────────────────────


_TEMPLATE_PATTERN = re.compile(r"\{([a-zA-Z0-9_.:%\-+ ]+)\}")
"""Match ``{key}`` and ``{key:fmt}`` substitutions in templates.
Deliberately minimal — no Jinja, no expression evaluation, just
named-substitution + Python format-spec for datetime fields."""


def render_template(template: str, context: Mapping[str, Any]) -> str:
    """Substitute ``{key}`` and ``{key:fmt}`` placeholders in a
    template string.

    Used to render ``cite_as_template`` and ``purpose_template``
    from the descriptor's ``[rendering]`` block at attestation
    time.

    Examples
    --------
    >>> render_template(
    ...     "retrieved {retrieved_at:%Y-%m-%d}",
    ...     {"retrieved_at": dt.datetime(2026, 5, 8)}
    ... )
    'retrieved 2026-05-08'
    """

    def _replace(match: "re.Match[str]") -> str:
        spec = match.group(1)
        if ":" in spec:
            key, fmt = spec.split(":", 1)
        else:
            key, fmt = spec, ""
        # Resolve dotted paths.
        cursor: Any = context
        for part in key.split("."):
            if isinstance(cursor, Mapping):
                cursor = cursor.get(part, "")
            else:
                cursor = getattr(cursor, part, "")
        if fmt:
            try:
                return format(cursor, fmt)
            except (TypeError, ValueError):
                return str(cursor)
        return str(cursor)

    return _TEMPLATE_PATTERN.sub(_replace, template)


# ──────────────────────────────────────────────────────────────────────
# Descriptor hash — canonical-serialised TOML
# ──────────────────────────────────────────────────────────────────────


def descriptor_hash(path: Path) -> str:
    """SHA-256 over the canonical-serialised content of a descriptor.

    Hashes the *parsed* dict (re-emitted as JSON with sort_keys=True),
    not the raw TOML bytes. This insulates the hash from whitespace
    / comment / key-ordering changes in the committed TOML — the
    hash documents the *logical content* of the descriptor, so the
    attestation block remains valid across cosmetic edits.

    Used by adapters' ``attest()`` step to populate the per-row
    ``collector_descriptor_hash`` attestation field.

    Task #201 Phase B5: the canonical-serialisation step stays in
    Python (TOML parsing + ``json.dumps(sort_keys=True)`` is small
    and already C-accelerated inside CPython's json module). The
    final SHA-256 routes through ``sha256_bytes`` which dispatches
    to the native C implementation when available.
    """
    from .format import sha256_bytes  # local import; avoids cycle
    parsed = tomllib.loads(path.read_bytes().decode("utf-8"))
    canonical = json.dumps(
        parsed, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(canonical)


# ──────────────────────────────────────────────────────────────────────
# Discovery — walk research/attested/ for descriptors
# ──────────────────────────────────────────────────────────────────────


def discover_descriptors(
    attested_root: Path,
    *,
    valid_regime_labels: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Descriptor]:
    """Walk ``attested_root`` for ``<source>/descriptor.toml`` files
    and return a mapping ``source_key -> Descriptor``.

    Skips any subdirectory that doesn't have a ``descriptor.toml``
    (e.g. ``__init__.py``-only marker directories).

    Raises
    ------
    DescriptorValidationError
        If two descriptors share the same ``source.key``.
    """
    found: Dict[str, Descriptor] = {}
    if not attested_root.exists():
        return found
    for child in sorted(attested_root.iterdir()):
        if not child.is_dir():
            continue
        descriptor_path = child / "descriptor.toml"
        if not descriptor_path.exists():
            continue
        descriptor = load_descriptor(
            descriptor_path,
            valid_regime_labels=valid_regime_labels,
        )
        if descriptor.key in found:
            raise DescriptorValidationError(
                f"duplicate source.key {descriptor.key!r} at "
                f"{descriptor_path} and {found[descriptor.key].path}"
            )
        found[descriptor.key] = descriptor
    return found


__all__ = [
    "REQUIRED_TOP_LEVEL_SECTIONS",
    "REQUIRED_SOURCE_FIELDS",
    "REQUIRED_FETCH_FIELDS",
    "REQUIRED_RENDERING_FIELDS",
    "KNOWN_ADAPTERS",
    "Descriptor",
    "DescriptorValidationError",
    "load_descriptor",
    "render_template",
    "descriptor_hash",
    "discover_descriptors",
]
