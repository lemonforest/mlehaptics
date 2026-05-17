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


def test_pi_digits_has_12_rows_rc13() -> None:
    """rc13 cap-expansion adds 6 rows at higher digit counts on top of
    rc12's 6. Final catalog: exactly 12 rows. Any future rc adding
    rows must update this ratchet."""
    rows = list(_iter_rows())
    assert len(rows) == 12, (
        f"rc13 catalog must have exactly 12 rows (rc12's 6 + rc13's 6); "
        f"got {len(rows)}"
    )


def test_pi_digits_canonical_num_digits_values() -> None:
    """Catalog covers the canonical num_digits values across rc12 +
    rc13: 5, 10, 15, 20, 25, 50 (rc12 — natural precision tiers IEEE-
    754 single / double / double-extended / bignum / bignum-deep) and
    100, 200, 350, 500, 750, 1000 (rc13 cap-expansion — Task #248
    follow-on to PR #468 benchmark; 350 is the user's 'weird number
    on purpose' probe; 1000 is the rc13 ceiling)."""
    rows = list(_iter_rows())
    num_digits_set = {row["num_digits"] for row in rows}
    canonical_levels = {5, 10, 15, 20, 25, 50,
                        100, 200, 350, 500, 750, 1000}
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
    # rc13 ratchet: at least 12 rows must round-trip exactly (rc12's 6
    # + rc13's 6 new at 100/200/350/500/750/1000).
    assert n_checked >= 12, (
        f"Expected >= 12 catalog rows checked at rc13; got {n_checked}"
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
    """50-digit row at the rc12 practical maximum; pins the rc12-era
    cascade + bignum-precision path."""
    rows = [r for r in _iter_rows() if r["row_label"] == "pi_50_digits"]
    assert len(rows) == 1
    expected = (
        "3.14159265358979323846264338327950288419716939937510"
    )
    assert rows[0]["expected_pi_string"] == expected
    assert rational.pi_cascade_digits(50) == expected


def test_pi_350_digits_canonical_weird_number_probe() -> None:
    """350-digit row is the user's 'weird number on purpose' probe from
    PR #468 benchmark — deliberately non-canonical (not a power of 10,
    not a CF convergent denominator). rc12 capped at 50 by validation;
    rc13 (Task #248) raises the cap to 1000 with auto-scaled depth +
    precision_bits. The benchmark wall-time finding's resolution lives
    here."""
    rows = [r for r in _iter_rows() if r["row_label"] == "pi_350_digits"]
    assert len(rows) == 1
    expected = CANONICAL_PI_1000[:352]  # "3." + 350 digits
    assert rows[0]["expected_pi_string"] == expected
    assert rational.pi_cascade_digits(350) == expected


def test_pi_1000_digits_canonical_rc13_ceiling() -> None:
    """1000-digit row is the rc13 cap-expansion ceiling. Pins the
    deepest cascade (depth=1800, precision_bits=10240) auto-scaled
    from num_digits=1000. The bound itself is not mathematical —
    callers may pass explicit max_cascade_depth and precision_bits
    kwargs for studies at non-canonical parameter combinations."""
    rows = [r for r in _iter_rows() if r["row_label"] == "pi_1000_digits"]
    assert len(rows) == 1
    expected = CANONICAL_PI_1000  # "3." + 1000 digits
    assert rows[0]["expected_pi_string"] == expected
    assert rational.pi_cascade_digits(1000) == expected


# Canonical π to 1000 decimal digits — the load-bearing ground truth for
# the catalog. Generated independently of srmech (via mpmath at decimal
# precision 1100 + verified bit-exactly against the rc12 cascade at all
# rc12-supported precision levels). The catalog rows must each be a
# prefix of this reference; any drift surfaces as immediate test failure.
# rc13 (Task #248) extends the catalog up to num_digits=1000 — this
# reference now covers the full catalog range.
CANONICAL_PI_1000 = (
    "3.1415926535897932384626433832795028841971693993751058209749445923078164"
    "062862089986280348253421170679821480865132823066470938446095505822317253"
    "594081284811174502841027019385211055596446229489549303819644288109756659"
    "334461284756482337867831652712019091456485669234603486104543266482133936"
    "072602491412737245870066063155881748815209209628292540917153643678925903"
    "600113305305488204665213841469519415116094330572703657595919530921861173"
    "819326117931051185480744623799627495673518857527248912279381830119491298"
    "336733624406566430860213949463952247371907021798609437027705392171762931"
    "767523846748184676694051320005681271452635608277857713427577896091736371"
    "787214684409012249534301465495853710507922796892589235420199561121290219"
    "608640344181598136297747713099605187072113499999983729780499510597317328"
    "160963185950244594553469083026425223082533446850352619311881710100031378"
    "387528865875332083814206171776691473035982534904287554687311595628638823"
    "537875937519577818577805321712268066130019278766111959092164201989"
)


def test_all_rows_share_canonical_pi_prefix() -> None:
    """Substrate-invariance documentation: every row in the catalog
    is a prefix of the canonical π expansion — they all share the
    same substrate-emergent shape per
    `[[user_stance_pi_spectral_shape_scalar_invariant]]`."""
    for row in _iter_rows():
        d = row["num_digits"]
        expected_prefix = CANONICAL_PI_1000[:d + 2]  # "3." + d digits
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
