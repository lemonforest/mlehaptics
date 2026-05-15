"""Spike #24 Phase 9.3b — COUNTERPOINT: does Feinberg deficiency reduce to
Class L (graph-Laplacian eigenbasis) at higher resolution?

Per [[feedback_dual_agent_research_pattern]], the deficiency-as-Class-O verdict
in Phase 9.3 is load-bearing enough to deserve counterpoint verification.

Claim under scrutiny: δ = n − ℓ − s does NOT reduce to a Laplacian eigenvalue
or eigenvector property.

Counterpoint approach: build the reaction-graph Laplacian L for each test
network from Phase 9.3 (with edges weighted by rate constants), compute its
spectrum (rank of L, dim of nullspace of L), and see if these graph-Laplacian-
derived quantities reproduce δ or relate to it deterministically.

The classical CRN-theory result is:
  - dim(ker L_complex) = ℓ (number of linkage classes) — well-known.
  - rank L_complex = n − ℓ.
  - δ = n − ℓ − s = rank L_complex − s.

So δ can be REWRITTEN as a difference between a Laplacian-spectrum quantity
(rank L_complex on complex space) and the stoichiometric-matrix rank s. This
means δ is NOT a Laplacian-eigenvalue invariant alone — it requires *both*
the Laplacian rank AND the stoichiometric rank to be combined.

Is this REDUCTION to Class L? Or COMPOSITION of Class L + a separate Class
(the stoichiometric rank — which is a Class J / linear-algebra rank on a
different matrix)?

This is the precise question the conductor will need to answer for Class O?
status: reducible-to-composition or genuinely-new.

Key counterpoint test: for each Phase 9.3 case, verify
  dim(ker L_complex) == ℓ (linkage class count)
  rank(L_complex) == n − ℓ
  δ == rank(L_complex) − rank(stoichiometric_matrix)

If these identities hold (they will — they are mathematical theorems), then
δ is a *derived* quantity from two Class L / Class J primitives. The question
remains whether this composition deserves its own Class O label or whether
it is a "Class L − Class J difference" and so a composition.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sympy import Matrix

# Inline parse_complex + crn_deficiency (the Phase 9.3 file has a hyphen in
# its name, so it cannot be imported as a Python module).


def parse_complex(s):
    s = s.strip()
    if s == "0" or s == "":
        return {}
    parts = [p.strip() for p in s.split("+")]
    out: dict[str, int] = {}
    for p in parts:
        coef = ""
        i = 0
        while i < len(p) and (p[i].isdigit() or p[i] == "."):
            coef += p[i]
            i += 1
        c = int(coef) if coef else 1
        species = p[i:].strip()
        if species == "":
            continue
        out[species] = out.get(species, 0) + c
    return out


def crn_deficiency(reactions):
    complex_strs = []
    for lhs, rhs in reactions:
        for c in (lhs, rhs):
            ck = parse_complex(c)
            key = tuple(sorted(ck.items()))
            if key not in [tuple(sorted(c2.items())) for c2 in complex_strs]:
                complex_strs.append(ck)
    n = len(complex_strs)
    species_set: set[str] = set()
    for c in complex_strs:
        species_set.update(c.keys())
    species = sorted(species_set)
    adj = [set() for _ in range(n)]
    for lhs, rhs in reactions:
        lk = parse_complex(lhs)
        rk = parse_complex(rhs)
        i = [tuple(sorted(c.items())) for c in complex_strs].index(tuple(sorted(lk.items())))
        j = [tuple(sorted(c.items())) for c in complex_strs].index(tuple(sorted(rk.items())))
        adj[i].add(j)
        adj[j].add(i)
    visited = [False] * n
    l = 0
    for v in range(n):
        if not visited[v]:
            l += 1
            stack = [v]
            while stack:
                u = stack.pop()
                if visited[u]:
                    continue
                visited[u] = True
                for w in adj[u]:
                    if not visited[w]:
                        stack.append(w)
    N = np.zeros((len(species), len(reactions)), dtype=int)
    for k, (lhs, rhs) in enumerate(reactions):
        lk = parse_complex(lhs)
        rk = parse_complex(rhs)
        for sp in species:
            N[species.index(sp), k] = rk.get(sp, 0) - lk.get(sp, 0)
    s = int(Matrix(N.tolist()).rank())
    return {
        "n_complexes": n,
        "n_linkage_classes": l,
        "stoichiometric_rank_s": s,
        "deficiency": n - l - s,
    }


def reaction_graph_laplacian(reactions):
    """Build the un-rate-weighted complex-space Laplacian L of a CRN.

    Vertices = distinct complexes; edges = reactions (directed). For the
    classical CRN-theory result (dim ker L = ℓ) we use the UNDIRECTED
    multigraph form: L[i][i] = degree(i), L[i][j] = -1 per undirected edge.
    """
    complex_strs = []
    for lhs, rhs in reactions:
        for c in (lhs, rhs):
            ck = parse_complex(c)
            key = tuple(sorted(ck.items()))
            if key not in [tuple(sorted(c2.items())) for c2 in complex_strs]:
                complex_strs.append(ck)
    n = len(complex_strs)
    L = np.zeros((n, n), dtype=float)
    edges_seen = set()
    for lhs, rhs in reactions:
        lk = parse_complex(lhs)
        rk = parse_complex(rhs)
        i = [tuple(sorted(c.items())) for c in complex_strs].index(tuple(sorted(lk.items())))
        j = [tuple(sorted(c.items())) for c in complex_strs].index(tuple(sorted(rk.items())))
        if i == j:
            continue
        # Use unordered pair to avoid double counting reversible reactions
        key = tuple(sorted([i, j]))
        if key in edges_seen:
            continue
        edges_seen.add(key)
        L[i][i] += 1
        L[j][j] += 1
        L[i][j] -= 1
        L[j][i] -= 1
    return L


def main() -> int:
    records: list[dict] = []
    records.append({
        "kind": "header",
        "spike": 24,
        "phase": "9.3b",
        "title": "Counterpoint: does Feinberg deficiency reduce to Class L (Laplacian) composed with Class J (rank)?",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })

    test_cases = [
        ("haber_bosch_reversible",
         [("N2 + 3H2", "2NH3"), ("2NH3", "N2 + 3H2")]),
        ("schlogl_bistable",
         [("2X", "3X"), ("3X", "2X"), ("X", "0"), ("0", "X")]),
        ("edelstein_three_reaction",
         [("A + X", "2X"), ("2X", "A + X"),
          ("X + Y", "Z"), ("Z", "X + Y"),
          ("Z", "Y"), ("Y", "Z")]),
        ("triangle_cycle",
         [("A", "B"), ("B", "C"), ("C", "A")]),
        ("michaelis_menten",
         [("E + S", "ES"), ("ES", "E + S"), ("ES", "E + P")]),
    ]

    for name, reactions in test_cases:
        invar = crn_deficiency(reactions)
        L = reaction_graph_laplacian(reactions)
        # Rank and kernel-dimension of L
        L_rank = int(Matrix(L.tolist()).rank())
        L_kernel_dim = invar["n_complexes"] - L_rank
        delta_recomputed = L_rank - invar["stoichiometric_rank_s"]
        # Identities:
        # (i)  L_kernel_dim == ℓ (linkage class count)?
        # (ii) L_rank == n − ℓ?
        # (iii) δ == L_rank − s?
        identity_i = (L_kernel_dim == invar["n_linkage_classes"])
        identity_ii = (L_rank == invar["n_complexes"] - invar["n_linkage_classes"])
        identity_iii = (delta_recomputed == invar["deficiency"])

        records.append({
            "kind": "counterpoint_test",
            "case": name,
            "deficiency": invar["deficiency"],
            "n_complexes": invar["n_complexes"],
            "n_linkage_classes": invar["n_linkage_classes"],
            "stoich_rank_s": invar["stoichiometric_rank_s"],
            "complex_laplacian_rank": L_rank,
            "complex_laplacian_kernel_dim": L_kernel_dim,
            "delta_via_Lrank_minus_s": delta_recomputed,
            "identity_kerL_eq_linkage_classes": identity_i,
            "identity_rankL_eq_n_minus_l": identity_ii,
            "identity_delta_eq_Lrank_minus_s": identity_iii,
        })

    # Verdict
    all_three = all(
        r.get("identity_kerL_eq_linkage_classes")
        and r.get("identity_rankL_eq_n_minus_l")
        and r.get("identity_delta_eq_Lrank_minus_s")
        for r in records if r.get("kind") == "counterpoint_test"
    )

    records.append({
        "kind": "summary",
        "all_three_identities_hold": all_three,
        "verdict": (
            "Deficiency δ DOES decompose as the difference of two existing-class "
            "invariants: dim(ker L_complex) = ℓ (Class L invariant on the "
            "complex-space Laplacian) and s = rank(stoichiometric matrix) "
            "(Class J / linear-algebra invariant on a SEPARATE matrix N). "
            "So δ = rank(L_complex) − rank(N) = (n − ℓ) − s. "
            "REDUCED FORMULA: δ = Class_L_rank(L_complex) − Class_J_rank(N). "
            "This is a COMPOSITION of two existing-class primitives, NOT a "
            "genuinely-new primitive class."
        ),
        "fermata_resolution_proposal": (
            "Class O? candidate is RESOLVED as Class L × Class J composition: "
            "specifically, δ = rank(complex-space Laplacian) − rank(stoichio"
            "metric matrix). Both are linear-algebra rank invariants on "
            "graph-derived matrices. The deficiency-zero theorem can be "
            "restated: when these two ranks AGREE (δ = 0), the dynamics has "
            "unique stable equilibrium regardless of rate constants. This is "
            "a beautiful statement at the COMPOSITION level — it links graph-"
            "topology (Class L) and stoichiometric algebra (Class J) via "
            "their rank-equality condition — without needing a new primitive."
        ),
        "alternative_framing": (
            "If the project's primitive vocabulary cares about DIFFERENCES of "
            "ranks as a separate primitive class, then Class O? survives "
            "as a derived-rank primitive distinct from L and J alone. "
            "Methodological choice for conductor."
        ),
        "honest_caveat": (
            "Even with this reduction, δ remains the most CONSEQUENTIAL "
            "invariant in CRN theory (deficiency-zero theorem etc.). "
            "Whether 'consequential composition' is named as its own class is "
            "a vocabulary choice; the algebraic reduction itself is "
            "mathematically tight."
        ),
    })

    out_path = Path(__file__).with_suffix(".ndjson")
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote {out_path}")
    for r in records:
        if r.get("kind") == "counterpoint_test":
            print(f"  {r['case']}: delta={r['deficiency']}, rank(L)={r['complex_laplacian_rank']}, "
                  f"rank(N)={r['stoich_rank_s']}, delta via formula={r['delta_via_Lrank_minus_s']}, "
                  f"identities {(r['identity_kerL_eq_linkage_classes'], r['identity_rankL_eq_n_minus_l'], r['identity_delta_eq_Lrank_minus_s'])}")
    print(f"  all identities hold: {all_three}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
