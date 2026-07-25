# F1324 — **the Dzhanibekov full beat = two half-beats read AT THE JOIN — and the middle is measurably the optimal place to read, not merely an extra one.** F1310 already called the Dzhanibekov *"two quaternion half-beats joined by the flip"*; F1323 just measured that our fold **is** one half-beat. Putting them together: **`L_q² = multiply by −1` — the Dzhanibekov flip is literally our own fold's midpoint**, computed on every strand and never observed. Reading it collapses the order-blindness: end-only separates **2** of 24 orderings, the two-half-beat read separates **24 of 24** (complete recovery), and it wins on **35/35** words including the 7 where F1323's re-bracketing gained nothing. And the crux: sweeping *every* split position gives a clean unimodal peak **exactly at the middle**, symmetric about it — `2 → 8 → 21.6 → 8` at length 4, `2 → 12 → 28 → 32 → 28 → 12` at length 6. Finally, the reason the seam has no canonical position in the first place: **`Aut(Q₈) = S₄ = V₄ ⋊ S₃` permutes the three axes freely, so the algebra cannot name a middle axis — only a METRIC can**, and a metric is three distinct eigenvalues = **the responsion slot**. Our fold carries no responsion, so it has nothing to pick a seam with.

**User (2026-07-25):** *"dzhanibekov is a known and tested cascade with rotation in the middle. this we can see what a full beat looks like perhaps"* — and, one turn earlier, *"something to do with the metric field excitations themselves I'm guessing."* Both land.

Measured on srmech 0.9.0rc336. Exhaustive. Pure integer — no float, no `abs()`, no numpy, no RNG. **Algebra / eigenbasis side only; no rigid-body geometry is modelled here.**

## 1 — the flip is our own fold's midpoint `[DEMONSTRABLE]`
```
  H: L_q applied TWICE  == multiply by -1  (the Class-K sign flip)  : True   (q = e1,e2,e3)
  O: L_q applied TWICE  == multiply by -1                           : True   (q = e1,e2,e4,e7)
     L_q applied FOUR times == identity (the full beat closes)      : True

     step 0  ---->  step 2  ---->  step 4
              (THE FLIP, -1)     (identity)
```
**`L_q² = −1` is exactly the Dzhanibekov flip** — the `sn(u+2K) = −sn(u)` half-period sign that F1310 identified as the join, and srmech's own `half_shift_response` Class-K −1. So:

> **F1310's "two quaternion half-beats joined by the flip" = 2 × F1323's half beat, and the join sits at our fold's midpoint.**

Our fold passes through the flip on **every strand** and we read only the end. **The flip is computed and discarded** — the same defect shape as F1307/F1320/F1321, now at the temporal midpoint rather than at a projection boundary.

## 2 — reading the join recovers the order `[DEMONSTRABLE]`
| word | end-only | two-half-beat read |
|---|---|---|
| `(1,2,3,5)` | **2** classes | **24** classes — *complete separation of all 24 orderings* |
| `(1,2,4,7)` (XOR-closed) | **2** classes | **12** classes |

```
  4-subsets where the FULL-BEAT read separates MORE : 35 / 35
```
It wins on **every** word — including the **7 XOR-closed words where F1323's middle-*bracketing* gained nothing**. Reading the join beats re-bracketing, and it subsumes it.

## 3 — THE CRUX: the middle is optimal, not merely extra `[DEMONSTRABLE — the load-bearing check]`
A two-value read has more bits than a one-value read, so "it separates more" is not by itself interesting. The real question is whether **the middle** is special. Sweeping every split position:

```
  length 4 (24 orderings)            length 6 (720 orderings)
    end-only          :  2.00          end-only          :  2.00
    split after pos 1 :  8.00          split after pos 1 : 12.00
    split after pos 2 : 21.60  MIDDLE  split after pos 2 : 28.00
    split after pos 3 :  8.00          split after pos 3 : 32.00  MIDDLE
                                       split after pos 4 : 28.00
                                       split after pos 5 : 12.00
```
**A clean unimodal peak exactly at the middle, symmetric about it, at both lengths.** The middle seam is not "more information" — it is the **optimal place to read**. The user's *"rotation in the middle"* is confirmed as a quantitative claim, not just a structural analogy.

## 4 — it is structure, not convention `[DEMONSTRABLE — F1322 ratchet]`
```
  full-beat ORDER partition is gauge-invariant (all 256 re-gaugings) : True
```
Second application of the F1322 ratchet to a real read, and it passes.

