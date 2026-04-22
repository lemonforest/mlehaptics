# Claude Code: §12 Phase A2 — turn-flip wrapper fix (expanded scope)

## Context

Phase A2's tautological-baseline check halted the re-run when
`derivation_c_after_magnitude`'s correlation with `is_check_unsafe`
failed to recover the near-1.0 baseline the metric is designed to
produce by construction. The diagnosis: **the C wrappers never flip
`board.turn` on the post-move board before computing the channel.**
Python-chess's `board.push(move)` flips `board.turn` to the opponent;
subsequent consultation of `board.turn` (via `board.king(board.turn)`
or `not board.turn`) then selects the wrong king / wrong attacker
color. The correct pattern — established in
`phase_operators/phase_check_detection.move_leaves_king_in_check` —
flips `board.turn` back before the post-move analysis:

```python
board.push(move)
board.turn = not board.turn    # <-- essential flip
result = phasecast_is_check(board)
board.turn = not board.turn    # <-- restore (only needed if board is reused)
```

**The researcher confirms the bug is NOT limited to the C wrappers.**
The same pattern appears in all three derivations:

- `derivation_a_laplacian.derivation_a_similarity` — consumes
  `derivation_a_channel(board_after)`, which calls
  `attack_graph.king_square(board)` → `board.king(board.turn)`. After
  push without flip, returns opponent's king, not mover's king.

- `derivation_b_d4.derivation_b_similarity` and
  `derivation_b_similarity_concat` — consume `derivation_b_channels
  (board_after)`, which calls `attack_adjacency(board)` with
  `opp_color = not board.turn`. After push without flip, `opp_color`
  identifies the mover, so the adjacency measures mover's outgoing
  attacks instead of the opponent's.

- `derivation_c_operator.derivation_c_similarity`,
  `derivation_c_delta`, `derivation_c_after_magnitude` — consume
  `derivation_c_channel(board_after)` which calls `board.king
  (board.turn)`. Same bug as A.

**Six functions total.** All need the one-line fix.

