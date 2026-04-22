# Claude Code: §11.6 Aliasing Horizon as Partition Detection

## Context

§11.3, §11.4, and §11.5 are all merged to main. §11.5 landed as validated null for phase-tuple *move-level* similarity as a check-filter signal (|ρ|=0.097). §11.6 is the final experiment in the §11 arc: does **position-level phase-space similarity structure** correspond to computational difficulty?

The null in §11.5 concerned move-pair similarity — the field-configuration-delta induced by a single transition. §11.6 asks a different question: do *positions* cluster into similarity-bounded regions such that the boundaries between regions align with places where evaluation becomes structurally uncertain? The supplement calls these regions "similarity cells" (having softened the original "CRT cell" framing per PATCH 4 earlier in the arc).

Two cross-references the supplement queues in §11.6.4 and §11.6.5:

1. **σ estimator cross-reference (§11.6.4).** Measures whether high gradient-roughness at the move level aligns with proximity to a partition boundary at the position level.
2. **Stockfish depth-gap cross-reference (§11.6.5).** Measures whether positions where shallow vs deep Stockfish disagree most align with partition boundaries. Prior A₁ channel correlates at ρ=+0.452 against depth-gap; does partition-proximity beat that?

**Scoping reality check.** Neither cross-reference has existing data sitting in `docs/chess-maths/results/`:

- The σ estimator is referenced in the supplement but not materialized as a CSV. `docs/chess-maths/archive/chess_depth_gap_expanded.py` exists but is archived, and its output schema does not match what §11.6.4 implies. Implementing σ as a prerequisite for §11.6.4 is a separate experiment outside §11.6's scope.
- Depth-gap data exists implicitly — `stockfish_correlation/stockfish_evaluations_v2.csv` has 6040 rows at depth 12, but §11.6.5 needs shallow+deep pairs (e.g., depth 1 vs depth 20) on the same position corpus to compute gaps. Re-running Stockfish at multiple depths takes hours and is out of scope for this prompt.

Given that reality, split §11.6 into two phases matching the §11.5 pattern:

- **Phase A** — run the partition-detection analysis itself on existing corpus and encoder (cheap, reuses everything, answerable today). Schema includes columns for σ and depth-gap cross-references but leaves them empty. Records partition structure as data.
- **Phase B** — deferred to a follow-up experiment that attaches σ and depth-gap data when those prerequisites exist. Outside this prompt's scope.

This mirrors exactly what §11.5 did with the Stockfish-dependent thermodynamic columns: run the primary experiment, leave cross-reference columns empty, document the deferral, ship the clean Phase A result.

Research notebook §11.6 (in the supplement) is the ground truth for the experimental protocol. Read it before starting.

---

## Phase 1 — Supplement patches

Three patches to `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md`. These document the Phase A vs Phase B split and patch §11.6.6's decision point to reflect that Phase A's output is partition structure itself, with cross-references deferred.

### PATCH 1 — §11.6.3 mark the protocol as Phase A

Locate §11.6.3 (the existing "Protocol" block):

OLD:
```
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
```

NEW:
```
### §11.6.3 Protocol (Phase A: partition detection)

For each game in the corpus:

1. Compute enc_640 for every ply.
2. Compute pairwise cosine similarities between all plies in the game (upper triangular matrix over plies).
3. Identify **phase clusters** — maximal sequences of consecutive plies whose pairwise similarities with every other ply in the cluster are above a threshold τ.
4. Identify **partition boundaries** — consecutive ply pairs where similarity drops below τ, crossing from one phase cluster into another.

For each ply, record:
- `position_fen`
- `game_id`, `ply_index`
- `cluster_id` (integer per-game cluster assignment)
- `cluster_size` (number of plies in this ply's cluster)
- `distance_to_nearest_boundary` (in plies, signed: negative if the previous boundary is nearer, positive if the next boundary is nearer, zero if this ply is itself a boundary)
- `similarity_to_previous_ply`, `similarity_to_next_ply`
- `similarity_to_cluster_centroid` (mean cosine to all other plies in the same cluster)

**Threshold τ.** The choice of τ is a hyperparameter. Phase A produces the analysis across a sweep of τ ∈ {0.70, 0.80, 0.85, 0.90, 0.95}, reporting cluster statistics per threshold. The researcher inspects the sweep and picks a canonical τ for §11.6.6 interpretation, or reports the full sweep if no single τ dominates.

**Data already available for cross-references.** The following columns are populated from existing data where it exists, and left empty otherwise:

- `sigma_local` — the σ estimator from §11.6.4 (currently **not available**; column left empty; §11.6.4 cross-reference is deferred to Phase B)
- `stockfish_cp` — Stockfish centipawn evaluation at a single reference depth (available from `stockfish_correlation/stockfish_evaluations_v2.csv` for games overlapping that corpus; left empty otherwise)
- `stockfish_depth_gap` — shallow vs deep disagreement magnitude (currently **not available** as shallow+deep pairs do not exist for this corpus; column left empty; §11.6.5 cross-reference deferred to Phase B)
- `kappa_annihilate`, `kappa_threat`, `delta_v1` — populated where the corpus overlaps with `stockfish_correlation/stockfish_evaluations_v2.csv`; empty otherwise

Phase A's primary output is the partition structure itself. Cross-reference analyses (§11.6.4, §11.6.5) run in Phase B when prerequisite data becomes available.
```

