"""rc404 (`#T1069`) — a non-retryable decline must cost exactly ONE native call.

This is the BEHAVIOURAL half of the OVERFLOW/LIMIT split. Its C peer
(``c/test/test_srmech_status_discrimination_rc404.c``) asserts that the STATUS
discriminates; this file asserts that the discrimination actually reaches the
caller's grow-loop and changes what it does.

THE DEFECT, as measured at rc403. ``json_loads_c`` / ``toml_loads_c`` size an
arena, call the parser, and on ``SRMECH_ERR_OVERFLOW`` double the arena and try
again up to a 256 MiB cap. That is correct when the arena really was too small.
Through rc403 the C parsers also returned status 4 for conditions no arena can
fix — an integer outside int64, a numeric literal past the 64-byte staging
buffer, nesting past a compiled-in depth of 64 — so the loop allocated its way
to a verdict that was fixed before it started:

======================  ==============  ===============  =====================
document                 rc403 calls     rc403 arena      rc404
======================  ==============  ===============  =====================
JSON valid                          1         0.1 MiB     1 call, 0.1 MiB
JSON int > int64                    0 [#]_    0.0 MiB     1 call, 0.1 MiB
JSON 63-byte literal                0 [#]_    0.0 MiB     1 call, 0.1 MiB
JSON depth-80                      13       511.9 MiB     1 call, 0.1 MiB
TOML int > int64                   13       536.9 MiB     1 call, 0.1 MiB
TOML depth-80                      13       676.9 MiB     1 call, 0.1 MiB
======================  ==============  ===============  =====================

.. [#] Absorbed by the rc401 Python pre-scan ``_json_native_safe``, which
   existed ONLY because the two conditions shared a status. rc404 deletes it,
   so those rows go 0 calls -> 1 call. That is not a regression: 1 native call
   is the correct cost of parsing, and it replaces a full regex pass over the
   document. It is also a real assertion — a build that deleted the pre-scan
   WITHOUT re-statusing ``srmech_json.c`` would show 13 here, not 1.

NON-VACUITY. The ``valid`` rows pin ``calls == 1`` exactly, so a change that
stopped calling C at all would fail this file just as loudly as one that
restored the grow-loop. And the ceiling is on CALLS, not on wall time, so it
does not go quiet on a fast machine.

The arena figures above are why the ceiling is worth having at all: the answers
were CORRECT at rc403 throughout. This was never a wrong-value defect, so no
value-comparison test could have found it — only counting the work could.
"""

from __future__ import annotations

import ctypes

import pytest

from srmech import _json, _native, _toml

from tests._native_gate import require_native

#: A non-retryable condition must be decided on the FIRST parse.
MAX_CALLS_NON_RETRYABLE = 1

#: Generous ceiling on total arena bytes requested for one decline. The rc403
#: figures were 511.9-676.9 MiB; one first-try arena is ~0.1 MiB. 8 MiB leaves
#: room for the first-try sizing rule to change without making this brittle,
#: while still being ~64x below the smallest defect figure.
MAX_ARENA_BYTES_NON_RETRYABLE = 8 * 1024 * 1024


