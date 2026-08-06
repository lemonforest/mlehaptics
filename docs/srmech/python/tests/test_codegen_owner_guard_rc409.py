"""rc409 (`#T1080`) — neither code generator refused PROFILE-owned rows.

`codegen_manifest.GENERATORS` holds six generators. **Two** walk the LIVE,
MUTABLE `srmech.introspect.tool_schema` registry, and both emitted whatever
they found with no owner filter:

===========================================  ==============================  =========
generator                                    output                          ships as
===========================================  ==============================  =========
``c/tools/gen_tool_registry.py``             ``c/src/srmech_tool_registry.c``  compiled in
``python/tools/gen_tool_docs.py``            ``srmech/introspect/_tool_docs.py``  in the wheel
===========================================  ==============================  =========

The second is the one that is easy to miss, and it is the one that reaches
users most directly — `_tool_docs.py` is read back by `describe()` and the MCP
tool list. If any profile is active in the generating interpreter, its tools
land in `get_tool_schema().tools` and are baked in **as srmech's own**, where
nothing downstream can tell them apart.

THIS CLOSES THE WRITE HALF OF A CONTRACT THAT ALREADY EXISTED
=============================================================
The READ side has enforced this all along: `tool_schema_view` plus three peers
in `introspect/{carrier,responsion,tool}_schema.py` and `mcp/_tools.py` all
refuse the C table the moment a profile tool is present, because the table is
only valid as a picture of the PURE srmech registry. Nothing enforced the same
thing when the table was WRITTEN. rc409 is not inventing an invariant; it is
closing the end that was never checked.

WHAT THIS IS *NOT*
==================
Not a stale-artifact check. The guard fires on a condition that is FALSE in a
clean codegen environment (measured owner census: ``{'srmech': 556}``), and the
emit path never branched on owner — ``gen_tool_registry.py:209`` writes
``t.owner`` unconditionally into a string pool where ``"srmech"`` already
lives. **Output is byte-identical**, which is why rc409 commits zero
regenerated C. `tests/test_regen_all_rc346.py::test_no_generated_file_is_stale`
is the independent proof of that, not an assumption made here.

DO NOT WIDEN TO THE OTHER FOUR GENERATORS
=========================================
They are genuinely out of class: `gen_carrier_registry` and
`gen_responsion_registry` read the static `_pure_*_schema` module tables, and
`gen_class_registry` reads TOML from disk without importing srmech at all. None
can observe a profile, so a guard there would be dead code asserting a
condition that cannot arise.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import srmech.introspect.tool_schema as ts
from srmech.introspect.tool_schema import (
    ToolEntry,
    ToolSchemaValidationError,
    register_profile_tools,
)

_SR_ROOT = Path(__file__).resolve().parents[2]           # docs/srmech
for _p in (_SR_ROOT / "python" / "tools", _SR_ROOT / "c" / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@pytest.fixture(autouse=True)
def _no_registry_leak():
    """Snapshot/restore `_REGISTRY` — this file REGISTERS into it.

    `tool_schema._REGISTRY` has no autouse snapshot in `conftest.py` (unlike
    `path_registry._REGISTRY`, whose rc283 post-mortem is at
    `conftest.py:190-218`). A profile entry leaking out of this module would
    inflate `describe()["tools"]["total"]` for every later test in the same
    process — and 74 assertions across 67 files pin that number. Restore the
    mapping IN PLACE; other modules hold a reference to the same dict.
    """
    snapshot = dict(ts._REGISTRY)
    try:
        yield
    finally:
        ts._REGISTRY.clear()
        ts._REGISTRY.update(snapshot)


def _register_intruder() -> None:
    register_profile_tools("rc409intruder", [
        ToolEntry(name="rc409intruder.leak", owner="rc409intruder",
                  category="test",
                  summary="a profile-owned row that must never be emitted"),
    ])


def test_c_registry_generator_refuses_profile_rows() -> None:
    """FAILS BEFORE: `generate()` returned normally and emitted the row."""
    import gen_tool_registry

    _register_intruder()
    with pytest.raises(ToolSchemaValidationError, match="PROFILE-owned"):
        gen_tool_registry.generate()


def test_tool_docs_generator_refuses_profile_rows() -> None:
    """FAILS BEFORE: `build_docs()` returned normally and seeded the entry.

    This is the generator whose output ships in the wheel.
    """
    import gen_tool_docs

    _register_intruder()
    with pytest.raises(ToolSchemaValidationError, match="PROFILE-owned"):
        gen_tool_docs.build_docs()


def test_both_generators_still_run_on_a_clean_registry() -> None:
    """NEGATIVE CONTROL — the guard must not fire on the normal path.

    Without this, a guard that raised unconditionally would satisfy both tests
    above while making `regen_all.py` permanently impossible. It also pins the
    fact the guard depends on: a clean interpreter has NO profile-owned rows.
    """
    import gen_tool_registry

    assert all(t.owner == "srmech" for t in ts._REGISTRY.values()), (
        "the registry already contains profile-owned rows before any test "
        "registered one - something leaked into this process")

    out = gen_tool_registry.generate()
    assert "srmech_tool_registry_table" in out
    assert "rc409intruder" not in out
