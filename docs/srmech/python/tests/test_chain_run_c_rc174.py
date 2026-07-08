"""rc174 — the amsc.compose LINEAR CHAIN-RUNNER RUN LOOP → C parity.

The ORCHESTRATION→C spine, batch 4: ``resolve_chain`` + ``run_chain`` earned a
C peer (``srmech_chain_run``). It RUNS a validated ``[[catalog.operator_chain]]``
end-to-end in C to BYTE-IDENTICAL OUTPUT for chains whose ops are all in the
BOUNDED Class-N dispatch table — the shipped apparatus: ``pi_cascade_digits`` /
``{exp,sin,cos,log1p,atan}_series_truncate`` / ``rational_{add,mul,div,pow_uint}``.

Parity is on OUTPUT, not the closure (a bare-C host has no live object graph):
the C peer marshals the final value back as a canonical value DESCRIPTOR
({"k":"s"/"q"/"i"/"n", ...}; bignums as decimal strings) the Python caller
reconstructs. rc103 inform-don't-limit: any out-of-table op / @catalog ref /
non-"raise" policy / non-i64 referenced input / C overflow → the COMPLETE pure
path runs (never a wrong answer; the pure path raises the exact error).

This proves: (a) every SHIPPED catalog chain runs end-to-end in C == pure
(pi digits / asymptotic-calculus series / the 9-step Friedmann dark-fraction
bignum-ℚ chain); (b) hand-built chains exercise every value-carrier type + each
reference kind + each error policy; (c) the out-of-table / @catalog / non-raise
/ error cases fall to pure identically; (d) the C path is GENUINELY exercised
(never a silent all-pure run).

numpy-free (stdlib json + tomllib/tomli).
"""
from __future__ import annotations

import sys

import pytest

from srmech.amsc import catalog, compose
from srmech.amsc.compose import (
    _NATIVE_MISS,
    _run_chain_native,
    parse_chain_spec,
    run_chain,
)

# Is the rc174 native run-loop bound? (A stale ABI-3 lib / pure wheel / numpy-
# absent-but-no-.so env keeps the pure path — parity still holds, pure vs pure.)
_HAS_NATIVE = compose._compose_lib(
    "srmech_chain_run", "srmech_chain_run_arena_bytes"
) is not None

# The shipped executable-chain descriptors (the real apparatus).
_SHIPPED = ("pi_digits", "asymptotic_calculus", "cosmos_validation")


def _force_pure(fn, *args, **kwargs):
    """Call ``fn`` with the native compose dispatch disabled (pure path)."""
    orig = compose._compose_lib
    compose._compose_lib = lambda *a, **k: None
    try:
        return fn(*args, **kwargs)
    finally:
        compose._compose_lib = orig


def _run_spec(chain_dict, row=None, inputs=None):
    """Build a ChainSpec from a dict + run it (native path if eligible)."""
    return run_chain(parse_chain_spec(chain_dict), row=row, inputs=inputs or {})


def _run_pure(chain_dict, row=None, inputs=None):
    return _force_pure(_run_spec, chain_dict, row=row, inputs=inputs)


# ---------------------------------------------------------------------
# (a) Every SHIPPED catalog chain runs end-to-end in C == pure.
# ---------------------------------------------------------------------


def _shipped_runs():
    """Enumerate (source, chain_name, row_index) for every shipped chain row."""
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
def test_shipped_chain_native_equals_pure(src, chain, ridx):
    """Each shipped catalog-chain row: native == pure, byte-identical."""
    native = catalog.run_catalog_chain(src, chain, row_index=ridx)
    pure = _force_pure(catalog.run_catalog_chain, src, chain, row_index=ridx)
    assert native == pure, f"{src}/{chain} row{ridx}: {native!r} != {pure!r}"


def test_shipped_chains_are_genuinely_run_in_c():
    """Every shipped chain row GENUINELY engages the C run loop (never a silent
    all-pure fallback) when the native lib is present."""
    if not _HAS_NATIVE:
        pytest.skip("rc174 native run loop not bound (pure-only env)")
    assert _SHIPPED_RUNS, "no shipped chain rows discovered"
    for src, chain, ridx in _SHIPPED_RUNS:
        chains = {c.name: c for c in catalog._load_catalog_chains(src)}
        ds = catalog.get_attested_dataset(src, limit=ridx + 1, offset=ridx)
        row = dict(ds["rows"][0].get("data", {}))
        result = _run_chain_native(chains[chain], row, {})
        assert result is not _NATIVE_MISS, (
            f"{src}/{chain} row{ridx} silently fell to pure (C should run it)"
        )


