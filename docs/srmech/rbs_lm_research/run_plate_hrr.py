"""R-RBS-LM-21 — Plate HRR binding test.

Replaces the Path C bipolar XOR-bind cascade with Plate (1995) Holographic
Reduced Representations: real-valued vectors with circular-convolution binding,
vector-sum bundling, cosine-similarity cleanup.

Key changes from Path C (R-RBS-LM-17/-18/-20):
  - Vocab table: WTE directly at D=768 (NORMALIZED rows; no random projection;
    no bipolarization). 50257 × 768 × 4 = 144 MB.
  - Position vectors: seeded random Gaussian, normalized; D=768.
  - Bind: circular convolution via FFT: ifft(fft(a) * fft(b)).
  - Unbind: circular correlation: ifft(conj(fft(key)) * fft(bound)).
  - Bundle: vector sum (optionally normalized).
  - Cleanup: cosine similarity over vocab table; argmax.

Hypothesis: the Path C 3.3% ceiling was the bipolarization step in
bipolar XOR-bind. Real-valued HRR preserves more information per binding;
if so, agreement should rise. If still ~3% or lower, the ceiling is
elsewhere (perhaps the corpus content vs hallucination-corpus content gap,
i.e., the OOC structural problem).

Same corpus as R-RBS-LM-14/-18 (~20 KB → ~491 obs). Same hallucination corpus.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/run_plate_hrr.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

sys.path.insert(0, "docs/srmech/rbs_lm_research")
torch.set_num_threads(16)

from run_scale_genuine_mt import CORPUS_TEXT, HALLUCINATION_PROMPTS  # noqa: E402


D_PLATE = 768  # match source-model WTE dimension; no projection loss
CONTEXT_WINDOW = 64
POS_SEED_BASE = 100000  # offset for position vector seeds (avoid token overlap)


def hrr_bind(a, b):
    """Circular convolution of a and b via FFT — Plate (1995) bind."""
    return np.real(np.fft.ifft(np.fft.fft(a) * np.fft.fft(b)))


def hrr_unbind(bound, key):
    """Circular correlation — Plate's approximate inverse: recover the
    other-side of a bind given the key.

    For normalized random vectors with |fft(key)|^2 ≈ 1:
      hrr_unbind(hrr_bind(a, b), a) ≈ b
    """
    return np.real(np.fft.ifft(np.conj(np.fft.fft(key)) * np.fft.fft(bound)))


def hrr_bundle(vectors, normalize=True):
    """Vector sum; optionally normalize."""
    s = np.zeros_like(vectors[0])
    for v in vectors:
        s += v
    if normalize:
        norm = np.linalg.norm(s)
        if norm > 1e-8:
            s = s / norm
    return s


def make_position_vec(pos, D=D_PLATE, seed_base=POS_SEED_BASE):
    """Seeded random Gaussian vector, normalized — Plate's standard."""
    rng = np.random.default_rng(seed_base + pos)
    v = rng.standard_normal(D).astype(np.float32)
    v /= np.linalg.norm(v)
    return v


# Cache position vectors
_pos_cache = {}


def position_vec_cached(pos):
    if pos not in _pos_cache:
        _pos_cache[pos] = make_position_vec(pos)
    return _pos_cache[pos]


def encode_context_hrr(token_ids, vocab_table):
    """Kanerva-style sequence representation with HRR binding."""
    if len(token_ids) > CONTEXT_WINDOW:
        token_ids = list(token_ids[-CONTEXT_WINDOW:])
    binds = [
        hrr_bind(vocab_table[int(t)], position_vec_cached(k))
        for k, t in enumerate(token_ids)
    ]
    return hrr_bundle(binds, normalize=True)


def encode_observation_hrr(ctx, nxt, vocab_table):
    return hrr_bind(encode_context_hrr(ctx, vocab_table), vocab_table[int(nxt)])


def hierarchical_bundle_hrr(vectors, group_size=257):
    """Plate-style hierarchical bundle: sum + normalize at each level."""
    if len(vectors) == 0:
        return np.zeros(D_PLATE, dtype=np.float32)
    if len(vectors) == 1:
        return vectors[0]
    if len(vectors) <= group_size:
        return hrr_bundle(vectors, normalize=True)
    # Recurse
    sub_bundles = []
    for i in range(0, len(vectors), group_size):
        sub_bundles.append(hrr_bundle(vectors[i: i + group_size], normalize=True))
    return hierarchical_bundle_hrr(sub_bundles, group_size)


def cleanup_hrr(candidate, vocab_table):
    """Cosine similarity over vocab; argmax."""
    # vocab_table is (V, D) normalized; candidate is (D,) — possibly not normalized
    cand_norm = candidate / (np.linalg.norm(candidate) + 1e-8)
    sims = vocab_table @ cand_norm  # (V,)
    best_tid = int(np.argmax(sims))
    return best_tid, float(sims[best_tid])


