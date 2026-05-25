# RBS-NN — Resonant Bit-Serialized Neural Net (research arc)

**Status:** opened 2026-05-25 · rolling draft · temp subtree (SSoT will be `docs/srmech/srmech_research_notebook.md` at R-RBS-NN-9 close)

**What it reads:** what an artificial neural network IS when decomposed across the srmech 14-class A-N cascade vocabulary and placed against the MFO two-level ontology (substrate / excitation). The framework reads NN architecture as substrate-self-recognition per `mfo_spectral_research_notebook.md` line 2812 ("when humans first built artificial neural networks, that was the substrate-self-recognition sign-flip at AI-substrate scale"); RBS-NN is the framework reading of that sign-flip event.

**What it is NOT:** a new NN architecture invented inside the framework. The arc reads what is already structurally present. No lineage claims per `[[feedback_no_lineage_claims_in_notebook]]`.

---

## §0 End-user goal

A foundational srmech feature that gives end users an entry point to a neural-net architecture that **learns and preserves a user lexicon in native format**. A neural net at the substrate level is incredibly efficient knowledge storage; RBS-NN names that efficiency explicitly via bit-exact HDC binding rather than learned-then-quantized weights. The user's vocabulary becomes the binding alphabet directly — no learned-embedding bottleneck quantizing the user.

---

## §1 The MFO reshape (foundation — load-bearing)

Per `docs/antikythera-maths/mfo_spectral_research_notebook.md` §VII.1.1 (lines 668–743), the substrate / excitation distinction maps directly onto compute primitives:

| MFO Level | Domain | Operations | Compute home |
|---|---|---|---|
| **Level 1 — substrate** | Hopf-compressed metric field at every instantiation depth | Class A content-mint (SHA-256), Class I cyclic shift, Class M XOR-bind, Class J prime, Class L Laplacian | **ALU, bit-exact** |
| **Level 2 — excitation** | Localized + delocalized excitations within the substrate | Class K rotate-overlay `max(v, rotate(v))`, Class M bundle-of-rotations averaging, derivative-sign-flip at extrema | **FPU, intentional lift** |

A conventional NN appears to lose bit-exactness because it performs **lossy averaging projections** (bundle, max-pool) that collapse Level 1 → Level 2 implicitly. RBS-NN names that collapse explicitly: Level-1 substrate ops on the ALU side stay bit-exact; rotate-overlay-class ops are routed through Class K on the FPU side **by ontological assignment** — not as a precision workaround. Per `[[user_stance_rotation_is_class_k_pin_slot]]`: rotation IS Class K pin-slot, and rotation inhabits fiber-space (continuous coupling to multiple substrate dimensions). The FPU lift is the right shape.

---

## §2 Partition walk

Following the R30 rolling-spike pattern. Each partition closes with a REPORT before the next opens. Full-coverage per `[[feedback_full_coverage_shipping_mpm_way]]` + `[[feedback_no_mvp_framing]]` (MVPs are learning rungs internal to a partition; never the deliverable).

| # | Partition | Closing artefact |
|---|---|---|
| **R-RBS-NN-1** | MFO two-level ontology mapped to NN cascade | REPORT — per-op two-level placement table |
| **R-RBS-NN-2** | User lexicon as native binding alphabet | REPORT + worked example over held-out user-vocab sample |
| **R-RBS-NN-3a** | MLP cascade decomposition through A-N | REPORT — MLP cascade → A-N slots + Level 1/2 placement |
| **R-RBS-NN-3b** | Decoder-only transformer cascade decomposition | REPORT — transformer cascade → A-N slots |
| **R-RBS-NN-4** | Token → hypervector encoding | REPORT + token-encoder cascade-recipe |
| **R-RBS-NN-5** | Position / context / rotate-overlay binding | REPORT + position-binder cascade |
| **R-RBS-NN-6** | 1:3:7:3 as architectural layout | REPORT + falsification record + chosen reading |
| **R-RBS-NN-7** | Capacity & grow-without-quantization | REPORT + capacity table D ∈ {8192, 32768, 131072, 524288} |
| **R-RBS-NN-8** | Local CPU ALU/FPU inference shape | REPORT + per-class instruction-primitive table |
| **R-RBS-NN-9** | Catalog shape + SSoT absorption | Catalog + ndjson + srmech notebook §RBS-NN landed |

