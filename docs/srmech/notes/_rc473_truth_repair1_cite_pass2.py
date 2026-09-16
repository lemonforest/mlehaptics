"""rc473 truth repair 1 — pass 2: the BARE `:NNN` follow-ons.

A bare `(:NNN)` / `(``:NNN``)` / `at :NNN` / `/ :NNN` cites a line of the file named
by the most recent `path.py` token earlier in the same string constant (with or
without its own line number). The cited NAME is the identifier just before it.
Each is judged:
  DEF      NNN is in the decorator..def span (or is the assignment line) of the name
  STALE    the name is defined in the file and NNN is not its definition
           -> `:NNN` becomes that file (`at :NNN` -> `in <file>`)
  MOVED    the name is not in the prior path's file but in exactly one package
           module -> judged there; stale -> that module's path
  USAGE    no identifier before it names a definition anywhere (a usage citation:
           "diagonalising H once (:166)"): printed with the cited line for a hand
           verdict; rewritten to the prior path only when listed in USAGE_STALE
Adjacent duplicates produced by a rewrite (`(X / X)`) collapse to one.
Usage: python r1_cite_bare.py <docs/srmech> <report.tsv> [--apply]
"""
import ast
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(sys.argv[1]).resolve()
REPORT = Path(sys.argv[2])
APPLY = "--apply" in sys.argv
CUR = BASE / "python" / "srmech" / "introspect" / "_tool_docs_curated.py"
tracked = subprocess.run(["git", "ls-files", "--", "*.py"], cwd=BASE, capture_output=True, check=True,
                         text=True).stdout.split()
# (entry, bare token as matched) whose cited line was read by hand and holds neither
# the definition nor the code the sentence describes (r1_bare_inspect.py output).
USAGE_STALE = {
    ("srmech.physics.qm.potentials.harmonic_oscillator_ladder", "at :189"),
    ("srmech.physics.qm.potentials.hydrogen_radial", "at :123"),
    ("srmech.physics.qm.pseudo_hermitian.construct_eta_from_eigendecomposition", "(:190"),
    ("srmech.physics.qm.pseudo_hermitian.is_pseudo_hermitian", "(:288"),
    ("srmech.physics.qm.pseudo_hermitian.pseudo_hermitian_eigenvalues_real", "at :237"),
    ("srmech.physics.qm.relativistic.charge_conjugation_matrix", "(:281"),
    ("srmech.physics.qm.relativistic.charge_conjugation_matrix", "/ :292"),
    ("srmech.physics.qm.relativistic.gamma_matrices", "(:227"),
    ("srmech.physics.qm.single_particle.heisenberg_evolve", "(:166"),
    ("srmech.physics.qm.single_particle.liouville_evolve", "at :252"),
}
# heisenberg_evolve's "commutator (:129)" follows a laplacian.py token; line 129 of
# laplacian.py is an import, and the commutator this sentence means is the sibling in
# srmech/physics/qm/single_particle.py (several modules define a `commutator`).
FORCE = {("srmech.physics.qm.single_particle.heisenberg_evolve", "(:129"): "srmech/physics/qm/single_particle.py"}
FILES = {}


def index(rel):
    if rel not in FILES:
        src = (BASE / rel).read_text(encoding="utf-8", errors="replace")
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


def resolve_path(spelled, names):
    s = spelled[len("docs/srmech/"):] if spelled.startswith("docs/srmech/") else spelled
    out = sorted({t for t in tracked for c in (t, t[7:] if t.startswith("python/") else "")
                  if c and (c == s or c.endswith("/" + s))})
    if len(out) > 1:
        o2 = [t for t in out if any(n in index(t)[1] for n in names)]
        out = o2 if len(o2) == 1 else out
    return out


def owners(name):
    return sorted({t for t in tracked if t.startswith("python/srmech/") and name in index(t)[1]})


PATH = re.compile(rb"(?P<path>(?:[\w.-]+/)*[\w-]+\.py)(?::\d+(?:[-,]\d+)*)?(?![\w])")
BARE = re.compile(rb"(?P<open>\(|\bat |, |/ )(?P<tick>``)?:(?P<a>\d+)(?:-(?P<b>\d+))?(?P=tick)?(?=[),;\s])")
IDENT = re.compile(rb"[A-Za-z_]\w*")
STOP = {"at", "and", "or", "the", "is", "in", "eig", "s", "vs"}

