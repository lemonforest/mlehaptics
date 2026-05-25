# R-RBS-LM-26 — Accessibility output surfaces: Braille (operational) + ASL/SignWriting (scaffold)

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #34 of the partition tracker
**Closing artefacts:**
- `rbs_lm_braille.py` — UEB Grade 1 deterministic encode/decode; 6/6 round-trip OK
- `rbs_lm_asl.py` — SignWriting Unicode surface (U+1D800..U+1DAAF) verified + parallel-corpus scaffold
- `rbs_lm_server.py` — extended with `response_format: {type: text|braille|signwriting}` (OpenAI-API extension); `/health.response_formats_supported` declaration

**Inheritance:** the ADA-accommodation framing (`[[feedback_llm_as_ada_accommodation_bci_proves_it]]`) now has its first operational output surface. Any cascade output — at the 3.3% structural ceiling or below — can be deterministically rendered as Braille for downstream visual-render or refreshable-Braille-display hardware. SignWriting Unicode is verified accepted; encoding deferred to when a parallel English↔SignWriting corpus is available.

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | R-RBS-LM-24 (OpenAI-API server architecture); R-RBS-LM-25 (byte-level surface that accepts SignWriting Unicode); `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` (foundational motivation); `[[user_stance_ai_is_not_a_substrate]]` (rendering is presentation, not substrate) |
| user direction (load-bearing) | *"now see if we can find a way to map ASL and braille. I know that we cannot image out put, but we can make output ready for visual render."* — the load-bearing scope statement: NOT image generation; structurally-ready-for-visual-renderer byte stream |
| external standards | Unicode 8.0 Sutton SignWriting block (ISO/IEC 10646:2014); UEB Grade 1 (Unified English Braille uncontracted); Unicode Braille Patterns block (U+2800..U+28FF, ISO 11548-1:2001) |
| empirical artefacts | `rbs_lm_braille.py`, `rbs_lm_asl.py`, modified `rbs_lm_server.py` |
| repo commit | `8402063f` at REPORT-write (R-RBS-LM-25 close) |
| reproducibility | `~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/rbs_lm_braille.py`; ditto `rbs_lm_asl.py`; server smoke via curl/openai SDK with `response_format` field |

---

## §0 Human walkthrough

**What we're doing.** Per your direction: *"now see if we can find a way to map ASL and braille."* The load-bearing constraint you set: *"I know that we cannot image out put, but we can make output ready for visual render."* This frames the work precisely — we don't generate images; we produce byte streams that a downstream renderer (a refreshable Braille display, a SignWriting-font-aware UI, an ASL-to-3D-avatar pipeline) turns into a visual modality.

Three different shapes of work, three different outcomes:

1. **Braille is deterministic — ships now.** Unicode Braille Patterns (U+2800..U+28FF) is exactly 256 codepoints, one per 8-dot pattern. UEB Grade 1 (uncontracted) is a char-by-char table mapping with capital + number indicators. Our byte-level surface already produces UTF-8; the encoder just translates ASCII English → Braille Unicode chars. No cascade re-training needed because this is a **rendering layer**, not a learning layer. Whatever the cascade produces in English gets rendered in Braille deterministically.

2. **SignWriting Unicode surface is operational — verified.** Sutton SignWriting (U+1D800..U+1DAAF; 688 codepoints; added Unicode 8.0) is a real Unicode block. Each codepoint encodes as 4 bytes in UTF-8. Our byte-level cascade (R-RBS-LM-25) already round-trips these through `errors='replace'` decoding. The surface accepts them; we don't need to do anything special at the wire level.

3. **ASL English↔SignWriting encoding — scaffold-only, honestly disclaimed.** The cascade can be TAUGHT byte-transitions, but only from data. Without a parallel English↔SignWriting corpus (or English↔HamNoSys, or English↔ASL-LRP-gloss), there's no training signal to encode. We ship the `encode_with_modality` hook so that when a corpus exists, it absorbs without architectural change. **No claim of ASL competence is made.** The OpenAI-API `response_format: "signwriting"` is RESERVED — it acknowledges the request with a clear "[signwriting reserved: parallel corpus required]" prefix and passes the underlying text through unchanged.

**Why this is a real ADA win even without ASL encoding.** A user with low vision who consumes content via a refreshable Braille display can now talk to the local expert via any OpenAI-API client (CopilotKit, LangChain, etc. — R-RBS-LM-24) and request `response_format: braille`. The server post-processes the cascade output → returns UEB Grade 1 Braille → the client's existing refreshable-Braille-display driver renders it. **Zero new hardware integration code; zero new tokenizer; zero new fetch.** The accessibility surface exists at the API layer, not the cascade layer.

