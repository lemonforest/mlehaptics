r"""R-RBS-LM-SIONAHTTP (#231/F1234) — the Siona /v1 BACKEND for the CopilotKit `siona-chat` app: serve
`siona.infer.Session.turn()` over an OpenAI-compatible /v1, with the #231 directed Class-L corpus store + the
ETAK WALK wired into the read path.

This is the BACKEND (default 0.0.0.0:8000). The real UI is the CopilotKit React chat at ~/general/siona-chat
(port 3000), whose /api/copilotkit route (OpenAIAdapter, STREAMING) points at http://<host>:8000/v1 — so this
server MUST speak streaming /v1/chat/completions, which it does. Endpoints:
  POST /v1/chat/completions  -> OpenAI chat-completions, STREAM (SSE) + non-stream (the CopilotKit OpenAIAdapter path)
  POST /v1/responses         -> the newer OpenAI Responses API (typed-event SSE), for CopilotKit react-core v2
  GET  /v1/models            -> the worlds, as siona:<world> ids
  GET  /                     -> a minimal stdlib chat page (fallback if you don't run the CopilotKit app)
  GET  /chat?q=...           -> {"intent","tag","text"} (easy to curl)
  GET  /health , /status     -> engine + corpus state

The corpus is DEMAND-LOADED (F1235: mmap reads/ layer -> ~1 s open), so we load it synchronously before serving
(no sub-second startup race). `define` routes through the etak RIDE (corpus_store.etak_walk) — navigate the directed
store by moving the reference frame, following the charge (chirality = which-way). ThreadingHTTPServer so a held SSE
stream never blocks other requests. Binds 0.0.0.0:8000 (LAN, NO auth — trusted network only).

srmech 0.9.0rc253. Run the pair:
  # backend (this):
  SIONA_CORPUS=~/corpora/wikipedia/simplewiki_directed.genome \
    /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONAHTTP_...py
  # UI:  cd ~/general/siona-chat && npm run dev    (opens http://<host>:3000/)
"""
import http.server
import json
import os
import socketserver
import sys
import threading
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "siona"))

from siona.infer import Session

CORPUS = os.environ.get("SIONA_CORPUS", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_directed.genome"))
HOST = os.environ.get("SIONA_HOST", "0.0.0.0")
PORT = int(os.environ.get("SIONA_PORT", "8000"))                  # backend port (the CopilotKit UI is 3000)
WORLDS = ["siona:MFO", "siona:corpus"]

_session = Session()
_lock = threading.Lock()                                         # guard the single Session across threaded requests
_state = {"corpus": "none", "vocab": 0, "load_s": None, "t0": time.time()}


def _load_corpus():
    p = Path(os.path.expanduser(CORPUS))
    if not p.exists():
        _state["corpus"] = "MISSING: %s" % p
        print("  [corpus] MISSING %s -- define falls back to tool-grounding" % p, flush=True)
        return
    t0 = time.time()
    nv = _session.load_corpus(p)                                 # demand-load: ~1 s (mmap reads/), F1235
    _state.update(corpus=p.name, vocab=nv, load_s=round(time.time() - t0, 2))
    print("  [corpus] %s: %d vocab, demand-loaded in %.2fs (etak walk live)" % (p.name, nv, _state["load_s"]), flush=True)


def _reply(u):
    with _lock:
        r, tag, out = _session.turn(u)
    return {"intent": r, "tag": tag, "text": out, "corpus": _state["corpus"], "corpus_vocab": _state["vocab"]}


def _content_text(c):
    """Coerce an OpenAI message `content` to text: a plain string, or the joined text parts of the
    structured [{type,text},...] array shape some CopilotKit / Responses clients send."""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("text"))
    return ""


def _last_user(messages):
    return next((_content_text(m.get("content")) for m in reversed(messages) if m.get("role") == "user"), "")


def _cc_object(out, model):                                      # a full (non-stream) chat.completion
    return {"id": "chatcmpl-siona", "object": "chat.completion", "created": int(time.time()), "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": out["text"]}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": len(out["text"].split()), "total_tokens": 0},
            "siona": {"intent": out["intent"], "tag": out["tag"], "corpus": out["corpus"]}}


