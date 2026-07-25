"""rc202 — run_class_method -> C: the STATELESS one-shot, proven vs the pure surface.

srmech_run_class_method (bound as srmech.amsc._native.run_class_method_c) is the C
peer of srmech.dsl._class_surface.run_class_method — the FINAL owed_orchestration
row (its discharge takes CEIL_NON_COMPUTE_OWED 1 -> 0, the everything-to-C program
complete). A bare-C host RESOLVES a class NAME to its packaged [class] descriptor
(the compiled-in srmech_class_registry_table — no Python, no host-FS), runs one
method through the rc201 srmech_make_class_run engine, and WRAPS the result as
{"class", "method", "result", "fields"} byte-identical to the pure
run_class_method. The NAME->descriptor resolve is genuinely in C (the whole
construct + invoke + wrap LOGIC runs standalone).

This proves, across the three engine-covered shipped classes:
  One (plain op):         dim / imag_dims / partition / plane_counts / grammar_slots
  SedenionRegister:       navmap / slots / is_navigable / navigate (returns=self)
                          + write(mutates) / materialize / read(chain) / carry / correct
  Genome:                 add_chromosome(appends) / recall / assemble / partition

and the DEFER contract (unknown class, unknown method, an engine-deferred leaf) —
each yields (False, None) so the caller runs the pure run_class_method.

numpy-free (stdlib json + base64 + srmech) per
[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]].
"""
from __future__ import annotations

import base64
import json

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade.one import the_one
from srmech.amsc.cascade.sedenion_register import SedenionRegister
from srmech.dsl import make_class, run_class_method

pytestmark = pytest.mark.skipif(
    not _native.has_native_run_class_method(),
    reason="rc202 run_class_method C peer not built",
)


def _norm(x):
    """JSON-native normalise (the shape srmech_mcp_serialise_result emits): bytes /
    HV byte-carrier -> base64 str; a returns=self CatalogClass -> its fields;
    tuple/list -> list; dict keys -> str; recursively."""
    if isinstance(x, bytes):
        return base64.b64encode(x).decode("ascii")
    if x.__class__.__name__ == "HV":
        return base64.b64encode(bytes(x)).decode("ascii")
    if x.__class__.__name__ == "CatalogClass":
        return _norm(x.fields)
    if isinstance(x, dict):
        return {str(k): _norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_norm(e) for e in x]
    return x


def _run_c(class_name, method, fields, args):
    dispatched, text = _native.run_class_method_c(class_name, method, fields, args)
    return dispatched, (json.loads(text) if text is not None else None)


# ── the NAME->DESCRIPTOR resolve is genuinely in C (no toml text passed) ───────

def test_class_descriptor_lookup_resolves_in_c():
    """srmech_class_descriptor_lookup resolves a shipped NAME to its descriptor
    bytes IN C (the compiled-in registry); an unknown / user class -> NULL."""
    import ctypes
    lib = _native.LIB
    if not hasattr(lib, "srmech_class_descriptor_lookup"):
        pytest.skip("descriptor lookup not bound")
    n = ctypes.c_size_t(0)
    for name in ("One", "Genome", "Hurwitz", "SedenionRegister"):
        got = lib.srmech_class_descriptor_lookup(name.encode(), ctypes.byref(n))
        assert got is not None and n.value > 0, f"{name} must resolve in C"
        assert got.startswith(b"#") or b"[class]" in got  # the descriptor text
    assert lib.srmech_class_descriptor_lookup(b"NotARealClass",
                                              ctypes.byref(n)) is None


# ── One (plain-op batch): the 5 inline-constant accessors ──────────────────────

@pytest.mark.parametrize("method", [
    "dim", "imag_dims", "partition", "plane_counts", "grammar_slots",
])
def test_one_plain_accessors_match_pure(method):
    one = the_one(+1, 0, 1)
    oj = one._to_jsonable()
    dispatched, got = _run_c("One", method, {"one": oj}, {})
    assert dispatched, f"One.{method} should dispatch through run_class_method in C"

    inst = make_class("One")(one=one)
    pure_result = getattr(inst, method)()
    # One's field is a live coupling object; its JSON-native form IS what C emits.
    expected = {"class": "One", "method": method,
                "result": _norm(pure_result), "fields": {"one": oj}}
    assert got == expected


