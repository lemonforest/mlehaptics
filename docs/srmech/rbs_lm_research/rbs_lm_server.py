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


class ResponseFormat(BaseModel):
    """OpenAI-API extension: request a specific output rendering format.

    Per R-RBS-LM-26: the cascade outputs the same byte stream either way;
    the post-processor applies a deterministic rendering layer. This is
    NOT a learning operation — it's a presentation operation. Supported:

    - "text" (default) — return raw cascade output as text
    - "braille" — encode as UEB Grade 1 Braille Unicode (U+2800..U+28FF)
    - "signwriting" — RESERVED; requires parallel-corpus encoding (not in
      this partition); currently passes through unchanged with a /health
      declaration noting the reservation

    Format choice does NOT affect the cascade or its 3.3% structural
    ceiling. Per `[[user_stance_ai_is_not_a_substrate]]`: rendering is
    surface, not substrate.
    """
    type: str = Field(default="text",
        description="Output rendering format: text | braille | signwriting")


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = Field(default=20, ge=1, le=512)
    temperature: Optional[float] = 0.0
    stream: Optional[bool] = False
    context_truncation: Optional[int] = Field(default=None, ge=1,
        description="RBS-LM extension: override CONTEXT_WINDOW for the truncation experiment")
    response_format: Optional[ResponseFormat] = Field(default=None,
        description="R-RBS-LM-26 extension: request alternative output rendering")
    long_context_buffer: Optional[str] = Field(default=None,
        description="R-RBS-LM-28 extension: long-context buffer to FFT-graft into the cascade's CONTEXT_WINDOW. Requires byte mode. The cascade sees a 64-byte window whose LOW-FREQ components are taken from this buffer + HIGH-FREQ from the recent prompt bytes.")
    fft_cutoff_freq: Optional[int] = Field(default=8, ge=0, le=32,
        description="R-RBS-LM-28 extension: graft cutoff bin index. 0 = no graft (baseline); higher admits more long-buffer signal. Saturates at W//2.")
    long_context_buffers: Optional[List[str]] = Field(default=None,
        description="R-RBS-LM-32 extension: ordered list of long-context buffers, lowest-freq first. Each buffer claims one frequency band per fft_layered_cutoffs. Use INSTEAD OF long_context_buffer for multi-band layered grafts (e.g., system prompt + conversation history + RAG document).")
    fft_layered_cutoffs: Optional[List[int]] = Field(default=None,
        description="R-RBS-LM-32 extension: monotonically-increasing list of band endpoints, parallel to long_context_buffers. layered_buffer[i] claims bins [fft_layered_cutoffs[i-1], fft_layered_cutoffs[i]); recent fills above the last endpoint.")


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
        "response_formats_supported": {
            "text": "raw cascade output (default)",
            "braille": "UEB Grade 1 English Braille (Unicode U+2800..U+28FF); deterministic; R-RBS-LM-26",
            "asl-gloss": "Slash-wrapped ASL gloss notation; R-RBS-LM-27; requires byte mode + v27-family parallel-corpus-encoded instrument; cascade is prompted with <english>\\x02 and generates gloss until \\x03",
            "signwriting": "RESERVED — Sutton SignWriting Unicode (U+1D800..U+1DAAF); requires direct English↔SignWriting parallel corpus (not the gloss-notation intermediate); encoding deferred",
        },
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

    fmt_type = req.response_format.type if req.response_format else "text"

    # R-RBS-LM-32: Multi-buffer FFT-graft (byte mode only; takes precedence
    # over single-buffer when both are present)
    if req.long_context_buffers:
        if not BYTE_MODE:
            raise HTTPException(
                status_code=400,
                detail="long_context_buffers requires byte mode (RBS_LM_BYTE_MODE=1).",
            )
        if not req.fft_layered_cutoffs:
            raise HTTPException(
                status_code=400,
                detail="long_context_buffers requires fft_layered_cutoffs (parallel list).",
            )
        if len(req.long_context_buffers) != len(req.fft_layered_cutoffs):
            raise HTTPException(
                status_code=400,
                detail=f"long_context_buffers ({len(req.long_context_buffers)}) and "
                       f"fft_layered_cutoffs ({len(req.fft_layered_cutoffs)}) "
                       f"must be parallel lists.",
            )
        if fmt_type == "asl-gloss":
            raise HTTPException(
                status_code=400,
                detail="multi-buffer FFT graft + asl-gloss not yet composed in one request.",
            )
        completion, n_prompt, n_new = _multi_buffer_fft_translate(
            bot, prompt,
            req.long_context_buffers, req.fft_layered_cutoffs,
            max_new_tokens=req.max_tokens,
            context_truncation=req.context_truncation,
        )
        completion = _apply_response_format(completion, req.response_format)
        result_usage = (n_prompt, n_new)
    # R-RBS-LM-28: FFT-graft single long-context buffer (byte mode only)
    elif req.long_context_buffer:
        if not BYTE_MODE:
            raise HTTPException(
                status_code=400,
                detail="long_context_buffer requires byte mode "
                       "(RBS_LM_BYTE_MODE=1); the FFT graft uses the byte vocab table.",
            )
        if fmt_type == "asl-gloss":
            raise HTTPException(
                status_code=400,
                detail="long_context_buffer + asl-gloss not yet composed in one request.",
            )
        completion, n_prompt, n_new = _fft_grafted_translate(
            bot, prompt, req.long_context_buffer,
            cutoff_freq=req.fft_cutoff_freq,
            max_new_tokens=req.max_tokens,
            context_truncation=req.context_truncation,
        )
        completion = _apply_response_format(completion, req.response_format)
        result_usage = (n_prompt, n_new)
    elif fmt_type == "asl-gloss":
        # R-RBS-LM-27 inference protocol: prompt is `<english>\x02`, cascade
        # generates gloss bytes until \x03 or max_tokens. Requires byte mode +
        # a parallel-corpus-encoded instrument (v27 family).
        if not BYTE_MODE:
            raise HTTPException(
                status_code=400,
                detail="asl-gloss response_format requires byte mode "
                       "(RBS_LM_BYTE_MODE=1) and a parallel-corpus-encoded "
                       "instrument (R-RBS-LM-27 v27 family).",
            )
        completion, n_prompt, n_new = _asl_gloss_translate(
            bot, prompt, max_new_tokens=req.max_tokens,
            context_truncation=req.context_truncation,
        )
        result_usage = (n_prompt, n_new)
    else:
        result = bot.respond_with_metadata(
            prompt,
            max_new_tokens=req.max_tokens,
            context_truncation=req.context_truncation,
        )
        completion = _apply_response_format(result["completion"], req.response_format)
        result_usage = (len(result["prompt_token_ids"]), len(result["new_token_ids"]))

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(time.time()),
        model=MODEL_ID,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=completion),
                finish_reason="length",
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=result_usage[0],
            completion_tokens=result_usage[1],
            total_tokens=result_usage[0] + result_usage[1],
        ),
    )


