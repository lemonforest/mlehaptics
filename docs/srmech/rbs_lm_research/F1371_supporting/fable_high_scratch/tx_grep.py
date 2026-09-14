"""Parse only transcript lines matching a regex; print timestamp, file, role/kind, short windows.
usage: python tx_grep.py <regex> <window_chars> <max_windows_per_line> file1 [file2 ...]
Classification: user+text  = maintainer (in a top-level session) / dispatcher (in a subagent file)
                user+tool_result = tool output (NOT maintainer)
                assistant+text = assistant statement; assistant+tool_use = tool input (assistant-authored)
"""
import sys, re, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rx = re.compile(sys.argv[1], re.I)
W = int(sys.argv[2]); MAXW = int(sys.argv[3])
files = sys.argv[4:]

def blocks(msg):
    c = msg.get("content")
    if isinstance(c, str):
        yield ("text", c)
        return
    if isinstance(c, list):
        for b in c:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "text":
                yield ("text", b.get("text", ""))
            elif t == "tool_use":
                yield ("tool_use", json.dumps(b.get("input", {}), ensure_ascii=False))
            elif t == "tool_result":
                cc = b.get("content")
                if isinstance(cc, str):
                    yield ("tool_result", cc)
                elif isinstance(cc, list):
                    for x in cc:
                        if isinstance(x, dict) and x.get("type") == "text":
                            yield ("tool_result", x.get("text", ""))
            elif t == "thinking":
                yield ("thinking", b.get("thinking", ""))

for fn in files:
    short = fn.replace("\\", "/").split("/projects/")[-1]
    with open(fn, encoding="utf-8", errors="replace") as f:
        for ln, line in enumerate(f, 1):
            if not rx.search(line):
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            typ = d.get("type")
            if typ not in ("user", "assistant"):
                continue
            msg = d.get("message") or {}
            role = msg.get("role", typ)
            ts = d.get("timestamp", "?")
            for kind, txt in blocks(msg):
                hits = list(rx.finditer(txt))
                if not hits:
                    continue
                print(f"=== {ts} {short}:{ln} role={role} kind={kind} nhits={len(hits)}")
                for m in hits[:MAXW]:
                    a = max(0, m.start() - W); b = min(len(txt), m.end() + W)
                    s = txt[a:b].replace("\n", " ⏎ ")
                    print(f"   …{s}…")
