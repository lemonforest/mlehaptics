# antikythera-spectral

Hyperdimensional-computing encoder + Pyodide bridge for the Antikythera mechanism.

> **Status:** v0.3.0 on PyPI ([`antikythera-spectral`](https://pypi.org/project/antikythera-spectral/)). Active development. v0.3.0 lands the `mars_models` facade (bronze projection + Freeth-reconstruction param sets, ADR 0012) and the `bit_alu` facade (bit-packed binary HDC ALU; the new package default, with `backend="complex128"` available as v0.2.x opt-out). See [`CHANGELOG.md`](CHANGELOG.md) for per-version detail and [`../ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md`](../ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md) for the original v0.1.0 release plan.

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
- The [hypothesis battery](../results/phase1_hypotheses.csv) (31 rows; the v0.3.0 research-scaffold rows include the Mars 38° gap audit decomposition — see [`figures/mars_38deg_gap_findings.md`](../figures/mars_38deg_gap_findings.md)).
- The [bit-ALU benchmark + cycle-alignment investigation](../figures/bit_alu_findings.md) (v0.3.0).
- The [planning document](../ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md) for v0.1.0 release scope (preserved as historical context; v0.2.0 / v0.3.0 deliverables tracked in [`CHANGELOG.md`](CHANGELOG.md) and [`ROADMAP.md`](ROADMAP.md)).
