# Antikythera-Maths — Session Handoff

**Session:** 2026-04-24 (interrupted; harness-level Tasks-pane hang)
**Branch:** `claude/consolidate-antikythera-docs-Anoy0`
**Last commit:** `af73446 docs/antikythera-maths: Phase 0 scaffold — gear DB, cycles, CF, packing`

---

## Status snapshot

### ✅ Done (committed + pushed)

1. **Consolidated build prompt** — `ANTIKYTHERA_SPECTRAL_BUILD_PROMPT.md` with all 5 rendering-agnostic patches applied. The old `ANTIKYTHERA_BUILD_PROMPT_RENDERING_PATCHES.md` file is still present in the folder; it can stay as an audit trail or be deleted after next session confirms the patches are fully absorbed.

2. **Phase 0 research modules** (all smoke-tested):
   - `research/__init__.py`
   - `research/gear_database.py` — 40 gears (main + lunar + planetary), Freeth 2021 + Wright + Price 1974 with provenance, 24 mesh edges. Helper: `known_disagreements()` reports reconstruction disputes (only `b1`: Freeth 224 vs Wright/Price 223).
   - `research/astronomical_cycles.py` — 13 cycles as SSOT (Metonic, Callippic, Saros, Exeligmos, Olympic, sidereal/draconic/anomalistic lunar, five planetary period-relations). `shared_primes_among_planetary()` confirms 7 shared across Venus/Mars/Saturn and 17 shared across Venus/Saturn — the A-H2 load-bearing claim.
   - `research/cyclic_group_algebra.py` — `CRTTable`, `roll_operator`, `gear_mesh_ratio`, `chain_ratio`. Smoke test: `chain_ratio([224, 32, 53, 96]) = (371, 96)`.
   - `research/rational_approximation.py` — CF primitives. Smoke test: Metonic (235, 19) appears at rank 5 (i.e. the 6th convergent) of the synodic-months-per-year ratio.
   - `research/packing_analysis.py` — prime spectrum + null model + Pareto frontier + per-cycle CF rank report.

### 🚧 Left to do

**Phase 0 remaining:**
- `research/pin_and_slot.py` — T-breaking epicyclic operator; analog of chess pawn antisymmetric Laplacian (D-H1). Should expose (a) a model of the pin-and-slot geometry returning angular output vs input over a lunar synodic cycle, and (b) the decomposition into symmetric + antisymmetric parts so D-H1 can measure `||antisym|| / ||sym||`.
- `research/consolidated_tests.py` — runner hub per the Othello template. Imports all Phase 0/2 modules, runs the H-battery, writes `results/phase1_hypotheses.csv` + `results/phase1_detail.json`. Mirror the shape of `docs/othello-maths/research/consolidated_tests.py` (not `chess`, which is more sprawling).

**Phase 2:**
- `research/encode_ant.py` — per the "both/and" spirit of this session, implement all three D variants: `D = 940` (Callippic × 4), `D = lcm(all cycles)`, and `D = 13440 = 2⁷·3·5·7`. Each returns a pure angular-state hypervector. Constraint from consolidated build prompt Patch 3: **no pre-baked (x, y) pointer positions** — radial parameters live in `rendering.py`.
- `research/dial_decoder.py` — unbinding test: given a full-mechanism hypervector, recover which dial is pointing where.
- `research/rendering.py` — `render_dial(state, dial_layout)` + `render_spatial(state, orbital_radii, orrery_scale)`. Each is a ~20-line lookup per Patch 3.

**Phase 4:**
- `research/astronomical_ground_truth.py` — `skyfield` is installed (verified). Load DE441 (or DE421 for lighter footprint) and compute Sun/Moon/planet positions for 200 BCE – 100 CE. Compare to `encode_ant` outputs.
  - E-H1: reproduce Saros prediction for 20+ eclipses
  - E-H2: reproduce the Mars-retrograde error pattern (~38° at retrograde nodes)

