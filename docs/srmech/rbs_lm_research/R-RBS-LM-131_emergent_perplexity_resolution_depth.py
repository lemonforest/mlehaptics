"""R-RBS-LM-131 — F168 test: emergent perplexity as resolution-level (chirality-sector) depth.

Reads perplexity off the STRUCTURE, never a forced softmax (the F166 Step 2-3
correction). The n-gram orders ARE the F155 structural levels = the chirality
sectors (word=order 1, bigram=order 2, … long-range=higher). The substrate
resolves a future at the DEEPEST level (sector) whose context fires — that is
backoff. So:

  emergent profile  = backoff_accuracy(max_order = K) as K rises 1 → max_order
  resolution DEPTH  = the order beyond which the profile plateaus
                      (the deepest sector the corpus's structure actually populates)

NO temperature, NO softmax — the spread is the substrate's own. Perplexity is
the shape of this profile, not a scalar laid on top.

F168 §5 prediction: the TEMPLATE corpus (F166 Step 4) plateaus early (~order 2 —
its long-range sectors are empty); a corpus with REAL long-range structure (the
F165 religious-text kernels — verse parallelism, formulaic openings) keeps
gaining accuracy at higher orders → its deeper sectors POPULATE → that is what
raises legality where the template could not. Null outcomes count (F168 §5).

Per-text = DOMAIN-anchored (each labeled kernel its own domain, F165 Rosetta
Stone operational). Plus a Klein-4 sector-occupancy realization: the per-order
continuations bound into distinct chirality sectors (klein4), occupancy read by
unbind+similarity — the literal "binding possible continuations into distinct
chirality-tagged sectors."

Catalog-driven (descriptor_religious_texts.toml [emergent_perplexity]); srmech
0.5.0 native ABI=3; structural-only per §VII.6.20 (texts are test-objects).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs

_spec_c = importlib.util.spec_from_file_location(
    "corpus_gen", HERE / "R-RBS-LM-113_larger_corpus_scaling.py")
corpus_gen = importlib.util.module_from_spec(_spec_c)
sys.modules["corpus_gen"] = corpus_gen
_spec_c.loader.exec_module(corpus_gen)

_spec_k = importlib.util.spec_from_file_location(
    "k1mod", HERE / "R-RBS-LM-124_k1_baseline_chirality_lift.py")
k1mod = importlib.util.module_from_spec(_spec_k)
sys.modules["k1mod"] = k1mod
_spec_k.loader.exec_module(k1mod)

from srmech.amsc import load_descriptor, descriptor_hash, hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"
MAX_TOKENS = 80000   # tractability cap per corpus stream


def build_ngram_models(train, max_order):
    """models[n] : dict[(n-1)-tuple context] -> Counter(next_token), for n=1..max_order."""
    models = {n: defaultdict(Counter) for n in range(1, max_order + 1)}
    for i in range(len(train)):
        for n in range(1, max_order + 1):
            if i >= n - 1:
                ctx = tuple(train[i - (n - 1):i])
                models[n][ctx][train[i]] += 1
    return models


def order_predict(models, n, context):
    """argmax next under the order-n model given the (n-1)-token context; None if unseen."""
    ctx = tuple(context[-(n - 1):]) if n > 1 else ()
    c = models[n].get(ctx)
    if not c:
        return None
    return c.most_common(1)[0][0]


def backoff_predict(models, K, context):
    """deepest sector that fires: highest order n<=K whose context is seen."""
    for n in range(K, 0, -1):
        p = order_predict(models, n, context)
        if p is not None:
            return p, n
    return None, 0


def profile_corpus(stream, max_order, n_test, rng):
    """Return per-order standalone accuracy + backoff-accuracy-by-max-order + min-resolving-order."""
    half = len(stream) // 2
    train, test = stream[:half], stream[half:]
    models = build_ngram_models(train, max_order)

    positions = [i for i in range(max_order, len(test))]
    if len(positions) > n_test:
        positions = list(rng.choice(positions, size=n_test, replace=False))

    standalone = {n: [0, 0] for n in range(1, max_order + 1)}  # [correct, total]
    backoff = {K: 0 for K in range(1, max_order + 1)}
    min_order_hist = Counter()                                  # deepest-needed resolution
    for i in positions:
        true = test[i]
        ctx = test[:i]
        # standalone per-order (unseen context counts as miss)
        for n in range(1, max_order + 1):
            p = order_predict(models, n, ctx)
            standalone[n][1] += 1
            if p == true:
                standalone[n][0] += 1
        # backoff per max-order
        for K in range(1, max_order + 1):
            p, _n = backoff_predict(models, K, ctx)
            if p == true:
                backoff[K] += 1
        # min resolving order: the SMALLEST order whose standalone prediction is right
        mr = next((n for n in range(1, max_order + 1)
                   if order_predict(models, n, ctx) == true), 0)
        min_order_hist[mr] += 1

    ntot = len(positions)
    standalone_acc = {n: standalone[n][0] / standalone[n][1] for n in standalone}
    backoff_acc = {K: backoff[K] / ntot for K in backoff}
    return {"n_positions": ntot, "vocab_train": len(set(train)),
            "standalone_acc": standalone_acc, "backoff_acc": backoff_acc,
            "min_order_hist": dict(min_order_hist)}


def resolution_depth(backoff_acc, max_order, thresh=0.005):
    """deepest order whose marginal backoff lift >= thresh."""
    depth = 1
    for K in range(2, max_order + 1):
        if backoff_acc[K] - backoff_acc[K - 1] >= thresh:
            depth = K
    return depth


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    D = int(lc["substrate"]["D"])
    hexc = int(lc["substrate"]["token_seed_hex_chars"])
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    texts = lc["corpus"]["texts"]
    ep = lc["emergent_perplexity"]
    max_order = int(ep["max_order"])
    n_units = int(ep["n_units_per_text"])
    n_test = int(ep["test_positions"])
    seed = int(ep["seed"])
    do_demo = bool(ep["klein4_sector_demo"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"max_order={max_order} (resolution sectors)  n_units/text={n_units}  test_positions={n_test}\n")
    print("STRUCTURAL-ONLY per §VII.6.20: texts are test-objects; no doctrinal claims.\n")

    rng = np.random.default_rng(seed)

    # --- assemble corpora: template control (shallow) + religious texts (deep) ---
    corpora = {}
    tmpl_rng = np.random.default_rng(seed)
    tmpl = corpus_gen.generate_corpus(2000, tmpl_rng)
    corpora["template_control"] = ("control", [t for s in tmpl for t in s][:MAX_TOKENS])
    for key, meta in texts.items():
        path = cache_dir / meta["filename"]
        body = k1mod.strip_gutenberg(path.read_text(encoding="utf-8", errors="replace"))
        toks = k1mod.tokenize(body)[:MAX_TOKENS]
        corpora[key] = (meta["family"], toks)

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "max_order": max_order,
              "scope": "STRUCTURAL resolution-depth; no doctrinal claims; §VII.6.20"}
    records = []

    # --- per-corpus resolution profile (domain-anchored) ---
    print("BACKOFF ACCURACY by max-order (= deepest chirality sector allowed to fire)")
    hdr = "  ".join(f"K={K}" for K in range(1, max_order + 1))
    print(f"{'corpus':>20} | {'fam':>9} | {'vocab':>6} | {hdr} | depth")
    print("-" * (44 + 8 * max_order))
    for key, (fam, stream) in corpora.items():
        rng_c = np.random.default_rng(seed)
        prof = profile_corpus(stream, max_order, n_test, rng_c)
        ba = prof["backoff_acc"]
        depth = resolution_depth(ba, max_order)
        cells = "  ".join(f"{ba[K]:.3f}" for K in range(1, max_order + 1))
        print(f"{key[:20]:>20} | {fam:>9} | {prof['vocab_train']:>6} | {cells} | {depth}")
        records.append({**attest, "phase": "P1_resolution_depth", "corpus": key,
                        "family": fam, "vocab_train": prof["vocab_train"],
                        "n_positions": prof["n_positions"],
                        "standalone_acc": prof["standalone_acc"],
                        "backoff_acc": ba, "resolution_depth": depth,
                        "min_order_hist": prof["min_order_hist"]})

    # --- deep-sector occupancy: fraction of futures that REQUIRE order >= 3 ---
    print("\nDEEP-SECTOR OCCUPANCY — fraction of correctly-resolved futures needing order >= 3")
    print("(bigram/order-2 alone would MISS these; the deep sectors are load-bearing)")
    print(f"{'corpus':>20} | {'fam':>9} | {'order>=3 share':>14} | {'order>=4 share':>14}")
    print("-" * 66)
    for r in records:
        h = r["min_order_hist"]
        resolved = sum(v for k, v in h.items() if int(k) >= 1)
        deep3 = sum(v for k, v in h.items() if int(k) >= 3)
        deep4 = sum(v for k, v in h.items() if int(k) >= 4)
        s3 = deep3 / resolved if resolved else 0.0
        s4 = deep4 / resolved if resolved else 0.0
        r["deep_sector_share_ge3"] = s3
        r["deep_sector_share_ge4"] = s4
        print(f"{r['corpus'][:20]:>20} | {r['family']:>9} | {s3:>14.3f} | {s4:>14.3f}")

    # --- Klein-4 sector realization: continuations bound into distinct sectors ---
    if do_demo:
        print("\n" + "=" * 78)
        print("KLEIN-4 SECTOR REALIZATION — possible continuations bound into distinct sectors")
        print("=" * 78)
        ctx = cs.ContextSubstrate(D=D, hex_chars=hexc)
        demo_key = "kjv_ot" if "kjv_ot" in corpora else list(corpora)[1]
        _, stream = corpora[demo_key]
        half = len(stream) // 2
        models = build_ngram_models(stream[:half], min(max_order, 4))
        test = stream[half:]
        within, cross = [], []
        n_demo = 0
        for i in range(4, len(test)):
            if n_demo >= 200:
                break
            preds = [order_predict(models, n, test[:i]) for n in range(1, 5)]
            if any(p is None for p in preds):
                continue
            # bind each order's predicted continuation into its OWN Klein-4 sector
            sector_vecs = [cs.encode_word_k4(preds[s], D=D, sector=s, hex_chars=hexc)
                           for s in range(4)]
            bundle = ctx.bundle_odd(sector_vecs)
            # read occupancy: each future recoverable from its own sector vs others
            for s in range(4):
                probe = cs.encode_word_k4(preds[s], D=D, sector=s, hex_chars=hexc)
                within.append(float(cs.sim_k4_batch(bundle, probe[None, :])[0]))
                s_other = (s + 1) % 4
                probe_x = cs.encode_word_k4(preds[s], D=D, sector=s_other, hex_chars=hexc)
                cross.append(float(cs.sim_k4_batch(bundle, probe_x[None, :])[0]))
            n_demo += 1
        wm, cm = float(np.mean(within)), float(np.mean(cross))
        print(f"  {demo_key}: {n_demo} contexts; futures bound into 4 distinct sectors")
        print(f"  within-sector recovery sim = {wm:.4f}   cross-sector sim = {cm:.4f}   "
              f"contrast = {wm / cm if cm > 1e-6 else float('inf'):.2f}")
        print(f"  → futures are HELD in distinct chirality-tagged sectors (within >> cross): "
              f"{wm > cm + 0.05}")
        records.append({**attest, "phase": "P2_klein4_sector_occupancy", "corpus": demo_key,
                        "n_contexts": n_demo, "within_sector_sim": wm,
                        "cross_sector_sim": cm,
                        "futures_held_distinctly": bool(wm > cm + 0.05)})

    out = args.catalog.parent / "substrate_measurements" / "emergent_perplexity_resolution_depth.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")

    # --- headline: template (shallow) vs religious (deep) ---
    ctrl = next(r for r in records if r["corpus"] == "template_control")
    rel = [r for r in records if r.get("family") in ("abrahamic", "eastern")]
    print("\n" + "=" * 78)
    print("F168 READING — does real long-range structure populate deeper sectors?")
    print("=" * 78)
    print(f"  template control : resolution depth {ctrl['resolution_depth']}, "
          f"order>=3 share {ctrl['deep_sector_share_ge3']:.3f}  (the shallow baseline)")
    md = float(np.mean([r["resolution_depth"] for r in rel]))
    ms3 = float(np.mean([r["deep_sector_share_ge3"] for r in rel]))
    print(f"  religious (mean) : resolution depth {md:.1f}, order>=3 share {ms3:.3f}")
    deeper = md > ctrl["resolution_depth"] and ms3 > ctrl["deep_sector_share_ge3"]
    print(f"  → real long-range corpora resolve DEEPER than the template: {deeper}")
    print(f"    (F168 §5: deeper sectors populate where the template's stay empty)")


if __name__ == "__main__":
    main()
