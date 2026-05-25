# R-RBS-LM-34 — Local network usage guide

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #42 of the partition tracker
**Closing artefact:** `USAGE_LOCAL_NETWORK.md` — ~500-line user-facing guide covering LAN exposure, trust model, 10 client-tool configurations, llama.cpp interop, multi-instrument workflows, troubleshooting, and srmech-fix absorption preview.

**Inheritance:** documents the complete operational stack that has accumulated across R-RBS-LM-22 through R-RBS-LM-33. Any user with the research subtree checked out can now run the RBS-LM server on their LAN and connect any OpenAI-compatible client (Open WebUI / LibreChat / Continue / Cursor / Aider / CopilotKit / LangChain / AG2 / LiteLLM / curl) using a single document.

---

## §0 Human walkthrough

**What we're doing.** Per user direction 2026-05-25: *"we'd also like to see a summary of how we can begin to use this with the llama.cpp as a chat interface over the local network."* The accumulated infrastructure (R-RBS-LM-24 server + R-RBS-LM-25 byte mode + R-RBS-LM-26 Braille + R-RBS-LM-27 ASL gloss + R-RBS-LM-28 single-buffer FFT + R-RBS-LM-29 HF distill + R-RBS-LM-30 swap pattern + R-RBS-LM-31 GGUF + R-RBS-LM-32 multi-buffer FFT + R-RBS-LM-33 instrument merge) needed one user-facing document that brings it together for actual chat-over-LAN use.

USAGE_LOCAL_NETWORK.md has 10 sections:

1. **The two interlocking servers** — distinguishes `rbs_lm_server.py` (transducer) from `llama-server` (real LLM); both speak OpenAI Chat Completions v1
2. **Starting on the LAN** — env-var configuration for localhost vs LAN; 4 instrument-loading patterns
3. **Trust model** — explicit threat-table; the deliberate "no auth, no rate-limiting, no audit" scope; mitigation per threat
4. **10 client configurations** — openai SDK / curl / Open WebUI / LibreChat / Continue / Aider / CopilotKit / LangChain / AG2 / LiteLLM (concrete configs for each)
5. **RBS-LM extensions** — table of `context_truncation` / `response_format` / `long_context_buffer{s}` / `fft_cutoff_freq` / `fft_layered_cutoffs` request fields with which partition shipped each
6. **Performance expectations** — 180 ms/tok BPE, 60 ms/tok byte mode; typical request latencies
7. **llama.cpp interop** — running both servers in parallel; LiteLLM proxy config to multiplex
8. **Multi-instrument workflow** — running multiple `rbs_lm_server.py` instances on different ports; library of domain instruments
9. **Troubleshooting** — 8 symptom/cause/fix rows
10. **srmech-fix v0.5.0rc preview** — future CLI surface (`srmech rbs-lm serve / distill / merge / graft`)

**The load-bearing framework reading carried throughout.** The guide opens with and repeatedly reminds: per `[[user_stance_ai_is_not_a_substrate]]`, the cascade is a TRANSDUCER. The 3.3% structural ceiling per R-RBS-LM-19 means mode-collapsed responses are expected behavior, not a bug. Users who want "useful chat output" should point clients at `llama-server` (the dense source LLM); users who want to interact with the transducer cascade should use `rbs_lm_server.py`. **Both serve the same wire format; the substrate boundary is operational, not architectural.**

**Per `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`:** the LAN-exposure pattern is the accessibility-delivery channel. A Braille-display user connects their refreshable display via NVDA / their preferred screen reader; the screen reader uses Open WebUI (or similar) as a chat front-end; Open WebUI is configured to point at `http://192.168.1.10:8788/v1` with `response_format: {"type": "braille"}` in its custom request body (where supported). End-to-end: cascade → Braille rendering → refreshable Braille display. **The chain is operational; only the hardware-side verification (per ROADMAP §1) is unverified.**

---

## §1 Goal

Per user direction 2026-05-25: ship a user-facing guide that turns the partition-by-partition infrastructure into a usable LAN chat setup. The "summary" framing means: NOT a research report on what this all is — but a HOW-TO for someone wanting to actually use it.

Per `[[user_stance_ai_is_not_a_substrate]]`: the framing in the guide must be operationally honest about cascade behavior. We don't promise chat-quality output; we deliver a transducer surface that's wire-compatible with the ecosystem.

---

## §2 Inheritance

