# Finding 118 — "Neural network" framing is vertebrate-centric; biology has multiple computational substrates

**Status:** Framework reframe based on published cnidarian + cephalopod research
**User direction 2026-05-27:**

> "are we saying that they still create a Neural Net structure or use
> something else entirely that we should be asking? Like if it is
> different, is it more discrete-cyclic than synaptic nets?"

---

## §1 The empirical answer

**Yes — jellyfish and octopus use something fundamentally different from
synaptic-weighted hierarchical neural networks.**

### Cnidarian (jellyfish) — discrete-cyclic oscillator ensembles

Published research (PLOS One 10.1371/pone.0027201; eLife jellyfish
Aurelia 50084):

- Pacemaker neurons in rhopalia oscillate from baseline to threshold;
  firing frequency depends on input conditions
- **Pacemakers mutually connected via INHIBITORY coupling** (not
  excitatory synaptic weights)
- **Multiple pacemaker centers in multiples of FOUR** (radial symmetry)
- Box jellyfish visual processing explicitly modeled as "ensemble of
  pulsed coupled oscillators" (Pattern Recognition in Box Jellyfish
  Rhopalial Nervous System)
- Information lives in TIMING + PHASE + INHIBITORY-COUPLING-RHYTHM, not
  in synaptic weights

This is **Class I (cyclic / modular arithmetic) embodied as primary
computational substrate**, not as an overlay rhythm on top of synaptic
networks.

The user's hypothesis is empirically supported: jellies are more
discrete-cyclic than synaptic.

### Cephalopod (octopus) — distributed-discrete agent coordination

Published research (Nature Communications s41467-024-55475-5;
bioRxiv 2024.09.13.612676):

- Each arm has its own ganglia — "brain-in-miniature with regional
  specializations, neurotransmitter systems, and computational
  architecture"
- 2024 computational modeling: "distributed but discrete architecture
  for sensing"
- Per-node computational units communicating via narrow-bandwidth
  links to central brain
- 3/5 of total neurons in arms, not central

This is **Class M (HDC bind across distributed agents) + Class K
(pin-slot / asymptotic-DoF for arm-coordination)** — different from
both vertebrate hierarchy and jellyfish oscillator ensemble.

### Vertebrate brain — synaptic-weighted hierarchical

Vertebrate cortex with layered processing is **Class L (graph
Laplacian) embodied via synaptic networks**.

Our entire analysis arc through R-RBS-LM-92 implicitly assumed THIS
substrate.

---

## §2 The framework move

The 14-class A-N operators are an **abstract universal algebra** of
computational primitives. Different biology embodies different
operator-subsets:

| Substrate | Primary operators | Example biology |
|---|---|---|
| Synaptic-weighted hierarchical | **L** (graph Laplacian) + **M** (HDC bind) | Vertebrate cortex; primate; cetacean |
| Discrete-cyclic oscillator | **I** (cyclic) + **K** (phase boundary) | Cnidarian nerve nets; jellyfish |
| Distributed agent-coordination | **M** (HDC bind) + **K** (pin-slot) | Octopus arms |
| Chemical-gradient | **J** (factor/divisor anchors) + **C** (chirality) | Slime mold; plant signaling |
| Gene-regulatory | **D** (pattern match) + **E** (catalog) | Unicellular cognition |

Each biology achieves the SAME functional partitions
(declarative/procedural/social/self per Finding 115) using DIFFERENT
operator-emphases.

**The "neural network" framing we've used throughout this arc is
vertebrate-centric.** It assumes synaptic-weighted hierarchical coupling.
Biology has discovered multiple computational substrates; "NN" is one.

---

## §3 What this reframes

### Finding 115 (cross-species partitions) refined

Functional partitions converge across species (declarative / procedural
/ social / self all appear in cetacean / primate / octopus). But the
COMPUTATIONAL SUBSTRATE varies:
- Cetacean: synaptic + spindle cells for social
- Octopus: synaptic + distributed-agent for procedural; central for social/declarative
- Jellyfish: oscillator-ensemble — DOES it have "declarative" knowledge?
  Or only procedural-pattern-recognition?

This nuances the cross-species partition claim. Functional partitions
may be UNIVERSAL at the operator-output level, but they don't all
require the SAME computational substrate to instantiate.

A jellyfish achieves "pattern recognition" (procedural) via coupled
oscillators rather than via synaptic weights. The output is comparable;
the substrate is fundamentally different.

### Methodology implications — our spectral analysis is calibrated to ONE substrate

Throughout R-RBS-LM-85 through 94, we used static cooccurrence + PPMI
+ graph Laplacian + eigendecomp. This methodology is **calibrated to
synaptic-NN-style architecture** — it detects coupling-weight structure
in cooccurrence matrices.

