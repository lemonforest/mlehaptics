# R-RBS-LM-22 — Storage management + check-before-fetch tooling

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #30 of the partition tracker
**Closing artefact:** `storage_management.py` — three utilities (disk_summary, cleanup_caches, precheck_fetch); verified via §4 captured runs
**Inheritance:** unblocks any future model fetch (R-RBS-LM-23 MiniMax descriptor; R-RBS-LM-24+ alternative source models); the precheck pattern protects all downstream encode/harvest scripts

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `HARDWARE_AND_THREADING.md` §1 (2009 Xeon E5530 hardware envelope); R-RBS-LM-12 §6 (upstream-to-srmech plan); `[[user_stance_hardware_age_not_penalty_for_sharing]]` (storage decisions inform what we share) |
| user direction (load-bearing) | *"we will need to remove dense LLMs when we don't need them anymore and we will need to check our storage space before fetching."* |
| empirical artefacts | `docs/srmech/rbs_lm_research/storage_management.py` |
| repo commit | `037538b1` at REPORT-write |
| reproducibility | `python3 docs/srmech/rbs_lm_research/storage_management.py` (no venv needed; stdlib-only) |

---

## §0 Human walkthrough

**What we're doing.** We just discovered the workstation's disk is at 94% used — only 670 MB free of 98 GB. Without a safety net, any attempt to download a larger source model would fail mid-fetch, possibly leaving half-downloaded artefacts behind. This partition builds three small Python utilities so the encoding pipeline can check disk space BEFORE fetching, clean up regenerable caches when needed, and report storage status honestly.

**How we're doing it.** Three functions in `storage_management.py`:

1. **`disk_summary()`** — read-only. Reports disk used/total/free; reports the sizes of regenerable caches (the 49 MB `vocab_table.npy` that takes 4 seconds to rebuild from token IDs); reports HuggingFace cache (re-downloadable); flags ≥85% used as a warning and ≥95% as critical.
2. **`cleanup_caches(remove_vocab_table=True, hf_models=['gpt2'])`** — destructive but bounded. Removes the regenerable vocab table; optionally removes named HuggingFace model caches. Reports bytes freed.
3. **`precheck_fetch(estimated_bytes, safety_margin_gb=1.0)`** — predicate. Raises `StorageInsufficientError` if free disk < estimated + safety_margin. Any encode/harvest script can call this before `from_pretrained()` to fail fast with a meaningful error instead of mid-download.

The CLI runs `disk_summary()` by default; `--cleanup` invokes `cleanup_caches`; flags control which caches to drop.

**How srmech automates it (future state per R-RBS-LM-12 §6).** When the srmech-fix session lands the v0.5.0rc with the `compute_from_source` adapter, the adapter calls `precheck_fetch()` automatically before any source-model download. The user doesn't have to remember; the AMSC framework handles it. End-user workflow:

```python
from srmech.amsc import run_descriptor
run_descriptor("rbs_lm")  # adapter precheck → fetch → encode → validate → save
```

If disk is insufficient, the user gets a clear error pointing to `srmech.amsc.storage.cleanup_caches()` to free space, rather than a mid-download `OSError: No space left on device`. **This brings the disk-space discipline into the same "srmech does it for you" envelope as everything else** — consistent with the "unquantized LLM at edge" framing.

---

## §1 Goal

Per user direction 2026-05-25: protect future model fetches from filling the disk; provide a clean way to clean regenerable caches when storage tightens. Document the 100% disk constraint we discovered this session, which is the operational context for any "download a larger model" direction.

---

## §2 Inheritance

| Source | Inherited finding | Use |
|---|---|---|
| HARDWARE_AND_THREADING.md §1 | 2009 Xeon E5530 envelope (98 GB disk; 96 GB RAM; no GPU) | The hardware on which these utilities run |
| R-RBS-LM-12 §6 | Upstream-to-srmech plan for v0.5.0rc | This module is one piece of `srmech.amsc.storage` future package |
| `[[user_stance_hardware_age_not_penalty_for_sharing]]` | Hardware age informs sharing decisions | Storage limits motivate sharing produced hypervectors when license allows |
| R-RBS-LM-11 §3.2 | vocab_table.npy is the largest regenerable cache (49 MB; 4s rebuild) | Primary cleanup target |
| R-RBS-LM-13 .gitignore | `vocab_table.npy` gitignored | Confirms it's intentionally not committed; safe to delete |

