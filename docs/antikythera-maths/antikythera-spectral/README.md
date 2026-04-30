# antikythera-spectral

Hyperdimensional-computing encoder + Pyodide bridge for the Antikythera mechanism.

> **Status:** v0.1.0 in active development on the
> [`antikythera-spectral-pypi-plan`](https://github.com/lemonforest/mlehaptics/tree/antikythera-spectral-pypi-plan)
> branch. Not yet on PyPI. Plan document:
> [`../ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md`](../ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md).

## Subtree layout

| Path | What it is |
| --- | --- |
| [`python/`](python/) | The PyPI package source — `pip install antikythera-spectral` builds from here |
| [`python/README.md`](python/README.md) | **PyPI long-description** (the page on `pypi.org/project/antikythera-spectral/`) |
| [`codegen/`](codegen/) | Codegen scripts that emit `_data/*.json` and basis-vector NPZs from `../research/*.py` |
| [`bridge/`](bridge/) | Standalone bridges that aren't part of the wheel (e.g. URL → ephemeris-kernel downloader) |
| [`docs/`](docs/) | Bridge API contract, ADRs, ΔT discussion, calendar systems reference |
| [`ROADMAP.md`](ROADMAP.md) | Status of advertised CLI / bridge methods |
| [`CHANGELOG.md`](CHANGELOG.md) | Per-version change log |

## How this relates to `../research/`

[`docs/antikythera-maths/research/`](../research/) is the working research scaffold: 25
Python modules totalling ~6 200 LOC that encode the HDC framing of the
Antikythera mechanism. It is the **single source of truth** for cycles,
gears, eclipse anchors, period relations, the H-battery, and the
architectural-mode hypotheses.

`antikythera-spectral` is the *packaging* of that scaffold — it re-exports
the encoder/decoder/data via a Pyodide-friendly Bridge API, ships frozen
JSON snapshots of the research-scaffold data, and wraps everything in a
PyPI distribution so a web frontend can install it via `micropip` and
drive a digital Antikythera in-browser.

The codegen layer (`codegen/`) keeps the two in sync: every `_data/*.json`
file is regenerable from the `research/*.py` source, and
`test_data_freshness.py` fails the build if drift exists.

## See also

- The [research notebook](../antikythera_spectral_research_notebook.md) for the project narrative.
- The [hypothesis battery](../results/phase1_hypotheses.csv) (31 rows, current as of v0.2.0 of the research scaffold).
- The [planning document](../ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md) for v0.1.0 release scope and rollout strategy.
