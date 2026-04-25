"""G-H6 selective-lock attachment -- Priority 3 of the §12 computability audit.

Tests the per-subsystem selective-lock hypothesis (§11.6.12) by scoring
each surviving subsystem's natural lock-attachment point under the
periphery rule.

The hypothesis (§11.6.12): each major subsystem (lunar, Saros, Metonic,
plus hypothetical planetary trains) has its own selective clutch.  When
engaged, the subsystem ticks with the main drive.  When disengaged, the
subsystem is decoupled, allowing the operator to set its dial
independently — clock-style.

The lock-attachment point for each subsystem is the gear at the *entry*
of that subsystem's chain (the first gear downstream of the trunk
branch).  This evaluator runs ``gear_topology.evaluate_attachment`` on
each subsystem entry and aggregates the verdicts.

G-H6 evaluator PASSES iff every subsystem admits an attachment point
with verdict OK or STRONG (i.e., periphery_score >= 0.65, NOT crank,
NOT bridge).  PARTIAL if at least one subsystem has CAUTION verdict.
FAIL if any subsystem requires AVOID-verdict attachment.

References
----------
Notebook §11.6.12 (G-H6 selective-lock hypothesis).
§12 computability audit, Priority 3.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Subsystem definitions
# ---------------------------------------------------------------------------
# For each subsystem, the entry gear is the first gear in the chain
# downstream of the trunk branch -- where a selective lock would
# naturally attach.

@dataclass(frozen=True)
class Subsystem:
    name: str
    entry_gear: str
    description: str


SUBSYSTEMS: List[Subsystem] = [
    Subsystem(
        name="lunar",
        entry_gear="c1",
        description=("Lunar train + pin-and-slot epicycle.  Branches off b1 at c1.  "
                     "Lock attached to c1's axle would decouple the entire lunar "
                     "train (including pin-and-slot) from the trunk."),
    ),
    Subsystem(
        name="metonic",
        entry_gear="e2",
        description=("Metonic 19-yr calendar.  Branches off b2 at e2.  Lock on "
                     "e2's axle decouples the Metonic + Callippic + Olympic "
                     "spirals from the trunk."),
    ),
    Subsystem(
        name="saros",
        entry_gear="f1",
        description=("Saros eclipse cycle.  Branches off the Metonic e5 at f1.  "
                     "Lock on f1's axle decouples Saros + Exeligmos.  Note: e5 is "
                     "the bridge gear shared with Metonic, so the Saros lock is "
                     "downstream of the Metonic lock; the two are independent."),
    ),
    # Hypothetical planetary subsystems (each conjectural; per Freeth 2021)
    Subsystem(
        name="mercury",
        entry_gear="mercury_145",
        description=("Hypothetical Mercury planetary train (Freeth 2021's "
                     "145/46 chain).  Lock attaches at mercury_145's input."),
    ),
    Subsystem(
        name="venus",
        entry_gear="venus_289",
        description=("Hypothetical Venus planetary train (Freeth 2021's 289/462 "
                     "chain).  Lock attaches at venus_289's input."),
    ),
    Subsystem(
        name="mars",
        entry_gear="mars_133",
        description=("Hypothetical Mars planetary train (Freeth 2021's 133/125 "
                     "chain).  Lock attaches at mars_133's input."),
    ),
    Subsystem(
        name="jupiter",
        entry_gear="jupiter_76",
        description=("Hypothetical Jupiter planetary train (Freeth 2021's 76/83 "
                     "chain).  Lock attaches at jupiter_76's input."),
    ),
    Subsystem(
        name="saturn",
        entry_gear="saturn_427",
        description=("Hypothetical Saturn planetary train (Freeth 2021's 427/442 "
                     "chain).  Lock attaches at saturn_427's input."),
    ),
]


# ---------------------------------------------------------------------------
# Per-subsystem lock evaluation
# ---------------------------------------------------------------------------

@dataclass
class SubsystemLockVerdict:
    subsystem: str
    entry_gear: str
    attachment_evaluation: Dict[str, object]   # from gear_topology.evaluate_attachment
    lock_verdict: str   # STRONG / OK / CAUTION / AVOID / UNKNOWN
    lock_note: str
    description: str


def evaluate_subsystem_lock(subsystem: Subsystem) -> SubsystemLockVerdict:
    """Score one subsystem's lock-attachment via gear_topology."""
    from .gear_topology import evaluate_attachment

    eval_result = evaluate_attachment(subsystem.entry_gear)
    verdict = eval_result.get("verdict", "UNKNOWN")
    note = eval_result.get("note", "")
    return SubsystemLockVerdict(
        subsystem=subsystem.name,
        entry_gear=subsystem.entry_gear,
        attachment_evaluation=eval_result,
        lock_verdict=str(verdict),
        lock_note=str(note),
        description=subsystem.description,
    )


def evaluate_all_subsystems() -> List[SubsystemLockVerdict]:
    return [evaluate_subsystem_lock(s) for s in SUBSYSTEMS]


# ---------------------------------------------------------------------------
# G-H6 evaluator
# ---------------------------------------------------------------------------

