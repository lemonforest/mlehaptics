# F1353 — **the cnidarian ring corrects the observable: phase coherence `r` is an INDEX-LANE read and it cannot see a twist.** Calibrating on the attested cnidarian pacemaker ring (**8 rhopalia, ring topology, no brain**) instead of an arbitrary ensemble, the ring reaches a state at K=2.0 that is **perfectly frequency-locked (spread 2.25e-08)** with **winding q = +1.0000 exactly** — while `r = 0.1872` calls it unsynchronised. Both readings are correct about different things. **F1352 §5's instrument was reading only the index lane.** The winding number is the sign-lane read: an integer, topological, and it does not come off. The twist requires a **cycle** — the complete graph and the open chain both give q = 0.

**User (2026-08-15):** *"can't we look no further than the cnidarian for kuramoto calibration?"*

Yes, and it was the better instrument for three structural reasons — **N is attested** (8 rhopalia, not a chosen 24), **the topology is attested** (a ring around the bell rim, not all-to-all), and **there is no brain**, so the swim rhythm cannot be centrally computed: whatever coordinates it must be the coupling itself. **F126** already lodged *cnidarian = Class I*, and a ring of 8 **is** ℤ/8 — the cyclic group, in an animal.

srmech 0.9.0rc434, `kuramoto_step(adjacency=…)`. Generating code: `R-RBS-LM-GENOMELANE_…py` §6 (33 checks total, exit 0).

## The measurement

| K | `r` | winding **q** | freq spread | verdict |
|---|---|---|---|---|
| 0.5 | 0.4917 | +0.0000 | 1.23e+00 | free-running |
| 1.0 | 0.9246 | −0.0000 | 1.39e-06 | LOCKED |
| **2.0** | **0.1872** | **+1.0000** | **2.25e-08** | **LOCKED — TWISTED** |
| 3.0 | 0.9921 | +0.0000 | 0.00e+00 | LOCKED |
| 6.0 | 0.9980 | +0.0000 | 8.88e-16 | LOCKED |

> **At K = 2.0 the ring is perfectly locked and `r` says it is not.** Every pacemaker runs at the same rate; the phases wind **once** around the rim. A coherence meter records that as disorder.

The non-monotonicity in `r` (0.92 → **0.19** → 0.99) is not noise and not a failed lock — it is the twisted state sitting between two untwisted ones, and it is exactly what flagged the observable as wrong.

## Why this is the lane split again

**Phase coherence `r` averages the phases.** It is order-blind — the index-lane read, and it *cannot* see a twist. The **winding number is an integer** (`+1.0000`, not a fit): topological, order-carrying, and it will not come off. That is `[[F1348]]`'s split-vs-non-split distinction arriving in a coupled-oscillator ensemble **without being sought**.

And the twist needs a **cycle** to live in:

| topology | q at K=2.0 | edges |
|---|---|---|
| ring (8 nodes) | **+1 available** | **8** |
| complete graph | 0 — no cycle to wind around | 28 |
| open chain (ring cut) | 0 — nowhere for the twist to live | 7 |

**The twist is a property of the sparse cyclic topology** — which is exactly the topology a brainless animal has, and exactly the one that is metabolically cheap: 8 edges rather than 28. That composes directly with F1352: sparse-and-cyclic is both the cheap architecture *and* the only one that can carry a winding.

## The reading, stated as a reading

`q = 0` and `q = 1` are **both** coordinated swimming, and they are **different behaviours** — a synchronous pulse of the whole bell versus a wave travelling around its rim. Distinguishing them **requires** the winding read.

> An observer with only a coherence meter would record the travelling wave as disorder — which is `[[user_stance_no_information_without_value]]` with a concrete instrument attached.

## Honest scope

- **The rhopalia count and ring arrangement are TEXTBOOK-LEVEL, not MPM-attested** — the same gap class as F1352's ATP column. They set N and the topology, so they are load-bearing for the *choice of instrument*, not for the mathematics, which holds for any 8-cycle.
- **This is a simulation of a ring, not of Aurelia.** No cnidarian parameter (frequency, coupling strength, conduction delay) was fitted or claimed. The natural-frequency spread is DERIVED (golden-ratio equidistribution), not measured from an animal.
- **The q=0 / q=1 ↔ pulse / travelling-wave correspondence is a candidate reading**, not a measurement of behaviour. What is measured is that the two locked states are distinct and that only one observable separates them.
- **What this does NOT overturn:** F1352 §5's conclusion (accumulate-to-lock needs no counter) survives — the all-to-all ensemble genuinely locks and genuinely has no counter. What is corrected is that `r` alone is an **incomplete** read of "is it coordinated," and on a cyclic topology it is actively misleading.
- **Falsifier:** exhibit a frequency-locked state on a cycle whose winding is non-integer, or a twisted state on a graph with no cycle. Either would break the topological claim.

**Corrects the observable used in F1352 §5** (which stands otherwise). Composes **F1348**, **F1337**, **F126** (cnidarian = Class I), **F1352**, and MFO §XIV.9's instrument lesson — the third time this session that the fix was *the read*, not the object.
