"""Correct hand-curated Hellenistic anchor JDs using DE422.

For each anchor in ``hellenistic_eclipses.HELLENISTIC_ANCHORS``, search
DE422 for the nearest syzygy of the matching eclipse type within
+-16 days of the hand-curated JD.  Print the correction table.

Run from docs/antikythera-maths:
    python scripts/correct_hellenistic_anchors.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running this script from docs/antikythera-maths/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from research.hellenistic_eclipses import HELLENISTIC_ANCHORS
    from research.sky_driven_validation import infer_anchor_jd_from_date

    print("Correcting hand-curated Hellenistic anchor JDs via DE422")
    print("=" * 78)
    print()
    print(f"{'date_iso':>14} {'type':>5}  {'nominal JD':>12}  "
          f"{'corrected':>12}  {'shift_d':>8}  {'phase':>7}")
    print("-" * 78)

    corrections = []
    for anc in HELLENISTIC_ANCHORS:
        result = infer_anchor_jd_from_date(
            nominal_jd=anc.jd,
            eclipse_type=anc.eclipse_type,
            tolerance_days=16.0,
            kernel="de422",
        )
        if result is None:
            print(f"{anc.date_iso:>14} {anc.eclipse_type:>5}  "
                  f"{anc.jd:>12.1f}  {'NO MATCH':>12}  "
                  f"{'n/a':>8}  {'n/a':>7}")
            continue
        shift = result["shift_days"]
        phase = result["phase_deg"]
        corrections.append({
            "almagest_ref": anc.almagest_ref,
            "date_iso": anc.date_iso,
            "type": anc.eclipse_type,
            "nominal_jd": anc.jd,
            "corrected_jd": result["corrected_jd"],
            "shift_days": shift,
            "phase_deg": phase,
        })
        print(f"{anc.date_iso:>14} {anc.eclipse_type:>5}  "
              f"{anc.jd:>12.1f}  {result['corrected_jd']:>12.3f}  "
              f"{shift:>+8.3f}  {phase:>7.2f}")

    print()
    print("Use these corrected_jd values to update HELLENISTIC_ANCHORS in")
    print("research/hellenistic_eclipses.py.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
