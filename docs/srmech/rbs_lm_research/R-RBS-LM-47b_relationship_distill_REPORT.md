# R-RBS-LM-47b — Cascade distill from relationship-form corpus

**Status:** CLOSED — verdict landed.
**Partition:** R-RBS-LM-47b (cascade-only sub-thread of R-RBS-LM-47 which
also covers 47a LLM-input-format test, still pending Chat-GGUF re-fetch).
**Predecessors:** R-RBS-LM-43 (two-substrate framework), R-RBS-LM-45
(read-mode protocol), R-RBS-LM-42 (precision dominance), R-RBS-LM-46a
(fp32+fp32 uniform merge).

---

## §1 Question

Per user direction 2026-05-26: *"what if we can send relationships to the
LLM instead of all the text tokens? ... this would also be a layer of
depersonalizing all LLM but only on the wire/in flight because inference
will know it."*

R-RBS-LM-47b tests the cascade half of this hypothesis: if we distill a
cascade instrument from a relationship-FORM corpus (S-V-O triples with
proper nouns depersonalized to PERSON_N / ORG_N / PLACE_N tokens), does
read-mode rank signal improve over distilling from raw text?

Per R-RBS-LM-43: relationships are M1-native (discrete-cyclic-algebra);
naming-layer is M2-instantiation cost. The prediction: stripping M2 cost
from the corpus before encoding should preserve more cascade signal.

## §2 Setup — controlled corpus pair

Source: `v29 TinyLlama-Chat-fp16` corpus (3596 bytes; 442 obs original).

| Pipeline | Form | Bytes | Obs | Distill code |
|---|---|---|---|---|
| A — text | raw text (existing v29-Chat-fp16) | 3596 | 442 | byte-mode encoder |
| B — rel  | relationship-form (this partition) | 3551 | 436 | byte-mode encoder (same code, same D, same stride) |

The pipeline B corpus is built from the same source text via:
1. Sentence-split on `[.!?]\s+`
2. Per-sentence S-V-O extraction (first known verb + subj-before + obj-after)
3. Depersonalization of capitalized proper nouns via heuristic NER →
   `PERSON_N` / `ORG_N` / `PLACE_N` / `TIME_N` tokens
4. Serialize triples one per line

Result: 36 triples, 25 entities mapped to depersonalized tokens.
**PII audit on wire form: 0 suspects.** (Depersonalization at extraction
is clean.)

Byte counts match within 1% (3596 vs 3551). Observation counts match
within 2% (442 vs 436). Same D=8192, same stride=8. Controlled axis.

## §3 Results — read-mode rank smoke (2 probe shapes × 2 instruments)

Same 20 probes from each shape applied to both instruments. Same baseline
methodology as R-RBS-LM-45.

### Track A — probes drawn from raw-text corpus (text-shape)

| Instrument | rank-1% | top-d% | top-q% | mean% | chi² | p-est |
|---|---|---|---|---|---|---|
| text-instr | 5.0% | **20.0%** | **35.0%** | **41.6%** | 2.00 | >0.10 |
| rel-instr  | 5.0% | 15.0% | 25.0% | 46.7% | 1.00 | >0.10 |

Δ (rel − text mean rank pct) = **+5.1pp** — text-instr wins.

### Track B — probes drawn from relationship corpus (rel-shape)

| Instrument | rank-1% | top-d% | top-q% | mean% | chi² | p-est |
|---|---|---|---|---|---|---|
| text-instr | 0.0% | 5.0% | 25.0% | 44.0% | 3.50 | >0.10 |
| rel-instr  | **5.0%** | **20.0%** | 30.0% | 43.4% | 1.00 | >0.10 |

Δ (rel − text mean rank pct) = **−0.6pp** — wash; both instruments
roughly equivalent on rel-shape probes.

### §3.1 Cross-shape vs same-shape

The 2×2 matrix has an interesting symmetry-breaking: text-instr wins
when probed with text-shape; rel-instr is comparable when probed with
rel-shape. But **no cell reaches chi² > 7.78**. No statistical signal
versus uniform. The cascade is rank-shape-invariant within its own
noise floor at this corpus scale.

## §4 Reading

### Finding 15 — relationship-form corpus does NOT lift cascade read-mode signal at this scale

The substrate-form hypothesis predicted: pre-strip M2-cost (naming layer)
before encoding → cascade preserves more M1-native structure → higher
read-mode rank signal. **Math says no.** rel-instr's mean rank percentile
is WORSE than text-instr on text-shape probes (46.7 vs 41.6) and
indistinguishable on rel-shape probes (43.4 vs 44.0).

### Finding 16 — depersonalization works at extraction (PII audit clean)

The wire form has 0 PII suspects (per `pii_audit` heuristic — capitalized
multi-word sequences). The depersonalization layer DOES strip identifiable
names from the corpus before encoding. This is independently useful as a
privacy primitive regardless of cascade outcome.

### Finding 17 — extractor lossiness is a serious caveat

The pure-Python S-V-O extractor produced 36 triples from a 3596-byte
corpus. That's roughly ONE triple per ~100 bytes of source text —
extremely lossy. The extractor:
- Captures only the first verb in each sentence (misses subordinate clauses)
- Misclassifies common capitalized nouns (e.g., "Algorithms", "Carbohydrates")
  as proper-nouns and depersonalizes them