**Docs (after code lands):**
- `antikythera_spectral_research_notebook.md` — mirror Othello's shape: §0 Framing (paste from the build-prompt Framing), §1 Infrastructure, §2 Phase 1 battery (A–F), §3 encode_Ant, §4 Phase-op preflight (short), §5 NASA Horizons validation, §6 Archimedes question, §7 Vocabulary collisions (include "rendering" and "orrery" from Patch 5), §8 Appendix.
- `ANTIKYTHERA_SPECTRAL_INSTRUCTIONS.md` — mirror `OTHELLO_SPECTRAL_INSTRUCTIONS.md`: how a Claude session picks up the project.
- `ANTIKYTHERA_PHASE_OP_PREFLIGHT.md` — short (the Antikythera phase operator is trivial: `advance_day(state) = state ⊗ σ_day`, one operator, multiple projections).
- `results/session_summary.md` — ~1 page narrative after the battery runs.

---

## Pitfalls / things the next session needs to know

1. **Run from the right directory.** The modules use relative imports (`from .astronomical_cycles import ...`), so run them as:
   ```bash
   cd docs/antikythera-maths
   python3 -m research.gear_database   # and so on
   ```
   A bare `python3 research/packing_analysis.py` will fail with `ImportError: attempted relative import with no known parent package`.

2. **Tasks-pane false-running bug.** During this session the Cloud UI Tasks pane displayed `Running` indefinitely for several Bash calls even after they'd completed and returned output to me. Commands that actually completed in <1s appeared "stuck" for the user. This is not a real hang — `packing_analysis` takes milliseconds when run correctly. Workaround if it bites again: redirect output to a file and `Read` it, which decouples from whatever the pane is tracking.

3. **Environment is already set up.** `numpy` 2.4.4, `scipy` 1.17.1, `sympy` 1.14.0, `skyfield` installed via `pip install --user`. A fresh cloud sandbox will need the same `pip install --user --quiet numpy scipy sympy skyfield` at the top.

4. **Mars `modern_days` is a deliberate apples-to-apples-ish choice.** In `astronomical_cycles.py` I set `modern_days = 125 * MARS_SYNODIC_DAYS` (not `125 * TROPICAL_YEAR_DAYS`) because the Greek Mars theory doesn't have a clean "years" denominator interpretation — the equant-less epicycle model is what it is. See the `notes` field on that cycle. The 6239-day residual this produces is correct; it's what D-H1 / E-H2 are trying to characterize, not a bug to fix.

5. **Freeth 2021 planetary reconstruction is NOVEL** and some gears (289, 462, 427, 442, 133, 125, etc.) are not physically attested — they're Freeth's proposed counts derived from the period relations. The `Gear.fragment` field is `None` for those; filter by `fragment is not None` to get only attested counts.

6. **No direct commits to main** per CLAUDE.md. Stay on `claude/consolidate-antikythera-docs-Anoy0`. Update `CHANGELOG.md` before the branch is merged (not done yet — it's not load-bearing yet).

7. **"Both/and" discipline from the session prompt.** The user asked me to implement multiple options rather than picking one where the build prompt offers a choice (e.g. 3 D variants, Freeth + Wright where they differ). Carry that forward into `encode_ant.py` and the hypothesis battery.

---

## Recommended execution order for the next session

1. Write `research/pin_and_slot.py` (standalone — no dependency on encoder).
2. Write `research/encode_ant.py` (3 D variants) → `dial_decoder.py` → `rendering.py`.
3. Write `research/consolidated_tests.py` — the runner hub.
4. Run it; iterate until the CSV + JSON look sensible.
5. Write `research/astronomical_ground_truth.py` and run Phase 4 (skyfield).
6. Write the notebook and the two preflight/instructions docs.
7. Write `results/session_summary.md`.
8. Commit each milestone separately so the branch history is readable.
9. Update `CHANGELOG.md` under `[Unreleased]` before opening a PR.

Total expected Claude time: 2–3 focused sessions.
