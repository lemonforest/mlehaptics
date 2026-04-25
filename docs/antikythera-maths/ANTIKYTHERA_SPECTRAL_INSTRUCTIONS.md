# Antikythera-Maths — Picking up the project in a new Claude session

**Sibling to** [../othello-maths/OTHELLO_SPECTRAL_INSTRUCTIONS.md](../othello-maths/OTHELLO_SPECTRAL_INSTRUCTIONS.md), with which it shares the cognitive style and methodological discipline.

---

## What this is

The Antikythera mechanism (Greek, ca. 150–60 BCE) is a physical instantiation of coprime-indexed phase-space addressing, designed deliberately 2100 years ago to solve the Diophantine approximation problems that [docs/addressing-maths/ADDRESSING_MATHS_RESEARCH_PLAN.md](../addressing-maths/ADDRESSING_MATHS_RESEARCH_PLAN.md) characterises formally. This project documents the artifact in addressing-maths vocabulary.

The encoding is **descriptive**, not **prescriptive**. The math is in the bronze; we read it off, we don't invent it. This is the first project in the mlehaptics triad-plus where the structure was *designed in* by named historical agents (plausibly in the Archimedean tradition).

---

## Steven's cognitive style

(Mostly inherited from the Othello / chess threads. Restated here so the doc stands alone.)

- **Both/and discipline.** When a design choice has multiple defensible options, implement them all where feasible. The encoder has three D variants (940, 13440, LCM-symbolic) for this reason; the gear database tabulates Freeth 2021, Wright, and Price 1974 wherever they disagree.
- **Honest tags.** Every claim in the notebook carries one of `KNOWN | NOVEL | CONFIRMED | FAILED | DISPUTED`. Don't write a sentence without thinking about which tag it earns.
- **No silent overclaiming.** The Greeks did not "invent HDC." They invented a specific geared astronomical calculator. The HDC recognition is *our* framing, valid as a description but not as an anachronistic attribution.
- **Don't conflate design with implementation.** The Guillermo & Szigety 2025 manufacturing-tolerance result is real — clean design at the gear-ratio layer does not guarantee smooth running at the bronze-cutting layer. C-H1's "zero error correction" is the theoretical reason this matters.
- **Keep rendering out of encoding.** Patch 3 of the build prompt is load-bearing: `encode_Ant(t)` returns angular state only; radial parameters and (x, y) coordinates live in [research/rendering.py](research/rendering.py). The dial calculator and the orrery are sibling renderings of the same parent state; perspective is the scale invariance.

---

## Discovery vs description

Chess, Othello, logo were *discovery* projects: structure was present and we used spectral tools to extract it. Antikythera is *reconstructive*: structure was designed in, and the job is to document it in modern vocabulary. This shifts the honest-science tags:

- **KNOWN** — published in archaeology / history (Price 1974, Freeth et al. 2006/2008/2021, Wright 2005-2012, Guillermo & Szigety 2025).
- **NOVEL** — the HDC / phase-space framing itself, naming a property of the mechanism in addressing-maths vocabulary that the archaeology literature has not used.
- **CONFIRMED** — computationally verified that the mechanism-as-HDC-object reproduces what the bronze does.
- **FAILED** — our HDC encoding cannot reproduce something the physical mechanism does (E-H2 Mars retrograde is the canonical example).
- **DISPUTED** — archaeological reconstructions disagree (b1 tooth count 224 vs 223, Archimedes attribution, etc.).

---

## File organisation

```
docs/antikythera-maths/
├── ANTIKYTHERA_SPECTRAL_BUILD_PROMPT.md   ← the original build prompt, with patches consolidated
├── ANTIKYTHERA_SPECTRAL_INSTRUCTIONS.md   ← THIS FILE
├── ANTIKYTHERA_PHASE_OP_PREFLIGHT.md      ← short Phase 3 handoff
├── SESSION_HANDOFF.md                     ← interrupted-session notes (April 2026)
├── antikythera_spectral_research_notebook.md  ← the main research narrative
├── research/
│   ├── __init__.py
│   ├── gear_database.py         ← 40 gears, 3 reconstructions, provenance
│   ├── astronomical_cycles.py   ← 13 cycles, prime factorisations
│   ├── cyclic_group_algebra.py  ← CRT tables, roll operators, gear-mesh ratios
│   ├── rational_approximation.py ← CF expansion, semi-convergents, best-under-budget
│   ├── packing_analysis.py      ← prime spectrum, Pareto frontier, CF-rank report
│   ├── pin_and_slot.py          ← Fragment B epicycle, T-breaking decomposition (D-H1)
│   ├── encode_ant.py            ← THREE D-variant resonant HDC encoder + DialSpec + sigma_day
│   ├── dial_decoder.py          ← FFT-based circular-correlation unbinding
│   ├── rendering.py             ← Patch-3 dial + orrery projections
│   ├── astronomical_ground_truth.py  ← skyfield DE421 (E-H1, E-H2)
│   └── consolidated_tests.py    ← H-battery runner, writes results/*
├── results/
│   ├── phase1_hypotheses.csv    ← runtime status per hypothesis
│   ├── phase1_detail.json       ← per-hypothesis numeric detail
│   └── session_summary.md       ← ~1-page narrative summary
├── figures/                     ← (empty; for future plots)
└── skyfield_data/               ← (gitignored; on-demand de421.bsp cache)
```

---

## How to run

