"""rc465 (`#T1188`) — the SILENT-CARRIER-DEMOTION probe: one instrument, two consumers.

``tests/test_silent_carrier_demotion_rc463.py`` is the ratchet; :func:`census`
writes ``tests/demotion_census_rc465.ndjson``. Both import the functions below,
so the shipped declaration and the published measurement cannot drift apart by
being separately hand-rolled — the same discipline ``tools/frame_probe.py``
carries, and for the same reason.

WHY THIS EXISTS
---------------
rc463 shipped the demotion class as **six hand-written rows in one test file**,
all six in ``srmech.math.laplacian``, with ``CEIL_SILENT_DEMOTION = 6`` pinned
to ``len(_DEMOTION_MANIFEST)``. Its own module docstring named the hole
(blind spot 1): *"A missing MANIFEST row is invisible. The gate asserts over the
rows it HAS. It has no oracle telling it a row is absent."* A gate over a
hand-written roster measures the roster.

Worse, the rc463 predicate's ADMISSION conjunct is decided **by the signature**,
so an op annotated ``Sequence[float]`` was excluded BY CONSTRUCTION however
exact the operand it was handed. That is R2 shielding: rc463's own honesty
ladder rates a float parameter ANNOTATION at rung **R2 — WEAK, "nothing
enforces it"** — and then let exactly that rung decide membership. A type
annotation stood in for an accuracy contract. Admission here is decided by
MEASUREMENT, and the parameter roster is read from the REGISTRY.

THE ORACLE IS DIFFERENTIAL, SO IT NEEDS NO PER-OP EXACT VALUE
--------------------------------------------------------------
That is what makes the manifest auto-populating. Three calls, one witness
triple, substituted at one numeric leaf of one sequence-shaped parameter:

    P = 2**53 + 1   the smallest positive integer float64 cannot represent
    F = 2**53       the value float64 collapses P to
    G = 2**53 + 2   the next representable neighbour above F

    out(P) == out(F)  and  out(G) != out(F)   ->  DEMOTED
    out(P) != out(F)                          ->  EXACT
    all three equal                           ->  INSENSITIVE

``INSENSITIVE`` is a CLASSIFIED NULL, not a pass: the leaf did not reach the
output. It is retried at further leaves before it is recorded, because the
verdict is position-specific.

``out(G) != out(F)`` is the vacuity guard and it is not decoration. Without it
an op that returns a constant, or that ignores the parameter, reads DEMOTED —
"an instrument that cannot return otherwise is not a measurement".

THE BASE MUST BE EXACT OR THE VERDICT IS NOT ABOUT THE CARRIER
---------------------------------------------------------------
If ANOTHER operand is a float, a float result is what the caller asked for and
"exact in, rounded out" was never tested. So every numeric leaf of the base is
exactified first (an integral ``1.0`` becomes ``1``); a base still carrying a
NON-integral float is recorded as ``INEXACT_BASE`` and is never called DEMOTED.

WHAT THIS PROBE CANNOT SEE — required disclosure
-------------------------------------------------
 1. **Coverage is bounded by argument reach.** An op the probe cannot build a
    binding for is emitted as ``NO_SHAPE`` and counted, never skipped silently.
    That count is the honest statement of the instrument's reach and it is what
    ``CEIL_DEMOTION_UNREACHED_BY_CELL`` ratchets down —
    ``tests/test_silent_carrier_demotion_rc463.py``, where that constant is
    DEFINED and ASSERTED, per CI cell. It was not, through rc465: this sentence named a
    ratchet that existed nowhere else in the repo, so the instrument's own
    reach was the one number in this file with no gate under it (rc465-fix,
    `#T1188`). The larger unreached class is ``RAISED`` — a real refusal by a
    real op against a synthesised binding — and it is deliberately left
    unratcheted, because driving it down is a question about
    :func:`synthesize`, not about the library.
 2. **One parameter at a time.** A demotion that needs two exact operands
    simultaneously is out of reach.
 3. **Bounded leaf positions** (:data:`MAX_LEAVES`). A demotion visible only at
    leaf 40 of a long vector is out of reach.
 4. **It measures through PYTHON only** (rc463 blind spot 4, unchanged). A
    demotion in the C projection the Python path does not share is invisible.
 5. **Layer-3 vocabulary is still a KEYWORD LIST** (rc463 blind spot 5). The
    delegate follow is generalised here to ``fn.__globals__`` — rc463's read
    ``getattr(_la, name)`` and so could not address an op outside
    ``srmech.math.laplacian`` at all, which is why its Layer 3 was structurally
    confined to the module its six hand-rows came from.
 6. **Byte / bit carriers admit no witness.** They surface as ``NO_SHAPE`` with
    the reason stated, which is a DOMAIN fact recorded as data. rc463 asserted
    this of the whole ``hdc`` family; rc465 measured it false — ``loop_conj``,
    ``loop_bind``, ``loop_inv``, ``loop_left_op`` and ``loop_right_op`` take
    float sequences and round P.

numpy-free. No ``abs()`` — a sign is a Class-K pin-slot branch composed with
Class C. No stdlib ``fractions``.
"""

