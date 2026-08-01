"""v0.9.0rc276 (§95.1d / #891 / F1244 / G4) — the srmech_genome_integrate C peer.

The stage-2 SPLICE primitive of the F1252 two-stage encode, and the first
genome-must-exist-fully-in-C parity correction from the rc273 C-host audit. Before
rc276 the ``integrate`` boundary-scan → locus → splice orchestration was Python-only;
its docstring's "a C-only host integrates identically" claim had NO C peer. rc276 ships
``srmech_genome_integrate`` (a bare-C host integrates end-to-end) and wires ``integrate``
to DISPATCH its splice to that peer when ``HAS_NATIVE``.

Proven here — C↔Python BYTE-PARITY: for many host / provirus / ``at`` combinations
(plasmid / nuclear-centromere / diploid chromosomes; every locus; empty host) the native
splice bytes == the pure splice bytes (0 mismatches); the §135/F1251 width-coherence
HONEST-DECLINE (`integrated=0` → Python ``None``) matches; the ``compatible=`` hook stays
a Python-only affordance; and the integrated genome still partitions (the coherence
survives the C splice). numpy-free; the whole file runs unchanged in a numpy-absent
forced-pure venv (where the dispatch is a no-op and the pure block splice is exercised).
"""
from __future__ import annotations

import pytest

from srmech.biology import genome as G
from srmech.amsc import _native
from srmech.math.hdc import klein4_expand


# ── builders (mirroring test_genome_integrate_rc262) ─────────────────────────

def _one(width=64, seed=7):
    return klein4_expand(width, seed)


def _lv(n, base=0, width=64):
    return [klein4_expand(width, base + s) for s in range(n)]


def _rich_host(one):
    # a Tier-2 eukaryote with THREE chromosomes on ONE coupling: a MINTED (nuclear,
    # interior-centromere) chromosome + a PLASMID (Tier-1) + a DIPLOID chromosome.
    return (G.mint({"astro": _lv(12, 100)}, one)
            + G.plasmid({"plas": _lv(3, 400)}, one)
            + G.diploid(_lv(6, 200), one, label="chr7"))


def _provirus(one):
    return G.plasmid({"provirus": _lv(3, 300)}, one)


def _blocks(strand):
    return [b.tobytes() for b in strand]


def _n_chrom(host):
    return sum(1 for hv in host if G._cap_kind(hv) in G._CHROM_BOUNDARY_MARKERS)


def _pure_splice(host, provirus, at):
    """The ORACLE: the direct Python list splice (no dispatch, no gate) — exactly
    ``host[:locus] + provirus + host[locus:]`` for a valid ``at``."""
    host = list(host)
    provirus = list(provirus)
    bounds = [i for i, hv in enumerate(host)
              if G._cap_kind(hv) in G._CHROM_BOUNDARY_MARKERS]
    locus = len(host) if at is None else (bounds[at] if at < len(bounds) else len(host))
    return host[:locus] + provirus + host[locus:]


# ── C↔Python byte-parity across every locus ──────────────────────────────────

@pytest.mark.parametrize("at", [None, 0, 1, 2, 3])
def test_native_splice_matches_pure_oracle(at, monkeypatch):
    one = _one()
    host, prov = _rich_host(one), _provirus(one)
    assert _n_chrom(host) == 3 and at is None or at <= 3

    got = G.integrate(host, prov, at=at)               # native path when HAS_NATIVE
    expected = _pure_splice(host, prov, at)
    assert _blocks(got) == _blocks(expected)           # correct vs the oracle

    # FORCE the pure fallback (as in a numpy-absent / no-C venv) and assert it is
    # byte-identical to whatever `got` was — native == pure, the differential proof.
    monkeypatch.setattr(_native, "genome_integrate_c", lambda *a, **k: None)
    pure = G.integrate(host, prov, at=at)
    assert _blocks(pure) == _blocks(got)


