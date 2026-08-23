"""`#T1160` / gh #1653 item 5 — the C-vs-Python VALUE-parity gate. rc450.

WHAT WAS MISSING, AND WHY IT WAS INVISIBLE
------------------------------------------
The rc446 C-parity ratchet measures ``srmech_chain_run`` by ``rc == 0`` alone.
Its ``_c_runs`` reads ``out_len`` at the call site and **never decodes
``out.raw``**. So a chain that RAN in the compiled projection and returned a
DIFFERENT VALUE than the scripting projection was indistinguishable from one
that agreed — nine chains were "accepted" on exactly that basis, and every
future ceiling decrement would have been unwitnessed in the same way.

That is this arc's named defect class: **an instrument that cannot return
otherwise is not a measurement.** So the first question this file answers about
itself is *what would it take for it to say something other than what it says*,
and the answer is written into the test bodies rather than into a comment.

WHAT IS GATED HERE
------------------
1. :func:`classify` — the ONE decision point. Given the C wire bytes and the
   Python value, it returns exactly one verdict from :data:`VERDICTS`. Every
   population row AND every witness goes through it; there is no second path.
   :func:`test_bits_is_reachable_only_through_classify` enforces that
   structurally over this module's own source, so a strict-witness /
   lax-population split is not merely discouraged, it is inexpressible.
2. Value parity over the WHOLE live population — every executable descriptor,
   every chain variant, every declared proof case (rc450: 18 / 20 / 98). The
   population is derived from the shipped catalog, never hard-coded, and the
   verdict tallies are reconciled against the total so a silently shrinking
   compared-set is a red test rather than a quieter green one.
3. The kind -> type bijection, pinned against BOTH artifacts: the C writer's
   emissions (parsed out of ``cr_desc_scalar`` / ``cr_desc_list``) and
   :func:`_reconstruct_value`'s branches. A kind either side grows alone reds.
4. Two PLANTED DESCRIPTOR-INTERIOR MUTATIONS, which is the only witness shape
   that can separate "the C run loop executed these steps" from "some compiled
   symbol computed the right answer for its own reasons". See the next section.

⚠️ WHY A PROOF-CASE INPUT CANNOT SERVE AS THE ANTI-COARSE WITNESS
-----------------------------------------------------------------
This is the shape rc451+ inherits, so it is stated in full rather than
assumed. The obvious witness — mutate ``cyclic_gcd``'s ``b`` from 18 to 19 and
require the wire to move 6 -> 1 — **does not test what it appears to test**:

* ``cyclic_gcd``'s only step is ``{"op": "gcd", "args": {"a": "@input.a",
  "b": "@input.b"}}``. Every argument is a ``@ref``. There is NO literal in
  the descriptor to mutate.
* ``b = 18`` lives in ``[[cascade.chain.proof_cases]] inputs``, which
  :func:`_chain_only` STRIPS before the chain document is handed to C. It
  travels the separate **ctx wire** (``{"inputs": ...}``).
* Therefore an implementation that ignored ``steps[]`` entirely and called any
  gcd symbol on the ctx inputs returns 1 for ``b = 19`` and passes the witness
  perfectly. Measured: ``srmech_gcd(12,18) = 6`` and ``(12,19) = 1``.

So that mutation proves ``@input.*`` REF RESOLUTION — which the rc446 ratchet's
``test_harness_resolves_input_refs`` already proves — while wearing the name of
a stronger claim. It is kept below, RELABELLED as the ctx-wire control it
actually is, and the real anti-coarse witnesses mutate a literal that lives
INSIDE the chain document and survives ``_chain_only``:

* ``magnitude`` step[1] ``args.orientation`` 1 -> -1  =>  wire 3.5 -> -3.5
* ``net_chirality`` step[0] ``fold_init`` 1 -> -1     =>  wire 1 -> -1

Both measured working before this file was written. A coarse compiled symbol, a
cached value or a pre-seeded accumulator cannot track a literal it never parses
— and unlike the ctx inputs, these two ARE inside the document the C run loop
parses, which is the whole distinction.

WHICH VERDICTS ARE REACHABLE, AND WHICH ARE NOT
-----------------------------------------------
A closed verdict set whose members cannot occur reconciles terms pinned at zero
BY DEFINITION rather than by measurement, so each is stated:

* ``BYTE_IDENTICAL``           reachable, and the bulk of the population.
* ``DIVERGENT``                reachable — three in-suite red witnesses classify
                               here, and the population ceiling is 0.
* ``C_REJECTED_<status>``      reachable, because the population is **all 18
                               executable chains**, not only the 9 accepted
                               ones. Scoping it to the accepted set — which is
                               DEFINED as ``rc == 0`` — would have made this
                               verdict dead by construction.
* ``NONFINITE_CANNOT_CROSS_WIRE``  reachable: ``magnitude`` declares ``nan`` /
                               ``inf`` / ``-inf`` proof cases and those are not
                               valid JSON, so the document cannot be built at
                               all. Reachable ONLY because the population is
                               every proof case rather than ``cases[0]``.
* ``UNKNOWN_WIRE_KIND_<k>``    NOT produced by any live C emission at rc450. It
                               is reachable synthetically (the bijection
                               witness) and it is a HARD RED wherever it appears
                               in the population — a kind the shipped reader
                               cannot reconstruct is a gate failure, not a
                               tolerated outcome.

``CARRIER_NOT_ON_WIRE_<kind>`` was specified for this gate and is **deliberately
absent**. Every chain whose carrier has no JSON form (``encode_loe_content``'s
bytes, ``schur_complement``'s Mat) is C-REJECTED first, so the verdict could
never fire on any population row — and a verdict that cannot fire is exactly
what this file exists to refuse. gh #1653 item 5's "shape 1" is therefore
discharged BY CONSTRUCTION (a typed reader over a pinned kind set), not by an
executed case, and the gap ledger row says so in those words.

SCOPE — SURFACE A ONLY
----------------------
This comparator covers ``srmech_chain_run`` (Surface A). It does NOT transfer
unchanged to ``srmech_dsl_chain_run``: that wire carries a ``t`` kind this one
does not, lacks ``q``, and reads ``desc["v"]`` where this one reads
``desc["items"]`` for kind ``l``. Filed as ledger rows
``dsl_wire_value_parity_unmeasured`` and ``wire_l_payload_key_divergence`` so
the untested assumption is a row rather than a silence.

DELIBERATELY NOT NORMALISED — each with its reason
--------------------------------------------------
:func:`_bits` distinguishes all of the following, and every one of them is a
distinction this project has decided is real:

* ``float`` vs ``int``      — the exact-vs-approximate dispatch contract. A
                              Class-N op returning ``3`` and one returning
                              ``3.0`` have taken different paths.
* NaN PAYLOAD, signed zero — Class-K pin-slot phase boundary. ``0.0`` and
                              ``-0.0`` are different pin states, and collapsing
                              them would erase the sign the class exists to
                              carry.
* ``tuple`` vs ``list``    — the filed two-wire divergence
                              (``wire_tuple_kind_absent``). C has no tuple kind;
                              a pair rides ``CR_LIST``. Collapsing them is how
                              that gap would ship unnoticed.
* ``bytes`` vs ``str``     — different carriers, and the byte-buffer carrier is
                              itself a filed gap.
* ``bool`` vs ``int``      — ``True == 1`` in Python and they are not the same
                              value.

``dict`` comparison IS key-order-free (sorted), because JSON objects carry no
order and the C writer canonical-sorts keys; that is a property of the wire, not
a normalisation of the value.
"""
from __future__ import annotations