REPORTs land in this directory as `R-RBS-NN-{n}_{slug}_REPORT.md`.

**Post-arc reference files:**
- [`ROADMAP.md`](ROADMAP.md) — next-work items after the arc closes (NEXT-1 LLM compression; NEXT-2 SSoT absorption; NEXT-3 literature attestation; etc.)
- [`UPSTREAM_NOTES.md`](UPSTREAM_NOTES.md) — srmech-side observations surfaced during research; resolved in dedicated srmech-fix sessions (not here)

---

## §3 Working constraints

| Constraint | Plan |
|---|---|
| Temp research subtree | `docs/srmech/rbs_nn_research/` — all per-partition REPORTs land here |
| Eventual SSoT | `docs/srmech/srmech_research_notebook.md` absorbs the arc at R-RBS-NN-9 close |
| Catalog homes | `docs/srmech/catalogs/rbs_nn/descriptor.toml` (+ ndjson rows) per srmech convention — created at R-RBS-NN-9 |
| No-edits constraint | Only ADD new files. Do not touch existing srmech modules (`python/srmech/**`, `c/**`, live notebooks). Other srmech work is active elsewhere. |
| PR shape | One rolling draft PR. Partition-boundary updates per `[[feedback_rolling_pr_partition_boundary_updates]]` |
| Attestation | MPR v1 on every cited claim per CLAUDE.md §2 — `source_doi`, `source_url`, `license`, `retrieved_at`, `response_sha256`, `parser_version`, `parser_rule_hash` |
| Citation discipline | Per `[[feedback_pdf_extraction_citation_discipline]]` — extract actual PDF; verify authors + title + arXiv-ID; don't trust prior attributions |
| Vocabulary | Abstract operational lexicon (sign flip, rotate-overlay, pin slot, etc.) is canonical per `[[feedback_abstract_lexicon_is_ada_accommodation]]` |

---

## §4 What stands already (no rebuild needed)

| Standing | Location | Role in RBS-NN |
|---|---|---|
| Class M HDC bind/bundle/similarity | `srmech/amsc/hdc.py` | Core binding op — bit-exact XOR-bind, majority-bundle, Hamming-similarity |
| Class A content-mint | `srmech.amsc.format.sha256_bytes` | Token → content-address; substrate-locus |
| Class I cyclic bind | `srmech/amsc/cyclic.py` | Position binding via `(ℤ/nℤ)*` shift |
| Class J primes | `srmech/amsc/primes.py` | Orthogonality / non-collision basis |
| Class L Laplacian | `srmech/amsc/laplacian.py` | Spectral structure across the binding graph |
| Class N rational anchor | `srmech/amsc/rational.py` | Discrete↔continuous bridge (Stern-Brocot) |
| RBS-HDC instrument prototype | `srmech/signal_processing/rbs_hdc_instrument.py` (Spike #170) | 10/10 strict-spec invariants verified at D=8192 |
| 256K ALU-native packing | ephemerides notebook §1.4 + v0.1.0 notes | Capacity proof at 52-body / 3.3 GB compression |
| AMSC catalog schema | `docs/unsolved-maths/biplanar_chromatic_number/descriptor.toml` | 6-section TOML template + MPR v1 attestation |
| 1:3:7:3 canonical statement | `docs/srmech/srmech_research_notebook.md` §2.6 (lines 175–182) | Substrate-native ordering — the candidate "shape" |
| MFO two-level ontology | `docs/antikythera-maths/mfo_spectral_research_notebook.md` §VII.1.1 (lines 668–743) | Substrate / excitation; ALU / FPU assignment |

---

## §5 Cross-arc references

- **Substrate-native maths (R30 walking-path):** `docs/substrate-native-maths/` — PR #680; 1:3:7:3 antiquity convergence 9/9
- **srmech research notebook:** `docs/srmech/srmech_research_notebook.md` — A-N primitive vocabulary lives here; eventual SSoT for RBS-NN
- **MFO notebook:** `docs/antikythera-maths/mfo_spectral_research_notebook.md` — two-level ontology; substrate / excitation; line 2812 NN-creation framing
- **Ephemerides notebook:** `docs/antikythera-maths/ephemerides_spectral_research_notebook.md` — 256K ALU-native packing precedent
- **Spike #170:** `docs/srmech/notes/spike170_loe_rbs_hdc_architecture_design.md` — RBS-HDC instrument architecture; 10/10 strict-spec invariants
