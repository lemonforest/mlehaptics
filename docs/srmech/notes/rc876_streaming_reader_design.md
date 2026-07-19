# `#876` — the genome STREAMING RENDER READER (EPH: find / ride / enter-ride-exit) — DESIGN

**Status:** design note. NOT the build. No version bump / branch / PR / ADR / production code here.
**Audited against** the worktree at `5adff4e5c` (v0.9.0rc281; ABI 6; `GENOME_FORMAT_VERSION` 15;
`CEIL_WIRE_GLUE_GAPS` 11).
**Governing:** **ADR-0009** (capability is the invariant; each implementation is a coherency
projection; no implementation is primary) · ADR-0003 (C-host standalone) · ADR-0005 (no external
math library) · ADR-0006 (carrier discipline; decline-at-a-ceiling is an anti-pattern) · §101
progress/abort · §102 / F1252 two-stage encode (`f1252_two_stage_encode_design.md` — the WRITER
this pairs with).
**Provenance:** every number below is emitted by
`rc876_streaming_reader_cost_probe.py` / `rc876_streaming_reader_marker_census.py` (this
directory) into `rc876_streaming_reader_design.ndjson`.

---

## 0. TL;DR — and the two things in the brief that are not true

1. **"The accessibility landscape IS the index" does not hold on the store this reader targets.**
   Measured: an F1252 stage-1 `plasmid_extract` store contains **only** `0x6B` kernel telomeres and
   data turns — **0 chromatin (`0x48`) caps, 0 gene gate caps**. `gene_express_plan` returns an
   **empty** plan at every `cell_state`; `accessible()` returns the chromatin-free `(1, 1)` default.
   The landscape is a design **target** needing a write-side change, not a property to read. → **F2**.
2. **The rc280 cost shape the brief asked us to hunt DOES recur, and the second instance is worse
   than a catalog re-derivation.** `_read_region_prefix` re-opens `turns.bin` on **every** call and
   `_section_node_ids` calls it in a growth loop → measured **exactly 2.0 opens/section**. At
   200 sections the rc280 targeted read is **1.8× SLOWER than a full sequential decode of the whole
   body**. rc280 fixed the asymptotics and left a syscall constant that dominates at the field
   store's section size. → **A2**, and the strongest argument *for* this reader.

What survives: the caps genuinely are a distributed TOC; a **single-held-handle forward stream** is
the right primitive; **no `.idx` side-car is needed for forward work**; and the design does **not**
require the `#899` `ws`/ABI 6→7 fix as a prerequisite (§6).

---

## 1. The capability set — implementation-neutral, two projections each (ADR-0009 §2)

Capability first; then both coherency projections. No projection is primary. `ws` = caller arena
(ADR-0006), so every compiled entry is reentrant **by construction** — the `#899` file-scope-static
defect is designed out, not inherited.

| # | CAPABILITY (the invariant) | scripting-coherency | compiled-coherency |
|---|---|---|---|
| **R1** | **open** a store to a forward reader position with O(1) resident state, deriving **no** catalog | `reader_open(store, the_one) -> Cursor` | `srmech_genome_reader_open(dir, the_one, leaf_dim, ws, ws_len, srmech_genome_cursor_t *out)` |
| **R2** | **find** — advance to the next region whose **cap bytes alone** satisfy a predicate; stop there | `reader_find(cur, pred) -> Hit \| None` | `srmech_genome_reader_find(cur, const srmech_genome_pred_t *, srmech_genome_hit_t *out)` |
| **R3** | **ride** — from a positioned cursor, stream the region's turns, uncoupling each through `the_one`, folding a harvest op; **stops early** when the harvest is satisfied | `reader_ride(cur, harvest, acc) -> acc` | `srmech_genome_reader_ride(cur, uint32_t harvest, unsigned char *out, size_t out_cap, size_t *out_len)` |
| **R4** | **skip** — advance past the current region **without** riding it (stride only, no decode) | `reader_skip(cur) -> Cursor` | `srmech_genome_reader_skip(cur)` |
| **R5** | **enter-ride-exit** — the bracketed unit: enter at a cap, ride to the closing boundary, exit positioned at the **next** cap; fold the region digest; fire the §101 tick at the exit | `reader_walk(cur, harvest, progress=) -> iterator` | `srmech_genome_reader_walk(cur, harvest, tick, tick_user, …)` |
| **R6** | **verify** — maintain the region-chain accumulator over exactly the bytes traversed | `cur.chain_hex` / `reader_verify(cur)` | `srmech_genome_reader_chain(cur, char out[65])` |

