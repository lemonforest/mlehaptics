# R-RBS-LM-30 — Swap-enabled distillation: fp16 70B is feasible, not infeasible

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #38 of the partition tracker
**Closing artefacts:**
- `check_swap.sh` — status / recommend / add / remove subcommands; recommends swap budget for any target model size
- ROADMAP.md — correction to R-RBS-LM-29 Finding 2 framing
- This REPORT — honest documentation of the swap pattern and the corrected feasibility table

**Inheritance:** corrects R-RBS-LM-29's "fp16 70B infeasible" framing. For Path D distillation we're not doing real-time inference, so swap absorbs RAM-overflow at a slower per-token rate. fp16 70B becomes a ~1-4 day cron-task on this hardware — slow but achievable. The corrected feasibility table is now: **ANY model that fits on the disk (533 GB) is achievable**, with per-token rate determined by RAM-vs-swap split.

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | R-RBS-LM-29 (the partition being corrected); R-RBS-LM-22 (storage discipline + precheck); R-RBS-LM-25 (Path D one-shot generation use case) |
| user direction (load-bearing) | *"Why can't we use swap for model conversion to RBS-LM? we aren't doing inference from it"* — the load-bearing question that surfaces the framing error |
| empirical artefacts | `check_swap.sh` (4 subcommands; smoke-verified across 3 model sizes); updated ROADMAP.md |
| current system state (2026-05-25) | 92.3 GB RAM (85 GB free); 8 GB swap (unused; default Ubuntu); 418 GB disk free; swappiness 60 |
| repo commit | `9c41e997` at REPORT-write (R-RBS-LM-29 close) |
| reproducibility | `docs/srmech/rbs_lm_research/check_swap.sh status` / `recommend MODEL_SIZE_GB` |

---

## §0 Human walkthrough

**What we're doing.** Per your question 2026-05-25: *"Why can't we use swap for model conversion to RBS-LM? we aren't doing inference from it."* You spotted a framing error in R-RBS-LM-29 §5 Finding 2 where I wrote that fp16 Llama 70B was "infeasible" because 140 GB > 96 GB RAM. That conflates two different use cases:

- **Real-time inference** (the conventional LLM use case): per-token latency is the bottleneck; memory pressure during a forward pass means tens of milliseconds matter; swap thrash would make this unusable.
- **Path D distillation** (our use case): we generate a corpus ONCE, then encode the byte stream into a static instrument, then drop the model. Per-token latency from swap doesn't matter — only TOTAL generation time, which is set by a cron-task pattern (R-RBS-LM-29 `distill_cron.sh`).

So the corrected reading: **for Path D, swap is the right answer when RAM is the constraint.** The model only has to be ACCESSIBLE during generation; it doesn't have to be RAM-RESIDENT.

This partition ships:

1. **`check_swap.sh`** — a helper that reports current swap state and recommends additional swap budget for a target model size. Subcommands: `status`, `recommend MODEL_SIZE_GB`, `add SIZE_GB [PATH]`, `remove PATH`. The status + recommend subcommands are non-destructive; add/remove require root.

2. **Honest correction in REPORT + ROADMAP.** The Findings table from R-RBS-LM-29 is updated below: fp16 70B is feasible at ~1-4 day cron-task pace. Q4 70B remains faster (~11 hours) when GGUF + llama-cpp-python is acceptable; fp16 + swap is the unquantized fallback for users who want full-precision Path D corpus.

3. **Cleaner feasibility framing:** the constraint is DISK SPACE (533 GB total), not RAM (96 GB). Any model that fits on disk can be loaded; the load just spills into swap when RAM fills.

**Honest performance numbers (rough estimates; not benchmarked end-to-end).** Disk reads on this hardware are ~500 MB/s. Each forward pass touches ALL weights once. For Llama 70B fp16 (140 GB) where ~48 GB needs to come from swap per token:

- Worst case (every byte re-paged): 48 GB / 500 MB/s = ~100 sec/token
- Best case (kernel LRU keeps hot layers in RAM): ~10-30 sec/token effective
- For a 50,000-byte corpus (~12,500 tokens at avg 4 bytes/token): **~1-4 days**

