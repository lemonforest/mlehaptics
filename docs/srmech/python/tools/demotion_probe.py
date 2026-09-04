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
    ``CEIL_DEMOTION_UNREACHED`` ratchets down.
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

#: Per-(op, parameter) wall-clock budget, seconds. Once a row has spent this
#: much, the remaining candidate SHAPES are abandoned and the row is recorded
#: ``BUDGET_EXHAUSTED`` with the seconds attached — a named residual class, not
#: a silent skip and not a verdict about the op.
#:
#: The number is a RECORDED DECISION, the discipline ``frame_probe.SLOW_SKIP``
#: already applies: a bare wall-clock cutoff makes a verdict depend on the
#: machine, so an op could be adjudicated on a fast runner and unadjudicated on
#: a slow one, silently changing what the ratchet requires. Here the budget
#: bounds only how many SHAPES are tried, never whether a reached verdict is
#: believed — a row that answers on shape 0 is unaffected by it.
PARAM_BUDGET = 6.0

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
    started = time.time()
    for si, raw_shape in enumerate(shapes):
        if time.time() - started > PARAM_BUDGET:
            rec["verdict"] = null_seen or "BUDGET_EXHAUSTED"
            rec["reason"] = (
                f"{PARAM_BUDGET}s budget spent over {si} candidate shapes; "
                f"the remaining shapes were not tried"
                if null_seen is None else
                f"{PARAM_BUDGET}s budget spent; recorded the null already reached")
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
    p = path or CENSUS
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
    return meta, recs


def write_census(path: Optional[Path] = None) -> Dict[str, Any]:
    import srmech
    recs = census(progress=True)
    meta = {
        "record": "meta",
        "srmech_version": srmech.__version__,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "n_rows": len(recs),
        "n_ops": len({r["op"] for r in recs}),
        "by_verdict": by_verdict(recs),
        "witness": {"P": str(P), "F": str(F), "G": str(G)},
    }
    p = path or CENSUS
    with p.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, sort_keys=True) + "\n")
        for r in sorted(recs, key=lambda r: (r["op"], r["param"])):
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return meta


if __name__ == "__main__":                                # pragma: no cover
    print(json.dumps(write_census(), indent=2, sort_keys=True))
