# phase_operators

Reference implementation of the §11.2 phase operators, the §11.3 empty-board
equivalence experiment, and the §11.4 occupation-aware Solutions B and C from
[../PHASE_OPERATOR_SUPPLEMENT.md](../PHASE_OPERATOR_SUPPLEMENT.md).

## Contents

### §11.3 substrate (unobstructed)

- `phase_operators.py` — operators on Z_640 (stdlib only).
- `phase_to_coords.py` — the injection φ: [0,8)² → Z_640 and its inversion.
- `equivalence_check.py` — CLI that validates §11.2 operators against
  python-chess empty-board legal moves (§11.3). Depends on `chess` 1.11.2.

### §11.4 occupation-aware (sliding + blockers)

- `occupation_field.py` — phase-native `dict[int, int]` occupation field;
  shared K/N/P localized filter.
- `occupation_aware_b.py` — Solution B (batch ray + set-intersection truncation).
- `occupation_aware_c.py` — Solution C (sequential step with early halt).
- `occupation_equivalence_check.py` — CLI that samples positions from a corpus
  and compares A (python-chess) vs B vs C.

### Tests

- `tests/` — unittest battery covering all modules (no pytest dep).

## Run

```sh
python -m unittest discover                       # all tests
python equivalence_check.py                       # §11.3, writes CSV
python equivalence_check.py --fail-on-mismatch    # exit 1 on any mismatch

python occupation_equivalence_check.py            # §11.4 on 100 positions
python occupation_equivalence_check.py --n-positions 500 --seed 7
```

Expected §11.3 stdout: `§11.3 complete: 416/416 pairs equivalent`.
Expected §11.4 stdout: `B matches C: 1153/1153 (100.00%)` (primary sanity check).

Default CSV paths (both under `../results/phase_operator_experiments/`, which
is gitignored — regenerate locally):
- `exp1_equivalence.csv` (§11.3)
- `exp2_occupation_equivalence.csv` (§11.4)

## TODO — committed results artifact

Because `docs/chess-maths/results/*/` is gitignored, the CSVs produced by
these CLIs are not checked into the repo. Headline numbers end up in commit
messages and PR descriptions only, which is brittle. Eventually we should
emit a small Markdown summary alongside each CSV (e.g.
`docs/chess-maths/phase_operator_results.md`) that captures the
reproducible top-line results for each experiment so the repo carries an
auditable record without committing the bulky per-row CSVs.
