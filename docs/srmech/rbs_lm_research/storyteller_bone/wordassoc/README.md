# `wordassoc/` — the big-wiki Class-L word-association kernel (shelf enrichment)

**Reference implementation:** F690 (R-RBS-LM-WIKIKERNEL)

**Lands in srmech:** `srmech/storyteller/wordassoc.py`

This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,
applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.
Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).

**⚠ CORPUS-CLEANING REQUIREMENT (F700) — load-bearing for grounding honesty.** F690's `strip_wiki_markup` is a *demo*
stripper that drops `<tag>`s but KEEPS their content — so `<math>` LaTeX (`\frac`/`\sqrt`/`displaystyle`), bare `<ref>`
citations, `{| tables |}`, and ext-links **leak into the vocabulary as junk tokens**, and the demo corpus never exercised
that path. A kernel built from un-cleaned text grounds beats in markup noise (spurious Class-L associations). **Before the
kernel's vocab is trusted, the corpus MUST be cleaned with a hardened stripper** that removes the *content* of
math/ref/code/score/chem/table/comment blocks + nested templates (F700 ships a reference; the real target is the F579/F607
wiki-formatting-language kernel). See `R-RBS-LM-FINDING_700`.
