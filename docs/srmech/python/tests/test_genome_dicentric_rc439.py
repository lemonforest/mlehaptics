"""v0.9.0rc439 (`#T1140`) — the DICENTRIC strand: the state class no fixture had ever minted.

`centromere_of` answers about ONE chromosome — its global 4-way orientation and its p:q
arm-split — while SCANNING A WHOLE STRAND. Nothing bounded the scan to one chromosome, and
nothing checked that the scan found only one ``0x58`` cap, so on a strand carrying two the
three code paths each answered differently and none of them raised:

    MEASURED at rc438, strand = [chrA telomere, t, t, t, cen(o=2,'cen',R=15), t,
                                 cen(o=1,'cen2',R=9), t, t]

      C peer  srmech_genome_centromere_of  -> keeps the LAST cap:  orientation 1
      Python  native branch                -> orientation/p/q from C (LAST) but
                                              handle/repeats re-scanned to the FIRST:
                                              {'orientation': 1, 'handle': 'cen', 'repeats': 15}
                                              — ONE record assembled from TWO different caps
      Python  pure walk                    -> all fields from the LAST cap:
                                              {'orientation': 1, 'handle': 'cen2', 'repeats': 9}

So the answer depended on whether a ``.so`` happened to be loaded, and the native answer was
not even internally coherent. **It had never fired because no fixture in the tree minted two
centromeres.** That absence is the finding this file closes: the instrument was missing, not
the defect.

The state is NOT exotic. ``mint()`` over two nuclear kernels writes it (one centromere per
nuclear chromosome), and there rc438 reported ``arm_ratio (9, 4)`` — a turn count taken ACROSS
a chromosome boundary that describes neither chromosome.

THE CONTRACT (rc439): both projections REFUSE. A dicentric chromosome is real in biology and
UNSTABLE — the two centromeres attach to opposite spindle poles and the chromosome breaks (the
breakage-fusion-bridge cycle) — so "there is no single orientation / arm-split" is the honest
answer, not a limitation. ``mint_strand`` has ALWAYS refused to splice a second centromere into
a strand that has one; rc439 gives the READER the contract the WRITER already had. Python
raises ``ValueError``; the C peer returns ``SRMECH_ERR_BAD_INPUT`` with ``*found_out = 0``
(ABI 15 -> 16, a status reinterpretation — the v10 / v12 / v14 shape).

Also pinned here, because both were measured in the same pass:

  * ``condense()`` does NOT re-target the centromere (§98's "modify WITHOUT changing the DNA"
    claim holds). Every field of ``centromere_of`` is invariant across condense/decondense; the
    only thing that moves is the raw BLOCK ORDINAL, which is not a designation any shipped read
    returns. Recorded explicitly so the v19 contract is written down rather than assumed.
  * The sibling scan ``chromatin_of`` takes the FIRST cap in ALL THREE paths (its C peer
    early-returns), so it carries no first-vs-last divergence. That bounds the population of
    this defect at exactly one op.

numpy-free; no ``fractions`` / ``math`` / ``decimal``; no ``abs()``.
"""
from __future__ import annotations

import ctypes

import pytest

from srmech.biology import genome as G
from srmech import _native
from srmech.math.hdc import klein4_expand

_DIM = 64
_SRMECH_ERR_BAD_INPUT = 2               # srmech.h status enum


def _one(seed=7):
    return klein4_expand(_DIM, seed)


def _leaves(n, base=0):
    return [klein4_expand(_DIM, base + s) for s in range(n)]


def _dicentric(one):
    """THE MISSING INSTRUMENT — a strand carrying TWO 0x58 caps, deliberately DIFFERENT in
    every field a read can return (orientation, handle, repeats) so a blend is detectable."""
    chrom = G.chromosome(_leaves(6, 100), one, label="chrA", centromere=2)
    second = G.centromere(1, repeats=9, handle="cen2", dim=_DIM)
    di = chrom[:6] + [second] + chrom[6:]
    assert _n_cen(di) == 2                      # the fixture really does carry two
    return di


def _n_cen(strand):
    return sum(1 for hv in strand if G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER)


def _force_pure(monkeypatch):
    """Drive the numpy-free pure walk regardless of whether a .so is loaded."""
    monkeypatch.setattr(_native, "genome_centromere_of_c", lambda *a, **k: None)


# ── 1. the fixture is real, and the two caps really do differ ───────────────

