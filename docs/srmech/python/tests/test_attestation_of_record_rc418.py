"""The ATTESTATION OF RECORD (rc418, `#T1108`).

srmech had no concept of *the attestation of record*. The write half
**synthesised where it had to preserve** — nine mutating ops re-minted srmech's
default block, so a genome saved under a real DOI and a real licence came back
``CC0`` / ``10.0/srmech.genome.persistence`` after one ``genome_append``. The
read half **read raw where it had to synthesise** — ``attestation_audit``
bypassed the adapter dispatch, so eight of nine registered sources reported an
entirely empty attestation for every row.

**Both defects were invisible to every differential test in the tree**, and the
reason is the same in each case and is the reason this file is written the way
it is: *the two projections agreed, byte for byte, on the wrong answer*. A
co-equal dual construction certifies MUTUAL REALIZABILITY, not correctness. So
no clause below compares C to Python and stops there. Every clause names an
external truth — a value that was PUT IN, or an answer another op already
gives — and asserts the op returns THAT.

The second discipline the file follows is ADR-0012 §6.1, taken from the shipped
template ``test_composes_grain_rc412.py``: **a strict-zero sweep over a
shrinking set is vacuously true.** Each section therefore carries the four
guards that template established —

  * an EMPTY-ROSTER guard (``:244`` there) — a roster that emptied itself would
    make every clause over it pass;
  * an explicit ``⚠️ NEGATIVE CONTROL`` (``:440`` there) — an instrument that
    cannot return otherwise is not a measurement;
  * a NON-VACUITY probe (``:602`` there) — the thing being read must actually
    read something;
  * a SPY on the compiled path — without it the "native vs pure" clauses
    silently become pure-vs-pure, which is exactly the hole ``§5.1`` deletes.
"""

from __future__ import annotations

import pathlib
import tempfile
from typing import Dict, List, Tuple

import pytest

from srmech import _json as _srmech_json
from srmech import _native
from srmech.amsc import catalog as _catalog
from srmech.amsc.format import MPRValidationError, read_ndjson
from srmech.biology import genome as G
from srmech.cascade.one import the_one
from srmech.math.hdc import klein4_expand, klein4_from_one
from srmech.math.search import byte_search

# ──────────────────────────────────────────────────────────────────────
# Fixtures — one distinctive non-default block, and a genome to carry it.
# ──────────────────────────────────────────────────────────────────────

#: The attestation of record under test. All four static fields differ from
#: srmech's defaults, so ANY re-mint is visible in ANY of them.
A: Dict[str, str] = {
    "source_doi": "10.9999/rc418.attestation.of.record",
    "source_url": "https://example.invalid/rc418-attestation-of-record",
    "license": "GPL-3.0-only",
    "retrieved_at": "2026-08-08T00:00:00Z",
}

#: The five fields that must be RE-SYNTHESISED on every write, never inherited.
#: ``response_sha256`` IS the body hash, so carrying it forward would freeze a
#: stale digest into an attested genome and every downstream re-verification
#: would fail against bytes that are perfectly intact — a WORSE defect than the
#: substitution this rc fixes, and the easy mistake when implementing carry.
RESYNTHESISED: Tuple[str, ...] = (
    "response_sha256",
    "parser_version",
    "parser_rule_hash",
    "collector_descriptor_path",
    "collector_descriptor_hash",
)

LEAF_DIM = 64


def _coupling():
    return klein4_from_one(the_one(1, 1, 4), LEAF_DIM)


def _leaves(n: int, base: int) -> List:
    return [klein4_expand(LEAF_DIM, base + i) for i in range(n)]


def _block(path) -> Dict[str, str]:
    """The on-disk attestation block, read through srmech's own JSON reader."""
    raw = (pathlib.Path(path) / "manifest.json").read_bytes()
    return dict(_srmech_json.loads(raw.decode("utf-8"))["attestation"])


def _chr_block(path) -> Dict[str, str]:
    raw = pathlib.Path(path).read_bytes()
    return dict(_srmech_json.loads(raw.decode("utf-8"))["attestation"])


