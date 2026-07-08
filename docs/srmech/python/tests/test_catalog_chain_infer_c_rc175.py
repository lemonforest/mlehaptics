"""rc175 — catalog CHAIN ORCHESTRATION → C parity (the ORCHESTRATION→C spine,
batch 5).

The two chain-runner-dependent catalog ops earned C peers, each COMPOSING the
rc173 chain PARSE + the rc174 chain-RUNNER over the catalog's
``operator_chain``:

  * ``list_catalog_chains`` → ``srmech_catalog_list_chains`` — validate + project
    each chain to its summary ``{classes, n_steps, name, on_error, returns,
    summary}`` (canonical JSON, byte-identical to the pure projection).
  * ``run_catalog_chain`` → ``srmech_catalog_run_chain`` — find the NAMED chain in
    ``operator_chain`` + RUN it end-to-end in C (same bounded Class-N op set +
    value-descriptor OUTPUT contract as ``srmech_chain_run``).

A bare-C host lists / runs a catalog's declared chains with these peers + the
srmech_toml parser (Python passes the descriptor's ``[catalog]`` table as
``{chain_schema_version, operator_chain}``). rc103 inform-don't-limit is
preserved: an unknown chain name / out-of-table op / non-i64 referenced input /
overflow → the COMPLETE pure path (never a wrong answer; the pure path raises the
exact error / runs over the live object graph).

HONEST SPLIT — ``dispatch.infer`` (the F929 OPEN/infer router) is DEFERRED to
rc176. It is NOT thin: its relationship payloads carry LIVE non-JSON carrier
objects (BiPoly / TriPoly / QPoly / QBiPoly / EllRatio / Mat / the One), and
moving its try-and-verify LOGIC to C needs a full multi-carrier FFI marshalling
layer for the 7 reducer families + closed_form return marshalling — a multi-rc
arc, not one clean rc. This file pins that infer STILL works (unchanged, pure)
and that it has NO C peer yet (the deferral is real, not a silent stub).

numpy-free + math-free (stdlib json + tomllib/tomli).
"""
from __future__ import annotations

import pytest

from srmech.amsc import catalog, compose

# Is the rc175 native chain-orchestration bound? (A stale ABI-3 lib / pure wheel
# / numpy-absent-but-no-.so env keeps the pure path — parity still holds.)
_HAS_LIST = catalog._catalog_lib(
    "srmech_catalog_list_chains", "srmech_catalog_list_chains_arena_bytes"
) is not None
_HAS_RUN = catalog._catalog_lib(
    "srmech_catalog_run_chain", "srmech_catalog_run_chain_arena_bytes"
) is not None

# The shipped executable-chain descriptors (the real apparatus).
_SHIPPED = ("pi_digits", "asymptotic_calculus", "cosmos_validation")


def _force_catalog_pure(fn, *args, **kwargs):
    """Call ``fn`` with the native CATALOG chain-orchestration dispatch disabled
    (the run/list fall to the pure path — which, for run, still routes the RUN
    through compose.run_chain's own C dispatch)."""
    orig = catalog._catalog_lib
    catalog._catalog_lib = lambda *a, **k: None
    try:
        return fn(*args, **kwargs)
    finally:
        catalog._catalog_lib = orig


def _force_all_pure(fn, *args, **kwargs):
    """Call ``fn`` with BOTH the catalog + compose native dispatch disabled — a
    genuinely all-Python reference (no C anywhere)."""
    oc, ocmp = catalog._catalog_lib, compose._compose_lib
    catalog._catalog_lib = lambda *a, **k: None
    compose._compose_lib = lambda *a, **k: None
    try:
        return fn(*args, **kwargs)
    finally:
        catalog._catalog_lib, compose._compose_lib = oc, ocmp


# ---------------------------------------------------------------------
# list_catalog_chains → srmech_catalog_list_chains
# ---------------------------------------------------------------------


@pytest.mark.parametrize("src", _SHIPPED)
def test_list_catalog_chains_native_equals_pure(src):
    """Each shipped catalog: the C-projected chain listing == the pure
    projection (dict-equal; the summary carries name/summary/returns/on_error/
    n_steps/classes)."""
    native = catalog.list_catalog_chains(src)
    pure = _force_catalog_pure(catalog.list_catalog_chains, src)
    assert native == pure, f"{src}: {native!r} != {pure!r}"
    assert native["ok"] is True
    assert native["n_chains"] >= 1
    for ch in native["chains"]:
        assert set(ch) == {"name", "summary", "returns",
                           "on_error", "n_steps", "classes"}
        assert ch["n_steps"] == len(ch["classes"])


