"""R-RBS-LM-128 — F166 Walk Step 3: temperature = the sampling knob; the
recall/diversity tradeoff curve.

Step 2 returned the conditioned distribution at a single reference temperature.
Step 3 makes temperature the dial (the R-RBS-NN-14b soft-retrieval knob) and maps
what it trades:

  P_cond(c; T) = softmax( sim_k4_batch(probe, cand_vecs) / T )

  RECALL    = E[ 1{sample == true_next} ] = mean_i P_cond(true_i; T)
              (low T → replay the exact recorded continuation; the substrate as memory)
  DIVERSITY = mean effective-candidate-count = mean_i exp(H(P_cond(·; T)))
              (high T → sample more uniformly over the bigram-LEGAL candidates;
               still grammatical by construction, but creative, not pure replay)
  PPL(T)    = exp(-mean_i log P_cond(true_i; T))
              (minimized at the best-CALIBRATED temperature T* — the natural dial setting)

Every sample is drawn from next_after[last] (bigram-legal), so the whole sweep
stays coherent at the bigram level; T moves us along recall↔diversity WITHIN that
coherent envelope. The T* that minimizes perplexity is the substrate's
self-calibrated temperature; Step 4's autoregressive loop runs at a chosen T and
tests whether coherence holds over many steps.

Catalog-driven ([inference.sampling]); shared ContextSubstrate; srmech 0.5.0
ABI=3. Deterministic / bit-exact (seeded sampling).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs

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
    sc = lc["inference"]["sampling"]
    temps = list(sc["temperature_sweep"])
    k = int(sc["sweep_k"])
    N = int(sc["sweep_n_assoc"])
    n_draws = int(sc["n_sampled_draws"])
    sample_seed = int(sc["sample_seed"])

    ctx = cs.ContextSubstrate(D=D, hex_chars=hexc)
    enc = ctx.enc

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"sweep_k={k}  sweep_n_assoc={N}  temps={temps}  n_draws={n_draws}\n")

    rng = np.random.default_rng(seed)
    corpus = corpus_gen.generate_corpus(corpus_n, rng)
    stream = [t for sent in corpus for t in sent]
    vocab = sorted(set(stream))
    vocab_vecs = np.stack([enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}

    bigram_counts: dict[str, Counter] = defaultdict(Counter)
    for a, b in zip(stream, stream[1:]):
        bigram_counts[a][b] += 1
    next_after = {a: sorted(c.keys()) for a, c in bigram_counts.items()}

    # build ONE associative memory at the productive (k, N) cell
    pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
    idx = rng.choice(len(pairs_all), size=N, replace=False)
    pairs = [pairs_all[i] for i in idx]
    ctx_states = [ctx.encode_context(list(c)) for c, _ in pairs]
    assoc = [hdc.klein4_bind(ctx_states[i], enc(pairs[i][1])) for i in range(N)]
    M = ctx.bundle_odd(assoc)

    # precompute, per probe with ≥2 legal candidates: sims over candidates + true position
    probes = []
    for i in range(N):
        ctx_win, true_tok = pairs[i]
        last = ctx_win[-1]
        candidates = next_after.get(last, [])
        if len(candidates) < 2:
            continue
        cand_idx = [vocab_idx[c] for c in candidates]
        sims = cs.sim_k4_batch(hdc.klein4_bind(M, ctx_states[i]), vocab_vecs[cand_idx])
        probes.append({"candidates": candidates, "sims": sims,
                       "true_pos": candidates.index(true_tok), "last": last,
                       "context": list(ctx_win), "true": true_tok})
    print(f"probes with ≥2 legal candidates: {len(probes)} / {N}  "
          f"(mean cand {np.mean([len(p['candidates']) for p in probes]):.1f})\n")

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "k": k, "N": N}
    records = []
    draw_rng = np.random.default_rng(sample_seed)

    print(f"{'T':>6} | {'recall':>7} | {'PPL':>7} | {'eff_cand':>8} | {'H_nats':>7} | "
          f"{'top1':>5} | {'samp_recall':>11} | {'samp_uniq':>9}")
    print("-" * 85)
    for T in temps:
        recalls, ppls, effs, ents, top1s = [], [], [], [], []
        samp_hits, samp_uniq = [], []
        for p in probes:
            pc = softmax(p["sims"], T)
            tp = p["true_pos"]
            recalls.append(float(pc[tp]))
            ppls.append(-math.log(max(pc[tp], 1e-12)))
            H = entropy_nats(pc)
            ents.append(H)
            effs.append(math.exp(H))
            top1s.append(float(pc.max()))
            # realized seeded sampling: draw n_draws, measure recall + distinct tokens
            draws = draw_rng.choice(len(p["candidates"]), size=n_draws, p=pc)
            samp_hits.append(float(np.mean(draws == tp)))
            samp_uniq.append(len(set(draws.tolist())))
        mean_recall = float(np.mean(recalls))
        ppl = math.exp(float(np.mean(ppls)))
        mean_eff = float(np.mean(effs))
        mean_H = float(np.mean(ents))
        mean_top1 = float(np.mean(top1s))
        mean_samp_recall = float(np.mean(samp_hits))
        mean_samp_uniq = float(np.mean(samp_uniq))
        records.append({**attest, "phase": "P3_temperature", "T": T,
                        "expected_recall": mean_recall, "ppl": ppl,
                        "mean_eff_candidates": mean_eff, "mean_entropy_nats": mean_H,
                        "mean_top1_mass": mean_top1, "sampled_recall": mean_samp_recall,
                        "sampled_unique_tokens": mean_samp_uniq, "n_probes": len(probes)})
        print(f"{T:>6.3f} | {mean_recall:>7.3f} | {ppl:>7.3f} | {mean_eff:>8.2f} | "
              f"{mean_H:>7.3f} | {mean_top1:>5.3f} | {mean_samp_recall:>11.3f} | "
              f"{mean_samp_uniq:>9.2f}")

    # best-calibrated temperature
    t_star = min(records, key=lambda r: r["ppl"])
    print(f"\nT* (min perplexity, best-calibrated): T={t_star['T']}  "
          f"PPL={t_star['ppl']:.3f}  recall={t_star['expected_recall']:.3f}  "
          f"eff_cand={t_star['mean_eff_candidates']:.2f}")

    # ------------------------------------------------------------------
    # Concrete realized sampling at low / mid / high T (aphantasia: show it)
    # ------------------------------------------------------------------
    demo = next((p for p in probes if len(p["candidates"]) >= 5), probes[0])
    print("\n" + "=" * 84)
    print(f"REALIZED SAMPLING — context={demo['context']}  last='{demo['last']}'  TRUE='{demo['true']}'")
    print(f"  ({len(demo['candidates'])} legal candidates)")
    print("=" * 84)
    demo_rng = np.random.default_rng(sample_seed + 1)
    for T in [0.02, 0.1, 0.35, 1.0]:
        pc = softmax(demo["sims"], T)
        draws = demo_rng.choice(len(demo["candidates"]), size=12, p=pc)
        toks = [demo["candidates"][j] for j in draws]
        print(f"  T={T:<4}: " + " ".join(toks))

    out = args.catalog.parent / "substrate_measurements" / "inference_step3_temperature.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")

    print("\n" + "=" * 84)
    print("STEP 3 READING (recall ↔ diversity, all within the bigram-legal envelope):")
    lo, hi = records[0], records[-1]
    print(f"  T={lo['T']:<4} (cold): recall {lo['expected_recall']:.3f}, "
          f"eff_cand {lo['mean_eff_candidates']:.2f}  — replay (memory)")
    print(f"  T={hi['T']:<4} (hot) : recall {hi['expected_recall']:.3f}, "
          f"eff_cand {hi['mean_eff_candidates']:.2f}  — diverse (still grammatical)")
    print(f"  T*={t_star['T']} minimizes perplexity — the substrate's self-calibrated dial")


if __name__ == "__main__":
    main()
