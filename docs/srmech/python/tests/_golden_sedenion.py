"""The ONE loader for the rc464 sedenion-register golden fixture (`#T1188`).

``tests/sedenion_register_golden_rc464.ndjson`` is the recorded behaviour of the
shipped 16-slot ``SedenionRegister``, produced by
``docs/srmech/notes/_golden_sedenion_register_rc464.py`` against the class source
whose SHA-256 the fixture's header carries.

WHY A FIXTURE AND NOT A PEER CLASS. Until rc464 the faithfulness of
``CDRegister(16, namespace="SEDENION")`` was gated against the LIVE
``SedenionRegister``, and a test asserted through ``inspect.getsource`` that the
oracle's source does not mention the subject — the guarantee was CODE
INDEPENDENCE. rc464 makes CDRegister the register shape and removes the 16-slot
class, so that guarantee has to MOVE rather than be deleted. It moves to DATA
PROVENANCE, which is the stronger form of the same claim: recorded output cannot
acquire the subject's failure modes because it is not running. The digest below
is what makes that binding — a fixture that could be regenerated from the subject
would prove nothing, so the bytes are pinned here, in test source, and the
generator is committed separately as provenance rather than run at test time.

Two things this module deliberately does NOT do:

* It does not read ``srmech/cascade/sedenion_register.py`` to re-verify
  ``oracle_source_sha256``. That file is removed in this arc; a checker that
  needs it would have to be deleted with it, which is exactly the coupling the
  fixture exists to break. The digest is provenance for a reader, not a live
  assertion — and it is the digest of the file AT the header's ``source_commit``,
  not of whatever is on disk now, so it stays verifiable after the file is gone::

      git show <source_commit>:docs/srmech/python/srmech/cascade/sedenion_register.py | sha256sum

* It does not regenerate. A missing or edited fixture is a hard failure, never a
  silent re-record.

THE ONE-WINDOW CHECK, AND WHERE ITS RESULT LIVES. A companion module
(``test_sedenion_golden_provenance_rc464.py``) replayed the recorded protocol
against the LIVE ``SedenionRegister`` — the one measurement nothing downstream
can make, because everything downstream compares the SUBJECT to the record and
the oracle is gone. It was deleted with the class, as its own docstring
instructed. Its last run was not the one that happened to be in the branch: the
tree at ``3d404205d`` was extracted with ``git archive`` and the module run
against it immediately before the deletion — **11 passed in 3.92 s**, on the
PURE path (the extracted shim expects ABI 24 and the built library is 25, so it
declined), while the fixture header records ``has_native: true`` at generation.
So the replay agreed with the recording across the native/pure split as well,
which is more than the module was written to prove.

LINE ENDINGS. The digest is over the fixture's CRLF-NORMALISED bytes, not the
bytes on disk. This repository checks out with ``core.autocrlf=true``, so a file
committed with LF arrives on a Windows working tree with CRLF — and a raw
``read_bytes()`` digest would then fail on Windows and pass everywhere else,
which is the worst shape a pin can have: red for one platform, and red in a way
that looks like the fixture was tampered with. Normalising first makes the pin a
statement about CONTENT. Precedent: ``tests/test_op_name_set_witness_rc361.py``
normalises its manifest the same way and for the same reason.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from srmech.amsc.format import sha256_bytes

GOLDEN_PATH = Path(__file__).with_name("sedenion_register_golden_rc464.ndjson")

#: SHA-256 of the fixture's CRLF-NORMALISED bytes (see :func:`golden_bytes`),
#: pinned so the recording cannot be silently re-made from the class it is the
#: oracle for. Precedent:
#: ``tests/test_op_name_set_witness_rc361.py::EXPECTED_NAME_SET_SHA256``.
GOLDEN_SHA256 = "906eee9a15250edd645187b27d998d34031251bdce567999068da71b69b6537e"

#: The record census, asserted as an EQUALITY. A truncated fixture is the
#: failure mode a digest alone would catch but a partial read would not — this
#: makes "the file is complete" a statement with a number behind it.
EXPECTED_RECORD_COUNTS = {
    "header": 1,
    "probe": 1080,        # 9 D values x 15 directions x 8 keys
    "probe_hits": 9,
    "navmap": 16,
    "navigate": 16,
    "couple": 4,
    "carry": 2,
    "correct": 22,        # 7 single-bit positions at n=3 + 15 at n=4
    "reads": 1,
    "storage": 6,         # 2 register fixtures x 3 D values
}

#: The D sweep the recorded probes cover — the rc297 faithfulness gate's own set.
GOLDEN_D_VALUES = (256, 288, 320, 352, 384, 448, 512, 1024, 4096)

#: The eight content keys every probe set writes, in slot order.
GOLDEN_KEYS = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta")

_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def golden_bytes() -> bytes:
    """The fixture's bytes with CRLF normalised to LF — what the digest is over.

    A targeted ``\\r\\n`` -> ``\\n`` replace rather than ``splitlines()``: the
    latter also splits on U+000B / U+000C / U+2028, and while ``json.dumps``
    escapes those inside strings today, a digest should not depend on that
    staying true."""
    return GOLDEN_PATH.read_bytes().replace(b"\r\n", b"\n")


def load_golden() -> Dict[str, List[Dict[str, Any]]]:
    """Parse the fixture, verifying its digest first. Returns records by ``kind``,
    each list in file order."""
    if _CACHE:
        return _CACHE
    raw = golden_bytes()
    digest = sha256_bytes(raw)
    if digest != GOLDEN_SHA256:
        raise AssertionError(
            f"{GOLDEN_PATH.name} does not match its pinned digest "
            f"({digest} != {GOLDEN_SHA256}). The fixture is the RECORD of a class "
            f"that no longer runs; it is never regenerated from the subject it "
            f"gates. If the file was edited, restore it — do not re-pin.")
    for line in raw.decode("utf-8").split("\n"):
        if not line:
            continue
        rec = json.loads(line)
        _CACHE.setdefault(rec["kind"], []).append(rec)
    return _CACHE


def golden_header() -> Dict[str, Any]:
    return load_golden()["header"][0]


def probes_for(D: int) -> List[Dict[str, Any]]:
    """The 120 recorded probes at width ``D``, in generation order."""
    return [r for r in load_golden()["probe"] if r["D"] == D]


def int_keyed(mapping: Dict[str, Any]) -> Dict[int, Any]:
    """JSON object keys are strings; slot maps are keyed by int everywhere else."""
    return {int(k): v for k, v in mapping.items()}
