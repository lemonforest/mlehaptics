# F1289 — **the numpy migration is started.** Tier-1 (pure-statistics) migrated: **17 files converted, 14 now run numpy-free that could not before**; imports **312 → 296**, HARD **297 → 286**. The work is carried by one shared, tested helper — because the substitutions have a trap that would otherwise have been made 21 times: **`np.std` is the POPULATION statistic; `statistics.stdev` is the SAMPLE one, and swapping them changes every number without erroring.**

## The survey that set the plan
4033 numpy uses across **123 distinct attributes**; the top 12 cover 67 %. But **the migratable unit is the FILE, not the call** — removing numpy changes what a function's *inputs* are, so a file's usage has to go together. Classified by *hardest* usage:

| tier | files | what it needs |
|---|---|---|
| **1 — pure statistics** | **21** | plain Python; no carrier |
| 2 — carrier | 105 | srmech `Mat`/`Vec`/`HV` + Class-L ops |
| 3 — RNG | **184** | a per-site DERIVED / DRAWN / STOCHASTIC decision (F1259) |

**Tier 3 is the biggest and the one that cannot be mechanised** — `np.random` is 323 uses, and F1259 established that which regime a call is in is a *research* judgement, not a rename.

## `srmech_stats.py` — one place, with the traps written down
srmech has no `mean`/`argsort`/`std`/`median` (they are plain statistics, not cascade ops), so these are pure Python — and each carries the divergence that would otherwise bite:

- **`np.std` / `np.var` are POPULATION (ddof=0); `statistics.stdev`/`variance` are SAMPLE (ddof=1).** Demonstrated: `std([1,2,3,4])` = **1.118034** (numpy) vs `statistics.stdev` = **1.290994**. Substituting silently changes every number it touches.
- `np.argsort`'s default is **not stable**; `sorted` is — a difference that can only make ties *more* deterministic.
- `np.median` on even length **averages** the two middle values.
- `np.mean([])` returns nan-with-warning; this **raises** instead, because a silent nan is exactly what `cascade.magnitude` would later swallow to 0.0 (F1284).
- `np.allclose` uses the **asymmetric** `|a−b| ≤ atol + rtol·|b|` — note `|b|`, not `|a|`.

**13/13 hand-computed vectors pass.**

## The verification limit, stated rather than glossed
**numpy will not install on this interpreter (Python 3.14, no wheel), so there is no live numpy to differential-test against, and the "before" state of these files cannot be run at all.** Verification is therefore: hand-computed vectors against numpy's *documented* semantics, plus the fact that 14 files now execute numpy-free **which they previously could not**. That is weaker than a differential test and it is the strongest available here — recorded so nobody later reads "13/13 pass" as "diffed against numpy".

## Result
| | before | after |
|---|---|---|
| numpy imports | 312 | **296** |
| files importing numpy | 310 | **294** |
| HARD (ratchet) | 297 | **286** |

**3 of the 17 still fail** — not from their own import, but **transitively**, via a local module that still imports numpy (`R-RBS-LM-242b`, `rbs_lm_bytes.py`). Worth naming as a structural point: **file-by-file migration does not free a file until its dependencies are also free**, so the true unit is the *import graph*, not the file. Tier-2 will have to be ordered by dependency, not alphabetically.

## Next
1. **Tier 2 (105 files)** — needs a `np.array`/`zeros`/`dot`/`linalg.norm` → `Mat`/`Vec` mapping, and should be ordered by import-graph depth so leaves convert first.
2. **Tier 3 (184 files)** — per-site DERIVED / DRAWN / STOCHASTIC classification. **Not mechanisable**; each `np.random` call is a judgement about which regime it is in.
3. The guard's `SRMECH_ALLOW_IMPORTS` shrinks as tiers land, which is the non-regressing path to switching it on venv-wide.

Composes **F1288** (the guard + the ratchet hole this pays down), **F1259** (the RNG regimes Tier 3 needs), **F1284** (why a silent nan is the dangerous default), **#564** (the purge this enforces).