import ast
import copy
import ctypes
import inspect
import json
import re
import struct
from pathlib import Path

import pytest

import srmech._native as _native
from srmech.cascade import compose as _compose
from srmech.dsl import _catalog as _cat
from srmech.dsl import _cascade_chain as _cc
from srmech.dsl._cascade_chain import cascade_chain_specs
from srmech.math.q import Q

from _native_gate import require_native

# ── the verdict set. CLOSED. ─────────────────────────────────────────────────
V_IDENTICAL = "BYTE_IDENTICAL"
V_DIVERGENT = "DIVERGENT"
V_REJECTED = "C_REJECTED_"                 # + status name
V_NONFINITE = "NONFINITE_CANNOT_CROSS_WIRE"
V_UNKNOWN_KIND = "UNKNOWN_WIRE_KIND_"      # + the offending kind

#: Every verdict :func:`classify` may return, as a prefix set. Membership is
#: asserted per row, so a sixth verdict cannot be introduced by a typo.
VERDICT_PREFIXES = (V_IDENTICAL, V_DIVERGENT, V_REJECTED, V_NONFINITE,
                    V_UNKNOWN_KIND)

_STATUS = {0: "SRMECH_OK", 2: "SRMECH_ERR_BAD_INPUT", 4: "SRMECH_ERR_OVERFLOW",
           5: "SRMECH_ERR_NOT_IMPL", 8: "SRMECH_ERR_LIMIT"}

#: The kind -> type bijection. Pinned against BOTH the C writer and the shipped
#: Python reader by :func:`test_wire_kind_bijection_is_pinned_on_both_sides`.
#:
#: ``t`` joined at rc451 (`#T1164`, gh #1653 item 4) — the TUPLE kind, which
#: closes ledger row ``wire_tuple_kind_absent`` and is why that rc bumps ABI
#: 19 -> 20.
#:
#: ⚠️ THIS PIN IS A SOURCE PARSE, NOT AN EMISSION CENSUS. A dead
#: ``srmech_json_new_string(bd, "t", 1u)`` inside the parsed region plus a
#: reader branch turns it green with no tuple ever crossing the wire. That hole
#: is closed by :func:`test_an_executed_case_emits_the_tuple_kind_itself`, which
#: reads the kind string off a REAL run — do not treat this pin as sufficient
#: on its own.
EXPECTED_WIRE_KINDS = frozenset({"n", "i", "s", "q", "f", "l", "t"})

# ── down-only ceilings, seeded at the MEASURED rc450 population ──────────────
#: STRICT ZERO. Not a ceiling that drains — a divergence between the two
#: projections on a chain C already runs is a wrong answer, and there is no
#: population of them to work down.
CEIL_DIVERGENT = 0

#: Proof cases whose inputs cannot be spelled as RFC 8259 JSON, so the chain
#: document never reaches C at all. ENUMERATED at rc450 rather than merely
#: counted, because a bare integer cannot say which rows it stands for:
#:     magnitude.default            cases 3, 4, 5   (nan / inf / -inf)
#:     best_rational_signed.default case 4          (a non-finite x)
#: Down-only: it falls if the wire ever learns to carry them. Note the
#: precedence — this verdict is decided BEFORE C is called, so a non-finite case
#: on a C-declined chain lands here and not in C_REJECTED. That is why
#: ``best_rational_signed`` appears in both tallies.
CEIL_NONFINITE = 4

#: Rows on chains the C run loop declines, PER CHAIN.
#:
#: ⚠️ THIS WAS A SINGLE SCALAR (55) THROUGH rc450, WITH THE PER-CHAIN SPLIT
#: WRITTEN BESIDE IT AS A COMMENT. That is the "prose isn't a test" shape this
#: arc exists to close, and it was reachable: a chain that PARTIALLY closes —
#: C accepts some of its proof cases and declines the rest, which is exactly
#: what a `scale >= 1`-style narrowing produces — moves the scalar by less than
#: its whole contribution and reds with a message telling the builder to lower
#: the ceiling by that smaller amount. Ratify that and the tree is fully green
#: with the chain measurably broken; the cross-artifact tie stays green too,
#: because the rc446 ratchet's ``_measure()`` reads only ``cases[0]``.
#: Promoting the comment to an asserted dict costs nothing (it reproduced the
#: live tallies exactly) and makes partial closure a named per-chain red.
#:
#: Down-only PER ENTRY: a chain closes by having its entry DELETED, never by
#: being decremented to something it does not measure. Measured at rc451 after
#: best_rational_signed closed (its 9 comparable rows became BYTE_IDENTICAL;
#: its 10th, a non-finite x, is decided BEFORE C is called and stays in
#: CEIL_NONFINITE — which is why that chain used to appear in both tallies).
#: The same drain the rc446 ratchet's CEIL_C_REJECTED_CHAINS measures one level
#: up: this one counts CASES, that one counts CHAINS, and they move together.
CEIL_C_REJECTED_ROWS_BY_CHAIN = {
    # ``autocorrelation``'s entry (5) was DELETED at rc452 (`#T1166`) — the
    # chain closed FULLY, all 5 proof cases BYTE_IDENTICAL, so the row is
    # removed rather than decremented, per the down-only-per-entry rule above.
    # Its steps run as steps: seq_len / mod_add / correlation_product /
    # compensated_sum, none of which names `srmech_autocorrelation_f64`. That
    # fused kernel exists and IS dispatched — but for the `autocorrelation` OP,
    # which is a different object from the `autocorrelation` CHAIN, so no
    # coarse bypass exists between them structurally.
    # ``kuramoto_step`` (10), ``octonion_dft`` (7) and ``quaternion_dft`` (6)
    # were DELETED at rc452 Phase 3 (`#T1166`) — each chain closed FULLY, every
    # representable proof case BYTE_IDENTICAL (kuramoto 10/10 across both
    # variants, including the exact-ℚ general path with pinning/broadcast/α;
    # the DFTs 6/6 and 7/7 including the S3/S7 sqrt axes and the inverse and
    # two-sided-bracketing cases). Rows removed, not decremented, per the
    # down-only-per-entry rule above. Their steps run as steps — the fused
    # srmech_cascade_kuramoto_step*_f64 / srmech_{quaternion,octonion}_dft
    # kernels are NOT referenced by the interpreter TU (the no-coarse gate
    # names all four), so no coarse bypass exists structurally.
    "encode_loe_content": 4,
    "klein4_from_one": 7,
    "parallel_sector_dispatch": 4,
    "schur_complement": 3,
}

