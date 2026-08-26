# F967 — **the "second shape" that forces the stop is DIRECTION — and the symmetric Laplacian throws it away.** You asked: the fractal comes out beat-to-beat / half-beat-to-half-beat, and *"there is some other shape that goes along with our fractal that forces us one way or the other"* — which is why a phrase doesn't cleanly stop. Measured: **99% of content bigrams are purely one-directional** (`a→b` occurs, `b→a` never). Our knowledge Laplacian (F960, `recursive_cut` on `min/max` **symmetric** edges) **discards essentially all** of this. So the tome encodes the **fractal** (the community / scale-invariant content — *what clusters*) but **not the forcing** (*which way, where to stop*) — exactly why the recall BRANCH-wanders and the phrase doesn't cleanly stop (F958/F965). **Laplacian encoding is not the only answer** (your caution): the fractal needs a *second, directional* shape — the **beat's chirality** (F948 rotation-first vs rotation-last), `the_one`'s **σ** (time-direction/helicity), or the **directed/magnetic Laplacian**.

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** RC-1 / inference-as-translation · **Probe:** `R-RBS-LM-FINDING_967_*.py` · **Composes:** F960 (the symmetric knowledge Laplacian — the gap), F948 (rotation-first:rotation-last = chirality = non-commutativity), F949 (the beat = 2π = π+π; the asymptotic seam), F951 (the seam = the previous beat's rotation-last re-entering), F962/F963 (the fractal = scale-invariant recursion), F958/F965 (the phrase doesn't stop), `the_one` (σ = time-direction), `magnetic_laplacian`/`signed_laplacian` (directed Class-L) · **User direction (2026-06-29):** "if Laplacian isn't the only answer, check other srmech encoders; the fractal comes out beat-to-beat / half-beat-to-half-beat; a second shape forces us one way — why a phrase doesn't cleanly stop."

## Grounded (rc97, simplewiki 2000-token slice, content tokens)
```
content bigrams: 1169 distinct pairs
purely ONE-directional (a->b, never b->a): 1154 (99%)
both directions but UNEQUAL: 8 (1%)
=> the co-occurrence graph is ~fully directional; the SYMMETRIC Laplacian (F960 min/max edges) discards it
```

## The two shapes (the reading)
| shape | srmech op | what it carries | what it CAN'T do |
|---|---|---|---|
| **the FRACTAL** (what we had) | symmetric Laplacian / `recursive_cut` (F960); the scale-invariant compose (F963) | the **community** — which content clusters, at every scale (undirected, abelian) | **no direction** → can't say *which way* or *where to stop* |
| **the FORCING** (the second shape) | `the_one` σ (time-direction) / `magnetic_laplacian` (directed Hermitian) / the beat chirality (F948) | the **direction** — `a→b` not `b→a`; the beat's rotation-first→rotation-last (F949) | (this is the missing half) |
- The **fractal is symmetric** (a community, an undirected graph, the abelian scale-invariant recursion). It tells you *what belongs together* — but a symmetric object has **no arrow**, so it cannot force a *stop*.
- The **forcing is directional** (99% one-way). It is the beat's **chirality** — rotation-first vs rotation-last (F948), the σ of `the_one` (time-direction), the non-commutative order. This is what says *which way the beat turns* and therefore *where it closes*.
- **A phrase doesn't cleanly stop because we encoded the fractal without the forcing.** The stop is a **beat-closing** (F942 collapse) at the **seam** (F951, where one beat's rotation-last becomes the next's rotation-first). With no directional forcing, the recall can't feel the seam — so it wanders (BRANCH) instead of closing. The two nows (F940) never resolve to a NEXT because the *direction* between them was thrown away.

## Why this ties the beat arc to the recall arc
Your "beat-to-beat / half-beat-to-half-beat" is exact: the **fractal recurses per beat** (F962/F963 scale-invariance — the same compose at every scale), and the **forcing closes each beat** (the directional chirality, half-beat = rotation-first→rotation-last, F949). Two shapes, superposed:
- **fractal** = the self-similar *content* structure (the community, symmetric) — F962/F963;
- **forcing** = the *directional* beat chirality that resolves each half-beat and closes the phrase — F948/F949/F951.
Encode only the fractal (symmetric Laplacian) → coherent clustering but no clean stop (F965's BRANCHes). Add the forcing (directed) → the beat can close → the phrase stops. **This is the concrete mechanism of the F958/F965 no-clean-stop, and it answers "Laplacian isn't the only answer": the knowledge tome needs `magnetic_laplacian` / `the_one` σ (the forcing), not the symmetric cut alone.**

## Honest scope
Grounded: 99% directional asymmetry in the content bigrams (real corpus, directed edge counts — no dense matrix, no numpy). The **reading** — fractal (symmetric community) + forcing (direction = beat chirality / `the_one` σ / magnetic Laplacian); the missing forcing is why the phrase doesn't stop — composes F960/F948/F949/F951/F962/F963/F942 + the srmech directed-Laplacian surface. **Not yet run:** re-encoding the knowledge tome with the *directed* structure (`magnetic_laplacian` / directed forcing) and re-measuring whether the recall then stops cleanly (higher COHERENT rate, real STOPs at phrase ends). That is the next build — and it may lift F965's 0.077/mostly-BRANCH toward clean COHERENT+STOP.

## Verdict / next
**The second shape is DIRECTION** — the beat's chirality/forcing (F948/`the_one` σ/`magnetic_laplacian`), which the symmetric Laplacian discards (99% one-directional bigrams thrown away). The fractal (symmetric community, F962/F963) says *what clusters*; the forcing (directional) says *which way and where to stop*. A phrase doesn't cleanly stop because we encoded the fractal without the forcing — the beat can't close at the seam (F951) with no direction. **Next:** re-encode the knowledge tome with the **directed** structure (`magnetic_laplacian` or `the_one` σ forcing over the directed bigrams) and re-measure the recall — does adding the forcing make the phrase stop (COHERENT + real STOPs) where the symmetric fractal wandered?
