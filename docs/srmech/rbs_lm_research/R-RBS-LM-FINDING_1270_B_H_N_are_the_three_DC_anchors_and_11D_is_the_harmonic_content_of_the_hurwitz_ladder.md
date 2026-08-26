# F1270 — the doubler↔binder role check, resolved: **B/H/N are the three DC (real) components, one per algebra block** — and the user's "11D as the harmonics that survive" is confirmed *behaviourally*, not by analogy. `One.dim = 14 = ℂ(2) ⊕ ℍ(4) ⊕ 𝕆(8)` splits as **3 reals + 11 imaginaries**; under the θ-crank the 11 imaginaries vary as **cos θ** and **flip sign under σ**, while the 3 reals are **invariant under both**. **11D = Im(ℂ) ⊕ Im(ℍ) ⊕ Im(𝕆) = 1+3+7 — the harmonic content of the Hurwitz ladder.** Includes a **correction of my own first verdict**, which was wrong because I misread a field name.

**User (2026-07-20/21):** *"those 11D come from our 1:3:7 where our B/H/N friends aren't sure where to go … those last 3 are like what bind 1:3:7 … might help if we think of our 11D as the harmonics that survive asymmetric inharmonic and subharmonic excitations."*

## srmech already encodes the split
`cascade.the_one` carries it in separate fields — this was not constructed for the test:
```
dim            14
partition      (1, 3, 7, 3)
imag_dims      (1, 3, 7)          <- the 11
grammar_slots  ('B', 'H', 'N')    <- separate field
```
And the blocks are the Hurwitz ladder as a **DIRECT SUM**, not a nested tower:

| block | real | imag | A-N imaginary slots |
|---|---|---|---|
| ℂ | 1 | 1 | A |
| ℍ | 1 | 3 | I, C, J |
| 𝕆 | 1 | 7 | D, E, F, G, K, L, M |
| **total** | **3** | **11** | **11 slots** |

`dim(ℂ)+dim(ℍ)+dim(𝕆) = 2+4+8 = 14 = One.dim`. **11D = Im(ℂ)⊕Im(ℍ)⊕Im(𝕆) = 1+3+7.**

## MY FIRST VERDICT WAS WRONG — recorded because the error is instructive
I initially concluded *"B/H/N are operations, not parts"*, reasoning that they carry no numeric component while the reals do. **That was a misreading of a field name.** The field is `an_imag_slots` — A-N ***imaginary*** slots. Reals are absent from it *by definition*, so their absence proves nothing.

The dimension arithmetic then forces the answer: **11 imaginaries occupy the 11 imaginary slots, so the only dimensions left for B/H/N are the 3 reals.** Counting alone could never have separated the two readings (3 doublings vs 3 reals both give 3) — but the slot accounting does, and it goes to the reals.

## The behavioural test — "harmonics that survive" is literal
| | value | under θ (the crank) | under σ (chirality) |
|---|---|---|---|
| **3 reals** | 1 | **invariant** | **invariant** |
| **11 imaginaries** | varies | **cos θ** (measured 1.0000, 0.9922, 0.9689, 0.8776, 0.5403 = cos 1) | **sign flip** |

So the 11 *are* the oscillating content and the 3 are DC. Turning the crank moves the harmonics and leaves the anchors fixed; flipping chirality inverts the harmonics and leaves the anchors fixed.

**This gives "B/H/N don't know where to go" a mechanical reading: they do not oscillate.** They never appear in a harmonic or spectral read because they have no harmonic content — which is precisely why they have been hard to place in a vocabulary assembled by reading spectra. They are the silent anchors.

## The doubler question — both readings partly right
There are exactly **3 doublings** (ℝ→ℂ→ℍ→𝕆), in **1:1 correspondence** with the 3 reals: one doubling → one new block → one new DC anchor. But doublings are **operations**, not dimensions, so the A-N *classes* land on the reals. The correspondence is real; the identification is to the reals.

**This also explains why there are 3 binders and not 4.** A 4th doubling (𝕆→𝕊) would add a 4th DC anchor and 15 further harmonics — and it is the doubling where **division dies**. So the vocabulary stopping at 14 is not an omission: **it stops where the Hurwitz ladder stops.** F1261 measured that boundary directly — the sedenion register is 16 slots with *exact* zero-divisor annihilation — so "B/H/N are only 3" and "division fails at rung 16" are the same fact from two sides.

## Verdict / next
Resolved: **B/H/N = the 3 DC anchors; 11D = the harmonic content of ℂ⊕ℍ⊕𝕆.** Confirmed behaviourally against the shipped `One`, with my own misread corrected in the record. **NEXT:** (a) whether the 4:3:7 fold (binders joining the anchor) is a *re-grouping* of these same 14 or a distinct object — testable by asking whether the 4 share a DC/harmonic character; (b) the 𝕊 boundary as its own probe, since it is where the vocabulary's edge and division's failure coincide.

Composes **F1269** (which opened this probe), **F1261** (the sedenion register at 16 slots; Klein-4 bi-axiality), **F1211** (what one axis costs), **F121/F123/F124** (4:3:7 and the 4:3-inside-7), **DUALITY.md / TRIALITY.md**, **#243/F1070**, #231/PKG-3.

**→ extended by F1273** — F1273 runs the 𝕊-boundary probe this finding queued, and reaches a result that constrains it: our addressing keeps working at 𝕊 (120/120 exact round-trip), so **no operation of ours needs the division property the ladder loses there**. F1270's 14 / 11D / 3-reals reading therefore rests on **Hurwitz as an external theorem**, not on our own machinery — a legitimate stance, but one that must be stated rather than implied by the numbers landing on 14.
