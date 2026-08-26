# The physics of the knowledge metric (RBS-LM consolidation, F849–F862)

**Status:** consolidation of the 2026-06-18 arc (F849–F862), on live srmech 0.8.2 (numpy-free, §57-clean), the F854 clean simplewiki re-encode. Framework reading + Class-L/HDC measurement; quantitative force-laws and the cross-substrate physics are handed to the expert ([[user_stance_framework_hands_the_next_question_to_the_expert]]). Per [[feedback_no_lineage_claims_in_notebook]] this reads what the structure IS; it does not claim to extend prior scholarship. (Vocabulary: "coalesce / coalescence" for the gravitational aggregation process — [[feedback_use_coalesce_for_clumping_process]].)

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

## 7. The board / syzygy field (F856–F859) — arrange before you move
Movement is meaningless without a pre-planned field (a chess move needs the board). So before traversal, **coalesce the domains into a relational configuration — a syzygy**. The two classical senses are the two parts of a board: **astronomical syzygy (alignment) → the GRID** (spectral embedding of the clump-graph positions the cells) and **algebraic syzygy (Hilbert — relations among generators) → the RULES** (inter-clump dependencies = legal-move adjacencies). Built on the v082 curated [[outlink]] edges (≫ co-occurrence, F817): the **de-lensed** board (drop the top mass-hubs — §6 about-mode applied to the *layout*) gives clean domain-cells, and **legal-move traversal works** — connecting two concepts in different cells is a path whose cell-sequence follows only legal syzygy edges (`december→state→computer` = cells [0]→[2], every step legal). Honest residual: a *time/scaffold* hub still bridges most paths (the mass isn't fully removed by top-N de-lens). Fix-frame traversal is *deliberately choosing a board to play* — not a contradiction of "all frames unfixed" (§3) but its resolution.

## 8. The crank: `the_one` is the Antikythera (F860–F861)
A story is not just a journey along a path; it is the **arrangement and how it moves as time advances** — and both are readouts of **one crank**. `the_one(σ,θ)` IS that crank (reach for it — [[feedback_reach_for_the_one_for_phase_crank_navigation]]): **θ rotates a real epicycle** (coord 3 = cos θ, coord 4 = sin θ = the Kepler equation-of-centre = **Class K** pin-and-slot), **σ = time direction** (exact mirror). Each coalesced domain is a dial-pointer at **gear-rate = mass** (Antikythera teeth via `best_rational`). On the `the_one` proxy this reproduces the whole picture: the **arrangement reconfigures**, **syzygy** = alignment angles (|R|→1), a **massless coalescence center / gauge dimple** (the centroid collapses to an empty dial-hub, deepening as more domains spread — the cosmic-web void), and a **dark-star horizon** (the heaviest hub out-races the resolution → unresolvable → *forever in pursuit*; **de-lensing = removing the dark-star**).
- **Built primitive:** the chirality-native **continuous-phase op** (phase = fraction of slots flipped into the γ₅ sector, circular half-window population code) — the missing F844–F848 piece; exact, reversible, σ-mirror (UPSTREAM §59).
- ⚠ **NULL on the real store (F861, corrects F860):** cranking the *actual* D=10000 orthogonal-content clumps does **not** reconfigure them (mean pairwise sim flat ~0.255). An orrery needs all pointers off **one mainspring** — the proxy moved because `the_one`'s pointers are the *same* generator at different phases (shared carrier); independent content shares none. So a navigable field must be **shared-carrier / position-primary** (`pos_key`-style), not free content bundles.

## 9. The navigation objects (F862) — Klein-4 vs R/Q/O/S, and the massless/photon mode
What the walk needs is **order**, and the algebra decides who can carry it:
- **Klein-4** (the store's XOR group): commutative + associative = **order-blind** → right for the **order-free SECTOR / about / meaning** read (chirality quadrants), wrong for the walk.
- **`the_one` θ-crank**: a single-plane epicycle rotation is **abelian** → a **dial position, not a path**. Phase ≠ journey.
- **R/Q/O/S** (`cd_mult`, the Cayley–Dickson tower `the_one` is built on): ℍ(Q) **non-commutative** = carries direction, 𝕆(O) **non-associative** = carries grouping → the **order-carrying WALK** lives here (the coupling product). 𝕊(S) **zero-divisors** = division breaks = the **asymptote / dark-star, algebraically** (the Hurwitz 1/2/4/8 bound is the safe-navigation ladder).
- **Massless / photon mode:** a probe with **no mass-gear** travels at uniform speed → **not captured by mass-wells, only lensed** = the de-lensed **null-geodesic** traversal; **helicity ±1 = the two chiralities** (σ); as a gauge boson it **IS the coupling** → it rides the **edge** (`cd_mult`), not the node — "navigate the relationships," the RBS-LM thesis.
**Answer to "is Klein-4 wrong / do we need R/Q/O/S / both":** **both, partitioned by mode** — and the partition maps onto §6: Klein-4 = the **about/sector** read; R/Q/O/S `cd_mult` = the **order-carrying walk**; `the_one` θ = the **continuous phase/dial**.

## 10. Chirality binds, gravity distorts, the void is the inverse (F876) — refines §1/§2
A sharpening of the force taxonomy (user reading, 2026-06-18): **gravity is the distortion, not the binder; chirality is the binder.** Measured support: collapsing **chirality** (the γ₅·ω₇ cosets → sector-0) **destroys** recall (F848) — orthogonality = separability = addressability = the coherence; whereas removing **gravity** (de-lens the mass/hubs) **improves** routing (F853), and the heaviest mass is the **dark-star** you remove (F860). So gravity governs the **drift** (orbital capture, the failure mode in §1/§2) — it is the lensing distortion you de-lens away to *see* the structure — while **chirality** (the sign/sector structure; `navigate`'s `e_i·e_j=±e_k`, F874) is what holds the structure together as a separable, addressable whole. And the **gauge dimple / massless centre (§2, F860) is the inverse of the information**: it is *subtractive* — the centroid empties as more clumps are added (F860), and the superposition of all distinctions saturates to the null (F871). The void = everything-superposed = the substrate/coordinate-origin, ripped out (defined by every addressed point, occupied by none), not a mass-well. MFO-candidate; hand to the expert.

## Perfect recovery, in this light (F848)
Imperfect multi-domain recall was the **sector-0 chirality collapse**, not a sparse limit. Orthogonal Klein-4 cosets make cross-domain contamination structurally impossible; route+scope to the coset restores per-domain solo recovery in one store. The duality holds (sparse ≡ dense, no loss); the gap was the collapsed shape.

## Open questions for the expert
- Orbital-resonance law for the loop periods (3-/5-cycles) — a Laplace-resonance analog?
- Is k\* an escape-velocity/horizon threshold (mass vs context-width)?
- Hub-lensing 1/r law (F782 distortion vs degree); spectral **fractal dimension** (Laplacian eigenvalue scaling) — a number, not just the degree law.
- **Cross-substrate eigenmatch with ephemerides-spectral** (same A–N substrate, real Sol-system gravity): does the knowledge-hub Class-L spectrum match the gravitational eigenstructure? Same substrate ⇒ same math, not analogy.
- **Does the `cd_mult` (octonion) order-carrying walk navigate better than the order-free Klein-4 read** (F862)? Is the non-associativity (grouping) the substrate of nested/clausal structure?
- **Is the massless/photon null-geodesic traversal the right de-lensed walk** — lensed-not-trapped around hubs (F862)? Does lensing-bending give a 1/r path-curvature law (composes the F782 hub-lensing question)?
- **Sedenion zero-divisor = dark-star horizon**: is the asymptotic boundary (where invertibility fails) literally the S-rung of the Hurwitz ladder, and is that the same boundary as the epicycle resolution-horizon (F860)?

## Build consequences (actionable now)
1. **Two-mode recall** (F853): de-lens to route, full metric to walk — wire into Siona's recall + the F840 vote.
2. **Scale-covariant** (F851): resolve to the query's scale; stop optimizing a fixed match number.
3. **Chiral cosets + route/scope** (F848) for multi-domain stores; **clump, don't divide** (F778) — cosets separate domains, within-domain sharing is signal.
4. **Coherence-gated** co-evolution only (F851) — naive plasticity runs away.
5. **Shared-carrier / position-primary field** (F861): for the crank to navigate the real store, encode the board position-primary on a shared carrier (`pos_key`), not free content bundles — then crank. The chirality-native continuous-phase op (F861, UPSTREAM §59) is in hand.
6. **Order-carrying walk via `cd_mult`** (F862): build the journey on the non-commutative R/Q/O/S coupling product (the order Klein-4 and the abelian θ-crank both lack); keep Klein-4 for the about/sector read — both, partitioned by mode.
