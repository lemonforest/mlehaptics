# {PROBLEM_NAME}

**Source**: {wikipedia URL section / list of unsolved problems entry}
**Status**: open / (a) SURVIVES / (b) REFINED / (c) FALSIFIED
**Cascade dispatched**: YYYY-MM-DD or "awaiting dispatch"
**Class cascade**: {e.g., A∘L∘N∘M∘I}

---

## 1. Problem statement

Formal statement of the problem, in its standard mathematical form. Cite the canonical source (Hilbert's lecture, Riemann's 1859 paper, etc.) at OA / textbook level only per `[[feedback_paywalled_doi_cannot_be_attested]]`.

## 2. Why it is open

Brief historical context: what's been tried, where the difficulty has been located, what the current best known bound / partial result is. Cite OA references with arXiv IDs where available.

## 3. Framework reading

What is this problem AS A CASCADE-SHAPE QUESTION? Reframe the statement so the 14-class operators (A-N) can address it. The reframe is the load-bearing step — most open problems become tractable once expressed in cascade-vocabulary.

Per `[[user_stance_identity_not_implementation_discipline]]`: the framework READS what the problem IS at substrate-level; it does not OVERWRITE the mathematical statement.

## 4. Cascade composition

The proposed cascade of primitive classes. Each step names:
- Which class operates
- What input it consumes (from previous step or from data)
- What output it produces (input to next step or final result)
- Why this composition is structurally appropriate (NOT result-driven)

Per `[[feedback_dont_pre_commit_spike_query_operators]]`: design the cascade for broad-query enumeration; don't lean the composition toward an expected verdict; let null findings count.

| Step | Class | Operation | Input | Output |
|------|-------|-----------|-------|--------|
| 1    | A     | content-address | … | hash |
| 2    | L     | Laplacian + eigendecompose | … | spectrum |
| 3    | N     | rationalize ratio | … | exact integer bound |
| 4    | M     | HDC encode + check | … | feasibility |
| 5    | I     | cyclic homomorphism verify | … | yes/no |

## 5. Configuration data needed (AMSC catalog)

What records does the catalog need? List the schema fields and any reference data the cascade consumes. Link to `descriptor.toml` + `schema.json` + `*.ndjson` in this directory.

## 6. Cascade execution

Reference `generate_catalog.py` in this directory. Run with:

```bash
python docs/unsolved-maths/{problem_dir}/generate_catalog.py
```

Or via AMSC bridge:

```python
from srmech.amsc.catalog import register_attested_root, get_attested_dataset
register_attested_root("docs/unsolved-maths", source="unsolved_maths_research")
ds = get_attested_dataset("{source_key}")
```

## 7. Findings

What does the cascade reveal? Report verdict-tier honestly per `[[feedback_dont_pre_commit_spike_query_operators]]`:

- **(a) SURVIVES**: cascade composition is internally consistent; no structural obstruction found. NOT a "proof" — just absence of falsification on the dispatched test set.
- **(b) REFINED**: cascade reveals a sharper reformulation. State the refined claim and what changed.
- **(c) FALSIFIED**: cascade finds a counter-example or structural inconsistency. State exactly what falsifies.
- **(open)**: cascade dispatched but inconclusive. State the open fermata.

## 8. Open fermatas

What remains open after the cascade runs? List specific testable sub-questions for future dispatches. Use spike-research numbering if dispatched.

## 9. Citations

Per `[[feedback_pdf_extraction_citation_discipline]]`: all citations PDF-verified at dispatch time. Per `[[feedback_paywalled_doi_cannot_be_attested]]`: OA / arXiv / open textbook only.

- Author Year *Journal* vol:pages — arXiv:XXXX.XXXXX (description)
- ...

## 10. Cross-references

- srmech catalog: `<source_key>` (registered via `register_attested_root`)
- Related canonical stances: `[[user_stance_...]]`
- Related spike research: Spike-research #...
- Related MFO / srmech notebook sections: §...
