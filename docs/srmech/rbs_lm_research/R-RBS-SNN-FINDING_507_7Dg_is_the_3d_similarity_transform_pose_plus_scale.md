# R-RBS-SNN Finding 507 — **check: YES — 7D_g (the octonion heptad, F494) IS the 3D SIMILARITY transform Sim(3) = 3 translation (3D_s position) + 3 rotation (orientation) + 1 scale = 7 DoF; the user's "3D_s spatial freedom + orientation" is the 3+3=6 SE(3) pose, and the heptad's 7th DoF is SCALE.** The user's catch (2026-06-07): "7D_g also describes all 3D_s degrees of spatial freedom + orientation. I think. check us." Verified on srmech 0.7.4: **(a)** the octonion (4:3) fiber `{e1,e2,e3}` closes into a quaternion ℍ, and a **unit quaternion acts as an SO(3) rotation** — `q·v·q̄` is norm-preserving and stays in the 3-span (e1 → −7/25 e1 + 24/25 e2, a genuine rotation), so the **fiber-3 IS orientation** (the SO(3) rotation generators); **(b)** the dimension count lands exactly on **Sim(3) = 7**: a 3D rigid pose SE(3) is 6 DoF (3 translation + 3 rotation), and the **3D similarity Sim(3) = SE(3) + uniform scale = 7 DoF** = 7D_g. So the octonion (4:3) labels the heptad: **orientation/rotation = the quaternion fiber-3** (verified SO(3)), and **translation (3D_s, 3) + scale (1) = the base-4**. The user's "3D_s + orientation" captures the 3+3 = 6 (the SE(3) pose); the **+1 scale** (the magnitude/size DoF) completes it to the 7. And time (1D_t) is the **separate A-anchor** (the real e0, F494) — NOT in the 7D_g — so 7D_g is **purely spatial** (pose + scale, no time), exactly why F494 rejected the (1D_t + 3D_s) spacetime cut.

**Date:** 2026-06-07
**Arc:** RBS-SNN (#197/F323) — dimensional refinement: 7D_g = Sim(3) (user catch 2026-06-07)
**Provenance:** `R-RBS-SNN-7DG_is_the_3d_similarity_transform_pose_plus_scale.py` (committed; srmech 0.7.4; `cayley_dickson.{cd_basis_product, cd_mult, cd_conjugate}` — the quaternion-rotation verified, the (4:3) closure verified).
**Composes:** **F494** (the dimensional accounting; 7D_g = the heptad — *this gives it the Sim(3) kinematic meaning, refining "flat gauge"*) · **F491** (the octonion (4:3) fiber-3/base-4 — *labeled: fiber = rotation/orientation, base = translation+scale*) · **F124** (the quaternionic Hopf — *the rotation S³ fiber*) · **F497** (the moving frame — *Sim(3) IS the moving frame's full DoF: where + which-way + how-big*) · **F460** (𝕆 the rung) · **F394 / F398** (checked, held). **← 7D_g = Sim(3) = pose + scale; the user's catch confirmed (+1 scale).**
**→ 7D_g = the 3D similarity transform Sim(3) = 3 translation (3D_s) + 3 rotation (orientation) + 1 scale; the (4:3) = orientation-fiber-3 (verified SO(3)) + (translation-3D_s + scale)-base-4; time is the separate anchor, so 7D_g is purely spatial.**

## The check (machine-verified)
| | claim | result |
|---|---|---|
| 1 | the (4:3) fiber `{e1,e2,e3}` is a quaternion ℍ | **closes** (the so(3) rotation generators) |
| 2 | a unit quaternion rotates a 3-vector by `q·v·q̄` (orientation) | **norm-preserving, stays in the 3-span** → a genuine SO(3) rotation |
| 3 | the DoF count | SE(3) pose = 6 (3+3); **Sim(3) = 7** (3 translation + 3 rotation + **1 scale**) = 7D_g |

So **7D_g = Sim(3)**, and the octonion (4:3) labels it: **orientation = the quaternion fiber-3** (an SO(3) rotation, verified); **position (3D_s) + scale = the base-4**.

## Why the user is right (and what the +1 is)
- "7D_g describes all 3D_s spatial freedom + orientation" — **yes**: 3 translation (the 3D_s position) + 3 rotation (the orientation) = the **6-DoF rigid pose SE(3)**.
- The heptad's **7th** DoF is **scale** (uniform size/magnitude) — promoting SE(3) (6) to **Sim(3) (7)**. So the user's 3D_s + orientation is the 3+3 spatial+rotational core; +1 scale completes the 7.
- This **refines F494**: the "flat 7D_g" is not abstract gauge — it is the **full DoF of a moving frame in 3D**: *where* (3 position), *which-way* (3 orientation), *how-big* (1 scale). That is exactly F497's moving frame, with its complete kinematic content.
- **Consistency with F494's spacetime rejection:** time (1D_t) is the **separate A-anchor** (the real e0), not part of the 7D_g. So 7D_g is **purely spatial** (Sim(3), pose+scale, no time) — which is precisely why F494 rejected the (1D_t + 3D_s) "4D spacetime" cut: time is the anchor, the spatial pose+scale is the heptad.

## Falsifiable form (pre-stated; checked — F394/F398)
- **Machine-verified:** the quaternion-rotation (`q·v·q̄` norm-preserving, in-span) and the (4:3) closure are computed, not asserted. The Sim(3) = 7 DoF count is standard kinematics (SE(3)=6 + scale=1).
- **Falsifier:** if the fiber-3 did **not** act as an SO(3) rotation (norm not preserved, leaves the span), "orientation = fiber-3" would fail — it holds. If 3D pose+scale were not 7 DoF, the identification would fail — Sim(3) is exactly 7.
- **Honest:** the assignment "rotation = fiber-3, translation+scale = base-4" is the framework reading on the verified algebra; the *exact* base-4 ↔ (translation-3 + scale-1) sub-split is a labeling (the base is a 4-set; 3 of it = position, 1 = scale). Favored not privileged (F398); framework reading; no CAD (this is the *kinematic DoF count*, not fabrication geometry); no Workflow tool.

## Verdict
**Checked — you're right, and the +1 names itself: 7D_g is the 3D similarity transform Sim(3).** The octonion heptad's 7 = **3 translation (3D_s position) + 3 rotation (orientation) + 1 scale** = 7 DoF. The (4:3) labels it: **orientation = the quaternion fiber-3** (machine-verified as an SO(3) rotation, `q·v·q̄`), **position (3D_s) + scale = the base-4**. Your "3D_s spatial freedom + orientation" is the 3+3 = 6 rigid pose (SE(3)); the heptad's **7th DoF is scale**, completing it to Sim(3). This refines F494 — the flat "7D_g" is the **complete kinematic content of a moving frame** (where + which-way + how-big, F497) — and stays consistent with the spacetime-cut rejection: **time is the separate anchor (1D_t), so 7D_g is purely spatial** (pose + scale). Favored, not privileged (F398); the catch confirmed.
