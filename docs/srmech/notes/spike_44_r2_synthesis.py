"""
Spike #44 round 2 - Synthesis: which hypothesis survives data?

H_sex: SEX (matriarchy) is decisive variable. All matriarchal mammals share signature.
H_coalition: FEMALE-COALITION-CAPABILITY is decisive. Hyena+bonobo cluster; others don't.
H_ecology: Sharing-shape varies with ecological niche independently of sex.
H_kinship: Sharing-shape varies with kinship structure.
H_compound: Multiple variables jointly; no single axis decisive.

Method: closed-form analysis from feature-by-feature pattern + cohesion scoring.
"""

import json
from pathlib import Path
import numpy as np

OUT_DIR = Path(r"D:\temp\spike_44_r2")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# Load fingerprints
records = []
with open(OUT_DIR / "spike_44_r2_records_2026-05-17.ndjson") as f:
    for line in f:
        records.append(json.loads(line))


fingerprints = [r for r in records if r["kind"] == "species_fingerprint"]
cohesion_scores = [r for r in records if r["kind"] == "matriarchal_cohesion_score"]
cohesion_with_mole_rat = [r for r in records if r["kind"] == "matriarchal_cohesion_score_with_mole_rat"]
feature_discrim = [r for r in records if r["kind"] == "feature_discrimination"]


# ===========================================================================
# Synthesis 1: Cohesion ranking
# ===========================================================================
print()
print("="*80)
print("SYNTHESIS §1 - HYPOTHESIS COHESION RANKING")
print("="*80)
print()

sorted_cohesion = sorted(cohesion_scores, key=lambda r: -r["cohesion_score"])
print("Without mole-rat (5 matriarchal + chimp control):")
for r in sorted_cohesion:
    print(f"  {r['hypothesis']:15s} cohesion={r['cohesion_score']:+.3f}")

print()
sorted_cohesion_with = sorted(cohesion_with_mole_rat, key=lambda r: -r["cohesion_score"])
print("With mole-rat (6 matriarchal + chimp control):")
for r in sorted_cohesion_with:
    print(f"  {r['hypothesis']:15s} cohesion={r['cohesion_score']:+.3f}")


# ===========================================================================
# Synthesis 2: Per-hypothesis examination - within-matriarchal heterogeneity
# ===========================================================================
print()
print("="*80)
print("SYNTHESIS §2 - WITHIN-MATRIARCHAL HETEROGENEITY (each hypothesis)")
print("="*80)

# Build species-fingerprint map
sp_fp = {fp["common"]: fp for fp in fingerprints}
matri = ["Bonobo", "African savanna elephant", "Killer whale / orca",
          "Spotted hyena", "Ring-tailed lemur"]

print()
print(f"H_sex (f3, f4, f5):")
print(f"  {'species':30s} | f3_FD_intersex | f4_matriarchal | f5_all_F_above_all_M")
for sp in matri:
    fp = sp_fp[sp]
    print(f"  {sp:30s} | {fp['f3_female_dominant_intersex']:14d} | {fp['f4_matriarchal']:14d} | {fp['f5_all_females_outrank_males']:18d}")
print("  ANOMALY: only Hyena and Lemur have f3=1 AND f5=1. Bonobo, Elephant, Orca have f4=1 but f3=0 + f5=0.")
print("  -> Matriarchy is heterogeneous: some species female-dominant by individual, others by coalition/age.")

print()
print(f"H_coalition (f6, f7, f8):")
print(f"  {'species':30s} | f6_intersex_coal | f7_F_coalit_dom | f8_high_freq")
for sp in matri:
    fp = sp_fp[sp]
    print(f"  {sp:30s} | {fp['f6_intersex_coalition']:16d} | {fp['f7_female_coalition_dominance']:14d} | {fp['f8_coalitions_high_frequency']:12d}")
print("  ANOMALY: ONLY Bonobo+Hyena have intersex coalition. ONLY Hyena has all-3.")
print("  -> Coalition is a Bonobo-Hyena signature, NOT a matriarchal universal.")

