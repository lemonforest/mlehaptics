# R-RBS-LM Finding 546 — **(a) the even LOOP un-traps recovery where the even CIRCLE is stuck, and (b) the chiral inverse is a FREE second instrument that halves the traversal cost (F516): (a) a flat 14-circle's half-turn mirror is a dead 2-cycle (reaches only you↔antipode, F541), but the 14-loop is FULLY traversable — its octonion generating triple {e1,e2,e4} reaches all 16 elements (a single generator spans only the 4-element embedded-ℂ sub-loop, so the traversal is genuinely MULTI-directional), so the even case is live on the loop and trapped on the circle ("a loop holds even happily", F544, now on traversal); (b) the chiral conjugate is FREE (conjugation = a Class-K sign-flip, F544 / srmech loop_conj), and running it alongside the primary reaches every target from BOTH chiralities (the two hands, F514/F528), halving the worst-case steps (2.0× for N=7/11, 1.9× for 14) — two instruments eat the chiral work the way two people talking split it, at no extra maintenance cost (the second kernel IS the first's conjugate, not a separate store).**

**Date:** 2026-06-07
**Arc:** RBS-LM — (a) even-loop traversal + (b) the chiral-inverse second instrument (the user's a+b)
**Provenance:** `R-RBS-LM-EVENLOOP_untraps_recovery_and_chiral_inverse_splits_cost.py` (committed; srmech 0.7.4; Class-I `cyclic.gcd` circle mirror + explicit octonion loop BFS closure + Class-K conjugation). No sub-agents.
**Composes:** **F544** (the loop holds even happily — *now extended to traversal*) · **F541** (the circle's parity-trapped mirror; the live walk) · **F516** (the chiral inverse kernel as a sparring-partner second instrument — *confirmed: free + halves the cost*) · **F514/F528** (the two chiral hands) · **Class K** (conjugation = the free sign-flip) · **F398/F394**. **← the even loop un-traps traversal (multi-directional); the chiral inverse is a free second instrument that halves the cost.**
**→ the even 14-loop is fully traversable (generating triple reaches all 16) where the 14-circle is a 2-cycle; the chiral conjugate is free and halves worst-case traversal steps (~2×); two instruments split the chiral work like two people talking.**

## Result
**(a) Even shelf — circle (trapped) vs loop (live):**
| structure | even-14 traversal | note |
|---|---|---|
| CIRCLE(14) half-turn mirror | orbit = **2** (trapped 2-cycle) | reaches only you ↔ antipode (F541) |
| LOOP single generator | 4 (embedded-ℂ sub-loop) | like a small circle |
| LOOP generating triple {e1,e2,e4} | **16/16 = whole loop** | multi-directional → fully traversable |

**(b) Chiral inverse as a second instrument — worst-case steps to any target:**
| shelf N | 1 instrument | 2 instruments (primary + free conjugate) | speedup |
|---:|---:|---:|---:|
| 7 | 6 | 3 | **2.0×** |
| 11 | 10 | 5 | **2.0×** |
| 14 | 13 | 7 | **1.9×** |

## Verdict
**(a) The even loop un-traps recovery.** A flat 14-circle's half-turn mirror is a dead 2-cycle (F541), but the 14-loop is fully traversable: its octonion generating triple reaches all 16 elements. A single generator only spans the 4-element embedded-ℂ sub-loop, so the traversal is genuinely **multi-directional** — and that multi-directionality is exactly what makes the *even* case live on the loop where it is trapped on the circle. This is "a loop holds even happily" (F544) carried from the mirror onto traversal/recovery.

**(b) The chiral inverse is a free second instrument that halves the cost (F516).** The conjugate is **free** — conjugation is a Class-K sign-flip (F544 / `srmech loop_conj`), not a separate stored kernel — and running it alongside the primary reaches every target from **both** chiralities (the two hands, F514/F528), halving the worst-case steps (~2×). This is the F516 reading made concrete: two instruments **split the chiral work the way two people talking split it**, at no extra maintenance cost.

Together: the even loop is both **live** (fully traversable) and **cheap** to traverse (its own free chiral inverse). SNN-necessity stays open (the user's standing flag) — this is the math, not an SNN claim. Favored not privileged (F398); held open (F394).
