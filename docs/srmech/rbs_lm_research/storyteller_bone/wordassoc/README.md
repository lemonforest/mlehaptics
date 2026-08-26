# `wordassoc/` — the big-wiki Class-L word-association kernel (shelf enrichment)

**Reference implementation:** F690 (R-RBS-LM-WIKIKERNEL)

**Lands in srmech:** `srmech/storyteller/wordassoc.py`

This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,
applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.
Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).

**✅ CORPUS-CLEANING (F700 requirement → F702 satisfied) — load-bearing for grounding honesty.** F690's *demo*
`strip_wiki_markup` dropped `<tag>`s but KEPT their content — so `<math>` LaTeX (`\frac`/`\sqrt`/`displaystyle`), bare
`<ref>` citations, `{| tables |}`, and ext-links **leaked into the vocabulary as junk tokens** (F700), and the demo corpus
never exercised that path. A kernel built from un-cleaned text grounds beats in markup noise (spurious Class-L
associations). **The kernel is now RE-ENCODED (F702):** F690's build path (`stream_articles`) uses
`strip_wiki_markup_hardened` (removes the *content* of math/ref/code/score/chem/table/comment blocks + clears nested
templates to a fixpoint) + `content_words` (F698, Unicode-aware) — verified: the re-encoded vocab carries **0** markup junk
tokens (the old path carried 7). The real-dump re-encode is the dev session pointing `stream_articles` at the dump; the real
cleaner is the **F579/F607 wiki-formatting-language kernel**. See `R-RBS-LM-FINDING_700` (the audit) + `R-RBS-LM-FINDING_702`
(the re-encode).
