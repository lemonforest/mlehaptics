"""rc464 (`#T1188`) — the CDRegister ``[class]`` through the bare-C make_class ENGINE.

This is the OWED PEER the rc297 conversion left behind, and the gate the removal
of the 16-slot register stands on. A bare-C host (no Python) resolves the packaged
``cd_register.toml`` descriptor and RUNS the register's declared methods natively:
``srmech_make_class_run`` (descriptor TEXT in) and ``srmech_run_class_method``
(class NAME in, resolved through the compiled-in registry). Both exports are
driven here, because a bare-C host reaches the class through the second one.

WHAT "FULL C PARITY" MEANS, PRECISELY. It is the tree's own rc201 contract: every
descriptor method either DISPATCHES byte-identically to the pure ``CatalogClass``
or is a DECLARED, TESTED defer. Both halves are asserted below — an untested
defer is indistinguishable from a thunk that silently returns the wrong shape,
and a dispatch nobody compares is indistinguishable from a laundered gap.

WHY dim 256 IS NOT DECORATION. The thunk family this replaces was written against
a SIXTEEN-slot register with a hard-coded ``SEDENION:e`` address namespace, and
its sharper wall was not the slot count but the FOUR separate two-digit slot-key
emitters. Slots 100..255 exist only at dim 128/256, so a half-migrated emitter
set would defer or assert exactly there and nowhere else. Every dim-256 case here
occupies slots straddling that boundary — ``{0, 7, 99, 100, 128, 255}`` — so a
regression to two digits is caught by content, not by a count.

WHY dim 16 / ``namespace="SEDENION"`` IS THE OTHER HALF. That spelling IS the
16-slot register, and the golden fixture recorded from the shipped class before
its removal is checked here against the C ENGINE's own emit — not just against
the pure Python class. Byte-identity to the pure peer and byte-identity to the
recorded bytes are different claims, and the second one is what says the C engine
reproduces a register that no longer exists in this tree.

numpy-free (stdlib json + base64 + srmech), per
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``.
"""
from __future__ import annotations

import base64
import json

import pytest

from srmech import _native
from srmech.amsc.format import sha256_bytes
from srmech.cascade import CD_DENSE_MAX_DIM, hamming_encode
from srmech.cascade.cd_register import CDRegister
from srmech.dsl import make_class
from srmech.dsl._class_catalog import CLASS_CATALOG_DIR, CatalogClass

from _golden_sedenion import load_golden

pytestmark = pytest.mark.skipif(
    not _native.has_native_make_class(),
    reason="the make_class engine C peer is not built",
)

_CDR_TOML = (CLASS_CATALOG_DIR / "cd_register.toml").read_text(encoding="utf-8")

#: The address-buffer cap in ``srmech_make_class.c`` (``MC_CDR_ADDR_MAX``). A
#: namespace needs room for itself plus ``":e255"`` and a NUL, so 58 is the
#: longest that can dispatch and 59 is the first that must DEFER. Both sides of
#: that edge are asserted: a cap nobody probes from the far side is a cap that
#: could be off by one in the direction that TRUNCATES, and a truncated namespace
#: mints a DIFFERENT address and returns wrong content silently.
_NS_CAP = 58


def _norm(x):
    """JSON-native normalise — the shape ``srmech_mcp_serialise_result`` emits."""
    if isinstance(x, bytes):
        return base64.b64encode(x).decode("ascii")
    if isinstance(x, dict):
        return {str(k): _norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_norm(e) for e in x]
    return x


def _wire(reg: CDRegister) -> dict:
    """The JSON-native seven-field state a bare-C host threads."""
    return {
        "dim": reg.dim,
        "D": reg.D,
        "namespace": reg.namespace,
        "codebook": {k: base64.b64encode(v).decode("ascii")
                     for k, v in reg.codebook.items()},
        "slots": {str(k): [v[0], v[1]] for k, v in reg._slots.items()},
        "coupling": reg._coupling,
        "error_correction": reg._error_correction,
    }


def _pyfields(reg: CDRegister) -> dict:
    """The same state as PYTHON values, for the pure CatalogClass oracle."""
    return {
        "dim": reg.dim,
        "D": reg.D,
        "namespace": reg.namespace,
        "codebook": dict(reg.codebook),
        "slots": {k: (v[0], v[1]) for k, v in reg._slots.items()},
        "coupling": reg._coupling,
        "error_correction": reg._error_correction,
    }


