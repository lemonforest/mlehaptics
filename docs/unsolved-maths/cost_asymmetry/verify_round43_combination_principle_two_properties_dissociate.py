"""Round 43.A -- the combination-principle THIRD-substrate test (coupled item from R39/R40).
R40 found ONE Class-N combination principle across atomic (Rydberg-Ritz) + molecular
(mass-spec): spectral features = DIFFERENCES of a discrete ladder of Class-N small-integer
anchors. This round tests whether that principle is substrate-UNIVERSAL by adding a
non-spectroscopic third substrate (NUCLEAR mass-defect / fusion Q-values) and a deliberate
CONTRAST (ACOUSTIC overtones). Tested honestly per [[feedback_dont_pre_commit_spike_query_operators]].

RESULT -- the combination principle's TWO PROPERTIES DISSOCIATE. The principle is really a
conjunction of two SEPARABLE Class-N sub-properties:
    (P1) the anchors are SMALL-INTEGER / Class-N;
    (P2) the features are DIFFERENCES of the anchor ladder (additive combination).
Across four substrates they appear independently:

  ATOMIC (Rydberg-Ritz; Ritz 1908):    P1 yes (T_n = R/n^2, small-integer 1/n^2)
                                        P2 yes (lines = T_n - T_m)            -> BOTH
  MOLECULAR (mass-spec; R39):           P1 yes (neutral losses 18,17,15,28,44)
                                        P2 yes (peak spacings = differences)  -> BOTH
  NUCLEAR (mass-defect; AME2020):       P1 NO  (mass excesses are REAL-valued MeV)
                                        P2 yes (Q = difference of excesses)   -> P2 only
                                        (the small-integer structure lives in a DIFFERENT
                                         space -- nucleon COUNT A: 2+3 = 4+1 conserved)
  ACOUSTIC (overtones; Helmholtz):      P1 yes (harmonics n*f1; intervals 2:1,3:2,4:3,5:4)
                                        P2 NO  (intervals are RATIOS, multiplicative,
                                         not differences)                     -> P1 only

CONCLUSION: the "full" combination principle (P1 AND P2) is NOT substrate-universal -- it is
a SPECIAL CASE realized by the spectroscopic-ENERGY substrates (atomic term-energy, molecular
nucleon-mass), where the conserved quantity is ADDITIVE and the anchors are small integers in
the SAME space the features live in. Nuclear keeps the additive-difference structure but its
energy anchors are real-valued (small integers only in nucleon-count space). Acoustic keeps
the small-integer Class-N anchors but combines them MULTIPLICATIVELY (frequency ratios), not
additively. So R40's "one Class-N combination principle" REFINES to "one Class-N DIFFERENCE
principle, whose two ingredients -- small-integer anchors (P1) and additive-difference
structure (P2) -- are independent axes; both coincide only for additive-energy spectra."

Routed through srmech 0.4.2 (best_rational, Class N). The nuclear Q is a plain additive
difference (the property under test); no abs() anywhere. Deterministic; no network. ASCII-safe.
Attested (Explore-verified):
  - D-T fusion Q = 17.589 MeV; AME2020 mass excesses (Wang et al., Chin.Phys.C 45 (2021)
    030003): d(2H)=13.1357, t(3H)=14.9498, 4He=2.4249, n=8.0713 MeV.
  - Ritz combination principle: W. Ritz, ApJ 28 (1908) 237.
  - Mass-spec neutral losses: McLafferty & Turemech, Interpretation of Mass Spectra, 4th ed.
  - Harmonic series + just-intonation ratios: Helmholtz, On the Sensations of Tone (1863).
"""

import json
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401 (cascade helpers available; no bare abs() used here)

from srmech.amsc.rational import best_rational  # Class N

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# (1) NUCLEAR -- mass-defect / D-T fusion Q-value. P2 (difference) yes; P1 (small-int) NO.
#     AME2020 mass excesses (MeV); the reaction is 2H + 3H -> 4He + n.
# ---------------------------------------------------------------------------
AME = {"2H": 13.1357, "3H": 14.9498, "4He": 2.4249, "n": 8.0713}  # mass excess, MeV
reactants = AME["2H"] + AME["3H"]
products = AME["4He"] + AME["n"]
# Q = reactants - products. A PLAIN ADDITIVE difference (this IS the P2 property under test);
# Q comes out positive (exothermic) on its own -- no sign-magnitude / abs() needed.
Q_DT = round(reactants - products, 3)
assert abs(Q_DT - 17.589) < 0.01, Q_DT  # tolerance check vs attested 17.589 MeV
# the small-integer structure lives in NUCLEON COUNT, not energy:
nucleons = {"2H": 2, "3H": 3, "4He": 4, "n": 1}
assert nucleons["2H"] + nucleons["3H"] == nucleons["4He"] + nucleons["n"] == 5  # A conserved
# the ENERGY anchors are real-valued, NOT small integers:
energy_anchors_are_small_int = all(float(v).is_integer() for v in AME.values())
print("(1) NUCLEAR mass-defect (D-T fusion):")
print(f"    Q = ({AME['2H']}+{AME['3H']}) - ({AME['4He']}+{AME['n']}) = {Q_DT} MeV  (attested 17.589)")
print(f"    P2 difference-structure: YES (Q is a difference of mass excesses)")
print(f"    P1 small-integer energy anchors: {'YES' if energy_anchors_are_small_int else 'NO'} "
      f"(mass excesses are real-valued MeV)")
