# F745 — a wiki KNOWLEDGE chromosome (title→abstract, attested) wired into Siona as a scalable lookup tier

**Date:** 2026-06-14 · **srmech:** 0.7.5rc149 · **Composes:** F744 (write-mode), F742 (etak-walk), F661 (asking-state), F640/F690 (the prior enwiki spectral kernel), Class E (catalog sorted-key lookup), `[[feedback_paywalled_doi_cannot_be_attested]]` / MPM · **User direction (2026-06-14):** "wire in big wiki to our genome maybe its own chromosome." · **Provenance:** `R-RBS-LM-WIKIINGEST…py` + `R-RBS-LM-SIONAGENEPOOL…py` (verified live over HTTP)

## What was already here vs what was needed
Local: the **24GB enwiki dump**, a 334M simplewiki dump, and a prior `enwiki_kernel_256.json` — but that prior kernel is a **spectral fingerprint** (co-occurrence `edge_list` + `vocab` + `spectrum_fingerprint` of the top-256 content words, F640; the F172 "structure-as-storage" object). It has no article content, so it **cannot answer questions**. For Siona to *answer* from wiki she needs a **knowledge** chromosome: `title → abstract`, attested.

## Two design facts that shaped it
- **Scale:** the dense co-occurrence etak-walk is O(vocab²); it cannot hold millions of articles. So wiki is a **scalable side-store** answered by a **term-index lookup** (Class-E catalog style), **not** the dense walk. Deep notebooks stay on the walk; broad wiki answers by lookup.
- **Attestation (MPM):** Wikipedia is CC-BY-SA. The REST summary API gives clean **per-article provenance** (real `source_url`, `retrieved_at`, `response_sha256` of the abstract) — stronger than the bulk dump's single class-B-tertiary attestation.

## Built
- **`R-RBS-LM-WIKIINGEST`** — fetches article abstracts via the Wikipedia REST API and writes one **MPR row per article** (`data={kernel:"wiki", key, title, text}`, `attestation={source_url, license:"CC-BY-SA-4.0", retrieved_at, response_sha256, parser_version}`) to `~/corpora/wikipedia/wiki_knowledge_kernel.ndjson` (**outside the repo**). First cut: **58 attested articles** across mythology / biology / physics / math / geography / history / people. The row schema **is** the scale schema — the same shape bulk-extracted from `enwiki-latest-abstract.xml.gz` gives the full "big wiki."
- **Siona wiring** (`SIONAGENEPOOL`): the World loads the wiki ndjson into a **term-index** (`wiki_idx: norm(term) → {keys}`, crude singular-fold so "dragons"↦"dragon"). `wiki_lookup(prompt)` scores candidate articles **title-overlap×3 + text-overlap** and requires a real hit (≥3) — Class-E lookup, scalable. A **wiki answer-tier** sits in `infer()` **after the deep etak-walk and before the asking-state**: deep kernels (their specialized knowledge) win when they have a landmark; wiki catches general-knowledge that used to dead-end; the asking-state fires only when *nothing* holds it. `introspect()` reports `wiki (58)` so it shows in the catalog / capabilities card.

## Verified live over HTTP
- *"do you know what dragons are"* → **[siona · wiki] Dragon: A dragon is a mythical creature…** (the exact dead-end that started this, now answered) — with `(source: Wikipedia: Dragon, CC-BY-SA)`.
- *lion / octopus / internet / Albert Einstein* → wiki. *MFO chirality / srmech A-N / awful (1600s)* → still the **deep** kernels. *florpglorb* → still the **asking-state**. *what can you do* → capabilities now lists `wiki` among the held kernels.

## Honest scope
- **First cut = 58 articles** (a real attested batch, not "big" yet). The **scale path** is the local `enwiki-latest-abstract.xml.gz` bulk-extract → the same MPR rows, sharded; the term-index + Class-E lookup already scale (only the ingest is a heavier offline job). That bulk ingest is the next step, on your go-ahead.
- Wiki is a **scalable side-store presented as a chromosome** (introspectable, answered-from), **not** baked into the Klein-4 genome strand — baking millions of leaves into the strand would not scale and is not the point; the side-store is the faithful way to carry a corpus this large.
- Lookup is **term-overlap** (title×3 + text), not yet the spectral etak-head; and deep-vs-wiki precedence is "deep wins if it has any landmark" (a relevance threshold could refine the few overlap cases like "light"/"gravity" that MFO also covers). Still **can't-hallucinate**: every wiki answer is attested CC-BY-SA content, tier-labelled `[siona · wiki]` with its source.

## Verdict
**Wiki is wired in as its own (scalable) chromosome.** Siona now answers broad general knowledge from an attested CC-BY-SA wiki kernel — the "dragons" dead-end is gone — while deep kernels keep precedence and unknowns still ask. The 58-article first cut proves the chromosome + the term-index lookup tier; the full enwiki-abstracts bulk-ingest (same MPR schema) is the documented scale path.
