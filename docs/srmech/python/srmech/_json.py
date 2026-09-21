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

**B. the C parser declines a value it cannot represent.** An integer outside
int64 returns ``SRMECH_ERR_OVERFLOW``: JSON legitimately permits such integers
and ``int64_t`` genuinely cannot hold them, so srmech declines and the floor
returns the exact int. (Inside srmech's own corpus these ride the rc176
decimal-STRING bignum transport instead — see ``srmech_carrier_marshal.c``.)

.. note::

   **This list used to be longer, and that is the point.** At rc401 category B
   was a set of pre-emptive PYTHON-side workarounds for three places where
   ``srmech_json.c`` returned ``SRMECH_OK`` with a WRONG VALUE — the one shape a
   status check cannot catch. rc402 (`#T1068`) fixed all three in the C parser:
   an out-of-int64 integer CLAMPED to ``INT64_MAX`` (``strtoll``'s ``ERANGE``
   was never read); the loose ``[0-9.eE+-]`` scanner turned ``--1`` and a bare
   ``-`` into ``0``, ``01`` into ``1`` and ``1.2.3`` into ``1.2``; and an object
   KEY carrying a NUL escape came back silently TRUNCATED. The C parser now
   declines each one with a status the caller can SEE, so the Python guard
   shrank to a single arena-grow FAST PATH and is no longer load-bearing for
   correctness. The int64 clamp had been known since **rc176**, where a bignum
   transport was built beside it rather than fixing it.

Declining is always SAFE: it costs a stdlib parse, never correctness.

Two consequences worth relying on
---------------------------------
1. **Every exception comes from the stdlib floor.** The native path never
   raises for bad input — it declines — so a caller's
   ``except json.JSONDecodeError`` keeps working unchanged at every repointed
   call site, with byte-identical message and position.
2. **Numbers are read EXACTLY — contract A, rc479 (`#T1188`).** A decimal
   literal is the rational it already names, so ``{"x": 0.1}`` loads as
   ``Q(1, 10)`` and not as binary64's ``3602879701896397 / 2**55``. The floor
   installs :func:`srmech.math.q.parse_float_exact` as its ``parse_float=``
   default; ``nan`` / ``inf`` / ``-inf`` never reach it on this front door
   (CPython's ``json`` routes them through ``parse_constant``), and ``-0.0``
   stays the float it is because ``Q`` has no signed zero (rule Z1).

   **Category C of the decline contract** follows from it, and it is what keeps
   the two projections equal: ``srmech_json.c`` yields a C ``double`` and no C
   value layer in this library can hold a rational (measured — ``dv_value_t``
   and ``srmech_mval_t`` both carry ``double``), so the native path DECLINES
   any document carrying a floating literal and the floor answers with the
   exact ``Q``. A native cell and a pure cell therefore return the SAME object
   for the same document, which silently returning doubles from C would not.
   The cost is one wasted C parse on such a document; correctness is never at
   stake, which is the decline contract's whole point.

   rc402 ADJUDICATED the ``strtod`` path and deliberately left it alone:
   ``strtod`` returns ``HUGE_VAL`` on overflow and ``0.0`` on underflow, which
   is exactly what CPython's ``json`` does (``1e400`` -> ``inf``, ``1e-400`` ->
   ``0.0``, ``5e-324`` -> the smallest subnormal), so adding an ``errno`` check
   there would have REGRESSED parity by declining input CPython accepts. **That
   adjudication is PROJECTION-SCOPED as of rc479, not retracted**: it stays
   true of the DOUBLE projection a bare-C host reads, and it is not a statement
   about the exact one, which has no double to round. It is pinned in
   ``c/test/test_srmech_json_number_rc402.c``. What rc479 DOES change in C is
   the other end: a literal past the A1 digit bound now returns
   ``SRMECH_ERR_LIMIT`` rather than ``inf``, so both projections refuse the
   same token.

The write half is still NOT here — and rc403 re-measured why
------------------------------------------------------------
``srmech_json_write_ws`` is byte-identical to
``json.dumps(obj, sort_keys=True, ensure_ascii=False)`` — that ONE keyword
combination, and (since rc403, `#T1071`) including FLOATS, which now ride an
integer-only Ryu converter instead of ``snprintf("%.17g")``.

The census in this docstring was WRONG until rc403 and is restated here from an
AST walk of ``srmech/`` rather than a line grep (the old numbers came from
single-line ``grep``, which misses every multi-line call). Measured: **64**
``json.dumps`` / ``json.dump`` call sites, using ``ensure_ascii`` (**23**),
``sort_keys`` (**21**), ``separators=`` (**10**), ``indent=`` (**9**) and
``default=`` (**8**). Every figure was under-counted before; ``separators`` and
``indent`` by roughly half.