from __future__ import annotations

import inspect
import json
import re
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import example_args as ea  # noqa: E402

PY_ROOT = _TOOLS.parent


def is_native() -> bool:
    """Is a `libsrmech` actually dispatching in THIS process?

    rc465-fix (`#T1188`). The verdicts below are read off VALUES the ops
    return, so a census taken with the C peers dispatching is a different
    measurement from one taken without them — not a stale copy of it.
    """
    try:
        from srmech import _native
        return bool(getattr(_native, "HAS_NATIVE", False))
    except Exception:                        # noqa: BLE001 — absent is "pure"
        return False


def census_path(native: Optional[bool] = None) -> Path:
    """The census artefact for a CELL.

    ⚠️ **There are two, and that is the whole point** (rc465-fix, `#T1188`).
    The first cut shipped ONE file, taken with native present, and asserted it
    against a live census in whatever cell the gate happened to run in. Every
    pure CI shard was therefore red on an unchanged tree — MEASURED locally by
    running the full suite with ``srmech/_native/libsrmech.so`` moved aside and
    ``SRMECH_EXPECT_PURE=1``: 3 failed, 13413 passed, and all three failures
    were this file's currency, roster and ceiling assertions.

    It is the same per-cell fact ``tests/test_worked_examples_execute_rc354.py``
    already records for its ledger — *"a number measured in one cell must never
    be pinned against the other"* — arrived at from the other direction: there
    the ceiling is a per-cell dict, here the whole artefact is per cell, because
    this gate asserts a full histogram and a roster IDENTITY rather than a
    count.
    """
    n = is_native() if native is None else native
    name = "demotion_census_rc465.ndjson" if n \
        else "demotion_census_rc465_pure.ndjson"
    return PY_ROOT / "tests" / name


#: The NATIVE-cell artefact. Kept as a module constant because it is the one a
#: reader means when they say "the census"; :func:`census_path` is what code
#: should call.
CENSUS = PY_ROOT / "tests" / "demotion_census_rc465.ndjson"

#: ``2**53 + 1`` — the smallest positive integer float64 cannot represent.
#: Significand 54 bits. The SAME value rc344 pinned for ``kron`` and rc463 for
#: the whole class.
P = 2 ** 53 + 1
#: What float64 collapses :data:`P` to.
F = 2 ** 53
#: The next representable neighbour above :data:`F`. Its role is the vacuity
#: guard: an op that ignores the parameter answers the same for F and G.
G = 2 ** 53 + 2
#: A COARSE fourth value, three ULP-decades away, used only to split the null.
#: ``F`` and ``G`` differ by one float64 step, so an op whose OWN output
#: resolution is coarser than that answers identically for all three — and a
#: two-way verdict would file it under "the leaf never reached the output",
#: which is a different and false statement. Measured: ``octonion_norm`` reduces
#: through a truncated Class-N rational ``sqrt`` and returns the same float for
#: P, F and G while ``H`` moves it, so it is ``UNRESOLVED_AT_WITNESS``, not
#: ``INSENSITIVE``. Classify every null; do not merge two of them.
H = 3 * 2 ** 53

#: How many numeric leaves of one parameter are tried before the row is
#: recorded ``INSENSITIVE``. Bounded so the census terminates; blind spot 3.
MAX_LEAVES = 6

#: Shapes synthesised for a sequence-shaped parameter with no harvested value.
#: The Cayley-Dickson ladder, because that is what this package's vector ops are
#: dimensioned by; ``3`` is included because the graph / geometry family is not.
FLAT_DIMS = (8, 4, 3, 2, 16, 1)
#: Square shapes for a matrix-shaped parameter.
SQUARE_DIMS = (2, 3, 4, 8, 1)

#: Per-call wall-clock cutoff, seconds. A call that exceeds it is recorded
#: ``RAISED`` with ``TIMEOUT`` and the number — never silently dropped.
#:
#: ⚠️ ``signal.SIGALRM`` fires between BYTECODES. A single long call inside the
#: native library does not return to the interpreter, so the alarm lands when
#: it finishes, not when it expires. That is why the per-op budget below exists
#: as well: a cutoff that can be outrun is not a cutoff.
CALL_TIMEOUT = 20

