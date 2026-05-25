"""R-RBS-LM-32 — Multi-buffer FFT graft behavioral smoke.

Tests whether layering multiple long-context buffers across distinct
frequency bands produces measurably different cascade output than:
  (a) single-buffer graft at the equivalent overall cutoff
  (b) baseline no-graft

Per R-RBS-LM-28 §5 Finding 1: cascade IS responsive to grafted signal.
This partition probes whether the cascade ALSO discriminates between
different BAND-COMPOSITIONS — i.e., whether feeding the same total signal
through a 3-layer arrangement vs a 1-layer arrangement produces different
mode-collapse patterns.

Honest expectations per `[[user_stance_ai_is_not_a_substrate]]`:
  - 3.3% structural ceiling still holds; outputs still mode-collapse
  - Multi-buffer might produce DIFFERENT mode-collapse patterns than
    single-buffer because the cascade's argmin cleanup sees a context_vec
    that was built from different frequency content
  - If yes: useful operationally (system + history + RAG can be layered
    surgically); if no: single-buffer cutoff is the only knob that matters

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/multi_buffer_fft_smoke.py
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
    vectorised_cleanup_bytes, text_to_bytes, bytes_to_text, encode_context_bytes,
)
from rbs_lm_fft import (  # noqa: E402
    encode_context_with_graft, encode_context_with_multi_buffer_graft,
)


INSTRUMENT_PATH = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin"
MAX_NEW = 24


def generate_with_encoder(bot, prompt_bytes, encode_ctx_fn, max_new=MAX_NEW):
    """Generate max_new bytes using a custom encode_ctx callable(ctx)."""
    tokens = list(prompt_bytes)
    new_bytes = []
    for _ in range(max_new):
        ctx = tokens[-CONTEXT_WINDOW:] if len(tokens) > CONTEXT_WINDOW else tokens
        ctx_vec = encode_ctx_fn(ctx)
        cand = bind(bot.instrument, ctx_vec)
        res = vectorised_cleanup_bytes(cand, bot.vocab_table, D, top_k=1)
        nxt = res[0][0]
        new_bytes.append(nxt)
        tokens.append(nxt)
    return new_bytes


def compare_outputs(a_bytes, b_bytes):
    n = min(len(a_bytes), len(b_bytes))
    return sum(1 for i in range(n) if a_bytes[i] == b_bytes[i]), n


def main():
    print(f"=== R-RBS-LM-32 — Multi-buffer FFT graft behavioral smoke ===")
    print(f"  instrument: {INSTRUMENT_PATH}")
    bot = RBSChatbotBytes.load(instrument_path=INSTRUMENT_PATH, verbose=True)
    vocab_table = bot.vocab_table

    # 3-layer scenario buffers
    system_prompt = text_to_bytes(
        "You are a careful cooking instructor. Answer with practical steps."
    )
    conversation_history = text_to_bytes(
        "User: Tell me about French cooking. Assistant: French cuisine emphasizes "
        "fresh ingredients, classical techniques, and precise timing. "
        "User: What about sauces? Assistant: Classical French sauces include "
        "espagnole, velouté, béchamel, hollandaise, and tomate."
    )
    rag_document = text_to_bytes(
        "Beating eggs incorporates air, lightening the texture. Use a balloon "
        "whisk in a steady circular motion for ~2 minutes until soft peaks form. "
        "For meringue: beat egg whites with a pinch of cream of tartar."
    )

    # Test prompts
    test_prompts = [
        "How do I beat eggs?",
        "What is the topic?",
        "Tell me more.",
    ]

    results = []

    for prompt_text in test_prompts:
        prompt_bytes = text_to_bytes(prompt_text)
        print(f"\n{'='*72}")
        print(f"=== prompt: {prompt_text!r}")
        print(f"{'='*72}")

        # Baseline: no graft
        out_base = generate_with_encoder(
            bot, prompt_bytes,
            lambda ctx: encode_context_bytes(ctx, vocab_table, D)
        )

        # Single-buffer graft (rag only, cutoff=10)
        out_single = generate_with_encoder(
            bot, prompt_bytes,
            lambda ctx: encode_context_with_graft(ctx, rag_document, vocab_table,
                                                   cutoff_freq=10, D=D)
        )

        # Multi-buffer graft (system + history + rag, endpoints [2, 6, 10])
        out_multi3 = generate_with_encoder(
            bot, prompt_bytes,
            lambda ctx: encode_context_with_multi_buffer_graft(
                ctx,
                layered_buffer_tokens=[system_prompt, conversation_history, rag_document],
                layered_end_cutoffs=[2, 6, 10],
                vocab_table=vocab_table, D=D,
            )
        )

        # Multi-buffer with reversed order (rag + history + system at [4, 8, 10])
        # — does ORDER matter?
        out_multi_rev = generate_with_encoder(
            bot, prompt_bytes,
            lambda ctx: encode_context_with_multi_buffer_graft(
                ctx,
                layered_buffer_tokens=[rag_document, conversation_history, system_prompt],
                layered_end_cutoffs=[4, 8, 10],
                vocab_table=vocab_table, D=D,
            )
        )

        # Two-buffer (system + rag at [4, 10])
        out_multi2 = generate_with_encoder(
            bot, prompt_bytes,
            lambda ctx: encode_context_with_multi_buffer_graft(
                ctx,
                layered_buffer_tokens=[system_prompt, rag_document],
                layered_end_cutoffs=[4, 10],
                vocab_table=vocab_table, D=D,
            )
        )

        print(f"  baseline (no graft):              {bytes_to_text(out_base)!r}")
        print(f"  single-buffer (rag@10):           {bytes_to_text(out_single)!r}")
        print(f"  multi-3 (sys+hist+rag@[2,6,10]):  {bytes_to_text(out_multi3)!r}")
        print(f"  multi-3 reversed (rag+hist+sys):  {bytes_to_text(out_multi_rev)!r}")
        print(f"  multi-2 (sys+rag@[4,10]):         {bytes_to_text(out_multi2)!r}")

        print(f"\n  Pairwise byte-by-byte matching (of {MAX_NEW} bytes):")
        pairs = [
            ("baseline vs single",   out_base, out_single),
            ("baseline vs multi-3",  out_base, out_multi3),
            ("single vs multi-3",    out_single, out_multi3),
            ("multi-3 vs reversed",  out_multi3, out_multi_rev),
            ("multi-3 vs multi-2",   out_multi3, out_multi2),
        ]
        for label, a, b in pairs:
            m, n = compare_outputs(a, b)
            print(f"    {label:<30s} {m:>2d}/{n} match  {'IDENTICAL' if m == n else 'DIFFER'}")

        results.append({
            "prompt": prompt_text,
            "baseline_completion": bytes_to_text(out_base),
            "single_buffer_completion": bytes_to_text(out_single),
            "multi3_completion": bytes_to_text(out_multi3),
            "multi3_reversed_completion": bytes_to_text(out_multi_rev),
            "multi2_completion": bytes_to_text(out_multi2),
            "baseline_bytes": out_base,
            "single_bytes": out_single,
            "multi3_bytes": out_multi3,
            "multi3_reversed_bytes": out_multi_rev,
            "multi2_bytes": out_multi2,
        })

    # Aggregate
    print(f"\n{'='*72}")
    print(f"=== Honest framework reading ===")
    print(f"{'='*72}")

    n_multi3_differs_from_single = 0
    n_multi3_differs_from_reversed = 0
    n_multi3_differs_from_multi2 = 0
    for r in results:
        if compare_outputs(r["single_bytes"], r["multi3_bytes"])[0] != MAX_NEW:
            n_multi3_differs_from_single += 1
        if compare_outputs(r["multi3_bytes"], r["multi3_reversed_bytes"])[0] != MAX_NEW:
            n_multi3_differs_from_reversed += 1
        if compare_outputs(r["multi3_bytes"], r["multi2_bytes"])[0] != MAX_NEW:
            n_multi3_differs_from_multi2 += 1

    print(f"\n  Across {len(results)} prompts:")
    print(f"    multi-3 ≠ single-buffer: {n_multi3_differs_from_single}/{len(results)}")
    print(f"    multi-3 ≠ multi-3-reversed (order matters?): "
          f"{n_multi3_differs_from_reversed}/{len(results)}")
    print(f"    multi-3 ≠ multi-2 (number of layers matters?): "
          f"{n_multi3_differs_from_multi2}/{len(results)}")

    out_path = Path("docs/srmech/rbs_lm_research/multi_buffer_fft_smoke_results.json")
    out_path.write_text(json.dumps({
        "partition": "R-RBS-LM-32",
        "instrument": INSTRUMENT_PATH,
        "results": results,
    }, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
