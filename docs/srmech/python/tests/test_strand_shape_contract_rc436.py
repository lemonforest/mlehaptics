"""The genome strand-shape contract — v0.9.0rc436 (local task T1141).

WHAT WAS WRONG
==============
``genome_save([chromosome(...), chromosome(...)], path, coupling)`` — passing a
LIST OF CHROMOSOMES where ONE flat strand is expected — died three frames down
with::

    File "srmech/biology/genome.py", line 8990, in genome_save
        chroms = _split_into_chromosomes(strand, labels)
    File "srmech/biology/genome.py", line 8346, in _split_into_chromosomes
        if _cap_kind(hv) in _CHROM_BOUNDARY_MARKERS:
    File "srmech/biology/genome.py", line 2735, in _cap_kind
        first = int(hv[0]) if len(hv) else -1
    TypeError: int() argument must be a string, a bytes-like object or a real
               number, not 'HV'

The message names ``int()`` and ``HV``. It does not name the STRAND, the SHAPE,
or the thing the caller almost certainly meant — and it surfaces in a private
function three frames below the public call.

WHY THE GUARD IS AT ``_cap_kind`` AND NOT AT ``genome_save``
============================================================
MEASURED at rc436 by static reachability over ``genome.py`` (call graph from
the module AST, transitively closed, intersected with the live registry):
**30 REGISTERED public ops reach ``_cap_kind``** —

    accessible, amplify, centromere_of, chromatin_of, condense, copy_number_of,
    decondense, gene_express, gene_express_levels, gene_express_plan, genes,
    genome_add_fiber, genome_add_octonion_fiber, genome_from_graph,
    genome_genes, genome_genes_expressed, genome_read_fiber,
    genome_read_octonion_fiber, genome_save, integrate, kernel_to_graph,
    kernel_unpack, mint_strand, modulator_consistent, modulator_constraint,
    modulator_recover, partition, recall, recover_diploid, telomere_tick

Every one of them inherits the repair from the single shared boundary. Guarding
only ``genome_save`` — the op the defect happened to be reported against —
would leave 29 public entry points with the bare ``int()`` message, which is
the MVP framing this project bans.

``_block_is_cap`` is the OTHER reader of ``_LEAF_WIDE_BLOCK_MARKERS`` and takes
raw ``bytes``, not an ``HV``; a nested sequence cannot reach it in that shape,
so it needs no twin guard.

PYTHON-ONLY, AND WHY NO PROJECTION GAP OPENS
============================================
The C peer is ``static int genome_cap_kind(const unsigned char *block,
size_t len)`` (``c/src/srmech_genome.c:287``) — a TYPED BUFFER. A nested list
cannot be expressed in that calling convention at all, so the malformed input
this guard names is UNREPRESENTABLE on the C projection. No capability diverges,
so per ADR-0009 §5 no decline row is owed: a decline row records something one
projection does and the other refuses, and the C side has no such input to
refuse. The question is answered here rather than skipped.
"""
from __future__ import annotations

import ast
import tempfile
from pathlib import Path

import pytest

from srmech.biology.genome import chromosome, genome_save, recall
from srmech.biology import genome as G
from srmech.math.hdc import klein4_address

D = 64


def _coupling():
    return klein4_address(D, b"rc436-coupling")


def _chrom(tag: str):
    c = _coupling()
    return chromosome([klein4_address(D, tag.encode() + b"0"),
                       klein4_address(D, tag.encode() + b"1")], c, label=tag)


def test_nested_chromosomes_raise_a_shape_error_that_names_the_shape():
    """The reported defect, repaired."""
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(TypeError) as exc:
            genome_save([_chrom("c1"), _chrom("c2")],
                        str(Path(d) / "g"), _coupling())
    msg = str(exc.value)
    assert "flat sequence of HVs" in msg.lower() or "FLAT sequence" in msg, msg
    assert "chromosome" in msg.lower(), msg
    assert "concatenate" in msg.lower(), msg


