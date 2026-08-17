"""Class-B TLV round-trip parity — the WRITER and the READER, both projections.

rc441 (``#T1148``) — the v20 prerequisites.

Through rc440 Class B shipped ``srmech_tlv_pack`` in C with **no reader half**:
``tlv_unpack`` existed in Python only (``srmech/math/tlv.py``), while the
compiled tool registry (``srmech_tool_registry.c``) advertised it to every MCP
client as *"the ONLY correct way to read these frames back"*. A bare-C host
could therefore EMIT a frame it had no sanctioned way to walk — half a
projection of a format whose whole point is that it round-trips.

This file pins the closed loop:

* ``tlv_unpack(tlv_pack(t, v)) == (t, v, 5 + len(v))`` — exact round trip;
* feeding ``next_offset`` back in walks a concatenation to exactly its length;
* the native and pure paths agree on EVERY case, including every malformed
  one, in the RAISED MESSAGE as well as the value (the C peer declines with
  ``SRMECH_ERR_BAD_INPUT`` and the pure body stays the oracle for the text);
* the u32 length field cannot wrap the end-bound check and hand back a span
  that runs off the buffer.

The malformed cases are the reason this file is not just "round trip works":
a frame reader's two classic defects are trusting an attacker-supplied length
and reading the length in host byte order, and both are only visible on inputs
that are *wrong*.

No stdlib ``fractions`` / ``math`` / ``decimal`` / numpy. No ``abs()``.
"""

from __future__ import annotations

import pytest

from srmech import _native
from srmech.math import tlv


# ──────────────────────────────────────────────────────────────────────
# The case grid — shared by the parity sweep and the pure-path pins.
# ──────────────────────────────────────────────────────────────────────

def _stream() -> bytes:
    """A three-frame concatenation, the shape the registry's worked example
    walks: a DOI, a 64-char digest, and a codon table."""
    return (tlv.tlv_pack(1, b"10.1093/database/baaa062")
            + tlv.tlv_pack(2, b"d" * 64)
            + tlv.tlv_pack(7, b"FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRR" * 2))


def _cases() -> "list[tuple[bytes, int]]":
    cases: "list[tuple[bytes, int]]" = []
    # Well-formed frames across the tag range and the value-length range.
    for tag in (0, 1, 7, 128, 255):
        for n in (0, 1, 2, 3, 31, 32, 255, 256, 1024):
            payload = bytes((i * 7 + n) % 256 for i in range(n))
            cases.append((tlv.tlv_pack(tag, payload), 0))
    # Every offset into a real stream, including past its end.
    stream = _stream()
    for off in range(len(stream) + 3):
        cases.append((stream, off))
    # Every truncation of a real frame — the clipped-prefix / clipped-value
    # boundary is where a reader hands back partial data if it is going to.
    frame = tlv.tlv_pack(3, b"ATGCATGC")
    for k in range(len(frame) + 1):
        cases.append((frame[:k], 0))
    # A length field that claims more than remains, up to the u32 ceiling:
    # the wrap case that a 32-bit end bound would admit.
    for claim in (1, 2, 6, 0x7FFF_FFFF, 0xFFFF_FFFE, 0xFFFF_FFFF):
        cases.append((bytes([9]) + claim.to_bytes(4, "big") + b"xy", 0))
    # Degenerate buffers and out-of-range offsets.
    for buf in (b"", b"\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00"):
        for off in (-1, 0, 1, 5, 99):
            cases.append((buf, off))
    return cases


def _call(buffer, offset):
    """``("ok", value)`` or ``("raise", type-name, message)`` — the message is
    part of the contract, so a divergence in TEXT is a divergence."""
    try:
        return ("ok", tlv.tlv_unpack(buffer, offset))
    except Exception as exc:                     # noqa: BLE001 — text is the contract
        return ("raise", type(exc).__name__, str(exc))


# ──────────────────────────────────────────────────────────────────────
# Round trip + walk (projection-independent)
# ──────────────────────────────────────────────────────────────────────

def test_round_trip_is_exact():
    for tag in (0, 1, 7, 128, 255):
        for n in (0, 1, 5, 64, 300):
            value = bytes((i * 3 + 1) % 256 for i in range(n))
            assert tlv.tlv_unpack(tlv.tlv_pack(tag, value)) == (
                tag, value, tlv.TLV_PREFIX_BYTES + n
            )


def test_next_offset_walks_a_concatenation_exactly():
    stream = _stream()
    seen, off, guard = [], 0, 0
    while off < len(stream):
        tag, value, off = tlv.tlv_unpack(stream, off)
        seen.append((tag, len(value)))
        guard += 1
        assert guard <= 16, "walk did not terminate — next_offset is not advancing"
    assert off == len(stream), "the walk must land on exactly the stream length"
    assert seen == [(1, 24), (2, 64), (7, 64)]


def test_malformed_frames_raise_and_never_return_partial_data():
    # A claimed length past the end must RAISE, not hand back what remains.
    clipped = tlv.tlv_pack(1, b"0123456789")[:8]
    with pytest.raises(ValueError, match="truncated TLV value"):
        tlv.tlv_unpack(clipped)
    with pytest.raises(ValueError, match="truncated TLV prefix"):
        tlv.tlv_unpack(b"\x01\x00\x00")
    with pytest.raises(ValueError, match="out of range"):
        tlv.tlv_unpack(b"", 1)


def test_u32_length_cannot_wrap_the_end_bound():
    """A frame claiming 0xFFFFFFFF bytes must decline, not wrap to a small
    end and return an in-bounds-looking span."""
    for claim in (0x7FFF_FFFF, 0xFFFF_FFFE, 0xFFFF_FFFF):
        buf = bytes([9]) + claim.to_bytes(4, "big") + b"xy"
        with pytest.raises(ValueError, match="truncated TLV value"):
            tlv.tlv_unpack(buf)


# ──────────────────────────────────────────────────────────────────────
# C ↔ Python parity (requires HAS_NATIVE)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_c_peer_is_exported():
    """The reader half must actually be IN the loaded library — a Python-only
    fallback that silently never dispatches is exactly the rc440 state this
    rc closes, and it would leave every parity case below vacuously green."""
    assert hasattr(_native.LIB, "srmech_tlv_unpack"), (
        "srmech_tlv_unpack is not exported by the loaded libsrmech — the C "
        "reader half is missing or the .so is stale"
    )


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_tlv_unpack_matches_pure_on_every_case():
    saved = _native.HAS_NATIVE
    cases = _cases()
    assert len(cases) > 100, "the grid collapsed — this would pass vacuously"
    divergences = []
    try:
        for buffer, offset in cases:
            _native.HAS_NATIVE = True
            native = _call(buffer, offset)
            _native.HAS_NATIVE = False
            pure = _call(buffer, offset)
            if native != pure:
                divergences.append((bytes(buffer)[:16], offset, native, pure))
    finally:
        _native.HAS_NATIVE = saved
    assert not divergences, (
        f"{len(divergences)} native/pure divergences: {divergences[:5]}"
    )


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_accepts_bytearray_and_memoryview_carriers():
    frame = tlv.tlv_pack(11, b"carrier")
    expect = (11, b"carrier", tlv.TLV_PREFIX_BYTES + 7)
    assert tlv.tlv_unpack(bytearray(frame)) == expect
    assert tlv.tlv_unpack(memoryview(frame)) == expect
