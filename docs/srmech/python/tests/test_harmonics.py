"""v0.7.0rc12 — F150 chirality-harmonic operator variants + §2.2 alignment.

Lands the RBS-LM UPSTREAM_NOTES §6 (F150) chiral A–N harmonics — per-operator
harmonic-1/2/3 classification + the harmonic-2 mirror ops (Class D/E/G) +
harmonic-3 three-cycle ops (Class I/L) + the spectral chirality classifier —
plus §2.2 greedy_bipartite_alignment. Per-class placement (no privileged
namespace, per [[feedback_no_privileged_primitive_classes]]); these live
in srmech.amsc.*.
"""
import pytest

from srmech.amsc import dispatch, naming, search, cyclic, laplacian, compose
from srmech.music import harmonics


# ── F150 operator → harmonic partition ────────────────────────────────────
def test_harmonic_partition_covers_all_14_disjoint():
    union = set(harmonics.HARMONIC_1) | set(harmonics.HARMONIC_2) | set(harmonics.HARMONIC_3)
    assert union == set("ABCDEFGHIJKLMN")
    assert len(union) == 14
    # disjoint
    assert not (set(harmonics.HARMONIC_1) & set(harmonics.HARMONIC_2))
    assert not (set(harmonics.HARMONIC_2) & set(harmonics.HARMONIC_3))
    assert not (set(harmonics.HARMONIC_1) & set(harmonics.HARMONIC_3))
    # the 5 + 6 + 3 = 14 reading
    assert (len(harmonics.HARMONIC_1), len(harmonics.HARMONIC_2),
            len(harmonics.HARMONIC_3)) == (5, 6, 3)


def test_classify_harmonic_every_letter():
    expect = {**{c: 1 for c in "ABFHN"}, **{c: 2 for c in "CDEGKM"},
              **{c: 3 for c in "IJL"}}
    for letter, order in expect.items():
        assert harmonics.classify_harmonic(letter) == order
        assert harmonics.classify_harmonic(letter.lower()) == order  # case-insensitive


def test_classify_harmonic_rejects_bad_input():
    for bad in ("", "AB", "Z", "1", 5):
        with pytest.raises((ValueError, TypeError)):
            harmonics.classify_harmonic(bad)


def test_deferred_rungs_logged():
    # CAPSTONE (rc32, F923 / §74): the ladder is now FULLY CLOSED — NO class
    # remains open. H2 (C, K) closed rc31 (F924 — Qi.arg() / Qi.modulus()); H3
    # (J) closed rc32 (Qprime — multiplicative-period). No encode blind spots.
    assert harmonics.HARMONIC_LADDER_OPEN_RUNGS == {2: (), 3: ()}


def test_harmonic_ladder_fully_closed_capstone():
    # the §74 / F923 capstone — no rung carries any open class
    # (C/K via Qi rc31, J via Qprime rc32). The empty ladder IS the capstone.
    assert all(open_classes == () for open_classes in
               harmonics.HARMONIC_LADDER_OPEN_RUNGS.values())


# ── spectral chirality classifier (§6.2) ──────────────────────────────────
def test_classify_chirality_harmonic_dc_is_h1():
    assert harmonics.classify_chirality_harmonic([1.0] * 16) == 1
    assert harmonics.classify_chirality_harmonic([3.0] * 9) == 1


def test_classify_chirality_harmonic_zero_mean_mirror_is_h2():
    # palindromic, zero-mean → mirror self-agreement dominates
    assert harmonics.classify_chirality_harmonic([1., -1, -1, 1]) == 2
    assert harmonics.classify_chirality_harmonic(
        [x - 2 / 3 for x in (2., 1, -1, -1, 1, 2)]) == 2


def test_classify_chirality_harmonic_block_repeated_three_times_is_h3():
    """rc359 (`#T1028`) — RENAMED. This was `..._three_periodic_is_h3`, and it
    passed for a reason its name got wrong: at n=9 the vector is BOTH
    period-3 AND one block of length 3 repeated three times, and it is the
    SECOND property the score measures. The differential below separates them.
    """
    v = [2., -1, -1, 2, -1, -1, 2, -1, -1]   # n=9: block [2,-1,-1] x3
    assert harmonics.classify_chirality_harmonic(v) == 3


