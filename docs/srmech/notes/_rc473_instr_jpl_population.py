"""rc473 instrument round (`#T1188`): the C function population the JPL audit counts,
at a base revision and at this checkout, differenced by (file, function).

``tools/hooks/check_hooks.py`` pins ``jpl_audit_gate.py --selftest``'s
``_scan_functions() total`` line as a vacuity literal. It read 3598 through rc473
while the selftest printed more; this prints where the difference is, with the
audit's OWN scanner (``tests/test_jpl_audit.py::_scan_functions``) run over both
trees, so the re-pin cites a derivation rather than a number.

Read-only. The base tree's ``c/src/*.c`` are read with ``git ls-tree`` / ``git show``
through ``tests/_git_env.py`` (scrubbed child environment, per-invocation location),
into a temporary directory that is removed afterwards. numpy-free; no hashlib; no abs().

Usage (from docs/srmech/python):  python3 ../notes/_rc473_instr_jpl_population.py [BASE_REV]
BASE_REV defaults to b398b8c46 (rc472, the merge-base of rc473 and main).
"""
import importlib.util
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

PY_ROOT = Path.cwd()
sys.path.insert(0, str(PY_ROOT))
from tests import _git_env  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else "b398b8c46"
C_SRC = PY_ROOT.parent / "c" / "src"


def git(args):
    proc = subprocess.run(_git_env.git_argv(PY_ROOT, args), cwd=str(PY_ROOT),
                          env=_git_env.scrubbed(), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} exited {proc.returncode}: "
                         f"{proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout


spec = importlib.util.spec_from_file_location("jpl_scanner", PY_ROOT / "tests" / "test_jpl_audit.py")
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


def population(directory):
    counts = Counter()
    files = sorted(Path(directory).glob("*.c"))
    for f in files:
        for name, _lines, _asserts in scanner._scan_functions(f):
            counts[(f.name, name)] += 1
    return len(files), counts


listing = git(["ls-tree", "--name-only", BASE, "--", "../c/src/"]).decode("utf-8").split()
print("base", BASE, git(["rev-parse", BASE]).decode().strip(), "c/src .c blobs:",
      sum(1 for p in listing if p.endswith(".c")))
print("head", git(["rev-parse", "HEAD"]).decode().strip(),
      "tracked changes under ../c/src:",
      len(git(["status", "--porcelain", "--untracked-files=no", "--", "../c/src"]).splitlines()))
with tempfile.TemporaryDirectory() as td:
    for rel in listing:
        if rel.endswith(".c"):
            (Path(td) / Path(rel).name).write_bytes(git(["show", f"{BASE}:{rel}"]))
    n_base, base = population(td)
n_head, head = population(C_SRC)
print(f"base: {n_base} .c files, {sum(base.values())} functions")
print(f"head: {n_head} .c files, {sum(head.values())} functions")
added = sorted((head - base).elements())
removed = sorted((base - head).elements())
print(f"added {len(added)} removed {len(removed)} net {len(added) - len(removed)}")
for f, name in added:
    print("  +", f, "::", name)
for f, name in removed:
    print("  -", f, "::", name)
