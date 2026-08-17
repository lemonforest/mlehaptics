"""§v19 IMPLICIT CLOSE → §GROUP/v20 EXPLICIT CLOSE — the inference, and its replacement.

rc441 (``#T1148``) shipped this file as the v20 PREREQUISITES. rc442 (``#T1150``) is v20,
and this file now records both halves of the story.

THE DEFECT rc441 STATED. A v19 strand had no CLOSER cap. A chromosome opened with a
boundary cap and simply ran until the next opener, or off the end of the strand. So
*"where does this unit end?"* was never READ — it was INFERRED. Two shared helpers encoded
that inference, and four call sites spliced at the position it returned:

======================================  =================================================
``genome_nth_data_turn``                returned ``n_blocks`` when ``split == n_turns``
``genome_label_range``                  ``end`` = next boundary index, else ``n_blocks``
``mint_strand`` / ``_chrom_range``      the Python twins of the same two
======================================  =================================================

At v19 the inference was **accidentally correct**: with no closer, the end of a unit and
the start of the next were the SAME index. rc441 predicted it would stop being correct the
moment a closer existed, and that it would stop *silently* — the splice landing on the
wrong side of a cap and producing a well-formed strand that means something else.

**THE PIN FIRED, AND IT FIRED FOR THE RIGHT REASON.** rc441's
``test_cap_marker_vocabulary_is_pinned`` was written to go red in rc442 and to route its
author to all four splice sites. That is exactly what happened: rc442 minted
:data:`~srmech.biology.genome.GROUP_CLOSE_MARKER`, the pin went red, and all four sites
were re-derived against the closer rather than the next opener. Going red there was it
working, not it breaking — so the pin is not deleted here, it is MOVED FORWARD to the v20
vocabulary, where it will fire again for the next marker.

WHAT REPLACED THE INFERENCE. ``_unit_end_before_closers`` (Python) and
``genome_unit_end_before_closers`` (C): a unit that runs to the end of the strand ends
BEFORE the trailing closers, which is READ from the markers rather than inferred from the
buffer running out. ``_chrom_range`` / ``genome_label_range`` additionally stop at a group
marker, because R1/R2 make ``[`` and ``]`` each implicitly close the open chromosome.

**An ungrouped strand has no frame markers, so every one of those extents is byte-for-byte
what v19 returned** — which is the property the last test in this file holds.

No stdlib ``fractions`` / ``math`` / ``decimal`` / numpy. No ``abs()`` — a block index is a
non-negative position, not a magnitude.
"""

from __future__ import annotations

import pytest

from srmech.biology import genome as G


# ──────────────────────────────────────────────────────────────────────
# 1. The version this reasoning is valid for
# ──────────────────────────────────────────────────────────────────────

def test_format_version_is_20():
    """rc442 IS v20. If this moves again, re-derive the four splice sites once more —
    a new marker is exactly the event that invalidates an extent rule."""
    assert G.GENOME_FORMAT_VERSION == 20, (
        f"GENOME_FORMAT_VERSION is {G.GENOME_FORMAT_VERSION}, not 20 — if the "
        f"format moved, revisit the four EXPLICIT CLOSE splice sites "
        f"(mint_strand insert_at, _chrom_range end, and their C twins "
        f"genome_nth_data_turn / genome_label_range)"
    )


# ──────────────────────────────────────────────────────────────────────
# 2. The guard, moved forward to the v20 vocabulary
# ──────────────────────────────────────────────────────────────────────

#: The v20 cap vocabulary, pinned by VALUE. rc441 pinned the v19 fourteen; rc442 adds the
#: two frame markers and nothing else. A future closer-shaped cap is a NEW marker byte, so
#: minting one necessarily changes this set — which is the event that invalidates an extent
#: rule at all four splice sites.
_V20_CAP_MARKERS = frozenset({
    G.CHROM_CAP_MARKER, G.GENE_CAP_MARKER, G.REGULATORY_GENE_MARKER,
    G.BOOLEAN_GENE_MARKER, G.THRESHOLD_GENE_MARKER, G.GRADED_GENE_MARKER,
    G.KERNEL_HEADER_MARKER, G.KERNEL_TELOMERE_MARKER, G.ACTIVE_TELOMERE_MARKER,
    G.CENTROMERE_CAP_MARKER, G.DIPLOID_TELOMERE_MARKER, G.CHROMATIN_MARKER,
    G.FIBER_CAP_MARKER, G.OCT_FIBER_CAP_MARKER,
    G.GROUP_OPEN_MARKER, G.GROUP_CLOSE_MARKER,
})

