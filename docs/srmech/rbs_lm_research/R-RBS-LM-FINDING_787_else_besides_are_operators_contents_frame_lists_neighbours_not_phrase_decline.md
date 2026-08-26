# F787 — "what else is in ketchup besides tomatoes" was odd for TWO compounding reasons (function-words counted as topics + the question-frame missed); fixed: `else`/`besides` are OPERATORS (stoplisted), and a CONTENTS frame lists the subject's held neighbours minus the exclusion (vinegar/salt surface — a grounded multi-item answer, not the phrase-decline)

**Date:** 2026-06-16 · **srmech:** 0.7.5rc165 · **Composes:** F776 (the ≥2-topic reasoner whose phrase-decline mis-fired), F770 (`[[feedback_operators_declared_operands_by_meaning]]` — function words are operators, declared not derived), F768/#221 (the aboutness-gate — `_recognized` over-counts in-corpus function words as topics), F760 (lead-sentence definition tier — the "single sentence" the user also flagged), F758 (the held neighbours are the assoc/relation stores) · **User report (2026-06-16):** flagged Siona's "what else is in ketchup besides tomatoes?" → *"That reads as several things (else, ketchup, besides, tomatoes) with no question — which one do you mean?"* as "very odd," and that answers are "all … a single sentence."

## Diagnosis (both confirmed against the stores)
The odd output had **two compounding bugs**:
1. **`else` and `besides` were counted as TOPICS.** They have co-occurrence entries (`else → something/someone…`, `besides → people/things…`) because they appear in text, so `_recognized()` (presence-in-a-store) returned True → the topic channel held `['else', 'ketchup', 'besides', 'tomatoes']` → the F776 reasoner saw ≥2 "topics" with no relate/compare cue → the **phrase-decline** fired. But `else`/`besides` are **function-word OPERATORS** (F770), not content — they should be consumed, not routed. (This is the F768/#221 aboutness-gate failure mode: *in-corpus ≠ contentful*.)
2. **"what else is in …" misses the question-frame regex** (`what\s+(is|are)` requires `what` immediately followed by is/are) → intent fell to `phrase` → straight to the decline.

And the **answer was actually present**: ketchup's held neighbours are `[tomato, food, heinz, tomatoes, vinegar, sauce, packets, salt, …]` — **vinegar** and **salt** are real "what else." The bugs just blocked the path to them.

## Fix (three small edits, F770/F787)
1. **Stoplist the connectives** — `else besides beside except apart aside excluding versus others` (+ scaffolding adverbs `often sometimes usually always inside within`) → ROUTING_STOPLIST. They're operators; now consumed from the topic channel.
2. **A CONTENTS frame** (`CONTENTS_RE`): "what else / what other / what's in X / besides Y / ingredients / made of" → fires *before* the 2-topic reasoner; lists the **subject's** held neighbours (assoc co-occurrence + typed relations), **excluding** the named exclusion `Y` (`EXCLUDE_RE` captures the word after besides/except/other than/…) and any other named topic.
3. Honest framing: the list is **held neighbours (co-occurrence + relations), NOT a verified contents/ingredient list** (CC-BY-SA).

## Result (tested on a fresh instance)
- **"what else is in ketchup besides tomatoes?"** → *"Besides tomato, what I hold near ketchup: food, heinz, **vinegar**, united, states, sauce, packets, fast, drug, **salt**."* — grounded, multi-item, includes the real other ingredients; no confabulation, no decline.
- "what is in soup" → *"What I hold near soup: miso, ramen, japanese, food, noodle, rice, eat, chicken, pumpkin, pancakes."*
- Regressions clean: "what is ketchup" / "what is tomato" still return the lead-sentence **definition**; "what else can you do" (no content topic) correctly falls to the identity card (the CONTENTS branch is guarded on `recognized`).

## On the "single sentence" (the other half of the report)
Definitions are deliberately the **lead sentence** (F760: "what X IS" — crisp by design). This fix shows Siona **can** answer in a multi-item list when the question is a *contents/list* question — so the single-sentence shape is specific to *definition* questions, not a global limit. **Richer multi-sentence PROSE** about a topic (the 2nd/3rd article sentences — e.g. ketchup's full ingredient prose) is a separate **data-scope decision**: only lead-sentence glosses + short abstracts are stored, not article bodies. Surfacing more prose means storing more of each article (attested, CC-BY-SA) — flagged, not done here.

## Honest scope
- Co-occurrence neighbours include noise (`united, states, fast, drug`) — the caveat marks them as "appears with," not "is made of." The deeper fix is #221 (measured function-ness / aboutness centrality) which would clean *both* the operator-leakage and the neighbour noise from one spectral pass — this finding is the **hand-set immediate fix**, that the **principled one**.
- Tested on a fresh instance; the **running server (port 8000) still has the old code** — it needs a redeploy (by-port, on user direction) to serve the fix.
- srmech-native stores (assoc/relations, Class-L co-occurrence); no `abs`, no CAD; data outside the repo.

## Verdict
The "very odd" output was the F768/#221 aboutness-gate failing on **function-word operators** (`else`/`besides` have co-occurrence entries, so they were mis-counted as topics → the F776 phrase-decline), compounded by the "what else is in" frame missing the `what is` regex. Fixed per **F770 (operators declared, not derived)**: stoplist the connectives + a **CONTENTS frame** that lists the subject's held neighbours minus the exclusion. Siona now answers "what else is in ketchup besides tomatoes" with **vinegar, salt, sauce…** — grounded, multi-item, honestly framed — instead of declining. Also clarifies the "single sentence": that's the *definition* tier by design (F760); list questions now give lists; richer prose is a data-scope choice (store article bodies). The principled successor is #221 (measured function-ness).
