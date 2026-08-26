"""R-RBS-LM-126 — F166 Walk Step 1: rolling context-state encoder + capacity.

The inference substrate's "hidden state": the last-k tokens encoded into ONE
Klein-4 state via positional role-filler binding (iω₇-style position keys), then
queried for the next token. The capacity question: how many (context→next) pairs
can ONE bundled associative memory hold, and how does context length k affect it,
before true-next-token retrieval degrades? That number IS the substrate's
bit-exact "context window".

Native cascade (28D, bit-exact):
  context_state = bundle_p [ klein4_bind(pos_key(p), encode(token_p)) ]   (Class A∘M + position)
  memory M      = bundle_i [ klein4_bind(context_state_i, encode(next_i)) ]  (associative store)
  retrieve      = cleanup_argmax_over_vocab( klein4_bind(M, context_state_q) )  (Class M unbind+argmax)

Klein-4 XOR is self-inverse, so bind(bind(cs_i, next_i), cs_q) = next_i when q==i
(cs_q⊕cs_q = identity) and noise otherwise; bundling N gives the true next once
plus (N-1) noise terms → capacity is the SNR crossover (the F154/F162 curve, now
for context→next associations).

Catalog-driven (descriptor_rbs_lm_inference.toml); srmech 0.5.0 native ABI=3.
Deterministic: same corpus + same catalog + same srmech_version → bit-exact.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs  # encode_word_k4, sim_k4_batch

_spec = importlib.util.spec_from_file_location(
    "corpus_gen", HERE / "R-RBS-LM-113_larger_corpus_scaling.py")
corpus_gen = importlib.util.module_from_spec(_spec)
sys.modules["corpus_gen"] = corpus_gen
_spec.loader.exec_module(corpus_gen)

from srmech.amsc import load_descriptor, descriptor_hash, hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_rbs_lm_inference.toml"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    D = int(lc["substrate"]["D"])
    hexc = int(lc["substrate"]["token_seed_hex_chars"])
    ic = lc["inference"]["context"]
    window_sweep = list(ic["window_sweep"])
    n_assoc_sweep = list(ic["n_assoc_sweep"])
    corpus_n = int(ic["corpus_n"])
    seed = int(ic["seed"])

    # rolling context-state encoder (shared substrate machinery; F166 hidden state)
    ctx = cs.ContextSubstrate(D=D, hex_chars=hexc)
    enc = ctx.enc
    encode_context = ctx.encode_context
    k4_bundle_odd = ctx.bundle_odd

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"window_sweep={window_sweep}  n_assoc_sweep={n_assoc_sweep}  corpus_n={corpus_n}\n")

    # Flat token stream from template corpus (deterministic)
    rng = np.random.default_rng(seed)
    corpus = corpus_gen.generate_corpus(corpus_n, rng)
    stream = [t for sent in corpus for t in sent]
    print(f"token stream: {len(stream)} tokens, {len(set(stream))} unique\n")

    # Cleanup vocabulary = all observed next-tokens (their encoded vectors)
    vocab = sorted(set(stream))
    vocab_vecs = np.stack([enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}

    # ------------------------------------------------------------------
    # Capacity sweep: for each (k, N) build a context→next associative
    # memory and measure true-next retrieval accuracy.
    # ------------------------------------------------------------------
    records = []
    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE}

    print(f"{'k':>3} | {'N':>5} | {'retrieval_acc':>13} | {'bigram_prior':>12} | {'lift':>6} | {'build_s':>7}")
    print("-" * 70)
    for k in window_sweep:
        # all (context_window, next) positions where a full k-window exists
        pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
        for N in n_assoc_sweep:
            if N > len(pairs_all):
                continue
            idx = rng.choice(len(pairs_all), size=N, replace=False)
            pairs = [pairs_all[i] for i in idx]

            t0 = time.time()
            # precompute context states + build associative memory
            ctx_states = [encode_context(list(ctx)) for ctx, _ in pairs]
            assoc = [hdc.klein4_bind(ctx_states[i], enc(pairs[i][1])) for i in range(N)]
            M = k4_bundle_odd(assoc)
            t_build = time.time() - t0

            # retrieval: unbind each context, cleanup-argmax over vocab
            correct = 0
            for i in range(N):
                probe = hdc.klein4_bind(M, ctx_states[i])
                sims = cs.sim_k4_batch(probe, vocab_vecs)
                if vocab[int(sims.argmax())] == pairs[i][1]:
                    correct += 1
            acc = correct / N

            # bigram prior baseline: predict the most common next-token overall
            # (context-free) — does context lift over this?
            from collections import Counter
            next_counts = Counter(nx for _, nx in pairs)
            prior_token, prior_n = next_counts.most_common(1)[0]
            bigram_prior = prior_n / N

            lift = acc - bigram_prior
            records.append({**attest, "phase": "P1_context_capacity", "k": k, "N": N,
                            "retrieval_acc": acc, "bigram_prior": bigram_prior,
                            "lift": lift, "build_seconds": t_build, "n_vocab": len(vocab)})
            print(f"{k:>3} | {N:>5} | {acc:>13.3f} | {bigram_prior:>12.3f} | "
                  f"{lift:>+6.3f} | {t_build:>7.2f}")

    # ------------------------------------------------------------------
    # Context distinguishability: do distinct contexts → distinct states?
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("Context distinguishability (mean pairwise sim of distinct context states)")
    print("=" * 70)
    print(f"{'k':>3} | {'mean_pairwise_sim':>17} | {'(random baseline ~0.25)':>24}")
    print("-" * 55)
    for k in window_sweep:
        pairs_all = [tuple(stream[i - k:i]) for i in range(k, len(stream))]
        uniq = list(dict.fromkeys(pairs_all))[:100]  # up to 100 distinct contexts
        states = np.stack([encode_context(list(c)) for c in uniq])
        sims = []
        for a in range(len(states)):
            row = cs.sim_k4_batch(states[a], states)
            sims.extend([row[b] for b in range(len(states)) if b != a])
        msim = float(np.mean(sims))
        records.append({**attest, "phase": "P1_context_distinguishability",
                        "k": k, "n_distinct": len(uniq), "mean_pairwise_sim": msim})
        print(f"{k:>3} | {msim:>17.4f} | {'distinct→distinct' if msim < 0.35 else 'COLLAPSING':>24}")

    out = args.catalog.parent / desc.schema["ndjson_file"]
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")


if __name__ == "__main__":
    main()
