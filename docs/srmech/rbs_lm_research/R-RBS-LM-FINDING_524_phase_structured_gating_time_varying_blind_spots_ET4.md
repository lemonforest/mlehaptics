# R-RBS-LM Finding 524 (ET-4) — **structured (rhythmic, theta/gamma-style) gating gives TIME-VARYING blind spots, unlike F517's uniform-random gate: modelling the projection as theta-phase-scheduled (trough = global/coarse band open, peak = local/fine band open), each single phase has a PARTIAL view (trough 87%, peak 100% reachability) and the gaps MOVE with phase — 13% of far pairs are reachable ONLY at the peak (local-open) phase, 0% only at the trough. Integrating over the FULL theta cycle recovers everything (100%). So with a rhythmic gate the self-mirror's blind spots are not fixed — they oscillate, and recovery requires integrating over a cycle (or waiting for the right phase). This refines F517's uniform-random gate into the structured theta/gamma schedule (F461): coarse/global on the slow theta, fine/local on the fast gamma, swept across the cycle.**

**Date:** 2026-06-07
**Arc:** RBS-LM — ET-4 (structured/phase non-uniform fiber-gate; theta/gamma)
**Provenance:** `R-RBS-LM-THETAGATE_phase_structured_gating_time_varying_blind_spots_ET4.py` (committed; srmech 0.7.4; reuses the F518 SUPERPOSITION band-gate as two theta phases; BFS reachability). No sub-agents.
**Composes:** **F517** (uniform-random fiber-gate — *ET-4 makes it STRUCTURED + rhythmic*) · **F518/F522** (the coarse/fine band split — *= the two theta phases; local carries reachability, global the short leap*) · **F461** (the theta/gamma k=7 consensus candidate — *the rhythmic schedule*) · **F514** (coarse/fine = the two hands) · **F394/F398/F282**. **← rhythmic gating → time-varying blind spots; full-cycle integration recovers.**
**→ a structured (theta/gamma) rhythmic gate gives TIME-VARYING blind spots (per-phase partial: 13% reachable only at the local-open peak, 0% only at the trough), and the full theta cycle recovers (100%); recovery needs integrating over a cycle, refining F517's uniform-random gate into the coarse-on-theta / fine-on-gamma schedule.**

## Result
| theta phase | band open | reachability |
|---|---|---:|
| **trough** | global / coarse (GATE-LOCAL: keep bridges) | 87% |
| **peak** | local / fine (GATE-GLOBAL: keep clusters) | 100% |
| **full cycle** | union of both phases | **100%** |

**Time-varying blind spots:** 13% of far pairs reachable **only at the peak** (local-open) phase, 0% only at the trough — the gaps **move with phase**. The peak (local band) reaches everything (consistent with F518/F522: local edges carry reachability); the trough (global band, local gated) misses 13%. **Integrating over the full theta cycle recovers everything.**

## The reading
A **rhythmic** gate means the self-mirror's blind spots are **not fixed** — they oscillate with the gate, so a given pair may be reachable at one phase and not another. Recovery requires **integrating over a cycle** (or waiting for the right phase). This is the theta/gamma nesting (F461): the slow **theta** sweeps the **coarse/global** band, the fast **gamma** the **fine/local** band; across the cycle both bands are visited. (With the ET-2 leap metric the asymmetry would flip — the trough/global phase gives the *short leaps* the peak/local phase lacks — so the cycle sweeps reachability *and* short-leap capability.) This refines F517's uniform-random gate into a structured schedule.

## Falsifiable form (held open — F394)
- **Shown:** per-phase reachability differs (87% vs 100%), 13% only-at-peak (time-varying), full-cycle 100%.
- **Falsifier:** if both phases reached the same pairs, "time-varying blind spots" would be empty — they don't (13% only-peak). If the full cycle didn't recover, integration wouldn't help — it does (100%).
- **Honest:** a 2-phase model of theta is **coarse** (real theta/gamma is continuous, nested, many gamma cycles per theta); the band-gate is the F518 spectral split; the asymmetry (peak=100%) follows F518/F522 (local carries reachability) — with the leap metric the phases would differ in leap-length instead. The **direction** (per-phase partial + time-varying gaps + full-cycle recovery) is the result, not the exact percentages. Theta/gamma is the framework reading (F461), handed to the expert (F282), not measured rhythms.
- **Scope:** framework build; srmech 0.7.4; Class-L eigen-basis; no abs(); no CAD; no sub-agents; held open (F394); favored not privileged (F398).

## Verdict
**ET-4 closed: structured rhythmic gating gives time-varying blind spots.** Modelling the fiber-gate as theta-phase-scheduled (trough = global band, peak = local band), each phase is partial (87% / 100%) and the gaps **move with phase** (13% reachable only at the peak), while the **full theta cycle recovers** (100%). So with a rhythmic gate the self-mirror's blind spots oscillate — recovery needs integrating over a cycle or waiting for the right phase — which is the theta/gamma schedule (F461): coarse/global on theta, fine/local on gamma. This refines F517's uniform-random gate into the structured biological one. Favored, not privileged (F398); held open (F394); structure for the expert (F282).