#: The subset that OPENS a chromosome. Under v20 an opener is no longer the ONLY thing that
#: can end the previous unit — a frame marker does too, which is the whole change.
_V20_BOUNDARY_MARKERS = frozenset({
    G.CHROM_CAP_MARKER, G.KERNEL_TELOMERE_MARKER,
    G.ACTIVE_TELOMERE_MARKER, G.DIPLOID_TELOMERE_MARKER,
})


def test_cap_marker_vocabulary_is_pinned():
    """A new cap marker must trip this gate.

    THIS GATE WENT RED IN rc442, BY DESIGN. The fix was not to add the new bytes to
    the set and move on: it was to revisit the four splice sites named in the message,
    because a closer changes what "the end of a unit" means at every one of them.
    That work is done (see section 4 below); the pin now guards the v20 set.
    """
    live = frozenset(G._LEAF_WIDE_BLOCK_MARKERS)
    added = live - _V20_CAP_MARKERS
    removed = _V20_CAP_MARKERS - live
    assert not added and not removed, (
        f"the genome cap-marker vocabulary moved (added={sorted(added)}, "
        f"removed={sorted(removed)}).\n"
        f"If one of these is a new CLOSER cap, the extent rule is now WRONG at four "
        f"splice sites and each must be re-derived against it:\n"
        f"  1. C  genome_nth_data_turn  (srmech_genome.c) — append-at-end locus\n"
        f"  2. C  genome_label_range    (srmech_genome.c) — the `end` extent\n"
        f"  3. Py mint_strand insert_at (genome.py) — the centromere splice\n"
        f"  4. Py _chrom_range end      (genome.py) — the chromatin splice\n"
        f"Each reports whether its extent was READ or INFERRED; the INFERRED branch "
        f"is the one that must change."
    )
    assert _V20_BOUNDARY_MARKERS <= live, "a boundary marker vanished"
    assert frozenset(G._GROUP_MARKERS) <= live, "a frame marker vanished"


def test_the_closer_is_the_only_marker_named_like_one():
    """v19 had no closer by construction; v20 has EXACTLY one.

    rc441's version of this test asserted NO marker was named like a closer. Inverting
    it rather than deleting it keeps the same thing measurable: a SECOND closer-shaped
    marker would be a genuinely new grammar and must not slip in unremarked."""
    suspicious = [
        n for n in dir(G)
        if n.endswith("_MARKER")
        and any(w in n.upper() for w in ("CLOSE", "CLOSER", "END_CAP", "TERMINATOR"))
    ]
    assert suspicious == ["GROUP_CLOSE_MARKER"], (
        f"closer-named marker constant(s): {suspicious} — v20 has exactly one "
        f"(GROUP_CLOSE_MARKER). A second one is a new grammar; see the four splice sites."
    )


# ──────────────────────────────────────────────────────────────────────
# 3. The extent helpers report their own provenance
# ──────────────────────────────────────────────────────────────────────

#: Wide enough that a default centromere cap (handle + the R=15 α-satellite array)
#: fits in ONE leaf — the mint_strand case below writes a real cap, not a stub.
_DIM = 32


def _strand(*labels):
    """A strand of `len(labels)` chromosomes, each a boundary cap + two data turns."""
    out = []
    for lab in labels:
        out.append(G.telomere(lab, dim=_DIM))
        out.extend(G._HV.from_sequence(bytes([k % 4] * _DIM), sectors=4)
                   for k in (1, 2))
    return out


def test_chrom_range_reports_inferred_end_on_the_last_chromosome():
    """The LAST chromosome's end is inferred (nothing follows it); an earlier
    chromosome's end is READ from the next boundary cap."""
    one = _strand("solo")
    start, end, implicit = G._chrom_range(one, None, op="condense")
    assert (start, end) == (0, len(one)), "extent value must be unchanged"
    assert implicit is True, "a sole chromosome's end is the strand end — INFERRED"

    two = _strand("a", "b")
    start_a, end_a, implicit_a = G._chrom_range(two, "a", op="condense")
    assert implicit_a is False, "chromosome 'a' ends at a real boundary cap — READ"
    assert end_a == 3, "the second chromosome's boundary is at block 3"

    start_b, end_b, implicit_b = G._chrom_range(two, "b", op="condense")
    assert implicit_b is True, "the last chromosome runs to the strand end — INFERRED"
    assert end_b == len(two)