### PATCH 2 — §11.6.4/§11.6.5 mark both cross-references as Phase B

Locate §11.6.4:

OLD:
```
### §11.6.4 Cross-reference with the σ experiment

For plies where we have σ data: does high σ correlate with proximity to a partition boundary? Does low σ correlate with being deep inside a phase cluster?

This tests whether the position-level partition structure (§11.6) is the same thing as the move-level gradient roughness (σ), viewed at different scales.
```

NEW:
```
### §11.6.4 Cross-reference with the σ experiment (Phase B — deferred)

**Status.** Deferred. The σ estimator referenced here is not materialized as a CSV in `docs/chess-maths/results/` at the time §11.6 Phase A runs. Implementing σ is a separate experiment outside §11.6's scope.

**Intended analysis (pending σ availability).** For plies where σ data exists: does high σ correlate with `distance_to_nearest_boundary` being small? Does low σ correlate with being deep inside a phase cluster (high `similarity_to_cluster_centroid`)?

This tests whether the position-level partition structure (§11.6) is the same thing as the move-level gradient roughness (σ), viewed at different scales.

Phase B will be scheduled once σ data exists on a corpus that overlaps with the §11.6 Phase A output.
```

Locate §11.6.5:

OLD:
```
### §11.6.5 Cross-reference with Stockfish depth-gap

For plies where we have Stockfish evaluations at multiple depths: do the depth-gap peaks (positions where shallow and deep evaluations disagree most) align with partition boundaries? Previous data showed A₁ correlates with depth gap (ρ = +0.452). Does proximity to a phase partition correlate more strongly?
```

NEW:
```
### §11.6.5 Cross-reference with Stockfish depth-gap (Phase B — deferred)

**Status.** Deferred. The existing `stockfish_correlation/stockfish_evaluations_v2.csv` is single-depth (depth 12) and does not contain the shallow+deep pairs needed to compute depth-gap magnitudes. Re-running Stockfish at multiple depths on the corpus is outside this experiment's compute budget.

**Intended analysis (pending depth-gap data).** For plies where Stockfish evaluations at multiple depths exist: do depth-gap peaks (positions where shallow and deep evaluations disagree most) align with partition boundaries (small `distance_to_nearest_boundary`)? Previous data showed the A₁ channel correlates with depth-gap at ρ=+0.452. Phase B asks whether partition-proximity correlates more strongly than A₁ alone.

Phase B will be scheduled once multi-depth Stockfish data exists on the §11.6 Phase A corpus.
```

### PATCH 3 — §11.6.6 update decision point for Phase A scope

Locate §11.6.6:

OLD:
```
### §11.6.6 Decision point

If partition boundaries align with high σ regions and with depth-gap peaks, we have a unified picture: the phase-space partition structure IS the structure that determines when local computation suffices versus when search is required. This would be the meta-cognitive signal we have been reaching for.

If partition boundaries are unrelated to σ or depth gap, the phase-space partitions are a structural feature of the encoding that does not correspond to computational difficulty. Still data, still informative, but a different answer.
```

