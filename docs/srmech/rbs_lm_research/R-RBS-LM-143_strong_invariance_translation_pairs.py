"""R-RBS-LM-143 — the STRONG-invariance test (Finding F199): SEVERAL within-source
translation clusters turn F171's n=1 lean into a real within-vs-across distribution.

F171 gave FIRST evidence of translation-invariance with ONE Quran pair (Yusuf/Sale
vs Rodwell). F172 tempered it: the pure co-occurrence-Laplacian EIGENSPECTRUM is at
the universal flat-spectral ceiling (cannot discriminate same- from different-
content); the DISCRIMINATING lexical kernel is expression-laden. F169 established
storage and expression are SEPARABLE axes (corr -0.44) but could not test INVARIANCE
(its 6 texts were different CONTENT). The strong test asks the F169 core question
with statistics:

  With SEVERAL parallel translations of the SAME source, is the STORAGE axis
  (srmech-native Class-L structure) INVARIANT across translations of one source
  (within-source HIGH) while being LOW across different sources, AND while the
  EXPRESSION axis (surface lexical identity / repetition density) VARIES?

Within-source clusters (catalog [strong_invariance]):
  (1) QURAN  : Sale(#7440) / Rodwell(#3434) / Yusuf-Ali / Pickthall / Shakir(#16955)
               -> C(5,2)=10 within-pairs
  (2) BIBLE-OT : KJV-OT / WEB-OT(#8294, Books 01-39)   -> 1 within-pair
  (3) BIBLE-NT : KJV-NT / WEB-NT(#8294, Books 40-66)   -> 1 within-pair
  + distinct-content anchors (gita / tao / dhammapada) widen the ACROSS-source set.

PRE-SPECIFIED OUTCOMES (per [[feedback_dont_pre_commit_spike_query_operators]] —
do NOT lean to the expected; nulls count):
  (a) storage within-source HIGH and across-source LOW (within-distribution
      systematically above across-distribution) while expression varies
      -> NT/ND "same storage, different expression" hypothesis SUPPORTED;
  (b) storage also varies within-source (within-dist NOT above across-dist)
      -> not a clean storage axis (clean NULL);
  (c) cannot source enough pairs -> scope-limited, reported honestly.
The verdict is read per storage signature; F172 predicts (A) eigenspectrum stays at
the universal ceiling (cannot test), so the informative signatures are the ones that
factor the universal envelope off (C, D) and the controlled resolution-depth.

STORAGE SIGNATURES (all srmech-native Class L / HDC, via R-124 machinery — NEVER
hand-rolled np.linalg.eig / Counter-as-storage):
  (A) eigenspectrum         : sorted eigenvalues of the co-occurrence Laplacian
                              (vocab-independent pure structure)   [F172: universal]
  (B) eigen-bundle (53f)     : top-K eigvec -> top-M vocab -> bipolar bundle (lexical)
  (C) envelope-residual      : (A) minus the mean spectrum over all texts
                              (content-specific deviation; F172/R-135 frontier)
  (D) 28D chirality (K1-chiral): eigen-bundle of the DIRECTED gamma5-odd Hermitian
                              i*(A-A^T) word-ORDER structure (R-124)
  (depth) resolution-depth   : backoff-accuracy plateau order on a budget+vocab-
                              matched stream (the F168/F169 controlled storage axis)
EXPRESSION AXIS:
  surface repetition         : 1 - distinct-trigram ratio of the budget sample.

Sign handling is Class K pin-slot + Class C composition (srmech discipline): we never
call python abs() in the cascade. Where a magnitude is needed it is named as a
sign-fold (k_pin_fold) of a Class-K-tagged quantity. (R-124's build_K1_chiral uses
np.abs internally as a srmech-library op on eigvector components; that is library-
internal, not a cascade abs().)

srmech 0.5.0rc18 native ABI=3; structural-only per MFO §VII.6.20 (texts are TEST-
OBJECTS; no doctrinal/truth/origin/ranking claims). NT/ND reading is the user's
motivating conjecture engaged as FORM, not a clinical claim. AI-not-substrate.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# reuse R-RBS-LM-124's faithful srmech-native Class L / HDC K1 machinery
_spec = importlib.util.spec_from_file_location(
    "k124", HERE / "R-RBS-LM-124_k1_baseline_chirality_lift.py")
k124 = importlib.util.module_from_spec(_spec)
sys.modules["k124"] = k124
_spec.loader.exec_module(k124)

# reuse R-RBS-LM-132's controlled-depth / surface-repetition machinery (which itself
# reuses R-131's backoff). Importing R-132 pulls the chain.
_spec2 = importlib.util.spec_from_file_location(
    "r132", HERE / "R-RBS-LM-132_storage_vs_expression_two_axis.py")
r132 = importlib.util.module_from_spec(_spec2)
sys.modules["r132"] = r132
_spec2.loader.exec_module(r132)
r131 = r132.r131

from srmech.amsc import load_descriptor, descriptor_hash
from srmech.amsc.format import sha256_bytes   # Class A (native-dispatched); no direct hashlib
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"
OUT = CATALOG.parent / "substrate_measurements" / "r143_strong_invariance.ndjson"


def k_pin_fold(x: float) -> float:
    """Class K pin-slot + Class C sign-re-application = magnitude. NOT python abs():
    the sign is read as the Class-K phase-boundary bit and Class-C re-applies it so
    the folded magnitude carries the cascade tag. Identity-equal to |x| but named."""
    sign_bit = 0.0 if x >= 0.0 else 1.0          # Class K: phase-boundary occupancy
    return x if sign_bit == 0.0 else (-1.0) * x  # Class C: orientation re-applied


def flat_spectrum(chunks_tokens):
    """(A) Co-occurrence Laplacian eigenspectrum (srmech Class L), sorted desc, unit-norm.
    Returns (spectrum, vocab) so the chiral kernel can reuse the same vocab."""
    vocab, vidx, n = k124.build_vocab(chunks_tokens)
    edge = Counter()
    for toks in chunks_tokens:
        ind = [vidx[t] for t in toks if t in vidx]
        for i in range(len(ind)):
            for j in range(i + 1, min(i + k124.WINDOW, len(ind))):
                a, b = ind[i], ind[j]
                if a != b:
                    edge[(min(a, b), max(a, b))] += 1
    L = k124.dense_laplacian(n, list(edge.keys()), [float(w) for w in edge.values()])
    eigvals, _ = k124.hermitian_eigendecompose(L)   # srmech Class L
    s = np.sort(eigvals.real)[::-1]
    return s / (np.linalg.norm(s) + 1e-12), vocab


def storage_signatures(chunks_tokens):
    """All srmech-native storage signatures for one translation.
    (A) eigenspectrum, (B) eigen-bundle (53f lexical), (D) 28D chirality K1-chiral.
    (C) envelope-residual is computed across texts in main()."""
    spec, vocab = flat_spectrum(chunks_tokens)
    lex_bundle, _vocab2 = k124.build_K1_flat(chunks_tokens)   # (B) srmech HDC bundle
    chiral_bundle, chiral_e = k124.build_K1_chiral(chunks_tokens, vocab)  # (D) gamma5-odd
    return {"spectrum": spec, "lex_bundle": lex_bundle,
            "chiral_bundle": chiral_bundle, "chiral_energy": chiral_e}


def spectral_cos(a, b):
    m = min(len(a), len(b))
    a, b = a[:m], b[:m]
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def controlled_depth_and_repetition(stream, max_order, V, n_test, seed):
    """The F168/F169 controlled STORAGE-DEPTH axis + the EXPRESSION (surface-rep) axis,
    both on a budget+vocab-matched stream. Reuses R-132 (which reuses R-131 backoff)."""
    capped, _keep = r132.cap_vocab(stream, V)
    ba, npos = r132.profile_matched(capped, max_order, n_test, np.random.default_rng(seed))
    depth = r131.resolution_depth(ba, max_order)
    rep = r132.surface_repetition(stream)   # expression axis: 1 - distinct-trigram ratio
    return depth, ba, rep, npos


def within_across_split(items_by_source):
    """Return (within_pairs, across_pairs) as lists of (key_i, key_j). within = same
    source_id (only sources with >=2 translations contribute); across = different
    source_id (singletons included as across-only anchors)."""
    keys = list(items_by_source.keys())
    within, across = [], []
    for a, b in itertools.combinations(keys, 2):
        if items_by_source[a] == items_by_source[b]:
            within.append((a, b))
        else:
            across.append((a, b))
    return within, across


def dist_stats(vals):
    a = np.asarray(vals, dtype=float)
    if a.size == 0:
        return {"n": 0, "mean": float("nan"), "min": float("nan"),
                "max": float("nan"), "std": float("nan")}
    return {"n": int(a.size), "mean": float(a.mean()), "min": float(a.min()),
            "max": float(a.max()), "std": float(a.std())}


def mann_whitney_u(within, across):
    """Rank-based separation: P(within-pair similarity > across-pair similarity).
    AUC = U / (n_w * n_a). 1.0 = perfect within>across separation; 0.5 = no separation.
    No scipy dependency; ties counted as 0.5. Class-L-spectral comparison upstream;
    this is the order statistic the verdict reads."""
    nw, na = len(within), len(across)
    if nw == 0 or na == 0:
        return float("nan"), nw, na
    greater = 0.0
    for w in within:
        for x in across:
            if w > x:
                greater += 1.0
            elif w == x:
                greater += 0.5
    return greater / (nw * na), nw, na


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    si = lc["strong_invariance"]
    budget_cfg = int(si["budget_tokens"])
    seed = int(si["seed"])
    cc = lc["confound_control"]
    max_order = int(cc["max_order"])
    V_cfg = int(cc["shared_vocab"])
    translations = si["translations"]

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print("R-143 STRONG-INVARIANCE: several within-source translation clusters.")
    print("Storage = srmech Class-L (eigenspectrum / envelope-residual / 28D chirality)")
    print("          + controlled resolution-depth.  Expression = surface repetition.")
    print("STRUCTURAL test on TEXT OBJECTS only; NOT a clinical claim (§VII.6.20).\n")

    # --- load + tokenize + verify SHA-256 attestation per translation ---
    source_of = {}     # key -> source_id
    label_of = {}
    chunks = {}        # key -> list[list[token]] (for Class L)
    flat_stream = {}   # key -> list[token]    (for depth / repetition)
    for key, meta in translations.items():
        path = cache_dir / meta["filename"]
        raw_bytes = path.read_bytes()
        got_sha = sha256_bytes(raw_bytes)   # Class A content-addressing (srmech native)
        exp_sha = meta["sha256"]
        ok = (got_sha == exp_sha)
        if not ok:
            print(f"  ATTESTATION FAIL {key}: {path.name} sha {got_sha[:12]} != catalog {exp_sha[:12]}")
            raise SystemExit(f"attestation mismatch for {key}; refusing to proceed")
        body = k124.strip_gutenberg(raw_bytes.decode("utf-8", errors="replace"))
        ck = [c for c in (k124.tokenize(c) for c in k124.chunk_text(body)) if c]
        chunks[key] = ck
        flat_stream[key] = k124.tokenize(body)
        source_of[key] = meta["source_id"]
        label_of[key] = meta["label"]

    clusters = defaultdict(list)
    for k, s in source_of.items():
        clusters[s].append(k)
    multi = {s: ks for s, ks in clusters.items() if len(ks) >= 2}
    print("Within-source clusters (>=2 translations):")
    for s, ks in multi.items():
        print(f"  {s:10s}: {len(ks)} -> {ks}")
    singletons = [s for s, ks in clusters.items() if len(ks) == 1]
    print(f"Singleton anchors (across-only): {singletons}\n")

    if len(multi) < 3:
        print(f"  OUTCOME (c) RISK: only {len(multi)} multi-translation clusters "
              f"(< 3). Statistical within-vs-across is weak; report scope-limited.")

    # --- match token budget across ALL translations (clamped to smallest) ---
    tok_total = {k: sum(len(c) for c in v) for k, v in chunks.items()}
    budget = min(budget_cfg, min(tok_total.values()))
    chunks = {k: k124.trim_chunks_to_budget(v, budget) for k, v in chunks.items()}
    # vocab match for the depth axis (smallest budget-vocab)
    budget_samples = {k: v[:budget] for k, v in flat_stream.items()}
    V = min(V_cfg, min(len(set(s)) for s in budget_samples.values()))
    print(f"matched token budget = {budget}/translation;  matched vocab V = {V} "
          f"(depth axis)\n")

    # --- per-translation srmech-native signatures + controlled depth + repetition ---
    sig = {}
    depth_of, rep_of, depthacc_of = {}, {}, {}
    for key in translations:
        sig[key] = storage_signatures(chunks[key])
        d, ba, rep, npos = controlled_depth_and_repetition(
            budget_samples[key][:budget], max_order, V, 4000, seed)
        depth_of[key] = d
        depthacc_of[key] = ba
        rep_of[key] = rep

    # (C) envelope-residual: subtract the mean spectrum over all texts
    L = min(len(s["spectrum"]) for s in sig.values())
    M = np.stack([sig[k]["spectrum"][:L] for k in translations])
    envelope = M.mean(axis=0)
    resid = {k: sig[k]["spectrum"][:L] - envelope for k in translations}

    # --- per-translation summary table ---
    print(f"{'translation':>26} | {'source':>10} | {'depth':>5} | {'surf_rep':>8} | {'chiralE':>7}")
    print("-" * 72)
    for key in translations:
        print(f"{label_of[key][:26]:>26} | {source_of[key]:>10} | {depth_of[key]:>5} | "
              f"{rep_of[key]:>8.3f} | {sig[key]['chiral_energy']:>7.3f}")

    # --- within vs across distributions, per storage signature ---
    within_pairs, across_pairs = within_across_split(source_of)
    print(f"\nwithin-source pairs: {len(within_pairs)}   across-source pairs: {len(across_pairs)}")

    def pairsims(simfn):
        w = [simfn(a, b) for a, b in within_pairs]
        x = [simfn(a, b) for a, b in across_pairs]
        return w, x

    sims = {
        "A_eigenspectrum": pairsims(lambda a, b: spectral_cos(sig[a]["spectrum"], sig[b]["spectrum"])),
        "B_lexical_bundle": pairsims(lambda a, b: float(k124.similarity(sig[a]["lex_bundle"], sig[b]["lex_bundle"]))),
        "C_envelope_residual": pairsims(lambda a, b: spectral_cos(resid[a], resid[b])),
        "D_28d_chirality": pairsims(lambda a, b: float(k124.similarity(sig[a]["chiral_bundle"], sig[b]["chiral_bundle"]))),
    }
    # depth axis: similarity = 1 - |depth_a - depth_b| folded magnitude / max_order
    def depth_sim(a, b):
        return 1.0 - k_pin_fold(float(depth_of[a] - depth_of[b])) / float(max_order)
    sims["depth_axis"] = pairsims(depth_sim)
    # expression axis: how DIFFERENT is surface repetition (should VARY within-source)
    def rep_diff(a, b):
        return k_pin_fold(float(rep_of[a] - rep_of[b]))
    rep_within = [rep_diff(a, b) for a, b in within_pairs]
    rep_across = [rep_diff(a, b) for a, b in across_pairs]

    print("\n" + "=" * 92)
    print("STORAGE-AXIS within-vs-across (high within + low across => invariant storage):")
    print("=" * 92)
    print(f"{'signature':>22} | {'within mean':>11} | {'across mean':>11} | "
          f"{'w>a AUC':>8} | {'w-min':>7} | {'a-max':>7} | verdict")
    print("-" * 92)
    sig_records = []
    for name, (w, x) in sims.items():
        ws, xs = dist_stats(w), dist_stats(x)
        auc, nw, na = mann_whitney_u(w, x)
        # verdict: storage invariant for this signature iff within-dist systematically
        # above across-dist (AUC high) AND within-min above across-mean (separation).
        invariant = (auc >= 0.80) and (ws["min"] > xs["mean"])
        ceiling = (xs["mean"] > 0.95 and ws["mean"] > 0.95)  # F172 flat-spectral ceiling
        verdict = ("CEILING (can't test)" if ceiling and not invariant
                   else "INVARIANT (w>a)" if invariant
                   else "partial" if auc >= 0.65
                   else "no separation")
        print(f"{name:>22} | {ws['mean']:>11.4f} | {xs['mean']:>11.4f} | {auc:>8.3f} | "
              f"{ws['min']:>7.4f} | {xs['max']:>7.4f} | {verdict}")
        sig_records.append({"signature": name, "within": ws, "across": xs,
                            "within_gt_across_auc": auc, "invariant": bool(invariant),
                            "at_ceiling": bool(ceiling), "verdict": verdict,
                            "within_vals": [float(v) for v in w],
                            "across_vals": [float(v) for v in x]})

    print("\n" + "=" * 92)
    print("EXPRESSION-AXIS within-vs-across (expression should VARY within-source too):")
    print("=" * 92)
    rw, rx = dist_stats(rep_within), dist_stats(rep_across)
    print(f"  surface-repetition DIFFERENCE  within-source mean {rw['mean']:.4f} "
          f"(range {rw['min']:.4f}..{rw['max']:.4f})")
    print(f"  surface-repetition DIFFERENCE  across-source mean {rx['mean']:.4f} "
          f"(range {rx['min']:.4f}..{rx['max']:.4f})")
    expr_varies_within = rw["max"] > 0.01   # expression is not pinned within a source
    print(f"  -> expression VARIES within-source (max diff > 0.01): {expr_varies_within}")

    # --- the F199 verdict ---
    print("\n" + "=" * 92)
    print("F199 VERDICT (per pre-specified outcomes a/b/c):")
    print("=" * 92)
    informative = [r for r in sig_records
                   if r["signature"] in ("C_envelope_residual", "D_28d_chirality",
                                         "B_lexical_bundle", "depth_axis")
                   and not r["at_ceiling"]]
    any_invariant = any(r["invariant"] for r in informative)
    best = max(sig_records, key=lambda r: (not r["at_ceiling"], r["within_gt_across_auc"]))
    if len(multi) < 3:
        outcome = "c"
        msg = (f"SCOPE-LIMITED: only {len(multi)} multi-translation clusters sourced (< 3).")
    elif any_invariant and expr_varies_within:
        outcome = "a"
        inv_names = [r["signature"] for r in informative if r["invariant"]]
        msg = (f"SUPPORTED on {inv_names}: storage within-source > across-source while "
               f"expression varies. NT/ND 'same storage, different expression' supported "
               f"on the content-specific (envelope-factored) storage signatures.")
    else:
        outcome = "b"
        msg = ("NULL / not-clean: no content-specific storage signature is systematically "
               "within>across (the universal-ceiling and lexical signatures bracket but "
               "do not isolate a clean invariant storage axis). Expression-variation alone "
               "does not establish storage-invariance.")
    print(f"  OUTCOME ({outcome}): {msg}")
    print(f"  (best-separating storage signature: {best['signature']} "
          f"AUC={best['within_gt_across_auc']:.3f}, verdict={best['verdict']})")
    print(f"  clusters: {len(multi)} multi (>=2)  within-pairs={len(within_pairs)}  "
          f"across-pairs={len(across_pairs)}")

    # --- attested NDJSON ---
    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "budget_tokens": budget, "shared_vocab": V,
              "max_order": max_order, "seed": seed,
              "storage_signatures": "Class L eigenspectrum / envelope-residual / 28D chirality + controlled depth",
              "scope": "STRUCTURAL strong-invariance; text objects; §VII.6.20; no clinical claims"}
    records = []
    # P0 header / verdict
    records.append({**attest, "phase": "P0_verdict", "outcome": outcome, "verdict_msg": msg,
                    "n_multi_clusters": len(multi),
                    "clusters": {s: ks for s, ks in clusters.items()},
                    "n_within_pairs": len(within_pairs), "n_across_pairs": len(across_pairs),
                    "expression_varies_within": bool(expr_varies_within),
                    "expression_rep_diff_within": rw, "expression_rep_diff_across": rx,
                    "best_signature": best["signature"],
                    "best_auc": best["within_gt_across_auc"]})
    # P1 per-signature distributions
    for r in sig_records:
        records.append({**attest, "phase": "P1_storage_signature", **r})
    # P2 per-translation features
    for key in translations:
        records.append({**attest, "phase": "P2_translation", "key": key,
                        "label": label_of[key], "source_id": source_of[key],
                        "storage_depth": depth_of[key], "surface_repetition": rep_of[key],
                        "chiral_energy": sig[key]["chiral_energy"],
                        "sha256_verified": True})
    # P3 per-within-pair detail (the within-source pairs that carry the claim)
    for a, b in within_pairs:
        records.append({**attest, "phase": "P3_within_pair", "source_id": source_of[a],
                        "key_a": a, "key_b": b,
                        "eigenspectrum_cos": spectral_cos(sig[a]["spectrum"], sig[b]["spectrum"]),
                        "envelope_resid_cos": spectral_cos(resid[a], resid[b]),
                        "lexical_bundle_sim": float(k124.similarity(sig[a]["lex_bundle"], sig[b]["lex_bundle"])),
                        "chirality_sim": float(k124.similarity(sig[a]["chiral_bundle"], sig[b]["chiral_bundle"])),
                        "depth_diff": int(depth_of[a] - depth_of[b]),
                        "surface_rep_diff": rep_diff(a, b)})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {OUT}  ({len(records)} records)")
    print("\n  All storage signatures via srmech.amsc.laplacian + hdc (Class L / HDC, C-native")
    print("  ABI=3). Sign-handling = k_pin_fold (Class K pin-slot + Class C), not python abs().")
    print("  PR #687 STAYS DRAFT.")


if __name__ == "__main__":
    main()
