"""v0.9.0rc279 (§102 / F1252 STAGE 2 — ORGANIZE) — the incremental organize step.

Stage 2 of the two-stage genome encode (design:
``docs/srmech/notes/f1252_two_stage_encode_design.md``). It consumes what rc278's
stage 1 built — an append-only store of plasmid sections plus the streamed
``section_count`` accumulator — and ORGANIZES it: CONSERVE (derive ``k`` from the
section-count distribution) -> PROMOTE (mint the induced core subgraph, the ``0x58``
centromere) -> MERGE (fold the retained plasmid sections in via ``integrate``).

Proven here:
  * **``k`` is DERIVED, not tuned** — on SYNTHETIC fixtures with a KNOWN planted
    core/periphery structure, the antimode read recovers the PLANTED split exactly,
    and a fixture whose periphery sits at a different count yields a DIFFERENT ``k``
    (so ``k`` tracks the data rather than being a constant);
  * a UNIMODAL distribution yields ONE-DNA-TYPE — the split is NOT forced (F1250);
  * **incremental == from-scratch**, BYTE-IDENTICALLY: ``add_plasmid`` D times
    produces the same organized genome as one ``genome_integrate_plasmids`` over the
    same D sections (the incremental rule is EXACT, not an approximation);
  * the organize equals a literal ``genome.integrate`` FOLD (so the accumulated
    concatenation is a proven-equal form of the primitive, not a shortcut past it);
  * **C<->Python BYTE-PARITY** — the native ``srmech_genome_integrate_plasmids``
    orchestrator's organized strand == the pure fold, block for block; and the native
    ``srmech_genome_conserved_core`` CONSERVE peer agrees with the pure antimode;
  * the F1251 SHAPE — the organized genome censuses as ONE ``nuclear`` core
    chromosome + the retained ``plasmid`` sections;
  * **the FAST PATH does no count re-derivation** — supplying ``section_count``
    (which stage 1 returns for free) never calls ``section_counts``, whose full
    section-body re-scan is the deliberate slow verification path;
  * the streamed accumulator == the derived on-disk read (the SSoT check);
  * §101 progress/cancel truncates at a whole-CHROMOSOME boundary — a valid, readable
    shorter organized genome, never a half-written chromosome.

**NOT proven here, and NOT claimed:** that the conservation criterion
(section-count >= k) CONVERGES with F1250's global cross-community participation
antimode. They are DIFFERENT discriminators — cross-DOCUMENT sharing vs
cross-COMMUNITY boundary mass — and the real corpus was not available to this rc, so
that convergence is **PENDING validation on the real corpus**. Everything asserted
below runs on synthetic fixtures with a planted structure.

numpy-free (no ``import numpy`` here — the whole file runs in a numpy-absent venv);
integer/exact (Class-N); no ``abs()``.
"""
from __future__ import annotations

import tempfile

import pytest

from srmech.amsc import _native
from srmech.biology import genome as G
from srmech.biology import plasmid as P
from srmech.math.hdc import klein4_expand

_DIM = 64                                           # >= 52 (the §89 kernel header)
_CORE = ["alpha", "beta", "gamma", "delta"]         # the PLANTED conserved core


def _one(seed=1279):
    return klein4_expand(_DIM, seed)


def _tmp():
    return tempfile.mkdtemp(prefix="srmech_organize_")


def _planted_every_doc(n_docs=12):
    """PLANTED FIXTURE A — the core words appear in EVERY document (count == n_docs);
    every periphery word appears in exactly ONE (count == 1). The section-count
    histogram is therefore occupied at {1, n_docs} with a wide empty valley between,
    so the antimode MUST split at k == 2 and recover exactly ``_CORE``."""
    return [list(_CORE) + [f"w{i}a", f"w{i}b", f"w{i}c"] for i in range(n_docs)]


