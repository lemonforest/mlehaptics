# F1257 — with the stoplist DISABLED the conserved core **absorbs the operator spine exactly**: all **94 added tokens are DEFAULT_STOPLIST members**, 94/94, and 21/22 probe operators enter the core. But the core/accessory **RATIO does not move** (0.0155 % → 0.0216 %, still ~740× off the attested 16 %). So the strip was a **real defect in what got encoded** and was **never a candidate cause of the ratio failure** — two independent issues, now separated. **+ a hard srmech gap: `tokenize` drops ALL single-character tokens even in raw mode, so `a` and `I` are unrepresentable.**

**User (2026-07-19):** *"re-run the conservation read with the stoplist disabled."* The highest-value NEXT from F1256. Harness `R-RBS-LM-NOSTOP_…py`, srmech 0.9.0rc281, both arms in one run, `k` **derived** (never picked) in both.

## The ratchet
The stoplisted arm must still reproduce F1254 or the comparison is void: **vocab 1,100,189 ✅ / k 10,714 ✅ / n_core 170 ✅.** It does.

## The two arms
| | vocab | derived `k` | gap | core | core % |
|---|---|---|---|---|---|
| stoplisted (F1254) | 1,100,189 | 10,714 | 250 | 170 | **0.0155 %** |
| **raw (`stoplist=None`)** | 1,100,333 | **12,090** | 171 | **238** | **0.0216 %** |

Both `k_source=derived`, both `bimodal=True`.

## Q1 IDENTITY — YES, decisively: the core absorbs the operator spine
**All 94 tokens added to the core are `DEFAULT_STOPLIST` members. 94 of 94.** Not "mostly" — every single one:

> about after against all also an and another are around as at back be because been before being between both but by can did do during each first for from had has have he her him his however if in into is it its like many may more most new no not now of old on one only or other out over same she so some such than that the their them then there these they this through to two under up very was well were when where which while who will with would

And 21/22 probe operators land in the core (`the of and in to is was for on with that by as it from at he she they his her`). **The one miss is `a`** — see the srmech gap below.

26 tokens dropped out (`album award com directed england europe five german germany great important include large london major members players region said season single song top usually way went`), pushed below the higher derived `k`=12,090.

**So F1256's diagnosis is confirmed: the strip hid a real kernel.** The operator layer genuinely belongs to the conserved core — it was excluded by construction, not by measurement. The form/boilerplate vocabulary is still there too; raw core = **form scaffolding ∪ operator spine**, additive rather than a replacement.

## Q2 RATIO — NO, and the reason is quantitative
| | core | accessory |
|---|---|---|
| stoplisted | 0.0155 % | 99.9845 % |
| raw | **0.0216 %** | 99.9784 % |
| attested *K. pneumoniae* (F1251) | 16 % | 84 % |

A 1.4× move, still **~740× short**. And it could not have been otherwise: `DEFAULT_STOPLIST` is **146 types**, of which 144 appear — **0.013 % of a 1,100,189-type vocabulary** (`1,100,189 → 1,100,333`). Restoring 144 types out of 1.1 M cannot move a ratio whose denominator is the open-class tail.

**This cleanly separates two things that were entangled in F1256's write-up:** the stoplist was a genuine defect in *what got encoded* (the operator layer was missing), but it was never a plausible cause of the *ratio* failure. The ratio failure remains **H2 (open-class ceiling)** — independently reconfirmed here by a third route, after F1254's derived-k null and the per-topic coherent-vs-random discriminator.

## The gauge read — LENGTH again (third time the control has earned its keep)
| | pure gauge |
|---|---|
| raw core (238 tokens) | **82.35 %** (196 acyclic, 0 flat, 42 curvature) |
| length-matched control (20 trials) | **82.67 %** — range 77.73–87.82 |

Inside the control range again. Function words are short; short words are acyclic **by topology**. Consistent with F1256 — core membership adds nothing beyond length, in either arm.

## The srmech gap (→ UPSTREAM_NOTES §105) — single-character tokens are dropped unconditionally
```python
T.tokenize("a", stoplist=None)            # -> []
T.tokenize("I", stoplist=None)            # -> []
T.tokenize("I am a cat", stoplist=None)   # -> ['am', 'cat']
T.tokenize("ox by", stoplist=None)        # -> ['ox', 'by']     (2-char fine)
```
**0 distinct single-character tokens exist in the raw 1,100,333-type vocabulary.** So `stoplist=None` is **not** raw text — there is a hard minimum-length-2 rule beneath it. English has exactly two single-letter words and **both are operators**: the indefinite article `a` and the first-person pronoun `I`. They are currently **unrepresentable in any srmech-tokenized corpus**, stoplist or not. For an operator-layer-complete encode that is a blocker, and it is why Q1 reads 21/22 rather than 22/22.

## Verdict / next
The stoplist strip is **confirmed real and confirmed narrow**. Fixing it changes *what the genome contains* (the operator layer, 94 tokens, entering the conserved core) but **not** the core/accessory ratio, which stays open-class-bound. **NEXT:** (1) re-run the two-stage genome encode with `stoplist=None` so the operator layer is actually in the stored object — it is a 35 min rebuild (F1254) and the relationships become operator↔operand rather than operand↔operand only; (2) srmech: allow single-character tokens so `a`/`I` are representable.

Composes **F1256** (the strip this tests — diagnosis confirmed, and its entanglement with the ratio now separated), **F1254** (reproduced exactly as the ratchet; the derived-k null), **F1255** (the gauge decomposition + the length control), **F1253**, **F1251** (the attested ratio that still does not transfer), `[[feedback_no_doctoring_ssot_use_sublanguage_kernels]]` (a strip hides a missing kernel — it did), `[[feedback_operators_declared_operands_by_meaning]]` (function words ARE the operators), `[[feedback_read_independent_structure_check_first]]`, #231/PKG-3.
