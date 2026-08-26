<!-- R-RBS-LM audit report. Produced by an 8-agent ultracode workflow (3 inspect / 2 design tracks each
     adversarially verified / 1 synthesis) against the LIVE srmech 0.9.0rc335 native wheel. BOTH design tracks
     scored survives=false on adversarial verification; every correction is applied in-body and the
     track-vs-track disagreements are recorded in §7. Nothing here is a changelog paraphrase — the numbers were
     re-run. User direction 2026-07-24: "pull latest testpypi srmech, introspect and check changelog ... review
     our siona side code for what has been absorbed into srmech and what is deprecated by h_genome carrier and
     the new operational surface ... and for encoding distributed table of contents using same biology cascade
     where maybe the_one can also be the glue". -->

# srmech rc321 → rc335, the h‑genome tower, and what it means for siona

**Ground truth for this report:** `/tmp/srmech_335/bin/python3`, `srmech.__version__ = '0.9.0rc335'`, `native_status() = {'has_native': True, 'dispatching': True, 'abi_version': 10, 'expected_abi': 10, 'native_version': '0.9.0rc335', 'load_error': None}`, `GENOME_FORMAT_VERSION = 19`. Comparison venv `/tmp/srmech_321/bin/python3` (ABI 10 also). siona PATH‑imported from `/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c/docs/srmech/siona`. **Nothing was committed; no file under `docs/srmech/python/srmech` was touched.**

Three inspection tracks fed this report and **two of the three track deliverables failed adversarial verification** (`survives=false`). Every correction is applied below, and every place the tracks contradict each other is called out in §7. Claims I re‑ran myself while writing this synthesis are marked **[DEMONSTRABLE — verified here]**; claims inherited from a track's measurement are **[DEMONSTRABLE — track]**; everything handed forward is **[SPECULATIVE]**.

---

## 1. rc321 → rc335: what broke

### 1.1 The Python surface did not break. At all.

| Axis | rc321 | rc335 | Verdict |
|---|---|---|---|
| Public symbols, package‑wide (`pkgutil.walk_packages` + `dir()`) | 3817 | 3885 | **0 removed**, +68 added [DEMONSTRABLE — track] |
| Tool count (`srmech.describe()['tools']['total']`) | 492 | **509** | **0 removed**, +17 [DEMONSTRABLE — verified here: 509] |
| `SRMECH_ABI_VERSION` | 10 | 10 | unchanged; C wire intact |
| Signatures of the 13 downstream genome ops | — | — | **byte‑for‑byte identical**, defaults included [DEMONSTRABLE — track] |
| Public constants | — | — | exactly **one** changed: `GENOME_FORMAT_VERSION 16 → 19` |
| siona module imports | — | 31/31 OK | no hard import break |

The +17 tools decompose exactly onto the changelog: rc322 `genome_add_fiber / genome_read_fiber / genome_fiber_holonomy` (+3), rc323 `srmech.qm.so9` ×5, rc324 `srmech.amsc.octonion` `{oct_mult, oct_conjugate, oct_bind}` (+3), rc325 the four octonion‑fiber ops (+4), rc328 `mass_normalized_laplacian / cotangent_weights` (+2). 3+5+3+4+2 = 17.

Two things a symbol‑set diff **misses** and you should know about:
- **rc330 added 5 `CDRegister` methods** (`add, conjugate, element, multiply, norm`) — instance methods on the object returned by `cd_register(8)`, invisible to a module‑level `dir()` diff.
- **rc327/329/332/333/334 are pure C‑parity work**: 22 new `srmech.amsc._native.*` private probes, ABI unmoved, tool count unmoved. The down‑only ratchet `CEIL_WIRE_GLUE_GAPS` went 9 → 8 → 6 → 4 → 1 → **0**.

### 1.2 The on‑disk story: three bumps, three markers, one‑way per feature

**[DEMONSTRABLE — verified here]** the full marker table on rc335:

```
PACKED_TURN_MARKER            0x51 'Q'   klein4 data turn, 2 bits/symbol
Q8_PACKED_TURN_MARKER         0x38 '8'   Q8 data turn,     3 bits/symbol
OCTONION_PACKED_TURN_MARKER   0x39 '9'   octonion turn,    4 bits/symbol
FIBER_CAP_MARKER              0x46 'F'   Q8 fiber cap      (v17, rc322)
OCT_FIBER_CAP_MARKER          0x4F 'O'   octonion fiber cap(v18, rc325)
CHROMATIN_MARKER              0x48 'H'
OCTONION_SECTORS              0x10 (=16)
```

| Bump | rc | What landed |
|---|---|---|
| v16 → **v17** | rc322 | `FIBER_CAP_MARKER 0x46 'F'` — the ℍ‑rung ordered left‑fold holonomy cap |
| v17 stays 17 | rc323–324 | octonion **carrier** shipped with *no* on‑disk wiring (the deliberate rc311→312 split precedent) |
| v17 → **v18** | rc325 | `OCT_FIBER_CAP_MARKER 0x4F 'O'` |
| v18 → **v19** | rc326 | `OCTONION_PACKED_TURN_MARKER 0x39 '9'` — 𝕆 data turns 4‑bit‑packed; manifest `carrier` gains `"octonion"` |

**Compatibility, measured both directions [DEMONSTRABLE — track]:**

- **Backward: HOLDS.** rc335 reads rc321‑written v16 genomes with no re‑encode, no error, exact recall, for klein4 and Q8 alike. `turns.bin` sha256 unchanged by the load.
- **Forward: BREAKS HARD, per feature not per version.** A klein4 v19 body with no new marker round‑trips through rc321 fine (`recall exact-match: True`) — a v19 body with no new markers *is* a v16 body. But a body carrying `0x46`, `0x4F`, or `0x39` dies in rc321 with `GenomeBoundingError: genome rebuild-by-scan: unrecognised block kind byte 70 at offset 104` / `byte 57 at offset 40`. **That is a scan crash, not a graceful version refusal.** Once you write any of the three new markers, every consumer pinned below rc326 must upgrade in lockstep.

### 1.3 The break that actually bit us is NOT the marker bump

**[DEMONSTRABLE — verified here.]** The real live‑data break is a **manifest key rename**: legacy manifests store the coupling under `data["the_one"]`; rc335's `_resolve_coupling` reads `data["coupling"]` and `KeyError`s. Complete inventory of every genome on this machine — **nine** legacy directories, ~973 MB, not the three one track reported:

```
path (basename)                fv   carrier  leaf_dim   n_turns     bytes    manifest key
knowledge_genome               11   None       256       12,309       871 KB   the_one
.siona_genepool                 2   None        64          327        21 KB   the_one
wiki_tomes_genome               2   None        64          523        33 KB   the_one
sublanguage_genome             11   None       256          231        16 KB   the_one
findings.genome                11   None        64        2,635        45 KB   the_one
responsion.genome              11   None        64        2,223        38 KB   the_one
simplewiki_directed.genome     11   None        64   18,401,391       313 MB   the_one
simplewiki_organized.genome    15   None        64   18,376,459       324 MB   the_one
simplewiki_sections.genome     15   None        64   19,097,380       336 MB   the_one
─────────────────────────────────────────────────────────────────────────────
(srmech's own test fixture)     2   None        16           13       208 B    coupling  ← already renamed
```

All nine fail `genome_load(path)` on rc335. `_carrier_name_from_body(body, leaf_dim)` returns `'klein4'` for all nine, so the "**zero Q8 / zero octonion data on disk**" conclusion does survive — but on evidence, not on an incomplete `find`.

**Struck:** the migration track's "complete inventory … three directories". It was three of nine, and it missed ~972 MB of persistent corpora.

Grep confirms siona has **zero** `GENOME_FORMAT_VERSION` pins, **zero** `format_version` comparisons and **zero** `"the_one"` manifest reads. So no pin needs bumping. One dead parameter needs wiring — and even that is not a blocker (see §2.4 F‑1).

### 1.4 The migration helper is real and misnamed

`srmech.amsc.genome.upgrade_v15_to_v16(path, *, coupling=None) -> dict` is the **only** `upgrade*`/`migrat*` function in the package, and it **stamps v19**, not v16. Measured: `turns.bin` sha256 UNCHANGED, manifest re‑stamped, recall still exact. It is a manifest re‑derive from the body (the §44 SSoT), not a body repack.

**But it has a measured read‑path regression the earlier track missed [DEMONSTRABLE — track‑adversarial]:** it replaces a full manifest (with a `chromosomes` array) with a **head‑only** manifest, so every subsequent `_catalog_data` must stream‑scan the body. On the knowledge genome: whole load 0.350 s → 0.414 s (fine), but **paged** `genome_load(p, labels=['calculus.atan'])` **0.002 s → 0.132 s, a 66× regression**. The paged read *is* siona's F1094 demand‑load rationale. On the 313–336 MB simplewiki genomes that is a seek turning into a full‑body scan.

### 1.5 What the h‑genome tower now IS, as an operational surface

Before rc322 the genome was a *store*: bytes in, bytes out, one algebra. As of rc335 it is a **fibrated bundle whose base and fiber are both on disk in the same file, and whose rung is discoverable by striding one byte at a time**. The base channel (the packed data turns) carries the *content* and is winding‑invariant — a reorder of the turns is invisible to it. The fiber channel (the `0x46`/`0x4F` caps) carries the *ordered left‑fold holonomy* — the walk order the base channel throws away. That is F1301 lodging made literal: the data turns are the operand/relational channel, the eigen‑style read‑outs are the distributional channel, and the fiber cap is the **responsion**. What the tower adds over rc321 is that all three now live in one self‑describing body, and moving up a rung (V4 → Q8 → 𝕆) buys you strictly more order structure at a strictly wider turn: 2 → 3 → 4 bits per symbol, and at 𝕆 an *associator defect* read that has no ℍ analogue.

