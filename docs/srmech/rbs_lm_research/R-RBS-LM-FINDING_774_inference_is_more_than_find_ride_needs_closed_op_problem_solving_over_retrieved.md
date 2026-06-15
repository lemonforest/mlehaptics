# F774 — genuine inference is MORE than etak find+ride: it needs PROBLEM-SOLVING (the closed ops solve-for/derive) over the retrieved material — coherence as a RESULT, not forced

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F773 (solve-for/derive/infer — the three operators; problem-solving FUSES them), F166 (the inference-walk = the current find+ride), F704/F740 (etak = grounded find+ride), F767 (no-confabulation = the safety property retrieval-only buys), F408 (meaning/premises are SOURCED — the ceiling on what can be solved/derived), F772 (language harder than continuous math) · **User direction (2026-06-15):** "this might be important for our LM scaffolding? it's more than an etak find and ride? even inferring from a knowledge store will need to do problem solving the way biology does to get an output that isn't forced to look coherent."

## The gap, verified live
Siona's inference today = **etak find** (understand into canonical) + **etak ride** (walk the genome/relations/assoc, render). That is **retrieval + traversal** — the OPEN operation (infer, F773) in a *degenerate, retrieval-only* form. Probed on questions that require problem-solving over ≥2 facts:

| query | operation needed | result |
|-------|------------------|--------|
| "is a tomato bigger than a planet?" | **solve-for** (compare two retrieved sizes) | punts → asking-state |
| "what do a volcano and a tomato have in common?" | **derive** (a shared property) | punts → asking-state |
| "what is a tomato?" | retrieve | answers (find+ride suffices) |

So find+ride **cannot solve-for or derive**; on a multi-fact question it can only retrieve-or-punt.

## The honest nuance (it does NOT currently force coherence)
The user's worry was "output forced to look coherent." Verified: Siona currently **avoids** forced coherence — on the multi-fact questions she **ASKS** (the multi-topic guard fires) rather than stitch retrieved fragments into a fake answer. So the *safety property holds* (better to ask than fake). The real gap is the **dual**: she can't **answer** these at all — she's confined to retrieval. The risk of "forced coherence" is what a **generative** problem-solver would introduce; Siona avoids it by punting, at the cost of capability.

## The resolution — problem-solve with the CLOSED operations, not generation
"Output that isn't forced to look coherent" is precisely the **design constraint** for adding problem-solving: the answer's coherence must be a **RESULT of solving**, not an imposed surface. That rules out generative (LLM-style) problem-solving — which fabricates fluent coherence (and hallucinates). It rules **in** the **closed** operations (F773):
- **solve-for** — treat the question as a CONSTRAINT, find the stored element(s) that SATISFY it (compare stored sizes, rank, select) — determinate, attestable.
- **derive** — from RETRIEVED premises, run a NECESSARY chain to the asked consequence (intersect two relation-sets for a shared property; compose two edges) — truth-preserving, attestable.
Both are **closed** → they produce genuinely-solved (not forced) coherence, and they stay in the **no-confabulation regime** (F767) because, unlike generation, they don't invent — they solve/derive over what's stored.

## The ceiling (F408) — bounded by what's sourced
You can only solve-for / derive over **sourced premises**. Siona can compare sizes only if sizes are stored; derive a commonality only if the properties are stored. Where the premise isn't sourced (no stored size for "planet"), the honest output is still to **ASK / decline**, not invent — the F408 ceiling. So the problem-solving layer is **bounded**: it answers the multi-fact questions whose premises are retrievable, and honestly punts the rest. That keeps "more capable" from sliding into "hallucinating."

## Verdict
**Yes — inference is more than find+ride.** find+ride is retrieval (the OPEN op degenerate); genuine inference is **problem-solving** = the fused solve-for/derive/infer (F773), "the way biology does." The **safe** way to add it — the way that yields output *solved* rather than *forced-coherent*, without reintroducing the hallucination retrieval-only avoids — is a **problem-solving layer using the CLOSED operations (solve-for, derive) over the RETRIEVED material**, bounded by what's sourced (F408), with honest-ASK as the fallback (preserving F767). Next inch: prototype a "relate / compare two topics" tier — fires on ≥2 topics + a relation/constraint, attempts solve-for (compare) or derive (intersect relation-sets) over the stored facts, attests the chain, else asks. (Architectural direction; not yet built.)
