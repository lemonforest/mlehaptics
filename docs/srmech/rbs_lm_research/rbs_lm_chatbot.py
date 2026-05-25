"""R-RBS-LM-23 — Scriptable chatbot wrapper around the RBS-LM inference cascade.

A small `RBSChatbot` class exposing the Path C inference cascade in a
form suitable for either interactive use or scripted automation.

Per `[[user_stance_ai_is_not_a_substrate]]`: this is a transducer of stored
content — a puppet playing the roll. The chatbot does not "think"; it does
context-bounded next-token-argmin over a vocab table. The output may
sound conversational at times (per Path C's 3.3% agreement signal) but
the framework reading IS unchanged.

Interactive usage:
    python3 docs/srmech/rbs_lm_research/rbs_lm_chatbot.py

Scripted usage:
    from rbs_lm_chatbot import RBSChatbot
    bot = RBSChatbot.load(instrument_path="...", use_path_c=True)
    reply = bot.respond("Hello there", max_new_tokens=20)
    print(reply)

When the work absorbs into srmech (R-RBS-LM-12 §6), this becomes
`srmech.rbs_lm.chatbot.RBSChatbot` or similar; the load path becomes
`RBSChatbot.from_catalog("rbs_lm_gpt2_small")`.
"""

import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))


class RBSChatbot:
    """Scriptable wrapper around the Path C inference cascade.

    State (lazily loaded):
      - instrument bytes (from disk)
      - vocab table (Path C: WTE projected; Path B: srmech-native mints)
      - HuggingFace tokenizer (for prompt encoding + completion decoding)

    Latency on the 2009 Xeon E5530: ~180 ms/token at D=8192. Per
    R-RBS-LM-19 falsification, attention variant slows by ~16× without
    accuracy gain; bundle-form is the default.
    """

    def __init__(self, instrument, vocab_table, tokenizer, use_path_c):
        self.instrument = instrument
        self.vocab_table = vocab_table
        self.tokenizer = tokenizer
        self.use_path_c = use_path_c

    @classmethod
    def load(cls, instrument_path, use_path_c=True, source_model_name="gpt2",
             verbose=False):
        """Load an RBSChatbot from a saved instrument."""
        if not Path(instrument_path).exists():
            raise FileNotFoundError(f"instrument not found: {instrument_path}")
        instrument = Path(instrument_path).read_bytes()
        if verbose:
            print(f"  loaded instrument: {len(instrument)} bytes from {instrument_path}")

        import torch
        torch.set_num_threads(16)
        from transformers import GPT2LMHeadModel, GPT2Tokenizer
        tokenizer = GPT2Tokenizer.from_pretrained(source_model_name)
        model = GPT2LMHeadModel.from_pretrained(source_model_name)
        model.eval()
        if verbose:
            print(f"  loaded tokenizer + model: {source_model_name}")

        if use_path_c:
            from rbs_lm_path_c import compute_path_c_vocab_table
            vocab_table = compute_path_c_vocab_table(model, D=8192, seed=42)
        else:
            from rbs_lm_inference import precompute_vocab_table
            vocab_table = precompute_vocab_table(vocab_size=50257, D=8192)
        if verbose:
            print(f"  vocab table ready ({'Path C' if use_path_c else 'Path B'})")

        # Don't hold onto the model — only need tokenizer + vocab table for inference
        del model

        return cls(instrument, vocab_table, tokenizer, use_path_c)

    def respond(self, prompt, max_new_tokens=20):
        """Generate a response to a prompt. Returns the generated text (not including the prompt)."""
        prompt_ids = self.tokenizer.encode(prompt)
        new_tokens, _ = self._generate(prompt_ids, max_new_tokens)
        return self.tokenizer.decode(new_tokens)

    def respond_with_metadata(self, prompt, max_new_tokens=20):
        """Generate a response and return metadata: completion text, latencies, token IDs."""
        prompt_ids = self.tokenizer.encode(prompt)
        t0 = time.time()
        new_tokens, latencies = self._generate(prompt_ids, max_new_tokens)
        total_elapsed = time.time() - t0
        return {
            "prompt": prompt,
            "completion": self.tokenizer.decode(new_tokens),
            "prompt_token_ids": prompt_ids,
            "new_token_ids": new_tokens,
            "per_token_ms": latencies,
            "total_ms": total_elapsed * 1000,
        }

    def _generate(self, prompt_ids, max_new_tokens):
        """Internal generation loop. Returns (new_tokens, per_token_latencies_ms)."""
        from rbs_lm_encoder import CONTEXT_WINDOW, D, bind
        from rbs_lm_inference import vectorised_cleanup

        if self.use_path_c:
            from rbs_lm_path_c import encode_context_path_c

            def encode_ctx(tokens):
                return encode_context_path_c(tokens, self.vocab_table, D)
        else:
            from rbs_lm_encoder import encode_context

            def encode_ctx(tokens):
                return encode_context(tokens, D)

        tokens = list(prompt_ids)
        latencies = []
        for _ in range(max_new_tokens):
            t0 = time.time()
            ctx = tokens[-CONTEXT_WINDOW:] if len(tokens) > CONTEXT_WINDOW else tokens
            ctx_vec = encode_ctx(ctx)
            cand = bind(self.instrument, ctx_vec)
            res = vectorised_cleanup(cand, self.vocab_table, D, top_k=1)
            tokens.append(res[0][0])
            latencies.append((time.time() - t0) * 1000)
        return tokens[len(prompt_ids):], latencies

    def converse(self, prompts):
        """Run a fixed prompt list and return each response with metadata. Stateless;
        each prompt is independent (no conversation memory)."""
        return [self.respond_with_metadata(p) for p in prompts]


