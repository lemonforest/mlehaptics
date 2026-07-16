"""v0.9.0rc259 (§95b, #1407 / F1244) — the DIPLOID pairing primitive: the erasure/break specialist.

The second rung of the #1407 biology-native genome architecture. A DIPLOID chromosome (marker
0x44 'D') stores TWO homologous copies of the kernel (maternal | paternal) split by an interior
centromere whose orientation is the which-template mark — 2 copies + 1 mark = 3 = the k=3 triality
(F291). It is the ERASURE/BREAK specialist (measured R-RBS-LM-DIPLOID-EC): on a DETECTABLE loss
(an erased leaf — a double-strand break) recover_diploid fills from the intact homolog, reaching
triality-level fidelity at 2× not 3×; on a substitution disagreement the centromere mark is the
tiebreak. It composes rc258's centromere directly (the centromere IS the diploid mark).

Proven here: the build + clean round-trip, the per-leaf EC (agree / erasure-fill / mark-tiebreak),
erasure recovery on a real strand, recall (raw 2n) vs recover_diploid (corrected n), partition +
persistence of a diploid in a mixed genome, format v14 dual-read, and the 1:1 C↔Python byte-parity
of srmech_genome_diploid + srmech_genome_recover_diploid (gated on the native peer). numpy-free.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.hdc import klein4_random

_DIM = 64


def _one(seed=7):
    return klein4_random(_DIM, seed=seed)


def _leaves(n, base=0):
    return [klein4_random(_DIM, seed=base + s) for s in range(n)]


def _bl(hvs):
    return [list(x) for x in hvs]


# ── 1. build + clean round-trip ─────────────────────────────────────────────

def test_format_version_is_14():
    assert G.GENOME_FORMAT_VERSION == 14


def test_marker_is_0x44():
    assert G.DIPLOID_TELOMERE_MARKER == 0x44


def test_diploid_shape_and_clean_recover():
    one = _one()
    leaves = _leaves(6)
    dip = G.diploid(leaves, one, label="astronomy")
    assert len(dip) == 2 * 6 + 2                        # cap + copyA + centromere + copyB
    assert G._cap_kind(dip[0]) == G.DIPLOID_TELOMERE_MARKER
    assert any(G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER for hv in dip)
    assert _bl(G.recover_diploid(dip, one)) == _bl(leaves)


def test_recover_rejects_non_diploid():
    one = _one()
    with pytest.raises(ValueError):
        G.recover_diploid(G.chromosome(_leaves(3), one, label="s"), one)


# ── 2. the per-leaf EC (agree / erasure / substitution-mark) ────────────────

def test_ec_leaf_agree_erasure_disagree():
    a = klein4_random(_DIM, seed=1)
    b = klein4_random(_DIM, seed=2)
    zero = G._HV.from_sequence([0] * _DIM, sectors=4)
    assert list(G._diploid_ec_leaf(a, a, 0)) == list(a)          # agree
    assert list(G._diploid_ec_leaf(zero, b, 0)) == list(b)       # erasure A -> intact B
    assert list(G._diploid_ec_leaf(a, zero, 1)) == list(a)       # erasure B -> intact A
    assert list(G._diploid_ec_leaf(a, b, 0)) == list(a)          # disagree, mark 0 -> A
    assert list(G._diploid_ec_leaf(a, b, 1)) == list(b)          # disagree, mark 1 -> B


def test_erasure_recovery_on_a_real_strand():
    one = _one()
    leaves = _leaves(6)
    dip = list(G.diploid(leaves, one, label="x"))
    dip[1 + 2] = one                       # erase copyA leaf 2 (uncouples to all-zero)
    assert _bl(G.recover_diploid(dip, one)) == _bl(leaves)       # filled from intact copyB


# ── 3. recall (raw 2n) vs recover (corrected n) + the erasure-specialist claim ──

def test_recall_returns_both_copies_recover_returns_one():
    one = _one()
    leaves = _leaves(6)
    dip = G.diploid(leaves, one, label="d")
    assert len(G.recall(dip, one)) == 12                # both homolog copies (raw)
    assert len(G.recover_diploid(dip, one)) == 6        # the corrected content


def test_diploid_is_the_erasure_specialist():
    # a single-copy chromosome has NO erasure recovery; the diploid fills from the homolog
    one = _one()
    leaves = _leaves(6)
    dip = list(G.diploid(leaves, one, label="x"))
    dip[1 + 1] = one                                    # erase a leaf
    assert _bl(G.recover_diploid(dip, one)) == _bl(leaves)   # recovered — the 2x erasure win


# ── 4. partition + persistence in a mixed genome ────────────────────────────

def test_partition_recognizes_the_diploid_boundary():
    one = _one()
    leaves = _leaves(6)
    mixed = G.chromosome(_leaves(3), one, label="stick") + G.diploid(leaves, one, label="dp")
    parts = G.partition(mixed, one)
    assert set(parts) == {"stick", "dp"}
    assert len(parts["dp"]) == 12                       # both homolog copies (raw turns)


def test_diploid_persists_and_reloads(tmp_path):
    one = _one()
    leaves = _leaves(6)
    mixed = G.chromosome(_leaves(3), one, label="stick") + G.diploid(leaves, one, label="dp")
    G.genome_save(mixed, tmp_path, the_one=one)
    loaded, _o, _l = G.genome_load(tmp_path, the_one=one)
    assert any(G._cap_kind(hv) == G.DIPLOID_TELOMERE_MARKER for hv in loaded)
    dip_i = next(i for i, hv in enumerate(loaded)
                 if G._cap_kind(hv) == G.DIPLOID_TELOMERE_MARKER)
    assert _bl(G.recover_diploid(loaded[dip_i:], one)) == _bl(leaves)
    assert G.genome_catalog(tmp_path, the_one=one)["format_version"] == 14


# ── 5. 1:1 C↔Python byte-parity (gated on the native peer) ──────────────────

_native_dip = pytest.mark.skipif(
    not _native.has_native_genome_diploid(),
    reason="native srmech_genome_diploid peer absent — pure path is the complete alternative")


@_native_dip
def test_parity_diploid_strand(monkeypatch):
    one = _one()
    leaves = _leaves(6)
    c = b"".join(hv.tobytes() for hv in G.diploid(leaves, one, label="astro"))
    monkeypatch.setattr(_native, "has_native_genome_diploid", lambda: False)
    pure = b"".join(hv.tobytes() for hv in G.diploid(leaves, one, label="astro"))
    assert c == pure


@_native_dip
def test_parity_recover_diploid_clean_and_erasure(monkeypatch):
    one = _one()
    leaves = _leaves(6)
    dip = G.diploid(leaves, one, label="astro")
    dip_erased = list(dip)
    dip_erased[1 + 2] = one
    for strand in (dip, dip_erased):
        c = b"".join(hv.tobytes() for hv in G.recover_diploid(strand, one))
        monkeypatch.setattr(_native, "has_native_genome_recover_diploid", lambda: False)
        pure = b"".join(hv.tobytes() for hv in G.recover_diploid(strand, one))
        monkeypatch.undo()
        assert c == pure
        assert c == b"".join(l.tobytes() for l in leaves)      # both recover the original


@_native_dip
def test_parity_diploid_genome_persistence(tmp_path, monkeypatch):
    one = _one()
    strand = (G.chromosome(_leaves(3), one, label="stick")
              + G.diploid(_leaves(6), one, label="dp"))

    def save(native):
        d = tmp_path / ("nat" if native else "pure")
        d.mkdir()
        monkeypatch.setattr(_native, "has_native_genome", lambda: native)
        G.genome_save(strand, d, the_one=one)
        return (d / "turns.bin").read_bytes(), (d / "manifest.json").read_bytes()

    cb, cm = save(True)
    pb, pm = save(False)
    assert cb == pb and cm == pm