```
                THE FIBRATED HURWITZ TOWER AS SHIPPED ON rc335
                (one turns.bin, one linear scan, no element_type context needed)

 rung  algebra   ELEMENT_TYPE        data-turn   bits/   on-disk turn @ leaf_dim=64
                                      marker     symbol  (1 marker byte + packed payload)
 ───────────────────────────────────────────────────────────────────────────────────
  0    R / C     KLEIN4   = 0   (V4)  0x51 'Q'     2      1 + 16 =  17 B
                 abelian sign-shadow, sectors {0,1,2,3}
                        ▲
                        │  q8_project_v4(q8_from_one(ONE,D)) == klein4_from_one(ONE,D)
                        │  ← the pi-faithful down-projection, measured EXACT
                        │
  1    H         Q8       = 1        0x38 '8'     3      1 + 24 =  25 B
                 non-abelian, sectors {0..7}, CENTRE = {0,4}, 0 = identity
                 └─ FIBER CAP  0x46 'F'  ordered left-fold holonomy
                        │              genome_add_fiber / _read_fiber / _fiber_holonomy
                        │              read-out: {holonomy, recomputed, consistent, lk_mod2}
                        ▼
  2    O         OCTONION = 2        0x39 '9'     4      1 + 32 =  33 B
                 non-associative Moufang loop, OCTONION_SECTORS = 16
                 └─ FIBER CAP  0x4F 'O'  holonomy + ASSOCIATOR DEFECT
                                       genome_add_octonion_fiber / _read_ / _holonomy
                                       / genome_octonion_associator   (no H analogue)

 CAPS shared by all rungs (always full leaf_dim bytes, inline UTF-8 label):
   0x43 'C' CHROM   0x47 'G' GENE     0x48 'H' CHROMATIN  0x58 'X' CENTROMERE
   0x44 'D' DIPLOID 0x4B 'K' KERNEL-HEADER (READ-ONLY back-compat; not emitted)
   0x6B 'k' KERNEL-TELOMERE   0x74 't' ACTIVE-TELOMERE
   0x62 'b' BOOLEAN-GENE  0x64 'd' GRADED-GENE  0x67 'g' REGULATORY-GENE  0x77 'w' THRESHOLD-GENE

 WHY THE SCAN WORKS WITH NO CONTEXT: data symbols are sectors, always <= 15;
 every marker byte is > 3 and (for the caps) > 0x39. The marker keys the codec,
 so a MIXED klein4 + Q8 + octonion body is walkable end to end.
 CAVEAT: _walk_region_blocks(region, leaf_dim) still REQUIRES leaf_dim, which
 comes from manifest.json. The cap KIND is context-free; the stride WIDTH is not.
```

**The self‑describing claim, precisely scoped.** A real body walk (5 chromosomes, leaf_dim 64, genes + centromere + chromatin + active telomere + both fiber caps → 840 B `turns.bin`) recovered every cap, its kind, and its inline UTF‑8 label in one pass. `manifest.json`'s `carrier` field is derived by `_carrier_name_from_body` from the first packed turn, and stamps `'klein4'` / `'q8'` / `'octonion'` correctly. **But `_carrier_name_from_body` is private and `genome_load` returns only `(strand, coupling, labels)` — no carrier.** Every caller still hard‑codes `element_type=` or hand‑parses the manifest. `hasattr(G,'genome_carrier') → False` **[DEMONSTRABLE — verified here]**.

### 1.6 Two rc335 hazards that are not version deltas but will bite

**Wrong coupling is undetectable on every rung.** `recall` / `partition` / `kernel_unpack` all return garbage with **no error** under a wrong `the_one`, on klein4, Q8 and 𝕆 alike. The klein4 case is structurally undetectable by statistics: XOR‑by‑constant is a Hamming isometry, so the internal similarity structure is *byte‑identical* under right and wrong keys (measured: raw `[0.25,0.5,1.0,0.25,0.25,0.5]`, coupled‑A same, coupled‑B same). `hasattr(G,'genome_verify_key') → False` **[verified here]**.

*Corrected from the TOC track*: "bare srmech has no wrong‑coupling detector at all" is **overstated**. The manifest stores the coupling **verbatim** as hex plus its own sha256, so `bytes(my_coupling) == bytes.fromhex(genome_catalog(path)['coupling']['hex'])` is a one‑line detector available today, and `body_sha256` + `_verify_body_integrity` ship. The real gap is narrower: `genome_load(path, coupling=X)` never compares `X` against the stored sha256 (`_resolve_coupling` returns the override immediately), and `kernel_unpack` decodes `leaf_dim` and `element_type` from the §89 base‑4 header into `_ld, _et` and **discards both**, so an absurd `true_len` degenerates to a silent full‑length read (measured: 256 symbols returned where 200 were written).

**Two distinct modules are now named `octonion`.** `srmech.amsc.octonion` (rc324, new) is the **discrete 4‑bit Moufang loop** `o = (sign_bit<<3)|index` — `oct_mult(4,5)=1`, `oct_conjugate(4)=12`, `oct_mult(4,oct_conjugate(4))=0`. `srmech.qm.octonion` (pre‑existing at rc321) is the **continuous `Mat` surface**. Always write the full dotted path.

**Struck:** rc331's claimed ~0.12 % `One.matrix` ULP change could **not** be reproduced through the Python entry point — 312 matrices from `the_one(σ, tn, td)`, 61,152 cells, **0 differing** rc321‑vs‑rc335, and native‑vs‑forced‑pure also 0 on both. Reported as measured, not as refuted: the fix is real in the C source and the sample may simply not reach the affected dispatch (rc331 explicitly adds `mc_one_matrix` and raises the `make_class` arena floor 65536 → 131072, so the affected route may be the DSL vtable thunk, not the plain function). **Do not trust a pinned golden digest of `One.matrix` output — re‑derive it.**

---

## 2. Siona audit

Four buckets. Every row carries `file:line` and the measurement that puts it there.

### 2.1 ABSORBED — srmech now ships it; our copy can go

| # | siona code | srmech peer on rc335 | Drop‑in quality | Evidence |
|---|---|---|---|---|
| A‑1 | `genome_store.py:124-134 _q8_partition` | `partition(strand, coupling, labels, *, element_type=1)` | **BYTE‑EXACT**, including the `labels` filter and its ordering | both returned `['b','a']` for `labels=["b","a"]`; values bit‑exact. Control: `partition(strand, q8one)` with no kwarg raises `ValueError: hdc.klein4_bind: klein-4 elements must be in {0,1,2,3}` — the shipped op fails loud exactly as our wrapper's docstring promised |
| A‑2 | `photosynth.py:107-135 excite_propagate_harvest` | `srmech.amsc.laplacian.eph_harvest(L, u0, z)` | **SEMANTIC** — identical top‑3 ordering, ~3e‑5 energy gap | siona `[('w0',0.146146),('w2',0.016395),('w3',0.014401)]` vs srmech `[('w0',0.146096),('w2',0.016386),('w3',0.014389)]`. Shipped docstring names our issue verbatim: *"The EPH cascade read (0.9.0rc136; siona gh#1274)"* |
| A‑3 | `infer.py:1414-1444 _k_pack` loose JSON | `graph_to_kernel` / `kernel_to_graph` / `kernel_pack` / `genome_save` / `genome_append_kernel` / `genome_register_attested` / `laplacian.recover_check` | **FULL** — every piece ships | `recover_check` returns `{'ok':True,'op':True,'operand':True,'responsion':True,'curvature':{...'verdict':'carries-direction + curvature (nonzero holonomy)'}}`. siona's own `introspect.py:108-109` PATTERNS already prescribes exactly this and calls loose JSON the anti‑pattern |
| A‑4 | `_native.py:265 cooccurrence_edges` **(qualified)** | `srmech.amsc.text.cooccurrence_edges` | **SET‑EQUAL, NOT ORDER‑EQUAL** | see correction below |
| A‑5 | rbs_lm_research duplicates | `srmech.rbs_lm.substrate`, `srmech.qm.so9.octonion_left_mult`, `hdc.klein4_chunk_bundle` | **NEW WORK ONLY** | see correction below |

