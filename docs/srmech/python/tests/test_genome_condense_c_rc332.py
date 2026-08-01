"""§102 G7 (rc332, task #887) — BYTE-PARITY between the two coherency projections of the
chromatin CONDENSE / DECONDENSE pair, the wire-glue ops that earned whole-op C peers this rc:

  * ``genome.condense`` -> ``srmech_genome_condense`` — the placement decision. The cap BYTES
    were already native (``srmech_genome_chromatin``); the Python-only part was the
    ``_chrom_range(label)`` lookup + the ``region`` resolution + the splice around them. rc332
    lifts the range-find + region resolution into C: the peer returns the BLOCK INDEX at which
    the cap is spliced (``region=None`` -> HEAD scope; ``region=int`` -> the k-th data turn;
    ``region="<gene>"`` -> before that gene's cap).
  * ``genome.decondense`` -> ``srmech_genome_decondense`` — the inverse. Writes a per-block
    KEEP-MASK: drop every ``0x48`` chromatin cap whole-strand, or only those inside the ``label``
    chromosome's block range (the SAME range-find as condense).

ADR-0009: the capability is the invariant; neither implementation is primary. So the test is NOT
"does C agree with Python" — it is "do the two projections emit the SAME result". The native
whole-op peer runs the WHOLE placement / clear decision in C; the pure body (forced here by
disabling the native surface) is the byte-parity ORACLE (and raises the exact ValueErrors the C
peer declines on). The list splice / filter is the trivial assembly (the rc329 mint_plan pattern:
the COMPUTATION runs in C, the assembly is formatting).

Both closures move ``_KNOWN_GLUE_GAPS -> _WHOLE_OP_C_PEER`` and drop ``CEIL_WIRE_GLUE_GAPS``
6 -> 4 in test_rosetta_transitive_standalone.py; this file pins the byte-parity AND that each peer
is both DECLARED in the whole-op map and actually DISPATCHED (not merely present in the lib).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from srmech.biology import genome as G
from srmech.amsc import _native as _N
from srmech.math.hdc import klein4_expand


def _one(seed=7):
    return klein4_expand(64, seed)


def _lv(n, base=0):
    return [klein4_expand(64, base + s) for s in range(n)]


def _bytes(strand):
    return [h.tobytes() for h in strand]


def _gene_chrom(one, label="c"):
    return G.chromosome(coupling=one, label=label,
                        genes=[("g1", _lv(2, 10)), ("g2", _lv(2, 20))])


def _load_rosetta():
    path = Path(__file__).with_name("test_rosetta_transitive_standalone.py")
    spec = importlib.util.spec_from_file_location("_rosetta_rc332", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_condense_native = pytest.mark.skipif(
    not _N.has_native_genome_condense(),
    reason="rc332 native srmech_genome_condense not built into this lib",
)
_decondense_native = pytest.mark.skipif(
    not _N.has_native_genome_decondense(),
    reason="rc332 native srmech_genome_decondense not built into this lib",
)


# ── condense — srmech_genome_condense ────────────────────────────────────────

@_condense_native
@pytest.mark.parametrize("state,region,label", [
    (True, None, None),                    # binary condensed, HEAD scope, single chrom
    (False, None, None),                   # binary open
    ((1, 3), None, None),                  # graded 1/3
    (True, 0, None),                       # region 0 -> the first data turn
    (True, 3, None),                       # an interior data-turn index
    (True, 12, None),                      # region == data-turn count -> append at end
    ({"activator": 0b1, "repressor": 0b0}, None, None),   # FACULTATIVE gate (dict state)
])
def test_condense_byte_parity_single_chrom(monkeypatch, state, region, label):
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    nat = G.condense(chrom, coupling=one, state=state, region=region, label=label)
    assert _N.has_native_genome_condense()
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        assert not _N.has_native_genome_condense()
        pur = G.condense(chrom, coupling=one, state=state, region=region, label=label)
    assert _bytes(nat) == _bytes(pur), (
        f"condense(state={state!r}, region={region!r}): strand bytes diverge")
    # exactly one cap spliced in, input untouched (the modify-without-re-mint property)
    assert len(nat) == len(chrom) + 1


@_condense_native
def test_condense_byte_parity_gene_label_region(monkeypatch):
    one = _one()
    chrom = _gene_chrom(one)
    nat = G.condense(chrom, coupling=one, region="g2", state=True)
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        pur = G.condense(chrom, coupling=one, region="g2", state=True)
    assert _bytes(nat) == _bytes(pur)


@_condense_native
def test_condense_byte_parity_multi_chromosome(monkeypatch):
    one = _one()
    genome = G.mint({"a": _lv(6, 1), "b": _lv(7, 40)}, one)
    for lbl in ("a", "b"):
        nat = G.condense(genome, coupling=one, state=True, label=lbl, region=2)
        with monkeypatch.context() as m:
            m.setattr(_N, "HAS_NATIVE", False)
            pur = G.condense(genome, coupling=one, state=True, label=lbl, region=2)
        assert _bytes(nat) == _bytes(pur), f"condense(label={lbl!r}) diverges"


@_condense_native
def test_condense_byte_parity_multi_region_stack(monkeypatch):
    """Condensing an ALREADY-condensed strand (a second interior cap): the range-find must
    still land the right insert index with a 0x48 already present."""
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    once = G.condense(chrom, coupling=one, state=True, region=None)     # HEAD cap present
    nat = G.condense(once, coupling=one, state=(1, 2), region=6)
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        pur = G.condense(once, coupling=one, state=(1, 2), region=6)
    assert _bytes(nat) == _bytes(pur)


@_condense_native
@pytest.mark.parametrize("kwargs", [
    {"state": True, "label": "a", "region": 99},              # region past the data-turn count
    {"state": True, "label": "a", "region": "no_such_gene"},  # a gene label with no match
    {"state": True, "label": "missing"},                      # no chromosome by that label
])
def test_condense_error_parity(monkeypatch, kwargs):
    """The C peer DECLINES exactly where the pure body RAISES — the caller falls back to the
    pure path, which raises the same ValueError, native or not."""
    one = _one()
    genome = G.mint({"a": _lv(6, 1), "b": _lv(7, 40)}, one)
    with pytest.raises(ValueError):
        G.condense(genome, coupling=one, **kwargs)
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        with pytest.raises(ValueError):
            G.condense(genome, coupling=one, **kwargs)


@_condense_native
def test_condense_ambiguous_label_none_error_parity(monkeypatch):
    """A multi-chromosome strand with no label= is ambiguous — the C range-find declines and the
    pure body raises, both native and forced-pure."""
    one = _one()
    genome = G.mint({"a": _lv(5, 1), "b": _lv(6, 40)}, one)
    with pytest.raises(ValueError):
        G.condense(genome, coupling=one, state=True)               # no label -> ambiguous
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        with pytest.raises(ValueError):
            G.condense(genome, coupling=one, state=True)


# ── decondense — srmech_genome_decondense ────────────────────────────────────

@_decondense_native
def test_decondense_whole_strand_byte_parity(monkeypatch):
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    cond = G.condense(chrom, coupling=one, state=(1, 4), region=2)
    nat = G.decondense(cond, coupling=one)
    assert _N.has_native_genome_decondense()
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        assert not _N.has_native_genome_decondense()
        pur = G.decondense(cond, coupling=one)
    assert _bytes(nat) == _bytes(pur)
    # and it is the exact inverse of condense (byte-identical to the un-condensed original)
    assert _bytes(nat) == _bytes(chrom)


@_decondense_native
def test_decondense_multi_cap_whole_strand(monkeypatch):
    """Two chromatin caps on one chromosome — whole-strand decondense drops BOTH."""
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    two = G.condense(G.condense(chrom, coupling=one, state=True, region=None),
                     coupling=one, state=(1, 2), region=6)
    nat = G.decondense(two, coupling=one)
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        pur = G.decondense(two, coupling=one)
    assert _bytes(nat) == _bytes(pur)
    assert _bytes(nat) == _bytes(chrom)                            # both caps cleared


@_decondense_native
def test_decondense_label_scoped_byte_parity(monkeypatch):
    """Label-scoped decondense drops ONLY the target chromosome's chromatin, leaving the
    OTHER chromosome's cap untouched (the same range-find as condense)."""
    one = _one()
    genome = G.mint({"a": _lv(6, 1), "b": _lv(7, 40)}, one)
    ca = G.condense(genome, coupling=one, state=True, label="a")
    both = G.condense(ca, coupling=one, state=True, label="b")
    nat = G.decondense(both, coupling=one, label="a")
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        pur = G.decondense(both, coupling=one, label="a")
    assert _bytes(nat) == _bytes(pur)
    # a's cap is gone but b's survives (the label scope held): 2 caps -> 1
    assert sum(1 for h in both if G._cap_kind(h) == G.CHROMATIN_MARKER) == 2
    assert sum(1 for h in nat if G._cap_kind(h) == G.CHROMATIN_MARKER) == 1


