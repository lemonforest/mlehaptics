# Finding 709 — the etak Story Teller, re-evaluated with the magic cap removed: the cap had quantized away its whole world

**Script:** `R-RBS-LM-ETAKPROSE_storyteller_paragraph_chapter_capped_vs_uncapped.py`
**Status:** VERIFIED — capped-vs-uncapped on the same corpus slice (srmech 0.7.5rc28)
**User direction:** *"should re-evaluate our etak story teller paragraph and chapter prose and compare what we get with
removed magic cap."*

## The before/after (same 20k-article simplewiki slice; one uncapped build, capped = the induced top-256 subgraph)

| | CAPPED (top-256, the old "magic cap") | UNCAPPED (F708) |
|---|---|---|
| vocabulary | 256 generic words | **157,444 words** |
| graph density | avg degree 240/255 — **~94% of word-pairs co-occur directly** → the etak walk is trivially 1-hop | avg degree 80/157,443 — **~0.05%** → the etak walk is **real multi-hop navigation** |
| `planet`/`ocean`/`science`/`disease` | **ASKING-STATE** (not in the 256) — the Story Teller is **mute** on them | present, grounded |
| paragraph for `planet` | *mute* (the cap made it impossible) | *"the planet is seen with the earth, the solar, the system"* |
| chapter from `planet` | *"[asking-state: I have no tome for 'planet']"* — it can't even begin | planet → earth → sun → … a grounded astronomy chapter |

The uncapped etak-walked chapter:
> the planet is seen with the earth, the solar, the system
> the earth is seen with the sun, the water, the moon
> the sun is seen with the earth, the around, the moon
> the around is seen with the world, the people, the city

Every hop is a **real attested edge** (the chord, F658; the etak walk, F704); on the capped kernel the same chapter is a
single line: *"I have no tome for 'planet'."*

## What this shows

The magic cap was **not a performance detail — it quantized away the Story Teller's entire world** (F49/F50: pre-encode
quantization is the anti-thesis). Two compounding harms:
1. **Vocabulary** — the Story Teller could narrate only the 256 most-frequent (generic) words; almost every real subject
   (planet, ocean, science, disease, …) fell to the asking-state. It was mute on the world.
2. **Navigation** — a ~94%-complete graph makes the etak walk trivially 1-hop; there is no journey. Uncapped, the 0.05%-
   dense graph makes the etak walk a **real grounded path** (planet → earth → sun → …), which is the whole point of
   "thinking is a walk" (F704).

The chord (F658) was always the same engine; with the cap removed it finally **has notes to strike**.

## Honest artifact (F573)

The uncapped chapter's 4th hop drifted to *"the around is seen with the world, the people, the city"* — **`around` is a
near-stopword** that leaked in as a walkable hop. The navigation is real and attested, but the stoplist needs tightening
(`around`/`world`/`people`/`city` are low-information hubs) so the etak walk doesn't wander into generic words mid-chapter.
A fuller stoplist (or an inverse-frequency hop weighting that down-ranks hub words) is the fix — noted, not hidden.

**Composes:** F708 (the cap removed — the enabling fix) · F697 (prose-from-kernel) · F704 (the etak walk) · F658/F661
(the chord / asking-state) · F640/F49/F50 (no-magic / no-quantization). srmech 0.7.5rc28. A slice (not full enwiki) — the
*comparison* is the point. Held open (F394).
