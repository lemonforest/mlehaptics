"""Contract A — a caller's decimal TEXT is the exact rational it already names.
rc479, `#T1188`.

Ten gates. Each one states what it does NOT prove, because that is where the
last four releases lost their green: a gate whose scope is unstated reads as
covering the thing beside it.

  G1        the A1 digit bound at BOTH front doors, with the five ZERO tokens
            as ACCEPTANCES and a planted-mutation proof
  G1-UNRED  the bound is on the UNREDUCED pair — `5e-4300` refuses
  G2        the verdict witness: a boundary EQUALITY flip, with the control
            that makes it a measurement
  G3        strict zero on a front-door bypass that reads CALLER text, with
            the two adapter `_coerce` sites named as exemptions
  G4        `float(Q(text))` is bit-identical to `float(text)` over the LIVE
            corpus — the invariant every float consumer rides
  G5/G8     the C node's OWN verdicts: the same refusals, the same
            acceptances, the zero collapse intact, the syntax errors intact
  G-MIX     a partially-exact sample: the declared chain and the shipped op
            agree bit-for-bit
  G-SIEVE   the ONE place this release turns an ANSWER into an EXCEPTION
  G-FLOATARM what the rc420 gate STOPS proving, pinned so the collapse cannot
            recur silently
  G-DIGEST  a committed attestation digest does not move

Integer oracles only: exactness is decided by cross-multiplication on Python
ints and bit-identity by ``struct.pack``. No ``math.*``, no ``fractions``, no
numpy, no ``abs()``.
"""

from __future__ import annotations

import ast
import json
import pathlib
import struct
import sys

import pytest

from srmech import _json, _native, _toml
from srmech.amsc.format import canonical_json_default, sha256_bytes
from srmech.math.q import (MAX_DEC_DIGITS, Q, decimal_text_to_pair,
                           parse_float_exact, to_q)

PY_DIR = pathlib.Path(__file__).resolve().parent.parent
PKG = PY_DIR / "srmech"

#: The FIVE legal spellings of zero whose significand is all zeros. Every one
#: parses today through ``float``, ``json`` AND ``tomllib`` (measured), so a
#: reader that refused them on the strength of their exponent would be a live
#: behaviour regression. They are here because NEITHER planning lane's token
#: table contained a zero-mantissa case, which is exactly how the defect
#: survived to the build.
ZERO_TOKENS = ("0e999999999", "0e-999999999", "-0e999999999",
               "0.0e999999999", "0." + "0" * 5000)

#: Tokens the A1 bound REFUSES, in both projections.
REFUSED = ("1e1000000", "1e3000000", "1e4300", "1e-4300", "5e-4300")

#: Tokens inside the bound. `1e4299` is the last acceptance and `1e4300` the
#: first refusal, so the pair is the boundary rather than a sample near it.
ACCEPTED = ("0.1", "1e400", "1e-400", "1e4299", "1e-4299", "1.0",
            "0." + "3" * 4299)


# ─────────────────────────────────────────────────────────────────────────
# G1 — the A1 bound at both front doors
# ─────────────────────────────────────────────────────────────────────────
def _loads_both(token):
    """(json result, toml result) for one numeric token, via the front doors."""
    return (_json.loads("{\"x\": %s}" % token)["x"],
            _toml.loads("x = %s\n" % token)["x"])


@pytest.mark.parametrize("token", REFUSED)
def test_g1_the_bound_refuses_in_both_front_doors(token):
    """Past :data:`MAX_DEC_DIGITS`, both doors raise rather than round.

    DOES NOT PROVE that the C node refuses the same token — that is G5, and
    the two are separate because the C node can DECLINE for width where
    Python refuses for the bound, which is agreement on the answer and
    disagreement on the route.
    """
    with pytest.raises(ValueError):
        _json.loads("{\"x\": %s}" % token)
    with pytest.raises(ValueError):
        _toml.loads("x = %s\n" % token)


@pytest.mark.parametrize("token", ACCEPTED)
def test_g1_inside_the_bound_both_doors_read_it_exactly(token):
    """Inside the bound the reading is EXACT, at both doors, and equal."""
    j, t = _loads_both(token)
    assert isinstance(j, Q), (token, type(j).__name__)
    assert isinstance(t, Q), (token, type(t).__name__)
    assert j == t and j.numerator == t.numerator, token