@_decondense_native
def test_decondense_empty_strand(monkeypatch):
    nat = G.decondense([], coupling=_one())
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        pur = G.decondense([], coupling=_one())
    assert nat == pur == []


@_decondense_native
def test_decondense_label_error_parity(monkeypatch):
    one = _one()
    genome = G.mint({"a": _lv(6, 1), "b": _lv(7, 40)}, one)
    cond = G.condense(genome, coupling=one, state=True, label="a")
    with pytest.raises(ValueError):
        G.decondense(cond, coupling=one, label="missing")
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        with pytest.raises(ValueError):
            G.decondense(cond, coupling=one, label="missing")


# ── round-trip + direct-dispatch coherence ───────────────────────────────────

@_condense_native
@_decondense_native
def test_condense_decondense_round_trips_native(monkeypatch):
    """condense then decondense == byte-identical original, on the fully-native path."""
    one = _one()
    chrom = _gene_chrom(one)
    snap = _bytes(chrom)
    cond = G.condense(chrom, coupling=one, state=True, region="g2")
    assert _bytes(cond) != snap                                    # a cap was really spliced in
    back = G.decondense(cond, coupling=one)
    assert _bytes(back) == snap


@_condense_native
def test_condense_c_returns_the_index_directly():
    """The C peer really produces an insert index (not a silent None -> pure)."""
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    sb = b"".join(h.tobytes() for h in chrom)
    idx = _N.genome_condense_c(sb, len(chrom), 64, None, None)
    assert idx == 1                                               # HEAD scope: after the telomere
    idx3 = _N.genome_condense_c(sb, len(chrom), 64, None, 3)
    assert isinstance(idx3, int) and idx3 > 1
    # a bogus label declines (None -> pure raises)
    assert _N.genome_condense_c(sb, len(chrom), 64, "missing", None) is None


