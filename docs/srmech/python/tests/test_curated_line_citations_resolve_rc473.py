"""Every ``path.py:NNN`` citation in the curated ToolEntry prose lands on what it names.
(rc473 final round, `#T1188`)

WHY
---
The curated file (``srmech/introspect/_tool_docs_curated.py``) is emitted into
``_tool_docs.py`` and the compiled-in ``srmech_tool_registry.c``, so its line
citations ship. rc473's truth round found 141 of them stale; truth repair 1
drained the class with two committed census scripts —
``notes/_rc473_truth_repair1_cite_pass1.py`` (full tokens: 662 read, 131 on a
definition line kept, 531 rewritten to the defining module with no line number)
and ``notes/_rc473_truth_repair1_cite_pass2.py`` (bare ``:NNN`` follow-ons: 189
read, 19 kept, 170 rewritten). Nothing ran either script afterwards, and a line
citation goes stale the moment its module gains a line above the cited
definition — which is how 701 of them got there.

WHAT THIS GATE IS
-----------------
Those two scripts' JUDGING rules as a test, git-free, over the live curated file:

* a FULL token ``path.py:N[-M][,…]`` plus the bare follow-ons pass 1 attaches to
  it is a GROUP; the NAMES it cites are the code-span and dotted identifiers in
  the window before it, plus the entry's own op name; every cited line must lie
  on a definition span (decorator line .. ``def`` line, or an assignment line) of
  one of those names in the one module the path resolves to;
* a BARE follow-on (``(:NNN)``, ``at :NNN``, ``, :NNN``, ``/ :NNN``) after a path
  token names the last op-shaped identifier before it, and must lie on that
  name's definition span in the prior path's module — or, when that module does
  not define the name, in the ONE package module that does (pass 2's MOVED rule).

Strict zero on anything else. The population is the ``*.py`` files under
``docs/srmech`` on disk (the scripts used ``git ls-files``; a test cannot assume a
git that reads the checkout), with build, cache and virtual-environment
directories excluded, and a path that still resolves to more than one file is
narrowed to the candidates that define a cited name, then to ``python/srmech``.

HOW IT CAN FAIL, IN THE TEST ITSELF
-----------------------------------
:func:`test_a_shifted_citation_is_judged_stale` takes a real kept citation from
the live file, moves its line number by one, and requires the judge to call it
stale; the bare-follow-on judge gets the same mutation. Non-vacuity floors
require the live file to still carry at least 100 judged groups and 10 judged
follow-ons, so an empty scan cannot read as a clean one.

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import ast
import os
import re
from collections import defaultdict
from pathlib import Path

import pytest

SR_ROOT = Path(__file__).resolve().parents[2]                     # docs/srmech
CURATED = SR_ROOT / "python" / "srmech" / "introspect" / "_tool_docs_curated.py"

_EXCLUDED_DIRS = {"__pycache__", "build", "dist", "node_modules", ".git",
                  ".venv", "venv", ".tox", ".pytest_cache"}


def _population() -> list:
    out = []
    for dirpath, dirnames, filenames in os.walk(SR_ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in _EXCLUDED_DIRS and not d.startswith("build")
                       and not d.endswith(".egg-info")]
        for name in filenames:
            if name.endswith(".py"):
                out.append(Path(dirpath, name).relative_to(SR_ROOT).as_posix())
    return sorted(out)


class _Index:
    """Per-file definition spans, read once. Mirrors the census scripts' ``index``."""

    def __init__(self, population):
        self.population = population
        self._files = {}
        self._package_defs = None

    def spans(self, rel):
        if rel not in self._files:
            src = (SR_ROOT / rel).read_text(encoding="utf-8", errors="replace")
            spans = defaultdict(list)
            try:
                for node in ast.walk(ast.parse(src)):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        lo = min([d.lineno for d in node.decorator_list] + [node.lineno])
                        spans[node.name].append((lo, node.lineno))
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                spans[target.id].append((node.lineno, node.lineno))
                    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                        spans[node.target.id].append((node.lineno, node.lineno))
            except SyntaxError:
                pass
            self._files[rel] = spans
        return self._files[rel]

    def resolve(self, spelled, names):
        s = spelled[len("docs/srmech/"):] if spelled.startswith("docs/srmech/") else spelled
        cands = sorted({t for t in self.population
                        for c in (t, t[len("python/"):] if t.startswith("python/") else "")
                        if c and (c == s or c.endswith("/" + s))})
        if len(cands) > 1:
            defining = [t for t in cands if any(n in self.spans(t) for n in names)]
            cands = defining if len(defining) >= 1 else cands
        if len(cands) > 1:
            package = [t for t in cands if t.startswith("python/srmech/")]
            cands = package if len(package) == 1 else cands
        return cands

    def owners(self, name):
        if self._package_defs is None:
            self._package_defs = defaultdict(set)
            for t in self.population:
                if t.startswith("python/srmech/"):
                    for n in self.spans(t):
                        self._package_defs[n].add(t)
        return sorted(self._package_defs.get(name, ()))


