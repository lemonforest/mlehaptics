# `engine/` — the seen-rule render engine + the chord + the asking-state

**Reference implementation:** F654/F658/F661 (in F692 STORYMODULE)

**Lands in srmech:** `srmech/storyteller/engine.py`

This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,
applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.
Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).