**Why SignWriting reservation is honest, not a placeholder.** The byte-level cascade can encode and produce SignWriting Unicode characters mechanically (just byte sequences). What it lacks is the *learned mapping* from English content to ASL content. Both Braille and SignWriting are presentation formats, but Braille is a **rule-based** presentation of English (deterministic), while SignWriting is a **structurally different language** (ASL has its own grammar, non-manual markers, classifiers, spatial reference). Translating English→ASL is a different problem than rendering English→Braille. We can do the first procedurally; the second needs training data we don't have.

**How srmech automates it (future state per R-RBS-LM-12 §6).** When srmech-fix lands the v0.5.0rc, this absorbs as:

```
docs/srmech/python/srmech/rbs_lm/braille.py     # absorbs rbs_lm_braille.py
docs/srmech/python/srmech/rbs_lm/asl.py         # absorbs rbs_lm_asl.py (scaffold-only)
docs/srmech/python/srmech/rbs_lm/server.py      # response_format integrated
```

End-user CLI surface:
```bash
srmech rbs-lm serve --byte-mode --port 8788
curl -X POST localhost:8788/v1/chat/completions \
  -d '{"model": "rbs-lm-v18-path-c", "messages": [...],
       "response_format": {"type": "braille"}}'
```

ANY downstream tool (CopilotKit / LangChain / AG2 / LiteLLM / curl) that sets `response_format: {"type": "braille"}` in its OpenAI-shape request gets Braille back. **The OpenAI-API extension mechanism (R-RBS-LM-24) IS the ADA-accommodation distribution channel.**

---

## §1 Goal

Per user direction 2026-05-25: extend the byte-level OpenAI-API surface (R-RBS-LM-25) with rendering surfaces appropriate for visual-render-targeted downstream tools. Scope explicitly bounded: NOT image generation; structurally-ready-for-visual-renderer byte stream. Two specific surfaces named: ASL + Braille.

Per `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` (foundational motivation): accessibility surfaces are NOT add-ons — they are core to the framework reading. A local expert that cannot serve a Braille-display user is missing a foundational dimension.

---

## §2 Inheritance

| Source | Inherited finding | Use |
|---|---|---|
| R-RBS-LM-24 | OpenAI-API server with extension fields (context_truncation precedent) | response_format added as a second extension field |
| R-RBS-LM-25 | Byte-level surface accepts ANY UTF-8 (verified Chinese/Arabic/emoji/code) | SignWriting Unicode is also UTF-8 → surface-accepted; same path |
| `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` | ADA accommodation is foundational | This partition operationalizes the framing |
| `[[user_stance_ai_is_not_a_substrate]]` | Local expert is transducer; rendering is presentation | Braille IS the same cascade output, different surface — framework reading unchanged |
| Unicode 8.0 Sutton SignWriting | U+1D800..U+1DAAF; 688 codepoints; visually renderable | Sample codepoints validated in §4.2 |
| UEB Grade 1 (BANA + ICEB standards) | Uncontracted English Braille; one cell per char | §3.1 table |

---

## §3 Implementation

### §3.1 `rbs_lm_braille.py` — UEB Grade 1 encode/decode

```python
def english_to_braille(text, capital_indicator=True, number_indicator=True) -> str
def braille_to_english(text) -> str
```

Tables:
- 26 lowercase letters → U+2801..U+283D
- 10 digits use letter patterns a-j with leading NUMBER_INDICATOR ⠼ (U+283C)
- 7 punctuation marks: `. , ; : ? ! '` (`" - ( ) /` also covered)
- CAPITAL_INDICATOR ⠠ (U+2820) precedes uppercase letters
- Newlines passed through; tabs become spaces
- **Unknown characters pass through unchanged** — this preserves non-English Unicode (Chinese / emoji / accented chars) so the cascade's multi-language outputs survive the rendering layer

### §3.2 `rbs_lm_asl.py` — SignWriting surface + scaffold

```python
SIGNWRITING_BLOCK_START = 0x1D800
SIGNWRITING_BLOCK_END = 0x1DAAF      # 688 codepoints
def is_signwriting_codepoint(cp) -> bool
def signwriting_string(codepoints) -> str
def text_contains_signwriting(text) -> bool
def encode_with_modality(english_text, signwriting_text, ...) -> bytes
    # raises NotImplementedError with clear corpus-requirement message
```