The old note also mis-diagnosed the blocker. It called ``default=`` "a PYTHON
CALLABLE the C writer cannot honour without an ABI change" — but **7 of the 8
``default=`` sites pass the builtin ``str``**, not a bespoke callable
(``cli/bus.py`` x4, ``mcp/_server.py``, ``mcp/_sse.py``, ``mcp/_stdio.py``);
only ``mcp/_tools.py`` passes a project function (``_json_fallback``). A
"stringify whatever is left" default needs no callback across the ABI at all.
The real obstacles are the ones that were never listed: ``indent=`` (9 sites)
is a whole second output grammar the C writer does not implement, and
``separators=`` (10 sites) means the compact form and the default-spaced form
are BOTH live in this tree while the C writer hard-codes one of them.

Two further domain limits, both exact, both discovered while measuring:

* **Non-string dict keys.** ``sort_keys=True`` sorts the original key OBJECTS
  and coerces afterwards, so ``{1:'a', 2:'b', 10:'c'}`` emits ``"1","2","10"``;
  the C writer's tree holds keys already as strings and sorts them bytewise,
  which for those same keys gives ``"1","10","2"``. Any C-backed ``dumps``
  must coerce and sort non-string keys on the PYTHON side first.
* **Non-finite floats.** ``json.dumps`` emits ``NaN`` / ``Infinity`` /
  ``-Infinity`` by default; ``srmech_json_write_ws`` DECLINES them (rc403),
  because it is paired with the strict-RFC-8259 ``srmech_json_parse`` and must
  not write a document its own parser refuses. A C-backed ``dumps`` would have
  to route those to the stdlib.

So the write half remains deliberately un-self-hosted. What rc403 changed is
that FLOAT PARITY is no longer one of the reasons.

This is an INTERNAL module. It registers no ToolEntry, adds nothing to
``describe()`` / introspect / MCP, and is not one of the 14 A-N compute
capabilities — it is plumbing srmech calls on itself.
"""

from __future__ import annotations

import json as _stdlib_json
from typing import Any

#: The exception :func:`loads` raises on a malformed document (rc407, `#T1076`).
#:
#: A front door owns its EXCEPTION CONTRACT, not just its happy path. Until
#: rc407 this module re-exported ``load``/``loads`` but no error type, so a
#: caller could not write ``except`` around it without importing the very
#: module the ban exists to remove — and four package files did exactly that,
#: importing stdlib ``json`` solely to name this class. ``_json.loads('{bad')``
#: raises a genuine ``json.JSONDecodeError`` on both the native and the stdlib
#: path (the native parser DECLINES and control rides the stdlib parse), so
#: this alias is the true type, not a look-alike.
#:
#: This is a deliberate DEPARTURE from the tomllib precedent, which kept such
#: aliases as named necessities. The justification is the front-door contract
#: itself: a caller cannot catch what ``loads`` raises without the banned
#: import. It is the correct thing rather than a shim around the break.
JSONDecodeError = _stdlib_json.JSONDecodeError

#: Contract A's reader, resolved ONCE and cached (rc479, `#T1188`).
#:
#: ``srmech.math.q`` imports ``srmech._native`` and the two Class-N modules
#: beneath it, so this module cannot import it at module scope without making
#: the JSON front door drag the whole math stack in at ``import srmech``. The
#: hook is resolved on first parse and held here afterwards — a module global,
#: not a per-literal import, because ``parse_float`` is called once per numeric
#: literal and a document can carry thousands.
_PARSE_FLOAT = None


def _exact_parse_float():
    """The ``parse_float=`` callable the stdlib floor is given."""
    global _PARSE_FLOAT
    if _PARSE_FLOAT is None:
        from .math.q import parse_float_exact
        _PARSE_FLOAT = parse_float_exact
    return _PARSE_FLOAT


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
    return _stdlib_json.loads(text, parse_float=_exact_parse_float())


def load(fp) -> Any:
    """Parse a JSON document from a file object (mirrors ``json.load``).

    Accepts a handle opened in binary (``'rb'``) or text mode; the bytes are
    decoded as UTF-8 before parsing, so both work.
    """
    data = fp.read()
    if isinstance(data, (bytes, bytearray)):
        data = bytes(data).decode("utf-8")
    return loads(data)
