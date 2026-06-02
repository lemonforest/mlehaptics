"""v0.7.0rc13 — the ``substrate_parameterization`` adapter + typed config.

Lands UPSTREAM_NOTES §7: a first-class adapter for catalog-driven substrate
runs, with typed sub-dataclasses (``SubstrateConfig`` + per-section dataclasses)
replacing dict-navigation, and the validation the substrate parameter set
earns (``D > 0``; ``cycle_policy`` / ``corpus`` / ``grammar`` enums;
``default_strategy ∈ allowed_strategies``; ``0 ≤ plausibility weight ≤ 1``).

The substrate-module port + ``run_substrate_characterization`` op (UPSTREAM_NOTES
§9) is rc14; this rc ships the typed config layer it will sit on.
"""
import textwrap

import pytest

from srmech.amsc import descriptor as descriptor_mod
from srmech.amsc.adapters import _base, substrate_parameterization as sp


# ── a minimal but complete valid parameter set (mirrors the canonical catalog)
def _valid_params():
    return {
        "substrate": {
            "D": 8192,
            "sector_count": 4,
            "min_skeleton_length": 4,
            "token_seed_hex_chars": 8,
        },
        "encoding": {
            "backend": "klein4",
            "encoder_library": "_canonical_substrate.py",
            "encoder_version": "0.1.0",
        },
        "generation": {
            "default_top_k": 5,
            "max_walk_length": 30,
            "max_paths": 100,
            "cycle_policy": "forbid",
            "l4_direct_composition": False,
            "skeleton_length_fallback": [],
        },
        "hierarchical": {
            "n_buckets": 16,
            "default_strategy": "hash",
            "allowed_strategies": ["hash", "first_bigram_hash", "sector_then_hash"],
            "sentence_hash_hex_chars": 8,
        },
        "corpus": {
            "source": "template",
            "tokenizer": "whitespace",
            "template": {"module": "x.py", "default_distribution": {"L4": 0.25}},
        },
        "grammar": {
            "mode": "pos_template",
            "pos_source": "vocab_categories",
            "allow_multi_class_pos": True,
            "templates": {"L4": ["DET", "SUBJ", "VERB", "OBJ"]},
        },
        "plausibility": {
            "combination_mode": "weighted_geometric_mean",
            "eps_smoothing": 1e-6,
            "skip_distances": [2, 3],
            "weights": {"bigram_freq": 0.4, "skip_gram": 0.2, "token_known": 0.1},
        },
        "measurement": {
            "recall_sample": 500,
            "seed": 42,
            "length_sweep": {"values": [2, 3, 4], "n_per_length": 50},
        },
    }


# ── KNOWN_ADAPTERS + registration ─────────────────────────────────────────
def test_substrate_parameterization_in_known_adapters():
    assert "substrate_parameterization" in descriptor_mod.KNOWN_ADAPTERS


def test_adapter_registered_and_resolvable():
    mod = _base.get_adapter("substrate_parameterization")
    assert mod.ADAPTER_NAME == "substrate_parameterization"
    assert mod is sp


# ── parse_substrate_config — typed happy path ─────────────────────────────
def test_parse_substrate_config_typed_fields():
    cfg = sp.parse_substrate_config(_valid_params())
    assert cfg.substrate.D == 8192
    assert cfg.substrate.sector_count == 4
    assert cfg.generation.cycle_policy == "forbid"
    assert cfg.generation.l4_direct_composition is False
    assert cfg.generation.skeleton_length_fallback == ()
    assert cfg.hierarchical.default_strategy == "hash"
    assert cfg.corpus.source == "template"
    assert cfg.corpus.tokenizer == "whitespace"
    # nested sub-tables preserved verbatim under the section's catch-all
    assert cfg.corpus.extra["template"]["default_distribution"] == {"L4": 0.25}
    assert cfg.grammar is not None and cfg.grammar.mode == "pos_template"
    assert cfg.plausibility is not None
    assert cfg.plausibility.weights["bigram_freq"] == 0.4
    assert cfg.measurement is not None and cfg.measurement.recall_sample == 500
    assert "length_sweep" in cfg.measurement.sweeps


def test_optional_sections_absent_are_none():
    params = _valid_params()
    del params["grammar"]
    del params["plausibility"]
    del params["measurement"]
    cfg = sp.parse_substrate_config(params)
    assert cfg.grammar is None
    assert cfg.plausibility is None
    assert cfg.measurement is None
    # required sections still present
    assert cfg.substrate.D == 8192


# ── validation guards ─────────────────────────────────────────────────────
def test_missing_required_subsection_rejected():
    params = _valid_params()
    del params["encoding"]
    with pytest.raises(sp.SubstrateConfigError, match="encoding"):
        sp.parse_substrate_config(params)


def test_non_positive_D_rejected():
    params = _valid_params()
    params["substrate"]["D"] = 0
    with pytest.raises(sp.SubstrateConfigError, match=r"\[substrate\].D"):
        sp.parse_substrate_config(params)


def test_bool_is_not_a_positive_int():
    params = _valid_params()
    params["substrate"]["D"] = True  # bool must not pass the int gate
    with pytest.raises(sp.SubstrateConfigError):
        sp.parse_substrate_config(params)


def test_bad_cycle_policy_rejected():
    params = _valid_params()
    params["generation"]["cycle_policy"] = "sometimes"
    with pytest.raises(sp.SubstrateConfigError, match="cycle_policy"):
        sp.parse_substrate_config(params)