def _planted_triples(n_triples=4):
    """PLANTED FIXTURE B — the core words appear in EVERY document (count == 12); the
    periphery words are shared across a TRIPLE of documents (count == 3). The
    histogram is occupied at {3, 12}, so the derived threshold is k == 4 — a DIFFERENT
    k from fixture A on the same code path, which is what makes ``k`` an output of the
    data rather than a constant."""
    docs = []
    for t in range(n_triples):
        for _ in range(3):
            docs.append(list(_CORE) + [f"p{t}a", f"p{t}b", f"p{t}c"])
    return docs


def _core_ids(vocab):
    """The GLOBAL ids the planted core words interned to."""
    return sorted(vocab.index(w) for w in _CORE)


def _extract(docs, store, one):
    return P.plasmid_extract(docs, store, one)


def _blocks(strand):
    return [bytes(h) for h in strand]


# ── k is DERIVED from the data ──────────────────────────────────────────────────

def test_derived_k_recovers_the_planted_core_every_doc():
    """FIXTURE A: the antimode recovers the PLANTED core exactly, with k == 2."""
    one = _one()
    ext = _extract(_planted_every_doc(), _tmp(), one)
    split = P.conserved_core(ext["section_count"])
    assert split["bimodal"] is True
    assert split["k"] == 2, f"expected the planted valley to derive k == 2; got {split['k']}"
    assert split["core"] == _core_ids(ext["vocab"]), (
        "the derived core must be EXACTLY the planted core words")
    assert split["n_core"] == len(_CORE)


def test_derived_k_tracks_the_distribution_not_a_constant():
    """FIXTURE B: the same code path derives a DIFFERENT k (4, not 2) because the
    periphery sits at count 3 — proof that k is measured, never tuned."""
    one = _one()
    ext = _extract(_planted_triples(), _tmp(), one)
    split = P.conserved_core(ext["section_count"])
    assert split["bimodal"] is True
    assert split["k"] == 4, (
        f"periphery at count 3 must push the derived threshold to k == 4; got {split['k']}")
    assert split["core"] == _core_ids(ext["vocab"])


def test_core_is_the_asymmetric_minority():
    """The F1251 SHAPE — a SMALL conserved core against a LARGE accessory remainder,
    not a 50/50 split."""
    one = _one()
    ext = _extract(_planted_every_doc(), _tmp(), one)
    split = P.conserved_core(ext["section_count"])
    assert split["n_core"] < split["n_accessory"], "the conserved core must be the minority"


def test_unimodal_distribution_is_one_dna_type_not_a_forced_split():
    """No clean antimode valley -> ACCEPT ONE-DNA-TYPE. The split is NOT forced (the
    F1250 discipline), so the core is empty and no chromosome is promoted."""
    flat = {i: 3 for i in range(20)}                 # one contiguous mass, no valley
    split = P.conserved_core(flat)
    assert split["bimodal"] is False
    assert split["one_dna_type"] is True
    assert split["core"] == [] and split["k"] == 0
    assert split["k_source"] == P.K_DECLINED


# ── the HEAVY-TAILED case: the method must HONESTLY DECLINE ─────────────────────

def _f1253_measured_curve(scale=100_000):
    """THE REAL SHAPE — a section-count distribution reproducing the F1253 measurement
    over the FULL simplewiki store (1,100,189 ids across 240,881 plasmid sections):

        singleton 64.6% | >=2 35.4% | >=5 14.5% | >=10 8.4%
        >=25 4.3% | >=50 2.7% | >=100 1.7%

    The successive ratios (35.4/14.5 ~ 2.4, 14.5/8.4 ~ 1.7, 8.4/4.3 ~ 2.0,
    4.3/2.7 ~ 1.6, 2.7/1.7 ~ 1.6) decay SMOOTHLY — a heavy-tailed, near-power-law
    curve, NOT a bimodal one with a clean valley. A scale-free distribution has no
    characteristic scale and therefore NO natural antimode. Deterministic (no RNG)."""
    bands = [(1, 1, 0.646), (2, 4, 0.209), (5, 9, 0.061), (10, 24, 0.041),
             (25, 49, 0.016), (50, 99, 0.010), (100, 240_881, 0.017)]
    counts = []
    for lo, hi, frac in bands:
        n = int(scale * frac)
        span = hi - lo + 1
        for j in range(n):                           # power-law placement in-band
            counts.append(lo + int((span - 1) * (j / max(n - 1, 1)) ** 3))
    return {i: c for i, c in enumerate(counts)}


