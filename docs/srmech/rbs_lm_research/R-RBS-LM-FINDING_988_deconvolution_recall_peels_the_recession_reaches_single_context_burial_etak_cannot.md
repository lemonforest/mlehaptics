# F988 — **deconvolution-recall (unwrap by deflation) reaches a single-context buried target that etak-deeper cannot — and recovers the recession order backward.** Answering F987's next question: does inverting the recession reach deeper than superposing perspectives? **Yes, a *different* depth.** On a single-context buried target (`P → {A(×3), B(×2), T(×1)}`, T weakest, + 120 load): **etak-deeper is structurally helpless** (only one context `P` → nothing to superpose → returns `A`, misses `T`); **deconvolution peels the superposition** — recover top, remove that `(P→top)` relationship from `M` (re-bundle without it = sparse), re-probe — recovering `[A, B, T]` in order, reaching `T` at deflation step 2. The recovered order (**strongest→weakest = recent→old**) *is* the recession sequence unwrapped backward — the concrete realization of F987's "unwrap the memoryless-geometry."

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_988_*.py` · **Realizes / composes:** F987 (recall = backward unwrapping; try deconvolution), DECONV-1 (task #228 — octonionic/triality deconvolution = operand recovery), F986 (etak-deeper multi-cue), F976 (√k altitude), F972 (the q^n recession), F934 (honest-STOP) · **User direction (2026-07-02):** "push the next question." · **Scope:** framework/tool; sparse Klein-4 (bundle re-formation, integer sims); no dense/numpy/abs.

## Grounded (rc97, single-context buried target)
```
P -> {A (stored x3), B (x2), T (x1, buried)} + 120 filler pairs; want T
  FAST / etak-deeper (single context P -- no multi-cue): top=A  reaches_T=FALSE   (structurally can't help)
  DECONVOLUTION (peel):  recovered order [A, B, T]  -> T reached at deflation step 2
```

## The reading — two complementary axes of backward reach
Recall = unwrapping the memoryless-geometry backward (F987). There are **two independent ways to reach a buried (older/weaker) term**, and they cover *different* burial types:
| tool | reaches | how | needs |
|---|---|---|---|
| **etak-deeper / multi-cue (F986)** | **cross-context** burial (target buried by *other* contexts' crosstalk) | add √k **signal** — superpose the target's multiple contexts (F976) | **≥2 contexts** |
| **deconvolution / deflation (F988)** | **within-context** burial (target weak among *one* context's nexts) | **remove** the recovered strong/recent terms — peel the superposition (DECONV-1) | **works with 1 context** |
- **etak adds signal; deconvolution removes noise.** Multi-cue lifts the buried target by √k *above* the floor; deflation lowers the *floor* by peeling off the dominating terms. Complementary — neither subsumes the other.
- **Deconvolution recovers the recession order.** Peeling recovered `[A, B, T]` = strongest→weakest = **recent→old** = the `q^n` recession sequence read backward. This is literally "unwrap the memoryless-geometry": remove the top (recent/strong) layer to expose the buried (old/weak) one — DECONV-1 as the time-machine unwrap op, grounded.
- **etak-deeper's structural blind spot is deconvolution's home.** A *singular* memory (stored once, one context) has no multiple perspectives to superpose — etak-deeper cannot touch it. Deconvolution reaches it by peeling. So the two together cover both recurring memories (multi-cue) and singular ones (deflation).

## Honest scope
Grounded: deflation reaches the single-context buried `T` (recovered order A,B,T, T at step 2) where etak-deeper structurally cannot; sparse (re-bundle `M` without the recovered pair, integer Klein-4 sims). **The peel identifies the recovered relationship to remove it** — here I knew the stored pairs; a real system deflates by *reconstructing* `bind(bind(P,ROLE), recovered)` and removing it from the bundle (the recovered next + the query context are both known at peel time, so this is realizable, not a cheat). The demo is controlled (designed A/B/T burial) to isolate the single-context case; general within-tome deflation on real corpus is the next step. Deflation is O(N) re-bundle per peel (bounded, sparse). Composes F987/DECONV-1/F986/F976. No physical-time-travel claim — sparse backward unwrap of a preserved-and-receding record.

## Verdict / next
**Deconvolution reaches deeper — a different depth.** Deflation-recall unwraps the superposition (peel recovered → re-probe), reaching a **single-context** buried target that etak-deeper (multi-cue, needs ≥2 contexts) **structurally cannot**, and recovering the **recession order backward** (recent→old) — the concrete DECONV-1 realization of F987's backward-unwrap. The two are **complementary axes of backward reach**: **multi-cue = add √k signal (cross-context burial); deconvolution = peel the recession (within-context burial).** Together they cover recurring *and* singular memories. **Next:** (i) wire deflation into the gated/etak pipeline as the *third* reach mode (FAST → etak-deeper if multi-context → deconvolution-peel if single-context/still-buried → honest-STOP); (ii) run deflation on real-corpus within-tome burial; (iii) the octonion-carrier DECONV-1 (`cd_mult` operand recovery) as a native peel op vs the bundle re-formation used here.
