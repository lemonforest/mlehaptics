"""
Spike #45 Round 1 — Cascade-composition signature analysis across substrates.

Apply Spike #44 R2 lens uniformly to cosmic + human + biological (from R2)
substrates. Pipeline:

  Class L: kinship-graph eigenstructure (Fiedler partition)
  Class E: catalog asymmetry (what's shared vs not)
  Class K: asymptotic-DOF (ε rate-parameter of kinship-decay)
  Class C: streaming-cascade direction (transmission mode)
  Class I: cyclic generational (period-like recurrence)

The cascade chain c_k = ε^k × K_k(substrate) per [[user_stance_kepler_shape_universal]]
is tested by collecting ε across substrates and checking whether the K_k binding
is substrate-specific (chemistry vs alleles vs citations vs ...) while ε^k tower
is invariant in form.
"""

import json
import math
from pathlib import Path

OUT_DIR = Path(__file__).parent
RECORDS_PATH = OUT_DIR / "signature_records.ndjson"

# Pull together biological fingerprints from Spike #44 R2 directly (encoded inline
# from the working note table to avoid cross-script dependency).
biological_fingerprints = [
    {"substrate": "bonobo", "domain": "biological_kinship",
     "f1_InterLethal": 0.0, "f2_IntraLethal": 0.0, "f4_MatriAnalog": 1,
     "f6_Coalition": 1, "f9_SubstrateSharing_chem": 1, "f10_Tool": 0,
     "f11_Allo": 1, "f12_MultiGen": 0, "f13_PostRep": 0,
     "f14_KinshipCode": 3, "f15_EpsDecay": None, "kinship_decisive": False,
     "kinship_outlier": True},
    {"substrate": "chimpanzee_control", "domain": "biological_kinship",
     "f1_InterLethal": 0.0, "f2_IntraLethal": 0.0, "f4_MatriAnalog": 0,
     "f6_Coalition": 0, "f9_SubstrateSharing_chem": 0, "f10_Tool": 1,
     "f11_Allo": 0, "f12_MultiGen": 0, "f13_PostRep": 0,
     "f14_KinshipCode": 3, "f15_EpsDecay": None, "kinship_decisive": False,
     "patriarchal_control": True},
    {"substrate": "elephant", "domain": "biological_kinship",
     "f1_InterLethal": 0.0, "f2_IntraLethal": 0.0, "f4_MatriAnalog": 1,
     "f6_Coalition": 0, "f9_SubstrateSharing_chem": 0, "f10_Tool": 0,
     "f11_Allo": 1, "f12_MultiGen": 1, "f13_PostRep": 1,
     "f14_KinshipCode": 1, "f15_EpsDecay": None, "kinship_decisive": True},
    {"substrate": "orca", "domain": "biological_kinship",
     "f1_InterLethal": 0.0, "f2_IntraLethal": 0.26, "f4_MatriAnalog": 1,
     "f6_Coalition": 0, "f9_SubstrateSharing_chem": 1, "f10_Tool": 0,
     "f11_Allo": 1, "f12_MultiGen": 1, "f13_PostRep": 1,
     "f14_KinshipCode": 2, "f15_EpsDecay": None, "kinship_decisive": True},
    {"substrate": "hyena", "domain": "biological_kinship",
     "f1_InterLethal": 2.5, "f2_IntraLethal": 2.5, "f4_MatriAnalog": 1,
     "f6_Coalition": 1, "f9_SubstrateSharing_chem": 1, "f10_Tool": 0,
     "f11_Allo": 1, "f12_MultiGen": 1, "f13_PostRep": 0,
     "f14_KinshipCode": 1, "f15_EpsDecay": None, "kinship_decisive": True},
    {"substrate": "lemur", "domain": "biological_kinship",
     "f1_InterLethal": 2.0, "f2_IntraLethal": 2.0, "f4_MatriAnalog": 1,
     "f6_Coalition": 0, "f9_SubstrateSharing_chem": 0, "f10_Tool": 0,
     "f11_Allo": 1, "f12_MultiGen": 1, "f13_PostRep": 0,
     "f14_KinshipCode": 1, "f15_EpsDecay": None, "kinship_decisive": True},
    {"substrate": "mole_rat", "domain": "biological_kinship",
     "f1_InterLethal": 0.0, "f2_IntraLethal": 3.0, "f4_MatriAnalog": 1,
     "f6_Coalition": 0, "f9_SubstrateSharing_chem": 1, "f10_Tool": 0,
     "f11_Allo": 1, "f12_MultiGen": 1, "f13_PostRep": 0,
     "f14_KinshipCode": 4, "f15_EpsDecay": None, "kinship_decisive": True},
]


