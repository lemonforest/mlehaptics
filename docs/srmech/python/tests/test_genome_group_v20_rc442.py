"""§GROUP/v20 — the nesting grammar, its five refusals, and what it does NOT move.

rc442 (``#T1150``). ``GENOME_FORMAT_VERSION`` 19 → 20; ``SRMECH_ABI_VERSION`` 16 → 17.

WHAT v20 IS. Through v19 a strand was a FLAT sequence of chromosomes, so a genome that
wanted to say *"these sixteen units are ONE thing"* had nowhere to say it: it either FUSED
them (losing the sixteen) or kept them apart (losing the one). Two markers close that gap —
:data:`~srmech.biology.genome.GROUP_OPEN_MARKER` (``0x5B``) and
:data:`~srmech.biology.genome.GROUP_CLOSE_MARKER` (``0x5D``) — and with them come four axes:
GROUPING (store-level), CLOSURE, PARTITION-COUPLING, and DESIGNATION (per unit).

THE GRAMMAR::

    strand := unit*
    unit   := chrom | group
    group  := '[' unit+ ']'          (arity >= 1; arity 0 is malformed)
    chrom  := leaf-opener block*

**R1** ``[`` implicitly closes the open chromosome and pushes a frame. **R2** ``]``
implicitly closes the open chromosome, then pops the innermost frame. **R3** a data turn or
interior cap is legal ONLY inside a chromosome. **R4** R1–R3 jointly make CROSSED NESTING
*unrepresentable*.

R4 is the load-bearing rule, and section 3 below is the measurement that earns it: before
R3 existed, ``C t [ t C t ]`` SAVED, HASHED and ROUND-TRIPPED while carrying two mutually
inconsistent readings, with no error at any layer. A refusal is a much weaker guarantee
than an inexpressibility, and this file asserts the stronger one.

EVERY GATE HERE SHIPS WITH THE MUTATION THAT TURNS IT RED — the ``*_is_not_vacuous``
tests. A gate whose subject cannot be perturbed is not measuring anything, so each one
perturbs the thing its sibling asserts and shows the assertion moves: strip the frame
markers and the SY14 discriminator collapses onto the ungrouped body; change one opener
label byte and the C/Python differential's answer changes.

No stdlib ``fractions`` / ``math`` / ``decimal`` / numpy. No ``abs()`` — a block index and a
byte count are non-negative positions, not magnitudes.
"""

from __future__ import annotations

import pytest

from srmech import _native
from srmech.biology import genome as G
from srmech.math.hv import HV

_DIM = 16


def _one(seed=7):
    return HV.from_sequence([(seed * (i + 1)) % 4 for i in range(_DIM)], sectors=4)


def _chrom(label, n_turns=2, seed=7):
    one = _one(seed)
    return ([G._pack_cap(G.CHROM_CAP_MARKER, label, _DIM)]
            + [G.quad_turn(one, one) for _ in range(n_turns)])


def _blocks(strand):
    return b"".join(G._leaf_blocks(strand))


# ═══════════════════════════════════════════════════════════════════════════
# 1. The version and the vocabulary
# ═══════════════════════════════════════════════════════════════════════════

def test_format_version_and_abi_are_pinned():
    """Both move in the same change, for the first time since rc326: the format really
    does gain a marker, AND every genome read's status contract is reinterpreted."""
    # NAME CARRIES NO NUMBER ON PURPOSE. This pin tracks a value that MOVES;
    # a name that spells the value is falsified by the next bump and was —
    # 16 such tests were found tree-wide, one named for 367 asserting 663.
    # See test_pinned_names_carry_no_value_rc447.py.
    assert G.GENOME_FORMAT_VERSION == 20
    assert _native.EXPECTED_ABI_VERSION == 24


def test_the_two_markers_are_distinct_leaf_wide_caps_above_the_klein4_range():
    """A marker <= 3 would be indistinguishable from a Klein-4 data symbol, which is the
    invariant the whole self-describing walk rests on."""
    assert G.GROUP_OPEN_MARKER == 0x5B and G.GROUP_CLOSE_MARKER == 0x5D
    assert G.GROUP_OPEN_MARKER > 3 and G.GROUP_CLOSE_MARKER > 3
    assert G.GROUP_OPEN_MARKER in G._LEAF_WIDE_BLOCK_MARKERS
    assert G.GROUP_CLOSE_MARKER in G._LEAF_WIDE_BLOCK_MARKERS
    # and they collide with nothing already in the vocabulary
    others = [m for m in G._LEAF_WIDE_BLOCK_MARKERS if m not in G._GROUP_MARKERS]
    assert G.GROUP_OPEN_MARKER not in others and G.GROUP_CLOSE_MARKER not in others
    assert len(set(G._LEAF_WIDE_BLOCK_MARKERS)) == len(G._LEAF_WIDE_BLOCK_MARKERS)


