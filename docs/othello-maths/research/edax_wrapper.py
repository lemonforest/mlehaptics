"""Phase 1c.4 — edax subprocess wrapper.

Thin adapter around the upstream ``edax`` Othello engine
(github.com/abulmo/edax-reversi).  Our Python code feeds edax a
position in OBF format plus a requested search depth, and gets back
(best_move, score_centidiscs).

Install notes for the user
--------------------------
Prebuilt Windows binaries are available on the upstream GitHub
releases page.  On Linux: ``git clone
https://github.com/abulmo/edax-reversi && cd edax-reversi/src
&& make -j build BUILD=OPTIMIZED`` plus downloading the evaluation
weights (``eval.dat``).  The README explains placement.

Path configuration
------------------
The runner reads the edax executable path from, in order:

    1. ``--edax-path`` CLI flag (if present)
    2. ``EDAX_PATH`` environment variable
    3. ``edax`` on the system PATH (``which edax``)

If none of these resolve, the wrapper raises a clear
``EdaxNotFoundError`` that the caller can catch and turn into a
"install required" message (see ``a1_depth_gap_runner.py`` for the
reference pattern).

edax text protocol
------------------
We use edax's "script mode" (-n 1 -l DEPTH -solve) invocations
per position.  That is simpler to parse than the interactive
protocol and avoids state carry-over between positions.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


class EdaxNotFoundError(RuntimeError):
    pass


def resolve_edax_path(explicit: str | None = None) -> Path:
    """Find the edax executable.  See module docstring for order."""
    if explicit:
        p = Path(explicit)
        if not p.exists():
            raise EdaxNotFoundError(
                f"--edax-path points to a nonexistent file: {p}"
            )
        return p
    env_path = os.environ.get("EDAX_PATH")
    if env_path:
        p = Path(env_path)
        if not p.exists():
            raise EdaxNotFoundError(
                f"EDAX_PATH env var points to a nonexistent file: {p}"
            )
        return p
    which = shutil.which("edax")
    if which:
        return Path(which)
    raise EdaxNotFoundError(
        "edax executable not found.  Set the EDAX_PATH environment "
        "variable to the full path of the edax binary, or pass "
        "--edax-path.  See research/edax_wrapper.py docstring for "
        "install instructions."
    )


_SCORE_RE = re.compile(
    r"(?:score|value)\s*[:=]?\s*(-?\d+)", re.IGNORECASE
)
_MOVE_RE = re.compile(r"\b(?:best\s*move|move)\s*[:=]?\s*([a-h][1-8])",
                       re.IGNORECASE)
# Edax printout line: "depth X score Y move ZZ ..."
_LINE_RE = re.compile(
    r"^\s*(?P<depth>\d+)\s+(?P<score>[+-]?\d+).*?(?P<move>[a-h][1-8])"
)


class EdaxResult:
    def __init__(
        self,
        depth: int,
        score: int,
        best_move: str | None,
        raw_stdout: str,
        raw_stderr: str,
    ) -> None:
        self.depth = depth
        self.score = score
        self.best_move = best_move
        self.raw_stdout = raw_stdout
        self.raw_stderr = raw_stderr

    def __repr__(self) -> str:
        return (
            f"EdaxResult(depth={self.depth}, score={self.score}, "
            f"best_move={self.best_move!r})"
        )


def evaluate(
    obf: str,
    depth: int,
    edax_path: Path,
    timeout_s: float = 600.0,
) -> EdaxResult:
    """Evaluate a single OBF position at requested search depth.

    Uses edax in "solve a given position from a problem file" mode
    with a single-line .obf input file piped via stdin.  Returns the
    principal-variation score for the side to move.
    """
    # Write the position to a temp file because some edax builds
    # only accept a file path, not stdin.
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".obf", delete=False
    ) as tf:
        tf.write(obf + "\n")
        tf_path = tf.name
    try:
        cmd = [
            str(edax_path),
            "-solve", tf_path,
            "-level", str(depth),
            "-n", "1",
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            # edax must run from a dir containing eval.dat; we assume
            # the user has placed eval.dat next to the binary (upstream
            # default).  The working directory defaults to edax's
            # parent dir.
            cwd=str(edax_path.parent),
        )
    finally:
        try:
            os.unlink(tf_path)
        except OSError:
            pass

    if proc.returncode != 0:
        raise RuntimeError(
            f"edax exited with code {proc.returncode}.  "
            f"stderr:\n{proc.stderr[:400]}"
        )

    # Parse: edax's solve output has one result line per position,
    # formatted roughly as:
    #   depth score move ...
    # e.g. "    20    -2       d3 ...  elapsed ..."
    score = None
    best_move = None
    observed_depth = None
    for line in proc.stdout.splitlines():
        m = _LINE_RE.match(line)
        if m:
            observed_depth = int(m.group("depth"))
            score = int(m.group("score"))
            best_move = m.group("move")
            break
    if score is None:
        # Fallback parser: look for "score = N" or "value = N"
        sm = _SCORE_RE.search(proc.stdout)
        if sm:
            score = int(sm.group(1))
        mm = _MOVE_RE.search(proc.stdout)
        if mm:
            best_move = mm.group(1).lower()
    if score is None:
        raise RuntimeError(
            "could not parse edax score from output:\n"
            + proc.stdout[:800]
        )
    return EdaxResult(
        depth=observed_depth if observed_depth is not None else depth,
        score=score,
        best_move=best_move,
        raw_stdout=proc.stdout,
        raw_stderr=proc.stderr,
    )


def smoke_test(edax_path: Path) -> bool:
    """Evaluate the starting position at depth 1; True if anything
    parses."""
    starting = (
        "---------------------------OX------XO--------------------------- X;"
    )
    try:
        result = evaluate(starting, depth=1, edax_path=edax_path)
        return result.score is not None
    except Exception as exc:
        print(f"smoke test failed: {exc}", file=sys.stderr)
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Check that edax is installed and responsive at depth 1.
  python research/edax_wrapper.py --smoke

  # Evaluate a single OBF position at depth 10.
  python research/edax_wrapper.py \\
      --obf '---------------------------OX------XO--------------------------- X;' \\
      --depth 10
""",
    )
    parser.add_argument(
        "--edax-path", default=None,
        help="Path to the edax binary.  Overrides EDAX_PATH env var.",
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help="Run a smoke test: evaluate the starting position at "
             "depth 1 and report whether the wrapper parsed a score.",
    )
    parser.add_argument(
        "--obf", default=None,
        help="Single OBF position string to evaluate.",
    )
    parser.add_argument(
        "--depth", type=int, default=10,
        help="Edax search depth (or solve level).  Default: 10.",
    )
    args = parser.parse_args()

    try:
        edax = resolve_edax_path(args.edax_path)
    except EdaxNotFoundError as exc:
        print(f"[edax_wrapper] {exc}", file=sys.stderr)
        sys.exit(2)

    if args.smoke:
        ok = smoke_test(edax)
        print(f"edax smoke test: {'PASS' if ok else 'FAIL'}")
        sys.exit(0 if ok else 1)
    if args.obf:
        r = evaluate(args.obf, args.depth, edax)
        print(r)
        sys.exit(0)
    parser.print_help()
