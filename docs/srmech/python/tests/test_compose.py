"""Tests for ``srmech.amsc.compose`` — ADR-0002 Phase 2 composition engine.

Schema v1 candidate per
``docs/srmech/adr/0002-phase-1-operator-chain-schema.md`` (Phase 1 ship)
implemented in v0.4.1rc5 (Phase 2 ship).
"""

from __future__ import annotations

import sys
from typing import Any, Dict

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from srmech.amsc import compose


# ---------------------------------------------------------------------
# parse_chain_spec — schema validation
# ---------------------------------------------------------------------


def _minimal_chain(steps: list[dict]) -> dict:
    return {
        "name": "test_chain",
        "summary": "A test chain.",
        "returns": "Any  # test",
        "steps": steps,
    }


def test_parse_chain_spec_validates_v1_schema():
    chain = _minimal_chain([
        {"class": "A", "op": "sha256_bytes", "args": {"data": "@input.payload"}},
    ])
    spec = compose.parse_chain_spec(chain)
    assert spec.name == "test_chain"
    assert spec.summary == "A test chain."
    assert spec.on_error == "raise"
    assert len(spec.steps) == 1
    assert spec.steps[0].class_id == "A"
    assert spec.steps[0].op == "sha256_bytes"


def test_parse_chain_spec_rejects_missing_required_key():
    chain = {"name": "x", "summary": "y", "steps": []}  # missing returns
    with pytest.raises(compose.ChainSpecError):
        compose.parse_chain_spec(chain)


def test_parse_chain_spec_rejects_unknown_class():
    chain = _minimal_chain([
        {"class": "Z", "op": "noop", "args": {}},
    ])
    with pytest.raises(compose.ChainSpecError, match="unknown class"):
        compose.parse_chain_spec(chain)


def test_parse_chain_spec_rejects_empty_steps():
    chain = _minimal_chain([])
    with pytest.raises(compose.ChainSpecError, match="non-empty"):
        compose.parse_chain_spec(chain)


def test_parse_chain_spec_rejects_illegal_on_error():
    chain = _minimal_chain([
        {"class": "A", "op": "sha256_bytes", "args": {}},
    ])
    chain["on_error"] = "bail_out"
    with pytest.raises(compose.ChainSpecError, match="illegal on_error"):
        compose.parse_chain_spec(chain)


def test_parse_chain_spec_rejects_malformed_reference():
    chain = _minimal_chain([
        {"class": "A", "op": "sha256_bytes", "args": {"data": "@@bogus"}},
    ])
    with pytest.raises(compose.ChainSpecError, match="DSL grammar"):
        compose.parse_chain_spec(chain)


def test_parse_chain_spec_rejects_step_self_reference():
    chain = _minimal_chain([
        {"class": "A", "op": "sha256_bytes",
         "args": {"data": "@step[0].output"}},
    ])
    with pytest.raises(compose.ChainSpecError, match="has not yet executed"):
        compose.parse_chain_spec(chain)


def test_parse_chain_spec_rejects_unknown_op_at_resolve_time():
    chain = _minimal_chain([
        {"class": "A", "op": "totally_made_up_op", "args": {}},
    ])
    spec = compose.parse_chain_spec(chain)  # parses OK
    with pytest.raises(compose.ChainSpecError, match="not found on"):
        compose.resolve_chain(spec)


# ---------------------------------------------------------------------
# Reference DSL resolution
# ---------------------------------------------------------------------


def test_resolve_reference_dsl_row_namespace():
    # Build a 1-step chain that just returns @row.text (using a custom
    # registry that maps a dummy class to a module that returns input).
    spec = compose.parse_chain_spec(_minimal_chain([
        {"class": "A", "op": "sha256_bytes", "args": {"data": "@row.payload"}},
    ]))
    result = compose.run_chain(
        spec, row={"payload": b"hello"}, inputs={},
    )
    # sha256("hello") = 2cf24dba...
    assert isinstance(result, str)
    assert result.startswith("2cf24dba")


def test_resolve_reference_dsl_input_namespace():
    spec = compose.parse_chain_spec(_minimal_chain([
        {"class": "A", "op": "sha256_bytes", "args": {"data": "@input.bytes"}},
    ]))
    result = compose.run_chain(spec, inputs={"bytes": b"world"})
    assert isinstance(result, str)
    # sha256("world") = 486ea46224d1bb4fb680f34f7c9ad96a8f24ec88be73ea8e5a6c65260e9cb8a7
    assert result.startswith("486ea462")


def test_resolve_reference_dsl_step_namespace():
    # Two-step chain: step 0 hashes input.a, step 1 hashes a string
    # derived from step 0's output.
    spec = compose.parse_chain_spec(_minimal_chain([
        {"class": "A", "op": "sha256_bytes", "args": {"data": "@input.a"}},
        {"class": "A", "op": "sha256_bytes",
         "args": {"data": "@input.b"}},
    ]))
    result = compose.run_chain(
        spec, inputs={"a": b"first", "b": b"second"},
    )
    # Step 1's output (sha256("second")) is the chain's output.
    import hashlib
    assert result == hashlib.sha256(b"second").hexdigest()


# ---------------------------------------------------------------------
# Linear pipeline
# ---------------------------------------------------------------------


