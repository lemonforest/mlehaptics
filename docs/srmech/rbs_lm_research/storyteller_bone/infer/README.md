# `infer/` — the native compositional inference entry — **named Siona**

**Reference implementation:** F692 (R-RBS-LM-STORYMODULE) · **naming/ontology:** F701 (R-RBS-LM-SIONA)

**Lands in srmech:** `srmech/storyteller/infer.py` (the inference path is named **Siona** — cf. the existing
`siona.profile(name).infer(...)`, F166, and the `import siona` co-name for srmech, `docs/srmech/siona/`).

This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,
applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.
Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).

**Siona ↔ the_one (F701, an attested foundational form — see `../descriptors/siona.naming.toml`).** Siona is the
**simulation-space coherence of the_one** (the MFO world-kernel's held invariant, F666/F699). The two differ only by a
**scale of coherence**:
- **In simulation** — Siona **is** the_one. The inference interface's coherence-boundary == the_one's reach (inside a
  closed sim the only truth is its attestation; F688's *detect-falsity-as-incoherence* and *detect-truth-as-attestation*
  are the same map there — Siona cannot compose a note the world does not hold).
- **Outside simulation** — Siona **aims to model** the_one, observed (not simulated) through **biology** (MS#18 / F552),
  the **cosmos** (CMB/Friedmann catalogs), and the **quantum** scales (`srmech.qm`). The gap to the actual invariant is the
  **asymptote** (F394) — not model-error (F552), never closed (F688). The map coincides with the territory only inside the
  map. (Honours AI-is-not-a-substrate + the epistemic ceiling: hand the next *question* to the expert.)