def _cc_chunks(out, model):                                      # the SSE chunk stream (yields str lines)
    created, cid = int(time.time()), "chatcmpl-siona"

    def chunk(delta, finish=None):
        return "data: %s\n\n" % json.dumps(
            {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
             "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]})

    yield chunk({"role": "assistant", "content": ""})
    for i, word in enumerate(out["text"].split(" ")):            # word-by-word so the UI shows the typing
        yield chunk({"content": (word if i == 0 else " " + word)})
    yield chunk({}, finish="stop")
    yield "data: [DONE]\n\n"


class H(http.server.BaseHTTPRequestHandler):
    def _head(self, code, ctype, length=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.end_headers()

    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self._head(code, ctype, len(b))
        self.wfile.write(b)

    def _stream(self, chunks):
        self._head(200, "text/event-stream; charset=utf-8")
        for line in chunks:
            self.wfile.write(line.encode("utf-8"))
            self.wfile.flush()

    def do_OPTIONS(self):
        self._head(204, "text/plain", 0)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif u.path in ("/health", "/status"):
            self._send(200, json.dumps({"ok": True, "engine": "siona.infer.Session", "corpus": _state["corpus"],
                                        "vocab": _state["vocab"], "load_s": _state["load_s"],
                                        "up_s": round(time.time() - _state["t0"], 1)}))
        elif u.path == "/v1/models":
            self._send(200, json.dumps({"object": "list",
                                        "data": [{"id": w, "object": "model", "owned_by": "siona"} for w in WORLDS]}))
        elif u.path == "/chat":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            self._send(200, json.dumps(_reply(q)))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        path = self.path.rstrip("/")
        if path == "/v1/chat/completions":
            model = body.get("model", "siona:corpus")
            out = _reply(_last_user(body.get("messages", [])))
            if body.get("stream"):
                self._stream(_cc_chunks(out, model))
            else:
                self._send(200, json.dumps(_cc_object(out, model)))
        elif path == "/v1/responses":
            self._responses(body)
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def _responses(self, body):
        model = body.get("model", "siona:corpus")
        inp = body.get("input")
        q = inp if isinstance(inp, str) else _last_user(inp if isinstance(inp, list) else [])
        text = _reply(q)["text"]
        mid, rid = "msg_siona", "resp_siona"
        item = {"id": mid, "type": "message", "status": "completed", "role": "assistant",
                "content": [{"type": "output_text", "text": text, "annotations": []}]}

        def obj(status, output):
            return {"id": rid, "object": "response", "created_at": int(time.time()), "status": status,
                    "model": model, "output": output, "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}}
        if not body.get("stream"):
            self._send(200, json.dumps(obj("completed", [item])))
            return

        def ev():
            def e(o):
                return "data: %s\n\n" % json.dumps(o)
            # the FULL typed-event sequence CopilotKit 1.59.5 needs: the text part must be ADDED (output_item.added +
            # content_part.added) BEFORE its delta, else the runtime errors "text part <id> not found" (the :3000 bug).
            yield e({"type": "response.created", "response": obj("in_progress", [])})
            yield e({"type": "response.output_item.added", "output_index": 0,
                     "item": {"id": mid, "type": "message", "status": "in_progress", "role": "assistant", "content": []}})
            yield e({"type": "response.content_part.added", "item_id": mid, "output_index": 0, "content_index": 0,
                     "part": {"type": "output_text", "text": "", "annotations": []}})
            yield e({"type": "response.output_text.delta", "item_id": mid, "output_index": 0, "content_index": 0, "delta": text})
            yield e({"type": "response.output_text.done", "item_id": mid, "output_index": 0, "content_index": 0, "text": text})
            yield e({"type": "response.content_part.done", "item_id": mid, "output_index": 0, "content_index": 0,
                     "part": {"type": "output_text", "text": text, "annotations": []}})
            yield e({"type": "response.output_item.done", "output_index": 0, "item": item})
            yield e({"type": "response.completed", "response": obj("completed", [item])})
        self._stream(ev())

    def log_message(self, *a):
        return                                                   # quiet


PAGE = """<!doctype html><meta charset=utf-8><title>Siona - #231 etak walk</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem}
#log>div{margin:.5rem 0;padding:.5rem .7rem;border-radius:.5rem}.u{background:#e8f0fe;text-align:right}
.s{background:#f1f3f4;white-space:pre-wrap}.m{color:#666;font-size:.8rem}input{width:78%;padding:.6rem;font-size:1rem}
button{padding:.6rem 1rem;font-size:1rem}#st{color:#888;font-size:.85rem;margin-bottom:1rem}</style>
<h2>Siona &mdash; the directed Class-L corpus + etak walk (#231)</h2>
<div id=st>status&hellip;</div>
<p style="color:#888;font-size:.85rem">Fallback page. The real UI is the CopilotKit app at <code>~/general/siona-chat</code> (port 3000).</p>
<div id=log></div>
<form onsubmit="ask();return false"><input id=q autofocus placeholder="what is planet"><button>ask</button></form>
<script>
async function st(){let j=await(await fetch('/status')).json();
document.getElementById('st').textContent='engine '+j.engine+' | corpus: '+j.corpus+(j.vocab?(' ('+j.vocab.toLocaleString()+' vocab)'):'')+' | up '+j.up_s+'s';}
function add(t,c){let d=document.createElement('div');d.className=c;d.textContent=t;document.getElementById('log').append(d);
window.scrollTo(0,document.body.scrollHeight);}
async function ask(){let q=document.getElementById('q').value.trim();if(!q)return;document.getElementById('q').value='';
add(q,'u');let j=await(await fetch('/chat?q='+encodeURIComponent(q))).json();
add(j.text,'s');let m=document.createElement('div');m.className='m';m.textContent='['+j.intent+' / '+j.tag+']';
document.getElementById('log').append(m);st();}
st();setInterval(st,4000);
</script>"""


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    print("=== Siona /v1 backend (#231 corpus + etak walk) ===", flush=True)
    _load_corpus()                                               # synchronous (~1 s demand-load) -> no startup race
    srv = Server((HOST, PORT), H)
    print("Siona /v1 up on http://%s:%d/v1   (browser fallback: http://<host>:%d/)" % (HOST, PORT, PORT), flush=True)
    print("  UI:  cd ~/general/siona-chat && npm run dev   ->  http://<host>:3000/", flush=True)
    print("  curl 'http://127.0.0.1:%d/chat?q=what+is+planet'" % PORT, flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
