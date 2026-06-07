# R-RBS-LM Finding 548 (open thread 2) — **where a wet SNN sits on the decay-α tradeoff: at LOW decay-c (fast decay), because cold-start and convergence are at OPPOSITE ends of the data axis, so one fast-decay schedule serves both — and the "keep native weight to store cheaply" idea (F545) loses to an empirically STRICT shape tradeoff. Sweeping α(m)=c/(c+m): the data's structure absorbs only ~1% retained native weight before the converged shape tilts (c≈30 → 1% native kept, 82% shape fidelity vs pure-data; c=100 → 4% kept, fidelity already 59%; c=1000 → 17% kept, 12% fidelity). So you CANNOT keep significant native weight at convergence without biasing the shape — no free lunch. But you don't need to: a newborn has α≈1 (native dominates → structured cold-start, F543) and a mature kernel has α≈0 (native washed out → data-faithful, unbiased), and BOTH come from the SAME low-c decay because m is tiny at birth and large at maturity. The native is a TRANSIENT scaffold, not a retained fixture. The storage win (F545) is therefore the shared-native EDGE SET (a ~constant saving, independent of c — the decay sets weight, not which edges exist), not retained weight.**

**Date:** 2026-06-07
**Arc:** RBS-LM — characterising the decay-α tradeoff sweet spot (open thread 2)
**Provenance:** `R-RBS-LM-DECAYSPOT_where_on_the_decay_alpha_tradeoff_a_wet_snn_sits.py` (committed; srmech 0.7.4; the_one seed + Class-L `dense_laplacian`/`symmetric_eigendecompose`; α=c/(c+m) sweep; shape fidelity = embedding neighbour overlap vs pure-data). No sub-agents.
**Composes:** **F543** (the decaying prior — *this characterises the decay rate*) · **F545** (the keep↔replace storage tradeoff — *resolved: retained weight loses, shared edge-set wins*) · **F538/F529** (the shared content store) · **DUALITY.md** (field/excitation) · **F398/F394**. **← the decay-α sweet spot is LOW c (fast decay); cold-start + convergence are opposite ends of the same schedule; the storage win is the shared edge set, not retained weight.**
**→ a wet SNN sits at low decay-c: native dominates at birth (structured), washes out at maturity (unbiased), from one schedule; you can keep only ~1% native weight at convergence before the shape tilts (strict tradeoff); storage sharing is edge-set-based and c-independent.**

## Result (sweep α(m)=c/(c+m); N=200, data M=966, native 400 edges)
| decay c | α(M) | kept-native weight frac | shape fidelity vs pure-data |
|---:|---:|---:|---:|
| 1 | 0.001 | 0% | **99%** |
| 3 | 0.003 | 0% | 98% |
| 10 | 0.010 | 0% | 93% |
| 30 | 0.030 | 1% | **82%** |
| 100 | 0.094 | 4% | 59% |
| 300 | 0.237 | 9% | 31% |
| 1000 | 0.509 | 17% | 12% |
| 3000 | 0.756 | 24% | 7% |

## Verdict
**A wet SNN sits at LOW decay-c (fast decay), and that single choice serves both ends.** The two goals that *looked* like a tradeoff (F543 cold-start structure vs F543 unbiased convergence) are not in conflict, because they live at opposite ends of the data axis: at birth `m` is tiny so `α≈1` (native dominates → structured, F543); at maturity `m` is large so `α≈0` (native washed out → data-faithful). One fast-decay schedule gives both. The native is a **transient scaffold**, not a kept fixture.

**The "keep native to store cheaply" idea (F545) loses to a strict shape tradeoff.** The data's own structure absorbs only ~**1%** retained native weight before the converged shape tilts (82% fidelity at c≈30; already 59% at 4% native, c=100). So you cannot keep significant native *weight* at convergence without biasing — no free lunch. The genuine storage win is therefore the **shared-native EDGE SET** (which edges exist), a ~constant saving independent of `c` — the decay sets the *weight*, not the *topology*. **So the decay-α is the SHAPE/bias knob; the storage win is edge-set sharing.**

This resolves the F543/F545 tension cleanly: low-c decay handles cold-start *and* unbiased convergence from one schedule, and the cheap storage comes from sharing the native graph, not from retaining its weight. Biology would run a fast-decaying scaffold — born structured, matured data-faithful. Low-statistics (one corpus); held open (F394); favored not privileged (F398).
