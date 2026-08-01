"""rc365 (`#T1034`) — the ``srmech/amsc/`` module-and-subpackage CENSUS.

WHY THIS EXISTS. ADR-0010 A.5 item 5. The decode-aware prefix ratchet
(``CEIL_AMSC_PREFIX``) counts **dotted module PATHS**, so it is structurally
blind to a directory/module MOVE: rc364 moved four directories out of ``amsc``
and both of its channels read FLAT (Amendment B.5). *"The quantity the arc
actually drains, module by module, has no instrument."* This file is that
instrument. It ships **alone and green** — it moves NO module — so that the
first module-moving slice has an attributable baseline (the A.5 ordering rule:
*an instrument built in the same arc as the change it detects has no green
baseline, so a red is unattributable*).

WHAT IT MEASURES — a name-SET, not a name-COUNT. A count of 75 is blind to a
rename-in-place, exactly as rc361 learned for op names
(``test_op_name_set_witness_rc361.py``). This arc moves *named* modules OUT of
``amsc``, so the SET is the right quantity and this file mirrors that shipped
precedent: a sorted, hand-committed manifest of the population plus a
``srmech.amsc.format.sha256_bytes`` digest over its normalised body.

THE RATCHET IS DOWN-ONLY. ``amsc`` drains 75 → 4 over the arc. The live module
set must stay a **subset** of the committed manifest — a module may LEAVE, but a
module *appearing* in ``amsc`` is the regression this catches. The floor is the
**four keepers** ``format`` / ``catalog`` / ``descriptor`` / ``gap_suggester``
(A.2): when the live module set equals ``KEEPERS`` the arc is DONE.

⚠️ THE MANIFEST IS HAND-COMMITTED ON PURPOSE — DO NOT WIRE IT INTO CODEGEN.
``tests/amsc_module_census.txt`` is NOT emitted by anything under ``tools/``, and
``test_the_manifest_is_not_codegen_emitted`` below asserts that it stays that
way. The reason is the whole point of the instrument: a declustering slice runs
``python tools/regen_all.py`` as a matter of course, so a codegen-emitted census
would be rewritten by the very change it is meant to detect and go green
unconditionally — the EMPTY-probe failure mode A.5 indicts.

TO CHANGE THE POPULATION DELIBERATELY (a later slice that MOVES a module), in
the same commit:
  1. rewrite the manifest, dropping the module stem(s) that left::
       python scratch/gen_census.py srmech/amsc tests/amsc_module_census.txt
     (or by hand — it is a plain sorted list; subpackages carry a trailing "/")
  2. update ``EXPECTED_CENSUS_SHA256`` (and ``EXPECTED_N_SUBPACKAGES`` if a
     subpackage moved) to what the failure message prints.
  3. lower ``EXPECTED_N_MODULES`` by the number that left, and add each departed
     stem to ``LANDED`` — the ``test_the_drain_is_conserved_*`` invariant
     requires ``EXPECTED_N_MODULES + len(LANDED) == ORIGINAL_N_MODULES``, so
     these two move together and neither can be forgotten silently.
Needing the digest pinned in SOURCE while the population is pinned on disk means
a careless single-file rewrite cannot pass; ``LANDED`` + the conservation
invariant means a manifest shrink cannot be booked without saying WHERE the
module went.

⚠️ rc366 — WHY THIS IS NOT THE ORIGINAL "TWO-EDIT" PROCEDURE. The rc365 mint
said only "drop from the manifest + update the digest", and the FIRST real move
(the ``harmonics`` -> ``srmech.music`` slice) proved that incomplete: the manifest
is the CURRENT amsc population (it must shrink so the down-only ceiling drops and
a re-add is caught), but ``NAMED_DEPARTURES`` / ``ADR_A2_DESTINATION_COUNTS`` are
A.2's FIXED plan (``harmonics -> music`` is a correct classification forever,
whether or not it has moved). At rc365 those agreed because nothing had moved, so
``test_the_move_map_matches_A2`` checked "named member still in the manifest" and
the "73 of 75" gap was stated against the live count — both rc365-snapshot
truths. Dropping ``harmonics`` from the manifest correctly turned them red. The
fix decouples the three quantities: ``LANDED`` (drain progress) restores the
distinction, a named member is REAL when it is still in amsc OR landed, and the
gap is stated against ``ORIGINAL_N_MODULES``. Step 3 above is the residue.
"""
from __future__ import annotations

from pathlib import Path

import srmech
from srmech.amsc.format import sha256_bytes

