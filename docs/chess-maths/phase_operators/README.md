# phase_operators (research CLIs)

Research CLIs and experiment harnesses from §11.3–§11.6 of
[../PHASE_OPERATOR_SUPPLEMENT.md](../PHASE_OPERATOR_SUPPLEMENT.md).

## Where the library lives

The validated library — phase arithmetic on Z_640, φ/invert lookups,
occupation-aware move generation (Solutions A/B/C), castling, and
phase-native `is_check` — now ships as the
`chess_spectral.phase_operators` subpackage of the
[chess-spectral](../chess-spectral/python/) package (v1.2.0+).

```sh
pip install -e ../chess-spectral/python/   # editable install for dev
# or
pip install chess-spectral                 # published wheel
```

Then from any Python:

```python
from chess_spectral.phase_operators import (
    phi, P_rook, P_knight,
    occupation_aware_moves_c,
    available_castles,
    phasecast_is_check,
)
```

Unit tests for the library moved with it; see
[../chess-spectral/python/tests/phase_operators/](../chess-spectral/python/tests/phase_operators/).

## What stays here

This directory retains only the research CLIs and §11.5/§11.6
experiment-scoped modules — things tied to specific supplement
sections rather than library API:

### §11.3 / §11.4 equivalence CLIs

- `equivalence_check.py` — validates §11.2 operators against
  python-chess empty-board legal moves (§11.3). Produces
  `exp1_equivalence.csv`. Expected stdout:
  `§11.3 complete: 416/416 pairs equivalent`.
- `occupation_equivalence_check.py` — samples positions from a corpus
  and runs all four channels (A, B, C, python-chess) with pairwise
  agreement rates and per-solution timings (§11.4). Expected stdout
  on 100 positions, seed=42:
  ```
  A matches python-chess: 1153/1153 (100.00%)
  B matches C:            1153/1153 (100.00%)   ← primary phase-native sanity
  B matches python-chess: 1086/1153  (94.19%)   ← residual is moves-into-check (§11.5)
  ```
- `benchmark_solutions.py` — wall-time benchmark with
  `--filter {pseudo,legal,both}` for apples-to-apples A/B/C
  comparison (§11.4.5).

### §11.5 phase-tuple similarity

- `phase_similarity.py` — library-style module for path-2 cosine
  similarity on pre/post-move `encode_640` vectors. Research-scoped:
  §11.5.6 validated its null result; kept here as the experiment
  artifact rather than packaged surface.
- `similarity_experiment.py` — CLI emitting the §11.5.4 CSV.

### §11.6 partition detection

- `partition_detector.py` — library-style module for §11.6.3 clustering
  on game trajectories. Research-scoped: §11.6.6.1 recorded a
  three-corpus DRIFT null on `encode_640`; kept here as the
  experiment artifact.
- `partition_experiment.py` — CLI emitting the §11.6 CSV.

### Tests (for the experiment-scoped modules only)

- `tests/test_phase_similarity.py`
- `tests/test_partition_detector.py`

## Run

All CLIs require the `chess_spectral` package installed:

```sh
python equivalence_check.py
python equivalence_check.py --fail-on-mismatch

python occupation_equivalence_check.py
python occupation_equivalence_check.py --n-positions 500 --seed 7

python benchmark_solutions.py --help

python similarity_experiment.py --help
python partition_experiment.py --help

python -m unittest discover tests    # the 2 research-CLI tests
```

Default CSV paths (under `../results/phase_operator_experiments/`,
gitignored — regenerate locally):

- `exp1_equivalence.csv` (§11.3)
- `exp2_occupation_equivalence_abc.csv` (§11.4)
- `exp3_phase_similarity.csv` (§11.5)
- `exp4_partitions.csv` (§11.6)

## Why the split?

The chess-spectral package is a library for spectral chess encoding;
it treats the phase-space move generator + check detector as stable
API (`chess_spectral.phase_operators.*`). The artifacts here are the
research machinery that produced the supplement's validation
numbers — reproducibility harnesses, not library surface. They stay
outside the package to keep the pypi distribution lean and the
research trail legible.
