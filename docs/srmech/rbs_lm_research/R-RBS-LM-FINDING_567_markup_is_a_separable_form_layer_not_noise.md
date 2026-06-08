# R-RBS-LM Finding 567 (the user's correction — corrects F566's blocklist) — **wiki markup leaking into the content is NOT noise to blocklist (F566's mistake) — it is ANOTHER separable FORM layer (Class-B TLV framing / Class-F render), recognised + stripped at the SOURCE and its structure USED, exactly as we did with LaTeX; and it is UNIVERSAL, not a wiki thing — the same markup grammar handles LaTeX \cmd{}, HTML <tag>, wiki [[ ]]/{{ }}, and code. A markup-aware pass over the raw text detects + classifies the spans (3 links, 1 template, 2 refs, 2 html, 319 CSS attribute spans, 12 table spans), strips the presentation markup at the source (the F566 "px/align/style leak" was `style="text-align:left"` → tokenized fragments — removed properly, not word-by-word), AND uses what the STRUCTURE markup encodes: [[links]] = RELATIONSHIPS (the linked entity is related → feed the content graph), <ref> = ATTESTATION (the MPM provenance discipline — citations first-class), {| tables |} = DATA. So markup-awareness gives BOTH clean prose AND extra structure — the opposite of throwing it away. This GENERALISES F311: content + MANY form layers (GRAMMAR F564–F566 and MARKUP here), each separable, one separation principle.**

**Date:** 2026-06-08
**Arc:** RBS-LM — markup as a separable form layer (corrects the F566 content-cleanup)
**Provenance:** `R-RBS-LM-MARKUPAWARE_markup_is_a_separable_form_layer_not_noise.py` (committed; srmech 0.7.4; markup = Class-B/F framing; detect/classify/strip + use the structure). No sub-agents.
**Composes:** **F566** (*CORRECTS its markup blocklist — markup is a layer, not noise*) · **F311** (content/form separation — *generalised to N form layers*) · **F564** (the grammar form layer — *markup is a sibling form layer*) · **F50** (architectural inversion) · **Class B** (TLV framing) · **Class F** (render) · **the MPM/AMSC attestation discipline** (refs = provenance) · **F398/F394**. **← markup is a separable, universal form layer (Class-B/F); recognise + use it (relationships / attestation / data), don't blocklist it.**
**→ markup (wiki/LaTeX/HTML/code) is a separable Class-B/F form layer; a markup-aware pass strips presentation at the source AND extracts links→relationships, refs→attestation, tables→data; the F566 blocklist is replaced; content + grammar + markup are three separable form layers (F311 generalised).**

## Result (1.4 MB raw text)
| markup kind | spans | what it encodes |
|---|---:|---|
| STRUCTURE:link `[[ ]]` | 3 | **relationships** (e.g. *Encyclopædia Britannica*) → content graph |
| STRUCTURE:template `{{ }}` | 1 | structured data |
| ATTEST:ref `<ref>` | 2 | **provenance / attestation** (MPM) |
| PRESENT:html `<tag>` | 2 | html |
| PRESENT:css `attr="…"` / `Npx` | 319 | **the F566 "leak"** — presentation, stripped at source |
| PRESENT:table `{| |} \|\|` | 12 | data layout |

Clean prose (markup-aware, no leak): *"April (Apr.) is the fourth month of the year in the Julian and Gregorian calendars, and comes between March and May. It is one of four months to have 30 days."*

## Verdict
**Markup is a separable form layer, not noise — the user's correction, applied.** The F566 "px/align/style leak" was CSS/table **markup** (`style="text-align:left"` → tokenized fragments); the right move is **markup-awareness** — recognise + strip the markup *spans at the source*, not blocklist words. And the same markup grammar handles **LaTeX `\cmd{}`, HTML `<tag>`, wiki `[[ ]]/{{ }}`, code** — markup is **universal** (Class-B TLV framing / Class-F render), *not* a wiki thing.

**And it is useful — recognised, not discarded.** `[[links]]` are **relationships** (the linked entity is related → feeds the content graph); `<ref>` are **attestation** (the MPM provenance discipline — citations first-class); tables are **data**. So markup-awareness yields **both** clean prose **and** extra structure — the opposite of throwing it away.

**The architecture generalises (F311).** Content + **many** form layers — **grammar** (F564–F566) and **markup** (here), each separable. The Story Teller reads **content**; grammar renders sentence **form**; markup-awareness peels the presentation/structure **form** and feeds its relationships/attestation back to content. Three layers, one separation principle. **This corrects F566's content-cleanup** (the SS-4 content source should be markup-aware). Favored not privileged (F398); held open (F394).
