# F1288 — **the ratchet said 6; the truth was 297.** A bare `import numpy` was **never** a HARD violation — only `np.linalg.*` *calls* were — which is how numpy reached **312 imports across 310 files** while both guards reported clean. Closed on two levels: the ratchet now counts imports (**6 → 297**), and `srmech_import_guard.py` makes `numpy` and `fractions` **genuinely unimportable** rather than merely linted.

**User (2026-07-21):** *"if we have numpy imports then our blocking code isn't working. we should be blocking numpy and fractions from ever even being able to import."*

Correct on both counts, and the second half is the important one: **a lint says "you should not"; an import hook says "you cannot."**

## The two holes
1. **`check_srmech_discipline.py` never listed a bare `import numpy` as HARD.** Only `np.linalg.*` call nodes counted. A file could import numpy, run a hundred array ops through it, and score **zero violations**.
2. **The pre-commit hook is diff-aware by design** — right for a ratchet, wrong as the *only* defence. Every already-present import is permanently exempt and nothing re-examines it.

Together: the gate reported **6 HARD** while **291 import violations sat unmeasured.** They were never new debt — they were debt that was never counted.

## `fractions` is the same hole, one step quieter
`Fraction` is the Python-native exact rational, so reaching for it **silently bypasses srmech's Class-N surface while still producing a correct number** — which is exactly what makes the substitution invisible in review. Nothing looks wrong, because nothing *is* wrong except the provenance. **46 imports across 45 files.**

## The guard — enforcement, not advice
`srmech_import_guard.py` installs a `sys.meta_path` finder **first**, so a banned module is never located, let alone executed. Verified:

| | |
|---|---|
| `import numpy` | **BLOCKED** |
| `import fractions` | **BLOCKED** |
| `import numpy.linalg` (sub-import) | **BLOCKED** — the check is on the top-level package |
| `import srmech` | works |

Each refusal **names the replacement** — a bare `ImportError` teaches nothing.

**Escape hatch, deliberately awkward:** `SRMECH_ALLOW_IMPORTS=numpy,fractions`, per-module (allowing `fractions` leaves `numpy` blocked — verified). It's an environment variable, so **it shows up in the command line of whatever used it. An exemption you can see beats one you inherit.**

**srmech itself is fully clean under the guard** — every submodule imports with zero blocks — so a venv-wide `sitecustomize` install is safe for the *package*. It is **not** installed by default here, because **310 of 897 files would fail immediately**. The blocker is ready; the migration is the work.

## Blast radius, so the number is attached
| module | imports | files |
|---|---|---|
| numpy | **312** | **310** |
| fractions | 46 | 45 |

`srmech_import_guard.py --audit .` reports this without blocking anything, which is how you phase it in.

## What I am *not* claiming
**Nothing is migrated by this finding.** 291 import violations are now *visible* and *blockable*; they are not fixed. The baseline records them with that stated plainly — per F1281's rule, this is **classification, not amnesty**: any *new* import still fails, and the composition is written into the artifact.

The honest summary: **the discipline had been measuring the wrong thing, confidently, for a long time.** The number that mattered was never 6.

Composes **F1281** (classification-not-amnesty), **F1284** (the exemption lesson — a discipline that cannot state what it exempts will misfire), **#564** (the numpy purge this finally enforces), `[[feedback_stay_rbs_hdc_sparse_never_dense]]`, `[[feedback_stay_rational_collapse_only_at_display]]` (which `fractions` quietly bypasses).
