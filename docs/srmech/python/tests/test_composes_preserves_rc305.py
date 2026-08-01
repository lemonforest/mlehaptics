"""composes / preserves — the Siona compose-a-cascade capstone (rc305, `#943`).

``describe()`` / ``example`` are PER-OP; a cascade is CROSS-OP. rc305 adds two
STRUCTURED fields to every ``ToolEntry`` so the chaining knowledge that
otherwise lives only in CHANGELOG prose is readable as data:

* ``composes`` — the ordered sub-ops an op is built from (empty for a leaf op).
* ``preserves`` — the invariants an op / cascade maintains.

These are CLAIMS THAT MUST BE TRUE (the exact defect class this whole rc line
corrects — a description outrunning the code). The gate here is:

1. every ``composes`` entry names a REAL registered op, and
2. every ``preserves`` entry is a non-empty invariant string,

so a populated field can never drift ahead of the registry. The genome
``genome_from_graph`` F1299 worked example is pinned explicitly; the rest is a
whole-registry sweep. The C serialiser mirror is covered by
``test_tool_registry_c_rc184`` (byte-identity + hash ratchet) — one focused
native assertion here confirms the two new keys ride that JSON.

numpy-free (imports only srmech + stdlib), per the numpy-absent CI cell.
"""

from __future__ import annotations

import json

import pytest

from srmech import _native
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

warmup_all()

_SCHEMA = get_tool_schema()
_BY_NAME = {t.name: t for t in _SCHEMA.tools}
_NAMES = frozenset(_BY_NAME)

_GENOME_FROM_GRAPH = "srmech.biology.genome.genome_from_graph"

# The F1299 worked example — the ordered cascade genome_from_graph is built from
# (call order), traced against srmech/biology/genome.py::genome_from_graph.
_EXPECTED_GENOME_COMPOSES = (
    "srmech.biology.genome.genome_partition",
    "srmech.biology.genome.graph_to_kernel",
    "srmech.biology.genome.mint_strand",
    "srmech.biology.genome.genome_save",
    "srmech.biology.genome.genome_census",
)


# ──────────────────────────────────────────────────────────────────────
# 1. The F1299 worked example — genome_from_graph
# ──────────────────────────────────────────────────────────────────────


def test_genome_from_graph_composes_is_the_traced_cascade() -> None:
    """genome_from_graph.composes is EXACTLY the call-order sub-op sequence."""
    e = _BY_NAME[_GENOME_FROM_GRAPH]
    assert tuple(e.composes) == _EXPECTED_GENOME_COMPOSES, (
        "genome_from_graph.composes drifted from the traced implementation "
        f"(got {e.composes!r})"
    )


def test_genome_from_graph_composes_are_all_registered_ops() -> None:
    """Every sub-op genome_from_graph claims to chain is a REAL registered op."""
    e = _BY_NAME[_GENOME_FROM_GRAPH]
    assert e.composes, "genome_from_graph must declare its composition"
    for sub in e.composes:
        assert sub in _NAMES, (
            f"genome_from_graph.composes names {sub!r} which is not a "
            f"registered tool — a composition claim outran the registry"
        )


def test_genome_from_graph_preserves_nonempty_invariants() -> None:
    """genome_from_graph.preserves states at least one non-empty invariant,
    including the byte-exact kernel_to_graph round-trip contract."""
    e = _BY_NAME[_GENOME_FROM_GRAPH]
    assert e.preserves, "genome_from_graph must declare its invariants"
    for inv in e.preserves:
        assert isinstance(inv, str) and inv.strip(), (
            f"empty preserves entry on genome_from_graph: {inv!r}"
        )
    joined = " ".join(e.preserves)
    assert "kernel_to_graph" in joined, (
        "the byte-exact round-trip invariant (via kernel_to_graph) must be "
        "stated in genome_from_graph.preserves"
    )


# ──────────────────────────────────────────────────────────────────────
# 2. Leaf-op default — empty is correct
# ──────────────────────────────────────────────────────────────────────


