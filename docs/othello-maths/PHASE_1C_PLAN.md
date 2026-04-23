# Phase 1c Plan — reversi-scripts integration

**Status:** planning / awaiting approval.
**Parent branch:** `main` (this is a new PR, not an amendment of PR #52).
**Target branch:** `othello-phase-1c-reversi-scripts-integration-v0.1.0`
**Depends on:** PR #52 merged (or the othello-maths Phase 0-2 + 1b
code it introduced).
**Blocked on:** nothing — everything in this plan is runnable without
the 20 GB figshare download.

## Why Phase 1c exists

Four probes from the Phase 1 hypothesis battery that went to
UNDETERMINED or PARTIAL can be upgraded now using artefacts from
[github.com/eukaryo/reversi-scripts](https://github.com/eukaryo/reversi-scripts).
This plan packages that upgrade as a discrete PR so reviewers see a
clean diff per concept.

Concretely, we intend to:

1. Independently validate our `OthelloBoard.legal_moves` against
   Takizawa's reference Python implementation.
2. Upgrade **§10.10 T3** (Shannon info per move) from UNDETERMINED
   to PASS or FAIL using the tournament move-frequency dictionary.
3. Use the 50-empty edax-knowledge CSV as a lightweight ground-truth
   anchor.
4. Upgrade **H9** (A₁ depth-gap transfer) from UNDETERMINED to
   PASS or FAIL using edax at depth 1 vs depth 20 — the direct
   analog of the chess §9h′ protocol which used Stockfish d1 vs
   d20 (**NOT** perfect play).
5. (Stretch) Evaluate whether our spectral observables or a future
   phase-space operator engine can be patched into edax as move-
   ordering or pruning heuristics with measurable performance
   gain.

Only items H9-strict (vs Takizawa's exact 20 GB perfect-play table)
and E8 (perfect-play spectral correlations) still need the
figshare download after this work lands.

---

## Sub-phase 1c.1 — Independent OthelloBoard validation

**Goal.** 100 % agreement between `research/othello_utils.py::
OthelloBoard.legal_moves()` and the Takizawa reference
(`reversi_misc.py`), across every position reachable in the Barcelona
EGP 2026 corpus (2184 positions) and a synthetic perturbation set of
~1000 random-play positions.

**Fetch.** Two small Python files: `reversi_misc.py` (12.5 KB) and
`reversi_player.py` (11.7 KB). Total 24 KB.

**Licensing.** Read `LICENSE` from the reversi-scripts repo (35 KB
file, probably GPL v3) and confirm compatibility with our GPL v3.
If compatible, inline-copy into `research/third_party/` with an
attribution header at the top of each file. If incompatible, invoke
their code via a sibling checkout directory; the repo stays external.

**Deliverables.**

- `research/third_party/reversi_misc.py` (copy-with-attribution, IF
  license allows) or `scripts/fetch_reversi_scripts.sh` (clone
  sibling).
- `research/cross_validate_othello_board.py --help` — argparse CLI
  with `--corpus`, `--synthetic-n`, `--seed`, `--fail-on-mismatch`.
  Runs both engines on every position; reports agreement count,
  per-position mismatches if any.
- `results/phase1c_cross_validation.json`.
- Notebook §1.5 paragraph: headline agreement rate (expected 100 %)
  plus any discrepancies with root-cause analysis.

**Effort.** 2–3 hours.

**Risk.** Low. If we find real disagreements the probe is *more*
valuable, not less — it means our `OthelloBoard` has a bug we need
to fix before anything downstream is trustworthy.

**Exit criterion.** Agreement rate ≥ 99.9 % (100 % expected). If
any genuine disagreement, fix `OthelloBoard` first, then retest.

---

## Sub-phase 1c.2 — §10.10 T3 Shannon information per move

**Goal.** Upgrade T3 from UNDETERMINED to CONFIRMED/FAILED with
numbers. For every played move in the Barcelona corpus,

    I_move = log2 |M(s)| - log2 P(chosen | empirical_freq)

where `|M(s)|` is the legal-move count (already in our per-ply CSV)
and `P(chosen | empirical_freq)` is the tournament-empirical
probability of the chosen move given the position.

**Fetch.** `opening_book_freq.csv.bz2` (24 MB compressed, probably
~100–200 MB uncompressed). Commit in-repo under
`dataset/reversi_scripts/opening_book_freq.csv.bz2`. Decompression
happens in the loader — no need to store the expanded form.

**Schema reverse-engineering.** Before writing the loader, read
`reversi_scripts/make_50_book.py` (3.1 KB) which likely emits this
CSV. Expected schema (inferred from filename and solver context):

    position_hash, move, count

or:

    bb_player, bb_opponent, move, count

where the position is represented as two 64-bit bitboards (one per
colour). If the schema is different, we adapt before committing to a
loader design.

**Deliverables.**

- `research/opening_book_loader.py --help` — `OpeningBookFreq` class
  exposing `probability(state, move) -> float | None` and `coverage()
  -> float` (fraction of game-tree positions with at least one entry).
- `research/shannon_info_runner.py --help` — compute I_move for
  every played ply in a corpus. Emits
  `results/phase1c_shannon_info.json` (aggregate) and
  `results/phase1c_shannon_per_move.csv` (per-ply).
- Correlations reported:
  - `Spearman(mean_I_per_game, |final_disc_diff|)` — does higher
    Shannon complexity track larger winning margins?
  - `Spearman(I_move, A1_minus_energy)` per ply — is A₁⁻ a
    spectral proxy for Shannon information?
  - `Spearman(I_move, n_legal_moves)` — sanity: decisions in
    positions with many legal moves carry more information.
- Notebook §2b.T3 paragraph with numbers and interpretation.

**Effort.** 4–6 hours: 1 hour schema inspection, 2 hours loader +
tests, 2 hours runner + correlations, 1 hour doc.

**Risk.** Medium. The opening book might cover only early-game
positions (hence the name "opening book"), in which case I_move is
undefined for midgame and endgame plies. Mitigation: report
`coverage()` explicitly; treat uncovered plies as NaN in the
aggregate; use `n_legal_moves` as a fallback uniform-policy baseline
for uncovered positions and note the distinction.

**Exit criterion.** T3 has numbers with a clear PASS/FAIL/PARTIAL
verdict; §10.10 T3 status in the chess notebook moves from
UNDETERMINED to a concrete status.

---

## Sub-phase 1c.3 — Edax 50-empty knowledge anchor

**Goal.** Use `empty50_tasklist_edax_knowledge.csv` (204 KB) as a
lightweight ground-truth anchor: for each Barcelona-corpus position
that happens to land at exactly 50 empty squares, look up edax's
static-eval knowledge and correlate it with our A₁⁻ energy.

**Pre-check.** Before building the full runner, count how many
Barcelona corpus positions land exactly at 50 empties (move 14 in a
60-move game). If < 20 matches across the 35 games, the correlation
is too noisy to be informative — in that case downgrade 1c.3 to a
single-sentence "insufficient overlap; test deferred" note and
skip the implementation.

**Fetch.** One small CSV (204 KB), committable as
`dataset/reversi_scripts/empty50_tasklist_edax_knowledge.csv`.

**Schema reverse-engineering.** Again read
`reversi_scripts/solve_one_e50_subproblem.py` (11 KB) for the exact
format. Expected: one row per 50-empty position with
`(bb_player, bb_opponent, predicted_eval)` or similar.

**Deliverables.**

- `research/edax_knowledge_anchor.py --help` — loads the CSV into
  a position-hash → eval dictionary; walks the Barcelona corpus;
  emits `phase1c_50empty_anchor.json` with match count and
  correlation.
- If match count ≥ 20: Spearman(A₁⁻ energy at 50-empties, edax
  knowledge). Else just the match count with a deferral note.
- Notebook §2b.H9-anchor paragraph (one-liner if insufficient,
  full result if enough matches).

**Effort.** 2–3 hours (including the pre-check).

**Risk.** Low. Worst case: insufficient overlap; we report that
and move on.

**Exit criterion.** Match count reported; correlation if ≥ 20
matches; otherwise deferral noted.

---

## Sub-phase 1c.4 — Edax d=1 vs d=20 → H9 surrogate (HEADLINE)

**Goal.** Direct Othello analog of chess §9h′:

    Spearman(A1_minus_energy, |d1_eval - d20_eval|)

Chess reported ρ = +0.452, p = 0.0005 on 55 positions with Stockfish.
Othello target: 55–200 positions with edax at the same depth
settings.

**Engine choice — key decision.**

- **Option A (recommended):** Upstream `abulmo/edax-reversi` pre-built
  binary (Windows / Linux releases available). Matches chess
  precedent of installing Stockfish separately.
- **Option B:** Compile Takizawa's modified edax from `Source.cpp`,
  `eval.cpp`, `misc.cpp`, `Header.hpp`, `Source_manyeval.cpp`,
  `Makefile` using MSYS2 / mingw-w64 on Windows or native gcc on
  Linux/WSL.

Option A saves 4–6 hours of build tooling and the modifications in
Option B are specifically for 36-empty solving, not general
deep-depth evaluation. **Recommendation: Option A.**

**Corpus and compute budget.**

- Default subsample: 200 positions sampled evenly across game phases
  (50 each at rho = 0.2, 0.4, 0.6, 0.8). Chess used 55 positions.
- Edax at depth 1 is sub-millisecond per position; depth 20 is
  ~1–10 seconds per position on a modern CPU. 200 × 10 s = 2000 s
  (~30 minutes) — feasible.
- Full Barcelona corpus (2184 positions × ~10 s each) = ~6 hours.
  Defer to Phase 1c-extension if subsample yields a strong signal.

**Deliverables.**

- `research/edax_wrapper.py --help` — subprocess bridge. Accepts a
  position string (standard Othello notation or bitboard), returns
  eval and best-move at requested depth. Configurable path to the
  edax binary via `--edax-path` or env var `EDAX_PATH`. Handles
  timeouts, parses the text protocol output robustly.
- `research/a1_depth_gap_runner.py --help` — sample positions from
  a corpus, call edax at d=1 and d=20, compute A₁⁻ energy, correlate.
  Emits `results/phase1c_a1_depth_gap.json` and
  `results/phase1c_a1_depth_gap_per_position.csv`.
- Headline correlations reported:
  - `Spearman(A1_minus_energy, |d1 - d20|)` vs chess +0.452
  - Partial ρ controlling for disc count, echoing chess §9h′ partial
- Notebook §2b.H9 paragraph with numbers and PASS/FAIL verdict
  against the +0.3 threshold from the original H9 specification.

**Effort.** Option A: 5–7 hours. Option B: 1–2 days.

**Risk.** Medium. Wrapper robustness (edax text protocol has edge
cases); compute-time budget; parsing edge cases. Mitigation:
smoke-test the wrapper on a 5-position set before committing to the
full 200.

**Exit criterion.** H9 status moves from UNDETERMINED to PASS /
FAIL / PARTIAL with a concrete Spearman correlation and p-value.

---

## Sub-phase 1c.5 (STRETCH) — Phase-space observable → edax integration

**Framing.** The original stretch ask: *"see if our phase space
operation evaluator can be patched into edax, assuming performance
is gained."* This is genuinely two tiers of work, with very
different prerequisites.

### Tier 1 — spectral-observable move ordering (runnable after 1c.4)

**Premise.** Even before the sequel phase-operator engine exists for
Othello, our existing Phase 1 / 1b spectral observables are
computable per-position:

- A₁⁻ magnetisation energy (correlates with disc density, E3)
- B₁ / B₂ energies (T2 — diagonal orbit runs ~12 % higher in
  tournament play)
- Sheaf λ₂ (correlates with legal-move count, E6)
- Fiber rank indicators (orbit vs directed)

Edax's move ordering already uses mobility, corner threats, parity
etc. — augmenting it with one of our spectral features is a minimal
one-call patch.

**Experiment.** Run edax in two configurations at fixed wall time
per move (say 1 s):

1. Stock move ordering.
2. Stock + spectral augmentation (add our A₁⁻ or B₁/B₂ delta as a
   weighted move-ordering term).

Measure:
- Reached search depth (higher = better ordering)
- Node count to depth-N (lower = better)
- Head-to-head win rate on a self-play tournament (300 games)

**Deliverables (Tier 1).**

- `patches/edax-spectral-moveorder.patch` — minimal diff against
  upstream edax adding a `--spectral-ordering` flag that calls out
  to a Python helper (or inlines a C port of A₁⁻ computation).
- `research/bench_edax_spectral.py --help` — runs the A/B
  configuration benchmarks and emits
  `results/phase1c_edax_bench.json`.
- Notebook §2b.stretch paragraph with the node-count delta and
  self-play win rate.

**Effort (Tier 1).** 1–2 days. The C-side code is small (A₁⁻ is
8 symmetry-partner sums plus squared norm, ~30 lines of C). The
harder part is the edax build with a patched move generator.

**Risk (Tier 1).** High that the effect is tiny or null. A₁⁻ is a
bulk-density proxy that edax's evaluator already knows implicitly
through disc count. B₁/B₂ delta is the novel part — if it helps, that
is a meaningful finding. **Null result is still valuable**: it
confirms that the spectral observables measure a *different* thing
from edax's evaluator, which is what §10.2 ("what fails" table)
predicted.

### Tier 2 — full phase-operator engine patched into edax (BLOCKED on sequel)

**Prerequisite.** The Othello phase-operator sequel prompt has
landed and `othello-spectral/python/othello_spectral/phase_operators/`
exists and is validated (analog of the chess §11.3 / §11.4
equivalence experiments).

**Premise.** The phase-space engine generates the legal-move set
using coprime cyclic phase arithmetic — NOT bitboards. The two
candidate wins:

1. **Raw move-generation speed.** Bitboard Othello is already
   extremely fast (< 1 microsecond per position). Beating it on
   speed with phase arithmetic is UNLIKELY — bitboards win on cache
   locality and register-width parallelism.
2. **Aliasing-horizon partition detection.** The phase-space
   analog of UTLP S4 (chess §11.6) detects spatial partitions in
   the legal-move set before full enumeration. Translated to edax,
   this could enable pruning of rays whose phase-tuples fall
   outside the current horizon — potentially saving search nodes
   per alpha-beta call.

**Experiment (Tier 2).** Same A/B structure as Tier 1, swapping in
the full phase-operator move generator instead of just a move-
ordering heuristic. Measure node counts at fixed depth and wall time
at fixed depth.

**Deliverables (Tier 2).**

- `patches/edax-phase-operator.patch` — diff replacing
  `generate_moves()` with the phase-operator equivalent, gated by
  a build-time flag.
- `research/bench_edax_phase_operator.py` — A/B benchmark.
- Notebook §2b.stretch-tier2 with speed / node-count results.

**Effort (Tier 2).** 2–5 days after the sequel phase-operator
engine exists. Dominated by C port of the phase-arithmetic core.

**Risk (Tier 2).** Medium-high. The structural hypothesis
(aliasing-horizon pruning accelerates edax) is interesting but
unproven. Null result is a clean falsification of one prediction of
the phase-operator framework.

### Stretch goal scope decision

**Recommendation:** Execute Tier 1 as part of this plan IF Phases
1c.1–1c.4 complete cleanly and time remains. Tier 2 is scoped
explicitly to *after* the sequel prompt lands — include only as a
roadmap note in the preflight doc.

---

## Execution order and decision gates

    1c.1  OthelloBoard cross-validation       (2-3 h,  low risk)
         Decision gate A: if any disagreement, fix OthelloBoard
         first, re-run; do not proceed to 1c.2 until 100 % match.

    1c.2  T3 Shannon info per move           (4-6 h,  medium risk)
         Decision gate B: if opening book coverage < 50 % of ply
         positions, split the probe: report I_move for covered
         positions; report uniform-policy baseline for uncovered.

    1c.3  50-empty edax-knowledge anchor     (2-3 h,  low risk)
         Decision gate C: if Barcelona corpus has < 20 positions at
         50 empties, downgrade to deferral note.

    1c.4  Edax d=1 vs d=20 H9 surrogate      (5-7 h,  medium risk)
         Decision gate D: smoke-test the edax wrapper on 5
         positions before committing to full 200.
         Decision gate E: if subsample shows |Spearman| > 0.3 at
         p < 0.01, expand to full Barcelona corpus; else land the
         subsample result and move on.

    1c.5  Spectral-observable edax patching  (STRETCH: Tier 1 only,
          1-2 d if time)

---

## Fetch plan

Files to bring into the repo:

| Path | Size | Purpose |
|---|---|---|
| `research/third_party/reversi_misc.py`                              | 12.5 KB | 1c.1 cross-validation |
| `research/third_party/reversi_player.py`                            | 11.7 KB | 1c.1 cross-validation |
| `dataset/reversi_scripts/opening_book_freq.csv.bz2`                 | 24 MB  | 1c.2 T3 |
| `dataset/reversi_scripts/empty50_tasklist_edax_knowledge.csv`       | 204 KB | 1c.3 anchor |

License check before copying: `reversi-scripts/LICENSE`. If GPL v3,
compatible with our project. If more restrictive, use fetch-on-
demand shell script rather than inline copy.

Not committed to repo:

- Edax binary (Option A) — user installs from upstream release at
  path pointed to by `EDAX_PATH` env var or `--edax-path` flag.
  Mirrors how chess-maths handles Stockfish.
- Modified edax source files (if we go with Option B) — fetched
  via `scripts/fetch_edax_takizawa.sh` on demand.

---

## Tooling conventions (MANDATORY for every CLI in this phase)

Every script added by Phase 1c MUST:

1. Use `argparse.ArgumentParser` with
   `formatter_class=argparse.RawDescriptionHelpFormatter`.
2. Include an `epilog="""examples:\n  ..."""` with 2-3 concrete
   invocations and a `notes:` paragraph explaining reading the
   output.
3. Give every argument a research-audience `help=` string. No
   placeholder bare arguments.
4. Call `_ensure_utf8_stdio()` from `othello_pgn_loader` before
   any print.
5. Accept a `--quiet` flag where appropriate.
6. Exit non-zero when a semantic failure occurs; exit zero for
   "task ran, results noted" even if the hypothesis failed.

This matches the chess-spectral CLI convention established in
commit `c009f23`.

---

## Git / PR shape

- **Branch:** `othello-phase-1c-reversi-scripts-integration-v0.1.0`
  off `main` (NOT off the PR #52 branch; assume PR #52 is merged
  first).
- **Single PR** covering 1c.1–1c.4 + Tier 1 of 1c.5 if reached.
  Split further only if the diff exceeds ~3 000 lines of code.
- **Commit structure:** one commit per sub-phase, with the
  structured `docs/othello-maths:` prefix matching chess precedent.
- **CHANGELOG.md:** the root CHANGELOG of this repo is for EMDR
  firmware. Follow the othello-maths convention: no root-CHANGELOG
  update; put the Phase 1c summary in the othello session summary
  file instead.
- **PR description:** reuse the commit-message-style summary
  from the Phase 1b PR comment; add explicit "needs edax binary
  installed" prerequisite line.

---

## Open decisions needing user confirmation before execution

1. **License compatibility on reversi-scripts.** I will read the
   LICENSE file and confirm GPL v3 compatibility BEFORE copying any
   file. If incompatible, pivot to fetch-on-demand. OK to do that
   silently, or do you want me to surface the license terms before
   proceeding?
2. **Commit the 24 MB bz2 in repo, or fetch script?** Default:
   commit. Alternative: fetch on demand. My recommendation: commit,
   for reproducibility.
3. **Edax binary path convention.** Default: `EDAX_PATH` env var
   or `--edax-path` CLI flag (matches how chess-maths handles
   Stockfish). OK?
4. **Corpus subsample for 1c.4.** Default: 200 positions evenly
   across game phases. Alternative: full Barcelona corpus (2184
   positions) at ~6 h walltime. Recommend: subsample first.
5. **Stretch Tier 1 in scope for this PR, or follow-up?** Default:
   in scope if time remains after 1c.1–1c.4. Alternative: push
   stretch to a separate PR.
6. **Stretch Tier 2 (full phase-operator patch into edax) scope.**
   Confirmed out of scope for this PR — requires the sequel phase-
   operator prompt to land first.

---

## What this plan is NOT

- Not the sequel phase-operator engine for Othello. That is its
  own prompt, to be written against `OTHELLO_PHASE_OP_PREFLIGHT.md`.
- Not a full WTHOR empirical analysis. §10.10 T4 and T5 still
  require a WTHOR .wtb parser and are scoped to Phase 1d or later.
- Not a performance optimisation pass on our own research code.
  `consolidated_tests.py` and `game_trajectory_tests.py` are fine
  as-is for the sample sizes involved.
- Not an attempt to reproduce Takizawa's 36-empty solve. We
  consume their outputs (knowledge tables, opening book); we do
  not re-solve.
