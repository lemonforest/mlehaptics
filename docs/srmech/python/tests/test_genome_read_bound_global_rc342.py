"""rc342 (#T969) — EVERY genome read bounds against the committed ``body_sha256``.

WHAT WAS WRONG
==============
rc337 bound exactly ONE read entry point, ``srmech_genome_catalog``, by inlining
the derive-vs-committed comparison into it. That made the bound **positional**:
whether a read rejected a body modified out of band was a fact about plumbing —
about which surfaces happened to route through the catalog — rather than about
policy. Measured on rc341 with a SINGLE byte changed inside a chromosome label
(the structural walk left entirely valid):

===========================  ==================  ==================
native entry point           flip in FIRST chrom flip in LAST chrom
===========================  ==================  ==================
``genome_catalog_c``         raised              raised
``genome_census_c``          **OK**              **OK**
``genome_registry_c``        **OK**              **OK**
``genome_load_c``            **OK**              **OK**
``genome_window_c``          raised              **OK**
``genome_export_c``          raised              **OK**
``genome_explode_c``         **OK**              **OK**
``genome_genome_genes_c``    declined            **OK**
===========================  ==================  ==================

Two things in that table matter more than the raw count of gaps.

**``window`` / ``export`` were bound by ACCIDENT, not by policy.** They reject a
first-chromosome flip because they re-hash that one region's cap against
``cap_sha256`` — a PER-REGION check. Move the flipped byte to the LAST chromosome
and they accept it. A test that only ever corrupts the first chromosome reads as
proving a whole-body bound while proving a per-region one, so both vectors are
pinned here.

**``gene_express_plan`` was the sharpest case.** It is the one read that does NOT
pass through ``_catalog_data`` before dispatching to native, so the scripting
layer's bound never reached the compiled path. Through the PUBLIC Python surface,
in the native projection, on a corrupt store, it returned::

    [('g\\x02ography', 0, 162), ('history', 162, 162)]

A mangled label with a success status — the exact symptom rc337 was written to
remove, on a surface rc337's own test file never enumerated.

And the surface where the gap MATTERED most is ``genome_census``: it is the cheap
inventory read, so a caller who censuses and never windows was told the object was
fine and never learned otherwise, while a caller who censused first and windowed
later got a green light followed by a hard error.

THE CONTRACT THIS PINS
======================
**Every READ bounds.** ``catalog`` / ``census`` / ``registry`` / ``load`` /
``window`` / ``genes`` / ``genes_expressed`` / ``gene_express_plan`` / ``export``
/ ``explode`` / ``section_counts``, in BOTH projections, raising the SAME type.

**Mutations are unbound at the C entry point BY DECLARATION** and bound one layer
up, in the scripting projection, which reads the catalog before dispatching. rc337
measured why the C-level bound cannot go there: a mutation obtains the manifest
MID-EDIT, so the comparison polices a TRANSIENT window, and binding the shared
derive turned Windows CI red with 22 mutation-path failures on stores an
instrumented probe proved byte-identical to a green Linux one. The public
behaviour IS asserted here; the declaration lives in ``srmech.h``.

**Two cases stay unbound because nothing exists to bind against**, and are
asserted to still SUCCEED so that a later "just always compare" cannot pass:

* a manifest-LESS genome — §44 makes the strand its own SSoT, so the bytes on disk
  are by definition the truth;
* a v≤11 FULL manifest — its ``body_sha256`` may be a plain whole-body digest
  rather than the v4+ region CHAIN a body scan re-derives, so an unconditional
  compare would hard-fail every legacy store.

HOW THIS SUITE AVOIDS BEING SATISFIED BY A BROKEN IMPLEMENTATION
================================================================
"Does it raise?" is the cheapest possible assertion to make green — reject
everything and the whole file passes. Four separate mechanisms stop that here:

1. ``test_clean_store_reads_on_every_surface`` runs the ENTIRE surface over an
   uncorrupted store and requires success. It is parametrised so a regression
   names the op rather than collapsing eleven surfaces into one line.
2. ``test_the_mangled_label_never_reaches_a_caller`` pins the ABSENCE of the
   corrupt value, not just the presence of an exception. An implementation that
   returned the ORIGINAL label from a cached head — papering over a corrupt body
   instead of reporting it — would pass the raise assertions and fail this one.
3. ``test_structurally_invalid_byte_was_already_rejected`` is the control vector.
   ``0x43 ^ 0x01 == 0x42`` is not a kind byte the walk recognises, so it was
   rejected long before rc342 on every surface. If the new bound were credited
   with THAT rejection, the suite would be measuring the walk, not the bound.
4. The manifest-less and v≤11 cases above assert SUCCESS on a corrupt body.

VECTORS
=======
* **A / A_last** — a label byte (``byte_offset+2``, ``(b+1)%4``) in the FIRST and
  in the LAST chromosome. The walk is untouched: kind byte, block widths and
  region tiling all stay valid; only a label payload byte moves. A_last is the
  vector that separates a whole-body bound from a per-region cap check.
* **B** — the last byte of the body (``^= 0x01``): no cap, no label, no marker.
  The part a structure-shaped check has no reason to look at.
* **D** — the CONTROL. ``byte_offset ^ 0x01``, an unrecognised kind byte, already
  rejected pre-rc342 and required to behave identically after.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import pytest

from srmech import _native
from srmech.biology import genome as G
from srmech.math import hdc
from srmech.biology import plasmid as P
from srmech.biology.genome import GenomeBoundingError

_DIM = 64

#: ``SRMECH_ERR_BAD_INPUT`` — the status that IS the ``GenomeBoundingError``
#: analogue (``_raise_native_genome`` maps every non-OK status to that type).
_BAD_INPUT = 2

#: An activator bit. The gene-expression surfaces need a genome whose chromosomes
#: carry inline GATE caps, or they raise ``ValueError`` on a CLEAN store and the
#: bound question becomes unaskable — a fixture that hides the finding.
_GATE = 0b10


def _one():
    return hdc.klein4_expand(_DIM, 0)


def _leaves(n):
    return [G._HV.from_sequence([(i * 7 + j) % 4 for j in range(_DIM)], sectors=4)
            for i in range(n)]


def _save_gated(root, name="g"):
    """A two-chromosome, gene-bearing, GATED store — the one fixture the whole
    read surface can be asked over.

    Two chromosomes is the minimum that makes the FIRST-vs-LAST distinction
    expressible at all. Inline gene caps make ``genome_genes`` non-degenerate (it
    raises a plain ``ValueError`` on a single-kernel chromosome). Gate masks make
    ``gene_express_plan`` / ``genome_genes_expressed`` non-degenerate.
    """
    d = Path(root) / name
    one = _one()
    G.genome_save(G.genome(coupling=one, chromosomes=[
        ("geography", [("rules", _leaves(2), _GATE), ("board", _leaves(2), _GATE)]),
        ("history", [("dates", _leaves(2), _GATE)]),
    ]), str(d), one)
    return d, one


def _corrupt(d, vector):
    """Apply `vector` to ``<d>/turns.bin`` in place.

    Offsets come from the genome's OWN catalog rather than from constants, so a
    vector keeps meaning the same thing ("the last chromosome's label byte") if the
    on-disk layout ever shifts.
    """
    cat = G.genome_catalog(str(d))
    first = cat["chromosomes"][0]["byte_offset"]
    last = cat["chromosomes"][-1]["byte_offset"]
    assert first != last, "fixture: need >= 2 chromosomes for the first/last split"
    b = bytearray((d / "turns.bin").read_bytes())
    if vector == "A":                            # label byte, FIRST chromosome
        b[first + 2] = (b[first + 2] + 1) % 4
    elif vector == "A_last":                     # label byte, LAST chromosome
        b[last + 2] = (b[last + 2] + 1) % 4
    elif vector == "B":                          # tail payload byte
        b[len(b) - 1] ^= 0x01
    elif vector == "D":                          # control: unrecognised kind byte
        b[first] ^= 0x01
        assert b[first] == 0x42, "vector D must land on a kind byte the walk REJECTS"
    else:                                        # pragma: no cover - typo guard
        raise AssertionError(f"unknown vector {vector!r}")
    (d / "turns.bin").write_bytes(bytes(b))


#: Every vector that leaves the structural walk VALID — i.e. every vector only a
#: committed-digest comparison can catch. D is excluded on purpose (it is the
#: control, asserted separately).
_LIVE_VECTORS = ("A", "A_last", "B")


def _requires_native():
    if not (_native.HAS_NATIVE and _native.has_native_genome()):
        pytest.skip("native genome ops not loaded — nothing to compare against")


def _call(fn):
    """``("ok", value)`` or ``("raised", ExceptionType)`` — the TYPE, never the
    message. A message assertion would pin prose the two projections have no reason
    to share; the type is the contract."""
    try:
        return ("ok", fn())
    except Exception as exc:                     # noqa: BLE001 — the type IS the assertion
        return ("raised", type(exc))


# ── the public READ surface ──────────────────────────────────────────────────

def _public_reads(d, one, tmp):
    return {
        "catalog": lambda: G.genome_catalog(str(d)),
        "census": lambda: G.genome_census(str(d)),
        "registry": lambda: G.genome_registry(str(d.parent)),
        "load": lambda: G.genome_load(str(d)),
        "window": lambda: G.genome_window(str(d), "geography"),
        "genes": lambda: G.genome_genes(str(d), "geography"),
        "genes_expressed": lambda: G.genome_genes_expressed(str(d), one, _GATE),
        "gene_express_plan": lambda: G.gene_express_plan(str(d), one, _GATE),
        "export": lambda: G.genome_export(str(d), "geography",
                                          str(Path(tmp) / "out.chr")),
        "explode": lambda: G.genome_explode(str(d), str(Path(tmp) / "ex")),
    }


#: ``section_counts`` is absent from this map on purpose: it reads a §89 PLASMID
#: SECTION store (built by ``plasmid_extract``, with a VOCAB karyotype chromosome),
#: not an arbitrary gene-bearing genome, and raises on the shared fixture for that
#: reason rather than for an integrity reason. It gets its own fixture + its own
#: pair of tests below — dropping it would leave a read this rc bound untested.
READ_SURFACE = ("catalog", "census", "registry", "load", "window", "genes",
                "genes_expressed", "gene_express_plan", "export", "explode")

#: The MUTATIONS. Their C entry points are unbound BY DECLARATION (see srmech.h);
#: the scripting projection reads the catalog before dispatching, so the PUBLIC
#: surface is bound and that is what is asserted.
def _public_mutations(d, one, tmp):
    return {
        "append": lambda: G.genome_append(str(d), "extra", _leaves(2), one),
        "remove": lambda: G.genome_remove(str(d), "history", coupling=one),
        "replace": lambda: G.genome_replace(str(d), "history", _leaves(2), one),
    }


MUTATION_SURFACE = ("append", "remove", "replace")


def _both_projections(build, make_fn):
    """``(native, pure)`` over a store built FRESH for each projection.

    Freshness is required, not tidy: the mutation ops edit the store, so running
    the compiled projection first and the scripting one over the SAME directory
    would hand the second call a genome the first already changed — and the test
    would read that as a projection split. Several reads also WRITE (``export`` /
    ``explode`` emit files), so isolating the output dirs matters too.

    The pure side forces ``has_native_genome`` off — plus the census / registry
    gates, which consult their own symbols — which is the real path a no-native
    host executes rather than a mock of one.
    """
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "ex").mkdir(exist_ok=True)
        d, one = build(tmp)
        native = _call(make_fn(d, one, tmp))
    saved = (_native.has_native_genome, _native.has_native_genome_census,
             _native.has_native_genome_registry)
    _native.has_native_genome = lambda: False
    _native.has_native_genome_census = lambda: False
    _native.has_native_genome_registry = lambda: False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "ex").mkdir(exist_ok=True)
            d, one = build(tmp)
            pure = _call(make_fn(d, one, tmp))
    finally:
        (_native.has_native_genome, _native.has_native_genome_census,
         _native.has_native_genome_registry) = saved
    return native, pure


def _corrupt_build(vector):
    def build(tmp):
        d, one = _save_gated(tmp)
        _corrupt(d, vector)
        return d, one
    return build


# ── THE RATCHET: every read, every live vector, both projections ─────────────

@pytest.mark.parametrize("op", READ_SURFACE)
@pytest.mark.parametrize("vector", _LIVE_VECTORS)
def test_every_read_rejects_a_corrupt_body_in_both_projections(op, vector):
    """The contract, asserted as a matrix rather than as a sentence.

    Parametrised on BOTH axes so a failure names the (surface, vector) pair. That
    is what makes the report diagnostic: "window fails on A_last but passes on A"
    is the signature of a per-region cap check masquerading as a whole-body bound,
    and it is precisely the state rc341 was in.

    The type equality is a third assertion beyond "native raised" and "pure
    raised". Without it the two projections could drift apart on the exception
    type — a ``UnicodeDecodeError`` on one side and a ``GenomeBoundingError`` on
    the other is what a downstream decode failure looks like when the integrity
    check is missing, which is the failure this rc replaces with a bound at source.
    """
    native, pure = _both_projections(
        _corrupt_build(vector), lambda d, one, tmp: _public_reads(d, one, tmp)[op])
    assert native[0] == "raised", (
        f"{op} / vector {vector}: the COMPILED projection returned "
        f"{native[1]!r} for a body modified out of band. A read that answers for "
        f"an object whose integrity has already failed elsewhere is the rc342 "
        f"defect.")
    assert pure[0] == "raised", (
        f"{op} / vector {vector}: the SCRIPTING projection returned {pure[1]!r}")
    assert native[1] is pure[1] is GenomeBoundingError, (
        f"{op} / vector {vector}: both projections must raise the SAME type — the "
        f"family's GenomeBoundingError; got native={native[1]!r} pure={pure[1]!r}")


@pytest.mark.parametrize("op", MUTATION_SURFACE)
def test_every_mutation_rejects_a_corrupt_body_at_the_public_surface(op):
    """The mutations, whose C entry points are unbound BY DECLARATION.

    They are bound one layer up: the scripting projection reads the catalog before
    dispatching. That is a weaker guarantee than the reads have — a bare-C host
    calling ``srmech_genome_remove`` directly is NOT bound — and ``srmech.h`` says
    so per-function. What is asserted here is the guarantee that DOES hold, so
    that losing it is a test failure rather than a silent regression.
    """
    native, pure = _both_projections(
        _corrupt_build("A"), lambda d, one, tmp: _public_mutations(d, one, tmp)[op])
    assert native == ("raised", GenomeBoundingError), f"{op}: compiled gave {native!r}"
    assert pure == ("raised", GenomeBoundingError), f"{op}: scripting gave {pure!r}"


# ── the NATIVE entry points, at the status level ──────────────────────────────

def _native_read_entries(d, tmp):
    """The native read entry points reachable through ctypes, as raw calls.

    THREE native reads are deliberately ABSENT — ``genome_genome_genes_c``,
    ``genome_genes_expressed_c`` and ``genome_section_counts_c``. Their ctypes
    wrappers map EVERY non-OK status to a DECLINE (``None``) so the caller runs the
    pure body, which means an integrity rejection is indistinguishable there from a
    capability decline, and asserting a raise would assert the wrapper's routing
    rather than the bound. Their C entry points DO return ``SRMECH_ERR_BAD_INPUT``;
    ``c/test/test_srmech_genome.c`` asserts it on a host with no Python, which is
    the only place it is observable. The public surfaces are still bound — the pure
    body raises from ``_catalog_data`` — and that IS asserted, above.

    ``genome_gene_express_plan_c`` is present because it does NOT decline: it
    raises, so its status is readable here. It is also the entry point behind the
    sharpest instance of the rc341 defect.
    """
    body = (d / "turns.bin").stat().st_size
    return {
        "genome_catalog_c": lambda: _native.genome_catalog_c(str(d), b""),
        "genome_census_c": lambda: _native.genome_census_c(str(d), b""),
        "genome_registry_c": lambda: _native.genome_registry_c(str(d.parent), b""),
        "genome_load_c": lambda: _native.genome_load_c(str(d), b"", 1 << 20),
        "genome_window_c": lambda: _native.genome_window_c(
            str(d), "geography", b"", body),
        "genome_export_c": lambda: _native.genome_export_c(
            str(d), "geography", str(Path(tmp) / "n.chr"), b""),
        "genome_explode_c": lambda: _native.genome_explode_c(
            str(d), str(Path(tmp) / "nex"), b""),
        "genome_gene_express_plan_c": lambda: _native.genome_gene_express_plan_c(
            str(d), _GATE, b""),
    }


NATIVE_READ_ENTRIES = ("genome_catalog_c", "genome_census_c", "genome_registry_c",
                       "genome_load_c", "genome_window_c", "genome_export_c",
                       "genome_explode_c", "genome_gene_express_plan_c")


@pytest.mark.parametrize("entry", NATIVE_READ_ENTRIES)
@pytest.mark.parametrize("vector", _LIVE_VECTORS)
def test_every_native_read_entry_point_returns_bad_input(entry, vector):
    """The bound asserted where a bare-C host meets it — at the status, not at the
    Python exception.

    This is the layer that actually moved. Several public surfaces were already
    bound through ``_catalog_data`` in the scripting layer, which means the public
    matrix above can be green while the compiled projection is permissive. That is
    exactly how rc337 shipped ``genome_load`` "bound" while
    ``srmech_genome_load`` returned the corrupt bytes with a success status.
    """
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        d, _one_ = _save_gated(tmp)
        (Path(tmp) / "nex").mkdir(exist_ok=True)
        _corrupt(d, vector)
        got = _call(_native_read_entries(d, tmp)[entry])
        assert got[0] == "raised", (
            f"{entry} / vector {vector}: returned {got[1]!r} with a success status "
            f"for a body modified out of band")
        assert got[1] is _native.NativeGenomeError, (
            f"{entry} / vector {vector}: raised {got[1]!r}, not NativeGenomeError")
        with pytest.raises(_native.NativeGenomeError) as ei:
            _native_read_entries(d, tmp)[entry]()
        assert ei.value.status == _BAD_INPUT, (
            f"{entry} / vector {vector}: status {ei.value.status}, expected "
            f"SRMECH_ERR_BAD_INPUT ({_BAD_INPUT}) — a different status here is an "
            f"ABI question, not a detail")


# ── the symptom, pinned by ABSENCE ───────────────────────────────────────────

def test_the_mangled_label_never_reaches_a_caller():
    """Pin the ABSENCE of the corrupt value, not only the presence of a raise.

    These are different assertions. An implementation that returned the ORIGINAL
    label from a cached head — silently papering over a corrupt body rather than
    reporting it — would satisfy every raise assertion above and fail this one.

    Both measured pre-rc342 values are named: ``genome_catalog`` returned
    ``'g\\x02ography'`` before rc337 fixed it, and ``gene_express_plan`` was STILL
    returning it at rc341 through the public Python surface.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save_gated(tmp)
        clean = [c["label"] for c in G.genome_catalog(str(d))["chromosomes"]]
        assert clean == ["geography", "history"], "fixture precondition"
        _corrupt(d, "A")
        for name, fn in (("catalog", lambda: G.genome_catalog(str(d))),
                         ("census", lambda: G.genome_census(str(d))),
                         ("gene_express_plan",
                          lambda: G.gene_express_plan(str(d), one, _GATE))):
            got = _call(fn)
            assert got == ("raised", GenomeBoundingError), (
                f"{name}: expected GenomeBoundingError, got {got!r}")
            if got[0] == "ok":               # defensive: name the symptom exactly
                assert "g\x02ography" not in repr(got[1]), (
                    f"{name} returned the MANGLED label with a success status")


