#!/usr/bin/env python3
"""rcdiff.py — the standing post-rcN check. Run this after EVERY srmech rc bump.

WHY THIS EXISTS. The research branch forked at rc256 and did not merge for 119 commits, so it carried its own
vendored copy of a surface `main` had deleted. Nothing looked broken from inside the branch — the probes ran
green against the private copy — and the drift only surfaced when issue #1454 was relayed from another session.
By then 179 files called an op that no longer existed. **A version bump is a two-way event and neither
direction was being watched:**

  REMOVED / RENAMED upstream -> our code silently breaks (we find out only when something is run, and 96.6 %
                               of the research tree is print-only with no test, so mostly we never run it)
  ADDED upstream            -> often an op WE asked for or prototyped here (CDRegister, cd_navmap,
                               cd_navmap_is_signed_permutation all landed after this branch built them by
                               hand). Not noticing means we keep maintaining a local version of something
                               that is now shipped and better-tested.

So the check is symmetric on purpose: what BROKE (act now) and what was ADOPTED (delete our copy).

USAGE
    python3 rcdiff.py <old_python> <new_python> [--scan DIR]

    python3 rcdiff.py /tmp/srmech_rc297/bin/python3 /tmp/srmech_new/bin/python3 --scan .

It introspects both interpreters' srmech surfaces, diffs them, and — if --scan is given — reports how many
files in the research tree call each REMOVED symbol, so the breakage has a number attached rather than an
adjective.

Deliberately introspection-based, not CHANGELOG-based: the changelog is prose written by a human and can omit
things, whereas `dir()` over the live package cannot. Read the CHANGELOG too — for the WHY — but let this
decide the WHAT.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

PROBE = r"""
import json, pkgutil, importlib, srmech
surface = {}
for m in pkgutil.walk_packages(srmech.__path__, "srmech."):
    if ".tests" in m.name:
        continue
    try:
        mod = importlib.import_module(m.name)
    except Exception:
        continue
    for n in dir(mod):
        if n.startswith("_"):
            continue
        surface.setdefault(n, []).append(m.name)
consts = {}
try:
    from srmech.amsc import cascade
    for c in ("CD_DIMS", "CD_MAX_DIM"):
        if hasattr(cascade, c):
            consts[c] = repr(getattr(cascade, c))
except Exception:
    pass
print(json.dumps({"version": srmech.__version__, "surface": sorted(surface), "consts": consts}))
"""


def introspect(py):
    out = subprocess.run([py, "-c", PROBE], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("introspection failed for %s:\n%s" % (py, out.stderr[-600:]))
    return json.loads(out.stdout)


def call_sites(root, names):
    """How many files CALL each removed name — an AST count, so a mention in prose does not inflate it."""
    counts = {n: [] for n in names}
    for p in sorted(Path(root).rglob("*.py")):
        try:
            tree = ast.parse(p.read_text())
        except (SyntaxError, UnicodeDecodeError):
            continue
        used = set()
        for node in ast.walk(tree):
            f = node.func if isinstance(node, ast.Call) else None
            if isinstance(f, ast.Attribute) and f.attr in counts:
                used.add(f.attr)
            elif isinstance(f, ast.Name) and f.id in counts:
                used.add(f.id)
        for u in used:
            counts[u].append(p.name)
    return counts


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    old, new = introspect(argv[0]), introspect(argv[1])
    scan = None
    if "--scan" in argv:
        scan = argv[argv.index("--scan") + 1]

    o, n = set(old["surface"]), set(new["surface"])
    removed, added = sorted(o - n), sorted(n - o)

    print("=== srmech %s -> %s ===" % (old["version"], new["version"]))
    for k in sorted(set(old["consts"]) | set(new["consts"])):
        a, b = old["consts"].get(k), new["consts"].get(k)
        if a != b:
            print("  CONST CHANGED  %-12s %s -> %s" % (k, a, b))

    print("\n--- REMOVED / RENAMED (%d) — these BREAK our code ---" % len(removed))
    if removed and scan:
        hits = call_sites(scan, removed)
        for r in removed:
            files = hits.get(r, [])
            mark = "  <-- BREAKS %d FILES" % len(files) if files else ""
            print("  %-42s %s%s" % (r, len(files), mark))
    else:
        for r in removed:
            print("  %s" % r)
    if not removed:
        print("  none")

    print("\n--- ADDED (%d) — check whether any was ADOPTED FROM HERE ---" % len(added))
    for a in added:
        print("  %s" % a)
    if not added:
        print("  none")

    print("\nNEXT: migrate every REMOVED symbol that has call sites; for each ADDED symbol, ask whether we")
    print("still maintain a local hand-rolled version that should now be deleted in its favour.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
