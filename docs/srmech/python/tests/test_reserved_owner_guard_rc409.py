"""rc409 (`#T1080`) — `"srmech"` is a privileged sentinel that nothing reserved.

`owner == "srmech"` is a DECISION PREDICATE at six shipped sites — it is what
`get_tool_schema()` splits on to separate srmech's own tools from
profile-contributed ones, and what four native fast-path gates read to decide
whether the live registry still equals the compiled-in C table. Yet the profile
name validator accepted it: `_NAME_PATTERN` is `^[a-z][a-z0-9_-]*$`, and
``"srmech"`` matches. Measured at rc408, before this file existed::

    _NAME_PATTERN matches 'srmech'                    -> True
    reserved-name symbols in profile_loader           -> []      (census of 0)
    unregister_profile_tools("srmech")                -> 556, registry left EMPTY

**LATENT, NOT LIVE — and the label matters.** There are ZERO shipped callers of
`unregister_profile_tools`: a tree-wide grep returns the definition, the
``__all__`` entry, and five test callsites that all pass genuine profile names
(`fakets`, `alpha`, `beta`, `gamma`, `delta`). It is not an MCP tool and not a
CLI route, and there is no profile-deactivation path that could reach it. So
nothing in the shipped product wipes its own registry today. What rc409 closes
is a **public-API footgun reachable by any in-process caller** — including
profile package code running during activation — not an active bug.

TWO DOORS; THIS CLOSES ONE, AND SAYS SO
=======================================
The sentinel is unsound in two independent ways:

  * **COLLISION** — a profile legally named ``srmech`` registers rows that the
    fast-path predicate then reads as srmech's own, so the gate stays armed
    while the live registry no longer matches the C table. **rc409 closes this**
    at the root (`_validate_descriptor` refuses the name) and again at the
    boundary (`unregister_profile_tools` refuses it).
  * **VACUOUS TRUTH** — the predicate is spelled
    ``not any(e.owner != "srmech" for e in _REGISTRY.values())``, which is
    trivially ``True`` on an EMPTY registry, so a wiped registry SELECTS the
    native path. **rc409 does NOT close this.** It needs a direct
    registry-identity check, and verifying it end-to-end needs a rebuilt library
    at ABI 12. It is filed as its own rc; do not read this file as covering it.

WHY IT RAISES RATHER THAN RETURNING 0
=====================================
Returning 0 would make the call a silent no-op, and the caller that wrote
``unregister_profile_tools("srmech")`` meant something — it is a programming
error, not a legitimate empty removal. Raising names it at the callsite. This
also matches the module's house pattern (`register_profile_tools` raises
`ToolSchemaValidationError` on an owner mismatch) and keeps the guard visible
under ``python -O``, which a bare ``assert`` would not.
"""

from __future__ import annotations

import pytest

import srmech.introspect.tool_schema as ts
from srmech.introspect.tool_schema import (
    RESERVED_OWNERS,
    ToolEntry,
    ToolSchemaValidationError,
    get_tool_schema,
    register_profile_tools,
    unregister_profile_tools,
)


@pytest.fixture(autouse=True)
def _no_registry_leak():
    """Snapshot/restore the 556-entry registry around every test in this file.

    `tool_schema._REGISTRY` has NO autouse snapshot in `conftest.py`, unlike
    `path_registry._REGISTRY` next door (whose rc283 post-mortem is written up
    at `conftest.py:190-218`). This module registers profile-owned entries and
    asserts on registry SIZE, so it is exactly the shape that leaked there.
    Restoring the mapping IN PLACE (rather than rebinding the name) matters:
    other modules hold a reference to the same dict object.
    """
    snapshot = dict(ts._REGISTRY)
    try:
        yield
    finally:
        ts._REGISTRY.clear()
        ts._REGISTRY.update(snapshot)


def test_srmech_is_declared_reserved() -> None:
    """The census that was 0. A named constant is what makes it non-zero."""
    assert "srmech" in RESERVED_OWNERS


def test_unregister_profile_tools_refuses_the_reserved_owner() -> None:
    """STRICT. FAILED BEFORE rc409 by WIPING THE WHOLE REGISTRY.

    Measured on rc408: this call returned 556 and left `_REGISTRY` empty, so
    `get_tool_schema().tools` went to zero and `describe()["tools"]["total"]`
    reported 0. The assertion below is deliberately written against a snapshot
    taken at runtime rather than the literal 556 — pinning the number here
    would mint a 75th copy of a count that already has 74 pins across 67 files.
    """
    before = len(get_tool_schema().tools)
    assert before > 0, "registry is empty before the call - fixture is broken"

    with pytest.raises(ToolSchemaValidationError, match="reserved"):
        unregister_profile_tools("srmech")

    assert len(get_tool_schema().tools) == before, (
        "the registry changed despite the call being refused")


def test_a_genuine_profile_can_still_be_unregistered() -> None:
    """NEGATIVE CONTROL — the guard must not break the real use.

    Without this, a guard that refused EVERY name would pass the test above and
    silently disable profile teardown for everyone.
    """
    before = len(get_tool_schema().tools)
    register_profile_tools("rc409probe", [
        ToolEntry(name="rc409probe.op", owner="rc409probe",
                  category="test", summary="probe entry"),
    ])
    assert len(get_tool_schema().tools) == before + 1

    assert unregister_profile_tools("rc409probe") == 1
    assert len(get_tool_schema().tools) == before


def test_validate_descriptor_refuses_a_profile_named_srmech() -> None:
    """ROOT CAUSE. The name should never reach the registry in the first place.

    FAILED BEFORE rc409: `_NAME_PATTERN` matches ``srmech``, so a descriptor
    claiming the name validated cleanly and the profile's tools registered as
    srmech's own.
    """
    from srmech.profile_loader import InvalidProfileError, _validate_descriptor

    def descriptor(name: str) -> dict:
        return {
            "profile_schema_version": "1.0",
            "profile": {
                "name": name,
                "version": "1.0.0",
                "summary": "rc409 reserved-name probe",
                "package": "rc409_probe_pkg",
                "srmech_requires": ">=0.9",
            },
        }

    with pytest.raises(InvalidProfileError, match="(?i)reserved"):
        _validate_descriptor(descriptor("srmech"), "rc409-probe")

    # NEGATIVE CONTROL: an ordinary name must still validate. A guard that
    # rejected everything would pass the assertion above.
    _validate_descriptor(descriptor("ephemerides"), "rc409-probe")
