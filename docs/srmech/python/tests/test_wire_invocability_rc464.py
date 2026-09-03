"""rc464 (`#T1188`) — every entry this rc registered must actually be CALLABLE
THROUGH THE WIRE, not merely present in the registry.

WHY THIS FILE EXISTS AT ALL
===========================
It is `tests/test_wire_invocability_rc463.py` applied to the next rc, and the
reason is the finding that file records rather than a habit. rc463 registered
eighteen entries and no rc463 test drove a single one of them through
:func:`srmech.mcp._tools.invoke_tool`; **three of the eighteen turned out not to
be callable at all**, and a fourth was silently reachable at only one of the two
carrier rungs it advertised. All four worked fine in direct Python. The
transport was what was broken, so a test that imported the callables would have
passed on the defective tree.

rc464 registers FOURTEEN entries — the `cdr_*` [class]-binding adapters — and
they are a HARDER case than rc463's, not an easier one, on two counts:

* their declared parameters include structured ``dict`` state (``slots`` /
  ``codebook``), which is exactly the shape that has no obvious wire form;
* their sibling family, the 16-slot ``sed_*`` adapters, was never registered at
  all and is exempt from the tool-schema coverage gate on the stated ground
  that it is "reachable ONLY via the make_class class surface". rc464 does NOT
  inherit that exemption — it registers instead — so the claim that these are
  wire-reachable is a NEW claim this rc is making, and a new claim needs an
  instrument rather than a precedent.

WHAT THE ARGUMENTS BELOW ARE, AND WHY THEY ARE SPELLED THIS WAY
===============================================================
Each case passes the **WIRE FORM** of the state, not the in-process form: slot
maps are STR-keyed with LIST pairs (``{"0": ["alpha", 1]}``), because that is
what a JSON / ``srmech_mval_t`` DICT actually carries and what ``_cdr_rehydrate``
is written to normalise. Passing the in-process ``{0: ("alpha", 1)}`` here would
test a shape the wire cannot produce and would leave the real one unmeasured.

Codebooks are passed EMPTY. That is not a dodge: a value vector is a minted
32-byte HDC vector, JSON cannot carry it, and the register mints on demand — so
an empty codebook with an occupied slot map is a fully-wire-expressible NON-EMPTY
register, which is precisely the case worth proving reachable.

⚠️ **This gate deliberately calls ``invoke_tool`` and not the op.** Every one of
the fourteen works in direct Python; the point is the transport.

BLIND SPOT, STATED
==================
It exercises the in-process ``invoke_tool`` seam, so a defect living in JSON
*serialisation of the result* (outbound) is outside it — the same boundary
rc463's file draws.

numpy-free; no native library required.
"""

from __future__ import annotations

import pytest

from srmech.introspect.tool_schema import get_tool_schema, warmup_all
from srmech.mcp._tools import invoke_tool


#: (op name, wire-form kwargs). One row per entry rc464 registered.
CASES = [
    ("srmech.cascade.cdr_write",
     {"slot": 0, "key": "alpha", "dim": 4, "D": 256, "namespace": None,
      "codebook": {}, "slots": {}}),
    ("srmech.cascade.cdr_materialize",
     {"dim": 4, "D": 256, "namespace": None, "codebook": {},
      "slots": {"0": ["alpha", 1]}}),
    ("srmech.cascade.cdr_read_unbind",
     {"slot": 0, "dim": 4, "D": 256, "namespace": None, "codebook": {},
      "slots": {}}),
    ("srmech.cascade.cdr_clean", {"noisy": None, "codebook": {}}),
    ("srmech.cascade.cdr_slots", {"slots": {"0": ["alpha", 1]}}),
    ("srmech.cascade.cdr_working_block", {"dim": 16}),
    ("srmech.cascade.cdr_carry_block", {"dim": 16}),
    ("srmech.cascade.cdr_couple_working",
     {"vals": [1.5, -2.25, 3.0], "dim": 16, "coupling": True}),
    ("srmech.cascade.cdr_uncouple_working",
     {"word": [1.0, 0.0, 0.0, 0.0], "dim": 16, "coupling": True}),
    ("srmech.cascade.cdr_carry",
     {"overflow_bits": [1, 0, 1, 1], "dim": 16, "error_correction": True}),
    ("srmech.cascade.cdr_correct",
     {"codeword": [0, 1, 1, 0, 0, 1, 1], "dim": 16, "error_correction": True}),
    ("srmech.cascade.cdr_element", {"slots": {"0": ["alpha", 1]}, "dim": 4}),
    ("srmech.cascade.cdr_element_of",
     {"other": {"dim": 4, "slots": {}}, "dim": 4}),
    ("srmech.cascade.cdr_navigate",
     {"j": 1, "dim": 4, "D": 256, "namespace": None, "codebook": {},
      "slots": {"0": ["alpha", 1]}, "coupling": False,
      "error_correction": False}),
]

