# F1193 (#243) (widening the order window bigram→trigram→4-gram: grammatical placement SATURATES AT THE BIGRAM — a genuine LOCALITY ceiling, not a data one — while content recovery shows the OPPOSITE order-scaling, needing long-EXACT recurrence: on 3 pooled novels, per-position grammatical-placement accuracy jumps bag→bigram (0.076→0.197) then goes FLAT — trigram 0.199, 4-gram 0.196 (realistic/backoff) — and the honest decomposition shows this is NOT just sparsity: even WHEN the full context is seen, accuracy barely climbs (bigram 0.200 → trigram 0.203 → 4-gram 0.210, +0.010 over two orders), so grammatical placement is a genuinely LOCAL (one-token-back) phenomenon — the bigram already captures ~95% of the recoverable grammar, and the residual is local ambiguity (the/a/his all grammatical) that no amount of ORDER resolves because resolving it needs the CONTENT, not more context; meanwhile the OPERAND (rare content) tier scales the OPPOSITE way — its when-seen accuracy climbs 6.7× with order (bigram 0.012 → 4-gram 0.081) but its coverage collapses (a specific 4-gram is rarely seen twice) so realistically it stays ~0.04 — i.e. content is recoverable from LONG-EXACT context only where that context RECURS (memorization = the F1177 repetition/parallel EC), the opposite of grammar's local generalization) — **user: "widen to trigram/4-gram, keeps climbing or saturates?" ANSWERED — grammar SATURATES at the bigram (locality ceiling, +0.01 when-seen over two orders; NOT data), content scales the OTHER way (long-exact memorization, climbs when-seen 6.7× but uncoverable) — so the frame/operand split is ALSO an order-SCALING split: local generalization (grammar) vs long-exact recurrence (content).**

**Date:** 2026-07-10 · **srmech:** 0.7.5rc135 · **Corpus (Gutenberg-attested):** 3 pooled novels — A Tale of Two Cities #98 + Gulliver's Travels #829 + Pride and Prejudice #1342 (train 11981 / test 1332 sentences; grammatical canon is author-invariant, so pooling gives the higher n-grams fair data). The n-gram tables are the Class-I SEQUENTIAL model (plain-dict tallies, argmax precomputed once per context; NOT Counter, NOT a spectral proxy — the actual n-gram grammar). numpy-free; no magnitude-builtin. · **Composes:** F1192 (the bigram/both-neighbour order lift this widens), F1177 (the repetition/parallel EC — what the operand's long-exact recurrence IS), F1171 (multi-scale recurrence comb — grammar = low-order/local comb, content = high-order/sparse comb), F1179 (monotone reinforcement — here it saturates at the local scale for grammar), F1175 (the op/operand boundary, now an order-scaling signature). **The next-rung probe F1192 called for.**

## Result — two opposite order-scaling behaviours

Per-position top-1 accuracy, decomposed into REALISTIC (stupid-backoff), COVERAGE (fraction of positions whose full L-context was seen in train), and WHEN-SEEN (accuracy only where the full context was present — isolates order-value from data-sparsity):

**FRAME (grammatical) tier — 22317 positions:**

| order | realistic (backoff) | coverage | when-seen |
|---|---|---|---|
| bag (L=0) | 0.076 | 1.000 | 0.076 |
| bigram (L=1) | **0.197** | 0.979 | 0.200 |
| trigram (L=2) | 0.199 | 0.643 | 0.203 |
| 4-gram (L=3) | 0.196 | 0.226 | **0.210** |

**OPERAND (rare content) tier — 10221 positions:**

| order | realistic | when-seen |
|---|---|---|
| bag | 0.000 | 0.000 |
| bigram | 0.012 | 0.012 |
| trigram | 0.035 | 0.043 |
| 4-gram | 0.041 | **0.081** |

## Reading — the honest decomposition (and a falsified going-in hypothesis)

**Grammar saturates at the bigram, and it is a LOCALITY ceiling, not a data one.** The whole grammatical lift is the bag→bigram jump (0.076→0.197); trigram and 4-gram add nothing realistically (0.199, 0.196). I went in hypothesising "if WHEN-SEEN keeps climbing while REALISTIC saturates, the ceiling is DATA (bigger corpus extends it)." The frame result **falsifies** that: WHEN-SEEN *also* barely climbs (0.200→0.203→0.210, +0.010 over two orders), so even with perfect coverage the higher-order context would add ~1pp. Grammatical placement is genuinely **local** — the single previous token carries ~95% of the recoverable grammatical structure, and the residual is genuine local ambiguity (*the / a / his* are all grammatical in a slot) that no amount of ORDER resolves, because resolving it needs the **content**, not more grammatical context.

**Content scales the OPPOSITE way — long-EXACT recurrence, not generalization.** The operand's WHEN-SEEN climbs **6.7×** with order (0.012→0.081): a specific long context ("it was the best of ___") does pin the next content word. But its COVERAGE collapses (a specific 4-gram is rarely seen twice), so realistically it stays ~0.04. So content is recoverable from long context *only where that exact context RECURS* — which is **memorization = the F1177 repetition/parallel EC**, the opposite of grammar's local generalization. This is exactly the going-in hypothesis's *data-ceiling* shape (when-seen climbs, coverage kills it) — it held for the operand, not the frame.

**So the frame/operand split is ALSO an order-SCALING signature.** The two intrinsic factors of op(x)operand scale oppositely with context width:
- **frame / OP** — LOCAL generalization: the grammatical canon is a low-order (bigram) comb, saturating immediately (F1171's local/period-1 scale).
- **operand** — LONG-EXACT recurrence: content is a high-order, sparse comb, recoverable only at exact repetition (F1177/F1188's parallel EC; F1171's slower comb).

The responsion (F1179/F1192) is therefore **fractal in ORDER**: a fast-saturating local grammatical reinforcement plus a sparse long-range content reinforcement — the same two-scale (harmonic + subharmonic) structure the whole arc found, now on the context-width axis.

## Verdict / next
**ANSWERED — widening the order window does NOT keep the grammar climbing: it SATURATES at the bigram (realistic 0.197→0.199→0.196), and the when-seen decomposition shows a genuine LOCALITY ceiling (+0.010 over two orders even with the context present), not a data one — grammatical placement is a one-token-back phenomenon, the bigram captures ~95% of it, the residual is local ambiguity needing the content. The operand scales the OPPOSITE way: its when-seen climbs 6.7× (0.012→0.081) but coverage collapses, so content is recoverable from long context only where the EXACT context RECURS (memorization = F1177's repetition/parallel EC). So the frame/operand (implied/specified) split is also an order-SCALING split: local generalization (grammar, bigram-saturating) vs long-exact recurrence (content, sparse) — the responsion is fractal in order (F1171's harmonic+subharmonic comb on the context-width axis). Honest: my going-in when-seen→data-ceiling hypothesis held for the operand and was FALSIFIED for the frame (locality ceiling). Read-independent-verified (realistic/coverage/when-seen decomposition, train/test split, tier-split); Gutenberg-attested; composes F1192/F1177/F1171/F1179/F1175. → extends F1192 (order lift → saturates at bigram for grammar) + F1177 (the operand's long-exact recurrence IS the repetition EC).**

Sources (corpus): [#98](https://www.gutenberg.org/ebooks/98) · [#829](https://www.gutenberg.org/ebooks/829) · [#1342](https://www.gutenberg.org/ebooks/1342) — Project Gutenberg, public domain; local research use.
