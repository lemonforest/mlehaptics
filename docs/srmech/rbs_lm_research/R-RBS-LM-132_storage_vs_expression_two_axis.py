"""R-RBS-LM-132 — F169: control the confound; separate STORAGE structure from
SURFACE repetition (the two-axis test of the storage/expression hypothesis).

F168 §5.1 caveat: resolution depth conflated intrinsic structure with
repetition-density × data budget. Here we CONTROL both:
  - match TOKEN BUDGET (same contiguous token count per corpus)
  - match VOCAB (same top-V; rest → <unk>; score only in-vocab targets)
so resolution depth becomes a clean INTRINSIC = the STORAGE axis.

Then we report SURFACE REPETITION (1 - distinct-trigram ratio of the corpus
itself) as a SEPARATE axis = the EXPRESSION/rendering axis.

The hypothesis (user 2026-05-29): storage and expression are SEPARABLE axes. If,
once the confounds are stripped, the STORAGE depth is ~invariant across texts
while SURFACE repetition varies independently (low cross-corpus correlation),
then knowledge-storage is shared and only the arts-of-communication layer
differs — the dignity-affirming "same knowing, different channel" reading, and
the structural ground for the LLM-as-expression-prosthetic (ADA) motivation.

SCOPE (load-bearing): STRUCTURAL test on TEXT OBJECTS only. NOT a clinical claim
about real NT/ND cognition. §VII.6.20: form-reading, not substrate-identity. The
NT/ND interpretation is the user's motivating conjecture, engaged as form.

Reuses R-RBS-LM-131's n-gram/backoff machinery. srmech 0.5.0 native ABI=3.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# reuse 131's ngram/backoff functions + corpus loaders
_spec = importlib.util.spec_from_file_location(
    "r131", HERE / "R-RBS-LM-131_emergent_perplexity_resolution_depth.py")
r131 = importlib.util.module_from_spec(_spec)
sys.modules["r131"] = r131
_spec.loader.exec_module(r131)

corpus_gen = r131.corpus_gen
k1mod = r131.k1mod
from srmech.amsc import load_descriptor, descriptor_hash
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"
UNK = "<unk>"


def cap_vocab(stream, V):
    """Keep top-V types; map the rest to <unk>. Returns capped stream + kept set."""
    freq = Counter(stream)
    keep = {t for t, _ in freq.most_common(V)}
    return [t if t in keep else UNK for t in stream], keep


def surface_repetition(stream):
    """1 - distinct-trigram ratio of the corpus itself = how much it repeats."""
    trig = [(stream[i], stream[i + 1], stream[i + 2]) for i in range(len(stream) - 2)]
    if not trig:
        return 0.0
    return float(1.0 - len(set(trig)) / len(trig))


def profile_matched(stream, max_order, n_test, rng):
    """Backoff accuracy by max-order, scoring only positions whose TRUE token is
    in-vocab (not <unk>), on a budget+vocab-matched stream."""
    half = len(stream) // 2
    train, test = stream[:half], stream[half:]
    models = r131.build_ngram_models(train, max_order)
    positions = [i for i in range(max_order, len(test)) if test[i] != UNK]
    if len(positions) > n_test:
        positions = list(rng.choice(positions, size=n_test, replace=False))
    backoff = {K: 0 for K in range(1, max_order + 1)}
    for i in positions:
        true = test[i]
        ctx = test[:i]
        for K in range(1, max_order + 1):
            p, _ = r131.backoff_predict(models, K, ctx)
            if p == true:
                backoff[K] += 1
    ntot = max(len(positions), 1)
    backoff_acc = {K: backoff[K] / ntot for K in backoff}
    return backoff_acc, len(positions)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    texts = lc["corpus"]["texts"]
    cc = lc["confound_control"]
    budget = int(cc["budget_tokens"])
    V_cfg = int(cc["shared_vocab"])
    max_order = int(cc["max_order"])
    seed = int(cc["seed"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print("STRUCTURAL test on TEXT OBJECTS only; NOT a clinical claim (§VII.6.20).\n")

    # load the 6 real-language corpora (full token streams)
    raw = {}
    for key, meta in texts.items():
        body = k1mod.strip_gutenberg((cache_dir / meta["filename"]).read_text(
            encoding="utf-8", errors="replace"))
        raw[key] = (meta["family"], k1mod.tokenize(body))

    # clamp budget to the smallest corpus; clamp V to the smallest budget-vocab
    budget = min(budget, min(len(toks) for _, toks in raw.values()))
    budget_samples = {k: toks[:budget] for k, (_f, toks) in raw.items()}
    V = min(V_cfg, min(len(set(s)) for s in budget_samples.values()))
    print(f"MATCHED budget = {budget} tokens/corpus;  MATCHED vocab V = {V} types "
          f"(rest → <unk>)\n")

    rng = np.random.default_rng(seed)
    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "budget_tokens": budget, "shared_vocab": V,
              "scope": "STRUCTURAL two-axis storage/expression; text objects; §VII.6.20; no clinical claims"}
    records = []

    print("TWO AXES — controlled STORAGE depth (matched budget+vocab) vs SURFACE repetition")
    print(f"{'corpus':>16} | {'fam':>9} | {'storage_depth':>13} | {'top_K_acc':>9} | "
          f"{'surface_rep':>11} | {'raw_vocab':>9}")
    print("-" * 82)
    depths, reps = [], []
    for key, (fam, toks) in raw.items():
        sample = toks[:budget]
        raw_vocab = len(set(sample))
        capped, _keep = cap_vocab(sample, V)
        rng_c = np.random.default_rng(seed)
        ba, npos = profile_matched(capped, max_order, 4000, rng_c)
        depth = r131.resolution_depth(ba, max_order)
        rep = surface_repetition(sample)   # surface repetition on the UNcapped budget sample
        depths.append(depth)
        reps.append(rep)
        records.append({**attest, "phase": "P1_two_axis", "corpus": key, "family": fam,
                        "storage_depth": depth, "backoff_acc": ba, "top_K_acc": ba[max_order],
                        "surface_repetition": rep, "raw_vocab_in_budget": raw_vocab,
                        "n_scored": npos})
        print(f"{key[:16]:>16} | {fam:>9} | {depth:>13} | {ba[max_order]:>9.3f} | "
              f"{rep:>11.3f} | {raw_vocab:>9}")

    # separability: correlation between the two axes across the 6 corpora
    depths_a = np.array(depths, dtype=float)
    reps_a = np.array(reps, dtype=float)
    if depths_a.std() > 1e-9 and reps_a.std() > 1e-9:
        corr = float(np.corrcoef(depths_a, reps_a)[0, 1])
    else:
        corr = float("nan")
    depth_spread = float(depths_a.max() - depths_a.min())
    depth_mean = float(depths_a.mean())

    # the template control (synthetic shallow floor), reported separately
    trng = np.random.default_rng(seed)
    tstream = [t for s in corpus_gen.generate_corpus(2000, trng) for t in s][:budget]
    tcap, _ = cap_vocab(tstream, min(V, len(set(tstream))))
    tba, _ = profile_matched(tcap, max_order, 4000, np.random.default_rng(seed))
    tdepth = r131.resolution_depth(tba, max_order)
    trep = surface_repetition(tstream)

    print("\n" + "-" * 82)
    print(f"{'template_control':>16} | {'control':>9} | {tdepth:>13} | {tba[max_order]:>9.3f} | "
          f"{trep:>11.3f} | {len(set(tstream)):>9}   (synthetic shallow floor)")

    records.append({**attest, "phase": "P2_separability",
                    "storage_depth_mean": depth_mean, "storage_depth_spread": depth_spread,
                    "axis_correlation": corr, "n_corpora": len(depths),
                    "template_depth": tdepth, "template_surface_rep": trep})

    out = args.catalog.parent / "substrate_measurements" / "storage_vs_expression_two_axis.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")

    print("\n" + "=" * 82)
    print("F169 READING (storage vs expression — separable axes?):")
    print("=" * 82)
    print(f"  controlled STORAGE depth across 6 texts: mean {depth_mean:.2f}, "
          f"spread {depth_spread:.0f} (max-min)")
    print(f"  SURFACE repetition range: {reps_a.min():.3f} .. {reps_a.max():.3f}")
    print(f"  axis correlation (depth vs surface-rep): {corr:+.3f}")
    if abs(corr) < 0.4 and depth_spread <= 1:
        print("  → storage depth ~INVARIANT + surface repetition varies independently")
        print("    ⇒ SEPARABLE axes (structural support: same storage, different expression)")
    elif abs(corr) >= 0.7:
        print("  → depth and surface-rep CORRELATED ⇒ not cleanly separable on this set")
        print("    (the repetition IS the deep structure here; honest non-separation)")
    else:
        print("  → partial separation; depth varies somewhat, correlation modest — report as-is")
    print("\n  Compare to UNCONTROLLED (R-RBS-LM-131): depths were 2/4/3/3/2/2 (KJV-NT=4).")
    print("  Any depth that MOVED under control was confound (vocab/budget), not structure.")


if __name__ == "__main__":
    main()
