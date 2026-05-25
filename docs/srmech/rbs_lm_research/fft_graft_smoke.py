"""R-RBS-LM-28 — FFT-graft smoke: long-context awareness without changing the cascade.

Tests whether the FFT-grafted context_vec produces measurably different
cascade behavior depending on (a) whether a long buffer is present, and
(b) whether the long buffer is topically RELEVANT or a DISTRACTOR.

The cascade itself is unchanged — the v25b BPE-stripped byte instrument
from R-RBS-LM-25. Only the encode_context step changes:

  - baseline:   encode_context_bytes(recent, vocab)           # R-RBS-LM-25
  - grafted:    encode_context_with_graft(recent, long, vocab, cutoff_freq=K)

Honest framework reading per `[[user_stance_ai_is_not_a_substrate]]` and
the R-RBS-LM-19 structural ceiling: cascade outputs will mode-collapse
either way. What we measure is whether the mode-collapse PATTERN differs
between baseline / grafted-relevant / grafted-distractor. If grafting
produces measurably different patterns, the FFT context surgery IS
operationally meaningful even at the ceiling.

Three scenarios:

  A. LONG-BUFFER AWARENESS: same query with vs. without a topically-
     relevant long buffer. Cascade output bytes should differ if the
     graft is delivering signal.

  B. RELEVANCE DISCRIMINATION: same query with a RELEVANT long buffer
     vs. an UNRELATED-DISTRACTOR long buffer. Pattern difference is
     the "is the cascade reading the graft" signal.

  C. CUTOFF SWEEP: vary cutoff_freq from 0 (no graft) to W//2 (max graft).
     How does cascade output change as we admit more long-buffer signal?

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/fft_graft_smoke.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_chatbot import RBSChatbotBytes  # noqa: E402
from rbs_lm_encoder import CONTEXT_WINDOW, D, bind  # noqa: E402
from rbs_lm_bytes import (  # noqa: E402
    compute_byte_vocab_table,
    encode_context_bytes,
    vectorised_cleanup_bytes,
    text_to_bytes,
    bytes_to_text,
)
from rbs_lm_fft import encode_context_with_graft  # noqa: E402


INSTRUMENT_PATH = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin"
MAX_NEW = 24


def generate_with_method(bot, prompt_bytes, encode_ctx_fn, max_new=MAX_NEW):
    """Generate `max_new` bytes using a custom encode_ctx_fn(tokens) callable.

    Each step:
        ctx = tokens[-WINDOW:]
        ctx_vec = encode_ctx_fn(ctx)
        candidate = bind(instrument, ctx_vec)
        next = argmin Hamming cleanup
    """
    tokens = list(prompt_bytes)
    new_bytes = []
    latencies = []
    for _ in range(max_new):
        t0 = time.time()
        ctx = tokens[-CONTEXT_WINDOW:] if len(tokens) > CONTEXT_WINDOW else tokens
        ctx_vec = encode_ctx_fn(ctx, tokens)
        cand = bind(bot.instrument, ctx_vec)
        res = vectorised_cleanup_bytes(cand, bot.vocab_table, D, top_k=1)
        nxt = res[0][0]
        new_bytes.append(nxt)
        tokens.append(nxt)
        latencies.append((time.time() - t0) * 1000)
    return new_bytes, latencies


def baseline_encoder(vocab_table):
    """No graft: standard byte-level encoding of the recent window."""
    def fn(ctx, _tokens_full):
        return encode_context_bytes(ctx, vocab_table, D)
    return fn


def graft_encoder(vocab_table, long_buffer_bytes, cutoff_freq):
    """Graft the long buffer's low-freq into the recent window."""
    def fn(ctx, _tokens_full):
        return encode_context_with_graft(
            ctx, long_buffer_bytes, vocab_table,
            cutoff_freq=cutoff_freq, D=D,
        )
    return fn


