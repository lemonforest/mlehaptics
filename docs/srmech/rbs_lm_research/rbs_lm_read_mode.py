"""R-RBS-LM-45 — Read-mode interrogative cleanup.

Tests user 2026-05-26 reading-phenomenology hypothesis: cascade may store
content correctly (gist / relationships-of-relationships) but single-pass
write-mode argmin is the WRONG INFERENCE PROTOCOL. Read-mode is k-NN
retrieval against a pre-encoded candidate corpus + recognition scoring.

Per `[[user_stance_ai_is_not_a_substrate]]`: cascade is still a transducer.
This partition does NOT anthropomorphize the cascade — read-mode is a
different inference protocol over the same substrate, NOT a "cognitive"
operation. DeepSeek-style "the cascade's honesty demanding a hearing" or
"your mind as existence proof" framings explicitly stripped.

Three read-mode operations beyond write-mode argmin:

  1. top_k_distribution(instrument, query, k=20):
     Instead of `argmin Hamming` (returning byte), return the full top-k
     distribution. This reveals whether the cascade has ONE strong
     attractor (mode-collapse confirmed) or a SPREAD of candidates
     (content might be there, just not surfaced by argmin).

  2. phrase_match_retrieval(instrument, query, phrase_corpus):
     Pre-encode N candidate phrases as their context-vectors. At query
     time, probe the instrument with the query; compare the probe output
     to each pre-encoded phrase vector via Hamming. Return ranked
     candidates. This is k-NN retrieval at the relationship level, NOT
     byte level.

  3. recognition_score(instrument, query, expected_answer):
     Given a query and a candidate "right answer", measure how well the
     cascade's probe-response aligns with that expected answer. Direct
     test of "is the answer there if we know what to look for?"

Falsifiable predictions:
  - If phrase_match_retrieval consistently returns semantically appropriate
    candidates (right answer in top-K) → cascade DOES store content; write-
    mode was wrong query protocol
  - If phrase_match_retrieval returns random-ranked candidates → cascade
    truly mode-collapsed; substrate-bound at this scale

Usage:
    from rbs_lm_read_mode import (
        load_instrument, top_k_distribution,
        phrase_match_retrieval, recognition_score,
    )
"""

import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_encoder import CONTEXT_WINDOW, D, bind  # noqa: E402
from rbs_lm_bytes import (  # noqa: E402
    compute_byte_vocab_table, encode_context_bytes,
    vectorised_cleanup_bytes, text_to_bytes,
)


def hamming(a: bytes, b: bytes) -> int:
    """Bit-Hamming distance between two D/8-byte hypervectors."""
    a_np = np.frombuffer(a, dtype=np.uint8)
    b_np = np.frombuffer(b, dtype=np.uint8)
    return int(np.bitwise_count(a_np ^ b_np).sum())


def similarity(a: bytes, b: bytes, D: int = D) -> float:
    """Normalized similarity in [-1, +1]; +1 = identical, ~0 = random."""
    return 1.0 - 2.0 * hamming(a, b) / D


# -------------------------------------------------------------------------
# Operation 1: top_k distribution
# -------------------------------------------------------------------------

def top_k_distribution(instrument, query_text, vocab_table, D=D, k=20):
    """For a single query, return the top-K byte candidates with their
    similarities. Write-mode is k=1; read-mode here uses k=20 to expose
    the activation distribution."""
    query_bytes = text_to_bytes(query_text)
    ctx = query_bytes[-CONTEXT_WINDOW:] if len(query_bytes) > CONTEXT_WINDOW else query_bytes
    ctx_vec = encode_context_bytes(ctx, vocab_table, D)
    cand = bind(instrument, ctx_vec)
    return vectorised_cleanup_bytes(cand, vocab_table, D, top_k=k)


