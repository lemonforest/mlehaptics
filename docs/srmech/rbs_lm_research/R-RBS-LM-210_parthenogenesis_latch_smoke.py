#!/usr/bin/env python3
"""R-RBS-LM-210 — parthenogenesis cascade: the LATCHING self-trigger (Class K) +
handedness (Class C), demonstrated on the shipped srmech cascade surface.

Finding 210 reads the minimal parthenogenetic-development trigger (egg activation
WITHOUT fertilization: a self-initiated Ca2+ wave/oscillation -> completion of
meiosis II -> diploidy restoration -> cell-cycle resumption) as an abstract
**self-initiated symmetry-break / autocatalytic completion that needs no external
trigger**. This smoke makes the A-N reading DEMONSTRATED rather than asserted:

  (K) the self-trigger is a Class K pin-slot zero-crossing that LATCHES — a control
      variable (the activation signal minus its threshold) crosses zero ONCE; the
      orientation it lands in is the commitment, and once committed the cascade does
      not return across the zero (the all-or-none egg-activation step; Whitaker 2006).
  (C) the developmental handedness is the Class C net orientation of the cascade
      (the product of per-stage orientations) — biology's single homochiral axis
      (F176: one gamma_5 axis read at two poles), conserved through the run.

srmech-first: pin_slot_at_zero (Class K), reorient / net_chirality (Class C),
magnitude (never python abs()). No numpy, no eig, no hashlib. This is a
demonstration of the ALREADY-SHIPPED cascade ops, not new mathematics.

Run:  <venv>/bin/python3 R-RBS-LM-210_parthenogenesis_latch_smoke.py
Check: <venv>/bin/python3 check_srmech_discipline.py R-RBS-LM-210_parthenogenesis_latch_smoke.py  -> 0 HARD
"""
from __future__ import annotations

import json

from srmech.amsc import cascade as C


def latched_self_trigger(signal_minus_threshold):
    """Class K: feed a rising activation track (signal minus its threshold) through the
    pin-slot at zero. The track starts BELOW threshold (orientation -1 = the resting,
    pre-trigger egg) and is driven UP by the egg's own machinery.

    Returns (committed_orientation, first_crossing_index, latched). Commitment is the
    pin clearing INTO the development slot — the FIRST upward crossing to orientation
    +1. The 'latch' is the one-way property: once committed to +1, the track does not
    return to -1. This is the all-or-none commitment of egg activation (Whitaker 2006,
    Physiol Rev 86:25): the Ca2+ transient is sufficient to drive the whole activation
    program; the system does not slide back across the zero.
    """
    committed = 0
    first_idx = None
    latched = True
    for i, x in enumerate(signal_minus_threshold):
        orientation, _mag = C.pin_slot_at_zero(x)  # Class K: (sign in {-1,0,+1}, magnitude)
        if committed == 0 and orientation > 0:
            committed = orientation          # pin clears into the development slot (+1)
            first_idx = i
        elif committed > 0 and orientation < 0:
            latched = False                  # crossed back below threshold -> NOT a latch
    return committed, first_idx, latched


def cascade_handedness(stage_orientations):
    """Class C: the net handedness of the committed cascade = product of per-stage
    orientations (srmech.amsc.cascade.net_chirality). One conserved sign — biology's
    single homochiral axis (F176), not two independent mirror copies."""
    return C.net_chirality(stage_orientations)


def main():
    # A self-initiated activation track: starts BELOW threshold (negative), the egg's
    # own machinery (osmotic/mechanical entry cue in Drosophila; PLCzeta-driven Ca2+ in
    # mammals) drives it UP through the threshold, then it stays above. The external
    # 'trigger' (sperm) is ABSENT — the crossing is self-initiated.
    activation_track = [-1.50, -0.75, -0.20, +0.05, +0.60, +1.20, +1.20, +1.20]
    committed, first_idx, latched = latched_self_trigger(activation_track)

    # Per-stage orientations of the committed developmental cascade. All same sign =
    # one homochiral axis carried through (Ca2+ wave -> meiosis-II completion ->
    # diploidy restoration -> cell-cycle resumption). net = product (Class C).
    stage_orientations = [committed, committed, committed, committed]
    net = cascade_handedness(stage_orientations)

    # Magnitude of the post-commit drive, via the Class K split (NOT python abs()).
    _o, drive_mag = C.pin_slot_at_zero(activation_track[-1])

    # Falsifier check (in-script): a NON-latching track that crosses back would NOT
    # commit (latched == False). Egg activation is empirically all-or-none, so the
    # latching model is the apt one; a freely-reversible crossing would falsify it.
    reversible_track = [-1.0, +0.5, -0.5, +0.5, -0.5]
    _c2, _i2, latched2 = latched_self_trigger(reversible_track)

    out = {
        "finding": "R-RBS-LM-210",
        "claim": "parthenogenesis self-trigger = Class K pin-slot zero-crossing that LATCHES; handedness = Class C net orientation",
        "activation_track": activation_track,
        "committed_orientation_K": committed,          # +1: committed to the development side
        "first_crossing_index": first_idx,             # the single zero-crossing (the activation event)
        "latched_one_way": latched,                    # True: once crossed, stays committed (all-or-none)
        "stage_orientations": stage_orientations,
        "net_handedness_C": net,                        # +1: one conserved homochiral axis (F176)
        "post_commit_drive_magnitude": drive_mag,       # via Class K split, not abs()
        "reversible_control_latched": latched2,         # False: a crossing-back track does NOT latch (the falsifier shape)
        "srmech_version": __import__("srmech").__version__,
        "ops_used": ["cascade.pin_slot_at_zero (K)", "cascade.net_chirality (C)"],
        "tier": "DEMONSTRATED (shipped srmech ops; reading of biology stays framework-reading)",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