#: The total, DERIVED from the per-chain map so the two cannot disagree.
CEIL_C_REJECTED_ROWS = sum(CEIL_C_REJECTED_ROWS_BY_CHAIN.values())

#: Chains in the ACCEPTED set for which no case produced a comparison at all
#: (every row classified). Such a chain reports as measured while measuring
#: nothing, so it is named rather than counted: adding a member is a deliberate
#: red edit that must state why. EMPTY at rc450 — every accepted chain has at
#: least one finite, representable case.
UNMEASURED_CHAINS: frozenset = frozenset()


# ── the canonical bit encoding ───────────────────────────────────────────────
#
# ⚠️ DUPLICATED from tests/test_cascade_catalog_executable_rc420.py ON PURPOSE
# — importing across test modules couples two gates' collection, and this one
# must be runnable alone. The copy is PINNED to its source by
# test_bits_matches_the_rc420_source, so the two cannot drift silently.
def _bits(x) -> bytes:
    if isinstance(x, float):
        return b"f" + struct.pack("<d", x)
    if isinstance(x, bool):
        return b"b1" if x else b"b0"
    if isinstance(x, int):
        return b"i" + repr(x).encode()
    if isinstance(x, str):
        return b"s" + x.encode("utf-8")
    if isinstance(x, bytes):
        return b"y" + x
    if isinstance(x, tuple):
        return b"t(" + b",".join(_bits(v) for v in x) + b")"
    if isinstance(x, list):
        return b"l[" + b",".join(_bits(v) for v in x) + b"]"
    if isinstance(x, dict):
        return b"d{" + b",".join(
            _bits(k) + b":" + _bits(v) for k, v in sorted(
                x.items(), key=lambda kv: repr(kv[0]))) + b"}"
    if x is None:
        return b"n"
    if isinstance(x, Q):                         # rc452 — the exact-ℚ carrier
        # PLACED BEFORE the tolist and repr arms, and explicit rather than
        # inherited, because BOTH of the arms below silently mis-encode a Q:
        #   * the final `b"r" + repr(x)` fallback is where a Q landed through
        #     rc451. A decoy class whose __repr__ returns "Q(5, 6)" produces
        #     BYTE-IDENTICAL comparator output — built independently by two of
        #     the four rc452 workshops — so the discrimination rested on a repr
        #     collision, not on the type.
        #   * giving Q a `.tolist()` at any future point would move it to the
        #     Mat/Vec arm and re-collapse it, silently.
        # An == based comparator cannot discriminate at all here: Q(5,6) == (5,6)
        # is True, and so is Q(5,6) == (10,12), because Q.__eq__ coerces through
        # _as_pair and cross-multiplies. This encoder never calls ==; that is
        # WHY it can tell them apart, and this arm is what makes that structural
        # instead of accidental.
        return b"q" + repr(x.numerator).encode() + b"/" + repr(x.denominator).encode()
    if hasattr(x, "tolist"):                     # Mat / Vec carriers
        return b"M" + _bits(x.tolist())
    return b"r" + repr(x).encode()


# ── THE ONE DECISION POINT ───────────────────────────────────────────────────

def classify(rc, wire: bytes, py_value, *, py_serialisable: bool = True) -> str:
    """Return exactly one verdict for one (C outcome, Python value) pair.

    THIS IS THE ONLY COMPARATOR. The population loop calls it and so does every
    green and red witness below — deliberately, because a gate whose witnesses
    exercise a strict path while its population takes a lax one is green on the
    defect it names. :func:`test_bits_is_reachable_only_through_classify` reads
    this module's own AST and fails if ``_bits`` is called from anywhere else.

    The Python value is NEVER passed through a serialiser on its way here. That
    removes the shared-encoder move entirely: there is no format both sides are
    projected into where a collapse could hide.
    """
    if not py_serialisable:
        return V_NONFINITE
    if rc != 0:
        return V_REJECTED + _STATUS.get(rc, "rc=%d" % rc)
    # The SHIPPED reader, both halves: srmech's own JSON parser and the shipped
    # value-descriptor reconstructor. Using json.loads / a bespoke reader here
    # would test a reader this project does not ship.
    desc = _compose._srmech_json.loads(wire.decode("utf-8"))
    kind = desc.get("k") if isinstance(desc, dict) else None
    try:
        got = _compose._reconstruct_value(desc)
    except ValueError:
        return V_UNKNOWN_KIND + str(kind)
    return V_IDENTICAL if _bits(got) == _bits(py_value) else V_DIVERGENT


# ── driving the two projections ──────────────────────────────────────────────

def _chain_only(entry):
    """The CHAIN-DEFINING keys — same predicate as the rc446 ratchet.

    ``proof_cases`` / ``summary`` / ``returns`` are documentation; the runner
    never reads them, and sending them couples a chain's executability to its
    own test data (rc447 measured that biting on ``magnitude``'s non-finite
    cases, whose ``json.dumps`` spelling is not valid JSON).
    """
    return {k: v for k, v in entry.items()
            if k in ("name", "steps", "on_error", "chain_schema_version")}


def _c_run(chain_dict, ctx):
    """(rc, wire_bytes, serialisable). ``serialisable`` False means the inputs
    cannot be spelled as RFC 8259 JSON, so C was never called."""
    lib = _compose._compose_lib("srmech_chain_run",
                                "srmech_chain_run_arena_bytes")
    assert lib is not None, "require_native passed but the chain-run symbols " \
                            "are absent — that is a different failure and it " \
                            "must not read as a skip"
    try:
        cj = json.dumps(chain_dict, ensure_ascii=False,
                        allow_nan=False).encode("utf-8")
        xj = json.dumps({"inputs": ctx}, ensure_ascii=False,
                        allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        return None, b"", False
    ws_bytes = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, ws_bytes,
                                  out, out_cap, ctypes.byref(out_len)))
    return rc, out.raw[:out_len.value], True


def _py_run(spec, inputs):
    """The Python value, on the PURE projection.

    Native dispatch is forced OFF for the duration. Several ops inside these
    chains route through the very C kernels under test, so leaving dispatch on
    would compare C against C and the whole file would be a tautology that
    could not fail.
    """
    saved = (_native.HAS_NATIVE, _native.LIB)
    _native.HAS_NATIVE, _native.LIB = False, None
    try:
        return _compose.run_chain(spec, inputs=inputs)
    finally:
        _native.HAS_NATIVE, _native.LIB = saved


#: Per-variant defaults merged UNDER a proof case's inputs — the SAME
#: construction tests/test_cascade_catalog_executable_rc420.py uses, so the two
#: sides of this comparison are fed identically and a harness difference cannot
#: surface as a DIVERGENT row.
#:
#: rc452 (`#T1171`): both sides now read the DESCRIPTOR rather than each holding
#: a copy. This file and rc420's held the same four kuramoto_step/general values
#: verbatim and independently, and they were the only thing making that variant
#: runnable at all — so the descriptor was not executable from shipped
#: configuration in either projection. "Fed identically" is now true by
#: construction instead of by two literals agreeing.
def _case_defaults(entry):
    from srmech.dsl._cascade_chain import chain_input_defaults
    return chain_input_defaults(entry)