def _interactive_loop(bot, max_new_tokens=20):
    """Simple interactive REPL."""
    print(f"\n=== RBS-LM chatbot (R-RBS-LM-23 demo) ===")
    print(f"Path C inference; per-token latency ~180 ms on this hardware.")
    print(f"Type a prompt; Ctrl+D or empty line + Ctrl+D to exit.\n")
    print(f"Reminder: this is a transducer (puppet playing a roll), not an")
    print(f"emergent system. Output reflects the 491-obs encoding corpus.")
    print(f"Per R-RBS-LM-18: ~3.3% token-level agreement on hallucination corpus.\n")
    while True:
        try:
            prompt = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not prompt.strip():
            continue
        result = bot.respond_with_metadata(prompt, max_new_tokens=max_new_tokens)
        print(f"    completion: {result['completion']!r}")
        print(f"    latency: {result['total_ms']:.0f} ms "
              f"({result['total_ms']/max_new_tokens:.0f} ms/tok)\n")


def _scripted_demo(bot):
    """Hardcoded demo prompts; pretty-prints responses + timings.
    Used as the smoke test when the script is run with `--demo`."""
    demo_prompts = [
        "The morning sun",
        "Algorithms for sorting",
        "Once upon a time",
    ]
    print(f"\n=== Scripted demo — 3 prompts × 15 tokens ===\n")
    for prompt in demo_prompts:
        result = bot.respond_with_metadata(prompt, max_new_tokens=15)
        print(f"  prompt:     '{prompt}'")
        print(f"  completion: '{result['completion']}'")
        print(f"  latency:    {result['total_ms']:.0f} ms total "
              f"({result['total_ms']/15:.0f} ms/tok)\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RBS-LM chatbot demo (R-RBS-LM-23)")
    parser.add_argument(
        "--instrument",
        default="docs/srmech/rbs_lm_research/rbs_lm_instrument_v18.bin",
        help="Instrument path (default: R-RBS-LM-18 Path C 491-obs)",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run scripted demo with hardcoded prompts (smoke test)",
    )
    parser.add_argument("--max-new", type=int, default=20)
    parser.add_argument("--no-path-c", action="store_true",
                        help="Use Path B (srmech-native vocab) instead of Path C")
    args = parser.parse_args()

    print(f"Loading chatbot...")
    bot = RBSChatbot.load(
        instrument_path=args.instrument,
        use_path_c=not args.no_path_c,
        verbose=True,
    )
    print(f"Loaded.")

    if args.demo:
        _scripted_demo(bot)
    else:
        _interactive_loop(bot, max_new_tokens=args.max_new)


if __name__ == "__main__":
    main()
