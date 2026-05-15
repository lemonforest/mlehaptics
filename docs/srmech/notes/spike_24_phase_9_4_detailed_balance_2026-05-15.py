"""Spike #24 Phase 9.4 — Detailed balance, equilibrium constants, and class assignment.

Hypothesis: At thermodynamic equilibrium, microscopic reversibility imposes
that the forward and reverse rate constants satisfy `k+/k- = K_eq`. Furthermore,
for a cycle of reactions, the product of equilibrium constants around the cycle
equals 1 (Wegscheider condition). This is a *multiplicative integer-ratio*
structure on rate-constant space.

Question: does this reduce to Class J (period-relation factorisation) or
Class K (continuous-frame equation-of-centre) or something else?

Test:
  (a) Compute K_eq for several elementary reactions from rate constants
  (b) Test Wegscheider condition for a cycle of reactions:
        A <-> B <-> C <-> A; require K_AB * K_BC * K_CA = 1
  (c) Show that detailed-balance gives an integer-cyclic structure on
        chemical potentials: mu_A - mu_B = -kT ln(K_AB), and around any
        cycle the sum of log-K's is zero (additive ℤ-homology).

Conclusion: detailed balance is Class J extended (multiplicative integer
ratio of rate constants ↔ additive ℤ-homology on chemical potentials around
cycles). The Wegscheider condition is a Z-homology condition: the cycle sum
of log-K is zero. This is structurally identical to Kirchhoff's voltage law
(EE substrate) and to the period-closure condition in cyclic-group algebra
(bronze substrate).

Outputs NDJSON.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from math import log, exp
from pathlib import Path

import numpy as np


def check_wegscheider(K_cycle: list[float], tol: float = 1e-10) -> dict:
    """Verify product of K's around a cycle equals 1 (within tol).

    Equivalently, sum of log(K)'s around cycle is zero — additive ℤ-homology
    on the cycle subgroup of H_1 of the reaction graph.
    """
    prod = 1.0
    log_sum = 0.0
    for K in K_cycle:
        prod *= K
        log_sum += log(K)
    return {
        "K_cycle_product": prod,
        "log_K_cycle_sum": log_sum,
        "wegscheider_satisfied": abs(prod - 1.0) < tol,
    }


def main() -> int:
    records: list[dict] = []
    records.append({
        "kind": "header",
        "spike": 24,
        "phase": "9.4",
        "title": "Detailed balance and Wegscheider condition: Class J multiplicative + additive ℤ-homology",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": "Symbolic and numeric verification of K_eq = k+/k- and cycle-product Wegscheider conditions",
    })

    # --- Case 1: Single reaction K_eq from rates ----------------------------
    # A <-> B; k+ = 2.5, k- = 0.5  =>  K_eq = 5.0
    records.append({
        "kind": "detailed_balance_test",
        "case": "single_reaction_AB",
        "k_plus": 2.5,
        "k_minus": 0.5,
        "K_eq": 2.5 / 0.5,
        "verdict": "Class J at substrate level: K_eq is a (real-valued, here exact) multiplicative ratio; the integer-cyclic upstream form would be a rational rate-ratio in a discrete-rate kinetics model (which is what Markov chains on chemical microstates give).",
    })

    # --- Case 2: Triangle cycle  A <-> B <-> C <-> A with consistent K's ---
    # If K_AB = 2, K_BC = 3, then K_CA must equal 1/6 for Wegscheider.
    K_AB = 2.0
    K_BC = 3.0
    K_CA_correct = 1.0 / (K_AB * K_BC)
    K_CA_inconsistent = 0.5  # deliberately wrong

    rec_consistent = check_wegscheider([K_AB, K_BC, K_CA_correct])
    rec_consistent.update({
        "kind": "wegscheider_test",
        "case": "triangle_consistent",
        "K_AB": K_AB, "K_BC": K_BC, "K_CA": K_CA_correct,
    })
    records.append(rec_consistent)

    rec_inconsistent = check_wegscheider([K_AB, K_BC, K_CA_inconsistent])
    rec_inconsistent.update({
        "kind": "wegscheider_test",
        "case": "triangle_inconsistent",
        "K_AB": K_AB, "K_BC": K_BC, "K_CA": K_CA_inconsistent,
        "note": "Deliberately inconsistent K_CA; Wegscheider violated.",
    })
    records.append(rec_inconsistent)

    # --- Case 3: Multi-cycle network. Consider the four-node graph
    #     A -> B, B -> C, A -> D, D -> C, with both directions for each.
    # This has two independent cycles: A-B-C-D-A (going A->B->C and A->D->C).
    # Wegscheider gives one constraint per independent cycle (= dim H_1 of the
    # undirected reaction graph). For this 4-node "kite" graph: 4 nodes,
    # 4 undirected edges (A-B, B-C, A-D, D-C), so cycle rank = 4 - 4 + 1 = 1.
    # One constraint: K_AB * K_BC * K_CD * K_DA = 1.
    K_AB2 = 2.0
    K_BC2 = 3.0
    K_CD2 = 2.0
    K_DA2 = 1.0 / (K_AB2 * K_BC2 * K_CD2)
    rec_kite = check_wegscheider([K_AB2, K_BC2, K_CD2, K_DA2])
    rec_kite.update({
        "kind": "wegscheider_test",
        "case": "kite_graph_cycle",
        "K_values": {"AB": K_AB2, "BC": K_BC2, "CD": K_CD2, "DA": K_DA2},
        "note": "Independent cycles = E - V + 1 = 4 - 4 + 1 = 1 constraint",
    })
    records.append(rec_kite)

    # --- Case 4: Cross-substrate connection to Kirchhoff voltage law ---
    # In an electrical circuit, sum of voltage drops around any cycle = 0.
    # In a chemical network, sum of (mu_i - mu_j) around any cycle = 0
    #   ⟺ sum of -kT log K_ij = 0 ⟺ product of K_ij = 1.
    # These are structurally identical: additive ℤ-homology on the cycle
    # subgroup of H_1 of the network graph.
    records.append({
        "kind": "cross_substrate_isomorphism",
        "case": "wegscheider_kirchhoff_isomorphism",
        "EE_substrate_form": "Σ V_drop around cycle = 0  (Kirchhoff voltage law)",
        "chemistry_substrate_form": "Σ Δμ around cycle = 0  ⟺  Π K around cycle = 1 (Wegscheider)",
        "shared_algebra": "Additive ℤ-cohomology of the network graph; cycle subgroup of H_1",
        "class_assignment": "Class J on the *log* scale (additive ℤ-homology on cycle subgroup); equivalently Class I on the multiplicative scale (cyclic-group constraint product = 1).",
        "primitive_class": "Reduces to a *cycle-closure* sub-primitive that already exists as the closure relation in Class I (cyclic-group algebra; rotations must compose to identity around a closed loop). Wegscheider is Class I's closure relation at chemistry substrate, with the parameters being equilibrium constants rather than rotation angles.",
    })

    # --- Verdict --------------------------------------------------------
    n_pass = sum(1 for r in records if r.get("wegscheider_satisfied") is True)
    n_fail = sum(1 for r in records if r.get("wegscheider_satisfied") is False)
    summary = {
        "kind": "summary",
        "n_wegscheider_tests": n_pass + n_fail,
        "n_pass": n_pass,
        "n_fail_deliberate": n_fail,
        "verdict": (
            "Detailed-balance equilibrium constants K_eq are a real-valued "
            "multiplicative ratio per reaction (Class J extended into the "
            "real-valued / chemical-potential frame). The Wegscheider cycle "
            "condition is a closure constraint: cycle-product of K's = 1, "
            "equivalently cycle-sum of log K's = 0. This is Class I's cyclic-"
            "group closure relation at chemistry substrate, isomorphic to "
            "Kirchhoff's voltage law at EE substrate, isomorphic to gear-"
            "DAG closure constraint at bronze substrate. NO NEW PRIMITIVE "
            "CLASS required — reduces to Class J × Class I composition: "
            "Class J for the per-edge ratio + Class I for the cycle-closure "
            "constraint."
        ),
        "class_assignment": "Class J (per-edge ratio) + Class I (cycle closure) composition",
    }
    records.append(summary)

    out_path = Path(__file__).with_suffix(".ndjson")
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote {out_path}")
    for r in records:
        if r.get("kind") == "wegscheider_test":
            print(f"  {r['case']}: product={r['K_cycle_product']:.6f}, "
                  f"log-sum={r['log_K_cycle_sum']:.2e}, "
                  f"wegscheider={r['wegscheider_satisfied']}")
    print(f"  verdict: {summary['class_assignment']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