class _Counter:
    """Wrap a native entry point, recording call count and requested arena."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._inner = getattr(_native.LIB, name)
        self.calls = 0
        self.arena_bytes = 0

    def __call__(self, *args):
        self.calls += 1
        # Signature: (src, n, ws, ws_len, out). ws_len is index 3.
        ws_len = args[3]
        self.arena_bytes += int(getattr(ws_len, "value", ws_len))
        return self._inner(*args)


def _measure(entry: str, loads, text: str):
    """Run ``loads(text)`` with ``entry`` instrumented; return the counter."""
    counter = _Counter(entry)
    original = getattr(_native.LIB, entry)
    setattr(_native.LIB, entry, counter)
    try:
        try:
            loads(text)
        except (ValueError, TypeError):
            # A decline that falls through to the stdlib floor may raise; the
            # COST is what is under test, not the exception.
            pass
    finally:
        setattr(_native.LIB, entry, original)
    return counter


def _deep_json(depth: int = 80) -> str:
    return "[" * depth + "]" * depth


def _deep_toml(depth: int = 80) -> str:
    return "a = " + "[" * depth + "]" * depth + "\n"


_JSON_NON_RETRYABLE = [
    ("int > int64", "99999999999999999999"),
    ("63-byte literal", "1" * 70),
    ("depth-80 array", _deep_json()),
]

_TOML_NON_RETRYABLE = [
    ("int > int64", "a = 99999999999999999999\n"),
    ("depth-80 array", _deep_toml()),
]


def _assert_cheap(label: str, counter: "_Counter") -> None:
    assert counter.calls <= MAX_CALLS_NON_RETRYABLE, (
        f"{label}: {counter.calls} native calls for a NON-RETRYABLE decline "
        f"(want <= {MAX_CALLS_NON_RETRYABLE}).\n"
        f"The C parser is reporting a structural bound as SRMECH_ERR_OVERFLOW, "
        f"so the caller's grow-loop cannot tell it from arena exhaustion and "
        f"doubles its way to the cap. Re-status the site to SRMECH_ERR_LIMIT."
    )
    assert counter.arena_bytes <= MAX_ARENA_BYTES_NON_RETRYABLE, (
        f"{label}: {counter.arena_bytes / (1024 * 1024):.1f} MiB of arena "
        f"requested for a decline that could never succeed "
        f"(want <= {MAX_ARENA_BYTES_NON_RETRYABLE / (1024 * 1024):.0f} MiB)."
    )


@pytest.mark.parametrize("label,doc", _JSON_NON_RETRYABLE)
def test_json_non_retryable_declines_in_one_call(label: str, doc: str) -> None:
    require_native("srmech._json non-retryable decline cost")
    _assert_cheap(f"JSON {label}", _measure("srmech_json_parse", _json.loads, doc))


@pytest.mark.parametrize("label,doc", _TOML_NON_RETRYABLE)
def test_toml_non_retryable_declines_in_one_call(label: str, doc: str) -> None:
    require_native("srmech._toml non-retryable decline cost")
    _assert_cheap(f"TOML {label}", _measure("srmech_toml_parse", _toml.loads, doc))


def test_valid_documents_still_take_exactly_one_call() -> None:
    """The negative control: this gate is not 'never call C'.

    Without these rows, a change that disabled the native path entirely would
    satisfy every assertion above at 0 calls.
    """
    require_native("srmech native parse happy path")

    j = _measure("srmech_json_parse", _json.loads, '{"a": [1, 2, 3]}')
    assert j.calls == 1, f"a valid JSON document took {j.calls} native calls, want 1"

    t = _measure("srmech_toml_parse", _toml.loads, "a = 1\n")
    assert t.calls == 1, f"a valid TOML document took {t.calls} native calls, want 1"


def test_declines_are_still_CORRECT_not_merely_cheap() -> None:
    """Cost is the defect; correctness is the thing cost must not buy.

    rc404 makes the decline cheap. This asserts it did not make it WRONG — the
    parsed values must still match CPython exactly, via the stdlib floor.
    """
    require_native("srmech native decline correctness")
    import json as _stdlib_json

    assert _json.loads("99999999999999999999") == 99999999999999999999
    assert _json.loads(_deep_json()) == _stdlib_json.loads(_deep_json())
    assert _toml.loads("a = 99999999999999999999\n") == {"a": 99999999999999999999}


def test_limit_status_is_exposed_to_python() -> None:
    """The new status is bound, distinct, and not shadowing an existing one."""
    assert _native.SRMECH_ERR_LIMIT == 8
    assert _native.SRMECH_CANCELLED == 7
    assert _native.SRMECH_ERR_OVERFLOW == 4
    assert "SRMECH_ERR_LIMIT" in _native.__all__
    # rc404 also added the long-missing CANCELLED export alongside it.
    assert "SRMECH_CANCELLED" in _native.__all__
