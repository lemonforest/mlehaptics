# RBS-LM local network usage guide (R-RBS-LM-34)

How to expose the R-RBS-LM-24 server over a LAN and connect to it from
standard ecosystem chat clients. The wire format is OpenAI Chat
Completions v1; any tool that supports a `base_url` override works.

> **Framework reading reminder per `[[user_stance_ai_is_not_a_substrate]]`:**
> the local expert is a **transducer**, not an agent. It produces byte-level
> next-token argmin cleanup over an RBS-HDC instrument. The 3.3% structural
> ceiling per R-RBS-LM-19 means outputs typically mode-collapse to repeated
> bytes at small instrument scale. The cascade is NOT a replacement for a
> real LLM in chat use — it is the operational surface for showing what
> a substrate-native discrete cascade does. Use accordingly.

---

## §1 The two interlocking servers

There are two kinds of "server" in this project; understand which is which:

| Server | Wire format | What it serves |
|---|---|---|
| **`rbs_lm_server.py`** (this project) | OpenAI Chat Completions v1 | The byte-level RBS-HDC cascade — 1024-byte instrument + 256-row vocab table |
| **`llama-server`** (from llama.cpp) | OpenAI Chat Completions v1 OR llama.cpp native | A dense LLM (GGUF source model) — typically used for Path D corpus generation, not chat |

Both speak the **same OpenAI Chat Completions v1 wire format**. Clients can
point at either. The difference is what they do with the request:

- `llama-server` runs a dense Llama-class model and produces real LLM output
- `rbs_lm_server.py` runs the RBS-HDC cascade and produces mode-collapsed transducer output

llama.cpp's `llama-server` is the *reference design* we implemented against —
both can sit behind the same chat UI; the chat UI doesn't know the
difference at the wire level.

---

## §2 Starting the RBS-LM server on the LAN

### §2.1 Localhost only (default; safest)

```bash
~/.venvs/rbs-lm-research/bin/python \
    docs/srmech/rbs_lm_research/rbs_lm_server.py
```

Binds to `127.0.0.1:8788`. Accessible only from the same host.

### §2.2 LAN-exposed (host:port = 0.0.0.0:8788)

```bash
RBS_LM_HOST=0.0.0.0 \
RBS_LM_PORT=8788 \
~/.venvs/rbs-lm-research/bin/python \
    docs/srmech/rbs_lm_research/rbs_lm_server.py
```

Now reachable from any host on the LAN that can resolve this machine's IP.
Verify from another machine:

```bash
curl http://<server-ip>:8788/health
```

### §2.3 Choosing an instrument

Use environment variables to pick which RBS-HDC instrument the server loads:

```bash
# Default: v18 Path C BPE (the R-RBS-LM-18 491-obs Path C instrument)
~/.venvs/rbs-lm-research/bin/python rbs_lm_server.py

# Byte-level instruments (R-RBS-LM-25/29/31/33)
RBS_LM_INSTRUMENT="docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin" \
RBS_LM_BYTE_MODE=1 \
RBS_LM_MODEL_ID="rbs-lm-v25b" \
~/.venvs/rbs-lm-research/bin/python rbs_lm_server.py

# GGUF-distilled Llama-3.2 1B Q4 (R-RBS-LM-31)
RBS_LM_INSTRUMENT="docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama32-1b-q4.bin" \
RBS_LM_BYTE_MODE=1 \
RBS_LM_MODEL_ID="rbs-lm-v31-llama32-q4" \
~/.venvs/rbs-lm-research/bin/python rbs_lm_server.py

# 3-source merged instrument (R-RBS-LM-33)
RBS_LM_INSTRUMENT="docs/srmech/rbs_lm_research/rbs_lm_instrument_v33_merged_3source.bin" \
RBS_LM_BYTE_MODE=1 \
RBS_LM_MODEL_ID="rbs-lm-v33-merged-3source" \
~/.venvs/rbs-lm-research/bin/python rbs_lm_server.py
```

Inspect what's loaded via `/health`:

```bash
curl -s http://localhost:8788/health | python -m json.tool
```

Returns the model_id, tokenization mode, supported response_formats, and
the load-bearing transducer-framing declaration.