def _population():
    """(name, variant, entry, spec, case_index, inputs) for EVERY proof case of
    EVERY executable descriptor. Derived live; never a hard-coded list.

    ⚠️ It is every EXECUTABLE chain, not every ACCEPTED one. The accepted set is
    DEFINED as ``rc == 0``, so a population scoped to it makes
    ``C_REJECTED_<status>`` unreachable by construction, and a tally over a
    verdict that cannot occur is arithmetic, not measurement.
    """
    catalog = _cat.load_catalog()
    names = sorted(n for n, d in catalog.items()
                   if _cc.descriptor_status(d) == "executable")
    rows = []
    for name in names:
        for variant, spec, entry in cascade_chain_specs(name):
            for j, case in enumerate(entry.get("proof_cases") or []):
                merged = dict(_case_defaults(entry))
                merged.update(dict(case.get("inputs") or {}))
                rows.append((name, variant, entry, spec, j, merged))
    return rows


def _measure_all():
    """Run the whole population once. Returns (rows, tally, per_chain)."""
    rows, tally, per_chain = [], {}, {}
    for name, variant, entry, spec, j, inputs in _population():
        rc, wire, ok = _c_run(_chain_only(entry), inputs)
        py = None
        if ok and rc == 0:
            py = _py_run(spec, inputs)
        verdict = classify(rc, wire, py, py_serialisable=ok)
        rows.append((name, variant, j, verdict, wire, py))
        tally[verdict] = tally.get(verdict, 0) + 1
        per_chain.setdefault(name, []).append(verdict)
    return rows, tally, per_chain


# ── 0. the library must be there ─────────────────────────────────────────────

def test_native_library_is_present():
    """FAIL, never skip. The rc446/rc447 family in this same arc uses a bare
    ``pytest.skip`` here, which means a broken or absent C build reports the
    whole cascade-parity family GREEN with nothing executed — and rc450 adds
    those gates to the ripple manifest, so the runner would inherit that
    vacuous green. This file uses the tree's own rc351 contract instead: the
    library is absent -> FAIL, unless the run has DECLARED ``SRMECH_EXPECT_PURE
    =1``, in which case the skip is tagged and COUNTED by the CI pure cell.
    (The retrofit of the rc446/447 family is filed as gap-ledger row
    ``native_parity_gates_use_bare_skip``, not done here.)"""
    require_native("srmech_chain_run value parity (gh #1653 item 5)")


# ── 1. the comparator cannot be two comparators ──────────────────────────────

def test_bits_is_reachable_only_through_classify():
    """STRUCTURAL. ``_bits`` may be CALLED only from inside :func:`classify`.

    Without this, nothing stops a later edit from giving the witnesses a strict
    path and the population loop a lax one — which would satisfy every stated
    criterion of this gate while carrying the collapses it exists to refuse
    (the rc444 wedge-join script has a ready-made float->int / tuple->list /
    strip-quotes collapse one copy-paste away). The witnesses below therefore
    do not call ``_bits``; they call ``classify``.
    """
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for sub in ast.walk(node):
            if (isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Name)
                    and sub.func.id == "_bits"
                    and node.name not in ("classify", "_bits")):
                offenders.append("%s:%d" % (node.name, sub.lineno))
    assert not offenders, (
        "_bits is called outside classify() at %s. Every comparison in this "
        "file must route through the single decision point, or a strict-"
        "witness / lax-population split becomes expressible." % offenders)


def test_bits_matches_the_rc420_source():
    """SOURCE-SYNC PIN on the duplicated encoder.

    The copy is deliberate (this gate must run standalone), so the drift risk
    is real and is closed by comparing the two function bodies token-for-token
    rather than by a comment asking the next author to remember.
    """
    import test_cascade_catalog_executable_rc420 as rc420
    mine = inspect.getsource(_bits)
    theirs = inspect.getsource(rc420._bits)

    def _norm(s):
        # Strip comments and collapse whitespace: the pin is on the ALGORITHM,
        # and a reflowed line is not drift.
        s = re.sub(r"#.*", "", s)
        return re.sub(r"\s+", " ", s).strip()

    assert _norm(mine) == _norm(theirs), (
        "this file's _bits has drifted from tests/"
        "test_cascade_catalog_executable_rc420.py::_bits. They are two copies "
        "of ONE canonical byte encoding; if the encoding changed, change both "
        "in the same commit.\n  here : %s\n  rc420: %s"
        % (_norm(mine), _norm(theirs)))


# ── 2. the kind -> type bijection ────────────────────────────────────────────

def _c_emitted_kinds():
    """The kind strings the C writer emits, PARSED from its two marshal
    functions.

    PREDICATE, stated so it can be reproduced or refuted: take the source of
    ``c/src/srmech_compose_run.c`` between ``cr_desc_scalar`` and the end of
    ``cr_desc_list``, and collect every ``srmech_json_new_string(bd, "X", 1u)``
    whose literal is a single character. Scoped to those two functions on
    purpose — an unscoped search over the file also catches key names and
    unrelated single-character strings.
    """
    path = (Path(__file__).resolve().parents[2] / "c" / "src"
            / "srmech_compose_run.c")
    text = path.read_text(encoding="utf-8", errors="replace").replace(
        "\r\n", "\n")
    start = text.index("cr_desc_scalar")
    end = text.index("static srmech_json_value_t *cr_desc(", start)
    region = text[start:end]
    found = set(re.findall(r'srmech_json_new_string\(bd,\s*"(.)",\s*1u\)',
                           region))
    assert found, ("the C-writer kind parse found NOTHING, which means the "
                   "predicate stopped matching — an empty parse must never "
                   "read as agreement")
    return found


def _python_read_kinds():
    """The kinds :func:`_reconstruct_value` branches on, parsed from its AST.

    PREDICATE: every ``k == "<literal>"`` comparison inside the function body.
    """
    src = inspect.getsource(_compose._reconstruct_value)
    found = set(re.findall(r'k\s*==\s*"(.)"', src))
    assert found, ("the Python-reader kind parse found NOTHING — same rule as "
                   "above")
    return found


def test_wire_kind_bijection_is_pinned_on_both_sides():
    """The writer's kinds and the reader's kinds are the SAME set, and that set
    is pinned. Either side growing alone is exactly how a value crosses the wire
    and comes back as something else."""
    c_kinds = _c_emitted_kinds()
    py_kinds = _python_read_kinds()
    assert c_kinds == EXPECTED_WIRE_KINDS, (
        "the C writer emits kinds %s; the pin is %s. A NEW kind must land in "
        "the reader and in this pin in the SAME change."
        % (sorted(c_kinds), sorted(EXPECTED_WIRE_KINDS)))
    assert py_kinds == EXPECTED_WIRE_KINDS, (
        "srmech.cascade.compose._reconstruct_value reads kinds %s; the pin is "
        "%s." % (sorted(py_kinds), sorted(EXPECTED_WIRE_KINDS)))


