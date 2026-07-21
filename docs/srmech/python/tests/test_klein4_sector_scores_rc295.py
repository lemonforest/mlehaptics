"""rc295 (§102 / F1265) — the NON-COLLAPSING read of the §50 accumulator.

``klein4_bundle_accumulate`` (write) and ``klein4_bundle_resolve`` (collapsing
read) were the whole accumulator family. ``_resolve`` emits one symbol per
coordinate — a strict per-bit majority — and throws the margins away, so a
coordinate a sector won 5/9 and one it won 9/9 resolve identically. There was
no soft read. ``klein4_bundle_sector_scores`` is it.

**Why this and not the 4xD joint.** Task ``#929`` (commit f5cceb635, harness at
``docs/srmech/notes/task929_klein4_joint_vs_marginal.py``) measured the arm
F1263 never ran. F1263 reported ~11x recall@1 from a joint count table at
N=1200/D=4096; at 400 probes that is **7.46x**, and the 11x rested on the
baseline scoring 1 hit in 25. Reading the ALREADY-SHIPPED ``1 + 2*D``
accumulator softly gets **4.25x of the 7.46x** with no storage change and no
rebuild of anything already written — and ``joint_hard`` is consistently WORSE
than ``marginal_soft`` (0.6075 vs 0.8000 at N=512). **The information loss is
in the READ, not the STORAGE.** So the read ships first; the joint gets priced
against what is left.

The lift is **dimension-specific** — never quote one scalar. See
``test_lift_is_dimension_specific``.
"""

from array import array
from operator import add

import pytest

from srmech.amsc import _native, hdc


# --------------------------------------------------------------- helpers

def _fold(vectors):
    """The shipped streaming write, so every test rides the real accumulator."""
    acc = None
    for v in vectors:
        acc = hdc.klein4_bundle_accumulate(acc, v)
    return acc


def _corpus(dim, n, base=777_000):
    return [hdc.klein4_expand(dim, seed=base + i) for i in range(n)]


def _brute_marginals(vectors, dim, i):
    """(n, c0, c1) recomputed from the vectors — never read off the docstring."""
    n = len(vectors)
    c0 = sum(1 for v in vectors if (v[i] & 1) == 1)
    c1 = sum(1 for v in vectors if ((v[i] >> 1) & 1) == 1)
    return n, c0, c1


def _pure(acc):
    """Force the pure-Python alternative regardless of what is loaded."""
    saved = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    try:
        return hdc.klein4_bundle_sector_scores(acc)
    finally:
        _native.HAS_NATIVE = saved


# ------------------------------------------------------------- the shape

def test_returns_four_uint64_scores_per_coordinate():
    dim = 64
    acc = _fold(_corpus(dim, 9))
    out = hdc.klein4_bundle_sector_scores(acc)

    assert isinstance(out, array)
    # 'Q' here is the stdlib uint64 TYPECODE, not srmech's exact-rational Q
    # carrier — see test_array_typecode_is_not_read_as_the_Q_carrier.
    assert out.typecode == "Q"
    assert out.itemsize == 8
    assert len(out) == 4 * dim, (
        "the whole point is FOUR scores per coordinate; a 1*D result would be "
        "the collapsed read this op exists to replace"
    )


def test_scores_are_the_marginal_agreement_product():
    """Ground truth recomputed from the vectors, not from the accumulator."""
    dim, n_vecs = 64, 9
    vecs = _corpus(dim, n_vecs)
    out = hdc.klein4_bundle_sector_scores(_fold(vecs))

    for i in range(dim):
        n, c0, c1 = _brute_marginals(vecs, dim, i)
        for s in range(4):
            a0 = c0 if (s & 1) else n - c0
            a1 = c1 if ((s >> 1) & 1) else n - c1
            assert out[4 * i + s] == a0 * a1, (
                f"coord {i} sector {s}: expected {a0 * a1}, got {out[4 * i + s]}"
            )