@pytest.mark.parametrize("token", ZERO_TOKENS)
def test_g1_the_zero_collapse_keeps_five_legal_tokens_accepted(token):
    """An all-zero significand names ZERO whatever its exponent says.

    The bound is a RESOURCE bound: for a zero significand ``int(digits)`` is
    never called and ``10**e`` is never built, so there is nothing to bound.
    A signed zero stays a ``float`` (rule Z1 — ``Q`` has no signed zero) and
    an unsigned one is ``Q(0, 1)``; either way it is ACCEPTED.

    DOES NOT PROVE the completeness of the false-positive class. That rests
    on the closed form (``digits`` carries no leading zero, so
    ``len(digits) + e`` and ``1 + (-e)`` are exact counts and never
    overcount), argued rather than swept.
    """
    j, t = _loads_both(token)
    for got in (j, t):
        if isinstance(got, float):
            assert struct.pack("<d", got) == struct.pack("<d", -0.0), token
        else:
            assert got == Q(0, 1), (token, got)


def test_g1_malformed_exponents_stay_errors():
    """The zero collapse runs AFTER the exponent's syntax check.

    Hoisting it above the validation would start accepting `0e` and `0eX`.
    This is the other half of the ordering the C node also enforces.
    """
    for token in ("0e", "0eX", "1e", "1e+"):
        assert decimal_text_to_pair(token) is None, token
        with pytest.raises(ValueError):
            _toml.loads("x = %s\n" % token)


def test_g1_is_not_vacuous_planted_mutation():
    """A reader with the bound RAISED must accept what the real one refuses.

    Without this the G1 rows above would pass against a reader that refused
    nothing at all in a range no token reaches.
    """
    import srmech.math.q as qmod
    saved = qmod.MAX_DEC_DIGITS
    try:
        qmod.MAX_DEC_DIGITS = 10 ** 9
        assert qmod.decimal_text_to_pair("1e1000000") is not None, (
            "the mutated reader still refuses — the bound is not the "
            "variable, so G1 is measuring something else")
    finally:
        qmod.MAX_DEC_DIGITS = saved
    with pytest.raises(ValueError):
        qmod.decimal_text_to_pair("1e1000000")


def test_g1_unreduced_is_the_bound_not_reduced():
    """``5e-4300`` REFUSES though its REDUCED denominator would fit.

    The bound is computed on the SCAN form, before anything is built, so it
    is the unreduced pair it bounds: `5e-4300` has denominator `10**4300`
    (4301 digits) unreduced and `2*10**4299` (4300) reduced. Written down
    because the C node computes the same thing and the two projections must
    refuse the SAME token — which G5 then checks.
    """
    with pytest.raises(ValueError):
        decimal_text_to_pair("5e-4300")
    # And the REDUCED pair really would have fitted. Decided by integer
    # COMPARISON rather than by `len(str(...))`, because CPython's own
    # int-to-str limit is the very bound under test and stringifying a
    # 4301-digit integer raises inside the assertion.
    unreduced_den = 10 ** 4300              # exactly MAX_DEC_DIGITS + 1 digits
    reduced_den = 2 * 10 ** 4299            # exactly MAX_DEC_DIGITS digits
    assert 10 ** (MAX_DEC_DIGITS - 1) <= reduced_den < 10 ** MAX_DEC_DIGITS
    assert 10 ** MAX_DEC_DIGITS <= unreduced_den < 10 ** (MAX_DEC_DIGITS + 1)
    # the value is the same either way — 5/10**4300 == 1/(2*10**4299)
    assert 5 * reduced_den == 1 * unreduced_den


def test_g1_to_q_widening_is_additive_and_exact_scalar_is_not_widened():
    """``to_q`` gains ``str``; ``exact_scalar`` deliberately does not.

    ``to_q`` is an explicit COERCION and ``exact_scalar`` is a TYPE TEST on
    an already-parsed operand; widening the latter would let a stray string
    operand silently elect the exact route.
    """
    from srmech.math.q import exact_scalar
    assert to_q("0.1") == Q(1, 10)
    assert to_q("1/10") == Q(1, 10)
    assert to_q("1_000.000_1") == Q(10000001, 10000)
    assert to_q("-0.0") == Q(0, 1)          # Z1 governs the PARSER, not this
    assert to_q(-0.0) == Q(0, 1)
    with pytest.raises(ValueError):
        to_q("nan")
    assert exact_scalar("0.1") is None, "exact_scalar must NOT be widened"
    assert exact_scalar(Q(1, 10)) == Q(1, 10), "the control must fire"


