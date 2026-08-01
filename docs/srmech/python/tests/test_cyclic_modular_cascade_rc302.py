"""rc302 (§110 / #1460, §112 / #1462) — the Class-I modular family becomes a
DSL-DECLARABLE, tool_schema-DISCOVERABLE cascade, plus a 128-bit-capable
modular multiply.

Before rc302 only ``cyclic_gcd`` lived in the cascade catalog, so a modular-
arithmetic cascade (an LCG, a hash, the PCG64 step) could not be *declared* via
``srmech.dsl.chain`` / a TOML chain spec — only hand-composed in Python. This
suite pins:

1. the five new cascade ops (cyclic_mod_mul/add/pow/inv/mul_wide) resolve, run,
   and match the ``srmech.math.cyclic.*`` primitive they delegate to;
2. a TOML-DECLARED LCG cascade matches the hand-composed Python LCG;
3. ``cyclic.mod_mul_wide`` == ``(a * b) % n`` at any width, does NOT weaken the
   uint64-capped ``mod_mul``, and reproduces the raw PCG64 128-bit LCG step;
4. ``cyclic.bigint_mul`` == ``a * b`` exactly (the C bignum product);
5. the seven new ops are registered in the tool_schema with user-facing
   "aboutness" (the words a caller would search), implementation words kept.

numpy-free (imports only srmech + stdlib), per the numpy-absent CI cell.
"""
from __future__ import annotations

import random

import pytest

from srmech.math import cyclic
from srmech.amsc import cascade
from srmech.amsc.tool_schema import get_tool_schema
from srmech.dsl import chain, list_cascade_ops, run_toml_chain


# ── 1. the five modular ops joined the cascade catalog ─────────────────────

_NEW_CASCADE_OPS = (
    "cyclic_mod_mul", "cyclic_mod_add", "cyclic_mod_pow",
    "cyclic_mod_inv", "cyclic_mod_mul_wide",
)


def test_modular_ops_are_in_the_cascade_catalog():
    ops = set(list_cascade_ops())
    for name in _NEW_CASCADE_OPS:
        assert name in ops, f"{name} missing from the cascade catalog"


def test_cascade_ops_delegate_to_the_cyclic_primitive():
    # each cascade op is a thin delegation to srmech.math.cyclic.*
    assert cascade.cyclic_mod_mul(7, 6, 10) == cyclic.mod_mul(7, 6, 10) == 2
    assert cascade.cyclic_mod_add(7, 6, 10) == cyclic.mod_add(7, 6, 10) == 3
    assert cascade.cyclic_mod_pow(3, 4, 10) == cyclic.mod_pow(3, 4, 10) == 1
    assert cascade.cyclic_mod_inv(3, 7) == cyclic.mod_inv(3, 7) == 5
    assert cascade.cyclic_mod_mul_wide(2**64, 3, 2**128) == \
        cyclic.mod_mul_wide(2**64, 3, 2**128)


# ── 2. a TOML-DECLARED modular cascade runs + matches hand-composed Python ──

# Numerical Recipes "ranqd1" LCG (mod 2**32, well within uint64).
_MOD, _MULT, _INC = 2**32, 1664525, 1013904223


def _lcg_python(state: int, steps: int) -> int:
    for _ in range(steps):
        state = (_MULT * state + _INC) % _MOD      # hand-composed reference
    return state


def test_toml_declared_lcg_cascade_matches_python():
    # one LCG step declared as a DSL chain: mod_mul then mod_add, bound kwargs.
    step = (chain("lcg")
            .then("cyclic_mod_mul", b=_MULT, n=_MOD)
            .then("cyclic_mod_add", b=_INC, n=_MOD))
    state = 12345
    for i in range(1, 11):
        state = step.run(state)
        assert state == _lcg_python(12345, i), f"LCG mismatch at step {i}"


def test_run_toml_chain_inline_spec_lcg_step():
    # the tool-callable, declarative face: an inline TOML chain spec.
    spec = """
[chain]
name = "lcg_step"

[[stage]]
op = "cyclic_mod_mul"
b = 1664525
n = 4294967296

[[stage]]
op = "cyclic_mod_add"
b = 1013904223
n = 4294967296
"""
    for seed in (0, 1, 12345, 2**31):
        assert run_toml_chain(spec, seed) == (_MULT * seed + _INC) % _MOD


