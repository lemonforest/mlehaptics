# phase_operators

Reference implementation of the §11.2 phase operators, the §11.3 empty-board
equivalence experiment, and the §11.4 occupation-aware Solutions A / B / C
(with §11.4.3.1 P_castle) from
[../PHASE_OPERATOR_SUPPLEMENT.md](../PHASE_OPERATOR_SUPPLEMENT.md).

## Contents

### §11.3 substrate (unobstructed)

- `phase_operators.py` — operators on Z_640 (stdlib only).
- `phase_to_coords.py` — the injection φ: [0,8)² → Z_640 and its inversion.
- `equivalence_check.py` — CLI that validates §11.2 operators against
  python-chess empty-board legal moves (§11.3). Depends on `chess` 1.11.2.

### §11.4 occupation-aware (sliding + blockers + castling)

- `occupation_field.py` — phase-native `dict[int, int]` occupation field;
  shared K/N/P localized filter.
- `occupation_aware_a.py` — Solution A (phase candidate set ∩ python-chess
  `legal_moves`; fourth cross-validation channel, timing baseline).
- `occupation_aware_b.py` — Solution B (batch ray + set-intersection truncation).
- `occupation_aware_c.py` — Solution C (sequential step with early halt).
- `castling.py` — §11.4.3.1 P_castle composite operator; 4-entry CASTLES
  dict built from φ() at module load, `available_castles(board)` predicate,
  unioned into the king output of all three solutions.
- `occupation_equivalence_check.py` — CLI that samples positions from a corpus
  and runs all four channels (A, B, C, python-chess) with pairwise agreement
  rates and per-solution timings.
- `benchmark_solutions.py` — dedicated wall-time benchmark for A/B/C with
  warmup, repeats, percentiles (p50/p95/p99), per-piece filtering, and
  `--filter {pseudo,legal,both}` to compare all three solutions at matched
  correctness (apples-to-apples). Run `python benchmark_solutions.py --help`
  for usage.

### Tests

- `tests/` — unittest battery covering all modules (no pytest dep).
  69 tests total: §11.3 operators + inversion, §11.4 occupation field,
  A/B/C sanity fixtures, P_castle.

## Run

```sh
python -m unittest discover                       # all tests
python equivalence_check.py                       # §11.3, writes CSV
python equivalence_check.py --fail-on-mismatch    # exit 1 on any mismatch

python occupation_equivalence_check.py            # §11.4 on 100 positions
python occupation_equivalence_check.py --n-positions 500 --seed 7
```

Expected §11.3 stdout: `§11.3 complete: 416/416 pairs equivalent`.
Expected §11.4 stdout (100 positions, seed=42):
```
A matches python-chess: 1153/1153 (100.00%)
B matches C:            1153/1153 (100.00%)   ← primary phase-native sanity
B matches python-chess: 1086/1153  (94.19%)   ← residual is moves-into-check (§11.5)
```

Default CSV paths (both under `../results/phase_operator_experiments/`, which
is gitignored — regenerate locally):
- `exp1_equivalence.csv` (§11.3)
- `exp2_occupation_equivalence_abc.csv` (§11.4 four-way A/B/C/python-chess)
- `exp2_occupation_equivalence.csv` (older §11.4 B/C-only output, preserved
  for reference during the A-channel integration).
