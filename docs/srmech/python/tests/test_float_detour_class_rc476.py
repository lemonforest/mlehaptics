"""0.9.0rc476 (`#T1188`) — the FLOAT-DETOUR class ratchet, and its deadlines.

THE CLASS. A root that leaves the exact carrier and is then divided, halved or
doubled rounds TWICE, and the second rounding is not repaired by fixing the
first. Measured across this rc: repairing ``rational.sqrt`` alone moved
``bell``'s ``1.0 / float(sqrt(2.0))`` from ``0x3ff6a09e667f3bcd`` — right, by
the two errors cancelling — to ``0x…bcc``, wrong. The repair is always the same
shape: put the reciprocal / halving / doubling INSIDE the exact radicand, so
there is one rounding, at the carrier boundary.

FOUR SHAPES, EACH WITH ITS OWN VERDICT, because they are not at the same stage:

* **S1** — ``1.0 / <a projected root>``. rc476 closed 7 Python + 7 C lines of
  it; what remains is owned by named LATER rcs and is tabulated below with a
  DEADLINE, not exempted.
* **S2** — ``float(sqrt(..., precision=...))``, an internal projection reading a
  CALLER-facing absolute grid. **Strict zero**, and reached: the one site
  (``bell.py:131``'s Tsirelson constant) is closed in this rc.
* **G8-P2** — PROSE that licenses a float oracle. Strict zero on the SOURCE
  side; a down-only ceiling on the test side, for the reason stated there.
* **G8-P1** — an AST scan for a libm ORACLE inside a test ``assert``. The
  scanner LANDS here and records its population; draining it is its own work.

⚠️ THE PREDICATE MASKS COMMENTS AND STRINGS, AND THAT IS NOT A DETAIL. The
predicate this gate inherited filtered out any line whose first non-space
character was ``#``, ``*``, ``/`` or a quote. Measured both ways at rc476:

* WITH that filter, ``srmech_compose_run.c:2405`` — ``*out = 1.0 / f;``, a real
  C statement whose line begins with the dereference ``*`` — was INVISIBLE, and
  it is a genuine member (``cr_inv_sqrt``, the C twin of the Python shape).
* WITHOUT it, six BLOCK-COMMENT continuation lines entered the C population,
  including three written by this very rc while explaining the defect, and two
  Python docstring lines did the same. A gate that counts its own prose is a
  gate whose number means nothing.

So neither heuristic is right, and the fix is not a third heuristic: the scan
MASKS real comments and string literals (``tokenize`` for Python, a character
walk for C) and then matches code. ``*out = 1.0 / f;`` survives and prose does
not. :func:`test_the_mask_keeps_code_and_drops_prose` pins both directions.
"""
from __future__ import annotations

import ast
import io
import os
import re
import tokenize

import pytest

import srmech

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRMECH = os.path.normpath(os.path.join(_HERE, "..", ".."))       # docs/srmech
_PY_SRC = os.path.join(_SRMECH, "python", "srmech")
_PY_TESTS = _HERE
_C_DIRS = [os.path.join(_SRMECH, "c", "src"), os.path.join(_SRMECH, "c", "include")]

#: Generated files are OUT: their content is a copy of a source this gate
#: already reads, so counting them would double every hit and make the ceiling
#: move for a regeneration rather than for a change.
_SKIP_BASENAMES = ("srmech_tool_registry.c",)
_SKIP_PREFIXES = ("_tool_docs",)

S1_PY = (r"[0-9]\.0\s*/\s*(float\(\s*(_rsqrt|_srn\.sqrt|rational\.sqrt|sqrt"
         r"|_R\.sqrt|R\.sqrt)\(|_fsqrt\()")
#: ⚠️ The ``r;|f;`` alternatives look loose and they STAY. Dropping them takes
#: the C population from 4 to 2 and the two lines lost are
#: ``compose_run.c:2405`` (a real member) and — at rc475 —
#: ``laplacian.c:1918``'s ``s[i] = 1.0 / r;``, which was one of this rc's OWN
#: edit sites. Anchoring to the root names would have blinded the gate to a row
#: it exists to find.
S1_C = r"[0-9]\.0\s*/\s*(lap_sqrt|sq_sqrt|srmech_rational_sqrt|s3\b|r;|f;)"
S2_PY = r"float\(\s*(_rsqrt|_srn\.sqrt|sqrt|R\.sqrt)\([^)]*precision\s*="
G8_P2 = (r"in TEST code is fine|discipline is SOURCE-only"
         r"|Round-off-faithful to numpy")


