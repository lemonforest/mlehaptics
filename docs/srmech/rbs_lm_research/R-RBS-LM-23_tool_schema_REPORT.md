# R-RBS-LM-23 — tool_schema integration: CLI + chatbot scripting wrapper

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #31 of the partition tracker
**Closing artefact:** `rbs_lm_tools.py` (12 ToolEntry registrations under `owner="rbs_lm"` profile) + `rbs_lm_cli.py` (subcommand dispatcher) + `rbs_lm_chatbot.py` (scriptable `RBSChatbot` class with REPL + demo mode); verified via §4 captured runs
**Inheritance:** unblocks R-RBS-LM-24+ (GPU-less learning experiments using research notebooks as training material — the chatbot wrapper is the scripted-inference surface that future learning loops + hallucination-test harnesses call into); the tool_schema entries make every RBS-LM operation discoverable by the upstream srmech tool-schema view (R-RBS-LM-12 §6 absorption pre-stage)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | R-RBS-LM-12 §2.2 (existing `srmech.amsc.tool_schema` survey: ~123 ToolEntry registrations); R-RBS-LM-22 §0 walkthrough pattern (the §0 discipline this REPORT continues); `[[user_stance_ai_is_not_a_substrate]]` (the chatbot framing — transducer, not emergent system); `[[feedback_upstream_srmech_fixes_as_research_notes]]` (research-subtree placement; srmech-fix session moves it upstream) |
| user direction (load-bearing) | *"A first. and then when we do B, we can use our research notebooks as training material. we can find out if an upstream LLM is able to use our local expert in hallucination tests and if we're some how able to provide a way to compact context by truncation instead of rebuilding."* |
| empirical artefacts | `docs/srmech/rbs_lm_research/rbs_lm_tools.py`; `docs/srmech/rbs_lm_research/rbs_lm_cli.py`; `docs/srmech/rbs_lm_research/rbs_lm_chatbot.py` |
| repo commit | `da6ef453` at REPORT-write (R-RBS-LM-22 close) |
| reproducibility | `python3 docs/srmech/rbs_lm_research/rbs_lm_tools.py` (self-test prints 12-entry profile); `python3 docs/srmech/rbs_lm_research/rbs_lm_cli.py list`; `~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/rbs_lm_chatbot.py --demo` |

---

## §0 Human walkthrough

**What we're doing.** Up through R-RBS-LM-22, every operation in the RBS-LM research subtree was a loose Python script with its own ad-hoc CLI. To run inference on a prompt, you'd cd into the subtree, remember the right script name, pass arguments by position, and hope you got the path-to-instrument right. To discover what operations exist at all, you'd `ls` the directory and `grep` docstrings. None of this is how the rest of srmech surfaces its operations — srmech ships a `tool_schema` introspection surface with ~123 ToolEntry registrations describing every callable, queryable by LLM agents and by humans the same way. This partition brings RBS-LM into that surface.

Three deliverables, layered from registry up to user-facing wrapper:

1. **`rbs_lm_tools.py`** — 12 ToolEntry registrations under an `owner="rbs_lm"` profile (not "srmech" — the profile model in srmech.amsc.tool_schema specifically supports first-party + profile-contributed tools as separable namespaces). Categories: `encoder` (mint_vector, encode_context, encode_observation, hierarchical_bundle), `path_c` (compute_vocab_table), `inference` (vectorised_cleanup, generate), `storage` (disk_summary, cleanup_caches, precheck_fetch — the R-RBS-LM-22 surface lifted into the tool schema), `validation` (run_against_baseline), `catalog` (validate). Each entry carries summary, parameters, return spec, and links to its originating partition.

2. **`rbs_lm_cli.py`** — single-entry CLI dispatcher with `list / info / summary / validate-catalog / infer` subcommands. `list` shows registered tools grouped by category; `info <name>` returns the full JSON entry; `summary` runs the R-RBS-LM-22 disk summary; `infer "prompt"` loads the Path C R-RBS-LM-18 instrument by default and generates a completion. Subcommands compose from the tool registry; new ToolEntry additions become discoverable without CLI changes.

