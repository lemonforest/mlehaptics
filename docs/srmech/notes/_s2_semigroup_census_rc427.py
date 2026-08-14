"""rc427 (`#T1130`) S2 — the REGISTRY-WIDE SEMIGROUP CENSUS that had never been run.

WHY THIS EXISTS
===============
The rc426 brief asserted **"0 of 649 ops are semigroup-not-group."** The rc427
synthesis (`rc427_research_round_synthesis.md` §6 Brief-1, §7 A1) established
that this census **was never run**: it covered 11 hand-picked surfaces, and it
is refuted outright by a shipped op — ``srmech.biology.q8.q8_project_v4`` is a
non-injective idempotent self-map WITH a C peer (``c/src/srmech_q8.c:108``).

Synthesis §8.2 rules: *"a registry-wide semigroup census presented as
pre-existing — it has never been run. If rc427 wants the claim, it must RUN
it."* This file runs it.

THE CRITERION, STATED BEFORE THE MEASUREMENT
============================================
An op ``f`` is **SEMIGROUP-NOT-GROUP** iff there is a **finite** set ``S``
(drawn from the declared carrier ladder below) with

  1. ``f`` **total on S** — it raises on no element of S;
  2. ``f(S) subset-of S`` — S is **invariant**, so ``f|_S`` is a self-map;
  3. ``f|_S`` **not injective** — ``|f(S)| < |S|``.

Under iteration ``{f, f^2, f^3, ...}`` is then a semigroup in which ``f`` has no
inverse: ``f`` is not a bijection of S, so it is not a group element. That is
exactly the "arrow" property of synthesis §4.

INSTRUMENT v1 WAS REFUTED BY ITS OWN NEGATIVE CONTROL — RECORDED, NOT HIDDEN
===========================================================================
v1 swept the **non-carrier parameters** of n-ary ops over a companion ladder and
applied the criterion to whatever landed. Pre-registered negative control PF3a
**FIRED**: ``srmech.cascade.cyclic_mod_add`` — a translation, provably a
bijection — was classified SEMIGROUP_NOT_GROUP, on the witness
``carrier=Z12, binding (b=12, n=6)``.

The classification is *arithmetically correct* and *structurally worthless*:
``a -> (a + 12) mod 6`` really is non-injective on ``{0..11}``, but only because
the sweep bound a modulus **smaller than the carrier it was enumerating**. The
op's own carrier is Z/6, on which it is a bijection. The collapse measured the
WINDOW, not the op.

A guard that fires is evidence, not an obstacle. Three candidate repairs were
tried and each **kills a true positive**, so none of them ships:

  * *reject when f is the identity on its image* — kills ``magnitude`` on
    ``{-3..3}`` (image ``{0,1,2,3}``, identity there), the archetypal Class-K
    pin-slot and a genuine information-destroying op;
  * *reject when f factors through a proper reduction* — kills
    ``mod_mul(., 6, 12)``, the synthesis §4 headline arrow, because
    ``6x mod 12 = 6(x mod 2)``: factoring-through **is** what non-injectivity
    is;
  * *require the image to shrink as the window grows* — cannot separate them,
    because ANY op with an internal modulus has an image bounded by that
    modulus regardless of the window.

**The residue is a real structural limit, and it is the honest finding.**
Separating "the op destroys information on its own carrier" from "I handed the
op a window wider than its contract" requires each parameter's **domain
constraint**, and the registry publishes none: ``ToolParameter`` carries exactly
``name`` / ``type`` / ``required`` / ``summary`` (measured, this run). So for
**n-ary** ops the criterion genuinely **cannot** be applied mechanically
registry-wide.

INSTRUMENT v2 — NARROW TO THE DECIDABLE CLASS
=============================================
The defect is entirely in the *binding sweep*. Remove the sweep and it is gone.

**TIER A (HARD CARDINAL).** Ops with **exactly one required parameter**
(measured: **259 of 649**). Every optional parameter takes the op's **own
declared default**, which is in-contract by construction, and there is no
non-carrier value left to get wrong. The only input is the carrier element, and
requirement (1) — totality — means every element of S was **accepted by the op's
own validation**. This is the same discipline as the shipped ref-notation gate:
strict on the decidable class, bounded on the residual.

**TIER B (BOUNDED, NOT A CARDINAL).** Ops with >= 2 required parameters
(measured: **310 of 649**). Reported with the sweep, and reported as
**UNSUPPORTED as a cardinal**, with ``cyclic_mod_add`` shipped as the worked
artifact so the boundary is visible rather than asserted.

**Ops with ZERO required parameters** (measured: **80**) have no carrier slot
and are NOT-APPLICABLE by construction.

THE OTHER LIMITS, STATED UP FRONT
=================================
L1. **Existential over a FIXED ladder.** A negative means "no witness among the
    carriers enumerated here", NOT "no witness exists". **Positives are
    CONFIRMED by execution; negatives are BOUNDED.** The ladder is printed in
    full and content-addressed so the bound is reproducible.
L2. **"CONTAINS a non-injective self-map" is NOT decidable here.** The brief
    asks "is, or contains". Only "IS" is executable. An op returning
    ``Dict[str, Any]`` may compute a non-injective self-map internally and
    report it as a field; nothing short of reading all 649 implementations
    decides that. Reported as an explicitly UNMEASURED axis, never folded into
    the cardinal.
L3. **The declared-type screen (Tier 1) inherits the returns=-honesty defect.**
    ``test_immolation.py::test_advertised_return_type_is_honest`` exists because
    ``returns=`` can lie; synthesis §5.3 records rc425 shipping six ops
    advertising ``list`` and returning ``tuple``. Tier 1 is a SHAPE census only.
    **Tiers A/B do not depend on it** — they probe the live callables, so a
    declared-type lie cannot hide a positive.
L4. **Constant-map witnesses are separated, not silently counted.** A binding
    making ``f`` constant is non-injective by the letter of the criterion but
    carries no information about the op. Bucketed apart, excluded from the
    headline.
L5. **Blind probing is bounded by a safety denylist** — ops owning global state,
    servers, the filesystem or the network are NOT called. Printed and counted.
L6. **Tier A is in-contract only up to the op's own validation.** An op that
    silently accepts an out-of-domain value could still yield a window artifact.
    Every positive therefore ships its carrier provenance so a reader can judge.

PRE-REGISTERED FALSIFIERS
=========================
PF1  POSITIVE CONTROL / SENSITIVITY. ``q8_project_v4`` (unary -> Tier A) MUST
     land in SEMIGROUP_NOT_GROUP. It is the shipped counterexample the synthesis
     names. If the instrument cannot see it, it is blind and the cardinal VOID.
PF2  BINDING-SWEEP SANITY (Tier B only). ``mod_mul`` MUST be found
     non-injective under some binding — the gcd(c, n) > 1 arrow of synthesis §4.
     Tier B is bounded regardless; this only shows the sweep is live.
PF3  NEGATIVE CONTROL / SPECIFICITY. ``chiral_flip`` (unary involution -> Tier A)
     MUST land in GROUP. If a provable bijection is called a semigroup, the
     instrument over-fires and the Tier-A cardinal is VOID.
     *(PF3a, ``cyclic_mod_add``, FIRED against instrument v1 and is what forced
     v2. It is n-ary, so under v2 it is Tier B and out of the cardinal.)*
PF4  DENOMINATOR HONESTY. The headline is reported over the **Tier-A
     MEASURED-SELF-MAP** denominator, never over 649. If fewer than 20 Tier-A
     ops are measured as self-maps at all, the verdict is BOUNDED, not a
     cardinal.
PF5  NON-VACUITY OF THE GROUP BUCKET. Tier-A GROUP must be non-empty. If every
     measured self-map were non-injective the injectivity test would never
     separate — the F14 / S6 "instrument cannot return otherwise" defect.

DISCIPLINE
==========
* No Python ``abs()``. The signed carrier window is a named **Class-K pin-slot**
  (``srmech.cascade.pin_slot_at_zero``) then **Class-C** orientation
  re-application (``srmech.cascade.reorient``) — two named cascade ops, so the
  cascade count matches the cascade shape.
* No stdlib ``math`` / ``fractions`` / ``decimal``; no numpy. Exact rates use
  ``srmech.math.q.Q``; content-addressing uses ``srmech.amsc.format.sha256_bytes``
  (Class A).
* Output is NDJSON, one record per line.

Run:  PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_s2_semigroup_census_rc427.py
"""