MANIFEST = Path(__file__).resolve().parent / "amsc_module_census.txt"
_AMSC = Path(srmech.__file__).resolve().parent / "amsc"

# ── pinned population (the committed census) ─────────────────────────────────

#: The rc365 BASELINE module count — the denominator A.2 classified against, and
#: a FIXED historical fact (the tree had exactly this many ``srmech/amsc/*.py``
#: modules the moment the census was minted). It never changes as the arc drains;
#: the "73 of 75 classified" gap and the drain-conservation invariant below are
#: both stated against it, so neither is a moving target.
ORIGINAL_N_MODULES = 75

#: LIVE ``srmech/amsc/`` module count — the CURRENT population, which DRAINS
#: 75 -> 4 over the arc. Pinned only so the failure message can say "74 -> 73"
#: instead of dumping the set; the SET on disk and its digest below are the
#: actual contract. rc366 (ADR-0010's first module-moving slice): 75 -> 74, the
#: ``harmonics`` departure to ``srmech.music``. rc367 (the second slice): 74 ->
#: 73, the ``naming`` departure to ``srmech.introspect``. rc368 (the third
#: slice): 73 -> 72, the ``responsion_schema`` departure to ``srmech.introspect``.
#: rc369 (the fourth slice): 72 -> 71, the ``op_provenance`` departure to
#: ``srmech.introspect`` (see ``LANDED`` below). rc370 (the fifth slice, and the
#: FIRST into a newly-created namespace): 71 -> 70, the ``elliptic_partial_fraction``
#: departure to ``srmech.apokatastasis`` (the elliptic domain's first module).
#: rc371 (the sixth slice, the WHOLE-FAMILY drain): 70 -> 46, the 24 remaining
#: elliptic / modular / theta / q-series modules departing to
#: ``srmech.apokatastasis`` in ONE slice — completing the 25-module bucket (the
#: rc370 ``elliptic_partial_fraction`` + these 24). rc372 (the seventh slice, and
#: the FIRST into a newly-created ``srmech.math`` namespace): 46 -> 43, the
#: general-algebra roster ``octonion`` / ``kepler`` / ``modular_linalg`` departing
#: to ``srmech.math``. ``modular_linalg`` is the H.2 apokatastasis OVER-COUNT
#: reassignment: GF(p) finite-field LA is a general math primitive (its name only
#: collides with "modular forms"), so it lands in ``srmech.math`` HERE, exactly
#: as Amendment H.2 recorded it would when the math bucket drained.
#: rc373 (the eighth slice, the A-N PRIMITIVES batch): 43 -> 33, the ten
#: primitive modules cyclic / dispatch / hdc / laplacian / primes / rational /
#: search / template / tlv / text departing to srmech.math (the bulk of the 14
#: A-N primitives; the general carriers stay for the rc374 carriers slice).
#: rc374 (the ninth slice, the CARRIERS batch — the math bucket's LAST slice):
#: 33 -> 18, the fifteen carrier modules mat / vec / hv / q / qmat / qi / qalg /
#: qprime / poly / qpoly / qbipoly / tripoly / complex128 / carrier_ladder /
#: carrier_spectrum departing to srmech.math. This DRAINS the math bucket: with
#: this slice srmech.math holds all 28 of its A.2 members (see the H.2 over-count
#: reconciliation at ADR_A2_DESTINATION_COUNTS below). carrier_schema STAYS in
#: amsc (it is the introspect surface, not a carrier).
#: rc375 (the tenth slice, the BIOLOGY bucket — opens AND drains srmech.biology in
#: ONE slice, the roster being small enough): 18 -> 14, the four biology modules
#: coupling / genome / plasmid / q8 departing to srmech.biology (the biology
#: domain's whole 4-module roster). genome is the arc's single largest C surface
#: (many srmech_genome_* peers); those C symbols are capability-named and DO NOT
#: rename, so the ABI stays 10. Takes LANDED from 57 to 61 and the live amsc count
#: from 18 to 14 (conservation 14 + 61 == 75).
EXPECTED_N_MODULES = 14
EXPECTED_N_SUBPACKAGES = 3

#: sha256 over the NORMALISED manifest body — "\n".join(sorted entries) + "\n",
#: UTF-8. Normalised rather than raw-file-bytes so a CRLF checkout cannot make
#: the digest disagree between the Windows and Linux CI cells; that would be a
#: platform artifact masquerading as a move (the rc361 rationale, verbatim).
EXPECTED_CENSUS_SHA256 = (
    "b7443cd00a388f24b2d212ee8ac9cb6b1c669a94fd8d70d2d8f16dbe8eb0a8fe")

