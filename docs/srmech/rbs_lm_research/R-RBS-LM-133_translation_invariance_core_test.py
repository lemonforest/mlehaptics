"""R-RBS-LM-133 — F171: the CORE invariance test (F169's named next step).

F169 established storage and expression are SEPARABLE axes, but could not test
INVARIANCE (its 6 texts were different CONTENT). This test uses the same content
rendered by TWO translators — the Quran in the Yusuf-Ali/Sale register (cached)
vs Rodwell 1861 (PG #3434, attested) — and asks:

  Is the confound-controlled STORAGE depth INVARIANT across translations of the
  same content, while SURFACE repetition is free to vary?

Method (no verse-alignment needed): profile each translation's confound-controlled
two-axis signature (matched budget + vocab, per R-RBS-LM-132), then contrast:
  - WITHIN-PAIR (Quran Yusuf vs Rodwell — SAME content): depth-diff, rep-diff
  - ACROSS-CONTENT (the distinct-content texts — different content): depth-diff spread
If within-pair depth-diff ≪ across-content depth-diff (storage ≈ invariant across
expression) AND within-pair rep-diff is non-trivial (expression varies), that is
the "same storage, different expression" signature on identical content.

n=1 same-content pair — a first datapoint, NOT a general law (more pairs = the
robustness follow-up). Null counts (storage-depth differing across translations
would refute invariance).

SCOPE: STRUCTURAL test on TEXT OBJECTS only; NOT a clinical claim about real
NT/ND cognition (§VII.6.20 + [[feedback_trauma_informed_defensive_scope]]). The
NT/ND reading is the user's motivating conjecture, engaged as form.

srmech 0.5.0 native ABI=3; reuses R-RBS-LM-132/131 machinery.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location(
    "r132", HERE / "R-RBS-LM-132_storage_vs_expression_two_axis.py")
r132 = importlib.util.module_from_spec(_spec)
sys.modules["r132"] = r132
_spec.loader.exec_module(r132)

r131 = r132.r131
k1mod = r132.k1mod
from srmech.amsc import load_descriptor, descriptor_hash
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    cc = lc["confound_control"]
    budget = int(cc["budget_tokens"])
    V_cfg = int(cc["shared_vocab"])
    max_order = int(cc["max_order"])
    seed = int(cc["seed"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print("STRUCTURAL test on TEXT OBJECTS only; NOT a clinical claim (§VII.6.20).\n")

    # the SAME-CONTENT pair (two Quran translations) + distinct-content reference set
    pair = {
        "quran_yusuf": ("quran_yusuf_ali.txt", "quran"),
        "quran_rodwell": ("quran_rodwell.txt", "quran"),
    }
    distinct = {  # one representative per distinct content (quran_yusuf stands in for Quran)
        "quran_yusuf": "quran_yusuf_ali.txt",
        "kjv_ot": "kjv_old_testament.txt",
        "kjv_nt": "kjv_new_testament.txt",
        "bhagavad_gita": "bhagavad_gita.txt",
        "tao_legge": "tao_te_ching.txt",
        "dhammapada": "dhammapada.txt",
    }
    all_files = {**{k: v[0] for k, v in pair.items()}, **distinct}

    streams = {}
    for key, fn in all_files.items():
        body = k1mod.strip_gutenberg((cache_dir / fn).read_text(encoding="utf-8", errors="replace"))
        streams[key] = k1mod.tokenize(body)

    budget = min(budget, min(len(s) for s in streams.values()))
    samples = {k: s[:budget] for k, s in streams.items()}
    V = min(V_cfg, min(len(set(s)) for s in samples.values()))
    print(f"MATCHED budget = {budget} tokens/corpus;  MATCHED vocab V = {V} types\n")

    def resolution_profile(ba):
        """Normalized marginal-lift distribution over orders = the storage-depth
        profile SHAPE (continuous; finer than the integer depth)."""
        lifts = [ba[1]] + [max(ba[k] - ba[k - 1], 0.0) for k in range(2, max_order + 1)]
        s = sum(lifts)
        return [x / s for x in lifts] if s > 0 else [1.0 / max_order] * max_order

    def tv(p, q):  # total-variation distance between two profile shapes
        return 0.5 * sum(abs(a - b) for a, b in zip(p, q))

    # two-axis profile (controlled) for each
    prof = {}
    for key, sample in samples.items():
        capped, _ = r132.cap_vocab(sample, V)
        ba, _ = r132.profile_matched(capped, max_order, 4000, np.random.default_rng(seed))
        depth = r131.resolution_depth(ba, max_order)
        rep = r132.surface_repetition(sample)
        prof[key] = {"storage_depth": depth, "surface_repetition": rep,
                     "top_K_acc": ba[max_order], "profile_shape": resolution_profile(ba)}

    print(f"{'corpus':>16} | {'role':>14} | {'storage_depth':>13} | {'surface_rep':>11}")
    print("-" * 64)
    for key in ("quran_yusuf", "quran_rodwell", "kjv_ot", "kjv_nt",
                "bhagavad_gita", "tao_legge", "dhammapada"):
        role = "PAIR (same content)" if key in ("quran_yusuf", "quran_rodwell") else "distinct"
        print(f"{key:>16} | {role:>14} | {prof[key]['storage_depth']:>13} | "
              f"{prof[key]['surface_repetition']:>11.3f}")

    # WITHIN-PAIR (same content, different translator)
    dd_within = abs(prof["quran_yusuf"]["storage_depth"] - prof["quran_rodwell"]["storage_depth"])
    rd_within = abs(prof["quran_yusuf"]["surface_repetition"] - prof["quran_rodwell"]["surface_repetition"])

    # ACROSS-CONTENT (distinct contents, pairwise)
    dkeys = list(distinct.keys())
    dd_across = [abs(prof[a]["storage_depth"] - prof[b]["storage_depth"])
                 for a, b in itertools.combinations(dkeys, 2)]
    rd_across = [abs(prof[a]["surface_repetition"] - prof[b]["surface_repetition"])
                 for a, b in itertools.combinations(dkeys, 2)]
    dd_across_mean = float(np.mean(dd_across))
    rd_across_mean = float(np.mean(rd_across))

    # CONTINUOUS storage metric: profile-SHAPE total-variation distance (the proper
    # invariance metric — integer depth is too coarse, everything ~1 level apart)
    sd_within = tv(prof["quran_yusuf"]["profile_shape"], prof["quran_rodwell"]["profile_shape"])
    sd_across = [tv(prof[a]["profile_shape"], prof[b]["profile_shape"])
                 for a, b in itertools.combinations(dkeys, 2)]
    sd_across_mean = float(np.mean(sd_across))

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "budget_tokens": budget, "shared_vocab": V,
              "scope": "STRUCTURAL translation-invariance; text objects; §VII.6.20; no clinical claims"}
    records = [{**attest, "phase": "P1_profile", "corpus": k, **prof[k]} for k in prof]
    records.append({**attest, "phase": "P2_invariance",
                    "pair_id": "quran", "within_pair_depth_diff": dd_within,
                    "within_pair_rep_diff": rd_within,
                    "across_content_depth_diff_mean": dd_across_mean,
                    "across_content_rep_diff_mean": rd_across_mean,
                    "across_content_depth_diffs": dd_across,
                    "within_pair_shape_tv": sd_within,
                    "across_content_shape_tv_mean": sd_across_mean,
                    "across_content_shape_tvs": sd_across})

    out = args.catalog.parent / "substrate_measurements" / "translation_invariance_core.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")

    print("\n" + "=" * 64)
    print("F171 CORE TEST — storage-depth invariance across translations?")
    print("=" * 64)
    print(f"  WITHIN-PAIR (Quran Yusuf vs Rodwell, SAME content):")
    print(f"    storage-depth diff = {dd_within}    surface-rep diff = {rd_within:.3f}")
    print(f"  ACROSS-CONTENT (distinct texts, mean of {len(dd_across)} pairs):")
    print(f"    storage-depth diff = {dd_across_mean:.2f}   surface-rep diff = {rd_across_mean:.3f}")
    print(f"\n  [coarse integer-depth metric — too coarse for invariance, ~1 level throughout]")
    print(f"    within-pair depth diff {dd_within} vs across-content {dd_across_mean:.2f}"
          f"  → invariance {'supported' if dd_within < dd_across_mean else 'NOT supported'} (resolution-limited)")
    print(f"\n  [CONTINUOUS profile-shape metric — the proper invariance test]")
    print(f"    WITHIN-PAIR shape distance (TV)      = {sd_within:.4f}")
    print(f"    ACROSS-CONTENT shape distance (mean) = {sd_across_mean:.4f}  "
          f"(range {min(sd_across):.4f}..{max(sd_across):.4f})")
    shape_invariant = sd_within < sd_across_mean
    expresses = rd_within > 0.02
    ratio = sd_across_mean / sd_within if sd_within > 1e-9 else float("inf")
    print(f"\n  storage-profile SHAPE closer within-translation than across-content? "
          f"{shape_invariant} (across/within = {ratio:.2f}×)")
    print(f"  surface expression VARIES within the pair (rep-diff > 0.02)?         {expresses}")
    if shape_invariant and expresses:
        print("  → storage SHAPE more invariant across translation than across content,")
        print("    while expression varies ⇒ supports SAME-storage/DIFFERENT-expression (n=1 pair).")
    elif not shape_invariant:
        print("  → storage shape differs across translation as much as across content ⇒")
        print("    invariance NOT supported even on the continuous metric (null).")
    print("\n  n=1 same-content pair: a first datapoint, not a general law. More pairs"
          "\n  (Tao, Bible, Gita) = the robustness follow-up.")


if __name__ == "__main__":
    main()
