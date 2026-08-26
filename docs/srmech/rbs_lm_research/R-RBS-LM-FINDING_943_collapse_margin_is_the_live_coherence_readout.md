# F943 — the build: the **collapse-margin (top₁ − top₂) wired as Siona's live coherence readout** — and it's *more honest* than the argmax walk. Per recall step: a **high margin** means the now **collapsed cleanly** (coherent — one hand chosen); a **near-zero margin** means the now **stayed superposed** (incoherent — no hand chosen → **honest-stop/flag**). It immediately caught what F941's argmax *masked*: only `a→b` was a confident collapse (margin **0.215**); `b→c` was marginal (**0.002** — the F896 crosstalk wall at just 4 edges), so the readout fires. The half-beat reads **0.006 from the start** (never collapses). The collapse-margin is the recall-level **anti-hallucination signal**: emit only when the now confidently collapses; say "I don't know" when it won't.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc58 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** RBS-LM / Siona · **Probe:** `R-RBS-LM-FINDING_943_*.py` · **Composes:** F942 (the now = superposition; margin = how collapsed), F941 (the full-beat recall), F933 (the coherence / order-parameter), F934 (`dispatch.infer`'s honest-OPEN residue), F896 (the 1/√N crosstalk wall), F843 (the half-beat stall) · **User direction (2026-06-26):** "wire the collapse-margin as the coherence readout."

## Result (real Klein-4 recall, threshold 0.10)
```
FULL-beat + collapse-margin readout:
   a->b  margin 0.215  coherent
   b->c  margin 0.002  INCOHERENT -> honest-stop (the now will not collapse)
HALF-beat:
   a->a  margin 0.006  INCOHERENT -> honest-stop
```
- **The margin is the live coherence signal.** `a→b` collapses cleanly (0.215); at `b→c` the now is essentially a tie (0.002 — superposed, not collapsed) → the readout **fires** and stops.
- **It exposes over-confidence.** F941's argmax produced a tidy `a→b→c→d`, but the margin shows only **one** step was a confident collapse — the rest were the bundle guessing at the F896 wall (4 edges already saturate this D). The readout makes the recall **tell the truth about its own confidence**, where the bare argmax hid it.
- **Half-beat never collapses** (0.006) — flat from the first step (the F843 stall, a now that won't resolve).

## What this gives Siona (the wired readout)
The collapse-margin is a **per-step, ~free** (it's just `top₁ − top₂` of similarities already computed) **coherence/confidence readout**:
- **margin ≥ θ** → the now collapsed cleanly → emit the NEXT (coherent advance).
- **margin < θ** → the now stayed superposed → **stop / flag / re-query** — do **not** emit a confident token for a now that didn't collapse.
This is the recall-level form of the **anti-hallucination discipline** — the same "verified or honest-OPEN" contract as `dispatch.infer` (F934), and the **coherence order-parameter** F933 asked for, now *live and per-step*: it is literally *did the beat close?* (F935) measured each step. It also **doubles as a capacity gauge**: the margin dropping at depth = the bundle is over its F896 capacity → **chunk** (split into per-tome bundles) and the margins recover.

## Honest scope
The margins (`a→b` 0.215; `b→c` 0.002; half-beat 0.006) are measured on the F941 chain (real Klein-4). The readout *correctly* flags the F896 SNR wall — so the headline is honest: with a 4-edge bundle at this D, only one confident collapse is available; the value is that the margin **says so** instead of confidently emitting marginal picks. The chirality-collapse framing composes F942/F933/F934 (reading). Wiring into `RBSLMInferenceSubstrate.next_token_distribution` (return the margin alongside the distribution; stop/flag below θ) + chunking against F896 = the next integration step.

## Verdict / next
**Wired + working:** the collapse-margin is Siona's live coherence readout — high = the now collapsed (coherent, emit); low = the now stuck/superposed (incoherent, honest-stop). It exposed F941's over-confident argmax (only `a→b` was a clean collapse) and *correctly* located the F896 wall. It is the recall-level anti-hallucination signal (F934) and the live coherence order-parameter (F933 / "did the beat close", F935). **Next:** (i) return the margin from `next_token_distribution` + honest-stop below θ; (ii) **chunk** the memory against F896 so the margins stay high deeper into the chain (the F941 derail and the early F943 stop are the *same* capacity wall — and now we can *see* it per step).
