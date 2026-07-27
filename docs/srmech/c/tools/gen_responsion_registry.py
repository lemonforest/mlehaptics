#!/usr/bin/env python3
"""Code-generator for ``c/src/srmech_responsion_registry.c`` (0.9.0rc225).

The RESPONSION (stored-relationship) introspection registry — the k=3
completion of the introspection triad (user design 2026-07-12): emit the
``srmech.amsc.responsion_schema`` per-EDGE data (the ``(operator, carrier)``
edge key + the responsions riding it — kind / regime / answers_with /
verified-or-OPEN status) as a ``const`` C data table so a bare-C host (no
Python) produces the responsion registry DATA and the canonical
responsion-schema JSON with no interpreter — the relationship-side peer of
the rc184 ``gen_tool_registry.py`` tool table and the rc205
``gen_carrier_registry.py`` carrier table.

Determinism / order
-------------------
Entries are emitted sorted by EDGE KEY in byte order — the SAME order
CPython's ``json.dumps(..., sort_keys=True)`` walks the top-level keys, so
the C assembler (``srmech_responsion_schema`` in
``srmech_responsion_schema.c``) produces the canonical whole-schema JSON by
plain concatenation in table order, BYTE-IDENTICAL to::

    json.dumps(_pure_responsion_schema(), sort_keys=True,
               separators=(",", ":"))

That byte-identity IS the hash-ratchet contract (sha256(C) == sha256(pure)
in ``tests/test_responsion_schema_rc225.py``): if an edge is added / an
``answers_with`` edited / a dispatch ``_OPEN_HINTS`` residue reworded
Python-side without regenerating this table, the ratchet fails.

Byte-identity strategy
----------------------
Each per-edge ENTRY payload (a JSON ARRAY of responsion objects) is baked as
its ALREADY-canonical compact JSON fragment (``json.dumps(entry,
sort_keys=True, separators=(",", ":"))`` — ensure_ascii=True, hence pure
ASCII). The edge ``key`` / ``operator`` / ``carrier`` additionally ride as
first-class struct fields (all pure-ASCII dotted identifiers, asserted) so a
bare-C consumer reads the edge refs without a JSON parse.

Regenerate (rc346, `#T975` — DO NOT run this script by hand)::

    python3 tools/regen_all.py          # from docs/srmech/python

This table's dependency on the tool surface is a VALIDATION edge, not a
byte one: ``_validate_refs`` requires every responsion ``operator`` to be a
live ``tool_schema`` key, so ADDING an op does not move these bytes but
RENAMING or REMOVING one makes ``_pure_responsion_schema()`` raise outright
(measured at rc346). It therefore belongs in the ordered pass even though a
"did anything here change?" reading would skip it — the same reading that
let rc345 ship a stale carrier table. ``regen_all.py`` derives its position
from the declared ``consumes=(responsion_schema,)`` edge; a direct run
refuses unless ``--standalone`` is passed.

An idempotence test (re-run -> no diff) guards drift.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Split baked C string literals into adjacent chunks (MSVC single-literal
# limit defence; C concatenates adjacent literals). Same policy as
# gen_carrier_registry.py.
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
        ident = f"rs_lstr_{self._n}"
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


def generate() -> str:
    # Import srmech from the sibling python/ tree (dev-time generation).
    here = Path(__file__).resolve()
    python_dir = here.parent.parent.parent / "python"
    sys.path.insert(0, str(python_dir))
    from srmech.amsc.responsion_schema import _pure_responsion_schema

    schema = _pure_responsion_schema()
    # Byte-order key sort == CPython json.dumps(sort_keys=True) top-level
    # key order (the edge keys are ASCII, asserted below), so the C
    # assembler concatenates in table order and reproduces the canonical
    # whole-schema JSON exactly.
    keys = sorted(schema, key=lambda k: k.encode("utf-8"))

    hoist = _Hoist()
    rows: "list[str]" = []
    for key in keys:
        assert key.isascii(), f"edge key must be pure ASCII: {key!r}"
        responsions = schema[key]
        operator = responsions[0]["operator"]
        carrier = responsions[0]["carrier"]
        assert all(r["operator"] == operator and r["carrier"] == carrier
                   for r in responsions), f"mixed refs on edge {key!r}"
        fragment = json.dumps(responsions, sort_keys=True,
                              separators=(",", ":"))
        rows.append("    {")
        rows.append(f"        {hoist.expr(key)},")
        rows.append(f"        {hoist.expr(operator)},")
        rows.append(f"        {hoist.expr(carrier)},")
        rows.append(f"        {len(responsions)}u,")
        rows.append(f"        {hoist.expr(fragment)},")
        rows.append(f"        {len(fragment.encode('utf-8'))}u,")
        rows.append("    },")

    out: "list[str]" = []
    w = out.append
    w("/* srmech_responsion_registry.c - GENERATED by "
      "c/tools/gen_responsion_registry.py.")
    w(" * DO NOT EDIT BY HAND. Regenerate with:")
    w(" *   python3 tools/regen_all.py            (from docs/srmech/python)")
    w(" *")
    w(" * rc347: this line named the raw generator plus a `>` redirect, which was")
    w(" * exactly trap 2 the runner removed - forget the redirect and the table")
    w(" * goes to the terminal, nothing changes, exit 0. The runner also fixes the")
    w(" * ORDER this file depends on. rc346 left it stale on purpose to keep its")
    w(" * own zero-delta signal clean; rc347 already moves these bytes.")
    w(" *")
    w(" * Source of truth: "
      "srmech.amsc.responsion_schema._pure_responsion_schema()")
    w(" * (the F929 dispatch reduce-back rows + their verbatim _OPEN_HINTS")
    w(" * residues + the continuous response-function ops). The 0.9.0rc225")
    w(" * RESPONSION (stored-relationship) introspection registry -- the k=3")
    w(" * EDGE face binding the rc184 tool registry (verbs) and the rc205")
    w(" * carrier registry (nouns) -- as a const data table (JPL-clean:")
    w(" * const arrays, no dynamic init, no malloc). The accessors + the")
    w(" * canonical JSON assembler live in srmech_responsion_schema.c.")
    w(" * Entries are in byte-sorted edge-key order == the")
    w(" * json.dumps(sort_keys=True) key order the hash-ratchet compares")
    w(" * against; each entry_json fragment is baked pre-canonical (compact,")
    w(" * sorted keys, ensure_ascii -> pure ASCII).")
    w(" *")
    w(f" * Edges: {len(keys)}; responsions: "
      f"{sum(len(schema[k]) for k in keys)}.")
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
    w("/* The responsion registry, in byte-sorted edge-key order (== the")
    w(" * canonical JSON key order the hash-ratchet compares against). */")
    w("const srmech_responsion_entry_t srmech_responsion_registry_table[] = {")
    out.extend(rows)
    w("};")
    w("")
    w("const size_t srmech_responsion_registry_len =")
    w("    sizeof(srmech_responsion_registry_table) "
      "/ sizeof(srmech_responsion_registry_table[0]);")
    w("")
    return "\n".join(out)


if __name__ == "__main__":
    sys.path.insert(
        0, str(Path(__file__).resolve().parents[2] / "python" / "tools"))
    from codegen_manifest import require_regen_all

    require_regen_all("gen_responsion_registry")
    sys.stdout.write(generate())
