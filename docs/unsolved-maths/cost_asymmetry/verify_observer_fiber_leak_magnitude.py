"""Round 8 entry-point A — observer Hopf-fiber-leak magnitude: derivation vs data.

Generating-code provenance per `[[feedback_computational_provenance_discipline]]`
for the magnitude claims in round8_entry_A_observer_fiber_leak_magnitude_derivation.md.

§11.9.6 reads the CMB Axis-of-Evil as the "observer Hopf-fiber leak" — the
observer's motion through the substrate (the kinematic dipole = the U(1) fiber
coordinate) imprinting on the largest-scale base (temperature) projection.

The framework FIXES the leak amplitude with NO free parameter: the fiber
coordinate that leaks IS the observer's motion, of magnitude

    beta = v / c                       (v = CMB-dipole solar-system velocity)

This script tests that parameter-free magnitude against attested data on the
two distinct ways the observer's motion can imprint on low-ell:

  (a) DOPPLER BOOSTING / ABERRATION — the ell <-> ell+/-1 mode coupling.
      Standard kinematic effect; amplitude ~ beta. Measured by Planck 2013
      (arXiv:1303.5087) at v_boost = 384 +/- 78 (stat) +/- 115 (sys) km/s,
      direction (l,b) = (264,48) deg.

  (b) QUADRUPOLE-OCTUPOLE ALIGNMENT (the Axis of Evil proper) — an
      order-unity re-pointing of where the ell=2,3 power sits, toward the
      dipole/ecliptic. de Oliveira-Costa+ 2004; Schwarz+ 2016 (arXiv:1510.07929).

The honest question: does the SINGLE parameter-free magnitude beta account for
BOTH (a) and (b), or only one? No bare abs() in cascade arithmetic per
`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`; numpy.hypot used
for error combination is a magnitude readout, not sign-handling.

Attested inputs (open-access; per `[[feedback_paywalled_doi_cannot_be_attested]]`):
  - v_dipole = 369.82 +/- 0.11 km/s   (Planck 2018; arXiv abstract values)
  - v_boost  = 384 +/- 78 +/- 115 km/s (Planck 2013 results XXVII; arXiv:1303.5087)
  - c        = 299792.458 km/s         (exact, SI definition)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

C_KM_S = 299792.458          # speed of light, km/s (exact)
V_DIPOLE = 369.82            # km/s, Planck 2018 CMB-dipole solar velocity
V_DIPOLE_ERR = 0.11         # km/s
V_BOOST = 384.0             # km/s, Planck 2013 boosting-only measurement
V_BOOST_STAT = 78.0         # km/s
V_BOOST_SYS = 115.0         # km/s


def main(out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(__file__).resolve().parent
    out_path = out_dir / "verify_observer_fiber_leak_magnitude.ndjson"

    # ---- Parameter-free framework prediction: leak amplitude = beta = v/c ----
    beta = V_DIPOLE / C_KM_S
    beta_err = V_DIPOLE_ERR / C_KM_S

    # ---- Channel (a): Doppler boosting. Predicted amplitude ~ beta; measured. ----
    # Consistency of the boosting-measured velocity with the dipole velocity.
    v_boost_err = float(np.hypot(V_BOOST_STAT, V_BOOST_SYS))   # combined error
    delta_v = V_BOOST - V_DIPOLE
    # tension in sigma (Class N rational readout of a magnitude; not sign-handling)
    sigma_tension = delta_v / v_boost_err
    boosting_consistent = bool(np.hypot(sigma_tension, 0.0) < 2.0)

    # ---- Channel (b): quad-oct alignment. It is an ORDER-UNITY re-pointing. ----
    # A kinematic modulation of amplitude beta produces fractional a_lm changes
    # of order beta. To re-point the ell=2,3 multipole vectors into the observed
    # alignment requires an order-unity rearrangement, ~O(0.1-1). The gap:
    alignment_order = 0.3   # representative order-unity scale of the AoE re-pointing
    magnitude_gap = alignment_order / beta   # how many x too small beta is
    beta_can_explain_alignment = bool(magnitude_gap < 3.0)  # within factor ~3?

    records = [
        {
            "kind": "framework_parameter_free_prediction",
            "claim": "observer Hopf-fiber-leak amplitude = beta = v/c (no free parameter)",
            "v_dipole_km_s": V_DIPOLE,
            "beta": beta,
            "beta_err": beta_err,
        },
        {
            "kind": "channel_a_doppler_boosting",
            "claim": "ell<->ell+/-1 coupling amplitude ~ beta; observer-motion imprint",
            "v_boost_km_s": V_BOOST,
            "v_boost_combined_err_km_s": v_boost_err,
            "v_dipole_km_s": V_DIPOLE,
            "tension_sigma": sigma_tension,
            "consistent_within_2sigma": boosting_consistent,
            "verdict": "(a)-CONFIRMED: parameter-free beta matches attested boosting measurement",
            "source": "Planck 2013 results XXVII, arXiv:1303.5087",
        },
        {
            "kind": "channel_b_quad_oct_alignment",
            "claim": "AoE quad-oct alignment is an order-unity multipole-vector re-pointing",
            "beta": beta,
            "alignment_order_unity_scale": alignment_order,
            "magnitude_gap_factor": magnitude_gap,
            "beta_can_explain_alignment": beta_can_explain_alignment,
            "verdict": ("(b)-REFUTED at magnitude beta: a ~1e-3 kinematic modulation is "
                        "~%.0fx too small to produce the order-unity alignment" % magnitude_gap),
            "source": "de Oliveira-Costa+ 2004; Schwarz+ 2016 arXiv:1510.07929",
        },
        {
            "kind": "framework_reading_refinement",
            "statement": ("The parameter-free fiber-leak magnitude beta=v/c CONFIRMS the "
                          "Doppler-boosting channel (observer motion imprints on low-ell at "
                          "beta, matching Planck 2013) but is ~3 orders of magnitude too small "
                          "to source the quad-oct alignment. Therefore the AoE reading of "
                          "section 11.9.6 must be SPLIT: boosting = confirmed fiber-leak at beta "
                          "(lifts toward (a)); quad-oct alignment = a distinct anomaly NOT "
                          "accounted for by the beta-magnitude fiber-leak (stays open)."),
            "verdict": "(b) REFINED — partial (a) on boosting; alignment remains open",
        },
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True))
            fh.write("\n")

    ndjson_sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "kind": "provenance_attestation",
            "ndjson_path": out_path.name,
            "ndjson_sha256_hex_pre_attestation": ndjson_sha,
            "generated_by": Path(__file__).name,
            "numpy_version": np.__version__,
        }, sort_keys=True))
        fh.write("\n")

    print(f"Wrote: {out_path}")
    print(f"beta = v/c = {beta:.6e}  (v = {V_DIPOLE} km/s)")
    print(f"(a) Doppler boosting: v_boost = {V_BOOST} +/- {v_boost_err:.0f} km/s; "
          f"tension = {sigma_tension:.2f} sigma -> {'CONSISTENT' if boosting_consistent else 'TENSION'}")
    print(f"(b) quad-oct alignment: beta is ~{magnitude_gap:.0f}x too small "
          f"-> {'OK' if beta_can_explain_alignment else 'CANNOT explain alignment'}")


if __name__ == "__main__":
    main()
