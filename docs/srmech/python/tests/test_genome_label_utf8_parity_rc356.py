"""rc356 (`#T954`) — an undecodable cap label is a GenomeBoundingError in BOTH
projections, and the C declines it on its own.

§44 defines a cap label as UTF-8 bytes up to the first NUL. Both writer halves
enforce that (``_pack_cap`` encodes UTF-8; the C ``genome_pack_cap`` documents
its input as bytes "already UTF-8"), so **no genome srmech wrote can carry a
label that fails to decode.** One that does is ungrammatical — the same class as
``_stream_body_blocks``' "unrecognised block kind byte", which has raised
``GenomeBoundingError`` from three branches away in the same generator all along.

At rc355 the two projections disagreed about what such a strand even IS.
Measured on the public read surface, manifest present, one CHROM label byte set
to ``0xFF``:

===================  =====================  =====================
read                 compiled               scripting
===================  =====================  =====================
catalog              GenomeBoundingError    UnicodeDecodeError
census               GenomeBoundingError    UnicodeDecodeError
content              GenomeBoundingError    UnicodeDecodeError
registry             GenomeBoundingError    UnicodeDecodeError
gene_express_plan    GenomeBoundingError    UnicodeDecodeError
load / window /      UnicodeDecodeError     UnicodeDecodeError
genes / export / …
===================  =====================  =====================

Five splits, and the six rows that "agreed" agreed on the WRONG type: a raw
codec exception, leaked through the ``GenomeBoundingError`` normalisation
boundary it was raised inside. ``UnicodeDecodeError`` names a codec, not a
genome; it carries no path, no genome identity and nothing to distinguish it
from a locale bug in the caller's own code. A caller could not write one
``except`` clause that held on both hosts (ADR-0009).

Worse underneath, and this is the ADR-0003 half. The compiled projection's
``GenomeBoundingError`` above was the rc342 digest bound firing on a byte flip
that happened to break the digest too — the right answer for an unrelated
reason. Asked where no digest binds (§44 rebuild-by-scan, no manifest), the C
returned **SRMECH_OK** and copied the raw ``0xFF`` into its own canonical JSON
output, which RFC 8259 §8.1 then makes invalid JSON. Measured at rc355: status
0, ``0xFF`` at output byte 825, inside ``"label": "g\\xffography"``. The
``UnicodeDecodeError`` the compiled projection showed was not C rejecting
anything — it was the ctypes shim choking on C's success. A bare-C host got
success plus a mangled label and no signal at all.

So rc356 fixes both halves: ``genome_decode_label`` in ``srmech_genome.c``
validates UTF-8 (the file said "labels are UTF-8" four times and checked it
nowhere), and ``genome._decode_label`` normalises the five bare
``.decode("utf-8")`` strand sites. Fixing only the Python side would have left
the bare-C host silently accepting.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from srmech.amsc import _native, hdc
from srmech.amsc import genome as G

_DIM = 64
_GATE = 0b10

#: 0xFF is invalid UTF-8 as a lead byte AND as a continuation byte, so it cannot
#: be excused by any surrounding context — unlike, say, a stray 0x80.
_BAD = 0xFF


def _one():
    return hdc.klein4_expand(_DIM, 0)


def _leaves(n):
    return [G._HV.from_sequence([(i * 7 + j) % 4 for j in range(_DIM)], sectors=4)
            for i in range(n)]


def _save(root, name="g"):
    d = Path(root) / name
    one = _one()
    G.genome_save(G.genome(coupling=one, chromosomes=[
        ("geography", [("rules", _leaves(2), _GATE), ("board", _leaves(2), _GATE)]),
        ("history", [("dates", _leaves(2), _GATE)]),
    ]), str(d), one)
    return d, one


def _set_label_byte(d, value):
    """Overwrite one byte of the FIRST chromosome's label.

    The offset comes from the genome's own catalog, so the vector keeps meaning
    "a label byte" if the on-disk layout shifts.
    """
    off = G.genome_catalog(str(d))["chromosomes"][0]["byte_offset"]
    b = bytearray((d / "turns.bin").read_bytes())
    b[off + 2] = value
    (d / "turns.bin").write_bytes(bytes(b))


#: EVERY native genome gate, not the three the rc342 helper flips.
#:
#: ``tests/test_genome_read_bound_global_rc342.py:259`` forces exactly
#: ``has_native_genome`` / ``_census`` / ``_registry`` off — but ``genes()``
#: gates on ``has_native_genome_genes()``, a different symbol, so its "scripting"
#: run still dispatched into C. There are 44 such gates. Any parity claim built
#: on a partial flip measures less than it says it does, and a projection test
#: that silently runs the same projection twice is the exact false green this
#: rc is about.
def _all_genome_gates():
    return [a for a in dir(_native) if a.startswith("has_native_genome")]


def _pure():
    """Context-manager-ish pair: (restore_map) with every genome gate forced off."""
    saved = {}
    for g in _all_genome_gates():
        saved[g] = getattr(_native, g)
        setattr(_native, g, lambda: False)
    return saved


def _restore(saved):
    for g, fn in saved.items():
        setattr(_native, g, fn)


def _raises(fn):
    try:
        fn()
    except Exception as exc:                     # noqa: BLE001 — the TYPE is the assertion
        return type(exc)
    return None


def test_all_genome_gates_are_flipped_not_three():
    """The helper above must really cover the surface it claims.

    If this ever drops back to a handful, every parity assertion below silently
    weakens without failing.
    """
    gates = _all_genome_gates()
    assert len(gates) >= 40, (
        f"only {len(gates)} has_native_genome* gates found; the scripting "
        f"projection is probably not being forced at all")


@pytest.mark.parametrize("read", ["catalog", "census", "content", "registry"])
def test_undecodable_label_is_a_bounding_error_in_both_projections(read):
    """The five splits, closed.

    Both projections must name the SAME contract violation. The type is the
    assertion — a message would pin prose the two projections have no reason to
    share.
    """
    got = {}
    for projection in ("compiled", "scripting"):
        saved = _pure() if projection == "scripting" else {}
        try:
            with tempfile.TemporaryDirectory() as tmp:
                d, _one = _save(tmp)
                _set_label_byte(d, _BAD)
                call = {
                    "catalog": lambda: G.genome_catalog(str(d)),
                    "census": lambda: G.genome_census(str(d)),
                    "content": lambda: G.genome_content(str(d)),
                    "registry": lambda: G.genome_registry(str(d.parent)),
                }[read]
                got[projection] = _raises(call)
        finally:
            _restore(saved)

    assert got["compiled"] is got["scripting"], (
        f"genome_{read} splits on an undecodable label: compiled raises "
        f"{got['compiled']}, scripting raises {got['scripting']}. Under ADR-0009 "
        f"the projections are co-equal; a caller cannot write one except clause "
        f"that holds on both hosts")
    assert got["compiled"] is G.GenomeBoundingError, (
        f"genome_{read} raises {got['compiled']} for a strand whose grammar §44 "
        f"defines; UnicodeDecodeError names a codec, not a genome")


def test_valid_utf8_label_change_is_not_rejected():
    """The negative control, and the one that matters most.

    A guard that rejects an undecodable label is worthless if it also rejects
    decodable ones. Same byte position, same everything, a valid ASCII value —
    and the manifest is dropped so the read goes through §44 rebuild-by-scan
    rather than being answered by a committed digest.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save(tmp)
        _set_label_byte(d, ord("z"))
        (d / "manifest.json").unlink()
        cat = G.genome_catalog(str(d), coupling=one)
        assert cat["chromosomes"][0]["label"] == "gzography", (
            "a VALID utf-8 label edit must read back unchanged; the rc356 guard "
            "is about well-formedness, not about labels being immutable")


