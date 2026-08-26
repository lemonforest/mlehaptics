# R-RBS-LM Finding 565 (sentence-structure step 2) — **the renderer puts sentence STRUCTURE on top of the story — the form-weaving WORKS (it hits the corpus's grammatical statistics) even though grammaticality is still coarse: the story's CONTENT trajectory (27 content words from the manifold) is rendered into 4 bounded SENTENCES by weaving a function-word scaffold between content words (content→F→content bridges) + sentence-enders at the length law, and it MATCHES the corpus form — function-word ratio 36% (corpus law 35%), sentence lengths [11,11,11,9] (law median 10). Content × form are ORTHOGONAL (F311): the content words ARE the story (unchanged); only the FORM (the scaffold + boundaries) was added on top — swap content → a different story same form, swap scaffold → same story different register. HONEST limits: a coarse v0 — greedy bridges (no agreement/clauses), AND the content carries markup noise ("px/align/style" leaked from the wiki) so the sentences don't fully parse ("history people thumb px a right the style text align left."). So the form LAYER is correctly imposed (the statistics prove it); the GRAMMATICALITY and the CONTENT cleanliness are the next rungs.**

**Date:** 2026-06-08
**Arc:** RBS-LM — the grammar renderer (sentence structure on the story, step 2)
**Provenance:** `R-RBS-LM-GRAMRENDER_weave_scaffold_into_story_content_grammatical_sentences.py` (committed; srmech 0.7.4; Class-L manifold content trajectory + grammar maps content→func / func→content + length law). No sub-agents.
**Composes:** **F564** (the grammar kernel — *the form maps used here*) · **F311** (content/form separation) · **F538–F562** (the story = content) · **F157** (the sentence substrate) · **F398/F394**. **← the renderer weaves the scaffold into the story content + boundaries; the form statistics match the corpus; grammaticality is coarse (v0).**
**→ the story content is rendered into bounded sentences matching the corpus form (function ratio 36% vs 35%, lengths vs median 10); content × form orthogonal; v0 grammaticality is coarse + content has markup noise; next = POS bridges + clause structure + cleaned content + the Story Teller driver.**

## Result
**RENDERED (story content woven with the grammar scaffold into sentences):**
> history people thumb px a right the style text align left. if they you cannot pay to their own the language and. april the world that war ii the chloride is ions in. when the two or main types of arable farming.

| measure | rendered | corpus law |
|---|---:|---:|
| function-word ratio | **36%** | 35% |
| sentences / lengths | 4 / [11,11,11,9] | median 10 |
| content = the story? | yes (unchanged) | — |

## Verdict
**Sentence structure goes on top of the story — and the form-weaving works.** The story's content trajectory is rendered into **4 bounded sentences** by weaving a grammatically-attested function-word scaffold between content words (content→F→content bridges) + sentence-enders at the length law — and it **matches the corpus form**: function-word ratio **36%** (law 35%), sentence lengths around the **median 10**. The form layer is correctly imposed (the statistics prove it).

**Content × form are orthogonal (F311).** The content words *are* the story (unchanged); only the FORM (the scaffold + boundaries) was added on top — swap the content → a different story in the same form; swap the scaffold → the same story in a different register. The layers compose — exactly the RBS-LM separation (vs an LLM's entangled next-token, F564).

**Honest limits (the next rungs).** A coarse **v0**: greedy bridges with **no agreement or clause structure**, and the content carries **markup noise** ("px/align/style" leaked from the wiki) so the sentences don't fully parse. So *form* is right; *grammaticality* and *content cleanliness* are next: POS-aware bridges + clause structure + cleaned content + the Story Teller driver feeding the content (step 3). Favored not privileged (F398); held open (F394).
