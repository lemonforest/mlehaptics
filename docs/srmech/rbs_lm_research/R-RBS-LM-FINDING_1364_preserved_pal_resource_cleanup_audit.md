# F1364 — **preserved: the PAL resource-cleanup audit (`#T1129`) — the C platform layer tracks no handles; Python has 5 HIGH mkdir-before-validate sites; C avoids that shape only by never creating the directory; one narrower hazard is shared by `recursive_cut` and `rcut_setup`**

Consolidation record (2026-09-14). Source: local branch `research-pal-cleanup`, two commits on no remote (2026-08-14). All three paths were absent here and the scanner does not use numpy, so both commits were cherry-picked with `-x`.

## What the audit found (its own words and figures)

**Setup:** *"READ-ONLY code archaeology. Nothing in `docs/srmech/{python,c}` was edited."* The branch came off `origin/main` at `a3f9fc847` (srmech v0.9.0rc430); every measurement ran under WSL2 with numpy absent. **Seed defect:** `genome_save` does `path.mkdir(parents=True, exist_ok=True)` *"as its FIRST executable line"*, before validation steps that can raise.

- **Q1 — the C PAL.** `srmech_platform.{c,h}` exists and is the only place with OS `#ifdef`s. *"No open-handle table, no created-node registry, no cleanup list exists anywhere in the PAL."* Asked whether a caller can check "is everything this call opened now closed?", it answers *"Measured: NO."*
- **Q2 — `goto`.** Rule 1 violations: 0. The replacement idiom is an early return with the release inlined on the guard line. Held-handle open sites: 5, with *"0 unsafe early returns"*. Does `test_jpl_audit.py` check acquire/release symmetry? *"Measured: NO … an UNGATED axis."*
- **Q3 — dual projection.** For `genome_save`: *"DISAGREEMENT, and it is the finding."* Python creates the directory before validation. C never calls `srmech_plat_mkdir` in `srmech_genome.c` — 0 calls across all 10 genome C write entry points — and relies on a pre-existing directory, which its own test harness creates before every call. The one shared hazard is `recursive_cut` (Python) / `rcut_setup` (C): three sequential creates with no rollback.
- **Q4 — class size.** Python: 264 files, 4,756 functions, 31 raw scanner hits, triaged to **HIGH 5** (`genome_save:8980`, `genome_import:11600`, `genome_explode:11680`, `genome_register_attested:11927`, `pack_mcpb:318`), **MEDIUM 3**, **LOW / benign 3 sites** and **REFUTED 4** (that row names five sites). C: 3 `srmech_plat_mkdir` call sites, all in `rcut_setup`. Both scanners carry planted positive and negative controls, and the controls caught three bugs in the C scanner's first version before anything was reported.
- **Q5 — gate-ability.** Python is *"NOT directly gate-able as a zero-false-positive ratchet"*; a bounded structural ratchet with a maintained allowlist is possible. For C, *"C-side IS realistically gate-able"* as an acquire/release-symmetry rule in `test_jpl_audit.py`, excluding constructor-shaped listen handles.
- **Ranked areas to look at first:** `genome_save`; the `genome_import` native branch; `genome_explode` and `genome_register_attested`; `pack_mcpb`; `rcut_setup` / `recursive_cut`; the C genome surface's missing mkdir (a maintainer decision about the contract); and a C acquire/release ratchet.

**Figures as printed, not reconciled here.** The second commit's message says it *"Appends 14 manual-triage verdicts … (5 HIGH-confirmed, 3 MEDIUM-confirmed-narrower, 3 LOW/benign, 4 REFUTED scanner false positives)"*; those four categories sum to 15. The report's file index lists *"14 `manual_triage`"* records.

## Where it lives on PR #687

- Cherry-picked with `-x` (two commits): `docs/srmech/notes/_pal_resource_cleanup_audit.py`, `_pal_resource_cleanup_audit.ndjson` and `_pal_resource_cleanup_audit.md`.
- Archive: `preserved_branches/research-pal-cleanup/`.
- The audit's file:line references are to srmech v0.9.0rc430 on `main`.

## DIFFERS

None.

Branch safe to delete once this commit is on origin: yes

Integrated 2026-09-14: see F1373.
