"""§v19 IMPLICIT CLOSE — the inference every splice position rests on, made visible.

rc441 (``#T1148``) — the v20 prerequisites. ``GENOME_FORMAT_VERSION`` stays **19**;
this file introduces no marker and no grammar.

THE DEFECT, STATED PRECISELY. A v19 strand has no CLOSER cap. A chromosome opens
with a boundary cap and simply runs until the next opener, or off the end of the
strand. So *"where does this unit end?"* is never READ — it is INFERRED. Two shared
helpers encode that inference, and four call sites splice at the position it
returns:

======================================  =================================================
``genome_nth_data_turn``                returns ``n_blocks`` when ``split == n_turns``
``genome_label_range``                  ``end`` = next boundary index, else ``n_blocks``
``mint_strand`` / ``_chrom_range``      the Python twins of the same two
======================================  =================================================

Today the inference is **accidentally correct**: with no closer, the end of a unit
and the start of the next are the SAME index. It stops being correct the moment a
closer exists, and it stops silently — the splice simply lands on the wrong side of
a cap and produces a well-formed strand that means something else.

WHAT THIS RC DID, AND WHAT IT DID NOT. It did **not** replace the inference with an
explicit read, and that is a finding rather than a shortfall: at v19 there is no
closer marker to read, so "make the extent explicit" is not expressible without
first minting the closer — which is v20's format change, not a prerequisite for it.
Shipping the marker here under a prerequisite's name would be the very thing the
brief warns against.

What it did instead is make the inference **loud**, in the three ways that were
missing:

1. **The rule has one name per projection.** ``_implicit_unit_end`` (Python) and the
   ``§v19 IMPLICIT CLOSE`` block above ``genome_nth_data_turn`` (C). Through rc440 it
   was re-derived independently at four sites with no shared name, so a v20 author
   had nothing to grep for.
2. **The extent now reports its own provenance.** Both helpers return, alongside the
   extent, whether it was READ from a marker or INFERRED from the buffer end
   (``end_is_implicit`` / ``at_unit_end``). Through rc440 a bare ``len(strand)`` came
   back either way and the caller could not tell them apart — so there was no place
   for v20 to hook and nothing to assert against. Every existing return value is
   byte-for-byte unchanged; the flag is purely additive.
3. **A guard that fires when the closer arrives** — the marker-vocabulary pin below.

THE PIN IS THE POINT. ``test_cap_marker_vocabulary_is_pinned`` fails the moment v20
adds a closer marker, and its message routes the author to all four splice sites.
That is deliberate: this gate is *designed to go red in rc442*. Going red there is
it working, not it breaking.

No stdlib ``fractions`` / ``math`` / ``decimal`` / numpy. No ``abs()`` — a block index
is a non-negative position, not a magnitude.
"""

from __future__ import annotations

import pytest

from srmech.biology import genome as G


# ──────────────────────────────────────────────────────────────────────
# 1. The version this reasoning is valid for
# ──────────────────────────────────────────────────────────────────────

def test_format_version_is_still_19():
    """rc441 is the v20 PREREQUISITES, not v20. If this fails, the closer may
    now exist and every implicit-close inference below needs re-deriving."""
    assert G.GENOME_FORMAT_VERSION == 19, (
        f"GENOME_FORMAT_VERSION is {G.GENOME_FORMAT_VERSION}, not 19 — if the "
        f"format moved, revisit the four §v19 IMPLICIT CLOSE splice sites "
        f"(mint_strand insert_at, _chrom_range end, and their C twins "
        f"genome_nth_data_turn / genome_label_range)"
    )


# ──────────────────────────────────────────────────────────────────────
# 2. The guard that fires when v20's closer arrives
# ──────────────────────────────────────────────────────────────────────

#: The v19 cap vocabulary, pinned by VALUE. A closer cap is a NEW marker byte, so
#: minting one necessarily changes this set — which is exactly the event that
#: invalidates the implicit-close inference at all four splice sites.
_V19_CAP_MARKERS = frozenset({
    G.CHROM_CAP_MARKER, G.GENE_CAP_MARKER, G.REGULATORY_GENE_MARKER,
    G.BOOLEAN_GENE_MARKER, G.THRESHOLD_GENE_MARKER, G.GRADED_GENE_MARKER,
    G.KERNEL_HEADER_MARKER, G.KERNEL_TELOMERE_MARKER, G.ACTIVE_TELOMERE_MARKER,
    G.CENTROMERE_CAP_MARKER, G.DIPLOID_TELOMERE_MARKER, G.CHROMATIN_MARKER,
    G.FIBER_CAP_MARKER, G.OCT_FIBER_CAP_MARKER,
})

