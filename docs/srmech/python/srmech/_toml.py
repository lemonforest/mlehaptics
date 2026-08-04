"""srmech's own internal TOML loader — the front door srmech's Python and
codegen use to read descriptor / catalog TOML.

Its PURPOSE is to drop the external ``tomli`` / ``tomllib`` dependency wherever
srmech's C parser is present. When the native library exposes
``srmech_toml_parse``, :func:`loads` walks the C parse tree straight to a Python
dict (Route A, #T907) — the same self-hosting move ``sha256_bytes`` makes for
hashing, but for TOML. On a pure / Pyodide wheel (no native library), or when the
C parser DECLINES a document (a construct outside its supported subset —
datetimes, quoted keys, non-decimal ints, arbitrary-precision ints, or a FLOAT,
whose libm-free C parse is not guaranteed bit-exact with the stdlib so
float-bearing documents ride the stdlib parser for fidelity), it falls back to
the stdlib ``tomllib`` (Python 3.11+) or the ``tomli`` backport (3.10).

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


def _stdlib_loads(text: str) -> Dict[str, Any]:
    """Parse via the stdlib tomllib (3.11+) / tomli backport (3.10)."""
    if sys.version_info >= (3, 11):
        import tomllib as _toml
    else:  # pragma: no cover
        import tomli as _toml  # type: ignore[no-redef]
    return _toml.loads(text)


def loads(text: str) -> Dict[str, Any]:
    """Parse a TOML string to a dict — native ``srmech_toml`` first, tomllib floor.

    The native path is taken only when the C library is loaded AND exposes
    ``srmech_toml_parse``; if it then DECLINES the document (returns ``None`` on
    an unsupported construct or syntax error), control rides the stdlib parse so
    the value — and any genuine ``TOMLDecodeError`` — is identical to the pure
    path.
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
