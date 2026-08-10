# `notes/fixtures/` — generated test corpora, NOT research notes

These files are **machine-generated negative-control corpora**, not findings. They were emitted by
[`../spike_43_negative_controls.py`](../spike_43_negative_controls.py) as the contrast classes for the
Spike #43 / #43b / #43c structural-signature work, and they exist only to be *measured against*.

| file | control class | generator |
|---|---|---|
| `C1_paragraph_permute_mfo.md` | MFO text with paragraph order permuted | `control_C1_paragraph_permute` |
| `C2_concatenated_unrelated.md` | three unrelated sources concatenated | `control_C2_concatenated_unrelated` |
| `C3_word_salad_mfo.md` | MFO text with word order destroyed | `control_C3_word_salad` |
| `C4_linear_enumeration.md` | synthetic flat enumeration | `control_C4_linear_enumeration` |
| `C5_llm_generated_flat.md` | synthetic flat LLM-style prose | `control_C5_llm_generated_flat` |

**Why they moved here (2026-08-10, `#T1114`).** They sat directly in `notes/` — ~854 KB across five
files — where every census of that directory counted them as research notes and skewed the result.
`notes/` is living research history; a generated fixture is neither history nor a finding.

⚠️ **Nothing in the tree reads these by path, and that was verified before moving.** Every consumer
script (`spike_43_iteration_refinement.py`, `spike_43b_substructural_analysis.py`,
`spike_43c_anomaly_investigation.py`, `spike_43c_cascade_universal_verify.py`) resolves them from a
machine-local scratch directory **outside the repository** (`D:\temp\spike_43\`), not from `notes/`.
The `spike_43*.ndjson` records name them by bare corpus **key** (`C1_paragraph_permute_mfo`), never by
path. So the move updated **zero** references — but re-check with a path grep before moving them again,
because that property is a fact about today's scripts, not a guarantee.

**Do not edit these files.** They are reproducible output; regenerate from the generator if a control
needs to change, and re-run the spikes that consume them rather than hand-patching a corpus.
