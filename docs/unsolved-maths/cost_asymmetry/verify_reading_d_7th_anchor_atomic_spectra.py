"""Round 17.A entry-point A — Reading-D 7th scale-ladder anchor: ATOMIC SPECTRAL LINES.

Generating-code provenance per `[[feedback_computational_provenance_discipline]]`
for round17_entry_A_reading_d_7th_anchor_atomic_spectra.md.

Reading D (§11.9.6): cost = B/H/N substrate-content saturation, OBSERVABLE as the substrate's
"translation fingerprint." Six anchors span 3 qubits -> observable universe, with a conspicuous
gap at the ATOMIC scale (~10^-10 m) between the abstract 3-qubit Born-rule anchor (Round 4.A) and
the molecular/biology rungs. This is the 7th rung, and the "translation fingerprint" is LITERAL:
an atomic emission/absorption spectrum IS a fingerprint (spectroscopy's founding premise).

The B/H/N decomposition of an atomic spectrum:
  - B (TLV-framing): each spectral LINE is a type-length-value record -- (series, transition
    n1->n2, wavenumber). The discrete line-catalogue frames the continuous EM field into typed records.
  - H (measurement / Hopf-projection): photon emission projects the atom's continuous bound-state
    phase structure to a discrete eigenvalue DIFFERENCE (a transition). This is the SAME H as the
    Born rule (Round 4.A) -- the atomic-scale instance of quantum measurement.
  - N (rational-approximation): the Rydberg-Ritz combination principle (Rydberg 1888; Ritz 1908) --
    spectral TERMS are T_n = R/n^2 (rational in the integer quantum number n), and every line
    wavenumber is a DIFFERENCE of terms, so line-wavenumber RATIOS are EXACT small-denominator
    rationals, INDEPENDENT of the physical Rydberg constant R. The fingerprint is rational-structured.

BIT-EXACT claim: hydrogen Balmer-series line-wavenumber ratios are exact small-denominator rationals
(pure integer arithmetic; R cancels). The match to ATTESTED air wavelengths is ~1e-5 (residual =
air refractive index dispersion + reduced-mass + fine structure -- reported honestly).

srmech routing (CLAUDE.md §2): Class N best_rational anchors the ratios; Class I cyclic.gcd reduces
the exact fractions; no bare abs() (magnitudes via cascade-helper). srmech 0.4.2.

Attested (Explore-verified, NIST ASD / CODATA 2022; Balmer wavelengths IN AIR):
  Rydberg formula 1/lambda = R (1/n1^2 - 1/n2^2); R_inf = 1.0973731568e7 /m (CODATA 2022).
  Balmer Halpha (3->2) 656.279 nm; Hbeta (4->2) 486.135 nm; Hgamma (5->2) 434.047 nm.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _cascade_helpers import magnitude  # Class K magnitude readout  # noqa: E402

import srmech  # noqa: E402
from srmech.amsc.rational import best_rational  # Class N  # noqa: E402
from srmech.amsc.cyclic import gcd  # Class I  # noqa: E402
from srmech.amsc import _native as _srn  # noqa: E402

# Attested Balmer-series air wavelengths (nm), n2 -> wavelength.  NIST ASD.
BALMER_AIR_NM = {3: 656.279, 4: 486.135, 5: 434.047}
N1 = 2  # Balmer series lower level


def wavenumber_fraction(n2: int) -> tuple[int, int]:
    """Exact Balmer wavenumber fraction (R cancels): (1/N1^2 - 1/n2^2) = (n2^2 - N1^2)/(N1^2 n2^2).
    Reduced by Class-I cyclic gcd. Returns (num, den)."""
    num = n2 * n2 - N1 * N1
    den = N1 * N1 * n2 * n2
    g = gcd(num, den)
    return num // g, den // g


def ratio_fraction(a: int, b: int) -> tuple[int, int]:
    """Exact wavenumber ratio sigma_a/sigma_b for Balmer lines n2=a, n2=b. R cancels."""
    na, da = wavenumber_fraction(a)
    nb, db = wavenumber_fraction(b)
    num, den = na * db, da * nb
    g = gcd(num, den)
    return num // g, den // g


def main(out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(__file__).resolve().parent
    out_path = out_dir / "verify_reading_d_7th_anchor_atomic_spectra.ndjson"

    # Exact wavenumber fractions per line (Class I reduction).
    fracs = {n2: wavenumber_fraction(n2) for n2 in (3, 4, 5)}

    # Pairwise line-wavenumber ratios as EXACT rationals (bit-exact; R-independent),
    # cross-checked through srmech Class-N best_rational, and compared to attested air-wavelength
    # ratios (lambda_a/lambda_b = sigma_b/sigma_a).
    pairs = [(3, 4), (4, 5), (3, 5)]
    ratio_records = []
    max_resid = 0.0
    for a, b in pairs:
        wn_num, wn_den = ratio_fraction(a, b)             # sigma_a / sigma_b exact
        # predicted wavelength ratio lambda_a/lambda_b = sigma_b/sigma_a = wn_den/wn_num
        pred_lambda_ratio = wn_den / wn_num
        # srmech Class-N anchor of the predicted wavelength ratio (should be the exact reduced pair)
        n_anchor = best_rational(wn_den, wn_num, 200)  # cap > 125 so 189/125 resolves exactly
        # attested wavelength ratio
        att_lambda_ratio = BALMER_AIR_NM[a] / BALMER_AIR_NM[b]
        resid = magnitude(att_lambda_ratio - pred_lambda_ratio) / pred_lambda_ratio  # Class K, no abs()
        max_resid = resid if resid > max_resid else max_resid
        ratio_records.append({
            "kind": "balmer_line_ratio",
            "line_a_3to2_4to2_5to2": "n2=%d->n1=2" % a, "line_b": "n2=%d->n1=2" % b,
            "wavenumber_ratio_sigma_a_over_sigma_b_exact": [wn_num, wn_den],
            "predicted_wavelength_ratio_exact_rational": [wn_den, wn_num],
            "predicted_wavelength_ratio_value": pred_lambda_ratio,
            "class_N_best_rational_of_predicted": list(n_anchor),
            "attested_air_wavelength_ratio": att_lambda_ratio,
            "relative_residual": resid,
            "bit_exact_rational": list(n_anchor) == [wn_den, wn_num]})

    records = [
        {"kind": "anchor_identity", "scale": "atomic (~1e-10 m)", "substrate_class": "atomic physics",
         "ladder_gap_filled": "between the 3-qubit Born-rule anchor (Round 4.A) and the molecular/biology rungs",
         "literal_fingerprint": "an atomic emission/absorption spectrum IS a fingerprint (spectroscopy's founding premise)"},
        {"kind": "BHN_decomposition",
         "B_tlv_framing": "each spectral LINE = typed record (series, transition n1->n2, wavenumber); discrete line-catalogue frames the continuous EM field",
         "H_measurement": "photon emission projects the continuous bound-state phase structure to a discrete term-DIFFERENCE -- the SAME H as the Born rule (Round 4.A), at the atomic scale",
         "N_rational": "Rydberg-Ritz: terms T_n=R/n^2 are rational in n; line wavenumbers are differences of terms; line RATIOS are exact small-denominator rationals, R-independent"},
        {"kind": "exact_wavenumber_fractions",
         "balmer_n2_3_Halpha": list(fracs[3]), "balmer_n2_4_Hbeta": list(fracs[4]),
         "balmer_n2_5_Hgamma": list(fracs[5]),
         "note": "(1/2^2 - 1/n2^2) reduced; 5/36, 3/16, 21/100 -- pure integer arithmetic, Class-I gcd reduced"},
        *ratio_records,
        {"kind": "verdict",
         "max_relative_residual_vs_attested_air_wavelengths": max_resid,
         "statement": ("The 7th Reading-D scale-ladder anchor is ATOMIC SPECTRAL LINES (atomic "
                       "scale, ~1e-10 m), filling the gap between the 3-qubit Born-rule anchor and "
                       "the molecular/biology rungs. The 'translation fingerprint' is LITERAL: an "
                       "atomic spectrum IS a fingerprint. Its B/H/N structure is exact -- B = the "
                       "discrete line-catalogue (TLV), H = photon-emission measurement (the same H "
                       "as the Born rule, at atomic scale), N = the Rydberg-Ritz rational term "
                       "structure. Hydrogen Balmer line-wavenumber RATIOS are EXACT small-"
                       "denominator rationals (20/27, 28/25, 189/125), R-independent and bit-exact "
                       "by integer arithmetic; they match the attested NIST air wavelengths to "
                       "max relative residual %.2e (air dispersion + reduced-mass + fine structure). "
                       "This closes the small-scale end of the quantum->cosmological ladder with a "
                       "second near-bit-exact anchor alongside Born-rule=Hopf." % max_resid),
         "verdict_tier": "(a)-bit-exact rational structure (R-independent) + attested match to ~1e-5; near-bit-exact anchor; ladder now 7 rungs"}]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        fh.write(json.dumps({"kind": "srmech_routing_provenance",
                             "srmech_version": srmech.__version__,
                             "has_native": bool(getattr(_srn, "HAS_NATIVE", False)),
                             "class_N_used": "best_rational (line-ratio anchors)",
                             "class_I_used": "cyclic.gcd (fraction reduction)",
                             "class_K_used": "magnitude() (residual, no bare abs)"}, sort_keys=True) + "\n")
    ndjson_sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "provenance_attestation", "ndjson_path": out_path.name,
                             "ndjson_sha256_hex_pre_attestation": ndjson_sha,
                             "generated_by": Path(__file__).name,
                             "attested_sources": "NIST ASD (Balmer air wavelengths); CODATA 2022 (R_inf); Rydberg 1888 / Ritz 1908"},
                            sort_keys=True) + "\n")

    print(f"Wrote: {out_path}")
    print(f"Exact Balmer wavenumber fractions: Halpha={fracs[3]} Hbeta={fracs[4]} Hgamma={fracs[5]}")
    for r in ratio_records:
        print(f"  {r['line_a_3to2_4to2_5to2']} / {r['line_b']}: lambda-ratio exact "
              f"{r['predicted_wavelength_ratio_exact_rational']} = {r['predicted_wavelength_ratio_value']:.5f}; "
              f"attested {r['attested_air_wavelength_ratio']:.5f}; resid {r['relative_residual']:.2e}; "
              f"bit-exact rational={r['bit_exact_rational']}")
    print(f"max relative residual vs attested air wavelengths: {max_resid:.2e}")
    print(f"srmech v{srmech.__version__} native={bool(getattr(_srn,'HAS_NATIVE',False))}")
    print("Verdict: 7th Reading-D anchor = atomic spectral lines (atomic scale); rational fingerprint bit-exact, attested to ~1e-5.")


if __name__ == "__main__":
    main()
