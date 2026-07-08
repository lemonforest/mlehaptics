"""rc173 — the amsc.compose LINEAR CHAIN-RUNNER PARSE+VALIDATE → C parity.

The ORCHESTRATION→C spine, batch 3: ``parse_chain_spec`` +
``parse_catalog_chains`` earned C peers (``srmech_chain_spec_parse`` /
``srmech_chain_catalog_parse``). This proves the native path is
STRUCTURALLY IDENTICAL to the pure path across a representative sweep —
every reference kind (@row/@input/@step/@catalog), nested args, each error
policy, and every validation-failure case (which the C peer defers to the
pure path so the specific ``ChainSpecError`` is raised).

HONEST SPLIT (reported at build): only PARSE is in C this rc. resolve_chain
/ run_chain invoke ARBITRARY srmech ops (heterogeneous kwargs) over the LIVE
Python object graph — a bounded-op FFI foundation, scoped rc174. So the run
loop is NOT exercised here; the parse outputs are exact/structural (no numeric
within-tol comparison needed — that lesson applies to the rc174 run loop).

numpy-free (stdlib json + tomllib/tomli).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from srmech.amsc import compose

_ATTESTED = Path(__file__).resolve().parent.parent / "srmech" / "amsc" / "attested"

# Is the rc173 native chain-parser bound? (A stale ABI-3 lib / pure wheel /
# numpy-absent-but-no-.so env keeps the pure path — the parity still holds,
# it just compares pure-vs-pure there.)
_HAS_NATIVE = compose._compose_lib(
    "srmech_chain_spec_parse", "srmech_chain_spec_parse_arena_bytes"
) is not None


def _force_pure(fn, *args, **kwargs):
    """Call ``fn`` with the native compose dispatch disabled (pure path)."""
    orig = compose._compose_lib
    compose._compose_lib = lambda *a, **k: None
    try:
        return fn(*args, **kwargs)
    finally:
        compose._compose_lib = orig


# ---------------------------------------------------------------------
# A representative sweep of VALID chains (native must == pure structurally)
# ---------------------------------------------------------------------

_VALID_CHAINS = {
    "single_step": {
        "name": "single", "summary": "one step", "returns": "int  # x",
        "steps": [{"class": "I", "op": "gcd", "args": {"a": 24, "b": 36}}],
    },
    "multi_step_step_ref": {
        "name": "multi", "summary": "threads outputs", "returns": "int",
        "steps": [
            {"class": "I", "op": "mod_add", "args": {"a": 3, "b": 5, "n": 10}},
            {"class": "I", "op": "mod_mul",
             "args": {"a": "@step[0].output", "b": 4, "n": 100}},
        ],
    },
    "row_ref": {
        "name": "rowc", "summary": "row ns", "returns": "str",
        "steps": [{"class": "A", "op": "sha256_bytes",
                   "args": {"data": "@row.payload"}}],
    },
    "input_ref": {
        "name": "inpc", "summary": "input ns", "returns": "str",
        "steps": [{"class": "A", "op": "sha256_bytes",
                   "args": {"data": "@input.bytes"}}],
    },
    "catalog_ref": {
        "name": "catc", "summary": "catalog ns", "returns": "Any",
        "steps": [{"class": "L", "op": "some_op",
                   "args": {"x": "@catalog.row_key.col"}}],
    },
    "step_dotted": {
        "name": "dotc", "summary": "dotted after index", "returns": "Any",
        "steps": [
            {"class": "A", "op": "sha256_bytes", "args": {"data": "@input.a"}},
            {"class": "L", "op": "op2", "args": {"v": "@step[0].output.field"}},
        ],
    },
    "nested_args_refs": {
        "name": "nest", "summary": "refs in list + dict", "returns": "Any",
        "steps": [{"class": "M", "op": "bind", "args": {
            "vecs": ["@input.a", "@input.b", "literal"],
            "opts": {"anchor": "@row.seed", "k": 3},
        }}],
    },
    "chain_on_error": {
        "name": "choe", "summary": "chain-level policy", "returns": "Any",
        "on_error": "warn_return_none",
        "steps": [{"class": "I", "op": "mod_inv", "args": {"a": 2, "n": 4}}],
    },
    "step_on_error": {
        "name": "stoe", "summary": "per-step policy", "returns": "Any",
        "steps": [
            {"class": "I", "op": "mod_inv", "args": {"a": 2, "n": 4},
             "on_error": "warn_return_none"},
            {"class": "I", "op": "gcd", "args": {"a": 6, "b": 9}},
        ],
    },
    "skip_policy": {
        "name": "skp", "summary": "skip policy is legal to parse",
        "returns": "Any", "on_error": "skip",
        "steps": [{"class": "A", "op": "sha256_bytes", "args": {}}],
    },
    "all_classes": {
        "name": "allc", "summary": "A..N are all legal", "returns": "Any",
        "steps": [{"class": c, "op": "noop", "args": {}}
                  for c in "ABCDEFGHIJKLMN"],
    },
    "step10_index": {  # @step[N] with N > 9 (multi-digit index)
        "name": "s10", "summary": "multi-digit step index", "returns": "Any",
        "steps": ([{"class": "A", "op": "o", "args": {}} for _ in range(11)]
                  + [{"class": "L", "op": "o", "args": {"x": "@step[10].output"}}]),
    },
}


@pytest.mark.parametrize("key", sorted(_VALID_CHAINS))
def test_parse_chain_spec_native_equals_pure(key):
    chain = _VALID_CHAINS[key]
    native = compose.parse_chain_spec(chain)
    pure = _force_pure(compose.parse_chain_spec, chain)
    assert native == pure, f"{key}: native spec != pure spec"
    # spot-check the reconstruction preserved fields + arg objects
    assert native.name == pure.name
    assert len(native.steps) == len(pure.steps)
    for ns, ps in zip(native.steps, pure.steps):
        assert ns.class_id == ps.class_id
        assert ns.op == ps.op
        assert ns.args == ps.args
        assert ns.on_error == ps.on_error


def test_native_path_is_actually_exercised():
    """When the native lib is present, the C peer really produces the spec
    (not a silent all-pure run)."""
    if not _HAS_NATIVE:
        pytest.skip("rc173 native chain-parser not bound (pure-only env)")
    spec = compose._parse_chain_spec_native(_VALID_CHAINS["multi_step_step_ref"])
    assert spec is not None
    assert spec.name == "multi"
    assert spec.steps[1].args["a"] == "@step[0].output"


def test_arg_object_type_preserved_not_json_roundtripped():
    """A tuple arg VALUE stays a tuple (native pulls args from the ORIGINAL
    dict, never a JSON round-trip that would turn it into a list)."""
    chain = {"name": "t", "summary": "s", "returns": "Any",
             "steps": [{"class": "L", "op": "o",
                        "args": {"pair": (1, 2), "ref": "@input.a"}}]}
    native = compose.parse_chain_spec(chain)
    pure = _force_pure(compose.parse_chain_spec, chain)
    assert native == pure
    assert native.steps[0].args["pair"] == (1, 2)
    assert isinstance(native.steps[0].args["pair"], tuple)


# ---------------------------------------------------------------------
# INVALID chains — the C peer defers to pure so the SAME ChainSpecError
# (with the SAME message) is raised on both paths.
# ---------------------------------------------------------------------

_INVALID_CHAINS = {
    "unknown_class": (
        {"name": "x", "summary": "y", "returns": "z",
         "steps": [{"class": "Z", "op": "n", "args": {}}]}, "unknown class"),
    "missing_returns": (
        {"name": "x", "summary": "y",
         "steps": [{"class": "A", "op": "o", "args": {}}]}, "returns"),
    "empty_steps": (
        {"name": "x", "summary": "y", "returns": "z", "steps": []},
        "non-empty"),
    "illegal_chain_on_error": (
        {"name": "x", "summary": "y", "returns": "z", "on_error": "bail",
         "steps": [{"class": "A", "op": "o", "args": {}}]}, "illegal on_error"),
    "illegal_step_on_error": (
        {"name": "x", "summary": "y", "returns": "z",
         "steps": [{"class": "A", "op": "o", "args": {}, "on_error": "bail"}]},
        "illegal on_error"),
    "malformed_ref": (
        {"name": "x", "summary": "y", "returns": "z",
         "steps": [{"class": "A", "op": "o", "args": {"d": "@@bogus"}}]},
        "DSL grammar"),
    "step_self_ref": (
        {"name": "x", "summary": "y", "returns": "z",
         "steps": [{"class": "A", "op": "o", "args": {"d": "@step[0].output"}}]},
        "has not yet executed"),
    "step_forward_ref": (
        {"name": "x", "summary": "y", "returns": "z", "steps": [
            {"class": "A", "op": "o", "args": {}},
            {"class": "A", "op": "o", "args": {"d": "@step[5].output"}}]},
        "has not yet executed"),
    "missing_op": (
        {"name": "x", "summary": "y", "returns": "z",
         "steps": [{"class": "A", "args": {}}]}, "op"),
    "args_not_dict": (
        {"name": "x", "summary": "y", "returns": "z",
         "steps": [{"class": "A", "op": "o", "args": [1, 2]}]}, "args must be"),
    "bad_namespace": (
        {"name": "x", "summary": "y", "returns": "z",
         "steps": [{"class": "A", "op": "o", "args": {"d": "@bogus.x"}}]},
        "DSL grammar"),
}


@pytest.mark.parametrize("key", sorted(_INVALID_CHAINS))
def test_invalid_chain_native_defers_to_pure(key):
    chain, expect = _INVALID_CHAINS[key]
    with pytest.raises(compose.ChainSpecError, match=expect) as native_exc:
        compose.parse_chain_spec(chain)
    with pytest.raises(compose.ChainSpecError, match=expect) as pure_exc:
        _force_pure(compose.parse_chain_spec, chain)
    # same class + same message (native path re-runs the pure raiser)
    assert str(native_exc.value) == str(pure_exc.value)


def test_non_dict_input_native_defers_to_pure():
    with pytest.raises(compose.ChainSpecError, match="must be a dict"):
        compose.parse_chain_spec(["not", "a", "dict"])  # type: ignore[arg-type]
    with pytest.raises(compose.ChainSpecError, match="must be a dict"):
        _force_pure(compose.parse_chain_spec, ["not", "a", "dict"])


# ---------------------------------------------------------------------
# parse_catalog_chains — native == pure (inline + the real descriptors)
# ---------------------------------------------------------------------


def _catalog(chains, version=1):
    cat = {"chain_schema_version": version, "operator_chain": chains}
    return {"catalog": cat}


def test_parse_catalog_chains_native_equals_pure_inline():
    chains = [_VALID_CHAINS["single_step"], _VALID_CHAINS["multi_step_step_ref"]]
    toml = _catalog(chains)
    native = compose.parse_catalog_chains(toml)
    pure = _force_pure(compose.parse_catalog_chains, toml)
    assert native == pure
    assert [c.name for c in native] == ["single", "multi"]


def test_parse_catalog_chains_empty_returns_empty_list():
    assert compose.parse_catalog_chains({"catalog": {}}) == []


def test_parse_catalog_chains_missing_version_defers_to_pure():
    toml = {"catalog": {"operator_chain": [_VALID_CHAINS["single_step"]]}}
    with pytest.raises(compose.ChainSpecError, match="chain_schema_version"):
        compose.parse_catalog_chains(toml)
    with pytest.raises(compose.ChainSpecError, match="chain_schema_version"):
        _force_pure(compose.parse_catalog_chains, toml)


def test_parse_catalog_chains_bad_version_defers_to_pure():
    toml = _catalog([_VALID_CHAINS["single_step"]], version=99)
    with pytest.raises(compose.ChainSpecError, match="implements v1"):
        compose.parse_catalog_chains(toml)
    with pytest.raises(compose.ChainSpecError, match="implements v1"):
        _force_pure(compose.parse_catalog_chains, toml)


def test_parse_catalog_chains_invalid_chain_defers_to_pure():
    """A malformed chain inside a valid-version catalog → the whole native
    call defers, and the pure path raises for that chain."""
    toml = _catalog([_VALID_CHAINS["single_step"],
                     {"name": "bad", "summary": "s", "returns": "z",
                      "steps": [{"class": "Z", "op": "o", "args": {}}]}])
    with pytest.raises(compose.ChainSpecError, match="unknown class"):
        compose.parse_catalog_chains(toml)
    with pytest.raises(compose.ChainSpecError, match="unknown class"):
        _force_pure(compose.parse_catalog_chains, toml)


@pytest.mark.parametrize("source_key", ["pi_digits", "asymptotic_calculus"])
def test_real_descriptor_catalog_chains_native_equals_pure(source_key):
    """The shipped executable-chain descriptors round-trip identically."""
    descriptor = _ATTESTED / source_key / "descriptor.toml"
    if not descriptor.exists():
        pytest.skip(f"{source_key} descriptor not present")
    with open(descriptor, "rb") as f:
        toml = tomllib.load(f)
    native = compose.parse_catalog_chains(toml)
    pure = _force_pure(compose.parse_catalog_chains, toml)
    assert native == pure
    assert len(native) >= 1
    # the chains are runnable-shaped (names + non-empty steps preserved)
    for cn, cp in zip(native, pure):
        assert cn.name == cp.name
        assert len(cn.steps) == len(cp.steps) >= 1


# ---------------------------------------------------------------------
# Consumer re-verify: catalog.list_catalog_chains routes through
# parse_catalog_chains → must stay byte-identical native vs pure.
# ---------------------------------------------------------------------


def test_consumer_list_catalog_chains_native_equals_pure():
    from srmech.amsc import catalog
    # find a source with executable chains (pi_digits ships one)
    listing_native = catalog.list_catalog_chains("pi_digits")
    listing_pure = _force_pure(catalog.list_catalog_chains, "pi_digits")
    assert listing_native == listing_pure
    assert listing_native.get("ok") is True
    assert listing_native.get("n_chains", 0) >= 1