def _offsets(hay: bytes, needle: bytes) -> List[int]:
    """Every offset of ``needle`` in ``hay`` — Class G (``byte_search`` returns
    ``None`` on a miss and takes no ``start=``, so the offset is carried by
    hand and the haystack re-sliced past each hit)."""
    out: List[int] = []
    base = 0
    while True:
        hit = byte_search(hay[base:], needle)
        if hit is None:
            return out
        out.append(base + hit)
        base += hit + 1


def _attested(tmp: pathlib.Path, name: str, *, attestation=A):
    """A fresh two-chromosome genome carrying ``attestation``."""
    path = tmp / name
    strand = G.genome({"alpha": _leaves(3, 10), "beta": _leaves(8, 40)},
                      _coupling())
    G.genome_save(strand, path, _coupling(), attestation=attestation)
    return path


def _default(tmp: pathlib.Path, name: str):
    """A fresh genome with NO attestation — the negative control's subject."""
    path = tmp / name
    strand = G.genome({"alpha": _leaves(3, 10), "beta": _leaves(8, 40)},
                      _coupling())
    G.genome_save(strand, path, _coupling())
    return path


# ──────────────────────────────────────────────────────────────────────
# §5.2  test_the_attestation_survives_the_lifecycle — the point of the rc.
#
# `tests/test_genome_attestation_rc304.py` has nineteen tests and they BUILD
# and READ only. Not one of them mutates. The verb was never exercised, which
# is exactly why nine ops could destroy the block for eleven releases with a
# green suite.
# ──────────────────────────────────────────────────────────────────────


def _mutate_append(path):
    G.genome_append(path, "gamma", _leaves(4, 90), _coupling())


def _mutate_append_kernel(path):
    G.genome_append_kernel(path, "kern", _leaves(3, 55)[0], coupling=_coupling())


def _mutate_remove(path):
    G.genome_remove(path, "alpha", coupling=_coupling())


def _mutate_replace(path):
    G.genome_replace(path, "alpha", _leaves(5, 70), _coupling())


def _mutate_resave(path):
    strand = G.genome({"alpha": _leaves(3, 10), "beta": _leaves(8, 40)},
                      _coupling())
    G.genome_save(strand, path, _coupling())


def _mutate_upgrade(path):
    G.upgrade_v15_to_v16(path, coupling=_coupling())


#: The mutating-op roster. Each entry is (name, callable). Every one of these
#: was MEASURED at rc417 to destroy a caller attestation.
MUTATORS: Tuple[Tuple[str, object], ...] = (
    ("genome_append", _mutate_append),
    ("genome_append_kernel", _mutate_append_kernel),
    ("genome_remove", _mutate_remove),
    ("genome_replace", _mutate_replace),
    ("genome_save re-save", _mutate_resave),
    ("upgrade_v15_to_v16", _mutate_upgrade),
)


def test_the_mutator_roster_is_not_empty_and_every_op_resolves() -> None:
    """EMPTY-ROSTER GUARD (template ``:244``). A roster that emptied itself
    would make :func:`test_the_attestation_survives_the_lifecycle` pass over
    nothing at all."""
    assert MUTATORS, "the mutator roster is empty — the lifecycle clause is vacuous"
    for name, _fn in MUTATORS:
        attr = name.split()[0]
        assert hasattr(G, attr), f"roster names a missing op: {attr}"
        assert callable(getattr(G, attr))


@pytest.mark.parametrize("name,mutate", MUTATORS, ids=[m[0] for m in MUTATORS])
def test_the_attestation_survives_the_lifecycle(name, mutate) -> None:
    """THE POINT OF THE RC. Build with attestation ``A``, mutate, and assert
    ``A``'s four static fields survived — **or** the op declined with the typed
    conflict error. There is no third outcome; silently writing srmech's
    default over a caller's real block is the defect."""
    with tempfile.TemporaryDirectory() as td:
        path = _attested(pathlib.Path(td), "g.genome")
        before = _block(path)
        assert before["license"] == A["license"], "fixture did not take"

        try:
            mutate(path)
        except G.GenomeAttestationConflict:
            return                                   # the declined branch is legal

        after = _block(path)
        for field, want in A.items():
            assert after.get(field) == want, (
                f"{name} did not carry {field} forward: {after.get(field)!r} "
                f"!= {want!r}. This is the rc417 substitution."
            )
        for field in RESYNTHESISED:
            assert after.get(field), f"{name} blanked {field}"
        assert after["collector_descriptor_path"] == "srmech/biology/genome.py"


