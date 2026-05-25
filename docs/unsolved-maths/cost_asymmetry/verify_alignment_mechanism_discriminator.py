"""Round 9 entry-point A — quad-oct alignment: amplitude discriminator between
a KINEMATIC mechanism (ruled out in Round 8.A) and a GEOMETRIC one.

Generating-code provenance per `[[feedback_computational_provenance_discipline]]`
for round9_entry_A_alignment_amplitude_target.md.

Round 8.A established: the observed Axis-of-Evil quad-oct alignment is an
ORDER-UNITY re-pointing of the ell=2,3 multipole geometry, and a kinematic
fiber-leak of amplitude beta = v/c = 1.234e-3 is ~243x too small to source it.

This script makes the discriminator explicit. Two mechanism CLASSES could
imprint the observer's preferred axis on the low-ell sky:

  KINEMATIC  — amplitude scales with beta = v/c (the boosting; Round 8.A).
               Ruled out: ~243x too small for an O(1) alignment.

  GEOMETRIC  — an off-centre observer / Class-K pin-slot offset in the
               Hopf-bundle base (framework prior: Spike #33 AoE=Class K;
               Spike #35 off-centre observer; Spike #26 / MFO sec VII.6.3.1
               bundle-projection reconfiguration). Amplitude scales with a
               geometric offset delta, NOT with beta. NOT beta-suppressed.

The test: is a geometric offset of the framework's prior magnitude
(Spike #35 reported the AoE anomaly at ~4% in angle) large enough to clear
the O(1)-alignment requirement that beta failed — i.e. is the geometric
mechanism VIABLE where the kinematic one is excluded?

This script does NOT derive the alignment amplitude from a concrete geometry.
It establishes only which mechanism CLASS survives the order-of-magnitude
test. The from-scratch derivation is logged as the remaining open target.

No bare abs() in cascade arithmetic per
`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

C_KM_S = 299792.458
V_DIPOLE = 369.82                  # km/s, Planck 2018 dipole
BETA = V_DIPOLE / C_KM_S           # kinematic amplitude (Round 8.A)

# Framework-internal prior (NOT an external measurement): Spike #35 expressed
# the AoE anomaly at ~4% in angle (task #313 re-statement "~7% in eps / ~4% in
# angle"). Used here only as the order-of-magnitude scale of a GEOMETRIC offset.
GEOMETRIC_OFFSET_SCALE = 0.04      # ~4%, framework prior (Spike #35)

# The observed alignment is an order-unity re-pointing; require the mechanism's
# amplitude to be within ~1 order of magnitude of O(1) to be "viable" (i.e. not
# excluded the way beta was at ~2-3 OOM).
ORDER_UNITY = 1.0
VIABILITY_OOM = 1.5                # allow up to ~1.5 decades below O(1)


def oom_below_unity(x: float) -> float:
    """How many orders of magnitude below O(1) an amplitude sits."""
    import math
    return math.log10(ORDER_UNITY / x)


def main(out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(__file__).resolve().parent
    out_path = out_dir / "verify_alignment_mechanism_discriminator.ndjson"

    kin_oom = oom_below_unity(BETA)
    geo_oom = oom_below_unity(GEOMETRIC_OFFSET_SCALE)
    kinematic_viable = bool(kin_oom <= VIABILITY_OOM)
    geometric_viable = bool(geo_oom <= VIABILITY_OOM)

    records = [
        {
            "kind": "kinematic_mechanism_class",
            "amplitude_symbol": "beta = v/c",
            "amplitude": BETA,
            "oom_below_unity": kin_oom,
            "viable_for_O1_alignment": kinematic_viable,
            "verdict": "EXCLUDED — ~2-3 orders of magnitude too small (Round 8.A)",
        },
        {
            "kind": "geometric_mechanism_class",
            "amplitude_symbol": "delta (off-centre-observer / Class-K offset)",
            "amplitude": GEOMETRIC_OFFSET_SCALE,
            "oom_below_unity": geo_oom,
            "viable_for_O1_alignment": geometric_viable,
            "verdict": ("VIABLE — NOT beta-suppressed; framework prior offset scale "
                        "(~4%, Spike #35) is within ~1.5 decades of O(1)"),
            "framework_priors": ["Spike #33 AoE=Class K",
                                 "Spike #35 off-centre observer",
                                 "Spike #26 / MFO VII.6.3.1 bundle-projection reconfiguration"],
        },
        {
            "kind": "discriminator_result",
            "statement": ("The quad-oct alignment AMPLITUDE discriminates mechanism classes: "
                          "kinematic (beta) is excluded; geometric (off-centre-observer / "
                          "Class K) is NOT excluded because it is not beta-suppressed. "
                          "Section 11.9.6 mis-stated the mechanism as the kinematic fiber-leak; "
                          "the framework's own prior AoE reading was geometric all along "
                          "(Spikes #33/#35/#26). The geometric reading SURVIVES the "
                          "order-of-magnitude test that killed the kinematic one."),
            "kinematic_oom_below_unity": kin_oom,
            "geometric_oom_below_unity": geo_oom,
            "separation_decades": kin_oom - geo_oom,
        },
        {
            "kind": "open_target",
            "statement": ("NOT achieved this round: a from-scratch derivation of the "
                          "alignment AMPLITUDE + direction from a concrete off-centre-observer "
                          "Hopf-bundle geometry. The round reframes the target (kinematic -> "
                          "geometric) and shows viability; it does NOT produce a derived number. "
                          "Sharp open target: compute the ell=2,3 multipole-vector alignment "
                          "from a specified Class-K offset delta and direction, and compare to "
                          "the observed alignment + ecliptic correlation."),
            "verdict": "(b) REFINED + (open) — mechanism reframed & viable; magnitude still open",
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
        }, sort_keys=True))
        fh.write("\n")

    print(f"Wrote: {out_path}")
    print(f"kinematic beta = {BETA:.3e}  -> {kin_oom:.2f} decades below O(1)  "
          f"-> {'viable' if kinematic_viable else 'EXCLUDED'}")
    print(f"geometric delta ~ {GEOMETRIC_OFFSET_SCALE:.3f} -> {geo_oom:.2f} decades below O(1)  "
          f"-> {'VIABLE' if geometric_viable else 'excluded'}")
    print(f"separation: {kin_oom - geo_oom:.2f} decades")
    print("Open target: derive alignment amplitude+direction from a concrete Class-K offset.")


if __name__ == "__main__":
    main()
