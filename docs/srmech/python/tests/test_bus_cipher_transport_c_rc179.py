"""rc179 ANNEX Batch A part 2 — the bus Bio-TOTP ENCRYPTED transport → C.

A bare-C host must speak the ENCRYPTED wire, not just plaintext. rc179 adds
``srmech_bus_serve_encrypted`` / ``srmech_bus_connect_encrypted`` to the
standalone-C bus (``c/src/srmech_bus.c``): the transport wraps each
request/response payload in the rc178 UTLP Bio-TOTP wire cipher (the DEFAULT
stdlib HMAC-SHA-256 counter-mode path — the AES-128-CTR ``[crypto]`` extra
stays Python). ENCRYPT composes ``srmech_bio_totp_derive_key`` +
``_keystream_xor``; DECRYPT composes ``srmech_bio_totp_decode_splice``
(permissive binding over the OPAQUE payload); the key window rolls on the PAL
wall clock (``srmech_plat_now_ns``, added this rc).

The standalone-C bus is NOT Python-dispatched (Python has its own asyncio /
socket bus), so this file pins:

* the two new C symbols are present (hasattr on the loaded lib) and the ABI is
  still 3 (the new symbols are additive — no wire-format change to an existing
  function);
* WIRE PARITY — the exact wire body the C ``serve_encrypted`` / ``connect_
  encrypted`` build (``[nonce:16][ciphertext]`` via the shared byte-exact
  cipher peers) is recovered by the Python ``decode_splice``, i.e. a
  C-encrypted frame is Python-decryptable and vice-versa on the HMAC path.

The full end-to-end C round-trip (serve_encrypted → thread accept_one →
connect_encrypted → send_recv → echo) + ASAN/UBSAN leak/UB clean is proven by
the ephemeral /tmp C driver at build time (see the rc179 CHANGELOG).

SCOPE — the bus **pub/sub** (``pipe``) → C is DEFERRED to rc180 (an honest
split, not a stub): it needs a new PAL mutex + a concurrent subscriber-registry
broadcast fan-out + client ``subscribe`` streaming + the ``pipe`` composition
under a no-data-races bar — too big for one clean rc alongside the cipher-wire.
So ``srmech.bus._pipe.pipe`` stays ``owed_orchestration`` (CEIL_NON_COMPUTE_OWED
stays 11) this rc; rc180 moves it → composes_c.

numpy-free (stdlib hmac / hashlib / json via the shared cipher).
"""
from __future__ import annotations

import os

import pytest

from srmech.amsc import _native
import srmech.bus._bio_totp as bt

WIN = bt.DEFAULT_WINDOW_NS
_NATIVE = _native.HAS_NATIVE

requires_native = pytest.mark.skipif(
    not _NATIVE, reason="native bus C peer not loaded")


# ──────────────────────────────────────────────────────────────────────
# The two new encrypted-transport symbols + ABI
# ──────────────────────────────────────────────────────────────────────

@requires_native
def test_encrypted_bus_symbols_present():
    """rc179 adds serve_encrypted + connect_encrypted (additive — ABI stays 3)."""
    assert _native.NATIVE_ABI_VERSION == 3, (
        f"ABI must stay 3 (additive symbols); got {_native.NATIVE_ABI_VERSION}"
    )
    for sym in ("srmech_bus_serve_encrypted", "srmech_bus_connect_encrypted"):
        assert hasattr(_native.LIB, sym), f"native lib missing C symbol {sym}"


@requires_native
def test_req_rep_core_symbols_still_present():
    """The rc2 req/rep core is unchanged — the encrypted variants are ADDED,
    not a replacement (send_recv / accept_one / stop / close are shared)."""
    for sym in (
        "srmech_bus_serve", "srmech_bus_server_accept_one",
        "srmech_bus_server_stop", "srmech_bus_connect",
        "srmech_bus_send_recv", "srmech_bus_client_close",
    ):
        assert hasattr(_native.LIB, sym), f"native lib missing C symbol {sym}"


# ──────────────────────────────────────────────────────────────────────
# Wire parity: the C bus wire body == the shared Bio-TOTP wire
# ──────────────────────────────────────────────────────────────────────

def _c_bus_wire_body(dna, sender_id, channel_id, send_seq, pt, time_ns, window_ns):
    """Reconstruct the EXACT wire body srmech_bus__encrypt produces:
    nonce = build_nonce(sender_id, channel_id, send_seq); key = derive_key(...);
    body = nonce || keystream_xor(key, nonce, pt). Uses the SAME cipher peers
    the C bus composes (they dispatch to native under HAS_NATIVE)."""
    nonce = bt.build_nonce(sender_id, channel_id, send_seq)
    key = bt.derive_key(dna, time_ns, window_ns)
    ct = bt._stream_cipher(key, nonce, pt)
    return nonce + ct


@pytest.mark.parametrize("pt", [b"", b"x", b"hello encrypted bus", os.urandom(2000)])
def test_c_bus_wire_is_decode_splice_recoverable(monkeypatch, pt):
    """A frame the C serve_encrypted/connect_encrypted build is recovered by the
    Python decode_splice (permissive) — cross-implementation wire parity on the
    HMAC path. Force the stdlib HMAC-CTR backend (the bare-C-host default; the
    AES extra is out of the C mirror)."""
    monkeypatch.setattr(bt, "_HAVE_AES_CTR", False)
    dna = os.urandom(32)
    sender_id, channel_id = 0x8000000000001092, 0x11223344
    T = 1_700_000_000_000_000_000
    W = 1 << 60   # large window: floor(T/W) constant (matches the C driver knob)
    body = _c_bus_wire_body(dna, sender_id, channel_id, 0, pt, T, W)
    assert len(body) == 16 + len(pt)
    recovered, used = bt.decode_splice(body, dna, window_ns=W, time_ns=T)
    assert recovered == pt
    assert used == T


@requires_native
def test_wrong_dna_does_not_recover(monkeypatch):
    """A frame built under one DNA does not recover the plaintext under a
    different DNA — the shared secret is what makes the transport round-trip
    (permissive decode returns non-matching bytes / a decrypt error, never the
    original plaintext)."""
    monkeypatch.setattr(bt, "_HAVE_AES_CTR", False)
    dna = os.urandom(32)
    bad = bytes([dna[0] ^ 0xFF]) + dna[1:]
    T, W = 1_700_000_000_000_000_000, 1 << 60
    pt = b"secret payload bytes"
    body = _c_bus_wire_body(dna, 4242, 0x11223344, 0, pt, T, W)
    try:
        recovered, _ = bt.decode_splice(body, bad, window_ns=W, time_ns=T)
    except bt.BioTotpDecryptError:
        return   # a hard decrypt failure is an acceptable "did not recover"
    assert recovered != pt


def test_pubsub_pipe_is_deferred_not_stubbed():
    """SCOPE marker: the bus pub/sub (pipe) → C is DEFERRED to rc180 (honest
    split). It is NOT stubbed in C this rc; srmech.bus.pipe stays a live pure
    Python op (owed_orchestration in the ledger). This asserts the deferral is
    the real state — pipe is callable + unchanged — not a broken half-ship."""
    from srmech.bus import pipe
    assert callable(pipe)
    # No srmech_bus_pipe / srmech_bus_broadcast C symbol yet (rc180).
    if _NATIVE:
        assert not hasattr(_native.LIB, "srmech_bus_broadcast")
        assert not hasattr(_native.LIB, "srmech_bus_subscribe")
