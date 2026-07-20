"""Text → tokens → co-occurrence-edge ingestion (the Class-L precursor front of K1).

The text→graph leaves of the RBS-LM **K1 presence-kernel** chain
``text → tokenize → cooccurrence_edges → dense_laplacian`` (UPSTREAM_NOTES §17 U1
/ §40). Kept in a dedicated **ingestion** module — `tokenize` is not a spectral
op and `cooccurrence_edges` is the Class-L *precursor* that produces what
:func:`srmech.amsc.laplacian.dense_laplacian` consumes — so ``laplacian`` stays
purely spectral (Class E/G ingestion vs Class-L spectral; §40 Option 1).

**rc287 — the unit is the GLYPH CLUSTER, not the word (BREAKING).**
:func:`glyph_stream` replaces the former ``tokenize``. The word decision it
retired carried four Latin-shaped assumptions — a 2-codepoint length floor, a
universal ``casefold``, a 146-word **English** stoplist applied to every
language, and an apostrophe special case — and each mis-handled most of the
world's writing systems. Measured on real Wikipedia prose, scriptio-continua
scripts collapsed into single 45-96 character "words" and **~89% of resulting
types were singletons** (English: 19.6%), so the co-occurrence graph those
tokens fed carried almost no association mass. The front door was not merely
mis-segmenting those languages; it was *manufacturing* a degenerate vocabulary.

A UAX #29 extended grapheme cluster is well-defined in **every** script, so no
per-language decision is made at ingestion. Scale moves the helpful way:
vocabulary shrinks ~5x and co-occurrence edges ~40%, while the stream is ~6.7x
longer (the graph is bounded by vocabulary, not stream length).

``DEFAULT_STOPLIST``, ``_MIN_LEN`` and the apostrophe handling are **gone**, not
deprecated — there is no compatibility shim and no legacy mode. Case folding and
confusable normalisation are per-locale concerns that now belong downstream.
Callers holding stored vocabularies / edge stores built on word ids must
re-encode; see CHANGELOG 0.9.0rc287.

Retained from the rc43/§40 lineage (`R-RBS-LM-WIKIKERNEL…` / `build_edges_topk`):

* **No silent vocab cap** (F708) — :func:`cooccurrence_edges` keeps the **full**
  ranked vocabulary by default; a top-K cap is an **explicit, logged** caller
  opt-in (``vocab_size=``), never a silent ``min(…, 256)``. The 256 native bound
  is for the dense-eig *block* only, never the vocabulary or the sparse adjacency.
* **Document-boundary window reset** — co-occurrence never crosses a document
  boundary (one article = one window reset). Pass ``docs`` as a sequence of
  token-sequences (a flat token list is treated as one document). NB the window
  is now counted in GLYPHS: ``window=5`` spans ~5 glyphs (under one word), not
  ~5 words. Window semantics need re-deriving per corpus, not rescaling.

Numpy-free, deterministic. Class B/G text-segmentation (`glyph_stream`) ∘ the
Class-L co-occurrence precursor (`cooccurrence_edges`) — no continuous math
(the FPU sits idle; counts are exact integers). Retires the hand-rolled
``Counter()`` co-occurrence idiom the CLAUDE.md STOP-list flags: the output is
edges → ``dense_laplacian``, not a ``Counter`` store.

**The three ops dispatch to BYTE-IDENTICAL C peers**
(``srmech_text_glyph_stream`` / ``srmech_text_cooccurrence_edges`` /
``srmech_text_cooccurrence_topk`` + ``…_topk_extract``) — the corpus-linear
hot loops (per-codepoint segmentation; windowed pair counting; bounded chunk
merge) run in C, while the vocab-scale string↔id mapping stays Python (the
``srmech_klein4_cooccurrence_fold`` split precedent).

**How the Unicode table reaches C changed at rc287.** The retired tokenizer
built its tables from the RUNNING interpreter's ``unicodedata``, so native ==
pure held BY CONSTRUCTION with nothing vendored. UAX #29 forecloses that:
``unicodedata`` exposes no grapheme-break property, no ``Extended_Pictographic``
(GB11) and no ``InCB`` (GB9c), so the real choice is vendored-vs-ABSENT, and
absent means broken emoji and broken Indic. srmech therefore vendors ONE
attested table (:mod:`srmech.amsc._unicode_gb_tables`, UCD 16.0.0) that both
coherency projections load; byte-identity is now pinned by **test**
(``test_unicode_gb_tables_attested.py``) rather than by construction, and
upstream drift is caught by ``c/tools/gen_unicode_gb_tables.py --verify``.

Running the other way from the usual vendoring worry: because the table no
longer tracks the host, two hosts at different Python / Unicode versions now
segment text IDENTICALLY. Under the derive-from-host scheme they would not have.

The pure-Python bodies below are the complete alternative (and the parity
oracle); both projections score 1093/1093 on the official ``GraphemeBreakTest``.
"""
from __future__ import annotations

import bisect
import ctypes
import itertools
import logging
import unicodedata
from array import array
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from . import _native
from . import _unicode_gb_tables as _gb

__all__ = ["glyph_stream", "cooccurrence_edges", "cooccurrence_topk"]

_log = logging.getLogger("srmech.amsc.text")

#: uint32 domain guard for the native co-occurrence kernels (vocab ids /
#: window / cap ride uint32 on the C side; anything beyond falls to pure).
_U32_MAX = 0xFFFFFFFF



# ── rc287: the vendored UAX #29 break table, decoded once per process ───────
#
# The retired word tokenizer built its Unicode tables from the RUNNING
# interpreter's `unicodedata`, which made native == pure byte-identical BY
# CONSTRUCTION with nothing vendored. That is not available for UAX #29:
# `unicodedata` exposes no grapheme-break property, no Extended_Pictographic
# (GB11) and no InCB (GB9c) — so the choice is vendored-vs-ABSENT, not
# vendored-vs-derived, and absent means broken emoji and broken Indic.
#
# srmech therefore vendors ONE attested table (`_unicode_gb_tables`, UCD
# 16.0.0) that BOTH coherency projections load, and byte-identity is pinned by
# test (test_unicode_gb_tables_attested.py) instead of by construction.
#
# A consequence worth naming, because it runs the other way from the usual
# "vendoring introduces drift" worry: two hosts at DIFFERENT Python / Unicode
# versions now segment text identically. Under the derive-from-host scheme
# they would not have. The drift that vendoring does introduce is against
# *upstream*, and it is caught by the re-verification script, not by the host.