def test_sector_bit_encoding_is_bit0_low_bit1_high():
    """s in {0,1,2,3} with bit0 = s & 1 and bit1 = (s >> 1) & 1 — the SAME
    encoding klein4 uses everywhere, so a caller can index by an unbind XOR."""
    dim = 32
    # A corpus where every vector carries one symbol makes the encoding readable
    # straight off the numbers: only the matching sector can score.
    for sym in range(4):
        vecs = [hdc.HV(array("B", bytes([sym]) * dim), sectors=4) for _ in range(5)]
        out = hdc.klein4_bundle_sector_scores(_fold(vecs))
        for i in range(dim):
            row = [out[4 * i + s] for s in range(4)]
            assert row[sym] == 25, f"sym {sym} coord {i}: {row}"
            assert sum(row) == 25, f"only sector {sym} may score: {row}"


# ------------------------------------------- the relation to the hard read

def test_argmax_of_the_soft_read_reproduces_resolve_exactly():
    """The load-bearing invariant: this REFINES the hard read, it does not
    replace it with a different quantity. The agreement product factorises as
    a0(bit0) * a1(bit1), so maximising it maximises each bit independently —
    which is exactly ``klein4_bundle_resolve``'s strict per-bit majority,
    including its tie -> 0 convention. Collapse the margins and the shipped
    bundle comes back, bit for bit.
    """
    dim = 96
    for n_vecs in (1, 2, 5, 8, 9, 16, 17):
        vecs = _corpus(dim, n_vecs, base=910_000)
        acc = _fold(vecs)
        resolved = hdc.klein4_bundle_resolve(acc)
        out = hdc.klein4_bundle_sector_scores(acc)

        for i in range(dim):
            best_s, best_v = 0, out[4 * i]
            for s in (1, 2, 3):
                if out[4 * i + s] > best_v:   # STRICTLY greater: tie -> lower s
                    best_v, best_s = out[4 * i + s], s
            assert best_s == resolved[i], (
                f"n={n_vecs} coord {i}: argmax {best_s} != resolve {resolved[i]}"
            )


def test_soft_read_separates_accumulators_the_hard_read_cannot():
    """Two accumulators that RESOLVE identically but are not equally confident.
    If this ever passes trivially, the op has stopped being a soft read."""
    dim = 8
    # Both: bit1 unanimous (9/9). narrow's bit0 wins 5/9, wide's wins 9/9.
    narrow = array("I", [9] + [5] * dim + [9] * dim)
    wide = array("I", [9] + [9] * dim + [9] * dim)

    assert list(hdc.klein4_bundle_resolve(narrow)) == \
        list(hdc.klein4_bundle_resolve(wide)), \
        "premise: the COLLAPSED read cannot tell these apart"

    n_scores = hdc.klein4_bundle_sector_scores(narrow)
    w_scores = hdc.klein4_bundle_sector_scores(wide)
    assert list(n_scores) != list(w_scores), \
        "the whole point: the NON-COLLAPSING read can"

    for i in range(dim):
        # narrow: e0=4, e1=0 -> [0, 0, 4*9, 5*9] = [0, 0, 36, 45]
        assert [n_scores[4 * i + s] for s in range(4)] == [0, 0, 36, 45]
        # wide:   e0=0, e1=0 -> [0, 0, 0, 81]
        assert [w_scores[4 * i + s] for s in range(4)] == [0, 0, 0, 81]
        # The winning sector is 3 in both; only the MARGIN over the runner-up
        # distinguishes them, and that margin is exactly what _resolve drops.
        assert n_scores[4 * i + 3] - n_scores[4 * i + 2] == 9
        assert w_scores[4 * i + 3] - w_scores[4 * i + 2] == 81


# ------------------------------------------------------- multi-implementation

