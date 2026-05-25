"""R-RBS-LM-4 — Path B encoder for the silicon-LLM → RBS-HDC translation.

Operationalizes Path B (function-level encoding, per R-RBS-LM-2 §6.1) for
GPT-2-small at D=8192 (per R-RBS-LM-3 §4 source-model selection).

The encoder takes a list of (context_tokens, next_token) observations
harvested from the source model and produces a single hypervector — the
RBS-HDC instrument — that contains the bundled bindings.

The instrument is queryable: given a new context, the encoder's query()
method returns the predicted next-token via cleanup against the vocabulary.

This module is the SHAPE; R-RBS-LM-5 actually runs it on real GPT-2-small
output; R-RBS-LM-6 wraps it as the full inference cascade.

Usage:
    sys.path.insert(0, "docs/srmech/python")
    from docs.srmech.rbs_lm_research.rbs_lm_encoder import (
        encode_observation, hierarchical_bundle, query_next_token,
    )

Design decisions committed in this partition (per R-RBS-LM-4 REPORT):

  * Context window: 64 tokens (Kanerva sequence in a single bundle).
    Source model supports 1024; the gap is a known design constraint
    R-RBS-LM-7 measures for behavioral impact.
  * Hierarchical bundling: sub-groups of 257 (MAX_BUNDLE_N), then
    bundle-of-bundles recursively. Bundle is odd-N majority; pad with
    a known sentinel when even.
  * Sampling discipline: argmax only (R-RBS-LM-2 + R-RBS-LM-3 align).
    Top-k recording is deferred to R-RBS-LM-8 if behavior fidelity needs it.
  * Vocabulary embedding: srmech-native Class A content-mint of
    f"LoE.vocab.{token_id}" (NOT the source-model's learned embedding).
    Per R-RBS-LM-2 Finding 6 — the substrate-native embedding IS the mint;
    the source model's embedding was Mechanism 2 residue.
"""

import sys
from typing import Sequence

sys.path.insert(0, "docs/srmech/python")

from srmech.amsc.hdc import bind, bundle, similarity  # noqa: E402
from srmech.signal_processing.rbs_hdc_instrument import (  # noqa: E402
    D_DEFAULT,
    mint_vector,
)


# ---- design constants --------------------------------------------------
D = D_DEFAULT                  # 8192 bits per srmech Spike #170
CONTEXT_WINDOW = 64            # tokens per single Kanerva bundle
MAX_BUNDLE_N = 257             # srmech MAX_BUNDLE_N (odd; coprime to D=2^13)


# ---- vocabulary + position mint caches (lazy) -------------------------
_vocab_cache: dict[int, bytes] = {}
_position_cache: dict[int, bytes] = {}
_sentinel_cache: dict[str, bytes] = {}


def vocab_vec(token_id: int, D: int = D) -> bytes:
    """Class A content-mint for a vocabulary token id."""
    if token_id not in _vocab_cache:
        _vocab_cache[token_id] = mint_vector(f"LoE.vocab.{token_id}", D=D)
    return _vocab_cache[token_id]


def position_vec(pos: int, D: int = D) -> bytes:
    """Class A content-mint for a sequence position."""
    if pos not in _position_cache:
        _position_cache[pos] = mint_vector(f"LoE.position.{pos}", D=D)
    return _position_cache[pos]


def sentinel(name: str, D: int = D) -> bytes:
    """Class A content-mint for a named sentinel (padding, empty, etc.)."""
    if name not in _sentinel_cache:
        _sentinel_cache[name] = mint_vector(f"LoE.sentinel.{name}", D=D)
    return _sentinel_cache[name]


# ---- core encoder ------------------------------------------------------
def encode_context(token_ids: Sequence[int], D: int = D) -> bytes:
    """Kanerva sequence representation per R-RBS-NN-5 §3.1.

    For each position k in token_ids, compute bind(vocab(token_k), position_k)
    and bundle them. Returns a single hypervector representing the context.

    If len(token_ids) is even, pad with sentinel('context.pad') to make
    bundle's odd-N requirement satisfied.

    NOTE: token_ids beyond CONTEXT_WINDOW are silently truncated to the
    most-recent CONTEXT_WINDOW. Sliding-window hierarchical sequence is
    deferred to R-RBS-LM-8 (if R-RBS-LM-7 finds the short window degrades
    behavior unacceptably).
    """
    if len(token_ids) > CONTEXT_WINDOW:
        token_ids = list(token_ids[-CONTEXT_WINDOW:])
    n = len(token_ids)
    if n == 0:
        return sentinel("empty_context", D)
    binds = [bind(vocab_vec(int(tid), D), position_vec(k, D))
             for k, tid in enumerate(token_ids)]
    if len(binds) == 1:
        return binds[0]
    if len(binds) % 2 == 0:
        binds.append(sentinel("context.pad", D))
    return bundle(binds)


def encode_observation(
    context_tokens: Sequence[int],
    next_token: int,
    D: int = D,
) -> bytes:
    """One behavioral observation: bind(context_vec, next_token_vec).

    This is the canonical Path B binding (R-RBS-LM-2 §4.2):
    encode HOW the source model maps context to next-token, NOT WHAT
    the source model's weights ARE.
    """
    ctx = encode_context(context_tokens, D)
    nxt = vocab_vec(int(next_token), D)
    return bind(ctx, nxt)


