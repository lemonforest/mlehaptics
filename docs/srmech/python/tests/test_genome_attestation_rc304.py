"""§113 / rc304 (`#942`, tracker #1466) — a caller-supplied ``attestation=`` for
``genome_from_graph`` / ``genome_save``.

The genome directory is the SSoT (no sidecar files, §41/F1300), so an attested
corpus genome's TRUE source can only live INSIDE ``manifest.json``. Before rc304 the
manifest always carried the srmech DEFAULT attestation
(``srmech.net/genome/persistence`` / ``1970-01-01T00:00:00Z``), so a real corpus
genome (e.g. a simplewiki dump under CC-BY-SA-4.0) MISATTRIBUTED its own source. This
suite proves the caller override: it round-trips, persists to disk, is read back by
the manifest reader + survives census, passes MPR validation, and — crucially — is
byte-IDENTICAL whether the native genome save is present or not (ADR-0009: the
capability is the invariant). The default is unchanged when ``attestation`` is omitted.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from srmech import _native
from srmech.biology import genome as G
from srmech.math.hdc import klein4_expand
from srmech.amsc.format import MPRRecord, MPRValidationError, validate_mpr_record

_DIM = 64

#: a plausible REAL corpus attestation — the simplewiki dump the tracker names.
_SIMPLEWIKI = {
    "source_url": "https://dumps.wikimedia.org/simplewiki/latest/",
    "source_doi": "",  # intentionally left to default below by NOT including it
    "license": "CC-BY-SA-4.0",
    "retrieved_at": "2026-07-20T00:00:00Z",
    "response_sha256": "b" * 64,
}
# (source_doi carries an empty string ONLY to show it can be omitted — drop it here so
#  the dict is a genuine PARTIAL override that keeps the srmech default source_doi.)
_SIMPLEWIKI.pop("source_doi")

_SRMECH_DEFAULT_URL = "https://srmech.net/genome/persistence"
_SRMECH_DEFAULT_RETRIEVED = "1970-01-01T00:00:00Z"


def _one(seed: int = 1272):
    return klein4_expand(_DIM, seed)


def _clique(nodes, weight=5, charge=1):
    e, w, c = [], [], []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            e.append((nodes[i], nodes[j]))
            w.append(weight)
            c.append(charge)
    return e, w, c


def _bimodal_graph():
    """Two dense 10-cliques joined by two bridge nodes — a clean nuclear/plasmid split
    so ``genome_from_graph`` really builds + saves a multi-chromosome genome."""
    A = list(range(0, 10))
    B = list(range(10, 20))
    e, w, c = _clique(A)
    e2, w2, c2 = _clique(B)
    edges = e + e2
    weights = w + w2
    charges = c + c2
    for b in (20, 21):
        for t in (A[0], A[1], B[0], B[1]):
            edges.append((b, t))
            weights.append(1)
            charges.append(-1)
    edges.append((20, 21))
    weights.append(1)
    charges.append(1)
    return 22, edges, weights, charges


def _build(path, *, attestation=None):
    one = _one()
    n, edges, weights, charges = _bimodal_graph()
    return G.genome_from_graph(n, edges, weights, charges, coupling=one,
                               path=str(path), leaf_dim=_DIM, max_tome=10,
                               attestation=attestation)


def _manifest_attestation(path) -> dict:
    """Read the on-disk manifest THROUGH the MPR reader (MPRRecord) — the manifest
    reader path, not a bespoke json probe."""
    text = (Path(path) / "manifest.json").read_text(encoding="utf-8")
    rec = MPRRecord.from_json_line(text)
    return dict(rec.attestation)


# ── round-trip + persistence ─────────────────────────────────────────────────

def test_override_round_trips_to_manifest(tmp_path):
    """Write with a custom attestation; read manifest.json back; the fields match."""
    _build(tmp_path / "g", attestation=_SIMPLEWIKI)
    att = _manifest_attestation(tmp_path / "g")
    assert att["source_url"] == _SIMPLEWIKI["source_url"]
    assert att["license"] == _SIMPLEWIKI["license"]
    assert att["retrieved_at"] == _SIMPLEWIKI["retrieved_at"]
    assert att["response_sha256"] == _SIMPLEWIKI["response_sha256"]


def test_override_persists_to_disk_not_just_memory(tmp_path):
    """The override is on the actual file — re-open a fresh Path and re-read it."""
    _build(tmp_path / "g", attestation=_SIMPLEWIKI)
    reopened = json.loads((tmp_path / "g" / "manifest.json").read_bytes().decode("utf-8"))
    assert reopened["attestation"]["source_url"] == _SIMPLEWIKI["source_url"]
    assert reopened["attestation"]["source_url"] != _SRMECH_DEFAULT_URL


def test_default_unchanged_when_attestation_omitted(tmp_path):
    """No attestation -> the srmech default source is written (byte-for-byte legacy)."""
    _build(tmp_path / "g")
    att = _manifest_attestation(tmp_path / "g")
    assert att["source_url"] == _SRMECH_DEFAULT_URL
    assert att["retrieved_at"] == _SRMECH_DEFAULT_RETRIEVED


# ── read-back by the manifest reader / census ────────────────────────────────

def test_overridden_manifest_is_a_valid_mpr(tmp_path):
    """The written block passes MPR validation (a real, re-verifiable attestation)."""
    _build(tmp_path / "g", attestation=_SIMPLEWIKI)
    text = (tmp_path / "g" / "manifest.json").read_text(encoding="utf-8")
    rec = MPRRecord.from_json_line(text)
    validate_mpr_record(rec)  # raises MPRValidationError on any malformed field


def test_census_reads_overridden_genome(tmp_path):
    """The census/manifest reader still works on the overridden genome."""
    res = _build(tmp_path / "g", attestation=_SIMPLEWIKI)
    census = G.genome_census(str(tmp_path / "g"), coupling=_one())
    assert census["n_chromosomes"] == len(res["chromosomes"])
    assert census["types"]["nuclear"] >= 1


def test_response_sha256_override_does_not_weaken_body_integrity(tmp_path):
    """attestation.response_sha256 is a decorative MPR mirror; body integrity is
    anchored on data.body_sha256. Overriding response_sha256 with the DUMP sha must
    still load + integrity-check clean."""
    _build(tmp_path / "g", attestation=_SIMPLEWIKI)
    att = _manifest_attestation(tmp_path / "g")
    man = json.loads((tmp_path / "g" / "manifest.json").read_text(encoding="utf-8"))
    # the two are now DIFFERENT (dump sha, not body sha) — the whole point:
    assert att["response_sha256"] == "b" * 64
    assert att["response_sha256"] != man["data"]["body_sha256"]
    # ...and the genome still loads (body re-hashed against data.body_sha256):
    strand, coupling, labels = G.genome_load(str(tmp_path / "g"), coupling=_one())
    assert len(strand) > 0


# ── the encoder-identity fields stay srmech-owned; partial override ──────────

def test_encoder_fields_stay_srmech_owned(tmp_path):
    _build(tmp_path / "g", attestation=_SIMPLEWIKI)
    att = _manifest_attestation(tmp_path / "g")
    assert att["parser_version"].startswith("srmech ")
    assert att["collector_descriptor_path"] == "srmech/biology/genome.py"
    assert len(att["parser_rule_hash"]) == 64
    assert len(att["collector_descriptor_hash"]) == 64


def test_partial_override_keeps_unspecified_source_defaults(tmp_path):
    """A partial dict (no source_doi) keeps the srmech default source_doi — override-only,
    never blank-the-rest."""
    _build(tmp_path / "g", attestation={"source_url": "https://example.org/x"})
    att = _manifest_attestation(tmp_path / "g")
    assert att["source_url"] == "https://example.org/x"
    assert att["source_doi"] == "10.0/srmech.genome.persistence"   # default kept
    assert att["license"] == "CC0"                                  # default kept


# ── ADR-0009 parity: native and pure produce byte-identical output ───────────

def _force_pure(monkeypatch):
    monkeypatch.setattr(_native, "has_native_genome", lambda: False)


def test_default_manifest_native_equals_pure(tmp_path, monkeypatch):
    _build(tmp_path / "native")
    native_bytes = (tmp_path / "native" / "manifest.json").read_bytes()
    _force_pure(monkeypatch)
    _build(tmp_path / "pure")
    pure_bytes = (tmp_path / "pure" / "manifest.json").read_bytes()
    assert native_bytes == pure_bytes


# ``test_override_manifest_native_equals_pure`` lived here and was DELETED at
# v0.9.0rc418 (`#T1108`). It built a "native" arm and a "pure" arm and asserted
# byte-equal manifests — but with an attestation present, ``genome_save`` forced
# the PURE branch in BOTH arms (the compiled ``srmech_genome_save`` took no
# attestation at all), so it compared pure to pure and could not fail. Measured:
# ``genome_save_c`` was entered ONCE with the attestation omitted and ZERO times
# with it present. Its sibling ``test_default_manifest_native_equals_pure`` above
# is real; the asymmetry sat exactly on the capability C lacked.
#
# A parity test that cannot enter C is not a parity test. rc418 gives the C the
# channel and the replacement lives in
# ``tests/test_attestation_of_record_rc418.py`` — which parametrises the same
# comparison across every mutating op AND spies on the compiled entry point, so
# it cannot silently re-become the pure-vs-pure vacuum.


def test_turns_bin_identical_with_and_without_attestation(tmp_path):
    """The override touches ONLY the manifest — turns.bin is byte-identical."""
    _build(tmp_path / "cust", attestation=_SIMPLEWIKI)
    _build(tmp_path / "def")
    assert (tmp_path / "cust" / "turns.bin").read_bytes() == \
           (tmp_path / "def" / "turns.bin").read_bytes()


def test_pure_path_override_persists(tmp_path, monkeypatch):
    """The override works on the pure path too (native absent)."""
    _force_pure(monkeypatch)
    _build(tmp_path / "g", attestation=_SIMPLEWIKI)
    att = _manifest_attestation(tmp_path / "g")
    assert att["source_url"] == _SIMPLEWIKI["source_url"]


# ── rejection: a bad override never gets written silently ─────────────────────

def test_reject_unknown_key(tmp_path):
    with pytest.raises(ValueError, match="not an overridable source field"):
        _build(tmp_path / "g", attestation={"source_uri": "typo"})


def test_reject_encoder_field_override(tmp_path):
    with pytest.raises(ValueError, match="not an overridable source field"):
        _build(tmp_path / "g", attestation={"parser_version": "evil 9.9"})


def test_reject_non_dict(tmp_path):
    with pytest.raises(TypeError, match="must be a dict"):
        _build(tmp_path / "g", attestation="not-a-dict")


def test_reject_empty_value(tmp_path):
    with pytest.raises(MPRValidationError):
        _build(tmp_path / "g", attestation={"source_url": ""})


def test_reject_non_string_value(tmp_path):
    with pytest.raises(MPRValidationError):
        _build(tmp_path / "g", attestation={"license": 123})


def test_bad_override_writes_nothing_to_disk(tmp_path):
    """A malformed override RAISES before any bytes hit disk — no half-written genome.

    ⚠️ **THIS GATE WAS GREEN ON THE DEFECT IT APPEARS TO COVER, from rc304 to
    rc431 (`#T1132`).** Its name says *nothing* is written and its docstring says
    *no half-written genome*, but its only assertion was that ``manifest.json``
    is absent. Driven at rc431, the rejected call left ``d`` behind as an EMPTY
    DIRECTORY — ``genome_save``'s ``mkdir`` was the first statement of its body,
    above every validation — and this test passed anyway. That orphaned directory
    is the node ``write_packed_graph`` later opened as a file and died on.

    The strengthening below is NOT 'editing correct prose to make a gate green'.
    The prose was already false and the assertion was already too weak: it named
    a claim it did not check. After the rc432 reorder the test stays green and
    the sentence becomes TRUE."""
    d = tmp_path / "g"
    with pytest.raises(ValueError):
        _build(d, attestation={"source_uri": "typo"})
    # genome_from_graph builds the strand then saves; a rejected save leaves no manifest.
    assert not (d / "manifest.json").exists()
    assert not d.exists(), (
        f"the rejected save left its target directory behind: "
        f"{sorted(p.name for p in d.iterdir())}. An acquisition above a "
        f"validation is an orphan on the error path (`#T1132`)."
    )


# ── genome_save direct (the underlying path genome_from_graph composes) ───────

def test_genome_save_direct_attestation(tmp_path):
    """genome_save itself honours attestation= (the composed path)."""
    one = _one()
    n, edges, weights, charges = _bimodal_graph()
    res = G.genome_from_graph(n, edges, weights, charges, coupling=one, leaf_dim=_DIM,
                              max_tome=10)  # no path -> in-memory strand
    G.genome_save(res["strand"], str(tmp_path / "g"), one, attestation=_SIMPLEWIKI)
    att = _manifest_attestation(tmp_path / "g")
    assert att["source_url"] == _SIMPLEWIKI["source_url"]
    assert att["license"] == _SIMPLEWIKI["license"]