# ── rc359 (`#T1028` + N4): what the 3-fold score ACTUALLY measures ─────────
#
# Two defects, both of the shape "a measurement surface reporting a value it
# did not measure":
#
#  1. FORCED ZERO. `three` was documented as a score. When 3 does not divide
#     n it is a closed-form function of `n mod 3` and not a function of x at
#     all — Z_n simply has no order-3 rotation to measure. The score itself is
#     CORRECT BY DESIGN and is deliberately left alone; the CONTRACT was wrong.
#  2. NOT A PERIOD-3 DETECTOR. The docstring claimed "a 3-periodic signal
#     scores high". The score rotates by n/3, so it detects THREE REPEATS OF
#     ONE BLOCK. For a genuinely period-3 vector the two coincide only when
#     9 | n — which is exactly why the pre-existing test above never caught it.

def test_three_fold_score_is_a_forced_zero_when_three_does_not_divide_n():
    """Not a measurement of x: a closed-form function of n mod 3."""
    from srmech.amsc.q import Q
    for n in (1, 2, 4, 5, 7, 8, 16, 32, 64, 127, 128):
        for trial in range(12):
            x = [((trial * 7919 + i * 104729) % 11) - 5 for i in range(n)]
            assert harmonics._spectral_scores(x)[2] == Q(0), (
                f"n={n} is not divisible by 3, so the 3-fold score must be a "
                f"forced exact zero regardless of the vector")


def test_verdict_three_is_unreachable_when_three_does_not_divide_n():
    """The reachable codomain is {1, 2}, not {1, 2, 3}.

    The 3-fold score is a forced zero, the mirror score is never negative, and
    verdict 3 needs `three > mirror`. This is not an edge case: it covers
    hdc.DEFAULT_HDC_BYTES and every Cayley-Dickson dim srmech ships.
    """
    from srmech.amsc import hdc
    assert hdc.DEFAULT_HDC_BYTES % 3 == 2, (
        "the flagship HDC width is no longer 2 mod 3 — re-derive this bound")
    for n in (8, 16, 32, 64, 128):
        assert n % 3 != 0
        for trial in range(80):
            x = [((trial * 31337 + i * 65537) % 21) - 10 for i in range(n)]
            assert harmonics.classify_chirality_harmonic(x) in (1, 2)


def test_three_fold_score_detects_block_repeats_not_period_three():
    """THE DIFFERENTIAL. Same period-3 pattern, four lengths, two verdicts.

    `[2,-1,-1]*m` is period-3 at every m. It scores 1 (verdict 3) only when
    9 | n; otherwise it scores exactly 1/2 and classifies as harmonic 2. A
    period-3 detector would return 3 for all of them.
    """
    from srmech.amsc.q import Q
    for m in range(1, 31):
        x = [2, -1, -1] * m
        n = 3 * m
        score = harmonics._spectral_scores(x)[2]
        if n % 9 == 0:
            assert score == Q(1), f"n={n}: 9|n so the block repeats exactly"
            assert harmonics.classify_chirality_harmonic(x) == 3
        else:
            assert score == Q(1, 2), f"n={n}: period-3 but NOT a 3x block repeat"
            assert harmonics.classify_chirality_harmonic(x) == 2

    # The three literal cases, spelled out: same pattern, different verdicts.
    assert harmonics.classify_chirality_harmonic([2, -1, -1] * 3) == 3   # n=9
    assert harmonics.classify_chirality_harmonic([2, -1, -1] * 4) == 2   # n=12
    # ...and at the flagship width the pattern cannot reach 3 at all.
    assert harmonics.classify_chirality_harmonic(([2, -1, -1] * 43)[:128]) == 2


def test_three_fold_score_is_one_exactly_for_a_block_repeated_three_times():
    """EXHAUSTIVE over the small-integer cubes: `three == 1` iff x is one
    block of length n/3 repeated three times (equivalently, x is invariant
    under rotation by n/3). Zero mismatches against that predicate."""
    import itertools
    from srmech.amsc.q import Q
    for n, alphabet in ((3, (-1, 0, 1, 2)), (6, (-1, 0, 1))):
        k = n // 3
        for x in itertools.product(alphabet, repeat=n):
            if all(v == 0 for v in x):
                continue                       # the all-zero guard path
            is_block_repeat = all(x[i] == x[i % k] for i in range(n))
            assert (harmonics._spectral_scores(list(x))[2] == Q(1)) \
                is is_block_repeat, f"n={n} x={x}"


