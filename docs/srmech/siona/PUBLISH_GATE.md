# siona 0.1.0rc1 — PUBLISH GATE (do these AT ready-to-publish, not before)

Recorded 2026-07-02 per user direction, so building/hardening continues unblocked. **None of these
executes until the rc1 cut is declared ready** ("almost there or all the way there").

## Repo / publisher moves (at publish time)
1. **PyPI trusted-publisher target → its own `lemonforest/siona` repo** (both indices,
   project=`siona`): move `siona-publish.yml` there; re-register the trusted publisher on
   TestPyPI + PyPI to point at `lemonforest/siona`; the package source tree moves with it.
2. **Update `[project.urls]`** (Homepage/Repository/Issues) from mlehaptics paths to
   `lemonforest/siona` in `pyproject.toml`.
3. **The siona RESEARCH NOTEBOOK stays in `lemonforest/mlehaptics`** — RTD is already set up there
   and serves the research-notebook family; only the *package* moves. The package README links back
   to the notebook on RTD.
4. **Release cut = its OWN PR** (never PR #687), then manual tag `siona-v0.1.0rc1` → TestPyPI
   (per `project_siona_package_takeover_unmirror` + `feedback_always_rc_first`). Clean
   `siona-v0.1.0` → PyPI is the human gate.
5. **Clean-venv verification OUTSIDE the source tree** before any tag (namespace-shadowing gotcha).

## Hardening backlog (before declaring ready)
- [ ] paraphrase intent-frames per board (asks outside the declared frames fall to `continue`)
- [x] name ALIAS/morphology — DONE by pre-measurement (F1017): PREFIX-COVER chosen (Gram unchanged 0.271, eval kept, alias 3/5); byteglyph vecs REJECTED read-independently (+0.130 cross-talk AND worse alias)
- [x] code-switching (user question, F1017): merged bilingual board routes mixed input 5/5; the attested 'save' homograph drops to grounding (operators declared; colliding declarations -> operands decide); notes store UNDOCTORED (the len-1 tokenizer filter was an English-privilege artifact dropping Bislama 'i' — fixed)
- [ ] rung-SUPERPOSED homographs in merge_boards (F1018: replace drop-to-grounding with superpose-and-select on the elliptic ladder + low-margin ask-fallback; 12/12 in the probe)
- [ ] operator ACCRETION with guards (F1018: fixed role-frame, measured word->role maps; threshold k + consistency + un-accrete path) — also prospectively fills F1016's unattested slots by usage
- [ ] byteglyph NOTE-encoding pre-measurement (cross-language content recall: 'luksave water' vs stored 'wota' — F1017's measured boundary; memory-note surface is smaller than the tool index, needs its own Gram cost measurement)
- [ ] conflict-fallback policy for sparse-content homographs ('save wota' -> low-margin ask or configurable default)
- [ ] structured operands (floats / Mat / Vec / HV / kwargs — F1009 scope was int/bytes/list)
- [x] failed-run recovery — DONE (F1015: fit-positive candidates in order, attempts recorded)
- [ ] kernel generality hand-off (multi-step / non-linear → srmech `dispatch.infer` axis)
- [x] within-family re-rank — DONE (F1015: whole-index name-coverage promotion)
- [x] bag-regression tests — DONE (F1015: fixtures pinned, suite green)
- [x] UDHR parallel-invariant run — DONE (F1015: 3–8× chance, zero dictionary; IR layer proven load-bearing)
- [x] egyptian_tla board exercised — DONE (F1015: distinct .386 + deterministic)
- [x] operator-board swap test — DONE (F1015 synthetic testlang full session; F1016 REAL Bislama board from UDHR-attested vocab, 2/2 tests)
- [ ] `siona.infer` test suite green under the venv pytest
- [ ] README + CHANGELOG final pass; version SSOT agreement (pyproject / __init__ / profile toml)

## Standing constraints
- TestPyPI-first, always; clean tag = human-only production gate.
- Never squash-merge. The wheel ships mechanism, not knowledge (PKG1_DECISION).
