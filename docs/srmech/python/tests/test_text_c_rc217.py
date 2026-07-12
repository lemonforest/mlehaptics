"""rc217 (gh #1360) — BYTE-IDENTICAL C peers for `srmech.amsc.text`.

The §40/§52 text→graph ingestion ops (`tokenize` / `cooccurrence_edges` /
`cooccurrence_topk`) shipped rc50/§52 as pure-Python kernels with NO C peer —
the enwiki comprehended-encode's dominant cost ran in Python even on a native
wheel. rc217 gives each a byte-identical C peer (`srmech_text_tokenize` /
`srmech_text_cooccurrence_edges` / `srmech_text_cooccurrence_topk` +
`…_topk_extract`) and fixes their Rosetta mis-classification
(non_compute/composes_c → c_dispatched — the self-contained-kernel hiding
spot; see COMPOSES_C_ZERO_REACH_PINNED in test_rosetta_completeness.py).

The parity contract here is BYTE-IDENTICAL equality of the whole result
(token stream / integer counts / tie-breaks / edge order) — the pure body is
the oracle, exercised by forcing every `has_native_text_*` gate off. On a
no-C host both sides run the pure body and the assertions still hold (the
suite stays green with no native lib, per the §17 discipline).

Numpy-free.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import text as T


# ──────────────────────────────────────────────────────────────────────
# forced-pure helpers (the oracle side of every parity assert)
# ──────────────────────────────────────────────────────────────────────

def _pure_tokenize(monkeypatch, *a, **kw):
    with monkeypatch.context() as m:
        m.setattr(_native, "has_native_text_tokenize", lambda: False)
        return T.tokenize(*a, **kw)


def _pure_edges(monkeypatch, *a, **kw):
    with monkeypatch.context() as m:
        m.setattr(_native, "has_native_text_cooccurrence_edges", lambda: False)
        return T.cooccurrence_edges(*a, **kw)


def _pure_topk(monkeypatch, *a, **kw):
    with monkeypatch.context() as m:
        m.setattr(_native, "has_native_text_cooccurrence_topk", lambda: False)
        return T.cooccurrence_topk(*a, **kw)


# ──────────────────────────────────────────────────────────────────────
# tokenize — Unicode battery (byte-identical native == pure)
# ──────────────────────────────────────────────────────────────────────

_TOKENIZE_CASES = [
    # plain English + default stoplist
    "Hello, world! The quick brown fox jumps over the lazy dog.",
    # Latin accents / Cyrillic / CJK (the F698 lesson — no ASCII \\w+)
    "café naïve Москва 日本語 straße test",
    # apostrophes: internal kept, trailing/leading trimmed, curly → ASCII
    "don't stop 'quoted' galaxy's rock'n'roll '' ' a''b",
    "’leading curly’ trailing’ mid’dle",
    # casefold expansions (ß→ss makes the 2-cp floor; İ → i + combining dot)
    "ß ẞ İstanbul DİYARBAKIR ΣΊΣΥΦΟΣ ὈΔΥΣΣΕΎΣ",
    # ligature folds (ﬃ → ffi) + titlecase digraphs
    "ﬁre ﬂow oﬃce Ǆungla ǅ ǆ ǳ Ǳ",
    # combining marks ride the run (category M kept)
    "étude combininǵ marks͂ café",
    # separators / punctuation / digits end runs; single letters dropped
    "ab-cd ef_gh 123 x9y a1 ..́..",
    "tabs\tand\nnewlines\r\nmixed  spaces",
    # empties / minimal
    "", "a", "xy", "''", "’’",
]


@pytest.mark.parametrize("case", _TOKENIZE_CASES)
def test_tokenize_native_equals_pure(monkeypatch, case):
    for kw in ({}, {"stoplist": None},
               {"stoplist": ["café", "straße", "hello", "ss"]},
               {"unicode_normalize": False}):
        assert T.tokenize(case, **kw) == _pure_tokenize(monkeypatch, case, **kw)


def test_tokenize_nfd_input_normalises_identically(monkeypatch):
    nfd = unicodedata.normalize("NFD", "café naïve étude")
    assert T.tokenize(nfd) == _pure_tokenize(monkeypatch, nfd)
    assert T.tokenize(nfd) == T.tokenize("café naïve étude")


def test_tokenize_known_values():
    # pinned semantics (not just parity): stop words drop, ß folds to ss,
    # curly apostrophe becomes ASCII, trailing apostrophes trim.
    assert T.tokenize("The Weiße Rose didn’t stop") == ["weisse", "rose", "didn't", "stop"]
    assert T.tokenize("ß alone") == ["ss", "alone"]     # 1 char → 2 cps ≥ MIN_LEN
    assert T.tokenize("a b c") == []                    # single letters drop


def test_tokenize_fold_concat_property():
    """str.casefold is per-codepoint (Unicode full folding C+F is context-free)
    — the property the C per-char fold relies on; locked over every
    non-identity fold row concatenated pairwise."""
    folds = [chr(cp) for cp in range(0x500) if chr(cp).casefold() != chr(cp)]
    probe = "".join(folds)
    assert probe.casefold() == "".join(c.casefold() for c in probe)


def test_tokenize_fold_outputs_carry_no_apostrophe():
    """No casefold output contains an apostrophe (the C trim-after-fold order
    relies on it; the table builder verifies EXHAUSTIVELY and declines the
    native path entirely if it ever appeared). Re-verified here over the BMP;
    plus the builder's tables exist with non-identity rows."""
    for cp in range(0x10000):
        f = chr(cp).casefold()
        if f != chr(cp):
            assert "'" not in f and "’" not in f, hex(cp)
    tables = T._unicode_tables()
    if tables is None:                                   # pragma: no cover
        pytest.skip("interpreter Unicode tables declined (fold apostrophe)")
    assert tables[4] > 0                                 # non-identity rows exist


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
    for op in ("tokenize", "cooccurrence_edges", "cooccurrence_topk"):
        row = rows[f"srmech.amsc.text.{op}"]
        assert row["bucket"] == "c_dispatched", row
        assert "non_compute_kind" not in row, row


def test_native_gates_bound_on_a_native_host():
    if not _native.HAS_NATIVE:
        pytest.skip("no native lib — pure-only host")
    assert _native.has_native_text_tokenize()
    assert _native.has_native_text_cooccurrence_edges()
    assert _native.has_native_text_cooccurrence_topk()
    for sym in ("srmech_text_tokenize", "srmech_text_cooccurrence_edges",
                "srmech_text_cooccurrence_topk",
                "srmech_text_cooccurrence_topk_extract"):
        assert hasattr(_native.LIB, sym), sym


def test_native_path_actually_dispatches(monkeypatch):
    """On a native host the wrapper genuinely reaches the C kernel (not a
    silent pure fallback): a sentinel on the ctypes symbol must fire."""
    if not (_native.HAS_NATIVE and _native.has_native_text_tokenize()):
        pytest.skip("no native lib — pure-only host")
    hits = []
    real = _native.LIB.srmech_text_tokenize

    def spy(*args):
        hits.append(1)
        return real(*args)

    with monkeypatch.context() as m:
        m.setattr(_native.LIB, "srmech_text_tokenize", spy)
        out = T.tokenize("café straße Hello world's end")
    assert hits, "native tokenize gate was on but the C symbol never fired"
    assert out == T.tokenize("café straße Hello world's end")


def test_tool_schema_entries_exist():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    for op in ("tokenize", "cooccurrence_edges", "cooccurrence_topk"):
        assert f"srmech.amsc.text.{op}" in names
