"""Round 41.A -- open-queue item: the ell=7 future-data test. NOT DISPATCHABLE TODAY
(the data does not exist yet). The honest "closing" is a TURNKEY PRE-REGISTRATION:
specify the exact test now, so it runs the moment CMB-S4 / LiteBIRD per-ell data lands.

THIS SCRIPT COMPUTES NO RESULT. It emits a pre-registration record only. The verdict is
PARKED. The withdrawn claim STAYS WITHDRAWN (Round 10.A / sec 11.9.6a) until/unless
future data re-opens it. No fabrication: there is no data, so there is no finding.

BACKGROUND (sec 11.9.6a, Round 10.A): the framework's {1+3+7} Hurwitz algebra identity
is preserved, but its *projection* onto CMB TT low-ell multipoles lost ell=7 -- Round
10.A tested ell=7 on Spike #190's attested SMICA per-ell data and found ell=7 ranks
#5/7 in ell=2..8 (outranked by non-Mersenne ell=5/4/2); NO ell=7-specific signature.
The per-ell projection claim was WITHDRAWN. This pre-registration names the resolving
event and fixes the test in advance (no post-hoc tuning).

PRE-REGISTERED PROTOCOL (fixed in advance; deterministic parameters only):
  * DATA: per-ell TT C_ell at low ell from a future high-precision / independent map --
    CMB-S4 (forecast 2030s) and/or LiteBIRD (launch ~2028); FITS -> HEALPix anafast,
    the SAME pipeline as Spike #190 (SMICA) / Spike #192 (NILC cross-method).
  * RANGE: ell = 2..8 (7 multipoles), exactly the Round 10.A comparison set.
  * STATISTIC: the Round 10.A per-ell concentration metric (C_ell relative to the smooth
    LCDM expectation), ranking ell=2..8.
  * NULL: no ell=7 preference -- ell=7 is uniform over the 7 ranks (rank ~ U{1..7}).
  * DECISION RULE (pre-registered, BOTH must hold to RE-OPEN the withdrawn claim):
      (a) ell=7 ranks #1 of the 7; AND
      (b) it exceeds significance after a LOOK-ELSEWHERE / Bonferroni correction over
          the n_tested = 7 multipoles (alpha_corrected = 0.05 / 7 ~ 0.00714), AND
          cross-confirms across >=2 independent component-separation methods
          (the Spike #190/#192 discipline).
  * OUTCOME IF NOT MET: the per-ell ell=7 claim REMAINS WITHDRAWN (the {1+3+7} algebra
    identity is unaffected either way -- only its multipole projection is at stake).

Routed through srmech 0.4.2 (loaded for parity; no maths performed). Deterministic.
ASCII-safe prints. Attested: Round 10.A / sec 11.9.6a; Spike #190 (SMICA) / #192 (NILC);
CMB-S4 (arXiv:1610.02743 science book) ; LiteBIRD (arXiv:2202.02773).
"""

import json
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401
import srmech  # noqa: F401  (loaded for parity; NO maths performed here)

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


n_tested = 7                                   # ell = 2..8
alpha = Fraction(5, 100)
alpha_corrected = alpha / n_tested             # Bonferroni over the 7 multipoles
print("ell=7 future-data test -- PRE-REGISTRATION (no data exists yet; NO result computed):")
print(f"  range: ell = 2..8 ({n_tested} multipoles); statistic: Round 10.A per-ell concentration metric")
print(f"  null: no ell=7 preference (rank ~ U{{1..{n_tested}}})")
print(f"  decision: ell=7 ranks #1 AND p < alpha/{n_tested} = {float(alpha_corrected):.5f} AND >=2-method cross-confirm")
print("  data: CMB-S4 (forecast 2030s) / LiteBIRD (~2028), FITS -> HEALPix anafast (Spike #190/#192 pipeline)")
print("  VERDICT: PARKED -- the withdrawn claim (Round 10.A) STAYS WITHDRAWN until data re-opens it.")

emit("preregistration",
     status="PARKED -- not dispatchable today (data does not exist)",
     background="Round 10.A / sec 11.9.6a: the {1+3+7} algebra identity is preserved, but its CMB-multipole PROJECTION lost ell=7 (ell=7 ranked #5/7 on SMICA); per-ell claim WITHDRAWN",
     data="future per-ell TT C_ell: CMB-S4 (forecast 2030s) and/or LiteBIRD (~2028); FITS -> HEALPix anafast (same pipeline as Spike #190 SMICA / #192 NILC)",
     range="ell = 2..8 (7 multipoles; Round 10.A comparison set)",
     statistic="Round 10.A per-ell concentration metric (C_ell vs smooth LCDM expectation), ranked over ell=2..8",
     null="no ell=7 preference; rank ~ uniform U{1..7}",
     decision_rule={"a": "ell=7 ranks #1 of 7", "b_alpha_corrected": float(alpha_corrected),
                    "b_correction": "Bonferroni / look-elsewhere over n_tested=7", "c": ">=2 independent component-separation methods cross-confirm (Spike #190/#192 discipline)"},
     outcome_if_not_met="per-ell ell=7 claim REMAINS WITHDRAWN; the {1+3+7} algebra identity is unaffected either way",
     no_result_computed=True)

emit("verdict",
     disposition="PARKED -- pre-registered turnkey protocol fixed in advance; NO result (no data exists); the Round 10.A withdrawal stands",
     why_parked="honest closing of a 'names-the-resolving-event' item: make the future test turnkey and tamper-proof (pre-registered statistic/null/threshold/cross-confirmation), without fabricating a finding",
     honest_scope="this is a PRE-REGISTRATION, not a result; verdict is PARKED-pending-data; no bit-exact claim beyond the fixed protocol parameters; framework reading only")

META = {
    "record": "meta",
    "round": "41.A",
    "title": "ell=7 future-data test -- PRE-REGISTRATION (PARKED; no result; turnkey protocol for CMB-S4/LiteBIRD)",
    "kind": "PARKED pre-registration -- the honest closing of a not-dispatchable-today item; NO finding fabricated",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "withdrawal": "Round 10.A / sec 11.9.6a (ell=7 ranked #5/7 on SMICA; per-ell claim withdrawn)",
        "pipeline": "Spike #190 (SMICA) / Spike #192 (NILC) HEALPix anafast",
        "future_data": "CMB-S4 science book (arXiv:1610.02743); LiteBIRD (arXiv:2202.02773)",
    },
    "discipline": "NO result computed (no data); PARKED-pending-data; pre-registered statistic/null/threshold/cross-confirm fixed in advance (no post-hoc tuning); the {1+3+7} algebra identity is unaffected; framework reading only; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: PARKED. The ell=7 future-data test is NOT dispatchable today (no data); this is a turnkey, "
      "tamper-proof PRE-REGISTRATION (statistic/null/threshold/cross-confirmation fixed in advance) for "
      "CMB-S4/LiteBIRD. The Round 10.A withdrawal of the per-ell ell=7 claim STANDS; the {1+3+7} algebra "
      "identity is unaffected. No result fabricated.")
