r"""R-RBS-LM-SIONASERVER (F726 build) — the Siona /v1: a runnable FastAPI OpenAI-compatible server wrapping
storyteller.infer (via the F689 STORYAPI handler), so CopilotKit / AG2 / any OpenAI client talks to Siona.

The F726 architecture made real: the OpenAI-compatible /v1 surface (= the Siona API). Endpoints:
  POST /v1/chat/completions   — stream AND non-stream (CopilotKit streams by default)
  GET  /v1/models             — the worlds, as `siona:<world>` model ids
  GET  /health

Honest scope: Siona is the GROUNDED demo engine (the MFO world) — it RENDERS for keys it knows
(the_one / chirality / spectrum / …) and ASKS for anything else (the asking-state, F661 — it cannot
hallucinate). So general chitchat returns "I have no tome for X. What is it?". That is the feature.

Run from the WORKTREE ROOT with the rc78 venv (numpy-free; needs fastapi + uvicorn):
  cd <worktree root>
  /tmp/srmech_rc78/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONASERVER_fastapi_openai_v1_wraps_storyteller_infer.py
Binds 0.0.0.0:8000 -> the siona-chat CopilotKit runtime reaches it at http://192.168.44.147:8000/v1.
No abs(); no CAD. Reference scaffold for the srmech dev session (the FastAPI ASGI app F726 called for).
"""
import importlib.util as U
import json
import sys
import time

# Load the F689 STORYAPI handler (the request->infer->OpenAI-shape mapping), backed by storyteller.infer.
sys.path.insert(0, "docs/srmech/rbs_lm_research")
_spec = U.spec_from_file_location(
    "storyapi",
    "docs/srmech/rbs_lm_research/R-RBS-LM-STORYAPI_openai_compatible_endpoint_reference_ag2_copilotkit.py",
)
storyapi = U.module_from_spec(_spec)
_spec.loader.exec_module(storyapi)

from fastapi import FastAPI, Request                       # noqa: E402
from fastapi.middleware.cors import CORSMiddleware         # noqa: E402
from fastapi.responses import JSONResponse, StreamingResponse  # noqa: E402
import uvicorn                                             # noqa: E402

app = FastAPI(title="Siona /v1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "engine": "storyteller.infer", "worlds": list(storyapi.WORLDS)}


@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [{"id": f"siona:{w}", "object": "model", "owned_by": "siona"} for w in storyapi.WORLDS],
    }


@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()
    resp = storyapi.chat_completion(body)  # OpenAI-shaped dict, backed by storyteller.infer (F692)

    if not body.get("stream"):
        return JSONResponse(resp)

    # Streaming: emit the rendered content as OpenAI SSE chunks (CopilotKit's OpenAIAdapter streams).
    content = resp["choices"][0]["message"]["content"] or ""
    created = int(time.time())

    def sse():
        first = {
            "id": resp["id"], "object": "chat.completion.chunk", "created": created, "model": resp["model"],
            "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(first)}\n\n"
        last = {
            "id": resp["id"], "object": "chat.completion.chunk", "created": created, "model": resp["model"],
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(last)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")


if __name__ == "__main__":
    print(f"Siona /v1 -> http://0.0.0.0:8000   worlds={list(storyapi.WORLDS)}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