#: The subset that OPENS a unit. Under v19 an opener is the only thing that can end
#: the PREVIOUS unit — which is the whole inference.
_V19_BOUNDARY_MARKERS = frozenset({
    G.CHROM_CAP_MARKER, G.KERNEL_TELOMERE_MARKER,
    G.ACTIVE_TELOMERE_MARKER, G.DIPLOID_TELOMERE_MARKER,
})


def test_cap_marker_vocabulary_is_pinned():
    """A new cap marker — v20's closer above all — must trip this gate.

    THIS GATE IS MEANT TO GO RED IN rc442. When it does, the fix is not to add
    the new byte to the set and move on: it is to revisit the four splice sites
    named in the message, because a closer changes what "the end of a unit"
    means at every one of them.
    """
    live = frozenset(G._LEAF_WIDE_BLOCK_MARKERS)
    added = live - _V19_CAP_MARKERS
    removed = _V19_CAP_MARKERS - live
    assert not added and not removed, (
        f"the genome cap-marker vocabulary moved (added={sorted(added)}, "
        f"removed={sorted(removed)}).\n"
        f"If one of these is v20's CLOSER cap, the §v19 IMPLICIT CLOSE "
        f"inference is now WRONG at four splice sites and each must be "
        f"re-derived against the closer rather than the next opener:\n"
        f"  1. C  genome_nth_data_turn  (srmech_genome.c) — append-at-end locus\n"
        f"  2. C  genome_label_range    (srmech_genome.c) — the `end` extent\n"
        f"  3. Py mint_strand insert_at (genome.py) — the centromere splice\n"
        f"  4. Py _chrom_range end      (genome.py) — the chromatin splice\n"
        f"Each now reports whether its extent was READ or INFERRED; the "
        f"INFERRED branch is the one that must change."
    )
    assert _V19_BOUNDARY_MARKERS <= live, "a boundary marker vanished"


def test_no_marker_is_named_like_a_closer():
    """v19 has no closer by construction. A constant whose NAME says otherwise
    means the format moved without this file noticing."""
    suspicious = [
        n for n in dir(G)
        if n.endswith("_MARKER")
        and any(w in n.upper() for w in ("CLOSE", "CLOSER", "END_CAP", "TERMINATOR"))
    ]
    assert not suspicious, (
        f"marker constant(s) named like a closer: {suspicious} — v19 has none; "
        f"see the four splice sites listed above"
    )


# ──────────────────────────────────────────────────────────────────────
# 3. The extent helpers now report their own provenance
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


def test_extent_values_are_byte_for_byte_what_rc440_returned():
    """The flag is ADDITIVE. Every (start, end) pair must equal the pre-rc441
    derivation — `next boundary after start, else len(strand)` — exactly."""
    for labels in (("solo",), ("a", "b"), ("a", "b", "c")):
        strand = _strand(*labels)
        bounds = [i for i, hv in enumerate(strand)
                  if G._cap_kind(hv) in G._CHROM_BOUNDARY_MARKERS]
        for lab, b in zip(labels, bounds):
            start, end, _ = G._chrom_range(strand, lab, op="condense")
            nxt = [x for x in bounds if x > start]
            assert start == b
            assert end == (nxt[0] if nxt else len(strand)), (
                "the rc441 refactor changed an extent — it must not"
            )


# ──────────────────────────────────────────────────────────────────────
# 4. mint_strand's append-at-end splice
# ──────────────────────────────────────────────────────────────────────

def test_mint_strand_append_at_end_lands_at_the_strand_end():
    """``centromere_at == n_turns`` is the append-at-end case: the §v19 implicit
    close puts the cap at ``len(strand)``. Under v20 it must go BEFORE the
    closer, which is why the branch is now named rather than inlined."""
    coupling = G._HV.from_sequence(bytes([1] * _DIM), sectors=4)
    strand = _strand("solo")
    n_turns = sum(1 for hv in strand if G._cap_kind(hv) is None)
    minted = G.mint_strand(strand, coupling=coupling, centromere_at=n_turns)
    assert len(minted) == len(strand) + 1
    assert G._cap_kind(minted[-1]) == G.CENTROMERE_CAP_MARKER, (
        "the append-at-end centromere must land at the very end of the strand "
        "under v19's implicit close"
    )
    # And an interior split still lands interior — the flag's other branch.
    interior = G.mint_strand(strand, coupling=coupling, centromere_at=1)
    assert G._cap_kind(interior[-1]) != G.CENTROMERE_CAP_MARKER


@pytest.mark.parametrize("n_chroms", [1, 2, 3])
def test_implicit_unit_end_is_the_strand_end(n_chroms):
    """The named rule returns exactly what the four sites used to inline."""
    strand = _strand(*[f"c{i}" for i in range(n_chroms)])
    assert G._implicit_unit_end(strand) == len(strand)