# ─────────────────────────────────────────────────────────────────────────
# G2 — the verdict witness
# ─────────────────────────────────────────────────────────────────────────
def test_g2_the_verdict_witness_is_a_boundary_equality_flip():
    """One op, one threshold, two spellings of one tenth, two verdicts.

    ``hv`` scores an exact DC of ``2/20 = 1/10``. JSON's ``0.1`` is exactly
    ``3602879701896397 / 2**55``; cross-multiplying against ``1/10`` gives
    ``36028797018963968`` against ``36028797018963970``, so the exact score
    is STRICTLY LESS than the float threshold while being EXACTLY EQUAL to
    the exact one. That is a boundary-equality flip, not a drift.

    THE CONTROL IS WHAT MAKES IT A MEASUREMENT: ``0.5`` is exact in binary64,
    and both spellings of it agree — so the CARRIER alone does not move the
    verdict and the flip at ``0.1`` is the ROUNDING.

    DOES NOT PROVE anything about the other 731 registry entries; it is one
    op's one boundary.
    """
    from srmech.mcp._tools import invoke_tool
    hv = [1] * 11 + [-1] * 9

    def verdict(threshold):
        r = invoke_tool("srmech.music.harmonics.classify_chirality_harmonic",
                        {"hv": hv, "dc_threshold": threshold})
        return r["harmonic"] if isinstance(r, dict) else r

    assert verdict(0.1) == 2, "the float threshold's verdict moved"
    assert verdict([1, 10]) == 1, "the exact pair's verdict moved"
    assert verdict(Q(1, 10)) == 1, "the exact carrier's verdict moved"
    assert verdict(0.5) == 2 and verdict([1, 2]) == 2, (
        "the CONTROL moved — 0.5 is exact in binary64, so its two spellings "
        "must agree; if they do not, the carrier is moving the verdict and "
        "the 0.1 row proves nothing about rounding")
    # the integers, so the flip is arithmetic rather than reported
    n, d = (0.1).as_integer_ratio()
    assert 1 * d < n * 10, "1/10 must be strictly below the double 0.1"
    assert n * 10 - 1 * d == 2, "the cross-product gap is 2 units"


# ─────────────────────────────────────────────────────────────────────────
# G3 — no front-door bypass reads caller text unhooked
# ─────────────────────────────────────────────────────────────────────────
#: Files that call stdlib ``json``/``tomllib`` on CALLER text and are EXEMPT
#: by name, each with the reason. A wildcard here would either break the
#: machine-written sites or force a ceiling, so the exemption is a roster.
_G3_EXEMPT = {
    # K1b — MACHINE-WRITTEN, lossless by construction: these re-read doubles
    # that srmech's own integer-Ryu writer emitted to match `repr`, so
    # re-reading them exactly is the same value either way.
    "srmech/_native/__init__.py",
    "srmech/bus/_event.py",
    "srmech/bus/_client.py",
    "srmech/bus/_server.py",
    # OUT-OF-CLASS per the census: schema TEXT and the C lifecycle handshake,
    # neither of which is a caller's numeric literal.
    "srmech/mcp/_tools.py",
    "srmech/mcp/_server.py",
    # SHAPE-ONLY: the Bio-TOTP wrong-key detector parses a decrypted payload
    # solely to ask "is this a JSON object at all", and discards it. No
    # numeric value is read, so the reader it uses cannot change an answer.
    # Named rather than hooked, because hooking it would put contract A's
    # refusal on a path whose whole job is to survive garbage.
    "srmech/bus/_bio_totp.py",
}


def _bypass_sites():
    """(file, lineno) for every stdlib json/tomllib load with no parse_float."""
    out = []
    for path in sorted(PKG.rglob("*.py")):
        rel = path.relative_to(PY_DIR).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:                       # pragma: no cover
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not isinstance(fn, ast.Attribute) or fn.attr not in (
                    "load", "loads"):
                continue
            base = fn.value
            if not isinstance(base, ast.Name) or base.id not in (
                    "json", "tomllib", "tomli"):
                continue
            if any(k.arg == "parse_float" for k in node.keywords):
                continue
            out.append((rel, node.lineno))
    return out


def test_g3_no_unhooked_stdlib_loader_reads_caller_text():
    """Strict zero outside the named exemptions.

    POSITIVE CONTROL: the predicate finds the exempt sites, so it is looking
    at something. DOES NOT PROVE that the front door's default is exact —
    that is G1.
    """
    sites = _bypass_sites()
    assert sites, "the predicate found nothing at all — it is not looking"
    exempt = [s for s in sites if s[0] in _G3_EXEMPT]
    assert exempt, "the positive control did not fire"
    bad = [s for s in sites if s[0] not in _G3_EXEMPT]
    assert not bad, (
        f"{len(bad)} stdlib loader call(s) read caller text with no "
        f"parse_float=: {bad}. Add the hook, or add the file to _G3_EXEMPT "
        f"WITH ITS REASON — never as a wildcard.")