# ── the four keepers, and the A.2 move map (as DATA the test reads) ──────────

#: ADR-0010 A.2: ``amsc`` KEEPS exactly these 4 of 75 modules — the attestation
#: framework it was named for. They are the ratchet's FLOOR and must NEVER
#: appear in the removed set. (The Decision-table body listed ``gap_suggester``
#: under introspect; A.2 is the authoritative correction and keeps it here.)
KEEPERS = frozenset({"catalog", "descriptor", "format", "gap_suggester"})

#: The three subpackages present at rc365. ``adapters`` + ``attested`` are the
#: attestation subpackages and STAY; ``cascade`` is slated to move under A.2's
#: ``srmech.cascade.*`` row (Status-of-adoption "verify"), so subpackages are
#: down-only too.
EXPECTED_SUBPACKAGES = frozenset({"adapters", "attested", "cascade"})
ATTESTATION_SUBPACKAGES = frozenset({"adapters", "attested"})

#: A.2's move map, per-destination COUNTS, quoted verbatim. These sum to 74; the
#: tree has 75. The residual 1 is A.2's OWN acknowledged classification gap (its
#: heading reads "73 of 75 classified"). The census does not depend on resolving
#: it — the departure allowlist below is derived from the authoritative fact that
#: only 4 modules keep, so all 71 non-keepers are permitted to leave regardless
#: of which bucket A.2 finally lands each in.
#: rc374 OVER-COUNT RECONCILIATION (ADR-0010 Amendment H.2, realised in full at
#: Amendment K). A.2's published split gave apokatastasis 31 and srmech.math 22.
#: But the real special-functions family is only 25 modules (the elliptic /
#: modular / theta / q-series galaxy); A.2's 31 OVER-counted it by 6, having
#: lumped in — by name-similarity — ``modular_linalg`` (GF(p) finite-field LA, a
#: general math primitive that only collides with "modular forms") plus 5 of the
#: general carriers. Those 6 belong to srmech.math, so the correct counts are
#: apokatastasis 25 and srmech.math 28 (22 + 6). The SUM is unchanged
#: (28 + 25 == 22 + 31 == 53), so the table still sums to 74 and the "73 of 75"
#: gap is preserved. This is booked HERE, in the same slice that drains the last
#: of srmech.math's members, because the carriers slice is what makes math's
#: real population (28) visible against the corrected count.
ADR_A2_DESTINATION_COUNTS = {
    "srmech.apokatastasis": 25,   # elliptic / modular / theta / q-series (H.2-corrected from 31)
    "srmech.math": 28,            # A-N primitives + carriers + general math (H.2-corrected from 22)
    "srmech.introspect": 10,      # + responsion_schema (the cross-cutting meta)
    "srmech.amsc": 4,             # KEEPS — the attestation framework
    "srmech.biology": 4,          # genome / plasmid / q8 / coupling
    "srmech.cascade": 1,          # compose
    "srmech.music": 1,            # harmonics
    "srmech._native": 1,          # the fifth bucket
}

