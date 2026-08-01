"""rc242 (#840) — the C progress / introspection callback ABI parity test.

Exercises srmech_progress_cb_t + srmech_set_progress_cb end-to-end THROUGH the
C dispatch spine: register a ctypes trampoline as the process-global progress
callback, drive one tool call through the native ``invoke_tool_c`` spine, and
assert the C library emitted EXACTLY the canonical-JSON event the Python
srmech.introspect._event.serialize shape prescribes —

    {"category": <cat>, "mpr_version": "1.0", "op_name": <dotted name>}

built through the srmech_json keystone, so it is byte-identical to
``json.dumps({...}, sort_keys=True, ensure_ascii=False)``. This is the
everything-to-C completion of Class-H self-introspection: today the C library
emits nothing (introspection is Python-only); this callback lets a bare-C host
observe which op ran.

The native-requiring assertions ``skipif`` cleanly with no C peer (a stale
ABI-4 lib lacks srmech_set_progress_cb → the hook simply never fires, and the
Python-only introspection is unchanged). ABI 4 → 5 (the new callback typedef).
"""
from __future__ import annotations

import ctypes
import json

import pytest

from srmech import _native

# A proven batch-1 C-dispatchable tool (Class-C net handedness; cf.
# test_invoke_tool_cascade_atoms_c_rc231): an int8-range plain-int LIST in,
# one int out — always dispatches in C.
_OP = "srmech.cascade.net_chirality"
_ARGS = {"orientations": [1, -1, -1]}


def _has_progress_cb() -> bool:
    return bool(
        _native.HAS_NATIVE
        and _native.has_native_invoke()
        and hasattr(_native.LIB, "srmech_set_progress_cb")
    )


def _expected_event_json() -> str:
    """The event the C emit must produce, computed from the tool registry's
    OWN category for ``_OP`` (single source of truth: the C const table is
    generated from this Python registry, so the categories agree)."""
    from srmech.introspect import tool_schema as ts

    tools = ts.get_tool_schema().to_jsonable()["tools"]
    entry = next(t for t in tools if t["name"] == _OP)
    payload = {
        "category": entry["category"],
        "mpr_version": "1.0",
        "op_name": _OP,
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


@pytest.mark.skipif(
    not _has_progress_cb(),
    reason="native progress-callback ABI (rc242) not loaded",
)
def test_progress_cb_fires_once_with_canonical_event():
    captured: list[bytes] = []

    # Keep the trampoline referenced for as long as it is registered — ctypes
    # does NOT hold it, so a dropped reference would dangle inside the C lib.
    def _observer(event_json: bytes, _user_data: int) -> None:
        captured.append(event_json)

    trampoline = _native.PROGRESS_CALLBACK(_observer)
    null_cb = _native.PROGRESS_CALLBACK()  # NULL function pointer → clears

    try:
        _native.LIB.srmech_set_progress_cb(trampoline, None)

        dispatched, text = _native.invoke_tool_c(_OP, _ARGS)
        assert dispatched is True, "net_chirality must dispatch in C"
        assert text is not None

        # EXACTLY ONE emit per real materialisation (buf != NULL guard: a
        # NULL-buf size-query does not emit, so even a two-pass caller sees one).
        assert len(captured) == 1, (
            f"expected exactly one progress event; got {len(captured)}"
        )
        event = captured[0].decode("utf-8")
        assert event == _expected_event_json(), event

        # The event is well-formed canonical JSON with the introspect shape.
        parsed = json.loads(event)
        assert parsed["op_name"] == _OP
        assert parsed["mpr_version"] == "1.0"
        assert parsed["category"] == "cascade"
    finally:
        # Unregister BEFORE the trampoline leaves scope (a dangling C-side
        # pointer would segfault a later dispatch). Must run even on failure.
        _native.LIB.srmech_set_progress_cb(null_cb, None)


@pytest.mark.skipif(
    not _has_progress_cb(),
    reason="native progress-callback ABI (rc242) not loaded",
)
def test_progress_cb_off_by_default_emits_nothing():
    """With no callback registered (the default), a dispatch emits nothing —
    the hot path pays only a NULL-pointer test."""
    captured: list[bytes] = []

    def _observer(event_json: bytes, _user_data: int) -> None:
        captured.append(event_json)

    trampoline = _native.PROGRESS_CALLBACK(_observer)
    null_cb = _native.PROGRESS_CALLBACK()

    # Ensure the slot starts clear, dispatch, and confirm silence.
    _native.LIB.srmech_set_progress_cb(null_cb, None)
    try:
        dispatched, _text = _native.invoke_tool_c(_OP, _ARGS)
        assert dispatched is True
        assert captured == [], "no callback registered ⇒ no emit"

        # Registering then clearing returns the slot to silent.
        _native.LIB.srmech_set_progress_cb(trampoline, None)
        _native.invoke_tool_c(_OP, _ARGS)
        assert len(captured) == 1
        _native.LIB.srmech_set_progress_cb(null_cb, None)
        _native.invoke_tool_c(_OP, _ARGS)
        assert len(captured) == 1, "cleared callback must not fire again"
    finally:
        _native.LIB.srmech_set_progress_cb(null_cb, None)


def test_progress_callback_cfunctype_constructible():
    """The CFUNCTYPE trampoline is constructible even with no native lib —
    it mirrors the C srmech_progress_cb_t typedef wire format (void return,
    const char *event_json, void *user_data)."""
    cb_type = _native.PROGRESS_CALLBACK
    assert cb_type is not None

    def _noop(event_json, user_data):
        return None

    trampoline = cb_type(_noop)
    assert trampoline is not None
    # Two args, void return — the srmech_progress_cb_t shape.
    assert cb_type._restype_ is None
    assert list(cb_type._argtypes_) == [ctypes.c_char_p, ctypes.c_void_p]