def _multi_buffer_fft_translate(bot, prompt, long_context_buffers,
                                  fft_layered_cutoffs, max_new_tokens=80,
                                  context_truncation=None):
    """R-RBS-LM-32: multi-buffer FFT-graft generation. Each long buffer claims
    one frequency band per the parallel cutoff list.
    """
    from rbs_lm_encoder import CONTEXT_WINDOW, D, bind
    from rbs_lm_bytes import vectorised_cleanup_bytes, bytes_to_text
    from rbs_lm_fft import encode_context_with_multi_buffer_graft

    window = context_truncation if context_truncation is not None else CONTEXT_WINDOW
    prompt_bytes = list(prompt.encode("utf-8"))
    layered_buffer_tokens = [list(b.encode("utf-8")) for b in long_context_buffers]

    tokens = list(prompt_bytes)
    new_bytes = []
    for _ in range(max_new_tokens):
        ctx = tokens[-window:] if len(tokens) > window else tokens
        ctx_vec = encode_context_with_multi_buffer_graft(
            ctx, layered_buffer_tokens, fft_layered_cutoffs,
            bot.vocab_table, D=D,
        )
        cand = bind(bot.instrument, ctx_vec)
        res = vectorised_cleanup_bytes(cand, bot.vocab_table, D, top_k=1)
        nxt = res[0][0]
        new_bytes.append(nxt)
        tokens.append(nxt)

    completion = bytes_to_text(new_bytes)
    return completion, len(prompt_bytes), len(new_bytes)


