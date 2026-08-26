#!/usr/bin/env python3
"""Audit the ``pure-by-design`` skips of a no-native pytest run (rc351, task `#T1004`).

``SRMECH_EXPECT_PURE=1`` lets a native-parity test skip instead of failing when the
library is absent BY DESIGN. That is a necessary excuse and therefore a dangerous one:
left unaudited it is a mute button, and a cell that goes green by learning to ignore
things is worse than no cell.

So the excuse is COUNTED, both ways, against the tree itself — never against a frozen
number (that would be its own defect):

* **DECLARED** — every ``require_native("…")`` call site under ``tests/``, read out of
  the source. This is the set of gates that exist. A reason that INTERPOLATES a value
  (``"…(ABI %d)" % EXPECTED_ABI_VERSION``) is paired as a PATTERN against the message it
  produces, so deriving a constant instead of re-spelling it does not blind the audit —
  see :data:`_PLACEHOLDER_RE` for the red that taught this.
* **OBSERVED** — every ``pure-by-design: …`` skip reason in the run's ``-rs`` output.
  This is the set of gates that actually fired.

The two sets must be EQUAL.

* A gate that fired but is not declared is impossible by construction; if it ever
  happens, something is generating skips this audit cannot account for.
* **A declared gate that did NOT fire is the failure that matters.** It means a test
  stopped reaching its gate — it was deleted, renamed, filtered out, or is now being
  skipped earlier for an unrelated reason. A seam that silently stops observing is
  exactly the false-green shape this whole rc is about, so it is RED here.

Adding an eleventh gated test is therefore a deliberate, visible act: the declared set
grows, the observed set grows with it, and the audit stays green only if the gate
genuinely fires. Nothing about this mechanism can excuse a pure-path DEFECT — a gate is
evaluated before the test body runs and cannot convert a failure into a skip.

Usage::

    python3 tools/audit_pure_by_design_skips.py <pytest-output.log> [tests-dir]

Exit 0 on agreement, 1 with a GitHub-Actions ``::error::`` annotation otherwise.
"""

from __future__ import annotations

import pathlib
import re
import sys

#: The tag :func:`tests._native_gate.require_native` stamps on every skip it issues.
#: Matched structurally rather than by prose so a reworded reason cannot silently
#: empty the observed set.
_OBSERVED_RE = re.compile(r"pure-by-design:\s*(.+?)\s+needs the native library")

#: The call sites, read out of the test sources. Single- or double-quoted.
#: The ``(?<![\w.])`` lookbehind is load-bearing: three test files predate this gate
#: and carry their OWN per-symbol ``_require_native(...)`` helper. Without the
#: lookbehind those call sites are swept in as declared-but-never-fired and the audit
#: reports a false failure — measured on the first run of this script.
_DECLARED_RE = re.compile(r"""(?<![\w.])require_native\(\s*(["'])(.+?)\1""", re.S)

#: DECLARED is read from SOURCE, OBSERVED from a RUNTIME message, so the two are only
#: equal as literals when the reason interpolates nothing. That contract was implicit
#: for 53 gates and cost a CI red the first time one derived a value instead of
#: re-spelling it: rc455 changed the exact-Q floor's reason from a hard-coded
#: ``ABI 23`` to ``"…(ABI %d…)" % EXPECTED_ABI_VERSION`` — the RIGHT move, since a
#: re-spelled constant goes stale at every bump — and the audit then reported the same
#: gate as both never-fired (``ABI %d``) and undeclared (``ABI 24``). Deriving the
#: number is not the defect; an instrument that cannot read a derived reason is. So a
#: declared literal carrying a placeholder is paired as a PATTERN against the message
#: it produces. ``%d`` narrows to digits rather than ``.+?`` so the widened match stays
#: as tight as the format string itself.
_PLACEHOLDER_RE = re.compile(r"%[difgsr]")


def _as_matcher(literal: str) -> re.Pattern[str] | None:
    """The pattern a declared literal's RUNTIME message must match, or ``None`` when
    the literal interpolates nothing and plain equality is the stricter test."""
    holes = _PLACEHOLDER_RE.findall(literal)
    if not holes:
        return None
    parts = _PLACEHOLDER_RE.split(literal)
    out = re.escape(parts[0])
    for hole, tail in zip(holes, parts[1:]):
        out += (r"\d+" if hole == "%d" else r".+?") + re.escape(tail)
    return re.compile(rf"\A{out}\Z", re.S)


def declared(tests_dir: pathlib.Path) -> set[str]:
    """Every ``require_native("…")`` argument under ``tests_dir`` (the gate's own file
    excluded — its docstring shows the call form and is not a call site)."""
    out: set[str] = set()
    for path in sorted(tests_dir.glob("test_*.py")):
        for _q, what in _DECLARED_RE.findall(path.read_text(encoding="utf-8")):
            out.add(what)
    return out


def observed(log: pathlib.Path) -> set[str]:
    """Every distinct gate that actually issued a skip in this run."""
    text = log.read_text(encoding="utf-8", errors="replace")
    return set(_OBSERVED_RE.findall(text))


def main(argv: list[str]) -> int:
    if not 2 <= len(argv) <= 3:
        print(__doc__)
        return 2
    log = pathlib.Path(argv[1])
    tests_dir = pathlib.Path(argv[2]) if len(argv) == 3 else pathlib.Path("tests")
    if not log.exists():
        print(f"::error::pytest log {log} not found — the audit cannot run blind")
        return 1

    dec, obs = declared(tests_dir), observed(log)
    print(f"declared require_native() gates : {len(dec)}")
    print(f"observed pure-by-design skips   : {len(obs)}")

    if not dec:
        print("::error::no require_native() call sites found — either the gate was "
              "removed or this audit is pointed at the wrong tree. A guard that "
              "cannot fire is not a guard.")
        return 1

    # Plain literals pair by EQUALITY, which is the stricter test and stays the rule for
    # 53 of the 54 gates. Only a literal that interpolates falls back to its pattern.
    plain = {d for d in dec if not _PLACEHOLDER_RE.search(d)}
    missing = sorted(plain - obs)        # declared but never fired
    accounted = obs & plain
    for d in sorted(dec - plain):
        hits = {o for o in obs if _as_matcher(d).match(o)}
        if hits:
            accounted |= hits
        else:
            missing.append(d)
    missing.sort()
    extra = sorted(obs - accounted)      # fired but not declared

    if missing:
        print("::error::these native gates were DECLARED but never fired — a test "
              "stopped reaching its gate (deleted, renamed, filtered, or skipped "
              "earlier for another reason). A seam that stops observing is a false "
              "green:")
        for w in missing:
            print(f"  - {w}")
    if extra:
        print("::error::these pure-by-design skips have no require_native() call "
              "site — something is generating skips this audit cannot account for:")
        for w in extra:
            print(f"  - {w}")
    if missing or extra:
        return 1

    print(f"OK: all {len(dec)} declared native gates fired, and nothing else did.")
    for w in sorted(dec):
        print(f"  · {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