def test_a_region_merge_never_reports_a_short_census():
    """The vector no per-region check can see, through the census.

    Setting the second chromosome's CHROM-cap marker to ``0x00`` does not break the
    walk — ``genome_block_len`` accepts ``kind <= 3`` as a legacy v2 turn — so the
    block is absorbed into chromosome 1's region and the derived tree comes back
    with ONE chromosome instead of two. Every digest in that tree is internally
    consistent; it is simply a tree of the wrong genome. Only a comparison against
    a value committed BEFORE the corruption can catch it.

    Measured pre-rc342: ``genome_census`` reported ``n_chromosomes 1`` with a
    success status in the native projection.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save_gated(tmp)
        off1 = G.genome_catalog(str(d))["chromosomes"][1]["byte_offset"]
        b = bytearray((d / "turns.bin").read_bytes())
        assert b[off1] == 0x43, f"fixture: expected a CHROM cap at {off1}"
        b[off1] = (b[off1] + 1) % 4
        assert b[off1] == 0x00, "the merge vector must land on a kind the walk ACCEPTS"
        (d / "turns.bin").write_bytes(bytes(b))
        got = _call(lambda: G.genome_census(str(d)))
        assert got == ("raised", GenomeBoundingError), (
            f"a merged region must raise, not report a short genome; got {got!r}")
        if got[0] == "ok":
            assert got[1].get("n_chromosomes") != 1


# ── the four non-degeneracy controls ─────────────────────────────────────────

@pytest.mark.parametrize("op", READ_SURFACE + MUTATION_SURFACE)
def test_clean_store_reads_on_every_surface(op):
    """CONTROL 1 — without this, every assertion above is satisfied by an
    implementation that rejects everything, which is the cheapest way to make a
    "does it raise?" suite green.

    It is also the assertion that would have caught the first cut of rc337:
    binding inside the shared derive made the mutation ops reject CLEAN stores on
    Windows.
    """
    def ops(d, one, tmp):
        both = _public_reads(d, one, tmp)
        both.update(_public_mutations(d, one, tmp))
        return both[op]
    native, pure = _both_projections(_save_gated, ops)
    assert native[0] == "ok", f"{op}: a CLEAN store must read; compiled gave {native!r}"
    assert pure[0] == "ok", f"{op}: a CLEAN store must read; scripting gave {pure!r}"


@pytest.mark.parametrize("entry", NATIVE_READ_ENTRIES)
def test_clean_store_reads_on_every_native_entry_point(entry):
    """CONTROL 1b — the same non-degeneracy at the status layer."""
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        d, _one_ = _save_gated(tmp)
        (Path(tmp) / "nex").mkdir(exist_ok=True)
        got = _call(_native_read_entries(d, tmp)[entry])
    assert got[0] == "ok", f"{entry}: a CLEAN store must read; got {got!r}"


@pytest.mark.parametrize("entry", NATIVE_READ_ENTRIES)
def test_structurally_invalid_byte_was_already_rejected(entry):
    """CONTROL 2 — the control vector, which keeps the bound from being credited
    with a rejection the structural walk was already making.

    ``0x43 ^ 0x01 == 0x42`` is not a kind byte ``genome_block_len`` recognises, so
    every surface rejected it long before rc342. It must still be rejected, and
    still with ``SRMECH_ERR_BAD_INPUT``: if this vector's status had changed, the
    "new bound" would in fact be a rewrite of the walk's error contract rather
    than an addition to it.
    """
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        d, _one_ = _save_gated(tmp)
        (Path(tmp) / "nex").mkdir(exist_ok=True)
        _corrupt(d, "D")
        with pytest.raises(_native.NativeGenomeError) as ei:
            _native_read_entries(d, tmp)[entry]()
        assert ei.value.status == _BAD_INPUT


@pytest.mark.parametrize("op", ("catalog", "census", "registry"))
def test_a_manifestless_genome_with_a_corrupt_body_still_reads(op):
    """CONTROL 3 — §44's optional-``.fai``-cache contract, which the bound must NOT
    have broken.

    With no ``manifest.json`` there is no committed value IN EXISTENCE, so there is
    nothing to bind against and the strand is by definition its own SSoT. Both
    projections must return the SAME answer — the one the corrupt bytes describe,
    mangled label and all — because that is what the file says.

    This is the case an unconditional ``memcmp`` breaks, and the reason the
    empty-string sentinel exists rather than a bare "always compare".
    """
    def build(tmp):
        d, one = _save_gated(tmp)
        _corrupt(d, "A")
        (d / "manifest.json").unlink()
        return d, one

    def ops(d, one, tmp):
        return {"catalog": lambda: G.genome_catalog(str(d), coupling=one),
                "census": lambda: G.genome_census(str(d), coupling=one),
                "registry": lambda: G.genome_registry(str(d.parent), coupling=one),
                }[op]
    native, pure = _both_projections(build, ops)
    assert native[0] == "ok" and pure[0] == "ok", (
        f"{op}: a manifest-LESS genome has nothing to bind against and must still "
        f"read; got native={native!r} pure={pure!r}")
    # Compare CONTENT, not the tmpdir: census / registry embed the store path, and
    # the two projections are deliberately given separate fresh directories.
    assert _strip_paths(native[1]) == _strip_paths(pure[1]), (
        f"{op}: and the two projections must read it IDENTICALLY (paths aside)")


def _strip_paths(tree):
    """`tree` with every ``path`` / ``root`` field blanked, recursively.

    Those fields carry the temp directory, which differs between the two
    projections by construction (each gets its OWN fresh store, so a mutation in
    one cannot be seen by the other). Blanking them keeps the comparison about the
    genome's CONTENT, which is the thing the two projections must agree on.
    """
    if isinstance(tree, dict):
        return {k: ("" if k in ("path", "root") else _strip_paths(v))
                for k, v in tree.items()}
    if isinstance(tree, list):
        return [_strip_paths(v) for v in tree]
    return tree


# ── section_counts: the same bound, over a §89 SECTION store ─────────────────

def _save_sections(root, n_sections=3):
    """A §89 plasmid SECTION store — the shape ``plasmid.section_counts`` reads.

    Its per-section node_ids tables are what the scan pages, and it carries a VOCAB
    karyotype chromosome the scan skips; a plain gene-bearing genome is not a legal
    input to that op at all.
    """
    one = _one()
    docs = [[f"w{(s * 17 + i * 5) % 40}" for i in range(12)]
            for s in range(n_sections)]
    d = Path(root) / "sections"
    d.mkdir()
    P.plasmid_extract(docs, str(d), one, window=2, k=2)
    return d, one


@pytest.mark.parametrize("vector", _LIVE_VECTORS)
def test_section_counts_rejects_a_corrupt_body_in_both_projections(vector):
    """``section_counts`` is a READ and bounds like every other one.

    It matters more than its obscurity suggests: it is the §102 corpus scan, the
    op rc280 took from ~22 hours to minutes, so it runs over the LARGEST stores in
    the system — exactly where a silent read of corrupt bytes does the most damage
    and is least likely to be noticed.

    It is also the surface that dictated HOW the bound is plumbed. Reaching the
    committed digest via a second open+parse of ``manifest.json`` — rc337's
    approach — pushed this op from 5 to 7 file opens per scan and tripped the rc282
    DOWN-ONLY open-count ratchet. The shipped bound threads the digest out of the
    parse the derive already performs, so the open count is unchanged.
    """
    native, pure = _both_projections(
        lambda tmp: (lambda dc: (_corrupt(dc[0], vector), dc)[1])(_save_sections(tmp)),
        lambda d, one, tmp: (lambda: P.section_counts(str(d), coupling=one)))
    assert native == ("raised", GenomeBoundingError), (
        f"section_counts / vector {vector}: compiled gave {native!r}")
    assert pure == ("raised", GenomeBoundingError), (
        f"section_counts / vector {vector}: scripting gave {pure!r}")


def test_section_counts_reads_a_clean_section_store():
    """CONTROL 1c — the non-degeneracy peer of the test above."""
    native, pure = _both_projections(
        _save_sections, lambda d, one, tmp: (lambda: P.section_counts(str(d),
                                                                     coupling=one)))
    assert native[0] == "ok", f"a CLEAN section store must read; compiled {native!r}"
    assert pure[0] == "ok", f"a CLEAN section store must read; scripting {pure!r}"
    assert native[1] == pure[1], "and both projections must count identically"
    assert native[1], "fixture is degenerate — no counts at all"


def test_a_manifestless_append_still_succeeds():
    """CONTROL 4 — the regression the first cut of rc337 actually shipped.

    ``genome_append`` on a manifest-LESS store migrates through the shared derive,
    which bound-checks the old body against the DERIVED tree. rc337's first cut
    restructured that function and this call began returning
    ``SRMECH_ERR_BAD_INPUT`` on a perfectly clean store. rc342 routes the read
    entry points through a WRAPPER and leaves the shared derive's own behaviour
    alone; this test says so out loud and fails loudly if a later refactor reaches
    back into it.
    """
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save_gated(tmp)
        (d / "manifest.json").unlink()
        data = G.genome_append(str(d), "extra", _leaves(2), one)
    assert [c["label"] for c in data["chromosomes"]] == [
        "geography", "history", "extra"]


# ── a rejected edit must not damage the store ────────────────────────────────

@pytest.mark.parametrize("op", ("remove", "replace"))
def test_a_rejected_edit_leaves_the_store_byte_identical(op):
    """The bound fires BEFORE any write, not partway through one.

    ``genome_remove`` / ``genome_replace`` splice ``turns.bin`` in place. If the
    check sat after the splice began — or if a caller retried past it — a corrupt
    store would become a corrupt-AND-truncated store, turning a detectable fault
    into an unrecoverable one. Both files are hashed, so a manifest rewrite counts
    as damage too.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save_gated(tmp)
        _corrupt(d, "A")
        before_body = hashlib.sha256((d / "turns.bin").read_bytes()).hexdigest()
        before_man = hashlib.sha256((d / "manifest.json").read_bytes()).hexdigest()
        fn = (lambda: G.genome_remove(str(d), "history", coupling=one)) if op == "remove" \
            else (lambda: G.genome_replace(str(d), "history", _leaves(2), one))
        with pytest.raises(GenomeBoundingError):
            fn()
        assert hashlib.sha256((d / "turns.bin").read_bytes()).hexdigest() == before_body, (
            f"genome_{op} raised but MUTATED turns.bin")
        assert hashlib.sha256((d / "manifest.json").read_bytes()).hexdigest() == before_man, (
            f"genome_{op} raised but MUTATED manifest.json")


