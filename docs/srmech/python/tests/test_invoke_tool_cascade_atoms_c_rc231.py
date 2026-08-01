"""rc231 — the CASCADE-ATOM invoke batch (#810): scalar Class-K / Class-C atoms
RUN in C through the ``srmech_invoke_tool`` dispatch spine.

rc188/189/190/191 wired the int / bytes / rational / float-carrier c_dispatched
tools into the invoke vtable. rc231 widens it to three scalar cascade atoms:

    magnitude(x: float) -> float                    (Class-K |x| pin-slot)
    pin_slot_at_zero(x: float) -> (int, float)      (Class-K split; a 2-list)
    net_chirality(orientations: [int]) -> int       (Class-C net handedness)

Each thunk mirrors its op's OWN native-dispatch boundary EXACTLY — the Python op
routes to the C symbol only for a FLOAT arg (magnitude / pin_slot) or an
int8-range plain-int LIST (net_chirality); every other shape (a JSON int for the
float atoms, a bool / out-of-int8 element, a non-list) takes the pure path with a
possibly-different result type/repr, so the C thunk DEFERS those. That keeps the
dispatched result BYTE-IDENTICAL to the pure ``serialise_result(invoke_tool(...))``.

THE PARITY PROOF (the DoD). For each dispatched case the C
``_native.invoke_tool_c(name, args)`` text == the pure
``serialise_result(invoke_tool(name, args))`` byte-for-byte; each off-boundary
case returns ``(False, None)`` and the pure path is the complete fallback.

No new C symbol / typedef — the thunks CALL the existing rc-earlier
``srmech_cascade_{magnitude,pin_slot_at_zero,net_chirality}_*`` kernels — so ABI
stays 4. The native-requiring assertions ``skipif`` cleanly with no C peer.
numpy-free (stdlib json + the srmech.mcp pure SSoT)."""
from __future__ import annotations

import random

import pytest

from srmech import _native
from srmech.mcp._tools import invoke_tool, serialise_result

_needs_native = pytest.mark.skipif(
    not _native.has_native_invoke(),
    reason="rc231 invoke cascade-atom C peer not loaded (pure / stale host)",
)

_BATCH_TOOLS = [
    "srmech.amsc.cascade.magnitude",
    "srmech.amsc.cascade.pin_slot_at_zero",
    "srmech.amsc.cascade.net_chirality",
]

# Dispatched (on-boundary) cases — the C invoke MUST run and match pure.
_DISPATCH_CASES = [
    ("srmech.amsc.cascade.magnitude", {"x": 2.5}),
    ("srmech.amsc.cascade.magnitude", {"x": -2.5}),
    ("srmech.amsc.cascade.magnitude", {"x": 0.0}),
    ("srmech.amsc.cascade.magnitude", {"x": 3.0}),
    ("srmech.amsc.cascade.pin_slot_at_zero", {"x": 2.5}),
    ("srmech.amsc.cascade.pin_slot_at_zero", {"x": -2.5}),
    ("srmech.amsc.cascade.pin_slot_at_zero", {"x": 0.0}),
    ("srmech.amsc.cascade.net_chirality", {"orientations": [1, -1, -1]}),
    ("srmech.amsc.cascade.net_chirality", {"orientations": [1, 0, -1]}),
    ("srmech.amsc.cascade.net_chirality", {"orientations": [-1, -1]}),
    ("srmech.amsc.cascade.net_chirality", {"orientations": []}),
    ("srmech.amsc.cascade.net_chirality", {"orientations": [1, 1, 1, 1]}),
]

# Off-boundary cases — the C thunk DEFERS (pure is the complete fallback).
_DEFER_CASES = [
    # a JSON int for a float atom -> pure returns an INT magnitude (repr "5", not
    # "5.0"); the thunk defers to stay byte-identical.
    ("srmech.amsc.cascade.magnitude", {"x": 5}),
    ("srmech.amsc.cascade.pin_slot_at_zero", {"x": 5}),
    # a bool element -> the op's own native guard rejects bools (False == 0
    # short-circuits via the Python loop); the thunk defers.
    ("srmech.amsc.cascade.net_chirality", {"orientations": [True, 1]}),
    # an out-of-int8 element -> the op takes the pure sign-normalising path.
    ("srmech.amsc.cascade.net_chirality", {"orientations": [1, 200]}),
]


@_needs_native
@pytest.mark.parametrize("name,args", _DISPATCH_CASES)
def test_native_invoke_matches_pure(name, args) -> None:
    """The C invoke_tool_c result text == the pure serialise_result(invoke_tool),
    byte-for-byte, for each on-boundary cascade-atom case."""
    dispatched, text = _native.invoke_tool_c(name, args)
    assert dispatched is True, (name, args)
    assert text == serialise_result(invoke_tool(name, args)), (name, args)


@_needs_native
@pytest.mark.parametrize("name,args", _DEFER_CASES)
def test_off_boundary_defers(name, args) -> None:
    """An off-boundary shape returns (False, None) — the pure path is the complete
    fallback (never a wrong answer, never a byte-mismatch)."""
    assert _native.invoke_tool_c(name, args) == (False, None), (name, args)


@_needs_native
def test_batch_dispatches_three_cascade_atoms() -> None:
    """The rc231 batch dispatches exactly the 3 scalar cascade atoms in C."""
    for name in _BATCH_TOOLS:
        disp, _text = _native.invoke_tool_c(
            name,
            {"x": 1.5} if "cascade.net_chirality" not in name
            else {"orientations": [1, -1]},
        )
        assert disp is True, name


@_needs_native
def test_native_invoke_matches_pure_random() -> None:
    """A random sweep of messy floats (magnitude / pin_slot) + random int8
    orientation lists (net_chirality) — byte-identical to pure. The floats do NOT
    round-trip cleanly under %.17g (that is the point — srmech_double_repr is the
    shortest-round-trip keystone shared with the rc190 mat carriers)."""
    rng = random.Random(2310)
    for _ in range(200):
        x = rng.uniform(-1e6, 1e6)
        args = {"x": x}
        disp, text = _native.invoke_tool_c("srmech.amsc.cascade.magnitude", args)
        assert disp and text == serialise_result(
            invoke_tool("srmech.amsc.cascade.magnitude", args)), args
        disp, text = _native.invoke_tool_c(
            "srmech.amsc.cascade.pin_slot_at_zero", args)
        assert disp and text == serialise_result(
            invoke_tool("srmech.amsc.cascade.pin_slot_at_zero", args)), args
        orients = [rng.randint(-128, 127) for _ in range(rng.randint(0, 12))]
        args = {"orientations": orients}
        disp, text = _native.invoke_tool_c(
            "srmech.amsc.cascade.net_chirality", args)
        assert disp and text == serialise_result(
            invoke_tool("srmech.amsc.cascade.net_chirality", args)), args


def test_helper_degrades_without_native() -> None:
    """Gate parity (always runs): with the C peer absent, invoke_tool_c returns
    (False, None) and the pure invoke_tool still answers — the dispatch is an
    accelerator, never a gate."""
    if not _native.has_native_invoke():
        assert _native.invoke_tool_c(
            "srmech.amsc.cascade.magnitude", {"x": 2.5}) == (False, None)
    # The pure op answers regardless of the native peer.
    assert serialise_result(
        invoke_tool("srmech.amsc.cascade.magnitude", {"x": 2.5})) == "2.5"
