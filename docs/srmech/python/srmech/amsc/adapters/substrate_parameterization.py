"""Substrate-parameterization adapter — catalog-driven substrate runs.

The first six adapters (``html_scraper``, ``json_api``, ``csv_bulk``,
``netcdf_grid``, ``geotiff_bbox``, ``literature_curated``) all answer the
question *"where do the ground-proof rows come from?"*. This seventh adapter
answers a different one: *"how is a parameterized substrate configured?"*.

A ``substrate_parameterization`` descriptor carries — under
``[fetch.substrate_parameterization.*]`` — the full parameter set that drives a
substrate characterization run (the RBS-LM variable-length Klein-4
chirality-level sentence substrate is the canonical consumer). Every former
module-level magic number (``D``, ``max_walk_length``, ``cycle_policy``,
plausibility weights, sweep ranges, …) lives in a nested sub-table so it is
attested catalog content, not script-embedded MVP magic
(``[[feedback_no_mvp_framing]]`` + user direction 2026-05-28). The catalog rode
the permissive ``literature_curated`` adapter as an interim home; this adapter
is the clean semantic match (UPSTREAM_NOTES §7).

What rc13 ships
---------------
* **Typed sub-dataclasses** — ``SubstrateParams``, ``EncodingParams``,
  ``GenerationParams``, ``HierarchicalParams``, ``CorpusParams`` (required) +
  ``GrammarParams``, ``PlausibilityParams``, ``MeasurementParams`` (optional),
  composed into a frozen ``SubstrateConfig``. First-class typed accessors
  (``cfg.substrate.D``) replace dict-navigation
  (``desc.fetch["literature_curated"]["substrate"]["D"]``).
* **``parse_substrate_config(params)``** — validates the called-out invariants
  (``D > 0``; ``cycle_policy ∈ {forbid, allow, count_limited}``;
  ``corpus.source`` / ``corpus.tokenizer`` enums; ``default_strategy`` is in
  ``allowed_strategies``; ``0 ≤ plausibility weight ≤ 1``; ``eps_smoothing >
  0``) and returns the typed ``SubstrateConfig``.
* **``config_for(descriptor)``** — extracts the right sub-table from
  ``descriptor.fetch`` (the ``substrate_parameterization`` key when present,
  else the legacy ``literature_curated`` key, else the ``fetch`` table itself)
  and parses it. Works for a migrated descriptor AND one still riding the
  legacy adapter.
* **``fetch`` / ``parse``** — the AMSC adapter protocol. ``fetch`` reads the
  committed ``[fetch].ndjson_path`` (the characterization measurement output,
  one MPR ``data`` block per line); ``parse`` decodes it line-by-line. These
  rows are *computed* measurement outputs attested by the descriptor +
  ``parser_rule_hash``, so (unlike ``literature_curated``) no per-row
  ``source_doi`` is required.

What lands later
----------------
The ``run_substrate_characterization`` operation that *consumes* a
``SubstrateConfig`` + a corpus source + a phase set and *produces* the
measurement NDJSON is the substrate-module port (UPSTREAM_NOTES §9 / rc14). This
adapter is the typed config layer it will sit on.

References
----------
* UPSTREAM_NOTES §7 — first-class ``substrate_parameterization`` adapter wishlist.
* ``srmech.amsc.adapters.literature_curated`` — the no-network sibling whose
  NDJSON-passthrough ``fetch``/``parse`` shape this adapter mirrors.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Mapping, Optional, Tuple

from ..descriptor import Descriptor
from . import _base

ADAPTER_NAME = "substrate_parameterization"

#: Required substrate sub-sections (a descriptor missing any of these is not a
#: valid substrate parameterization).
REQUIRED_SUBSECTIONS: Tuple[str, ...] = (
    "substrate",
    "encoding",
    "generation",
    "hierarchical",
    "corpus",
)

#: Optional substrate sub-sections (validated when present, absent → ``None``).
OPTIONAL_SUBSECTIONS: Tuple[str, ...] = (
    "grammar",
    "plausibility",
    "measurement",
)

#: Allowed enum values for the validated string fields.
_CYCLE_POLICIES: Tuple[str, ...] = ("forbid", "allow", "count_limited")
_CORPUS_SOURCES: Tuple[str, ...] = ("template", "hf_dataset", "file", "stdin")
_CORPUS_TOKENIZERS: Tuple[str, ...] = (
    "whitespace",
    "python_tokenize",
    "byte_level",
    "bpe",
)
_GRAMMAR_MODES: Tuple[str, ...] = ("pos_template", "substrate_native", "none")


class SubstrateConfigError(ValueError):
    """Raised when a substrate-parameterization config fails validation."""


# ──────────────────────────────────────────────────────────────────────
# Typed sub-dataclasses — first-class accessors replacing dict navigation
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SubstrateParams:
    """``[…substrate]`` — the hyperdimensional substrate geometry."""

    D: int
    sector_count: int
    min_skeleton_length: int
    token_seed_hex_chars: int


@dataclass(frozen=True)
class EncodingParams:
    """``[…encoding]`` — which encoder library + version produced the binds."""

    backend: str
    encoder_library: str
    encoder_version: str


@dataclass(frozen=True)
class GenerationParams:
    """``[…generation]`` — the bigram-walk / sentence-generation policy."""

    default_top_k: int
    max_walk_length: int
    max_paths: int
    cycle_policy: str
    l4_direct_composition: bool
    skeleton_length_fallback: Tuple[Any, ...]


@dataclass(frozen=True)
class HierarchicalParams:
    """``[…hierarchical]`` — the sentence-bucketing strategy."""

    n_buckets: int
    default_strategy: str
    allowed_strategies: Tuple[str, ...]
    sentence_hash_hex_chars: int


@dataclass(frozen=True)
class CorpusParams:
    """``[…corpus]`` — corpus source + tokenizer; nested sub-tables (e.g.
    ``corpus.template``) are preserved verbatim in ``extra``."""

    source: str
    tokenizer: str
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GrammarParams:
    """``[…grammar]`` (optional) — POS-template grammar; the per-length
    ``templates`` sub-table is preserved verbatim."""

    mode: str
    pos_source: str
    allow_multi_class_pos: bool
    templates: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlausibilityParams:
    """``[…plausibility]`` (optional) — the scoring blend; ``weights`` is a
    per-channel mapping, each validated to ``0 ≤ w ≤ 1``."""

    combination_mode: str
    eps_smoothing: float
    skip_distances: Tuple[int, ...]
    weights: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class MeasurementParams:
    """``[…measurement]`` (optional) — the characterization sweep protocol;
    nested ``*_sweep`` sub-tables are preserved verbatim in ``sweeps``."""

    recall_sample: int
    seed: int
    sweeps: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SubstrateConfig:
    """The full typed substrate parameterization parsed from a descriptor.

    The five required sections are always present; the three optional ones are
    ``None`` when the descriptor omits them.
    """

    substrate: SubstrateParams
    encoding: EncodingParams
    generation: GenerationParams
    hierarchical: HierarchicalParams
    corpus: CorpusParams
    grammar: Optional[GrammarParams] = None
    plausibility: Optional[PlausibilityParams] = None
    measurement: Optional[MeasurementParams] = None


# ──────────────────────────────────────────────────────────────────────
# Validation helpers — small, single-purpose, no abs() on the substrate
# ──────────────────────────────────────────────────────────────────────


def _section(params: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    sub = params.get(name)
    if not isinstance(sub, Mapping):
        raise SubstrateConfigError(
            f"[{name}] sub-section is required and must be a table; "
            f"got {type(sub).__name__}"
        )
    return sub


def _pos_int(sub: Mapping[str, Any], key: str, section: str) -> int:
    val = sub.get(key)
    if not isinstance(val, int) or isinstance(val, bool) or val <= 0:
        raise SubstrateConfigError(
            f"[{section}].{key} must be a positive int; got {val!r}"
        )
    return val


def _enum(sub: Mapping[str, Any], key: str, section: str,
          allowed: Tuple[str, ...]) -> str:
    val = sub.get(key)
    if val not in allowed:
        raise SubstrateConfigError(
            f"[{section}].{key} must be one of {allowed}; got {val!r}"
        )
    return str(val)


def _bool(sub: Mapping[str, Any], key: str, section: str,
          default: bool = False) -> bool:
    val = sub.get(key, default)
    if not isinstance(val, bool):
        raise SubstrateConfigError(
            f"[{section}].{key} must be a bool; got {val!r}"
        )
    return val


def _str(sub: Mapping[str, Any], key: str, section: str) -> str:
    val = sub.get(key)
    if not isinstance(val, str) or not val:
        raise SubstrateConfigError(
            f"[{section}].{key} must be a non-empty string; got {val!r}"
        )
    return val


# ──────────────────────────────────────────────────────────────────────
# Per-section parsers
# ──────────────────────────────────────────────────────────────────────


def _parse_substrate(params: Mapping[str, Any]) -> SubstrateParams:
    sub = _section(params, "substrate")
    return SubstrateParams(
        D=_pos_int(sub, "D", "substrate"),
        sector_count=_pos_int(sub, "sector_count", "substrate"),
        min_skeleton_length=_pos_int(
            sub, "min_skeleton_length", "substrate"
        ),
        token_seed_hex_chars=_pos_int(
            sub, "token_seed_hex_chars", "substrate"
        ),
    )


def _parse_encoding(params: Mapping[str, Any]) -> EncodingParams:
    sub = _section(params, "encoding")
    return EncodingParams(
        backend=_str(sub, "backend", "encoding"),
        encoder_library=_str(sub, "encoder_library", "encoding"),
        encoder_version=_str(sub, "encoder_version", "encoding"),
    )


def _parse_generation(params: Mapping[str, Any]) -> GenerationParams:
    sub = _section(params, "generation")
    fallback = sub.get("skeleton_length_fallback", [])
    if not isinstance(fallback, (list, tuple)):
        raise SubstrateConfigError(
            f"[generation].skeleton_length_fallback must be a list; "
            f"got {fallback!r}"
        )
    return GenerationParams(
        default_top_k=_pos_int(sub, "default_top_k", "generation"),
        max_walk_length=_pos_int(sub, "max_walk_length", "generation"),
        max_paths=_pos_int(sub, "max_paths", "generation"),
        cycle_policy=_enum(
            sub, "cycle_policy", "generation", _CYCLE_POLICIES
        ),
        l4_direct_composition=_bool(
            sub, "l4_direct_composition", "generation"
        ),
        skeleton_length_fallback=tuple(fallback),
    )


def _parse_hierarchical(params: Mapping[str, Any]) -> HierarchicalParams:
    sub = _section(params, "hierarchical")
    allowed = sub.get("allowed_strategies", [])
    if (not isinstance(allowed, (list, tuple)) or not allowed
            or not all(isinstance(s, str) for s in allowed)):
        raise SubstrateConfigError(
            f"[hierarchical].allowed_strategies must be a non-empty list "
            f"of strings; got {allowed!r}"
        )
    allowed_t = tuple(allowed)
    default_strategy = _enum(
        sub, "default_strategy", "hierarchical", allowed_t
    )
    return HierarchicalParams(
        n_buckets=_pos_int(sub, "n_buckets", "hierarchical"),
        default_strategy=default_strategy,
        allowed_strategies=allowed_t,
        sentence_hash_hex_chars=_pos_int(
            sub, "sentence_hash_hex_chars", "hierarchical"
        ),
    )


def _parse_corpus(params: Mapping[str, Any]) -> CorpusParams:
    sub = _section(params, "corpus")
    extra = {
        k: v for k, v in sub.items()
        if k not in ("source", "tokenizer")
    }
    return CorpusParams(
        source=_enum(sub, "source", "corpus", _CORPUS_SOURCES),
        tokenizer=_enum(sub, "tokenizer", "corpus", _CORPUS_TOKENIZERS),
        extra=extra,
    )


def _parse_grammar(params: Mapping[str, Any]) -> Optional[GrammarParams]:
    if "grammar" not in params:
        return None
    sub = _section(params, "grammar")
    return GrammarParams(
        mode=_enum(sub, "mode", "grammar", _GRAMMAR_MODES),
        pos_source=_str(sub, "pos_source", "grammar"),
        allow_multi_class_pos=_bool(
            sub, "allow_multi_class_pos", "grammar"
        ),
        templates=dict(sub.get("templates", {})),
    )


def _parse_plausibility(
    params: Mapping[str, Any],
) -> Optional[PlausibilityParams]:
    if "plausibility" not in params:
        return None
    sub = _section(params, "plausibility")
    eps = sub.get("eps_smoothing")
    if not isinstance(eps, (int, float)) or isinstance(eps, bool) or eps <= 0:
        raise SubstrateConfigError(
            f"[plausibility].eps_smoothing must be a positive number; "
            f"got {eps!r}"
        )
    weights = dict(sub.get("weights", {}))
    for name, w in weights.items():
        if (not isinstance(w, (int, float)) or isinstance(w, bool)
                or w < 0.0 or w > 1.0):
            raise SubstrateConfigError(
                f"[plausibility.weights].{name} must be in [0, 1]; "
                f"got {w!r}"
            )
    skips = sub.get("skip_distances", [])
    if (not isinstance(skips, (list, tuple))
            or not all(isinstance(s, int) and not isinstance(s, bool)
                       for s in skips)):
        raise SubstrateConfigError(
            f"[plausibility].skip_distances must be a list of ints; "
            f"got {skips!r}"
        )
    return PlausibilityParams(
        combination_mode=_str(sub, "combination_mode", "plausibility"),
        eps_smoothing=float(eps),
        skip_distances=tuple(skips),
        weights=weights,
    )


def _parse_measurement(
    params: Mapping[str, Any],
) -> Optional[MeasurementParams]:
    if "measurement" not in params:
        return None
    sub = _section(params, "measurement")
    seed = sub.get("seed", 0)
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise SubstrateConfigError(
            f"[measurement].seed must be a non-negative int; got {seed!r}"
        )
    sweeps = {
        k: v for k, v in sub.items()
        if k not in ("recall_sample", "seed")
    }
    return MeasurementParams(
        recall_sample=_pos_int(sub, "recall_sample", "measurement"),
        seed=seed,
        sweeps=sweeps,
    )


# ──────────────────────────────────────────────────────────────────────
# Public surface — parse + descriptor accessor
# ──────────────────────────────────────────────────────────────────────


def parse_substrate_config(params: Mapping[str, Any]) -> SubstrateConfig:
    """Validate ``params`` and return the typed :class:`SubstrateConfig`.

    ``params`` is the mapping that contains the substrate sub-sections
    (``substrate``, ``encoding``, …). :func:`config_for` extracts it from a
    loaded descriptor; pass it directly when validating an in-memory table.

    Raises
    ------
    SubstrateConfigError
        If a required sub-section is missing, or any validated invariant fails
        (``D > 0``; ``cycle_policy``/``corpus``/``grammar`` enums;
        ``default_strategy ∈ allowed_strategies``; ``0 ≤ weight ≤ 1``;
        ``eps_smoothing > 0``).
    """
    if not isinstance(params, Mapping):
        raise SubstrateConfigError(
            f"substrate params must be a table; got {type(params).__name__}"
        )
    missing = [s for s in REQUIRED_SUBSECTIONS if s not in params]
    if missing:
        raise SubstrateConfigError(
            f"missing required substrate sub-section(s): {missing}; "
            f"required: {list(REQUIRED_SUBSECTIONS)}"
        )
    return SubstrateConfig(
        substrate=_parse_substrate(params),
        encoding=_parse_encoding(params),
        generation=_parse_generation(params),
        hierarchical=_parse_hierarchical(params),
        corpus=_parse_corpus(params),
        grammar=_parse_grammar(params),
        plausibility=_parse_plausibility(params),
        measurement=_parse_measurement(params),
    )


def _substrate_params(descriptor: Descriptor) -> Mapping[str, Any]:
    """Locate the substrate sub-table inside ``descriptor.fetch``.

    Looks under the adapter-name key first (``substrate_parameterization``),
    then the legacy ``literature_curated`` key (the catalog's interim home),
    then the ``[fetch]`` table itself (params nested directly).
    """
    fetch = descriptor.fetch
    for key in (ADAPTER_NAME, "literature_curated"):
        nested = fetch.get(key)
        if isinstance(nested, Mapping) and any(
            s in nested for s in REQUIRED_SUBSECTIONS
        ):
            return nested
    return fetch


def config_for(descriptor: Descriptor) -> SubstrateConfig:
    """Parse the typed :class:`SubstrateConfig` from a loaded descriptor.

    The typed accessor that replaces dict-navigation: ``config_for(desc)``
    returns a :class:`SubstrateConfig` whose ``.substrate``, ``.generation``,
    … fields are typed sub-dataclasses.
    """
    return parse_substrate_config(_substrate_params(descriptor))


# ──────────────────────────────────────────────────────────────────────
# AMSC adapter protocol — NDJSON passthrough of computed measurement rows
# ──────────────────────────────────────────────────────────────────────


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    """Read the committed measurement NDJSON declared by the descriptor.

    Like ``literature_curated``, no network I/O: the descriptor's
    ``[fetch].ndjson_path`` is resolved relative to the descriptor's directory
    and yielded once (the whole measurement file is one "response" for
    attestation — ``response_sha256`` covers the entire NDJSON file).
    """
    rel_path = str(descriptor.fetch.get("ndjson_path", ""))
    if not rel_path:
        raise _base.AdapterError(
            f"substrate_parameterization: descriptor "
            f"{descriptor.path.name!r} is missing required "
            f"[fetch].ndjson_path"
        )
    target = descriptor.path.parent / rel_path
    if not target.is_file():
        raise _base.AdapterError(
            f"substrate_parameterization: NDJSON file not found at "
            f"{target!r}"
        )
    yield target.read_bytes()


def parse(
    raw: bytes, descriptor: Descriptor
) -> Iterator[Dict[str, Any]]:
    """Decode the measurement NDJSON line-by-line into per-row data dicts.

    Empty lines and ``#``-prefixed comment lines are skipped. Each remaining
    line is one characterization measurement (one MPR ``data`` block). These
    are *computed* outputs attested by the descriptor + ``parser_rule_hash``,
    so — unlike ``literature_curated`` — no per-row ``source_doi`` is required.
    """
    text = raw.decode("utf-8")
    for line_index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise _base.AdapterError(
                f"substrate_parameterization: NDJSON parse error at line "
                f"{line_index} in {descriptor.path.name!r}: {exc}"
            ) from exc
        if not isinstance(row, dict):
            raise _base.AdapterError(
                f"substrate_parameterization: NDJSON line {line_index} in "
                f"{descriptor.path.name!r} did not decode to an object "
                f"(got {type(row).__name__})"
            )
        yield row


_base.register(ADAPTER_NAME, sys.modules[__name__])

__all__ = [
    "ADAPTER_NAME",
    "REQUIRED_SUBSECTIONS",
    "OPTIONAL_SUBSECTIONS",
    "SubstrateConfigError",
    "SubstrateParams",
    "EncodingParams",
    "GenerationParams",
    "HierarchicalParams",
    "CorpusParams",
    "GrammarParams",
    "PlausibilityParams",
    "MeasurementParams",
    "SubstrateConfig",
    "parse_substrate_config",
    "config_for",
    "fetch",
    "parse",
]