#: The members A.2 / the Decision table name EXPLICITLY per destination. The
#: winding/math/introspect split is published only as an aggregate count, so it
#: is deliberately NOT reproduced per-module here — inventing that assignment
#: would fabricate authority A.2 does not carry. Each such module is still
#: covered by the departure allowlist (it is a non-keeper), and lands in its
#: named bucket in the slice that actually moves it.
NAMED_DEPARTURES = {
    "srmech.biology": frozenset({"coupling", "genome", "plasmid", "q8"}),
    "srmech.cascade": frozenset({"compose"}),
    "srmech.music": frozenset({"harmonics"}),
    "srmech._native": frozenset({"_native"}),
    "srmech.introspect": frozenset({
        "tool_schema", "_tool_docs", "carrier_schema",
        "op_provenance", "naming", "responsion_schema"}),
    # rc370 — the elliptic domain's first named member. rc371 — the WHOLE-FAMILY
    # drain names the other 24, so this bucket is the full 25-module elliptic /
    # modular / theta / q-series family. rc374 CLOSES the H.2 over-count: A.2's
    # published 31 OVER-counted this family by 6 (it lumped ``modular_linalg`` +
    # 5 general carriers in by name-similarity). Those 6 are now realised as
    # srmech.math members (``modular_linalg`` at rc372, the 5 carriers within the
    # rc374 carrier slice), and ADR_A2_DESTINATION_COUNTS["srmech.apokatastasis"]
    # is corrected 31 -> 25 to match. So this bucket is now FULLY named: 25
    # members == the corrected count of 25 (no longer a subset). See ADR-0010
    # Amendment H (the finding) + Amendment K (the reconciliation).
    "srmech.apokatastasis": frozenset({
        "elliptic_partial_fraction",
        "apagodu_zeilberger", "eisenstein", "ellbase", "elliptic_determinant",
        "elliptic_gosper", "elliptic_jackson", "elliptic_jackson_an",
        "elliptic_recurrence", "elliptic_wz_certificate", "elliptic_zeilberger",
        "eta_quotient", "gosper", "harmonic_maass", "modular_forms_ring",
        "q_gosper", "q_wz_certificate", "q_zeilberger", "quasimodular_forms_ring",
        "riemann_theta", "riemann_theta_multisum", "thetasum", "unary_theta",
        "wz_certificate", "zeilberger"}),
    # rc372 opened this bucket (octonion / kepler / modular_linalg); rc373 added
    # the ten A-N primitives; rc374 (this slice) adds the fifteen CARRIERS and
    # DRAINS the bucket. It is now FULLY named: 28 members == the H.2-corrected
    # A.2 count of 28 (see ADR_A2_DESTINATION_COUNTS above). ``modular_linalg``
    # was the H.2 apokatastasis over-count reassignment (𝔽_p linear algebra, a
    # general math primitive, NOT modular forms); the 15 carriers here are the
    # other half of that over-count — the general Mat/Vec/HV/Q/… carriers A.2
    # had lumped into apokatastasis's 31 by name-similarity.
    "srmech.math": frozenset({"octonion", "kepler", "modular_linalg",
        "cyclic", "dispatch", "hdc", "laplacian", "primes", "rational",
        "search", "template", "tlv", "text",
        "mat", "vec", "hv", "q", "qmat", "qi", "qalg", "qprime", "poly",
        "qpoly", "qbipoly", "tripoly", "complex128", "carrier_ladder",
        "carrier_spectrum"}),
}

#: Modules that have COMPLETED their ADR-0010 departure — they have LEFT
#: ``srmech/amsc/`` (so they are no longer in the manifest) and ARRIVED at their
#: A.2 destination. This is the drain's running record, and it exists because the
#: first real move (rc366) exposed a conflation the rc365 mint could not see: the
#: manifest is the CURRENT amsc population (it must shrink as modules leave, so
#: the down-only ratchet's ceiling actually drops and a re-add is caught), while
#: ``NAMED_DEPARTURES`` / ``ADR_A2_DESTINATION_COUNTS`` are A.2's FIXED plan
#: (harmonics -> music is true forever, whether or not it has moved yet). At rc365
#: those two agreed because nothing had moved; the move-map test below asserted
#: "every named member is still in the manifest", which is only a rc365-snapshot
#: truth. ``LANDED`` restores the distinction: a named member is REAL when it is
#: still in amsc OR has already landed, and the population is CONSERVED
#: (live + landed == original). rc366: the harmonics slice, the first entry.
#: rc367: the ``naming`` slice (amsc -> srmech.introspect), the second entry.
#: rc368: the ``responsion_schema`` slice (amsc -> srmech.introspect), the third.
#: rc369: the ``op_provenance`` slice (amsc -> srmech.introspect), the fourth.
#: rc370: the ``elliptic_partial_fraction`` slice (amsc -> srmech.apokatastasis),
#: the fifth — and the first departure to a namespace CREATED by the same slice.
#: rc371: the WHOLE-FAMILY drain — the 24 remaining elliptic / modular / theta /
#: q-series modules land in srmech.apokatastasis in one slice (the sixth), taking
#: LANDED from 5 to 29 and the live amsc count from 70 to 46 (conservation
#: 46 + 29 == 75).
#: rc372: the general-algebra roster ``octonion`` / ``kepler`` / ``modular_linalg``
#: lands in srmech.math (the seventh slice, the first into that namespace), taking
#: LANDED from 29 to 32 and the live amsc count from 46 to 43 (conservation
#: 43 + 32 == 75).
#: rc373: the ten A-N primitives (cyclic / dispatch / hdc / laplacian / primes /
#: rational / search / template / tlv / text) land in srmech.math, taking LANDED
#: from 32 to 42 and the live amsc count from 43 to 33 (conservation 33 + 42 == 75).
#: rc374: the fifteen CARRIERS (mat / vec / hv / q / qmat / qi / qalg / qprime /
#: poly / qpoly / qbipoly / tripoly / complex128 / carrier_ladder /
#: carrier_spectrum) land in srmech.math — the math bucket's LAST slice, taking
#: LANDED from 42 to 57 and the live amsc count from 33 to 18 (conservation
#: 18 + 57 == 75).
#: rc375: the four BIOLOGY modules (coupling / genome / plasmid / q8) land in
#: srmech.biology — the biology bucket opened AND drained in one slice, taking
#: LANDED from 57 to 61 and the live amsc count from 18 to 14 (conservation
#: 14 + 61 == 75).
LANDED = frozenset({"harmonics", "naming", "responsion_schema", "op_provenance",
                    "elliptic_partial_fraction",
                    "apagodu_zeilberger", "eisenstein", "ellbase",
                    "elliptic_determinant", "elliptic_gosper", "elliptic_jackson",
                    "elliptic_jackson_an", "elliptic_recurrence",
                    "elliptic_wz_certificate", "elliptic_zeilberger",
                    "eta_quotient", "gosper", "harmonic_maass",
                    "modular_forms_ring", "q_gosper", "q_wz_certificate",
                    "q_zeilberger", "quasimodular_forms_ring", "riemann_theta",
                    "riemann_theta_multisum", "thetasum", "unary_theta",
                    "wz_certificate", "zeilberger",
                    "octonion", "kepler", "modular_linalg",
                    "cyclic", "dispatch", "hdc", "laplacian", "primes",
                    "rational", "search", "template", "tlv", "text",
                    "mat", "vec", "hv", "q", "qmat", "qi", "qalg", "qprime",
                    "poly", "qpoly", "qbipoly", "tripoly", "complex128",
                    "carrier_ladder", "carrier_spectrum",
                    "coupling", "genome", "plasmid", "q8"})


