#!/usr/bin/env python3
"""Code-generator for ``c/src/srmech_tool_registry.c`` (0.9.0rc184).

The C MCP-server FOUNDATION GATE: emit the ~403-entry
``srmech.amsc.tool_schema`` registry as a ``const`` C data table so a
bare-C host (no Python) can produce the tool registry DATA and the
canonical ``tool_schema_sha256`` attestation with no interpreter.

Determinism / order
-------------------
Walks ``get_tool_schema().tools`` — the SAME order the Python canonical
payload (``schema.to_jsonable()["tools"]``) uses (srmech tools in
registration order, then profile tools by owner). The generated table
row order is therefore identical to the order the byte-identity
hash-ratchet compares against.

Byte-identity strategy
----------------------
The C serialiser (``srmech_tool_schema.c``) rebuilds the canonical JSON
field-by-field (sorted keys, compact separators, ensure_ascii=True
escaping). The two documentation-hint fields ``example`` /
``smoke_test_hint`` carry an ARBITRARY-schema payload, so this generator
bakes each as its ALREADY-canonical compact JSON fragment
(``json.dumps(value, sort_keys=True, separators=(",", ":"))`` — which is
ensure_ascii=True, hence pure ASCII) for the serialiser to splice raw.

Every other (structured) string is baked as its decoded UTF-8 bytes via
an ASCII-only C string literal (non-ASCII bytes as ``\\NNN`` 3-digit
octal — MSVC-safe, no source-encoding dependency), so the runtime string
holds the genuine value the accessors return.

Regenerate::

    python3 c/tools/gen_tool_registry.py > c/src/srmech_tool_registry.c

An idempotence test (re-run → no diff) guards drift.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Split a baked C string literal into adjacent chunks no larger than this
# many source characters (defence-in-depth vs the MSVC ~16380-byte single
# string-literal limit; C concatenates adjacent literals). Chosen well
# below the limit and split only on whole escape-token boundaries.
_CHUNK = 4000


def _escape_tokens(s: str) -> list[str]:
    """The per-byte C-string-literal escape tokens for the UTF-8 bytes of
    ``s`` (so a chunk boundary can never split a multi-char escape)."""
    tokens: list[str] = []
    for b in s.encode("utf-8"):
        if b == 0x22:      # "
            tokens.append('\\"')
        elif b == 0x5C:    # backslash
            tokens.append("\\\\")
        elif b == 0x0A:
            tokens.append("\\n")
        elif b == 0x09:
            tokens.append("\\t")
        elif b == 0x0D:
            tokens.append("\\r")
        elif 0x20 <= b <= 0x7E:
            tokens.append(chr(b))
        else:
            # 3-digit octal is unambiguous (C stops an octal escape at 3
            # digits) and covers every byte 0x80..0xFF.
            tokens.append("\\%03o" % b)
    return tokens


def c_string_literal(s: str) -> str:
    """A C expression evaluating to the UTF-8 bytes of ``s``: one or more
    adjacent double-quoted literals. ASCII-only source (MSVC-safe)."""
    tokens = _escape_tokens(s)
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for tok in tokens:
        if cur_len + len(tok) > _CHUNK and cur:
            chunks.append('"' + "".join(cur) + '"')
            cur = []
            cur_len = 0
        cur.append(tok)
        cur_len += len(tok)
    chunks.append('"' + "".join(cur) + '"')
    return " ".join(chunks)


# A single string literal (even after adjacent-literal concatenation) may
# not exceed the C99 "minimum maximum" of 4095 bytes without tripping
# ``-Woverlength-strings`` under ``-Wpedantic -Werror``. Strings longer
# than this are hoisted into a ``static const unsigned char[]`` brace-
# initialiser array (a char array is NOT a string constant, so the limit
# does not apply) and referenced by a ``(const char *)`` cast.
_OVERLENGTH = 4000


class _Hoist:
    """Collects hoisted long-string array definitions during generation."""

    def __init__(self) -> None:
        self.defs: list[str] = []
        self._n = 0

    def expr(self, s: str) -> str:
        """A C ``const char *`` expression for ``s`` — an inline literal
        when short, else a cast to a hoisted char array."""
        data = s.encode("utf-8")
        if len(data) <= _OVERLENGTH:
            return c_string_literal(s)
        ident = f"ts_lstr_{self._n}"
        self._n += 1
        body = list(data) + [0]
        rows: list[str] = []
        for off in range(0, len(body), 20):
            rows.append("    " + ", ".join(str(b) for b in body[off:off + 20])
                        + ",")
        self.defs.append(
            f"static const unsigned char {ident}[] = {{\n"
            + "\n".join(rows)
            + "\n};"
        )
        return f"(const char *){ident}"

    def opt_expr(self, s: "str | None") -> str:
        return "NULL" if s is None else self.expr(s)


def _fragment(value: "dict | None") -> "str | None":
    """The already-canonical compact JSON fragment for an
    ``example`` / ``smoke_test_hint`` payload (ensure_ascii=True →
    pure ASCII), or None."""
    if value is None:
        return None
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def generate() -> str:
    # Import srmech from the sibling python/ tree (dev-time generation).
    here = Path(__file__).resolve()
    python_dir = here.parent.parent.parent / "python"
    sys.path.insert(0, str(python_dir))
    import srmech  # noqa: F401  (import side effects: warmup)
    from srmech.amsc.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    schema = get_tool_schema()
    tools = list(schema.tools)

    hoist = _Hoist()
    body: list[str] = []
    b = body.append

    # Per-entry parameter arrays (only for entries with >= 1 param).
    b("/* Per-entry parameter arrays. */")
    for idx, t in enumerate(tools):
        if not t.parameters:
            continue
        b(f"static const srmech_tool_param_t ts_params_{idx}[] = {{")
        for p in t.parameters:
            b("    { %s, %s, %d, %s }," % (
                hoist.expr(p.name),
                hoist.expr(p.type),
                1 if p.required else 0,
                hoist.expr(p.summary),
            ))
        b("};")
    b("")

    # The entry table.
    b("/* The tool registry, in get_tool_schema().tools order (== the order")
    b(" * the byte-identity hash-ratchet compares against). */")
    b("const srmech_tool_entry_t srmech_tool_registry_table[] = {")
    for idx, t in enumerate(tools):
        params_ref = f"ts_params_{idx}" if t.parameters else "NULL"
        ret_type = t.returns.type if t.returns is not None else None
        ret_shape = t.returns.shape if t.returns is not None else None
        b(f"    {{ /* {idx} */")
        b(f"        {hoist.expr(t.name)},")
        b(f"        {hoist.expr(t.owner)},")
        b(f"        {hoist.expr(t.category)},")
        b(f"        {hoist.expr(t.summary)},")
        b(f"        {params_ref}, {len(t.parameters)}u,")
        b(f"        {hoist.opt_expr(ret_type)},")
        # returns_shape: emit "" when returns present with empty shape,
        # NULL only when there is no `returns` at all.
        if ret_type is None:
            b("        NULL,")
        else:
            b(f"        {hoist.expr(ret_shape or '')},")
        b(f"        {1 if t.mcp_callable else 0},")
        b(f"        {hoist.opt_expr(t.mcp_unavailable_reason)},")
        b(f"        {hoist.opt_expr(_fragment(t.example))},")
        b(f"        {hoist.opt_expr(_fragment(t.smoke_test_hint))},")
        b("    },")
    b("};")
    b("")
    b("const size_t srmech_tool_registry_len =")
    b("    sizeof(srmech_tool_registry_table) "
      "/ sizeof(srmech_tool_registry_table[0]);")
    b("")

    out: list[str] = []
    w = out.append
    w("/* srmech_tool_registry.c — GENERATED by c/tools/gen_tool_registry.py.")
    w(" * DO NOT EDIT BY HAND. Regenerate with:")
    w(" *   python3 c/tools/gen_tool_registry.py > c/src/srmech_tool_registry.c")
    w(" *")
    w(" * Source of truth: srmech.amsc.tool_schema (warmup_all() registry).")
    w(" * The 0.9.0rc184 C MCP-server FOUNDATION GATE — the tool registry as a")
    w(" * const data table (JPL-clean: const arrays, no dynamic init, no malloc).")
    w(" * The accessors + the canonical serialiser live in srmech_tool_schema.c.")
    w(" *")
    w(f" * Entries: {len(tools)}. tool_schema_version: "
      f"{schema.tool_schema_version}.")
    w(" */")
    w("")
    w('#include "srmech.h"')
    w("")
    w("/* tool_schema_version (srmech.amsc.tool_schema.TOOL_SCHEMA_VERSION). */")
    w("const char srmech_tool_schema_version_str[] = "
      f"{c_string_literal(schema.tool_schema_version)};")
    w("")
    if hoist.defs:
        w("/* Hoisted long strings (> %d bytes) — char arrays, not string"
          % _OVERLENGTH)
        w(" * literals, so -Woverlength-strings does not apply. */")
        for d in hoist.defs:
            w(d)
        w("")
    out.extend(body)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.write(generate())
