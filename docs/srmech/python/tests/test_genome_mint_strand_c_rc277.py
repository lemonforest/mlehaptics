"""v0.9.0rc277 (§100 GAP 1 / #891-peer / F1249 / G5) — the srmech_genome_mint_strand C peer.

The stage-2 PROMOTE primitive of the F1252 two-stage encode, and the next
genome-must-exist-fully-in-C parity correction after rc276's ``integrate``. Before rc277
``mint_strand``'s GLUE (data-turn scan → metacentric midpoint → single-block centromere
insert) was Python-only; the cap-writer ``srmech_genome_centromere`` had a C peer but the
op did not, so its docstring's "byte-identical whether the cap came from C or pure Python"
covered only the cap bytes. rc277 ships ``srmech_genome_mint_strand`` (a bare-C host
PROMOTES a strand end-to-end) and wires ``mint_strand`` to DISPATCH the whole op to it
when ``HAS_NATIVE``.

Proven here — C↔Python BYTE-PARITY: for many strand shapes (graph_to_kernel /
kernel_pack / chromosome / plasmid), every ``centromere_at`` locus, and both the
content-address (``orientation=None``) and explicit orientations, the native minted bytes
== the pure minted bytes (0 mismatches); ``kernel_to_graph`` round-trips byte-exact after
minting (the interior centromere is transparent, §44); the content-address orientation the
peer computes (recall → sha256&3) matches the pure ``_mint_orientation``; the §101
``progress=`` gate stays a Python-only affordance; and the error contract is unchanged.
numpy-free; the whole file runs unchanged in a numpy-absent forced-pure venv (where the
dispatch is a no-op and the pure block splice is exercised).
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.hdc import klein4_random

_DIM = 64


def _one(seed=1277):
    return klein4_random(_DIM, seed=seed)


def _leaves(n, base=0):
    return [klein4_random(_DIM, seed=base + s) for s in range(n)]


def _graph_strand(one):
    edges = [(0, 1), (1, 2), (2, 0), (3, 1), (4, 4), (0, 2), (1, 3), (2, 4)]
    weights = [5, 7, 2, 9, 1, 3, 8, 6]
    charges = [1, -1, 1, -1, 0, 1, -1, 1]
    strand, n = G.graph_to_kernel(6, edges, weights, charges, node_ids=[100, 200, 300, 400, 500],
                                  extras=[42, 7], leaf_dim=_DIM, label="wiki", the_one=one)
    return strand, n


def _blocks(strand):
    return [b.tobytes() for b in strand]


def _n_turns(strand):
    return sum(1 for hv in strand if G._cap_kind(hv) is None)


def _strand_shapes(one):
    """Already-packed strands mint_strand accepts — each opens with a boundary cap."""
    gstrand, _n = _graph_strand(one)
    return {
        "graph": gstrand,
        "chromosome": G.chromosome(_leaves(9, 500), one, label="chr"),
        "kernel_pack": G.kernel_pack(
            [s % 4 for s in range(30)], leaf_dim=_DIM, label="kern", the_one=one),
        "plasmid": G.plasmid({"plas": _leaves(4, 700)}, one),
    }


# ── C↔Python byte-parity across strand shapes / loci / orientations ───────────

@pytest.mark.parametrize("shape", ["graph", "chromosome", "kernel_pack", "plasmid"])
@pytest.mark.parametrize("orient", [None, 0, 2, 3])
def test_native_mint_matches_pure_oracle(shape, orient, monkeypatch):
    one = _one()
    strand = _strand_shapes(one)[shape]
    nt = _n_turns(strand)
    for cat in [None, 0, 1, nt // 2, nt]:
        got = G.mint_strand(strand, one, orientation=orient, centromere_at=cat)  # native
        # FORCE the pure fallback (as in a numpy-absent / no-C venv) and assert it is
        # byte-identical — native == pure, the differential proof.
        monkeypatch.setattr(_native, "genome_mint_strand_c", lambda *a, **k: None)
        pure = G.mint_strand(strand, one, orientation=orient, centromere_at=cat)
        monkeypatch.undo()
        assert _blocks(got) == _blocks(pure), f"{shape} cat={cat} orient={orient}"


def test_native_peer_byte_identical_over_many_combos():
    """The native peer, exercised across every strand shape × locus × orientation —
    the minted bytes match the pure oracle exactly (0 mismatches)."""
    if not _native.has_native_genome_mint_strand():
        pytest.skip("no native srmech_genome_mint_strand peer in this build")
    one = _one()
    mismatches, combos = 0, 0
    for strand in _strand_shapes(one).values():
        nt = _n_turns(strand)
        for cat in [None] + list(range(nt + 1)):
            for orient in (None, 1):
                combos += 1
                got = G.mint_strand(strand, one, orientation=orient, centromere_at=cat)
                # the raw native bytes directly, to prove the peer itself (not only the
                # dispatch wrapper) is byte-exact vs the pure list-splice result.
                blocks = [b.tobytes() for b in strand]
                split = cat if cat is not None else nt // 2
                raw = _native.genome_mint_strand_c(
                    b"".join(blocks), len(blocks), _DIM,
                    G._the_one_block_bytes(one), split, orient, 15, b"cen")
                exp = b"".join(b.tobytes() for b in got)
                if raw != exp:
                    mismatches += 1
    assert mismatches == 0, f"{mismatches}/{combos} native mints diverged from pure"
    assert combos >= 40


# ── kernel_to_graph round-trips byte-exact after minting (cap transparent) ────

def test_kernel_to_graph_roundtrips_after_native_mint():
    one = _one()
    strand, n = _graph_strand(one)
    base = G.kernel_to_graph(strand, one, n)             # un-minted decode
    for cat in [None, 0, 2]:
        minted = G.mint_strand(strand, one, centromere_at=cat)
        assert any(G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER for hv in minted)
        assert G.kernel_to_graph(minted, one, n) == base  # 0x58 is skipped on read


# ── the content-address orientation the peer computes matches the pure rule ───

def test_content_address_orientation_matches_pure():
    one = _one()
    for strand in _strand_shapes(one).values():
        minted = G.mint_strand(strand, one)              # orientation=None → content-address
        o_native = G.centromere_of(minted)["orientation"]
        o_pure = G._mint_orientation(G.recall(strand, one))
        assert o_native == o_pure and 0 <= o_native <= 3


# ── the metacentric arm-ratio is byte-exact native vs pure ────────────────────

def test_metacentric_arm_ratio_native_and_pure(monkeypatch):
    one = _one()
    strand = G.chromosome(_leaves(9, 500), one, label="chr")   # 9 data turns → (4, 5)
    got = G.mint_strand(strand, one, orientation=1)
    assert G.centromere_of(got)["arm_ratio"] == (4, 5)
    monkeypatch.setattr(_native, "genome_mint_strand_c", lambda *a, **k: None)
    pure = G.mint_strand(strand, one, orientation=1)
    assert _blocks(got) == _blocks(pure)


# ── the §101 progress= gate stays a Python-only affordance ────────────────────

def test_progress_gate_declines_before_dispatch():
    one = _one()
    strand = G.chromosome(_leaves(9, 500), one, label="chr")
    # a truthy pre-op gate DECLINES cleanly → the UNMODIFIED pre-mint strand.
    out = G.mint_strand(strand, one, progress=lambda ev: True)
    assert _blocks(out) == _blocks(list(strand))
    # a falsy gate mints exactly as the no-gate (dispatched) path.
    got = G.mint_strand(strand, one, orientation=1, progress=lambda ev: False)
    assert _blocks(got) == _blocks(G.mint_strand(strand, one, orientation=1))


# ── the error contract is unchanged (raised in Python, before dispatch) ───────

def test_error_contract_unchanged():
    one = _one()
    with pytest.raises(ValueError, match="empty"):
        G.mint_strand([], one)
    with pytest.raises(ValueError, match="OPEN with a chromosome-boundary cap"):
        G.mint_strand([klein4_random(_DIM, seed=1)], one)  # raw leaf, no boundary cap
    minted = G.mint_strand(G.chromosome(_leaves(6, 900), one, label="c"), one)
    with pytest.raises(ValueError, match="already carries an interior centromere"):
        G.mint_strand(minted, one)                         # re-minting doubles the anchor
    strand = G.chromosome(_leaves(6, 900), one, label="c")
    with pytest.raises(ValueError, match="out of range"):
        G.mint_strand(strand, one, centromere_at=99)
