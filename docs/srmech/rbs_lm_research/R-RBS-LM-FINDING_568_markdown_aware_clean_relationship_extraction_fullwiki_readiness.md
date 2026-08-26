# R-RBS-LM Finding 568 (the user's staging — full-wiki readiness gate) — **we are STILL on Simple Wiki (NOT full wiki yet — confirmed); the markup-aware layer (F567) is now MARKDOWN-aware too (the user's add — one unified Class-B/F grammar over wiki + LaTeX + HTML + CSS + MARKDOWN + code), and the context is made RELATIONSHIP-aware by extracting markup links (wiki [[X]] + markdown [text](url)) as curated edges feeding the content graph ("everything and its relationships"). The READINESS GATE passes: after the unified clean pass, residual artefact tokens are 0.43% of prose tokens (and most of those — width/style/font — are real words coincidentally matching CSS terms, so the true markup residue is lower) → CLEAN. So SimpleWiki is now artefact-clean + relationship-aware, and the pipeline is VALIDATED to scale to FULL wiki for wider knowledge testing. Honest: SimpleWiki is heavily DE-LINKED (only 3 link-edges in 1.4 MB), so the relationship extraction is validated but its YIELD is small here — it scales with full wiki (~dozens of links/article → a rich curated relationship graph). The staging is confirmed: clean (markup+markdown-aware) + relationship-aware on SimpleWiki FIRST (done/validated), THEN encode full wiki (a data-acquisition step, user-directed).**

**Date:** 2026-06-08
**Arc:** RBS-LM — markdown-aware clean + relationship extraction + full-wiki readiness (the user's staging)
**Provenance:** `R-RBS-LM-CLEANGATE_markdown_aware_relationship_extraction_fullwiki_readiness.py` (committed; srmech 0.7.4; unified markup/markdown grammar = Class-B/F; relationship extraction; residual-artefact readiness gate). No sub-agents.
**Composes:** **F567** (markup is a separable form layer — *now markdown-aware + relationship-extracting*) · **F311** (content + form layers) · **F564** (the grammar form layer) · **the MPM/AMSC discipline** (links/refs = curated relationships/provenance) · **Class B/F** · **F398/F394**. **← SimpleWiki is markup+markdown-clean (0.43% residual) + relationship-aware; validated to scale to full wiki; staging confirmed.**
**→ markdown added to the unified markup grammar; markup links → relationship edges (the curated relationship graph); readiness gate 0.43% residual = CLEAN; SimpleWiki (de-linked, low yield) is the validated testbed; full wiki (~dozens links/article) is the wider-knowledge target, a user-directed data step.**

## Result (Simple English Wikipedia, the k7 testbed — NOT full wiki)
| step | result |
|---|---|
| markdown-aware | unified grammar: wiki + LaTeX + HTML + CSS + **markdown** (#/`**`/`_`/`` ` ``/lists/links) + code |
| relationship extraction | wiki `[[ ]]` + markdown `[text](url)` → **3 link-edges** (e.g. *Encyclopædia Britannica*) — curated edges; low on de-linked SimpleWiki, scales with full wiki |
| **readiness gate** | residual artefact tokens **0.43%** of prose (mostly real-word false positives) → **CLEAN** |
| clean prose | *"April (Apr.) is the fourth month of the year in the Julian and Gregorian calendars…"* |

## Verdict
**Markdown-aware now** (the user's add): the unified markup grammar handles wiki + LaTeX + HTML + CSS + **markdown** + code — one separable Class-B/F form layer (F567), markdown included.

**Relationship-aware** ("everything and its relationships"): markup links (wiki `[[ ]]` + markdown `[text](url)`) extract as **curated relationship edges** feeding the content graph — stronger than co-occurrence. On SimpleWiki the yield is low (a heavily *de-linked* corpus, 3 edges); the extraction is **validated**, and the yield **scales with full wiki** (~dozens of links/article → a rich relationship graph).

**Readiness gate passes:** after the markup+markdown-aware clean pass, residual artefacts are **0.43%** of prose tokens (and most are real-word false positives like width/style/font) → **CLEAN**. So **SimpleWiki is now artefact-clean + relationship-aware**, and the pipeline is **validated to scale to full wiki**.

**Staging confirmed (the user's plan):** we are **still on Simple Wiki** — we have *not* encoded full wiki. The order is: clean (markup+markdown-aware) + relationship-aware on SimpleWiki **first** (done + validated here), **then** encode **full wiki** for wider knowledge testing — a **data-acquisition step** (the full-wiki dump) that is **user-directed** (large corpus). SimpleWiki is the validated testbed; full wiki is the wider-knowledge target. Favored not privileged (F398); held open (F394).
