"""v0.9.0rc449 (`#T1158`, gh #1653 residual) — REFUSAL-SET EQUALITY.

rc447 closed the `#T1146` unknown-kwarg divergence at the PYTHON IR BUILDER:
``_then_native_desc`` declines to emit a stage whose kwarg the op does not accept.
Its own commit says so — *"CLOSED AT THE IR BUILDER, NOT INSIDE C, because that is
where the two projections diverge."*

That makes the two projections AGREE. It does not make C REFUSE. On a bare-C host
there is no IR builder to decline, so a malformed declaration was still accepted
and computed, and rc447 is the same release that shipped
``c/test/test_srmech_chain_run.c`` — the ADR-0003 proof that consumers reach
exactly that host. **"The projections agree" and "C refuses what it should" are
different properties, and a parity harness comparing only OUTPUTS cannot tell them
apart.** This module measures the second one.

──────────────────────────────────────────────────────────────────────────────
WHY IT DRIVES ctypes DIRECTLY AND NOT THE PUBLIC SURFACE

``srmech/dsl/_chain.py`` collapses every non-OK C status to ``_NATIVE_MISS`` and
falls through to pure; ``srmech/cascade/compose.py`` does the same. Through the
front door a REFUSAL and a DEFERRAL are indistinguishable — the instrument would
have precisely the blindness it exists to remove. So the ``rc`` is read BEFORE the
collapse. ctypes is legitimate here because the ADR-0003 bare-C claim is carried by
``c/test/test_srmech_chain_run.c``, not by this file; this one is about the
STATUS VALUE, which a bare-C test cannot compare against a Python ``TypeError``.

──────────────────────────────────────────────────────────────────────────────
WHY THE CORPUS IS GENERATED

D1 was missed by CASE SELECTION, not by a missing mechanism.
``tests/test_dsl_chain_c_rc181.py`` has a real forced-pure arm (``_no_native``) and
simply never fed it an invalid chain. Nothing structural stopped it. So the probes
here are DERIVED from each op's live signature rather than hand-listed, and the
generator has anti-vacuity floors: a corpus that silently became empty would
otherwise pass every assertion in this file.

VERDICTS, NOT VALUES. Pure-vs-C value parity for ``autocorrelation`` diverges in 8
of 9 measured cases by up to 2.0 absolute; that is a real, separately-filed finding
(ledger row ``parity_tests_are_tautological_for_native_dispatched_ops``) and
importing it here would entangle a pre-existing defect with this rc's claim.
"""

from __future__ import annotations

import ctypes
import inspect
import json
from typing import Any, Dict, List, Tuple

import pytest

from srmech import _native

_HAS = (
    getattr(_native, "HAS_NATIVE", False)
    and getattr(_native, "LIB", None) is not None
    and hasattr(_native.LIB, "srmech_dsl_chain_run")
    and hasattr(_native.LIB, "srmech_dsl_chain_run_arena_bytes")
    and hasattr(_native.LIB, "srmech_chain_run")
    and hasattr(_native.LIB, "srmech_chain_run_arena_bytes")
)

pytestmark = pytest.mark.skipif(
    not _HAS,
    reason="native chain runners not present (pure-only build; the Windows dev "
           "host is has_native=False — CI's native job is authoritative)")

SRMECH_OK = 0
SRMECH_ERR_BAD_INPUT = 2
SRMECH_ERR_NOT_IMPL = 5

#: the seven ops dsl_leaf_dispatch really runs, pinned as literals AND
#: cross-checked against the C source text below (the
#: test_combinator_kernel_closure.py pattern).
_DSL_LEAVES = ("magnitude", "reorient", "pin_slot_at_zero",
               "best_rational_signed", "chiral_flip", "net_chirality",
               "autocorrelation")

#: a float seed every leaf accepts. magnitude on an INT seed returns NOT_IMPL for
#: unrelated carrier reasons, which is exactly the vacuity a hand-picked corpus
#: walks into — so the seed is fixed at a float and the clean arm is asserted.
_SEED = {"k": "f", "v": 0.3333333333333333}
_SEQ_SEED = {"k": "l", "v": [{"k": "f", "v": 1.0}, {"k": "f", "v": 2.0}]}

#: ops whose carrier is a SEQUENCE, not a scalar
_SEQ_OPS = ("chiral_flip", "net_chirality", "autocorrelation")