def compare_outputs(a_bytes, b_bytes):
    """Byte-position agreement between two output byte sequences."""
    n = min(len(a_bytes), len(b_bytes))
    n_match = sum(1 for i in range(n) if a_bytes[i] == b_bytes[i])
    return n_match, n


def main():
    print(f"=== R-RBS-LM-28 — FFT-graft long-context awareness smoke ===")
    print(f"  instrument: {INSTRUMENT_PATH}")
    bot = RBSChatbotBytes.load(instrument_path=INSTRUMENT_PATH, verbose=True)
    vocab_table = bot.vocab_table

    # --- Test queries (each short; fits in 64-byte window) ---
    queries = [
        "What is the topic?",
        "Tell me more.",
        "The morning sun",
        "Once upon a time",
    ]

    # --- Long buffers (each well over CONTEXT_WINDOW=64 bytes) ---
    long_buffers = {
        "cooking_topic": (
            "We baked a chocolate cake yesterday. The recipe called for "
            "two cups of flour, three eggs, and a tablespoon of vanilla "
            "extract. The oven was preheated to 350 degrees Fahrenheit. "
            "We mixed the dry ingredients first, then folded in the wet."
        ),
        "astronomy_topic": (
            "The Andromeda galaxy lies approximately 2.5 million light-years "
            "from Earth. It contains roughly one trillion stars and is "
            "expected to collide with the Milky Way in about 4.5 billion "
            "years. Its diameter spans roughly 220,000 light-years."
        ),
        "distractor_random": (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna "
            "aliqua. Ut enim ad minim veniam, quis nostrud exercitation."
        ),
    }

    all_results = {"queries": [], "summary": {}}

    # ===== SCENARIO A: Long-buffer awareness =====
    print(f"\n{'='*72}")
    print(f"=== Scenario A: With vs. without long buffer ===")
    print(f"  (Does presence of a long buffer change the cascade output?)")
    print(f"{'='*72}")

    cutoff = 8  # graft low-freq cutoff

    for query in queries:
        prompt_bytes = text_to_bytes(query)
        long_buf = text_to_bytes(long_buffers["cooking_topic"])

        baseline_out, _ = generate_with_method(
            bot, prompt_bytes, baseline_encoder(vocab_table))
        grafted_out, _ = generate_with_method(
            bot, prompt_bytes, graft_encoder(vocab_table, long_buf, cutoff))

        match, n = compare_outputs(baseline_out, grafted_out)
        print(f"\n  query:        {query!r}")
        print(f"    baseline:   {bytes_to_text(baseline_out)!r}")
        print(f"    grafted:    {bytes_to_text(grafted_out)!r}  (cooking buffer; cutoff {cutoff})")
        print(f"    match:      {match}/{n} bytes identical "
              f"({'IDENTICAL' if match == n else 'DIFFER'})")
        all_results["queries"].append({
            "scenario": "A_with_vs_without_long_buffer",
            "query": query,
            "baseline_output": bytes_to_text(baseline_out),
            "grafted_output": bytes_to_text(grafted_out),
            "baseline_bytes": baseline_out,
            "grafted_bytes": grafted_out,
            "matching_bytes": match,
            "total_bytes": n,
        })

    # ===== SCENARIO B: Relevance discrimination =====
    print(f"\n{'='*72}")
    print(f"=== Scenario B: Relevant vs. distractor long buffer ===")
    print(f"  (Does WHICH long buffer matters? — relevance discrimination)")
    print(f"{'='*72}")

    for query in queries[:2]:  # subset since this is slower (multiple buffers)
        prompt_bytes = text_to_bytes(query)
        outputs_per_buffer = {}
        for buf_label, buf_text in long_buffers.items():
            buf_bytes = text_to_bytes(buf_text)
            out, _ = generate_with_method(
                bot, prompt_bytes, graft_encoder(vocab_table, buf_bytes, cutoff))
            outputs_per_buffer[buf_label] = out

        print(f"\n  query: {query!r}")
        # Pairwise comparison
        labels = list(outputs_per_buffer.keys())
        for i, label_a in enumerate(labels):
            print(f"    [{label_a:>20s}]: {bytes_to_text(outputs_per_buffer[label_a])!r}")
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                a, b = outputs_per_buffer[labels[i]], outputs_per_buffer[labels[j]]
                match, n = compare_outputs(a, b)
                print(f"    [{labels[i][:12]}] vs [{labels[j][:12]}]: "
                      f"{match}/{n} bytes match")

        all_results["queries"].append({
            "scenario": "B_relevance_discrimination",
            "query": query,
            "outputs_per_buffer": {k: bytes_to_text(v) for k, v in outputs_per_buffer.items()},
            "output_bytes_per_buffer": {k: v for k, v in outputs_per_buffer.items()},
        })

    # ===== SCENARIO C: Cutoff sweep =====
    print(f"\n{'='*72}")
    print(f"=== Scenario C: Cutoff sweep (how much long-buffer signal admitted?) ===")
    print(f"{'='*72}")

    query = queries[0]
    long_buf = text_to_bytes(long_buffers["cooking_topic"])
    prompt_bytes = text_to_bytes(query)
    print(f"\n  query: {query!r}")
    print(f"  long buffer: cooking_topic")

    cutoff_outputs = {}
    for c in [0, 2, 4, 8, 16, 32]:
        if c == 0:
            out, _ = generate_with_method(bot, prompt_bytes, baseline_encoder(vocab_table))
        else:
            out, _ = generate_with_method(
                bot, prompt_bytes, graft_encoder(vocab_table, long_buf, c))
        cutoff_outputs[c] = out
        print(f"    cutoff={c:>2d}: {bytes_to_text(out)!r}")

    # Match each cutoff to baseline (cutoff=0)
    print(f"\n  Match-to-baseline:")
    base = cutoff_outputs[0]
    for c, out in cutoff_outputs.items():
        match, n = compare_outputs(base, out)
        print(f"    cutoff={c:>2d}: {match}/{n} bytes match baseline")

    all_results["queries"].append({
        "scenario": "C_cutoff_sweep",
        "query": query,
        "long_buffer": "cooking_topic",
        "cutoff_outputs": {str(c): bytes_to_text(v) for c, v in cutoff_outputs.items()},
        "cutoff_output_bytes": {str(c): v for c, v in cutoff_outputs.items()},
    })

    # --- Aggregate summary ---
    print(f"\n{'='*72}")
    print(f"=== Honest framework reading ===")
    print(f"{'='*72}")

    scenario_a = [r for r in all_results["queries"]
                  if r["scenario"] == "A_with_vs_without_long_buffer"]
    n_a_differ = sum(1 for r in scenario_a if r["matching_bytes"] != r["total_bytes"])
    print(f"\n  Scenario A (long-buffer awareness):")
    print(f"    {n_a_differ}/{len(scenario_a)} queries produced different output "
          f"when a long buffer was added.")
    if n_a_differ == 0:
        print(f"    → Cascade output is INVARIANT to long-buffer graft at this cutoff.")
        print(f"    → Possible cause: graft signal is below the cleanup threshold,")
        print(f"      OR the recent-window's high-freq dominates argmax cleanup.")
    elif n_a_differ < len(scenario_a):
        print(f"    → PARTIAL — some queries respond to graft, others don't.")
    else:
        print(f"    → All queries respond to graft. Long-context awareness IS")
        print(f"      operationally measurable in cascade output.")

    scenario_b = [r for r in all_results["queries"]
                  if r["scenario"] == "B_relevance_discrimination"]
    print(f"\n  Scenario B (relevance discrimination):")
    print(f"    Output differs across long buffers? (see per-query pairs above)")

    out_path = Path("docs/srmech/rbs_lm_research/fft_graft_smoke_results.json")
    out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
