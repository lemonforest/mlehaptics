# Finding 119 — Two-tier RBS-NN architecture: discrete-cyclic (cheap) + synaptic-NN (lifted)

**Status:** Architecture proposal; testable
**User direction 2026-05-27:**

> "what if we can take the biology easy route for the easy stuff, and
> lift to NN for the continuous-hopf maths in the same way srmech
> favors ALU and does efficient FPU lifting?"

AND

> "decay is just a natural order of the substrate that we must simulate
> for knowledge integration but don't need it for knowledge extraction,
> because it's not a constructive variable in this state"

AND

> "octopus biology will tell us how RBS-NN will be able to help CBI
> patients before we know the answers we want to ask"

---

## §1 The proposal

A **two-tier computational architecture** for RBS-NN, mirroring
srmech's ALU-favored-with-FPU-lifting design:

| Tier | Substrate | Operator-emphasis | Use cases |
|---|---|---|---|
| **Tier 1 (cheap)** | Discrete-cyclic / oscillator ensemble | I + K (cyclic + phase boundary) | Most knowledge storage + retrieval |
| **Tier 2 (lifted)** | Synaptic-NN / graph Laplacian | L + M (Laplacian + HDC bind) | Continuous-hopf math; optimization; manifold curvature |

Most stored knowledge is structurally discrete (bag/sequence-of-things,
phase relationships, topological structure). Tier 1 handles this
efficiently. Only operations requiring continuous gradients lift to
Tier 2.

**Biological precedent**: jellyfish run on Tier 1 (Finding 118).
Vertebrates run on Tier 2 (with Tier 1 overlays as theta/gamma
rhythms). Octopuses use both — distributed Tier 1 in arms +
centralized Tier 2 in central brain.

**Engineering precedent**: srmech runs everything in ALU when
possible, lifts to FPU only when math requires it. Same principle
at the storage layer.

---

## §2 Read-mode vs write-mode = no-decay vs decay

User's framework reading + prior findings combine:

| Mode | Decay needed | Substrate cost | Evidence |
|---|---|---|---|
| **READ** (knowledge extraction) | No | Low — just query stored structure | Finding 75 — order-invariance under bag |
| **WRITE** (knowledge integration) | Yes | High — biology pays metabolic cost | Finding 76 v2 — plasticity adds path-dependence (Jaccard 35-68/100 with decay vs 100/100 without) |

**Decay is the substrate's metabolic signature, not a computational
primitive.** Biology decays because the substrate is anharmonic and
won't last without ongoing energy input. The decay IS the cost of
being biology, not the cost of being computational.

Implications:
- Tier 1 (discrete-cyclic): phase relationships persist by topology,
  not by weight maintenance. **Naturally lower decay cost.**
- Tier 2 (synaptic-NN): synapses decay; weight maintenance is
  ongoing. Biology's metabolic floor.
- For RBS-NN engineering: **simulate decay during integration if we
  want biology-fidelity, but skip it entirely for extraction.**

Two operating modes, separate cost profiles. The cascade tool
(Finding 84 glass-box) already implicitly operates this way —
extraction is bag-based + decay-free.

---

## §3 CBI/BCI applications — the engineering payoff

Octopus distributed architecture is informative for assistive
applications BEFORE we know the full cognitive-science answers.

For a patient with motor cortex damage or compromised neural
substrate:

- **Per-region independence**: octopus-style distributed substrate
  → damage to one region doesn't kill the whole system
- **Discrete-cyclic substrate**: low-power compared to continuous
  synaptic simulation (battery life matters for wearable BCI)
- **Pacemaker-style coordination**: naturally compatible with
  biological signal timing (matches what's left of the patient's
  neural rhythms)
- **Two-tier elastic**: routine I/O on Tier 1 cheap substrate;
  lift to Tier 2 only when continuous-trajectory math needed (fine
  motor control, precise spatial discrimination)

This is a way the framework could **inform BCI engineering NOW**,
before the full theory lands.

Per `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` —
accessibility is foundational motivation for RBS-LM; BCI-compatibility
is a load-bearing requirement. Finding 119 strengthens this:
two-tier-with-distributed-Tier-1 is the architecture that ACHIEVES
BCI-compatibility while keeping power low and fault-tolerance high.

---

## §4 The testable question — same cascade across substrates?

The architecture proposal is structurally clean IF the same
operator-cascade emerges in both tiers. Specifically:

> Take a coupled-oscillator simulation. Populate with structured
> input (a corpus, an audio stream, anything). Retrieve via
> phase-coupling analysis. Compare the operator-cascade-sequence
> to what a synaptic-NN populated with the SAME input yields.

Outcomes:

