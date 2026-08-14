"""rc431 `#T1129` — the native contract-divergence census.

THE QUESTION
------------
srmech is MULTI-IMPLEMENTATION, not "Python + a C accelerator": the capability is
the invariant and the two projections are co-equal (see
``[[user_stance_srmech_is_multi_implementation_not_python_with_c_accel]]``).  A
``*_c`` ctypes wrapper in ``srmech/_native/__init__.py`` returns ``None`` to mean
*"native absent -- run the pure body"*.  But **84 of those wrappers (72 under the
criterion below) also return ``None`` from a predicate on their own ARGUMENTS**,
and for some of them the C peer would have returned an ERROR STATUS for exactly
that input.  When that happens ``None`` is OVERLOADED: it carries both *"native
absent"* and *"C refused this input"*, the caller cannot tell them apart, and the
invalidity signal is destroyed at the boundary.  If the pure body then does not
reject the input either, the C guard is **dead through the Python front door** --
a defensive guard that no Python call can ever cause to fire -- and the op
returns a value on an input its own co-equal projection calls invalid.

This file measures the size of that set.

THE CENSUS CRITERION (pre-registered before the scan was run)
-------------------------------------------------------------
A wrapper predicate is a CANDIDATE iff, inside a top-level ``def *_c``, there is
an ``if <test>: return None`` where

  1. the ``if`` occurs textually BEFORE the first ``LIB.<attr>`` access (so it
     cannot be a post-call status check), and
  2. the test mentions none of ``has_native`` / ``LIB`` / ``_bound`` (a
     native-presence guard), and
  3. the test mentions neither ``SRMECH_OK`` nor ``SRMECH_ERR`` (a status check).

Each candidate is then classified into FOUR mutually exclusive buckets:

  ``BENIGN_CAPABILITY``
      The C peer has no error-status return, or none whose condition shares a
      normalised comparison atom with the wrapper predicate.  ``None`` correctly
      means *"native declines; the pure body is the COMPLETE alternative."*  This
      is the contract working, and it is expected to be the majority.

  ``CONCURRING_GUARD``
      The C peer returns an error status for the predicate AND the pure arm
      rejects the same input.  Both arms refuse; correct.

  ``DIVERGENT_DEAD_GUARD``
      The C peer returns an error status for the predicate AND the pure arm
      RETURNS A VALUE.  **The defect.**

  ``UNDECIDED``
      No input satisfying the predicate could be constructed through any public
      caller, so the pure arm was never exercised.  Reported, never guessed.

CONTROLS (pre-registered before the scan; both fire -- see ``controls``)
-----------------------------------------------------------------------
  POSITIVE  ``iir_lfilter_f64_c`` MUST land ``DIVERGENT_DEAD_GUARD`` --
            **on the rc430 tree**. See the note below; this control is
            state-dependent by construction and the instrument knows it.
  NEGATIVE  ``lll_reduce_c``'s delta predicate MUST NOT land
            ``DIVERGENT_DEAD_GUARD`` -- ``_lll_reduce_pure`` raises
            ``ValueError`` for delta outside (1/4, 1], so both arms refuse.
  FALSIFIER If ``DIVERGENT_DEAD_GUARD`` is EMPTY while the positive control
            fires, that is a contradiction and the instrument -- not the tree --
            is broken.

THE POSITIVE CONTROL IS THE THING THIS rc REPAIRS
-------------------------------------------------
``iir`` is both the instrument's positive control AND rc431's headline repair,
so the control CANNOT keep firing once the repair lands -- the probe that
returned ``[0.0, 0.0, 0.0]`` on rc430 now raises ``ValueError``. An instrument
that simply asserted "the control fired" would therefore go red the moment its
own finding was fixed, and the obvious way to quiet it (delete the control)
would leave every future zero unverifiable.

So the run is TWO-STATE and names which state it is in:

  ``PRE_REPAIR``   the ``iir`` front door still accepts ``b == []``.
                   ``iir_lfilter_f64_c`` MUST be ``DIVERGENT_DEAD_GUARD``.
                   This is the state rc430 was measured in, and the committed
                   NDJSON alongside this file records it.
  ``POST_REPAIR``  the front door refuses it with a house-style ``ValueError``.
                   ``iir_lfilter_f64_c`` MUST be ``CONCURRING_GUARD`` -- both
                   arms now refuse -- and ``DIVERGENT_DEAD_GUARD`` MUST be
                   empty. This is the state from rc431 onward.

Neither state is a pass by default: the run fails if the observed classification
does not match the state the tree is actually in, which keeps the control a
measurement in both directions rather than a fact about one commit.

BLIND SPOT (verbatim, per the rc431 specification)
--------------------------------------------------
**BLIND SPOT.** This instrument classifies a wrapper by its *source predicate*
and a C peer by its *guard block*, both read statically, and confirms membership
by *executing the Python arm only*.  It therefore **cannot see** a divergence in
which both arms return a value and the values differ -- the numerically-wrong-
answer class, which is this project's worst.  It also runs with
``SRMECH_EXPECT_PURE=1`` against a stale ABI-12 ``.so``, so **no C code was
executed to produce any number here**; the C side is read, not run.  A wrapper
whose ``return None`` predicate and whose C guard disagree with each other would
be classified from the predicate and the disagreement missed.  The 44 rc430
acceptors that took every edge argument remain **UNADJUDICATED** on the value
axis; this rc adjudicates only the subset where one arm *refuses*.

THE CENSUS CLAIM CARRIED FORWARD FROM rc430 (verbatim, per the specification)
-----------------------------------------------------------------------------
**The srmech group/semigroup census is BOUNDED, not cardinal.** Its measured
**floor is 31 of 245 Tier-A ops** (the rc427 carrier ladder u the rc430
worked-example oracle u ``srmech.cascade.autocorrelation``), under a **hard cap
of 141 of 245** -- the ops for which any orbit-closure verdict is reachable at
all.  It is bounded because the verdict **depends on the seed set**, which is a
**window**: the pre-registered control ``cyclic_mod_add``, provably a
permutation, returns GROUP seeded from the rc430 oracle and SEMIGROUP seeded from
``srmech.dsl.list_catalog_ops``, and ``srmech.math.text.fold_marks`` flips in
both directions across the same pair.  rc430's claim that generation by ``f``
removes the window is **retracted**.  **No cardinal may be stated for this
census** until a seed-invariance criterion exists, and none does.

A floor that only ever rises is not a measurement.  If a later seed lowers it,
the floor goes DOWN and this file says so.  This is not a ratchet.

Run:  PYTHONPATH=docs/srmech/python SRMECH_EXPECT_PURE=1 \
      python3 docs/srmech/notes/_p1_native_contract_divergence_rc431.py
"""

