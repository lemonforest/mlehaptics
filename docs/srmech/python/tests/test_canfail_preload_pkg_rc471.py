"""rc471 (`#T1188`) — the can-fail harness reaches PACKAGE modules, and refuses
LOUDLY in the two states where it would otherwise green every gate in the arc.

WHY THIS FILE EXISTS
--------------------
The rest of the "ALU All The Way" arc mutates ``srmech/math/rational.py`` and
its siblings to prove its gates can fail. Through rc470 ``canfail_preload``
refused package modules **on the record**, and the refusal named the correct
process: *"A gate that needs a mutant of a package module should say so in a
review rather than acquire it by widening this."* rc471 is that review, and it
overturns the refusal with a DIFFERENT MECHANISM — a ``sys.meta_path`` finder,
which the refusal never ruled on, because no amount of ``sys.path`` reaches a
dotted name at all.

THE LOAD-BEARING TEST IS THE NEGATIVE CONTROL
---------------------------------------------
:func:`test_negative_control_pythonpath_alone_cannot_deliver_the_mutant`. If the
same mutant delivered by ``PYTHONPATH`` alone went RED, then ``PYTHONPATH`` was
sufficient and the finder is not the causal mechanism — and the whole widening
would be a coincidence dressed as a proof. A false-green mutation test happened
in this arc's research phase for exactly that class of reason.

AND THE SECOND ONE IS THE SILENT FALSE GREEN
---------------------------------------------
A research report's own "proof" command named ``-p canfail_pkg_proto``, a file
that is a LIBRARY with no pytest hook. pytest loaded it, ran nothing of it, and
printed **33 passed** — indistinguishable from a real pass. A builder porting
only the file that report named would have shipped a can-fail harness that
mutates nothing and reports green on every gate in the arc. So:
:func:`test_a_run_that_mutated_nothing_is_refused_out_loud` asserts on the
**stderr banner and the exit status**, never on the tally — the tally is
exactly what a silent false green gets right.

numpy-free. No ``abs()``. Every digest routes through
``srmech.amsc.format.sha256_bytes``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_PY_ROOT = _HERE.parents[0]
_TOOLS = _PY_ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import canfail_preload as cf  # noqa: E402  (tools/ is on sys.path just above)

#: The arc's real target, and the one whose mutation the rest of rc-C..rc-H
#: needs. Its Euclidean fallback is one line and its expansion is pinned by
#: ``tests/test_rational_parity.py``, so a wrong term is loudly wrong.
TARGET = "srmech.math.rational"
MUTATION = ("result.append(p // q)", "result.append(p // q + 1)  # MUTANT")


def _mutant_dir(tmp_path: Path, module: str = TARGET,
                mutation=MUTATION) -> Path:
    cf.write_mutant(module, [mutation], tmp_path)
    return tmp_path


def _run(args, env_extra=None, cwd=None):
    env = {k: v for k, v in __import__("os").environ.items()}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(env_extra or {})
    return subprocess.run([sys.executable, *args], capture_output=True,
                          text=True, cwd=str(cwd or _PY_ROOT), env=env)


# ── 1. the widening itself ───────────────────────────────────────────────────

def test_source_of_resolves_a_dotted_package_module() -> None:
    assert cf.source_of(TARGET) == _PY_ROOT / "srmech" / "math" / "rational.py"
    assert cf.source_of("demotion_probe") == _TOOLS / "demotion_probe.py"


def test_source_of_refuses_a_name_with_no_shipped_source() -> None:
    """A REAL raise, not a bare ``assert`` — and the type says which fault.

    ⚠️ Both of these were ``pytest.raises(AssertionError)`` when rc471 first
    shipped, and `tests/test_assert_contract_gate_rc433.py` went RED on them at
    five sites across this file. That gate was RIGHT, and its message says the
    repair: *"THE FIX IS NEVER TO DELETE THE TEST. Promote the ``assert`` to a
    real ``raise`` of the type tree precedent already uses for that input
    class, then update the test to expect it."* ``canfail_preload``'s own
    module docstring had been citing that discipline since rc471 while its
    input contract rested on four bare asserts, so ``python -O`` deleted every
    guard this file certifies. Adding the five lines to the gate's EXEMPTIONS
    would have been widening a ceiling to green a red gate.
    """
    with pytest.raises(FileNotFoundError):
        cf.source_of("srmech.math.no_such_module_rc471")
    with pytest.raises(FileNotFoundError):
        cf.source_of("no_such_tool_rc471")


def test_the_promoted_guards_survive_python_dash_O() -> None:
    """THE CAN-FAIL FOR THE PROMOTION ITSELF, and it is the whole point.

    ``python -O`` strips every ``assert`` statement. Under the old spelling
    this subprocess would have completed with no exception at all and
    ``write_mutant`` would have written a no-op "mutant" into the package tree.
    Run with ``-O``, each promoted guard must still raise.
    """
    probe = (
        "import sys; sys.path.insert(0, %r)\n"
        "import canfail_preload as cf\n"
        "seen = []\n"
        "for fn, exc in ((lambda: cf.source_of('srmech.math.nope_rc471'),"
        " FileNotFoundError),\n"
        "                (lambda: cf.write_mutant(%r, [('x','y')], %r),"
        " ValueError)):\n"
        "    try:\n"
        "        fn()\n"
        "    except exc as e:\n"
        "        seen.append(type(e).__name__)\n"
        "    except BaseException as e:\n"
        "        seen.append('WRONG:' + type(e).__name__)\n"
        "    else:\n"
        "        seen.append('NO RAISE')\n"
        "print('SEEN' + repr(seen))\n"
    ) % (str(_TOOLS), TARGET, str(_PY_ROOT))
    out = _run(["-O", "-c", probe])
    assert out.returncode == 0, out.stderr
    line = [x for x in out.stdout.splitlines() if x.startswith("SEEN")][-1]
    assert eval(line[4:]) == ["FileNotFoundError", "ValueError"], (
        "a guard vanished under `python -O`: " + line)


def test_the_refusal_it_overturned_is_gone_from_the_file() -> None:
    """rc471 REVERSED a shipped refusal; it must not still argue against itself.

    The old text is quoted in the module docstring as history — that is the
    record the reversal owes. What must not survive is the refusal standing as
    the CONTRACT of :func:`source_of`.
    """
    doc = cf.source_of.__doc__ or ""
    assert "Deliberately narrow" not in doc, (
        "source_of() still documents the refusal rc471 overturned")
    assert "rc471" in doc, "source_of() does not name the review that widened it"
    module_doc = cf.__doc__ or ""
    assert "Deliberately narrow" in module_doc, (
        "the overturned refusal must be quoted in the module docstring; a "
        "reversal that deletes the text it reversed leaves a later reader "
        "unable to tell a reversal from a forgotten narrowing")


def test_the_mutant_keeps_the_dots_in_its_filename(tmp_path) -> None:
    """W2.5 — a free SECOND safety property, and it is measurable.

    A directory holding only ``srmech.math.rational.py`` exposes nothing
    importable: the dotted name resolves through the parent package's
    ``__path__``, and the bare name does not exist. Strip the dots and the same
    bytes become a live bare-name collision target on any ``sys.path``.
    """
    dst = cf.write_mutant(TARGET, [MUTATION], tmp_path)
    assert dst.name == "srmech.math.rational.py"
    out = _run(["-c", "import importlib, sys;"
                      "print(getattr(importlib.import_module('srmech.math.rational'),"
                      "'__file__'))"],
               {"PYTHONPATH": str(tmp_path)})
    assert out.returncode == 0, out.stderr
    assert str(cf.source_of(TARGET)) in out.stdout, (
        "PYTHONPATH delivered the mutant for a DOTTED name — it must not")
    bare = _run(["-c", "import rational"], {"PYTHONPATH": str(tmp_path)})
    assert bare.returncode != 0 and "No module named 'rational'" in bare.stderr


# ── 2. install() refuses LOUDLY, in each state, with its own can-fail ────────

def test_install_refuses_an_empty_target_map() -> None:
    with pytest.raises(RuntimeError) as excinfo:
        cf.install({})
    assert "NO targets" in str(excinfo.value)


def test_parse_env_takes_one_name_or_a_comma_separated_list(tmp_path) -> None:
    """W2.7 — the multi-target ENV interface, which the prototype never ran.

    The rc470 prototype called ``install()`` with a dict and DOCUMENTED a
    comma-separated ``CANFAIL_MODULE`` it never implemented or exercised.
    """
    one = cf.parse_env(str(tmp_path), TARGET)
    assert one == {TARGET: tmp_path / (TARGET + ".py")}
    two = cf.parse_env(str(tmp_path), f" {TARGET} ,srmech.math.q ")
    assert sorted(two) == ["srmech.math.q", TARGET]
    with pytest.raises(RuntimeError):
        cf.parse_env(str(tmp_path), "  ,  ")


def test_install_refuses_a_target_already_in_sys_modules(tmp_path) -> None:
    """REFUSAL (a) — and this process is itself the proof it is needed.

    A bare ``import srmech`` pulls ``srmech.math.rational`` in with it
    (MEASURED: ``'srmech.math.rational' in sys.modules`` is True after
    ``import srmech``). So by the time any test module runs, the finder could
    never be consulted — every import would bind the SHIPPED module and the
    gate would pass for the wrong reason, with no trace at all. That is why the
    plugin is loaded with ``-p canfail_preload`` on the COMMAND LINE, before
    anything imports the target.
    """
    import srmech  # noqa: F401  (the import IS the fixture)
    assert TARGET in sys.modules, (
        "this test's premise no longer holds: importing srmech no longer "
        "imports the target, so the refusal below is being proven vacuously")
    with pytest.raises(RuntimeError) as excinfo:
        cf.install({TARGET: _mutant_dir(tmp_path) / (TARGET + ".py")})
    assert "already in sys.modules" in str(excinfo.value)
    assert TARGET in str(excinfo.value)
    assert cf.INSTALLED is None or TARGET not in cf.INSTALLED.targets


def test_install_refuses_a_target_whose_source_does_not_exist(tmp_path) -> None:
    """A typo in ``CANFAIL_MODULE`` must not install a finder that never fires."""
    with pytest.raises(FileNotFoundError) as excinfo:
        cf.install({"srmech.math.no_such_module_rc471": tmp_path / "x.py"})
    assert "no shipped source at" in str(excinfo.value)


def test_install_refuses_a_target_with_no_mutant_written(tmp_path) -> None:
    """A mutant path that is not there greens the gate silently otherwise."""
    victim = "gen_tool_docs"
    if victim in sys.modules:            # another test module got there first
        pytest.skip(f"{victim} already imported in this process")
    with pytest.raises(RuntimeError) as excinfo:
        cf.install({victim: tmp_path / (victim + ".py")})
    assert "no mutant for" in str(excinfo.value)
    assert cf.INSTALLED is None or victim not in cf.INSTALLED.targets


# ── 3. THE THREE ARMS ────────────────────────────────────────────────────────

#: ⚠️ THE BEHAVIOURAL PROBE IS ROUTE-DEPENDENT, and rc471 first shipped it as
#: if it were not. The mutated line — ``result.append(p // q)`` — lives in
#: ``continued_fraction``'s **pure-Python fallback**
#: (``srmech/math/rational.py``, under ``# Pure-Python fallback: Euclidean
#: expansion``), and the function RETURNS before reaching it whenever
#: ``_native.HAS_NATIVE and _native.LIB is not None``. So a bare
#: ``continued_fraction(22, 7) != [3, 7]`` assertion cannot fire on any host
#: that builds ``libsrmech`` — which is four of CI's jobs, where it failed with
#: *"the mutant is behaving like the shipped file"*. The mutant WAS loaded; the
#: probe was asking the wrong route.
#:
#: The repair measures BOTH routes and says which is which. Forcing the
#: fallback by toggling ``_native.HAS_NATIVE`` is not invented here: it is the
#: shipped spelling of ``tests/test_rational_parity.py``'s own native/fallback
#: parity sweep, which is also why the RED arm below survives on a native host
#: — that sweep compares the two routes, so a mutated fallback makes it
#: disagree with the native one and go red.
_INSPECT = """
import json
import canfail_preload as cf
from srmech.math import rational, q

