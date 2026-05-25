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

## §11 Worked example — Windows browser front-end for llama.cpp + RBS-LM over LAN

Per user direction 2026-05-25: end-to-end concrete walkthrough for the
common case — a Linux server on the LAN hosts BOTH `llama-server` (real
LLM via llama.cpp) AND `rbs_lm_server.py` (RBS-LM cascade); a Windows
machine on the same LAN runs a browser-based chat UI that can switch
between them.

This section is the "I want to use the actual stack from a browser on my
Windows box" guide.

### §11.1 Topology

```
  ┌─────────────────────────────────┐         ┌──────────────────────────┐
  │ Linux server  (192.168.1.10)    │         │ Windows machine          │
  │                                 │         │                          │
  │ • llama-server  :8090           │ ─LAN─►  │  Browser                 │
  │   (Llama-3.1-8B Q4 GGUF)        │         │   ↓                      │
  │ • rbs_lm_server :8788           │ ─LAN─►  │   http://192.168.1.10:3000 │
  │   (byte-mode v25b instrument)   │         │   (Open WebUI)            │
  │ • Open WebUI    :3000  (Docker) │         │                          │
  └─────────────────────────────────┘         └──────────────────────────┘
```

Three services on the Linux box, all reachable from any browser on the
LAN. Pick a model in Open WebUI → it routes to either llama-server (real
LLM) or rbs_lm_server (cascade transducer).

### §11.2 Step-by-step on the Linux server

#### Step 1: find the Linux box's LAN IP

```bash
hostname -I
# → 192.168.1.10 192.168.1.10
# (first IP is the LAN address; second is often the same if single-NIC)

# Alternative
ip -4 addr show | grep -oP 'inet \K[\d.]+' | grep -v '127.0'
```

Note the IP — Windows clients connect to it.

#### Step 2: open firewall ports

If using `ufw`:

```bash
sudo ufw allow 8090/tcp comment 'llama-server (llama.cpp)'
sudo ufw allow 8788/tcp comment 'rbs_lm_server (RBS-LM cascade)'
sudo ufw allow 3000/tcp comment 'Open WebUI'
sudo ufw status
```

If using `firewalld`:

```bash
sudo firewall-cmd --add-port=8090/tcp --permanent
sudo firewall-cmd --add-port=8788/tcp --permanent
sudo firewall-cmd --add-port=3000/tcp --permanent
sudo firewall-cmd --reload
```

#### Step 3: start `llama-server` (real LLM via llama.cpp)

llama-cpp-python (R-RBS-LM-31) does NOT ship the `llama-server` binary;
that comes from the C++ llama.cpp project. Install separately or use the
ready-built Python wrapper:

```bash
# Option A: use llama-cpp-python's bundled server CLI
~/.venvs/rbs-lm-research/bin/python -m llama_cpp.server \
    --model_alias Llama-3.1-8B-Instruct-Q4 \
    --hf_pretrained_model_name_or_path bartowski/Meta-Llama-3.1-8B-Instruct-GGUF \
    --hf_model_repo_id bartowski/Meta-Llama-3.1-8B-Instruct-GGUF \
    --port 8090 \
    --host 0.0.0.0 &

# Option B: native llama.cpp llama-server binary (if installed)
~/llama.cpp/build/bin/llama-server \
    --hf-repo bartowski/Meta-Llama-3.1-8B-Instruct-GGUF \
    --hf-file Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
    --host 0.0.0.0 \
    --port 8090 \
    --threads 16 \
    --ctx-size 4096 &
```

Verify it's up:

```bash
curl http://192.168.1.10:8090/v1/models
# → {"object": "list", "data": [{"id": "Llama-3.1-8B-Instruct-Q4", ...}]}
```

llama-server's built-in browser UI is also at `http://192.168.1.10:8090/`
if you want the llama.cpp-shipped front-end specifically (zero install
beyond llama-server itself).

#### Step 4: start `rbs_lm_server.py` (RBS-LM cascade)

```bash
cd ~/GitHub/mlehaptics  # or wherever the worktree lives
RBS_LM_HOST=0.0.0.0 \
RBS_LM_PORT=8788 \
RBS_LM_INSTRUMENT="docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin" \
RBS_LM_BYTE_MODE=1 \
RBS_LM_MODEL_ID="rbs-lm-v25b" \
~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/rbs_lm_server.py &
```

Verify:

```bash
curl http://192.168.1.10:8788/health | python3 -m json.tool
```

#### Step 5: start Open WebUI via Docker

If Docker is installed on Linux:

```bash
docker run -d \
    -p 3000:8080 \
    --add-host=host.docker.internal:host-gateway \
    -v open-webui:/app/backend/data \
    --name open-webui \
    --restart always \
    ghcr.io/open-webui/open-webui:main
```

The `--add-host=host.docker.internal:host-gateway` makes the host's
loopback (the place where llama-server + rbs_lm_server listen on
127.0.0.1 OR the LAN IP) reachable from inside the container.

If Docker is NOT installed on Linux but IS on Windows, see §11.4 below
for the Windows-side-Docker option.

#### Step 6: confirm everything is reachable

From the Linux box:

```bash
curl -s http://localhost:8090/v1/models | python3 -m json.tool
curl -s http://localhost:8788/v1/models | python3 -m json.tool
curl -sI http://localhost:3000 | head -1  # → HTTP/1.1 200 OK from Open WebUI
```

### §11.3 Step-by-step on the Windows machine

#### Step 1: verify LAN connectivity

Open PowerShell or Command Prompt:

```powershell
ping 192.168.1.10
```

Should respond. If not, troubleshoot LAN routing (both machines on same
subnet; firewall on Linux side allowed the ports).

