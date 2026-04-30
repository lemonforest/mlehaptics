# ADR 0003: Ephemeris-kernel allowlist (CodeQL discipline)

**Status:** Accepted (2026-04-29)

## Context

The v0.2.0 research-scaffold work hit `py/clear-text-logging-sensitive-data` seven times because kernel filenames look like paths to CodeQL's heuristic. The `lgtm[...]` suppress comments did not stick (modern CodeQL ignores them). Five commits later we landed on sanitisation-barrier numeric casts, which worked but were fragile.

For v0.1.0 we want a structurally cleaner solution that prevents the call-site that triggers the heuristic.

## Decision

Three layered mitigations:

1. **`bridge/ephemeris_bridge.py` is the ONLY URL builder.** Validates kernel name against a frozen tuple before any URL or filesystem path is constructed:

   ```python
   ALLOWED_KERNELS = ("de421", "de422", "de440", "de441",
                       "de441_part1", "de441_part2")
   if name not in ALLOWED_KERNELS:
       raise ValueError(f"unknown kernel {name!r}")
   ```

   CodeQL's flow analysis sees the constant-set membership gate.

2. **Logging redacts paths.** Loggers log only the kernel *name* (which is in the allowlist), never the full path:

   ```python
   log.info("loaded kernel %s (size %.1f MB)", kernel_name, size_mb)   # OK
   log.info("loaded %s", kernel_path)                                    # NOT OK
   ```

   `tests/test_codeql_allowlist.py` greps the package source for `log.*kernel_path|log.*\.bsp` and fails the build if any line matches.

3. **What-if input gates** (see ADR 0008) keep user-controlled `p, q` inputs bounded so they cannot trigger pathological enumeration.

## Consequences

- The user-controllable string surface is tiny (kernel names from a 6-tuple, dial names from `DIAL_SPECS`).
- Adding a kernel requires a PR review (and an ADR if from a non-JPL source).
- Future contributors don't accidentally widen the URL space — the allowlist is the only path.

## Alternatives considered

- **Suppress with `# nosec` / `# noqa`.** Brittle — only works in some CodeQL versions.
- **Escape paths via `repr()`.** Doesn't help; CodeQL flags the data flow, not the formatting.
- **Disable the check globally.** Removes a useful rule for the rest of the codebase.