# ── 3. mod_mul_wide — the 128-bit-capable modular multiply ──────────────────

def test_mod_mul_wide_equals_product_mod_n_any_width():
    rng = random.Random(7)
    for _ in range(3000):
        bits = rng.choice([64, 128, 192, 256])
        a = rng.getrandbits(bits)
        b = rng.getrandbits(bits)
        n = rng.getrandbits(rng.randint(2, 130)) or 1
        assert cyclic.mod_mul_wide(a, b, n) == (a * b) % n


def test_mod_mul_does_not_weaken_the_uint64_cap():
    # the capped op MUST still reject > uint64 — mod_mul_wide is the widening,
    # not a loosening of mod_mul's fixed-64-bit guard.
    with pytest.raises(ValueError):
        cyclic.mod_mul(2**64, 3, 2**100)
    with pytest.raises(ValueError):
        cyclic.mod_mul(3, 3, 2**64)         # n == 2**64 exceeds uint64-1


def test_mod_mul_wide_reproduces_raw_pcg64_step():
    # numpy PCG64 default multiplier; state <- (state*MULT + INC) mod 2**128.
    MULT = 0x2360ed051fc65da44385df649fccf645
    INC = 0xda3e39cb94b95bdb | 1          # any odd stream increment
    MASK = (1 << 128) - 1

    def pcg_raw(state: int) -> int:
        return (state * MULT + INC) & MASK

    def pcg_via_wide(state: int) -> int:
        # multiply-and-reduce half via the wide op, then + inc mod 2**128
        return cyclic.mod_mul_wide(state, MULT, 1 << 128) + INC & MASK

    st = 0x853c49e6748fea9b
    for _ in range(2000):
        assert pcg_via_wide(st) == pcg_raw(st)
        st = pcg_raw(st)


def test_mod_mul_wide_rejects_negative_and_zero_modulus():
    with pytest.raises(ValueError):
        cyclic.mod_mul_wide(-1, 2, 5)
    with pytest.raises(ValueError):
        cyclic.mod_mul_wide(2, 3, 0)
    with pytest.raises(TypeError):
        cyclic.mod_mul_wide(True, 2, 5)     # bool rejected


# ── 4. bigint_mul — the uncapped C bignum product ──────────────────────────

def test_bigint_mul_equals_product_any_width():
    rng = random.Random(11)
    for _ in range(3000):
        a = rng.getrandbits(rng.randint(1, 300))
        b = rng.getrandbits(rng.randint(1, 300))
        s = rng.choice([1, -1])
        assert cyclic.bigint_mul(s * a, b) == (s * a) * b


def test_bigint_mul_rejects_bool():
    with pytest.raises(TypeError):
        cyclic.bigint_mul(True, 3)


# ── 5. tool_schema registration + user-facing aboutness ────────────────────

def test_new_ops_are_registered_in_tool_schema():
    names = {t.name for t in get_tool_schema().tools}
    expected = {
        "srmech.math.cyclic.bigint_mul",
        "srmech.math.cyclic.mod_mul_wide",
        "srmech.amsc.cascade.cyclic_mod_mul",
        "srmech.amsc.cascade.cyclic_mod_add",
        "srmech.amsc.cascade.cyclic_mod_pow",
        "srmech.amsc.cascade.cyclic_mod_inv",
        "srmech.amsc.cascade.cyclic_mod_mul_wide",
    }
    assert expected <= names, f"missing: {expected - names}"


def test_summaries_carry_user_facing_aboutness():
    by_name = {t.name: t for t in get_tool_schema().tools}
    # mod_mul: the searchable phrase AND the implementation words are present.
    mm = by_name["srmech.math.cyclic.mod_mul"].summary.lower()
    assert "modular multiply" in mm and "russian-peasant" in mm
    # mod_pow: searchable "modular exponentiation" + kept "square-and-multiply".
    mp = by_name["srmech.math.cyclic.mod_pow"].summary.lower()
    assert "modular exponentiation" in mp and "square-and-multiply" in mp
    # magnitude: searchable "absolute value" + kept "class k pin-slot".
    mag = by_name["srmech.amsc.cascade.magnitude"].summary.lower()
    assert "absolute value" in mag and "class k pin-slot" in mag
    # bignum multiply is discoverable by "bignum multiply".
    bm = by_name["srmech.math.cyclic.bigint_mul"].summary.lower()
    assert "bignum multiply" in bm