from __future__ import annotations

import ast
import json
import os
import pathlib
import re
import sys
import traceback

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[3]                     # .../mlehaptics
SRMECH_ROOT = ROOT / "docs" / "srmech"
NATIVE_PY = SRMECH_ROOT / "python" / "srmech" / "_native" / "__init__.py"
C_SRC_DIR = SRMECH_ROOT / "c" / "src"
OUT = HERE.with_suffix(".ndjson")

sys.path.insert(0, str(SRMECH_ROOT / "python"))
os.environ.setdefault("SRMECH_EXPECT_PURE", "1")

RECORDS: list[dict] = []


def emit(**row):
    RECORDS.append(row)


# --------------------------------------------------------------------------
# Phase A -- the wrapper scan
# --------------------------------------------------------------------------

def scan_wrappers():
    src = NATIVE_PY.read_text(encoding="utf-8")
    tree = ast.parse(src)
    total = 0
    cands: list[dict] = []
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef) or not fn.name.endswith("_c"):
            continue
        total += 1
        lib_lines = [
            n.lineno for n in ast.walk(fn)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
            and n.value.id == "LIB"
        ]
        first_lib = min(lib_lines) if lib_lines else 10 ** 9
        syms = sorted({
            n.attr for n in ast.walk(fn)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
            and n.value.id == "LIB"
        })
        for node in ast.walk(fn):
            if not isinstance(node, ast.If):
                continue
            body = node.body
            if not (len(body) == 1 and isinstance(body[0], ast.Return)):
                continue
            rv = body[0].value
            if not (rv is None or (isinstance(rv, ast.Constant) and rv.value is None)):
                continue
            if node.lineno >= first_lib:
                continue
            test = ast.get_source_segment(src, node.test) or ""
            if any(t in test for t in ("has_native", "LIB", "_bound")):
                continue
            if "SRMECH_OK" in test or "SRMECH_ERR" in test:
                continue
            cands.append(dict(wrapper=fn.name, line=node.lineno,
                              predicate=" ".join(test.split()), c_symbols=syms))
    return total, cands


