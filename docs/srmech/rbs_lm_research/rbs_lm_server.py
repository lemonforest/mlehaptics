"""R-RBS-LM-24 — OpenAI-API-compatible HTTP server for the RBS-LM local expert.

A small FastAPI app exposing the OpenAI Chat Completions v1 API shape so
the existing ecosystem (CopilotKit / AG2 / LangChain / LlamaIndex /
Continue / Cursor / Open WebUI / LiteLLM / DSPy / Pydantic AI / openai
Python SDK / curl / etc.) can talk to our local expert via a standard
`base_url` override. The wire format matches llama.cpp's `llama-server`
OpenAI-compat surface — we are simply another model endpoint.

Per `[[user_stance_ai_is_not_a_substrate]]`: this exposes the local expert
as a *callee*, not a planner. The orchestration logic (multi-agent loops,
RAG retrieval, tool-call routing) lives in the upstream code; we serve
generations only. The `/health` endpoint declares this plainly so any
operator inspecting the surface understands the substrate boundary.

Endpoints:
  GET  /health                     — server status + transducer framing
  GET  /v1/models                  — list available models (RBS-LM Path C variants)
  POST /v1/chat/completions        — OpenAI-shape chat completion (non-streaming)

Localhost-only by default. No auth / persistence / rate-limiting; those are
scope creep for framework research. If you need them, put nginx in front
or deploy with `--host 0.0.0.0` only behind a trusted reverse proxy.

Usage:
    # Server side
    uvicorn rbs_lm_server:app --host 127.0.0.1 --port 8788

    # Client side (any OpenAI-API tool)
    from openai import OpenAI
    client = OpenAI(base_url="http://127.0.0.1:8788/v1", api_key="not-needed")
    resp = client.chat.completions.create(
        model="rbs-lm-v18",
        messages=[{"role": "user", "content": "The morning sun"}],
        max_tokens=20,
    )
    print(resp.choices[0].message.content)
"""

import os
import sys
import time
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))


DEFAULT_INSTRUMENT = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v18.bin"
INSTRUMENT_PATH = os.environ.get("RBS_LM_INSTRUMENT", DEFAULT_INSTRUMENT)
MODEL_ID = os.environ.get("RBS_LM_MODEL_ID", "rbs-lm-v18-path-c")
BYTE_MODE = os.environ.get("RBS_LM_BYTE_MODE", "0") == "1"


_bot = None
_load_t = None


def _get_bot():
    """Lazy-load the chatbot on first request. Idempotent.

    BYTE_MODE selects RBSChatbotBytes (R-RBS-LM-25; UTF-8 tokenization;
    256-byte vocab; no GPT-2 dependency) vs RBSChatbot (R-RBS-LM-17 Path C;
    GPT-2 BPE; WTE projected vocab). The OpenAI-API surface is identical
    either way.
    """
    global _bot, _load_t
    if _bot is None:
        t0 = time.time()
        if BYTE_MODE:
            from rbs_lm_chatbot import RBSChatbotBytes
            _bot = RBSChatbotBytes.load(instrument_path=INSTRUMENT_PATH, verbose=False)
        else:
            from rbs_lm_chatbot import RBSChatbot
            _bot = RBSChatbot.load(instrument_path=INSTRUMENT_PATH, use_path_c=True,
                                   verbose=False)
        _load_t = time.time() - t0
    return _bot


# ---- OpenAI-API request/response models (subset; non-streaming) ---------

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = Field(default=20, ge=1, le=512)
    temperature: Optional[float] = 0.0
    stream: Optional[bool] = False
    context_truncation: Optional[int] = Field(default=None, ge=1,
        description="RBS-LM extension: override CONTEXT_WINDOW for the truncation experiment")


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


# ---- FastAPI app --------------------------------------------------------

app = FastAPI(
    title="RBS-LM OpenAI-API server",
    description=(
        "OpenAI-API-compatible HTTP shim around the RBS-LM Path C inference "
        "cascade. Per [[user_stance_ai_is_not_a_substrate]], this endpoint "
        "exposes the local expert as a transducer callee — orchestration "
        "logic lives in the calling code, not here."
    ),
    version="0.1.0",
)


