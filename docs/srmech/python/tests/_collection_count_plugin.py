"""A pytest plugin that counts the items a session COLLECTED, KEPT and RAN.
(rc473 instrument repairs 1 and 2, `#T1188`)

Loaded with ``-p tests._collection_count_plugin`` by ``tools/ripple_check.py``'s gate run and by
the COLLECTION check in ``tests/test_ripple_manifest_covers_known_gates.py``. It is not a test
module and asserts nothing. When ``SRMECH_COLLECTION_COUNT_OUT`` names a file, it writes four
numbers there as JSON at the end of the session; when the variable is unset it writes nothing:

* ``collected`` — the number of ``pytest_itemcollected`` calls;
* ``selected`` — ``len(session.items)`` in a ``trylast`` ``pytest_collection_finish``;
* ``deselected`` — the total of every ``pytest_deselected`` call (``-k``, ``-m``, ``--deselect``,
  and the same options arriving through an ini ``addopts``, ``-o addopts=`` or ``PYTEST_ADDOPTS``);
* ``ran`` — the number of ``setup``-phase ``pytest_runtest_logreport`` calls. pytest's own run
  protocol logs one per item it runs; under ``--collect-only`` nothing runs and it is 0.

WHY ``collected`` IS COUNTED WHERE IT IS
----------------------------------------
Instrument repair 1 read ``collected`` as ``len(items)`` on entry to
``pytest_collection_modifyitems``, in a ``tryfirst`` hookwrapper, and this docstring said that read
came "before any implementation of that hook has run". Gate round i2 measured that false: a
``tryfirst`` hookwrapper that filters before its ``yield``, in either wrapper style, from a conftest
or from a ``PYTEST_PLUGINS`` module, removed the item before that read, and the plugin wrote
``collected == selected``. Such a wrapper registers after this ``-p`` plugin, and pluggy enters the
later-registered one first.

``pytest_itemcollected`` does not depend on that order. In the two pytest versions whose source was
read for this repair, 9.0.3 and 9.1.1, ``Session.genitems`` calls it for each item as the item is
appended to ``session.items``, and ``Session.perform_collect`` calls
``pytest_collection_modifyitems`` only after that loop has finished. So in those versions no
implementation of that hook, registered in any order, runs before an item is counted. Other pytest
versions were not read.

WHAT IT WAS MEASURED TO REPORT
------------------------------
``notes/_rc473_instr_r2_order_probe.py`` runs a four-item sandbox in which each filter drops one
parametrization, collect-only and as a run. With this file, on Windows CPython 3.14.3 / pytest 9.0.3
and on WSL CPython 3.12.3 and 3.10.21 / pytest 9.1.1:

* ``selected`` below ``collected``, in both views: a ``pytest_collection_modifyitems`` that is
  plain, ``tryfirst``, or a ``tryfirst`` old-style hookwrapper filtering after its ``yield``, from a
  conftest; a ``tryfirst`` hookwrapper filtering BEFORE its ``yield``, old-style and new-style, from a
  conftest and from a ``PYTEST_PLUGINS`` module; and a ``tryfirst`` ``pytest_collection_finish``
  hookwrapper filtering before its ``yield``, from a conftest.
* ``deselected``: ``-k`` and ``-o addopts=-k``.
* ``ran`` below ``collected``, on a run only: a ``trylast`` ``pytest_collection_finish``, and a
  ``tryfirst`` ``pytest_runtestloop`` hookwrapper filtering before its ``yield``, each from a conftest
  and from a ``PYTEST_PLUGINS`` module; and a ``tryfirst`` ``pytest_runtest_protocol`` returning
  ``True`` for the item, from a conftest.

WHAT IT CANNOT SEE, stated
--------------------------
* An item that never reaches ``pytest_itemcollected``. Measured: a ``pytest_make_collect_report``
  hookwrapper that leaves the item out of its report wrote ``collected`` 3, ``selected`` 3, ``ran`` 3.
  Not planted, and not claimed either way: ``--ignore`` / ``--ignore-glob``, ``collect_ignore``,
  ``pytest_ignore_collect``, a module that skips at collection, a ``pytest_generate_tests`` or
  ``pytest_pycollect_makeitem`` that makes fewer items, and a plugin disabled with ``-p no:``.
* An item that runs and is then reported skipped, or whose report a hook rewrites. Measured: a
  ``pytest_runtest_setup`` that skips the item wrote ``ran`` 4 of 4.
* Under ``--collect-only``, a removal made after this plugin reads ``selected``. Measured, collect-only:
  the trylast ``pytest_collection_finish``, the ``pytest_runtestloop`` hookwrapper and the
  ``pytest_runtest_protocol`` above each wrote ``selected == collected``. A run's ``ran`` reports
  them, which is why ``tools/ripple_check.py`` reads ``ran`` and the collect-only COLLECTION check
  cannot.
* A plugin or conftest that replaces, unregisters or bypasses this plugin's hook implementations, and
  any pytest version other than the two read.

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import json
import os

import pytest

#: The environment variable naming the file the four counts are written to.
OUT_ENV = "SRMECH_COLLECTION_COUNT_OUT"

_STATE = {"collected": 0, "selected": None, "deselected": 0, "ran": 0}


def pytest_itemcollected(item):
    _STATE["collected"] += 1


def pytest_deselected(items):
    _STATE["deselected"] += len(items)


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session):
    _STATE["selected"] = len(session.items)


def pytest_runtest_logreport(report):
    if report.when == "setup":
        _STATE["ran"] += 1


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get(OUT_ENV)
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(_STATE, fh)
