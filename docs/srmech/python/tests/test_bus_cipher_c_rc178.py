"""rc178 ANNEX Batch A part 1 — the bus Bio-TOTP wire cipher → C.

A FAITHFUL BYTE-EXACT mirror of the already-shipped Python cipher
(``srmech/bus/_bio_totp.py``), the DEFAULT stdlib HMAC-SHA-256 counter-mode
path. This file pins:

* ``srmech_hmac_sha256`` against the RFC 4231 HMAC-SHA-256 test vectors AND
  against Python ``hmac.new(key, msg, sha256)`` over a random sweep.
* the native Bio-TOTP path == the forced-pure path for ``derive_key`` /
  the HMAC-CTR keystream / ``decode_splice`` (accept / ±window walk /
  binding mismatch / wrong-key / empty / short-frame), plus the encrypt→
  decrypt round-trip.

Parity IS the correctness + safety property — a deviation would silently
break the wire cipher's compatibility / security. numpy-free (stdlib
hmac / hashlib / json). The optional AES-128-CTR backend (the ``[crypto]``
extra) is out of scope: every test forces the default HMAC-CTR path via
``_HAVE_AES_CTR = False`` so the native HMAC peer is the one exercised.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os

import pytest

from srmech.amsc import _native
import srmech.bus._bio_totp as bt

WIN = bt.DEFAULT_WINDOW_NS
_NATIVE = _native.has_native_bio_totp()

# The RFC 4231 HMAC-SHA-256 test vectors (full 32-byte MACs; the truncation
# vector 5 is omitted — we never truncate).
_RFC4231 = [
    (b"\x0b" * 20, b"Hi There",
     "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"),
    (b"Jefe", b"what do ya want for nothing?",
     "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"),
    (b"\xaa" * 20, b"\xdd" * 50,
     "773ea91e36800e46854db8ebd09181a72959098b3ef8c122d9635514ced565fe"),
    (bytes(range(1, 26)), b"\xcd" * 50,
     "82558a389a443c0ea4cc819899f2083a85f0faa3e578f8077a2e3ff46729665b"),
    (b"\xaa" * 131,
     b"Test Using Larger Than Block-Size Key - Hash Key First",
     "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54"),
    (b"\xaa" * 131,
     b"This is a test using a larger than block-size key and a larger "
     b"than block-size data. The key needs to be hashed before being "
     b"used by the HMAC algorithm.",
     "9b09ffa71b942fcb27635fbcd5b0e944bfdc63644f0713938a7f51535c3a35e2"),
]

requires_native = pytest.mark.skipif(
    not _NATIVE, reason="native Bio-TOTP cipher peer not loaded")


# ──────────────────────────────────────────────────────────────────────
# HMAC-SHA-256 — RFC 4231 + Python parity
# ──────────────────────────────────────────────────────────────────────

@requires_native
@pytest.mark.parametrize("key,msg,expected", _RFC4231)
def test_hmac_sha256_rfc4231_vectors(key, msg, expected):
    assert _native.hmac_sha256_c(key, msg).hex() == expected


@requires_native
def test_hmac_sha256_matches_python_hmac_sweep():
    rng = __import__("random").Random(1789)
    for _ in range(300):
        k = bytes(rng.randrange(256) for _ in range(rng.randint(0, 90)))
        m = bytes(rng.randrange(256) for _ in range(rng.randint(0, 400)))
        assert _native.hmac_sha256_c(k, m) == hmac.new(k, m, hashlib.sha256).digest()


def test_hmac_vectors_agree_with_python():
    """The pinned RFC 4231 vectors also match Python's hmac (guards the
    fixture even on a no-C host)."""
    for key, msg, expected in _RFC4231:
        assert hmac.new(key, msg, hashlib.sha256).hexdigest() == expected


# ──────────────────────────────────────────────────────────────────────
# native == forced-pure — derive_key / keystream / decode_splice
# ──────────────────────────────────────────────────────────────────────

def _force_pure(mp):
    """Force the pure path: native OFF + the stdlib HMAC-CTR backend."""
    mp.setattr(_native, "has_native_bio_totp", lambda: False)
    mp.setattr(bt, "_HAVE_AES_CTR", False)


def _pure_stream(key, nonce, data):
    """Reference stdlib HMAC-SHA-256 counter-mode keystream XOR."""
    out = bytearray()
    counter = 0
    while len(out) < len(data):
        out.extend(hmac.new(key, nonce + counter.to_bytes(4, "big"),
                            hashlib.sha256).digest())
        counter += 1
    ks = bytes(out[:len(data)])
    return bytes(a ^ b for a, b in zip(data, ks))


@requires_native
def test_derive_key_native_equals_pure(monkeypatch):
    rng = __import__("random").Random(42)
    cases = []
    for _ in range(200):
        dna = os.urandom(rng.choice([32, 33, 40, 64]))
        t = rng.randint(-(10 ** 18), 2 * 10 ** 18)
        w = rng.choice([WIN, 1, 7, 30_000_000_000])
        cases.append((dna, t, w))
    native = [bt.derive_key(d, t, w) for d, t, w in cases]  # native ON
    with monkeypatch.context() as mp:
        _force_pure(mp)
        pure = [bt.derive_key(d, t, w) for d, t, w in cases]
    assert native == pure
    # and both equal the independent reference
    for (d, t, w), nk in zip(cases, native):
        q = t // w
        ref = bytes.fromhex(hashlib.sha256(
            bytes(d) + q.to_bytes(8, "big", signed=True)).hexdigest())[:16]
        assert nk == ref


@requires_native
def test_keystream_native_equals_pure(monkeypatch):
    key = os.urandom(16)
    nonce = bt.build_nonce(4242, 0x11223344, 7)
    for n in [0, 1, 31, 32, 33, 64, 65, 179, 512]:
        data = os.urandom(n)
        monkeypatch.setattr(bt, "_HAVE_AES_CTR", False)
        native = bt._stream_cipher(key, nonce, data)   # native ON
        with monkeypatch.context() as mp:
            _force_pure(mp)
            pure = bt._stream_cipher(key, nonce, data)
        assert native == pure == _pure_stream(key, nonce, data)


def _event(sender, channel, extra=None):
    att = {"sender_pid": sender, "sender_name": "n", "ts_ns": 5,
           "sender_id_u64": sender, "channel_id_u32": channel}
    if extra:
        att.update(extra)
    ev = {"mpr_version": "bus/1", "type": "t", "payload": {"a": 1},
          "attestation": att}
    return json.dumps(ev, ensure_ascii=False, sort_keys=True).encode()


def _decode_verdict(fn):
    try:
        return ("ok", fn())
    except bt.BioTotpFormatError:
        return ("format",)
    except bt.BioTotpDecryptError:
        return ("decrypt",)


@requires_native
def test_decode_splice_native_equals_pure(monkeypatch):
    """decode_splice native == forced-pure over accept / ±window walk /
    binding mismatch / wrong-key / empty / short-frame."""
    monkeypatch.setattr(bt, "_HAVE_AES_CTR", False)
    orig = _native.has_native_bio_totp
    sender, channel = 4242, 0x11223344
    nonce = bt.build_nonce(sender, channel, 7)
    T = 1_700_000_000_000_000_000

    def build(dna, ev, t):
        key = bt.derive_key(dna, t, WIN)
        return nonce + bt._stream_cipher(key, nonce, ev)

    rng = __import__("random").Random(7)
    for _ in range(120):
        dna = os.urandom(32)
        frames = []
        # accept: matched binding, current window
        frames.append((build(dna, _event(sender, channel), T), dna))
        # ±window: frame minted one window away
        for d in (-1, 1):
            frames.append((build(dna, _event(sender, channel), T + d * WIN), dna))
        # binding mismatch (valid JSON, wrong sender) at current window
        frames.append((build(dna, _event(sender + rng.randint(1, 9), channel), T),
                       dna))
        # wrong dna secret
        frames.append((build(dna, _event(sender, channel), T), os.urandom(32)))
        # empty ciphertext (bare nonce)
        frames.append((nonce, dna))
        for frame, key_dna in frames:
            _native.has_native_bio_totp = orig
            vn = _decode_verdict(
                lambda: bt.decode_splice(frame, key_dna, window_ns=WIN, time_ns=T))
            _native.has_native_bio_totp = lambda: False
            vp = _decode_verdict(
                lambda: bt.decode_splice(frame, key_dna, window_ns=WIN, time_ns=T))
            _native.has_native_bio_totp = orig
            assert vn == vp, (vn, vp)
    # short frames -> BioTotpFormatError both paths
    for bad in [b"", b"short", os.urandom(15)]:
        _native.has_native_bio_totp = orig
        vn = _decode_verdict(
            lambda: bt.decode_splice(bad, os.urandom(32), window_ns=WIN, time_ns=T))
        _native.has_native_bio_totp = lambda: False
        vp = _decode_verdict(
            lambda: bt.decode_splice(bad, os.urandom(32), window_ns=WIN, time_ns=T))
        _native.has_native_bio_totp = orig
        assert vn == vp == ("format",)


@requires_native
def test_decode_splice_accept_recovers_plaintext(monkeypatch):
    monkeypatch.setattr(bt, "_HAVE_AES_CTR", False)
    sender, channel = 4242, 0x11223344
    nonce = bt.build_nonce(sender, channel, 7)
    T = 1_700_000_000_000_000_000
    dna = os.urandom(32)
    ev = _event(sender, channel)
    frame = nonce + bt._stream_cipher(bt.derive_key(dna, T, WIN), nonce, ev)
    pt, used = bt.decode_splice(frame, dna, window_ns=WIN, time_ns=T)
    assert pt == ev and used == T


@requires_native
def test_encrypt_decrypt_round_trip_hmac_path(monkeypatch):
    """Full BioTotpChannel round-trip on the HMAC-CTR path — and a native-
    encrypted frame decrypts under the forced-pure backend (cross-parity)."""
    monkeypatch.setattr(bt, "_HAVE_AES_CTR", False)
    dna = os.urandom(32)
    T = 1_700_000_000_000_000_000
    for pt in [b"", b"x", b"hello bio-totp" * 20, os.urandom(500)]:
        enc = bt.BioTotpChannel(dna=dna, sender_id=1234, channel_id=987654321)
        frame = enc.encrypt(pt, time_ns=T)          # native crypto
        dec = bt.BioTotpChannel(dna=dna, sender_id=1234, channel_id=987654321)
        assert dec.decrypt(frame, time_ns=T) == pt
        # cross-parity: force pure and decrypt the SAME native-made frame
        with monkeypatch.context() as mp:
            _force_pure(mp)
            dec2 = bt.BioTotpChannel(dna=dna, sender_id=1234, channel_id=987654321)
            assert dec2.decrypt(frame, time_ns=T) == pt


@requires_native
def test_strict_decrypt_rejects_wrong_dna(monkeypatch):
    """The strict binding still rejects a wrong-DNA frame with the native
    crypto in play (bus-consumer implicit-MAC discipline)."""
    monkeypatch.setattr(bt, "_HAVE_AES_CTR", False)
    dna = os.urandom(32)
    T = 1_700_000_000_000_000_000
    enc = bt.BioTotpChannel(dna=dna, sender_id=4242, channel_id=0x11223344,
                            strict=True)
    ev = _event(4242, 0x11223344)
    frame = enc.encrypt(ev, time_ns=T)
    good = bt.BioTotpChannel(dna=dna, sender_id=4242, channel_id=0x11223344,
                             strict=True)
    assert good.decrypt(frame, time_ns=T) == ev
    bad = bt.BioTotpChannel(dna=os.urandom(32), sender_id=4242,
                            channel_id=0x11223344, strict=True)
    with pytest.raises(bt.BioTotpDecryptError):
        bad.decrypt(frame, time_ns=T)