def test_an_executed_case_emits_the_tuple_kind_itself():
    """rc451 (`#T1164`, gh #1653 item 4). THE SUBJECT IS THE KIND STRING AN
    EXECUTED SHIPPED PROOF CASE ACTUALLY EMITS — not that reconstruction
    succeeded, not that :func:`classify` said BYTE_IDENTICAL, and not the
    source-parsed bijection above.

    WHY THIS ASSERTION AND NOT ONE OF THOSE THREE. The adjudicated dodge for
    ``best_rational_signed`` is to emit its ``(num, den)`` as the EXISTING kind
    ``q``, whose reader returns ``(int(n), int(d))`` — a tuple. Simulated
    against this file's own predicates before rc451 was written, that dodge
    scores 9 BYTE_IDENTICAL, DIVERGENT 0, the declined-row ceiling landing
    exactly on its target, and a GREEN bijection pin, because q-spelling adds
    no kind to either source. Every other instrument in the tree ratifies it.
    Only a predicate whose subject is the emitted kind can refuse it — and the
    refusal matters because it is what makes the ABI 19 -> 20 bump honest
    rather than ceremonial.

    It is also the emission census the bijection pin is NOT: that one parses
    source, so a dead literal inside the parsed region plus a reader branch
    turns it green with nothing ever crossing the wire. This runs the chain.

    HOW IT RETURNS OTHERWISE: any kind other than ``t`` fails, naming what was
    seen. Through rc450 it would have failed on rc=5 with an empty wire.
    """
    require_native("srmech_chain_run value parity (the emitted tuple kind)")
    _variant, _spec, entry = cascade_chain_specs("best_rational_signed")[0]
    cases = entry.get("proof_cases") or []
    inputs = dict((cases[0] or {}).get("inputs") or {})
    rc, wire, ok = _c_run(_chain_only(entry), inputs)
    assert ok and rc == 0, (
        "best_rational_signed did not run in C (ok=%r rc=%r). rc451 closed this "
        "chain; if it declines again the ceilings above are also wrong."
        % (ok, rc))
    desc = _compose._srmech_json.loads(wire.decode("utf-8"))
    assert desc.get("k") == "t", (
        "the C wire spelled best_rational_signed's final value as kind %r, not "
        "'t'. If that is 'q', the chain is being answered as a RATIONAL rather "
        "than as the generic Class-B pair it declares — which reconstructs to a "
        "tuple and so passes every value-level gate in this file, while forking "
        "`pair`'s kind by operand type (klein4_from_one uses pair twice more) "
        "and leaving the tuple kind unshipped. Wire: %r" % (desc.get("k"), wire))
    assert sorted(desc) == ["k", "v"], (
        "the tuple descriptor's key set is %r; rc451 unified l/t payloads under "
        "'v' (ledger row wire_l_payload_key_divergence)." % (sorted(desc),))
    got = _compose._reconstruct_value(desc)
    assert type(got) is tuple, (
        "the shipped reader rebuilt %r (%s) from a 't' descriptor; it must be a "
        "tuple exactly, not a list and not a subclass"
        % (got, type(got).__name__))


def test_an_unknown_kind_is_a_hard_red_not_a_soft_verdict():
    """A synthetic ``{"k": "z"}`` must NOT pass through. If it did, the
    bijection pin above would be decoration: the comparator would meet a kind
    it cannot reconstruct and say nothing about it."""
    v = classify(0, b'{"k": "z", "v": "1"}', 1)
    assert v == V_UNKNOWN_KIND + "z", v
    assert v not in (V_IDENTICAL,), "an unreadable kind read as agreement"


# ── 3. the witnesses. ALL of them go through classify(). ─────────────────────

@pytest.mark.parametrize("wire,py_value,why", [
    (b'{"d": "6", "k": "q", "n": "5"}', Q(5, 6),
     "an exact rational vs the exact-ℚ carrier. rc452 (`#T1166`) FLIPPED this "
     "row's partner: through rc451 this wire was required IDENTICAL against a "
     "Python (5, 6) TUPLE, which is the collapse the rc removes — the shipped "
     "reader rebuilt `q` as a tuple, and a tuple is also what a Class-K pin "
     "pair and a Class-B `pair` step produce, so the type was erased on "
     "arrival. Against Q the agreement is real: same value AND same carrier. "
     "Its DIVERGENT twin (this wire vs the tuple) is in the red set below, so "
     "the pair is pinned in both directions and loosening either would show"),
    (b'{"k": "t", "v": [{"k": "i", "v": "3"}, {"d": "6", "k": "q", "n": "5"}]}',
     (3, Q(5, 6)),
     "HETEROGENEOUS, DEPTH 1: a tuple of an int and a rational. The reader "
     "rebuilds containers RECURSIVELY, so the `q` inside a `t` must come back "
     "as a Q too — through rc451 it came back as a nested TUPLE, a latent "
     "wrong value nothing exercised. This is the depth-1 half of the ruling's "
     "carrier predicate, on the inside of its boundary"),
    (b'{"k": "i", "v": "6"}', 6,
     "a bignum-as-decimal-string vs a Python int"),
    (b'{"k": "f", "v": 3.5}', 3.5, "a double"),
    (b'{"k": "l", "v": [{"k": "f", "v": 11.0}]}', [11.0],
     "a flat list — payload key 'v' since rc451, unified with the sibling DSL "
     "wire and with the new 't' kind (ledger row "
     "wire_l_payload_key_divergence)"),
    (b'{"k": "t", "v": [{"k": "i", "v": "5"}, {"k": "i", "v": "6"}]}', (5, 6),
     "a TUPLE — the rc451 kind. The SAME payload as the red witness below "
     "differing only in the kind letter, which is the whole point: the letter "
     "is what carries the type"),
    (b'{"k": "n"}', None, "the null kind"),
])
def test_green_witnesses_classify_identical(wire, py_value, why):
    """GREEN: agreement is recognised THROUGH the reconstruction, not by
    comparing raw spellings. If either of the first two classifies DIVERGENT,
    the comparator is reading bytes rather than values."""
    assert classify(0, wire, py_value) == V_IDENTICAL, why


