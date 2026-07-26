"""rc340 (`#T965`) — the genome CARRIER-COVERAGE ratchet, over BOTH surfaces.

rc339 shipped the measured capability LADDER (what each element_type rung can do).
This module pins the other half: **which genome ops can be ASKED**, and — the part a
plain count cannot see — whether an op that ACCEPTS the argument actually HONOURS it.

Three guards, all down-only or exact:

1. **Classification completeness.** Every public ``srmech.amsc.genome`` callable
   appears exactly once in :data:`~srmech.amsc.genome.GENOME_CARRIER_SURFACE`. A new
   op must be classified deliberately; it cannot default into an unexamined bucket.

2. **The coverage ratchet, on BOTH surfaces.** The count of ops LACKING
   ``element_type`` may only go DOWN — measured separately for the Python signature
   and for the MCP / tool-schema surface, because those disagreed for 19 ops until
   rc340. The MCP number is the one that bounds a REMOTE caller: the tool schema is
   what an LLM prosthetic calls through, so an op missing there is klein4-only over
   the wire no matter what Python accepts. A Python/MCP crack is pinned at ZERO.

3. **The honesty guard — an accepted argument must CHANGE something.** Every
   ``"accepts"`` op is DRIVEN on all three rungs against identical inputs and its
   outputs compared. An op that took ``element_type`` and ignored it would be a false
   green — reporting a capability it does not deliver — and is strictly worse than
   not offering the parameter. Ops whose outputs are legitimately rung-INVARIANT are
   listed in :data:`_RUNG_INVARIANT` with the reason, so "identical" is a stated
   claim rather than a silent pass.

The complement matters as much as the coverage: ops classified ``"free"`` must NOT
grow an ``element_type``. Padding the coverage number by handing a carrier parameter
to something with no carrier is the exact failure this file exists to prevent.
"""

from __future__ import annotations

import inspect
from collections import Counter

import pytest

from srmech.amsc import genome as G
from srmech.amsc import tool_schema as TS
from srmech.amsc.hv import HV


# ──────────────────────────────────────────────────────────────────────
# The ratchet ceilings — DOWN ONLY. Lower them when coverage improves;
# never raise them. rc340 measured 70 public callables.
# ──────────────────────────────────────────────────────────────────────

#: Ops with NO ``element_type`` on the PYTHON surface. rc339: 56. rc340: 48.
CEIL_GENOME_CARRIER_GAP_PY = 48

#: Ops with NO ``element_type`` on the MCP / tool-schema surface. rc339: 65 (of 67
#: registered entries — only kernel_pack + genome_append_kernel published it).
#: rc340: 45.
CEIL_GENOME_CARRIER_GAP_MCP = 45

#: Ops accepting ``element_type`` in Python whose MCP entry does NOT publish it —
#: the silent-default crack. rc339: 19 (quad_turn among them). rc340: 0, and it
#: stays 0: a remote caller must never be handed the abelian rung without being
#: told the choice exists.
CEIL_GENOME_CARRIER_PYTHON_MCP_CRACKS = 0


def _public_callables():
    """Every public callable DEFINED in ``srmech.amsc.genome`` (not re-exports,
    not exception classes, not typing imports)."""
    out = {}
    for name in dir(G):
        if name.startswith("_"):
            continue
        obj = getattr(G, name)
        if not callable(obj) or isinstance(obj, type):
            continue
        if getattr(obj, "__module__", "") != G.__name__:
            continue
        out[name] = obj
    return out


def _accepts_python(name, obj):
    try:
        return "element_type" in inspect.signature(obj).parameters
    except (TypeError, ValueError):  # pragma: no cover — no introspectable signature
        return False


