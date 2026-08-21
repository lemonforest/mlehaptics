"""rc290 (§102 / F1259 / F1260) — the Klein-4 mint SPLIT BY REGIME + ONE-A14.

Two defects closed together, because they are the same defect at two levels.

**F1259 — the genome coupling was DRAWN, not DERIVED.** The slot held
``klein4_random(dim, seed=<magic int>)``: an undeclared draw from an undeclared
ensemble. ``klein4_from_one`` replaces it with ONE-A14, a declared function of
the ``One``'s three constructor integers. The win is NOT better numbers — the
two are statistically indistinguishable — it is that a derivable description
replaces an undeclared draw.

**F1260 — one op served four regimes with different correctness criteria.** A
``seed=`` parameter spanning both "magic number" and "content address" is what
let DRAWN and DERIVED be conflated in the first place, because a call site could
not be READ to find out which was meant. Four ops now; the regime is declared.

The three findings these tests exist to keep from being quietly undone:

1. **A coupling is a ROLE, not a representation.** ``quad_turn`` applies it as a
   uniform XOR and XOR-by-constant is a Hamming isometry, so a coupling
   *mathematically cannot* transmit structure into stored content. The 0.25
   floor and incompressibility are therefore the CORRECT targets.
2. **The (1,3,7,3) partition cannot survive as vector structure** — it is
   OPERATOR structure and the projection target is an operand. It enters as a
   period-14 sector MASK, well-defined at any D.
3. **D is free and 14-divisibility earns nothing** (falsifier F7 → FALSE).

Generating code for the measured figures: ``notes/rc290_one_a14_shipped_measure.py``.
"""
from __future__ import annotations

import json

import pytest

from srmech import _native
from srmech.math import hdc
from srmech.cascade.one import the_one

D = 64


def _theta_grid(count):
    """``count`` DISTINCT REDUCED rationals. Reduction is load-bearing: an
    unreduced grid emits (2,4) and (1,2) as different theta, which then look
    like projection COLLISIONS when they are the same input twice."""
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a
    seen, out, den = set(), [], 2
    while len(out) < count:
        for num in range(1, den):
            if gcd(num, den) != 1 or (num, den) in seen:
                continue
            seen.add((num, den))
            out.append((num, den))
            if len(out) >= count:
                break
        den += 1
    return out


def _mean_max_identical(vectors, dim):
    tot = pairs = ident = 0
    best = 0
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            m = hdc.klein4_match_count(vectors[i], vectors[j])
            tot += m
            pairs += 1
            best = m if m > best else best
            ident += 1 if m == dim else 0
    return tot / (pairs * dim), best / dim, ident


# ── the regime split: each op REFUSES the other regimes' inputs ────────────

def test_klein4_expand_is_the_deterministic_regime():
    """EXPAND: same (D, seed) -> same bytes, and the MT19937 stream is
    byte-for-byte the CPython ``random.Random(seed).randrange(4)`` sequence the
    pre-rc290 ``klein4_random(D, seed=…)`` produced. The rename must not have
    moved a single byte."""
    import random
    for seed in (0, 1, 255, 1080, 4242, -7, 2 ** 70):
        a = list(hdc.klein4_expand(D, seed))
        assert a == list(hdc.klein4_expand(D, seed))
        r = random.Random(seed)
        assert a == [r.randrange(4) for _ in range(D)], seed


def test_klein4_expand_refuses_non_integer_seeds():
    """The EXPAND regime takes an integer that already means something. Bytes
    belong to ``klein4_address``, a slot name to ``klein4_role`` — and the error
    says so, because the whole point of the split is that the wrong choice is
    hard to WRITE."""
    for bad in (b"cat", "cat", 1.5, None, True):
        with pytest.raises(TypeError) as exc:
            hdc.klein4_expand(D, bad)
        assert "klein4_address" in str(exc.value)
        assert "klein4_role" in str(exc.value)


