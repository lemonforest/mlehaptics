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

#: rc452 (`#T1171`) — "... `CEIL_C_REJECTED_CHAINS`, which is **7** ...". The
#: rc451 gate derived the running count from this ceiling but never read the
#: ceiling's own literal where the README RESTATES it, so mid-rc452 prose
#: said `8` beside a gated `11 of the 18` and satisfied every assertion here.
#: The two were self-refuting on one line — `18 - 8 = 10`, not 11 — and nothing
#: compared them, because the derivation and the restatement were different
#: strings.
_REJECTED_CEIL = re.compile(r"`CEIL_C_REJECTED_CHAINS`, which is \*\*(\d+)\*\*")

#: rc452 — "... counts **0 of 3 forms unsupported** ...". rc452 drove
#: CEIL_SURFACE_A_UNSUPPORTED_FORMS to 0 in the same change that added the map
#: form and left the README saying 2.
_FORMS_UNSUPPORTED = re.compile(
    r"\*\*(\d+) of (\d+) forms unsupported\*\*")

#: rc452 — the PROSE claim, not a cardinal. Through rc451 the README said the C
#: peer "does not execute `map` at all"; rc452 added `cr_step_map` and the
#: sentence survived the release. A number gate cannot see this one, so it is
#: pinned as a forbidden phrase keyed to the live form ceiling.
_MAP_DENIALS = (
    "does not execute `map` at all",
    "`map` does not run at all",
)


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


def _ratchet():
    import test_c_cascade_parity_ratchet_rc446 as ratchet
    return ratchet


def test_readme_rejected_chain_ceiling_matches_the_ratchet() -> None:
    """rc452 (`#T1171`). The README RESTATES `CEIL_C_REJECTED_CHAINS` inline;
    pin that literal to the ratchet that owns it.

    This is the assertion whose absence let mid-rc452 prose say `8` beside a gated
    `11 of the 18`. The derivation below is the same one
    ``test_readme_running_chain_cardinal_matches_the_live_ceiling`` uses, so if
    both figures are present they cannot disagree with each other either.
    """
    m = _REJECTED_CEIL.search(_text(_README))
    assert m, ("no '`CEIL_C_REJECTED_CHAINS`, which is **N**' clause found in "
               "python/README.md — it was rephrased and this gate has stopped "
               "observing. Re-point the regex; do not delete the assertion.")
    live = _ratchet().CEIL_C_REJECTED_CHAINS
    assert int(m.group(1)) == live, (
        "python/README.md restates CEIL_C_REJECTED_CHAINS as %s; the ratchet "
        "holds %d. This text ships as the PyPI long-description, and the "
        "restated figure is the one a reader subtracts — at rc452 it said 8 "
        "beside a gated '11 of the 18', inviting 18-8=10."
        % (m.group(1), live))


def test_readme_unsupported_form_count_matches_the_ceiling() -> None:
    """rc452 (`#T1171`). One rc452 commit drove CEIL_SURFACE_A_UNSUPPORTED_FORMS to 0 and
    left the README advertising 2."""
    m = _FORMS_UNSUPPORTED.search(_text(_README))
    assert m, ("no '**N of M forms unsupported**' cardinal found in "
               "python/README.md — it was rephrased and this gate has stopped "
               "observing.")
    ratchet = _ratchet()
    live = ratchet.CEIL_SURFACE_A_UNSUPPORTED_FORMS
    total = len(ratchet.SURFACE_A_STEP_FORMS)
    assert (int(m.group(1)), int(m.group(2))) == (live, total), (
        "python/README.md says %s of %s step forms are unsupported; the live "
        "ceiling is %d of %d (CEIL_SURFACE_A_UNSUPPORTED_FORMS over "
        "SURFACE_A_STEP_FORMS)."
        % (m.group(1), m.group(2), live, total))


def test_readme_does_not_deny_a_form_the_c_peer_now_runs() -> None:
    """rc452 (`#T1171`). The PROSE half of the same defect.

    Numbers were not the only thing rc452 falsified: the README still said the
    C peer "does not execute `map` at all" in the release that added
    `cr_step_map`. A cardinal gate cannot see a sentence, so this keys the
    forbidden phrasing to the live form ceiling — the denial is only a defect
    while the ceiling says every form runs, and the assertion says so rather
    than banning the words unconditionally.
    """
    ratchet = _ratchet()
    if ratchet.CEIL_SURFACE_A_UNSUPPORTED_FORMS != 0:
        return  # a form really is unsupported; the denial may be accurate
    text = _text(_README)
    present = [p for p in _MAP_DENIALS if p in text]
    assert not present, (
        "python/README.md still denies the C peer executes `map` (%s) while "
        "CEIL_SURFACE_A_UNSUPPORTED_FORMS is 0 and SURFACE_A_STEP_FORMS lists "
        "%r — every form executes. rc452 added `cr_step_map` and shipped this "
        "sentence unchanged in the PyPI long-description."
        % ("; ".join(repr(p) for p in present), list(ratchet.SURFACE_A_STEP_FORMS)))


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
