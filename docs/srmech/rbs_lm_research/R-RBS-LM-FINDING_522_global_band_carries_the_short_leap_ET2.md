# R-RBS-LM Finding 522 (ET-2) — **the metric F518 needed: BFS path-EXISTENCE was blind to the global/coarse (RH) band's job, but path-LENGTH sees it — gating the GLOBAL band (the long-range bridges) keeps everything connected (756/756, no reachability loss, exactly as F518 found) yet LENGTHENS the mean leap +0.95 hops (2.23→3.18), while gating fine LOCAL detail loses some reachability (660/756) and lengthens less (+0.48). So the global band's real job is the SHORT distant LEAP (Beeman insight), not mere reachability — and "which band needs the second person" is TASK-relative: reachability → the local band (F518); insight / short-leap → the GLOBAL band (here). Both bands real, different jobs.**

**Date:** 2026-06-07
**Arc:** RBS-LM — ET-2 (leap-distance metric for the global band; the sharper test F518 left open)
**Provenance:** `R-RBS-LM-LEAP_global_band_carries_the_short_leap_ET2.py` (committed; srmech 0.7.4; reuses the F518 SUPERPOSITION build + band-gate; BFS shortest-path length). No sub-agents.
**Composes:** **F518** (refuted its prediction *because* BFS reachability was blind to the global band — *ET-2 supplies the path-LENGTH metric it called for, and the prediction HOLDS under it*) · **F514** (coarse/fine = the band split; Beeman RH coarse-coding = the distant leap) · **F515/F517** (the global hand / fiber-gating) · **F394** (a held-open lead now resolved). **← the global band carries the short leap; path-length is the right ruler.**
**→ path-length (not connectivity) reveals the global/coarse band's job: gating it keeps reachability intact but lengthens the leap (+0.95 hops) — the global bridges ARE the short distant leaps (insight); gating local detail loses reachability instead; "which band needs the 2nd person" is task-relative (reachability→local, insight→global).**

## Result
| gating | mean leap (hops) | connected | vs FULL |
|---|---:|---:|---:|
| FULL (no gate) | 2.23 | 756/756 | +0.00 |
| **GATE-LOCAL** (drop fine detail, keep bridges) | 2.70 | **660/756** | +0.48 |
| **GATE-GLOBAL** (drop bridges, keep clusters) | **3.18** | **756/756** | **+0.95** |

**Gating the GLOBAL band lengthens the leap most (+0.95) while losing no reachability** — the long-range bridges gave short, surprising jumps; without them you go the long way round. **Gating LOCAL detail loses reachability (660/756)** and lengthens less — consistent with F518 (local carries connectivity). So the two bands do **different jobs**: local = reachability (is there a path?), global = the **short leap** (is the path *short/surprising*? = insight).

## Falsifiable form (held open — F394)
- **Shown:** GATE-GLOBAL +0.95 hops at full connectivity; GATE-LOCAL +0.48 at 660/756 — path-length distinguishes the bands where connectivity (F518) could not.
- **Falsifier:** if gating the global band did NOT lengthen the leap, "global band = short leap" would be empty — it doesn't (it adds ~1 hop). If it had also dropped reachability, it wouldn't be a *pure* leap effect — it didn't (756/756).
- **Honest:** the +0.95 vs +0.48 gap is on a small (200-node) graph at q=0.25 — the *direction* (global→leap, local→reachability) is the result, magnitudes are parameter-dependent; "insight" is the framework reading of the short leap (Beeman), handed to the expert (F282), not measured cognition.
- **Scope:** framework build; srmech 0.7.4; Class-L eigen-basis; no abs(); no CAD; no sub-agents; held open (F394); favored not privileged (F398).

## Verdict
**ET-2 closed, and it resolves F518's open question.** F518 found gating the global band left reachability intact and concluded BFS was the wrong ruler. ET-2 supplies the right ruler — **path-length** — and the prediction now holds: gating the GLOBAL band **lengthens the leap +0.95 hops at full connectivity**, while gating LOCAL detail loses reachability instead. The global/coarse (RH) band's job is the **short distant leap** (Beeman insight), invisible to connectivity, visible to path-length. So "which band needs the second person" is **task-relative**: reachability → the local band (F518); insight / short-leap → the global band. Favored, not privileged (F398); held open (F394); structure for the expert (F282).