# ── the SIBLING crack, measured and left as an executable spec ───────────────

#: #T954 — same surface, same question ("what does a read do when the object is
#: bad?"), DIFFERENT vector, and rc342 does NOT close it. Kept as an xfail rather
#: than a prose TODO for the reason rc337's xfails just proved out: nobody has to
#: remember it exists, and it XPASSes into the report the moment the behaviour
#: moves. Non-strict so a host whose behaviour moves first does not turn CI red.
_PENDING_T954 = pytest.mark.xfail(
    reason="#T954: with a NON-UTF-8 label byte the pure projection raises "
           "UnicodeDecodeError where native raises GenomeBoundingError. Not "
           "closable without also fixing the manifest-LESS native boundary — see "
           "the measurement in the test body.",
)


def _corrupt_label_not_utf8(d):
    """Set a label byte to ``0xFF`` — the #T954 vector.

    rc342's vectors all keep the label DECODABLE (``(b+1)%4`` lands in 0..3, which
    are control characters but perfectly valid UTF-8), so they exercise the
    integrity bound without ever touching the decode path. ``0xFF`` is not valid
    UTF-8 in any position, which is what makes this a different question.
    """
    off = G.genome_catalog(str(d))["chromosomes"][0]["byte_offset"]
    b = bytearray((d / "turns.bin").read_bytes())
    b[off + 2] = 0xFF
    (d / "turns.bin").write_bytes(bytes(b))


