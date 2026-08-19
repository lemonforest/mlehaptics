"""rc451 (`#T1164`, closing `#T1163`) — the two UNGATED C-coverage cardinals in
``python/README.md``, tied to the values they describe.

THE DEFECT, MEASURED
====================
One shipped sentence in the PyPI long-description carried two undated literals:

    The shared dispatch table `CR_OP_REG` holds **20 op spellings** at
    v0.9.0rc450 ... a bare-C host runs **9 of the 18** chains from their
    descriptors today, measured by execution.

Both were TRUE at rc450 and both went FALSE the moment rc451 landed (24 and 10).
Neither had a gate: grepping ``tests/`` for ``CR_OP_REG``, ``op spellings`` and
``9 of the 18`` at rc450 found only
``test_t1158_registry_param_order_rc449.py``'s own docstring and marker
literals, none of which reads the README. The "9 of the 18" half was already
FILED as `#T1163` — *true but undated and ungated, so it goes stale the moment
the ceiling moves* — and the "20 op spellings" half was filed nowhere, a second
undated figure in the same sentence with the same failure mode.

WHY A GATE RATHER THAN A FIX
============================
Fixing the numbers is what rc451 would have done anyway; it does not stop rc452
from repeating it. This is the tree's own answer to that shape — "a number
written as a literal, with no tie to the value it describes, rots, while the
same number written as a live lookup cannot" (``test_readme_currency_rc419``'s
docstring). "Ungated surfaces trickle; gated ones race to 100%."

WHAT EACH ASSERTION KEYS ON — nothing here compares a literal to a literal:
  * the op-spelling count is PARSED out of ``CR_OP_REG``'s initialiser in
    ``c/src/srmech_compose_run.c`` (the initialiser, not a grep — a grep also
    catches the ``cr_op_is`` arms and over-counts, which is what the README
    sentence itself says);
  * the running-chain count is DERIVED as ``executable - CEIL_C_REJECTED_CHAINS``
    from the live catalog and the rc446 ratchet, the two artifacts that actually
    own it.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat

_README = Path(__file__).resolve().parents[1] / "README.md"
_COMPOSE_C = (Path(__file__).resolve().parents[2] / "c" / "src"
              / "srmech_compose_run.c")

#: "... holds **24 op spellings** at v0.9.0rc451 ..."
_OP_SPELLINGS = re.compile(r"\*\*(\d+) op spellings\*\*")

#: "... runs **10 of the 18** chains from their descriptors today ..."
_CHAINS_RUN = re.compile(r"runs \*\*(\d+) of the (\d+)\*\* chains")


def _text(path: Path) -> str:
    with io.open(path, "r", encoding="utf-8", errors="replace",
                 newline=None) as fh:
        return fh.read()


def _cr_op_reg_size() -> int:
    """The op-spelling count, PARSED from the C initialiser.

    PREDICATE: find ``} CR_OP_REG[`` ... ``= {``, take the text to the closing
    ``};``, and count the ``{ "bare", <len>u, "full" }`` rows. Deliberately the
    row count and not the declared array size, so a declared size that outran
    its rows could not satisfy this.
    """
    text = _text(_COMPOSE_C)
    m = re.search(r"\}\s*CR_OP_REG\[(\d+)\]\s*=\s*\{", text)
    assert m, ("CR_OP_REG's initialiser was not found in %s — the declaration "
               "was reshaped and this parse has stopped observing. Re-point it; "
               "do not delete the assertion." % _COMPOSE_C.name)
    body = text[m.end():text.index("};", m.end())]
    rows = re.findall(r'\{\s*"([A-Za-z0-9_]+)"\s*,\s*(\d+)u\s*,\s*"', body)
    assert rows, "CR_OP_REG parsed to ZERO rows; an empty parse is not a count"
    declared = int(m.group(1))
    assert declared == len(rows), (
        "CR_OP_REG declares size %d but its initialiser holds %d rows"
        % (declared, len(rows)))
    return len(rows)


def _chains_running_in_c() -> tuple:
    """(running, executable), derived from the catalog and the rc446 ceiling."""
    import test_c_cascade_parity_ratchet_rc446 as ratchet
    catalog = _cat.load_catalog()
    executable = sum(1 for d in catalog.values()
                     if _cc.descriptor_status(d) == "executable")
    return executable - ratchet.CEIL_C_REJECTED_CHAINS, executable


def test_readme_op_spelling_cardinal_matches_the_c_table() -> None:
    m = _OP_SPELLINGS.search(_text(_README))
    assert m, ("no '**N op spellings**' cardinal found in python/README.md — "
               "the sentence was rephrased and this gate has stopped "
               "observing. Re-point the regex; do not delete the assertion.")
    live = _cr_op_reg_size()
    assert int(m.group(1)) == live, (
        "python/README.md advertises %s op spellings in CR_OP_REG; the C "
        "initialiser holds %d. This text ships as the PyPI long-description. "
        "It was an UNDATED literal with no gate until rc451, and rc451's four "
        "new arms are exactly the kind of change that falsifies it silently."
        % (m.group(1), live))


def test_readme_running_chain_cardinal_matches_the_live_ceiling() -> None:
    """`#T1163`, closed. The sentence is now keyed to the ratchet that owns the
    number instead of restating it."""
    m = _CHAINS_RUN.search(_text(_README))
    assert m, ("no 'runs **N of the M** chains' sentence found in "
               "python/README.md — it was rephrased and this gate has stopped "
               "observing.")
    running, executable = _chains_running_in_c()
    assert (int(m.group(1)), int(m.group(2))) == (running, executable), (
        "python/README.md says a bare-C host runs %s of the %s chains; the "
        "live derivation is %d of %d (executable descriptors minus "
        "CEIL_C_REJECTED_CHAINS). Filed as `#T1163` at rc450 precisely because "
        "the sentence was true, undated and ungated — so it would go stale on "
        "the next decrement, which is what rc451 is."
        % (m.group(1), m.group(2), running, executable))


def test_the_gate_would_have_fired_on_the_rc450_text() -> None:
    """RETRO-CHECK. A gate that would not have caught the defect that motivated
    it is not the gate. The rc450 strings are reproduced VERBATIM and run
    through the SHIPPED regexes, so loosening either predicate fails here.
    """
    rc450_ops = ("The shared dispatch table `CR_OP_REG` holds **20 op "
                 "spellings** at v0.9.0rc450 across Classes N / I / K / C")
    rc450_chains = ("a bare-C host runs **9 of the 18** chains from their "
                    "descriptors today, measured by execution.")
    m = _OP_SPELLINGS.search(rc450_ops)
    assert m and int(m.group(1)) == 20
    assert int(m.group(1)) != _cr_op_reg_size(), (
        "the rc450 op-spelling figure (20) equals the live count, so this "
        "retro-check is vacuous — the defect it replays no longer exists as "
        "stated and the carve-out needs re-basing, not deleting")
    m = _CHAINS_RUN.search(rc450_chains)
    assert m and (int(m.group(1)), int(m.group(2))) == (9, 18)
    running, executable = _chains_running_in_c()
    assert (int(m.group(1)), int(m.group(2))) != (running, executable), (
        "the rc450 running-chain figure (9 of 18) equals the live derivation, "
        "so this retro-check is vacuous")
