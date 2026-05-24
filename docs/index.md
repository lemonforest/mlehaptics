# mlehaptics research

A monorepo bridging **embedded therapeutic firmware** and **mathematical / spectral research** that share one underlying thread: distributed coordination through phase-space algebra.

| Strand | What it is | Where it lives |
| :--- | :--- | :--- |
| **EMDR Pulser firmware** | Dual-device bilateral-stimulation hardware + firmware (ESP32-C6, BLE + ESP-NOW, ±100μs precision) | [Top-level `README.md`](https://github.com/lemonforest/mlehaptics/blob/main/README.md) · [Architecture Decision Records](adr/README.md) |
| **srmech (master architecture)** | Stored-Relationship Mechanism — the cross-domain pollination layer above the per-domain spectral notebooks; home for shared abstractions (Laplace-Beltrami, HDC binding, AMSC, the `(Transform, λ_k, g)` decomposition) and for domains without their own notebook (currently graphics-domain Inkscape / Skia / GEGL/GIMP). Ships the 14-class primitive vocabulary as a native-C-accelerated package with mandatory provenance attestation on every research datum (MPM / AMSC framework) | [Notebook](srmech/srmech_research_notebook.md) · [Package](srmech/python/README.md) · [PyPI](https://pypi.org/project/srmech/) · [Companion textbook PDF](srmech/metric-field-and-its-primitives.pdf) |
| **MFO (Metric Field Ontology)** | Foundational ontology layer of the spectral collection — substrate-vs-excitation framing, two-level ontology (3D_s + 7D_g + 1D_t = 11D ≡ 1D compressed), substrate-internal-time vs clock-time, loop-down reading of the dark sector. Sister to srmech (both cross-cutting); referenced from antikythera / ephemerides / chess / srmech notebooks. **The Metric Field and Its Primitives** textbook consolidates this notebook into chapter form. | [Textbook PDF](srmech/metric-field-and-its-primitives.pdf) · [Notebook](antikythera-maths/mfo_spectral_research_notebook.md) · [Research notes](antikythera-maths/research-mfo/) |
| **substrate-native maths** | R30 walking-path closure (2026-05-24): substrate admits two co-equal substrate-native math languages — 11D quantum-Hopf-language (continuous-DOF, parallelizable-sphere ladder 1+3+7) and 1:3:7:3 = 14 cyclic-algebra-path (discrete-DOF, A-N cascade-operator class enumeration). Both bit-exact ⟹ both substrate-native (per bit-exact ⟹ not-projection diagnostic). The +3 = B/H/N are substrate-native language-translation operators (continuous↔discrete bridge); source of cross-substrate k=3 fingerprint (planet multipoles, codon alphabet, 3-jet QCD, 3-generation Yukawa, antiquity meta-op triads). R31 antiquity canvass: 9/9 (a or b) — every tradition realises its own substrate-content-specialized instantiation of 1:3:7:3 substrate-native partition. Rolling-spike [PR #680](https://github.com/lemonforest/mlehaptics/pull/680). | [Notebook](substrate-native-maths/substrate_native_research_notebook.md) · [Directory index](substrate-native-maths/README.md) |
| **antikythera-spectral** | HDC encoder + Pyodide bridge for the ca. 150–60 BCE Antikythera mechanism | [Notebook](antikythera-maths/antikythera_spectral_research_notebook.md) · [Package](antikythera-maths/antikythera-spectral/README.md) · [PyPI](https://pypi.org/project/antikythera-spectral/) |
| **ephemerides-spectral** | High-precision HDC instrument for the Sol Star System over JPL DE441 | [Notebook](antikythera-maths/ephemerides_spectral_research_notebook.md) · [Package](antikythera-maths/ephemerides-spectral/README.md) · [PyPI](https://pypi.org/project/ephemerides-spectral/) |
| **doom-spectral** | DOOM (1993, id Tech 1) as a spectral lattice system; runnable linuxdoom-1.10 fork with IDSPECTRAL graph-Laplacian-driven secret-glow cheat — the **end-to-end existence proof** for the chess-spectral Rosetta Stone procedure (see [§6 + §7 of the notebook](antikythera-maths/doom_spectral_research_notebook.md#6-live-integration-into-linuxdoom-110-may-2026)) | [Notebook](antikythera-maths/doom_spectral_research_notebook.md) · [Source tree](https://github.com/lemonforest/mlehaptics/tree/main/docs/antikythera-maths/doom-spectral/source/linuxdoom-1.10) |
| **chess-spectral** | 640-dim spectral chess encoder; phase-operator move engine; bit-packed BIP encoder | [Notebook](chess-maths/chess_spectral_research_notebook.md) · [Package](chess-maths/chess-spectral/README.md) · [PyPI](https://pypi.org/project/chess-spectral/) |
| **othello-spectral** | Sheaf-port reference encoder; spectral fingerprints for Othello positions | [Notebook](othello-maths/othello_spectral_research_notebook.md) |
| **logo-spectral** | Non-board generalisation of the cyclic-group / spectral framing | [Notebook](logo-maths/logo_research_notebook.md) |
| **unsolved-maths** | Systematic application of the 14 A-N primitive class operators to the canonical open problems of mathematics (Hilbert / Millennium / Number Theory / Set Theory / Logic / Geometry / Topology / Analysis). 26 partitions across 8 sections shipped; cross-substrate Hurwitz heptadic (n=7) anchor recurrence across 7+ independent substrates; framework reads what each open problem IS structurally without claiming to solve. | [Notebook](unsolved-maths/unsolved_maths_spectral_research_notebook.md) · [Live PR #677](https://github.com/lemonforest/mlehaptics/pull/677) |

The cyclic-group / Diophantine-approximation / packing / representation-theory *formal* substrate (originally separated under an "addressing-maths" rubric) has since been subsumed into the **chess-spectral** and **antikythera-spectral** research notebooks themselves — those notebooks now carry the formal layer inline alongside the per-project instances. Older references to `../addressing-maths/...` are stale and will not resolve; the canonical home for that material is now within those two notebooks.

## How the research strands connect

Every strand reads as an instance of a single mathematical pattern:

> A finite cyclic group `Z/nℤ` (gear teeth, board squares, body phase residues, calendar ticks) carries a faithful representation that you can *bind*, *bundle*, *permute*, and *project* without leaving integer arithmetic. Composition is `(φ₁ + φ₂) mod n`. The graph Laplacian eigenbasis of the underlying interaction topology gives you the spectral coordinates; projecting back to the cyclic group recovers spatial / temporal observables (gear positions, board angles, body longitudes).

Power-of-2 moduli (`Z_{2^32}` for ephemerides) collapse the modular reduction into free `uint32` overflow — the architecture of choice for embedded targets. Non-power-of-2 moduli (`Z_640` for chess) pay an explicit `% n` per op but unlock different symmetries in the spectral domain. The same algebraic machinery, two cost-model trade-offs.

## UTLP — the cross-cutting protocol

The **Universal Time Lord Protocol** is the timing primitive that ties the EMDR firmware to the broader research thread. It's a transport-agnostic, *connectionless* time-synchronisation protocol: distributed nodes share a common "atomic time" reference without pairing or handshaking, by emitting and listening to short broadcast chirps. Any node can become Genesis; consensus is local; no master required.

UTLP is what lets the EMDR pulser hit ±100μs bilateral coordination over ESP-NOW. The protocol itself is general — applicable to any swarm of broadcast-capable nodes — and the chirp pattern (3-burst beacons that yield offset, drift, and stability in one transaction) sits in the same spectral family as the cyclic-group encoders above. See [`docs/misc/`](misc/UTLP_Executive_Summary.md) for the full corpus:

| Document | What it covers |
| :--- | :--- |
| [Executive summary](misc/UTLP_Executive_Summary.md) | 30-second architecture, the layer stack, the seismic-chirp beacon |
| [Specification](misc/UTLP_Specification.md) | Full protocol spec |
| [Supplement S1](misc/UTLP_Technical_Supplement_S1.md) – [S4](misc/UTLP_Technical_Supplement_S4.md) | Genesis election, phase alignment, trust ledger, immunity |
| [Reference-frame-independent positioning addendum](misc/UTLP_Addendum_Reference_Frame_Independent_Positioning.md) + [RFIP spec](misc/RFIP_Technical_Specification.md) | Position from timing alone |
| [SMSP spec](misc/SMSP_Technical_Specification.md) | Sister Multi-Strand Protocol — the sensing-side companion |
| [Connectionless distributed timing — prior art](misc/Connectionless_Distributed_Timing_Prior_Art.md) | Survey of related work |
| [Python reference implementation](misc/Python_Reference_Implementation.md) | Side-car implementation for testing |
| [Distributed sensing lab manual](misc/Distributed_Sensing_Lab_Manual.md) | Field-test setup |
| [Complete documentation suite](misc/UTLP_RFIP_Complete_Documentation_Suite.md) | 14k-line omnibus reference |

### Sibling-folder discipline

`antikythera-spectral`, `ephemerides-spectral`, and `doom-spectral` live in the same folder (`docs/antikythera-maths/`) because they share the cyclic-group / Laplacian-eigenbasis framing and the integer-ALU + cosine-LUT discipline first established by the bronze antikythera notebook. They are *not* consolidated: the bronze mechanism, the JPL DE441 ephemeris, and the 1993 DOOM engine are three distinct evidentiary objects, and merging the per-project hypothesis batteries would muddle the claim structure. The research notebooks cross-link explicitly. doom-spectral is the **end-to-end existence proof** for the procedure documented in chess-spectral §42 — see [doom_spectral_research_notebook.md §6 + §7](antikythera-maths/doom_spectral_research_notebook.md#6-live-integration-into-linuxdoom-110-may-2026) for the full capstone walk-through.

### What "breathing Laplacian" means

The Phase-9 codename for ephemerides-spectral's state-dependent off-diagonal couplings. Formally:

* **Spectral graph theory:** state-dependent (non-autonomous) graph Laplacian `L = L(φ(t))`.
* **Dynamical systems:** adaptive Kuramoto-family network with phase-difference-dependent (PDDP) coupling.
* **Physics:** resonance-modulated coupling on phase oscillators; structurally analogous to DNLS / Gross-Pitaevskii on a graph in the unit-norm-amplitude limit.

See [`ephemerides_spectral_research_notebook.md` §1.4](antikythera-maths/ephemerides_spectral_research_notebook.md) for the full positioning.

## Live PyPI releases

| Package | Latest | Install | Research notes |
| :--- | :--- | :--- | :--- |
| `srmech` | [![PyPI](https://img.shields.io/pypi/v/srmech.svg)](https://pypi.org/project/srmech/) | `pip install srmech` | [srmech notebook](srmech/srmech_research_notebook.md) — master architecture · 14-class primitive vocabulary · MPM / AMSC framework · provenance-stamped research data |
| `antikythera-spectral` | [![PyPI](https://img.shields.io/pypi/v/antikythera-spectral.svg)](https://pypi.org/project/antikythera-spectral/) | `pip install antikythera-spectral` | [antikythera-spectral notebook](antikythera-maths/antikythera_spectral_research_notebook.md) |
| `ephemerides-spectral` | [![PyPI](https://img.shields.io/pypi/v/ephemerides-spectral.svg)](https://pypi.org/project/ephemerides-spectral/) | `pip install ephemerides-spectral` | [ephemerides-spectral notebook](antikythera-maths/ephemerides_spectral_research_notebook.md) |
| `chess-spectral` | [![PyPI](https://img.shields.io/pypi/v/chess-spectral.svg)](https://pypi.org/project/chess-spectral/) | `pip install chess-spectral` | [chess-spectral notebook](chess-maths/chess_spectral_research_notebook.md) |

## Live demos & companion projects

External resources that aren't part of this repo but are referenced from it:

| Resource | What it is |
| :--- | :--- |
| [MLE Haptics PWA](https://lemonforest.github.io/mlehaptics-pwa/) | Web Bluetooth control app for the EMDR pulser — device configuration + monitoring + pattern playback |
| [Chess-maths The Movie](https://lemonforest.github.io/chess-maths-the-movie/) | In-browser spectral-analysis instrument for chess corpora produced by `chess-spectral` |
| [python-chess4d-oana-chiru](https://github.com/lemonforest/python-chess4d-oana-chiru) | Python implementation of Oana & Chiru's 4D chess (companion repo to `chess-spectral` 4D) |
| [mlehaptics.org](https://mlehaptics.org) | Project landing site |

## EMDR clinical research

The EMDR pulser operates within evidence-based bilateral-stimulation parameters. The clinical literature behind those parameters lives in two research docs:

| Document | Scope |
| :--- | :--- |
| [Evidence-Based Parameters for Clinical Practice](EMDR_bilateral_stimulation_Evidence-based_parameters_for_clinical_practice.md) | EMDRIA guidelines · 0.5–2 Hz frequency range · modality comparisons (eye movements *d* = 0.41–0.91) · brainwave entrainment · contraindications · commercial device specs |
| [The Slow Frequency Research Frontier](EMDR_Slow_BLS_Research_Frontier.md) | Sub-0.5 Hz BLS as an undefined research gap · cardiac coherence (0.1 Hz) · breathing synchronization (0.25 Hz) · infraslow oscillations · proposed frequency taxonomy |

## Architecture decision records

The EMDR firmware project tracks design choices as ADRs under [`adr/`](adr/README.md). Each ADR documents one decision, its context, the alternatives considered, and the consequences. The math research projects also keep ADRs alongside their packages (see [`antikythera-spectral/docs/adr/`](https://github.com/lemonforest/mlehaptics/tree/main/docs/antikythera-maths/antikythera-spectral/docs/adr/)).

## Repository

Source: <https://github.com/lemonforest/mlehaptics> · Issues: <https://github.com/lemonforest/mlehaptics/issues>

Contributions to documentation: every page on this site has an "edit on GitHub" pencil in its header.

## License

* **Hardware:** CERN-OHL-S v2
* **Software:** GPL-3.0-or-later