# --------------------------------------------------------------------------
# Phase B -- the C-side guard extraction + atom overlap
# --------------------------------------------------------------------------

_ERR_RE = re.compile(r"return\s+(SRMECH_ERR_\w+)\s*;")
_ATOM_RE = re.compile(r"([A-Za-z_][\w\.\[\]\(\)]*)\s*(==|!=|<=|>=|<|>)\s*([\w\.\-]+)")
_TOKSTRIP = re.compile(r"_(list|bytes|buf|arr|vals|components)$")


def index_c_bodies():
    bodies: dict[str, tuple[str, str]] = {}
    for path in sorted(C_SRC_DIR.glob("*.c")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^(\w[\w \t\*]*?)\b(srmech_\w+)\s*\(", text, re.M):
            name = m.group(2)
            open_brace = text.find("{", m.end())
            semi = text.find(";", m.end())
            if open_brace < 0 or (semi != -1 and semi < open_brace):
                continue                      # a declaration, not a definition
            depth, j = 0, open_brace
            while j < len(text):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            bodies[name] = (path.name, text[open_brace:j + 1])
    return bodies


def c_error_guards(body: str):
    """`(condition_text, SRMECH_ERR_*)` for every error-status return under an if."""
    out = []
    for m in _ERR_RE.finditer(body):
        k = m.start()
        window_start = max(0, k - 400)
        seg = body[window_start:k]
        ifs = list(re.finditer(r"if\s*\(", seg))
        if not ifs:
            continue
        s = window_start + ifs[-1].end() - 1
        depth, j = 0, s
        while j < len(body):
            if body[j] == "(":
                depth += 1
            elif body[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append((" ".join(body[s + 1:j].split()), m.group(1)))
    return out


def _norm(tok: str) -> str:
    tok = re.sub(r"\[[^\]]*\]", "", tok.strip())
    tok = re.sub(r"^len\((.*)\)$", r"\1", tok).strip()
    return _TOKSTRIP.sub("", tok)


def atoms(text: str) -> set:
    out = set()
    for m in _ATOM_RE.finditer(text.replace("\n", " ")):
        lhs, op, rhs = _norm(m.group(1)), m.group(2), m.group(3).strip()
        if rhs in ("NULL", "None"):
            rhs = "NULL"
        rhs = rhs.rstrip("uUlL")
        try:
            rhs = str(int(float(rhs)))
        except ValueError:
            pass
        out.add((lhs, op, rhs))
    return out


# --------------------------------------------------------------------------
# Phase C -- the executable probe of the PURE arm, at a public front door
# --------------------------------------------------------------------------
# Each entry: wrapper -> list of (predicate_case, callable-building thunk).
# The thunk must construct an input SATISFYING the wrapper predicate and call the
# public op that would dispatch through that wrapper.  RAISED => the pure arm
# refuses too; RETURNED => the pure arm accepts what C refuses.

def _probe_iir_nb0():
    from srmech.signal_processing.closed_form_ops import iir
    return iir.op([1.0, 2.0, 3.0], [], [1.0])


def _probe_iir_na0():
    from srmech.signal_processing.closed_form_ops import iir
    return iir.op([1.0, 2.0, 3.0], [1.0], [])


def _probe_iir_a0_zero():
    from srmech.signal_processing.closed_form_ops import iir
    return iir.op([1.0, 2.0, 3.0], [1.0], [0.0])


def _probe_svd_m_lt_n():
    from srmech.math.laplacian import mat_svd
    from srmech.math.mat import Mat
    return mat_svd(Mat.from_rows([[1.0, 2.0, 3.0]]))


def _probe_sturm_n_lt_1():
    from srmech.cascade.matrix_cascades import eigvals_exact
    from srmech.math.mat import Mat
    return eigvals_exact(Mat.from_rows([]))


def _probe_split_defect_n_lt_2():
    from srmech.biology.genome import split_defect
    return split_defect(bytes([1]), 1)


def _probe_split_defect_k_ge_n():
    from srmech.biology.genome import split_defect
    return split_defect(bytes([1, 2]), 2)


def _probe_bessel_scale_bits_lt_8():
    from srmech.music._bessel import bessel_j_fixed
    return bessel_j_fixed(0, 1, 2, scale_bits=4)


def _probe_lll_delta_out_of_range():
    """NEGATIVE CONTROL -- the pure arm MUST refuse (delta outside (1/4, 1])."""
    from srmech.cascade.matrix_cascades import lll_reduce
    return lll_reduce([[1, 0], [0, 1]], delta=(1, 8))


PROBES = {
    "iir_lfilter_f64_c": [
        ("nb == 0", _probe_iir_nb0),
        ("na == 0", _probe_iir_na0),
        ("a[0] == 0.0", _probe_iir_a0_zero),
    ],
    "svd_f64_c": [("m < n", _probe_svd_m_lt_n)],
    "sturm_isolate_c": [("n < 1", _probe_sturm_n_lt_1)],
    "split_defect_c": [
        ("n < 2", _probe_split_defect_n_lt_2),
        ("k >= n", _probe_split_defect_k_ge_n),
    ],
    "bessel_j_fixed_c": [("scale_bits < 8", _probe_bessel_scale_bits_lt_8)],
    "lll_reduce_c": [("delta outside (1/4, 1]", _probe_lll_delta_out_of_range)],
}


def run_probe(thunk):
    """Run one probe.  A raise whose innermost frame is THIS FILE is a HARNESS
    ERROR (a mis-built probe), never a refusal by the op -- recording one as
    ``RAISED`` would manufacture a false ``CONCURRING_GUARD``.  It gets its own
    outcome so it can never be counted as evidence.  This guard exists because
    the first run did exactly that: the ``bessel_j_fixed`` probe passed
    ``scale_bits`` positionally to a keyword-only parameter, and the resulting
    ``TypeError`` was recorded as the pure arm refusing the input."""
    try:
        value = thunk()
        return "RETURNED", repr(value)[:120], None
    except Exception as exc:                                  # noqa: BLE001
        tb = traceback.extract_tb(exc.__traceback__)[-1]
        site = f"{pathlib.Path(tb.filename).name}:{tb.lineno}"
        if pathlib.Path(tb.filename).name == HERE.name:
            return "HARNESS_ERROR", f"{type(exc).__name__}: {str(exc)[:100]}", site
        return "RAISED", f"{type(exc).__name__}: {str(exc)[:100]}", site


# --------------------------------------------------------------------------
# Phase D -- ADJUDICATION of the mechanical DIVERGENT candidates
# --------------------------------------------------------------------------
# The mechanical rule ("C returns an error status for this predicate AND the
# pure arm returns a value") cannot distinguish two very different things:
#
#   (a) the input is OUTSIDE the op's declared mathematical domain, so the pure
#       arm is returning a value for nonsense -- the defect; and
#   (b) the input is a perfectly VALID mathematical input that the particular C
#       kernel does not implement (a wide matrix for a tall-only one-sided-Jacobi
#       SVD, a 0x0 operator), so the pure arm is returning the CORRECT answer and
#       the C status is a capability floor -- not a defect.
#
# Both look identical to the scanner: SRMECH_ERR_BAD_INPUT on one side, a value
# on the other.  The discriminator is therefore stated explicitly and applied by
# hand, WITH its evidence, per candidate:
#
#   ** Is an input satisfying the predicate inside the op's declared domain? **
#     yes -> BENIGN_CAPABILITY (the pure answer is correct; C declines a shape)
#     no  -> DIVERGENT_DEAD_GUARD (the pure arm answers an invalid question)
#
# Every mechanical DIVERGENT candidate MUST appear here or the run fails, so a
# newly-flagged wrapper can never be silently absorbed.

ADJUDICATION = {
    ("iir_lfilter_f64_c", "nb == 0"): dict(
        verdict="DIVERGENT_DEAD_GUARD",
        rationale=(
            "b == [] is NOT a filter: `iir` documents `b` as the numerator "
            "coefficient sequence, and a coefficient sequence with no "
            "coefficients has no z-transform to apply. The pure body returns "
            "[0.0]*n by silently zero-padding to len(a) in _lfilter_direct, so "
            "the op answers an invalid question with a plausible-looking "
            "all-zero signal. The C peer returns SRMECH_ERR_NULL_ARG for the "
            "same input, and the ctypes wrapper RE-STATES that predicate and "
            "then discards it by returning None -- which op() reads as 'native "
            "absent'. Both other cases of the same predicate (na == 0, "
            "a[0] == 0.0) escape as a raw IndexError / ZeroDivisionError from "
            "inside _lfilter_direct rather than a house-style ValueError."),
    ),
    ("svd_f64_c", "m < n"): dict(
        verdict="BENIGN_CAPABILITY",
        rationale=(
            "A wide (m < n) matrix is a completely valid SVD input and mat_svd "
            "returns the correct decomposition for it. The C guard is a "
            "capability floor: srmech_svd_f64 implements the one-sided Jacobi "
            "sweep, which requires a tall/square operand. mat_svd's own comment "
            "names the Gram-eigen route 'the COMPLETE alternative (complex "
            "input, m<n, no-C host, or a non-converged native sweep)', so None "
            "here means exactly what None is supposed to mean. m == 0 / n == 0, "
            "the other half of the same predicate, is rejected at the front "
            "door with ValueError before the wrapper is reached."),
    ),
    ("sturm_isolate_c", "n < 1"): dict(
        verdict="BENIGN_CAPABILITY",
        rationale=(
            "n < 1 is the 0x0 operator, whose spectrum is the empty list -- and "
            "eigvals_exact returns []. That is the correct answer, and it "
            "matches the degenerate-empty convention already shipped elsewhere "
            "in the cascade layer (lll_reduce([]) -> []). The C guard is a "
            "defensive floor over a raw pointer + length pair, where n == 0 "
            "would pair with a NULL buffer; handing back to the pure body is "
            "the right response, not a lost error."),
    ),
}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    import srmech
    from srmech.introspect.tool_schema import warmup_all, get_tool_schema

    warmup_all()
    emit(kind="env", srmech_file=srmech.__file__, version=srmech.__version__,
         registry=len(get_tool_schema().tools),
         describe_keys=len(srmech.describe()),
         expect_pure=os.environ.get("SRMECH_EXPECT_PURE"))
    print(f"srmech {srmech.__file__} {srmech.__version__}")

    total, cands = scan_wrappers()
    bodies = index_c_bodies()
    emit(kind="phase_a", wrappers_scanned=total, candidate_predicates=len(cands),
         c_bodies_indexed=len(bodies))
    print(f"wrappers scanned: {total}   candidate predicates: {len(cands)}")

    verdicts = {"BENIGN_CAPABILITY": 0, "CONCURRING_GUARD": 0,
                "DIVERGENT_DEAD_GUARD": 0, "UNDECIDED": 0}
    divergent, undecided = [], []
    harness_errors: list[str] = []
    unadjudicated: list[tuple] = []
    mech_divergent: list[str] = []

    for cand in cands:
        mechanical, adjudication = None, None
        pred_atoms = atoms(cand["predicate"])
        overlap = None
        for sym in cand["c_symbols"]:
            if sym not in bodies:
                continue
            cfile, body = bodies[sym]
            for cond, err in c_error_guards(body):
                inter = sorted(pred_atoms & atoms(cond))
                if inter:
                    overlap = dict(c_symbol=sym, c_file=cfile, c_error=err,
                                   c_condition=cond[:160], shared_atoms=inter)
                    break
            if overlap:
                break

        if overlap is None:
            verdict, probe = "BENIGN_CAPABILITY", None
            reason = ("no C error-status guard shares a comparison atom with the "
                      "predicate -- None means 'native declines, pure is COMPLETE'")
        else:
            cases = PROBES.get(cand["wrapper"], [])
            if not cases:
                verdict, probe = "UNDECIDED", None
                reason = ("no input satisfying the predicate could be constructed "
                          "through a public caller -- the pure arm was never "
                          "exercised, so no verdict is claimed")
            else:
                probe = []
                for case, thunk in cases:
                    outcome, detail, site = run_probe(thunk)
                    probe.append(dict(case=case, outcome=outcome,
                                      detail=detail, site=site))
                harness = [p for p in probe if p["outcome"] == "HARNESS_ERROR"]
                if harness:
                    harness_errors.extend(
                        f"{cand['wrapper']} [{p['case']}] {p['detail']}"
                        for p in harness)
                returned = [p for p in probe if p["outcome"] == "RETURNED"]
                if returned:
                    mechanical = "DIVERGENT_DEAD_GUARD"
                    reason = ("MECHANICAL: the C peer returns an error status "
                              "for this predicate and the pure arm RETURNS A "
                              "VALUE")
                    # Phase D -- every mechanical DIVERGENT must be adjudicated.
                    key = (cand["wrapper"], returned[0]["case"])
                    adj = ADJUDICATION.get(key)
                    if adj is None:
                        unadjudicated.append(key)
                        verdict = "DIVERGENT_DEAD_GUARD"
                        adjudication = None
                    else:
                        verdict = adj["verdict"]
                        adjudication = dict(key=list(key), **adj)
                elif harness:
                    mechanical = verdict = "UNDECIDED"
                    reason = ("every probe failed inside the harness itself -- "
                              "no evidence about the pure arm")
                    adjudication = None
                else:
                    mechanical = verdict = "CONCURRING_GUARD"
                    reason = "both arms refuse the same input"
                    adjudication = None

        verdicts[verdict] += 1
        row = dict(kind="candidate", verdict=verdict,
                   mechanical_verdict=mechanical, adjudication=adjudication,
                   reason=reason, overlap=overlap, probe=probe, **cand)
        emit(**row)
        if mechanical == "DIVERGENT_DEAD_GUARD":
            mech_divergent.append(f"{cand['wrapper']}:{cand['line']}")
        if verdict == "DIVERGENT_DEAD_GUARD":
            divergent.append(row)
        elif verdict == "UNDECIDED":
            undecided.append(row)

    # ---- controls ---------------------------------------------------------
    # Both controls are RUN, not merely read off the classification: a control
    # that passes because its probe never executed is not a measurement.
    neg_outcome, neg_detail, neg_site = run_probe(_probe_lll_delta_out_of_range)
    pos_outcome, pos_detail, _ = run_probe(_probe_iir_nb0)
    emit(kind="control_probe", control="negative", target="lll_reduce_c",
         case="delta outside (1/4, 1]", outcome=neg_outcome,
         detail=neg_detail, site=neg_site,
         expected="RAISED -- _lll_reduce_pure refuses the same delta the "
                  "wrapper predicate declines, so both arms concur")
    emit(kind="control_probe", control="positive", target="iir_lfilter_f64_c",
         case="nb == 0", outcome=pos_outcome, detail=pos_detail,
         expected="RETURNED -- the pure arm answers an input C refuses")
    print(f"negative control probe: {neg_outcome} {neg_detail} @ {neg_site}")
    print(f"positive control probe: {pos_outcome} {pos_detail}")

    # Which state is the tree in? Decided by EXECUTION, not by a version string.
    state = "POST_REPAIR" if pos_outcome == "RAISED" else "PRE_REPAIR"
    pos = any(r["wrapper"] == "iir_lfilter_f64_c" for r in divergent)
    neg = not any(r["wrapper"] == "lll_reduce_c" for r in divergent)
    if state == "PRE_REPAIR":
        control_ok = pos
        control_expect = "iir_lfilter_f64_c -> DIVERGENT_DEAD_GUARD"
    else:
        control_ok = (not pos) and not divergent
        control_expect = ("iir front door refuses b == [] -> "
                          "iir_lfilter_f64_c CONCURRING_GUARD and "
                          "DIVERGENT_DEAD_GUARD empty")
    contradiction = pos and not divergent            # structurally impossible
    emit(kind="controls", tree_state=state,
         positive_control=control_expect, positive_fired=control_ok,
         positive_probe_outcome=pos_outcome, positive_probe_detail=pos_detail,
         negative_control="lll_reduce_c delta predicate -> not DIVERGENT",
         negative_held=neg,
         falsifier="DIVERGENT empty while positive control fires",
         falsifier_tripped=contradiction,
         harness_errors=harness_errors,
         unadjudicated=[list(k) for k in unadjudicated])
    print("tree state:", state)

    # The null is BOUNDED, not EMPTY and not REFUTED: 25 candidate predicates
    # could not be reached through any public caller, so the pure arm was never
    # exercised for them and no verdict is claimed.
    null_class = "BOUNDED" if undecided else ("REFUTED" if divergent else "EMPTY")
    emit(kind="summary", verdicts=verdicts, null_classification=null_class,
         mechanical_divergent=mech_divergent,
         adjudicated_divergent=[f"{r['wrapper']}:{r['line']}" for r in divergent],
         undecided_wrappers=sorted({r["wrapper"] for r in undecided}),
         bound=("the 25 UNDECIDED predicates are unreachable through any public "
                "caller, so this census bounds the divergent set from below, "
                "not from above"))

    print(json.dumps(verdicts, indent=2))
    print("null classification:", null_class)
    print(f"positive control ({state}) satisfied:", control_ok,
          "  negative control held:", neg)
    print("harness errors:", harness_errors or "none")
    print("MECHANICAL DIVERGENT:", mech_divergent)
    print("ADJUDICATED DIVERGENT:",
          [f"{r['wrapper']}:{r['line']}" for r in divergent])

    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in RECORDS:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
    print("wrote", OUT, len(RECORDS), "records")

    if not control_ok:
        raise SystemExit(
            f"INSTRUMENT REFUTED: tree state is {state} but the classification "
            f"does not match it. Expected: {control_expect}. "
            f"iir in DIVERGENT set: {pos}; DIVERGENT set: "
            f"{[r['wrapper'] for r in divergent]}")
    if contradiction:
        raise SystemExit("INSTRUMENT REFUTED: falsifier tripped")
    if unadjudicated:
        raise SystemExit(
            f"UNADJUDICATED mechanical divergences: {unadjudicated} -- every "
            f"mechanical DIVERGENT candidate must carry a recorded adjudication")
    if harness_errors:
        raise SystemExit(f"HARNESS ERRORS: {harness_errors}")


if __name__ == "__main__":
    main()
