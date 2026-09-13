"""rc473 — why the new ctest name carries NO in-body comment (`#T1188`).

Generating code for the warning written into ``CMakeLists.txt`` above
``set(SRMECH_C_TESTS_RC452 ...)``.

THE CLAIM UNDER TEST. ``tests/test_ctest_collection_parity_rc452.py::_registered``
resolves ``foreach(t ${LIST})`` through a ``set(LIST ...)`` block using

    re.finditer(r"set\\(\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+(.*?)\\)", text, re.S)

The second group is NON-GREEDY, so the capture ends at the FIRST ``)`` in the
body.  CMake ignores ``#`` comments inside a command's argument list, so a
comment there is invisible to the build and NOT invisible to this parse: a
``)`` inside one — for instance the closing paren of a backticked task id —
truncates the captured body and silently drops every name written after it.

The failure mode that makes this worth a probe: the build is FINE, the target
is compiled and run, and the gate reports the file as UNREGISTERED. The reader
is pointed at the registration, which is correct.

Usage::

    uv run --python 3.12 --no-project --offline \\
        python docs/srmech/notes/_rc473_cmake_set_parse_probe.py
"""

from __future__ import annotations

import json
import re

# The gate's own regex, copied verbatim from
# tests/test_ctest_collection_parity_rc452.py:88.
SET_RE = re.compile(r"set\(\s*([A-Za-z_][A-Za-z0-9_]*)\s+(.*?)\)", re.S)
NAME_RE = re.compile(r"test_srmech_[A-Za-z0-9_]+")

WITHOUT_COMMENT = """
        set(SRMECH_C_TESTS_RC452
            test_srmech_toml test_srmech_wz test_srmech_zeilberger
            test_srmech_value_status_rc473)
"""

# The exact shape that was written first: a comment carrying a backticked task
# id, placed between the old last name and the new one.
WITH_PAREN_COMMENT = """
        set(SRMECH_C_TESTS_RC452
            test_srmech_toml test_srmech_wz test_srmech_zeilberger
            # rc473 (`#T1188`) - the bare-C-HOST value/status gate.
            test_srmech_value_status_rc473)
"""

# A comment with no ")" at all, to isolate the cause: it is the paren, not the
# comment. Checking both directions rather than one.
WITH_PLAIN_COMMENT = """
        set(SRMECH_C_TESTS_RC452
            test_srmech_toml test_srmech_wz test_srmech_zeilberger
            # rc473 T1188 - the bare-C-HOST value/status gate.
            test_srmech_value_status_rc473)
"""


def parse(text: str) -> set[str]:
    """Exactly what the gate does: first set() match, names inside the capture."""
    names: set[str] = set()
    for match in SET_RE.finditer(text):
        names |= set(NAME_RE.findall(match.group(2)))
    return names


def main() -> int:
    target = "test_srmech_value_status_rc473"
    for label, text in (
        ("no comment in body", WITHOUT_COMMENT),
        ("comment containing ')'", WITH_PAREN_COMMENT),
        ("comment with no ')'", WITH_PLAIN_COMMENT),
    ):
        names = parse(text)
        print(json.dumps({
            "variant": label,
            "names_parsed": sorted(names),
            "n": len(names),
            "new_target_seen": target in names,
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