**Run from `docs/antikythera-maths/`** (NOT from the repo root). The research modules use relative imports (`from .astronomical_cycles import ...`) so they must be invoked as packages:

```bash
cd docs/antikythera-maths
PYTHONIOENCODING=utf-8 python3 -m research.consolidated_tests
```

Bare `python3 research/consolidated_tests.py` will fail with `ImportError: attempted relative import with no known parent package`.

`PYTHONIOENCODING=utf-8` is needed on Windows because the default cp1252 console can't print the Greek letters in the smoke-test output (ε, σ, θ, etc.).

Per-module smoke tests:

```bash
PYTHONIOENCODING=utf-8 python3 -m research.gear_database
PYTHONIOENCODING=utf-8 python3 -m research.astronomical_cycles
PYTHONIOENCODING=utf-8 python3 -m research.cyclic_group_algebra
PYTHONIOENCODING=utf-8 python3 -m research.rational_approximation
PYTHONIOENCODING=utf-8 python3 -m research.packing_analysis
PYTHONIOENCODING=utf-8 python3 -m research.pin_and_slot
PYTHONIOENCODING=utf-8 python3 -m research.encode_ant
PYTHONIOENCODING=utf-8 python3 -m research.dial_decoder
PYTHONIOENCODING=utf-8 python3 -m research.rendering
PYTHONIOENCODING=utf-8 python3 -m research.astronomical_ground_truth
```

Dependencies: `numpy`, `scipy`, `sympy`, `skyfield`. Install with:

```bash
python3 -m pip install --user numpy scipy sympy skyfield
```

---

## Common pitfalls

1. **Relative imports** — see "How to run." Always `python3 -m research.<module>`.

2. **Tasks-pane false-running bug** (April 2026 cloud sandbox) — Bash calls sometimes appear "Running" indefinitely in the pane even after they've completed. Workaround: redirect output to a file (`python3 -m research.X > /tmp/x.log 2>&1`) and `Read` the log. This decouples from whatever the pane is tracking.

3. **skyfield ephemeris coverage** — DE421 covers 1900-01-01 through 2050-01-01 only. Hellenistic-era validation (200 BCE – 100 CE) requires DE422 (~600 MB) or DE441 (~3 GB). E-H1 is currently anchored at 1999-08-11 (modern total solar eclipse) for the Saros-period test; absolute Hellenistic placement is a follow-up.

4. **Mars `modern_days` is deliberate** — `astronomical_cycles.py` uses `125 × MARS_SYNODIC_DAYS` (not tropical years) for the Mars cycle's `modern_days` because the Greek Mars theory has no clean "years" denominator. The 6239-day residual is what D-H1 / E-H2 are characterising, not a bug.

5. **Freeth-only planetary gears** — gears 289 (Venus), 462 (Venus), 427 (Saturn), 442 (Saturn), 133 (Mars), 125 (Mars) are not physically attested. Freeth 2021 derives them from the proposed period relations. Filter `Gear.fragment is not None` to get only attested counts.

6. **Encoder D=940 planetary support** — `encode_ant_callippic` raises `UnsupportedDialError` if you ask for any planetary dial. This is intentional — D=940 is the "calendar-only honest" variant. Use D=13440 for the all-thirteen-dial encoding.

7. **σ_day is a roll, not a per-cycle rate** — `sigma_day(D) = roll_operator(D, 1)` is a single unitary on ℂ[ℤ/Dℤ]. It does NOT advance each dial by its physical daily rate; that's `advance_day(date, D, days=1)` which re-encodes for the new date. The build prompt's "one operator, many projections" framing is honoured by the trivial roll (the operator) and the per-dial decoder gear ratios (the many projections).

8. **CHANGELOG and branch workflow** — per [CLAUDE.md](../../CLAUDE.md), no direct commits to main. Stay on the active branch; update CHANGELOG.md under `[Unreleased] → Added` before opening the PR.

---

## Key references

- Freeth, T., et al. (2021). *A Model of the Cosmos in the ancient Greek Antikythera Mechanism.* Scientific Reports 11:5821. — current authoritative reconstruction.
- Freeth, T., Jones, A., Steele, J. M., & Bitsakis, Y. (2008). *Calendars with Olympiad display and eclipse prediction on the Antikythera Mechanism.* Nature 454:614.
- Freeth, T., et al. (2006). *Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism.* Nature 444:587. — Fragment B pin-and-slot geometry.
- de Solla Price, D. (1974). *Gears from the Greeks.* Trans. American Philosophical Society 64(7). — foundational, superseded on specific tooth counts.
- Wright, M. T. (2005-2012). Multiple papers on the alternative reconstruction.
- Guillermo, R. & Szigety, S. (2025, arXiv). Manufacturing-tolerance simulation suggesting the mechanism may not have run smoothly.
- Cicero, *De re publica* and *Tusculan Disputations*. — Archimedean planetarium tradition (DISPUTED attribution).

---

## What this project is NOT

- Not a claim that the Greeks "invented HDC." They invented a geared astronomical calculator. The HDC framing is ours.
- Not a hardware reconstruction. Deliverable is computational/descriptive.
- Not a commitment to one reconstruction as ground truth. Where Freeth, Wright, Price disagree, all are documented.
- Not a replacement for the archaeology literature. We cite and build on it; we do not supplant it.
- Not a commitment to the Archimedes attribution. Tag DISPUTED, stay DISPUTED.
