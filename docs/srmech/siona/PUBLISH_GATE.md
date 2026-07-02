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
- [ ] structured operands (floats / Mat / Vec / HV / kwargs — F1009 scope was int/bytes/list)
- [ ] failed-run → next-candidate recovery loop (ERR is already captured into memory)
- [ ] kernel generality hand-off (multi-step / non-linear → srmech `dispatch.infer` axis)
- [ ] within-family disambiguation re-rank (bundle vs bundle_resolve; F1008's open lever)
- [ ] bag-regression tests in `siona/tests/` (the F1004/F1008/F1010 incidents as fixtures)
- [ ] UDHR parallel-invariant run (Bislama board vs English board — matching IR digest; public-domain text)
- [ ] exercise the egyptian_tla board (local, 22k rows) — read-independent structural checks
- [ ] operator-board swap test (a second-language TOML descriptor; router unchanged)
- [ ] `siona.infer` test suite green under the venv pytest
- [ ] README + CHANGELOG final pass; version SSOT agreement (pyproject / __init__ / profile toml)

## Standing constraints
- TestPyPI-first, always; clean tag = human-only production gate.
- Never squash-merge. The wheel ships mechanism, not knowledge (PKG1_DECISION).
