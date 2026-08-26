# F819 — NO manual-removal edits in the encoder: a strip HIDES a missing sublanguage kernel. The encoder now SURFACES a missing-kernel MAP (construct-family → count) instead of silently stripping, and the #1 gap (templates: 11.4/page, 98% of pages) gets a real kernel — a discrete `{{name|args}}` grammar that RENDERS content-templates ({{convert|5|km}}→"5 km", {{lang|fr|bonjour}}→"bonjour") and reports every unkerneled family. Re-encoded all 271,174 simplewiki bodies: the gap map (8,385 families) IS the empirical kernel-build queue.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc169 (encode) / rc166 (live) · **Provenance:** `R-RBS-LM-MARKUPGRAMMAR` (the template kernel + `gaps=` surfacing) + `R-RBS-LM-RAWENCODE` (gap aggregation → `simplewiki_rawbody_gapmap.json`) · **Composes:** F817 (the no-doctoring raw re-encode), F764 (understand_markup), the §2 reflex-override (a strip is the data-cleaning analogue of `Counter()`), #225 (the sub-language ROUTER tier — this is its foundation), #226 (the remaining specialized kernels — now quantified) · **User direction (2026-06-17):** "do not do manually removing edits on encoding source. it shows us where we are missing sublanguage kernels. these are always discrete math and not hard to solve."

## The principle
A manual `re.sub` that removes a construct (template / ref / table / latex / code) is the same failure as a blanket markup strip — it discards content AND erases the *signal* of which sublanguage kernel is missing. Wiki constructs are discrete (context-free-ish) grammars — tractable. So the encoder must SURFACE each construct it can't yet route to a content kernel (detect + count + report), and we drive that gap toward zero by BUILDING kernels, never by silently stripping.

## What was built
1. **`understand_markup(text, *, gaps=None)`** — back-compatible (still returns `(clean, edges)`); when a `gaps` dict is passed it is populated with `construct-family → count` for everything dropped without a content kernel. CONTENT kernels (kept): links (unwrap + edges), emphasis/heading (unwrap), CONTENT templates (rendered). Surfaced-as-gap: unknown template families, `<ref>`, tables, `<math>`/`$LaTeX$`, `<code>`, and the `<score>/<chem>/<gallery>/<timeline>` block tags. (html-tag/css/list markers wrap content we KEEP → form-not-gap.)
2. **The template sub-language kernel** (`_resolve_template`) — parses the discrete `{{name|pos|k=v}}` grammar (innermost-first in the fixpoint, so nesting resolves inside-out). A curated render registry handles content-bearing families (convert/cvt/lang/lang-xx/nowrap/nobr/frac/sfrac/val/formatnum/as-of/nihongo); every other family is recorded in `gaps` (the missing-kernel signal) and dropped from the prose walk. Verified: `{{convert|5|km}}`→"5 km", `{{lang|fr|bonjour}}`→"bonjour", `{{nowrap|very tasty}}`→"very tasty", `{{Infobox food|…}}`→surfaced as gap `infobox`.
3. **`R-RBS-LM-RAWENCODE`** aggregates the per-page gaps corpus-wide → `simplewiki_rawbody_gapmap.json` (8,385 construct families). Re-encoded all bodies (NO regression: 271,174 pages, uniq-walk 99.1%, mean k* 5.3, 5.78M curated edges). Live recall verified (tomato full body, honest "de Bruijn shape-graph (the fiber)" label).

## The missing-kernel map (the empirical kernel-build queue — top families by occurrence over the full corpus)
| family | occ | the kernel to build |
|---|---|---|
| `<ref>` | 1,056,916 | **citation kernel** — parses the citation; FEEDS the MPM/attestation layer (the highest-value kernel) |
| `reflist` / `webarchive` / `cite` | 177k / 41k / … | same citation family |
| `infobox` | 136,059 | **structured-FACTS kernel** — key=value facts as edges/relations |
| `coord` | 88,965 | **geo-coordinate facts** |
| `birth` / `start` / `dts` | 47k / 33k / 24k | **date kernel** (content) |
| `efn` | 25,563 | explanatory-footnote **content** |
| `<math>` (block) + `$latex$` | (sep.) | route to the existing **F452/F454 LaTeX tree-signature kernel** |
| `table {\|` | 54,860 | **table kernel** (tabular data) |
| `m+j` / `mp` / `goal` / `party` / `football` / `election` | 100k–186k | sport/measurement infobox helpers (mostly facts or decorative) |
| `defaultsort` / `sort` / `sortname` / `flagicon` / `flag` / `authority` | 96k / 49k / … | pure METADATA/decorative — now dropped **knowingly** (no content), not silently |

## Honest scope
- The template kernel renders the common content families + surfaces the rest; the long tail (8,385 families) is dominated by the top ~30. Building the citation + infobox-facts + date + coord kernels (all discrete, tractable) is the queued next step (#225/#226) — each one shrinks the gap map measurably.
- `<math>`/`<code>` are surfaced but not yet ROUTED to the existing F452/F454/F456 kernels — that routing is the #225 ROUTER tier proper.
- Metadata/decorative families (defaultsort/flagicon/…) are correctly dropped, but now it is a RECORDED decision (visible in the gap map), not a hidden strip.

## Verdict
The encoder no longer hides where kernels are missing: it renders the content it can (the template kernel, #1 gap) and SURFACES the rest as a ranked, corpus-wide missing-kernel map. "Do not do manually removing edits" is now structural — every drop is counted and queued, and the map tells us exactly which discrete-grammar kernel to build next (citations first, feeding the MPM). Re-encoded clean (99.1% uniq, no regression); live-verified.
