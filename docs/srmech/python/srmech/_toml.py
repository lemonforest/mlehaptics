"""srmech's own internal TOML loader — the front door srmech's Python and
codegen use to read descriptor / catalog TOML.

Its PURPOSE is to drop the external ``tomli`` / ``tomllib`` dependency wherever
srmech's C parser is present. When the native library exposes
``srmech_toml_parse``, :func:`loads` walks the C parse tree straight to a Python
dict (Route A, #T907) — the same self-hosting move ``sha256_bytes`` makes for
hashing, but for TOML. Floats self-host too: as of rc397 (`#T1066`) the C
decimal→double parse is correctly-rounded (Clinger fast path + a srmech_bigint
exact tail), so a float value is bit-identical to the stdlib's. On a pure /
Pyodide wheel (no native library), or when the C parser DECLINES a document (a
construct outside its supported subset — datetimes, quoted keys, non-decimal
ints, or an int that overflows int64), it falls back to the stdlib ``tomllib``
(Python 3.11+) or the ``tomli`` backport (3.10).

That fallback is MANDATORY and is never removed: the C library is absent on pure
/ Pyodide installs, so ``tomllib`` / ``tomli`` remains the correctness path
there. Native-first is throughput + zero-external-dep; stdlib is the floor.

This is an INTERNAL module. It registers no ToolEntry, adds nothing to
``describe()`` / introspect / MCP, and is not one of the 14 A-N compute
capabilities — it is plumbing srmech calls on itself.
"""

from __future__ import annotations

import sys
from typing import Any, Dict


def _stdlib_backend():
    """The stdlib tomllib (3.11+) / tomli backport (3.10) module."""
    if sys.version_info >= (3, 11):
        import tomllib as _backend
    else:  # pragma: no cover
        import tomli as _backend  # type: ignore[no-redef]
    return _backend


#: Contract A's reader, resolved ONCE and cached (rc479, `#T1188`).
#:
#: ``srmech.math.q`` imports ``srmech._native`` and the Class-N modules beneath
#: it, so resolving the hook at module scope would make the TOML front door
#: drag the whole math stack in at ``import srmech``. ``parse_float`` is called
#: once per float literal and a descriptor can carry hundreds, so it is held in
#: a module global rather than re-imported per literal.
_PARSE_FLOAT = None


def _exact_parse_float():
    """The ``parse_float=`` callable the stdlib floor is given."""
    global _PARSE_FLOAT
    if _PARSE_FLOAT is None:
        from .math.q import parse_float_exact
        _PARSE_FLOAT = parse_float_exact
    return _PARSE_FLOAT


def _stdlib_loads(text: str) -> Dict[str, Any]:
    """Parse via the stdlib tomllib (3.11+) / tomli backport (3.10).

    **Contract A, rc479 (`#T1188`).** A TOML float literal is read as the
    exact rational it already names — ``dead_band = 1e-12`` loads as
    ``Q(1, 1000000000000)`` — via
    :func:`srmech.math.q.parse_float_exact` installed as ``parse_float=``.
    Unlike JSON, tomllib hands ``nan`` / ``inf`` / ``-inf`` to ``parse_float``
    like any other token, and it hands the RAW token including underscores
    (``1_000.000_1``); the reader carries both, returning the float for the
    non-finite three (rule Z1) and stripping lexer-validated underscores.
    """
    return _stdlib_backend().loads(text, parse_float=_exact_parse_float())


#: The exception :func:`loads` raises on a malformed document (rc407, `#T1076`).
#:
#: The peer of :data:`srmech._json.JSONDecodeError`, and bound from whichever
#: backend the version branch above selected, so it is the SAME class the
#: parse actually raises on 3.10 and on 3.11+ alike — not a look-alike and not
#: a version-specific guess. Without it a caller had to re-run the
#: tomllib/tomli branch itself just to name the type, which is precisely what
#: ``srmech/amsc/descriptor.py`` and ``srmech/profile_loader.py`` were doing.
TOMLDecodeError = _stdlib_backend().TOMLDecodeError


def loads(text: str) -> Dict[str, Any]:
    """Parse a TOML string to a dict — native ``srmech_toml`` first, tomllib floor.

    The native path is taken only when the C library is loaded AND exposes
    ``srmech_toml_parse``; if it then DECLINES the document (returns ``None`` on
    an unsupported construct or syntax error), control rides the stdlib parse so
    the value — and any genuine ``TOMLDecodeError`` — is identical to the pure
    path.

    ⚠️ **rc479 (`#T1188`) added a decline category, and it is what keeps the
    projections equal.** Under contract A a decimal literal reads as an exact
    ``Q``; ``srmech_toml.c`` yields a C ``double`` and no C value layer in this
    library can hold a rational, so the native path now declines ANY document
    carrying a float literal and the floor answers exactly. A native cell and a
    pure cell return the same object for the same descriptor — which silently
    returning doubles from C would not. It costs one wasted C parse on such a
    document and never costs correctness.
    """
    from . import _native

    if (
        _native.HAS_NATIVE
        and getattr(_native, "LIB", None) is not None
        and hasattr(_native.LIB, "srmech_toml_parse")
    ):
        data = _native.toml_loads_c(text)
        if data is not None:
            return data
    return _stdlib_loads(text)


def load(fp) -> Dict[str, Any]:
    """Parse a TOML document from a file object (mirrors ``tomllib.load``).

    Accepts a handle opened in binary (``'rb'``) or text mode; the bytes are
    decoded as UTF-8 before parsing, so both work.
    """
    data = fp.read()
    if isinstance(data, (bytes, bytearray)):
        data = bytes(data).decode("utf-8")
    return loads(data)
