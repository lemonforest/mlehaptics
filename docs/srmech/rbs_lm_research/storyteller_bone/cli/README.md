# `cli/` — the self-describing + self-asking `srmech story` CLI

**Reference implementation:** F693 (R-RBS-LM-STORYCLI)

**Lands in srmech:** `srmech/__main__.py (the `story` subcommand)`

This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,
applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.
Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).