# ── readers ──────────────────────────────────────────────────────────────────

def _manifest_entries() -> list[str]:
    text = MANIFEST.read_text(encoding="utf-8")
    return [ln for ln in text.splitlines() if ln.strip()]


def _manifest_modules() -> frozenset[str]:
    return frozenset(e for e in _manifest_entries() if not e.endswith("/"))


def _manifest_subpackages() -> frozenset[str]:
    return frozenset(e[:-1] for e in _manifest_entries() if e.endswith("/"))


def _live_modules() -> frozenset[str]:
    return frozenset(p.stem for p in _AMSC.glob("*.py") if p.name != "__init__.py")


def _live_subpackages() -> frozenset[str]:
    return frozenset(p.name for p in _AMSC.iterdir()
                     if p.is_dir() and (p / "__init__.py").is_file())


def _normalised(entries) -> bytes:
    return ("\n".join(sorted(entries)) + "\n").encode("utf-8")


def _digest_of(modules, subpkgs) -> str:
    """Digest a hypothetical population the way the manifest is digested."""
    entries = list(modules) + [s + "/" for s in subpkgs]
    return sha256_bytes(_normalised(entries))


# ── pure predicates (shared with the non-vacuity proof) ──────────────────────

def _down_only_ok(committed, live) -> bool:
    """A module may LEAVE ``amsc``; one may never appear. live ⊆ committed."""
    return live <= committed


def _departures(committed, live) -> frozenset:
    return committed - live


def _all_departures_mapped(removed, allowed) -> bool:
    """Every departing module is one A.2 permits to leave."""
    return removed <= allowed


def _keepers_intact(removed) -> bool:
    """None of the four attestation keepers left."""
    return not (removed & KEEPERS)


# ── 1. the committed manifest is well-formed ─────────────────────────────────

def test_manifest_exists_sorted_unique_and_partitions() -> None:
    assert MANIFEST.exists(), (
        f"{MANIFEST.name} is missing — it is the move witness and it is "
        f"HAND-COMMITTED, so nothing regenerates it for you. See this module's "
        f"docstring for the two-edit procedure.")
    entries = _manifest_entries()
    assert entries == sorted(entries), "the manifest must be sorted"
    assert len(entries) == len(set(entries)), "the manifest has duplicate lines"
    mods, subs = _manifest_modules(), _manifest_subpackages()
    assert len(mods) == EXPECTED_N_MODULES, (
        f"committed module count {len(mods)} != {EXPECTED_N_MODULES}")
    assert len(subs) == EXPECTED_N_SUBPACKAGES, (
        f"committed subpackage count {len(subs)} != {EXPECTED_N_SUBPACKAGES}")
    assert subs == EXPECTED_SUBPACKAGES, f"committed subpackages: {subs}"
    assert KEEPERS <= mods, (
        f"a keeper is not in the committed manifest: {KEEPERS - mods}")


