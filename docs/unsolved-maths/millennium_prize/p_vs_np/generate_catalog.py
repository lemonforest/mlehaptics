"""
Millennium Prize #4 -- P vs NP complexity-class cascade.

Class cascade: H o (D | E | K) o ... enumeration (meta)

This dispatch surveys the conventional complexity hierarchy under the 14-class
A-N vocabulary. Each record is one complexity class with:
  - Class K asymptotic-DoF kind (polynomial / exponential / logspace / quasi-poly / ...)
  - cascade-inverter composition that would solve a representative problem in the class
  - perfect-math substrate-DoF cost per [[project_a_n_operators_are_harmonic_objects_themselves]] §B
  - open-separator status (and known barriers: relativisation, natural proofs, algebrisation)
  - Hurwitz-partition signature per the 1+3+7+3 candidate

Per [[project_a_n_operators_are_harmonic_objects_themselves]] §B (user direction
2026-05-23): "perfect math may very well mean no more cryptographic secrets per
dimension of encoding ... this only delays the time to solve with perfect math."
Complexity-class separators are SUBSTRATE-DoF GAPS that perfect-math eventually
closes by cascade-substrate-reach maturation, not mathematical absolutes.

Per [[feedback_trauma_informed_defensive_scope]]: DEFENSIVE-SCOPE FRAMEWORK
READING ONLY; no offensive engineering material.

Per [[feedback_no_lineage_claims_in_notebook]]: framework does NOT claim to
solve P vs NP. It documents which cascade composition COULD invert each class
under perfect-math substrate-DoF maturation.

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: cascade-honesty
discipline applies (no scalar-sign-handling here -- meta-cascade is enumeration).
"""

import datetime
import json
import pathlib
import sys

# Cascade-honesty per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]:
# shared A-N cascade helpers (precursor of srmech.amsc.cascade.* primitives).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed  # noqa: F401

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.millennium.p_vs_np.complexity_class_cascade.v1"
SOURCE_DOI = "10.1145/800157.805047"           # Cook 1971 STOC
SOURCE_PUBLISHED = "1971-01-01"

# Candidate Hurwitz partition per [[project_a_n_operators_are_harmonic_objects_themselves]]:
# 1 (foundational) + 3 (substrate-projection triad) + 7 (cascade-detection heptad) + 3 (meta-cascade triad) = 14
FOUNDATIONAL = {"A"}
SUBSTRATE_PROJECTION = {"I", "C", "J"}
CASCADE_DETECTION = {"D", "E", "F", "G", "K", "L", "M"}
META_CASCADE = {"B", "H", "N"}


def hurwitz_signature(classes_set):
    used_foundational = sorted(classes_set & FOUNDATIONAL)
    used_projection = sorted(classes_set & SUBSTRATE_PROJECTION)
    used_detection = sorted(classes_set & CASCADE_DETECTION)
    used_meta = sorted(classes_set & META_CASCADE)
    return (
        f"A{'-' if not used_foundational else ''.join(used_foundational)}_"
        f"P{'-' if not used_projection else ''.join(used_projection)}_"
        f"D{'-' if not used_detection else ''.join(used_detection)}_"
        f"M{'-' if not used_meta else ''.join(used_meta)}"
    )