# ──────────────────────────────────────────────────────────────────────
# Masking — see the module docstring for why this is the load-bearing part.
# ──────────────────────────────────────────────────────────────────────
def _mask_py(text: str) -> str:
    """Blank every COMMENT and STRING token, preserving line and column."""
    rows = [list(line) for line in text.split("\n")]
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):  # pragma: no cover
        return text
    for tok in toks:
        if tok.type not in (tokenize.COMMENT, tokenize.STRING):
            continue
        (r1, c1), (r2, c2) = tok.start, tok.end
        for r in range(r1, min(r2 + 1, len(rows) + 1)):
            row = rows[r - 1]
            lo = c1 if r == r1 else 0
            hi = c2 if r == r2 else len(row)
            for c in range(lo, min(hi, len(row))):
                row[c] = " "
    return "\n".join("".join(r) for r in rows)


def _mask_c(text: str) -> str:
    """Blank block comments, line comments and string / char literals."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i)
            j = n if j < 0 else j
        elif ch in "\"'":
            q, j = ch, i + 1
            while j < n and text[j] != q:
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
        else:
            i += 1
            continue
        for k in range(i, j):
            if out[k] != "\n":
                out[k] = " "
        i = j
    return "".join(out)


def _files(roots, exts):
    for root in roots:
        for dirpath, _dirs, names in os.walk(root):
            for name in sorted(names):
                if not name.endswith(exts):
                    continue
                if name in _SKIP_BASENAMES or name.startswith(_SKIP_PREFIXES):
                    continue
                yield os.path.join(dirpath, name)


def _scan(roots, exts, pattern, masker):
    """``(relative path, 1-based line, stripped text)`` per masked-code hit."""
    rx = re.compile(pattern)
    hits = []
    for path in _files(roots, exts):
        raw = open(path, "r", encoding="utf-8", errors="replace").read()
        masked = _mask_py(raw) if masker is _mask_py else _mask_c(raw)
        original = raw.split("\n")
        for i, line in enumerate(masked.split("\n"), 1):
            if rx.search(line):
                rel = os.path.relpath(path, _SRMECH).replace(os.sep, "/")
                hits.append((rel, i, original[i - 1].strip()))
    return hits


def _s1_live():
    return (_scan([_PY_SRC], (".py",), S1_PY, _mask_py)
            + _scan(_C_DIRS, (".c", ".h"), S1_C, _mask_c))


# ──────────────────────────────────────────────────────────────────────
# The residual: a DEADLINE table, not an exemption list.
# ──────────────────────────────────────────────────────────────────────
#: ``(path, line) -> (owner_rc, recorded line text, why)``.
#:
#: Each row is a site this rc did NOT close, with the rc that owns it. A
#: "pinned exemption fixture" was the shape first proposed and it is the wrong
#: one: nothing in it would ever force it to empty, so it becomes permanent by
#: default and stops being read. The four assertions below make that
#: impossible — an unlisted hit fails, a stale entry fails, the count cannot
#: rise, and an entry whose owning rc has SHIPPED fails.
#:
#: ⚠️ The owner numbers are THIS rc's declaration, not an external commitment.
#: When one fires, the two honest answers are to do the work or to move the
#: deadline deliberately and say why in the same commit. Silence is the one
#: outcome the clause exists to prevent.
S1_RESIDUAL: "dict[tuple[str, int], tuple[str, str, str]]" = {
    # ── G1 axis constants: a NAMED axis is a label and has no carrier, so the
    #    reciprocal belongs inside the radicand. Owned by the G1/D2 group.
    ("python/srmech/cascade/hypercomplex_dft.py", 121): (
        "0.9.0rc480", "_S3 = 1.0 / float(_rsqrt(3.0))", "G1 axis CF-003"),
    ("python/srmech/cascade/hypercomplex_dft.py", 847): (
        "0.9.0rc480", "inv = 1.0 / float(_rsqrt(float(hi - 1)))", "G1 CF-004"),
    ("python/srmech/physics/qm/octonion.py", 140): (
        "0.9.0rc480", "_S3 = 1.0 / float(_rsqrt(3.0))", "G1 axis CF-007"),
    ("python/srmech/physics/qm/octonion.py", 141): (
        "0.9.0rc480", "_S7 = 1.0 / float(_rsqrt(7.0))", "G1 axis CF-008"),
    ("python/srmech/physics/qm/octonion.py", 791): (
        "0.9.0rc480", "inv = 1.0 / float(_rsqrt(float(norm_sq)))", "G1 CF-010"),
    ("python/srmech/physics/qm/quaternion.py", 132): (
        "0.9.0rc480", "_S3 = 1.0 / float(_rsqrt(3.0))", "G1 axis CF-006"),
    ("python/srmech/physics/qm/quaternion.py", 340): (
        "0.9.0rc480", "inv = 1.0 / float(_rsqrt(norm_sq))", "G1 CF-009"),
    ("c/src/srmech_compose_run.c", 2405): (
        "0.9.0rc480", "*out = 1.0 / f;",
        "G1 CF-011 cr_inv_sqrt, the C twin of the Python shape; D2 deletes it"),
    # ── OPERAND-CARRIED: the value divided is the CALLER's float, inside an
    #    iterative FPU kernel. SCHEDULED FOR REPAIR, not exempt — the
    #    operand-carried exemption was withdrawn, and P-C owns these.
    ("python/srmech/math/laplacian.py", 915): (
        "0.9.0rc482", "c = 1.0 / _fsqrt(1.0 + t * t)",
        "Jacobi rotation cosine; operand-carried, owned by P-C"),
    ("python/srmech/math/laplacian.py", 1057): (
        "0.9.0rc482", "c = 1.0 / _fsqrt(1.0 + t * t)",
        "Jacobi rotation cosine; operand-carried, owned by P-C"),
    ("python/srmech/math/laplacian.py", 2901): (
        "0.9.0rc482", "inv = 1.0 / _fsqrt(norm2)",
        "vector normalise; operand-carried, owned by P-C"),
    ("python/srmech/signal_processing/closed_form_ops/ica_jade.py", 253): (
        "0.9.0rc482",
        "inv_sqrt = [1.0 / float(_srn.sqrt(lam[c])) for c in range(k)]",
        "JADE whitening; operand-carried, owned by P-C"),
    ("c/src/srmech_laplacian.c", 1392): (
        "0.9.0rc482", "double c = 1.0 / lap_sqrt(1.0 + t * t);",
        "Jacobi rotation cosine, C twin; owned by P-C"),
    ("c/src/srmech_laplacian.c", 1561): (
        "0.9.0rc482", "double c = 1.0 / lap_sqrt(1.0 + t * t);",
        "Jacobi rotation cosine, C twin; owned by P-C"),
    ("c/src/srmech_svd_qr.c", 298): (
        "0.9.0rc482", "double c = 1.0 / sq_sqrt(1.0 + t * t);",
        "QR rotation cosine; owned by P-C"),
}

#: Down-only. It is an EQUALITY, not a ``<=``: a ceiling left above the live
#: count is invisible slack a new site could be added into with nothing firing.
CEIL_S1_RESIDUAL: int = 15

#: G8-P2, test side. Down-only rather than strict zero, and the reason is not
#: difficulty: the remaining row is a comment that correctly DESCRIBES a stdlib
#: reference used as an oracle in that test. Deleting the comment while the
#: oracle stays would forge the adjacency the gate is measuring. Draining it
#: means replacing the oracle, which is G8's own work.
CEIL_G8_P2_TESTS: int = 1

#: G8-P1: libm oracles inside a test ``assert``, by AST. The scanner LANDS at
#: this rc; the population it finds is recorded, not repaired. Down-only.
#:
#: 60 and not 57: a first pass of this scan matched only ``math.*`` and got 57.
#: ``cmath`` is the same C library through a complex door and belongs in the
#: same population, and adding it found three more rows. Recorded because the
#: number a scan returns is a property of the predicate, not of the tree.
CEIL_G8_P1: int = 60

_LIBM_ORACLE = frozenset({
    "sqrt", "hypot", "pow", "log", "exp", "sin", "cos", "tan",
    "atan", "atan2", "asin", "acos", "log2", "log10", "expm1", "log1p",
})


def _rc_number(version: str) -> int:
    m = re.search(r"rc(\d+)", version)
    return int(m.group(1)) if m else 10 ** 9      # a clean tag is past every rc


# ──────────────────────────────────────────────────────────────────────
# S1 — the four assertions.
# ──────────────────────────────────────────────────────────────────────
def test_s1_every_live_site_is_declared() -> None:
    """An UNLISTED hit fails. This is the half that catches a new float detour."""
    live = _s1_live()
    unlisted = [(f, ln, txt) for f, ln, txt in live if (f, ln) not in S1_RESIDUAL]
    assert not unlisted, (
        "a float-detour site is not declared in S1_RESIDUAL: "
        + "; ".join(f"{f}:{ln}  {txt}" for f, ln, txt in unlisted)
        + ". Either repair it (put the reciprocal inside the exact radicand) "
          "or add it with an OWNER rc and a reason — there is no third option, "
          "because an undeclared site is one nobody has decided about."
    )


def test_s1_every_declared_site_still_exists() -> None:
    """A STALE entry fails, so the table cannot outlive its sites.

    Line numbers move. An entry whose recorded text no longer sits at its
    recorded line is not evidence of anything, and a table of such entries is
    the "pinned exemption" failure mode wearing a different name.
    """
    live = {(f, ln): txt for f, ln, txt in _s1_live()}
    stale = []
    for (f, ln), (_owner, recorded, _why) in sorted(S1_RESIDUAL.items()):
        got = live.get((f, ln))
        if got is None:
            stale.append(f"{f}:{ln} is declared but the scan no longer finds it")
        elif got != recorded:
            stale.append(f"{f}:{ln} now reads {got!r}, recorded {recorded!r}")
    assert not stale, (
        "S1_RESIDUAL is out of date: " + "; ".join(stale)
        + ". If the site MOVED, update the line. If it was REPAIRED, delete "
          "the entry and lower CEIL_S1_RESIDUAL in the same commit."
    )


def test_s1_residual_never_rises() -> None:
    """Down-only, seeded at the rc476 measurement.

    Strict zero is arithmetically impossible here and saying so is the point:
    8 of the 15 rows are G1 constants another group owns and 7 are
    operand-carried sites P-C owns. A gate that demanded 0 today would have to
    be disabled today.

    ⚠️ 15 and not the 16 this rc was briefed with. The difference is the MASK,
    not a repair: the sixteenth row was ``qalg.py:743``, a DOCSTRING sentence
    quoting the shape. It is prose, it is real, and it is gated as prose by
    :func:`test_g8_p2_source_prose_is_strict_zero`'s family rather than counted
    as code here. Nothing was dropped; one row changed which gate owns it.
    """
    live = _s1_live()
    assert len(live) <= CEIL_S1_RESIDUAL, (
        f"S1 population is {len(live)}, over the down-only ceiling "
        f"{CEIL_S1_RESIDUAL}"
    )
    assert len(live) == CEIL_S1_RESIDUAL, (
        f"S1 population is {len(live)} but CEIL_S1_RESIDUAL is "
        f"{CEIL_S1_RESIDUAL} — if a site was repaired, LOWER the ceiling in "
        f"the same commit; it is down-only and an unlowered ceiling is slack"
    )
    assert len(S1_RESIDUAL) == CEIL_S1_RESIDUAL, (
        f"the table holds {len(S1_RESIDUAL)} rows against a ceiling of "
        f"{CEIL_S1_RESIDUAL}"
    )


def test_s1_no_entry_has_outlived_its_owning_rc() -> None:
    """THE DEADLINE. This is what makes "a later rc" enforceable.

    Every entry names the rc that owns its repair. Once that rc has shipped,
    a surviving entry is no longer scheduled work — it is an exemption that
    nobody chose — and this fails until someone chooses.
    """
    here = _rc_number(srmech.__version__)
    overdue = [
        f"{f}:{ln} owned by {owner} ({why})"
        for (f, ln), (owner, _txt, why) in sorted(S1_RESIDUAL.items())
        if _rc_number(owner) <= here
    ]
    assert not overdue, (
        f"srmech is at {srmech.__version__} and these entries' owning rc has "
        "already shipped: " + "; ".join(overdue)
        + ". Repair the site, or move the deadline DELIBERATELY and say why "
          "in the same commit. Letting it pass silently is the one outcome "
          "this clause exists to prevent."
    )


# ──────────────────────────────────────────────────────────────────────
# S2 — strict zero, and reached.
# ──────────────────────────────────────────────────────────────────────
def test_s2_no_internal_projection_reads_a_precision_root() -> None:
    """``precision=`` is the literal ABSOLUTE floored grid a CALLER asks for.

    An INTERNAL constant read off it makes that constant depend on a
    caller-facing knob, and the one site that did — ``bell.py``'s Tsirelson
    bound at ``precision=64`` — justified itself by calling the default route
    "the fast, ~1-ULP path". The ~1 ULP was the defect. Both are closed, so
    this clause is strict zero and measured to be.
    """
    hits = _scan([_PY_SRC], (".py",), S2_PY, _mask_py)
    assert not hits, (
        "an internal projection reads a precision= root at: "
        + "; ".join(f"{f}:{ln}  {t}" for f, ln, t in hits)
    )


# ──────────────────────────────────────────────────────────────────────
# G8 — float ORACLES, in prose and in code.
# ──────────────────────────────────────────────────────────────────────
def test_g8_p2_source_prose_is_strict_zero() -> None:
    """No SHIPPED docstring may state its contract against numpy or libm.

    The two rows this closes were ``elementwise_hypot`` / ``elementwise_sqrt``
    promising to be "round-off-faithful to numpy" — in a package that has no
    numpy, describing an op a bare-C host is supposed to be able to check for
    itself. They now state the value: correctly rounded.
    """
    hits = _scan([_PY_SRC], (".py",), G8_P2, lambda t: t)
    assert not hits, (
        "shipped prose states a contract against a float oracle at: "
        + "; ".join(f"{f}:{ln}  {t}" for f, ln, t in hits)
    )


def test_g8_p2_test_prose_ceiling() -> None:
    """The test side, down-only. See :data:`CEIL_G8_P2_TESTS` for why not zero."""
    hits = _scan([_PY_TESTS], (".py",), G8_P2, lambda t: t)
    assert len(hits) <= CEIL_G8_P2_TESTS, (
        f"G8-P2 test-side population is {len(hits)}, over {CEIL_G8_P2_TESTS}: "
        + "; ".join(f"{f}:{ln}" for f, ln, _t in hits)
    )
    assert len(hits) == CEIL_G8_P2_TESTS, (
        f"live {len(hits)} against a ceiling of {CEIL_G8_P2_TESTS} — lower it"
    )


def _g8_p1_rows():
    """Every libm call inside a test ``assert``: the oracle population.

    AST rather than text, because ``math.sqrt`` in a fixture and ``math.sqrt``
    in an assertion are different things and only the second is an oracle.
    """
    rows = []
    for path in _files([_PY_TESTS], (".py",)):
        try:
            tree = ast.parse(open(path, "r", encoding="utf-8",
                                  errors="replace").read())
        except SyntaxError:                                # pragma: no cover
            continue
        aliases = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "math":
                for a in node.names:
                    aliases[a.asname or a.name] = a.name
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assert):
                continue
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Call):
                    continue
                fn = sub.func
                if (isinstance(fn, ast.Attribute)
                        and isinstance(fn.value, ast.Name)
                        and fn.value.id in ("math", "cmath")
                        and fn.attr in _LIBM_ORACLE):
                    rows.append((os.path.basename(path), node.lineno,
                                 f"{fn.value.id}.{fn.attr}"))
                elif (isinstance(fn, ast.Name)
                        and aliases.get(fn.id) in _LIBM_ORACLE):
                    rows.append((os.path.basename(path), node.lineno,
                                 f"math.{aliases[fn.id]}"))
    return rows


def test_g8_p1_scanner_is_not_vacuous() -> None:
    """The scanner must FIND the population it is about to pin.

    A count of 0 from a broken AST walk and a count of 0 from a clean tree read
    the same in the ceiling below, which is the state Rule 7 and Rule 2 of the
    JPL audit both spent their lives in.
    """
    rows = _g8_p1_rows()
    assert rows, "the G8-P1 AST scan found NOTHING — it is not looking"
    names = {r[2] for r in rows}
    assert "math.sqrt" in names, f"no math.sqrt oracle found; saw {sorted(names)}"


def test_g8_p1_libm_oracle_in_assert_ceiling() -> None:
    """Down-only, seeded at rc476's measurement.

    This rc LANDS the scanner; it does not drain it. Every row is a test that
    proves a srmech cascade by comparing it to libm — which is the thing the
    cascade exists to replace, and which cannot see a 1-ulp misround when it is
    read through a tolerance. That is not hypothetical: the sqrt defect this
    release repairs sat under exactly such a comparison for its whole life.
    """
    rows = _g8_p1_rows()
    assert len(rows) <= CEIL_G8_P1, (
        f"G8-P1 population is {len(rows)}, over the down-only ceiling "
        f"{CEIL_G8_P1}. New rows: "
        + "; ".join(f"{f}:{ln} {n}" for f, ln, n in sorted(rows)[:10])
    )
    assert len(rows) == CEIL_G8_P1, (
        f"live G8-P1 population is {len(rows)} but CEIL_G8_P1 is {CEIL_G8_P1} "
        f"— if an oracle was replaced, LOWER the ceiling; it is down-only"
    )


# ──────────────────────────────────────────────────────────────────────
# Non-vacuity: the scan must be able to FIND a planted site, and must not
# find prose.
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "lang,snippet",
    [
        ("py", "    inv = 1.0 / float(_rsqrt(3.0))\n"),
        ("py", "    s = 1.0 / _fsqrt(deg[i])\n"),
        ("c", "    *out = 1.0 / f;\n"),
        ("c", "    double r = lap_sqrt(d); s[i] = 1.0 / r;\n"),
        ("c", "    out[0] = 1.0 / s3;\n"),
    ],
)
def test_the_scan_fires_on_a_planted_site(tmp_path, lang, snippet) -> None:
    """Every shape this rc REPAIRED must still be detectable if it comes back.

    Each snippet below is a line rc476 deleted. A ratchet that could not see
    them re-appear would report a clean tree forever.
    """
    ext = ".py" if lang == "py" else ".c"
    f = tmp_path / ("planted" + ext)
    f.write_text("x = 1\n" + snippet if lang == "py" else "int x;\n" + snippet,
                 encoding="utf-8")
    pat = S1_PY if lang == "py" else S1_C
    masker = _mask_py if lang == "py" else _mask_c
    hits = _scan([str(tmp_path)], (ext,), pat, masker)
    assert hits, f"the scan did not fire on the planted {lang} site {snippet!r}"


@pytest.mark.parametrize(
    "lang,body",
    [
        ("py", 'def f():\n    """text: 1.0 / float(_rsqrt(3.0)) in prose."""\n'),
        ("py", "# comment: 1.0 / _fsqrt(d) in prose\nx = 1\n"),
        ("c", "/* comment: 1.0 / lap_sqrt(d) in prose */\nint x;\n"),
        ("c", "/*\n * 1.0 / s3 on a continuation line\n */\nint x;\n"),
    ],
)
def test_the_mask_keeps_code_and_drops_prose(tmp_path, lang, body) -> None:
    """The other direction, and the one the inherited filter got wrong.

    A leading-``*`` filter drops ``*out = 1.0 / f;`` (code) and keeps nothing
    useful; no filter at all keeps block-comment continuations (prose). Only a
    real mask does both, and both directions are pinned so a future
    "simplification" back to a leading-character rule fails here.
    """
    ext = ".py" if lang == "py" else ".c"
    f = tmp_path / ("prose" + ext)
    f.write_text(body, encoding="utf-8")
    pat = S1_PY if lang == "py" else S1_C
    masker = _mask_py if lang == "py" else _mask_c
    hits = _scan([str(tmp_path)], (ext,), pat, masker)
    assert not hits, f"the scan counted PROSE as a site: {hits}"


def test_the_c_scan_sees_the_dereference_statement() -> None:
    """``compose_run.c:2405`` is the anti-vacuity member, named explicitly.

    It is the row the inherited leading-``*`` filter silently dropped, and the
    row anchoring the pattern to the root names would also drop. Naming it here
    means either mistake fails a test instead of shrinking a number.
    """
    live = {(f, ln) for f, ln, _t in _s1_live()}
    assert ("c/src/srmech_compose_run.c", 2405) in live, (
        "the C scan no longer sees compose_run.c:2405 (`*out = 1.0 / f;`) — "
        "either the line moved (update S1_RESIDUAL) or the predicate was "
        "narrowed in a way that blinds it to a real member"
    )