def test_native_and_pure_paths_are_bit_identical():
    """Co-equal coherency projections, not a fast path and a fallback."""
    dim = 128
    for n_vecs in (1, 3, 9, 32):
        acc = _fold(_corpus(dim, n_vecs, base=555_000))
        assert list(hdc.klein4_bundle_sector_scores(acc)) == list(_pure(acc))


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_c_peer_is_present_and_reachable():
    """A symbol in the header that no glue can reach is not a C peer."""
    assert hasattr(_native.LIB, "srmech_klein4_bundle_sector_scores")
    dim = 16
    acc = _fold(_corpus(dim, 7, base=333_000))
    # Round-trip through the real ctypes glue, not just a hasattr.
    assert len(hdc.klein4_bundle_sector_scores(acc)) == 4 * dim


def test_uint64_headroom_beyond_uint32():
    """uint32 would silently wrap past n = 65535 folded vectors, and the
    accumulator carries no such cap. Synthesised directly because folding
    100k vectors in a unit test is not the point being tested."""
    dim = 2
    n = 100_000
    acc = array("I", [n] + [n] * dim + [n] * dim)
    out = hdc.klein4_bundle_sector_scores(acc)
    expected = n * n                                  # 10**10
    assert expected > 2 ** 32, "the test must actually exceed uint32"
    for i in range(dim):
        assert out[4 * i + 3] == expected
    assert list(out) == list(_pure(acc)), "both projections must carry it"


# ------------------------------------------------------------ the failures

def test_malformed_accumulator_raises_rather_than_wrapping():
    """A 1-count exceeding n is a corrupt store. Unsigned subtraction would
    wrap it into an enormous plausible-looking score."""
    dim = 4
    bad = array("I", [3] + [99] * dim + [1] * dim)    # c0 = 99 > n = 3
    with pytest.raises(ValueError):
        hdc.klein4_bundle_sector_scores(bad)
    with pytest.raises(ValueError):
        _pure(bad)


@pytest.mark.parametrize("bad", [None, array("I", []), array("I", [1, 2]),
                                 array("I", [1, 2, 3, 4])])
def test_non_accumulator_shapes_raise(bad):
    """Width must be 1 + 2*D — an even length is not an accumulator."""
    with pytest.raises(ValueError):
        hdc.klein4_bundle_sector_scores(bad)


def test_empty_accumulator_scores_zero_everywhere():
    """n = 0 -> every agreement count is 0, so every sector scores 0. Consistent
    with _resolve's all-zero vector: nothing is known, and it says so."""
    dim = 8
    acc = array("I", bytes(4 * (1 + 2 * dim)))
    out = hdc.klein4_bundle_sector_scores(acc)
    assert list(out) == [0] * (4 * dim)
    assert list(hdc.klein4_bundle_resolve(acc)) == [0] * dim


# --------------------------------------------------------------- the lift

