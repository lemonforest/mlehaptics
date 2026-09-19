"""rc477 (`#T1188`) — the shapes ``S1_RESIDUAL`` cannot express.

``tests/test_float_detour_class_rc476.py`` keys on ``1.0 / <a projected root>``
and drained to 7 in this release. Two shapes it never saw are what rc477 closed,
and both are STRICT ZERO here:

* **S3 — the stored float axis.** A NAMED axis is a label and has no carrier, so
  a table that stores ``(0.0, _S3, _S3, _S3)`` has already rounded three times
  before any caller arrives. S1 saw the ``_S3 = 1.0 / …`` assignment; it could
  not see the TABLE, nor ``mu_q61 = [_to_q61(v) for v in mu]``, which quantises
  a float axis onto a grid it was never near.
* **S5 — the reciprocal-then-multiply.** S1 keys on the reciprocal, and the
  reciprocal is not the defect: ``1.0 / n`` IS correctly rounded (0 of the 4999
  integers 2..5000 miss it). The cost is the SECOND rounding, so this scan keys
  on the **multiply**, by DATAFLOW in Python and by a bounded window in C.

⚠️ **What a shape ratchet does not prove.** It reads SPELLING, not value. It
cannot see a new float detour written in a spelling nobody has used, and it says
nothing about the C compilers' own rounding. The value claims live in
``tests/test_axis_words_are_nearest_rc477.py``; this file only stops a repaired
shape from coming back under its old name.

numpy-free; stdlib ``ast`` / ``re`` / ``tokenize`` only.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

from test_float_detour_class_rc476 import (        # the shipped scanner halves
    _C_DIRS,
    _PY_SRC,
    _files,
    _mask_c,
    _mask_py,
    _rel,
    _scan,
)

# ── S3: the stored float axis, and the Q61 projection OF a float axis ──────
#: ``_S3 = …`` / ``_S7 = …`` bound to anything, and a float literal sitting in a
#: named-axis tuple. Both are the "a label has a carrier" mistake.
S3_AXIS = r"^\s*_S[0-9]+\s*=|\(\s*0\.0\s*,\s*_S[0-9]"

#: The Q61 projection taken OF an already-float axis — the line that could only
#: quantise what three roundings had already lost.
S3_Q61 = r"_to_q61\(\s*v\s*\)\s+for\s+v\s+in\s+mu\b"

#: The C twin rc477 deleted: a local reciprocal-of-a-root helper in the chain
#: interpreter, absorbed by the private ``srmech_inv_sqrt``.
S_CR_INV = r"\bcr_inv_sqrt\b"


@pytest.mark.parametrize("name,pattern", [
    ("S3-axis", S3_AXIS),
    ("S3-q61", S3_Q61),
])
def test_s3_the_stored_float_axis_is_strict_zero(name, pattern):
    hits = _scan([_PY_SRC], (".py",), pattern, _mask_py)
    assert not hits, (
        f"{name}: a float axis is stored or projected at "
        + "; ".join(f"{f}:{ln}  {txt}" for f, ln, txt in hits)
        + ". A NAMED axis is a label and has no carrier: keep the DIRECTION as "
          "integers and put the 1/√k inside the radicand (srmech.math.qalg."
          "_axis_float / _axis_q61)."
    )


def test_the_cr_inv_sqrt_duplicate_is_gone_from_the_c_tree():
    hits = _scan(_C_DIRS, (".c", ".h"), S_CR_INV, _mask_c)
    assert not hits, (
        "cr_inv_sqrt is back at "
        + "; ".join(f"{f}:{ln}" for f, ln, _t in hits)
        + ". It is the two-rounding duplicate of srmech_inv_sqrt (misses the "
          "correctly rounded 1/√k on 101 of 399 k where srmech_inv_sqrt misses "
          "0); one op serves all callers."
    )


# ── S5: keyed on the MULTIPLY, because the reciprocal is not the defect ────
def _py_reciprocal_then_multiply():
    """``(path, line, text)`` per Python function that binds ``x = 1.0 / …``
    and then MULTIPLIES by ``x`` — the two-rounding shape, by dataflow.

    Keyed on the multiply and scoped to ONE FUNCTION BODY, so ``1.0 / n`` handed
    straight to a consumer (one rounding) is NOT a hit, and a reciprocal used
    only as a divisor is not either.

    ⚠️ The scope is ``FunctionDef`` and not ``Module``: walking the module too
    puts EVERY reciprocal name in the tree into one bag, and a same-named local
    in an unrelated function then reads as a hit. Measured while this file was
    written — it reported ``laplacian.py:915`` (``c = 1.0 / _fsqrt(…)``, no
    multiply on that line at all) because a ``c`` bound elsewhere matched."""
    out = []
    for path in _files([_PY_SRC], (".py",)):
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        try:
            tree = ast.parse(src)
        except SyntaxError:                                # pragma: no cover
            continue
        lines = src.split("\n")
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            recip = {}
            for node in ast.walk(fn):
                if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                    continue
                tgt = node.targets[0]
                val = node.value
                if not isinstance(tgt, ast.Name):
                    continue
                if (isinstance(val, ast.BinOp) and isinstance(val.op, ast.Div)
                        and isinstance(val.left, ast.Constant)
                        and val.left.value == 1.0):
                    recip[tgt.id] = node.lineno
            if not recip:
                continue
            for node in ast.walk(fn):
                names = []
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
                    names = [node.left, node.right]
                elif isinstance(node, ast.AugAssign) and isinstance(node.op,
                                                                   ast.Mult):
                    names = [node.value]
                for nd in names:
                    if isinstance(nd, ast.Name) and nd.id in recip:
                        ln = getattr(node, "lineno", nd.lineno)
                        out.append((_rel(path), ln, lines[ln - 1].strip()))
    return sorted(set(out))


#: The FILES rc477 owns: every divide-by-N site named in its own scope. These
#: are STRICT ZERO — the release either repaired them or it did not.
S5_OWNED = (
    "python/srmech/cascade/hypercomplex_dft.py",
    "python/srmech/cascade/leaves.py",
    "python/srmech/signal_processing/_fft_carrier.py",
    "c/src/srmech_fft.c",
    "c/src/srmech_quaternion.c",
    "c/src/srmech_octonion.c",
    "c/src/srmech_eph_propagate_sparse.c",
    "c/src/srmech_heat_trace.c",
    "c/src/srmech_compose_run.c",
)

#: The RESIDUAL the scan lands on, per file, seeded at the rc477 measurement.
#: Down-only, and an EQUALITY so an unlowered entry is not invisible slack.
#:
#: ⚠️ **These are a CENSUS, not a repair, and the distinction is the point.**
#: The predicate is wider than rc477's twelve sites: it finds every function
#: that binds ``x = 1.0 / …`` and then multiplies by ``x``, which is also the
#: shape of a Jacobi rotation's ``t``, a JPEG normalisation and an so(8)
#: Gram-Schmidt. Most are OPERAND-CARRIED — the value divided is the caller's
#: float inside an iterative kernel — and P-C owns them at ``0.9.0rc482`` with
#: the seven ``S1_RESIDUAL`` rows they sit beside. Recording the number is what
#: makes the next release's drain measurable; narrowing the predicate until it
#: reported zero would have been the other option, and it is the wrong one.
S5_RESIDUAL_BY_FILE = {
    "python/srmech/math/laplacian.py": 19,
    "python/srmech/math/rational.py": 1,
    "python/srmech/physics/qm/potentials.py": 1,
    "python/srmech/physics/qm/so8.py": 3,
    "python/srmech/signal_processing/closed_form_ops/jpeg.py": 1,
    "python/srmech/signal_processing/closed_form_ops/multirate.py": 1,
    "c/src/srmech_jpeg.c": 1,
    "c/src/srmech_laplacian.c": 2,
    "c/src/srmech_svd_qr.c": 2,
    "c/src/srmech_trig.c": 1,
}

#: Down-only. 26 Python + 6 C at the rc477 measurement.
CEIL_S5_RESIDUAL: int = 32


def _s5_live():
    return _py_reciprocal_then_multiply() + _c_reciprocal_then_multiply()


def test_s5_is_strict_zero_in_every_file_rc477_owns():
    """THE RELEASE'S OWN CLAIM, and the only strict-zero half.

    ``1.0 / n`` is correctly rounded — 0 of the 4999 integers 2..5000 miss it
    — so the reciprocal was never the defect. The SECOND rounding was:
    ``x * (1.0/n)`` misses ``CR(x/n)`` on **5354 of 20000** seeded ``x``, and
    ``float(Q(x) * Q(1, n))`` misses **0 of 20000**. Divide, or form the term
    exactly and project once."""
    hits = [h for h in _s5_live() if h[0] in S5_OWNED]
    assert not hits, (
        "a rounded reciprocal is MULTIPLIED by inside a file rc477 owns: "
        + "; ".join(f"{f}:{ln}  {txt}" for f, ln, txt in hits)
    )


def test_s5_every_live_file_is_declared_and_the_census_never_rises():
    """The residual, per FILE so a line shift is not a false alarm.

    Keyed on the file rather than the line because these rows are not scheduled
    for THIS release and a per-line table would go stale on every unrelated
    edit — which is how a residual stops being read."""
    live = _s5_live()
    by_file = {}
    for f, _ln, _txt in live:
        if f in S5_OWNED:
            continue
        by_file[f] = by_file.get(f, 0) + 1
    unlisted = sorted(set(by_file) - set(S5_RESIDUAL_BY_FILE))
    assert not unlisted, (
        "a reciprocal-then-multiply appeared in an undeclared file: "
        + ", ".join(unlisted) + ". Repair it, or declare it with a count.")
    risen = {f: (n, S5_RESIDUAL_BY_FILE[f]) for f, n in by_file.items()
             if n > S5_RESIDUAL_BY_FILE[f]}
    assert not risen, f"the S5 census ROSE in {risen} — it is down-only"
    assert by_file == S5_RESIDUAL_BY_FILE, (
        f"the S5 census is {by_file} against a declared {S5_RESIDUAL_BY_FILE} "
        "— if a site was repaired, LOWER the count in the same commit")
    assert sum(by_file.values()) == CEIL_S5_RESIDUAL, (
        f"the census totals {sum(by_file.values())} against "
        f"CEIL_S5_RESIDUAL {CEIL_S5_RESIDUAL}")


#: The C half: a local bound to ``1.0 / <expr>`` and MULTIPLIED by within the
#: next :data:`_C_WINDOW` lines. A window rather than a parse, and the number is
#: part of the predicate: every site rc477 repaired had its multiply within 5
#: lines, and the window is set well above that so a repair cannot be faked by
#: moving the multiply down the function.
_C_WINDOW = 40
_C_RECIP = re.compile(r"\b(?:const\s+)?double\s+(\w+)\s*=\s*(?:\([^;]*\)\s*\?\s*)?"
                      r"\(?\s*1\.0\s*/")


def _c_reciprocal_then_multiply():
    out = []
    for path in _files(_C_DIRS, (".c", ".h")):
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        masked = _mask_c(raw).split("\n")
        orig = raw.split("\n")
        for i, line in enumerate(masked):
            m = _C_RECIP.search(line)
            if not m:
                continue
            name = m.group(1)
            use = re.compile(r"(\*\s*" + re.escape(name) + r"\b"
                             r"|\b" + re.escape(name) + r"\s*\*[^=]"
                             r"|\*=\s*" + re.escape(name) + r"\b)")
            for j in range(i + 1, min(i + 1 + _C_WINDOW, len(masked))):
                if use.search(masked[j]):
                    out.append((_rel(path), j + 1, orig[j].strip()))
                    break
    return sorted(set(out))




# ── non-vacuity: every shape must fire on a PLANT ─────────────────────────
@pytest.mark.parametrize("ext,body,scan", [
    (".py", "_S3 = 1.0 / float(_rsqrt(3.0))\n", "S3_AXIS"),
    (".py", '_MU_AXES = {"ijk": (0.0, _S3, _S3, _S3)}\n', "S3_AXIS"),
    (".py", "mu_q61 = [_to_q61(v) for v in mu]\n", "S3_Q61"),
    (".c", "static int cr_inv_sqrt(double x) { return 0; }\n", "S_CR_INV"),
])
def test_the_spelling_scans_fire_on_a_planted_site(tmp_path, ext, body, scan):
    """A shape no plant can trip is not a detector.

    Each snippet is a line rc477 DELETED, so a ratchet that could not see them
    come back would report a clean tree for ever."""
    f = tmp_path / ("planted" + ext)
    f.write_text(("x = 1\n" if ext == ".py" else "int x;\n") + body,
                 encoding="utf-8")
    pat = {"S3_AXIS": S3_AXIS, "S3_Q61": S3_Q61, "S_CR_INV": S_CR_INV}[scan]
    masker = _mask_py if ext == ".py" else _mask_c
    hits = _scan([str(tmp_path)], (ext,), pat, masker)
    assert hits, f"the {scan} scan did not fire on the planted {body!r}"


def test_the_python_dataflow_scan_fires_on_a_planted_function(tmp_path,
                                                              monkeypatch):
    """The S5 Python half, planted — it is a dataflow scan, not a regex, so it
    needs its own plant rather than riding the one above."""
    f = tmp_path / "planted_s5.py"
    f.write_text("def g(n, xs):\n"
                 "    inv = 1.0 / n\n"
                 "    return [x * inv for x in xs]\n", encoding="utf-8")
    monkeypatch.setitem(globals(), "_PY_SRC", str(tmp_path))
    hits = _py_reciprocal_then_multiply()
    assert hits and hits[0][1] == 3, (
        f"the dataflow scan did not see the planted reciprocal-then-multiply "
        f"(got {hits})")


def test_the_c_window_scan_fires_on_a_planted_block(tmp_path, monkeypatch):
    """The S5 C half, planted — the block shape, not a one-line change."""
    f = tmp_path / "planted_s5.c"
    f.write_text("void g(double *out, unsigned n) {\n"
                 "    double inv = 1.0 / (double)n;\n"
                 "    out[0] *= inv;\n"
                 "}\n", encoding="utf-8")
    monkeypatch.setitem(globals(), "_C_DIRS", [str(tmp_path)])
    hits = _c_reciprocal_then_multiply()
    assert hits and hits[0][1] == 3, (
        f"the C window scan did not see the planted block (got {hits})")


def test_the_scans_do_not_fire_on_the_CORRECT_spellings():
    """The negative controls, NAMED — a scan that fires on the repair is worse
    than one that fires on nothing.

    ``srmech_inv_sqrt`` is the one-rounding absorber; ``_HC_INV_Q61`` is the
    shipped exact Q61 anchor and its live use in ``hypercomplex_exp``'s pure
    arm; the seven operand-carried rows P-C owns stay in ``S1_RESIDUAL`` and
    must not be counted twice here."""
    from test_float_detour_class_rc476 import S1_RESIDUAL
    live = {(f, ln) for f, ln, _t in _s5_live()}
    for key in S1_RESIDUAL:
        if key in live:
            # The two ratchets MAY meet on one line — `c = 1.0 / _fsqrt(1+t*t)`
            # is S1's reciprocal AND contains `t * t` with `t` itself a
            # reciprocal — but only in a file S1 already declares, never in one
            # rc477 owns. A site in an OWNED file counted by both would mean the
            # release drained it twice or not at all.
            assert key[0] not in S5_OWNED, (
                f"{key} is in a file rc477 owns AND is declared in S1_RESIDUAL")
    src = os.path.join(_PY_SRC, "cascade", "hypercomplex_dft.py")
    text = open(src, "r", encoding="utf-8").read()
    assert "_HC_INV_Q61" in text, "the exact Q61 anchor was deleted"
    assert "_q61_fxmul(s, _HC_INV_Q61[k_axes])" in text, (
        "the anchor's LIVE use in hypercomplex_exp's pure Q61 arm is gone — "
        "it is the in-file precedent the rc477 axis formula absorbs")
    assert not _scan([_PY_SRC], (".py",), S3_AXIS, _mask_py)
