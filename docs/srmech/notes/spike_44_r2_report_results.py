"""Report results of cross-clade signature analysis."""
import json

records = []
with open("D:/temp/spike_44_r2/spike_44_r2_records_2026-05-17.ndjson") as f:
    for line in f:
        records.append(json.loads(line))


print("="*80)
print("=== SPECIES FINGERPRINTS ===")
print("="*80)
for r in records:
    if r["kind"] == "species_fingerprint":
        common = r["common"]
        print(f"\n  {common}:")
        for k in sorted(r.keys()):
            if k.startswith("f"):
                v = r[k]
                if isinstance(v, float):
                    print(f"    {k}: {v:.3f}")
                else:
                    print(f"    {k}: {v}")


print()
print("="*80)
print("=== MATRIARCHAL COHESION SCORES (without mole-rat) ===")
print("=== higher = matriarchal clade tighter under hypothesis ===")
print("="*80)
for r in records:
    if r["kind"] == "matriarchal_cohesion_score":
        h = r["hypothesis"]
        c = r["cohesion_score"]
        intra = r["intra_matriarchal_mean_distance"]
        cross = r["matriarchal_to_control_mean_distance"]
        print(f"  {h:15s} cohesion={c:+.3f}  (intra_M={intra:.3f}, M-to-control={cross:.3f})")


print()
print("="*80)
print("=== MATRIARCHAL COHESION WITH MOLE-RAT ===")
print("="*80)
for r in records:
    if r["kind"] == "matriarchal_cohesion_score_with_mole_rat":
        h = r["hypothesis"]
        c = r["cohesion_score"]
        print(f"  {h:15s} cohesion={c:+.3f}")


print()
print("="*80)
print("=== CLOSEST 3 PAIRS UNDER EACH HYPOTHESIS ===")
print("="*80)
for r in records:
    if r["kind"] == "hypothesis_test":
        print(f"\n  {r['hypothesis']}:")
        for p in r["closest_3_pairs"]:
            print(f"    {p[0]:30s} <-> {p[1]:30s} d={p[2]:.3f}")


print()
print("="*80)
print("=== FULL-FEATURE CLOSEST PAIRS ===")
print("="*80)
for r in records:
    if r["kind"] == "cross_clade_clustering_FULL":
        print()
        for p in r["closest_5_pairs"]:
            print(f"  {p[0]:30s} <-> {p[1]:30s} d={p[2]:.3f}")


print()
print("="*80)
print("=== FEATURE DISCRIMINATION (matriarchal vs control = chimp) ===")
print("="*80)
for r in records:
    if r["kind"] == "feature_discrimination":
        marker = " *** " if r["discriminates"] else "     "
        print(f"  {marker}{r['feature']:35s} M={r['matriarchal_mean']:+6.3f}  C={r['control_mean']:+6.3f}  diff={r['difference']:+6.3f}")