def test_clean_genome_is_unaffected():
    """The other half of the negative control: no false positive on a genome
    nobody touched, through both projections."""
    for projection in ("compiled", "scripting"):
        saved = _pure() if projection == "scripting" else {}
        try:
            with tempfile.TemporaryDirectory() as tmp:
                d, _one = _save(tmp)
                cat = G.genome_catalog(str(d))
                assert [c["label"] for c in cat["chromosomes"]] == \
                    ["geography", "history"], f"{projection}: clean genome misread"
        finally:
            _restore(saved)


def test_the_c_declines_it_on_its_own():
    """ADR-0003: the bare-C host must not need Python to catch this.

    Asked where no committed digest can answer for it (no manifest -> §44
    rebuild-by-scan), the C returned SRMECH_OK at rc355 and emitted the raw byte
    into its own canonical JSON. This asserts the C's OWN verdict, through the
    native call, with the scripting path irrelevant.
    """
    if not (_native.HAS_NATIVE and _native.has_native_genome()):
        pytest.skip("native genome ops not loaded — no C verdict to ask for")
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save(tmp)
        _set_label_byte(d, _BAD)
        (d / "manifest.json").unlink()
        exc = _raises(lambda: _native.genome_catalog_c(str(d), one.tobytes()))
        assert exc is not None, (
            "srmech_genome_catalog accepted a strand with a non-UTF-8 label and "
            "emitted it into its own canonical JSON output — which RFC 8259 §8.1 "
            "then makes invalid JSON. A bare-C host gets success plus a mangled "
            "label and no signal")
        assert exc is _native.NativeGenomeError, (
            f"expected the C to DECLINE (NativeGenomeError from a non-OK status); "
            f"got {exc}. A UnicodeDecodeError here means the C still returned OK "
            f"and the ctypes shim choked on decoding its output — which is the "
            f"rc355 behaviour, not a fix")