def test_the_body_hash_is_resynthesised_not_inherited() -> None:
    """The easy mistake, pinned separately because it fails the OTHER way.

    An implementation that inherited the whole block — all five
    ``_ATTESTATION_SOURCE_FIELDS`` rather than the four
    ``_ATTESTATION_CARRY_FIELDS`` — would pass every clause above while
    freezing a stale body digest into an attested genome."""
    with tempfile.TemporaryDirectory() as td:
        path = _attested(pathlib.Path(td), "g.genome")
        before = _block(path)["response_sha256"]
        G.genome_append(path, "gamma", _leaves(4, 90), _coupling())
        after = _block(path)
        assert after["response_sha256"] != before, (
            "response_sha256 was CARRIED FORWARD. It IS the body hash; the body "
            "just changed. _ATTESTATION_CARRY_FIELDS is four fields, not five."
        )
        assert after["response_sha256"] == _catalog_body_sha(path)


def _catalog_body_sha(path) -> str:
    raw = (pathlib.Path(path) / "manifest.json").read_bytes()
    return str(_srmech_json.loads(raw.decode("utf-8"))["data"]["body_sha256"])


def test_the_instrument_discriminates_on_a_default_genome() -> None:
    """⚠️ NEGATIVE CONTROL (template ``:440``).

    A DEFAULT-attested genome under the same mutation must PASS — it must come
    back carrying srmech's default, with no conflict raised. Two things fail
    here and nowhere else:

    * an implementation that refused every mutation (so the clauses above
      passed only via their ``except`` branch) goes red;
    * an implementation whose conflict predicate is written over all FIVE
      ``_ATTESTATION_SOURCE_FIELDS`` instead of the static four goes red,
      because ``response_sha256`` moves on every ordinary append. Measured at
      rc417: that predicate fires on all 178 ``genome_append`` call sites in
      the tree; scoped to the four it fires on none.
    """
    with tempfile.TemporaryDirectory() as td:
        path = _default(pathlib.Path(td), "d.genome")
        G.genome_append(path, "gamma", _leaves(4, 90), _coupling())
        after = _block(path)
        assert after["source_doi"] == "10.0/srmech.genome.persistence"
        assert after["license"] == "CC0"
        raw = (pathlib.Path(path) / "manifest.json").read_bytes()
        assert _offsets(raw, b"CC0"), "Class-G: the default licence is on disk"


def test_an_explicit_override_that_conflicts_is_refused_not_applied() -> None:
    """Overwriting an attestation of record is allowed; it is never SILENT."""
    with tempfile.TemporaryDirectory() as td:
        path = _attested(pathlib.Path(td), "g.genome")
        with pytest.raises(G.GenomeAttestationConflict):
            G.genome_append(path, "gamma", _leaves(4, 90), _coupling(),
                            attestation={"license": "MIT"})
        assert _block(path)["license"] == A["license"], (
            "the refusal must leave the genome untouched"
        )
        # Re-passing the values already on disk is NOT a conflict.
        G.genome_append(path, "gamma", _leaves(4, 90), _coupling(),
                        attestation=dict(A))
        assert _block(path)["license"] == A["license"]


