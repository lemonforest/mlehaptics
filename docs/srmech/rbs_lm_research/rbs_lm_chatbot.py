"""R-RBS-LM-23 — Scriptable wrapper around the RBS-LM inference cascade.

Trimmed to class-only in R-RBS-LM-24: the REPL + scripted demo + custom CLI
were retired when the OpenAI-API-compatible server (`rbs_lm_server.py`)
became the canonical user-facing interface. CopilotKit / AG2 / LangChain /
LlamaIndex / Continue / Cursor / Open WebUI / LiteLLM / DSPy / Pydantic AI
all speak the OpenAI-API as the lingua franca; we stop maintaining our own
presentation layer and serve via the standard the ecosystem already uses.

Per `[[user_stance_ai_is_not_a_substrate]]`: this is a transducer of stored
content — a puppet playing the roll. The class encapsulates the Path C
cascade as a callable; the orchestration layer (multi-agent loops, RAG,
tool-call routing) lives in the upstream code, NOT in this local expert.

Scripted usage:
    from rbs_lm_chatbot import RBSChatbot
    bot = RBSChatbot.load(instrument_path="...", use_path_c=True)
    reply = bot.respond("Hello there", max_new_tokens=20)

When the work absorbs into srmech (R-RBS-LM-12 §6), this becomes
`srmech.rbs_lm.chatbot.RBSChatbot`; the load path becomes
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
    R-RBS-LM-19 falsification, attention variant slows by ~16x without
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

        del model
        return cls(instrument, vocab_table, tokenizer, use_path_c)

    def respond(self, prompt, max_new_tokens=20):
        """Generate a response to a prompt. Returns the generated text (not including the prompt)."""
        prompt_ids = self.tokenizer.encode(prompt)
        new_tokens, _ = self._generate(prompt_ids, max_new_tokens)
        return self.tokenizer.decode(new_tokens)

    def respond_with_metadata(self, prompt, max_new_tokens=20, context_truncation=None):
        """Generate a response and return metadata: completion text, latencies, token IDs.

        If context_truncation is not None, override the encoder's CONTEXT_WINDOW
        with the given value (used by the R-RBS-LM-24 truncation experiment).
        """
        prompt_ids = self.tokenizer.encode(prompt)
        t0 = time.time()
        new_tokens, latencies = self._generate(prompt_ids, max_new_tokens,
                                                context_truncation=context_truncation)
        total_elapsed = time.time() - t0
        return {
            "prompt": prompt,
            "completion": self.tokenizer.decode(new_tokens),
            "prompt_token_ids": prompt_ids,
            "new_token_ids": new_tokens,
            "per_token_ms": latencies,
            "total_ms": total_elapsed * 1000,
        }

    def _generate(self, prompt_ids, max_new_tokens, context_truncation=None):
        """Internal generation loop. Returns (new_tokens, per_token_latencies_ms)."""
        from rbs_lm_encoder import CONTEXT_WINDOW, D, bind
        from rbs_lm_inference import vectorised_cleanup

        window = context_truncation if context_truncation is not None else CONTEXT_WINDOW

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
            ctx = tokens[-window:] if len(tokens) > window else tokens
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
