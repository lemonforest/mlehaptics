# F1285 — **the rcN-diff discipline, and the 72 sites that must NOT be renamed.** `rcdiff.py` makes a version bump a **two-way** event: what BROKE (rc288→rc299: **1 removed symbol, 190 files**) and what was **ADOPTED FROM HERE** (32 added — `CDRegister`, `cd_register`, `cd_navmap`, `cd_navigate`, `cd_navmap_is_signed_permutation`, all hand-built in F1275). **335 `klein4_random` calls renamed; 72 deliberately left alone** — renaming those would silently collapse experiments. And the general register is now confirmed **general across 7 rungs: 100 % round-trip at 4 → 256**.

## (1) The standing check — `rcdiff.py`, run after every rc bump
The branch forked at rc256 and didn't merge for 119 commits. Nothing *looked* broken, because it carried its own vendored copy of a surface `main` had deleted. **A version bump is two-way and neither direction was watched:**

- **REMOVED/RENAMED upstream** → our code silently breaks, and 96.6 % of the tree is print-only with no test, so mostly nothing runs to find out.
- **ADDED upstream** → often an op *we* prototyped here. Not noticing means maintaining a local copy of something now shipped and better-tested.

`rcdiff.py` introspects both interpreters' live surfaces and diffs them — **deliberately not CHANGELOG-based**, since a changelog is prose that can omit things while `dir()` cannot. Read the changelog for the *why*; let introspection decide the *what*. With `--scan`, each removed symbol gets an **AST call-site count**, so breakage arrives with a number attached.

**rc288 → rc299:**
| | |
|---|---|
| `CD_DIMS` | `(1…64)` → **`(1…256)`** |
| `CD_MAX_DIM` | 64 → **256** |
| **REMOVED** | `klein4_random` — **breaks 190 files** |
| **ADDED (32)** | incl. `CDRegister`, `cd_register`, `cd_navmap`, `cd_navigate`, `cd_navmap_is_signed_permutation` (+ native `_c` peers) |

**Those five added ops are the F1275 hand-rolled register, adopted upstream.** That is the "adopted from here" column doing its job on its first run.

## (2) The rename — and the 72 sites that must not be touched
An AST survey of every call shape *before* editing (the step I skipped on the previous migration, at cost):

| shape | count | action |
|---|---|---|
| `klein4_random(D, seed=X)` | 647 | **rename** → `klein4_expand(D, X)` |
| `klein4_random(D, rng)` | 133 | **DO NOT TOUCH** |
| `klein4_random(D, rng=...)` | 3 | **DO NOT TOUCH** |
| `klein4_random(SEED)` | 2 | **DO NOT TOUCH** |

**Why, verified rather than taken on faith** — #1454 warned of exactly this and it reproduces:

```
klein4_random(D, rng) x5, shared rng  -> 5 of 5 DISTINCT
klein4_expand(D, 42)  x5              -> 1 of 5 distinct
```

A shared stateful generator yields **N distinct** vectors; `klein4_expand(D, k)` yields **the same vector N times**. A mechanical rename would silently turn any similarity experiment into ≈1.0 — **a redesign, not a rename**, exactly as #1454 said. **335 calls renamed across 166 files; 72 left untouched across 25 files.**

Verification: **6/6 comparable probes byte-identical** across `HEAD@rc288` → `renamed@rc299`. Only the **pre-existing** `FINDING_943` parse failure remains.

## (3) Is the "general" register actually general? — now testable to 256
| rung | signed-permutation | `e₃·e₃` | round-trip (name + Class-C sign) |
|---|---|---|---|
| 4 ℍ | True | (0, −1) | **8/8 (100 %)** |
| 8 𝕆 | True | (0, −1) | **32/32 (100 %)** |
| 16 𝕊 | True | (0, −1) | **96/96 (100 %)** |
| 32 𝕋 | True | (0, −1) | **192/192 (100 %)** |
| **64** | True | (0, −1) | **192/192 (100 %)** |
| **128** | True | (0, −1) | **192/192 (100 %)** |
| **256** | True | (0, −1) | **192/192 (100 %)** |

**F1275 extends cleanly to 128 and 256.** Addressing is intact **seven rungs deep**, at dimensions where composition has long since failed — and the involution (`e₃·e₃ = −1`) holds at every one. The earlier 64 ceiling was, as F1275 stated, a **tooling bound and not a mathematical one**; raising it changed nothing about the result, which is what a correct structural claim should do.

## What this establishes as standing practice
**After every rc bump: run `rcdiff.py`, then read the CHANGELOG for the why.** Migrate every removed symbol *that has call sites* — **but survey the call shapes first**, because a symbol can be removed while its replacement has *different semantics for some callers*. 335 of 407 calls here were a safe rename and 72 were not, and only an AST survey told them apart.

Composes **#1454** (which predicted the rng trap; confirmed), **F1275** (extended to 256; its hand-rolled ops now adopted upstream), **F1284/F1283** (the migration-discipline lessons that produced the survey-first rule), `[[feedback_introspect_srmech_before_python_dispatch]]` (**now mechanised**).