NEW:
```
### §11.6.6 Decision point (Phase A)

Phase A produces partition structure itself, not the cross-reference verdicts. Phase A's decision point is narrower than the original §11.6.6 question: **does the phase-space similarity structure exhibit well-defined partitions at all, or does it look like a continuous drift with no natural cluster boundaries?**

Three possible Phase A outcomes:

1. **Clear partitions.** At some threshold τ, games decompose into a small number of internally-coherent clusters with sharp boundaries. `cluster_size` distribution has a modal peak; `similarity_to_cluster_centroid` is tight within clusters and drops cleanly across boundaries. This is the setup Phase B wants — partitions that can be cross-referenced with σ and depth-gap data.

2. **Continuous drift.** Pairwise similarity decays monotonically with ply distance. No natural cluster boundaries; every τ choice is arbitrary. `cluster_size` varies smoothly with τ without a plateau. This closes the partition-detection hypothesis for the C17 encoder: the encoder sees games as continuous trajectories, not as a sequence of phase-cells, and the "similarity cell" framing is descriptive rather than structural.

3. **Mixed behavior.** Some games partition cleanly, others do not. Examine whether the partitioning behavior correlates with game characteristics (opening type, time control, result, Elo) — this is itself an interesting structural finding even if Phase B is partially blocked.

**Phase B decision (deferred).** Once σ and depth-gap data become available, Phase B answers the original §11.6 question: do partition boundaries align with computational-difficulty indicators?

- If boundaries align with both σ and depth-gap peaks: the phase-space partition structure IS the structure that determines when local computation suffices versus when search is required. Meta-cognitive signal confirmed.
- If boundaries are unrelated to both: the phase-space partitions are a structural feature of the encoding that does not correspond to computational difficulty. Null result for the meta-cognitive hypothesis; still structurally informative about how enc_640 organizes game trajectories.
- If boundaries align with one but not the other: partial signal. The decomposition between σ (move-level roughness) and depth-gap (position-level evaluation instability) tells us which scale of computational difficulty the partitions track.

All Phase B outcomes are informative. Phase A must complete cleanly first.
```

### Grep verification for Phase 1

```bash
grep -c "Protocol (Phase A: partition detection)" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md   # expect 1
grep -c "Phase B — deferred" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md                        # expect 2
grep -c "Decision point (Phase A)" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md                  # expect 1
grep -c "similarity_to_cluster_centroid" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md            # expect 2 or 3
```

Commit Phase 1 with message: `§11.6 supplement: split into Phase A (partition detection, available) and Phase B (σ / depth-gap cross-references, deferred)`

---

## Phase 2 — Code build: Phase A partition detector

Add to `docs/chess-maths/phase_operators/` following the same pattern as previous experiments. Do not modify any existing file.

### Directory layout additions

```
docs/chess-maths/phase_operators/
├── (existing files — do not modify)
├── partition_detector.py       # core partition detection logic
├── partition_experiment.py     # §11.6 CLI
└── tests/
    ├── (existing tests — do not modify)
    └── test_partition_detector.py
```

### `partition_detector.py` — core logic

Pure analysis module; no CLI, no I/O. Depends only on numpy and the chess_spectral encoder.

