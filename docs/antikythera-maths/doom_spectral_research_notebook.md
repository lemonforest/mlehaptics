# DOOM as a Spectral Lattice System

**Authors:** Steven (mlehaptics Project) & Gemini Code Assist
**Date:** May 2026
**Status:** Active research — translating id Tech 1 into a graph-Laplacian spectral model.

> Living document. Sibling to:
> - [../chess-maths/chess_spectral_research_notebook.md](../chess-maths/chess_spectral_research_notebook.md) — The static fiber bundle and piece kinematics.
> - [../othello-maths/othello_spectral_research_notebook.md](../othello-maths/othello_spectral_research_notebook.md) — The dynamic sheaf Laplacian (raycasting and LoS).
> - [./ephemerides_spectral_research_notebook.md](./ephemerides_spectral_research_notebook.md) — The ALU-native $Z_{2^{32}}$ BIP encoder and Phase-9 adaptive couplings.

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

## 3. Results & System Integration

The components were integrated in `integration_test.py` with the following results:

- **3D Movement Denial:** The Z-Fiber successfully severs edges in the Sector Laplacian when an entity's height exceed ceiling clearance or when floor elevations exceed `MaxStep` (24 units).
- **Sheaf Ray Absorption:** Hitscan rays correctly absorb at the first grid cell where the sheaf restriction map is $0.0$, identifying impact points through the dynamic sheaf Laplacian.
- **Topological Diffusion:** Sound propagation via $e^{-Lt}$ correctly identifies the acoustic reachability of sectors, with sound intensity decaying as a function of graph-Laplacian distance rather than Euclidean distance.

## 4. Future Directions

- **Phase-9 BIP Encoding:** Transition the kinematics from standard fixed-point to the Phase-9 adaptive coupling model used in the Ephemerides HDC.
- **BSP Spectral Partitioning:** Use spectral clustering on the Sector Graph to automatically generate BSP trees based on eigenbasis nodal domains.
- **Visibility (PVS) as Eigenfunction:** Model the Potentially Visible Set (PVS) as the principal eigenfunction of the local visibility operator.