def test_the_fixture_mints_two_distinguishable_centromeres():
    di = _dicentric(_one())
    caps = [hv for hv in di if G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER]
    assert len(caps) == 2
    assert caps[0].tobytes() != caps[1].tobytes()
    # every field a read can return differs between them, so ANY blend is visible
    assert G._unpack_cap(caps[0])[1] == "cen" and G._unpack_cap(caps[1])[1] == "cen2"
    assert len(G._centromere_votes(caps[0])) == 15
    assert len(G._centromere_votes(caps[1])) == 9
    assert G._centromere_orientation(G._centromere_votes(caps[0])) == 2
    assert G._centromere_orientation(G._centromere_votes(caps[1])) == 1


# ── 2. BOTH Python projections refuse — proven by execution, not by reading ──

def test_native_path_refuses_a_dicentric_strand():
    di = _dicentric(_one())
    with pytest.raises(ValueError, match="2 centromere caps"):
        G.centromere_of(di)


def test_pure_path_refuses_a_dicentric_strand(monkeypatch):
    di = _dicentric(_one())
    _force_pure(monkeypatch)
    with pytest.raises(ValueError, match="2 centromere caps"):
        G.centromere_of(di)


def test_both_projections_refuse_with_the_same_message(monkeypatch):
    """The AGREEMENT is the point: same input, same refusal, either projection."""
    di = _dicentric(_one())
    with pytest.raises(ValueError) as native:
        G.centromere_of(di)
    _force_pure(monkeypatch)
    with pytest.raises(ValueError) as pure:
        G.centromere_of(di)
    assert str(native.value) == str(pure.value)


# ── 3. the C peer refuses too (a bare-C host gets the same contract) ────────

@pytest.mark.skipif(not _native.has_native_genome_centromere_of(),
                    reason="no native srmech_genome_centromere_of")
def test_c_peer_refuses_a_dicentric_strand():
    di = _dicentric(_one())
    buf = b"".join(hv.tobytes() for hv in di)
    o_out = ctypes.c_uint8(255)
    p_out = ctypes.c_size_t(0)
    q_out = ctypes.c_size_t(0)
    found = ctypes.c_int(-1)
    rc = _native.LIB.srmech_genome_centromere_of(
        _native._u8(buf), ctypes.c_size_t(len(di)), ctypes.c_uint32(_DIM),
        ctypes.byref(o_out), ctypes.byref(p_out), ctypes.byref(q_out),
        ctypes.byref(found))
    assert rc == _SRMECH_ERR_BAD_INPUT       # NOT SRMECH_OK-with-a-blend
    assert found.value == 0                  # and it does not claim to have found one


@pytest.mark.skipif(not _native.has_native_genome_centromere_of(),
                    reason="no native srmech_genome_centromere_of")
def test_the_ctypes_shim_reports_the_refusal_as_none():
    """The shim maps a non-OK status to None — which is ALSO its "no fast path" signal. That
    collision is exactly why centromere_of gates in Python BEFORE dispatching: leaning on this
    return value would fall through to the pure walk, which would answer."""
    di = _dicentric(_one())
    buf = b"".join(hv.tobytes() for hv in di)
    assert _native.genome_centromere_of_c(buf, len(di), _DIM) is None


# ── 4. the reachable case: a multi-chromosome genome strand ─────────────────

def test_mint_over_two_nuclear_kernels_is_a_two_centromere_strand():
    """Not a hand-built curiosity: a SHIPPED op writes this strand."""
    strand = G.mint({"chrA": _leaves(6, 100), "chrB": _leaves(7, 200)}, _one())
    assert _n_cen(strand) == 2
    with pytest.raises(ValueError, match="2 centromere caps"):
        G.centromere_of(strand)


def test_scoping_to_one_chromosome_is_the_route_back_to_an_answer():
    """The refusal is not a dead end — slice at the boundary cap and the read works."""
    one = _one()
    strand = G.mint({"chrA": _leaves(6, 100), "chrB": _leaves(7, 200)}, one)
    bounds = [i for i, hv in enumerate(strand)
              if G._cap_kind(hv) in G._CHROM_BOUNDARY_MARKERS]
    assert len(bounds) == 2
    first = strand[bounds[0]:bounds[1]]
    second = strand[bounds[1]:]
    assert _n_cen(first) == 1 and _n_cen(second) == 1
    a, b = G.centromere_of(first), G.centromere_of(second)
    assert a is not None and b is not None
    # each scoped read describes ITS OWN chromosome: p + q == that chromosome's data turns
    for part, info in ((first, a), (second, b)):
        turns = sum(1 for hv in part if G._cap_kind(hv) is None)
        assert info["arm_ratio"][0] + info["arm_ratio"][1] == turns


