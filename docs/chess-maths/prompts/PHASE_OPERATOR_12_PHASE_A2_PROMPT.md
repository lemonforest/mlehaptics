# Claude Code: §12 Phase A2 — evaluation refinements (same branch)

## Context

§12 Phase A produced an AMBIGUOUS result across three corpora:

```
Derivation A (k=5): max |ρ| = 0.161-0.179 across corpora
Derivation B:       max |ρ| = 0.172-0.332; 0.332 on drnykterstein
                    king-moves does NOT replicate on other corpora
Derivation C:       NaN (cosine of two near-zero vectors = degenerate)
```

The researcher's review identified two evaluation bugs that prevent
the AMBIGUOUS label from being a fair test of the derivations:

1. **A's k=5 did not test A.** Variance-explained on δ_king at k=5
   is only 7-11% mean across rows. The first five eigenvectors of
   the attack Laplacian carry almost none of the king-impulse
   energy; attack-line structure lives in higher-frequency modes.
   A's |ρ|=0.161 tested "the smoothest 5 of 64 modes carry a little
   signal," not "the king-centered Laplacian eigenchannel carries
   signal." The latter is untested.

2. **C's cosine metric did not measure what the corpus contains.**
   Every Carlsen middlegame position has a king that is not under
   direct attack, so `derivation_c_channel` is all-zeros on every
   one of the 3393 rows. The cosine between two zero vectors is 0.0
   by convention, producing zero variance in sim_c and NaN Spearman.
   The corpus DOES have is_check_unsafe variance (pinned pieces,
   square-vacation-exposes-king moves), but C's before-to-after
   *cosine* strips the relevant magnitude information out through
   normalization. C's *derivation* is correct; the scalar summary
   wrapped around it assumed variance-on-both-sides that the corpus
   does not provide.

**Both fixes are to the evaluation harness, not to the derivations.**
The §11.7.4 rule ("do not tune operators to match results") applies
to changing A's, B's, or C's definitions. Changing the *k* at which
A is measured (a parameter A already accepts) and changing the
scalar summary wrapped around C (a new function that reuses the
frozen `derivation_c_channel`) is fixing measurement bugs, not
tuning derivations.

**Derivation B is NOT refined.** Its current evaluation is
methodologically sound. Its AMBIGUOUS result across three corpora
is the honest answer. Trying alternative B signals (column-sum,
weighted adjacency, per-piece-type decomposition) to see if any
crosses 0.3 on replication would be §11.7.4-forbidden
threshold-tuning. B stays as-is.

**Branch state.** `chess-spectral-phase-operator-12-phase-a` sits at
7 commits, unpushed, no PR. Phase A2 is a continuation, not a new
experiment — one or two additional commits on the same branch,
re-run the evaluation, update the handoff.

## Design discipline

Phase A2 may do:
- Expose `k` as a CLI parameter to the evaluation harness.
- Add new scalar summary functions for Derivation C that reuse the
  frozen `derivation_c_channel`.
- Update `process_csv` to compute the new scalars alongside existing
  ones.
