# `wordassoc/` — the big-wiki Class-L word-association kernel (shelf enrichment)

**Reference implementation:** F690 (R-RBS-LM-WIKIKERNEL)

**Lands in srmech:** `srmech/storyteller/wordassoc.py`

This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,
applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.
Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).