For other substrates:
- **Jellies**: would need PHASE/TIMING coupling analysis (Fourier on
  pulse sequences; phase-coupling between pacemakers; coupled-oscillator
  reduced models)
- **Octopus**: would need DISTRIBUTED-AGENT coordination metrics
  (mutual information across per-arm states; bandwidth-limited
  cross-arm channels)
- **Plants/slime mold**: would need GRADIENT analysis (chemical
  concentration fields; reaction-diffusion dynamics)
- **Gene-regulatory**: would need TOPOLOGICAL analysis of regulatory
  graphs

Our methodology is good for ONE substrate. The framework is broader.

### "NN-storage architecture" terminology — replace with "computational substrate"

Going forward, the language matters. Specific:
- "NN-storage architecture" → "computational substrate"
- "Populated NN" → "populated computational structure"
- "Synaptic coupling" → "coupling" (with substrate qualifier when
  needed)

This is per `[[feedback_no_privileged_primitive_classes]]` discipline
applied at the substrate level — don't privilege one substrate type as
THE neural model.

---

## §4 What this validates from earlier framework

### User's prior framework moves

- "We cannot privilege with human only perspectives" — confirmed at
  even broader scope; can't privilege vertebrate perspectives either
- "Knowledge partitions are the purpose" — different substrates achieve
  the same partition function; the purpose is substrate-agnostic
- "Specialized domains emerge with strong cross coupling that we
  pretend not to see" — applies across substrates; cross-coupling is
  universal even when substrate-mechanism differs
- "Trailing-3 are binding doing moving descriptions" — these are
  operations that any substrate must support, regardless of mechanism

### The 14-class A-N partition strengthened

The partition is more clearly an ABSTRACT ALGEBRA than a biology-
specific architecture. It's the operator set that any computational
substrate draws from to do its work. Different substrates emphasize
different subsets; the universal partition encompasses all of them.

This is consistent with the user's `[[project_a_n_operators_are_harmonic_objects_themselves]]` — operators are harmonic objects in an abstract
algebra; biology is one substrate where they're embodied.

---

## §5 The discrete-cyclic question generalized

User asked: "is it more discrete-cyclic than synaptic nets?"

The answer for jellies is YES. But this prompts a deeper question:
**ARE different mathematical structures (continuous-synaptic vs
discrete-cyclic vs distributed-agent vs gradient-flow) themselves the
14 A-N classes in mathematical form?**

If yes, then biology is just one application surface of the A-N
operators. The operators exist mathematically; biology evolved
specific instantiations.

This connects to:
- Antikythera (R30 walking-path): bronze gears = discrete-cyclic
  embodiment of Class I + Class C
- Quantum mechanics (srmech.qm): linear operators on Hilbert space =
  Class L embodiment
- Chess (chess-maths): discrete state lattice = Class K + Class M
  embodiment
- Cnidarian: pacemaker ensemble = Class I + Class K embodiment

All these are different substrate-embodiments of the same abstract
A-N operator set.

---

## §6 What this does NOT claim

Per MFO §VII.6.20:

- Cnidarian nervous systems are EXACTLY Class I+K (likely closer to
  the truth than synaptic-NN framing; but specific operator
  identification needs more careful work)
- All biology must use some subset of the 14 A-N operators (we don't
  know this; it's a framework prediction, not a substantiated claim)
- "Vertebrate-centric" is wrong to use (it's *one* substrate; using
  it is fine when accurate to scope; the issue is generalizing it as
  universal)
- The 14-class partition explains ALL biological computation (it's an
  abstract framework that's testable against biology; not yet shown
  to be exhaustive)

---

## §7 What's still open

### Test the substrate-variety claim empirically

Can we:
1. Take cnidarian behavioral data (if available) and analyze with
   COUPLED-OSCILLATOR methodology rather than cooccurrence
2. Take octopus arm coordination data and analyze with DISTRIBUTED-
   AGENT methodology
3. Compare the operator-signatures across substrates

If the same A-N operators emerge with different substrate-appropriate
methodologies — strong validation.

If methodologies don't cross over cleanly — the operator-universal
claim is weaker than the framework hopes.

### Connect to R30 walking-path

The R30 substrate-native maths arc (PR #680) is examining 1:3:7:3
embodiment in Antikythera. The cnidarian/jellyfish discrete-cyclic
substrate is potentially a BIOLOGICAL parallel — both are discrete-
cyclic instantiations of the same A-N operator subset.

Worth checking if R30 framework predicts cnidarian substrate as a
parallel to Antikythera.

---

*Articulated 2026-05-27 per user direction. PR #687 STAYS DRAFT.*

*Substrate-variety is real. "NN" is vertebrate-centric. Biology has
multiple computational substrates, each embodying different A-N
operator subsets. The 14-class partition is the abstract algebra;
biology + mechanism + culture are application surfaces.*