def test_default_strategy_must_be_in_allowed():
    params = _valid_params()
    params["hierarchical"]["default_strategy"] = "not_listed"
    with pytest.raises(sp.SubstrateConfigError, match="default_strategy"):
        sp.parse_substrate_config(params)


def test_bad_corpus_source_rejected():
    params = _valid_params()
    params["corpus"]["source"] = "carrier_pigeon"
    with pytest.raises(sp.SubstrateConfigError, match="corpus"):
        sp.parse_substrate_config(params)


def test_plausibility_weight_out_of_range_rejected():
    params = _valid_params()
    params["plausibility"]["weights"]["bigram_freq"] = 1.5
    with pytest.raises(sp.SubstrateConfigError, match=r"weights"):
        sp.parse_substrate_config(params)


def test_non_positive_eps_smoothing_rejected():
    params = _valid_params()
    params["plausibility"]["eps_smoothing"] = 0.0
    with pytest.raises(sp.SubstrateConfigError, match="eps_smoothing"):
        sp.parse_substrate_config(params)


def test_non_mapping_params_rejected():
    with pytest.raises(sp.SubstrateConfigError):
        sp.parse_substrate_config(["not", "a", "table"])  # type: ignore[arg-type]


# ── config_for(descriptor) — new nesting + legacy nesting ─────────────────
def _write_descriptor(tmp_path, adapter_key, *, with_ndjson=False):
    """Write a complete descriptor.toml with substrate params nested under
    [fetch.<adapter_key>.*]; returns the directory."""
    d = tmp_path / "cat"
    d.mkdir()
    ndjson_line = ""
    if with_ndjson:
        (d / "m.ndjson").write_text(
            '{"phase": 1, "metric": "recall", "value": 1.0}\n'
            "# a comment line is skipped\n"
            '{"phase": 2, "metric": "capacity", "value": 4.0}\n',
            encoding="utf-8",
        )
        ndjson_line = '\nndjson_path = "m.ndjson"'
    toml = textwrap.dedent(f"""\
        [source]
        key = "sub_test"
        human_readable_name = "Substrate test"
        purpose = "test"
        license = "CC0"
        homepage = "https://example.invalid"

        [fetch]
        adapter = "substrate_parameterization"{ndjson_line}

        [fetch.{adapter_key}.substrate]
        D = 4096
        sector_count = 4
        min_skeleton_length = 4
        token_seed_hex_chars = 8

        [fetch.{adapter_key}.encoding]
        backend = "klein4"
        encoder_library = "x.py"
        encoder_version = "0.1.0"

        [fetch.{adapter_key}.generation]
        default_top_k = 5
        max_walk_length = 10
        max_paths = 5
        cycle_policy = "allow"
        l4_direct_composition = false
        skeleton_length_fallback = [4]

        [fetch.{adapter_key}.hierarchical]
        n_buckets = 16
        default_strategy = "hash"
        allowed_strategies = ["hash"]
        sentence_hash_hex_chars = 8

        [fetch.{adapter_key}.corpus]
        source = "template"
        tokenizer = "whitespace"

        [parse]
        format = "ndjson"

        [schema]
        data_schema_id = "test://schema/substrate"

        [rendering]
        cite_as_template = "Substrate run row {{row_index}}"
        purpose_template = "characterization"

        [attestation]
        hash_algorithm = "sha256"
        """)
    (d / "descriptor.toml").write_text(toml, encoding="utf-8")
    return d


def test_config_for_new_adapter_nesting(tmp_path):
    d = _write_descriptor(tmp_path, "substrate_parameterization")
    desc = descriptor_mod.load_descriptor(d / "descriptor.toml")
    assert desc.adapter_name == "substrate_parameterization"
    cfg = sp.config_for(desc)
    assert cfg.substrate.D == 4096
    assert cfg.generation.cycle_policy == "allow"
    assert cfg.generation.skeleton_length_fallback == (4,)


def test_config_for_legacy_literature_curated_nesting(tmp_path):
    # The catalog rode literature_curated as its interim home; config_for must
    # still find the params there for a not-yet-migrated descriptor.
    d = _write_descriptor(tmp_path, "literature_curated")
    desc = descriptor_mod.load_descriptor(d / "descriptor.toml")
    cfg = sp.config_for(desc)
    assert cfg.substrate.D == 4096


# ── adapter protocol — fetch + parse over committed measurement NDJSON ────
def test_fetch_parse_measurement_ndjson(tmp_path):
    d = _write_descriptor(
        tmp_path, "substrate_parameterization", with_ndjson=True
    )
    desc = descriptor_mod.load_descriptor(d / "descriptor.toml")
    raw_chunks = list(sp.fetch(desc))
    assert len(raw_chunks) == 1
    rows = list(sp.parse(raw_chunks[0], desc))
    assert len(rows) == 2  # comment line skipped
    assert rows[0]["phase"] == 1 and rows[1]["metric"] == "capacity"


def test_fetch_missing_ndjson_path_raises(tmp_path):
    d = _write_descriptor(tmp_path, "substrate_parameterization")
    desc = descriptor_mod.load_descriptor(d / "descriptor.toml")
    with pytest.raises(_base.AdapterError, match="ndjson_path"):
        list(sp.fetch(desc))
