"""rc473 final repair 1: is tests/test_ledger_write_refusals_rc469.py's failure in a GIT-FREE
extract environmental? Run the same file, the same way, in a git-free extract of the rc473 base
1ab8d405b and of the code head 5a75bf347 (Windows CPython 3.14.4, pure), normalise the extract
path out of the failure lines, and compare. Usage: python base_rc469.py"""
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
WT = r"D:/GitHub/mlehaptics/.claude/worktrees/wf_5285136b-875-6"
BASE = Path("C:/Users/sckir/rc473c_win/fr1/base")
HEAD = Path("C:/Users/sckir/rc473c_win/fr1/win/src")
env = dict(os.environ, SRMECH_EXPECT_PURE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
env.pop("SRMECH_ALLOW_STALE_NATIVE", None)
print("exported GIT_DIR/GIT_WORK_TREE:", sum(1 for k in ("GIT_DIR", "GIT_WORK_TREE") if k in os.environ))

if BASE.exists():
    shutil.rmtree(BASE)
BASE.mkdir(parents=True)
tar = BASE.with_suffix(".tar")
subprocess.run(["git", "-c", "core.autocrlf=false", "archive", "-o", str(tar), "1ab8d405b",
                "docs/srmech/python", "docs/srmech/c"], cwd=WT, check=True)
with tarfile.open(tar) as tf:
    tf.extractall(BASE, filter="data")
tar.unlink()


def run(label, root):
    py = root / "docs/srmech/python"
    libs = [p for p in py.rglob("*") if p.suffix in (".dll", ".so", ".pyd")]
    gitdirs = [p for p in [root, *root.parents] if (p / ".git").exists()]
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE",
                        "tests/test_ledger_write_refusals_rc469.py"], cwd=str(py), env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    norm = str(root).replace("/", "\\")
    lines = sorted({l.replace(norm, "<extract>") for l in out.splitlines()
                    if l.startswith("FAILED") or re.match(r"^E\s+RuntimeError", l)})
    tally = [l for l in out.splitlines() if re.search(r"\d+ (passed|failed)", l)]
    print(f"=== {label}: libs {len(libs)} .git above extract {len(gitdirs)} exit {p.returncode}: {tally[-1] if tally else '?'}")
    for l in lines:
        print("   ", l[:220])
    return lines


a = run("base 1ab8d405b", BASE)
b = run("head 5a75bf347", HEAD)
print("normalised failure lines:", len(a), "/", len(b), "IDENTICAL" if a == b else "DIFFER")
# A first run of this script printed DIFFER with the lines shown identical to 220 characters:
# print WHERE they differ, and compare the failing node set separately.
fa = [l for l in a if l.startswith("FAILED")]
fb = [l for l in b if l.startswith("FAILED")]
print("failing node set:", "IDENTICAL" if fa == fb else "DIFFER", len(fa), "/", len(fb))
ea = [l for l in a if not l.startswith("FAILED")]
eb = [l for l in b if not l.startswith("FAILED")]
for x, y in zip(ea, eb):
    k = 0
    while k < min(len(x), len(y)) and x[k] == y[k]:
        k += 1
    print("E line: common prefix", k, "chars, ending:", repr(x[max(0, k - 80):k]))
    print("   base continues:", repr(x[k:k + 400]))
    print("   head continues:", repr(y[k:k + 400]))