raw = CUR.read_bytes()
starts = [0] + [i + 1 for i, ch in enumerate(raw) if ch == 10]
tree = ast.parse(raw)
rows, edits, tally = [], [], Counter()
for node in ast.walk(tree):
    if not isinstance(node, ast.Dict):
        continue
    for k, v in zip(node.keys, node.values):
        if not (isinstance(k, ast.Constant) and isinstance(k.value, str) and k.value.startswith("srmech.")):
            continue
        for c in ast.walk(v):
            if not (isinstance(c, ast.Constant) and isinstance(c.value, str)):
                continue
            a0 = starts[c.lineno - 1] + c.col_offset
            seg = raw[a0:starts[c.end_lineno - 1] + c.end_col_offset]
            paths = list(PATH.finditer(seg))
            prev_bare = None
            for bm in BARE.finditer(seg):
                prior = [p for p in paths if p.end() <= bm.start()]
                if not prior:
                    continue
                pm = prior[-1]
                tok = bm.group(0).decode()
                # "(:281 / :292)": the second follow-on shares the first one's name
                before = seg[max(pm.end(), bm.start() - 90):bm.start()]
                idents = [m.group(0).decode() for m in IDENT.finditer(before)]
                opshaped = [x for x in idents if "_" in x.strip("_")]
                # the cited name is the last op-shaped identifier before the follow-on
                # ("gamma_5 comes out OFF-diagonal (:227)" cites gamma_5); with none,
                # the last two words are kept only to show the usage in the report
                names = opshaped[-1:] if opshaped else [x for x in idents if x not in STOP][-2:]
                if bm.group("open") == b"/ " and prev_bare is not None and prev_bare[0].end() + 1 >= bm.start() - 2:
                    names = prev_bare[1]
                spell = pm.group("path")
                cands = resolve_path(spell.decode(), names)
                x = int(bm.group("a"))
                y = int(bm.group("b") or x)
                verdict, target = "NOFILE", None
                if len(cands) == 1:
                    target = cands[0]
                    if opshaped and names and not any(n in index(target)[1] for n in names):
                        own = owners(names[-1])
                        if len(own) == 1:
                            target, spell = own[0], own[0][len("python/"):].encode()
                    L, spans = index(target)
                    defn = any((x == y and lo <= x <= dl) or (x != y and x <= dl <= y)
                               for n in names for (lo, dl) in spans.get(n, ()))
                    if defn:
                        verdict = "DEF"
                    elif any(n in spans for n in names):
                        verdict = "STALE" if spell == pm.group("path") else "MOVED-STALE"
                    elif (k.value, tok) in FORCE:
                        # read by hand: the name has several owners and the sentence's
                        # module is named below; the cited line is not its definition
                        spell = FORCE[(k.value, tok)].encode()
                        target = "python/" + FORCE[(k.value, tok)]
                        L, spans = index(target)
                        verdict = "DEF" if any(lo <= x <= dl for n in names for (lo, dl) in spans.get(n, ())) else "FORCED-STALE"
                    else:
                        verdict = "USAGE-STALE" if (k.value, tok) in USAGE_STALE else "USAGE"
                tally[verdict] += 1
                ctx = seg[max(0, bm.start() - 70):bm.end() + 12].decode(errors="replace").replace("\n", "\\n").replace("\t", " ")
                line = "?"
                if target:
                    LL = index(target)[0]
                    line = LL[x - 1].strip()[:70] if 0 < x <= len(LL) else "past EOF"
                rows.append("\t".join([verdict, k.value, tok, spell.decode(), str(target), ",".join(names),
                                       line, ctx]))
                prev_bare = (bm, names)
                if verdict in ("STALE", "MOVED-STALE", "USAGE-STALE", "FORCED-STALE"):
                    tick = bm.group("tick") or b""
                    op = bm.group("open")
                    if op == b"at ":
                        s0, pre = bm.start(), b"in "
                    else:
                        s0, pre = bm.start() + len(op), b""
                    edits.append((a0 + s0, a0 + bm.end(), pre + tick + spell + tick))
REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")
print("bare follow-ons with a prior path token:", sum(tally.values()), dict(tally))
if APPLY:
    out = bytearray(raw)
    for s0, e0, nb in sorted(edits, reverse=True):
        out[s0:e0] = nb
    res = bytes(out)
    # a rewrite can leave "(``p.py`` / ``p.py``)" or "(p.py / p.py)": collapse to one
    dup = re.compile(rb"(?P<t>``)?(?P<p>(?:[\w.-]+/)*[\w-]+\.py)(?P=t) / (?P=t)(?P=p)(?P=t)(?![\w/])")
    n_dup = len(dup.findall(res))
    res = dup.sub(lambda m: (m.group("t") or b"") + m.group("p") + (m.group("t") or b""), res)
    CUR.write_bytes(res)
    print("WROTE", len(edits), "rewrites,", n_dup, "duplicate pairs collapsed; bytes", len(raw), "->", len(res),
          "CR", raw.count(b"\r"), "->", res.count(b"\r"))
