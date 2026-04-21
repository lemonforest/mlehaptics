# Phase-Operator Move Engine: Notebook Supplement

**Status:** working supplement — occupies the **§11** slot in [chess_spectral_research_notebook.md](chess_spectral_research_notebook.md) and will be merged in place once experimental validation is complete. Internal numbering §11.1 through §11.9 matches the target slot exactly. Prior-art cross-references assume the current notebook state through §9r (polarization reframing) and §10 (phase-space Othello).

**Framing:** this supplement investigates whether the legal reachable set of each polarization state on the 8×8 lattice can be generated entirely in phase space — via coprime cyclic phase operators acting on a polarization's origin phase tuple — without ever consulting the 2D board coordinates. The goal is data, not theory. Each step defines a concrete computation and a concrete decision point. We do not know in advance whether the phase-operator formulation provides anything that the geometric generator does not. The point of the experiment is to find out.

**Language discipline:** throughout this supplement, movement is "phase transition," pieces are "polarization states" (or "locked-phase excitations"), the board is "the lattice domain" or "the coprime cyclic phase space," and decisions are thermodynamic (gradient-following) rather than strategic. Specific chess terminology is retained only where it references the validation ground truth (python-chess legal move sets).

**Connection to UTLP S4:** the central mechanism is the Chinese Remainder Theorem aliasing horizon from UTLP S4, applied spatially rather than temporally. Where S4 uses the horizon to detect temporal partitions between network nodes (HD vector similarity below threshold indicates temporal phase recovery is ambiguous), this supplement uses an analogous horizon to detect spatial partitions between polarization reachable sets (phase-tuple transformations beyond the polarization's characteristic horizon produce ambiguous destinations). Same mathematics, different domain.

---

## §11.1. The Phase-Operator Hypothesis

### §11.1.1 Statement

For each of the six polarization states {N, B, R, Q, K, P} parameterized in §9r (angle θ, mass/damping, T-symmetry class, Z₂ charge), there exists a characteristic phase-shift operator **P_polarization** such that:

- Applied to the phase tuple φ_origin of any lattice node, P_polarization generates a discrete set of reachable destination phase tuples {φ_dest}.
- The generated set is identical (as a set of lattice nodes, after phase-to-lattice inversion) to the legal reachable set computed by the geometric generator from §5 and used throughout the existing notebook.
- The operator is defined purely in terms of the coprime generators from §9f (67 for row-axis, 7 for column-axis, mod 640) and the polarization's quantum numbers from §9r.

### §11.1.2 What this hypothesis would establish if confirmed

If the phase operators reproduce the geometric reachable sets exactly, then the 2D lattice coordinates are **redundant representation**. The lattice domain is already encoded, in full, by the coprime phase-tuple structure of the 640-dim HDC space. Every legal transition corresponds to a phase-arithmetic operation in this space. The 2D board is a visualization of the phase structure, not the substrate of it.

This would be a strong claim. It is the reason the experiment is worth running even if it produces nothing operationally new — confirming or refuting it tells us something structural about the field representation.

### §11.1.3 What this hypothesis would not establish

Nothing about whether phase-space computation is faster, more accurate, or more revealing than geometric computation. Nothing about whether phase-space similarity corresponds to thermodynamic similarity. Nothing about fog-of-war, partial observation, or the aliasing horizon beyond demonstrating that the full horizon contains the full legal reachable set.

Those are downstream experiments (§11.3–§11.6). §11.1 just tests the equivalence.

### §11.1.4 The null hypothesis

The phase-operator formulation may fail in one of three ways:

1. **Incomplete reach**: the operators produce a subset of the legal reachable set (some legal destinations are missed).
2. **Excess reach**: the operators produce a superset (some generated phase tuples correspond to illegal destinations).
3. **State-dependent failure**: the operators work for unobstructed positions but fail when other excitations block paths for sliding polarization states.

Case 3 is the most likely failure mode. Sliding polarization states (R, B, Q) have their reachable set truncated by other excitations along the ray. A pure phase operator does not know about other excitations — it operates on the origin phase alone. Resolving this will require either phase-space representation of occupation (possible via the existing 640-dim encoding, which already represents occupation globally) or admission that the phase operator generates the **unobstructed** reachable set and a separate occupation check is required to prune.

Either outcome is informative. Data first, interpretation after.

---

## §11.2. Phase Operator Specifications

### §11.2.1 Coordinate conventions

Row index r ∈ {0, 1, …, 7}. Column index c ∈ {0, 1, …, 7}. The origin phase tuple for lattice node (r, c) is:

φ(r, c) = (r × 67 + c × 7) mod 640

This extends §9f's coprime roll binding from the historical 512-dim encoder (mod 512) to the production 640-dim encoder (mod 640). Both moduli admit the same generators 67 and 7: gcd(67, 512) = gcd(67, 640) = gcd(7, 512) = gcd(7, 640) = 1. The 64-point image of Z₈ × Z₈ under φ is verified distinct (no collisions) for both moduli. §11 operates at mod 640 throughout; any reference to §9f's mod 512 formulation should be read as the antecedent of this extended form.

The phase tuple is a single integer in [0, 640), but it carries two components: r × 67 mod 640 (row phase) and c × 7 mod 640 (column phase), which are individually recoverable because 67 and 7 are coprime to 640 (640 = 2⁷ × 5; 67 is prime and not 2 or 5; 7 is prime and not 2 or 5).

**Subgroup structure.** The image set {φ(r, c) : (r, c) ∈ [0, 7]²} is *not* a subgroup of Z₆₄₀ — closure fails (e.g., 384 + 384 = 128 mod 640, which is not in the image). This is the correct structure for the problem: phase-op shifts that carry an origin off the lattice land in the off-image complement of Z₆₄₀, where §11.3.2 inversion fails, and §11.3.3 pruning catches them. A subgroup image would close under piece-operator addition and eliminate the boundary-detection mechanism.

### §11.2.2 Phase operator for the rook (massless, θ = 0° and 90°, T-symmetric)

The rook propagates along orthogonal rays. The two primary D4 axes correspond to pure row phase shifts and pure column phase shifts:

**P_rook(φ_origin)** = {φ_origin + k × 67 mod 640 : k ∈ {±1, ±2, …, ±7}} ∪ {φ_origin + k × 7 mod 640 : k ∈ {±1, ±2, …, ±7}}

Unobstructed reachable set: up to 14 destinations (7 in each orthogonal direction). The upper bound is the path graph diameter minus 1.

### §11.2.3 Phase operator for the bishop (massless, θ = 45° and 135°, T-symmetric)

The bishop propagates along diagonal rays. Diagonal phase shifts are combinations of row and column phases at equal magnitude:

**P_bishop(φ_origin)** = {φ_origin + k × (67 + 7) mod 640 : k ∈ {±1, ±2, …, ±7}} ∪ {φ_origin + k × (67 − 7) mod 640 : k ∈ {±1, ±2, …, ±7}}

Note: 67 + 7 = 74 is the NE/SW diagonal generator; 67 − 7 = 60 is the NW/SE diagonal generator.

### §11.2.4 Phase operator for the queen (massless, θ ∈ {0°, 45°, 90°, 135°}, T-symmetric)

The queen is the superposition of rook and bishop operators:

**P_queen(φ_origin)** = P_rook(φ_origin) ∪ P_bishop(φ_origin)

Unobstructed reachable set: up to 28 destinations (14 orthogonal + 14 diagonal).

### §11.2.5 Phase operator for the king (massive, all θ at radius r = 1, T-symmetric)

The king is a localized excitation — k = ±1 only, all 8 directions:

**P_king(φ_origin)** = {φ_origin + s mod 640 : s ∈ {±67, ±7, ±74, ±60}}

Unobstructed reachable set: up to 8 destinations.

### §11.2.6 Phase operator for the knight (tunneling, knight-offset θ class, T-symmetric)

The knight occupies its own θ class in the §9r polarization framework — disjoint from {axial, diagonal}. Its 8 destinations are the D4 orbit of (1, 2), with angles {26.57°, 63.43°, 116.57°, 153.43°, 206.57°, 243.43°, 296.57°, 333.43°} (arctan(1/2) is one representative, not the full class). The 8 destinations correspond to 8 distinct linear combinations of the row and column generators:

**P_knight(φ_origin)** = {φ_origin + s mod 640 : s ∈ {±(2×67 + 7), ±(2×67 − 7), ±(67 + 2×7), ±(67 − 2×7)}}
                              = {φ_origin + s mod 640 : s ∈ {±141, ±127, ±81, ±53}}

Unobstructed reachable set: up to 8 destinations.

### §11.2.7 Phase operator for the pawn (massive, forward-only, T-violating, Z₂-charge-dependent)

The pawn operator depends on Z₂ charge. For white (charge +V):

**P_pawn_white(φ_origin, move_type)** = 
- if move_type = advance and on starting rank: {φ_origin + 67, φ_origin + 2×67} mod 640
- if move_type = advance: {φ_origin + 67} mod 640
- if move_type = capture: {φ_origin + 67 + 7, φ_origin + 67 − 7} mod 640

For black (charge −V): replace +67 with −67 throughout.

The T-violation is explicit: there is no inverse operator. The phase operator is non-Hermitian, consistent with §9m's identification of the pawn's antisymmetric fiber.

**Empty-board comparison caveat (§11.3).** python-chess does not report diagonal captures as legal moves when no enemy piece occupies the target square. The §11.3 equivalence check against python-chess therefore compares *advance* destinations only; capture destinations are validated in §11.4 (occupation-aware) where enemy pieces are present on the board. This is a quirk of the reference implementation, not of the phase operator — the capture phases are arithmetically correct, they just lack validation targets on an empty board.

### §11.2.8 What these operators do and do not include

**Included:** the unobstructed reachable set for each polarization from any origin. The mathematics is pure phase arithmetic modulo 640.

**Not included:** 
- Occupation-based ray truncation (handled separately in §11.4)
- En passant (a temporal couple between two pawn moves)
- Castling (a coupled two-polarization transition)
- Promotion (a polarization-identity change at the horizon boundary)
- Check/checkmate legality (a global constraint on the king's phase tuple)

The base experiment (§11.3) tests only the unobstructed set. Subsequent experiments extend to the full legal set.

---

## §11.3. Experiment 1: Equivalence on Empty Board

### §11.3.1 Protocol

For each polarization state p ∈ {N, B, R, Q, K, P_white, P_black}, and for each origin square (r, c) ∈ {0, …, 7}²:

1. Compute the phase-operator reachable set: apply P_p to φ(r, c), obtain a set of output phase tuples, invert each output phase tuple back to (r', c') coordinates. Prune any (r', c') outside [0, 7]² (boundary handling).
2. Compute the geometric reachable set: instantiate a position with only polarization p at (r, c) (appropriate color for pawn) in python-chess, enumerate legal moves, collect destination squares.
3. Compare as sets. Record: positions where sets match, positions where phase-operator set is missing destinations, positions where phase-operator set has extra destinations.

### §11.3.2 Inversion from phase tuple to coordinates

Given a phase tuple φ_out ∈ [0, 640), recover (r', c') by:

- φ_out mod 7 gives information about the column (but with collisions every 7 values)
- φ_out mod 67 gives information about the row (with collisions every 67 values)

Since 640 = 2⁷ × 5 is not coprime with 7 or 67, the inversion is not a simple modular division. The correct inversion is: search over all (r', c') ∈ [0, 7]² and find the one whose φ(r', c') equals φ_out. This is a 64-entry table lookup.

### §11.3.3 Boundary handling

The phase operators are defined modulo 640, so they naturally wrap. A rook at (0, 0) moving 7 units in the +row direction produces φ = 7 × 67 = 469 mod 640 = 469, which inverts to (7, 0) — correct. But a rook at (7, 0) moving 1 unit in the +row direction produces φ = 8 × 67 = 536 mod 640 = 536, which inverts to... nothing in [0, 7]².

Boundary condition: destinations must satisfy r', c' ∈ {0, …, 7}. Any phase tuple that does not invert to a valid lattice node is outside the boundary and must be pruned.

This means the phase operator generates a **torus** reachable set which is then clipped to the finite 8×8 domain. This is the same structure as the DCT eigenbasis being extended periodically beyond the board and then truncated — consistent with the existing framework.

### §11.3.4 Success criteria

**Full equivalence:** for all polarizations, for all origins, phase-operator set = geometric set.

**Partial equivalence:** full equivalence for some polarizations, failure for others. Record which and analyze.

**Failure:** phase-operator set systematically differs from geometric set. Record the pattern of differences.

### §11.3.5 Data to collect

Per (polarization, origin) pair:
- phase_op_destinations: set of (r', c') produced by phase operator + inversion + boundary clipping
- geometric_destinations: set of (r', c') from python-chess on an empty-board-with-one-piece position
- set_equal: boolean
- missing: geometric_destinations − phase_op_destinations
- extra: phase_op_destinations − geometric_destinations

Total rows: 7 polarizations × 64 origins = 448 rows. Small enough to inspect manually if needed.

### §11.3.6 Decision point

If §11.3 produces full equivalence, proceed to §11.4 (occupied-board extension).

If §11.3 produces partial or full failure, stop and analyze before proceeding. The failure pattern will indicate whether the phase-operator formulation is fundamentally wrong or just needs refinement.

---

## §11.4. Experiment 2: Occupation-Aware Phase Operators

### §11.4.1 The occupation problem

Sliding polarizations (R, B, Q) have rays truncated by other excitations. A rook at d1 in the starting position cannot reach d8 because d2 is occupied by a pawn. The phase operator from §11.2 produces the unobstructed set — it does not know about d2.

### §11.4.2 Candidate solutions

**Solution A: Post-hoc geometric pruning.** Generate the unobstructed set via phase operators, then use the geometric board state to prune blocked destinations. This is a hybrid — phase-space generation followed by geometric filtering. It works but undermines the goal of pure phase-space computation.

**Solution B: Phase-space occupation field.** The 640-dim HDC encoding already represents the global occupation state. For each ray direction, compute the "occupation phase" — the phase tuple(s) of the nearest occupied node along the ray. Truncate the unobstructed set at the occupation phase. Purely phase-space, but requires defining "nearest along ray" in phase-space terms.

**Solution C: Incremental phase operator.** Instead of generating all k ∈ {±1, …, ±7} at once, iterate k = 1, 2, 3, … and halt when the generated phase tuple matches an occupied node's phase tuple. This is purely phase-space and matches the physical intuition of a ray propagating until it hits something.

Solution C is cleanest and most consistent with the lattice-fermion framing — the ray propagates step by step, interacts with the first excitation it encounters, and terminates. This is the phase-space analog of the Green's function collapsing at a scattering site.

### §11.4.3 Protocol for Solution C

For each sliding polarization p ∈ {R, B, Q} and for each origin φ_origin in a position with other excitations present:

1. For each ray direction d (e.g., +row, −column) defined by the polarization's phase-shift unit u_d:
2. Initialize k = 1.
3. Compute candidate phase φ_k = φ_origin + k × u_d mod 640.
4. Check if φ_k corresponds to a valid lattice node (inside [0, 7]²). If not, halt the ray (boundary reached).
5. Check if φ_k corresponds to an occupied node in the current position. If occupied by same Z₂ charge, halt the ray before φ_k (cannot capture own charge). If occupied by opposite Z₂ charge, include φ_k (capture) and halt. If unoccupied, include φ_k and continue to k = k + 1.

The occupation check in step 5 is the only geometric operation. All phase generation is pure arithmetic.

### §11.4.4 Data to collect

For positions sampled from an existing corpus (e.g., `sweep_chain_lichess_drnykterstein_2026-04-14_N10`):

- position_fen
- polarization and origin
- phase_op_legal_set: set of (r', c') after occupation-aware phase operator
- geometric_legal_set: set of (r', c') from python-chess legal moves for that polarization from that origin
- set_equal: boolean
- missing, extra: as in §11.3

Sample 100 positions uniformly from the corpus. For each position, iterate over all polarizations and all origins with that polarization's Z₂ charge. Expected: ~30 polarization-origin pairs per position × 100 positions = ~3000 rows.

### §11.4.5 Decision point

Full equivalence with geometric legal moves means the phase-operator formulation is operationally complete for move generation. We can then ask what the phase-space representation offers that the geometric one does not (§11.5 onward).

Partial or full failure means specific edge cases need special handling. Record which.

---

## §11.5. Experiment 3: Phase-Tuple Similarity as Field Gradient Indicator

### §11.5.1 Motivation

If §11.3 and §11.4 succeed, we have a phase-space move generator that reproduces the geometric one. The next question is whether phase-space operations reveal thermodynamic structure that geometric operations do not.

Specifically: for any candidate transition (φ_origin → φ_dest) under polarization operator P_p, does the **phase-tuple similarity** between the pre-transition and post-transition 640-dim encodings correlate with the thermodynamic gradient Δ from the earlier experiments?

### §11.5.2 What phase-tuple similarity measures

The 640-dim encoding is a superposition over all current excitations. A transition modifies the encoding by removing the origin's contribution and adding the destination's contribution (and, for captures, removing the annihilated excitation's contribution). The cosine similarity between pre- and post-transition encodings measures how much the field configuration changes.

Large change (low similarity) = transition perturbs the field significantly = large gradient.
Small change (high similarity) = transition perturbs the field minimally = small gradient.

This is a field-theoretic quantity, not a geometric one.

### §11.5.3 Protocol

For each position in the sample corpus (§11.4), for each legal transition:

1. Compute enc_before = encode_640(position_before).
2. Compute enc_after = encode_640(position_after_transition).
3. Compute phase_similarity = cosine(enc_before, enc_after).
4. Record phase_similarity alongside the Δ value from the earlier experiment (if position is in the Stockfish corpus, record Stockfish eval too).

### §11.5.4 Data to collect

Per legal transition:
- position_fen
- transition_uci
- polarization_type
- phase_similarity (cosine in [−1, 1])
- delta_v1 (from prior experiment, if available)
- stockfish_eval (from prior experiment, if available)
- kappa_annihilate, kappa_threat (from prior experiment)
- was_played (boolean)

### §11.5.5 Analysis

Compute Spearman ρ between phase_similarity and each of: delta_v1, stockfish_eval, kappa_annihilate, kappa_threat. Break down by polarization type and by capture/non-capture.

### §11.5.6 Decision point

If phase_similarity correlates strongly (|ρ| > 0.3) with any existing thermodynamic quantity, the phase representation is capturing the same signal. If it correlates only with specific components (say, high correlation with kappa_annihilate but low with delta_v1), the phase representation is revealing a decomposition of the thermodynamic gradient we have not explicitly computed.

If phase_similarity correlates with nothing (|ρ| < 0.1 across the board), the phase representation is capturing an orthogonal quantity — potentially the "field geometry" that Stockfish does not measure but that we suspected in the κ_position experiments.

All three outcomes are informative.

---

## §11.6. Experiment 4: Aliasing Horizon as Partition Detection

### §11.6.1 The UTLP S4 mechanism, applied spatially

In UTLP S4, partition detection uses HD vector similarity between nodes. When similarity drops below threshold, the nodes have drifted beyond the CRT aliasing horizon and phase-lock fallback becomes necessary. S4's "CRT aliasing horizon" is the literal Chinese Remainder Theorem — coprime temporal moduli lose unambiguous recovery past a specific range.

Spatial analog (as framework, not theorem): consider two positions P₁ and P₂. Compute similarity(enc_640(P₁), enc_640(P₂)). If the positions are close in phase space (high similarity), they are in the same *similarity cell* — field-theoretically similar and expected to have similar thermodynamic gradients. If similarity drops below threshold, the positions are in different similarity cells — the phase representation cannot reliably extrapolate between them.

This gives a partition detector for phase space. Positions within the same partition should have consistent local gradients. Positions across a partition boundary should have discontinuous gradients.

**Mathematical honesty caveat.** The enc_640 vector is a bundled HDC superposition of piece states, not a literal coprime-residue encoding of position. A similarity drop is a high-dimensional noise-floor crossing in that bundled representation, not a CRT-recovery ambiguity event. The "similarity cell" framing is metaphorically useful and S4-analogous, but claiming CRT-specific partition-detection guarantees requires either (a) a proof that the bundled HDC similarity structure factorizes into per-axis aliasing kernels — the Vector Function Architecture product-kernel result from Frady et al. 2022 (arXiv:2109.03429) and the Residue HDC kernel theorem from Kymn et al. 2024 (arXiv:2311.04872) are the relevant tools, or (b) reframing §11.6 as an empirical partition-detection experiment with no appeal to CRT guarantees. This supplement takes path (b) for the experimental phase and flags (a) as a downstream analytical task.

### §11.6.2 Why this matters for the depth-of-search question

The σ estimator from earlier experiments measures gradient roughness across fiber-neighbor transitions. Aliasing horizon detection is the complementary concept at the position level: it asks whether the current position is in a region of phase space where local gradients are reliable.

A position with low σ in a small CRT cell: gradient is reliable, local decision suffices.
A position with high σ or near a partition boundary: gradient is unreliable or inapplicable, deeper exploration needed.

### §11.6.3 Protocol

For each game in the corpus:

1. Compute enc_640 for every ply.
2. Compute pairwise similarities between all plies in the game (upper triangular matrix).
3. Identify "phase clusters" — sequences of consecutive plies with mutual similarity above threshold.
4. Identify "partition boundaries" — consecutive plies with similarity below threshold.

For each ply:
- ply_index
- cluster_id (which phase cluster this ply belongs to)
- distance_to_nearest_boundary (in plies)
- similarity_to_previous_ply
- similarity_to_next_ply

### §11.6.4 Cross-reference with the σ experiment

For plies where we have σ data: does high σ correlate with proximity to a partition boundary? Does low σ correlate with being deep inside a phase cluster?

This tests whether the position-level partition structure (§11.6) is the same thing as the move-level gradient roughness (σ), viewed at different scales.

### §11.6.5 Cross-reference with Stockfish depth-gap

For plies where we have Stockfish evaluations at multiple depths: do the depth-gap peaks (positions where shallow and deep evaluations disagree most) align with partition boundaries? Previous data showed A₁ correlates with depth gap (ρ = +0.452). Does proximity to a phase partition correlate more strongly?

### §11.6.6 Decision point

If partition boundaries align with high σ regions and with depth-gap peaks, we have a unified picture: the phase-space partition structure IS the structure that determines when local computation suffices versus when search is required. This would be the meta-cognitive signal we have been reaching for.

If partition boundaries are unrelated to σ or depth gap, the phase-space partitions are a structural feature of the encoding that does not correspond to computational difficulty. Still data, still informative, but a different answer.

---

## §11.7. Open Infrastructure Requirements

### §11.7.1 What Claude Code needs to build

1. **phase_operators.py** — the seven operator functions from §11.2, implemented as pure arithmetic on 640-dim phase tuples.
2. **phase_to_coords.py** — the inversion lookup table from phase tuple to (r, c), and the boundary check.
3. **equivalence_check.py** — §11.3 experimental protocol. Runs in minutes.
4. **occupation_aware_phase_op.py** — §11.4 Solution C implementation. Uses phase_operators.py + a minimal occupation check against a python-chess Board object.
5. **phase_similarity_analysis.py** — §11.5 experimental protocol. Reuses the existing encoder.
6. **partition_detector.py** — §11.6 experimental protocol. Produces phase cluster assignments per game.

### §11.7.2 Data flow

All experiments produce CSV outputs with the schema specified in each §11.3–§11.6 data-to-collect block. Outputs go to `docs/chess-maths/results/phase_operator_experiments/`.

### §11.7.3 Dependencies

- python-chess (already in the project per §analyze_delta_sigma.py)
- numpy
- The existing `spectral_py.py` encoder for the 640-dim encode_640 function
- No new installs expected

### §11.7.4 What to not do

- Do not tune phase operator definitions to match geometric results. If §11.3 fails, record the failure — do not adjust the operators to fit. The point is to test whether the §11.2 operators as specified produce the legal reachable set.
- Do not produce visualizations during the experiment runs. Raw CSV + summary text only.
- Do not attempt to interpret results during the collection phase. Interpretation happens after all data is collected.
- Do not optimize for runtime. §11.3 runs in seconds; §11.4 and §11.5 run in minutes; §11.6 runs per-game. None of this is compute-bound.

---

## §11.8. What We Will Ask After Data Collection

We are deliberately not specifying the post-data questions here. The point of this experimental arc is to generate data that may change what questions are worth asking. Some preliminary guesses at what the data might force us to ask:

- If §11.3 fails for the knight but succeeds for others, does the phase-shifted harmonic at arctan(1/2) require a different operator structure than linear combinations of row/column generators?
- If §11.5 shows phase_similarity uncorrelated with all thermodynamic quantities, is the phase representation measuring something we have not yet named?
- If §11.6 partition boundaries align with depth-gap peaks, can we use phase-cluster membership to replace depth-15 Stockfish with a phase-arithmetic classifier?
- If the phase operators work but offer no operational advantage, have we demonstrated that the 2D lattice is a convenient redundancy over a more fundamental coprime-cyclic structure?

These are placeholders. The real questions emerge from the data.

---

## §11.9. Success and Failure Both Produce Knowledge

The explicit stance of this supplement: we do not know if the phase-operator move engine is a better abstraction than the geometric move generator. We do not know if it reveals structure the geometric representation hides. We do not know if UTLP S4's aliasing horizon mechanism transfers cleanly from temporal synchronization to spatial move generation.

We know what experiments would answer each of these questions, and we know the data each experiment would produce. We are running the experiments because the answer — whatever it is — will change what we understand about the chess lattice as a field-theoretic object.

If the phase operators reproduce the geometric generator exactly and offer no additional structure, we will have demonstrated that the geometric representation is the efficient one and the phase representation is a redundant alternative. That is a real result.

If the phase operators reveal partition structure that corresponds to computational difficulty, we will have found the meta-cognitive signal for search-budget allocation. That is a different real result.

If the phase operators fail to reproduce the geometric generator, we will have learned something specific about which polarization states resist phase-arithmetic description. That is another real result.

All three outcomes advance the research. None of them is wasted effort.