def test_klein4_random_is_gone_entirely_rc292():
    """rc292 REMOVED the STOCHASTIC regime. No op, no shim, no alias.

    This test used to assert that ``klein4_random`` refused a ``seed=`` and
    honoured an explicit ``rng=``. That second assertion is what retired the
    op. rc290 removed ``seed=`` on the reasoning that a seed made an op named
    "random" silently deterministic — but it left ``rng=``, and a SEEDED
    generator through that door is exactly as reproducible. The old test
    asserted the reproducibility itself
    (``klein4_random(D, rng=Random(0))`` twice, equal) and called it correct
    behaviour, so the F1259 defect was not merely surviving, it was PINNED.

    A survey of real call sites found every one of them passing
    ``default_rng(<seed>)`` — i.e. the op whose documented correctness
    criterion was NON-REPRODUCIBILITY was, in practice, never used
    stochastically. An op whose declared regime does not match any of its use
    is not a regime; it is a defect. There is deliberately no replacement:
    a caller who wants an unpredictable Klein-4 vector draws their own bytes
    and composes ``klein4_encode_bytes``, which keeps the non-reproducibility
    visible at the call site and has C parity all the way down.
    """
    assert not hasattr(hdc, "klein4_random")
    assert "klein4_random" not in hdc.__all__
    # No silent re-export anywhere on the public surface.
    from srmech.introspect import tool_schema
    assert all(e.name != "srmech.math.hdc.klein4_random"
               for e in tool_schema.get_tool_schema().tools)
    # The documented replacement composition works and is genuinely per-run.
    import os
    a = hdc.klein4_encode_bytes(os.urandom(32), 4096)
    b = hdc.klein4_encode_bytes(os.urandom(32), 4096)
    assert list(a) != list(b)


def test_klein4_address_refuses_an_integer_seed():
    """ADDRESSED takes CONTENT. An int is the EXPAND regime, and passing one
    here was the exact confusion (``seed=sha256(content)``) that made a content
    address indistinguishable from a magic number at the call site."""
    with pytest.raises(TypeError) as exc:
        hdc.klein4_address(D, 42)            # type: ignore[arg-type]
    assert "klein4_expand" in str(exc.value)


def test_klein4_role_is_klein4_expand_over_the_token_fold():
    """ROLE is a declared composition, not a new kernel — value-identical to the
    pre-rc290 ``klein4_random(dim, seed=_cooc_token_seed(tok, base))`` that the
    co-occurrence fold and the HRR codebook used. Same bytes, declared regime."""
    for role, base in (("subject", 0), ("VAL:3/4", 11), ("ROLE:c0", 7)):
        assert list(hdc.klein4_role(D, role, base)) == \
            list(hdc.klein4_expand(D, hdc._cooc_token_seed(role, base)))


def test_klein4_role_distinct_names_are_near_orthogonal():
    """The ROLE criterion. Near-orthogonality is not merely acceptable here — it
    IS the functional requirement, because it is what stops one slot's binding
    being read out by another's key."""
    names = [f"slot{i}" for i in range(60)]
    vecs = [hdc.klein4_role(512, n) for n in names]
    mean, best, ident = _mean_max_identical(vecs, 512)
    assert ident == 0
    assert 0.20 < mean < 0.30, mean
    assert best < 0.40, best
    # `base` re-namespaces the SAME name to an independent codebook.
    assert list(hdc.klein4_role(D, "slot0", 0)) != list(hdc.klein4_role(D, "slot0", 9))


# ── F1260: high diffusion makes an ADDRESS and unmakes a REPRESENTATION ────

def test_address_hides_a_one_char_edit_and_encode_bytes_shows_it():
    """The teaching case. ``cat``/``cats`` is INVISIBLE to the address (it sits
    on its ``cat``/``dog`` control) and LOUD to the byte encoder. One property —
    SHA-256 avalanche — read against two opposite requirements. This is the
    whole reason the regimes are separate ops rather than a documented
    convention."""
    D2 = 8192
    a = hdc.klein4_address(D2, b"cat")
    b = hdc.klein4_address(D2, b"cats")
    c = hdc.klein4_address(D2, b"dog")
    edit = hdc.klein4_match_count(a, b) / D2
    control = hdc.klein4_match_count(a, c) / D2
    morph = hdc.klein4_match_count(hdc.klein4_encode_bytes(b"cat", D2),
                                   hdc.klein4_encode_bytes(b"cats", D2)) / D2
    assert abs(edit - control) < 0.03, (edit, control)   # edit invisible
    assert morph > 0.60, morph                            # edit loud
    assert morph > edit + 0.3