def _recall_at_1(dim, n, probes, table_for_coord):
    """Task #929's protocol, verbatim in shape: score every stored value
    against a key-bound probe and count argmax hits."""
    keys = [hdc.klein4_expand(dim, seed=10_000 + i) for i in range(n)]
    vals = [hdc.klein4_expand(dim, seed=20_000 + i) for i in range(n)]
    cols = [bytes(vals[j][i] for j in range(n)) for i in range(dim)]
    step = max(1, n // probes)
    idx = list(range(0, n, step))[:probes]

    hits = 0
    for j in idx:
        key = keys[j]
        scores = [0] * n
        for i in range(dim):
            ti = table_for_coord(i)
            k = key[i]
            ui = (ti[k], ti[k ^ 1], ti[k ^ 2], ti[k ^ 3])
            scores = list(map(add, scores, map(ui.__getitem__, cols[i])))
        best_j, best_s = 0, scores[0]
        for jj in range(1, n):
            if scores[jj] > best_s:
                best_s, best_j = scores[jj], jj
        if best_j == j:
            hits += 1
    return hits, len(idx)


def _both_reads(dim, n, probes):
    keys = [hdc.klein4_expand(dim, seed=10_000 + i) for i in range(n)]
    vals = [hdc.klein4_expand(dim, seed=20_000 + i) for i in range(n)]
    acc = _fold([hdc.klein4_bind(keys[i], vals[i]) for i in range(n)])
    bundle = hdc.klein4_bundle_resolve(acc)
    tbl = hdc.klein4_bundle_sector_scores(acc)

    hard, n_probes = _recall_at_1(
        dim, n, probes,
        lambda i: [1 if s == bundle[i] else 0 for s in range(4)])
    soft, _ = _recall_at_1(dim, n, probes, lambda i: tbl[4 * i:4 * i + 4])
    return hard, soft, n_probes


def test_soft_read_beats_the_collapsed_read_at_load():
    """The measured claim, end to end, on whatever path is loaded. Seeded, so
    this is a fixed number and not a coin flip."""
    hard, soft, n_probes = _both_reads(dim=256, n=64, probes=48)
    assert n_probes == 48
    # Measured 22/48 vs 38/48 at these seeds. Asserted as a gap, not as the
    # exact pair, so a future klein4_expand stream change fails loudly on the
    # CLAIM rather than on an incidental hit count.
    assert hard < soft, f"hard={hard}/{n_probes} soft={soft}/{n_probes}"
    assert soft - hard >= 8, (
        f"the lift collapsed: hard={hard}/{n_probes} soft={soft}/{n_probes}"
    )


def test_lift_is_dimension_specific():
    """F1264 (PR #687) and the #929 D=1024 sweep both say the numbers are
    dimension-specific; #929 measured 100/74/50% capture at D=4096 against
    100/61/38/48% at D=1024. So the op must never be sold with one scalar —
    this pins that the SAME load lands differently at two dimensions."""
    hard_a, soft_a, _ = _both_reads(dim=128, n=64, probes=32)
    hard_b, soft_b, _ = _both_reads(dim=512, n=64, probes=32)

    assert hard_a <= soft_a and hard_b <= soft_b
    # Same N, different D -> different absolute recall. If these ever coincide,
    # the "dimension-specific" claim in the docstring needs re-measuring.
    assert (hard_a, soft_a) != (hard_b, soft_b), (
        f"D=128 {hard_a}/{soft_a} vs D=512 {hard_b}/{soft_b} — the "
        "dimension-specificity claim no longer reproduces"
    )


# ------------------------------------------------------------ registration

def test_registered_in_the_tool_schema():
    from srmech.amsc.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.hdc.klein4_bundle_sector_scores" in names


def test_name_does_not_say_resolve():
    """Regime honesty (F1259): the name must let a reader at the call site tell
    which regime they are in. This op does NOT resolve or collapse, so reusing
    'resolve' would describe an intent the behaviour contradicts."""
    assert "resolve" not in "klein4_bundle_sector_scores"
    assert hasattr(hdc, "klein4_bundle_sector_scores")
    assert "klein4_bundle_sector_scores" in hdc.__all__


def test_array_typecode_is_not_read_as_the_Q_carrier():
    """rc295 regression. The carrier scan matches carrier names with
    identifier-boundary lookarounds, and a quote is a boundary — so the uint64
    typecode in ``array('Q')`` matched srmech's exact-rational **Q** carrier and
    filed this op under ``Q.produces``. It produces no Q. Latent before rc295
    only because no registered ToolEntry type carried ``array('Q')``.
    """
    from srmech.amsc.carrier_schema import carrier_schema

    produces = carrier_schema()["Q"]["ops"]["produces"]
    assert "srmech.amsc.hdc.klein4_bundle_sector_scores" not in produces, \
        "array('Q') is a stdlib uint64 typecode, not the exact-rational Q carrier"
    # The guard must be specific, not a blanket empty list.
    assert "srmech.amsc.hdc.klein4_similarity" in produces, \
        "ops that really do produce Q must still be listed"
