# R-RBS-LM Finding 540 — **14-tome circle (the_one's dim) vs 16-tome (the sedenion address space), and "odd matters" is exact chiral structure: on the SAME spectral ring, the tome COUNT is a granularity knob (16=sedenion surfaces far-reaching long chords — 38% of tomes' best match is a distant tome, mean dist 2.94; 14=the_one keeps meaning local — 0% far chords, 74% of true neighbours recoverable from own+adjacent vs 16's 50%), while PARITY is a SEPARATE, exact axis: the chiral half-turn (the mirror, Class C) is an INVOLUTION on EVEN rings (folds into NT/2 fixed antipodal mirror PAIRS — a static reflection axis) but is FRUSTRATED on ODD rings (applied twice it rotates by ±1, so NO tome has a mirror partner — the chirality is LIVE/moving, never landing; the moving-mirror of F516, the tie-free-majority of F527's odd-bundle). So 14 (even) = paired/static mirror + local recall; 16 (even) = paired/static mirror + far-reaching chords; 7/13/15 (odd) = chirally-live shelf. Neither count nor parity is privileged (F398) — they are two independent knobs the user's pokes surfaced.**

**Date:** 2026-06-07
**Arc:** RBS-LM — the circle-shelf partition count (14 vs 16) + odd/even chiral parity (the user's pokes)
**Provenance:** `R-RBS-LM-CIRCLE14_partition_count_14_vs_16_recoverability_and_far_chords.py` (committed; srmech 0.7.4; Class-L spectral circular embedding via **`srmech.calculus.atan2`** — the srmech-first, range-safe full-circle angle, replacing the earlier scripts' `np.arctan2` slip; Class-I cyclic mirror-involution test). No sub-agents.
**Composes:** **F535/F537** (the circle shelf as a semantic MoE — *now swept over partition count*) · **F398** (no count/parity privileged) · **F516** (the moving chiral mirror — *= the odd-ring frustrated half-turn*) · **F527** (hdc.bundle needs ODD for a tie-free majority — *same parity family*) · **F514/F528** (the two chiral hands) · **the_one dim 14 = 1+3+7+3 (A-N) · sedenion 16 = 2⁴ (CD top)** · **F394**. **← the user's 14-vs-16 + "odd matters" pokes; far-reach is the count knob, fixed-vs-live mirror is the parity knob.**
**→ on one spectral ring, tome COUNT trades local-recall (14, the_one) against far-reaching long chords (16, sedenion), and PARITY (odd/even) sets whether the chiral mirror is frustrated/live (odd) or a fixed antipodal pairing (even) — two independent axes; uses `srmech.calculus.atan2` not numpy.**

## Result (same manifold, only NT varies)
| NT | parity | meaning | nbr/far | recall (own+adj) | far-chord % | chiral half-turn ×2 |
|---:|---|---|---:|---:|---:|---|
| 7 | **ODD** | k=7 loop | 1.9× | 84% | 0% | FRUSTRATED (×2 = rotate-by-±1, no pairs) |
| 8 | even | octonion | 2.3× | 85% | 12% | INVOLUTION (4 fixed pairs) |
| 13 | **ODD** | — | 3.0× | 74% | 0% | FRUSTRATED (no pairs) |
| **14** | even | **the_one (1+3+7+3)** | 2.6× | **74%** | **0%** | INVOLUTION (7 fixed pairs) |
| 15 | **ODD** | — | 2.9× | 62% | 0% | FRUSTRATED (no pairs) |
| **16** | even | **sedenion (2⁴)** | 2.5× | **50%** | **38%** | INVOLUTION (8 fixed pairs) |
| 28 | even | so(8) dim | 2.8× | 41% | 32% | INVOLUTION (14 fixed pairs) |

## Verdict
**Two independent knobs, both surfaced by the user's pokes.**
- **COUNT (14 vs 16):** the **sedenion** partition (16) *makes* the far-reaching connections — 38% of tomes' best semantic match is a long chord across the ring (mean dist 2.94), the cross-circle links the user wanted. The **the_one** partition (14, wider arcs) keeps meaning **local** — 0% far chords, 74% of a word's true neighbours recoverable from its own + adjacent tomes (vs 16's 50%). Same manifold, two different jobs: 16 for far-reaching association, 14 for local recoverability. *(Honest: low-statistics — one corpus, ~14–16 tomes, 8 probe words; the 15→0% / 16→38% jump is a sharp curious signal, held open, not a law.)*
- **PARITY (odd vs even) — exact, not statistical:** the chiral half-turn `t → (t + round(NT/2)) mod NT` (Class C, the mirror) is an **involution on even rings** (`2·(NT/2) ≡ 0` → folds into NT/2 fixed antipodal **mirror pairs**, a static reflection axis) but is **frustrated on odd rings** (`2·round(NT/2) ≡ ±1` → no tome maps to a tome, the mirror **never lands**, the chirality stays **live/moving**). This is the **moving chiral mirror** of F516 and the same parity family as **F527's** odd-bundle tie-free majority. So **odd matters** lands: parity decides fixed-vs-live mirror **independently** of the recall/far-reach count knob.

Neither count nor parity is privileged (F398): 14 = the_one's dimension (1+3+7+3 A-N), 16 = the sedenion address space (2⁴, CD top), 7 = the k=7 loop. The numbers are the honest answer to "what changes," not a forced one. **Tooling note:** uses `srmech.calculus.atan2` (range-safe full-circle) — the earlier circle scripts' `np.arctan2` was a srmech-first slip; angles identical to machine precision, prior numbers stand (logged W14 + UPSTREAM). Held open (F394).
