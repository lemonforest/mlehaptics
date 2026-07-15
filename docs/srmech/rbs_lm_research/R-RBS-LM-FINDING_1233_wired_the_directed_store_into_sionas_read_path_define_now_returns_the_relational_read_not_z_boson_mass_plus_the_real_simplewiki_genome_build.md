# F1233 — wired the directed Class-L store into Siona's READ path: `define` now returns the relational read ("water — seen with: ocean, steam, liquid…") instead of z_boson_mass. Moves Siona off F1219's CAN'T-TELL. + the REAL simplewiki body instrument built as ONE native genome.

**User (2026-07-15):** *"build the real simplewiki genome and wire the store into Siona's read path."* Both done — the wiring tested + working, the genome building on the full 831k/39M at real scale.

## The read-path wiring (the F1219 fix) — tested, working
F1219 measured Siona at CAN'T-TELL: `define`/`answer` grounded to srmech **TOOLS** (`self.g.ground(text, owner="srmech")`), so "what is water?" → **z_boson_mass** — the corpus store was never in the read path. Fix (additive, guarded):
- **`siona/corpus_store.py`** (new) — loads a directed Class-L corpus genome (the #231 store: `graph_to_kernel` directed Laplacian + a vocab chromosome) with **no external metadata** (self-describing format stops at n_edges; the vocab tail is trimmed to `vocab_size`), builds a token→neighbors **adjacency index** (O(degree) lookup, not O(edges) scan), and answers the **relational read**: what co-occurs with X, metric-ranked, with the charge/direction (→ / ←).
- **`siona/infer.py`** — `Session.corpus` (opt-in, `None` = shipped baseline unchanged) + `Session.load_corpus(genome_dir)`; `_define` now consults the corpus **first** and falls back to the tool-grounding when a token isn't in it.

**Measured (a tiny water corpus):**
| query | baseline (no corpus) | with the directed store |
|---|---|---|
| what is water | `z_boson_mass: Z boson mass…` | `water — seen with: → hot, → ocean, → steam, ← carry, → clear, → essential` |
| what is ocean | — | `ocean — seen with: → water, ← flows, → full, ← river, → salt` |
| what is quantum (out-of-vocab) | `z_boson_mass…` | `z_boson_mass…` (falls back — baseline preserved) |

So Siona's conversational "what is X?" now reads the **directed Class-L relational store** (F1216) instead of collapsing to the coarse-M tool ground — **off the F1219 CAN'T-TELL**. Additive + guarded: `corpus is None` by default, and out-of-vocab tokens fall back to the shipped behavior, so nothing in the rc1 baseline changes until a corpus is loaded (no F1215-style regression).

## The real simplewiki body instrument → ONE native genome
`R-RBS-LM-SIMPLEWIKIGENOME_…py`: the actual #231 target — `simplewiki_directed_sparse_kernel.json` (916 MB, **831,139 vocab / 39,048,148 directed edges**) → one content-addressed genome via the native rc253 store. **BUILT + verified (PASS):**
- **int-cap check PASSED with room:** max node id 831,139, **max metric 193,858, max |charge| 55,174 — all ≪ 2³⁰** — the codec's 30-bit bound (F1227) is comfortable for simplewiki (the flag was right, this corpus is safe).
- **genome = 313 MB (3.07× smaller** than the 916 MB loose kernel), sha `44e7d40895c8…`, built in 1516 s (~25 min). *(Actual 313 MB vs F1227's ~226 MB projection — the projection used the findings corpus's lighter weight distribution; simplewiki weights are larger, so more base-4 digits/edge. Honest: 3.07×, not 4.3×.)*
- `recover_check_structural` PASS + `recover_check_spectral(max_dim=256)` op=True/responsion=True, and a **byte-exact round-trip on ALL 39,048,148 edges + metric + charge + vocab** (True). Relationally queryable: `neighbors('science')` → fiction, technology, computer, university; `neighbors('country')` → subdivision, united, music. The whole simplewiki body instrument is ONE integrity-checked native genome.

## LIVE demo — `define` over the real simplewiki store (`R-RBS-LM-SIONALIVE`, PASS)
`Session.load_corpus(simplewiki_directed.genome)` (831,139 vocab loaded in ~21 min = `kernel_to_graph` over 39M edges + the adjacency index; reads instant after) → `define` over the REAL body instrument:
| query | baseline (srmech-tool ground) | with the real simplewiki store |
|---|---|---|
| what is water | z_boson_mass | `water — seen with: ← area, → sq, ← mi, ← land, ← km, → polo` |
| what is science | z_boson_mass | `science — seen with: → fiction, → technology, ← computer, → university, → movie` |
| what is country | expectation_eta | `country — seen with: → subdivision, → united, → music, → states` |
| what is music | — | `music — seen with: → video, → awards, → song, → album, ← rock` |
| what is language | — | `language — seen with: ← english, → spoken, → languages, ← sign` |
| what is planet | — | `planet — seen with: ← minor, → earth, ← planets, → apes, ← dwarf` |
| what is river | — | `river — seen with: → flows, → south, → north, → lake, ← tributary` |
Genuinely meaningful corpus relationships (science *fiction*, *computer* science, *United* States, country *music*, sign *language*, *dwarf* planet, *Planet of the Apes*, rivers *flow* to *lakes* with *tributaries*), with direction (→/←), read straight off the directed Class-L store — not z_boson_mass. F1219's CAN'T-TELL closed at real scale.

## Where #231 stands
The corpus store is now **built native (rc253), proven at real scale (313 MB simplewiki genome, 39M edges, round-trip byte-exact), WIRED into Siona's read path, and demonstrated LIVE** over the real body instrument. That is the full #231/PKG-3 loop and the F1219 "wiring that moves the needle" — delivered end to end. Remaining polish (optional): extend the relational tier from `define` to `answer`/`acquire`; cache the loaded adjacency index so the ~21 min `load_corpus` is a one-time cost (or lazy-load per query token via `gene_express`).

Composes **F1219** (the CAN'T-TELL diagnosis: store right, read not wired — now wired), **F1216** (L-store relational read = what `define` now uses), **F1232** (the native rc253 ops the store rides), **F1227** (the int-cap flag — confirmed safe for simplewiki), **F1221/F1222** (store the directed Laplacian + fiber, not Klein-4), #231/PKG-3, [[feedback_siona_working_memory_never_compacted]] (additive, no truncation), [[feedback_read_independent_structure_check_first]] (measured the wiring effect directly).