import importlib
import importlib.util
import inspect
import json
import os
import sys
import time
from array import array

import srmech
from srmech.amsc.format import sha256_bytes
from srmech.cascade import pin_slot_at_zero, reorient
from srmech.introspect.tool_schema import ToolParameter, get_tool_schema, warmup_all
from srmech.math.hv import HV
from srmech.math.q import Q

OUT = __file__[: -len(".py")] + ".ndjson"

PREREGISTERED = {
    "PF1_positive_control_sensitivity": {
        "op": "srmech.biology.q8.q8_project_v4",
        "tier": "A",
        "must_land_in": "SEMIGROUP_NOT_GROUP",
        "void_if_fails": True,
        "why": "synthesis §1.5 / §7-A1: shipped non-injective idempotent self-map with a C peer",
    },
    "PF2_binding_sweep_sanity": {
        "op": "srmech.math.cyclic.mod_mul",
        "tier": "B",
        "must_be": "non-injective under some binding",
        "void_if_fails": False,
        "why": "the gcd(c, n) > 1 arrow of synthesis §4; shows the Tier-B sweep is live. "
        "Tier B is BOUNDED regardless of this.",
    },
    "PF3_negative_control_specificity": {
        "op": "srmech.cascade.chiral_flip",
        "tier": "A",
        "must_land_in": "GROUP",
        "void_if_fails": True,
        "why": "order reversal is an involution, hence bijective; if the instrument "
        "calls a bijection a semigroup it over-fires and the Tier-A cardinal is void",
    },
    "PF3a_negative_control_that_FIRED_against_instrument_v1": {
        "op": "srmech.cascade.cyclic_mod_add",
        "instrument_v1_verdict": "SEMIGROUP_NOT_GROUP on witness carrier=Z12 binding (b=12, n=6)",
        "truth": "a translation is a bijection; the sweep bound a modulus SMALLER than "
        "the carrier it enumerated, so the collapse measured the WINDOW, not the op",
        "consequence": "instrument v1 REFUTED for n-ary ops; v2 narrows the cardinal to "
        "the unary decidable class where no binding exists to get wrong",
        "status_under_v2": "n-ary -> Tier B -> excluded from the cardinal",
    },
    "PF4_denominator_honesty": {
        "rule": "headline is over TIER-A MEASURED_SELF_MAP, never over 649",
        "bounded_if_tier_a_measured_self_maps_below": 20,
    },
    "PF5_group_bucket_non_vacuity": {
        "rule": "Tier-A GROUP must be non-empty, else the injectivity test never separates",
        "void_if_group_bucket_empty": True,
    },
}

# ── safety denylist (L5) ────────────────────────────────────────────────────
DENY_PREFIXES = (
    "srmech.bus.",
    "srmech.dsl.",
    "srmech.amsc.catalog.",
    "srmech.amsc.descriptor.",
    "srmech.introspect.publish",
    "srmech.signal_processing.path_registry.",
    "srmech.signal_processing.cascade_dispatcher.",
    "srmech.introspect.by_pid",
)