The scaffold (`encode_with_modality`) is real code that documents the encoding plan in its docstring:
1. Tokenize both English and SignWriting as UTF-8 bytes
2. Build paired byte stream with separator
3. Slide context window; encode (context, next_byte) bindings
4. At separator position, cascade learns what bytes follow

When a parallel corpus arrives, this function absorbs it. **No claim of ASL competence is made.**

### §3.3 Server `response_format` extension (OpenAI-API)

Request schema gains an optional field:
```python
class ResponseFormat(BaseModel):
    type: str = Field(default="text")  # text | braille | signwriting

class ChatCompletionRequest(BaseModel):
    ...
    response_format: Optional[ResponseFormat] = None
```

Post-processing dispatcher:
```python
def _apply_response_format(text, response_format):
    if response_format is None or response_format.type == "text":
        return text
    if response_format.type == "braille":
        return english_to_braille(text)
    if response_format.type == "signwriting":
        return f"[signwriting reserved: parallel corpus required] {text}"
    raise HTTPException(400, ...)
```

`/health` advertises supported formats:
```json
"response_formats_supported": {
  "text": "raw cascade output (default)",
  "braille": "UEB Grade 1 English Braille (Unicode U+2800..U+28FF); ...",
  "signwriting": "RESERVED — requires parallel English↔SignWriting corpus; ..."
}
```

### §3.4 What this partition does NOT do

- **Generate images.** Explicitly excluded per user scope direction. We produce byte streams ready for downstream renderers (refreshable Braille displays, SignWriting fonts, ASL avatar pipelines).
- **Lift the 3.3% cascade ceiling.** This is rendering work, not learning work. The cascade output quality is unchanged.
- **Provide ASL competence.** No parallel corpus → no English↔ASL training signal → no ASL knowledge. The surface is ready; the data is the gap.
- **Implement Grade 2 Braille (contractions).** Grade 1 round-trips cleanly; Grade 2 has ~180 contractions and would need a dedicated library (e.g., `liblouis`). Deferred unless a Grade 1 limitation surfaces in actual use.
- **Implement HamNoSys / ASL-LRP / other ASL notations.** SignWriting is the canonical Unicode-block ASL notation; others can absorb via the same scaffold once a corpus exists in their notation.

---

## §4 Verification — captured runs

### §4.1 Braille round-trip self-test

```
=== R-RBS-LM-26 Braille self-test ===

  'Hello, World!'  →  ⠠⠓⠑⠇⠇⠕⠂⠀⠠⠺⠕⠗⠇⠙⠖   →  'Hello, World!'  OK
  'ABC abc'        →  ⠠⠁⠠⠃⠠⠉⠀⠁⠃⠉           →  'ABC abc'        OK
  'Once upon a time'   → ⠠⠕⠝⠉⠑⠀⠥⠏⠕⠝⠀⠁⠀⠞⠊⠍⠑    →  'Once upon a time'  OK
  'Send 42 cookies.'   → ⠠⠎⠑⠝⠙⠀⠼⠙⠃⠀⠉⠕⠕⠅⠊⠑⠎⠲  →  'Send 42 cookies.'  OK
  'Test: a-z mapping.' → ⠠⠞⠑⠎⠞⠒⠀⠁⠤⠵⠀⠍⠁⠏⠏⠊⠝⠛⠲ →  'Test: a-z mapping.'  OK
  'The morning sun cast' → ⠠⠞⠓⠑⠀⠍⠕⠗⠝⠊⠝⠛⠀⠎⠥⠝⠀⠉⠁⠎⠞ →  'The morning sun cast'  OK

Round-trip: 6/6 cases OK

=== Mixed-modality (cascade output that's non-English survives) ===
  'Hello 世界'      → ⠠⠓⠑⠇⠇⠕⠀世界            →  'Hello 世界'      OK
  'test 🌍 emoji'   → ⠞⠑⠎⠞⠀🌍⠀⠑⠍⠕⠚⠊         →  'test 🌍 emoji'   OK
  'café résumé'    → ⠉⠁⠋é⠀⠗é⠎⠥⠍é           →  'café résumé'    OK
```

All 6 English round-trips clean. Mixed-modality preserves non-English Unicode (Chinese / emoji / accented characters pass through the formatter unchanged) — important for multi-language cascade outputs from R-RBS-LM-25.

### §4.2 SignWriting Unicode surface

