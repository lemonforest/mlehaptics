# ADR 0010: TestPyPI pre-merge gating

**Status:** Accepted (2026-04-29)

## Context

We want to verify the wheel actually installs cleanly from PyPI before we cut a real release tag. PyPI versions are immutable — once you publish `0.1.0`, that version slot is permanently consumed. Mistakes mean burning to `0.1.1` or `0.1.0.post1`.

## Decision

The publish workflow accepts a `target` workflow_dispatch input:

- `target=testpypi` (default) → publishes to `test.pypi.org`. Used during development to verify installability.
- `target=pypi` → publishes to `pypi.org`. Only fires automatically on tag-push (`antikythera-spectral-v*`).

Pre-merge workflow:

1. Build artifacts on the feature branch.
2. `gh workflow run antikythera-spectral-publish.yml --ref antikythera-spectral-pypi-plan -f target=testpypi`.
3. Wait for the workflow to land `0.1.0rcN` on TestPyPI.
4. In a clean venv: `pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ antikythera-spectral==0.1.0rcN`.
5. Smoke-test: import + a few bridge calls + the CLI.
6. Iterate `rcN` if anything's wrong.
7. Once green, bump version to `0.1.0`, merge, tag.

The `--extra-index-url https://pypi.org/simple/` is needed because TestPyPI doesn't host all dependencies (numpy, skyfield); they're pulled from real PyPI.

## Consequences

- Production PyPI sees `0.1.0` only after we've proved an identical wheel installs cleanly from TestPyPI.
- `0.1.0rcN` versions on TestPyPI are NOT autotagged (per ADR 0009; autotag requires strict semver).
- Both PyPI environments need trusted-publisher entries (one-time human setup; both ✅ done).

## Alternatives considered

- **Skip TestPyPI, publish straight to PyPI.** Rejected — version-burn risk too high for a project with active community.
- **Use `0.1.0a1` / `0.1.0b1` instead of `rc1`.** All three are valid pre-release markers; `rc1` is the most common convention for "this is the candidate we expect to ship."
