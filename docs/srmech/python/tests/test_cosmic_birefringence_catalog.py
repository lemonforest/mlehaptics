"""Falsification test for the cosmic_birefringence attested catalog.

v0.5.0rc20 / issue #743 (wishlist W9). New AMSC attested catalog
``srmech.amsc.attested.cosmic_birefringence`` carrying the published
cosmic-birefringence isotropic rotation angle beta posterior — the
parity-ODD CMB observable extracted from the EB cross-correlation. It is
the parity-odd companion to the parity-even ``cmb_polarisation_spectra``
(TE/EE/BB) and ``cmb_bispectrum`` (fNL) catalogs.

This test:

1. Asserts the three catalog files (descriptor.toml + row.ndjson +
   row.schema.json) are present in the package.
2. Asserts the catalog auto-discovers (appears in ``list_attested_sources``)
   and loads via ``get_attested_dataset`` with the full synthesised 9-field
   MPR attestation block per row.
3. Asserts >= 4 rows, the single ``row_type`` ``birefringence_beta_posterior``,
   and the adapter-required per-row trio (source_doi + source_published_date
   + entered_locally_at) plus source_arxiv.
4. Regression-PINS the four PDF-verified beta central values
   (0.35 / 0.30 / 0.33 / 0.342) AND the ASYMMETRIC Eskilt & Komatsu pair
   (beta_err_lo_deg = 0.091, beta_err_hi_deg = 0.094, lo != hi) — the
   read path does NOT validate against row.schema.json, so the value pins
   live here (matching how the other attested-catalog tests work). The
   asymmetry is kept intact (never symmetrised / abs()'d) — sign /
   phase-boundary discipline at the attestation scale.
5. Asserts the Minami & Komatsu measurement row cites arXiv **2011.11254**
   (the measurement paper) and NOT 2006.15982 (the methodology-only
   companion that reports no beta from data) — a load-bearing citation
   correction (the MPM guard against attesting a value to a paper that
   does not report it).

Pure-Python; no C.
"""

from __future__ import annotations

import importlib.resources as pkg_resources
import json
from pathlib import Path

from srmech.amsc.catalog import (
    get_attested_dataset,
    list_attested_sources,
)


_CATALOG_PKG = "srmech.amsc.attested.cosmic_birefringence"
_SOURCE_KEY = "cosmic_birefringence"
_ROW_NDJSON = "row.ndjson"
_ROW_TYPE = "birefringence_beta_posterior"

# The four PDF-verified headline measurements (measurement_id -> beta_deg).
# Extracted from the measuring papers' arXiv abstracts; do NOT alter.
_EXPECTED_BETA = {
    "minami_komatsu_2020_planck_pr3": 0.35,
    "diego_palazuelos_2022_planck_pr4": 0.30,
    "eskilt_2022_planck_pr4_freqindep": 0.33,
    "eskilt_komatsu_2022_wmap_planck_pr4": 0.342,
}

# The 9 mandatory MPR attestation fields synthesised at read time.
_ATTESTATION_FIELDS = {
    "source_doi",
    "source_url",
    "license",
    "retrieved_at",
    "response_sha256",
    "parser_version",
    "parser_rule_hash",
    "collector_descriptor_path",
    "collector_descriptor_hash",
}


def _row_ndjson_path() -> Path:
    """Locate row.ndjson via importlib.resources (editable + wheel alike)."""
    files = pkg_resources.files(_CATALOG_PKG)
    return Path(str(files.joinpath(_ROW_NDJSON)))


def _iter_raw_rows():
    """Yield each row's FLAT data dict directly from the catalog NDJSON."""
    path = _row_ndjson_path()
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            yield json.loads(line)


# ──────────────────────────────────────────────────────────────────────
# Catalog presence + auto-discovery
# ──────────────────────────────────────────────────────────────────────


def test_cosmic_birefringence_catalog_files_exist() -> None:
    """descriptor.toml + row.ndjson + row.schema.json are present."""
    files = pkg_resources.files(_CATALOG_PKG)
    for name in ("descriptor.toml", "row.ndjson", "row.schema.json"):
        p = Path(str(files.joinpath(name)))
        assert p.exists(), f"cosmic_birefringence/{name} missing at {p}"


def test_cosmic_birefringence_auto_discovers() -> None:
    """The new source appears in list_attested_sources() with no
    registration code (auto-discovery walks the attested root)."""
    listing = list_attested_sources()
    assert listing["ok"] is True
    keys = {s["key"] for s in listing["sources"]}
    assert _SOURCE_KEY in keys, (
        f"{_SOURCE_KEY!r} not auto-discovered; got {sorted(keys)}"
    )
    # The literature_curated filter must also surface it.
    curated = list_attested_sources(adapter_class="curated")
    curated_keys = {s["key"] for s in curated["sources"]}
    assert _SOURCE_KEY in curated_keys


# ──────────────────────────────────────────────────────────────────────
# Dataset load + row count + row_type + attestation synthesis
# ──────────────────────────────────────────────────────────────────────


