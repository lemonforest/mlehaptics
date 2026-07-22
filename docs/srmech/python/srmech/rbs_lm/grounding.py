"""srmech.rbs_lm.grounding — the doc-frequency-gated aboutness grounding encoder.

The §112 / F1008 first-class capability: a natural "user asks X" utterance (or an
op's name+summary) → ONE structure-bearing Klein-4 aboutness hypervector, so that
retrieving "which srmech op does this?" is one call instead of a hand-build. The
shipped :func:`srmech.rbs_lm.encode_sentence_l3` grounds at the ~1/5 orthogonality
FLOOR on this task (measured top-1 3/18 ≈ 17% over the shipped ``tool_schema``,
both ``byteglyph`` and ``wordhash``) because it lacks the three levers F1008
(SIONA-INFER-2, `research/rbs-lm-rolling-2`) proved are load-bearing:

1. a **doc-frequency aboutness gate** (F768/F984) — a token that appears in a
   large fraction of the catalog is function-word "glue", not aboutness; gate it
   out so the shared generic tokens ("matrix", "vector", "of") stop dominating;
2. **name-weighting** (F769 title-vs-definition) — an op's own NAME is its
   identity, so its name tokens count more (3× unigram + 2× bigram) than its
   description tokens;
3. **order-aware bigrams** (`[[feedback_never_bag_of_words_even_for_testing]]`) —
   adjacency binds so ``(klein, 4)`` ≠ ``(klein, gordon)`` on the shared unigram
   "klein"; a bag collides physics ``klein_gordon`` onto a klein-4 query.

Plus **letter-digit tokenization** (``klein4`` → ``klein 4``, ``sha256`` → ``sha
256``) on both sides so a query that spells ``klein-4`` aligns with the ``klein4``
in an op name.

Structure-bearing, NOT high-diffusion (F1260)
---------------------------------------------
Grounding is a REPRESENTATION problem, not an ADDRESS problem. F1260 established
that a word-hashed / SHA-seeded Klein-4 vector (``klein4_random(seed=sha256(w))``
= the ``klein4_address`` ADDRESSED regime) puts EVERY token pair on the 0.25
orthogonality floor: ``cat``/``cats`` is then indistinguishable from ``cat``/``dog``
(the SHA avalanche destroys morphology — high diffusion makes a good ADDRESS and
disqualifies it as a REPRESENTATION). So the DEFAULT token backend here is the
COMPOSED regime :func:`srmech.amsc.hdc.klein4_encode_bytes` (byte-position-bound
bundle), which restores morphology — ``cat``/``cats`` ≈ 0.66 while ``cat``/``dog``
stays ≈ 0.25 — keeping the encoder on the structure-bearing side of the F1260
axis. ``token_mode="address"`` is offered as the F1008 fast/orthogonal dual
(clean per-token orthogonality, no morphology), but it is NOT the default and is
NOT structure-bearing.

Classification
--------------
``composition_of_c``: the representation-bearing compute is a transitive
composition of the ``c_dispatched`` Klein-4 primitives
(``klein4_encode_bytes`` → ``klein4_bind`` / ``klein4_bundle`` /
``klein4_random``); the tokenizer / doc-frequency gate / name-weighting are
Python SELECTION glue over which C-backed atoms get composed, exactly like the
existing rbs_lm ladder. There is no dedicated ``srmech_rbs_lm_encode_aboutness``
C symbol, so this is NOT ``c_dispatched`` — the honest narrow bucket is
``composition_of_c`` (standalone-ready: every composed leaf reaches C).

numpy-free; no ``abs()`` / ``Counter`` / bag.
"""
from __future__ import annotations

import re

from srmech.amsc import hdc
from srmech.amsc.hv import HV

__all__ = [
    "encode_aboutness",
    "ground_tool_schema",
]

