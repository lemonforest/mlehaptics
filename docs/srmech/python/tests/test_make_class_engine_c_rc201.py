"""rc201 — the make_class OBJECT-MODEL ENGINE in C, proven vs the pure CatalogClass.

srmech_make_class_run (bound as srmech._native.make_class_run_c) is the C
peer of the compute half of srmech.dsl._class_catalog.CatalogClass: a bare-C host
constructs a DSL [class] instance from its packaged TOML descriptor + a field-
state map and RUNS its declared methods natively. This proves the rc201 ENGINE
BATCH runs each method BYTE-IDENTICAL / value-identical to the pure CatalogClass
(the make_class object model), across TWO of the four shipped classes:

  One (plain op):  dim / imag_dims / partition / plane_counts / grammar_slots

and that every OTHER method DEFERS to pure (the rc103 inform-don't-limit
contract the heavy-carrier leaf batch rides until rc201b/rc202).

rc464 (`#T1188`) MOVED the register half of this module. It proved the
16-slot register's four addressing methods and the engine's DEFER contract
against them; the 16-slot class is gone and the GENERAL CDRegister replaces
it, so that coverage now lives in tests/test_cd_register_engine_c_rc464.py --
same routes, both exports, at dim 16 AND dim 256. Deleting rather than
re-pointing here is deliberate: two modules asserting the same dispatch
would read as two independent proofs and be one.

numpy-free (stdlib json + base64 + srmech). The whole test is numpy-free per
[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]].
"""
from __future__ import annotations

import base64
import json

import pytest

from srmech import _native
from srmech.cascade.one import the_one
from srmech.dsl import make_class
from srmech.dsl._class_catalog import CLASS_CATALOG_DIR, CatalogClass

pytestmark = pytest.mark.skipif(
    not _native.has_native_make_class(),
    reason="rc201 make_class engine C peer not built",
)

_ONE_TOML = (CLASS_CATALOG_DIR / "one.toml").read_text(encoding="utf-8")


def _norm(x):
    """JSON-native normalise: bytes -> base64 str, tuple/list -> list, dict keys
    -> str, recursively — the same shape srmech_mcp_serialise_result emits."""
    if isinstance(x, bytes):
        return base64.b64encode(x).decode("ascii")
    if isinstance(x, dict):
        return {str(k): _norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_norm(e) for e in x]
    return x


def _run_c(toml: str, method: str, fields: dict, args: dict):
    dispatched, text = _native.make_class_run_c(toml, method, fields, args)
    return dispatched, (json.loads(text) if text is not None else None)


# ── One (plain-op batch): the 5 inline-constant accessors ──────────────────

@pytest.mark.parametrize("method", [
    "dim", "imag_dims", "partition", "plane_counts", "grammar_slots",
])
def test_one_plain_accessors_match_pure(method):
    one = the_one(+1, 0, 1)
    oj = one._to_jsonable()
    dispatched, got = _run_c(_ONE_TOML, method, {"one": oj}, {})
    assert dispatched, f"One.{method} should dispatch in the rc201 engine"

    # pure oracle: the CatalogClass make_class object model.
    inst = make_class("One")(one=one)
    pure_result = getattr(inst, method)()
    expected = {"result": _norm(pure_result), "fields": {"one": oj}}
    assert got == expected


def test_one_theta_variants_match_pure():
    for sigma, tn, td in [(+1, 0, 1), (-1, 1, 2), (+1, 22, 7)]:
        oj = the_one(sigma, tn, td)._to_jsonable()
        dispatched, got = _run_c(_ONE_TOML, "partition", {"one": oj}, {})
        assert dispatched
        assert got["result"] == [1, 3, 7, 3]
        assert got["fields"] == {"one": oj}


# ── rc331 (#948 Thread B): One.matrix DISPATCHES byte-identically ──────────────

def test_one_matrix_dispatches_byte_identical():
    """One.matrix() now DISPATCHES in the make_class engine (srmech_one_matrix →
    a SRMECH_MVAL_MAT carrier, cos/sin correctly-rounded), emitting JSON BYTE-
    IDENTICAL to the pure CatalogClass emit. Includes a |value|>1 large-angle case
    (θ=27, cos ≈ 9.5e6) that the old fixed-96-bit shift mis-handled."""
    from srmech.mcp._coercion import serialise_native
    for sigma, tn, td, terms in [(+1, 1, 2, 24), (-1, 22, 7, 24),
                                 (+1, 0, 1, 24), (+1, 27, 1, 24)]:
        one = the_one(sigma, tn, td, terms)
        oj = one._to_jsonable()
        dispatched, text = _native.make_class_run_c(_ONE_TOML, "matrix", {"one": oj}, {})
        assert dispatched, f"One.matrix must DISPATCH in rc331 ({sigma},{tn}/{td},{terms})"
        pure_mat = make_class("One")(one=one).matrix()
        expected = {"result": serialise_native(pure_mat), "fields": {"one": oj}}
        assert text == json.dumps(expected, separators=(",", ":")), (sigma, tn, td, terms)
        got = json.loads(text)
        assert len(got["result"]) == 14 and all(len(r) == 14 for r in got["result"])
        assert got["fields"] == {"one": oj}