#: rc464 registered FOURTEEN entries (720 -> 734). Pinned so a row silently
#: dropped from the table above cannot make this file smaller and greener — the
#: failure mode a strict-zero sweep over a shrinking set cannot see.
EXPECTED_ROWS = 14


def _entry(name: str):
    warmup_all()
    e = get_tool_schema().lookup(name)
    assert e is not None, f"{name} is not in the live registry"
    return e


def test_the_table_covers_every_entry_this_rc_registered():
    """The roster is the population, so it must BE the population."""
    assert len(CASES) == EXPECTED_ROWS
    names = [n for n, _ in CASES]
    assert len(set(names)) == EXPECTED_ROWS, "duplicate row in CASES"
    live = {e.name for e in get_tool_schema().tools
            if e.name.startswith("srmech.cascade.cdr_")}
    assert set(names) == live, (
        f"the table and the registry disagree.\n"
        f"  in the table, not registered: {sorted(set(names) - live)}\n"
        f"  registered, not in the table: {sorted(live - set(names))}")


@pytest.mark.parametrize("name,kwargs", CASES, ids=[n for n, _ in CASES])
def test_every_rc464_registration_is_callable_through_invoke_tool(name, kwargs):
    """THE GATE. Not "is it in the registry" — "does it ANSWER over the wire".

    ``None`` is an accepted answer for exactly one op (``cdr_read_unbind`` on an
    empty register, the documented read short-circuit), so the assertion is that
    the call did not RAISE, checked separately from the value.
    """
    _entry(name)                       # registered at all
    result = invoke_tool(name, dict(kwargs))
    if name == "srmech.cascade.cdr_read_unbind":
        assert result is None, (
            "the empty-register short-circuit is the documented answer here; "
            "a non-None result means the wire reached a different state than "
            "the one these kwargs describe")
    else:
        assert result is not None, f"{name} returned None over the wire"


@pytest.mark.parametrize("name,kwargs", CASES, ids=[n for n, _ in CASES])
def test_the_wire_answer_equals_the_direct_python_answer(name, kwargs):
    """Callable is not enough — it must be callable and RIGHT.

    rc463's fourth finding was not a refusal but a silent DEMOTION: an op that
    answered over the wire, with no error, from only one of the two carrier
    rungs it advertised. A gate that stops at "did not raise" cannot see that
    class, so each row is compared against the same call made directly.
    """
    import importlib
    mod_path, _, attr = name.replace("srmech.cascade.",
                                     "srmech.cascade.cd_register.").rpartition(".")
    fn = getattr(importlib.import_module(mod_path), attr)
    assert invoke_tool(name, dict(kwargs)) == fn(**kwargs)


def test_the_str_keyed_wire_form_is_normalised_rather_than_rejected():
    """The load-bearing detail behind every row above. A slot map crossing JSON
    or the ``srmech_mval_t`` DICT arrives STR-keyed with LIST pairs; the
    in-process form is INT-keyed with TUPLE pairs. If the adapters rejected the
    wire form, every registration here would be reachable in name only.
    """
    wire = invoke_tool("srmech.cascade.cdr_slots",
                       {"slots": {"0": ["alpha", 1], "3": ["beta", -1]}})
    assert wire == {0: ("alpha", 1), 3: ("beta", -1)}
    # And it survives a round trip through an op that REBUILDS a register.
    routed = invoke_tool(
        "srmech.cascade.cdr_navigate",
        {"j": 1, "dim": 4, "D": 256, "namespace": None, "codebook": {},
         "slots": {"0": ["alpha", 1]}, "coupling": False,
         "error_correction": False})
    assert routed["slots"] == {1: ("alpha", 1)}
    assert routed["namespace"] == "CD4", "the None default must resolve"


def test_the_gate_would_fire_on_an_uncallable_entry():
    """The negative control. rc463's finding was that nothing measured this, so
    a gate that cannot come out otherwise would reproduce the defect it exists
    to end. Drive a registered op with an argument its own contract refuses and
    require the seam to report it."""
    with pytest.raises(Exception):
        invoke_tool("srmech.cascade.cdr_working_block", {"dim": 7})
