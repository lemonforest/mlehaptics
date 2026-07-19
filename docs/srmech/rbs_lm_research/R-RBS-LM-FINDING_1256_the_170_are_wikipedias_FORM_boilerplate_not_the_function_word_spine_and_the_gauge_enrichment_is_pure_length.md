# F1256 — the 170 conserved-core tokens are **Wikipedia's own FORM/boilerplate vocabulary**, NOT the function-word spine — and F1254's prediction was falsified **by construction**, because `T.tokenize` stoplists function words before they can ever be counted. The apparent gauge-enrichment (74.71 % vs the 49.08 % baseline) is **entirely a word-LENGTH artifact** — a length-matched control gives 76.18 %. Core/accessory and gauge/curvature are **INDEPENDENT partitions**, not the same one seen twice.

**Context:** the cheap NEXT flagged by F1255. Harness `R-RBS-LM-CORE170_…py`, srmech 0.9.0rc281, importing F1255's `glyph_graph`/`gauge_decompose` **verbatim** (same code, not a re-implementation).

## Method + the ratchet (why this is trustworthy)
`section_count` **is** document frequency, so it is recomputable in ONE streaming pass (39 s) instead of a 22 h `section_counts()` re-derivation (F1253) or a genome round-trip (the organized genome has no vocab chromosome, F1254). Keying the histogram by token rather than global-id cannot change the antimode.

**A faithful recomputation must reproduce F1254 exactly. Asserted, not assumed:**

| ratchet | expected (F1254) | got | |
|---|---|---|---|
| vocab | 1,100,189 | 1,100,189 | ✅ |
| derived `k` | 10,714 | 10,714 | ✅ |
| `n_core` | 170 | 170 | ✅ |

`k_source=derived`, `bimodal=True`, `gap=250` — all reproduced. The recomputation is faithful, so what follows is comparable to F1254.

## Result 1 — F1254's structural read is FALSIFIED, and falsified *by construction*
F1254 predicted the 170 were "almost certainly the ultra-high-df **function-word spine**." They are not, and they **could not have been**:

```python
T.tokenize("The cat of the house is on a mat and it was there")
# -> ['cat', 'house', 'mat']
```

`srmech.amsc.text.tokenize` applies `DEFAULT_STOPLIST`. **Function words are removed before counting**, so they are not in the 1,100,189-token vocabulary at all. Confirmed: none of `the / of / and / a / in / to / is / was / for / on / with / that / by / as / it` appear in the core. F1254's reasoning ("the tokens the tome-tree already drops as hubs") sounded self-consistent but named the wrong mechanism — the drop happens **upstream at tokenization**, not downstream at the hub filter.

## Result 2 — what the 170 ACTUALLY are: the medium's form layer
| group | tokens |
|---|---|
| **MediaWiki markup residue** | `px` `thumb` `references` `com` `th` `de` `ii` `st` |
| **category/template scaffolding** | `category` `births` `deaths` `establishments` |
| **calendar** | all twelve months (`january` … `december`) |
| **biography boilerplate** | `born` `died` `career` `politician` `politicians` `award` `actors` |
| **geography boilerplate** | `city` `cities` `county` `district` `region` `population` `north/south/east/west` |
| **sport boilerplate** | `team` `league` `season` `played` `player` `players` `club` `football` |
| **encyclopedia-generic** | `called` `known` `used` `made` `part` `name` `named` `include` `including` |

**The conserved "core genome" of simplewiki is the encyclopedia's own structural/metadata scaffolding — the FORM layer — not the language's spine.** That is a *better* biological correspondence than F1254 reached for, and a different one: the role-analog is the **housekeeping machinery of the medium**, expressed in essentially every document/cell. But it is the *corpus format's* housekeeping, not the *language's*.

## Result 3 — the gauge enrichment is PURE LENGTH (the control kills it)
| | pure gauge |
|---|---|
| the 170 core tokens | **74.71 %** (127 acyclic, 0 cyclic-zero-holonomy, 43 curvature) |
| **length-matched random control** (20 trials) | **76.18 %** — range **69.41–80.59** |
| all types baseline (F1255) | 49.08 % |

**The core sits INSIDE the control range, slightly BELOW its mean.** Common words are short (Zipf's law of abbreviation) and short words are acyclic *by topology* — that single confound explains the whole 1.52× apparent enrichment. **Core membership contributes nothing beyond length.**

**So H-same is falsified: core/accessory and gauge/curvature are INDEPENDENT partitions.** F1255's "same partition seen twice" speculation is retired — it was flagged there as "to confirm, cheap," and the cheap check refuted it. Had the control been skipped, 74.71 % vs 49.08 % would have shipped as a real effect; it is a length artifact. (`[[feedback_read_independent_structure_check_first]]` — the control *is* the read-independent check.)

## The surface this exposes — the stoplist is an undeclared SSoT strip
`T.tokenize`'s `DEFAULT_STOPLIST` silently removes the function words **at tokenization**, so the entire simplewiki genome (F1253/F1254 stage 1 + 2) was built on a stoplisted stream. Per `[[feedback_no_doctoring_ssot_use_sublanguage_kernels]]` a strip **hides a missing kernel** — and per `[[feedback_operators_declared_operands_by_meaning]]` function words are the **OPERATORS**. Declaring operators by rule is correct; **silently deleting them before encode means the operator layer is absent from the genome entirely.** Every relationship the encode stores is operand↔operand, with the operators removed — which is a live candidate explanation for why the conserved core came out as *format boilerplate* rather than *language structure*, and plausibly bears on F1254's honest null (the 16/84 ratio failing to reproduce). **NEXT:** re-run the conservation read with `stoplist` disabled and compare — does the core become the operator spine, and does the ratio move?

## Verdict / next
Three claims, two of them corrections. (1) The recomputation is **exact** against F1254. (2) F1254's function-word prediction is **falsified by construction** — the tokenizer strips them first; the 170 are Wikipedia's form/boilerplate vocabulary. (3) The gauge-enrichment is **entirely length** — the two partitions are independent, retiring F1255's structural-read speculation. The one genuinely new object is the **undeclared stoplist strip**, which is now the highest-value thing to test.

Composes **F1255** (the gauge decomposition, imported verbatim; its "structural read" hypothesis retired here), **F1254** (the derived core — reproduced exactly, its structural read corrected), **F1253** (section_count = document frequency), **F1251** (core/accessory), `[[feedback_read_independent_structure_check_first]]` (the length-matched control), `[[feedback_no_doctoring_ssot_use_sublanguage_kernels]]` + `[[feedback_operators_declared_operands_by_meaning]]` (the stoplist strip), #231/PKG-3.
