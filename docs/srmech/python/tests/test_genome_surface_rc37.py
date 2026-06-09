"""v0.7.5rc37 — the genome-storage surface, brick 1 (#566 / Part 2 of #962).

Biological-structure names as cascade names: genome / chromosome / telomere /
quad-strand. This brick ships the encode CRITERION (``encode_shape``, F715) and
the helix-turn COUPLING (``quad_turn``, F713). Validates:

  * the encode criterion reproduces F715's attested table to the byte
    (200 -> tome, 800 -> mobius, 5000 -> quad_strand depth 3, 1.77M -> depth 7);
  * the criterion is pure-integer (no float in the returned depth/leaves);
  * ``quad_turn`` couples a turn through the_one by the REVERSIBLE Klein-4 bind
    (quad_turn(quad_turn(t, one), one) == t — the duality held without collapse).
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome
from srmech.amsc.hdc import klein4_random


# ── encode_shape — the criterion (F715) ──────────────────────────────────────

def test_constants_attested_to_256_and_klein4_order():
    assert genome.LEAF_CAP == 256          # 2**8 (F708/F640)
    assert genome.QUAD == 4                 # Klein-4 order Z2 x Z2
    assert genome.MOBIUS_CAP == 1024        # 4 x 256 — one quad-turn


@pytest.mark.parametrize(
    "n, shape, depth",
    [
        (1, "tome", 0),
        (200, "tome", 0),            # F715 verified
        (256, "tome", 0),            # exact leaf cap
        (257, "mobius", 1),          # just over one leaf
        (800, "mobius", 1),          # F715 verified
        (1024, "mobius", 1),         # exact mobius cap (4 leaves)
        (1025, "quad_strand", 2),    # just over the biaxial shelf
        (5000, "quad_strand", 3),    # F715 verified (depth 3)
        (1_770_000, "quad_strand", 7),  # F715 verified (depth 7)
    ],
)
def test_encode_shape_matches_f715_table(n, shape, depth):
    r = genome.encode_shape(n)
    assert r["shape"] == shape, (n, r)
    assert r["depth"] == depth, (n, r)
    assert r["n"] == n
    assert r["leaf_cap"] == 256


def test_encode_shape_leaves_is_ceil_div():
    assert genome.encode_shape(256)["leaves"] == 1
    assert genome.encode_shape(257)["leaves"] == 2
    assert genome.encode_shape(5000)["leaves"] == (5000 + 255) // 256  # 20


def test_encode_shape_is_pure_integer():
    r = genome.encode_shape(5000)
    # no float anywhere in the decision (Class I/N; "floats are for the FPU lift")
    for k in ("n", "leaves", "depth", "leaf_cap"):
        assert isinstance(r[k], int) and not isinstance(r[k], bool), (k, r[k])


@pytest.mark.parametrize("bad", [0, -1, -256, 1.5, "5", None])
def test_encode_shape_rejects_non_positive_int(bad):
    with pytest.raises((ValueError, TypeError)):
        genome.encode_shape(bad)


def test_depth_monotone_nondecreasing_in_n():
    prev = -1
    for n in (1, 256, 257, 1024, 1025, 4096, 5000, 100_000, 1_770_000):
        d = genome.encode_shape(n)["depth"]
        assert d >= prev, (n, d, prev)
        prev = d


# ── quad_turn — the reversible the_one coupling (F713) ────────────────────────

def test_quad_turn_is_reversible_through_the_one():
    t = klein4_random(64, seed=1)
    one = klein4_random(64, seed=99)
    coupled = genome.quad_turn(t, one)
    recovered = genome.quad_turn(coupled, one)        # re-bind the_one
    assert list(recovered) == list(t)                 # bind o bind == identity
    assert list(coupled) != list(t)                   # it actually coupled


def test_the_one_is_the_shared_invariant_across_turns():
    one = klein4_random(64, seed=7)
    turns = [klein4_random(64, seed=s) for s in range(5)]
    # every turn recovers exactly by re-binding the SAME the_one
    for t in turns:
        assert list(genome.quad_turn(genome.quad_turn(t, one), one)) == list(t)


def test_quad_turn_distinct_one_gives_distinct_coupling():
    t = klein4_random(64, seed=3)
    one_a = klein4_random(64, seed=10)
    one_b = klein4_random(64, seed=11)
    assert list(genome.quad_turn(t, one_a)) != list(genome.quad_turn(t, one_b))


# ── brick 2 (rc38): telomere / chromosome / recall ───────────────────────────

def test_telomere_is_deterministic_per_label():
    assert list(genome.telomere("astronomy", dim=64)) == list(genome.telomere("astronomy", dim=64))


def test_telomere_distinct_labels_distinct_caps():
    assert list(genome.telomere("astronomy", dim=64)) != list(genome.telomere("geography", dim=64))


def test_chromosome_is_telomere_capped_strand():
    one = klein4_random(64, seed=7)
    leaves = [klein4_random(64, seed=s) for s in range(5)]
    strand = genome.chromosome(leaves, one, label="astronomy")
    assert len(strand) == len(leaves) + 1                  # one cap + N coupled turns
    assert list(strand[0]) == list(genome.telomere("astronomy", dim=64))   # leading cap


def test_recall_round_trips_the_kernel():
    one = klein4_random(64, seed=7)
    leaves = [klein4_random(64, seed=s) for s in range(5)]
    strand = genome.chromosome(leaves, one, label="astronomy")
    cap = genome.telomere("astronomy", dim=64)
    recovered = genome.recall(strand, one, cap)
    assert [list(x) for x in recovered] == [list(l) for l in leaves]   # exact inverse


def test_recall_skips_the_cap_by_value_not_position():
    # a cap appearing anywhere (the multi-chromosome genome shape) is skipped
    one = klein4_random(64, seed=2)
    cap = genome.telomere("k", dim=64)
    leaf = klein4_random(64, seed=9)
    strand = [genome.quad_turn(leaf, one), cap, genome.quad_turn(leaf, one)]
    recovered = genome.recall(strand, one, cap)
    assert len(recovered) == 2 and all(list(x) == list(leaf) for x in recovered)


# ── brick 3 (rc42): genome (multi-kernel) + partition ────────────────────────

def _kernels(one):
    return {
        "astronomy": [klein4_random(64, seed=s) for s in range(3)],
        "geography": [klein4_random(64, seed=s) for s in (10, 11)],
        "music": [klein4_random(64, seed=20)],
    }


def test_genome_is_concatenated_telomere_capped_chromosomes():
    one = klein4_random(64, seed=7)
    k = _kernels(one)
    strand = genome.genome(k, one)
    # 3 caps + (3+2+1) coupled turns
    assert len(strand) == 3 + (3 + 2 + 1)
    # the three telomere caps appear in the strand, in declared order
    caps = [list(genome.telomere(lbl, dim=64)) for lbl in k]
    positions = [i for i, hv in enumerate(strand) if list(hv) in caps]
    assert positions == [0, 4, 7]              # astronomy@0, geography@4 (cap+3), music@7 (+2)


def test_partition_round_trips_every_kernel():
    one = klein4_random(64, seed=7)
    k = _kernels(one)
    strand = genome.genome(k, one)
    back = genome.partition(strand, one, list(k))
    assert set(back) == set(k)
    for label, leaves in k.items():
        assert [list(x) for x in back[label]] == [list(l) for l in leaves]


def test_genome_accepts_pair_sequence_form():
    one = klein4_random(64, seed=3)
    A = [klein4_random(64, seed=1)]
    assert [list(x) for x in genome.genome([("k", A)], one)] \
        == [list(x) for x in genome.genome({"k": A}, one)]


def test_genome_seed_class_assemble_and_partition():
    # the Genome CatalogClass now drives the multi-kernel genome end-to-end
    from srmech.dsl import make_class
    one = klein4_random(64, seed=7)
    g = make_class("Genome")(the_one=one)
    k = _kernels(one)
    strand = g.assemble(kernels=k)                 # binds the_one from the field
    back = g.partition(strand=strand, labels=list(k))
    for label, leaves in k.items():
        assert [list(x) for x in back[label]] == [list(l) for l in leaves]
