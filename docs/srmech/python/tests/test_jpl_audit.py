"""JPL Power-of-Ten ratchet for srmech's C library.

Task #201 Phase B6 — mechanically detectable rule violations are
pinned at the counts documented in
``docs/srmech/c/JPL_AUDIT.md``. The pins can only go DOWN
(violations removed), never UP (violations added).

A PR that pushes a new function over 60 lines, removes an assertion
from a function below the 2-assert floor, introduces a goto /
malloc / multi-line macro, etc. will fail this test.

Mirrors the discipline of ephemerides-spectral's
``tests/test_jpl_audit.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


# The C source tree lives at docs/srmech/c/, three levels up from
# this test file (tests/ -> python/ -> srmech/ -> c/ sibling of python/).
_HERE = Path(__file__).resolve().parent
_C_SRC_DIR = _HERE.parent.parent / "c" / "src"
_C_INCLUDE_DIR = _HERE.parent.parent / "c" / "include"


def _c_files() -> list[Path]:
    """All srmech C source files we audit."""
    files = sorted(_C_SRC_DIR.glob("*.c"))
    files += sorted(_C_INCLUDE_DIR.glob("*.h"))
    return files


pytestmark = pytest.mark.skipif(
    not _C_SRC_DIR.exists(),
    reason=(
        "C source tree not present "
        f"({_C_SRC_DIR} does not exist); "
        "this test pins the JPL audit of the C library and is "
        "only meaningful when the C sources are checked out"
    ),
)


# ──────────────────────────────────────────────────────────────────────
# Rule-by-rule mechanical pins
# ──────────────────────────────────────────────────────────────────────


def test_rule_1_no_goto() -> None:
    """JPL Rule 1: no goto, no setjmp / longjmp."""
    pattern = re.compile(r"\b(goto|setjmp|longjmp)\b")
    for f in _c_files():
        text = f.read_text(encoding="utf-8")
        # Strip /* ... */ and // comments so doc mentions don't count
        text_no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        text_no_line = re.sub(r"//.*$", "", text_no_block, flags=re.MULTILINE)
        matches = pattern.findall(text_no_line)
        assert not matches, (
            f"{f.relative_to(_HERE.parent.parent)}: Rule 1 violation "
            f"— goto/setjmp/longjmp found: {matches}"
        )


# Source files for which JPL Rule 3 (no malloc/free) is RELAXED at
# the cold-path setup boundary. Each entry must document the rationale
# in the JPL_AUDIT.md scope note. The relaxation does NOT extend to
# hot-path code — entries here just opt the FILE out of the regex
# scan; the spirit of Rule 3 (no allocation per-request inside the
# accept loop) still applies.
RULE_3_COLD_PATH_FILES: set[str] = {
    # v0.5.0rc2: bus C peer. calloc + malloc in srmech_bus_serve
    # (once per server start); free in srmech_bus_server_stop /
    # srmech_bus_client_close (once per teardown). No allocation in
    # srmech_bus_server_accept_one / srmech_bus_send_recv / the
    # per-request worker (those reuse the workspace allocated at
    # serve-time).
    "srmech_bus.c",
}


def test_rule_3_no_dynamic_allocation() -> None:
    """JPL Rule 3: no malloc / calloc / realloc / free / alloca.

    The ``RULE_3_COLD_PATH_FILES`` allowlist relaxes the regex scan
    for files whose only allocations are once-per-server-setup /
    once-per-server-teardown (no per-request allocation in the hot
    path). See entries above for per-file rationale.
    """
    pattern = re.compile(r"\b(malloc|calloc|realloc|free|alloca)\s*\(")
    for f in _c_files():
        if f.name in RULE_3_COLD_PATH_FILES:
            continue
        text = f.read_text(encoding="utf-8")
        text_no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        text_no_line = re.sub(r"//.*$", "", text_no_block, flags=re.MULTILINE)
        matches = pattern.findall(text_no_line)
        assert not matches, (
            f"{f.relative_to(_HERE.parent.parent)}: Rule 3 violation "
            f"— dynamic allocation found: {matches}"
        )


# ──────────────────────────────────────────────────────────────────────
# Rule 4 (functions ≤ 60 lines) + Rule 5 (≥ 2 asserts) ratchet
# ──────────────────────────────────────────────────────────────────────


# Functions exempted from Rule 5's ≥2-assert floor. See
# JPL_AUDIT.md for rationale per entry.
RULE_5_EXEMPT_FUNCTIONS: set[str] = {
    "srmech_version",       # trivial accessor returning a constant
    "srmech_abi_version",   # trivial accessor returning a constant
    "srmech_plat_has_threads",  # PAL trivial accessor: returns a compile-time
                                # 1/0 (is a threading backend present?). No
                                # state to assert; see c/JPL_AUDIT.md.
    "srmech_plat_has_streams",  # PAL trivial accessor: returns a compile-time
                                # 1/0 (is a stream-IPC backend present?). No
                                # state to assert; see c/JPL_AUDIT.md.
    # sha256 inline helpers — 4-7 lines each, no anomalous conditions
    "srmech_ror32",
    "srmech_ch",
    "srmech_maj",
    "srmech_bigsig0",
    "srmech_bigsig1",
    "srmech_smallsig0",
    "srmech_smallsig1",
    # v0.5.0rc2: srmech_bus.c framing helpers — each is a 1-assert
    # big-endian u32 (de)serialiser on its sole pointer arg; a second
    # assert would re-assert the same pointer. Static-internal-only;
    # the public API entry points have ≥2 asserts. (v0.7.5rc5: the
    # platform read/write/ensure-dir wrappers moved to the PAL —
    # srmech_platform.c — where each gained a 2nd assert and left the
    # exempt list; the ratchet went DOWN by five entries.)
    "srmech_bus__write_u32_be",
    "srmech_bus__read_u32_be",
    # v0.7.0rc10 (F292 graft #1): srmech_sha256_batch.c `__ror` is a 1-line
    # rotate (like the exempt scalar srmech_ror32), no pointer/bounds invariant.
    "srmech_sha256b__ror",
    # v0.7.0rc11 (SIMD optimize-path HAL): srmech_simd.c CPU-feature detectors
    # are pure cpuid/xgetbv probes returning 0/1 with no pointer/bounds
    # invariant to assert (they replaced per-file copies in sha256_batch.c /
    # loopbind_hd.c — net FEWER exempt functions). srmech_simd_tier is NOT
    # exempt (it asserts env_var != NULL + max_tier >= 0). See c/JPL_AUDIT.md.
    "srmech_simd_has_avx2",
    "srmech_simd_has_avx",
    "srmech_simd_has_sse2",
    # v0.7.0rc18 (F292 graft #3): srmech_simd_has_shani is the same kind of
    # pure cpuid feature detector (leaf7 EBX bit29). srmech_sha256_shani.c
    # `__ror` is the 1-line rotate (like srmech_ror32 / srmech_sha256b__ror).
    "srmech_simd_has_shani",
    "srmech_sha256ni__ror",
}

# Maximum allowed function length (JPL Rule 4).
RULE_4_MAX_LINES: int = 60

# Minimum allowed asserts per non-exempt function (JPL Rule 5).
RULE_5_MIN_ASSERTS: int = 2


def _scan_functions(path: Path) -> list[tuple[str, int, int]]:
    """Crude C function scanner — returns ``(name, lines, asserts)``
    per function defined in `path`. Same algorithm the
    JPL_AUDIT.md audit script uses; pure regex + brace counting.

    Limitations: this isn't a real C parser. It assumes srmech's
    formatting conventions: function definitions are at column 0,
    parameter list opens on the definition line, body brace opens
    on the next line OR same line.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    # Track {definition_line_idx: (name, fn_body_open_idx)}
    fn_starts: list[tuple[str, int]] = []

    def_pat = re.compile(
        r"^[a-zA-Z_][a-zA-Z_0-9 \t\*]+[ \t\*]([a-zA-Z_][a-zA-Z_0-9]+)\s*\("
    )
    for i, line in enumerate(lines):
        # Skip declarations (semicolon-terminated)
        if line.rstrip().endswith(";"):
            continue
        m = def_pat.match(line)
        if m is None:
            continue
        # Skip typedef / forward decl shapes
        if line.lstrip().startswith(("typedef", "static const",
                                     "extern", "#")):
            continue
        # Confirm an open brace appears within the next ~5 lines
        for look in range(i, min(i + 10, len(lines))):
            if "{" in lines[look] and not lines[look].lstrip().startswith("/*"):
                fn_starts.append((m.group(1), i))
                break

    # For each detected function start, count brace depth to find
    # the closing brace + count asserts in between.
    out: list[tuple[str, int, int]] = []
    for name, start_idx in fn_starts:
        depth = 0
        asserts = 0
        end_idx = start_idx
        # Find first '{'
        body_start = start_idx
        while body_start < len(lines) and "{" not in lines[body_start]:
            body_start += 1
        if body_start >= len(lines):
            continue
        depth = lines[body_start].count("{") - lines[body_start].count("}")
        for j in range(body_start + 1, len(lines)):
            depth += lines[j].count("{") - lines[j].count("}")
            if "assert(" in lines[j]:
                asserts += 1
            if depth == 0:
                end_idx = j
                break
        out.append((name, end_idx - start_idx + 1, asserts))
    return out


