# F817 — NO DOCTORING the SSoT: the F814 encode ran on a wikiextractor PROJECTION (`articles.jsonl`), where the raw markup ([[links]], {{templates}}, ==headings==) had ALREADY been stripped to ~0.1% before we ever consumed it — the doctoring happened upstream, leaving pipe/`thumb`/`$latex$` residue polluting the walk and DISCARDING the curated relationship layer entirely. Corrected: re-encode the entire simplewiki FROM THE RAW DUMP through the F764 `understand_markup` sublanguage kernel (hardened for raw-wikitext nesting) — it COMPREHENDS the markup (unwraps link/emphasis/heading CONTENT, extracts the curated [[Target]] EDGES, removes only pure FORM), never strips. Sample (4000 raw pages): 98.5% unique-walk, 100% (400/400) exact walk-reconstruct, mean k*=6.9, **115.6 curated edges/page** (the relationship layer the projection threw away).

**Date:** 2026-06-17 · **srmech:** 0.7.5rc169 · **Provenance:** `R-RBS-LM-RAWENCODE_…py` (raw-dump streaming encoder) + the F764 kernel hardening (`R-RBS-LM-MARKUPGRAMMAR_…py`) · **Composes:** F814 (the instrument it corrects), F764 (the understand_markup kernel — now nesting-hardened), F805/F808/F813 (fiber / context-addressed walk / entire-article reconstruct), §52 (streaming), #225/#226 (the sub-language router + remaining kernels — the deeper path) · **User direction (2026-06-17):** "do not use stripping from SSoT. we MUST use sublanguage kernels to understand. no doctoring the data before consumption."

## The empirical correction (the user asked for data, not assumptions)
The F814 instrument was built from `simplewiki_extracted/articles.jsonl`. Surveyed, that file is **already a wikiextractor projection** of the wiki, NOT the raw SSoT:

| construct in `articles.jsonl` | presence |
|---|---|
| `[[wikilink]]` | 0.1% |
| `{{template}}` | 0.1% |
| `==heading==` | ~0.0% (rendered to a bare line) |
| `<ref>` | 0.1% |
| `\| pipe` (the "47%-with-markup") | **42.6%** — mostly residue: `thumb\|180px\|right\|caption` image-param lines wikiextractor left as plaintext |

So the markup was **stripped before we consumed it** (the doctoring is upstream), and what remained was *residue* (`thumb`, `180px`, `right` entered the token walk as if prose) — the opposite failure from "use a kernel": not over-stripping, but UNDER-understanding leftover junk. And the curated **relationship edges** (the [[Target]] outlinks) were gone entirely — `articles.jsonl` has 0 extractable edges.

The **true SSoT** is on disk: `simplewiki-latest-pages-articles.xml.bz2` (334 MB, full raw wikitext). On it, the kernel does real work — "April" raw = 22,079 c → 418 curated edges (month, year, julian calendar, gregorian calendar, …); "Art" = 86 edges.

## The fix (use the sublanguage kernel; no doctoring)
1. **Hardened the F764 `understand_markup` SSoT kernel for raw-wikitext NESTING** (the lead tier never exercised it): a BALANCED innermost-first fixpoint resolves `{{…}}` (pure form → removed) and `[[…]]` (media/`File:`/`Image:`/`Category:` → form; else KEEP the display text) so a `[[File:…|caption with [[nested]] link]]` or a template-in-template is comprehended, not left as residue. Verified: the lead self-test is byte-identical (shallow markup converges in one pass), and the raw "Art" body no longer leaks the `is a work of art.` File-caption residue; no `thumb`/`px`/`{{`/`[[`/`File` tokens leak.
2. **`R-RBS-LM-RAWENCODE`** streams the raw bz2 dump (ns=0, non-redirect, len>200), runs `understand_markup(raw) → (clean, edges)`, tokenises the clean prose, finds k*, and persists the walkable token SHAPE + k* + the curated EDGE list (NDJSON `simplewiki_rawbody_instrument.ndjson` + title→offset index). STREAMING (one page in RAM, §52) so RAM stays flat. The full run is in flight.

## Sample (4000 raw pages, validated before the full run)
- unique-walk **98.5%**; mean k* **6.9**; mean tokens/page **782** (raw bodies recover MORE content than the projection — headings + link text kept).
- **walk-reconstruct: 400/400 = 100% exact** on unique articles (the fiber, F813, holds on raw bodies).
- **mean 115.6 curated edges/page** (462,569 in 4000 pages) — the relationship layer that "everything AND its relationships survive the read" requires, which the projection had discarded.

## Honest scope (what is still a projection / a follow-on)
- understand_markup is the **markup** sub-language kernel; deeper sub-languages still route to FORM-removal, not their own kernels: `<math>`/`$…$` LaTeX (the F452/F454 tree-signature kernel), `<code>` (F456), and #226's `<score>` music / `<chem>`/`<ce>` chemistry / IPA / `{{lang|xx}}` embedded-NL. Those spans are notation, not prose-walk content; capturing their kernel-signatures (not just removing them) is the #225 ROUTER tier — the genuinely-deeper no-doctoring step.
- The recall walk regenerates the lowercased alphanumeric token sequence (the shape); casing/punctuation is a rendering layer (F814 scope, unchanged).
- The 1.5% long-range-ambiguous tail still needs explicit branch-choices for 100% exact (F813).
- The curated edge list is persisted per-page but not yet wired into recall (it is the §52 cross-article shared-graph seed, F809) — a follow-on.

## Verdict
The SSoT was being doctored upstream (wikiextractor) before consumption; the no-doctoring re-encode runs the F764 sublanguage kernel on the RAW dump — comprehending markup, keeping content + curated relationships, stripping nothing. Sample-validated (98.5% unique, 100% exact reconstruct, the relationship layer recovered). This corrects F814's instrument; the deeper sub-language kernels (LaTeX/code/music/chem/IPA, the #225 router) are the named next step.
