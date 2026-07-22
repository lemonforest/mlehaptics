"""v0.9.0rc198 — the genome MULTI-KERNEL + PARTITION get their C peers (#887).

The FOURTH (and final in-memory) leaf-batch of the make_class → C arc, COMPLETING
the genome leaf-family in C. The genome.toml [class] descriptor binds 10 leaf ops;
rc198 ships the C peers of the two multi-kernel leaves:

  * ``srmech_genome_genome`` — assemble n labelled kernels into ONE strand: each
    kernel → a CHROM-capped chromosome (LOOPING the rc197 ``srmech_genome_chromosome``),
    concatenated in kernel order. ``genome.genome`` DISPATCHES to it when HAS_NATIVE
    for the plain single-gene-per-chromosome path → BYTE-IDENTICAL to the pure loop.

  * ``srmech_genome_partition`` — the inverse: open a partition per CHROM /
    kernel-telomere / active-telomere cap (label inline), skip gene / header caps
    (flatten), re-bind each data turn through ``coupling``. ``genome.partition``
    DISPATCHES to it when HAS_NATIVE; the caller builds the ``{label: [leaves]}``
    dict (dict overwrite-on-duplicate-label) + applies the ``labels=`` filter.

Both LOOP the rc197 leaves + reuse the rc196 cap foundation verbatim. The genome
in-memory ops are byte-exact (cap framing + reversible Klein-4 XOR), so everything
here is byte-identical portable — NOT within-tol. Additive C symbols →
SRMECH_ABI_VERSION stays 4. numpy-free.
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome
from srmech.amsc import _native
from srmech.amsc.hdc import klein4_expand


_DIMS = [8, 16, 64]
_LABELS_SETS = [
    ["astronomy", "geography", "music"],        # the F715 exemplar
    ["a"],
    ["", "b", "chr-3"],
    ["x", "x", "y"],                            # duplicate labels (dict last-wins)
    ["z" * 7, "TTAGGG", "unicode-éè"],
]


def _one(dim, seed=7):
    return klein4_expand(dim, seed)


def _fits(labels, dim):
    """A label must fit one fixed-width ``dim``-byte cap leaf (§44: marker + label +
    NUL padding → label ≤ dim - 1 UTF-8 bytes)."""
    return all(len(lbl.encode("utf-8")) <= dim - 1 for lbl in labels)


def _kernels(labels, dim, base_seed):
    """A ``{label: [leaves]}`` mapping — deterministic klein4 leaves, varied counts
    (0..3 leaves per kernel, so empty kernels + duplicate labels are exercised)."""
    out = []
    for i, lbl in enumerate(labels):
        n = i % 4                                # 0, 1, 2, 3, … leaves
        leaves = [klein4_expand(dim, base_seed + i * 10 + j) for j in range(n)]
        out.append((lbl, leaves))
    return out


def _strand_bytes(strand):
    return [hv.tobytes() for hv in strand]


def _dict_bytes(d):
    return {k: [hv.tobytes() for hv in v] for k, v in d.items()}


# ── the C peers are actually loaded (so parity exercises C, not both-pure) ─────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_multikernel_symbols_present():
    assert _native.has_native_genome_genome()
    assert _native.has_native_genome_partition()
    assert _native.EXPECTED_ABI_VERSION == 9


# ── (i) srmech_genome_genome → the strand is BYTE-IDENTICAL native-vs-pure ─────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_genome_native_equals_pure_byte_identical():
    saved = _native.HAS_NATIVE
    try:
        for dim in _DIMS:
            one = _one(dim)
            for si, labels in enumerate(_LABELS_SETS):
                if not _fits(labels, dim):
                    continue
                items = _kernels(labels, dim, base_seed=100 + si)
                _native.HAS_NATIVE = True
                native = genome.genome(dict(items), one)
                _native.HAS_NATIVE = False
                pure = genome.genome(dict(items), one)
                assert _strand_bytes(native) == _strand_bytes(pure), (dim, labels)
                # a genome strand IS a strand — its blocks are (n_kernels + Σleaves).
                n_leaves = sum(len(lv) for _, lv in dict(items).items())
                assert len(native) == len(dict(items)) + n_leaves
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_genome_accepts_pair_sequence_like_pure():
    # genome() takes a dict OR a (label, leaves) sequence (insertion order) — both
    # dispatch byte-identically.
    saved = _native.HAS_NATIVE
    try:
        dim = 16
        one = _one(dim)
        items = _kernels(["p", "q", "r"], dim, base_seed=41)
        _native.HAS_NATIVE = True
        native = genome.genome(items, one)          # sequence form
        _native.HAS_NATIVE = False
        pure = genome.genome(items, one)
        assert _strand_bytes(native) == _strand_bytes(pure)
    finally:
        _native.HAS_NATIVE = saved


# ── (ii) srmech_genome_partition → {label: leaves} round-trips native-vs-pure ──

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_partition_native_equals_pure_byte_identical():
    saved = _native.HAS_NATIVE
    try:
        for dim in _DIMS:
            one = _one(dim)
            for si, labels in enumerate(_LABELS_SETS):
                if not _fits(labels, dim):
                    continue
                items = _kernels(labels, dim, base_seed=200 + si)
                strand = genome.genome(dict(items), one)   # native build (HAS_NATIVE)
                _native.HAS_NATIVE = True
                native = genome.partition(strand, one)
                _native.HAS_NATIVE = False
                pure = genome.partition(strand, one)
                assert _dict_bytes(native) == _dict_bytes(pure), (dim, labels)
                # keys preserve insertion order (dict overwrite-on-dup keeps position)
                assert list(native.keys()) == list(pure.keys())
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_partition_recovers_the_original_leaves():
    # the round-trip law: partition(genome({...})) recovers each kernel's leaves.
    saved = _native.HAS_NATIVE
    try:
        dim = 32
        one = _one(dim, seed=13)
        items = _kernels(["astronomy", "geography", "music"], dim, base_seed=300)
        km = dict(items)
        strand = genome.genome(km, one)
        _native.HAS_NATIVE = True
        recovered = genome.partition(strand, one)
        # every DISTINCT label round-trips to its exact leaves (last-wins for dups,
        # but these labels are distinct)
        for lbl, leaves in km.items():
            assert [hv.tobytes() for hv in recovered[lbl]] == \
                   [hv.tobytes() for hv in leaves], lbl
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_partition_labels_filter_native_equals_pure():
    saved = _native.HAS_NATIVE
    try:
        dim = 16
        one = _one(dim)
        items = _kernels(["a", "b", "c", "d"], dim, base_seed=55)
        strand = genome.genome(dict(items), one)
        for flt in (["b", "d"], ["c"], ["missing"], ["d", "a"], []):
            _native.HAS_NATIVE = True
            native = genome.partition(strand, one, labels=flt)
            _native.HAS_NATIVE = False
            pure = genome.partition(strand, one, labels=flt)
            assert _dict_bytes(native) == _dict_bytes(pure), flt
            assert list(native.keys()) == list(pure.keys())
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_partition_flattens_multigene_strand_native_equals_pure():
    # partition FLATTENS across §44 gene caps (gate-agnostic). A chromosomes= genome
    # strand (multi-gene, built pure) partitions to concatenated leaves — native == pure.
    saved = _native.HAS_NATIVE
    try:
        dim = 16
        one = _one(dim)
        chromosomes = [
            ("rules", [("r", [klein4_expand(dim, 1)]),
                       ("s", [klein4_expand(dim, 2), klein4_expand(dim, 3)])]),
            ("board", [("b", [klein4_expand(dim, 4)])]),
        ]
        strand = genome.genome(coupling=one, chromosomes=chromosomes)   # pure §44 build
        _native.HAS_NATIVE = True
        native = genome.partition(strand, one)
        _native.HAS_NATIVE = False
        pure = genome.partition(strand, one)
        assert _dict_bytes(native) == _dict_bytes(pure)
        # rules flattens its two genes (1 + 2 = 3 leaves); board has 1.
        assert [len(v) for v in native.values()] == [3, 1]
    finally:
        _native.HAS_NATIVE = saved


# ── over-long label: native returns None → the pure path raises (identical) ───

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_genome_overlong_label_raises_in_both_paths():
    # a kernel label that will not fit dim - 1 bytes → the native genome_genome_c
    # returns None (its guard rejects it) so the pure per-kernel chromosome raises the
    # exact ValueError — identical error semantics native or pure.
    dim = 8
    one = _one(dim)
    km = {"x" * 8: [klein4_expand(dim, 1)]}      # 8 > dim - 1 = 7
    saved = _native.HAS_NATIVE
    try:
        for flag in (True, False):
            _native.HAS_NATIVE = flag
            with pytest.raises(ValueError):
                genome.genome(km, one)
    finally:
        _native.HAS_NATIVE = saved


# ── (iii) the round-trip identity holds (native path) ─────────────────────────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_full_roundtrip_genome_then_partition():
    saved = _native.HAS_NATIVE
    try:
        dim = 64
        one = _one(dim, seed=99)
        km = dict(_kernels(["one", "two", "three", "four"], dim, base_seed=400))
        _native.HAS_NATIVE = True
        rt = genome.partition(genome.genome(km, one), one)
        assert set(rt.keys()) == set(km.keys())
        for lbl in km:
            assert [hv.tobytes() for hv in rt[lbl]] == \
                   [hv.tobytes() for hv in km[lbl]]
    finally:
        _native.HAS_NATIVE = saved


# ── (iv) the genome leaf-family is COMPLETE in C — all 10 leaves C-realizable ──

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_genome_leaf_family_complete_in_c():
    # rc196: encode_shape + telomere; rc197: chromosome + recall; rc198: genome +
    # partition; the 4 FS ops already have C peers + native-dispatching wrappers.
    assert _native.has_native_genome_encode_shape()
    assert _native.has_native_genome_telomere()
    assert _native.has_native_genome_chromosome()
    assert _native.has_native_genome_recall()
    assert _native.has_native_genome_genome()
    assert _native.has_native_genome_partition()
    # the 4 FS peers (legitimate host-FS dispatch, ready for the rc201 leaf-vtable)
    assert _native.has_native_genome()                       # the family gate
    for sym in ("srmech_genome_save", "srmech_genome_load",
                "srmech_genome_catalog", "srmech_genome_append"):
        assert hasattr(_native.LIB, sym), sym
    for wrapper in ("genome_save_c", "genome_load_c",
                    "genome_catalog_c", "genome_append_c"):
        assert callable(getattr(_native, wrapper)), wrapper
