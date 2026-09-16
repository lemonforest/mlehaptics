"""rc473 truth repair 1 — resolve EVERY line citation in the curated ToolEntry prose by content.

For each string constant in `_tool_docs_curated.py` (raw bytes, so a rewrite maps to
the source exactly), find every `path.py:N[-M][,N...]` token and every bare `:N`
follow-on that continues it. A GROUP is one full token plus its follow-ons. The
NAMES a group cites are the identifiers in the code spans / dotted identifiers just
before it. Each line number is judged against the defining spans (decorator line ..
def line, or the assignment line) of those names in the resolved file:

  DEF      the line holds the definition of a cited name (for a range, the range
           contains a definition line)
  MENTION  the line only mentions a cited name
  OTHER    neither
A group whose lines are ALL DEF is kept. Every other group is STALE, and is
rewritten to name its module with no line number — after asserting (ast) that a
cited name is defined in that module. A path that resolves to no tracked file is
UNRESOLVED; it is rewritten to the one module that defines the cited name.

Usage: python r1_cite_resolve.py <docs/srmech> <report.tsv> [--apply] [--overrides overrides.py]
"""
import ast
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(sys.argv[1]).resolve()                     # docs/srmech
REPORT = Path(sys.argv[2])
APPLY = "--apply" in sys.argv
OVR = {}
if "--overrides" in sys.argv:
    ns = {}
    exec(Path(sys.argv[sys.argv.index("--overrides") + 1]).read_text(encoding="utf-8"), ns)
    OVR = ns["OVERRIDES"]
CUR = BASE / "python" / "srmech" / "introspect" / "_tool_docs_curated.py"

# ------------------------------------------------------------------ tracked .py files
tracked = subprocess.run(["git", "ls-files", "--", "*.py"], cwd=BASE, capture_output=True, check=True,
                         text=True).stdout.split()
FILES = {}   # repo-relative-to-docs/srmech posix path -> (lines, spans)


def index(rel):
    if rel in FILES:
        return FILES[rel]
    p = BASE / rel
    src = p.read_text(encoding="utf-8", errors="replace")
    spans = defaultdict(list)
    try:
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                lo = min([d.lineno for d in node.decorator_list] + [node.lineno])
                spans[node.name].append((lo, node.lineno))
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        spans[t.id].append((node.lineno, node.lineno))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                spans[node.target.id].append((node.lineno, node.lineno))
    except SyntaxError:
        pass
    FILES[rel] = (src.split("\n"), spans)
    return FILES[rel]


def resolve_path(spelled):
    """Tracked files whose docs/srmech-relative path ends with the spelled path."""
    s = spelled
    for pre in ("docs/srmech/",):
        if s.startswith(pre):
            s = s[len(pre):]
    out = []
    for t in tracked:
        for cand in (t, t[len("python/"):] if t.startswith("python/") else None):
            if cand and (cand == s or cand.endswith("/" + s)):
                out.append(t)
                break
    return sorted(set(out))


PKG_DEFS = None


def definers(name):
    global PKG_DEFS
    if PKG_DEFS is None:
        PKG_DEFS = defaultdict(set)
        for t in tracked:
            if t.startswith("python/srmech/"):
                for nm in index(t)[1]:
                    PKG_DEFS[nm].add(t)
    return sorted(PKG_DEFS.get(name, ()))


# ------------------------------------------------------------------ tokens
FULL = re.compile(rb"(?P<path>(?:[\w.-]+/)*[\w-]+\.py):(?P<lines>\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)")
BARE = re.compile(rb"(?P<tick>``?)?:(?P<lines>\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)(?P=tick)?")
SPAN = re.compile(rb"``([^`]+)``|`([^`]+)`")
IDENT = re.compile(rb"[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)*")


def names_in(window):
    out = []
    for m in SPAN.finditer(window):
        body = m.group(1) or m.group(2)
        for im in IDENT.finditer(body):
            out.append(im.group(0).decode().split(".")[-1])
    stripped = SPAN.sub(b" ", window)
    for im in IDENT.finditer(stripped):
        w = im.group(0).decode()
        if "." in w or "_" in w:
            out.append(w.split(".")[-1])
    return [n for n in out if n and not n.endswith("py")]


def parse_lines(s):
    out = []
    for part in s.decode().split(","):
        a, _, b = part.partition("-")
        out.append((int(a), int(b or a)))
    return out