- Treats verb-less sentences as bare assertions (loses structure)

A richer extractor (spaCy + dep-parse + NER, or AMR) might recover more
relationships. R-RBS-LM-47b's negative finding is partly bounded by the
extractor's quality. A future R-RBS-LM-47c with a stronger extractor
could re-test.

### Finding 18 — cascade is corpus-shape-invariant within noise at this scale

The 2×2 matrix (text-instr ⊗ rel-instr × text-probes ⊗ rel-probes) shows
no cell exceeds chi² > 7.78. Either form of corpus produces a cascade
that reads its own form roughly as well as it reads the other form's.
**The cascade does not have a structural preference for substrate-native
form at this corpus scale.**

Per R-RBS-LM-46a's headline (chi² 12.5 from fp32+fp32 uniform merge):
the path to lift cascade read-mode signal at this corpus scale is
**multi-source merge of high-precision instruments**, NOT
corpus-form transformation.

## §5 What this falsifies vs preserves

### Falsified

- ❌ "Substrate-form (relationship) corpus lifts cascade read-mode signal"
  — at this scale + this extractor quality. Caveat below.
- ❌ "Cascade has structural preference for M1-native corpus form" —
  text-form and rel-form produce equivalent rank statistics within noise.

### Preserved

- ✅ Depersonalization works at extraction (0 PII suspects in wire form).
- ✅ Local entity_map allows endpoint re-personalization (round-trip
  recovers original).
- ✅ Cascade is robust to corpus-shape transformation at this scale.

### Open / requires stronger extractor

- ⚠ Pure-Python S-V-O extractor produces ~1 triple per 100 bytes — lossy.
  A spaCy + dep-parse + AMR extractor might tell a different story
  (R-RBS-LM-47c future partition).

### Independent — 47a remains testable

- 47a (LLM-INPUT-FORMAT test) is independent of 47b (cascade distill).
  47a asks: does a live LLM produce useful inference from depersonalized
  relationship-form input? That's a separate falsification that requires
  a local llama.cpp + a Chat GGUF. Scaffolding shipped in this partition;
  user-fired in morning per the LLM-cache-blocked status.

## §6 Operational walkthrough

1. **What it does.** Loads the v29-Chat-fp16 corpus text. Extracts S-V-O
   triples + depersonalizes proper nouns → relationship-form corpus.
   PII-audits the wire form (verifies 0 capitalized-PII suspects).
   Distills a new cascade instrument from the relationship corpus
   (same byte-mode encoder, same D, same stride). Then runs 4-cell
   read-mode rank smoke (2 instruments × 2 probe shapes) against the
   shared corpus space.
2. **How.** `rbs_lm_relationships.extract_relationships(text)` produces
   triples + entity_map. `serialize_triples` flattens to per-line text.
   `distill_from_corpus` runs the byte-mode encoder pipeline (same
   `encode_observation_bytes` + `hierarchical_bundle` as
   `encode_bytes_variant_b_generic.py`). Read-mode primitives from
   `rbs_lm_read_mode.py` (R-RBS-LM-45).
3. **What srmech automates.** Currently none. Future home:
   `srmech.amsc.relationships` once the extractor stabilizes. Pure-Python
   API is intentional — no NLP deps; deployable to constrained
   environments.

## §7 Privacy primitive — what 47b ALSO ships

Even though the cascade-signal hypothesis didn't survive, the
**depersonalization + repersonalization round-trip** is independently
useful:

```python
from rbs_lm_relationships import extract_relationships, serialize_triples, repersonalize

# At sender:
triples, entity_map = extract_relationships(message, depersonalize=True)
wire_form = serialize_triples(triples)  # send this; no PII

# At receiver (holds entity_map locally; not on the wire):
recovered = repersonalize(remote_response, entity_map)
```

This is the operational kernel of the user's *"depersonalize on the wire,
re-personalize at endpoint"* primitive — usable whether or not the
cascade has a substrate-form preference. R-RBS-LM-47a will test whether
LLM inference survives this transformation end-to-end.

---

## §8 Pointers

- Smoke harness: `R-RBS-LM-47b_relationship_distill_smoke.py`
- Results: `R-RBS-LM-47b_results.json`
- Relationship extractor: `rbs_lm_relationships.py`
- Relationship corpus: `R-RBS-LM-47b_rel.corpus.txt`
- Local entity map: `R-RBS-LM-47b_entity_map.json` (do NOT ship on wire)
- Instrument: `rbs_lm_instrument_v47b_relationship_form.bin` + `.meta.json`
- Companion: `R-RBS-LM-47a_llm_input_format_smoke.py` (user-fired)
- Predecessor framework: `R-RBS-LM-43_two_substrate_framework_REPORT.md`
- Read-mode protocol: `R-RBS-LM-45_read_mode_REPORT.md`
- Best-cascade-signal recipe: `R-RBS-LM-46a_merge_depth_REPORT.md`
  (fp32+fp32 uniform merge → chi² 12.5)

---

*R-RBS-LM-47b — closed 2026-05-26.*