**Wire discipline.** `pred` is a **struct**, not a callback: `{marker_mask, label_prefix,
label_prefix_len, cell_state, require_open}`. `harvest` is an **enum**
(`NODE_IDS` / `GRAPH_EDGES` / `RAW_SYMBOLS` / `COUNT_ONLY` / `REGION_SHA`). Neither crosses the wire
as a function pointer, so **no new callback typedef → ABI stays 6** (the §101 tick reuses the
existing `srmech_progress_tick_cb_t`). The cursor is caller-arena-backed and carries a `struct_size`
gate, mirroring `srmech_progress_ev_t`, so later append-only growth does not re-bump either.

**Ratchet.** Each of R1–R6 lands as a whole-op C entry in `_WHOLE_OP_C_PEER`
(`test_rosetta_transitive_standalone.py`), so `CEIL_WIRE_GLUE_GAPS` **stays 11 and never rises**.
Candidate bonus: R2+R3+R5 compose into the orchestration `genome_genes_expressed` currently lacks,
which would let the ceiling **drop to 10** — one candidate, not a commitment.

---

## 2. The op family — EPH semantics, precisely

```
  EXCITE            PROPAGATE                       HARVEST
   find    ───►    ride (uncouple each turn)   ───►  fold → value
     │                    │                             │
  reads CAP bytes    reads REGION bytes            returns acc
  only (leaf_dim)    (stops early if the
     │                harvest is satisfied)           │
     └──────── enter-ride-exit brackets the pair ─────┘
               exit = a valid cancel point (§101)
```

| op | what excites / propagates / harvests | returns | cost |
|---|---|---|---|
| **find** (EXCITE) | the cursor is excited to the first cap matching `pred`; the predicate touches **only** cap bytes | `(label, byte_offset, cap_kind, access_num, access_den)`, cursor left at the region's first data turn | O(bytes **strided** to the hit). Early exit is the whole win |
| **ride** (PROPAGATE + HARVEST) | the excitation propagates along the region's turns; each uncouples independently (`quad_turn`); the fold is the harvest | the harvest accumulator | O(bytes **ridden**). `NODE_IDS` terminates the instant `n_node_ids` ints complete → O(node_ids extent), **rc280's targeted read re-expressed as a ride-termination condition rather than a separate seek path** |
| **skip** | no propagation — stride past | cursor at the next cap | O(region blocks), **measured 9.7× cheaper than riding the same bytes** |
| **enter-ride-exit** | the bracketed unit | `(hit, acc)` + a cursor at the next cap | ride + one chain fold; the **exit** is the §101 tick site, so a cancel truncates at a chromosome boundary — the same contract stage 1/2 already honor |

**Cancel semantics (§101).** `SRMECH_CANCELLED = 7`. A cancelled **read** returns a partial
accumulator **and** the cursor, because a partial read is a *resumable* read, not a wrong one —
unlike `section_counts`, where rc280 correctly **raises** because a partial *count* silently shifts
every downstream threshold. The reader therefore follows the encode convention (clean partial), and
any op that folds a reader stream into a **count** must adopt the `SectionCountsCancelled` raise
instead. Stated so the difference is a decision, not an accident.

**Genome-as-projection (design intent, under test — not an established result).** R1–R6 name no
genome concept: a store is a byte sequence of self-describing blocks; a cap is a block whose first
byte is `> 3`; a turn uncouples against a held invariant. The genome case supplies the marker
alphabet and the §89 payload grammar as *parameters*. Whether this generalises to any
finitely-seeded matrix under EPH is **untested** and is carried as intent only.

---

## 3. Why no `.idx` — and exactly where the argument fails