def _mcp_parameters():
    """``{op_short_name: {param names}}`` for every registered genome tool entry.

    Reads :func:`~srmech.amsc.tool_schema.tool_schema_view` deliberately — that is the
    view the MCP adapter serves, and when the native peer is loaded it is produced by
    the C const table (``srmech_tool_registry.c``). So this ALSO catches the rc340
    trap where a Python-side schema edit lands but the generated C registry is not
    regenerated: the Python source would look fixed while the served surface stayed
    stale.
    """
    out = {}
    for tool in TS.tool_schema_view()["tools"]:
        name = tool["name"]
        if name.startswith("srmech.amsc.genome."):
            out[name.rsplit(".", 1)[1]] = {p["name"] for p in tool["parameters"]}
    return out


# ──────────────────────────────────────────────────────────────────────
# 1 — classification completeness
# ──────────────────────────────────────────────────────────────────────


def test_every_public_genome_callable_is_classified():
    """No op may default into an unexamined bucket."""
    public = set(_public_callables())
    mapped = set(G.GENOME_CARRIER_SURFACE)
    assert public - mapped == set(), (
        f"unclassified genome callable(s): {sorted(public - mapped)}. Add each to "
        f"GENOME_CARRIER_SURFACE with one of {G.GENOME_CARRIER_RELATIONSHIPS} and a "
        f"one-line reason — deciding is the point; defaulting hides the gap."
    )
    assert mapped - public == set(), (
        f"GENOME_CARRIER_SURFACE names ops that no longer exist: "
        f"{sorted(mapped - public)}"
    )


def test_relationships_are_from_the_declared_vocabulary():
    bad = {n: r for n, (r, _) in G.GENOME_CARRIER_SURFACE.items()
           if r not in G.GENOME_CARRIER_RELATIONSHIPS}
    assert bad == {}, f"unknown relationship(s): {bad}"


def test_every_classification_carries_a_reason():
    missing = [n for n, (_, why) in G.GENOME_CARRIER_SURFACE.items()
               if not why or not why.strip()]
    assert missing == [], (
        f"classification without a reason: {missing}. A defensible short list beats a "
        f"large meaningless one — every entry states WHY."
    )


def test_classification_matches_the_measured_python_signatures():
    """``"accepts"`` is a claim about the real signature, checked against it.

    A ``"derived"`` op MAY carry an ``element_type`` — ``genome_append_kernel`` does —
    but only as an ASSERTION checked against the store, never as a free choice. What
    is forbidden is claiming ``"accepts"`` without the parameter, or a ``"free"`` /
    ``"fixed"`` op growing one.
    """
    public = _public_callables()
    surface = G.GENOME_CARRIER_SURFACE
    claims = {n for n, (r, _) in surface.items() if r == "accepts"}
    actual = {n for n, o in public.items() if _accepts_python(n, o)}

    assert claims - actual == set(), (
        f"classified 'accepts' but the signature has no element_type: "
        f"{sorted(claims - actual)}"
    )
    stray = {n for n in actual - claims if surface[n][0] in ("free", "fixed")}
    assert stray == set(), (
        f"op(s) classified {[surface[n][0] for n in sorted(stray)]} grew an "
        f"element_type: {sorted(stray)}. A carrier parameter on something with no "
        f"carrier is a false green — reclassify the op or drop the parameter."
    )


def test_free_ops_never_take_a_carrier():
    """The complement of the ratchet: do not pad coverage."""
    public = _public_callables()
    offenders = [n for n, (r, _) in G.GENOME_CARRIER_SURFACE.items()
                 if r == "free" and n in public and _accepts_python(n, public[n])]
    assert offenders == [], (
        f"carrier-FREE op(s) accepting element_type: {offenders}. These have no turn "
        f"to couple — the parameter could only be ignored."
    )


# ──────────────────────────────────────────────────────────────────────
# 2 — the down-only coverage ratchet, on BOTH surfaces
# ──────────────────────────────────────────────────────────────────────