#: Deny by SIGNATURE, not by name-regex — an op with a filesystem-path
#: parameter must never be blind-probed.
#:
#: This rule is here because the first full run **destroyed its own stdout**.
#: ``srmech.math.laplacian.write_packed_graph(path, edges, weights=None)``
#: declares ``path: str``; the probe put an int carrier element in slot 0, and
#: Python's ``open()`` accepts an **integer file descriptor**. ``open(1, "wb")``
#: therefore wrote binary edge records onto fd 1 and closed it. The census ran
#: to completion with no visible output and exited 1 with no traceback.
#:
#: This is NOT a defect claim about srmech — over the wire the MCP inputSchema
#: types ``path`` as a string. It is the same structural fact L6/Tier-B rest on,
#: with teeth: **the registry publishes no per-parameter domain constraint**, so
#: nothing mechanical stops a caller handing a parameter a value from outside
#: the set its contract means. Here it cost the instrument a silent run.
DENY_PARAM_NAMES = frozenset(
    {"path", "file", "filename", "fname", "dest", "destination", "out_path",
     "outfile", "dir", "directory", "root", "url", "uri", "src", "source_path"}
)

PER_OP_TIME_BUDGET_S = 6.0
MAX_SWEPT_EXTRA_REQUIRED = 2


# ── Class-K pin-slot then Class-C re-application (NEVER abs()) ─────────────
def _class_k_then_c_signed_window(max_magnitude):
    """The signed integer window ``{-m..m}``, as a named K/C composition.

    Class **K** (pin-slot / phase boundary): ``pin_slot_at_zero`` splits a value
    into ``(orientation, magnitude)``. Class **C** (cascade-orientation):
    ``reorient`` re-applies a chosen orientation to a magnitude. Enumerating
    magnitudes and re-orienting them BOTH ways is exactly the signed window —
    and it is two named cascade ops, not one ALU ``abs()``.
    """
    seen = {}
    for m in range(0, max_magnitude + 1):
        _orientation, magnitude = pin_slot_at_zero(m)  # Class K
        for want in (1, -1):
            seen[reorient(magnitude, orientation=want)] = None  # Class C
    return sorted(seen)


# ── the carrier ladder (L1: this IS the bound of every negative) ───────────
def _key_int(v):
    return ("i", v) if type(v) is int else None


def _key_float(v):
    if type(v) is float:
        return ("f", v)
    if type(v) is int:
        return ("f", float(v))
    return None


def _key_bytes(v):
    return ("b", bytes(v)) if type(v) in (bytes, bytearray) else None


#: The integer sequence carriers are EXACT-Z. A key function must therefore
#: never COERCE — an earlier revision spelled ``tuple(int(x) for x in v)``, which
#: truncated a float result into the integer carrier: ``multitaper`` returns a
#: float PSD, ``[0.3, 0.7, 1.2]`` keyed as ``(0, 0, 1)``, landed "inside"
#: SIGNED_LIST3 and manufactured collisions that were pure rounding. It scored a
#: spurious 27 -> 3 positive. A float where the object is exact is a defect, so
#: the key demands ``type(x) is int`` and returns None otherwise (bool excluded:
#: it is an int subclass and would smuggle a 2-element domain in).
def _exact_int_seq(v):
    out = []
    for x in v:
        if type(x) is not int:
            return None
        out.append(x)
    return tuple(out)


def _key_tuple(v):
    if type(v) is not tuple:
        return None
    k = _exact_int_seq(v)
    return None if k is None else ("t", k)


def _key_list(v):
    if type(v) is not list:
        return None
    k = _exact_int_seq(v)
    return None if k is None else ("l", k)


def _key_hv(v):
    if not isinstance(v, HV):
        return None
    k = _exact_int_seq(list(v))  # HV.__iter__ already yields plain ints
    return None if k is None else ("h", k, v.sectors)


def _hv(seq):
    return HV(array("B", seq), sectors=4)


def _build_carriers():
    signed3 = _class_k_then_c_signed_window(3)
    carriers = []

    def add(cid, elems, keyfn, companions, note):
        keys = [keyfn(e) for e in elems]
        assert all(k is not None for k in keys), cid
        assert len(set(keys)) == len(keys), cid
        carriers.append(
            {
                "id": cid,
                "elements": list(elems),
                "keys": set(keys),
                "key": keyfn,
                "companions": list(companions),
                "note": note,
            }
        )

    add("Z12", list(range(12)), _key_int, [12, 6, 5, 4, 2, 1], "Z/12 as int")
    add("Z7", list(range(7)), _key_int, [7, 3, 2, 1, 0], "Z/7 as int (prime)")
    add("Z8", list(range(8)), _key_int, [8, 4, 2, 1, 0], "Z/8 as int (2-power)")
    add("SIGNED_INT7", signed3, _key_int, [3, 2, 1, 0, 7], "{-3..3}, built K-then-C")
    add(
        "SIGNED_F64",
        [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0],
        _key_float,
        [2.0, 1.0, 0.0, 2, 1],
        "7 exactly-representable dyadic floats; float equality is EXACT on these",
    )
    add("Q8BYTE", [bytes([b]) for b in range(8)], _key_bytes, [8, 4, 2, 1, 0],
        "the 8 single-byte Q8 elements")
    add("V4BYTE", [bytes([b]) for b in range(4)], _key_bytes, [4, 2, 1, 0],
        "the 4 single-byte Klein-4 / V4 elements")
    add("BYTE2x4", [bytes([a, b]) for a in range(4) for b in range(4)], _key_bytes,
        [4, 2, 1, 0], "length-2 byte buffers over {0..3}")
    add("TUP3x3", [(a, b, c) for a in range(3) for b in range(3) for c in range(3)],
        _key_tuple, [3, 2, 1, 0], "length-3 int tuples over {0,1,2}")
    add("LIST3x3", [[a, b, c] for a in range(3) for b in range(3) for c in range(3)],
        _key_list, [3, 2, 1, 0], "length-3 int lists over {0,1,2}")
    # ── ladder extension, and WHY it was added ──
    # The first complete run filed ``srmech.signal_processing.sign_quantise`` as
    # SEMIGROUP_CONSTANT_ONLY (degenerate, excluded from the headline). That was
    # an artifact of THIS ladder: LIST3x3 is non-negative, so an op that keeps
    # only the sign lane returned [1,1,1] for all 27 inputs and looked CONSTANT.
    # On signed input it returns e.g. [-1,1,1] — non-injective and NOT constant,
    # the exact Class-K dual of ``magnitude`` (which keeps the magnitude and
    # destroys the sign). The scalar carriers were signed and the sequence
    # carriers were not; these two close that asymmetry. Recorded rather than
    # quietly folded in — it is L1 ("the ladder IS the bound") with a name.
    sgn1 = _class_k_then_c_signed_window(1)  # {-1, 0, 1}, K-then-C
    add("SIGNED_TUP3", [(a, b, c) for a in sgn1 for b in sgn1 for c in sgn1],
        _key_tuple, [3, 2, 1, 0], "length-3 int tuples over {-1,0,1}")
    add("SIGNED_LIST3", [[a, b, c] for a in sgn1 for b in sgn1 for c in sgn1],
        _key_list, [3, 2, 1, 0], "length-3 int lists over {-1,0,1}")
    add("HV3x4", [_hv([a, b, c]) for a in range(4) for b in range(4) for c in range(4)],
        _key_hv, [4, 3, 2, 1, 0], "length-3 sectors=4 hypervectors over {0..3}")
    return carriers


