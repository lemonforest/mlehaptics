"""Native-dispatch spy ratchet (srmech 0.9.0rc9).

**The gap this closes.** The byte-parity tests (``test_native_q61_parity_rc7.py``
et al.) prove the native C and the pure-Python cascade produce the SAME bytes —
but byte-equality cannot distinguish "native actually ran" from "pure-Python
produced the same bytes." A silent regression that left the dispatch guard
mis-wired (or bound the C function at import time so a later swap is missed)
would pass every parity test while never touching the C library.

This module spies the native entrypoints in ``srmech.amsc._native`` and asserts
the **public Python PyPI surface dispatches into C** when the shared library is
present — i.e. when NOT pure-Python, the native calls are genuinely made. It is
native-gated: it SKIPS in a numpy-/native-absent dev env and on the pure-wheel
CI cell, and RUNS on the native CI matrix cells (the real gate). Itself
numpy-free (per the numpy-free-module test discipline).
"""

from __future__ import annotations

import pytest

from srmech.amsc import _native
from srmech.amsc import format as _format
from srmech.amsc import rational as R
from srmech.amsc.q import Q

native_trans = pytest.mark.skipif(
    not _native.has_native_trans_q61(),
    reason="native Q61 transcendental peers not loaded; the native CI cells are the gate",
)
native_lib = pytest.mark.skipif(
    not _native.HAS_NATIVE,
    reason="native srmech library not loaded; the native CI cells are the gate",
)


def _spy(monkeypatch, name, counter):
    """Wrap ``_native.<name>`` with a call-counter that still runs the original.

    rational.py / format.py read these as module ATTRIBUTES at call time
    (``_native.sin_q61_c(x)``), so patching the attribute is observed — which is
    exactly the property under test (no import-time-bound private reference that
    would bypass the swap)."""
    if not hasattr(_native, name):
        return
    orig = getattr(_native, name)

    def wrapped(*args, **kwargs):
        counter[name] = counter.get(name, 0) + 1
        return orig(*args, **kwargs)

    monkeypatch.setattr(_native, name, wrapped)


# ── 1. the rc7/rc8 Q61 transcendental surface dispatches to native C ──────────

# (public rational op, native peers it MUST reach when the lib is present)
_Q61_DISPATCH = [
    ("sin",   lambda: R.sin(0.7),       ["sin_q61_c"]),
    ("cos",   lambda: R.cos(0.7),       ["cos_q61_c"]),
    ("tan",   lambda: R.tan(0.7),       ["sin_q61_c", "cos_q61_c"]),  # sin/cos compose
    ("atan",  lambda: R.atan(0.7),      ["atan_q61_c"]),
    ("atan2", lambda: R.atan2(1.0, 2.0), ["atan_q61_c"]),             # via atan(y/x)
    ("exp",   lambda: R.exp(0.5),       ["exp_q61_c"]),
    ("log",   lambda: R.log(2.0),       ["log_q61_c"]),
    ("sqrt",  lambda: R.sqrt(2.0),      ["sqrt_q61_c"]),
]

_Q61_NATIVES = ["sin_q61_c", "cos_q61_c", "atan_q61_c",
                "exp_q61_c", "log_q61_c", "sqrt_q61_c"]


@native_trans
@pytest.mark.parametrize("label,call,expect", _Q61_DISPATCH,
                         ids=[r[0] for r in _Q61_DISPATCH])
def test_q61_op_dispatches_to_native(monkeypatch, label, call, expect):
    counter: dict[str, int] = {}
    for n in _Q61_NATIVES:
        _spy(monkeypatch, n, counter)
    call()
    for peer in expect:
        assert counter.get(peer, 0) >= 1, (
            f"rational.{label} did NOT reach native {peer} "
            f"(observed native calls: {counter}) — the PyPI surface is NOT "
            f"dispatching to C despite has_native_trans_q61() being True")


@native_trans
def test_hypot_stays_pure_alu_isqrt(monkeypatch):
    """hypot is the honest exception: an EXACT bignum integer-isqrt of a²+b²,
    with no native FPU peer (``sqrt_q61_c`` is float->Q61, not bignum-isqrt). It
    must produce the exact ``Q`` and make NO native trans call — locks the
    intentional pure-ALU path so a future edit can't silently reroute it."""
    counter: dict[str, int] = {}
    for n in _Q61_NATIVES:
        _spy(monkeypatch, n, counter)
    result = R.hypot(3.0, 4.0)
    assert result == Q(5, 1)  # exact: 3²+4²=25, isqrt→5, no native FPU peer used
    assert sum(counter.values()) == 0, (
        f"hypot unexpectedly reached a native trans peer: {counter}")


# ── 2. established native families also dispatch from the PyPI surface ────────

@native_lib
def test_sha256_bytes_dispatches_to_native(monkeypatch):
    """Class A: format.sha256_bytes -> native, via the SHA-NI accelerated path
    (sha256_shani_c) when the CPU symbol is present, else sha256_hex_c."""
    counter: dict[str, int] = {}
    _spy(monkeypatch, "sha256_hex_c", counter)
    _spy(monkeypatch, "sha256_shani_c", counter)
    digest = _format.sha256_bytes(b"srmech native dispatch ratchet")
    assert len(digest) == 64
    assert sum(counter.values()) >= 1, (
        f"format.sha256_bytes did NOT reach native (observed: {counter})")


@native_lib
def test_read_ndjson_dispatches_to_native(monkeypatch, tmp_path):
    """Class C: format.read_ndjson -> native ndjson_lines_c (the streaming
    tokeniser). Only the dispatch is under test, so per-record parsing is
    tolerated to fail — the native reader is reached during iteration."""
    counter: dict[str, int] = {}
    _spy(monkeypatch, "ndjson_lines_c", counter)
    p = tmp_path / "dispatch.ndjson"
    p.write_text('{"a": 1}\n{"b": 2}\n', encoding="utf-8")
    try:
        for _ in _format.read_ndjson(p):
            pass
    except Exception:
        pass  # record-shape parsing is not what we are asserting
    assert counter.get("ndjson_lines_c", 0) >= 1, (
        "format.read_ndjson did NOT reach native ndjson_lines_c")
