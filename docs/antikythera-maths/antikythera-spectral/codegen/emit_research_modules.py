"""Copy ``research/*.py`` into ``antikythera_spectral/_research/`` for shipping.

The research-scaffold modules under ``docs/antikythera-maths/research/`` are
the implementation. The PyPI wheel needs to contain those modules so the
package's facade modules (encoder.py, decoder.py, etc.) have something to
re-export from when the wheel is installed standalone (no monorepo
checkout). This emitter copies them verbatim into the package's
``_research/`` directory; facades import from there.

The relative imports inside the research modules
(``from .astronomical_cycles import …``) work unchanged after the copy
because the destination is also a Python package (we drop a stub
``__init__.py``).

The ``_research/`` directory is **codegen-managed**: every file here is
overwritten on each ``regenerate.py`` run. Do not edit by hand —
``test_data_freshness.py`` will fail the build if hand-edits drift from
the source.

Modules NOT copied:

- ``carrier_insertion_geometry.py``: research-only G-H7 evaluator that
  depends on figure / SVG generation; too heavy for the wheel and not
  exposed as a bridge method in v0.1.0. The G-H7 hypothesis row in
  the H-battery facade reads its frozen result from ``_data/`` instead.

All other research modules are copied; the wheel ships the full
implementation so consumers without the monorepo can drive the encoder
and re-run the H-battery.

Run::

    python codegen/emit_research_modules.py
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, List

from _paths import RESEARCH_ROOT

# Where the package's _research/ directory lives.
_RESEARCH_DST: Path = (
    Path(__file__).resolve().parents[1]
    / "python"
    / "antikythera_spectral"
    / "_research"
)

# Modules in research/ to copy. Curated; see module docstring.
_INCLUDED_MODULES: List[str] = [
    "__init__.py",
    "astronomical_cycles.py",
    "astronomical_ground_truth.py",
    "bit_alu.py",
    "bronze_planetary_encoder.py",
    "consolidated_tests.py",
    "cyclic_group_algebra.py",
    "dial_decoder.py",
    "encode_ant.py",
    "ephemeris_loader.py",
    "equant_encoder.py",
    "gear_database.py",
    "gear_noise_models.py",
    "gear_topology.py",
    "hellenistic_eclipses.py",
    "historical_cross_reference.py",
    "historical_periods.py",
    "manufacturing_tolerance.py",
    "packing_analysis.py",
    "paired_chain_search.py",
    "pareto_analysis.py",
    "pin_and_slot.py",
    "rational_approximation.py",
    "rendering.py",
    "selective_lock_search.py",
    "sky_driven_validation.py",
]


def _included_files() -> Iterable[Path]:
    src_root = RESEARCH_ROOT / "research"
    for name in _INCLUDED_MODULES:
        p = src_root / name
        if p.exists():
            yield p


def emit() -> List[Path]:
    """Copy curated research/ modules to _research/.

    Returns the list of destination paths written. Wipes any stale
    files in ``_research/`` before writing so the directory is a
    deterministic mirror of the curated module list.
    """
    if _RESEARCH_DST.exists():
        for child in _RESEARCH_DST.iterdir():
            if child.is_file():
                child.unlink()
            else:
                shutil.rmtree(child)
    _RESEARCH_DST.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []
    for src in _included_files():
        dst = _RESEARCH_DST / src.name
        # Read the source as bytes, normalise CRLF to LF, then write.
        # shutil.copy2 would preserve the source's line endings, which
        # vary per OS / per git autocrlf setting; the manifest's SHA-256
        # checks would then fail on CI runners with different settings.
        # (See .gitattributes for the corresponding git-side
        # normalisation.)
        raw = src.read_bytes().replace(b"\r\n", b"\n")
        dst.write_bytes(raw)
        written.append(dst)

    # Drop a README pointing at the SSOT.
    readme = _RESEARCH_DST / "README.md"
    readme_text = (
        "# antikythera-spectral _research/\n\n"
        "**Auto-generated. Do not edit.**\n\n"
        "These files are exact copies of selected modules from\n"
        "`docs/antikythera-maths/research/` (the SSOT). They ship in\n"
        "the wheel so that consumers who `pip install antikythera-spectral`\n"
        "without the monorepo can still drive the encoder.\n\n"
        "To refresh: run `python codegen/regenerate.py`.\n"
        "Drift between this directory and the SSOT is caught by\n"
        "`test_data_freshness.py`.\n"
    )
    readme.write_bytes(readme_text.encode("utf-8"))
    written.append(readme)

    return written


if __name__ == "__main__":
    paths = emit()
    print(f"copied {len(paths)} research modules into {_RESEARCH_DST}")