# ── pass 1: full tokens and the follow-ons attached to them ─────────────────

FULL = re.compile(rb"(?P<path>(?:[\w.-]+/)*[\w-]+\.py):(?P<lines>\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)")
ATTACHED = re.compile(rb"(?P<tick>``?)?:(?P<lines>\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)(?P=tick)?")
SPAN = re.compile(rb"``([^`]+)``|`([^`]+)`")
IDENT = re.compile(rb"[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)*")


def _names_in(window):
    out = []
    for m in SPAN.finditer(window):
        body = m.group(1) or m.group(2)
        for im in IDENT.finditer(body):
            out.append(im.group(0).decode().split(".")[-1])
    for im in IDENT.finditer(SPAN.sub(b" ", window)):
        word = im.group(0).decode()
        if "." in word or "_" in word:
            out.append(word.split(".")[-1])
    return [n for n in out if n and not n.endswith("py")]


def _parse_lines(spec):
    out = []
    for part in spec.decode().split(","):
        a, _, b = part.partition("-")
        out.append((int(a), int(b or a)))
    return out


def _string_segments(raw):
    """``(entry key, segment bytes)`` for every string constant under a ``srmech.*`` key."""
    starts = [0] + [i + 1 for i, ch in enumerate(raw) if ch == 10]
    for node in ast.walk(ast.parse(raw)):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and isinstance(key.value, str)
                    and key.value.startswith("srmech.")):
                continue
            for c in ast.walk(value):
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    a = starts[c.lineno - 1] + c.col_offset
                    b = starts[c.end_lineno - 1] + c.end_col_offset
                    yield key.value, raw[a:b]


def full_token_groups(raw):
    groups = []
    for entry, seg in _string_segments(raw):
        fulls = list(FULL.finditer(seg))
        for i, fm in enumerate(fulls):
            nxt = fulls[i + 1].start() if i + 1 < len(fulls) else len(seg)
            g = {"entry": entry, "full": fm, "bares": [], "seg": seg}
            pos = fm.end()
            while True:
                bm = ATTACHED.search(seg, pos, nxt)
                if not bm:
                    break
                gap = seg[pos:bm.start()]
                ok_gap = (len(gap) <= 48 and not re.search(rb"[.;]\s|\(\s*$|\)\s", gap)
                          and re.fullmatch(rb"[`\s/,]*(?:(?:``?[\w.()]+``?|and|or)[`\s/,]*)*", gap))
                before = seg[bm.start() - 1:bm.start()] if bm.start() else b""
                if not ok_gap or before in (b"[", b"]") or re.match(rb"\w", before or b" "):
                    break
                g["bares"].append(bm)
                pos = bm.end()
            lo = max(0, fm.start() - 200)
            if i:
                prev = groups[-1]
                lo = max(lo, prev["bares"][-1].end() if prev["bares"] else prev["full"].end())
            win = seg[lo:fm.start()]
            cut = max(win.rfind(b". "), win.rfind(b"; "), win.rfind(b" - "), win.rfind(b"\xe2\x80\x94"))
            if cut > 0:
                win = win[cut + 2:]
            tail = seg[fm.end():(g["bares"][-1].start() if g["bares"] else fm.end())]
            g["names"] = _names_in(win) + _names_in(tail)
            if i and not _names_in(win) and re.fullmatch(rb"[`\s/,]*", win) and groups[-1]["seg"] is seg:
                g["names"] = groups[-1]["names"] + g["names"]
            groups.append(g)
    return groups


