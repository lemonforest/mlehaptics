"""v0.9.0rc262 (§95.1d / #1407 / F1244) — the coherency-translation-layer CAPSTONE.

A Tier-1 STICK provirus (a retrovirus genome — telomere-capped, no centromere) integrates INTO
a Tier-2 host genome (a eukaryote — MINTED + DIPLOID chromosomes), and thereafter EVERY mode
still recovers — because rc258 centromere, rc259 diploid, and the mint umbrella ALL couple every
turn through the SAME the_one (one k=3 cascade at different rungs, ADR-0005). The translation
between the Tier-1 and Tier-2 levels is FREE: it needs no conversion because they are the same
cascade. srmech.amsc.genome.integrate(host, provirus, at=) splices the provirus into the host at
a chromosome boundary; the coherence is the point.

Proven here: integration grows the strand; partition recovers all chromosomes; the host's minted
centromere_of and diploid recover_diploid still work post-integration; the provirus recovers; the
at= locus; provirus validation; and the integrated genome round-trips through disk. This completes
the #1407 biology-native genome architecture arc. numpy-free.
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome as G
from srmech.amsc.hdc import klein4_random


def _one(seed=7):
    return klein4_random(64, seed=seed)


def _lv(n, base=0):
    return [klein4_random(64, seed=base + s) for s in range(n)]


def _host(one):
    # a Tier-2 eukaryote: a MINTED chromosome + a DIPLOID chromosome, on ONE the_one
    return G.mint({"astronomy": _lv(12, 100)}, one) + G.diploid(_lv(6, 200), one, label="chr7")


def _provirus(one):
    # a Tier-1 stick (a retrovirus genome), same the_one
    return G.plasmid({"provirus": _lv(3, 300)}, one)


# ── the integration ─────────────────────────────────────────────────────────

def test_integration_grows_the_strand_by_the_provirus():
    one = _one()
    host, provirus = _host(one), _provirus(one)
    integrated = G.integrate(host, provirus)
    assert len(integrated) == len(host) + len(provirus)


def test_partition_recovers_all_three_chromosomes():
    one = _one()
    integrated = G.integrate(_host(one), _provirus(one))
    parts = G.partition(integrated, one)
    assert set(parts) == {"astronomy", "chr7", "provirus"}
    assert len(parts["provirus"]) == 3
    assert [x.tobytes() for x in parts["provirus"]] == [x.tobytes() for x in _lv(3, 300)]


# ── the COHERENCE PROOF: every mode still recovers post-integration ─────────

def test_minted_centromere_survives_integration():
    one = _one()
    integrated = G.integrate(_host(one), _provirus(one))
    start = next(i for i, hv in enumerate(integrated)
                 if G._cap_kind(hv) == G.CHROM_CAP_MARKER)          # the minted chromosome
    info = G.centromere_of(integrated[start:])
    assert info is not None and info["orientation"] in (0, 1, 2, 3)


def test_diploid_survives_integration():
    one = _one()
    integrated = G.integrate(_host(one), _provirus(one))
    start = next(i for i, hv in enumerate(integrated)
                 if G._cap_kind(hv) == G.DIPLOID_TELOMERE_MARKER)
    end = next((i for i in range(start + 1, len(integrated))
                if G._cap_kind(integrated[i]) in G._CHROM_BOUNDARY_MARKERS), len(integrated))
    rec = G.recover_diploid(integrated[start:end], one)
    assert [x.tobytes() for x in rec] == [x.tobytes() for x in _lv(6, 200)]


# ── the at= locus + validation ──────────────────────────────────────────────

def test_integrate_at_locus():
    one = _one()
    host, provirus = _host(one), _provirus(one)
    front = G.integrate(host, provirus, at=0)                       # before chromosome 0
    assert list(G.partition(front, one))[0] == "provirus"
    end = G.integrate(host, provirus, at=None)                      # after the last
    assert list(G.partition(end, one))[-1] == "provirus"


def test_integrate_rejects_a_non_chromosome_provirus():
    one = _one()
    with pytest.raises(ValueError):
        G.integrate(_host(one), [klein4_random(64, seed=1)])        # a bare turn, no boundary cap


def test_integrate_rejects_at_out_of_range():
    one = _one()
    with pytest.raises(ValueError):
        G.integrate(_host(one), _provirus(one), at=99)


# ── persistence: the integrated genome round-trips ──────────────────────────

def test_integrated_genome_round_trips_through_disk(tmp_path):
    one = _one()
    integrated = G.integrate(_host(one), _provirus(one))
    G.genome_save(integrated, tmp_path, the_one=one)
    loaded, _o, _l = G.genome_load(tmp_path, the_one=one)
    assert set(G.partition(loaded, one)) == {"astronomy", "chr7", "provirus"}
    # and the recovered provirus is still exact after the disk round-trip
    assert [x.tobytes() for x in G.partition(loaded, one)["provirus"]] == \
           [x.tobytes() for x in _lv(3, 300)]