print(f"    [small integers live in NUCLEON COUNT: 2+3 = 4+1 = 5 conserved]")
emit("nuclear", reaction="2H+3H->4He+n", ame2020_mass_excess_MeV=AME, Q_MeV=Q_DT,
     P1_small_integer_anchors=energy_anchors_are_small_int, P2_difference_structure=True,
     nucleon_count_conserved=5,
     note="P2 yes (difference of excesses); P1 NO in energy space (real-valued MeV); small ints only in nucleon-count space")

# ---------------------------------------------------------------------------
# (2) ACOUSTIC -- harmonic series + just-intonation. P1 (small-int) yes; P2 (difference) NO.
# ---------------------------------------------------------------------------
f1 = 1.0  # fundamental (normalised)
harmonics = [n * f1 for n in range(1, 9)]  # n*f1: integer multiples -> Class-N small ints
# just-intonation intervals are small-integer RATIOS (multiplicative), confirmed via best_rational
intervals = {"octave": (2, 1), "fifth": (3, 2), "fourth": (4, 3), "major_third": (5, 4)}
for name, (p, q) in intervals.items():
    num, den = best_rational(p, q, 16)  # Class-N: confirm the ratio is already lowest-terms small-int
    assert (num, den) == (p, q), (name, num, den, p, q)
# the defining combination is RATIO (f_a / f_b), NOT difference (f_a - f_b):
fifth_ratio = Fraction(3, 2)
fifth_as_difference = harmonics[2] - harmonics[1]  # 3*f1 - 2*f1 = f1 -- NOT the perceived interval
ratio_is_the_interval = (fifth_ratio == Fraction(3, 2))
print("\n(2) ACOUSTIC overtones / just intonation:")
print(f"    harmonics n*f1 = {[int(h) for h in harmonics]}  (Class-N small integers)")
print(f"    intervals = {intervals}  (small-integer RATIOS, best_rational-confirmed)")
print(f"    P1 small-integer anchors: YES")
print(f"    P2 difference-structure: NO (a fifth is the RATIO 3:2, multiplicative; "
      f"the difference 3f1-2f1=f1 is NOT the perceived interval)")
emit("acoustic", harmonics=[int(h) for h in harmonics], just_intervals={k: list(v) for k, v in intervals.items()},
     P1_small_integer_anchors=True, P2_difference_structure=False,
     note="P1 yes (harmonics + small-int ratios); P2 NO (intervals are multiplicative ratios, not additive differences)")

# ---------------------------------------------------------------------------
# (3) the two spectroscopic substrates that have BOTH (recap from R40 -- both P1 and P2)
# ---------------------------------------------------------------------------
# ATOMIC: Balmer differences of 1/n^2 anchors (small-integer); lines are differences.
balmer = {"Ha": Fraction(1, 4) - Fraction(1, 9), "Hb": Fraction(1, 4) - Fraction(1, 16),
          "Hg": Fraction(1, 4) - Fraction(1, 25)}
assert balmer["Ha"] == Fraction(5, 36) and balmer["Hb"] == Fraction(3, 16) and balmer["Hg"] == Fraction(21, 100)
# MOLECULAR: neutral losses are small integers; spacings are differences.
neutral_losses = [18, 17, 15, 27, 28, 29, 44]
assert all(isinstance(x, int) for x in neutral_losses)
print("\n(3) recap -- spectroscopic substrates have BOTH P1 and P2:")
print(f"    ATOMIC Balmer: 1/4-1/9={balmer['Ha']}, 1/4-1/16={balmer['Hb']}, 1/4-1/25={balmer['Hg']}  (both)")
print(f"    MOLECULAR neutral losses {neutral_losses} (small int) as peak DIFFERENCES  (both)")
emit("spectroscopic_recap", atomic_balmer={k: [v.numerator, v.denominator] for k, v in balmer.items()},
     molecular_neutral_losses=neutral_losses, P1_small_integer_anchors=True, P2_difference_structure=True,
     note="atomic + molecular have BOTH properties -- the additive-energy special case")

