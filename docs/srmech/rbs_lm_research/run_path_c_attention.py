"""R-RBS-LM-19 — Path C + attention variant (MFO Mechanism 3).

Replaces the soft-bundle cleanup (Mechanism 2; ~6.9% averaging cost
per MFO §VII.1.3 line 741) with Class K per-position selection
(Mechanism 3; no averaging cost per line 751).

Per R-RBS-LM-20 §7: the 3.3% ceiling is consistent with the bundle-
averaging projection cost. If MFO is right about the mechanism asymmetry
being load-bearing here, attention should lift the ceiling. If
attention doesn't help, the diagnosis was wrong — informative either way.

INFERENCE CHANGE:
  Current Path C: ctx_vec = bundle(bind(token_k, P_k) for k in window)
                  cand = bind(instrument, ctx_vec)        # extracts via the bundled context
                  next_tid = argmin Hamming(cand, vocab_table_pc)

  Attention variant: per position k in last N positions:
                     cand_k = bind(instrument, bind(token_vec[k], P_k))  # one-position bind
                     best_tid_k, best_sim_k = cleanup(cand_k, vocab_table_pc)
                  Class K argmax over positions: winner_pos = argmax_k best_sim_k
                  next_tid = best_tid_{winner_pos}

Cost: N cleanups per query (vs 1 for Path C). At N=16, ~16× the per-query
work. For 180 generations: ~4 min vs ~1 min. Acceptable.

ENCODING UNCHANGED: same Path C corpus encoding from R-RBS-LM-17/-18; we
reuse rbs_lm_instrument_v18.bin (R-RBS-LM-18; 491 obs Path C at D=8192).

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/run_path_c_attention.py
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

from rbs_lm_encoder import CONTEXT_WINDOW, D, bind, position_vec, sentinel  # noqa: E402
from rbs_lm_inference import vectorised_cleanup  # noqa: E402
from rbs_lm_path_c import compute_path_c_vocab_table  # noqa: E402

from run_scale_genuine_mt import HALLUCINATION_PROMPTS  # noqa: E402


N_ATTEND = 16   # number of recent positions to test per query (computational tradeoff)
INSTRUMENT_PATH = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v18.bin")


def attention_next_token(instrument, prompt_tokens, vocab_table_pc, D=D, n_attend=N_ATTEND):
    """Class K per-position selection: test the last n_attend positions
    individually; pick the one with the highest cleanup similarity; return
    its best-matching token.

    Returns: (next_tid, winner_position, winner_sim, per_position_details).
    """
    ctx = prompt_tokens[-min(len(prompt_tokens), CONTEXT_WINDOW):]
    # Test only the last n_attend positions (compute tradeoff per module docstring)
    positions_to_test = list(range(max(0, len(ctx) - n_attend), len(ctx)))

    per_position = []
    for k in positions_to_test:
        token_vec = vocab_table_pc[ctx[k]].tobytes()
        bound = bind(token_vec, position_vec(k, D))
        cand = bind(instrument, bound)
        # cleanup against vocab
        res = vectorised_cleanup(cand, vocab_table_pc, D, top_k=1)
        best_tid, best_sim = res[0]
        per_position.append({
            "position": k,
            "token_at_position": int(ctx[k]),
            "best_tid": best_tid,
            "best_sim": best_sim,
        })

    # Class K argmax over positions
    winner = max(per_position, key=lambda d: d["best_sim"])
    return winner["best_tid"], winner["position"], winner["best_sim"], per_position


def main():
    print(f"=== R-RBS-LM-19 — Path C + attention variant (Class K per-position) ===")
    print(f"  torch threads: {torch.get_num_threads()}")
    print(f"  D = {D}, CONTEXT_WINDOW = {CONTEXT_WINDOW}, N_ATTEND = {N_ATTEND}")

    if not INSTRUMENT_PATH.exists():
        print(f"  ERROR: instrument {INSTRUMENT_PATH} not found — run R-RBS-LM-18 first")
        sys.exit(1)

    print(f"\nLoading source model + instrument...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()
    instrument = INSTRUMENT_PATH.read_bytes()
    print(f"  instrument: {len(instrument)} bytes (from R-RBS-LM-18: Path C; 491 obs; D=8192)")

    print(f"\nComputing Path C vocab table (D=8192; same seed as R-RBS-LM-17/-18)...")
    vocab_table_pc = compute_path_c_vocab_table(model, D=D, seed=42)

    # ---- validate with attention variant -----------------------------
    print(f"\n=== Validate on hallucination corpus (attention variant; N_ATTEND={N_ATTEND}) ===")
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
        prompt_winners = []  # which position won at each step
        for step in range(20):
            t0 = time.time()
            next_tid, winner_pos, winner_sim, _ = attention_next_token(
                instrument, rbs_tokens, vocab_table_pc, D, n_attend=N_ATTEND,
            )
            rbs_tokens.append(next_tid)
            prompt_lats.append((time.time() - t0) * 1000)
            prompt_winners.append((winner_pos, winner_sim))
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
            "avg_winner_position": float(np.mean([w[0] for w in prompt_winners])),
            "avg_winner_sim": float(np.mean([w[1] for w in prompt_winners])),
        })
        print(f"  '{prompt[:40]}...' → agreement {sum(agreement)}/20  "
              f"(avg winner pos {np.mean([w[0] for w in prompt_winners]):.1f}, "
              f"avg winner sim {np.mean([w[1] for w in prompt_winners]):+.4f})")
        if sum(agreement) > 0:
            print(f"    src:  {tokenizer.decode(src_new)[:80]}")
            print(f"    RBS:  {tokenizer.decode(rbs_new)[:80]}")

    overall = n_agree / n_total
    print(f"\n  Overall: {n_agree}/{n_total} ({100*overall:.1f}%)")
    print(f"  Per-token latency: {np.mean(latencies):.1f} ± {np.std(latencies):.1f} ms")

    print(f"\n=== Bundle vs attention comparison ===")
    print(f"  {'Configuration':<60} {'mechanism':>14} {'agreement':>12}")
    print(f"  {'Path C bundle cleanup (R-RBS-LM-18, 491 obs)':<60} {'M2 bundle':>14} {'3.3%':>12}")
    print(f"  {'Path C attention (R-RBS-LM-19, same instrument)':<60} {'M3 Class K':>14} "
          f"{100*overall:>11.1f}%")

    results = {
        "partition": "R-RBS-LM-19",
        "instrument_source": "R-RBS-LM-18 (Path C; 491 obs; D=8192)",
        "n_attend": N_ATTEND,
        "overall_agreement_pct": 100 * overall,
        "latency_ms_mean": float(np.mean(latencies)),
        "latency_ms_std": float(np.std(latencies)),
        "per_prompt_results": per_prompt_results,
        "comparison": {
            "path_c_bundle_491_pct": 3.3,
            "path_c_attention_491_pct": 100 * overall,
        },
    }
    Path("docs/srmech/rbs_lm_research/rbs_lm_attention_results.json").write_text(
        json.dumps(results, indent=2)
    )
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
