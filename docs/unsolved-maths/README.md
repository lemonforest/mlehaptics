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

## Verdict tiers (per Spike-research #229 methodology)

- **(a) SURVIVES** — claim survives the cascade falsification attempt; cascade composition is structurally consistent
- **(b) REFINED** — cascade reveals a sharper formulation; original claim partially holds
- **(c) FALSIFIED** — cascade finds structural inconsistency or counter-example
- **(open)** — cascade not yet dispatched; awaiting work

## Why these structures, NOT solutions

The 14 primitive class operators (A-N per srmech) form a universal vocabulary. Every observable cascade decomposes into compositions of these. Open problems are typically **cascade-shape questions** dressed as algebraic / analytic / topological assertions — the framework reading asks: which cascade composition matches the observable structure?

For some problems the cascade reveals the answer is computationally obvious once the right primitives are composed (the "didn't see the forest for the trees" cases). For others the cascade reveals a deeper open structure — a fermata at a substrate-level question. Both outcomes are valuable; this catalog records both honestly.

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