_saved = rational._native.HAS_NATIVE
try:
    rational._native.HAS_NATIVE = False
    _cf22_fallback = rational.continued_fraction(22, 7)
finally:
    rational._native.HAS_NATIVE = _saved

print("JSON" + json.dumps({
    "rational": rational.__file__,
    "package": rational.__package__,
    "q_rational": q._rational.__file__,
    "cyclic": rational._cyclic.__file__,
    "native": rational._native.__file__,
    "has_native": bool(_saved and rational._native.LIB is not None),
    "cf22": rational.continued_fraction(22, 7),
    "cf22_fallback": _cf22_fallback,
    "mutated": sorted(cf.mutated()),
}))
"""


def _inspect(tmp_path, extra_prelude="", env_extra=None):
    out = _run(["-c", extra_prelude + _INSPECT], env_extra)
    assert out.returncode == 0, out.stderr
    line = [x for x in out.stdout.splitlines() if x.startswith("JSON")][-1]
    return json.loads(line[4:])


def test_arm_i_the_finder_delivers_a_package_mutant_with_real_siblings(tmp_path) -> None:
    """ARM (i): the mutant loads as ``srmech.math.rational``, nothing else moves.

    Its ``__package__`` is the REAL parent, so its own ``from .. import
    _native`` / ``from . import cyclic`` bind the shipped objects; the parent's
    attribute is rebound; and the sibling ``srmech.math.q`` picks the mutant up
    as its ``_rational``. Those five assertions are route-independent — they
    are about which FILE loaded — and they were never the problem.

    The behavioural assertion was. See the note on :data:`_INSPECT`: the
    mutation lives in the pure-Python fallback, so on a native host the shipped
    dispatch returns before reaching it and ``continued_fraction(22, 7)``
    answers ``[3, 7]`` from a mutant that IS loaded. The check now names the
    route it measured, and pins the native route as UNAFFECTED rather than
    skipping it — *an instrument that cannot return otherwise is not a
    measurement*, and "the mutation changed nothing on this route" is a real
    answer here, not a missing one.
    """
    got = _inspect(tmp_path, env_extra={
        "PYTHONPATH": str(_TOOLS),
        cf.ENV_DIR: str(_mutant_dir(tmp_path)),
        cf.ENV_MODULE: TARGET})
    mutant = str(tmp_path / (TARGET + ".py"))
    assert got["rational"] == mutant
    assert got["q_rational"] == mutant, "the sibling cross-import missed it"
    assert got["package"] == "srmech.math"
    assert got["cyclic"] == str(_PY_ROOT / "srmech" / "math" / "cyclic.py")
    assert got["native"] == str(_PY_ROOT / "srmech" / "_native" / "__init__.py")
    assert got["cf22_fallback"] != [3, 7], (
        "the MUTATED ROUTE is behaving like the shipped file: the mutant is "
        "loaded (asserted above) but its pure-Python Euclidean expansion "
        "returned the shipped expansion of 22/7, so the mutation did not take")
    if got["has_native"]:
        assert got["cf22"] == [3, 7], (
            "the native route answered a MUTATED value. The mutation is a "
            "one-line edit to the pure-Python fallback and cannot reach "
            "libsrmech, so either the mutation moved or the dispatch did")
    else:
        assert got["cf22"] == got["cf22_fallback"], (
            "HAS_NATIVE is False, so the live call and the forced fallback "
            "must be the SAME route and cannot differ")
    assert got["mutated"] == [TARGET]


def test_the_mutation_target_lives_below_the_native_dispatch_return() -> None:
    """WHY arm (i) has to name its route — proven from the SOURCE, not the host.

    This host may or may not have ``libsrmech``. The claim "the native route
    cannot see this mutation" must not depend on which one it is, so it is
    decided structurally: inside ``continued_fraction``, the
    ``if _native.HAS_NATIVE and _native.LIB is not None:`` block ENDS in a
    ``return``, and the mutation target sits strictly below it. A caller with
    native present therefore never executes the mutated line — which is exactly
    what four CI jobs reported as *"the mutant is behaving like the shipped
    file"* before this rc named the route.

    If someone later moves the mutation above the dispatch, or gives the native
    branch a fall-through, this goes red and arm (i)'s asymmetric assertion
    needs re-deciding. That is the correct behaviour.
    """
    import ast

    src_path = _PY_ROOT / "srmech" / "math" / "rational.py"
    src = src_path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef)
               and n.name == "continued_fraction"), None)
    assert fn is not None, f"continued_fraction is gone from {src_path}"

    branches = [n for n in ast.walk(fn)
                if isinstance(n, ast.If) and "HAS_NATIVE" in ast.unparse(n.test)]
    assert len(branches) == 1, (
        f"expected exactly one HAS_NATIVE branch in continued_fraction, "
        f"found {len(branches)}")
    branch = branches[0]
    assert any(isinstance(n, ast.Return) for n in branch.body), (
        "the native branch does not return, so it FALLS THROUGH into the "
        "pure-Python expansion and arm (i)'s route split is wrong")

    lines = src.split("\n")
    hits = [i + 1 for i, s in enumerate(lines) if MUTATION[0] in s]
    assert len(hits) == 1, (
        f"the mutation target occurs {len(hits)} times; write_mutant refuses "
        f"anything but 1, so this file and that refusal disagree")
    assert hits[0] > branch.end_lineno, (
        f"the mutation target is at line {hits[0]}, which is NOT below the "
        f"native dispatch branch (ends {branch.end_lineno}) — the native "
        f"route would execute it and arm (i) must be re-decided")
    assert fn.lineno < hits[0] <= fn.end_lineno, (
        "the mutation target is not inside continued_fraction at all")


def test_arm_ii_a_hostile_sys_path_insert_cannot_outrank_the_finder(tmp_path) -> None:
    """ARM (ii): ``PathFinder`` is LAST in ``sys.meta_path``.

    So a gate doing an unconditional module-level ``sys.path.insert(0, ...)``
    — including one pointing straight at ``srmech/math/`` — cannot take the
    import back. A ``sys.path`` shim loses this case; a meta-path finder does
    not, and that is why the widening is a different mechanism rather than a
    relaxation of the old one.
    """
    hostile = ("import sys, canfail_preload as _cf\n"
               "sys.path.insert(0, str(_cf.PACKAGE_ROOT))\n"
               "sys.path.insert(0, str(_cf.PACKAGE_ROOT / 'srmech' / 'math'))\n")
    got = _inspect(tmp_path, hostile, env_extra={
        "PYTHONPATH": str(_TOOLS),
        cf.ENV_DIR: str(_mutant_dir(tmp_path)),
        cf.ENV_MODULE: TARGET})
    assert got["rational"] == str(tmp_path / (TARGET + ".py"))


def test_negative_control_pythonpath_alone_cannot_deliver_the_mutant(tmp_path) -> None:
    """ARM (iii), THE LOAD-BEARING ONE.

    The same mutant, in the same directory, with NO plugin — only
    ``PYTHONPATH``. It must stay GREEN. If it went red, ``PYTHONPATH`` was
    sufficient, the finder is not the causal mechanism, and arm (i)'s red
    proves nothing.
    """
    _mutant_dir(tmp_path)
    out = _run(["-m", "pytest", "tests/test_rational_parity.py", "-q",
                "-p", "no:cacheprovider"], {"PYTHONPATH": str(tmp_path)})
    assert out.returncode == 0, (
        "the NEGATIVE CONTROL went RED: PYTHONPATH alone delivered the mutant, "
        "so the meta-path finder is not the causal mechanism and arm (i) is a "
        "coincidence.\n" + out.stdout[-3000:])
    assert " failed" not in out.stdout


def test_arm_i_red_and_arm_iii_green_differ_only_by_the_plugin(tmp_path) -> None:
    """The two arms side by side, on the SAME gate and the SAME mutant.

    One variable separates them: ``-p canfail_preload``. Asserting the pair
    rather than each alone is what makes the finder the named cause.
    """
    _mutant_dir(tmp_path)
    green = _run(["-m", "pytest", "tests/test_rational_parity.py", "-q",
                  "-p", "no:cacheprovider"], {"PYTHONPATH": str(tmp_path)})
    red = _run(["-m", "pytest", "tests/test_rational_parity.py", "-q",
                "-p", "no:cacheprovider", "-p", "canfail_preload"],
               {"PYTHONPATH": str(_TOOLS),
                cf.ENV_DIR: str(tmp_path), cf.ENV_MODULE: TARGET})
    assert green.returncode == 0, green.stdout[-2000:]
    assert red.returncode != 0, (
        "the mutant run stayed GREEN — the gate does not measure what the "
        "mutation broke, or the mutant was never loaded.\n" + red.stdout[-2000:])
    assert "MUTANT figure" in red.stderr


# ── 4. REFUSAL (b): the run that mutated nothing ─────────────────────────────

def test_a_run_that_mutated_nothing_is_refused_out_loud(tmp_path) -> None:
    """REFUSAL (b) — assert on the BANNER and the EXIT, never on the tally.

    A harness that mutates nothing prints a tally a real pass would print. That
    is the whole defect: a research report's own command named a library with
    no pytest hook and got "33 passed". Here the target is a ``tools/`` module
    the gate never imports, so nothing is mutated — and the run must still
    refuse.
    """
    cf.write_mutant("frame_probe",
                    [("from __future__ import annotations",
                      "from __future__ import annotations  # MUTANT")],
                    tmp_path)
    gate = tmp_path / "test_trivially_green_rc471.py"
    gate.write_text("def test_green():\n    assert True\n", encoding="utf-8")
    out = _run(["-m", "pytest", str(gate), "-q", "-p", "no:cacheprovider",
                "-p", "canfail_preload"],
               {"PYTHONPATH": str(_TOOLS),
                cf.ENV_DIR: str(tmp_path), cf.ENV_MODULE: "frame_probe"})
    assert "1 passed" in out.stdout, (
        "the premise of this test is that the TALLY looks like a pass; if it "
        "does not, the refusal is being proven against the wrong thing")
    assert "REFUSING THIS RUN" in out.stderr, out.stderr[-2000:]
    assert "frame_probe" in out.stderr
    assert out.returncode == 4, (
        f"exit {out.returncode}; a run that mutated nothing must exit "
        f"USAGE_ERROR(4), not report its tally as a result")


def test_the_refusal_does_not_fire_when_something_WAS_mutated(tmp_path) -> None:
    """The can-fail of REFUSAL (b): it must be silent on a real mutant run."""
    _mutant_dir(tmp_path)
    out = _run(["-m", "pytest", "tests/test_rational_parity.py", "-q",
                "-p", "no:cacheprovider", "-p", "canfail_preload"],
               {"PYTHONPATH": str(_TOOLS),
                cf.ENV_DIR: str(tmp_path), cf.ENV_MODULE: TARGET})
    assert "REFUSING THIS RUN" not in out.stderr
    assert out.returncode == 1, (
        f"exit {out.returncode}; a real mutant run must exit with pytest's own "
        f"TESTS_FAILED(1), distinguishable from the harness's USAGE_ERROR(4)")


# ── 5. the out-of-tree write refusal is UNTOUCHED (W2.4) ─────────────────────

@pytest.mark.parametrize("inside", ["", "tests", "srmech/math", "tools/x"])
def test_the_out_of_tree_refusal_keys_on_out_dir_not_on_the_module_name(
        inside) -> None:
    """W2.4 — it refuses a dotted target and a bare one IDENTICALLY.

    The refusal keys on ``out_dir``; widening ``source_of`` did not touch it,
    and this pins that it did not.
    """
    target = _PY_ROOT / inside if inside else _PY_ROOT
    for module in (TARGET, "demotion_probe"):
        with pytest.raises(ValueError) as excinfo:
            cf.write_mutant(module, [MUTATION], target)
        assert "inside the package tree" in str(excinfo.value)


def test_a_zero_match_replacement_is_a_stale_control(tmp_path) -> None:
    with pytest.raises(ValueError) as excinfo:
        cf.write_mutant(TARGET, [("no such text rc471", "x")], tmp_path)
    assert "occurs 0 times" in str(excinfo.value)