_GB_TABLE: Optional[tuple] = None
_GB_TABLE_C: Optional[tuple] = None


def _gb_table() -> tuple:
    """The decoded ``(lo, hi, prop)`` range arrays, built once per process."""
    global _GB_TABLE
    if _GB_TABLE is None:
        blob = _gb.GB_TABLE_BLOB
        n = _gb.GB_RANGE_COUNT
        lo = array("I", bytes(n * 4))
        hi = array("I", bytes(n * 4))
        prop = bytearray(n)
        for i in range(n):
            base = i * 9
            lo[i] = int.from_bytes(blob[base:base + 4], "little")
            hi[i] = int.from_bytes(blob[base + 4:base + 8], "little")
            prop[i] = blob[base + 8]
        _GB_TABLE = (lo, hi, bytes(prop))
    return _GB_TABLE


def _gb_table_ctypes() -> tuple:
    """The same table as ctypes arrays for the native peer (built once)."""
    global _GB_TABLE_C
    if _GB_TABLE_C is None:
        lo, hi, prop = _gb_table()
        _GB_TABLE_C = (
            (ctypes.c_uint32 * len(lo)).from_buffer_copy(lo),
            (ctypes.c_uint32 * len(hi)).from_buffer_copy(hi),
            (ctypes.c_uint8 * len(prop)).from_buffer_copy(prop),
            len(prop),
        )
    return _GB_TABLE_C


def _gb_prop(cp: int) -> int:
    """Packed property byte for ``cp`` — gbp in bits 0-3, Extended_Pictographic
    in bit 4, InCB in bits 5-6.

    Hangul LV/LVT come from the UAX #29 §3 syllable algebra rather than table
    rows: the precomposed block U+AC00..U+D7A3 is 798 ranges of pure
    alternation, so deriving it saves exactly 7,254 B and is exact. The
    algebra covers ONLY that block — jamo L/V/T stay table rows, because
    LBase/VBase/TBase are *composition* anchors that do not coincide with the
    GBP jamo ranges (U+1160 HANGUL JUNGSEONG FILLER is GBP=V yet sits below
    VBase=U+1161, and the Jamo Extended-A/B blocks are outside them entirely).
    """
    if _gb.HANGUL_SBASE <= cp < _gb.HANGUL_SBASE + _gb.HANGUL_SCOUNT:
        return (_GBP_LV if (cp - _gb.HANGUL_SBASE) % _gb.HANGUL_TCOUNT == 0
                else _GBP_LVT)
    lo, hi, prop = _gb_table()
    i = bisect.bisect_right(lo, cp) - 1
    if i >= 0 and cp <= hi[i]:
        return prop[i]
    return _GBP_OTHER          # GB999 default


#: GBP tag ordinals, resolved once from the generated table's wire order.
(_GBP_OTHER, _GBP_CR, _GBP_LF, _GBP_CONTROL, _GBP_EXTEND, _GBP_ZWJ,
 _GBP_RI, _GBP_PREPEND, _GBP_SPACINGMARK, _GBP_L, _GBP_V, _GBP_T,
 _GBP_LV, _GBP_LVT) = range(len(_gb.GBP_TAGS))

#: InCB tag ordinals (UAX #29 GB9c).
_INCB_NONE, _INCB_LINKER, _INCB_CONSONANT, _INCB_EXTEND = range(
    len(_gb.INCB_TAGS))

_CONTROLISH = frozenset({_GBP_CONTROL, _GBP_CR, _GBP_LF})


def _glyph_stream_native(text: str) -> Optional[List[str]]:
    """Native :func:`glyph_stream` body. Returns the cluster list, or ``None``
    to decline to the pure path (non-encodable text such as lone surrogates)."""
    try:
        raw = text.encode("utf-8")
    except UnicodeEncodeError:
        return None                    # lone surrogates — pure path handles
    lo_c, hi_c, prop_c, n_ranges = _gb_table_ctypes()
    cap = len(raw) + 1                 # one cluster per byte is the worst case
    out = (ctypes.c_uint32 * cap)()
    out_n = ctypes.c_size_t(0)
    rc = _native.LIB.srmech_text_glyph_stream(
        raw, len(raw), lo_c, hi_c, prop_c, n_ranges,
        out, cap, ctypes.byref(out_n))
    if rc != _native.SRMECH_OK:
        raise RuntimeError(f"srmech_text_glyph_stream returned status {rc}")
    n = out_n.value
    return [raw[out[i]:out[i + 1]].decode("utf-8") for i in range(n)]


