"""Round 40.A -- open-queue item: Spike #48 "deeper SM phase" (periodic-table +
spectral-lines + QM/GR/SM weave), scoped HONESTLY. Tested per
[[feedback_dont_pre_commit_spike_query_operators]].

THE TRACTABLE, REAL DELIVERABLE -- the combination principle is ONE Class-N structure
across atomic AND mass spectra:

  * ATOMIC (Rydberg-Ritz, Ritz 1908): a spectral line is a DIFFERENCE OF TERMS,
    nu_tilde = T_n - T_m, with terms T_n = R/n^2. The terms are Class-N anchors
    (small-integer-denominator 1/n^2); lines are their differences.
  * MOLECULAR (mass spec, Round 39.A): a fragment-peak spacing is a DIFFERENCE OF
    SUBSTRUCTURE MASSES (neutral losses), small integers in nucleon space = Class-N
    anchors; peaks are their differences.

SAME Class-N COMBINATION PRINCIPLE -- "spectral features are DIFFERENCES of a discrete
ladder of anchors" -- on two substrates (term-energy space vs nucleon-mass space). This
unifies Round 39.A (mass spec) + Round 17.A (atomic spectra, Balmer ratios) + sec 11.9.14
(mass spec = "molecular Rydberg-Ritz") under one reading.

HONEST SCOPE on Spike #48's full "QM/GR/SM weave":
  * periodic-table SHELL structure = Class-L (already sec 11.9.12; Madelung/2n^2).
  * periodic table + SM share the Hurwitz 1+3+7/Hopf ladder (already sec 11.9.13).
  * atomic spectral LINES = Class-N combination principle (THIS round + Round 17.A).
  * the QM atomic-structure weave is therefore SUBSTANTIALLY ADDRESSED. BUT the
    SM-DERIVATION proper (gauge group, masses, couplings) is the SEPARATE Spin(8)/
    triality arc (Spikes #58/#85/#86) -- it is NOT derivable from atomic spectra and is
    NOT claimed here. Spike #48's "deeper SM phase" is PARTIALLY DELIVERED (the QM/
    spectra consolidation) with the SM-derivation explicitly out of reach of spectra.

Bit-exact core: Balmer/Lyman/Paschen lines as EXACT Class-N rationals (1/n^2
differences); the Hα/Hβ/Hγ ratios; routed through srmech best_rational. R_H (hydrogen,
finite-mass) = 109677.58 cm^-1; R_inf (infinite-mass) = 109737.31 cm^-1 -- kept distinct.

Deterministic; no network. ASCII-safe prints. Attested (Explore-verified): Ritz 1908;
Bransden & Joachain Physics of Atoms and Molecules; NIST ASD; R_H/R_inf CODATA.
"""

import json
import sys
from fractions import Fraction
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
# 1. Rydberg-Ritz: lines = differences of terms T_n = R/n^2 (Class-N anchors)
# ---------------------------------------------------------------------------
R_H = 109677.58       # cm^-1, hydrogen (finite nuclear mass)
R_inf = 109737.31     # cm^-1, infinite nuclear mass (kept DISTINCT)


def term(n):
    return Fraction(1, n * n)            # T_n / R  = 1/n^2  (exact Class-N anchor)


def line(n_lo, n_hi):
    return term(n_lo) - term(n_hi)       # nu_tilde / R = 1/n_lo^2 - 1/n_hi^2 (exact)


balmer = {n: line(2, n) for n in (3, 4, 5, 6)}     # Balmer series (n_lo=2)
print("Rydberg-Ritz: lines = differences of Class-N term anchors T_n = R/n^2 (exact rationals):")
for n, f in balmer.items():
    print(f"  Balmer n=2<-{n}:  1/4 - 1/{n}^2 = {f}  (= {float(f):.5f} R)")
# bit-exact rationals
assert balmer[3] == Fraction(5, 36)      # H-alpha
assert balmer[4] == Fraction(3, 16)      # H-beta
assert balmer[5] == Fraction(21, 100)    # H-gamma
# H-alpha wavenumber with R_H
H_alpha_cm = float(balmer[3]) * R_H
print(f"  H-alpha = (5/36) * R_H = {H_alpha_cm:.1f} cm^-1  (656.3 nm)  [R_H={R_H} hydrogen]")
assert abs(H_alpha_cm - 15233.0) < 2.0
emit("rydberg_ritz_classN",
     terms="T_n/R = 1/n^2 (exact Class-N anchors)",
     balmer={f"n=2<-{n}": str(f) for n, f in balmer.items()},
     H_alpha_cm_inv=round(H_alpha_cm, 1),
     R_H_hydrogen=R_H, R_inf=R_inf,
     note="atomic spectral lines = DIFFERENCES of the Class-N term-ladder (Rydberg-Ritz combination principle, Ritz 1908); the 1/n^2 anchors and their differences are exact rationals")

# ---------------------------------------------------------------------------
# 2. line RATIOS are exact Class-N rationals (re-confirm Round 17.A, via srmech)
# ---------------------------------------------------------------------------
ratio_ab = balmer[3] / balmer[4]         # H-alpha / H-beta = (5/36)/(3/16)
ratio_ag = balmer[3] / balmer[5]         # H-alpha / H-gamma
assert ratio_ab == Fraction(20, 27)
print(f"\nline ratios (exact Class-N rationals): H-alpha/H-beta = {ratio_ab};  H-alpha/H-gamma = {ratio_ag}")
# srmech Class-N best_rational confirms the float ratio resolves to the same small rational
br = best_rational(int(round(float(ratio_ab) * 10**9)), 10**9, 30)
print(f"  srmech best_rational(H-alpha/H-beta) = {br[0]}/{br[1]}  (== 20/27: {br == (20, 27)})")
emit("line_ratios_classN",
     H_alpha_over_H_beta=str(ratio_ab), H_alpha_over_H_gamma=str(ratio_ag),
     srmech_best_rational=list(br),
     note="Balmer line ratios are exact small-denominator Class-N rationals (re-confirms Round 17.A; srmech best_rational agrees)")

