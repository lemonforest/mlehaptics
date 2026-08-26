# `kernel/` — the bit-exact comm kernel + the two-tier adaptive kernel

**Reference implementation:** F613 (bit_exact_comm_kernel.py) + F628 (adaptive_tier.py)

**Lands in srmech:** `srmech/storyteller/kernel.py`

This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,
applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.
Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).
