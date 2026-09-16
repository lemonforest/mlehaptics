"""A pytest plugin that counts the items a session COLLECTED, KEPT and RAN, and names the ids
that differ. (rc473 instrument repairs 1, 2 and 3, `#T1188`)

Loaded with ``-p tests._collection_count_plugin`` by ``tools/ripple_check.py``'s gate run and by
the COLLECTION check in ``tests/test_ripple_manifest_covers_known_gates.py``. It is not a test
module and asserts nothing. When ``SRMECH_COLLECTION_COUNT_OUT`` names a file, it writes one JSON
object there at the end of the session; when the variable is unset it writes nothing:

* ``collected`` — the number of ``pytest_itemcollected`` calls;
* ``selected`` — ``len(session.items)`` in a ``trylast`` ``pytest_collection_finish``;
* ``deselected`` — the total of every ``pytest_deselected`` call (``-k``, ``-m``, ``--deselect``,
  and the same options arriving through an ini ``addopts``, ``-o addopts=`` or ``PYTEST_ADDOPTS``);
* ``ran`` — the number of items whose protocol reached the ``call`` phase, plus those whose
  ``setup`` report was not ``passed`` (a skip or an error at setup ends the protocol there, and
  that item did run);
* ``selected_missing`` / ``selected_extra`` and ``ran_missing`` / ``ran_extra`` — the node ids in
  one of those two multisets and not in the other, each as ``{"n": <exact count>, "names":
  [<up to eight ids>]}``.

WHY THE IDS ARE THERE, AND WHY ``ran`` IS NOT A COUNT OF SETUP REPORTS
----------------------------------------------------------------------
Instrument repair 2 wrote four totals, and ``ran`` was the number of ``setup``-phase reports. Gate
round j1 measured two geometries that leave all four totals equal while the gate run did not run
what the manifest collects (Windows CPython 3.14.3 / pytest 9.0.3 and WSL 3.12.3 / pytest 9.1.1,
``notes/_rc473_instr_r3_probe.py`` over the four-item sandbox; both also measured in the real
geometry, `tools/ripple_check.py` exiting 0 on a one-file manifest):

* **a protocol that runs no test body.** ``--setup-plan`` or ``--setup-only``, arriving through an
  ini ``addopts`` or set on ``config.option`` by a ``conftest`` ``pytest_configure``, logs a
  ``setup`` report for every item and calls no test function: counts ``{4, 4, 0, 4}``, pytest "no
  tests ran", **zero** test bodies executed. Counting the ``call`` phase instead makes ``ran`` 0
  there, because that is the phase such a run skips;
* **a count-preserving substitution.** A ``pytest_collection_modifyitems`` that drops one item and
  appends a second reference to another leaves ``collected``, ``selected`` and ``ran`` at 4 while
  one item never runs and another runs twice. No count can show that — only the ids do.

The ids are compared as MULTISETS, so a repeat is as visible as an absence. The lists are capped at
eight names because a gate run collects thousands of items; ``n`` is exact.

WHERE ``collected`` IS COUNTED
------------------------------
Instrument repair 1 read ``collected`` as ``len(items)`` on entry to
``pytest_collection_modifyitems``, in a ``tryfirst`` hookwrapper, and its docstring said that read
came "before any implementation of that hook has run". Gate round i2 measured that false: a
``tryfirst`` hookwrapper that filters before its ``yield``, in either wrapper style, from a conftest
or from a ``PYTEST_PLUGINS`` module, removed the item before that read, and the plugin wrote
``collected == selected``. Such a wrapper registers after this ``-p`` plugin, and pluggy enters the
later-registered one first.

``pytest_itemcollected`` does not depend on that order. In the two pytest versions whose source was
read for these repairs, 9.0.3 and 9.1.1, ``Session.genitems`` calls it for each item as the item is
appended to ``session.items``, and ``Session.perform_collect`` calls
``pytest_collection_modifyitems`` only after that loop has finished. So in those versions no
implementation of that hook, registered in any order, runs before an item is counted. Other pytest
versions were not read.

WHAT IT WAS MEASURED TO REPORT
------------------------------
``notes/_rc473_instr_r2_order_probe.py`` and ``notes/_rc473_instr_r3_probe.py`` run four-item
sandboxes in which each filter drops one parametrization (or substitutes it), collect-only and as a
run. With this file, on Windows CPython 3.14.3 / pytest 9.0.3 and on WSL CPython 3.12.3 and 3.10.21
/ pytest 9.1.1:

* ``selected`` below ``collected``, in both views: a ``pytest_collection_modifyitems`` that is
  plain, ``tryfirst``, or a ``tryfirst`` old-style hookwrapper filtering after its ``yield``, from a
  conftest; a ``tryfirst`` hookwrapper filtering BEFORE its ``yield``, old-style and new-style, from
  a conftest and from a ``PYTEST_PLUGINS`` module; and a ``tryfirst``
  ``pytest_collection_finish`` hookwrapper filtering before its ``yield``, from a conftest.
* ``deselected``: ``-k`` and ``-o addopts=-k``.
* ``ran`` below ``collected``, on a run only: a ``trylast`` ``pytest_collection_finish``, and a
  ``tryfirst`` ``pytest_runtestloop`` hookwrapper filtering before its ``yield``, each from a
  conftest and from a ``PYTEST_PLUGINS`` module; a ``tryfirst`` ``pytest_runtest_protocol``
  returning ``True`` for the item, from a conftest; and — instrument repair 3 — a setup-only
  protocol from an ini ``addopts`` (``--setup-plan``, ``--setup-only``) or from a conftest
  ``pytest_configure``, where ``ran`` is 0 of 4.
* ``ran_missing`` and ``ran_extra`` both 1, with the counts unmoved, for the drop-and-duplicate
  substitution; ``selected_missing`` and ``selected_extra`` likewise, which is what the collect-only
  COLLECTION check reads.

WHAT IT CANNOT SEE, stated
--------------------------
* An item that never reaches ``pytest_itemcollected``. Measured: a ``pytest_make_collect_report``
  hookwrapper that leaves the item out of its report wrote ``collected`` 3, ``selected`` 3, ``ran``
  3 with no id difference. Not planted, and not claimed either way: ``--ignore`` / ``--ignore-glob``,
  ``collect_ignore``, ``pytest_ignore_collect``, a module that skips at collection, a
  ``pytest_generate_tests`` or ``pytest_pycollect_makeitem`` that makes fewer items, and a plugin
  disabled with ``-p no:``.
* An item that runs and is then reported skipped, or whose report a hook rewrites. Measured: a
  ``pytest_runtest_setup`` that skips the item wrote ``ran`` 4 of 4 — the item's protocol did start,
  and this plugin counts that as run.
* An item whose BODY is replaced while the item is collected, kept, run and reported passed.
  Measured (instrument repair 3): a ``tryfirst`` ``pytest_pyfunc_call`` returning ``True`` for one
  item wrote ``{4, 4, 0, 4}`` with no id difference, while three of four test bodies executed. That
  is the same class as editing the test, and no count or id of a run can show it.
* Under ``--collect-only``, a removal made after this plugin reads ``selected``. Measured,
  collect-only: the trylast ``pytest_collection_finish``, the ``pytest_runtestloop`` hookwrapper and
  the ``pytest_runtest_protocol`` above each wrote ``selected == collected`` with no id difference.
  A run's ``ran`` reports them, which is why ``tools/ripple_check.py`` reads ``ran`` and the
  collect-only COLLECTION check cannot.
* A plugin or conftest that replaces, unregisters or bypasses this plugin's hook implementations, and
  any pytest version other than the two read.

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import json
import os

import pytest

#: The environment variable naming the file the counts are written to.
OUT_ENV = "SRMECH_COLLECTION_COUNT_OUT"

#: Most node ids listed in one difference. ``n`` is exact; the names are a sample, because a gate
#: run of the whole manifest collects thousands of items.
MAX_NAMES = 8

_STATE = {"collected": 0, "selected": None, "deselected": 0, "ran": 0}
_COLLECTED: list = []
_SELECTED: list = []
_RAN: list = []


def pytest_itemcollected(item):
    _STATE["collected"] += 1
    _COLLECTED.append(item.nodeid)


def pytest_deselected(items):
    _STATE["deselected"] += len(items)


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session):
    _STATE["selected"] = len(session.items)
    _SELECTED[:] = [item.nodeid for item in session.items]


def pytest_runtest_logreport(report):
    # The CALL phase is the one a setup-only protocol skips, so an item counts as run when its
    # protocol reached it — or when its setup report is not `passed`, which ends the protocol
    # there for an item that did run (a skip or an error at setup).
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        _STATE["ran"] += 1
        _RAN.append(report.nodeid)


def _diff(left: list, right: list) -> dict:
    """The node ids in ``left`` and not in ``right``, as MULTISETS: an exact count and up to
    :data:`MAX_NAMES` names. An id repeated in ``left`` and present once in ``right`` is one
    difference, which is how a substitution shows up in the ids while every count stays equal."""
    pool: dict = {}
    for nodeid in right:
        pool[nodeid] = pool.get(nodeid, 0) + 1
    over = []
    for nodeid in left:
        if pool.get(nodeid):
            pool[nodeid] -= 1
        else:
            over.append(nodeid)
    return {"n": len(over), "names": sorted(over)[:MAX_NAMES]}


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get(OUT_ENV)
    if path:
        payload = dict(_STATE)
        payload["selected_missing"] = _diff(_COLLECTED, _SELECTED)
        payload["selected_extra"] = _diff(_SELECTED, _COLLECTED)
        payload["ran_missing"] = _diff(_COLLECTED, _RAN)
        payload["ran_extra"] = _diff(_RAN, _COLLECTED)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