raw = CUR.read_bytes()
starts = [0]
for i, ch in enumerate(raw):
    if ch == 10:
        starts.append(i + 1)
tree = ast.parse(raw)

groups = []   # dicts
for node in ast.walk(tree):
    if not isinstance(node, ast.Dict):
        continue
    for k, v in zip(node.keys, node.values):
        if not (isinstance(k, ast.Constant) and isinstance(k.value, str) and k.value.startswith("srmech.")):
            continue
        for c in ast.walk(v):
            if not (isinstance(c, ast.Constant) and isinstance(c.value, str)):
                continue
            a = starts[c.lineno - 1] + c.col_offset
            b = starts[c.end_lineno - 1] + c.end_col_offset
            seg = raw[a:b]
            fulls = list(FULL.finditer(seg))
            if not fulls:
                continue
            for i, fm in enumerate(fulls):
                nxt = fulls[i + 1].start() if i + 1 < len(fulls) else len(seg)
                g = {"entry": k.value, "abs": a, "full": fm, "bares": [], "seg": seg}
                pos = fm.end()
                while True:
                    bm = BARE.search(seg, pos, nxt)
                    if not bm:
                        break
                    gap = seg[pos:bm.start()]
                    # a follow-on continues the group: short gap, list punctuation or a
                    # method/code span, no sentence break, no new parenthetical opener
                    ok_gap = (len(gap) <= 48 and not re.search(rb"[.;]\s|\(\s*$|\)\s", gap)
                              and re.fullmatch(rb"[`\s/,]*(?:(?:``?[\w.()]+``?|and|or)[`\s/,]*)*", gap))
                    before = seg[bm.start() - 1:bm.start()] if bm.start() else b""
                    if not ok_gap or before in (b"[", b"]") or re.match(rb"\w", before or b" "):
                        break
                    g["bares"].append(bm)
                    pos = bm.end()
                # window of cited names: up to 200 bytes before the full token, cut at
                # the previous group's end or a sentence boundary
                lo = max(0, fm.start() - 200)
                if i:
                    prev = groups[-1]
                    pend = (prev["bares"][-1].end() if prev["bares"] else prev["full"].end())
                    lo = max(lo, pend)
                win = seg[lo:fm.start()]
                cut = max(win.rfind(b". "), win.rfind(b"; "), win.rfind(b" - "), win.rfind(b"\xe2\x80\x94"))
                if cut > 0:
                    win = win[cut + 2:]
                # names that sit between the full token and its follow-ons belong to the group too
                tail = seg[fm.end():(g["bares"][-1].start() if g["bares"] else fm.end())]
                g["names"] = names_in(win) + names_in(tail)
                # "A / B (f.py:1 / f.py:2)": the second full token's window is only the
                # separator, so it cites the names its predecessor's window named
                if i and not names_in(win) and re.fullmatch(rb"[`\s/,]*", win) and groups[-1]["seg"] is seg:
                    g["names"] = groups[-1]["names"] + g["names"]
                g["window"] = win
                groups.append(g)

