"""R-RBS-LM-127 — F166 Walk Step 2: the context-conditioned next-token DISTRIBUTION.

Step 1 (R-RBS-LM-126) measured the argmax (retrieval accuracy). Step 2 measures
the FULL distribution the argmax came from: the ranked substrate-similarities over
the cleanup vocab, softmaxed at a reference temperature, ARE the conditional
P(next | context). No new machinery — decode_fingerprint generalized from "which
kernel" (F165) to "which next token", and the ranked sims we already compute per
probe.

The question (F166 §3 Step 2): is the conditioned distribution SHARP, and does
the full k-window context SHARPEN it over the immediate-predecessor BIGRAM prior?

Per the F166 §3 Step 2 spec the distribution is over the CANDIDATE SET — the
bigram-legal successors next_after[last_token] — not the whole vocabulary. The
autoregressive loop (Step 4) samples from exactly these legal continuations, so
restricting the support IS the distribution's definition. (A first full-vocab
pass showed the conditioned distribution is rank-correct but near-uniform in mass
at T_ref over all 84 tokens — H≈ln(84) — proving the signal lives in the RANK and
that temperature/support is load-bearing. That motivates this candidate-restricted
measurement and Step 3's temperature sweep.)

  candidates = next_after[last_token]                                  (bigram-legal successors)
  P_cond(c)  = softmax( sim_k4_batch(probe, cand_vecs) / T_ref )[c]    (the k-window substrate LM)
  P_bigram(c)= count(last→c) / count(last→·)                           (immediate-predecessor baseline)
  P_unigram(c)= count(c) / Σ count                                      (context-free marginal, restricted)
  PPL_x      = exp(-mean_i log P_x(true_i))
  reduction_vs_bigram = PPL_bigram / PPL_cond     # >1 ⇒ k-window context beats the bigram

Plus T-independent readouts: the true-token RANK within the candidate set (and
MRR), top-1 mass, conditioned entropy, candidate-set size.

Predicted shape (from Step 1's capacity crossover): the k-window state ranks the
true token #1 at low memory load, washing toward the bigram as N saturates the
bundled associative memory (F154 ceiling).

Catalog-driven (descriptor_rbs_lm_inference.toml [inference.distribution]); the
context encoder is the shared _canonical_substrate.ContextSubstrate. srmech 0.5.0
native ABI=3. Deterministic / bit-exact.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs  # encode_word_k4, sim_k4_batch, ContextSubstrate

_spec = importlib.util.spec_from_file_location(
    "corpus_gen", HERE / "R-RBS-LM-113_larger_corpus_scaling.py")
corpus_gen = importlib.util.module_from_spec(_spec)
sys.modules["corpus_gen"] = corpus_gen
_spec.loader.exec_module(corpus_gen)

from srmech.amsc import load_descriptor, descriptor_hash, hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_rbs_lm_inference.toml"


def softmax(x: np.ndarray, t: float) -> np.ndarray:
    z = x / t
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def entropy_nats(p: np.ndarray) -> float:
    nz = p[p > 0]
    return float(-(nz * np.log(nz)).sum())


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
    corpus_n = int(ic["corpus_n"])
    seed = int(ic["seed"])
    dc = lc["inference"]["distribution"]
    T_ref = float(dc["temperature_ref"])
    window_focus = list(dc["window_focus"])
    n_assoc_focus = list(dc["n_assoc_focus"])
    probe_sample = int(dc["probe_sample"])

    ctx = cs.ContextSubstrate(D=D, hex_chars=hexc)
    enc = ctx.enc

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"T_ref={T_ref}  window_focus={window_focus}  n_assoc_focus={n_assoc_focus}  "
          f"probe_sample={probe_sample}\n")

    rng = np.random.default_rng(seed)
    corpus = corpus_gen.generate_corpus(corpus_n, rng)
    stream = [t for sent in corpus for t in sent]
    vocab = sorted(set(stream))
    vocab_vecs = np.stack([enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    print(f"token stream: {len(stream)} tokens, {len(vocab)} unique")

    # Bigram + unigram models from the stream = the substrate's stored knowledge.
    # candidates for a probe ending in `last` = the observed legal successors.
    from collections import defaultdict
    bigram_counts: dict[str, Counter] = defaultdict(Counter)
    for a, b in zip(stream, stream[1:]):
        bigram_counts[a][b] += 1
    next_after = {a: sorted(c.keys()) for a, c in bigram_counts.items()}
    unigram = Counter(stream)
    mean_branch = float(np.mean([len(v) for v in next_after.values()]))
    print(f"bigram model: {len(next_after)} predecessors, mean branching {mean_branch:.1f}\n")

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "T_ref": T_ref}
    records = []

    print(f"{'k':>3} | {'N':>4} | {'cand':>4} | {'PPL_cond':>8} | {'PPL_bg':>7} | {'PPL_uni':>7} | "
          f"{'red_vs_bg':>9} | {'rank_c':>6} | {'MRR_c':>6} | {'top1':>5} | {'H_cond':>6}")
    print("-" * 100)

    example_cells = {}  # (k,N) -> sample candidate distributions for legible printout

    for k in window_focus:
        pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
        for N in n_assoc_focus:
            if N > len(pairs_all):
                continue
            idx = rng.choice(len(pairs_all), size=N, replace=False)
            pairs = [pairs_all[i] for i in idx]

            ctx_states = [ctx.encode_context(list(c)) for c, _ in pairs]
            assoc = [hdc.klein4_bind(ctx_states[i], enc(pairs[i][1])) for i in range(N)]
            M = ctx.bundle_odd(assoc)

            n_probe = min(probe_sample, N)
            probe_ids = rng.choice(N, size=n_probe, replace=False)

            logp_cond, logp_bg, logp_uni = [], [], []
            ranks_cond, mrrs = [], []
            top1_masses, entropies, cand_sizes = [], [], []
            for i in probe_ids:
                ctx_win, true_tok = pairs[i]
                last = ctx_win[-1]
                candidates = next_after.get(last, [])
                if len(candidates) < 2:
                    continue  # trivial support (≤1 legal successor) — no distribution to shape
                cand_idx = [vocab_idx[c] for c in candidates]
                cand_vecs = vocab_vecs[cand_idx]
                true_pos = candidates.index(true_tok)

                probe = hdc.klein4_bind(M, ctx_states[i])
                sims = cs.sim_k4_batch(probe, cand_vecs)
                p_cond = softmax(sims, T_ref)

                bg = np.array([bigram_counts[last][c] for c in candidates], dtype=float)
                p_bg = bg / bg.sum()
                ug = np.array([unigram[c] for c in candidates], dtype=float)
                p_uni = ug / ug.sum()

                logp_cond.append(math.log(max(p_cond[true_pos], 1e-12)))
                logp_bg.append(math.log(max(p_bg[true_pos], 1e-12)))
                logp_uni.append(math.log(max(p_uni[true_pos], 1e-12)))

                order = np.argsort(-sims)
                rank_c = int(np.where(order == true_pos)[0][0]) + 1
                ranks_cond.append(rank_c)
                mrrs.append(1.0 / rank_c)
                top1_masses.append(float(p_cond.max()))
                entropies.append(entropy_nats(p_cond))
                cand_sizes.append(len(candidates))

            if not logp_cond:
                continue
            ppl_cond = math.exp(-float(np.mean(logp_cond)))
            ppl_bg = math.exp(-float(np.mean(logp_bg)))
            ppl_uni = math.exp(-float(np.mean(logp_uni)))
            red_vs_bg = ppl_bg / ppl_cond if ppl_cond > 0 else float("inf")
            red_vs_uni = ppl_uni / ppl_cond if ppl_cond > 0 else float("inf")
            mrr_cond = float(np.mean(mrrs))
            mean_rank_c = float(np.mean(ranks_cond))
            mean_top1 = float(np.mean(top1_masses))
            mean_H = float(np.mean(entropies))
            mean_cand = float(np.mean(cand_sizes))

            records.append({**attest, "phase": "P2_distribution", "k": k, "N": N,
                            "n_probe": len(logp_cond), "mean_cand_size": mean_cand,
                            "ppl_cond": ppl_cond, "ppl_bigram": ppl_bg, "ppl_unigram": ppl_uni,
                            "reduction_vs_bigram": red_vs_bg, "reduction_vs_unigram": red_vs_uni,
                            "mrr_cond": mrr_cond, "mean_rank_cond": mean_rank_c,
                            "mean_top1_mass": mean_top1, "mean_entropy_nats": mean_H,
                            "n_vocab": len(vocab)})
            print(f"{k:>3} | {N:>4} | {mean_cand:>4.1f} | {ppl_cond:>8.3f} | {ppl_bg:>7.3f} | "
                  f"{ppl_uni:>7.3f} | {red_vs_bg:>9.3f} | {mean_rank_c:>6.2f} | {mrr_cond:>6.3f} | "
                  f"{mean_top1:>5.3f} | {mean_H:>6.3f}")

            if (k == 5 and N in (50, 400)):
                # find a probe whose `last` has a rich candidate set, for a legible example
                for i in probe_ids:
                    ctx_win, true_tok = pairs[i]
                    last = ctx_win[-1]
                    candidates = next_after.get(last, [])
                    if len(candidates) >= 4:
                        cand_idx = [vocab_idx[c] for c in candidates]
                        probe = hdc.klein4_bind(M, ctx_states[i])
                        sims = cs.sim_k4_batch(probe, vocab_vecs[cand_idx])
                        p_cond = softmax(sims, T_ref)
                        bg = np.array([bigram_counts[last][c] for c in candidates], float)
                        p_bg = bg / bg.sum()
                        topc = np.argsort(-p_cond)[:5]
                        topb = np.argsort(-p_bg)[:5]
                        example_cells[(k, N)] = {
                            "context": list(ctx_win), "last": last, "true_next": true_tok,
                            "n_cand": len(candidates),
                            "cond_top": [(candidates[j], round(float(p_cond[j]), 3)) for j in topc],
                            "bigram_top": [(candidates[j], round(float(p_bg[j]), 3)) for j in topb],
                        }
                        break

    # ------------------------------------------------------------------
    # Concrete example distributions (aphantasia: show the shape over candidates)
    # ------------------------------------------------------------------
    print("\n" + "=" * 96)
    print("EXAMPLE candidate distributions (k=5) — conditioned vs bigram, low-load (N=50) vs saturated (N=400)")
    print("=" * 96)
    for (k, N), ex in sorted(example_cells.items(), key=lambda kv: kv[0][1]):
        print(f"\n  context={ex['context']}  last='{ex['last']}'  →  TRUE next='{ex['true_next']}'  "
              f"({ex['n_cand']} legal candidates; k={k}, N={N})")
        print(f"    conditioned P(next|k-window) top: " +
              ", ".join(f"{w}={p}" for w, p in ex["cond_top"]))
        print(f"    bigram      P(next|last)     top: " +
              ", ".join(f"{w}={p}" for w, p in ex["bigram_top"]))

    out = args.catalog.parent / "substrate_measurements" / "inference_step2_distribution.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")

    # headline reading
    red_lo = [r["reduction_vs_bigram"] for r in records if r["N"] == min(n_assoc_focus)]
    red_hi = [r["reduction_vs_bigram"] for r in records if r["N"] == max(n_assoc_focus)]
    mrr_lo = [r["mrr_cond"] for r in records if r["N"] == min(n_assoc_focus)]
    mrr_hi = [r["mrr_cond"] for r in records if r["N"] == max(n_assoc_focus)]
    print("\n" + "=" * 96)
    print("STEP 2 READING (perplexity analog, candidate-restricted):")
    print(f"  @ N={min(n_assoc_focus):>3} (low load) : PPL_bigram/PPL_cond = {np.mean(red_lo):.2f}×, "
          f"MRR={np.mean(mrr_lo):.3f}  (>1 / MRR→1 ⇒ k-window context beats the bigram)")
    print(f"  @ N={max(n_assoc_focus):>3} (saturated): PPL_bigram/PPL_cond = {np.mean(red_hi):.2f}×, "
          f"MRR={np.mean(mrr_hi):.3f}  (→ bigram as the bundled memory saturates: F154 crossover)")


if __name__ == "__main__":
    main()