def test_address_is_identity_stable_and_accepts_str_and_empty():
    assert list(hdc.klein4_address(D, "cat")) == list(hdc.klein4_address(D, b"cat"))
    assert list(hdc.klein4_address(D, bytearray(b"cat"))) == \
        list(hdc.klein4_address(D, b"cat"))
    assert len(hdc.klein4_address(D, b"")) == D           # the empty address exists
    big = bytes(range(256)) * 4096                        # 1 MiB: no ceiling
    assert len(hdc.klein4_address(D, big)) == D


# ── the (1,3,7,3) sector frame ────────────────────────────────────────────

def test_sector_frame_is_period_14_at_every_D():
    """The partition enters as a MASK precisely so it is well-defined at any D
    — including every D NOT divisible by 14, which is every power of two."""
    expect = [1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3]   # C=2, H=4, O=8
    for dim in (1, 13, 14, 15, 28, 56, 64, 1000, 1024):
        f = list(hdc.klein4_sector_frame(dim))
        assert len(f) == dim
        assert f == [expect[j % 14] for j in range(dim)], dim


def test_sector_frame_is_statistically_inert_and_says_so():
    """HONEST DISCLOSURE, asserted rather than only documented. XOR-by-constant
    is a Hamming isometry, so masking CANNOT move a pairwise statistic. The
    frame is carried for legibility and attestation — if this test ever fails,
    the frame has stopped being a constant and the docstring has become false."""
    grid = _theta_grid(40)
    masked = [hdc.klein4_from_one(the_one(1, tn, td, 4), D) for tn, td in grid]
    frame = hdc.klein4_sector_frame(D)
    unmasked = [hdc.klein4_bind(v, frame) for v in masked]
    assert _mean_max_identical(masked, D) == _mean_max_identical(unmasked, D)


# ── ONE-A14 ───────────────────────────────────────────────────────────────

def test_one_a14_is_derivable_from_sigma_theta_terms_alone():
    """No stored bytes, no seed table, no label — the F1259 ask. Equal
    constructor integers give equal couplings; any difference in them gives a
    different coupling."""
    a = hdc.klein4_from_one(the_one(1, 1, 4, 24), D)
    assert list(a) == list(hdc.klein4_from_one(the_one(1, 1, 4, 24), D))
    for other in (the_one(-1, 1, 4, 24), the_one(1, 3, 4, 24), the_one(1, 1, 4, 20)):
        assert list(a) != list(hdc.klein4_from_one(other, D))


def test_one_a14_sits_at_the_floor_with_no_collisions():
    """F1 + F3, and the CORRECT target — not a defect. Design note: mean 0.2491,
    0 identical over 120 theta / 7140 pairs; the DRAWN incumbent it replaces:
    0.2498. The shipped op measures 0.2501. Statistically indistinguishable, by
    design: the gain is provenance, not numbers."""
    grid = _theta_grid(120)
    vecs = [hdc.klein4_from_one(the_one(1, tn, td, 4), D) for tn, td in grid]
    mean, best, ident = _mean_max_identical(vecs, D)
    assert ident == 0
    assert 0.24 < mean < 0.26, mean
    assert best < 0.55, best


def test_one_a14_holds_the_floor_when_theta_clusters_in_value():
    """F2 — the falsifier that REJECTED the base-4 digit-ladder candidate
    (ONE-D4 degraded 0.2747 -> 0.3336 -> 0.4477 because cos is continuous, so
    nearby theta share leading digits). A content address has no continuity in
    theta, which is exactly why it survives this row. Do not resurrect ONE-D4."""
    for den in (100, 1000, 100000):
        vecs = [hdc.klein4_from_one(the_one(1, 1 + k, den, 4), D)
                for k in range(40)]
        mean, _best, ident = _mean_max_identical(vecs, D)
        assert ident == 0
        assert mean < 0.30, (den, mean)


