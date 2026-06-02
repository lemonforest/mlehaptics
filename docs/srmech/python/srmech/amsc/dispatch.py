"""Class D — late-binding / dispatch primitive (Task #217 Phase C1).

Single operation: :func:`match` — given an input byte sequence and an
ordered list of (pattern, tag) rules, find the first rule whose pattern
occurs in the input and return its tag. Multi-needle byte-pattern
dispatcher; the "select an implementation at runtime" primitive
expressed as a flat operation on bytes.

Class D is universal across srmech's Spike #24 cross-substrate audit
(instantiated at five of six bonus substrates). The C path
(``srmech_dispatch_match``) builds on Class G's byte search; the
pure-Python fallback uses ``bytes.find``.

API
---

- :func:`match(input, rules)` — ``rules`` is an iterable of
  ``(pattern_bytes, tag_int)`` pairs. Returns ``(matched: bool,
  tag: int)``. ``matched`` is False iff none of the patterns
  occurs in ``input``.
"""

from __future__ import annotations

import ctypes
from typing import Iterable, Tuple

from . import _native

__all__ = ["match", "mirror_pattern"]


def mirror_pattern(pattern: bytes) -> bytes:
    """Harmonic-2 chiral mirror of a dispatch pattern (F150): the byte-reversed
    needle. Class D is harmonic-2 (chiral inverse / self-inverse) per F150 §6.1
    — ``mirror_pattern(mirror_pattern(p)) == p`` (period 2). Matching a
    mirror-reversed input against the mirrored pattern yields the mirror match;
    the chirality-aware companion to :func:`match`. ``pattern`` is bytes-like.
    """
    if not isinstance(pattern, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"pattern must be bytes-like; got {type(pattern).__name__}"
        )
    return bytes(pattern)[::-1]


def match(input_bytes: bytes,
          rules: Iterable[Tuple[bytes, int]]) -> Tuple[bool, int]:
    """First-match dispatcher: return the tag of the first rule whose
    pattern occurs in ``input_bytes``.

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_def_parity.py``.
    """
    if not isinstance(input_bytes, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"input must be bytes-like; got {type(input_bytes).__name__}"
        )
    rule_list = [(bytes(p), int(t)) for (p, t) in rules]
    n_rules = len(rule_list)
    input_b = bytes(input_bytes)
    if _native.HAS_NATIVE and _native.LIB is not None:
        # Pack patterns into a contiguous buffer + parallel arrays.
        patterns_buf = bytearray()
        offsets = (ctypes.c_uint32 * max(n_rules, 1))()
        lengths = (ctypes.c_uint32 * max(n_rules, 1))()
        tags = (ctypes.c_uint32 * max(n_rules, 1))()
        for i, (p, t) in enumerate(rule_list):
            offsets[i] = len(patterns_buf)
            lengths[i] = len(p)
            tags[i] = t
            patterns_buf.extend(p)
        pat_buf_c = (
            (ctypes.c_uint8 * len(patterns_buf)).from_buffer_copy(bytes(patterns_buf))
            if len(patterns_buf) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        input_c = (
            (ctypes.c_uint8 * len(input_b)).from_buffer_copy(input_b)
            if len(input_b) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        out_matched = ctypes.c_bool(False)
        out_tag = ctypes.c_uint32(0)
        rc = _native.LIB.srmech_dispatch_match(
            input_c, ctypes.c_uint32(len(input_b)),
            pat_buf_c, offsets, lengths, tags,
            ctypes.c_uint32(n_rules),
            ctypes.byref(out_matched), ctypes.byref(out_tag),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_dispatch_match returned {rc}")
        return bool(out_matched.value), int(out_tag.value)
    # Pure-Python fallback: bytes.find iteration.
    for p, t in rule_list:
        if len(p) == 0:
            return True, t  # empty pattern matches at 0
        if input_b.find(p) >= 0:
            return True, t
    return False, 0