def hierarchical_bundle(
    vectors: Sequence[bytes],
    group_size: int = MAX_BUNDLE_N,
    D: int = D,
    _depth: int = 0,
) -> bytes:
    """Bundle list larger than MAX_BUNDLE_N via hierarchical sub-bundles.

    Splits vectors into groups of <= group_size, bundles each group,
    then recurses on the sub-bundles. Per R-RBS-NN-7 §3.2 hierarchical
    bundling — the structural workaround for n > srmech MAX_BUNDLE_N.

    Each hierarchy level carries an additional bundle-projection cost
    (per MFO §VII.1.3 line 741 ~6.9% per layer if bundle is averaging).
    Deep hierarchies compound this cost; R-RBS-LM-7 measures the impact.
    """
    if len(vectors) == 0:
        return sentinel("empty_bundle", D)
    if len(vectors) == 1:
        return vectors[0]
    if len(vectors) <= group_size:
        vlist = list(vectors)
        if len(vlist) % 2 == 0:
            vlist.append(sentinel(f"bundle.pad.depth{_depth}", D))
        return bundle(vlist)
    # Recurse: split into sub-groups; bundle each; bundle the sub-bundles
    # Leave one slot per sub-group for the pad (so group of 256 effective).
    effective_group = group_size - 1
    sub_bundles: list[bytes] = []
    for i in range(0, len(vectors), effective_group):
        group = list(vectors[i: i + effective_group])
        if len(group) % 2 == 0:
            group.append(sentinel(f"bundle.pad.depth{_depth}", D))
        sub_bundles.append(bundle(group))
    return hierarchical_bundle(sub_bundles, group_size, D, _depth + 1)


def encode_corpus(
    observations: Sequence[tuple[Sequence[int], int]],
    D: int = D,
) -> bytes:
    """Encode a behavioral corpus of (context_tokens, next_token) observations
    into a single RBS-HDC instrument.

    This is the Path B encoder's main entry point. R-RBS-LM-5 calls this
    with observations harvested from running GPT-2-small over a text corpus.
    """
    bindings = [encode_observation(ctx, nxt, D)
                for ctx, nxt in observations]
    return hierarchical_bundle(bindings, D=D)


# ---- inference (used by R-RBS-LM-6) -----------------------------------
def query_next_token(
    instrument: bytes,
    context_tokens: Sequence[int],
    vocab_size: int,
    D: int = D,
    top_k: int = 1,
) -> list[tuple[int, float]]:
    """Query the instrument for next-token given context.

    Recovery is the canonical HDC unbind + cleanup:
        candidate = bind(instrument, context_vec)
        next_token = argmax_t similarity(candidate, vocab(t))

    NOTE: O(vocab_size) similarity calls per query. At vocab=50257
    pure-Python this is ~5 seconds per query. R-RBS-LM-6 optimises
    (batching; srmech-native if HAS_NATIVE; or Class L sub-decomposition
    per R-RBS-NN-6 §6 catalog l_laplacian_spectra slot).

    Returns list of (token_id, similarity) tuples, top_k entries,
    sorted by similarity descending.
    """
    ctx = encode_context(context_tokens, D)
    candidate = bind(instrument, ctx)
    scored: list[tuple[int, float]] = []
    for token_id in range(vocab_size):
        s = similarity(candidate, vocab_vec(token_id, D))
        scored.append((token_id, s))
    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]


# ---- self-test --------------------------------------------------------
def _self_test() -> None:
    """Algebraic POC: encode 5 observations; verify each recoverable."""
    print(f"=== R-RBS-LM-4 encoder self-test (D={D}) ===")

    # 5 toy observations: small contexts, tiny vocab
    observations = [
        ([100, 101, 102], 200),  # "abc → X"
        ([100, 101, 103], 201),  # "abd → Y"
        ([200, 201, 202], 300),  # "XYZ → P"
        ([200, 201, 203], 301),  # "XYW → Q"
        ([500, 501, 502], 600),  # "lmn → R"
    ]
    print(f"  encoding {len(observations)} observations...")
    instrument = encode_corpus(observations)
    print(f"  instrument: {len(instrument)} bytes ({len(instrument)*8} bits = D)")

    # Query each in-corpus context; check recovery
    # Small effective vocab for the test (the 5 next-tokens + a few distractors)
    test_vocab = sorted({nxt for _, nxt in observations} |
                       {nxt + 100 for _, nxt in observations})
    print(f"  test vocab (members + distractors): {test_vocab}")
    print()
    n_correct = 0
    for ctx, expected in observations:
        # Use a custom query restricted to test_vocab for the demo
        ctx_vec = encode_context(ctx)
        candidate = bind(instrument, ctx_vec)
        scored = [(t, similarity(candidate, vocab_vec(t))) for t in test_vocab]
        scored.sort(key=lambda x: -x[1])
        predicted, top_sim = scored[0]
        ok = predicted == expected
        n_correct += ok
        print(f"  ctx={ctx} → predicted {predicted} (sim {top_sim:+.4f}), "
              f"expected {expected}, {'OK' if ok else 'FAIL'}")
        if not ok:
            print(f"    top-3: {scored[:3]}")
    print(f"\n  Accuracy: {n_correct}/{len(observations)} "
          f"({100*n_correct/len(observations):.0f}%)")
    print()
    print("  Note: at 5 observations the bundle has plenty of capacity.")
    print("  Real GPT-2-small encoding (R-RBS-LM-5) will have ≫ 257 bindings;")
    print("  hierarchical_bundle() handles that case.")


if __name__ == "__main__":
    _self_test()
