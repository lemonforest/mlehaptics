"""Falsification test for the pi_digits attested catalog.

Per `[[feedback_every_doc_edit_faces_falsification]]` (2026-05-16):
every project doc claim must come with a class-operator chain spec
that proves or disproves the claim under the ADR-0002 catalog-as-
computation framework. This catalog is the second concrete instance
of that falsification infrastructure (after asymptotic_calculus) and
the first to operationalise
`[[user_stance_pi_spectral_shape_scalar_invariant]]` (Spike #32 /
PR #460).

For each row in ``srmech.amsc.attested.pi_digits/row.ndjson``, the
test:

1. Reads the row's (num_digits) input + (expected_pi_string) ground-
   truth output.
2. Runs the operator chain (Class N rational ``pi_cascade_digits``
   primitive composed via integer Newton-Raphson rational √ at fixed
   precision) against the input.
3. Bit-exact compares the chain's produced output to the row's
   stored expected output.

Any drift in the underlying Class N primitive surfaces as immediate
row-by-row test failure. "Sounds right" is NOT a shipping bar; chain-
verified is.
"""

from __future__ import annotations

import importlib.resources as pkg_resources
import json
from pathlib import Path

import pytest

from srmech.amsc import rational


_CATALOG_PKG = "srmech.amsc.attested.pi_digits"
_ROW_NDJSON = "row.ndjson"


def _row_ndjson_path() -> Path:
    """Locate row.ndjson via importlib.resources (works in editable +
    wheel installs alike)."""
    files = pkg_resources.files(_CATALOG_PKG)
    return Path(str(files.joinpath(_ROW_NDJSON)))


def _iter_rows():
    """Yield each row's data block from the catalog NDJSON."""
    path = _row_ndjson_path()
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            yield json.loads(line)


# ──────────────────────────────────────────────────────────────────────
# Catalog presence + parse smoke
# ──────────────────────────────────────────────────────────────────────


def test_pi_digits_row_ndjson_exists() -> None:
    """row.ndjson is present in the catalog directory."""
    path = _row_ndjson_path()
    assert path.exists(), f"pi_digits/row.ndjson missing at {path}"


def test_pi_digits_descriptor_and_schema_exist() -> None:
    """descriptor.toml and row.schema.json are present."""
    files = pkg_resources.files(_CATALOG_PKG)
    descriptor = files.joinpath("descriptor.toml")
    schema = files.joinpath("row.schema.json")
    assert Path(str(descriptor)).exists(), "descriptor.toml missing"
    assert Path(str(schema)).exists(), "row.schema.json missing"


def test_pi_digits_has_at_least_5_rows() -> None:
    """Catalog ships at least 5 rows covering canonical precision levels."""
    rows = list(_iter_rows())
    assert len(rows) >= 5, (
        f"pi_digits catalog must have >= 5 rows; got {len(rows)}"
    )


def test_pi_digits_canonical_num_digits_values() -> None:
    """Catalog covers the canonical num_digits values: 5, 10, 15, 20,
    25, 50. These map to the natural precision tiers (IEEE-754 single,
    double, double-extended, bignum, bignum-deep)."""
    rows = list(_iter_rows())
    num_digits_set = {row["num_digits"] for row in rows}
    canonical_levels = {5, 10, 15, 20, 25, 50}
    assert canonical_levels.issubset(num_digits_set), (
        f"missing canonical levels: "
        f"{canonical_levels - num_digits_set}"
    )


# ──────────────────────────────────────────────────────────────────────
# Chain falsification — the load-bearing test
# ──────────────────────────────────────────────────────────────────────


def test_pi_cascade_digits_chain_falsification_all_rows() -> None:
    """For every row, run the chain and bit-exact-compare to expected.

    Any drift in the Class N pi_cascade_digits primitive (or its
    helpers _integer_sqrt / _scaled_integer_sqrt) surfaces as
    row-by-row exact string mismatch.
    """
    n_checked = 0
    for row in _iter_rows():
        assert row["row_type"] == "cascade_decimal_expansion", (
            f"row {row['row_label']}: unexpected row_type {row['row_type']!r}"
        )
        assert row["chain_id"] == "pi_cascade_digits"
        # Run the chain:
        produced = rational.pi_cascade_digits(num_digits=row["num_digits"])
        # Bit-exact falsification:
        assert produced == row["expected_pi_string"], (
            f"Row {row['row_label']}: chain produced {produced!r}, "
            f"expected {row['expected_pi_string']!r}"
        )
        n_checked += 1
    assert n_checked >= 5, (
        f"Expected >= 5 catalog rows checked at rc12; got {n_checked}"
    )


# ──────────────────────────────────────────────────────────────────────
# Individual canonical rows (regression-pinned)
# ──────────────────────────────────────────────────────────────────────


def test_pi_15_digits_canonical_double_precision_boundary() -> None:
    """15-digit row is at the IEEE-754 double-precision boundary
    (the most common reference value for π in numerical code)."""
    rows = [r for r in _iter_rows() if r["row_label"] == "pi_15_digits"]
    assert len(rows) == 1
    assert rows[0]["expected_pi_string"] == "3.141592653589793"
    assert (rational.pi_cascade_digits(15)
            == "3.141592653589793")


def test_pi_50_digits_canonical_bignum_deep() -> None:
    """50-digit row at the practical maximum; pins the deepest cascade
    + bignum-precision path."""
    rows = [r for r in _iter_rows() if r["row_label"] == "pi_50_digits"]
    assert len(rows) == 1
    expected = (
        "3.14159265358979323846264338327950288419716939937510"
    )
    assert rows[0]["expected_pi_string"] == expected
    assert rational.pi_cascade_digits(50) == expected


def test_all_rows_share_canonical_pi_prefix() -> None:
    """Substrate-invariance documentation: every row in the catalog
    is a prefix of the canonical π expansion — they all share the
    same substrate-emergent shape per
    `[[user_stance_pi_spectral_shape_scalar_invariant]]`."""
    canonical = "3.14159265358979323846264338327950288419716939937510"
    for row in _iter_rows():
        d = row["num_digits"]
        expected_prefix = canonical[:d + 2]  # "3." + d digits
        assert row["expected_pi_string"] == expected_prefix, (
            f"Row {row['row_label']}: expected_pi_string is not a "
            f"prefix of canonical π (expected {expected_prefix!r}, "
            f"got {row['expected_pi_string']!r})"
        )


def test_pi_digits_attestation_required_source_fields() -> None:
    """Every row carries the expected source-citation fields per the
    catalog's `[attestation]` block."""
    for row in _iter_rows():
        # source_published_date is mandatory per row.schema.json:
        assert "source_published_date" in row, (
            f"Row {row['row_label']}: missing source_published_date"
        )
        # entered_locally_at is mandatory:
        assert "entered_locally_at" in row, (
            f"Row {row['row_label']}: missing entered_locally_at"
        )
        # chain_id must point to the descriptor's operator_chain:
        assert row["chain_id"] == "pi_cascade_digits"