@_PENDING_T954
def test_a_non_utf8_label_raises_the_same_type_in_both_projections():
    """#T954, measured at rc342 so the follow-up starts from data.

    ==========================  ======================  ====================
    store                       compiled                scripting
    ==========================  ======================  ====================
    manifest PRESENT            ``GenomeBoundingError`` ``UnicodeDecodeError``
    manifest ABSENT             ``UnicodeDecodeError``  ``UnicodeDecodeError``
    ==========================  ======================  ====================

    WHY THE SPLIT IS IN THE TOP ROW ONLY. With a manifest present, the compiled
    projection's integrity bound fires in C before any label is decoded, so the
    corrupt body is reported as what it is. The scripting projection derives the
    catalog by SCANNING the body first — which decodes labels — and only then
    compares ``body_sha256``, so the decode blows up before the bound is reached.
    Same defect shape as rc294's registry ``OSError``: both projections agree it is
    an error and disagree about what KIND.

    WHY rc342 DOES NOT FIX IT, stated plainly rather than deferred vaguely. The
    obvious fix — raise ``GenomeBoundingError`` from the pure decode site, chained
    from the ``UnicodeDecodeError`` so the diagnostic detail survives, exactly as
    rc294 chained its ``OSError`` — closes the top row and OPENS THE BOTTOM ONE.
    With no manifest there is nothing to bind against (§44), both projections
    currently raise ``UnicodeDecodeError``, and they AGREE; changing only the pure
    side makes them disagree. Closing the bottom row too means deciding what an
    undecodable label means on a genome that is its own SSoT, and fixing the ctypes
    boundary where the compiled projection's JSON output is decoded — which is a
    different layer from anything rc342 touched. So it is a real second piece of
    work, not a loose end of this one.

    What rc342 DOES guarantee here is the thing that would have made #T954 worse:
    no THIRD error shape was introduced. Every rejection this rc adds is
    ``GenomeBoundingError`` / ``SRMECH_ERR_BAD_INPUT``, both already in the family.
    """
    native, pure = _both_projections(
        lambda tmp: (lambda dc: (_corrupt_label_not_utf8(dc[0]), dc)[1])(
            _save_gated(tmp)),
        lambda d, one, tmp: (lambda: G.genome_catalog(str(d))))
    assert native[0] == "raised" and pure[0] == "raised", (native, pure)
    assert native[1] is pure[1], (
        f"#T954: the two projections must raise the SAME type for an undecodable "
        f"label; got native={native[1]!r} pure={pure[1]!r}")


