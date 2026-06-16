# F799 — the running-context instrument was eating Siona's OWN rendering scaffolding (the parse-line words input/ride/topic/steer/definition leaked back in as "context"), because her prior answers are fed back verbatim. Fixed with a context-cleaning step (strip the [bracketed] parse-lines/tags + citation parentheticals before extracting content). Plus: a self-PROVENANCE route — "where is your source code?" now answers from what she holds (she IS the srmech package + version), not a random notebook etak-walk and not a fabricated URL.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** F759 (the running-context bundle — the instrument that had the gap), F798 (anaphora carry-forward — same conversation-state plumbing), F743 (self-knowledge is READ FROM STRUCTURE, no baked-in self-answers — the provenance answer obeys this), F751 (declared operators — Siona's framing words are her own reserved scaffold) · **User report (2026-06-16):** "maybe we are not using our context instrument correctly or have forgotten a step?" + a "curious, not wrong" source-code reply.

## Bug 1 — the context instrument ate its own scaffolding (the "forgotten step")
The reported context list for a turn was:
`context ['tomato', 'input', 'ride', 'definition', 'topic', 'steer', 'solanum', 'lycopersicum', 'vegetable', …]`

**`input`, `ride`, `definition`, `topic`, `steer` are not conversation content** — they are Siona's OWN parse-line scaffolding (`[input-ride: definition · topic ['tomato'] · steer ['what']]`). The server (F759) threads the prior turns as running context by joining ALL prior messages — including Siona's prior *answers*, brackets and all. So `_context_content` fed her own rendering meta back into the running-context bundle as if it were the conversation. The instrument was reading its own output.

**Fix:** a context-cleaning step (`_context_content()`), applied wherever context is consumed (the `ctx_terms` bundle, the F769 `ctx_words`, the F798 `_prev_topic` fallback):
- Strip every `[bracketed]` segment — the parse lines + tags (`[input-ride …]`, `[siona · …]`, `[etak: …]`, `[anaphora: …]`, notebook §-refs). **Nested brackets are collapsed innermost-first** (`['tomato']`/`['what']` removed, then the now-flat outer bracket) — a single pass stops at the first `]` and leaks the `· steer ·` connective, which was the residual bug caught on first test.
- Strip Siona's citation / honest-note **parentheticals** (`(source: …, CC-BY-SA)`, `(related: …)`, `(these are …)`) via `SCAFFOLD_PAREN_RE` — matched by a scaffold marker, so a *content* parenthetical like `(Solanum lycopersicum)` carries no marker and **survives**.

Verified — the context list is now pure conversation content:
`context ['tomato', 'solanum', 'lycopersicum', 'vegetable', 'botanical', 'fruit', 'specifically', 'berry']` — zero scaffold leaks (live, through the HTTP API).

## Bug 2 — "where does your source code exist?" misrouted (honest, but odd)
The reply etak-walked the srmech_notebook to a random session-spikes section (§3.15 precession) — *not wrong* (it IS srmech material) but odd; the user expected a source/repo pointer. Cause: "your source code" has a self-reference ("your") but the identity gate only fires on `siona`/`\byou\b…srmech`, and `\byou\b` doesn't match "your" — so the content tokens (source/code/exist) routed into the notebook walk.

**Fix:** a self-PROVENANCE route (`PROVENANCE_RE`, before the identity gate): a self-reference (`you/your/yourself`) + a source/repo cue (`source code`, `your code`, `repo/repository`, `github/gitlab`, `pypi`, `open source`, `where do you live`, `where can I find/download/install you`) → `_provenance_card()`. The card is **read from structure** (F743): she states she IS the srmech package (name + version + op/category counts from `describe()`), that she's an open research package locatable by its name — and **honestly that she does NOT hold a repository URL as an attested fact, so she won't fabricate one** (no-hallucination). She points at *what she is* (the package), not an invented github link. Live:
> *"My source IS the srmech package — srmech — Stored-Relationship Mechanism research package (srmech 0.7.5rc166). I'm an open research package, not a hidden model … I do NOT hold a specific repository URL as an attested fact, so I won't fabricate one; look up the "srmech" package to find the code."*

## Verified (live, rc166)
- multi-turn context list → content only, no scaffold (`['tomato','solanum','vegetable',…]`). ✓
- "where does your source code exist?" / "are you open source?" → `[siona · provenance]`. ✓
- Regression: "who are you?" → identity card; "what is a galaxy?" → definition (no provenance/identity misfire); F798 anaphora "what can it be used for" → uses (unaffected). ✓

## Honest scope
- The cleaning is a heuristic on Siona's *known* scaffold shapes (`[…]` segments + marker-bearing parentheticals). A future answer format with a new wrapper would need its marker added — but `[…]`-stripping is general and covers all current tags.
- The provenance card deliberately holds NO URL (F743 + no-magic): if a repository pointer is ever wanted as an attested fact, it should enter the genome as an attested provenance gene, not be hard-coded — surfaced as a follow-on, not done here.
- A content word that only ever appeared inside a parse-line bracket (never in prose) is dropped from context — acceptable; the topic almost always appears in the answer prose too.

## Verdict
The running-context instrument had a **forgotten step**: it consumed Siona's prior answers verbatim, so her own rendering scaffolding (input/ride/topic/steer/definition) re-entered as "context." Fixed by cleaning the context (strip `[bracketed]` scaffold + citation parentheticals, nested-bracket-safe) before it feeds the bundle — context is now the conversation's content, as F759 intended. Separately, a self-provenance route answers "where is your source code" from what she holds (the srmech package identity), honestly declining to invent a URL (F743). Both deployed to the live rc166 server.
