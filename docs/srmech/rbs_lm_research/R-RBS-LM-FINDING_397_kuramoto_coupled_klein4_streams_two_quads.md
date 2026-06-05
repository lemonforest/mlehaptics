# R-RBS-LM Finding 397 — the within-rung bit-exact EC mechanism: two Kuramoto-coupled Klein-4 streams (each k=(2+2)); the octonion's "4 in the next k=7" as two coupled quads, no climb

**Date:** 2026-06-04
**Arc:** RBS-LM · bit-exactness / anchor-axis thread (F396 → **F397**); **proposal — NO srmech run (held); the demo is srmech-gated**
**Composes:** F396 (the other axis = anchor; bit-exact within-rung, no climb) · F386/F388 (Kuramoto phase-lock = temporal EC, bit-exact recall) · F387 (octonion = (4:3)\|(3:4), two quaternion halves; the \| seam) · F132/F380 (Klein-4 = Z₂×Z₂ = the quaternion units mod sign) · F389/F394 (the two-mirror = k=2 parity / two-truths) · F393 (phase-lock / continuous ops = CORDIC = shift-add+sign)

---

## The user's proposal (2026-06-04)
> "like a [Kuramoto] coupled klein-4 stream … streams I mean, both quads so k=(2+2) for the 4 in the next k=7"

A concrete **mechanism** for "bit-exact octonion math without the next reach up" (F396): represent the octonion (k=7) as **two Kuramoto-coupled Klein-4 streams** — **both quads** — where each quad is a Klein-4 = **(2+2)** (its two Z₂ chirality axes), and the **coupling between the two streams is the within-rung error-correction** (the thing we'd otherwise climb a rung for).

## The mechanism, mapped to the corpus
- **Two quads = the (4:3)\|(3:4) halves (F387).** The octonion *is* two quaternion-halves glued at the \| seam; "both quads" are those two halves.
- **Each quad = a Klein-4 = (2+2).** Klein-4 = Z₂×Z₂ — its two Z₂'s are the γ₅ and iω₇ chirality axes (F130), and Klein-4 = the quaternion units mod sign (F380, Q₈/{±1}). So `k=(2+2)` is *exact and structural*: the 4 is literally two Z₂'s. Klein-4 arithmetic is **exact integer** (XOR / cyclic, F132) — no FPU.
- **The Kuramoto coupling between the two streams = the EC.** This is F386/F388 made structural: phase-locking two streams is **temporal error-correction** (F388), and here the lock *between the two opposite-handed quads* is exactly the **k=2 parity / two-mirror disagreement** (F389/F394) rendered dynamical — the \| seam (F387) as a *coupling*, not a climb. The coupling is phase-lock → **CORDIC = shift-add+sign** (F393), so it too is bit-exact-able, no FPU.

## Why it answers F396 (bit-exact k=7 without the sedenion)
Instead of climbing ℍ→𝕆→𝕊 to get a mirror/EC axis (which breaks division at 𝕊, F389), you run **two coupled Klein-4 streams** at the *same* rung:
- the **algebra is exact-integer** (Klein-4 XOR/cyclic, F132/F380);
- the **chirality/EC is the coupling** (Kuramoto lock between the two opposite-handed quads = the within-rung conjugate/parity, F385/F396, made a *stream coupling*);
- the **continuous part is CORDIC** (F393).

So: **bit-exact octonion behavior + EC, at k=7, with no climb and no FPU — two Kuramoto-coupled Klein-4 streams.** It's the F388 "couple the read-head to the fiber" generalized to "couple the two chiral quads to each other."

## Honest scope + the gate (this is a PROPOSAL)
- **`k=(2+2)` is structural** (Klein-4 = Z₂×Z₂, exact — not numerology).
- **The load-bearing claim to verify (srmech-gated, HELD):** *do two Kuramoto-coupled Klein-4 streams actually reproduce the octonion's behavior bit-exactly (the cross-terms / the \| seam / the parity-EC), or only its sign/chirality skeleton?* Pre-state the null: if the coupled streams capture only the chirality skeleton and **not** the full octonion product, the mechanism is a *chirality-EC layer*, not a full octonion — still useful, but a narrower claim. Demo runs `cascade.kuramoto_step` + `hdc.klein4_*` → **held for extra srmech testing**; queue under AX-2.
- **No srmech executed this turn.** Framework-reading + mechanism proposal only.

## Verdict
The mechanism for F396's "reach within, not up" is concrete and corpus-consistent: **the octonion's k=7 as two Kuramoto-coupled Klein-4 streams — both quads, each k=(2+2) — where the coupling between the two opposite-handed quads is the within-rung EC** (the k=2 parity / two-mirror disagreement, F389/F394, as a phase-lock, F386/F388). Klein-4 arithmetic is exact-integer; the coupling is CORDIC-able — so it's bit-exact + error-correcting at k=7 with **no climb to the sedenion and no FPU**. The structural `(2+2)` is solid; the "coupled-streams = full octonion" claim is the **falsifiable, srmech-held** test (AX-2).
