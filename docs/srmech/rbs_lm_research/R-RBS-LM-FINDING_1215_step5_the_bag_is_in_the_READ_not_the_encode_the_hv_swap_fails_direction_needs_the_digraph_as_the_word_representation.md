# F1215 — Step 5: the `_word_hv` swap FAILS — the bag is in the READ (klein4_similarity), not the encode. Direction needs the DIGRAPH as the word representation (a genepool matching-layer change, #231), not a drop-in HV swap

**User (2026-07-14):** *"go ahead with step 5"* (swap the live `_word_hv`/`build_genepool` to the directed encoder + re-encode). Attempted, MEASURED, and it does **not** work as an HV swap — for a reason that sharpens F1214.

## Measured (the swapped two-channel `_word_hv`, in the live genepool)
Swapped `_word_hv` to carry both channels in one HV: undirected bigram binds (the edit-robust METRIC, F762) **+** src/dst role-bound directed bigrams (the DIRECTION). Result on `klein4_similarity`:

| check | result |
|---|---|
| **direction** (word vs reverse; was 1.000 as a bag) | `cat/tac` 1.000, `listen/netsil` 1.000, `vanuatu/utaunav` 1.000, `draw/ward` 1.000, only `order/redro` 0.656 — **still ~1.0** |
| **metric / edit-robust** (word vs 1-typo) | 0.875–0.969 — preserved ✓ |
| **unrelated** (`water/mountain`) | **0.797** — high; the read is fuzzy *everywhere* |

## The finding: the bag is in the READ, not (only) the encode
Encoding direction into the word HV (role-bind) does not surface it, because **`klein4_similarity` is a coarse sector-occupancy read** — it barely separates *unrelated* words (0.797), so it certainly cannot resolve a word from its reverse (~1.000). This is the deeper form of F1214: Klein-4's *similarity metric* is itself substantially order/direction-blind, so **no HV re-encode fixes the bag at the read level.** A drop-in `_word_hv` swap is therefore a cosmetic non-fix — it changes the HV bytes but not what the matching can distinguish — so it was **reverted** (the original edit-robust metric HV is kept; a non-readable direction component is pure cost).

## The real step-5 (a scope escalation, handed back)
The base's **word representation** must BE the **digraph kernel** (R-RBS-LM-NIVDIRECTED / F1213 — exact integer `edge_charge`, round-trippable via the sandroing Eulerian walk), read with a **direction-aware, structural read** (charge / holonomy / round-trip), NOT `klein4_similarity`. That is not a `_word_hv` swap — it is a change to the genepool's **matching layer** (how words are stored *and* compared): the gene becomes a directed Class-L kernel, and nearest-word/edit-robust matching runs on the metric channel (`w_fwd+w_bwd`) while direction reads on the charge channel (`w_fwd−w_bwd`). This is the F1210 "one object, two read-outs" made the genepool's word type, and it belongs to the **#231** genome-native repack (word-leaf → directed kernel), not a hot-swap.

## What step 5 actually delivered
- **The genepool `_word_hv` is now honestly documented** (F1214/F1215): it is the METRIC channel only; direction lives in the digraph kernel; the bag is in the coarse `klein4_similarity` read.
- **The directed word encoder exists + is validated** (F1213, genome-native, round-trips) — ready to become the word representation when the #231 matching-layer change is done.
- **Escalation surfaced honestly** instead of shipping a cosmetic swap: making the base directional is a genepool matching-layer redesign (structural charge read replaces/augments `klein4_similarity`), the user's call.

Composes **F1214** (the coarse read is half the bag — now the *decisive* half at the genepool level), **F1213** (the digraph encoder — the correct word representation), **F1212** (digraph is the reliable channel), **F1211** (the base was metric-only), **F762** (edit-robust matching the metric HV must keep), #231 (genome-native repack — where the word-leaf→directed-kernel change lands). Candidate upstream: a direction-aware klein4 read (or `klein4_permute`) so the HV channel could carry order — but the structural charge read is the reliable path regardless.
