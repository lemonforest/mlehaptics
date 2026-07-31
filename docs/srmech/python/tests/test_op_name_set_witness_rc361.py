"""rc361 (`#T1034`) — the op-name-SET witness: the instrument a rename trips.

WHY THIS EXISTS. ADR-0010 declustering moves ~73 modules between top-level
namespaces. Before rc361 the tree had **no gate that detects a rename**. It had
54 test files / 60 assertions pinning the op COUNT, and a count is the wrong
quantity: a rename relocates names and leaves cardinality untouched. Measured
2026-07-29 by simulating this ADR's own example move
(`srmech.amsc.rational` -> `srmech.math.rational`): 28 of 516 dotted names
relocate, the total stays **516**, and every one of those 60 pins stays GREEN.

That is an **EMPTY** null about the pins, not a defect — `len(...)` measures
cardinality and measures it correctly. It is a real gap about the arc. This file
closes it by pinning the SET, not the size.

⚠️ THE MANIFEST IS HAND-COMMITTED ON PURPOSE — DO NOT WIRE IT INTO CODEGEN.
`tests/registered_op_names.txt` is NOT emitted by `tools/regen_all.py` or by
`tools/codegen_manifest.py`, and `test_the_manifest_is_not_codegen_emitted`
below asserts that it stays that way. The reason is the whole point of the
instrument: a rename arc runs `python tools/gen_*.py` as a matter of course, so
a codegen-emitted manifest would be rewritten by the very change it is meant to
detect and go green unconditionally — reproducing the exact failure mode
(a probe that cannot come out otherwise) that this file was written to fix.

TO CHANGE THE NAME SET DELIBERATELY, two edits are required, in the same commit:
  1. rewrite the manifest:
       python -c "from srmech.amsc.tool_schema import get_tool_schema; \
                  ns=sorted(e.name for e in get_tool_schema().tools); \
                  open('tests/registered_op_names.txt','w',encoding='utf-8', \
                       newline='\\n').write('\\n'.join(ns)+'\\n')"
  2. update `EXPECTED_NAME_SET_SHA256` and `EXPECTED_N` below to what the failure
     message prints.
Needing TWO edits is deliberate: a careless single-file regen cannot silently
pass, because the digest is pinned in source and the names are pinned on disk.
"""
from __future__ import annotations

from pathlib import Path

from srmech.amsc.format import sha256_bytes
from srmech.amsc.tool_schema import get_tool_schema

MANIFEST = Path(__file__).resolve().parent / "registered_op_names.txt"

#: Registered public-callable count at rc361. Pinned here only so the failure
#: message can say "516 -> 517" instead of dumping 516 lines; the SET below is
#: the actual contract.
EXPECTED_N = 525

#: sha256 over the NORMALISED manifest body — "\n".join(sorted names) + "\n",
#: UTF-8. Normalised rather than raw-file-bytes so a CRLF checkout cannot make
#: the digest disagree between the Windows and Linux CI cells; that would be a
#: platform artifact masquerading as a rename.
EXPECTED_NAME_SET_SHA256 = (
    "812dc897bc12cf8ebfdc76dd12445e9b2c29484df4b9c82bb7c9b3d7f390a509")


def _live_names() -> list[str]:
    return sorted(e.name for e in get_tool_schema().tools)


def _manifest_names() -> list[str]:
    text = MANIFEST.read_text(encoding="utf-8")
    return [ln for ln in text.splitlines() if ln.strip()]


def _normalised(names: list[str]) -> bytes:
    return ("\n".join(names) + "\n").encode("utf-8")


def test_manifest_exists_and_is_line_per_name() -> None:
    assert MANIFEST.exists(), (
        f"{MANIFEST.name} is missing — it is the rename witness and it is "
        f"HAND-COMMITTED, so nothing regenerates it for you. See this module's "
        f"docstring for the two-edit procedure.")
    names = _manifest_names()
    assert names == sorted(names), "the manifest must be sorted"
    assert len(names) == len(set(names)), "the manifest has duplicate names"


