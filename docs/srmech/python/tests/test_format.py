"""Format module tests — MPR record + validation + NDJSON IO.

Ported from
``docs/antikythera-maths/ephemerides-spectral/python/tests/test_attested_collector.py``
(Format module section) at Phase 2 of Task #197. Each test exercises
the `srmech.amsc.format` surface in isolation; no ephemerides-spectral
dependency.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srmech.math.q import Q            # rc479 (`#T1188`): contract A's carrier
from srmech.amsc.format import (
    MANDATORY_ATTESTATION_FIELDS,
    MANDATORY_RENDERING_FIELDS,
    MPR_SCHEMA_VERSION,
    MPRRecord,
    MPRValidationError,
    read_ndjson,
    sha256_bytes,
    validate_mpr_record,
    write_ndjson,
)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────


def _valid_attestation() -> dict:
    return {
        "source_doi": "10.1029/test",
        "source_url": "https://example.com/page",
        "license": "CC-BY-4.0",
        "retrieved_at": "2026-05-13T14:23:11Z",
        "response_sha256": "0" * 64,
        "parser_version": "srmech 0.1.0",
        "parser_rule_hash": "1" * 64,
        "collector_descriptor_path": "configs/test.toml",
        "collector_descriptor_hash": "2" * 64,
    }


def _valid_rendering() -> dict:
    return {
        "human_readable_name": "Fixture Source — row 1",
        "cite_as": "Fixture 2026; retrieved 2026-05-13.",
        "purpose": "fixture row for tests",
    }


def _valid_record() -> MPRRecord:
    return MPRRecord(
        mpr_version=MPR_SCHEMA_VERSION,
        data={"name": "Mauna Loa", "latitude_deg": 19.475, "longitude_deg": -155.608},
        data_schema_id="fixture.test.v1",
        attestation=_valid_attestation(),
        rendering=_valid_rendering(),
    )


# ──────────────────────────────────────────────────────────────────────
# Schema-version + mandatory-field counts
# ──────────────────────────────────────────────────────────────────────


def test_mpr_schema_version_is_1_0() -> None:
    assert MPR_SCHEMA_VERSION == "1.0"


def test_mandatory_attestation_fields_count() -> None:
    """Pin the v1 attestation schema at 9 required fields."""
    assert len(MANDATORY_ATTESTATION_FIELDS) == 9


def test_mandatory_rendering_fields_count() -> None:
    assert len(MANDATORY_RENDERING_FIELDS) == 3


# ──────────────────────────────────────────────────────────────────────
# MPRRecord serialization
# ──────────────────────────────────────────────────────────────────────


def test_mpr_record_round_trip_through_json_line() -> None:
    """The NDJSON round trip, RESTATED for contract A (rc479, `#T1188`).

    ⚠️ **It used to read ``from_json_line(to_json_line(r)) == r`` and that is
    now false BY DESIGN, on the one axis the whole rc is about.** The fixture
    holds Python ``float``s (``19.475``); ``to_json_line`` writes the decimal
    text ``19.475``; and the reader now returns the exact rational that TEXT
    names, ``Q(779, 40)`` — which is not the double ``19.475``, because the
    double is ``5482716835708109 / 2**48``. Asserting the old equality would
    be pinning the rounding the contract removes.

    Four clauses replace it, and together they are stronger than the equality
    they retire:

    1. the read-back leaf is EXACT and is the decimal the line spells;
    2. it PROJECTS to the bit-identical double the record held, so no float
       consumer moves;
    3. the WRITE is byte-stable — re-serialising the read-back record gives
       the identical line, which is what keeps every committed
       ``response_sha256`` valid;
    4. the round trip is an exact FIXED POINT from the second pass onward.
    """
    import struct

    record = _valid_record()
    line = record.to_json_line()
    back = MPRRecord.from_json_line(line)

    # (1) exact, and the decimal the line spells
    lat = back.data["latitude_deg"]
    assert isinstance(lat, Q), f"contract A: exact leaf, got {type(lat).__name__}"
    assert lat.numerator * 1000 == 19475 * lat.denominator

    # (2) projects to the bit-identical double the record held
    for key in ("latitude_deg", "longitude_deg"):
        assert struct.pack(">d", float(back.data[key])) == \
               struct.pack(">d", record.data[key]), key

    # (3) byte-stable write — the digest surface does not move
    assert back.to_json_line() == line

    # (4) an exact fixed point from the second pass
    assert MPRRecord.from_json_line(back.to_json_line()) == back

    # the non-numeric fields are untouched
    assert back.mpr_version == record.mpr_version
    assert back.data["name"] == record.data["name"]
    assert back.data_schema_id == record.data_schema_id
    assert back.attestation == record.attestation
    assert back.rendering == record.rendering


def test_validate_accepts_valid_record() -> None:
    validate_mpr_record(_valid_record())


def test_validate_rejects_unknown_mpr_version() -> None:
    record = MPRRecord(
        mpr_version="99.0",
        data={},
        data_schema_id="x.v1",
        attestation=_valid_attestation(),
        rendering=_valid_rendering(),
    )
    with pytest.raises(MPRValidationError, match="unrecognised mpr_version"):
        validate_mpr_record(record)


def test_validate_rejects_missing_attestation_field() -> None:
    bad = dict(_valid_attestation())
    del bad["response_sha256"]
    record = MPRRecord(
        mpr_version=MPR_SCHEMA_VERSION,
        data={},
        data_schema_id="x.v1",
        attestation=bad,
        rendering=_valid_rendering(),
    )
    with pytest.raises(MPRValidationError, match="response_sha256"):
        validate_mpr_record(record)


def test_validate_rejects_empty_data_schema_id() -> None:
    record = MPRRecord(
        mpr_version=MPR_SCHEMA_VERSION,
        data={},
        data_schema_id="",
        attestation=_valid_attestation(),
        rendering=_valid_rendering(),
    )
    with pytest.raises(MPRValidationError, match="data_schema_id"):
        validate_mpr_record(record)


def test_validate_rejects_missing_rendering_field() -> None:
    """rendering block must carry all 3 mandatory fields."""
    bad = dict(_valid_rendering())
    del bad["cite_as"]
    record = MPRRecord(
        mpr_version=MPR_SCHEMA_VERSION,
        data={},
        data_schema_id="x.v1",
        attestation=_valid_attestation(),
        rendering=bad,
    )
    with pytest.raises(MPRValidationError, match="cite_as"):
        validate_mpr_record(record)


# ──────────────────────────────────────────────────────────────────────
# NDJSON IO
# ──────────────────────────────────────────────────────────────────────


def test_ndjson_round_trip(tmp_path: Path) -> None:
    """Write three records, read them back, assert byte-stable order."""
    records = [
        MPRRecord(
            mpr_version=MPR_SCHEMA_VERSION,
            data={"name": f"r{i}", "lat": float(i)},
            data_schema_id="fixture.test.v1",
            attestation=_valid_attestation(),
            rendering=_valid_rendering(),
        )
        for i in range(3)
    ]
    path = tmp_path / "out.ndjson"
    n = write_ndjson(path, records)
    assert n == 3
    read_back = list(read_ndjson(path))
    assert read_back == records


def test_ndjson_rejects_invalid_json(tmp_path: Path) -> None:
    """Lines that aren't valid JSON raise MPRValidationError with the line number."""
    path = tmp_path / "bad.ndjson"
    path.write_text("this is not json at all\n", encoding="utf-8")
    with pytest.raises(MPRValidationError, match="line"):
        list(read_ndjson(path))


