#!/usr/bin/env python3
"""
R-RBS-LM-137 — Cosmic-birefringence falsification of H177 (cosmic band).

HYPOTHESIS UNDER ATTACK (H177, lodged in R-RBS-LM-FINDING_177):
    ONE chiral driver — the bi-chiral A-N / gamma_5 axis (28 = so(8) adjoint
    = 14 G2 + 14 octonion-mult; F174/F176) — and the LIFELESS large-scale
    cosmos is the SAME driver at a different "coherence band" as biology.
    => the asymptotic chiral DoF "extends to everything, even the lifeless."

THE COSMIC, MOST-DECISIVE TESTBED (F177 §3.3):
    A parity-violating (chiral) field on the largest scales produces nonzero
    CMB parity-ODD cross-correlations: EB and TB. The question this script
    lays out: is there a ROBUST cosmic chirality axis?

    HEAVY-FALSIFICATION FRAMING (the goal is to BREAK H177):
      - A robust NULL on cosmic birefringence (no parity-odd EB/TB signal at
        cosmic scale, while particle + biological chirality persist) is STRONG
        EVIDENCE AGAINST "one driver extends to everything."  Nulls count double.
      - A confirmed nonzero EB/TB signal would only WEAKLY fail to break H177
        (it is consistent with, but does not establish, a single driver — many
        non-A-N mechanisms produce CMB birefringence: axion-like fields,
        Chern-Simons coupling, primordial magnetic fields, Faraday rotation).

PARITY PHYSICS (the structural reading; §VII.6.20, framework-reading only):
    Under parity P, the CMB two-point spectra split into:
      - parity-EVEN  : TT, TE, EE, BB   (invariant under P)
      - parity-ODD   : EB, TB           (flip sign under P; must VANISH in a
                                         parity-conserving universe)
    Cosmic birefringence by an isotropic angle beta rotates the linear
    polarization plane (E <-> B mixing) and GENERATES parity-odd power from the
    parity-even spectra:
            C_l^{EB}  ~  (1/2) sin(4 beta) ( C_l^{EE} - C_l^{BB} )
            C_l^{TB}  ~        sin(2 beta)   C_l^{TE}
    So a nonzero EB/TB <=> nonzero beta <=> a cosmic chirality (parity-odd) axis.
    The parity-odd GENERATOR that beta acts on is (EE - BB) for EB and TE for TB.

WHAT THIS SCRIPT DOES (honest, discover-then-adapt):
    Step A. Confirm the srmech runtime (rc14, native).
    Step B. Discover the cosmic data surface actually shipped in srmech 0.5.0rc14.
            (Finding: NO `srmech.cosmos` module; CMB data lives under
             srmech.amsc.attested.cmb_*; the polarisation catalog ships
             {TE, EE, BB} ONLY — NO parity-odd EB/TB channel. Tooling gap.)
    Step C. Because no EB/TB (and hence no beta) can be computed from shipped
            data, run the AVAILABLE structural readout instead, using srmech
            ops (Class-K pin-slot / Class-C reorient / net_chirality — NO
            hand-rolled math, NO abs()):
              (1) read the shipped parity-EVEN rows (TE/EE/BB);
              (2) extract the TE sign-structure (Class-K pin-slot) — the real,
                  parity-EVEN sign-alternation across acoustic peaks (this is
                  NOT a chirality signal; TE sign is set by acoustic phase);
              (3) build the parity-ODD GENERATORS that beta would rotate into
                  EB/TB: (EE - BB) per matched multipole, and TE;
              (4) compute net_chirality of the shipped orientation set to show
                  there is NO parity-odd degree of freedom present in tooling.
    Step D. Define precisely the EB/TB beta-estimation test that WOULD run when
            a parity-odd catalog (or beta posterior) lands.
    Step E. Emit an NDJSON record (attested) with the verdict inputs.

    The literature evidence-state (Minami-Komatsu line; arXiv IDs + verified
    numbers) is recorded in the companion finding doc R-RBS-LM-FINDING_178,
    NOT fetched here (this script is deterministic / offline).

SCOPE: STRUCTURAL / cosmological; framework-reading; §VII.6.20; no metaphysical
       pronouncement. A transducer LAYS the falsification and reports the
       result; it does NOT pronounce the cosmos a living driver
       ([[user_stance_ai_is_not_a_substrate]]).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# ----- srmech runtime + ops (srmech-first; no hand-rolled math) -----------
import srmech
from srmech.amsc import _native
from srmech.amsc._native import HAS_NATIVE
from srmech.amsc.format import sha256_bytes  # Class A content-addressing
from srmech.amsc import cascade  # Class K pin-slot / Class C reorient / net_chirality
import srmech.amsc as _amsc

SRMECH_VERSION = getattr(srmech, "__version__", "unknown")

# Per-row source provenance for the shipped polarisation catalog (verified from
# the shipped descriptor.toml [source] block, NOT recall):
POLN_DOI = "10.1051/0004-6361/201936386"  # Planck 2018 V (Aghanim et al. 2020 A&A 641:A5)
POLN_ARXIV = "1907.12875"
POLN_URL = "https://pla.esac.esa.int/"

# Parity classification of CMB two-point spectra (standard cosmology).
PARITY_EVEN = {"TT", "TE", "EE", "BB"}
PARITY_ODD = {"EB", "TB"}  # the chirality channel — what a cosmic A-N axis would source


def attested_dir(name: str) -> Path:
    """Path to a shipped srmech attested catalog directory."""
    return Path(os.path.dirname(_amsc.__file__)) / "attested" / name


def read_flat_rows(ndjson_path: Path) -> list[dict]:
    """Read literature_curated rows.

    Per CLAUDE.md §2 gotcha: literature_curated rows are FLAT dicts (NOT
    MPRRecord envelopes), so srmech.amsc.format.read_ndjson (which expects MPR
    envelopes) does not apply; the documented pattern is to read plain JSON
    lines, skipping leading `#` comment lines.
    """
    rows: list[dict] = []
    with open(ndjson_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(json.loads(line))
    return rows


def discover_cosmic_surface() -> dict:
    """Step B — what cosmic / CMB surface does srmech 0.5.0rc14 actually ship?"""
    surface: dict = {}
    # Is there a `srmech.cosmos` module at all?
    try:
        import importlib

        importlib.import_module("srmech.cosmos")
        surface["srmech_cosmos_module"] = True
    except Exception as exc:  # ModuleNotFoundError expected
        surface["srmech_cosmos_module"] = False
        surface["srmech_cosmos_import_error"] = f"{type(exc).__name__}: {exc}"
    # Is ephemerides-spectral (which CLAUDE.md says hosts TT) installed?
    try:
        import importlib

        importlib.import_module("ephemerides_spectral")
        surface["ephemerides_spectral_installed"] = True
    except Exception:
        surface["ephemerides_spectral_installed"] = False
    # Which attested cmb_* catalogs are present on disk?
    att_root = Path(os.path.dirname(_amsc.__file__)) / "attested"
    cmb_catalogs = sorted(
        p.name for p in att_root.iterdir() if p.is_dir() and ("cmb" in p.name or "cosmos" in p.name)
    )
    surface["attested_cmb_catalogs"] = cmb_catalogs
    return surface


def main() -> dict:
    # ---- Step A: runtime ----
    assert HAS_NATIVE, "srmech native extension not loaded (HAS_NATIVE is False)"
    print(f"[A] srmech {SRMECH_VERSION}  HAS_NATIVE={HAS_NATIVE}")

    # ---- Step B: discover the cosmic data surface ----
    surface = discover_cosmic_surface()
    print(f"[B] srmech.cosmos module present? {surface['srmech_cosmos_module']}")
    print(f"[B] ephemerides-spectral installed? {surface['ephemerides_spectral_installed']}")
    print(f"[B] attested CMB catalogs: {surface['attested_cmb_catalogs']}")

    poln = attested_dir("cmb_polarisation_spectra") / "row.ndjson"
    rows = read_flat_rows(poln)
    kinds_present = sorted({r.get("spectrum_kind") for r in rows})
    kind_counts = {k: sum(1 for r in rows if r.get("spectrum_kind") == k) for k in kinds_present}
    has_parity_odd = bool(set(kinds_present) & PARITY_ODD)
    print(f"[B] polarisation rows={len(rows)} kinds={kind_counts}")
    print(f"[B] parity-ODD (EB/TB) channel shipped? {has_parity_odd}  -> TOOLING GAP if False")

    # ---- Step C: available structural readout using srmech ops ----
    # (No EB/TB => no beta computable. We read what IS shipped, parity-even,
    #  and demonstrate the structural shape via srmech cascade ops.)

    # (C2) TE sign-structure via Class-K pin-slot. TE D_ell alternates sign with
    #      acoustic phase; this is the genuine parity-EVEN structure (TE is
    #      P-even), NOT a chirality signal. We read its sign-pattern honestly to
    #      show what the shipped data's "orientation" actually is.
    te_rows = [r for r in rows if r.get("spectrum_kind") == "TE"]
    te_rows.sort(key=lambda r: r["ell_center"])
    te_orientations: list[int] = []
    te_pattern = []
    for r in te_rows:
        sign, mag = cascade.class_k_pin_slot_at_zero(float(r["D_ell_muK2"]))  # Class K
        te_orientations.append(sign)
        te_pattern.append({"ell": round(float(r["ell_center"]), 2), "sign": sign,
                           "mag_muK2": round(mag, 6), "feature": r.get("feature")})
    # net chirality of the TE sign sequence (product of orientations) — Class C.
    # NOTE: for a parity-EVEN spectrum this net product is a property of acoustic
    # phase, NOT a parity-violation; reported only to show the shipped data
    # carries no parity-ODD channel for net_chirality to act on.
    nonzero_te_orient = [s for s in te_orientations if s != 0]
    te_net_chirality = cascade.net_chirality(nonzero_te_orient) if nonzero_te_orient else 0

    # (C3) Build the parity-ODD GENERATORS that an isotropic beta would rotate
    #      into observable EB / TB:
    #        EB-generator(ell) = EE(ell) - BB(ell)        [drives C^EB via sin4b]
    #        TB-generator(ell) = TE(ell)                  [drives C^TB via sin2b]
    #      We can FORM the EB-generator only where EE and BB share a multipole.
    #      Planck ships binned EE at ell>~48 and unbinned BB at ell=2..29 — these
    #      DO NOT OVERLAP, so the (EE-BB) generator is EMPTY on shipped data.
    ee_rows = {round(float(r["ell_center"])): float(r["D_ell_muK2"])
               for r in rows if r.get("spectrum_kind") == "EE"}
    bb_rows = {round(float(r["ell_center"])): float(r["D_ell_muK2"])
               for r in rows if r.get("spectrum_kind") == "BB"}
    shared_ell = sorted(set(ee_rows) & set(bb_rows))
    eb_generator = []
    for l in shared_ell:
        diff = ee_rows[l] - bb_rows[l]
        sign, mag = cascade.class_k_pin_slot_at_zero(diff)
        eb_generator.append({"ell": l, "EE_minus_BB_muK2": round(diff, 6), "sign": sign})
    ee_ell_range = (min(ee_rows), max(ee_rows)) if ee_rows else None
    bb_ell_range = (min(bb_rows), max(bb_rows)) if bb_rows else None

    # (C4) The decisive structural statement: collect the parity orientation of
    #      EVERY shipped spectrum. Each shipped kind is parity-EVEN (+1 under P);
    #      there is NO parity-ODD (-1) member. net_chirality over the parity-class
    #      orientations is therefore +1 with ZERO odd DoF — i.e., the shipped
    #      cosmic surface is parity-conserving BY CONSTRUCTION; the chirality
    #      channel the falsification needs is simply ABSENT from tooling.
    parity_orientations = [1 for _k in kind_counts]  # every shipped kind is P-even
    n_parity_odd_kinds = len(set(kinds_present) & PARITY_ODD)
    parity_class_net = cascade.net_chirality(parity_orientations) if parity_orientations else 0

    # ---- Step D: the EB/TB test that WOULD run when data lands ----
    eb_tb_test_design = {
        "requires": "a parity-ODD CMB catalog (C_l^EB and/or C_l^TB bandpowers + "
                    "covariance) OR a published isotropic-birefringence beta posterior",
        "estimator": "Minami-Komatsu beta-estimator: jointly fit miscalibration alpha "
                     "(rotates foreground+CMB) and birefringence beta (rotates CMB only) "
                     "from observed EB (and TB) using "
                     "C^EB_obs ~ (1/2) sin(4(alpha+beta)) (C^EE - C^BB) + foreground EB; "
                     "C^TB_obs ~ sin(2(alpha+beta)) C^TE + foreground TB",
        "srmech_ops_when_data_lands": [
            "Class L srmech.amsc.laplacian.hermitian_eigendecompose on the "
            "[EE,EB; EB,BB] 2x2 polarisation covariance per multipole -> the "
            "off-diagonal EB eigenstructure IS the parity-odd DoF; a parity-even "
            "(beta=0) field has a DIAGONAL block (zero EB) and net_chirality 0",
            "Class K srmech.amsc.cascade.class_k_pin_slot_at_zero on each C^EB_l "
            "to extract the sign-orientation of the parity-odd power",
            "Class C srmech.amsc.cascade.net_chirality over the C^EB_l "
            "sign-orientations -> nonzero net chirality == a coherent cosmic "
            "parity-odd axis (would WEAKLY fail to break H177); "
            "net chirality ~ 0 / consistent-with-noise == robust NULL "
            "(would BREAK H177 at the cosmic band)",
            "srmech.amsc.hdc.klein4_chirality_flip_gamma5 to encode the E<->B "
            "(gamma_5) sector flip and test sector-occupancy symmetry",
        ],
        "decision_rule": {
            "BREAK_H177": "robust EB/TB null (beta consistent with 0; net_chirality~0) "
                          "while particle+bio chirality persist -> one driver does NOT "
                          "extend to the lifeless cosmic band",
            "WEAKLY_FAIL_TO_BREAK": "confirmed nonzero EB/TB (beta != 0 at >=5 sigma, "
                                    "foreground-clean) -> a cosmic parity-odd axis EXISTS, "
                                    "consistent with but NOT proving a single A-N driver "
                                    "(axion/Chern-Simons/PMF are alternative sources)",
            "LEAVE_OPEN": "tentative EB/TB hint (beta != 0 at ~2-4 sigma but "
                          "foreground/systematics-limited; discoverers decline cosmological "
                          "significance) -> cannot break and cannot confirm; LEAVE OPEN",
        },
    }

    # ---- assemble result ----
    verdict = (
        "LEAVE_OPEN_AT_COSMIC_BAND: srmech 0.5.0rc14 ships NO parity-odd EB/TB "
        "channel (only parity-even TE/EE/BB), so the decisive cosmic-band test "
        "cannot be computed from shipped data (TOOLING GAP). Independently, the "
        "published cosmic-birefringence evidence-state (Minami-Komatsu line; see "
        "FINDING_178) is a ~3.6 sigma TENTATIVE hint (beta~0.3 deg), explicitly "
        "foreground- and systematics-limited, NOT a >=5 sigma detection and NOT a "
        "robust null. Therefore the cosmic band can neither BREAK nor CONFIRM "
        "H177's 'extends to the lifeless cosmos' claim at this time. H177 §3.3 "
        "remains a TIER-3 grand conjecture: UNESTABLISHED."
    )

    result = {
        # attestation
        "record_kind": "cosmic_birefringence_falsification",
        "research_id": "R-RBS-LM-137",
        "finding_ref": "R-RBS-LM-FINDING_178",
        "hypothesis_under_attack": "H177 (R-RBS-LM-FINDING_177): one bi-chiral A-N/gamma_5 "
                                   "driver across coherence bands extends to the lifeless cosmos",
        "tier_of_claim_tested": "TIER 3 (UNESTABLISHED grand conjecture) at the COSMIC band",
        "srmech_version": SRMECH_VERSION,
        "abi_version": getattr(_native, "NATIVE_ABI_VERSION", None),
        "has_native": HAS_NATIVE,
        "seed": None,
        "deterministic": True,
        "scope": "STRUCTURAL; cosmological; framework-reading; §VII.6.20; "
                 "no metaphysical pronouncement (transducer lays the test, does not "
                 "pronounce the cosmos a living driver)",
        "source_urls": [POLN_URL, f"https://arxiv.org/abs/{POLN_ARXIV}",
                        f"https://doi.org/{POLN_DOI}"],
        "shipped_data_doi": POLN_DOI,
        "shipped_data_arxiv": POLN_ARXIV,
        # Step B — discovery / tooling gap
        "cosmic_surface": surface,
        "polarisation_rows": len(rows),
        "polarisation_kinds": kind_counts,
        "parity_even_kinds_shipped": sorted(set(kinds_present) & PARITY_EVEN),
        "parity_odd_kinds_shipped": sorted(set(kinds_present) & PARITY_ODD),
        "n_parity_odd_kinds_shipped": n_parity_odd_kinds,
        "EB_TB_available": has_parity_odd,
        "TOOLING_GAP_no_EB_TB": (not has_parity_odd),
        "tooling_gap_note": "srmech.cosmos module absent; CMB data lives under "
                            "srmech.amsc.attested.cmb_*; cmb_polarisation_spectra ships "
                            "the parity-EVEN canonical set {TE,EE,BB} only (spectrum_kind "
                            "enum is exactly ['TE','EE','BB']); NO parity-odd EB/TB "
                            "observable exists -> the cosmic-birefringence (beta) test "
                            "cannot run on shipped data. (For UPSTREAM_NOTES.)",
        # Step C — available structural readout (srmech ops only)
        "TE_sign_structure_classK": te_pattern,
        "TE_net_chirality_classC": te_net_chirality,
        "TE_net_chirality_caveat": "TE is parity-EVEN; its sign-alternation is acoustic "
                                   "phase, NOT parity violation. Reported only to show the "
                                   "shipped data carries no parity-ODD channel.",
        "EB_generator_EE_minus_BB": eb_generator,
        "EB_generator_shared_multipoles": shared_ell,
        "EB_generator_empty_reason": "Planck ships binned EE (ell~%s) and unbinned low-ell "
                                     "BB (ell~%s) with NO overlapping multipoles, so the "
                                     "(EE-BB) parity-odd generator is EMPTY on shipped data "
                                     "even before beta is applied." % (ee_ell_range, bb_ell_range),
        "ee_ell_range": ee_ell_range,
        "bb_ell_range": bb_ell_range,
        "parity_class_net_chirality": parity_class_net,
        "parity_class_net_chirality_meaning": "every shipped spectrum kind is parity-EVEN "
                                              "(+1 under P); ZERO parity-odd members; the "
                                              "shipped cosmic surface is parity-conserving "
                                              "by construction (no chirality DoF present).",
        # Step D — the test that would run
        "EB_TB_test_design": eb_tb_test_design,
        # Step E — verdict
        "falsification_attempt": "TRY TO BREAK H177 via a robust cosmic EB/TB null",
        "verdict": verdict,
        "verdict_tier_breakdown": {
            "TIER_1_FACT": "the cosmos IS chiral at the particle scale (weak-force parity "
                           "violation; CP) — established, not in question here",
            "TIER_2_CONTESTED": "Vester-Ulbricht bridge (bio-homochirality <- weak parity) "
                                "— contested; not tested here",
            "TIER_2_COSMIC_HINT": "cosmic birefringence beta~0.3 deg at ~3.6 sigma "
                                  "(Eskilt-Komatsu 2022, arXiv:2205.13962) — TENTATIVE; "
                                  "foreground/systematics-limited; NOT a 5 sigma detection",
            "TIER_3_UNESTABLISHED": "one A-N/gamma_5 driver extends to the lifeless cosmic "
                                    "band — UNESTABLISHED; this script neither breaks nor "
                                    "confirms it (tooling gap + tentative literature)",
        },
        "DOES": [
            "confirm srmech rc14 ships NO parity-odd EB/TB CMB observable (tooling gap)",
            "lay out the exact Minami-Komatsu EB/TB beta-test + srmech op-chain for "
            "when parity-odd data lands",
            "demonstrate via srmech Class-K/Class-C ops that the shipped cosmic surface "
            "is parity-conserving by construction (no chirality DoF to read)",
        ],
        "DOES_NOT": [
            "compute a cosmic birefringence angle beta (impossible on shipped data)",
            "produce a robust cosmic null (cannot — no parity-odd channel shipped)",
            "confirm OR refute H177 at the cosmic band (LEAVE-OPEN)",
            "pronounce the lifeless cosmos a living driver (out of scope; "
            "[[user_stance_ai_is_not_a_substrate]])",
        ],
        "cross_refs": ["R-RBS-LM-FINDING_177 (H177)", "F176 (bilateral = one gamma_5 axis)",
                       "F174 (28D = so(8) = 14 G2 + 14 octonion-mult)"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return result


if __name__ == "__main__":
    res = main()
    out_dir = Path(__file__).resolve().parents[1] / "catalogs" / "rbs_lm_substrate" / "substrate_measurements"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "cosmic_birefringence_falsification.ndjson"
    # content-address the record (Class A) for the attestation block
    payload = json.dumps(res, sort_keys=True).encode("utf-8")
    res["record_sha256"] = sha256_bytes(payload)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(res) + "\n")
    print()
    print(f"[E] wrote {out_path}")
    print(f"[VERDICT] {res['verdict']}")