# Letter-digit split BOTH sides (klein4 -> klein 4, sha256 -> sha 256) so a
# query spelled "klein-4" aligns with the "klein4" of an op name (F1008 iter 2).
_LD_ALPHA_DIGIT = re.compile(r"([a-z])([0-9])")
_LD_DIGIT_ALPHA = re.compile(r"([0-9])([a-z])")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _aboutness_tokens(text):
    """Lower-case, letter-digit-split, non-alphanumeric-split tokenizer.

    Drops length-1 alphabetic noise (``a``, ``x``) but keeps bare digits
    (``4``, ``256``). Deterministic; the SAME split is applied to both the op
    name/summary side and the query side so their tokens align. PRIVATE glue —
    no compute, no C dispatch, kept off the public surface so the rosetta ledger
    never has to account for a bare tokenizer as a compute op."""
    s = (text or "").lower()
    s = _LD_ALPHA_DIGIT.sub(r"\1 \2", s)
    s = _LD_DIGIT_ALPHA.sub(r"\1 \2", s)
    return [w for w in _NON_ALNUM.split(s) if len(w) > 1 or w.isdigit()]


def _doc_frequencies(documents):
    """Build the (df, n_docs) doc-frequency table for the aboutness gate.

    ``documents`` is an iterable of documents, each a raw string OR an
    already-tokenized ``list``/``tuple``. ``df[token]`` counts the documents the
    token appears in (once per document — a ``set`` per doc). PRIVATE glue for
    :func:`ground_tool_schema`; callers grounding a CUSTOM corpus pass their own
    ``df`` dict to :func:`encode_aboutness` directly."""
    df: dict[str, int] = {}
    n_docs = 0
    for doc in documents:
        toks = doc if isinstance(doc, (list, tuple)) else _aboutness_tokens(doc)
        n_docs += 1
        for w in set(toks):
            df[w] = df.get(w, 0) + 1
    return df, n_docs


def _gate_keep(w, df, func):
    """F768/F984 aboutness gate as a keep/drop boolean: KEEP token ``w`` iff it
    is NOT a catalog-wide function word, i.e. its doc-frequency is below the
    ``func`` threshold. With no ``df`` corpus the gate is disabled (keep all)."""
    if df is None:
        return True
    return df.get(w, 0) < func


def encode_aboutness(text, *, D, df=None, n_docs=None, name=None,
                     name_weight=3, name_bigram_weight=2, func_frac=0.35,
                     token_mode="byteglyph"):
    """Encode ``text`` as one df-gated, name-weighted, order-aware aboutness HV.

    This is the reusable grounding PRIMITIVE (F1008 recipe): encode an op's
    ``name`` + ``summary`` this way to build the retrieval index, and encode a
    user utterance the SAME way (``name=None``) to query it; the nearest tool by
    :func:`srmech.amsc.hdc.klein4_similarity` is the grounded op.

    Args:
        text: the description / summary / utterance body. Its tokens are
            doc-frequency GATED (dropped when they are catalog-wide glue).
        D: Klein-4 dimension (positive int; F1008 used ``D=8192``).
        df: optional doc-frequency table from :func:`_doc_frequencies`. ``None``
            disables the gate (every token kept — the single-word / no-corpus
            case, e.g. the F1260 morphology check).
        n_docs: the document count paired with ``df`` (sets the gate threshold
            ``func = int(n_docs * func_frac)``). Required when ``df`` is given.
        name: optional IDENTITY string (an op's own name). Its tokens are NEVER
            gated and are weighted ``name_weight``× as unigrams +
            ``name_bigram_weight``× as bigrams (F769 title-vs-definition). Pass
            ``None`` for a query utterance.
        name_weight: unigram repeat count for name tokens (default 3).
        name_bigram_weight: bigram repeat count for name tokens (default 2).
        func_frac: gate threshold as a fraction of ``n_docs`` (default 0.35).
        token_mode: per-token vector backend. ``"byteglyph"`` (default) =
            :func:`~srmech.amsc.hdc.klein4_encode_bytes`, the STRUCTURE-BEARING
            COMPOSED regime that preserves morphology (F1260). ``"address"`` =
            :func:`~srmech.amsc.hdc.klein4_address`, the F1008 fast ADDRESSED
            dual (orthogonal per token, NO morphology — not structure-bearing).

    Returns:
        HV: the aboutness hypervector (sectors=4).
    """
    D = int(D)
    if D <= 0:
        raise ValueError("encode_aboutness: D must be positive")
    if token_mode not in ("byteglyph", "address"):
        raise ValueError(
            "encode_aboutness: token_mode must be 'byteglyph' (default — the "
            "structure-bearing klein4_encode_bytes; F1260) or 'address' (the "
            f"F1008 orthogonal klein4_address dual); got {token_mode!r}")
    if df is not None and n_docs is None:
        raise ValueError(
            "encode_aboutness: n_docs is required when a df table is given "
            "(the gate threshold is int(n_docs * func_frac))")
    func = int((n_docs or 0) * func_frac)

    cache: dict[str, HV] = {}

    def vec(w):
        v = cache.get(w)
        if v is None:
            v = (hdc.klein4_encode_bytes(w, D) if token_mode == "byteglyph"
                 else hdc.klein4_address(D, w))
            cache[w] = v
        return v

    def bigrams(ws):
        # adjacency bind = order-aware, NOT a bag (feedback_never_bag_of_words)
        return [hdc.klein4_bind(vec(a), vec(b)) for a, b in zip(ws, ws[1:])]

    parts: list[HV] = []
    if name:
        nmw = _aboutness_tokens(name)          # identity tokens: NEVER gated
        parts += [vec(w) for w in nmw] * name_weight
        parts += bigrams(nmw) * name_bigram_weight
    body = [w for w in _aboutness_tokens(text) if _gate_keep(w, df, func)]
    parts += [vec(w) for w in body]
    parts += bigrams(body)

    if not parts:
        parts = [vec("_")]                    # fixed neutral atom for empty input
    return _bundle_odd(parts, D)


