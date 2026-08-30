"""rc430 (`#T1127`) — the FRAME instrument: is an op's frame an INPUT or WELDED IN?

ONE INSTRUMENT, TWO CONSUMERS. ``tests/test_frame_scope_rc430.py`` is the
ratchet; ``docs/srmech/notes/_frame_scope_census_rc430.py`` is the census that
writes the NDJSON. They import the same functions, so the shipped declaration
and the published measurement cannot drift apart by being separately
hand-rolled — which is the failure mode a test that re-implements its own
subject always eventually has.

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
}


def is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def is_int_seq(v: Any) -> bool:
    return isinstance(v, list) and len(v) > 0 and all(is_int(x) for x in v)


def is_frame_coordinate(v: Any) -> bool:
    """A value that can be TRANSLATED along a frame axis."""
    return is_int(v) or is_int_seq(v)


def translate(v: Any, d: int) -> Any:
    """Translate a frame coordinate by ``d``.

    A scalar moves. A SEQUENCE moves exactly ONE element, and that is
    load-bearing: shifting every element of a pitch-class set is a
    TRANSPOSITION, and every transposition-invariant op is unchanged by it for
    a reason that has nothing to do with the frame. Translating one element
    tests the frame; translating all of them tests transposition invariance
    and would report ``interval_vector`` as degenerate.
    """
    if is_int(v):
        return v + d
    return [v[0] + d] + list(v[1:])


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
    ``NO_INT_INPUT`` · ``BASE_RAISES``. The last three are the residual
    classes the ratchet holds under a down-only ceiling — they are counted and
    named, never quietly dropped.
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
    drv = Driver(name, base, fn)
    coords = drv.coordinates()
    if not coords:
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
