"""
Spike #43b — Apply the substructural analysis to the real-world mixed-quality substrates.

Uses the same M1-M6 toolchain from spike_43b_substructural_analysis.py.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

# Import the analyser module from this directory
sys.path.insert(0, r"D:\temp\spike_43b")
from spike_43b_substructural_analysis import (  # type: ignore
    Substrate, analyse_substrate, tokenize_chapters, tokenize_paragraphs, tokenize_words,
)


REAL_WORLD_DIR = Path(r"D:\temp\spike_43b\real_world_substrates")


def main():
    manifest_path = Path(r"D:\temp\spike_43b\spike_43b_real_world_records_2026-05-17.ndjson")
    manifest = [json.loads(l) for l in manifest_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    records = []
    for entry in manifest:
        path = Path(entry["path"])
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        sub = Substrate(
            name=entry["name"],
            path=str(path),
            text=text,
            is_canonical_good=False,
            notes=f"real-world; source_class={entry['source_class']}; license={entry['license']}",
        )
        sys.stderr.write(f"[analyse] {sub.name} ({len(text)} bytes; class={entry['source_class']})\n")
        rec = analyse_substrate(sub)
        rec["substrate_class"] = entry["source_class"]
        rec["source_url"] = entry["source_url"]
        rec["license"] = entry["license"]
        records.append(rec)

    out = Path(r"D:\temp\spike_43b\spike_43b_real_world_substructural_2026-05-17.ndjson")
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    sys.stderr.write(f"\nWrote {len(records)} real-world records to {out}\n")


if __name__ == "__main__":
    main()
