# R-RBS-LM Finding 527 — **the user's architecture works: RBS-LM memory can be its OWN KERNEL — a constant-D HDC bundle maintained every exchange — so there is NOTHING TO EVER COMPACT (the kernel is 1024 bytes after 1 exchange and 1024 bytes after 24; a Gen-1 LLM context would have grown 24×). Old exchanges FADE gracefully (recall +0.48 at age 0 → +0.37 → +0.21 → ~noise by age ~8, the HDC capacity F137/F152 + recency/plasticity-decay F76/F141) — biological working memory, NOT a hard truncation — and the exact content survives in an append-only LOG. And it is REWINDABLE like a Gen-1 LLM: rebuild the kernel from any log prefix → rewind to turn k reconstructs the exact memory state at turn k (recalls the then-recent exchange +0.50, the future exchange ~0). So the RBS-LM memory is WORKING memory (the constant kernel, fades, never compacts) + EPISODIC memory (the log, exact, rewindable) — and the Gen-1 LLM compaction/truncation problem (what THIS session has been doing by hand) simply does not arise.**

**Date:** 2026-06-07
**Arc:** RBS-LM — memory as its own constant-size, rewindable kernel (user architecture 2026-06-07)
**Provenance:** `R-RBS-LM-MEMKERNEL_constant_size_no_compaction_rewindable.py` (committed; srmech 0.7.4; Class-M `hdc.bundle`/`similarity`; recency by vote-weight; mint_vector exchanges). No sub-agents.
**Composes:** **F166** (the rolling context-state encoder — *= this kernel, the working-memory state*) · **F137/F152** (HDC capacity — *the graceful fade limit*) · **F76/F141** (plasticity/Hebbian decay — *the recency weighting*) · **F154** (hierarchical bundling for N>257 — *the refinement to extend the working window*) · **F521–F525** (the story/arc — *held in the kernel as the conversation state*) · **`[[feedback_no_subagents_compact_via_re_prime]]`** (the compaction problem — *DISSOLVED here: a constant kernel never compacts*) · **F282/F398/F394**. **← memory = a constant-size kernel (no compaction) + an append-only log (rewind).**
**→ the RBS-LM memory is its own constant-D kernel (maintained every exchange → nothing to ever compact; old content fades gracefully, not truncated) plus an append-only log (exact, rewindable to any turn) — working memory + episodic memory, dissolving the Gen-1 LLM compaction problem.**

## Result
| (1) NOTHING TO COMPACT | after 1 exchange | after 24 exchanges |
|---|---:|---:|
| kernel size | **1024 bytes** | **1024 bytes** (constant; a Gen-1 context would be ~24×) |

| (2) GRACEFUL FADE — recall by recency | age 0 | age 1 | age 3 | age 7 | age 15 | age 23 |
|---|---:|---:|---:|---:|---:|---:|
| recall similarity | **+0.48** | +0.37 | +0.21 | +0.06 | ~+0.07 | ~+0.07 |

| (3) REWIND from log prefix | recalls then-recent | recalls the future |
|---|---:|---:|
| rewind to turn 8 | exchange 07: **+0.50** | exchange 08: +0.02 (unknown ✓) |
| rewind to turn 16 | exchange 15: **+0.48** | exchange 16: −0.02 (unknown ✓) |

Recent exchanges are **sharp**, old ones **fade smoothly to noise** (no hard cut-off); rewind rebuilds the **exact** state at any turn (then-recent recalled, future correctly absent).

## The architecture
- **WORKING memory = the constant kernel.** A fixed-D HDC bundle, recency-weighted, updated each exchange. It **never grows** → the compaction/truncation problem (a growing context window) **does not exist**. It holds a **recent gist window** sharply; older content fades (the HDC capacity, not a cut).
- **EPISODIC memory = the append-only log.** The exact per-exchange vectors (and text), kept forever. **Rewind** to turn k = rebuild the kernel from `log[0:k]`. Anything faded from the kernel is **re-bindable from the log** on demand.
- **This dissolves the compaction problem.** This very session has been compacting by hand (re-priming from CLAUDE.md/MEMORY.md). A constant kernel + log needs **no compaction** — the working state is bounded by construction, the full record is the log.

## Falsifiable form (held open — F394)
- **Shown:** kernel size constant (1024 B at N=1 and N=24); recall recency gradient (+0.48 → noise by age ~8); rewind reconstructs the then-state (then-recent +0.50, future ~0).
- **Falsifier:** if the kernel grew with N, "nothing to compact" would be false — it doesn't (constant). If old exchanges were hard-cut (not faded), it would be truncation not graceful fade — they fade smoothly. If rewind recalled the future, the log-rebuild would be wrong — it doesn't.
- **Honest:** the kernel's effective **working window is bounded** (~HDC capacity, here old content fades to noise by age ~8) — so the kernel ALONE is a *recent-gist* memory, and **anything older lives only in the log** (re-bindable, but not in the live kernel). Extending the working window is the **hierarchical-kernel** refinement (F154: chunk into kernel-of-kernels). The vote-weight recency is a simple decay; richer (Hebbian/coupling) decay is F76/F141. This is a framework architecture demonstration, handed to the expert (F282) — the exchanges here are mint-vector stand-ins, not real encoded turns.
- **Scope:** framework build; srmech 0.7.4; Class-M HDC; no abs(); no CAD; no Workflow tool; no sub-agents; held open (F394); favored not privileged (F398).

## Verdict
**The user's architecture works and is the right shape.** RBS-LM memory as its **own constant-D kernel**, maintained every exchange, is **1024 bytes at N=1 and N=24** — it never grows, so there is **nothing to ever compact**; old exchanges **fade gracefully** (HDC capacity + recency decay), biological working memory rather than a hard truncation, and the exact content survives in an **append-only log** that makes the conversation **rewindable** (rebuild the kernel from any prefix → the exact then-state). So the RBS-LM has **working memory (the constant kernel) + episodic memory (the log)**, and the Gen-1 LLM compaction problem — the thing this session has been doing by hand — **simply does not arise**. Honest: the kernel's live window is capacity-bounded (older content is in the log, re-bindable); the **hierarchical kernel** (F154) extends it. Favored, not privileged (F398); held open (F394); structure for the expert (F282).