def test_list_catalog_chains_multichain_projection():
    """asymptotic_calculus declares 5 chains — the C projection lists all 5 with
    their per-step class sequences."""
    listing = catalog.list_catalog_chains("asymptotic_calculus")
    assert listing["n_chains"] == 5
    names = {c["name"] for c in listing["chains"]}
    assert names == {"exp_series_truncate", "sin_series_truncate",
                     "cos_series_truncate", "log1p_series_truncate",
                     "atan_series_truncate"}
    for c in listing["chains"]:
        assert c["classes"] == ["N"]      # each is a single Class-N step


def test_list_catalog_chains_genuinely_engaged():
    """The C list path GENUINELY runs (returns non-None) when the lib is present
    — never a silent all-pure fallback."""
    if not _HAS_LIST:
        pytest.skip("rc175 native list peer not bound (pure-only env)")
    _descriptor, toml_dict = catalog._catalog_toml_dict("asymptotic_calculus")
    out = catalog._list_catalog_chains_native("asymptotic_calculus", toml_dict)
    assert out is not None and out["n_chains"] == 5


def test_list_catalog_chains_unknown_source():
    """An unknown source_key → the honest error dict (never a crash), on both
    native + pure."""
    for run in (catalog.list_catalog_chains,
                lambda s: _force_catalog_pure(catalog.list_catalog_chains, s)):
        out = run("no_such_source_xyz")
        assert out["ok"] is False
        assert "error" in out and "available" in out


# ---------------------------------------------------------------------
# run_catalog_chain → srmech_catalog_run_chain
# ---------------------------------------------------------------------


def _shipped_runs():
    """(source, chain_name, row_index) for every shipped chain row."""
    cases = []
    for src in _SHIPPED:
        try:
            chains = {c.name for c in catalog._load_catalog_chains(src)}
            ds = catalog.get_attested_dataset(src)
        except Exception:  # pragma: no cover — descriptor absent
            continue
        for i, row in enumerate(ds.get("rows", [])):
            cid = row.get("data", {}).get("chain_id")
            if cid in chains:
                cases.append((src, cid, i))
    return cases


_SHIPPED_RUNS = _shipped_runs()


@pytest.mark.parametrize("src,chain,ridx", _SHIPPED_RUNS,
                         ids=[f"{s}:{c}:{i}" for s, c, i in _SHIPPED_RUNS])
def test_run_catalog_chain_native_equals_fully_pure(src, chain, ridx):
    """Each shipped chain row: the C orchestration peer's output == the fully-
    pure (no-C-anywhere) output, byte-identical."""
    native = catalog.run_catalog_chain(src, chain, row_index=ridx)
    pure = _force_all_pure(catalog.run_catalog_chain, src, chain, row_index=ridx)
    assert native == pure, f"{src}/{chain} row{ridx}: {native!r} != {pure!r}"


def test_run_catalog_chain_matches_attested():
    """Every shipped chain row with an attested expected value: the C peer's
    output matches the attested ground-truth (not just self-consistent)."""
    for src, chain, ridx in _SHIPPED_RUNS:
        ds = catalog.get_attested_dataset(src, limit=ridx + 1, offset=ridx)
        data = ds["rows"][0].get("data", {})
        if "expected_num" not in data:
            continue
        out = catalog.run_catalog_chain(src, chain, row_index=ridx)
        assert out == (data["expected_num"], data["expected_den"]), (
            f"{src}/{chain} row{ridx}: {out} != attested "
            f"({data['expected_num']}, {data['expected_den']})"
        )


def test_run_catalog_chain_genuinely_engaged():
    """Every shipped chain row GENUINELY engages the C orchestration peer (never
    a silent MISS) when the native lib is present."""
    if not _HAS_RUN:
        pytest.skip("rc175 native run peer not bound (pure-only env)")
    assert _SHIPPED_RUNS, "no shipped chain rows discovered"
    for src, chain, ridx in _SHIPPED_RUNS:
        chains = catalog._load_catalog_chains(src)
        spec = next(c for c in chains if c.name == chain)
        ds = catalog.get_attested_dataset(src, limit=ridx + 1, offset=ridx)
        row = dict(ds["rows"][0].get("data", {}))
        out = catalog._run_catalog_chain_native(chains, chain, spec, row, {})
        assert out is not catalog._RUN_NATIVE_MISS, (
            f"{src}/{chain} row{ridx} silently MISSed (C should run it)"
        )


def test_run_catalog_chain_friedmann_9step_bignum():
    """The deepest shipped chain — the 9-step Friedmann dark-fraction over
    bignum-ℚ intermediates (a_den^4 overflows int64) — runs through the C
    orchestration peer to the attested reduced rational."""
    if not _HAS_RUN:
        pytest.skip("native run peer not bound")
    ds = catalog.get_attested_dataset("cosmos_validation")
    hit = False
    for i, row in enumerate(ds.get("rows", [])):
        data = row.get("data", {})
        if data.get("chain_id") != "friedmann_dark_fraction":
            continue
        hit = True
        out = catalog.run_catalog_chain(
            "cosmos_validation", "friedmann_dark_fraction", row_index=i)
        assert out == (data["expected_num"], data["expected_den"])
    assert hit, "no friedmann_dark_fraction rows discovered"


