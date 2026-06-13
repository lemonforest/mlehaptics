"""v0.7.0rc12 — F150 chirality-harmonic operator variants + §2.2 alignment.

Lands the RBS-LM UPSTREAM_NOTES §6 (F150) chiral A–N harmonics — per-operator
harmonic-1/2/3 classification + the harmonic-2 mirror ops (Class D/E/G) +
harmonic-3 three-cycle ops (Class I/L) + the spectral chirality classifier —
plus §2.2 greedy_bipartite_alignment. Per-class placement (no privileged
namespace, per [[feedback_no_privileged_primitive_classes]]); siona is a
co-name alias so these live in srmech.amsc.*.
"""
import pytest

from srmech.amsc import harmonics, dispatch, naming, search, cyclic, laplacian, compose


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
    # no-silent-caps: rc12 leaves C/K (H2) + J (H3) open; logged, not hidden.
    assert harmonics.HARMONIC_LADDER_OPEN_RUNGS == {2: ("C", "K"), 3: ("J",)}


# ── spectral chirality classifier (§6.2) ──────────────────────────────────
def test_classify_chirality_harmonic_dc_is_h1():
    assert harmonics.classify_chirality_harmonic([1.0] * 16) == 1
    assert harmonics.classify_chirality_harmonic([3.0] * 9) == 1


def test_classify_chirality_harmonic_zero_mean_mirror_is_h2():
    # palindromic, zero-mean → mirror self-agreement dominates
    assert harmonics.classify_chirality_harmonic([1., -1, -1, 1]) == 2
    assert harmonics.classify_chirality_harmonic(
        [x - 2 / 3 for x in (2., 1, -1, -1, 1, 2)]) == 2


def test_classify_chirality_harmonic_three_periodic_is_h3():
    v = [2., -1, -1, 2, -1, -1, 2, -1, -1]  # period-3, zero-mean
    assert harmonics.classify_chirality_harmonic(v) == 3


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