def _run_toml(method: str, fields: dict, args: dict):
    ok, text = _native.make_class_run_c(_CDR_TOML, method, fields, args)
    return ok, (json.loads(text) if text is not None else None)


def _run_name(method: str, fields: dict, args: dict):
    ok, text = _native.run_class_method_c("CDRegister", method, fields, args)
    return ok, (json.loads(text) if text is not None else None)


def _pure(reg: CDRegister, method: str, args: dict):
    """Run the method on the PURE CatalogClass and normalise its answer."""
    inst = make_class("CDRegister")(**_pyfields(reg))
    out = getattr(inst, method)(**args)
    result = out.fields if isinstance(out, CatalogClass) else out
    return _norm(result), _norm(inst.fields)


def _sed16(D: int = 256) -> CDRegister:
    """The subsuming spelling of the removed 16-slot register."""
    return CDRegister(16, D=D, namespace="SEDENION", coupling=True,
                      error_correction=True)


def _reg16() -> CDRegister:
    r = _sed16()
    r.write(0, "alpha")
    r.write(3, "beta", sign=-1)
    r.write(6, "gamma")
    return r


def _reg256() -> CDRegister:
    """dim 256, occupying slots on BOTH sides of the two-digit wall."""
    r = CDRegister(256, D=256)
    for slot, key, sign in [(0, "a", 1), (7, "b", -1), (99, "c", 1),
                            (100, "d", -1), (128, "e", 1), (255, "f", -1)]:
        r.write(slot, key, sign=sign)
    return r


# ── the subsumption core DISPATCHES, at both rungs, through both exports ─────

#: Every method the removed 16-slot register had, plus the two block accessors
#: and ``element``. Each entry is (method, args-factory).
_CORE = [
    ("slots", lambda r: {}),
    ("working_block", lambda r: {}),
    ("carry_block", lambda r: {}),
    ("element", lambda r: {}),
    ("materialize", lambda r: {}),
    ("navmap", lambda r: {"j": 1}),
    ("navigate", lambda r: {"j": 1}),
]


@pytest.mark.parametrize("method,mkargs", _CORE, ids=[m for m, _ in _CORE])
@pytest.mark.parametrize("make", [_reg16, _reg256], ids=["dim16", "dim256"])
def test_core_methods_dispatch_byte_identical(make, method, mkargs):
    reg = make()
    args = mkargs(reg)
    ok, got = _run_toml(method, _wire(reg), args)
    assert ok, f"CDRegister.{method} must DISPATCH at dim {reg.dim}, not defer"
    exp_result, exp_fields = _pure(reg, method, args)
    assert got["result"] == exp_result
    assert got["fields"] == exp_fields


@pytest.mark.parametrize("make,slots", [(_reg16, (0, 3, 6)),
                                        (_reg256, (0, 7, 99, 100, 128, 255))],
                         ids=["dim16", "dim256"])
def test_read_chain_dispatches_at_every_occupied_slot(make, slots):
    """The 2-stage chain (unbind -> clean). Every occupied slot is read, because
    the dim-256 wall is a per-SLOT property: a two-digit emitter answers for
    slot 99 and fails for slot 100, and one probe on either side alone would
    report a half-migrated emitter set as healthy."""
    reg = make()
    for slot in slots:
        ok, got = _run_toml("read", _wire(reg), {"slot": slot})
        assert ok, f"read(slot={slot}) must DISPATCH at dim {reg.dim}"
        exp_result, _ = _pure(reg, "read", {"slot": slot})
        assert got["result"] == exp_result, f"read(slot={slot}) at dim {reg.dim}"


def test_read_of_an_empty_register_short_circuits_like_pure():
    """The read chain's short-circuit: stage 1 emits NONE for an empty register
    and stage 2 turns that into ``(None, +1)``. Carried over from the coverage
    the 16-slot engine module had -- an empty register is the one input where
    the chain's two stages disagree about what "no answer" looks like, and a
    thunk that returned NULL instead would DEFER a case pure ANSWERS."""
    empty = CDRegister(16, D=256, namespace="SEDENION")
    ok, got = _run_toml("read", _wire(empty), {"slot": 0})
    assert ok, "read on an empty register must DISPATCH, not defer"
    inst = make_class("CDRegister")(**_pyfields(empty))
    assert got["result"] == _norm(inst.read(slot=0)) == [None, 1]
    assert got["fields"] == _norm(inst.fields)