def test_the_non_utf8_vector_is_at_least_rejected_by_both_projections():
    """The part of #T954 that DOES hold today, pinned so it cannot silently rot.

    The projections disagree about the exception TYPE, which is the defect. They do
    NOT disagree about whether this is an error — neither returns a mangled label
    with a success status, which is the failure class rc342 exists to remove. That
    distinction is worth an assertion of its own: if a future change made either
    side ACCEPT a non-UTF-8 label, the xfail above would keep passing (it only
    compares types) while a genuinely worse regression shipped.
    """
    native, pure = _both_projections(
        lambda tmp: (lambda dc: (_corrupt_label_not_utf8(dc[0]), dc)[1])(
            _save_gated(tmp)),
        lambda d, one, tmp: (lambda: G.genome_catalog(str(d))))
    assert native[0] == "raised", f"compiled ACCEPTED a non-UTF-8 label: {native!r}"
    assert pure[0] == "raised", f"scripting ACCEPTED a non-UTF-8 label: {pure!r}"


# ── the ABI statement, made executable ───────────────────────────────────────

def test_rc342_introduces_no_new_status_enumerator_and_does_not_move_the_abi():
    """rc342 adds no exported symbol, changes no exported signature, removes
    nothing, and adds no callback typedef — every function it introduced or
    re-shaped is ``static``. The rejection reuses ``SRMECH_ERR_BAD_INPUT``, already
    in every touched export's documented error set. So ``SRMECH_ABI_VERSION`` did not move at
    rc342 (rc395 later moved it 10 -> 11 by removing srmech_cd_zero_divisor_witness).

    If a later change routes this bound through a NEW status, this fails and the
    ABI question has to be answered deliberately rather than by omission.
    """
    _requires_native()
    assert _native.EXPECTED_ABI_VERSION == 23, (
        "rc342 is ABI-neutral (rc404 moved the baseline 11 -> 12); a bump here needs its own justification")
    assert _native.NATIVE_ABI_VERSION == _native.EXPECTED_ABI_VERSION, (
        "the loaded library's ABI does not match the one this shim compiled "
        "against — a stale .so, which would make every assertion above a "
        "measurement of the WRONG artifact")
    with tempfile.TemporaryDirectory() as tmp:
        d, _one_ = _save_gated(tmp)
        _corrupt(d, "A_last")
        with pytest.raises(_native.NativeGenomeError) as ei:
            _native.genome_census_c(str(d), b"")
        assert ei.value.status == _BAD_INPUT
