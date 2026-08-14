"""rc201b — the make_class HEAVY-carrier vtable + state-route machinery in C.

srmech_make_class_run (bound as srmech._native.make_class_run_c) is the C
peer of the compute half of srmech.dsl._class_catalog.CatalogClass. rc201 proved
the plain + returns="self" spine; rc201b wires the HEAVY leaves + the remaining
state-route machinery and proves each method dispatches BYTE-IDENTICAL to the
pure CatalogClass object model, across the two rich classes:

  SedenionRegister:
    write        -> mutates=["slots","codebook"]  (mint VAL:key + slot record)
    materialize  -> plain BYTES  (bundle_k bind(ADDR[k], value_k) over sorted slots)
    read         -> a 2-stage CHAIN (unbind -> nearest-codebook clean -> (key, sign))
    carry        -> plain LIST[int]  (Hamming(2ⁿ−1) encode)
    correct      -> plain DICT       (Hamming decode + correct)
  Genome:
    add_chromosome -> appends="chromosomes"  (CHROM cap + coupled leaves)
    recall / assemble / partition -> plain reads (leaf/dict recovery)

Every wired leaf composes the shipped C peers (srmech_mint_vector + srmech_hdc_*
+ srmech_genome_* + srmech_hamming_*); its canonical-JSON emission is byte-
identical to the pure make_class. The One bignum leaves (exact rationals overflow
the int64 mval carrier) + the float couple/uncouple + the host-FS save/load STILL
defer — see test_make_class_engine_c_rc201.py::test_heavy_leaves_defer_to_pure.

numpy-free (stdlib json + base64 + srmech) per
[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]].
"""
from __future__ import annotations

import base64
import json

import pytest

from srmech import _native
from srmech.cascade.sedenion_register import SedenionRegister
from srmech.dsl import make_class
from srmech.dsl._class_catalog import CLASS_CATALOG_DIR

pytestmark = pytest.mark.skipif(
    not _native.has_native_make_class(),
    reason="make_class engine C peer not built",
)

_SED_TOML = (CLASS_CATALOG_DIR / "sedenion_register.toml").read_text(encoding="utf-8")
_GEN_TOML = (CLASS_CATALOG_DIR / "genome.toml").read_text(encoding="utf-8")


def _norm(x):
    """JSON-native normalise (the same shape srmech_mcp_serialise_result emits):
    bytes / HV byte-carrier -> base64 str; a returns=self CatalogClass -> its
    fields; tuple/list -> list; dict keys -> str; recursively."""
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


def _run_c(toml, method, fields, args):
    dispatched, text = _native.make_class_run_c(toml, method, fields, args)
    return dispatched, (json.loads(text) if text is not None else None)


# ── SedenionRegister field-state carriers ──────────────────────────────────

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
    """The pure make_class oracle: run the method, capture (result, post-fields)."""
    inst = make_class("SedenionRegister")(**_sed_pyfields(_make_reg()))
    result = getattr(inst, method)(**args)
    return {"result": _norm(result), "fields": _norm(inst.fields)}


# ── sed write (mutates route) ──────────────────────────────────────────────

@pytest.mark.parametrize("slot,key,extra", [
    (1, "x", {}),
    (2, "delta", {"sign": 1}),
    (5, "eps", {"sign": -1}),
    (0, "alpha", {}),               # overwrite an existing slot (key already minted)
    (3, "gamma", {}),               # re-key an existing slot to an existing key
])
def test_sed_write_mutates_matches_pure(slot, key, extra):
    args = {"slot": slot, "key": key}
    args.update(extra)
    dispatched, got = _run_c(_SED_TOML, "write", _sed_jsonfields(_make_reg()), args)
    assert dispatched, "sed.write must dispatch (mutates route)"
    assert got == _sed_expect("write", args)
    # the mutates route returns None + replaces the slots + codebook fields
    assert got["result"] is None
    assert set(got["fields"]) == {"D", "codebook", "slots"}


# ── sed materialize (plain BYTES) ──────────────────────────────────────────

def test_sed_materialize_matches_pure():
    dispatched, got = _run_c(_SED_TOML, "materialize", _sed_jsonfields(_make_reg()), {})
    assert dispatched
    assert got == _sed_expect("materialize", {})


# ── sed read (the 2-stage CHAIN) ───────────────────────────────────────────

@pytest.mark.parametrize("slot", [0, 3, 6, 1, 2, 7, 15])
def test_sed_read_chain_matches_pure(slot):
    dispatched, got = _run_c(_SED_TOML, "read", _sed_jsonfields(_make_reg()), {"slot": slot})
    assert dispatched, "sed.read must dispatch (the chain route)"
    assert got == _sed_expect("read", {"slot": slot})