def test_the_exported_chromosome_carries_the_parent_attestation() -> None:
    """A ``.chr`` is the DISTRIBUTION unit — it leaves the machine. At rc417 a
    chromosome exported from a ``GPL-3.0-only`` parent shipped as ``CC0``
    under ``10.0/srmech.genome.chromosome``, which makes this the
    highest-severity single site of the substitution."""
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        path = _attested(tmp, "g.genome")
        out = tmp / "alpha.chr"
        G.genome_export(path, "alpha", out, coupling=_coupling())
        block = _chr_block(out)
        for field, want in A.items():
            assert block.get(field) == want, f".chr lost {field}"
        # response_sha256 stays srmech-owned: it IS the region digest, and BOTH
        # projections hard-check it on import.
        data = _srmech_json.loads(out.read_text(encoding="utf-8"))["data"]
        assert block["response_sha256"] == data["region"]["sha256"]
        # …and it is not caller-settable, unlike the manifest's.
        with pytest.raises(ValueError):
            G._chr_record(data, attestation={"response_sha256": "0" * 64})


def test_a_seeded_destination_inherits_from_the_bundle() -> None:
    """NOT IN THE BRIEF, found while building. ``genome_import`` into a FRESH
    dest and ``genome_pack`` into a fresh dest have no destination manifest to
    carry from — the bundle IS the genome at that moment. Reading the block
    off disk alone therefore leaves them writing ``CC0``, which is the same
    substitution one indirection further out."""
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        path = _attested(tmp, "g.genome")
        out = tmp / "alpha.chr"
        G.genome_export(path, "alpha", out, coupling=_coupling())

        dest = tmp / "imported.genome"
        G.genome_import(out, dest, coupling=_coupling())
        assert _block(dest)["license"] == A["license"], "import SEED lost it"

        loose = tmp / "loose"
        loose.mkdir()
        G.genome_explode(path, loose, coupling=_coupling())
        packed = tmp / "packed.genome"
        G.genome_pack(loose, packed, coupling=_coupling())
        assert _block(packed)["license"] == A["license"], "pack lost it"
        assert _block(packed)["source_doi"] == A["source_doi"]