#: ⚠️ **rc465 (`#T1188`) — the shape budget is a CALL-TIMEOUT rule, not a
#: cumulative wall clock, because a verdict must be a function of the TREE.**
#:
#: rc465 shipped this as ``PARAM_BUDGET = 6.0`` seconds of cumulative time per
#: ``(op, parameter)``: once a row had spent that, the remaining candidate
#: SHAPES were abandoned and the row was recorded ``BUDGET_EXHAUSTED``. Its own
#: comment named the hazard it then implemented — *"a bare wall-clock cutoff
#: makes a verdict depend on the machine, so an op could be adjudicated on a
#: fast runner and unadjudicated on a slow one"* — and
#: ``test_layer2_the_committed_census_matches_the_live_one`` asserts the whole
#: verdict HISTOGRAM, so any such flip is a red CI run on an unchanged tree.
#:
#: MEASURED before the change (WSL2 py3.10, native present): every one of the
#: six ``BUDGET_EXHAUSTED`` rows exhausted after **exactly one candidate shape
#: and one call**, and that call had itself hit :data:`CALL_TIMEOUT` —
#: ``alcove_fold.weight`` 20.4s/1 call, ``equal_temperament_partials.degrees``
#: 59.7s/1 call, the four ``mlse`` params 33.6–58.5s/1 call each. Nothing was
#: ever abandoned because ORDINARY calls had accumulated; the accumulation
#: clause only added machine dependence.
#:
#: So the rule is now the one the measurement showed was actually operating:
#: **a call that TIMES OUT abandons the remaining shapes**, recorded as
#: ``CALL_TIMED_OUT``. The same six rows are recorded, on this cell and on a
#: slower one, and a row that answers in milliseconds can no longer be retired
#: by the clock. A timeout still involves a wall clock — :data:`CALL_TIMEOUT`
#: is unavoidable, or the census hangs (see the weight-lattice CONTRACT_SKIPs)
#: — but 20s against a typical 5ms call is a ~4000x margin, where 6s of
#: accumulation was not a margin at all.
TIMEOUT_MARKER = "TIMEOUT>"

#: Ops skipped by NAME with the reason attached — the same discipline as
#: ``frame_probe.CONTRACT_SKIP``: a probe must not violate a contract the op
#: states plainly. ``gf_*`` document "p must be PRIME" and the native peer
#: ``assert()``s it, which took SIGABRT under the asserts-live CI job at rc430.
CONTRACT_SKIP: Dict[str, str] = {
    "srmech.math.modular_linalg.gf_rref":
        "p must be PRIME (2 <= p < 2**31); the native peer asserts",
    "srmech.math.modular_linalg.gf_solve": "same prime contract as gf_rref",
    "srmech.math.modular_linalg.gf_nullspace": "same prime contract as gf_rref",
    # The witness is a LABEL, not a value carrier. A Dynkin / weight coordinate
    # of 2**53 asks these ops to enumerate a Weyl orbit of that size, so the
    # substitution is not "the same question at a bigger magnitude" — it is a
    # different question the op cannot be asked. MEASURED: the first census run
    # hung indefinitely inside `tensor_product_multiplicities` (no verdict after
    # 20 min; SIGALRM cannot pre-empt a long pure loop that never yields, and
    # the per-shape budget is only checked BETWEEN shapes). `frame_probe`
    # already names two of these three in its own SLOW_SKIP for the same
    # structural reason (|P_k| is quartic in level).
    "srmech.math.weight_lattice.tensor_product_multiplicities":
        "a weight LABEL, not a value carrier: a 2**53 Dynkin coordinate makes "
        "the Weyl-orbit sum unbounded (census hang, measured)",
    "srmech.math.weight_lattice.affine_fusion_multiplicities":
        "same weight-label contract as tensor_product_multiplicities",
    "srmech.math.weight_lattice.verlinde_fusion_multiplicities":
        "same weight-label contract; frame_probe.SLOW_SKIP names it too",
    # ⚠️ rc465-fix (`#T1188`) — THE OP THAT WAS KILLING CI RUNNERS, and the
    # reason is the same one the three weight-lattice rows above give.
    #
    # MEASURED (per-op peak-RSS profile over the whole census, WSL2 py3.10):
    #
    #     peak RSS 7342 MiB (start 35 MiB)
    #       +7256.8 MiB -> 7342.4 MiB   srmech.signal_processing.mlse
    #       +  17.4 MiB ->   81.4 MiB   cascade.matrix_cascades.singular_values_exact
    #       +  12.1 MiB ->   59.9 MiB   cascade.matrix_cascades.eigvals_exact
    #
    # One op accounts for 7.1 GiB of a 7.3 GiB peak; the next largest is 17 MiB.
    # A GitHub-hosted Linux runner has ~7 GiB, so the census reached `mlse`
    # about five minutes in and the RUNNER died — reported as
    # "The runner has received a shutdown signal" and exit 143, with no pytest
    # failure line, on `ubuntu-latest` py3.10 and py3.12, `fallback shard 6/6`
    # and `asserts-live shard 4/4`, in EVERY run on this branch, including a
    # 5-job re-run far under the concurrency cap. Those four jobs' logs carry
    # ZERO `F` markers and their `always()` artifact steps are `skipped`, which
    # is what a lost runner looks like and what a failing test does not.
    #
    # WHY IT IS A CONTRACT SKIP AND NOT A BUDGET: `mlse`'s `n_states` means
    # `A**L` (the rc425 v14 ABI bump), so the Viterbi trellis is EXPONENTIAL in
    # the operand. Substituting `2**53` into `alphabet` / `channel_taps` /
    # `initial_state` / `observations` does not ask the same question at a
    # bigger magnitude — it asks for a trellis the op cannot build, exactly as
    # a `2**53` Dynkin coordinate asks for an unbounded Weyl orbit. The witness
    # is not a value carrier here. A wall-clock or memory cutoff would report
    # the machine; this reports the CONTRACT.
    "srmech.signal_processing.mlse":
        "n_states is A**L, so the trellis is EXPONENTIAL in the operand: a "
        "2**53 witness asks for a state space the op cannot build, not the "
        "same question at a bigger magnitude. MEASURED +7.1 GiB peak RSS in "
        "one op, which killed the CI runner outright",
}