# ── 5. the SINGLE-centromere read is untouched, and the projections agree ───

def test_single_centromere_read_is_unchanged_and_projections_agree(monkeypatch):
    one = _one()
    chrom = G.chromosome(_leaves(6, 100), one, label="chrA", centromere=2)
    native = G.centromere_of(chrom)
    assert native == {"orientation": 2, "arm_ratio": (3, 3),
                      "handle": "cen", "repeats": 15}
    _force_pure(monkeypatch)
    assert G.centromere_of(chrom) == native          # native == pure, field for field


def test_a_strand_with_no_centromere_is_still_none_in_both_projections(monkeypatch):
    one = _one()
    pl = G.chromosome(_leaves(3, 500), one, label="pl")
    assert _n_cen(pl) == 0
    assert G.centromere_of(pl) is None
    _force_pure(monkeypatch)
    assert G.centromere_of(pl) is None


def test_empty_strand_is_none():
    assert G.centromere_of([]) is None


# ── 6. DEFECT-1 RECORD: condense does NOT re-target the centromere ──────────

def test_condense_leaves_every_centromere_field_invariant():
    """§98 claims condense() modifies accessibility WITHOUT changing the DNA. MEASURED: true.
    The centromere cap is byte-identical and every field of centromere_of is unchanged."""
    one = _one()
    chrom = G.chromosome(_leaves(6, 100), one, label="chrA", centromere=2)
    before = G.centromere_of(chrom)
    cond = G.condense(chrom, coupling=one, state=True, label="chrA")
    assert G.centromere_of(cond) == before
    cap_before = [h.tobytes() for h in chrom if G._cap_kind(h) == G.CENTROMERE_CAP_MARKER]
    cap_after = [h.tobytes() for h in cond if G._cap_kind(h) == G.CENTROMERE_CAP_MARKER]
    assert cap_before == cap_after
    back = G.decondense(cond, coupling=one, label="chrA")
    assert [h.tobytes() for h in back] == [h.tobytes() for h in chrom]
    assert G.centromere_of(back) == before


def test_the_block_ordinal_moves_and_that_is_not_a_designation():
    """The v19 contract, written down. A splice DOES shift the centromere's raw block index —
    it must, a block was inserted before it — but no shipped read designates the centromere by
    that ordinal. Designation is by CONTENT (data-turn counts and labels), and data-turn counts
    do not move when a CAP is spliced in, because a cap is not a data turn."""
    one = _one()
    chrom = G.chromosome(_leaves(6, 100), one, label="chrA", centromere=2)
    idx = [i for i, h in enumerate(chrom) if G._cap_kind(h) == G.CENTROMERE_CAP_MARKER]
    cond = G.condense(chrom, coupling=one, state=True, label="chrA")
    idx_after = [i for i, h in enumerate(cond) if G._cap_kind(h) == G.CENTROMERE_CAP_MARKER]
    assert idx == [4] and idx_after == [5]           # the ordinal DID move
    assert G.centromere_of(cond)["arm_ratio"] == G.centromere_of(chrom)["arm_ratio"]
    assert len(cond) == len(chrom) + 1               # exactly one cap spliced


# ── 7. the population bound: the sibling scan has no such divergence ────────

def test_chromatin_of_takes_the_first_cap_in_both_projections(monkeypatch):
    """chromatin_of is the same shape of op (scan the strand for an interior cap) and its C
    peer EARLY-RETURNS on the first match, so native and pure agree by construction. This is
    what bounds the first-vs-last population at exactly one op — centromere_of."""
    one = _one()
    chrom = G.chromosome(_leaves(6, 100), one, label="chrA", centromere=2)
    first = G.condense(chrom, coupling=one, state=True, handle="outer", label="chrA")
    both = G.condense(first, coupling=one, state=(1, 2), region=2,
                      handle="inner", label="chrA")
    caps = [hv for hv in both if G._cap_kind(hv) == G.CHROMATIN_MARKER]
    assert len(caps) == 2
    native = G.chromatin_of(both)
    monkeypatch.setattr(_native, "genome_chromatin_of_c", lambda *a, **k: None)
    pure = G.chromatin_of(both)
    assert native == pure                            # no first-vs-last divergence
    assert native["handle"] == "outer"               # and it is the FIRST cap
