# F1266 — **the user was right and F1265 was wrong: N/dim is NOT an invariant.** Sampled off the power-of-two grid, the same recall (0.778) occurs at **N/dim = 0.2373 at dim 2048 and 0.1780 at dim 4096** — a 1.33× shift. Doubling dim buys **1.50×** capacity, not 2× (ratio law) and not 4× (square law). So the "1/16" was an artifact of where I sampled, and the capacity relation is a **projection whose apparent value moves with the substrate parameter**, exactly as framed. **Separately: chunking revives a dead store — one big store at M=4000 recalls 0.000; sixteen chunks of dim/16 recall 1.000, and 16× faster.** **And an honest negative: the three-regime (k=3) reading is NOT supported by this object** — the flat steps are a saturation ceiling, not a mid-curve plateau.

**User (2026-07-20):** *"do the chunked stores at dim/16 each and also investigate if the N/dim ratio happens to be like our physical/mechanical coupled turn ratio? I think that all of our human research, or most, treats this like some magic number to find like pi, whereas it's more likely a projection that just happens to look slightly different from coherency and substrate differences that make finding an exact value different than finding an exact, perhaps k=3 ratio."*

## The error being corrected (mine)
F1265 reported capacity thresholds at N/dim = 1/16, 1/8, 1/4, 1/2 and called the ratio law "confirmed". But **I chose N as 2ᵏ·1000 and dim as 2ᵐ, so N/dim fell on powers of two by construction.** The clean-looking dyadic thresholds were my sampling grid, not the object. Worse, ratio-law and square-law *both* fit that data, because the two discriminating points (N=2000 and N=4000 at dim=16384) both sat on the 0.800 plateau. **F1265's "ratio law confirmed" is withdrawn.**

## Measured on a NON-DYADIC ladder (N on a 1.5× geometric ladder)
| N | N/dim @2048 | recall | N/dim @4096 | recall |
|---|---|---|---|---|
| 96 | 0.0469 | 1.000 | 0.0234 | 1.000 |
| 216 | 0.1055 | 1.000 | 0.0527 | 1.000 |
| 324 | 0.1582 | 1.000 | 0.0791 | 1.000 |
| 486 | 0.2373 | **0.778** | 0.1187 | 1.000 |
| 729 | 0.3560 | 0.333 | 0.1780 | **0.778** |
| 1093 | 0.5337 | 0.111 | 0.2668 | 0.444 |
| 1640 | 0.8008 | 0.000 | 0.4004 | 0.250 |

**The decisive comparison — same recall, different N/dim:**

| recall | N @dim 2048 | N @dim 4096 | N ratio |
|---|---|---|---|
| 0.778 | 486 | 729 | **1.50** |
| ~0.4 | 729 | 1093 | **1.50** |
| ~0.2 | 1093 | 1640 | **1.50** |

**dim doubled; capacity scaled by 1.50, consistently at three recall levels.** Ratio law predicts 2.00, square law predicts 4.00. Neither holds. And directly: recall 0.778 sits at **N/dim 0.2373 (dim 2048)** vs **0.1780 (dim 4096)** — **the ratio is not invariant, it shifts by 1.33× under a 2× change of substrate.**

**This is the user's claim, measured.** N/dim is not a constant awaiting a precise value; it is a **projection**, and its apparent value depends on the coherency/substrate parameter you happen to be at. Chasing "the exact N/dim" would be chasing a shadow's length while moving the light.

**Honest bound on the exponent.** 1.50× per doubling implies capacity ∝ dim^log₂1.5 ≈ **dim^0.585**, between linear and √. But my ladder *is* 1.5× geometric, so "one ladder step" and "1.5×" are the same quantity — with two dimensions and this resolution I can measure that the ratio law is **refuted**, not pin the exponent. A finer ladder over ≥4 dims would be needed to claim 0.585.

## The k=3 reading — NOT supported by this object
The harness counted "near-flat steps" and reported *"PLATEAU present (structure)"* for both dims. **That verdict is wrong and I am retracting it.** Reading the deltas:

```
dim 2048   +0.00 +0.00 +0.00 -0.22 -0.44 -0.22 -0.11
dim 4096   +0.00 +0.00 +0.00 +0.00 -0.22 -0.33 -0.19
```

**Every flat step is at recall = 1.000** — that is the saturation ceiling, not a distinct middle regime. Once the curve leaves the ceiling it decays monotonically with no plateau. My flat-counter conflated "ceiling" with "plateau", the same reading error F1265 made about dimension saturation.

So: **this object shows ceiling → monotone decay, i.e. TWO regimes, not three.** The k=3 reading is not supported *here*. That is a finding about this measurement, not about the framework claim in general — the user's own framing ("perhaps k=3") was offered as a hypothesis and this is the honest answer to it for this object.

## (A) CHUNKED STORES — the engineering result, and it is large
M = 4000 items, dim = 4096:

| configuration | chunks | recall | read time | total cells |
|---|---|---|---|---|
| **one big store** | 1 | **0.000** | 28.9 s | 16,384 |
| chunked, cap = dim/16 (256) | 16 | **1.000** | **1.8 s** | 262,144 |
| chunked, cap = dim/8 (512) | 8 | **1.000** | 3.6 s | 131,072 |
| chunked, cap = dim/4 (1024) | 4 | 0.750 | 6.2 s | 65,536 |

**Chunking converts a completely dead store (0.000) into a perfect one (1.000), and reads 16× faster.** Storage grows 16× while read cost *falls* 16× — each probe touches one chunk instead of all items.

That trade is the **melange shape** (F1205/#263): route and couple, never merge. It is not a compression win and should not be sold as one — it is a *routing* win, and the capacity law is what tells you the chunk size.

## Verdict / next
Three results, two of them corrections to my own prior claims. **(1) The ratio law is refuted and F1265's "confirmed" is withdrawn — N/dim is a projection, not a constant.** **(2) The k=3 three-regime reading is not supported by this object** (ceiling → monotone decay). **(3) Chunking at the measured capacity is a decisive engineering win** and is the route to corpus scale.

**NEXT:** (a) a finer ladder over ≥4 dimensions to actually pin the capacity exponent — the honest version of "what is the law"; (b) chunked stores against a real corpus with content-routed chunks, checking whether semantic routing beats hash routing; (c) the per-query index, still the only live route past O(N·dim) within a chunk.

Composes **F1265** (whose ratio-law claim and 1/16 threshold are both withdrawn here), **F1264**, **F1263**, `[[feedback_dim_size_2n_capacity_is_D_independent]]` ("chunk for capacity" — now with a measured chunk size and a measured payoff), **F1205/#263** (route and couple, never merge), `[[feedback_read_independent_structure_check_first]]`, `[[user_stance_no_information_without_value]]`, #231/PKG-3.