def glyph_stream(
    text: str,
    *,
    unicode_normalize: bool = True,
) -> List[str]:
    """Segment ``text`` into UAX #29 **extended grapheme clusters** — the
    language-agnostic glyph stream (rc287).

    A grapheme cluster is what a reader perceives as ONE character. It is the
    only unit that is well-defined in every script, which is precisely why it
    replaced the word here. The word decision this op retired carried four
    Latin-shaped assumptions — a 2-codepoint length floor, a universal
    ``casefold``, a 146-word English stoplist, and an apostrophe special case
    — and each one mis-handled most of the world's writing systems::

        tokenize('语言是人类交流的工具')  →  ['语言是人类交流的工具']   # 1 "word"
        glyph_stream('语言是人类交流的工具') →  ['语','言','是', …]      # 10 glyphs

    In scriptio-continua scripts the old front door made ~89% of types
    singletons — a co-occurrence graph over a 89%-singleton vocabulary carries
    almost no association mass. It was not merely mis-segmenting those
    languages; it was manufacturing a degenerate vocabulary.

    The clusters where codepoint-level and glyph-level answers diverge most
    are the clearest demonstration that the cluster is the right primitive —
    each of these is ONE thing a human sees, and ONE element of the stream::

        '👨‍👩‍👧‍👦'  → one cluster (7 codepoints, GB11)
        '🇻🇺'      → one cluster (2 codepoints, GB12/13)
        'क्षि'      → one cluster (GB9c, Unicode 15.1)
        '1️⃣'      → one cluster (the old path emitted a base-less mark token)

    Parameters
    ----------
    text
        Already-clean text. Markup stripping (wiki/HTML/LaTeX) is
        corpus-specific and stays in the caller/adapter (F700).
    unicode_normalize
        When ``True`` (default), NFC-normalise first so a cluster's string form
        is canonical. Note this is the ONE place the host's ``unicodedata``
        still participates; the break decision itself reads only the vendored
        table, so cluster BOUNDARIES are host-version-independent.

    Returns
    -------
    list[str]
        The glyph stream. Every codepoint of ``text`` appears in exactly one
        cluster, in order, so ``"".join(result)`` reconstructs the (normalised)
        input exactly — the op is lossless, and a boundary never falls inside a
        codepoint or between a base and its combining marks.

    Notes
    -----
    No case folding, no stoplist, no length floor, and whitespace and
    punctuation are emitted as clusters (they *are* clusters). Case folding and
    confusable normalisation are per-locale decisions that now belong
    downstream rather than at the front door.

    Class B/G text-segmentation — framing of the text substrate, no numeric
    compute. Numpy-free, deterministic. Dispatches to the byte-identical C peer
    ``srmech_text_glyph_stream`` when the native lib is loaded; the pure-Python
    body below is the complete alternative (and the parity oracle). Scores
    1093/1093 on the official UAX #29 ``GraphemeBreakTest.txt`` in BOTH
    projections.
    """
    if not isinstance(text, str):
        raise TypeError(
            f"glyph_stream: text must be str; got {type(text).__name__}")
    if unicode_normalize:
        text = unicodedata.normalize("NFC", text)
    if not text:
        return []
    if _native.has_native_text_glyph_stream():
        native = _glyph_stream_native(text)
        if native is not None:
            return native
    props = [_gb_prop(ord(ch)) for ch in text]
    out: List[str] = []
    start = 0
    gb11 = 0                 # 0 none · 1 saw `ExtPict Extend*` · 2 then ZWJ
    incb_consonant = incb_linker = False
    ri_run = 0
    prev = _GBP_OTHER
    for i, cur in enumerate(props):
        brk = True if i == 0 else _gb_is_break(
            prev, cur, gb11, incb_consonant, incb_linker, ri_run)
        if brk and i:
            out.append(text[start:i])
            start = i
        # ── fold `cur` into the lookbehind flags (GB11 / GB9c / GB12-13) ──
        b = cur & _gb.PROP_GBP_MASK
        if cur & _gb.PROP_EXTPICT_BIT:
            gb11 = 1
        elif gb11 == 1 and b == _GBP_EXTEND:
            pass                                     # stay armed
        elif gb11 == 1 and b == _GBP_ZWJ:
            gb11 = 2
        else:
            gb11 = 0
        incb = (cur & _gb.PROP_INCB_MASK) >> _gb.PROP_INCB_SHIFT
        if incb == _INCB_CONSONANT:
            incb_consonant, incb_linker = True, False
        elif incb == _INCB_LINKER:
            if incb_consonant:
                incb_linker = True
        elif incb != _INCB_EXTEND:
            incb_consonant = incb_linker = False
        if b == _GBP_RI:
            ri_run = (ri_run + 1
                      if (prev & _gb.PROP_GBP_MASK) == _GBP_RI and not brk
                      else 1)
        else:
            ri_run = 0
        prev = cur
    out.append(text[start:])
    return out


def _gb_is_break(prev: int, cur: int, gb11: int, incb_consonant: bool,
                 incb_linker: bool, ri_run: int) -> bool:
    """The UAX #29 GB1..GB999 rule ladder. Rule order is significant.

    GB9c and GB11 are specified with lookbehind; both are carried here as
    running flags (``gb11`` / ``incb_*``) so the segmenter is a single forward
    pass — which is also what keeps the C projection inside JPL Rule 4.
    """
    a = prev & _gb.PROP_GBP_MASK
    b = cur & _gb.PROP_GBP_MASK
    if a == _GBP_CR and b == _GBP_LF:
        return False                                              # GB3
    if a in _CONTROLISH or b in _CONTROLISH:
        return True                                               # GB4 / GB5
    if a == _GBP_L and b in (_GBP_L, _GBP_V, _GBP_LV, _GBP_LVT):
        return False                                              # GB6
    if a in (_GBP_LV, _GBP_V) and b in (_GBP_V, _GBP_T):
        return False                                              # GB7
    if a in (_GBP_LVT, _GBP_T) and b == _GBP_T:
        return False                                              # GB8
    if b in (_GBP_EXTEND, _GBP_ZWJ):
        return False                                              # GB9
    if b == _GBP_SPACINGMARK:
        return False                                              # GB9a
    if a == _GBP_PREPEND:
        return False                                              # GB9b
    if a == _GBP_ZWJ and (cur & _gb.PROP_EXTPICT_BIT):
        return gb11 != 2                                          # GB11
    if a == _GBP_RI and b == _GBP_RI:
        return (ri_run % 2) == 0                                  # GB12 / GB13
    if (((cur & _gb.PROP_INCB_MASK) >> _gb.PROP_INCB_SHIFT) == _INCB_CONSONANT
            and incb_consonant and incb_linker):
        return False                                              # GB9c
    return True                                                   # GB999


def _pair_events(m: int, window: int) -> int:
    """Exact windowed pair-event count of one m-token document — the size
    bound for the native hash / scratch arenas (Σ_a min(window, m-1-a))."""
    if m < 2:
        return 0
    w = window if window < m else m - 1
    return w * m - (w * (w + 1)) // 2