**The caps are a real distributed TOC.** Three measured/verified properties carry it:

1. **Self-describing blocks.** `kind byte + leaf_dim` gives the stride (`_walk_region_blocks`); no
   length field is needed to **advance**.
2. **Per-leaf reversible coupling.** `quad_turn` uncouples leaf *k* from leaf *k* alone — no chaining
   — so **any prefix decodes to the corresponding prefix of the symbol stream**. This is what lets a
   ride stop anywhere. (rc280 proved it for `node_ids`; it is general.)
3. **Region-leading cap integrity.** The bound is the region's first `leaf_dim` bytes, so a prefix
   read pays the *same* bound as a whole-region read — a targeted read is not a weaker read.

**So no side-car is needed for forward work.** Every capability in §1 is one forward pass.

**Where it fails — state it plainly.** A cap carries **no region length**. Region boundaries are
discoverable only by walking. That splits two quantities the design must never conflate:

| quantity | field-store value | meaning |
|---|---|---|
| bytes **touched for a decision** | P × leaf_dim ≈ 240,881 × 64 = **15.4 MB** | what the predicate actually reads |
| bytes **traversed** | **336 MB** | what the reader must stride to reach them |

The **22× gap** between them is exactly what a persisted region-offset table would buy — and it is
the only thing that makes **random access** sub-O(body). Consequences, unhedged:

- **Forward sweeps:** no `.idx`. Confirmed.
- **A single random access by label:** O(body). Acceptable once.
- **N random accesses:** O(N · body) without a resident catalog. **This is a genuine failure of the
  no-index position** and it is why `_catalog_data` exists. If the workload is random-access-heavy,
  something must be persisted or kept resident. → **fermata F1: the query workload is not derivable
  from the brief, and it is the single fact that decides this.**

**One candidate that keeps the index IN the strand (not a side-car).** Caps are `leaf_dim ≥ 52`
bytes of `[marker][label NUL-padded]`. There is already an established, back-compatible pattern for
a `uint64` big-endian field carried right after the label's NUL — §127 active-telomere count and
§135/rc281 gene copy-number both use it, with all-NUL padding reading as "absent". A
**`next_region_delta`** in the same slot would let a reader **jump** cap-to-cap: a find sweep becomes
O(P) seeks of `leaf_dim` bytes (≈15.4 MB touched) instead of a 336 MB traversal, and random access
becomes O(P) rather than O(body). `genome_append` already knows `region_len` at write time, so the
field is writable without a second pass; a delta of 0 means "unknown — stride instead", so every
existing store stays readable. This is **derived-in-place, not a stored plaintext TOC**, which is the
distinction ADR-0003 actually draws. Offered as **one candidate**; it is a format addition and
therefore a conductor decision, not a design conclusion.

---

## 4. The distributed-TOC coherency read

Caps are encountered in **body order = append order = the order stage 1 extracted documents**. The
"table of contents" is read by **traversal**, not lookup, and the reader opens at scale because the
*decision* is cap-local even though the *traversal* is not:

```
turns.bin ─────────────────────────────────────────────────────────────────►
[0x6B sec0][turns…][0x6B sec1][turns…][0x48?][0x47?][turns…][0x6B sec2]…
   ▲  ▲                ▲                  ▲      ▲
   │  └ label (inline, to first NUL)      │      └ gene gate cap  ─┐ the accessibility
   └ marker byte (cap iff > 3)            └ chromatin cap (0x48) ──┘ landscape — ABSENT
                                                                      on a stage-1 store (§0.1)
find:  stride ──► test cap ──► miss ──► skip ──► test cap ──► HIT ──► ride
verify: fold region digest into the running chain at each EXIT
```

**Ordering guarantee:** the reader visits regions in coherency order and the region-chain
accumulator is folded in that same order, so `cur.chain_hex` after a **complete** traversal equals
the head's `body_sha256`. After a **partial** traversal it is a verified-**prefix** value only —
comparable to nothing stored. Say so; do not let a partial read imply a verified store.