```
  Sutton SignWriting block: U+1D800..U+1DAAF
  Block size: 688 codepoints

  Sample codepoints:
    U+1D800 → '𝠀' → UTF-8 bytes: [240, 157, 160, 128] (4 bytes)
    U+1D801 → '𝠁' → UTF-8 bytes: [240, 157, 160, 129] (4 bytes)
    U+1D850 → '𝡐' → UTF-8 bytes: [240, 157, 161, 144] (4 bytes)
    U+1D8A0 → '𝢠' → UTF-8 bytes: [240, 157, 162, 160] (4 bytes)
    U+1D900 → '𝤀' → UTF-8 bytes: [240, 157, 164, 128] (4 bytes)
    U+1DA00 → '𝨀' → UTF-8 bytes: [240, 157, 168, 128] (4 bytes)
    U+1DAA0 → '\U0001daa0' → UTF-8 bytes: [240, 157, 170, 160] (4 bytes)

  Round-trip test:
    Input:   7 SignWriting codepoints
    Encoded: 28 UTF-8 bytes
    Decoded: 7 chars
    Round-trip OK: True

  Codepoint predicate tests: 6/6 OK
  encode_with_modality scaffold: raises NotImplementedError as expected
```

Surface verified: 4-byte UTF-8 encoding per codepoint; round-trip clean. The byte-level cascade (R-RBS-LM-25) accepts these the same way it accepts emoji (4-byte UTF-8) and CJK (3-byte UTF-8).

### §4.3 End-to-end OpenAI-API with response_format

```
$ curl http://127.0.0.1:8788/health | jq '.response_formats_supported'
{
  "text": "raw cascade output (default)",
  "braille": "UEB Grade 1 English Braille (Unicode U+2800..U+28FF); deterministic; R-RBS-LM-26",
  "signwriting": "RESERVED — requires parallel English↔SignWriting corpus; surface accepted, encoding deferred"
}
```

Three round-trips (prompt = "The morning sun"; max_tokens=10; v18 BPE Path C):

```
  response_format=type='text'
    completion: ' answer.13.11 is13 is\n\n'

  response_format=type='braille'
    completion: '⠀⠁⠝⠎⠺⠑⠗⠲⠼⠁⠉⠲⠼⠁⠁⠀⠊⠎⠼⠁⠉⠀⠊⠎\n\n'

  response_format=type='signwriting'
    completion: '[signwriting reserved: parallel corpus required]  answer.13.11 is13 is\n\n'

  (no response_format — default text)
    completion: ' answer.13.11 is13 is\n\n'
```

Verification of the Braille rendering:
- `⠀⠁⠝⠎⠺⠑⠗⠲` decodes back to ` answer.` (leading space, a-n-s-w-e-r, period)
- `⠼⠁⠉` = number indicator ⠼ + a + c = `13` (a=1, c=3 in number mode)
- `⠲` = period
- `⠼⠁⠁` = `11`
- `⠊⠎` = is
- `⠼⠁⠉` = 13
- `⠊⠎` = is

The cascade output ` answer.13.11 is13 is` renders to Braille as expected. **Same content; alternative surface.**

---

## §5 Findings

**Finding 1 — Braille rendering is deterministic, operational, and trivially distributable.** Per §3.1 + §4.1 + §4.3. The mapping is a fixed table; 6/6 English round-trip OK; non-English Unicode passes through unchanged. Any cascade output the local expert produces — even at the 3.3%-ceiling mode-collapse outputs of R-RBS-LM-25 byte-level — renders to valid Braille codepoints downstream renderers can display.

**Finding 2 — The OpenAI-API `response_format` extension is the ADA-accommodation distribution channel.** Per §3.3 + §4.3. ANY tool in the ecosystem (CopilotKit / LangChain / AG2 / LiteLLM / vanilla openai / curl) that sets `response_format: {"type": "braille"}` in its standard request gets Braille back. Zero new wire format; zero new client SDKs needed. The accessibility surface lives at the API layer.

**Finding 3 — SignWriting Unicode surface is operationally accepted.** Per §4.2. 688-codepoint Unicode block; 4-byte UTF-8 per codepoint; round-trip clean. The byte-level cascade (R-RBS-LM-25) already handles this; no new wire-level work needed. **What's missing is the parallel corpus to teach English↔ASL mappings** — surface ≠ knowledge.

**Finding 4 — Braille rendering does NOT lift the cascade ceiling — it's not supposed to.** Per §4.3 + §0. The Braille output of ` answer.13.11 is13 is` is the same low-quality cascade output rendered in a different surface. Per `[[user_stance_ai_is_not_a_substrate]]`: rendering is presentation, not substrate. **Better output requires a better cascade, not a better renderer.** Honest framework reading.

