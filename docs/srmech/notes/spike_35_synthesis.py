"""Spike #35 — synthesis NDJSON: combine all verdicts into a single rollup record."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    in_dir = Path("D:/temp/spike_35")
    out_path = in_dir / "spike_35_synthesis.ndjson"

    files = [
        "spike_35_q1_brouwer_clemence.ndjson",
        "spike_35_q2_signflip_asymmetry.ndjson",
        "spike_35_q3_galactic_itn_v2.ndjson",
        "spike_35_integrated.ndjson",
        "spike_35_falsifier_tests.ndjson",
    ]

    records: list[dict] = []
    records.append({
        "spike": 35, "kind": "meta",
        "title": "Spike #35 — Q1+Q2+Q3 synthesis: downstream consequences of AoE off-centre-observer reading",
        "files_aggregated": files,
        "claim": ("AoE direction = our observer-frame radial offset at eps = 0.0506 produces "
                  "three reinforcing downstream consequences: (Q1) Brouwer-Clemence c_k = eps^k "
                  "modulation in kinematic spectra; (Q2) sign-flip phase asymmetry at apse "
                  "projection; (Q3) Fiedler-partition-applicable structure at cosmic-web scale"),
    })

    # Collect verdicts
    for fname in files:
        with (in_dir / fname).open("r") as f:
            for line in f:
                rec = json.loads(line.strip())
                if rec.get("kind") in ("verdict", "verdict_v2", "integrated_verdict",
                                        "falsifier_verdict"):
                    records.append(rec)

    # Top-level rollup
    q1_pass = next((r["Q1_overall_pass"] for r in records
                     if r.get("question") == "Q1" and r.get("kind") == "verdict"), False)
    q2_pass = next((r["Q2_overall_pass"] for r in records
                     if r.get("question") == "Q2" and r.get("kind") == "verdict"), False)
    q3_pass = next((r["Q3_overall_pass"] for r in records
                     if r.get("question") == "Q3" and r.get("kind") == "verdict_v2"), False)
    integrated_pass = next((r["integrated_reinforcement"] for r in records
                             if r.get("kind") == "integrated_verdict"), False)
    falsifier_pass = next((r["all_pass"] for r in records
                            if r.get("kind") == "falsifier_verdict"), False)

    print("=" * 80)
    print("Spike #35 ROLLUP")
    print("=" * 80)
    print(f"  Q1 PASS: {q1_pass}")
    print(f"  Q2 PASS: {q2_pass}")
    print(f"  Q3 PASS: {q3_pass}")
    print(f"  Integrated reinforcement: {integrated_pass}")
    print(f"  Falsifier tests (F1+F2+F3): {falsifier_pass}")

    records.append({
        "spike": 35, "kind": "ROLLUP",
        "Q1_pass": q1_pass,
        "Q2_pass": q2_pass,
        "Q3_pass": q3_pass,
        "integrated_reinforcement": integrated_pass,
        "falsifier_all_pass": falsifier_pass,
    })

    with out_path.open("w") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"\nWrote {len(records)} NDJSON records to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
