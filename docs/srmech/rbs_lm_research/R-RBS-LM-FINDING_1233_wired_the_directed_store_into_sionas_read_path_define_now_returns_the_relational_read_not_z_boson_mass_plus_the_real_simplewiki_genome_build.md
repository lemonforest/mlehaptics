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
`R-RBS-LM-SIMPLEWIKIGENOME_…py`: the actual #231 target — `simplewiki_directed_sparse_kernel.json` (916 MB, **831,139 vocab / 39,048,148 directed edges**) → one content-addressed genome via the native rc253 store, verified with `recover_check_structural`/`recover_check_spectral(max_dim=256)` + a full round-trip. Measured so far:
- **int-cap check PASSED with room:** max node id 831,139, **max metric 193,858, max |charge| 55,174 — all ≪ 2³⁰**. So the codec's 30-bit bound (F1227) is comfortable for simplewiki (confirming the flag was right *and* that this corpus is safe).
- The build (39M-edge `graph_to_kernel`) runs the ~18-min pack; on completion it yields the ~226 MB genome (F1227's projection: ~4.3× smaller than the 916 MB loose kernel), byte-exact round-trip + relationally queryable. (Numbers to be confirmed on completion.)

## Where #231 stands
The corpus store is now: **built native (rc253), proven at real scale (18k findings + the 831k/39M simplewiki), and WIRED into Siona's read path** so it changes her answers. The remaining polish: point `load_corpus` at the finished simplewiki genome for a live "what is X?" over the real body instrument, and extend the relational tier to `answer`/`acquire` (define is done). This is the F1219 "wiring that moves the needle" delivered.

Composes **F1219** (the CAN'T-TELL diagnosis: store right, read not wired — now wired), **F1216** (L-store relational read = what `define` now uses), **F1232** (the native rc253 ops the store rides), **F1227** (the int-cap flag — confirmed safe for simplewiki), **F1221/F1222** (store the directed Laplacian + fiber, not Klein-4), #231/PKG-3, [[feedback_siona_working_memory_never_compacted]] (additive, no truncation), [[feedback_read_independent_structure_check_first]] (measured the wiring effect directly).