---

## §3 Implementation

`docs/srmech/rbs_lm_research/storage_management.py` — stdlib-only (no venv dependency). 200 lines including CLI + tests + the three core functions.

### §3.1 Core API

```python
def disk_summary(verbose=True) -> dict
def cleanup_caches(remove_vocab_table=True, hf_models=None, verbose=True) -> int
def precheck_fetch(estimated_bytes, safety_margin_gb=1.0, label="") -> dict
class StorageInsufficientError(RuntimeError)
```

### §3.2 Design choices

- **stdlib-only**: no torch / transformers / huggingface_hub dependency. Anyone with Python 3.11+ can run this; no need to be in the research venv.
- **`shutil.disk_usage("/")`**: queries the root filesystem (where most caches live on this hardware). Could be parameterized for multi-disk systems; not needed here.
- **`safety_margin_gb`**: default 1 GB headroom beyond the fetch. Calibrated for the BCI-companion-class storage envelope (8 GB SSDs are common); 1 GB margin is ~12% of an 8 GB device. For larger machines, callers can pass smaller margins.
- **HF cache cleanup uses `models--{name}` pattern**: matches HuggingFace's cache directory structure (`~/.cache/huggingface/hub/models--{user}--{name}/`).

### §3.3 What the module does NOT do

- Doesn't query HuggingFace Hub for actual model sizes — caller passes `estimated_bytes`. Easy future addition (`huggingface_hub.model_info(name).siblings`).
- Doesn't manage non-HF caches (npm, apt, pip wheel caches, etc.).
- Doesn't auto-cleanup the venv — keeping the venv is intentional.

---

## §4 Verification — captured runs

### §4.1 disk_summary

```
=== Disk status ===
  /: 92.2 GB used / 97.9 GB total (0.65 GB free; 94% used)
  ⚠️  WARNING: disk >= 85% used — consider cleanup before fetching

=== Research artefacts ===
  vocab_table.npy:  49.1 MB  (regenerable in ~4s; gitignored)
  rbs_lm_research/: 49.8 MB total (includes the vocab table)
  committed instruments (7 files): 0.0 MB

=== Caches ===
  HF cache:         525.5 MB (re-downloadable from HuggingFace)
  venv (rbs-lm):    1044.6 MB (keep — needed for our scripts)
```

### §4.2 precheck_fetch — 3 scenarios verified

```
Test 1 (small fetch, 100 MB + 0.1 GB margin):
  PASS — headroom after: 467 MB

Test 2 (gpt2-medium, 1.4 GB + 0.5 GB margin):
  correctly raised — free=669.2 MB; need=1912.0 MB

Test 3 (MiniMax M2.5 int4, ~115 GB + 1 GB margin):
  correctly raised — free=669.2 MB; need=118784.0 MB
```

All three tests behave as designed. Small fetches pass; medium fetches that would actually fail are caught; large fetches (MiniMax-class) are caught at the order-of-magnitude level.

---

## §5 Integration points

How the existing encode/harvest scripts should call precheck (small, focused changes):

### §5.1 baseline_measurement.py (R-RBS-LM-3)

Before `GPT2LMHeadModel.from_pretrained("gpt2")`:

```python
from storage_management import precheck_fetch
precheck_fetch(estimated_bytes=500 * 1024**2, safety_margin_gb=0.5,
               label="gpt2 (~500 MB)")
```

### §5.2 Future fetches

Any partition that fetches a different model (R-RBS-LM-23 MiniMax descriptor for documentation; R-RBS-LM-24 alternative source like Phi-3-mini ~7.6 GB; etc.) calls precheck with the appropriate `estimated_bytes`.

### §5.3 vocab_table regeneration (rbs_lm_inference.py)

The existing `precompute_vocab_table()` checks cache and rebuilds if missing. With storage_management, the script can also call `cleanup_caches(remove_vocab_table=True)` between sessions to free 49 MB when desk space is tight. Existing behavior is preserved.

---