print()
print(f"H_kinship (f11, f12, f13, f14):")
print(f"  {'species':30s} | f11_allom | f12_multgen | f13_postrep | f14_kinship_code")
for sp in matri:
    fp = sp_fp[sp]
    print(f"  {sp:30s} | {fp['f11_allomothering']:9d} | {fp['f12_multigenerational']:11d} | {fp['f13_post_reproductive_longevity']:11d} | {fp['f14_kinship_code']:16d}")
print("  PATTERN: All matriarchal species f11=1 (allomothering). 4/5 multigenerational (Bonobo=0).")
print("  Kinship: Elephant=1, Orca=2, Hyena=1, Lemur=1; Bonobo=3 (male-philopatric like chimp!)")
print("  -> Bonobo is KINSHIP-OUTLIER among matriarchal clades. Its matriarchy is REINVENTED via coalition.")


# ===========================================================================
# Synthesis 3: The kinship-vs-sex finding
# ===========================================================================
print()
print("="*80)
print("SYNTHESIS §3 - KINSHIP > SEX AS DISCRIMINATOR")
print("="*80)
print()
print("Cohesion scores: H_kinship (+0.661) > H_sex (+0.444) > H_ecology (-0.188) > H_coalition (-0.341)")
print()
print("H_kinship outperforms H_sex because:")
print("  - Bonobo (male-philopatric, kinship_code=3) clusters with Chimp (male-philopatric, =3)")
print("    UNDER kinship lens, despite both being matriarchal vs patriarchal under sex lens")
print("  - Elephant/Hyena/Lemur all kinship_code=1 (female-philopatric, matrilineal)")
print("    cluster tightly together with each other")
print("  - Orca is kinship_code=2 (both-natally-philopatric) - boundary case but closer to 1 than 3")
print()
print("Implication: the variable that best predicts the OTHER signature features")
print("(allomothering, multigenerational structure, post-reproductive longevity)")
print("is MATRILINEAL KINSHIP STRUCTURE, not female dominance per se.")


# ===========================================================================
# Synthesis 4: Round 1 review through round 2 lens
# ===========================================================================
print()
print("="*80)
print("SYNTHESIS §4 - ROUND 1 RECONSIDERED")
print("="*80)
print()
print("Round 1 fermata: is it female-DOMINANCE or female-COALITION-CAPABILITY decisive?")
print()
print("Round 2 answer: NEITHER alone.")
print("  - female-coalition-capability is a Bonobo-Hyena SHARED FEATURE not a matriarchy universal")
print("  - female-dominance is heterogeneous (individual vs coalition vs age-based)")
print()
print("The deeper variable is KINSHIP STRUCTURE - which constrains what coalitions can form")
print("and how multigenerational knowledge transmission works:")
print()
print("Class L female-philopatric clade (Elephant, Hyena, Lemur):")
print("  - Multigenerational matriline lineages within social group")
print("  - Females can coalesce because they grew up together")
print("  - Knowledge transmission via matriline")
print()
print("Class L male-philopatric clade (Chimp, Bonobo):")
print("  - Females immigrate as adults; no kin ties at adulthood")
print("  - Female coalition requires REINVENTION across unrelated immigrants")
print("  - CHIMP: female coalition fails (no kin substrate) -> male coalition dominates")
print("  - BONOBO: female coalition emerges DESPITE lack of kin substrate (Tokuyama 2019")
print("    documents cross-group female cooperation; Surbeck 2025 documents 85% coalition")
print("    targeting males) -> ANOMALY requiring explanation")
print()
print("Class L both-natally-philopatric (Orca):")
print("  - Both sexes stay -> kin substrate for both")
print("  - But coalitions don't form because there is no intergroup competition to coalesce against")
print("  - Pod cooperation IS the structure; no internal coalition contest")