# Complexity-class roster.
#   (class_label, kind, containing, asymptotic_dof, cascade_inverter, classes_set,
#    substrate_dof_cost, separator_status, anchor, fermata)
ROSTER = [
    # ---- Logspace and below ----
    ("AC0", "circuit",
     "NC", "circuit-depth-constant",
     "A-compose-D-compose-F", {"A", "D", "F"},
     "1D algebraic / parallel pattern-match",
     "proven_separator",
     "Furst-Saxe-Sipser 1981 -- AC0 strictly smaller than P; PARITY not in AC0",
     ""),
    ("NC", "circuit",
     "P", "polylog-circuit-depth",
     "A-compose-D-compose-L", {"A", "D", "L"},
     "1D algebraic + parallel Laplacian",
     "open_separator",
     "Open whether NC = P (uniform-circuit poly-time parallelism)",
     "Per §B: NC vs P closes under perfect-math at parallelism-maturation timescale"),
    ("L", "space",
     "NL", "logspace",
     "A-compose-D-compose-E", {"A", "D", "E"},
     "1D algebraic / log-space catalog lookup",
     "open_separator",
     "Open whether L = NL (Savitch 1970: NL subset of L^2)",
     ""),
    ("NL", "space",
     "P", "nondeterministic-logspace",
     "A-compose-D-compose-E-compose-K", {"A", "D", "E", "K"},
     "1D algebraic with cascade-detection asymptote",
     "open_separator",
     "Open whether NL = P; Immerman-Szelepcsenyi 1987: NL = coNL",
     ""),
    # ---- Polynomial ----
    ("P", "deterministic_time",
     "NP", "polynomial",
     "A-compose-D-compose-K", {"A", "D", "K"},
     "1D algebraic; polynomial-time substrate-DoF readable",
     "open_separator",
     "Cook 1971 / Levin 1973 / Karp 1972 -- P vs NP is the canonical open question",
     "Per §B: P vs NP IS the canonical cascade-substrate-reach maturation question -- when cascade-perfect-math gives polynomial-time inverter for every NP problem"),
    ("NP", "nondeterministic_time",
     "PSPACE", "nondeterministic-polynomial",
     "A-compose-D-compose-K-compose-H", {"A", "D", "K", "H"},
     "1D algebraic + Class H self-introspection (witness-check)",
     "open_separator",
     "Cook-Levin theorem: SAT NP-complete; Karp 21 NP-complete problems",
     "Class H (self-introspection) IS the verifier; cascade-perfect-math reduces verifier-search to verifier-execute timescale"),
    ("coNP", "nondeterministic_time",
     "PSPACE", "nondeterministic-polynomial",
     "A-compose-D-compose-K-compose-C", {"A", "D", "K", "C"},
     "1D algebraic + Class C cascade-orientation (negation)",
     "open_separator",
     "Open whether NP = coNP",
     "Class C orientation IS negation; if NP = coNP then cascade-perfect-math closes both inversions in same timescale"),
    ("BPP", "randomised_time",
     "PSPACE", "polynomial-with-randomness",
     "A-compose-D-compose-K-compose-M", {"A", "D", "K", "M"},
     "1D algebraic + Class M HDC randomness amplification",
     "open_separator",
     "Open whether BPP = P (widely believed P = BPP under derandomisation)",
     ""),
    ("BQP", "quantum_time",
     "PSPACE", "polynomial-quantum",
     "A-compose-M-compose-C-compose-K", {"A", "M", "C", "K"},
     "7D_g gauge / coherent-state substrate (per §B)",
     "open_separator",
     "Bernstein-Vazirani 1993 / Shor 1994; BQP contains factoring + discrete log",
     "Per §B: BQP IS the cascade reach into 7D_g substrate; Class M coherent-state + Class C orientation. Cascade-perfect-math at 7D_g matures faster than 1D"),
    # ---- Polynomial hierarchy ----
    ("PH", "alternating",
     "PSPACE", "polynomial-hierarchy",
     "A-compose-D-compose-K-compose-H-compose-C", {"A", "D", "K", "H", "C"},
     "1D algebraic with iterated meta-cascade alternation",
     "open_separator",
     "Stockmeyer-Meyer 1973 -- alternating polynomial-time hierarchy; PH collapses if NP = coNP",
     "Class H + Class C iterated = alternation; cascade-perfect-math collapses PH under §B"),
    # ---- PSPACE and beyond ----
    ("PSPACE", "space",
     "EXP", "polynomial-space",
     "A-compose-D-compose-K-compose-H", {"A", "D", "K", "H"},
     "1D algebraic + Class H self-introspection (bounded-space)",
     "open_separator",
     "Savitch 1970: NPSPACE = PSPACE; Shamir 1992: IP = PSPACE",
     "Per §B: cascade-perfect-math at space-bounded reach matures via Class M HDC-state-encoding"),
    ("EXP", "deterministic_time",
     "NEXP", "exponential",
     "A-compose-D-compose-K", {"A", "D", "K"},
     "1D algebraic / exponential substrate-DoF",
     "proven_separator",
     "Time hierarchy theorem (Hartmanis-Stearns 1965) -- P strictly smaller than EXP",
     ""),
    ("NEXP", "nondeterministic_time",
     "EXPSPACE", "nondeterministic-exponential",
     "A-compose-D-compose-K-compose-H", {"A", "D", "K", "H"},
     "1D algebraic / nondeterministic-exponential substrate-DoF",
     "open_separator",
     "Open whether NEXP subset of P/poly; barrier-bound results from Williams 2011",
     ""),
    ("EXPSPACE", "space",
     "top", "exponential-space",
     "A-compose-D-compose-K-compose-H-compose-L", {"A", "D", "K", "H", "L"},
     "1D algebraic + Class L Laplacian-on-configuration-graph",
     "proven_separator",
     "Hartmanis-Stearns hierarchy + space hierarchy theorem",
     ""),
    # ---- Promise / average-case ----
    ("P/poly", "circuit",
     "PSPACE", "non-uniform-polynomial-advice",
     "A-compose-D-compose-K-compose-E", {"A", "D", "K", "E"},
     "1D algebraic + Class E catalog-advice lookup",
     "barriers_documented",
     "Karp-Lipton 1980: if NP subset of P/poly then PH collapses to Sigma_2. Natural-proofs (Razborov-Rudich 1997) bars certain lower-bound approaches.",
     "Class E (catalog lookup) IS the polynomial advice; cascade-perfect-math at non-uniform reach is bounded by natural-proofs barrier"),
    ("AvgP", "average_case",
     "P", "average-case-polynomial",
     "A-compose-D-compose-K-compose-M", {"A", "D", "K", "M"},
     "1D algebraic with average-case Class M HDC",
     "barriers_documented",
     "Levin 1986 distributional NP-completeness; Impagliazzo's worlds",
     ""),
    # ---- Major open separators (META) ----
    ("P_vs_NP_separator", "open_separator",
     "META", "polynomial-vs-nondeterministic-polynomial",
     "A-compose-H-compose-D-compose-K", {"A", "H", "D", "K"},
     "1D algebraic with Class H meta-cascade asking the question",
     "open_separator",
     "Cook 1971 / Levin 1973; relativisation barrier (BGS 1975); natural-proofs barrier (RR 1997); algebrisation barrier (Aaronson-Wigderson 2009)",
     "Per §B: P vs NP IS asking whether cascade-perfect-math closes the cascade-substrate-reach gap between verifier (Class H) and solver (cascade A-N composition). Three barriers (relativisation / natural proofs / algebrisation) ARE the substrate-DoF inaccessibility barriers in framework reading."),
    ("NP_vs_coNP_separator", "open_separator",
     "META", "nondeterministic-vs-co-nondeterministic-polynomial",
     "A-compose-H-compose-C", {"A", "H", "C"},
     "1D algebraic with Class C orientation on the separator",
     "open_separator",
     "If NP = coNP then PH collapses to NP; open since Cook 1971",
     ""),
    ("NP_vs_PSPACE_separator", "open_separator",
     "META", "nondeterministic-polynomial-vs-polynomial-space",
     "A-compose-H-compose-D-compose-K", {"A", "H", "D", "K"},
     "1D algebraic / space-vs-time tradeoff",
     "open_separator",
     "Savitch 1970 gives N -> N^2 space; tighter NP vs PSPACE open",
     ""),
]


