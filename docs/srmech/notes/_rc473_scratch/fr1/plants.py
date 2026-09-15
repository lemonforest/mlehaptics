"""rc473 final repair 1: plant each regression a blocking finding named, run the gate that
must catch it (a fresh pytest per plant), restore the bytes, and prove them restored.

Usage: python plants.py <python-root> <out.ndjson> <plant>[,<plant>...] [-- <pytest prefix...>]
The pytest prefix defaults to [sys.executable, -m, pytest]. Every substitution is exact text
that must match EXACTLY ONCE, or the plant aborts with nothing written. A whole-file revert
reads its bytes from a file given as `@<path>`. Each plant is followed by a restore that must
reproduce the original bytes, and the gate is then run once more on the restored tree.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PY = Path(sys.argv[1])
OUT = Path(sys.argv[2])
NAMES = sys.argv[3].split(",")
PREFIX = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [sys.executable, "-m", "pytest"]

LEAK = "tests/test_git_env_cannot_reach_a_repository_rc473.py"
PHR = "tests/test_kepler_identity_phrases_absent_rc473.py"
RC471 = "tests/test_hook_fixture_env_isolation_rc471.py"
N_ARM1B = LEAK + "::test_the_git_writing_tests_scrub_at_their_source_without_the_suite_guard"
N_ARM2B = LEAK + "::test_the_suite_conftest_loads_the_guard_before_a_writer_runs"
N_ARM3 = LEAK + "::test_check_hooks_ledger_under_an_exported_GIT_DIR_passes_and_writes_nothing"
N_WALK = LEAK + "::test_the_walk_stops_at_a_repository_directory_nested_under_a_pointer_checkout"

PLANTS = {
    # sweep B1: ARM 3 hands check_hooks.py an argument that selects no check
    "arm3_zero_cases": ([(LEAK, '[sys.executable, str(CHECKER), "ledger"]',
                          '[sys.executable, str(CHECKER), "no-such-check"]')], [N_ARM3]),
    # can-fail B1: the rc471 helpers back to the INHERITED environment
    "m1_helpers_inherit": ([(RC471, "    return _git_plain(args, root, CH.fixture_git_env(root))\n",
                             "    return _git_plain(args, root, None)\n")], [LEAK]),
    # can-fail B1, second shape: the whole rc471 file back to its 52371629a blob (bytes from FR1_RC471_BLOB)
    "m1_file_revert": ([(RC471, None, "@" + os.environ.get("FR1_RC471_BLOB", ""))], [LEAK]),
    # can-fail B2: the suite guard's wiring removed from conftest.py
    "m2_unwire": ([("tests/conftest.py",
                    "from tests import _git_env_guard  # noqa: E402,F401  (import-time scrub)\n", "")],
                  [LEAK]),
    # can-fail B4: the walk continues past a .git directory
    "x_walk_dir": ([("tests/_git_env.py", "        if dotgit.is_dir():\n            return []\n",
                     "        if dotgit.is_dir():\n            continue\n")], [LEAK]),
    # can-fail B3, the gate's own control: the gap back to ONE backslash before n
    "gap_single_backslash": ([(PHR, '_GAP = r"(?:\\s|[*#>\\"]|\\\\+n)+"',
                               '_GAP = r"(?:\\s|[*#>\\"]|\\\\n)+"')], [PHR]),
}


def run(nodes, tag):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("SRMECH_ALLOW_STALE_NATIVE", None)
    bt = ["--basetemp=%s/%s" % (os.environ["FR1_BASETEMP"], tag)] if os.environ.get("FR1_BASETEMP") else []
    t = time.time()
    p = subprocess.run([*PREFIX, "-q", "-p", "no:cacheprovider", "-rfE", *bt, *nodes], cwd=str(PY), env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=3000)
    out = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    tally = [l for l in out.splitlines() if re.search(r"\d+ (passed|failed|error)", l)]
    failed = sorted(set(re.findall(r"^FAILED \S+::(\S+?)(?: - |$)", out, re.M)))
    return dict(exit=p.returncode, tally=(tally[-1].strip() if tally else out[-300:]), failed=failed,
                seconds=round(time.time() - t, 1)), out


def main():
    # A first run without this printed "2 passed, 9 errors" planted AND restored: pytest's
    # --basetemp does not create missing parents, so every tmp_path test errored at setup.
    # Instrument error, recorded, not counted.
    if os.environ.get("FR1_BASETEMP"):
        os.makedirs(os.environ["FR1_BASETEMP"], exist_ok=True)
        print("basetemp parent:", os.environ["FR1_BASETEMP"], "exists:", os.path.isdir(os.environ["FR1_BASETEMP"]))
    with OUT.open("a", encoding="utf-8") as fh:
        for name in NAMES:
            subs, nodes = PLANTS[name]
            saved = {}
            for rel, old, new in subs:
                path = PY / rel
                orig = saved.setdefault(rel, path.read_bytes())
                if old is None:
                    blob = Path(new[1:]).read_bytes()
                    assert blob and blob != path.read_bytes(), f"{name}: revert blob empty or equal to the tree"
                    path.write_bytes(blob)
                    continue
                text = path.read_bytes().decode("utf-8")
                n = text.count(old)
                assert n == 1, f"{name}: {rel} expected exactly one match, found {n}"
                path.write_bytes(text.replace(old, new).encode("utf-8"))
            print(f"=== {name}: planted {len(subs)} change(s) in {sorted(saved)}", flush=True)
            planted, out = run(nodes, name + "-planted")
            print(f"  PLANTED  exit={planted['exit']} {planted['tally']}  failed={planted['failed']}", flush=True)
            for line in out.splitlines():
                if line.startswith("E ") and ("WROTE" in line or "ran no cases" in line or "handed" in line
                                              or "survive" in line or "went past" in line):
                    print("   ", line[:260], flush=True)
                    break
            for rel, orig in saved.items():
                (PY / rel).write_bytes(orig)
                assert (PY / rel).read_bytes() == orig, f"{rel} not restored"
            restored, _ = run(nodes, name + "-restored")
            print(f"  RESTORED exit={restored['exit']} {restored['tally']}  bytes identical: True", flush=True)
            fh.write(json.dumps(dict(plant=name, nodes=nodes, planted=planted, restored=restored)) + "\n")


if __name__ == "__main__":
    main()