#: Ops skipped by NAME **in one cell only**, because their per-call cost THERE
#: sits at the :data:`CALL_TIMEOUT` boundary and the verdict therefore stops
#: being a function of the tree. Same discipline as ``frame_probe.SLOW_SKIP``,
#: made PER CELL because the cost is (rc465-fix, `#T1188`).
#:
#: MEASURED, same tree, same commit, `seconds` straight off the two censuses:
#:
#:   ==========================  ========  ========
#:   row                          native    pure
#:   ==========================  ========  ========
#:   recover_check::weights          0.154    53.1
#:   recover_check_spectral::w.      0.159    59.1
#:   recover_check::charges          6.615    16.6
#:   recover_check_spectral::ch.     6.652    23.4
#:   recover_check_spectral::ed.     4.686   526.5
#:   ==========================  ========  ========
#:
#: The instability is measured, not feared. Two consecutive pure censuses on an
#: unchanged tree: run 1 differed from the committed artefact in **0** rows,
#: run 2 in exactly **2** — ``recover_check::weights`` and
#: ``recover_check_spectral::weights``, both ``DEMOTED -> EXACT``, at 56.0s and
#: 61.2s. A call inside each sometimes crosses the 20s cutoff and sometimes
#: does not, so the verdict is decided by machine load. The NATIVE cell measures
#: the same two rows in 0.15s and is stable across three runs, so skipping them
#: there would delete real signal to fix someone else's problem — which is why
#: this roster is keyed by cell and the native column is EMPTY.
#:
#: Drain path, stated rather than implied: these are pure-Python Laplacian
#: recovery checks whose cost is dominated by a dense eigen-solve the C peer
#: does in microseconds. The rows come back the moment either the pure path
#: gets cheaper or the probe learns to bound a call by WORK rather than by
#: wall clock.
SLOW_SKIP: Dict[str, Dict[str, str]] = {
    "native": {},
    "pure": {
        "srmech.math.laplacian.recover_check":
            "pure cost 53-56s per row against a 20s CALL_TIMEOUT; measured "
            "unstable (DEMOTED <-> EXACT) across two consecutive censuses. "
            "0.154s and stable in the native cell, where it is NOT skipped.",
        "srmech.math.laplacian.recover_check_spectral":
            "pure cost 59-526s per row against a 20s CALL_TIMEOUT; measured "
            "unstable (DEMOTED <-> EXACT) across two consecutive censuses. "
            "0.159s and stable in the native cell, where it is NOT skipped.",
    },
}

_IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")

#: Type identifiers that denote a sequence-shaped parameter — one that CAN carry
#: a numeric leaf. Read from the REGISTRY, never from the signature: the
#: signature is what shielded this class in rc463.
_SEQ_IDENTS = frozenset({
    "HV", "Vec", "Mat", "QMat", "list", "sequence", "Sequence",
    "tuple", "array", "iterable", "Iterable",
})

#: Identifiers that make a shape UNSYNTHESISABLE by this probe (no numeric leaf
#: is constructible). Recorded, not skipped.
_OPAQUE_IDENTS = frozenset({
    "bytes", "str", "dict", "Mapping", "SpectralHandle", "host_callable",
    "host_rng", "Path", "pathlib", "object", "ChainSpec", "One",
    "RecoverableFold", "MockQSeries", "operator_name", "CDRegister",
})


def type_idents(ty: str) -> Tuple[str, ...]:
    """The identifier tokens of a registry type string."""
    return tuple(_IDENT.findall(ty or ""))


def sequence_shaped(ty: str) -> bool:
    """Does the REGISTRY declare this parameter as sequence-shaped?"""
    return any(i in _SEQ_IDENTS for i in type_idents(ty))


# ── exactness plumbing ────────────────────────────────────────────────────────
def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def exactify(v: Any) -> Tuple[Any, bool]:
    """Replace every INTEGRAL float leaf with the ``int`` it equals.

    Returns ``(value, clean)``; ``clean`` is False when a NON-integral float
    survives, which disqualifies the binding from a DEMOTED verdict.
    """
    if isinstance(v, bool) or v is None:
        return v, True
    if isinstance(v, float):
        if v == int(v):
            return int(v), True
        return v, False
    if isinstance(v, list):
        out: List[Any] = []
        ok = True
        for x in v:
            y, k = exactify(x)
            out.append(y)
            ok = ok and k
        return out, ok
    if isinstance(v, tuple):
        acc: List[Any] = []
        ok = True
        for x in v:
            y, k = exactify(x)
            acc.append(y)
            ok = ok and k
        return tuple(acc), ok
    if isinstance(v, dict):
        dd: Dict[Any, Any] = {}
        ok = True
        for k2, x in v.items():
            y, k = exactify(x)
            dd[k2] = y
            ok = ok and k
        return dd, ok
    return v, True


