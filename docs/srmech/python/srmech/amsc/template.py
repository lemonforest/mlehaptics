"""Class F — substitution / templating primitive (Task #217 Phase C1).

Single operation: :func:`render` — given a template byte sequence with
``{key}`` placeholders and a (key, value) mapping, expand placeholders
into the output bytes.

Class F is the placeholder-substitution primitive. The existing
``srmech.amsc.descriptor.render_template`` is a higher-level Python
form of the same operation tailored to descriptor cite/purpose
templates; this module exposes the bare primitive so the C path is
reachable when needed.

Format
------

- Plain bytes pass through verbatim.
- ``{key}`` substitutes with the value bytes for ``key`` from the
  mapping.
- Unterminated ``{...`` or unknown key raises ``ValueError``.

No escape sequences for ``{`` and ``}`` (keep simple per JPL discipline
on the C side). To emit a literal brace, supply a mapping entry whose
value is the brace byte.

API
---

- :func:`render(template, mapping)` — ``mapping`` is a dict-like of
  ``bytes → bytes``. Returns the rendered ``bytes``.
"""

from __future__ import annotations

import ctypes
from typing import Mapping

from . import _native

__all__ = ["render"]


def render(template_bytes: bytes,
           mapping: Mapping[bytes, bytes]) -> bytes:
    """Render ``template_bytes`` with ``{key}`` placeholders expanded
    via ``mapping``.

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_def_parity.py``.
    """
    if not isinstance(template_bytes, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"template must be bytes-like; got {type(template_bytes).__name__}"
        )
    t = bytes(template_bytes)
    # Normalise + sort the mapping for binary-search semantics.
    items = sorted(
        ((bytes(k), bytes(v)) for k, v in mapping.items()),
        key=lambda kv: kv[0],
    )
    n_pairs = len(items)
    if _native.HAS_NATIVE and _native.LIB is not None:
        keys_buf = bytearray()
        values_buf = bytearray()
        key_off = (ctypes.c_uint32 * max(n_pairs, 1))()
        key_len = (ctypes.c_uint32 * max(n_pairs, 1))()
        val_off = (ctypes.c_uint32 * max(n_pairs, 1))()
        val_len = (ctypes.c_uint32 * max(n_pairs, 1))()
        for i, (k, v) in enumerate(items):
            key_off[i] = len(keys_buf)
            key_len[i] = len(k)
            keys_buf.extend(k)
            val_off[i] = len(values_buf)
            val_len[i] = len(v)
            values_buf.extend(v)
        # Output capacity: tmpl_len + sum(value_lens) is a generous
        # upper bound; sum(value_lens - 2 - key_lens) per substitution
        # would be tighter, but the buffer is short-lived.
        total_value_bytes = sum(int(val_len[i]) for i in range(n_pairs))
        capacity = len(t) + total_value_bytes + 64
        out_buf = (ctypes.c_uint8 * capacity)()
        out_written = ctypes.c_uint32(0)
        tmpl_c = (
            (ctypes.c_uint8 * len(t)).from_buffer_copy(t)
            if len(t) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        keys_c = (
            (ctypes.c_uint8 * len(keys_buf)).from_buffer_copy(bytes(keys_buf))
            if len(keys_buf) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        vals_c = (
            (ctypes.c_uint8 * len(values_buf)).from_buffer_copy(bytes(values_buf))
            if len(values_buf) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        rc = _native.LIB.srmech_template_render(
            tmpl_c, ctypes.c_uint32(len(t)),
            keys_c, key_off, key_len,
            vals_c, val_off, val_len,
            ctypes.c_uint32(n_pairs),
            out_buf, ctypes.c_uint32(capacity),
            ctypes.byref(out_written),
        )
        if rc == _native.SRMECH_ERR_BAD_INPUT:
            raise ValueError(
                "template render failed: unterminated `{...` or unknown key"
            )
        if rc == _native.SRMECH_ERR_OVERFLOW:
            raise OverflowError(
                "template render output exceeded buffer capacity"
            )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_template_render returned {rc}")
        return bytes(out_buf[: out_written.value])
    # Pure-Python fallback: hand-roll the same scan-and-substitute.
    item_dict = {k: v for k, v in items}
    out = bytearray()
    i = 0
    while i < len(t):
        if t[i] != 0x7B:  # `{`
            out.append(t[i])
            i += 1
            continue
        key_start = i + 1
        key_end = key_start
        while key_end < len(t) and t[key_end] != 0x7D:  # `}`
            key_end += 1
        if key_end >= len(t):
            raise ValueError("template render failed: unterminated `{...`")
        key = t[key_start:key_end]
        if key not in item_dict:
            raise ValueError(
                f"template render failed: unknown key {key!r}"
            )
        out.extend(item_dict[key])
        i = key_end + 1
    return bytes(out)
