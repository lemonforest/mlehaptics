# F945 — the general (branching) case: **community-tome routing + a coherence trichotomy.** Routing relationships by source/community into bounded tomes (F778/F465) keeps the single-next collapse-margins high *on a branching graph* (not just a chain); and a **low margin now splits three ways** instead of always meaning "stop": **COHERENT** (one clear next → emit), **BRANCH** (multiple *valid* nexts, both above the noise floor → a legitimate choice point, **sample**), **STOP** (top candidate near the noise floor → incoherent, honest-stop). Measured: at a branch node `a→{b,c}` both candidates read **0.56** (floor ≈ 0.34) with margin **0.00** → correctly **BRANCH (sample b/c)**, while the single-next steps `b→d`, `c→d`, `d→e` read margin **0.74–1.0** → **COHERENT**. A low margin is not always incoherence — sometimes the now is *legitimately* poised between valid hands.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc58 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** RBS-LM / Siona · **Probe:** `R-RBS-LM-FINDING_945_*.py` · **Composes:** F944 (chunk + wire the margin), F943 (the collapse-margin readout), F942 (the now = superposition), F778 (spectral-clumped community-tomes + etak routing), F465 (address-routing), F934 (anti-hallucination honest-OPEN) · **UPSTREAM:** §78 (expose the raw collapse-margin + the trichotomy classification natively) · **User direction (2026-06-26):** "yes please" (write the upstream ask + push on to community-tome routing for the general case).

## The branching graph (real Klein-4)
`a→b, a→c` (branch), `b→d, c→d` (merge), `d→e`; relationships routed by **source** into bounded tomes (the general case = spectral community-tomes, F778):
```
recall a : top [(c,0.56),(b,0.56),(e,0.26)]  margin 0.00   BRANCH -> sample {c,b}
recall b : top [(d,1.00),(i,0.25),(b,0.25)]  margin 0.75   COHERENT -> d
recall c : top [(d,1.00),(i,0.25),(b,0.25)]  margin 0.75   COHERENT -> d
recall d : top [(e,1.00),(g,0.26),(a,0.25)]  margin 0.74   COHERENT -> e
```

## The coherence trichotomy (the new piece)
A single threshold ("margin < θ → stop") is too blunt for a branching memory — it would call every real branch "incoherent." With the **raw sims** (top-1 / top-2 vs the noise floor) the low-margin case splits:

| case | signature | action |
|---|---|---|
| **COHERENT** | `top₁` ≫ floor, margin high | emit the one next |
| **BRANCH** | `top₁` *and* `top₂` ≫ floor, margin low | **sample** among the valid hands (a real choice point, not an error) |
| **STOP** | `top₁` ≈ floor | honest-stop (incoherent / noise) |

This is why the readout needs the **raw sims, not the softmaxed probs** (F944) *and* the **noise-floor** reference — to tell "two valid nexts" (branch) from "nothing resolved" (noise). The branch's low margin is the now *legitimately* superposed over multiple hands (the temperature/sampler picks one — the F942 collapse with >1 valid outcome); the stop's low margin is the now *failing* to collapse at all.

## The recall mechanism, now general
F940→F945 give the full coherent + honest Siona recall, valid for branching memories:
1. **chunk** into bounded, address-routed **community-tomes** (F778/F465) — keeps single-next margins high;
2. **full-beat query** — `bind(encode_context, ROLE_next)` (two nows → composite);
3. **read the raw-sim collapse-margin + the top-vs-floor gap** = the coherence trichotomy;
4. **act by case** — emit (COHERENT), sample among valid hands (BRANCH), honest-stop (STOP); the dropping margin *with* top-near-floor (not branch) triggers re-chunking (F896 gauge).

## Honest scope
Branch/coherent/stop measured on the branching graph (real Klein-4). The floor (0.34) is the ~0.25 random-`klein4`-similarity baseline plus a band; the community routing here is route-by-source (the clean general case — full spectral community detection is F778). The package is unmodified; the wrapper recomputes the raw-sim margin. The native exposure of the raw margin + the trichotomy inputs is the UPSTREAM §78 ask.

## Verdict / next
**Built:** community-tome routing handles the general (branching) memory with high single-next margins, and the coherence readout becomes a **trichotomy** — COHERENT (emit), BRANCH (sample valid hands), STOP (honest-stop) — distinguishing a real choice point from noise via the raw sims + the noise floor. **Next:** (i) UPSTREAM §78 — `next_token_distribution` to expose the raw collapse-margin + the trichotomy inputs; (ii) full spectral community-tome routing (F778) on a real corpus; (iii) read the live trichotomy trace over a real walk (where it emits, branches, stops).