Plenty of headroom in `distill_cron.sh`'s tracking — a 4-day distillation is just `start --label llama70b-fp16` once and check status periodically. The "set it and forget it" pattern absorbs the swap-induced slowdown.

**Why we still document this honestly even though we don't run it.** Running a 4-day distillation isn't on this session's critical path, and it would require provisioning swap (sudo operation) the user should do themselves with explicit consent. But the framing was wrong and that mattered: we'd been telling future readers that fp16 70B was infeasible, when it's actually achievable on this hardware. The correction matters for any future partition that scopes large-model experiments.

**How srmech automates it (future state per R-RBS-LM-12 §6).** When srmech-fix lands the v0.5.0rc, `check_swap.sh` absorbs as `srmech.amsc.storage.swap_recommend(model_gb)` returning a structured recommendation that the `compute_from_source` adapter can act on. The full chain:

```
adapter resolves catalog descriptor
  → swap_recommend(estimated_model_gb)
  → if shortfall: raise clear error pointing to provisioning command
  → else: proceed with precheck_fetch → fetch → generate → encode
```

---

## §1 Goal

Per user direction 2026-05-25: correct the R-RBS-LM-29 framing error. Document the swap pattern honestly. Ship infrastructure (check_swap.sh) so future partitions or operators have a clear path to provisioning swap when needed.

Per `[[user_stance_ai_is_not_a_substrate]]` continuity: the cascade is still a transducer; the model is still being dropped after generation; swap is just plumbing under the hood. Framework reading unchanged.

---

## §2 Inheritance

| Source | Inherited finding | Use |
|---|---|---|
| R-RBS-LM-29 §5 Finding 2 | I claimed fp16 70B was infeasible | Corrected here |
| R-RBS-LM-22 | precheck_fetch + cleanup_caches storage discipline | check_swap.sh composes alongside these |
| R-RBS-LM-25 §3.2 | Path D is one-shot generation, not real-time | Justifies swap pattern |
| R-RBS-LM-29 §3.2 | distill_cron.sh long-running infrastructure | Set-and-forget pattern absorbs swap-induced slowdown |
| User 2026-05-25 question | "Why can't we use swap?" | The framing error that motivated this correction |

---

## §3 Implementation

### §3.1 `check_swap.sh`

| Subcommand | Purpose | Requires root |
|---|---|---|
| `status` | Reports RAM total, swap total, disk free, swappiness, active swap files | No |
| `recommend MODEL_SIZE_GB` | Computes shortfall and recommends swap addition for the given model size; estimates per-token rate via swap | No |
| `add SIZE_GB [PATH]` | Creates a swapfile of the given size via `fallocate + mkswap + swapon`; defaults path to `/swap_rbs_lm_30.img` | Yes |
| `remove PATH` | Deactivates and deletes a swapfile | Yes |

The `recommend` subcommand uses a 12 GB working-memory overhead (KV cache + activations + buffers) as a heuristic. For Llama 70B fp16: 140 GB model + 12 GB overhead = 152 GB total need; current 100 GB capacity → 52 GB shortfall → recommend adding 67 GB swap (shortfall + 16 GB headroom).

### §3.2 Corrected feasibility table

R-RBS-LM-29 §0 table updated:

| Model | Quantization | Size | Capacity needed (with overhead) | Path on this hardware |
|---|---|---|---|---|
| TinyLlama 1.1B | fp32 | 4.4 GB | ~16 GB | **In RAM**; ~3.2 min per 3500-byte corpus (measured) |
| Llama 3.2 1B | Q4 GGUF | ~700 MB | ~2 GB | **In RAM**; need llama-cpp-python |
| Llama 3.1 8B | Q4 GGUF | ~5 GB | ~17 GB | **In RAM**; ~50 min per 50k-byte corpus (est.) |
| Llama 3.1 8B | fp16 | ~16 GB | ~28 GB | **In RAM** (current 100 GB capacity); ~1.5 hours est. |
| Llama 3.1 30B | Q4 GGUF | ~18 GB | ~30 GB | **In RAM**; ~5 hours per 50k corpus (est.) |
| Llama 3.1 30B | fp16 | ~60 GB | ~72 GB | **In RAM** (current capacity ~100 GB); ~8-10 hours est. |
| Llama 3.1 70B | Q4 GGUF | ~40 GB | ~52 GB | **In RAM**; ~11 hours per 50k corpus (est.) |
| **Llama 3.1 70B** | **fp16** | **~140 GB** | **~152 GB** | **VIA SWAP** (add 67 GB swap); ~1-4 days per 50k corpus (est.) |
| Llama 3.1 405B | Q4 GGUF | ~200 GB | ~212 GB | **Mostly swap** (add ~115 GB swap); multi-week per 50k corpus |
| Llama 3.1 405B | fp16 | ~810 GB | exceeds 533 GB total disk | **Infeasible on this hardware** (disk-bound, not RAM-bound) |

