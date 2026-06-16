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

Pure-Python, numpy-free, deterministic. Class B/G text-segmentation (`tokenize`)
∘ the Class-L co-occurrence precursor (`cooccurrence_edges`) — no continuous
math (the FPU sits idle; counts are exact integers). Retires the hand-rolled
``Counter()`` co-occurrence idiom the CLAUDE.md STOP-list flags: the output is
edges → ``dense_laplacian``, not a ``Counter`` store.
"""
from __future__ import annotations

import itertools
import logging
import unicodedata
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

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

#: Minimum content-word length (single letters are not content words).
_MIN_LEN = 2


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
    compute. Pure-Python, numpy-free, deterministic.
    """
    if not isinstance(text, str):
        raise TypeError(f"tokenize: text must be str; got {type(text).__name__}")
    if unicode_normalize:
        text = unicodedata.normalize("NFC", text)
    stop = (
        frozenset(s.casefold() for s in stoplist)
        if stoplist is not None
        else frozenset()
    )
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


def cooccurrence_edges(
    docs: Sequence[object],
    *,
    window: int = 2,
    vocab: Optional[Sequence[str]] = None,
    vocab_size: Optional[int] = None,
) -> Tuple[int, List[Tuple[int, int]], List[int]]:
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

    Returns
    -------
    (n, edges, weights)
        ``n`` = node count = ``len(vocab)``; ``edges`` = list of ``(u, v)`` int
        2-tuples (``u < v``); ``weights`` = parallel list of **integer**
        co-occurrence counts — exactly the triple ``dense_laplacian(n, edges,
        weights)`` consumes. Raw counts only (IDF / hub down-weighting are
        downstream walk-time re-weights, F714 — not stored here).

    Pure-Python, numpy-free, deterministic. Retires the hand-rolled ``Counter()``
    co-occurrence idiom (the output is edges → ``dense_laplacian``, not a store).
    """
    if not isinstance(window, int) or isinstance(window, bool) or window < 1:
        raise ValueError(
            f"cooccurrence_edges: window must be a positive int; got {window!r}"
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
        per-token view (the §52 contract). Numpy-free, deterministic.
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