def load_ndjson(path: Path) -> list[dict]:
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def class_E_catalog_asymmetry(rows: list[dict], decisive_field: str) -> dict:
    """Class E: catalog asymmetry — what proportion of decisive vs non-decisive
    substrates have each feature on. Returns ratios; high asymmetry = strong
    discriminator at this resolution."""
    decisive = [r for r in rows if r.get(decisive_field)]
    nondec = [r for r in rows if not r.get(decisive_field)]
    if not decisive or not nondec:
        return {}
    features = ["f4_MatriAnalog", "f6_Coalition", "f9_SubstrateSharing_chem",
                "f10_Tool", "f11_Allo", "f12_MultiGen", "f13_PostRep"]
    asym = {}
    for feat in features:
        d_mean = sum(r.get(feat, 0) for r in decisive) / len(decisive)
        n_mean = sum(r.get(feat, 0) for r in nondec) / len(nondec)
        asym[feat] = {"decisive_rate": d_mean, "nondecisive_rate": n_mean,
                      "asymmetry": abs(d_mean - n_mean)}
    return asym


def class_L_fiedler_partition(rows: list[dict], by_field: str = "f14_KinshipCode") -> dict:
    """Class L: kinship-code clustering.
    For each kinship-code value, count members; compute cohesion of
    decisive-kinship grouping vs non-decisive."""
    by_code = {}
    for r in rows:
        c = r.get(by_field)
        by_code.setdefault(c, []).append(r["substrate"])

    # Cohesion: high if decisive-kinship-codes-cluster cleanly
    decisive_codes = set(r[by_field] for r in rows if r.get("kinship_decisive"))
    nondec_codes = set(r[by_field] for r in rows if not r.get("kinship_decisive"))
    overlap = decisive_codes & nondec_codes
    separation = (1.0 if not overlap
                  else 1.0 - len(overlap) / len(decisive_codes | nondec_codes))
    return {
        "by_code": by_code,
        "decisive_codes": sorted(decisive_codes, key=lambda x: (x is None, x)),
        "nondecisive_codes": sorted(nondec_codes, key=lambda x: (x is None, x)),
        "overlap": sorted(overlap, key=lambda x: (x is None, x)),
        "code_separation": separation,
    }


def class_K_asymptotic_dof(rows: list[dict]) -> dict:
    """Class K: asymptotic-DOF rate from f15_EpsDecay. Group by domain;
    report mean and spread; check ε ∈ [0, 1] (Cauchy-form regime)."""
    by_domain = {}
    for r in rows:
        eps = r.get("f15_EpsDecay")
        if eps is None:
            continue
        by_domain.setdefault(r["domain"], []).append(eps)
    summary = {}
    for dom, eps_list in by_domain.items():
        if not eps_list:
            continue
        mean = sum(eps_list) / len(eps_list)
        var = sum((e - mean) ** 2 for e in eps_list) / max(len(eps_list), 1)
        summary[dom] = {
            "n": len(eps_list),
            "eps_mean": mean,
            "eps_std": math.sqrt(var),
            "eps_min": min(eps_list),
            "eps_max": max(eps_list),
            "in_cauchy_regime": all(0 <= e <= 1 for e in eps_list),
        }
    return summary


def class_C_streaming_direction(rows: list[dict]) -> dict:
    """Class C: cascade direction. Count by transmission_mode keywords."""
    modes = {}
    for r in rows:
        tm = r.get("transmission_mode", "unknown")
        modes[tm] = modes.get(tm, 0) + 1
    return modes


def class_I_cyclic_generational(rows: list[dict]) -> dict:
    """Class I: cyclic / generational structure proxy from f7/f8 lineage depth."""
    depths = []
    for r in rows:
        d = r.get("f8_LineageDepth_logmyr")
        if d is not None:
            depths.append((r["substrate"], d))
    if not depths:
        return {}
    return {
        "n_with_depth": len(depths),
        "depth_min_substrate": min(depths, key=lambda x: x[1]),
        "depth_max_substrate": max(depths, key=lambda x: x[1]),
        "depth_mean": sum(d for _, d in depths) / len(depths),
    }


