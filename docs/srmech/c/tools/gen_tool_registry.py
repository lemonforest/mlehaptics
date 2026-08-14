#!/usr/bin/env python3
"""Code-generator for ``c/src/srmech_tool_registry.c`` (0.9.0rc184).

The C MCP-server FOUNDATION GATE: emit the
``srmech.introspect.tool_schema`` registry as a ``const`` C data table so a
bare-C host (no Python) can produce the tool registry DATA and the
canonical ``tool_schema_sha256`` attestation with no interpreter.

*(rc409, `#T1080`: this line said "the ~403-entry ... registry" against a
measured 556 — the same unattributed-cardinal rot the adapter docstring
carried. The count is deliberately NOT restated here: ``:265`` already emits
``Entries: {len(tools)}`` from the live value, so the number has an
authoritative home and does not need a second hand-maintained copy.)*

Determinism / order
-------------------
Walks ``get_tool_schema().tools`` — the SAME order the Python canonical
payload (``schema.to_jsonable()["tools"]``) uses. The generated table row
order is therefore identical to the order the byte-identity hash-ratchet
compares against.

**srmech tools ONLY.** This previously read "srmech tools in registration
order, then profile tools by owner", which described the ordering of
``get_tool_schema()`` in general and so read as SANCTIONING profile rows in
the emitted table. It never was: the table is compiled into the shipped
library, where a bare-C host cannot distinguish a profile's row from
srmech's own. ``_reject_profile_tools`` now enforces what the read side
(``tool_schema_view`` and its three peers) has always assumed.

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

Regenerate (rc346, `#T975` — DO NOT run this script by hand)::

    python3 tools/regen_all.py          # from docs/srmech/python

This generator EMBEDS the prose in ``srmech/introspect/_tool_docs.py``, which
``gen_tool_docs.py`` writes, so running it first leaves the table stale
against the very docs it contains — measured at 14 bytes propagating
827380 -> 827394. It also wrote to STDOUT, so a bare invocation with no
redirect changed nothing while exiting 0. ``regen_all.py`` derives the
order from ``codegen_manifest.py`` and owns the write; a direct run now
refuses unless ``--standalone`` is passed.

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


def _reject_profile_tools(tools: "list") -> None:
    """Refuse to emit a table containing PROFILE-owned rows (rc409, `#T1080`).

    This generator walks the LIVE, MUTABLE `srmech.introspect.tool_schema`
    registry. If any profile is active in the generating interpreter, its tools
    land in `get_tool_schema().tools` and are emitted verbatim into a `const` C
    table that then ships COMPILED INTO the library — where a bare-C host reads
    them as srmech's own, with no way to tell the difference and no way to
    remove them.

    THE READ SIDE ALREADY ENFORCES THIS; THE WRITE SIDE ENFORCED IT NOWHERE.
    `tool_schema.tool_schema_view` and three peers refuse the C table the
    moment a profile tool is present, precisely because the table is only
    valid as a picture of the pure srmech registry. rc409 closes the write
    half of that existing contract — it does not invent a new one.

    Raises `ToolSchemaValidationError` rather than asserting: `assert`
    vanishes under `python -O`, and a codegen guard must not be optimizable
    away. Every offender is collected before raising, so one run names them
    all instead of failing on the first.
    """
    from srmech.introspect.tool_schema import (
        RESERVED_OWNERS, ToolSchemaValidationError,
    )
    intruders = [t for t in tools if t.owner not in RESERVED_OWNERS]
    if intruders:
        raise ToolSchemaValidationError(
            f"refusing to generate the C tool registry: "
            f"{len(intruders)} of {len(tools)} entries are PROFILE-owned and "
            f"would be compiled into the shipped library as srmech's own.\n"
            + "\n".join(f"    {t.name!r} owner={t.owner!r}"
                        for t in intruders[:10])
            + ("\n    ..." if len(intruders) > 10 else "")
            + "\n\nRegenerate from a clean interpreter with no profile "
              "activated. The C table is only meaningful as the PURE srmech "
              "registry — that is the invariant tool_schema_view() and its "
              "three peers already check on the READ side."
        )


def generate() -> str:
    # Import srmech from the sibling python/ tree (dev-time generation).
    here = Path(__file__).resolve()
    python_dir = here.parent.parent.parent / "python"
    sys.path.insert(0, str(python_dir))
    import srmech  # noqa: F401  (import side effects: warmup)
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    schema = get_tool_schema()
    tools = list(schema.tools)
    _reject_profile_tools(tools)

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

    # Per-entry composes / preserves string arrays (rc305 #T943; only for
    # composite ops — a leaf op emits NULL + 0 in the table row below).
    b("/* Per-entry composes / preserves / reads_input / frame_axis string")
    b(" * arrays (rc305 #T943; reads_input rc347 #T985; frame_axis rc430")
    b(" * #T1127). */")
    for idx, t in enumerate(tools):
        for field_name in ("composes", "preserves", "reads_input", "frame_axis"):
            seq = getattr(t, field_name, ()) or ()
            if not seq:
                continue
            b(f"static const char *const ts_{field_name}_{idx}[] = {{")
            for s in seq:
                b(f"    {hoist.expr(s)},")
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
        b(f"        {hoist.opt_expr(t.explanation)},")
        # rc305 (#T943): composes / preserves arrays + counts (NULL + 0 for a
        # leaf op; the ts_{field}_{idx} arrays are emitted above for composites).
        composes = getattr(t, "composes", ()) or ()
        preserves = getattr(t, "preserves", ()) or ()
        b("        %s, %du," % (
            f"ts_composes_{idx}" if composes else "NULL", len(composes)))
        b("        %s, %du," % (
            f"ts_preserves_{idx}" if preserves else "NULL", len(preserves)))
        # rc347 (#T985): the lane axis. reads_lane NULL + reads_input NULL/0
        # for the (majority) undeclared case; both together otherwise.
        reads_input = getattr(t, "reads_input", ()) or ()
        b(f"        {hoist.opt_expr(getattr(t, 'reads_lane', None))},")
        b("        %s, %du," % (
            f"ts_reads_input_{idx}" if reads_input else "NULL",
            len(reads_input)))
        # rc430 (#T1127): the frame axis. frame_scope NULL + frame_axis NULL/0
        # for the (majority) undeclared case; both together otherwise.
        frame_axis = getattr(t, "frame_axis", ()) or ()
        b(f"        {hoist.opt_expr(getattr(t, 'frame_scope', None))},")
        b("        %s, %du," % (
            f"ts_frame_axis_{idx}" if frame_axis else "NULL",
            len(frame_axis)))
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
    w(" *   python3 tools/regen_all.py            (from docs/srmech/python)")
    w(" *")
    w(" * rc347: this line named the raw generator plus a `>` redirect, which was")
    w(" * exactly trap 2 the runner removed - forget the redirect and the table")
    w(" * goes to the terminal, nothing changes, exit 0. The runner also fixes the")
    w(" * ORDER this file depends on. rc346 left it stale on purpose to keep its")
    w(" * own zero-delta signal clean; rc347 already moves these bytes.")
    w(" *")
    w(" * Source of truth: srmech.introspect.tool_schema (warmup_all() registry).")
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
    w("/* MSVC C4125 (\"decimal digit terminates octal escape sequence\") is a")
    w(" * STYLE nag: the baked non-ASCII bytes are emitted as 3-digit octal")
    w(" * escapes (\\NNN) which the C standard caps at 3 digits, so a following")
    w(" * decimal digit is unambiguous (gcc/clang stay silent). It fires only")
    w(" * under MSVC /WX on this generated pure-DATA table. Suppress it locally")
    w(" * (the compiled bytes are identical → the tool_schema_sha256 ratchet is")
    w(" * unaffected). */")
    w("#ifdef _MSC_VER")
    w("#pragma warning(disable : 4125)")
    w("#endif")
    w("")
    w("/* tool_schema_version (srmech.introspect.tool_schema.TOOL_SCHEMA_VERSION). */")
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
    sys.path.insert(
        0, str(Path(__file__).resolve().parents[2] / "python" / "tools"))
    from codegen_manifest import require_regen_all

    require_regen_all("gen_tool_registry")
    sys.stdout.write(generate())
