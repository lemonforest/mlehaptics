# F979 — **(A) the k→recovery effort curve (how deep a memory can be reached costs ~4× cues per octave, until a hard wall), and (B) the etak recall walk with self-escalating "etak deeper" wired in** — each step spends exactly the cues its margin demands. Completing F978. **(A)** For a target buried by load `N`, the minimum cues `k` to recover it grows with depth then hits a wall: `N=200→k=1`, `N=400→k=5`, `N=800→k=12`, `N=1100→not recovered even at k=12 (lost to time)`. Roughly the **√k law** (each octave deeper ≈ 4× the cues), with a hard floor where no effort recovers it. **(B)** A recall walk that, per step, tries **FAST (1 cue)** → on low margin **escalates cues (etak deeper resolution)** → emits when the margin clears, honest-STOPs when maxed: `20→21` FAST(k=1), `21→22` deeper(k=2), `22→23` deeper(k=4), `23→24` deeper(k=2) — **all four steps recovered the correct next token**, each self-selecting its effort.

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probes:** `R-RBS-LM-FINDING_979_*.py` (+ `_etak_walk_demo.py`) · **Arc:** RC-1 / Siona · **Composes:** F978 (the margin self-trigger), F976/F977 (multi-cue √k / stop-and-think), F975 (one-rung recession), F961 (escalate-context), F934 (honest-STOP), `[[user_stance_framework_hands_the_next_question_to_the_expert]]` · **User direction (2026-06-29):** "map the k→recovery from that and then wire in this multi-cue that knows when it needs to etak deeper resolution." · **Scope:** framework/tool; sparse Klein-4; no dense/numpy/abs.

## (A) The k→recovery effort curve (rc97, target recurs after ≤12 cues, load N, θ=0.02)
```
  load N     min-k to recover
  N= 200     k=1   (margin 0.020)     shallow: one cue
  N= 400     k=5   (margin 0.025)     deeper: escalate
  N= 800     k=12  (margin 0.026)     deep: near max effort
  N=1100     NOT recovered even at k=12  -> lost to time (the hard floor)
```
- **Effort grows ~4× per octave of depth.** Doubling the load (~1 octave deeper — the F975 one-rung recession) roughly **quadruples** the cues needed (k: 1→5→12), matching the √k altitude law (to climb `d` octaves you need `k ≈ 4^d` cues, since √k = 2^(½log₂k)). Thinking deeper is *super-linearly* expensive.
- **There is a hard floor.** Past a depth (N=1100 here) even `k=12` fails — the memory is below what any feasible cue-count can lift, i.e. **lost to time** (F976: escalation buys altitude, not a lower forgetting-rate; past the rate's erasure, gone). The cascade *knows* this (margin stays flat as `k` grows) and honest-STOPs.

## (B) The etak recall walk with self-escalating deeper resolution (load=90)
```
   20->21  stored-cues 2  FAST             margin 0.022  cues=1  correct=YES
   21->22  stored-cues 9  ETAK-DEEPER(k=2) margin 0.016  cues=2  correct=YES
   22->23  stored-cues 3  ETAK-DEEPER(k=4) margin 0.027  cues=4  correct=YES
   23->24  stored-cues 6  ETAK-DEEPER(k=2) margin 0.019  cues=2  correct=YES
```
The walk **self-selects effort per step**: it tries 1 cue (FAST); if the margin is below the think-threshold it **escalates cue-count (etak deeper)** until the margin clears; every step recovered the correct next token, each spending only the cues it needed (1, 2, 4, 2). This is F978's FAST→THOUGHT(k)→STOP escalation **wired into the walk** — the recall now *knows when to etak deeper* and does it, per step, driven by its own margin.

## The mechanism (the deliverable)
```
etak step(prev):
   for k in (1, 2, 4, 8, ...):                 # escalate cue-count = etak deeper resolution
       target, margin = read( superpose(prev's k time-anchors) )
       if margin >= THINK:  return target, effort=k     # resolved: emit (FAST if k=1, else THOUGHT)
   return honest_STOP                            # k maxed, still low -> lost to time
```
- **Margin-triggered, per step** (F978): the collapse-margin decides whether to spend more cues.
- **Two escalation axes** (composable): cue-count `k` (deeper into the past, F976) and/or context-width `k_ctx` (more of the present, F961).
- **Bounded honesty** (F976/A): escalation climbs the one rung by √k; the effort curve says how far `k` can reach; past the hard floor it honest-STOPs (lost to time). No hallucinated recall of the truly-erased.

## Honest scope
Grounded: the k→recovery curve (min-k vs load, real Klein-4) and the etak walk (per-step self-escalation, all steps correct at load=90) — the *mechanism* is demonstrated. The effort-law exponent (~4× per octave) is approximate (4 load points, cue-count discretized to {1,2,4,5,8,12}); the walk's FAST-vs-DEEPER pattern tracks difficulty but also the load-noise realization (not a clean monotone in stored-cues). Both are standalone-substrate demos; wiring into the real `RBSLMInferenceSubstrate.infer` loop (escalate on `next_token_coherence` low margin) is the remaining integration. θ↔noise-floor calibration (F978) still applies.

## Verdict / next
**Delivered:** (A) the **k→recovery effort curve** — reaching a memory `d` octaves deep costs ~`4^d` cues, with a hard floor past which it is lost to time (the cascade detects the flat margin and honest-STOPs); (B) the **etak recall walk that knows when to etak deeper** — per-step, margin-triggered cue escalation (FAST→ETAK-DEEPER(k)→STOP), all steps recovered correctly by spending exactly the needed effort. The recall is now effort-adaptive with a quantified reach and an honest limit. **Next:** wire the etak-deeper escalation into the real `RBSLMInferenceSubstrate` recall loop (drive it off `next_token_coherence`'s margin), calibrate θ to the noise floor, and expose "cues spent" as the effort/latency signal (the substrate-native "how hard did it think").