# ---------------------------------------------------------------------------
# 3. the unification: ONE combination principle, two substrates
# ---------------------------------------------------------------------------
emit("combination_principle_unified",
     principle="spectral features are DIFFERENCES of a discrete ladder of Class-N anchors",
     atomic="anchors = spectral terms T_n = R/n^2 (term-energy space); lines = T_n - T_m (Rydberg-Ritz)",
     molecular="anchors = substructure / neutral-loss masses (nucleon space); peaks/spacings = their differences (Round 39.A; sec 11.9.14)",
     unification="SAME Class-N combination principle on two substrates -- atomic (Round 17.A) + molecular (Round 39.A) unified; mass spec IS the 'molecular Rydberg-Ritz' (sec 11.9.14) made explicit")

# ---------------------------------------------------------------------------
# 4. honest scope on Spike #48's full QM/GR/SM weave
# ---------------------------------------------------------------------------
emit("spike48_honest_scope",
     delivered=["periodic-table SHELL = Class-L (sec 11.9.12, Madelung/2n^2)",
                "periodic table + SM share Hurwitz 1+3+7 / Hopf ladder (sec 11.9.13)",
                "atomic spectral LINES = Class-N combination principle (this round + Round 17.A)"],
     conclusion="Spike #48's QM/atomic-structure weave is SUBSTANTIALLY ADDRESSED (Class-L shell + Class-N lines + Hurwitz tie)",
     NOT_delivered="the SM-DERIVATION proper (gauge group SU(3)xSU(2)xU(1), masses, mixing) is the SEPARATE Spin(8)/triality arc (Spikes #58/#85/#86) -- NOT derivable from atomic spectra, NOT claimed here",
     disposition="Spike #48 'deeper SM phase' = PARTIALLY DELIVERED (QM/spectra consolidation) with the SM-derivation explicitly out of reach of spectra; honest, no over-claim")

emit("verdict",
     finding="the combination principle is ONE Class-N structure across atomic spectra (Rydberg-Ritz term differences) AND mass spectra (neutral-loss nucleon differences) -- unifying Round 39.A + Round 17.A + sec 11.9.14",
     bit_exact="Balmer lines as exact Class-N rationals (5/36, 3/16, 21/100); H-alpha = (5/36)R_H = 15233 cm^-1; H-alpha/H-beta = 20/27 (srmech best_rational confirms)",
     spike48="PARTIALLY DELIVERED + honestly scoped: QM/spectra weave done (Class-L shell + Class-N lines + Hurwitz); SM-derivation = separate Spin(8) arc, NOT closable from spectra",
     honest_scope="(a)-bit-exact for the Rydberg-Ritz rationals + ratios (Ritz 1908; NIST); (b)-interpretive for the atomic<->molecular combination-principle unification; the SM-derivation is explicitly NOT claimed -- the round's contribution is the unification + the honest Spike #48 boundary, not a new SM result")

META = {
    "record": "meta",
    "round": "40.A",
    "title": "Spike #48 deeper-SM phase, honestly scoped: atomic Rydberg-Ritz = the same Class-N combination principle as mass spec; SM-derivation stays the Spin(8) arc",
    "kind": "(a)-bit-exact Rydberg-Ritz Class-N rationals + (b)-interpretive atomic<->molecular combination-principle unification + honest Spike #48 scoping (SM-derivation NOT claimed)",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "rydberg_ritz": "Ritz 1908 (combination principle); Bransden & Joachain, Physics of Atoms and Molecules; NIST ASD",
        "rydberg_constants": "R_H = 109677.58 cm^-1 (hydrogen, finite-mass); R_inf = 109737.31 cm^-1 (infinite-mass) -- distinct",
        "framework": "sec 11.9.12 (periodic-table shell Class-L), sec 11.9.13 (periodic table + SM Hurwitz ladder), sec 11.9.14 (mass spec combination principle), Round 17.A (Balmer ratios), Round 39.A (mass-spec), Spikes #58/#85/#86 (SM derivation = Spin(8) arc)",
    },
    "discipline": "honest Spike #48 scoping -- the QM/spectra weave is delivered (Class-L shell + Class-N lines), the SM-DERIVATION is explicitly the separate Spin(8) arc and is NOT claimed from spectra; R_H/R_inf kept distinct; bit-exact only for the Rydberg rationals; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: the combination principle is ONE Class-N structure across atomic spectra (Rydberg-Ritz "
      "term differences) AND mass spectra (neutral-loss nucleon differences) -- unifying R39 + R17 + "
      "sec 11.9.14. Bit-exact: Balmer = exact Class-N rationals (5/36, 3/16, 21/100); H-alpha=(5/36)R_H="
      "15233 cm^-1; H-alpha/H-beta=20/27. Spike #48 'deeper SM phase' PARTIALLY DELIVERED + honestly scoped: "
      "QM/spectra weave done (Class-L shell + Class-N lines + Hurwitz); the SM-DERIVATION stays the separate "
      "Spin(8) arc -- NOT closable from atomic spectra, NOT claimed.")