def test_leaf_op_has_empty_composes_and_preserves() -> None:
    """A leaf primitive (sha256_bytes) carries the empty default — NOT
    fabricated composition."""
    e = _BY_NAME["srmech.amsc.format.sha256_bytes"]
    assert e.composes == ()
    assert e.preserves == ()


def test_leaf_op_omits_the_keys_in_to_jsonable() -> None:
    """Empty composes/preserves are OMITTED from to_jsonable (mirrors the C
    serialiser's key omission — the byte-identity contract)."""
    j = _BY_NAME["srmech.amsc.format.sha256_bytes"].to_jsonable()
    assert "composes" not in j
    assert "preserves" not in j


# ──────────────────────────────────────────────────────────────────────
# 3. Whole-registry claim-is-true sweep — the gate
# ──────────────────────────────────────────────────────────────────────


def test_every_composes_entry_is_a_registered_op() -> None:
    """GLOBAL: across ALL tools, every declared composes sub-op exists as a
    real registered op. This is the `#943` claim-is-true contract — a
    composition field can never name a phantom op."""
    offenders = {}
    for t in _SCHEMA.tools:
        missing = [s for s in t.composes if s not in _NAMES]
        if missing:
            offenders[t.name] = missing
    assert not offenders, f"composes entries naming non-existent ops: {offenders}"


def test_every_preserves_entry_is_a_nonempty_string() -> None:
    """GLOBAL: across ALL tools, every declared preserves invariant is a
    non-empty string (no blank claims)."""
    bad = {}
    for t in _SCHEMA.tools:
        for inv in t.preserves:
            if not (isinstance(inv, str) and inv.strip()):
                bad.setdefault(t.name, []).append(inv)
    assert not bad, f"empty / non-string preserves entries: {bad}"


def test_composes_and_preserves_are_tuples() -> None:
    """The fields are immutable tuples (frozen-dataclass friendly), never
    lists / None."""
    for t in _SCHEMA.tools:
        assert isinstance(t.composes, tuple), t.name
        assert isinstance(t.preserves, tuple), t.name


# ──────────────────────────────────────────────────────────────────────
# 4. to_jsonable round-trip shape
# ──────────────────────────────────────────────────────────────────────


def test_to_jsonable_emits_composes_preserves_as_ordered_arrays() -> None:
    """A composite op's to_jsonable carries composes/preserves as JSON arrays
    of strings, ORDER-PRESERVING (json sorts object keys, never array items)."""
    j = _BY_NAME[_GENOME_FROM_GRAPH].to_jsonable()
    assert j["composes"] == list(_EXPECTED_GENOME_COMPOSES)
    assert isinstance(j["preserves"], list) and j["preserves"]
    # survives a canonical dump/reload unchanged (the hash pre-image path).
    reloaded = json.loads(json.dumps(j, sort_keys=True, separators=(",", ":")))
    assert reloaded["composes"] == list(_EXPECTED_GENOME_COMPOSES)


# ──────────────────────────────────────────────────────────────────────
# 5. C serialiser mirror (native only)
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(
    not _native.has_native_tool_schema(),
    reason="rc184 tool-schema registry C peer not loaded (pure / stale host)",
)
def test_c_tool_schema_json_carries_composes_and_preserves() -> None:
    """The C serialiser emits the two new keys (byte-identity vs the Python
    SSoT is the rc184 gate; this asserts the keys are actually present so the
    mirror is exercised, not vacuously equal on absence)."""
    c_json = _native.tool_schema_json_c()
    assert c_json is not None
    assert b'"composes":' in c_json
    assert b'"preserves":' in c_json
    # and the C JSON parses back to a dict carrying genome_from_graph's cascade.
    doc = json.loads(c_json)
    entry = next(t for t in doc["tools"] if t["name"] == _GENOME_FROM_GRAPH)
    assert entry["composes"] == list(_EXPECTED_GENOME_COMPOSES)
    assert entry["preserves"]
