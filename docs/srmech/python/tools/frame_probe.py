"""rc430 (`#T1127`) — the FRAME instrument: is an op's frame an INPUT or WELDED IN?

ONE INSTRUMENT, TWO CONSUMERS. ``tests/test_frame_scope_rc430.py`` is the
ratchet; ``tools/frame_scope_census.py`` is the census that writes the NDJSON.
They import the same functions, so the shipped declaration and the published
measurement cannot drift apart by being separately hand-rolled — which is the
failure mode a test that re-implements its own subject always eventually has.

⚠️ AND THAT IS NOT ENOUGH, measured at rc465 (`#T1188`). A shared import
guarantees agreement WHEN BOTH RUN. The census file was last regenerated at
rc430 and sat at ``NO_INT_INPUT: 152`` while the gate's ceiling for that one
class was raised NINE times to 184 — every raise justified from an ad-hoc
per-op probe recorded in a comment, none from a published measurement. The
artefact now lives at ``tests/frame_scope_census.ndjson`` and the gate compares
its ``meta.by_verdict`` to the live census in the same process, so a stale
census is a red test rather than a quiet document.

WHAT IS BEING MEASURED
----------------------
An op that reduces modulo something works in a FRAME. The question is not
"what is the frame" but "is it an INPUT, or welded into the op", because a
consumer composing two ops needs to know whether it may choose.

    parametric   sweeping some parameter MOVES the output; the output is
                 invariant under translating a frame-carrying input by THAT
                 parameter's value; and no single constant period survives
                 the sweep.
    fixed        there is a least constant m > 1 with f(x + m) == f(x) for
                 every x in the swept range, no parameter carries m, and the
                 op is NOT constant along that coordinate.

VERDICTS ARE SWEPT, NEVER SAMPLED — AND THAT IS NOT A STYLE POINT
-----------------------------------------------------------------
The first draft of this instrument sampled six offsets and classified
``srmech.math.primes.is_prime`` as ``fixed`` with **period 6**. is_prime is
not periodic; six draws happened to agree. Had that shipped, a gate would have
been protecting a false declaration on a real op — the precise defect this
whole rc exists to prevent, reproduced by the instrument built to prevent it.

The repair is structural rather than a bigger sample: build the whole value
SEQUENCE over a dense contiguous range and require a candidate period to hold
across EVERY residue in it, with a floor on how many pairs actually witnessed
it. At ``R=72`` and ``m<=36`` that is at least 36 independent confirmations.
``least_period`` re-derives ``is_prime -> None`` as a precondition, and
``tests/test_frame_scope_rc430.py`` asserts it.

THE ROSTER IS DERIVED BEHAVIOURALLY, NEVER FROM NAMES
-----------------------------------------------------
Measured at rc430: 67 ops take an int parameter from the modulus name-family
and MOST ARE NOT FRAMES — ``is_prime(n)``, ``factor(n)``,
``dense_laplacian(n=|V|)``, ``cooccurrence_edges(window)``. A name-derived
roster would force a false declaration on roughly 58 ops. Names are used
nowhere in this module.

No ``abs()`` anywhere: a sign is a Class-K pin-slot read composed with Class C.
No float, no numpy, no ``fractions``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import example_args as ea  # noqa: E402

#: Dense frame-coordinate range. Every candidate period is checked at every
#: residue in ``0..R-1``, not at a sample of them.
R = 72

#: Largest constant period considered. Bounded so ``R - MMAX`` still leaves a
#: real confirmation count; see :data:`MIN_CONFIRMATIONS`.
MMAX = 36

#: A period fewer than this many (d, d+m) pairs witnessed is not a
#: measurement. This is the floor that kills the `is_prime` artefact.
MIN_CONFIRMATIONS = 24

#: Length of the cheap rejection prefix. A candidate period that fails here
#: cannot hold on the full range, so screening removes RUNTIME, never
#: verdicts — which is why the screen is allowed to be short.
SCREEN = 24
SCREEN_MIN_CONF = 6
SCREEN_TAIL = 8

#: The modulus sweep. Five distinct values: two primes (5, 7, 11), a composite
#: with a repeated factor (9), and a highly-composite one (12) — so an op that
#: is periodic only for prime moduli, or only for even ones, cannot pass by
#: accident. 12 is included deliberately because it is the ONE modulus a
#: hard-wired music op would also satisfy, which is what forces the
#: "no constant period survives the sweep" clause to do real work.
NS = (5, 7, 9, 11, 12)


#: MEASURED-SLOW ops, skipped by NAME with a number attached.
#:
#: "Slow" is a RECORDED DECISION here, never a silently raised global timeout —
#: the discipline ``tools/run_worked_examples.py`` already applies with its own
#: ``SLOW_ALLOWLIST``, and for the same reason: a wall-clock cutoff makes a
#: verdict depend on the machine, so an op could be adjudicated on a fast
#: runner and unadjudicated on a slow one, silently changing what the ratchet
#: requires. A named list cannot do that.
#:
#: Every number below was measured by the rc430 census profile. The dense
#: 72-point sweep multiplies the per-call cost, and these ops are expensive per
#: CALL rather than call-hungry — ``recover_check`` took **1332 s in 50 calls**.
#: All of them classify NOT_ADMISSIBLE anyway (dense-matrix ops with no frame
#: coordinate to translate), so skipping costs no verdict; it is recorded as
#: its own residual class rather than folded into a passing one.
#: Ops whose parameter carries a DOCUMENTED domain contract the translation
#: sweep cannot honour. Skipped by name with the contract quoted, and counted as
#: its own residual class — never folded into a passing one.
#:
#: rc430 shipped without this and CI aborted (`#T1127`). `gf_rref` documents
#: "a prime with 2 <= p < 2**31 … primality is the caller's contract", and the
#: sweep drives `p` over NS = (5, 7, 9, 11, 12) — 9 and 12 are composite — plus
#: the whole translation walk. `_check_field` enforces the RANGE, not primality,
#: exactly as documented, so the pure body just computes a wrong answer quietly;
#: but the native peer `assert()`s it, and under the asserts-live CI job the
#: process took SIGABRT. Every one of the 20 parametrized ratchet cases then
#: reported CRASHED, because they share one cached census — the abort happened
#: inside the first call, on an op that is not in the roster at all.
#:
#: This is the INSTRUMENT violating a contract the op states plainly, not a
#: defect in the op. The general repair is the per-parameter domain field
#: deferred to rc431 (`docs/srmech/notes/rc430_deferral_T1127_param_domain.md`);
#: until it exists there is nothing for the probe to read, so the three ops
#: carrying this contract are named here.
CONTRACT_SKIP: Dict[str, str] = {
    "srmech.math.modular_linalg.gf_rref":
        "p must be PRIME (2 <= p < 2**31); the sweep drives composite p and the "
        "native peer asserts — SIGABRT under the asserts-live CI job",
    "srmech.math.modular_linalg.gf_solve":
        "p must be PRIME (2 <= p < 2**31); same contract as gf_rref",
    "srmech.math.modular_linalg.gf_nullspace":
        "p must be PRIME (2 <= p < 2**31); same contract as gf_rref",
}

SLOW_SKIP: Dict[str, str] = {
    "srmech.math.laplacian.recover_check": "1332 s measured (50 calls) — dense recover",
    "srmech.math.laplacian.recover_check_spectral": "dense recover (rwe: 244 s)",
    "srmech.math.laplacian.recover_check_structural": "dense recover (rwe: 33 s)",
    "srmech.math.laplacian.three_fold_eigvec_groups": "dense eigvec pass",
    "srmech.math.laplacian.ground_state_flux_response": "60.5 s measured (25 calls)",
    "srmech.math.laplacian.propagate_sparse": "11.0 s measured (27 calls)",
    "srmech.math.laplacian.klein4_relational_structure": "8.5 s measured (30 calls)",
    "srmech.math.hdc.cooccurrence_fold": "18.8 s measured (119 calls)",
    "srmech.introspect.search.search": "21.3 s measured (25 calls) — corpus build",
    "srmech.music.membrane_partials": "18.3 s measured (138 calls) — Bessel zeros",
    "srmech.math.laplacian.spectral_spine": "10.9 s measured (25 calls)",
    "srmech.math.laplacian.recursive_cut": "5.3 s measured (177 calls)",
    "srmech.physics.qm.so8.an_embedding": "g2 = Der(O) branching (rwe: 22.5 s)",
    "srmech.physics.qm.so8.so7_subalgebra": "so(7) branching (rwe: 31.3 s)",
    # is_prime's harvested argument is a Mersenne prime and the pure path is
    # trial division (rwe: 206 s). It is skipped as a CENSUS subject and is
    # still driven as the §0 precondition control on small inputs, where it is
    # microseconds — the two uses are separate and only one is expensive.
    "srmech.math.primes.is_prime": "Mersenne M61 on the pure trial-division path"
                                   " (rwe: 206 s)",
    # rc461 part 3 (`#T1183`). BOTH are the an_embedding / so7_subalgebra
    # class: real ops whose harvested base is D4, where the `level` sweep
    # drives an object that grows quartically. |P_k| for D4 is 4 at level 1,
    # 11 at level 2, 11011 at level 24 and 658711 at level 72, and the
    # Kac-Peterson sum is |P_k|^2 x |W| = |P_k|^2 x 192 terms in Z[zeta_e].
    # MEASURED with the real Driver at SCREEN=24: the s_matrix screen passed
    # 90 s at call SIX (levels 1-6) and the verlinde screen at call TEN; both
    # were still climbing. Their three siblings needed NO entry --
    # integrable_weights screens in 0.25 s, alcove_fold in 0.00 s and
    # affine_fusion_multiplicities in 0.02 s -- which is what shows this is
    # about the Weyl-sum cost and not about the family being unprobeable.
    # DRAINABLE, and recorded as such rather than left implicit: the base
    # args come from the FIRST returning call in the worked example, so
    # leading those examples with A1 instead of D4 would make the sweep
    # cheap and retire both entries. That is not done here because the D4
    # transcript IS the acceptance test -- it is the equality against
    # character_table of the centre -- and demoting it to satisfy a probe
    # would weaken the shipped documentation to move a census number.
    "srmech.math.weight_lattice.affine_modular_s_matrix":
        "D4 Kac-Peterson Weyl sum; the level sweep is |P_k|^2 x 192 terms"
        " and |P_k| is quartic in level (>90 s measured at 6 calls)",
    "srmech.math.weight_lattice.verlinde_fusion_multiplicities":
        "builds the same D4 S-matrix and then contracts over every"
        " primary (>90 s measured at 10 calls)",
    # rc465 (`#T1188`). THE ONE UPWARD MOVE IN THIS RC, and it is a
    # CONSEQUENCE of the nested-leaf widening rather than a concession: both
    # ops were previously NO_INT_INPUT — unreachable, uncounted as slow because
    # they were never driven at all — and become reachable the moment a
    # matrix-shaped operand counts as a coordinate. Each carries the number the
    # skip is FOR, and each carries the verdict it reaches when it IS driven,
    # so this class is not hiding an admissible op behind a wall clock:
    #   g2_membership        -> NOT_ADMISSIBLE in  50.9 s (MEASURED, full
    #                           classify(); one base call is 48.7 s and the
    #                           perturbed matrix is non-orthogonal, so its own
    #                           guard raises at d=1 and the sequence is
    #                           not-total).
    #   relational_structure -> NOT_ADMISSIBLE in 258.7 s (MEASURED, full
    #                           classify(); ~10 s per call over the screen).
    # DRAINABLE the same way every other entry here is: a smaller base object in
    # the worked example. Not done in rc465 because the shipped examples are the
    # acceptance transcripts for these ops.
    "srmech.physics.qm.so8.g2_membership":
        "8x8 exact-orthogonal G2 membership; 48.7 s per call, 50.9 s for the"
        " whole classify() (rc465 measured; reaches NOT_ADMISSIBLE)",
    "srmech.math.laplacian.relational_structure":
        "dense relational structure over the harvested edge matrix; ~10 s per"
        " call, 258.7 s for the whole classify() (rc465 measured; reaches"
        " NOT_ADMISSIBLE)",
}


def is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def is_int_seq(v: Any) -> bool:
    return isinstance(v, list) and len(v) > 0 and all(is_int(x) for x in v)


def is_nested_int_seq(v: Any) -> bool:
    """A RECTANGULAR list of non-empty int rows — a matrix-shaped operand."""
    return (isinstance(v, list) and len(v) > 0
            and all(is_int_seq(row) for row in v))


def is_frame_coordinate(v: Any) -> bool:
    """A value that can be TRANSLATED along a frame axis.

    rc465 (`#T1188`) admits ONE more nesting level, and the reason is that the
    depth cut was never a semantic boundary. Through rc464 this stopped at a
    FLAT int sequence, and the standing justification for stopping there was
    that "a matrix is an OPERATOR, not a coordinate — perturbing an entry asks
    a different question". That is a per-op SEMANTIC claim being asserted from
    a nesting-DEPTH test, and the same objection applies one level up: element
    ``[0]`` of a flat int vector is content just as often (``zeta_mul`` takes
    ``Z[zeta]`` COEFFICIENTS and rc458 drove it to NOT_ADMISSIBLE in 73 calls;
    ``interval_vector`` takes pitch classes and is translated BY DESIGN). The
    probe already perturbs those and reports the honest answer. Refusing to
    perturb ``[0][0]`` was a wall at depth 2, not a rule.

    And within one shape the semantics differ anyway: ``list[list[int]]`` is a
    Cayley table (element LABELS) in ``conjugacy_classes``, literal geometric
    COORDINATES in ``cotangent_weights(positions)``, vertex labels in
    ``edges``, an operator over Q in ``qmat_*``, and an array of RESIDUES MOD p
    in ``gf_rref(rows, p)``. The shape cannot decide which; only the measurement
    can, and the measurement was being refused.

    MEASURED at rc465 over the 26 ops this widening makes reachable: 24 drive
    to a verdict in under 0.2 s each and **every one is NOT_ADMISSIBLE** — zero
    false ``ADMISSIBLE``, so the feared "asking a different question under this
    name" produced no frame declarations at all. The two that are expensive are
    named in :data:`SLOW_SKIP` with their measured seconds. Ops whose own guard
    rejects the perturbed matrix (a Cayley table, an orthogonal ``g``) go
    not-total and ``sequence`` returns ``None``, which is the correct verdict
    for a group op rather than a corruption of it.
    """
    return is_int(v) or is_int_seq(v) or is_nested_int_seq(v)


def translate(v: Any, d: int) -> Any:
    """Translate a frame coordinate by ``d``.

    A scalar moves. A SEQUENCE moves exactly ONE element, and that is
    load-bearing: shifting every element of a pitch-class set is a
    TRANSPOSITION, and every transposition-invariant op is unchanged by it for
    a reason that has nothing to do with the frame. Translating one element
    tests the frame; translating all of them tests transposition invariance
    and would report ``interval_vector`` as degenerate.

    A NESTED sequence moves exactly one LEAF — element ``[0][0]`` — for the
    same reason, one level down (rc465, `#T1188`).
    """
    if is_int(v):
        return v + d
    if is_int_seq(v):
        return [v[0] + d] + list(v[1:])
    return [[v[0][0] + d] + list(v[0][1:])] + [list(row) for row in v[1:]]


#: Parameter types the registry spells for an integer-valued parameter. Used to
#: separate "this op HAS an integer input the probe could not see" from "this op
#: has no integer input at all" — two facts rc464 counted as one.
_INT_TYPE_SPELLINGS = frozenset({
    "int", "Optional[int]", "int | None", "None | int",
})


def declared_int_params(name: str) -> Tuple[str, ...]:
    """The op's OWN declaration of which parameters take an integer.

    Read from the tool schema rather than from the signature, because the
    signature is not a reliable source here: ``eulerian_circuit(edges,
    start=None)`` carries no annotation at all while its ``ToolEntry`` declares
    ``start: Optional[int]``. The declaration is the SSoT for the type; the
    signature is the SSoT for the default.
    """
    from srmech.introspect.tool_schema import get_tool_schema
    entry = get_tool_schema().lookup(name)
    if entry is None:
        return ()
    return tuple(p.name for p in (entry.parameters or [])
                 if (p.type or "").strip() in _INT_TYPE_SPELLINGS)


def binding_gap(fn, base: Dict[str, Any]) -> Tuple[str, ...]:
    """Names the harvested binding is MISSING, or ``()`` when it is complete.

    Two ways a binding can be incomplete, and both were being reported as "this
    op has no integer input" through rc464:

    * a REQUIRED parameter is absent — ``inspect.signature(fn).bind(**base)``
      raises ``TypeError``. Measured at rc465: **55 of the 184** ops in that
      bucket. Python binds before the body runs, so ``Driver.raw({})`` would
      have raised identically; they were never drivable, and the ordering
      (coordinate test at :430, first call at :434) is what hid it.
    * a VAR_POSITIONAL the harvest dropped. ``signature.bind`` cannot see this
      — ``*operands`` accepts zero arguments — but the op's own guard does:
      ``einsum`` says "2 operand specs but 0 operands" and ``klein4_bundle``
      says "requires at least one vector". Both are ops whose harvested call
      has NO OPERANDS, which is the same fact as the first bullet wearing a
      different signature shape.
    """
    import inspect
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):          # builtins without a signature
        return ()
    try:
        sig.bind(**base)
    except TypeError:
        missing = tuple(
            p.name for p in sig.parameters.values()
            if p.default is inspect.Parameter.empty
            and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
            and p.name not in base)
        return missing or ("<unbindable>",)
    return tuple(f"*{p.name}" for p in sig.parameters.values()
                 if p.kind is p.VAR_POSITIONAL and not base.get(p.name))


def sentinel_int_params(name: str, base: Dict[str, Any]) -> Tuple[str, ...]:
    """Int-typed parameters the harvested binding carries as ``None``.

    The op DECLARES an integer parameter; its default is a sentinel meaning
    "resolve me at use time"; so the harvested binding — which is the worked
    example's first returning call with defaults applied — carries ``None``
    where the integer would be. That is neither an example defect (the
    parameter is ``required=False`` on every one of the 13 measured at rc465,
    so omitting it is what a worked example SHOULD do) nor an op defect. It is
    a fact about the instrument's reach, and rc465 gives it its own name
    instead of filing it under "no integer input at all".
    """
    return tuple(p for p in declared_int_params(name)
                 if p in base and base[p] is None)


def okey(x: Any) -> str:
    """A comparison key for an op's output. ``default=repr`` so a carrier that
    JSON cannot encode still compares by its repr rather than aborting the
    sweep — an unencodable output is still an output that either moved or did
    not."""
    try:
        return json.dumps(x, sort_keys=True, default=repr)
    except BaseException:
        return repr(x)


def least_period(vals: List[str], mmax: int = MMAX,
                 min_conf: int = MIN_CONFIRMATIONS) -> Tuple[Optional[int], int]:
    """``(m, confirmations)`` for the least period of a dense value sequence.

    ``(None, 0)`` when there is none — which is the answer for ``is_prime``
    and the reason this function exists as a named, testable thing rather than
    an inline loop.
    """
    n = len(vals)
    for m in range(2, mmax + 1):
        conf = n - m
        if conf < min_conf:
            break
        if all(vals[d + m] == vals[d] for d in range(conf)):
            return m, conf
    return None, 0


def first_difference(vals: List[int], mod: Optional[int] = None) -> Optional[int]:
    """The constant first difference of an integer sequence, or ``None``.

    THE GENERATOR CLAUSE, and it is NARROW BY CONSTRUCTION. A constant first
    difference means the op is AFFINE in the frame coordinate, and then that
    difference IS the generator. A non-affine op that hard-wires a generator
    is NOT detected here and is counted in the residual ceiling instead. R19's
    motivating blind spot (rc427 G3b) is therefore NARROWED, not closed, and
    the field docstring says so.

    ``mod`` IS REQUIRED FOR ANY OP THAT REDUCES, and leaving it out was a real
    defect in this instrument's first draft. The rc430 negative control
    ``LEAK_B(x, y, n) = mod_mul(7, cyclic_mod_add(x, y, n), n)`` welds in the
    generator 7, but over ℤ its first differences are ``7, 7, -5, 7, ...``:
    every wraparound breaks the constancy, so the clause returned ``None`` and
    LEAK_B passed as clean — which is EXACTLY the rc426 F12b blind spot this
    axis exists to narrow, reproduced by the instrument built to catch it.
    Reduced mod ``n`` the differences are a constant 7 and the leak is seen.

    Sign handling is a Class-K pin-slot read composed with Class C
    re-application: Python's ``%`` against a positive modulus returns the
    canonical non-negative residue, so no ``abs()`` appears here or anywhere
    in this module.
    """
    if len(vals) < 3:
        return None
    def d(i: int) -> int:
        raw = vals[i + 1] - vals[i]
        return raw % mod if mod else raw
    d0 = d(0)
    for i in range(1, len(vals) - 1):
        if d(i) != d0:
            return None
    return d0


def _carries(base: Dict[str, Any], value: int,
             mod: Optional[int] = None) -> List[str]:
    """Parameters that SUPPLY ``value`` — the test for "the caller chose this".

    Three widenings, each forced by a false positive this instrument actually
    produced:

    * **elements of a sequence**, not just scalars.
      ``crt_combine(residues=[...], moduli=[...])`` is periodic in
      ``residues[0]`` with period ``moduli[0]``, so the period IS supplied by
      the caller. Looking only at scalar parameters reported it WELDED IN — a
      false ``fixed`` on a shipped op.
    * **congruence, not equality**, when a frame is known. ``cyclic_mod_mul``
      advances by ``a mod n``; with ``a = 19`` and ``n = 12`` the generator
      reads 7 while no parameter equals 7. Comparing raw values called a
      caller-supplied generator welded-in.
    * a value of ``0`` supplies nothing — see :func:`_add_generator`.
    """
    out: List[str] = []

    def same(v: int) -> bool:
        return v == value or (mod is not None and mod > 0 and v % mod == value)

    for k, v in base.items():
        if is_int(v) and same(v):
            out.append(k)
        elif is_int_seq(v) and any(same(e) for e in v):
            out.append(k)
    return sorted(out)


def _add_generator(finding: Dict[str, Any], base: Dict[str, Any],
                   ints: Optional[List[int]], mod: Optional[int]) -> None:
    """Attach the generator axis to a finding — but ONLY when it is welded in.

    Three conditions, and dropping any one of them produces a false
    declaration:

    * the op must be AFFINE in the frame coordinate (constant first
      difference, reduced mod the frame — see :func:`first_difference`);
    * the generator must be neither ``1`` nor ``0``. ``1`` is "no generator"
      rather than a generator that happens to equal one; ``0`` means the op is
      CONSTANT along this coordinate at this frame, which is degeneracy, not
      an affine step. The first draft reported ``mod_mul`` with
      ``generator: 0`` for exactly that reason.
    * **no parameter may CARRY it**, tested up to congruence mod the frame.
      ``mod_mul(a, b, n)`` advances ``a`` by ``b`` each step, so its first
      difference is ``b mod n`` — a real generator, supplied by the caller.
      Declaring that welded-in is the same false-``fixed`` error as reading a
      caller-supplied modulus as a hard-wired one, one axis over.
    """
    if not ints:
        return
    gen = first_difference(ints, mod)
    if gen is None or gen in (0, 1):
        return
    if _carries(base, gen, mod):
        return
    finding["generator"] = gen
    finding["axis"] = ["modulus", "generator"]


class Driver:
    """A cached driver for one op over one harvested base binding.

    The cache is what makes a whole-registry sweep affordable: the parametric
    branch needs the same ``(coordinate, modulus)`` sequence once per candidate
    period, and recomputing it turned an uncached prototype into a run that
    never finished.
    """

    def __init__(self, name: str, base: Dict[str, Any], fn) -> None:
        self.name = name
        self.base = dict(base)
        self.fn = fn
        self._cache: Dict[Tuple[str, str], Optional[List[str]]] = {}
        self.calls = 0

    def coordinates(self) -> List[str]:
        return [k for k, v in self.base.items() if is_frame_coordinate(v)]

    def moduli(self, exclude: str) -> List[str]:
        return [k for k, v in self.base.items()
                if k != exclude and is_int(v) and v > 1]

    def raw(self, overrides: Dict[str, Any]) -> Any:
        self.calls += 1
        return self.fn(**dict(self.base, **overrides))

    def sequence(self, coord: str, over: Optional[Dict[str, Any]] = None,
                 length: int = R) -> Optional[List[str]]:
        """``[key(f(coord + d)) for d in 0..length-1]``, or ``None`` if the op
        is not TOTAL over the range. Not-total is a real answer, not an error:
        an op that raises partway cannot have its period measured."""
        over = over or {}
        ck = (coord, json.dumps(sorted(over.items()), default=repr) + f"|{length}")
        if ck in self._cache:
            return self._cache[ck]
        out: List[str] = []
        try:
            for d in range(length):
                kw = dict(over)
                kw[coord] = translate(self.base[coord], d)
                out.append(okey(self.raw(kw)))
        except BaseException:
            out_val = None
        else:
            out_val = out
        self._cache[ck] = out_val
        return out_val

    def int_sequence(self, coord: str,
                     over: Optional[Dict[str, Any]] = None,
                     length: int = 8) -> Optional[List[int]]:
        """The raw INTEGER outputs over the coordinate, for the generator
        clause. ``None`` unless every output is a bare int."""
        over = over or {}
        vals: List[int] = []
        try:
            for d in range(length):
                kw = dict(over)
                kw[coord] = translate(self.base[coord], d)
                r = self.raw(kw)
                if not is_int(r):
                    return None
                vals.append(r)
        except BaseException:
            return None
        return vals


def classify(name: str, base: Dict[str, Any], fn) -> Dict[str, Any]:
    """The predicate. Returns a record with ``verdict`` and ``findings``.

    ``verdict`` is one of: ``ADMISSIBLE`` · ``NOT_ADMISSIBLE`` · ``NO_ARG`` ·
    ``UNBOUND_REQUIRED`` · ``SENTINEL_INT_DEFAULT`` · ``NO_INT_INPUT`` ·
    ``BASE_RAISES``, plus the two by-name skips. The residual classes are
    named, never quietly dropped.

    rc465 (`#T1188`) SPLIT THE RESIDUAL, because ``NO_INT_INPUT`` had been
    carrying three different facts under one name and one number. It rose nine
    times in twenty-one days — 152 (rc430) 153 154 160 163 170 171 172 182 184
    (rc464) — and never once drained. Every raise carried a measured per-op
    justification and every one was honest about the LABEL; what none of them
    could say is what the label MEANT, because the bucket was decided at
    ``if not coords`` BEFORE the first call, so membership was a property of
    the harvested BINDING and not a measurement of the op. Partitioned at
    rc465 (executed, ledger-only, reproducing the live 184 exactly):

      55  the binding does not BIND — a required parameter is absent, so the
          probe never reached the op's body. Now ``UNBOUND_REQUIRED``. Seven of
          the ops the ceiling comments cite as "MEASURED to have no integer
          input" are in here, including five of the twelve behind the rc463 and
          rc464 raises (``eigvec_exact``, ``eigvec_exact_float``,
          ``jordan_chains_exact``, ``qmat_rank``, ``cdr_clean``).
       2  the binding drops a VAR_POSITIONAL the op requires — same fact, a
          signature shape ``bind()`` cannot see. Also ``UNBOUND_REQUIRED``.
      13  the op DECLARES an int parameter whose default is a sentinel, so the
          harvested binding carries ``None`` where the integer would be. Now
          ``SENTINEL_INT_DEFAULT``.
      26  the binding carries a matrix-shaped int operand the depth-2 wall
          refused to translate. 24 now drive to a real verdict (all
          NOT_ADMISSIBLE); 2 are measured-slow and named in ``SLOW_SKIP``.
      88  genuinely no integer anywhere in the binding. Still ``NO_INT_INPUT``,
          and now held to that STATEMENT rather than to a number.

    The order below is load-bearing: reachability is decided BEFORE the
    coordinate test, because "the probe could not call this op" and "this op
    has no frame coordinate" are different answers and only one of them is
    about the op.
    """
    rec: Dict[str, Any] = {"op": name, "verdict": "", "findings": []}
    if name in CONTRACT_SKIP:
        rec["verdict"] = "CONTRACT_SKIP"
        rec["reason"] = CONTRACT_SKIP[name]
        return rec
    if name in SLOW_SKIP:
        rec["verdict"] = "SLOW_SKIP"
        rec["reason"] = SLOW_SKIP[name]
        return rec
    if not base:
        rec["verdict"] = "NO_ARG"
        return rec
    gap = binding_gap(fn, base)
    if gap:
        rec["verdict"] = "UNBOUND_REQUIRED"
        rec["missing"] = list(gap)
        return rec
    drv = Driver(name, base, fn)
    coords = drv.coordinates()
    if not coords:
        sentinels = sentinel_int_params(name, base)
        if sentinels:
            rec["verdict"] = "SENTINEL_INT_DEFAULT"
            rec["sentinel_params"] = list(sentinels)
        else:
            rec["verdict"] = "NO_INT_INPUT"
        return rec
    try:
        drv.raw({})
    except BaseException as exc:
        rec["verdict"] = "BASE_RAISES"
        rec["exc"] = f"{type(exc).__name__}: {exc}"[:140]
        return rec

    for x in coords:
        # ── CHEAP SCREEN ──────────────────────────────────────────────
        # The full R-sweep costs 72 calls per (coordinate, modulus) pair and
        # an uncached, unscreened prototype never finished over 655 ops. A
        # short prefix decides the overwhelming majority in 24 calls, and it
        # can only ever REJECT: a period that fails on the prefix cannot hold
        # on the superset, so the screen removes runtime, never verdicts.
        short = drv.sequence(x, length=SCREEN)
        if short is None:
            continue                       # not total along this coordinate

        # DEGENERATE AT BASE. A constant function has every period and must
        # never classify `fixed` (PF8); this test is where that is enforced.
        #
        # rc430 REPAIR (`#T1127`): it used to `continue`, which also skipped the
        # PARAMETRIC sweep below — and constancy AT THE BASE ARGUMENTS is a
        # statement about the fixed branch only. It says nothing about whether
        # sweeping a modulus parameter makes the op periodic, which is a
        # different question asked with different arguments.
        #
        # WITNESS (the reason this is a repair and not a preference):
        # f(x, n) = x % n is genuinely parametric, and the shipped screen
        # returned NOT_ADMISSIBLE for it at base n = 1 (where x % 1 == 0 for
        # every x) while returning ADMISSIBLE/parametric for the SAME callable
        # at base n = 5. The verdict tracked the arguments, not the op — so the
        # census UNDER-reported, and "declared == admissible in both directions"
        # was being asserted against a roster that could be short.
        degenerate_at_base = len(set(short)) < 2

        if not degenerate_at_base:
            screen_m, _ = least_period(short, mmax=MMAX,
                                       min_conf=SCREEN_MIN_CONF)

            vals = drv.sequence(x) if screen_m is not None else None
            if vals is None and screen_m is not None:
                # Total on the prefix, not on R. NOTE (`#T1127`): this is the
                # SAME shape of leak as the degeneracy screen above — a
                # fixed-branch screen that also skips the parametric sweep —
                # but no non-contrived witness was constructed for it at rc430,
                # so it is left as-shipped and NAMED here rather than changed
                # on a structural argument alone. UNMEASURED, not closed.
                continue

            m, conf = (least_period(vals) if vals is not None else (None, 0))
            if m is not None:
                carried = _carries(base, m)
                if not carried:
                    f: Dict[str, Any] = {"coord": x, "scope": "fixed",
                                         "period": m, "confirmations": conf,
                                         "axis": ["modulus"]}
                    _add_generator(f, base, drv.int_sequence(x), m)
                    rec["findings"].append(f)
                    continue
                rec.setdefault("period_carried_by", {})[x] = carried

        for np_ in drv.moduli(x):
            try:
                outs = {n: okey(drv.raw({np_: n})) for n in NS}
            except BaseException:
                continue
            if len(set(outs.values())) < 2:
                continue                   # sweeping it does not move anything
            # screen: n-periodicity must already hold on a short prefix for
            # the SMALLEST n. Rejection here is sound for the same reason as
            # above — a prefix failure cannot become a full-range success.
            n0 = min(NS)
            pre = drv.sequence(x, {np_: n0}, length=2 * n0 + SCREEN_TAIL)
            if pre is None or any(pre[d + n0] != pre[d]
                                  for d in range(len(pre) - n0)):
                continue
            ok = True
            for n in NS:
                vs = drv.sequence(x, {np_: n})
                if vs is None or any(vs[d + n] != vs[d]
                                     for d in range(len(vs) - n)):
                    ok = False
                    break
            if not ok:
                continue
            const = None
            for mm in range(2, 25):
                good = True
                for n in NS:
                    vs = drv.sequence(x, {np_: n})
                    if vs is None or any(vs[d + mm] != vs[d]
                                         for d in range(len(vs) - mm)):
                        good = False
                        break
                if good:
                    const = mm
                    break
            if const is not None:
                continue                   # a constant period survived => fixed
            f = {"coord": x, "scope": "parametric", "param": np_,
                 "axis": ["modulus"]}
            n_gen = NS[-1]
            _add_generator(f, dict(base, **{np_: n_gen}),
                           drv.int_sequence(x, {np_: n_gen}), n_gen)
            rec["findings"].append(f)

    rec["calls"] = drv.calls
    rec["verdict"] = "ADMISSIBLE" if rec["findings"] else "NOT_ADMISSIBLE"
    return rec


def declared_scope(findings: List[Dict[str, Any]]) -> Optional[str]:
    """The scope a finding set implies. ``fixed`` WINS over ``parametric``.

    An op with a welded-in frame on ANY coordinate is one a consumer cannot
    fully choose the frame for, and that is the fact the field exists to
    publish. Reporting it as `parametric` because some OTHER coordinate is
    open would be the more flattering answer and the less true one.
    """
    scopes = {f["scope"] for f in findings}
    if "fixed" in scopes:
        return "fixed"
    if "parametric" in scopes:
        return "parametric"
    return None


def declared_axis(findings: List[Dict[str, Any]]) -> Tuple[str, ...]:
    axes = set()
    for f in findings:
        axes.update(f.get("axis") or ())
    return tuple(sorted(axes))


def probe_from_ledger(name: str, rows: Optional[Dict[str, Any]] = None
                      ) -> Dict[str, Any]:
    """Classify one registered op using its harvested arguments."""
    rows = ea.load_ledger() if rows is None else rows
    base = dict((rows.get(name) or {}).get("args") or {})
    res = ea.resolve(name)
    if res is None:
        return {"op": name, "verdict": "UNRESOLVABLE", "findings": []}
    return classify(name, base, res[2])
