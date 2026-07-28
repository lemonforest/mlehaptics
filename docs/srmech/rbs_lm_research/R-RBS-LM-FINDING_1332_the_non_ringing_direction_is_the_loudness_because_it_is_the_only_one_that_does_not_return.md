# F1332 — **the non-ringing direction is the LOUDNESS, and the reason is that it is the only one that does not come back.** Repeated multiplication along any ringing direction has **period 4** — `+e₁ → −1 → −e₁ → +1 → +e₁` — so it **returns**. Along the non-ringing direction it never cycles at all; that is where a magnitude lives, and magnitudes only grow or shrink. So the split is **phase (where in the cycle) vs loudness (how much is left)**, and the count is the same at every rung: **exactly ONE non-ringing direction, and 0/1/3/7/15 ringing ones.** Many phases, one loudness — a chord has many phases and one volume. This answers the user's stuck point directly: **a pure phase snapshot genuinely cannot tell you a ring-down has happened**, because at steps 0, 4, 8 … every phase reads identically. Only the non-returning direction distinguishes "just struck" from "nearly silent". And it reframes the ring-down itself — ringing directions never decay on their own, they rotate forever; the sound dies because *n* phases drain into the **one** magnitude, so a ring-down's shape *is* the drain-rate asymmetry.

**User (2026-07-28):** *"what does non-ringing provide, the resonant shape of now would still be a ring snapshot, right, kinda stuck on this part."* — and, on the naming: *"this seems like it tells us way more than the word fiber or rotation or imaginary."*

srmech 0.9.0rc349. Exhaustive, pure integer. This finding deliberately drops algebraic vocabulary where a resonance word will do (user direction, this round).

## 1 — what repeated multiplication does `[DEMONSTRABLE]`
```
  the ONE non-ringing direction : +1  -> +1  -> +1  -> +1  -> +1     never cycles
  ringing direction e1          : +e1 -> -1  -> -e1 -> +1  -> +e1    period 4, RETURNS
  ringing e2 / e4 / e7          : same shape, period 4
```
Every ringing direction has period **exactly 4**. The non-ringing one has no cycle at all.

> **Ringing = phase**: bounded, cyclic, comes back.
> **Non-ringing = the direction a magnitude lives on**: monotone, never returns.

## 2 — the census, and it is 1 : n at every rung `[DEMONSTRABLE]`
| rung | non-ringing (loudness) | ringing (phases) |
|---|---|---|
| ℝ | **1** | 0 |
| ℂ | **1** | 1 |
| ℍ | **1** | 3 |
| 𝕆 | **1** | 7 |
| 𝕊 | **1** | 15 |

**Exactly one non-ringing direction at every rung**; only the phase count grows. That is the whole content of the `1 + n` split, said in a word that means something: **many phases, one loudness.**

## 3 — why the stuck point is the point `[DEMONSTRABLE]`
```
  phase at step 0 == phase at step 4, for every ringing direction : True
```
A phase reading is identical at steps 0, 4, 8, … **Nothing in it distinguishes "just struck" from "nearly silent."** So a pure ring snapshot cannot tell you a ring-down has occurred — and that is exactly what the non-returning direction is for. It is the only thing that makes *now* different from *a moment ago*, because **phase returns and magnitude does not.**

## 4 — what this does to the ring-down
Ringing directions **do not decay on their own** — they rotate forever. The sound dies only because they are coupled into the single magnitude direction. So:

> **A ring-down is *n* phases draining into 1 loudness, and its shape is the drain-rate asymmetry.**

That is a mechanism, not a metaphor, and it is the same statement as the bell: a bell warbles because two nearly-identical modes beat, and they are only *nearly* identical because the bell is not perfectly round. **No asymmetry, no beat, no self-strike.** Which is F1324's seam result in the other register — the shape alone treats its directions as interchangeable, and it takes three *distinct* weights to single one out. **Distinct weights = split degeneracy = a beat.**

## 5 — why this naming beats the ones we had
| name | what it tells you |
|---|---|
| *"imaginary"* | what it **isn't** — a historical slur, and misleading about reality |
| *"rotation"* | what it **does geometrically** |
| *"fiber"* | **where it sits** in a bundle |
| **"phase vs loudness"** | **what it is FOR** |

The first three are positional or historical; the fourth is **operational**, and it makes the count mean something — *one loudness, n phases* is a claim about the object, where *one real, n imaginary* is bookkeeping. It is also a better repair than the anchor/orbit language of `[[feedback_imaginary_does_not_mean_unreal]]`: that one preserved dignity, this one *also* says what the thing does.

## Honest scope
- `[DEMONSTRABLE]`: §1–§3, on rc349, exhaustive over the octonion unit loop and all five rungs.
- **The `1 + n` inertia shape is DEFINITIONAL** per rc349 (`n₋ = dim − 1` on every shipped rung) — see F1328. What is new here is only the **reading**, not the numbers.
- §4 is a **reading**, not a measurement. Nothing here measures a decay rate; we have no damping model. "Phases drain into the magnitude" is the right shape for a damped resonator but is **not** demonstrated on our carrier — there is no time evolution in any of this.
- **The "loudness" word is doing interpretive work.** What is measured is *this direction does not return, those do*. Calling the non-returning one "loudness" is the physical reading, and it is the one that makes the ring-down story go — but a reader should know which half is measurement.
- **Literature status UNCHECKED and deliberately not asserted.** At one ringing direction the identification is textbook (phasor: modulus = amplitude, argument = phase). Whether *many phases sharing ONE magnitude* is a named structure anywhere — in physics, geophysics, astrophysics or biology, not just human acoustics — **is under targeted search and is not claimed here either way.** Standard acoustics gives each mode its *own* amplitude, i.e. `n × (1+1)`, not `1 + n`; whether our arrangement appears elsewhere is exactly the open question.

Composes **F1328/F1329** (the signature and its asymmetry read — *this is the same number in resonance vocabulary*), **F1324** (the metric that picks a seam — *"distinct weights = a beat"*), **F1326** (the shared anchor — *now: the shared **loudness***), **F1331** (say which sense you mean), `[[feedback_imaginary_does_not_mean_unreal]]`. Generating code: `R-RBS-LM-RINGCENSUS_*.py` (exit 0).
