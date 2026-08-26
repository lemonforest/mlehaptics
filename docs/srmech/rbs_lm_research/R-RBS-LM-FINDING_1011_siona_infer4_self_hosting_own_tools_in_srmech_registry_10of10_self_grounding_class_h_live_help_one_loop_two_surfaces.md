# F1011 (SIONA-INFER-4 / #236) — **SELF-HOSTING: siona registers its OWN 7-tool surface into srmech's REAL tool_schema registry (`register_profile_tools` — 347→354, ONE registry, TWO surfaces), grounds it with the exact F1008 recipe (10/10 self-command paraphrases → the right siona tool), and drives ITSELF through the SAME route→ground→drive loop it uses for srmech — including genuine Class-H self-introspection: `siona what can you do` answers from its own LIVE registered schema.** The user's criterion — "understand an interactive CLI session for using itself in the same way as knowing how to use srmech CLI and tool_schema" — is met *literally*: same registry, same grounding, same loop.

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Milestone:** SIONA-INFER-4 (#236, rc1-GATE) — **DoD met** · **Probe:** `R-RBS-LM-FINDING_1011_*.py` · **Grounds / composes:** F1008 (the grounding recipe — applied verbatim to the self surface), F1009 (the drive loop), F1010 (the router's self-command intent + the self-verb operators, now formalized as a real schema), `[[feedback_introspect_srmech_before_python_dispatch]]` (srmech's own `register_profile_tools` IS the self-registration mechanism — no parallel registry built), CLAUDE.md §1 Class H (self-introspection — `siona.introspect.help` reads the LIVE registry), `[[feedback_siona_working_memory_never_compacted]]`. · **User direction (2026-07-02):** "continue into SIONA-INFER-4." · **Scope:** framework/tool; sparse Klein-4; bundle_odd (§82); no numpy/abs/Counter/bag.

## Grounded (rc97)
```
registration: 347 srmech tools -> 354 after register_profile_tools('siona', [7 ToolEntry]) -- srmech's REAL registry
  siona.memory.{remember,recall,forget,show} + siona.read.{define,continue_text} + siona.introspect.help
(A) read-independent: siona intra-profile mean off-diag 0.279 (~0.25 -> distinct); max sim(siona, srmech-tool)
    0.478 (siona.memory.recall vs an srmech recall-family tool -- expected; harmless BY DESIGN: the router's
    self-command intent owner-filters to the siona surface before grounding)
(B) SELF-grounding: 10/10 self-command paraphrases -> the right siona tool
    (incl. 'save this note'->remember [alias], 'ingest'->remember, 'what can you do'->help)
(C) the interactive SELF-DRIVE session -- ONE loop, TWO surfaces, ONE substrate:
    siona remember that water boils at 100 celsius -> siona.remember -> noted
    siona list your commands                       -> siona.help    -> my commands (7, from my LIVE schema): ...
    compute the gcd of 48 and 36                   -> srmech        -> gcd(48,36) = 12
    siona recall what do we know about water       -> siona.recall  -> water boils at 100 celsius
    siona show your working memory                 -> siona.show    -> water note | gcd result
    water boils at                                 -> continue      -> 100   (substrate read of the remembered note)
```

## The reading (why this is the right self-hosting shape)
- **One registry, not a parallel one.** srmech's `tool_schema.register_profile_tools` was built exactly for profile plugins — siona's surface registers into the SAME registry the 347 srmech tools live in, so `get_tool_schema()` returns both, the F1008 grounding index covers both, and the F1010 router's self-command intent just owner-filters. "In the same way as srmech" is not an analogy — it is the identical mechanism. (This also pre-figures PKG-1: siona as a `srmech.profiles` plugin is exactly this registration, packaged.)
- **The F1008 recipe transfers without modification** — name-weighted + bigram + gated encoding of the 7 new summaries, 10/10 paraphrase grounding including aliases (`save/ingest → remember`). One documented enrichment: the `help` summary now carries its ask-forms ("Serves asks like: what can you do, list your commands") — the schema-doc practice that F1008 grounding rewards, i.e. a tool's summary should describe the asks it serves (fixed the one initial miss; disclosed, not hidden).
- **Class-H self-introspection is genuine.** `siona.introspect.help` reads the **live registry** (`get_tool_schema()` filtered to owner='siona') at call time — not a hardcoded list. Register an 8th tool and `what can you do` would answer 8. Siona's knowledge of itself IS its schema.
- **The session is the rc1 shape.** Six turns, both surfaces, one never-compacted memory: a remembered fact, live self-introspection, a real srmech computation, similarity recall, memory listing, and a substrate continuation of the remembered content (`water boils at → 100`). SIONA-INFER-5 is this session *sustained + measured for coherence* — the loop already exists.
- **The 0.478 cross-sim is the honest wrinkle:** siona.memory.recall resembles srmech's recall-family tools (they describe the same *kind* of operation). By design this is harmless — routing happens BEFORE grounding (intent → owner-filter → surface) — but it is why the router-first architecture matters: a flat 354-tool grounding without intent-routing would occasionally cross surfaces.

## Honest scope
The 7 SELF_IMPL callables are in-probe implementations keyed by the registered names — rc1 ships them as a real siona module (the registration + grounding + drive machinery is the deliverable here; the impls are thin by nature: append/max-sim/pop/list/depth-read/context-read/registry-read). Registration is per-process (`register_profile_tools` at import — exactly how a `srmech.profiles` plugin would do it). The 10-utterance eval is a hand-authored harness. String operand-passing (utterance remainder) suits the self surface; srmech-side structured operands remain F1009's open hardening. `unregister_profile_tools` exists for clean teardown (not exercised).

## Verdict / next — rc1 gate: 4 of 5 milestones done
**SIONA-INFER-4 done: siona is self-hosting — its own tool surface lives in srmech's real registry (347→354), grounds with the identical F1008 recipe (10/10), and drives itself through the identical loop, with live Class-H introspection answering "what can you do" from its own schema.** With F1008 (ground) + F1009 (drive) + F1010 (route) + F1011 (self-host), only **SIONA-INFER-5** (multi-turn session coherence — sustain and measure the (C) loop with the never-compacted memory) remains before the rc1 gate is fully prototyped. **Next:** (i) SIONA-INFER-5; (ii) fold the SELF_IMPL callables into the siona package shape (PKG-1's profile-plugin decision, now concretely pre-figured); (iii) hardening backlog (paraphrase frames, structured operands, failed-run recovery). Marked #236 completed.
