"""v0.9.0rc273 (§95.1d / #1407 / F1244 / F1251) — the integrate COMPATIBILITY GATE.

F1251 (attested Shropshire bacterial genomics) measured that horizontal transfer has
EMPIRICAL BOUNDARIES: CG307 plasmids are shared with other clonal groups EXCEPT CG258,
which stays SEGREGATED. So `integrate` is NOT universal — it must be able to REFUSE. rc273
adds a compatibility gate: `integrate(host, provirus, *, at=None, compatible=None)` checks
host<->provirus coherence BEFORE splicing and HONEST-DECLINES on incompatibility (returns
None, host unchanged — mirroring telomere_tick's senescence), NOT forcing every element into
every host.

The DEFAULT predicate is the F1244 coherence contract made checkable: host + provirus must
share the coupling WIDTH (== coupling / leaf_dim); two genomes at different widths were coupled
through different invariants and cannot cohere (an incompatible replicon, the CG258 analog).
An explicit `compatible=(host, provirus)->bool` hook adds a domain lineage barrier (checked in
addition; both must pass). A COMPATIBLE provirus integrates EXACTLY as rc262 (the gate adds
ONLY a refuse path). Class-K/C equality read, never abs(). numpy-free.
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome as G
from srmech.math.hdc import klein4_expand


def _one(dim=64, seed=7):
    return klein4_expand(dim, seed)


def _lv(n, base=0, dim=64):
    return [klein4_expand(dim, base + s) for s in range(n)]


def _host(one):
    # a Tier-2 eukaryote: a MINTED (nuclear) chromosome + a DIPLOID chromosome, ONE coupling
    return G.mint({"astronomy": _lv(12, 100)}, one) + G.diploid(_lv(6, 200), one, label="chr7")


def _provirus(one):
    # a Tier-1 plasmid (a retrovirus genome), SAME coupling
    return G.plasmid({"provirus": _lv(3, 300)}, one)


# ── the COMPATIBLE path is byte-for-byte rc262 (full back-compat) ────────────

def test_compatible_integration_is_exactly_rc262():
    one = _one()
    host, provirus = _host(one), _provirus(one)
    integrated = G.integrate(host, provirus)
    assert integrated is not None                             # a compatible provirus integrates
    assert len(integrated) == len(host) + len(provirus)       # grows by the provirus
    parts = G.partition(integrated, one)
    assert set(parts) == {"astronomy", "chr7", "provirus"}    # every chromosome recovers
    assert [x.tobytes() for x in parts["provirus"]] == [x.tobytes() for x in _lv(3, 300)]


def test_compatible_at_locus_unchanged():
    one = _one()
    host, provirus = _host(one), _provirus(one)
    front = G.integrate(host, provirus, at=0)
    assert front is not None and list(G.partition(front, one))[0] == "provirus"
    end = G.integrate(host, provirus, at=None)
    assert end is not None and list(G.partition(end, one))[-1] == "provirus"


# ── the INCOMPATIBLE path: honest-decline (return None), host UNCHANGED ──────

def test_incompatible_width_is_honest_declined():
    """A provirus coupled at a DIFFERENT width (an incompatible replicon — the CG258
    segregated case) fails the coherence predicate → integrate refuses with None."""
    one64 = _one(64)
    host = _host(one64)
    one32 = _one(32, seed=7)
    provirus32 = G.plasmid({"provirus": _lv(3, 300, dim=32)}, one32)   # different replicon width
    host_before = [x.tobytes() for x in host]
    refused = G.integrate(host, provirus32)
    assert refused is None                                    # honest-decline (not a crash)
    # the host is UNCHANGED (integrate never mutates its input on a refuse)
    assert [x.tobytes() for x in host] == host_before


def test_compatible_hook_barrier_is_honest_declined():
    """A same-width host + provirus that a caller-supplied lineage predicate rejects (the
    CG258 same-replicon-different-lineage barrier) is honest-declined; host unchanged."""
    one = _one()
    host, provirus = _host(one), _provirus(one)
    host_before = [x.tobytes() for x in host]
    refused = G.integrate(host, provirus, compatible=lambda h, p: False)
    assert refused is None
    assert [x.tobytes() for x in host] == host_before


def test_compatible_hook_true_integrates():
    one = _one()
    host, provirus = _host(one), _provirus(one)
    ok = G.integrate(host, provirus, compatible=lambda h, p: True)
    assert ok is not None and len(ok) == len(host) + len(provirus)


def test_compatible_hook_receives_host_and_provirus():
    one = _one()
    host, provirus = _host(one), _provirus(one)
    seen = {}

    def hook(h, p):
        seen["h"], seen["p"] = len(h), len(p)
        return True

    ok = G.integrate(host, provirus, compatible=hook)
    assert ok is not None
    assert seen["h"] == len(host) and seen["p"] == len(provirus)


# ── edge cases preserved ─────────────────────────────────────────────────────

def test_empty_host_integrates_any_provirus():
    one = _one()
    provirus = _provirus(one)
    got = G.integrate([], provirus)                           # nothing to be incompatible with
    assert got is not None and [x.tobytes() for x in got] == [x.tobytes() for x in provirus]


def test_still_rejects_a_non_chromosome_provirus():
    one = _one()
    with pytest.raises(ValueError):
        G.integrate(_host(one), [klein4_expand(64, 1)])  # a bare turn, no boundary cap


def test_still_rejects_at_out_of_range():
    one = _one()
    with pytest.raises(ValueError):
        G.integrate(_host(one), _provirus(one), at=99)


# ── the coherence proof still holds on a compatible integration ──────────────

def test_minted_centromere_and_diploid_survive_compatible_integration():
    one = _one()
    integrated = G.integrate(_host(one), _provirus(one))
    assert integrated is not None
    start = next(i for i, hv in enumerate(integrated)
                 if G._cap_kind(hv) == G.CHROM_CAP_MARKER)
    info = G.centromere_of(integrated[start:])
    assert info is not None and info["orientation"] in (0, 1, 2, 3)
    dstart = next(i for i, hv in enumerate(integrated)
                  if G._cap_kind(hv) == G.DIPLOID_TELOMERE_MARKER)
    dend = next((i for i in range(dstart + 1, len(integrated))
                 if G._cap_kind(integrated[i]) in G._CHROM_BOUNDARY_MARKERS), len(integrated))
    rec = G.recover_diploid(integrated[dstart:dend], one)
    assert [x.tobytes() for x in rec] == [x.tobytes() for x in _lv(6, 200)]