@app.get("/health")
def health():
    """Server status + transducer framing.

    Returns enough info for any operator to confirm: (a) the server is up,
    (b) the instrument is loaded, (c) what the substrate boundary IS.
    """
    return {
        "status": "ok",
        "instrument_path": INSTRUMENT_PATH,
        "instrument_loaded": _bot is not None,
        "load_time_seconds": _load_t,
        "model_id": MODEL_ID,
        "tokenization": "utf-8 bytes (V=256; no BPE)" if BYTE_MODE else "GPT-2 BPE (V=50,257)",
        "byte_mode": BYTE_MODE,
        "framework_reading": (
            "This server exposes a transducer (RBS-LM inference cascade) "
            "as an OpenAI-API endpoint. Per [[user_stance_ai_is_not_a_substrate]]: "
            "this is a puppet playing the roll. Orchestration logic lives in "
            "the calling code. The 3.3%-style token-agreement ceiling "
            "characterized in R-RBS-LM-18 is structural — driven by the "
            "continuous rotation that multi-head attention performs and the "
            "discrete bind/bundle cascade cannot replicate (R-RBS-LM-19 "
            "falsification)."
            + (" Byte-level mode (R-RBS-LM-25 Path D) strips BPE tokenization "
               "from any source model — language-agnostic; zero GPT-2 "
               "dependency at serve time." if BYTE_MODE else "")
        ),
        "hardware": "2009 Xeon E5530; ~180 ms/tok at D=8192",
    }


@app.get("/v1/models")
def list_models():
    """OpenAI-compatible models list. Single entry: the loaded RBS-LM instrument."""
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_ID,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "rbs-lm-research",
                "permission": [],
            }
        ],
    }


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
def chat_completions(req: ChatCompletionRequest):
    """OpenAI-compatible chat completion endpoint.

    Stateless per request (no conversation memory beyond the messages array).
    The messages array is flattened to a single prompt via role-prefixed
    concatenation (the GPT-2-style tokeniser was never trained on chat-format
    tokens, so this is the most honest mapping).
    """
    if req.stream:
        raise HTTPException(
            status_code=501,
            detail="Streaming not yet implemented. Set stream=false.",
        )

    bot = _get_bot()
    prompt = _flatten_messages(req.messages)

    result = bot.respond_with_metadata(
        prompt,
        max_new_tokens=req.max_tokens,
        context_truncation=req.context_truncation,
    )

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(time.time()),
        model=MODEL_ID,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=result["completion"]),
                finish_reason="length",
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=len(result["prompt_token_ids"]),
            completion_tokens=len(result["new_token_ids"]),
            total_tokens=len(result["prompt_token_ids"]) + len(result["new_token_ids"]),
        ),
    )


def _flatten_messages(messages: List[ChatMessage]) -> str:
    """Flatten a chat-format messages array to a single prompt string.

    GPT-2 was pretrained on web text, not chat-format. Two cases:

    - Single user message: use content directly (the prompt is web-text-shaped;
      this matches how llama.cpp serves base models without chat templates).
    - Multi-turn: role-prefix each message + trailing 'assistant:' for
      continuation. The Path C cascade will be more off-distribution here
      because chat-format tokens are novel; behavior reflects R-RBS-LM-18
      3.3%-style ceiling with extra noise from the chat-format drag.
    """
    if len(messages) == 1 and messages[0].role == "user":
        return messages[0].content
    parts = []
    for m in messages:
        parts.append(f"{m.role}: {m.content}")
    parts.append("assistant:")
    return "\n".join(parts)


if __name__ == "__main__":
    # Direct-run convenience: `python rbs_lm_server.py`
    import uvicorn
    host = os.environ.get("RBS_LM_HOST", "127.0.0.1")
    port = int(os.environ.get("RBS_LM_PORT", "8788"))
    print(f"Starting RBS-LM OpenAI-API server on http://{host}:{port}")
    print(f"  instrument: {INSTRUMENT_PATH}")
    print(f"  model_id:   {MODEL_ID}")
    uvicorn.run(app, host=host, port=port, log_level="info")