def test_heavy_tailed_real_curve_declines_to_derive_a_k():
    """**THE DECLINE PATH — as load-bearing as the success path.** On the REAL F1253
    conservation curve the antimode finds no qualifying split, so ``conserved_core``
    must report "no natural split in this distribution" rather than manufacture a
    threshold: ``k_source == "declined"``, ``k == 0``, an EMPTY core.

    This is the honest outcome for a scale-free distribution, and it is a FINDING, not
    a failure — the count-threshold discriminator may simply have no natural split."""
    split = P.conserved_core(_f1253_measured_curve())
    assert split["k_source"] == P.K_DECLINED, (
        "a heavy-tailed / near-power-law curve has no characteristic scale and so no "
        "natural antimode — the method MUST decline, not invent a k")
    assert split["bimodal"] is False and split["one_dna_type"] is True
    assert split["k"] == 0
    assert split["core"] == [], "no core may be promoted from a declined derivation"


def test_declining_organize_promotes_no_core_and_says_so():
    """A declined derivation organizes as ALL-PLASMID — no nuclear chromosome is
    minted — and the result reports the provenance so a caller cannot mistake it."""
    one = _one()
    store = _tmp()
    docs = _planted_every_doc(4)
    ext = _extract(docs, store, one)
    flat = {v: 1 for v in ext["section_count"]}      # a declining distribution
    org = P.genome_integrate_plasmids(store, one, section_count=flat)
    assert org["k_source"] == P.K_DECLINED
    assert org["core"] == [] and org["counts"]["nuclear"] == 0
    assert org["status"] == "ok"                     # a decline is not an error
    out = _tmp() + "/declined.genome"
    P.genome_integrate_plasmids(store, one, section_count=flat, out_path=out)
    kinds = {c["type"] for c in G.genome_census(out, coupling=one)["chromosomes"]}
    assert "nuclear" not in kinds, "a declined derivation must mint NO nuclear core"


def test_k_source_separates_measured_from_stated_policy():
    """A DERIVED k and a caller-supplied k must never be confused. An explicit integer
    is a STATED POLICY CHOICE the caller owns (``k_source == "policy"``) — it is not
    presented as measured, whatever value it takes."""
    one = _one()
    ext = _extract(_planted_every_doc(), _tmp(), one)
    derived = P.conserved_core(ext["section_count"])
    assert derived["k_source"] == P.K_DERIVED
    policy = P.conserved_core(ext["section_count"], k=12)
    assert policy["k_source"] == P.K_POLICY and policy["k"] == 12
    assert policy["core"] == _core_ids(ext["vocab"])
    # a policy k applied to a curve that DECLINES is still policy, never "derived"
    forced_on_flat = P.conserved_core(_f1253_measured_curve(), k=5)
    assert forced_on_flat["k_source"] == P.K_POLICY
    assert forced_on_flat["k"] == 5
    assert P.conserved_core(ext["section_count"], k="auto")["k_source"] == P.K_DERIVED
    with pytest.raises(ValueError):
        P.conserved_core(ext["section_count"], k=0)