def _cooc_edges_native(
    doc_list: List[List[str]], idx: Dict[str, int], keep: set, n: int,
    window: int, covers_all: bool,
) -> Optional[Tuple[int, List[Tuple[int, int]], List[int]]]:
    """Native :func:`cooccurrence_edges` counting stage. The vocab build /
    ranking stays in the (shared) caller; this maps tokens→ids (the same
    ``idx``/``keep`` expressions as the pure loop — when ``covers_all`` the
    vocab covers every token, so the ``in keep`` filter is skipped as an
    identity) and runs the windowed pair-count + deterministic edge sort in
    C. Returns ``None`` to decline (uint32 domain exceeded)."""
    if n > _U32_MAX or window > _U32_MAX:
        return None
    ids = array("I")
    doc_off = [0]
    events = 0
    getid = idx.__getitem__
    for doc in doc_list:
        # one doc = one window reset; identical ids to the pure listcomp
        toks = (list(map(getid, doc)) if covers_all
                else [idx[t] for t in doc if t in keep])
        ids.extend(toks)
        doc_off.append(len(ids))
        events += _pair_events(len(toks), window)
    n_docs = len(doc_list)
    max_cap = 1 << max(10, (2 * max(events, 1)).bit_length())
    cap = min(max_cap, 1 << max(10, (2 * min(max(events, 1), 1 << 21)).bit_length()))
    ids_c = ((ctypes.c_uint32 * len(ids)).from_buffer(ids) if len(ids)
             else (ctypes.c_uint32 * 1)())
    off_c = (ctypes.c_size_t * len(doc_off))(*doc_off)
    n_edges = ctypes.c_size_t(0)
    while True:
        keys = array("Q", bytes(8 * cap))
        vals = array("Q", bytes(8 * cap))
        keys_c = (ctypes.c_uint64 * cap).from_buffer(keys)
        vals_c = (ctypes.c_uint64 * cap).from_buffer(vals)
        rc = _native.LIB.srmech_text_cooccurrence_edges(
            ids_c, len(ids), off_c, n_docs, window, n, keys_c, vals_c, cap,
            ctypes.byref(n_edges))
        del keys_c, vals_c            # release the buffer exports
        if rc == _native.SRMECH_OK:
            break
        if rc == _native.SRMECH_ERR_OVERFLOW and cap < max_cap:
            cap <<= 1                 # grow + retry — identical result
            continue
        raise RuntimeError(f"srmech_text_cooccurrence_edges returned status {rc}")
    ne = n_edges.value
    edges = [(int(kk) >> 32, int(kk) & _U32_MAX) for kk in keys[:ne]]
    weights = [int(v) for v in vals[:ne]]
    return n, edges, weights


def _cooc_edges_directed_native(
    doc_list: List[List[str]], idx: Dict[str, int], keep: set, n: int,
    window: int, covers_all: bool,
) -> Optional[Tuple[int, List[Tuple[int, int]], List[int], List[int]]]:
    """Native directed :func:`cooccurrence_edges` (#1390 item 1). Same
    token→id mapping + arena-grow discipline as :func:`_cooc_edges_native`,
    but the C peer fills the canonical-key ``metric`` (== the undirected
    weight) and signed ``charge`` (``w_fwd − w_bwd``) columns in one pass.
    Returns ``None`` to decline (uint32 domain exceeded)."""
    if n > _U32_MAX or window > _U32_MAX:
        return None
    ids = array("I")
    doc_off = [0]
    events = 0
    getid = idx.__getitem__
    for doc in doc_list:
        toks = (list(map(getid, doc)) if covers_all
                else [idx[t] for t in doc if t in keep])
        ids.extend(toks)
        doc_off.append(len(ids))
        events += _pair_events(len(toks), window)
    n_docs = len(doc_list)
    max_cap = 1 << max(10, (2 * max(events, 1)).bit_length())
    cap = min(max_cap, 1 << max(10, (2 * min(max(events, 1), 1 << 21)).bit_length()))
    ids_c = ((ctypes.c_uint32 * len(ids)).from_buffer(ids) if len(ids)
             else (ctypes.c_uint32 * 1)())
    off_c = (ctypes.c_size_t * len(doc_off))(*doc_off)
    n_edges = ctypes.c_size_t(0)
    while True:
        keys = array("Q", bytes(8 * cap))
        met = array("Q", bytes(8 * cap))
        chg = array("q", bytes(8 * cap))               # signed int64 charge
        keys_c = (ctypes.c_uint64 * cap).from_buffer(keys)
        met_c = (ctypes.c_uint64 * cap).from_buffer(met)
        chg_c = (ctypes.c_int64 * cap).from_buffer(chg)
        rc = _native.LIB.srmech_text_cooccurrence_edges_directed(
            ids_c, len(ids), off_c, n_docs, window, n,
            keys_c, met_c, chg_c, cap, ctypes.byref(n_edges))
        del keys_c, met_c, chg_c      # release the buffer exports
        if rc == _native.SRMECH_OK:
            break
        if rc == _native.SRMECH_ERR_OVERFLOW and cap < max_cap:
            cap <<= 1                 # grow + retry — identical result
            continue
        raise RuntimeError(
            f"srmech_text_cooccurrence_edges_directed returned status {rc}")
    ne = n_edges.value
    edges = [(int(kk) >> 32, int(kk) & _U32_MAX) for kk in keys[:ne]]
    metric = [int(v) for v in met[:ne]]
    charge = [int(c) for c in chg[:ne]]
    return n, edges, metric, charge