def test_the_bounding_error_chains_the_codec_exception():
    """The offset must not be lost.

    ``GenomeBoundingError`` is the right TYPE, but a caller debugging a real
    corrupt strand still wants the byte position, and only the codec exception
    knows it. rc294 chained its ``OSError`` for the same reason.
    """
    saved = _pure()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            d, _one = _save(tmp)
            _set_label_byte(d, _BAD)
            with pytest.raises(G.GenomeBoundingError) as ei:
                G.genome_catalog(str(d))
            assert isinstance(ei.value.__cause__, UnicodeDecodeError), (
                "the scripting projection raised GenomeBoundingError but dropped "
                "the UnicodeDecodeError, and with it the byte offset")
            assert "UTF-8" in str(ei.value), (
                "the message should say what the violated invariant IS")
    finally:
        _restore(saved)


def test_no_bare_label_decode_remains_in_genome_py():
    """The five sites, kept normalised.

    ``_decode_label`` is only load-bearing while it is the ONLY place strand
    bytes become a label. A new bare ``.decode("utf-8")`` on a NUL-split slice
    reopens the split silently — it would pass every assertion above, because
    those exercise the CHROM path and the reopened site would be some other one.
    """
    src = Path(G.__file__).read_text(encoding="utf-8").splitlines()
    # The one legitimate decode lives INSIDE _decode_label; excise that function
    # by line range rather than by counting, so the check says what it means.
    # (A whole-file substring count fails on _decode_label's own docstring, which
    # quotes the pattern — the same comments-are-exempt trap this rc hit twice
    # already, in the Makefile stub check and the enable_testing check.)
    start = next(i for i, ln in enumerate(src) if ln.startswith("def _decode_label"))
    end = next(i for i in range(start + 1, len(src))
               if src[i].startswith("def ") or src[i].startswith("class "))
    outside = src[:start] + src[end:]
    bare = [ln.strip() for ln in outside
            if 'split(b"\\x00", 1)[0].decode("utf-8")' in ln
            or 'label_bytes.decode("utf-8")' in ln]
    assert not bare, (
        f"{len(bare)} bare label decode(s) in genome.py outside _decode_label: "
        f"{bare}. Route strand bytes through _decode_label so the violation is "
        f"named as a GenomeBoundingError in the scripting projection too")


def test_gene_cap_labels_are_covered_too():
    """Not just CHROM caps.

    The body scan only decodes CHROM-boundary caps, so a ``0xFF`` in a GENE
    label slips past that site entirely and surfaces at ``_unpack_cap`` instead —
    a different decode site, reached by a different read. Both are routed through
    ``_decode_label``, and the C's single ``genome_decode_label`` covers both cap
    kinds; this asserts the gene half rather than assuming it.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save(tmp)
        b = bytearray((d / "turns.bin").read_bytes())
        # Walk leaf-wide blocks from the head. The strand is NOT uniformly
        # leaf_dim-aligned — PACKED_TURN blocks are narrower — so a naive stride
        # walks off the rails after the first one. The first gene cap sits before
        # any packed turn, so walking only while blocks stay leaf-wide reaches it
        # and stops honestly rather than guessing.
        #
        # Any of _GENE_MARKERS, not GENE_CAP_MARKER: a GATED gene (which this
        # fixture builds, and which gene_express_plan needs) is written with
        # REGULATORY_GENE_MARKER, so scanning for 71 alone finds nothing and the
        # test would pass by never asking its question.
        leaf_dim = G.genome_catalog(str(d))["leaf_dim"]   # from the genome, not a constant
        off = None
        p = 0
        while p + leaf_dim <= len(b):
            k = b[p]
            if k in G._GENE_MARKERS:
                off = p
                break
            if not (k in G._LEAF_WIDE_BLOCK_MARKERS or k <= 3):
                break
            p += leaf_dim
        assert off is not None, "fixture: no gene cap in the strand head"
        b[off + 2] = _BAD
        (d / "turns.bin").write_bytes(bytes(b))
        (d / "manifest.json").unlink()

        for projection in ("compiled", "scripting"):
            saved = _pure() if projection == "scripting" else {}
            try:
                exc = _raises(lambda: G.genome_genes(str(d), "geography",
                                                     coupling=one))
                assert exc is G.GenomeBoundingError, (
                    f"{projection}: genome_genes raises {exc} on a gene label "
                    f"that is not UTF-8; §44 grammar applies to every cap kind")
            finally:
                _restore(saved)
