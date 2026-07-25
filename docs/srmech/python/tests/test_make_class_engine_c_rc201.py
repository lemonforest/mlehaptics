"""rc201 — the make_class OBJECT-MODEL ENGINE in C, proven vs the pure CatalogClass.

srmech_make_class_run (bound as srmech.amsc._native.make_class_run_c) is the C
peer of the compute half of srmech.dsl._class_catalog.CatalogClass: a bare-C host
constructs a DSL [class] instance from its packaged TOML descriptor + a field-
state map and RUNS its declared methods natively. This proves the rc201 ENGINE
BATCH runs each method BYTE-IDENTICAL / value-identical to the pure CatalogClass
(the make_class object model), across TWO of the four shipped classes:

  One (plain op):  dim / imag_dims / partition / plane_counts / grammar_slots
  SedenionRegister: navmap / slots / is_navigable (plain) + navigate (returns=self)

and that every OTHER method DEFERS to pure (the rc103 inform-don't-limit contract
the heavy-carrier leaf batch — the One bignum leaves, the genome byte/disk leaves,
the sed HDC-storage leaves — rides until rc201b/rc202).

numpy-free (stdlib json + base64 + srmech). The whole test is numpy-free per
[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]].
"""
from __future__ import annotations

import base64
import json

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade.one import the_one
from srmech.amsc.cascade.sedenion_register import SedenionRegister
from srmech.dsl import make_class
from srmech.dsl._class_catalog import CLASS_CATALOG_DIR, CatalogClass

pytestmark = pytest.mark.skipif(
    not _native.has_native_make_class(),
    reason="rc201 make_class engine C peer not built",
)

_ONE_TOML = (CLASS_CATALOG_DIR / "one.toml").read_text(encoding="utf-8")
_SED_TOML = (CLASS_CATALOG_DIR / "sedenion_register.toml").read_text(encoding="utf-8")


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


# ── SedenionRegister (plain + returns="self") ──────────────────────────────

def _sed_fields(reg: SedenionRegister) -> dict:
    """The JSON-native field-state a bare-C host threads (D / base64 codebook /
    "slot" -> [key, sign] slots) — the srmech_mval_t DICT carrier shape."""
    return {
        "D": reg.D,
        "codebook": {k: base64.b64encode(v).decode("ascii")
                     for k, v in reg.codebook.items()},
        "slots": {str(k): [v[0], v[1]] for k, v in reg._slots.items()},
    }


def _make_reg() -> SedenionRegister:
    r = SedenionRegister(D=256)
    r.write(0, "alpha")
    r.write(3, "beta", sign=-1)
    r.write(6, "gamma")
    return r


@pytest.mark.parametrize("j", [0, 1, 2, 7, 15])
def test_sed_navmap_matches_pure(j):
    reg = _make_reg()
    dispatched, got = _run_c(_SED_TOML, "navmap", _sed_fields(reg), {"j": j})
    assert dispatched
    inst = make_class("SedenionRegister")(**_pyfields(reg))
    expected = {"result": _norm(inst.navmap(j=j)),
                "fields": _norm(_pyfields_state(reg))}
    assert got["result"] == expected["result"]


def test_sed_slots_matches_pure():
    reg = _make_reg()
    dispatched, got = _run_c(_SED_TOML, "slots", _sed_fields(reg), {})
    assert dispatched
    inst = make_class("SedenionRegister")(**_pyfields(reg))
    assert got["result"] == _norm(inst.slots())


def test_sed_is_navigable_matches_pure():
    reg = _make_reg()
    one_hot = [0, 1] + [0] * 14                 # e1 — always navigable
    dispatched, got = _run_c(_SED_TOML, "is_navigable",
                             _sed_fields(reg), {"direction": one_hot})
    assert dispatched
    inst = make_class("SedenionRegister")(**_pyfields(reg))
    assert got["result"] == inst.is_navigable(direction=one_hot) is True


@pytest.mark.parametrize("j", [1, 2, 7])
def test_sed_navigate_returns_self_matches_pure(j):
    """The returns='self' route: navigate builds a NEW register (self untouched).
    The C engine emits the new instance's {D, codebook, slots} field DICT as
    'result'; 'fields' stays the (unchanged) self state."""
    reg = _make_reg()
    fields = _sed_fields(reg)
    dispatched, got = _run_c(_SED_TOML, "navigate", fields, {"j": j})
    assert dispatched

    inst = make_class("SedenionRegister")(**_pyfields(reg))
    new_inst = inst.navigate(j=j)
    assert isinstance(new_inst, CatalogClass)          # returns='self' contract
    assert got["result"] == _norm(new_inst.fields)     # the NEW register's state
    assert got["fields"] == fields                     # self untouched
    # the codebook rides through unchanged (navigate routes only the names)
    assert got["result"]["codebook"] == fields["codebook"]


# ── the DEFER contract (the leaves the mval carrier can't emit byte-identically) ──

def test_heavy_leaves_defer_to_pure():
    """rc201b wired the byte-representable heavy leaves (sed write/materialize/
    read/carry/correct + genome chromosome/recall/genome/partition); rc331 (#948
    Thread B) wired One.matrix (the MAT carrier + correctly-rounded cos/sin). What
    STILL defers is exactly what the int64/bytes mval carrier cannot emit byte-
    identically: the One bignum leaves (flat/scalar exact rationals overflow int64)
    + the float couple/uncouple working word.
    (rc103 inform-don't-limit: pure runs these, never a wrong answer.)"""
    oj = the_one(+1, 1, 2)._to_jsonable()
    for method in ["flat", "scalar"]:                      # One bignum leaves (matrix now dispatches)
        dispatched, _ = _run_c(_ONE_TOML, method, {"one": oj}, {})
        assert not dispatched, f"One.{method} must DEFER (bignum, not int64-emit)"
    reg = _make_reg()
    fields = _sed_fields(reg)
    for method, args in [("couple_working", {"vals": [1.0, 2.0]}),
                         ("uncouple_working", {"octonion": [1.0, 2.0]})]:
        dispatched, _ = _run_c(_SED_TOML, method, fields, args)
        assert not dispatched, f"Sed.{method} must DEFER (float working word)"


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


def test_unknown_method_and_class_defer():
    oj = the_one(+1, 0, 1)._to_jsonable()
    assert _native.make_class_run_c(_ONE_TOML, "nope", {"one": oj}, {}) == (False, None)
    assert _native.make_class_run_c("not toml at all", "dim", {}, {}) == (False, None)


# ── helpers: build the pure CatalogClass field kwargs from a live register ──

def _pyfields(reg: SedenionRegister) -> dict:
    return {"D": reg.D, "codebook": dict(reg.codebook),
            "slots": dict(reg._slots)}


def _pyfields_state(reg: SedenionRegister) -> dict:
    return {"D": reg.D, "codebook": dict(reg.codebook),
            "slots": {k: list(v) for k, v in reg._slots.items()}}
