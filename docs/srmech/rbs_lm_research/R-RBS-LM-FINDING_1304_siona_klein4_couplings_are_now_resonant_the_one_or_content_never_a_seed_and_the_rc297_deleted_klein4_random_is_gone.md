# F1304 — **siona's klein4 couplings are now resonant instruments — from `the_One` or from content, never a random seed** — and the rc297-deleted `klein4_random` is gone from `siona/` (it had escaped the F1285 rename). Two live couplings fixed: `genome_store._coupler` (documented as `the_one`, was `klein4_random(seed=0)`) → the actual `the_one` winding; `corpus_store.COUPLE` (the UNESCO-00073 source, was `klein4_random(seed=1080)`) → a Class-A **content-address of the named source**. The store spine now runs on rc299.

**User (2026-07-22):** *"fix corpus_store.py and rescan siona/ for klein4_random. klein4 is just a carrier type and the shape can either come from the_One or from the knowledge it contains, never a random seed that cannot be a resonant instrument."*

## The principle, applied
**klein4 is a carrier; its shape is set by one of two resonant sources, never a magic seed:**
- **the_One** — the canonical winding, for a *structural* coupling.
- **the knowledge it contains** — a Class-A content-address (`klein4_encode_bytes` of a named source), for a *source-anchored* coupling.

A `klein4_random(seed=N)` coupling fails on **both** counts F1259 names: it is a **DRAWN magic number** (an undeclared pin), and it is **not resonant** (an arbitrary code at the orthogonality floor). And on rc297 it is a **dead call** — `klein4_random` was deleted (F1284/F1285).

## The two live couplings (verified on rc299)
| site | was | now | source |
|---|---|---|---|
| `genome_store._coupler` | `klein4_random(leaf, seed=0)` — but its **own docstring calls it `the_one`** | **`klein4_from_one(the_one(1,0), leaf)`** | the_One winding |
| `corpus_store.COUPLE` | `klein4_random(LEAF, seed=1080)` — the "sandroing/UNESCO-00073 seed" | **`klein4_encode_bytes(b"UNESCO-ICH-00073:vanuatu-sand-drawings", LEAF)`** | content-address of the named source |

The genome coupler was *already documented as `the_one`* — the seed was the wrong implementation of the right intent; now it **is** `the_one`. The corpus coupler was anchored to UNESCO-00073 in a comment — now it **is** the content-address of that source, stable across processes (verified) and de-magicked (F1259 DERIVED regime, no `1080`).

## The rescan — siona/ is clear
8 `klein4_random` occurrences: **2 live couplings (fixed)**, 4 **test fixtures** (→ `klein4_encode_bytes(b"fixture-N")`, content-derived, round-trip verified), and 2 **comments** (`bridge.py`/`infer.py` — historical documentation of the F1260 defect, correctly left). The F1285 rename missed `siona/` because its glob ran under `rbs_lm_research/`, not the sibling subtree; this closes that gap.

## Why it matters beyond the fix
`corpus_store.py` was **non-runnable** on current srmech (Breakage 3 of the F1303 ASL-plan verification) — a deleted function + an undeclared magic seed. It now runs. More broadly: the coupling is the store's **invariant** — the thing every leaf is coupled through — so making it a **resonant, attested** instrument (the_One or content) rather than a drawn number is the difference between a store whose invariant *means something* and one pinned to a number nobody can justify. This is F1259 (three-things-called-random) and F1302 (klein4 is the carrier, not the content) applied to the store spine.

Composes **F1303** (Breakage 3, now cleared), **F1259** (DRAWN vs DERIVED), **F1302** (klein4 = carrier), **F1284/F1285** (the deleted `klein4_random`), **F1300** (the_one coupling in the genome), `[[feedback_three_things_called_random_derived_drawn_stochastic]]`, `[[feedback_persist_genome_native_not_loose_json]]`.