#: STRICT ZERO. Two adapter ``_coerce`` sites read caller decimal TEXT
#: through a BARE ``float()`` — `csv_bulk` and `html_scraper` — and they are
#: invisible to every json/toml predicate, because they reach a float through
#: neither front door nor any stdlib loader. The rc479 entry-point census
#: found them only by this scan.
#:
#: They were adjudicated as a NAMED EXEMPTION seeded at 2, on the ground that
#: neither is wired to a shipped catalog (the only ``adapter =`` value under
#: ``amsc/attested/`` is ``literature_curated``). That is an argument about
#: BLAST RADIUS, not about the contract: a CSV cell IS caller decimal text,
#: and leaving it rounding while a JSON literal beside it is read exactly
#: would be two contracts wearing one name, with the difference decided by
#: which adapter a descriptor happens to name. Both were converted instead,
#: so the population is ZERO and a third one cannot join a roster — it has to
#: be fixed or argued.
_TEXT_COERCE_EXEMPT = 0


def _bare_float_hits(tree, where):
    """``(where, fn, lineno)`` for every builtin ``float(<name>)`` whose
    argument is a ``str``-annotated parameter of the enclosing def.

    This is the ONLY predicate that can see a contract-A entry point which
    reaches a float through neither front door nor any stdlib loader —
    ``json``/``tomllib`` AST censuses are blind to it by construction.
    """
    out = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef):
            continue
        strs = {a.arg for a in fn.args.args
                if isinstance(a.annotation, ast.Name)
                and a.annotation.id == "str"}
        if not strs:
            continue
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "float"
                    and len(node.args) == 1
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id in strs):
                out.append((where, fn.name, node.lineno))
    return out


def test_g3_no_adapter_reads_decimal_text_through_a_bare_float():
    """A ``float(<str-annotated param>)`` census over the adapters, at ZERO.

    POSITIVE CONTROL: the predicate is re-run against a planted function, so
    a scan that silently matches nothing cannot read as a clean sweep.
    """
    planted = ast.parse(
        "def g(text: str):\n    return float(text)\n")
    assert _bare_float_hits(planted, "planted"), (
        "the predicate does not fire on its own positive control — a zero "
        "below would be the scan failing, not the tree being clean")
    negative = ast.parse(
        "def g(x: float):\n    return float(x)\n")
    assert not _bare_float_hits(negative, "planted"), (
        "the predicate fires on a FLOAT parameter — it is not selecting for "
        "text at all")

    hits = []
    for path in sorted((PKG / "amsc" / "adapters").rglob("*.py")):
        hits.extend(_bare_float_hits(
            ast.parse(path.read_text(encoding="utf-8")), path.name))
    assert len(hits) == _TEXT_COERCE_EXEMPT, (
        f"the bare-float text-coercion population is {len(hits)}, not "
        f"{_TEXT_COERCE_EXEMPT}: {hits}. A new one is a new contract-A entry "
        f"point and needs adjudicating, not absorbing.")


# ─────────────────────────────────────────────────────────────────────────
# G4 — the projection invariant every float consumer rides
# ─────────────────────────────────────────────────────────────────────────
def test_g4_the_exact_reading_projects_to_the_same_double():
    """Over the shipped descriptor corpus, ``float(Q(text)) == float(text)``.

    The tokens come from the real corpus rather than a hand list, by
    installing a RECORDING ``parse_float`` — the same mechanism the front
    door ships, so the harvest doubles as a reach proof.

    DOES NOT PROVE that any op's OUTPUT is unchanged; it proves only that a
    float consumer keeps its double. The signed zeros are the ONLY class
    where the exact reading cannot carry the value, and rule Z1 keeps those
    on the float carrier so they never reach the comparison.
    """
    import tomllib
    seen = []

    def record(text):
        seen.append(text)
        return float(text)

    files = sorted((PKG / "cascade" / "catalogs").rglob("*.toml")) + \
        sorted((PKG / "amsc" / "attested").rglob("*.toml"))
    assert len(files) >= 10, "the corpus is too small to mean anything"
    for p in files:
        try:
            tomllib.loads(p.read_text(encoding="utf-8"), parse_float=record)
        except tomllib.TOMLDecodeError:            # pragma: no cover
            continue
    assert len(seen) >= 100, f"only {len(seen)} float tokens harvested"

    nonfinite = signed_zero = same = differ = 0
    for text in seen:
        pair = decimal_text_to_pair(text)
        if pair is None:
            nonfinite += 1
            continue
        if pair[0] == 0 and text.lstrip()[:1] == "-":
            signed_zero += 1
            continue
        got = parse_float_exact(text)
        assert isinstance(got, Q), text
        if struct.pack("<d", float(got)) == struct.pack("<d", float(text)):
            same += 1
        else:                                      # pragma: no cover
            differ += 1
    assert differ == 0, (
        f"{differ} of {same + differ} corpus tokens do not project to the "
        f"double the old reader returned — every float consumer of those "
        f"values moves")
    assert same > 0, "the comparison never ran"