def test_one_a14_is_the_address_of_the_canonical_form_under_the_frame():
    """F4 — the frame is a FALSIFIABLE structural invariant: strip it and the
    raw Class-A expansion of the One's own canonical serialisation reappears
    exactly. This is what makes the (1,3,7,3) claim checkable rather than
    decorative."""
    one = the_one(1, 1, 4)
    stripped = hdc.klein4_bind(hdc.klein4_from_one(one, D),
                               hdc.klein4_sector_frame(D))
    preimage = json.dumps(one._to_jsonable(), sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
    assert list(stripped) == list(hdc.klein4_address(D, preimage))


def test_one_a14_preserves_intra_genome_geometry_exactly():
    """R3 — a THEOREM, recorded as such and never as a falsifier (it closes by
    construction). XOR-by-constant is a Hamming isometry, so the coupling never
    perturbs recall WITHIN one genome: sim(t1^c, t2^c) == sim(t1, t2) for any c.
    This is why a coupling cannot carry structure into stored content, and hence
    why the floor is the right target."""
    coupling = hdc.klein4_from_one(the_one(1, 1, 4), D)
    leaves = [hdc.klein4_expand(D, s) for s in range(12)]
    coupled = [hdc.klein4_bind(v, coupling) for v in leaves]
    for i in range(len(leaves)):
        for j in range(len(leaves)):
            assert hdc.klein4_match_count(leaves[i], leaves[j]) == \
                hdc.klein4_match_count(coupled[i], coupled[j])


def test_one_a14_D_divisible_by_14_earns_nothing():
    """F7 returns FALSE — recorded as a NULL RESULT, not omitted. 14 = 2*7 and 7
    never divides 2^n, so no power of two is ever divisible by 14; the question
    is whether that costs anything, and it does not. The reason is structural:
    the projection never TILES the partition into D positions."""
    grid = _theta_grid(40)
    for d14, p2 in ((56, 64), (112, 128), (224, 256)):
        m14 = _mean_max_identical(
            [hdc.klein4_from_one(the_one(1, tn, td, 4), d14) for tn, td in grid], d14)[0]
        m2 = _mean_max_identical(
            [hdc.klein4_from_one(the_one(1, tn, td, 4), p2) for tn, td in grid], p2)[0]
        assert abs(m14 - m2) < 0.01, (d14, p2, m14, m2)


def test_one_a14_rejects_a_non_One_operand():
    with pytest.raises(TypeError) as exc:
        hdc.klein4_from_one("not a One", D)
    assert ".sigma" in str(exc.value)


def test_one_a14_refuses_a_zero_theta_denominator_before_dispatch():
    """The C peer ASSERTS theta_den != 0, and an assert-enabled build would
    SIGABRT the host rather than raise. `the_one` rejects a zero denominator at
    construction, so this can only arrive from a duck-typed operand — but that
    is reachable, and rc289's lesson is that a reachable input which one
    projection answers and the other kills the process on is a parity break of
    the worst shape. Both projections must refuse it identically."""
    class _FakeOne:
        sigma, theta, terms = 1, (1, 0), 24
    with pytest.raises(ValueError):
        hdc.klein4_from_one(_FakeOne(), D)
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        with pytest.raises(ValueError):
            hdc.klein4_from_one(_FakeOne(), D)
    finally:
        _native.HAS_NATIVE = saved


# ── ADR-0009: BOTH coherency projections, byte-identical ──────────────────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library absent")
@pytest.mark.parametrize("dim", [1, 7, 13, 14, 15, 64, 65, 128, 1000])
def test_native_and_pure_projections_are_byte_identical(dim):
    """F5 / ADR-0009. Every rc290 op exists in BOTH projections and the two
    agree byte-for-byte — including at D not divisible by 14, and at content
    sizes far past any fixed buffer (the C peer folds content to a digest first
    precisely so it needs no arena and declines nothing)."""
    one = the_one(-1, 22, 7, 24)
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = True
        nat = (list(hdc.klein4_expand(dim, 4242)),
               list(hdc.klein4_role(dim, "subject", 11)),
               list(hdc.klein4_address(dim, b"cat")),
               list(hdc.klein4_address(dim, bytes(range(256)) * 40)),
               list(hdc.klein4_sector_frame(dim)),
               list(hdc.klein4_from_one(one, dim)))
        _native.HAS_NATIVE = False
        pure = (list(hdc.klein4_expand(dim, 4242)),
                list(hdc.klein4_role(dim, "subject", 11)),
                list(hdc.klein4_address(dim, b"cat")),
                list(hdc.klein4_address(dim, bytes(range(256)) * 40)),
                list(hdc.klein4_sector_frame(dim)),
                list(hdc.klein4_from_one(one, dim)))
    finally:
        _native.HAS_NATIVE = saved
    assert nat == pure


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library absent")
def test_native_declines_rather_than_truncates_a_bignum_theta():
    """The C wire is int64. A theta past it must fall to the pure path, never be
    silently truncated into a DIFFERENT coupling — a truncation here would make
    the two projections disagree while both reported success."""
    big = the_one(1, 1, 2 ** 70 + 3, 4)
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = True
        nat = list(hdc.klein4_from_one(big, D))
        _native.HAS_NATIVE = False
        pure = list(hdc.klein4_from_one(big, D))
    finally:
        _native.HAS_NATIVE = saved
    assert nat == pure


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library absent")
def test_the_renamed_c_symbol_is_present_and_the_old_one_is_gone():
    """rc290 REMOVED ``srmech_klein4_random`` and added ``srmech_klein4_expand``
    — the removal is what bumps ABI 7 -> 8. A stale library would otherwise pass
    every other check while the wrapper quietly ran its pure body."""
    lib = _native.LIB
    assert hasattr(lib, "srmech_klein4_expand")
    assert hasattr(lib, "srmech_klein4_address")
    assert hasattr(lib, "srmech_klein4_role")
    assert hasattr(lib, "srmech_klein4_sector_frame")
    assert hasattr(lib, "srmech_klein4_from_one")
    assert not hasattr(lib, "srmech_klein4_random")
    # ABI has since advanced past rc290's 8 (rc306 = 9, section_counts caller-arena;
    # rc307 = 10, fiedler_sparse ws_len unified to BYTES); this pins the CURRENT
    # value so a stale lib is still caught.
    assert _native.EXPECTED_ABI_VERSION == 21
    assert _native.NATIVE_ABI_VERSION == 21


# ── the genome slot rename ────────────────────────────────────────────────

def test_genome_takes_coupling_and_the_one_is_gone():
    """Two unrelated objects named ``the_one`` in one package had already misled
    a reader. With ONE-A14 the slot holds something DERIVED FROM the One but not
    the One, so the old name got MORE misleading, not less. No alias: a caller
    who passes ``the_one=`` must see a failure, not a silent success."""
    from srmech.biology import genome as G
    one = the_one(1, 1, 4)
    coupling = hdc.klein4_from_one(one, 64)
    leaves = [hdc.klein4_expand(64, s) for s in range(3)]
    strand = G.chromosome(leaves, coupling, label="c")
    assert [list(x) for x in G.recall(strand, coupling)] == [list(x) for x in leaves]
    with pytest.raises(TypeError):
        G.chromosome(leaves, the_one=coupling, label="c")   # type: ignore[call-arg]


def test_one_a14_works_as_a_genome_coupling_end_to_end():
    """The whole point: a genome whose coupling is a DECLARED FUNCTION of
    (sigma, theta, terms) rather than a magic integer — reproducible from the
    parameters alone, with no stored key."""
    from srmech.biology import genome as G
    leaves = [hdc.klein4_expand(64, s) for s in range(5)]
    c1 = hdc.klein4_from_one(the_one(1, 1, 4), 64)
    strand = G.chromosome(leaves, c1, label="astronomy")
    # Rebuilt from the parameters — no stored bytes anywhere.
    c2 = hdc.klein4_from_one(the_one(1, 1, 4), 64)
    assert [list(x) for x in G.recall(strand, c2)] == [list(x) for x in leaves]
    # A DIFFERENT One does NOT read it (cross-store namespace isolation, the
    # only thing near-orthogonality actually buys — R4).
    wrong = hdc.klein4_from_one(the_one(1, 3, 4), 64)
    got = [list(x) for x in G.recall(strand, wrong)]
    assert got != [list(x) for x in leaves]