def test_one_matrix_run_class_method_dispatches():
    """srmech_run_class_method (class NAME resolved IN C) also dispatches
    One.matrix — the 4-key {"class","method","result","fields"} wrap byte-identical
    to the pure run_class_method emit."""
    if not _native.has_native_run_class_method():
        pytest.skip("rc202 run_class_method C peer not built")
    from srmech.mcp._coercion import serialise_native
    for sigma, tn, td, terms in [(+1, 1, 2, 24), (-1, 7, 3, 30)]:
        one = the_one(sigma, tn, td, terms)
        oj = one._to_jsonable()
        dispatched, text = _native.run_class_method_c("One", "matrix", {"one": oj}, {})
        assert dispatched, f"run_class_method One.matrix must DISPATCH ({sigma},{tn}/{td})"
        pure_mat = make_class("One")(one=one).matrix()
        expected = {"class": "One", "method": "matrix",
                    "result": serialise_native(pure_mat), "fields": {"one": oj}}
        assert text == json.dumps(expected, separators=(",", ":")), (sigma, tn, td, terms)


# ── rc335 (#948/#887): One.flat + One.scalar DISPATCH byte-identically ─────────

@pytest.mark.parametrize("sigma,tn,td,terms", [
    (+1, 1, 2, 24), (-1, 1, 2, 24), (+1, 0, 1, 24), (+1, 99, 100, 24),
    (+1, 355, 113, 30), (+1, 1, 1, 50), (-1, 22, 7, 40),
])
def test_one_flat_dispatches_byte_identical(sigma, tn, td, terms):
    """One.flat() now DISPATCHES in the make_class engine (srmech_the_one → 14
    exact adjoint rationals → LIST[14] of LIST[2] of SRMECH_MVAL_BIGINT), emitting
    JSON BYTE-IDENTICAL to the pure CatalogClass emit — including the ~249-bit
    (1/2, 24-term) numerators that overflow int64."""
    from srmech.mcp._coercion import serialise_native
    one = the_one(sigma, tn, td, terms)
    oj = one._to_jsonable()
    dispatched, text = _native.make_class_run_c(_ONE_TOML, "flat", {"one": oj}, {})
    assert dispatched, f"One.flat must DISPATCH in rc335 ({sigma},{tn}/{td},{terms})"
    expected = {"result": serialise_native(one.to_flat_rational()),
                "fields": {"one": oj}}
    assert text == json.dumps(expected, separators=(",", ":"))
    got = json.loads(text)
    assert len(got["result"]) == 14 and all(len(p) == 2 for p in got["result"])
    assert got["fields"] == {"one": oj}


@pytest.mark.parametrize("mode,kwargs", [
    ("trace", {}), ("trace", {"mode": "trace"}),
    ("sqnorm", {"mode": "sqnorm"}), ("component", {"mode": "component", "index": 3}),
    ("component", {"mode": "component", "index": 0}),
    ("component", {"mode": "component", "index": 13}),
])
def test_one_scalar_dispatches_byte_identical(mode, kwargs):
    """One.scalar() now DISPATCHES (srmech_one_scalar → an exact (num, den) →
    LIST[2] of SRMECH_MVAL_BIGINT), byte-identical to the pure CatalogClass emit,
    across all three modes. The scalar carrier is a Q — build the expected via
    serialise_native (the pure oracle), NOT bare _norm (which can't emit a Q)."""
    from srmech.mcp._coercion import serialise_native
    one = the_one(+1, 1, 2, 24)                 # the ~249-bit numerator case
    oj = one._to_jsonable()
    dispatched, text = _native.make_class_run_c(_ONE_TOML, "scalar", {"one": oj}, kwargs)
    assert dispatched, f"One.scalar must DISPATCH in rc335 (mode={mode})"
    pure_q = one.to_scalar(**kwargs)
    expected = {"result": serialise_native(pure_q), "fields": {"one": oj}}
    assert text == json.dumps(expected, separators=(",", ":"))


def test_one_scalar_as_float_defers():
    """as_float=True is the terminal float cast — the pure caller's job. The C
    scalar thunk DEFERS it (it emits only the exact (num, den) bignum rational)."""
    oj = the_one(+1, 1, 2, 24)._to_jsonable()
    dispatched, _ = _run_c(_ONE_TOML, "scalar", {"one": oj}, {"as_float": True})
    assert not dispatched, "One.scalar(as_float=True) must DEFER (terminal float cast)"


def test_unknown_method_and_class_defer():
    oj = the_one(+1, 0, 1)._to_jsonable()
    assert _native.make_class_run_c(_ONE_TOML, "nope", {"one": oj}, {}) == (False, None)
    assert _native.make_class_run_c("not toml at all", "dim", {}, {}) == (False, None)
