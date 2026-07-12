"""rc184 — the C tool-schema registry FOUNDATION GATE.

A bare-C host (no Python) must produce the ~403-tool registry DATA and
the canonical ``tool_schema_sha256`` attestation with no interpreter.
This test pins:

1. **The hash-ratchet (THE gate).** ``srmech_tool_schema_to_json()`` emits
   bytes BYTE-IDENTICAL to the Python SSoT pre-image
   ``json.dumps(get_tool_schema().to_jsonable(), sort_keys=True,
   separators=(",", ":"))``, so ``sha256(C-JSON)`` equals the
   ``_mcpb`` ``tool_schema_sha256``. If a tool is added / changed
   Python-side without regenerating the C table, this fails.

2. **Codegen idempotence.** Re-running ``c/tools/gen_tool_registry.py``
   reproduces the checked-in ``c/src/srmech_tool_registry.c`` exactly
   (drift catcher).

3. **The const table genuinely holds the registry** — count + names +
   get-by-index + get-by-name round-trip the Python registry (not a
   subset / not a shell).

The native-requiring assertions ``skipif`` cleanly when ``HAS_NATIVE`` is
False (a pure / numpy-absent / stale-lib host uses the Python path). The
table-coverage + idempotence tests are pure Python and always run.

numpy-free (imports only srmech + stdlib), per the numpy-absent CI cell.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.tool_schema import get_tool_schema, warmup_all

warmup_all()

_HERE = Path(__file__).resolve().parent
_C_SRC = _HERE.parent.parent / "c" / "src" / "srmech_tool_registry.c"
_CODEGEN = _HERE.parent.parent / "c" / "tools" / "gen_tool_registry.py"

_needs_native = pytest.mark.skipif(
    not _native.has_native_tool_schema(),
    reason="rc184 tool-schema registry C peer not loaded (pure / stale host)",
)


def _canonical_payload() -> bytes:
    """The Python SSoT canonical pre-image the tool_schema_sha256 is
    taken over (compact, sorted, default ensure_ascii=True)."""
    schema = get_tool_schema()
    return json.dumps(
        schema.to_jsonable(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


# ──────────────────────────────────────────────────────────────────────
# 1. The hash-ratchet — THE gate
# ──────────────────────────────────────────────────────────────────────


@_needs_native
def test_c_json_byte_identical_to_python_ssot() -> None:
    """The C serialiser is byte-for-byte identical to the Python
    canonical pre-image (the exactness contract — non-ASCII \\uXXXX,
    astral surrogate pairs, sorted keys, compact separators)."""
    c_json = _native.tool_schema_json_c()
    assert c_json is not None
    py = _canonical_payload()
    assert c_json == py, (
        f"C tool-schema JSON diverged from the Python SSoT "
        f"(C {len(c_json)} bytes vs PY {len(py)} bytes) — regenerate "
        f"c/src/srmech_tool_registry.c with c/tools/gen_tool_registry.py"
    )


@_needs_native
def test_hash_ratchet_matches_mcpb_tool_schema_sha256() -> None:
    """sha256(C canonical JSON) == the _mcpb tool_schema_sha256 (computed
    live from the SSoT). LOCKS the C table to the Python registry."""
    from srmech.mcp._mcpb import _tool_schema_hash

    c_json = _native.tool_schema_json_c()
    assert c_json is not None
    c_hash = hashlib.sha256(c_json).hexdigest()
    assert c_hash == _tool_schema_hash(), (
        "the C tool-schema hash does not match the Python tool_schema_sha256"
    )


@_needs_native
def test_size_query_matches_fill_length() -> None:
    """The NULL-buffer size-query returns the exact byte count a full
    write produces (the two-pass contract)."""
    import ctypes

    lib = _native.LIB
    need = ctypes.c_size_t(0)
    rc = lib.srmech_tool_schema_to_json(None, ctypes.c_size_t(0),
                                        ctypes.byref(need))
    assert rc == _native.SRMECH_OK
    c_json = _native.tool_schema_json_c()
    assert c_json is not None
    assert need.value == len(c_json)


@_needs_native
def test_too_small_buffer_overflows_cleanly() -> None:
    """A too-small non-NULL buffer returns SRMECH_ERR_OVERFLOW (never
    writes past the buffer)."""
    import ctypes

    lib = _native.LIB
    cap = 16
    raw = (ctypes.c_char * cap)()
    got = ctypes.c_size_t(0)
    rc = lib.srmech_tool_schema_to_json(
        ctypes.cast(raw, ctypes.c_void_p), ctypes.c_size_t(cap),
        ctypes.byref(got))
    assert rc == _native.SRMECH_ERR_OVERFLOW


# ──────────────────────────────────────────────────────────────────────
# 2. The const table genuinely holds the whole registry (not a shell)
# ──────────────────────────────────────────────────────────────────────


@_needs_native
def test_registry_count_matches_python() -> None:
    assert _native.tool_registry_count_c() == len(get_tool_schema().tools)


@_needs_native
def test_registry_names_round_trip_in_order() -> None:
    """get-by-index over the whole table reproduces the Python registry
    names in the SAME order the canonical payload uses."""
    names = _native.tool_registry_names_c()
    assert names == [t.name for t in get_tool_schema().tools]


@_needs_native
def test_registry_find_by_name() -> None:
    """get-by-name resolves real tools (first / middle / last of the
    live registry) and rejects an absent one."""
    tools = get_tool_schema().tools
    for entry in (tools[0], tools[len(tools) // 2], tools[-1]):
        assert _native.tool_registry_find_name_c(entry.name) == entry.name
    assert _native.tool_registry_find_name_c("no.such.tool") is None


# ──────────────────────────────────────────────────────────────────────
# 3. Codegen idempotence (drift catcher) — pure Python
# ──────────────────────────────────────────────────────────────────────


def _load_codegen():
    spec = importlib.util.spec_from_file_location(
        "gen_tool_registry_rc184", _CODEGEN
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_codegen_is_idempotent() -> None:
    """Re-running the generator reproduces the checked-in table exactly
    (line-ending normalised). If this fails, the .c is stale."""
    assert _C_SRC.exists(), f"missing generated table {_C_SRC}"
    assert _CODEGEN.exists(), f"missing codegen {_CODEGEN}"
    mod = _load_codegen()
    regenerated = mod.generate().replace("\r\n", "\n")
    on_disk = _C_SRC.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert regenerated == on_disk, (
        "c/src/srmech_tool_registry.c is out of date — regenerate with "
        "c/tools/gen_tool_registry.py"
    )


def test_generated_table_declares_403_entries() -> None:
    """The generated .c mentions the registry size the Python SSoT has
    (a coarse sanity pin independent of the native lib)."""
    n = len(get_tool_schema().tools)
    text = _C_SRC.read_text(encoding="utf-8")
    # Every entry carries an `/* <idx> */` marker; the last is n-1.
    assert f"/* {n - 1} */" in text
    assert f"/* {n} */" not in text
