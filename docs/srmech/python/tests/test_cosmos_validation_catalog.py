"""Falsification test for the cosmos_validation attested catalog.

Per `[[feedback_every_doc_edit_faces_falsification]]` — Spike #27 /
PR #437 Q6.1 dark-sector monotonicity claim now ships as a
chain-falsifiable catalog. Each row stores Planck-canonical Ω values
+ a scale-factor + expected f_dark(a) rational; this test re-runs
the 9-step `friedmann_dark_fraction` chain row-by-row and bit-exact-
compares produced output to stored expected.
"""

from __future__ import annotations

import importlib.resources as pkg_resources
import json
from pathlib import Path

import pytest

from srmech.amsc import rational


_CATALOG_PKG = "srmech.amsc.attested.cosmos_validation"


def _row_ndjson_path() -> Path:
    return Path(str(pkg_resources.files(_CATALOG_PKG).joinpath("row.ndjson")))


def _iter_rows():
    with open(_row_ndjson_path(), "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            yield json.loads(line)


def _f_dark(row):
    """Reproduce the 9-step Friedmann chain in pure Python."""
    ob = (row["omega_b_num"], row["omega_b_den"])
    oc = (row["omega_c_num"], row["omega_c_den"])
    ol = (row["omega_lambda_num"], row["omega_lambda_den"])
    o_r = (row["omega_r_num"], row["omega_r_den"])
    a = (row["a_num"], row["a_den"])
    a4 = rational.rational_pow_uint(a, 4)
    oc_a = rational.rational_mul(oc, a)
    ol_a4 = rational.rational_mul(ol, a4)
    numer = rational.rational_add(oc_a, ol_a4)
    ob_a = rational.rational_mul(ob, a)
    s1 = rational.rational_add(ob_a, oc_a)
    s2 = rational.rational_add(s1, ol_a4)
    denom = rational.rational_add(s2, o_r)
    return rational.rational_div(numer, denom)


def test_cosmos_validation_row_ndjson_exists() -> None:
    assert _row_ndjson_path().exists()


def test_cosmos_validation_has_at_least_10_rows() -> None:
    assert len(list(_iter_rows())) >= 10


def test_friedmann_chain_falsification_all_rows() -> None:
    n_checked = 0
    for row in _iter_rows():
        assert row["row_type"] == "friedmann_ratio"
        out = _f_dark(row)
        expected = (row["expected_num"], row["expected_den"])
        assert out == expected, (
            f"Row {row['row_label']}: chain produced {out}, expected {expected}"
        )
        n_checked += 1
    assert n_checked >= 10


def test_q6_1_monotonicity_in_a() -> None:
    """f_dark(a) must be strictly monotone increasing in a (Spike #27 Q6.1)."""
    points = []
    for row in _iter_rows():
        a_val = row["a_num"] / row["a_den"]
        f_val = row["expected_num"] / row["expected_den"]
        points.append((a_val, f_val, row["row_label"]))
    points.sort(key=lambda p: p[0])
    for i in range(1, len(points)):
        prev_a, prev_f, prev_l = points[i - 1]
        curr_a, curr_f, curr_l = points[i]
        assert curr_f > prev_f, (
            f"Monotonicity violated: f_dark({prev_l}, a={prev_a:.6f}) = "
            f"{prev_f:.9f} >= f_dark({curr_l}, a={curr_a:.6f}) = {curr_f:.9f}"
        )


def test_rational_add_basic() -> None:
    assert rational.rational_add((1, 2), (1, 3)) == (5, 6)
    assert rational.rational_add((1, 2), (-1, 2)) == (0, 1)
    assert rational.rational_add((3, 4), (5, 4)) == (2, 1)


def test_rational_mul_basic() -> None:
    assert rational.rational_mul((2, 3), (3, 4)) == (1, 2)
    assert rational.rational_mul((0, 1), (5, 7)) == (0, 1)
    assert rational.rational_mul((-2, 3), (3, 4)) == (-1, 2)


def test_rational_div_basic() -> None:
    assert rational.rational_div((1, 1), (1, 2)) == (2, 1)
    assert rational.rational_div((3, 4), (1, 2)) == (3, 2)
    assert rational.rational_div((1, 1), (-1, 2)) == (-2, 1)
    with pytest.raises(ZeroDivisionError):
        rational.rational_div((1, 2), (0, 1))


def test_rational_pow_uint_basic() -> None:
    assert rational.rational_pow_uint((2, 3), 0) == (1, 1)
    assert rational.rational_pow_uint((2, 3), 1) == (2, 3)
    assert rational.rational_pow_uint((2, 3), 4) == (16, 81)
    assert rational.rational_pow_uint((1, 1), 100) == (1, 1)


def test_rational_canonical_today_value() -> None:
    """Spike #27 / PR #437 canonical pin: f_dark(a=1) = 9500/9991."""
    rows = [r for r in _iter_rows() if r["row_label"] == "z_0"]
    assert len(rows) == 1
    assert (rows[0]["expected_num"], rows[0]["expected_den"]) == (9500, 9991)
    assert _f_dark(rows[0]) == (9500, 9991)