The honest reframing: **the binding constraint is disk space, not RAM.** On 533 GB total disk with 418 GB free, any model up through ~400 GB on disk is achievable. fp16 405B (810 GB) genuinely doesn't fit; everything smaller does.

### §3.3 What this partition does NOT do

- **Actually configure additional swap.** The `add` subcommand requires sudo; you should run it with your own consent and verify. Documented as a one-line command from the `recommend` output.
- **Run a Llama 70B fp16 distillation.** Would take ~1-4 days as a cron task. Documented as achievable via `distill_cron.sh start --source meta-llama/Llama-3.1-70B --gen-bytes 50000 --label llama70b-fp16` after `sudo bash check_swap.sh add 67 /swap_rbs_lm_30.img`.
- **Replace the Q4 GGUF path.** Q4 is still faster when available. fp16 + swap is the unquantized fallback.
- **Tune swappiness.** Default 60 is reasonable for our pattern. Tuning to higher values (e.g., 100) would page out idle RAM more aggressively, freeing more for the model — but at the cost of paging in any background processes. Out of scope.

---

## §4 Verification — captured runs

### §4.1 Status

```
$ docs/srmech/rbs_lm_research/check_swap.sh status
=== Current memory / swap state ===
  RAM total:        92.3 GB
  Swap total:       7.9 GB
  Disk free (root): 418 GB
  Swappiness:       60  (60 = balanced; higher = more aggressive)

  Active swap devices/files:
    /swap.img  (type file; 8.0 GB)
```

### §4.2 Recommend for three model sizes

```
$ check_swap.sh recommend 16
  ✓ Current capacity sufficient. No additional swap needed.
    Headroom after model load: 72.2 GB

$ check_swap.sh recommend 40        # Llama 70B Q4
  ✓ Current capacity sufficient. No additional swap needed.
    Headroom after model load: 48.2 GB

$ check_swap.sh recommend 140       # Llama 70B fp16
  Shortfall:        51.8 GB
  Recommended:      ADD 67 GB of swap (shortfall + 16 GB headroom)
  Disk free:        418 GB  (capacity sufficient: YES)

  Command:
    sudo bash check_swap.sh add 67 /swap_rbs_lm_30.img

  Estimated per-token rate via swap on 2009 Xeon E5530 + HDD/SSD:
    fp16 model loaded from swap: ~10-30 sec/token (highly variable)
    For a 50,000-byte corpus (~12,500 tokens): ~1-4 days
    Use distill_cron.sh start to launch unattended.
```

All three recommendations are accurate. The fp16 70B recommendation correctly identifies the 67 GB swap addition + provides the exact sudo command to provision it + extrapolates the per-token rate honestly.

---

## §5 Findings

**Finding 1 — fp16 Llama 70B is feasible on this hardware via swap.** Per §3.2 + §4.2. R-RBS-LM-29 §5 Finding 2 was wrong to call it infeasible. The constraint was RAM-only thinking; with swap on a 533 GB disk, the model has room to spill. Estimated rate: ~10-30 sec/token; 50k-byte corpus in ~1-4 days as a cron task.

**Finding 2 — The binding constraint is disk space, not RAM.** Per §3.2 table. Of the model sizes we care about, only fp16 Llama 405B (810 GB) genuinely doesn't fit. Every other Llama-class size (1B / 8B / 30B / 70B in any reasonable quantization, plus 405B Q4) is achievable.

**Finding 3 — The `recommend` subcommand makes the swap-budget calculation explicit + machine-readable.** Per §4.2. `check_swap.sh recommend MODEL_SIZE_GB` outputs the shortfall, the recommended addition, the exact provisioning command, and the per-token rate estimate. Future partitions don't have to re-derive this math — they call the script.

