# F944 — the two builds, both working: **(1) chunk the memory** (route by source) so the collapse-margin stays high deep into the chain, and **(2) wire the collapse-margin into the real resonator** with an honest-stop. (1) Source-routed tomes hold **margin 0.74 across the whole chain `a→b→c→d→e`** (vs one confident step for a single N=4 bundle), honest-stopping cleanly at the chain end. (2) On the real `RBSLMInferenceSubstrate` the **raw-sim collapse-margin** (the softmaxed *prob*-margin is flattened and useless) stays coherent every step and generates `a b c d e a b c d e`. The recall mechanism is now complete: **chunked tomes (route by source) + full-beat composite query + raw-sim collapse-margin readout + honest-stop.**

**Date:** 2026-06-26 · **srmech:** 0.9.0rc58 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** RBS-LM / Siona · **Probe:** `R-RBS-LM-FINDING_944_*.py` · **Composes:** F943 (collapse-margin readout), F941 (full-beat recall), F896 (the 1/√N wall), F778 (spectral-clumped community-tomes + etak routing), F465 (address-routing), F934 (anti-hallucination honest-OPEN), F843 (the half-beat) · **User direction (2026-06-26):** "do both" (chunk against F896 + wire the margin into the real `next_token_distribution`).

## Build 1 — chunk the memory (route by source) against the F896 wall
```
single bundle (N=4)        : a->b(0.21) b->c(0.00) STOP        # crosstalk after one step
source-routed tomes        : a->b(0.74) b->c(0.75) c->d(0.74) d->e(0.74) e->-(0.00) STOP
```
Routing each relationship into a **bounded per-source tome** (the etak / F465 address-routed clump, F778) keeps every tome small enough to sit *under* the F896 wall → the collapse-margin stays at its max (**0.74**) the **whole chain**, and the honest-stop fires correctly at the end (`e`, no next stored = "I don't know what's next"). Chunking is the fix the F941 derail and F943 early-stop both pointed at — same wall, dissolved by bounding the bundle.

## Build 2 — wire the collapse-margin into the REAL resonator
On `RBSLMInferenceSubstrate` (learned `a b c d e` ×3):
```
a->b->c->d->e->a->b->c->d   collapse-margins 0.072..0.095, all >= theta=0.05  -> generated: a b c d e a b c d e
```
**Load-bearing detail:** the resonator's `next_token_distribution` returns **softmaxed probs**, whose top₁−top₂ margin is **flattened** by the softmax over the full vocab (it read 0.006 → false honest-stop). The true collapse-margin is the **raw sim** margin — `top₁−top₂` of `klein4_similarity(bind(M, encode_context), vocab_vec)` *before* the softmax. With the raw-sim margin, the readout tracks coherence correctly and the walk generates the full cyclic chain. **So the wiring must read the pre-softmax sims, not the probs** (UPSTREAM note: `next_token_distribution` should expose the raw collapse-margin / the top-sim gap, not only the softmaxed probabilities).

## The completed recall mechanism
Putting F940–F944 together, a coherent + honest Siona recall step is:
1. **chunk** the memory into bounded, address-routed tomes (route by source/community — F778/F465) so each bundle stays under F896;
2. **full-beat query** — `bind(encode_context, ROLE_next)` (two nows → composite), unbind against the routed tome;
3. **read the raw-sim collapse-margin** (top₁−top₂ of the pre-softmax sims) = the now's coherence;
4. **honest-stop** below θ — never emit a confident token for a now that didn't collapse (F934 anti-hallucination), and let the dropping margin trigger re-chunking (F896 gauge).

## Honest scope
Build 1 (margin 0.74 across the chain; honest-stop at end) and Build 2 (raw-sim margin coherent; prob-margin flattened) are both measured on real srmech (Klein-4 + the real `RBSLMInferenceSubstrate`). The source-routing here is the clean chain case (one outgoing edge per token); the general case is community-tome routing (F778). The package itself is unmodified — the wrapper recomputes the raw-sim margin from `sub.M`/`sub.ctx`/`sub.vocab_vecs`; making `next_token_distribution` return the margin natively is the upstream ask.

## Verdict / next
**Both built:** chunking (route by source) keeps the collapse-margin at 0.74 across the whole chain; the raw-sim collapse-margin wired into the real resonator gives a live, honest coherence readout (the prob-margin is flattened — use the raw sims). The recall mechanism the F930→F943 arc converged to is now operational end-to-end on the real substrate. **Next:** (i) UPSTREAM ask — `next_token_distribution` to expose the raw collapse-margin; (ii) community-tome routing (F778) for the general (non-chain) case; (iii) run it on a real corpus and read the live coherence trace.