# ── Tier 1: the DECIDABLE declared-shape screen (all 649) ──────────────────
_FAMILY = {}
for _n in ("int", "bool"):
    _FAMILY[_n] = "INT"
for _n in ("float", "complex", "number", "Q", "Real"):
    _FAMILY[_n] = "SCALAR_CONT"
for _n in ("list", "tuple", "sequence", "bytes", "bytearray", "str", "array", "HV", "Vec"):
    _FAMILY[_n] = "SEQ"
_FAMILY["Mat"] = "MAT"
_FAMILY["dict"] = "DICT"


def _family(t):
    """Widen a declared type string to a coarse family. Widening is DELIBERATELY
    aggressive: it can only SHRINK the not-self-map-shaped bucket, the safe
    direction under L3."""
    s = t.strip()
    if s.startswith("Optional[") and s.endswith("]"):
        s = s[len("Optional[") : -1]
    out = set()
    for arm in s.split("|"):
        a = arm.strip()
        if not a or a == "None":
            continue
        head = a.split("[")[0].strip().strip("'\"")
        out.add(_FAMILY.get(head, head))
    return out


def tier1_shape_screen(tools):
    rows = {}
    for e in tools:
        rfam = _family(e.returns.type) if e.returns else set()
        exact, fam = [], []
        for p in e.parameters:
            if e.returns and p.type.strip() == e.returns.type.strip():
                exact.append(p.name)
            elif _family(p.type) & rfam:
                fam.append(p.name)
        rows[e.name] = {
            "op": e.name,
            "returns": e.returns.type if e.returns else None,
            "exact_type_slots": exact,
            "family_slots": fam,
            "shaped": bool(exact or fam),
        }
    return rows


# ── contract adjudication (the ONE domain constraint the registry DOES publish)
#
# L6 says Tier A is in-contract only up to the op's own validation. There is
# exactly one place where an op's validation cannot help, because Python itself
# widens the domain: **``bool`` is a subclass of ``int``**. A parameter declared
# ``bool`` has a TWO-element domain ``{False, True}``; feed it the seven ints of
# a Z-carrier and any op branching on truthiness looks non-injective, when on its
# real domain it is a bijection.
#
# Measured this run: ``srmech.cascade.dft_sigma(inverse: bool)`` — declared
# ``sigma = 1 if inverse else -1`` — returned ``[1,1,1,-1,1,1,1]`` over
# ``{-3..3}`` purely because only ``0`` is falsy. On ``{False, True}`` it is
# ``{False -> -1, True -> +1}``: a BIJECTION.
#
# So: a witness is a **bool-domain artifact** when the slot's declared type is
# exactly ``bool`` and the fed element is not a ``bool``. This is the only
# rejecting use of a declared type in the whole instrument — everywhere else L3
# forbids trusting ``returns=``/``type=``. It is admissible here because it can
# only move an op OUT of the positive set, it is mechanical, and the widening it
# corrects is a property of the Python language, not of a possibly-stale
# annotation.
def adjudicate(entry, witnesses):
    """Split a positive's witnesses into (contract_clean, bool_domain_artifact)."""
    declared = {p.name: p.type.strip() for p in entry.parameters}
    clean, artifact = [], []
    for w in witnesses:
        if w["injective"] or w["constant"]:
            continue
        if declared.get(w["slot_name"]) == "bool" and w["carrier"] not in ("BOOL2",):
            artifact.append(w)
        else:
            clean.append(w)
    return clean, artifact


# ── the executed probe ─────────────────────────────────────────────────────
def _required_params(fn):
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return None, None
    req, opt = [], []
    for name, p in sig.parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        (req if p.default is p.empty else opt).append(name)
    return req, opt


def _bindings(companions, n_extra):
    if n_extra == 0:
        return [()]
    if n_extra == 1:
        return [(c,) for c in companions]
    return [(a, b) for a in companions for b in companions]


#: A shipped op called with an argument it never asked for may raise
#: ``SystemExit``, which is a ``BaseException`` and slips past ``except
#: Exception`` — it killed the first full run of this census silently, exit 1
#: with no traceback. Caught explicitly, counted, and reported.
_PROBE_CATCH = (Exception, SystemExit)


