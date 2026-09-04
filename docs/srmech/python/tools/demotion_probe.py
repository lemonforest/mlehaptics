"""rc465 (`#T1188`) — the SILENT-CARRIER-DEMOTION probe: a DELIBERATE TOOL RUN.

``tests/test_silent_carrier_demotion_rc463.py`` is the ratchet; :func:`merge_cell`
writes ``tests/demotion_census.ndjson``, ONE committed manifest carrying BOTH CI
cells' columns. The gate READS that manifest; it does not re-derive it.

⚠️ **A CENSUS IS NOT A GATE, AND rc465 SPENT THREE COMMITS LEARNING IT**
------------------------------------------------------------------------
Through ``08d80a037`` the gate called :func:`census` — the whole
registry-wide derivation — on every CI run, in every cell, and then diffed it
against a host-specific pin. Deriving the population is expensive; checking the
invariant is not. Three consecutive commits fought the same symptom without
asking whether the derivation belonged where it was:

  * ``8be4a95ce`` — red in every PURE shard, "the artefact did not know which
    cell it came from" -> a SECOND per-cell pinned artefact.
  * ``83aa9b74f`` — ``mlse`` allocated **7.1 GiB** inside the census and killed
    the runner -> a skip.
  * ``08d80a037`` — ``windows-latest`` has no ``SIGALRM``, so its calls were
    unbounded and the job timed out at 99% -> two more skips.

Each of those is a MITIGATION: green bought by teaching a census which ops to
avoid. Worse, the expected value was per-cell, so the pin measured the HOST
rather than the code — the same defect class this project keeps finding in its
own instruments. The resolution is placement. The census is now a tool run a
human starts on purpose; the gate reads a committed file and checks a predicate
in milliseconds, identically in every cell. **MEASURED: the gate cost
66.18 s (native) / 153.80 s (pure) per CI job and now costs 8.02 s / 7.21 s, of
which every test call is <= 0.04 s and the rest is ``import srmech``. In the
``--forked`` asserts-live cell it was paid ONCE PER TEST — ``pytest-forked``
gives each test a fresh child, so the module cache never survived and 15
census-consuming tests each re-derived it: ~15 minutes of census, observed as
+12 m of wall clock on ``asserts-live shard 4/4`` against the ``main``
baseline.**

The two per-cell artefacts consolidate to one. The native-vs-pure disagreement
does NOT disappear by being merged: it becomes a **named finding with its op
list** (``divergent`` rows, and ``meta.divergent`` naming every one), pinned in
the gate. An op whose answer depends on whether ``libsrmech`` loaded is the
``fir`` / ``matched_filter`` class rc463 already rated WORSE than a plain
demotion. Surfacing it is the resolution; absorbing it into two pins was the
mitigation.

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
    ``CEIL_DEMOTION_UNREACHED`` ratchets down —
    ``tests/test_silent_carrier_demotion_rc463.py``, where that constant is
    DEFINED and ASSERTED, over BOTH cells' columns in every cell. It was not,
    through rc465: this sentence named a ratchet that existed nowhere else in
    the repo, so the instrument's own reach was the one number in this file
    with no gate under it (`#T1188`). The larger unreached class is ``RAISED``
    — a real refusal by a real op against a synthesised binding — and it is
    deliberately left unratcheted, because driving it down is a question about
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
 6. **THE MANIFEST GOES STALE SILENTLY, and only one HALF of that is guarded.**
    The gate no longer re-derives the census, so nothing re-measures the tree
    on its own. :func:`registry_signature` is the cheap half: hashing
    ``(op name, parameter types, return type)`` over the whole registry costs
    milliseconds and moves whenever an op is ADDED, REMOVED or RE-SIGNATURED,
    which is what decides demotion-CANDIDACY. **It does NOT move when an
    implementation changes carrier behaviour behind an unchanged signature** —
    the very class this probe exists to find. That is stated here and again in
    the gate, because the tree has already paid for the identical blind spot
    once: ``tools/run_worked_examples.py``'s ``--only-stale`` keys on the
    snippet-TEXT hash, which does not move when the implementation moves, "and
    that blind spot is exactly how the ℚ-flip defect shipped". A guard whose
    limit is unwritten is a guard people believe.
 7. **Byte / bit carriers admit no witness.** They surface as ``NO_SHAPE`` with
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


def cell() -> str:
    """``"native"`` or ``"pure"`` — which CI cell this process is."""
    return "native" if is_native() else "pure"


#: The two column names the manifest carries, in report order.
CELLS = ("native", "pure")

#: **THE** manifest. One file, both columns, host-independent to read.
#:
#: ⚠️ There were TWO through ``08d80a037`` — ``demotion_census_rc465.ndjson``
#: and ``..._pure.ndjson`` — because the gate re-derived the census live and
#: had to compare it against something taken in the same cell. That is the
#: mitigation this rc removes: with the derivation out of CI there is nothing
#: to compare per-cell, so the disagreement between the cells becomes DATA in
#: one file instead of a second pin.
CENSUS = PY_ROOT / "tests" / "demotion_census.ndjson"

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

#: Per-call wall-clock cutoff, seconds — a HANG GUARD for the instrument, not
#: a verdict-shaping cutoff. A call that exceeds it is recorded
#: ``CALL_TIMED_OUT`` with the number, never silently dropped.
#:
#: ⚠️ **20 through ``08d80a037``, and at 20 it DECIDED verdicts.** Two rows
#: measured 20.0-22.2 s straddling it and flipped between consecutive censuses
#: on an unchanged tree — a verdict that is a function of the MACHINE. The
#: repair shipped then was to skip both ops (see :data:`CONTRACT_SKIP`, where
#: they now sit for a reason about the OP), and to skip four more in the pure
#: cell whose only fault was costing 53-526 s there against 0.15 s in native.
#: All of that existed because the census ran inside CI, where a slow row is a
#: job that dies and ``windows-latest`` cannot enforce a ``SIGALRM`` cutoff at
#: all.
#:
#: With the census OUT of CI that argument dissolves. A deliberate tool run may
#: take as long as the tree takes, so the cutoff is set clear of every call that
#: can still reach it instead of through the middle of two. MEASURED, slowest
#: rows now that the two label-operand ops are contract-skipped (a row is 3-4
#: calls):
#:
#:     pure    ``recover_check_spectral::edges``        526.5 s
#:             ``recover_check_spectral::weights``       59.1 s
#:             ``recover_check::weights``                53.1 s
#:     native  the same three                        0.15-6.7 s
#:
#: Those four rows are now MEASURED rather than skipped, in both cells, and the
#: ~13 extra minutes are paid by whoever chose to run the instrument. 900 s
#: against a 592 s worst row bounds a HANG and adjudicates nothing.
#:
#: REPRODUCIBILITY, measured rather than argued: a second independent pure pass
#: over exactly those five rows differed from the committed column in **0**
#: verdicts, while their wall clocks moved by up to 27% (157.6 -> 200.0 s on
#: ``recover_check_spectral::weights``). At 20 s the cutoff sat INSIDE that
#: spread and adjudicated; at 900 s it does not.
#:
#: It is still needed: ``tensor_product_multiplicities`` hung indefinitely in
#: the first census run, and a probe that can hang has no honest verdict to
#: publish. ``signal.SIGALRM`` fires between BYTECODES and does not exist on
#: Windows — neither fact bounds anything the tree depends on any more, because
#: this is a tool a human runs and can interrupt, not a job with a timeout.
CALL_TIMEOUT = 900

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
    # ⚠️ rc465-fix (`#T1188`) — TWO ROWS THAT ``08d80a037`` PUT IN ``SLOW_SKIP``
    # FOR A WINDOWS-TIMEOUT REASON, AND THAT BELONG HERE FOR THE OP'S OWN.
    #
    # That commit skipped them because a 20 s cutoff `windows-latest` cannot
    # enforce is not a cutoff — true, and about the MACHINE. The question this
    # rc asks of every skip is whether the reason survives the census leaving
    # CI. MEASURED (WSL2 py3.10, native), scanning the operand rather than
    # asserting about it:
    #
    #   alcove_fold("A1", [w], level=1)          w = 1 .. 4096   0.00 s
    #                                            w = 2**20       1.06 s
    #                                            w = 2**30       NO ANSWER >30 s
    #                                            w = 2**53+1     NO ANSWER >60 s
    #   equal_temperament_partials(degrees=[d])  d = 1 .. 4096   0.00 s
    #                                            d = 2**20       ValueError:
    #                                              "Exceeds the limit (4300) for
    #                                               integer string conversion"
    #                                            d = 2**53+1     NO ANSWER >60 s
    #
    # Both costs are LINEAR IN THE OPERAND'S VALUE, because in both ops the
    # operand is an INDEX and not a value carrier. `weight` is documented "a
    # rank-length DYNKIN LABEL", and the affine Weyl fold takes one reflection
    # step per unit of the label, so a 2**53 coordinate asks for ~2**53 steps —
    # the identical unbounded-orbit fact the three weight-lattice rows below
    # already record, and those predate the CI panic entirely. `degrees` is
    # documented "which SCALE DEGREES to return", and the exact ratio is
    # `octave**(degree/divisions)`, so degree 2**20 already exceeds CPython's
    # 4300-digit integer conversion limit; at 2**53 the number has ~10**15 bits.
    #
    # Neither is "the same question at a bigger magnitude", which is the test
    # the mlse note below states. That reason holds on any machine, so these
    # stay skipped and the WINDOWS reason is retired as the wrong one.
    "srmech.math.weight_lattice.alcove_fold":
        "a Dynkin LABEL, not a value carrier: the affine Weyl fold takes one "
        "reflection step per unit of the coordinate, so cost is LINEAR IN THE "
        "OPERAND VALUE. MEASURED 0.00s at 4096, 1.06s at 2**20, no answer in "
        "30s at 2**30. frame_probe.SLOW_SKIP names this family too",
    "srmech.music.equal_temperament_partials":
        "a scale-degree INDEX, not a value carrier: the exact ratio is "
        "octave**(degree/divisions), so the operand sizes the NUMBER rather "
        "than the question. MEASURED, degree 2**20 already raises \"Exceeds "
        "the limit (4300) for integer string conversion\"; at 2**53 the value "
        "has ~10**15 bits",
    # ⚠️ **THE ONE SKIP THAT SURVIVED THE rc465 CENSUS-PLACEMENT FIX, and it
    # survives on its own merits rather than on CI's** (`#T1188`).
    #
    # It ARRIVED as a mitigation — `83aa9b74f`, "one op allocated 7.1 GiB
    # inside the census and killed the CI runner" — and every other skip added
    # in that panic is deleted, because "the census is expensive in CI" stopped
    # being a reason the moment the census left CI. This one is kept, and the
    # test is whether the reason is about the OP or about the MACHINE:
    #
    #   `mlse`'s `n_states` means `A**L` (the rc425 v14 ABI bump), so the
    #   Viterbi trellis is EXPONENTIAL in the operand. Substituting `2**53`
    #   into `alphabet` / `channel_taps` / `initial_state` / `observations`
    #   does not ask the same question at a bigger magnitude — it asks for a
    #   trellis the op cannot build, exactly as a `2**53` Dynkin coordinate
    #   asks for an unbounded Weyl orbit in the three weight-lattice rows
    #   above, which predate the CI panic entirely. The witness is not a value
    #   carrier here.
    #
    # That reason holds on a workstation with 128 GiB as squarely as on a
    # 7 GiB runner, so it stays. It is recorded AS DATA — a `CONTRACT_SKIP`
    # verdict with this reason attached in every manifest row — not as a
    # silence. MEASURED per-op peak-RSS profile over the whole census (WSL2
    # py3.10): +7256.8 MiB for `mlse` against +17.4 MiB for the next largest
    # op, `singular_values_exact`.
    "srmech.signal_processing.mlse":
        "n_states is A**L, so the trellis is EXPONENTIAL in the operand: a "
        "2**53 witness asks for a state space the op cannot build, not the "
        "same question at a bigger magnitude. MEASURED +7.1 GiB peak RSS, "
        "against +17.4 MiB for the next largest op in the census",
}

# ⚠️ **THERE IS NO ``SLOW_SKIP`` HERE, AND ITS DELETION IS THE POINT**
# (`#T1188`). ``08d80a037`` shipped one — a per-cell roster of ops the census
# was told to avoid — holding ``alcove_fold`` and ``equal_temperament_partials``
# in BOTH cells (20.0-22.2 s rows against a 20 s cutoff that ``windows-latest``
# cannot enforce at all) and ``recover_check`` / ``recover_check_spectral`` in
# the pure cell (53-526 s rows whose verdicts were measured FLIPPING between
# consecutive censuses). Both rosters existed for one reason: the census was
# being re-derived inside CI, where a slow row is a job that dies.
#
# A deliberate tool run has no such constraint, so each of the six was re-asked
# the only question that matters — is the reason about the OP or about the
# MACHINE? The four ``recover_check`` rows are about the machine: they ANSWER,
# they just cost 53-526 s on the pure path against 0.15 s in native, so they are
# MEASURED now in both cells, ``CALL_TIMEOUT`` is set clear of them, and the
# ~11 extra minutes are paid by whoever chose to run the instrument. The other
# two are about the op — ``alcove_fold`` and ``equal_temperament_partials`` take
# an INDEX where the probe substitutes a VALUE, measured linear in the operand
# — so they move to :data:`CONTRACT_SKIP` and are recorded there with the scan
# that shows it. That is where a genuinely unadjudicable row belongs, next to
# ``mlse`` and the three weight-lattice rows. A roster keyed by how fast the
# machine is measures the machine.


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


def by_verdict(recs: Sequence[Dict[str, Any]], cel: str = "") -> Dict[str, int]:
    """Verdict histogram. ``cel`` selects a MANIFEST column; "" reads a flat
    cell census (what :func:`census` returns)."""
    out: Dict[str, int] = {}
    for r in recs:
        col = r.get(cel) if cel else r
        if col:
            out[col["verdict"]] = out.get(col["verdict"], 0) + 1
    return dict(sorted(out.items()))


def key(row: Dict[str, Any]) -> str:
    """``op::param`` — the row identity, in every consumer."""
    return f"{row['op']}::{row['param']}"


# -- the REGISTRY SIGNATURE: the whole staleness guard -------------------------
def registry_signature_lines() -> List[str]:
    """``name|pname:ptype,...|returntype`` for every registered op, sorted.

    The triple is chosen because it is exactly what decides DEMOTION-CANDIDACY:
    :func:`probe_op` selects parameters by their REGISTRY type, builds a binding
    from the signature, and files the answer under the return carrier. An op
    added, removed or re-signatured moves this string; nothing else about the
    tree does — and that limit is the guard's declared blind spot, written out
    in ``tests/test_silent_carrier_demotion_rc463.py`` rather than left implied.
    """
    from srmech.introspect.tool_schema import get_tool_schema
    out: List[str] = []
    for e in get_tool_schema().tools:
        params = ",".join(f"{q.name}:{q.type or ''}"
                          for q in (e.parameters or ()))
        rt = getattr(getattr(e, "returns", None), "type", "") or ""
        out.append(f"{e.name}|{params}|{rt}")
    return sorted(out)


def registry_signature() -> str:
    """sha256 over the NORMALISED signature lines.

    Normalised (newline-joined with a trailing newline, UTF-8) rather than raw
    file bytes, for the reason ``tests/test_op_name_set_witness_rc361.py`` gives
    about its own manifest: a CRLF checkout must not make the digest disagree
    between the Windows and Linux CI cells, or a platform artifact wears a
    rename's clothes.

    Routed through ``srmech.amsc.format.sha256_bytes`` — never a direct
    ``hashlib`` call — so native dispatch picks it up transparently.
    """
    from srmech.amsc.format import sha256_bytes
    body = ("\n".join(registry_signature_lines()) + "\n").encode("utf-8")
    return sha256_bytes(body)


# -- manifest readers ---------------------------------------------------------
def demoters(recs: Sequence[Dict[str, Any]], cel: str = ""
             ) -> List[Dict[str, Any]]:
    """DEMOTED rows, sorted. ``cel`` selects a MANIFEST column; "" reads flat."""
    def v(r):
        return (r.get(cel) or {}).get("verdict") if cel else r.get("verdict")
    return sorted((r for r in recs if v(r) == "DEMOTED"),
                  key=lambda r: (r["op"], r["param"]))


def undeclared(recs: Sequence[Dict[str, Any]], cel: str = ""
               ) -> List[Dict[str, Any]]:
    """DEMOTED rows publishing NO R3 accuracy declaration — the strict-zero set."""
    return [r for r in demoters(recs, cel)
            if not ((r.get(cel) or {}) if cel else r).get("declares")]


def undeclared_keys(recs: Sequence[Dict[str, Any]], cel: str) -> List[str]:
    return sorted(key(r) for r in undeclared(recs, cel))


def divergent(recs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """THE NAMED FINDING: rows whose verdict depends on whether `libsrmech` loaded.

    rc463 already rates this class WORSE than a plain demotion — an op whose
    ANSWER is decided by which projection happens to be dispatching is not
    merely inexact, it is two ops wearing one name. Through ``08d80a037`` the
    disagreement was ABSORBED into two per-cell pinned artefacts, which is
    exactly how it stopped being visible. Here it is a first-class row property
    and every member is named in ``meta.divergent``.
    """
    out = []
    for r in recs:
        n, u = r.get("native"), r.get("pure")
        if n and u and n["verdict"] != u["verdict"]:
            out.append(r)
    return sorted(out, key=lambda r: (r["op"], r["param"]))


def load_manifest(path: Optional[Path] = None
                  ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """``(meta, rows)`` from the ONE committed manifest.

    There is no cell-swap check here and nothing to stale-check against a live
    run: this file is read identically in every CI cell, which is the whole
    reason it replaced the two per-cell artefacts.
    """
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


# -- the tool run -------------------------------------------------------------
#: Row fields that belong to the (op, parameter) itself rather than to a cell.
_SHARED = ("op", "param", "type", "base_source")
#: Per-cell fields. ``seconds`` is DELIBERATELY not among them: it is a property
#: of the HOST, and a committed artefact carrying it would churn on every
#: regeneration and make any digest over the file host-dependent — the defect
#: this rc removed at the level of the whole artefact. The tool PRINTS the
#: slowest rows instead, which is where that number is actually useful.
_CELL_FIELDS = ("verdict", "reason", "leaf", "shape", "declares")


def merge_cell(path: Optional[Path] = None, *, progress: bool = True
               ) -> Dict[str, Any]:
    """Measure THIS cell and merge its column into the committed manifest.

    The other cell's column is carried forward UNTOUCHED — which is the rc460
    worked-example-ledger defect (its own CHANGELOG entry: ``--only-stale``
    "stamps the CURRENT cell's ``native`` flag onto rows merged from another
    cell") repaired rather than repeated: nothing here relabels a measurement it
    did not take.

    ⚠️ It REFUSES to carry forward a column measured against a DIFFERENT
    registry signature. Two halves of one manifest measured on two different
    trees is a file that is internally consistent and jointly false, and the
    gate reading it could not tell.
    """
    import srmech
    p = path or CENSUS
    me = cell()
    sig = registry_signature()

    prev_meta: Dict[str, Any] = {}
    prev_rows: Dict[str, Dict[str, Any]] = {}
    if p.exists():
        prev_meta, prv = load_manifest(p)
        prev_rows = {key(r): r for r in prv}
    other = [c for c in CELLS if c != me][0]
    prev_sigs = dict(prev_meta.get("registry_signature_sha256") or {})
    if other in prev_sigs and prev_sigs[other] != sig:
        raise SystemExit(
            f"REFUSING to merge: the committed {other!r} column was measured "
            f"against registry signature {prev_sigs[other][:12]} and this tree "
            f"is {sig[:12]}. Re-measure {other!r} on THIS tree "
            f"(`PYTHONPATH=$PWD python3 tools/demotion_probe.py` in that cell) "
            f"or delete {p.name} and measure both.")

    t0 = time.time()
    recs = census(progress=progress)
    elapsed = round(time.time() - t0, 1)

    merged: Dict[str, Dict[str, Any]] = {}
    for r in recs:
        k = key(r)
        row = dict(prev_rows.get(k) or {})
        for f in _SHARED:
            if r.get(f) is not None:
                row[f] = r[f]
        row[me] = {f: r[f] for f in _CELL_FIELDS if r.get(f) is not None}
        merged[k] = row
    # Rows the OTHER cell measured that this one no longer reaches at all are
    # KEPT with this cell's column dropped, so a shrinking reach is visible as a
    # half-populated row rather than as a silent deletion.
    for k, row in prev_rows.items():
        if k not in merged:
            keep = dict(row)
            keep.pop(me, None)
            if keep.get(other):
                merged[k] = keep

    rows = [merged[k] for k in sorted(merged)]
    for r in rows:
        n, u = r.get("native"), r.get("pure")
        if n and u and n["verdict"] != u["verdict"]:
            r["divergent"] = True
        else:
            r.pop("divergent", None)

    sigs = dict(prev_sigs)
    sigs[me] = sig
    measured = dict(prev_meta.get("measured_at") or {})
    # ⚠️ NO WALL CLOCK HERE. `census_seconds` was in this dict until it was
    # MEASURED: a native re-run on an unchanged tree reproduced all 703 rows
    # byte-identically and differed in exactly one field, this one (74.2 ->
    # 66.6). A committed artefact carrying the host's clock can never diff
    # empty on a no-op re-measurement, which destroys the one signal a
    # maintainer actually reads off `git diff` — and it is the same
    # host-dependence this rc removed from the ROWS, left behind in the meta.
    # The elapsed time is PRINTED below, which is where a human wanting it
    # looks; nothing reads it back.
    measured[me] = {
        "srmech_version": srmech.__version__,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
    }
    cells_present = [c for c in CELLS if any(r.get(c) for r in rows)]
    meta = {
        "record": "meta",
        "cells_measured": cells_present,
        "registry_signature_sha256": sigs,
        "measured_at": measured,
        "n_rows": len(rows),
        "n_ops": len({r["op"] for r in rows}),
        "by_verdict": {c: by_verdict(rows, c) for c in cells_present},
        "undeclared": {c: undeclared_keys(rows, c) for c in cells_present},
        "divergent": [f"{key(r)} native={r['native']['verdict']} "
                      f"pure={r['pure']['verdict']}" for r in divergent(rows)],
        "witness": {"P": str(P), "F": str(F), "G": str(G)},
    }
    with p.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, sort_keys=True) + "\n")
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    slow = sorted(((r.get("seconds") or 0.0), key(r)) for r in recs)[-8:]
    print(f"\n[{me}] census {elapsed}s over {len(recs)} rows; manifest now "
          f"{len(rows)} rows / {meta['n_ops']} ops; "
          f"cells {meta['cells_measured']}", file=sys.stderr)
    print("slowest rows this cell:", file=sys.stderr)
    for sec, k in reversed(slow):
        print(f"  {sec:8.1f}s  {k}", file=sys.stderr)
    if meta["divergent"]:
        print(f"NATIVE-vs-PURE DIVERGENCE ({len(meta['divergent'])} rows):",
              file=sys.stderr)
        for d in meta["divergent"]:
            print(f"  {d}", file=sys.stderr)
    return meta


if __name__ == "__main__":                                # pragma: no cover
    m = merge_cell()
    print(json.dumps({k: v for k, v in m.items() if k != "undeclared"},
                     indent=2, sort_keys=True))
