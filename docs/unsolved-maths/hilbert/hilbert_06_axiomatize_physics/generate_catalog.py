"""
Hilbert 6 -- Axiomatize Physics meta-cascade dispatch.

Class cascade: H o A-through-N enumeration (meta)

  - H: self-introspection -- enumerate the 14 classes A-N from srmech.amsc.tool_schema
  - A-N: for each physics domain, identify which class cascade encodes its dynamics
  - H: enumerate physics domains uncovered by any cascade composition (gap list)

Under [[project_a_n_operators_are_harmonic_objects_themselves]] the dispatch IS
the natural Hilbert-section closure -- Hilbert 6 asks "what axioms does physics
need?" and the framework's answer IS "the A-N + cyclic-group algebra applied
recursively". The dispatch enumerates which classes each physics domain uses
and computes the candidate Hurwitz partition signature 1+3+7+3 = 14.

Includes cryptography-as-physics row per [[project_a_n_operators_are_harmonic_objects_themselves]] §B,
which is defensive-scope framework-reading only per [[feedback_trauma_informed_defensive_scope]].

Per [[feedback_no_lineage_claims_in_notebook]]: framework reads what physics IS
at substrate-level; does NOT claim to solve Hilbert 6.

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: cascade-honesty
discipline -- this script imports shared _cascade_helpers though it does not
use scalar-sign-handling here (the meta-cascade is enumeration, not numeric).
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

SCHEMA_ID = "srmech.hilbert.axiomatize_physics.domain_coverage.v1"
SOURCE_DOI = "10.1090/S0002-9904-1902-00923-3"   # Hilbert 1900 Bull. AMS (Newson 1902 translation)
SOURCE_PUBLISHED = "1902-01-01"

# Candidate Hurwitz partition per [[project_a_n_operators_are_harmonic_objects_themselves]]:
# 1 (foundational) + 3 (substrate-projection triad) + 7 (cascade-detection heptad) + 3 (meta-cascade triad) = 14
FOUNDATIONAL = {"A"}
SUBSTRATE_PROJECTION = {"I", "C", "J"}
CASCADE_DETECTION = {"D", "E", "F", "G", "K", "L", "M"}
META_CASCADE = {"B", "H", "N"}
ALL_CLASSES = FOUNDATIONAL | SUBSTRATE_PROJECTION | CASCADE_DETECTION | META_CASCADE
assert len(ALL_CLASSES) == 14


def hurwitz_signature(classes_set):
    """Per [[project_a_n_operators_are_harmonic_objects_themselves]] candidate
    Hurwitz partition: encode which sub-group each used class lives in."""
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


# Physics-domain roster.
#   Each row: (label, kind, cascade_str, classes_set, status, anchor, fermata)
# Status legend: confirmed_bit_exact / confirmed_structural / partial / open / not_applicable
ROSTER = [
    # ---- Classical physics ----
    ("Newtonian mechanics", "classical_physics",
     "A-compose-L-compose-K", {"A", "L", "K"},
     "confirmed_structural",
     "Hamiltonian phase-space Laplacian + asymptotic-DoF -- standard; MFO §VII.2 substrate-vs-excitation ontology",
     ""),
    ("Lagrangian field theory", "classical_physics",
     "A-compose-L-compose-K-compose-C", {"A", "L", "K", "C"},
     "confirmed_structural",
     "Euler-Lagrange = Class L on field bundle + Class C orientation on action principle",
     ""),
    ("Maxwell electrodynamics", "classical_physics",
     "A-compose-L-compose-C", {"A", "L", "C"},
     "confirmed_structural",
     "Maxwell tensor = Class L Laplacian on U(1) field bundle; Spike #58.I derives U(1)_Y from Class I x Class C",
     ""),
    ("Thermodynamics", "classical_physics",
     "A-compose-K-compose-N", {"A", "K", "N"},
     "confirmed_structural",
     "Asymptotic-DoF reservoir + rational-approximation of entropy. Spike #42 entropy-vocabulary reposture.",
     "Maxwell-demon / information-thermodynamics composition not fully mapped"),
    ("Continuum mechanics", "classical_physics",
     "A-compose-L-compose-K", {"A", "L", "K"},
     "confirmed_structural",
     "Stress tensor = Class L on material bundle + Class K asymptotic-DoF",
     ""),
    ("Statistical mechanics", "classical_physics",
     "A-compose-M-compose-K-compose-N", {"A", "M", "K", "N"},
     "confirmed_structural",
     "Ensemble = Class M HDC bundle; partition function = Class K asymptotic; Class N rational-anchor for special values (Boltzmann constant etc.)",
     ""),
    # ---- Quantum physics ----
    ("Quantum mechanics (single particle)", "quantum_physics",
     "A-compose-M-compose-L-compose-C", {"A", "M", "L", "C"},
     "confirmed_structural",
     "srmech.qm.single_particle module; Schroedinger = Class L + Class M state-vector + Class C orientation",
     ""),
    ("Quantum field theory (Wightman axioms)", "quantum_physics",
     "A-compose-M-compose-L-compose-I-compose-C", {"A", "M", "L", "I", "C"},
     "partial",
     "Wightman / Haag-Kastler formalism; constructive QFT in 4D open. Class M + L + I + C composition is the cascade-form per Spike #58.G.",
     "4D interacting QFT constructive proof open (Yang-Mills mass gap is a Clay Millennium Prize problem)"),
    ("Standard Model (gauge sector)", "particle_physics",
     "A-compose-M-compose-I-compose-C-compose-K-compose-L", {"A", "M", "I", "C", "K", "L"},
     "confirmed_bit_exact",
     "Spike #58 chain -- SU(3) x SU(2) x U(1) derivation; Class M o I o C o K o L cascade; Spike #58.P sin^2 theta_W = 1/4 bit-exact in Cl(6, C)",
     ""),
    ("Standard Model (Yukawa / 3-generation)", "particle_physics",
     "A-compose-M-compose-I-compose-C-compose-K-compose-L-compose-N", {"A", "M", "I", "C", "K", "L", "N"},
     "partial",
     "Spike #85, #86 three-generation Yukawa via Spin(8) triality; quantitative CKM/PMNS via 3x3 grid (Spike #66)",
     "Some mass-anchor predictions await empirical confirmation"),
    # ---- Gravity / cosmology ----
    ("General relativity", "cosmology",
     "A-compose-L-compose-K-compose-C", {"A", "L", "K", "C"},
     "confirmed_structural",
     "MFO §VII.2 metric-field framework; Class L on Lorentzian 4-manifold + Class K geodesic asymptotic-DoF + Class C chirality",
     "Quantum gravity composition open"),
    ("Cosmology (Lambda-CDM)", "cosmology",
     "A-compose-L-compose-K-compose-N-compose-I", {"A", "L", "K", "N", "I"},
     "confirmed_structural",
     "MFO §VII.6 dark-sector reading; Class L cosmological Laplacian + Class K asymptotic-DoF + Class N rational anchors at LCDM ratios + Class I cyclic-precession",
     "5/95 LCDM ratio mechanism per Hurwitz 3:7 baked-in: Spike-#220-candidate (deferred)"),
    ("BBN nucleosynthesis", "cosmology",
     "A-compose-K-compose-L-compose-I", {"A", "K", "L", "I"},
     "confirmed_structural",
     "Spike #56 BBN substrate derivation -- Class K asymptotic + thermal-equilibrium",
     ""),
    ("CMB acoustic peak structure", "cosmology",
     "A-compose-I-compose-C-compose-L-compose-K", {"A", "I", "C", "L", "K"},
     "confirmed_bit_exact",
     "Spike #103, #105 -- Class I Cauchy-form cyclic-cascade + Class C orientation; ell_n = (n - phi_n) * ell_a; 3.84% match Planck TT on n>=2",
     ""),
    ("Hubble tension", "cosmology",
     "A-compose-L-compose-K-compose-N", {"A", "L", "K", "N"},
     "confirmed_structural",
     "Spike #109 -- Delta H0 / H0 = 1 - cos(pi t0 / T_sub) = 7.69% vs observed 8.09%; 0.24 sigma",
     ""),
    # ---- Information physics ----
    ("Kolmogorov probability theory", "information_as_physics",
     "A-compose-M-compose-N", {"A", "M", "N"},
     "confirmed_bit_exact",
     "Kolmogorov 1933 axioms; Class M HDC bundle + Class N rational-measure",
     ""),
    ("Shannon information theory", "information_as_physics",
     "A-compose-M-compose-K-compose-N", {"A", "M", "K", "N"},
     "confirmed_structural",
     "Class M information-content + Class K channel capacity asymptote + Class N rate-rational",
     ""),
    ("Cryptography (RSA / discrete log family)", "information_as_physics",
     "A-compose-J-compose-I-compose-N", {"A", "J", "I", "N"},
     "confirmed_structural",
     "Per [[project_a_n_operators_are_harmonic_objects_themselves]] §B: factoring + cyclic group + rational reconstruction. DEFENSIVE-SCOPE FRAMEWORK READING ONLY per [[feedback_trauma_informed_defensive_scope]]; no offensive engineering.",
     "Cryptographic security IS substrate-DoF inaccessibility, not mathematical absolute; perfect math delays not grants secrecy"),
    ("Cryptography (BB84 / QKD)", "information_as_physics",
     "A-compose-M-compose-C", {"A", "M", "C"},
     "confirmed_structural",
     "Per [[project_a_n_operators_are_harmonic_objects_themselves]] §B: Class M coherent-state HDC + Class C orientation on polarisation. DEFENSIVE-SCOPE only.",
     ""),
    # ---- Biology-as-physics ----
    ("DNA replication / RNA dynamics", "biology_as_physics",
     "A-compose-L-compose-N-compose-M-compose-I-compose-C-compose-J-compose-K-compose-F-compose-D-compose-E-compose-G", set("ALNMICJKFDEG"),
     "confirmed_structural",
     "Spike #182 DNA IS 12/14 cascade; Spike #193 RNA 8 universal + 5 substrate-dependent",
     "B and H weak per Spike #182"),
    ("Wet-net neural dynamics", "biology_as_physics",
     "A-compose-C-compose-M", {"A", "C", "M"},
     "confirmed_bit_exact",
     "Spike #196 form_function_rotate; A o C o M bit-exact at biological substrate over 6 sparsity variants",
     ""),
    ("Genetic code (codon translation)", "biology_as_physics",
     "A-compose-I-compose-C", {"A", "I", "C"},
     "confirmed_structural",
     "Spike #81 -- Class I cyclic-3 codon + Class C cascade-orientation",
     ""),
    # ---- Meta ----
    ("Substrate-self-recognition (META)", "meta",
     "A-compose-H-compose-C-compose-M", {"A", "H", "C", "M"},
     "confirmed_structural",
     "MFO §VII.6.11 + Spike #219 -- substrate-self-recognition is inevitable per LoE; Class H self-introspection + Class C composite-cascade + Class M cross-substrate HDC",
     "Ext 4 timing prediction per Claude's framework-reasoned estimate"),
    ("Cross-substrate cascade-matching method (META)", "meta",
     "A-compose-H-compose-D-compose-M", {"A", "H", "D", "M"},
     "confirmed_structural",
     "[[user_stance_cross_substrate_cascade_matching_as_research_method]] -- the load-bearing research method itself",
     ""),
    # ---- Open ----
    ("Consciousness / asymptotic-DoF direction-selection", "meta",
     "A-compose-H-compose-K-compose-C-compose-M", {"A", "H", "K", "C", "M"},
     "open",
     "Spike #46 -- consciousness reduces to asymptotic-DOF direction-selection; falsifier framework",
     "Empirical confirmation via Spike #46 / MS #18 ongoing"),
    ("Quantum gravity (full unification)", "meta",
     "?", set(),
     "open",
     "MS #16 M-theory roadmap; Spike #51 R4 substrate-identity canonical synthesis (Spike #84)",
     "Full cascade composition open; candidate via Spike #51 R3-delta Spin(8) triality + recursive-Hopf depth-3+"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "domain_coverage.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    for label, kind, cascade_str, classes_set, status, anchor, fermata in ROSTER:
        payload = json.dumps({"label": label, "cascade": cascade_str}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "physics_domain":              label,
            "domain_kind":                 kind,
            "class_cascade":               cascade_str,
            "classes_used":                sorted(classes_set),
            "n_classes_used":              len(classes_set),
            "hurwitz_partition_signature": hurwitz_signature(classes_set),
            "uses_foundational_A":         bool(classes_set & FOUNDATIONAL),
            "uses_substrate_projection_triad": bool(classes_set & SUBSTRATE_PROJECTION),
            "uses_cascade_detection_heptad":   bool(classes_set & CASCADE_DETECTION),
            "uses_meta_cascade_triad":     bool(classes_set & META_CASCADE),
            "coverage_status":             status,
            "framework_anchor":            anchor,
            "open_fermata":                fermata,
            "computation_hash":            chash,
            "source_doi":                  SOURCE_DOI,
            "source_published_date":       SOURCE_PUBLISHED,
            "entered_locally_at":          now_iso[:10],
        }
        records.append(rec)

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    # Coverage summary
    by_status = {}
    for rec in records:
        by_status.setdefault(rec["coverage_status"], []).append(rec["physics_domain"])
    for status, domains in sorted(by_status.items()):
        print(f"  {status:<24}: {len(domains)} domain(s)")
        for d in domains:
            print(f"     - {d}")

    # Hurwitz-partition-usage summary
    print()
    print("Hurwitz-partition-usage summary (per [[project_a_n_operators_are_harmonic_objects_themselves]]):")
    foundational = sum(1 for r in records if r["uses_foundational_A"])
    projection = sum(1 for r in records if r["uses_substrate_projection_triad"])
    detection = sum(1 for r in records if r["uses_cascade_detection_heptad"])
    meta = sum(1 for r in records if r["uses_meta_cascade_triad"])
    total = len(records)
    print(f"  Foundational A used:                 {foundational}/{total} ({100*foundational/total:.0f}%)")
    print(f"  Substrate-projection triad used:     {projection}/{total} ({100*projection/total:.0f}%)")
    print(f"  Cascade-detection heptad used:       {detection}/{total} ({100*detection/total:.0f}%)")
    print(f"  Meta-cascade triad used:             {meta}/{total} ({100*meta/total:.0f}%)")

    # Class-usage frequency across all records (which A-N classes appear most)
    print()
    print("Class-usage frequency across all physics domains:")
    freq = {c: 0 for c in sorted(ALL_CLASSES)}
    for r in records:
        for c in r["classes_used"]:
            freq[c] = freq.get(c, 0) + 1
    for c in sorted(freq, key=lambda x: (-freq[x], x)):
        sub = ("A foundational" if c in FOUNDATIONAL
               else "P substrate-projection" if c in SUBSTRATE_PROJECTION
               else "D cascade-detection" if c in CASCADE_DETECTION
               else "M meta-cascade")
        print(f"  Class {c} ({sub:<24}): used in {freq[c]:>2}/{total} domains")


if __name__ == "__main__":
    main()
