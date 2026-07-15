"""Text → tokens → co-occurrence-edge ingestion (the Class-L precursor front of K1).

The text→graph leaves of the RBS-LM **K1 presence-kernel** chain
``text → tokenize → cooccurrence_edges → dense_laplacian`` (UPSTREAM_NOTES §17 U1
/ §40). Kept in a dedicated **ingestion** module — `tokenize` is not a spectral
op and `cooccurrence_edges` is the Class-L *precursor* that produces what
:func:`srmech.amsc.laplacian.dense_laplacian` consumes — so ``laplacian`` stays
purely spectral (Class E/G ingestion vs Class-L spectral; §40 Option 1).

This module REPLACES the rc43 `srmech.amsc.laplacian.{tokenize, cooccurrence_edges}`
that failed the §40 acceptance bar 3/3 (F722). Each function now matches the
reference wiki kernel (`R-RBS-LM-WIKIKERNEL…` — `content_words` / `build_edges_topk`
/ `DEFAULT_STOPLIST`) and the three lessons the rc43 versions regressed:

* **Unicode-aware** (F698) — keep codepoints whose ``unicodedata.category(ch)[0]``
  is ``"L"`` (letter) or ``"M"`` (combining mark), casefold; **not** an ASCII
  ``\\w+`` (which truncated ``café`` → ``caf`` and dropped Cyrillic / CJK).
* **No silent vocab cap** (F708) — :func:`cooccurrence_edges` keeps the **full**
  ranked vocabulary by default; a top-K cap is an **explicit, logged** caller
  opt-in (``vocab_size=``), never a silent ``min(…, 256)``. The 256 native bound
  is for the dense-eig *block* only, never the vocabulary or the sparse adjacency.
* **Document-boundary window reset** — co-occurrence never crosses a document
  boundary (one article = one window reset). Pass ``docs`` as a sequence of
  token-sequences (a flat token list is treated as one document).

Numpy-free, deterministic. Class B/G text-segmentation (`tokenize`) ∘ the
Class-L co-occurrence precursor (`cooccurrence_edges`) — no continuous math
(the FPU sits idle; counts are exact integers). Retires the hand-rolled
``Counter()`` co-occurrence idiom the CLAUDE.md STOP-list flags: the output is
edges → ``dense_laplacian``, not a ``Counter`` store.

**rc217 (gh #1360): the three ops dispatch to BYTE-IDENTICAL C peers**
(``srmech_text_tokenize`` / ``srmech_text_cooccurrence_edges`` /
``srmech_text_cooccurrence_topk`` + ``…_topk_extract``) — the corpus-linear
hot loops (per-codepoint tokenize; windowed pair counting; bounded chunk
merge) run in C, while the vocab-scale string↔id mapping stays Python (the
``srmech_klein4_cooccurrence_fold`` split precedent). The tokenizer's Unicode
tables (kept-bitset + casefold exceptions) are built ONCE per process from the
RUNNING interpreter's ``unicodedata`` and handed to C, so native == pure is
byte-identical by construction on any interpreter / Unicode version. The
pure-Python bodies below are the complete alternative (and the parity oracle).
"""
from __future__ import annotations

import ctypes
import itertools
import logging
import unicodedata
from array import array
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from . import _native

__all__ = ["DEFAULT_STOPLIST", "tokenize", "cooccurrence_edges", "cooccurrence_topk"]

_log = logging.getLogger("srmech.amsc.text")

#: General function-word stoplist (articles / conjunctions / prepositions /
#: be-have-do-modal / determiners / pronouns / high-frequency connectives).
#: Function words carry no association mass. This is the **general** stoplist —
#: corpus-specific furniture (wiki markup tokens, etc.) is the caller/adapter's
#: concern per F700, NOT baked in here. The F714 prepositions
#: (``around/across/along/toward/onto/within/among/against/throughout``…) ARE
#: included: the etak-walk drift bug was a *missing function word*, so a thin
#: list is insufficient. Callers extend or replace it (``stoplist=``); pass an
#: empty stoplist for raw mode.
DEFAULT_STOPLIST: frozenset = frozenset({
    # articles / conjunctions / prepositions
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "for",
    "with", "by", "from", "into", "than", "then", "so", "as", "about", "over",
    "under", "after", "before", "between", "during", "through", "out", "up",
    "down", "off", "above", "below", "near", "around", "across", "along",
    "toward", "towards", "onto", "upon", "within", "without", "behind",
    "beyond", "beside", "among", "amongst", "against", "throughout",
    # be / have / do / modal
    "is", "are", "was", "were", "be", "been", "being", "am", "has", "have",
    "had", "having", "do", "does", "did", "may", "can", "could", "would",
    "should", "will", "shall", "must", "might",
    # determiners / pronouns
    "this", "that", "these", "those", "it", "its", "he", "she", "they", "them",
    "their", "his", "her", "him", "we", "us", "our", "you", "your", "i", "me",
    "my", "who", "whom", "whose", "which", "what", "such", "no", "not", "all",
    "any", "some", "each", "every", "both", "few", "more", "most", "other",
    "another", "many", "much", "one", "two", "there", "here",
    # high-frequency connectives / function-ish adverbs
    "also", "when", "where", "while", "how", "why", "if", "because", "however",
    "though", "like", "just", "only", "very", "too", "now", "well", "back",
    "even", "still", "first", "same", "new", "old",
})