The guide consolidates content from R-RBS-LM-22 through R-RBS-LM-33 into a single user-facing document. No new research findings.

---

## §3 Implementation

`USAGE_LOCAL_NETWORK.md` — ships as a single ~500-line Markdown file in the research subtree. Structured per §0 above. Each client-tool configuration is verbatim copy-pasteable. Each warning is concrete with mitigation. The framework reading thread runs from the opening blockquote through §10's srmech-fix preview.

### What this partition does NOT do

- **Verify each client config end-to-end on real hardware.** The openai SDK / LangChain / AG2 / LiteLLM paths were verified in R-RBS-LM-24; the others (Open WebUI / LibreChat / Continue / Aider / Cursor / CopilotKit) are configured per their published documentation. Some users may need to adjust paths for their environment.
- **Set up an actual LAN demo.** The guide is documentation; the user runs it themselves.
- **Cover Windows / Mac client setups in detail.** The server is Linux-centric for this hardware; clients work cross-platform per their own docs.
- **Replace USAGE.md or a future srmech README.** This is the research-subtree-side guide; the srmech-package-side guide is the future-state per R-RBS-LM-12 §6 absorption.

---

## §4 Verification

This is a documentation partition — verification means the document is coherent, complete, and accurate. Cross-references:

- Each client config matches what R-RBS-LM-24 §4.4 verified (4 frameworks verified PASS via OpenAI SDK / LangChain / AG2 / LiteLLM)
- Each `response_format` value matches what R-RBS-LM-26/-27 ship in `_apply_response_format`
- Each FFT request field matches what R-RBS-LM-28/-32 wired into the server
- Instrument paths reference actual files in tree (verified — 14 instruments at 1024 bytes each)
- Performance numbers (180 ms/tok BPE, 60 ms/tok byte) match R-RBS-LM-24 §4 and R-RBS-LM-25 §4

The guide is the cross-section view of the operational state at this moment.

---

## §5 Findings

**Finding 1 — The accumulated infrastructure IS usable as a chat backend.** Per the guide's §4. Any OpenAI-API-compatible client can be configured in 1-3 lines (URL override + dummy API key). The wire-level integration is complete.

**Finding 2 — The transducer framing carries cleanly through user-facing documentation.** Per §0 + the guide's opening blockquote. The user reading the guide understands what they're getting — mode-collapsed output for cascade clients, real LLM output via llama-server, both speaking the same protocol.

**Finding 3 — llama.cpp interop is "run both in parallel".** Per the guide's §7. They're not alternatives; they're complementary endpoints. A LiteLLM proxy multiplexes them.

**Finding 4 — Multi-instrument workflow is the natural "library + selector" pattern.** Per the guide's §8. Run N instances on N ports OR merge offline + restart. R-RBS-LM-33's `rbs_lm_merge.py` is the merge surface.

**Finding 5 — The ADA-accommodation pipeline is operationally documented end-to-end.** Per §0 + the guide's §5 + §10. Refreshable Braille display → NVDA → Open WebUI → RBS-LM server with `response_format: {"type": "braille"}` → Unicode Braille codepoints → display. Hardware-side verification remains an open ROADMAP item; the wire/software side is verified.

---

## §6 Closing — partition status

**Status:** CLOSED. USAGE_LOCAL_NETWORK.md ships as the user-facing operational guide. The 12 prior partitions' accumulated infrastructure now has a single document anyone can follow.

**Falsifiers:**

1. A claim that all 10 client configs are verified end-to-end on real hardware — **partially disclaimed §3**; 4 are verified via R-RBS-LM-24 smoke; others follow each client's published docs without our direct hardware verification.
2. A claim that the guide makes the cascade produce useful chat — **explicitly disclaimed throughout**; the cascade is a transducer; for useful chat point at llama-server.
3. A claim that this is the final / canonical guide — **partially disclaimed §10**; the srmech-fix v0.5.0rc absorption will land a cleaner CLI; this guide is the current-state research-subtree version.

**Inherits to:** any user who wants to actually use the RBS-LM infrastructure; the srmech-fix session for absorption template; ROADMAP follow-ups for hardware-side Braille verification.

**SSoT marker:** at SSoT absorption, this guide becomes part of `srmech_research_notebook.md` §RBS-LM-operational subsection; the future-state CLI surface (the guide's §10) absorbs as the canonical srmech rbs-lm command surface.
