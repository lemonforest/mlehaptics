#!/usr/bin/env python3
"""Code-generator for ``c/src/srmech_carrier_registry.c`` (0.9.0rc205).

The CARRIER (operand) introspection registry — gh #1293: emit the
``srmech.amsc.carrier_schema`` per-carrier metadata (name / description /
ladder / rung / variables / the rc339 CAPABILITY block / the DERIVED ops
back-index) as a ``const`` C data
table so a bare-C host (no Python) produces the carrier registry DATA and the
canonical carrier-schema JSON with no interpreter — the operand-side peer of
the rc184 ``gen_tool_registry.py`` tool table (and the rc202
``gen_class_registry.py`` descriptor table).

Determinism / order
-------------------
Entries are emitted sorted by carrier NAME in byte order — the SAME order
CPython's ``json.dumps(..., sort_keys=True)`` walks the top-level keys, so the
C assembler (``srmech_carrier_schema`` in ``srmech_carrier_schema.c``)
produces the canonical whole-schema JSON by plain concatenation in table
order, BYTE-IDENTICAL to::

    json.dumps(_pure_carrier_schema(), sort_keys=True, separators=(",", ":"))

That byte-identity IS the hash-ratchet contract (sha256(C) == sha256(pure) in
``tests/test_carrier_schema_rc205.py``): if a carrier is added / a description
edited / a new op joins a back-index Python-side without regenerating this
table, the ratchet fails.

Byte-identity strategy
----------------------
Each per-carrier ENTRY payload is baked as its ALREADY-canonical compact JSON
fragment (``json.dumps(entry, sort_keys=True, separators=(",", ":"))`` —
ensure_ascii=True, hence pure ASCII). ``name`` / ``description`` / ``ladder``
/ ``rung`` additionally ride as first-class struct fields (decoded UTF-8, via
ASCII-only ``\\NNN`` octal escapes — MSVC-safe) so a bare-C consumer reads
them without a JSON parse.

Regenerate (rc346, `#T975` — DO NOT run this script by hand)::

    python3 tools/regen_all.py          # from docs/srmech/python

**This table bakes the SORTED TOOL-NAME LIST** (the per-carrier ``ops``
back-index over ``get_tool_schema().tools``), so it goes stale whenever the
tool surface changes — *whether or not any carrier moved*. rc345 asked the
semantic question ("did a carrier move?"), answered it correctly, skipped
this generator and shipped red. The rule is MECHANICAL: ``tools.total``
changed => this regenerates. Measured — adding one public callable moved
this file 180889 -> 181113 bytes. ``regen_all.py`` derives that from the
declared ``consumes=(carrier_schema,)`` edge, so it can no longer be
reasoned away; a direct run refuses unless ``--standalone`` is passed.

An idempotence test (re-run -> no diff) guards drift.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Split baked C string literals into adjacent chunks (MSVC single-literal
# limit defence; C concatenates adjacent literals). Same policy as
# gen_tool_registry.py.
_CHUNK = 4000

# A single (concatenated) string constant may not exceed the C99 minimum
# maximum of 4095 bytes without -Woverlength-strings under -Wpedantic
# -Werror; longer strings are hoisted to unsigned-char arrays.
_OVERLENGTH = 4000


def _escape_tokens(s: str) -> "list[str]":
    """Per-byte C-string-literal escape tokens for the UTF-8 bytes of ``s``
    (a chunk boundary can never split a multi-char escape)."""
    tokens: "list[str]" = []
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
            # 3-digit octal is unambiguous (C caps octal escapes at 3 digits).
            tokens.append("\\%03o" % b)
    return tokens


def c_string_literal(s: str) -> str:
    """A C expression evaluating to the UTF-8 bytes of ``s``: one or more
    adjacent double-quoted literals. ASCII-only source (MSVC-safe)."""
    tokens = _escape_tokens(s)
    chunks: "list[str]" = []
    cur: "list[str]" = []
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


class _Hoist:
    """Collects hoisted long-string array definitions during generation
    (the gen_tool_registry.py -Woverlength-strings defence)."""

    def __init__(self) -> None:
        self.defs: "list[str]" = []
        self._n = 0

    def expr(self, s: str) -> str:
        data = s.encode("utf-8")
        if len(data) <= _OVERLENGTH:
            return c_string_literal(s)
        ident = f"cs_lstr_{self._n}"
        self._n += 1
        body = list(data) + [0]
        rows: "list[str]" = []
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


def generate() -> str:
    # Import srmech from the sibling python/ tree (dev-time generation).
    here = Path(__file__).resolve()
    python_dir = here.parent.parent.parent / "python"
    sys.path.insert(0, str(python_dir))
    from srmech.amsc.carrier_schema import _pure_carrier_schema

    schema = _pure_carrier_schema()
    # Byte-order name sort == CPython json.dumps(sort_keys=True) top-level
    # key order (the names are ASCII), so the C assembler concatenates in
    # table order and reproduces the canonical whole-schema JSON exactly.
    names = sorted(schema, key=lambda n: n.encode("utf-8"))

    hoist = _Hoist()
    rows: "list[str]" = []
    for name in names:
        entry = schema[name]
        fragment = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        rung = entry["rung"] if entry["rung"] is not None else 0
        rows.append("    {")
        rows.append(f"        {hoist.expr(name)},")
        rows.append(f"        {hoist.expr(entry['description'])},")
        rows.append(f"        {hoist.opt_expr(entry['ladder'])},")
        rows.append(f"        {rung},")
        rows.append(f"        {hoist.expr(fragment)},")
        rows.append(f"        {len(fragment.encode('utf-8'))}u,")
        rows.append("    },")

    out: "list[str]" = []
    w = out.append
    w("/* srmech_carrier_registry.c - GENERATED by "
      "c/tools/gen_carrier_registry.py.")
    w(" * DO NOT EDIT BY HAND. Regenerate with:")
    w(" *   python3 tools/regen_all.py            (from docs/srmech/python)")
    w(" *")
    w(" * rc347: this line named the raw generator plus a `>` redirect, which was")
    w(" * exactly trap 2 the runner removed - forget the redirect and the table")
    w(" * goes to the terminal, nothing changes, exit 0. The runner also fixes the")
    w(" * ORDER this file depends on. rc346 left it stale on purpose to keep its")
    w(" * own zero-delta signal clean; rc347 already moves these bytes.")
    w(" *")
    w(" * Source of truth: srmech.amsc.carrier_schema._pure_carrier_schema()")
    w(" * (the authored per-carrier metadata + the DERIVED ops back-index).")
    w(" * The 0.9.0rc205 CARRIER (operand) introspection registry (gh #1293)")
    w(" * as a const data table (JPL-clean: const arrays, no dynamic init,")
    w(" * no malloc). The accessors + the canonical JSON assembler live in")
    w(" * srmech_carrier_schema.c. Entries are in byte-sorted name order ==")
    w(" * the json.dumps(sort_keys=True) key order the hash-ratchet compares")
    w(" * against; each entry_json fragment is baked pre-canonical (compact,")
    w(" * sorted keys, ensure_ascii -> pure ASCII).")
    w(" *")
    w(f" * Carriers: {len(names)} ({', '.join(names)}).")
    w(" */")
    w("")
    w('#include "srmech.h"')
    w("")
    w("/* MSVC C4125 (\"decimal digit terminates octal escape sequence\") is a")
    w(" * STYLE nag on the baked \\NNN octal escapes (the C standard caps an")
    w(" * octal escape at 3 digits, so a following decimal digit is")
    w(" * unambiguous; gcc/clang stay silent). Generated pure-DATA table ->")
    w(" * suppress locally (compiled bytes identical; the hash-ratchet is")
    w(" * unaffected). */")
    w("#ifdef _MSC_VER")
    w("#pragma warning(disable : 4125)")
    w("#endif")
    w("")
    if hoist.defs:
        w("/* Hoisted long strings (> %d bytes) - char arrays, not string"
          % _OVERLENGTH)
        w(" * literals, so -Woverlength-strings does not apply. */")
        for d in hoist.defs:
            w(d)
        w("")
    w("/* The carrier registry, in byte-sorted name order (== the canonical")
    w(" * JSON key order the hash-ratchet compares against). */")
    w("const srmech_carrier_entry_t srmech_carrier_registry_table[] = {")
    out.extend(rows)
    w("};")
    w("")
    w("const size_t srmech_carrier_registry_len =")
    w("    sizeof(srmech_carrier_registry_table) "
      "/ sizeof(srmech_carrier_registry_table[0]);")
    w("")
    return "\n".join(out)


if __name__ == "__main__":
    sys.path.insert(
        0, str(Path(__file__).resolve().parents[2] / "python" / "tools"))
    from codegen_manifest import require_regen_all

    require_regen_all("gen_carrier_registry")
    sys.stdout.write(generate())
