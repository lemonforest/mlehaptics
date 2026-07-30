"""THE embedded-byte-array decoder for the generated C registries — one copy.

rc361 (`#T1034`). EXTRACTED, not written: this decoder was built at rc359
(`#T1035`) inside ``tests/test_ref_notation_emitted_rc348.py`` to find bare
``#NNN`` refs hiding inside byte arrays. rc361 needs the SAME decode step to
count dotted NAMESPACE PREFIXES for the ADR-0010 declustering arc, so the
regex + decode moved here and both gates now import it.

Forking it would have been the very defect the sibling rc361 instrument
exists to stop: ``tests/test_rosetta_roots_single_source_rc361.py`` fails the
build if a 12-entry root tuple gains a fifth copy, and it would be
incoherent to fix that duplication while minting a second decoder in the same
rc. One decoder also means a fix to the extraction (a generator that switches
to hex literals, say) reaches every consumer at once instead of leaving the
newer gate silently reading zero.

WHY A DECODER IS NEEDED AT ALL
==============================
Three of the six regen-all artifacts do not store their text as text. They
bake it as DECIMAL BYTE ARRAYS::

    static const unsigned char cls_desc_0[] = {
        99, 46, 99, 97, 115, 99, 97, 100, 101, ...
    };

To ``grep`` that is a wall of integers. Measured at rc361, counting the
dotted prefix ``srmech.amsc.``:

    srmech_carrier_registry.c      191 as-text /  533 DECODED
    srmech_class_registry.c          0 as-text /   40 DECODED
    srmech_tool_registry.c        1219 as-text /    4 DECODED
    srmech_responsion_registry.c    72 as-text /    0 DECODED

The MIXED rows are more dangerous than the invisible one. A textual sweep
over the carrier registry reports 191 hits, "fixes" them, exits clean — and
533 survive in the compiled table that a bare-C host reads directly. A flat
``0`` at least invites suspicion; ``191`` looks like a completed job.

THERE IS NO SHIPPED srmech OP TO REUSE HERE, AND THAT WAS CHECKED
================================================================
Introspected at rc361 across the 516-name registry and the off-registry
surface: srmech ships nothing that turns a sequence of ints 0-255 into a
``str``. ``amsc.tlv.tlv_unpack`` and ``amsc.search.byte_search`` both
hard-``TypeError`` on a non-bytes-like argument and return ``bytes`` / ``int``
anyway; ``amsc.text.*`` is str-in; the decode-DIRECTION ops
(``cascade.hamming_decode_correct``, ``hdc.klein4_holographic_decode``,
``genome.kernel_unpack``, ``bus.decode_splice``, the ``closed_form_ops``
codecs) return bits / ints / bytes / catalog labels, never decoded text. The
closest shipped pieces are the ``HV`` carrier's ``from_sequence`` (which does
own the 0-255 range guard) plus ``HV.tobytes``, but ``HV`` is a carrier class,
not a registered op, and the final ``.decode`` would still be stdlib.

So this is verification tooling, correctly living in ``tests/``. It is NOT a
missing shipped op and must not be "promoted" into the package to satisfy a
parity ratchet — nothing in srmech's own surface needs to read its own
generated C tables.
"""
from __future__ import annotations

import re
from pathlib import Path

#: A C byte-array literal: `static const unsigned char NAME[] = { 1, 2, ... };`
BYTE_ARRAY = re.compile(
    r"static\s+const\s+unsigned\s+char\s+(\w+)\s*\[\]\s*=\s*\{(.*?)\}\s*;",
    re.DOTALL)

#: An octal escape inside a C string literal: ``\101``, ``\12``, ``\7``.
#:
#: The generated registries ALSO carry text as string literals with non-ASCII
#: bytes octal-escaped (21,297 of them in the tool registry alone). That is a
#: THIRD encoding channel, and the reason it does not need its own decoder is
#: MEASURED rather than assumed — see ``octal_escaped_name_chars`` below.
OCTAL_ESCAPE = re.compile(r"\\([0-7]{1,3})")

#: The characters a dotted srmech op name can be built from. An octal escape
#: decoding to one of these would mean the as-text channel is INCOMPLETE — part
#: of a name would be spelled as an escape and no textual count could see it.
_NAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._")


def decoded_blobs(path: Path) -> "list[tuple[str, str]]":
    """Every embedded byte array in ``path``, decoded to the text it carries.

    Returns ``(array_name, text)``. Non-UTF-8 bytes are replaced rather than
    raising: the point is to read the CONTENT present, not to validate
    encoding. (The payloads are genuinely UTF-8 — the class registry carries
    em-dashes as ``226, 128, 148`` — but a replacement char can never
    manufacture a false ASCII match, so ``errors="replace"`` is safe for
    counting.)

    Non-``.c`` files return ``[]``: the two generated ``.py`` artifacts embed
    no byte arrays. That is verified, not assumed — their long integer runs
    were inspected at rc361 and are worked-example OUTPUT VALUES (octonion
    basis vectors, inertia signatures, index triples), not encoded text.
    """
    if path.suffix != ".c":
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    out: "list[tuple[str, str]]" = []
    for m in BYTE_ARRAY.finditer(text):
        nums = [int(t) for t in re.findall(r"\d+", m.group(2))]
        if not nums or any(n > 255 for n in nums):
            continue                       # not a byte payload
        out.append((m.group(1), bytes(nums).decode("utf-8", errors="replace")))
    return out


def octal_escaped_name_chars(path: Path) -> "list[int]":
    """Octal escapes in ``path`` that decode to a dotted-name character.

    This is the completeness proof for the AS-TEXT channel. A plain
    ``str.count("srmech.amsc.")`` over the raw file is only a valid measure of
    the string-literal channel while no character OF A NAME is written as an
    escape. Measured at rc361: the four registries carry 21,474 octal escapes
    between them and NONE decodes into ``[A-Za-z0-9._]`` — every escape is a
    non-ASCII UTF-8 byte. So the textual count is complete, and this returns
    an empty list.

    If a future generator ever escapes ASCII, this returns non-empty and the
    as-text half of the ratchet has silently started undercounting.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    return [v for v in (int(e, 8) for e in OCTAL_ESCAPE.findall(text))
            if v < 128 and chr(v) in _NAME_CHARS]
