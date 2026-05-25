# RBS-LM research subtree — open-thread ROADMAP

Tracks named follow-up directions the user has explicitly flagged for
later but is not pursuing right now. Each item carries enough context
that a future partition (or someone else) can pick it up without
re-deriving the framework reading.

For closed partitions see `R-RBS-LM-*_REPORT.md` files alongside this one.

---

## ADA-engineering threads (R-RBS-LM-26 / -27 follow-ups)

### Braille refreshable-display hardware verification

**Status:** UNVERIFIED. Per user direction 2026-05-25: *"I cannot do hardware
verification for braille. I don't know it and don't have the hardware,
but I understand ADA Accommodations."*

**What's already operational (R-RBS-LM-26):**
- Server returns UEB Grade 1 Braille as Unicode Braille Patterns
  (U+2800..U+28FF) when `response_format: {"type": "braille"}`
- Wire format is Unicode-standard — what every refreshable Braille display
  driver consumes as input
- 6/6 English round-trip verified; mixed-modality preserves non-English Unicode

**What's NOT verified:**
- Real-hardware end-to-end with refreshable Braille displays:
  - HumanWare BrailleNote Touch / Touch Plus
  - Freedom Scientific Focus 40 Blue / Focus 14 Blue
  - HIMS BrailleSense Polaris / U2
  - Orbit Reader 20
- Screen-reader Braille pipelines: NVDA + display, JAWS + display
- Embosser pipelines: Index Everest / ViewPlus Spot Dot — these consume
  Braille ASCII (different from Unicode Braille Patterns); a conversion
  step may be needed
- Real-world UEB Grade 1 vs Grade 2 contracted Braille — some readers
  expect Grade 2 (~180 contractions); we ship Grade 1 only

**Next step when an accessibility-engineering volunteer is available:**
1. Open one of the response_format: braille endpoints; capture output
2. Send to a real refreshable display via standard screen-reader pipeline
3. Verify reader behavior matches the Unicode codepoints we emit
4. If Grade 2 needed: integrate `liblouis` (open Braille translation lib)
5. Document any quirks/divergences as a new partition REPORT

**Why we can document this without verifying it:**
The Unicode Braille Patterns block IS the lingua franca between Braille
software (SBC NVDA + others) and refreshable displays. We emit standard-
conforming codepoints. The verification gap is *real* but the format gap
is closed.

---

### Parallel English↔SignWriting corpus sourcing

**Status:** SCAFFOLD ONLY (R-RBS-LM-26 §3.2). The byte-level surface
accepts Sutton SignWriting Unicode (U+1D800..U+1DAAF; 688 codepoints;
verified accepted), but no English↔SignWriting parallel corpus has been
absorbed.

**The R-RBS-LM-27 intermediate is NOT a SignWriting corpus.** R-RBS-LM-27
ships an English↔ASL-gloss-notation corpus (slash-wrapped sign names like
`/beat-egg/`). That gloss notation is render-ready: a downstream tool
maps `/beat-egg/` → SignWriting glyphs / 3D-avatar animation / video clip.
This intermediate is operational; the direct SignWriting Unicode
encoding is still gapped.