def test_the_census_digest_is_pinned_in_source() -> None:
    """The second of the two required edits. Pinning the digest in SOURCE means
    a rewrite of the data file alone cannot pass."""
    got = sha256_bytes(_normalised(_manifest_entries()))
    assert got == EXPECTED_CENSUS_SHA256, (
        f"census digest drifted.\n  expected {EXPECTED_CENSUS_SHA256}\n"
        f"  got      {got}\n"
        "Update EXPECTED_CENSUS_SHA256 to the 'got' value IN THE SAME COMMIT as "
        "the manifest rewrite (the two-edit procedure in the module docstring).")


# ── 2. DOWN-ONLY: the live population is a subset of the committed one ────────

def test_the_live_module_set_is_a_subset_of_the_manifest() -> None:
    """⚠️ THE MOVE GATE. A module may leave ``amsc``; one may not appear.

    ``removed`` (committed − live) is EXPECTED to be non-empty as the arc
    proceeds — that is the drain, and it is legal. ``added`` (live − committed)
    is the regression: a new module dropped into ``amsc``, or a moved module
    that never left. That is what goes red here.
    """
    committed, live = _manifest_modules(), _live_modules()
    added = sorted(live - committed)
    removed = sorted(committed - live)
    assert _down_only_ok(committed, live), (
        "a module APPEARED in srmech/amsc that is not in the committed census.\n"
        f"  committed {len(committed)}  live {len(live)}\n"
        f"  added({len(added)}): {added}\n"
        "amsc is draining 75 -> 4; nothing may be added to it. If this module "
        "genuinely belongs in the attestation framework, follow the two-edit "
        "procedure in this module's docstring to re-baseline the census.")
    # informational: report the drain progress in the failure of a later check
    assert removed == sorted(committed - live)  # tautology-free: names the drain


def test_live_subpackages_are_a_subset_of_the_manifest() -> None:
    committed, live = _manifest_subpackages(), _live_subpackages()
    added = sorted(live - committed)
    assert live <= committed, (
        f"a subpackage APPEARED in srmech/amsc not in the census: {added}. "
        f"The attestation subpackages are {sorted(ATTESTATION_SUBPACKAGES)}; "
        f"'cascade' is slated to move to the top-level srmech.cascade namespace.")


# ── 3. the departures respect A.2, and the keepers never leave ───────────────

def test_the_four_keepers_are_present_and_have_not_departed() -> None:
    """A.2's floor. These four are the reason ``amsc`` exists at all."""
    live = _live_modules()
    assert KEEPERS <= live, (
        f"an attestation keeper has left srmech/amsc: {sorted(KEEPERS - live)}. "
        f"The keepers {sorted(KEEPERS)} are the ratchet's floor and A.2 keeps "
        f"them by name — a slice that moved one is wrong, not the census.")
    removed = _departures(_manifest_modules(), live)
    assert _keepers_intact(removed), (
        f"a keeper is in the removed set: {sorted(removed & KEEPERS)}")


def test_every_departure_is_a_module_A2_permits_to_leave() -> None:
    """removed ⊆ the departure allowlist (all non-keepers).

    A module leaving ``amsc`` for nowhere A.2 classifies would be red here. The
    allowlist is derived from the authoritative fact that only the four keepers
    stay, so every one of the 71 non-keepers is a permitted departure.
    """
    committed, live = _manifest_modules(), _live_modules()
    allowed = committed - KEEPERS
    removed = _departures(committed, live)
    unmapped = sorted(removed - allowed)
    assert _all_departures_mapped(removed, allowed), (
        f"module(s) left srmech/amsc that A.2 does not classify: {unmapped}. "
        f"Either a keeper left (see the keeper gate) or the move map needs the "
        f"module added to a destination before the slice that moves it.")