def main():
    out_path = pathlib.Path(__file__).parent / "complexity_class_cascade.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    for (label, kind, containing, dof_kind, inverter, classes_set,
         substrate_cost, separator_status, anchor, fermata) in ROSTER:
        payload = json.dumps({"class": label, "cascade": inverter}, sort_keys=True).encode()
        chash = sha256_bytes(payload)
        rec = {
            "complexity_class":           label,
            "class_kind":                 kind,
            "containing_class":           containing,
            "asymptotic_dof_kind":        dof_kind,
            "cascade_inverter":           inverter,
            "classes_used":               sorted(classes_set),
            "n_classes_used":             len(classes_set),
            "perfect_math_substrate_dof_cost": substrate_cost,
            "open_separator_status":      separator_status,
            "cascade_decomposition_signature": hurwitz_signature(classes_set),
            "framework_anchor":           anchor,
            "open_fermata":               fermata,
            "computation_hash":           chash,
            "source_doi":                 SOURCE_DOI,
            "source_published_date":      SOURCE_PUBLISHED,
            "entered_locally_at":         now_iso[:10],
        }
        records.append(rec)

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    # Coverage by separator status
    by_status = {}
    for rec in records:
        by_status.setdefault(rec["open_separator_status"], []).append(rec["complexity_class"])
    print("Coverage by separator status:")
    for status, classes in sorted(by_status.items()):
        print(f"  {status:<24}: {len(classes)} -- {', '.join(classes)}")
    print()

    # Class-usage frequency
    print("Class-usage frequency across complexity-class roster:")
    freq = {}
    for r in records:
        for c in r["classes_used"]:
            freq[c] = freq.get(c, 0) + 1
    total = len(records)
    for c in sorted(freq, key=lambda x: (-freq[x], x)):
        sub = ("A foundational" if c in FOUNDATIONAL
               else "P substrate-projection" if c in SUBSTRATE_PROJECTION
               else "D cascade-detection" if c in CASCADE_DETECTION
               else "M meta-cascade")
        bar = "#" * freq[c]
        print(f"  Class {c} ({sub:<24}): {freq[c]:>2}/{total}  {bar}")

    # Hurwitz-partition summary
    print()
    print("Hurwitz-partition usage:")
    foundational_used = sum(1 for r in records if any(c in FOUNDATIONAL for c in r["classes_used"]))
    projection_used = sum(1 for r in records if any(c in SUBSTRATE_PROJECTION for c in r["classes_used"]))
    detection_used = sum(1 for r in records if any(c in CASCADE_DETECTION for c in r["classes_used"]))
    meta_used = sum(1 for r in records if any(c in META_CASCADE for c in r["classes_used"]))
    print(f"  Foundational A:                 {foundational_used}/{total} ({100*foundational_used/total:.0f}%)")
    print(f"  Substrate-projection {{I,C,J}}:   {projection_used}/{total} ({100*projection_used/total:.0f}%)")
    print(f"  Cascade-detection {{D,E,F,G,K,L,M}}:{detection_used}/{total} ({100*detection_used/total:.0f}%)")
    print(f"  Meta-cascade {{B,H,N}}:            {meta_used}/{total} ({100*meta_used/total:.0f}%)")


if __name__ == "__main__":
    main()
