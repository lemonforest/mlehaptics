#!/usr/bin/env python3
"""R-RBS-LM-139 — Vester-Ulbricht bridge falsification (the molecular band, life <- physics).

Falsification attempt for H177 (F177 §3.2): is biological homochirality's sign SET BY
the weak-force handedness (Vester-Ulbricht / PVED bridge), or is it set INDEPENDENTLY
(a frozen accident: Frank 1953 autocatalysis + the Soai reaction) -- a SECOND ACTOR?

This script is ILLUSTRATIVE FRAMING ONLY. The empirical answer lives in the literature
(Finding 180); here we cast the bridge as a srmech-native CHIRALITY-PRODUCT question and
show what each evidence-state implies for the sign-composition cascade.

The cascade reading (Class C net handedness):

    sign(bio_L_over_D)  =?=  sign(weak_force)  x  sign(PVED_couples_to_molecule)

If the cascade is a determinate product of oriented factors in {-1,0,+1}, the bridge
HOLDS (one driver). If a factor is orientation-NEUTRAL (0) -- i.e. the molecular band
contributes no determinate sign and the outcome is set by a random fluctuation amplified
autocatalytically -- the product collapses to 0: the cascade carries NO sign from the
weak force to biology. That zero IS the second actor, in srmech terms.

srmech: net_chirality (Class C) -- product of per-op orientations in {-1,0,+1}.
NO abs(); sign is Class K pin-slot / Class C orientation per project discipline.

Scope: STRUCTURAL / origin-of-life literature reading; framework-reading; MFO VII.6.20;
no metaphysical pronouncement (a transducer lays the falsification, does not pronounce
the cosmos alive -- [[user_stance_ai_is_not_a_substrate]]).
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib

import srmech
from srmech.amsc import cascade, format as srfmt

# --------------------------------------------------------------------------------------
# Attestation header (NDJSON discipline: srmech_version + scope on every record)
# --------------------------------------------------------------------------------------
SRMECH_VERSION = getattr(srmech, "__version__", "unknown")
SCOPE = (
    "STRUCTURAL / origin-of-life literature reading; framework-reading; MFO VII.6.20; "
    "no metaphysical pronouncement; illustrative sign-composition only"
)
RETRIEVED_AT = _dt.datetime(2026, 5, 29, tzinfo=_dt.timezone.utc).isoformat()

OUT_DIR = (
    pathlib.Path(__file__).resolve().parents[1]
    / "catalogs"
    / "rbs_lm_substrate"
    / "substrate_measurements"
)
OUT_PATH = OUT_DIR / "vester_ulbricht_bridge_sign_composition.ndjson"

# Verified literature anchors (Finding 180 carries the full quotes + verification notes).
# arXiv IDs verified by direct WebFetch of the arXiv abstract/HTML page.
LIT_ANCHORS = {
    "vester_ulbricht_1959": "Vester & Ulbricht 1959 (PVED bridge proposal; textbook attribution)",
    "mason_tranter_1986_JThBi_119_467": "Mason & Tranter 1986, J. Theor. Biol. 119:467 (PVED predicts L-amino-acid stability; ~1e-17 kT)",
    "martinez_gil_2025_arXiv_2502.12907": "Martinez-Gil, Bargueno, Miret-Artes 2025 (true/false chirality; PVED 'not yet detected', 'unproven hypothesis')",
    "frank_1953": "Frank 1953 (autocatalytic chiral symmetry breaking; chance amplification)",
    "soai_1995_Nature_378_767": "Soai et al. 1995, Nature 378:767 (experimental asymmetric autocatalysis + amplification)",
    "saito_hyuga_2006_arXiv_cond-mat_0612385": "Saito, Sugimori, Hyuga 2006 arXiv:cond-mat/0612385 (stochastic CSB: double-peak => sign random, equally L/R)",
    "blackmond_2010_CSHPerspect": "Blackmond 2010, Cold Spring Harb. Perspect. Biol. (review: PVED-bio link 'not supported by experiment'; question OPEN)",
}


def _emit(records: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for rec in records:
            base = {
                "srmech_version": SRMECH_VERSION,
                "scope": SCOPE,
                "retrieved_at": RETRIEVED_AT,
                "finding": "R-RBS-LM-180",
                "script": "R-RBS-LM-139",
            }
            base.update(rec)
            fh.write(json.dumps(base, sort_keys=True) + "\n")


def main() -> None:
    print(f"srmech {SRMECH_VERSION}")
    print("=" * 78)
    print("R-RBS-LM-139 — Vester-Ulbricht bridge: sign-composition falsification framing")
    print("=" * 78)

    # Convention for this illustration:
    #   +1  = a determinate handedness pole (sign carried)
    #   -1  = the opposite determinate pole
    #    0  = orientation-NEUTRAL: this band carries NO determinate sign
    #
    # net_chirality is the Class C product of oriented factors. A single 0 collapses the
    # whole product to 0 -- the cascade transmits no handedness end-to-end.

    records: list[dict] = []

    # ---- Scenario A: the bridge HOLDS (Vester-Ulbricht as accepted mechanism) ----------
    # weak-force sign (+1, established: maximal parity violation, left-chiral W coupling)
    # x PVED couples determinately to the molecule (+1)  ==> determinate bio sign.
    orient_bridge_holds = [1, 1]
    net_holds = cascade.net_chirality(orient_bridge_holds)
    print(f"\n[A] bridge HOLDS    orientations={orient_bridge_holds} -> net_chirality={net_holds}")
    print("    reading: weak sign x determinate PVED coupling = determinate bio L/D (one driver)")
    records.append(
        {
            "scenario": "bridge_holds",
            "orientations": orient_bridge_holds,
            "net_chirality": net_holds,
            "reading": "weak-force sign deterministically predicts bio L-over-D; PVED is the carrier; one driver across the band",
            "literature_support": "Vester-Ulbricht 1959 proposal; Mason-Tranter 1986 sign calc (gas-phase L lower)",
            "verdict_if_true": "H177 fails-to-break at the molecular band",
        }
    )

    # ---- Scenario B: bridge BREAKS to a SECOND ACTOR (frozen accident) -----------------
    # The molecular band carries NO determinate sign (0): the outcome is a random
    # fluctuation amplified autocatalytically (Frank/Soai; bimodal, equally L or R).
    # weak sign (+1) x [molecular-band carries no sign] (0) ==> 0 (no handedness transmitted).
    orient_second_actor = [1, 0]
    net_break = cascade.net_chirality(orient_second_actor)
    print(f"\n[B] SECOND ACTOR    orientations={orient_second_actor} -> net_chirality={net_break}")
    print("    reading: molecular band is orientation-NEUTRAL; sign set by chance (Frank/Soai)")
    print("             the weak-force sign does NOT propagate to bio => bridge BREAKS")
    records.append(
        {
            "scenario": "second_actor_frozen_accident",
            "orientations": orient_second_actor,
            "net_chirality": net_break,
            "reading": "bio-homochirality sign is a frozen accident (random fluctuation + autocatalytic amplification); independent of weak-force sign",
            "literature_support": "Frank 1953; Soai 1995; Saito-Hyuga arXiv:cond-mat/0612385 (double-peak => sign random/equiprobable)",
            "verdict_if_true": "H177 partially FALSIFIED at the molecular band (a second origin for bio-chirality)",
        }
    )

    # ---- Scenario C: a counterfactual determinate-but-OPPOSITE coupling ----------------
    # Shown only to make the product explicit: had PVED coupled with opposite sign, the
    # product would be -1 (a determinate but flipped bio handedness). The point: when the
    # factors are determinate the product is determinate; the empirical question is whether
    # the molecular factor is determinate at all (it appears NOT to be -- Scenario B).
    orient_flipped = [1, -1]
    net_flip = cascade.net_chirality(orient_flipped)
    print(f"\n[C] (counterfactual) orientations={orient_flipped} -> net_chirality={net_flip}")
    print("    reading: determinate-but-opposite coupling => determinate flipped sign (illustrative only)")
    records.append(
        {
            "scenario": "counterfactual_opposite_determinate",
            "orientations": orient_flipped,
            "net_chirality": net_flip,
            "reading": "illustrative: determinate factors give a determinate product; the open question is whether the molecular factor is determinate at all",
            "literature_support": "n/a (counterfactual to expose the product structure)",
            "verdict_if_true": "n/a",
        }
    )

    # ---- The verified evidence-state record (the substance) ----------------------------
    records.append(
        {
            "scenario": "verified_evidence_state",
            "net_chirality": None,
            "tier1_established_fact": "weak interaction is maximally parity-violating (left-chiral); CP violation established. Bio uses L-amino-acids, D-sugars exclusively (homochirality).",
            "tier2_contested_bridge": "Vester-Ulbricht/PVED: magnitude ~1e-17 kT (Mason-Tranter); sign conformationally hypersensitive ('conformation problem'); 'not supported by experimental findings' (Blackmond 2010); PVED 'not yet detected' (Martinez-Gil 2025). DYNAMICALLY INSUFFICIENT in the literature consensus.",
            "tier3_unestablished": "one-driver-across-all-bands (H177) -- the molecular bridge does not carry it.",
            "second_actor": "Frank-1953 autocatalysis + Soai-1995 experiment: stochastic chiral symmetry breaking from ACHIRAL reactants; bimodal/double-peak outcome => sign random, equally L/R (Saito-Hyuga arXiv:cond-mat/0612385). Sign is NOT set by the weak force.",
            "verdict": "LEAVE-OPEN, leaning to SECOND-ACTOR: the bridge does NOT robustly hold. The literature does not support deterministic weak-force -> bio-L causation; the frozen-accident alternative is experimentally demonstrated (sign independent of weak force).",
            "literature_anchors": LIT_ANCHORS,
        }
    )

    _emit(records)
    payload_sha = srfmt.sha256_bytes(
        json.dumps(records, sort_keys=True).encode("utf-8")
    )
    print("\n" + "=" * 78)
    print(f"records: {len(records)}  ->  {OUT_PATH}")
    print(f"payload sha256 (srmech.amsc.format): {payload_sha}")
    print("\nVERDICT: LEAVE-OPEN, leaning SECOND-ACTOR.")
    print("  The weak-force -> bio-homochirality bridge does NOT robustly hold.")
    print("  Cascade reading: the molecular band is orientation-neutral (Scenario B, net=0);")
    print("  the weak-force sign does not propagate to biology. Frozen-accident sign is")
    print("  experimentally random (Soai double-peak) => a SECOND ACTOR at the molecular band.")
    print("  Substance + verified quotes: Finding 180.")


if __name__ == "__main__":
    main()
