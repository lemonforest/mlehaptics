"""Spike #138.1 — Post-run analysis.

Reads the NDJSON outputs of spike138_1_closure_verifier.py and produces
human-readable summaries for the findings doc.

Run:
  python notes/spike138_1_analyze.py [--d4 PATH] [--d5 PATH] [--falsifier PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

HERE = Path(__file__).resolve().parent


def read_ndjson(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Returns (frames_and_summaries, per_cell_records)."""
    framing: List[Dict[str, Any]] = []
    cells: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("kind") in ("framing", "summary"):
                framing.append(rec)
            else:
                cells.append(rec)
    return framing, cells


def compute_universal_identities(cells: List[Dict[str, Any]]) -> Set[Tuple[str, ...]]:
    """A tuple is universal-identity if classification == identity_attractor
    on every (substrate, ordering) cell."""
    cells_by_tuple: Dict[Tuple[str, ...], List[Dict[str, Any]]] = defaultdict(list)
    for rec in cells:
        cells_by_tuple[tuple(rec["generation_cascade"])].append(rec)
    universal: Set[Tuple[str, ...]] = set()
    for tup, recs in cells_by_tuple.items():
        if all(r["output_form_classification"] == "identity_attractor" for r in recs):
            universal.add(tup)
    return universal


def hash_universal_set(universal: Set[Tuple[str, ...]]) -> str:
    """Deterministic SHA-256 of the sorted universal-identity set."""
    payload = "\n".join("-".join(t) for t in sorted(universal))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def analyse_closure_run(path: Path, label: str) -> Dict[str, Any]:
    framing, cells = read_ndjson(path)
    if not cells:
        return {"label": label, "error": "no cells in file"}
    summary = next((f for f in framing if f.get("kind") == "summary"), None)
    if summary is None:
        return {"label": label, "error": "no summary in file"}

    universal = compute_universal_identities(cells)
    uni_hash = hash_universal_set(universal)
    classify_counter = Counter(r["output_form_classification"] for r in cells)

    # Per-substrate / per-ordering breakdown of non-identity cells.
    non_identity_by_substrate: Counter[str] = Counter()
    non_identity_by_ordering: Counter[str] = Counter()
    non_identity_class: Counter[str] = Counter()
    for rec in cells:
        if rec["output_form_classification"] != "identity_attractor":
            non_identity_by_substrate[rec["substrate_id"]] += 1
            non_identity_by_ordering[rec["inspection_cascade_ordering"]] += 1
            non_identity_class[rec["output_form_classification"]] += 1

    out = {
        "label": label,
        "path": str(path),
        "depth": summary.get("depth"),
        "n_tuples": summary.get("n_tuples"),
        "n_cells": summary.get("n_cells_total"),
        "closure_rate": summary.get("closure_rate"),
        "n_tuples_closed": summary.get("n_tuples_closed"),
        "n_tuples_failed": summary.get("n_tuples_failed"),
        "universal_identity_count": len(universal),
        "universal_identity_sha256": uni_hash,
        "classification_counts": dict(classify_counter),
        "non_identity_by_substrate": dict(non_identity_by_substrate),
        "non_identity_by_ordering": dict(non_identity_by_ordering),
        "non_identity_classes": dict(non_identity_class),
        "wall_seconds": summary.get("wall_seconds"),
    }
    return out


def analyse_falsifier_run(path: Path) -> Dict[str, Any]:
    framing, cells = read_ndjson(path)
    summary = next((f for f in framing if f.get("kind") == "summary"), None)
    if summary is None:
        return {"error": "no summary"}

    # Per-tuple identity counts: how often does a complement-touching tuple
    # yield identity_attractor?
    cells_by_tuple: Dict[Tuple[str, ...], List[Dict[str, Any]]] = defaultdict(list)
    for rec in cells:
        cells_by_tuple[tuple(rec["generation_cascade"])].append(rec)

    n_tuples = len(cells_by_tuple)
    fully_identity: List[Tuple[str, ...]] = []
    partial_identity: List[Tuple[str, ...]] = []
    no_identity: List[Tuple[str, ...]] = []
    for tup, recs in cells_by_tuple.items():
        n_id = sum(1 for r in recs if r["output_form_classification"] == "identity_attractor")
        if n_id == len(recs):
            fully_identity.append(tup)
        elif n_id > 0:
            partial_identity.append(tup)
        else:
            no_identity.append(tup)

    classify_counter = Counter(r["output_form_classification"] for r in cells)

    return {
        "n_tuples": n_tuples,
        "fully_identity_count": len(fully_identity),
        "partial_identity_count": len(partial_identity),
        "no_identity_count": len(no_identity),
        "fully_identity_sample": ["-".join(t) for t in fully_identity[:20]],
        "partial_identity_sample": ["-".join(t) for t in partial_identity[:20]],
        "classification_counts": dict(classify_counter),
        "wall_seconds": summary.get("wall_seconds"),
        "sharp_boundary_violations": summary.get("sharp_boundary_violations"),
    }


def cross_stack_verify(
    path_a: Path, path_b: Path, label: str = "cross_stack",
) -> Dict[str, Any]:
    """Compare universal-identity sets between two runs (Python+C vs Python-pure)."""
    _, cells_a = read_ndjson(path_a)
    _, cells_b = read_ndjson(path_b)
    uni_a = compute_universal_identities(cells_a)
    uni_b = compute_universal_identities(cells_b)
    hash_a = hash_universal_set(uni_a)
    hash_b = hash_universal_set(uni_b)
    return {
        "label": label,
        "path_a": str(path_a),
        "path_b": str(path_b),
        "count_a": len(uni_a),
        "count_b": len(uni_b),
        "sha256_a": hash_a,
        "sha256_b": hash_b,
        "bit_exact_match": hash_a == hash_b,
        "set_diff_a_minus_b": ["-".join(t) for t in sorted(uni_a - uni_b)][:20],
        "set_diff_b_minus_a": ["-".join(t) for t in sorted(uni_b - uni_a)][:20],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--d4", default=str(HERE / "spike138_1_d4_closure.ndjson"))
    ap.add_argument("--d5", default=str(HERE / "spike138_1_d5_closure.ndjson"))
    ap.add_argument("--falsifier", default=str(HERE / "spike138_1_external_falsifier.ndjson"))
    ap.add_argument("--d4-pure", default=str(HERE / "spike138_1_d4_python_pure.ndjson"))
    ap.add_argument("--summary-out", default=str(HERE / "spike138_1_analysis.json"))
    args = ap.parse_args()

    out: Dict[str, Any] = {}

    p = Path(args.d4)
    if p.exists():
        out["d4"] = analyse_closure_run(p, "depth4_closure")
    p = Path(args.d5)
    if p.exists():
        out["d5"] = analyse_closure_run(p, "depth5_closure")
    p = Path(args.falsifier)
    if p.exists():
        out["external_falsifier"] = analyse_falsifier_run(p)

    p_a = Path(args.d4)
    p_b = Path(args.d4_pure)
    if p_a.exists() and p_b.exists():
        out["cross_stack_d4"] = cross_stack_verify(p_a, p_b, "cross_stack_d4")

    with open(args.summary_out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
