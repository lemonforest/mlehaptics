# `adapters/` — the epub_book AMSC adapter (book-worlds -> the shelf)

**Reference implementation:** F691 (R-RBS-LM-EPUBADAPTER)

**Lands in srmech:** `srmech/amsc/adapters/epub_book.py`

This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,
applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.
Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).