def judge_group(g, index):
    """``("OK" | "STALE" | "UNRESOLVED", detail)`` by pass 1's rule."""
    fm = g["full"]
    spelled = fm.group("path").decode()
    lines = _parse_lines(fm.group("lines")) + [ln for bm in g["bares"]
                                               for ln in _parse_lines(bm.group("lines"))]
    names = list(dict.fromkeys(g["names"]))
    own = g["entry"].rsplit(".", 1)[-1]
    if own not in names:
        names.append(own)
    cands = index.resolve(spelled, names)
    if len(cands) != 1:
        return "UNRESOLVED", f"{spelled} -> {cands}"
    spans = index.spans(cands[0])
    for (x, y) in lines:
        on_def = any((x == y and lo <= x <= dline) or (x != y and x <= dline <= y)
                     for n in names for (lo, dline) in spans.get(n, ()))
        if not on_def:
            return "STALE", f"{cands[0]} line {x}{'-' + str(y) if y != x else ''} names {names[-6:]}"
    return "OK", cands[0]


# ── pass 2: bare follow-ons after any path token ────────────────────────────

PATH = re.compile(rb"(?P<path>(?:[\w.-]+/)*[\w-]+\.py)(?::\d+(?:[-,]\d+)*)?(?![\w])")
BARE = re.compile(rb"(?P<open>\(|\bat |, |/ )(?P<tick>``)?:(?P<a>\d+)(?:-(?P<b>\d+))?(?P=tick)?(?=[),;\s])")
WORD = re.compile(rb"[A-Za-z_]\w*")
STOP = {"at", "and", "or", "the", "is", "in", "eig", "s", "vs"}


def bare_followons(raw):
    rows = []
    for entry, seg in _string_segments(raw):
        paths = list(PATH.finditer(seg))
        prev = None
        for bm in BARE.finditer(seg):
            prior = [p for p in paths if p.end() <= bm.start()]
            if not prior:
                continue
            pm = prior[-1]
            before = seg[max(pm.end(), bm.start() - 90):bm.start()]
            idents = [m.group(0).decode() for m in WORD.finditer(before)]
            opshaped = [w for w in idents if "_" in w.strip("_")]
            names = opshaped[-1:] if opshaped else [w for w in idents if w not in STOP][-2:]
            if bm.group("open") == b"/ " and prev is not None and prev[0].end() + 1 >= bm.start() - 2:
                names = prev[1]
            rows.append({"entry": entry, "token": bm.group(0).decode(),
                         "path": pm.group("path").decode(), "names": names,
                         "opshaped": bool(opshaped),
                         "a": int(bm.group("a")), "b": int(bm.group("b") or bm.group("a"))})
            prev = (bm, names)
    return rows


def judge_followon(row, index):
    """``("DEF" | "STALE" | "USAGE" | "NOFILE", detail)`` by pass 2's rule."""
    cands = index.resolve(row["path"], row["names"])
    if len(cands) != 1:
        return "NOFILE", f"{row['path']} -> {cands}"
    target = cands[0]
    names = row["names"]
    if row["opshaped"] and names and not any(n in index.spans(target) for n in names):
        owners = index.owners(names[-1])
        if len(owners) == 1:
            target = owners[0]
    spans = index.spans(target)
    x, y = row["a"], row["b"]
    if any((x == y and lo <= x <= dline) or (x != y and x <= dline <= y)
           for n in names for (lo, dline) in spans.get(n, ())):
        return "DEF", target
    if any(n in spans for n in names):
        return "STALE", f"{target} line {x} is not the definition of {names}"
    return "USAGE", f"{target} line {x}: no cited name is defined there ({names})"