def cross_substrate_cohesion_score(rows: list[dict]) -> float:
    """Spike #44 R2-style cohesion: average asymmetry in the kinship-decisive
    discriminator across the 15-feature space. Higher = H_kinship discriminates
    cleanly across the substrate set."""
    decisive = [r for r in rows if r.get("kinship_decisive")]
    nondec = [r for r in rows if not r.get("kinship_decisive")]
    if not decisive or not nondec:
        # All decisive or all not — cohesion is uniform agreement; positive but
        # undiscriminating
        return 1.0 if decisive and not nondec else 0.0
    features = ["f4_MatriAnalog", "f6_Coalition", "f9_SubstrateSharing_chem",
                "f10_Tool", "f11_Allo", "f12_MultiGen", "f13_PostRep",
                "f14_KinshipCode"]
    asyms = []
    for feat in features:
        d_vals = [r.get(feat, 0) or 0 for r in decisive]
        n_vals = [r.get(feat, 0) or 0 for r in nondec]
        d_mean = sum(d_vals) / len(d_vals)
        n_mean = sum(n_vals) / len(n_vals)
        # Normalise per-feature spread
        all_vals = d_vals + n_vals
        rng = max(all_vals) - min(all_vals) if max(all_vals) != min(all_vals) else 1
        asyms.append(abs(d_mean - n_mean) / rng)
    return sum(asyms) / len(asyms)


def main() -> int:
    cosmic = load_ndjson(OUT_DIR / "cosmic_fingerprints.ndjson")
    human = load_ndjson(OUT_DIR / "human_fingerprints.ndjson")
    bio = biological_fingerprints

    # Augment cosmic / human with kinship_decisive flag
    for r in cosmic:
        r["kinship_decisive"] = r.get("kinship_decisive", True)
    for r in human:
        r["kinship_decisive"] = r.get("kinship_decisive", True)

    all_substrates = cosmic + human + bio

    print(f"Total substrates: {len(all_substrates)} ({len(cosmic)} cosmic + "
          f"{len(human)} human + {len(bio)} biological)")

    # --- Per-substrate fingerprint analysis ---
    results = {}
    for name, rows in [("cosmic", cosmic), ("human", human),
                        ("biological", bio), ("all_combined", all_substrates)]:
        results[name] = {
            "n_substrates": len(rows),
            "n_decisive": sum(1 for r in rows if r.get("kinship_decisive")),
            "class_E_catalog_asymmetry": class_E_catalog_asymmetry(rows, "kinship_decisive"),
            "class_L_fiedler_partition": class_L_fiedler_partition(rows),
            "class_K_asymptotic_dof": class_K_asymptotic_dof(rows),
            "class_C_streaming_direction": class_C_streaming_direction(rows),
            "class_I_cyclic_generational": class_I_cyclic_generational(rows),
            "cohesion_score": cross_substrate_cohesion_score(rows),
        }

    # Write summary records
    with RECORDS_PATH.open("w", encoding="utf-8") as f:
        for name, res in results.items():
            rec = {"date": "2026-05-17", "spike": "spike_45_round1",
                   "kind": "signature_summary", "substrate_group": name, **res}
            f.write(json.dumps(rec, default=str) + "\n")

    # Print human-readable summary
    print("\n" + "=" * 70)
    print("CROSS-SUBSTRATE CASCADE-COMPOSITION SIGNATURES")
    print("=" * 70)
    for name in ["biological", "cosmic", "human", "all_combined"]:
        res = results[name]
        print(f"\n--- {name.upper()} ({res['n_substrates']} substrates) ---")
        print(f"  H_kinship-decisive: {res['n_decisive']}/{res['n_substrates']}")
        print(f"  Cohesion score:     {res['cohesion_score']:.3f}")
        print(f"  Code separation:    {res['class_L_fiedler_partition']['code_separation']:.3f}")
        print(f"  Decisive codes:     {res['class_L_fiedler_partition']['decisive_codes']}")
        print(f"  Non-decisive codes: {res['class_L_fiedler_partition']['nondecisive_codes']}")

        dof = res['class_K_asymptotic_dof']
        if dof:
            for dom, s in dof.items():
                print(f"  Class K eps ({dom}): mean={s['eps_mean']:.4f} "
                      f"std={s['eps_std']:.4f} range=[{s['eps_min']:.4f}, "
                      f"{s['eps_max']:.4f}] cauchy_regime={s['in_cauchy_regime']}")

        # Top discriminating features
        ce = res['class_E_catalog_asymmetry']
        if ce:
            top = sorted(ce.items(), key=lambda x: -x[1]['asymmetry'])[:3]
            print(f"  Top class-E asymmetry features:")
            for feat, info in top:
                print(f"    {feat}: {info['decisive_rate']:.2f} vs "
                      f"{info['nondecisive_rate']:.2f} "
                      f"(asym={info['asymmetry']:.2f})")

    print(f"\nWrote signature records to {RECORDS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
