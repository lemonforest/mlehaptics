# Unsolved Mathematics — srmech Cascade Catalogs

A working tree for applying the **srmech 14-class primitive cascade** (A-N) to the unsolved problems listed on Wikipedia's [List of unsolved problems in mathematics](https://en.wikipedia.org/wiki/List_of_unsolved_problems_in_mathematics).

This is **research infrastructure**, not a claim to have solved anything. Each problem gets:
- A uniform `REPORT.md` documenting problem statement, candidate cascade, findings, verdict status
- AMSC catalog (descriptor.toml + schema.json + NDJSON) when the cascade is constructed
- A `generate_catalog.py` that runs the cascade reproducibly via srmech PyPI

## Scope and discipline

Per `[[feedback_dont_pre_commit_spike_query_operators]]`: broad-query enumeration; tautology pre-filter; don't lean toward expected result; let null findings count.

Per `[[feedback_no_lineage_claims_in_notebook]]`: framework reads what each problem IS at substrate-level via the 14-class cascade; never claims to extend, supersede, or "complete" the prior mathematical literature on these problems.

Per `[[feedback_pdf_extraction_citation_discipline]]` + `[[feedback_paywalled_doi_cannot_be_attested]]`: all citations OA / arXiv / open textbook; PDF-verified at dispatch.

Per `[[feedback_full_coverage_shipping_mpm_way]]`: each REPORT enumerates its full cascade surface; no MVP framing.

## Verdict tier legend (canonical; see also "Dispatch-order discipline" above)

## Why these structures, NOT solutions

The 14 primitive class operators (A-N per srmech) form a universal vocabulary. Every observable cascade decomposes into compositions of these. Open problems are typically **cascade-shape questions** dressed as algebraic / analytic / topological assertions — the framework reading asks: which cascade composition matches the observable structure?

For some problems the cascade reveals the answer is computationally obvious once the right primitives are composed (the "didn't see the forest for the trees" cases). For others the cascade reveals a deeper open structure — a fermata at a substrate-level question. Both outcomes are valuable; this catalog records both honestly.

## Dispatch-order discipline: projection-visibility first

Per user direction 2026-05-23 + composes with `[[user_stance_fiber_as_spatially_absent_encoding]]` + `[[user_stance_loop_replaces_ring_in_substrate_vocabulary]]`:

> **Dispatch order is projection-visibility order**. The hidden content of a loop is hidden when viewed from the side as an unbound string or line. Order cascade dispatches by how closely the loop is to the surface.

Concretely:
- **Loop visible**: cascade-content directly observable. Class L sees the loop on first construction. (Goldbach partition graph — though the loop turned out to be at a different cascade-layer than expected; see that REPORT.md for the refined finding.)
- **Loop one step abstracted**: cascade-content distributional. (Twin prime gaps; biplanar spectral ratios.)
- **Loop projected to line**: cascade-content visible only as edge-on shadow. The Hilbert-Pólya-style work is reverse-engineering the loop from its line projection. (RH; abelian-extension generators for arbitrary number fields.)
- **Loop is the cascade vocabulary itself**: meta-loop. (Hilbert 6: is A-N complete?)

When a cascade reveals the loop is **at a different cascade-layer than initially proposed** (the Goldbach finding — Class L was applied to a degenerate matching when the loop actually lives at the upstream Class J prime-distribution level), that's a **(b) REFINED** verdict, NOT a failure. It tells you where the loop ISN'T, narrowing where to look next.

## Verdict tiers (per Spike-research `#229` methodology)

- **(a) SURVIVES** — claim survives the cascade falsification attempt; cascade composition is structurally consistent
- **(b) REFINED** — cascade reveals a sharper formulation OR identifies the wrong cascade-layer; original claim partially holds or redirects to a different cascade composition
- **(c) FALSIFIED** — cascade finds structural inconsistency or counter-example
- **(open)** — cascade not yet dispatched; awaiting work

## Repository layout

```
docs/unsolved-maths/
├── README.md                                     ← you are here
├── REPORT_TEMPLATE.md                            ← uniform report skeleton
├── biplanar_chromatic_number/                    ← non-Hilbert prototype (cascade complete)
│   ├── REPORT.md
│   ├── descriptor.toml
│   ├── schema.json
│   ├── biplanar_graphs.ndjson
│   └── generate_catalog.py
├── hilbert/                                      ← Hilbert's 23 problems
│   ├── README.md                                 ← status of all 23
│   ├── hilbert_06_axiomatize_physics/
│   ├── hilbert_08_riemann_hypothesis/
│   ├── hilbert_08_goldbach_conjecture/           ← cascade-tractable demo
│   ├── hilbert_08_twin_prime/
│   ├── hilbert_12_kronecker_jugendtraum/
│   └── hilbert_16_limit_cycles/
└── (future sections: millennium-prize/, number-theory/, set-theory/, ...)
```

## Cascade-class quick reference (from srmech tool-schema)

| Class | Purpose | srmech surface |
|-------|---------|----------------|
| **A** | content-addressing (SHA-256) | `srmech.amsc.format.sha256_bytes` |
| **B** | TLV byte-canonical form | `srmech.amsc.tlv.tlv_pack` |
| **C** | dispatch / orientation | `srmech.amsc.dispatch.match` |
| **D** | multi-needle pattern match | `srmech.amsc.dispatch.match` |
| **E** | catalog sorted-key lookup | `srmech.amsc.naming.lookup` |
| **F** | template rendering | `srmech.amsc.template.render` |
| **G** | byte-pattern search | `srmech.amsc.search.byte_search` |
| **H** | self-introspection | `srmech.amsc.tool_schema.get_tool_schema` |
| **I** | cyclic-group / modular arithmetic | `srmech.amsc.cyclic.*` |
| **J** | prime factorisation / period | `srmech.amsc.primes.*` |
| **K** | asymptotic-DoF (pin-slot / Kepler) | `srmech.amsc.kepler.*` |
| **L** | graph Laplacian / eigendecomposition | `srmech.amsc.laplacian.*` |
| **M** | HDC bind / bundle / permute / similarity | `srmech.amsc.hdc.*` |
| **N** | rational approximation | `srmech.amsc.rational.*` |

## Reproducibility (anyone with `pip install srmech`)

```python
from srmech.amsc.catalog import register_attested_root, get_attested_dataset
register_attested_root("path/to/unsolved-maths", source="unsolved_maths_research")
ds = get_attested_dataset("biplanar_chromatic")
# Returns all cascade-output rows with full attestation
```

Each catalog is also runnable standalone:

```bash
python docs/unsolved-maths/<problem>/generate_catalog.py
```

## Not shipped to PyPI

This tree lives under `docs/` outside `docs/srmech/python/srmech/`, so it is NOT included in the `srmech` PyPI wheel. The catalogs are research artifacts; the framework primitives are the deliverable. Catalogs can be registered into a user's local srmech instance via `register_attested_root` at any time.