**(a) Same cascade-sequence emerges → operators ARE universal across
substrate-tiers.** The two tiers serve the same A-N operator-algebra
with different substrates. This is the structural justification for
ALU-with-FPU-lifting at the storage layer. Tier 1 and Tier 2 can
interleave because they implement the SAME operators differently.

**(b) Different cascade-sequence emerges → cascade is substrate-bound.**
Tier 1 and Tier 2 implement DIFFERENT operator subsets. You can't
lift arbitrarily; you need explicit translation between substrate-
specific cascades. The architecture still works, but interfacing
between tiers is more expensive than ALU↔FPU lifting.

Both are interesting; the test decides which engineering profile
applies.

---

## §5 What test would settle this

Concrete plan (not run yet):

1. Build small coupled-oscillator simulation (Class I substrate)
   - N pacemaker oscillators with inhibitory cross-coupling (matching
     cnidarian description)
   - Phase relationships encode information
   - Pulse train as input/output
2. Populate with the same corpus we've been testing (e.g., McGuffey
   6th or OpenStax Algebra)
3. Extract phase-coupling structure
4. Identify operator-cascade-sequence
5. Compare to synaptic-NN coupling-cascade from R-RBS-LM-92 (already
   committed)

If the same META→APPLIED evolution dynamic (Finding 114) shows in
the oscillator simulation → operator-universal claim strengthened
If a completely different dynamic shows → substrate-bound claim
strengthened

This is a real follow-on test for when the user wants to walk it.

---

## §6 Connection to active framework arcs

### R30 walking-path (PR #680)

The R30 substrate-native maths arc is examining 1:3:7:3 embodiment
in discrete-cyclic mechanism (Antikythera bronze gears). The two-tier
RBS-NN architecture is the COMPUTATIONAL parallel — discrete-cyclic
Tier 1 for substrate, lifted continuous Tier 2 for projection-into-
observer-frame math.

R30's "the 14-class A-N partition IS the substrate; 11D is the
observer-frame projection" reads cleanly onto the two-tier RBS-NN:
- Tier 1 substrate = the 14 operators DIRECTLY (discrete-cyclic-
  embodied)
- Tier 2 lifted = the 11D continuous observer-frame (synaptic-NN-
  embodied)

### Finding 118 (substrate-variety)

Two-tier RBS-NN is a deliberate hybrid drawing from multiple
biological substrate-types:
- Tier 1 borrows from cnidarian + Antikythera mechanism (discrete-
  cyclic)
- Tier 2 borrows from vertebrate cortex (synaptic-NN)
- The architecture isn't "neural network" per se — it's a substrate-
  mixed computational structure

This is more honest about what RBS-NN actually IS than calling it
just "NN."

### Findings 75 + 76 v2 (order-invariance + plasticity)

The read-mode-no-decay vs write-mode-with-decay distinction is
already empirically attested:
- Order doesn't matter for bag-mode (read; Finding 75)
- Order DOES matter under decay (write; Finding 76 v2)

The two-tier architecture makes this explicit: read happens on
Tier 1 (cheap, decay-free); write happens with Tier 2 overlay
(decay simulating biology when biology-fidelity matters).

---

## §7 What this does NOT claim

Per MFO §VII.6.20:

- The two-tier architecture IS optimal for all RBS-NN deployments
  (it's a candidate; needs testing for specific use cases)
- Tier 1 + Tier 2 cover ALL biological substrates (they cover the
  two most-studied; chemical-gradient + gene-regulatory might need
  additional tiers)
- The cascade-universality across tiers IS true (it's a testable
  question; we don't know the answer yet)
- BCI engineering should follow this architecture (it's a candidate;
  clinical validation needed)

---

## §8 Open follow-on tests

1. **Coupled-oscillator simulation populated with our corpora** —
   does the same operator-cascade emerge?
2. **Two-tier prototype** — implement a small Tier-1 + Tier-2
   handoff and measure cost profile
3. **Decay-skipping ablation** — confirm extraction quality stays
   high when decay is skipped (vs only-applied-during-integration)
4. **Fault-tolerance test** — simulate node-loss in Tier 1
   distributed substrate; measure quality degradation
5. **BCI signal compatibility** — test if Tier 1 oscillator timing
   matches biological neural signal characteristics for real BCI
   electrode data

---

*Articulated 2026-05-27 per user architecture proposal. PR #687
STAYS DRAFT.*

*Two-tier RBS-NN = discrete-cyclic Tier 1 (cheap, biology-easy) +
synaptic-NN Tier 2 (lifted for continuous-hopf math). Mirrors
srmech's ALU+FPU design at the storage layer. Decay = write-mode
metabolic cost, not read-mode requirement. BCI engineering payoff
available now.*