## §6 Future upstream (srmech.amsc.storage)

Per R-RBS-LM-12 §6 upstream-to-srmech plan, the srmech-fix session would move this into the package:

```
docs/srmech/python/srmech/amsc/storage.py    # new module
docs/srmech/python/tests/test_amsc_storage.py
```

Wire it into the `compute_from_source` adapter so adapter resolution automatically calls `precheck_fetch()` before model download. Surface `cleanup_caches()` as a CLI command via the existing `srmech` entrypoint (if there is one) or as a documented module-call.

Per R-RBS-LM-13 §5 forward-spec'd discipline: until that lands, the research-subtree version is the canonical implementation, used by hand by the scripts in this subtree.

---

## §7 Findings

**Finding 1 — Disk is at 94% used (670 MB free).** Per §4.1. Critical context for any future model-fetch direction; the immediate workspace has space for partition REPORTs + git commits but not for new dense LLM downloads.

**Finding 2 — The three-utility pattern is sufficient for the immediate need.** Per §3-§5. `disk_summary` informs; `cleanup_caches` frees; `precheck_fetch` guards. Each is small, testable, and stdlib-only.

**Finding 3 — Precheck correctly identifies MiniMax M2.5 as un-fetchable on this hardware.** Per §4.2 Test 3. MiniMax M2.5 int4 quantized (~115 GB) far exceeds our 98 GB total disk; the descriptor-only AMSC entry (deferred per user direction) is the right call.

**Finding 4 — Cleanup of regenerable artefacts can free ~575 MB instantly** (vocab_table.npy 49 MB + HF gpt2 cache 526 MB). This is enough to drop the disk from 94% to ~93% — not transformative, but useful if a fetch is just slightly over the line. Bigger cleanups would need to look outside our research subtree (the 49 GB gitlab + 20 GB download directories are the bulk of disk usage and not ours to manage).

**Finding 5 — The accessibility framing extends to storage.** Per `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` + §0 walkthrough. BCI-companion-class devices often have 8-32 GB SSDs; the precheck + cleanup pattern protects users on those devices the same way it protects this 2009 workstation. **Storage discipline is part of "unquantized LLM at edge."**

**Finding 6 — The "human walkthrough" §0 pattern is operational.** Per `[[feedback_human_coherent_steps_in_reports]]`. This REPORT is the first to apply it; the three-paragraph what/how/srmech-automates structure reads cleanly for someone unfamiliar with the deeper framework.

---

## §8 Open threads (not blockers for partition close)

- **HuggingFace Hub `model_info()` integration for precheck** — would let `precheck_fetch` query actual model size instead of hard-coded estimates. ~10 lines additional code.
- **srmech-fix session upstream work** — move this module to `srmech.amsc.storage`; wire into `compute_from_source` adapter; add tests.
- **Multi-disk support** — if a system has separate disks for ~/.cache vs ~/.venvs, the current single-path query is incomplete. Future enhancement.
- **Automatic-cleanup-on-low-disk** — could add a "fetch policy" that auto-cleans regenerable caches if precheck fails marginally. Currently the user has to call cleanup manually after a precheck raise.

---

## §9 Closing — partition status

**Status:** CLOSED. Three storage utilities implemented + verified; ready for any future fetch direction to use precheck before downloading. The 100% disk constraint discovered this session is now documented + has guardrails.

**Falsifiers:**

1. A precheck call that fails to detect actually-insufficient disk — **not encountered** in the 3 tested scenarios.
2. A claim that this fixes the 94% disk usage — **explicitly disclaimed §7 Finding 4**; we don't manage external dirs; cleanup of our caches frees ~575 MB at most.
3. A claim that storage management makes MiniMax M2.5 fetchable — **disclaimed**; M2.5 is structurally too large for this 98 GB disk in any quantization tested.

**Inherits to:** any subsequent partition that fetches a model or large dataset. The precheck pattern is the load-bearing safety net.

**SSoT marker:** at SSoT absorption, §0 human walkthrough + §3 design + §5 integration pattern + §6 upstream plan absorb into `srmech_research_notebook.md` as a new §RBS-LM-storage subsection. The pattern is reusable for any srmech catalog that involves resource-significant fetches.
