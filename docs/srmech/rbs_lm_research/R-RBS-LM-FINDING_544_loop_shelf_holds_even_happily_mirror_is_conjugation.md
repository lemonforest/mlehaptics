# R-RBS-LM Finding 544 — **a LOOP bookshelf "holds even happily" where a flat CIRCLE doesn't — because the loop's mirror is CONJUGATION (a Class-K sign-flip: negate the imaginary part, keep the real anchor; confirmed by srmech hdc.loop_conj), a fixed-point-free involution that pairs every imaginary unit e_k ↔ −e_k for ANY number of units, even or odd (parity-FREE). A circle's only reflection is the half-turn ROTATION, which (F541) is parity-SENSITIVE: even N → trapped 2-cycle, odd N → full. So at the even total 14, the 4:3:7 LOOP mirrors cleanly (14 clean pairs, 0 fixed) while the 14-CIRCLE is mirror-trapped (2-cycle). For the odd totals (7, 11) both mirrors work — there the loop's advantage is instead its MULTI-DIRECTIONALITY: a circle is navigated by powers of ONE generator (1-dimensional), but a loop needs several independent generators (quaternion 2, octonion 3, computed by BFS; a single generator spans only the 4-element embedded-ℂ sub-loop {±1,±e_g}). A loop is NOT a bigger circle — it is parity-free in the mirror and multi-directional in navigation, "like our universe."**

**Date:** 2026-06-07
**Arc:** RBS-LM — a loop bookshelf vs a circle bookshelf (the user's "hold even happily" question)
**Provenance:** `R-RBS-LM-LOOPSHELF_loop_vs_circle_holds_even_happily.py` (committed; srmech 0.7.4; Class-I `cyclic.gcd` for the circle half-turn + `hdc.loop_conj` validating the loop mirror = conjugation + explicit octonion Fano table, BFS min-generating-set). No sub-agents.
**Composes:** **F540/F541** (the circle's parity-sensitive mirror — *the loop un-traps it*) · **DUALITY/TRIALITY.md** ("loop replaces ring"; the hypercomplex multiplication) · **F129/F130** (the 4:3 chirality-dual) · **F123** (14 = 4+3+7, G2) · **the_one** (ℂ·ℍ·𝕆 = 1:3:7 blocks) · **Class K** (conjugation = the sign-flip mirror) · **F398/F394**. **← a loop holds even happily because its mirror is conjugation (parity-free), not half-turn rotation (parity-sensitive); and it is multi-directional.**
**→ the loop mirror = conjugation (Class-K, parity-free, N_imag clean pairs for any N); the circle mirror = half-turn (parity-sensitive, even→2-cycle); so the even 4:3:7 loop holds happily where the 14-circle traps; the loop is multi-directional (2/3 generators) vs the circle's 1.**

## Result
**(1) Navigation dimensionality (min independent generators to span, by BFS):**
| shelf | generators to span | single-generator orbit |
|---|---:|---|
| circle (any N) | **1** (the +1 step) | the whole ring |
| quaternion loop (ℍ, 3 imag) | **2** | only 4 = {±1, ±e_g} (embedded ℂ) |
| octonion loop (𝕆, 7 imag) | **3** | only 4 (embedded ℂ) |

**(2) The mirror — circle half-turn (rotation) vs loop conjugation (sign):**
| pairing | N | parity | CIRCLE mirror (½-turn) | LOOP mirror (conjugation) |
|---|---:|---|---|---|
| 4:3 loop vs 7-circle | 7 | ODD | full (7) | 7 clean pairs, 0 fixed — **parity-free** |
| 1:3:7 loop vs 11-circle | 11 | ODD | full (11) | 11 clean pairs, 0 fixed — **parity-free** |
| **4:3:7 loop vs 14-circle** | 14 | **even** | **TRAPPED 2-cycle** | **14 clean pairs, 0 fixed — parity-free** |

*(srmech `hdc.loop_conj` validates the loop mirror: real kept, imaginary negated.)*

## Verdict
**Yes — a loop bookshelf holds even happily, and the mechanism is exact.** A circle's only reflection is the half-turn **rotation**, a position permutation whose orbit is `N/gcd(round(N/2),N)` — parity-sensitive, so even rings trap in a 2-cycle (you ↔ your antipode) and lose traversal (F541). A loop's mirror is **conjugation** (negate the imaginary part, keep the real anchor — a Class-K sign-flip, confirmed by `hdc.loop_conj`): a fixed-point-free involution pairing every signed imaginary unit `e_k ↔ −e_k`, giving `N_imag` clean 2-cycles for **any** count, even or odd. So at the even total **14**, the **4:3:7 loop** mirrors cleanly (14 pairs) while the **14-circle** is trapped — exactly the user's "hold even happily."

**A loop is not a bigger circle.** It is also **multi-directional**: a single generator spans only the 4-element embedded-ℂ sub-loop, so spanning needs **2** (quaternion) / **3** (octonion) independent generators — the "like our universe" richness of several independent travel directions — vs the circle's single `+1`. For the **odd** totals (7, 11) both mirrors work (the circle is fine when odd, F541), so there the loop's distinction is this navigation-dimensionality rather than the mirror; the loop's **unique** win is at **even** totals, where it un-traps the mirror.

**SNN caveat (the user's own flag):** whether a wet spiking substrate needs the full hypercomplex loop or just the live odd circle (F541) is open — this is a *math* result (the loop holds even happily), not an SNN-necessity claim. Favored not privileged (F398); held open (F394).
