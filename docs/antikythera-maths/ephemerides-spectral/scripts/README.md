# scripts/

Local-developer scripts for the ephemerides-spectral package.

## `smoke_local.sh` — pre-push smoke test

Mirrors the two key Linux CI checks before push:

1. **Codegen reproducibility** — snapshot SHA-256s of `_data/` + `_research/`, run `regenerate.py`, snapshot again, diff. Catches the "edited `research/` source files but forgot to mirror to `_research/`" miss that hit PR #286.
2. **Test suite** — `pytest tests/`. Catches ratchet asserts, manifest SHA mismatches, and runtime tests that broke when the new saturn_rings pilot landed without the ratchet updates.

### How to run

**From WSL2 (recommended on Windows):**

```bash
wsl bash docs/antikythera-maths/ephemerides-spectral/scripts/smoke_local.sh
```

Or open a WSL2 shell and run directly:

```bash
cd /mnt/d/GitHub/mlehaptics
bash docs/antikythera-maths/ephemerides-spectral/scripts/smoke_local.sh
```

**From native Linux or macOS:**

```bash
bash docs/antikythera-maths/ephemerides-spectral/scripts/smoke_local.sh
```

### What it covers vs what it does not

✅ Catches:
- Codegen drift (`research/` → `_research/` mirror missing or stale)
- Manifest SHA-256 mismatches against committed bytes
- All ratchet test asserts (source counts, adapter registry, etc.)
- Bridge / CLI surface contract regressions
- Adapter Protocol conformance

❌ Does **not** catch:
- **CRLF/LF mismatches** between Windows working copy and git's stored bytes. WSL2 sees the same working-copy bytes the Windows side does. The `.gitattributes` pin LF on the paths that matter; CI confirms LF on push.
- Native (C) build or parity issues. The smoke uses the pure-Python fallback (no `pip install -e ".[ephemeris,tests]"` build step), matching the CI's "fallback (pure-Python, no native)" job. Run platform-wheel CI on push to catch C-side regressions.
- Cross-platform-wheel verification — only CI's verify-wheels job covers that.

### First-run timing

- Venv creation + pip install: ~30s one-time
- Subsequent runs: ~60–90s (codegen + ~1900 tests)

### Venv location

The venv lives at `~/.venvs/ephemerides-spectral-smoke/` outside the repo, to avoid Windows-mount perf hits and accidental git tracking. Override with `VENV_HOME=/some/path` if needed.

### When to use

- **Before every push to a feature branch.** Run once before `git push` to catch the Linux-side issues that PR #286 turned up.
- **After running `regenerate.py`.** The codegen-drift check is its primary value.
- **After updating ratchet asserts.** Catches the "I missed a third / fourth ratchet" pattern that PR #286 hit twice.
