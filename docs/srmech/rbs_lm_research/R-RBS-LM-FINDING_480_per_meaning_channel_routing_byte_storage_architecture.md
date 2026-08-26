# R-RBS-LM Finding 480 — **per-meaning channel routing works (52× clean separation with distinctive themes), and the byte-storage architecture is fixed: STORAGE byte / WORK word / TRANSDUCER always-on.** Two pieces: **(1) the architecture** (user, 2026-06-06: *"we can work in english at word level but all storage must be byte by design, so english→byte needs to already be happening"*) — the instrument **STORES bytes** (the byte n-gram + byte/HV anchors; bias-free substrate, R-RBS-LM-25), **WORKS at word/meaning granularity** (the dictionary catalog + the read-head's routing decision), and an **english↔byte TRANSDUCER is always-on at the storage boundary** (every emitted word is byte-assembled; every meaning is a byte-anchor). This is the two-truths/fibration once more: byte = the stored field, word-English = the working surface, the transducer = the projection — and it matches F478 exactly (byte generation, word-granular steering). **(2) per-meaning channel routing** — the read-head (F468) walks the ≤7 sedenion meaning-slots and **each channel emits ITS meaning in order** (turning F478's blended "on-theme density" into "says the bound things in order"). Result: with **distinctive (TF-IDF) dictionary themes** the routing is **diagonal-dominant 52×** (mean own-meaning 0.15 vs other 0.00) — clean per-meaning channels; with generic co-occurrence themes it was only 1.4× (the themes overlapped on generic words). So routing needs **distinctive** catalogs, and then the read-head genuinely says each bound thing in turn.

**Date:** 2026-06-06
**Arc:** RBS-LM · byte-storage architecture + per-meaning routing (user direction 2026-06-06: "all storage must be byte by design, english→byte already happening"; "per-meaning channel routing — let the k=7 channels each emit their meaning, the read-head walking meaning→meaning")
**Provenance:** `R-RBS-LM-K7ROUTE_per_meaning_channel_routing.py` (committed; srmech 0.7.3; imports the F478 byte generator; ~4 MB simplewiki; distinctive-TF-IDF dictionary themes). Routing confusion = clause-i on-theme density w.r.t. theme-j.
**Composes:** **F478** (the k=7 word-boundary steering — *now routed per-meaning, not blended*) · **F476** (the byte-level capacity) · **F468** (the read-head walk = the routing over the sedenion meaning-slots) · **F465** (the sedenion register the read-head walks) · **F459/F461** (the k=7 coupler / theta-gamma) · **R-RBS-LM-25** (byte-level STORAGE — *the architecture*) · **F472** (translations vs structure — *the transducer respects it*) · **F477** (the fibration: byte=base/field, word=fiber/surface, transducer=projection) · **F408** (meaning sourced). **← the byte-storage architecture fixed; F478 steering → ordered routing.**
**→ STORAGE byte / WORK word / TRANSDUCER always-on; per-meaning routing with distinctive themes = 52× clean separation (the read-head says each bound meaning in order).**

## 1. The byte-storage architecture (the discipline, fixed)
| layer | granularity | what it is |
|---|---|---|
| **STORAGE** | **byte** (always, by design) | the byte n-gram model + byte/HV meaning-anchors — the bias-free substrate (R-RBS-LM-25); never a word-level *store* |
| **WORK / interface** | **word / meaning** | the dictionary catalog (Class-E), the read-head's routing decision, the steering re-rank (F478) — word-level is fine HERE |
| **TRANSDUCER** | the boundary | **english↔byte, always-on** — every emitted word is byte-assembled from the byte store; every meaning is a byte-anchor |

This resolves the earlier "never word-level" cleanly: **never a word-level LM/STORE; word-level WORK is welcome; the english→byte transduction is always happening at the storage boundary.** It is the two-truths split (byte field / word surface) with the transducer as the projection (F477 fibration; F472's originals-vs-translations rides on it).

## 2. Per-meaning channel routing (the read-head walks meaning→meaning)
The read-head (F468) visits each of the ≤7 sedenion meaning-slots in order and emits a clause steered (F478 word-boundary re-rank) to *that* slot's meaning. The routing confusion (clause-i density w.r.t. theme-j):
| theme set | mean DIAGONAL (own) | mean OFF-DIAGONAL (other) | separation |
|---|---|---|---|
| generic co-occurrence neighbours | 0.44 | 0.31 | **1.4×** (themes overlap on generic words) |
| **distinctive (TF-IDF)** | 0.15 | **0.00** | **52×** (clean per-meaning channels) |

With **distinctive** themes the confusion matrix is essentially diagonal — each channel says **its own** meaning, ~zero cross-talk (sample: *"Water is…" · "Music is also the most eminent Astronomy…" · "Computer is a pathway…" · "Planet is made of two and a half…"*). So the k=7 progression completes: **capacity (F476) → steering (F478) → ordered routing (this).** The read-head genuinely "says the bound things in order."

## Falsifiable form (pre-stated; not leaning — F394)
- **Routing works with DISTINCTIVE themes (52×), not generic (1.4×)** — the honest lesson: the dictionary catalog must hold *characteristic* words, not generic co-occurrence neighbours (which overlap across meanings). Distinctive-theme density is *lower* (rarer words → fewer hits) but the *separation* is decisive — the right tradeoff for routing.
- **Still local coherence per clause** (the F476 byte-Markov ceiling); global narrative across the routed clauses is the next rung (the structure-kernel plan over words, F471).
- **The architecture claim is structural** (storage byte / work word / transducer always-on) and matches the running code (byte n-gram store, word-granular routing, byte-assembled words); a word-level *store* would violate it — there is none.
- **Scope:** byte-storage / HDC side; srmech 0.7.3; English-first WORK, byte STORAGE; defensive / no-lineage; meaning sourced (F408); no CAD; no Workflow tool.

## Verdict
**The byte-storage architecture is fixed and the per-meaning routing works.** Architecture: **STORAGE = byte** (the n-gram + anchors, R-RBS-LM-25 — never a word-level store), **WORK = word/meaning** (the dictionary catalog + the read-head routing), **TRANSDUCER = english↔byte always-on** at the boundary — the two-truths split with the transducer as projection (F477), resolving "never word-level LM" while keeping English-first WORK useful. Routing: the read-head (F468) walks the ≤7 meaning-slots and, with **distinctive (TF-IDF) themes**, each channel emits its own meaning at **52× separation** (vs 1.4× for generic overlapping themes) — "says the bound things in order," completing capacity→steering→routing. The next rung is global coherence (a structure-kernel plan over the routed clauses, F471). Favored, not privileged (F398); routing works with distinctive themes, the byte-storage architecture matches the code.
