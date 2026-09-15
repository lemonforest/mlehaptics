"""A pytest plugin that counts what collection REMOVED, however the removal was spelled.
(rc473 instrument repair 1, `#T1188`)

Loaded with ``-p tests._collection_count_plugin`` by ``tools/ripple_check.py``'s gate run and by
the COLLECTION check in ``tests/test_ripple_manifest_covers_known_gates.py``. It is not a test
module and asserts nothing. When ``SRMECH_COLLECTION_COUNT_OUT`` names a file, it writes three
numbers there as JSON; when the variable is unset it writes nothing:

* ``collected`` — ``len(items)`` on ENTRY to ``pytest_collection_modifyitems``, read by a
  ``tryfirst`` hookwrapper before any implementation of that hook has run;
* ``selected`` — ``len(session.items)`` in a ``trylast`` ``pytest_collection_finish``, after every
  implementation, a conftest hookwrapper that filters after its own ``yield`` included;
* ``deselected`` — the total of every ``pytest_deselected`` call (``-k``, ``-m``, ``--deselect``,
  and the same options arriving through an ini ``addopts``, ``-o addopts=`` or ``PYTEST_ADDOPTS``).

WHY IT EXISTS
-------------
The rc473 instrument round gave ``ripple_check`` a DENY-list of narrowing options, and gate
round i1 ran ``-xk``, ``-qk``, ``-o addopts=-k …`` and ``--setup-plan`` straight past it. It gave
the manifest meta-test a collection check keyed on test FUNCTIONS, and a conftest hook that drops
one PARAMETRIZATION left it green. Both instruments asked how a filter was spelled; this one asks
whether anything was removed, so a new spelling of the same filter is not a new blind spot.

WHAT IT CANNOT SEE, stated
--------------------------
An item that never reaches ``pytest_collection_modifyitems``: ``--ignore`` / ``--ignore-glob``, a
conftest ``collect_ignore`` or ``pytest_ignore_collect``, a module that skips at collection, a
``pytest_generate_tests`` that generates fewer parameters, and a plugin disabled with ``-p no:``.
Nor a filter applied after collection finishes. The runner refuses those spellings by an
allow-list; the meta-test's AST comparison sees a whole test function that goes missing.

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import json
import os

import pytest

#: The environment variable naming the file the three counts are written to.
OUT_ENV = "SRMECH_COLLECTION_COUNT_OUT"

_STATE = {"collected": None, "selected": None, "deselected": 0}


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    _STATE["collected"] = len(items)
    yield


def pytest_deselected(items):
    _STATE["deselected"] += len(items)


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session):
    _STATE["selected"] = len(session.items)
    path = os.environ.get(OUT_ENV)
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(_STATE, fh)
