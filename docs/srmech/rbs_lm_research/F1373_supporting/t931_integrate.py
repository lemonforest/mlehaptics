"""Integrate task931 3/3 (e035d2495) or 3b/3 (dff66d754) into the branch's
worktree files, site by site. No git calls.

Usage: python t931_integrate.py 3|3b [--write]

For each hunk the source replaced ONE call `klein4_random(D, seed=X)` with a
`klein4_address(...)` call. On the branch that site now reads either
  * `klein4_expand(D, X)`  — F1285's number-preserving rename (5f55963cf): the
    call is located by AST equality with the renamed source call and replaced
    by the source's new call text, character for character; nothing else on
    the line changes; or
  * `klein4_encode_bytes(...)` — F1284's later migration (145558237) of a
    builtin-hash() site: the branch version is kept.
Anything else stops the run.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

WT = Path(r"D:/GitHub/mlehaptics/.claude/worktrees/wf_7e7f47ba-1ab-1")
HERE = Path(__file__).resolve().parent
F1284 = set((HERE / "f1284_files.txt").read_text().split())


def call_spans(text: str, name: str):
    """(start, end, expr) of every `name(...)` call in text, paren-matched."""
    out = []
    i = 0
    while True:
        j = text.find(name + "(", i)
        if j < 0:
            return out
        if j > 0 and (text[j - 1].isalnum() or text[j - 1] == "_"):
            i = j + 1
            continue
        depth = 0
        k = text.index("(", j)
        m = k
        for m in range(k, len(text)):
            if text[m] == "(":
                depth += 1
            elif text[m] == ")":
                depth -= 1
                if depth == 0:
                    break
        out.append((j, m + 1, text[j:m + 1]))
        i = m + 1


def dump_call(expr: str, rename_seed: bool = False) -> str:
    node = ast.parse(expr, mode="eval").body
    args = list(node.args)
    kws = []
    for kw in node.keywords:
        if rename_seed and kw.arg == "seed":
            args.append(kw.value)
        else:
            kws.append(kw)
    name = "klein4_expand" if rename_seed else node.func.id
    return ast.dump(ast.Call(func=ast.Name(id=name), args=args, keywords=kws), include_attributes=False)


def main() -> None:
    tag = sys.argv[1]
    write = "--write" in sys.argv
    d = json.loads((HERE / "t931_classify.json").read_text(encoding="utf-8"))
    by_file: dict[str, list] = {}
    for r in d[tag]:
        by_file.setdefault(r["path"], []).append(r)
    report = []
    counts = {}
    for path, rows in by_file.items():
        p = WT / path
        raw = p.read_bytes()
        text = raw.decode("utf-8")
        lines = text.splitlines(keepends=True)
        try:
            ast.parse(text.replace("\r\n", "\n"))
            parsed_before = True
        except SyntaxError:
            parsed_before = False
        edits = []  # (line_idx, start, end, new_text)
        for r in rows:
            olds = [s for l in r["old"] for s in call_spans(l, "klein4_random")]
            news = [s for l in r["new"] for s in call_spans(l, "klein4_address")]
            assert len(olds) == 1 and len(news) == 1, (path, r["old_start"], olds, news)
            want = dump_call(olds[0][2], rename_seed=True)
            new_expr = news[0][2]
            new_prefix = "".join(r["new"])[:news[0][0]][-4:]
            hits = []
            for li, ln in enumerate(lines):
                for s, e, ex in call_spans(ln, "klein4_expand"):
                    try:
                        if dump_call(ex) == want:
                            hits.append((li, s, e, ex))
                    except SyntaxError:
                        pass
            taken = {(h[0], h[1]) for h in edits}
            free = [h for h in hits if (h[0], h[1]) not in taken]
            if free:
                h = min(free, key=lambda h: abs(h[0] + 1 - r["old_start"]))
                assert lines[h[0]][:h[1]][-4:] == new_prefix, (path, lines[h[0]][:h[1]][-8:], new_prefix)
                edits.append((h[0], h[1], h[2], new_expr))
                action = "INTEGRATED"
                before = lines[h[0]].rstrip("\r\n")
                after = before[:h[1]] + new_expr + before[h[2]:]
                ln_no = h[0] + 1
            elif path in F1284 and any("klein4_encode_bytes(" in lines[i]
                                       for i in range(max(0, r["old_start"] - 4), min(len(lines), r["old_start"] + 4))):
                action = "KEPT_BRANCH_F1284"
                i = next(i for i in range(max(0, r["old_start"] - 4), min(len(lines), r["old_start"] + 4))
                         if "klein4_encode_bytes(" in lines[i])
                before = after = lines[i].rstrip("\r\n")
                ln_no = i + 1
            else:
                raise SystemExit(f"NO SITE: {path} @{r['old_start']} want {olds[0][2]}")
            counts[action] = counts.get(action, 0) + 1
            report.append({"path": path, "old_start": r["old_start"], "action": action, "line": ln_no,
                           "source_old": olds[0][2], "source_new": new_expr,
                           "branch_before": before.strip(), "branch_after": after.strip()})
        if edits and write:
            for li in sorted({e[0] for e in edits}):
                row_edits = sorted([e for e in edits if e[0] == li], key=lambda e: -e[1])
                ln = lines[li]
                for _, s, e, new in row_edits:
                    ln = ln[:s] + new + ln[e:]
                lines[li] = ln
            new_text = "".join(lines)
            if parsed_before:
                ast.parse(new_text.replace("\r\n", "\n"))
            p.write_bytes(new_text.encode("utf-8"))
    (HERE / f"t931_integrate_{tag}.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(tag, "write" if write else "dry-run", json.dumps(counts))


if __name__ == "__main__":
    main()
