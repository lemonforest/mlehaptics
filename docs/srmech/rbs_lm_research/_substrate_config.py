"""_substrate_config — Catalog-driven substrate configuration loader.

Reads an AMSC catalog descriptor (TOML) and returns a typed config object
that the substrate module + downstream scripts consume in place of
module-level magic numbers.

Per [[feedback_no_mvp_framing]] + [[feedback_full_coverage_shipping_mpm_way]]:
parameters live in the attested catalog descriptor, not in scripts.

Per AMSC MPM (docs/srmech/CLAUDE.md §MPM): catalog entries carry attestation
via descriptor_hash; same descriptor + same corpus + same srmech_version
yields bit-exact reproducible substrate measurements.

Canonical catalog: docs/srmech/catalogs/rbs_lm_substrate/descriptor.toml
"""
from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]


CANONICAL_CATALOG_PATH = (
    Path(__file__).parent.parent / "catalogs" / "rbs_lm_substrate" / "descriptor.toml"
)


@dataclass(frozen=True)
class SubstrateParams:
    D: int
    sector_count: int
    min_skeleton_length: int
    token_seed_hex_chars: int


@dataclass(frozen=True)
class EncodingParams:
    backend: str
    encoder_module: str
    encoder_version: str


@dataclass(frozen=True)
class GenerationParams:
    default_top_k: int
    max_walk_length: int
    max_paths: int
    cycle_policy: str  # "forbid" | "allow" | "count_limited"
    l4_direct_composition: bool
    skeleton_length_fallback: tuple[int, ...]


@dataclass(frozen=True)
class HierarchicalParams:
    n_buckets: int
    default_strategy: str
    allowed_strategies: tuple[str, ...]
    sentence_hash_hex_chars: int


@dataclass(frozen=True)
class CorpusParams:
    source: str  # "template" | "hf_dataset" | "file" | "stdin"
    tokenizer: str  # "whitespace" | "python_tokenize" | "byte_level" | "bpe"
    template_module: str | None
    template_distribution: dict[str, float] | None
    hf_dataset: str | None
    hf_split: str | None
    hf_language: str | None
    file_path: str | None


@dataclass(frozen=True)
class GrammarParams:
    mode: str  # "pos_template" | "substrate_native" | "none"
    pos_source: str
    allow_multi_class_pos: bool
    templates: dict[int, tuple[str, ...]]  # length → POS template


@dataclass(frozen=True)
class PlausibilityParams:
    combination_mode: str
    eps_smoothing: float
    skip_distances: tuple[int, ...]
    weights: dict[str, float]


@dataclass(frozen=True)
class MeasurementParams:
    recall_sample: int | str  # int or "full"
    seed: int
    length_sweep: tuple[int, ...]
    length_n_per: int
    corpus_sweep: tuple[int, ...]
    dimension_sweep: tuple[int, ...]
    dimension_fixed_n: int
    bucket_sweep: tuple[int, ...]
    top_k_sweep: tuple[int, ...]
    perturbation_categories: tuple[str, ...]
    weight_sensitivity_configs: dict[str, dict[str, float]]


@dataclass(frozen=True)
class SubstrateConfig:
    """Top-level catalog-driven substrate configuration.

    Carries a descriptor_hash for AMSC attestation: this hash identifies the
    exact parameter set in measurement output, so reruns can be diffed.
    """

    descriptor_path: Path
    descriptor_hash: str
    source_key: str
    substrate: SubstrateParams
    encoding: EncodingParams
    generation: GenerationParams
    hierarchical: HierarchicalParams
    corpus: CorpusParams
    grammar: GrammarParams
    plausibility: PlausibilityParams
    measurement: MeasurementParams
    raw_descriptor: dict[str, Any] = field(repr=False, compare=False)


def _descriptor_hash(descriptor_bytes: bytes) -> str:
    return hashlib.sha256(descriptor_bytes).hexdigest()


def _coerce_skeleton_fallback(raw: list[Any] | None) -> tuple[int, ...]:
    if raw is None:
        return ()
    return tuple(int(v) for v in raw)


def _parse_grammar_templates(raw: dict[str, list[str]] | None) -> dict[int, tuple[str, ...]]:
    if not raw:
        return {}
    parsed: dict[int, tuple[str, ...]] = {}
    for key, slots in raw.items():
        # Catalog keys are TOML strings like "L4"; parse the integer length out
        if isinstance(key, str) and key.upper().startswith("L"):
            length = int(key[1:])
        else:
            length = int(key)
        parsed[length] = tuple(slots)
    return parsed


