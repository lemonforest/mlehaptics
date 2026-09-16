"""The A6 phrase gate, RUN — because a detector nothing runs is this rc's subject.

`notes/_rc473_a6_phrase_gate.py` scans the surfaces that ship for twelve
phrases rc473 MEASURED false, and classifies each hit as LIVE or as quoted
inside its own correction. It was written as a script, and the A3a gate beside
it is a script too — which is the precedent, and also the shape this whole rc
is about: `c/JPL_AUDIT.md` recorded Rule 7 as "Violations: 0 / Pass" for a rule
with no detector, and four of this pass's own sentences survived six commits
because nothing read them mechanically.

So the script is imported and run here, in `pytest tests/`, which
`build-and-test` runs on ubuntu-latest, macos-14 and windows-latest.

WHAT THIS IS NOT. It is not a style rule about wording. Each phrase is a claim
the tree can decide against itself — "Ratchet unshipped" against four
`test_rule_7_*` functions, "carries no RULE_7 symbol at all" against 32
occurrences of that symbol, `theta_res` "equal to the fold grids' common
resolution" against a measured 8.04e-21-per-turn drift. A LIVE hit means a
shipped surface asserts something the tree contradicts.

WHY IT IS NOT STRICT-ZERO ON HITS. This tree keeps superseded sentences and
corrects them in place rather than deleting them
(`[[feedback_no_doctoring_ssot_use_sublanguage_kernels]]`), so the corrections
necessarily QUOTE the false claim. A zero-tolerance count would force those
notes to be deleted — the one outcome the convention exists to prevent. The
gate therefore counts LIVE and CORRECTED separately and this file asserts
strict zero on LIVE only.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SR_ROOT = _HERE.parent.parent            # docs/srmech
_GATE = _SR_ROOT / "notes" / "_rc473_a6_phrase_gate.py"

# `notes/` is NOT in python/pyproject.toml's sdist.include, so in an
# sdist-installed cell this file does not exist while the surfaces it scans
# partly do. Same discipline as test_jpl_audit.py's `_C_TEST_DIR.exists()`
# skip: an absent generator is a cell fact, not a failure.
pytestmark = pytest.mark.skipif(
    not _GATE.exists(),
    reason=f"{_GATE} absent (sdist-installed cell: notes/ is not shipped)",
)


def _load_gate():
    spec = importlib.util.spec_from_file_location("_rc473_a6_phrase_gate", _GATE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_no_shipped_surface_asserts_a_phrase_this_rc_measured_false() -> None:
    """Strict zero on LIVE. CORRECTED hits are the record and are allowed."""
    gate = _load_gate()
    rows, tally = gate.scan(_SR_ROOT)
    live = [r for r in rows if r.get("verdict") == "LIVE"]
    assert not live, (
        f"{len(live)} shipped surface(s) assert a phrase this rc measured "
        "FALSE, with no correction marker in the same paragraph:\n  "
        + "\n  ".join(
            f"{r['file']}:{r['paragraph_line']} [{r['phrase']}] x{r['hits']}"
            for r in live
        )
        + "\n\nCorrect the sentence. Do NOT delete this gate, and do NOT delete "
        "a correction note to make the count zero — a quoted, corrected phrase "
        "is the record and is counted separately on purpose. If the claim has "
        "genuinely become TRUE again, remove its entry from PHRASES with the "
        "measurement that says so."
    )


def test_the_gate_is_not_vacuous() -> None:
    """It must still FIND the phrases, as quotations, or it is not looking.

    The corrections above quote every falsified sentence. If the CORRECTED
    tally ever falls to zero, either the record was deleted or the scanner
    stopped matching — and a scanner that finds nothing reports exactly the
    same number as a clean tree. This is the same non-vacuity discipline
    `test_rule_7_detector_is_not_vacuous` applies one file over.
    """
    gate = _load_gate()
    _rows, tally = gate.scan(_SR_ROOT)
    corrected = sum(counts["corrected"] for counts in tally.values())
    assert corrected >= 6, (
        "the A6 phrase gate found fewer than six quoted-and-corrected hits "
        f"(found {corrected}). Either the correction notes were removed — "
        "which doctors the record — or the scanner has stopped matching. "
        "Both report the same LIVE count as a clean tree, which is why this "
        "assertion exists."
    )


def test_the_normalisation_is_load_bearing() -> None:
    """At least one phrase must be INVISIBLE to a single-line grep.

    The whole reason this gate exists is that both rc473 scoping plans shipped
    a single-line `grep` for a line-wrapped phrase and would have reported
    their step green over three live falsehoods. If every phrase were visible
    to a naive line scan, the normalisation would be decoration.
    """
    gate = _load_gate()
    _rows, tally = gate.scan(_SR_ROOT)
    wrapped = [
        name for name, counts in tally.items()
        if counts["corrected"] + counts["live"] > counts["naive_single_line"]
    ]
    assert wrapped, (
        "every phrase this gate matches is also visible to a single-line "
        "grep, so the whitespace normalisation is currently decoration. That "
        "is not a failure of the tree — but it means this gate no longer "
        "demonstrates the defect it was written for, and the next person "
        "should know that before trusting it to catch a wrapped one."
    )