def test_the_live_name_SET_matches_the_manifest() -> None:
    """⚠️ THE RENAME GATE. Set equality, not cardinality.

    A rename shows up here as one name in `added` and one in `removed` while the
    counts are identical — which is precisely the case every count-pin in the
    tree is blind to.
    """
    live, pinned = _live_names(), _manifest_names()
    added = sorted(set(live) - set(pinned))
    removed = sorted(set(pinned) - set(live))
    assert not (added or removed), (
        "the registered op-name SET changed.\n"
        f"  live {len(live)}  pinned {len(pinned)}"
        f"{'  (SAME COUNT — a rename, which no count-pin can see)' if len(live) == len(pinned) else ''}\n"
        f"  added({len(added)}):   {added[:12]}\n"
        f"  removed({len(removed)}): {removed[:12]}\n"
        "If this is a DELIBERATE rename or an intended new op, follow the "
        "two-edit procedure in this module's docstring — rewrite the manifest "
        "AND update EXPECTED_NAME_SET_SHA256 / EXPECTED_N in the same commit.")
    assert len(live) == EXPECTED_N, (
        f"count moved {EXPECTED_N} -> {len(live)}; update EXPECTED_N")


def test_the_manifest_digest_is_pinned_in_source() -> None:
    """The second of the two required edits. Pinning the digest in SOURCE means
    a rewrite of the data file alone cannot pass."""
    got = sha256_bytes(_normalised(_manifest_names()))
    assert got == EXPECTED_NAME_SET_SHA256, (
        f"manifest digest drifted.\n  expected {EXPECTED_NAME_SET_SHA256}\n"
        f"  got      {got}\n"
        "Update EXPECTED_NAME_SET_SHA256 to the 'got' value IN THE SAME COMMIT "
        "as the manifest rewrite.")


def test_the_witness_can_actually_fail_on_a_rename() -> None:
    """⚠️ NON-VACUITY. A gate that cannot fail is not evidence.

    Mutate one name with the SAME cardinality — exactly what declustering does —
    and prove (a) the set comparison catches it and (b) a count comparison does
    NOT. The second half is the measured indictment of the count-pins, asserted
    rather than asserted-about.
    """
    pinned = _manifest_names()
    renamed = sorted(
        ["srmech.math.rational" + n[len("srmech.amsc.rational"):]
         if n.startswith("srmech.amsc.rational") else n
         for n in pinned])

    assert len(renamed) == len(pinned), "the simulation must preserve cardinality"
    moved = sum(1 for n in pinned if n.startswith("srmech.amsc.rational"))
    assert moved > 0, "the simulated prefix matches nothing — probe is inert"

    # (a) the SET witness sees it
    assert set(renamed) != set(pinned)
    assert sha256_bytes(_normalised(renamed)) != EXPECTED_NAME_SET_SHA256
    # (b) a COUNT witness is blind to it — this is why this file exists
    assert len(renamed) == EXPECTED_N


def test_the_manifest_is_not_codegen_emitted() -> None:
    """⚠️ If codegen ever writes this file, the witness dies silently.

    The rename arc runs the generators as routine work. A generated manifest
    would be rewritten by the change it is meant to detect and go green
    unconditionally. Keep it hand-committed.
    """
    tools = Path(__file__).resolve().parents[1] / "tools"
    assert tools.is_dir(), tools
    writers = [p.name for p in sorted(tools.glob("*.py"))
               if MANIFEST.name in p.read_text(encoding="utf-8", errors="replace")]
    assert writers == [], (
        f"{MANIFEST.name} is referenced by codegen tool(s) {writers}. If a "
        f"generator now writes it, this witness can no longer detect a rename — "
        f"it would be regenerated by the same command the rename arc runs. Keep "
        f"the manifest hand-committed and review-gated.")
