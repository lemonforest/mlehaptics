# F1213 — The directed glyph-graph word encoder is BUILT + genome-native (F1212 root fix, steps 1–4 PASS)

**User (2026-07-14):** *"proceed with digraph."* Built the ni-Vanuatu root fix on the winning carrier (F1212: digraph). Prototype `R-RBS-LM-NIVDIRECTED_…py` — NOT yet swapped into the live genepool (step 5, reviewed follow-on).

## What it is
`word_to_kernel(w)` → a word as a **directed glyph Class-L** (F1210 one scale down): `vocab` = glyphs used, `start` = the sandroing walk anchor, `edge_list` = canonical (i<j) glyph pairs, `edge_weights` = w_fwd+w_bwd (the **METRIC** = today's adjacency content), `edge_charge` = w_fwd−w_bwd (the **DIRECTION** the base lacked). Persisted genome-native via `kernel_pack` → `genome_save` (content-addressed directory) → `genome_load` → `kernel_unpack` (a discrete JSON-free int→klein4 codec), NOT loose JSON.

## Ratchet (11 words)
| axis | result |
|---|---|
| **direction** (word ≠ reverse, via charge) | **11/11** — `cat` charge `[-1,+1]` vs `tac` `[+1,-1]`; the bag scored 1.000 (F1211), now distinguished |
| **metric kept** (reversal leaves weights, flips only charge) | **11/11** — anagram discrimination (F1013) preserved |
| **genome-native round-trip** (content-addressed, bit-identical) | **11/11** — ~1.6 KB/word packed chromosome; body_sha256 identity (fixes the loose-JSON regression) |
| **Eulerian round-trip** (recover the word = the sandroing walk, Hierholzer) | **10/11 exact** — the one miss (`vanuatu`→`vatuanu`) is genuine **F1079 Euler-path ambiguity** (repeated glyphs → multiple valid unicursal lines; recovers a VALID reading, not a defect) |

## Reading
The word is now literally a **sandroing walk over its glyphs** (F1080 Eulerian circuit), carrying the direction the abelian Klein-4 bag threw away (F1211), packed as the **same F1210 directed-edge object one scale down** (glyph→glyph in a word = word→word in a corpus), stored **genome-native + content-addressed** (F1207 discipline, [[feedback_persist_genome_native_not_loose_json]]). Exact round-trip holds iff the Euler path is unique (commensurate, F1079); repeated-glyph words are genuinely one-of-many unicursal lines (incommensurate) — the attested closability property, and full determinism there would need a branch tie-break anchor (approaching storing the sequence — a commensurate/incommensurate knob, the user's call).

## Next (reviewed — step 5, NOT done here)
Swap the live `_word_hv` / `build_genepool` to this directed encoder and re-encode the language layer (ni-Vanuatu base + SignWriting + dict-en projecting up); repoint the wiki/kernel persist to `kernel_pack` too (fold the F1210 directed simplewiki JSON into a genome). This is the invasive live-genome mutation + re-encode — gated on user go-ahead.

Composes **F1212** (digraph = the winning carrier), **F1211** (the base was metric-only — this fixes it), **F1210** (the directed-edge object — now the base primitive), **F1080/F1079** (sandroing Eulerian walk / commensurate-vs-incommensurate), **F1207** + [[feedback_persist_genome_native_not_loose_json]] (genome-native, content-addressed), [[project_ni_vanuatu_byteglyph_is_the_order_native_base_of_all_kernels]].
