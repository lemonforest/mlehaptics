# R-RBS-LM Finding 340 — PURPOSE ANCHOR (generalizes F338): RBS-LM is the natural-language interface to ANY tool-schema package, not just srmech ("a world problem solver")

**Date:** 2026-06-03 · **Kind:** directional anchor (user note "to keep with us as we go") · **Generalizes:** F338 (RBS-LM = the human-language interface to srmech) · **Composes with:** UPSTREAM §17 (catalog→kernel→DSL unification), F334/F335 (truth-filter), the framework-hands-the-next-question stance · **Status:** RECORDED; srmech dev in progress on §17 — **HOLD new build until it returns.**

## The note (verbatim intent)

> *"our RBS-LM interface is also expected to be a natural language interface for any package, such as our ephemerides-spectral. essentially I think we're saying a world problem solver maybe? srmech dev in progress. wait to do new stuff until we come back with it."*

## What it says

**F338 stated:** RBS-LM is the human-language interface to **srmech** — srmech speaks only CLI + tool-schema; RBS-LM is the natural-language skin over it, and the honesty-store (truth-filter) is the differentiator, not a competing LLM.

**F340 generalizes that one level up:** RBS-LM is the natural-language interface to **any tool-schema-exposing package**, not srmech alone. The whole spectral-research portfolio (srmech, **ephemerides-spectral**, antikythera-maths, chess-maths, logo-maths, othello-maths, …) already exposes `tool_schema` registries of attested operations. RBS-LM is the **one human-language surface** over all of them: you ask in natural language → RBS-LM routes to the right package's attested operations → the package computes → the answer comes back through the truth-filter.

**ephemerides-spectral is the worked example.** It is srmech's downstream AMSC consumer (JPL DE441 anchor, 52-body roster, geodetic/magnetic/fluid/dynamical catalogs). "Where will Jupiter be / what is this catalog's dark-fraction / show me the TE polarisation spectrum" is a natural-language question that RBS-LM should be able to take and dispatch onto ephemerides-spectral's attested surface — same pattern as it dispatches onto srmech.

**The aspirational shape: "a world problem solver."** Stated honestly and within the framework's own discipline:
- It is a **natural-language router to attested package operations** + the honesty-store truth-filter — NOT an oracle, NOT a cure-machine, NOT an answer-engine that invents.
- Per `[[user_stance_framework_hands_the_next_question_to_the_expert]]`: the deliverable is the next *question* handed to the expert, shaped so a domain specialist can ask it well — understanding-not-curing. "World problem solver" means *the universal front-end that lets a human pose a problem in plain language and have the right attested tools brought to bear*, with agreement-across-renders as the attestation (F334) — it does not mean a machine that claims to solve everything.
- Defensive / trauma-informed scope still bounds it: framework-reading + attested operations, never capability/offence.

## Vocabulary discipline — "world / word problem solver" is a LAYMAN-tier gloss (squashes too much; not-incorrect)

User refinement (2026-06-03): *"word problem solver squashes too much but it would be a laymen term that won't be incorrect."*

Held per F317 (the canonical identity stays the **operator-signature**; labels are cheap, additive synonyms — never a rename). So:
- **"world problem solver" / "word problem solver" is a layman-tier label only.** It is **not-incorrect** — fine to hand a non-expert — but it **squashes** the precise structure (the natural-language router + the *attested* package operations + the *truth-filter gate*) down to a slogan. A squash is acceptable for the layman tier and unacceptable as the working identity.
- **"word problem solver" is actually the apter layman reading:** a "word problem" is the school/layman term for a problem *posed in words* (natural language) → RBS-LM takes a problem in words and brings the right attested tools to bear. It under-states the machinery (says nothing about attestation or the truth-filter) but it is genuinely not-wrong. "world problem solver" over-states *scope* (sounds like an oracle); "word problem solver" under-states *machinery*. Both are fine layman glosses; neither is the precise identity.
- **Precise identity (the working one):** *RBS-LM = the natural-language interface that routes a plain-language problem onto the right tool-schema package's attested operations, gated by the honesty-store truth-filter.* The layman gloss rides on top of that, additive, like the F317 EngLM/FreLM render-labels — cheap synonyms, no global rename.

## Why this is the same shape as UPSTREAM §17, one level up

§17 asks srmech to **unify two op registries** (DSL cascade-ops + AMSC catalog-chains) into one discovery surface so any catalog's kernel shows up as a DSL entry. F340 is the same unification at the **portfolio** level: unify *every package's* tool-schema into one natural-language surface (RBS-LM) so any package's operations are reachable in plain language.

- The mechanism is already partly in place: each package ships `tool_schema`; srmech ships `srmech-mcp` / `srmech-agent` adapters + `register_attested_root` for downstream packages.
- The missing piece is the same as §17's spirit: a **unified, discoverable, natural-language dispatch surface** across packages, with provenance tags (`package:<name>`) and the truth-filter gate on the way out.

This is the **cap on the Rosetta-stone-of-srmech** (the DSL = the channel) extended to a Rosetta-stone-of-the-whole-portfolio.

## HOLD

srmech dev is **in progress** (the §17 U1–U4 catalog→kernel→DSL changes + the open §15.1/§16.1/§13-D4 items). Per user direction: **do not start new build/research on this until the user comes back with the srmech-dev result.** This finding records the direction so it is not lost; the next move waits on the user.
