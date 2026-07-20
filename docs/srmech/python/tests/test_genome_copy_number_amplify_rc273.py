"""v0.9.0rc273 (§135 / F1251) — gene COPY-NUMBER (multiplicity): amplify + copy_number_of.

F1251 (attested Shropshire bacterial genomics) measured that IS26-mediated amplification
raises a resistance gene's COPY NUMBER — the genome stores "how many copies", a MULTIPLICITY
annotation (a count), NOT N physical duplicated strands. rc273 records that on the named plain
gene's 0x47 cap: `amplify(chrom, label, n)` sets the count, `copy_number_of(chrom, label)`
reads it (default 1 = a plain / pre-rc273 gene = present-once).

Encoding = a uint64 big-endian field carried RIGHT AFTER the label's NUL, in what was the gene
cap's NUL padding (the §127 active-count / §129 mask placement). n == 1 is BYTE-IDENTICAL to a
plain gene (only n >= 2 spends the field); the count is TRANSPARENT to every reader (a 0x47 cap
reads always-express regardless of the trailing bytes) and survives genome_save / reload +
integrate byte-exact. No new marker; format 15 stays. Class-I/N exact integer, no float, never
abs(). numpy-free.
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome as G
from srmech.amsc.hdc import klein4_expand


def _one(seed=7):
    return klein4_expand(64, seed)


def _lv(n, base=0):
    return [klein4_expand(64, base + s) for s in range(n)]


def _chrom(one):
    # a multi-gene chromosome: two plain genes (resA, resB)
    return G.chromosome(genes=[("resA", _lv(2, 10)), ("resB", _lv(3, 20))],
                        coupling=one, label="plasmidR")


# ── amplify sets, copy_number_of reads; a plain gene reads 1 ─────────────────

def test_plain_gene_reads_copy_number_one():
    one = _one()
    chrom = _chrom(one)
    assert G.copy_number_of(chrom, "resA") == 1               # present-once (default)
    assert G.copy_number_of(chrom, "resB") == 1


def test_amplify_then_copy_number_of_returns_n():
    one = _one()
    chrom = _chrom(one)
    amp = G.amplify(chrom, "resA", 7)
    assert G.copy_number_of(amp, "resA") == 7                 # amplified
    assert G.copy_number_of(amp, "resB") == 1                 # the other gene unchanged
    assert len(amp) == len(chrom)                             # a count, NOT N strands


def test_amplify_various_counts_roundtrip():
    one = _one()
    for n in (2, 3, 42, 1000, (1 << 40)):
        amp = G.amplify(_chrom(one), "resB", n)
        assert G.copy_number_of(amp, "resB") == n


# ── n == 1 is byte-identical to a plain gene (§129 dual-read) ────────────────

def test_amplify_to_one_is_byte_identical_to_plain():
    one = _one()
    chrom = _chrom(one)
    amp1 = G.amplify(chrom, "resA", 1)
    assert [x.tobytes() for x in amp1] == [x.tobytes() for x in chrom]
    assert G.copy_number_of(amp1, "resA") == 1


def test_only_the_named_gene_is_rewritten():
    one = _one()
    chrom = _chrom(one)
    amp = G.amplify(chrom, "resA", 9)
    # every block EXCEPT the resA gene cap is byte-identical to the original
    diffs = [i for i, (a, b) in enumerate(zip(chrom, amp)) if a.tobytes() != b.tobytes()]
    assert len(diffs) == 1                                    # exactly one block changed
    # and that one block is a plain GENE cap whose label is resA
    changed = amp[diffs[0]]
    assert G._cap_kind(changed) == G.GENE_CAP_MARKER
    assert G._unpack_cap(changed)[1] == "resA"


# ── the count is TRANSPARENT to every existing reader ────────────────────────

def test_amplify_preserves_gene_content_and_labels():
    one = _one()
    chrom = _chrom(one)
    amp = G.amplify(chrom, "resA", 5)
    g0 = dict((l, [x.tobytes() for x in leaves]) for l, leaves in G.genes(chrom, one))
    g1 = dict((l, [x.tobytes() for x in leaves]) for l, leaves in G.genes(amp, one))
    assert g0 == g1                                           # labels + leaves byte-identical


def test_gene_express_is_transparent_to_copy_number():
    one = _one()
    amp = G.amplify(_chrom(one), "resA", 5)
    # plain genes always express — the copy-number field does not gate them
    expressed = sorted(l for l, _ in G.gene_express(amp, one, 0))
    assert expressed == ["resA", "resB"]


# ── the count survives genome_save / reload + integrate byte-exact ───────────

def test_copy_number_survives_save_reload(tmp_path):
    one = _one()
    amp = G.amplify(_chrom(one), "resA", 13)
    G.genome_save(amp, tmp_path, coupling=one)
    loaded, _o, _l = G.genome_load(tmp_path, coupling=one)
    assert G.copy_number_of(loaded, "resA") == 13
    assert G.copy_number_of(loaded, "resB") == 1


def test_copy_number_survives_integrate_and_disk(tmp_path):
    one = _one()
    provirus = G.amplify(_chrom(one), "resA", 21)             # an amplified plasmid provirus
    host = G.mint({"core": _lv(6, 100)}, one)
    integrated = G.integrate(host, provirus)
    assert integrated is not None
    assert G.copy_number_of(integrated, "resA") == 21         # survives the splice
    G.genome_save(integrated, tmp_path, coupling=one)
    loaded, _o, _l = G.genome_load(tmp_path, coupling=one)
    assert G.copy_number_of(loaded, "resA") == 21             # + the disk round-trip
    assert set(G.partition(loaded, one)) == {"core", "plasmidR"}


# ── backward-compat: a pre-rc273-shaped genome reads copy_number 1 ───────────

def test_pre_rc273_plain_genome_reads_one(tmp_path):
    """A genome built + saved with NO copy-number (the pre-rc273 shape — all plain genes)
    reads copy_number 1 on every gene: the all-NUL gene-cap padding == stored 0 == 1."""
    one = _one()
    chrom = _chrom(one)                                       # plain genes, no amplify
    G.genome_save(chrom, tmp_path, coupling=one)
    loaded, _o, _l = G.genome_load(tmp_path, coupling=one)
    assert G.copy_number_of(loaded, "resA") == 1
    assert G.copy_number_of(loaded, "resB") == 1


# ── exact encoding (native==pure): amplify is deterministic byte work ────────

def test_copy_number_field_is_exact_uint64_be():
    one = _one()
    amp = G.amplify(_chrom(one), "resA", 258)                 # 258 = 0x0102
    cap = next(hv for hv in amp
               if G._cap_kind(hv) == G.GENE_CAP_MARKER and G._unpack_cap(hv)[1] == "resA")
    raw = cap.tobytes()
    nul = raw.find(b"\x00", 1)
    stored = int.from_bytes(raw[nul + 1:nul + 9], "big")
    assert stored == 258
    # the cap is a deterministic function of (label, n, dim) — the native==pure guarantee for a
    # pure-composition op: amplify rewrites the cap identically regardless of how chrom was built
    # (the chromosome() builder is c_dispatched byte-identical, so amplify over it is native==pure)
    expected = G._pack_gene_cap_copy_number("resA", 258, len(cap)).tobytes()
    assert raw == expected


# ── error handling: no such gene / invalid n ─────────────────────────────────

def test_amplify_unknown_gene_raises():
    one = _one()
    with pytest.raises(ValueError):
        G.amplify(_chrom(one), "nope", 3)


def test_copy_number_of_unknown_gene_raises():
    one = _one()
    with pytest.raises(ValueError):
        G.copy_number_of(_chrom(one), "nope")


@pytest.mark.parametrize("bad", [0, -1, -5])
def test_amplify_rejects_non_positive_n(bad):
    one = _one()
    with pytest.raises(ValueError):
        G.amplify(_chrom(one), "resA", bad)


def test_amplify_rejects_bool_n():
    one = _one()
    with pytest.raises(ValueError):
        G.amplify(_chrom(one), "resA", True)                  # bool is not an exact int count