**Significance of the bug.** The entire Phase A three-corpus decision
matrix — including the methodological-catch narrative ("B's 0.332 on
drnykterstein didn't replicate") — was computed on post-move boards
where A and C queried the opponent's king and B queried mover's
outgoing attacks. Those are all the wrong measurements for
`is_check_unsafe` (which asks about the mover's king). The three-
corpus protocol still did its job by exposing non-replication, but
the *quantity* being measured was not the one we intended. Fresh
numbers are needed before any §12.10 interpretation is valid.

## Design discipline

This is a **wrapper-layer fix**, same discipline as the Phase A2
`--k-for-a` exposure and the addition of `derivation_c_delta` /
`derivation_c_after_magnitude`. The frozen objects are:

- `derivation_a_channel`, `variance_explained` — unchanged.
- `derivation_b_channels`, `attack_row_sum_signal` — unchanged.
- `derivation_c_channel` — unchanged.
- `attack_graph.attack_adjacency`, `attack_laplacian`, `king_square`
  — unchanged.
- Phase operator imports — unchanged.

What changes:

- Six `*_similarity*` wrapper functions each get one line added:
  `board_after.turn = not board_after.turn` after the push.
- One regression test per derivation pinning the expected post-flip
  behavior.
- §12.7.1 supplement gets a short addendum documenting the bug and
  fix for the research record.
- Three-corpus re-run with corrected wrappers; fresh §12.10.1
  writeup.

Per §11.7.4, the derivations themselves are not tuned. This is the
same kind of correction as fixing C's cosine metric — an evaluation-
pipeline bug, caught by a tautological baseline that was specifically
designed to catch it, now being repaired.

## Phase 1 — Code fix (six functions)

### Change 1 — `derivation_a_laplacian.py::derivation_a_similarity`

OLD (around lines 55-64):
```python
def derivation_a_similarity(board_before: chess.Board,
                            move: chess.Move,
                            k: int = DEFAULT_K) -> float:
    """Cosine similarity between Derivation A encodings before/after a
    move. Returns a float in [-1, 1]; 0.0 when either side has zero
    norm (degenerate king-absent positions)."""
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    a_before = derivation_a_channel(board_before, k=k)
    a_after = derivation_a_channel(board_after, k=k)
```

NEW:
```python
def derivation_a_similarity(board_before: chess.Board,
                            move: chess.Move,
                            k: int = DEFAULT_K) -> float:
    """Cosine similarity between Derivation A encodings before/after a
    move. Returns a float in [-1, 1]; 0.0 when either side has zero
    norm (degenerate king-absent positions).

    board.turn is flipped on the post-move board so that the
    mover's king (not the opponent's) remains the analysis target
    after the push. See PHASE_OPERATOR_SUPPLEMENT_12.md §12.7.1
    addendum for the bug history.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    board_after.turn = not board_after.turn
    a_before = derivation_a_channel(board_before, k=k)
    a_after = derivation_a_channel(board_after, k=k)
```

### Change 2 — `derivation_b_d4.py::derivation_b_similarity`

Add the turn-flip line after the push. Same docstring addendum about
§12.7.1.

### Change 3 — `derivation_b_d4.py::derivation_b_similarity_concat`

Same fix.

### Change 4 — `derivation_c_operator.py::derivation_c_similarity`

Same fix.

### Change 5 — `derivation_c_operator.py::derivation_c_delta`

Same fix.

### Change 6 — `derivation_c_operator.py::derivation_c_after_magnitude`

Same fix.

## Phase 2 — Regression tests (one per derivation)

Add one test to each of `test_derivation_a.py`, `test_derivation_b.py`,
and `test_derivation_c.py`. The test uses a constructed FEN where the
mover's king and opponent's king have *measurably different* post-
move attack environments — specifically, where `is_check_unsafe` is
True for the mover (mover's king attacked after move) but the
opponent's king remains attack-free.

### Test FEN (shared across the three regression tests)

```
FEN: k7/8/8/4r3/4Q3/8/8/4K3 w - - 0 1
Move: e4d4 (white queen off the pinned e-file)

Setup:
  - White king on e1
  - White queen on e4 (pinned by black rook on e5 to white king)
  - Black rook on e5
  - Black king on a8 (safely out of the action)

After Qe4d4:
  - White king on e1 is now attacked by black rook on e5 through
    the cleared e-file. is_check_unsafe = True.
  - Black king on a8 has no attackers. The only white pieces are
    king (e1) and queen (d4); neither attacks a8.

With correct turn-flip (fix applied):
  - derivation_*_channel(board_after) queries the mover (white)
    king on e1. Attack density is non-zero (rook-ray hit at k=4).
  - derivation_c_after_magnitude > 0.

Without the turn-flip (buggy):
  - derivation_*_channel(board_after) queries the opponent (black)
    king on a8. No attackers. All-zero channel.
  - derivation_c_after_magnitude == 0.

The tests assert the FIX behavior.
```

### Test for `derivation_a`

```python
def test_similarity_uses_mover_king_after_move(self):
    """Regression test for the §12.7.1 turn-flip fix.

    Constructs a position where the mover's king IS attacked after
    the move (is_check_unsafe) but the opponent's king is NOT. The
    Derivation A channel computed on the post-move board must
    reflect the mover's king's neighborhood, not the opponent's.

    Before the fix, derivation_a_similarity consulted board.turn
    AFTER push without flipping, picking up the opponent's king.
    """
    fen = "k7/8/8/4r3/4Q3/8/8/4K3 w - - 0 1"
    move = chess.Move.from_uci("e4d4")
    board = chess.Board(fen)

    # Compute the reference post-move channel manually with
    # explicit turn-flip — this is what the wrapper SHOULD produce.
    board_after = board.copy(stack=False)
    board_after.push(move)
    board_after.turn = not board_after.turn
    expected_after_channel = derivation_a_channel(board_after, k=DEFAULT_K)

    # And the pre-move channel for the full reference cosine.
    expected_before_channel = derivation_a_channel(board, k=DEFAULT_K)
    norm_b = float(np.linalg.norm(expected_before_channel))
    norm_a = float(np.linalg.norm(expected_after_channel))
    expected_sim = (float(np.dot(expected_before_channel,
                                 expected_after_channel)) / (norm_b * norm_a)
                    if norm_b > 0 and norm_a > 0 else 0.0)

    actual_sim = derivation_a_similarity(board, move, k=DEFAULT_K)
    self.assertAlmostEqual(actual_sim, expected_sim, places=10,
        msg="derivation_a_similarity must flip board.turn on the "
            "post-move board; the mover's king is the analysis "
            "target, not the opponent's.")
```

### Test for `derivation_b`

Analogous; use `derivation_b_similarity_concat` as the wrapper and
`derivation_b_channels` as the reference. Construct the concatenated
320-dim vector manually with explicit turn-flip and compare.

### Test for `derivation_c`

Tightest version because the tautological baseline is so clean:

```python
def test_after_magnitude_measures_mover_king(self):
    """Regression test for the §12.7.1 turn-flip fix.

    derivation_c_after_magnitude is designed as a tautological
    baseline: |C_after| must be non-zero whenever the move leaves
    the MOVER's king attacked (is_check_unsafe=True). If the
    wrapper queries the opponent's king instead, this baseline
    fails.
    """
    fen = "k7/8/8/4r3/4Q3/8/8/4K3 w - - 0 1"
    move = chess.Move.from_uci("e4d4")
    board = chess.Board(fen)

    mag = derivation_c_after_magnitude(board, move)
    self.assertGreater(mag, 0.0,
        "Mover's king (white e1) is attacked after Qd4 clears the "
        "e-file; |C_after| must be positive. A value of 0.0 means "
        "the wrapper is querying the opponent's king (black a8) "
        "instead, indicating the turn-flip fix has regressed.")

    # Also pin the exact value: rook ray from e1 hits e5 at k=4,
    # density = 1/4 in the -row direction component.
    board_after = board.copy(stack=False)
    board_after.push(move)
    board_after.turn = not board_after.turn
    expected_channel = derivation_c_channel(board_after)
    expected_mag = float(np.linalg.norm(expected_channel))
    self.assertAlmostEqual(mag, expected_mag, places=10)
    # Sanity: the -row component (index 1) carries the rook attack
    self.assertAlmostEqual(expected_channel[1], 0.25, places=10)
```

Also add an analogous test for `derivation_c_delta` and
`derivation_c_similarity` pinning the same FEN through those
wrappers.

### Run tests

```bash
cd docs/chess-maths
python -m unittest discover king_attack_encoder.tests -v
```

All existing tests must still pass; six new tests (two for C: delta
+ similarity + after_magnitude = three; plus one each for A and B)
are added. Total new tests: 3 for C, 1 for A, 1 for B = 5 new.
Plus the full suite continues to pass.

## Phase 3 — Supplement §12.7.1 addendum

Append to §12.7.1 in `PHASE_OPERATOR_SUPPLEMENT_12.md`:

```markdown
### §12.7.1.1 Turn-flip wrapper fix

Phase A2's tautological-baseline check (|C_after| correlation with
`is_check_unsafe` should be near 1.0 by construction) halted the
three-corpus re-run when the baseline failed on drnykterstein. The
diagnosis was a missing `board.turn` flip in all six similarity
wrappers across Derivations A, B, and C: after `board.push(move)`,
python-chess flips `board.turn` to the opponent, and the subsequent
call to `derivation_*_channel(board_after)` queries the wrong king
(for A and C) or wrong attacker color (for B). The correct pattern —
established in `phase_operators/phase_check_detection.
move_leaves_king_in_check` — flips `board.turn` back before the
post-move channel computation.

The fix is one line per wrapper: `board_after.turn = not
board_after.turn` after the push. The channel functions themselves
(`derivation_a_channel`, `derivation_b_channels`,
`derivation_c_channel`) and the underlying `attack_graph` primitives
are unchanged.

Consequence for the research record: the original Phase A three-
corpus numbers (B's 0.332 single-corpus crossing, A's 0.161-0.179
across corpora, C's NaN) were computed on wrong-side measurements.
The three-corpus protocol still detected non-replication of B, but
the quantity being measured was not the one the derivation was
designed to produce. Phase A2 (post-fix) supplies the fresh three-
corpus matrix that §12.10.1 interprets.

The tautological-baseline design pattern is preserved as a reusable
check for any future evaluation harness: any derivation whose
correlation with its target is provably near 1.0 by construction
should be included and asserted, to catch exactly this class of
wrapper-layer bug before it contaminates interpretation.
```

Grep verification:

```bash
grep -c "§12.7.1.1 Turn-flip wrapper fix" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md   # expect 1
grep -c "tautological-baseline design pattern" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md   # expect 1
```

Commit Phase 1-3 together (fix + tests + supplement) as one atomic
commit:

`§12.7.1.1 wrapper fix: turn-flip in all six similarity wrappers (A/B/C); regression tests`

## Phase 4 — Three-corpus re-run at k=16

Run the evaluation CLI on each of the three §11.5 input CSVs:

```bash
cd docs/chess-maths

python -m king_attack_encoder.evaluate_encoder \
    --input-csv results/phase_operator_experiments/exp3_phase_similarity.csv \
    --out results/phase_operator_experiments/exp5_king_attack_correlation_a2.csv \
    --k-for-a 16

python -m king_attack_encoder.evaluate_encoder \
    --input-csv results/phase_operator_experiments/exp3_phase_similarity_ashchess.csv \
    --out results/phase_operator_experiments/exp5_king_attack_correlation_a2_ashchess.csv \
    --k-for-a 16

python -m king_attack_encoder.evaluate_encoder \
    --input-csv results/phase_operator_experiments/exp3_phase_similarity_hf.csv \
    --out results/phase_operator_experiments/exp5_king_attack_correlation_a2_hf.csv \
    --k-for-a 16
```

**Halt condition — tautological baseline.** After the drnykterstein
run, inspect the stdout summary for the `mag_c_after` maximum |ρ|
across slices. It must be ≥ 0.7. If it is not, halt before running
the other two corpora and report the remaining bug. (The baseline
should now recover cleanly; if it doesn't, there's another layer of
bug the first round didn't catch.)

**Escalation condition — variance-explained.** Inspect the
variance-explained mean for Derivation A at k=16 on the first
corpus. If it is still below 0.80 ("partial" or "inadequate" per
the §12.7.1 threshold definitions), re-run the same corpus at
`--k-for-a 32`. Report both the k=16 and k=32 numbers in the handoff.

**Do not** continue escalating to k=48 or k=64. If k=32 still does
not reach 0.80, that is itself a structural finding about the
attack Laplacian's eigenvector concentration — the king's local
neighborhood does not live in the low-frequency subspace — and
belongs in the §12.10.1 write-up as a finding rather than as a
reason to keep searching.

## Phase 5 — §12.10.1 write-up

After the three-corpus re-run completes, append §12.10.1 to
`PHASE_OPERATOR_SUPPLEMENT_12.md` using the template below. Do
NOT write interpretation beyond the three-outcome categorization
the data directly supports. The researcher writes the narrative.

Template:

```markdown
## §12.10.1 Phase A2 result — fresh three-corpus matrix (post turn-flip fix)

Run parameters: same three §11.5 input CSVs as Phase A; Derivation
A at k=16 (variance-explained XX.X% mean); Derivations B and C
unchanged in their channel definitions. Tautological baseline
`mag_c_after` recovered at max |ρ| = X.XXX across the three corpora.

| Corpus | n transitions | A max |ρ| | A slice | B max |ρ| | B slice | C-cosine max | C-delta max |
|---|---|---|---|---|---|---|---|
| drnykterstein | NNNN | X.XXX | <slice> | X.XXX | <slice> | X.XXX | X.XXX |
| ashchess      | NNNN | X.XXX | <slice> | X.XXX | <slice> | X.XXX | X.XXX |
| fishtest      | NNNN | X.XXX | <slice> | X.XXX | <slice> | X.XXX | X.XXX |

**Durability criterion.** A crossing of the |ρ| > 0.3 viability
threshold is durable iff it replicates across all three corpora,
not just one (per §11.6.6.1 three-corpus protocol).

**Categorical outcome:** <VIABLE | AMBIGUOUS | VALIDATED NULL>

<VIABLE>: Derivation <X> crosses durably. The HDC family carries
king-attack signal when the encoder is targeted to king-attack
structure. §11.5's null was specific to `encode_640`. Phase B
(assembly) is unblocked pending researcher review.

<AMBIGUOUS>: No derivation crosses durably. Single-corpus crossings
(if any) do not replicate. §12 records the AMBIGUOUS label and the
stable per-irrep / per-channel sub-findings (from Phase A's
structural observations) as secondary results.

<VALIDATED NULL>: All derivations below 0.1 durably across three
corpora. The §11.5 null generalizes: the HDC construction pattern
does not naturally produce king-attack signal through any of the
three principled derivations tested. This is a real structural
finding about encoder family construction.

[Fill in which category and which slice/derivation, from the
actual numbers.]

**Pairwise cosines (first corpus, 50 sampled positions):**
cos(A, B) = X.XX; cos(A, C) = X.XX; cos(B, C) = X.XX.

**Per-call timings (first corpus):** A XXXX µs; B XXXX µs; C XXX µs.

**Research record note.** The original Phase A matrix was computed
on post-move boards where `board.turn` was not flipped, causing A
and C to query the opponent's king and B to measure the mover's
outgoing attacks. The three-corpus protocol detected the non-
replication of B's single-corpus crossing even on the buggy
measurements; the tautological-baseline check then exposed the bug
itself. The §12.7.1.1 fix restored the measurements to what the
derivations were designed to compute. The original buggy CSVs
(`exp5_king_attack_correlation*.csv` without `_a2` suffix) remain
on disk as part of the research trail.
```

Commit Phase 4-5 together:

`§12.10.1 Phase A2 post-fix result: three-corpus matrix at k=16 (k=32 if escalated)`

## Phase 6 — Handoff

Print the handoff message:

```
Branch chess-spectral-phase-operator-12-phase-a updated.
§12.7.1.1 turn-flip wrapper fix applied across six similarity
wrappers (A: 1; B: 2; C: 3). Five regression tests added; total
tests in king_attack_encoder/ now NN, all passing.

Tautological baseline recovered: mag_c_after max |ρ| = X.XXX
(expected ≥ 0.7; was 0.0 pre-fix due to opponent-king bug).

Phase A2 three-corpus result at k=16 (variance-explained XX.X%):

  Derivation A: max |ρ| per corpus = X.XXX / X.XXX / X.XXX
  Derivation B: max |ρ| per corpus = X.XXX / X.XXX / X.XXX
  Derivation C cosine: X.XXX / X.XXX / X.XXX
  Derivation C delta:  X.XXX / X.XXX / X.XXX
  [If variance-explained was below 0.80 at k=16, also report k=32.]

Categorical outcome (per §12.10.1): <VIABLE | AMBIGUOUS | VALIDATED NULL>

Commits added to branch:
  <sha>  §12.7.1.1 wrapper fix + regression tests + supplement addendum
  <sha>  §12.10.1 Phase A2 post-fix three-corpus matrix

Total branch commits: NN. Not pushed, no PR.

Pausing for researcher review.
```

## Scope guard

- Do not modify `derivation_a_channel`, `variance_explained`,
  `derivation_b_channels`, `attack_row_sum_signal`,
  `derivation_c_channel`, `attack_graph.*`, or any phase_operators
  module. Only the six similarity wrappers change.
- Do not change the test FEN. It is chosen to create a clean
  mover-vs-opponent-king distinction; other positions may work
  but the prompt specifies this one to keep the test documentation
  consistent.
- Do not delete or overwrite the Phase A CSVs (without the `_a2`
  suffix). They remain as the "buggy measurement" trail.
- Do not try alternative B signals, alternative k values beyond
  k=16 → k=32 escalation, or alternative metrics for C beyond the
  three already defined. §11.7.4 applies.
- Do not interpret the §12.10.1 outcome beyond the three
  categorical labels. Numbers + category only; researcher writes
  the narrative.
- Do not open the PR.

## Success criteria

Phase 1: six one-line fixes applied; `git diff` shows exactly six
added lines of the form `board_after.turn = not board_after.turn`
(plus docstring addenda).

Phase 2: five new regression tests pass; full test suite passes.
Each test asserts either the exact expected similarity/magnitude
value OR `assertGreater(mag, 0.0)` with a clear regression message.

Phase 3: §12.7.1.1 subsection appended to the supplement; two grep
checks pass.

Phase 4: CLI runs cleanly on drnykterstein with `mag_c_after` max
|ρ| ≥ 0.7; proceeds to ashchess and fishtest. Variance-explained
reported; k=32 escalation executed if needed.

Phase 5: §12.10.1 appended with the full three-corpus matrix,
durability criterion applied, categorical outcome determined
strictly from the numbers.

Phase 6: handoff message printed with actual numbers; branch sits
at its new HEAD; PR not opened.

If the tautological baseline still fails after the fix (max |ρ|
< 0.7), halt before the ashchess/fishtest runs and report. That
would indicate a deeper bug in the evaluation pipeline not covered
by the turn-flip fix.