def test_rule_4_function_length_under_60() -> None:
    """JPL Rule 4: every function ≤ 60 lines."""
    violations: list[str] = []
    for f in sorted(_C_SRC_DIR.glob("*.c")):
        for name, lines, _ in _scan_functions(f):
            if lines > RULE_4_MAX_LINES:
                violations.append(
                    f"{f.name}::{name} = {lines} lines (> {RULE_4_MAX_LINES})"
                )
    assert not violations, "Rule 4 violations: " + "; ".join(violations)


def test_rule_5_minimum_two_asserts_per_function() -> None:
    """JPL Rule 5: every non-exempt function has ≥ 2 assertions."""
    violations: list[str] = []
    for f in sorted(_C_SRC_DIR.glob("*.c")):
        for name, _, asserts in _scan_functions(f):
            if name in RULE_5_EXEMPT_FUNCTIONS:
                continue
            if asserts < RULE_5_MIN_ASSERTS:
                violations.append(
                    f"{f.name}::{name} has {asserts} asserts "
                    f"(< {RULE_5_MIN_ASSERTS}); add asserts or document "
                    f"in RULE_5_EXEMPT_FUNCTIONS with rationale"
                )
    assert not violations, "Rule 5 violations: " + "; ".join(violations)


def test_rule_8_no_multiline_macros() -> None:
    """JPL Rule 8: no multi-line macros, no token-paste, no varargs."""
    forbidden = re.compile(r"##|__VA_ARGS__|\\\s*$")
    for f in _c_files():
        text = f.read_text(encoding="utf-8")
        for i, line in enumerate(text.split("\n"), 1):
            # Only check inside #define lines
            stripped = line.lstrip()
            if not stripped.startswith("#define"):
                continue
            if forbidden.search(line):
                pytest.fail(
                    f"{f.name}:{i}: Rule 8 violation — "
                    f"multi-line macro / token-paste / VA_ARGS in "
                    f"#define: {line.rstrip()!r}"
                )


def test_audit_doc_present_and_mentions_all_rules() -> None:
    """Sanity check: JPL_AUDIT.md exists and references every rule
    by number, so an auditor can find the rationale per rule."""
    audit = _C_SRC_DIR.parent / "JPL_AUDIT.md"
    assert audit.exists(), f"missing {audit}"
    text = audit.read_text(encoding="utf-8")
    for n in range(1, 11):
        marker = f"Rule {n}"
        assert marker in text, (
            f"JPL_AUDIT.md does not mention {marker!r}"
        )