```python
"""§11.6 Phase A — partition detection in phase space.

For a sequence of per-ply 640-dim encodings, computes pairwise similarity
matrix, identifies phase clusters (sequences of consecutive plies with
internal similarity above τ), and records partition boundaries (drops
below τ between consecutive plies).

See PHASE_OPERATOR_SUPPLEMENT.md §11.6 for the experimental protocol.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class PartitionResult:
    """Per-game partition structure at a specific threshold τ.

    similarity_matrix: (n_plies, n_plies) symmetric cosine-similarity matrix.
    cluster_ids: length-n_plies array; integer cluster assignment per ply.
    boundaries: list of ply indices where a cluster ends (right before the next starts).
    """
    similarity_matrix: np.ndarray
    cluster_ids: np.ndarray
    boundaries: list[int]
    threshold: float


def pairwise_cosine(encodings: np.ndarray) -> np.ndarray:
    """Input: (n_plies, 640) array of per-ply encodings.
    Output: (n_plies, n_plies) symmetric cosine-similarity matrix.
    
    Handles zero-norm rows gracefully by returning 0.0 for those pairs
    (should not occur in practice but guards against encoder edge cases).
    """
    ...


def detect_clusters(
    similarity_matrix: np.ndarray,
    threshold: float,
) -> tuple[np.ndarray, list[int]]:
    """Identify maximal consecutive-ply clusters at a given threshold.

    A cluster is a maximal [start, end] range of consecutive plies such that
    similarity_matrix[i, j] >= threshold for all i, j in [start, end].
    
    Returns:
        cluster_ids: length-n_plies int array, cluster assignment per ply
                     (0-indexed within the game).
        boundaries:  sorted list of ply indices where cluster i ends
                     (so ply boundaries[k] is in cluster k, ply boundaries[k]+1
                     is in cluster k+1, for k < len(boundaries)).
    
    Implementation note: walk plies left to right, greedily extending the
    current cluster while every pair in it still satisfies the threshold.
    When the threshold breaks, start a new cluster. This is O(n²) per game
    in the worst case but n is per-game ply count (typically 40-120), so
    total cost is trivial.
    """
    ...


def run_partition_analysis(
    encodings: np.ndarray,
    thresholds: tuple[float, ...] = (0.70, 0.80, 0.85, 0.90, 0.95),
) -> dict[float, PartitionResult]:
    """Run cluster detection at each threshold in the sweep.
    
    Returns a dict mapping each τ to its PartitionResult.
    """
    ...


def per_ply_features(
    result: PartitionResult,
    ply_index: int,
) -> dict:
    """Compute the per-ply features required by the §11.6.3 Phase A schema
    for one ply at the given PartitionResult.
    
    Returns a dict with keys:
        cluster_id, cluster_size, distance_to_nearest_boundary,
        similarity_to_previous_ply, similarity_to_next_ply,
        similarity_to_cluster_centroid
    
    distance_to_nearest_boundary is signed per §11.6.3:
        negative if the previous boundary (end of previous cluster) is nearer,
        positive if the next boundary (end of current cluster) is nearer,
        zero if this ply IS the boundary (last ply of its cluster).
    """
    ...
```

Implementation guidance:

- `pairwise_cosine` is one numpy matmul of row-normalized encodings, then AND with the transpose for symmetry.
- `detect_clusters` greedy left-to-right: for each new ply, check that its similarity to **every** ply currently in the cluster is ≥ τ. If yes, extend; if no, close the cluster and start a new one with just this ply.
- The worst-case O(n²) check (every new ply vs every ply in current cluster) is fine because clusters are bounded in size by τ — once a cluster gets large enough that similarity drops, it closes. For τ=0.70 on middlegame transitions, expect clusters of 5-20 plies.
- `similarity_to_cluster_centroid`: the ply's mean cosine similarity to every *other* ply in its own cluster. For a singleton cluster, define as 1.0 (trivially matches itself).

### `partition_experiment.py` — the §11.6 Phase A CLI

Analogous to `similarity_experiment.py` from §11.5. Iterates over corpus games, encodes each ply, runs partition analysis at each τ, emits per-ply CSV, prints summary.

```python
"""§11.6 Phase A CLI: partition detection in phase space.

For each game in a corpus, encode every ply, compute pairwise cosine
similarity, detect phase clusters at a sweep of thresholds, and emit a
per-ply CSV with cluster assignments and partition-boundary features.

Run from phase_operators/ directory:
    python partition_experiment.py \\
        --corpus ../results/sweep_chain_lichess_drnykterstein_2026-04-14_N10 \\
        [--thresholds 0.70 0.80 0.85 0.90 0.95] \\
        [--stockfish-csv ../results/stockfish_correlation/stockfish_evaluations_v2.csv] \\
        [--out PATH]
"""
```

Required behaviors:

1. **Corpus iteration.** Loop over each game's NDJSON file, parse out per-ply FENs (the ndjson-fen-v2 format has `{"game", "ply", "fen", ...}` records after the header lines).

2. **Encoding.** For each ply, call `encode_640(fen_to_pos(fen))` (same pattern as `phase_similarity.py`).

3. **Partition analysis.** Feed the game's encodings into `run_partition_analysis()` with the threshold sweep.

4. **Per-ply CSV output.** One row per (game × ply × threshold) triple. CSV schema matches §11.6.3:

