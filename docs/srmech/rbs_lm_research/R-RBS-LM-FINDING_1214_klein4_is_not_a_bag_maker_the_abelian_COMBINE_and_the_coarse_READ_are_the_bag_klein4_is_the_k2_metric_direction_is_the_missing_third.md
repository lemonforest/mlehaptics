# F1214 — Klein-4 is NOT a bag-maker: the bag came from the ABELIAN combine + the COARSE similarity read, not the Klein-4 shape. Klein-4 IS the k=2 metric (the 4 quadrants); direction is the MISSING THIRD, addable at the same Class-L cost

**User (2026-07-14):** *"why did Klein-4 end up as a bag? our idea was it should stream the genome content — all 4 quadrants as a single object. Was it the wrong tool (all it will ever do is bags), even though a genome has endianness — or could it have been given symmetry/asymmetry for the same Class-L cost?"* The instinct is right: it was **not** the wrong tool, and direction **is** addable at the same cost. The bag came from HOW we combined + read, not from Klein-4.

## Three layers — only two are the bag, and neither is the Klein-4 shape
1. **Klein-4 the CARRIER (4 sectors/quadrants per dimension) is correct.** "All 4 quadrants as one object" is a per-slot **STATE** (which of the (4:3)|(3:4) chirality quadrants, γ₅/iω₇ — F130/F132). Klein-4 encodes that perfectly. Sound idea, right tool.
2. **The bag came from the ABELIAN combine.** `klein4_bind` = the V₄ = Z₂×Z₂ group op = **commutative** (`bind(a,b)=bind(b,a)`, measured sim 1.000, F1211) → a *pair* loses which-is-which. `klein4_bundle` = superposition = **order-free** → a *sequence* loses order. Klein-4 is abelian **by definition** (that is what V₄ *is*), so combining items with only bind+bundle can ONLY produce order/direction-blind objects. That is not a Klein-4 defect — abelian groups are order-blind, full stop.
3. **AND the `klein4_similarity` READ is coarse (sector-occupancy), so even direction ENCODED into the HV barely surfaces.** MEASURED: a src/dst **role-bind** (same carrier, same bundle cost, +2 fixed role vectors) distinguishes long words (`draw/ward` 0.879, `listen/netsil` 0.972) but NOT short ones (`cat/tac`, `abc/cba` still 1.000) — the similarity histogram saturates. So the HV-similarity channel is itself a partial bag.

## The genome's endianness WAS in the input — the abelian combine projected it out
A byte/genome stream has direction (endianness); the content we fed in carried order. The abelian bind+bundle **flattened it away** — exactly the k=2 metric read that provably cannot see the odd/which-way channel (F552). The direction wasn't absent from the data; it was discarded by the even-only combine.

## The framework read: Klein-4 IS the k=2 metric; direction is the MISSING THIRD
Klein-4 = V₄ = the **two truths** — its two Z₂ generators ARE γ₅ and iω₇ (F403), the k=2 even structure. It carries the 4 quadrants (the metric/state) perfectly. **Direction / order / curvature is the THIRD** — the *product* of the two generators (the coupling), the k=3 completion, the responsion (F1209). The bag was the **missing third**, precisely F1209/F1211: op/operand/**responsion** = field/excitation/**curvature**, and we only ever built the field+excitation (the abelian even part).

## Direction is addable at the same Class-L cost — three ways (we picked the reliable one)
Add ONE non-abelian ingredient on top of the same Klein-4 carrier:
- **role** (src/dst bind) — cheapest, but limited by the coarse similarity read (measured above);
- **permutation** ρ (the classic VSA sequence operator) — but srmech has no klein4-native permute (`permute` is a byte bit-rotation), so a `klein4_permute` (sector/dimension permutation) is a **missing primitive → upstream candidate**;
- **signed edge** — the directed (magnetic) Laplacian charge (`w_fwd−w_bwd`): the **winning** carrier (F1212), because it stores direction in an **exactly-readable integer channel**, not the coarse similarity histogram. Same node/edge structure, one extra signed column — same Class-L cost.

So: Klein-4 stays (it IS the metric / the 4 quadrants). Direction is a **cheap add-on**, and the *reliable* place to put it is the structural charge (the digraph, F1212/F1213), because the klein4 HV-similarity read is too coarse to carry it dependably. The base bagged because it used ONLY the abelian ops and never added the third — not because Klein-4 can only bag.

Composes **F1211** (the base was metric-only — this explains WHY), **F1209** (curvature = the third/responsion), **F403** (Klein-4's two Z₂ = γ₅/iω₇ = the two truths; their product = the third), **F1212/F1213** (digraph = the reliable direction channel), **F552** (the odd channel the metric read can't see), **F132/F130** (Klein-4 = the chirality-quadrant carrier), [[feedback_reach_for_the_one_for_phase_crank_navigation]] (abelian crank vs non-abelian walk).
