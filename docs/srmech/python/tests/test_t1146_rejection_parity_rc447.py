"""`#T1146` / gh #1653 — REJECTION parity: C must refuse what Python refuses.

THE DEFECT (measured rc444, 24 of 34 probes across 5 ops). ``Chain.then(op,
**kwargs)`` built a native C stage that SILENTLY DROPPED a kwarg the op does not
accept, then computed an answer — while the pure path raised ``TypeError`` from
the callable's own signature::

    chain().then('autocorrelation', bogus=1).run([1,2,3])
        pure   -> TypeError: autocorrelation() got an unexpected keyword 'bogus'
        native -> [14.0, 11.0, 11.0]          # a WRONG ANSWER to a bad program

⚠️ WHY THIS IS THE HALF A CAPABILITY-ONLY FIX LEAVES OPEN.
   Co-equal projections must agree on what they REFUSE, not only on what they
   compute. A projection that ACCEPTS a declaration the other REJECTS does not
   have a capability gap — it gives a wrong answer to a malformed program, and
   the malformed program looks like it worked. Every other gate in this issue
   measures acceptance, so all of them could go green with this wide open. The
   parity ratchet is blind to it BY CONSTRUCTION: a down-only count of REJECTED
   chains cannot see a chain that is wrongly ACCEPTED.

THE FIX defers rather than raises. An unaccepted kwarg makes the stage
non-nativizable, so the whole chain takes the pure runner and raises the SAME
``TypeError`` from the SAME place. Python's observable behaviour is unchanged —
fixing parity by changing the scripting projection's shipped contract would be
solving the wrong problem. It reuses the existing "return None → defer" contract
that already handled non-scalar kwargs (rc103 inform-don't-limit).

⚠️ WHAT THE rc444 PROBE ALSO ESTABLISHED, so the fix is not credited too widely:
   the ops that ALREADY had parity had it INCIDENTALLY. ``cyclic_gcd`` and
   ``pin_slot_at_zero`` reject because the native stage-builder declined for an
   unrelated reason and PYTHON then raised — the error is a Python ``TypeError``
   on both paths.

⚠️⚠️ SUPERSEDED AT rc449 (`#T1158`) — TWO CLAIMS IN THIS DOCSTRING WERE WRONG, and
   this module SHIPS, so they are corrected here rather than annotated elsewhere.

   1. *"There is NO key-set validator anywhere in the C leaf surface, so there was
      no in-tree pattern to copy."* The second half was false when written:
      ``iv_no_extra_keys`` (``c/src/srmech_invoke.c:1580``) already walked an
      arguments object against ``e->params[j].name`` and declined. It did not
      match the greps that motivated the claim (``key_set|keyset|unknown_key|
      validate_keys``) — a grep artifact reported as an absence. rc449 copied its
      WALK; it deliberately did not copy its DEFER disposition, which is correct
      only because its one bare-C consumer converts it to an explicit MCP error.
      The first half is now false too: rc449 added ``dsl_leaf_keyset_ok``
      (``c/src/srmech_dsl_chain_run.c``) and ``cr_args_keyset_ok``
      (``c/src/srmech_compose_run.c``).

   2. *"this closes the gap"* — it closed the DIVERGENCE, not the gap. Teaching
      the IR builder to decline makes the two projections AGREE while leaving C's
      ACCEPTANCE behaviour untouched, so on a bare-C host — where no IR builder
      exists — the malformed declaration was still accepted and computed. Measured
      at rc448 head: ``{"op":"best_rational_signed","max_denominatr":2}`` returned
      ``SRMECH_OK`` and ``(1, 3)`` instead of the ``(0, 1)`` the correctly-spelled
      stage gives. rc447 is also the release that shipped
      ``c/test/test_srmech_chain_run.c``, so it demonstrated that consumers reach
      exactly that host. "The projections agree" and "C refuses what it should"
      are DIFFERENT PROPERTIES, and an output-comparing parity harness cannot tell
      them apart — see ``test_t1158_refusal_set_equality_rc449.py``, which
      compares STATUS rather than output.

   The rc447 behaviour asserted BELOW is still correct and still required; only
   the two claims above about its scope were overstated. Per
   [[feedback_fix_falsehoods_when_found_latency_by_surface]] a false claim in
   shipped text is repaired in the current rc.
"""
from __future__ import annotations