# ─────────────────────────────────────────────────────────────────────────
# G5 / G8 — the C node's own verdicts
# ─────────────────────────────────────────────────────────────────────────
def _c_toml_status(text):
    """``srmech_toml_parse``'s OWN status for a document — the bare-C verdict.

    The Python binding DECLINES every float document under contract A (the
    carrier decline), so ``toml_loads_c`` cannot report this. A C host calls
    the export, so this does too.
    """
    import ctypes
    raw = text.encode("utf-8")
    n = len(raw)
    ws_len = max(65536, 256 * n)
    ws = ctypes.create_string_buffer(ws_len)
    out = ctypes.POINTER(_native._TomlValue)()
    return int(_native.LIB.srmech_toml_parse(
        raw, ctypes.c_size_t(n), ctypes.cast(ws, ctypes.c_void_p),
        ctypes.c_size_t(ws_len), ctypes.byref(out)))


def _c_json_status(text):
    """``srmech_json_parse``'s OWN status — the peer of :func:`_c_toml_status`."""
    import ctypes
    raw = text.encode("utf-8")
    n = len(raw)
    ws_len = max(65536, 64 * n)
    ws = ctypes.create_string_buffer(ws_len)
    out = ctypes.POINTER(_native._JsonValue)()
    return int(_native.LIB.srmech_json_parse(
        raw, ctypes.c_size_t(n), ctypes.cast(ws, ctypes.c_void_p),
        ctypes.c_size_t(ws_len), ctypes.byref(out)))


def _require_native():
    if not (_native.HAS_NATIVE and getattr(_native, "LIB", None) is not None
            and hasattr(_native.LIB, "srmech_toml_parse")):
        pytest.skip("pure-by-design: no native library to ask")


def test_g5_the_c_node_refuses_the_tokens_python_refuses():
    """SRMECH_ERR_LIMIT on both exports, for the same tokens, inside the bound.

    DOES NOT PROVE that the C node's ARENA is right — only that its VERDICTS
    match. The C node never produces the exact rational at all; it declines
    a float document to the Python floor, which is what G-XCELL's equality
    rests on.
    """
    _require_native()
    for token in ("1e4300", "1e-4300", "5e-4300", "1e99999", "1e1000000"):
        assert _c_toml_status("x = %s\n" % token) == _native.SRMECH_ERR_LIMIT, \
            "toml: %s" % token
        assert _c_json_status('{"x": %s}' % token) == \
            _native.SRMECH_ERR_LIMIT, "json: %s" % token
    for token in ("0.1", "1.0", "1e400", "1e-400", "1e4299", "1e-4299",
                  "1e308", "1e309"):
        assert _c_toml_status("x = %s\n" % token) == _native.SRMECH_OK, \
            "toml accepted-side: %s" % token
        assert _c_json_status('{"x": %s}' % token) == _native.SRMECH_OK, \
            "json accepted-side: %s" % token


def test_g8_the_c_zero_collapse_survives_the_bound():
    """The ordering guard, and it is not hypothetical.

    Putting the refusal inside the exponent scan — which runs BEFORE the
    all-zero collapse — compiles, looks right, and turns all four of these
    into ``SRMECH_ERR_LIMIT``. That was measured on a compiled variant
    before this rc shipped, which is why the scanner reports an "exceeded"
    FLAG and its caller decides.
    """
    _require_native()
    for token in ZERO_TOKENS[:4]:      # the fifth is 5002 chars, past the cap
        assert _c_toml_status("x = %s\n" % token) == _native.SRMECH_OK, token
        assert _c_json_status('{"x": %s}' % token) == _native.SRMECH_OK, token
    for token in ("0e", "0eX", "1e", "1e+"):
        assert _c_toml_status("x = %s\n" % token) == \
            _native.SRMECH_ERR_BAD_INPUT, token


def test_g5_the_native_path_declines_a_float_document():
    """The CARRIER decline — what keeps a native cell equal to a pure one.

    No C value layer in this library can hold a rational, so returning the
    C tree's doubles would make the same call answer differently in the two
    projections. The binding declines instead and the floor answers exactly.
    """
    _require_native()
    assert _native.json_loads_c('{"x": 0.1}') is None
    assert _native.toml_loads_c("x = 0.1\n") is None
    # the control: an INTEGER document still rides the native path
    assert _native.json_loads_c('{"x": 5}') == {"x": 5}
    assert _native.toml_loads_c("x = 5\n") == {"x": 5}
    # and the front door's answer is the exact one either way
    assert _json.loads('{"x": 0.1}')["x"] == Q(1, 10)
    assert _toml.loads("x = 0.1\n")["x"] == Q(1, 10)