@pytest.mark.parametrize("wire,py_value,collapse", [
    (b'{"d": "6", "k": "q", "n": "5"}', (5, 6),
     "exact ℚ -> int pair. rc452 (`#T1166`): THE DELIVERABLE. This row was a "
     "shipped GREEN witness through rc451 — the comparator was REQUIRED to "
     "call a `q` wire identical to a Python 2-tuple, which is the collapse "
     "this whole arc exists to remove. A tuple of two ints is also exactly "
     "how pin_slot_at_zero and pair spell themselves, so under the old "
     "requirement no comparator could ever tell an exact-ℚ chain from an "
     "integer-pair one. Its IDENTICAL twin (this wire vs Q(5, 6)) is in the "
     "green set above"),
    (b'{"d": "6", "k": "q", "n": "5"}', 5 / 6,
     "exact ℚ -> float. The exact-vs-approximate dispatch contract, on the "
     "carrier the contract is about"),
    (b'{"k": "s", "v": "6"}', 6,
     "str -> int (the wedge-join script's strip('\"') collapse)"),
    (b'{"k": "i", "v": "3"}', 3.0,
     "int -> float (the exact-vs-approximate dispatch contract)"),
    (b'{"k": "f", "v": 0.0}', -0.0,
     "signed zero (Class-K pin-slot phase boundary)"),
    (b'{"k": "l", "v": [{"k": "i", "v": "5"}, {"k": "i", "v": "6"}]}',
     (5, 6),
     "list -> tuple. rc451 SHIPPED the 't' kind that closes ledger row "
     "wire_tuple_kind_absent, and this witness SURVIVES UNCHANGED apart from "
     "the payload-key respelling: an 'l' wire against a Python tuple is still "
     "the wrong answer. Loosening it to green anything would be the tell"),
    (b'{"k": "t", "v": [{"k": "i", "v": "5"}, {"k": "i", "v": "6"}]}',
     [5, 6],
     "tuple -> list, the MIRROR of the row above (rc451). Without it the new "
     "kind would be pinned in one direction only, and a writer that flagged "
     "EVERY list a tuple would pass"),
    (b'{"k": "i", "v": "1"}', True,
     "bool -> int"),
])
def test_red_witnesses_classify_divergent(wire, py_value, collapse):
    """RED: each of these passes any normalise-to-agreement encoder, and each
    must be DIVERGENT here. This is the collapse-killer set — the comparator
    fails ITSELF if it is ever loosened."""
    assert classify(0, wire, py_value) == V_DIVERGENT, (
        "the comparator collapsed %s — the encoding is normalising values it "
        "must distinguish" % collapse)


# ── rc452 (`#T1166`): the Q arm is EXPLICIT, and here is why it has to be ───

class _QImpostor:
    """A decoy whose ``__repr__`` is exactly a ``Q``'s.

    Two of the four rc452 workshops built this independently, which is the tell
    that it is not a contrived case: through rc451 a ``Q`` fell through every
    arm of :func:`_bits` to the final ``b"r" + repr(x)`` FALLBACK, so ANY object
    that repr'd the same way produced byte-identical comparator output. The
    discrimination the whole arc turns on rested on a repr collision.
    """

    def __repr__(self):
        return "Q(5, 6)"


def test_a_repr_impostor_does_not_pass_as_the_exact_q_carrier():
    """The impostor must classify DIVERGENT against the ``q`` wire.

    Without the explicit ``isinstance(x, Q)`` arm this test FAILS — measured,
    not asserted: the fallback encodes both as ``b"rQ(5, 6)"``.
    """
    v = classify(0, b'{"d": "6", "k": "q", "n": "5"}', _QImpostor())
    assert v == V_DIVERGENT, (
        "a class that merely REPRS like a Q was accepted as one (%s). The "
        "comparator is reading text, not type." % v)


@pytest.mark.parametrize("wire,why", [
    (b'{"k": "t", "v": [{"k": "i", "v": "5"}, {"k": "i", "v": "6"}]}',
     "a TUPLE of two ints. If Q were ever made a tuple subclass it would "
     "encode as one and this would silently go IDENTICAL"),
    (b'{"k": "l", "v": [{"k": "i", "v": "5"}, {"k": "i", "v": "6"}]}',
     "a LIST of two ints. If Q ever grew a .tolist() it would move to the "
     "Mat/Vec arm, whose encoding is the list's, and this would collapse"),
    (b'{"k": "f", "v": 0.8333333333333334}',
     "the FLOAT the rational is nearest to — the exact-vs-approximate "
     "dispatch contract, on the carrier the contract is about"),
])
def test_the_exact_q_carrier_is_not_any_other_carrier(wire, why):
    """Q must classify DIVERGENT against every neighbouring spelling.

    THROUGH ``classify``, never through ``_bits`` directly — this file's own
    structural rule (:func:`test_bits_is_reachable_only_through_classify`)
    forbids a second comparison path, and these assertions are worth nothing if
    they exercise an encoder the population does not.

    Each row names a DIFFERENT way the explicit ``isinstance(x, Q)`` arm could
    stop being reached without any other test in this file noticing.
    """
    assert classify(0, wire, Q(5, 6)) == V_DIVERGENT, why


def test_an_unreduced_q_wire_rebuilds_canonically_and_that_is_correct():
    """A ``q`` descriptor spelling 10/12 rebuilds as ``Q(5, 6)`` and AGREES.

    Recorded as a positive rather than left implicit, because it is the one
    place the reader legitimately normalises. ``Q.__init__`` reduces through
    the Class-N canonical reducer, so two wire spellings of the same rational
    land on one carrier — which is what "exact rational" MEANS, and is not the
    collapse this gate refuses (that one erases the TYPE, not the spelling).
    It is also unreachable from the shipped C: every ``q`` emission comes out
    of an op that reduced it. Pinned so a future reader that stopped reducing
    would be a red here rather than a silent canonical-form divergence.
    """
    assert classify(0, b'{"d": "12", "k": "q", "n": "10"}', Q(5, 6)) == V_IDENTICAL
    assert classify(0, b'{"d": "12", "k": "q", "n": "10"}', (5, 6)) == V_DIVERGENT


def test_a_rational_inside_a_tuple_rebuilds_as_a_rational():
    """DEPTH 1: the reader is recursive, so a ``q`` nested in a ``t`` must come
    back as a ``Q``. Through rc451 it came back as a nested tuple — a latent
    wrong value with nothing exercising it."""
    desc = _compose._srmech_json.loads(
        '{"k": "t", "v": [{"k": "i", "v": "3"}, {"d": "6", "k": "q", "n": "5"}]}')
    got = _compose._reconstruct_value(desc)
    assert type(got) is tuple and len(got) == 2, got
    assert got[0] == 3 and type(got[0]) is int, got
    assert type(got[1]) is Q, (got[1], type(got[1]).__name__)
    assert (got[1].numerator, got[1].denominator) == (5, 6), got[1]


def test_a_pair_of_rationals_marshals_through_the_real_library():
    """CONFIG B'S PINNED REGRESSION. ``pair(Q, Q)`` must still cross the wire.

    Config B's tuple spelling regressed this from OK to ERR_OVERFLOW, because
    each rational became a nested LIST and JPL Rule 1 forbids the recursion
    needed to marshal it. The `q` spelling keeps the pair at depth 1, which is
    exactly why it fits the marshal budget. Executed against the real .so, not
    reasoned about.
    """
    require_native("pair(Q, Q) marshalling")
    rc, wire, ok = _c_run(_chain_only({
        "name": "rc452_pair_of_rationals", "on_error": "raise", "steps": [
            {"class": "N", "op": "srmech.math.rational.rational_add",
             "args": {"a": [1, 2], "b": [1, 3]}},
            {"class": "N", "op": "srmech.math.rational.rational_add",
             "args": {"a": [1, 4], "b": [1, 4]}},
            {"class": "B", "op": "srmech.cascade.pair",
             "args": {"first": "@step[0].output",
                      "second": "@step[1].output"}},
        ]}), {})
    assert ok and rc == 0, (
        "pair(Q, Q) did not marshal (ok=%r rc=%r). Config B's spelling "
        "regressed exactly this to ERR_OVERFLOW; the `q` spelling must not."
        % (ok, rc))
    desc = _compose._srmech_json.loads(wire.decode("utf-8"))
    assert desc.get("k") == "t", desc
    got = _compose._reconstruct_value(desc)
    assert type(got) is tuple and len(got) == 2, got
    assert all(type(v) is Q for v in got), [type(v).__name__ for v in got]
    assert got[0] == Q(5, 6) and got[1] == Q(1, 2), got


