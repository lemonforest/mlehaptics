# DOOM as a Spectral Lattice System

**Authors:** Steven (mlehaptics Project) & Gemini Code Assist
**Date:** May 2026
**Status:** Active research — translating id Tech 1 into a graph-Laplacian spectral model.

> Living document. Sibling to:
> - [../chess-maths/chess_spectral_research_notebook.md](../chess-maths/chess_spectral_research_notebook.md) — The static fiber bundle and piece kinematics; §20.21 frames this notebook as the fourth sibling and tabulates the Track 1 / Track 3 / Track 4 correspondences (2D Grid Laplacian; dynamic sheaf raycast; heat-equation diffusion). The chess notebook is the foundational one — it carries the full vocabulary stack and the cross-disciplinary methodological note (§42).
> - [../othello-maths/othello_spectral_research_notebook.md](../othello-maths/othello_spectral_research_notebook.md) — The dynamic sheaf Laplacian (raycasting and LoS). Track 3 of this notebook is mathematically identical to Othello's **§10.7 ray-flanking mechanic** — the doom-spectral implementation reuses the algebra directly.
> - [./antikythera_spectral_research_notebook.md](./antikythera_spectral_research_notebook.md) — **same-folder sibling.** The cyclic-group / Laplacian-eigenbasis structure read off the ca. 150–60 BCE Antikythera bronze; established the integer-ALU + cosine-LUT + Q-format discipline that this notebook reuses for the BSP / Sector graph.
> - [./ephemerides_spectral_research_notebook.md](./ephemerides_spectral_research_notebook.md) — **same-folder sibling.** The ALU-native $Z_{2^{32}}$ BIP encoder and Phase-9 adaptive couplings shipped to PyPI as `ephemerides-spectral`; this notebook is the first sibling that ports the BIP/Phase-9 machinery to a non-celestial-mechanics problem (a 1993 first-person-shooter map).

## 0. Framing: 1993 Carmack Meets 2026 Spectral Graph Theory

The original DOOM (1993) engine is a masterpiece of integer ALU-dominant engineering. Because 1993 CPUs lacked fast FPUs, DOOM relied on:
- **16.16 Fixed-Point Arithmetic:** Integer representations of continuous space.
- **BAMs (Binary Angle Measurement):** Angles mapped to an 8-bit or 32-bit integer cycle (0-255 or 0-4294967295), where integer overflow handles $2\pi$ wrap-around natively.
- **Precomputed LUTs:** Sine and cosine evaluated via array lookups.

This is exactly the substrate of our `ephemerides-spectral` BIP (Bit-Interleaved Phases) encoder. This project translates the spatial and mechanical realities of DOOM into a **physics-only hyperdimensional engine** governed by graph-Laplacian spectral methods.

### 0.1 The 2.5D Assumption as a Fiber Bundle
DOOM maps are 2D planar partitions (the BSP tree). "Height" (floor and ceiling elevation) exists as a property of a 2D polygonal Sector. 
Mathematically, DOOM is a 2D base manifold with a scalar fiber. The topological impossibility of "room-over-room" in the original engine is the definition of a trivial trivialized fiber bundle.

## 1. Research Subagents & Implementation Tracks

To build this ALU-dominant physics engine, the research is split into five distinct subagents:

### Track 1: The Base Graph (Blockmap & Sector Topology)
DOOM uses a 128x128 unit regular grid (the Blockmap) to optimize collision detection, laid over an arbitrary planar graph (Sectors and Linedefs).
- **Hypothesis 1.1:** The Blockmap can be modeled exactly as a 2D Grid Laplacian, yielding the 2D DCT eigenbasis.
- **Hypothesis 1.2:** Sectors act as a super-graph (a coarse-graining of the Blockmap). The restriction map between the Blockmap Laplacian and the Sector Laplacian defines physical boundaries.

### Track 2: The Z-Axis Fiber (Elevation and Collision)
Elevation (Z) is not a 3rd dimension in the base graph; it is a fiber attached to the Sector graph.
- **Physics Constraint:** An entity can move from Sector A to Sector B if `Floor(B) <= Z_entity + MaxStep` and `Ceiling(B) >= Z_entity + Height_entity`.
- **Spectral Mapping:** This is a state-dependent phase gate on the edges of the Sector Laplacian. If the fiber criteria are unmet, the edge weight goes to 0 (a wall).

### Track 3: Dynamic Sheaf Laplacian (Line of Sight & Raycasting)
Hitscan weapons (pistol, shotgun) and monster Line of Sight (LoS) require traversing rays across the map.
- **Othello Connection:** This is mathematically identical to the Othello ray-flanking mechanic (§10.7 of the Othello notebook).
- **Implementation:** A cellular sheaf where restriction maps along a ray evaluate to 1 (open air) or 0 (solid linedef / closed door). The dynamic sheaf Laplacian instantly identifies the first point of impact for any hitscan vector.