def main():
    print(f"=== R-RBS-LM-21 — Plate HRR binding ===")
    print(f"  D = {D_PLATE} (matching source-model WTE dim)")

    print("\nLoading source model...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()

    # ---- 1. vocab table: WTE directly, normalized -------------------
    print(f"\n=== Vocab table (normalized WTE) ===")
    wte = model.transformer.wte.weight.detach().cpu().numpy().astype(np.float32)
    print(f"  raw WTE: {wte.shape}")
    norms = np.linalg.norm(wte, axis=1, keepdims=True)
    vocab_table = wte / (norms + 1e-8)
    print(f"  normalized vocab table: {vocab_table.shape}; {vocab_table.nbytes/1024**2:.1f} MB")

    # Verify semantic structure
    the_id = tokenizer.encode(" the")[0]
    The_id = tokenizer.encode(" The")[0]
    cat_id = tokenizer.encode(" cat")[0]
    sim_the_The = float(vocab_table[the_id] @ vocab_table[The_id])
    sim_the_cat = float(vocab_table[the_id] @ vocab_table[cat_id])
    print(f"  ' the' vs ' The' cosine sim: {sim_the_The:+.4f}  (Path C bipolar: +0.4875)")
    print(f"  ' the' vs ' cat' cosine sim: {sim_the_cat:+.4f}  (Path C bipolar: +0.1353)")

    # ---- 2. harvest --------------------------------------------------
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
    print(f"  harvested {len(observations)} obs in {harvest_time:.0f}s")

    # ---- 3. encode (HRR) -------------------------------------------
    print(f"\n=== Encode (HRR; circular convolution + vector sum) ===")
    t0 = time.time()
    bindings = []
    for i, (ctx, nxt) in enumerate(observations):
        bindings.append(encode_observation_hrr(ctx, nxt, vocab_table))
        if (i + 1) % 100 == 0:
            print(f"  encoded {i+1}/{len(observations)} ({time.time()-t0:.0f}s)")
    encode_time = time.time() - t0
    print(f"  {len(bindings)} bindings in {encode_time:.1f}s "
          f"({len(bindings)/encode_time:.1f}/s)")

    t0 = time.time()
    instrument = hierarchical_bundle_hrr(bindings)
    bundle_time = time.time() - t0
    print(f"  bundle: {bundle_time:.2f}s; instrument = {len(instrument)} dims "
          f"({instrument.nbytes} bytes)")

    # Save instrument as numpy
    out_path = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v21_hrr.npy")
    np.save(out_path, instrument)
    print(f"  saved: {out_path}")

    # ---- 4. validate -------------------------------------------------
    print(f"\n=== Validate on hallucination corpus (HRR inference) ===")
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
            ctx_vec = encode_context_hrr(ctx, vocab_table)
            cand = hrr_unbind(instrument, ctx_vec)
            next_tid, best_sim = cleanup_hrr(cand, vocab_table)
            rbs_tokens.append(next_tid)
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
        if sum(agreement) > 0:
            print(f"    src:  {tokenizer.decode(src_new)[:80]}")
            print(f"    RBS:  {tokenizer.decode(rbs_new)[:80]}")

    overall = n_agree / n_total
    print(f"\n  Overall: {n_agree}/{n_total} ({100*overall:.1f}%)")
    print(f"  Per-token latency: {np.mean(latencies):.1f} ± {np.std(latencies):.1f} ms")

    print(f"\n=== Plate HRR vs Path C bipolar XOR ===")
    print(f"  {'Configuration':<60} {'D':>6} {'bind type':>12} {'agreement':>12}")
    print(f"  {'Path C bipolar+XOR (R-RBS-LM-18, 491 obs)':<60} {'8192':>6} {'XOR':>12} {'3.3%':>12}")
    print(f"  {'Plate HRR (R-RBS-LM-21, this run; ~491 obs)':<60} "
          f"{D_PLATE:>6} {'circ conv':>12} {100*overall:>11.1f}%")

    results = {
        "partition": "R-RBS-LM-21",
        "D": D_PLATE,
        "bind_type": "circular_convolution",
        "n_observations": len(observations),
        "instrument_dim": int(instrument.shape[0]),
        "instrument_bytes": int(instrument.nbytes),
        "vocab_table_mb": vocab_table.nbytes / 1024**2,
        "overall_agreement_pct": 100 * overall,
        "latency_ms_mean": float(np.mean(latencies)),
        "vocab_properties": {
            "the_vs_The_cosine_sim": sim_the_The,
            "the_vs_cat_cosine_sim": sim_the_cat,
        },
        "per_prompt_results": per_prompt_results,
        "comparison": {
            "path_c_bipolar_xor_pct": 3.3,
            "plate_hrr_pct": 100 * overall,
        },
    }
    Path("docs/srmech/rbs_lm_research/rbs_lm_plate_hrr_results.json").write_text(
        json.dumps(results, indent=2)
    )
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