**Finding 5 — The ASL scaffold is honest, not a placeholder.** Per §3.2. `encode_with_modality` raises `NotImplementedError` with a clear corpus-requirement message; `response_format: "signwriting"` returns `[signwriting reserved: parallel corpus required] <text>` so the client unambiguously sees the state. No silent broken behavior; no false ASL-competence claim.

**Finding 6 — The user's scope constraint *"we cannot image out put, but we can make output ready for visual render"* is the load-bearing read.** Per §0. Braille IS visual-renderable byte stream — refreshable Braille displays, Braille-font UIs, embossers all consume Unicode Braille Patterns directly. SignWriting IS visual-renderable byte stream — Sutton SignWriting fonts render the codepoints to glyphs. **We deliver byte streams; the visual render is downstream.** This is the right substrate boundary per the framework reading.

**Finding 7 — Cross-modal preservation: rendering layer respects multi-language cascade outputs.** Per §4.1 (mixed-modality cases). When the Braille formatter encounters non-English Unicode (Chinese / emoji / accented chars), it passes them through unchanged. This means if R-RBS-LM-25 byte-level produces a Chinese fragment, the Braille formatter preserves it adjacent to English-Braille output. **No silent data loss across the rendering layer.**

**Finding 8 — The §0 human-walkthrough discipline holds even when one deliverable is a scaffold-only.** Per §0. The walkthrough is honest about Braille=operational vs. ASL=scaffold without losing reader-coherence. The pattern accommodates mixed-status deliverables in one partition.

---

## §6 Open threads (not blockers for partition close)

- **Parallel English↔SignWriting corpus sourcing.** The sister direction R-RBS-LM-25 §7 noted Path-D-distillation of a sign-language-trained model as an option. Other options: ASL-LRP gloss corpora (public; English glosses + linguistic annotations); SignBank.org SignPuddle (community-contributed SignWriting examples); ASLLVD / WLASL (video-aligned but visual-only).
- **Grade 2 (contracted) Braille.** UEB Grade 2 has ~180 contractions. `liblouis` is the canonical open implementation; would add as a dependency if Grade 1 limitation surfaces.
- **Refreshable-Braille-display driver verification.** Our server returns Braille Unicode; we haven't verified end-to-end with a real refreshable-Braille-display device (e.g., BrailleSense, Focus 40 Blue). The Unicode IS the standard interchange format; verification on real hardware is a separate accessibility-engineering effort.
- **HamNoSys / ASL-LRP gloss as alternative response_format types.** SignWriting is the canonical Unicode option; HamNoSys uses Private Use Area codepoints; gloss is ASCII. Could extend `response_format.type` enum if a downstream tool needs a specific notation.
- **Multi-format response (e.g., `formats: ["text", "braille"]` array).** Currently one format per response. A multi-format response would let clients fan out to multiple renderers. Easy extension if needed.

---

## §7 Closing — partition status

**Status:** CLOSED. Braille rendering ships operational + verified end-to-end via OpenAI-API. SignWriting Unicode surface verified accepted. ASL encoding scaffold documents parallel-corpus requirement honestly. The OpenAI-API `response_format` extension provides the distribution channel for any ecosystem tool to consume the ADA-accommodation surface without new client SDKs.

**Falsifiers:**

1. A claim that this partition delivers ASL competence — **explicitly disclaimed §5 Finding 5**; ASL is scaffold-only; no parallel corpus, no claim.
2. A claim that Braille rendering improves the cascade ceiling — **explicitly disclaimed §5 Finding 4**; rendering is presentation, not substrate.
3. A claim that we generate images — **explicitly disclaimed §0 + §3.4** per the user's load-bearing scope constraint.
4. A claim that the OpenAI-API extension is non-standard / breaks ecosystem compatibility — **partially disclaimed**: `response_format` IS the OpenAI-defined extension field (used for JSON-mode requests in production OpenAI); we extend its `type` enum with new values (`braille`, `signwriting`). Tools that don't set the field get unchanged default behavior.

**Inherits to:**
- Any downstream Braille-display integration (the wire surface is now in place)
- Any future partition that sources a parallel English↔SignWriting corpus (the scaffold absorbs it)
- The srmech-fix v0.5.0rc absorption (per R-RBS-LM-12 §6 plan)

**SSoT marker:** at SSoT absorption, §0 human walkthrough + §3 implementation + §5 framework-reading findings absorb into `srmech_research_notebook.md` as a new §RBS-LM-accessibility subsection. The ADA-accommodation framing operationalization is potentially load-bearing for the broader MFO discipline (rendering surface vs. substrate boundary).