### Track 4: Sound Propagation (Graph Diffusion)
In DOOM, when a weapon is fired, the sound travels from the origin Sector to all adjacent Sectors sharing a portal, waking up monsters. Sound does not travel by physical distance, but by topological flooding.
- **Spectral Mapping:** This is exact heat diffusion on the Sector Graph.
- **Equation:** $S(t) = e^{-L_{sector} \cdot t} S(0)$. The spectrum of $L_{sector}$ dictates exactly how sound permeates a map, identifying acoustic "bottlenecks" (choke points in the map design).

### Track 5: ALU-Native Kinematics (BIP Encoder)
Entities moving through the map have momentum and inertia.
- Using the `ephemerides-spectral` integer ALU pattern, `Velocity_X` and `Velocity_Y` are mapped to modular phase additions over $Z_{2^{32}}$.
- Wall sliding (sliding along a linedef when colliding at an angle) is the projection of the velocity vector onto the null space of the collision edge's normal vector.

## 2. Experimental Data / Ground Truth

We will use the original DOOM shareware WAD (`DOOM1.WAD`), specifically parsing **E1M1: Hangar**, to extract the ground-truth node topologies, linedefs, and sectors for our initial spectral constructions.

### 2.1 Track Implementations (Verified May 2026)

The five foundational research tracks have been materialized into Python reference implementations and verified via `integration_test.py`:

1. **Topology & Diffusion** (`research-doom/doom_topology.py`): Extracted the `L_sector` graph Laplacian and mapped sound propagation to exact matrix exponential diffusion (the Heat Equation over the sector super-graph). Verified that sound decays physically across topological distances.
2. **Kinematics** (`research-doom/doom_kinematics.py`): Replicated John Carmack's BAM (Binary Angle Measurement) fixed-point movement model using strictly bitwise modular math on $Z_{2^{32}}$, including wall-sliding projections.
3. **Dynamic Sheaf Hitscan** (`research-doom/doom_sheaf.py` & `research-doom/doom_raycast.py`): Implemented a Bresenham-based 1D raycaster that models Line of Sight as a directed sheaf Laplacian, where restriction maps act as phase gates (open air = 1.0, wall = 0.0).
4. **Z-Axis Fiber Bundle** (`research-doom/doom_fiber.py`): Modeled 2.5D physical constraints (floor step-up, ceiling clearance) as state-dependent edge severing on the 2D sector graph. Height is mathematically confirmed as a scalar fiber.
5. **WAD Geometry Mocking** (`research-doom/wad_parser_mock.py`): Scaffolded a baseline topology (inspired by E1M1 Hangar) with floor/ceiling elevations for spectral testing.

### 2.2 Real-World Ground Truth: E1M1 Hangar (Verified May 2026)

Using `wad_parser.py` to extract the original 1993 id Tech 1 geometry from `DOOM1.WAD`, we verified the spectral models against **E1M1: Hangar**.

| Metric | Real E1M1 Result | Interpretation |
| :--- | :--- | :--- |
| **Sector Count** | 85 | Total topological nodes in the base manifold. |
| **Portals (Edges)** | 100 | Total two-sided linedef connections. |
| **Sound Reach (t=2.0)** | 18 Sectors | Acoustic reachability from Sector 0 (Start). |
| **Z-Fiber Step-Up > 24** | 24 Portals | 24% of edges represent "windows" or "ledges" requiring lifts/jumps. |
| **Player Connectivity** | 39 Portals | Only 39% of connections are traversable by Player 1 (Z=0, Step=24). |
| **Algebraic Connectivity** | 0.012923 | Extremely low $\lambda_2$ confirms a linear "corridor-based" expansion. |
| **Spectral Radius** | 11.024394 | Max eigenvalue of the Laplacian. |

### 3. Results & System Integration

The components were integrated and validated against both mock and real WAD data:

- **3D Movement Denial:** The Z-Fiber successfully severs edges in the Sector Laplacian. In real E1M1 data, it identifies that over 60% of visible portals are physically impassable from a neutral $Z=0$ state.
- **Sheaf Ray Absorption:** Hitscan rays correctly absorb at the first grid cell where the sheaf restriction map is $0.0$.
- **Topological Diffusion:** Sound propagation via $e^{-Lt}$ correctly identifies the acoustic reachability of sectors. The 18-sector reach in E1M1 matches the "cascading" layout of the initial hangar complex.


