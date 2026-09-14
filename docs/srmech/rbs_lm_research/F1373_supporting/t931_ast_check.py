"""For every DIVERGED hunk of task931 1/3, check at the AST level whether the
branch file already carries the hunk's replacement call(s) and no longer carries
its removed call(s). No git calls; reads t931_classify.json and the worktree.

A call is compared by ast.dump(..., include_attributes=False), so spelling
differences that do not change the parsed expression (10_000 vs 10000,
0x7FFFFFFF vs 2147483647, quote style, spacing) compare equal.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

WT = Path(r"D:/GitHub/mlehaptics/.claude/worktrees/wf_7e7f47ba-1ab-1")
HERE = Path(__file__).resolve().parent
NAMES = {"klein4_random", "klein4_expand", "klein4_address", "klein4_encode_bytes"}


def call_name(node: ast.Call):
    f = node.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return None


def calls_in_source(src: str):
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and call_name(node) in NAMES:
            f = node.func
            norm = ast.Call(func=ast.Name(id=call_name(node)), args=node.args, keywords=node.keywords)
            out.append(ast.dump(norm, include_attributes=False))
    return out


def extract_calls(text: str):
    """Pull every klein4_* call expression out of hunk text by paren matching."""
    res = []
    i = 0
    while True:
        j = min((text.find(n + "(", i) for n in NAMES if text.find(n + "(", i) >= 0), default=-1)
        if j < 0:
            break
        k = text.index("(", j)
        depth = 0
        for m in range(k, len(text)):
            if text[m] == "(":
                depth += 1
            elif text[m] == ")":
                depth -= 1
                if depth == 0:
                    break
        expr = text[j:m + 1]
        try:
            node = ast.parse(expr, mode="eval").body
            res.append(ast.dump(ast.Call(func=ast.Name(id=call_name(node)), args=node.args,
                                         keywords=node.keywords), include_attributes=False))
        except SyntaxError:
            res.append("UNPARSEABLE:" + expr)
        i = m + 1
    return res


def main() -> None:
    d = json.loads((HERE / "t931_classify.json").read_text(encoding="utf-8"))
    tally = {}
    lines_out = []
    for r in d["1"]:
        if r["cls"] != "DIVERGED":
            continue
        src = (WT / r["path"]).read_bytes().decode("utf-8", "surrogateescape").replace("\r\n", "\n")
        branch_calls = calls_in_source(src)
        if branch_calls is None:
            verdict = "BRANCH_FILE_UNPARSEABLE"
        else:
            new_calls = extract_calls("\n".join(r["new"]))
            old_calls = extract_calls("\n".join(r["old"]))
            new_ok = all(c in branch_calls for c in new_calls)
            old_gone = all(c not in branch_calls for c in old_calls)
            verdict = "AST_PRESENT" if (new_ok and old_gone) else f"NOT_PRESENT(new_ok={new_ok},old_gone={old_gone})"
        tally[verdict] = tally.get(verdict, 0) + 1
        lines_out.append(f"{verdict}\t{r['path'].split('/')[-1]}\t@{r['old_start']}")
    (HERE / "t931_ast_check.txt").write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    print(json.dumps(tally, indent=1))


if __name__ == "__main__":
    main()
