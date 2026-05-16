"""Falsification test for the asymptotic_calculus attested catalog.

Per ``[[feedback_every_doc_edit_faces_falsification]]`` (2026-05-16):
every project doc claim must come with a class-operator chain spec
that proves or disproves the claim under the ADR-0002 catalog-as-
computation framework. This catalog is the first concrete instance
of that falsification infrastructure (Task #234, Spike #28 §10/§11
PR #447).

For each row in ``srmech.amsc.attested.asymptotic_calculus/row.ndjson``,
the test:

1. Reads the row's (x_num, x_den, num_terms) input + (expected_num,
   expected_den) ground-truth output.
2. Runs the operator chain (Class N rational ``exp_series_truncate``
   primitive composed with Class J integer factorial) against the
   input.
3. Bit-exact compares the chain's produced output to the row's
   stored expected output.

Any drift in the underlying Class N / Class J primitives surfaces as
immediate row-by-row test failure. "Sounds right" is NOT a shipping
bar; chain-verified is.
"""

from __future__ import annotations

import importlib.resources as pkg_resources
import json
from pathlib import Path

import pytest

from srmech.amsc import rational
from srmech.amsc.format import read_ndjson


# Path to the catalog ships in-tree (build-time) and in-wheel
# (install-time) at this same module path.
_CATALOG_PKG = "srmech.amsc.attested.asymptotic_calculus"
_ROW_NDJSON = "row.ndjson"


def _row_ndjson_path() -> Path:
    """Locate row.ndjson via importlib.resources so it works in editable
    + wheel installs alike."""
    files = pkg_resources.files(_CATALOG_PKG)
    return Path(str(files.joinpath(_ROW_NDJSON)))


# ──────────────────────────────────────────────────────────────────────
# Catalog presence + parse smoke
# ──────────────────────────────────────────────────────────────────────


def test_catalog_row_ndjson_exists() -> None:
    path = _row_ndjson_path()
    assert path.exists(), f"asymptotic_calculus/row.ndjson missing at {path}"


def test_catalog_descriptor_toml_exists() -> None:
    files = pkg_resources.files(_CATALOG_PKG)
    descriptor = files.joinpath("descriptor.toml")
    schema = files.joinpath("row.schema.json")
    assert Path(str(descriptor)).exists(), "descriptor.toml missing"
    assert Path(str(schema)).exists(), "row.schema.json missing"


def test_catalog_has_at_least_one_row() -> None:
    rows = [r for r in _iter_rows()]
    assert len(rows) >= 1, "asymptotic_calculus catalog must have rows"


# ──────────────────────────────────────────────────────────────────────
# Chain falsification — the load-bearing test
# ──────────────────────────────────────────────────────────────────────


def _iter_rows():
    """Yield each row's data block from the catalog NDJSON."""
    path = _row_ndjson_path()
    # `read_ndjson` returns iterator of MPRRecord-or-bytes depending on
    # version. Use raw-line iteration for explicit control:
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            yield json.loads(line)


def test_exp_series_truncate_chain_falsification_all_rows() -> None:
    """For every row, run the chain and bit-exact-compare to expected.

    rc11: expanded to dispatch by `kind` (exp / sin / cos / log1p / atan).
    Any drift in Class N + Class J primitives surfaces as row-by-row
    exact rational mismatch.
    """
    kind_to_op = {
        "exp":   rational.exp_series_truncate,
        "sin":   rational.sin_series_truncate,
        "cos":   rational.cos_series_truncate,
        "log1p": rational.log1p_series_truncate,
        "atan":  rational.atan_series_truncate,
    }
    n_checked = 0
    for row in _iter_rows():
        assert row["row_type"] == "partial_sum_truncation"
        kind = row["kind"]
        assert kind in kind_to_op, f"unknown kind {kind!r} in row {row['row_label']}"
        op = kind_to_op[kind]
        out_num, out_den = op(
            numerator=row["x_num"],
            denominator=row["x_den"],
            num_terms=row["num_terms"],
        )

        # Bit-exact falsification:
        assert out_num == row["expected_num"], (
            f"Row {row['row_label']}: numerator drift "
            f"(produced {out_num}, expected {row['expected_num']})"
        )
        assert out_den == row["expected_den"], (
            f"Row {row['row_label']}: denominator drift "
            f"(produced {out_den}, expected {row['expected_den']})"
        )
        n_checked += 1

    assert n_checked >= 12, (
        f"Expected >= 12 catalog rows checked at rc6; got {n_checked}"
    )


# ──────────────────────────────────────────────────────────────────────
# Individual canonical rows (regression-pinned)
# ──────────────────────────────────────────────────────────────────────


def test_exp_one_N10_is_canonical_S10_value() -> None:
    """S_10(1) = 9864101/3628800 (the Spike #28 §9 V4 canonical exemplar)."""
    out_num, out_den = rational.exp_series_truncate(1, 1, 10)
    assert (out_num, out_den) == (9864101, 3628800)


def test_exp_zero_returns_unit() -> None:
    """S_N(0) = 1/1 for any N >= 0."""
    for N in [0, 1, 5, 10, 50]:
        out_num, out_den = rational.exp_series_truncate(0, 1, N)
        assert (out_num, out_den) == (1, 1), f"S_{N}(0) should be 1/1"


def test_exp_series_truncate_input_validation() -> None:
    """Type + range guards."""
    with pytest.raises(TypeError):
        rational.exp_series_truncate(1.0, 1, 5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        rational.exp_series_truncate(1, 1, "5")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        rational.exp_series_truncate(1, 0, 5)  # denominator = 0
    with pytest.raises(ValueError):
        rational.exp_series_truncate(1, -1, 5)  # negative denominator
    with pytest.raises(ValueError):
        rational.exp_series_truncate(1, 1, -1)  # negative N
    with pytest.raises(ValueError):
        rational.exp_series_truncate(1, 1, 1000)  # exceeds MAX_TERMS
