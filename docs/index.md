# mlehaptics research

A monorepo bridging **embedded therapeutic firmware** and **mathematical / spectral research** that share one underlying thread: distributed coordination through phase-space algebra.

| Strand | What it is | Where it lives |
| :--- | :--- | :--- |
| **EMDR Pulser firmware** | Dual-device bilateral-stimulation hardware + firmware (ESP32-C6, BLE + ESP-NOW, ±100μs precision) | [Top-level `README.md`](https://github.com/lemonforest/mlehaptics/blob/main/README.md) · [Architecture Decision Records](adr/README.md) |
| **antikythera-spectral** | HDC encoder + Pyodide bridge for the ca. 150–60 BCE Antikythera mechanism | [Notebook](antikythera-maths/antikythera_spectral_research_notebook.md) · [Package](antikythera-maths/antikythera-spectral/README.md) · [PyPI](https://pypi.org/project/antikythera-spectral/) |
| **ephemerides-spectral** | High-precision HDC instrument for the Sol Star System over JPL DE441 | [Notebook](antikythera-maths/ephemerides_spectral_research_notebook.md) · [Package](antikythera-maths/ephemerides-spectral/README.md) · [PyPI](https://pypi.org/project/ephemerides-spectral/) |
| **chess-spectral** | 640-dim spectral chess encoder; phase-operator move engine; bit-packed BIP encoder | [Notebook](chess-maths/chess_spectral_research_notebook.md) · [Package](chess-maths/chess-spectral/README.md) · [PyPI](https://pypi.org/project/chess-spectral/) |
| **othello-spectral** | Sheaf-port reference encoder; spectral fingerprints for Othello positions | [Notebook](othello-maths/othello_spectral_research_notebook.md) |
| **logo-spectral** | Non-board generalisation of the cyclic-group / spectral framing | [Notebook](logo-maths/logo_research_notebook.md) |

The `addressing-maths` substrate referenced from several of these notebooks (Diophantine approximation, packing, cyclic-group representation theory) is currently maintained in a separate repo; it is the *formal* layer the research notebooks here read as instances. References to `../addressing-maths/...` in the notebooks below will not resolve on this site.

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

`antikythera-spectral` and `ephemerides-spectral` live in the same folder (`docs/antikythera-maths/`) because they share the cyclic-group / Laplacian-eigenbasis framing and the Pyodide bridge contract. They are *not* consolidated: the bronze mechanism and the JPL DE441 ephemeris are separate evidentiary objects, and merging the per-project hypothesis batteries would muddle the claim structure. The research notebooks cross-link explicitly.

### What "breathing Laplacian" means

The Phase-9 codename for ephemerides-spectral's state-dependent off-diagonal couplings. Formally:

* **Spectral graph theory:** state-dependent (non-autonomous) graph Laplacian `L = L(φ(t))`.
* **Dynamical systems:** adaptive Kuramoto-family network with phase-difference-dependent (PDDP) coupling.
* **Physics:** resonance-modulated coupling on phase oscillators; structurally analogous to DNLS / Gross-Pitaevskii on a graph in the unit-norm-amplitude limit.

See [`ephemerides_spectral_research_notebook.md` §1.4](antikythera-maths/ephemerides_spectral_research_notebook.md) for the full positioning.

## Live PyPI releases

| Package | Latest | Install |
| :--- | :--- | :--- |
| `antikythera-spectral` | [![PyPI](https://img.shields.io/pypi/v/antikythera-spectral.svg)](https://pypi.org/project/antikythera-spectral/) | `pip install antikythera-spectral` |
| `ephemerides-spectral` | [![PyPI](https://img.shields.io/pypi/v/ephemerides-spectral.svg)](https://pypi.org/project/ephemerides-spectral/) | `pip install ephemerides-spectral` |
| `chess-spectral` | [![PyPI](https://img.shields.io/pypi/v/chess-spectral.svg)](https://pypi.org/project/chess-spectral/) | `pip install chess-spectral` |

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