#: A FIXED, content-orthogonal neutral pad label. Encoded via the ADDRESSED
#: regime (``klein4_address``) so the pad sits at the 0.25 floor against every
#: real content token — it breaks an even-count tie WITHOUT biasing the bundle
#: toward any token's bytes (a byteglyph pad would share structure with content).
_PAD_LABEL = "\x00__srmech_aboutness_bundle_pad__"


def _bundle_odd(vecs, D):
    """Majority bundle with an odd-count guarantee. ``klein4_bundle`` resolves an
    even tie deterministically to 0; F1008 (via ``ContextSubstrate.bundle_odd``)
    APPENDS a fixed neutral pad on an even count instead — never biasing the tie
    — so this encoder reproduces that recipe. A single vector bundles to itself.

    The pad is a ``klein4_address`` atom (the orthogonal ADDRESSED regime) — a
    ROLE here, not content — so it is deliberately NOT structure-bearing."""
    if len(vecs) == 1:
        return vecs[0]
    if len(vecs) % 2 == 0:
        vecs = list(vecs) + [hdc.klein4_address(D, _PAD_LABEL)]  # fixed neutral pad
    return hdc.klein4_bundle(*vecs)


def ground_tool_schema(utterance, *, D=8192, k=3, token_mode="byteglyph"):
    """One-call convenience: "which srmech op does this utterance ask for?"

    Fits the doc-frequency gate over the LIVE ``tool_schema`` (each tool's
    name-leaf + summary is a document), encodes every tool with
    :func:`encode_aboutness` (name-weighted), encodes the ``utterance`` as a
    gated query, and returns the top-``k`` ``(tool_name, similarity)`` by
    :func:`~srmech.amsc.hdc.klein4_similarity`, best first. This is the F1009
    "srmech-drive" grounding surface built on the encoder primitive — a helper,
    not a separate registered tool.
    """
    from srmech.amsc import tool_schema as ts

    tools = ts.get_tool_schema().tools
    docs = [_aboutness_tokens(t.name.split(".")[-1]) + _aboutness_tokens(t.summary)
            for t in tools]
    df, n_docs = _doc_frequencies(docs)
    index = [
        (t.name, encode_aboutness(t.summary, D=D, df=df, n_docs=n_docs,
                                  name=t.name.split(".")[-1], token_mode=token_mode))
        for t in tools
    ]
    q = encode_aboutness(utterance, D=D, df=df, n_docs=n_docs,
                         token_mode=token_mode)

    def _fl(x):
        return x.as_float() if hasattr(x, "as_float") else float(x)

    scored = sorted(
        ((_fl(hdc.klein4_similarity(q, v)), name) for name, v in index),
        reverse=True,
    )
    return [(name, score) for score, name in scored[:k]]