def test_sed_read_empty_register_matches_pure():
    empty = make_class("SedenionRegister")(D=256, codebook={}, slots={})
    exp = {"result": _norm(empty.read(slot=0)), "fields": _norm(empty.fields)}
    dispatched, got = _run_c(_SED_TOML, "read",
                             {"D": 256, "codebook": {}, "slots": {}}, {"slot": 0})
    assert dispatched
    assert got == exp
    assert got["result"] == [None, 1]


# ── sed carry / correct (Hamming) ──────────────────────────────────────────

@pytest.mark.parametrize("bits", [[1, 0, 1, 1], [0, 0, 0, 0], [1, 1, 1, 1], [0, 1, 0, 1]])
def test_sed_carry_matches_pure(bits):
    dispatched, got = _run_c(_SED_TOML, "carry", _sed_jsonfields(_make_reg()),
                             {"overflow_bits": bits})
    assert dispatched
    assert got == _sed_expect("carry", {"overflow_bits": bits})


@pytest.mark.parametrize("codeword", [
    [1, 0, 1, 0, 1, 0, 1], [0, 1, 1, 0, 0, 1, 1], [1, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0],
])
def test_sed_correct_matches_pure(codeword):
    dispatched, got = _run_c(_SED_TOML, "correct", _sed_jsonfields(_make_reg()),
                             {"codeword": codeword})
    assert dispatched
    assert got == _sed_expect("correct", {"codeword": codeword})


# ── Genome field-state carriers ────────────────────────────────────────────

_ONE_G = bytes([1, 2, 3, 0, 1, 2, 3, 0])         # a leaf_dim=8 Klein-4 coupling
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


# ── genome add_chromosome (appends route) ──────────────────────────────────

@pytest.mark.parametrize("label,leaves", [
    ("astro", [_LA, _LB]),
    ("bio", [_LC]),
    ("solo", [_LA]),
    ("empty", []),
])
def test_genome_add_chromosome_appends_matches_pure(label, leaves):
    g = make_class("Genome")(coupling=_ONE_G)
    result = g.add_chromosome(leaves=leaves, label=label)
    exp = {"result": _norm(result), "fields": _norm(g.fields)}
    args = {"leaves": [_b64(x) for x in leaves], "label": label}
    dispatched, got = _run_c(_GEN_TOML, "add_chromosome", _gen_jsonfields(), args)
    assert dispatched, "genome.add_chromosome must dispatch (appends route)"
    assert got == exp
    # the appends route grows the chromosomes field by one entry
    assert got["fields"]["chromosomes"] == [got["result"]]


# ── genome recall / assemble / partition (reads) ───────────────────────────

def test_genome_recall_matches_pure():
    g = make_class("Genome")(coupling=_ONE_G)
    ch = g.add_chromosome(leaves=[_LA, _LB], label="astro")
    strand_b64 = [_b64(x) for x in ch]
    tel_b64 = _b64(g.cap(label="astro"))
    rec = g.recall(strand=ch, telomere=g.cap(label="astro"))
    exp = {"result": _norm(rec), "fields": _norm(g.fields)}
    dispatched, got = _run_c(_GEN_TOML, "recall",
                             _gen_jsonfields([strand_b64]),
                             {"strand": strand_b64, "telomere": tel_b64})
    assert dispatched
    assert got == exp


def test_genome_assemble_matches_pure():
    g = make_class("Genome")(coupling=_ONE_G)
    asm = g.assemble(kernels={"astro": [_LA, _LB], "bio": [_LC]})
    exp = {"result": _norm(asm), "fields": _norm(g.fields)}
    kern = {"astro": [_b64(_LA), _b64(_LB)], "bio": [_b64(_LC)]}
    dispatched, got = _run_c(_GEN_TOML, "assemble", _gen_jsonfields(), {"kernels": kern})
    assert dispatched
    assert got == exp


@pytest.mark.parametrize("labels", [
    None, ["astro"], ["bio", "astro"], ["astro", "astro"], ["missing"], ["astro", "bio"],
])
def test_genome_partition_matches_pure(labels):
    """partition's dict semantics — strand order (labels=None) OR the labels=
    order (dedup, filtered) — replicated byte-identically in C."""
    g = make_class("Genome")(coupling=_ONE_G)
    asm = g.assemble(kernels={"astro": [_LA, _LB], "bio": [_LC]})
    asm_b64 = [_b64(x) for x in asm]
    part = g.partition(strand=asm, labels=labels)
    exp = {"result": _norm(part), "fields": _norm(g.fields)}
    dispatched, got = _run_c(_GEN_TOML, "partition", _gen_jsonfields(),
                             {"strand": asm_b64, "labels": labels})
    assert dispatched
    assert got == exp
