# ADR-0007: Release engineering — version SSOT, rc-first, the registry ripple, JPL

**Status:** Accepted (standing architecture policy; consolidates discipline previously held only in project memory).
**Date:** 2026-07-17.
**Authors:** Steven Kirkland + Claude.
**Supersedes:** none.
**Superseded-by:** none.

---

## 1. Context

srmech (and its sister packages) publish continuously. The recurring failure modes
are mechanical and cheap to prevent with a fixed procedure: a version bumped in some
but not all SSOT locations; a new public callable that trips CI one hidden gate at a
time; a clean tag pushed by hand that should have been auto-tagged; a "fast test" CI
that misses a build-env error. This ADR fixes the mechanical release procedure.
(Standing *authorizations* — autonomous rc-merge, no human gate between rcs — live
in project memory, not here; this ADR is the mechanics.)

## 2. Decision

1. **Version SSOT is FIVE locations, changed together.**
   `python/pyproject.toml`, `python/pyproject-pure.toml`, `python/srmech/version.py`,
   `c/include/srmech.h` (both `SRMECH_VERSION_PRE` + `SRMECH_VERSION`), and the
   version-pin in `python/tests/test_signal_processing_scaffolding.py`. After a bump,
   rebuild the native `.so` (a stale `.so` fails version/parser-version parity
   locally only — CI builds fresh). A genome/format change also bumps the format
   version + the C rule preimages in lockstep.

2. **rc-first to TestPyPI; clean tags auto-publish to production.** Every release
   ships `vX.Y.ZrcN` to TestPyPI first (autotag SKIPS pre-release/non-strict-semver
   tags — push the rc tag by hand on the FEATURE branch/merge commit). Only a clean
   (non-rc) strict-semver tag routes to production PyPI, and clean tags are
   AUTO-tagged on merge — never pushed by hand. Verify in a clean venv OUTSIDE the
   source tree (source-tree namespace shadowing loads `_native.py` with
   `HAS_NATIVE=False` spuriously).

3. **A new PUBLIC `srmech.amsc.*` callable trips a fixed ripple — run it ALL locally
   before pushing** (rc258 burned 3 CI cycles finding these one at a time):
   (a) a `tool_schema.py` `ToolEntry`; (b) MCP coercion — every param TYPE STRING
   must have a coercer in `srmech.mcp._coercion` (reuse `dict`/`Sequence[tuple]` etc.,
   never a novel type string); (c) a `rosetta_classification.ndjson` bucket line;
   (d) regenerate `_tool_docs.py`; (e) the `tools.total` count across ~46 test files;
   (f) regenerate BOTH C registries (`srmech_carrier_registry.c` +
   `srmech_tool_registry.c`, UTF-8/LF) and rebuild the `.so` to verify byte-parity.
   A callable that merely *composes* registered ops may be `_EXEMPT` + a rosetta
   line only (2 gates, not 6).

4. **Merge policy.** Never squash-merge (`gh pr merge --merge` / `--rebase`). At a
   partition boundary, update the rolling PR description.

5. **CI shape + local pre-checks.** Per-PR CI is LEAN fast tests + a pedantic C
   matrix (Linux gcc / macOS clang / Windows MSVC, `-Werror`/`/WX`) + a pure-wheel
   build; the rc→TestPyPI step is what catches build-env errors the fast tests miss.
   A local WSL C smoke MUST build RELEASE (`-O2 -DNDEBUG`, pedantic) to reproduce
   CI. In a native-absent dev env, native-presence / single-C-call checks **skip**
   (not fail) via `@pytest.mark.skipif(not _native.HAS_NATIVE)` (#843, fixed) — CI
   always builds the native lib fresh, so those checks always run + assert there;
   the skip only affects a native-off dev run.

6. **Platform-agnostic by construction — machine-specific code routes ONLY through
   the HAL or the PAL; the core C is portable.** Target-specific optimizations (SIMD /
   SHA-NI / intrinsics) go behind the **HAL** (`srmech_simd.h`, the optimize path) so
   no machine-specific code leaks into a kernel — its target magic constants are
   attested in the header and derive-and-assert. All I/O (file / stream / socket —
   e.g. Windows named pipes vs POSIX) goes behind the **PAL** (`srmech_platform*.c`;
   the everything-mirrors-through-PAL rule is ADR-0003 point 4). The pedantic 3-OS
   matrix (Linux gcc / macOS clang / Windows MSVC, `-Werror`/`/WX`) is the PROOF that
   no target-specific code escaped the HAL/PAL — a new warning on any OS fails CI.

7. **Full immolation before a production graduation.** Before a clean (non-rc)
   PyPI publish, exercise every class/function touched through its TOML + surface in
   a clean environment.

8. **A float/FPU-derived parity test is within-tolerance, NEVER a cross-platform
   SHA.** Only exact-integer ops get a byte-identical cross-platform digest.

## 3. Consequences

- Version drift, hidden-gate CI churn, and hand-pushed clean tags are structurally
  prevented.
- The registry-ripple checklist is the single reference for "I added a public op".

## 4. Sources (consolidated from project memory)

`[[feedback_srmech_version_bump_hits_five_locations_run_suite_after]]` ·
`[[feedback_new_amsc_public_callable_registry_checklist]]` ·
`[[feedback_new_tool_entry_needs_mcp_coercer_and_smoke_sample]]` ·
`[[feedback_new_tool_ripple_full_checklist]]` ·
`[[feedback_always_rc_first_for_downstream_publishes]]` ·
`[[feedback_clean_release_tags_are_autotagged_never_manual]]` ·
`[[feedback_rc_tag_targets_branch_not_merge]]` · `[[feedback_no_squash_merges]]` ·
`[[feedback_rolling_pr_partition_boundary_updates]]` ·
`[[feedback_lean_test_ci_testpypi_catches_build_env_errors]]` ·
`[[feedback_wsl_smoke_must_build_release_ndebug_to_match_ci_pedantic]]` ·
`[[feedback_native_absent_dev_env_stale_dll_and_immolation_hang]]` ·
`[[feedback_full_immolation_before_live_publish]]` ·
`[[feedback_numeric_parity_test_within_tol_not_cross_platform_sha]]` ·
`[[feedback_no_ship_known_broken_gold_is_law]]`

**JPL Power-of-Ten (C):** the srmech C library passes all 10 Holzmann rules
(`docs/srmech/c/JPL_AUDIT.md`); `tests/test_jpl_audit.py` is a mechanical ratchet
(no-goto / no-malloc / ≤60-line functions / ≥2 asserts per non-exempt function /
no multi-line macros) — violations only go DOWN. Struct fields are ordered
big-first (8→4→2→1 byte) to minimise padding. (The HAL/PAL platform-abstraction that
keeps machine-specific code out of the kernels is decision point 6 above.)
(`[[feedback_jpl_rule_5_two_assert_habit]]` ·
`[[feedback_struct_field_ordering_big_first]]` ·
`[[feedback_simd_optimize_path_goes_through_hal]]` ·
`[[feedback_hal_magic_constants_attested_and_derived]]`)
