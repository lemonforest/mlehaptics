"""rc476 (`#T1188`) — the CAN-FAIL control for the cross-drive path guard.

``tests/test_float_detour_class_rc476.py::test_the_scan_survives_a_path_it_cannot_relativise``
forces the Windows condition rather than waiting for a platform to supply it,
which raises the obvious question: would it have failed BEFORE the fix, or is it
a test that can only pass? An instrument that cannot return otherwise is not a
measurement, so this file answers it by execution.

It runs the scan twice under the SAME forced condition — ``os.path.relpath``
patched to raise exactly what a GitHub Windows runner raises
(``ValueError: path is on mount 'C:', start on mount 'D:'``, because pytest's
``tmp_path`` sits on ``C:`` while the checkout sits on ``D:``) — once with the
shipped ``_rel`` and once with the pre-fix one restored.

MEASURED (WSL2, CPython 3.12.3, numpy absent)::

    shipped _rel  -> OK, hits = 1 key = /tmp/tmpko6gm7up/planted.py
    pre-fix _rel  -> ValueError: path is on mount 'C:', start on mount 'D:'

so the ``try``/``except`` is load-bearing and the guard is not vacuous. The
originating failure is CI run 35395828855, ``windows-latest • py3.12``: five
``test_the_scan_fires_on_a_planted_site`` parametrisations, Windows only, green
on Linux and macOS because both paths share ``/`` there.

Usage (from ``docs/srmech/python``)::

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 ../notes/_rc476_canfail_cross_drive.py
"""

import os
import sys
import tempfile

sys.path.insert(0, "tests")
import test_float_detour_class_rc476 as M  # noqa: E402

tmp = tempfile.mkdtemp()
with open(os.path.join(tmp, "planted.py"), "w", encoding="utf-8") as fh:
    fh.write("x = 1\n    s = 1.0 / _fsqrt(deg[i])\n")


def pre_fix_rel(path):
    """``_rel`` as it stood before the repair — a bare, drive-naive relpath."""
    return os.path.relpath(path, M._SRMECH).replace(os.sep, "/")


def refuse(path, start):
    """Exactly what Windows raises when the two paths are on different drives."""
    raise ValueError("path is on mount 'C:', start on mount 'D:'")


# 1) the SHIPPED `_rel`, under the forced condition: must SURVIVE and still hit
os.path.relpath = refuse
hits = M._scan([tmp], (".py",), M.S1_PY, M._mask_py)
print("shipped _rel  ->", "OK, hits =", len(hits), "key =", hits[0][0])

# 2) the PRE-FIX `_rel`, same condition: must DIE — otherwise the guard proves
#    nothing, because the behaviour it asserts was never at risk
M._rel = pre_fix_rel
try:
    M._scan([tmp], (".py",), M.S1_PY, M._mask_py)
    print("pre-fix _rel  -> NO RAISE  <-- the guard would be VACUOUS")
except ValueError as exc:
    print("pre-fix _rel  -> ValueError:", exc)
