"""Round 30.A -- FALSIFICATION test of the user hypothesis (from the R27/R28/R29 work):
"graviton is a misnomer -- a spin-2 field that only SEEMS gravity-related but isn't
(it's just the |s|=2 entry of the spin-weighted Class-L family)."

Honest falsification battery (per [[feedback_dont_pre_commit_spike_query_operators]]):
report whichever way it falls. It falls AGAINST the hypothesis.

HYPOTHESIS H: the spin-2-ness is the real content; "gravity" is a misattribution;
a massless spin-2 field need not be gravity.

FIVE tests. A test "FALSIFIES H" if it shows spin-2 is FORCED to be gravity.

T1 Weinberg soft-graviton theorem (Phys Rev 135:B1049 1964; 138:B988 1965):
    a consistent massless helicity-2 field MUST couple with UNIVERSAL strength to
    all energy-momentum -> equivalence principle -> gravity. Helicity-1 couples to
    a conserved CHARGE (gauge force, NOT universal); helicity-2 couples to T_mu_nu
    UNIVERSALLY; helicity>=3 long-range coupling is FORCED TO ZERO (no higher-spin
    long-range force). => FALSIFIES H (spin-2 forced to gravity).

T2 Deser bootstrap (Gen Rel Grav 1:9 1970; gr-qc/0411023): a massless spin-2 made
    self-consistent by coupling to its OWN stress-energy bootstraps UNIQUELY to the
    full nonlinear Einstein equations = GR = gravity. => FALSIFIES H.

T3 Unique T_mu_nu sink: the stress-energy tensor (Noether current of spacetime
    translations) is the unique conserved symmetric rank-2 current a massless spin-2
    can couple to (Coleman-Mandula: no extra rank-2 charges on the S-matrix in a
    gapped Poincare theory). There is no "other" rank-2 charge to couple to instead.
    => FALSIFIES H.

T4 Empirical energy loss: PSR B1913+16 orbital decay matches the GR QUADRUPOLE
    (l=2) energy-loss formula to 0.997 +/- 0.002 (Weisberg-Nice-Taylor ApJ 722:1030
    2010); LIGO GW150914 shows exactly the 2 transverse-traceless polarizations of a
    massless spin-2 (Abbott+ PRL 116:061102 2016). The spin-2 radiation DOES
    gravitational work at the GR rate. => FALSIFIES H.

T5 The framework's own l>=|s| floor (R28 sec 11.9.21 / R29 sec 11.9.22): the
    graviton's |s|=2 gives the l>=2 (no monopole/dipole) floor. BUT this floor is a
    property of ANY spin-2 field -- it cannot distinguish "graviton=gravity" from
    "generic spin-2". => NULL / non-distinguishing (honest: this test does NOT
    falsify H, but neither does it support it).

VERDICT: 4 FALSIFY, 1 NULL => H is FALSIFIED. "graviton" is NOT a misnomer; the
spin-2-ness FORCES gravity (Weinberg/Deser uniqueness + unique T_mu_nu + empirical
quadrupole energy-loss). The graviton is genuinely gravity-related.

FRAMEWORK REFINEMENT (the payoff): the spin-weighted Class-L family (R28/R29) has a
SHARP helicity ceiling for long-range forces: |s| in {0,1,2} only --
  |s|=0 scalar (no constraint), |s|=1 gauge force (couples to a charge),
  |s|=2 gravity (couples universally to T_mu_nu), |s|>=3 FORBIDDEN long-range.
So the graviton (|s|=2) is the TOP RUNG of the allowed-long-range-force helicity
ladder, uniquely forced to gravity -- a bounded ladder echoing the framework's
Hurwitz-ceiling theme. "gravity" is read (per Spike #70 Verlinde-emergent-G /
Spike #107 / Spike #71) as the emergent substrate-geometry sector; the graviton is
its spin-2 excitation. Correctly named; the only nuance is fundamental-vs-emergent,
which is NOT "not gravity-related".

Routed through srmech 0.4.2. Deterministic; no network. ASCII-safe prints.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # Class N

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# 1. the helicity ceiling of consistent long-range massless forces (Weinberg)
# ---------------------------------------------------------------------------
HELICITY_LADDER = {
    0: {"name": "scalar", "long_range": "allowed", "couples_to": "(no soft-theorem constraint)"},
    1: {"name": "photon / gauge", "long_range": "allowed", "couples_to": "a conserved CHARGE Q (gauge force; NOT universal)"},
    2: {"name": "graviton / gravity", "long_range": "allowed", "couples_to": "T_mu_nu UNIVERSALLY (equivalence principle)"},
    3: {"name": "spin-3+", "long_range": "FORBIDDEN", "couples_to": "soft theorem forces coupling -> 0 (no long-range higher-spin force)"},
}
allowed_long_range = [s for s, v in HELICITY_LADDER.items() if v["long_range"] == "allowed"]
print("helicity ladder of consistent long-range massless forces (Weinberg soft theorem):")
for s, v in HELICITY_LADDER.items():
    print(f"  |s|={s} {v['name']:20s}: {v['long_range']:9s} -> couples to {v['couples_to']}")
assert allowed_long_range == [0, 1, 2]                 # CEILING at |s|=2
print("=> allowed long-range helicities = {0,1,2}; |s|=2 (gravity) is the TOP RUNG")
emit("helicity_ceiling",
     ladder=HELICITY_LADDER, allowed_long_range=allowed_long_range, ceiling=2,
     note="Weinberg: |s|=1 couples to a charge (gauge), |s|=2 couples universally to T_mu_nu (gravity), |s|>=3 long-range FORBIDDEN; the graviton sits at the ceiling")

# ---------------------------------------------------------------------------
# 2. the falsification battery
# ---------------------------------------------------------------------------
TESTS = [
    {"id": "T1", "name": "Weinberg soft-graviton theorem (1964/1965)",
     "result": "FALSIFIES",
     "finding": "consistent massless helicity-2 MUST couple universally to all energy-momentum -> equivalence principle -> gravity"},
    {"id": "T2", "name": "Deser self-coupling bootstrap (1970)",
     "result": "FALSIFIES",
     "finding": "self-consistent massless spin-2 bootstraps uniquely to nonlinear Einstein equations = GR"},
    {"id": "T3", "name": "Unique T_mu_nu rank-2 sink (Noether / Coleman-Mandula)",
     "result": "FALSIFIES",
     "finding": "T_mu_nu is the unique conserved symmetric rank-2 current; no 'other' rank-2 charge for a spin-2 to couple to"},
    {"id": "T4", "name": "Empirical quadrupole energy loss (Hulse-Taylor; LIGO)",
     "result": "FALSIFIES",
     "finding": "PSR B1913+16 orbital decay = 0.997+/-0.002 of GR quadrupole prediction; GW150914 = 2 TT spin-2 polarizations"},
    {"id": "T5", "name": "Framework l>=|s| floor (R28/R29)",
     "result": "NULL",
     "finding": "the l>=2 floor is a property of ANY spin-2; cannot distinguish graviton-as-gravity from generic-spin-2 -> non-distinguishing"},
]
n_fals = sum(1 for t in TESTS if t["result"] == "FALSIFIES")
n_null = sum(1 for t in TESTS if t["result"] == "NULL")
print("\nfalsification battery for H ('graviton is a misnomer / not really gravity'):")
for t in TESTS:
    print(f"  {t['id']} [{t['result']:9s}] {t['name']}")
print(f"=> {n_fals} FALSIFY, {n_null} NULL")
assert (n_fals, n_null) == (4, 1)
emit("falsification_battery", tests=TESTS, n_falsifies=n_fals, n_null=n_null,
     verdict="H FALSIFIED (4 falsify, 1 null) -- spin-2 is FORCED to gravity")

# ---------------------------------------------------------------------------
# 3. empirical anchor: Hulse-Taylor ratio (attested)
# ---------------------------------------------------------------------------
ht_ratio = 0.997
r = best_rational(997, 1000, 1000)
print("\nHulse-Taylor observed/GR-quadrupole =", ht_ratio, "+/- 0.002 -> best_rational", r,
      "(Weisberg-Nice-Taylor 2010)")
emit("hulse_taylor_anchor", ratio=ht_ratio, uncertainty=0.002, best_rational=list(r),
     source="Weisberg, Nice & Taylor, ApJ 722:1030 (2010), arXiv:1011.0718",
     note="the l=2 quadrupole radiation removes orbital energy at 99.7% of the GR rate -- attested empirical confirmation that spin-2 GW does gravitational work")

# ---------------------------------------------------------------------------
# 4. verdict + framework refinement
# ---------------------------------------------------------------------------
emit("verdict",
     hypothesis="graviton is a misnomer (spin-2 but only SEEMS gravity-related)",
     disposition="FALSIFIED",
     why=("a consistent massless spin-2 is FORCED to be gravity: Weinberg soft theorem (universal "
          "T_mu_nu coupling = equivalence principle), Deser bootstrap (-> Einstein eqs), unique "
          "T_mu_nu sink, and empirical quadrupole energy-loss (Hulse-Taylor 0.997, LIGO TT). "
          "The graviton is genuinely gravity-related; the spin-2 label and the gravity label are "
          "the SAME thing by theorem, not a coincidence."),
     framework_refinement=("the spin-weighted Class-L family (R28/R29) has a SHARP helicity ceiling "
                           "for long-range forces: |s| in {0,1,2}; |s|=2=gravity is the forced TOP RUNG "
                           "(|s|>=3 long-range forbidden). The graviton is the |s|=2 entry, uniquely forced "
                           "to couple universally to T_mu_nu. 'gravity' is read as the emergent "
                           "substrate-geometry sector (Spike #70 Verlinde-emergent-G / #107 / #71); the "
                           "graviton is its spin-2 excitation -- correctly named. The only honest nuance "
                           "is fundamental-vs-emergent, which is NOT 'not gravity-related'."),
     bounded_ladder_tie="the {0,1,2} helicity ceiling echoes the framework's Hurwitz-bounded-ladder theme (no continuation past the bound)")

META = {
    "record": "meta",
    "round": "30.A",
    "title": "Falsification: is 'graviton' a misnomer? (user question from R27/R28/R29)",
    "kind": "falsification of a user-proposed hypothesis -- HONEST NEGATIVE (H falsified)",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "weinberg_soft": "Weinberg, Phys. Rev. 135, B1049 (1964); 138, B988 (1965)",
        "deser_bootstrap": "Deser, Gen. Rel. Grav. 1, 9 (1970); arXiv:gr-qc/0411023",
        "weinberg_witten": "Weinberg & Witten, Phys. Lett. B 96, 59 (1980)",
        "hulse_taylor": "Weisberg, Nice & Taylor, ApJ 722, 1030 (2010), arXiv:1011.0718",
        "ligo_gw150914": "Abbott et al. (LIGO/Virgo), Phys. Rev. Lett. 116, 061102 (2016), arXiv:1602.03837",
        "emergent_gravity_framework": "Spike #70 (Verlinde-emergent-G), #107 (bulk-to-gauge), #71 (2D phase boundary)",
    },
    "discipline": "framework reading only; honest falsification battery; negative result reported as prominently as a positive; no lean toward the framework's prior emergent-gravity preference; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: 'graviton is a misnomer' FALSIFIED -- a consistent massless spin-2 is FORCED to "
      "gravity (Weinberg/Deser/unique-T_mu_nu/Hulse-Taylor). REFINEMENT: |s|=2=gravity is the forced "
      "TOP RUNG of the {0,1,2} helicity ceiling of long-range forces; graviton correctly named.")