def leaf_paths(v: Any, prefix: Tuple[int, ...] = ()) -> Iterator[Tuple[int, ...]]:
    """Paths to every numeric leaf of a nested list/tuple, depth-first."""
    if isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            yield from leaf_paths(x, prefix + (i,))
    elif _is_int(v) or isinstance(v, float):
        yield prefix


def set_leaf(v: Any, path: Tuple[int, ...], value: Any) -> Any:
    """A COPY of ``v`` with the leaf at ``path`` replaced. No mutation."""
    if not path:
        return value
    i, rest = path[0], path[1:]
    seq = list(v)
    seq[i] = set_leaf(seq[i], rest, value)
    return tuple(seq) if isinstance(v, tuple) else seq


def synthesize(ty: str, extra_dims: Sequence[int] = ()) -> List[Any]:
    """Candidate INT-filled shapes for a sequence-shaped type, best first.

    Int-filled is load-bearing: a synthesised ``1.0`` would force every op —
    exact ones included — onto a float route, and the probe would then report
    the whole population DEMOTED.

    ``extra_dims`` carries the lengths of the OTHER list-valued parameters in
    the same binding, tried first. Measured: without it ``dense_adjacency`` and
    ``dense_laplacian`` reported ``RAISED`` on ``weights``, because a weight
    vector must be as long as the harvested ``edges`` list and no dimension in
    :data:`FLAT_DIMS` happened to match. That is an instrument artefact wearing
    the name of an op fact — the exact confusion this rc's D2 half is about.
    """
    idents = set(type_idents(ty))
    if idents & _OPAQUE_IDENTS and not (idents & {"list", "Sequence", "sequence"}):
        return []
    matrixish = bool(idents & {"Mat", "QMat"}) or "list[list" in ty \
        or "Sequence[Sequence" in ty
    dims: List[int] = []
    for n in tuple(extra_dims) + FLAT_DIMS:
        if n > 0 and n not in dims:
            dims.append(n)
    # A UNIT-FIRST vector isolates the witness: every other leaf is 0, so a
    # derived quantity carries the witness alone. ``octonion_norm`` needs it —
    # sqrt(P^2 + junk) can round P, F and G together and read INSENSITIVE.
    flats = [[1] * n for n in dims] + [[1] + [0] * (n - 1) for n in dims if n > 1]
    squares = [[[1 if r == c else 0 for c in range(n)] for r in range(n)]
               for n in SQUARE_DIMS]
    return (squares + flats) if matrixish else (flats + squares)


# ── exact structural comparison ───────────────────────────────────────────────
_ADDR = re.compile(r" at 0x[0-9a-fA-F]+")


def canon(x: Any) -> Any:
    """A hashable EXACT canonical form. Type-tagged, so ``1`` and ``1.0`` differ.

    That distinction is the point: an op that returns the ``int`` it was given
    is exact; one that returns ``1.0`` has passed the value through a float
    carrier even where the magnitude happened to survive.
    """
    if x is None or isinstance(x, bool):
        return ("b", x)
    if _is_int(x):
        return ("i", x)
    if isinstance(x, float):
        return ("f", x.hex() if x == x else "nan")
    if isinstance(x, complex):
        return ("c", canon(x.real), canon(x.imag))
    if isinstance(x, (bytes, bytearray)):
        return ("y", bytes(x))
    if isinstance(x, str):
        return ("s", x)
    if hasattr(x, "to_lists"):
        return ("Q", canon(x.to_lists()))
    if hasattr(x, "tolist"):
        return ("M", canon(x.tolist()))
    if hasattr(x, "numerator") and hasattr(x, "denominator"):
        return ("q", canon(x.numerator), canon(x.denominator))
    if isinstance(x, dict):
        return ("d", tuple(sorted((canon(k), canon(v)) for k, v in x.items())))
    if isinstance(x, (list, tuple, set, frozenset)):
        return ("l", tuple(canon(v) for v in x))
    r = repr(x)
    if _ADDR.search(r):
        return ("?", type(x).__name__)          # unstable identity: uncomparable
    return ("r", r)


def _uncomparable(c: Any) -> bool:
    """Does this canonical form contain the unstable-identity marker?

    Walks EVERY element, and guards the empty tuple. The first draft read
    ``c[0] == "?" or any(... for v in c[1:])``, which assumed every nested
    tuple was a tagged node — but a container node's payload is a tuple OF
    nodes, so the recursion reached a bare child tuple, then an empty one, and
    the whole census died on ``IndexError`` after ~200 ops. A scanner must not
    assume the shape it is scanning.
    """
    if isinstance(c, tuple):
        if c and c[0] == "?":
            return True
        return any(_uncomparable(v) for v in c)
    return False


