"""srmech's own internal JSON loader — the front door srmech's Python and
codegen use to read descriptor / manifest / catalog / provenance JSON.

Its PURPOSE is to run srmech's OWN parser wherever the native library is
present, the same self-hosting move ``sha256_bytes`` makes for hashing and
``srmech._toml`` makes for TOML (`#T907`). When the native library exposes
``srmech_json_parse``, :func:`loads` walks the C parse tree straight to a
Python object (`#T1008` slice 1). On a pure / Pyodide wheel (no native
library), or when the native path DECLINES a document, it falls back to the
stdlib ``json``.

That fallback is MANDATORY and is never removed: the C library is absent on
pure / Pyodide installs, so stdlib ``json`` remains the correctness path there.
Native-first is throughput; stdlib is the floor.

**This is the READ half only.** ``json.dumps`` is deliberately NOT self-hosted
here — see the write-half note at the bottom of this docstring.

The decline contract
--------------------
The native path is taken only when the C library is loaded AND exposes
``srmech_json_parse``. It then declines — returning ``None`` from
``_native.json_loads_c`` so control rides the stdlib parse — in two families of
case, and the distinction matters:

**A. The C parser itself refuses** (returns non-``SRMECH_OK``). These are
constructs outside its supported subset, and it is LOUD about them:

* ``NaN`` / ``Infinity`` / ``-Infinity`` — CPython's ``json`` accepts these
  non-standard literals; ``srmech_json`` matches only ``true``/``false``/``null``.
* a lone UTF-16 surrogate escape (``\\ud800`` with no trailing low surrogate,
  or a bare low surrogate) — CPython produces a lone-surrogate ``str``.
* nesting deeper than ``SRMECH_JSON_MAX_DEPTH`` (64).
* ordinary syntax errors, unterminated strings, trailing garbage, empty input.
* an arena that grew past the 256 MiB cap.

**B. srmech declines pre-emptively**, because the C parser would return
``SRMECH_OK`` with a value that DISAGREES with CPython. These are the dangerous
ones — a status check alone cannot catch them — and
``_native._json_native_safe`` scans for them before any C call:

* an integer outside int64: ``srmech_json.c`` parses with a bare ``strtoll``
  and never checks ``errno``, so ``99999999999999999999`` would CLAMP to
  ``INT64_MAX``. CPython returns the exact int, so srmech declines and the
  floor returns the exact int too.
* a number literal 63 bytes or longer (the C scanner's fixed staging buffer).
* a malformed number the C scanner accepts loosely — its character class is
  ``[0-9.eE+-]``, so ``01``, ``1.2.3``, ``1e``, ``--1`` and a bare ``-`` are all
  swallowed and handed to ``strtoll``/``strtod``, which stop at the first bad
  byte and yield a value where CPython raises.
* any ``\\u0000`` escape (conservative: only an object KEY is actually
  corrupted, since keys are stored NUL-terminated and re-measured with
  ``strlen``, but declining on either is cheap).

Declining is always SAFE: it costs a stdlib parse, never correctness.

Two consequences worth relying on
---------------------------------
1. **Every exception comes from the stdlib floor.** The native path never
   raises for bad input — it declines — so a caller's
   ``except json.JSONDecodeError`` keeps working unchanged at every repointed
   call site, with byte-identical message and position.
2. **Floats are the stdlib's.** ``srmech_json.c`` parses doubles with
   ``strtod``, which is correctly rounded, matching CPython's ``float()``. This
   is checked directly by ``tests/test_json_read_selfhost_rc401.py`` rather
   than assumed.

The write half is NOT here (deferred to rc402/rc403)
----------------------------------------------------
``srmech_json_write_ws`` exists and is byte-identical to
``json.dumps(obj, sort_keys=True, ensure_ascii=False)`` — but only for that ONE
keyword combination. Measured across the tree, the ``json.dumps`` call sites use
``ensure_ascii`` (21), ``sort_keys`` (20), ``separators=`` (7), ``indent=`` (5),
and — the actual blocker — ``default=`` (4), which passes a PYTHON CALLABLE the
C writer cannot honour without an ABI change. The write half is therefore not a
drop-in and is deliberately left for its own rc rather than half-done here.

This is an INTERNAL module. It registers no ToolEntry, adds nothing to
``describe()`` / introspect / MCP, and is not one of the 14 A-N compute
capabilities — it is plumbing srmech calls on itself.
"""

from __future__ import annotations

import json as _stdlib_json
from typing import Any


def loads(text: str) -> Any:
    """Parse a JSON string — native ``srmech_json`` first, stdlib floor.

    The native path is taken only when the C library is loaded AND exposes
    ``srmech_json_parse``; if it DECLINES the document (see the module
    docstring's decline contract) control rides the stdlib parse, so the value —
    and any genuine ``json.JSONDecodeError`` — is identical to the pure path.

    Accepts ``bytes`` / ``bytearray`` as well as ``str``, matching
    ``json.loads``.
    """
    if isinstance(text, (bytes, bytearray)):
        text = bytes(text).decode("utf-8")
    from . import _native

    if (
        _native.HAS_NATIVE
        and getattr(_native, "LIB", None) is not None
        and hasattr(_native.LIB, "srmech_json_parse")
    ):
        obj = _native.json_loads_c(text)
        if obj is not None:
            return obj
    return _stdlib_json.loads(text)


def load(fp) -> Any:
    """Parse a JSON document from a file object (mirrors ``json.load``).

    Accepts a handle opened in binary (``'rb'``) or text mode; the bytes are
    decoded as UTF-8 before parsing, so both work.
    """
    data = fp.read()
    if isinstance(data, (bytes, bytearray)):
        data = bytes(data).decode("utf-8")
    return loads(data)
