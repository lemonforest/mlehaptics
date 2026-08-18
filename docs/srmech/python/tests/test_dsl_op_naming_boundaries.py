"""The op-naming boundaries the DSL actually enforces, EXECUTED (`#T1137`).

WHY THIS FILE EXISTS
====================
Three shipped sentences taught a false boundary, and two independent outside
readers acted on it. One filed "two missing leaves" that BOTH ship (retracted a
day later). One filed a grammar gap as absolute that is true of one step grammar
and false of the other. The sentences were individually defensible; collectively
they drew a limit that is not where the code puts it.

The fix was prose, in three places::

    srmech/dsl/_catalog.py          module docstring — the dotted arm + its bound
    srmech/cascade/leaves.py        module docstring — NEIGHBOURHOOD, not vocabulary
    docs/srmech/adr/0008-*.md       the two step grammars answer differently

**Prose rots; this file is the part that cannot.** Every claim those docstrings
now make about what resolves, what does not, and where the asymmetry sits is
RE-DERIVED here by running it. A corrected sentence that silently becomes false
in the OTHER direction — "dotted names work" surviving as prose after the arm is
removed — is the same defect wearing a fix, so the dotted arm is pinned by
execution in both directions: it must resolve, AND the bare form it is contrasted
with must still be rejected.

WHAT EACH TEST PINS, AND WHY A STATIC CHECK CANNOT
==================================================
The load-bearing facts are all about RESOLUTION ORDER inside
``lookup_cascade_op`` / ``_resolve_step_op``. No name-comparison can see them:
``magnitude`` and ``srmech.cascade.magnitude`` are the SAME function object, yet
one is A-tier and the other is untiered; ``probe_double_flip`` is one string that
resolves on one grammar and raises on the other. The discriminator is which
resolver ran, and the only instrument that reports that is running it.

DIRECTION
=========
These are EQUALITIES, not ratchets — with ONE deliberate exception: the
introspection-visibility census is DOWN-ONLY (see its docstring), because
there the code side is a defect we want drained, not a contract we want
frozen. Every other test asserts the measured rc434 behaviour; a change in
either direction is a real change to the DSL's naming contract and must be a
deliberate edit here plus the three docstrings above, together.

`#T1137` ADJUDICATION (third pass)
==================================
The visibility gate originally here asserted
``resolve("srmech.cascade.leaves.seq_len") is None`` — green exactly while
the alias gap SURVIVES, red the day it is fixed: a ratchet aimed at its own
correction, pinning a false doc sentence ("visibility follows the TARGET")
with a true measurement. It is re-aimed below at the MECHANISM
(spelling-keyed resolution) plus a down-only, doc-synced census. The
adjudication also measured the dropped claim (b) TRUE at the CHAIN level (a
dotted spelling evicts the whole chain from both native run loops; the op
object is spelling-independent, which is all the earlier pass measured),
promoted "catalog names never contain a dot" from an observation to a
load-time guard (pre-guard, an importable dotted ``[cascade].name`` loaded,
listed, introspected as the user's descriptor and silently RAN the shipped
import), and pinned the ``[composite]``-body boundary of the dotted arm.
"""

from __future__ import annotations

import importlib
import os
import textwrap

import pytest

from srmech import dsl
from srmech.cascade import compose as _compose
from srmech.dsl import _catalog
from srmech.dsl._catalog import get_descriptor, lookup_cascade_op


@pytest.fixture(autouse=True)
def _reset_catalog_state():
    """Hermetic catalog: shipped-only before AND after each test.

    Mirrors ``test_byo_cascade_toml.py``. Without the ``lru_cache`` clear a
    registered dir leaks into the next test and the asymmetry probes below stop
    measuring what they claim to.
    """
    _catalog._USER_CATALOG_DIRS.clear()
    os.environ.pop("SRMECH_CASCADE_PATH", None)
    _catalog.load_catalog.cache_clear()
    try:
        yield
    finally:
        _catalog._USER_CATALOG_DIRS.clear()
        os.environ.pop("SRMECH_CASCADE_PATH", None)
        _catalog.load_catalog.cache_clear()


