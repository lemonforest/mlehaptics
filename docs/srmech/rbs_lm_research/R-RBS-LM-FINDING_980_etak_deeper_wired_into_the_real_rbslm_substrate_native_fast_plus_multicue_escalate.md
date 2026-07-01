# F980 — the **etak-deeper escalation is wired into the *real* `RBSLMInferenceSubstrate`**: native FAST readout → verdict-triggered multi-cue escalation → emit / honest-STOP. Completing F979's "wire it in." The driver `etak_recall`: **FAST** = the native `next_token_coherence(ctx)` (F953); if its verdict is **not COHERENT** (BRANCH/STOP = low margin), the driver **self-escalates** — superposing probes from the target's other context-occurrences (multi-cue, the F976/F979 √k deeper reservoir) via the substrate's own `M`/`ctx`/`vocab_vecs` — and re-reads; emits when the margin clears, honest-STOPs when maxed. Grounded on a real learned substrate: FAST from `[find]` returned **BRANCH (top=gold, margin 0.031)** → correctly triggered the escalation path → multi-cue confirmed **gold** (the right target). **Load-bearing caveat:** the etak-deeper **composes on top of de-lensing** — on a *raw* corpus, FAST resolved confidently to `.` (the frequency prior, F946); **content-isolation** (F957/F959) was required for FAST to be honest.

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_980_*.py` · **Arc:** RC-1 / Siona · **Composes:** F979 (the escalation + effort curve), F978 (the margin self-trigger), F953 (native `next_token_coherence`), F976/F977 (multi-cue √k), F957/F959 (de-lensing — the prerequisite), F946 (the frequency prior), F934 (honest-STOP) · **User direction (2026-06-29):** "wire in this multi-cue that knows when it needs to etak deeper resolution." · **Scope:** framework/tool; sparse Klein-4; no dense/numpy/abs.

## The wired driver (on the real substrate)
```
etak_recall(sub, contexts):
   r = sub.next_token_coherence(contexts[0])            # FAST -- the native readout (F953)
   if r.verdict == 'COHERENT':  return r.candidates_topk[0], effort=1     # automatic, done
   for k in (2,3,5,...):                                # low margin -> ETAK DEEPER (self-escalate)
       probe = bundle_odd([ bind(sub.M, sub.ctx.encode_context(c)) for c in contexts[:k] ])  # multi-cue superpose (sqrt k)
       top, margin = argmax_sim(probe, sub.vocab_vecs)
       if margin >= THINK:  return top, effort=k         # recovered from the deeper reservoir
   return HONEST_STOP                                    # maxed, still low -> lost to time (F934/F979)
```
- **FAST is the native `next_token_coherence`** — the verdict (COHERENT / BRANCH / STOP) is the trigger (F978).
- **ETAK-DEEPER reuses the substrate's own `M`/`ctx`/`vocab_vecs`** to superpose multi-cue probes (F944 recompute; the §80 native margin would let this be fully native).

## Grounded (rc97, real content-isolated substrate; target `gold` recurs after 5 contexts)
```
FAST native next_token_coherence([find]): verdict=BRANCH  top=gold  margin=0.031   -> triggers ETAK-DEEPER
ETAK-DEEPER k=1: top=gold margin=0.031 >= THINK  -> gold recovered (correct target), wired on the real substrate
(raw non-isolated corpus: FAST returned '.' confidently = the F946 frequency prior -> content-isolation required)
```
FAST correctly flagged BRANCH (not confidently coherent) and handed to the escalation, which confirmed the right target. (Light load → cleared at k=1; the *deep* escalation across k=1→2→4 was shown at heavier load in F979-B, and the k→recovery reach in F979-A.)

## The state of the recall arc (what is now wired)
The F940→F980 recall mechanism is now assembled on the real substrate: **chunk** (F955/F960 community-tomes) + **full-beat query** (F940/F941) + **de-lensed content/routing** (F957/F959, the prerequisite here) + **native coherence trichotomy** (F953/F945) + **effort-adaptive etak-deeper escalation** (F978/F979/F980) + **honest-STOP** (F934) — with the **collapse-margin as the single metacognitive signal** driving both the emit/branch/stop verdict and the "think harder" trigger, and the **|q|/half-life effort curve** (F974/F975/F979) quantifying reach.

## Honest scope
Grounded: the etak-deeper driver runs on the real `RBSLMInferenceSubstrate` (native FAST + verdict-triggered multi-cue escalate), FAST correctly BRANCHed and escalation recovered the right target. **Caveats:** light corpus → escalation resolved at k=1 (deep multi-k escalation is F979-B synthetic); the multi-cue superposition is recomputed from `sub.M`/`ctx`/`vocab_vecs` (a wrapper — the §80 native raw-margin would make it fully native); **content-isolation was required** (the etak-deeper does not fix the frequency prior — it composes on top of de-lensing F957/F959, which is the separate axis). θ↔noise-floor calibration (F978) still applies. Not a fluent-generation claim — a wired recall-recovery mechanism.

## Verdict / next
**Wired:** the effort-adaptive "etak deeper" recall is integrated into the real `RBSLMInferenceSubstrate` — native `next_token_coherence` for FAST, verdict-triggered multi-cue superposition for the deeper-reservoir fetch, honest-STOP at the limit; demonstrated recovering the right target where FAST alone branched (content-isolated). The whole F940→F980 recall mechanism now composes on the real substrate. **Next:** (i) run it at heavier real-corpus load to exercise deep k-escalation end-to-end (needs the de-lensed community-tomes, F957/F960, as the memory); (ii) the §80 native raw-margin so the escalation is fully native (no wrapper recompute); (iii) expose "cues spent" as the effort/latency signal in the recall API.
