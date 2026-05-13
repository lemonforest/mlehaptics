# srmech v0.1.0 — TestPyPI release procedure

**Status:** Pending. Triggers after **Task #197 Phase 4 PR merges to `main`**.

This file documents the post-merge release sequence for the first TestPyPI
publication of the `srmech` package. The TestPyPI step is autonomous (no
human-in-loop); the subsequent PyPI step is human-in-loop and requires
explicit authorization.

---

## §1. Predecessor state

Before this procedure runs, the following must be true:

- Task #197 Phase 2 PR (#380) has merged to `main` — bootstraps the
  `docs/srmech/python/` Python package, `pyproject.toml` (version `0.1.0`),
  `srmech.amsc.*` framework copy, CI workflows
  (`srmech-ci.yml`, `srmech-publish.yml`, `srmech-autotag.yml`), and the
  initial 48 in-isolation tests.
- Task #197 Phase 3 PR (#381) has merged to `main` — ephemerides-spectral
  imports swap to `srmech.amsc.*`, bootstrap registration is added in
  `ephemerides_spectral/__init__.py`, and `srmech>=0.1.0` is added to
  ephemerides-spectral's runtime dependencies. (Adds 11 new
  `test_register_classifier` tests on the srmech side, bringing the
  in-isolation count to 59.)
- Task #197 Phase 4 PR has merged to `main` — duplicate AMSC framework
  code removed from ephemerides-spectral (12 mirrored module files);
  codegen `_INCLUDED_MODULES` / `_INCLUDED_SUBDIRS` updated; CHANGELOG
  entries in place.

At that point the `main` branch carries a `srmech v0.1.0` source tree that
has passed all 5 Phase 1 parity gates at every phase boundary.

---

## §2. Release procedure (TestPyPI — autonomous)

Run these commands from a clean checkout of `main` once Phase 4 merges:

```bash
# 1. Sync the local main branch
git checkout main
git pull origin main

# 2. Create the release tag and push it.
#    The autotag workflow (.github/workflows/srmech-autotag.yml) usually
#    catches version bumps and tags automatically, but a manual tag also
#    triggers the publish workflow cleanly.
git tag srmech-v0.1.0
git push origin srmech-v0.1.0

# 3. The .github/workflows/srmech-publish.yml workflow auto-triggers on
#    the tag push (tag pattern: srmech-v*). It:
#      - builds sdist + py3-none-any wheel from docs/srmech/python/
#      - publishes to PyPI via trusted-publisher OIDC by default.
#
#    For the **first TestPyPI release**, the workflow must be dispatched
#    manually (workflow_dispatch input `target: testpypi`) rather than
#    relying on the tag-push handler:
#
#      gh workflow run srmech-publish.yml \
#         --ref srmech-v0.1.0 \
#         -f target=testpypi
#
#    This ensures srmech v0.1.0 lands on TestPyPI without being
#    auto-promoted to PyPI in the same run.

# 4. Verify the install from TestPyPI succeeds (use a clean venv):
#      python -m venv /tmp/test-srmech && source /tmp/test-srmech/bin/activate
#      pip install --index-url https://test.pypi.org/simple/ srmech==0.1.0
#      python -c "import srmech; print(srmech.__version__)"
#      python -c "from srmech.amsc.catalog import list_attested_sources; print(list_attested_sources())"
#    Expected output: 0.1.0 and an empty list (srmech ships zero
#    catalogs in v0.1.0; ephemerides-spectral registers its 19 catalogs
#    at runtime via register_attested_root()).
```

---

## §3. After TestPyPI install verifies

Once the TestPyPI install verifies clean:

1. ephemerides-spectral's next release (whatever version comes next after
   the Phase 4 merge) can satisfy `srmech>=0.1.0` from TestPyPI for
   verification builds, and from PyPI once the human-in-loop PyPI
   promotion below completes.
2. Open a tracking issue (or update Task #197) noting the TestPyPI URL
   and the SHA-256 of the published wheel for future reproducibility
   audits.

---

## §4. PyPI release (human-in-loop)

The PyPI release is **deliberately separate** from the TestPyPI release.
The user must explicitly authorize the PyPI publish before it runs.

When authorized:

```bash
gh workflow run srmech-publish.yml \
   --ref srmech-v0.1.0 \
   -f target=pypi
```

Verify:

```bash
pip install srmech==0.1.0
python -c "import srmech; print(srmech.__version__)"
```

After the PyPI release verifies, ephemerides-spectral's next release can
pin `srmech>=0.1.0` from PyPI and the AMSC-to-srmech refactor is fully
realized end-to-end.

---

## §5. Rollback

If the TestPyPI release surfaces a bug:

- TestPyPI releases are *yanked* with `pip` admin actions (TestPyPI
  permits delete; PyPI does not).
- A patch release `srmech v0.1.1` is cut from a fix branch off `main`.
- The Phase 4 PR is not reverted (the framework is gone from
  ephemerides-spectral; ephemerides-spectral depends on a fixed srmech
  patch release on TestPyPI rather than v0.1.0).

If a critical bug surfaces *after* the PyPI release, follow standard PyPI
yank procedure (`pip install` skips yanked versions unless explicitly
pinned). Patch-release `v0.1.1` from `main` and re-publish.

---

## §6. Discipline metadata

- **Citation discipline**: 0 brief misattributions expected; the running
  tally stays at 19 catches (12 from conductor briefs).
- **5-gate parity**: all 5 Phase 1 gates were green at Phase 4 boundary
  (the only gate that could regress post-merge is Gate 4 / bridge surface
  parity, which is recovered by running the parity snapshot script
  against the TestPyPI-installed srmech and comparing to the local
  baseline).
- **Branch + PR workflow** (per project CLAUDE.md): No direct commits to
  `main`. Tag-push is the release trigger, not a commit.
