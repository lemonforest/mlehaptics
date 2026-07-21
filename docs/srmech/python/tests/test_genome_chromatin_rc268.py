"""v0.9.0rc268 (§98 / #1422 / F1246-F1247) — the CHROMATIN ACCESS LAYER.

Biology's epigenetic PACKAGING gate ABOVE the coupled-turn content: a per-region
euchromatin(accessible) / heterochromatin(silenced) marker (0x48 'H') that gates WHICH
regions express — the modify-WITHOUT-changing-the-DNA layer. ONE interior cap-marker
spanning BOTH granularities (head → whole-chromosome / interior → a stretch) and BOTH
states (binary open/condensed OR a graded exact-rational accessibility level).

Proven here: the marker is set/cleared IN-PLACE with NO re-mint (the centromere + body
stay byte-identical); both granularities + both states round-trip; marks survive
genome_save + integrate; the outer-gate composition expressed = accessible AND promoter
(graded chromatin × graded gene = the exact-rational product); the STRAND demand-load plan
skips condensed regions; native == pure for every new C op; and a pre-chromatin (v≤14)
genome reads identically (format v14 → v15 additive / back-compatible). numpy-free.

(rc269 follow-up, EXPLICITLY DEFERRED: the PATH demand-load single-seek chromatin skip in
srmech_genome_gene_express_plan — the C peer — is NOT wired here; the STRAND plan variant IS.)
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native as _N
from srmech.amsc.hdc import klein4_expand


def _one(seed=7):
    return klein4_expand(64, seed)


def _lv(n, base=0):
    return [klein4_expand(64, base + s) for s in range(n)]


def _reload_strand(path, leaf_dim):
    """Read turns.bin back into a full HV strand (every block — caps + turns)."""
    body = (path / "turns.bin").read_bytes()
    return G._region_strand(body, leaf_dim)


# ── format version + marker economy ──────────────────────────────────────────

def test_format_version_bumped_to_15():
    assert G.GENOME_FORMAT_VERSION == 15


def test_chromatin_marker_is_unused_0x48():
    assert G.CHROMATIN_MARKER == 0x48
    # distinct from every prior structural marker (the 12 that existed pre-rc268)
    prior = {G.CHROM_CAP_MARKER, G.GENE_CAP_MARKER, G.PACKED_TURN_MARKER,
             G.KERNEL_HEADER_MARKER, G.KERNEL_TELOMERE_MARKER, G.ACTIVE_TELOMERE_MARKER,
             G.REGULATORY_GENE_MARKER, G.BOOLEAN_GENE_MARKER, G.THRESHOLD_GENE_MARKER,
             G.GRADED_GENE_MARKER, G.CENTROMERE_CAP_MARKER, G.DIPLOID_TELOMERE_MARKER}
    assert G.CHROMATIN_MARKER not in prior
    assert len(prior) == 12


# ── the primitive: both states, both granularities ───────────────────────────

def test_binary_condensed_head_scope():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    cond = G.condense(chrom, coupling=one, state=True)
    info = G.chromatin_of(cond, one)
    assert info["type"] == "binary" and info["state"] == "condensed"
    assert info["level"] == (0, 1)
    assert info["scope"] == "chromosome" and info["at"] == 0


def test_binary_open_marker():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    op = G.condense(chrom, coupling=one, state=False)
    info = G.chromatin_of(op, one)
    assert info["type"] == "binary" and info["state"] == "open"
    assert info["level"] == (1, 1)


def test_graded_level_reduced_exact():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    grad = G.condense(chrom, coupling=one, state=(2, 6))     # reduces to 1/3
    info = G.chromatin_of(grad, one)
    assert info["type"] == "graded" and info["level"] == (1, 3)


def test_interior_stretch_scope():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    strt = G.condense(chrom, coupling=one, region=3, state=True)
    info = G.chromatin_of(strt, one)
    assert info["scope"] == "stretch" and info["at"] == 3


def test_chromatin_free_is_none():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    assert G.chromatin_of(chrom, one) is None


def test_level_out_of_range_rejected():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    with pytest.raises(ValueError):
        G.condense(chrom, coupling=one, state=(3, 2))        # num > den -> not in [0,1]
    with pytest.raises(ValueError):
        G.condense(chrom, coupling=one, state=(1, 0))        # den 0


# ── modify-minted-WITHOUT-re-mint (the load-bearing property) ────────────────

def test_condense_preserves_the_centromere_byte_identical():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    cen_before = [h.tobytes() for h in chrom if G._cap_kind(h) == G.CENTROMERE_CAP_MARKER]
    info0 = G.centromere_of(chrom)
    cond = G.condense(chrom, coupling=one, state=True)
    cen_after = [h.tobytes() for h in cond if G._cap_kind(h) == G.CENTROMERE_CAP_MARKER]
    assert cen_before == cen_after                          # NO re-mint of the centromere
    assert G.centromere_of(cond) == info0                   # orientation + arm-ratio unchanged
    assert len(cond) == len(chrom) + 1                      # exactly one marker spliced in


def test_decondense_is_the_exact_inverse():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    cond = G.condense(chrom, coupling=one, state=(1, 4), region=2)
    back = G.decondense(cond, coupling=one)
    assert [h.tobytes() for h in back] == [h.tobytes() for h in chrom]   # byte-identical original
    assert G.chromatin_of(back, one) is None


def test_condense_does_not_mutate_the_input():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    snapshot = [h.tobytes() for h in chrom]
    G.condense(chrom, coupling=one, state=True)
    assert [h.tobytes() for h in chrom] == snapshot         # input strand unchanged


# ── the OUTER gate: expressed = accessible AND promoter ──────────────────────

def _gene_chrom(one):
    return G.chromosome(genes=[("g1", _lv(2, 10)), ("g2", _lv(2, 20))], coupling=one)


def test_heterochromatin_silences_even_when_promoter_fires():
    one = _one()
    chrom = _gene_chrom(one)
    assert {l for l, _ in G.gene_express(chrom, one, 0)} == {"g1", "g2"}   # promoters fire
    cond = G.condense(chrom, coupling=one, state=True)                     # whole-chrom condensed
    assert G.gene_express(cond, one, 0) == []                             # accessible=0 gates all


def test_euchromatin_defers_to_the_promoter():
    one = _one()
    chrom = _gene_chrom(one)
    op = G.condense(chrom, coupling=one, state=False)                      # explicit euchromatin
    assert {l for l, _ in G.gene_express(op, one, 0)} == {"g1", "g2"}     # falls through to promoter


def test_interior_stretch_silences_only_the_stretch():
    one = _one()
    chrom = _gene_chrom(one)
    strt = G.condense(chrom, coupling=one, region="g2", state=True)        # stretch from g2 on
    assert {l for l, _ in G.gene_express(strt, one, 0)} == {"g1"}         # g1 accessible, g2 silenced


def test_graded_chromatin_times_graded_gene_is_exact_rational_product():
    one = _one()
    # a graded gene: level_weight [1] over condition bit 0, denom 2 -> level 1/2 when bit0 present
    strand = G.chromosome(coupling=one, label="c",
                          genes=[("gd", _lv(2, 30), {"gate": "graded", "weights": [1], "denom": 2})])
    base = G.gene_express_levels(strand, one, 0b1)
    assert base and base[0][2] == (1, 2)                                  # promoter level 1/2
    # chromatin graded 1/3 over it: accessibility 1/3 × promoter 1/2 = 1/6
    gcond = G.condense(strand, coupling=one, state=(1, 3))
    lv = G.gene_express_levels(gcond, one, 0b1)
    assert lv and lv[0][2] == (1, 6)                                      # exact rational product


def test_condensed_graded_zero_is_silenced_in_levels():
    one = _one()
    chrom = _gene_chrom(one)
    cond = G.condense(chrom, coupling=one, state=True)                     # level 0
    assert G.gene_express_levels(cond, one, 0) == []                      # 0 × anything = silenced


# ── the STRAND demand-load plan skips condensed genes ────────────────────────

def test_strand_plan_skips_condensed_genes():
    one = _one()
    chrom = _gene_chrom(one)
    base = {p[0] for p in G.gene_express_plan(chrom, one, 0)}
    assert base == {"g1", "g2"}
    strt = G.condense(chrom, coupling=one, region="g2", state=True)
    assert {p[0] for p in G.gene_express_plan(strt, one, 0)} == {"g1"}    # g2's gate not planned
    cond = G.condense(chrom, coupling=one, state=True)
    assert G.gene_express_plan(cond, one, 0) == []                        # whole chrom skipped


def test_strand_plan_matches_gene_express_set():
    one = _one()
    chrom = _gene_chrom(one)
    strt = G.condense(chrom, coupling=one, region="g2", state=True)
    plan_set = {p[0] for p in G.gene_express_plan(strt, one, 0)}
    express_set = {l for l, _ in G.gene_express(strt, one, 0)}
    assert plan_set == express_set                                       # plan == express (chromatin)


# ── round-trip survival: genome_save + integrate preserve the marks ──────────

def test_marks_survive_genome_save_and_reload(tmp_path):
    one = _one()
    chrom = G.condense(G.mint({"astro": _lv(12, 100)}, one), coupling=one, state=(1, 3))
    G.genome_save(chrom, tmp_path, one)
    leaf_dim = len(list(one))
    reloaded = _reload_strand(tmp_path, leaf_dim)
    assert G.chromatin_of(reloaded, one) == G.chromatin_of(chrom, one)
    # census is unaffected — a chromatin cap is orthogonal to plasmid/nuclear/diploid
    cen = G.genome_census(tmp_path, coupling=one)
    assert cen["types"] == {"plasmid": 0, "nuclear": 1, "diploid": 0}
    assert cen["total_leaves"] == 12                                     # leaf-count unbroken


def test_marks_survive_integrate():
    one = _one()
    host = G.mint({"astro": _lv(12, 100)}, one) + G.plasmid({"p": _lv(3, 300)}, one)
    provirus = G.condense(G.plasmid({"provirus": _lv(4, 400)}, one), coupling=one, state=True)
    integrated = G.integrate(host, provirus)
    # find the provirus chromosome and confirm its chromatin state rode along
    start = next(i for i, hv in enumerate(integrated)
                 if G._cap_kind(hv) in G._CHROM_BOUNDARY_MARKERS
                 and G._unpack_cap(hv)[1] == "provirus")
    end = next((i for i in range(start + 1, len(integrated))
                if G._cap_kind(integrated[i]) in G._CHROM_BOUNDARY_MARKERS), len(integrated))
    assert G.chromatin_of(integrated[start:end], one)["state"] == "condensed"


def test_multi_chromosome_condense_by_label():
    one = _one()
    genome = G.plasmid({"a": _lv(3, 1), "b": _lv(3, 2)}, one)
    with pytest.raises(ValueError):
        G.condense(genome, coupling=one, state=True)                      # ambiguous: needs a label
    cond = G.condense(genome, coupling=one, state=True, label="b")
    # chromatin_of on the 'b' chromosome region sees it; 'a' is untouched
    bounds = [i for i, hv in enumerate(cond)
              if G._cap_kind(hv) in G._CHROM_BOUNDARY_MARKERS]
    a_start, b_start = bounds[0], bounds[1]
    assert G.chromatin_of(cond[a_start:b_start], one) is None
    assert G.chromatin_of(cond[b_start:], one)["state"] == "condensed"


# ── backward-compat: a chromatin-free genome reads identically ───────────────

def test_chromatin_free_genome_round_trips_unchanged(tmp_path):
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    data = G.genome_save(chrom, tmp_path, one)
    assert data["format_version"] == 15                                  # v15 writer
    cat = G.genome_catalog(tmp_path, coupling=one)
    assert cat["chromosomes"][0]["cap_kind"] == "nuclear"                # census unbroken
    assert cat["chromosomes"][0]["leaf_count"] == 12
    reloaded = _reload_strand(tmp_path, len(list(one)))
    assert G.chromatin_of(reloaded, one) is None


# ── native == pure parity for every new C op ─────────────────────────────────

@pytest.mark.skipif(not _N.HAS_NATIVE, reason="native lib not loaded (pure path is the oracle)")
def test_native_cap_writer_equals_pure():
    dim = 64
    for ct, num, den, handle in [(0, 0, 1, "chr"), (0, 1, 1, "x"), (1, 1, 3, "cen"),
                                 (1, 2, 5, ""), (1, 7, 9, "region_a")]:
        nat = _N.genome_chromatin_c(ct, num, den, handle, dim)
        pure = G._pack_chromatin(ct, num, den, dim, handle=handle).tobytes()
        assert nat is not None and nat == pure, (ct, num, den, handle)


@pytest.mark.skipif(not _N.HAS_NATIVE, reason="native lib not loaded (pure path is the oracle)")
def test_native_chromatin_of_equals_pure():
    one = _one()
    chrom = G.mint({"astro": _lv(12, 100)}, one)
    for kwargs in [dict(state=True), dict(state=False), dict(state=(1, 3)),
                   dict(state=(2, 7), region=4), dict(state=True, region=0)]:
        cond = G.condense(chrom, coupling=one, **kwargs)
        native = G.chromatin_of(cond, one)
        import srmech.amsc._native as NN
        saved = NN.has_native_genome_chromatin_of
        NN.has_native_genome_chromatin_of = lambda: False
        try:
            pure = G.chromatin_of(cond, one)
        finally:
            NN.has_native_genome_chromatin_of = saved
        assert native == pure, kwargs
