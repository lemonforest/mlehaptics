# F1252 / §102 — the two-stage genome encode, C-native — BUILD-READY design

**Status:** design + rc-breakdown note (NOT the build). No version bump / branch / PR / ADR here.
**Audited against** `origin/main` @ `6e0cbc893…rc273` (v0.9.0rc273; ABI 5). Builds on
`c_host_parity_audit_rc273.md` (the genome C-host GAP list — used as input, not redone) and
`rc275_progress_abort_prototype.md` (the §101 progress/cancel primitive — threaded in, not redesigned).
**Discipline anchors:** `[[feedback_genome_must_exist_fully_in_c]]`, `[[feedback_persist_genome_native_not_loose_json]]`,
`[[feedback_encode_once_render_on_the_fly_epigenetic_reader]]`, ADR-0003/0005/0007, MPM (F1251 mapping is
already attested — cited, not re-derived).

---

## 0. TL;DR

Split the encode the finding names: **stage 1 EXTRACT** (dense/text → append-only *sectional plasmid*
subgraphs) + **stage 2 ORGANIZE** (integrate plasmids → minted nuclear core, ~16/84). Two ground-truth
findings shape the build:

1. **The stage-1 C encode primitives ALREADY EXIST.** `srmech_text_cooccurrence_topk` +
   `_topk_extract` (§52 bounded top-K), `srmech_graph_kernel_encode` (#1390 codec), and — decisively —
   `srmech_genome_append` (§v12 **O(1) head-only** genome-native append; the O(N²) wall is already gone).
   Stage 1 = **wiring existing C peers**, not a from-scratch build. This is the exact machinery the loose
   916 MB JSON should have been using: append a plasmid section, rewrite only the head.
2. **The incremental organize path NEVER calls `recursive_cut`.** So the parity audit's "ship G1
   (recursive_cut) FIRST, it's the deepest/largest build" ordering is **inverted**: G1 becomes a LATE
   *fallback* (cold-start / provenance-less dumps), and the two genuine hot-path gaps — **G4
   `srmech_genome_integrate`** (splice) and **G5 `srmech_genome_mint_strand`** (promote) — ship first as
   the stage-2 primitives.

**Which rc kills the blind 3.4 h partition:** **rc279** (stage-2 `genome_integrate_plasmids`) structurally
removes the monolithic from-scratch `recursive_cut` from the encode path. **rc275** (progress) only
*de-blinds* the interim run (heartbeat + cancel); rc279 removes the block itself.

---

## 1. The two-stage flow (aphantasia: draw it)

```
                       ┌──────────── STAGE 1: EXTRACT (cheap, streaming, once-per-doc) ────────────┐
 doc_1 ─┐              │  window co-occurrence (LOCAL)      graph→Klein-4          O(1) HEAD append │
 doc_2 ─┤  tok_ids ──► │  srmech_text_cooccurrence_topk ─► srmech_graph_kernel ─► srmech_genome_    │
  ...   │  (GLOBAL     │       _extract  (per doc)          _encode (1 chromo)     append (section)  │
 doc_D ─┘   vocab id)  │            │                                                    │           │
                       └────────────┼────────────────────────────────────────────────────┼──────────┘
                                    ▼                          append-only, genome-native  ▼
                            section_count[node] += 1     sections/  turns.bin  (P plasmid chromosomes)
                            (integer accumulator)                  manifest.json (v12 HEAD, .fai cache)
                                    │                                          + vocab chromosome (shared)
                       ┌────────────┼──────── STAGE 2: ORGANIZE (incremental, the "genome step") ─────┐
                       │            ▼                                                                  │
                       │  CONSERVE: nodes with section_count ≥ k   ──►  induced core subgraph         │
                       │  (the ~16/84 minority — F1251)                        │                       │
                       │                                                       ▼  mint (0x58 centromere)│
                       │  PROMOTE  → srmech_genome_mint_strand (G5) ──► nuclear core chromosome(s)     │
                       │  MERGE    → srmech_genome_integrate  (G4) ──► core + retained plasmids        │
                       │                                                       │                        │
                       └───────────────────────────────────────────────────────┼────────────────────┘
                                                                                ▼
                                                            ORGANIZED genome (nuclear core + plasmids)
       add one doc  ──►  stage-1 append (1 chromo)  +  count bump (O(section))  +  re-integrate CORE DELTA
                          ── never re-extracts, never a global recursive_cut ──
```

Invariants: (a) each section is extracted ONCE and appended; re-encode = re-ORGANISE, never re-extract
(F1247 at the graph-L layer). (b) The tick fires between whole SECTIONS → cancel truncates at a valid
chromosome boundary. (c) All arithmetic integer/exact (Class-N) — no `abs()`, no float, closed-form.

### Stage / biology / cost table

| stage | op | biology (F1251, attested) | cost | on-disk |
|---|---|---|---|---|
| **1 EXTRACT** | per-doc local co-occurrence → 1 plasmid chromosome, appended | plasmid / accessory genome — accrete per HGT-acquisition event | O(doc) each; **O(\|E\|) total** streaming | append-only `sections/` (genome-native) |
| **2 ORGANIZE** | conservation read → mint core → integrate | nuclear-core formation via `integrate`/HGT; ~16/84 minority | O(section) per add; core-delta re-mint | organized genome dir |
| *(old)* | `genome_from_graph` → `recursive_cut` on 39 M edges | — (a monolith biology never builds) | **O(\|E\|·log n) from scratch, EVERY re-encode** ← the 3.4 h blind block | loose 916 MB JSON |

---

## 2. Derivations (science-derived, not menu)

### D1 — the plasmid-section boundary (Q1)

**Derived: one section = one ingest unit (document; a batch only when docs are tiny — a knob, not a
semantic).** *Not* a participation-derived unit. Reasoning: F1250 participation is a **global** read (it
needs the whole periphery to see the nuclear cliques), so it is **unavailable at extract time** — the very
global structure the two-stage exists to avoid computing. Co-occurrence, by contrast, is **inherently
local** (a window inside one document): a document's co-occurrence subgraph is COMPLETE and self-contained
at extract time — you never need another document to compute it. Biology matches: a plasmid is acquired as
a *unit* (one HGT event ≈ one document's worth of relationships). So the **participation/antimode split is
DEFERRED to organize-time** (D2); the extract-time key is provenance (the doc boundary).
**Falsification:** if a corpus arrives as a provenance-less edge dump with no doc boundaries, this key is
unavailable and the cold-start fallback (recursive_cut, D4) is required — see the riskiest-derivation flag.

**On-disk plasmid-section format (genome-native, NOT loose JSON):** each section is ONE Tier-1 **plasmid
chromosome** — a `graph_to_kernel` strand (kernel-telomere cap `0x6B`, Klein-4 leaves, **no** centromere),
appended to a single `sections/` genome directory via `srmech_genome_append` (§v12: rewrites only the
O(1) HEAD; body = concatenation of self-describing regions; manifest is the re-derivable `.fai` cache).
Edges are stored in **GLOBAL node-ids** (via `graph_to_kernel`'s `node_ids` table) so a word shared across
sections carries the SAME id — the precondition D2 needs to detect conservation. The global word→id vocab
is itself one append-only **vocab chromosome** (the karyotype index) in the same store. Append-only /
streaming falls straight out of the §v12 append contract — this IS `[[feedback_persist_genome_native_not_loose_json]]`
one layer up.

### D2 — the incremental organize/integrate rule (Q2)

**Conservation criterion (derived):** a node is CONSERVED iff its **section-occurrence count ≥ k** — the
number of distinct sections it appears in. This is the section-level, extract-time-available analog of
F1250 cross-community participation, computed as a plain **integer accumulator** (no spectral solve).
HIGH section-count = shared across many plasmids = the conserved core = **NUCLEAR**; count == 1 = accessory
= stays **PLASMID**. Expect the ~16/84 asymmetric minority (F1251) — the conserved core is small.

**Incremental update rule.** Maintain `section_count[node]` (int vector) + the current nuclear-core
node-set. On a NEW section:
1. append it (stage 1);
2. `for node in section: section_count[node] += 1`  — **O(section)**;
3. any node crossing `k-1 → k` is newly-conserved → add to the core node-set; add the new section's edges
   with both endpoints in the core to the core subgraph;
4. re-mint ONLY the affected nuclear-core chromosome (or `integrate` the newly-conserved delta into it).
   Every plasmid section and the unaffected core stay byte-untouched.

**Why it beats from-scratch `recursive_cut` asymptotically.** From-scratch = O(\|E\|·log n) spectral
bisection over ALL edges, re-run on the WHOLE graph every re-encode → adding D docs costs
**O(D·\|E\|·log n)**. Incremental = O(section) count bump + O(core-delta) re-mint per doc; the global
spectral solve is **never run** → adding D docs costs **O(Σ section sizes) = O(\|E\|) total**. A factor
~D·log n win, and — the load-bearing point — it is INCREMENTAL: append a doc → touch only that doc + the
core delta. There is no monolithic block left to be blind inside.

**Reuse vs new (derived):** `integrate` (F1244) is the SPLICE **primitive** — reuse it as the MERGE
mechanism. `mint_strand` (F1249) is the PROMOTE **primitive** — reuse it to mint the conserved core. The
conservation read + core-delta orchestration is NEW → a **new `genome_integrate_plasmids`** that composes
`section_count` (new, integer) + `mint_strand` + `integrate`. Do **not** overload `integrate` (keep the
primitive clean) and do **not** overload `genome_from_graph` (that stays the monolithic fallback, D4).

### D3 — the C-native path (Q3)

The whole pipeline runs on a bare-C host. **Existing C peers that compose in** (verified in `srmech.h`):
`srmech_text_cooccurrence_topk` / `_topk_extract`, `srmech_graph_kernel_encode`, `srmech_genome_append`
(§v12 O(1)), `srmech_genome_centromere`, `srmech_genome_save`, `srmech_sha256_hex`. **New C entries
required:**

| C entry | rc | composes | ~lines |
|---|---|---|---|
| `srmech_genome_integrate` (G4) | rc276 | pure block splice at a boundary cap; width-coherence equality gate (Class-K), `*integrated_out=0` on decline | ~40 |
| `srmech_genome_mint_strand` (G5) | rc277 | data-turn scan → `centromere_at` midpoint → `srmech_genome_centromere` cap → single-block insert | ~50 |
| `srmech_genome_plasmid_extract` (stage 1) | rc278 | `…cooccurrence_topk_extract` → `…graph_kernel_encode` → `…genome_append` (thin orchestrator; may be Python-orchestrated over the 3 C peers + a convenience C entry) | ~35 |
| `srmech_genome_integrate_plasmids` (stage 2) | rc279 | section-count integer read + `…mint_strand` (G5) + `…genome_integrate` (G4) | ~55 |
| `srmech_laplacian_recursive_cut` (G1) | rc280 | fallback partitioner; PAL tome I/O + loops `fiedler_sparse_file` | ~55 (largest) |

Each: `srmech_status_t`, caller-arena out buffer, C↔Python byte-parity, JPL-clean (≤60 lines, ≥2 asserts,
no goto/malloc, **never `abs()`** — sign/gate is a Class-K equality read; counts are cardinalities, no sign
to strip), closed-form/no-external-math.

**§101 hook points (rc275 threaded through both stages).** Both stages are loops over whole SECTIONS, so
the `srmech_progress_tick_cb_t` heartbeat fires **between complete sections** → cancel truncates at a valid
chromosome boundary → a valid partial store / organized genome. Stage 1: `done = sections_extracted`,
`total = n_docs`, **phase `SRMECH_PHASE_EXTRACTING`** (append one enum value — additive, no ABI bump).
Stage 2: `done = sections_integrated`, `total = n_sections`, phase `SRMECH_PHASE_MINTING`. **This RESOLVES
the parity audit §4 concern** that rc275's pipeline progress on Python-only orchestrators bakes a permanent
C-host hole: once the orchestration is C (rc279/rc280), the pipeline progress/cancel is C-host-REAL, not a
Python-driver hook. Callable-not-a-wire-param (rc273/rc275 lesson) holds: `progress=` is a Python-only
kwarg, absent from every `ToolEntry.parameters`.

### D4 — where `recursive_cut` lands (Q4)

**Derived: DEMOTED from encode load-bearer to FALLBACK.** The two-stage front-loads structuring into
stage-1 sections (each section is already a local community — biology never partitions a monolith), so
stage 2 is merge+promote, not a global spectral solve. `recursive_cut` is then needed only for:
(a) **cold-start** from a legacy provenance-less monolith (one-time; even this is better replaced by
re-extracting per-document); (b) **within-section** sub-partition of a pathologically huge single document
(rare, bounded, small); (c) inside the retained monolithic `genome_from_graph` fallback (D-less edge dumps).
**Revised priority:** the audit ranked G1 "ship first, largest build." The two-stage **inverts** this — G1
`srmech_laplacian_recursive_cut` ships **LAST (rc280)** as the fallback C peer; G4+G5 + the two stage
orchestrators ship first because they are the incremental HOT path. G1 is still required for full C-host
parity (a bare-C host must be able to cold-start), but it is no longer the gate.

### D5 — JSON retirement (Q5)

The loose `simplewiki_directed_sparse_kernel.json` (~916 MB) is a monolithic dense node-table + edge-list,
re-extracted dense→graph-L every re-encode. **Retirement = route each document's bounded co-occurrence
through `srmech_genome_append` into the `sections/` store instead of dumping to JSON.** The genome-native
append machinery already exists (§v12, O(1) head-only), so this is a re-target, not a new mechanism:
node-ids live in the vocab chromosome; edges live as bit-packed Klein-4 kernel leaves (4 symbols/byte —
far smaller than JSON's decimal-int text); the body is content-addressed + self-describing (SSoT); the
manifest is the droppable `.fai` cache. Adding a document appends ONE plasmid chromosome (bounded) + bumps
the head — no rewrite of the 916 MB. **Migration:** a one-time pass re-runs stage-1 extract per document
(preferred, keeps provenance) or reads the legacy JSON once; then the JSON is deleted. This is F1247
(encode once / render on the fly) enforced at the graph-L layer.

---

## 3. The rc breakdown (ordered) + queued-task subsumption

| rc | ships | closes / reframes | kills 3.4 h? |
|---|---|---|---|
| **rc275** | §101 progress primitive (`srmech_progress_ev_t` + tick typedef + `SRMECH_CANCELLED`, ABI 5→6) + the C-REAL hooks only (`fiedler…_progress`, `genome_mint_progress`, Python `progress=` on already-C-reachable ops) | **#886** foundation (folds in; full pipeline-reality completed at rc279/rc280) | de-blinds only (heartbeat + cancel) |
| **rc276** | **G4** `srmech_genome_integrate` C peer — the stage-2 SPLICE primitive (self-contained) | **#891** integrate-C **becomes the stage-2 primitive** | — |
| **rc277** | **G5** `srmech_genome_mint_strand` C peer — the stage-2 PROMOTE primitive | mint_strand gap (audit) | — |
| **rc278** | **Stage 1** plasmid-native sectional store (Python + C `plasmid_extract` orchestrator over existing `cooccurrence_topk_extract`+`graph_kernel_encode`+`genome_append`); **retires the 916 MB JSON** | part of **#890** (encode-chain **REPLACED** by this arc) | — (enables the kill) |
| **rc279** | **Stage 2** `genome_integrate_plasmids` incremental organize (Python + C) — conservation read → mint core → integrate; INCREMENTAL | **#890** encode-chain (core); the two-stage input contract | **★ STRUCTURAL KILL** |
| **rc280** | **G1** `srmech_laplacian_recursive_cut` **fallback** C peer (DEMOTED) + `genome_from_graph` rewired to cold-start/batch fallback; completes **#886** pipeline-progress C-reality | G1/G2 audit gaps, now as fallback | — (block already gone) |
| **rc281** ‖ | **G6** `srmech_genome_amplify` + `srmech_genome_copy_number` C peers | **#889** — **stays STANDALONE**; independent of the arc, may ship in ANY slot / in parallel | — |

Six arc rcs (rc275 foundation → rc280) + one parallel standalone (rc281/#889). Exact numbers are the
conductor's to finalize (rc274 may be in flight) — see fermata F1.

---

## 4. Per-stage build sketches

### 4.1 Stage 1 — `plasmid_extract` (rc278)

```python
def plasmid_extract(tokens, *, section_store, coupling, vocab, window=..., cap=..., k=...,
                    leaf_dim=None, progress=None):        # progress= is Python-only (no wire param)
    """dense/text (one DOC) -> one Tier-1 plasmid chromosome, APPENDED to section_store.
    GLOBAL node-ids via `vocab` so stage 2 can detect conservation. Never re-extracts."""
    ids   = [vocab.intern(t) for t in tokens]                       # append-only global vocab
    edges, weights, charges = cooccurrence_topk(ids, window=window, cap=cap, k=k)  # C: …topk_extract
    chrom, n_syms = graph_to_kernel(len(vocab), edges, weights, charges,
                                    node_ids=sorted(set(ids)),      # the section's node table
                                    leaf_dim=leaf_dim, label=_section_label(section_store),
                                    coupling=coupling)                # C: srmech_graph_kernel_encode
    genome_append(section_store, chrom, coupling)                    # C: srmech_genome_append (§v12 O(1))
    return {"n_syms": n_syms, "nodes": sorted(set(ids))}
```
C entry `srmech_genome_plasmid_extract(...)` chains the three existing C peers with a caller arena; the
tick fires once per call (`EXTRACTING`).

### 4.2 Stage 2 — `genome_integrate_plasmids` (rc279)

```python
def genome_integrate_plasmids(section_store, coupling, *, k, out_path=None, progress=None):
    """ORGANIZE: sections -> minted nuclear core + retained plasmids. INCREMENTAL.
    Conservation = section-occurrence count >= k (integer, no spectral solve)."""
    count = _section_counts(section_store)                 # {node: n_sections}; O(total section mass)
    core_nodes = [v for v, c in count.items() if c >= k]   # the ~16/84 conserved minority (F1251)
    core_sub   = _induced_on(section_store, core_nodes)    # conserved edges among core nodes
    core_chrom, _ = graph_to_kernel(..., core_sub, ..., coupling=coupling)
    core_chrom = mint_strand(core_chrom, coupling)          # PROMOTE  (G5 / 0x58 centromere)
    organized  = core_chrom
    for sec in _plasmid_sections(section_store):           # tick per section (MINTING)
        if progress and progress({...,"done":i,"total":P}): return {..., "status":"cancelled"}
        organized = integrate(organized, sec)              # MERGE (G4) — retained plasmids
    if out_path: genome_save(organized, out_path, coupling)
    return {"strand": organized, "counts": {"nuclear": ..., "plasmid": ...}, "status": "ok"}
```
Incremental variant `add_plasmid(...)`: append (stage 1) → bump `count` over the new section → if any node
crosses `k` re-mint the core delta and `integrate` it; else just `integrate` the new plasmid. **No global
re-solve.** C entry `srmech_genome_integrate_plasmids(...)` composes the rc276 + rc277 peers + the integer
`section_count`; tick per integrated section.

### 4.3 §101 clean-cancel shapes

Stage 1: cancel → the store holds the sections appended so far (each a complete chromosome) + `"status":
"cancelled"`; no half-written section (append is per-chromosome). Stage 2: cancel → `strand` = minted core
+ plasmids integrated so far (a valid shorter organized genome), no `genome_save`. C ops → `SRMECH_CANCELLED`,
out-count = complete sections. Mirrors `telomere_tick`'s honest-decline one scale up.

---

## 5. Parity-gap closures (from the audit) + test shapes

**Closures:** rc276→G4, rc277→G5, rc279 uses both as the stage-2 spine, rc280→G1 (fallback) + G2 rewire,
rc281→G6. The audit's systemic ratchet fix (flag a `composition_of_c` op with non-trivial Python-only glue
and no C entry) should ride rc276 so the class does not recur (fermata F2).

**Registry ripple (per the rc273 Callable + public-callable-ripple-gate lessons):** the new public callables
(`plasmid_extract`, `genome_integrate_plasmids`, and the exposed `mint_strand`/`integrate` C-parity) DO fire
the public-callable gate → regen `carrier_registry.c`, add Rosetta buckets, bump `describe()["tools"]["total"]`
in the five duplicated count-tests, add `ToolEntry` rows + `_native.py` bindings. `progress=` does NOT
(Python-only kwarg, no coercer, absent from `ToolEntry.parameters` — `test_all_param_types_json_coercible`
stays green). New C symbols are additive → **ABI stays 6** (rc275's bump is the only one; new functions
reusing the existing tick typedef do not re-bump per ADR-0007).

**Test shapes:**
1. **Extract-once / append-only (rc278):** append N doc-sections; assert `turns.bin` grows by exactly each
   section's region and prior-section bytes are byte-unchanged (O(1) head rewrite); JSON path gone.
2. **Conservation convergence (rc279) — the ground-proof, NOT a parity test.** On the simplewiki graph,
   assert the section-count≥k nuclear core CONVERGES with (or is a principled superset of) the F1250
   participation-antimode core — a NEW MPM datum, because the two-stage is a *different* (biology-exact)
   encode, not a byte-refactor of `genome_from_graph` (see §6 riskiest). Assert the ~16/84 asymmetry.
3. **Incremental == batch:** `add_plasmid` D times vs one `genome_integrate_plasmids` over the same D
   sections → byte-identical organized genome (the incremental rule is exact, not approximate).
4. **C↔Python byte-parity** for G4/G5/stage entries; run once `HAS_NATIVE=True` and once in a numpy-absent
   forced-pure venv (numpy-free-module discipline).
5. **§101:** monotone `done`, reaches `total`; cancel at X% → clean partial + `status=="cancelled"`, no
   further ticks, no `genome_save`; C op → `SRMECH_CANCELLED`.
6. **JPL-clean:** new C ≤60 lines, ≥2 asserts, no goto/malloc, no `abs()`, no float in the conservation math.
7. **k is derived, not tuned:** a test that pins how `k` is chosen from the section-count distribution (an
   antimode/participation read on the counts, mirroring F1250) — not a magic constant.

---

## 6. The single riskiest derivation

**The conservation criterion (section-count ≥ k) is a DIFFERENT discriminator from F1250's global
participation-antimode, and their equivalence is UNPROVEN.** F1250 measures cross-*community* boundary
participation on the global graph; D2 measures cross-*document* sharing. The two-stage is therefore **not a
byte-equivalent refactor** of `genome_from_graph` — it is a new, biology-exact encode that must earn its OWN
ground-proof (test 5.2: does section-conservation recover the nuclear core the spectral participation read
finds, on the real simplewiki graph?), and `k` must be **derived** from the section-count distribution
(an antimode read on the counts), not hand-tuned. If section-sharing and spectral participation diverge
materially, rc279 produces a genome that differs from the old path — acceptable only if we can show the
divergence is the *biology-correct* one (conserved-core = shared-across-plasmids is the F1251 claim), which
needs the measured convergence check before rc279 is called a "kill," not after. Secondary risk (D1/D4): the
whole ordering-inversion assumes ingest carries document/batch provenance; a provenance-less edge dump puts
`recursive_cut` back on the critical path.

---

## 7. Fermatas (conductor decisions)

- **F1** — exact rc numbers (rc274 in flight?) and whether stage-1+stage-2 Python paths may land in ONE rc
  to kill the block sooner with C parity following (vs the co-equal-per-rc discipline). Leading: keep
  co-equal Python+C per rc (rc278/rc279 split); the discipline outweighs the interim-speed gain now that
  rc275 de-blinds the current run.
- **F2** — scope of the systemic ratchet fix (own rc vs folded into rc276).
- **F3** — the `SRMECH_PHASE_EXTRACTING` enum add (append value = additive, no ABI bump) — confirm the
  phase vocabulary (EXTRACTING for stage 1; MINTING reused for stage-2 organize) vs a separate ORGANIZING.
- **F4** — placement of the convergence ground-proof (test 5.2): a gate ON rc279, or a following
  validation rc. Leading: gate — a "kill" claim needs the measured convergence in hand.
