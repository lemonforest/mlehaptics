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
These are EQUALITIES, not ratchets. Each asserts the measured rc434 behaviour;
a change in either direction is a real change to the DSL's naming contract and
must be a deliberate edit here plus the three docstrings above, together.
"""

from __future__ import annotations

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


def test_introspect_visibility_follows_the_target_not_the_dotted_form():
    """`srmech/dsl/_catalog.py`: a dotted step is not INHERENTLY invisible.

    The tempting overcorrection — "dotted steps have no ToolEntry, so they are
    invisible to describe() / MCP" — is FALSE as a general claim and was
    measured false before the docstring was written. Visibility is a property
    of the target's own registration.
    """
    from srmech.introspect.tool_schema import get_tool_schema
    schema = get_tool_schema()

    entry = schema.resolve("srmech.cascade.magnitude")
    assert entry is not None and entry.name == "srmech.cascade.magnitude"

    # ...while an unregistered target — shipped or not — has none.
    assert schema.resolve("srmech.cascade.leaves.seq_len") is None
    assert schema.resolve("builtins.set") is None


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
