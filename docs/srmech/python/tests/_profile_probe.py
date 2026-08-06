"""rc410 (`#T1085`) — the PROFILE PROBE harness.

WHY THIS EXISTS
===============
srmech's own suite never activates a profile. There is no
``register_profile_tools`` / ``load_profile`` / ``SRMECH_PROFILE`` anywhere in
``conftest.py`` or in any CI workflow. So the measured owner census is a single
key — ``{'srmech': 556}`` — and therefore

    len(get_tool_schema().tools) == len(get_tool_schema().by_owner("srmech"))

**identically, today.** Every count assertion in the tree is green whichever of
those two it happens to ask for, which means a gate written on the WRONG AXIS
(total, when it means srmech's own) is indistinguishable from a correct one by
running the suite.

That is not a hypothetical. ``get_tool_schema()`` deliberately publishes
``srmech_tools + profile_tools`` (see its docstring), so a downstream consumer
that registers a profile and runs srmech's suite moves every unfiltered
aggregate. This module supplies the ONE bit of state that tells the two axes
apart, so a wrong-axis gate can be made to FAIL BEFORE and PASS AFTER.

OPT-IN ONLY — NEVER AUTOUSE, NEVER SUITE-WIDE
=============================================
``probe_profile`` is a plain (non-autouse) fixture. Request it explicitly in
the handful of assertions that need it. It is deliberately NOT installed in
``conftest.py``:

* rc409 declined a global ``_REGISTRY`` snapshot fixture on purpose, and that
  decision stands. A global clean-registry fixture would make rc409's shipped
  leak DETECTOR (``test_codegen_owner_guard_rc409.py::
  test_both_generators_still_run_on_a_clean_registry``) vacuous — it could
  never fire again. An instrument that cannot return otherwise is not a
  measurement.
* A suite-wide probe would move ``describe()["tools"]["total"]`` for all 74
  count assertions across 67 files, which are CORRECT as written and must stay
  green.

The snapshot/restore body is copied verbatim from
``test_codegen_owner_guard_rc409.py:68-85`` — same contract, same reason: the
mapping is restored IN PLACE because other modules hold a reference to the same
dict.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import pytest

import srmech.introspect.tool_schema as ts
from srmech.introspect.tool_schema import (
    ToolEntry,
    register_profile_tools,
)

#: The probe profile's owner. Must NOT be in ``RESERVED_OWNERS`` — registering a
#: reserved owner as a profile is refused by ``register_profile_tools`` (rc409).
PROBE_OWNER = "rc410probe"

#: The probe's single op name. Deliberately NOT ``test.``-prefixed: the six
#: name-prefix filters this rc corrects would otherwise silently pass it, and
#: the whole point is that a name-prefix is the wrong answer to an OWNER
#: question. Those filters excluded names beginning ``test.`` — which is
#: neither necessary (the two such injections in ``test_tool_schema.py`` are
#: owner ``"srmech"`` and are ``try``/``finally``-protected, so they do not
#: leak) nor sufficient (the one genuinely unprotected leak in that file is
#: owner ``"gamma"``, whose names a prefix test does not match at all).
PROBE_NAME = f"{PROBE_OWNER}.op"

#: Deliberately a category no srmech op uses, so ``by_category`` grows too.
PROBE_CATEGORY = "rc410probe_cat"


def probe_entry() -> ToolEntry:
    """The single profile-owned row the probe registers."""
    return ToolEntry(
        name=PROBE_NAME,
        owner=PROBE_OWNER,
        category=PROBE_CATEGORY,
        summary="rc410 probe row — a PROFILE-owned tool srmech does not own",
    )


@contextmanager
def probe_registered() -> Iterator[str]:
    """Register the probe for the duration of a ``with`` block; restore after.

    Preferred over the fixture when a test wants to measure the SAME expression
    before, during and after. That shape makes the assertion self-evidently
    non-vacuous — ``before == during == after`` cannot be satisfied by an
    expression that simply stopped looking, because ``before`` and ``after`` pin
    it to the real clean-registry value.
    """
    snapshot = dict(ts._REGISTRY)
    try:
        register_profile_tools(PROBE_OWNER, [probe_entry()])
        yield PROBE_OWNER
    finally:
        ts._REGISTRY.clear()
        ts._REGISTRY.update(snapshot)


@pytest.fixture()
def probe_profile() -> Iterator[str]:
    """Register ONE profile-owned ``ToolEntry``; restore ``_REGISTRY`` after.

    Yields the probe owner name. Snapshot/restore is mandatory: a row leaking
    out of a test would inflate ``describe()["tools"]["total"]`` for every later
    test in the same process, and 74 assertions across 67 files pin that number.
    """
    snapshot = dict(ts._REGISTRY)
    try:
        register_profile_tools(PROBE_OWNER, [probe_entry()])
        yield PROBE_OWNER
    finally:
        ts._REGISTRY.clear()
        ts._REGISTRY.update(snapshot)
