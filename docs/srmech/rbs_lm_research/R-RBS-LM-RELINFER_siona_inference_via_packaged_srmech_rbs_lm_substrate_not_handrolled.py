"""R-RBS-LM-RELINFER (F834) — Siona recall IS inference on relationships, via the PACKAGED srmech tooling
(`srmech.rbs_lm`, the F166 RBS-LM inference substrate), NOT a hand-rolled store.

The whole-session error this corrects: I built classical stores (a {random-HV: token} dictionary, then a byte-packed
id-stream) and called them "RBS-HDC", reaching for storage reflexes instead of srmech's HDC tooling. The tooling
already exists and ships native:

    srmech.rbs_lm.RBSLMInferenceSubstrate.from_params(params)   # the relationship-inference substrate
      .learn(token_stream)   -> builds the relationship state: the bound memory M + next_after + bigram_counts
      .infer(prompt, ...)    -> the F166 autoregressive walk (grounded inference, NOT readback)
      .next_token_distribution(context) -> the context-conditioned next-token distribution
    srmech.rbs_lm.sim_k4_batch(query, candidates)               # the batched resonance / cleanup
    srmech.rbs_lm.substrate.ContextSubstrate(...)               # the rolling context-state encoder

This is "inference on relationships": the article's context->successor relationships are LEARNED into a Klein-4
bound-memory substrate; recall COMPOSES a grounded continuation by resonance — grounded (every token from the
learned relationships) but not bit-exact (recombined, not replayed) — the inference signature. The kernels are the
learned substrate state; the genome's job is to CONSOLIDATE those kernels (agnostically), not re-encode the corpus.

Verified (srmech 0.8.1, native): tomato -> learned 387/4000 relationships; infer from "the tomato solanum
lycopersicum" -> a grounded tomato continuation that diverges from the verbatim body (ketchup / many small seeds /
south america wild versions were poisonous — real tomato facts, recombined). See R-RBS-LM-FINDING_834.

srmech edge-case found: infer(temperature=0.0) -> ZeroDivisionError in the substrate softmax (no greedy fallback);
use temperature>0. Logged UPSTREAM_NOTES §56.

No hand-rolled HDC: every op is srmech.rbs_lm. Composes F166 (the walk), F806-F809 (the per-article bundle-record),
F826 (genome = consolidate RBS-HDC kernels), §9 (the upstream-absorbed RBS-LM substrate).
"""
import json
from pathlib import Path

from srmech.rbs_lm import RBSLMInferenceSubstrate
import srmech

INST = Path.home() / "corpora" / "wikipedia" / "simplewiki_rawbody_instrument.ndjson"
IDX = Path.home() / "corpora" / "wikipedia" / "simplewiki_rawbody_index.json"

PARAMS = {
    "substrate": {"D": 10000, "token_seed_hex_chars": 16},
    "inference": {"instrument": {"operating_k": 3, "operating_temperature": 0.3,
                                 "memory_capacity": 4000, "default_max_tokens": 60, "learn_seed": 0}},
}


def load(title):
    off = json.loads(IDX.read_text())[title.lower()]
    with open(INST) as f:
        f.seek(off)
        return json.loads(f.readline())["s"].split()


def main():
    toks = load("tomato")
    sub = RBSLMInferenceSubstrate.from_params(PARAMS)   # the packaged relationship-inference substrate
    sub.learn(toks)                                     # learn the relationships (native Klein-4 bound memory)
    print(f"srmech {srmech.__version__} | {sub.describe()}")
    prompt = toks[:4]
    out = sub.infer(prompt, max_tokens=40, temperature=0.3)   # the F166 walk — grounded inference, not readback
    print("\nprompt:", " ".join(prompt))
    print("infer :", " ".join(out))
    print("truth :", " ".join(toks[:len(out)]))
    print("\nnext_token_distribution(['the','tomato','solanum']) ->", sub.next_token_distribution(toks[:3]))


if __name__ == "__main__":
    main()
