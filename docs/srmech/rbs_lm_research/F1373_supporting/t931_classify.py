"""Classify every hunk of the four task931 rewrite commits against the branch
worktree (research/rbs-lm-rolling-2 checked out, clean). No git calls: reads the
-U0 diffs saved beside this script and the worktree files.

Per hunk:
  PRESENT     the hunk's new lines already sit in the branch file as a block and
              its old block does not
  APPLICABLE  the hunk's old block sits in the branch file unchanged (can be applied)
  DIVERGED    neither: the branch changed those lines another way
  NOFILE      the path does not exist on the branch
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WT = Path(r"D:/GitHub/mlehaptics/.claude/worktrees/wf_7e7f47ba-1ab-1")
HERE = Path(__file__).resolve().parent


def parse(diff_path: Path):
    files = []
    cur = None
    hunk = None
    for raw in diff_path.read_bytes().split(b"\n"):
        line = raw.decode("utf-8", "surrogateescape")
        if line.startswith("diff --git "):
            cur = {"path": None, "hunks": []}
            files.append(cur)
            hunk = None
        elif line.startswith("+++ "):
            p = line[4:]
            cur["path"] = p[2:] if p.startswith("b/") else p
        elif line.startswith("--- "):
            continue
        elif line.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            hunk = {"old_start": int(m.group(1)), "old": [], "new": []}
            cur["hunks"].append(hunk)
        elif hunk is not None and line.startswith("-"):
            hunk["old"].append(line[1:].rstrip("\r"))
        elif hunk is not None and line.startswith("+"):
            hunk["new"].append(line[1:].rstrip("\r"))
    return files


def find_block(lines, block):
    n = len(block)
    if n == 0:
        return []
    return [i for i in range(len(lines) - n + 1) if lines[i:i + n] == block]


def key_of(old_line: str) -> str:
    m = re.search(r"klein4_random\((.*)\)", old_line)
    return m.group(1) if m else old_line.strip()


def main() -> None:
    out = {}
    for tag in ("1", "2", "3", "3b"):
        files = parse(HERE / f"t931_{tag}.diff")
        rows = []
        for f in files:
            p = WT / f["path"]
            if not p.exists():
                for h in f["hunks"]:
                    rows.append({"path": f["path"], "old_start": h["old_start"], "cls": "NOFILE",
                                 "old": h["old"], "new": h["new"]})
                continue
            lines = [l.rstrip("\r") for l in p.read_bytes().decode("utf-8", "surrogateescape").split("\n")]
            for h in f["hunks"]:
                old_at = find_block(lines, h["old"])
                new_at = find_block(lines, h["new"])
                if old_at:
                    cls = "APPLICABLE"
                elif new_at:
                    cls = "PRESENT"
                else:
                    cls = "DIVERGED"
                row = {"path": f["path"], "old_start": h["old_start"], "cls": cls,
                       "old": h["old"], "new": h["new"], "old_at": old_at[:3], "new_at": new_at[:3]}
                if cls == "DIVERGED":
                    cands = []
                    for ol in h["old"]:
                        k = key_of(ol)
                        # search the branch for the argument text, then for the assigned name
                        lhs = ol.split("=")[0].strip() if "=" in ol.split("klein4_random")[0] else None
                        for i, bl in enumerate(lines):
                            if (k and k in bl) or (lhs and bl.strip().startswith(lhs + " =")):
                                cands.append((i + 1, bl.strip()))
                    row["branch_candidates"] = cands[:6]
                rows.append(row)
        out[tag] = rows
    summary = {}
    for tag, rows in out.items():
        c = {}
        files_by = {}
        for r in rows:
            c[r["cls"]] = c.get(r["cls"], 0) + 1
            files_by.setdefault(r["path"], set()).add(r["cls"])
        fc = {}
        for path, s in files_by.items():
            k = "+".join(sorted(s))
            fc[k] = fc.get(k, 0) + 1
        summary[tag] = {"hunks": len(rows), "by_class": c, "files": len(files_by), "file_class_mix": fc}
    (HERE / "t931_classify.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    sys.exit(main())
