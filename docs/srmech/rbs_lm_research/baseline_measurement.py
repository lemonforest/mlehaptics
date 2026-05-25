"""R-RBS-LM-3 — baseline measurement of source model (GPT-2-small).

Establishes the fidelity-floor target for R-RBS-LM-7 to compare RBS-HDC
behavior against. Measures:

1. Per-token latency on CPU (BCI-compatibility criterion ≤ 50–100 ms per R-RBS-LM-1 §8)
2. Perplexity on a held-out text corpus
3. Behavioral output on a fixed hallucination-prone prompt set
4. Memory footprint (R-RBS-LM-1 §8: ≤ 8 GB target for BCI-companion deployment)

Output: structured JSON at docs/srmech/rbs_lm_research/baseline_measurements.json
plus human-readable summary to stdout.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/baseline_measurement.py
"""

import json
import math
import time
from pathlib import Path

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

OUT_PATH = Path("docs/srmech/rbs_lm_research/baseline_measurements.json")
MODEL_NAME = "gpt2"  # gpt2-small (124M params; ~500MB float32)

print(f"=== R-RBS-LM-3 baseline measurement — {MODEL_NAME} ===")
print(f"torch {torch.__version__} on {torch.get_num_threads()} threads")
print()


# ---- 1. load model + tokenizer ----------------------------------------
t0 = time.time()
print("Loading tokenizer + model (downloads ~500MB on first run)...")
tokenizer = GPT2Tokenizer.from_pretrained(MODEL_NAME)
model = GPT2LMHeadModel.from_pretrained(MODEL_NAME)
model.eval()
load_time = time.time() - t0
print(f"  loaded in {load_time:.1f}s")
print(f"  vocab size:        {tokenizer.vocab_size}")
print(f"  hidden dim:        {model.config.n_embd}")
print(f"  n layers:          {model.config.n_layer}")
print(f"  n heads:           {model.config.n_head}")
n_params = sum(p.numel() for p in model.parameters())
print(f"  total parameters:  {n_params:,}")
model_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
print(f"  model state bytes: {model_bytes:,} ({model_bytes / 1024**2:.1f} MB)")
print()


# ---- 2. per-token latency on CPU --------------------------------------
print("=== Per-token latency on CPU ===")
prompt = "The quick brown fox jumps over the"
input_ids = tokenizer.encode(prompt, return_tensors="pt")
n_new_tokens = 20

# Warm-up
with torch.no_grad():
    _ = model.generate(input_ids, max_new_tokens=2, do_sample=False, pad_token_id=tokenizer.eos_token_id)