def _fft_grafted_translate(bot, prompt, long_context_buffer,
                            cutoff_freq=8, max_new_tokens=80,
                            context_truncation=None):
    """R-RBS-LM-28: generate using FFT-grafted context.

    The cascade itself is unchanged — only the encode_context step is
    replaced with encode_context_with_graft, which surgically combines
    LOW-freq of the long_context_buffer with HIGH-freq of the recent window.
    """
    from rbs_lm_encoder import CONTEXT_WINDOW, D, bind
    from rbs_lm_bytes import vectorised_cleanup_bytes, bytes_to_text
    from rbs_lm_fft import encode_context_with_graft

    window = context_truncation if context_truncation is not None else CONTEXT_WINDOW
    prompt_bytes = list(prompt.encode("utf-8"))
    long_buf_bytes = list(long_context_buffer.encode("utf-8"))

    tokens = list(prompt_bytes)
    new_bytes = []
    for _ in range(max_new_tokens):
        ctx = tokens[-window:] if len(tokens) > window else tokens
        ctx_vec = encode_context_with_graft(
            ctx, long_buf_bytes, bot.vocab_table,
            cutoff_freq=cutoff_freq, D=D,
        )
        cand = bind(bot.instrument, ctx_vec)
        res = vectorised_cleanup_bytes(cand, bot.vocab_table, D, top_k=1)
        nxt = res[0][0]
        new_bytes.append(nxt)
        tokens.append(nxt)

    completion = bytes_to_text(new_bytes)
    return completion, len(prompt_bytes), len(new_bytes)


def _asl_gloss_translate(bot, english_prompt, max_new_tokens=80,
                          context_truncation=None):
    """R-RBS-LM-27 inference protocol: <english>\\x02 → cascade → ...\\x03

    Cascade trained on paired English↔ASL-gloss corpus expects this prompt
    format. Generation stops at ETX (0x03) or max_new_tokens.

    Returns (completion_text, n_prompt_bytes, n_new_bytes).
    """
    from rbs_lm_encoder import CONTEXT_WINDOW, D, bind
    from rbs_lm_bytes import encode_context_bytes, vectorised_cleanup_bytes

    SEP, END = 0x02, 0x03
    window = context_truncation if context_truncation is not None else CONTEXT_WINDOW

    prompt_bytes = list(english_prompt.encode("utf-8")) + [SEP]
    tokens = list(prompt_bytes)
    new_bytes = []
    for _ in range(max_new_tokens):
        ctx = tokens[-window:] if len(tokens) > window else tokens
        ctx_vec = encode_context_bytes(ctx, bot.vocab_table, D)
        cand = bind(bot.instrument, ctx_vec)
        res = vectorised_cleanup_bytes(cand, bot.vocab_table, D, top_k=1)
        nxt = res[0][0]
        new_bytes.append(nxt)
        tokens.append(nxt)
        if nxt == END:
            new_bytes = new_bytes[:-1]
            break

    completion = bytes(bytearray(new_bytes)).decode("utf-8", errors="replace")
    return completion, len(prompt_bytes), len(new_bytes)


def _apply_response_format(text, response_format):
    """R-RBS-LM-26: post-process cascade output for visual-render readiness.

    Deterministic rendering layer — does NOT change the cascade, does NOT
    affect the structural ceiling. Format choice is presentation only.
    """
    if response_format is None or response_format.type == "text":
        return text
    if response_format.type == "braille":
        from rbs_lm_braille import english_to_braille
        return english_to_braille(text)
    if response_format.type == "asl-gloss":
        # asl-gloss is INFERENCE-format, not post-process. Routed in
        # chat_completions() via _asl_gloss_translate. If we reach this path,
        # the caller used asl-gloss with byte mode off (which raises 400)
        # or the routing fell through — return a clear declaration.
        return f"[asl-gloss requires byte mode + v27 instrument; routed in chat_completions] {text}"
    if response_format.type == "signwriting":
        # Reserved per R-RBS-LM-26 §3 — requires DIRECT English↔SignWriting
        # parallel corpus (the asl-gloss notation is a separate
        # intermediate format, not raw SignWriting Unicode).
        return f"[signwriting reserved: direct parallel corpus required] {text}"
    raise HTTPException(
        status_code=400,
        detail=f"unsupported response_format.type: {response_format.type!r} "
               f"(supported: text, braille, signwriting)",
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
