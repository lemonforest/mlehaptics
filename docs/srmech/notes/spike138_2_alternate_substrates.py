"""Spike #138.2 — Cascade exploration on ALTERNATE substrate roster.

Multi-DOMAIN validation companion to Spike #138.1 (depth-4/5 closure on
SAME substrates). This spike replaces Spike #138's roster
(chess / image / ephemeris / quantum / physarum) with five NEW substrates
drawn from project canon:

  1. sparse-coding    — Spike #117 substrate-A power-law Laplacian
                        (n=64; alpha=1.0; Class K asymptotic-DOF truncation)
  2. geomagnetic      — Spike #131 core-mantle MHD shell Laplacian
                        (n=60; spherical-shell discretisation; Class C cascade-
                        orientation via dipole/multipole eigenmode competition)
  3. genetic-code     — Spike #81 substrate (64 codons; Class I cyclic-cascade
                        on (alphabet=4) × (positions=3) graph with wobble edges)
  4. cmb-acoustic     — Spike #103 CMB acoustic-peak substrate
                        (l_n = n·π/θ_s with θ_s = 0.0104109; n=64 peaks;
                        Class I + Class C cyclic Cauchy-form)
  5. bipartite-graph  — explicit bipartite Class L substrate (n=64 = 32+32;
                        K_{32,32} - matching edges; eigenvalue-symmetric
                        spectrum; substitute for the absent Spike #135 BBB
                        bipartite asset)

The test is whether Spike #138's three structural findings replicate:

  - {B, D, E, F, L} closed identity-attractor subgroup at depth-2
  - 72.5% substrate-invariant cascade ratio
  - 0/1196 ordering-dependence

If they replicate, the closure-subgroup pattern is substrate-class-universal
(not artifact of Spike #138's specific 5-substrate selection). If they fail,
the depth-2 finding was substrate-bounded — sample-selection-bias caveat per
Spike #141 Meta-lesson 1.

Run:
    python notes/spike138_2_alternate_substrates.py [--depth2-only] [--seed 138]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Make srmech importable from the source tree without an install.
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "python"))

import numpy as np  # noqa: E402

# Re-use Spike #138 explorer machinery so we don't fork operators / inspectors.
sys.path.insert(0, str(HERE))
import spike138_explorer as s138  # noqa: E402

from srmech.amsc import laplacian as amsc_laplacian  # noqa: E402


SPIKE_NUMBER = "138.2"
SPIKE_DATE = "2026-05-18"


# ----------------------------------------------------------------------
# Alternate substrate fixtures
#
# Each substrate produces the same composite "form" Spike #138 uses
# (HDC + spectrum + period + ...), so its operators and inspection
# cascades apply unchanged. The substrate_class field on each record
# marks which alternate-substrate cohort the row belongs to.
# ----------------------------------------------------------------------


def make_substrate_sparse_coding() -> Dict[str, Any]:
    """Spike #117 substrate-A: natural-image power-law Laplacian.

    n = 64 nodes. Edge weights w_ij = 1 / (1 + |i - j|^alpha) with alpha=1.0
    (natural-image regime) per Spike #117 substrate_a parameterisation.
    Class K asymptotic-DOF cascade-stretched-exp signature S(k)=1-exp(-(k/tau)^beta)
    with beta≈0.58 expected.
    """
    n = 64
    alpha = 1.0
    edges = []
    weights = []
    # Power-law-coupled Laplacian: every pair has a weighted edge.
    for i in range(n):
        for j in range(i + 1, n):
            d = abs(i - j)
            w = 1.0 / (1.0 + float(d) ** alpha)
            edges.append((i, j))
            weights.append(w)
    L = amsc_laplacian.dense_laplacian(n, edges, weights=weights)
    return {
        "id": "sparse_coding",
        "n": n,
        "L": L,
        "spectrum": None,
        "period": 8,  # Class K tau ≈ 27 → low-rank effective period; chosen 8 (low integer)
        "hdc": s138._laplacian_to_hdc(L, seed=138_201),
        "substrate_class": "sparse_coding",
    }


def make_substrate_geomagnetic() -> Dict[str, Any]:
    """Spike #131 geodynamo: spherical-shell core-mantle Laplacian.

    Discretised as a graph on a (latitude × longitude) tessellation of a
    spherical shell. n = 60 = 6 lat-bands × 10 lon-bands. Edges connect
    nearest neighbours in lat and lon (periodic in lon). Substrate-specific
    operations (Coriolis, Lorentz feedback, Pm ratio) are reflected only as
    edge-weight asymmetries (E-W slightly stronger than N-S → mimics
    rotational coupling) — magnitude detail per
    [[user_stance_framework_domain_algebra_not_length_or_magnitude]].
    """
    n_lat = 6
    n_lon = 10
    n = n_lat * n_lon
    edges = []
    weights = []
    for ilat in range(n_lat):
        for ilon in range(n_lon):
            u = ilat * n_lon + ilon
            # East neighbour (periodic in lon).
            ilon_e = (ilon + 1) % n_lon
            v = ilat * n_lon + ilon_e
            edges.append((min(u, v), max(u, v)))
            # Coriolis coupling: E-W slightly stronger than N-S.
            weights.append(1.20)
            # North neighbour (no wrap in lat).
            if ilat + 1 < n_lat:
                v = (ilat + 1) * n_lon + ilon
                edges.append((min(u, v), max(u, v)))
                weights.append(1.00)
    L = amsc_laplacian.dense_laplacian(n, edges, weights=weights)
    return {
        "id": "geomagnetic",
        "n": n,
        "L": L,
        "spectrum": None,
        "period": 2,  # dipole-up / dipole-down two-state cyclic
        "hdc": s138._laplacian_to_hdc(L, seed=138_202),
        "substrate_class": "geomagnetic",
    }


def make_substrate_genetic_code() -> Dict[str, Any]:
    """Spike #81 genetic-code substrate: 64-codon Class I cyclic-3.

    n = 64 codons. Each codon is a triple (a,b,c) over alphabet {0,1,2,3}.
    Edges connect codons differing in exactly ONE position (single-mutation
    Hamming-1 graph) — the wobble-equivalence skeleton from Spike #81. This
    is a regular Cayley graph of degree 3·3=9; its Laplacian carries Class I
    cyclic-3 structure (each position is a (ℤ/4) coordinate).
    """
    n = 64
    edges = []
    # Codon i has coordinates (i // 16, (i // 4) % 4, i % 4).
    for i in range(n):
        a, b, c = i // 16, (i // 4) % 4, i % 4
        # Single-position neighbours (Hamming-1).
        for newA in range(4):
            if newA != a:
                j = newA * 16 + b * 4 + c
                if i < j:
                    edges.append((i, j))
        for newB in range(4):
            if newB != b:
                j = a * 16 + newB * 4 + c
                if i < j:
                    edges.append((i, j))
        for newC in range(4):
            if newC != c:
                j = a * 16 + b * 4 + newC
                if i < j:
                    edges.append((i, j))
    L = amsc_laplacian.dense_laplacian(n, edges)
    return {
        "id": "genetic_code",
        "n": n,
        "L": L,
        "spectrum": None,
        "period": 3,  # triplet codon Class I cyclic-3
        "hdc": s138._laplacian_to_hdc(L, seed=138_203),
        "substrate_class": "genetic_code",
    }


def make_substrate_cmb_acoustic() -> Dict[str, Any]:
    """Spike #103 CMB acoustic-peak substrate: l_n = n·π/θ_s cyclic Cauchy-form.

    n = 64 acoustic-peak modes. Edges form a 1-D cyclic chain (Class I
    structure preserved); edge weights reflect peak-spacing 2π/θ_s ≈ 603.52.
    Per Spike #103 finding: constant angular spacing 2π/N bit-exact;
    Class I primitive at this scale (Class L sqrt-eigenvalue-growth is the
    wrong primitive — Spike #103 verdict). Substrate honours Class I + Class C
    cascade-orientation per Spike #103 finding.
    """
    n = 64
    edges = []
    weights = []
    # Cyclic chain: i — (i+1) mod n.
    for i in range(n):
        j = (i + 1) % n
        edges.append((min(i, j), max(i, j)))
        # Normalised weight 1.0 (Class I cyclic doesn't need amplitude).
        weights.append(1.0)
    L = amsc_laplacian.dense_laplacian(n, edges, weights=weights)
    return {
        "id": "cmb_acoustic",
        "n": n,
        "L": L,
        "spectrum": None,
        "period": 6,  # ~6 acoustic peaks per Planck 2018 inventory
        "hdc": s138._laplacian_to_hdc(L, seed=138_204),
        "substrate_class": "cmb_acoustic",
    }


def make_substrate_bipartite() -> Dict[str, Any]:
    """Bipartite Class L substrate: n = 64 = 32 + 32 partition (BBB-substitute).

    Spike #135 BBB asset is not in tree. Substituted with explicit bipartite
    K_{32,32} - matching: every left-vertex connects to every right-vertex
    EXCEPT for the index-matched pair. This produces an eigenvalue-symmetric
    spectrum (Class L bipartite signature: eigenvalues come in (λ, -λ) pairs).
    Distinct from Spike #138's roster because every edge crosses the
    partition — no within-side edges, unlike chess/image/ephemeris/quantum/
    physarum which all have within-region edges.
    """
    n_left = 32
    n_right = 32
    n = n_left + n_right
    edges = []
    weights = []
    # Bipartite K_{32,32} minus a perfect matching.
    for i in range(n_left):
        for j in range(n_right):
            if i == j:
                continue  # skip the matched pair
            u = i
            v = n_left + j
            edges.append((u, v))
            weights.append(1.0)
    L = amsc_laplacian.dense_laplacian(n, edges, weights=weights)
    return {
        "id": "bipartite",
        "n": n,
        "L": L,
        "spectrum": None,
        "period": 2,  # bipartite 2-coloring → period-2 cyclic
        "hdc": s138._laplacian_to_hdc(L, seed=138_205),
        "substrate_class": "bipartite",
    }


def build_alternate_substrates() -> Dict[str, Dict[str, Any]]:
    return {
        "sparse_coding": make_substrate_sparse_coding(),
        "geomagnetic": make_substrate_geomagnetic(),
        "genetic_code": make_substrate_genetic_code(),
        "cmb_acoustic": make_substrate_cmb_acoustic(),
        "bipartite": make_substrate_bipartite(),
    }


# ----------------------------------------------------------------------
# Main loop — mirrors Spike #138's main, but with alternate substrates
# and a substrate_class field on each record.
# ----------------------------------------------------------------------


def run_cell_with_class(
    generation_cascade,
    substrate,
    inspection_name,
    inspection_cascade,
    rng_seed,
    stack_id,
):
    """Wrap s138.run_cell to add the substrate_class field."""
    rec = s138.run_cell(
        generation_cascade, substrate, inspection_name, inspection_cascade,
        rng_seed, stack_id
    )
    rec["spike"] = SPIKE_NUMBER
    rec["substrate_class"] = substrate.get("substrate_class", substrate["id"])
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth2-only", action="store_true",
                    help="Skip depth-3 sampling (4900 cells, fast smoke).")
    ap.add_argument("--depth3-samples", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=138)
    ap.add_argument("--stack-id", default="python+c")
    ap.add_argument("--out", default=str(HERE / "spike138_2_findings_2026-05-18.ndjson"))
    args = ap.parse_args()

    print(f"spike138.2: alternate substrate roster cascade-exploration")
    print(f"spike138.2: seed={args.seed}, stack={args.stack_id}, out={args.out}")

    substrates = build_alternate_substrates()
    print(f"spike138.2: built {len(substrates)} alternate substrates: "
          f"{list(substrates.keys())}")
    for sub_id, sub in substrates.items():
        print(f"  {sub_id}: n={sub['n']}, period={sub['period']}")

    cascades_d2 = s138.enumerate_depth2()
    print(f"spike138.2: depth-2 cascades = {len(cascades_d2)}")
    if args.depth2_only:
        cascades_d3 = []
    else:
        cascades_d3 = s138.sample_depth3(args.depth3_samples, args.seed)
    print(f"spike138.2: depth-3 cascades = {len(cascades_d3)}")

    all_cascades = cascades_d2 + cascades_d3
    total_cells = len(all_cascades) * len(substrates) * len(s138.INSPECTION_ORDERINGS)
    print(f"spike138.2: total cells = {total_cells}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    classify_counter: Counter = Counter()
    identity_by_cascade: defaultdict = defaultdict(list)
    invariance_by_cascade: defaultdict = defaultdict(lambda: defaultdict(Counter))
    fingerprint_by_cascade: defaultdict = defaultdict(list)
    per_class_total_ns: Counter = Counter()
    per_class_call_count: Counter = Counter()
    # Per-substrate-class breakdown for the multi-domain analysis.
    classify_by_substrate: defaultdict = defaultdict(Counter)
    identity_by_substrate: defaultdict = defaultdict(set)
    cells_done = 0

    t0 = time.perf_counter()
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        framing = {
            "spike": SPIKE_NUMBER,
            "date": SPIKE_DATE,
            "kind": "framing",
            "stack_id": args.stack_id,
            "spike_138_companion": "Multi-DOMAIN validation of Spike #138 closure-subgroup pattern",
            "n_classes": len(s138.CLASSES),
            "n_substrates": len(substrates),
            "substrate_roster": list(substrates.keys()),
            "substrate_origins": {
                "sparse_coding": "Spike #117 substrate-A natural-image power-law Laplacian",
                "geomagnetic": "Spike #131 core-mantle MHD spherical-shell Laplacian",
                "genetic_code": "Spike #81 64-codon Class I cyclic-3 Hamming-1 graph",
                "cmb_acoustic": "Spike #103 Class I cyclic Cauchy-form acoustic-peak chain",
                "bipartite": "Class L bipartite K_{32,32}-matching substitute for Spike #135 BBB asset",
            },
            "n_cascades_depth2": len(cascades_d2),
            "n_cascades_depth3": len(cascades_d3),
            "n_inspection_orderings": len(s138.INSPECTION_ORDERINGS),
            "total_cells": total_cells,
            "fixed_point_threshold": s138.FIXED_POINT_THRESHOLD,
            "inspection_depth_cap": s138.INSPECTION_DEPTH_CAP,
            "anchor_citation": "Spike #138.2 brief; alternate-substrate-roster multi-domain validation per [[feedback_multi_domain_multi_round_survival_falsification_method]]",
            "spike_138_reference_universal_count": 28,
            "spike_138_reference_substrate_invariant_ratio": 0.725,
            "spike_138_reference_ordering_dependent_count": 0,
        }
        fh.write(json.dumps(framing) + "\n")

        for cas in all_cascades:
            for sub_id, sub in substrates.items():
                for ins_name, ins_cas in s138.INSPECTION_ORDERINGS.items():
                    rec = run_cell_with_class(
                        cas, sub, ins_name, ins_cas, args.seed, args.stack_id
                    )
                    fh.write(json.dumps(rec) + "\n")
                    cls_label = rec["output_form_classification"]
                    classify_counter[cls_label] += 1
                    classify_by_substrate[sub_id][cls_label] += 1
                    if cls_label == "identity_attractor":
                        identity_by_cascade[tuple(cas)].append(f"{sub_id}/{ins_name}")
                        identity_by_substrate[sub_id].add(tuple(cas))
                    invariance_by_cascade[tuple(cas)][ins_name][sub_id] = cls_label
                    fingerprint_by_cascade[tuple(cas)].append(rec["fixed_point_form_sha256"])
                    for cls, ns in rec["per_class_timing_ns"].items():
                        per_class_total_ns[cls] += ns
                        per_class_call_count[cls] += 1
                    cells_done += 1
                    if cells_done % 1000 == 0:
                        elapsed = time.perf_counter() - t0
                        rate = cells_done / max(elapsed, 1e-9)
                        eta = (total_cells - cells_done) / max(rate, 1e-9)
                        print(f"  {cells_done}/{total_cells} cells, "
                              f"{elapsed:.1f}s elapsed, ETA {eta:.0f}s, "
                              f"rate {rate:.0f} cells/s")

        # Summary rows.
        summary = {
            "spike": SPIKE_NUMBER,
            "date": SPIKE_DATE,
            "kind": "summary",
            "stack_id": args.stack_id,
            "cells_done": cells_done,
            "wall_seconds": time.perf_counter() - t0,
            "classification_counts": dict(classify_counter),
            "classification_by_substrate": {
                sub_id: dict(counts) for sub_id, counts in classify_by_substrate.items()
            },
            "per_class_total_ns": dict(per_class_total_ns),
            "per_class_call_count": dict(per_class_call_count),
        }
        fh.write(json.dumps(summary) + "\n")

        # Universal-identity-attractor catalog (must hit on ALL substrate × ordering pairs).
        n_required = len(substrates) * len(s138.INSPECTION_ORDERINGS)
        universal_identities = []
        partial_identities = []
        for cas, occurrences in identity_by_cascade.items():
            if len(occurrences) == n_required:
                universal_identities.append(list(cas))
            elif len(occurrences) >= n_required // 2:
                partial_identities.append({"cascade": list(cas), "n_hits": len(occurrences),
                                           "n_total": n_required})
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "identity_attractor_catalog",
            "stack_id": args.stack_id,
            "universal_count": len(universal_identities),
            "partial_count": len(partial_identities),
            "universal_identities": universal_identities,
            "partial_identities": partial_identities[:50],
        }) + "\n")

        # Closure-subgroup specific catalog: how many of the 25 {B,D,E,F,L}
        # ordered pairs are identity-attractor on this roster?
        closure_set = {"B", "D", "E", "F", "L"}
        closure_pairs = [(a, b) for a in closure_set for b in closure_set]
        closure_universal = []
        closure_partial = []
        for pair in closure_pairs:
            occ = identity_by_cascade.get(pair, [])
            if len(occ) == n_required:
                closure_universal.append(list(pair))
            elif len(occ) >= 1:
                closure_partial.append({"cascade": list(pair), "n_hits": len(occ),
                                        "n_total": n_required})
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "closure_subgroup_replication",
            "stack_id": args.stack_id,
            "closure_set": sorted(closure_set),
            "closure_universal_count": len(closure_universal),
            "closure_partial_count": len(closure_partial),
            "closure_universal_pairs": closure_universal,
            "closure_partial_pairs": closure_partial,
            "spike_138_reference": "25/25 pairs universal on Spike #138 roster",
        }) + "\n")

        # Self-identity check {H∘H, K∘K, M∘M} from Spike #138.
        self_inverse = []
        for cls in ("H", "K", "M"):
            pair = (cls, cls)
            occ = identity_by_cascade.get(pair, [])
            self_inverse.append({
                "cascade": [cls, cls],
                "is_universal_identity": len(occ) == n_required,
                "n_hits": len(occ),
                "n_total": n_required,
            })
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "self_inverse_replication",
            "stack_id": args.stack_id,
            "self_inverse_pairs": self_inverse,
            "spike_138_reference": "3/3 self-inverse pairs universal on Spike #138 roster",
        }) + "\n")

        # Substrate-invariant cascades (same classification across ALL substrates
        # for at least one inspection ordering).
        substrate_invariant = []
        for cas, by_ins in invariance_by_cascade.items():
            for ins_name, by_sub in by_ins.items():
                if (len(by_sub) == len(substrates)
                        and len(set(by_sub.values())) == 1):
                    substrate_invariant.append({
                        "cascade": list(cas),
                        "inspection_ordering": ins_name,
                        "classification": next(iter(by_sub.values())),
                    })
        # Substrate-invariant occurrences classification breakdown for the ratio
        # comparison with Spike #138's 72.5%.
        inv_class_counter: Counter = Counter()
        for entry in substrate_invariant:
            inv_class_counter[entry["classification"]] += 1
        total_pairs = len(all_cascades) * len(s138.INSPECTION_ORDERINGS)
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "substrate_invariant_catalog",
            "stack_id": args.stack_id,
            "count": len(substrate_invariant),
            "total_pairs": total_pairs,
            "ratio": (len(substrate_invariant) / max(1, total_pairs)),
            "by_classification": dict(inv_class_counter),
            "spike_138_reference_ratio": 0.725,
            "samples": substrate_invariant[:100],
        }) + "\n")

        # Inspection-ordering dependence per (cascade, substrate).
        ordering_dependent = []
        for cas, by_ins in invariance_by_cascade.items():
            for sub_id in substrates.keys():
                seen_class = set()
                for ins_name, by_sub in by_ins.items():
                    if sub_id in by_sub:
                        seen_class.add(by_sub[sub_id])
                if len(seen_class) > 1:
                    ordering_dependent.append({
                        "cascade": list(cas),
                        "substrate_id": sub_id,
                        "distinct_classifications": sorted(seen_class),
                    })
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "ordering_dependent_cases",
            "stack_id": args.stack_id,
            "count": len(ordering_dependent),
            "total_pairs_tested": len(all_cascades) * len(substrates),
            "spike_138_reference": "0/1196 cascades ordering-dependent on Spike #138 roster",
            "samples": ordering_dependent[:100],
        }) + "\n")

        # Form-attractor fingerprint distribution (distinct fixed-points per cascade).
        fingerprint_buckets: Counter = Counter()
        for cas, fps in fingerprint_by_cascade.items():
            distinct = len(set(fps))
            fingerprint_buckets[distinct] += 1
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "fingerprint_distribution",
            "stack_id": args.stack_id,
            "histogram_distinct_fp_per_cascade": dict(fingerprint_buckets),
            "spike_138_reference": "{25: 1196} — every cascade had 25 distinct fingerprints",
        }) + "\n")

        # Per-substrate identity-attractor counts (key replication signal).
        per_substrate_identity = {
            sub_id: {
                "identity_attractor_unique_cascades": len(identity_by_substrate[sub_id]),
                "spike_138_reference": "Spike #138 roster: chess/image/ephemeris/quantum/physarum",
            }
            for sub_id in substrates.keys()
        }
        fh.write(json.dumps({
            "spike": SPIKE_NUMBER, "date": SPIKE_DATE,
            "kind": "per_substrate_identity_summary",
            "stack_id": args.stack_id,
            "per_substrate": per_substrate_identity,
        }) + "\n")

    print(f"spike138.2: done in {time.perf_counter() - t0:.1f}s")
    print(f"spike138.2: wrote {cells_done} cells to {out_path}")
    print(f"spike138.2: classifications = {dict(classify_counter)}")
    print(f"spike138.2: universal identities = {len(universal_identities)}")
    print(f"spike138.2: closure subgroup {{B,D,E,F,L}} universal: "
          f"{len(closure_universal)}/25")
    print(f"spike138.2: self-inverse universal:")
    for entry in self_inverse:
        cas = entry["cascade"]
        print(f"  {cas[0]}-{cas[1]}: {entry['n_hits']}/{entry['n_total']} "
              f"({'YES' if entry['is_universal_identity'] else 'no'})")
    print(f"spike138.2: substrate-invariant pairs = {len(substrate_invariant)} "
          f"(ratio {len(substrate_invariant) / max(1, total_pairs):.3f}; "
          f"Spike #138 = 0.725)")
    print(f"spike138.2: ordering-dependent cases = {len(ordering_dependent)} "
          f"(Spike #138 = 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