def test_run_chain_linear_pipeline_threads_step_outputs():
    """Step 1 consumes step 0's output via @step[0].output reference."""
    # We use Class I (cyclic) operations: mod_add then mod_mul.
    spec = compose.parse_chain_spec(_minimal_chain([
        {"class": "I", "op": "mod_add",
         "args": {"a": 3, "b": 5, "n": 10}},
        {"class": "I", "op": "mod_mul",
         "args": {"a": "@step[0].output", "b": 4, "n": 100}},
    ]))
    result = compose.run_chain(spec, inputs={})
    # step 0: (3 + 5) % 10 = 8; step 1: (8 * 4) % 100 = 32
    assert result == 32


def test_run_chain_returns_last_step_output():
    spec = compose.parse_chain_spec(_minimal_chain([
        {"class": "I", "op": "gcd", "args": {"a": 24, "b": 36}},
    ]))
    assert compose.run_chain(spec, inputs={}) == 12


# ---------------------------------------------------------------------
# Error policy
# ---------------------------------------------------------------------


def test_run_chain_error_policy_raise_propagates():
    spec = compose.parse_chain_spec(_minimal_chain([
        {"class": "I", "op": "mod_inv",
         "args": {"a": 2, "n": 4}},  # gcd(2, 4) != 1; raises
    ]))
    with pytest.raises(Exception):
        compose.run_chain(spec, inputs={})


def test_run_chain_error_policy_warn_return_none_per_step():
    chain = _minimal_chain([
        {"class": "I", "op": "mod_inv",
         "args": {"a": 2, "n": 4},
         "on_error": "warn_return_none"},
        {"class": "I", "op": "gcd", "args": {"a": 6, "b": 9}},
    ])
    spec = compose.parse_chain_spec(chain)
    with pytest.warns(RuntimeWarning):
        result = compose.run_chain(spec, inputs={})
    # Step 1 still executes; result is gcd(6, 9) = 3.
    assert result == 3


# ---------------------------------------------------------------------
# Catalog-level chain parsing
# ---------------------------------------------------------------------


def test_parse_catalog_chains_empty_when_no_chains():
    toml = {"catalog": {}}
    chains = compose.parse_catalog_chains(toml)
    assert chains == []


def test_parse_catalog_chains_requires_schema_version():
    toml = {
        "catalog": {
            "operator_chain": [_minimal_chain([
                {"class": "A", "op": "sha256_bytes", "args": {}},
            ])],
        },
    }
    with pytest.raises(compose.ChainSpecError, match="chain_schema_version"):
        compose.parse_catalog_chains(toml)


def test_parse_catalog_chains_rejects_unsupported_version():
    toml = {
        "catalog": {
            "chain_schema_version": 99,
            "operator_chain": [_minimal_chain([
                {"class": "A", "op": "sha256_bytes", "args": {}},
            ])],
        },
    }
    with pytest.raises(compose.ChainSpecError, match="implements v1"):
        compose.parse_catalog_chains(toml)


def test_parse_catalog_chains_cosmos_descriptors_have_no_executable_chains():
    """Cosmos catalog descriptors carry the `[catalog].chain_schema_version`
    field but ship no executable chain specs at v0.4.1rc7.

    The four Phase 1 worked-example chains (cmb_low_ell_maps ×2,
    cmb_polarisation_spectra ×1, cmb_bispectrum ×1) were removed in
    v0.4.1rc7 because they referenced primitives that don't yet exist
    (Class L `spherical_harmonic_decompose`, Class E
    `sorted_lookup_batch`, Class D `match_filter`, etc.). Per
    `[[feedback_every_doc_edit_faces_falsification]]` (user direction
    2026-05-16), the project does not ship chain specs that cannot
    execute. The chains re-land row-by-row as their underlying
    primitives ship (see each descriptor's deprecation comment for
    the Task # tracking).
    """
    from pathlib import Path
    attested = (Path(__file__).parent.parent / "srmech" / "amsc"
                / "attested")
    if not attested.exists():
        pytest.skip(f"attested dir not present at {attested}")
    cosmos_keys = {
        "cmb_low_ell_maps",
        "cmb_polarisation_spectra",
        "cmb_bispectrum",
    }
    seen_keys = set()
    for source_dir in attested.iterdir():
        if source_dir.name not in cosmos_keys:
            continue
        descriptor = source_dir / "descriptor.toml"
        if not descriptor.exists():
            continue
        with open(descriptor, "rb") as f:
            toml = tomllib.load(f)
        # Schema version preserved for forward compatibility
        assert toml.get("catalog", {}).get("chain_schema_version") == 1, (
            f"{source_dir.name}: chain_schema_version=1 must be preserved"
        )
        # No executable chains at rc7
        chains = compose.parse_catalog_chains(toml)
        assert len(chains) == 0, (
            f"{source_dir.name}: expected 0 chains at rc7, got {len(chains)}: "
            f"{[c.name for c in chains]}"
        )
        seen_keys.add(source_dir.name)
    assert seen_keys == cosmos_keys, (
        f"expected to inspect all 3 cosmos catalogs; got {seen_keys}"
    )


# ---------------------------------------------------------------------
# DEFAULT_CLASS_REGISTRY completeness
# ---------------------------------------------------------------------


def test_default_class_registry_covers_all_14_classes():
    expected = set("ABCDEFGHIJKLMN")
    actual = set(compose.DEFAULT_CLASS_REGISTRY.keys())
    assert actual == expected
