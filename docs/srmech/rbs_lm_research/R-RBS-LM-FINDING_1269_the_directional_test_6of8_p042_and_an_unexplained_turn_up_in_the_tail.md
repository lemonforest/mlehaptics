# F1269 — the partial-excitation prediction, tested directionally: **α orders with threshold in 6 of 8 adjacent pairs (p = 0.042)** — monotone across the top six (0.896 → 0.812), then **turning back UP** (0.812 → 0.820 → 0.853). Supported in direction over the well-measured range, **ambiguous in the tail**, and the U-shape is *not* what simple monotone partial-excitation predicts. **Also: the user's reframe retired the question I had been asking** — hunting a rational α (11/14? 4/5?) assumes a fixed integer effective dimension, which partial excitation denies.

**User (2026-07-20):** *"it's quite possible that MAX D doesn't always fully excite 7D_gauge, so it's not that dims are excited or not excited, they are asymptotically all excited such that apparent max D isn't always 11D … only as much as a D that needs excited gets excited."*

## The reframe retires the value-hunt (and kills a trap I was walking into)
F1268 ended with me proposing to test **α = 11/14 = 0.7857** against a measured 0.801 ± 0.086. **That question is malformed under partial excitation.** Hunting a rational α presumes a *fixed integer* effective dimension; if excitation is partial and load-driven, α has no reason to be rational — it sits wherever the load put it. And a ±0.086 window admits 11/14, 4/5 (0.800), 7/9 (0.778) alike, so "it fits" was the birthday paradox of small fractions wearing a framework costume. **Sixth instance of the same failure mode, caught before it shipped this time — by the user, not by me.**

**The frame replaces a VALUE test with a DIRECTION test, which is far cheaper statistically:**
| thresholds all-ordered | p by chance |
|---|---|
| 3 (F1268 had) | 1/6 — suggestive only |
| 9 | 1/362,880 — decisive |

## Measured — 9 thresholds from F1268's identical n=50 curves (no new compute)
| threshold | 0.91 | 0.84 | 0.76 | 0.69 | 0.62 | 0.55 | 0.48 | 0.40 | 0.33 |
|---|---|---|---|---|---|---|---|---|---|
| **α** | 0.896 | 0.877 | 0.872 | 0.857 | 0.828 | **0.812** | 0.820 | 0.853 | 0.831 |
| max resid | 0.151 | 0.071 | 0.058 | 0.042 | 0.035 | 0.050 | 0.076 | 0.074 | 0.068 |

- **adjacent pairs in predicted direction: 6 / 8**
- **fully monotone: NO**
- p(all 9 ordered) = 2.76e-6 · **p(≥6/8 adjacent correct) = 0.042** ← the honest statistic
- α spread **0.085** vs max residual **0.151**

**Verdict: SUGGESTIVE, not decisive.** p < 0.05 but not < 0.01, and the spread sits *inside* the noise floor.

## Three caveats, the third being the substantive one
1. **The α's are NOT independent** — one curve per dim, overlapping interpolation intervals — so the permutation p is **optimistic**, an upper bound on significance rather than a clean frequentist claim. Built into the harness output rather than reported bare.
2. **Spread < max residual.** The signal is inside the noise.
3. **The turn-up is unexplained.** α falls monotonically 0.896 → 0.812 across the top six thresholds, then rises 0.812 → 0.820 → 0.853. **A monotone partial-excitation reading does not predict a U-shape.** Either something re-enters at low threshold, or the tail α's are noise — and the tail is exactly where every curve is flattest, so interpolation is worst there. **Cannot currently distinguish these.**

## Why the tail is hard, and what was done about it
`crossing error ≈ recall_noise / |local slope|`. In the tail the slope is small, so error is large **regardless of sampling density** — density improves interpolation but leaves the noise term untouched.

