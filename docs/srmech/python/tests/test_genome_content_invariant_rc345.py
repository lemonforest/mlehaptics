"""rc345 (task T964) — the genome CONTENT invariant, and what ``genome_save`` returns.

Three things are pinned here:

1. **The invariant.** ``n_turns - n_chromosomes`` is fixed under repartitioning of fixed
   content, while ``n_turns`` / ``n_chromosomes`` / ``body_sha256`` all move. The 8-row
   partition sweep is the fixture; ``scratchpad/fusion_test.py`` is the generator for the
   numbers quoted in the CHANGELOG.
2. **The return shape.** ``genome_save`` returns the FULL catalog; it now carries the
   scalars ``n_chromosomes`` + ``n_content`` alongside the ``chromosomes`` array, and
   the on-disk HEAD is unchanged (no ``n_content``, ``format_version`` still 19).
3. **The no-auto-partition contract.** ``genome_save`` derives boundaries from caps the
   caller placed; it never invents one.

Every test here is numpy-free (the module under test is).
"""

import json

import pytest

import srmech.biology.genome as G
from srmech.math.hdc import klein4_expand

DIM = 64
TOTAL = 24
SEED = 7
#: (n_chromosomes, leaves_per_chromosome, expected n_turns) — MEASURED, not predicted.
#: Each row's n_turns is TOTAL + n_chromosomes: one boundary cap per chromosome, and a
#: cap IS a turn. See scratchpad/fusion_test.py.
SWEEP = (
    (1, 24, 25),
    (2, 12, 26),
    (3, 8, 27),
    (4, 6, 28),
    (6, 4, 30),
    (8, 3, 32),
    (12, 2, 36),
    (24, 1, 48),
)


def _coupling():
    return klein4_expand(DIM, SEED)


def _leaves():
    return [klein4_expand(DIM, s) for s in range(TOTAL)]


def _save_partitioned(tmp_path, parts, name=None):
    """Write the SAME TOTAL leaves as ``parts`` chromosomes. Returns (path, ret)."""
    one = _coupling()
    leaves = _leaves()
    step = TOTAL // parts
    strand = []
    for i in range(parts):
        strand += G.chromosome(leaves[i * step:(i + 1) * step], one, label=f"c{i}")
    path = tmp_path / (name or f"g{parts}")
    ret = G.genome_save(strand, str(path), coupling=one)
    return path, ret


# ── 1. the invariant ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("parts,step,expected_turns", SWEEP)
def test_cap_is_a_turn_so_n_turns_is_leaves_plus_chromosomes(
        tmp_path, parts, step, expected_turns):
    """Each chromosome costs EXACTLY one turn. The whole rc rests on this row."""
    _path, ret = _save_partitioned(tmp_path, parts)
    assert ret["n_turns"] == expected_turns
    assert ret["n_chromosomes"] == parts
    # The exact statement: turns minus containers is the content, with no residual.
    assert ret["n_turns"] - ret["n_chromosomes"] == TOTAL
    assert ret["n_content"] == TOTAL


def test_content_is_invariant_while_turns_chroms_and_digest_all_move(tmp_path):
    """The discriminating test: three quantities move, one does not.

    Without the "and the others move" half this would pass on a fixture that never
    repartitioned anything.
    """
    contents, turns, chroms, digests = set(), set(), set(), set()
    for parts, _step, _expected in SWEEP:
        _path, ret = _save_partitioned(tmp_path, parts, name=f"p{parts}")
        contents.add(ret["n_content"])
        turns.add(ret["n_turns"])
        chroms.add(ret["n_chromosomes"])
        digests.add(ret["body_sha256"])
    assert contents == {TOTAL}, "n_content must be invariant under repartitioning"
    assert len(turns) == len(SWEEP), "n_turns must NOT be invariant (else no discrimination)"
    assert len(chroms) == len(SWEEP), "n_chromosomes must NOT be invariant"
    assert len(digests) == len(SWEEP), "body_sha256 must NOT be invariant"


def test_content_counts_non_boundary_blocks_not_leaves(tmp_path):
    """The honest scope of the invariant: n_content includes INLINE caps.

    ``n_content == total_leaves`` is a CAP-FREE-INTERIOR statement. Written as genes, the
    same 24 leaves give a strictly larger n_content — by exactly the inline-cap count.
    This is the test that stops the invariant being oversold as "the leaf count".
    """
    one = _coupling()
    leaves = _leaves()
    n_genes = 4
    per = TOTAL // n_genes
    genes = [(f"g{i}", leaves[i * per:(i + 1) * per]) for i in range(n_genes)]
    path = tmp_path / "genes"
    ret = G.genome_save(G.chromosome(coupling=one, label="multi", genes=genes),
                        str(path), coupling=one)
    census = G.genome_census(str(path), coupling=one)
    assert ret["n_chromosomes"] == 1
    assert census["total_leaves"] == TOTAL
    # MEASURED: n_turns 29, n_content 28, total_leaves 24 → 4 inline GENE caps.
    assert ret["n_content"] == census["total_leaves"] + n_genes
    assert ret["n_content"] > census["total_leaves"]
    # ...whereas a cap-free-interior genome has them equal (the SWEEP case).
    _p2, flat = _save_partitioned(tmp_path, 1, name="flat")
    flat_census = G.genome_census(str(tmp_path / "flat"), coupling=one)
    assert flat["n_content"] == flat_census["total_leaves"] == TOTAL


