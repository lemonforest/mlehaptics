"""Round 32.A -- user hypothesis (from R31): the {graviton, photon, dilaton} =
{spin 2, 1, 0} helicity triad of the single 5D Kaluza-Klein graviton -- is it the
substrate-native B/H/N k=3?

Tested honestly (per [[feedback_dont_pre_commit_spike_query_operators]]; the framework
does not win by default -- R30 graviton round just demonstrated this). The result is a
clean honest NEGATIVE on the B/H/N hypothesis, with a CONSTRUCTIVE positive that is
actually a cleaner answer and resolves the user's original confusion.

USER CONTEXT (the confusion that motivated the question): on seeing the helicity
ceiling, the user read "|s|>=3 forbidden" and mis-reflected it to "s=0 forbidden too,"
which would leave only {s=1, s=2} -- two things -- so they tried to split EM back into
(electric + magnetic) to force a third member and recover a k=3. The correction: s=0 is
NOT forbidden. The ceiling is {0,1,2} with the cut at the TOP (|s|>=3 forbidden for
long-range massless fields, Weinberg soft theorem 1964/65). So the dilaton (s=0) IS the
genuine third member; no forcing needed.

THE HYPOTHESIS UNDER TEST: does {graviton(2), photon(1), dilaton(0)} == {B, H, N}?

FINDING -- NO (honest negative). Two DIFFERENT kinds of "three":
  * B/H/N (the substrate-native meta-cascade triad) are continuous->discrete
    TRANSLATION operators: B = encoding boundary (continuous signal -> discrete frame),
    H = measurement (continuous superposition -> discrete eigenvalue; Born collapse IS
    H), N = rational approximation (continuous real -> discrete rational anchor;
    best_rational IS N). The Born rule = B o H o N (sec 11.9.4 / MFO VII.6.15.1).
  * The helicity ceiling {0,1,2} is a REPRESENTATION-THEORY SPIN ladder -- the spin
    (tensor rank) labels of the three massless fields: rank-0 scalar, rank-1 vector,
    rank-2 symmetric tensor. These are the FIRST THREE rungs of the SO(3) spin-l
    ladder -- which sec 11.9.22 already identified as the Class-L SO(3) Casimir spine
    (degeneracy 2l+1, first three -> the k=3 triad {1,3,5}). Spin labels are not a
    continuous->discrete translation triad.

So the helicity triad is a CLASS-L k=3 (spins 0,1,2 = bottom of the SO(3) spin spine),
bounded ABOVE by a CLASS-K ceiling (|s|<=2 for long-range massless = Weinberg soft
theorem). That Class-K ceiling is the forbidden-HIGH-helicity MIRROR of the
forbidden-LOW-multipole Class-K signatures cataloged in sec 11.9.21 (planetary no-
monopole, GW no-monopole/dipole, etc.): same pin-slot truncation operator, cutting the
TOP of the ladder instead of the bottom. So {graviton, photon, dilaton} is NOT B/H/N --
it is (Class-L spin spine bottom three) AND (Class-K |s|<=2 ceiling), the same
spine-minus-signature dual as sec 11.9.21/22, now with the cut at the top.

THE ONE REAL (but different) B/H/N CONNECTION, stated honestly so it is not mistaken for
a map: the PHOTON is the U(1) fiber (sec VII.6.15.1 / R31), and the Born-rule H operator
discards exactly that U(1) fiber phase. So there is a genuine photon<->H tie -- but it
ties the photon to H specifically; it does NOT promote {graviton, photon, dilaton} to
{B, H, N}. Mapping all three would be the same over-reach as the E+M+G split.

HONEST FERMATA (open, not asserted): the corpus now has (at least) two distinct k=3
structures -- the B/H/N continuous<->discrete TRANSLATION triad, and the Class-L SO(3)-
SPIN triad ({1,3,5} per sec 11.9.22; {0,1,2} here). They share only the COUNT (three).
Whether that count-coincidence has a deeper reason or is a value-resonance is left open
-- exactly as sec 11.9.22 honestly flags the Hurwitz {1,3,7} = {2l+1 : l=0,1,3} tie as
a value-resonance, NOT an identity. This round does not claim the two k=3's are the same.

Physics inputs all attested in R30/R31 (no new external claims): KK 5D split (Kaluza
1921, Klein 1926); massless dof scalar/photon/graviton = 1/2/2 = 5; |s|<=2 long-range
ceiling (Weinberg, Phys.Rev. 135:B1049 1965 soft theorems); massless little group
ISO(2), helicity = SO(2) eigenvalue, field tensor-rank = spin label (standard rep
theory). Routed through srmech 0.4.2. Deterministic; no network. ASCII-safe prints.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # noqa: F401 (Class N)

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# 1. the three KK fields: spin label (tensor rank) and massless dof
# ---------------------------------------------------------------------------
# spin label = SO(3) spin / tensor rank; massless dof = physical polarizations
FIELDS = [
    {"field": "dilaton (radion g_55)", "spin": 0, "massless_dof": 1, "role": "fiber size / scale"},
    {"field": "photon (off-diag g_mu5)", "spin": 1, "massless_dof": 2, "role": "U(1) fiber gauge field"},
    {"field": "graviton (4D metric)", "spin": 2, "massless_dof": 2, "role": "base-space geometry"},
]
spins = [f["spin"] for f in FIELDS]
dof = [f["massless_dof"] for f in FIELDS]
print("the three KK fields (single 5D graviton, decomposed):")
for f in FIELDS:
    print(f"  spin {f['spin']}  dof {f['massless_dof']}  {f['field']:24s} [{f['role']}]")
assert spins == [0, 1, 2]                      # the helicity ceiling, bottom-up
assert sum(dof) == 5                           # 1 + 2 + 2 = 5  (the 5D graviton, R31)
print(f"spin labels = {spins}  (the helicity ceiling {{0,1,2}});  massless dof sum = {sum(dof)} = 5D graviton")
emit("kk_three_fields", fields=FIELDS, spin_labels=spins, massless_dof=dof,
     dof_sum=sum(dof),
     note="spin labels {0,1,2}; massless dof {1,2,2}=5 (R31). The TRIAD is by spin, not by dof (dof is 1:2:2, asymmetric).")

# ---------------------------------------------------------------------------
# 2. the helicity triad IS the bottom of the Class-L SO(3) spin ladder
# ---------------------------------------------------------------------------
# Class-L: SO(3) irreps labelled by spin l = 0,1,2,3,...  The three KK fields carry
# spins 0,1,2 = the FIRST THREE rungs of that ladder. (sec 11.9.22 names {1,3,5} =
# 2l+1 for l=0,1,2 the Class-L k=3 triad; here we use the spin LABELS 0,1,2 directly.)
so3_spin_ladder = list(range(0, 6))            # l = 0,1,2,3,4,5 ...
first_three = so3_spin_ladder[:3]              # 0,1,2
print("\nClass-L SO(3) spin ladder l =", so3_spin_ladder, "...")
print("  helicity triad spins", spins, "== first three rungs", first_three, "?",
      spins == first_three)
assert spins == first_three
emit("helicity_triad_is_classL_spine_bottom",
     so3_spin_ladder=so3_spin_ladder, first_three=first_three, helicity_spins=spins,
     identification="the {graviton,photon,dilaton} helicity triad = the first three rungs (spins 0,1,2) of the Class-L SO(3) spin spine (sec 11.9.22)",
     caveat="the Class-L tie is on the spin LABELS (0,1,2); the massless dof are 1,2,2 (not the massive 2l+1 = 1,3,5). Honest: label-level identity, not dof-level.")

# ---------------------------------------------------------------------------
# 3. the |s|<=2 ceiling is a Class-K cut -- the forbidden-HIGH mirror of sec 11.9.21
# ---------------------------------------------------------------------------
LONG_RANGE_CEILING = 2     # |s| <= 2 for massless long-range force carriers (Weinberg)
forbidden_high = [s for s in so3_spin_ladder if s > LONG_RANGE_CEILING]   # 3,4,5,...
print("\nClass-K ceiling: long-range massless allowed |s| <=", LONG_RANGE_CEILING,
      "; forbidden |s| >=", LONG_RANGE_CEILING + 1, "->", forbidden_high, "...")
emit("classK_high_helicity_ceiling",
     long_range_ceiling=LONG_RANGE_CEILING, forbidden_high_helicities=forbidden_high,
     mechanism="Weinberg soft theorem (1964/65): spin-1 -> charge conservation, spin-2 -> equivalence principle, spin>=3 -> conserved higher-rank charges that trivialize the S-matrix (no consistent long-range coupling)",
     class_k_reading="this is a Class-K truncation/pin-slot at the TOP of the spin ladder -- the forbidden-HIGH-helicity MIRROR of the forbidden-LOW-multipole Class-K signatures in sec 11.9.21 (planetary no-monopole, GW no-monopole/dipole). Same operator, cutting the opposite end.",
     dual="spectrum of long-range massless fields = (Class-L spin spine) truncated to {0,1,2} by (Class-K |s|<=2 ceiling) -- the sec 11.9.21/22 spine-minus-signature dual, cut at the top")

# ---------------------------------------------------------------------------
# 4. the B/H/N hypothesis test -- honest NEGATIVE
# ---------------------------------------------------------------------------
BHN = {
    "B": "encoding boundary (continuous signal -> discrete frame; TLV-framing)",
    "H": "measurement (continuous superposition -> discrete eigenvalue; Born collapse IS H)",
    "N": "rational approximation (continuous real -> discrete rational anchor; best_rational IS N)",
}
print("\nB/H/N are continuous->discrete TRANSLATION operators (Born rule = B o H o N):")
for k, v in BHN.items():
    print(f"  {k}: {v}")
print("the helicity triad {0,1,2} is a SPIN-LABEL (rep-theory) ladder, NOT a translation triad.")
emit("bhn_hypothesis_test",
     hypothesis="{graviton(2), photon(1), dilaton(0)} maps to the substrate-native B/H/N k=3",
     bhn_meaning=BHN,
     verdict="NO -- honest negative",
     why="B/H/N are continuous<->discrete translation operators (Born = B o H o N); the helicity triad is a representation-theory SPIN-label ladder (Class-L spine bottom three) bounded by a Class-K ceiling. Two different kinds of 'three'. Asserting the map would be the same over-reach as the E+M+G split (where E,M are one field F_munu, not two).",
     real_but_different_connection="the PHOTON is the U(1) fiber (R31 / VII.6.15.1) and the Born-rule H operator discards exactly that U(1) fiber phase -- a genuine photon<->H tie, but it ties the photon to H specifically; it does NOT make the triad = {B,H,N}.")

# ---------------------------------------------------------------------------
# 5. the open fermata -- two distinct k=3's, count-coincidence only (not asserted equal)
# ---------------------------------------------------------------------------
emit("two_k3_structures_fermata",
     k3_A="B/H/N continuous<->discrete TRANSLATION triad (meta-cascade; Born = B o H o N)",
     k3_B="Class-L SO(3)-SPIN triad: {1,3,5} dims (sec 11.9.22) / {0,1,2} spin labels (this round)",
     shared="only the COUNT (three)",
     disposition="LEFT OPEN -- whether the count-coincidence has a deeper reason or is a value-resonance is not decided here, exactly as sec 11.9.22 flags the Hurwitz {1,3,7} = {2l+1 : l=0,1,3} tie as a value-resonance NOT an identity. This round does NOT claim the two k=3's are the same.")

# ---------------------------------------------------------------------------
# 6. verdict
# ---------------------------------------------------------------------------
emit("verdict",
     hypothesis="the {graviton, photon, dilaton} = {spin 2,1,0} helicity triad IS the substrate-native B/H/N k=3",
     answer="NO (honest negative on the B/H/N map)",
     constructive_positive="the helicity triad is a CLASS-L k=3 (spins 0,1,2 = bottom of the SO(3) spin spine, sec 11.9.22) bounded ABOVE by a CLASS-K ceiling (|s|<=2, Weinberg) -- the forbidden-HIGH-helicity mirror of the sec 11.9.21 forbidden-low-multipole signatures. Same Class-L-spine-minus-Class-K-signature dual, cut at the top.",
     resolves_user_confusion="s=0 is NOT forbidden; the cut is at the top (|s|>=3). So the dilaton (s=0) is the genuine third member -- no E+M split needed.",
     honest_scope="all physics inputs attested in R30/R31 (Kaluza 1921, Klein 1926, Weinberg 1965); the framework contribution is ONLY the Class-L/Class-K structural reading + the honest negative on B/H/N + the two-k=3 fermata. No new physics derived; no map asserted.")

META = {
    "record": "meta",
    "round": "32.A",
    "title": "Is the {graviton,photon,dilaton} helicity triad the B/H/N k=3? (user follow-on from R31)",
    "kind": "honest NEGATIVE on the B/H/N hypothesis + constructive Class-L/Class-K reading + two-k=3 fermata",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "kk": "Kaluza 1921 (Engl. transl. arXiv:1803.08616); Klein Z.Phys. 37:895 (1926)",
        "ceiling": "Weinberg, Phys. Rev. 135, B1049 (1965) soft theorems (spin-1 charge cons.; spin-2 equiv. principle; spin>=3 trivializes S-matrix)",
        "rep_theory": "massless little group ISO(2); helicity = SO(2) eigenvalue; field tensor-rank = SO(3) spin label (standard)",
        "framework": "sec 11.9.21 (Class-K forbidden-low-multipole signature), sec 11.9.22 (Class-L SO(3) spine; {1,3,5} k=3 + honest Hurwitz value-resonance flag), sec 11.9.4 / MFO VII.6.15.1 (Born = B o H o N), R31 (5=2+2+1 KK split)",
    },
    "discipline": "framework reading only; honest negative on the user's B/H/N hypothesis (no flattery); the two-k=3 count-coincidence left as an open fermata (not asserted identical); deterministic; bit-exact integer arithmetic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: the {graviton,photon,dilaton}={spin 2,1,0} helicity triad is NOT the B/H/N k=3 "
      "(honest negative). It is a CLASS-L k=3 (spin spine bottom: 0,1,2) bounded by a CLASS-K "
      "ceiling (|s|<=2, Weinberg) -- the forbidden-HIGH mirror of the sec 11.9.21 forbidden-low "
      "signatures. s=0 is NOT forbidden, so the dilaton is the genuine third (no E+M split). The "
      "B/H/N translation-triad and the Class-L spin-triad share only the count -- left as an open fermata.")