@_decondense_native
def test_decondense_c_returns_the_keep_mask_directly():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    cond = G.condense(chrom, coupling=one, state=True)
    sb = b"".join(h.tobytes() for h in cond)
    keep = _N.genome_decondense_c(sb, len(cond), 64, None)
    assert isinstance(keep, list) and len(keep) == len(cond)
    assert keep.count(False) == 1                                # exactly the one 0x48 cap dropped


def test_rc332_peers_declared_and_gap_closed():
    """The two ops left ``_KNOWN_GLUE_GAPS`` for ``_WHOLE_OP_C_PEER`` — assert the map names the
    right symbol and neither is still a gap. (The full transitive ratchet + the DOWN-ONLY global
    ceiling pin live in test_rosetta_transitive_standalone.py; this is a local coherence pin for
    THESE ops only — it does NOT re-pin the global ceiling to its rc332-era value.)"""
    rosetta = _load_rosetta()
    assert rosetta._WHOLE_OP_C_PEER["srmech.biology.genome.condense"] == "srmech_genome_condense"
    assert rosetta._WHOLE_OP_C_PEER["srmech.biology.genome.decondense"] == "srmech_genome_decondense"
    assert "srmech.biology.genome.condense" not in rosetta._KNOWN_GLUE_GAPS
    assert "srmech.biology.genome.decondense" not in rosetta._KNOWN_GLUE_GAPS
    assert len(rosetta._KNOWN_GLUE_GAPS) == rosetta.CEIL_WIRE_GLUE_GAPS