@pytest.mark.parametrize("make", [_reg16, _reg256], ids=["dim16", "dim256"])
def test_write_mutates_both_fields_byte_identical(make):
    reg = make()
    slot = reg.dim - 1
    ok, got = _run_toml("write", _wire(reg),
                        {"slot": slot, "key": "zz", "sign": -1})
    assert ok, f"write must DISPATCH at dim {reg.dim}"
    exp_result, _ = _pure(reg, "write", {"slot": slot, "key": "zz", "sign": -1})
    # The mutates route emits the return value plus the POST-route field state.
    inst = make_class("CDRegister")(**_pyfields(reg))
    inst.write(slot=slot, key="zz", sign=-1)
    assert got["result"] == exp_result
    assert got["fields"] == _norm(inst.fields)


@pytest.mark.parametrize("j", [0, 1, 7, 15])
def test_navigate_carries_all_seven_fields_at_dim16(j):
    """``returns="self"`` sits at EXACTLY ``MC_MAX_BINDS = 8`` (seven fields plus
    ``j``). An over-cap method DEFERS silently, so the dispatch assertion here is
    the only thing standing between that zero headroom and a wrong answer."""
    reg = _reg16()
    ok, got = _run_toml("navigate", _wire(reg), {"j": j})
    assert ok, "navigate must DISPATCH — 8 binds is AT the cap, not over it"
    exp_result, exp_fields = _pure(reg, "navigate", {"j": j})
    assert got["result"] == exp_result
    assert set(got["result"]) == {"dim", "D", "namespace", "codebook", "slots",
                                  "coupling", "error_correction"}
    assert got["fields"] == exp_fields          # self untouched


@pytest.mark.parametrize("j", [0, 1, 100, 255])
def test_navigate_routes_high_slots_at_dim256(j):
    reg = _reg256()
    ok, got = _run_toml("navigate", _wire(reg), {"j": j})
    assert ok
    exp_result, _ = _pure(reg, "navigate", {"j": j})
    assert got["result"] == exp_result
    assert got["result"]["namespace"] == "CD256"


def test_opt_layer_methods_dispatch_when_the_gate_is_open():
    reg = _reg16()                               # coupling + EC both True
    for method, args in [("carry", {"overflow_bits": [1, 0, 1, 1]}),
                         ("correct", {"codeword": [1, 0, 1, 1, 0, 1, 0]})]:
        ok, got = _run_toml(method, _wire(reg), args)
        assert ok, f"{method} must DISPATCH on a register with the gate open"
        exp_result, _ = _pure(reg, method, args)
        assert got["result"] == exp_result


def test_opt_layer_methods_defer_when_the_gate_is_shut():
    """A bare register RAISES on the OPT layers. C cannot raise, so the only
    honest answer is DEFER — and the pure class then produces the ValueError.
    Binding these to the UNGATED free ops would have dispatched an answer where
    the class raises, which is a behaviour fork wearing the name "conversion"."""
    bare = CDRegister(16, D=256)                 # both gates shut
    inst = make_class("CDRegister")(**_pyfields(bare))
    for method, args in [("carry", {"overflow_bits": [1, 0, 1, 1]}),
                         ("correct", {"codeword": [1, 0, 1, 1, 0, 1, 0]}),
                         ("couple_working", {"vals": [1.0, 2.0]}),
                         ("uncouple_working", {"word": [1.0] * 8})]:
        ok, _ = _run_toml(method, _wire(bare), args)
        assert not ok, f"{method} must DEFER on a bare register (pure raises)"
        with pytest.raises(ValueError):
            getattr(inst, method)(**args)