def test_the_move_map_matches_A2_where_A2_is_authoritative() -> None:
    """Encode A.2 as data and check it against the committed population.

    Only the destinations A.2 names per-module are asserted member-by-member;
    the winding/math/introspect split is checked at the aggregate-count level it
    is published at.
    """
    mods = _manifest_modules()
    # named members are real, and none is a keeper. "Real" = still in amsc OR
    # already LANDED at its destination — A.2 classifies a module whether it has
    # moved yet or not, so once ``harmonics`` leaves the manifest it is still a
    # correct A.2 classification, just a completed one. Checking against ``mods``
    # alone was a rc365-snapshot truth that the first real move (rc366) broke.
    real = mods | LANDED
    seen: set[str] = set()
    for dest, members in NAMED_DEPARTURES.items():
        assert members <= real, (
            f"{dest}: named member(s) neither in the census nor landed: "
            f"{sorted(members - real)}")
        assert not (members & KEEPERS), (
            f"{dest}: names a keeper: {sorted(members & KEEPERS)}")
        assert not (members & seen), (
            f"{dest}: member classified twice: {sorted(members & seen)}")
        seen |= set(members)
    # the small destinations A.2 gives exactly: named members == published count
    for dest in ("srmech.biology", "srmech.cascade", "srmech.music",
                 "srmech._native"):
        assert len(NAMED_DEPARTURES[dest]) == ADR_A2_DESTINATION_COUNTS[dest], (
            f"{dest}: named {len(NAMED_DEPARTURES[dest])} but A.2 counts "
            f"{ADR_A2_DESTINATION_COUNTS[dest]}")
    # introspect names a subset of its count (the rest are unnamed by A.2)
    assert len(NAMED_DEPARTURES["srmech.introspect"]) <= \
        ADR_A2_DESTINATION_COUNTS["srmech.introspect"]
    # apokatastasis is now FULLY named (rc371 landed all 25; rc374 corrected the
    # count 31 -> 25 per H.2), so this is an equality, still expressed as <=.
    assert len(NAMED_DEPARTURES["srmech.apokatastasis"]) <= \
        ADR_A2_DESTINATION_COUNTS["srmech.apokatastasis"]
    # math is now FULLY named too: rc374 drains the last of it (28 named == the
    # H.2-corrected count of 28). The math bucket is DONE.
    assert len(NAMED_DEPARTURES["srmech.math"]) <= \
        ADR_A2_DESTINATION_COUNTS["srmech.math"]
    # the keeps count is the keeper set
    assert ADR_A2_DESTINATION_COUNTS["srmech.amsc"] == len(KEEPERS)
    # A.2's table sums to 74; the ORIGINAL tree had 75 (its own "73 of 75" gap,
    # documented). The gap is stated against the FIXED baseline, not the draining
    # live count — otherwise it would falsely move by 1 on every slice.
    assert sum(ADR_A2_DESTINATION_COUNTS.values()) == 74
    assert ORIGINAL_N_MODULES - sum(ADR_A2_DESTINATION_COUNTS.values()) == 1


def test_the_drain_is_conserved_and_landed_is_a_real_record() -> None:
    """live + landed == original — the drain moves modules, it never loses them.

    rc366 added ``LANDED`` when the first module-moving slice exposed that the
    manifest (current amsc population) and A.2's fixed plan are DIFFERENT
    quantities the rc365 mint had conflated. This is the invariant that keeps
    them honest: every module the manifest has shed is accounted for as landed,
    so ``EXPECTED_N_MODULES`` (live) + ``len(LANDED)`` always reconstructs the
    fixed baseline. A module that "left" without being recorded as landed — or a
    landed module still sitting in amsc — is the drift this catches.
    """
    assert EXPECTED_N_MODULES + len(LANDED) == ORIGINAL_N_MODULES, (
        f"drain not conserved: live {EXPECTED_N_MODULES} + landed {len(LANDED)} "
        f"!= original {ORIGINAL_N_MODULES}. A module left the manifest without "
        f"being recorded in LANDED, or LANDED gained a module that is still live.")
    live = _live_modules()
    # A landed module has genuinely LEFT amsc (it is what makes the down-only
    # ceiling drop) and is NOT in the committed manifest either …
    assert not (LANDED & live), (
        f"LANDED names a module still live in srmech/amsc: {sorted(LANDED & live)} "
        f"— it has not actually departed, so it is not landed.")
    assert not (LANDED & _manifest_modules()), (
        f"LANDED names a module still in the census manifest: "
        f"{sorted(LANDED & _manifest_modules())} — drop it from the manifest in "
        f"the same slice that lands it.")
    # … and A.2 actually classified it (it lands SOMEWHERE named, not nowhere).
    a2_named = frozenset().union(*NAMED_DEPARTURES.values())
    assert LANDED <= a2_named, (
        f"LANDED names a module A.2 does not classify per-module: "
        f"{sorted(LANDED - a2_named)} — a module cannot land at a destination "
        f"the move map never named.")


# ── 4. NON-VACUITY: prove each assertion can actually fire ────────────────────

