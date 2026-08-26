# F955 — **per-tome native coherence: chunking makes the *default* floor work** (the F954 remaining integration, done). Chunk the memory into small tomes (one `RBSLMInferenceSubstrate` each, `M` under the F896 wall), and route each recall step to the **best tome's `next_token_coherence`** — and the walk is clean COHERENT on the **default floor, no per-corpus tuning**. A small tome's margin is **0.161** (vs the 13-pair chain's 0.072), so the default 0.34 floor classifies COHERENT; route-to-best sends each context to its own tome; an unknown context → STOP. This closes the loop: native readout (F953) → native walk (F954) → **native + chunked, default-floor-clean** (F955).

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_955_*.py` · **Composes / closes:** F954 (native walk; the "wire per-tome native coherence" next-step), F953 (native `next_token_coherence`), F947 (chunking spreads margins to clear the floor), F944 (route-to-best / etak), F946 (single-M saturation), F940–F945 (the recall mechanism) · **User direction (2026-06-26):** "continue" (the F954 next step — per-tome native coherence so the default floor works on a real corpus without tuning).

## The per-tome native recall step (no tuning)
```python
def routed(context):                          # etak route-to-best across tomes
    best = None
    for s in tomes:                           # one small substrate per tome
        r = s.next_token_coherence(context)   # DEFAULT floor — no tuning
        if r.verdict != 'STOP':
            g = r.top1_floor_gap
            if best is None or g > best[1]: best = (r, g)
    return best[0] if best else None          # None == all tomes STOP -> honest-stop
```

## Grounded (rc79, 3 small topical tomes, DEFAULT floor)
```
small tome ctx[a,b] : verdict=COHERENT  margin=0.161 (vs 13-pair chain 0.072)  top1_floor_gap=0.174
routed walk:
   from a,b : c d e ...            (routed to tome-1: a b c d e)
   from p,q : r s t ...            (routed to tome-2: p q r s t)
   from m,n : o m n o m n o m n o  (routed to tome-3: m n o — fully clean COHERENT cycle)
   from zz,yy (unknown) : <STOP>   (no tome resolves it — honest)
```
- **Chunking spreads the margin → the default floor works.** A small tome (few pairs, well under the F896 wall) has top₂ far below the 0.34 floor, so `next_token_coherence` returns **COHERENT** with **no tuning** — exactly the F947 mechanism (margins spread when bundles shrink), now confirmed on the native method. The single-`M` saturated case (F954) needed a tuned floor; the chunked case does not.
- **Route-to-best routes correctly.** Each context wins on the tome whose chain it belongs to (`a,b`→tome-1, `p,q`→tome-2, `m,n`→tome-3) — the etak clump-route (F944), now over native readouts (highest `top1_floor_gap`, skip STOP).
- **Unknown → STOP.** A context no tome resolves returns `None` (all STOP) → honest-stop. The anti-hallucination contract holds across the routed ensemble.
- (Minor: the 5-token cycles show a single BRANCH at the wrap `e→a` / `t→p` — a k=2-context artifact at the cycle seam; the 3-token tome wraps fully clean.)

## The mechanism, complete and native
F940→F955 is now end-to-end on the maintainer's native readout, chunked, no tuning:
1. **chunk** into small address-routed tomes (one substrate each) — F947/F955;
2. **route** each step to the best tome's `next_token_coherence` (highest `top1_floor_gap`, skip STOP) — F944/F955;
3. **act by verdict** — COHERENT → emit, BRANCH → sample, STOP → honest-stop — F945/F954;
4. all on the **default floor** (chunking spreads margins so no per-corpus tuning is needed) — F955.

## Honest scope
Grounded on 3 small synthetic topical tomes (clean demonstration that small-tome margins clear the default floor + route-to-best + ensemble honest-stop). The cycle-wrap BRANCH is a k=2 artifact, not a failure. The **real-corpus** version needs topical partitioning of the corpus into substrates — natural unit = the simplewiki **article** (each article a tome), or F947 spectral community-tomes (with the IDF-de-lensing balanced cut F947 flagged). That partition-the-real-corpus step is the remaining scale-up; the per-tome native-coherence *mechanism* is proven here.

## Verdict / next
**Done — the F954 integration is closed:** per-tome native coherence (small tomes + route-to-best `next_token_coherence`) gives clean COHERENT walks on the **default floor with no tuning**, routes correctly, and honest-stops on unknowns. The F940–F955 recall mechanism is native, exact, trichotomy-aware, chunked, and tuning-free. **Next (scale-up):** partition a real corpus into per-article (or F947 community) tome-substrates and run the routed native-coherence walk on it — the last step from synthetic tomes to a real corpus.
