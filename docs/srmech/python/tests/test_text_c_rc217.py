"""rc217 (gh #1360) + rc287 — BYTE-IDENTICAL C peers for `srmech.math.text`.

The §40/§52 text→graph ingestion ops shipped rc50/§52 as pure-Python kernels
with NO C peer — the enwiki comprehended-encode's dominant cost ran in Python
even on a native wheel. rc217 gave each a byte-identical C peer and fixed
their Rosetta mis-classification (non_compute/composes_c → c_dispatched — the
self-contained-kernel hiding spot; see COMPOSES_C_ZERO_REACH_PINNED in
test_rosetta_completeness.py).

**rc287 replaced the segmentation op.** `srmech_text_tokenize` is gone and
`srmech_text_glyph_stream` (+ `srmech_text_default_gb_table`) takes its place,
because the unit is now the UAX #29 grapheme cluster rather than the word.
The Unicode battery below was REWRITTEN rather than deleted: every case is
kept and re-pointed at `glyph_stream`, plus the cases that only exist because
the word decision existed (casefold expansions, ligature folds, apostrophe
trimming) are retained as *inputs* — they still have to segment identically in
both projections, they simply no longer fold or drop anything. Several cases
that the old suite pinned as correct were pinning bugs; those are called out
individually where they appear.

The parity contract is unchanged and is the point of this file: BYTE-IDENTICAL
equality of the whole result (cluster stream / integer counts / tie-breaks /
edge order), with the pure body as the oracle, exercised by forcing every
`has_native_text_*` gate off. On a no-C host both sides run the pure body and
the assertions still hold (the suite stays green with no native lib, per the
§17 discipline).

Numpy-free.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import _unicode_gb_tables as gbt
from srmech.math import text as T


# ──────────────────────────────────────────────────────────────────────
# forced-pure helpers (the oracle side of every parity assert)
# ──────────────────────────────────────────────────────────────────────

def _pure_glyph_stream(monkeypatch, *a, **kw):
    with monkeypatch.context() as m:
        m.setattr(_native, "has_native_text_glyph_stream", lambda: False)
        return T.glyph_stream(*a, **kw)


def _pure_edges(monkeypatch, *a, **kw):
    with monkeypatch.context() as m:
        m.setattr(_native, "has_native_text_cooccurrence_edges", lambda: False)
        return T.cooccurrence_edges(*a, **kw)


def _pure_topk(monkeypatch, *a, **kw):
    with monkeypatch.context() as m:
        m.setattr(_native, "has_native_text_cooccurrence_topk", lambda: False)
        return T.cooccurrence_topk(*a, **kw)


# ──────────────────────────────────────────────────────────────────────
# glyph_stream — Unicode battery (byte-identical native == pure)
# ──────────────────────────────────────────────────────────────────────

_GLYPH_CASES = [
    # plain English (the old suite also exercised the default stoplist here —
    # there is no stoplist now, so the whole string must survive)
    "Hello, world! The quick brown fox jumps over the lazy dog.",
    # Latin accents / Cyrillic / CJK (the F698 lesson — no ASCII \\w+)
    "café naïve Москва 日本語 straße test",
    # apostrophes: the old path mapped curly → ASCII and trimmed them, which
    # DELETED the Hawaiian okina when U+2019 stood in for U+02BB. Kept as a
    # segmentation battery; nothing is trimmed or rewritten now.
    "don't stop 'quoted' galaxy's rock'n'roll '' ' a''b",
    "’leading curly’ trailing’ mid’dle",
    # cases that existed for casefold expansion (ß→ss, İ → i + combining dot).
    # No folding now, but they remain excellent segmentation inputs: İ carries
    # a combining dot, and the Greek is a real accent/case battery.
    "ß ẞ İstanbul DİYARBAKIR ΣΊΣΥΦΟΣ ὈΔΥΣΣΕΎΣ",
    # ligature + titlecase digraphs (single codepoints -> single clusters)
    "ﬁre ﬂow oﬃce Ǆungla ǅ ǆ ǳ Ǳ",
    # combining marks ride their base (GB9)
    "étude combininǵ marks͂ café",
    # separators / punctuation / digits are clusters in their own right; the
    # old path dropped all of them AND any single letter (_MIN_LEN).
    "ab-cd ef_gh 123 x9y a1 ..́..",
    "tabs\tand\nnewlines\r\nmixed  spaces",
    # empties / minimal
    "", "a", "xy", "''", "’’",
    # rc287 additions — the clusters the old path could not represent at all
    "\U0001F468‍\U0001F469‍\U0001F467‍\U0001F466",   # GB11 family ZWJ
    "\U0001F1FB\U0001F1FA\U0001F1F3\U0001F1FF",     # GB12/13 flag pair
    "1️⃣2️⃣",                                        # keycaps
    "क्षि क्त",                                       # GB9c conjuncts
    "한국어 ᄀᅠ",                                      # Hangul + jamo filler
    "中 国",                                          # single-codepoint CJK
]


@pytest.mark.parametrize("case", _GLYPH_CASES)
def test_glyph_stream_native_equals_pure(monkeypatch, case):
    for kw in ({}, {"unicode_normalize": False}):
        assert (T.glyph_stream(case, **kw)
                == _pure_glyph_stream(monkeypatch, case, **kw))


@pytest.mark.parametrize("case", _GLYPH_CASES)
def test_glyph_stream_is_lossless(monkeypatch, case):
    """No codepoint may be dropped. The old path silently deleted the okina,
    single-codepoint CJK, digits, punctuation and every emoji."""
    for kw in ({}, {"unicode_normalize": False}):
        assert "".join(T.glyph_stream(case, **kw)) == (
            unicodedata.normalize("NFC", case) if kw.get(
                "unicode_normalize", True) else case)


def test_glyph_stream_nfd_input_normalises_identically(monkeypatch):
    nfd = unicodedata.normalize("NFD", "café naïve étude")
    assert T.glyph_stream(nfd) == _pure_glyph_stream(monkeypatch, nfd)
    assert T.glyph_stream(nfd) == T.glyph_stream("café naïve étude")
    # ...and with normalisation OFF the base+mark pairs are STILL one cluster
    # each (GB9), which is the break rule rather than the normaliser.
    assert len(T.glyph_stream(nfd, unicode_normalize=False)) == len(
        "café naïve étude")


def test_glyph_stream_known_values():
    """Pinned semantics, not just parity.

    The rc217 version of this test pinned three behaviours that rc287 found to
    be defects, so the assertions are inverted here and each says why:

    * ``tokenize("The Weiße Rose didn’t stop") == ["weisse","rose","didn't","stop"]``
      — casefold split Turkish vocabularies and could not repair Greek
      uppercase accent loss; the curly→ASCII rewrite deleted the okina.
    * ``tokenize("ß alone") == ["ss","alone"]`` — a fold, not a segmentation.
    * ``tokenize("a b c") == []`` — ``_MIN_LEN`` deleted content words, which
      erased single-codepoint CJK entirely.
    """
    assert T.glyph_stream("The Weiße Rose didn’t stop") == list(
        "The Weiße Rose didn’t stop")
    assert T.glyph_stream("ß alone") == list("ß alone")     # no fold to "ss"
    assert T.glyph_stream("a b c") == list("a b c")         # nothing dropped
    assert T.glyph_stream("中 国") == ["中", " ", "国"]


def test_break_table_is_loaded_and_handed_to_c_intact():
    """Replaces ``test_tokenize_fold_outputs_carry_no_apostrophe``.

    That test guarded a real invariant of the retired tokenizer — no casefold
    output may contain an apostrophe, because the C peer trimmed AFTER folding
    while the pure body trimmed BEFORE, so a folding apostrophe would have made
    the two projections disagree. rc287 removed both the fold and the trim, so
    the invariant has no consumer left and asserting it would be theatre.

    The structural counterpart is kept instead: the table both projections hand
    to C must decode to the same shape the vendored blob declares, and the
    ctypes view handed across the FFI must be that table and not a copy that
    drifted. This is the same class of guard (the tables exist, are non-trivial,
    and cross the boundary intact) pointed at the object that now matters.
    """
    lo, hi, prop = T._gb_table()
    assert len(lo) == len(hi) == len(prop) == gbt.GB_RANGE_COUNT
    assert gbt.GB_RANGE_COUNT > 0

    lo_c, hi_c, prop_c, n_ranges = T._gb_table_ctypes()
    assert n_ranges == gbt.GB_RANGE_COUNT
    assert list(lo_c) == list(lo)
    assert list(hi_c) == list(hi)
    assert bytes(bytearray(prop_c)) == prop

    # The two properties that cannot be derived from ANY host interpreter must
    # actually be present -- their silent absence would degrade emoji and Indic
    # while leaving every Latin assertion in this file green.
    assert any(p & gbt.PROP_EXTPICT_BIT for p in prop)
    assert any((p & gbt.PROP_INCB_MASK) for p in prop)


# ──────────────────────────────────────────────────────────────────────
# cooccurrence_edges — window / vocab / boundary battery
# ──────────────────────────────────────────────────────────────────────

_EDGE_DOCS = [
    [["a", "b", "c", "a", "b"], ["b", "c", "d"], [], ["x"]],
    ["flat", "tokens", "one", "doc", "flat", "tokens"],   # flat = one document
    [["w%d" % (i % 37) for i in range(500)], ["w%d" % (i % 11) for i in range(200)]],
    [],
    [["solo"]],
    [["r", "r", "r", "r"]],                               # self-pairs skipped
]


@pytest.mark.parametrize("docs_i", range(len(_EDGE_DOCS)))
def test_cooccurrence_edges_native_equals_pure(monkeypatch, docs_i):
    docs = _EDGE_DOCS[docs_i]
    for kw in ({}, {"window": 1}, {"window": 5}, {"window": 1000},
               {"vocab": ["a", "b", "c", "w1", "w2"]}, {"vocab_size": 3}):
        a = T.cooccurrence_edges([list(d) if not isinstance(d, str) else d for d in docs], **kw)
        b = _pure_edges(monkeypatch, [list(d) if not isinstance(d, str) else d for d in docs], **kw)
        assert a == b


def test_cooccurrence_edges_doc_boundary_reset(monkeypatch):
    # the pair (a, b) must NOT be counted across the document boundary
    one = T.cooccurrence_edges([["a", "b"], ["b", "a"]], window=5)
    two = T.cooccurrence_edges([["a", "b", "b", "a"]], window=5)
    assert one != two                                    # boundary is load-bearing
    assert one == _pure_edges(monkeypatch, [["a", "b"], ["b", "a"]], window=5)


def test_cooccurrence_edges_triple_matches_dense_laplacian_contract():
    n, edges, weights = T.cooccurrence_edges([["a", "b", "c", "a"]], window=2)
    assert n == 3
    assert all(isinstance(e, tuple) and len(e) == 2 and e[0] < e[1] for e in edges)
    assert edges == sorted(edges)                        # lexicographic order
    assert all(isinstance(w, int) and w >= 1 for w in weights)


# ──────────────────────────────────────────────────────────────────────
# cooccurrence_topk — streaming / truncation / tie-break battery
# ──────────────────────────────────────────────────────────────────────

_TOPK_CASES = [
    ([["a", "b", "c", "a", "b"], ["b", "c", "d"]], {}),
    (["flat", "tokens", "one", "doc"], {}),
    # heavy truncation + tiny chunks (the parity-load-bearing flush cadence)
    ([["t%d" % (i * 7 % 20) for i in range(80)] for _ in range(30)],
     {"k": 2, "cap_slack": 1, "chunk_docs": 4}),
    ([["t%d" % (i % 8) for i in range(50)] for _ in range(50)],
     {"k": 1, "cap_slack": 1, "chunk_docs": 3, "window": 3}),
    # ties: equal weights rank by smaller neighbour index first
    ([["m", "x", "m", "y", "m", "z"]], {"k": 2, "cap_slack": 1}),
    ([], {}),
    ([[]], {}),
    ([["x"]], {}),
    ([["a", "b"], [3, None, "c", "d"]], {}),             # non-str tokens skipped
    ([["a", "b", "c"]], {"vocab": ["c", "a", "zz"]}),    # fixed vocab, OOV skipped
]


@pytest.mark.parametrize("case_i", range(len(_TOPK_CASES)))
def test_cooccurrence_topk_native_equals_pure(monkeypatch, case_i):
    docs, kw = _TOPK_CASES[case_i]
    a = T.cooccurrence_topk([list(d) if not isinstance(d, str) else d for d in docs], **kw)
    b = _pure_topk(monkeypatch, [list(d) if not isinstance(d, str) else d for d in docs], **kw)
    assert a == b


def test_cooccurrence_topk_stream_is_single_pass(monkeypatch):
    # a generator stream (never all resident) — both paths consume it once
    def gen():
        for i in range(40):
            yield ["g%d" % (i % 9), "g%d" % ((i + 1) % 9), "g%d" % ((i + 2) % 9)]
    a = T.cooccurrence_topk(gen(), k=2, cap_slack=1, chunk_docs=5)
    b = _pure_topk(monkeypatch, gen(), k=2, cap_slack=1, chunk_docs=5)
    assert a == b
    assert a["n"] == 9 and a["vocab"][0] == "g0"          # first-appearance ids


def test_cooccurrence_topk_first_seen_edge_weight(monkeypatch):
    """After truncation the two endpoints' stores can carry DIVERGENT weights
    for one pair; the edge takes the FIRST-SEEN one (u ascending, rank order
    within u) — the exact pure `seen`-set rule, locked under a cap that forces
    divergence across chunks."""
    docs = []
    for rep in range(6):
        docs.append(["hub"] + ["sat%d" % (rep % 4)] * 3)
        docs.append(["sat%d" % (rep % 4), "hub", "sat%d" % ((rep + 1) % 4)])
    kw = {"k": 1, "cap_slack": 1, "chunk_docs": 2, "window": 2}
    assert T.cooccurrence_topk([list(d) for d in docs], **kw) == \
        _pure_topk(monkeypatch, [list(d) for d in docs], **kw)


def test_cooccurrence_topk_chunk_cadence_parity(monkeypatch):
    """Truncation happens per flush, so the chunk_docs cadence is part of the
    result — parity must hold at EVERY cadence, including chunk_docs=1."""
    docs = [["c%d" % (i % 6), "c%d" % ((i + 1) % 6), "c%d" % ((i + 3) % 6)]
            for i in range(25)]
    for cd in (1, 2, 5, 2048):
        kw = {"k": 2, "cap_slack": 1, "chunk_docs": cd}
        assert T.cooccurrence_topk([list(d) for d in docs], **kw) == \
            _pure_topk(monkeypatch, [list(d) for d in docs], **kw)


# ──────────────────────────────────────────────────────────────────────
# registration + ledger rows (the rc217 mis-classification fix)
# ──────────────────────────────────────────────────────────────────────

_LEDGER = Path(__file__).resolve().parent / "rosetta_classification.ndjson"


def test_rosetta_rows_are_c_dispatched():
    rows = {json.loads(l)["defined_at"]: json.loads(l)
            for l in _LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()}
    for op in ("glyph_stream", "cooccurrence_edges", "cooccurrence_topk"):
        row = rows[f"srmech.math.text.{op}"]
        assert row["bucket"] == "c_dispatched", row
        assert "non_compute_kind" not in row, row


def test_native_gates_bound_on_a_native_host():
    if not _native.HAS_NATIVE:
        pytest.skip("no native lib — pure-only host")
    assert _native.has_native_text_glyph_stream()
    assert _native.has_native_text_cooccurrence_edges()
    assert _native.has_native_text_cooccurrence_topk()
    for sym in ("srmech_text_glyph_stream", "srmech_text_default_gb_table",
                "srmech_text_cooccurrence_edges",
                "srmech_text_cooccurrence_topk",
                "srmech_text_cooccurrence_topk_extract"):
        assert hasattr(_native.LIB, sym), sym
    # rc287 removed the word tokenizer from the C surface too, keeping the
    # C and Python surfaces 1:1 (the rc135 carrier-consolidation precedent:
    # an orphaned kernel with no caller is removed, not left dangling).
    assert not hasattr(_native.LIB, "srmech_text_tokenize")


def test_native_path_actually_dispatches(monkeypatch):
    """On a native host the wrapper genuinely reaches the C kernel (not a
    silent pure fallback): a sentinel on the ctypes symbol must fire."""
    if not (_native.HAS_NATIVE and _native.has_native_text_glyph_stream()):
        pytest.skip("no native lib — pure-only host")
    hits = []
    real = _native.LIB.srmech_text_glyph_stream

    def spy(*args):
        hits.append(1)
        return real(*args)

    with monkeypatch.context() as m:
        m.setattr(_native.LIB, "srmech_text_glyph_stream", spy)
        out = T.glyph_stream("café straße Hello world's end")
    assert hits, "native glyph_stream gate was on but the C symbol never fired"
    assert out == T.glyph_stream("café straße Hello world's end")


def test_tool_schema_entries_exist():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    for op in ("glyph_stream", "cooccurrence_edges", "cooccurrence_topk"):
        assert f"srmech.math.text.{op}" in names
    assert "srmech.math.text.tokenize" not in names        # retired at rc287
