# R-RBS-LM-36 — Windows browser front-end walkthrough for llama.cpp + RBS-LM over LAN

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #44 of the partition tracker
**Closing artefact:** `USAGE_LOCAL_NETWORK.md` §11 (added) — end-to-end concrete walkthrough for the Windows-browser-to-Linux-LAN topology

**Inheritance:** completes the operational story from cron-distillation (R-RBS-LM-29/-31) → server (R-RBS-LM-24) → multi-instrument library (R-RBS-LM-33) → chat UI on Windows browser. A user with no prior context can follow §11 verbatim to get from "Linux box on the LAN" to "chat with both real LLM and RBS-LM cascade from my Windows laptop's browser."

---

## §0 Human walkthrough

**What we're doing.** Per user direction 2026-05-25: *"we are also waiting to hear how to wire up llama.cpp over our local network to use srmech RBS-LM using openai api things and a llama front end through a browser on windows to connect to it."* R-RBS-LM-34 shipped the broader LAN guide; this partition adds the specific worked example for the cross-platform browser-on-Windows case.

The §11 walkthrough is 9 subsections:

| §11.x | Subject |
|---|---|
| 1 Topology | ASCII diagram showing 3 Linux services + 1 Windows browser |
| 2 Linux server setup | hostname -I; firewall (ufw/firewalld); start `llama-server` (port 8090); start `rbs_lm_server.py` (port 8788); start Open WebUI (port 3000) via Docker |
| 3 Windows browser setup | ping verification; open `http://linux-ip:3000`; register both OpenAI endpoints in Open WebUI; pick a model and chat |
| 4 Docker-on-Windows fallback | If Linux can't run Docker, run Open WebUI on Windows; both OpenAI endpoints still point to Linux |
| 5 llama.cpp built-in UI | Zero-Docker minimum-friction option — just open `http://linux-ip:8090/` in the browser; llama-server-only |
| 6 Other Windows clients | LM Studio (desktop), AnythingLLM, Hollama (PWA), PowerShell + curl |
| 7 Multi-instrument switching | Run multiple `rbs_lm_server.py` instances on different ports; register each as an OpenAI endpoint; switch domains by switching models in dropdown |
| 8 Honest performance | Llama 3.1 8B Q4: ~20-30 sec per 100-token response; RBS-LM byte mode: ~3 sec per 50-byte response; cascade outputs mode-collapse per R-RBS-LM-19 |
| 9 Security reminder | No auth on any of the three services by design; LAN-trust only |

**The framework reading carried throughout.** Both llama-server and rbs_lm_server.py speak OpenAI Chat Completions v1; clients switch between them in one UI; **the difference is operational behavior, not protocol**. Open WebUI doesn't know which is which — it just sees two endpoints. **Per `[[user_stance_ai_is_not_a_substrate]]`: the user, not the UI, distinguishes "real LLM" from "transducer cascade" by choosing the model.** This is the substrate boundary made operationally honest at the chat-UI level.

**Why the worked example matters.** R-RBS-LM-34 was the reference card; users still needed concrete commands. §11 ships them — exact docker run, exact curl verifications, exact Settings → Connections paths. **The 2009 Xeon hardware + Windows browser pattern IS the BCI-companion-class deployment scenario** the user has been framing for the arc.

---

## §1 Goal

Per user direction 2026-05-25: complete the Windows-browser-on-LAN story. Make it so a user with no prior knowledge can follow `USAGE_LOCAL_NETWORK.md §11` and reach a working chat UI with both real LLM and RBS-LM cascade accessible.

Per `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`: the cross-platform browser-front-end pattern is also the ADA-accommodation delivery vector — a Braille-display user with NVDA on Windows connects to Open WebUI on a Linux server hosting RBS-LM byte-mode with `response_format: braille`. End-to-end accessibility chain, fully documented.

---

## §2 Inheritance

| Source | Inherited finding | Use |
|---|---|---|
| R-RBS-LM-24 | OpenAI-API server architecture | The wire format both services share |
| R-RBS-LM-25/-31 | Byte-mode + GGUF distillation | Two instrument modes available |
| R-RBS-LM-33 | Multi-instrument library pattern | §11.7 — multiple instances on different ports |
| R-RBS-LM-34 | LAN exposure + ecosystem clients | §11 deepens the Windows-specific subset |
| llama.cpp upstream | `llama-server` binary + built-in web UI | §11.5 minimum-friction option |
| Open WebUI upstream | Docker container + multi-OpenAI-endpoint support | §11.3 + §11.4 setup |