# ─────────────────────────────────────────────────────────────────────────
# G-MIX — the partially-exact sample the rc466 rationale warned about
# ─────────────────────────────────────────────────────────────────────────
def test_gmix_a_partially_exact_sample_agrees_chain_vs_op():
    """The shape rc466's comment named, and never tested.

    Its premise was that removing the entry cast would turn the chain into
    Q-of-float arithmetic. The chain ALREADY had it at the rc478 baseline —
    what the cast prevented was the OP matching the chain. Under M2/M3 they
    agree, which is the claim, and the tree's own mixed-carrier detector
    (``test_silent_carrier_demotion_rc463``) is unchanged by it.

    DOES NOT PROVE the mixed carrier is ABSENT. It is present and
    pre-existing; what is proven is that the two routes agree about it.
    """
    from srmech.cascade.hypercomplex_dft import quaternion_dft, as_quat4
    from srmech.cascade.composites import (autocorrelation, compensated_sum,
                                           correlation_product)

    # autocorrelation: the op against its OWN declared body, elementwise
    for xs in ([Q(1, 2), 0.5, 3], [1, 2.5], [Q(3, 1)], [1, Q(1, 3), 0.25]):
        n = len(xs)
        want = [compensated_sum([correlation_product(list(xs), i, (i + k) % n)
                                 for i in range(n)]) for k in range(n)]
        got = autocorrelation(list(xs))
        assert [type(a).__name__ for a in got] == \
               [type(b).__name__ for b in want], xs
        assert all(a == b for a, b in zip(got, want)), xs

    # as_quat4 requires ALL FOUR components exact, so a within-vector mix
    # stays on the float carrier — stated rather than assumed
    out = quaternion_dft([[Q(1, 2), 0.5, 0, 0]])
    assert all(isinstance(c, float) for row in out for c in row)
    assert all(isinstance(c, float) for c in as_quat4([Q(1, 2), 0.5, 0, 0]))
    # while an ACROSS-vector mix keeps each sample's own carrier
    out2 = quaternion_dft([[Q(1, 2), 0, 0, 0], [0.1, 0, 0, 0]])
    assert any(not isinstance(c, float) for row in out2 for c in row)


def test_gmix_qalg_orders_exactly_where_an_order_exists():
    """The THIRD carrier gap, and its limit is the point.

    Through rc478 a ``Qalg`` never reached a public wrapper's OUTPUT — the DFT
    transforms cast to float at their own entry. M2/M3 removed that cast, so
    an exact sample returns ``Qalg`` leaves, and ``quaternion_dft``'s own
    SHIPPED worked example — which a user copies — computes a round-trip
    residue and asks ``d >= 0`` for its Class-K sign branch. That raised
    ``TypeError: '>=' not supported between instances of 'Qalg' and 'int'``.

    ⚠️ **NOT a total order, and it must not become one.** A general element of
    ℚ(α) is COMPLEX, and ``<`` on a complex number is not hard — it is
    UNDEFINED. So the order exists exactly where the element lies in the prime
    field ℚ, and REFUSES otherwise with a message that says why. Measured on
    that worked snippet: all 32 round-trip residues are RATIONAL and exactly
    ZERO, so the rational arm closes it completely, with no projection and no
    tolerance. ``float(Qalg)`` is deliberately not the fallback — it needs an
    attached embedding root, and a comparison that depends on a rounding is
    the defect this release removes.

    DOES NOT PROVE anything about ordering a non-rational element; it proves
    that asking for one REFUSES rather than inventing an answer.
    """
    from srmech.math.qalg import Qalg

    m = (1, 0, 0, 0, 1)                      # ℚ(ζ₈)
    one = Qalg(m, (Q(1, 1), Q(0, 1), Q(0, 1), Q(0, 1)))
    half = Qalg(m, (Q(1, 2), Q(0, 1), Q(0, 1), Q(0, 1)))
    zero = Qalg(m, (Q(0, 1), Q(0, 1), Q(0, 1), Q(0, 1)))
    alpha = Qalg(m, (Q(0, 1), Q(1, 1), Q(0, 1), Q(0, 1)))   # ζ₈ — NOT real

    # the rational arm: exact, both directions, against int / Q / float / Qalg
    assert one >= 0 and one > 0 and zero >= 0 and not (zero > 0)
    assert half < one and one > half and half <= half and half >= half
    assert one > Q(1, 2) and one >= Q(1, 1) and half < 1 and half <= 1.0
    assert 0 < one and 1 >= one and Q(1, 2) < one

    # the refusal, and it NAMES the reason rather than reading as a type slip
    for bad in (lambda: alpha >= 0, lambda: alpha < one,
                lambda: one < alpha, lambda: alpha > alpha):
        with pytest.raises(TypeError) as exc:
            bad()
        assert "prime field" in str(exc.value), str(exc.value)[:120]

    # EQUALITY is untouched and was already correct — pinned so a future
    # ordering edit cannot quietly change it
    assert one == 1 and 1 == one and one == Q(1, 1) and one == 1.0
    assert zero == 0 and not bool(zero) and bool(one)


