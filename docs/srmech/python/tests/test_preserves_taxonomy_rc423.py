"""preserves — the TAXONOMY, and the hold LIFTED (rc423, `#T1113`).

THE HOLD, AND WHY IT HAD TO BE ADJUDICATED RATHER THAN RENEWED
==============================================================
``ToolEntry.preserves`` shipped at rc305 alongside ``composes``, and was put
on an explicit HOLD. ADR-0013 §1.7.1 records it as *"2 / 559, deliberately
held pending a taxonomy"*, and ADR-0012 §6.1 gives the reason verbatim:

    *"`composes` 9/559; `preserves` still 2/559 and deliberately so — it is a
    DIFFERENT feature (rc305 checks `composes` for registry membership and
    `preserves` only for non-emptiness), and any floor on it is satisfiable at
    scale with zero per-op information, so it gets a declared taxonomy before
    it gets rows."*

**The hold LEAKED.** It went 2 -> 13 anyway (21 invariant strings), because
nothing enforced it — a hold with no instrument is a comment, and rc419 and
rc422 both added rows in good faith without meeting one. That is not a
failure of those rcs. It is the same defect this rc fixes on the ``composes``
side: a property nothing can measure does not hold, it just goes unobserved.

So the 13 were read, and the finding is that they are **unclassified, not
wrong**. Every one is a genuine INVARIANT claim. More usefully, a taxonomy is
already implicit in them and it closes: all 21 strings classify below with no
residue and no kind invented to catch a stray. A taxonomy derived from the
rows the tree actually wrote is worth more than one designed in advance, and
that is the benefit of having adjudicated late rather than never.

THE CALL: THE HOLD IS LIFTED
============================
The hold's stated blocker was a missing taxonomy. The taxonomy is below, it
is DECLARED (each kind carries a definition and a verifiability class), and
it is ENFORCED — an unclassified ``preserves`` string now fails
:func:`test_every_shipped_invariant_is_classified` at strict zero. The
specific fear ("satisfiable at scale with zero per-op information") is
answered structurally rather than by promise: a row must now name what KIND
of guarantee it makes, and the kind constrains what the sentence has to say.
A contentless string has no kind to take.

**What is deliberately NOT done in this rc, and is not a hidden deferral:**
``preserves`` is NOT seeded broadly here. Lifting the hold makes population
legitimate; it does not make it automatic, and doing both in one rc would
mean writing hundreds of invariant claims under a taxonomy that had existed
for minutes. The population pass is the follow-on, and it now has a rule to
follow.

**What the taxonomy CREATES, stated plainly so it is not mistaken for done:**
eight of the ten kinds are marked ``EXECUTABLE`` — a machine could run them.
Nothing in this rc runs them. That is a NEW obligation created by classifying
the rows, not a survival of the OLD hold, and conflating the two would be how
a discharged hold silently renews itself. The honest status is: **population
unblocked, execution owed.**

THE TAXONOMY IS DERIVED, AND ITS COMPLETENESS CLAIM IS BOUNDED
==============================================================
Ten kinds over 21 strings. Every kind is USED — a taxonomy carrying an unused
kind is speculation, and :func:`test_no_kind_is_aspirational` refuses one.
But 21 strings is a small corpus and this file does not claim the ten are
exhaustive over invariants srmech has not written yet. Adding a kind is a
REVIEWED act (add it to :data:`KINDS` with its definition and verifiability
class, in the same commit as the row that needs it) — the same contract
``test_composes_grain_rc412.py::ROSTER`` sets for the other field.

numpy-free; stdlib only.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from composes_derive import SCHEMA  # noqa: E402


# ──────────────────────────────────────────────────────────────────────
# THE KINDS. Each is (definition, verifiability class).
#
# VERIFIABILITY is the field that makes this taxonomy do work rather than
# just sort things. It answers "could an instrument ever check a row of this
# kind?", which is what decides whether a `preserves` string is a testable
# guarantee or a note:
#
#   EXECUTABLE  — a machine can run the op and check the claim directly.
#   STRUCTURAL  — checkable, but against the registry / source rather than by
#                 executing the op.
#   PROSE       — a real guarantee no instrument can confirm from the op
#                 alone; it bounds INTERPRETATION rather than values.
#
# ⚠️ A kind is added by REVIEW, in the same commit as the row needing it.
# Never add one to make a red row pass — an unclassifiable string is evidence
# that the string is vague, which is exactly what the hold feared.
# ──────────────────────────────────────────────────────────────────────
KINDS: Dict[str, Tuple[str, str]] = {
    "ALGEBRAIC": (
        "a structural property of the returned mathematical object — "
        "closure, involution, group structure, equivariance/intertwining, or "
        "invariance under a group action",
        "EXECUTABLE"),
    "ROUND_TRIP": (
        "a named inverse op recovers the input exactly",
        "EXECUTABLE"),
    "EXACTNESS": (
        "no silent precision loss — an exact integer or rational is retained "
        "rather than reduced away or rounded",
        "EXECUTABLE"),
    "HONEST_NULL": (
        "the op reports ABSENCE rather than fabricating a value it cannot "
        "justify (returns None / omits a field instead of guessing)",
        "EXECUTABLE"),
    "PURITY": (
        "no side effects — the op does not run other ops and does not mutate "
        "shared state",
        "EXECUTABLE"),
    "IDEMPOTENCE": (
        "applying the op a second time changes nothing — f(f(x)) == f(x), "
        "including the case where the repeat must not re-run a side effect "
        "the first call already performed",
        "EXECUTABLE"),
    "IMMUTABILITY": (
        "a value already returned is unaffected by later state changes",
        "EXECUTABLE"),
    "DESIGN_CONTRACT": (
        "a caller-facing precedence, forwarding, scope-bound or iff "
        "condition — what the op promises about HOW it treats its inputs",
        "EXECUTABLE"),
    "CROSS_CHECK": (
        "agreement with another shipped op, or referential integrity into "
        "the registry — including non-circularity (a quantity derived "
        "independently rather than by definition) and measured negative "
        "controls",
        "STRUCTURAL"),
    "IMPLEMENTATION_DISCIPLINE": (
        "a claim about HOW the code is written rather than about its values "
        "(numpy-free, no abs()) — enforced by other gates, never by running "
        "this op",
        "STRUCTURAL"),
}

#: ⚠️ ``PROSE`` currently has ZERO members, and that is a RESULT rather than an
#: oversight — it says the 21 shipped invariants are, every one of them,
#: checkable in principle. It stays declared because the honest answer to "can
#: an instrument confirm this?" is sometimes no, and a taxonomy with no way to
#: say so would push an unverifiable claim into a verifiable-looking bucket.
#: Note the asymmetry with :func:`test_no_kind_is_aspirational`, which DOES
#: refuse an unused kind: a KIND is a claim that the corpus contains such a
#: thing, whereas a verifiability class is one of the possible ANSWERS to a
#: question asked of every kind. An unused answer is a measurement; an unused
#: kind is a guess.
VERIFIABILITY_CLASSES = ("EXECUTABLE", "STRUCTURAL", "PROSE")


# ──────────────────────────────────────────────────────────────────────
# THE CLASSIFICATION — all 21 shipped invariant strings, keyed by the FULL
# string on purpose.
#
# Keying by the whole sentence (rather than by op + index) means EDITING an
# invariant invalidates its classification and forces re-review, which is the
# wanted behaviour: a reworded guarantee may be a different guarantee. A
# positional key would silently carry the old kind onto new words.
# ──────────────────────────────────────────────────────────────────────
CLASSIFIED: Dict[str, Tuple[str, ...]] = {
    # ── srmech.biology.genome.cwf_consistency_mod2
    'Wr is computed from geometry (discrete_writhe), never defined as Lk-Tw — a real independent check':
        ('CROSS_CHECK',),
    'mod-2 only: Q8 pins Lk to its center-parity, not the unbounded integer linking number':
        ('DESIGN_CONTRACT',),
    'no-embedding path returns only the intrinsic mod-2 Lk; no Wr is fabricated':
        ('HONEST_NULL',),
    # ── srmech.biology.genome.genome_from_graph
    "byte-exact per-community round-trip: kernel_to_graph on any chromosome (with its n_syms) recovers that community's induced sub-graph exactly (§44 interior-centromere skip-on-read)":
        ('ROUND_TRIP',),
    "measured {nuclear, plasmid} counts equal genome_partition's classification":
        ('CROSS_CHECK',),
    'numpy-free; no abs() — sign-handling stays Class-K pin-slot + Class-C':
        ('IMPLEMENTATION_DISCIPLINE',),
    # ── the rc460 srmech.math.weight_lattice triple. ONE sentence across
    # three ops, the shared-TEXT discipline the codec note below states.
    # It is deliberately NOT the sibling string above: the added "exact ℤ"
    # clause is a SECOND guarantee of a different KIND, not a rewording.
    # The weight-lattice stratum's whole carrier claim is that Racah–Speiser
    # and Freudenthal stay in the integers end to end — the Gram matrix is
    # carried 3-SCALED precisely so the recursion never leaves ℤ, and every
    # division is a guarded `_exact_div` that RAISES on a remainder rather
    # than rounding. That is EXACTNESS ("an exact integer is retained rather
    # than reduced away or rounded"), and it is executable, where the
    # numpy-free / no-abs() half is structural. Classifying it as one kind
    # would drop the half the rc exists to guarantee.
    'numpy-free; exact ℤ; no abs() — sign-handling stays Class-K pin-slot + Class-C':
        ('IMPLEMENTATION_DISCIPLINE', 'EXACTNESS'),
    # ── the four LOSSLESS codecs registered at rc425 (`#T1112`):
    # huffman / arithmetic_coding / lz77 / rle. ONE sentence across four ops,
    # deliberately: keying the taxonomy by the whole string makes reuse the
    # cheap path and rewording the reviewed one, so a shared guarantee should
    # be shared TEXT rather than four near-identical sentences that would each
    # need classifying and could each drift apart. The "together with the
    # side-table" clause is load-bearing rather than hedging -- three of the
    # four genuinely cannot decode without what the encoder returned (huffman
    # needs codes + bit_length, arithmetic_coding needs freq + length), and a
    # round-trip claim that quietly omitted that would be false as written.
    'lossless: decoding an encoded payload together with the side-table the encoder returned reproduces the input exactly':
        ('ROUND_TRIP',),
    # ── srmech.math.covering.center_lift
    'cover_lift is the exact integer sum regardless of center_order — the cover datum is never reduced away':
        ('EXACTNESS',),
    'shadow_determines_lift is True iff center_order == 0':
        ('DESIGN_CONTRACT',),
    # ── srmech.math.covering.center_parity
    'orientation-blind: center_parity(w) == center_parity(-w)':
        ('ALGEBRAIC',),
    # ── srmech.math.covering.covering_catalog
    'every shipped_ops entry in a reached row is a live registered op path — a row cannot outlive the op it names':
        ('CROSS_CHECK',),
    # ── srmech.math.covering.lift_fibre
    'determined is True iff the fibre has exactly one element':
        ('DESIGN_CONTRACT',),
    # ── srmech.math.covering.linking_number_cwf
    'the exact rational sum is preserved even when non-integral — linking_number is None rather than rounded':
        ('EXACTNESS', 'HONEST_NULL'),
    # ── srmech.physics.qm.triality.spin8_center
    'the four scalar triples close under componentwise product and are all involutions — a Klein four-group, checked not assumed':
        ('ALGEBRAIC',),
    'each non-identity central element acts trivially on exactly one of {8v, 8s, 8c}':
        ('ALGEBRAIC',),
    # ── srmech.physics.qm.triality.triality_rep_dictionary
    'the derived bijection intertwines BOTH shipped generator pairs — the order-3 cycle and the order-2 transposition':
        ('ALGEBRAIC',),
    'the two order-2-for-order-3 controls return 0 and the identity-for-cycle control returns 6':
        ('CROSS_CHECK',),
    # ── srmech.signal_processing.cascade_dispatcher.dispatch
    'path= is honoured unconditionally — an explicit side is never overridden by the cascade hint or by the class default':
        ('DESIGN_CONTRACT',),
    'arguments are forwarded verbatim; D is injected only into implementations whose signature accepts it':
        ('DESIGN_CONTRACT',),
    # ── srmech.signal_processing.cascade_dispatcher.end_cascade
    'idempotent: flushing an already-closed context does not re-run the flush':
        ('IDEMPOTENCE',),
    # ── srmech.signal_processing.cascade_dispatcher.resolve_path
    'pure: resolve_path never runs the op and never mutates the registry or the cascade stack':
        ('PURITY',),
    # ── srmech.signal_processing.path_registry.registered_ops
    'an immutable snapshot — a later registration does not change a tuple already returned':
        ('IMMUTABILITY',),
    # ── rc424 (`#T1113`) — the music RELATIONS family + the MUSIC DOA
    # registration. Seven ops, seven invariants, classified AS WRITTEN rather
    # than back-filled: rc423's whole point was that the next row must arrive
    # already classified.
    # ── srmech.music.just_limit
    'no silent precision loss — the ratio is reduced and factored exactly, and float input raises rather than being coerced':
        ('EXACTNESS',),
    # ── srmech.music.comma_of_chain
    'derived, never tabulated: the comma is computed from the generator chain, so no named constant is stored anywhere in the op':
        ('IMPLEMENTATION_DISCIPLINE',),
    # ── srmech.music.tempers_out
    'no logarithm and no tolerance: the patent val is decided by exact integer comparison, so the same input always yields the same val':
        ('EXACTNESS',),
    # ── srmech.music.interval_vector
    'input order and duplication are irrelevant: the vector depends only on the SET of pitch classes mod 12':
        ('DESIGN_CONTRACT',),
    # ── srmech.music.normal_order
    'a caller-facing requirement, not a default: the convention must be named on every call, and an unknown one raises':
        ('DESIGN_CONTRACT',),
    # ── srmech.music.prime_form
    # ALGEBRAIC, not DESIGN_CONTRACT: the kind's own wording names "invariance
    # under a group action", and Tn/TnI IS the group whose orbit a set class is.
    'transposition- and inversion-invariant: every member of a set class returns the same prime form under a given convention':
        ('ALGEBRAIC',),
    # ── srmech.signal_processing.music_doa
    'numpy-free and abs()-free: |z|**2 is computed as re**2 + im**2 through the native Mat carrier':
        ('IMPLEMENTATION_DISCIPLINE',),
}


def _shipped() -> Dict[str, Tuple[str, ...]]:
    """``op name -> its preserves tuple``, live from the registry."""
    return {t.name: tuple(t.preserves) for t in SCHEMA.tools if t.preserves}


# ──────────────────────────────────────────────────────────────────────
# The enforcement. This is what turns the hold from a comment into a rule.
# ──────────────────────────────────────────────────────────────────────


def test_every_shipped_invariant_is_classified() -> None:
    """STRICT ZERO. Every ``preserves`` string in the registry carries a kind.

    This is the clause that discharges the hold. The hold existed because
    ``preserves`` had no checker beyond "is a non-empty string" (rc305:147),
    so a row could say anything at all. Now it must say something that fits a
    declared kind, and a new row that fits none is a red — which is the
    review the hold was asking for, applied at the moment the row is written
    rather than never.
    """
    unclassified: Dict[str, list] = {}
    for name, invariants in sorted(_shipped().items()):
        missing = [s for s in invariants if s not in CLASSIFIED]
        if missing:
            unclassified[name] = missing
    assert not unclassified, (
        f"{sum(len(v) for v in unclassified.values())} preserves string(s) "
        f"carry no taxonomy kind: {unclassified}. Classify each one in "
        f"CLASSIFIED above — if none of the ten kinds fits, that is evidence "
        f"the string is vague, and the fix is usually to sharpen the "
        f"invariant rather than to invent a kind for it.")


def test_every_classification_names_a_declared_kind() -> None:
    """A kind used but not declared would carry no definition and no
    verifiability class, which is the whole content of the taxonomy."""
    for text, kinds in CLASSIFIED.items():
        assert kinds, f"empty kind tuple for: {text[:60]}"
        for kind in kinds:
            assert kind in KINDS, (
                f"undeclared kind {kind!r} on: {text[:60]}...")


def test_every_kind_declares_a_definition_and_verifiability_class() -> None:
    """A kind is (definition, verifiability). Both are load-bearing: the
    definition is what stops two authors sorting the same claim differently,
    and the verifiability class is what says whether a gate could ever exist.
    """
    for kind, (definition, verifiability) in KINDS.items():
        assert definition and len(definition) > 30, (
            f"{kind}: the definition is too thin to sort by")
        assert verifiability in VERIFIABILITY_CLASSES, (
            f"{kind}: unknown verifiability class {verifiability!r}")


def test_no_kind_is_aspirational() -> None:
    """⚠️ NON-VACUITY. Every declared kind is actually USED.

    A taxonomy is cheap to over-build, and an unused kind is a category
    nobody has met — speculation shipped as structure. The corpus is what
    justifies the ten, so the ten may not outrun the corpus.
    """
    used = {k for kinds in CLASSIFIED.values() for k in kinds}
    unused = sorted(set(KINDS) - used)
    assert not unused, (
        f"declared but never used: {unused}. Either classify a row under it "
        f"or delete the kind — a taxonomy entry with no instance is a guess.")


def test_the_classification_has_no_dead_rows() -> None:
    """The reverse drift: a classified string no op ships any more.

    Left alone, these accumulate and make the classification look larger and
    better-maintained than the population it describes.
    """
    live = {s for inv in _shipped().values() for s in inv}
    dead = sorted(s for s in CLASSIFIED if s not in live)
    assert not dead, (
        f"{len(dead)} classified invariant(s) are no longer shipped by any "
        f"op: {[s[:70] for s in dead]}. Remove them — a classification of "
        f"strings the registry does not carry describes nothing.")


def test_the_corpus_is_not_empty() -> None:
    """GUARDS THE GUARD. Every clause above sweeps the shipped set, and a
    strict-zero sweep over an empty set passes."""
    shipped = _shipped()
    assert len(shipped) >= 13, (
        f"only {len(shipped)} ops carry preserves; the taxonomy clauses are "
        f"near-vacuous. The hold was lifted against a 13-op / 21-string "
        f"corpus and this is the floor that says so.")
    total = sum(len(v) for v in shipped.values())
    assert total >= 21, f"only {total} invariant strings shipped"


def test_the_population_is_stated() -> None:
    """ADR-0012 §12: declaring an arc complete requires STATING the
    population. Printed, never a failure — the number is the point.

    Note what this says and does not say. ``preserves`` is 13/605 and rc423
    does not move it; what rc423 moved is that the 13 are now CLASSIFIED and
    the next row must be. Reporting the ratio without that distinction would
    be the "capstone language" ADR-0012 §12 warns about.
    """
    shipped = _shipped()
    total_strings = sum(len(v) for v in shipped.values())
    by_kind: Dict[str, int] = {}
    for kinds in CLASSIFIED.values():
        for k in kinds:
            by_kind[k] = by_kind.get(k, 0) + 1
    executable = sum(n for k, n in by_kind.items() if KINDS[k][1] == "EXECUTABLE")
    print(f"\n[rc423] preserves population: {len(shipped)} / "
          f"{len(SCHEMA.tools)} ops, {total_strings} invariant strings, "
          f"100% classified across {len(KINDS)} kinds")
    print(f"[rc423] by kind: {dict(sorted(by_kind.items()))}")
    print(f"[rc423] {executable} of {total_strings} strings are of an "
          f"EXECUTABLE kind — NONE is executed yet. Population unblocked, "
          f"execution owed.\n")
    assert True