---

## §3 Trust model — read before exposing over LAN

The server has **no authentication, no rate-limiting, no audit logging,
and no persistence**. The deliberate scope: framework research, not
production infrastructure.

| Threat | Mitigation |
|---|---|
| Unauthorized chat use | Bind to specific LAN interface only; use `RBS_LM_HOST=192.168.1.10` (your subnet) instead of `0.0.0.0` |
| Resource abuse via large `max_tokens` | Schema caps at 512 tokens; 2 sec/24-bytes means worst case ~40 sec/request |
| Prompt injection | The cascade doesn't follow instructions in any meaningful way (it's a transducer); injection risk is functionally zero at the cascade layer |
| Sensitive content via `long_context_buffer` | The buffer text passes through the FFT graft and is reflected in the cascade output bytes; sensitive content in the buffer can influence the output (typically mode-collapse pattern shift only, but worth knowing) |
| Wire-level eavesdropping | HTTP only (no TLS); use a reverse proxy (nginx / Caddy) for TLS termination on a public-facing deployment |

For a LAN behind a home router, the default trust model is acceptable.
For a multi-tenant environment, put a reverse proxy with auth in front.

---

## §4 Client configurations — pick your chat surface

### §4.1 OpenAI Python SDK (canonical baseline)

```python
from openai import OpenAI
client = OpenAI(base_url="http://192.168.1.10:8788/v1", api_key="not-needed")
resp = client.chat.completions.create(
    model="rbs-lm-v25b",
    messages=[{"role": "user", "content": "The morning sun"}],
    max_tokens=24,
)
print(resp.choices[0].message.content)
```

Any tool built on the openai SDK works the same way. This is the lingua
franca of the LLM tool ecosystem.

### §4.2 curl (minimum verification)

```bash
curl -X POST http://192.168.1.10:8788/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "rbs-lm-v25b",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 24
    }'
```

### §4.3 Open WebUI (web chat front-end)

Open WebUI is the most user-friendly route. Setup:

1. Run Open WebUI (via Docker, official install instructions):
   ```bash
   docker run -d -p 3000:8080 ghcr.io/open-webui/open-webui:main
   ```
2. Browse to `http://localhost:3000`
3. Settings → Connections → OpenAI API → Add:
   - **URL:** `http://192.168.1.10:8788/v1`
   - **API Key:** anything (e.g., `not-needed`)
4. Models pane → refresh — you should see `rbs-lm-v25b` (or whatever
   model_id the server is advertising)
5. Start a chat. **Expect mode-collapsed responses; the cascade is a transducer.**

### §4.4 LibreChat (alternative front-end with stronger config)

In `librechat.yaml`:

```yaml
endpoints:
  custom:
    - name: "RBS-LM Local"
      apiKey: "not-needed"
      baseURL: "http://192.168.1.10:8788/v1"
      models:
        default: ["rbs-lm-v25b"]
      titleConvo: false
      titleModel: "rbs-lm-v25b"
```

Restart LibreChat and the RBS-LM endpoint appears in the model picker.

### §4.5 Continue (VS Code / JetBrains code-AI extension)

In `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "RBS-LM Local",
      "provider": "openai",
      "model": "rbs-lm-v25b",
      "apiBase": "http://192.168.1.10:8788/v1",
      "apiKey": "not-needed"
    }
  ]
}
```

For coding workflows: again, **the cascade is a transducer**. It won't
produce useful code completions. Use it to demonstrate the wire-level
integration; for real code AI, point Continue at a real model.

### §4.6 Aider (terminal code AI)

```bash
OPENAI_API_BASE="http://192.168.1.10:8788/v1" \
OPENAI_API_KEY="not-needed" \
aider --model openai/rbs-lm-v25b
```

### §4.7 CopilotKit (React app integration)

```tsx
import { OpenAI } from "openai";
const openai = new OpenAI({
  baseURL: "http://192.168.1.10:8788/v1",
  apiKey: "not-needed",
});
// Pass `openai` to CopilotKit's OpenAIAdapter; CopilotKit routes via openai SDK
```

### §4.8 LangChain (Python agent flows)