def cooccurrence_edges(
    docs: Sequence[object],
    *,
    window: int = 2,
    vocab: Optional[Sequence[str]] = None,
    vocab_size: Optional[int] = None,
    directed: bool = False,
) -> Union[
    Tuple[int, List[Tuple[int, int]], List[int]],
    Tuple[int, List[Tuple[int, int]], List[int], List[int]],
]:
    """Build the weighted co-occurrence graph — the Class-L precursor (§40).

    The tokens→edges step that feeds :func:`srmech.amsc.laplacian.dense_laplacian`.
    Within a sliding ``window`` over each document (the window **resets at every
    document boundary** — co-occurrence never crosses one), counts each unordered
    co-occurring vocabulary pair ``(u, v)`` with ``u < v``.

    Parameters
    ----------
    docs
        Either a sequence of token-sequences (``Sequence[Sequence[str]]`` — one
        inner sequence per document, so the window resets per document) OR a flat
        token sequence (``Sequence[str]``, treated as a single document). A bare
        ``str`` is rejected (tokenise it first).
    window
        Sliding-window radius (caller-set; default 2 per the wiki kernel F681).
    vocab
        An explicit ranked vocabulary (``Sequence[str]``; index = position). When
        given it is used verbatim — tokens outside it are skipped. When ``None``
        (default) the **full** vocabulary is built from token frequency
        (most-frequent first, ties a-z, then sorted for stable ids).
    vocab_size
        Explicit top-K vocabulary cap. ``None`` (default) → **no cap** (keep all
        content words; the F708 fix — the rc43 silent ``vocab_size=1000`` default
        was the pre-encode quantization bug). An int caps to the top-K
        most-frequent and **logs** the dropped count. Ignored when ``vocab`` is
        passed. (The 256 native bound applies to the dense-eig *block* only, never
        the vocabulary or the sparse adjacency.)
    directed
        When ``False`` (default) the unordered ``(n, edges, weights)`` triple
        above. When ``True`` a backward-compatible **superset** returning
        ``(n, edges, metric, charge)`` on the SAME canonical edges: ``metric``
        (== the ``directed=False`` weights, ``w_fwd + w_bwd``) and ``charge``
        (``w_fwd − w_bwd``, the direction the unordered fold discards — reversing
        the corpus flips ``charge`` exactly). ``metric`` + ``charge`` feed
        :func:`srmech.amsc.laplacian.magnetic_laplacian` as ``weights`` +
        ``charges`` (the directed Hermitian L; #1390 item 1).

    Returns
    -------
    (n, edges, weights)  — or  (n, edges, metric, charge) when ``directed``
        ``n`` = node count = ``len(vocab)``; ``edges`` = list of ``(u, v)`` int
        2-tuples (``u < v``); ``weights``/``metric`` = parallel list of **integer**
        co-occurrence counts — exactly the triple ``dense_laplacian(n, edges,
        weights)`` consumes. Raw counts only (IDF / hub down-weighting are
        downstream walk-time re-weights, F714 — not stored here). When
        ``directed`` a fourth parallel **signed integer** ``charge`` list.

    Numpy-free, deterministic. Retires the hand-rolled ``Counter()``
    co-occurrence idiom (the output is edges → ``dense_laplacian``, not a
    store). The windowed pair-count + edge sort dispatch to the byte-identical
    C peer ``srmech_text_cooccurrence_edges`` when the native lib is loaded
    (rc217); the pure-Python loop below is the complete alternative.
    """
    if not isinstance(window, int) or isinstance(window, bool) or window < 1:
        raise ValueError(
            f"cooccurrence_edges: window must be a positive int; got {window!r}"
        )
    if not isinstance(directed, bool):
        raise ValueError(
            f"cooccurrence_edges: directed must be a bool; got {directed!r}"
        )
    if vocab_size is not None and (
        not isinstance(vocab_size, int)
        or isinstance(vocab_size, bool)
        or vocab_size < 1
    ):
        raise ValueError(
            f"cooccurrence_edges: vocab_size must be None or a positive int; "
            f"got {vocab_size!r}"
        )
    doc_list = _as_doc_list(docs)

    if vocab is not None:
        vocab_list: List[str] = list(vocab)
    else:
        freq: Dict[str, int] = {}
        for doc in doc_list:
            for tok in doc:
                freq[tok] = freq.get(tok, 0) + 1
        ranked = sorted(freq, key=lambda w: (-freq[w], w))  # frequent first, ties a-z
        if vocab_size is None or vocab_size >= len(ranked):
            vocab_list = sorted(ranked)                     # NO cap — keep all (F708)
        else:
            kept = ranked[:vocab_size]
            dropped = len(ranked) - len(kept)
            _log.info(
                "cooccurrence_edges: explicit vocab_size=%d capped %d ranked "
                "tokens; dropped %d (caller opt-in, not a default).",
                vocab_size, len(ranked), dropped,
            )
            vocab_list = sorted(kept)

    idx: Dict[str, int] = {w: i for i, w in enumerate(vocab_list)}
    n = len(vocab_list)
    keep = set(vocab_list)
    # covers_all: the uncapped default vocab contains EVERY token, so the
    # native mapping may skip the `in keep` filter (an identity there).
    # NOTE a capped build has n == vocab_size, so only the fully-uncapped
    # (vocab=None, vocab_size=None) case is statically safe to skip.
    covers_all = vocab is None and vocab_size is None
    if directed:
        if _native.has_native_text_cooccurrence_edges_directed():
            native = _cooc_edges_directed_native(
                doc_list, idx, keep, n, window, covers_all)
            if native is not None:
                return native
        fwd: Dict[Tuple[int, int], int] = {}
        bwd: Dict[Tuple[int, int], int] = {}
        for doc in doc_list:
            toks = [idx[t] for t in doc if t in keep]       # one doc = one window reset
            m = len(toks)
            for a in range(m):
                ia = toks[a]
                for b in range(a + 1, min(a + window + 1, m)):
                    ib = toks[b]
                    if ia == ib:
                        continue
                    key = (ia, ib) if ia < ib else (ib, ia)
                    if ia < ib:
                        fwd[key] = fwd.get(key, 0) + 1      # earlier id smaller → forward
                    else:
                        bwd[key] = bwd.get(key, 0) + 1      # earlier id larger → backward
        edges = sorted(set(fwd) | set(bwd))
        metric = [fwd.get(e, 0) + bwd.get(e, 0) for e in edges]
        charge = [fwd.get(e, 0) - bwd.get(e, 0) for e in edges]
        return n, edges, metric, charge
    if _native.has_native_text_cooccurrence_edges():
        native = _cooc_edges_native(doc_list, idx, keep, n, window, covers_all)
        if native is not None:
            return native
    counts: Dict[Tuple[int, int], int] = {}
    for doc in doc_list:
        toks = [idx[t] for t in doc if t in keep]           # one doc = one window reset
        m = len(toks)
        for a in range(m):
            ia = toks[a]
            for b in range(a + 1, min(a + window + 1, m)):
                ib = toks[b]
                if ia == ib:
                    continue
                key = (ia, ib) if ia < ib else (ib, ia)
                counts[key] = counts.get(key, 0) + 1
    edges = sorted(counts)
    weights = [counts[e] for e in edges]
    return n, edges, weights


