"""Cross-language parity test for srmech_ndjson_iter.

Task #201 Phase B4 — pins the native C NDJSON line tokeniser to
byte-exact agreement with Python's text-mode line iteration over
the same files. JSON parsing stays in Python; this test verifies
the file-IO + line-split layer.

The test is gracefully skipped when the native library isn't shipped
(pure-Python wheel install on Pyodide / WASM).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from srmech.amsc import _native, format as srfmt


pytestmark = pytest.mark.skipif(
    not _native.HAS_NATIVE,
    reason=(
        "native srmech library not loaded "
        f"(LOAD_ERROR={_native.LOAD_ERROR}); "
        "this test pins C/Python parity, so a pure-Python wheel "
        "install legitimately skips it"
    ),
)


# ──────────────────────────────────────────────────────────────────────
# Fixture helpers
# ──────────────────────────────────────────────────────────────────────


def _write_tmp(content: bytes) -> Path:
    """Write `content` to a tempfile and return its path."""
    fd, path = tempfile.mkstemp(suffix=".ndjson")
    os.close(fd)
    p = Path(path)
    p.write_bytes(content)
    return p


def _python_lines(p: Path) -> list[tuple[int, bytes]]:
    """Reference (lineno, line_bytes) extraction matching the
    C-side semantics: 1-indexed over all lines (including empty),
    only non-empty lines (after CR-strip) returned."""
    out: list[tuple[int, bytes]] = []
    with p.open("rb") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip(b"\n").rstrip(b"\r")
            if len(line) == 0:
                continue
            out.append((lineno, line))
    return out


# ──────────────────────────────────────────────────────────────────────
# Fixture inputs covering the line-tokenisation edge cases
# ──────────────────────────────────────────────────────────────────────
FIXTURES: list[tuple[str, bytes]] = [
    ("empty file", b""),
    ("one line, no trailing newline", b"hello"),
    ("one line, trailing newline", b"hello\n"),
    ("two lines", b"first\nsecond\n"),
    ("blank lines between content",
     b'{"a":1}\n\n{"b":2}\n\n\n{"c":3}\n'),
    ("only blank lines", b"\n\n\n\n"),
    ("CRLF line endings",
     b'{"x":1}\r\n{"y":2}\r\n'),
    ("mixed LF and CRLF",
     b'{"a":1}\n{"b":2}\r\n{"c":3}\n'),
    ("trailing line, no final newline",
     b'first\nsecond\nthird'),
    ("leading blanks then content",
     b'\n\n{"a":1}\n'),
    ("long single line",
     b'{"a":"' + b"x" * 1000 + b'"}\n'),
    ("100 lines",
     b"\n".join(f'{{"i":{i}}}'.encode() for i in range(100)) + b"\n"),
]


@pytest.mark.parametrize("name,content", FIXTURES, ids=[n for n, _ in FIXTURES])
def test_native_matches_python_lines(name: str, content: bytes) -> None:
    """Native srmech_ndjson_iter produces the same (lineno, bytes)
    sequence as the Python reference reader, for every fixture."""
    p = _write_tmp(content)
    try:
        py = _python_lines(p)
        native = _native.ndjson_lines_c(str(p))
        assert native == py, (
            f"{name}: native {native!r} != python {py!r}"
        )
    finally:
        p.unlink(missing_ok=True)


def test_format_read_ndjson_dispatches_to_native(tmp_path: Path) -> None:
    """``srmech.amsc.format.read_ndjson`` returns MPRRecords whose
    payloads round-trip through json.loads identically on both
    paths."""
    # Use a real MPR-shaped row so MPRRecord.from_json_line accepts it.
    rows = [
        {
            "mpr_version": "1.0",
            "data": {"name": "alpha", "value": 1},
            "data_schema_id": "test://schema/alpha",
            "attestation": {
                "source_doi": "10.0/test",
                "source_url": "https://example.invalid/a",
                "license": "CC0",
                "retrieved_at": "2026-05-13T00:00:00Z",
                "response_sha256": "0" * 64,
                "parser_version": "srmech 0.1.1rc6",
                "parser_rule_hash": "1" * 64,
                "collector_descriptor_path": "test/desc.toml",
                "collector_descriptor_hash": "2" * 64,
            },
            "rendering": {
                "name": "Alpha",
                "purpose": "test",
                "cite_as": "Alpha",
            },
        },
    ]
    p = tmp_path / "rows.ndjson"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n",
                 encoding="utf-8")

    records = list(srfmt.read_ndjson(p))
    assert len(records) == 1
    assert records[0].data == rows[0]["data"]


def test_read_ndjson_malformed_line_lineno_correct(tmp_path: Path) -> None:
    """When a malformed JSON line trips MPRValidationError, the
    line number in the error message corresponds to the original
    file line (including any leading blank lines)."""
    p = tmp_path / "bad.ndjson"
    # JSON syntax error on line 3 (two leading blank lines).
    p.write_bytes(b'\n\n{not valid json}\n')
    with pytest.raises(srfmt.MPRValidationError) as exc_info:
        list(srfmt.read_ndjson(p))
    msg = str(exc_info.value)
    assert ":3:" in msg or "line 3" in msg, (
        f"expected line-3 marker in error message, got: {msg!r}"
    )


def test_read_ndjson_missing_file_raises_oserror(tmp_path: Path) -> None:
    """A missing-file path raises ``OSError`` (covers both native
    NativeNDJsonError → OSError translation and the Python path's
    open() FileNotFoundError, which is a subclass of OSError)."""
    p = tmp_path / "nonexistent.ndjson"
    with pytest.raises(OSError):
        list(srfmt.read_ndjson(p))


def test_native_line_count_matches_python_for_big_file(tmp_path: Path) -> None:
    """1000-record stress: counts agree, last-record agrees."""
    rows_bytes = b"\n".join(
        json.dumps({"i": i, "padding": "x" * 50}).encode()
        for i in range(1000)
    ) + b"\n"
    p = tmp_path / "big.ndjson"
    p.write_bytes(rows_bytes)
    py = _python_lines(p)
    native = _native.ndjson_lines_c(str(p))
    assert len(native) == 1000
    assert native == py


def test_native_handles_files_larger_than_chunk(tmp_path: Path) -> None:
    """Files larger than the C-side 64 KiB chunk buffer must
    correctly assemble lines that span chunk boundaries."""
    # Build a payload >> 64 KiB (the C-side SRMECH_NDJSON_CHUNK_BYTES).
    # Each row carries enough padding that 5000 rows ≈ 250 KiB, well
    # past two chunk reads.
    rows_bytes = b"\n".join(
        json.dumps({"i": i, "tag": f"row_{i:04d}", "pad": "y" * 32}).encode()
        for i in range(5000)
    ) + b"\n"
    assert len(rows_bytes) > 64 * 1024, "fixture must exceed chunk size"
    p = tmp_path / "big.ndjson"
    p.write_bytes(rows_bytes)
    py = _python_lines(p)
    native = _native.ndjson_lines_c(str(p))
    assert native == py, "chunk-boundary line assembly diverged"


def test_native_rejects_line_over_max(tmp_path: Path) -> None:
    """A line > SRMECH_NDJSON_MAX_LINE_BYTES (1 MiB) returns
    SRMECH_ERR_OVERFLOW → NativeNDJsonError."""
    # 1.5 MiB single line
    huge_line = b"x" * (1 * 1024 * 1024 + 256 * 1024) + b"\n"
    p = tmp_path / "huge.ndjson"
    p.write_bytes(huge_line)
    with pytest.raises(_native.NativeNDJsonError) as exc_info:
        _native.ndjson_lines_c(str(p))
    assert exc_info.value.status == _native.SRMECH_ERR_OVERFLOW
