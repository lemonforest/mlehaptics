"""rc431 `#T1129` -- an op owns its EXCEPTION contract, and its C peer's.

``tests/test_front_door_error_contract_rc407.py`` established that a front door
owns its exception contract, not just its happy path. This gate is the same axis
one level down: srmech is MULTI-IMPLEMENTATION, so an op owns the exception
contract of BOTH its projections, and the two must refuse the same inputs.

THE DEFECT THIS GATE PINS
-------------------------
A ``*_c`` ctypes wrapper returns ``None`` to mean *"native absent -- run the
pure body"*. Many wrappers ALSO return ``None`` from a predicate on their own
ARGUMENTS. Where the C peer would have returned an error status for that same
input, ``None`` is OVERLOADED -- it carries both *"native absent"* and *"C
refused this input"* -- and the invalidity signal is destroyed at the boundary.
If the pure body then does not reject the input either, the C guard is **dead
through the Python front door**: a defensive guard no Python call can cause to
fire, with the op returning a value on an input its own co-equal projection
calls invalid.

``srmech.signal_processing.iir`` was such a site through rc430:

    C peer (srmech_iir.c:64-77)   nb == 0 || na == 0  -> SRMECH_ERR_NULL_ARG
                                  a0 == 0.0           -> SRMECH_ERR_BAD_INPUT
    ctypes wrapper (:10419)       re-states the predicate, returns None
    op() pure body                b == []  -> RETURNED [0.0] * len(signal)
                                  a == []  -> raw IndexError      @ iir.py:56
                                  a[0]== 0 -> raw ZeroDivisionError @ iir.py:57

Python moved to C, never the reverse: C is the already-shipped, stricter,
correct contract, and the capability is the invariant across co-equal
projections.

WHAT THIS GATE ASSERTS
----------------------
1. STRICT ZERO on the adjudicated divergence: every case of the repaired
   contract must raise ``ValueError`` from the FRONT DOOR, before dispatch, so
   the native and pure arms refuse identically.
2. A DOWN-ONLY CEIL on the residual ``UNDECIDED`` population -- candidate
   predicates that overlap a C error guard but for which no input could be
   constructed through a public caller, so the pure arm was never exercised.
   That number may only fall.

The scan derives from LIVE wrapper source and LIVE C guard blocks, so
registering an op with a native peer moves it. It is listed in
``tools/ripple_gates.txt`` for that reason.

WHAT THIS GATE DOES NOT SEE
---------------------------
It cannot see a divergence in which BOTH arms return a value and the values
differ -- the numerically-wrong-answer class, this project's worst. It reads the
C side and executes only the Python side. The full statement lives in the census
note's BLIND SPOT section.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

SRMECH_PY = pathlib.Path(__file__).resolve().parents[1]
NATIVE_PY = SRMECH_PY / "srmech" / "_native" / "__init__.py"
C_SRC_DIR = SRMECH_PY.parent / "c" / "src"

# Down-only. rc431 measured 25 candidate predicates that overlap a C error guard
# but could not be reached through any public caller. It may only fall: each
# decrement is either a wrapper predicate that became reachable and was
# adjudicated, or one that was removed. NEVER raise this to make a gate green --
# a rise means a new unadjudicated overloaded-None site was introduced.
CEIL_UNDECIDED = 25

_ERR_RE = re.compile(r"return\s+(SRMECH_ERR_\w+)\s*;")
_ATOM_RE = re.compile(r"([A-Za-z_][\w\.\[\]\(\)]*)\s*(==|!=|<=|>=|<|>)\s*([\w\.\-]+)")
_TOKSTRIP = re.compile(r"_(list|bytes|buf|arr|vals|components)$")


def _norm(tok: str) -> str:
    tok = re.sub(r"\[[^\]]*\]", "", tok.strip())
    tok = re.sub(r"^len\((.*)\)$", r"\1", tok).strip()
    return _TOKSTRIP.sub("", tok)


def _atoms(text: str) -> set:
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


def _index_c_bodies() -> dict:
    bodies = {}
    for path in sorted(C_SRC_DIR.glob("*.c")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^(\w[\w \t\*]*?)\b(srmech_\w+)\s*\(", text, re.M):
            name = m.group(2)
            brace = text.find("{", m.end())
            semi = text.find(";", m.end())
            if brace < 0 or (semi != -1 and semi < brace):
                continue
            depth, j = 0, brace
            while j < len(text):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            bodies[name] = text[brace:j + 1]
    return bodies


def _c_error_guard_atoms(body: str) -> set:
    out = set()
    for m in _ERR_RE.finditer(body):
        start = max(0, m.start() - 400)
        seg = body[start:m.start()]
        ifs = list(re.finditer(r"if\s*\(", seg))
        if not ifs:
            continue
        s = start + ifs[-1].end() - 1
        depth, j = 0, s
        while j < len(body):
            if body[j] == "(":
                depth += 1
            elif body[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out |= _atoms(body[s + 1:j])
    return out


def _overloaded_none_candidates():
    """Wrapper predicates that return None on an INPUT-SHAPE test, before any
    LIB call, that also overlap a C error-status guard."""
    src = NATIVE_PY.read_text(encoding="utf-8")
    tree = ast.parse(src)
    bodies = _index_c_bodies()
    hits = []
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef) or not fn.name.endswith("_c"):
            continue
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
            if not isinstance(node, ast.If) or node.lineno >= first_lib:
                continue
            body = node.body
            if not (len(body) == 1 and isinstance(body[0], ast.Return)):
                continue
            rv = body[0].value
            if not (rv is None
                    or (isinstance(rv, ast.Constant) and rv.value is None)):
                continue
            test = ast.get_source_segment(src, node.test) or ""
            if any(t in test for t in ("has_native", "LIB", "_bound")):
                continue
            if "SRMECH_OK" in test or "SRMECH_ERR" in test:
                continue
            pred_atoms = _atoms(test)
            for sym in syms:
                if sym in bodies and pred_atoms & _c_error_guard_atoms(bodies[sym]):
                    hits.append((fn.name, node.lineno, " ".join(test.split())))
                    break
    return hits


# ---------------------------------------------------------------------------
# 1 -- STRICT ZERO: the adjudicated divergence must be repaired, at the FRONT DOOR
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "b, a, why",
    [
        ([], [1.0], "b == [] is not a filter -- an empty numerator has no "
                    "z-transform to apply; through rc430 this RETURNED "
                    "[0.0]*n by zero-padding to len(a)"),
        ([1.0], [], "a == [] -- through rc430 this escaped as a raw IndexError "
                    "from inside _lfilter_direct"),
        ([1.0], [0.0], "a[0] == 0 is not a valid recursion -- through rc430 "
                       "this escaped as a raw ZeroDivisionError"),
    ],
)
def test_iir_front_door_refuses_what_its_c_peer_refuses(b, a, why):
    """srmech_iir_lfilter_f64 returns an error status for each of these; the
    Python front door must raise ValueError for each, BEFORE dispatch, so both
    co-equal projections refuse identically."""
    from srmech.signal_processing.closed_form_ops import iir

    with pytest.raises(ValueError) as excinfo:
        iir.op([1.0, 2.0, 3.0], b, a)
    assert "iir:" in str(excinfo.value), (
        f"the guard must name the op in house style; got {excinfo.value!r} "
        f"({why})"
    )


def test_iir_still_filters_valid_input():
    """The repair must not have been bought by rejecting valid input -- the
    negative control for the guard above."""
    from srmech.signal_processing.closed_form_ops import iir

    y = iir.op([1.0, 0.0, 0.0, 0.0], [1.0], [1.0, -0.5])
    assert y == [1.0, 0.5, 0.25, 0.125], y
    # the biquad branch still reaches _lfilter_direct with length-3 coefficient
    # vectors, which is why op() is the necessary AND sufficient guard site
    assert iir.op([1.0, 2.0], [1.0], [1.0],
                  biquad_sections=[[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]]) == [1.0, 2.0]


def test_lll_reduce_and_signed_sum_squared_refuse_shape_in_house_style():
    """The other two rc431 repairs: a shape defect must raise the ValueError the
    docstring promises, not a bare TypeError from a coercion comprehension."""
    from srmech.cascade.matrix_cascades import lll_reduce
    from srmech.cascade import signed_sum_squared

    for bad in (5, None, [1, 2]):
        with pytest.raises(ValueError, match="lll_reduce:"):
            lll_reduce(bad)
    assert lll_reduce([]) == [], "the empty lattice is degenerate-empty, not malformed"

    for bad in (5, [1, 0]):
        with pytest.raises(ValueError, match="signed_sum_squared:"):
            signed_sum_squared(bad)
    assert signed_sum_squared([[1, 0, 1], [0, 0, 1]]) == [0, 4, 4]


# ---------------------------------------------------------------------------
# 2 -- DOWN-ONLY CEIL on the unadjudicated residual
# ---------------------------------------------------------------------------

def test_overloaded_none_residual_is_down_only():
    """Candidate predicates that overlap a C error guard, minus the ones rc431
    adjudicated. May only fall."""
    candidates = _overloaded_none_candidates()
    assert candidates, (
        "the scan found NO overloaded-None candidates at all -- that is not an "
        "improvement, it is the scanner failing to parse the wrapper module. "
        "The positive control below pins the shape it must be able to find."
    )
    adjudicated = {"iir_lfilter_f64_c", "svd_f64_c", "sturm_isolate_c",
                   "split_defect_c", "bessel_j_fixed_c"}
    residual = [c for c in candidates if c[0] not in adjudicated]
    assert len(residual) <= CEIL_UNDECIDED, (
        f"overloaded-None residual ROSE to {len(residual)} (ceil "
        f"{CEIL_UNDECIDED}). A rise means a new wrapper returns None from an "
        f"input-shape predicate that its C peer treats as an error, with no "
        f"adjudication. Adjudicate it in "
        f"docs/srmech/notes/_p1_native_contract_divergence_rc431.py -- do NOT "
        f"raise this number.\n  new: "
        + "\n  ".join(f"{w}:{ln}  {p}" for w, ln, p in residual[:12])
    )


def test_scanner_finds_the_known_site():
    """POSITIVE CONTROL. A scanner that returns zero because it silently failed
    to parse would make the ceil above vacuous, so pin the one site whose shape
    is documented in this file's header."""
    names = {c[0] for c in _overloaded_none_candidates()}
    assert "iir_lfilter_f64_c" in names, (
        "the scanner no longer finds iir_lfilter_f64_c's input-shape predicate "
        "-- it is parsing something other than the wrapper module, and every "
        "zero it reports is meaningless"
    )