def test_python_surface_carrier_gap_is_down_only():
    public = _public_callables()
    lacking = sorted(n for n, o in public.items() if not _accepts_python(n, o))
    assert len(lacking) <= CEIL_GENOME_CARRIER_GAP_PY, (
        f"PYTHON carrier gap ROSE to {len(lacking)} (ceiling "
        f"{CEIL_GENOME_CARRIER_GAP_PY}); the ratchet is down-only. Lacking: {lacking}"
    )


def test_mcp_surface_carrier_gap_is_down_only():
    """The number that actually bounds a REMOTE caller."""
    mcp = _mcp_parameters()
    lacking = sorted(n for n, params in mcp.items() if "element_type" not in params)
    assert len(lacking) <= CEIL_GENOME_CARRIER_GAP_MCP, (
        f"MCP carrier gap ROSE to {len(lacking)} (ceiling "
        f"{CEIL_GENOME_CARRIER_GAP_MCP}); the ratchet is down-only. The tool schema is "
        f"the surface an LLM prosthetic calls through, so an op missing here is "
        f"klein4-only over the wire. Lacking: {lacking}"
    )


def test_no_python_mcp_carrier_crack():
    """An op taking element_type in Python MUST publish it on the wire.

    Otherwise a remote caller silently gets KLEIN-4 — abelian, carrying no which-way
    — with no way to ask for another rung and no error saying so. A silently-wrong
    carrier is worse than an absent parameter.
    """
    public = _public_callables()
    mcp = _mcp_parameters()
    cracks = sorted(
        n for n, o in public.items()
        if _accepts_python(n, o) and n in mcp and "element_type" not in mcp[n]
    )
    assert len(cracks) <= CEIL_GENOME_CARRIER_PYTHON_MCP_CRACKS, (
        f"Python/MCP carrier crack(s): {cracks}. Add the shared ET_PARAM to each "
        f"entry in tool_schema.py AND regenerate c/src/srmech_tool_registry.c — "
        f"tool_schema_view() serves the C table when HAS_NATIVE, so a Python-only "
        f"edit leaves the served surface stale."
    )


def test_ratchet_ceilings_are_not_slack():
    """A ceiling far above the real count stops ratcheting. Keep them tight."""
    public = _public_callables()
    py_lacking = sum(1 for n, o in public.items() if not _accepts_python(n, o))
    mcp = _mcp_parameters()
    mcp_lacking = sum(1 for params in mcp.values() if "element_type" not in params)
    assert py_lacking == CEIL_GENOME_CARRIER_GAP_PY, (
        f"PYTHON gap is {py_lacking} but the ceiling says "
        f"{CEIL_GENOME_CARRIER_GAP_PY} — lower the ceiling to lock the gain in."
    )
    assert mcp_lacking == CEIL_GENOME_CARRIER_GAP_MCP, (
        f"MCP gap is {mcp_lacking} but the ceiling says "
        f"{CEIL_GENOME_CARRIER_GAP_MCP} — lower the ceiling to lock the gain in."
    )


# ──────────────────────────────────────────────────────────────────────
# 3 — the honesty guard: an accepted rung must CHANGE something
# ──────────────────────────────────────────────────────────────────────

_RUNGS = (G.ELEMENT_TYPE_KLEIN4, G.ELEMENT_TYPE_Q8, G.ELEMENT_TYPE_OCTONION)

#: Ops whose output is legitimately IDENTICAL across rungs, with the reason. Being on
#: this list is a stated claim, not a silent pass — an op here still gets driven on
#: all three rungs, it is just asserted EQUAL instead of DIFFERENT.
_RUNG_INVARIANT = {
    "modulator_consistent": (
        "returns a CONSISTENT/INCONSISTENT verdict over the expressed LABEL SET. The "
        "labels come from cap masks, which no rung changes; only the leaf bytes the "
        "verdict does not inspect differ."),
    "kernel_to_graph": (
        "driven as a ROUND TRIP, and recovering the SAME graph on every rung is "
        "exactly the contract graph_to_kernel documents: the rung is a STORAGE choice "
        "(which algebra binds the turns, hence the on-disk width), while the graph "
        "PAYLOAD is base-4 digits valid on every rung. What must differ is the STORED "
        "STRAND, and that is probed by graph_to_kernel; what must not differ is the "
        "graph read back out."),
}