def test_c_rejection_is_its_own_verdict_not_a_silence():
    v = classify(5, b"", None)
    assert v == V_REJECTED + "SRMECH_ERR_NOT_IMPL", v


def test_nonfinite_is_its_own_verdict_not_a_silence():
    v = classify(None, b"", float("nan"), py_serialisable=False)
    assert v == V_NONFINITE, v


# ── 4. the PLANTED DESCRIPTOR-INTERIOR MUTATIONS ─────────────────────────────
#
# See the module docstring for why a proof-case input cannot do this job.

@pytest.mark.parametrize("name,mutate,ctx,base_wire,mutant_wire", [
    ("magnitude",
     lambda ch: ch["steps"][1]["args"].__setitem__("orientation", -1),
     {"x": -3.5}, b'{"k": "f", "v": 3.5}', b'{"k": "f", "v": -3.5}'),
    ("net_chirality",
     lambda ch: ch["steps"][0].__setitem__("fold_init", -1),
     {"orientations": [-1, -1]}, b'{"k": "i", "v": "1"}',
     b'{"k": "i", "v": "-1"}'),
])
def test_descriptor_interior_literal_mutation_moves_the_C_output(
        name, mutate, ctx, base_wire, mutant_wire):
    """ANTI-GAMING. Mutate a literal that lives INSIDE the chain document and
    require the C wire to move correspondingly.

    Both halves are asserted — baseline-ran AND mutant-ran — so a decline
    cannot satisfy this vacuously by returning nothing twice. A coarse compiled
    symbol, a cached value or a pre-seeded accumulator cannot track a literal it
    never parses, and these literals survive :func:`_chain_only` into the
    document the C run loop actually reads. THIS is the witness shape rc451+
    must extend to every newly-unblocked chain.
    """
    # ⚠️ THE GATE MUST PRECEDE :func:`_c_run`, whose own assert says "require_native
    # passed but the chain-run symbols are absent". Without this call that message
    # is FALSE — require_native never ran — and on the deliberately native-absent
    # `fallback (pure-Python, no native)` cell the test FAILS where it should record
    # a pure-by-design SKIP. That is what turned shard 1/6 red at rc450's first CI
    # round: three tests reached _c_run ungated while their six siblings gated.
    require_native("srmech_chain_run value parity (descriptor-interior mutation witness)")
    _variant, _spec, entry = cascade_chain_specs(name)[0]
    base_chain = _chain_only(entry)

    rc_b, wire_b, ok_b = _c_run(base_chain, ctx)
    assert ok_b and rc_b == 0, (
        "the BASELINE did not run in C (rc=%s) — a mutation witness over a "
        "chain that declines proves nothing" % rc_b)
    assert wire_b == base_wire, (
        "baseline wire moved: expected %r, got %r" % (base_wire, wire_b))

    mutant = copy.deepcopy(base_chain)
    mutate(mutant)
    assert mutant != base_chain, "the mutation did not change the document"

    rc_m, wire_m, ok_m = _c_run(mutant, ctx)
    assert ok_m and rc_m == 0, (
        "the MUTANT did not run in C (rc=%s). A mutation that turns the chain "
        "into a decline is not a witness — the value must MOVE, not vanish."
        % rc_m)
    assert wire_m == mutant_wire, (
        "mutant wire: expected %r, got %r. If this is unchanged from the "
        "baseline, the C run loop is not reading the step literal and some "
        "coarser path is producing the answer." % (mutant_wire, wire_m))
    assert wire_m != wire_b


def test_ctx_wire_control_is_labelled_as_what_it_is():
    """CONTROL, NOT the anti-coarse witness — kept and relabelled.

    Mutating ``cyclic_gcd``'s ``b`` input 18 -> 19 moves the wire 6 -> 1, and
    that is worth having: it proves ``@input.*`` refs resolve end to end. It
    does NOT discriminate a coarse dispatcher, because the value travels the
    ctx wire and ``srmech_gcd(12, 19)`` returns 1 for its own reasons. The
    assertion below is deliberately about REF RESOLUTION and says so.
    """
    # Same reason as the mutation witness above: this reaches _c_run, so the gate
    # has to run first or _c_run's assert message is a falsehood and the pure cell
    # reds instead of skipping.
    require_native("srmech_chain_run value parity (ctx-wire ref-resolution control)")
    _v, _s, entry = cascade_chain_specs("cyclic_gcd")[0]
    ch = _chain_only(entry)
    assert all(isinstance(a, str) and a.startswith("@")
               for a in ch["steps"][0]["args"].values()), (
        "cyclic_gcd's step args are no longer all @refs — if a literal has "
        "appeared, this control could be promoted, but that is a conscious "
        "edit and not something to assume")
    rc1, w1, _ = _c_run(ch, {"a": 12, "b": 18})
    rc2, w2, _ = _c_run(ch, {"a": 12, "b": 19})
    assert rc1 == rc2 == 0
    assert w1 == b'{"k": "i", "v": "6"}' and w2 == b'{"k": "i", "v": "1"}', (
        "@input.* refs do not resolve through the ctx wire (%r / %r)"
        % (w1, w2))


# ── 5. the population ────────────────────────────────────────────────────────

def test_population_is_derived_and_non_empty():
    """A loop over an empty parse returns green while comparing nothing. The
    floor is asserted against the LIVE catalog, not against a literal."""
    rows = _population()
    catalog = _cat.load_catalog()
    n_exec = sum(1 for _n, d in catalog.items()
                 if _cc.descriptor_status(d) == "executable")
    chains = {r[0] for r in rows}
    variants = {(r[0], r[1]) for r in rows}
    assert len(chains) == n_exec and n_exec > 0, (
        "%d chains in the population against %d executable descriptors — the "
        "derivation dropped some" % (len(chains), n_exec))
    assert len(rows) >= 80, (
        "only %d proof cases collected; rc420 authored >= 80 and this gate "
        "consumes the same population" % len(rows))
    assert len(variants) >= len(chains)