def test_classify_chirality_harmonic_empty_raises():
    with pytest.raises(ValueError):
        harmonics.classify_chirality_harmonic([])


# ── harmonic-2 mirror ops (period-2 involutions) ──────────────────────────
def test_mirror_pattern_is_byte_reverse_involution():
    p = b"abcde"
    assert dispatch.mirror_pattern(p) == b"edcba"
    assert dispatch.mirror_pattern(dispatch.mirror_pattern(p)) == p
    assert dispatch.mirror_pattern(b"") == b""
    with pytest.raises(TypeError):
        dispatch.mirror_pattern("not bytes")


def test_reverse_order_is_involution():
    pairs = [(b"a", b"1"), (b"b", b"2"), (b"c", b"3")]
    assert naming.reverse_order(pairs) == [(b"c", b"3"), (b"b", b"2"), (b"a", b"1")]
    assert naming.reverse_order(naming.reverse_order(pairs)) == pairs


def test_byte_search_backward_finds_last():
    assert search.byte_search_backward(b"a-b-a-b", b"b") == 6
    assert search.byte_search_backward(b"a-b-a-b", b"a") == 4
    assert search.byte_search_backward(b"xyz", b"q") is None
    assert search.byte_search_backward(b"abc", b"") == 3  # bytes.rfind(b"")
    # the forward/backward mirror pair agree when the needle occurs once
    assert search.byte_search_backward(b"xqz", b"q") == search.byte_search(b"xqz", b"q")


# ── harmonic-3 three-cycle ops (period-3) ─────────────────────────────────
def test_three_cycle_period_3():
    assert [cyclic.three_cycle(v) for v in (0, 1, 2)] == [1, 2, 0]
    for v in (0, 1, 2):
        assert cyclic.three_cycle(cyclic.three_cycle(cyclic.three_cycle(v))) == v


def test_three_cycle_wraps_mod_3():
    # any non-negative int is read mod 3 (so generic MCP int-synth is in-domain)
    assert cyclic.three_cycle(3) == 1
    assert cyclic.three_cycle(4) == 2
    assert cyclic.three_cycle(5) == 0
    assert cyclic.three_cycle(7) == 2
    with pytest.raises(ValueError):
        cyclic.three_cycle(-1)  # negative is out of domain
    with pytest.raises(TypeError):
        cyclic.three_cycle(True)  # bool is not an accepted int here


def test_three_fold_eigvec_groups_band_split():
    n = 8
    # Path-graph adjacency + Laplacian L = D − A as plain nested lists (numpy-free).
    A = [[0.0] * n for _ in range(n)]
    for i in range(n - 1):
        A[i][i + 1] = A[i + 1][i] = 1.0
    L = [[(sum(A[i]) if i == j else 0.0) - A[i][j] for j in range(n)] for i in range(n)]
    g = laplacian.three_fold_eigvec_groups(L)
    # rc129: each band is an n×k real Mat (k = number of eigenvector COLUMNS).
    def _cols(band):
        return band.n_cols
    sizes = (_cols(g["low"]), _cols(g["mid"]), _cols(g["high"]))
    assert sum(sizes) == n
    assert sizes[0] <= sizes[1] <= sizes[2]      # remainder to later bands
    assert all(band.n_rows == n for band in g.values())  # full eigvec columns (n rows)


# ── §2.2 greedy bipartite alignment ───────────────────────────────────────
def test_greedy_bipartite_alignment_matches_and_uses_each_b_once():
    m = compose.greedy_bipartite_alignment(
        [0.0, 1.0, 2.0], [2.0, 1.0, 0.0], lambda a, b: -abs(a - b))
    assert m[0] == (2, 0.0) and m[1] == (1, 0.0) and m[2] == (0, 0.0)
    # fewer B rows → trailing A rows unmatched
    m2 = compose.greedy_bipartite_alignment([0, 1, 2], [0], lambda a, b: -abs(a - b))
    assert set(m2) == {0} and m2[0][0] == 0


def test_greedy_bipartite_alignment_rejects_non_callable():
    with pytest.raises(TypeError):
        compose.greedy_bipartite_alignment([1], [1], "not callable")
