"""R-RBS-LM-20 — Path C at D=32768 (4× current D=8192).

Tests whether dimensional capacity is the bottleneck in Path C's 3.3%
ceiling (R-RBS-LM-18 finding). Keeps everything else identical:
- Same WTE random-projection design (but R is now (32768, 768))
- Same Path B compute body (bind-with-position; Kanerva sequence; bundle)
- Same hallucination corpus
- Same encoding corpus (R-RBS-LM-14 ~20 KB → 491 obs)

Expected memory + latency cost: ~4× the D=8192 baseline.
- Vocab table: ~196 MB (vs 49 MB at D=8192)
- Per-token latency: ~720 ms estimated (vs 180 ms)
- Encode throughput: ~4 obs/s estimated (vs 15 obs/s)

If agreement > 3.3% → dimensional capacity was a real lever.
If ≈ 3.3% → ceiling persists across D; architecture change needed
   (R-RBS-LM-19 attention is the next direction).

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/run_path_c_d32k.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

sys.path.insert(0, "docs/srmech/python")
sys.path.insert(0, "docs/srmech/rbs_lm_research")

torch.set_num_threads(16)

from srmech.amsc.hdc import bind, bundle, similarity  # noqa: E402
from srmech.signal_processing.rbs_hdc_instrument import mint_vector  # noqa: E402

# Pull the corpus + prompts from R-RBS-LM-14's runner
from run_scale_genuine_mt import CORPUS_TEXT, HALLUCINATION_PROMPTS  # noqa: E402


D_TEST = 32768  # 4× the default 8192
CONTEXT_WINDOW = 64


# Local mint caches (D=32768)
_position_cache = {}
_sentinel_cache = {}


def position_vec(pos, D=D_TEST):
    if pos not in _position_cache:
        _position_cache[pos] = mint_vector(f"LoE.position.{pos}", D=D)
    return _position_cache[pos]


def sentinel(name, D=D_TEST):
    if name not in _sentinel_cache:
        _sentinel_cache[name] = mint_vector(f"LoE.sentinel.{name}", D=D)
    return _sentinel_cache[name]


def compute_path_c_vocab_table(model, D=D_TEST, seed=42):
    """Same as rbs_lm_path_c.compute_path_c_vocab_table but at any D."""
    print(f"  Computing Path C vocab table at D={D}...")
    t0 = time.time()
    wte = model.transformer.wte.weight.detach().cpu().numpy()
    vocab_size, source_dim = wte.shape
    print(f"  WTE matrix: ({vocab_size}, {source_dim})")
    rng = np.random.default_rng(seed)
    R = rng.standard_normal((D, source_dim)).astype(np.float32)
    print(f"  Random projection R: ({D}, {source_dim}) = {R.nbytes/1024**2:.1f} MB")
    projected = wte @ R.T  # (vocab_size, D); ~50K × 32K × 4B = 6.5 GB temp
    bipolar = (projected > 0).astype(np.uint8)
    vocab_table = np.packbits(bipolar, axis=1, bitorder="big")
    elapsed = time.time() - t0
    print(f"  Path C vocab table: {vocab_table.shape}; "
          f"{vocab_table.nbytes/1024**2:.1f} MB; {elapsed:.1f}s")
    # Free the large temporaries
    del projected, bipolar, R
    return vocab_table


def encode_context_path_c(token_ids, vocab_table_pc, D=D_TEST):
    if len(token_ids) > CONTEXT_WINDOW:
        token_ids = list(token_ids[-CONTEXT_WINDOW:])
    n = len(token_ids)
    if n == 0:
        return sentinel("empty_context", D)
    binds = [
        bind(vocab_table_pc[int(t)].tobytes(), position_vec(k, D))
        for k, t in enumerate(token_ids)
    ]
    if len(binds) == 1:
        return binds[0]
    if len(binds) % 2 == 0:
        binds.append(sentinel("context.pad", D))
    return bundle(binds)


def encode_observation_path_c(ctx, nxt, vocab_table_pc, D=D_TEST):
    return bind(
        encode_context_path_c(ctx, vocab_table_pc, D),
        vocab_table_pc[int(nxt)].tobytes(),
    )


def hierarchical_bundle_local(vectors, group_size=257, D=D_TEST, _depth=0):
    """Local hierarchical_bundle that uses D_TEST sentinels."""
    if len(vectors) == 0:
        return sentinel("empty_bundle", D)
    if len(vectors) == 1:
        return vectors[0]
    if len(vectors) <= group_size:
        vlist = list(vectors)
        if len(vlist) % 2 == 0:
            vlist.append(sentinel(f"bundle.pad.depth{_depth}", D))
        return bundle(vlist)
    effective_group = group_size - 1
    sub_bundles = []
    for i in range(0, len(vectors), effective_group):
        group = list(vectors[i: i + effective_group])
        if len(group) % 2 == 0:
            group.append(sentinel(f"bundle.pad.depth{_depth}", D))
        sub_bundles.append(bundle(group))
    return hierarchical_bundle_local(sub_bundles, group_size, D, _depth + 1)


def vectorised_cleanup(candidate_bytes, vocab_table, D=D_TEST, top_k=1):
    candidate = np.frombuffer(candidate_bytes, dtype=np.uint8)
    xor = vocab_table ^ candidate
    hamming = np.bitwise_count(xor).sum(axis=1)
    if top_k == 1:
        best = int(np.argmin(hamming))
        sim = 1.0 - 2.0 * float(hamming[best]) / D
        return [(best, sim)]
    idx = np.argpartition(hamming, top_k)[:top_k]
    idx = idx[np.argsort(hamming[idx])]
    return [(int(t), 1.0 - 2.0 * float(hamming[t]) / D) for t in idx]


def main():
    print(f"=== R-RBS-LM-20 — Path C at D={D_TEST} (4× the default) ===")
    print(f"  torch threads: {torch.get_num_threads()}")
    print(f"  D = {D_TEST}, CONTEXT_WINDOW = {CONTEXT_WINDOW}")

    print("\nLoading source model...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()

    print(f"\n=== Computing Path C vocab table at D=32768 ===")
    vocab_table_pc = compute_path_c_vocab_table(model, D=D_TEST, seed=42)

    # Verify structure preserved
    print(f"\n=== Path C vocab table properties (D=32768) ===")
    rng = np.random.default_rng(0)
    n_pairs = 100
    rand_pairs = rng.integers(0, vocab_table_pc.shape[0], (n_pairs, 2))
    hammings = []
    for i, j in rand_pairs:
        xor = vocab_table_pc[i] ^ vocab_table_pc[j]
        h = int(np.bitwise_count(xor).sum())
        hammings.append(h)
    print(f"  random-pair Hamming: {np.mean(hammings):.0f} ± {np.std(hammings):.0f} "
          f"(expected ≈ D/2 = {D_TEST//2})")
    the_id = tokenizer.encode(" the")[0]
    The_id = tokenizer.encode(" The")[0]
    h_the_The = int(np.bitwise_count(vocab_table_pc[the_id] ^ vocab_table_pc[The_id]).sum())
    sim_the_The = 1 - 2 * h_the_The / D_TEST
    print(f"  ' the' vs ' The' sim: {sim_the_The:+.4f} (R-RBS-LM-17 D=8192: +0.4875)")
    cat_id = tokenizer.encode(" cat")[0]
    h_the_cat = int(np.bitwise_count(vocab_table_pc[the_id] ^ vocab_table_pc[cat_id]).sum())
    sim_the_cat = 1 - 2 * h_the_cat / D_TEST
    print(f"  ' the' vs ' cat' sim: {sim_the_cat:+.4f} (R-RBS-LM-17 D=8192: +0.1353)")

    # ---- harvest -----------------------------------------------------
    print(f"\n=== Harvest (batched) ===")
    all_tokens = tokenizer.encode(CORPUS_TEXT)
    print(f"  corpus: {len(all_tokens)} tokens")
    stride = 8
    contexts = [
        all_tokens[i:i + CONTEXT_WINDOW]
        for i in range(0, len(all_tokens) - CONTEXT_WINDOW, stride)
    ]
    print(f"  target observations: {len(contexts)}")
    observations = []
    t0 = time.time()
    batch_size = 32
    for batch_start in range(0, len(contexts), batch_size):
        batch = contexts[batch_start: batch_start + batch_size]
        input_ids = torch.tensor(batch)
        with torch.no_grad():
            logits = model(input_ids).logits
        nexts = logits[:, -1, :].argmax(dim=-1).tolist()
        for ctx, nxt in zip(batch, nexts):
            observations.append((ctx, int(nxt)))
    harvest_time = time.time() - t0
    print(f"  harvested {len(observations)} obs in {harvest_time:.0f}s "
          f"({len(observations)/harvest_time:.1f}/s)")

    # ---- encode using Path C at D=32768 -----------------------------
    print(f"\n=== Encode at D={D_TEST} ===")
    t0 = time.time()
    bindings = [
        encode_observation_path_c(ctx, nxt, vocab_table_pc, D=D_TEST)
        for ctx, nxt in observations
    ]
    encode_time = time.time() - t0
    print(f"  {len(bindings)} bindings in {encode_time:.1f}s "
          f"({len(bindings)/encode_time:.1f}/s)")

    t0 = time.time()
    instrument = hierarchical_bundle_local(bindings, D=D_TEST)
    bundle_time = time.time() - t0
    print(f"  bundle: {bundle_time:.2f}s; instrument = {len(instrument)} bytes "
          f"({len(instrument)*8} bits = D)")

    out_path = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v20.bin")
    out_path.write_bytes(instrument)
    print(f"  saved: {out_path}")

    # ---- validate ----------------------------------------------------
    print(f"\n=== Validate on hallucination corpus (D={D_TEST}) ===")
    n_total = 0
    n_agree = 0
    latencies = []
    per_prompt_results = []
    for prompt in HALLUCINATION_PROMPTS:
        prompt_ids = tokenizer.encode(prompt)
        with torch.no_grad():
            src_out = model.generate(
                torch.tensor([prompt_ids]),
                max_new_tokens=20,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        src_new = src_out[0][len(prompt_ids):].tolist()
        rbs_tokens = list(prompt_ids)
        prompt_lats = []
        for _ in range(20):
            t0 = time.time()
            ctx = rbs_tokens[-CONTEXT_WINDOW:] if len(rbs_tokens) > CONTEXT_WINDOW else rbs_tokens
            ctx_vec = encode_context_path_c(ctx, vocab_table_pc, D=D_TEST)
            cand = bind(instrument, ctx_vec)
            res = vectorised_cleanup(cand, vocab_table_pc, D=D_TEST, top_k=1)
            rbs_tokens.append(res[0][0])
            prompt_lats.append((time.time() - t0) * 1000)
        rbs_new = rbs_tokens[len(prompt_ids):]
        latencies.extend(prompt_lats)
        agreement = [int(s == r) for s, r in zip(src_new, rbs_new)]
        n_total += len(agreement)
        n_agree += sum(agreement)
        per_prompt_results.append({
            "prompt": prompt,
            "source_decoded": tokenizer.decode(src_new),
            "rbs_decoded": tokenizer.decode(rbs_new),
            "agreement": sum(agreement),
        })
        print(f"  '{prompt[:40]}...' → agreement {sum(agreement)}/20")

    overall = n_agree / n_total
    print(f"\n  Overall: {n_agree}/{n_total} ({100*overall:.1f}%)")
    print(f"  Per-token latency: {np.mean(latencies):.1f} ± {np.std(latencies):.1f} ms")

    print(f"\n=== D scaling comparison ===")
    print(f"  {'Configuration':<60} {'D':>8} {'agreement':>12}")
    print(f"  {'Path C at D=8192 (R-RBS-LM-17, 109 obs)':<60} {'8192':>8} {'3.3%':>12}")
    print(f"  {'Path C at D=8192 (R-RBS-LM-18, 492 obs)':<60} {'8192':>8} {'3.3%':>12}")
    print(f"  {'Path C at D=32768 (R-RBS-LM-20, 491 obs, this)':<60} "
          f"{D_TEST:>8} {100*overall:>11.1f}%")

    results = {
        "partition": "R-RBS-LM-20",
        "D": D_TEST,
        "n_observations": len(observations),
        "instrument_bytes": len(instrument),
        "vocab_table_mb": vocab_table_pc.nbytes / 1024**2,
        "overall_agreement_pct": 100 * overall,
        "latency_ms_mean": float(np.mean(latencies)),
        "vocab_properties": {
            "random_pair_hamming_mean": float(np.mean(hammings)),
            "the_vs_The_sim": sim_the_The,
            "the_vs_cat_sim": sim_the_cat,
        },
        "comparison": {
            "path_c_d8192_109obs_pct": 3.3,
            "path_c_d8192_492obs_pct": 3.3,
            "path_c_d32768_491obs_pct": 100 * overall,
        },
        "per_prompt_results": per_prompt_results,
    }
    Path("docs/srmech/rbs_lm_research/rbs_lm_d32k_results.json").write_text(
        json.dumps(results, indent=2)
    )
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