def test_chrom_boundary_markers_is_UNCHANGED_by_v20():
    """The un-merge an earlier v20 draft proposed was WITHDRAWN, and this pins that.

    The draft flagged a ``body_sha256`` double-fold as its own highest-risk line; an
    adversarial pass REFUTED it, because the scan assigns every block to exactly ONE region
    and an overlap is therefore structurally unrepresentable. A frame marker does not open
    a chromosome, so it belongs in its own named subset and NOT in this one."""
    assert G._CHROM_BOUNDARY_MARKERS == (
        G.CHROM_CAP_MARKER, G.KERNEL_TELOMERE_MARKER,
        G.ACTIVE_TELOMERE_MARKER, G.DIPLOID_TELOMERE_MARKER)
    assert G._GROUP_MARKERS == (G.GROUP_OPEN_MARKER, G.GROUP_CLOSE_MARKER)
    assert not set(G._GROUP_MARKERS) & set(G._CHROM_BOUNDARY_MARKERS)
    # the derived §98 access-reset set therefore does not learn about frames either
    assert not set(G._GROUP_MARKERS) & set(G._ACCESS_RESET_MARKERS)


def test_the_closer_carries_nothing():
    """No label, no depth. Both are derivable from the walker's stack, so a written copy
    would be a sidecar field inside the object — and a written LABEL would be worse than
    redundant: it would make crossed nesting expressible again (a closer could name a group
    other than the innermost) and mint a sixth malformed class, label-mismatch-at-pop."""
    g = G.genome_group("grp-label", _chrom("aa"), dim=_DIM)
    closer = G._leaf_blocks(g)[-1]
    assert closer[0] == G.GROUP_CLOSE_MARKER
    assert closer[1:] == b"\x00" * (_DIM - 1), (
        "every byte after the marker must be NUL — the closer is payload-free"
    )
    opener = G._leaf_blocks(g)[0]
    assert opener[1:].split(b"\x00", 1)[0] == b"grp-label", (
        "the label lives on the OPENER, once"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 2. The five malformed classes — each refused, each in ONE forward pass
# ═══════════════════════════════════════════════════════════════════════════

def _open(label="x"):
    return G._pack_cap(G.GROUP_OPEN_MARKER, label, _DIM)


def _close():
    return G._pack_cap(G.GROUP_CLOSE_MARKER, "", _DIM)


_MALFORMED = {
    # name                         strand
    "closer_without_opener": lambda: _chrom("aa") + [_close()],
    "unclosed_opener": lambda: [_open()] + _chrom("aa"),
    "childless_group": lambda: [_open(), _close()],
    "turn_at_group_scope": lambda: (
        [_open()] + [G.quad_turn(_one(), _one())] + _chrom("aa") + [_close()]),
    "crossed_nesting_attempt": lambda: (
        _chrom("aa") + [_open()] + [G.quad_turn(_one(), _one())]
        + _chrom("bb") + [_close()]),
}


@pytest.mark.parametrize("name", sorted(_MALFORMED))
def test_every_malformed_class_is_refused(name):
    """All five, and each one decided in a single forward pass — no second scan is owed
    even for the unclosed-opener case, because the frame stack already names every
    offender by its open block."""
    with pytest.raises(G.GenomeGroupError):
        G.genome_groups(_MALFORMED[name]())


def test_depth_overflow_is_refused_at_exactly_MAX_GROUP_DEPTH():
    """The cap is a compiled-in structural bound: at the cap it passes, one past it it
    raises. A cap that cannot be reached is not a measured bound."""
    deep = _chrom("aa")
    for i in range(G.MAX_GROUP_DEPTH):
        deep = G.genome_group(f"d{i}", deep, dim=_DIM)
    assert len(G.genome_groups(deep)) == G.MAX_GROUP_DEPTH, "at the cap: legal"
    with pytest.raises(G.GenomeGroupError, match="MAX_GROUP_DEPTH"):
        G.genome_group("over", deep, dim=_DIM)


def test_a_group_of_ONE_is_legal():
    """Banning arity 1 would be the same constraint error as banning arity 0, only in the
    opposite direction. A singleton container is a real thing to want to say."""
    g = G.genome_group("solo", _chrom("aa"), dim=_DIM)
    recs = G.genome_groups(g)
    assert len(recs) == 1 and recs[0]["arity"] == 1


def test_arity_counts_DIRECT_members_only():
    """A group holding one group that holds three chromosomes has arity 1, not 3."""
    inner = G.genome_group("in", _chrom("a") + _chrom("b") + _chrom("c"), dim=_DIM)
    outer = G.genome_group("out", inner, dim=_DIM)
    by_label = {r["label"]: r for r in G.genome_groups(outer)}
    assert by_label["in"]["arity"] == 3
    assert by_label["out"]["arity"] == 1


def test_records_are_emitted_on_POP_never_on_PUSH():
    """A record emitted at the opener would be a claim the walk has not yet earned — that
    opener might never close. Emission order is therefore by CLOSE position, which for
    nesting means innermost-first."""
    inner = G.genome_group("in", _chrom("a"), dim=_DIM)
    outer = G.genome_group("out", inner, dim=_DIM)
    labels = [r["label"] for r in G.genome_groups(outer)]
    assert labels == ["in", "out"], (
        "emission order must be by close position (innermost first), which is what "
        "emit-on-pop produces; emit-on-push would give ['out', 'in']"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 3. R4 — crossed nesting is UNREPRESENTABLE, not merely detected
# ═══════════════════════════════════════════════════════════════════════════

def test_crossed_nesting_cannot_be_SAVED(tmp_path):
    """THE FATAL THIS RULE REPAIRS. Before R3, a group opening inside one chromosome and
    closing inside the next SAVED, HASHED and ROUND-TRIPPED carrying two mutually
    inconsistent readings, with no error at any layer. The refusal must fire at the
    PERSISTENCE boundary too, not only in the in-memory walker — the in-memory half is
    the half the original design walked, and the store was where it failed."""
    crossed = _MALFORMED["crossed_nesting_attempt"]()
    with pytest.raises(G.GenomeGroupError):
        G.genome_save(crossed, tmp_path / "x", _one())
    assert not (tmp_path / "x" / "turns.bin").exists(), (
        "a refused save must leave no bytes behind"
    )


def test_a_group_can_never_open_inside_a_chromosome():
    """R1 restated as a property: after a `[`, no chromosome is open, so there is no
    chromosome for a group to be 'inside' of. Every legal strand's frame markers sit at
    unit boundaries by construction."""
    g = G.genome_group("sy", _chrom("aa") + _chrom("bb"), dim=_DIM)
    kinds = [G._cap_kind(hv) for hv in g]
    for i, k in enumerate(kinds):
        if k not in G._GROUP_MARKERS:
            continue
        if i + 1 < len(kinds):
            assert (kinds[i + 1] in G._CHROM_BOUNDARY_MARKERS
                    or kinds[i + 1] in G._GROUP_MARKERS), (
                f"block {i + 1} after a frame marker must open a unit, not continue one"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 4. THE SY14 CASE — sixteen units vs one fused unit that used to be sixteen
# ═══════════════════════════════════════════════════════════════════════════

def _sixteen():
    return [hv for i in range(16) for hv in _chrom(f"u{i:02d}", n_turns=1)]


def test_sixteen_units_and_one_fused_unit_are_BYTE_DISTINGUISHABLE(tmp_path):
    """The capability v20 exists to provide, stated as a discriminator.

    THREE readings of the same content must be three different objects:
      A  sixteen loose units          (no grouping — v19 could say this)
      B  sixteen units, grouped as one (v19 could NOT say this at all)
      C  one fused unit that used to be sixteen (v19's only way to say "one")

    Through v19 a caller wanting "one thing" had to collapse to C and lose the sixteen.
    The gate is that B is distinct from BOTH — if B collided with A the grouping would be
    unrecorded, and if it collided with C the members would be unrecoverable."""
    a = _sixteen()
    b = G.genome_group("sy", a, dim=_DIM)
    one = _one()
    fused = [G._pack_cap(G.CHROM_CAP_MARKER, "sy", _DIM)] + [
        hv for hv in a if G._cap_kind(hv) is None]

    da = G.genome_save(a, tmp_path / "a", one)
    db = G.genome_save(b, tmp_path / "b", one)
    dc = G.genome_save(fused, tmp_path / "c", one)

    shas = {da["body_sha256"], db["body_sha256"], dc["body_sha256"]}
    assert len(shas) == 3, "all three readings must be byte-distinguishable"

    # and B keeps BOTH facts, which is the whole point
    assert db["n_chromosomes"] == 16, "the sixteen survive"
    assert len(G.genome_groups(b)) == 1, "and so does the one"
    assert G.genome_groups(b)[0]["arity"] == 16
    # C lost the sixteen; A never had the one
    assert dc["n_chromosomes"] == 1
    assert G.genome_groups(a) == []
    # the CONTENT is the same in all three -- grouping and fusing are both container ops
    assert da["n_content"] == db["n_content"] == dc["n_content"] == 16


def test_the_sy14_discriminator_is_not_vacuous(tmp_path):
    """THE MUTATION. If the group markers were dropped from the body, B would collapse
    onto A — which is exactly the pre-v20 state, and exactly what this gate must catch."""
    a = _sixteen()
    b = G.genome_group("sy", a, dim=_DIM)
    mutant = [hv for hv in b if G._cap_kind(hv) not in G._GROUP_MARKERS]
    one = _one()
    da = G.genome_save(a, tmp_path / "a", one)
    dm = G.genome_save(mutant, tmp_path / "m", one)
    assert da["body_sha256"] == dm["body_sha256"], (
        "stripping the frame markers must reproduce the ungrouped body EXACTLY — if it "
        "does not, the grouping is leaking into bytes it should not touch"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 5. ZERO EXTRA BYTES — an object that never groups is byte-identical to v19
# ═══════════════════════════════════════════════════════════════════════════

def test_an_ungrouped_object_is_byte_identical_to_v19(tmp_path):
    """The v19 body bytes for this strand are a fixed, checkable value: v20 adds two
    markers to the VOCABULARY and no bytes to a body that does not use them.

    Held two ways, because either alone is weak: (a) the body equals the concatenated
    leaf blocks with nothing inserted, and (b) the region tiling is still exactly one
    region per chromosome, so the ``body_sha256`` chain has the same number of folds over
    the same spans it had at v19."""
    strand = _chrom("aa") + _chrom("bb") + _chrom("cc")
    one = _one()
    data = G.genome_save(strand, tmp_path / "g", one)
    body = (tmp_path / "g" / "turns.bin").read_bytes()

    # The on-disk body bit-packs data turns, so the comparison is against the DISK
    # encoding, not the in-memory leaf blocks -- comparing to the latter would be a test
    # of the packer rather than of v20.
    expect = b"".join(G._disk_block(blk, _DIM, G.ELEMENT_TYPE_KLEIN4)
                      for blk in G._leaf_blocks(strand))
    assert body == expect, "not one byte added"
    assert G.GROUP_OPEN_MARKER not in body and G.GROUP_CLOSE_MARKER not in body, (
        "an object that never groups must carry neither frame marker"
    )
    assert len(data["regions"]) == len(data["chromosomes"]) == 3, (
        "regions stay 1:1 with chromosomes when nothing groups"
    )
    for reg, chrom in zip(data["regions"], data["chromosomes"]):
        assert (reg["byte_offset"], reg["byte_len"]) == (
            chrom["byte_offset"], chrom["byte_len"])
    assert data["n_content"] == G._content_turns(data["n_turns"],
                                                 data["n_chromosomes"])


def test_regions_always_tile_the_body_exactly(tmp_path):
    """The property that made the region rework necessary. A frame block is a real body
    byte belonging to NO chromosome, so if regions had stayed 1:1 with chromosomes the
    tiling check would refuse the very first grouped genome."""
    one = _one()
    for name, strand in (
            ("flat", _chrom("aa") + _chrom("bb")),
            ("grouped", G.genome_group("sy", _chrom("aa") + _chrom("bb"), dim=_DIM)),
            ("nested", G.genome_group(
                "out", G.genome_group("in", _chrom("aa"), dim=_DIM) + _chrom("bb"),
                dim=_DIM)),
    ):
        data = G.genome_save(strand, tmp_path / name, one)
        body_len = (tmp_path / name / "turns.bin").stat().st_size
        expect = 0
        for r in data["regions"]:
            assert r["byte_offset"] == expect, f"{name}: regions must tile without a gap"
            expect += r["byte_len"]
        assert expect == body_len, f"{name}: regions must cover the whole body"
        # and the load path re-verifies the same tiling
        G.genome_load(tmp_path / name, coupling=one)


def test_n_content_survives_a_REGROUPING(tmp_path):
    """``n_content``'s entire job is to be the quantity a repartitioning leaves alone.
    Grouping is a container operation, so frame blocks must be subtracted exactly as
    boundary caps are — the general law is
    ``n_turns == n_chromosomes + n_group_blocks + n_content``, with no residual."""
    one = _one()
    flat = _chrom("aa") + _chrom("bb") + _chrom("cc")
    grouped = G.genome_group("sy", flat, dim=_DIM)
    nested = G.genome_group("outer",
                            G.genome_group("inner", _chrom("aa"), dim=_DIM)
                            + _chrom("bb") + _chrom("cc"), dim=_DIM)
    vals = []
    for name, strand in (("f", flat), ("g", grouped), ("n", nested)):
        d = G.genome_save(strand, tmp_path / name, one)
        n_groups = len(d["regions"]) - len(d["chromosomes"])
        assert d["n_turns"] == d["n_chromosomes"] + n_groups + d["n_content"], (
            "the decomposition must be EXACT, with no residual"
        )
        vals.append(d["n_content"])
        # both projections must agree -- a divergence here was measured and fixed at rc442
        assert G.genome_content(tmp_path / name, coupling=one)["n_content"] == d["n_content"]
    assert len(set(vals)) == 1, f"n_content moved under regrouping: {vals}"


# ═══════════════════════════════════════════════════════════════════════════
# 6. THE BREAK — a v19 reader cannot read a grouped body
# ═══════════════════════════════════════════════════════════════════════════

_V19_LEAF_WIDE = tuple(m for m in G._LEAF_WIDE_BLOCK_MARKERS
                       if m not in G._GROUP_MARKERS)


def test_a_v19_reader_refuses_a_grouped_body_at_the_frame_marker(tmp_path, monkeypatch):
    """CLEAN BREAK, no dual-format reader, no shim.

    The v19 reader is reconstructed exactly: the leaf-wide marker set WITHOUT the two
    frame markers. Given a grouped body it does not mis-parse, silently skip, or return a
    truncated strand — it fails on the first frame byte with 'unrecognised block kind
    byte 91'. Migration is a REWRITER op, not a reader branch."""
    one = _one()
    grouped = G.genome_group("sy", _chrom("aa") + _chrom("bb"), dim=_DIM)
    G.genome_save(grouped, tmp_path / "g", one)
    body = (tmp_path / "g" / "turns.bin").read_bytes()
    assert body[0] == G.GROUP_OPEN_MARKER, "this body's very first byte is the opener"

    monkeypatch.setattr(G, "_LEAF_WIDE_BLOCK_MARKERS", _V19_LEAF_WIDE)
    with pytest.raises(G.GenomeBoundingError, match="unrecognised block kind byte 91"):
        list(G._walk_region_blocks(body, _DIM, context="v19 reader"))


def test_the_v19_reader_still_reads_an_UNGROUPED_v20_body(tmp_path, monkeypatch):
    """THE OTHER HALF, and the one that makes the break precise rather than sweeping. The
    break is not 'v20 bodies are unreadable' — it is 'bodies that USE the new markers are'.
    An ungrouped v20 body is v19 bytes, and a v19 reader takes it."""
    one = _one()
    strand = _chrom("aa") + _chrom("bb")
    G.genome_save(strand, tmp_path / "g", one)
    body = (tmp_path / "g" / "turns.bin").read_bytes()
    monkeypatch.setattr(G, "_LEAF_WIDE_BLOCK_MARKERS", _V19_LEAF_WIDE)
    assert len(list(G._walk_region_blocks(body, _DIM, context="v19 reader"))) == len(strand)


# ═══════════════════════════════════════════════════════════════════════════
# 7. C ↔ Python differential over random nested strands
# ═══════════════════════════════════════════════════════════════════════════

def _lcg(seed):
    """A tiny deterministic integer generator — no stdlib random, no float."""
    state = seed
    while True:
        state = (1103515245 * state + 12345) % 2147483648
        yield state


def _random_nested(seed, n_units=6):
    """Build a RANDOM but always-well-formed nested strand: a bounded shuffle of
    'open a group', 'close it', 'add a chromosome' that never violates the grammar."""
    rng = _lcg(seed)
    out, depth, since_open, made = [], 0, [], 0
    for step in range(n_units * 3):
        r = next(rng) % 3
        if r == 0 and depth < 6:
            out.append(_open(f"g{step}"))
            since_open.append(0)
            depth += 1
        elif r == 1 and depth > 0 and since_open[-1] > 0:
            out.append(_close())
            since_open.pop()
            depth -= 1
            if since_open:
                since_open[-1] += 1
        else:
            out.extend(_chrom(f"c{step}", n_turns=1 + (next(rng) % 2)))
            made += 1
            if since_open:
                since_open[-1] += 1
    while depth > 0:                       # close whatever is still open
        if since_open[-1] == 0:            # never leave a childless group
            out.extend(_chrom(f"fill{depth}", n_turns=1))
            since_open[-1] += 1
        out.append(_close())
        since_open.pop()
        depth -= 1
        if since_open:
            since_open[-1] += 1
    return out if made else _chrom("only")


@pytest.mark.skipif(not _native.has_native_genome_group(),
                    reason="native group peers not built in this env")
@pytest.mark.parametrize("seed", [1, 7, 19, 42, 101, 256, 999, 4242])
def test_c_and_python_agree_on_random_nested_strands(seed):
    """CO-EQUAL PROJECTIONS. The C walker and the Python walker must return the same
    records — same labels, same indices, same depths, same arities — for the same bytes."""
    strand = _random_nested(seed)
    raw = _blocks(strand)
    py = G.genome_groups(strand)
    status, c = _native.genome_group_walk_c(raw, len(strand), _DIM)
    assert status == 0, f"C refused a strand Python accepted (seed {seed})"
    assert c == py, f"C/Python divergence at seed {seed}:\n C  = {c}\n py = {py}"


@pytest.mark.skipif(not _native.has_native_genome_group(),
                    reason="native group peers not built in this env")
@pytest.mark.parametrize("name", sorted(_MALFORMED))
def test_c_refuses_every_strand_python_refuses(name):
    """The refusals must be co-equal too. A projection that ACCEPTS what its peer refuses
    is the silent-wrong-answer class, which is worse than either answer alone."""
    strand = _MALFORMED[name]()
    raw = _blocks(strand)
    status, _recs = _native.genome_group_walk_c(raw, len(strand), _DIM)
    assert status != 0, f"C accepted the malformed '{name}' that Python refuses"
    with pytest.raises(G.GenomeGroupError):
        G.genome_groups(strand)


@pytest.mark.skipif(not _native.has_native_genome_group(),
                    reason="native group peers not built in this env")
def test_c_depth_overflow_returns_ERR_LIMIT_not_ERR_OVERFLOW():
    """rc404 defines SRMECH_ERR_LIMIT as 'a compiled-in structural cap; retrying is futile
    BY CONSTRUCTION' — this case verbatim. OVERFLOW would tell a caller its buffer was too
    small and send a grow-loop into futile doubling against a bound no buffer can move."""
    deep = _chrom("aa")
    for i in range(G.MAX_GROUP_DEPTH):
        deep = G.genome_group(f"d{i}", deep, dim=_DIM)
    over = ([_open("over")] + list(deep) + [_close()])
    status, _ = _native.genome_group_walk_c(_blocks(over), len(over), _DIM)
    assert status == 8, (
        f"expected SRMECH_ERR_LIMIT (8) for depth overflow, got {status}. "
        f"SRMECH_ERR_OVERFLOW (4) would be wrong: it means 'your buffer was too small'."
    )


@pytest.mark.skipif(not _native.has_native_genome_group(),
                    reason="native group peers not built in this env")
def test_c_and_python_mint_the_same_bytes():
    """The MINT is co-equal as well — a bare-C host writes a byte-identical group."""
    sub = _chrom("aa") + _chrom("bb")
    status, c_bytes = _native.genome_group_wrap_c(_blocks(sub), len(sub), _DIM, "sy")
    assert status == 0
    assert c_bytes == _blocks(G.genome_group("sy", sub, dim=_DIM))


@pytest.mark.skipif(not _native.has_native_genome_group(),
                    reason="native group peers not built in this env")
def test_the_differential_is_not_vacuous():
    """THE MUTATION. If the two walkers could not disagree, the differential above would
    be theatre. Perturb one byte of a well-formed strand and the C walker's answer must
    move — which proves the comparison has something to compare."""
    strand = G.genome_group("sy", _chrom("aa") + _chrom("bb"), dim=_DIM)
    raw = bytearray(_blocks(strand))
    status, before = _native.genome_group_walk_c(bytes(raw), len(strand), _DIM)
    assert status == 0 and before
    raw[1] = ord("Z")                       # change the opener's label
    status, after = _native.genome_group_walk_c(bytes(raw), len(strand), _DIM)
    assert status == 0
    assert after != before, (
        "a perturbed opener label must change the C walker's record, or the "
        "differential above is comparing something that cannot move"
    )