# ── 2. the return shape, and what stays off disk ─────────────────────────────

def test_genome_save_return_carries_the_scalar_and_agrees_with_the_array(tmp_path):
    """The rc345 fix: the FULL catalog had the array but not the scalar, so
    ``genome_save(...).get("n_chromosomes")`` read None while the HEAD carried it."""
    for parts, _step, _expected in SWEEP:
        path, ret = _save_partitioned(tmp_path, parts, name=f"s{parts}")
        assert ret["n_chromosomes"] is not None
        assert ret["n_chromosomes"] == len(ret["chromosomes"]) == parts
        assert ret["n_content"] == ret["n_turns"] - ret["n_chromosomes"]
        # the HEAD's scalar is the same number, read back off disk
        head = json.loads((path / "manifest.json").read_text(encoding="utf-8"))["data"]
        assert head["n_chromosomes"] == ret["n_chromosomes"]


def test_content_is_derived_never_stored(tmp_path):
    """ONE ENCODING PER DATUM. n_content is exactly recoverable from the strand, so it
    gets no home in the format: the on-disk head is unchanged and the format version
    does not move. A stored copy would be a second encoding that can go stale."""
    path, _ret = _save_partitioned(tmp_path, 3)
    head = json.loads((path / "manifest.json").read_text(encoding="utf-8"))["data"]
    assert "n_content" not in head, "n_content must NOT be persisted"
    assert head["format_version"] == G.GENOME_FORMAT_VERSION == 20
    assert sorted(head) == ["body_sha256", "carrier", "coupling", "format_version",
                            "leaf_dim", "n_chromosomes", "n_turns"]


def test_genome_content_accessor_agrees_with_save_and_catalog(tmp_path):
    """The accessor, the save return, and the re-derived catalog are one answer."""
    one = _coupling()
    for parts, _step, _expected in SWEEP:
        path, ret = _save_partitioned(tmp_path, parts, name=f"a{parts}")
        got = G.genome_content(str(path), coupling=one)
        cat = G.genome_catalog(str(path), coupling=one)
        assert got["n_turns"] == ret["n_turns"] == cat["n_turns"]
        assert got["n_chromosomes"] == ret["n_chromosomes"] == cat["n_chromosomes"]
        assert got["n_content"] == ret["n_content"] == cat["n_content"] == TOTAL
        assert got["path"] == str(path)


def test_genome_content_bounds_against_the_committed_digest(tmp_path):
    """genome_content derives from the STRAND, not from the head's cached scalars —
    so it inherits the rc342 read-side integrity bound for free. A head-only fast path
    would have answered cheerfully here."""
    path, _ret = _save_partitioned(tmp_path, 3)
    body = path / "turns.bin"
    raw = bytearray(body.read_bytes())
    raw[70] ^= 0x01                      # one bit, inside the first region
    body.write_bytes(bytes(raw))
    with pytest.raises(G.GenomeBoundingError):
        G.genome_content(str(path), coupling=_coupling())


# ── 3. the no-auto-partition contract ────────────────────────────────────────

def test_genome_save_does_not_auto_partition(tmp_path):
    """``save`` DERIVES boundaries from caps the caller placed; it never invents one.

    Pinned three ways: one long chromosome stays ONE (no size threshold splits it),
    twenty-four single-leaf chromosomes stay TWENTY-FOUR (nothing merges them), and the
    labels come back exactly as handed in (no renaming or reordering).
    """
    one = _coupling()
    leaves = _leaves()

    long_one = G.genome_save(G.chromosome(leaves, one, label="solo"),
                             str(tmp_path / "solo"), coupling=one)
    assert long_one["n_chromosomes"] == 1
    assert [c["label"] for c in long_one["chromosomes"]] == ["solo"]

    strand = []
    for i in range(TOTAL):
        strand += G.chromosome([leaves[i]], one, label=f"c{i}")
    many = G.genome_save(strand, str(tmp_path / "many"), coupling=one)
    assert many["n_chromosomes"] == TOTAL
    assert [c["label"] for c in many["chromosomes"]] == [f"c{i}" for i in range(TOTAL)]

    # Same content, same coupling, same leaf order — the ONLY difference is where the
    # caller put the caps. So partitioning is the caller's, and it is the only input
    # that changed the stored bytes.
    assert long_one["n_content"] == many["n_content"] == TOTAL
    assert long_one["body_sha256"] != many["body_sha256"]