def probe_op(fn, carriers, req, opt):
    """Execute one op over the carrier ladder. Returns (bucket, witnesses, diag)."""
    slots = list(range(min(len(req), 3)))
    n_extra = len(req) - 1
    witnesses, any_call_ok, any_closed = [], False, False
    t0, calls, abandoned = time.monotonic(), 0, False
    sysexits = 0

    for carrier in carriers:
        elems, keys, keyfn = carrier["elements"], carrier["keys"], carrier["key"]
        probe_elem = elems[0]
        for slot in slots:
            if n_extra > MAX_SWEPT_EXTRA_REQUIRED:
                continue
            for extra in _bindings(carrier["companions"], n_extra):
                if time.monotonic() - t0 > PER_OP_TIME_BUDGET_S:
                    abandoned = True
                    break
                args = list(extra)
                args.insert(slot, probe_elem)
                try:
                    calls += 1
                    r = fn(*args)
                except SystemExit:
                    sysexits += 1
                    continue
                except Exception:
                    continue
                any_call_ok = True
                k = keyfn(r)
                if k is None or k not in keys:
                    continue
                # the probe landed INSIDE the carrier -- enumerate all of S
                image, total_ok = set(), True
                for x in elems:
                    a2 = list(extra)
                    a2.insert(slot, x)
                    try:
                        calls += 1
                        rv = fn(*a2)
                    except _PROBE_CATCH:
                        total_ok = False
                        break
                    kk = keyfn(rv)
                    if kk is None or kk not in keys:
                        total_ok = False
                        break
                    image.add(kk)
                if not total_ok:
                    continue
                any_closed = True
                witnesses.append(
                    {
                        "carrier": carrier["id"],
                        "carrier_size": len(elems),
                        "slot_name": req[slot],
                        "binding_names": [req[i] for i in range(len(req)) if i != slot],
                        "binding": [repr(v) for v in extra],
                        "image_size": len(image),
                        "injective": len(image) == len(elems),
                        "constant": len(image) == 1,
                        "collapse_ratio": str(Q(len(image), len(elems))),
                    }
                )
            if abandoned:
                break
        if abandoned:
            break

    diag = {
        "n_required": len(req),
        "n_optional": len(opt),
        "calls": calls,
        "seconds": round(time.monotonic() - t0, 3),
        "abandoned_on_time_budget": abandoned,
        "systemexit_raised": sysexits,
    }
    if not any_call_ok:
        return "NOT_EXECUTABLE", witnesses, diag
    if not any_closed:
        return "NOT_CLOSED", witnesses, diag
    noninj = [w for w in witnesses if not w["injective"]]
    if not noninj:
        return "GROUP", witnesses, diag
    if all(w["constant"] for w in noninj):
        return "SEMIGROUP_CONSTANT_ONLY", witnesses, diag
    return "SEMIGROUP_NOT_GROUP", witnesses, diag


BUCKETS = (
    "SEMIGROUP_NOT_GROUP",
    "SEMIGROUP_CONSTANT_ONLY",
    "SEMIGROUP_BOOL_DOMAIN_ARTIFACT",
    "GROUP",
    "NOT_CLOSED",
    "NOT_EXECUTABLE",
    "NO_CARRIER_SLOT",
    "EXCLUDED_SAFETY",
)


def _best(detail_entry):
    w = [x for x in detail_entry["witnesses"] if not x["injective"] and not x["constant"]]
    return max(w, key=lambda x: x["image_size"]) if w else None