def test_the_message_names_the_likely_intent_not_just_the_type():
    """A good error names what the caller MEANT, and shows the fix.

    This is the half that distinguishes the repair from a re-spelling of the
    TypeError: the message carries an executable suggestion.
    """
    with pytest.raises(TypeError) as exc:
        G._cap_kind([_chrom("x")])
    msg = str(exc.value)
    assert "for hv in chrom" in msg, f"no concrete fix offered:\n{msg}"
    assert "§44" in msg, msg


def test_the_guard_is_inherited_by_the_shared_boundary_not_bolted_to_one_op():
    """CONTROL FOR THE PLACEMENT CLAIM.

    Drive the boundary directly and assert the guard is on ``_cap_kind``, which
    is what makes the other 29 ops inherit it. If a future edit moves the check
    up into ``genome_save``, this goes red while the first test still passes —
    which is exactly the regression worth catching.
    """
    with pytest.raises(TypeError) as exc:
        G._cap_kind([_chrom("y")])
    assert "strand" in str(exc.value).lower()


def test_at_least_25_registered_ops_reach_the_guarded_boundary():
    """The 30 is DERIVED here, not quoted, so it cannot silently rot.

    Floor rather than equality: ops get added, and this test's claim is "the
    boundary is shared by many", not "by exactly thirty".
    """
    src = (Path(G.__file__)).read_text(encoding="utf-8")
    tree = ast.parse(src)
    calls = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            seen = set()
            for c in ast.walk(node):
                if isinstance(c, ast.Call):
                    f = c.func
                    if isinstance(f, ast.Name):
                        seen.add(f.id)
                    elif isinstance(f, ast.Attribute):
                        seen.add(f.attr)
            calls[node.name] = seen

    reach = {"_cap_kind"}
    changed = True
    while changed:
        changed = False
        for fn, sub in calls.items():
            if fn not in reach and (sub & reach):
                reach.add(fn)
                changed = True

    from srmech.introspect import tool_schema as ts
    registered = {n.rsplit(".", 1)[-1] for n in ts._REGISTRY
                  if ".genome." in n}
    inheriting = sorted(registered & reach)
    assert len(inheriting) >= 25, (
        f"only {len(inheriting)} registered genome ops reach _cap_kind: "
        f"{inheriting}. The shared-boundary argument for this guard rests on "
        f"that population; if it collapsed, re-examine the placement.")
    assert "genome_save" in inheriting
    assert "recall" in inheriting


def test_control_a_wellformed_flat_strand_still_works():
    """THE NEGATIVE CONTROL — the guard must not reject valid input.

    A guard that raises on everything would pass every test above. This drives
    a real save/recall round-trip through the same boundary and asserts the
    payload survives, so the strict behaviour above is bounded.
    """
    c = _coupling()
    leaves = [klein4_address(D, b"a"), klein4_address(D, b"b")]
    strand = chromosome(leaves, c, label="ok")
    with tempfile.TemporaryDirectory() as d:
        genome_save(strand, str(Path(d) / "g"), c)
    got = recall(strand, c)
    assert len(got) == len(leaves)
    for a, b in zip(got, leaves):
        assert a.tobytes() == b.tobytes()


def test_control_the_bare_int_message_is_what_the_guard_replaces():
    """PROOF THE GUARD IS THE THING SUPPLYING THE GUIDANCE.

    Reproduce the UNGUARDED expression — ``int(hv[0])`` on a nested sequence —
    and assert its message carries none of the guidance. Without this control,
    the assertions above could be satisfied by a message that Python raised on
    its own, and the test would prove nothing about the guard.
    """
    nested = [_chrom("z")]
    with pytest.raises(TypeError) as raw:
        int(nested[0])
    raw_msg = str(raw.value)
    assert "concatenate" not in raw_msg.lower()
    assert "strand" not in raw_msg.lower()

    with pytest.raises(TypeError) as guarded:
        G._cap_kind(nested)
    assert "concatenate" in str(guarded.value).lower(), (
        "the guard added nothing over the bare int() failure")
