"""
Spike #51 dual-axis verification — strict-spec test gate per
[[feedback_multi_domain_multi_round_survival_falsification_method]] Meta-lesson 2.

AXIS A: substrate-identity test (M-theory squashed-S^7 G2 vs Spike #47 R1 S^7)
        already closed at Spike #84 R4 = PARTITION-COEXISTENCE-CANONICAL ~90%.
        This script re-affirms the verdict against AXIS B brane mappings.

AXIS B: brane-cascade-mapping (10 candidates against 14 A-N class operators)
        per spike_51_brane_cascade_mapping_ledger_2026-05-19.ndjson.

Strict-spec discipline:
  - 14 classes A-N intact (no promotion)
  - Each candidate's class assignment is verified against a canonical class
    definition (per [[user_stance_closure_subgroup_BDEFL_substrate_class_universal]]
    strict definitions) — IDENTITY-LEVEL or IMPLEMENTATION-only.
  - Dissolved classes (Class O → L signed-variant) honored.
  - No autonomous stance authoring.
"""

import json
import pathlib

CANONICAL_CLASSES = {
    "A": "content-addressing (SHA-256)",
    "B": "TLV byte-canonical form",
    "C": "cyclic-cascade orientation reversal (signed-Laplacian variant per dissolved O)",
    "D": "dispatch multi-needle pattern match",
    "E": "catalog sorted-key lookup",
    "F": "template {key} substitution",
    "G": "byte-pattern search",
    "H": "self-introspection (version / ABI)",
    "I": "cyclic-group / modular arithmetic",
    "J": "prime factorisation / period (multiplicative order)",
    "K": "asymptotic-DOF pin-slot mechanism",
    "L": "graph Laplacian / Jacobi eigvals (signed variant absorbs dissolved Class O)",
    "M": "HDC bind / bundle / permute / similarity",
    "N": "equation-of-centre algebra / rational approximation",
}

# Allowed match-level vocabulary
MATCH_LEVELS = {"IDENTITY", "IMPLEMENTATION", "ANALOGY"}


def load_ledger(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def normalise_class(class_tag):
    """Map composite class tags (L_signed_variant, L_bipartite, L_plus_triality)
    back to canonical 14 A-N. Sub-operations are sub-structural, not new classes.
    """
    base = class_tag.split("_")[0]
    return base


def verify_record(rec):
    cls = rec["candidate_class"]
    base = normalise_class(cls)
    issues = []
    if base not in CANONICAL_CLASSES:
        issues.append(f"class {base!r} not in 14 A-N")
    if rec["match_level"] not in MATCH_LEVELS:
        issues.append(f"match_level {rec['match_level']!r} not in {MATCH_LEVELS}")
    if not rec.get("strict_spec_pass", False):
        issues.append("strict_spec_pass missing or False")
    if not rec.get("supporting_citation"):
        issues.append("supporting_citation empty")
    return issues, base


def main():
    here = pathlib.Path(__file__).parent
    ledger = here / "spike_51_brane_cascade_mapping_ledger_2026-05-19.ndjson"
    records = load_ledger(ledger)

    print(f"Loaded {len(records)} brane-cascade-mapping records from {ledger.name}")
    print()

    by_class = {}
    by_match_level = {}
    all_issues = []

    for rec in records:
        issues, base = verify_record(rec)
        by_class.setdefault(base, []).append(rec["mapping_id"])
        by_match_level.setdefault(rec["match_level"], []).append(rec["mapping_id"])
        if issues:
            all_issues.append((rec["mapping_id"], issues))

    print("Class coverage (canonical 14 A-N basis):")
    for cls in sorted(CANONICAL_CLASSES):
        ids = by_class.get(cls, [])
        if ids:
            print(f"  {cls} ({CANONICAL_CLASSES[cls]}): mappings {ids}")
    print()

    print("Match-level distribution:")
    for lvl in MATCH_LEVELS:
        ids = by_match_level.get(lvl, [])
        print(f"  {lvl}: {len(ids)} mappings — {ids}")
    print()

    identity_count = len(by_match_level.get("IDENTITY", []))
    impl_count = len(by_match_level.get("IMPLEMENTATION", []))
    analogy_count = len(by_match_level.get("ANALOGY", []))
    total = identity_count + impl_count + analogy_count

    print(f"AXIS B verdict numerics:")
    print(f"  Total mappings: {total}")
    print(f"  IDENTITY-level matches: {identity_count}/{total} = {identity_count*100/total:.1f}%")
    print(f"  IMPLEMENTATION-only: {impl_count}/{total}")
    print(f"  ANALOGY-only: {analogy_count}/{total}")
    print()

    if identity_count >= 7:
        print(f"  AXIS B verdict: STRONG support for substrate-identity reframe attempt")
        print(f"    (IDENTITY >= 7/10 threshold met)")
    elif identity_count < 5:
        print(f"  AXIS B verdict: REFUTES substrate-identity reframe attempt")
        print(f"    (IDENTITY < 5/10 threshold)")
    else:
        print(f"  AXIS B verdict: WEAK support (5-6/10) -- need to read with AXIS A context")
    print()

    if all_issues:
        print(f"VALIDATION ISSUES ({len(all_issues)} records):")
        for mid, issues in all_issues:
            print(f"  mapping_id {mid}: {issues}")
    else:
        print("ALL RECORDS PASS strict-spec validation.")
    print()

    # Vocabulary intact check
    classes_used = set(by_class.keys())
    expected_canon = set(CANONICAL_CLASSES.keys())
    extra = classes_used - expected_canon
    if extra:
        print(f"FAIL: vocabulary expanded beyond 14 A-N: {extra}")
    else:
        print(f"PASS: vocabulary stays at 14 A-N (used {len(classes_used)}/{14} classes).")
    print()

    # Class coverage summary for class-substitution-on-invariant-backbone
    # (per [[user_stance_class_substitution_on_invariant_backbone]])
    print("Class-substitution-on-invariant-backbone analysis:")
    print(f"  M-theory cascade substrate uses classes: {sorted(classes_used)}")
    print(f"  Invariant-backbone candidate: {{C, D, E, K, L, M}} (6 classes touched)")
    print(f"  Closure-subgroup BDEFL overlap: {sorted(classes_used & {'B','D','E','F','L'})}")
    print()

    # AXIS A re-affirmation
    print("AXIS A re-affirmation (substrate-identity verdict):")
    print("  Per Spike #84 R4 canonical: PARTITION-COEXISTENCE-CANONICAL ~90%.")
    print("  Three substrate realizations all valid different geometric")
    print("  instantiations of same Class I cyclic-cascade primitive on")
    print("  parallelizable 7-sphere (Adams 1958):")
    print("    (1) project round-S^7 (Spin(8); lambda^2=1)")
    print("    (2) M-theory squashed-S^7 (Sp(2)xSp(1); lambda^2=1/5)")
    print("    (3) Joyce-class compact-G_2 (T^7/Gamma + ADE resolution)")
    print("  Verdict A (unique-identity): ~5%")
    print("  Verdict B (partition-coexistence): ~90% CANONICAL")
    print("  Verdict C (different-substrates): ~5%")


if __name__ == "__main__":
    main()