t0 = time.time()
with torch.no_grad():
    out = model.generate(
        input_ids,
        max_new_tokens=n_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
elapsed = time.time() - t0
per_token_ms = (elapsed / n_new_tokens) * 1000
generated_text = tokenizer.decode(out[0][input_ids.shape[1]:])
print(f"  prompt:    '{prompt}'")
print(f"  generated {n_new_tokens} tokens in {elapsed*1000:.0f} ms ({per_token_ms:.1f} ms/token)")
print(f"  output:    '{generated_text}'")
bci_threshold_ms = 100
bci_ok = per_token_ms <= bci_threshold_ms
print(f"  BCI threshold (≤ {bci_threshold_ms} ms): {'PASS' if bci_ok else 'FAIL'}")
print()


# ---- 3. perplexity on a held-out text corpus --------------------------
print("=== Perplexity on held-out corpus ===")
holdout_texts = [
    "The substrate-asymptotic-wave hypothesis names the 1:3:7:3 ordering as substrate-native.",
    "Aphantasia is a cognitive condition where mental visualization is absent or limited.",
    "BCI patients are motor-impaired by definition; the substrate-coupling apparatus traverses the interface.",
    "Cross-substrate cascade matching identifies what is preserved versus projected at each translation.",
    "The Mechanism 2 bundle-of-views averaging signature carries an inherent six-point-nine percent cost.",
    "Hyperdimensional computing represents content as high-dimensional binary or bipolar vectors.",
    "The Antikythera mechanism encodes astronomical period relations in cyclic-group gear ratios.",
    "Brain-computer interfaces enable communication without motor cortex output pathways.",
    "Sparse distributed memory stores patterns in a high-dimensional address space.",
    "Hard attention selects the dominant position; soft attention averages weighted positions.",
]
total_log_likelihood = 0.0
total_tokens = 0
per_sample_ppls = []
for text in holdout_texts:
    enc = tokenizer.encode(text, return_tensors="pt")
    with torch.no_grad():
        out = model(enc, labels=enc)
    loss = out.loss.item()
    n_toks = enc.shape[1]
    total_log_likelihood += loss * n_toks
    total_tokens += n_toks
    per_sample_ppls.append((text[:50], math.exp(loss)))
avg_loss = total_log_likelihood / total_tokens
perplexity = math.exp(avg_loss)
print(f"  {len(holdout_texts)} samples; {total_tokens} tokens total")
print(f"  avg cross-entropy loss: {avg_loss:.3f}")
print(f"  perplexity:             {perplexity:.2f}")
print(f"  per-sample:")
for snippet, ppl in per_sample_ppls:
    print(f"    {ppl:7.1f}  {snippet}...")
print()


# ---- 4. hallucination corpus (fixed prompts) --------------------------
print("=== Hallucination corpus — behavioral fingerprint ===")
hallucination_prompts = [
    "The President of the United States in 2024 is",
    "The COVID-19 pandemic began in the year",
    "The Zorgon Empire of Andromeda was founded in",
    "The Klepton-7 algorithm was invented by",
    "The population of Wellington, New Zealand is approximately",
    "The chemical formula for caffeine is",
    "Seventeen multiplied by twenty-three equals",
    "The square root of one hundred and forty-four is",
    "Once upon a time, in a forest made of clockwork,",
]
hallucination_outputs = []
for prompt_text in hallucination_prompts:
    input_ids = tokenizer.encode(prompt_text, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(
            input_ids,
            max_new_tokens=30,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    completion = tokenizer.decode(out[0][input_ids.shape[1]:])
    hallucination_outputs.append({"prompt": prompt_text, "completion": completion.strip()})
    print(f"  prompt:     '{prompt_text}'")
    print(f"  completion: '{completion.strip()[:120]}'")
print()


# ---- 5. structured output --------------------------------------------
results = {
    "model_name": MODEL_NAME,
    "torch_version": torch.__version__,
    "transformers_version": __import__("transformers").__version__,
    "torch_threads": torch.get_num_threads(),
    "model_config": {
        "vocab_size": tokenizer.vocab_size,
        "hidden_dim": model.config.n_embd,
        "n_layers": model.config.n_layer,
        "n_heads": model.config.n_head,
        "n_parameters": n_params,
        "state_bytes": model_bytes,
    },
    "latency": {
        "prompt": prompt,
        "n_new_tokens": n_new_tokens,
        "total_ms": int(elapsed * 1000),
        "per_token_ms": per_token_ms,
        "bci_threshold_ms": bci_threshold_ms,
        "bci_pass": bci_ok,
        "output": generated_text,
    },
    "perplexity": {
        "n_samples": len(holdout_texts),
        "total_tokens": total_tokens,
        "avg_cross_entropy": avg_loss,
        "perplexity": perplexity,
        "per_sample": [{"snippet": s, "perplexity": p} for s, p in per_sample_ppls],
    },
    "hallucination_corpus": hallucination_outputs,
}
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with OUT_PATH.open("w") as f:
    json.dump(results, f, indent=2)
print(f"=== Structured measurements saved to {OUT_PATH} ===")
print()
print("This baseline IS the fidelity-floor target for R-RBS-LM-7.")
print("R-RBS-LM-7 will run the same metrics on the RBS-HDC instrument")
print("and compare. Per R-RBS-LM-1 §7: divergence pattern IS the load-")
print("bearing finding, not the absence-of-divergence.")