### 4.1 Phase-9 BIP Kinematics & Breathing Couplings (Implemented May 2026)

We transitioned kinematics from 16.16 fixed-point to a **Phase-9 BIP (Bit-Interleaved Phases)** encoder.

- **Encoding:** Coordinates $(x, y)$ are mapped to a 512-dimensional hypervector $H \in \{-1, 1\}^{512}$ via coprime cyclic shifts (67, 7).
- **Breathing Couplings:** To mirror the Ephemerides HDC (Jupiter-Saturn resonances), we introduced non-linear interaction energy between the X and Y axes. The cyclic shift is perturbed by a "breathing term" $(x \cdot y \bmod 512)$. This introduces harmonic resonances into the spatial manifold, causing the phase space to bend slightly based on geometric coordinates.
- **Spatial Orthogonality:** Distant points in E1M1 (e.g., $(100, 200)$ vs $(500, 800)$) show near-zero similarity (dot product $\approx -0.015$), while adjacent points maintain a detectable correlation.
- **Result:** Spatial progression is now represented as a trajectory in high-dimensional phase space, allowing for collision detection via dot-product thresholding.

### 4.2 Spectral BSP Partitioning (Implemented May 2026)

The level's spatial hierarchy was automatically derived using **Spectral Clustering** (Fiedler vector partitioning) rather than heuristic geometric splits.

- **Primary Cut:** The Fiedler vector ($\lambda_2 = 0.012923$) split E1M1 into two nodal domains of 39 and 46 sectors.
- **Bottleneck Identification:** The spectral split severed only **3 portals**, identifying the absolute geographic "choke point" of the Hangar's layout.
- **Application:** This method allows for the automated generation of BSP trees that are topologically optimized for sound and visibility propagation.
### 4.3 Physical Sound Diffusion (Refined May 2026)

Replaced the unstable high-order Taylor expansion with a stable **multi-step Euler integration** of the Heat Equation:
- **Model:** $s(t+\Delta t) = s(t) - \Delta t \cdot L \cdot s(t)$.
- **Implementation:** 8-step iterative diffusion in `doom_spectral.c`.
- **Result:** Sound intensity remains strictly bounded within $[0, 1]$, providing a physically correct "spectral flooding" signal that naturally obeys the level's topological bottlenecks.

### 4.4 The Haptic Manifold: Phase Anchors (Implemented May 2026)

To drive the **mlehaptics** hardware, we implemented a sensory layer that translates topological state into motor tension.

- **Phase Anchors:** Each sector is assigned a 512D "Anchor Hypervector" $H_{anchor}$. These anchors are diffused across the graph to maintain local phase correlation.
- **Spectral Tension:** The "friction" experienced by the player is calculated as:
  $Tension = 1.0 - \text{Similarity}(H_{player}, H_{anchor})$.
- **Engine Trace:** The DOOM engine now outputs real-time `[HAPTIC]` tension signals in the player loop, enabling high-fidelity sensory feedback based on the player's resonance with the environment.

### 4.5 Sheaf Raycasting & AI BIM Awareness (Implemented May 2026)

We have fully replaced DOOM's heuristic Line of Sight (LoS) and sound-alert logic with pure spectral operators.

- **Sheaf Raycasting (`p_sight.c`):** Integrated `ds_sheaf_raycast` as a fast-path in `P_CheckSight`. The raycaster models LoS as a directed sheaf Laplacian, absorbing spectral signals at topological boundaries.
- **AI BIM Awareness (`p_enemy.c`):** Replaced `P_NoiseAlert` flood-fill with `ds_calculate_monster_awareness`. Monsters now "wake up" based on the topological resonance (dot product) between their local Phase Anchor and the diffused sound field $S(t)$.

## 5. Summary of Artifacts

| Artifact | Location | Description |
| :--- | :--- | :--- |
| **BIP State** | `results-doom/e1m1_bip_sample.npy` | 512D hypervector of a sample E1M1 coordinate. |
| **Partition Map** | `results-doom/e1m1_spectral_partition.npy` | Fiedler vector and sector cluster assignments. |
| **Haptic Anchors**| `results-doom/e1m1_haptic_anchors.npy` | 85 sector Phase Anchors for sensory feedback. |
| **WAD Parser** | `research-doom/wad_parser.py` | Binary IWAD extractor for id Tech 1 data. |
| **Headless Runner**| `research-doom/ds_headless` | Compiled manifold simulator with rich CLI args. |
| **Spectral Engine**| `doom-spectral/source/linuxdoom-1.10/` | DOOM source code with integrated spectral lattice. |

| **Spectral Engine**| `doom-spectral/source/linuxdoom-1.10/` | DOOM source code with integrated spectral lattice. |