class _Timeout(Exception):
    pass


def _alarm(_sig, _frm):                                # pragma: no cover
    raise _Timeout()


def call_bounded(fn, kwargs: Dict[str, Any]):
    """``(ok, value_or_exception_string)`` with the per-call cutoff applied."""
    has = hasattr(signal, "SIGALRM")
    old = None
    if has:
        old = signal.signal(signal.SIGALRM, _alarm)
        signal.setitimer(signal.ITIMER_REAL, CALL_TIMEOUT)
    try:
        return True, fn(**kwargs)
    except _Timeout:
        return False, f"TIMEOUT>{CALL_TIMEOUT}s"
    except BaseException as exc:
        return False, f"{type(exc).__name__}: {exc}"[:160]
    finally:
        if has:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)


# ── the honesty read (rc463 Layer 3, generalised off srmech.math.laplacian) ───
#: R3 vocabulary, LIFTED VERBATIM from
#: ``tests/test_silent_carrier_demotion_rc463.py``. A closed keyword list; see
#: blind spot 5. Do NOT simplify it.
R3_VOCABULARY = (
    "ulp", "to round-off", "round-off", "tolerance", "float64", "approximate",
    "terminal float lift", "accurate to", "~1e-",
)


def declaration_hits(fn) -> List[str]:
    """Every R3 marker reachable from ``fn``'s own contract surface.

    ⚠️ The delegation follow is rc463's, with ONE change that is the whole point
    of this file: rc463 resolved a delegate as ``getattr(_la, name)``, hard-wired
    to ``srmech.math.laplacian``, so Layer 3 could not read the contract of any
    op outside the module its six hand-rows came from. Here the delegate is
    resolved in ``fn.__globals__``, which is the module the body actually names
    its callees in.
    """
    doc = (inspect.getdoc(fn) or "").lower()
    hits = [d for d in R3_VOCABULARY if d in doc]
    try:
        if "exact" in inspect.signature(fn).parameters:
            hits.append("exact= opt-in")
    except (TypeError, ValueError):
        pass
    if not hits:
        code = getattr(fn, "__code__", None)
        glb = getattr(fn, "__globals__", {}) or {}
        for name in (code.co_names if code is not None else ()):
            delegate = glb.get(name)
            if delegate is None or delegate is fn or not callable(delegate):
                continue
            ddoc = (inspect.getdoc(delegate) or "").lower()
            hits += [f"{d} (via {name})" for d in R3_VOCABULARY if d in ddoc]
            if hits:
                break
    return hits


# ── the probe ─────────────────────────────────────────────────────────────────
def _base_for(entry, rows: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, str]:
    """``(base, exact_clean, source)`` — the harvested binding, exactified."""
    raw = dict((rows.get(entry.name) or {}).get("args") or {})
    src = "ledger" if raw else "none"
    if not raw:
        hint = getattr(entry, "smoke_test_hint", None)
        if isinstance(hint, dict) and isinstance(hint.get("args"), dict):
            raw = dict(hint["args"])
            src = "smoke_test_hint"
    base, clean = exactify(raw)
    return base, clean, src


