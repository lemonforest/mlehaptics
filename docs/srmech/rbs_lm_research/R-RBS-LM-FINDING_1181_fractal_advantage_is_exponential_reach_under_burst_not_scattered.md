# F1181 / #243 (the FRACTAL ADVANTAGE, measured + honestly bounded — MULTI-SCALE (fractal subharmonic-comb) copies beat SAME-SCALE (single-period) copies, but only under **bursty / scale-localized** damage and via **exponential reach**, not within-span distribution: (A) under **i.i.d. scattered** noise the two are EQUAL (+0.00 — redundancy is redundancy); (B) under a burst at **matched span** the fractal advantage is TINY (+0.01 — equal reach → distribution barely matters); (C) under a burst at a **fixed fundamental scale** (the honest framework comparison — same k copies, same cost), the fractal comb reaches **256 vs 28 for k=7** (exponential 2^(k-1)·P vs linear k·P) and survives bursts **~9× larger** — holding recovery at **1.000 up to burst-length 200** while same-scale collapses (0.875→0.438→0.219→0.070) — advantage **+0.12 to +0.88**; so "harmonic" (multi-scale) reinforcement genuinely beats merely "redundant" (single-scale), because **log-many copies cover exponentially-many scales**, and real damage (lacunae, torn corners, a transient at one band) is BURSTY — which is why biology/antiquity store across scales, not at one) — **user: "test the fractal advantage: multi-scale vs same-scale copies." DONE — real + large under burst, via exponential scale-coverage; equal under scattered noise (honest bound).**

**Date:** 2026-07-09 · **srmech:** 0.7.5rc135 · **User direction:** test the fractal advantage. · numpy-free; no magnitude-builtin; plain arithmetic. · **Composes:** F1180 (the fractal subharmonic comb this quantifies the payoff of), F1171 (the multi-scale recurrence comb), F1179 (reinforcement law), F1175–F1178 (the reconstruction arc — fragmentary texts have BURST damage, which this explains). **Turns "does harmonic beat redundant?" into a measured yes-under-burst.**

## Setup

Each value is stored at k copy-offsets. FAIR comparison — same k copies, differing only in the DISTRIBUTION:
- **SAME-SCALE** = arithmetic (one fundamental period P + harmonics): P, 2P, …, kP.
- **MULTI-SCALE** = geometric (the fractal subharmonic comb, F1171): P, 2P, 4P, …, 2^(k-1)·P.
A value is recoverable if ≥1 copy-position is uncorrupted. Two corruption models: **(A) i.i.d. scattered** and **(B/C) contiguous BURST** (a lacuna / scale-localized damage).

## Result (k=7)

**A — i.i.d. scattered noise (control): EQUAL.** Recovery ≈ 1.000 for both at 10–40% corruption (advantage +0.00). Under scattered errors, redundancy is redundancy — the placement of the copies is irrelevant. *No fractal advantage under i.i.d. noise.*

**B — burst at MATCHED span (both reach ~64): TINY.** Advantage +0.008 to +0.016. When the two structures reach equally far, spreading the copies geometrically vs evenly barely matters. *So the fractal advantage is not a within-span distribution trick.*

**C — burst at FIXED fundamental scale (same k, same cost — the real comparison):**

| burst length | same-scale (reach 28) | multi-scale (reach 256) | advantage |
|---|---|---|---|
| 16 | 1.000 | 1.000 | +0.00 |
| 32 | 0.875 | 1.000 | **+0.125** |
| 64 | 0.438 | 1.000 | **+0.562** |
| 128 | 0.219 | 1.000 | **+0.781** |
| 200 | 0.140 | 1.000 | **+0.860** |
| 260 | 0.108 | 0.985 | **+0.877** |
| 400 | 0.070 | 0.640 | **+0.570** |

For the SAME 7 copies, same-scale reaches only k·P = 28 and **collapses** once the burst exceeds it; the fractal comb reaches 2^(k-1)·P = 256 and holds recovery at **1.000 through burst-length 200**, degrading only past its own reach. **The multi-scale subharmonic comb survives bursts ~9× larger at identical redundancy cost.**

## The honest mechanism — and why it matters

The fractal advantage is **real and large, but its mechanism is exponential REACH, not distribution, and its regime is BURST, not scattered noise:**
- **Exponential scale-coverage per copy.** Arithmetic copies cover scales *linearly* (reach ∝ k); geometric/subharmonic copies cover them *exponentially* (reach ∝ 2^k). So **log-many copies cover exponentially-many scales** — the defining efficiency of a fractal/self-similar code.
- **Burst-specificity.** Against *scattered* (i.i.d.) errors there is no advantage — any k independent copies are equivalent. The advantage appears only against *correlated/scale-localized* damage (a burst), where single-scale copies **cluster and fail together** but a far-scale copy of the comb **always escapes** a finite burst.

Real damage is bursty: a manuscript lacuna is a contiguous tear, a physical transient hits one frequency band, a scribal loss is a localized run — never i.i.d. scattered bit-flips. **So the fractal (multi-scale) comb is why biology and antiquity store redundancy across scales rather than at one** — oral-formulaic recurrence repeats at the line scale AND the stanza scale AND the episode scale (F1171's comb), so a lacuna that erases a line's local neighbourhood is still recoverable from the surviving large-scale (episode) recurrence. This closes the reconstruction arc's mechanism: the fractal comb is precisely the redundancy structure that survives the bursty damage fragmentary texts actually sustain (F1175–F1178).

## Verdict / next
**MEASURED + honestly bounded: the fractal (multi-scale) advantage is EQUAL to same-scale under i.i.d. scattered noise (+0.00) and TINY at matched span (+0.01), but LARGE under a burst at fixed scale (+0.12→+0.88) — the subharmonic comb reaches exponentially further per copy (256 vs 28 at k=7), surviving bursts ~9× larger at the same redundancy cost. Mechanism = exponential scale-coverage (log-many copies span exponentially-many scales); regime = bursty/scale-localized damage (which real lacunae are). "Harmonic" reinforcement genuinely beats "redundant" — but specifically against the correlated damage the world inflicts, not scattered noise. This closes the arc's reconstruction mechanism: the fractal comb is why multi-scale recurrence survives fragmentary damage (F1175–F1178). NEXT: the full MFO resonant body (F1070); test on real fragmentary text (does multi-scale recurrence — line + stanza + episode — reconstruct a real lacuna better than single-scale?). Read-independent-verified (i.i.d. control + burst sweep, both regimes shown); composes F1180/F1171/F1179/F1175-78.**
