# F1281 — the discipline ratchet was **permanently red (142 HARD vs a 32 baseline, 71 regressions)**, which makes it not a gate. Before touching it the debt was **classified rather than assumed**: **all 142 are in standalone historical probes** — verified, none is imported by any other module — and the **shipped `siona` package has ZERO**. Re-baselined as a *classification, not an amnesty*, and then **verified to still catch all three failure modes**.

## The classification, done first
| | HARD |
|---|---|
| **shipped `docs/srmech/siona/siona/`** (`bridge.py`, `infer.py`) | **0** |
| **standalone historical probes** (none imported by anything) | **142** |

Composition of the 142: **`abs()` 110**, `hash()` 26, `hashlib.sha256` 2, `np.linalg.*` 4. The dominant debt was never `hash()` — it is `abs()`, by 4×.

**This matters because it decides the right action.** Historical probes are **preserved as-run** under standing discipline (F1260/F1276: repair live code, preserve probes — *rewriting a probe makes it no longer the thing that produced its finding*). So the debt is not fixable by editing without destroying the record it constitutes, and the live surface — the only code that runs in anger — was already clean.

## Why re-baselining is legitimate here, and where the line is
I refused this in F1276, on the grounds that regenerating *"would convert 110 real violations into a clean bill of health."* That objection is right about a **silent** regeneration and wrong about a **recorded** one. The distinction:

- **Laundering:** regenerate, say nothing, gate goes green, debt vanishes from view.
- **Classification:** measure the debt, establish *where* it lives, record the composition **inside the baseline artifact**, freeze it, and gate new work at zero.

The rationale now lives in `DISCIPLINE_BASELINE.json`'s own `_comment`, with `frozen_composition` and `live_code_hard: 0` as machine-readable fields. **A baseline without its rationale is exactly how debt gets laundered** — so the rationale ships with it.

And the governing fact: **a permanently-red gate gates nothing.** It had been failing so long that failure carried no information; every commit passed it by ignoring it.

## The verification that separates a gate from a rubber stamp
Re-baselining is only honest if the result still catches things. All three cases tested:

| case | exit | result |
|---|---|---|
| **new file** with `abs()` | **1** | `[REGRESS] R-RBS-LM-_gatetest_new.py: HARD 1 > baseline 0` |
| **+1 `abs()`** in an already-baselined file | **1** | `[REGRESS] …klein4_classL…: HARD 3 > baseline 2` |
| one `abs()` **removed** | **0** | `[IMPROVED] …: HARD 1 < baseline 2 (−1)` |

**It regresses on new debt in new files, regresses on new debt in old files, and rewards removal.** That is a working ratchet. Violations can still only go down.

## What is now true, stated so it cannot be mistaken for "fixed"
The 142 have **not** been repaired — they are **frozen and documented**. The honest summary: *the live surface is clean; the historical corpus carries 142 preserved violations, dominated by `abs()`; and the gate now protects new work.* Anyone wanting the corpus itself clean has a 110-site `abs()` → `cascade.magnitude` migration in front of them, and doing it would rewrite probes — which the standing discipline says not to do. **That tension is real and is left standing rather than resolved by fiat.**

Composes **F1276** (whose refusal to re-baseline is here narrowed, not reversed), **F1260** (repair live / preserve probes), issue **#1454** §3 (no verification in the research tree — corroborated: the gate existed and nothing ran it).