rows = []
edits = []   # (abs_start, abs_end, new_bytes)
verdicts = Counter()
for g in groups:
    fm = g["full"]
    spelled = fm.group("path").decode()
    key = (g["entry"], fm.group(0).decode(), g["seg"][max(0, fm.start() - 60):fm.start()].decode(errors="replace"))
    cands = resolve_path(spelled)
    lines = parse_lines(fm.group("lines")) + [ln for bm in g["bares"] for ln in parse_lines(bm.group("lines"))]
    names = list(dict.fromkeys(g["names"]))
    # a citation with no cited name defined in its file cites the entry's OWN op
    # (the "WHAT - ... (srmech/x.py:NNN)" self-citation form)
    own = g["entry"].rsplit(".", 1)[-1]
    if own not in names:
        names.append(own)
    judged = []
    target = None
    if len(cands) > 1:
        c2 = [c for c in cands if any(n in index(c)[1] for n in names)]
        cands = c2 if len(c2) == 1 else cands
    if len(cands) == 1:
        target = cands[0]
        L, spans = index(target)
        for (x, y) in lines:
            j = "OTHER"
            for n in names:
                for (dlo, dline) in spans.get(n, ()):
                    if (x == y and dlo <= x <= dline) or (x != y and x <= dline <= y):
                        j = "DEF"
                if j == "DEF":
                    break
            if j != "DEF" and 0 < x <= len(L) and any(re.search(r"\b%s\b" % re.escape(n), L[x - 1]) for n in names):
                j = "MENTION"
            judged.append(j)
        defined_here = [n for n in names if n in spans]
        verdict = "OK" if all(j == "DEF" for j in judged) else "STALE"
        new_path = spelled
        if verdict == "STALE" and not defined_here:
            verdict = "STALE-NODEF"
    else:
        defined_here = []
        verdict = "UNRESOLVED" if not cands else "AMBIGUOUS"
        new_path = None
        # the path moved (ADR-0010 took srmech/amsc/* to srmech/math/* etc.): a tracked
        # package file with the same basename that DEFINES a cited name other than the
        # entry's own op (or the own op when it is the only name)
        base = spelled.rsplit("/", 1)[-1]
        cited = [n for n in names if n != own] or [own]
        same = [t for t in tracked if t.startswith("python/srmech/") and t.rsplit("/", 1)[-1] == base
                and any(n in index(t)[1] for n in cited)]
        if not same:   # the window named only carriers / types: the self-citation form
            same = [t for t in tracked if t.startswith("python/srmech/") and t.rsplit("/", 1)[-1] == base
                    and own in index(t)[1]]
            if same:
                cited = [own]
        defs = sorted({d for n in cited for d in definers(n)})
        if len(same) == 1:
            defs = same
        if len(defs) == 1:
            target = defs[0]
            rel = target[len("python/"):] if target.startswith("python/") else target
            new_path = rel if "/" in spelled else rel.rsplit("/", 1)[-1]
            defined_here = [n for n in names if n in index(target)[1]]
    ov = OVR.get((g["entry"], fm.group(0).decode()))
    if ov is not None:
        verdict = "OVERRIDE:" + ov[0]
        new_path = ov[1]
    verdicts[verdict.split(":")[0] if not verdict.startswith("OVERRIDE") else verdict] += 1
    rows.append("\t".join([verdict, g["entry"], fm.group(0).decode()
                           + "".join(" +" + bm.group(0).decode() for bm in g["bares"]),
                           spelled, str(target), ",".join(judged), ",".join(names[-6:]),
                           ",".join(defined_here), str(new_path),
                           g["window"][-90:].decode(errors="replace").replace("\t", " ")]))
    if verdict in ("STALE", "UNRESOLVED") or (verdict.startswith("OVERRIDE:rewrite")):
        if new_path is None:
            continue
        a0 = g["abs"]
        # full token -> path only; each bare follow-on and the separator before it removed
        edits.append((a0 + fm.start(), a0 + fm.end(), new_path.encode()))
        prev_end = fm.end()
        for bm in g["bares"]:
            gap = g["seg"][prev_end:bm.start()]
            sep = re.search(rb"(?:\s*/\s*|\s*,\s*|\s+)(?:``?)?$", gap)
            s0 = prev_end + (sep.start() if sep else len(gap))
            # keep a method span that sits in the gap (`.det()` :470 -> `.det()`)
            if re.search(rb"`[^`]+`", gap):
                s0 = prev_end + len(gap) - len(re.search(rb"\s*(?:``?)?$", gap).group(0))
            e0 = bm.end()
            if bm.group("tick") and gap.endswith(bm.group("tick")):
                pass
            edits.append((a0 + s0, a0 + e0, b""))
            prev_end = bm.end()

REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")
print("groups", len(groups), "full tokens", len(groups), "follow-ons", sum(len(g["bares"]) for g in groups))
print("verdicts", dict(verdicts))
print("edits", len(edits))
if APPLY:
    out = bytearray(raw)
    for s0, e0, nb in sorted(edits, reverse=True):
        out[s0:e0] = nb
    for old, new in (ns.get("LITERAL", []) if OVR else []):
        n = bytes(out).count(old.encode())
        assert n == 1, (n, old)
        out = bytearray(bytes(out).replace(old.encode(), new.encode()))
        print("LITERAL x1:", old[:80])
    CUR.write_bytes(bytes(out))
    print("WROTE", CUR, "bytes", len(raw), "->", len(out), "CR", raw.count(b"\r"), "->", bytes(out).count(b"\r"))
