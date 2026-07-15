r"""R-RBS-LM-SIONAHTTP (#231/F1234) — serve Siona over HTTP with the #231 directed Class-L corpus store wired in.

A dependency-free stdlib server (http.server; no fastapi/uvicorn) exposing `siona.infer.Session.turn()`:
  GET  /                     -> a minimal browser chat page (check it out at http://<host>:3000/)
  GET  /chat?q=...           -> {"intent","tag","text"} (easy to curl / fetch)
  GET  /health , /status     -> engine + corpus-load state
  POST /v1/chat/completions  -> OpenAI-compatible (the universal connector: CopilotKit / AG2 / openai SDK)

The #231 corpus (default: the real simplewiki directed genome) loads in a BACKGROUND THREAD, so the server is up
INSTANTLY; `/status` shows the load; `define` falls back to the shipped tool-grounding until it lands, then reads
the corpus (F1233). Binds 0.0.0.0:3000 by default (LAN-accessible, NO auth — keep to a trusted network).

srmech 0.9.0rc253. Run:
  SIONA_CORPUS=~/corpora/wikipedia/simplewiki_directed.genome \
    /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONAHTTP_...py
"""
import http.server
import json
import os
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
PORT = int(os.environ.get("SIONA_PORT", "3000"))

_session = Session()
_lock = threading.Lock()                                         # http.server is single-threaded, but guard turn() anyway
_state = {"corpus": "none", "vocab": 0, "load_s": None, "t0": time.time()}


def _load_corpus_bg():
    p = Path(os.path.expanduser(CORPUS))
    if not p.exists():
        _state["corpus"] = "MISSING: %s" % p
        return
    _state["corpus"] = "loading %s" % p.name
    t0 = time.time()
    nv = _session.load_corpus(p)                                 # ~21 min at 39M edges; reads instant after
    _state.update(corpus=p.name, vocab=nv, load_s=round(time.time() - t0, 1))


def _reply(u):
    with _lock:
        r, tag, out = _session.turn(u)
    return {"intent": r, "tag": tag, "text": out,
            "corpus": _state["corpus"], "corpus_vocab": _state["vocab"]}


def _openai(out, model):
    return {"id": "chatcmpl-siona", "object": "chat.completion", "created": int(time.time()), "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": out["text"]},
                         "finish_reason": "stop"}],
            "siona": {"intent": out["intent"], "tag": out["tag"], "corpus": out["corpus"]}}


PAGE = """<!doctype html><meta charset=utf-8><title>Siona — #231 corpus</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem}
#log>div{margin:.5rem 0;padding:.5rem .7rem;border-radius:.5rem}.u{background:#e8f0fe;text-align:right}
.s{background:#f1f3f4}.m{color:#666;font-size:.8rem}input{width:78%;padding:.6rem;font-size:1rem}
button{padding:.6rem 1rem;font-size:1rem}#st{color:#888;font-size:.85rem;margin-bottom:1rem}</style>
<h2>Siona &mdash; the directed Class-L corpus (#231)</h2>
<div id=st>loading status&hellip;</div><div id=log></div>
<form onsubmit="ask();return false"><input id=q autofocus placeholder="what is water"><button>ask</button></form>
<script>
async function st(){let r=await fetch('/status');let j=await r.json();
document.getElementById('st').textContent='engine '+j.engine+' | corpus: '+j.corpus+(j.vocab?(' ('+j.vocab.toLocaleString()+' vocab)'):'')+' | up '+j.up_s+'s';}
function add(t,c){let d=document.createElement('div');d.className=c;d.textContent=t;document.getElementById('log').append(d);
window.scrollTo(0,document.body.scrollHeight);}
async function ask(){let q=document.getElementById('q').value.trim();if(!q)return;document.getElementById('q').value='';
add(q,'u');let r=await fetch('/chat?q='+encodeURIComponent(q));let j=await r.json();
add(j.text,'s');let m=document.createElement('div');m.className='m';m.textContent='['+j.intent+' / '+j.tag+']';
document.getElementById('log').append(m);st();}
st();setInterval(st,4000);
</script>"""


class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif u.path in ("/health", "/status"):
            self._send(200, json.dumps({"ok": True, "engine": "siona.infer.Session", "corpus": _state["corpus"],
                                        "vocab": _state["vocab"], "load_s": _state["load_s"],
                                        "up_s": round(time.time() - _state["t0"], 1)}))
        elif u.path == "/chat":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            self._send(200, json.dumps(_reply(q)))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path.rstrip("/") == "/v1/chat/completions":
            n = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
            msgs = body.get("messages", [])
            q = msgs[-1].get("content", "") if msgs else ""
            self._send(200, json.dumps(_openai(_reply(q), body.get("model", "siona"))))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, *a):
        return                                                   # quiet


def main():
    threading.Thread(target=_load_corpus_bg, daemon=True).start()
    srv = http.server.HTTPServer((HOST, PORT), H)
    print("Siona HTTP up on http://%s:%d/  (corpus=%s, loading in background)" % (HOST, PORT, CORPUS), flush=True)
    print("  browser: http://<this-host>:%d/   |   curl 'http://127.0.0.1:%d/chat?q=what+is+water'" % (PORT, PORT), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