# ===========================================================================
# Synthesis 5: Class-by-class round-2 verdict
# ===========================================================================
print()
print("="*80)
print("SYNTHESIS §5 - PRIMITIVE-CLASS VERDICT")
print("="*80)
print()
print("Class L (Laplacian / partition):")
print("  Lethal-aggression-partition signature (round 1 cleanest discriminator) extended:")
print("    Chimp: 125/100k/y intergroup; the OUTLIER among 7 species")
print("    Bonobo, Elephant, Orca, Mole-rat: ~0 intergroup lethal")
print("    Hyena, Lemur: moderate (documented but not standardized)")
print("  -> Lethal-aggression-partition correlates with kinship-substrate-availability:")
print("     male-philopatric clades CAN escalate to intergroup violence (chimp) or NOT (bonobo)")
print("     female-philopatric clades DON'T escalate to high intergroup violence rates")
print()
print("Class K (asymmetric pin-slot / dominance steepness):")
print("  Heterogeneous across matriarchal clades:")
print("    Hyena: linear hierarchy, matrilineal rank inheritance, all-F-above-all-M (strict)")
print("    Lemur: female-dominant by individual aggression")
print("    Elephant: female-dominant in family group BUT no intersex contest (sexes separate)")
print("    Orca: matriarch-led but no explicit intersex steepness")
print("    Bonobo: female-dominant via coalition (REINVENTED matriarchy)")
print("    Mole-rat: queen-dominant, eusocial - extreme asymmetry")
print()
print("Class C (cascade composition):")
print("  Aggression cascades:")
print("    Chimp: cross-sex, escalates")
print("    Bonobo: male-male, non-lethal (de-escalates)")
print("    Hyena: high frequency, ritualized in greeting/coalition")
print("    Elephant: low frequency, mostly play-like at young ages")
print("    Orca: rare and low")
print("    Lemur: high female-to-male agonism rates (5.2/h)")
print("    Mole-rat: queen-driven, suppressive")
print()
print("Class E (catalog of shared resources):")
print("  Food sharing universal among matriarchal-with-strong-coalition (Bonobo, Hyena, Orca)")
print("  Knowledge transmission universal among multigenerational matriarchal (Elephant, Orca, Hyena)")
print("  Allomothering universal across ALL matriarchal clades")
print("  Tool sharing only in Chimpanzee (NOT matriarchal)")
print()
print("Class I (cyclic / multigenerational):")
print("  Multigenerational structure correlates with kinship-philopatry NOT with sex hierarchy")
print("  Post-reproductive longevity (menopause-like): ONLY Elephant and Orca")
print("    -> These two = both have post-reproductive matriarch knowledge-leader role")
print("    -> Suggests: 'matriarch-as-repository' is its own ecological niche, distinct from")
print("       'female-dominant-aggressive' niche of hyena/lemur")


# ===========================================================================
# Synthesis 6: The fermata for round 3
# ===========================================================================
print()
print("="*80)
print("SYNTHESIS §6 - FERMATA FOR ROUND 3 (if needed)")
print("="*80)
print()
print("Round 2 finds H_compound is the actual answer: multiple variables jointly.")
print("Specifically: KINSHIP STRUCTURE > SEX HIERARCHY in predicting sharing-shape.")
print()
print("This refines the round-1 finding. Round 1 found bonobo Class L override of male Class K.")
print("Round 2 finds: that override CAN happen even WITHOUT female-philopatric kinship substrate")
print("(bonobo is male-philopatric), but it's structurally REINVENTED rather than inherited.")
print()
print("Open questions for round 3 if dispatched:")
print()
print("1. WITHIN the female-philopatric matriarchal cluster (Elephant + Hyena + Lemur),")
print("   what discriminates the THREE? Is it ecological niche (mega-herbivore vs carnivore vs primate)")
print("   or is it body-size (Hyena large; Lemur small) or fission-fusion (Elephant fission-fusion;")
print("   Lemur cohesive troop)?")
print()
print("2. IS the bonobo female-coalition REINVENTION a substrate-portable mechanism, or")
print("   bonobo-specific? Are there OTHER male-philopatric matriarchal-via-coalition species?")
print("   (Candidates: Atelids; some lemurs; if not, bonobo is the unique reinvention)")
print()
print("3. POST-REPRODUCTIVE LONGEVITY (menopause-like) clusters only Elephant+Orca+(human).")
print("   This is a DIFFERENT cluster than 'matriarchal' broadly. Round 3 could test:")
print("   menopause-cluster vs matriarchal-cluster distinction. Different sharing-shape signatures?")
print()
print("4. MOLE-RAT boundary case: eusociality is its own thing. Including it shifts kinship-cohesion")
print("   down (0.66 -> 0.23) but doesn't qualitatively change verdict. Round 3 could choose")
print("   to include or exclude eusocial mammals (mole-rats + Damaraland mole-rats) as a")
print("   separate cluster.")


