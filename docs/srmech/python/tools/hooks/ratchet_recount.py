"""Stop / SubagentStop — re-run the status-conflation ratchet at the moment an
agent declares itself done. (rc452, `#T1166`)

WHAT IT CATCHES, MEASURED
=========================
This session's R1. ``return SRMECH_ERR_OVERFLOW`` lines rose 725 -> 739 and the
rise was delivered as an after-the-fact "residual" in a closing report. The
number is a DOWN-ONLY ceiling; a rise is the one thing it exists to forbid, and
it was discovered after the work was declared finished rather than at the
moment of declaring. Exit 2 at the emit-residuals moment is what converts
"oh by the way" into "you are not done".

THE INSTRUMENT IS THE GATE'S OWN COUNTER, NOT A GREP
====================================================
The hook runs ``tests/test_status_conflation_ratchet_rc404.py`` and nothing
else. That file strips block comments and string literals before counting,
because ``return SRMECH_ERR_OVERFLOW`` inside a ``/* ... */`` narration is
prose, not a return. A raw grep reads HIGHER than the gate — the gate's own
docstring records the raw count as 744 against its stripped 739 at the time it
was written. A hook that grepped would therefore block on a number the gate
calls green, which is a false positive by construction.

HOW "ADJUDICATED" IS DECIDED — DETERMINISTICALLY, BY THE FILE ITSELF
====================================================================
There is no marker to parse and no honor system. The gate asserts BOTH
directions::

    assert total <= CEIL_CONFLATING_RETURN_LINES   # a rise is red
    assert total == CEIL_CONFLATING_RETURN_LINES   # a FALL is also red

so the constant must equal the measured count exactly. An agent that takes the
sanctioned raise edits ``CEIL_CONFLATING_RETURN_LINES`` and writes the per-line
adjudication in the block of ``#:`` prose above it — the rc420 note is the
template the gate names. Once that edit lands the gate is green and this hook
passes. An agent that raises the count WITHOUT touching the constant leaves the
gate red and this hook blocks. "Adjudicated" versus "silent" is thus decided by
the ratchet file's own content, and the pass fixture in ``check_hooks.py`` is
this rc's REAL adjudicated state (measured CEIL 745 == 745 counted, green in
11s), while the block fixture is a REAL planted return line.

LOOP SAFETY
===========
``stop_hook_active`` is consulted. The first stop gets one block; a second stop
while a block is already in flight is allowed through with a loud warning, so
an agent cannot be wedged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

#: The gate this hook runs. Kept as a single relative path so that renaming the
#: ratchet is a one-line change here and an immediately obvious one.
GATE = "tests/test_status_conflation_ratchet_rc404.py"

#: The gate measured 11.16 s on this tree. 180 s is ~16x headroom; a timeout is
#: reported as "did not finish", never as "passed".
TIMEOUT_S = 180.0


def body(payload: Dict[str, Any]) -> int:
    root = H.repo_root()
    pyr = H.py_root(root)
    gate_path = pyr / GATE
    if not gate_path.exists():
        return H.allow([f"[ratchet-recount] {GATE} not present; nothing to check."])

    if H.stop_is_repeat(payload):
        return H.allow([
            "[ratchet-recount] WARNING: stop_hook_active is set — allowing this "
            "stop through WITHOUT re-running the ratchet to avoid a loop. "
            f"If you have not already, run: pytest {GATE} -x -q"])

    code, out = H.run(
        [H.python_exe(), "-m", "pytest", GATE, "-x", "-q"],
        cwd=pyr, timeout=TIMEOUT_S, env_extra={"PYTHONPATH": "."},
    )

    if code == 0:
        return H.allow()

    if code < 0:  # did not finish — NOT evidence of a violation
        return H.allow([
            f"[ratchet-recount] the ratchet did not finish ({out.strip()}); "
            "allowing the stop. This is not a pass — re-run it by hand: "
            f"pytest {GATE} -x -q"])

    tail = "\n".join(out.strip().splitlines()[-40:])
    return H.block([
        "BLOCKED (ratchet-recount): the status-conflation ratchet is RED, so "
        "this work is not done.",
        "",
        tail,
        "",
        "The gate's own message names the only two legitimate exits:",
        "  1. ROOT-FIX each new line — if it is a value outside a representable "
        "range, a compiled-in cap, or a non-convergent iteration, it is "
        "SRMECH_ERR_LIMIT, not OVERFLOW.",
        "  2. RAISE CEIL_CONFLATING_RETURN_LINES explicitly, with a written "
        "per-line adjudication naming each line and its provenance (the rc420 "
        "note above the constant is the template).",
        "Never re-label a CORRECT status-4 return as LIMIT to keep the number "
        "flat — caller grow-loops key on 4.",
    ])


if __name__ == "__main__":
    H.run_hook(body)
