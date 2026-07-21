# F1290 — **numpy Tiers 1–2 landed: imports 312 → 258, files 310 → 256, HARD 297 → 253.** And Tier 3 is where the migration stops being mechanical: **numpy's `Generator` (PCG64) and Python's `Random` (Mersenne Twister) are different algorithms, so the same seed gives different numbers — all 320 RNG sites would CHANGE THEIR RESULTS.** That is a re-run of the experiments, not a rename.

## What landed
| tier | files | result |
|---|---|---|
| **1 — pure statistics** | 17 | migrated; 14 run numpy-free that could not before |
| **2 — carrier/array** | 38 | migrated; 29/30 sampled run numpy-free |
| **3 — RNG** | 0 of 184 | **blocked, see below** |

**Cumulative: 54 numpy imports removed, 54 files freed.** 21/21 helper vectors pass.

## The Tier-2 principle: srmech where srmech has the op, plain Python where it does not
srmech ships `mat_norm`, `elementwise_sqrt`, and the `Mat`/`Vec` carriers with `@`, `.T`, indexing — used for those. It ships no "array", because **for the 1-D numeric work these files actually do, a plain list IS the honest carrier.** Wrapping a list in a srmech type to look compliant would be the same error as calling `sum(x)/len(x)` a cascade of the 14. `zeros()` here **raises on a 2-D shape on purpose**, so a site needing real array semantics is forced to declare itself rather than silently getting a wrong-shaped list.

π is the exception in the other direction: `np.pi` → **`srmech`'s Class-N `pi_cascade_digits`**, because per CLAUDE.md **π is a cascade attested to its derivation, not a literal**.

## Why Tier 3 stops here — and the good news in it
320 RNG call sites, classified:

| regime | count |
|---|---|
| seed is an **expression** (`default_rng(SEED_OCT + off)`) | 187 |
| **literal** seed (`default_rng(297)`) | 133 |
| **no seed** — live rng | **0** |

**Zero unseeded calls.** Per F1259 a live rng inside a cascade is a defect; **the tree has none.** That is worth stating positively — the RNG debt is a *portability* problem, not a correctness one.

But the migration itself is blocked on something real: **`random.Random(297)` and `np.random.default_rng(297)` produce entirely different sequences** (Mersenne Twister vs PCG64). Every Tier-3 file would change its numbers, and those numbers are what the findings rest on. srmech ships no general-purpose numeric RNG to migrate onto either — `klein4_expand(D, seed)` is a deterministic *vector* expansion, not a float stream.

**So Tier 3 is a research decision, not an engineering one:** either accept that 184 files' results change and re-run them, or keep numpy for the RNG path. **I am not making that call unilaterally** — it invalidates lodged numbers across a large part of the corpus.

## Honest status
- **Not verified against live numpy.** It will not install on Python 3.14, so there is no differential test and no "before" run. Verification is hand-computed vectors against numpy's documented semantics, plus files now executing numpy-free that previously could not.
- **Transitive blocking persists.** A migrated file still fails if a module it imports has numpy. The unit is the **import graph**, not the file — 1 of 30 sampled Tier-2 files is still blocked this way.
- **255 files skipped in Tier 2** because they use unmapped ops (broadcasting, slicing, `ndarray` typing, `frombuffer`). Those need per-file reads, not a table.

Composes **F1289** (Tier 1), **F1288** (the guard whose allow-list shrinks as tiers land), **F1259** (the RNG regimes — and the finding that none is STOCHASTIC), **#564**.