# ── the gate ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def live():
    if not CURATED.is_file():
        pytest.skip(f"{CURATED} absent")
    raw = CURATED.read_bytes()
    return raw, _Index(_population())


def test_every_curated_full_citation_lands_on_a_definition_it_names(live) -> None:
    raw, index = live
    groups = full_token_groups(raw)
    verdicts = [(judge_group(g, index), g) for g in groups]
    bad = [f"{g['entry']}: {g['full'].group(0).decode()} -> {v} ({d})"
           for (v, d), g in verdicts if v != "OK"]
    assert len(groups) >= 100, (
        f"only {len(groups)} full citation tokens were found in {CURATED.name}; "
        "the scan is not reading the file it was written for")
    assert not bad, (
        f"{len(bad)} of {len(groups)} curated line citation(s) no longer land on "
        "the definition they name (a line was inserted above the cited def, or the "
        "name moved):\n  " + "\n  ".join(bad[:40])
        + "\n\nRe-point each by CONTENT, or drop the line number and name the module, "
        "as notes/_rc473_truth_repair1_cite_pass1.py does; then regenerate.")


def test_every_curated_bare_followon_lands_on_its_definition(live) -> None:
    raw, index = live
    rows = bare_followons(raw)
    verdicts = [(judge_followon(r, index), r) for r in rows]
    bad = [f"{r['entry']}: {r['token']!r} after {r['path']} -> {v} ({d})"
           for (v, d), r in verdicts if v != "DEF"]
    assert len(rows) >= 10, f"only {len(rows)} bare follow-ons were found"
    assert not bad, (
        f"{len(bad)} of {len(rows)} bare `:NNN` follow-on citation(s) do not land "
        "on the definition of the name before them:\n  " + "\n  ".join(bad[:40])
        + "\n\nRe-point by content or rewrite to the module path, as "
        "notes/_rc473_truth_repair1_cite_pass2.py does; then regenerate.")


def test_a_shifted_citation_is_judged_stale(live) -> None:
    """THE CAN-FAIL, on real data: move one kept citation by a line."""
    raw, index = live
    groups = [g for g in full_token_groups(raw)
              if not g["bares"] and judge_group(g, index)[0] == "OK"
              and re.fullmatch(rb"\d+", g["full"].group("lines"))]
    assert groups, "no single-line kept citation to mutate"
    shifted_any = False
    for g in groups[:25]:
        fm = g["full"]
        n = int(fm.group("lines"))
        spans = index.spans(judge_group(g, index)[1])
        # a line that is on NO definition span of any name at all
        on_any = {ln for rows in spans.values() for (lo, dl) in rows for ln in range(lo, dl + 1)}
        for cand in (n + 1, n - 1, n + 2):
            if cand > 0 and cand not in on_any:
                mutated = dict(g)
                mutated["full"] = FULL.search(fm.group("path") + b":" + str(cand).encode())
                assert judge_group(mutated, index)[0] == "STALE", (
                    f"{g['entry']}: {fm.group(0).decode()} moved to line {cand} was not "
                    "judged stale — the gate cannot see the defect it exists for")
                shifted_any = True
                break
        if shifted_any:
            break
    assert shifted_any, "no kept citation had a non-definition neighbour line to plant"

    rows = [r for r in bare_followons(raw) if judge_followon(r, index)[0] == "DEF"]
    assert rows, "no kept bare follow-on to mutate"
    row = dict(rows[0])
    target = judge_followon(rows[0], index)[1]
    on_any = {ln for spans in index.spans(target).values()
              for (lo, dl) in spans for ln in range(lo, dl + 1)}
    for cand in (row["a"] + 1, row["a"] - 1, row["a"] + 2):
        if cand > 0 and cand not in on_any:
            row["a"] = row["b"] = cand
            assert judge_followon(row, index)[0] != "DEF", (
                "a bare follow-on moved off its definition was still judged DEF")
            return
    pytest.fail("no kept follow-on had a non-definition neighbour line to plant")