def test_k_is_not_selected_to_reproduce_the_attested_core_fraction():
    """**Anti-numerology guard.** F1251 attests a ~16 % nuclear core, and on the F1253
    curve ``k>=5`` happens to give 14.5 % — but that correspondence is
    threshold-dependent and MUST NOT be how ``k`` is chosen. The derivation reads the
    distribution's own antimode and nothing else, so on this curve it DECLINES rather
    than landing on the value that would match the attested fraction."""
    curve = _f1253_measured_curve()
    assert P.conserved_core(curve)["k_source"] == P.K_DECLINED
    matching = P.conserved_core(curve, k=5)          # the ~16%-reproducing threshold
    frac = 100.0 * matching["n_core"] / len(curve)
    assert 10.0 < frac < 20.0, f"sanity: k>=5 lands near the attested band ({frac:.1f}%)"
    assert matching["k_source"] == P.K_POLICY, (
        "the fraction-matching threshold must be reported as a caller POLICY choice — "
        "selecting k to reproduce ~16% would be post-hoc numerology, not a derivation")


# ── the organized genome ────────────────────────────────────────────────────────

def test_organize_censuses_as_nuclear_core_plus_plasmids():
    """The F1251 shape on disk: ONE minted NUCLEAR core chromosome (the 0x58
    centromere is present) + the retained PLASMID sections."""
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)
    out = _tmp() + "/organized.genome"
    org = P.genome_integrate_plasmids(store, one, section_count=ext["section_count"],
                                      out_path=out)
    assert org["status"] == "ok"
    kinds = {}
    for chrom in G.genome_census(out, coupling=one)["chromosomes"]:
        kinds[chrom["type"]] = kinds.get(chrom["type"], 0) + 1
    assert kinds.get("nuclear") == 1, f"expected exactly ONE minted core; got {kinds}"
    assert kinds.get("plasmid") == org["n_sections"]


def test_organize_equals_a_literal_integrate_fold():
    """The accumulated concatenation IS ``genome.integrate`` folded over the sections
    (``at=None`` makes the splice a tail-append, and concatenation is associative) —
    so the fast path is a proven-equal form of the primitive, not a shortcut past it."""
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)
    org = P.genome_integrate_plasmids(store, one, section_count=ext["section_count"])
    labels = P._section_labels(store, one)
    split = P.conserved_core(ext["section_count"])
    edges = [P._section_global_edges(store, lb, one) for lb in labels]
    weight = P._core_weight_from_sections(edges, set(split["core"]))
    fold = G.mint_strand(P._core_packed(split["core"], weight, one, _DIM), one)
    for lb in labels:
        fold = G.integrate(fold, P._section_strand(store, lb, one, _DIM))
    assert _blocks(fold) == _blocks(org["strand"])


# ── the INCREMENTAL contract ────────────────────────────────────────────────────

def test_incremental_equals_from_scratch_byte_identically():
    """THE rc279 EQUIVALENCE PROOF — ``add_plasmid`` D times produces a BYTE-IDENTICAL
    organized genome to one from-scratch ``genome_integrate_plasmids`` over the same D
    sections. The incremental rule is EXACT, not an approximation."""
    one = _one()
    docs = _planted_every_doc()
    batch_store = _tmp()
    ext = _extract(docs, batch_store, one)
    batch = P.genome_integrate_plasmids(batch_store, one,
                                        section_count=ext["section_count"])
    inc_store = _tmp()
    state, last = None, None
    for doc in docs:
        last = P.add_plasmid(inc_store, one, doc, state=state)
        state = last["state"]
    assert last["n_sections"] == batch["n_sections"]
    assert last["k"] == batch["k"]
    assert _blocks(last["strand"]) == _blocks(batch["strand"]), (
        "the incremental organize must equal the from-scratch organize byte for byte")


def test_incremental_running_counts_match_the_batch_accumulator():
    one = _one()
    docs = _planted_every_doc()
    ext = _extract(docs, _tmp(), one)
    state = None
    for doc in docs:
        state = P.add_plasmid(_INC_STORE, one, doc, state=state)["state"]
    assert state["section_count"] == ext["section_count"]