def test_cosmic_birefringence_loads_at_least_4_rows() -> None:
    """get_attested_dataset returns the catalog with >= 4 rows."""
    ds = get_attested_dataset(_SOURCE_KEY)
    assert ds["ok"] is True, ds
    total = ds.get("total")
    assert total is not None and total >= 4, (
        f"cosmic_birefringence must have >= 4 rows; got {total}"
    )
    assert len(ds["rows"]) >= 4


def test_cosmic_birefringence_single_row_type() -> None:
    """Every row carries the single row_type 'birefringence_beta_posterior'
    (both in the raw NDJSON and in the loaded dataset)."""
    for data in _iter_raw_rows():
        assert data["row_type"] == _ROW_TYPE, (
            f"row {data.get('measurement_id')!r}: unexpected row_type "
            f"{data.get('row_type')!r}"
        )
    ds = get_attested_dataset(_SOURCE_KEY)
    for row in ds["rows"]:
        assert row["data"]["row_type"] == _ROW_TYPE


def test_cosmic_birefringence_attestation_synthesised() -> None:
    """Each loaded row carries the full 9-field synthesised MPR attestation
    block, with per-row source_doi and a deterministic retrieved_at."""
    ds = get_attested_dataset(_SOURCE_KEY)
    assert len(ds["rows"]) >= 4
    for row in ds["rows"]:
        att = row["attestation"]
        assert _ATTESTATION_FIELDS.issubset(att.keys()), (
            f"missing attestation fields: {_ATTESTATION_FIELDS - set(att)}"
        )
        # per-row DOI flows into the attestation block:
        assert att["source_doi"] == row["data"]["source_doi"]
        assert att["source_doi"].startswith("10.")
        # retrieved_at is deterministic (derived from entered_locally_at):
        assert att["retrieved_at"].endswith("T00:00:00Z")
        assert att["retrieved_at"].startswith(row["data"]["entered_locally_at"])
        # response_sha256 is a 64-hex SHA-256 digest:
        assert len(att["response_sha256"]) == 64
        assert att["parser_version"] == "literature_curated/v1"


def test_cosmic_birefringence_per_row_provenance_trio() -> None:
    """Every row carries the adapter-required trio (source_doi,
    source_published_date, entered_locally_at) plus source_arxiv."""
    n = 0
    for data in _iter_raw_rows():
        mid = data.get("measurement_id")
        for field in ("source_doi", "source_published_date",
                      "entered_locally_at", "source_arxiv"):
            assert data.get(field), (
                f"row {mid!r}: missing/empty required field {field!r}"
            )
        n += 1
    assert n >= 4


# ──────────────────────────────────────────────────────────────────────
# Regression-pinned beta values (the schema does NOT enforce these)
# ──────────────────────────────────────────────────────────────────────


def test_cosmic_birefringence_beta_values_pinned() -> None:
    """The four PDF-verified beta central values are pinned exactly."""
    by_id = {d["measurement_id"]: d for d in _iter_raw_rows()}
    for mid, expected in _EXPECTED_BETA.items():
        assert mid in by_id, f"missing measurement {mid!r}"
        assert by_id[mid]["beta_deg"] == expected, (
            f"{mid}: beta_deg {by_id[mid]['beta_deg']} != {expected}"
        )


def test_cosmic_birefringence_eskilt_komatsu_asymmetric_error() -> None:
    """The Eskilt & Komatsu 2022 joint posterior is ASYMMETRIC: the two
    68% C.L. half-widths are stored separately (lo=0.091, hi=0.094) and
    are NOT symmetrised/abs()'d. lo != hi must hold."""
    by_id = {d["measurement_id"]: d for d in _iter_raw_rows()}
    row = by_id["eskilt_komatsu_2022_wmap_planck_pr4"]
    assert row["beta_err_lo_deg"] == 0.091
    assert row["beta_err_hi_deg"] == 0.094
    assert row["beta_err_lo_deg"] != row["beta_err_hi_deg"], (
        "asymmetric posterior must NOT be symmetrised"
    )
    # The three symmetric quotes keep lo == hi:
    for mid in ("minami_komatsu_2020_planck_pr3",
                "diego_palazuelos_2022_planck_pr4",
                "eskilt_2022_planck_pr4_freqindep"):
        r = by_id[mid]
        assert r["beta_err_lo_deg"] == r["beta_err_hi_deg"], (
            f"{mid}: symmetric quote should have lo == hi"
        )


def test_cosmic_birefringence_minami_arxiv_is_measurement_paper() -> None:
    """The Minami & Komatsu 0.35-deg row cites arXiv 2011.11254 (the
    measurement paper 'New Extraction of the Cosmic Birefringence from the
    Planck 2018 Polarization Data') and NOT 2006.15982 (the methodology-only
    companion that reports no beta from data). Attesting the value to
    2006.15982 would cite a paper that does not report it."""
    by_id = {d["measurement_id"]: d for d in _iter_raw_rows()}
    row = by_id["minami_komatsu_2020_planck_pr3"]
    assert row["source_arxiv"] == "2011.11254", (
        f"Minami & Komatsu measurement must cite arXiv 2011.11254; "
        f"got {row['source_arxiv']!r}"
    )
    assert row["source_arxiv"] != "2006.15982"
    assert "2011.11254" in (row.get("source_url") or "")
    assert row["source_doi"] == "10.1103/PhysRevLett.125.221301"
