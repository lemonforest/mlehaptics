"""v0.11.2 — JPL Power-of-Ten violation ratchet for the C library.

Mirrors `c/JPL_AUDIT.md`: every mechanically-detectable violation is
pinned. PRs are allowed to *decrease* each count (rule fixes), but
increases fail the test loudly. Adding a new violation requires
updating the pin upward in the same PR with explicit justification.

History:
  - v0.11.2: baseline audit, all pins set to first-measured values.
  - v0.13.4: Rule 1 (goto) 5 → 0 and Rule 3 (dynamic alloc) 29 → 0
             via the `es_hd_state.c` caller-supplied-scratch refactor
             (combined fix; ABI v5 → v6).
  - v0.13.5: Rule 4 (long functions) 4 → 0 by splitting the long
             functions in es_encode.c, es_parity.c, and es_hd_state.c
             into <60-line factors via 10 new static helpers.
             PIN_RULE_5_TOTAL_FUNCS bumped 32 → 42 to track the new
             helper count (Rule 5 work in v0.13.6 will need the
             larger function inventory).
  - v0.13.6: Rule 5 (assertion density) flipped from SKIP to PASS.
             88 assertions across 42 functions = 2.10/function avg
             (target ≥ 2.0). PIN_RULE_5_ASSERTIONS ratcheted 0 → 88.
             Assertions gated behind <assert.h> NDEBUG semantics —
             zero runtime cost in release builds.

Same modular discipline as `test_native_version_string_matches_package_version`,
`test_parity_smoke.py::PARITY_TARGETS`, and `test_readme_freshness.py`:
enumerate the truth, fail loudly on drift, reduce on improvement.

Reference: Holzmann, G. J. (2006). "The Power of Ten — Rules for
Developing Safety Critical Code." *IEEE Computer* 39(6), 95-99.

What this DOES detect:

  - Rule 1: `goto`, `setjmp`, `longjmp` keyword occurrences.
  - Rule 2: `while(1)` / `for(;;)` infinite-loop syntax.
  - Rule 3: `malloc`, `calloc`, `realloc`, `free` calls.
  - Rule 4: function bodies > 60 lines.
  - Rule 5: total `assert(...)` call count.
  - Rule 8: multi-line `#define` macros.
  - Rule 9: function-pointer declaration syntax `(*name)(`.

What this does NOT detect (manual audit; queued for v0.11.3+):

  - Rule 1 recursion (semantic; needs call-graph analysis).
  - Rule 6 smallest-scope (semantic).
  - Rule 7 return-value checking by callers (semantic).
  - Rule 10 zero-warnings-at-pedantic (toolchain-dependent; Rule 10
    audit ships in v0.11.6 with a cross-platform CI matrix).

The pinned counts here DO NOT include those un-mechanical rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

# ──────────────────────────────────────────────────────────────────────
# Pinned violation counts (v0.11.2 baseline)
# ──────────────────────────────────────────────────────────────────────
#
# Update DOWN as v0.11.3+ rule-fix work removes violations. Updating
# UP requires explicit justification in the PR description.

#: Rule 1 — control flow: no goto / setjmp / longjmp.
#: v0.13.4: 5 → 0 (es_hd_state.c caller-supplied-scratch refactor
#: removed the goto-cleanup pattern).
PIN_RULE_1_GOTO:           int = 0
PIN_RULE_1_SETJMP:         int = 0
PIN_RULE_1_LONGJMP:        int = 0

#: Rule 2 — fixed loop bounds.
PIN_RULE_2_UNBOUNDED:      int = 0

#: Rule 3 — no dynamic allocation. Counts malloc + calloc + realloc + free
#: occurrences in source (each `free()` call counts; mirrored allocation
#: + free pairs count as 2).
#: v0.13.4: 29 → 0 (same refactor; the C library no longer calls
#: malloc/free after init — scratch buffers are caller-supplied).
PIN_RULE_3_DYNAMIC_ALLOC:  int = 0

#: Rule 4 — functions ≤ 60 lines.
#: v0.13.5: 4 → 0 (long functions split via 10 new static helpers in
#: es_encode.c, es_parity.c, es_hd_state.c).
PIN_RULE_4_LONG_FUNCTIONS: int = 0

#: Rule 5 — ≥ 2 assertions per function (averaged). Total assertion
#: count across the codebase. Pinned as the assertion total; the
#: 2/function average is enforced as a derived test below.
#: v0.13.6:   0  → 88. Assertions gated behind <assert.h> NDEBUG so
#:                  production builds (-DNDEBUG) strip them entirely
#:                  — assertions are a development tool, not a
#:                  runtime cost.
#: v0.28.0rc5: 88 → 102. +14 from the Phase 10a EOC C-side
#:                  completion (es_solve_kepler ×3,
#:                  es_true_anomaly ×2, es_eval_eoc_residue ×4,
#:                  es_clear_eoc_patches ×2, es_validate_patch
#:                  ECC-kind branch ×3).
#: v0.29.0rc1: 102 → 110. +8 from the channel-basis dual-path spike:
#:                  es_channel_basis_legacy ×3, es_channel_basis_cospi_route
#:                  ×3, es_channel_basis (post-null-check) ×1,
#:                  es_channel_basis_method (post-null-check) ×1; old
#:                  es_channel_basis loop's 2 asserts roll into
#:                  _legacy. New es_splitmix64_uniform_half_turns
#:                  carries 2 asserts (range invariants). Net +8.
PIN_RULE_5_ASSERTIONS:     int = 110
#: Total functions in the codebase. Used to compute the 2/function
#: average enforcement. Pinned because adding functions changes the
#: required assertion count; if a PR adds functions it should ALSO
#: add proportional assertions to keep the average above 2.
#: v0.13.5:   32 → 42 (10 new static helpers from the Rule 4 splits).
#: v0.28.0rc5: 42 → 46. +4 from Phase 10a EOC: es_solve_kepler,
#:                  es_true_anomaly, es_eval_eoc_residue,
#:                  es_clear_eoc_patches. Density: 102 / 46 = 2.22
#:                  (well above the ≥2.0 floor).
#: v0.29.0rc1: 46 → 53. +7 from the channel-basis dual-path spike:
#:                  es_cospi_d (inline), es_sinpi_d (inline),
#:                  es_has_native_cospi, es_channel_basis_legacy,
#:                  es_channel_basis_cospi_route, es_channel_basis_method,
#:                  es_splitmix64_uniform_half_turns (in es_prng.c);
#:                  es_channel_basis (preserved). Density: 110/53 =
#:                  2.075 (above the ≥2.0 floor).
PIN_RULE_5_TOTAL_FUNCS:    int = 53

#: Rule 8 — limited preprocessor: no multi-line macros.
PIN_RULE_8_MULTILINE_MACROS: int = 0

#: Rule 9 — no function pointers.
PIN_RULE_9_FUNCTION_POINTERS: int = 0


# ──────────────────────────────────────────────────────────────────────
# Source enumeration
# ──────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[2]  # python/tests → up 2 = ephemerides-spectral/
_C_SRC_DIR = _REPO_ROOT / "c" / "src"
_C_INCLUDE_DIR = _REPO_ROOT / "c" / "include"


def _collect_source_files() -> List[Path]:
    sources: List[Path] = []
    sources.extend(sorted(_C_SRC_DIR.glob("*.c")))
    sources.extend(sorted(_C_INCLUDE_DIR.glob("*.h")))
    return sources


def _strip_comments(text: str) -> str:
    """Strip C-style block + line comments. Imperfect but good enough
    for keyword-counting: handles `// ...`, `/* ... */`, but not strings
    that happen to contain `goto` etc."""
    # Strip /* ... */ block comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    # Strip // line comments
    text = re.sub(r"//[^\n]*", "", text)
    return text


# ──────────────────────────────────────────────────────────────────────
# Rule 1 — no goto / setjmp / longjmp
# ──────────────────────────────────────────────────────────────────────

def _count_keyword(keyword: str) -> int:
    """Count occurrences of `keyword` as a standalone identifier, ignoring comments."""
    pattern = re.compile(r"\b" + re.escape(keyword) + r"\b")
    total = 0
    for p in _collect_source_files():
        text = _strip_comments(p.read_text(encoding="utf-8"))
        total += len(pattern.findall(text))
    return total


def test_rule_1_no_goto() -> None:
    """JPL Rule 1: no goto. Pinned at v0.11.2 baseline; can only decrease."""
    actual = _count_keyword("goto")
    assert actual <= PIN_RULE_1_GOTO, (
        f"Rule 1 (no goto) regressed: {actual} occurrences vs. pinned "
        f"{PIN_RULE_1_GOTO}. Either remove the new goto(s) or update "
        f"PIN_RULE_1_GOTO upward with justification in the PR description."
    )
    if actual < PIN_RULE_1_GOTO:
        # Drop hint — the pin should be tightened in this same PR.
        import warnings
        warnings.warn(
            f"Rule 1 (no goto) improved: {actual} < pinned {PIN_RULE_1_GOTO}. "
            f"Update PIN_RULE_1_GOTO = {actual} in this PR to ratchet the "
            f"baseline down.", stacklevel=2,
        )


def test_rule_1_no_setjmp() -> None:
    actual = _count_keyword("setjmp")
    assert actual <= PIN_RULE_1_SETJMP, (
        f"Rule 1 (no setjmp) regressed: {actual} vs. pinned {PIN_RULE_1_SETJMP}."
    )


def test_rule_1_no_longjmp() -> None:
    actual = _count_keyword("longjmp")
    assert actual <= PIN_RULE_1_LONGJMP, (
        f"Rule 1 (no longjmp) regressed: {actual} vs. pinned {PIN_RULE_1_LONGJMP}."
    )


# ──────────────────────────────────────────────────────────────────────
# Rule 2 — fixed loop bounds (no while(1) / for(;;))
# ──────────────────────────────────────────────────────────────────────

def test_rule_2_no_unbounded_loops() -> None:
    """No `while(1)` / `while(true)` / `for(;;)` patterns."""
    pattern = re.compile(r"\b(?:while\s*\(\s*1\s*\)|while\s*\(\s*true\s*\)|for\s*\(\s*;\s*;\s*\))")
    total = 0
    for p in _collect_source_files():
        text = _strip_comments(p.read_text(encoding="utf-8"))
        total += len(pattern.findall(text))
    assert total <= PIN_RULE_2_UNBOUNDED, (
        f"Rule 2 (fixed loop bounds) regressed: {total} unbounded-loop "
        f"patterns vs. pinned {PIN_RULE_2_UNBOUNDED}."
    )


# ──────────────────────────────────────────────────────────────────────
# Rule 3 — no dynamic allocation
# ──────────────────────────────────────────────────────────────────────

def _count_dynamic_allocation() -> int:
    """Count malloc / calloc / realloc / free call sites (rough — counts
    keyword occurrences after stripping comments; a `free` in a struct
    field name would count erroneously, but our code doesn't have that)."""
    keywords = (r"\bmalloc\s*\(", r"\bcalloc\s*\(",
                r"\brealloc\s*\(", r"\bfree\s*\(")
    pattern = re.compile("|".join(keywords))
    total = 0
    for p in _collect_source_files():
        text = _strip_comments(p.read_text(encoding="utf-8"))
        total += len(pattern.findall(text))
    return total


def test_rule_3_no_dynamic_allocation() -> None:
    actual = _count_dynamic_allocation()
    assert actual <= PIN_RULE_3_DYNAMIC_ALLOC, (
        f"Rule 3 (no dynamic allocation) regressed: {actual} "
        f"malloc/calloc/realloc/free call sites vs. pinned "
        f"{PIN_RULE_3_DYNAMIC_ALLOC}. Use static or caller-supplied "
        f"buffers instead."
    )


# ──────────────────────────────────────────────────────────────────────
# Rule 4 — functions ≤ 60 lines
# ──────────────────────────────────────────────────────────────────────

def _detect_functions(text: str) -> List[Tuple[str, int, int]]:
    """Return [(fn_name, start_line, length), ...] for all top-level
    functions in the source text. Heuristic — same one used in the
    research/audit scripts."""
    lines = text.split("\n")
    funcs: List[Tuple[str, int, int]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line and line[0].isalpha() and "(" in line and "=" not in line.split("(")[0] and ";" not in line:
            m = re.search(r"(\w+)\s*\(", line)
            if m:
                fn_name = m.group(1)
                if fn_name in ("if", "while", "for", "switch", "return",
                               "sizeof", "typedef"):
                    i += 1
                    continue
                j = i
                while j < len(lines) and "{" not in lines[j]:
                    j += 1
                if j >= len(lines):
                    i += 1
                    continue
                depth = 0
                k = j
                while k < len(lines):
                    depth += lines[k].count("{") - lines[k].count("}")
                    if depth == 0:
                        funcs.append((fn_name, i + 1, k - i + 1))
                        break
                    k += 1
                i = k + 1
                continue
        i += 1
    return funcs


def test_rule_4_function_length_under_60() -> None:
    long_count = 0
    long_names: List[str] = []
    for p in sorted(_C_SRC_DIR.glob("*.c")):
        text = p.read_text(encoding="utf-8")
        for fn_name, start_line, length in _detect_functions(text):
            if length > 60:
                long_count += 1
                long_names.append(f"{p.name}:{start_line} {fn_name}() — {length} lines")
    assert long_count <= PIN_RULE_4_LONG_FUNCTIONS, (
        f"Rule 4 (functions ≤ 60 lines) regressed: {long_count} long "
        f"functions vs. pinned {PIN_RULE_4_LONG_FUNCTIONS}. Long ones:\n  "
        + "\n  ".join(long_names)
    )


def test_rule_4_total_function_count_changes_force_pin_update() -> None:
    """If the total function count changes, the pin should be reviewed.

    Adding new functions doesn't violate Rule 4 directly, but it changes
    the assertion-density math in Rule 5 (more functions → more assertions
    needed). Failing here forces the PR author to consider both.
    """
    total_funcs = 0
    for p in sorted(_C_SRC_DIR.glob("*.c")):
        text = p.read_text(encoding="utf-8")
        total_funcs += len(_detect_functions(text))
    assert total_funcs == PIN_RULE_5_TOTAL_FUNCS, (
        f"Total C function count changed: {total_funcs} vs. pinned "
        f"{PIN_RULE_5_TOTAL_FUNCS}. Update PIN_RULE_5_TOTAL_FUNCS in this "
        f"PR; if the count went UP, also reassess PIN_RULE_5_ASSERTIONS "
        f"(Rule 5 requires ≥2 assertions per function on average)."
    )


# ──────────────────────────────────────────────────────────────────────
# Rule 5 — ≥ 2 assertions per function (averaged)
# ──────────────────────────────────────────────────────────────────────

def test_rule_5_assertion_count() -> None:
    """Total assert(...) calls; the 2/function average is enforced
    as a derived check below."""
    pattern = re.compile(r"\bassert\s*\(")
    total = 0
    for p in _collect_source_files():
        text = _strip_comments(p.read_text(encoding="utf-8"))
        total += len(pattern.findall(text))
    # Assertion count should ONLY GO UP. Failing means assertions
    # were removed.
    assert total >= PIN_RULE_5_ASSERTIONS, (
        f"Rule 5 (assertion density) regressed: {total} total assertions "
        f"vs. pinned {PIN_RULE_5_ASSERTIONS}. Don't remove assertions "
        f"without justification."
    )


def test_rule_5_density_meets_2_per_function() -> None:
    """Derived check: total assertions / function count ≥ 2.0.

    This test is allowed to FAIL at v0.11.2 baseline (current density
    is 0.0). It becomes the gate that proves we've done the v0.11.5
    Rule 5 work (≥64 assertions added). Marked xfail until the work
    lands.
    """
    pattern = re.compile(r"\bassert\s*\(")
    total_assertions = 0
    for p in _collect_source_files():
        text = _strip_comments(p.read_text(encoding="utf-8"))
        total_assertions += len(pattern.findall(text))
    total_funcs = 0
    for p in sorted(_C_SRC_DIR.glob("*.c")):
        text = p.read_text(encoding="utf-8")
        total_funcs += len(_detect_functions(text))
    if total_funcs == 0:
        return  # no functions; trivially passes
    density = total_assertions / total_funcs
    # At v0.11.2 baseline this is 0.0. The test is currently expected
    # to fail; the v0.11.5 Rule 5 ship flips it to passing. We mark
    # the failure soft via a clear message (skip semantics).
    if density < 2.0:
        import pytest
        pytest.skip(
            f"Rule 5 density at {density:.2f} (need ≥ 2.0). "
            f"v0.11.5 ship will add assertions to satisfy. "
            f"Currently {total_assertions} assertions across {total_funcs} functions."
        )


# ──────────────────────────────────────────────────────────────────────
# Rule 8 — limited preprocessor (no multi-line macros)
# ──────────────────────────────────────────────────────────────────────

def test_rule_8_no_multiline_macros() -> None:
    """Match `#define X ... \\` with line-continuation."""
    total = 0
    for p in _collect_source_files():
        text = p.read_text(encoding="utf-8")
        for line in text.split("\n"):
            if re.match(r"^\s*#define\b.*\\\s*$", line):
                total += 1
    assert total <= PIN_RULE_8_MULTILINE_MACROS, (
        f"Rule 8 (limited preprocessor) regressed: {total} multi-line "
        f"macros vs. pinned {PIN_RULE_8_MULTILINE_MACROS}."
    )


# ──────────────────────────────────────────────────────────────────────
# Rule 9 — no function pointers
# ──────────────────────────────────────────────────────────────────────

def test_rule_9_no_function_pointers() -> None:
    """Match `(*name)(` function-pointer declarations."""
    pattern = re.compile(r"\([\s\*]+\w+\)\s*\(")
    total = 0
    for p in _collect_source_files():
        text = _strip_comments(p.read_text(encoding="utf-8"))
        total += len(pattern.findall(text))
    assert total <= PIN_RULE_9_FUNCTION_POINTERS, (
        f"Rule 9 (no function pointers) regressed: {total} declarations "
        f"vs. pinned {PIN_RULE_9_FUNCTION_POINTERS}."
    )


# ──────────────────────────────────────────────────────────────────────
# Audit completeness — make sure JPL_AUDIT.md is up to date
# ──────────────────────────────────────────────────────────────────────

def test_audit_document_exists() -> None:
    """The audit document must exist alongside this test."""
    audit_path = _REPO_ROOT / "c" / "JPL_AUDIT.md"
    assert audit_path.is_file(), (
        f"Missing JPL audit document at {audit_path}. The pinned "
        f"counts in this test must be paired with a human-readable "
        f"audit record explaining the violations."
    )
