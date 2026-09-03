"""rc202 — run_class_method -> C: the STATELESS one-shot, proven vs the pure surface.

srmech_run_class_method (bound as srmech._native.run_class_method_c) is the C
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
  CDRegister:             its whole surface, in
                          tests/test_cd_register_engine_c_rc464.py (rc464,
                          `#T1188`) -- the 16-slot register it replaces was
                          proved here and its coverage moved with it
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

from srmech import _native
from srmech.cascade.one import the_one
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
    for name in ("One", "Genome", "Hurwitz", "CDRegister"):
        got = lib.srmech_class_descriptor_lookup(name.encode(), ctypes.byref(n))
        assert got is not None and n.value > 0, f"{name} must resolve in C"
        assert got.startswith(b"#") or b"[class]" in got  # the descriptor text
    assert lib.srmech_class_descriptor_lookup(b"NotARealClass",
                                              ctypes.byref(n)) is None


# ── rc359 (`#T1009`): the descriptor BODY, not just the NAME ──────────────────
#
# The test ABOVE is a NAME witness: it asserts a blob comes back and that the
# blob starts with `#` or contains `[class]`. Every descriptor in the tree
# satisfies that, and would keep satisfying it if its CONTENT rotted entirely.
#
# That gap is load-bearing rather than cosmetic. The four class TOMLs bake 29
# DOTTED OP REFS into the C registry, all under `srmech.biology.genome.*` or
# `srmech.cascade.*`. If those prefixes are ever renamed and the class
# registry is not regenerated (or the .so not rebuilt), C keeps resolving
# "One" to a descriptor whose op refs point at names that no longer exist,
# `b"[class]" in got` still passes, and the PURE path keeps answering because
# srmech/dsl reads the TOML off disk. C dispatch is broken; nothing is red.
#
# Carrier and responsion have had byte-identity ratchets since rc205 / rc225.
# These three give CLASS the same standard.

def _catalog_dir():
    """The packaged class_catalog directory, via the package itself.

    Deliberately NOT a `parents[2]` reach: resolving through the imported
    package keeps this test inside `docs/srmech/python/**` for the rc359
    SCAN_ROOTS / CI-trigger invariant.
    """
    from pathlib import Path
    from srmech.cascade.catalogs import class_catalog
    return Path(class_catalog.__file__).resolve().parent


def _on_disk_descriptors():
    return {p.stem: p.read_text(encoding="utf-8")
            for p in sorted(_catalog_dir().glob("*.toml"))}


@pytest.mark.skipif(not _native.has_native_class_registry(),
                    reason="rc359 class-registry enumeration accessors not built")
def test_c_class_registry_enumerates_exactly_the_shipped_catalog():
    """C must carry the SAME SET of classes the catalog ships.

    Lookup-by-name can only confirm names the caller already holds, so it can
    never see a class that exists on disk but was never compiled in (or the
    reverse). Enumeration can.
    """
    names_c = _native.class_registry_names_c()
    assert names_c is not None
    disk = _on_disk_descriptors()
    # The TOML stem is snake_case; the [class].name is CamelCase. Compare on
    # the descriptor TEXT's own declared name to avoid encoding a mapping.
    assert len(names_c) == len(disk), (
        f"C carries {len(names_c)} class descriptors {sorted(names_c)} but the "
        f"catalog ships {len(disk)} TOMLs {sorted(disk)} — one side is stale. "
        f"Regenerate (python3 tools/regen_all.py) AND rebuild the library.")
    assert len(set(names_c)) == len(names_c), "duplicate class name in the C table"


@pytest.mark.skipif(not _native.has_native_class_registry(),
                    reason="rc359 class-registry enumeration accessors not built")
def test_c_class_descriptor_bodies_are_byte_identical_to_the_catalog():
    """CONTENT ratchet: the compiled bytes ARE the on-disk descriptor.

    This is the assertion a stale `.so` cannot survive — and the one a
    prefix-rename that skips the class registry cannot survive either.
    """
    disk_texts = set(_on_disk_descriptors().values())
    n = _native.class_registry_count_c()
    for i in range(n):
        d = _native.class_descriptor_c(i)
        assert d is not None
        assert d["toml_len"] == len(d["toml"].encode("utf-8")), (
            f"{d['name']}: declared toml_len {d['toml_len']} != actual "
            f"{len(d['toml'].encode('utf-8'))} bytes")
        assert d["toml"] in disk_texts, (
            f"the COMPILED descriptor for {d['name']!r} is not byte-identical "
            f"to any on-disk .toml. Either c/src/srmech_class_registry.c is "
            f"stale against the catalog (run tools/regen_all.py), or the "
            f"LIBRARY is stale against the generated .c (rebuild + reinstall "
            f"libsrmech). The name still resolves, which is why nothing else "
            f"fails.")


@pytest.mark.skipif(not _native.has_native_class_registry(),
                    reason="rc359 class-registry enumeration accessors not built")
def test_every_dotted_op_ref_baked_into_c_still_resolves():
    """ADR-0010's PREREQUISITE, stated as a test.

    The op refs compiled into the C registry must name callables that exist.
    A rename of `srmech.biology.genome.*` / `srmech.cascade.*` that updates
    the Python surface but not this table leaves C dispatching to dead names;
    this is the assertion that goes red for it.

    It must land BEFORE that rename, not with it: an instrument built in the
    same change it is meant to police has no green baseline, so a red would be
    unattributable.
    """
    import importlib
    import re as _re

    refs = set()
    for i in range(_native.class_registry_count_c()):
        d = _native.class_descriptor_c(i)
        # No trailing `.`: these refs appear in prose as well as in `op =`
        # values, so a greedy `[A-Za-z0-9_.]+` swallows sentence-ending periods
        # and invents refs like `srmech.biology.genome.` that never existed.
        # The prefix tracks where ADR-0010 moved the class-descriptor op refs:
        # the amsc-era ops now live under ``srmech.cascade.*`` (rc364/rc377 —
        # One / CDRegister / Hurwitz bind cascade ops) and
        # ``srmech.biology.*`` (rc375 — Genome). Was ``srmech\.amsc\.`` before
        # the arc drained amsc; keeping it would make this scan go blind.
        refs.update(_re.findall(
            r"srmech\.(?:cascade|biology)\.[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*",
            d["toml"]))
    assert refs, "decoded no dotted op refs at all — the scan has gone blind"

    broken = []
    for ref in sorted(refs):
        module, _, attr = ref.rpartition(".")
        try:
            mod = importlib.import_module(module)
        except ImportError:
            try:
                importlib.import_module(ref)      # ref IS a module
                continue
            except ImportError:
                broken.append(f"  {ref}: module {module!r} not importable")
                continue
        if not hasattr(mod, attr):
            broken.append(f"  {ref}: {module!r} has no attribute {attr!r}")

    assert not broken, (
        f"{len(broken)} op ref(s) baked into the C class registry no longer "
        f"resolve:\n" + "\n".join(broken)
        + "\n\nC dispatches on these names with no Python present. The pure "
          "path reads the TOML off disk and keeps answering, so this is the "
          "only surface that fails.")


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
    """A leaf the engine cannot emit byte-identically DEFERS through the NAME
    export exactly as it does through the descriptor export. rc331 dispatched
    One.matrix and rc335 dispatched One.flat + One.scalar via SRMECH_MVAL_BIGINT,
    so the One-adjacent engine defer that remains is Hurwitz.generate — a LIVE
    One object, not JSON, which no carrier can emit at all.

    rc464 (`#T1188`) moved the REGISTER defers (the float working word,
    is_navigable past the dense cap, the exact-Q carrier chains, an over-long
    address namespace) to tests/test_cd_register_engine_c_rc464.py, where each
    is asserted WITH the pure peer's answer beside it — which is what makes a
    defer inform-don't-limit rather than a gap."""
    dispatched, _ = _run_c("Hurwitz", "generate", {"n": 1}, {})
    assert not dispatched, "Hurwitz.generate must DEFER (a live One, not JSON)"


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