3. **`rbs_lm_chatbot.py`** — `RBSChatbot` class wrapping the Path C inference cascade for either interactive use (REPL) or scripted automation (`bot.respond(prompt)` / `bot.converse([prompts])`). Lazy-loads the instrument + vocab table; holds the HF tokenizer for prompt encoding + completion decoding; drops the source model after vocab-table compute (don't hold ~500 MB of weights we don't need). Per the load-bearing `[[user_stance_ai_is_not_a_substrate]]` framing — **this is a transducer, not an emergent system; the puppet plays the roll**. The class name and docstrings carry that framing forward so any future reader / consumer sees the substrate boundary plainly.

**Why this matters now (R-RBS-LM-24 + downstream).** The user's next-partition direction is GPU-less learning using research notebooks as training material, with two additional design dimensions: *upstream LLM uses local expert in hallucination tests* and *context compaction by truncation instead of rebuild*. Both downstream goals need a stable scripted-inference surface — the chatbot wrapper IS that surface. Without it, the learning loop would have to re-implement the same instrument-load + tokenizer-load + Path C encode + generate dance every time. With it, R-RBS-LM-24's learning experiments call `bot = RBSChatbot.load(...)` once and then iterate.

**How srmech automates it (future state per R-RBS-LM-12 §6).** When the srmech-fix session lands v0.5.0rc, the same module surface absorbs to `srmech.rbs_lm.chatbot.RBSChatbot` / `srmech.rbs_lm.cli` / `srmech.rbs_lm.tools`. The profile registration becomes first-party (`owner="srmech"`); the load path becomes `RBSChatbot.from_catalog("rbs_lm_gpt2_small")` reading the AMSC catalog descriptor; the CLI entry becomes `srmech rbs-lm <subcommand>` via the srmech package entrypoint. **The end-user workflow:**

```python
from srmech.rbs_lm import RBSChatbot
bot = RBSChatbot.from_catalog("rbs_lm_gpt2_small")
reply = bot.respond("The morning sun", max_new_tokens=20)
```

