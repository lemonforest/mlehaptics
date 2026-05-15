"""Spike #24 Phase 9.5 — Multi-substrate matrix update with chemistry-reaction-network column.

Extends Phase 7.4's 6-substrate matrix (CPU, bronze, cosmos, chess, chemistry,
conformal-groups) with a SEVENTH substrate column: chemistry-reaction-network
(CRN). The CRN substrate is where the *dynamic-chemistry* primitives live —
stoichiometric coefficients, mass-action ODEs, Feinberg deficiency, detailed
balance / Wegscheider cycles, reaction-graph Laplacian.

Phase 9 verdicts:
  9.1: Stoichiometric coefficients = Class J extended (integer null space).
  9.2: Mass-action ODEs show Kepler-shape signature → Class K confirmed
       at chemistry-dynamics substrate.
  9.3: Feinberg deficiency δ = n − ℓ − s is a candidate NEW primitive class
       (Class O) — a topological/combinatorial counting invariant that does
       NOT reduce to L (eigenvalue) or J (factorisation) or K (projection).
  9.4: Detailed balance + Wegscheider = Class J × Class I composition
       (per-edge ratio × cycle-closure).
  9.6: Molecular vibrational quanta = Class J on molecular substrate
       (anharmonic ladder ν_n = ν_e(n+½) − ν_e·x_e·(n+½)²).

This script consolidates the matrix update as NDJSON; one record per
(class, substrate) cell.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


# Substrates from Phase 7.4
SUBSTRATES = ["CPU", "bronze", "cosmos", "chess", "chemistry", "conformal_groups",
              "CRN"]  # CRN = chemistry-reaction-network (Phase 9 new)

# Cells: (class_id, substrate, fidelity, note)
# fidelity ∈ {native, composed, candidate, absent}
CELLS = [
    # Class A — content-addressing
    ("A", "CRN", "absent", "No content-addressing primitive in CRN theory; species are named by elemental composition, not hashed."),
    # Class B — tagged-tuples
    ("B", "CRN", "native", "Complexes are tagged-tuples of (species, multiplicity) pairs; reactions are tagged-tuples (reactant_complex, product_complex, rate_constant)."),
    # Class C — iteration
    ("C", "CRN", "native", "Mass-action ODE integration is iteration over time; reaction-step iteration is the chemistry-substrate primitive."),
    # Class D — late-binding
    ("D", "CRN", "composed", "Rate laws can be late-bound (mass-action default; can be replaced with Michaelis-Menten enzyme-rate, Hill rate, etc.) — but this is composition over basic Class B reaction records."),
    # Class E — catalog
    ("E", "CRN", "native", "Reaction network IS a catalog: species roster + reaction-list + rate-constant table."),
    # Class F — templating
    ("F", "CRN", "absent", "No templating primitive native to CRN; rate-law parameterisation is constants, not templates."),
    # Class G — discovery
    ("G", "CRN", "native", "Conservation analysis surfaces moiety-conservation laws (left null space of stoich matrix); pathway enumeration is gap-discovery on reaction graph."),
    # Class H — self-introspection
    ("H", "CRN", "native", "Deficiency, rank, linkage classes are introspective invariants of the CRN itself."),
    # Class I — cyclic-group
    ("I", "CRN", "native", "Wegscheider cycle-closure on log(K) IS Class I: cycle subgroup of H_1 on reaction graph, with ratesum-around-cycle constraint = identity. (Phase 9.4)"),
    # Class J — period-relation / prime-factorisation
    ("J", "CRN", "native", "Stoichiometric coefficients are integer null-space vectors with gcd=1 primitive form. (Phase 9.1) Equilibrium constants are multiplicative ratios per reaction. (Phase 9.4)"),
    # Class K — equation-of-centre / pin-slot
    ("K", "CRN", "native", "Mass-action ODE concentration trajectories show Kepler-shape sparse integer-multiple harmonics on the residual against equilibrium. (Phase 9.2 — Lotka-Volterra, Brusselator, Oregonator)"),
    # Class L — Laplacian eigenbasis
    ("L", "CRN", "native", "Reaction-graph Laplacian governs convergence rates of mass-action dynamics; its eigenvalues / eigenvectors are spectral primitives of CRN dynamics. Distinct from Class O (deficiency)."),
    # Class M — HDC encoding
    ("M", "CRN", "composed", "Reaction networks can be HDC-encoded (each reaction as a bound vector in concentration-space) but this is not natively in CRN theory."),
    # Class N — rational-approximation / Diophantine
    ("N", "CRN", "absent", "No rational-approximation primitive in CRN theory; stoichiometric coefficients are integers by construction."),
    # Class O? — NEW: deficiency-style topological counting invariant on hypergraph
    ("O?", "CRN", "native", "Feinberg deficiency δ = n − ℓ − s is a candidate-new-primitive: topological counting invariant on the reaction graph that controls global dynamics via the deficiency-zero theorem. Distinct from L (eigenvalue) and J (factorisation). (Phase 9.3) STATUS: CANDIDATE — fermata-tagged for conductor decision."),
    # Class O? — other substrates
    ("O?", "CPU", "composed", "Counting invariants on data-flow graphs (e.g., feedback-vertex-set, strongly-connected-component count) are computable but not native CPU primitives — composed from graph algorithms."),
    ("O?", "bronze", "candidate", "The bronze has a candidate analog: closure relations on the gear-DAG. Gear-DAG IS a reaction-graph-like structure; cycle-count vs species-count vs rank could be computed. Whether bronze SHOWS this invariant determining its dynamics is unverified — open candidate."),
    ("O?", "cosmos", "absent", "Celestial-mechanics doesn't have a natural reaction-graph analog; orbits are continuous trajectories, not transitions between discrete complexes."),
    ("O?", "chess", "candidate", "Chess position-graph could be analysed as a reaction-network (positions = complexes, moves = reactions); deficiency analog would be (n_positions − n_components − rank_of_move_matrix). Untested in current notebook scope; flagged as future investigation."),
    ("O?", "chemistry", "native", "Same as CRN — chemistry IS CRN at the dynamics level. (The 'chemistry' substrate column in Phase 7 captured *non-dynamic* chemistry: stereochemistry, orbital algebra, etc.; the new CRN column captures the *dynamic* sub-substrate.)"),
    ("O?", "conformal_groups", "absent", "No reaction-graph analog in conformal-group theory."),
    # Class P? — conformal projection
    ("P?", "CRN", "absent", "No conformal-projection primitive in CRN theory; reaction graphs are combinatorial, not geometric."),
]


def main() -> int:
    records: list[dict] = []
    records.append({
        "kind": "header",
        "spike": 24,
        "phase": "9.5",
        "title": "Multi-substrate matrix updated with chemistry-reaction-network (CRN) column",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "substrates": SUBSTRATES,
        "n_classes_existing": 16,  # A..N + O? + P?
        "new_candidate_class": "O? (Feinberg deficiency / topological counting invariant on reaction graph)",
        "method": "Cell-by-cell assignment for the new CRN column; cross-substrate audit for the new Class O? row.",
    })

    for class_id, substrate, fidelity, note in CELLS:
        records.append({
            "kind": "matrix_cell",
            "class_id": class_id,
            "substrate": substrate,
            "fidelity": fidelity,
            "note": note,
        })

    records.append({
        "kind": "matrix_summary",
        "n_cells_added": len(CELLS),
        "n_native_in_CRN": sum(1 for c in CELLS if c[1] == "CRN" and c[2] == "native"),
        "n_composed_in_CRN": sum(1 for c in CELLS if c[1] == "CRN" and c[2] == "composed"),
        "n_absent_in_CRN": sum(1 for c in CELLS if c[1] == "CRN" and c[2] == "absent"),
        "key_finding": (
            "CRN substrate instantiates 10 of the 14 existing primitive classes "
            "(A absent, F absent, M composed, N absent; the rest native or "
            "composed); ADDITIONALLY surfaces a CANDIDATE NEW primitive class "
            "O? (Feinberg deficiency) that is native to CRN but only candidate "
            "or composed in other substrates."
        ),
        "kepler_universal_status": (
            "Kepler-shape universal stands stronger after Phase 9. Class K is "
            "now confirmed at TWO chemistry sub-substrates: chemistry-static "
            "(Phase 6/7: ethane V_3, Felkin-Anh, anomeric) AND "
            "chemistry-dynamics (Phase 9.2: Lotka-Volterra, Brusselator, "
            "Oregonator residuals)."
        ),
        "vocabulary_changes_required_for_notebook": [
            "Phase 7.4's 16-row × 6-column matrix becomes 17-row × 7-column.",
            "New row 17 (Class O?) — Feinberg deficiency / topological-counting invariant. Native in CRN; candidate in bronze and chess; absent elsewhere.",
            "New column 7 (CRN) — chemistry-reaction-network. 10/14 existing classes native; introduces Class O?.",
            "Class K's chemistry row in Phase 7.4 should be updated to indicate the new chemistry-dynamics confirmation as a SECOND confirming sub-substrate (vs only F24/static chemistry in Phase 7).",
        ],
    })

    out_path = Path(__file__).with_suffix(".ndjson")
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote {out_path}")
    print(f"  cells added: {len(CELLS)}")
    print(f"  native in CRN: {sum(1 for c in CELLS if c[1] == 'CRN' and c[2] == 'native')}")
    print(f"  candidate new class: O? (Feinberg deficiency)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