def test_is_navigable_dispatches_up_to_the_dense_cap():
    """Every power-of-two rung UP TO AND INCLUDING the cap, which is the whole
    point of the name.

    ⚠️ THIS TEST PROBED ONLY dim 16 UNTIL rc464 CLOSED IT. It was named for a
    cap of 64 and never passed a direction longer than 16, so it could not see
    that the engine was in fact declining from THIRTY-THREE elements up --
    ``mc_parse_map`` carved the JSON parser a hand-rolled ``8 * len + 4096``
    workspace against a measured need of ~28x, and an OVERFLOW there is
    indistinguishable from a declared defer at the call boundary. Its sibling
    below asserts the dim-256 defer and attributes it to the dense kernel, which
    is correct; between the two, a boundary of 64 was certified by probing 16 and
    256 and nothing in between. The cap itself is the one value that had to be
    exercised, and it is now the loop's last entry.
    """
    for dim in (2, 4, 8, 16, 32, CD_DENSE_MAX_DIM):
        reg = CDRegister(dim, D=256)
        reg.write(0, "alpha")
        one_hot = [0] * dim
        one_hot[1] = 1
        ok, got = _run_toml("is_navigable", _wire(reg), {"direction": one_hot})
        assert ok, (
            f"is_navigable must DISPATCH at dim {dim} — at or below "
            f"SRMECH_CD_DENSE_MAX_DIM = {CD_DENSE_MAX_DIM}, where the "
            f"dense kernel answers. A defer here is the make_class arena "
            f"under-carving the JSON parse, NOT a capability boundary."
        )
        exp_result, _ = _pure(reg, "is_navigable", {"direction": one_hot})
        assert got["result"] == exp_result is True


def test_hamming_methods_dispatch_past_the_32_element_wall():
    """``correct`` and ``carry`` take LISTS, and the arena cliff was on length.

    The same ``8 * len + 4096`` carve deferred every bind list past 32 compact
    elements, so these two silently fell back to pure at codeword length 63 and
    at 57 data bits — against a declared ``MC_HAMMING_MAX`` of 65535. Both
    lengths straddle the old wall, so this fails if the carve regresses.
    """
    reg = CDRegister(16, D=256, error_correction=True)
    for n in (5, 6, 7):                      # codewords 31, 63, 127
        data = [(i % 2) for i in range((1 << n) - 1 - n)]
        codeword = list(hamming_encode(data, n))

        ok, got = _run_toml("carry", _wire(reg),
                            {"overflow_bits": data, "n": n})
        assert ok, (
            f"carry must DISPATCH at {len(data)} data bits (n={n}); a defer is "
            f"the JSON-parse arena, not MC_HAMMING_MAX = 65535"
        )
        assert got["result"] == codeword

        flipped = list(codeword)
        flipped[0] ^= 1                      # one Class-K pin-slot sign-flip
        ok, got = _run_toml("correct", _wire(reg), {"codeword": flipped})
        assert ok, (
            f"correct must DISPATCH at codeword length {len(flipped)} (n={n})"
        )
        exp_result, _ = _pure(reg, "correct", {"codeword": flipped})
        assert got["result"] == exp_result


# ── the DECLARED defers — each asserted, with its reason on the test ─────────

def test_declared_defer_is_navigable_above_the_dense_cap():
    """The dense kernel ``srmech_sedenion_is_navigable`` is the library's one
    QUADRATIC buffer and declines above ``SRMECH_CD_DENSE_MAX_DIM = 64``.

    This is a defer of the ENGINE COMPOSITION, not of the capability: in process
    the exact-rational nullspace route dispatches to ``srmech_qmat_nullspace``,
    so the answer is C-computed at every rung. What a bare-C host lacks at
    128/256 is the composition over that kernel — a named rc464 follow-up whose
    arena size and wall-clock are unmeasured."""
    reg = _reg256()
    one_hot = [0] * 256
    one_hot[1] = 1
    ok, _ = _run_toml("is_navigable", _wire(reg), {"direction": one_hot})
    assert not ok
    # ...and the pure peer still ANSWERS, which is what makes this a defer and
    # not a gap. A one-hot direction is navigable at every rung.
    assert make_class("CDRegister")(**_pyfields(reg)).is_navigable(
        direction=one_hot) is True


def test_declared_defer_float_working_word():
    """``couple_working`` / ``uncouple_working`` defer even with the gate OPEN.

    The reason on record through rc463 — "the mval carrier cannot emit the float
    working word byte-identically" — is STALE: rc331 emits a within-tol float MAT
    and rc335 emits bignums. rc464 restates it as a SCOPE defer: the Q61-exact
    coupler ``srmech_hypercomplex_couple_q61`` plus the rc331 float emit make it
    dissolvable, and doing that inside an ABI-moving rc is scope creep. Recorded
    as a decision, not discovered as a limit."""
    reg = _reg16()                               # coupling=True
    for method, args in [("couple_working", {"vals": [1.0, 2.0]}),
                         ("uncouple_working", {"word": [1.0] * 8})]:
        ok, _ = _run_toml(method, _wire(reg), args)
        assert not ok, f"{method} is a DECLARED defer; it must not dispatch"
        # the pure peer answers, so this is inform-don't-limit, never a failure
        assert getattr(make_class("CDRegister")(**_pyfields(reg)), method)(**args)


