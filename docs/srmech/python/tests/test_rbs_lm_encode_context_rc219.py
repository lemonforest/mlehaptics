"""rc219 (gh #827): srmech_rbs_lm_encode_word / _encode_context parity gate.

The C peers collapse the `srmech.rbs_lm.substrate` per-token / per-window
Klein-4 encode loop (sha256 token seeds + MT19937 mint + XOR bind + strict
majority bundle + the even-count odd-pad) into ONE C crossing, with an
optional caller-owned window-invariant MINT CACHE (byte vocab / byteglyph
position keys / window position keys — lazily filled, persistent across calls
on the ContextSubstrate instance).

PARITY KIND: **EXACT byte-identical** — every leaf is an integer/byte op, so
native == forced-pure == the pre-rc219 Python orchestration, byte for byte,
on every platform (the rc217 srmech_text contract, NOT the within-tol numeric
one). The battery covers both enc_modes, odd/even/empty windows (the pad
path), empty tokens, unicode tokens, and the mint-cache edges (tokens longer
than the byteglyph-position cache, windows wider than the position-key cache,
cold + warm cache).

BOTH ARMS RUN IN-FILE (the house rc213/rc217 convention): the forced-pure arm
is ``monkeypatch.setattr(_native, "HAS_NATIVE", False)`` — every ``has_native_
*`` gate (the rc219 peers AND the klein4 leaves) then declines, so the
comparison is genuinely one-C-crossing-native vs fully-pure Python. On a no-C
host both sides take the pure route and the asserts still run (no skips
except the dispatch spies).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from srmech.amsc import _native, hdc
from srmech.rbs_lm.substrate import (
    ContextSubstrate,
    _sector_const,
    encode_word_byteglyph,
    encode_word_k4,
    token_seed,
)


def _forced_pure(monkeypatch, fn, *args, **kwargs):
    """Run ``fn`` with the WHOLE native surface off (HAS_NATIVE False → every
    has_native_* gate declines) — the fully-pure arm of the parity claim."""
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        return fn(*args, **kwargs)


# ── the pre-rc219 pure bodies (the byte-identity oracles) ────────────────────


def _oracle_word_k4(word, D, sector, hex_chars):
    """The pre-rc219 encode_word_k4 body, verbatim."""
    base = hdc.klein4_expand(D, token_seed(word, hex_chars))
    return hdc.klein4_bind(base, _sector_const(D, sector))


def _oracle_word_byteglyph(word, D, sector):
    """The pre-rc219 encode_word_byteglyph body, verbatim."""
    data = word.encode("utf-8")
    if len(data) == 0:
        base = hdc.klein4_expand(D, 0)
    else:
        base = hdc.klein4_encode_bytes(data, D)
    return hdc.klein4_bind(base, _sector_const(D, sector))


def _oracle_context(cs, window):
    """The pre-rc219 ContextSubstrate.encode_context body, verbatim (the
    per-token orchestration over the substrate's own enc / pos_key /
    bundle_odd — those are byte-stable public surface)."""
    bound = [hdc.klein4_bind(cs.pos_key(p), cs.enc(tok))
             for p, tok in enumerate(window)]
    return cs.bundle_odd(bound)


_WORDS = ["cat", "cats", "", "a", "naïve", "日本語テスト", "Ω≠ø",
          "__bundle_pad__", "x" * 300]

_WINDOWS = [
    [],                                        # empty → the pad alone
    ["a"],                                     # single → no bundle
    ["the", "cat", "sat"],                     # odd
    ["the", "cat", "sat", "on"],               # even → pad appended
    ["", "b", ""],                             # empty tokens in-window
    ["日本", "語", "テスト", "x", "y"],          # unicode
    ["w%d" % i for i in range(16)],            # the profiled k=16 shape
    ["x" * 100, "y"],                          # token beyond the bytepos cache
    ["p%d" % i for i in range(140)],           # window beyond the ctxpos cache
]


@pytest.mark.parametrize("enc_mode", ["byteglyph", "wordhash"])
@pytest.mark.parametrize("D", [16, 64, 256])
def test_encode_context_native_equals_pure_equals_pre_rc219(
        monkeypatch, enc_mode, D):
    """encode_context (live arm) == the fully-forced-pure encode_context ==
    the pre-rc219 per-token orchestration, byte for byte, across enc_modes /
    D / the window battery — INCLUDING a repeat call per window (cold + warm
    mint cache must give the same bytes)."""
    cs = ContextSubstrate(D=D, hex_chars=16, enc_mode=enc_mode)

    def _fresh_pure(win):
        # a FRESH substrate built AND encoded fully-pure (no shared _pad /
        # _poskey minted on the live arm) — the strict pure-arm value
        return ContextSubstrate(
            D=D, hex_chars=16, enc_mode=enc_mode).encode_context(win)

    for window in _WINDOWS:
        expected = _oracle_context(cs, window)
        pure = _forced_pure(monkeypatch, _fresh_pure, list(window))
        assert pure.tobytes() == expected.tobytes(), (
            f"forced-pure drift: enc_mode={enc_mode} D={D} len={len(window)}"
        )
        for _ in range(2):                     # cold cache, then warm cache
            got = cs.encode_context(list(window))
            assert got.tobytes() == expected.tobytes(), (
                f"encode_context drift: enc_mode={enc_mode} D={D} "
                f"window={window[:4]}…(len {len(window)})"
            )


@pytest.mark.parametrize("sector", [0, 1, 2, 3])
def test_encode_context_sector_channel(sector):
    """The sector channel is preserved (the pad carries it; the bound tokens
    cancel it) — byte parity across all four sectors."""
    cs = ContextSubstrate(D=64, hex_chars=16, sector=sector)
    for window in ([], ["a", "b"], ["a", "b", "c"]):
        assert cs.encode_context(window).tobytes() == \
            _oracle_context(cs, window).tobytes()


@pytest.mark.parametrize("hex_chars", [1, 8, 16, 63, 64])
def test_encode_word_k4_matches_pre_rc219_bytes(monkeypatch, hex_chars):
    """encode_word_k4 (live arm) == forced-pure == the pre-rc219 body across
    hex prefix widths (including the odd width 63 — the nibble-parse path —
    and the full 64)."""
    for word in _WORDS:
        for sector in (0, 3):
            got = encode_word_k4(word, D=64, sector=sector,
                                 hex_chars=hex_chars)
            exp = _oracle_word_k4(word, 64, sector, hex_chars)
            assert got.tobytes() == exp.tobytes(), (
                f"encode_word_k4 drift: word={word!r} hex_chars={hex_chars} "
                f"sector={sector}"
            )
            pure = _forced_pure(monkeypatch, encode_word_k4, word, D=64,
                                sector=sector, hex_chars=hex_chars)
            assert pure.tobytes() == exp.tobytes()


def test_encode_word_byteglyph_matches_pre_rc219_bytes(monkeypatch):
    for word in _WORDS:
        for D in (16, 256):
            for sector in (0, 1):
                got = encode_word_byteglyph(word, D=D, sector=sector)
                exp = _oracle_word_byteglyph(word, D, sector)
                assert got.tobytes() == exp.tobytes(), (
                    f"encode_word_byteglyph drift: word={word!r} D={D} "
                    f"sector={sector}"
                )
                pure = _forced_pure(monkeypatch, encode_word_byteglyph, word,
                                    D=D, sector=sector)
                assert pure.tobytes() == exp.tobytes()


def test_hex_chars_beyond_digest_clamps_like_the_slice():
    """token_seed slices digest[:hex_chars]; widths past 64 clamp to the full
    digest — the native path must reproduce that (it passes min(hc, 64))."""
    a = encode_word_k4("clamp", D=32, sector=0, hex_chars=64)
    b = encode_word_k4("clamp", D=32, sector=0, hex_chars=200)
    assert a.tobytes() == b.tobytes()


def test_pinned_context_state_bytes():
    """A fixed config pins a fixed state: all leaves are integer/byte ops
    (sha256 → MT19937 → XOR → majority), so this hash is platform- AND
    arm-independent — the accidental-algorithm-drift tripwire. (Contrast the
    float-eig spectral peer, where such a pin would be UNSOUND — rc218.)"""
    from srmech.amsc.format import sha256_bytes
    cs = ContextSubstrate(D=64, hex_chars=16, enc_mode="byteglyph")
    state = cs.encode_context(["the", "cat", "sat", "on"])
    assert sha256_bytes(state.tobytes()) == (
        "f343ebfb7869c3890265bfdf9fbcb0f4d3f3635e30c788db55091c7a93007db5"
    )


def test_window_generator_input_still_works():
    """encode_context accepted any iterable pre-rc219; the native path lists
    it once and must not consume it twice."""
    cs = ContextSubstrate(D=32, hex_chars=16)
    from_gen = cs.encode_context(w for w in ["a", "b", "c"])
    from_list = cs.encode_context(["a", "b", "c"])
    assert from_gen.tobytes() == from_list.tobytes()


def test_non_string_token_still_raises_pythonically():
    """A non-str token must surface the pure path's error (the native gate
    declines, never swallows)."""
    cs = ContextSubstrate(D=32, hex_chars=16)
    with pytest.raises((AttributeError, TypeError)):
        cs.encode_context(["ok", 42])


def test_native_path_actually_dispatches(monkeypatch):
    """On a native host the wrapper genuinely reaches the C kernels (not a
    silent pure fallback): sentinels on the ctypes symbols must fire."""
    if not (_native.HAS_NATIVE and _native.has_native_rbs_lm_encode_context()
            and _native.has_native_rbs_lm_encode_word()):
        pytest.skip("no native lib — pure-only host")
    hits = {"ctx": 0, "word": 0}
    real_ctx = _native.LIB.srmech_rbs_lm_encode_context
    real_word = _native.LIB.srmech_rbs_lm_encode_word

    def spy_ctx(*args):
        hits["ctx"] += 1
        return real_ctx(*args)

    def spy_word(*args):
        hits["word"] += 1
        return real_word(*args)

    with monkeypatch.context() as m:
        m.setattr(_native.LIB, "srmech_rbs_lm_encode_context", spy_ctx)
        m.setattr(_native.LIB, "srmech_rbs_lm_encode_word", spy_word)
        cs = ContextSubstrate(D=32, hex_chars=16)
        cs.encode_context(["a", "b", "c"])
        encode_word_k4("spy", D=32, sector=0, hex_chars=16)
    assert hits["ctx"] >= 1, "native encode_context gate on but C never fired"
    assert hits["word"] >= 1, "native encode_word gate on but C never fired"


_LEDGER = Path(__file__).resolve().parent / "rosetta_classification.ndjson"


def test_rosetta_rows_are_c_dispatched():
    """The rc219 ledger move: the two word-encode ops now carry their OWN C
    symbol (srmech_rbs_lm_encode_word) → c_dispatched."""
    rows = {r["defined_at"]: r["bucket"]
            for r in (json.loads(line)
                      for line in _LEDGER.read_text(encoding="utf-8").splitlines()
                      if line.strip())}
    assert rows["srmech.rbs_lm.substrate.encode_word_k4"] == "c_dispatched"
    assert rows["srmech.rbs_lm.substrate.encode_word_byteglyph"] == \
        "c_dispatched"