def main():
    # Defense in depth after the write_packed_graph incident: keep private dups
    # of stdout/stderr so a probed op that closes fd 1 or 2 cannot silence the
    # census. The denylist is the fix; this is the seatbelt.
    guard_out = os.fdopen(os.dup(1), "w", buffering=1)
    guard_err = os.fdopen(os.dup(2), "w", buffering=1)
    sys.stdout, sys.stderr = guard_out, guard_err

    print(f"srmech.__file__    = {srmech.__file__}")
    print(f"srmech.__version__ = {srmech.__version__}")
    numpy_present = importlib.util.find_spec("numpy") is not None
    print(f"numpy present      = {numpy_present}")

    warmup_all()  # LOAD-BEARING -- without it the registry count is short
    tools = get_tool_schema().tools
    print(f"registry           = {len(tools)}")

    # measured, not assumed: the registry publishes no per-parameter domain
    param_fields = [f for f in ToolParameter.__dataclass_fields__]
    print(f"ToolParameter fields = {param_fields}  <- no domain/range constraint")
    print()

    carriers = _build_carriers()
    ladder = [
        {"id": c["id"], "size": len(c["elements"]), "companions": c["companions"], "note": c["note"]}
        for c in carriers
    ]
    ladder_sha = sha256_bytes(json.dumps(ladder, sort_keys=True).encode())  # Class A
    print("CARRIER LADDER (this IS the bound of every negative):")
    for c in carriers:
        print(f"  {c['id']:<12} |S|={len(c['elements']):<4} {c['note']}")
    print(f"  ladder sha256 = {ladder_sha}")
    print()

    t1 = tier1_shape_screen(tools)
    shaped = [r for r in t1.values() if r["shaped"]]
    exact = [r for r in t1.values() if r["exact_type_slots"]]
    print("TIER 1 -- declared-shape screen (decidable, 649/649; SHAPE ONLY, see L3)")
    print(f"  self-map-shaped, exact declared-type match : {len(exact)}")
    print(f"  self-map-shaped, family-widened            : {len(shaped)}")
    print(f"  NOT self-map-shaped even widened           : {len(t1) - len(shaped)}")
    print()

    # ── execute ──
    tierA = {k: [] for k in BUCKETS}
    tierB = {k: [] for k in BUCKETS}
    detail = {}
    t_start = time.monotonic()
    excluded_by_param = []
    for i, e in enumerate(tools):
        mod, _, fname = e.name.rpartition(".")
        fn = getattr(importlib.import_module(mod), fname)
        req, opt = _required_params(fn)
        io_params = [] if req is None else [
            n for n in (req + opt) if n.lower() in DENY_PARAM_NAMES
        ]
        if e.name.startswith(DENY_PREFIXES) or io_params:
            if io_params and not e.name.startswith(DENY_PREFIXES):
                excluded_by_param.append({"op": e.name, "io_params": io_params})
            tierA["EXCLUDED_SAFETY"].append(e.name)
            detail[e.name] = {"bucket": "EXCLUDED_SAFETY", "tier": "-", "witnesses": [], "diag": {}}
            continue
        if req is None:
            tier, bucket, wits, diag = "-", "NOT_EXECUTABLE", [], {"reason": "no signature"}
        elif len(req) == 0:
            tier, bucket, wits, diag = "-", "NO_CARRIER_SLOT", [], {"reason": "zero required params"}
        else:
            tier = "A" if len(req) == 1 else "B"
            bucket, wits, diag = probe_op(fn, carriers, req, opt)
        (tierA if tier in ("A", "-") else tierB)[bucket].append(e.name)
        detail[e.name] = {"bucket": bucket, "tier": tier, "witnesses": wits, "diag": diag}
        if (i + 1) % 150 == 0:
            print(f"  ... {i + 1}/{len(tools)} probed ({time.monotonic() - t_start:.0f}s)")
    print(f"  execution complete in {time.monotonic() - t_start:.0f}s")
    print()

    A = {k: [n for n in v if detail[n]["tier"] == "A"] for k, v in tierA.items()}

    # ── contract adjudication of the Tier-A positive set ──
    by_name = {e.name: e for e in tools}
    adjud, bool_artifacts = {}, []
    kept = []
    for op in A["SEMIGROUP_NOT_GROUP"]:
        clean, art = adjudicate(by_name[op], detail[op]["witnesses"])
        adjud[op] = {"clean": clean, "artifact": art}
        if clean:
            kept.append(op)
        else:
            bool_artifacts.append(op)
    A["SEMIGROUP_BOOL_DOMAIN_ARTIFACT"] = bool_artifacts
    A["SEMIGROUP_NOT_GROUP"] = kept

    a_self_maps = sum(
        len(A[k])
        for k in (
            "SEMIGROUP_NOT_GROUP",
            "SEMIGROUP_CONSTANT_ONLY",
            "SEMIGROUP_BOOL_DOMAIN_ARTIFACT",
            "GROUP",
        )
    )
    b_self_maps = sum(
        len(tierB[k]) for k in ("SEMIGROUP_NOT_GROUP", "SEMIGROUP_CONSTANT_ONLY", "GROUP")
    )
    a_total = sum(len(v) for v in A.values())

    # ── controls ──
    def bk(op):
        return detail.get(op, {}).get("bucket", "ABSENT")

    ctl = {
        "PF1": {"op": "srmech.biology.q8.q8_project_v4", "tier_expected": "A",
                "tier": detail.get("srmech.biology.q8.q8_project_v4", {}).get("tier"),
                "expected": "SEMIGROUP_NOT_GROUP",
                "measured": bk("srmech.biology.q8.q8_project_v4")},
        "PF3": {"op": "srmech.cascade.chiral_flip", "tier_expected": "A",
                "tier": detail.get("srmech.cascade.chiral_flip", {}).get("tier"),
                "expected": "GROUP", "measured": bk("srmech.cascade.chiral_flip")},
    }
    for v in ctl.values():
        v["pass"] = v["measured"] == v["expected"] and v["tier"] == v["tier_expected"]
    mm = detail.get("srmech.math.cyclic.mod_mul", {})
    ctl["PF2"] = {
        "op": "srmech.math.cyclic.mod_mul", "tier": mm.get("tier"),
        "measured": mm.get("bucket"),
        "expected": "SEMIGROUP_NOT_GROUP (Tier B; bounded regardless)",
        "pass": mm.get("bucket") == "SEMIGROUP_NOT_GROUP",
    }
    cma = detail.get("srmech.cascade.cyclic_mod_add", {})
    ctl["PF3a_v1_refutation_reproduced"] = {
        "op": "srmech.cascade.cyclic_mod_add", "tier": cma.get("tier"),
        "measured": cma.get("bucket"),
        "note": "n-ary -> Tier B under v2, hence OUT of the cardinal. Reproduced here "
                "as the worked window-artifact, not repaired.",
        "pass": cma.get("tier") == "B",
    }
    ctl["PF4"] = {"rule": "cardinal over TIER-A measured self-maps",
                  "tier_a_measured_self_maps": a_self_maps, "pass": a_self_maps >= 20}
    ctl["PF5"] = {"rule": "Tier-A GROUP non-empty", "group_size": len(A["GROUP"]),
                  "pass": len(A["GROUP"]) > 0}
    void_keys = ("PF1", "PF3", "PF4", "PF5")
    cardinal_valid = all(ctl[k]["pass"] for k in void_keys)

    print("PRE-REGISTERED FALSIFIERS")
    for k, v in ctl.items():
        print(f"  {k:<32} {'PASS' if v.get('pass') else 'FAIL'}   {v}")
    print(f"\n  Tier-A cardinal VALID: {cardinal_valid}  "
          f"(void-if-fail set = {void_keys})")
    print()

    print(f"TIER A -- HARD CARDINAL   (exactly one required parameter; {a_total} ops)")
    for k in BUCKETS:
        if A[k]:
            print(f"  {k:<26} {len(A[k]):>4}")
    print(f"  {'-> measured self-maps':<26} {a_self_maps:>4}")
    print()
    print(f"TIER B -- BOUNDED, NOT A CARDINAL   (>= 2 required params; "
          f"{sum(len(v) for v in tierB.values())} ops)")
    for k in BUCKETS:
        if tierB[k]:
            print(f"  {k:<26} {len(tierB[k]):>4}")
    print(f"  {'-> measured self-maps':<26} {b_self_maps:>4}")
    print()

    head_n = len(A["SEMIGROUP_NOT_GROUP"])
    print("=" * 78)
    print(f"HEADLINE:  {head_n} of {a_self_maps} Tier-A MEASURED SELF-MAPS are "
          f"semigroup-not-group")
    print(f"           (denominator is {a_self_maps}, NOT {len(tools)} — see PF4)")
    print(f"           rate = {Q(head_n, a_self_maps) if a_self_maps else 'n/a'}")
    print("=" * 78)
    print()
    print(f"EVERY TIER-A POSITIVE, NAMED ({head_n}) — contract-adjudicated:")
    for op in sorted(A["SEMIGROUP_NOT_GROUP"]):
        b = max(adjud[op]["clean"], key=lambda w: w["image_size"])
        print(f"  {op}")
        print(f"      carrier={b['carrier']} |S|={b['carrier_size']} slot={b['slot_name']} "
              f"|f(S)|={b['image_size']} surviving={b['collapse_ratio']}")
    print()
    print(f"REJECTED AS BOOL-DOMAIN ARTIFACTS ({len(A['SEMIGROUP_BOOL_DOMAIN_ARTIFACT'])}) — "
          f"a two-element domain fed 7 ints because bool is a subclass of int:")
    for op in sorted(A["SEMIGROUP_BOOL_DOMAIN_ARTIFACT"]):
        print(f"  {op}  (slot declared bool; a BIJECTION on {{False, True}})")
    print()
    print(f"TIER-A CONSTANT-ONLY (degenerate, excluded from the headline) "
          f"({len(A['SEMIGROUP_CONSTANT_ONLY'])}):")
    for op in sorted(A["SEMIGROUP_CONSTANT_ONLY"]):
        print(f"  {op}")
    print()
    print(f"TIER-B positives (BOUNDED — each may be a window artifact like "
          f"cyclic_mod_add): {len(tierB['SEMIGROUP_NOT_GROUP'])}")
    print()

    missed = [op for op in A["SEMIGROUP_NOT_GROUP"] if not t1[op]["shaped"]]
    print(f"Tier-1 x Tier-A cross-check: positives the declared-SHAPE screen would "
          f"have MISSED = {len(missed)}")
    for op in sorted(missed):
        print(f"  {op}  (declares returns={t1[op]['returns']})")

    # ── NDJSON ──
    recs = [
        {"record": "environment", "task": "#T1130", "srmech_file": srmech.__file__,
         "srmech_version": srmech.__version__, "numpy_present": numpy_present,
         "registry_total": len(tools), "warmup_all_called": True,
         "tool_parameter_fields": param_fields,
         "tool_parameter_publishes_domain_constraint": False},
        {"record": "preregistered_falsifiers", "falsifiers": PREREGISTERED},
        {"record": "instrument_v1_refuted_by_own_negative_control",
         "control": "PF3a srmech.cascade.cyclic_mod_add",
         "v1_verdict": "SEMIGROUP_NOT_GROUP on carrier=Z12 binding (b=12, n=6)",
         "why_wrong": "the sweep bound a modulus SMALLER than the enumerated carrier; "
                      "(a+12) mod 6 collapses {0..11} but the op's carrier is Z/6, on "
                      "which it is a bijection. The collapse measured the WINDOW.",
         "repairs_tried_and_rejected": [
             {"repair": "reject when f is the identity on its image",
              "kills": "magnitude on {-3..3} (image {0,1,2,3}, identity there)"},
             {"repair": "reject when f factors through a proper reduction",
              "kills": "mod_mul(.,6,12): 6x mod 12 == 6(x mod 2); factoring-through IS "
                       "what non-injectivity is"},
             {"repair": "require the image to shrink as the window grows",
              "kills": "nothing, but separates nothing either — any op with an internal "
                       "modulus has an image bounded by it regardless of the window"}],
         "residue": "separating a genuine collapse from a window artifact needs each "
                    "parameter's DOMAIN CONSTRAINT; the registry publishes none",
         "resolution": "v2 narrows the hard cardinal to the unary decidable class"},
        {"record": "carrier_ladder", "ladder_sha256": ladder_sha, "carriers": ladder,
         "limits": {
             "L1": "existential over THIS ladder; negatives BOUNDED, positives CONFIRMED",
             "L2": "'CONTAINS a non-injective self-map' is NOT decidable here; only 'IS'",
             "L3": "Tier-1 declared types can lie (immolation gate); Tiers A/B do not use them",
             "L4": "constant-map witnesses bucketed apart, excluded from the headline",
             "L5": "safety-denylist ops are not called",
             "L6": "Tier A is in-contract only up to the op's own validation"}},
        {"record": "tier1_shape_screen", "total": len(t1),
         "exact_declared_type_shaped": len(exact),
         "family_widened_shaped": len(shaped),
         "not_shaped": len(t1) - len(shaped)},
        {"record": "controls", "controls": ctl,
         "tier_a_cardinal_valid": cardinal_valid, "void_if_fail_set": list(void_keys)},
        {"record": "tier_a_cardinal",
         "definition": "ops with exactly ONE required parameter; optionals take the op's "
                       "own declared defaults, so no binding can be out-of-contract",
         "tier_a_total": a_total,
         "buckets": {k: len(A[k]) for k in BUCKETS},
         "measured_self_maps": a_self_maps,
         "semigroup_not_group": head_n,
         "bool_domain_artifacts_rejected": len(A["SEMIGROUP_BOOL_DOMAIN_ARTIFACT"]),
         "headline": f"{head_n} of {a_self_maps} Tier-A measured self-maps",
         "headline_denominator_is_not": len(tools),
         "rate_exact_q": str(Q(head_n, a_self_maps)) if a_self_maps else None,
         "tier1_shape_screen_would_have_missed": missed},
        {"record": "tier_b_bounded",
         "definition": "ops with >= 2 required parameters; the non-carrier binding sweep "
                       "can hand the op a window wider than its contract",
         "classification": "UNSUPPORTED as a cardinal",
         "tier_b_total": sum(len(v) for v in tierB.values()),
         "buckets": {k: len(tierB[k]) for k in BUCKETS},
         "measured_self_maps": b_self_maps,
         "raw_semigroup_not_group": len(tierB["SEMIGROUP_NOT_GROUP"]),
         "worked_artifact": "srmech.cascade.cyclic_mod_add",
         "ops": sorted(tierB["SEMIGROUP_NOT_GROUP"])},
    ]
    for op in sorted(A["SEMIGROUP_NOT_GROUP"]):
        d = detail[op]
        recs.append({"record": "tier_a_positive", "op": op,
                     "contract_adjudicated": "CLEAN",
                     "best_witness": max(adjud[op]["clean"], key=lambda w: w["image_size"]),
                     "n_clean_noninjective_nonconstant_witnesses": len(adjud[op]["clean"]),
                     "carriers_closed_on": sorted({w["carrier"] for w in d["witnesses"]}),
                     "declared_returns": t1[op]["returns"],
                     "tier1_shaped": t1[op]["shaped"]})
    for op in sorted(A["SEMIGROUP_BOOL_DOMAIN_ARTIFACT"]):
        recs.append({"record": "tier_a_bool_domain_artifact", "op": op,
                     "contract_adjudicated": "REJECTED",
                     "why": "the carrier slot is declared bool — a TWO-element domain. "
                            "Python's bool-subclasses-int let 7 Z-carrier ints in; on "
                            "{False, True} the op is a BIJECTION.",
                     "rejected_witnesses": adjud[op]["artifact"],
                     "true_classification_by_this_instrument": "UNDETERMINED "
                            "(never measured on its own 2-element domain)"})
    for op in sorted(A["SEMIGROUP_CONSTANT_ONLY"]):
        recs.append({"record": "tier_a_constant_only", "op": op,
                     "witnesses": detail[op]["witnesses"][:4]})
    recs.append({"record": "tier_a_group_bucket", "n": len(A["GROUP"]), "ops": sorted(A["GROUP"])})
    recs.append({"record": "tier_a_not_closed", "n": len(A["NOT_CLOSED"]),
                 "note": "executed without raising somewhere, but the image never landed "
                         "back inside any enumerated carrier — NOT a group verdict",
                 "ops": sorted(A["NOT_CLOSED"])})
    recs.append({"record": "tier_a_not_executable", "n": len(A["NOT_EXECUTABLE"]),
                 "note": "every attempted call raised — BOUNDED, not a negative",
                 "ops": sorted(A["NOT_EXECUTABLE"])})
    # NOTE: these two buckets hold tier-"-" ops (no carrier slot / not called),
    # which the Tier-A view filters out. Report them from the UNFILTERED dict or
    # the census stops summing to the registry total.
    no_slot = [n for n in tierA["NO_CARRIER_SLOT"] if detail[n]["tier"] == "-"]
    excl = [n for n in tierA["EXCLUDED_SAFETY"] if detail[n]["tier"] == "-"]
    recs.append({"record": "no_carrier_slot", "n": len(no_slot),
                 "note": "zero required parameters — NOT-APPLICABLE by construction",
                 "ops": sorted(no_slot)})
    recs.append({"record": "excluded_safety",
                 "module_prefixes": list(DENY_PREFIXES),
                 "denied_param_names": sorted(DENY_PARAM_NAMES),
                 "n": len(excl),
                 "excluded_by_io_parameter": excluded_by_param,
                 "why_param_rule_exists":
                     "write_packed_graph(path: str, ...) probed with an int carrier "
                     "element: Python open() accepts an integer FILE DESCRIPTOR, so "
                     "open(1, 'wb') wrote binary onto fd 1 and closed stdout. The census "
                     "completed with zero visible output and exit 1, no traceback. Not a "
                     "defect claim about srmech (MCP types path as a string) — it is the "
                     "SAME missing per-parameter domain constraint that bounds Tier B.",
                 "ops": sorted(excl)})
    recs.append({"record": "registry_partition_sums_to_total",
                 "tier_a": a_total, "tier_b": sum(len(v) for v in tierB.values()),
                 "no_carrier_slot": len(no_slot), "excluded_safety": len(excl),
                 "sum": a_total + sum(len(v) for v in tierB.values()) + len(no_slot) + len(excl),
                 "registry_total": len(tools)})
    ab = sorted(op for op, d in detail.items() if d["diag"].get("abandoned_on_time_budget"))
    recs.append({"record": "time_budget_abandoned", "budget_s": PER_OP_TIME_BUDGET_S,
                 "n": len(ab), "ops": ab})
    se = sorted(op for op, d in detail.items() if d["diag"].get("systemexit_raised"))
    recs.append({"record": "systemexit_raisers",
                 "note": "shipped ops that raise SystemExit (a BaseException) when handed "
                         "an argument they never asked for. This slipped past 'except "
                         "Exception' and killed the first full run silently, exit 1, no "
                         "traceback.",
                 "n": len(se),
                 "ops": {op: detail[op]["diag"]["systemexit_raised"] for op in se}})
    recs.append({"record": "unmeasured_axis_L2",
                 "axis": "'CONTAINS a non-injective self-map'",
                 "classification": "UNSUPPORTED",
                 "why": "only 'IS a self-map' is executable; deciding 'contains' needs all "
                        "649 implementations read. Never folded into the cardinal."})

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"\nwrote {len(recs)} NDJSON records -> {OUT}")
    return 0 if cardinal_valid else 1


if __name__ == "__main__":
    sys.exit(main())