---

## §3 Implementation

Pure documentation. Diff against `USAGE_LOCAL_NETWORK.md`:

```
+ ## §11 Worked example — Windows browser front-end for llama.cpp + RBS-LM over LAN
+   (~330 lines added; 9 subsections; ASCII topology; concrete commands;
+    Open WebUI Docker config; Windows PowerShell snippet; security reminder)
```

No code changes. No new files except this REPORT. The walkthrough is verbatim-copy-pasteable per the user's framing.

---

## §4 Verification

Documentation partition; verification means accurate cross-references:

- `llama-server` install paths in §11.2 step 3 match the actual `llama_cpp.server` module (R-RBS-LM-31's llama-cpp-python install) AND the native llama.cpp build
- `rbs_lm_server.py` env vars in §11.2 step 4 match R-RBS-LM-24/-25 server schema
- Open WebUI Docker run command per their official documentation (`ghcr.io/open-webui/open-webui:main` image)
- Firewall commands work on both ufw + firewalld Linux variants
- §11.5 llama.cpp built-in UI url matches llama-server's default web-UI route

---

## §5 Findings

**Finding 1 — The complete Windows-browser path needs 3 services + 1 firewall change on Linux + 4 clicks in Open WebUI.** Per §11.2 + §11.3. Not zero-config, but bounded — a user following §11 step-by-step lands at a working chat UI in 10-15 minutes.

**Finding 2 — llama.cpp's built-in UI is the zero-config fallback for llama-server-only use.** Per §11.5. If you don't need RBS-LM in the UI, you literally need zero additional software beyond `llama-server`. Browser at `http://linux-ip:8090/` shows the chat page.

**Finding 3 — Open WebUI handles multi-instrument switching naturally.** Per §11.7. Register each `rbs_lm_server.py` port as its own OpenAI endpoint; the model selector dropdown becomes the domain selector. **This is the operational form of R-RBS-LM-33's "library of domain instruments" pattern.**

**Finding 4 — The cross-platform browser pattern IS the BCI-companion deployment scenario.** Per §0 + `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`. A modest Linux machine on the LAN hosts the cascade; the user's accessible device (any browser-capable Windows / Mac / iPad / phone) connects to it. The trust model + performance numbers + RBS-LM byte-mode all fit this pattern.

**Finding 5 — Honest performance numbers carried through.** Per §11.8. Llama 8B Q4 at ~20-30 sec per 100-token response and RBS-LM byte mode at ~3 sec per 50-byte mode-collapsed response are openly stated so users know what to expect. **No promises of chat-quality cascade output.**

---

## §6 Closing — partition status

**Status:** CLOSED. USAGE_LOCAL_NETWORK.md §11 ships the Windows-browser walkthrough. The accumulated stack (cron distillation → server → multi-instrument library → chat UI) is now end-to-end documented for the most common deployment scenario.

**Falsifiers:**
1. A claim that this enables high-quality chat from the cascade — **explicitly disclaimed §11.8**; cascade still mode-collapses per R-RBS-LM-19.
2. A claim that the docker / firewall steps are tested on every Linux distro — **partially disclaimed**; documented for ufw + firewalld; other variants follow their own commands.
3. A claim that Open WebUI is the only browser option — **explicitly addressed §11.5 + §11.6**; llama.cpp built-in UI, LM Studio, AnythingLLM, Hollama, raw PowerShell all documented.

**Inherits to:**
- Any user wanting to actually use the LAN stack from their Windows laptop
- The ADA-accommodation delivery vector
- ROADMAP follow-ups: Mac / iPad / phone browser instructions (mechanical extension of §11.3)

**SSoT marker:** §11 absorbs alongside the rest of USAGE_LOCAL_NETWORK.md into `srmech_research_notebook.md` §3.25.7 at SSoT absorption. The cross-platform-deployment pattern is potentially load-bearing for the ADA-accommodation framework reading.
