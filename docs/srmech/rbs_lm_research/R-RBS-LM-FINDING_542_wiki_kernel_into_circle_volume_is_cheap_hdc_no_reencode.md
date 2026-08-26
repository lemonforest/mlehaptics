# R-RBS-LM Finding 542 — **putting the wiki kernel into a circle volume is CHEAP HDC, NO re-encode: the kernel (the Class-L co-occurrence Laplacian + eigendecomposition, the one expensive step, 382 ms) is built ONCE and REUSED. The circle structure was LATENT in it — ROUTING a word to its tome is just atan2(V[:,2], V[:,1]) (a free read-out of two eigenvector columns the kernel already holds; the tome-bucketing is 0.47 ms), and the VOLUME is a Class-M bundle of per-word HVs (16–61 ms, 4–16% of the kernel). No corpus re-read, no new eigendecomposition. The per-word HV is a CHOICE, both cheap: (B1) a random identity tag stores WHICH words (tome-membership recovery 100%) but carries no inter-word structure; (B2) a spectral-derived HV — bundle over modes of bind(mode_hv, sign_token[sign V[i,m]]) — additionally CARRIES the kernel's similarity (kernel-neighbour pairs HDC-sim +0.82 vs random +0.53, gap +0.29; B1's gap is +0.00). So if you want the HDC volume itself navigable by meaning (the live-mirror walk, F541), use B2 — still no re-encode, just binds+bundles of the V-rows you already have.**

**Date:** 2026-06-07
**Arc:** RBS-LM — putting the wiki kernel into a circle volume (the user's re-encode-or-cheap-HDC question)
**Provenance:** `R-RBS-LM-CIRCLEVOL_wiki_kernel_into_circle_volume_reencode_or_cheap_hdc.py` (committed; srmech 0.7.4; Class-L kernel REUSED + `srmech.calculus.atan2` routing + Class-M `hdc.bind`/`bundle`/`similarity` volume; `perf_counter` timings). No sub-agents.
**Composes:** **F535/F537/F540/F541** (the circle shelf / live ring — *now holding the real wiki kernel*) · **F529/F538** (reversible content-addressed storage — *the volume is the semantic peer*) · **Class L** (the kernel, reused) · **Class M** (`hdc.bind`/`bundle` volume) · **F527** (odd bundle = tie-free) · **W14** (the atan2 series is slow per-call — perf addendum) · **F398/F394**. **← the circle volume is cheap HDC on the existing kernel; no re-encode; B2 carries structure, B1 only tags.**
**→ no re-encode/re-eigendecomposition to put the kernel in a circle volume: routing is a free read-out of V, the tome volume is a cheap Class-M bundle; a random-tag volume stores membership (100%), a spectral-derived volume also carries the kernel's similarity (+0.29 gap) and is meaning-navigable.**

## Result (kernel built once, 200 words, NT=7 live ring)
| step | cost | as % of kernel | what |
|---|---:|---:|---|
| **kernel** (Class-L Laplacian + eigendecomposition) | 382 ms | — | the one expensive step; built ONCE, reused |
| routing — tome bucketing | **0.47 ms** | 0.1% | the actual op: `atan2(V[:,2],V[:,1])` → tome |
| routing — `srmech.calculus.atan2` series | 1095 ms | (W14) | slow per-call series (200×40-term); one-time, cached; np.arctan2 sub-ms |
| **volume B1** (random-tag bundle) | 16 ms | 4% | stores WHICH words |
| **volume B2** (spectral-derived bundle) | 61 ms | 16% | also carries kernel similarity |

| test | B1 random-tag | B2 spectral-derived |
|---|---:|---:|
| tome-membership recovery | **100%** | — |
| HDC sim: kernel-neighbour vs random pairs | +0.00 gap (just labels) | **+0.29 gap** (+0.82 vs +0.53; carries structure) |

## Verdict
**Easy HDC — no re-encode.** The expensive part (the Class-L eigendecomposition = the wiki kernel) is computed **once** and reused. Putting it into a circle volume needs **no corpus re-read and no new eigendecomposition**: the tome **routing** is a free read-out of eigenvector columns the kernel already holds (the circle was *latent* in the kernel — the 0.47 ms bucketing is the whole op), and the **volume** is a cheap Class-M bundle (16–61 ms, 4–16% of the kernel). The per-word HV is a choice, both cheap: **B1** random tags store membership (recovery 100%) but carry no inter-word structure; **B2** spectral-derived HVs (bind mode-vectors to the sign of the word's existing V-row, then bundle) additionally **carry the kernel's similarity** (neighbour-vs-random gap **+0.29** vs B1's +0.00) — so the HDC volume itself becomes navigable by meaning (the live-mirror walk, F541) with **no re-encode**, just binds+bundles of V-rows we already have.

**Honest perf note:** the routing's wall-clock was dominated by `srmech.calculus.atan2`'s slow per-call series (1095 ms for 200 calls; `np.arctan2` would be sub-ms) — a **one-time** cost paid at kernel-build and cached as tome metadata (not per query), logged as the W14 perf addendum. It does not change the answer: the circle volume is cheap HDC, not a re-encode. Favored not privileged (F398); held open (F394).
