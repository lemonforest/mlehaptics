"""v0.9.0rc281 (§135 / F1251 / G6) — the srmech_genome_amplify + srmech_genome_copy_number peers.

The c_host_parity_audit_rc273 called this pair its CLEANEST EXHIBIT of a 1:1-parity gap
wearing an honest-looking label. rc273 shipped ``amplify`` / ``copy_number_of`` Python-only
under a ``composition_of_c`` bucket, and its C test proved only that the copy-number field is
TRANSPARENT to the existing readers (``srmech_genome_gene_express`` returns on the ``0x47``
marker before reading any field) — concluding "no C change needed". That conclusion confuses
two different properties: **transparent-to-readers is not C-host parity**. There was no C path
to WRITE the count (``amplify``) or to READ its value (``copy_number_of``), so a bare-C host
could only IGNORE the copy-number axis, never use it.

rc281 ships both peers and wires both Python ops to DISPATCH the WHOLE op to them, so
ADR-0003 (C-host-standalone) holds across the whole §135 surface.

Proven here — C↔Python BYTE-PARITY: across several labels, copy numbers (1 / 2 / large /
uint64-max) and multiple ``leaf_dim``s, the native strand bytes == the pure strand bytes (0
mismatches) and the native count == the pure count; ``n == 1`` stays byte-identical to a plain
never-amplified gene (no field spent); a plain / pre-rc273 gene still reads 1 through BOTH
paths; the error contract is unchanged when the peer DECLINES; and the C peer is exercised
directly through ``_native``. numpy-free; the whole file runs unchanged in a numpy-absent
forced-pure venv (where the dispatch is a no-op and the pure cap rewrite is exercised).
"""
from __future__ import annotations

import pytest

from srmech.biology import genome as G
from srmech import _native
from srmech.math.hdc import klein4_expand

# leaf_dims wide enough for the label + NUL + the 8-byte field, and one (32) that is
# comfortably tight — the field placement must hold at every width.
_DIMS = (32, 64, 128)
_LABELS = ("resA", "resB", "bla", "tetA_long_gene_label")
# 1 == the DEFAULT (byte-identical to plain), 2 == the first count that spends the field,
# then a spread up to the uint64 ceiling the field can hold.
_COUNTS = (1, 2, 3, 255, 256, 65535, 1 << 20, 1 << 40, (1 << 64) - 1)


def _one(dim, seed=1281):
    return klein4_expand(dim, seed)


def _lv(n, dim, base=0):
    return [klein4_expand(dim, base + s) for s in range(n)]


def _chrom(dim, one):
    """A multi-gene chromosome carrying every label under test."""
    genes = [(lab, _lv(2, dim, 10 + 40 * i)) for i, lab in enumerate(_LABELS)]
    return G.chromosome(genes=genes, coupling=one, label="plasmidR")


def _blocks(strand):
    return [b.tobytes() for b in strand]


def _sectors(strand):
    return [getattr(b, "sectors", None) for b in strand]


# ── C↔Python byte-parity: amplify ────────────────────────────────────────────

@pytest.mark.parametrize("dim", _DIMS)
@pytest.mark.parametrize("label", _LABELS)
def test_native_amplify_matches_pure_oracle(dim, label, monkeypatch):
    """native == pure, byte-for-byte, for every count — the differential proof."""
    one = _one(dim)
    chrom = _chrom(dim, one)
    for n in _COUNTS:
        got = G.amplify(chrom, label, n)                      # native (when built)
        # FORCE the pure fallback (as in a numpy-absent / no-C venv) and compare.
        monkeypatch.setattr(_native, "genome_amplify_c", lambda *a, **k: None)
        pure = G.amplify(chrom, label, n)
        monkeypatch.undo()
        assert _blocks(got) == _blocks(pure), f"dim={dim} label={label} n={n}"
        # the carrier shape must round-trip too, not just the bytes
        assert _sectors(got) == _sectors(pure), f"sectors drift dim={dim} n={n}"
        assert len(got) == len(chrom)          # a MULTIPLICITY, never N strands


@pytest.mark.parametrize("dim", _DIMS)
@pytest.mark.parametrize("label", _LABELS)
def test_native_copy_number_matches_pure_oracle(dim, label, monkeypatch):
    """The READ half: native count == pure count for every amplified value."""
    one = _one(dim)
    chrom = _chrom(dim, one)
    for n in _COUNTS:
        amp = G.amplify(chrom, label, n)
        got = G.copy_number_of(amp, label)                    # native (when built)
        monkeypatch.setattr(_native, "genome_copy_number_c", lambda *a, **k: None)
        pure = G.copy_number_of(amp, label)
        monkeypatch.undo()
        assert got == pure == n, f"dim={dim} label={label} n={n}: {got} vs {pure}"


def test_native_peer_byte_identical_over_many_combos():
    """The native peer across every dim × label × count — 0 mismatches."""
    if not _native.has_native_genome_amplify():
        pytest.skip("no native srmech_genome_amplify peer in this build")
    mismatches, combos = 0, 0
    for dim in _DIMS:
        one = _one(dim)
        chrom = _chrom(dim, one)
        blocks = [b.tobytes() for b in chrom]
        raw = b"".join(blocks)
        for label in _LABELS:
            for n in _COUNTS:
                combos += 1
                native = _native.genome_amplify_c(raw, len(blocks), dim, label, n)
                pure = b"".join(b.tobytes()
                                for b in G.amplify(chrom, label, n))
                if native != pure:
                    mismatches += 1
    assert combos > 0
    assert mismatches == 0, f"{mismatches}/{combos} native-vs-pure byte mismatches"


