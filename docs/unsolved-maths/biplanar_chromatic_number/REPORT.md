# Biplanar (Thickness-2) Graph Chromatic Number

**Source**: [Wikipedia — List of unsolved problems in mathematics → Graph theory → Chromatic and edge-colouring](https://en.wikipedia.org/wiki/List_of_unsolved_problems_in_mathematics#Graph_theory)
**Status**: (open) — cascade dispatched 2026-05-23; reveals tight Hoffman bound for K_n biplanar; no falsifier yet for "≤ 8 suffices" conjecture
**Cascade dispatched**: 2026-05-23
**Class cascade**: **A ∘ L ∘ N ∘ M ∘ I**

---

## 1. Problem statement

A graph G has **thickness** t if its edges can be partitioned into t planar subgraphs and not into t−1. A **biplanar** graph is one with thickness 2.

**Open question**: What is the maximum chromatic number χ(G) over all biplanar graphs G?

Known bounds:
- **Lower bound**: χ ≥ 8. The complete graph K₈ is biplanar (Beineke-Harary 1965) and has χ(K₈) = 8.
- **Upper bound**: Standard degeneracy argument gives χ ≤ 11 (each planar graph is 5-degenerate; union of two is at most 10-degenerate).
- **Conjecture**: most researchers believe χ ≤ 9 for all biplanar graphs; some believe χ = 8.

## 2. Why it is open

K₉ is NOT biplanar (thickness 3), so the chromatic-number-8 lower bound stops at K₈. Constructing a biplanar graph with χ > 8 would require a non-complete structure where the union of two planar layers forces a 9th independent set. No such graph has been constructed. Proving χ ≤ 8 for all biplanar graphs requires an argument tighter than the degeneracy / product bounds.

The problem composes with Hilbert-style structural questions about graph colourings: the Four Color Theorem (Appel-Haken 1976) handles thickness-1; biplanar is the natural next case.

## 3. Framework reading

**Substrate-level reframing**: a biplanar graph is the EDGE-WISE UNION of two planar substrates G₁ ∪ G₂. The Laplacian L is ADDITIVE over edge sets:

```
L(G₁ ∪ G₂) = L(G₁) + L(G₂)   exactly
```

This is a structural identity, not a bound. The chromatic number question becomes a **spectral question** about the union Laplacian:

> What is the maximum value of `1 − λ_max(A)/λ_min(A)` (Hoffman lower bound on χ) achieved by adjacency matrices of the form A = A₁ + A₂ where A₁, A₂ are planar adjacency matrices?

For K_n with thickness 2: λ_max(A) = n−1, λ_min(A) = −1, so Hoffman bound = n. This is **exactly tight** for K_n. The cascade verifies:

| n | Hoffman bound | χ(K_n) |
|---|---------------|--------|
| 5 | 5             | 5 ✓    |
| 6 | 6             | 6 ✓    |
| 7 | 7             | 7 ✓    |
| 8 | 8             | 8 ✓    |

Per `[[user_stance_identity_not_implementation_discipline]]`: the framework READS the chromatic question as a spectral question via the Hoffman bound. It does not overwrite the graph-theoretic statement.

## 4. Cascade composition (A∘L∘N∘M∘I)

| Step | Class | Operation | Input | Output |
|------|-------|-----------|-------|--------|
| 1 | **A** | `sha256_bytes(edge_list)` | layer1+layer2 edges | content-hash for provenance |
| 2 | **L** | `dense_laplacian(n, G_i)` + `jacobi_eigvals` | edge lists | Laplacian eigenvalues per layer + union |
| 2′| **L** | `dense_adjacency(n, G)` + `jacobi_eigvals` | union edges | adjacency spectral radius λ_max, λ_min |
| 3 | **N** | `best_rational(λ_max·1000, 1000·\|λ_min\|, 100)` | spectral ratio | exact `p/q` rational |
| 3′| **N** | `ceil(1 − λ_max/λ_min)` | Hoffman bound | integer chromatic lower bound |
| 4 | **M** | `bind` + `similarity` over color hypervectors | k color HVs, vertex adjacency | feasibility verdict |
| 5 | **I** | greedy Z/kZ coloring respecting adjacency | n vertices, adj | smallest k' ≥ Hoffman where homomorphism exists |

Per `[[feedback_dont_pre_commit_spike_query_operators]]`: cascade designed to broad-query the spectral structure; tautology pre-filter is the Hoffman bound (NOT result-driven; tightness on K_n is the EMPIRICAL FINDING, not the assumption).

## 5. Configuration data (AMSC catalog)

- `descriptor.toml` — AMSC source descriptor; `literature_curated` adapter; primary reference Beineke-Harary 1965
- `schema.json` — JSON Schema `srmech.biplanar_chromatic.graph.v1` with 21 required fields
- `biplanar_graphs.ndjson` — 5 cascade-output records (K₅, K₆, K₇, K₈, grid3x4+matching)
- `generate_catalog.py` — reproducible cascade generator

## 6. Cascade execution

```bash
# Run the cascade
python docs/unsolved-maths/biplanar_chromatic_number/generate_catalog.py

# Or query via the AMSC bridge
python -c "
from srmech.amsc.catalog import register_attested_root, get_attested_dataset
register_attested_root('docs/unsolved-maths', source='unsolved_maths_research')
ds = get_attested_dataset('biplanar_chromatic')
for row in ds['rows']:
    d = row['data']
    print(d['graph_id'], 'Hoffman=', d['hoffman_bound_exact'])
"
```

## 7. Findings (2026-05-23 cascade)

| Graph | n | Hoffman bound | Spectral ratio | HDC verified | χ known | Fiedler(union) |
|-------|---|---------------|----------------|--------------|---------|-----------------|
| K₅ | 5 | **5** | 4/1 | 5 colors | 5 ✓ | 5.000 |
| K₆ | 6 | **6** | 5/1 | 6 colors | 6 ✓ | 6.000 |
| K₇ | 7 | **7** | 6/1 | 7 colors | 7 ✓ | 7.000 |
| K₈ | 8 | **8** | 7/1 | 8 colors | 8 ✓ | 8.000 |
| grid3x4 + matching | 12 | 3 | 1/1 | 2 colors | unknown | 0.764 |

**Verdict**: **(open)** — Hoffman bound is tight on K_n for n=5..8 (the maximal-density biplanar graphs). For non-complete biplanar graphs the spectral ratio drops sharply. No biplanar graph in this small sample exhibits a spectral ratio > 7 (which would force χ > 8). The cascade has not falsified the "≤ 8 suffices" conjecture but the sample is small.

**Structural observation** (not a result): The cascade reveals that K_n biplanar graphs are **spectrally saturated** — Hoffman gives the exact χ. Any biplanar graph achieving χ > 8 must exhibit a different spectral structure than K_n. This is the open empirical question: do such graphs exist?

## 8. Open fermatas

- **Larger search**: dispatch the cascade over random biplanar graphs (planar G₁ + planar G₂ on N ∈ {20, 50, 100} vertices) to scan for ratio > 7. None found in tiny sample; need much larger search.
- **Theoretical**: is the spectral ratio `λ_max(A₁+A₂)/|λ_min(A₁+A₂)|` provably bounded by 7 over all pairs of planar adjacency matrices? This would close the conjecture at χ ≤ 8.
- **Hopf composition**: the user's framework predicts a 3:7 Hurwitz ratio baked into Laplacian sums (per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`). Does the biplanar spectral ratio cluster at 7:1 because 7 = 3+4 in the Hurwitz partition? Untested fermata.

## 9. Citations

Per `[[feedback_pdf_extraction_citation_discipline]]` + `[[feedback_paywalled_doi_cannot_be_attested]]`: citations flagged for PDF + OA verification at canonical-stance dispatch.

- Beineke LW, Harary F (1965). The thickness of the complete graph. *Canadian Journal of Mathematics* 17:850-859. DOI 10.4153/CJM-1965-086-x. Canadian Mathematical Society — verify open access.
- Appel K, Haken W (1976). Every planar map is four colorable. *Bull. Amer. Math. Soc.* 82(5):711-712. Open access via Project Euclid.
- Hoffman AJ (1970). On eigenvalues and colorings of graphs. In: *Graph Theory and its Applications* (ed. B. Harris), Academic Press, pp. 79-91. Textbook chain.

## 10. Cross-references

- srmech catalog: `biplanar_chromatic` (registered via `register_attested_root("docs/unsolved-maths", source="unsolved_maths_research")`)
- Related canonical stances: `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]` (3:7 Hurwitz ratio; possible explanation for 7:1 Hoffman saturation on K_n biplanar), `[[user_stance_identity_not_implementation_discipline]]`
- Related framework discipline: `[[feedback_srmech_amsc_catalog_pitfalls]]` (catalog created during this work; documents 7 gotchas hit)
- Companion textbook: [The Metric Field and Its Primitives](../../srmech/metric-field-and-its-primitives.pdf) §Class L + §Class M