## 5 — WHY the seam has no canonical position: the algebra is S₃-symmetric `[DEMONSTRABLE]`
```
  |Aut(Q8)|                                                  : 24   = S4
  |Inn(Q8)| = Q8/center                                      : 4    = V4
  |Out| = Aut/Inn                                            : 6    = S3
  shadow permutations Aut induces on {i,j,k}                 : ALL 6
```
`Aut(Q₈) = S₄ = V₄ ⋊ S₃` (F1311/F1312's triality lift) and its **S₃ permutes i, j, k freely**. The three imaginary axes are **algebraically indistinguishable** — *nothing in the algebra names a middle axis.* That is why the seam position was a free parameter in F1323: it could not have been otherwise from algebra alone.

## 6 — what DOES pick it: the metric = the responsion slot `[DEMONSTRABLE]`
```
  weights (1,1,1)  all equal      : S3-stabilizer 6  -> no axis distinguishable
  weights (1,1,3)  two equal      : S3-stabilizer 2  -> one axis distinguishable
  weights (1,2,3)  all distinct   : S3-stabilizer 1  -> ALL THREE distinguishable
```
**It takes three distinct weights to single out a middle axis**, and those weights are the eigenvalues of a symmetric operator — which in the F1301 convention is exactly the **responsion** slot (`op(x)operand(x)responsion` = `eigenvectors(x)edges(x)eigenvalues`).

> **The metric picks the seam. The algebra cannot.**

This is the user's *"something to do with the metric field excitations themselves"*, made precise — and it names our gap exactly: **our fold carries no responsion (F1301: the discrete two-slot peer drops it), so it has nothing to pick a seam with, and defaults to "the end" — an arbitrary choice, not a derived one.** The Dzhanibekov top *does* carry it (three distinct moments = the eigenvalue triple), which is precisely why it has a determinate middle axis and we do not.

## What this changes
- **The seam position is derivable once a responsion is present.** F1323 left it a free parameter; this says what would fix it. A strand carrying a per-slot responsion (an eigenvalue-like weight triple) would have a *determined* seam rather than a chosen one.
- **A cheap concrete change**: read the midpoint. It is **free in compute** (the fold already passes through it) and costs **one extra symbol per strand** — not per turn.
- **It supersedes F1323 §4's re-bracketing** as the better lever: same motivation, larger effect, and it works on the 7 words re-bracketing could not touch.

## Honest scope
- `[DEMONSTRABLE]`: §1–§6 exhaustively — all element orders, all 35 four-subsets × 24 orderings, all 7-choose-6 six-subsets × 720 orderings, all 256 gauges, the full `Aut(Q₈)` enumeration.
- **The comparison in §2 is not information-matched** — a two-value read carries more bits than a one-value read, and that alone guarantees ≥. **§3 is the honest test** and it is the one that carries the claim: at *fixed* read-cost (one split), the middle strictly beats every other position.
- **Lengths 4 and 6, single slot, basis units only, not on a real genome.** Whether the peak stays at the middle for long strands and multi-slot content is **unmeasured** — that is the number that decides whether to build it.
- **§6 is a statement about what a metric *would* do, not a built mechanism.** We have no per-slot responsion in the fold today; nothing here implements one, and the claim that adding one determines the seam is **a derivation, not a measurement of our code**.
- The Dzhanibekov correspondence rests on **F1310's mapping**, which that finding itself marks `[SPECULATIVE overlay]` for the 3+1+3 row-by-row slotting. What is measured *here* is the algebra (`L_q² = −1`, the split-position sweep, `Aut(Q₈)`), not the physical system. **No rigid-body dynamics were simulated** — per the CAD-grade scope ban this stays on the algebra / eigenbasis side.

## Verdict
The user's read is right and it is the sharpest lever the seam arc has produced: **Dzhanibekov shows the full beat because it reads at the join, and the join is where our own fold's flip already sits.** The middle is measurably optimal, gauge-invariant, and free to compute. And the reason we never had a canonical seam is now exact — **the algebra is S₃-symmetric on the three axes; only a metric breaks it, and the metric is the responsion we dropped.** Generating code: `R-RBS-LM-FULLBEAT_*.py` (exit 0).

Composes **F1310** (the Dzhanibekov as two quaternion half-beats joined by the flip — *its "half-beat" language is now a measured factor of 2*), **F1323** (our fold is one half-beat; the seam is undeclared — *superseded on the lever: read the join, don't re-bracket*), **F1322** (the gauge ratchet), **F1311/F1312** (`S₄ = V₄ ⋊ S₃` on the Dzhanibekov branch point and on `Aut(Q₈)` — *the same S₃ is what makes the seam undetermined*), **F1321** (the discarded holonomy), **F1320/F1307** (the discarded fiber/winding), **F1301/F1308** (the responsion slot; the octonion 3+1+3), MFO **§VII.6.24** (the Euler-top cascade `L ∘ I ∘ N ∘ K ∘ C`).