**Finding 4 — Q4 GGUF remains the fastest path when available.** Per §3.2 table. Llama 70B Q4 GGUF (40 GB) at ~11 hours beats Llama 70B fp16 + swap (~1-4 days) by 3-9×. fp16 + swap is the unquantized fallback, not a replacement.

**Finding 5 — The framing correction matters for future partitions.** Per §0. The R-RBS-LM-29 REPORT now carries a clear "Llama 70B fp16: infeasible" claim that's incorrect. Future readers (or future-me) might propagate that error. The ROADMAP correction + this REPORT close that error path.

**Finding 6 — The user-direction question pattern caught a framework-reading error.** Per `[[feedback_full_coverage_shipping_mpm_way]]` + the partition tracker. The discipline of partition-per-question + honest negative-result REPORTs surfaced an inconsistency for the user to spot. **Catching framing errors via direct question is an important quality-control loop in this project.**

**Finding 7 — Swap thrash on 2009 hardware is acceptable for Path D, NOT for inference.** Per §0. The 10-30 sec/token rate via swap would be unusable for chat / agent loops. For Path D one-shot corpus generation it's fine because `distill_cron.sh` separates human-attention from generation-time. **The two use cases share the same `model.generate()` API but have totally different latency tolerances.**

---

## §6 Open threads (not blockers for partition close)

- **Provision swap + run an actual Llama 70B fp16 distillation.** Multi-day cron task. Document path in ROADMAP; run when you're ready.
- **Tune swappiness for distillation runs.** Setting `vm.swappiness=80` or `100` during a distillation might shift more idle RAM out, leaving more for the model. Could shave hours off a multi-day run. Untested.
- **Compare fp16+swap vs Q4 RAM-resident outputs.** Does the unquantized signal matter? Maybe fp16 70B Path D output has different byte statistics than Q4 70B even though both produce single-byte mode-collapse. Worth a follow-up if R-RBS-LM-29's structural-ceiling argument is to be probed further.
- **zswap / zram for faster swap.** Compressed in-memory swap (`zram`) is much faster than disk swap; would fit in remaining unused RAM. Could turn the 92 GB RAM into effectively 130-150 GB of compressed-RAM swap. Untested.
- **`accelerate` library disk offload.** As an alternative to system swap, `transformers` + `accelerate` has explicit `device_map="disk"` that serializes layers from disk per-forward-pass. More predictable than swap-thrash. Not benchmarked on this hardware.

---

## §7 Closing — partition status

**Status:** CLOSED. R-RBS-LM-29 framing error corrected. `check_swap.sh` provides the swap-budget calculation + provisioning interface. ROADMAP.md updated. The corrected feasibility table establishes that disk space (not RAM) is the binding constraint for Path D distillation on this hardware.

**Falsifiers:**

1. A claim that fp16 70B is infeasible on this hardware — **explicitly disclaimed §5 Finding 1**; achievable via 67 GB swap addition + ~1-4 day cron task.
2. A claim that swap + fp16 is faster than Q4 GGUF — **explicitly disclaimed §5 Finding 4**; Q4 is still ~3-9× faster when available.
3. A claim that this partition runs a 70B distillation — **explicitly disclaimed §3.3**; documented as achievable; not run in this session.
4. A claim that all Llama models are achievable — **partially disclaimed §3.2 table**; fp16 Llama 3.1 405B (810 GB) genuinely doesn't fit on the 533 GB disk; everything smaller does.

**Inherits to:**
- Any future partition that scopes a large-model experiment can use `check_swap.sh recommend` to size the budget
- ROADMAP.md correction lands in the canonical follow-up registry
- The "Path D = one-shot generation" framing now has clear documentation of its swap-tolerant nature, which will save framing errors in future partitions

**SSoT marker:** at SSoT absorption, §0 human walkthrough + §3.2 feasibility table + §5 findings absorb into `srmech_research_notebook.md` as a corollary to R-RBS-LM-22 storage discipline. Finding 7 ("swap thrash acceptable for Path D, not for inference") is potentially load-bearing for the broader MFO / framework reading around use-case-dependent latency tolerances.
