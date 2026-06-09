# `api/` — the OpenAI-compatible endpoint (AG2 / CopilotKit)

**Reference implementation:** F694 (R-RBS-LM-STORYAPI)

**Lands in srmech:** `srmech/storyteller/serve.py (FastAPI/ASGI)`

This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,
applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.
Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).
