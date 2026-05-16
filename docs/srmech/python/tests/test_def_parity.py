"""Parity tests for Classes D (dispatch) + E (naming/catalog) +
F (template render).

Reference values + Python-equivalence + native ↔ fallback parity sweep.
"""

from __future__ import annotations

import random

import pytest

from srmech.amsc import _native, dispatch, naming, template


# ---------------------------------------------------------------------
# Class D — dispatch.match
# ---------------------------------------------------------------------

@pytest.mark.parametrize("input_b, rules, expected", [
    (b"hello world", [(b"world", 42)], (True, 42)),
    (b"hello world", [(b"xyz", 1), (b"world", 2)], (True, 2)),
    (b"hello world", [(b"hello", 1), (b"world", 2)], (True, 1)),  # first match wins
    (b"hello world", [(b"xyz", 1)], (False, 0)),
    (b"", [(b"xyz", 1)], (False, 0)),
    (b"abc", [], (False, 0)),
    (b"abc", [(b"", 99)], (True, 99)),  # empty pattern matches at 0
])
def test_dispatch_match_reference_values(input_b, rules, expected):
    assert dispatch.match(input_b, rules) == expected


def test_dispatch_match_first_rule_wins():
    rules = [(b"o", 1), (b"l", 2), (b"e", 3)]
    matched, tag = dispatch.match(b"hello", rules)
    assert matched is True
    assert tag == 1  # `o` is the first rule that matches


def test_dispatch_invalid_input():
    with pytest.raises(TypeError):
        dispatch.match("not bytes", [(b"x", 1)])


# ---------------------------------------------------------------------
# Class E — naming.lookup
# ---------------------------------------------------------------------

@pytest.mark.parametrize("key, pairs, expected", [
    (b"foo", [(b"bar", b"BAR"), (b"foo", b"FOO")], b"FOO"),
    (b"foo", [(b"foo", b"FOO")], b"FOO"),
    (b"baz", [(b"bar", b"BAR"), (b"foo", b"FOO")], None),
    (b"foo", [], None),
    (b"", [(b"", b"EMPTY"), (b"x", b"X")], b"EMPTY"),
])
def test_naming_lookup_reference_values(key, pairs, expected):
    assert naming.lookup(key, pairs) == expected


def test_naming_lookup_binary_search_correctness():
    """Sweep over a sorted catalog of 100 entries; every key present
    should be found; every absent key should return None."""
    pairs = sorted([(f"key{i:03d}".encode(), f"value{i:03d}".encode())
                    for i in range(100)])
    for i in range(100):
        assert naming.lookup(f"key{i:03d}".encode(), pairs) == \
            f"value{i:03d}".encode()
    assert naming.lookup(b"missing", pairs) is None
    assert naming.lookup(b"key999", pairs) is None
    assert naming.lookup(b"", pairs) is None


def test_naming_lookup_invalid_input():
    with pytest.raises(TypeError):
        naming.lookup("not bytes", [(b"k", b"v")])


# ---------------------------------------------------------------------
# Class F — template.render
# ---------------------------------------------------------------------

@pytest.mark.parametrize("tmpl, mapping, expected", [
    (b"hello", {}, b"hello"),                                # no placeholders
    (b"hello {name}", {b"name": b"world"}, b"hello world"),
    (b"{a}{b}{c}", {b"a": b"X", b"b": b"Y", b"c": b"Z"}, b"XYZ"),
    (b"{x}", {b"x": b""}, b""),                              # empty value
    (b"", {b"k": b"v"}, b""),                                # empty template
    (b"prefix-{x}-suffix", {b"x": b"MID"}, b"prefix-MID-suffix"),
])
def test_template_render_reference_values(tmpl, mapping, expected):
    assert template.render(tmpl, mapping) == expected


def test_template_unknown_key_raises():
    with pytest.raises(ValueError):
        template.render(b"hello {unknown}", {b"name": b"world"})


def test_template_unterminated_brace_raises():
    with pytest.raises(ValueError):
        template.render(b"hello {oops", {b"oops": b"x"})


def test_template_render_invalid_input():
    with pytest.raises(TypeError):
        template.render("not bytes", {b"k": b"v"})


# ---------------------------------------------------------------------
# C ↔ Python parity (requires HAS_NATIVE)
# ---------------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_dispatch_matches_fallback():
    rng = random.Random(20260516)
    saved = _native.HAS_NATIVE
    try:
        alphabet = b"ABC"
        for _ in range(50):
            input_b = bytes(rng.choices(alphabet, k=rng.randint(0, 50)))
            n_rules = rng.randint(0, 5)
            rules = [
                (bytes(rng.choices(alphabet, k=rng.randint(0, 3))),
                 rng.randint(1, 1000))
                for _ in range(n_rules)
            ]
            _native.HAS_NATIVE = True
            native_result = dispatch.match(input_b, rules)
            _native.HAS_NATIVE = False
            fallback_result = dispatch.match(input_b, rules)
            assert native_result == fallback_result, (
                f"input={input_b!r} rules={rules} "
                f"native={native_result} fallback={fallback_result}"
            )
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_naming_matches_fallback():
    rng = random.Random(20260517)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(30):
            n = rng.randint(0, 50)
            pairs = sorted([(f"k{i:03d}".encode(),
                             bytes(rng.choices(b"xyz", k=rng.randint(0, 5))))
                            for i in range(n)])
            # Test a hit
            if n > 0:
                target_idx = rng.randint(0, n - 1)
                target_key = pairs[target_idx][0]
                _native.HAS_NATIVE = True
                a = naming.lookup(target_key, pairs)
                _native.HAS_NATIVE = False
                b = naming.lookup(target_key, pairs)
                assert a == b
            # Test a miss
            _native.HAS_NATIVE = True
            a_miss = naming.lookup(b"definitely_missing", pairs)
            _native.HAS_NATIVE = False
            b_miss = naming.lookup(b"definitely_missing", pairs)
            assert a_miss is None and b_miss is None
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_template_matches_fallback():
    rng = random.Random(20260518)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(30):
            keys = [f"k{i}".encode() for i in range(rng.randint(1, 5))]
            mapping = {k: bytes(rng.choices(b"abc", k=rng.randint(0, 4)))
                       for k in keys}
            # Build a template that uses some of the keys
            parts = []
            for _ in range(rng.randint(0, 5)):
                parts.append(bytes(rng.choices(b"xyz", k=rng.randint(0, 3))))
                if keys:
                    parts.append(b"{" + rng.choice(keys) + b"}")
            tmpl = b"".join(parts)
            _native.HAS_NATIVE = True
            native_out = template.render(tmpl, mapping)
            _native.HAS_NATIVE = False
            fallback_out = template.render(tmpl, mapping)
            assert native_out == fallback_out
    finally:
        _native.HAS_NATIVE = saved
