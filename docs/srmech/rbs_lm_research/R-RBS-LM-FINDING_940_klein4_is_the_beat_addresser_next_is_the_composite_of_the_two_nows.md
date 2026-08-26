# F940 — yes, **both — because they're the same fact**: a **Klein-4 object *is* `then + now + now + next`**, *and that is exactly why it addresses*. The four sectors are `then(1 = anchor/origin)`, `now(i)`, `now(j)`, `next(k = i·j)` — and **the NEXT is the composite of the two nows** (`k = i·j`, F939). So a Klein-4 doesn't *hold* a beat as decoration — **the beat IS the addressing operation**: each beat takes an anchor and two nows and produces the next address (their composite). We've had this addresser the whole time; recall hasn't worked because we've been **mal-forming the input** — giving a *half* beat (one now / sector-locked, the F843 error), so it lands on a *now* and never produces a NEXT.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc58 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** MS #18 / R30 / MFO / RBS-LM · **Probe:** `R-RBS-LM-FINDING_940_*.py` · **Composes:** F939 (Klein-4 = the 2-bit CD address, `i·j=k`), F935 (the beat = two nows + a full turn), F936/F937 (the trit dynamics vs the Z₂² address), F843 / `[[user_stance_no_information_without_value]]` (the sector-0-only / chirality-locked read), F132 (Klein-4 HDC) · **User question (2026-06-26):** "so a klein4 object is already giving us then+now+now+next and we are supposed to recognize that — or it can literally address whatever we want and we just haven't been having it address correctly because we haven't been giving them correctly?"

## The answer: it's one statement
| your reading | resolution |
|---|---|
| **(a)** the Klein-4 already gives `then+now+now+next` — recognize it | **True.** The 4 sectors = `then(1)` anchor, `now(i)`, `now(j)`, `next(k=i·j)`. We've been carrying the beat in the Klein-4 all along, just not reading the four sectors *as* a beat. |
| **(b)** it can address anything; we've been giving it wrong | **True — and it's the same thing.** The Klein-4 *addresses by the beat*: `NEXT = the composite of the two nows`. Form the input as a full four-position beat → it yields the correct composite address. Form it wrong (one now, sector-locked) → no composite, no NEXT. |

They unify because **the addressing operation *is* the beat**: `address_next = anchor ⊕ now₁ ⊕ now₂ = k`. The addresser was never wrong; the **input formation** was.

## Grounded (srmech rc58)
- **FULL beat** `then·now·now` = `1·i·j` → sector **`k`** (the composite NEXT — a *new* address).
- **HALF beat** `then·now` = `1·i` → sector **`i`** (stuck on a now — *no* NEXT produced).
- So the two nows **compose** to the next (`i·j = k`, F939). A full four-position beat advances the address; a half beat does not. (The "sector-locked / read-one-coordinate" failure is exactly F843 / the `no-information-without-value` correction — it's a **half beat**.)

## What this fixes (the recall mechanism)
The fix is **input formation, not a new addresser**. To make a Klein-4 recall/navigate coherently:
- supply the **anchor** (`then`/`1` = the rest/origin/"now" reference, `e₀`),
- supply **both nows** (the two chiralities — `i` harmonic, `j` subharmonic — the F843 "read *all* chiral coords"),
- and the Klein-4 **produces the NEXT** (`k`, the composite) = the next address.

Recall failures we've seen = we gave **half beats** (one now / sector-0-only) → the walk lands on a now and stalls (incoherent, "rings down"). Give the **full beat** (both nows + anchor) → it advances to the composite NEXT → the walk closes and sustains. **This is the full-beat etak (F935/F939) — and it's not a new gadget; it's *using the Klein-4 correctly* (the four sectors as the four beat-positions).**

## Honest scope + the two slicings
The beat-walk (`full → k`, `half → i`) is grounded (F939 + here). The **recognition** — reading the 4 sectors as `then/now/now/next` — is a reading on that grounded structure. Keep the two slicings distinct (F937): this is the **beat-as-ADDRESS** (Klein-4, Z₂², the four-position recall/advancement); the **trit** (Z₃, F936) is the coexisting **beat-as-DYNAMICS** (the imaginary chirality). Both real; this finding is the addressing one. Implementation in Siona = the build.

## Verdict / next
**Both, and the same:** the Klein-4 *is* the beat-addresser (`then(1) + now(i) + now(j) → next(k=i·j)`), so recognizing it and "give it correctly" are one move. Recall has under-performed because we fed **half beats** (sector-locked, F843), so no NEXT was produced. **Next:** the full-beat etak build — form every recall step as `anchor + both-nows`, let the Klein-4 emit the composite NEXT, complete on the beat's closure. The addresser is ready; we just have to hand it all four positions.