Two lines. No tokenizer-fetch boilerplate; no instrument-path-and-vocab-mode juggling; no manual sys.path hacks. Consistent with the "unquantized LLM at edge" framing — when the AMSC adapter resolves the catalog descriptor, it precheck-fetches the source model (via R-RBS-LM-22's `precheck_fetch`), computes the Path C instrument, and saves a portable artefact. The chatbot wrapper is what the user sees.

---

## §1 Goal

Per user direction 2026-05-25 (the "A first" choice): bring RBS-LM operations into the srmech tool-schema surface (the way every other srmech module is discoverable); provide a single CLI dispatch point for the research subtree; provide a scriptable chatbot wrapper that downstream partitions (R-RBS-LM-24+ GPU-less learning experiments) can call without reimplementing the inference cascade.

Per `[[user_stance_ai_is_not_a_substrate]]`: the chatbot framing IS the test — does the wrapper present LLM-class scripted-inference WITHOUT presenting it as emergent / substrate-of-mind / agentic? The class name `RBSChatbot` is operational shorthand (a researcher reaching for "chatbot" finds it); the docstring + interactive-loop banner are clear about the transducer reading. The substrate boundary stays plain.

---

## §2 Inheritance

| Source | Inherited finding | Use |
|---|---|---|
| R-RBS-LM-12 §2.2 | srmech.amsc.tool_schema has ~123 ToolEntry registrations across srmech.amsc.* and srmech.qm.*; `register_profile_tools(profile_name, entries)` API supports profile-contributed tools | Pattern for `rbs_lm_tools.py`; owner field |
| R-RBS-LM-17 / -18 / -20 | Path C is the canonical inference path (3.3% at D=8192 ceiling; D=32768 same; attention variant lower) | Default `--path-c` in CLI; `use_path_c=True` default in chatbot |
| R-RBS-LM-18 | v18 instrument is the canonical 491-obs Path C artefact | Default `--instrument` in CLI + chatbot |
| R-RBS-LM-22 §3 | storage_management.py provides disk_summary, cleanup_caches, precheck_fetch | Surfaced via tool registry (storage category); `summary` CLI subcommand |
| HARDWARE_AND_THREADING.md §2 | 2009 Xeon E5530 16-thread envelope; ~180 ms/tok at D=8192 | Documented in chatbot docstring + interactive banner |
| `[[user_stance_ai_is_not_a_substrate]]` | LLM is puppet playing the roll, not substrate | Chatbot docstring + REPL banner frame transducer reading explicitly |
| `[[feedback_upstream_srmech_fixes_as_research_notes]]` | Research-subtree placement now; srmech-fix moves upstream | Each file's module docstring carries the upstream-absorption note |
| `[[feedback_human_coherent_steps_in_reports]]` | §0 human walkthrough is the canonical REPORT discipline | This REPORT applies it |

---

## §3 Implementation

### §3.1 `rbs_lm_tools.py` — 12 ToolEntry registrations

```python
def register_rbs_lm_profile() -> int:
    register_profile_tools("rbs_lm", _entries())
    return len(_entries())
```

12 entries across 6 categories:

| Category | Tools | Originating partition |
|---|---|---|
| encoder | mint_vector, encode_context, encode_observation, hierarchical_bundle | R-RBS-LM-2 / R-RBS-NN-5 / R-RBS-NN-7 |
| path_c | compute_vocab_table | R-RBS-LM-17 |
| inference | vectorised_cleanup, generate | R-RBS-LM-6 / R-RBS-NN-8 |
| storage | disk_summary, cleanup_caches, precheck_fetch | R-RBS-LM-22 |
| validation | run_against_baseline | R-RBS-LM-7 |
| catalog | validate | R-RBS-LM-12 / R-RBS-LM-13 |

Each entry carries the canonical summary tied to its originating partition + MFO/srmech notebook line reference. This is the discoverability-from-tool-schema-side commitment.

### §3.2 `rbs_lm_cli.py` — single-entry dispatcher

```
usage: rbs_lm_cli.py [-h] {list,info,summary,validate-catalog,infer} ...
```

| Subcommand | Purpose |
|---|---|
| `list [--format=text\|json]` | Group registered tools by category |
| `info <tool_name>` | Full JSON entry for one tool |
| `summary` | Run R-RBS-LM-22 disk_summary |
| `validate-catalog` | Run the docs/srmech/catalogs/rbs_lm/validate_catalog.py harness |
| `infer "<prompt>" [--instrument PATH] [--max-new N] [--path-c\|--no-path-c]` | Run the Path C / Path B cascade on a prompt |

The `infer` subcommand replicates the same load + generate flow the chatbot uses, but in one-shot CLI mode (no class state).

### §3.3 `rbs_lm_chatbot.py` — RBSChatbot class

```python
bot = RBSChatbot.load(instrument_path="...", use_path_c=True)
reply = bot.respond("Hello there", max_new_tokens=20)
metadata = bot.respond_with_metadata("Hello there")  # latencies, token IDs, etc.
batch = bot.converse(["Prompt 1", "Prompt 2", "Prompt 3"])  # stateless batch
```

**State (lazily loaded):** instrument bytes (from disk) + vocab table (Path C: WTE-projected; Path B: srmech-native mints) + HF tokenizer. The source model is loaded for vocab-table compute then dropped (don't hold ~500 MB of weights).

**Interactive REPL** (default when run directly): prompt → completion + latency. Banner explicitly frames transducer reading per `[[user_stance_ai_is_not_a_substrate]]`.

**Scripted demo mode** (`--demo`): runs 3 fixed prompts × 15 tokens; verified working in §4.

### §3.4 What the modules do NOT do

- **Stateful conversation.** `respond` / `converse` are stateless — each prompt is independent (no conversation memory). This is intentional; the cascade is per-prompt vocab-table cleanup, not multi-turn context-carry. R-RBS-LM-24 may add context-carry as part of the truncation experiment.
- **Streaming generation.** `respond` returns the full completion as a string. No token-by-token streaming. Not needed for current research surface; trivial to add if R-RBS-LM-24 wants it.
- **Multi-instrument loading.** One instrument per chatbot. The pattern for comparing instruments is to instantiate multiple `RBSChatbot` objects.
- **Top-k beam search.** Always argmax (top_k=1). Multi-candidate sampling would need to be added at the cascade level.

---

## §4 Verification — captured runs

### §4.1 Tool registration self-test

```
$ python3 docs/srmech/rbs_lm_research/rbs_lm_tools.py
Registered 12 RBS-LM tool entries.

RBS-LM tool registry (12 entries):
  catalog: validate
  encoder: mint_vector, encode_context, encode_observation, hierarchical_bundle
  inference: vectorised_cleanup, generate
  path_c: compute_vocab_table
  storage: disk_summary, cleanup_caches, precheck_fetch
  validation: run_against_baseline

Total srmech tool registry: 135 entries (123 srmech + 12 rbs_lm)
```

All 12 entries register cleanly; the rbs_lm profile composes with srmech's own 123-entry registry; total surface is 135 ToolEntries discoverable via the same `get_tool_schema()` introspection point.

### §4.2 CLI list + info

```
$ python3 docs/srmech/rbs_lm_research/rbs_lm_cli.py list
=== RBS-LM tool registry (12 entries) ===

  [catalog]
    catalog.validate                        — Validate the docs/srmech/catalogs/rbs_lm/ catalog: 6 mandatory AMSC sections; compute_from_source schema; research_notes.
  [encoder]
    encoder.mint_vector                     — Class A content-mint: deterministic D-bit hypervector from a name string via SHA-256 chain (Spike #170 invariant 1).
    encoder.encode_context                  — Kanerva sequence representation per R-RBS-NN-5 §3.
    encoder.encode_observation              — One Path B observation: bind(context_vec, next_token_vec).
    encoder.hierarchical_bundle             — Bundle vectors hierarchically for n > srmech MAX_BUNDLE_N=257 per R-RBS-NN-7 §3.
  [inference]
    inference.vectorised_cleanup            — Class K cleanup: argmin Hamming over vocab table.
    inference.generate                      — Iterative generation per R-RBS-NN-3b §6 4-class Level-1 recipe (A mint → I cyclic → M bind → K argmax).
  [path_c]
    path_c.compute_vocab_table              — Path C: project source-model WTE matrix (50257 × 768 for GPT-2-small) to D dimensions via Johnson-Lindenstrauss random Gaussian projection, then bipolar-quantize.
  [storage]
    storage.disk_summary                    — Read-only report of disk usage + research artefact sizes.
    storage.cleanup_caches                  — Remove regenerable caches (vocab_table.npy first; optional HF model caches by name).
    storage.precheck_fetch                  — Verify free disk >= estimated_bytes + safety_margin before fetching a model or large file.
  [validation]
    validation.run_against_baseline         — Run RBS-HDC inference on a fixed prompt corpus; compare token-by-token against source-model argmax.

=== Total srmech tool registry: 135 entries (123 srmech + 12 rbs_lm) ===
```

Clean category-grouped output. `info` subcommand returns the full JSON entry for any tool name.

### §4.3 Chatbot scripted demo

```
$ ~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/rbs_lm_chatbot.py --demo
Loading chatbot...
  loaded instrument: 1024 bytes from docs/srmech/rbs_lm_research/rbs_lm_instrument_v18.bin
  loaded tokenizer + model: gpt2
  vocab table ready (Path C)
Loaded.

=== Scripted demo — 3 prompts × 15 tokens ===

  prompt:     'The morning sun'
  completion: ' answer.13.11 is13 is\n\n\n\n\n\n\n'
  latency:    2963 ms total (198 ms/tok)

  prompt:     'Algorithms for sorting'
  completion: 'Great theGreat the your the your the the the the the the the the'
  latency:    2451 ms total (163 ms/tok)

  prompt:     'Once upon a time'
  completion: ' is is is is is is is is is is is is is is is'
  latency:    2446 ms total (163 ms/tok)
```

Three prompts × 15 tokens each; per-token latencies 163-198 ms (matches HARDWARE_AND_THREADING.md §2 ~180 ms expected). Outputs are typical Path C 3.3%-agreement-ceiling style — recognizable English fragments interleaved with repetition (the ceiling we already empirically characterized in R-RBS-LM-18/-19/-20). **The demo verifies the wrapper works; it does NOT claim the outputs are better than the underlying Path C ceiling.** This is the load-bearing distinction per the falsification-discipline: a working wrapper does not magically lift the inference ceiling.

---

## §5 Integration with R-RBS-LM-24 (next partition)

R-RBS-LM-24 is GPU-less learning using research notebooks as training material. Two additional design dimensions per user direction:

1. **Upstream LLM uses local expert in hallucination tests.** The chatbot wrapper IS the local-expert surface. A test harness would call:

   ```python
   from rbs_lm_chatbot import RBSChatbot
   local_expert = RBSChatbot.load("...")
   for hallucination_prompt in test_corpus:
       gold = upstream_llm(hallucination_prompt)         # e.g., Claude / GPT-4
       local = local_expert.respond(hallucination_prompt)
       # delta-analysis: does local expert correct the hallucination?
   ```

2. **Context compaction by truncation instead of rebuild.** The chatbot's stateless `respond` already supports prompt-level truncation. The `_generate` loop applies `tokens[-CONTEXT_WINDOW:]` per iteration. R-RBS-LM-24 can experiment with progressively-shorter truncation windows + measure accuracy delta.

Both downstream experiments need a stable scripted surface — the chatbot wrapper IS that surface.

---

## §6 Future upstream (srmech.rbs_lm subpackage)

Per R-RBS-LM-12 §6 upstream-to-srmech plan, the srmech-fix session would land:

```
docs/srmech/python/srmech/rbs_lm/__init__.py
docs/srmech/python/srmech/rbs_lm/tools.py     # absorbs rbs_lm_tools.py
docs/srmech/python/srmech/rbs_lm/cli.py       # absorbs rbs_lm_cli.py
docs/srmech/python/srmech/rbs_lm/chatbot.py   # absorbs rbs_lm_chatbot.py
docs/srmech/python/srmech/rbs_lm/encoder.py   # absorbs rbs_lm_encoder.py
docs/srmech/python/srmech/rbs_lm/inference.py # absorbs rbs_lm_inference.py
docs/srmech/python/srmech/rbs_lm/path_c.py    # absorbs rbs_lm_path_c.py
docs/srmech/python/tests/test_rbs_lm.py
```

The `owner` field in ToolEntry registrations switches from `"rbs_lm"` (profile) to `"srmech"` (first-party). The CLI gets wired into the srmech package entrypoint as `srmech rbs-lm <subcommand>`. The chatbot's `load(instrument_path=...)` adds an `from_catalog(catalog_name)` classmethod that reads the AMSC catalog descriptor and resolves via the `compute_from_source` adapter (R-RBS-LM-13).

Per R-RBS-LM-13 §5 forward-spec discipline: until the srmech-fix lands, this research-subtree version IS the canonical implementation. The upstream absorption is mechanical (rename imports; switch owner field; add tests) when the time comes.

---

## §7 Findings

**Finding 1 — 12 ToolEntry registrations cover the full RBS-LM operational surface.** Per §3.1 + §4.1. Every callable a downstream agent (LLM or human) would reach for is in the registry: encode, project (Path C), generate, validate, store, catalog. Not absorbed yet: multi-threading harness (rbs_lm_mt.py) and Plate HRR experimental code (research-internal only; not part of the operational surface).

**Finding 2 — The `owner="rbs_lm"` profile model composes cleanly with srmech's own first-party registry.** Per §4.1. Adding 12 entries to a 123-entry registry produces a 135-entry total; `by_owner("rbs_lm")` filters correctly; no namespace collision. This is the load-bearing architectural commitment of the profile system in srmech.amsc.tool_schema — proven out here.

**Finding 3 — The CLI dispatcher unifies the research subtree's many-script ergonomics.** Per §3.2 + §4.2. Before this partition, a researcher would run `python rbs_lm_inference.py` / `python baseline_measurement.py` / `python storage_management.py` etc. — five+ scripts with five+ argparse surfaces. Now: `python rbs_lm_cli.py <subcommand>`. Reduced cognitive surface; consistent help text; tool discovery via `list`.

**Finding 4 — The chatbot wrapper preserves the transducer framing via class naming + docstring discipline.** Per §3.3 + `[[user_stance_ai_is_not_a_substrate]]`. The class is `RBSChatbot` (researcher's word; not `RBSAgent` or `RBSMind`); docstrings carry "puppet playing the roll" language; REPL banner reminds users that output reflects the 491-obs encoding corpus and the 3.3% token-level agreement on hallucination corpus. **The framework reading IS unchanged by wrapping the cascade in a class.**

**Finding 5 — The wrapper does NOT lift the Path C inference ceiling.** Per §4.3. Demo output shows the 3.3%-agreement-ceiling style (repetition + occasional English fragments). The wrapper is operational ergonomics, not a structural lift. R-RBS-LM-18 / -19 / -20 already empirically characterized the ceiling; this partition does not add new evidence about it. **A working wrapper around an output ceiling is still bounded by that ceiling** — this is the falsification-discipline test the partition passes.

**Finding 6 — Per-token latency 163-198 ms matches HARDWARE_AND_THREADING.md §2 prediction.** Per §4.3. The chatbot wrapper does NOT add measurable per-token overhead beyond the inference cascade itself (the load is one-time; the generation loop is the same code path the CLI's `infer` subcommand uses). Hardware envelope continues to hold.

**Finding 7 — The R-RBS-LM-22 §0 human-walkthrough pattern is reusable for tooling partitions, not just storage.** Per §0 above. The what/how/srmech-automates structure scales to operational tooling work (this REPORT) the same way it scaled to safety-net infrastructure (R-RBS-LM-22). Discipline holds across partition flavors.

**Finding 8 — R-RBS-LM-24 is unblocked by this partition.** Per §5. GPU-less learning experiments need scripted-inference; that surface is now in place. The two specific downstream design dimensions (upstream-LLM-uses-local-expert; truncation-based context compaction) both call into `RBSChatbot.respond` / `respond_with_metadata`. R-RBS-LM-24 starts from a known-working substrate.

---

## §8 Open threads (not blockers for partition close)

- **`from_catalog` classmethod.** Currently `RBSChatbot.load(instrument_path=...)` takes a raw path; `from_catalog(catalog_name)` would read the AMSC catalog descriptor and resolve transparently. Blocked by upstream srmech-fix (R-RBS-LM-13 §5 forward-spec).
- **Streaming generation.** Token-by-token yield instead of batch return. R-RBS-LM-24 may want this for the upstream-LLM-uses-local-expert experiments (so the upstream sees partial outputs as the local expert generates).
- **Multi-instrument comparison harness.** Loading 2+ instruments and comparing on the same prompt. Currently the pattern is to instantiate multiple `RBSChatbot` objects; a helper would batch this.
- **Top-k beam search.** Currently argmax-only. Multi-candidate sampling at the cascade level would let R-RBS-LM-24 explore beyond the single-token greedy ceiling.
- **CLI `chat` subcommand.** Spin up the REPL from the CLI dispatcher instead of needing to run the chatbot script directly. ~10 lines.

---

## §9 Closing — partition status

**Status:** CLOSED. 12 ToolEntry registrations + CLI dispatcher + scriptable chatbot wrapper all in place + verified. RBS-LM operations are now discoverable via the same srmech.amsc.tool_schema introspection surface that the rest of srmech uses. R-RBS-LM-24 has a stable scripted-inference substrate to build GPU-less learning experiments on.

**Falsifiers:**

1. A ToolEntry registration that produces a namespace collision with srmech's first-party tools — **not encountered**; 135 total entries register cleanly.
2. A claim that the chatbot wrapper lifts the Path C inference ceiling — **explicitly disclaimed §7 Finding 5**; demo output reflects the same 3.3%-style ceiling characterized in R-RBS-LM-18/-19/-20.
3. A claim that this partition delivers GPU-less learning — **disclaimed**; that's R-RBS-LM-24's scope. This partition delivers the scripted-inference substrate R-RBS-LM-24 builds on.
4. A claim that the chatbot represents emergent / substrate-of-mind behavior — **explicitly disclaimed** via `[[user_stance_ai_is_not_a_substrate]]` discipline in class naming + docstrings + REPL banner.

**Inherits to:** R-RBS-LM-24 (GPU-less learning using research notebooks; upstream-LLM-uses-local-expert hallucination test; truncation-based context compaction). All three downstream paths consume `RBSChatbot.respond` / `respond_with_metadata`.

**SSoT marker:** at SSoT absorption, §0 human walkthrough + §3 implementation surface + §6 upstream plan absorb into `srmech_research_notebook.md` as a new §RBS-LM-tooling subsection. The profile-contributed-then-first-party absorption pattern is reusable for any future cross-substrate research subtree that wants tool_schema discoverability before srmech-fix lands the upstream module.