def _truncate_to(neigh: Dict[int, int], cap: int) -> None:
    """Truncate one node's neighbour map to its ``cap`` highest-weight entries
    (ties → smaller neighbour index first; deterministic). In place — the cap
    that keeps the per-node store bounded."""
    if len(neigh) <= cap:
        return
    kept = sorted(neigh.items(), key=lambda kv: (-kv[1], kv[0]))[:cap]
    neigh.clear()
    neigh.update(kept)


class _CoocTopkNative:
    """The rc217 native state of one :func:`cooccurrence_topk` run: buffers the
    current chunk's per-document vocab-id streams, and drives the C chunk-flush
    (``srmech_text_cooccurrence_topk``) + final read-out (``…_topk_extract``)
    over the persistent bounded store arrays (n_rows × cap, neighbour-ascending
    rows — content-equal to the pure per-node dicts). All arenas are exact-safe
    sized from the chunk's pair-event count, reused + grown across flushes."""

    def __init__(self, window: int, cap: int) -> None:
        self.window = window
        self.cap = cap
        self.rows = 0                       # allocated store rows
        self.store_nbr = array("I")
        self.store_w = array("Q")
        self.store_len = array("I")
        self.ids = array("I")               # current chunk's token ids
        self.doc_off: List[int] = [0]
        self.events = 0                     # current chunk's pair-event bound
        self._ht = array("Q")               # keys+vals hash arena (2×ht_cap)
        self._ht_cap = 0
        self._dir = array("Q")              # directed (key, w) record scratch
        self._scr = array("Q")              # one node's merge scratch

    def add_doc(self, toks: List[int]) -> None:
        self.ids.extend(toks)
        self.doc_off.append(len(self.ids))
        self.events += _pair_events(len(toks), self.window)

    def _grow_store(self, n_vocab: int) -> None:
        if n_vocab > self.rows:
            new_rows = max(n_vocab, 2 * self.rows, 1024)
            self.store_nbr.frombytes(bytes(4 * self.cap * (new_rows - self.rows)))
            self.store_w.frombytes(bytes(8 * self.cap * (new_rows - self.rows)))
            self.store_len.frombytes(bytes(4 * (new_rows - self.rows)))
            self.rows = new_rows

    def flush(self, n_vocab: int) -> None:
        """One chunk flush — the same cadence as the pure ``_flush`` (the
        flush timing is parity-load-bearing: truncation happens per flush)."""
        n_docs = len(self.doc_off) - 1
        if n_docs == 0 or self.events == 0:
            # No documents / no pair events in this chunk — the pure _flush
            # is a no-op too (no chunk entries were accumulated). Reset only.
            self.ids = array("I")
            self.doc_off = [0]
            self.events = 0
            return
        self._grow_store(n_vocab)
        ht_cap = 1 << max(10, (2 * max(self.events, 1) + 1).bit_length())
        if self._ht_cap < ht_cap:
            self._ht = array("Q", bytes(16 * ht_cap))
            self._ht_cap = ht_cap
        dir_recs = 2 * max(self.events, 1)
        if len(self._dir) < 2 * dir_recs:
            self._dir = array("Q", bytes(16 * dir_recs))
        scr_recs = self.cap + max(self.events, 1)
        if len(self._scr) < 2 * scr_recs:
            self._scr = array("Q", bytes(16 * scr_recs))
        ids_c = ((ctypes.c_uint32 * len(self.ids)).from_buffer(self.ids)
                 if len(self.ids) else (ctypes.c_uint32 * 1)())
        off_c = (ctypes.c_size_t * len(self.doc_off))(*self.doc_off)
        snbr_c = (ctypes.c_uint32 * len(self.store_nbr)).from_buffer(self.store_nbr)
        sw_c = (ctypes.c_uint64 * len(self.store_w)).from_buffer(self.store_w)
        slen_c = (ctypes.c_uint32 * len(self.store_len)).from_buffer(self.store_len)
        keys_c = (ctypes.c_uint64 * self._ht_cap).from_buffer(self._ht)
        vals_c = (ctypes.c_uint64 * self._ht_cap).from_buffer(
            self._ht, 8 * self._ht_cap)
        dir_c = (ctypes.c_uint64 * len(self._dir)).from_buffer(self._dir)
        scr_c = (ctypes.c_uint64 * len(self._scr)).from_buffer(self._scr)
        rc = _native.LIB.srmech_text_cooccurrence_topk(
            ids_c, len(self.ids), off_c, n_docs, self.window, self.cap,
            n_vocab, snbr_c, sw_c, slen_c, keys_c, vals_c, self._ht_cap,
            dir_c, len(self._dir) // 2, scr_c, len(self._scr) // 2)
        del ids_c, snbr_c, sw_c, slen_c, keys_c, vals_c, dir_c, scr_c
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_text_cooccurrence_topk returned status {rc}")
        self.ids = array("I")
        self.doc_off = [0]
        self.events = 0

    def extract(self, n_vocab: int, k: int):
        """The final §52 read-out: per-node ranked top-k rows + the first-seen
        deduplicated (key, weight) edge records, all in C."""
        self._grow_store(max(n_vocab, 1))
        total = 0
        slen = self.store_len
        for u in range(n_vocab):
            l = slen[u]
            total += l if l < k else k
        topk_nbr = array("I", bytes(4 * k * max(1, n_vocab)))
        topk_w = array("Q", bytes(8 * k * max(1, n_vocab)))
        topk_len = array("I", bytes(4 * max(1, n_vocab)))
        edge_recs = array("Q", bytes(24 * max(1, total)))
        node_scr = array("Q", bytes(16 * self.cap))
        n_edges = ctypes.c_size_t(0)
        snbr_c = (ctypes.c_uint32 * len(self.store_nbr)).from_buffer(self.store_nbr)
        sw_c = (ctypes.c_uint64 * len(self.store_w)).from_buffer(self.store_w)
        slen_c = (ctypes.c_uint32 * len(self.store_len)).from_buffer(self.store_len)
        tn_c = (ctypes.c_uint32 * len(topk_nbr)).from_buffer(topk_nbr)
        tw_c = (ctypes.c_uint64 * len(topk_w)).from_buffer(topk_w)
        tl_c = (ctypes.c_uint32 * len(topk_len)).from_buffer(topk_len)
        er_c = (ctypes.c_uint64 * len(edge_recs)).from_buffer(edge_recs)
        ns_c = (ctypes.c_uint64 * len(node_scr)).from_buffer(node_scr)
        rc = _native.LIB.srmech_text_cooccurrence_topk_extract(
            snbr_c, sw_c, slen_c, n_vocab, self.cap, k,
            tn_c, tw_c, tl_c, er_c, max(1, total), ctypes.byref(n_edges),
            ns_c, self.cap)
        del snbr_c, sw_c, slen_c, tn_c, tw_c, tl_c, er_c, ns_c
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_text_cooccurrence_topk_extract returned status {rc}")
        ne = n_edges.value
        edges = [(int(kk) >> 32, int(kk) & _U32_MAX)
                 for kk in edge_recs[0:2 * ne:2]]
        weights = [int(w) for w in edge_recs[1:2 * ne:2]]
        return edges, weights, topk_nbr, topk_w, topk_len


def cooccurrence_topk(
    docs: Iterable[object],
    *,
    window: int = 2,
    k: int = 20,
    vocab: Optional[Sequence[str]] = None,
    cap_slack: int = 4,
    chunk_docs: int = 2048,
) -> Dict[str, object]:
    """Streaming / bounded top-K co-occurrence — the LOW-RAM ENCODE peer of
    :func:`cooccurrence_edges` (UPSTREAM §52 / F793).

    The all-in-RAM :func:`cooccurrence_edges` holds every document in memory and
    materialises the FULL pair-count edge list (the measured 2.1–2.4 GB encode
    peak: docs + ~9 M edges). This streaming peer instead

    * consumes ``docs`` as a **one-pass stream** (an iterable / generator — each
      document is processed then released, so the corpus is never all resident),
      and
    * keeps only a **bounded top-K-per-node** store via **chunked merge**: it
      accumulates the FULL co-occurrence of each ``chunk_docs``-document chunk
      (bounded by the chunk, not the corpus), then merges those weights into the
      running per-node store and truncates each node to a cap of ``k * cap_slack``
      highest-weight neighbours,

    so the peak is ``O(vocab × k·cap_slack + chunk)`` — never the full edge count.
    It is the *explicit* bounded analog of the §50 holographic
    :func:`srmech.amsc.hdc.cooccurrence_fold`, and the bounded ``(n, edges,
    weights)`` triple it returns is a drop-in for
    :func:`srmech.amsc.laplacian.fiedler_sparse` /
    :func:`srmech.amsc.laplacian.normalized_cut_bisect` — so the whole
    spectral-clump ENCODE (tokens → bounded graph → recursive cut) stays bounded.

    HONESTY: when a node's realized degree never exceeds the cap it is **bit-exact**
    to the full-graph top-K (no truncation happens); the chunked merge keeps the
    **full summed weight** for every retained neighbour (within-chunk weights
    accumulate before any truncation, so a heavy co-occurrence is never lost to a
    mid-accumulation eviction). Truncation only drops a neighbour that fell out of
    the ``k·cap_slack`` window AND did not return within a later chunk — the long
    tail, which the downstream normalized-cut is robust to (top-K sparsification IS
    the production preprocessing; §51 stress test). Larger ``cap_slack`` /
    ``chunk_docs`` → more exact, more RAM. For ``vocab=None`` the vocabulary is built
    **incrementally** (index = order of first appearance) because a single
    streaming pass cannot pre-rank by frequency; pass an explicit ``vocab`` for a
    stable index map. For a genuinely low-RAM encode, stream a **per-document**
    iterable (each ``doc`` a token sequence — then the transient per-doc token
    list is the only doc-scale allocation); a flat ``Sequence[str]`` is treated
    as a single document (small-input convenience).

    Returns
    -------
    dict
        ``{"n", "vocab", "edges", "weights", "topk"}`` — ``n`` / ``vocab`` the
        node count + index→token list; ``(edges, weights)`` the bounded
        undirected sparse-graph triple (``u < v``, integer counts) for the
        Laplacian path; ``topk`` the ``{token: [(neighbour, weight), …≤k]}``
        per-token view (the §52 contract). Numpy-free, deterministic. The
        chunk flush + final read-out dispatch to the byte-identical C peers
        ``srmech_text_cooccurrence_topk`` / ``…_topk_extract`` when the native
        lib is loaded (rc217); the pure-Python body is the complete alternative.
    """
    if not isinstance(window, int) or isinstance(window, bool) or window < 1:
        raise ValueError(f"cooccurrence_topk: window must be a positive int; got {window!r}")
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError(f"cooccurrence_topk: k must be a positive int; got {k!r}")
    if not isinstance(cap_slack, int) or isinstance(cap_slack, bool) or cap_slack < 1:
        raise ValueError(f"cooccurrence_topk: cap_slack must be a positive int; got {cap_slack!r}")
    if not isinstance(chunk_docs, int) or isinstance(chunk_docs, bool) or chunk_docs < 1:
        raise ValueError(f"cooccurrence_topk: chunk_docs must be a positive int; got {chunk_docs!r}")
    if isinstance(docs, str):
        raise TypeError("cooccurrence_topk: docs must be a token sequence or a stream of "
                        "token sequences, not a raw str — tokenize() it first")
    cap = k * cap_slack

    fixed_vocab = vocab is not None
    vocab_list: List[str] = list(vocab) if fixed_vocab else []
    idx: Dict[str, int] = {w: i for i, w in enumerate(vocab_list)}

    def _index(tok: str) -> Optional[int]:
        if fixed_vocab:
            return idx.get(tok)                  # out-of-vocab tokens skipped
        j = idx.get(tok)
        if j is None:
            j = len(vocab_list)
            idx[tok] = j
            vocab_list.append(tok)
        return j

    # Peek ONE item (without draining the stream) to disambiguate a flat token
    # sequence (one document) from a stream of documents.
    it = iter(docs)
    try:
        head = next(it)
    except StopIteration:
        return {"n": 0, "vocab": vocab_list, "edges": [], "weights": [], "topk": {}}
    if isinstance(head, str):
        doc_stream: Iterable[object] = [itertools.chain([head], it)]   # one flat document
    else:
        doc_stream = itertools.chain([head], it)                       # a document stream

    # rc217 native path: the SAME stream / vocab / chunk cadence, with the
    # window pair accumulation + chunked merge/truncate + final read-out in C
    # (byte-identical to the pure body below — the parity battery locks it).
    if (_native.has_native_text_cooccurrence_topk()
            and window <= _U32_MAX and cap <= _U32_MAX and k <= _U32_MAX):
        st = _CoocTopkNative(window=window, cap=cap)
        pending = 0
        for doc in doc_stream:                    # STREAM — one doc at a time
            toks: List[int] = []
            for t in doc:
                if isinstance(t, str):
                    j = _index(t)
                    if j is not None:
                        toks.append(j)
            st.add_doc(toks)
            pending += 1
            if pending >= chunk_docs:
                st.flush(len(vocab_list))
                pending = 0
        st.flush(len(vocab_list))                 # final partial chunk
        n = len(vocab_list)
        edges, weights, topk_nbr, topk_w, topk_len = st.extract(n, k)
        topk: Dict[str, List[Tuple[str, int]]] = {}
        for u in range(n):
            ln = topk_len[u]
            if ln == 0:
                continue
            base = u * k
            topk[vocab_list[u]] = [
                (vocab_list[topk_nbr[base + r]], int(topk_w[base + r]))
                for r in range(ln)
            ]
        return {"n": n, "vocab": vocab_list, "edges": edges,
                "weights": weights, "topk": topk}

    store: Dict[int, Dict[int, int]] = {}         # running per-node top-cap (bounded)
    chunk: Dict[int, Dict[int, int]] = {}         # current chunk's full adjacency (bounded by chunk)

    def _flush() -> None:
        """Merge the current chunk's full weights into the running store, then
        truncate each touched node back to the cap. Within-chunk weights are
        already FULL, so heavy co-occurrences are never lost mid-accumulation."""
        for u, neigh in chunk.items():
            su = store.setdefault(u, {})
            for v, w in neigh.items():
                su[v] = su.get(v, 0) + w
            if len(su) > cap:
                _truncate_to(su, cap)
        chunk.clear()

    pending = 0
    for doc in doc_stream:                        # STREAM — one document at a time
        toks: List[int] = []
        for t in doc:
            if isinstance(t, str):
                j = _index(t)
                if j is not None:
                    toks.append(j)
        m = len(toks)
        for a in range(m):                        # forward window (resets per doc)
            ia = toks[a]
            for b in range(a + 1, min(a + window + 1, m)):
                ib = toks[b]
                if ia == ib:
                    continue
                cu = chunk.setdefault(ia, {})
                cu[ib] = cu.get(ib, 0) + 1
                cv = chunk.setdefault(ib, {})
                cv[ia] = cv.get(ia, 0) + 1
        pending += 1
        if pending >= chunk_docs:                 # flush the bounded chunk into the store
            _flush()
            pending = 0
        # `toks` released here
    _flush()                                      # final partial chunk

    n = len(vocab_list)
    topk: Dict[str, List[Tuple[str, int]]] = {}
    seen: set = set()
    edges: List[Tuple[int, int]] = []
    weights: List[int] = []
    for u in range(n):
        su = store.get(u)
        if not su:
            continue
        ranked = sorted(su.items(), key=lambda kv: (-kv[1], kv[0]))[:k]   # node's top-K
        topk[vocab_list[u]] = [(vocab_list[v], w) for v, w in ranked]
        for v, w in ranked:                       # union of per-node top-K → sparse graph
            a, b = (u, v) if u < v else (v, u)
            if (a, b) in seen:
                continue
            seen.add((a, b))
            edges.append((a, b))
            weights.append(w)
    order = sorted(range(len(edges)), key=lambda i: edges[i])
    edges = [edges[i] for i in order]
    weights = [weights[i] for i in order]
    return {"n": n, "vocab": vocab_list, "edges": edges, "weights": weights, "topk": topk}


def _as_doc_list(docs: Sequence[object]) -> List[List[str]]:
    """Normalise ``docs`` to a list of token lists (one per document).

    A flat ``Sequence[str]`` is treated as a single document; a sequence of
    token-sequences is taken per-document (window resets at each boundary). A
    bare ``str`` is rejected — tokens, not characters, are wanted.
    """
    if isinstance(docs, str):
        raise TypeError(
            "cooccurrence_edges: docs must be a token sequence or a sequence of "
            "token sequences, not a raw str — tokenize() it first"
        )
    materialised = list(docs)
    if not materialised:
        return []
    if isinstance(materialised[0], str):
        return [list(materialised)]                          # flat tokens → one document
    return [list(d) for d in materialised]                   # per-document token lists