def test_native_peer_byte_identical_over_host_shapes():
    """The native peer, exercised directly across host chromosome counts 1..3 and
    every valid `at` — the spliced bytes match the pure oracle exactly."""
    if not _native.has_native_genome_integrate():
        pytest.skip("no native srmech_genome_integrate peer in this build")
    one = _one()
    prov = _provirus(one)
    shapes = {
        1: G.mint({"astro": _lv(12, 100)}, one),
        2: G.mint({"astro": _lv(12, 100)}, one) + G.plasmid({"plas": _lv(3, 400)}, one),
        3: _rich_host(one),
    }
    mismatches = 0
    combos = 0
    for hk, host in shapes.items():
        for at in [None] + list(range(hk + 1)):
            combos += 1
            got = G.integrate(host, prov, at=at)
            exp = _pure_splice(host, prov, at)
            if _blocks(got) != _blocks(exp):
                mismatches += 1
    assert mismatches == 0, f"{mismatches}/{combos} native splices diverged from pure"
    assert combos >= 9


# ── empty host coheres with any provirus ─────────────────────────────────────

def test_empty_host_integrates_to_the_provirus():
    one = _one()
    prov = _provirus(one)
    got = G.integrate([], prov)
    assert _blocks(got) == _blocks(list(prov))


# ── §135/F1251 width-coherence honest-decline ────────────────────────────────

def test_width_mismatch_is_honest_declined_native_and_pure():
    one64 = _one(width=64, seed=7)
    one32 = _one(width=32, seed=9)
    host = _rich_host(one64)                            # 64-wide
    prov32 = G.plasmid({"provirus": _lv(3, 300, width=32)}, one32)   # 32-wide
    # Python gates on width BEFORE dispatch -> None (host unchanged), native or pure.
    assert G.integrate(host, prov32) is None


def test_native_peer_declines_width_mismatch_directly():
    """The C gate itself: called directly with mismatched leaf dims, the peer returns
    integrated=False (the C analog of None) — NEVER a forced splice at a bad width."""
    if not _native.has_native_genome_integrate():
        pytest.skip("no native srmech_genome_integrate peer in this build")
    one64 = _one(width=64, seed=7)
    one32 = _one(width=32, seed=9)
    host = _rich_host(one64)
    prov32 = G.plasmid({"provirus": _lv(3, 300, width=32)}, one32)
    hb = [b.tobytes() for b in host]
    pb = [b.tobytes() for b in prov32]
    res = _native.genome_integrate_c(b"".join(hb), len(hb), 64,
                                     b"".join(pb), len(pb), 32, -1)
    assert res is not None and res[1] is False and res[0] == b""


# ── the compatible= hook stays Python-only ───────────────────────────────────

def test_compatible_hook_is_python_only_and_declines():
    one = _one()
    host, prov = _rich_host(one), _provirus(one)
    assert G.integrate(host, prov, compatible=lambda h, p: False) is None
    # a True hook integrates exactly as the no-hook (dispatched) path
    got = G.integrate(host, prov, compatible=lambda h, p: True)
    assert _blocks(got) == _blocks(_pure_splice(host, prov, None))


# ── the coherence survives the C splice ──────────────────────────────────────

def test_integrated_genome_still_partitions_after_dispatch():
    one = _one()
    integrated = G.integrate(_rich_host(one), _provirus(one))
    parts = G.partition(integrated, one)
    assert set(parts) == {"astro", "plas", "chr7", "provirus"}
    assert [x.tobytes() for x in parts["provirus"]] == [x.tobytes() for x in _lv(3, 300)]


# ── validation errors are unchanged (raised in Python, before dispatch) ──────

def test_non_chromosome_provirus_still_raises():
    one = _one()
    with pytest.raises(ValueError):
        G.integrate(_rich_host(one), [klein4_expand(64, 1)])


def test_at_out_of_range_still_raises():
    one = _one()
    with pytest.raises(ValueError):
        G.integrate(_rich_host(one), _provirus(one), at=99)
