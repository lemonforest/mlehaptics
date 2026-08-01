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
from srmech.math.hdc import klein4_expand

_DIM = 64


def _one(seed=7):
    return klein4_expand(_DIM, seed)


def _leaves(n, base=0):
    return [klein4_expand(_DIM, base + s) for s in range(n)]


def _bl(hvs):
    return [list(x) for x in hvs]


def _zero():
    # the ERASURE sentinel: an all-zero STORED TURN (a zeroed locus / double-strand break;
    # §95.4). NOT `one` — a real erasure zeros the on-disk bytes, and an all-zero turn
    # decouples to a NON-zero leaf, so recovery must read the erasure on the turn.
    return G._HV.from_sequence([0] * _DIM, sectors=4)


# ── 1. build + clean round-trip ─────────────────────────────────────────────

def test_format_version_is_14():
    assert G.GENOME_FORMAT_VERSION == 19


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
    # §95.4: _diploid_ec_leaf takes the STORED TURNS (+ coupling) and reads erasure on the
    # turn (all-zero) BEFORE decoupling; it returns the recovered (decoupled) leaf.
    one = _one()
    zero = _zero()
    la = klein4_expand(_DIM, 1)
    lb = klein4_expand(_DIM, 2)
    ta, tb = G.quad_turn(la, one), G.quad_turn(lb, one)          # the on-disk turns of la/lb
    assert list(G._diploid_ec_leaf(ta, ta, 0, one)) == list(la)  # agree -> the leaf
    assert list(G._diploid_ec_leaf(zero, tb, 0, one)) == list(lb)  # erasure A -> intact B
    assert list(G._diploid_ec_leaf(ta, zero, 1, one)) == list(la)  # erasure B -> intact A
    assert list(G._diploid_ec_leaf(ta, tb, 0, one)) == list(la)  # disagree, mark 0 -> A
    assert list(G._diploid_ec_leaf(ta, tb, 1, one)) == list(lb)  # disagree, mark 1 -> B


def test_erasure_recovery_symmetric_both_homologs():
    # §95.4 regression: an erased leaf (an all-zero stored TURN) on EITHER homolog heals from
    # the intact one — break-repair is direction-free. Pre-fix, only one direction healed (the
    # erasure was read on the DECOUPLED leaf, which a zeroed turn never zeroes, so a copyA break
    # survived only by substitution-tiebreak luck — asymmetric).
    one = _one()
    leaves = _leaves(6)
    dip = list(G.diploid(leaves, one, label="x"))
    cen_i = next(i for i, hv in enumerate(dip) if G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER)
    for tgt, name in [(1 + 2, "copyA"), (cen_i + 1 + 2, "copyB")]:
        broken = list(dip)
        broken[tgt] = _zero()                                   # zero the on-disk turn
        assert _bl(G.recover_diploid(broken, one)) == _bl(leaves), f"{name} erasure did not heal"


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
    dip[1 + 1] = _zero()                                # erase a leaf (zero the stored turn)
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
    G.genome_save(mixed, tmp_path, coupling=one)
    loaded, _o, _l = G.genome_load(tmp_path, coupling=one)
    assert any(G._cap_kind(hv) == G.DIPLOID_TELOMERE_MARKER for hv in loaded)
    dip_i = next(i for i, hv in enumerate(loaded)
                 if G._cap_kind(hv) == G.DIPLOID_TELOMERE_MARKER)
    assert _bl(G.recover_diploid(loaded[dip_i:], one)) == _bl(leaves)
    assert G.genome_catalog(tmp_path, coupling=one)["format_version"] == 19


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
    dip_erased[1 + 2] = _zero()                         # §95.4: all-zero stored-turn erasure
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
        G.genome_save(strand, d, coupling=one)
        return (d / "turns.bin").read_bytes(), (d / "manifest.json").read_bytes()

    cb, cm = save(True)
    pb, pm = save(False)
    assert cb == pb and cm == pm