**Correction to A‑2's rationale.** The migration track said the ~3e‑5 gap is siona's float‑divided Machin 2π. **That is wrong.** Measured: siona `_TWO_PI = 6.283185307179586`, error vs `math.tau` = **0.0**; srmech `_EPH_TWO_PI = 7595904947272677161575987 / 2^80 = 6.283185307179586`, error vs tau = **0.0**. The 2π constants are bit‑identical as doubles and contribute nothing. The real difference is the **argument‑fold denominator** (siona's magic `1000` vs `_EPH_FOLD_DEN = 2^44 = 17592186044416`) and **series length** (18 vs `_EPH_EXP_TERMS = 24`). Also struck: "it removes the only float‑mid‑cascade and the only magic denominator in the module" — `excite_propagate_harvest_2axis` (`:137-186`), `_crank_cossin` (`~:100`) and `path_emit` (`:218-219`) all keep the same `int(round(...*1000))` and float divides, `1e-9` sits at `:185`, and srmech's own `eph_harvest` runs on `complex()` floats. **This is an ACCURACY win, not a float‑elimination win.**

**Correction to A‑4.** The earlier track called this "bit‑identical". At the 4‑token toy it is. At scale it is not: on 400 docs × 200 tokens, vocab 400, both return 68,732 edges, `set(e1)==set(e2)` **True**, 0 weight mismatches — but **`e1==e2` is False**. siona native returns hash‑bucket order `[(256,341),(256,381),(0,232),…]` with `array('I')` weights; srmech returns sorted order `[(0,1),(0,2),(0,3),…]` with `list` weights. **Any content‑address over the edge list, any `sha256_bytes` over the arrays, or any index‑order‑dependent consumer diverges.** Two further corrections: (a) siona's `_native.cooccurrence_edges` / `_parallel` / `_laplacian` have **zero non‑test callers** — `infer.py:1422` already calls srmech's — so the "hot undirected path" being protected does not exist; (b) the "0.173 s vs 0.292 s" figure was cited with **no generating code** (a computational‑provenance violation) and does not reproduce: re‑measured **siona 0.0547 s vs srmech 0.1097 s (2.0×)**, srmech directed 0.1228 s.

**Correction to A‑5.** `srmech.rbs_lm.substrate` ships **two** word encoders and only one is safe. `encode_word_k4 = hdc.klein4_expand(D, token_seed(word, hex_chars))` — a content‑derived **seed** fed to an expansion, which siona's own `bridge.py:12-17` documents as the recurring defect (*"the RNG's avalanche destroys the content's structure … cat/cats 0.2552 ≈ cat/dog 0.2426 … Third occurrence of this defect — F899 measured it first"*) and which siona already replaced with `klein4_encode_bytes`. **New work must import `encode_word_byteglyph`, never `encode_word_k4`.** File count corrected: **912 `.py` / 2612 total**, not 908.

### 2.2 BLOCKED‑ABSORPTION — technically absorbed, but deleting breaks a green provenance artifact

This is the cross‑track finding the migration plan missed entirely, and it is the reason two of its "zero‑risk" deletions are not zero‑risk.

| siona code | srmech peer | Why it is blocked |
|---|---|---|
| `genome_store.py:82-91 _q8_sign_preimage` + `:94-103 _coupler_q8` | `srmech.amsc.q8.q8_from_one(one, D)` | **Four dependents OUTSIDE the siona package.** `docs/srmech/rbs_lm_research/R-RBS-LM-Q8SUBSTRATEVERIFY_siona_genome_couples_through_the_resonant_q8_substrate_five_checks.py` **runs green on rc335** — `=== ALL FIVE PASS ===`, with check `[4] coupler_q8: deterministic=True pi-faithful=True sign-nontrivial=True (138/256)`. Plus its finding note `R-RBS-LM-FINDING_1307_….md`, `UPSTREAM_NOTES.md`, and the migration note. The earlier grep was scoped to `siona/` only. |
| `genome_store.py:225-241 express()` Q8 `NotImplementedError` | `gene_express(strand, coupling, cell_state, *, element_type=1)` | Same script, check `[5] express/add_kernel Q8 fail-loud (NotImplementedError): True`. Removing the guard turns a green F1307 verification **red**. |

The technical points are both correct: `q8_from_one` is the right peer, and `gene_express(element_type=Q8)` returns `['g1']` bit‑exact on a Q8 strand. But these edits are **provenance edits**, not cleanups: they must land together with an update to the F1307 script and its finding note, and the script must be re‑run.

**On the coupler swap itself:** `_coupler_q8` and `q8_from_one` share the V4 shadow **exactly** (`q8_project_v4(q8_from_one(ONE,D)) == klein4_from_one(ONE,D)` → True; siona's V4‑shadow differing = 0/256) but differ in the **sign channel at 114 of 256 positions**. A cross‑coupler read is **silent garbage, not an exception** (saved with `_coupler_q8`, read with `q8_from_one`, `element_type=Q8` → no error, `bit-exact: False`). Today that is data‑risk‑free because **zero Q8 genomes exist on disk** (§1.3, now on a complete inventory). The moment one is written it becomes a data migration.

**Unstated fact that changes every Q8 risk assessment:** `grep -rn 'ELEMENT_TYPE_Q8\|_coupler_q8\|element_type' siona/tests/*.py` returns **ZERO hits**. The entire §Q8 block in `genome_store.py` is **untested inside siona**; its only green coverage is the external F1307 script that these two edits would break. So the correct safety statement is not "zero Q8 data at risk" — it is *"zero data, zero in‑package tests, one external green artifact that WILL break."*

### 2.3 DEPRECATED‑BY‑H‑GENOME — still runs, but it is a two‑rung stub against a three‑rung package

| siona code | What is deprecated | Evidence |
|---|---|---|
| `genome_store.py:50-51 __all__` | Exports `ELEMENT_TYPE_KLEIN4`, `ELEMENT_TYPE_Q8` and **no `ELEMENT_TYPE_OCTONION`**. `_coupler_for` branches on two rungs only; `_coupler_for(2).sectors → 4` (should be 16). | `hasattr(GS,'ELEMENT_TYPE_OCTONION') → False`. `pack_instrument([...], d, element_type=2)` → `ValueError: q8_bind: a Q8 element must be an int in [0, 8); got 14` — fails loud but with a *misleading* message, because `_q8_chromosomes` hardcodes `ELEMENT_TYPE_Q8`. Proof the rung works one level down: a hand‑minted `sectors=16` coupling round‑tripped a full octonion genome bit‑exact (`carrier='octonion'`, `fv=19`) |
| `genome_store.py:24-33` docstring | **HALF FALSE.** It says `express` and `add_kernel` are klein4‑only *"because gene_express / genome_append have no element_type yet"*. `gene_express` **has one and it works** on rc335. Only the `genome_append` half survives. | `inspect.signature(G.gene_express)` → `(strand, coupling, cell_state, *, element_type=0)` [verified here] |
| `knowledge_genome.py:125,130,131,145,150` | **klein4‑only by omission.** `_GS._coupler()` (hardwired, bypasses `_coupler_for`), then `chromosome(...)`, `genome_save(...)`, `gene_express(...)` — all four take `element_type` on rc335 and **none is passed**. Siona's own self‑knowledge genome can never ride the tower. | source read |
| `introspect.py:33-46 SRMECH_MODULES` | Stale 20‑module hand list. `introspect_srmech() → 431 ops`; `q8.q8_from_one` ABSENT, `octonion.oct_mult` ABSENT, `so9.so9_adjoint_basis` ABSENT, `text.cooccurrence_edges` ABSENT. Adding the four modules → **454 ops (+23)**, all four `True`. | measured. Note the tower *ops* are already visible because `srmech.amsc.genome` and `.laplacian` ARE listed — `genome_add_fiber`, `genome_add_octonion_fiber`, `eph_harvest`, `propagate_wound`, `recover_check` all `True`. The gap is exactly the four new **modules** |
| `bridge.py:5-11` | **One claim refuted, one claim UPHELD.** | see below |

**`bridge.py` — split verdict, this is where two tracks disagree.**

- **Claim 1, "a full byte per 2‑bit Klein‑4 lane (a flat 4× bloat)" → REFUTED.** 20 kernels × D=8192 = 163,840 symbols → `turns.bin` **51,840 bytes = 0.3164 bytes/symbol**. Off by ~12.6×. Delete this claim.
- **Claim 2, "`genome_pack` is O(n²) in chromosome count" → STANDS.** The migration track timed **6** sequential `add_kernel` calls, saw `[0.0195…0.0217]` s, and called it flat. A longer window refutes that: **160** sequential appends on one genome give per‑quartile means **0.01797 / 0.02613 / 0.04018 / 0.05466 s** — 3.0× growth, monotone. Per‑append cost is linear in chromosome count, so cumulative append is O(n²). Also `hasattr(srmech.amsc.genome,'genome_pack') → True` — the named op still exists. **The bridge.py caveat is TRUE on rc335. Do not delete it; file it upstream.**

**A second measured strike against the "derived by scanning" O(1) claim:** `_catalog_data` is reparsed on **every** `genome_genes` call and is linear in chromosome count. Re‑measured on rc335 (`turns.bin` reproduces exactly at 61,100 / 244,400 / 977,600 B): N=100 `genome_genes` 18.65 ms of which `_catalog_data` 14.64 ms (79 %); N=400 70.43 / 35.35 ms (50 %); N=1600 176.20 / 143.96 ms (82 %). The earlier "~88 %" single figure is **timing noise — struck**. The durable finding is the **O(N) reparse**, which makes a TOC walk over every chromosome **O(N²) at corpus scale**.

### 2.4 BROKEN‑ON‑RC335

| # | Site | Symptom | Corrected severity |
|---|---|---|---|
| B‑1 | `genome_store.py:185,197` — `load_instrument`/`load_kernel` accept `the_one=` and **never pass it**: `strand, one, labels = _G.genome_load(str(path))` | `KeyError: 'coupling'` on all nine legacy genomes | **MINOR / PERFORMANCE, not BLOCKER** — see below |
| B‑2 | Legacy manifests key the coupling as `the_one`, not `coupling` | `genome_load(path)` with no override cannot read any of the nine | Real, but the remedy is **not general** — see below |
| B‑3 | `introspect.py:103` PATTERNS prescribes `srmech.amsc.text.tokenize` | `hasattr → False` [verified here]. Real surface: `{cooccurrence_edges, cooccurrence_topk, fold_marks, glyph_stream}` | **REPOINT, not delete** — see below |
| B‑4 | `introspect.py:106` PATTERNS prescribes `graph_to_kernel(..., the_one=COUPLE)` | `TypeError: unexpected keyword argument 'the_one'` — the param is `coupling=`. Verified signature: `graph_to_kernel(vocab_size, edges, weights, charges=None, *, node_ids=None, extras=(), leaf_dim, label, coupling)` [verified here] | **second phantom in the same attested string** |
| B‑5 | Reserved‑name leak: `the_one=` is a **coupling** kwarg at 9 non‑test sites (`genome_store.py:154,179,193,205,244`; `corpus_store.py:43,67`; `introspect.py:106`; `infer.py:415`) | None is the σ,θ resonant generator | srmech's own manifest rename `the_one → coupling` **IS this discipline applied upstream** |
| B‑6 | `knowledge_genome.py` `build_regulatory` / `express_relevant` | Path‑collision hazard with `load_or_build` | **DEAD CODE, not a live collision** — see below |
| B‑7 | rc335 upstream bug: `genome_append_kernel → genome_window → kernel_unpack` | Appended D=8229 to a leaf_dim=256 genome; `genome_window` returned 34 leaves, `kernel_unpack` returned **8704** symbols, **no exception**. 475 phantom trailing symbols | `genome_window` strips the `KERNEL_TELOMERE` that discriminates the §89 header, so `kernel_unpack` falls back to the §60 `D = n_leaves × leaf_dim` rule. `kernel_pack → kernel_unpack` direct round‑trips 8229 exactly |
| B‑8 | rc335 native/pure parity break: `genome_genome_genes_c` **silently ignores its `coupling=` override** | `raw [0,3,2,1,0,3,2,1]` / native‑right same / **native‑WRONG same** (should be garbage) / pure‑WRONG `[3,2,1,1,3,2,0,2]` / native‑WRONG‑with‑manifest‑REMOVED `[3,2,1,1,3,2,0,2]` | Deleting `manifest.json` makes native agree with pure — localises the cause exactly. The docstring claims a *"byte‑identical C peer"*. **Consequence: a genome whose manifest is swapped is read with the swapped key by the native path, with no error** |

**B‑1 re‑graded.** The migration track called this "(BLOCKER) … the whole live‑data break". **It never reaches a user on the shipped path.** (a) `introspect.py:287` calls `load_or_build` inside `try: … except Exception: kg = {}` — the `KeyError` is swallowed and Siona re‑encodes live. (b) Decisively: `~/.cache/siona/knowledge_genome.srmech_version` contains `0.9.0rc230:0a108220da5c0818` while `K._stream_version()` now returns `0.9.0rc335:6a82f361cf481f99`, so `fresh=False` and `load_or_build` calls `build()` — which **overwrites the cache** — before `load_instrument` is ever reached. The symptom today is a **silent ~214 s re‑encode**, not a crash. The two‑line fix is still correct and should land; it is not a blocker.

**B‑2 remedy is not general.** "Pass `coupling=` and `_resolve_coupling` returns the override before touching the manifest, so risk is none" is **false in general**. Measured: `genome_load('/home/skirklan/corpora/wikipedia/simplewiki_organized.genome', coupling=<stored hv>)` → `KeyError: 'coupling'` at `genome.py:8423` inside `_catalog_data`, which runs **before** `_resolve_coupling` and reads `head["coupling"]["hex"]` **unconditionally** for head‑only (no `chromosomes` array) manifests. Same for `simplewiki_sections.genome`. `simplewiki_directed.genome` fails differently: `MPRValidationError: attestation.source_doi is required and must be a non-empty string (got '')`. **The remedy fixes 6 of 9, not the class.**

**B‑3 repoint, not delete.** `siona._native.tokenize('Hello, world. Foo') → ['hello','world','foo']` ships, is native‑backed, and is parity‑tested at `tests/test_native_parity.py:68-74`. The `srmech.amsc.text.tokenize` reference is the **sole** occurrence in the tree and it sits inside a PATTERNS prose string, so no caller breaks — this is a docstring correction. Every *other* srmech op named in that string exists on rc335 (`cooccurrence_edges`, `glyph_stream`, `graph_to_kernel`, `genome_append_kernel`, `recover_check_structural`) — **except** the `the_one=` call‑form of `graph_to_kernel` (B‑4). **Two hallucinated call‑forms in one attested self‑knowledge string, not one.** Re‑audit the whole PATTERNS tier by *executing* every prescribed call, not by spot‑checking names.

**B‑6 re‑stated.** `_default_cache_path()` is defined at `introspect.py:262` and reaches exactly one call site, `introspect.py:287 → load_or_build`. `build_regulatory` / `express_relevant` have **no caller in the shipped package** (grep finds only `siona/tests/test_synthesis_wiki_kernel_trig.py:501`, in a tmpdir). The collision is **hypothetical**; the regulatory path is dead code with a latent hazard if wired up. The cited fix sites `knowledge_genome.py:53,131` are mislabeled — neither line names a default path.

### 2.5 STILL OURS — no srmech peer, and mostly should not get one

| siona code | Why it stays |
|---|---|
| `genome_store.py:113-121 _q8_chromosomes` | `genome(kernels, one, element_type=et)` → `TypeError`; `genome(kernels, q8one)` → `ValueError: hdc.klein4_bind…` — it does **not** infer the carrier from `coupling.sectors`. Generalise to `_tower_chromosomes(kernels, one, element_type)` (the loop over `chromosome(..., element_type=)` is verified correct on all three rungs) but **cannot delete** |
| `genome_store.py:256-261` `add_kernel`'s Q8 guard | `genome_append` has no `element_type` and hard‑fails on Q8/𝕆 turns |
| `genome_store.py:264-267` alignment guard | **Do NOT delete** — B‑7. It currently fails loud and correctly (`ValueError: add_kernel: D=8229 is not a multiple of leaf_dim=256`) where the shipped path over‑reads silently |
| `corpus_store.py:59-89` `_adjacency` / `build_reads` | Per‑token **directed** adjacency with a per‑view charge flip; `adj.bin` (`'<iii'` = neighbour, metric, charge) + `adj.idx` (`'<QI'`). srmech's `write_packed_graph(path, edges, weights)` is *"one 16‑byte record per undirected edge: uint32 u | uint32 v | double w"* — **no charge channel, no per‑token index**, and it feeds `fiedler_sparse_file`, a different consumer |
| `photosynth.py:137-186 _2axis` + `:201-245 path_emit` | **Moved out of the DELETE list.** `propagate_wound` returns `['eigenvalues','harvest_im','harvest_re','sigma_effective','spinor_sign','theta','winding']` — per‑mode winding/θ plus the **aggregate** `e^{-zL}·u0`. It returns **no eigenvectors and no per‑winding‑level node harvest**. siona's SLOW axis (`winding: [(w, [(label, energy)])]`, `:180-186`) is exactly the winding‑stratified partial harvest that `propagate_wound` does not compute, and `path_emit` consumes precisely that. **Adopt `propagate_wound` for the fold; KEEP the grouping loop.** This is a fix, not a delete |
| `story.py:50-79 _betweenness` (Brandes) | `grep -rl betweenness <installed srmech>` returns **nothing** |
| `dataset.py:21-29 _znorm` | no peer |
| `bridge.py:49-68 walk` | de Bruijn (k−1)‑gram successor walk over a **sequence** — a different object from `laplacian.eulerian_circuit(edges, start)` over a **graph** |
| The whole inference/routing/rendering tier: `infer.py` (1449 lines), `register.py`, `couple.py`, `reconstruct.py`, `analytic.py`/`synthetic.py`, `anchor.py`/`sumerian.py`/`asl.py`, `boards.py`, `chirality.py`/`conceptnet.py`/`relate.py`/`sense.py`, `g4.py`, `story.py`, `dataset.py`, `context_shape.py`, `goal_typing.py`/`operand_typing.py`, `graft.py`, `translate.py`, `planner.py`, `cli.py` | They **compose** srmech primitives rather than reimplement them (`register.py:34` → `hdc.klein4_similarity`; `couple.py:77-131` emits `(vocab, edges, weights)` for a signed Class‑L eigendecomposition; `translate.py:23` imports `srmech.rbs_lm.substrate`; `planner.py:33-51` graph‑searches `carrier_ladder_descriptor`). No peer, and none wanted |

---

## 3. The migration plan

**Gate discipline.** The siona pytest suite is **not** a per‑step gate: 79 tests collected, **did not complete in >40 minutes** on rc335 across three runs, and a single `Grounding()` costs **210.0 s** (509 tools) while most tests build one. Use the fast per‑step probes; run the suite once, overnight, as the final gate.

```bash
export SIONA=/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c/docs/srmech/siona
export PY=/tmp/srmech_335/bin/python3
export PYTHONPATH=$SIONA
export SCRATCH=/tmp/claude-1000/-home-skirklan-GitHub-mlehaptics/ea4e167c-b53e-4b40-9a86-72e117a3818e/scratchpad
```

| # | Step | Files | Gate | Pass criterion | Gated? |
|---|---|---|---|---|---|
| **0** | **Baseline snapshot of all NINE genome dirs.** `sha256(turns.bin)` + `manifest.json` bytes, copied to scratch | — | `find /home/skirklan -name turns.bin \| xargs sha256sum` | nine digests recorded (~973 MB — check disk first) | no |
| **1** | **B‑1** wire `the_one=` into `load_instrument`/`load_kernel` — **and rename it `coupling=` in the same edit (B‑5)** | `genome_store.py:185,197` | `$PY -c "import siona.genome_store as GS,json;from srmech.amsc import hdc as H;p='$HOME/.cache/siona/knowledge_genome';h=json.load(open(p+'/manifest.json'))['data']['the_one']['hex'];print(len(GS.load_instrument(p,coupling=H.HV.from_sequence(bytes.fromhex(h)))))"` | prints `373`, no `KeyError` | no |
| **2** | **B‑5** rename `the_one=` → `coupling=` at the remaining 7 non‑test sites | `genome_store.py:154,179,193,205,244`; `corpus_store.py:43,67`; `infer.py:415` | `grep -rn 'the_one=' $SIONA/siona/*.py \| grep -v test` → only genuine σ,θ generators | 0 coupling‑sense hits | no |
| **3** | **B‑3/B‑4** repoint `introspect.py:103` → `siona._native.tokenize`; fix `:106` `the_one=` → `coupling=`; then **execute every call in the PATTERNS tier** | `introspect.py` | a script that runs each prescribed call form | all resolve, no `AttributeError`/`TypeError` | no |
| **4** | **§2.3 docstring corrections**: `genome_store.py:24-33` (half false), `bridge.py:5-11` (delete the 4× bloat claim, **KEEP the O(n²) caveat** and cite the 160‑append measurement) | 2 files | `grep -c "flat 4×\|no element_type yet" $SIONA/siona/*.py` → 0 | 0 | no |
| **5** | **A‑1** delete `_q8_partition`, call `partition(..., element_type=)` | `genome_store.py:124-134,187,199` | Q8 `chromosome`→`partition` round‑trip | `key order equal: True`, `values bit-exact: True` | no |
| **6** | **F1307 co‑landing**: update `R-RBS-LM-Q8SUBSTRATEVERIFY_….py` checks [4] and [5] + the finding note, **then** swap `_coupler_q8 → q8_from_one` and drop `express()`'s Q8 guard. **Add in‑package Q8 tests first — there are currently zero.** | `genome_store.py:82-110,225-241` + 2 rbs_lm files | re‑run the F1307 script; `$PY -c "…GS._coupler_for(1,256) == q8.q8_from_one(GS._ONE,256)"` | script green again; `True`; Q8 `pack_instrument`→`load_instrument` bit‑exact | **USER‑GATED** — this edits a committed provenance artifact. Re‑run the §1.3 inventory first to confirm still zero Q8 on disk |
| **7** | **§2.3** add `srmech.amsc.{q8,octonion,text}` + `srmech.qm.so9` to `SRMECH_MODULES` | `introspect.py:33-46` | ops count + membership | `431 → 454`; all four ops `True` | no |
| **8** | **Knowledge‑genome rebuild** (step 7 changes `_stream_version` → cache invalidated) | `~/.cache/siona/knowledge_genome` | build to a **NEW path**, diff against the snapshot | new genome builds; old dir untouched | **USER‑GATED** — mutates the live cache in place if you don't redirect the path. Budget ≥210 s + encode |
| **9** | **A‑2** `photosynth` → `laplacian.eph_harvest` (state the correct rationale: fold denominator + series terms, **not** 2π) | `photosynth.py:107-135` | top‑3 label ordering identical | same order (energies differ ~3e‑5 by design) | no |
| **10** | **§2.5** `_2axis` adopts `propagate_wound`'s fold; **keep** the grouping loop; adapt `path_emit` | `photosynth.py:137-245` | golden‑compare `path_emit(...)["path"]` on ≥5 fixed queries | identical path lists | no |
| **11** | **A‑3** `_k_pack` → genome‑native | `infer.py:1414-1444` | `graph_to_kernel`/`kernel_to_graph` + `recover_check` | `{'ok':True,'op':True,'operand':True,'responsion':True}` | no |
| **12** | **A‑4** route **directed** co‑occurrence to srmech; leave siona's native op in place unused or delete it (**zero non‑test callers**) | `_native.py:265` callers | edge‑**set** equality + weights; assert charges non‑empty | `set(e1)==set(e2)` True, 0 weight mismatches. **Do not assert list equality** | no |
| **13** | **TOWER** `_tower_chromosomes` + `ELEMENT_TYPE_OCTONION` + a real 𝕆 coupler | `genome_store.py` | all three rungs `reload bit-exact` | True ×3 | **USER/SUBSTRATE‑GATED** — the choice of `one` at `sectors=16` is not a refactor decision |
| **14** | **FINAL** full suite | — | `cd $SIONA && PYTHONPATH=$PWD $PY -m pytest siona/tests -q` | green | allow ≥1 h |

### Steps that were in the earlier plan and are now REMOVED or re‑scoped

- **~~Re‑stamp `~/.cache/siona/knowledge_genome` to v19~~ — DROPPED.** `pack_instrument` overwrites an existing dir in place with **no error and no backup** (measured). The stale `.srmech_version` guarantees the next `Tooling()` rebuilds over it. The re‑stamp destroys the only rc230‑era encoding to produce an artifact with a **~214 s life expectancy**.
- **Re‑stamping any of the other eight is USER‑GATED and must be preceded by a paged‑read measurement.** `upgrade_v15_to_v16` converts a full manifest to head‑only; measured paged `genome_load(p, labels=[one])` regressed **0.002 s → 0.132 s (66×)** on the knowledge genome. On the 313–336 MB simplewiki genomes that is a full‑body scan per paged read.
- **The stored coupling is a DRAWN magic number, so re‑encode beats upgrade.** Both live genomes were minted with the deleted `klein4_random(seed=0)`; `stored == siona _coupler(ld)` → **False**. Evidence the earlier track's histogram argument needs replacing: its headline "261× separation" **does not reproduce** — over the whole genome (n = 3,055,616) stored gives `[0.22965,0.24454,0.24707,0.27875]` (sum‑sq dev 1.279e‑3) and siona's `_coupler` gives `[0.24872,0.25113,0.24742,0.25273]` (1.70e‑5), a **75× separation, not 261×**; the 261× came from an unstated ~1/6 subset. **Direction survives; the number is struck.** A cheaper and stronger discriminator that the audit missed: the two stored couplings are **prefix‑identical across different widths** (the 64‑byte genepool coupling == the first 64 bytes of the 256‑byte knowledge‑genome coupling) and both self‑verify against their stored sha256 — the signature of one deterministic seed‑0 stream truncated at two widths. That confirms `klein4_random(seed=0)` provenance directly, and it means **re‑encoding with the resonant `_coupler` — not upgrading — is the discipline‑correct move.**
- **~~"F‑7 both stamp the same file"~~ — struck** (B‑6: dead code, hypothetical collision).
- **~~Delete the `add_kernel` alignment guard~~ — struck** (B‑7).
- **~~Rewrite the rbs_lm_research duplicates~~ — struck.** 912 files of computational‑provenance artifacts. Only new work imports the shipped ops, and only `encode_word_byteglyph`.

---

## 4. The distributed table of contents

### 4.1 The problem the TOC solves, and the one it does not

srmech already self‑describes **which algebra a turn is written in** — the marker byte does it with no context, and the manifest's `carrier` is derived from a body scan. srmech does **not** describe **which cascade turns those symbols back into meaning**. `recall()` hands you `[0,1,2,3,…]` and never says whether those are ASCII bytes, glyph codepoints, a Laplacian adjacency, or an ASL handshape index.

> **carrier** = what alphabet the turn is written in → already shipped, in the marker.
> **cascade/recipe** = what op‑chain renders that alphabet to meaning → the TOC's job.

### 4.2 What ships, and the layout

Zero new files. One `0x67` REGULATORY‑GENE cap plus one ordinary coupled data turn, **per chromosome**, in the promoter position. The corpus‑wide TOC is *derived* by scanning, the way srmech already derives its `chromosomes`/`regions` arrays.

```
 ONE CHROMOSOME WITH A TOC PROMOTER (leaf_dim = 128)

  turns.bin ──────────────────────────────────────────────────────────────────
   0x43 'C'  CHROM cap        label "doc_A"            128 B
   0x67 'g'  REG-GENE cap     label "toc/k4-ascii@1"   128 B   ← the TOC entry
             ├─ activator mask  uint64 BE   ┐ INLINE, UNCOUPLED, 8 B each,
             └─ repressor mask  uint64 BE   ┘ packed into what was NUL padding
   0x51 'Q'  packed turn      the TOC RECORD leaf       33 B   ← coupled
   0x47 'G'  GENE cap         label "data/0"           128 B
   0x51 'Q'  packed turn      payload                   33 B
   ...
  ──────────────────────────────────────────────────────────────────────────────

 THE TOC RECORD LEAF  (base-4, big-endian, same convention as srmech's own
 §89 kernel header; verified _uint_to_base4(200,8) == [0,0,0,0,3,0,2,0])

  field      syms  bits  meaning
  --------   ----  ----  --------------------------------------------------------
  magic         8    16  0x70C — wrong-key / not-a-TOC detector
  version       4     8  TOC leaf version (2)
  recipe_fp    32    64  THE GLUE — ClassA(recipe_canon || ClassA(the_One))
  carrier       4     8  element_type of the DATA genes (0/1/2)
  n_data        8    16  how many data genes this recipe consumes
  param_fp     32    64  ClassA of the canonical params blob
  order_fp     32    64  THE RESPONSION — ClassA of the ordered fiber holonomy
  --------   ----  ----
              120   240   then Klein-4 zero-pad to leaf_dim  (needs leaf_dim >= 120)

 The record is KLEIN-4 VALUED on every rung — symbols 0..3 are legal turns for
 klein4, Q8 and octonion alike, so one codec indexes the whole tower.
 [DEMONSTRABLE] on the Q8 chromosome: TOC leaf max symbol = 3.
 That is a deliberate commitment: the TOC record IS the abelian shadow of the
 strand it indexes — which is exactly why it needs the order_fp lift, and
 exactly why §4.5 kills it.
```

The glue derivation, all inputs declared, no RNG / seed / clock / path:

```python
one_tag(one)      = sha256( json({"sigma":σ, "theta":[n,d], "terms":t}, sorted, compact) )
recipe_canon(r)   = json({"carrier":…, "name":…, "ops":[…], "version":…}, sorted, compact)
recipe_fp(r, one) = int.from_bytes( sha256( recipe_canon(r) || one_tag(one) )[:8], "big" )
```

`the_one` serialises to exactly three integers (`{'sigma':1,'theta':[0,1],'terms':24}`), so `one_tag` is a Class‑A content‑address of a resonant generator. The discipline sweep is clean: no `abs()`, no numpy, no `fractions`, no `random`, no `seed`, no clock in either prototype file.

### 4.3 The read algorithm — CORRECTED

```
SCAN      genome_catalog(path)         -> labels + byte ranges + carrier + coupling hex/sha
                                          (no leaf decoded)
PAGE      genome_genes(path, label)    -> region-scoped read of ONE chromosome
                                          ** THIS is the RAM-bounded path **
                                          ** it has NO capability gating **
                                          ** and it costs O(N chromosomes) per call **
GATE      gene_express(strand, one, cell_state)
                                       -> a READ-TIME FILTER over an ALREADY-LOADED strand
                                          (shipped docstring's own words)
                                          ** it is NOT a demand-load **
IDENTIFY  for each expressed gene labelled "toc/":
              unpack_toc_leaf(leaves[0])
              magic   != 0x70C  -> TocError  (wrong the_One, or not a TOC leaf)
              version unknown   -> TocError
              carrier not 0/1/2 -> TocError
DISPATCH  fp = record.recipe_fp
              fp not in reader's table          -> TocError, NO FALLBACK RENDERER
              param_fp(params) != record        -> TocError
              len(data)        != record.n_data -> TocError
              order_fp(data)   != record        -> TocError   <-- THE LIFT GATE (BROKEN, §4.5)
          renderer(data_leaves, params)
   [struck] recipe.carrier != record.carrier -> UNREACHABLE. `carrier` is inside
            recipe_canon and therefore inside recipe_fp (verified:
            fp(carrier=0)=0xD1069051B86620C4 vs fp(carrier=1)=0x73F7CAD312FE081C),
            so a matching fp implies a matching carrier. The branch can only fire
            on a 64-bit collision, and it has never been exercised.
```

**Three load‑bearing corrections to the design as originally written:**

1. **"The gate step *is* the demand‑load; RAM tracks the expressed subset" — FALSE, and inverted.** `gene_express(strand, coupling, cell_state, *, element_type=0)` takes an **already‑loaded in‑memory strand**; its shipped docstring opens *"Cell‑state‑modulated gene expression — a READ‑TIME FILTER (§128/#728; §130/#730)"*. Measured at N=200: `turns.bin` on disk = 90,000 B; `genome_load` returned 1000 turns = **128,000 B of turn payload in RAM**; 200 labels loaded; **then** `gene_express(cell_state=0b0100 GRAPH‑only — a capability this genome does not have)` still returned **200 expressed genes**, because data genes are unregulated and always express. Gating touches only the TOC caps. **Capability gating as prototyped bounds neither disk reads nor RAM.** Making it a real demand‑load requires reading the `0x67` caps' inline masks during the body scan — they are uncoupled and inline, 8 bytes each after the label NUL — and paging only the surviving regions. **That is unbuilt.**

2. **"The TOC record needs the right the_one to read" — FALSE.** `genome_save` writes the coupling **verbatim** into `manifest.json`: `manifest['data']['coupling']['hex']` is the full Klein‑4 coupling leaf (`'020103020102020301030301…'`). Demonstrated end‑to‑end with **no `the_one` ever constructed**: `cpl = bytes.fromhex(genome_catalog('gen/corpus')['coupling']['hex'])`; `genome_genes(..., coupling=cpl)`; `read_toc_entries(...)` → `toc/k4-ascii@1 fp=0x78F44C1F2EF35D89`; render → `'the one is the glue'`. **The three‑trust‑level table collapses to two.** The three channels differ in **forgeability** (label = plaintext hint; masks = plaintext filter; leaf = magic‑checked record), **not in readability**. What is genome‑local is the **fingerprint namespace**, not the content. The property that *does* survive: a TOC cap minted under one `the_one` cannot be replayed into a genome coupled by another — measured, `TocError: UNKNOWN recipe fingerprint 0x78F44C1F2EF35D89`.

3. **"Discoverable with zero out‑of‑band context" — overstated.** `_walk_region_blocks(region: bytes, leaf_dim: int, *, context='genome')` **requires** `leaf_dim`, which in practice comes from `manifest.json`. The marker byte self‑describes the **cap kind** with no context; the **stride width** does not.

### 4.4 What the prototype actually demonstrated — real outputs only

The full driver reproduces **byte‑identically** across processes (`diff` clean, `sha256(turns.bin) = a5b35aee…3500`, `manifest` 1429 B / 1428 B, `turns.bin` 1350 B / 867 B).

**Body scan, no coupling, no manifest** — walking `turns.bin` and reading only the first byte + inline label:
```
@0     CHROM     doc_A
@128   REG-GENE  toc/k4-ascii@1
@450   CHROM     doc_B
@578   REG-GENE  toc/k4-glyphstream@1
@900   CHROM     doc_C
@1028  REG-GENE  toc/k4-ascii@1
```

**Same carrier, different cascade, different renderer** — the whole point in three lines:
```
doc_A: toc/k4-ascii@1       fp=0x78F44C1F2EF35D89 carrier=0 n_data=1 -> 'the one is the glue'
doc_B: toc/k4-glyphstream@1 fp=0x7DFB725736702FC9 carrier=0 n_data=1 -> ['s','a','n','d','r','o','i','n','g',' ','w','a','l','k','s',' ','o','n','e',' ','l','i','n','e']
doc_C: toc/k4-ascii@1       fp=0x78F44C1F2EF35D89 carrier=0 n_data=1 -> 'an older render, superseded'
```

**Fail loud, wrong `the_one`** (the two couplings differ in 97 of 128 slots):
```
gene_express under the WRONG One returned 5 genes with NO error; toc leaf[:12] = [3,1,2,3,3,1,1,3,3,0,1,2]
TOC -> toc: MAGIC mismatch -- read 0xDBD7, expected 0x70C.
control: rendering the wrong-key payload anyway -> UnicodeDecodeError 0xa8 in position 0
```

**Fail loud, unknown recipe** (two‑stage honesty — the *structure* read fine, the refusal is specifically about the recipe):
```
TOC read OK: toc/not-shipped-anywhere@7 fp=0xA1CAD3D11BF55688
TocError: UNKNOWN recipe fingerprint 0xA1CAD3D11BF55688 -- this reader has 2 recipe(s)
          registered under this the_One and none match. Refusing to render (no fallback renderer exists).
```

**Carrier ≠ cascade on the ℍ rung** (Q8 coupling from the shipped `q8_from_one`):
```
q8 coupling sectors = 8 ; TOC leaf max symbol = 3 ; manifest carrier = q8
TOC record = carrier 1  fp=0x547EECAF518734AF   -> dispatch -> 'q8 rung'
klein4 reader -> TocError: UNKNOWN recipe fingerprint 0x547EECAF518734AF
```
*Honest note:* that refusal came from the **unknown‑fingerprint** branch (`R_Q8TXT` was never registered in the klein4 table), **not** from the carrier gate, which is unreachable (§4.3).

**Byte cost — CORRECTED.** Per chromosome the overhead is **161 B flat** (one 128 B REG‑GENE cap + one 33 B packed TOC turn); at 3 chromosomes `867 → 1350 B`. The original extrapolation to 200 chromosomes had **no generating code** and is **struck**. Rebuilt with the prototype's own recipe, `the_one`, leaf_dim and payload:

| N | TOC | `turns.bin` | B/chrom |
|---|---|---|---|
| 3 | off | 867 | 289.0 |
| 3 | on | 1,350 | 450.0 |
| 200 | off | 57,800 | 289.0 |
| **200** | **on** | **90,000** | **450.0** |

**At 200 chromosomes: 90,000 B, 450 B/chrom, overhead 161/450 = 35.8 %** — not the claimed 251,000 B / 1255 B/chrom / ~13 %. Overhead is dominated by the full‑`leaf_dim` cap, so the ratio is set entirely by mean document size: ~36 % at 19‑byte documents, falling below 10 % only past ~1.5 kB/chromosome. The N=3 figures reproduce exactly, which confirms the rebuild is faithful and the extrapolation was simply wrong.

**The reorder demo is weaker than claimed.** `run_toc.py:354` is `shuffled = [ldata[i] for i in (2,0,1,3)]` — an **in‑RAM permutation of a Python list after the read**, never a permutation of bytes on the wire. And `genome_genes` returns labels that already encode order: `['toc/q8-ascii@1','data/0','data/1','data/2','data/3']`. **The demonstrated reorder is detectable from labels alone with no holonomy.** The gate is load‑bearing only against label‑free strands, or a reorder that permutes labels and leaves together — **neither was constructed.**

### 4.5 FALSIFICATION — the lift gate fails, and it fails in exactly the regime we mandate

Per `stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure`: a bit‑exact `op(x)operand` is **necessary but not sufficient**. In F1301 lodging, for a TOC: **op** = the recipe (`recipe_fp`, distributional), **operand** = the data genes (the leaves, relational), **responsion** = the **walk order** (`order_fp`, the eigenvalue‑shaped read‑out).

**v1 was a false shadow, and the measurement killed it:**
```
SHADOW: recipe_fp identical after permutation : True
        param_fp  identical after permutation : True
        n_data    identical after permutation : True
LIFT:   holonomy ordered[:8]  = [3, 2, 0, 0, 4, 5, 5, 3]
        holonomy permuted[:8] = [7, 2, 0, 0, 4, 5, 5, 3]
        order_fp 0xEAE9AFB08EDCFE29  vs  0xEC7C853675245D45   differs: True
CONSEQUENCE: ordered  -> 'the abelian shadow survives a reorder but the walk does not…'
             permuted -> UnicodeDecodeError 0xa1 in position 0   (not even valid UTF-8)
```
Every abelian field matched and the render is not valid UTF‑8. v2 added `order_fp = ClassA(genome_fiber_holonomy(data turns in walk order))` and enforced it in `dispatch`.

**v2 is ALSO a false shadow, in the sparse regime this project mandates. [DEMONSTRABLE — verified here, independently.]**

The original deliverable scoped this risk to "centre‑heavy strands" and declined to run it. The real failure condition is not centre density but **per‑slot support overlap**, because `genome_fiber_holonomy` is a **per‑slot left fold** (`len(holonomy) == leaf_dim`).

I re‑derived the mechanism directly:
```
Q8 centre under q8_mult              = [0, 4]     (40 of 64 pairs commute)
symbol 0 is the IDENTITY
genome_fiber_holonomy([b'\x01\x00\x00\x00', b'\x00\x02\x00\x00']) -> [1, 2, 0, 0]
genome_fiber_holonomy([b'\x00\x02\x00\x00', b'\x01\x00\x00\x00']) -> [1, 2, 0, 0]
                                                   ^^^^^^ IDENTICAL — order-blind
```
**Any two leaves with disjoint non‑zero per‑slot support commute in every slot.** The density sweep (deterministic content‑derived leaves, 4 leaves, 23 perms × 20 trials = 460 perms per row, 128‑slot leaves):

```
 nonzero slots/leaf   density   collision rate over 460 permutations
 ──────────────────────────────────────────────────────────────────
        1              0.8%     460/460  = 100.0%   ████████████████████
        2              1.6%     460/460  = 100.0%   ████████████████████
        4              3.1%     460/460  = 100.0%   ████████████████████
        8              6.2%       0/460  =   0.0%
       16             12.5%       0/460  =   0.0%
       32 / 64 / 128    —         0/460  =   0.0%
```

End‑to‑end through the real gate — four **distinct** sparse klein4 leaves with disjoint support, packed and unpacked via `TOC.pack_toc_leaf`/`unpack_toc_leaf`, then `RendererTable.dispatch`:
```
in-order      -> RENDERED order=0102030
perm (1,0,2,3)-> RENDERED order=1002030   <-- LIFT GATE BLESSED A REORDER
perm (3,2,1,0)-> RENDERED order=3020100   <-- BLESSED
perm (2,0,1,3)-> RENDERED order=2001030   <-- BLESSED
```
**Three different renders, all blessed.** On *dense* text leaves the gate is sound (0 collisions in 40,319 permutations of an 8‑leaf klein4 strand, 0 in 23 permutations of the 4‑leaf Q₈ strand). But project discipline **mandates** sparse storage (`feedback_stay_rbs_hdc_sparse_never_dense`, `feedback_sparse_complete_never_top_k_truncation_at_storage`), so **sparse is the default regime for siona genomes, not an edge case. The v2 TOC is a false shadow exactly where siona will use it.**

**What a v3 responsion must be [SPECULATIVE]:** order‑sensitive **independent of support overlap**. Two candidate shapes, both cheap to test: (i) **position‑tag before folding** — bind turn *t* with a Class‑A content‑address of its index, so every slot carries positional information regardless of the data's support; (ii) **fold across slots rather than within them** — a single left fold over the concatenated stream, which cannot be defeated by per‑slot disjointness. Either is a small change; **neither is written.**

### 4.6 Honest scope — what the TOC does NOT do

- **It does not authenticate.** `recipe_fp` is a content‑address, not a MAC. And it is weaker than first stated: anyone with the **directory** has the One's coupling in plaintext (§4.3 correction 2). It detects accident and mismatch, not an adversary. `feedback_trauma_informed_defensive_scope` — do not read this as a security control.
- **It does not carry the render params.** `pack_toc_leaf` stores only `param_fp`, never the params blob, and `dispatch` requires the caller to *supply* them. Measured against `gen/corpus/doc_A` with only the directory + a registered renderer: `params {'n_syms': 76}` → RENDERED; `{'n_syms': 128}` → `toc: param fingerprint mismatch -- record 0x093536AA2058A6A6`; `{}` → same. **The reader must already know `n_syms=76` out‑of‑band.** Either spill the canonical params blob into a second TOC leaf, or accept that the TOC identifies a cascade without making it runnable.
- **It does not make renders portable.** The reader still needs the renderer *code*.
- **It does not fix `recall`/`partition` carrier blindness.** Both still default `element_type=0`. Only callers going through the TOC path benefit.
- **It does not survive `leaf_dim < 120`.** The v2 record needs 120 base‑4 symbols.
- **The renderers are toys.** Real siona cascades (byte‑glyph, ni‑Vanuatu order‑native base, ASL, Sumerian anchor) are the actual recipe catalog and are out of scope.
- **`order_fp` uses the ℍ rung for everything.** An 𝕆‑carried chromosome should use `genome_octonion_holonomy` plus `genome_octonion_associator` (a non‑associativity read the Q₈ fold cannot see). Not prototyped.
- **Cultural note:** ni‑Vanuatu / ASL / Warlpiri recipes belong to their communities. A `toc/` entry names *how bytes render*; the framework reads that structure only, and the meaning is never framework data.

### 4.7 The remaining falsification queue for the TOC

1. ~~Find a permutation with colliding holonomy~~ — **DONE, it fires at 100 % below 8 nonzero slots per 128‑slot leaf.** Re‑run against any v3 responsion.
2. **Fingerprint collision under a shared One.** Two distinct recipes hashing to the same 64‑bit `recipe_fp` → silent wrong‑renderer dispatch. 64 bits is a birthday wall near 2³² recipes; sweep the real catalog.
3. **The gate is decorative if the carrier lies.** If `manifest.carrier` and the TOC's `carrier` disagree, the TOC refuses — but `recall`/`partition` default to klein4 regardless, so a caller who never consults the TOC gets a silently wrong read.
4. **Capability gating must not be load‑bearing for correctness.** The activator masks are inline and **uncoupled** — anyone can flip them by editing bytes. Test: for every recipe, render under every `cell_state` that expresses it and assert bit‑identical output.
5. **Round‑trip on the real corpus, not the toy.** Everything here is ≤200 chromosomes of synthetic ASCII. `simplewiki_sections.genome` is 19.1 M turns.

---

## 5. srmech asks that fall out

**Not to be filed yet** — the user is holding filings until the srmech worktree deliverables preview. Consolidated and de‑duplicated across all three tracks; every one is measured on rc335.

| # | Ask | Evidence |
|---|---|---|
| **U1** | `genome(kernels, coupling, *, element_type=)` — the last klein4‑hardwired builder | `TypeError`; and `genome(kernels, q8one)` does **not** infer the carrier from `coupling.sectors`, it raises `klein4_bind` |
| **U2** | `genome_append(path, label, leaves, coupling, *, element_type=)` | `TypeError`; hard‑fails on Q8/𝕆 turns |
| **U3** | `graph_to_kernel(..., element_type=)` — **blocks any corpus tower move** | `graph_to_kernel(..., coupling=q8_from_one(...))` → `ValueError: hdc.klein4_bind…` |
| **U4** | `srmech.amsc.octonion.oct_from_one(one, D)` — the missing 𝕆 peer to `q8_from_one` | `srmech.amsc.octonion` exports only `{oct_mult, oct_conjugate, oct_bind}`; no public 𝕆 coupling minter exists |
| **U5** | **BUG:** `genome_append_kernel → genome_window → kernel_unpack` over‑reads to `n_leaves × leaf_dim` **with no exception** | 8229 written, **8704** returned, silent. `genome_window` strips the `KERNEL_TELOMERE` that discriminates the §89 header |
| **U6** | **BUG / parity break:** `genome_genome_genes_c` ignores its `coupling=` override and substitutes the manifest coupling; the pure path honours it. Contradicts the shipped *"byte‑identical C peer"* docstring | 5‑line repro in §2.4 B‑8; deleting `manifest.json` makes native agree with pure |
| **U7** | `genome_carrier(path) -> str`, or a 4th `genome_load` return | `_carrier_name_from_body` is private; `hasattr(G,'genome_carrier') → False` [verified here]. Every caller re‑introduces the out‑of‑band knowledge the self‑describing wire removed |
| **U8** | `genome_load(path, coupling=X)` never checks `X` against the manifest's stored `coupling.sha256`, though both are right there. **Free wrong‑key detection, currently unused** | `_resolve_coupling` returns the override at `genome.py:8870` before the hash check; measured: right‑key sha `7c8975e1…` vs wrong‑key sha `27bfa40e…`, load succeeded silently |
| **U9** | Raise (or return) on out‑of‑range §89 header fields. srmech already computes a three‑field plausibility check and throws it away | Same strand: RIGHT key → `true_len=200 leaf_dim=64 element_type=0`; WRONG key → `true_len=15914530304487944901 leaf_dim=3080050594 element_type=165` — all three out of range. But `kernel_unpack` does `true_len, _ld, _et = …; return flat[:true_len]` and an absurd `true_len` degenerates to a silent full‑length read |
| **U10** | `_catalog_data` must honour the `coupling=` override on the **head‑only‑manifest** branch | `genome.py:8423` reads `head["coupling"]["hex"]` unconditionally, **before** `_resolve_coupling`; breaks the read of both fv15 simplewiki genomes even with a correct override |
| **U11** | `upgrade_v15_to_v16` drops the `chromosomes` array, converting a full manifest to head‑only and regressing **paged** `genome_load(labels=[…])` by **66×** (0.002 s → 0.132 s). It should preserve or re‑emit the catalog arrays | measured on the knowledge genome |
| **U12** | `_catalog_data` is reparsed on **every** `genome_genes` call and is O(N chromosomes) — 14.64 / 35.35 / 143.96 ms at N=100/400/1600, i.e. 79 % / 50 % / 82 % of the call. Ask: an O(1) head lookup or a cached catalog | makes a TOC walk over every chromosome O(N²) |
| **U13** | `genome_append`'s per‑append cost is **linear in chromosome count** (0.01797 → 0.05466 s per‑quartile means over 160 appends), i.e. **O(n²) cumulative**. The docstring's *"DERIVED by scanning the self‑describing body"* does not deliver O(1) in practice | 160‑append sweep; also `genome_pack` still exists on rc335 |
| **U14** | Rename or alias `upgrade_v15_to_v16` — it stamps **v19** | measured; docstring still says "to format v16" |
| **U15** | `kernel_pack` / `genome_append_kernel` take the **string** `element_type='klein4'` while every carrier op takes the **int** `0`. Two `element_type` families coexist (`_ELEMENT_TYPE_CODES == {'klein4':0,'q8':1,'octonion':2}`) — worth an alias or at least a docstring cross‑reference | `inspect.signature` A/B |
| **U16** *(design, recommend AGAINST)* | A first‑class `0x54 'T'` TOC cap marker would make the TOC visible to `genome_census`/`genome_registry` as a distinct `cap_kind`. **Not needed** — the `toc/` label namespace on the existing `0x67` works today, and a new marker is a v19→v20 one‑way door (measured: old readers die with `GenomeBoundingError: unrecognised block kind byte`) | design call |
| **U17** *(feature)* | A **winding‑stratified** harvest peer to `propagate_wound` — it returns per‑mode `winding`/`theta` and the aggregate node harvest, but no per‑winding‑level node harvest, which is exactly what siona's SLOW axis and `path_emit` consume | §2.5 |

---

## 6. Open questions for the expert (F282 — framed as decidable experiments)

**Q1. What is the correct order‑sensitive responsion for a sparse strand?**
*Decidable:* implement both candidates — (i) fold a position‑tagged turn (bind turn *t* with `sha256_bytes(index)` before folding), (ii) fold **across** slots rather than within them — and re‑run the density sweep. **Pass criterion: 0 collisions at 1 nonzero slot per 128‑slot leaf over ≥460 permutations**, where v2 scores 460/460. This is the single highest‑value next measurement and it is cheap.

**Q2. Does the epigenetic gate survive the lift to a sign‑BEARING carrier?**
*Partially answered, favourably.* Same five genes, same `1<<i` activator masks, klein4‑**valued** content, built on klein4 vs Q8: **0 label mismatches across all 32 cell_states**, and `q8_project_v4` of the Q8 expression equals the klein4 expression exactly. So the masks are carrier‑orthogonal *for klein4‑valued content*. **Still open:** sign‑**bearing** Q8 content (symbols 4..7), which this test does not exercise. That is the π‑faithfulness question one rung up, and it is precisely the `bit_exact_is_the_abelian_shadow` gate. *Decidable:* build a Q8 genome whose gene payloads use the high sectors, express under all 32 states, and compare against the V4 projection.

**Q3. Which resonant `one` belongs at `OCTONION_SECTORS = 16`?**
Not plumbing. The genome ops already take `element_type=2` and an 𝕆 genome round‑trips bit‑exact with a hand‑minted coupling, but srmech ships no `oct_from_one`. A wrong‑**side** couple is caught by srmech's `_oct_side_ok` hard assert; a badly **chosen** `one` degrades addressing quality silently. *Decidable:* mint several candidate 𝕆 couplings, and rank them by the read‑independent structure check (Gram/sidelobe + eigenspectrum) *before* any recall number, per `feedback_read_independent_structure_check_first`.

**Q4. Is the corpus store's per‑edge charge the same object as the Q8 fiber sign?**
`corpus_store.py:59-65` already carries a per‑edge sign that flips with reading direction — structurally the same object the V4 couple discards and Q8 restores. *Decidable:* encode one corpus both ways (as `'<iii'` charge records, and as a `0x46` fiber cap), then compare `genome_fiber_holonomy`'s `consistent` + `lk_mod2` read‑out against the charge channel. **The question is whether the holonomy is MEANINGFUL, not merely storable.**

**Q5. Does F1301 lodging actually hold for the corpus store's three read‑outs?**
`laplacian.recover_check(vocab_size, edges, weights, charges=None)` ships, siona's own PATTERNS prescribes it, and grep shows `corpus_store` **never calls it**. *Decidable:* run the ratchet on the real 831k‑vocab genome and report `op` / `operand` / `responsion` individually. Nobody has run it, and it is the honest gate on any re‑encode.

**Q6. Is "index one rung below, honesty check one rung above" the general shape?** [SPECULATIVE]
The TOC record is Klein‑4‑valued while its responsion is read at the ℍ rung. If that split (marker = carrier, base‑4 shadow record = identity, fiber holonomy = responsion) is general rather than a TOC trick, it should apply to the corpus store's directed charge channel, to the melange bridge, and to `recover_check`'s three read‑outs — and it predicts that an 𝕆‑carried structure needs `genome_octonion_associator`, a non‑associativity read with **no ℍ analogue**, in its index. That is a testable consequence, not an analogy. Untested. §4.5 is where it first breaks.

---

## 7. Where the tracks disagreed (recorded honestly)

| Question | Track claim | Verified answer |
|---|---|---|
| How many legacy genomes? | 3 (~890 KB) | **9 (~973 MB)** [verified here] |
| Is siona "broken" by v16→v19? | Recon: "not BROKEN, just blind to the 𝕆 rung" | Both true at different levels — no `format_version` pin exists, **but** the `the_one`→`coupling` manifest rename fails all nine loads |
| Is B‑1 a blocker? | Migration: "BLOCKER, the whole live‑data break" | **MINOR/PERFORMANCE** — swallowed by `except Exception`, and the version‑keyed cache rebuilds first |
| Is `genome_append` O(n²)? | Recon + migration: "retired by the shipped docstring / measured flat over 6 appends" | **STANDS** — 160 appends, 3.0× monotone growth. `bridge.py`'s caveat is correct |
| Is `cooccurrence_edges` bit‑identical? | "Bit‑identical" | **Set‑equal, order‑ and container‑DIFFERENT** at scale |
| Its speed ratio? | 0.173 / 0.292 s (1.7×), no generating code | **0.0547 / 0.1097 s (2.0×)**, code committed |
| Coupler discriminator strength? | 261× histogram separation | **75×** over the whole genome; the 261× came from an unstated ~1/6 subset. Better discriminator: prefix‑identical couplings at two widths |
| TOC leaf confidentiality? | "needs the right `the_one`" | **Coupling ships in plaintext in `manifest.json`** |
| TOC at 200 chromosomes? | 251,000 B / 1255 B/chrom / ~13 % | **90,000 B / 450 B/chrom / 35.8 %** |
| `_catalog_data` share of `genome_genes`? | ~88 % | **79 / 50 / 82 %** — noisy; the O(N) reparse is the durable finding |
| rc331 One.matrix ULP fix? | Changelog: ~0.12 % of cells | **0 of 61,152 cells differ** through the Python entry point. Unresolved — do not trust a pinned golden digest either way |
| Is the `_coupler_q8` deletion zero‑risk? | "zero Q8 genomes on disk, zero risk" | **BLOCKED** — a green committed F1307 provenance script exercises it, and siona has **zero in‑package Q8 tests** |
| `srmech.amsc.text.tokenize`? | "Retire the phantom — no replacement exists" | **Repoint to `siona._native.tokenize`** (ships, parity‑tested). And there is a **second** phantom in the same string: `graph_to_kernel(the_one=)` |

---

## 8. What I would do next, in order

1. **Write the v3 responsion and re‑run the density sweep** (Q1). Until the lift gate survives at 1 nonzero slot per leaf, the TOC is a false shadow in siona's mandated storage regime and should not be wired into `genome_store.py`. Everything else in §4 is sound and can ship behind it.
2. **Take the nine‑genome baseline snapshot** (step 0). ~973 MB; check disk. Nothing else should touch a genome directory until this exists.
3. **Land migration steps 1–5** (the `coupling=` wiring, the reserved‑name rename, the two PATTERNS repoints, the docstring corrections, `_q8_partition`). All no‑gate, all cheap, all reversible, and step 2 closes a reserved‑name leak that srmech already closed upstream.
4. **Re‑audit the whole `introspect.py` PATTERNS tier by executing every prescribed call.** Two phantoms in one attested string is not a spot‑check result; it is a systematic gap in Siona's self‑knowledge, and it is the exact failure class MPM discipline exists to prevent — applied to her own tooling rather than to a citation.
5. **Write in‑package Q8 tests** (currently zero), *then* do the F1307 co‑landing (step 6). The provenance artifact and the siona edit must move together and the script must be re‑run green.
6. **Run Q2's sign‑bearing Q8 gate test.** It is small, and it is the falsification gate standing between us and a tower‑carried knowledge genome.
7. **Re‑encode, do not upgrade, the knowledge genome and `.siona_genepool`** — the stored coupling is a DRAWN `klein4_random(seed=0)` magic number, and `upgrade_v15_to_v16` costs a 66× paged‑read regression. Leave the three simplewiki corpora alone until U10 lands upstream; two of them cannot be loaded with an override at all.
8. **Hold all 17 srmech asks for the worktree deliverables preview**, then file U5/U6 (the two silent‑corruption bugs) first — they are the only two where a downstream caller gets wrong data with no exception.