#: Apostrophes kept word-internal (ASCII + curly): ``don't`` / ``galaxy's``.
_APOS = "'’"

#: The casefolded DEFAULT_STOPLIST, precomputed once — the common-case
#: ``tokenize`` call re-derives the same frozenset per invocation otherwise
#: (a measured ~23 µs/article tax on the encode loop, both paths).
_DEFAULT_STOP_FOLDED: frozenset = frozenset(s.casefold() for s in DEFAULT_STOPLIST)

#: Minimum content-word length (single letters are not content words).
_MIN_LEN = 2

#: uint32 domain guard for the native co-occurrence kernels (vocab ids /
#: window / cap ride uint32 on the C side; anything beyond falls to pure).
_U32_MAX = 0xFFFFFFFF


# ── rc217: the once-per-process Unicode tables for the native tokenizer ─────
#
# Built from the RUNNING interpreter's unicodedata (never vendored), so the C
# peer is byte-identical to the pure body BY CONSTRUCTION on any Python /
# Unicode version: (a) the kept-bitset — bit cp set iff category(cp)[0] in
# ("L", "M"); (b) the casefold exception table — every cp whose str.casefold
# differs from itself, as sorted cps + offset-indexed folded-UTF-8 blob.
# str.casefold is per-codepoint (Unicode full case folding C+F is
# context-free), which the rc217 test battery locks. If any fold output ever
# contained an apostrophe the C trim-after-fold order would diverge from the
# pure strip-before-fold order — no Unicode version does this; the builder
# verifies and declines the native path entirely if it ever appears.

_TOKENIZE_TABLES: Optional[tuple] = None
_TOKENIZE_TABLES_BUILT = False


def _unicode_tables() -> Optional[tuple]:
    """The cached (kept_bits, fold_cps, fold_off, fold_bytes, n_folds) ctypes
    tables for :func:`srmech_text_tokenize`, or ``None`` when the native path
    must decline (fold-output apostrophe — never on any known Unicode)."""
    global _TOKENIZE_TABLES, _TOKENIZE_TABLES_BUILT
    if _TOKENIZE_TABLES_BUILT:
        return _TOKENIZE_TABLES
    kept = bytearray(0x110000 >> 3)
    fold_cps = array("I")
    fold_off = array("I", [0])
    fold_bytes = bytearray()
    usable = True
    for cp in range(0x110000):
        ch = chr(cp)
        if unicodedata.category(ch)[0] in ("L", "M"):
            kept[cp >> 3] |= 1 << (cp & 7)
        f = ch.casefold()
        if f != ch:
            if "'" in f or "’" in f:      # trim-order safety property
                usable = False
                break
            fold_cps.append(cp)
            fold_bytes += f.encode("utf-8")
            fold_off.append(len(fold_bytes))
    if usable:
        _TOKENIZE_TABLES = (
            (ctypes.c_uint8 * len(kept)).from_buffer_copy(kept),
            (ctypes.c_uint32 * len(fold_cps)).from_buffer_copy(fold_cps),
            (ctypes.c_uint32 * len(fold_off)).from_buffer_copy(fold_off),
            (ctypes.c_uint8 * max(1, len(fold_bytes))).from_buffer_copy(
                bytes(fold_bytes) or b"\x00"),
            len(fold_cps),
        )
    else:                                       # pragma: no cover — no known
        _TOKENIZE_TABLES = None                 # Unicode version trips this
    _TOKENIZE_TABLES_BUILT = True
    return _TOKENIZE_TABLES


@lru_cache(maxsize=32)
def _stop_tables(stop: frozenset) -> tuple:
    """The (stop_off, stop_bytes, n_stop) ctypes tables for one casefolded
    stoplist frozenset — sorted UTF-8 entries for the C binary search (UTF-8
    byte order == codepoint order, so bytewise compare == str compare)."""
    entries = sorted(s.encode("utf-8") for s in stop)
    off = array("I", [0])
    blob = bytearray()
    for e in entries:
        blob += e
        off.append(len(blob))
    return (
        (ctypes.c_uint32 * len(off)).from_buffer_copy(off),
        (ctypes.c_uint8 * max(1, len(blob))).from_buffer_copy(
            bytes(blob) or b"\x00"),
        len(entries),
    )