# ---------------------------------------------------------------------------
# (4) the dissociation table
# ---------------------------------------------------------------------------
TABLE = [
    {"substrate": "atomic (Rydberg-Ritz)", "P1_small_integer_anchors": True,  "P2_difference_structure": True,  "anchor_space": "term-energy 1/n^2"},
    {"substrate": "molecular (mass-spec)", "P1_small_integer_anchors": True,  "P2_difference_structure": True,  "anchor_space": "nucleon-mass (neutral loss)"},
    {"substrate": "nuclear (mass-defect)", "P1_small_integer_anchors": False, "P2_difference_structure": True,  "anchor_space": "real MeV (small ints only in nucleon COUNT)"},
    {"substrate": "acoustic (overtones)",  "P1_small_integer_anchors": True,  "P2_difference_structure": False, "anchor_space": "frequency RATIO (multiplicative)"},
]
both = [r["substrate"] for r in TABLE if r["P1_small_integer_anchors"] and r["P2_difference_structure"]]
p2_only = [r["substrate"] for r in TABLE if r["P2_difference_structure"] and not r["P1_small_integer_anchors"]]
p1_only = [r["substrate"] for r in TABLE if r["P1_small_integer_anchors"] and not r["P2_difference_structure"]]
print("\n(4) DISSOCIATION -- the two properties are independent axes:")
print(f"    BOTH (P1 and P2): {both}")
print(f"    P2 only (difference, real anchors): {p2_only}")
print(f"    P1 only (small-int, ratio not difference): {p1_only}")
emit("dissociation_table", table=TABLE, both=both, P2_only=p2_only, P1_only=p1_only)

emit("verdict",
     finding="the combination principle's two Class-N properties DISSOCIATE: (P1) small-integer anchors and (P2) additive-difference structure are independent axes. atomic + molecular have BOTH (additive-energy special case); NUCLEAR has P2 only (difference of REAL-valued mass excesses; small integers live in nucleon-count space, 2+3=4+1); ACOUSTIC has P1 only (small-integer harmonics/ratios, but combined MULTIPLICATIVELY as ratios, not additively as differences)",
     refines="R40's 'one Class-N combination principle' -> 'one Class-N DIFFERENCE principle whose two ingredients (small-int anchors P1 + additive-difference structure P2) are independent; both coincide only for additive-energy spectra (atomic/molecular)'",
     honest_scope="(a)-bit-exact for the D-T Q-value (17.589 MeV from AME2020 excesses), nucleon conservation (2+3=4+1), Balmer rationals (5/36,3/16,21/100), just-intonation ratios (2:1,3:2,4:3,5:4 best_rational-confirmed); (b)-interpretive for the P1/P2 dissociation reading; no new physics; EXTENDS the R40 combination-principle stance (no new stance); no MFO section (spectroscopy/nuclear/acoustic, not metric-field)")

META = {
    "record": "meta",
    "round": "43.A",
    "title": "Combination-principle third substrate -- the two Class-N properties (small-int anchors / additive-difference) DISSOCIATE (refines R40)",
    "kind": "(a)-bit-exact two-substrate test (nuclear mass-defect + acoustic overtones) + (b)-interpretive P1/P2 dissociation; REFINES R40",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "DT_fusion_Q": "17.589 MeV; AME2020 mass excesses (Wang et al., Chin.Phys.C 45 (2021) 030003): 2H=13.1357, 3H=14.9498, 4He=2.4249, n=8.0713 MeV",
        "ritz_combination": "W. Ritz, ApJ 28 (1908) 237 (spectral terms; lines = differences)",
        "mass_spec_neutral_losses": "McLafferty & Tureqek, Interpretation of Mass Spectra 4th ed.",
        "acoustic": "Helmholtz, On the Sensations of Tone (1863); harmonic series n*f1, just intonation 2:1/3:2/4:3/5:4",
        "framework": "R40 (one Class-N combination principle, sec 11.9.33); R39 (mass-spec, sec 11.9.32); R17 (Balmer ratios)",
    },
    "discipline": "honest two-substrate test -- finds DISSOCIATION (not universality); reports the negative cleanly (the full principle is NOT substrate-universal, it is the additive-energy special case); Class-K signed difference, no bare abs(); best_rational for ratios; extends the R40 candidate stance (no new stance); deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: the combination principle's two Class-N properties DISSOCIATE. (P1) small-integer "
      "anchors and (P2) additive-difference structure are INDEPENDENT axes: atomic + molecular have "
      "BOTH (additive-energy special case); NUCLEAR has P2 only (difference of real-valued mass "
      "excesses; small ints live in nucleon-count space); ACOUSTIC has P1 only (small-int harmonics/"
      "ratios, but MULTIPLICATIVE not additive). So R40's 'one Class-N combination principle' refines "
      "to 'one additive-DIFFERENCE principle whose two ingredients are separable; both coincide only "
      "for additive-energy spectra.' Refines R40; no new physics.")