def _fill_required(fn, base: Dict[str, Any], entry
                   ) -> Tuple[Dict[str, Any], List[str]]:
    """Synthesise the required parameters the harvest left unbound."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return base, ["<no signature>"]
    types = {p.name: (p.type or "") for p in (entry.parameters or ())}
    missing: List[str] = []
    out = dict(base)
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if p.default is not inspect.Parameter.empty or p.name in out:
            continue
        cands = synthesize(types.get(p.name, ""))
        if not cands:
            missing.append(p.name)
            continue
        out[p.name] = cands[0]
    for k in list(out):
        if k not in sig.parameters:
            del out[k]
    return out, missing


def _verdict(cP: Any, cF: Any, cG: Any) -> str:
    if _uncomparable(cP) or _uncomparable(cF) or _uncomparable(cG):
        return "UNCOMPARABLE"
    if cP != cF:
        return "EXACT"
    if cG == cF:
        return "INSENSITIVE"
    return "DEMOTED"


def probe_param(fn, base: Dict[str, Any], opname: str,
                pname: str, ptype: str) -> Dict[str, Any]:
    """One (op, sequence-shaped parameter) row."""
    rec: Dict[str, Any] = {"op": opname, "param": pname, "type": ptype}
    # ⚠️ Cleanliness is read over the OTHER parameters ONLY. The probed one is
    # about to be REPLACED by the witness shape, so judging the binding by a
    # value that will not survive the call retires the parameter on a question
    # nobody asked: it is what made ``octonion_conjugate`` and
    # ``quaternion_conjugate`` read INEXACT_BASE while they demote.
    clean = exactify({k: v for k, v in base.items() if k != pname})[1]
    extra = [len(v) for k, v in base.items()
             if k != pname and isinstance(v, (list, tuple)) and v]
    synth = synthesize(ptype, extra)
    shapes: List[Any] = []
    harvested = pname in base and isinstance(base[pname], (list, tuple))
    # ⚠️ ORDER IS A MEASUREMENT DECISION. A harvested vector carrying a
    # NON-INTEGRAL float can only ever yield ``INEXACT_BASE`` — a float result
    # is what such a caller asked for — so trying it first would retire the
    # parameter on a binding that cannot answer the question. It is used only
    # after every int-clean synthesised shape has failed to bind.
    hv_clean = harvested and exactify(base[pname])[1]
    if hv_clean:
        shapes.append(base[pname])
    shapes.extend(synth)
    if harvested and not hv_clean:
        shapes.append(base[pname])
    if not shapes:
        rec["verdict"] = "NO_SHAPE"
        rec["reason"] = f"no shape synthesisable for declared type {ptype!r}"
        return rec

    last_err: Optional[str] = None
    saw_leafless = False
    null_seen: Optional[str] = None
    timed_out = 0
    for si, raw_shape in enumerate(shapes):
        if timed_out:
            rec["verdict"] = null_seen or "CALL_TIMED_OUT"
            rec["reason"] = (
                f"a call exceeded {CALL_TIMEOUT}s on candidate shape "
                f"{timed_out - 1}; the remaining shapes were not tried"
                if null_seen is None else
                f"a call exceeded {CALL_TIMEOUT}s; recorded the null already "
                f"reached")
            return rec
        shape, sclean = exactify(raw_shape)
        paths = list(leaf_paths(shape))[:MAX_LEAVES]
        if not paths:
            saw_leafless = True
            continue
        for path in paths:
            outs: Dict[str, Any] = {}
            failed: Optional[str] = None
            for tag, w in (("P", P), ("F", F), ("G", G)):
                kw = dict(base)
                kw[pname] = set_leaf(shape, path, w)
                ok, val = call_bounded(fn, kw)
                if not ok:
                    failed = val
                    if isinstance(val, str) and val.startswith(TIMEOUT_MARKER):
                        timed_out = si + 1
                    break
                outs[tag] = canon(val)
            if failed is not None:
                last_err = failed
                break                        # this shape does not bind; next one
            v = _verdict(outs["P"], outs["F"], outs["G"])
            if v == "INSENSITIVE":
                # SPLIT THE NULL. One coarse extra call decides whether the leaf
                # reaches the output at all, or merely not at one float64 step.
                ok, val = call_bounded(fn, {**base,
                                            pname: set_leaf(shape, path, H)})
                cH = canon(val) if ok else None
                null_seen = ("INSENSITIVE" if (not ok or cH == outs["F"])
                             else "UNRESOLVED_AT_WITNESS")
                continue                     # position-specific; try next leaf
            if v == "DEMOTED" and not (clean and sclean):
                rec["verdict"] = "INEXACT_BASE"
                rec["reason"] = ("a non-integral float survives in the binding, "
                                 "so a float result is what the caller asked for")
            else:
                rec["verdict"] = v
            rec["leaf"] = list(path)
            rec["shape"] = ("harvested" if raw_shape is base.get(pname)
                            else f"synth[{si}]")
            return rec
        if timed_out:
            continue                     # decided at the top of the next pass
    if timed_out:
        rec["verdict"] = null_seen or "CALL_TIMED_OUT"
        rec["reason"] = (
            f"a call exceeded {CALL_TIMEOUT}s on the last candidate shape"
            if null_seen is None else
            f"a call exceeded {CALL_TIMEOUT}s; recorded the null already reached")
        return rec
    if null_seen is not None:
        rec["verdict"] = null_seen
        rec["reason"] = (
            f"no witness reached the output in {MAX_LEAVES} leaves"
            if null_seen == "INSENSITIVE" else
            "the leaf reaches the output, but the op's own resolution is "
            "coarser than one float64 step at 2**53 — this witness triple "
            "cannot decide the carrier")
        return rec
    if saw_leafless and last_err is None:
        rec["verdict"] = "NO_SHAPE"
        rec["reason"] = "no numeric leaf constructible (byte / string carrier)"
        return rec
    rec["verdict"] = "RAISED"
    rec["reason"] = last_err or "no shape bound"
    return rec


def probe_op(entry, rows: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every sequence-shaped parameter of one registered op."""
    params = [p for p in (entry.parameters or ()) if sequence_shaped(p.type or "")]
    if not params:
        return []
    if entry.name in CONTRACT_SKIP:
        return [{"op": entry.name, "param": p.name, "type": p.type,
                 "verdict": "CONTRACT_SKIP", "reason": CONTRACT_SKIP[entry.name],
                 "base_source": "none", "seconds": 0.0} for p in params]
    slow = SLOW_SKIP["native" if is_native() else "pure"]
    if entry.name in slow:
        return [{"op": entry.name, "param": p.name, "type": p.type,
                 "verdict": "SLOW_SKIP", "reason": slow[entry.name],
                 "base_source": "none", "seconds": 0.0} for p in params]
    res = ea.resolve(entry.name)
    if res is None:
        return [{"op": entry.name, "param": p.name, "type": p.type,
                 "verdict": "UNRESOLVABLE", "base_source": "none",
                 "seconds": 0.0} for p in params]
    fn = res[2]
    base, _clean, src = _base_for(entry, rows)
    base, missing = _fill_required(fn, base, entry)
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        sig = None
    variadic = {p.name for p in (sig.parameters.values() if sig else ())
                if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)}
    out: List[Dict[str, Any]] = []
    for p in params:
        t0 = time.time()
        rec: Dict[str, Any]
        if p.name in variadic:
            rec = {"op": entry.name, "param": p.name, "type": p.type,
                   "verdict": "NO_SHAPE",
                   "reason": "VAR_POSITIONAL / VAR_KEYWORD: cannot be bound by "
                             "keyword, so a single-parameter witness has no slot"}
        elif missing:
            rec = {"op": entry.name, "param": p.name, "type": p.type,
                   "verdict": "NO_SHAPE",
                   "reason": f"required parameter(s) unbindable: {sorted(missing)}"}
        elif sig is not None and p.name not in sig.parameters:
            rec = {"op": entry.name, "param": p.name, "type": p.type,
                   "verdict": "NO_SHAPE",
                   "reason": "declared in the registry but absent from the "
                             "signature; nothing to bind the witness to"}
        else:
            rec = probe_param(fn, base, entry.name, p.name, p.type or "")
        rec["base_source"] = src
        rec["seconds"] = round(time.time() - t0, 3)
        if rec.get("verdict") == "DEMOTED":
            rec["declares"] = declaration_hits(fn)
        out.append(rec)
    return out