```
game_id, ply_index, position_fen, threshold,
cluster_id, cluster_size, distance_to_nearest_boundary,
similarity_to_previous_ply, similarity_to_next_ply, similarity_to_cluster_centroid,
sigma_local, stockfish_cp, stockfish_depth_gap,
kappa_annihilate, kappa_threat, delta_v1
```

The last six columns are the cross-reference slots. Populate `stockfish_cp`, `kappa_annihilate`, `kappa_threat`, `delta_v1` from the optional `--stockfish-csv` when (game_id, ply_index) matches; leave `sigma_local` and `stockfish_depth_gap` empty in all rows (per §11.6.4/§11.6.5 deferral).

5. **Stockfish CSV join.** If `--stockfish-csv` points to `stockfish_correlation/stockfish_evaluations_v2.csv`, build a `(game_id, ply) -> row` lookup once at startup. Note the schema is per-move not per-position — each (game, ply) has ~30 candidate moves, each with its own kappa / delta. For position-level join, aggregate: take the mean of `kappa_annihilate`, `kappa_threat`, `delta` across all moves at that (game, ply). These are position-level aggregates. Record them in the `kappa_*` and `delta_v1` columns.

6. **Stdout summary.** After the run, print per-threshold statistics:

```
§11.6 Phase A complete:
  Corpus:        sweep_chain_lichess_drnykterstein_2026-04-14_N10
  Games:         10
  Plies:         1042
  Thresholds swept: [0.70, 0.80, 0.85, 0.90, 0.95]
  
  Per-threshold cluster statistics:
  τ=0.70: clusters/game mean=N.N median=N max=NN; cluster_size mean=N.N median=N p95=NN
  τ=0.80: clusters/game mean=N.N median=N max=NN; cluster_size mean=N.N median=N p95=NN
  τ=0.85: clusters/game mean=N.N median=N max=NN; cluster_size mean=N.N median=N p95=NN
  τ=0.90: clusters/game mean=N.N median=N max=NN; cluster_size mean=N.N median=N p95=NN
  τ=0.95: clusters/game mean=N.N median=N max=NN; cluster_size mean=N.N median=N p95=NN
  
  Continuous-drift check: correlation of similarity_to_previous_ply with
  ply_index-modulo-cluster: if near-zero across all τ, partitioning is real;
  if strongly positive/negative, behavior may be better described as drift.
  
  Phase A outcome: [INTERPRET]
  
  CSV written to: results/phase_operator_experiments/exp4_partitions.csv
  Stockfish cross-reference columns populated: N/M rows
  σ and depth-gap columns: empty (Phase B deferred per §11.6.4/§11.6.5)
```

The `[INTERPRET]` line should summarize the data in one sentence: `"Clear partitions at τ=0.80 (mean N.N clusters/game, tight size distribution) — Phase B cross-reference data acquisition is the next step"` OR `"Continuous drift observed across all τ (no plateau in cluster_size, similarity decays smoothly with ply distance) — partition hypothesis for the C17 encoder is closed"` OR an honest in-between.