Two routes were considered and one was **explicitly rejected**:
- **REJECTED — trim to the steep band (0.91…0.55), where the ordering is a clean 6/6 monotone.** Choosing the window *after seeing the result* is precisely the grid-fitting failure behind F1265–F1268. It would only be legitimate against a criterion fixed in advance.
- **TAKEN — measure better.** `R-RBS-LM-TAILFIX`: probes 50→80 (sd 0.071→0.056, attacks the numerator), ladder 8→13 points with extra density past 1.4×, extended 2.5×→4.3× of centre so low thresholds are **bracketed rather than extrapolated off the last point** (attacks the denominator).

**Honest bound on that fix:** the tail is intrinsically the flat part of a sigmoid. This makes the low thresholds *better* measured, not *well* measured. **If the turn-up survives, it is structure; if it flattens into the monotone run, it was tail noise.** Both outcomes are reportable and neither is being pre-judged.

## The pooled read, re-read under this frame
F1268's pooled experiment failed its validation guard (α 0.936 pooled vs 0.812 full, Δ 0.124 > 0.10 bar) and correctly stopped. **Under partial excitation that failure reads as a decomposition:** a fixed 255-distractor pool **pins the load**, removing exactly the load-variation the frame says drives excitation — and it returned a near-perfect power law (**resid 0.0001** vs full-read 0.0184, 180× cleaner). **Fixed-excitation vs varying-excitation, with the residual gap as the signature.** Offered as a reading the numbers volunteered, not as a result.

## The 4:3:7 / 7+7 arithmetic (recorded, not endorsed)
User: 11D = **1:3:7**, with **B/H/N as binders** rather than members; 4:3:7 is the same 14 folded so the binders join the anchor; k=7 is itself 4:3 collapsed chirally; hence 7+7, "maybe 4:3+7".
- **A/B/H/N = 4** — anchor plus meta-triad. That is the 4 in 4:3:7. ✅ arithmetic holds
- **(4:3):7 = 7:7 = 14** ✅
- **Im(𝕊) = 15 = 7+7+1**, so **A-N (14) + 1 = 15**, the +1 being the Cayley–Dickson doubler

**The last is recorded as a correspondence to check, NOT endorsed.** 14+1=15 is true of many groupings; what would make it real is whether the doubler's *role* (takes 𝕆→𝕊, destroys division) matches what the binders do to 1:3:7 — a structural check, not a counting one. **Note F1261 measured the sedenion register is 16 slots with exact zero-divisor annihilation** — non-division appearing precisely at the doubling. If binders ≙ doubler, then *"B/H/N don't know where to go"* and *"division fails at rung 16"* may be one fact from two sides. **Opened as its own probe; not started.**

## The 2D floor — derivable, and independently measured in our own carrier
The user's floor argument is **structural, not asserted**: an observation is a *relationship*; a relationship needs ≥2 relata; therefore minimum observable dimensionality is 2. 1D_t alone has nothing to relate to.

**Our carrier already exhibits it.** Klein-4 is **Z₂×Z₂ — irreducibly bi-axial**. F1261 measured `bind(a,a) = identity`, confirming no order-4 cycle: two independent Z₂ axes (γ₅, iω₇), not one Z₄. It cannot reduce to one axis — that is Z₂, a different and weaker object — and **F1211 measured exactly what one axis costs: the metric survives, the which-way is lost.** Same structural reason, independently measured, in a different part of the stack.

## Verdict / next
Directional prediction **supported over the well-measured range (6/8, p=0.042), ambiguous in the tail**, with an unexplained turn-up. **NEXT:** (1) `TAILFIX` in flight — decides whether the U-shape is structure or noise; (2) the **doubler↔binder role check** as its own probe (user-approved, not started); (3) if the turn-up survives, the question becomes *what re-enters at low threshold* — which is a new object, not a refinement of this one.

Composes **F1268** (whose curves these are, and whose 11/14 proposal is retired here), **F1267**, **F1266**, **F1265**, **F1263**, **F1261** (Klein-4 bi-axiality; the sedenion register), **F1211** (one-axis cost), **F1063** (the fractal tower), **#243/F1070** (the asymmetric-resonator arc), `[[feedback_dont_pre_commit_spike_query_operators]]` (the rejected post-hoc trim), `[[feedback_read_independent_structure_check_first]]`, #231/PKG-3.
