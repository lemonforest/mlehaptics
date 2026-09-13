"""rc473 — the fail-not-skip branch actually fires (`#T1188`).

``tests/test_value_status_c_boundary_rc473.py`` claims that a library which is
present on disk but does not load FAILS rather than skips. On a healthy native
cell that branch is never taken, so the claim would otherwise be asserted and
never executed — an instrument that cannot return otherwise.

This probe drives the classifier through all three cells and prints what each
returns, so the claim is measured. It does not modify the tree: the pure and
broken cells are built by rebinding the module's own two inputs.

Usage::

    PYTHONPATH=docs/srmech/python uv run --python 3.12 --no-project --offline \\
        python docs/srmech/notes/_rc473_cell_classification_probe.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python" / "tests"))

import test_value_status_c_boundary_rc473 as mod  # noqa: E402

from srmech import _native  # noqa: E402


def classify() -> str:
    """Run the classifier and name which of the three outcomes it took."""
    try:
        mod.test_the_cell_is_classified()
    except BaseException as exc:  # noqa: BLE001 - classifying, not handling
        return "%s: %s" % (type(exc).__name__, str(exc).splitlines()[0][:90])
    return "returned (no failure raised)"


def main() -> int:
    real_has_native = _native.HAS_NATIVE
    real_files = mod._LIB_FILES

    # 1. The live cell, whatever it is.
    print(json.dumps({
        "cell": "as-loaded",
        "has_native": real_has_native,
        "lib_files": [p.name for p in real_files],
        "outcome": classify(),
    }, sort_keys=True))

    # 2. BROKEN: a library file is on disk and HAS_NATIVE is False. This is the
    #    state that must FAIL. It is the state a stale or ABI-mismatched
    #    artifact produces, and the one in which every native gate in the tree
    #    silently degrades to a skip.
    _native.HAS_NATIVE = False
    mod._LIB_FILES = real_files or [Path("libsrmech.so")]
    print(json.dumps({
        "cell": "library-present-but-not-loaded",
        "has_native": False,
        "lib_files": [p.name for p in mod._LIB_FILES],
        "outcome": classify(),
    }, sort_keys=True))

    # 3. PURE: nothing on disk to load. A legitimate cell; must NOT fail.
    mod._LIB_FILES = []
    print(json.dumps({
        "cell": "genuinely-pure",
        "has_native": False,
        "lib_files": [],
        "outcome": classify(),
    }, sort_keys=True))

    _native.HAS_NATIVE = real_has_native
    mod._LIB_FILES = real_files
    return 0


if __name__ == "__main__":
    assert pytest is not None
    raise SystemExit(main())