def census(rows: Optional[Dict[str, Any]] = None, *,
           progress: bool = False) -> List[Dict[str, Any]]:
    """Every sequence-shaped parameter of every registered op."""
    from srmech.introspect.tool_schema import get_tool_schema
    rows = ea.load_ledger() if rows is None else rows
    recs: List[Dict[str, Any]] = []
    tools = list(get_tool_schema().tools)
    for i, entry in enumerate(tools):
        t0 = time.time()
        got = probe_op(entry, rows)
        recs.extend(got)
        if got and progress:
            dt = time.time() - t0
            print(f"[{i + 1}/{len(tools)}] {dt:7.2f}s {entry.name} "
                  + ",".join(sorted({r["verdict"] for r in got})),
                  file=sys.stderr, flush=True)
    return recs


def by_verdict(recs: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in recs:
        out[r["verdict"]] = out.get(r["verdict"], 0) + 1
    return dict(sorted(out.items()))


def demoters(recs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """DEMOTED rows, sorted — the auto-populated manifest."""
    return sorted((r for r in recs if r["verdict"] == "DEMOTED"),
                  key=lambda r: (r["op"], r["param"]))


def undeclared(recs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """DEMOTED rows publishing NO R3 accuracy declaration — the strict-zero set."""
    return [r for r in demoters(recs) if not r.get("declares")]


def load_census(path: Optional[Path] = None
                ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """The census artefact for THIS cell, plus a loud refusal on a cell swap.

    The ``native`` meta field is compared to the live cell rather than trusted:
    a census read in the wrong cell is the exact defect this pair of files
    exists to remove, and it would otherwise present as an ordinary stale-
    artefact failure with a misleading remedy.
    """
    p = path or census_path()
    meta: Dict[str, Any] = {}
    recs: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("record") == "meta":
                meta.update(obj)
            else:
                recs.append(obj)
    if path is None and "native" in meta and meta["native"] != is_native():
        raise AssertionError(
            f"{p.name} was recorded with native={meta['native']} and this "
            f"process has native={is_native()}. That is a CELL SWAP, not a "
            f"stale artefact: regenerate the census for the cell you are in "
            f"(`PYTHONPATH=$PWD python3 tools/demotion_probe.py`) and commit "
            f"it as the file for that cell.")
    return meta, recs


def write_census(path: Optional[Path] = None) -> Dict[str, Any]:
    import srmech
    recs = census(progress=True)
    meta = {
        "record": "meta",
        "srmech_version": srmech.__version__,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "native": is_native(),
        "n_rows": len(recs),
        "n_ops": len({r["op"] for r in recs}),
        "by_verdict": by_verdict(recs),
        "witness": {"P": str(P), "F": str(F), "G": str(G)},
    }
    p = path or census_path()
    with p.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, sort_keys=True) + "\n")
        for r in sorted(recs, key=lambda r: (r["op"], r["param"])):
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return meta


if __name__ == "__main__":                                # pragma: no cover
    print(json.dumps(write_census(), indent=2, sort_keys=True))