def test_incremental_without_the_edge_cache_is_equivalent():
    """``cache_edges=False`` trades memory for a store re-read on a core change; the
    organized genome is unchanged."""
    one = _one()
    docs = _planted_every_doc(6)
    cached_store, plain_store = _tmp(), _tmp()
    state, cached = None, None
    for doc in docs:
        cached = P.add_plasmid(cached_store, one, doc, state=state)
        state = cached["state"]
    state, plain = None, None
    for doc in docs:
        plain = P.add_plasmid(plain_store, one, doc, state=state, cache_edges=False)
        state = plain["state"]
    assert _blocks(plain["strand"]) == _blocks(cached["strand"])


# ── the FAST PATH (the streamed accumulator, not a re-scan) ─────────────────────

def test_supplying_section_count_never_re_derives_the_counts(monkeypatch):
    """THE HOT-PATH GATE. ``plasmid_extract`` returns ``section_count`` for free as a
    streamed accumulator; stage 2 must CONSUME it. Re-deriving would decode every
    section body — the measured ~0.33 s/section full re-scan — which would replace one
    slow monolithic step with another. Supplying the accumulator must not call
    :func:`section_counts` at all."""
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)

    def _boom(*_a, **_k):
        raise AssertionError(
            "genome_integrate_plasmids re-derived section_counts on the FAST path — "
            "the supplied streamed accumulator must be consumed as-is")

    monkeypatch.setattr(P, "section_counts", _boom)
    org = P.genome_integrate_plasmids(store, one, section_count=ext["section_count"])
    assert org["status"] == "ok" and org["k"] == 2


def test_supplying_core_edges_skips_the_core_harvest_read(monkeypatch):
    """With both the accumulator AND the per-section edge lists supplied, stage 2 reads
    NO section body for the core harvest (the fully-chained stage-1 -> stage-2 path)."""
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)
    labels = P._section_labels(store, one)
    edges = [P._section_global_edges(store, lb, one) for lb in labels]
    calls = []
    real = P._section_global_edges
    monkeypatch.setattr(P, "_section_global_edges",
                        lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    org = P.genome_integrate_plasmids(store, one, section_count=ext["section_count"],
                                      core_edges=edges)
    assert calls == [], "the core harvest re-read sections despite core_edges being supplied"
    assert org["status"] == "ok"


def test_the_slow_fallback_still_agrees_with_the_accumulator():
    """The re-derivation path is the deliberate VERIFICATION route — it must produce
    the same organized genome as the free accumulator (the SSoT check)."""
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)
    assert P.section_counts(store, coupling=one) == ext["section_count"], (
        "the streamed accumulator and the on-disk derived read must agree")
    fast = P.genome_integrate_plasmids(store, one, section_count=ext["section_count"])
    slow = P.genome_integrate_plasmids(store, one)          # re-derives (slow path)
    assert _blocks(slow["strand"]) == _blocks(fast["strand"])