def test_declared_defer_exact_q_carrier_chains():
    """``norm`` / ``conjugate`` / ``multiply`` / ``add`` defer as CHAINS.

    Their first stage (``element``) dispatches — asserted in ``_CORE`` — and
    their terminal ops are the exact-Q bigint kernels ``srmech_cd_qnorm_sq`` /
    ``_qconjugate`` / ``srmech_cd_mult`` / ``_qadd``, which need the intermediate
    Q-vector to round-trip through the BIGINT carrier. That plumbing is a named
    follow-up. Nothing REGRESSES here: the 16-slot register had no
    carrier-arithmetic surface at all, so these never dispatched."""
    reg = _reg16()
    other = _wire(_reg16())
    for method, args in [("norm", {}), ("conjugate", {}),
                         ("multiply", {"other": other}), ("add", {"other": other})]:
        ok, _ = _run_toml(method, _wire(reg), args)
        assert not ok, f"{method} is a DECLARED defer; it must not dispatch"


def test_declared_defer_namespace_over_the_address_buffer():
    """A namespace too long for the address buffer DEFERS rather than truncates.

    A truncated namespace would mint a DIFFERENT address and return the wrong
    content with no error at all — the worst failure shape a storage layer has.
    Both sides of the edge are probed so the cap cannot drift into truncation."""
    fits = CDRegister(4, D=256, namespace="N" * _NS_CAP)
    fits.write(0, "k")
    ok, got = _run_toml("materialize", _wire(fits), {})
    assert ok, f"a {_NS_CAP}-char namespace fits and must dispatch"
    exp_result, _ = _pure(fits, "materialize", {})
    assert got["result"] == exp_result

    over = CDRegister(4, D=256, namespace="N" * (_NS_CAP + 1))
    over.write(0, "k")
    ok, _ = _run_toml("materialize", _wire(over), {})
    assert not ok, "a namespace past the buffer must DEFER, never truncate"
    assert over.materialize() is not None          # pure still answers


# ── the scalar defaults resolve identically in both projections ──────────────

@pytest.mark.parametrize("method,args", [
    ("navigate", {"j": 1}),
    ("materialize", {}),
    ("slots", {}),
    ("element", {}),
])
def test_dim_only_field_state_matches_pure(method, args):
    """A class constructed with ``dim=`` alone arrives with ``D`` / ``namespace``
    / both flags absent. The C thunks resolve them to ``DEFAULT_D`` / ``CD{dim}``
    / ``False`` — the same rule ``_cdr_defaults`` applies — so the two
    projections cannot drift apart on a state the contract makes reachable."""
    fields = {"dim": 8, "slots": {"0": ["k", 1], "5": ["m", -1]}}
    ok, got = _run_toml(method, fields, args)
    assert ok, f"{method} must dispatch on a dim-only field state"
    inst = make_class("CDRegister")(dim=8, slots={0: ("k", 1), 5: ("m", -1)})
    out = getattr(inst, method)(**args)
    expected = out.fields if isinstance(out, CatalogClass) else out
    assert got["result"] == _norm(expected)


def test_dim_only_navigate_resolves_D_and_namespace_in_the_emitted_state():
    """The resolved values must reach the NEW instance, not just the computation:
    ``returns="self"`` rebuilds from the emitted dict, so a ``D`` emitted as
    ``null`` would silently un-default the routed register."""
    ok, got = _run_toml("navigate", {"dim": 8}, {"j": 1})
    assert ok
    assert got["result"]["D"] == 8192
    assert got["result"]["namespace"] == "CD8"
    assert got["result"]["coupling"] is False
    assert got["result"]["error_correction"] is False


# ── the NAME-resolved export a bare-C host actually uses ─────────────────────

@pytest.mark.skipif(not _native.has_native_run_class_method(),
                    reason="the run_class_method C peer is not built")
