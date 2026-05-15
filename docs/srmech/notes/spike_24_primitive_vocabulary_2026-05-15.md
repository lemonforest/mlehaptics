# Spike #24 — Cross-domain primitive vocabulary + ephemerides residual analysis

**Status:** SCOPE locked 2026-05-15; Phase 1 inventory begins.
**Branch:** `research/spike-24-primitive-vocabulary-2026-05-15`
**Predecessor:** PR #416 (pin-and-slot algebra + algebraic-uniqueness synthesis), merged as `fba3065` to main.

## Genesis question

PR #416 closed with the §11.6.17 algebraic-uniqueness finding: the bronze's structure is forced by the algebra; anyone with the same period observations + same engineering substrate + minimum-cost optimization lands on the same gear-grouping. The user then extended this to a universal:

> *"if keplers equation is just gears and slots and pins, it does apply to anything else that moves the same way. I don't think that we can argue against that anymore."*

The burden of proof flipped (per `[[user_stance_kepler_shape_universal]]`): any Kepler-shape system instantiates pin-slot-gear primitives in some substrate; the counter-claim requires producing a Kepler-shape system that is NOT primitive-composable. Spike #24 tests this across the spectral collection's plug-ins.

## Methodology — disciplines locked

Five disciplines locked through the planning conductor calls of 2026-05-15:

1. **Abstraction-layer-first.** srmech is the score (abstraction); the spectral plug-ins (antikythera-spectral, ephemerides-spectral, chess-spectral, doom-spectral, othello-spectral, logo) are the instruments (instantiation). Phase 1 identifies primitives at the srmech abstraction layer first, ignoring all plug-in-specific cosmos / chess / doom content. What survives is *abstraction-layer-real*. *"Ignore the plug-in as one step of our research"* per user instruction.

2. **Mechanical-first abstraction-layer identification.** What is in the srmech python package source = abstraction layer. What is in plug-in packages = instantiation. Phase 2's "extends" cells flag promotion candidates for a future PR pass.

3. **Pi-as-projection.** Integer-cyclic upstream, continuous (pi-bearing) downstream. Per `[[user_stance_pi_as_projection]]`. Name primitives in integer-cyclic terms where possible; pi-bearing forms are documentation aids for cross-referencing continuous-frame literature, not load-bearing primitive descriptions.

4. **Real-coupling subtraction before primitive claims.** Earned-frontier discipline. For Phase 3, extract known couplings from JPL data + existing ephemerides-spectral structures (Sol Resonance Graph, breathing-Laplacian, spin-orbit-resonance, tidal, secular, J2/J4 gravitational harmonics) and subtract their contributions from the residual against DE441 before naming any "missing primitive." A residual that resolves to a real coupling is NOT a primitive — it's an under-modelled physics term. *"Learn how to learn what we don't know"* applies only at the residual that survives the subtraction.

