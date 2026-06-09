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