def test_one_partition_theta_variants():
    for sigma, tn, td in [(+1, 0, 1), (-1, 1, 2), (+1, 22, 7)]:
        oj = the_one(sigma, tn, td)._to_jsonable()
        dispatched, got = _run_c("One", "partition", {"one": oj}, {})
        assert dispatched
        assert got == {"class": "One", "method": "partition",
                       "result": [1, 3, 7, 3], "fields": {"one": oj}}


# ── SedenionRegister field-state carriers ──────────────────────────────────────

def _sed_pyfields(reg):
    return {"D": reg.D, "codebook": dict(reg.codebook), "slots": dict(reg._slots)}


def _sed_jsonfields(reg):
    """The JSON-native field-state a bare-C host threads."""
    return {
        "D": reg.D,
        "codebook": {k: base64.b64encode(v).decode("ascii")
                     for k, v in reg.codebook.items()},
        "slots": {str(k): [v[0], v[1]] for k, v in reg._slots.items()},
    }


def _make_reg():
    r = SedenionRegister(D=256)
    r.write(0, "alpha")
    r.write(3, "beta", sign=-1)
    r.write(6, "gamma")
    return r


def _sed_expect(method, args):
    """The pure run_class_method oracle (the whole 4-key dict, JSON-normalised)."""
    return _norm(run_class_method("SedenionRegister", method,
                                  fields=_sed_pyfields(_make_reg()), args=args))


@pytest.mark.parametrize("method,args", [
    ("navmap", {"j": 0}), ("navmap", {"j": 7}), ("navmap", {"j": 15}),
    ("slots", {}),
])
def test_sed_plain_reads_match_pure(method, args):
    dispatched, got = _run_c("SedenionRegister", method,
                             _sed_jsonfields(_make_reg()), args)
    assert dispatched, f"sed.{method} should dispatch in C"
    assert got == _sed_expect(method, args)
    assert got["class"] == "SedenionRegister" and got["method"] == method


def test_sed_is_navigable_matches_pure():
    one_hot = [0, 1] + [0] * 14                     # e1 — always navigable
    args = {"direction": one_hot}
    dispatched, got = _run_c("SedenionRegister", "is_navigable",
                             _sed_jsonfields(_make_reg()), args)
    assert dispatched
    assert got == _sed_expect("is_navigable", args)
    assert got["result"] is True


@pytest.mark.parametrize("j", [1, 2, 7])
def test_sed_navigate_returns_self_matches_pure(j):
    args = {"j": j}
    dispatched, got = _run_c("SedenionRegister", "navigate",
                             _sed_jsonfields(_make_reg()), args)
    assert dispatched
    assert got == _sed_expect("navigate", args)
    # returns='self': result is the NEW register's state; self (fields) untouched
    assert got["fields"] == _sed_jsonfields(_make_reg())
    assert got["result"]["codebook"] == _sed_jsonfields(_make_reg())["codebook"]


@pytest.mark.parametrize("slot,key,extra", [
    (1, "x", {}),
    (2, "delta", {"sign": 1}),
    (5, "eps", {"sign": -1}),
    (0, "alpha", {}),                               # overwrite an existing slot
    (3, "gamma", {}),                               # re-key to an existing key
])
def test_sed_write_mutates_matches_pure(slot, key, extra):
    args = {"slot": slot, "key": key}
    args.update(extra)
    dispatched, got = _run_c("SedenionRegister", "write",
                             _sed_jsonfields(_make_reg()), args)
    assert dispatched, "sed.write must dispatch (mutates route)"
    assert got == _sed_expect("write", args)
    assert got["result"] is None
    assert set(got["fields"]) == {"D", "codebook", "slots"}


def test_sed_materialize_matches_pure():
    dispatched, got = _run_c("SedenionRegister", "materialize",
                             _sed_jsonfields(_make_reg()), {})
    assert dispatched
    assert got == _sed_expect("materialize", {})