def test_a_default_block_is_never_inherited_across_a_kind_boundary() -> None:
    """⚠️ REGRESSION. A genome manifest's default DOI
    (``10.0/srmech.genome.persistence``) is NOT a ``.chr``'s default
    (``10.0/srmech.genome.chromosome``), and the two KINDS meet at exactly two
    places: export (genome → bundle) and a seeded import/pack (bundle → genome).

    A default block is the ABSENCE of an attestation of record, so it must never
    cross that boundary. Copying one across stamps the wrong kind's DOI onto the
    artifact — and it does it only on genomes that carry NO attestation, which is
    every genome the rest of this file does not build. Measured as a genuine
    native-vs-pure byte divergence at index 477 of the exported ``.chr``
    (``…persistence`` where ``…chromosome`` belonged) before the fix, so this
    clause is a real regression guard, not a restatement.
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        path = _default(tmp, "d.genome")
        assert _block(path)["source_doi"] == "10.0/srmech.genome.persistence"

        out = tmp / "alpha.chr"
        G.genome_export(path, "alpha", out, coupling=_coupling())
        assert _chr_block(out)["source_doi"] == "10.0/srmech.genome.chromosome", (
            "the genome's DEFAULT block was copied into the .chr"
        )

        dest = tmp / "seeded.genome"
        G.genome_import(out, dest, coupling=_coupling())
        assert _block(dest)["source_doi"] == "10.0/srmech.genome.persistence", (
            "the .chr's DEFAULT block was copied into the seeded genome"
        )


# ──────────────────────────────────────────────────────────────────────
# §5.1 / the SPY — a parity test that cannot enter C is not a parity test.
# ──────────────────────────────────────────────────────────────────────


def test_the_compiled_projection_is_actually_entered() -> None:
    """SPY. ``test_genome_attestation_rc304.py:193``
    ``test_override_manifest_native_equals_pure`` built a "native" arm and a
    "pure" arm and asserted byte-equal manifests — but with an attestation
    present ``genome.py`` forced the PURE branch in both, so it compared pure
    to pure and could not fail. Measured: ``genome_save_c`` was called ONCE
    with the attestation omitted and ZERO times with it present. That test is
    deleted by this rc; this is what replaces it.

    The asymmetry sat exactly on the capability C lacked, which is why the
    dead gate is evidence rather than an accident.
    """
    if not _native.has_native_genome():
        pytest.skip("no compiled genome surface in this cell")
    calls: List[str] = []
    real = _native.genome_save_c

    def spy(*args, **kwargs):
        calls.append(str(kwargs.get("attestation")))
        return real(*args, **kwargs)

    _native.genome_save_c = spy
    try:
        with tempfile.TemporaryDirectory() as td:
            _attested(pathlib.Path(td), "g.genome")
    finally:
        _native.genome_save_c = real
    assert calls, "genome_save_c was never entered WITH an attestation present"
    assert "GPL-3.0-only" in calls[0], (
        "the compiled path was entered but the attestation did not reach it"
    )


@pytest.mark.parametrize("name,mutate", MUTATORS, ids=[m[0] for m in MUTATORS])
def test_the_two_projections_write_the_same_manifest_bytes(name, mutate) -> None:
    """ADR-0009 parity, on the capability that did not exist until this rc.

    This is the clause the deleted rc304 test CLAIMED to make. It could not:
    there was no C entry point taking an attestation, so its counterfactual
    ("what a byte-identical C save would emit for the same override") had no
    referent. It does now.
    """
    if not _native.has_native_genome():
        pytest.skip("no compiled genome surface in this cell")

    def run() -> bytes:
        with tempfile.TemporaryDirectory() as td:
            path = _attested(pathlib.Path(td), "g.genome")
            try:
                mutate(path)
            except G.GenomeAttestationConflict:
                pass
            return (path / "manifest.json").read_bytes()

    native_bytes = run()
    saved = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    try:
        pure_bytes = run()
    finally:
        _native.HAS_NATIVE = saved
    assert native_bytes == pure_bytes, (
        f"{name}: the two projections diverge on the manifest bytes"
    )


def test_the_c_entry_point_accepts_what_its_python_peer_accepts() -> None:
    """§5.4 — THE ADR-0009 CAPABILITY CLAUSE.

    This defect was invisible to every DIFFERENTIAL test because both
    projections agreed perfectly. So this clause asserts the CAPABILITY, not
    the value: every C entry point that WRITES a genome manifest must accept a
    caller attestation, read off the live ctypes ``argtypes`` — the wire
    contract itself, not a docstring about it.

    **Scope, measured rather than assumed.** The brief listed ten write
    symbols. A census of ``genome_write_file`` call sites in
    ``c/src/srmech_genome.c`` finds only THREE places that write a manifest or
    a ``.chr`` — ``srmech_genome_save``, the O(1) head append, and the ``.chr``
    export — and every other write op reaches one of them. ``from_graph`` and
    ``add_plasmid`` emit IN-MEMORY blocks and write no manifest at all, so
    they need no channel, for exactly the reason the brief already exempts
    ``integrate_plasmids``. Eight symbols, not ten.
    """
    if not _native.HAS_NATIVE:
        pytest.skip("no compiled library in this cell")
    lib = _native.LIB
    import ctypes

    writers = (
        "srmech_genome_save",
        "srmech_genome_append",
        "srmech_genome_remove",
        "srmech_genome_replace",
        "srmech_genome_export",
        "srmech_genome_import",
        "srmech_genome_pack",
        "srmech_genome_plasmid_extract",
    )
    assert writers, "the writer roster is empty — this clause would be vacuous"
    for name in writers:
        fn = getattr(lib, name, None)
        assert fn is not None, f"{name} is not exported by libsrmech"
        argtypes = list(fn.argtypes or ())
        assert argtypes, f"{name} has no bound argtypes"
        # the channel is (const char *, size_t) — a c_char_p immediately
        # followed by a c_size_t, sitting before the caller arena.
        pairs = [
            i for i in range(len(argtypes) - 1)
            if argtypes[i] is ctypes.c_char_p
            and argtypes[i + 1] is ctypes.c_size_t
        ]
        assert pairs, (
            f"{name} advertises no (const char *, size_t) attestation channel; "
            f"its Python peer accepts attestation= and the compiled projection "
            f"cannot express it (ADR-0009 capability gap)"
        )

    # ⚠️ NEGATIVE CONTROL. A clause that found the pair in EVERY symbol would
    # be measuring the C calling convention, not this rc. A READ op must not
    # have gained one.
    census = getattr(lib, "srmech_genome_census", None)
    if census is not None and census.argtypes:
        assert ctypes.c_char_p not in list(census.argtypes)[1:], (
            "srmech_genome_census gained a char* — the roster above is no "
            "longer discriminating between write ops and read ops"
        )


def test_upgrade_v15_to_v16_has_no_c_symbol_and_that_is_correct() -> None:
    """Pinned so a later reader does not "fix" it. ``upgrade_v15_to_v16`` is a
    manifest RE-STAMP classified ``non_compute`` in
    ``tests/rosetta_classification.ndjson`` and pinned by name in
    ``tests/test_non_compute_ratchet_rc170.py``. It dispatches ``json_loads_c``
    + ``sha256_shani_c`` and needs no whole-op entry point of its own. It is
    NOT an overlooked wire-glue gap, and it still had to learn to preserve —
    which it does, in Python, above."""
    if not _native.HAS_NATIVE:
        pytest.skip("no compiled library in this cell")
    assert not hasattr(_native.LIB, "srmech_genome_upgrade_v15_to_v16")


# ──────────────────────────────────────────────────────────────────────
# §5.3  test_the_audit_agrees_with_the_reader — the invariant that would
#       have caught the read half on day one. Measured at rc417: 180 of 180
#       rows DISAGREED. Maximally non-vacuous; it goes to 0 on fix.
# ──────────────────────────────────────────────────────────────────────


def _sources() -> List[str]:
    listing = _catalog.list_attested_sources()
    return sorted(s["key"] for s in listing["sources"])


def test_the_source_roster_is_not_empty() -> None:
    """EMPTY-ROSTER GUARD for the audit clause."""
    assert _sources(), "no registered attested sources — the audit clause is vacuous"


def test_the_audit_agrees_with_the_reader() -> None:
    """For EVERY registered source and EVERY row, the audit's projected fields
    equal the reader's attestation for the same row.

    One reader, one answer. Before rc418 there were two: ``attestation_audit``
    called ``read_ndjson`` directly and reported an empty block for all eight
    data-only sources, while ``get_attested_dataset`` returned the synthesised
    block for the very same rows. No differential test could see it because
    both PROJECTIONS of each reader agreed with each other.
    """
    disagreements: List[str] = []
    compared = 0
    for key in _sources():
        audit = _catalog.attestation_audit(key)
        if not audit.get("ok"):
            continue
        rows = list(_catalog.iter_attested_dataset(key))
        assert len(rows) == len(audit["rows"]), (
            f"{key}: audit reports {len(audit['rows'])} rows, reader yields "
            f"{len(rows)} — they are not reading the same file"
        )
        for index, (arow, record) in enumerate(zip(audit["rows"], rows)):
            for field in _catalog.AUDIT_PROJECTED_FIELDS:
                compared += 1
                want = str(record.attestation.get(field, ""))
                got = str(arow.get(field, ""))
                if got != want:
                    disagreements.append(
                        f"{key}[{index}].{field}: audit {got!r} != reader {want!r}"
                    )
    assert compared, "nothing was compared — the clause is vacuous"
    assert not disagreements, (
        f"{len(disagreements)} of {compared} projected fields disagree; "
        f"first five: {disagreements[:5]}"
    )


def test_the_audit_actually_reports_something() -> None:
    """NON-VACUITY (template ``:602``). A projection that silently emptied
    itself again would satisfy the equality clause above trivially — both
    sides blank. At least one source must yield a POPULATED ``source_doi``
    and a populated ``response_sha256``."""
    populated_doi = 0
    populated_sha = 0
    for key in _sources():
        audit = _catalog.attestation_audit(key)
        for row in audit.get("rows", ()):
            if row.get("source_doi"):
                populated_doi += 1
            if row.get("response_sha256"):
                populated_sha += 1
    assert populated_doi, "no row reports a source_doi — the projection is blank"
    assert populated_sha, "no row reports a response_sha256"


def test_the_audit_projects_the_doi_it_promises() -> None:
    """The audit's own docstring says a consumer can "reproduce the row's
    provenance trail". A trail with no DOI is not one, and the omission was
    self-concealing: 51 of 180 readable rows were short of EXACTLY
    ``source_doi`` and the audit could not have reported that either way."""
    assert "source_doi" in _catalog.AUDIT_PROJECTED_FIELDS
    assert "source_url" in _catalog.AUDIT_PROJECTED_FIELDS
    assert "license" in _catalog.AUDIT_PROJECTED_FIELDS


def test_the_committed_envelope_source_is_read_verbatim() -> None:
    """``genetic_code`` is the one catalogue committed as a whole MPR envelope.
    Its attestation was minted when the upstream response was captured, so it
    must be read back VERBATIM — synthesising over it would manufacture a
    ``response_sha256`` over the row's own JSON on top of one that already
    hashes the real upstream response."""
    if "genetic_code" not in _sources():
        pytest.skip("genetic_code is not registered in this cell")
    rows = list(_catalog.iter_attested_dataset("genetic_code"))
    assert rows, "genetic_code yielded no rows"
    attestation = rows[0].attestation
    assert attestation.get("source_doi"), "the committed DOI was not read back"
    assert len(str(attestation.get("response_sha256", ""))) == 64


# ──────────────────────────────────────────────────────────────────────
# §5.5  read_ndjson raises TYPED on every malformed shape.
#
# Measured at rc417: SEVEN of twelve escaped as a bare ``TypeError`` from the
# ``dict()`` coercions in ``format.py`` — list/int/bool/null in ``data``,
# list/int in ``attestation``, list in ``rendering``. A ``TypeError`` with no
# line number is not a diagnosis.
# ──────────────────────────────────────────────────────────────────────

MALFORMED_SHAPES: Tuple[Tuple[str, str], ...] = tuple(
    (f"{key}:{kind}", body)
    for key in ("data", "attestation", "rendering")
    for kind, body in (
        ("list", "[]"),
        ("number", "1"),
        ("bool", "true"),
        ("null", "null"),
    )
    for body in (body,)
)


def test_the_malformed_shape_roster_is_not_empty() -> None:
    """EMPTY-ROSTER GUARD."""
    assert len(MALFORMED_SHAPES) == 12, (
        f"expected 12 shapes (3 coerced keys x 4 JSON value-types), "
        f"got {len(MALFORMED_SHAPES)}"
    )


@pytest.mark.parametrize("label,body", MALFORMED_SHAPES,
                         ids=[s[0] for s in MALFORMED_SHAPES])
def test_read_ndjson_raises_typed_on_every_malformed_shape(label, body) -> None:
    """Every malformed shape must raise ``MPRValidationError`` carrying the
    LINE NUMBER — never a bare ``TypeError`` from a ``dict()`` coercion."""
    key = label.split(":")[0]
    line = (
        '{"mpr_version": "1.0", "data_schema_id": "test://schema/x", '
        f'"{key}": {body}}}'
    )
    with tempfile.TemporaryDirectory() as td:
        path = pathlib.Path(td) / "row.ndjson"
        path.write_text("# a comment header\n\n" + line + "\n", encoding="utf-8")
        with pytest.raises(MPRValidationError) as excinfo:
            list(read_ndjson(path))
        message = str(excinfo.value)
        assert "3" in message, (
            f"{label}: the raise does not carry the line number: {message!r}"
        )


def test_read_ndjson_still_accepts_a_well_formed_line() -> None:
    """⚠️ NEGATIVE CONTROL for §5.5. A reader that raised on EVERYTHING would
    satisfy all twelve clauses above and be useless."""
    line = (
        '{"mpr_version": "1.0", "data_schema_id": "test://schema/x", '
        '"data": {"k": 1}, "attestation": {}, "rendering": {}}'
    )
    with tempfile.TemporaryDirectory() as td:
        path = pathlib.Path(td) / "row.ndjson"
        path.write_text(line + "\n", encoding="utf-8")
        rows = list(read_ndjson(path))
    assert len(rows) == 1
    assert rows[0].data == {"k": 1}