def test_gmix_the_transform_round_trips_its_own_output():
    """A transform whose output its own entry coercer cannot accept is broken.

    Every ``n = 3`` transform returns ``Qalg`` leaves, and through the first
    pass of this rc feeding that output back raised ``TypeError: float()
    argument must be a string or a real number, not 'Qalg'``.
    """
    from srmech.cascade.hypercomplex_dft import (quaternion_dft, octonion_dft,
                                                 as_quat4, as_oct8)
    q = quaternion_dft([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])
    assert any(type(c).__name__ == "Qalg" for row in q for c in row), (
        "the control did not fire — no Qalg leaf, so the round trip below "
        "would pass without exercising the arm it exists for")
    for row in q:
        assert len(as_quat4(row)) == 4
    back = quaternion_dft(q, inverse=True)
    assert len(back) == 3
    o = octonion_dft([[1] + [0] * 7, [0, 1] + [0] * 6, [0, 0, 1] + [0] * 5])
    assert any(type(c).__name__ == "Qalg" for row in o for c in row)
    for row in o:
        assert len(as_oct8(row)) == 8
    assert len(octonion_dft(o, inverse=True)) == 3


# ─────────────────────────────────────────────────────────────────────────
# G-SIEVE — the ONE answer-to-exception boundary
# ─────────────────────────────────────────────────────────────────────────
def test_gsieve_the_answer_to_exception_boundary_is_named():
    """An exact sample above the field-degree cap RAISES where it answered.

    Through rc478 the DFT wrappers cast to float at their own entry, so this
    was unreachable from the public wrapper; M2/M3 make it reachable. It is
    the only place this release turns an answer into an exception and it
    ships gated and announced rather than silently.

    ⚠️ The rc478 DEGREE cap moved this boundary, and the figures from the
    rc477 INDEX rule (`qdft ijk` first refusing at n=23, `odft diagonal` at
    n=11/13/15) are SUPERSEDED, not contradicted. Measured at
    `MAX_CYCLOTOMIC_DEGREE = 888`: `axis_k = 1` refuses NOTHING at n <= 256,
    `ijk` first refuses at n = 227 (Phi_2724, degree 904) with 6 refusals,
    and `diagonal` first refuses at n = 79 (Phi_2212, degree 936) with 82.

    DOES NOT PROVE anything about n > 256: it is a SIEVE over n, and the
    rule is gated by its closed form with the two measured witnesses.
    """
    from srmech.math import qalg as _qalg
    from srmech.cascade.hypercomplex_dft import quaternion_dft, octonion_dft

    def refusals(base, hi):
        return [n for n in range(1, hi + 1)
                if _qalg._field_too_big(
                    _qalg._turn_field_index(n, base)) is not None]

    assert refusals(1, 256) == [], "axis_k=1 must refuse nothing at n<=256"
    assert refusals(3, 256)[0] == 227, refusals(3, 256)[:4]
    assert len(refusals(3, 256)) == 6
    assert refusals(7, 256)[0] == 79, refusals(7, 256)[:4]
    assert len(refusals(7, 256)) == 82
    assert 128 - len(refusals(7, 128)) == 114, "114 of 128 admitted"

    # EXECUTED at the two witnesses. A refusal is arithmetic and costs
    # milliseconds; the ADMITTED transform at the same n is O(n^2) exact
    # field work and is deliberately not run.
    for op, axis, n, dim in ((quaternion_dft, "ijk", 227, 4),
                             (octonion_dft, "diagonal", 79, 8)):
        exact = [[Q(1, 1)] + [Q(0, 1)] * (dim - 1)] + \
                [[Q(0, 1)] * dim for _ in range(n - 1)]
        with pytest.raises(ValueError) as exc:
            op(exact, mu_axis=axis)
        assert "degree" in str(exc.value), str(exc.value)[:120]
        # THE CONTROL: the same op, the same axis, an ADMITTED length —
        # so the raise is the SIEVE and not the op being broken.
        small = [[Q(1, 1)] + [Q(0, 1)] * (dim - 1), [Q(0, 1)] * dim]
        assert len(op(small, mu_axis=axis)) == 2


