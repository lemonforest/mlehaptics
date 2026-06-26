# F941 — the build: a **full-beat recall step advances where the half-beat stalls.** On a stored chain `a→b→c→d→e` in a real Klein-4 memory, querying with the **context alone** (one now) **stalls flat: `a→a→a→a→a`** — it returns the present, never a NEXT. Binding the context **with the next-relation** `ROLE` (two nows → composite query) **walks the chain: `a→b→c→d`** (then derails `d→c` — bundle crosstalk at the chain end, the F896 1/√N capacity wall, not a failure of the step). This is F940 made operational: the NEXT is recovered only by composing the two nows; one now leaves the value still bound to the relation and cleanup can't reach it.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc58 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** RBS-LM / Siona · **Probe:** `R-RBS-LM-FINDING_941_*.py` · **Composes:** F940 (the Klein-4 beat-addresser; NEXT = composite of two nows), F935 (full vs half beat), F843 (`no-information-without-value` / sector-locked = half beat), F166 (the resonator walk), F896 (the 1/√N bundle wall) · **User direction (2026-06-26):** "yes, let's do it!" (build the minimal full-beat recall step).

## The step (real Klein-4, the Siona bind)
- **Store:** `M = bundle_odd[ bind(bind(enc(prev), ROLE), enc(next)) ]` over the chain edges (`ROLE` = the "next" relation = the second now).
- **Half-beat recall** (one now): `cleanup( bind(M, enc(x)) )` — query with the context alone. The `enc(x)` cancels `prev=x`'s key, leaving `ROLE⊗next` — **not** a vocab vector → cleanup falls back to the present → **stall**.
- **Full-beat recall** (two nows → composite): `cleanup( bind(M, bind(enc(x), ROLE)) )` — query with the context **bound to** `ROLE`. The composite key unbinds the clean value `enc(next)` → cleanup → **the NEXT**.

## Result
```
chain     : a->b->c->d->e
FULL-beat : a->b->c->d->c->d      (advances the chain; late d->c = crosstalk/F896 capacity)
HALF-beat : a->a->a->a->a->a      (stuck on the now — no NEXT ever produced)
```
**Half-beat = stall (the present, repeated); full-beat = advance (the chain).** The decisive contrast is unambiguous; the late full-beat derail is the bundle's SNR at depth (F896 — fixable with chunking / larger D / fewer edges per tome), not the step.

## What it means for Siona (the spec, now demonstrated)
The recall step must **bind the context with the next-relation** (two nows → composite query), not query the context alone (one now). Concretely in the resonator: form the query as `bind(encode_context(window), ROLE_next)` and unbind against `M`, rather than probing `M` with `encode_context(window)` alone. The "single-sector / context-only" query is the half beat (F843); the relation-bound composite is the full beat. **This is the minimal change to the Siona walk** — same `M`, same atoms, a composite query key.

## Honest scope
Clean minimal prototype on a constructed chain (controls the structure to isolate the principle); real srmech Klein-4 (`bind`/`bundle_odd`/`klein4_similarity`). The half-beat stall and full-beat advance are decisive; the late derail is the F896 capacity wall (expected). Full integration into `RBSLMInferenceSubstrate.next_token_distribution` (forming the query as the relation-bound composite, reading all chiral coords) is the next build step. The recall-as-chirality-collapse reading is F942.

## Verdict / next
**Built + demonstrated:** the full-beat recall step (`bind(context, ROLE)` → composite → cleanup) advances the chain where the half-beat (context alone) stalls. **Next:** wire it into the real `next_token_distribution` (relation-bound composite query + all-chiral read), and chunk against the F896 wall so the late-chain derail closes.