#: DECODE ops must be probed against a FIXED strand, not a round trip.
#:
#: A round trip (encode at rung R, decode at rung R) recovers the original leaves on
#: EVERY rung — that is the correctness property, so using it as the honesty probe
#: would compare three identical answers and conclude the argument was ignored. It
#: would be a probe that cannot see what it is looking for. Instead these ops are
#: driven against ONE strand encoded at klein4, varying only the DECODE rung: the
#: recovered leaves (or the refusal) must then differ, which is what proves the rung
#: reached the bind. A refusal counts as a difference — decoding klein4 bytes as
#: octonion legitimately raises, and that IS the rung being honoured.
_DECODE_OPS = frozenset({
    "recall", "partition", "genes", "recover_diploid", "gene_express",
    "gene_express_levels", "kernel_unpack",
})

_DIM = 64


def _leaf(pattern):
    """A leaf whose symbols are all in ``{0..3}`` — VALID on every rung, so the same
    input can be driven across all three and any output difference is attributable to
    the bind alone, never to the alphabet."""
    return HV.from_sequence([pattern[i % len(pattern)] for i in range(_DIM)],
                            sectors=G.OCTONION_SECTORS)


#: A coupling that COLLIDES with the turn at position 0 (both symbol 1). That is what
#: separates the rungs: klein4 XOR gives 1^1 = 0, Q8 gives i*i = -1 (byte 4), and the
#: octonion product gives -e0 (byte 8). Without a collision the three binds can agree
#: on V4-coset representatives and a real difference would go unmeasured.
_ONE = _leaf([1, 2, 1, 3])
_LEAVES = [_leaf([1, 1, 2, 3]), _leaf([2, 0, 3, 1])]

# The FIXED klein4-encoded fixtures the decode probes read (see _DECODE_OPS).
_K4 = G.ELEMENT_TYPE_KLEIN4
_K4_CHROM = G.chromosome(_LEAVES, _ONE, label="c", element_type=_K4)
_K4_GENES = G.chromosome(coupling=_ONE, label="c",
                         genes=[("g1", [_LEAVES[0]]), ("g2", [_LEAVES[1]])],
                         element_type=_K4)
_K4_REG = G.chromosome(coupling=_ONE, label="c",
                       genes=[("on", [_LEAVES[0]], 0), ("off", [_LEAVES[1]], 0b1)],
                       element_type=_K4)
_K4_DIPLOID = G.diploid(_LEAVES, _ONE, element_type=_K4)
_K4_KERNEL = G.kernel_pack([1, 2, 3, 0] * 8, leaf_dim=_DIM, label="k",
                           coupling=_ONE, element_type=_K4)
_K4_GRAPH_STRAND, _K4_GRAPH_NSYMS = G.graph_to_kernel(
    3, [(0, 1), (1, 2)], [1, 2], [1, -1], leaf_dim=_DIM, label="g",
    coupling=_ONE, element_type=_K4)