def test_the_flag_is_not_constant():
    """Both values must be reachable.

    A flag that is always True (or always False) records nothing and would let
    v20 hook a branch that never runs — the same class of defect as the extent
    it replaces. Asserting BOTH readings occur is what makes it a measurement.
    """
    two = _strand("a", "b")
    seen = {G._chrom_range(two, lab, op="condense")[2] for lab in ("a", "b")}
    assert seen == {True, False}, (
        f"the end_is_implicit flag took only {seen} — it must distinguish a "
        f"READ extent from an INFERRED one, or it is not an instrument"
    )


# ──────────────────────────────────────────────────────────────────────
# 4. §GROUP/v20 — the extent is now READ, at all four sites
# ──────────────────────────────────────────────────────────────────────

def test_a_grouped_chromosome_ends_at_the_closer_not_the_strand_end():
    """THE rc441 PREDICTION, now measured. Inside a group the last chromosome's end and
    the strand end are DIFFERENT indices, and the extent must be the former."""
    inner = _strand("a", "b")
    grouped = G.genome_group("sy", inner, dim=_DIM)
    # blocks: [ '[' , a-cap, t, t, b-cap, t, t, ']' ]
    inner_view = grouped[1:]
    start, end, implicit = G._chrom_range(inner_view, "b", op="condense")
    assert implicit is False, (
        "the extent must be READ from the closer, not inferred from the buffer end — "
        "this is precisely the branch rc441 named"
    )
    assert end == len(inner_view) - 1, (
        "chromosome 'b' ends BEFORE the ']' block, not at the end of the strand"
    )


def test_unit_end_walks_back_over_trailing_closers():
    """``_unit_end_before_closers`` is the named rule. Nested closers all belong to their
    enclosing frames, so the walk-back is over ALL of them, not just the last."""
    strand = _strand("a")
    assert G._unit_end_before_closers(strand) == len(strand), "ungrouped: unchanged"
    g1 = G.genome_group("in", strand, dim=_DIM)
    g2 = G.genome_group("out", g1, dim=_DIM)
    assert G._unit_end_before_closers(g2) == len(g2) - 2, (
        "two trailing closers belong to two frames; the unit ends before both"
    )


def test_mint_strand_append_at_end_lands_inside_the_group():
    """Splice site 3. ``centromere_at == n_turns`` is the append-at-end case. Under v19 it
    landed at ``len(strand)``; under v20 it must land BEFORE the closer, or the centromere
    would sit outside the chromosome that owns it while still parsing as well-formed."""
    coupling = G._HV.from_sequence(bytes([1] * _DIM), sectors=4)
    strand = _strand("solo")
    grouped = G.genome_group("sy", strand, dim=_DIM)
    n_turns = sum(1 for hv in grouped if G._cap_kind(hv) is None)
    minted = G.mint_strand(grouped, coupling=coupling, centromere_at=n_turns)
    assert len(minted) == len(grouped) + 1
    assert G._cap_kind(minted[-1]) == G.GROUP_CLOSE_MARKER, (
        "the closer must remain the LAST block — the splice goes before it"
    )
    assert G._cap_kind(minted[-2]) == G.CENTROMERE_CAP_MARKER, (
        "the append-at-end centromere lands inside the group, immediately before "
        "the closer. Landing after it is the silent v19 answer this rc removes."
    )


@pytest.mark.parametrize("n_chroms", [1, 2, 3])
def test_implicit_unit_end_is_the_strand_end_when_nothing_closes(n_chroms):
    """The ungrouped rule survives: with no closer to read, the strand end IS the answer."""
    strand = _strand(*[f"c{i}" for i in range(n_chroms)])
    assert G._implicit_unit_end(strand) == len(strand)
    assert G._unit_end_before_closers(strand) == len(strand)


def test_extent_values_are_byte_for_byte_what_rc440_returned():
    """The v20 change is INVISIBLE to an ungrouped strand. Every ``(start, end)`` pair must
    still equal the pre-rc441 derivation — `next boundary after start, else len(strand)`."""
    for labels in (("solo",), ("a", "b"), ("a", "b", "c")):
        strand = _strand(*labels)
        bounds = [i for i, hv in enumerate(strand)
                  if G._cap_kind(hv) in G._CHROM_BOUNDARY_MARKERS]
        for lab, b in zip(labels, bounds):
            start, end, _ = G._chrom_range(strand, lab, op="condense")
            nxt = [x for x in bounds if x > start]
            assert start == b
            assert end == (nxt[0] if nxt else len(strand)), (
                "the rc441/rc442 refactors changed an extent on an UNGROUPED strand — "
                "they must not"
            )