**The heterogeneity trap (A3).** The VOCAB karyotype chromosome carries the **same** `0x6B` marker
as a plasmid section but holds a raw Klein-4 byte blob, not a §89 graph payload. Every current
consumer excludes it by **string comparison** against `VOCAB_LABEL`. A reader classifying by cap
kind cannot tell them apart and hard-errors (`GenomeBoundingError: …declares 23 node_ids but only 0
are present … the section is malformed`). → **fermata F3.**

---

## 5. Cost model

**Measured** — scripting-coherency path, `HAS_NATIVE=False`, this machine, `leaf_dim=64`, P=200
plasmid sections, 95,790-byte body (~480 B/section). Best-of-3, **two independent runs** (run 1 /
run 2).

| operation over the whole body | time (run 1 / run 2) | ratio to stride |
|---|---|---|
| **stride** (walk every block, classify caps, decode nothing) | **0.0128 / 0.0175 s** | 1.0× |
| **ride** (uncouple every data turn through `the_one`) | **0.1246 / 0.1511 s** | **9.7× / 8.6×** |
| **rc280 targeted `node_ids`, all sections** (current `section_counts` inner loop) | **0.2235 / 0.2146 s** | **17.4× / 12.3×** — and **1.8× / 1.4× slower than a full sequential decode** |
| cold `_catalog_data` derivation | 0.0289 / 0.0301 s | 2.3× |
| └ region-Merkle + array materialisation term | 0.0016 / 0.0015 s | **5.7 % / 5.1 % of catalog** |
| `turns.bin` opens for one targeted pass | **400 (= 2.0/section), both runs** | — |

**⚠️ Run-to-run variance is real — do not over-trust a single ratio.** The timing ratios move
**±20–40 %** between runs (page cache, GC, scheduling). What is stable across both runs, and is what
the design actually rests on:

- ride ≫ stride (**8.6–9.7×**) — the skip/ride separation is real but its constant is soft;
- targeted ≫ stride (**12.3–17.4×**) **and targeted > a full sequential decode (1.4–1.8×)** — the
  direction reproduces, which is the load-bearing claim;
- the region-Merkle + array term is **~5 %** of cold-open in both runs;
- the syscall count is **exactly** 2.0 opens/section in both runs — the only number here with no
  measurement noise at all, and correspondingly the one to lean on.

**Three conclusions that shape the design:**

1. **Cold-open time is dominated by the block walk (66 %), not by hashing or array building (5.7 %).**
   So streaming instead of materialising the catalog buys **memory** (O(P) → O(1)) and **early exit**
   — it does **not** buy much wall time on a full pass. Do not oversell it.
2. **Skip is 9.7× cheaper than ride.** The accessibility landscape is worth building *because of this
   constant* — but only once it exists (§0.1).
3. **The targeted read's syscall constant dominates at small sections.** 2.0 opens/section →
   extrapolated **~481,762 opens** for one field-store pass. A single held handle removes it
   entirely. This is the reader's central claim and its central falsifier (F2).

**Field-store extrapolation — explicitly labelled as extrapolation.** From 95,790 B → 336 MB is
**3.5 × 10³** in body bytes and 200 → 240,881 is **1.2 × 10³** in sections. These are
order-of-magnitude only; **the ordering is what is defensible, not the seconds.**

| | extrapolated | scaling basis |
|---|---|---|
| stride whole body | ~45 s | bytes |
| ride whole body | ~7 min | bytes |
| cold `_catalog_data` | ~100 s | bytes |
| rc280 targeted pass | ~4.5 min | sections (syscall-bound) |

Against the anchors: stage-1 extract did 240,881 sections in **11.1 min / 336 MB**, replacing an 8 h+
monolith that never finished; `section_counts` pre-rc280 was **~22 h**. A reader in the tens of
minutes for a full pass is in the right regime. **A reader that reintroduces a quadratic is a failed
design** — the specific shape to guard is any per-region call that re-derives the catalog or re-opens
the body. Both instances found in the current tree are that shape (A1, A2).

---

## 6. Known ceilings — is the `#899` fix a prerequisite?

**No, for the reader as designed. Yes, for `section_counts` as it stands.**