**Sourcing options for English↔SignWriting Unicode parallel data:**
1. **SignBank SignPuddle** (https://signbank.org/signpuddle/) —
   community-contributed SignWriting examples; some carry English labels
2. **Path D distillation** from a sign-language-trained BPE model —
   no public ASL-trained model with byte-decodable SignWriting output
   exists today; would need to be commissioned
3. **Auto-generate from R-RBS-LM-27 gloss notation** via a deterministic
   `/sign-name/` → SignWriting codepoint table — only works for signs
   that have a published Sutton notation; many lexical items don't
4. **Manual curation** — annotate 1000+ English sentences with full
   SignWriting Unicode; substantial linguistic-engineering effort

---

### Grade 2 (contracted) Braille

**Status:** NOT IMPLEMENTED (R-RBS-LM-26 §6 open thread).

UEB Grade 2 has ~180 contractions (word-level: `the` → `⠮`; part-word:
`-ing` → `⠬`; etc.). Many Braille readers — particularly experienced
adult users — read Grade 2 by default. Grade 1 is more common in
beginner / international contexts.

**Implementation path:**
- Use `liblouis` (https://liblouis.io/) — open Braille translation
  library; standard in NVDA, BRLTTY, others
- Wrap as another `response_format` value: `{"type": "braille-grade2"}`
- Keep Grade 1 as the default; opt-in for Grade 2

---

### Larger ASL-gloss corpus for context-sensitivity

**Status:** R-RBS-LM-27 ships 74 pairs / 1324 observations; polysemy hit
rate 0/11 (mode-collapse below context-disambiguation threshold).

**Sourcing options:**
- ASL-LRP corpora (Boston University ASL Linguistic Research Project) —
  English glosses + linguistic annotations; not Sutton notation but
  compatible with our slash-notation
- WLASL (Word-Level American Sign Language) — video-aligned but
  metadata includes English glosses
- ASLG-PC12 (ASL Gloss Parallel Corpus, 12-million-word) — large
  parallel corpus; requires acceptance + use agreement
- Manual extension of R-RBS-LM-27's corpus to ~500-1000 pairs with
  comprehensive polysemy coverage

**Scale prediction (extrapolating from R-RBS-LM-25 / -27):**
- At ~1300 obs: surface works, mode-collapse on content
- At ~10,000 obs (10x scale): might see polysemy structure emerging
- At ~100,000 obs (with multi-threaded R-RBS-LM-11 encode): plausible
  context-disambiguation; not guaranteed (the 3.3% structural ceiling
  per R-RBS-LM-19 still applies)

---

## Translation surfaces beyond English-only

### English↔French / English↔Spanish / English↔Chinese

**Status:** STRUCTURALLY AVAILABLE; no parallel corpus encoded yet.

Per R-RBS-LM-25 byte-level finding: the surface accepts ALL languages
(UTF-8 covers everything). Per R-RBS-LM-27 paired-stream pattern: any
parallel corpus can be absorbed via the same `<source>\x02<target>\x03`
encoding.

**To enable English↔French (worked example):**
1. Source a parallel corpus (Europarl; ParaCrawl; UN; OPUS):
   ```
   from datasets import load_dataset
   ds = load_dataset("Helsinki-NLP/opus-100", "en-fr")
   ```
2. Reuse `encode_asl_corpus.py` with the new corpus path
3. Add `response_format: {"type": "french-translation"}` to the server
4. Run smoke against held-out test sentences

**Or Path D distillation from an existing translation model:**
- NLLB (Meta; multilingual; English-anchored)
- M2M-100 (Meta; 100-language any-to-any)
- OPUS-MT (Helsinki; per-language-pair small models)
- Use Path D pattern (R-RBS-LM-25 §3.2): generate text from the source
  model; retokenize as UTF-8 bytes; encode (source, target) pairs

**Expected outcome:** at modest corpus scale (~10k pairs), same
structural ceiling as ASL-gloss — surface works, content mode-collapses.
At larger scale (~1M+ pairs), maybe some translation structure
emerges; the 3.3% structural ceiling per R-RBS-LM-19 still bounds it.

---

## Cascade-level research threads

### FFT-based active context grafting

**Status:** CLOSED in R-RBS-LM-28 — see
`R-RBS-LM-28_fft_graft_REPORT.md` and `rbs_lm_fft.py`.

The original framing shifted from "truncation" (lossy compression in
frequency basis) to "graft" (surgical COMPOSITION across frequency
bands) per user direction. FFT of bipolar bit-vectors over time
(candidate #2) was the chosen mapping. NTT (candidate #3) remains a
follow-up if pure-substrate finite-field operations are needed.

Result: graft IS operationally meaningful at the cascade interface
level — measurable dose-dependent output changes; cascade discriminates
between long buffers (cooking vs astronomy vs distractor). Surface
operationally available via server's `long_context_buffer` + `fft_cutoff_freq`
request fields.

### FFT multi-buffer graft (layered band composition)

**Status:** CLOSED in R-RBS-LM-32 — see
`R-RBS-LM-32_multi_buffer_fft_REPORT.md` and `multi_buffer_graft` /
`encode_context_with_multi_buffer_graft` in `rbs_lm_fft.py`.

Extends R-RBS-LM-28's single-buffer graft to N buffers across N
contiguous frequency bands (system prompt at lowest band; conversation
history at next; RAG at next; recent fills above). Smoke evidence:
ORDER of band assignment matters (2/3 prompts differ when buffers are
reversed); NUMBER of layers matters (3/3 prompts differ between 2-layer
and 3-layer). Multi-buffer outputs showed HIGHER byte diversity than
single-buffer — first sign of edging out of single-byte mode-collapse.
Server surface: `long_context_buffers` (array) + `fft_layered_cutoffs`
(parallel array) request fields.

### srmech C/Python parity multi-thread design notes

**Status:** PROPOSED. Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`,
ships as research notes for the srmech-fix session to consume.

Target: `vectorised_cleanup` is the per-step bottleneck (~180 ms/tok for
BPE; ~60 ms/tok for byte-level). Multi-threaded C version splitting vocab
rows across CPU threads could compound the existing numpy SIMD speedup.

Surface: thread-safety contract for Class M / K / L primitives;
OpenMP integration plan; ABI compatibility analysis.

### Larger-scale byte-level encode

**Status:** PROPOSED (R-RBS-LM-25 §7 open thread).

R-RBS-LM-25 capped at 10k bytes / ~600 obs. Multi-threaded encode
(R-RBS-LM-11 path) on the full srmech notebook (203k tokens × ~5 bytes/token
≈ 1M bytes; stride 8 → 125k obs) takes ~minutes single-thread; ~30s
multi-thread. Test whether mode-collapse persists or disambiguation
emerges at 100x R-RBS-LM-25 scale.

---

## Upstream-absorption thread

### srmech.rbs_lm subpackage at v0.5.0rc

**Status:** DEFERRED to a dedicated srmech-fix session per
`[[feedback_upstream_srmech_fixes_as_research_notes]]`.

Per R-RBS-LM-12 §6 + each subsequent REPORT's §6 plan, the research-subtree
modules absorb into:

```
docs/srmech/python/srmech/rbs_lm/
├── __init__.py
├── encoder.py          # absorbs rbs_lm_encoder.py + rbs_lm_path_c.py
├── bytes.py            # absorbs rbs_lm_bytes.py
├── inference.py        # absorbs rbs_lm_inference.py
├── chatbot.py          # absorbs RBSChatbot + RBSChatbotBytes
├── server.py           # absorbs rbs_lm_server.py
├── cli.py              # CLI wrapper: srmech rbs-lm <subcommand>
├── distill.py          # absorbs encode_bytes_variant_b.py (Path D)
├── learning.py         # absorbs encode_research_notebook.py
├── tools.py            # absorbs rbs_lm_tools.py (ToolEntry registrations)
├── braille.py          # absorbs rbs_lm_braille.py
└── asl.py              # absorbs rbs_lm_asl.py + asl_gloss_notation logic
```

CLI:

```bash
srmech rbs-lm encode-notebook --notebook PATH
srmech rbs-lm distill --source gpt2 --gen-bytes 100000
srmech rbs-lm encode-pairs --corpus PATH       # for parallel-corpus learning
srmech rbs-lm serve [--byte-mode] [--instrument PATH] [--port 8788]
srmech rbs-lm list-tools                       # tool_schema introspection
```

Storage tooling (R-RBS-LM-22) absorbs as `srmech.amsc.storage`.

The AMSC `compute_from_source` adapter (R-RBS-LM-13) does the precheck →
fetch → encode → save end-to-end via catalog descriptor.

---

## Tested and answered (no longer open)

### Does source-model size lift the cascade ceiling?

**Answered NO in R-RBS-LM-29** (see `R-RBS-LM-29_source_size_REPORT.md`).
9× larger source (GPT-2 124M → TinyLlama 1.1B) produced the same single-
byte mode-collapse at the same encoding scale. R-RBS-LM-19 structural-
ceiling argument reinforced: cascade architecture IS the ceiling, not
training-corpus richness. Architectural moves (R-RBS-LM-28 FFT graft, etc.)
are the research priority going forward.

Infrastructure built: `distill_cron.sh` makes Llama 8B / 30B / 70B Q4
distillations achievable as overnight/weekend cron tasks if a future
question wants to verify the orthogonality at larger source scale.

### Correction to R-RBS-LM-29 Finding 2 framing — fp16 70B is feasible via swap

**Documented in R-RBS-LM-30** (see `R-RBS-LM-30_swap_REPORT.md` + `check_swap.sh`).
R-RBS-LM-29 claimed "Llama 70B fp16: infeasible (140 GB > 96 GB RAM)."
That's incorrect for Path D distillation: we're not doing real-time
inference, so swap absorbs the overflow at a slower per-token rate
(~10-30 sec/tok estimated). 50k-byte corpus via fp16 70B with swap is
a ~1-4 day cron-task — slow but achievable. `check_swap.sh recommend
140` reports the exact swap budget needed (67 GB additional on top of
the existing 8 GB Ubuntu default). Q4 GGUF is still faster when
available; fp16 with swap is the unquantized fallback.

---

*Last updated: 2026-05-25 — R-RBS-LM-32 close.*
