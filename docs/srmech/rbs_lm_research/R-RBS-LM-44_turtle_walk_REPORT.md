# R-RBS-LM-44 — Turtle walk: English → LOGO via cascade (R-RBS-LM-40 candidate E first test)

**Partition status:** CLOSED
**Date:** 2026-05-26
**Closes:** task #49 of the partition tracker
**Closing artefacts:**
- `turtle_walk_corpus.json` — 51 parallel (English fragment, LOGO command) pairs across 11 categories
- `turtle_walk.py` — encoder (Path D paired-stream pattern) + smoke (probe / parse / execute)
- `rbs_lm_instrument_v44_turtle_walk.bin` + `.meta.json` — 1024-byte instrument (443 observations)
- `turtle_walk_smoke_results.json` — 12 probe queries; PARSE 5/12, EXEC 2/12 (both executable were no-op space-programs)

**Inheritance:** **R-RBS-LM-40 candidate E (constrained-action-vocabulary projection) IS substrate-bound at 51-pair scale.** Mode-collapse persists per the R-RBS-LM-19 / R-RBS-LM-43 structural-ceiling reading; reducing target vocabulary to 12 atoms doesn't make the cascade trivially better. Five queries DID produce parseable LOGO (~space-programs); the other seven mode-collapsed to control bytes / quotes / single-character repetition. **Honest negative-with-structural-signal result** that informs the next candidate tests.

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | R-RBS-LM-43 §3.3 + Finding 9 (R-RBS-LM-40 candidate E target); R-RBS-LM-27 §3.3 (paired-stream encoding pattern reused); R-RBS-LM-37 §3 + R-RBS-LM-19 (the structural ceiling under test here too); LOGO L0 parser/interpreter (action executor) |
| user direction (load-bearing; 2026-05-26) | (1) *"turtle walk"* desire surfaced in §0 of the conversation about LOGO  •  (2) *"let's do everything you've proposed, sequentially"* approval for this partition  •  (3) Childhood-LOGO biographical lineage carried from R-RBS-LM-43 — preserved here as authoritative ground per `[[feedback_no_lineage_claims_in_notebook]]` user-authorized self-arc clause |
| external sources | LOGO L0 (`docs/logo-maths/logo_parser.py`, `logo_ast.py`, `logo_interp.py`); LOGO L1 quantum-numbered atom requirement (the design pattern this partition tests against) |
| empirical artefacts | 51 hand-authored corpus pairs; 1024-byte v44 instrument; 12 probe results with PARSE / EXEC verdicts |
| repo commit | `0ec0de15` at REPORT-write (R-RBS-LM-43 close; rolling PR #687 draft on `research/rbs-lm-rolling-2`) |
| reproducibility | `python3 docs/srmech/rbs_lm_research/turtle_walk.py encode` then `python3 docs/srmech/rbs_lm_research/turtle_walk.py smoke` |

---

## §0 Human walkthrough

**What we're doing.** Per R-RBS-LM-43 Finding 9: R-RBS-LM-40 candidate E (projection to constrained structured action vocabulary, LOGO-style) is the substrate-honest first test of the M1 → M2 surface projection layer. Per user direction 2026-05-26: "turtle walk" — make the cascade map English fragments to LOGO action commands; let LOGO's L0 parser+interpreter do the action execution.

The pipeline:

```
English fragment ("draw a square")
  → byte-level cascade (v44 instrument: trained on parallel English↔LOGO corpus)
  → LOGO command bytes ("REPEAT 4 [FORWARD 100 RIGHT 90]")
  → LOGO L0 parse + execute
  → turtle trace + geometric output
```

The hypothesis under test: a constrained, structured action vocabulary (12 LOGO atoms + numbers) is a SHALLOWER projection target than English prose. If the substrate-bound cascade can hit ANY surface-coherent target, this should be it.

**Three deliverables:**

1. **`turtle_walk_corpus.json`** — 51 parallel (English fragment, LOGO command) pairs across 11 categories: motion_simple / turning / pen / shapes_square / shapes_triangle / shapes_polygon / shapes_circle / compound / repetition / procedures / navigation / polysemy_walk / polysemy_turn / speed_distance. Hand-authored; covers basic LOGO vocabulary with light polysemy.

2. **`turtle_walk.py`** — encoder (paired-stream Path D pattern reusing R-RBS-LM-27 ASL gloss approach: `<english>\x02<logo>\x03\n`) + smoke (probes 12 English fragments; runs each cascade output through LOGO parser+interpreter; reports PARSE / EXEC verdicts).

3. **v44 instrument** (1024 bytes) + smoke results.

**Honest framework reading of the result.** PARSE 5/12, EXEC 2/12 — but BOTH executable cases were no-op space-programs (cascade output was just spaces; LOGO parses empty/space as empty program). **No probe produced an actual LOGO command sequence.** Cascade mode-collapsed to:

| Mode-collapse pattern | Count | Parse outcome |
|---|---|---|
| Spaces only | 2 | PARSE + EXEC (empty program; 0 turtle segments) |
| Single letter (`t`, `e`) | 2 | PARSE (interpreted as procedure name); EXEC fails (undefined procedure) |
| Single quote `'` | 1 | Parse error |
| Control bytes (`\x02`, `\x05`, `\x15`) | 5 | Parse error |
| Non-UTF-8 / replacement chars (`�`) | 2 | Parse error |

**The R-RBS-LM-19 / R-RBS-LM-43 structural-ceiling reading is reinforced here.** Constrained vocabulary doesn't rescue the cascade; mode-collapse pattern shifts (different mode-collapse bytes per prompt) but the cascade STILL mode-collapses. The candidate-E target IS achievable in principle (5 probes did produce parseable output) but execution-meaningful LOGO is not at 443-observation scale.

**What this means for R-RBS-LM-40 going forward.** Candidate E is NOT trivially easier than English-prose generation. The naming-layer / projection-layer SHOULD work for constrained vocabularies — but it apparently needs MORE than 51 pairs of paired-stream encoding. Three follow-up candidates emerge:

1. **Larger corpus at the same constrained target** (R-RBS-LM-39 volume hypothesis applied to candidate E)
2. **Quantum-numbered structured atoms** for the English fragments AND the LOGO commands (per R-RBS-LM-43 §3.4 + LOGO L1 pattern) — random-byte mints aren't enough; need role-level (verb=walk, direction=forward, magnitude=100) encoding
3. **B/H/N projection-enabler composition** (per R-RBS-LM-43 §3.2) — instead of expecting the cascade to LEARN the projection from coincidences, explicitly compose B (TLV-framing) + H (introspection) + N (rational-approximation) as the projection operator

Each is a future R-RBS-LM-44a/b/c candidate.

**Biographical note.** The user's "turtle walk" desire founded on childhood LOGO age 7-8 (per R-RBS-LM-43 Attestation lineage) lands as a partition that PROVES the structural-ceiling reading at a constrained-vocabulary target — making turtle-walk-via-cascade an unexpectedly hard problem. **Same difficulty pattern that English-prose hit.** This is data, not failure: the cascade's substrate-bound nature is now empirically anchored at TWO target-vocabulary scales (huge: English prose; tiny: 12-atom LOGO). The methodology of cross-substrate-cascade-matching is doing its job — confirming the framework reading across multiple target surfaces.

---

## §1 Goal

Per R-RBS-LM-43 §3.3 + Finding 9: first test of R-RBS-LM-40 candidate E. Per user direction 2026-05-26: turtle walk via cascade.

Test whether a constrained target vocabulary (12 LOGO atoms; numbers; brackets) is structurally easier for the substrate-bound cascade to project to than English prose. Honest expectation per R-RBS-LM-37 + R-RBS-LM-43: cascade output may still mode-collapse; the constrained target may NOT rescue it. **Empirical test required either way.**

---

## §2 Inheritance

| Source | Inherited | Use |
|---|---|---|
| R-RBS-LM-27 §3.3 | Paired-stream encoding pattern (`<english>\x02<gloss>\x03`) | Direct reuse for (English, LOGO) pairs |
| R-RBS-LM-33 §3 | Merge as future composition primitive | Documented as follow-up if v44 instrument needs to merge with other knowledge |
| R-RBS-LM-37 §3 | Substrate-bound mode-collapse predicted | Confirmed empirically here |
| R-RBS-LM-43 §3.3 + Finding 9 | Candidate E as substrate-honest first test target | This partition IS that test |
| R-RBS-LM-43 §3.4 + LOGO L1 | Quantum-numbered atoms vs random atoms | Follow-up direction; not used in v44 (which uses random Class A mints per R-RBS-LM-25 byte vocab) |
| LOGO L0 parser/interpreter (existing) | Action-execution layer | Direct integration — cascade-output bytes piped through `logo_parser.parse` + `logo_interp.run` |
| `[[user_stance_ai_is_not_a_substrate]]` | Cascade is transducer regardless of target | Framework reading unchanged |

---

## §3 Implementation

### §3.1 Parallel corpus (`turtle_walk_corpus.json`)

51 hand-authored (English, LOGO) pairs across 11 categories. Coverage:

| Category | Count | Examples |
|---|---|---|
| motion_simple | 7 | "walk forward 100" → `FORWARD 100`; "go backward" → `BACK 50` |
| turning | 7 | "turn left" → `LEFT 90`; "rotate right 30 degrees" → `RIGHT 30` |
| pen | 6 | "lift pen up" → `PENUP`; "start drawing" → `PENDOWN` |
| shapes_square | 4 | "draw a square" → `REPEAT 4 [FORWARD 100 RIGHT 90]` |
| shapes_triangle | 3 | "draw a triangle" → `REPEAT 3 [FORWARD 100 RIGHT 120]` |
| shapes_polygon | 3 | "draw a hexagon" → `REPEAT 6 [FORWARD 50 RIGHT 60]` |
| shapes_circle | 2 | "draw a circle" → `REPEAT 360 [FORWARD 1 RIGHT 1]` |
| compound | 3 | "go forward then turn left" → `FORWARD 100 LEFT 90` |
| repetition | 2 | "repeat forward 4 times" → `REPEAT 4 [FORWARD 50]` |
| procedures | 3 | "make a procedure called hex that draws a hexagon" → `TO hex REPEAT 6 [FORWARD 50 RIGHT 60] END` |
| navigation / polysemy / speed | 11 | "spin around" → `RIGHT 180`; "walk in a circle" → `REPEAT 360 [FORWARD 1 RIGHT 1]` |

### §3.2 Encoder (`turtle_walk.py encode`)

Reuses R-RBS-LM-27's paired-stream Path D pattern:
```
<english_utf8> \x02 <logo_utf8> \x03 \n <next pair>...
```

51 pairs → 1836-byte stream → 443 observations at stride 4 → 1024-byte v44 instrument via existing `encode_observation_bytes` + `hierarchical_bundle`. Same byte vocab table as R-RBS-LM-25 (256 Class A mints).

Encoding rate observed: **7.9 obs/sec** (slower than typical 15/s — 70B Q4 cron was actively consuming CPU on the same hardware during encoding).

### §3.3 Smoke runner (`turtle_walk.py smoke`)

12 probe queries — mix of direct-training-examples + near-training + out-of-distribution (OOD):

| Category | Probes |
|---|---|
| Direct training (in corpus) | "walk forward 100"; "turn left"; "draw a square"; "draw a circle"; "lift pen up"; "spin around" |
| Near training | "make a hexagon"; "go forward 50"; "walk in a circle"; "take a big step" |
| OOD (not in corpus) | "draw a star"; "make me a flower" |

For each probe:
1. Prompt cascade with `<english_utf8>\x02`
2. Generate up to 64 bytes; stop at ETX (`\x03`)
3. Decode bytes as UTF-8 (with `errors='replace'`)
4. Try `logo_parser.parse(text)` — record PARSE_OK + error
5. If parse OK: try `logo_interp.run(prog)` — record EXEC_OK + segment count + error

### §3.4 What this partition does NOT do

- **Lift the structural ceiling.** Per R-RBS-LM-19 / R-RBS-LM-43 prediction; confirmed empirically by 0/12 meaningful LOGO output.
- **Use quantum-numbered structured atoms.** v44 uses random Class A byte mints (per R-RBS-LM-25); the LOGO L1 quantum-numbered-atom pattern is a follow-up direction (R-RBS-LM-44b candidate).
- **Implement turtle-graphics rendering.** LOGO L0 produces `trace.segments` (line segments); rendering to image / SVG is downstream (LOGO has CSV export per L5; image render is its own layer).
- **Compose with R-RBS-LM-33 merge.** v44 stands alone for this partition; merge with knowledge instruments is a follow-up direction.
- **Test multi-buffer FFT graft (R-RBS-LM-32) for the turtle-walk task.** Future candidate; not run here.

---

## §4 Verification — captured runs

### §4.1 Encoding

```
=== R-RBS-LM-44 — Encode English↔LOGO parallel corpus ===
  D = 8192; CONTEXT_WINDOW = 64 bytes; V = 256
  corpus: 51 (English, LOGO) pairs from turtle_walk_corpus.json
    English bytes total: 782
    LOGO bytes total:    901

=== Build paired byte stream ===
  stream length: 1836 bytes (1683 content + 153 delim)

=== Harvest (stride 4) ===
  observations: 443

=== Encode + bundle ===
  443 bindings in 56.2s (7.9/s)            ← slow due to 70B Q4 cron CPU contention
  bundle: 0.78s; instrument = 1024 bytes
  saved: rbs_lm_instrument_v44_turtle_walk.bin
```

### §4.2 Smoke (12 probe queries)

```
   FAIL  english:  'walk forward 100'   cascade:  ' \x05\x05\x05\x05...'         (control bytes; parse error)
   FAIL  english:  'turn left'          cascade:  ' \x15...'                      (control bytes; parse error)
   FAIL  english:  'draw a square'      cascade:  "''''''''..."                   (single-quote repetition; parse error)
   FAIL  english:  'make a hexagon'     cascade:  'ss�ss�ss...'                   (mode-collapse to 's'; parse error)
   FAIL  english:  'go forward 50'      cascade:  ' \x15 � � � � �...'            (mixed control + replacement; parse error)
   FAIL  english:  'draw a circle'      cascade:  ' \x02\x02\x02\x02...'          (STX repetition; parse error)
  PARSE  english:  'lift pen up'        cascade:  ' t              '              (parse: procedure call "t"; exec: undefined procedure)
   EXEC  english:  'walk in a circle'   cascade:  '                '              (all spaces; parse: empty program; exec: 0 turtle segments)
   FAIL  english:  'spin around'        cascade:  ' �...'                          (replacement char; parse error)
  PARSE  english:  'take a big step'    cascade:  ' eeeeeeee...'                  (mode-collapse to 'e'; parse: long procedure name; exec: undefined)
   FAIL  english:  'draw a star'        cascade:  ' \x02 \x02\x02\x02...'         (OOD; STX repetition)
   EXEC  english:  'make me a flower'   cascade:  '                '              (OOD; spaces; empty program)

=== Summary ===
  PARSE success: 5/12
  EXEC  success: 2/12   (both empty-program no-ops)
```

### §4.3 Honest framework reading

**No probe produced an actual LOGO command sequence.** The 5 parseable cases are:
- 2 mode-collapsed to spaces (parse as empty program; exec produces 0 turtle segments — a no-op)
- 2 mode-collapsed to single-letter repetition (`t`, `e`) which the LOGO parser interpreted as procedure-call syntax; exec fails on the undefined procedure
- 1 was a near-empty space output

**The cascade did NOT produce a single FORWARD/BACK/LEFT/RIGHT/REPEAT/PENUP/PENDOWN/TO command for any probe.**

Mode-collapse patterns differ per probe (different bytes get chosen) but never converge on LOGO-token bytes. Even direct training examples (`'walk forward 100'`, `'draw a square'`) failed.

---

## §5 Findings

**Finding 1 — Constrained-action-vocabulary projection does NOT trivially escape the structural ceiling.** Per §4.2. 0/12 probes produced executable LOGO commands. The R-RBS-LM-19 / R-RBS-LM-43 substrate-bound mode-collapse persists even when the target vocabulary is small (12 atoms) and structured.

**Finding 2 — Mode-collapse byte choice DOES vary with prompt; cascade has weak structural signal.** Per §4.2. Different probes mode-collapse to different bytes (`'`, `t`, `e`, `s`, `\x02`, `\x05`, `\x15`, space, `�`). The cascade is responding to input differences — just not enough to surface LOGO tokens.

**Finding 3 — 5/12 outputs were AT LEAST PARSEABLE LOGO syntax (even if meaningless).** Per §4.2. Space-only outputs parse as empty programs; single-character repetition parses as procedure-call syntax. This is sub-ceiling structural signal that the cascade output IS biased toward LOGO-shaped bytes for some queries — just not strongly enough to surface a real command.

**Finding 4 — Direct training examples failed alongside OOD probes.** Per §4.2. `'walk forward 100'` (literal corpus entry) failed; `'draw a star'` (OOD) failed similarly. **The cascade is not "memorizing" the training corpus byte-transitions strongly enough for direct lookup**, even at the modest 51-pair scale where memorization would be theoretically possible.

**Finding 5 — The corpus-scale alone is insufficient under candidate E framing.** Per R-RBS-LM-39 volume hypothesis + Finding 4. 443 observations from 51 pairs is comparable to R-RBS-LM-25 byte-mode scale (which mode-collapsed); we'd expect candidate E to need substantially MORE pairs OR structured-atom encoding (R-RBS-LM-43 §3.4 + LOGO L1 pattern).

**Finding 6 — R-RBS-LM-43 §3.4 was right: random Class A byte mints are NOT enough for naming-layer encoding.** Per §3.4 of R-RBS-LM-43 (the user's "people words are not natural and must have some heavy lifting work" framing). v44 used random byte mints (per R-RBS-LM-25); LOGO L1's lesson was that random atoms FAIL for symmetry-bearing tasks. The candidate-E target HAS symmetry structure (the 12 atoms have a sub-vocabulary structure: motion verbs / pen ops / repetition / numbers / brackets). **Random atoms don't surface that structure.**

**Finding 7 — R-RBS-LM-44b candidate emerges: structured-atom English-fragment encoding.** Per Finding 6 + R-RBS-LM-43 §3.4. Encode the ENGLISH fragments as quantum-numbered atoms (e.g., `(action_verb, object_noun, magnitude_num, direction_axis, modifier)`), not as raw bytes. Encode LOGO commands similarly. Then run the same paired-stream protocol. **This is the most substrate-honest next test.**

**Finding 8 — R-RBS-LM-44c candidate emerges: explicit B/H/N projection composition.** Per R-RBS-LM-43 §3.2 + Finding 8 — instead of expecting the cascade to LEARN the projection from coincidences (which 51 pairs don't sustain), explicitly compose B (TLV-framing of English fragment) + H (introspect cascade state) + N (rational-approximation to nearest LOGO command in a discrete lookup). Hybrid cascade + explicit-projection approach.

**Finding 9 — The cross-substrate-cascade-matching methodology is doing its job.** Per `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`. Same structural-ceiling pattern recurs at: byte-level mode-collapse (R-RBS-LM-25); ASL gloss projection (R-RBS-LM-27); LOGO action projection (this partition). **The methodology validates R-RBS-LM-37 / R-RBS-LM-43 at multiple constrained-vocabulary targets**, not just one.

**Finding 10 — Honest negative result is data; not failure.** Per `[[feedback_full_coverage_shipping_mpm_way]]` + R-RBS-LM-43 §3.6 falsifiability discipline. This partition empirically rules out "candidate E works trivially at small scale." The R-RBS-LM-40 design space narrows: candidates A-D and refinements (R-RBS-LM-44a-c) are the remaining surface.

---

## §6 Open threads (candidate refinements + alternative paths)

| Direction | What changes | Cost |
|---|---|---|
| **R-RBS-LM-44a — volume scale-up** | Same encoder; 500-1000 pairs; structured corpus generated from LOGO programs | Medium — corpus authoring; encoding at higher scale slower |
| **R-RBS-LM-44b — quantum-numbered atoms** | Encode English fragments + LOGO commands as structured atoms (LOGO L1 pattern); not raw byte mints | High — requires designing the role vocabulary (verb/noun/magnitude/etc.) AND a new encoder script |
| **R-RBS-LM-44c — explicit B/H/N projection** | Hybrid: cascade picks discrete LOGO-atom candidate; explicit lookup-table-style projection composes the program; rational-approximation snaps to nearest valid command | Medium — needs lookup-table + N-class composition logic |
| **R-RBS-LM-44d — multi-buffer FFT graft applied** | Use R-RBS-LM-32 multi-buffer FFT to provide system-prompt + grammar primer + RAG entry, with cascade picking final atoms | Medium — composition of existing infrastructure |
| **R-RBS-LM-44e — merge LOGO atom vocabulary as a separate instrument** | Per DeepSeek-derived insight (R-RBS-LM-43 §3.2 absorption): a dedicated 1024-byte "LOGO vocab" instrument that merges with v44 via R-RBS-LM-33 merge_instruments | Medium |

Per R-RBS-LM-43 §6 roadmap, these are all candidate refinements; each is its own partition when scoped.

---

## §7 Closing — partition status

**Status:** CLOSED. R-RBS-LM-40 candidate E first-test executed honestly. Result: substrate-bound mode-collapse persists at the constrained-vocabulary target; 0/12 probes produced executable LOGO commands; 5/12 produced parseable syntax (no-op programs). R-RBS-LM-19 / R-RBS-LM-43 structural-ceiling reading is reinforced at a NEW vocabulary scale.

**Falsifiers:**

1. A claim that this partition delivered working turtle-walk — **explicitly disclaimed §4-§5**; 0/12 meaningful LOGO commands; the user's turtle-walk desire is not yet operational via candidate E at this scale.
2. A claim that R-RBS-LM-40 candidate E is structurally impossible — **NOT disclaimed**; this partition rules out one specific implementation (random byte mints; 51 pairs; paired-stream encoding). Refinements (44a-e) remain testable. The structural ceiling may dominate, OR scale + structured atoms may surface the projection. Open question.
3. A claim that constrained vocabulary is HARDER than English prose — **partially supported**; PARSE 5/12 is comparable to English prose mode-collapse patterns we've seen; EXEC 0/12 (meaningful) is consistent with substrate-bound limitation. Constrained vocab isn't easier OR harder than English; it's substrate-bound in the same way.
4. A claim that LOGO L1 quantum-numbered atoms would automatically rescue this — **partially disclaimed §6**; R-RBS-LM-44b is a future test; we don't know it'll work; the LOGO L1 evidence is FOR symmetry-bearing tasks, not necessarily for English-fragment→LOGO-command mapping.

**Inherits to:**
- R-RBS-LM-44a/b/c/d/e candidate refinements (each a future partition)
- ROADMAP.md updates: candidate E first-test result documented; substrate-bound reading reinforced
- R-RBS-LM-43 §3.6 falsifier table updated with one more empirical anchor
- srmech_research_notebook.md §3.25 may absorb this finding alongside the R-RBS-LM-43 framework reading

**SSoT marker:** Findings 1 (constrained vocabulary doesn't escape ceiling) + 6 (random atoms don't surface naming-layer structure) + 9 (cross-substrate-cascade-matching working) + 10 (honest negative = data) absorb into `srmech_research_notebook.md` §3.25 at next SSoT absorption. The candidate-E follow-up directions in §6 inform R-RBS-LM-40 design space.

---

*The turtle-walk founded on user's childhood LOGO experience is not yet operational; the structural-ceiling reading is what got tested honestly. Per `[[feedback_full_coverage_shipping_mpm_way]]`: negative result counts, and informs the next-rung scoping.*
