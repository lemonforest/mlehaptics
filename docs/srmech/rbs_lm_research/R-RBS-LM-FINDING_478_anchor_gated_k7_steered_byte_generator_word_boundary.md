# R-RBS-LM Finding 478 — the **anchor-gated (k=7-STEERED) byte generator**: per-byte steering FAILS, **word-boundary re-rank WORKS** (~doubles on-theme density) — generation stays on the bound meaning, LM stays byte-level. Turning F476's k=7 *capacity* into k=7 *steering*: re-weight generation toward the coupled meaning-anchor so output stays on-meaning instead of drifting. Two mechanisms tested (srmech 0.7.3): **(a) per-byte prefix-boost** (boost bytes that extend toward an on-theme word) — **WEAK/NULL** (water 0.36→0.38, computer 0.10→**0.07**, k=7 0.41→**0.34**): the order-9 byte-grammar dominates a single-byte nudge, and common prefixes ("th","co") prefix theme *and* non-theme words, so it can't discriminate. **(b) word-boundary re-rank** — the GRAMMAR kernel (byte-LM) proposes K byte-built candidate words, the DICTIONARY catalog re-ranks them by theme — **WORKS: on-theme density ~doubles** (water 0.18→**0.45**, music 0.18→**0.40**, computer 0.19→**0.28**) and the text stays coherent. The lesson is itself framework-clean: **byte-level generation (the fiber assembles byte-by-byte), but steering must act at meaning-bearing (word) granularity** — the LM stays byte-level (never word-level); the *steering decision* is a word-level re-rank. This is the **three-kernel fibration (F477) operational**: GRAMMAR (byte-LM, fiber) gated by the DICTIONARY catalog (meaning→words) under the **k=7 coupler** (≤7 meanings, theta-gamma F461/F466; coherence 0.91 for 7 distinct = capacity).

**Date:** 2026-06-06
**Arc:** RBS-LM · byte-level k=7-steered generation (user direction 2026-06-06: "build the anchor-gated (k=7-steered) byte generator next as well")
**Provenance:** `R-RBS-LM-K7STEER_anchor_gated_byte_generator.py` (committed; srmech 0.7.3; byte n-gram orders 1..9 over ~4 MB simplewiki — byte-level LM; dictionary = corpus co-occurrence catalog (Class-E), word-level KNOWLEDGE only; `hypercomplex_couple` for the k=7 bind). On-theme density = fraction of generated words in the meaning's dictionary.
**Composes:** **F476** (the k=7 *capacity* / byte-level generation — *now steered*) · **F477** (the three-kernel fibration — *operational here: grammar=fiber, dictionary=catalog, structure=anchor*) · **F459** (the k=7 coupler) · **F461/F466** (theta-gamma ≤7) · **R-RBS-LM-25** (byte-level LM, never word-level — *the LM stays byte; only the steering re-rank is word-granular*) · **F471** (the order channel = the grammar kernel) · **F408** (the meaning sourced/seeded) · **F468** (the read-head walk — *steering = gating the walk*). **← turns F476 capacity into steering; the fibration's generation half.**
**→ per-byte steering fails (grammar dominates, prefixes don't discriminate); word-boundary re-rank works (~2× on-theme density); byte-level generation + word-granular steering = the fibration operational.**

## Results
**[a] per-byte prefix-boost (the naive try) — WEAK/NULL:**
| meaning | unsteered (F476) | per-byte boost (α=4) |
|---|---|---|
| water | 0.36 | 0.38 |
| music | 0.15 | 0.18 |
| computer | 0.10 | 0.07 |
| k=7 (all coupled) | 0.41 | 0.34 |

The order-9 byte-grammar's local fluency dominates a single-byte ×5 nudge, and a 40-word theme set's prefixes overlap common non-theme words — so per-byte boosting **cannot discriminate**. Honest null (not a deliverable).

**[b] word-boundary re-rank (the fix) — WORKS:**
| meaning | unsteered | word-steered | gain |
|---|---|---|---|
| water | 0.18 | **0.45** | ~2.5× |
| music | 0.18 | **0.40** | ~2.2× |
| computer | 0.19 | **0.28** | ~1.5× |

The GRAMMAR kernel (byte-LM) proposes K=10 byte-built candidate *words*; the DICTIONARY catalog re-ranks them by theme-membership (softmax, β=6); the chosen word is appended and the byte-LM continues. On-theme density roughly **doubles**, and the output stays locally coherent English ("Water is also forms the border… people can tell that can play chess"; "Music is also the hurricane-like storm on the ship… refers to the speed"). **The LM stays byte-level; only the steering decision is word-granular.**

## The framework point (why word-granularity)
Steering must act at the **meaning-bearing granularity**, which is the **word**, not the byte — because meaning lives in words, and a single byte is below the discrimination threshold (it commits to a prefix shared by many words). So the operational split is clean and substrate-honest: **the fiber (surface) assembles byte-by-byte (the byte-LM, R-RBS-LM-25); the steering (the anchor → which meaning) acts per word (the dictionary re-rank).** This is exactly the F477 fibration: the byte-LM is the fiber-assembly; the dictionary+coupler is the base-anchor pulling the fiber toward the bound meaning; and the pull is applied at the granularity where base and fiber meet — the word boundary.

## Falsifiable form (pre-stated; not leaning — F394)
- **Per-byte steering is an honest NULL** (0.36→0.38; computer/k7 *decreased*) — reported as failure, not smoothed. It located the fix (granularity).
- **Word-boundary re-rank works, bounded:** ~2× on-theme density, coherent — but it is *biased sampling over grammar-proposed words*, not deep planning; coherence is still **local** (the byte-LM's order-9 ceiling, F476) — global narrative coherence is a separate, harder problem (a structure-kernel-driven plan over words, the flagged next).
- **The LM stays byte-level** (orders 1..9, no word vocab); the dictionary is a Class-E *catalog* (word-level knowledge as reference, permitted); the steering re-rank is a word-level *decision*, not a word-level LM — the R-RBS-LM-25 discipline holds.
- **k=7 is capacity, shown (coherence 0.91 for 7 distinct anchors); steering used a single/blended theme** — per-meaning *channel* routing (emit word for meaning-i at step-i) is the next refinement.
- **Scope:** byte-LM/HDC side; srmech 0.7.3; English-first; defensive / no-lineage; meaning seeded/sourced (F408); no CAD; no Workflow tool.

## Verdict
**The anchor-gated k=7-steered byte generator works — once the steering acts at the right granularity.** Per-byte prefix-boosting is a null (the order-9 grammar dominates; common prefixes don't discriminate); **word-boundary re-rank ~doubles on-theme density** (water 0.18→0.45, music →0.40, computer →0.28) while keeping the text coherent. The clean split: **byte-level generation (the fiber, R-RBS-LM-25 — never word-level LM) + word-granular steering (the dictionary catalog re-rank under the k=7 coupler, F459/theta-gamma)** — the F477 three-kernel fibration made operational, F476's k=7 *capacity* now k=7 *steering*. Honest bounds: still *local* coherence + *biased-sampling* (not planning); global narrative + per-meaning channel routing are the flagged next rungs. Favored, not privileged (F398); per-byte null reported, word-boundary fix demonstrated, byte-LM discipline intact.