def test_the_friedmann_9step_bignum_chain_runs_in_c():
    """The deepest shipped chain — the 9-step Friedmann dark-fraction over
    bignum-ℚ intermediates (a_den^4 = 1e20 overflows int64) — runs in C to the
    attested reduced rational, byte-identical to the pure path."""
    if not _HAS_NATIVE:
        pytest.skip("native run loop not bound")
    ds = catalog.get_attested_dataset("cosmos_validation")
    for i, row in enumerate(ds.get("rows", [])):
        data = row.get("data", {})
        if data.get("chain_id") != "friedmann_dark_fraction":
            continue
        native = catalog.run_catalog_chain(
            "cosmos_validation", "friedmann_dark_fraction", row_index=i)
        assert native == (data["expected_num"], data["expected_den"]), (
            f"row{i}: {native} != attested "
            f"({data['expected_num']}, {data['expected_den']})"
        )


# ---------------------------------------------------------------------
# (b) Hand-built chains — every value-carrier type + reference kind.
# ---------------------------------------------------------------------


def test_str_carrier_and_input_ref():
    """CV_STR output + @input reference: pi_cascade_digits(@input.d)."""
    chain = {"name": "p", "summary": "s", "returns": "str",
             "steps": [{"class": "N", "op": "pi_cascade_digits",
                        "args": {"num_digits": "@input.d"}}]}
    native = _run_spec(chain, inputs={"d": 12})
    pure = _run_pure(chain, inputs={"d": 12})
    assert native == pure == "3.141592653589"


def test_rational_carrier_list_arg_and_step_threading():
    """CV_RATIONAL output + CV_LIST rational-pair arg + @step[N] threading:
    (1/2 + 1/3) * 6 == 5/1."""
    chain = {"name": "r", "summary": "s", "returns": "q", "steps": [
        {"class": "N", "op": "rational_add", "args": {"a": [1, 2], "b": [1, 3]}},
        {"class": "N", "op": "rational_mul",
         "args": {"a": "@step[0].output", "b": [6, 1]}},
    ]}
    native = _run_spec(chain)
    pure = _run_pure(chain)
    assert native == pure == (5, 1)


def test_pow_and_div_and_row_ref():
    """rational_pow_uint + rational_div + @row rational-pair reference."""
    chain = {"name": "d", "summary": "s", "returns": "q", "steps": [
        {"class": "N", "op": "rational_pow_uint",
         "args": {"base": ["@row.bn", "@row.bd"], "exp": 3}},
        {"class": "N", "op": "rational_div",
         "args": {"a": "@step[0].output", "b": [8, 27]}},
    ]}
    row = {"bn": 2, "bd": 3}
    native = _run_spec(chain, row=row)
    pure = _run_pure(chain, row=row)
    assert native == pure == (1, 1)


@pytest.mark.parametrize("op", [
    "exp_series_truncate", "sin_series_truncate", "cos_series_truncate",
    "log1p_series_truncate", "atan_series_truncate",
])
def test_series_ops_native_equals_pure(op):
    """Each of the five series ops runs in C == pure for a small rational arg
    (exp gives the attested 6331/3840 at x=1/2, N=5)."""
    chain = {"name": "t", "summary": "s", "returns": "q",
             "steps": [{"class": "N", "op": op,
                        "args": {"numerator": 1, "denominator": 2,
                                 "num_terms": 5}}]}
    native = _run_spec(chain)
    pure = _run_pure(chain)
    assert native == pure
    if op == "exp_series_truncate":
        assert native == (6331, 3840)


def test_single_step_chain():
    """A single-step chain (the simplest run)."""
    chain = {"name": "s", "summary": "s", "returns": "q",
             "steps": [{"class": "N", "op": "rational_add",
                        "args": {"a": [1, 4], "b": [1, 4]}}]}
    assert _run_spec(chain) == _run_pure(chain) == (1, 2)


# ---------------------------------------------------------------------
# (c) rc103 inform-don't-limit — these fall to the pure path IDENTICALLY,
#     and _run_chain_native reports the MISS honestly.
# ---------------------------------------------------------------------


def _miss(chain, row=None, inputs=None):
    return _run_chain_native(parse_chain_spec(chain), row, inputs or {})


def test_out_of_table_op_falls_to_pure():
    """An op not in the C dispatch table (sha256_bytes, Class A) → the pure
    path; native == pure."""
    chain = {"name": "o", "summary": "s", "returns": "str",
             "steps": [{"class": "A", "op": "sha256_bytes",
                        "args": {"data": "@input.b"}}]}
    assert _miss(chain, inputs={"b": b"x"}) is _NATIVE_MISS
    native = _run_spec(chain, inputs={"b": b"x"})
    pure = _run_pure(chain, inputs={"b": b"x"})
    assert native == pure