`srmech_genome_section_counts` works out of three file-scope statics (`g_sc_arena`, `g_sc_slots`,
`g_sc_win` — `c/src/srmech_genome.c:6099-6101`), because JPL Rule 3 bans malloc and its exported
signature carries no `ws`. Verified bounds (`c/include/srmech.h` §6618-6625): the 32 MiB catalog
arena's ~2.7 KiB/chromosome term → **~11,000 sections** against **240,881**; the 2^18-slot table →
**196,608 distinct ids** against **1,100,189**. Over either bound it returns `SRMECH_ERR_OVERFLOW`
and the scripting path runs. The same statics make it **not reentrant**.

The reader **does not inherit this**, on two conditions that are design constraints, not hopes:

- **C1 — every reader entry takes `ws` from the start.** No file-scope statics. Reentrant by
  construction; two concurrent readers are well-defined. This is the ADR-0009 lesson applied *before*
  the fact rather than retrofitted.
- **C2 — no reader op may call `_catalog_data` / `srmech_genome_obtain_manifest`.** That call is
  where the 2.7 KiB/chromosome arena term lives. **Any fallback to the catalog re-imports the
  ~11,000-section ceiling.** This is the single hardest constraint in the design and the thing most
  likely to be violated during a build.

**A candidate, not a claim:** `section_counts` *is* "find every section, ride its `node_ids` prefix,
harvest a count." If the reader subsumes it, `#899` closes by **obsolescence** — the ceilinged symbol
stops being the path that matters — which is a better outcome than a `ws` retrofit. Whether to
subsume or coexist is **fermata F4**. If they coexist, `#899` stays open on its own schedule and the
ABI 6→7 bump is still owed there.

---

## 7. Falsifiers