def load_substrate_config(
    descriptor_path: Path | str | None = None,
) -> SubstrateConfig:
    """Load substrate config from an AMSC catalog descriptor.

    Args:
        descriptor_path: Path to descriptor.toml. If None, uses the canonical
            catalog at docs/srmech/catalogs/rbs_lm_substrate/descriptor.toml.

    Returns:
        SubstrateConfig with all substrate, encoding, generation, hierarchical,
        corpus, grammar, plausibility, and measurement parameters resolved.
    """
    path = Path(descriptor_path) if descriptor_path else CANONICAL_CATALOG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Substrate catalog not found at {path}")

    raw_bytes = path.read_bytes()
    descriptor = tomllib.loads(raw_bytes.decode("utf-8"))

    src = descriptor.get("source", {})
    sub = descriptor.get("substrate", {})
    enc = descriptor.get("encoding", {})
    gen = descriptor.get("generation", {})
    hier = descriptor.get("hierarchical", {})
    corp = descriptor.get("corpus", {})
    tpl_section = corp.get("template", {})
    hf_section = corp.get("hf_dataset", {})
    file_section = corp.get("file", {})
    gram = descriptor.get("grammar", {})
    gram_templates_raw = gram.get("templates", {})
    plaus = descriptor.get("plausibility", {})
    plaus_weights = plaus.get("weights", {})
    meas = descriptor.get("measurement", {})
    meas_lengths = meas.get("length_sweep", {})
    meas_corpus = meas.get("corpus_sweep", {})
    meas_dims = meas.get("dimension_sweep", {})
    meas_buckets = meas.get("bucket_sweep", {})
    meas_topk = meas.get("top_k_sweep", {})
    meas_perts = meas.get("perturbation_categories", {})
    meas_wsens = meas.get("weight_sensitivity_configs", {})

    config = SubstrateConfig(
        descriptor_path=path,
        descriptor_hash=_descriptor_hash(raw_bytes),
        source_key=str(src.get("key", "unknown")),
        substrate=SubstrateParams(
            D=int(sub["D"]),
            sector_count=int(sub["sector_count"]),
            min_skeleton_length=int(sub["min_skeleton_length"]),
            token_seed_hex_chars=int(sub["token_seed_hex_chars"]),
        ),
        encoding=EncodingParams(
            backend=str(enc.get("backend", "klein4")),
            encoder_module=str(enc.get("encoder_module", "vl_memory")),
            encoder_version=str(enc.get("encoder_version", "0.1.0")),
        ),
        generation=GenerationParams(
            default_top_k=int(gen["default_top_k"]),
            max_walk_length=int(gen["max_walk_length"]),
            max_paths=int(gen["max_paths"]),
            cycle_policy=str(gen["cycle_policy"]),
            l4_direct_composition=bool(gen.get("l4_direct_composition", False)),
            skeleton_length_fallback=_coerce_skeleton_fallback(gen.get("skeleton_length_fallback")),
        ),
        hierarchical=HierarchicalParams(
            n_buckets=int(hier["n_buckets"]),
            default_strategy=str(hier["default_strategy"]),
            allowed_strategies=tuple(hier.get("allowed_strategies", ["hash"])),
            sentence_hash_hex_chars=int(hier.get("sentence_hash_hex_chars", 8)),
        ),
        corpus=CorpusParams(
            source=str(corp.get("source", "template")),
            tokenizer=str(corp.get("tokenizer", "whitespace")),
            template_module=str(tpl_section.get("module")) if tpl_section.get("module") else None,
            template_distribution=(
                {str(k): float(v) for k, v in tpl_section.get("default_distribution", {}).items()}
                if tpl_section.get("default_distribution")
                else None
            ),
            hf_dataset=hf_section.get("name"),
            hf_split=hf_section.get("split"),
            hf_language=hf_section.get("language"),
            file_path=file_section.get("path"),
        ),
        grammar=GrammarParams(
            mode=str(gram.get("mode", "pos_template")),
            pos_source=str(gram.get("pos_source", "vocab_categories")),
            allow_multi_class_pos=bool(gram.get("allow_multi_class_pos", True)),
            templates=_parse_grammar_templates(gram_templates_raw),
        ),
        plausibility=PlausibilityParams(
            combination_mode=str(plaus.get("combination_mode", "weighted_geometric_mean")),
            eps_smoothing=float(plaus.get("eps_smoothing", 1e-6)),
            skip_distances=tuple(int(d) for d in plaus.get("skip_distances", [2, 3])),
            weights={
                str(k): float(v) for k, v in plaus_weights.items()
            },
        ),
        measurement=MeasurementParams(
            recall_sample=meas.get("recall_sample", "full"),
            seed=int(meas.get("seed", 42)),
            length_sweep=tuple(int(x) for x in meas_lengths.get("values", [])),
            length_n_per=int(meas_lengths.get("n_per_length", 50)),
            corpus_sweep=tuple(int(x) for x in meas_corpus.get("values", [])),
            dimension_sweep=tuple(int(x) for x in meas_dims.get("values", [])),
            dimension_fixed_n=int(meas_dims.get("fixed_n", 2000)),
            bucket_sweep=tuple(int(x) for x in meas_buckets.get("values", [])),
            top_k_sweep=tuple(int(x) for x in meas_topk.get("values", [])),
            perturbation_categories=tuple(str(c) for c in meas_perts.get("values", [])),
            weight_sensitivity_configs={
                str(name): {str(k): float(v) for k, v in cfg.items()}
                for name, cfg in meas_wsens.items()
            },
        ),
        raw_descriptor=descriptor,
    )
    return config


def attestation_block(config: SubstrateConfig) -> dict[str, Any]:
    """Return AMSC-style attestation block for measurement output.

    This goes into every measurement record so reruns can be diffed
    against the catalog parameter set that produced them.
    """
    return {
        "descriptor_path": str(config.descriptor_path),
        "descriptor_hash": config.descriptor_hash,
        "source_key": config.source_key,
        "substrate_D": config.substrate.D,
        "substrate_sector_count": config.substrate.sector_count,
        "generation_max_walk_length": config.generation.max_walk_length,
        "generation_max_paths": config.generation.max_paths,
        "grammar_mode": config.grammar.mode,
        "corpus_source": config.corpus.source,
        "corpus_tokenizer": config.corpus.tokenizer,
    }