Per §11.7.4 (the researcher's standing rule): do not tune τ or any analysis parameter to force a clear outcome. Report what the data shows.

### CLI flags

```
--corpus PATH          required; path to corpus directory containing ndjson/
--thresholds F [F ...] optional; default [0.70, 0.80, 0.85, 0.90, 0.95]
--stockfish-csv PATH   optional; if present, join per-position Stockfish data
--out PATH             optional; default results/phase_operator_experiments/exp4_partitions.csv
--games N              optional; limit to first N games (default: all)
--verbose              optional; print per-game progress
```

### Tests

`tests/test_partition_detector.py` — unit tests for the pure-analysis functions:

1. **pairwise_cosine identity.** For identical rows, similarity is 1.0 on and off diagonal.
2. **pairwise_cosine antipode.** For `[v, -v]`, similarity is -1.0 off-diagonal, 1.0 on-diagonal.
3. **Single cluster detection.** On a similarity matrix of all-ones, `detect_clusters(τ=0.9)` produces one cluster spanning all plies, no boundaries.
4. **No clustering at high τ.** On a similarity matrix where every off-diagonal is 0.5, `detect_clusters(τ=0.9)` produces `n` singleton clusters, `n-1` boundaries.
5. **Two-cluster split.** On a 6-ply synthetic where plies 0-2 are mutually similar (0.95) and plies 3-5 are mutually similar (0.95) but cross-group similarity is 0.3, `detect_clusters(τ=0.8)` produces exactly 2 clusters with boundary between ply 2 and 3.
6. **per_ply_features on synthetic.** For test 5's setup: ply 1 has distance_to_nearest_boundary=-1 (previous boundary) or +1 (next boundary) depending on which is closer; boundary cases zero.
7. **Determinism.** Same input produces same output bit-identically.

### Running order

1. Apply Phase 1 supplement patches. Verify with grep.
2. Build `partition_detector.py` + tests. Run `python -m unittest discover` — all tests pass.
3. Build `partition_experiment.py`. Dry-run on 1 game via `--games 1 --verbose` to confirm encoder loads and cross-reference join works.
4. Full run: `python partition_experiment.py --corpus ../results/sweep_chain_lichess_drnykterstein_2026-04-14_N10 --stockfish-csv ../results/stockfish_correlation/stockfish_evaluations_v2.csv`.
5. Inspect the CSV and stdout summary. The researcher will interpret the Phase A outcome.

### Commit structure

Three commits on branch `chess-spectral-phase-operator-11-6`:

1. `§11.6 supplement: split into Phase A (available) and Phase B (deferred)` — Phase 1 patches only.
2. `§11.6 partition_detector: pure-analysis partition detection at threshold sweep` — `partition_detector.py` + unit tests.
3. `§11.6 Phase A CLI: partition_experiment.py with Stockfish cross-reference join` — CLI, dry-run verified, full run output, CSV committed.

### Handoff

Do not open the PR. Print handoff message:

```
Branch chess-spectral-phase-operator-11-6 ready for review.
§11.6 Phase A data collection complete.

Corpus: sweep_chain_lichess_drnykterstein_2026-04-14_N10 (N games, N plies)

Per-threshold cluster structure:
  τ=0.70: N.N clusters/game (mean size N.N)
  τ=0.80: N.N clusters/game (mean size N.N)
  τ=0.85: N.N clusters/game (mean size N.N)
  τ=0.90: N.N clusters/game (mean size N.N)
  τ=0.95: N.N clusters/game (mean size N.N)

Phase A outcome: [CLEAR / DRIFT / MIXED — from the stdout summary]

Stockfish cross-reference: N/M rows populated from stockfish_evaluations_v2.csv.
σ and depth-gap columns: empty; Phase B deferred per §11.6.4/§11.6.5.

CSV at results/phase_operator_experiments/exp4_partitions.csv.
Pausing for researcher review and interpretation before PR.
```

---

## Scope guard

- Do not modify any file in `phase_operators/` that already exists. §11.3/§11.4/§11.5 substrate is frozen.
- Do not implement the σ estimator. It is a separate experiment; §11.6.4 is explicitly deferred.
- Do not re-run Stockfish at multiple depths. §11.6.5 is explicitly deferred.
- Do not tune τ or any parameter to force a clear outcome. Per §11.7.4, report what the data shows.
- Do not interpret the Phase A outcome beyond the stdout summary's one-line categorical label. The researcher interprets.
- Do not start §12 or any other experiment. Stop at Phase A completion.
- Do not open the PR. Hand off for researcher review first.

## Success criteria

Phase 1: three supplement patches applied, four grep checks pass, commit landed.

Phase 2: 
- `partition_detector.py` passes 7 unit tests.
- `partition_experiment.py` runs on the corpus without error. CSV exists at the default path with expected columns. Stockfish cross-reference columns populated for overlapping (game, ply) pairs. `sigma_local` and `stockfish_depth_gap` columns empty throughout.
- Stdout summary reports per-threshold cluster statistics and one-line Phase A outcome label.
- Three commits on `chess-spectral-phase-operator-11-6`. Handoff message printed. PR not opened.

If all pass, §11.6 Phase A data is collected, partition structure recorded as empirical data, cross-references honestly deferred with documented prerequisites, and the researcher has a clean Phase A outcome to interpret before deciding whether to commission the σ experiment and multi-depth Stockfish run for Phase B.