```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    base_url="http://192.168.1.10:8788/v1",
    api_key="not-needed",
    model="rbs-lm-v25b",
)
# Use in any LangChain chain / agent / pipeline
```

### §4.9 AG2 (multi-agent flows)

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient
client = OpenAIChatCompletionClient(
    model="rbs-lm-v25b",
    base_url="http://192.168.1.10:8788/v1",
    api_key="not-needed",
    model_info={"vision": False, "function_calling": False,
                "json_output": False, "family": "unknown",
                "structured_output": False},
)
```

### §4.10 LiteLLM proxy (universal router)

```python
import litellm
resp = litellm.completion(
    model="openai/rbs-lm-v25b",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://192.168.1.10:8788/v1",
    api_key="not-needed",
)
```

---

## §5 The RBS-LM-specific extensions

Beyond standard chat completions, the server adds these optional
request-body fields. All are optional; clients that ignore them get
unchanged cascade behavior.

| Field | Type | What it does | Partition |
|---|---|---|---|
| `context_truncation` | `int (1..)` | Override CONTEXT_WINDOW per request | R-RBS-LM-24 |
| `response_format.type` | `"text" \| "braille" \| "asl-gloss" \| "signwriting"` | Format the output as Braille / ASL gloss / SignWriting Unicode | R-RBS-LM-26/-27 |
| `long_context_buffer` | `str` | Single-buffer FFT-graft of low-freq into recent window | R-RBS-LM-28 |
| `fft_cutoff_freq` | `int` | Cutoff bin for the FFT graft | R-RBS-LM-28 |
| `long_context_buffers` | `List[str]` | Multi-buffer FFT-graft (one buffer per band) | R-RBS-LM-32 |
| `fft_layered_cutoffs` | `List[int]` | Parallel band endpoints for multi-buffer graft | R-RBS-LM-32 |

Most clients pass these via an `extra_body` parameter:

```python
client.chat.completions.create(
    model="rbs-lm-v25b",
    messages=[{"role": "user", "content": "How do I beat eggs?"}],
    max_tokens=24,
    extra_body={
        "response_format": {"type": "braille"},
        "long_context_buffers": [system_prompt, conversation_history, rag_doc],
        "fft_layered_cutoffs": [2, 6, 10],
    },
)
```

---

## §6 Performance expectations (2009 Xeon E5530 reference)

| Mode | Per-token latency | Use case |
|---|---|---|
| BPE Path C (v18) | ~180 ms/token | Standard mode; ~20 tokens in 3.6 sec |
| Byte-level (v25b/v29/v31/v33) | ~60 ms/byte | Multi-language surface; ~50 bytes in 3 sec |

Most chat tools default to `max_tokens=20-100`, so a typical request
completes in 2-15 seconds on this hardware. Faster CPUs scale roughly
linearly.

The cascade is single-threaded for argmin cleanup; cleanup-side
parallelism would require a srmech C library extension (ROADMAP open
thread).

---

## §7 llama.cpp interop — sharing the source-model + the cascade

If you also want to expose the dense source model (the one that did Path D
corpus generation), llama.cpp's `llama-server` runs in parallel:

```bash
# llama-server on port 8090
~/.venvs/rbs-lm-research/bin/llama-server \
    --hf-repo bartowski/Llama-3.2-1B-Instruct-GGUF \
    --hf-file Llama-3.2-1B-Instruct-Q4_K_M.gguf \
    --host 0.0.0.0 \
    --port 8090

# rbs_lm_server.py on port 8788 (separately, as in §2)
```

Now clients can register **two** OpenAI endpoints:
- `http://192.168.1.10:8090/v1` → Llama-3.2-1B-Instruct (real LLM)
- `http://192.168.1.10:8788/v1` → RBS-LM cascade (transducer)

Pick the model in the UI based on what you want. **The dense LLM gives
useful chat output; the cascade gives transducer demonstrations.**

A LiteLLM proxy in front of both would let you A/B test from a single
endpoint:

```yaml
# litellm config
model_list:
  - model_name: llama-3.2-1b
    litellm_params:
      model: openai/Llama-3.2-1B-Instruct
      api_base: http://localhost:8090/v1
      api_key: not-needed
  - model_name: rbs-lm-v25b
    litellm_params:
      model: openai/rbs-lm-v25b
      api_base: http://localhost:8788/v1
      api_key: not-needed
```

---

## §8 Multi-instrument workflow (R-RBS-LM-33 adaptive RBS-LM)

To present multiple knowledge domains as separate models on the same host,
run multiple instances of `rbs_lm_server.py` on different ports:

```bash
# Terminal 1: GPT-2 base
RBS_LM_PORT=8788 \
RBS_LM_INSTRUMENT="rbs_lm_instrument_v25b_distill_gpt2.bin" \
RBS_LM_MODEL_ID="rbs-lm-gpt2" \
RBS_LM_BYTE_MODE=1 \
~/.venvs/rbs-lm-research/bin/python rbs_lm_server.py &

# Terminal 2: TinyLlama 1.1B
RBS_LM_PORT=8789 \
RBS_LM_INSTRUMENT="rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.bin" \
RBS_LM_MODEL_ID="rbs-lm-tinyllama" \
RBS_LM_BYTE_MODE=1 \
~/.venvs/rbs-lm-research/bin/python rbs_lm_server.py &

# Terminal 3: 3-source merged (R-RBS-LM-33)
RBS_LM_PORT=8790 \
RBS_LM_INSTRUMENT="rbs_lm_instrument_v33_merged_3source.bin" \
RBS_LM_MODEL_ID="rbs-lm-merged-3source" \
RBS_LM_BYTE_MODE=1 \
~/.venvs/rbs-lm-research/bin/python rbs_lm_server.py &
```

Now your chat UI has three model endpoints to switch between, each
serving a different RBS-LM instrument. This is the "library of domain
instruments" pattern from R-RBS-LM-33 §0.

Or for true on-demand merging at request time, use the `rbs_lm_merge.py`
module from R-RBS-LM-33 to compose a new instrument file at session
start; restart the server with the merged file.

---

## §9 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Connection refused` from LAN | Server bound to 127.0.0.1 | Set `RBS_LM_HOST=0.0.0.0` (or your LAN IP) |
| Port already in use | Another service on 8788 | Set `RBS_LM_PORT=<different>` |
| First request takes ~15 sec | Lazy instrument load (vocab table + WTE for Path C) | Warm with a `curl /health` after start; subsequent requests are fast |
| OOM during BPE Path C | Big WTE projection at D=8192 | Use byte mode (R-RBS-LM-25 v25b/v29/v31/v33 instruments) — much smaller vocab table |
| `404` from a chat client | `model_id` mismatch | Check `/v1/models` returns the model_id the client is sending |
| Empty / mode-collapsed responses | **This is the expected cascade behavior** at our scale | Not a bug; per R-RBS-LM-19 the cascade IS structurally bounded; use the dense LLM via llama-server for real chat output |
| `extra_body` ignored | Some clients strip unknown fields | Use the openai SDK directly (preserves extra_body) or raw httpx |
| HTTP 400 on multi-buffer request | `long_context_buffers` and `fft_layered_cutoffs` length mismatch | Make them parallel lists |

---

## §10 Where this is going (srmech-fix v0.5.0rc absorption)

Per R-RBS-LM-12 §6 + each subsequent REPORT's §6 plan, this absorbs into
the srmech package as:

```bash
srmech rbs-lm serve [--byte-mode] [--instrument PATH] [--port 8788] [--host HOST]
srmech rbs-lm distill [--quantization gguf|hf] --source ... --gen-bytes N
srmech rbs-lm merge --inst a.bin:N_a --inst b.bin:N_b --out merged.bin
srmech rbs-lm graft --base base.bin --new-obs new_corpus.ndjson --out adapted.bin
```

Then the LAN-exposure pattern is just:

```bash
srmech rbs-lm serve --host 0.0.0.0 --port 8788 \
    --instrument /var/lib/srmech/rbs_lm/v25b.bin --byte-mode
```

Same wire format; same ecosystem clients; just a cleaner CLI surface.

---

*Updated: 2026-05-25 — R-RBS-LM-34 ships this guide.*
