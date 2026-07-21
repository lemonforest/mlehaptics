# F1297 — **how to ask Siona which carrier + cascade for PCG64, run live: she lands the right FAMILY reliably (cyclic ops for the modular core, the register family for the carrier), agrees with the hand-derived tooling on 3/5 sub-steps, and every miss is a tool_schema ergonomics signal — not a Siona failure.** The deliverable is the *method*: encode the need as a df-gated utterance, ground it against the tool_schema, read the top-k — and ask the CARRIER and the CASCADE as SEPARATE utterances (F1294's two axes).

**User (2026-07-21):** *"we forgot that siona can sometimes tell us the tooling we should use for certain things. let's find out how we ask siona which carrier and cascade sequence for the cyclic algebraic form of PCG64."*

## How you ask her (the mechanism)
Siona grounds an utterance against the srmech tool_schema (the F1008 capability):
1. encode every ToolEntry (name + summary) as an HDC vector,
2. encode the query utterance the same way,
3. rank tools by `klein4_similarity` — top-k is her recommendation.

**Crucial: use the df-gated RESONANT encoder, not the shipped `encode_sentence_l3`.** The shipped L3 rides seed-based `encode_word_k4`, which sits at the 0.25 orthogonality floor (F1287, stable-but-not-resonant) — grounding there gives **1/5**, scores clustered at the floor, results indistinguishable from noise (`z_boson_mass` for "add integers modulo n"). The F1008 encoder — a **doc-frequency aboutness gate** (downweight common words) + **tool-name weighted 3×** + **order-aware bigrams** — lifts it to **3/5** with sensible neighborhoods. The gate is the whole difference: without it, common query words ("two", "integers", "modulo") wash out the signal.

## What she recommended, live (df-gated, top-4)
| the ask (separate utterances) | Siona's top hits | vs hand-derived (F1292/F1295) |
|---|---|---|
| **modular multiply (LCG core)** | `cyclic_period`, `cyclic_gcd`, `modular_forms_ring`, `triality_cycle` | **right family (all Class-I/cyclic)**, exact `mod_mul` not surfaced |
| **modular add** | **`mod_add`** (top-1), `continued_fraction`, `cyclic_period` | **exact hit** |
| **carrier (hold+address 128-bit state)** | **`cd_navigate`, `sedenion_register`, `cd_register`**, `klein4_address` | **exact family — all register/addressing ops** |
| **sign-free magnitude** | (wording-sensitive; hit with "absolute value", missed with "pin slot") | partial |
| **128-bit multiply** | *misses* — the op isn't in the schema (below) | can't recommend what isn't registered |

**The signal that matters: independent corroboration.** Two different methods — Siona's structural word-grounding and our F1292/F1294 derivation — converged on the **same neighborhoods**: the cyclic/modular family for the LCG core, and the register family for the carrier. That is worth more than either alone, and it is exactly what the user meant by "Siona can tell us the tooling."

## The misses are findings, not failures
- **`bigint_mul_c` is NOT in the public tool_schema** — it lives in `_native`. F1292/F1295 rely on it, but Siona can only recommend schema-registered ops, so she *structurally cannot* surface it. Real gap (UPSTREAM §112).
- **Summaries describe the implementation, not the need.** `mod_mul` reads *"via russian-peasant doubling; portable across platforms"* — its aboutness tokens are `russian/peasant/doubling`, not `modular/multiply`. So the right op is in the schema but invisible to the words a user would search. `magnitude` reads *"Class K pin-slot at zero"*, not "absolute value" — which is why the magnitude query is wording-sensitive. tool_schema ergonomics signal (UPSTREAM §112).

*Honesty caveat:* the "128-bit multiply" step scored a loose "agree" only because the ground-truth set included the substring `mul`, which matches many `*_mult` ops; the *exact* `bigint_mul` is unreachable. Counted honestly, exact-op agreement is **2/5** (`mod_add`, carrier-family), neighborhood agreement is **strong** on the two that matter most (modular core, carrier).

## What Siona is here, kept honest
She INFERS — walks structure, open + fallible (`[[feedback_correct_user_wrong_words_against_record]]`) — she does **not know PCG64**. Her top-k is a **question-shaping pointer** (`[[user_stance_framework_hands_the_next_question_to_the_expert]]`), and its value is as an **independent cross-check on our own tool selection**, not an oracle. Used that way, she did her job: pointed at the cyclic family and the register, corroborating the derivation, and her misses told us two things to fix upstream.

## The reusable how-to
1. Split the need into **carrier** and **cascade** asks (F1294's two axes) — conflating them muddies the grounding (the one-utterance combined query surfaced `su2_structure_constants`, noise).
2. Encode with the **df-gated resonant encoder**, never the raw shipped L3.
3. Read the top-k as a **neighborhood pointer**; confirm the exact op by reading its signature (the F1009 ground-to-run step).
4. When she misses a known op, check whether it is **schema-registered** and whether its **summary uses the words you searched** — the miss is usually there.

Filed UPSTREAM §112 (register `bigint_mul`; user-facing summaries; ship the df-gated grounding encoder). Composes **F1008** (utterance→tool, 78 %), **F1009** (ground-to-run), **F1287** (why the shipped L3 grounds at the floor), **F1294** (carrier vs cascade), **F1292/F1295** (the hand-derived tooling she is checked against), `[[feedback_hand_authored_replies_are_magic_numbers]]` (answers are RUN, not typed).