@pytest.mark.parametrize("method,args", [
    ("slots", {}), ("materialize", {}), ("navmap", {"j": 1}),
    ("navigate", {"j": 1}), ("read", {"slot": 0}), ("element", {}),
])
def test_name_resolved_export_agrees_with_the_descriptor_export(method, args):
    """``srmech_run_class_method`` resolves "CDRegister" through the COMPILED-IN
    registry — the path a bare-C host takes, and the one that proves the
    descriptor baked into ``srmech_class_registry.c`` is this descriptor."""
    reg = _reg16()
    ok_name, got_name = _run_name(method, _wire(reg), args)
    ok_toml, got_toml = _run_toml(method, _wire(reg), args)
    assert ok_name and ok_toml
    assert got_name["class"] == "CDRegister"
    assert got_name["method"] == method
    assert got_name["result"] == got_toml["result"]
    assert got_name["fields"] == got_toml["fields"]


@pytest.mark.skipif(not _native.has_native_run_class_method(),
                    reason="the run_class_method C peer is not built")
def test_name_resolved_export_reaches_dim_256():
    reg = _reg256()
    ok, got = _run_name("read", _wire(reg), {"slot": 255})
    assert ok
    exp_result, _ = _pure(reg, "read", {"slot": 255})
    assert got["result"] == exp_result


# ── the removed register, reproduced BY THE C ENGINE from recorded bytes ─────

def _golden_storage():
    return load_golden()["storage"]


@pytest.mark.parametrize("idx", range(6))
def test_engine_reproduces_the_recorded_register_bytes(idx):
    """The C ENGINE's ``materialize`` at ``dim=16, namespace="SEDENION"`` equals
    the bytes recorded from the shipped 16-slot register before its removal.

    This is a different claim from byte-identity with the pure ``CDRegister``,
    which the rest of this module asserts. Two registers can agree with each
    other and BOTH differ from the class they replace; only the recorded digest
    can say they do not. The record is data, so it cannot acquire the subject's
    failure modes — it is not running."""
    rec = _golden_storage()[idx]
    reg = _sed16(D=rec["D"])
    for slot, key, sign in rec["writes"]:
        reg.write(slot, key, sign=sign)
    ok, got = _run_toml("materialize", _wire(reg), {})
    assert ok, "materialize must DISPATCH at the subsuming dim-16 spelling"
    blob = base64.b64decode(got["result"])
    assert len(blob) == rec["materialize_bytes"]
    assert sha256_bytes(blob) == rec["materialize_sha256"], (
        f"the C engine's materialize at D={rec['D']} ({rec['label']}) does not "
        f"reproduce the recorded 16-slot register")


@pytest.mark.parametrize("idx", range(6))
def test_engine_read_chain_reproduces_the_recorded_reads(idx):
    """Every one of the sixteen recorded ``read`` answers, through the C chain."""
    rec = _golden_storage()[idx]
    reg = _sed16(D=rec["D"])
    for slot, key, sign in rec["writes"]:
        reg.write(slot, key, sign=sign)
    fields = _wire(reg)
    for slot_s, expected in sorted(rec["reads"].items(), key=lambda kv: int(kv[0])):
        ok, got = _run_toml("read", fields, {"slot": int(slot_s)})
        assert ok
        assert got["result"] == expected, (
            f"read({slot_s}) at D={rec['D']} ({rec['label']}): C engine "
            f"{got['result']} != recorded {expected}")


@pytest.mark.parametrize("j", range(16))
def test_engine_navmap_reproduces_the_recorded_navmaps(j):
    """All sixteen recorded navmaps, through the C engine at the dim-16 spelling.
    ``srmech_cd_navmap`` is the dim-general peer of the removed
    ``srmech_sedenion_navmap``; this is where "bit-identical at dim 16" stops
    being a header sentence and becomes a comparison against recorded bytes."""
    rec = load_golden()["navmap"][j]
    assert rec["j"] == j and rec["dim"] == 16
    ok, got = _run_toml("navmap", _wire(_reg16()), {"j": j})
    assert ok
    assert got["result"] == rec["map"]


def test_the_golden_comparison_actually_fires():
    """The negative control. Every assertion above compares the engine to a
    recorded digest; if the comparison were vacuous — a digest read from the
    wrong record, a result that is always ``None`` — the whole block would pass
    while measuring nothing. Perturbing one recorded byte must make it fail."""
    rec = _golden_storage()[0]
    reg = _sed16(D=rec["D"])
    for slot, key, sign in rec["writes"]:
        reg.write(slot, key, sign=sign)
    ok, got = _run_toml("materialize", _wire(reg), {})
    assert ok
    blob = bytearray(base64.b64decode(got["result"]))
    blob[0] ^= 0x01                                # Class-K flip of one bit
    assert sha256_bytes(bytes(blob)) != rec["materialize_sha256"]