def distribution_stats(top_k_results):
    """Measure 'mode-collapse-ness' of a top-k distribution.
    - max_sim: the top-1 similarity
    - top1_minus_top10: gap between top-1 and top-10 (high = sharp peak; low = spread)
    - bytes_concentrated: are top-K all clustered to common bytes (' ', 'e', etc.)?
    """
    if not top_k_results:
        return {}
    sims = [s for (_, s) in top_k_results]
    max_sim = sims[0]
    if len(sims) >= 10:
        spread = sims[0] - sims[9]
    else:
        spread = sims[0] - sims[-1]

    # Byte-class concentration: is the top-K dominated by ASCII-letter / space / common?
    top_bytes = [b for (b, _) in top_k_results]
    common_count = sum(1 for b in top_bytes if b == 32 or 97 <= b <= 122 or 65 <= b <= 90)
    common_frac = common_count / max(len(top_bytes), 1)

    return {
        "top1_sim": round(max_sim, 4),
        "top1_minus_top10_spread": round(spread, 4),
        "common_byte_frac": round(common_frac, 3),
    }


# -------------------------------------------------------------------------
# Operation 2: phrase-level retrieval (k-NN over pre-encoded phrase vectors)
# -------------------------------------------------------------------------

def encode_phrase_as_vector(phrase, vocab_table, D=D):
    """Encode a phrase as a context vector (the same operation that turns
    a query prompt into a query vector). This is what the cascade uses to
    represent the phrase internally."""
    phrase_bytes = text_to_bytes(phrase)
    ctx = phrase_bytes[-CONTEXT_WINDOW:] if len(phrase_bytes) > CONTEXT_WINDOW else phrase_bytes
    return encode_context_bytes(ctx, vocab_table, D)


def phrase_match_retrieval(instrument, query_text, phrase_corpus, vocab_table, D=D):
    """Probe the instrument with `query_text`; rank `phrase_corpus`
    candidates by their similarity to the probe response.

    The premise: when the cascade probes with a query, the resulting
    candidate vector (bind(instrument, query_vec)) is the cascade's
    response. If that response is closer to phrase_corpus[i] than to
    phrase_corpus[j], the cascade "prefers" candidate i for this query.
    This is recognition-cued retrieval at the relationship level.

    Returns: list of (phrase, similarity) sorted by similarity DESCENDING.
    """
    query_bytes = text_to_bytes(query_text)
    ctx = query_bytes[-CONTEXT_WINDOW:] if len(query_bytes) > CONTEXT_WINDOW else query_bytes
    query_vec = encode_context_bytes(ctx, vocab_table, D)
    cand = bind(instrument, query_vec)  # the cascade's probe response

    # Pre-encode each phrase (this could be cached for repeated queries)
    scored = []
    for phrase in phrase_corpus:
        phrase_vec = encode_phrase_as_vector(phrase, vocab_table, D)
        sim = similarity(cand, phrase_vec, D)
        scored.append((phrase, sim))

    scored.sort(key=lambda x: -x[1])
    return scored


# -------------------------------------------------------------------------
# Operation 3: recognition score (does cascade align with expected answer?)
# -------------------------------------------------------------------------

def recognition_score(instrument, query_text, expected_answer, vocab_table, D=D):
    """How well does the cascade's probe-response align with the expected
    answer for this query?

    Computes: similarity(cascade_probe_response, encode_phrase_as_vector(expected_answer))

    A high similarity means: even if write-mode picks a different byte,
    the cascade's response-vector IS close to the expected answer's
    vector. This is the recognition signal — 'I knew this when reminded.'
    """
    query_bytes = text_to_bytes(query_text)
    ctx = query_bytes[-CONTEXT_WINDOW:] if len(query_bytes) > CONTEXT_WINDOW else query_bytes
    query_vec = encode_context_bytes(ctx, vocab_table, D)
    cand = bind(instrument, query_vec)

    expected_vec = encode_phrase_as_vector(expected_answer, vocab_table, D)
    return similarity(cand, expected_vec, D)


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def load_instrument_bytes(path):
    return Path(path).read_bytes()


def baseline_random_phrase_sim(phrase_corpus, vocab_table, D=D, n_samples=100, seed=42):
    """Baseline: what's the typical similarity between RANDOM pairs of
    phrase vectors? Establishes a noise floor for the retrieval task."""
    rng = np.random.default_rng(seed)
    vectors = [encode_phrase_as_vector(p, vocab_table, D) for p in phrase_corpus]
    sims = []
    for _ in range(n_samples):
        i, j = rng.integers(0, len(vectors)), rng.integers(0, len(vectors))
        if i != j:
            sims.append(similarity(vectors[i], vectors[j], D))
    return {
        "mean": round(float(np.mean(sims)), 4),
        "std": round(float(np.std(sims)), 4),
        "max": round(float(np.max(sims)), 4),
        "min": round(float(np.min(sims)), 4),
        "n_samples": len(sims),
    }