Each must be able to come back **FALSE**. (Rejected as vacuous: "the reader returns the same bytes
as the reader"; and any `Lk − Tw − Wr = 0`-shaped restatement of a theorem.)

| # | claim | FALSIFIED IF | status |
|---|---|---|---|
| **F1** | skip is ≥5× cheaper than ride | measured skip:ride < 5:1 **on the field store** | open (9.7:1 synthetic; small sections could collapse it) |
| **F2** | a single-handle forward stream beats the current per-section targeted read | measured stream ≥ measured rc280 targeted, same store | open — **the load-bearing one**; OS page cache could make the 481,762 opens nearly free |
| **F3** | every required read is expressible as one forward pass | any required read is genuinely random-access-by-label at N ≫ 1 | **ALREADY PARTIALLY FIRING** — §3 |
| **F4** | the accessibility landscape can serve as the index | the store carries no such marks | **ALREADY FALSE** — measured, §0.1 |
| **F5** | the reader ships additively at ABI 6 | the cursor cannot be expressed without a new callback typedef or an existing-signature change | open |
| **F6** | reentrant by construction | two readers over one store in two threads diverge | open — directly runnable |
| **F7** | byte-parity between projections | any harvest op differs scripting vs compiled | open |
| **F8** | no reintroduced quadratic | bytes-read or syscall count grows super-linearly in P over a 4-point sweep | open — should be a shipped ratchet test, not a one-off |

---

## 8. Unknowns — what could not be determined

- **U1.** The real 336 MB / 240,881-section store is **not in this worktree**. Every field-scale
  figure in §5 is extrapolated across ~3 orders of magnitude. Absolute seconds are not defensible;
  cost *ordering* is.
- **U2.** `HAS_NATIVE=False` here (no built shared library in the source tree). **All measurements
  are the scripting-coherency path only.** The compiled path's constants are unmeasured, so the
  9.7× skip:ride and 2.0 opens/section may differ materially in C.
- **U3.** **The query workload is unknown.** Whether random-access-by-label at scale is required
  decides §3 outright, and it is not derivable from the brief. → F1.
- **U4.** Tracker tasks **`#899` / `#901` could not be read** — see §9.
- **U5.** The "universal wherever a finitely-seeded matrix undergoes EPH" claim is **untested**;
  carried as design intent per the brief, with no evidence offered either way.
- **U6.** The C `srmech_genome_obtain_manifest` scan path was **not** read line-by-line; its O(body)
  shape is inferred from the documented ~2.7 KiB/chromosome arena term and the Python mirror.
  Confirm before build — C2 in §6 depends on it.

---

## 9. Corrections to the brief

1. **`#899` / `#901` are not readable as tracker tasks.** GitHub **#899** = merged PR *"srmech
   v0.7.1rc2: Schur/DtN wired as DSL cascade stage"*; **#901** = merged PR *"srmech v0.7.1 —
   production graduation"*. Neither concerns `section_counts`. In the tree, `#899` appears **only**
   inside ADR-0009 §1.2 — which itself flags *"the id does not appear in the tree, so it is recorded
   here on that authority, not tree-verified."* `#901` appears **nowhere** under `docs/srmech/`.
   **The brief's substance is correct** and fully documented in ADR-0009 §1.2 + `c/include/srmech.h`
   §6618-6625 + CHANGELOG rc280; those are what §6 above is built on.
2. **"The accessibility landscape IS the index" is false of the target store today** (§0.1, measured).
   It is a design target requiring a write-side change. → F2 (fermata).
3. **rc281 has landed** (`5adff4e5c`): the `amplify` / `copy_number_of` C peers and the wire-glue
   ratchet are on `main`; `CEIL_WIRE_GLUE_GAPS` is already **11**, down from 13. The brief is current
   on this.
4. **The rc280 shape recurs — twice, and one instance is worse than the original** (A1, A2 below).

---

## 10. Anomalies (see also `rc876_streaming_reader_design.ndjson`)

- **A1 — stale bounded-I/O claim.** `genome.py:7216` (`_gene_express_plan_path`):
  `data = _catalog_data(path, the_one)   # the manifest read — never opens turns.bin`. **False** on a
  v12 head-only manifest — and every store written today is head-only (verified: on-disk `data` keys
  are `body_sha256 / format_version / leaf_dim / n_chromosomes / n_turns / the_one`, no
  `chromosomes`). `_catalog_data` reads the **whole** body and re-Merkle-folds it. The C header block
  for `srmech_genome_gene_express_plan` carries the same claim ("NEVER reads a region body — bounded
  I/O"): true of its gate loop, false of its manifest derivation. **Verdict:** comment/doc drift, not
  a logic bug — the op is correct, its advertised cost is not. Exactly the class rc280 corrected in
  `_section_labels`. **Next:** correct both; add a bytes-read pin.
- **A2 — the targeted read re-opens the body per read.** `_read_region_prefix` opens `turns.bin`
  fresh on every call; `_section_node_ids` calls it in a growth loop. **Measured 2.0 opens/section**
  (400 for 200 sections). The targeted pass is **1.8× slower than a full sequential decode of the
  whole body**. **Verdict:** real; rc280 fixed the asymptotics and left a syscall constant that
  dominates at the field store's ~1,462 B/section. **Next:** confirm on the real store before
  claiming the reader wins (F2).
- **A3 — VOCAB is label-discriminated, not marker-discriminated.** `_section_node_ids` on
  `__vocab__` raises `GenomeBoundingError`. Same `0x6B` marker, different payload grammar. **Next:**
  fermata F3 — new marker byte vs. a reserved-label contract.

---

## 11. Fermatas (conductor decisions)

- **F1** — **the query workload.** Random-access-by-label at N ≫ 1 is the one requirement that forces
  a persisted or resident index. Decides §3 outright. Not derivable from the brief.
- **F2** — **the write-side prerequisite.** The accessibility landscape must be *written* before the
  reader can consult it. Does stage 1 gain chromatin/gate caps, or does stage 2's organize lay them
  down? Format decision.
- **F3** — **VOCAB discrimination** (A3): a new marker byte, or a documented reserved-label contract.
- **F4** — **does the reader subsume `section_counts` or coexist?** Subsume → `#899` closes by
  obsolescence. Coexist → `#899` stays open and still owes the `ws` + ABI 6→7 work.
- **F5** — **the `next_region_delta` cap field** (§3): worth ~22× on predicate-sweep I/O and makes
  random access O(P). A format addition; not a design conclusion.