def _drivers():
    """``{op: callable(element_type) -> comparable}`` for every ``"accepts"`` op.

    Each driver exercises the op END TO END on the rung it is handed, returning
    something byte-comparable. Ops are driven with the SAME inputs on every rung.
    """
    one, leaves = _ONE, _LEAVES

    def _flat(strand):
        return [list(hv) for hv in strand]

    def _chrom(et):
        return G.chromosome(leaves, one, label="c", element_type=et)

    def _genes_strand(et):
        return G.chromosome(coupling=one, label="c",
                            genes=[("g1", [leaves[0]]), ("g2", [leaves[1]])],
                            element_type=et)

    def _reg_gene_strand(et):
        return G.chromosome(coupling=one, label="c",
                            genes=[("on", [leaves[0]], 0), ("off", [leaves[1]], 0b1)],
                            element_type=et)

    return {
        "quad_turn": lambda et: list(G.quad_turn(leaves[0], one, element_type=et)),
        "chromosome": lambda et: _flat(_chrom(et)),
        "genome": lambda et: _flat(G.genome({"a": leaves}, one, element_type=et)),
        "mint": lambda et: _flat(G.mint({"a": leaves}, one, element_type=et)),
        "plasmid": lambda et: _flat(G.plasmid({"a": leaves}, one, element_type=et)),
        "diploid": lambda et: _flat(G.diploid(leaves, one, element_type=et)),
        # DECODE ops: the strand is built ONCE at klein4 and only the decode rung
        # varies (see _DECODE_OPS — a round trip would be invariant by construction).
        "recall": lambda et: [list(x) for x in G.recall(_K4_CHROM, one,
                                                        element_type=et)],
        "partition": lambda et: {k: [list(x) for x in v] for k, v in
                                 G.partition(_K4_CHROM, one, element_type=et).items()},
        "genes": lambda et: [(lab, [list(x) for x in lv]) for lab, lv in
                             G.genes(_K4_GENES, one, element_type=et)],
        "recover_diploid": lambda et: [
            list(x) for x in G.recover_diploid(_K4_DIPLOID, one, element_type=et)],
        "gene_express": lambda et: [(lab, [list(x) for x in lv]) for lab, lv in
                                    G.gene_express(_K4_REG, one, 0,
                                                   element_type=et)],
        # returns (label, leaves, level) — the LEVEL is the exact rational dose.
        "gene_express_levels": lambda et: [
            (lab, [list(x) for x in lv], lvl) for lab, lv, lvl in
            G.gene_express_levels(_K4_REG, one, 0, element_type=et)],
        "gene_express_plan": lambda et: G.gene_express_plan(
            _reg_gene_strand(et), one, 0, element_type=et),
        "modulator_consistent": lambda et: G.modulator_consistent(
            _reg_gene_strand(et), one, ["on"], 0, element_type=et),
        "kernel_pack": lambda et: _flat(G.kernel_pack(
            [1, 2, 3, 0] * 8, leaf_dim=_DIM, label="k", coupling=one,
            element_type=et)),
        "kernel_unpack": lambda et: list(G.kernel_unpack(_K4_KERNEL, one,
                                                         element_type=et)),
        "graph_to_kernel": lambda et: _flat(G.graph_to_kernel(
            3, [(0, 1), (1, 2)], [1, 2], [1, -1], leaf_dim=_DIM, label="g",
            coupling=one, element_type=et)[0]),
        # ROUND TRIP (encode + decode at the same rung) — see _RUNG_INVARIANT.
        "kernel_to_graph": lambda et: G.kernel_to_graph(
            *(lambda p: (p[0], one, p[1]))(G.graph_to_kernel(
                3, [(0, 1), (1, 2)], [1, 2], [1, -1], leaf_dim=_DIM, label="g",
                coupling=one, element_type=et)),
            element_type=et),
        "mint_strand": lambda et: _flat(G.mint_strand(
            _chrom(et), one, element_type=et)),
        "genome_save": lambda et: _genome_save_bytes(et),
        "genome_from_graph": lambda et: _flat(G.genome_from_graph(
            6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)],
            [1] * 6, [1] * 6, coupling=one, leaf_dim=_DIM,
            element_type=et)["strand"]),
    }


_SAVE_TMP = {}


def _genome_save_bytes(et):
    """``genome_save``'s on-disk body — the rung sets the packed-turn WIDTH + marker,
    so the bytes differ even though the recovered leaves do not."""
    path = _SAVE_TMP["dir"] / f"g{et}"
    G.genome_save(G.chromosome(_LEAVES, _ONE, label="c", element_type=et),
                  path, _ONE, element_type=et)
    return (path / "turns.bin").read_bytes()


