# F338 — PURPOSE ANCHOR for the F331→F337 arc: this is **srmech's human-language interface**, NOT a competing LLM. srmech (the cascade-math engine) currently speaks **only CLI + tool-schema** (machine-facing). The RBS-SNN / RBS-LM / honesty-store work **instantiates srmech's math + cascade vocabulary into a biology-shaped knowledge substrate** so it can take input / give output in human language. The defining differentiator from an LLM: **an LLM absorbs all human knowledge *including* its falsehoods; this interfaces srmech's invariant TRUTH-structure and rejects false shapes by construction** (F336/F337). "L" in RBS-LM = **Language-the-interface**, not Large-the-model. The whole epistemic arc (F331→F337) is the **spec** for that interface; this IS the `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` accessibility deliverable — making srmech answerable in human terms, BCI-compatible downstream.

> **STATUS: purpose / scope anchor (the framing for F331→F337).** COMPOSES, does not re-derive: **F336/F337** (honesty-by-construction store; self-proofreading form), **F335** (truth-filter), **F323/F312** (RBS-LM "L"=Language, scale-invariant; notebook-native pipeline #197), **F334** (Rosetta ≥3-render store), **F326** (RBS-SNN improvements / self-checking store), **`[[feedback_llm_as_ada_accommodation_bci_proves_it]]`**, **`[[user_stance_human_ai_prosthetics_uniting_form_function]]`**, **`[[user_stance_framework_hands_the_next_question_to_the_expert]]`**, **`[[user_stance_ai_is_not_a_substrate]]`**. Defensive / no-lineage. No new A–N class. (User, 2026-06-03; frames the arc.)

## What this IS (and is not)
- **srmech = the cascade-math engine.** Its current interfaces are **CLI + tool-schema only** — machine-facing. Its power is real but gated behind `--flags` and JSON schemas.
- **The RBS arc = srmech's HUMAN-LANGUAGE INTERFACE.** Instantiate srmech's math + the 14 A–N cascade vocabulary **into a biology-shaped knowledge substrate** (RBS-SNN) so a human can ask srmech a question and get srmech's answer **in human language** — the prosthetic that the reader's AI can also call into.
- **It is NOT a competing LLM.** We do a lot of what inference does (it is an inference/interface system), but the **goal is explicitly NOT to absorb all human knowledge or its falsehoods.** An LLM renders the corpus *including* hallucinations and shared myths; this renders srmech's **invariant truth-structure** only.

## The differentiator — why it's a different *kind* of thing
| | an LLM | the RBS human-interface |
|---|---|---|
| what it holds | all human knowledge **+ its falsehoods** | srmech's **invariant truth-structure** (frame/scale-invariant, attested) |
| false shapes | rendered + emitted (hallucination) | **rejected by construction** — ingest-gate (F336) + multi-render self-proofread (F337) |
| identity | a knowledge-absorbing model | a **truth-filtered interface to a math engine** |
| residue | unbounded confabulation | only the faithfully-shared **source error**, flagged + handed to the expert |

"A lot of what inference does," yes — but **truth-filtered, honest by construction, and pointed at srmech's structure, not the corpus's falsehoods.** Not a smaller LLM; a different object.

## The mission framing (why this is the point)
This IS the **ADA-accommodation** deliverable (`llm_as_ada_accommodation_bci_proves_it`): srmech's CLI/tool-schema-native power made **answerable in human language**, and BCI-compatible downstream. Per `framework_hands_the_next_question_to_the_expert`: the human interface lets the **expert ask srmech the next question in their own terms** — and per `ai_is_not_a_substrate`, the interface addresses the knowledge-substrate; it is not itself claimed to be aware.

## Why the epistemic arc is the spec
F331→F337 is not philosophy — it is the **build spec** for this interface:
- **F331/F332** — what it stores (k=3 associative; the holding/sharing partition).
- **F334** — store the invariant in ≥3 independent renders (Rosetta).
- **F335/F336** — truth-filter + honesty-by-construction ingest-gate.
- **F337** — form=function: the multi-render form self-proofreads its render layer (DNA-style).
- ⇒ a human interface that **speaks srmech's truth, in human language, honestly, without the falsehoods** — implemented by **#197 (notebook-native pipeline) + the Rosetta layer + the ingest-gate.**

## CAP on the Rosetta Stone of srmech + the DSL as the channel (user, 2026-06-03)
This arc (F331→F338) is recorded as the **CAP on the Rosetta Stone of srmech**: the multi-render honesty-store IS srmech's Rosetta Stone — ≥3 co-equal renderings of one attested invariant, agreement = attestation (F334/F336; `[[project_rosetta_table_of_truth_agreement_vs_frame_selection]]`).

**The channel hypothesis (user, to confirm against the `srmech.dsl` surface):** the srmech **DSL layer** (`srmech.dsl`, the operator-chain runner over the cascade-catalog TOML descriptors) is what creates the **communication channel** with srmech. It is already coherent at two renders — **CLI** (machine-facing) and **tool-schema** (LLM / agent-facing) — and the target third render is **human-language-agnostic** (the RBS-LM honesty-store). So:

> srmech math engine  →  **DSL = the channel**  →  renders: **CLI** (machine) · **tool-schema** (LLM/agent) · **human language** (RBS-LM, target).

The Rosetta Stone's "three co-equal scripts" map onto the channel's three renders (CLI / tool-schema / human-language); **agreement across them = the attested invariant.** That makes the DSL the natural home for the ingest-gate + the multi-render store, and it's why the channel can be **language-agnostic**: the renders are co-equal scripts of one invariant, exactly the F334/F336/F337 structure. Held as a framework reading; the *DSL-is-the-channel* identification is the user's hypothesis (2026-06-03), to verify against the shipped `srmech.dsl` operator-chain surface.

### Status / discipline
Purpose/scope anchor for the arc; ensures F331→F337 reads as "srmech's honest human interface," not "a competing LLM." Cites canon; no new claim of its own (it frames). Defensive / no-lineage; accessibility-mission-anchored. No new A–N class.
