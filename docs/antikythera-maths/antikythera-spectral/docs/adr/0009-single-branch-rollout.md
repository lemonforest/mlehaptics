# ADR 0009: Single-branch rollout for v0.1.0

**Status:** Accepted (2026-04-29)

## Context

The original packaging plan envisioned 18 phases as 18 individual PRs landing incrementally on main. The user's preferred workflow is a single PR with all phases as commits, so a release can be tested end-to-end against TestPyPI before any merge to main.

## Decision

The v0.1.0 release lands as a **single PR** (`antikythera-spectral-pypi-plan` branch). Each implementation phase is a commit on that branch. The PR is opened in **draft** while phases land. When all phases are complete:

1. Dispatch the publish workflow with `target=testpypi` against the branch.
2. Verify `pip install --index-url https://test.pypi.org/simple/ antikythera-spectral==0.1.0rcN` works (iterate `rcN` if needed).
3. Bump `python/pyproject.toml` from `0.1.0rcN` to `0.1.0`, commit, mark PR ready.
4. Get final review, merge to main.
5. Autotag fires on main, pushes `antikythera-spectral-v0.1.0`, publish workflow lands real PyPI release.

Pre-release versions (`0.1.0rc1`, `0.1.0.dev0`, …) are intentionally excluded from autotag — they're test-only.

## Consequences

- Reviewer sees a coherent v0.1.0 release rather than 18 incremental drafts.
- Zero version-burn on real PyPI during development (the production version slot is used exactly once).
- `git log` on main has 1 merge commit for v0.1.0; subsequent versions follow the same pattern.
- Single-PR review is harder than 18 small PRs, but the per-phase commits give reviewers a logical reading order.

## Alternatives considered

- **18 individual PRs.** Rejected per the user's "single PR" decision. Plan §10 originally said "each phase is its own PR"; ADR supersedes that.
- **Squash to a single commit at merge time.** Rejected — the per-phase commit history is useful for `git bisect` and post-merge audit.
