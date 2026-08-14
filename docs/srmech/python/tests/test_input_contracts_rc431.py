"""rc431 (`#T1129`) — the four tiny repairs, each gated at the axis it repairs.

WHY THIS MODULE EXISTS
======================
Four repairs landed in this rc that share one property: **nothing in the tree
could have told you they were needed, and nothing would tell you if they were
undone.** Three of them are input-domain contracts (what an op raises, and in
which interpreter mode), and one is a generator literal that ships in the
wheel. None of the four moves a registry count, an ABI number or a
content-address, so the ordinary ratchets are all blind to them.

The gates below are written at the AXIS of each repair rather than against a
file, per the house rule that a gate which fires on correct code is a broken
gate. Each one states its own falsifier.

THE ONE THAT SURPRISED THE BRIEF
================================
The brief that commissioned these repairs described the two ``assert``
conversions as "the shipped contract vanishes under ``python -O``". Executed
both ways, that is **inverted for one of the two**, and the two now differ:

* ``continued_fraction_convergents`` — a real ``raise TypeError`` loop was
  ALREADY below the assert, so ``-O`` behaved CORRECTLY and the assert broke
  the declared contract in the DEFAULT mode. The worse half, since almost
  nobody runs ``-O``.
* ``path_registry.lookup`` — nothing re-enforced the claim, so ``-O`` really
  did drop it, and the malformed argument was then misreported as a registry
  miss rather than a type error.

So the two sites failed in OPPOSITE modes, which is exactly why a gate here
must assert the ``-O`` invariance rather than assert one mode's behaviour:
either single-mode gate would have passed on one of the two defects.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from srmech.cascade.leaves import vec_add
from srmech.math.cyclic import lcm
from srmech.math.primes import factor
from srmech.math.rational import continued_fraction_convergents, rational_div
from srmech.signal_processing.path_registry import lookup


# ── 1. the -O invariance axis (repair 2) ───────────────────────────────────

#: Each row: a call, and the exception type its docstring declares for it.
#: The gate is that the SAME type comes back with and without ``-O``.
_O_INVARIANT_CASES = [
    ("from srmech.math.rational import continued_fraction_convergents as f",
     "f([1, 1.5])", "TypeError"),
    ("from srmech.math.rational import continued_fraction_convergents as f",
     "f([1.5])", "TypeError"),
    ("from srmech.math.rational import continued_fraction_convergents as f",
     "f([])", "ValueError"),
    ("from srmech.signal_processing.path_registry import lookup as f",
     "f(123)", "TypeError"),
    ("from srmech.signal_processing.path_registry import lookup as f",
     "f(None)", "TypeError"),
    ("from srmech.signal_processing.path_registry import lookup as f",
     "f('')", "ValueError"),

    # ── rc433 (`#T1131`) — the twelve promotions + their unpinned siblings.
    # Every row below returned SOMETHING WRONG, or the wrong exception type,
    # under `-O` at rc432. The measured before-states are named per row.

    # Mat.from_rows ragged. BOTH orientations: short-row-first was the silent
    # one (shape (2,1), 3.0 dropped, no error); long-row-first crashed in
    # tolist(). Only the noisy orientation had a test.
    ("from srmech.math.mat import Mat",
     "Mat.from_rows([[1.0], [2.0, 3.0]])", "ValueError"),
    ("from srmech.math.mat import Mat",
     "Mat.from_rows([[1.0, 2.0], [3.0]])", "ValueError"),

    # Vec.__getitem__. v[-5] on n=3 RETURNED v[1] == 20.0 under -O.
    ("from srmech.math.vec import Vec",
     "Vec.from_sequence([10.0, 20.0, 30.0])[-5]", "IndexError"),
    ("from srmech.math.vec import Vec",
     "Vec.from_sequence([10.0, 20.0, 30.0])[3]", "IndexError"),

    # _as_hd — ONE helper behind five ops. Each silently truncated 25 -> 24.
    ("from srmech.math import hdc",
     "hdc.loop_bind_hd([1.0]*25, [1.0]*25)", "ValueError"),
    ("from srmech.math import hdc",
     "hdc.loop_unbind_hd([1.0]*25, [1.0]*25)", "ValueError"),
    ("from srmech.math import hdc",
     "hdc.loop_conj_hd([1.0]*25)", "ValueError"),
    ("from srmech.math import hdc",
     "hdc.loop_inv_hd([1.0]*25)", "ValueError"),
    ("from srmech.math import hdc",
     "hdc.loop_runbind_hd([1.0]*25, [1.0]*25)", "ValueError"),

    # The equal-length guards — three siblings, one of which had a test.
    ("from srmech.math import hdc",
     "hdc.loop_bind_hd([1.0]*56, [1.0]*48)", "ValueError"),
    ("from srmech.math import hdc",
     "hdc.loop_unbind_hd([1.0]*56, [1.0]*48)", "ValueError"),
    ("from srmech.math import hdc",
     "hdc.loop_runbind_hd([1.0]*56, [1.0]*48)", "ValueError"),

    # Zero-norm inverse. -O already gave ZeroDivisionError from 1.0/nsq; the
    # assert MASKED the ruled-correct type in the DEFAULT mode.
    ("from srmech.math import hdc",
     "hdc.loop_inv_hd([0.0]*24)", "ZeroDivisionError"),
    ("from srmech.math import hdc",
     "hdc.loop_inv([0.0]*8)", "ZeroDivisionError"),

    # register_catalog_dir — under -O this RETURNED CLEANLY and poisoned the
    # module-global _USER_CATALOG_DIRS with the bad path.
    ("from srmech import dsl",
     "dsl.register_catalog_dir('/definitely/not/a/real/path/t1131')",
     "FileNotFoundError"),

    # The six identical isinstance(..., Mat) guards. Five had no test at all;
    # every one of them leaked AttributeError on a private attribute under -O.
    ("from srmech.math import laplacian as L",
     "L.mat_matmul([[1.0]], [[1.0]])", "TypeError"),
    ("from srmech.math import laplacian as L",
     "L.mat_solve([[1.0]], [[1.0]])", "TypeError"),
    ("from srmech.math import laplacian as L",
     "L.mat_lstsq([[1.0]], [[1.0]])", "TypeError"),
    ("from srmech.math import laplacian as L",
     "L.mat_hermitian_eigendecompose([[1.0]])", "TypeError"),
    ("from srmech.math import laplacian as L",
     "L.mat_eigvals([[1.0]])", "TypeError"),
    ("from srmech.math import laplacian as L",
     "L.mat_svd([[1.0]])", "TypeError"),

    # operator_norm. The SQUARE assert was DELETED (a real ValueError already
    # sat below it, so -O was the CORRECT half and the assert broke the
    # contract in the default mode — the third instance of the rc431
    # inversion). The NDIM assert was PROMOTED, because an object that lies
    # about ndim while yielding 2-D rows RETURNED 1.0 under -O.
    ("from srmech.physics.qm import bell\n"
     "from srmech.math.mat import Mat",
     "bell.operator_norm(Mat.from_rows([[1.0,2.0,3.0],[4.0,5.0,6.0]]))",
     "ValueError"),
    ("from srmech.physics.qm import bell\n"
     "class _L:\n"
     "    ndim = 1\n"
     "    def __iter__(self):\n"
     "        return iter([[1.0, 0.0], [0.0, 1.0]])",
     "bell.operator_norm(_L())", "TypeError"),

    # The two big-ℚ zero-denominator guards, hoisted above the native check.
    ("from srmech import _native",
     "_native.bigq_reduce_c(5, 0)", "ZeroDivisionError"),
    ("from srmech import _native",
     "_native.bigq_div_c(1, 2, 0, 1)", "ZeroDivisionError"),
]


def _raised_type(imp: str, call: str, optimized: bool) -> str:
    """Run ``call`` in a FRESH interpreter and report the exception type name.

    A subprocess is not ceremony here: ``python -O`` is a startup flag, and
    ``assert`` statements are stripped at COMPILE time, so an in-process test
    cannot observe the optimized behaviour of an already-imported module at
    all. Measuring this axis requires a separate interpreter by construction.
    """
    # NOT textwrap.dedent on an interpolated block: ``imp`` may itself be
    # multi-line (the control below plants a whole function), and dedent
    # computes ONE common prefix for the formatted result, so the second and
    # later lines of an interpolated block lose their indentation and the
    # probe dies with IndentationError. Measured while writing this file --
    # the control was the only case with a multi-line ``imp``, so the bug hit
    # exactly the test whose job is to prove the probe works.
    src = "\n".join([
        imp,
        "try:",
        f"    {call}",
        "except BaseException as e:",
        "    print(type(e).__name__)",
        "else:",
        '    print("NO_RAISE")',
    ])
    argv = [sys.executable] + (["-O"] if optimized else []) + ["-c", src]
    out = subprocess.run(argv, capture_output=True, text=True, timeout=180)
    assert out.returncode == 0, f"probe crashed: {out.stderr[-500:]}"
    return out.stdout.strip().splitlines()[-1]


@pytest.mark.parametrize("imp,call,declared", _O_INVARIANT_CASES)
def test_declared_exception_survives_python_dash_O(imp, call, declared):
    """The repaired contract holds in BOTH interpreter modes.

    FALSIFIER: if the validation is ever written back as an ``assert``, the
    two modes diverge and this fails — which is the whole defect class. It
    catches BOTH observed directions, because it compares the modes to each
    other AND to the declared type, rather than trusting either one.
    """
    plain = _raised_type(imp, call, optimized=False)
    opt = _raised_type(imp, call, optimized=True)
    assert plain == opt, (
        f"{call} raises {plain} normally but {opt} under -O: input validation "
        f"has been written as an assert, which -O strips")
    assert plain == declared, (
        f"{call} raises {plain}; the docstring declares {declared}")


def test_the_dash_O_probe_can_actually_detect_a_stripped_assert():
    """CONTROL on the instrument above — a gate that cannot return otherwise
    is not a measurement.

    A planted function whose ONLY validation is an ``assert`` must show the
    two modes disagreeing. If this ever passes quietly, ``_raised_type`` has
    stopped distinguishing the modes and every assertion above is vacuous.
    """
    imp = "def f(x):\n    assert isinstance(x, int), 'must be int'\n    return x"
    plain = _raised_type(imp, "f('nope')", optimized=False)
    opt = _raised_type(imp, "f('nope')", optimized=True)
    assert plain == "AssertionError", plain
    assert opt == "NO_RAISE", (
        f"planted assert still fired under -O ({opt}) — the probe is not "
        f"running optimized and the -O half of this module proves nothing")


# ── 2. the declared-Raises axis (repair 4) ─────────────────────────────────

#: (callable, args, exception) triples for contracts that rc431 DECLARED.
#: Behaviour did not change here; the docstrings were incomplete. The gate
#: exists so the declaration and the behaviour cannot drift apart again.
_DECLARED_RAISES = [
    (lcm, (-1, 2), ValueError),
    (lcm, (2.5, 2), TypeError),
    (lcm, (2 ** 65, 2), ValueError),
    (lcm, (2 ** 63, 2 ** 63 - 1), OverflowError),
    (factor, (-6,), ValueError),
    (factor, (2.5,), TypeError),
    (factor, (2 ** 65,), ValueError),
    (rational_div, (5, (1, 1)), TypeError),
    (rational_div, ((1, -2), (1, 1)), ValueError),
    (rational_div, ((1, 2), (0, 1)), ZeroDivisionError),
]


@pytest.mark.parametrize("fn,args,exc", _DECLARED_RAISES)
def test_the_raises_block_matches_what_is_raised(fn, args, exc):
    """Every exception rc431 added to a ``Raises:`` block is the one the op
    actually raises for that input.

    FALSIFIER: a docstring listing an exception the code does not raise (or a
    code path changing type under a later edit) fails here. These three
    docstrings were each declaring ONE exception while raising two or three,
    and in ``factor``'s case the single declared one was the UNREACHABLE one.
    """
    with pytest.raises(exc):
        fn(*args)


def test_factor_returns_empty_only_for_the_in_range_small_cases():
    """The companion to ``factor``'s ValueError row, and the reason it is
    worth stating: the prose "Returns ``[]`` for ``n < 2``" reads as though it
    covers ``n = -6``, and it does not — a negative RAISES.
    """
    assert factor(0) == []
    assert factor(1) == []
    assert factor(2) == [(2, 1)]
    with pytest.raises(ValueError):
        factor(-6)


# ── 3. the silent-truncation axis (repair 3) ───────────────────────────────

def test_vec_add_refuses_both_orientations_of_a_length_mismatch():
    """BOTH orientations, because the defect was asymmetric.

    ``vec_add`` silently returned a truncated answer one way round and leaked
    a bare ``IndexError`` the other, so a guard written against only the
    noisy orientation would have left the silent one — the half that corrupts
    data — intact. Asserting one direction here would repeat that mistake.
    """
    with pytest.raises(ValueError):
        vec_add([1.0], [1.0, 2.0])
    with pytest.raises(ValueError):
        vec_add([1.0, 2.0], [1.0])
    # the guard must not have eaten the valid case
    assert vec_add([1.0, 2.0], [3.0, 4.0]) == [4.0, 6.0]
    assert vec_add([], []) == []


# ── 4. the shipped-literal axis (repair 1) ─────────────────────────────────

def _synth_arg_provider():
    """Import ``tools/gen_tool_docs.py`` the way the generator itself runs.

    Skips rather than fails when the tools directory is absent, because a
    WHEEL install legitimately has no ``tools/`` — the file this gate is
    about is generator input, not shipped code. (Its OUTPUT ships, which is
    exactly why the generator is worth gating from the source tree.)
    """
    import pathlib
    tools = pathlib.Path(__file__).resolve().parent.parent / "tools"
    if not (tools / "gen_tool_docs.py").is_file():
        pytest.skip("tools/ not present (wheel install) — generator not gated here")
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    import gen_tool_docs
    return gen_tool_docs


def _required_param_synths():
    """Every (op, param, value) the generator would synthesise and EXECUTE."""
    g = _synth_arg_provider()
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    for entry in get_tool_schema().tools:
        for p in (getattr(entry, "parameters", None) or []):
            if not p.required:
                continue
            good, val = g._synth_arg(p.type, p.name, entry.name)
            if good:
                yield entry.name, p.name, val


#: Bare placeholder literals that say nothing about their own origin. rc430
#: removed ``"a"`` from the MCP smoke's synthesizer; rc431 removed ``"abc"``
#: from THIS one, whose output is committed into
#: ``srmech/introspect/_tool_docs.py`` and ships in the wheel.
_ANONYMOUS_LITERALS = {"a", "abc", "foo", "bar", "test", "x"}


def test_no_required_param_is_fed_an_anonymous_string_literal():
    """STRICT ZERO on the decidable class.

    ``_build_example`` EXECUTES what ``_synth_arg`` returns, so any string in
    this table can escape into a file, a log or an error message. A
    self-describing value names its own origin when that happens; ``"abc"``
    names nothing. Measured at rc431: 24 required ``str`` params were being
    fed ``"abc"`` and 7 of them reached a real call.

    FALSIFIER: re-introducing any bare placeholder for a live param type
    fails this. Note it is scoped to params that are actually REACHED — a
    dead table row is not a defect, and the companion test below is what
    keeps this one from passing merely because nothing is reached.
    """
    offenders = [(op, param, val) for op, param, val in _required_param_synths()
                 if isinstance(val, str) and val in _ANONYMOUS_LITERALS]
    assert not offenders, (
        f"{len(offenders)} required param(s) receive an anonymous placeholder "
        f"literal that _build_example will EXECUTE: {offenders[:10]}")


def test_the_literal_scan_actually_reaches_string_params():
    """CONTROL on the scan above — an instrument that cannot return otherwise
    is not a measurement, and a zero from a scanner that reached nothing is a
    FALSE null.

    This asserts the scan visits a healthy number of string-valued synths and
    that the self-describing convention is the one in force, so the strict
    zero above is a real absence rather than an empty iteration.
    """
    strings = [(op, param, val) for op, param, val in _required_param_synths()
               if isinstance(val, str)]
    assert len(strings) >= 20, (
        f"only {len(strings)} string synths reached — the scan has stopped "
        f"seeing its own subject and the strict-zero test above is vacuous")


def test_every_synthesised_string_carries_the_self_describing_literal():
    """The convention axis — stated as a PREDICATE, never as a census.

    rc431 repair (`#T1129`): this assertion was written as
    ``len(named) >= 20`` over the params still receiving the *synthesised*
    literal, measured at 24. That is a ratchet pointing the wrong way. A
    harvested value from the op's own worked example takes PRECEDENCE over
    the type table (``_synth_arg`` consults ``_ea.provider()`` first), so
    curating five more examples — an unambiguous improvement — drops the
    count to 19 and turns the gate red on correct code. A gate that fires
    on an improvement teaches people to weaken gates.

    The axis it was reaching for is not "how many params are synthesised"
    but "every string this generator SYNTHESISES names its own origin".
    That is count-free: it holds at 24 synthesised params, at 2, and
    vacuously at 0 — and the reach control above is what keeps 0 honest.

    It is also stricter on PARTIAL drift, which is the case the census could
    not see. Demonstrated by construction, not argued: drifting exactly four
    of the 24 synthesised params leaves ``named == 20``, so
    ``len(named) >= 20`` PASSES, while the predicate below is strict-zero per
    param and fails, naming which four. (A first attempt drifted 11 and
    failed both — the two only separate BELOW the threshold's slack, which is
    the whole objection to writing the gate as a threshold.) (A first draft of this docstring claimed the census also missed
    TOTAL drift — that was wrong and the mutation audit caught it: flipping
    the table row to ``"zzz"`` sends ``named`` to 0 and the old assertion
    does fail. Recorded because the claim was written before it was run.)
    """
    g = _synth_arg_provider()
    import example_args as _ea

    offenders = []
    for op, param, val in _required_param_synths():
        if not isinstance(val, str):
            continue
        if _ea.provider().get(op, param) is not _ea.UNSYNTHESIZABLE:
            continue  # curated/harvested — valid by construction, not our axis
        offenders.append((op, param, val))
    bad = [t for t in offenders if t[2] != "srmech_synth"]
    assert not bad, (
        f"{len(bad)} synthesised string(s) do not carry the self-describing "
        f"literal 'srmech_synth'; the rc430/rc431 convention has drifted: "
        f"{bad[:10]}")

    # The type table is the single source of the literal — pin it directly so
    # the predicate above cannot pass merely because nothing is synthesised.
    good, val = g._synth_arg("str", "label", "")
    assert good and val == "srmech_synth", (
        f"the generator's 'str' row is {val!r}; the self-describing "
        f"convention has been edited out of the table itself")
