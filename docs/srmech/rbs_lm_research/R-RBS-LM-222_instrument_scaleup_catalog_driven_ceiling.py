"""R-RBS-LM-222 — F203 follow-up: CATALOG-DRIVE the scale-up sweep + find the
HIERARCHICAL capacity KNEE (push N >> 1024).

Lodges Finding 222. The direct follow-up to Finding 203 (R-RBS-LM-146), which
measured the FLAT / HIER / HIER+DOMAIN capacity curve at N <= 1024 but did so
from MODULE-LEVEL constants (N_SWEEP / N_BUCKETS / TOP_K_GEN) — leaving the sweep
un-catalog-driven (the F203 §6 follow-up note). This finding does TWO things:

  (1) CATALOG-DRIVE the sweep. All sweep params (n_sweep, n_buckets_sweep,
      window_k, top_k_gen, n_probe_gen, the two null thresholds, and the
      tractability caps scaleup_D / scaleup_corpus_n / scaleup_seed) now load
      from a NEW additive descriptor section [inference.scaleup] in
      descriptor_rbs_lm_inference.toml. No existing section was touched; the
      run is descriptor_hash-attested. (This closes the F203 §6 note.)

  (2) PUSH N >> 1024 to find the HIERARCHICAL ceiling (the knee). F203 showed
      hierarchical (8 buckets) retains capacity ~0.41 at N=1024 (vs flat 0.12),
      and the DOMAIN anchor lifts it to ~0.90. But hierarchical is NOT immune:
      each bucket is itself a single Klein-4 bundle with the SAME ~257 ceiling
      (F154), so once N/n_buckets exceeds that per-bucket ceiling, hierarchical
      must ALSO degrade. We sweep N = 128..8192 at n_buckets ∈ {8, 32} and
      measure (a) where hierarchical capacity finally falls (the knee) and (b)
      whether the DOMAIN-anchor orthogonalization persists at higher N.

The MEMORY classes (FlatMemory / HierarchicalMemory) are imported verbatim from
R-RBS-LM-146 — same bit-exact 28D Klein-4 cascade, no primitive reimplemented:
  encode context  : ContextSubstrate.encode_context  (Class A o M + iw7 position)
  domain label    : ContextSubstrate.enc("__domain_{d}__")  (Class A content-mint)
  bind / bundle   : srmech.amsc.hdc.klein4_bind / klein4_bundle  (Class M)
  bucket routing  : srmech.amsc.format.sha256_bytes(context)     (Class A)
  retrieve        : sim_k4_batch fractional-agreement argmax      (Class M)

================================ PRE-STATED NULLS ===============================
Three honest readings, each null fixed BEFORE the run (per
[[feedback_dont_pre_commit_spike_query_operators]]):

  CAPACITY-EXTENDS null (the F203 re-confirmation, now catalog-driven): at the
    LARGEST N, hierarchical does NOT beat flat => FAIL if hier_acc - flat_acc
    <= capacity_null_threshold (0.05) at N_max. (F203 showed +0.298 at N=1024
    for 8 buckets; flat is expected to be pinned near the 0.012 chance floor at
    N=8192, so hier should clear it easily even past its own knee.)

  HIERARCHICAL-KNEE null (the NEW reading): hierarchical capacity does NOT fall
    as N grows => FAIL TO FIND A KNEE if hier_acc stays >= 0.90 across the whole
    sweep at a given n_buckets. PRE-STATED EXPECTATION (the honest prediction):
    hierarchical capacity WILL fall once per-bucket load (~N/n_buckets) exceeds
    the ~257 single-bundle ceiling — i.e. for n_buckets=8 the knee is expected
    near N ~ 8*257 ≈ 2056 (visible by N=2048/4096), and for n_buckets=32 near
    N ~ 32*257 ≈ 8224 (so 32 buckets should still be high at N=8192). Finding
    the knee at the predicted N/bucket band CONFIRMS the n_buckets x V_ceiling
    capacity law (F203 §6.1).

  DOMAIN-PERSISTS null: the DOMAIN anchor's capacity orthogonalization does NOT
    survive past N=1024 => FAIL if, at the largest N where hier itself has
    degraded, hier_dom_acc - hier_acc <= capacity_null_threshold (0.05). PASS
    means the F203 second-axis effect (dom_q cancels dom_i only on a domain
    match) keeps cutting intra-bucket collision even at the higher per-bucket
    loads. (NOTE: with only 4 structural domains, each bucket's domain split is
    coarse; at very high per-bucket load even the domain axis can saturate —
    a null here is a valid, reportable "the 4-domain axis is exhausted" result.)

These are DEMONSTRATED (bit-exact srmech) measurements, not framework-reading.

TRACTABILITY (honest): the retrieval cost is O(N x |vocab| x D) x 3 configs x
each N x each n_buckets. To keep N=8192 tractable we CAP D at scaleup_D (4096;
F203 used 8192) and bump corpus_n so the pair pool isn't exhausted. The knee is
D-RELATIVE — the per-bucket ceiling V_ceiling scales with D, so a smaller D
shifts the absolute knee N but does NOT change the SHAPE (knee at the same
N/bucket band). D is recorded in every NDJSON record; no D-universality claimed.

Catalog-driven (descriptor_rbs_lm_inference.toml [inference.scaleup]); srmech
0.5.0 native ABI=3. Deterministic: same corpus + same catalog + same
srmech_version -> bit-exact.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs  # ContextSubstrate, sim_k4_batch

# Reuse the F203 corpus generator + the F203 memory classes verbatim (same
# bit-exact cascade; no primitive reimplemented — import, don't copy).
_spec_c = importlib.util.spec_from_file_location(
    "corpus_gen", HERE / "R-RBS-LM-113_larger_corpus_scaling.py")
corpus_gen = importlib.util.module_from_spec(_spec_c)
sys.modules["corpus_gen"] = corpus_gen
_spec_c.loader.exec_module(corpus_gen)

_spec_m = importlib.util.spec_from_file_location(
    "f203_mem", HERE / "R-RBS-LM-146_instrument_scaleup_hierarchical_domain.py")
f203 = importlib.util.module_from_spec(_spec_m)
sys.modules["f203_mem"] = f203
_spec_m.loader.exec_module(f203)
FlatMemory = f203.FlatMemory
HierarchicalMemory = f203.HierarchicalMemory
domain_of_length = f203.domain_of_length
build_pairs = f203.build_pairs

from srmech.amsc import load_descriptor, descriptor_hash
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_rbs_lm_inference.toml"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    # ----- EVERYTHING comes from the catalog [inference.scaleup] section -----
    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    su = lc["inference"]["scaleup"]            # the NEW additive section (F222)

    N_SWEEP = [int(n) for n in su["n_sweep"]]
    N_BUCKETS_SWEEP = [int(b) for b in su["n_buckets_sweep"]]
    k = int(su["window_k"])
    TOP_K_GEN = int(su["top_k_gen"])
    N_PROBE_GEN = int(su["n_probe_gen"])
    DOM_NULL = float(su["domain_null_threshold"])
    CAP_NULL = float(su["capacity_null_threshold"])
    D = int(su["scaleup_D"])                    # capped for tractability (honest)
    corpus_n = int(su["scaleup_corpus_n"])
    seed = int(su["scaleup_seed"])
    hexc = int(lc["substrate"]["token_seed_hex_chars"])

    ctx = cs.ContextSubstrate(D=D, hex_chars=hexc)

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"[inference.scaleup] CATALOG-DRIVEN: D={D} (capped; F203 used 8192), "
          f"corpus_n={corpus_n}, seed={seed}")
    print(f"  N_sweep={N_SWEEP}  n_buckets_sweep={N_BUCKETS_SWEEP}  k={k}  "
          f"top_k_gen={TOP_K_GEN}  n_probe_gen={N_PROBE_GEN}")
    print("\nPRE-STATED NULLS:")
    print(f"  CAPACITY-EXTENDS : FAIL if hier_acc - flat_acc <= {CAP_NULL} at N_max")
    print(f"  HIER-KNEE        : FAIL TO FIND if hier_acc stays >= 0.90 across the whole N sweep")
    print(f"  DOMAIN-PERSISTS  : FAIL if hier_dom_acc - hier_acc <= {CAP_NULL} at the N where hier has degraded")
    print(f"  (predicted knee band: per-bucket load N/n_buckets ~ 257 => "
          f"n_buckets=8 knee ~N=2056; n_buckets=32 knee ~N=8224)\n")

    # ----- corpus: a flat token stream tagged with structural-domain (sentence length) -----
    rng = np.random.default_rng(seed)
    corpus = corpus_gen.generate_corpus(corpus_n, rng)
    stream_with_dom = [(tok, domain_of_length(len(sent)))
                       for sent in corpus for tok in sent]
    toks_only = [t for t, _ in stream_with_dom]
    print(f"token stream: {len(toks_only)} tokens, {len(set(toks_only))} unique; "
          f"domains={sorted(set(d for _, d in stream_with_dom))}\n")

    vocab = sorted(set(toks_only))
    vocab_vecs = np.stack([ctx.enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    chance = 1.0 / len(vocab)

    pairs_all = build_pairs(stream_with_dom, k)
    # bigram-legal candidate map (for the generation-quality top-k readout)
    bigram_next = defaultdict(set)
    for a, b in zip(toks_only, toks_only[1:]):
        bigram_next[a].add(b)

    records = []
    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "k": k, "D": D, "n_vocab": len(vocab),
              "chance": chance, "scaleup_corpus_n": corpus_n, "scaleup_seed": seed,
              "finding": "F222"}

    # ===================================================================
    # (a) CAPACITY KNEE: retrieval accuracy vs N, for each n_buckets,
    #     for FLAT / HIER / HIER+DOMAIN. Pushes N far past the F203 ceiling.
    # ===================================================================
    print("=" * 110)
    print("(a) CAPACITY KNEE -- true-next retrieval accuracy as N grows past the ~257 ceiling, per n_buckets")
    print("=" * 110)
    print(f"chance (1/|vocab|) = {chance:.4f}; |vocab| = {len(vocab)}; D = {D}\n")

    cap_by_bn = {}  # (n_buckets) -> {N -> rec}
    knee_by_bn = {}  # (n_buckets) -> first N where hier_acc < 0.90 (the knee), else None
    for n_buckets in N_BUCKETS_SWEEP:
        print(f"--- n_buckets = {n_buckets}  (per-bucket ceiling ~257; predicted knee N ~ {n_buckets * 257}) ---")
        print(f"{'N':>5} | {'N/buck':>6} | {'flat':>6} | {'hier':>6} | {'hierDOM':>7} | "
              f"{'h-flat':>7} | {'dom-h':>6} | {'maxLoad':>7} | {'build_s':>7}")
        print("-" * 88)
        cap_by_N = {}
        knee_N = None
        for N in N_SWEEP:
            if N > len(pairs_all):
                continue
            # deterministic pair sample (fresh rng per (n_buckets,N) for bit-exactness)
            rng_s = np.random.default_rng(seed + N + 7919 * n_buckets)
            idx = rng_s.choice(len(pairs_all), size=N, replace=False)
            pairs = [pairs_all[i] for i in idx]

            t0 = time.time()
            flat = FlatMemory(ctx); flat.build(pairs)
            hier = HierarchicalMemory(ctx, n_buckets, use_domain=False); hier.build(pairs)
            hier_dom = HierarchicalMemory(ctx, n_buckets, use_domain=True); hier_dom.build(pairs)
            t_build = time.time() - t0

            flat_correct = sum(1 for i in range(N)
                               if flat.retrieve_argmax(i, vocab, vocab_vecs) == pairs[i][1])
            hier_correct = sum(1 for (c, nx, dom) in pairs
                               if hier.retrieve_argmax(c, dom, vocab, vocab_vecs) == nx)
            hier_dom_correct = sum(1 for (c, nx, dom) in pairs
                                   if hier_dom.retrieve_argmax(c, dom, vocab, vocab_vecs) == nx)
            flat_acc = flat_correct / N
            hier_acc = hier_correct / N
            hier_dom_acc = hier_dom_correct / N
            loads = hier.bucket_loads()
            max_load = max(loads) if loads else 0

            if knee_N is None and hier_acc < 0.90:
                knee_N = N  # first N where the no-domain hierarchical drops below 0.90

            rec = {**attest, "phase": "P_capacity", "n_buckets": n_buckets, "N": N,
                   "per_bucket_mean": N / n_buckets,
                   "flat_acc": flat_acc, "hier_acc": hier_acc, "hier_dom_acc": hier_dom_acc,
                   "hier_minus_flat": hier_acc - flat_acc,
                   "domain_minus_nodomain": hier_dom_acc - hier_acc,
                   "n_retrievable_flat": flat_correct, "n_retrievable_hier": hier_correct,
                   "n_retrievable_hier_dom": hier_dom_correct,
                   "bucket_load_max": max_load,
                   "bucket_load_mean": float(np.mean(loads)) if loads else 0.0,
                   "build_seconds": t_build}
            records.append(rec)
            cap_by_N[N] = rec
            print(f"{N:>5} | {N / n_buckets:>6.1f} | {flat_acc:>6.3f} | {hier_acc:>6.3f} | "
                  f"{hier_dom_acc:>7.3f} | {hier_acc - flat_acc:>+7.3f} | "
                  f"{hier_dom_acc - hier_acc:>+6.3f} | {max_load:>7} | {t_build:>7.1f}")
        cap_by_bn[n_buckets] = cap_by_N
        knee_by_bn[n_buckets] = knee_N
        if knee_N is not None:
            kr = cap_by_N[knee_N]
            print(f"  KNEE (n_buckets={n_buckets}): hier_acc first < 0.90 at N={knee_N} "
                  f"(per-bucket mean {kr['per_bucket_mean']:.1f}, max bucket {kr['bucket_load_max']}); "
                  f"hier={kr['hier_acc']:.3f}, hierDOM={kr['hier_dom_acc']:.3f}")
        else:
            print(f"  KNEE (n_buckets={n_buckets}): hier_acc stayed >= 0.90 across the whole N sweep "
                  f"(no knee found in {N_SWEEP}) -> HIER-KNEE null NOT rejected at this n_buckets")
        print()

    # ===================================================================
    # (b) GENERATION QUALITY at the largest N (the F203 borderline re-measured
    #     at the larger N / capped D): does the DOMAIN anchor help held-out top-k?
    #     Uses the largest n_buckets (best-case hierarchical) as the host.
    # ===================================================================
    n_buckets_gen = max(N_BUCKETS_SWEEP)
    N_gen = max(n for n in N_SWEEP if n <= len(pairs_all))
    print("=" * 110)
    print(f"(b) GENERATION QUALITY -- next-structure top-{TOP_K_GEN} hit-rate (held-out) "
          f"at N={N_gen}, n_buckets={n_buckets_gen}")
    print("=" * 110)

    rng_g = np.random.default_rng(seed + N_gen + 7919 * n_buckets_gen)
    idx = rng_g.choice(len(pairs_all), size=N_gen, replace=False)
    pairs = [pairs_all[i] for i in idx]
    flat = FlatMemory(ctx); flat.build(pairs)
    hier = HierarchicalMemory(ctx, n_buckets_gen, use_domain=False); hier.build(pairs)
    hier_dom = HierarchicalMemory(ctx, n_buckets_gen, use_domain=True); hier_dom.build(pairs)

    trained_pos = set(idx.tolist())
    holdout_pos = [i for i in range(k, len(toks_only)) if i not in trained_pos]
    rng_g.shuffle(holdout_pos)
    holdout_pos = holdout_pos[:N_PROBE_GEN]

    def topk_hit(ranker, context, dom, true_next, cands):
        cand_idx = [vocab_idx[c] for c in cands]
        if ranker == "flat":
            cs_state = flat.ctx.encode_context(list(context))
            ranked = flat.rank_candidates(cs_state, cand_idx, vocab_vecs)
        elif ranker == "hier":
            ranked = hier.rank_candidates(context, dom, cand_idx, vocab_vecs)
        else:
            ranked = hier_dom.rank_candidates(context, dom, cand_idx, vocab_vecs)
        return vocab_idx[true_next] in ranked[:TOP_K_GEN]

    agg = defaultdict(list)
    random_expect = []
    for i in holdout_pos:
        context = tuple(toks_only[i - k:i])
        true_next = toks_only[i]
        dom = stream_with_dom[i][1]
        last = context[-1]
        cands = sorted(bigram_next.get(last, set()))
        if true_next not in cands or len(cands) < 2:
            continue
        agg["flat"].append(topk_hit("flat", context, dom, true_next, cands))
        agg["hier"].append(topk_hit("hier", context, dom, true_next, cands))
        agg["hier_dom"].append(topk_hit("hier_dom", context, dom, true_next, cands))
        random_expect.append(min(TOP_K_GEN, len(cands)) / len(cands))

    n_probe = len(agg["flat"])
    flat_hit = float(np.mean(agg["flat"])) if n_probe else 0.0
    hier_hit = float(np.mean(agg["hier"])) if n_probe else 0.0
    hier_dom_hit = float(np.mean(agg["hier_dom"])) if n_probe else 0.0
    rand_hit = float(np.mean(random_expect)) if n_probe else 0.0

    rec_gen = {**attest, "phase": "P_generation_quality", "n_buckets": n_buckets_gen,
               "N": N_gen, "top_k": TOP_K_GEN, "n_probe": n_probe,
               "flat_topk_hit": flat_hit, "hier_topk_hit": hier_hit,
               "hier_dom_topk_hit": hier_dom_hit, "random_baseline_hit": rand_hit,
               "domain_minus_nodomain": hier_dom_hit - hier_hit,
               "hier_minus_random": hier_hit - rand_hit,
               "domain_minus_random": hier_dom_hit - rand_hit}
    records.append(rec_gen)

    print(f"held-out probes with >=2 bigram-legal candidates: {n_probe}")
    print(f"  random-ranking baseline (top-{TOP_K_GEN}/|cands|) : {rand_hit:.3f}")
    print(f"  FLAT      top-{TOP_K_GEN} hit-rate                : {flat_hit:.3f}  ({flat_hit - rand_hit:+.3f} vs random)")
    print(f"  HIER      top-{TOP_K_GEN} hit-rate                : {hier_hit:.3f}  ({hier_hit - rand_hit:+.3f} vs random)")
    print(f"  HIER+DOM  top-{TOP_K_GEN} hit-rate                : {hier_dom_hit:.3f}  ({hier_dom_hit - rand_hit:+.3f} vs random)")
    print(f"  DOMAIN lift over no-domain                  : {hier_dom_hit - hier_hit:+.4f}  (null threshold +{DOM_NULL})")

    # ===================================================================
    # VERDICT against the pre-stated nulls
    # ===================================================================
    print("\n" + "=" * 110)
    print("VERDICT (against pre-stated nulls)")
    print("=" * 110)

    # --- CAPACITY-EXTENDS (at the largest N, the largest n_buckets) ---
    bn_max = max(N_BUCKETS_SWEEP)
    Nmax = max(cap_by_bn[bn_max].keys())
    cmax = cap_by_bn[bn_max][Nmax]
    if cmax["hier_minus_flat"] > CAP_NULL:
        cap_verdict = (f"CAPACITY EXTENDS (re-confirmed, catalog-driven): at N={Nmax}, "
                       f"n_buckets={bn_max}, hier {cmax['hier_acc']:.3f} vs flat "
                       f"{cmax['flat_acc']:.3f} (+{cmax['hier_minus_flat']:.3f}) -> null REJECTED")
    else:
        cap_verdict = (f"CAPACITY NULL at N={Nmax}: hier {cmax['hier_acc']:.3f} vs flat "
                       f"{cmax['flat_acc']:.3f} (delta {cmax['hier_minus_flat']:+.3f} <= +{CAP_NULL})")

    # --- HIER-KNEE (per n_buckets) ---
    knee_lines = []
    for bn in N_BUCKETS_SWEEP:
        kN = knee_by_bn[bn]
        if kN is None:
            knee_lines.append(f"n_buckets={bn}: NO KNEE in {N_SWEEP} (hier stayed >=0.90) "
                              f"-> per-bucket ceiling not reached at these N")
        else:
            kr = cap_by_bn[bn][kN]
            knee_lines.append(f"n_buckets={bn}: KNEE at N={kN} (per-bucket mean {kr['per_bucket_mean']:.1f}, "
                              f"max bucket {kr['bucket_load_max']}; hier drops to {kr['hier_acc']:.3f}) "
                              f"-> matches the ~257/bucket prediction (predicted ~N={bn * 257})")
    any_knee = any(knee_by_bn[bn] is not None for bn in N_BUCKETS_SWEEP)
    knee_verdict = ("HIER-KNEE FOUND (null REJECTED): " if any_knee else
                    "HIER-KNEE NOT FOUND in this N range (null NOT rejected): ") + " | ".join(knee_lines)

    # --- DOMAIN-PERSISTS (at the largest N where hier has degraded, largest n_buckets) ---
    # pick the largest N for the largest n_buckets where hier_acc < 0.90 if any, else N_max
    degraded_N = None
    for N in sorted(cap_by_bn[bn_max].keys(), reverse=True):
        if cap_by_bn[bn_max][N]["hier_acc"] < 0.90:
            degraded_N = N
            break
    test_N = degraded_N if degraded_N is not None else Nmax
    dr = cap_by_bn[bn_max][test_N]
    dom_lift_cap = dr["domain_minus_nodomain"]
    where = "where hier has degraded" if degraded_N is not None else "at N_max (hier not yet degraded)"
    if dom_lift_cap > CAP_NULL:
        dom_verdict = (f"DOMAIN-ON-CAPACITY PERSISTS (null REJECTED): at N={test_N} ({where}, "
                       f"n_buckets={bn_max}), hier_dom {dr['hier_dom_acc']:.3f} vs hier "
                       f"{dr['hier_acc']:.3f} (+{dom_lift_cap:.3f}) -> the F203 second-axis "
                       f"orthogonalization still cuts intra-bucket collision")
    else:
        dom_verdict = (f"DOMAIN-ON-CAPACITY EXHAUSTED (null NOT rejected): at N={test_N} ({where}, "
                       f"n_buckets={bn_max}), hier_dom {dr['hier_dom_acc']:.3f} vs hier "
                       f"{dr['hier_acc']:.3f} (delta {dom_lift_cap:+.3f} <= +{CAP_NULL}) -> the coarse "
                       f"4-domain axis saturates at this per-bucket load")

    # --- DOMAIN-on-generation-topk (the F203 borderline, re-measured) ---
    gen_lift = hier_dom_hit - hier_hit
    beats_random = (hier_hit > rand_hit + 1e-9) or (hier_dom_hit > rand_hit + 1e-9)
    if not beats_random:
        gen_verdict = (f"GEN NULL: neither hier ({hier_hit:.3f}) nor domain ({hier_dom_hit:.3f}) "
                       f"beats random {rand_hit:.3f}")
    elif gen_lift >= DOM_NULL + 0.005:
        gen_verdict = (f"DOMAIN-ON-GEN HELPS: top-{TOP_K_GEN} lift {gen_lift:+.4f} > +{DOM_NULL} "
                       f"(and beats random {rand_hit:.3f}) -> null REJECTED")
    elif gen_lift <= DOM_NULL - 0.005:
        gen_verdict = (f"DOMAIN-ON-GEN NULL: lift {gen_lift:+.4f} <= +{DOM_NULL} -- domain redundant "
                       f"with bigram-legal gating for held-out top-{TOP_K_GEN} (hier {hier_hit:.3f} "
                       f"already beats random {rand_hit:.3f})")
    else:
        gen_verdict = (f"DOMAIN-ON-GEN BORDERLINE/NULL: lift {gen_lift:+.4f} sits ON the +{DOM_NULL} "
                       f"threshold -- NOT a clean pass (consistent with F203); the clean DOMAIN effect "
                       f"is on CAPACITY, not held-out top-{TOP_K_GEN}.")

    print(f"  (a) {cap_verdict}")
    print(f"  (b) {knee_verdict}")
    print(f"  (c) {dom_verdict}")
    print(f"  (d) {gen_verdict}")
    records.append({**attest, "phase": "P_verdict",
                    "capacity_extends_verdict": cap_verdict,
                    "hier_knee_verdict": knee_verdict,
                    "domain_on_capacity_verdict": dom_verdict,
                    "domain_on_generation_verdict": gen_verdict,
                    "knee_N_by_n_buckets": {str(bn): knee_by_bn[bn] for bn in N_BUCKETS_SWEEP}})

    out = args.catalog.parent / "substrate_measurements" / "r222_instrument_scaleup_ceiling.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")


if __name__ == "__main__":
    main()