def test_every_verdict_is_in_the_closed_set_and_the_tally_reconciles():
    """Count reconciliation. ``identical + divergent + classified == total``,
    over a live-derived population — so a silently shrinking compared-set is a
    RED test rather than a quieter green one."""
    require_native("srmech_chain_run value parity")
    rows, tally, _per = _measure_all()
    bad = [(n, v, j, verdict) for n, v, j, verdict, _w, _p in rows
           if not verdict.startswith(VERDICT_PREFIXES)]
    assert not bad, "verdict outside the closed set: %s" % bad[:5]
    assert sum(tally.values()) == len(rows) == len(_population()), (
        "tally %d, rows %d, population %d — they must be the same number"
        % (sum(tally.values()), len(rows), len(_population())))


def test_no_divergence_between_the_two_projections():
    """THE CLAIM. Every chain the C run loop accepts returns a BIT-IDENTICAL
    value to the pure Python projection, over every declared proof case."""
    require_native("srmech_chain_run value parity")
    rows, tally, _per = _measure_all()
    divergent = [(n, v, j, w, p) for n, v, j, verdict, w, p in rows
                 if verdict == V_DIVERGENT]
    assert len(divergent) == CEIL_DIVERGENT, (
        "%d C/Python value divergence(s), ceiling %d:\n%s"
        % (len(divergent), CEIL_DIVERGENT,
           "\n".join("  %s.%s case %d\n    C wire : %r\n    python : %r"
                     % (n, v, j, w, p) for n, v, j, w, p in divergent[:8])))
    unknown = sorted({verdict for _n, _v, _j, verdict, _w, _p in rows
                      if verdict.startswith(V_UNKNOWN_KIND)})
    assert not unknown, (
        "the C wire produced kind(s) the shipped reader cannot reconstruct: "
        "%s. A new kind closes its reader gap in the SAME change." % unknown)


def test_classified_rows_are_enumerated_and_down_only():
    """The rows that could NOT be compared, counted per class. These are the
    honest holes; they are pinned so they drain rather than accumulate."""
    require_native("srmech_chain_run value parity")
    rows, tally, _per = _measure_all()
    nonfinite = tally.get(V_NONFINITE, 0)
    assert nonfinite == CEIL_NONFINITE, (
        "%d non-finite-input case(s), ceiling %d. Down-only: it falls when the "
        "wire learns to carry them." % (nonfinite, CEIL_NONFINITE))

    # PER CHAIN, and per STATUS. rc451 (`#T1164`) split what was one scalar,
    # because the scalar could not tell three genuinely different reds apart.
    measured: dict = {}
    statuses: dict = {}
    for name, _v, _j, verdict, _w, _p in rows:
        if verdict.startswith(V_REJECTED):
            measured[name] = measured.get(name, 0) + 1
            statuses[verdict] = statuses.get(verdict, 0) + 1

    closed = sorted(set(CEIL_C_REJECTED_ROWS_BY_CHAIN) - set(measured))
    grew = sorted(set(measured) - set(CEIL_C_REJECTED_ROWS_BY_CHAIN))
    partial = sorted((n, measured[n], CEIL_C_REJECTED_ROWS_BY_CHAIN[n])
                     for n in set(measured) & set(CEIL_C_REJECTED_ROWS_BY_CHAIN)
                     if measured[n] != CEIL_C_REJECTED_ROWS_BY_CHAIN[n])
    assert not (closed or grew or partial), (
        "the C-declined population moved. THREE causes are reachable here and "
        "they are NOT the same finding — read which one fired before touching "
        "the ceiling:\n"
        "  (1) FULL CLOSURE — a chain now runs every case. Chains with no "
        "declined row left: %s. The fix is to DELETE that chain's entry (never "
        "decrement it to 0) and lower the rc446 ratchet's "
        "CEIL_C_REJECTED_CHAINS in the same change.\n"
        "  (2) PARTIAL CLOSURE — C accepts SOME of a chain's cases and declines "
        "the rest: %s (measured, seeded). That is a NARROWING BUG, not a drain: "
        "an arm answering part of an op's domain and refusing the rest. Fix the "
        "arm; do not write the smaller number here.\n"
        "  (3) A NEW DECLINE — a chain that used to run now declines: %s. That "
        "is a regression.\n"
        "  per-status breakdown of every decline: %s\n"
        "  (a status other than SRMECH_ERR_NOT_IMPL is the `#T1146` shape — C "
        "REJECTING what Python ACCEPTS, e.g. a domain guard the Python twin "
        "does not have.)"
        % (closed, partial, grew, dict(sorted(statuses.items()))))


def test_no_accepted_chain_reports_measured_while_measuring_nothing():
    """UNMEASURED, made mechanical.

    A chain every one of whose cases CLASSIFIED (rejected / non-finite) has
    produced no comparison at all, yet contributes no divergence and so reads
    as fine. The set is pinned ``==`` and EMPTY at rc450; adding a member is a
    deliberate red edit that has to state its reason, which is the difference
    between a known hole and a silence.
    """
    require_native("srmech_chain_run value parity")
    _rows, _tally, per_chain = _measure_all()
    accepted = {n for n, verdicts in per_chain.items()
                if any(v in (V_IDENTICAL, V_DIVERGENT) for v in verdicts)}
    unmeasured = {n for n, verdicts in per_chain.items()
                  if n in accepted
                  and not any(v == V_IDENTICAL for v in verdicts)}
    assert unmeasured == UNMEASURED_CHAINS, (
        "chains that compared nothing: %s; the pinned set is %s"
        % (sorted(unmeasured), sorted(UNMEASURED_CHAINS)))


def test_the_compared_set_agrees_with_the_rc446_ratchet():
    """CROSS-ARTIFACT TIE. The chains this gate actually COMPARED must be
    exactly the chains the rc446 ratchet reports as accepted.

    Two harnesses, one claim. If they disagree, one of them is wrong and the
    disagreement is the finding — which is why this is an assertion and not a
    print."""
    require_native("srmech_chain_run value parity")
    import test_c_cascade_parity_ratchet_rc446 as ratchet
    _rows, _tally, per_chain = _measure_all()
    compared = {n for n, verdicts in per_chain.items()
                if any(v in (V_IDENTICAL, V_DIVERGENT) for v in verdicts)}
    _rejected, accepted = ratchet._measure()
    assert compared == set(accepted), (
        "this gate compared %s; the rc446 ratchet calls %s accepted. The two "
        "harnesses disagree, and that disagreement is the finding."
        % (sorted(compared), sorted(accepted)))


def test_reports_the_full_state(capsys):
    """Visibility: the per-verdict tally every run, so it is never invisible."""
    require_native("srmech_chain_run value parity")
    rows, tally, per_chain = _measure_all()
    with capsys.disabled():
        print("\n  C-vs-Python VALUE parity @ srmech %s (ABI %s)"
              % (_native.NATIVE_VERSION if hasattr(_native, "NATIVE_VERSION")
                 else "?", _native.NATIVE_ABI_VERSION))
        print("  population: %d proof cases over %d chains"
              % (len(rows), len(per_chain)))
        for verdict in sorted(tally):
            print("    %-34s %d" % (verdict, tally[verdict]))
    assert sum(tally.values()) == len(rows)