# ─────────────────────────────────────────────────────────────────────────
# G-FLOATARM — what the rc420 gate stops proving
# ─────────────────────────────────────────────────────────────────────────
#: FLOAT input leaves across the rc420 gate's own 98 proof cases. It was 313
#: at rc478 and is 6 now, because the proof-case inputs are read from the
#: descriptor TOML and contract A makes them exact. The 6 survivors are
#: exactly the rule-Z1 non-finite escapes (`magnitude` nan/inf/-inf x4,
#: `best_rational_signed` nan x2).
#:
#: ⚠️ THE POINT OF THIS GATE. "107 passed" at rc479 is a materially NARROWER
#: claim than the identical "107 passed" at rc478, and nothing in that gate
#: says so. Pinning the number here means the collapse cannot deepen — or
#: silently reverse — without a reader being told.
FLOAT_INPUT_LEAVES_IN_RC420_CORPUS = 6


def test_gfloatarm_the_rc420_gates_float_arm_is_pinned():
    """The rc420 corpus's float arm, counted rather than assumed."""
    sys.path.insert(0, str(PY_DIR / "tests"))
    import test_cascade_catalog_executable_rc420 as G

    def leaves(v):
        if isinstance(v, (list, tuple)):
            for e in v:
                yield from leaves(e)
        elif isinstance(v, dict):
            for e in v.values():
                yield from leaves(e)
        else:
            yield v

    nf = nq = 0
    cases = G._executable_cases()
    for case in cases:
        for leaf in leaves(case[4]):
            if isinstance(leaf, bool):
                continue
            if isinstance(leaf, float):
                nf += 1
            elif isinstance(leaf, Q):
                nq += 1
    assert nq > 0, "no exact leaf at all — contract A did not reach the corpus"
    assert nf == FLOAT_INPUT_LEAVES_IN_RC420_CORPUS, (
        f"the rc420 corpus carries {nf} float input leaves, pinned at "
        f"{FLOAT_INPUT_LEAVES_IN_RC420_CORPUS}. Fewer means the float rung "
        f"is exercised even less than this rc measured; more means a "
        f"descriptor literal stopped being read exactly. Either way the "
        f"gate's '107 passed' now means something different.")


# ─────────────────────────────────────────────────────────────────────────
# G-DIGEST — a committed attestation digest does not move
# ─────────────────────────────────────────────────────────────────────────
def test_gdigest_canonicalisation_stays_in_the_double_projection():
    """``response_sha256`` and ``collector_descriptor_hash`` do not move.

    Both are SHA-256 over a canonical re-serialisation of PARSED content —
    neither is over raw fetched bytes, which is the opposite of what a
    reader assumes and of what this rc's own planning assumed. Contract A
    changes how srmech CARRIES a number it reads, not what the committed
    bytes SAY, so the canonicalisation writes the double the rational
    projects to.

    THE CONTROL IS THE WHOLE TEST: without the ``default=`` these same rows
    raise ``TypeError: Object of type Q is not JSON serializable``, which is
    what proves an exact leaf was actually present.
    """
    rows = []
    for p in sorted((PKG / "amsc" / "attested").rglob("*.ndjson")):
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                rows.append(line)
    assert len(rows) >= 50, f"only {len(rows)} attested rows found"

    control_fired = same = 0
    for line in rows:
        old = json.loads(line)                    # the DOUBLE projection
        new = _json.loads(line)                   # contract A
        ob = json.dumps(old, sort_keys=True,
                        ensure_ascii=False).encode("utf-8")
        try:
            json.dumps(new, sort_keys=True, ensure_ascii=False)
        except TypeError:
            control_fired += 1                    # an exact leaf IS present
        nb = json.dumps(new, sort_keys=True, ensure_ascii=False,
                        default=canonical_json_default).encode("utf-8")
        assert sha256_bytes(ob) == sha256_bytes(nb), (
            "a committed row digest MOVED under contract A — every "
            "attestation carrying it is now unverifiable")
        same += 1
    assert control_fired > 0, (
        "no row carried an exact leaf, so this comparison proves nothing "
        "about contract A")
    assert same == len(rows)


def test_gdigest_the_descriptor_hash_is_invariant():
    """``descriptor_hash`` hashes the PARSED dict; contract A must not move it."""
    import tomllib
    from srmech.amsc.descriptor import descriptor_hash

    checked = 0
    for p in sorted((PKG / "amsc" / "attested").rglob("*.toml")):
        old = tomllib.loads(p.read_text(encoding="utf-8"))
        ob = json.dumps(old, sort_keys=True,
                        ensure_ascii=False).encode("utf-8")
        assert descriptor_hash(p) == sha256_bytes(ob), p.name
        checked += 1
    assert checked >= 5, f"only {checked} descriptors checked"