#### Step 2: open the Open WebUI URL in any modern browser

```
http://192.168.1.10:3000
```

Edge / Chrome / Firefox all work. First-time setup creates a local
account on the Open WebUI instance (the account lives in Open WebUI's
Docker volume on the Linux box).

#### Step 3: register the two OpenAI endpoints

In Open WebUI:

1. Click profile icon (top-right) → **Settings** → **Admin Settings**
2. **Connections** → **OpenAI API**
3. Add connection #1:
   - **URL:** `http://192.168.1.10:8090/v1`
   - **API Key:** `not-needed`
   - Save
4. Add connection #2:
   - **URL:** `http://192.168.1.10:8788/v1`
   - **API Key:** `not-needed`
   - Save
5. **Models** pane → refresh — both `Llama-3.1-8B-Instruct-Q4` and
   `rbs-lm-v25b` should appear

#### Step 4: chat

Top of the chat page, click the model selector. Pick:

- **`Llama-3.1-8B-Instruct-Q4`** — get real LLM responses (slow on 2009
  Xeon E5530 at ~3-5 tok/sec; ~30-60 sec per ~100-token response)
- **`rbs-lm-v25b`** — get RBS-LM cascade output (~60 ms/byte; mode-collapsed
  per the structural ceiling)

Same chat history is preserved across model switches. The framework
reading: **both are wire-compatible; behavioral difference is the
cascade ceiling per R-RBS-LM-19**.

### §11.4 Alternative — Open WebUI runs on Windows (no Docker on Linux)

If your Linux server can't run Docker but your Windows machine can:

1. Install Docker Desktop on Windows
2. Run Open WebUI on Windows:

```powershell
docker run -d `
    -p 3000:8080 `
    -v open-webui:/app/backend/data `
    --name open-webui `
    --restart always `
    ghcr.io/open-webui/open-webui:main
```

3. Open browser at `http://localhost:3000` (now LOCAL on Windows)
4. Configure the two OpenAI endpoints pointing to Linux:
   - `http://192.168.1.10:8090/v1` (llama-server)
   - `http://192.168.1.10:8788/v1` (rbs_lm_server)

This trades "Docker-on-Linux" for "Docker-on-Windows" but the integration
is otherwise identical.

### §11.5 Minimum-friction alternative — llama.cpp's built-in web UI

If you only want llama-server's responses (no RBS-LM, no Open WebUI):

1. Start `llama-server` per §11.2 step 3
2. From Windows browser, open `http://192.168.1.10:8090/`
3. The llama.cpp shipped front-end loads — type in the chat box

This works without Docker, without Open WebUI, without any other moving
parts. It's the simplest "browser on Windows talking to LLM on Linux"
setup possible. **Limitation: this UI does NOT see the rbs_lm_server.py
endpoint**; it's llama-server-only. Use Open WebUI (§11.3) if you want
both models in one UI.

### §11.6 Other Windows-friendly clients (no browser)

If a browser-based UI is overkill:

- **LM Studio** (Windows desktop app): Settings → "Local Server" → add
  endpoint URL → chat in the GUI. Supports OpenAI API endpoints.
- **AnythingLLM Desktop** (Windows installer): supports custom OpenAI
  endpoints in Settings → LLM Selection.
- **Hollama** (PWA / single-page): https://hollama.fernando.is — pure
  HTML/JS; just point at your endpoint URL.
- **PowerShell** with `curl`:
  ```powershell
  $body = '{"model":"rbs-lm-v25b","messages":[{"role":"user","content":"Hello"}],"max_tokens":24}'
  curl http://192.168.1.10:8788/v1/chat/completions `
       -H "Content-Type: application/json" `
       -d $body
  ```

### §11.7 Multi-instrument switching from the chat UI

If you've followed R-RBS-LM-33's "library of domain instruments" pattern
(running multiple `rbs_lm_server.py` instances on different ports per
§8 above), Open WebUI will surface ALL of them as separate models if you
register each port as its own OpenAI endpoint. **Switch domains by
switching models in the dropdown.** Useful for testing:

```
  rbs-lm-v25b-gpt2-base       (port 8788; GPT-2 124M distilled)
  rbs-lm-v31-llama-base       (port 8789; Llama 3.2 1B Q4)
  rbs-lm-v33-merged           (port 8790; 3-source merge)
  Llama-3.1-8B-Instruct-Q4    (port 8090; real LLM via llama-server)
```

Four models; one UI; one click between them.

### §11.8 What to expect (honest performance reminders)

On 2009 Xeon E5530 hardware:

- `llama-server` Llama 3.1 8B Q4: ~3-5 tok/sec → ~20-30 sec for a
  100-token response
- `rbs_lm_server.py` byte-mode: ~60 ms/byte → ~3 sec for a 50-byte response
- Open WebUI UI overhead: negligible (~50 ms per request); responses
  stream as the model produces them

If the cascade output mode-collapses to single bytes (`'                    '`
or `'eeeeeee'`), that's expected behavior per R-RBS-LM-19. **Switch to the
llama-server model in the same chat for real LLM output.** The cascade
is a transducer demonstration; not a chat replacement.

### §11.9 Security reminder

- All three services on the Linux box have **no authentication** by
  design (research scope).
- Anyone on your LAN can reach them once firewall ports are open.
- For multi-tenant or internet-exposed deployments: put nginx / Caddy
  with auth in front; do NOT expose these directly to the public
  internet.

---

*Updated: 2026-05-25 — R-RBS-LM-34 ships this guide; §11 added by R-RBS-LM-36 (Windows browser walkthrough).*