if __name__ == "__main__":
    # Quick self-test against v44 turtle-walk instrument (most constrained;
    # cleanest test case for read-mode)
    import json

    INSTRUMENT_PATH = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v44_turtle_walk.bin"
    CORPUS_PATH = "docs/srmech/rbs_lm_research/turtle_walk_corpus.json"

    print(f"=== R-RBS-LM-45 self-test on v44 turtle-walk ===")
    instrument = load_instrument_bytes(INSTRUMENT_PATH)
    print(f"  instrument loaded: {len(instrument)} bytes")
    vocab_table = compute_byte_vocab_table(D)
    print(f"  vocab table: {vocab_table.shape}")

    corpus = json.load(open(CORPUS_PATH))
    pairs = corpus["pairs"]
    print(f"  corpus: {len(pairs)} (english, logo) pairs")

    # Phrase corpus: the LOGO commands (the candidates the cascade SHOULD
    # surface for each English query if it stored the mapping correctly)
    logo_phrases = [p["logo"] for p in pairs]
    unique_logo = list(set(logo_phrases))
    print(f"  unique LOGO commands: {len(unique_logo)}")

    # Baseline random sim across pre-encoded LOGO commands
    print(f"\n  === Baseline random pairwise sim between LOGO phrase vectors ===")
    baseline = baseline_random_phrase_sim(unique_logo, vocab_table, D)
    print(f"    mean={baseline['mean']:+.4f}, std={baseline['std']:.4f}, "
          f"min={baseline['min']:+.4f}, max={baseline['max']:+.4f}")

    print(f"\n  === Top-k distribution (write-mode equivalent at k=20) ===")
    for query in ["walk forward 100", "draw a square", "draw a star (OOD)"]:
        top_k = top_k_distribution(instrument, query, vocab_table, D, k=20)
        stats = distribution_stats(top_k)
        print(f"    query: {query!r}")
        print(f"      top-5 byte candidates: {[(chr(b) if 32<=b<127 else f'\\x{b:02x}', round(s,3)) for (b,s) in top_k[:5]]}")
        print(f"      stats: {stats}")

    print(f"\n  === Phrase-match retrieval (read-mode k-NN over LOGO commands) ===")
    for i, p in enumerate(pairs[:6]):
        query = p["english"]
        expected = p["logo"]
        ranked = phrase_match_retrieval(instrument, query, unique_logo, vocab_table, D)
        # Find rank of the expected answer
        try:
            expected_rank = next(idx for idx, (phr, _) in enumerate(ranked) if phr == expected)
        except StopIteration:
            expected_rank = -1
        top3 = [(phr[:30], round(s, 3)) for phr, s in ranked[:3]]
        print(f"    query: {query!r}")
        print(f"      expected: {expected!r}")
        print(f"      expected rank: {expected_rank + 1}/{len(unique_logo)}")
        print(f"      top-3 retrieved: {top3}")

    print(f"\n  === Recognition score (how well does cascade align with expected?) ===")
    rec_sims = []
    for p in pairs:
        rs = recognition_score(instrument, p["english"], p["logo"], vocab_table, D)
        rec_sims.append(rs)
    print(f"    n={len(rec_sims)} (english, logo) pairs")
    print(f"    mean recognition sim: {np.mean(rec_sims):+.4f}")
    print(f"    std:                  {np.std(rec_sims):.4f}")
    print(f"    max:                  {max(rec_sims):+.4f}")
    print(f"    min:                  {min(rec_sims):+.4f}")
    print(f"    >0.1 (signal):        {sum(1 for r in rec_sims if r > 0.1)}/{len(rec_sims)}")
    print(f"    (compare to baseline mean {baseline['mean']:+.4f}; "
          f"recognition > baseline → read-mode signal)")
