"""W4 (RBS-LM bugfix wishlist) — ``sha256_hex`` / ``sha256_raw`` companions.

``sha256_bytes`` returns a 64-char hex *str* (the ``_bytes`` names the INPUT
type, not the return type), which trips callers who read it as a return type.
v0.7.5rc1 adds the name-says-return alias ``sha256_hex`` and the raw-32-byte
companion ``sha256_raw``. Both ride the SAME native/stdlib dispatch as
``sha256_bytes`` (no new ``hashlib.sha256`` call site — Phase B5 discipline).
"""

from __future__ import annotations

import hashlib

import pytest

from srmech.amsc.format import sha256_bytes, sha256_hex, sha256_raw

_VECTORS = [b"", b"abc", b"the quick brown fox", bytes(range(256)), b"\x00" * 100]


@pytest.mark.parametrize("data", _VECTORS)
def test_sha256_hex_equals_sha256_bytes_and_hashlib(data: bytes) -> None:
    """``sha256_hex`` is the value-identical alias of ``sha256_bytes`` and of
    ``hashlib.sha256(...).hexdigest()``."""
    expected = hashlib.sha256(data).hexdigest()
    assert sha256_hex(data) == expected
    assert sha256_hex(data) == sha256_bytes(data)
    assert len(sha256_hex(data)) == 64
    assert sha256_hex(data) == sha256_hex(data).lower()


@pytest.mark.parametrize("data", _VECTORS)
def test_sha256_raw_returns_32_raw_bytes(data: bytes) -> None:
    """``sha256_raw`` returns the raw 32-byte digest (``bytes``), matching
    ``hashlib.sha256(...).digest()`` — the companion the name ``sha256_bytes``
    falsely promised."""
    raw = sha256_raw(data)
    assert isinstance(raw, bytes)
    assert len(raw) == 32
    assert raw == hashlib.sha256(data).digest()


@pytest.mark.parametrize("data", _VECTORS)
def test_hex_and_raw_are_two_views_of_one_digest(data: bytes) -> None:
    """The hex string and the raw bytes are two encodings of the same digest:
    ``sha256_raw(d).hex() == sha256_hex(d)`` and
    ``int.from_bytes(sha256_raw(d), "big") == int(sha256_hex(d), 16)`` — the
    int-from-bytes path W4 unblocks."""
    assert sha256_raw(data).hex() == sha256_hex(data)
    assert int.from_bytes(sha256_raw(data), "big") == int(sha256_hex(data), 16)


def test_exported_at_amsc_level() -> None:
    """Both names are re-exported at the ``srmech.amsc`` package level."""
    import srmech.amsc as amsc

    assert amsc.sha256_hex(b"x") == amsc.sha256_bytes(b"x")
    assert amsc.sha256_raw(b"x") == hashlib.sha256(b"x").digest()
