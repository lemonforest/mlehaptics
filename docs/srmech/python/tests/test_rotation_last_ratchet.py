"""Rotation-last classification ratchet (rc20; the rotation-last audit rc-A).

The avoidable-only criterion
----------------------------
A "rotation" here means a continuous / frame / float projection step (an FPU
last-mile readout). The srmech cascade discipline is **rotation-LAST**: keep the
body bit-exact on the exact substrate (integer add / sub / mul / floor-divmod,
or exact (num, den) rationals) and perform the single continuous projection ONCE,
terminally — the canonical example being ``pi_chudnovsky_digits`` (exact-integer
Chudnovsky body, ONE terminal isqrt+divide+render).

A mid-body rotation is a VIOLATION **only when an exact-substrate rotation-last
form is achievable** — i.e. it is *avoidable*. When the quantity is intrinsically
transcendental / float (the FPU last-mile cannot be deferred to a single terminal
step on any exact substrate), a per-step float touch is **PRIMITIVE_NA** — an
intrinsic-float LIMIT, not an avoidable violation. Examples: the two-sided
Pfaff-Archimedes ``pi_cascade_digits`` chiral pair (a per-step integer isqrt, and
pi is transcendental), and the iterative float eigensolvers (Jacobi / Fiedler /
JADE), which have no exact-substrate closed form.

This file is the **down-only** ledger for that audit. The single guard that
matters is: ``AVOIDABLE_VIOLATION`` count must stay **0**. The rc20 audit found
and removed the only avoidable violation (the naive linear single-bound
hexagon-doubling ``pi_cascade_digits``, which fed one rational sqrt into the next
radicand at every step where the two-sided bracket — or Chudnovsky — is exact).
No cascade may rotate mid-body when an exact-substrate rotation-last form is
achievable.

Buckets:
  CANONICAL          — rotation-last on the exact substrate (the discipline met)
  PRIMITIVE_NA       — intrinsic-float limit (FPU last-mile); not an avoidable
                       violation, the rotation cannot be deferred on any substrate
  AVOIDABLE_VIOLATION— a mid-body rotation where an exact-substrate form IS
                       achievable. MUST be 0 (down-only; this is the whole point).
"""
from __future__ import annotations

import json
from pathlib import Path

# The ledger lives next to this test; the `file` paths it lists are relative to
# the srmech package root (python/srmech/...), i.e. one level up from tests/.
_LEDGER = Path(__file__).resolve().parent / "rotation_last_classification.ndjson"
_PKG_ROOT = Path(__file__).resolve().parent.parent  # python/

_VALID_VERDICTS = {"AVOIDABLE_VIOLATION", "CANONICAL", "PRIMITIVE_NA"}


def _load_ledger() -> list[dict]:
    """Parse the NDJSON ledger into a list of record dicts."""
    assert _LEDGER.exists(), f"rotation-last ledger missing: {_LEDGER}"
    records: list[dict] = []
    with _LEDGER.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            rec = json.loads(line)
            assert isinstance(rec, dict), (
                f"ledger line {lineno}: expected a JSON object, got "
                f"{type(rec).__name__}"
            )
            for key in ("op", "file", "verdict", "note"):
                assert key in rec, (
                    f"ledger line {lineno}: missing required key {key!r}"
                )
            assert rec["verdict"] in _VALID_VERDICTS, (
                f"ledger line {lineno}: bad verdict {rec['verdict']!r}; "
                f"must be one of {sorted(_VALID_VERDICTS)}"
            )
            records.append(rec)
    return records


def test_no_avoidable_rotation_last_violations() -> None:
    """THE down-only guard: zero avoidable rotation-last violations.

    A mid-body rotation is a violation ONLY when an exact-substrate
    rotation-last form is achievable; intrinsic-float is the FPU last-mile
    PRIMITIVE_NA. The rc20 audit removed the only avoidable violation (the
    linear single-bound Archimedes ``pi_cascade_digits``). This count may
    only go DOWN; it must never rise above 0.
    """
    records = _load_ledger()
    offenders = [r for r in records if r["verdict"] == "AVOIDABLE_VIOLATION"]
    assert len(offenders) == 0, (
        "rotation-last AVOIDABLE_VIOLATION count must be 0 (down-only); "
        f"found {len(offenders)}: {[r['op'] for r in offenders]}"
    )


def test_ledger_files_exist_and_op_tokens_present() -> None:
    """Keep the ledger honest: every listed file must exist (relative to the
    srmech package root) and the op token must appear in that file's text."""
    records = _load_ledger()
    assert records, "rotation-last ledger is empty"
    for rec in records:
        target = (_PKG_ROOT / rec["file"]).resolve()
        assert target.exists(), (
            f"ledger op {rec['op']!r}: file does not exist: {rec['file']}"
        )
        text = target.read_text(encoding="utf-8")
        assert rec["op"] in text, (
            f"ledger op {rec['op']!r} not found as a token in {rec['file']}"
        )


def test_every_record_has_one_of_three_verdicts() -> None:
    """Each record carries exactly one of the three valid verdicts (the
    NDJSON parse already asserts this; re-pin it as an explicit contract)."""
    records = _load_ledger()
    for rec in records:
        assert rec["verdict"] in _VALID_VERDICTS, (
            f"op {rec['op']!r}: verdict {rec['verdict']!r} not valid"
        )