def _write(dirpath, fname, body):
    p = dirpath / fname
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


# A pure-TOML composite: no Python callable exists for this name ANYWHERE.
# That is what makes it a clean discriminator between the two resolvers.
_DOUBLE_FLIP = """
    [cascade]
    name = "probe_double_flip"
    class_composition = "C ∘ C"
    purpose = "two chiral flips (identity) — resolution-order probe"
    kind = "stage"

    [composite]
    [[composite.stage]]
    op = "chiral_flip"

    [[composite.stage]]
    op = "chiral_flip"
"""

# A composite whose ONLY stage names the descriptor above BY CATALOG NAME.
_OUTER = """
    [cascade]
    name = "probe_outer"
    class_composition = "C ∘ C"
    purpose = "names a sibling descriptor — descriptor-to-descriptor probe"
    kind = "stage"

    [composite]
    [[composite.stage]]
    op = "probe_double_flip"
"""

# A descriptor carrying a declared [[cascade.chain]] but NO [composite] and no
# Python callable — the state that proves a declared chain is not an execution
# path.
_CHAIN_ONLY = """
    [cascade]
    name = "probe_chainonly"
    class_composition = "C"
    purpose = "a declared chain with no [composite] and no callable"
    kind = "stage"

    [[cascade.chain]]
    chain_schema_version = 2
    summary = "reverse once"
    returns = "seq"

    [[cascade.chain.steps]]
    class = "C"
    op = "srmech.cascade.atoms.chiral_flip"
    args = { seq = "@input.seq" }
"""


# ── 1. the dotted arm, pinned in BOTH directions ──────────────────────────

def test_dotted_op_name_resolves_without_a_descriptor():
    """`srmech/dsl/_catalog.py`: a dotted step resolves by IMPORT, not lookup.

    Pins the corrected sentence against silently becoming false the other way.
    If the rc420 BLK-REGMAP dotted arm is ever removed, this fails and the
    docstring that advertises it must be edited in the same commit.
    """
    out = (dsl.chain()
           .then("builtins.set")
           .then("builtins.sorted")
           .run([3, 1, 4, 1, 5, 9, 2, 6, 5, 3]))
    assert out == [1, 2, 3, 4, 5, 6, 9]

    # and a shipped leaf that has no descriptor of its own — the arm's REASON
    assert dsl.chain().then("srmech.cascade.leaves.seq_len").run([7, 7, 7]) == 3


def test_bare_unknown_op_is_still_rejected():
    """The other half: the dotted arm did NOT open the bare form.

    A correction that reads as a general invitation would be worse than the
    original falsehood, so the rejection it is contrasted with is executed too.
    """
    with pytest.raises(ValueError, match="unknown cascade op"):
        dsl.chain().then("foo").run(1)


def test_dotted_step_has_no_descriptor_and_so_no_provenance_tier():
    """`srmech/dsl/_catalog.py`: the A/B tier is a property of the DESCRIPTOR.

    The SAME function object under two spellings: one carries provenance, the
    other carries none. No static check can see this — it is one identity.
    """
    import srmech.cascade as _cascade
    assert lookup_cascade_op("magnitude") is _cascade.magnitude
    assert lookup_cascade_op("srmech.cascade.magnitude") is _cascade.magnitude

    assert get_descriptor("magnitude")["_provenance"] == "srmech"
    with pytest.raises(ValueError, match="unknown cascade op"):
        get_descriptor("srmech.cascade.magnitude")


# ── census machinery for the visibility gate ──────────────────────────────

#: Step keys that can name an op inside a declared [[cascade.chain]].
_CHAIN_OP_KEYS = ("op", "fold_op", "reduce_op", "parallel_body", "map_op",
                  "body_op")