def _tokenize_native(text: str, stop: frozenset) -> Optional[List[str]]:
    """Native :func:`tokenize` body (text already NFC-normalised when asked).
    Returns the token list, or ``None`` to decline to the pure path (missing
    tables / non-encodable text such as lone surrogates)."""
    tables = _unicode_tables()
    if tables is None:
        return None
    try:
        raw = text.encode("utf-8")
    except UnicodeEncodeError:
        return None                    # lone surrogates — pure path handles
    kept_c, fcps_c, foff_c, fbytes_c, n_folds = tables
    soff_c, sbytes_c, n_stop = _stop_tables(stop)
    # ≥ worst-case fold expansion (≤3× bytes) + one '\n' per token; rounded to
    # the next power of two so the ctypes array TYPE is cache-hit per bucket
    # (a fresh per-length type costs more than the C call on small articles).
    out_cap = 1 << (4 * len(raw) + 16).bit_length()
    out = (ctypes.c_uint8 * out_cap)()
    out_len = ctypes.c_size_t(0)
    rc = _native.LIB.srmech_text_tokenize(
        raw, len(raw), kept_c, fcps_c, foff_c, fbytes_c, n_folds,
        soff_c, sbytes_c, n_stop, out, out_cap, ctypes.byref(out_len))
    if rc != _native.SRMECH_OK:
        raise RuntimeError(f"srmech_text_tokenize returned status {rc}")
    n = out_len.value
    if n == 0:
        return []
    return (ctypes.string_at(ctypes.addressof(out), n - 1)
            .decode("utf-8").split("\n"))


def tokenize(
    text: str,
    *,
    stoplist: Optional[Iterable[str]] = DEFAULT_STOPLIST,
    unicode_normalize: bool = True,
) -> List[str]:
    """Segment ``text`` into casefolded, Unicode-aware content tokens (§40 / F698).

    Walks codepoints and accumulates runs of Unicode **letters** and **combining
    marks** (``unicodedata.category(ch)[0] in ("L", "M")``) — so ``café`` /
    ``naïve`` / ``Москва`` / ``日本語`` survive intact, where the rc43 ASCII
    ``\\w+`` truncated or dropped them. A word-internal apostrophe (ASCII ``'`` or
    curly ``’``) is kept; every other character ends the run. Each run is
    casefolded, apostrophe-stripped at the ends, and kept iff length ≥ 2 and not
    in ``stoplist``.

    Parameters
    ----------
    text
        Already-clean text. Markup stripping (wiki/HTML/LaTeX) is corpus-specific
        and stays in the caller/adapter (F700) — ``tokenize`` takes clean text so
        the op stays general.
    stoplist
        Iterable of function words to drop (compared casefolded). Defaults to
        :data:`DEFAULT_STOPLIST`. Pass ``None`` or an empty iterable for **raw
        mode** (keep all content words). Extend the default to add domain words.
    unicode_normalize
        When ``True`` (default), NFC-normalise ``text`` first so a token's string
        form is canonical (precomposed ``café``), independent of input encoding.

    Returns
    -------
    list[str]
        The casefolded content-token stream :func:`cooccurrence_edges` consumes.

    Class B/G text-segmentation — framing of the text substrate, no numeric
    compute. Numpy-free, deterministic. Dispatches the per-codepoint loop to
    the byte-identical C peer ``srmech_text_tokenize`` when the native lib is
    loaded (rc217); the pure-Python body below is the complete alternative.
    """
    if not isinstance(text, str):
        raise TypeError(f"tokenize: text must be str; got {type(text).__name__}")
    if unicode_normalize:
        text = unicodedata.normalize("NFC", text)
    if stoplist is DEFAULT_STOPLIST:               # common case, precomputed
        stop = _DEFAULT_STOP_FOLDED
    elif stoplist is not None:
        stop = frozenset(s.casefold() for s in stoplist)
    else:
        stop = frozenset()
    if _native.has_native_text_tokenize():
        native = _tokenize_native(text, stop)
        if native is not None:
            return native
    out: List[str] = []
    cur: List[str] = []
    for ch in text:
        if unicodedata.category(ch)[0] in ("L", "M"):
            cur.append(ch)
        elif ch in _APOS and cur:
            cur.append("'")
        elif cur:
            _emit(cur, stop, out)
            cur = []
    if cur:
        _emit(cur, stop, out)
    return out


def _emit(cur: List[str], stop: frozenset, out: List[str]) -> None:
    """Casefold + apostrophe-trim one accumulated run; append iff a kept token."""
    word = "".join(cur).strip("'").casefold()
    if len(word) >= _MIN_LEN and word not in stop:
        out.append(word)


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