def test_catalog_ref_falls_to_pure():
    """A @catalog reference is not supported by the C run loop → pure."""
    chain = {"name": "c", "summary": "s", "returns": "q",
             "steps": [{"class": "N", "op": "rational_add",
                        "args": {"a": "@catalog.k.col", "b": [1, 1]}}]}
    assert _miss(chain) is _NATIVE_MISS


@pytest.mark.parametrize("policy", ["warn_return_none", "skip"])
def test_non_raise_policy_falls_to_pure(policy):
    """A non-"raise" error policy routes to pure (warnings / None / skip
    semantics stay Python-side)."""
    chain = {"name": "w", "summary": "s", "returns": "q", "on_error": policy,
             "steps": [{"class": "N", "op": "rational_add",
                        "args": {"a": [1, 2], "b": [1, 2]}}]}
    assert _miss(chain) is _NATIVE_MISS


def test_non_i64_referenced_input_falls_to_pure():
    """A referenced @input int that exceeds int64 → pure (C reads int64), yet
    an UNREFERENCED bignum stays irrelevant."""
    big = 1 << 70
    chain = {"name": "b", "summary": "s", "returns": "q",
             "steps": [{"class": "N", "op": "rational_add",
                        "args": {"a": ["@input.n", 1], "b": [1, 1]}}]}
    assert _miss(chain, inputs={"n": big}) is _NATIVE_MISS
    native = _run_spec(chain, inputs={"n": big})
    pure = _run_pure(chain, inputs={"n": big})
    assert native == pure == (big + 1, 1)


def test_unreferenced_bignum_row_field_still_runs_in_c():
    """A shipped-shape row with a bignum UNREFERENCED field (the expected_*
    columns) still runs in C — only referenced ints must fit int64."""
    if not _HAS_NATIVE:
        pytest.skip("native run loop not bound")
    chain = {"name": "u", "summary": "s", "returns": "q",
             "steps": [{"class": "N", "op": "rational_add",
                        "args": {"a": ["@row.x_num", "@row.x_den"],
                                 "b": [0, 1]}}]}
    row = {"x_num": 1, "x_den": 2, "expected_num": 1 << 200, "unused": "z"}
    assert _miss(chain, row=row) is not _NATIVE_MISS
    assert _run_spec(chain, row=row) == _run_pure(chain, row=row) == (1, 2)


# ---------------------------------------------------------------------
# (d) Edge — a mid-chain error propagates identically (C returns non-OK,
#     the pure path raises the exact exception).
# ---------------------------------------------------------------------


def test_mid_chain_division_by_zero_raises_on_both():
    """A zero divisor mid-chain: C returns non-OK → the pure path raises the
    exact ZeroDivisionError."""
    chain = {"name": "z", "summary": "s", "returns": "q", "steps": [
        {"class": "N", "op": "rational_add", "args": {"a": [1, 2], "b": [1, 2]}},
        {"class": "N", "op": "rational_div",
         "args": {"a": "@step[0].output", "b": [0, 1]}},
    ]}
    with pytest.raises(ZeroDivisionError):
        _run_spec(chain)
    with pytest.raises(ZeroDivisionError):
        _run_pure(chain)


def test_unknown_op_raises_chainspecerror_on_both():
    """An op that does not exist on the Class-N module raises ChainSpecError at
    resolve time on BOTH paths (before the run loop)."""
    chain = {"name": "x", "summary": "s", "returns": "q",
             "steps": [{"class": "N", "op": "definitely_not_an_op",
                        "args": {"a": [1, 1], "b": [1, 1]}}]}
    with pytest.raises(compose.ChainSpecError):
        _run_spec(chain)
    with pytest.raises(compose.ChainSpecError):
        _run_pure(chain)


# ---------------------------------------------------------------------
# Consumer re-verify — the catalog surface stays byte-identical.
# ---------------------------------------------------------------------


def test_consumer_run_catalog_chain_native_equals_pure():
    """catalog.run_catalog_chain routes through compose.run_chain → native ==
    pure on the real shipped rows."""
    for src, chain, ridx in _SHIPPED_RUNS[:6]:
        native = catalog.run_catalog_chain(src, chain, row_index=ridx)
        pure = _force_pure(catalog.run_catalog_chain, src, chain, row_index=ridx)
        assert native == pure


def test_consumer_list_catalog_chains_native_equals_pure():
    """list_catalog_chains is descriptor-only (no run loop) — stays identical."""
    listing = catalog.list_catalog_chains("pi_digits")
    pure = _force_pure(catalog.list_catalog_chains, "pi_digits")
    assert listing == pure
    assert listing.get("ok") is True and listing.get("n_chains", 0) >= 1