def _walk_chain_ops(node, sink):
    """Collect every dotted op-naming value under a chain dict, recursively
    (plain steps, fold steps, map bodies at any depth)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in _CHAIN_OP_KEYS and isinstance(v, str) and "." in v:
                sink.add(v)
            _walk_chain_ops(v, sink)
    elif isinstance(node, list):
        for item in node:
            _walk_chain_ops(item, sink)


def _shipped_dotted_chain_spellings():
    """Every distinct dotted spelling in the shipped [[cascade.chain]]s."""
    dotted: set = set()
    for desc in _catalog.load_catalog().values():
        _walk_chain_ops(desc.get("cascade", {}).get("chain", []), dotted)
    return dotted


def _import_spelling(name):
    """The object a dotted spelling imports to, or None."""
    mod_path, _, attr = name.rpartition(".")
    if not mod_path:
        return None
    try:
        mod = importlib.import_module(mod_path)
    except ImportError:
        return None
    return getattr(mod, attr, None)


#: rc434 census — shipped chain-step spellings that return ``None`` from
#: ``resolve()`` while the SAME object is registered under another name (in
#: every current case: its published ``srmech.cascade.<name>`` re-export).
#: DOWN-ONLY. Fixing the gap — respelling descriptors to the published form,
#: or object-aware resolution — DRAINS this set: the subset assert stays
#: green, and only the doc-sync figures in ``srmech/dsl/_catalog.py`` go
#: red, in the same commit, on purpose. A NEW invisible spelling fails here.
#: ⚠️ DRAINED TO EMPTY at rc448 (`#T1145`). It was seeded at 32 in rc434 and
#: held every DEFINING-MODULE spelling the shipped descriptors used. rc448
#: respelled all 85 sites across 11 descriptor files onto the published
#: ``srmech.cascade.<name>`` re-exports, so the measured invisible set is now
#: ``0`` and the census this pins is EMPTY — which is the outcome the re-aimed
#: gate was built to produce (the fix drains the ratchet; only the stale
#: ``_catalog.py`` figures go red, in the same commit, on purpose).
#:
#: EMPTY IS NOT VACUOUS. The subset assert below still fires on any NEW
#: invisible spelling, and with the seed at ``0`` it is now a STRICT ZERO:
#: a descriptor written with a defining-module path reopens the gap and goes
#: red immediately, instead of being absorbed by a 32-row allowance. Do not
#: re-seed it to "make room" for a new one — respell the descriptor.
_INVISIBLE_WHILE_TARGET_REGISTERED_RC434 = frozenset()


def test_dotted_visibility_is_spelling_keyed_and_the_shipped_gap_drains():
    """`srmech/dsl/_catalog.py`: visibility is keyed by the SPELLING.

    Re-aimed by the `#T1137` adjudication. The gate this replaces asserted
    ``resolve("srmech.cascade.leaves.seq_len") is None`` — an equality that
    would go RED the day the alias gap is FIXED: a ratchet aimed at its own
    correction. The doc's actual claims are (1) a MECHANISM — resolution
    answers name strings (exact, or a dotted-suffix shortening), never the
    callable behind them — and (2) a dated CENSUS of the gap that mechanism
    leaves across the shipped descriptors. (1) is pinned as an equality;
    (2) as a down-only subset plus a doc-sync, so a fix drains the census
    and reddens only the stale docstring figures, never the fix itself.
    """
    from srmech.introspect.tool_schema import get_tool_schema
    schema = get_tool_schema()

    dotted = _shipped_dotted_chain_spellings()
    assert dotted, "census walker found no dotted spellings — walker broke"

    obj_to_names: dict = {}
    for t in schema.tools:
        obj = _import_spelling(t.name)
        if obj is not None:
            obj_to_names.setdefault(id(obj), []).append(t.name)

    resolving, invisible, unregistered = set(), set(), set()
    for op in sorted(dotted):
        entry = schema.resolve(op)
        if entry is not None:
            # (1) MECHANISM: a hit is the exact spelling, never a rename onto
            # the target's other alias. (resolve() also answers dotted-suffix
            # SHORTENINGS like "cascade.magnitude", but a RUNNABLE spelling
            # is a full import path, which can only hit by exact match.)
            assert entry.name == op, (
                f"resolve({op!r}) returned {entry.name!r}: resolution "
                f"followed the OBJECT, not the spelling — the resolver "
                f"contract changed; rewrite the _catalog.py docstring and "
                f"this gate together, deliberately")
            resolving.add(op)
            continue
        obj = _import_spelling(op)
        assert obj is not None and callable(obj), (
            f"shipped chain step {op!r} does not even import — an "
            f"install-integrity break, not a visibility gap")
        if obj_to_names.get(id(obj)):
            invisible.add(op)
        else:
            unregistered.add(op)

    # negative control for the mechanism claim: an importable callable with
    # no registration anywhere resolves to nothing.
    assert schema.resolve("builtins.set") is None

    # (2) CENSUS — down-only.
    new = invisible - _INVISIBLE_WHILE_TARGET_REGISTERED_RC434
    assert not new, (
        f"NEW introspection-invisible chain-step spellings shipped: "
        f"{sorted(new)}. Use the published re-export spelling in the "
        f"descriptor, register the spelling, or (deliberately) extend the "
        f"pinned census AND the _catalog.py docstring figures together.")

    # (3) DOC-SYNC — the docstring's census figures must match the measured
    # census, so a DRAIN reddens the stale prose, not the fix.
    doc = _catalog.__doc__ or ""
    assert f"the {len(dotted)} distinct dotted spellings" in doc, (
        f"_catalog.py docstring census stale: measured {len(dotted)} "
        f"distinct dotted spellings in shipped [[cascade.chain]] steps")
    assert f"{len(resolving)} resolve, {len(invisible)} return ``None``" in doc, (
        f"_catalog.py docstring census stale: measured {len(resolving)} "
        f"resolving / {len(invisible)} invisible-while-target-registered — "
        f"update the docstring figures in the same commit")
    assert f"and {len(unregistered)} (the RBS-HDC" in doc, (
        f"_catalog.py docstring census stale: measured {len(unregistered)} "
        f"genuinely unregistered chain-step spelling(s)")


# ── 2. the two step grammars, executed side by side ───────────────────────

def test_composite_stage_resolves_a_sibling_descriptor(tmp_path):
    """ADR-0008: descriptor-to-descriptor reference EXISTS on `[[composite.stage]]`.

    `probe_outer`'s only stage names `probe_double_flip`, for which no Python
    callable exists anywhere — so a pass here can ONLY mean the resolver walked
    into the sibling descriptor's sub-chain.
    """
    _write(tmp_path, "double_flip.toml", _DOUBLE_FLIP)
    _write(tmp_path, "outer.toml", _OUTER)
    dsl.register_catalog_dir(str(tmp_path))

    assert list(dsl.chain().then("probe_outer").run([1, 2, 3])) == [1, 2, 3]


def test_cascade_chain_grammar_cannot_name_a_descriptor(tmp_path):
    """ADR-0008: ...and does NOT exist in the `[[cascade.chain]]` grammar.

    The SAME name, registered in the SAME catalog, on the other grammar. It
    parses (so this is not a schema error) and fails at RUN naming the class
    letter's registered module — which is the evidence that the cascade catalog
    was never consulted.
    """
    _write(tmp_path, "double_flip.toml", _DOUBLE_FLIP)
    dsl.register_catalog_dir(str(tmp_path))
    assert "probe_double_flip" in dsl.list_cascade_ops()

    spec = {
        "name": "probe_chain",
        "summary": "does a cascade.chain step see a catalog descriptor?",
        "returns": "seq",
        "steps": [{"class": "C", "op": "probe_double_flip",
                   "args": {"seq": "@input.seq"}}],
    }
    parsed = _compose.parse_chain_spec(spec)  # parses + validates + cycle-checks

    with pytest.raises(_compose.ChainSpecError) as exc:
        _compose.run_chain(parsed, inputs={"seq": [1, 2, 3]})
    msg = str(exc.value)
    assert "probe_double_flip" in msg
    assert "not found on" in msg

    # CONTROL: the same grammar, same catalog, a DOTTED name — runs. This is
    # what isolates the failure to bare-name resolution rather than to the
    # grammar or the fixture being broken.
    ok = {
        "name": "probe_chain_ok",
        "summary": "dotted control",
        "returns": "seq",
        "steps": [{"class": "C", "op": "srmech.cascade.atoms.chiral_flip",
                   "args": {"seq": "@input.seq"}}],
    }
    assert list(_compose.run_chain(_compose.parse_chain_spec(ok),
                                   inputs={"seq": [1, 2, 3]})) == [3, 2, 1]


# ── 3. the bound — a declared chain is a PROOF, not an execution path ─────

def test_declared_chain_is_never_the_execution_path(tmp_path):
    """ADR-0008: `[[cascade.chain]]` is documentation-with-teeth, not an impl.

    A descriptor with a declared chain but no `[composite]` and no callable is
    UNRUNNABLE — the resolver falls straight past the chain to the
    `srmech.cascade` attribute lookup. And it raises at BUILD time, because
    `lookup_cascade_op` runs when the stage is appended, not when it executes.
    """
    _write(tmp_path, "chainonly.toml", _CHAIN_ONLY)
    dsl.register_catalog_dir(str(tmp_path))
    assert "probe_chainonly" in dsl.list_cascade_ops()  # LOADS fine

    with pytest.raises(RuntimeError, match="does not expose a matching callable"):
        dsl.chain().then("probe_chainonly")  # NOT .run() — build-time


def test_encode_loe_content_is_the_only_callable_less_shipped_name():
    """The population behind the bound, measured rather than asserted.

    Every shipped catalog name resolves to an `srmech.cascade` attribute except
    ONE, which is reachable only via its dotted `[cascade].op`. If a second
    descriptor ever loses its callable, that is either an install-integrity
    break or a new pattern — either way it should be looked at, not absorbed.
    """
    import srmech.cascade as _cascade
    catalog = _catalog.load_catalog()
    callable_less = sorted(n for n in catalog if not hasattr(_cascade, n))
    assert callable_less == ["encode_loe_content"]

    dotted = catalog["encode_loe_content"]["cascade"]["op"]
    assert dotted == "srmech.signal_processing.encode_loe_content"
    assert callable(lookup_cascade_op("encode_loe_content"))


# ── 4. the leaves module is a NEIGHBOURHOOD, not the vocabulary ───────────

def test_leaves_module_is_not_the_declarable_vocabulary():
    """`srmech/cascade/leaves.py`: the count is a fact about one file only.

    Pins the two halves the old sentence conflated: `__all__` is the honest
    inventory of THIS module, and the dotted-addressable set is strictly
    larger — a callable from a different module resolves identically. This is
    the exact inversion that produced the "missing leaves" report.
    """
    from srmech.cascade import leaves
    assert len(leaves.__all__) == 12
    assert "seq_len" in leaves.__all__

    # a dotted step reaching OUTSIDE this module resolves the same way, which
    # is what makes "these leaves are dotted-addressable" a statement about
    # addressing rather than about membership.
    assert lookup_cascade_op("srmech.cascade.leaves.seq_len") is leaves.seq_len
    assert callable(lookup_cascade_op("srmech.cascade.atoms.chiral_flip"))
    assert callable(lookup_cascade_op("builtins.sorted"))


# ── 5. `#T1137` adjudication gates ────────────────────────────────────────

def test_dotted_catalog_name_is_rejected_at_load(tmp_path):
    """`srmech/dsl/_catalog.py`: a dotted `[cascade].name` fails LOUD at load.

    Measured pre-guard, a dotted name had two failure modes, both silent. An
    unimportable one ("probe.dotted") loaded and listed but could never be
    looked up. An IMPORTABLE one ("srmech.cascade.magnitude") was worse: it
    loaded, listed, answered get_descriptor() with the USER descriptor — and
    then RAN the shipped import (`chain().then(...).run(-5)` gave `5`, not
    the descriptor's identity composite), because the dot routes resolution
    to the import arm before any catalog consultation. The descriptor could
    never win; introspection and execution disagreed about one name. The
    guard turns both modes into this load error.
    """
    _write(tmp_path, "probe.toml", _DOUBLE_FLIP.replace(
        'name = "probe_double_flip"', 'name = "probe.dotted"'))
    dsl.register_catalog_dir(str(tmp_path))
    with pytest.raises(ValueError, match="contains a dot"):
        dsl.list_cascade_ops()

    # the importable spelling — the silent-shadow mode — is equally rejected.
    _catalog._USER_CATALOG_DIRS.clear()
    _catalog.load_catalog.cache_clear()
    hijack = tmp_path / "hijack"
    hijack.mkdir()
    _write(hijack, "hijack.toml", _DOUBLE_FLIP.replace(
        'name = "probe_double_flip"', 'name = "srmech.cascade.magnitude"'))
    dsl.register_catalog_dir(str(hijack))
    with pytest.raises(ValueError, match="contains a dot"):
        dsl.list_cascade_ops()

    # strict-zero on the shipped catalog: the guarded invariant was already
    # true of every shipped descriptor (this is what makes the guard a
    # promotion of a true sentence, not a behaviour change for valid input).
    _catalog._USER_CATALOG_DIRS.clear()
    _catalog.load_catalog.cache_clear()
    assert not [n for n in _catalog.load_catalog() if "." in n]


def test_composite_descriptor_body_rejects_dotted_stage_ref(tmp_path):
    """ADR-0008 boundary: the dotted arm is a BUILDER-surface property.

    A dotted ref INSIDE a `[composite]` descriptor body never reaches
    `lookup_cascade_op`: `_validate_composite` rejects any stage ref not in
    the catalog at LOAD. The same spelling on the builder surface runs — the
    control that pins WHERE the boundary sits, and keeps the ADR table's
    "resolves by import" cell honest about its reach.
    """
    _write(tmp_path, "dotted_stage.toml", """
        [cascade]
        name = "probe_dotted_stage"
        class_composition = "C"
        purpose = "a composite stage naming a DOTTED op"
        kind = "stage"

        [composite]
        [[composite.stage]]
        op = "srmech.cascade.leaves.seq_len"
    """)
    dsl.register_catalog_dir(str(tmp_path))
    with pytest.raises(ValueError, match="references unknown op"):
        dsl.list_cascade_ops()

    # CONTROL: the identical spelling runs on the builder surface.
    _catalog._USER_CATALOG_DIRS.clear()
    _catalog.load_catalog.cache_clear()
    assert dsl.chain().then("srmech.cascade.leaves.seq_len").run([7, 7, 7]) == 3


def test_dotted_spelling_no_longer_evicts_a_chain_from_the_native_run_loop():
    """`srmech/dsl/_catalog.py`: the run-loop cost of a dotted spelling.

    The TRUE version of the adjudicated claim (b). The earlier pass measured
    the OP — one self-routing object under either spelling — and stopped;
    that layer is spelling-independent, and the claim as originally worded
    ("no C peer => pure Python") is false there. The cost lives one level
    up: both chain-level C engines key their dispatch on the BARE catalog
    spelling (`_RUN_C_OPS` here; `dsl_leaf_dispatch` / `cr_dispatch` in C),
    so ONE dotted step evicts the WHOLE chain from the C run loop. The
    eligibility gate is pure-Python-decidable — no `.so` needed here; the C
    leg was measured in the `#T1137` adjudication with an ABI-14 `.so`
    (bare ran end-to-end in C, dotted was a native MISS, values identical).
    Value parity is asserted on whichever engine runs: inform-don't-limit
    means the eviction is a cost, never a wrong answer.

    ⚠️ THE EVICTION IS GONE AS OF rc447 (gh #1653), AND THIS TEST NOW PINS ITS
    ABSENCE. The finding above was TRUE when adjudicated: the C table matched
    `memcmp(op, "name", N)`, an exact BARE compare, so a dotted step missed.
    rc447 made the table match the last DOTTED SEGMENT uniformly (`cr_op_is`),
    because it had drifted into using TWO rules — the Class-N arms compared
    bare while the new Class-I/C/K/L arms compared by suffix, so
    `srmech.math.rational.sin_series_truncate` was NOT_IMPL while
    `srmech.cascade.atoms.chiral_flip` ran. Measured, and it put the Python
    eligibility predicate out of agreement with the runner on any dotted
    Class-N chain.

    Two rules on one table is worse than either rule, so one rule ships. It is
    ALSO the direction `#T1145` needs: that task's unlanded follow-up respells
    descriptors to their published dotted forms, and under the old bare compare
    every respelled chain would have silently left the C loop.

    The boundary matters and is asserted below: `cr_op_is` requires a `.`
    immediately before the match, so `poly_gcd` does NOT answer to `gcd`. A raw
    suffix compare would have dispatched one op's chain to another.
    """
    from srmech.cascade import compose as C

    bare = {
        "name": "probe_n_bare", "summary": "bare Class-N chain",
        "returns": "q",
        "steps": [{"class": "N", "op": "sin_series_truncate",
                   "args": {"numerator": 1, "denominator": 3,
                            "num_terms": 8}}],
    }
    dotted = {**bare, "name": "probe_n_dotted",
              "steps": [{**bare["steps"][0],
                         "op": "srmech.math.rational.sin_series_truncate"}]}
    sb, sd = C.parse_chain_spec(bare), C.parse_chain_spec(dotted)

    # the earlier pass's finding, kept: ONE callable under both spellings.
    assert (C._resolve_step_op("p", 0, "N", "sin_series_truncate",
                               C.DEFAULT_CLASS_REGISTRY)
            is C._resolve_step_op("p", 0, "N",
                                  "srmech.math.rational.sin_series_truncate",
                                  C.DEFAULT_CLASS_REGISTRY))

    # ...and BOTH spellings are now C-run-eligible (rc447). The `is False`
    # here was the adjudicated rc-`#T1137` behaviour; it is deliberately
    # inverted, not deleted, so the change of contract is visible in the diff.
    assert C._chain_c_eligible(sb) is True
    assert C._chain_c_eligible(sd) is True

    # the spelling never changes the VALUE (exact rational, either engine).
    assert C.run_chain(sb, inputs={}) == C.run_chain(sd, inputs={})


def test_the_dotted_match_respects_the_SEGMENT_boundary():
    """`poly_gcd` must not answer to `gcd`.

    The uniform matcher compares the last dotted segment. A raw suffix compare
    — which is what the rc447 arms used before this was generalised — matches
    `poly_gcd` and `bigint_gcd` against `gcd`, dispatching one op's chain to a
    DIFFERENT op. That is a wrong answer, not a capability gap, so it gets its
    own gate rather than riding on the test above.
    """
    import ctypes
    import json
    from srmech.cascade import compose as _C
    lib = _C._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    if lib is None:
        pytest.skip("no native library")

    def _rc(op):
        chain = {"name": "t", "steps": [
            {"class": "I", "op": op, "args": {"a": 12, "b": 18}}]}
        cj = json.dumps(chain).encode("utf-8")
        xj = json.dumps({"inputs": {}}).encode("utf-8")
        n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
        ws = (ctypes.c_char * n)()
        cap = max(n // 2, 65536)
        out = (ctypes.c_char * cap)()
        ol = ctypes.c_size_t()
        return int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n,
                                        out, cap, ctypes.byref(ol)))

    assert _rc("gcd") == 0, "the bare spelling must run"
    assert _rc("srmech.math.cyclic.gcd") == 0, "the dotted spelling must run"
    for impostor in ("poly_gcd", "bigint_gcd"):
        assert _rc(impostor) != 0, (
            "%r dispatched to `gcd` — the match is not respecting the dotted "
            "segment boundary, so one op's chain runs another's" % impostor)
