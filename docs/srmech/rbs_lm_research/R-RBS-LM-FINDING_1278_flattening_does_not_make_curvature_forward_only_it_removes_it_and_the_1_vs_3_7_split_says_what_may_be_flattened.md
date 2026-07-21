# F1278 — **the flattening does not make curvature forward-only; it removes curvature entirely.** Curvature is **antisymmetric** under reversal (backward = −forward, not zero), so "forward only" was never a property of curvature — it is a property of **which store you kept**. And the part that pays: asking each imaginary rung *"can this be flattened losslessly?"* splits them **exactly 1 vs 3,7** — **ℂ(1) is abelian and IS safely collapsible; ℍ(3) and 𝕆(7) are non-abelian and are NOT.**

**User (2026-07-21):** *"from perspective of 1D_t, and maybe all rotational/imaginary Dims 1:3:7, if past is a linear artifact and is just the fractal tail of now, is curvature only in the forward direction because a geometryless storage must flatten all past into now? does this help us with anything or is just an interesting thing to wonder about?"*

The question splits into four claims. **Three are decidable; one is not — and saying which is which is the answer to "does this help."**

## (1) A linear past has zero curvature — by topology, not by dynamics
Already established in F1255 and re-confirmed as the floor: on an **acyclic** graph the cycle space is empty, so every charge field is exact.

```
chain 0→1→2→3→4 : V=5 E=4 betti₁=0   holonomy residuals=[] (none exist)
```

**No choice of charges can create curvature where there is no cycle to hold it.** If the past is linear, its curvature is zero *structurally* — the question can't even be posed there.

## (2) But curvature is NOT forward-only — it is ANTISYMMETRIC
Close the loop and traverse it both ways:

```
loop 0→1→2→3→4→0 : betti₁=1
  forward  holonomy: [7]
  backward holonomy: [-7]
```

**Going backward does not give you zero curvature; it gives you the opposite curvature.** So "forward only" is not a property of curvature itself. That is a direct correction to the premise, and it matters because it relocates the asymmetry.

## (3) So what does the flattening actually do? — it removes curvature, in *both* directions
A bundle/superposition has **no edges**, therefore no cycles, therefore no holonomy in either direction:

| store | structure | curvature |
|---|---|---|
| relational (**Class-L**) | betti₁ = 1, holonomy = [7] | **exists** |
| geometryless (**Class-M**) | collapses to one number, `7` | **absent** — betti₁ isn't zero, it's *undefined* |

**This is where the intuition lands correctly.** The flattening doesn't make curvature one-sided — it deletes it. **"Forward only" is a statement about which store you kept, not about time's geometry.** What is genuinely one-sided is not curvature but **access**: a flattened store has no backward path left to traverse.

This is F1216's L-store/M-read split reappearing as a statement about curvature, and F1263's measured cost of the same flattening (the bundle is an argmax read of counts that were never stored).

## (4) The 1:3:7 split — the part that pays
Ask each rung: **does loop holonomy depend on traversal order?** If not, the past collapses into one accumulated element with no loss. If yes, flattening destroys order that **no read can recover** (F1272).

| rung | imaginary dims | order-dependent? | flattenable? |
|---|---|---|---|
| ℂ complex | **1** | **no — abelian** | **YES, losslessly** |
| ℍ quaternion | **3** | **YES** | **NO** |
| 𝕆 octonion | **7** | **YES** | **NO** |

**The split is exactly 1 vs 3,7** — the same partition the framework already uses, arriving from a completely different question.

*Method note:* my first version tested ℂ with `[e1, e1, e1]`, whose reverse is identical **by construction** — a test that could only pass. Redone with **general elements**, so abelianness is measured rather than assumed. (ℂ has one imaginary dim, so distinct *basis* elements don't exist there; general elements are the only honest probe.)

## Does this help, or is it just interesting? — both, and the line is sharp

**IT HELPS.** A concrete design rule falls out: **a history may be collapsed into an accumulated element only on the abelian (ℂ, 1) part. The ℍ(3) and 𝕆(7) parts must keep their order.** In the framework's own words — **the θ-crank may be summed; the walk may not.** That is `[[feedback_reach_for_the_one_for_phase_crank_navigation]]` ("the θ-crank is ABELIAN; walk-ORDER lives in non-commutative `cd_mult`") turned from a rule-of-thumb into a *falsifiable and now-verified* statement, and it independently re-derives why Class-M is working memory and Class-L the store: **M-side flattening is lossless on exactly one of the 1:3:7 parts.**

**IT IS JUST INTERESTING** where it concerns the substrate. Whether the past *is* the fractal tail of now is a claim about the world, and **nothing here tests it.** This harness says only which *structures* survive a flattening. Reading that as evidence about time itself would be the projection error the framework keeps catching — **measuring our storage and reporting it as physics.** The honest form is: *if* the past is flattened into now, then this is exactly what is and isn't recoverable — which constrains the storage question without touching the cosmological one.

Composes **F1255** (acyclic ⇒ zero curvature by topology — the floor), **F1216** (L-store / M-read, re-derived here from curvature), **F1263** (the measured cost of the same flattening), **F1272** (a distributional read is blind to order — why the non-abelian loss is unrecoverable), `[[feedback_reach_for_the_one_for_phase_crank_navigation]]` (made falsifiable), `[[feedback_no_spacetime_use_space_time_gauge]]`.