# ────────────────────────────────────────────────────────────────────────
# the two C entry points, status read BEFORE any collapse
# ────────────────────────────────────────────────────────────────────────

def _dsl_status(stage: Dict[str, Any], seed: Dict[str, Any]) -> int:
    lib = _native.LIB
    chain_json = json.dumps({"chain": {"name": "t"}, "stage": [stage]},
                            ensure_ascii=False).encode("utf-8")
    input_json = json.dumps(seed, ensure_ascii=False).encode("utf-8")
    ws_bytes = int(lib.srmech_dsl_chain_run_arena_bytes(
        len(chain_json), len(input_json)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    return int(lib.srmech_dsl_chain_run(
        chain_json, len(chain_json), input_json, len(input_json),
        ws, ws_bytes, out, out_cap, ctypes.byref(out_len)))


def _compose_status(op: str, args: Dict[str, Any],
                    inputs: Dict[str, Any]) -> int:
    lib = _native.LIB
    chain_json = json.dumps(
        {"name": "t", "steps": [{"class": "I", "op": op, "args": args}]},
        ensure_ascii=False).encode("utf-8")
    ctx_json = json.dumps({"inputs": inputs},
                          ensure_ascii=False).encode("utf-8")
    ws_bytes = int(lib.srmech_chain_run_arena_bytes(
        len(chain_json), len(ctx_json)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    return int(lib.srmech_chain_run(
        chain_json, len(chain_json), ctx_json, len(ctx_json),
        ws, ws_bytes, out, out_cap, ctypes.byref(out_len)))


def _pure_refuses(fn, kwargs: Dict[str, Any], carrier) -> bool:
    """True iff the PURE projection rejects this call by SIGNATURE.

    ``inspect.signature().bind`` is the signature question by itself, with no
    body executed — so a ValueError raised for a bad VALUE (a different defect
    class, and one this rc explicitly does not touch) cannot be mistaken for a
    key-set refusal.
    """
    try:
        inspect.signature(fn).bind(carrier, **kwargs)
    except TypeError:
        return True
    return False


# ────────────────────────────────────────────────────────────────────────
# corpus generation
# ────────────────────────────────────────────────────────────────────────

def _dsl_probes() -> List[Tuple[str, Dict[str, Any], bool, str]]:
    """(op, stage_kwargs, expect_refusal, label) for the DSL surface.

    ⚠️ EVERY PROBE IS ``clean_base + delta``. The base supplies each op's REQUIRED
    kwargs, so a dirty probe differs from its own clean twin by exactly the one
    key under test. Without that, ``reorient`` probes would all carry a missing
    REQUIRED ``orientation`` as well — and missing-required is a DISJOINT defect
    class that defers rather than refuses, so every such probe would have been
    measuring the wrong mechanism while looking green.
    """
    from srmech.dsl._catalog import lookup_cascade_op

    probes: List[Tuple[str, Dict[str, Any], bool, str]] = []
    legal_by_op: Dict[str, List[str]] = {}
    base_by_op: Dict[str, Dict[str, Any]] = {}

    for op in _DSL_LEAVES:
        params = inspect.signature(lookup_cascade_op(op)).parameters
        names = list(params)
        legal_by_op[op] = names[1:]
        base_by_op[op] = {
            k: 1 for k in names[1:]
            if params[k].default is inspect.Parameter.empty}

    for op in _DSL_LEAVES:
        params = inspect.signature(lookup_cascade_op(op)).parameters
        names = list(params)
        carrier, legal = names[0], legal_by_op[op]
        base = base_by_op[op]

        def probe(delta: Dict[str, Any], refuse: bool, label: str) -> None:
            d = dict(base)
            d.update(delta)
            probes.append((op, d, refuse, label))

        probe({}, False, "clean")
        # (ii) each legal key present and correct
        for k in legal:
            probe({k: 2}, False, f"legal:{k}")
        # (iii) each legal key with its last character dropped — the MEASURED
        #       witness class (max_denominator -> max_denominatr)
        for k in legal:
            if k[:-1] not in legal:
                probe({k[:-1]: 2}, True, f"truncated:{k[:-1]}")
        # (iv) an unmistakably foreign key
        probe({"bogus_t1158": 1}, True, "bogus")
        # (v) a key legal on a DIFFERENT op — per-op sets, not a vocabulary
        for other, keys in legal_by_op.items():
            if other != op and keys and keys[0] not in legal:
                probe({keys[0]: 1}, True, f"foreign:{keys[0]}")
                break
        # (vi) the data-carrier name as a kwarg (DSL surface only)
        probe({carrier: 5}, True, f"carrier:{carrier}")
    return probes


def _compose_probes() -> List[Tuple[str, str, Dict[str, Any], bool, str]]:
    """(op, registry_name, args, expect_refusal, label) for the compose surface."""
    cases = [
        ("gcd", "srmech.math.cyclic.gcd", {"a": 12, "b": 18}),
        ("mod_add", "srmech.math.cyclic.mod_add", {"a": 12, "b": 18, "n": 5}),
        ("mod_mul", "srmech.math.cyclic.mod_mul", {"a": 12, "b": 18, "n": 5}),
        ("mod_pow", "srmech.math.cyclic.mod_pow", {"a": 12, "k": 3, "n": 5}),
        ("mod_inv", "srmech.math.cyclic.mod_inv", {"a": 7, "n": 5}),
        ("rational_add", "srmech.math.rational.rational_add",
         {"a": 1, "b": 2}),
    ]
    probes: List[Tuple[str, str, Dict[str, Any], bool, str]] = []
    for op, full, good in cases:
        probes.append((op, full, dict(good), False, "clean"))
        for k in good:
            bad = dict(good)
            bad[k[:-1]] = bad.pop(k)
            probes.append((op, full, bad, True, f"truncated:{k[:-1]}"))
        bad = dict(good)
        bad["bogus_t1158"] = 1
        probes.append((op, full, bad, True, "bogus"))
    # the same-arity cross-op pair: `n` is real on mod_add, meaningless on gcd
    probes.append(("gcd", "srmech.math.cyclic.gcd",
                   {"a": 12, "b": 18, "n": 5}, True, "foreign:n"))
    return probes


# ────────────────────────────────────────────────────────────────────────
# the gates
# ────────────────────────────────────────────────────────────────────────

def test_dsl_refusal_set_equals_the_pure_signature_verdict() -> None:
    """Bidirectional, per probe: C returns BAD_INPUT ⟺ the pure signature rejects.

    Both directions matter and they fail differently. C accepting what pure
    rejects is the rc448 silent-wrong-answer. C rejecting what pure accepts is
    STRICTER-THAN-PYTHON — a bare-C host refusing chains a Python user runs
    fine — and the whole output-parity corpus is blind to it (30 of 45 parity
    files have no forced-pure arm at all).
    """
    from srmech.dsl._catalog import lookup_cascade_op

    probes = _dsl_probes()
    seen_ok = seen_bad = 0
    mismatches: List[str] = []
    unclassified: List[str] = []

    # ⚠️ THE CLEAN BASELINE, established BEFORE any dirty probe is believed.
    # A dirty probe on an op whose CLEAN twin does not run is vacuous: C would be
    # declining for a carrier reason that has nothing to do with key sets, and the
    # row would score a refusal it did not earn. Ops without a working clean arm
    # are EXCLUDED and counted, never silently passed.
    clean_base = {op: kw for op, kw, _, lab in probes if lab == "clean"}
    clean_ok = {}
    for op in _DSL_LEAVES:
        seed = _SEQ_SEED if op in _SEQ_OPS else _SEED
        clean_ok[op] = _dsl_status(
            {"op": op, **clean_base[op]}, seed) == SRMECH_OK
    assert sum(clean_ok.values()) >= 4, (
        f"only {sum(clean_ok.values())} of {len(_DSL_LEAVES)} leaves have a "
        f"working clean arm ({clean_ok}); the corpus cannot attribute anything")

    for op, kwargs, expect_refusal, label in probes:
        if not clean_ok[op]:
            continue
        seed = _SEQ_SEED if op in _SEQ_OPS else _SEED
        rc = _dsl_status({"op": op, **kwargs}, seed)
        fn = lookup_cascade_op(op)
        carrier = [1.0, 2.0] if op in _SEQ_OPS else 0.3333333333333333
        pure_refuses = _pure_refuses(fn, kwargs, carrier)

        assert pure_refuses == expect_refusal, (
            f"{op} {label}: the CORPUS is wrong about the pure verdict "
            f"(expected refusal={expect_refusal}, pure says {pure_refuses}) — "
            f"fix the generator, not the assertion.")

        if rc == SRMECH_OK:
            seen_ok += 1
        elif rc == SRMECH_ERR_BAD_INPUT:
            seen_bad += 1
        elif rc == SRMECH_ERR_NOT_IMPL:
            # ⚠️ EVERY NOT_IMPL MUST BE CLASSIFIED. It is the defer-to-pure
            # channel, so an UNEXPLAINED one silently converts "C refuses" into
            # "C shrugs" — rc447's shape rebuilt inside C. The only legal
            # defers here are carrier shapes the strict C path declines on a
            # CLEAN probe; a DIRTY probe must never reach this branch.
            if expect_refusal:
                unclassified.append(f"{op} {label}: dirty probe got NOT_IMPL")
            continue
        else:
            unclassified.append(f"{op} {label}: unexpected status {rc}")
            continue

        c_refuses = (rc == SRMECH_ERR_BAD_INPUT)
        if c_refuses != pure_refuses:
            direction = ("C ACCEPTS what pure refuses (silent wrong answer)"
                         if pure_refuses else
                         "C REFUSES what pure accepts (stricter-than-Python)")
            mismatches.append(f"{op} {label}: {direction} (rc={rc})")

    assert not unclassified, (
        "unclassified C statuses — every NOT_IMPL must be an explained "
        "defer:\n  " + "\n  ".join(unclassified))
    assert not mismatches, (
        "refusal-set mismatch between the projections:\n  "
        + "\n  ".join(mismatches))

    # anti-vacuity: an empty or degenerate generator must go RED, not green
    assert len(probes) >= 20, f"corpus collapsed to {len(probes)} probes"
    assert seen_ok >= 1, "no probe was ACCEPTED — the corpus proves nothing"
    assert seen_bad >= 10, (
        f"only {seen_bad} refusals observed; the generator is not producing "
        f"the malformed half of the corpus")


def test_compose_refusal_set_equals_the_pure_signature_verdict() -> None:
    """The Surface-A twin, on ``args`` keys."""
    from srmech._resolve import resolve_dotted_callable

    probes = _compose_probes()
    seen_ok = seen_bad = 0
    mismatches: List[str] = []
    unclassified: List[str] = []

    # The same clean baseline as the DSL gate, and it is load-bearing here: the
    # C rational_* arms take bignum-Q operands and decline plain int literals with
    # BAD_INPUT for a VALUE reason. Comparing a dirty probe against that would
    # report "C refuses what pure accepts" for a refusal the key-set validator
    # never made — the stricter-than-Python false positive, from the harness.
    clean_ok = {}
    for op, full, args, refuse, label in probes:
        if label != "clean":
            continue
        inputs = {k: v for k, v in args.items() if isinstance(v, int)}
        clean_ok[op] = _compose_status(op, args, inputs) == SRMECH_OK
    assert sum(clean_ok.values()) >= 4, (
        f"only {sum(clean_ok.values())} compose ops have a working clean arm "
        f"({clean_ok}); the corpus cannot attribute anything")

    for op, full, args, expect_refusal, label in probes:
        if not clean_ok.get(op):
            continue
        inputs = {k: v for k, v in args.items() if isinstance(v, int)}
        rc = _compose_status(op, args, inputs)
        fn = resolve_dotted_callable(full)
        legal = set(inspect.signature(fn).parameters)
        pure_refuses = not set(args).issubset(legal)

        assert pure_refuses == expect_refusal, (
            f"{op} {label}: the CORPUS is wrong about the pure verdict")

        if rc == SRMECH_OK:
            seen_ok += 1
        elif rc == SRMECH_ERR_BAD_INPUT:
            seen_bad += 1
        elif rc == SRMECH_ERR_NOT_IMPL:
            if expect_refusal:
                unclassified.append(f"{op} {label}: dirty probe got NOT_IMPL")
            continue
        else:
            unclassified.append(f"{op} {label}: unexpected status {rc}")
            continue

        if (rc == SRMECH_ERR_BAD_INPUT) != pure_refuses:
            direction = ("C ACCEPTS what pure refuses (silent wrong answer)"
                         if pure_refuses else
                         "C REFUSES what pure accepts (stricter-than-Python)")
            mismatches.append(f"{op} {label}: {direction} (rc={rc})")

    assert not unclassified, (
        "unclassified C statuses:\n  " + "\n  ".join(unclassified))
    assert not mismatches, (
        "refusal-set mismatch:\n  " + "\n  ".join(mismatches))
    assert len(probes) >= 20, f"corpus collapsed to {len(probes)} probes"
    # Derived rather than hardcoded: every op with a working clean arm must have
    # contributed at least that arm. Combined with the >= 4 clean-arm floor above
    # this cannot go vacuous, and it does not need editing when an op's carrier
    # support changes.
    assert seen_ok >= sum(clean_ok.values()), (
        f"{sum(clean_ok.values())} ops had a clean arm but only {seen_ok} "
        f"acceptances were observed")
    assert seen_bad >= 10, f"only {seen_bad} refusals observed"
    # EXCLUSIONS ARE REPORTED, NOT HIDDEN. An op silently dropping out of the
    # corpus is how a harness quietly stops measuring its own subject.
    excluded = sorted(op for op, ok in clean_ok.items() if not ok)
    assert excluded == ["rational_add"], (
        f"the set of ops with no clean C arm changed: {excluded}. Each is "
        f"EXCLUDED from refusal comparison because C declines it for a VALUE "
        f"reason (the rational_* arms want bignum-Q operands, not int "
        f"literals), which says nothing about key sets. A new entry here means "
        f"the corpus is measuring less than it was — widen the operands or "
        f"file the op, do not just update this list.")


def test_the_defer_channel_is_not_reclassified() -> None:
    """Refuse is not defer. Pinned BY VALUE on both surfaces.

    If an unknown key returned NOT_IMPL it would read as *"this projection does
    not do it yet; the other one might"* — false on a bare-C host, where nothing
    will ever implement ``max_denominatr``. That would be rc447's divergence-only
    shape re-implemented inside C, with only the constants moved.
    """
    assert _dsl_status({"op": "definitely_not_an_op"}, _SEED) == \
        SRMECH_ERR_NOT_IMPL, "an unknown OP must still DEFER"
    assert _dsl_status({"op": "reorient"}, _SEED) == SRMECH_ERR_NOT_IMPL, (
        "a MISSING REQUIRED kwarg must still DEFER — a disjoint defect class")
    assert _dsl_status({"op": "best_rational_signed", "max_denominatr": 2},
                       _SEED) == SRMECH_ERR_BAD_INPUT, (
        "an unknown KEY must REFUSE, not defer")
    assert _compose_status("no_such_op", {}, {}) == SRMECH_ERR_NOT_IMPL
    assert _compose_status("gcd", {"a": 12, "b": 18, "bogus": 1},
                           {"a": 12, "b": 18}) == SRMECH_ERR_BAD_INPUT


def test_the_witness_that_motivated_the_rc() -> None:
    """The single measured case, stated by itself so it cannot be refactored away.

    rc448: both of these returned ``SRMECH_OK``; the second one answered ``(1, 3)``
    instead of ``(0, 1)`` because the constraint was dropped and the default 100
    was used. One letter, no error, a different number.
    """
    ok = _dsl_status({"op": "best_rational_signed", "max_denominator": 2}, _SEED)
    bad = _dsl_status({"op": "best_rational_signed", "max_denominatr": 2}, _SEED)
    assert ok == SRMECH_OK, "the LEGAL spelling must still run"
    assert bad == SRMECH_ERR_BAD_INPUT, (
        "the one-letter typo must REFUSE; at rc448 it returned OK and (1, 3)")


def test_dsl_leaf_names_match_the_c_source() -> None:
    """The pinned op list is cross-checked against the C dispatch table.

    A literal list that silently stopped matching the shipped surface would make
    every assertion above true of a corpus describing nothing.
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parents[2] / "c" / "src"
           / "srmech_dsl_chain_run.c").read_text(encoding="utf-8")
    body = src[src.index("static srmech_status_t dsl_leaf_dispatch("):]
    body = body[:body.index("\n}\n")]
    import re
    arms = set(re.findall(r'memcmp\(op,\s*"([A-Za-z0-9_]+)"', body))
    assert arms == set(_DSL_LEAVES), (
        f"_DSL_LEAVES is stale: C dispatches {sorted(arms)}, this module "
        f"probes {sorted(_DSL_LEAVES)}")