import pytest

from srmech.dsl._catalog import lookup_cascade_op
from srmech.dsl._chain import _op_accepts, _then_native_desc

#: The 5 ops the rc444 probe measured as defective, with a valid input each.
DEFECTIVE_OPS = ["autocorrelation", "chiral_flip", "magnitude",
                 "net_chirality", "reorient"]

#: Keys no cascade op declares. ``orientation`` / ``max_denominator`` / ``index``
#: are deliberately REAL parameter names of OTHER ops — a plausible-looking key
#: is the realistic mistake, and a check that only caught obvious junk like
#: ``bogus`` would miss it.
UNKNOWN_KEYS = ["bogus", "nonexistent_kwarg", "max_denominator",
                "orientation", "index"]


@pytest.mark.parametrize("op_name", DEFECTIVE_OPS)
@pytest.mark.parametrize("key", UNKNOWN_KEYS)
def test_an_unaccepted_kwarg_is_NOT_nativized(op_name, key):
    """The core gate. A stage the pure path would reject must not run in C."""
    op_fn = lookup_cascade_op(op_name)
    if _op_accepts(op_fn, key):
        pytest.skip("%s genuinely accepts %r — not an unknown-key case"
                    % (op_name, key))
    assert _then_native_desc(op_name, {key: 1}, op_fn) is None, (
        "%s(%s=...) built a native stage. C would drop the key and COMPUTE, "
        "while pure raises TypeError — that is `#T1146`." % (op_name, key))


@pytest.mark.parametrize("op_name", DEFECTIVE_OPS)
def test_the_VALID_call_still_nativizes(op_name):
    """THE CONTROL THAT MATTERS. A fix that deferred everything would score a
    perfect zero defects and be worthless — it would silently delete the native
    path. This asserts the check DISCRIMINATES."""
    op_fn = lookup_cascade_op(op_name)
    assert _then_native_desc(op_name, {}, op_fn) == {"op": op_name}


@pytest.mark.parametrize("key,value", [("max_denominator", 100),
                                       ("fine_scale", 1000)])
def test_a_REAL_keyword_only_option_still_nativizes(key, value):
    """``best_rational_signed`` genuinely declares these. They must survive —
    they are exactly the shape (keyword-only, plausible name) most at risk from
    an over-eager signature check."""
    op_fn = lookup_cascade_op("best_rational_signed")
    desc = _then_native_desc("best_rational_signed", {key: value}, op_fn)
    assert desc == {"op": "best_rational_signed", key: value}


def test_a_mix_of_valid_and_invalid_keys_defers():
    """One bad key poisons the stage — a partial nativization would drop it."""
    op_fn = lookup_cascade_op("best_rational_signed")
    assert _then_native_desc("best_rational_signed",
                             {"max_denominator": 100, "bogus": 2}, op_fn) is None


def test_op_accepts_is_permissive_where_it_cannot_know():
    """An unreadable signature is NOT evidence of rejection. Guessing "no"
    there would defer valid chains and quietly delete the native path for any
    op whose signature cannot be introspected."""
    assert _op_accepts(object(), "anything") is True

    def var_kw(**kwargs):
        return kwargs

    assert _op_accepts(var_kw, "literally_anything") is True


def test_positional_only_is_not_accepted_as_a_keyword():
    """A positional-only parameter cannot be passed by name, so naming it must
    defer — the name EXISTING is not the same as it being bindable."""
    def pos_only(a, /, b=1):
        return a + b

    assert _op_accepts(pos_only, "a") is False
    assert _op_accepts(pos_only, "b") is True


def test_the_end_to_end_behaviour_through_the_public_surface():
    """Pinned through ``.then()``, not the helper — the helper's ``op_fn``
    parameter defaults to None (skipping the check), so a caller that forgot to
    pass it would still pass a helper-level test while shipping the defect."""
    from srmech.dsl import chain
    with pytest.raises(TypeError):
        chain().then("autocorrelation", bogus=1).run([1.0, 2.0, 3.0])
    # and the valid call still works, natively or not
    assert chain().then("autocorrelation").run([1.0, 2.0, 3.0]) is not None
