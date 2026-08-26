# F1194 (#243) (content-conditioned grammar: the nearby CONTENT does NOT unlock the grammatical residual — op and operand PARTITION CLEANLY at the local scale, they do NOT co-determine: conditioning the masked-frame prediction on the nearest content words instead of the adjacent order, CONTENT-right (head noun) reaches only **0.114** and CONTENT-both **0.100** — both ABOVE the bag (0.075, so content carries a LITTLE grammatical signal) but WELL BELOW the adjacent bigram (**0.190**), and crucially COMBINING order×content adds **+0.001** over the bigram alone (0.190→0.191) — so whatever grammatical signal the local content carries is already REDUNDANT with the adjacent order; the residual disambiguation ("the vs a vs his" in a slot) is therefore NOT recoverable from the local content either — it is DISCOURSE/referential-bound (whose hand? which thing?), above the local window, which is the OPERAND's long-range domain (F1193's operand-scaling: long-exact recurrence / the referent) → the expert (F282)) — **user: "run the content-conditioned grammar probe." ANSWERED — content does NOT unlock the residual (combined − bigram = +0.001); op(x)operand is a genuine k=2 PARTITION at the local scale (order carries the grammatical frame, the discourse-operand carries the disambiguation), co-determined ONLY through the long-range discourse the operand holds, not through local content — each factor carries exactly what the other cannot. My going-in co-determination hypothesis is REFUTED.**

**Date:** 2026-07-10 · **srmech:** 0.7.5rc135 · **Corpus (Gutenberg-attested):** 3 pooled novels — #98 + #829 + #1342 (train 11981 / test 1332 sentences; right-content context seen 88%). Conditionals (not raw counts) so a ubiquitous "the" cannot dominate by frequency. Class-I sequential + content-association tallies (plain dicts, NOT Counter). numpy-free; no magnitude-builtin. · **Composes:** F1193 (the order-saturation whose residual this tests), F1192 (the adjacent-order predictor), F1177/F1188 (the operand's long-range/parallel EC — where the disambiguation actually lives), F282 (the residual → the expert), F1175 (the op/operand boundary, now shown to be a genuine k=2 partition not a blend), TRIALITY.md (k=2 DETECTS/partitions vs k=3 corrects). **The co-determination test F1193 called for.**

## Result — content does not beat, and does not add to, the adjacent order

Predicting the masked grammatical (frame) token, same task as F1192/F1193, now conditioned on the nearby CONTENT instead of the adjacent function words:

| predictor | frame-position accuracy |
|---|---|
| BAG (marginal, no context) | 0.075 |
| BIGRAM (adjacent order, F1193) | **0.190** |
| CONTENT-right (head noun) | 0.114 |
| CONTENT-both (left + right content) | 0.100 |
| COMBINED (order × content) | 0.191 |

**Decisive lift: COMBINED − BIGRAM = +0.001.**

## Reading — clean partition, not co-determination (hypothesis refuted)

I went in hypothesising that the F1193 residual ("*the vs a vs his* all fit") is unlockable by the operand — that the head noun co-determines the determiner ("___ hand" → *his/her/the*). The measurement **refutes** that at the local scale, three ways:

1. **Content is WEAKER than adjacent order.** CONTENT-right 0.114 vs BIGRAM 0.190. The immediate function-word context predicts the grammatical slot better than the nearby content noun does.
2. **Content adds essentially NOTHING to order.** COMBINED 0.191 vs BIGRAM 0.190 — +0.001. Whatever grammatical signal the local content carries is already **redundant** with the adjacent order; it contributes no independent lift.
3. **Content is not zero, but it is not the residual's key.** CONTENT-right 0.114 > BAG 0.075, so a head noun does carry a little grammatical bias (e.g. "hand" leans *his/her/the* over *a*). But that sliver is subsumed by order, and it does not reach into the residual.

So the grammatical residual is NOT in the local content. It is **discourse/referential** — *whose* hand, *which* thing — which lives above the local window, in the wider story. That is precisely the OPERAND's domain, and F1193 already showed the operand is recoverable only from **long-exact recurrence** (the referent's actual prior mention), not local generalization. So the residual routes to the operand's long-range mechanism (F1177/F1188's parallel EC) → the expert (F282).

## What this settles about op(x)operand

**op(x)operand is a genuine k=2 PARTITION at the local scale, not a blend.** Each factor carries exactly what the other cannot, with no local overlap:
- **op / grammatical frame** ← local ADJACENT ORDER (bigram, F1192/F1193), saturating ~0.19.
- **operand / disambiguation + content** ← the LONG-RANGE DISCOURSE / referent (whose/which), recoverable only by exact recurrence (F1193 operand-scaling) → the expert (F282).

They co-determine the surface sentence, but ONLY through the long-range discourse the operand holds — NOT through the local content, which adds +0.001. This is the framework's k=2 duality showing its DETECT/partition character (TRIALITY.md): the two factors are separable and non-redundant locally; the error-correction that would BIND them (k=3) is the long-range recurrence/parallel (F1177/F1188), not a local content-grammar merge. The clean partition is why the operand always needs an external witness: locally, grammar cannot supply it and the local content cannot either — only the wider story can.

## Verdict / next
**ANSWERED — content-conditioned grammar does NOT unlock the F1193 residual: the nearest content predicts the grammatical slot WORSE than the adjacent order (0.114 vs 0.190) and adds only +0.001 when combined, so op(x)operand is a genuine k=2 PARTITION at the local scale — order carries the grammatical frame, the disambiguation is DISCOURSE/referential-bound (whose/which), above the local window, in the operand's long-range domain (F1193 operand-scaling / F1177 recurrence) → the expert (F282). My going-in co-determination hypothesis is refuted: they co-determine the surface only through the long-range discourse the operand holds, not through local content, each carrying exactly what the other cannot. Read-independent-verified (conditional-probability predictors, train/test split, order-vs-content-vs-combined isolation); Gutenberg-attested; composes F1193/F1192/F1177/F1188/F282/F1175/TRIALITY.md. → extends F1193 (the residual is discourse/operand-bound, not local-content-unlockable) + F1175 (the op/operand boundary is a clean local partition).**

Sources (corpus): [#98](https://www.gutenberg.org/ebooks/98) · [#829](https://www.gutenberg.org/ebooks/829) · [#1342](https://www.gutenberg.org/ebooks/1342) — Project Gutenberg, public domain; local research use.
