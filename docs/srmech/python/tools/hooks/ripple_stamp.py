"""Run ``tools/ripple_check.py`` and record the verdict against a commit.

    python3 tools/hooks/ripple_stamp.py            # run the sweep, stamp it
    python3 tools/hooks/ripple_stamp.py --show     # print the current stamp

This is the writer half of ``ripple_stamp_before_push.py``. It exists so the
push hook can ask a decidable question — "was the sweep run, at THIS commit,
and did it pass?" — instead of trusting a recollection.

THE STAMP LIVES IN ``.git/``
===========================
``<repo>/.git/srmech_ripple_stamp.json``. Inside ``.git`` it can never be
accidentally staged, needs no ``.gitignore`` entry, and is correctly per-clone:
a sweep run in one worktree does not vouch for another.

WHAT IS RECORDED
================
``{"sha": <HEAD at the time of the run>, "status": <ripple_check exit code>,
"finished_at": <unix ts>, "argv": [...], "failed": <n or null>}``.

The sha is captured AFTER the sweep finishes, and the hook requires it to equal
HEAD at push time. Any commit made after the sweep invalidates the stamp, which
is the intended semantics: the sweep vouches for a tree, not for an intention.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

STAMP_REL = Path(".git") / "srmech_ripple_stamp.json"

#: ripple_check.py reports "12 failed / 2065 passed"; captured for the record.
_FAILED = re.compile(r"(\d+)\s+failed")


def stamp_path(root: Path) -> Path:
    return root / STAMP_REL


def main(argv: list[str]) -> int:
    root = H.repo_root()
    pyr = H.py_root(root)
    sp = stamp_path(root)

    if "--show" in argv:
        if not sp.is_file():
            print(f"no stamp at {sp}")
            return 1
        print(sp.read_text(encoding="utf-8"))
        return 0

    passthrough = [a for a in argv if a != "--show"]
    print(f"running ripple_check.py {' '.join(passthrough)} (this takes ~27 min)",
          file=sys.stderr)
    code, out = H.run(
        [H.python_exe(), "tools/ripple_check.py", *passthrough],
        cwd=pyr, timeout=4 * 60 * 60, env_extra={"PYTHONPATH": "."},
    )
    sys.stdout.write(out)

    rc, sha_out = H.git(["rev-parse", "HEAD"], cwd=root)
    sha = sha_out.strip() if rc == 0 else ""

    m = _FAILED.search(out)
    record = {
        "sha": sha,
        "status": code,
        "finished_at": int(time.time()),
        "argv": passthrough,
        "failed": int(m.group(1)) if m else None,
    }
    try:
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"stamped {sp} status={code} sha={sha[:12]}", file=sys.stderr)
    except OSError as exc:
        print(f"could not write stamp: {exc}", file=sys.stderr)
        return code or 1
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