def test_run_catalog_chain_unknown_chain_raises_keyerror():
    """An unknown chain name raises KeyError on BOTH native + pure (the C peer
    returns non-OK for not-found → the pure path raises)."""
    with pytest.raises(KeyError):
        catalog.run_catalog_chain("pi_digits", "no_such_chain")
    with pytest.raises(KeyError):
        _force_all_pure(catalog.run_catalog_chain, "pi_digits", "no_such_chain")


def test_run_catalog_chain_unknown_source_raises_keyerror():
    """An unknown source_key raises KeyError (from _load_catalog_chains, before
    any dispatch)."""
    with pytest.raises(KeyError):
        catalog.run_catalog_chain("no_such_source_xyz", "x")


# ---------------------------------------------------------------------
# inform-don't-limit — the C run peer MISSes to pure on ineligible chains.
# ---------------------------------------------------------------------


def test_run_native_misses_out_of_table_op():
    """A chain with a non-Class-N op (Class A sha256_bytes) → the C run peer
    MISSes (the pure path runs it over the live object graph)."""
    spec = compose.parse_chain_spec(
        {"name": "h", "summary": "s", "returns": "str",
         "steps": [{"class": "A", "op": "sha256_bytes",
                    "args": {"data": "@input.b"}}]})
    out = catalog._run_catalog_chain_native(
        [spec], "h", spec, None, {"b": b"x"})
    assert out is catalog._RUN_NATIVE_MISS


def test_run_native_misses_non_i64_referenced_input():
    """A Class-N chain whose referenced @input int exceeds int64 → MISS (the C
    JSON parser reads int64; the pure bignum path is exact)."""
    spec = compose.parse_chain_spec(
        {"name": "b", "summary": "s", "returns": "q",
         "steps": [{"class": "N", "op": "rational_add",
                    "args": {"a": ["@input.n", 1], "b": [1, 1]}}]})
    out = catalog._run_catalog_chain_native(
        [spec], "b", spec, None, {"n": 1 << 70})
    assert out is catalog._RUN_NATIVE_MISS


def test_run_native_misses_non_raise_policy():
    """A non-"raise" chain policy → MISS (warn/skip semantics stay Python-side)."""
    spec = compose.parse_chain_spec(
        {"name": "w", "summary": "s", "returns": "q", "on_error": "warn_return_none",
         "steps": [{"class": "N", "op": "rational_add",
                    "args": {"a": [1, 2], "b": [1, 2]}}]})
    out = catalog._run_catalog_chain_native([spec], "w", spec, None, {})
    assert out is catalog._RUN_NATIVE_MISS


# ---------------------------------------------------------------------
# dispatch.infer — DEFERRED to rc176. Pin that it still works (pure) and has
# NO C peer yet (the honest split, not a silent stub).
# ---------------------------------------------------------------------


def test_infer_deferred_has_no_c_peer():
    """The F929 infer router is deferred to rc176 — there is NO srmech_infer C
    symbol (the deferral is real; infer stays pure orchestration this rc)."""
    from srmech.amsc import _native
    if _native.LIB is None:
        pytest.skip("no native lib bound")
    assert not hasattr(_native.LIB, "srmech_infer")
    assert not hasattr(_native.LIB, "srmech_dispatch_infer")


def test_infer_still_routes_each_row_and_open_unchanged():
    """infer STILL routes each F929 row + the honest OPEN residue (unchanged by
    this rc). A spectral (edges) row, a cyclic (σ,θ) row, and an unrecognizable
    input → OPEN; the anti-hallucination invariant holds."""
    from srmech.amsc.dispatch import infer

    spec = infer({"edges": [(0, 1), (1, 2), (2, 3)], "n": 4})
    assert spec["reducible"] is True and spec["row"] == "spectral"

    cyc = infer({"sigma": 1, "theta_num": 0, "theta_den": 1})
    assert cyc["reducible"] is True and cyc["row"] == "cyclic"

    opn = infer({"flavor": "strawberry", "count": 7})
    assert opn["reducible"] is False and opn["row"] is None
    assert opn["candidate_next_theory"]


def test_module_is_numpy_and_math_free():
    """This test module imports neither numpy nor math (the §2 discipline).
    The forbidden tokens are assembled by concatenation so the source itself
    does not contain the literal (avoiding a self-referential false positive)."""
    import re

    with open(__file__, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert ("import" + " numpy") not in text
    assert ("import" + " math") not in text
    assert re.search(r"\babs\([^)]", text) is None