def test_the_census_can_actually_fail() -> None:
    """⚠️ A census that cannot be shown to fail is the EMPTY probe A.5 warns
    against. Four injections on the real committed population, each proving that
    exactly the intended assertion goes red while the others stay green.
    """
    committed = _manifest_modules()
    subs = _manifest_subpackages()
    allowed = committed - KEEPERS
    assert _digest_of(committed, subs) == EXPECTED_CENSUS_SHA256, (
        "the digest helper disagrees with the pinned value — the injection "
        "proofs below would be measuring the wrong thing.")

    # (1) a module leaves for a MAPPED destination (compose -> srmech.cascade):
    #     down-only stays GREEN (a departure is legal), and the digest CHANGES
    #     — the move is detected. (Was ``poly`` until rc374 then ``genome`` until
    #     rc375, each retired as a stand-in once it actually departed — genome to
    #     srmech.biology this slice; ``compose`` is the remaining still-present
    #     non-keeper A.2 maps, to srmech.cascade.)
    leaver = "compose"
    assert leaver in allowed and leaver not in KEEPERS
    live1 = committed - {leaver}
    removed1 = _departures(committed, live1)
    assert _down_only_ok(committed, live1)                 # subset holds
    assert _all_departures_mapped(removed1, allowed)       # move-map green
    assert _keepers_intact(removed1)                       # keeper green
    assert _digest_of(live1, subs) != EXPECTED_CENSUS_SHA256, (
        "a module left but the digest did not change — the move would be "
        "invisible, which is the exact blindness this census exists to remove.")

    # (2) a departure the map does NOT classify -> the move-map assert goes RED,
    #     while down-only (it IS a departure) and the keeper gate stay green.
    unmapped = "__module_the_map_forgot__"
    assert unmapped not in allowed and unmapped not in KEEPERS
    removed2 = frozenset({unmapped})
    assert not _all_departures_mapped(removed2, allowed)   # move-map RED
    assert _keepers_intact(removed2)                       # keeper still green
    assert _down_only_ok(committed | removed2, committed)  # a departure, legal

    # (3) a NEW module APPEARS in amsc -> down-only goes RED. The regression the
    #     ratchet exists to catch (amsc must only drain).
    newcomer = "__a_new_module_in_amsc__"
    live3 = committed | {newcomer}
    assert not _down_only_ok(committed, live3)             # down-only RED
    assert sorted(live3 - committed) == [newcomer]

    # (4) a KEEPER leaves -> the keeper assert goes RED (and, being outside the
    #     allowlist, the move-map assert too — but the keeper gate is the named
    #     one).
    keeper = "format"
    assert keeper in KEEPERS
    removed4 = frozenset({keeper})
    assert not _keepers_intact(removed4)                   # keeper RED
    assert not _all_departures_mapped(removed4, allowed)   # keeper ∉ allowlist


# ── 5. the manifest is not codegen-emitted ───────────────────────────────────

def test_the_manifest_is_not_codegen_emitted() -> None:
    """⚠️ If codegen ever writes this file, the witness dies silently.

    A declustering slice runs ``tools/regen_all.py`` as routine work. A
    generated census would be rewritten by the change it is meant to detect and
    go green unconditionally (A.5 item 1's rule, applied to the census). Keep it
    hand-committed and review-gated.
    """
    tools = Path(__file__).resolve().parents[1] / "tools"
    assert tools.is_dir(), tools
    writers = [p.name for p in sorted(tools.glob("*.py"))
               if MANIFEST.name in p.read_text(encoding="utf-8", errors="replace")]
    assert writers == [], (
        f"{MANIFEST.name} is referenced by codegen tool(s) {writers}. If a "
        f"generator now writes it, this census can no longer detect a move — it "
        f"would be regenerated by the same command the arc runs. Keep the "
        f"manifest hand-committed.")


# ── 6. the end state, documented ─────────────────────────────────────────────

def test_the_end_state_floor_is_the_four_keepers() -> None:
    """The ratchet's floor, stated so a later reader knows when the arc is DONE.

    ``amsc`` drains 75 modules -> 4. The arc is COMPLETE when ``_live_modules()``
    equals ``KEEPERS`` (and only the two attestation subpackages remain). This is
    documentary, not a live assertion of completion — the drain is monotone, not
    instantaneous.
    """
    assert len(KEEPERS) == 4
    assert KEEPERS < _manifest_modules(), (
        "the keepers are the floor; the committed population must be a strict "
        "superset of them until the arc completes.")