@pytest.mark.parametrize("slot", [0, 3, 6, 1, 2, 7, 15])
def test_sed_read_chain_matches_pure(slot):
    args = {"slot": slot}
    dispatched, got = _run_c("SedenionRegister", "read",
                             _sed_jsonfields(_make_reg()), args)
    assert dispatched, "sed.read must dispatch (chain route)"
    assert got == _sed_expect("read", args)


@pytest.mark.parametrize("bits", [[1, 0, 1, 1], [0, 0, 0, 0], [1, 1, 1, 1]])
def test_sed_carry_matches_pure(bits):
    args = {"overflow_bits": bits}
    dispatched, got = _run_c("SedenionRegister", "carry",
                             _sed_jsonfields(_make_reg()), args)
    assert dispatched
    assert got == _sed_expect("carry", args)


@pytest.mark.parametrize("codeword", [
    [1, 0, 1, 0, 1, 0, 1], [0, 1, 1, 0, 0, 1, 1], [0, 0, 0, 0, 0, 0, 0],
])
def test_sed_correct_matches_pure(codeword):
    args = {"codeword": codeword}
    dispatched, got = _run_c("SedenionRegister", "correct",
                             _sed_jsonfields(_make_reg()), args)
    assert dispatched
    assert got == _sed_expect("correct", args)


# ── Genome field-state carriers ────────────────────────────────────────────────

_ONE_G = bytes([1, 2, 3, 0, 1, 2, 3, 0])            # a leaf_dim=8 Klein-4 coupling
_LA = bytes([0, 1, 2, 3, 3, 2, 1, 0])
_LB = bytes([2, 2, 2, 2, 1, 1, 1, 1])
_LC = bytes([3, 3, 0, 0, 1, 1, 2, 2])


def _b64(b):
    return base64.b64encode(bytes(b)).decode("ascii")


def _gen_jsonfields(chromosomes=None):
    f = {"coupling": _b64(_ONE_G)}
    if chromosomes is not None:
        f["chromosomes"] = chromosomes
    return f


@pytest.mark.parametrize("label,leaves", [
    ("astro", [_LA, _LB]),
    ("bio", [_LC]),
    ("solo", [_LA]),
    ("empty", []),
])
def test_genome_add_chromosome_appends_matches_pure(label, leaves):
    g = make_class("Genome")(coupling=_ONE_G)
    result = g.add_chromosome(leaves=leaves, label=label)
    expected = {"class": "Genome", "method": "add_chromosome",
                "result": _norm(result), "fields": _norm(g.fields)}
    args = {"leaves": [_b64(x) for x in leaves], "label": label}
    dispatched, got = _run_c("Genome", "add_chromosome", _gen_jsonfields(), args)
    assert dispatched, "genome.add_chromosome must dispatch (appends route)"
    assert got == expected
    assert got["fields"]["chromosomes"] == [got["result"]]


def test_genome_recall_matches_pure():
    g = make_class("Genome")(coupling=_ONE_G)
    ch = g.add_chromosome(leaves=[_LA, _LB], label="astro")
    strand_b64 = [_b64(x) for x in ch]
    tel_b64 = _b64(g.cap(label="astro"))
    rec = g.recall(strand=ch, telomere=g.cap(label="astro"))
    expected = {"class": "Genome", "method": "recall",
                "result": _norm(rec), "fields": _norm(g.fields)}
    dispatched, got = _run_c("Genome", "recall", _gen_jsonfields([strand_b64]),
                             {"strand": strand_b64, "telomere": tel_b64})
    assert dispatched
    assert got == expected


def test_genome_assemble_matches_pure():
    g = make_class("Genome")(coupling=_ONE_G)
    asm = g.assemble(kernels={"astro": [_LA, _LB], "bio": [_LC]})
    expected = {"class": "Genome", "method": "assemble",
                "result": _norm(asm), "fields": _norm(g.fields)}
    kern = {"astro": [_b64(_LA), _b64(_LB)], "bio": [_b64(_LC)]}
    dispatched, got = _run_c("Genome", "assemble", _gen_jsonfields(),
                             {"kernels": kern})
    assert dispatched
    assert got == expected