# ── the n == 1 identity: the DEFAULT spends no wire ──────────────────────────

@pytest.mark.parametrize("dim", _DIMS)
def test_amplify_to_one_is_byte_identical_to_a_plain_gene(dim):
    """n == 1 rewrites to the PLAIN cap — the field is ABSENT, not zero-filled.
    This is what keeps a never-amplified gene and an amplified-to-1 gene the same
    bytes, and it must hold through the native path as well as the pure one."""
    one = _one(dim)
    chrom = _chrom(dim, one)
    amp1 = G.amplify(chrom, "resA", 1)
    assert _blocks(amp1) == _blocks(chrom)
    assert G.copy_number_of(amp1, "resA") == 1


@pytest.mark.parametrize("dim", _DIMS)
def test_plain_and_pre_rc273_genes_read_one_through_both_paths(dim, monkeypatch):
    """All-NUL padding == stored 0 == copy-number 1 (back-compat), native AND pure."""
    one = _one(dim)
    chrom = _chrom(dim, one)
    for label in _LABELS:
        native = G.copy_number_of(chrom, label)
        monkeypatch.setattr(_native, "genome_copy_number_c", lambda *a, **k: None)
        pure = G.copy_number_of(chrom, label)
        monkeypatch.undo()
        assert native == pure == 1, f"{label} at dim={dim}"


# ── only the named gene moves; every other block is byte-copied ──────────────

@pytest.mark.parametrize("dim", _DIMS)
def test_amplify_touches_exactly_one_block(dim):
    one = _one(dim)
    chrom = _chrom(dim, one)
    before = _blocks(chrom)
    amp = G.amplify(chrom, "resB", 12345)
    after = _blocks(amp)
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert len(changed) == 1, f"expected 1 rewritten cap, got {changed}"
    # and the OTHER genes still read their own (default) count
    for other in _LABELS:
        if other != "resB":
            assert G.copy_number_of(amp, other) == 1
    assert G.copy_number_of(amp, "resB") == 12345


def test_amplify_is_not_in_place():
    """A READ-shaped contract: the input strand is untouched by amplify."""
    one = _one(64)
    chrom = _chrom(64, one)
    before = _blocks(chrom)
    G.amplify(chrom, "resA", 99)
    assert _blocks(chrom) == before


# ── error contract unchanged (the peer DECLINES; the pure body raises) ───────

@pytest.mark.parametrize("bad", [0, -1, -1000])
def test_amplify_rejects_counts_below_one(bad):
    """A multiplicity is never signed — there is nothing to strip, so this is a
    DOMAIN gate, not a Class-K pin-slot site (and never abs())."""
    one = _one(64)
    with pytest.raises(ValueError):
        G.amplify(_chrom(64, one), "resA", bad)


def test_amplify_rejects_a_missing_gene():
    one = _one(64)
    with pytest.raises(ValueError):
        G.amplify(_chrom(64, one), "nosuchgene", 4)


def test_copy_number_of_rejects_a_missing_gene():
    """A caller must be able to tell "absent gene" from "present once" — so this
    raises rather than returning 0 or 1, through the native path too."""
    one = _one(64)
    with pytest.raises(ValueError):
        G.copy_number_of(_chrom(64, one), "nosuchgene")


def test_amplify_rejects_a_non_integer_count():
    one = _one(64)
    for bad in (2.0, "3", None, True):
        with pytest.raises(ValueError):
            G.amplify(_chrom(64, one), "resA", bad)


# ── the count survives the readers it must be transparent to ────────────────

def test_amplified_cap_is_still_read_as_a_plain_always_expressed_gene():
    """The rc273 transparency property, re-proven with the peer in the loop: an
    amplified cap is still the SAME always-expressed plain gene to every reader."""
    one = _one(64)
    chrom = _chrom(64, one)
    amp = G.amplify(chrom, "resA", 500)
    before = [lab for lab, _ in G.genes(chrom, one)]
    after = [lab for lab, _ in G.genes(amp, one)]
    assert before == after                       # same genes, same order, same labels
    assert G.recall(amp, one) == G.recall(chrom, one)   # the data turns are untouched


def test_count_survives_a_second_amplify():
    """Amplifying an already-amplified gene REPLACES the count (it is an annotation,
    not an accumulator) — and the label still decodes uniformly past the field."""
    one = _one(64)
    chrom = _chrom(64, one)
    amp = G.amplify(G.amplify(chrom, "resA", 9), "resA", 4)
    assert G.copy_number_of(amp, "resA") == 4
    amp1 = G.amplify(amp, "resA", 1)             # back to the plain form
    assert _blocks(amp1) == _blocks(chrom)


# ── the peer's own guards ───────────────────────────────────────────────────

def test_native_declines_rather_than_guessing():
    """A DECLINE (None) is how the peer hands a case back to the pure body — it must
    never return a wrong answer instead."""
    if not _native.has_native_genome_amplify():
        pytest.skip("no native srmech_genome_amplify peer in this build")
    one = _one(64)
    chrom = _chrom(64, one)
    raw = b"".join(b.tobytes() for b in chrom)
    n_blocks = len(chrom)
    assert _native.genome_amplify_c(raw, n_blocks, 64, "nosuchgene", 3) is None
    assert _native.genome_amplify_c(raw, n_blocks, 64, "resA", 0) is None
    assert _native.genome_copy_number_c(raw, n_blocks, 64, "nosuchgene") is None
    # a width that does not match the buffer is a shape decline, not a crash
    assert _native.genome_amplify_c(raw, n_blocks, 63, "resA", 3) is None
