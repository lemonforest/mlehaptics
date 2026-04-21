# phase_operators

Reference implementation of the §11.2 phase operators and the §11.3 equivalence
experiment from [../PHASE_OPERATOR_SUPPLEMENT.md](../PHASE_OPERATOR_SUPPLEMENT.md).

## Contents

- `phase_operators.py` — operators on Z_640 (stdlib only).
- `phase_to_coords.py` — the injection φ: [0,8)² → Z_640 and its inversion.
- `equivalence_check.py` — CLI that validates §11.2 operators against
  python-chess empty-board legal moves (§11.3). Depends on `chess` 1.11.2.
- `tests/` — unittest battery. `python -m unittest discover`.

## Run

```sh
python -m unittest discover
python equivalence_check.py                # writes CSV, prints summary
python equivalence_check.py --fail-on-mismatch   # exit 1 on any mismatch
```

Expected stdout: `§11.3 complete: 416/416 pairs equivalent`.
Default CSV path: `../results/phase_operator_experiments/exp1_equivalence.csv`.
