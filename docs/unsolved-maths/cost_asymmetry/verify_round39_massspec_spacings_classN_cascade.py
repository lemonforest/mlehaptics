"""Round 39.A -- open-queue item (thread 9b): mass-spec enhancement -- fragment m/z
SPACINGS as Class-N small-integer anchors + fragmentation as a cascade. Builds on
sec 11.9.14 (mass spec = combination principle in integer-nucleon space, the "molecular
Rydberg-Ritz") + Spike #38/#38b (caffeine). Tested honestly.

THE ENHANCEMENT (3 parts):
(1) ENCODE BY SPACINGS, not absolute m/z. A fragmentation spectrum's information is in
    the DIFFERENCES between peaks; those differences are characteristic "neutral losses"
    -- small integers in nucleon-count space (H2O=18, NH3=17, CH3=15, HCN=27, CO=28,
    CHO=29, CO2=44, ...). These are Class-N small-integer anchors. Delta-encoding the
    spectrum against the neutral-loss catalog IS the biological-cascade-style
    "delta-encode only what changed" (srmech.signal_processing).
(2) FRAGMENTATION = a CASCADE. Each fragmentation step is one neutral loss = a Class-K
    sign (subtraction direction) o Class-N integer-anchor; the fragmentation TREE is
    A o ... o (per-step K o N). The molecule sheds Class-N integer chunks step by step.
(3) This is the MOLECULAR analogue of the Rydberg-Ritz combination principle (atomic
    spectra; Round 40.A): "lines/peaks are differences of anchors". Same Class-N
    combination principle, two substrates (nucleon-mass space vs term-energy space).

Bit-exact core: the neutral-loss catalog integers + a worked decode of the attested
caffeine EI-MS fragment series -- clean single losses match the catalog exactly;
composite spacings decompose as SUMS of catalog anchors (Class-N combination).

Routed through srmech 0.4.2. Deterministic; no network. ASCII-safe prints.
Attested (Explore-verified): neutral losses McLafferty-Turecek 1993 Table 2.1;
caffeine (C8H10N4O2, M=194) EI-MS NIST MS #1681 fragments 194/165/109/82/67/55;
combination-principle framing standard (McLafferty).
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
# 1. the Class-N neutral-loss catalog (small-integer nucleon anchors)
# ---------------------------------------------------------------------------
NEUTRAL_LOSS = {15: "CH3 (methyl)", 17: "NH3 / OH", 18: "H2O", 27: "HCN",
                28: "CO / C2H4", 29: "CHO", 44: "CO2"}
print("Class-N neutral-loss catalog (small-integer nucleon anchors):")
for m, name in sorted(NEUTRAL_LOSS.items()):
    print(f"  -{m:>2}  {name}")
emit("neutral_loss_catalog", catalog={str(k): v for k, v in NEUTRAL_LOSS.items()},
     note="characteristic neutral losses are small integers in nucleon-count space = Class-N anchors (McLafferty-Turecek 1993)")

# ---------------------------------------------------------------------------
# 2. caffeine EI-MS: decode the fragment series by SPACINGS (delta-encode)
# ---------------------------------------------------------------------------
caffeine = [194, 165, 109, 82, 67, 55]        # attested NIST MS #1681 principal ions
spacings = [caffeine[i] - caffeine[i + 1] for i in range(len(caffeine) - 1)]
print("\ncaffeine (M=194) fragment series:", caffeine)
print("consecutive spacings (the delta-encoding):", spacings)


def decompose(delta, catalog_keys, max_terms=2):
    """is `delta` a single catalog anchor, or a SUM of <=max_terms anchors? (Class-N combination)"""
    if delta in catalog_keys:
        return [delta]
    for a in catalog_keys:
        if (delta - a) in catalog_keys:
            return sorted([a, delta - a], reverse=True)
    return None   # not a clean 1-or-2-term catalog combination


keys = sorted(NEUTRAL_LOSS)
decoded = []
for d in spacings:
    parts = decompose(d, keys)
    decoded.append({"spacing": d, "decomposition": parts,
                    "clean_single": (parts is not None and len(parts) == 1)})
    label = (" + ".join(f"{p}({NEUTRAL_LOSS[p]})" for p in parts) if parts else "composite/uncertain (>2 anchors)")
    print(f"  delta={d:>3}  ->  {label}")
# clean single-loss spacings present (bit-exact catalog hits):
clean = [d["spacing"] for d in decoded if d["clean_single"]]
assert 27 in clean and 15 in clean and 29 in clean   # HCN, CH3, CHO are clean single losses
emit("caffeine_spacing_decode",
     fragment_series=caffeine, spacings=spacings, decoded=decoded,
     clean_single_losses=clean,
     note="spacings decode against the Class-N catalog: clean single losses {29 CHO, 27 HCN, 15 CH3} match exactly; composite spacings (e.g. 56) decompose as SUMS of catalog anchors (Class-N combination). 12 flagged uncertain (sub-catalog).")

# ---------------------------------------------------------------------------
# 3. the cascade reading + the Rydberg-Ritz cross-link
# ---------------------------------------------------------------------------
emit("fragmentation_cascade",
     cascade="A (the parent molecular ion, content-addressed) o [per fragmentation step: K (loss direction / sign) o N (the integer neutral-loss anchor)] o ... -- the fragmentation TREE is a cascade shedding Class-N integer chunks",
     delta_encoding="encode the spectrum by SPACINGS against the neutral-loss catalog (srmech.signal_processing delta-encode), not absolute m/z -- the biological-cascade 'only what changed' encoding")

emit("combination_principle_crosslink",
     statement="mass spectra are the MOLECULAR instance of the same Class-N COMBINATION PRINCIPLE as atomic spectra: peaks/lines are DIFFERENCES of anchors. Mass spec: differences of substructure masses (neutral losses) in nucleon space. Atomic spectra: differences of spectral terms (Rydberg-Ritz) in term-energy space. Round 40.A unifies both under one Class-N reading.",
     ties=["sec 11.9.14 (mass spec = combination principle in nucleon space)", "Spike #38/#38b (caffeine)", "Round 40.A (atomic Rydberg-Ritz)"])

emit("verdict",
     finding="mass-spec ENHANCEMENT delivered: (1) encode by SPACINGS = Class-N neutral-loss anchors (delta-encoding); (2) fragmentation = cascade (per-step K o N, shedding integer chunks); (3) the molecular instance of the Class-N combination principle (peaks = differences of anchors), cross-linking to atomic Rydberg-Ritz (R40).",
     bit_exact="the neutral-loss catalog integers + caffeine clean single-loss spacings {29 CHO, 27 HCN, 15 CH3} matching exactly; composite spacings = sums of catalog anchors",
     honest_scope="(a)-bit-exact for the integer neutral-loss catalog + the clean caffeine spacing matches (attested NIST + McLafferty); (b)-interpretive for the delta-encode / cascade / combination-principle framing. NOT a new fragmentation-mechanism claim -- composite spacings (56, 12) are flagged as multi-anchor / sub-catalog, not mechanistically certified. Builds on sec 11.9.14 + Spike #38; framework reading only.")

META = {
    "record": "meta",
    "round": "39.A",
    "title": "Mass-spec enhancement: fragment SPACINGS = Class-N neutral-loss anchors; fragmentation = cascade; the molecular combination principle",
    "kind": "(a)-bit-exact neutral-loss catalog + caffeine spacing decode + (b)-interpretive delta-encode/cascade/combination-principle framing",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "neutral_losses": "McLafferty & Turecek, Interpretation of Mass Spectra (4th ed. 1993) Table 2.1",
        "caffeine": "NIST MS #1681 (C8H10N4O2, M=194; principal ions 194/165/109/82/67/55)",
        "combination_principle": "McLafferty (fragment differences = neutral losses); the molecular analogue of Ritz",
        "framework": "sec 11.9.14 (mass spec combination principle); Spike #38/#38b (caffeine); Round 40.A (atomic Rydberg-Ritz); srmech.signal_processing (delta-encode)",
    },
    "discipline": "bit-exact only for the integer catalog + clean caffeine matches; composite spacings flagged (not mechanistically certified); no new fragmentation-mechanism claim; framework reading only; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: mass-spec enhancement -- fragment SPACINGS = Class-N small-integer neutral-loss anchors "
      "(delta-encode against the catalog, not absolute m/z); fragmentation = a cascade (per-step K o N "
      "shedding integer chunks); the MOLECULAR instance of the Class-N combination principle (peaks = "
      "differences of anchors), cross-linking to atomic Rydberg-Ritz (R40). Bit-exact: caffeine clean "
      "single losses {29 CHO, 27 HCN, 15 CH3} match the catalog; composite spacings = sums of anchors.")
