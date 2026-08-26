# F790 — multi-word ENTITY ("solanum lycopersicum") was hitting the ≥2-topic phrase-decline; fixed: if the queried tokens are named TOGETHER (as a phrase) in one subject's definition, resolve to that subject (→ the tomato), not decline

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** F776 (the ≥2-topic reasoner whose phrase-decline mis-fired), F788 (serve the abstract when want_abstract), F787 (same class — tokenizer splits a single unit), `[[feedback_operators_declared_operands_by_meaning]]` (a binomial is ONE operand spanning two tokens) · **User report (2026-06-16):** "explain solanum lycopersicum" (NOT a typo) → *"That reads as several things (solanum, lycopersicum)…"* — same decline as the typo'd variant.

## The gap
A scientific binomial — `solanum lycopersicum` — names **one** entity (the tomato), but the tokenizer splits it into two topics → `len(topics) >= 2` with no compare/relate cue → the F776 **phrase-decline** ("reads as several things"). The typo variant and the correctly-spelled variant failed identically, so it was never a spelling issue — it was a **multi-word-entity** gap (same root as F787: a single unit split into tokens).

## The fix (precise, no over-collapse)
Before the phrase-decline, `_resolve_entity(topics)`: is the queried phrase (`" ".join(topics)`) present **verbatim** in the gloss/abstract of some candidate subject? Candidates = the topics + their gloss/abstract-having co-occurrence neighbours (cheap — not a 216k scan). For `solanum lycopersicum`: `assoc[solanum]`/`assoc[lycopersicum]` → `tomato`; tomato's lead is *"The tomato (Solanum lycopersicum) is …"* → contains the phrase verbatim → resolve to **tomato**, serve its abstract (the ask was "explain" → want_abstract). The **verbatim-phrase** bar is what keeps it precise: `dog cat` appears in no gloss as a phrase → no collapse → the decline still fires (correct); cued queries (`compare`, `relate`) still take precedence.

## Tested (fresh instance)
- `explain solanum lycopersicum` → **tomato** abstract ("named in tomato's definition"). ✓
- `what is solanum lycopersicum` → **tomato** lead sentence. ✓
- `compare dog and cat` → COMPARE decline (cue path precedence, unchanged). ✓
- `explain solanum lycopericum` (typo, no conversation context) → resolves to **solanum** (the recognized genus) + its species relations; with context memory the usage-correction → tomato (the "maybe expected" typo case).

## Honest scope
- Resolves only when the phrase is named **verbatim** in a held definition — covers binomials / multi-word names whose components co-occur in an article lead, not arbitrary multi-token entities (e.g. a name never written together). A general phrase/n-gram index is the broader fix.
- Candidate set = topics + their top-25 assoc neighbours with a gloss/abstract; if the right subject isn't an assoc-neighbour it's missed (rare for tight binomials). srmech-native stores; no abs/CAD; not yet redeployed to the live server.

## Verdict
"solanum lycopersicum" now resolves to the **tomato** (the entity its tokens name verbatim in the held definition) instead of the ≥2-topic phrase-decline — the multi-word-entity gap (F787's class, one layer up) closed for verbatim-named binomials/phrases, precisely (cued queries + genuine word-salad unaffected). A general n-gram entity index is the broader follow-on.
