"""R-RBS-LM-130 — F166 Walk Step 5: the fully-realized artifact, end-to-end.

Demonstrates the native RBS-LM inference substrate as an INSTANTIABLE OBJECT:

    substrate = RBSLMInferenceSubstrate.from_catalog(catalog)   # build from SSOT
    substrate.learn(token_stream)                                # load knowledge
    text = substrate.infer(["the", "cat"], temperature=0.02)     # generate
    cands, probs = substrate.next_token_distribution(["the","cat"])  # distribution
    att = substrate.attestation()                                # MPR block

This is the F166 goal reached: a native, bit-exact, catalog-instantiable,
MPR-attested inference substrate built UP from the 28D Klein-4 coordinate — the
inversion of the Path-D float-distillation arc. It can be instantiated, learned,
queried, and ATTESTED.

Verifies the load-bearing property: DETERMINISM (same catalog + same corpus +
same seed → bit-exact identical generation; different seed → different but still
grammatical). srmech 0.5.0 native ABI=3.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from _rbs_lm_inference import RBSLMInferenceSubstrate

_spec = importlib.util.spec_from_file_location(
    "corpus_gen", HERE / "R-RBS-LM-113_larger_corpus_scaling.py")
corpus_gen = importlib.util.module_from_spec(_spec)
sys.modules["corpus_gen"] = corpus_gen
_spec.loader.exec_module(corpus_gen)

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_rbs_lm_inference.toml"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    # 1) INSTANTIATE from the catalog (the SSOT)
    sub = RBSLMInferenceSubstrate.from_catalog(args.catalog)
    print("=" * 78)
    print("INSTANTIATE  — RBSLMInferenceSubstrate.from_catalog(descriptor)")
    print("=" * 78)
    print(f"  {sub.describe()}")

    # 2) LEARN corpus knowledge (deterministic in the catalog's learn_seed)
    ic = None
    from srmech.amsc import load_descriptor
    desc = load_descriptor(args.catalog)
    corpus_n = int(desc.fetch["literature_curated"]["inference"]["context"]["corpus_n"])
    seed = int(desc.fetch["literature_curated"]["inference"]["context"]["seed"])
    rng = np.random.default_rng(seed)
    corpus = corpus_gen.generate_corpus(corpus_n, rng)
    stream = [t for sent in corpus for t in sent]
    sub.learn(stream)
    print("\n" + "=" * 78)
    print(f"LEARN  — .learn(stream of {len(stream)} tokens)")
    print("=" * 78)
    print(f"  {sub.describe()}")

    # 3) next-token DISTRIBUTION (Steps 2-3)
    print("\n" + "=" * 78)
    print("DISTRIBUTION  — .next_token_distribution(context)  [Steps 2-3]")
    print("=" * 78)
    for ctx_demo in (["the", "cat"], ["the", "scientist", "wrote"]):
        cands, probs = sub.next_token_distribution(ctx_demo)
        order = np.argsort(-probs)[:5]
        top = ", ".join(f"{cands[j]}={probs[j]:.3f}" for j in order)
        print(f"  P(next | {ctx_demo})  top-5: {top}")

    # 4) INFER — autoregressive generation (Step 4)
    print("\n" + "=" * 78)
    print(f"INFER  — .infer(prompt, T={sub.operating_temperature})  [Step 4]")
    print("=" * 78)
    for prompt in (["the", "cat"], ["a", "wolf"], ["the", "wizard"]):
        for s in (0, 1):
            out = sub.infer(prompt, max_tokens=18, seed=s)
            print(f"  seed={s}  {' '.join(out)}")

    # 5) DETERMINISM — same seed → bit-exact; different seed → different
    print("\n" + "=" * 78)
    print("DETERMINISM  — bit-exact reproducibility")
    print("=" * 78)
    a = sub.infer(["the", "cat"], max_tokens=20, seed=0)
    b = sub.infer(["the", "cat"], max_tokens=20, seed=0)
    c = sub.infer(["the", "cat"], max_tokens=20, seed=1)
    # also re-instantiate + re-learn from scratch → must reproduce
    sub2 = RBSLMInferenceSubstrate.from_catalog(args.catalog)
    rng2 = np.random.default_rng(seed)
    stream2 = [t for s in corpus_gen.generate_corpus(corpus_n, rng2) for t in s]
    sub2.learn(stream2)
    d = sub2.infer(["the", "cat"], max_tokens=20, seed=0)
    print(f"  same instance, same seed  → identical: {a == b}")
    print(f"  same instance, diff seed  → different: {a != c}")
    print(f"  fresh instance, same seed → identical: {a == d}  (bit-exact across instantiation)")

    # 6) ATTESTATION — the MPR block making any output re-derivable + citable
    print("\n" + "=" * 78)
    print("ATTESTATION  — .attestation()  [MPR block]")
    print("=" * 78)
    att = sub.attestation()
    for key in ("method", "descriptor_hash", "srmech_version", "abi_version",
                "has_native", "operating_k", "operating_temperature", "n_learned",
                "vocab_size", "substrate"):
        print(f"  {key:22s}: {att[key]}")

    # persist a small attested generation record
    out_rec = {**att, "phase": "P5_instantiable_demo",
               "determinism_same_seed": a == b,
               "determinism_cross_instance": a == d,
               "determinism_diff_seed_differs": a != c,
               "example_generation": a}
    out = args.catalog.parent / "substrate_measurements" / "inference_step5_instrument.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write(json.dumps(out_rec, default=str) + "\n")
    print(f"\nResults: {out}")

    ok = (a == b) and (a == d) and (a != c)
    print("\n" + "=" * 78)
    print(f"STEP 5 VERDICT: instantiable inference substrate {'WORKS' if ok else 'FAILED'} "
          f"— build→learn→infer→attest, bit-exact across instantiation: {ok}")
    print("  The F166 goal: a native, srmech-instantiable, MPR-attested RBS-LM")
    print("  inference substrate from 28D maths — NOT a float distillation.")


if __name__ == "__main__":
    main()
