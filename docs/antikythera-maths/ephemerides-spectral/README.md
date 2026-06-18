# ephemerides-spectral

High-precision HDC reference instrument for the Sol Star System, encoding
the live JPL DE441 ephemeris as resonant phases over a state-dependent graph
Laplacian.

> **Status:** v0.1.0 on PyPI ([`ephemerides-spectral`](https://pypi.org/project/ephemerides-spectral/)). Active development. v0.1.0 lands the 26-body Sol Star System Laplacian, the Phase 9 "breathing" couplings (formally a state-dependent / adaptive Kuramoto-family network — see [research notebook §1.4](../ephemerides_spectral_research_notebook.md#14-mathematical-positioning-of-the-breathing-laplacian)), the ALU-native BIP encoder (305× speedup, 256 KB state at D=65536, integer cosine LUT), and the FPU complex128 reference for the algebraic identities (observer binding, syzygy operator). See [`CHANGELOG.md`](CHANGELOG.md) for per-version detail and [`ROADMAP.md`](ROADMAP.md) for advertised-vs-shipped status.

## Subtree layout

| Path | What it is |
| --- | --- |
| [`python/`](python/) | The PyPI package source — `pip install ephemerides-spectral` builds from here |
| [`python/README.md`](python/README.md) | **PyPI long-description** (the page on `pypi.org/project/ephemerides-spectral/`) |
| [`codegen/`](codegen/) | Codegen scripts that emit `_data/manifest.json` and mirror `../research/*.py` into the wheel under `_research/` |
| [`bridge/`](bridge/) | Standalone bridges not part of the wheel (e.g. ephemeris-kernel staging) |
| [`ROADMAP.md`](ROADMAP.md) | Status of advertised CLI / bridge methods |
| [`CHANGELOG.md`](CHANGELOG.md) | Per-version change log |

## How this relates to `../research/`

[`docs/antikythera-maths/research/`](../research/) is the working research
scaffold: ~10 Python modules including `bodies.py` (26-body roster),
`laplacian.py` (the static + breathing Laplacian construction),
`bip_instrument.py` (ALU-native BIP encoder with integer cosine LUT),
`ephemeris_reference_instrument.py` (FPU complex128 reference), and
`ephemeris_loader.py` (skyfield kernel adapter). It is the **single source of
truth** for the celestial bodies table, the Laplacian topology, the Phase 9
breathing-coupling design, and the Q-format / overflow-discipline
documentation that lives next to the code that implements it.

The PyPI package is a **frozen snapshot** of those modules under
`python/ephemerides_spectral/_research/`. The codegen step computes per-file
SHA-256 sums and stamps them into `_data/manifest.json` so consumers can
verify which research-tree commit they're running.

## How this relates to `../antikythera-spectral/`

`antikythera-spectral` is the bronze-mechanism sibling project (ca. 150–60
BCE). The two share the spectral / cyclic-group framing and the
Pyodide-friendly bridge contract; they do not share data. See
[`../antikythera_spectral_research_notebook.md`](../antikythera_spectral_research_notebook.md)
§11.5 for the cross-reference and the design rationale for keeping the
projects separate ("the bronze and DE441 are separate evidentiary
objects").

The chess-spectral notebook §20.20 names the third leg of the cross-pollination:
chess uses `Z_{640}` (an explicit `% 640` per op); ephemerides uses
`Z_{2^32}` (free `uint32` overflow). Same algebraic family, different
moduli.

## Install

```bash
# Plain install (BIP integer ALU + complex128 reference encoder)
pip install ephemerides-spectral==0.1.0

# With JPL DE-kernel ephemeris support (skyfield + jplephem)
pip install "ephemerides-spectral[ephemeris]==0.1.0"
```

## CLI sketch

```bash
ephemerides-spectral --help
ephemerides-spectral version
ephemerides-spectral encode --jd 2451545.0
ephemerides-spectral adaptive --jd 2451545.0    # Phase 9 LUT inspector
                                                # (`breathing` is a hidden
                                                # synonym; same handler)
```

See the [PyPI README](python/README.md) for the full CLI cheat-sheet and
Python API reference.

## License

MIT. `ephemerides-spectral` and its runtime engine
[`srmech`](https://pypi.org/project/srmech/) are both MIT-licensed, so the
instrument is freely reusable. (The wider `mlehaptics` monorepo this package is
developed in remains GPL-3-or-later; this package carries its own MIT terms.)