# ── C <-> Python byte parity ────────────────────────────────────────────────────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_native_organize_is_byte_identical_to_pure(monkeypatch):
    """The parity contract — the C orchestrator's organized strand == the pure fold,
    block for block."""
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)
    assert _native.has_native_genome_integrate_plasmids(), "rc279 C peer not bound"
    native = P.genome_integrate_plasmids(store, one, section_count=ext["section_count"])
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    pure = P.genome_integrate_plasmids(store, one, section_count=ext["section_count"])
    assert _blocks(native["strand"]) == _blocks(pure["strand"])
    assert native["k"] == pure["k"] and native["core"] == pure["core"]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_native_conserved_core_agrees_with_the_pure_antimode(monkeypatch):
    """The CONSERVE peer derives the SAME k and the SAME core set as the pure walk."""
    one = _one()
    assert _native.has_native_genome_conserved_core(), "rc279 CONSERVE peer not bound"
    for docs in (_planted_every_doc(), _planted_triples()):
        counts = _extract(docs, _tmp(), one)["section_count"]
        native = P.conserved_core(counts)
        monkeypatch.setattr(_native, "HAS_NATIVE", False)
        pure = P.conserved_core(counts)
        monkeypatch.setattr(_native, "HAS_NATIVE", True)
        assert native["k"] == pure["k"]
        assert native["core"] == pure["core"]
        assert native["bimodal"] == pure["bimodal"]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_native_organize_actually_dispatches():
    """Guard against a VACUOUS parity test: the C peer must really run (a silent
    decline would make native == pure trivially true)."""
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)
    labels = P._section_labels(store, one)
    split = P.conserved_core(ext["section_count"])
    edges = [P._section_global_edges(store, lb, one) for lb in labels]
    weight = P._core_weight_from_sections(edges, set(split["core"]))
    packed = P._core_packed(split["core"], weight, one, _DIM)
    strands = [P._section_strand(store, lb, one, _DIM) for lb in labels]
    got = P._organize_native(packed, strands, one, _DIM, None)
    assert got is not None, "the rc279 C orchestrator DECLINED — parity would be vacuous"
    assert got[1] == len(labels) and got[2] is False


# ── §101 progress / graceful abort ──────────────────────────────────────────────

def test_progress_ticks_between_whole_chromosomes():
    """MINTING once for the core promote, then INTEGRATING per section with a monotone
    ``done`` that reaches ``total``."""
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)
    seen = []
    P.genome_integrate_plasmids(store, one, section_count=ext["section_count"],
                                progress=lambda ev: seen.append(
                                    (ev["phase"], ev["done"], ev["total"])) or False)
    minting = [e for e in seen if e[0] == _native.SRMECH_PHASE_MINTING]
    merging = [e for e in seen if e[0] == _native.SRMECH_PHASE_INTEGRATING]
    assert len(minting) == 1, f"expected ONE core-promote tick; got {minting}"
    assert [d for _p, d, _t in merging] == list(range(len(merging)))
    assert merging[-1][2] == ext["n_sections"]
    assert all(e[0] != _native.SRMECH_PHASE_EXTRACTING for e in seen), (
        "no EXTRACTING phase belongs to stage 2 on the fast path")


def test_cancel_truncates_at_a_chromosome_boundary():
    """A cancel yields a VALID shorter organized genome — the minted core plus the
    sections merged so far — never a half-written chromosome, and no save."""
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)
    full = P.genome_integrate_plasmids(store, one, section_count=ext["section_count"])
    stop_after = 3

    def _cancel(ev):
        return (ev["phase"] == _native.SRMECH_PHASE_INTEGRATING
                and ev["done"] == stop_after)

    part = P.genome_integrate_plasmids(store, one, section_count=ext["section_count"],
                                       progress=_cancel)
    assert part["status"] == "cancelled"
    assert part["n_integrated"] == stop_after
    assert len(part["strand"]) < len(full["strand"])
    # the partial is a PREFIX of the full organized genome — whole chromosomes only
    assert _blocks(part["strand"]) == _blocks(full["strand"])[:len(part["strand"])]
    recovered = G.partition(part["strand"], one)
    assert len(recovered) == stop_after + 1, (
        "the cancelled partial must recover as the minted core + the merged sections")


def test_cancel_does_not_write_out_path(tmp_path):
    one = _one()
    store = _tmp()
    ext = _extract(_planted_every_doc(), store, one)
    out = str(tmp_path / "never.genome")
    part = P.genome_integrate_plasmids(
        store, one, section_count=ext["section_count"], out_path=out,
        progress=lambda ev: ev["phase"] == _native.SRMECH_PHASE_INTEGRATING)
    assert part["status"] == "cancelled"
    assert not (tmp_path / "never.genome").exists()


_INC_STORE = _tmp()