@pytest.mark.parametrize("labels", [
    None, ["astro"], ["bio", "astro"], ["astro", "astro"], ["missing"],
])
def test_genome_partition_matches_pure(labels):
    g = make_class("Genome")(coupling=_ONE_G)
    asm = g.assemble(kernels={"astro": [_LA, _LB], "bio": [_LC]})
    asm_b64 = [_b64(x) for x in asm]
    part = g.partition(strand=asm, labels=labels)
    expected = {"class": "Genome", "method": "partition",
                "result": _norm(part), "fields": _norm(g.fields)}
    dispatched, got = _run_c("Genome", "partition", _gen_jsonfields(),
                             {"strand": asm_b64, "labels": labels})
    assert dispatched
    assert got == expected


# ── the DEFER contract ─────────────────────────────────────────────────────────

def test_unknown_class_defers():
    """An unknown / register_class_dir USER class does not resolve in the
    compiled-in registry -> DEFER (caller runs the pure run_class_method)."""
    assert _native.run_class_method_c("NotARealClass", "dim", {}, {}) == (False, None)


def test_unknown_method_defers():
    oj = the_one(+1, 0, 1)._to_jsonable()
    assert _native.run_class_method_c("One", "nope", {"one": oj}, {}) == (False, None)


def test_engine_deferred_leaves_defer():
    """A leaf the mval carrier cannot emit byte-identically DEFERS — exactly as
    make_class_run defers it. (rc331 dispatched One.matrix; rc335 dispatched
    One.flat + One.scalar via SRMECH_MVAL_BIGINT — so the remaining One-adjacent
    engine defer is the sed float couple/uncouple working word.)"""
    for method, args in [("couple_working", {"vals": [1.0, 2.0]}),
                         ("uncouple_working", {"octonion": [1.0, 2.0]})]:
        dispatched, _ = _run_c("SedenionRegister", method,
                               _sed_jsonfields(_make_reg()), args)
        assert not dispatched, f"sed.{method} must DEFER (float working word)"


# ── rc335 (#948/#887): One.flat + One.scalar DISPATCH byte-identically ─────────

@pytest.mark.parametrize("sigma,tn,td,terms", [
    (+1, 1, 2, 24), (-1, 1, 2, 24), (+1, 0, 1, 24), (+1, 355, 113, 30),
])
def test_one_flat_run_class_method_dispatches(sigma, tn, td, terms):
    """run_class_method (class NAME resolved IN C) dispatches One.flat — the 4-key
    {"class","method","result","fields"} wrap byte-identical to the pure emit
    (LIST[14] of LIST[2] of SRMECH_MVAL_BIGINT, incl. the ~249-bit case)."""
    from srmech.mcp._coercion import serialise_native
    one = the_one(sigma, tn, td, terms)
    oj = one._to_jsonable()
    dispatched, text = _native.run_class_method_c("One", "flat", {"one": oj}, {})
    assert dispatched, f"run_class_method One.flat must DISPATCH ({sigma},{tn}/{td})"
    expected = {"class": "One", "method": "flat",
                "result": serialise_native(one.to_flat_rational()),
                "fields": {"one": oj}}
    assert text == json.dumps(expected, separators=(",", ":"))


@pytest.mark.parametrize("kwargs", [
    {}, {"mode": "trace"}, {"mode": "sqnorm"},
    {"mode": "component", "index": 3}, {"mode": "component", "index": 13},
])
def test_one_scalar_run_class_method_dispatches(kwargs):
    """run_class_method dispatches One.scalar across all three modes — byte-
    identical to the pure emit (LIST[2] of SRMECH_MVAL_BIGINT [num, den]). The
    scalar carrier is a Q; the expected is built via serialise_native, NOT _norm."""
    from srmech.mcp._coercion import serialise_native
    one = the_one(+1, 1, 2, 24)
    oj = one._to_jsonable()
    dispatched, text = _native.run_class_method_c("One", "scalar", {"one": oj}, kwargs)
    assert dispatched, f"run_class_method One.scalar must DISPATCH ({kwargs})"
    expected = {"class": "One", "method": "scalar",
                "result": serialise_native(one.to_scalar(**kwargs)),
                "fields": {"one": oj}}
    assert text == json.dumps(expected, separators=(",", ":"))