- Update `print_summary` to report the new metrics.
- Re-run evaluation across all three corpora (same three input CSVs
  used for Phase A's three-corpus extension).

Phase A2 may NOT do:
- Change `derivation_a_channel` math (the Laplacian construction,
  the eigendecomposition, the projection onto δ_king). The k
  parameter was always there; only its default and CLI exposure
  change.
- Change `derivation_c_channel` math (the 16-dim feature layout,
  the per-component definitions, the occupation-field consultation).
  Only the scalar-summary function wrapped around it changes.
- Modify Derivation B in any way.
- Try alternative signals, alternative reductions, alternative
  weightings on any derivation to search for a threshold crossing.
- Delete, overwrite, or amend the existing Phase A output CSVs.
  Phase A2 emits new CSVs with distinct filenames; the Phase A
  record stays on disk as part of the research trail.
- Open a PR.

## Phase 1 — Supplement §12.7 update

Locate §12.7 in `PHASE_OPERATOR_SUPPLEMENT_12.md` (the evaluation
section). After the existing text, add a new subsection §12.7.1
documenting the Phase A2 refinements:

```
### §12.7.1 Phase A2 — evaluation refinements

Phase A's three-corpus extension produced an AMBIGUOUS categorical
result with two evaluation-harness bugs that prevented a clean test
of Derivations A and C:

**Derivation A at k=5 did not test the eigenchannel hypothesis.**
Variance-explained on δ_king at k=5 was 7-11% across the three
corpora. The first five eigenvectors of the attack Laplacian carry
almost none of the king-impulse energy; attack-line structure lives
in higher-frequency modes. A's measured |ρ|=0.161-0.179 tested
"the smoothest 5 of 64 modes carry some signal," not the full
eigenchannel hypothesis. Phase A2 re-runs Derivation A at k=16 (and
reports variance-explained at that k as a diagnostic). If
variance-explained at k=16 is still below 0.8, the CLI accepts
--k-for-a values up to 32; the first k that achieves ≥0.8
variance-explained on a representative position sample is the
honest test of A.

**Derivation C's cosine metric did not measure corpus-relevant
change.** Every sampled position in the three corpora has a king
not under direct attack, so `derivation_c_channel` returns
all-zeros on every row, and cosine of two zero vectors collapses to
0.0. C's feature vector is correct; the cosine summary wrapped
around it was the wrong reduction for corpora where both sides of
the transition have zero-magnitude C vectors. Phase A2 adds two
alternative scalar summaries alongside cosine:

- `delta_c`: L2 norm of (C_after - C_before). Nonzero whenever the
  move changes any component of the king-attack vector, even when
  both endpoints are near-zero.
- `mag_c_after`: L2 norm of C_after alone. Captures the post-move
  attack density directly; its correlation with is_check_unsafe is
  expected to be near-1 by construction (is_check_unsafe is
  literally "some component of C_after is positive"), and serves
  as a sanity check that the evaluation pipeline recovers the
  tautological baseline.

The three C metrics together let us distinguish:

- "C's derivation does not carry signal" (all three near zero)
- "C's derivation carries signal but cosine is the wrong metric"
  (cosine near zero, delta_c and/or mag_c_after above threshold)
- "C's evaluation pipeline has a bug beyond the metric choice"
  (mag_c_after fails to recover the near-1 tautological baseline)

**Derivation B is not refined.** Its current three-corpus
evaluation is methodologically sound. Its ambiguous result (single
corpus crosses 0.3 on a single slice; does not replicate on other
corpora) is the honest research finding. Per §11.7.4, alternative
B signals are not explored in Phase A2.

Phase A2 emits new CSVs with `_a2` suffix on disk; Phase A CSVs
remain unchanged as part of the research record.
```

Grep verification after Phase 1:

```bash
grep -c "§12.7.1 Phase A2" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md   # expect 1
grep -c "delta_c" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md             # expect 1 or more
grep -c "mag_c_after" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md         # expect 1 or more
grep -c "variance-explained" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md  # expect 2 or more
```

Commit Phase 1 alone:
`§12.7.1 supplement: Phase A2 evaluation refinements (A at k=16, C with delta and magnitude)`

## Phase 2 — Code changes

### Change 1 — `derivation_c_operator.py`: add two scalar functions

Append to the existing module (do not modify `derivation_c_channel`
or `derivation_c_similarity`):

```python
def derivation_c_delta(board_before: chess.Board,
                       move: chess.Move) -> float:
    """L2 norm of (C_after - C_before). Complementary metric to the
    cosine similarity: handles the common case where both C_before
    and C_after are near-zero vectors (king in no danger on either
    side of the move) by measuring the displacement directly rather
    than through a normalized inner product.

    Returns a non-negative float. Zero means the king-attack vector
    is unchanged by the move; positive values scale with the
    magnitude of change in attack density.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    b = derivation_c_channel(board_before)
    a = derivation_c_channel(board_after)
    return float(np.linalg.norm(a - b))


def derivation_c_after_magnitude(board_before: chess.Board,
                                 move: chess.Move) -> float:
    """L2 norm of C(board_after) alone. A tautological baseline:
    is_check_unsafe is defined as 'some component of C_after is
    positive,' so this metric's correlation with is_check_unsafe
    should be near 1.0 by construction. Its role in Phase A2 is
    to verify the evaluation pipeline recovers that baseline; any
    meaningful finding from A or delta_c must beat it along a
    dimension other than raw post-move attack density.

    Returns a non-negative float.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    a = derivation_c_channel(board_after)
    return float(np.linalg.norm(a))
```

### Change 2 — `evaluate_encoder.py`: expose k-for-a + compute new C scalars + update summary

Make the following modifications:

**2a. CLI argument for k.**

Add to `main()`:

```python
parser.add_argument(
    "--k-for-a", type=int, default=16,
    help="Number of eigenvectors to use for Derivation A "
         "(default: 16; k=5 was the Phase A setting and is "
         "retained for direct comparison but requires passing "
         "--k-for-a 5 explicitly to reproduce).")
```

Thread it through `process_csv` signature.

**2b. Output columns — add three, parameterize one.**

Update `OUTPUT_COLUMNS_EXTRA`:

```python
OUTPUT_COLUMNS_EXTRA = [
    "similarity_a",
    "similarity_b_concat",
    "similarity_b_A1", "similarity_b_A2", "similarity_b_B1",
    "similarity_b_B2", "similarity_b_E",
    "similarity_c",
    "delta_c",              # Phase A2: L2(C_after - C_before)
    "mag_c_after",          # Phase A2: |C_after|
    "var_exp_a",            # Phase A2: parameterized; was var_exp_a_k5
    "timing_a_ns", "timing_b_ns", "timing_c_ns",
]
```

Note the column rename: `var_exp_a_k5` → `var_exp_a`. The actual
k is recorded as CLI metadata (printed in the summary header) so
downstream consumers of the CSV can interpret the column.

**2c. Inside `process_csv` inner loop:**

Replace the current C computation block:

```python
t0 = time.perf_counter_ns()
sim_a = derivation_a_similarity(board, move, k=k_for_a)
t1 = time.perf_counter_ns()
per_irrep = derivation_b_similarity(board, move)
sim_b_concat = derivation_b_similarity_concat(board, move)
t2 = time.perf_counter_ns()
sim_c = derivation_c_similarity(board, move)
dlt_c = derivation_c_delta(board, move)
mag_c = derivation_c_after_magnitude(board, move)
t3 = time.perf_counter_ns()
var_exp = variance_explained(board, k=k_for_a)
```

Update `out_row.update(...)` with the three new/renamed columns:

```python
"similarity_c": f"{sim_c:.12f}",
"delta_c": f"{dlt_c:.12f}",
"mag_c_after": f"{mag_c:.12f}",
"var_exp_a": f"{var_exp:.12f}",
```

And update the `enriched` dict:

```python
enriched.append({
    ...
    "sim_c": sim_c,
    "dlt_c": dlt_c,
    "mag_c": mag_c,
    "var_exp": var_exp,
    ...
})
```

Add the imports for the two new C functions:

```python
from .derivation_c_operator import (
    derivation_c_channel, derivation_c_similarity,
    derivation_c_delta, derivation_c_after_magnitude,
)
```

**2d. `print_summary` — report all three C metrics + variance-explained at the CLI's k.**

Replace the Derivation C block with:

```python
# Derivation C — three scalar summaries of the same 16-dim feature
print("  Derivation C (attack operator from king's phase, "
      "16-dim feature):")
for metric_name, metric_key, metric_label in [
    ("sim_c", "sim_c",   "cosine similarity"),
    ("dlt_c", "dlt_c",   "L2 delta (C_after - C_before)"),
    ("mag_c", "mag_c",   "|C_after| (tautological baseline)"),
]:
    print(f"    [{metric_label}]")
    print(f"      all transitions:   {_fmt(rep(enriched, metric_key))}")
    for name, letter in piece_slices:
        sub = _slice_by_piece(enriched, letter)
        print(f"      {name+' moves:':<19}"
              f"{_fmt(rep(sub, metric_key))}")
    print(f"      captures:          "
          f"{_fmt(rep(cap_rows, metric_key))}")
    print(f"      non-captures:      "
          f"{_fmt(rep(non_rows, metric_key))}")
print("")
```

Update the Derivation A header to print the actual k (not DEFAULT_K):

```python
print(f"  Derivation A (king-centered Laplacian, k={k_for_a}):")
```

And print a variance-explained interpretation hint:

```python
mean_var_exp = float(np.mean(var_exps)) if var_exps else 0.0
var_label = "faithful" if mean_var_exp >= 0.80 else \
    ("partial" if mean_var_exp >= 0.50 else "inadequate")
print(f"    variance explained (mean over all rows, k={k_for_a}): "
      f"{100 * mean_var_exp:.1f}% ({var_label})")
```

Threshold interpretations:
- ≥80%: k is adequate; A's correlation is a fair test of the
  eigenchannel hypothesis.
- 50-79%: partial; A's correlation is informative but incomplete.
- <50%: inadequate; re-running at higher k is recommended.

**2e. Update the Phase A decision block to consider all three C metrics.**

In the `all_slices_c` construction and the best-of computation, add
both new C metrics:

```python
all_slices_c = []
for metric_name, metric_key in [
    ("C cosine",    "sim_c"),
    ("C delta",     "dlt_c"),
    ("C |C_after|", "mag_c"),
]:
    all_slices_c.append((f"all ({metric_name})", enriched, metric_key))
    all_slices_c.append((f"captures ({metric_name})", cap_rows,
                        metric_key))
    all_slices_c.append((f"non-captures ({metric_name})", non_rows,
                        metric_key))
    for n, l in piece_slices:
        all_slices_c.append((f"{n} moves ({metric_name})",
                            _slice_by_piece(enriched, l), metric_key))
```

Same `best_c = max(...)` pattern works on the expanded list.

**IMPORTANT discipline point for interpretation.** The decision
logic should report `mag_c_after`'s correlation separately from the
viability decision. It is near-1 by construction and its high
correlation does NOT count as §12 signal — it is the tautological
baseline. The decision uses the best |ρ| across A, B, and C-cosine +
C-delta ONLY (not C-after-magnitude).

Implement this by flagging mag_c specifically:

```python
# Exclude C |C_after| from the viability decision (tautological baseline).
all_slices_for_decision = (
    all_slices_a + all_slices_b +
    [s for s in all_slices_c if "|C_after|" not in s[0]]
)
best_for_decision = max(
    ((abs_rho(rows, key), name, "A/B/C-sim/C-delta")
     for name, rows, key in all_slices_for_decision),
    key=lambda t: t[0])
```

Report `mag_c_after`'s correlation as a separate "Tautological
baseline" line below the decision:

```python
mag_best = max(((abs_rho(rows, key), name) for name, rows, key
                in all_slices_c if "|C_after|" in name[0]),
               key=lambda t: t[0])
print(f"  Tautological baseline check:")
print(f"    mag_c_after max |ρ|: {mag_best[0]:.3f} ({mag_best[1]})")
if mag_best[0] < 0.7:
    print(f"    WARNING: tautological baseline should be near 1.0; "
          f"{mag_best[0]:.3f} suggests evaluation bug.")
else:
    print(f"    Tautological baseline recovered as expected.")
```

If the tautological baseline fails to recover (max |ρ| below 0.7 on
`mag_c_after`), halt and report — this indicates a bug in the
evaluation pipeline, not a research finding.

### Change 3 — CSV output filenames

Default output path should be `exp5_king_attack_correlation_a2.csv`
(with `_a2` suffix) to preserve the Phase A outputs unchanged. The
CLI's `--out` argument governs the actual path; the three-corpus
re-run commands (below) use `_a2` suffix explicitly.

Do NOT overwrite the existing Phase A CSVs.

## Phase 3 — Run against all three corpora

Run the evaluation CLI three times:

```bash
cd docs/chess-maths

# 1. drnykterstein (Carlsen N=10)
python -m king_attack_encoder.evaluate_encoder \
    --input-csv results/phase_operator_experiments/exp3_phase_similarity.csv \
    --out results/phase_operator_experiments/exp5_king_attack_correlation_a2.csv \
    --k-for-a 16

# 2. ashchess (FM blitz N=50)  -- assumes the §11.5 CSV exists for this corpus;
#                                 if not, note in handoff and skip.
python -m king_attack_encoder.evaluate_encoder \
    --input-csv results/phase_operator_experiments/exp3_phase_similarity_ashchess.csv \
    --out results/phase_operator_experiments/exp5_king_attack_correlation_a2_ashchess.csv \
    --k-for-a 16

# 3. fishtest (engines N=50)  -- same note on availability.
python -m king_attack_encoder.evaluate_encoder \
    --input-csv results/phase_operator_experiments/exp3_phase_similarity_hf.csv \
    --out results/phase_operator_experiments/exp5_king_attack_correlation_a2_hf.csv \
    --k-for-a 16
```

Inspect the first run's `variance_explained` report. If below 0.80
mean across rows, re-run with `--k-for-a 32` and record both results
in the handoff. If 0.80 is still not reached at k=32, flag this as
a structural finding: the attack Laplacian's eigenvectors do not
concentrate on the king's neighborhood, which is itself informative
about what Derivation A can and cannot measure.

**On missing §11.5 CSVs for ashchess / fishtest.** The Phase A
handoff references three separate CSVs (`exp5_king_attack_correlation.csv`,
`_ashchess.csv`, `_hf.csv`). These were produced by running the
Phase A evaluate_encoder against three §11.5 input CSVs. Verify
the input CSVs exist before running; if the ashchess or fishtest
§11.5 CSV does not exist, Phase A2 cannot reproduce the three-corpus
analysis on those corpora and the handoff should state so explicitly
rather than silently running on one corpus only.

## Phase 4 — Commit and handoff

Two additional commits on the existing branch
`chess-spectral-phase-operator-12-phase-a`:

1. `§12.7.1 supplement + code: Phase A2 evaluation refinements (A at k=16, C with delta/magnitude)`
2. `§12 Phase A2 run: three-corpus re-evaluation with refined metrics`

The second commit includes any new CSV outputs if they fit under
1 MB each (Phase A's were ~971 KB); otherwise leave CSVs on disk
and reference paths in the handoff.

Do NOT open the PR. Print handoff:

```
Branch chess-spectral-phase-operator-12-phase-a updated with Phase A2.
Three-corpus re-evaluation with refined metrics complete.

Previous Phase A state preserved; Phase A2 outputs have _a2 suffix.

Derivation A (king-centered Laplacian, k=16):
  Variance explained (mean across rows):
    drnykterstein: XX.X% (<adequate/partial/inadequate>)
    ashchess:      XX.X%
    fishtest:      XX.X%
  Max |ρ(similarity_a, is_check_unsafe)|:
    drnykterstein: X.XXX (<slice>)
    ashchess:      X.XXX (<slice>)
    fishtest:      X.XXX (<slice>)
  [If variance-explained <80% at k=16, note re-run at k=32 and its numbers]

Derivation B (D4 decomposition, unchanged from Phase A):
  [Re-state Phase A numbers unchanged; no re-run needed]

Derivation C — three metrics:
  cosine similarity (Phase A baseline):
    [three corpora × best slice; previously NaN]
  L2 delta (C_after - C_before) (Phase A2):
    drnykterstein: X.XXX (<slice>)
    ashchess:      X.XXX
    fishtest:      X.XXX
  |C_after| (tautological baseline, Phase A2):
    drnykterstein: X.XXX (expected near 1.0)
    ashchess:      X.XXX
    fishtest:      X.XXX
  Tautological baseline check: <PASS|WARNING>

Phase A2 decision (excluding tautological C-magnitude):
  Best durable |ρ| across three corpora:
    <derivation>, <metric>, <slice>: X.XXX / X.XXX / X.XXX
  Categorical: <VIABLE | AMBIGUOUS | VALIDATED NULL>

"Durable" here means |ρ| > 0.3 on all three corpora (not just max).
If a single-corpus |ρ| > 0.3 does not replicate on other corpora,
the finding is AMBIGUOUS per §11.6.6.1's three-corpus protocol, not
VIABLE.

Pairwise cosines (first corpus only, 50 sampled positions):
  cos(A, B): +X.XX   cos(A, C): +X.XX   cos(B, C): +X.XX

Per-call timings (first corpus):
  A: XXXX µs  B: XXXX µs  C: XXX µs

Commits on branch (N total, not pushed, no PR):
  <existing 7 Phase A commits>
  <sha>  §12.7.1 supplement + code: Phase A2 evaluation refinements
  <sha>  §12 Phase A2 run: three-corpus re-evaluation

Pausing for researcher review. No PR opened.
```

## Scope guard

- Do not modify `derivation_a_channel`, `derivation_a_similarity`,
  `variance_explained`. The k parameter was always accepted; only
  its default in the CLI changes.
- Do not modify `derivation_c_channel` or `derivation_c_similarity`.
  Only ADD the new `derivation_c_delta` and
  `derivation_c_after_magnitude` functions.
- Do not modify `derivation_b_d4.py`. B stays at its Phase A
  evaluation exactly.
- Do not modify `attack_graph.py`.
- Do not modify any file under `phase_operators/` or `chess_spectral/`.
- Do not overwrite Phase A output CSVs. Phase A2 emits new files
  with `_a2` suffix.
- Do not try alternative signals / weightings for any derivation to
  search for a threshold crossing. §11.7.4 applies.
- Do not open the PR.

## Success criteria

Phase 1: §12.7.1 subsection added to `PHASE_OPERATOR_SUPPLEMENT_12.md`;
four grep checks pass.

Phase 2: `derivation_c_operator.py` has two new public functions that
reuse `derivation_c_channel`; `evaluate_encoder.py` accepts `--k-for-a`
CLI flag, threads it through `process_csv`, computes delta_c and
mag_c_after per row, emits them as new CSV columns, reports all three
C metrics in the stdout summary, renames `var_exp_a_k5` → `var_exp_a`.
Existing tests in `king_attack_encoder/tests/` still pass.

Phase 3: CLI runs cleanly on all three §11.5 CSVs (or cleanly on the
subset available with explicit notes on missing corpora). Output CSVs
emitted with `_a2` suffix. Variance-explained at k=16 reported per
corpus; if <80% mean, k=32 re-run executed and reported.

Phase 4: two commits added to existing branch; handoff printed with
actual numbers; decision categorized as VIABLE / AMBIGUOUS /
VALIDATED NULL per durable-three-corpus criterion; PR not opened.

If the tautological `mag_c_after` baseline fails to recover (max
|ρ| < 0.7 across any corpus), halt, do not emit the viability
decision, and report the evaluation-pipeline bug instead.

Per §11.7.4, if Phase A2 still produces AMBIGUOUS or VALIDATED NULL,
do not commission a Phase A3 search for refinements. Two evaluation
bugs were worth fixing once. A third round would be threshold-tuning
in all but name.