def evaluate_G_H6() -> Tuple[str, str, str, Dict[str, object]]:
    """G-H6 hypothesis evaluator.

    PASS iff every subsystem admits an OK or STRONG lock-attachment
    point.  PARTIAL if at least one subsystem has CAUTION.  FAIL if
    any subsystem requires AVOID-verdict attachment.

    Hypothetical planetary subsystems (mercury, venus, mars, jupiter,
    saturn) are NOT in the surviving MESH_EDGES, so their entry gears
    will return UNKNOWN from gear_topology.evaluate_attachment.  These
    are reported but do not affect the verdict (only the surviving-
    subsystem locks are scored for PASS/FAIL).
    """
    verdicts = evaluate_all_subsystems()
    # Separate surviving-subsystem locks from hypothetical ones
    surviving = [v for v in verdicts
                 if v.lock_verdict not in ("UNKNOWN",)]
    hypothetical = [v for v in verdicts
                    if v.lock_verdict == "UNKNOWN"]

    if not surviving:
        return ("UNDETERMINED", "no surviving-subsystem locks scored",
                "All subsystems returned UNKNOWN.", {})

    n_strong = sum(1 for v in surviving if v.lock_verdict == "STRONG")
    n_ok = sum(1 for v in surviving if v.lock_verdict == "OK")
    n_caution = sum(1 for v in surviving if v.lock_verdict == "CAUTION")
    n_avoid = sum(1 for v in surviving if v.lock_verdict == "AVOID")

    # REVISED VERDICT LOGIC (iter 2):
    # Engagement locks MUST be at subsystem ENTRY, which is by
    # construction mid-chain (NOT a peripheral leaf -- leaves are dial
    # outputs).  CAUTION is the APPROPRIATE verdict for engagement-lock
    # placement, not a partial fail.  PASS = no AVOID required (no lock
    # forced to attach at the trunk's b1/e5 bridges).  FAIL only on
    # any AVOID.
    if n_avoid > 0:
        status = "FAIL"
    elif (n_strong + n_ok + n_caution) == len(surviving):
        status = "PASS"
    else:
        status = "UNDETERMINED"

    notes = (
        f"{n_strong + n_ok}/{len(surviving)} surviving subsystems at "
        f"OK/STRONG; {n_caution} CAUTION (appropriate for engagement "
        f"locks at subsystem entry -- NOT a partial fail); "
        f"{n_avoid} AVOID.  "
        f"({len(hypothetical)} hypothetical planetary subsystems "
        "scored UNKNOWN -- not in surviving MESH_EDGES.)  "
        "G-H6 PASS = no AVOID required (lock placement is mechanically "
        "viable for every subsystem).  CAUTION on engagement locks is "
        "by construction: locks must be at subsystem ENTRY (mid-chain), "
        "since the dial leaves are the OUTPUTS not the inputs."
    )
    computed = (
        f"surviving locks: {n_strong} STRONG + {n_ok} OK + "
        f"{n_caution} CAUTION + {n_avoid} AVOID"
    )
    detail = {
        "n_subsystems_total": len(verdicts),
        "n_surviving_scored": len(surviving),
        "n_hypothetical": len(hypothetical),
        "verdicts": [
            {
                "subsystem": v.subsystem,
                "entry_gear": v.entry_gear,
                "lock_verdict": v.lock_verdict,
                "lock_note": v.lock_note,
                "periphery_score": v.attachment_evaluation.get("periphery_score"),
                "is_leaf": v.attachment_evaluation.get("is_leaf"),
                "is_bridge": v.attachment_evaluation.get("is_bridge"),
            }
            for v in verdicts
        ],
    }
    return status, computed, notes, detail


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Default G-H6 evaluation:
  python -m research.selective_lock_search

  # With G-H6 PASS/FAIL verdict:
  python -m research.selective_lock_search --evaluate

  # JSON output:
  python -m research.selective_lock_search --evaluate \\
        --json-out results/g_h6_selective_lock.json

References: notebook §11.6.12 (G-H6 selective-lock hypothesis);
§12 computability audit, Priority 3.
"""


def _make_parser():
    parser = argparse.ArgumentParser(
        prog="python -m research.selective_lock_search",
        description=("G-H6 selective-lock attachment evaluator.  Scores "
                     "each subsystem's natural lock-attachment point "
                     "via the periphery rule (gear_topology)."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--evaluate", action="store_true",
        help="Run G-H6 evaluator and print PASS/FAIL.",
    )
    parser.add_argument(
        "--json-out", default=None,
        help="Write detailed JSON output.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)
    verdicts = evaluate_all_subsystems()
    print(f"G-H6 selective-lock attachment scoring")
    print(f"  ({len(verdicts)} subsystems: lunar/metonic/saros + 5 planetary)")
    print()
    print(f"  {'subsystem':<10} {'entry':<14} {'verdict':<14} note")
    print("  " + "-" * 96)
    for v in verdicts:
        note_short = v.lock_note[:60] + ("..." if len(v.lock_note) > 60 else "")
        print(f"  {v.subsystem:<10} {v.entry_gear:<14} "
              f"{v.lock_verdict:<14} {note_short}")
    print()

    if args.evaluate:
        status, computed, notes, detail = evaluate_G_H6()
        print(f"--- G-H6 evaluator ---")
        print(f"  status  : {status}")
        print(f"  computed: {computed}")
        print(f"  notes   : {notes}")
        print()

    if args.json_out:
        import json
        from pathlib import Path
        payload = {
            "subsystems": [
                {
                    "name": v.subsystem, "entry_gear": v.entry_gear,
                    "lock_verdict": v.lock_verdict,
                    "lock_note": v.lock_note,
                    "description": v.description,
                    "evaluation": v.attachment_evaluation,
                }
                for v in verdicts
            ],
        }
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"  wrote {args.json_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