5. **Two-table CPU mapping with bronze-standalone column.** Per user 2026-05-15: *"cpu mapping is great, but it's only one perspective. an additional table that is bronze-operator mapping will reveal things we don't know."* Table 2A = bronze→CPU correspondence (where it's clean). Table 2B = bronze-standalone (where bronze content has no clean CPU analog, OR has a lossy/leaky CPU analog — document both *lossy* and *leaks*, not just absence). The bronze isn't a degenerate CPU; it's its own algebra, and the CPU mapping might lose content.

## Phases

### Phase 1 — Abstraction-layer-only inventory

Walk the srmech python package source. Identify each module, function, dataclass, and data structure. For each: name the primitive transformation it represents, in substrate-agnostic terms (integer-cyclic algebra when possible).

Output: `spike_24_primitive_vocabulary_findings_2026-05-15.md` Phase 1 section. Format: bullet-list per primitive with (name, what-it-does, where-it-lives, integer-algebraic form, CPU-analog if obvious).

Expected character: srmech currently is the *provenance scaffolding* (AMSC attestation, NDJSON streaming, profile loading) more than the *algebraic scaffolding*. The algebraic primitives (cyclic-group ops, period-relation factorization, pin-slot atan2, etc.) currently live mostly in plug-ins. This is itself a Phase 1 finding worth recording — the abstraction layer may need promotion-from-plug-in to be complete.

### Phase 2 — Per-plug-in instantiation matrix

For each spectral plug-in (antikythera-spectral, ephemerides-spectral, chess-spectral, doom-spectral, othello-spectral, logo), audit which Phase 1 primitives it uses, which it extends with plug-in-specific content, and which it doesn't touch. Output: a markdown matrix in the findings doc + an NDJSON tabular form.

For each "extends" cell: the plug-in-specific extension is a candidate for promotion to the abstraction layer (if substrate-agnostic) OR a genuine plug-in-bound primitive that should stay (if domain-specific). Phase 2 doesn't decide promotions; it surfaces candidates.

Plus the two CPU tables:
- **Table 2A — bronze→CPU correspondence**: primitive name, bronze instantiation, CPU operator analog, mapping fidelity (exact / lossy / leaky).
- **Table 2B — bronze-standalone**: bronze primitives where the CPU analog is *lossy* (CPU has an operator but it elides bronze algebra), *leaks* (CPU operator captures less than bronze content carries), or *absent* (no clean CPU analog at all).

### Phase 3 — Ephemerides residual analysis (full body sweep)

Real-coupling subtraction first, then partition the surviving residual into integer-algebraic / continuous-projection / unexplained.

- **3a. Abstraction-only forward-sweep.** Predict per-body motion using ONLY abstraction-layer primitives (cyclic-group period ratios, integer mesh), no ephemerides-spectral plug-in cosmos functions. Compare to DE441 truth over the design epoch. Residual = *what the abstraction layer alone cannot say.*
- **3b. Subtract abstraction-layer-predictable content.** What srmech alone can predict gets subtracted. What remains is plug-in territory.
- **3c. Enable the ephemerides-spectral plug-in and subtract real couplings.** Extract from JPL data + existing package structures:
  - Mean-motion resonances (Sol Resonance Graph; `gateway_graph_laplacian.py`)
  - Secular resonances (Laskar planetary tables; apsidal/nodal alignments)
  - Tidal couplings (`tidal_migration_data.py`; per-body Q values)
  - Gravitational harmonics J₂, J₄ (geodetic + magnetic catalog data)
  - Breathing-Laplacian state-dependent terms (Phase 9 dynamic coupling)
  - Spin-orbit resonance locks (`spin_orbit_resonance_data.py`)

  For each (body, coupling-source) pair, compute the coupling's predicted contribution analytically (fast, structural), then validate numerically (slower, catches what analytical misses). If analytical and numerical diverge for a particular body, the divergence itself is a finding worth recording.

  Subtract the real-coupling contributions from the post-3b residual.

- **3d. Partition the surviving residual.**
  - **Integer-algebraic structure** at period-ratio-derived frequencies, amplitudes that factor through ℤ/n cleanly → candidate missing primitive. Goes to primitive inventory pipeline (Phase 1 / 2 promotion candidates).
  - **Continuous-frame structure** without integer-algebraic content (irrational frequencies, transcendental basis, broadband) → projection artifact. Documented but not claimed as primitive.
  - **Unexplained content** (neither integer-algebraic nor pure projection) → the earned frontier. *"Learn how to learn what we don't know"* applies here, not earlier.

Output per tier: NDJSON record per (body, residual-component, classification).

### Phase 4 — Ephemerides handoff packet

Single notes file `spike_24_ephemerides_handoff_2026-05-15.md` for the next-door session that handles ephemerides-spectral *code* work. Contains:
- Per-body real-coupling subtractions made (so they can verify the package models these correctly; discrepancies are bugs they fix, not primitives we name).
- Surviving residuals with classification (missing-primitive candidate / projection artifact / unexplained).
- Specific code changes the next-door session would need to instantiate any primitives we name (NOT executed here — we only describe).

### Phase 5 — Notebook landing

Update `docs/srmech/srmech_research_notebook.md` with a primitive-vocabulary cross-domain section. Concrete shape: a new subsection in srmech's §3.5 cross-manifold pattern, or a new §3.6 specifically for the primitive inventory. Per `[[user_stance_kepler_shape_universal]]`, the inventory should explicitly note that Kepler-shape behavior across any plug-in domain identifies the same pin-slot-gear primitive composition.

## Bounds and disciplines

- **Single PR** for the analysis. ephemerides-spectral *code* work goes to a separate session via the Phase 4 handoff packet.
- **No ephemerides-spectral version bump** in this PR. Any code changes the analysis recommends are deferred.
- **No naming yet** — Phase 1 produces an inventory list; naming convention decisions come later.
- **No closure claim** — we're not proving the primitive vocabulary complete in this spike. The user explicitly: *"our inquiries don't necessarily terminate with a long series of 7 null results."* Open question remains open.
- **NDJSON output** for all tabular content (per `[[feedback_ndjson_over_bloated_json]]`).
- **No squash merge** when ready (per `[[feedback_no_squash_merges]]`).

## Cross-references

- PR #416 (merged `fba3065`) — pin-and-slot algebra + §11.6.17 algebraic-uniqueness synthesis
- `[[user_stance_kepler_shape_universal]]` — the universal claim that drives Spike #24
- `[[user_stance_pi_as_projection]]` — integer-cyclic upstream methodology
- `[[user_stance_fiber_as_spatially_absent_encoding]]` — algebra-upstream-projection-downstream pattern
- `[[user_stance_string_theory_instrument_first]]` — burden-of-proof discipline; counter-claims must produce instruments, not extra dimensions
- `[[feedback_orchestration_metaphor]]` — score/instrument metaphor for srmech/plug-ins
- `[[user_explanation_discipline]]` — preserve user vocabulary in derived artifacts
