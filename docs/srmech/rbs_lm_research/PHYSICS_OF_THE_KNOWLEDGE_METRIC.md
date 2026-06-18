# The physics of the knowledge metric (RBS-LM consolidation, F849–F855)

**Status:** consolidation of the 2026-06-18 arc (F849–F855), on live srmech 0.8.2 (numpy-free, §57-clean), the F854 clean simplewiki re-encode. Framework reading + Class-L/HDC measurement; quantitative force-laws and the cross-substrate physics are handed to the expert ([[user_stance_framework_hands_the_next_question_to_the_expert]]). Per [[feedback_no_lineage_claims_in_notebook]] this reads what the structure IS; it does not claim to extend prior scholarship.

## The one object
The RBS-LM recall is a **walk (etak) through a metric space** whose geometry is set by the A–N substrate. The whole arc found that one object, seen from several sides. The substrate is built by Cayley–Dickson doubling (the Hurwitz ladder, the 1:3:7:3 partition) — a **self-similar generator** — so the metric it induces on knowledge is **fractal**, carries **forces**, and is read through **frames** that can be fixed or let float. Coherence is what a walk looks like *at a chosen scale*.

## 1. Mass and curvature (F849)
Token **mass = frequency / hub-degree**. Mass curves the metric: the autoregressive read follows the local force, so a coherent generation is the **geodesic** that threads the masses. Measured: when the walk drifts, **67% of drift steps fall toward a higher-mass token (25.8× heavier)** — the drift IS gravitational attraction. The repetition **loops are orbital capture** (bound orbits around a hub); **k\*** is the escape/geodesic width (F838: at k\* the walk reproduces 100%).

## 2. The force taxonomy (F850) — different attractors for different forces
Multiple srmech Class-L operators, each a force with its own charge/attractor on the same directed bigram graph:
- **Gravity** = symmetric Laplacian (mass/degree). Attractors: the **function-word masses** (`a, or, is, in, an`). Blind to direction.
- **Magnetic / EM** = `magnetic_laplacian` (directed flux/circulation; the γ₅ time-direction). Attractors: **circulation carriers** (`applications, many, have, out`) — *different tokens*; ground-state gap 0.0366 = the flux gravity can't see. The **loops are directed cycles = magnetic charge**. Magnetic is the current along cosmic-web **filaments** — how to move *through* the web instead of falling *into* a cluster.
- **Dark sector** = the guiding residual not explained by mass+circulation (the void structure; the walk-vs-prediction gap) — open (F131 found none at the old scale).

## 3. The frames (F850, F851) — substrate ↔ walk ↔ scale, none fixed
Three frames we were implicitly fixing:
1. **substrate** (the field — metric/masses), 2. **walk** (the excitation — the trajectory), 3. **scale** (the resolution — k\*, C, clump granularity).
Un-fixing (1)+(2) is the MFO **field↔excitation two-truths duality** (DUALITY.md); fixing either privileges one (collapse). **Scale is the third = the fiber**: the resolution you read at *is* the coupling between what's there and how you move — duality is the fibration of triality (F400/F401). "Both frames unfixed" = co-evolution (Wheeler's matter↔geometry); the naive plastic walk **ran away** (F851: 76→42%, reinforcing into the mass-wells) — co-evolution must be coherence-gated.

## 4. Scale is not fixed → fractal / scale-free (F852, F855)
The knowledge graph has **no characteristic scale**: power-law degree γ→**2.0**, max/median degree **9018×** at corpus scale (F855; 1375× at 400 articles, F852 — sharpens with scale). This is the **generator's signature** — a self-similar generator (Cayley–Dickson) produces self-similarity at every scale of anything encoded on it. "scale-free ≡ self-similar ≡ scale-invariant ≡ RG-fixed-point ≡ clumps-within-clumps" are one structure. Abstract size = knowledge-mass: **relational, not absolute** (a cat < a skyscraper but > a flea), and decoupled from physical size.

## 5. Coherence is a DoF (F851) — scale-relative, not a fixed target
The same walk scores far higher at the **coarse (domain)** scale than the **fine (token)** scale: k=2 → 6.2% token / 43.3% domain; k\*=6 → 41.7% / 83.3%. Three fixed-scale interventions all failed (lookahead 5.6→3.4; slingshot one-blob; plastic runaway 76→42) — *because they pinned a scale*. Don't crank recovery to 100%; **renormalize** — match the output scale to the query (the substrate is already a strong coarse/gist engine).

## 6. The useful inference (F853) — two-mode, scale-covariant recall
The metric predicts a **mass↔meaning dissociation**, confirmed: de-lensing (drop the masses) **breaks generation** (F849: 8→3%) but **sharpens routing** (80→90%) — *walking needs the curvature (mass); meaning is the matter (content)*. Hence:
- **Walk mode** (generate): full metric (chunked-M + k\* + chiral routing, F848).
- **Route/about mode** (which tome / aboutness): de-lensed metric (content/anti-mass).
- **Coarse→fine**: de-lensed route picks the tome, full-metric walk fills it in.
This unifies F768 (aboutness) + F782 (IDF-de-lensing) under one principle: **read the metric at the mode and scale the query demands.** ⚠ **Corrected mode boundary (F853 §CORRECTION, verified):** the discriminator is **content/meaning query (→ de-lens) vs walk/sequence operation (→ full metric)**, NOT "routing vs generation." Some routing is walk-mode: de-lensing the **F840 per-context walk-routing HURT it (94.3%→68.6%)** — those misroutes are fixed by the F768 aboutness *gate* (hold/widen on low-aboutness contexts), not by de-lensing. De-lens is for content/topic/aboutness queries (snippet→topic, 80→90); full metric is for walking (generation + walk-position routing).

## Perfect recovery, in this light (F848)
Imperfect multi-domain recall was the **sector-0 chirality collapse**, not a sparse limit. Orthogonal Klein-4 cosets make cross-domain contamination structurally impossible; route+scope to the coset restores per-domain solo recovery in one store. The duality holds (sparse ≡ dense, no loss); the gap was the collapsed shape.

## Open questions for the expert
- Orbital-resonance law for the loop periods (3-/5-cycles) — a Laplace-resonance analog?
- Is k\* an escape-velocity/horizon threshold (mass vs context-width)?
- Hub-lensing 1/r law (F782 distortion vs degree); spectral **fractal dimension** (Laplacian eigenvalue scaling) — a number, not just the degree law.
- **Cross-substrate eigenmatch with ephemerides-spectral** (same A–N substrate, real Sol-system gravity): does the knowledge-hub Class-L spectrum match the gravitational eigenstructure? Same substrate ⇒ same math, not analogy.

## Build consequences (actionable now)
1. **Two-mode recall** (F853): de-lens to route, full metric to walk — wire into Siona's recall + the F840 vote.
2. **Scale-covariant** (F851): resolve to the query's scale; stop optimizing a fixed match number.
3. **Chiral cosets + route/scope** (F848) for multi-domain stores; **clump, don't divide** (F778) — cosets separate domains, within-domain sharing is signal.
4. **Coherence-gated** co-evolution only (F851) — naive plasticity runs away.