def test_ndjson_skips_empty_lines(tmp_path: Path) -> None:
    """NDJSON allows empty lines by convention; the reader skips them."""
    path = tmp_path / "with_blanks.ndjson"
    path.write_text("\n\n\n", encoding="utf-8")
    assert list(read_ndjson(path)) == []


def test_ndjson_skips_hash_comment_lines(tmp_path: Path) -> None:
    """Lines beginning with ``#`` are project-convention comment headers
    and must be skipped by both pure-Python and native paths.

    Regression test for the 0.4.1rc1 bug where ``read_ndjson`` choked
    on the leading ``# CMB Polarisation Power Spectra catalogue ...``
    block in ``cmb_polarisation_spectra/row.ndjson`` (and the same
    block at the head of every ``cmb_*`` / attested-collector NDJSON
    file across the spectral-research portfolio).
    ``catalog.get_attested_dataset`` was already comment-aware via a
    different code path; ``catalog.attestation_audit`` calls
    ``read_ndjson`` directly and was failing on the same files.
    """
    record = _valid_record()
    path = tmp_path / "with_comments.ndjson"
    payload = (
        "# Header comment line 1\n"
        "# Header comment line 2\n"
        "\n"
        + record.to_json_line() + "\n"
        "# Mid-file comment, just in case\n"
        + record.to_json_line() + "\n"
        "   # Indented comment (leading whitespace tolerated)\n"
    )
    path.write_text(payload, encoding="utf-8")
    records = list(read_ndjson(path))
    assert len(records) == 2
    assert all(r.mpr_version == record.mpr_version for r in records)


def test_ndjson_writes_lf_line_endings_always(tmp_path: Path) -> None:
    """Byte-stability across Windows/Linux checkouts requires LF endings."""
    record = _valid_record()
    path = tmp_path / "out.ndjson"
    write_ndjson(path, [record])
    raw = path.read_bytes()
    # On Windows, default newline mode would yield CRLF; we explicitly
    # set newline='\n' in write_ndjson to prevent that.
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")


# ──────────────────────────────────────────────────────────────────────
# SHA-256 helper
# ──────────────────────────────────────────────────────────────────────


def test_sha256_bytes_deterministic() -> None:
    assert sha256_bytes(b"abc") == sha256_bytes(b"abc")
    assert sha256_bytes(b"abc") != sha256_bytes(b"abd")
    # Well-known SHA-256("abc").
    assert sha256_bytes(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_sha256_bytes_empty() -> None:
    """SHA-256 of empty bytes is a fixed well-known value."""
    assert sha256_bytes(b"") == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