print()
print("="*80)
print("BOTTOM LINE")
print("="*80)
print()
print("H_kinship (matrilineal kinship structure) survives the data BETTER than H_sex.")
print("H_compound (kinship + reinvention of coalitions where kin substrate absent) survives BEST.")
print()
print("Sex per se is NOT the decisive variable.")
print("KINSHIP STRUCTURE that enables multigenerational female bonds IS the deeper variable.")
print("Bonobos are the special case: matriarchy REINVENTED across an unfavorable kin substrate.")


# Write synthesis records
synthesis_records = [
    {"kind": "synthesis_cohesion_ranking",
     "ranking_without_mole_rat": [{"hyp": r["hypothesis"], "cohesion": r["cohesion_score"]} for r in sorted_cohesion],
     "ranking_with_mole_rat": [{"hyp": r["hypothesis"], "cohesion": r["cohesion_score"]} for r in sorted_cohesion_with]},
    {"kind": "synthesis_bottom_line",
     "verdict": "H_kinship_over_H_sex",
     "h_kinship_cohesion": next(r["cohesion_score"] for r in cohesion_scores if r["hypothesis"] == "H_kinship"),
     "h_sex_cohesion": next(r["cohesion_score"] for r in cohesion_scores if r["hypothesis"] == "H_sex"),
     "h_coalition_cohesion": next(r["cohesion_score"] for r in cohesion_scores if r["hypothesis"] == "H_coalition"),
     "h_ecology_cohesion": next(r["cohesion_score"] for r in cohesion_scores if r["hypothesis"] == "H_ecology"),
     "interpretation": "Matrilineal kinship structure that enables multigenerational female bonds is the deeper variable. Female dominance per se is heterogeneous across matriarchal clades and not the cleanest discriminator. Bonobos are the special-case anomaly: matriarchy REINVENTED across an unfavorable (male-philopatric) kin substrate."},
    {"kind": "synthesis_bonobo_anomaly",
     "anomaly": "Bonobo is male-philopatric (kinship_code=3) like chimp, yet exhibits female-coalition matriarchy",
     "explanation_candidate": "Female-coalition can be REINVENTED across unrelated adult immigrants given right substrate-conditions; documented by Tokuyama 2019 (cross-group female cooperation at Wamba) and Surbeck 2025 (85% of coalitions target males)",
     "implication": "Sharing-shape is NOT strictly substrate-bound to kinship; reinvention pathways exist. But default pathway (kin-based) is more common."},
    {"kind": "synthesis_class_verdict",
     "class_L_lethal_partition": "kinship-substrate-availability constrains; female-philopatric clades show low rates",
     "class_K_steepness": "heterogeneous across matriarchal clades; not a clean signature alone",
     "class_C_cascade": "varies by clade; bonobo de-escalates, hyena ritualizes, elephant low-frequency",
     "class_E_catalog": "allomothering universal among matriarchals; food-sharing in Bonobo/Hyena/Orca; knowledge-transmission in multigenerational",
     "class_I_multigenerational": "correlates with kinship-philopatry; menopause-cluster (Elephant+Orca) is a sub-niche"},
    {"kind": "synthesis_round3_fermata",
     "open_q_1": "What discriminates within female-philopatric matriarchal cluster (Elephant/Hyena/Lemur)?",
     "open_q_2": "Is bonobo female-coalition reinvention substrate-portable or unique?",
     "open_q_3": "Post-reproductive-longevity cluster (Elephant+Orca+human) vs matriarchal broadly - different sharing-shape?",
     "open_q_4": "Eusocial mammals as separate cluster - include or exclude?"},
]

with open(OUT_DIR / "spike_44_r2_synthesis_records.ndjson", "w", encoding="utf-8") as f:
    for r in synthesis_records:
        f.write(json.dumps(r, default=str) + "\n")

print(f"\nWrote {len(synthesis_records)} synthesis records.")
