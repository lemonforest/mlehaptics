# F805 — a deterministic encyclopedia-LM is buildable from simplewiki ALONE, on RBS-HDC instruments, with no cross-language translation: an article IS the FIBER (an Eulerian path) over its own shape-relationship graph (a de Bruijn graph). The exact content is already encoded in the ordered relationships — we compute the co-occurrence spectrum (F172) but never read the path back out ("we aren't looking at it"). The de Bruijn k is the F803/F804 context-constraint dial made literal: unique path = on-resonance = deterministic; many paths = off-resonance = generative. Translation is the SEPARATE open inference tool (it moves the base); deterministic-within-one-language needs only a LOCKED surface + form-parsing (markup/LaTeX, #225).

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Type:** framework reading + concrete research target (no lineage claim) · **Composes:** F804 (closed form = harmonic coupling whose resonant eigenstate is input=output), F803 (generative↔deterministic = one open↔closed axis), F802 (find C* — the null), F801 (encode→infer drift), F172 (the co-occurrence Laplacian eigenspectrum IS the storage signature), the user's stance "Fiber as spatially-absent encoding" (a fiber encodes algebraic content spatially absent until projected — the gear-tooth ℤ/n example), F796 (a genuine RBS-HDC instrument, not a borrowed host — the bar), #225 (the sub-language form kernels: markup/LaTeX), F700/F702 (clean the markup before trusting the graph), the Rosetta/cross-substrate layer R-RBS-LM-54 (translation = the open tool) · **User direction (2026-06-16):** "everything we need to solve for this is in the simple wiki. we don't even need language translation for this (except parsing markup/down/latex; i might be wrong and we do need some locked language state) — that is an inference tool. when we want a LM to give deterministic output of an article from only shape relationships, the hidden fiber content is already there and we aren't looking at it. for an encyclopedia, deterministic LM would be awesome. but this only becomes meaningful if it can be done from RBS-HDC instruments."

## 1. The article IS the fiber over its shape-graph (de Bruijn / Eulerian path)
An article's ordered relationships — its k-grams (word → next-word, with multiplicity) — form a **de Bruijn graph**. The exact article is an **Eulerian path** through it. So:
- the shape relationships = the BASE manifold (the graph);
- the specific article = the FIBER (the path) — the user's "fiber as spatially-absent encoding": the WORD ORDER is algebraically present in the relationships, spatially absent until walked out.

"The hidden fiber content is already there and we aren't looking at it" is literally true: we compute the co-occurrence SPECTRUM (F172, the storage signature) but never reconstruct the PATH from it. The reconstruction (fiber projection) is the unbuilt step.

## 2. This diagnoses the F801 drift
ENCODEINFER decoded the BAG (the base) word-by-word and discarded ORDER — so it drifted; the fiber (order/position) was exactly the discarded part. Restore the order (position-bound relationships) and the article is determined. The drift was not lossiness — it was looking at the base without the fiber.

## 3. `k` is the F803/F804 context-constraint dial, made literal
- Eulerian path UNIQUE → reconstruction deterministic → input = output → the resonance (F804).
- Graph admits MANY paths (repeats) → ambiguous → the open / generative tail.
- The context window **k** tunes it: k=1 maximally ambiguous (off-resonance, generative); larger k pins the path (on-resonance, deterministic). "More context constrains the output" is now a tunable integer — the F803 dial as a graph parameter.

## 4. Locked language state, yes; translation, no
The base must be FIXED — one locked surface language (English simplewiki) — so the path is well-defined (the user's "locked language state" instinct, confirmed). Translation MOVES the base (re-projects to another surface) → it is the SEPARATE, OPEN inference tool (the Rosetta layer, R-RBS-LM-54), NOT needed for deterministic-within-one-language. The only language work needed: **form parsing** — markup/markdown/LaTeX (the #225 sub-language kernels) — so the relationship graph is clean content, not markup noise (F700/F702). So: locked surface + form-parse, no translation.

## 5. Encyclopedia = the right first target; RBS-HDC = the constraint that makes it meaningful
An encyclopedia is where exact, attested, drift-free reproduction is DESIRABLE (the opposite of creative variation) — and it is all in simplewiki, nothing external. It only matters on **RBS-HDC instruments**: the de Bruijn graph as HDC bindings (k-grams bound; position via `permute`), the path-walk as `Class C ∘ Class M`, the unique-path / resonance test as Class-L power-iteration / Kuramoto phase-lock (`cascade.kuramoto_step`). srmech ships every op. On numpy or a trained net it would be another black box; on the HDC substrate it is grounded, GPU-free, attestable (the F796 bar).

## The first build (makes #227 concrete)
One simplewiki article → form-parse (markup/LaTeX, #225) → encode the ordered k-gram relationships as an RBS-HDC fiber (binds + position permute) → reconstruct by walking / resonating the HDC graph → measure EXACT reproduction, and characterize where it is deterministic (unique Eulerian path) vs ambiguous (the off-resonance tail), as a function of k. Storage-by-seed payoff (F804): store the graph + the resonant entry-point, regenerate the article exactly by walking — not stored prose.

## Honest scope
- A reading + a concrete target; NOT yet built. The de Bruijn / Eulerian framing is a falsifiable hypothesis (does an RBS-HDC walk reproduce a real article exactly at sufficient k?), to be tested on one article first.
- Ambiguity (repeated k-grams) is REAL and expected — it is the generative tail, not a failure; characterizing the deterministic fraction vs k is the experiment's point.
- Exact reproduction for EVERY article at finite k is not assumed — whether the resonance is always reachable is the open DUALITY F400/F401 collapse trichotomy (F803/F804).

## Verdict
A deterministic encyclopedia-LM is buildable from simplewiki alone on RBS-HDC instruments, no translation: the article is the Eulerian-path FIBER over its de Bruijn shape-graph; the content is already in the ordered relationships (we read the spectrum, not the path — F172); the context window k is the deterministic↔generative dial made literal (unique path = resonance = F804); a locked surface + form-parsing (#225) suffice, with translation as the separate open tool. Concrete first build: reconstruct one simplewiki article from its RBS-HDC-encoded ordered relationships and measure exact reproduction vs k (#227).