@pytest.fixture(autouse=True)
def _tmp(tmp_path):
    _SAVE_TMP["dir"] = tmp_path
    yield
    _SAVE_TMP.clear()


def test_every_accepting_op_has_a_driver():
    """The honesty guard is only as good as its coverage of the accepting set."""
    accepts = {n for n, (r, _) in G.GENOME_CARRIER_SURFACE.items() if r == "accepts"}
    driven = set(_drivers())
    assert accepts - driven == set(), (
        f"'accepts' op(s) with no honesty driver: {sorted(accepts - driven)}. Every "
        f"op that takes element_type must be DRIVEN on all three rungs — a parameter "
        f"nothing exercises is how an ignored argument survives."
    )


@pytest.mark.parametrize("op", sorted(_drivers()))
def test_accepting_op_does_not_ignore_the_rung(op):
    """Drive one op on all three rungs; assert it does not ignore the argument."""
    driver = _drivers()[op]
    results = {}
    for rung in _RUNGS:
        try:
            results[rung] = driver(rung)
        except Exception as exc:      # noqa: BLE001 — a refusal IS an observable
            # Decoding klein4 bytes as octonion legitimately raises: the symbol is out
            # of the alphabet. That refusal is the rung being HONOURED, not an error to
            # hide — record it as the outcome so it counts as a distinct answer.
            results[rung] = f"{type(exc).__name__}: {exc}"

    if op in _RUNG_INVARIANT:
        assert results[_RUNGS[0]] == results[_RUNGS[1]] == results[_RUNGS[2]], (
            f"{op} is listed rung-INVARIANT ({_RUNG_INVARIANT[op]}) but its outputs "
            f"DIFFER across rungs. Either the reason is wrong or the op changed — "
            f"resolve it, do not relax the assertion."
        )
        return

    distinct = Counter(repr(v) for v in results.values())
    assert len(distinct) == len(_RUNGS), (
        f"{op} accepts element_type but produced the SAME output on "
        f"{len(_RUNGS) - len(distinct) + 1} of {len(_RUNGS)} rungs — the argument is "
        f"being IGNORED, which is a false green (it reports a capability it does not "
        f"deliver). Thread the rung to the bind, or move {op} to the carrier-free / "
        f"derived list in GENOME_CARRIER_SURFACE and state why."
    )


def test_element_type_name_and_code_are_the_same_request():
    """rc340 unified the two vocabularies that had drifted apart."""
    for name, code in (("klein4", 0), ("q8", 1), ("octonion", 2)):
        by_code = list(G.quad_turn(_LEAVES[0], _ONE, element_type=code))
        by_name = list(G.quad_turn(_LEAVES[0], _ONE, element_type=name))
        assert by_code == by_name, f"element_type={name!r} != element_type={code}"


@pytest.mark.parametrize("bad", [True, False, 3, -1, "klein-4", 1.0, None])
def test_unknown_element_type_is_refused(bad):
    """A which-carrier choice is not a flag, and there is no rung 3."""
    with pytest.raises(ValueError):
        G.quad_turn(_LEAVES[0], _ONE, element_type=bad)


def test_klein4_remains_the_default_everywhere_it_accepts():
    """Default-preserving: omitting element_type == asking for klein4."""
    # the explicit spot-checks: the omitted-argument call equals the klein4 call
    assert (list(G.quad_turn(_LEAVES[0], _ONE))
            == list(G.quad_turn(_LEAVES[0], _ONE,
                                element_type=G.ELEMENT_TYPE_KLEIN4)))
    assert ([list(x) for x in G.chromosome(_LEAVES, _ONE, label="c")]
            == [list(x) for x in G.chromosome(_LEAVES, _ONE, label="c",
                                              element_type=G.ELEMENT_TYPE_KLEIN4)])
    assert ([list(x) for x in G.genome({"a": _LEAVES}, _ONE)]
            == [list(x) for x in G.genome({"a": _LEAVES}, _ONE,
                                          element_type=G.ELEMENT_TYPE_KLEIN4)])
