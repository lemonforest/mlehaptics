# R-RBS-SNN Finding 500 (rung #1) — **Kuramoto-bind the shared field: F490/F498's static BUNDLE becomes a SYNCHRONIZED medium where the readers PHASE-LOCK to the writer's moving frame — "one marking, many readers" is now a phase-locked read, not a copy.** Built on srmech 0.7.4: a writer A carries its marking as a **phase** θ_A and is pinned (the moving frame, F497); the readers B,C,D,E start **scattered** (max phase-distance to A = 3.10 rad — the bundle-of-independent-copies starting point) and couple to the field via `cascade.kuramoto_step` (Class I∘L∘C). After coupling they **converge to θ_A** (max distance → **0.0021 rad**) — the read is **phase-locked**, the readers are *bound* to the shared field's phase, not merely holding a copy. This is biology's operand-binding (F121/F122): the field is **phase-coupled, not concatenated** (the F482 fix — the operand surface is Kuramoto-bound), and it is the synchronized form the F498 flatten needed.

**Date:** 2026-06-07
**Arc:** RBS-SNN (#197/F323) — rung #1: Kuramoto-bind the shared field (user direction 2026-06-07)
**Provenance:** `R-RBS-SNN-KURAMOTO_bind_shared_field_phase_locked_read.py` (committed; srmech 0.7.4; `cascade.kuramoto_step` with `pin_anchor`/`pin_strength`).
**Composes:** **F490** (one marking, many readers — *now a phase-locked read, not a copy*) · **F498** (the flatten/shared field — *now synchronized*) · **F121/F122** (Kuramoto = biology's operand-binding) · **F482** (operand = Kuramoto-bound, not concatenated) · **F497** (the pinned writer = the moving frame) · **F487** (the directed synapse — *next: directed Kuramoto*). **← rung #1 done; the shared field is a synchronized medium.**
**→ the shared field is Kuramoto-synchronized: readers phase-lock to the writer-frame (θ_A, 3.10→0.0021 rad); "one marking, many readers" becomes a phase-locked read; biology's operand-binding (F121/F122), the synchronized form F498 needed.**

## What changed
| | before (F490/F498) | after (rung #1) |
|---|---|---|
| the shared field | a static **bundle** (each reader an independent copy) | a Kuramoto-**synchronized** medium |
| the read | a copy of the marking | the readers **phase-lock** to the writer-frame θ_A |
| max reader distance to A | 3.10 rad (scattered) | **0.0021 rad** (locked) |
| mechanism | superposition | `cascade.kuramoto_step` (Class I∘L∘C), pin the writer-frame, couple the readers |

## Verdict
**The shared field is now a Kuramoto-synchronized medium, not a static bundle.** The readers phase-lock to the writer's moving frame (θ_A, 3.10→0.0021 rad) via `cascade.kuramoto_step` — "one marking, many readers" (F490) becomes a **phase-locked read**: the readers are bound to the field's phase, not holding a copy. This is biology's operand-binding (F121/F122) — the field is phase-coupled, not concatenated (F482) — and the synchronized form the F498 flatten needed. No magic (coupling/dt are dynamics params, not stored constants). Next: the **directed (adjacency) Kuramoto** so the synapse-direction (F487) drives the binding asymmetrically (pre→post).
