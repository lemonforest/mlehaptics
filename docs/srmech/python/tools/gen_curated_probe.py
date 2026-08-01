#!/usr/bin/env python3
"""Dev-time PROBE that executes the central ops with real inputs + captures
verified input->output, refreshing their _tool_docs_curated.py CURATED rows.

NOT the SSoT — the human reviews/edits the emitted file. This just guarantees
every curated EXAMPLE is a REAL executed result (never hand-typed / fabricated).
Run:  python tools/gen_curated_probe.py   (from docs/srmech/python)

**MERGES, never clobbers (rc291, #T916).** This script used to write the whole
file from the ``CENTRAL`` list below, which silently deleted every curated
entry CENTRAL does not mention — the same "generator eats curation" defect
that #T916 tracked in gen_tool_docs.py, but worse, because here the casualty
is the curation SSoT itself. It now loads the existing CURATED, updates only
the keys it actually probed, and reports preserved-vs-refreshed counts. A key
present on disk is never dropped.
"""
from __future__ import annotations
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import srmech  # noqa: F401,E402
from srmech.introspect.tool_schema import warmup_all  # noqa: E402
warmup_all()

_EDGES = [(0, 1), (1, 2), (2, 0), (2, 3)]
_W = [1.0, 1.0, 1.0, 1.0]


def _resolve(name):
    import importlib
    mod, _, attr = name.rpartition(".")
    return getattr(importlib.import_module(mod), attr)


_DL = _resolve("srmech.math.laplacian.dense_laplacian")(n=4, edges=_EDGES, weights=_W)

# (tool name, (args tuple, kwargs dict), curated explanation or None=use docstring)
CENTRAL = [
    ("srmech.math.laplacian.dense_laplacian", ((), dict(n=4, edges=_EDGES, weights=_W)),
     "Combinatorial graph Laplacian L = D − A of a weighted undirected graph "
     "(n nodes, edges + per-edge weights) as a dense Mat — the foundation the "
     "Class-L spectral readers (fiedler / spine / eigvals) run on. F1216: the "
     "Class-L Laplacian IS the LONG-TERM relational STORE (exact, addressed, "
     "directional, GROWS with knowledge — the genome / disk); the Class-M "
     "Klein-4/HDC bundle is the transient working-memory read, bridged by the "
     "reversible spectral basis-change (eigen / Walsh-Hadamard)."),
    ("srmech.math.laplacian.jacobi_eigvals", ((_DL,), {}),
     "Ascending eigenvalues of a symmetric Mat via cyclic Jacobi rotations "
     "(no numpy). On a graph Laplacian: λ0 = 0 for a connected graph; λ1 (the "
     "Fiedler value) measures algebraic connectivity."),
    ("srmech.math.laplacian.fiedler_vector", ((_DL,), {}),
     "Eigenvector of the second-smallest Laplacian eigenvalue (λ1). Its sign "
     "per node gives the natural 2-way spectral cut of the graph."),
    ("srmech.math.laplacian.three_fold_eigvec_groups", ((_DL,), {}),
     "3-way spectral partition from the sign pattern across the low eigenvectors "
     "(the k=3 community read; complements fiedler's 2-way and spine's centrality)."),
    ("srmech.math.laplacian.spectral_spine", ((), dict(edges=_EDGES, weights=_W, k=3)),
     "The structurally-central 'spine': top-|component| nodes of the dominant-"
     "eigenvalue eigenvector — the centrality axis, complementing the community "
     "readers (fiedler 2-way / three_fold 3-way)."),
    # ``the_one`` moved to WORKED (rc353, `#T1006`) — its single-call row here
    # produced one repr and no sibling context, and the whole point of that op
    # is the (σ, θ, w) FAMILY. Deleted rather than left alongside: ``main()``
    # applies WORKED last, so a stale CENTRAL row for the same op is dead
    # weight that still prints "OK", which is exactly how an author comes to
    # edit the copy that does not ship.
    ("srmech.math.cyclic.gcd", ((), dict(a=12, b=18)), None),
    ("srmech.math.cyclic.mod_pow", ((), dict(a=7, k=13, n=11)),
     "Modular exponentiation a^k mod n by square-and-multiply (Class-I cyclic "
     "group). Exact; the Fermat/RSA-style fast power on ℤ/n."),
    ("srmech.math.rational.best_rational", ((), dict(numerator=314159, denominator=100000, max_denominator=100)),
     "Best rational p/q with q ≤ max_denominator approximating numerator/"
     "denominator (Class-N small-denominator anchor via continued fractions). "
     "Takes an INTEGER numerator/denominator pair, never a float."),
    ("srmech.math.primes.is_prime", ((), dict(n=97)),
     "Deterministic primality test (Class-J). True iff n is prime."),
    ("srmech.amsc.format.sha256_bytes", ((), dict(data=b"abc")), None),
    ("srmech.math.hdc.bind", ((), dict(a=b"abc", b=b"abc")),
     "Component-wise XOR of two binary-spatter-code (BSC) hypervectors — the "
     "Class-M bind that ties a role to a filler; self-inverse (bind(x,x)=0). "
     "F1216: Class-M / HDC = WORKING MEMORY / active context (fuzzy, composable, "
     "BOUNDED ~24-bind span, gracefully decays) — a transient read of the "
     "Class-L Laplacian long-term store, never the store itself."),
    ("srmech.math.hdc.bundle", ((), dict(vectors=[b"abc", b"abd", b"abe"])),
     "Majority-rule superposition of several BSC hypervectors into one that is "
     "similar to each input — the Class-M bundle (the set/record former)."),
    ("srmech.math.hdc.similarity", ((), dict(a=b"abc", b=b"abd")),
     "Normalised agreement (1 − 2·Hamming/D) between two BSC hypervectors, as an "
     "exact rational Q. +1 = identical, 0 = orthogonal, −1 = complementary."),
    ("srmech.cascade.magnitude", ((), dict(x=-3.5)),
     "The Class-K real pin-slot magnitude |x| — the cascade-honest replacement "
     "for Python abs(): a sign-branch phase-boundary op, NOT a complex modulus "
     "(it rejects complex input by contract)."),
    ("srmech.cascade.pin_slot_at_zero", ((), dict(x=-3.5)),
     "The Class-K pin-slot at zero: splits x into its sign (the pinned phase "
     "boundary, −1/0/+1) and its magnitude — the primitive |·| composes from."),
    ("srmech.cascade.net_chirality", ((), dict(orientations=[1, -1, 1, 1])),
     "Class-C net chirality: the signed product/sum reduction of a sequence of "
     "per-step orientations into the one net which-way handedness."),
    # The auto-seed probes fold_marks with 'abc', which round-trips unchanged
    # and so demonstrates nothing. Probe it with the Devanagari case instead:
    # the virama and the vowel sign are BOTH marks, which is the whole reason
    # the op is fold_marks and not fold_accents.
    ("srmech.math.text.fold_marks", ((), dict(text="क्षि")),
     "Drop combining marks by Unicode CATEGORY — Mn/Mc/Me and nothing else "
     "(Class B/G text-framing; §106/F1258; rc293). The name is the contract: a "
     "VIRAMA is a mark, not an accent, so `fold_accents` would have been wrong "
     "in exactly the Indic cases that matter most while quietly re-scoping the "
     "op toward Latin. Category only — no case change, no locale tailoring, no "
     "NFKD/compatibility folding, no ligature expansion — so 'ø' and the OHM "
     "SIGN are unchanged and Hangul is unchanged in either normalization form. "
     "Needs NO normalizer: precomposed characters are handled by the vendored "
     "table's replacement rows and decomposed sequences by its drop rows, so "
     "the same marks fall out whichever form is supplied. Idempotent. A "
     "SEPARATE op, not a glyph_stream mode — folding is lossy and glyph_stream "
     "is contractually lossless; compose as glyph_stream(fold_marks(s))."),
]


def _rs(v):
    r = repr(v)
    return r if len(r) <= 200 else r[:197] + "..."


# ══════════════════════════════════════════════════════════════════════
# WORKED examples — the F08 Cayley–Dickson / algebra_table / carrier
# family (rc353, `#T1006`).
#
# WHY A SECOND FORM. ``CENTRAL`` above probes ONE call per op, which is
# enough for ``gcd(12, 18) -> 6`` and not enough for anything whose job
# is only visible NEXT TO its siblings. It is the second kind that was
# costing real work: an Opus 5 agent reading the old signature-stencil
# examples queued ``mat_rank`` as a gap while ``QMat.rank`` was shipping
# (``srmech/amsc/qmat.py:446``, C peer ``srmech_qmat_rank``). A worked
# sequence is the fix — the reader SEES the op doing its job and sees
# which neighbour already covers the adjacent job.
#
# A row is ``(tool_name, [(label, source), ...], explanation, why)``.
# Every ``source`` is EVAL'd here, in order, in :data:`_WORKED_NS`, and
# its REAL ``repr`` is captured — so a shipped ``output`` is a transcript
# of a run, never typed prose. An expression whose repr exceeds
# :data:`_WORKED_MAX` RAISES rather than truncating: a truncated output
# is a fabricated output with extra steps (the same rc294 `#T924` rule
# that made ``gen_tool_docs`` drop stale executed-I/O), so the author is
# forced to narrow the expression instead.
#
# SUBJECT DISCIPLINE (user, 2026-07-28): examples compute something from
# a REAL research subject, never random values. This family's subject is
# the h-genome carrier + the Hurwitz tower, so the sequences run on:
#   * the ATTESTED Standard Genetic Code (``amsc/attested/genetic_code``,
#     response_sha256 ddda97af…, NCBI transl_table=1) — 64 codons indexed
#     16·b0 + 4·b1 + b2 over TCAG, which is exactly a 6-bit address, so a
#     64-slot Cayley–Dickson register addresses the code one codon per
#     slot. MEASURED HERE: the XOR-63 direction IS the Rumer involution
#     (T↔G, C↔A) on all 64 codons, so ``e_i·e_63`` reads the code's own
#     order-2 alphabet symmetry — the index lane — while the cocycle sign
#     carries the Class-C which-way that the involution alone cannot see.
#   * the octonion / split-octonion pair — ``algebra_table(8)`` IS
#     ``qm.octonion_mult_table()`` (the Furey ℝ⊗ℂ⊗ℍ⊗𝕆 anchor), and
#     ``gammas=[1,-1,-1]`` is the split negative control that
#     `[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]`
#     makes mandatory for any carrier claim.
#   * the sedenion zero divisor x = e1+e10, y = e4−e15 — the structural
#     mutation floor past 𝕆 (catalog C7), taken from OUR OWN table.
# ══════════════════════════════════════════════════════════════════════

_WORKED_MAX = 320


def _worked_ns():
    """The evaluation namespace the worked sources run in — the ops
    themselves plus the attested genetic-code reader they are grounded on."""
    import itertools
    import json as _json
    from pathlib import Path as _Path

    import srmech.amsc.attested as _attested
    from srmech.cascade import (
        algebra_table, cd_basis_product, cd_carry, cd_conjugate, cd_correct,
        cd_couple_working, cd_mult, cd_navigate, cd_navmap,
        cd_navmap_is_signed_permutation, cd_norm_sq, cd_project, cd_promote,
        cd_register, cd_uncouple_working, hypercomplex_couple,
        hypercomplex_exp, inertia_signature, is_division_algebra_dim,
        left_mult_is_invertible, left_mult_kernel, sedenion_register,
        sedenion_zero_divisor_witness, table_product, the_one,
    )
    from srmech.qm.octonion import octonion_mult_table
    from srmech.qm.quaternion import quaternion_mult_table

    gc_path = _Path(_attested.__file__).parent / "genetic_code" / "row.ndjson"
    gc = None
    for line in gc_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rec = _json.loads(line)
        if rec.get("data", {}).get("row_type") == "genetic_code_table":
            gc = rec["data"]
            break
    if gc is None:                                    # pragma: no cover
        raise RuntimeError("attested genetic_code row not found")
    bases = gc["base_order"]                          # "TCAG"

    def codon(i):
        """Codon at index ``i`` under the attested 16·b0+4·b1+b2 / TCAG map."""
        return bases[(i >> 4) & 3] + bases[(i >> 2) & 3] + bases[i & 3]

    ns = dict(locals())
    ns["ZD"] = sedenion_zero_divisor_witness()
    ns["O8"] = algebra_table(8)
    ns["SPLIT8"] = algebra_table(8, gammas=[1, -1, -1])
    return ns


# (tool, [(label, source), ...], explanation, why)
WORKED = [

    # ── the integer core ──────────────────────────────────────────────
    ("srmech.cascade.cd_basis_product", [
        ("1", "[cd_basis_product(64, i, 63) for i in (0, 21, 42, 63)]"),
        ("2", "[codon(i) for i in (0, 21, 42, 63)]"),
        ("3", "[codon(cd_basis_product(64, i, 63)[0]) for i in (0, 21, 42, 63)]"),
        ("4", "cd_basis_product(64, 21, 63), cd_basis_product(64, 63, 21)"),
        ("5", "cd_basis_product(8, 1, 2), cd_basis_product(8, 2, 1)"),
    ],
     "WHAT — the integer structural core of every Cayley–Dickson algebra: "
     "one basis pair in, ``(index, sign)`` out, with ``index == i XOR j`` "
     "always and the sign carrying the Fano/orientation cocycle. No "
     "elements, no Q, no allocation. The product FACTORS into these two "
     "lanes: the index lane is ABELIAN and order-blind and exact at every "
     "rung; the sign lane is where every ceiling srmech publishes actually "
     "lives (see ``describe()['lanes']``). "
     "WHEN — reach for it whenever the question is about ONE basis pair: "
     "addressing, a permutation, a sign audit. What you would otherwise "
     "wrongly hand-roll is the octonion sign table off a Fano-plane diagram "
     "or a 7-line mnemonic; that table already ships FOUR ways and all four "
     "agree because they are the same C cocycle. "
     "SIBLINGS — ``algebra_table(dim)`` materialises this same cocycle as "
     "the full dim³ tensor (and adds ``gammas=`` for split twists this op "
     "has no parameter for); ``qm.octonion_mult_table()`` and "
     "``qm.quaternion_mult_table()`` ARE ``algebra_table(8)`` / "
     "``algebra_table(4)`` — do not write a third; ``cd_navmap(dim, j)`` is "
     "this op swept over all i at fixed j; ``cd_mult`` is its bilinear "
     "extension to whole elements; ``table_product`` is the version that "
     "reads a table instead of the hard-wired ladder.",
     "e_i·e_j splits into an abelian index lane and an order-carrying sign "
     "lane: on the 64-slot codon register the ×e63 index lane IS the Rumer "
     "involution T↔G / C↔A, and reversing the operands keeps the index and "
     "flips the sign."),

    ("srmech.cascade.algebra_table", [
        ("1", "algebra_table(8) == octonion_mult_table()"),
        ("2", "algebra_table(4) == quaternion_mult_table()"),
        ("3", "algebra_table(8)[1][2]"),
        ("4", "algebra_table(8)[1][1], algebra_table(8, gammas=[1, -1, -1])[1][1]"),
        ("5", "sum(1 for i in range(8) for j in range(8) for k in range(8)"
              " if O8[i][j][k] != SPLIT8[i][j][k])"),
        ("6", "sorted({tuple(inertia_signature(algebra_table(8, gammas=list(g)))"
              "['signature']) for g in itertools.product((-1, 1), repeat=3)})"),
    ],
     "WHAT — the rank-3 structure-constant tensor of the GENERALISED "
     "Cayley–Dickson doubling, with the ``γ`` that ``cd_mult``'s recursion "
     "hard-wires to −1 exposed once PER DOUBLING in ladder order "
     "(``gammas[0]`` is ℝ→ℂ). All −1 is the definite ladder ℝ→ℂ→ℍ→𝕆→𝕊; a "
     "single +1 makes the algebra split from that rung up. "
     "WHEN — reach for it for the NEGATIVE CONTROL. "
     "`[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]` "
     "requires split-𝕆 and a random anticommutative table before any "
     "carrier claim counts, and before this op every one of those controls "
     "was hand-rolled for want of a constructor. What you would otherwise "
     "wrongly hand-roll: a split-octonion sign table (error-prone, and the "
     "shipped one is C-backed and differs from 𝕆 in exactly 16 of 512 "
     "entries). "
     "WHERE THE TWIST ACTUALLY BITES — call 4 is the whole difference in "
     "one entry: e1² = −1 on the definite ladder and +1 once gammas[0] is "
     "+1, because gammas[0] IS the ℝ→ℂ doubling. Only 16 of 512 entries "
     "move (call 5), which is why eyeballing a table tells you nothing and "
     "``inertia_signature`` does. "
     "SIBLINGS — ``cd_basis_product(dim, i, j)`` is ONE entry of this "
     "tensor, cheaper when you want one; ``qm.octonion_mult_table`` / "
     "``qm.quaternion_mult_table`` are this op at dim 8 / 4 with "
     "``gammas=None``, bit-identically, so they are not a separate source "
     "of truth; ``table_product`` is the product this table drives; "
     "``inertia_signature`` and ``left_mult_kernel`` both accept it, which "
     "is how a split algebra gets measured at all.",
     "gammas=None reproduces the shipped octonion table bit-identically "
     "while one +1 flips e1² from −1 to +1 — and all eight γ-triples at "
     "dim 8 collapse to exactly TWO inertia answers, 𝕆 and split-𝕆."),

    ("srmech.cascade.table_product", [
        ("1", "cd_mult([1,0,0,0,0,0,0,1], [1,0,0,0,0,0,0,-1])"),
        ("2", "table_product(O8, [1,0,0,0,0,0,0,1], [1,0,0,0,0,0,0,-1])"),
        ("3", "table_product(SPLIT8, [1,0,0,0,0,0,0,1], [1,0,0,0,0,0,0,-1])"),
        ("4", "table_product(algebra_table(2, gammas=[1]), [1,-1], [1,1])"),
        ("5", "cd_mult([1,-1], [1,1])"),
    ],
     "WHAT — the product read off a STRUCTURE-CONSTANT TABLE: "
     "``(x·y)_k = Σ_ij table[i][j][k]·x_i·y_j``, exact ℚ, defined for any "
     "algebra a table can express — a split twist from ``algebra_table``, a "
     "hand-built control, a table with no algebraic structure at all. "
     "WHEN — reach for it the moment the algebra is not the shipped "
     "definite ladder. ``cd_mult`` computes the ONE product its recursion "
     "is wired for; this computes whichever algebra you name. What you "
     "would otherwise wrongly hand-roll is a triple loop over a tensor — "
     "and that is not hypothetical: two such loops already existed in-tree "
     "(a private dim-8 one in ``laplacian`` with a single caller, and a "
     "test-local oracle that existed only BECAUSE no shipped product took a "
     "table) and zero shipped, until this op became the one both route "
     "through. "
     "SIBLINGS — ``cd_mult`` is the recursive-doubling route and returns "
     "the same exact-Q carrier, so the two are directly comparable and "
     "agree wherever both are defined (300/300 integer + 200/200 exact-ℚ "
     "dim-8 pairs); ``cd_basis_product`` is the basis-pair atom; "
     "``left_mult_kernel(x, table=…)`` is this product composed into a "
     "linear map so a zero divisor can be exhibited on the named algebra.",
     "The same two elements, two algebras: (1+e7)(1−e7) = 2 on 𝕆 and 0 on "
     "split-𝕆 — the table route agrees with the shipped product where both "
     "are defined and is the only route that can see the split answer."),

    ("srmech.cascade.inertia_signature", [
        ("1", "[(n, inertia_signature(t)['signature'], inertia_signature(t)['norm_signature'])"
              " for n, t in (('R', algebra_table(1)), ('C', algebra_table(2)),"
              " ('H', algebra_table(4)), ('O', O8), ('split-O', SPLIT8))]"),
        ("2", "inertia_signature(SPLIT8)['witness']"),
        ("3", "inertia_signature(algebra_table(2, gammas=[1]))['signature'],"
              " inertia_signature(algebra_table(2, gammas=[1]))['has_negative_direction']"),
        ("4", "left_mult_is_invertible([1, -1], table=algebra_table(2, gammas=[1]))"),
    ],
     "WHAT — Sylvester inertia (n₊, n₋, n₀) of the TRACE form "
     "q(x) = Re(x·x) read off a rank-3 structure-constant table, with the "
     "negative pivot direction attached as a witness; the NORM form's "
     "inertia ships alongside because the literature's split-𝕆 (4,4) is the "
     "norm read, not the trace read. "
     "WHEN — reach for it to ask what a table's quadratic form actually IS, "
     "on an algebra you may have just constructed. What you would otherwise "
     "wrongly hand-roll is the coordinate shortcut a² − |v|²; that "
     "substitution is INPUT-BLIND — it matches the real read 4000/4000 on 𝕆 "
     "and only 854/4000 on split-𝕆, and stays wrong at infinite precision. "
     "SCOPE, and this is the part a reader must not over-read: it reads ONE "
     "quadratic form and nothing else. n₋ == 0 does NOT mean orderable "
     "(split-ℂ answers (2,0,0) and still has (1+j)(1−j)=0, shown here), and "
     "a diagonal-pinned scrambled table answers exactly as 𝕆 does, so it "
     "certifies nothing about associativity, alternativity, composition or "
     "division. "
     "SIBLINGS — ``algebra_table`` builds the table it reads; "
     "``left_mult_is_invertible`` / ``left_mult_kernel`` answer the "
     "division question this op deliberately does not; ``cd_norm_sq`` gives "
     "the norm form's VALUE at one element where this gives the form's "
     "signature over the whole algebra.",
     "It reads the table, never a declared dimension — so split-𝕆 answers "
     "trace (5,3,0) / norm (4,4,0) rather than 𝕆's (1,7,0) / (8,0,0), and "
     "split-ℂ's n₋ = 0 sits right next to a genuine zero divisor."),

    # ── the element layer ─────────────────────────────────────────────
    ("srmech.cascade.cd_mult", [
        ("1", "cd_mult([0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0])"),
        ("2", "cd_mult([0,0,1,0,0,0,0,0], [0,1,0,0,0,0,0,0])"),
        ("3", "cd_mult(cd_mult([0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0]),"
              " [0,0,0,0,1,0,0,0])"),
        ("4", "cd_mult([0,1,0,0,0,0,0,0], cd_mult([0,0,1,0,0,0,0,0],"
              " [0,0,0,0,1,0,0,0]))"),
        ("5", "ZD['x_form'], ZD['y_form'], ZD['x_norm_sq'], ZD['y_norm_sq']"),
        ("6", "cd_mult(ZD['x'], ZD['y'])"),
    ],
     "WHAT — the exact-rational Cayley–Dickson product at any power-of-two "
     "rung, by the recursive doubling "
     "``(a1,a2)(b1,b2) = (a1b1 − b̄2a2, b2a1 + a2b̄1)``. Every component is a "
     "Q; there is no float anywhere in it. "
     "WHEN — reach for it for ℝ/ℂ/ℍ/𝕆 arithmetic and for the open exterior "
     "past 𝕆. What you would otherwise wrongly hand-roll: a quaternion "
     "multiply. srmech has ``qm.quaternion.quaternion_left_mult`` / "
     "``quaternion_right_mult`` for the matrix form, ``q8.q8_mult`` for the "
     "DISCRETE 8-element group, and this for the exact-ℚ algebra at every "
     "rung — three shipped answers, so a fourth is a duplicate. "
     "TWO STRUCTURAL FACTS THE EXAMPLE MEASURES RATHER THAN ASSERTS — "
     "calls 1–2 are non-COMMUTATIVITY (e1·e2 = e3, e2·e1 = −e3, already "
     "true in ℍ); calls 3–4 are non-ASSOCIATIVITY, which is new at 𝕆: "
     "(e1·e2)·e4 = +e7 while e1·(e2·e4) = −e7. Anything that groups a "
     "product differently gets a different answer at dim ≥ 8, so a "
     "left-fold and a right-fold over the same operands are DIFFERENT "
     "cascades. "
     "SIBLINGS — ``table_product`` is the same product driven by a table "
     "(the only route to a split algebra); ``cd_basis_product`` is the "
     "basis-pair cocycle underneath both; ``cd_norm_sq`` / ``cd_conjugate`` "
     "are the norm and involution that go with it; ``cd_register.multiply`` "
     "is the method form on a register's held element. Note the boundary "
     "this example lands on: the op is TOTAL at dim 16, and it is the "
     "ALGEBRA, not the op, that stops being a division algebra there.",
     "One op across the whole tower: e1·e2 = −e2·e1 (order is content), "
     "(e1·e2)·e4 = −e1·(e2·e4) (grouping is content too, from 𝕆 up), and at "
     "dim 16 the same call returns all-zero for two elements of norm 2."),

    ("srmech.cascade.cd_conjugate", [
        ("1", "cd_conjugate([0,1,0,0])"),
        ("2", "cd_mult([0,1,0,0], cd_conjugate([0,1,0,0]))"),
        ("3", "cd_conjugate(ZD['x'])"),
        ("4", "cd_mult(ZD['x'], cd_conjugate(ZD['x']))"),
        ("5", "left_mult_is_invertible(ZD['x'])"),
    ],
     "WHAT — Cayley–Dickson conjugation: negate every imaginary component, "
     "keep the real one. A Class-K sign-flip, never Python ``abs()``. "
     "WHEN — reach for it whenever you need x̄: the norm form N(x) = Re(x·x̄), "
     "an inverse x̄/N(x) where one exists, the unbind twiddle "
     "``hypercomplex_couple(..., sigma=-1)`` applies, or the reversed "
     "orientation of a product. What you would otherwise wrongly hand-roll "
     "is ``[x[0]] + [-c for c in x[1:]]``, which is right and still a "
     "duplicate — and gets the carrier wrong, because this returns exact Q. "
     "THE POINT THE EXAMPLE MAKES — conjugation is defined at EVERY rung "
     "and x·x̄ = N(x)·1 keeps holding past the Hurwitz wall: the sedenion "
     "zero divisor e1+e10 still satisfies it with N = 2, while "
     "``left_mult_is_invertible`` on that same element is False. Chirality "
     "persists; its reversing power does not. "
     "SIBLINGS — ``cd_norm_sq`` is Re(x·x̄) computed directly (do not "
     "compose the two to get a norm); ``cascade.chiral_flip`` / "
     "``net_chirality`` are the Class-C orientation ops on SEQUENCES, not "
     "on an algebra element; ``q8_conjugate`` / ``oct_conjugate`` are the "
     "discrete-group and fixed-dim-8 peers; ``cd_register.conjugate`` is "
     "the method form.",
     "x·x̄ = N(x)·1 holds at dim 16 for the very element that has no "
     "inverse — the involution survives the Hurwitz wall even though "
     "invertibility does not."),

    ("srmech.cascade.cd_norm_sq", [
        ("1", "cd_norm_sq([1, -1])"),
        ("2", "cd_norm_sq([1, -1], gammas=[1])"),
        ("3", "table_product(algebra_table(2, gammas=[1]), [1, -1], [1, 1])"),
        ("4", "cd_norm_sq(ZD['x']) * cd_norm_sq(ZD['y'])"),
        ("5", "cd_norm_sq(cd_mult(ZD['x'], ZD['y']))"),
    ],
     "WHAT — the norm form N(x) = Re(x·x̄) as an exact Q. On the definite "
     "ladder it collapses to the coordinate sum Σxᵢ², which is why it was "
     "unconditionally Σxᵢ² before the gate shipped. "
     "WHEN — reach for it for length, for the composition law, and for "
     "isotropy. GAMMAS DECLARES WHICH ALGEBRA AND THE DECLARATION IS "
     "LOAD-BEARING: on a split twist the coordinate sum is simply the wrong "
     "function, and the measured symptom was this op reporting N([1,−1]) = 2 "
     "for a GENUINE null vector of split-ℂ, unable to see isotropy at all. "
     "ON A DECLARED SPLIT TWIST THE RESULT CAN BE NEGATIVE OR ZERO FOR A "
     "NONZERO ELEMENT — reading ``_sq`` as non-negative is exactly the trap "
     "the parameter removes. The twisted read is O(dim), not O(dim³): the "
     "generalised product is monomial with index i⊕j, so "
     "N(x) = Σᵢ xᵢ·x̄ᵢ·sign_γ(i,i). "
     "SIBLINGS — ``cd_conjugate`` + ``cd_mult`` would recompute this the "
     "slow way; ``inertia_signature(table)['norm_signature']`` gives the "
     "same form's SIGNATURE over the whole algebra rather than its value at "
     "one point; ``cd_register.norm`` is the method form; "
     "``qm.quaternion.quaternion_norm`` / ``qm.octonion.octonion_norm`` are "
     "the fixed-rung float peers.",
     "gammas is the algebra declaration: N([1,−1]) is 2 on definite ℂ and 0 "
     "on split-ℂ (a real null vector), and the composition law N(xy) = "
     "N(x)N(y) visibly fails at dim 16 — 0 versus 4."),

    # ── the rung ladder ───────────────────────────────────────────────
    ("srmech.cascade.cd_promote", [
        ("1", "cd_promote([0,1,0,0], 8)"),
        ("2", "cd_project(cd_promote([0,1,0,0], 8))"),
        ("3", "cd_mult(cd_promote([0,1,0,0], 8), cd_promote([0,0,1,0], 8))"
              " == cd_promote(cd_mult([0,1,0,0], [0,0,1,0]), 8)"),
        ("4", "cd_promote([1], 8)"),
    ],
     "WHAT — promote an element UP the Hurwitz ladder ℝ↪ℂ↪ℍ↪𝕆↪𝕊 by the "
     "trivial SUBALGEBRA EMBEDDING x ↦ (x, 0), one or more rungs at a time. "
     "TOTAL, and a no-op when the target dim already matches. "
     "WHEN — reach for it before an operation that needs both operands at "
     "the same rung, or to check that a lower-rung answer is the higher "
     "rung's answer. What you would otherwise wrongly hand-roll is "
     "``list(x) + [0]*(dim-len(x))`` — which is the right bytes and the "
     "wrong claim, because the content of this op is that the padding is a "
     "SUBALGEBRA embedding: as measured here on the Q8 generators i and j, "
     "the product computed at ℍ and then promoted equals the product "
     "computed at 𝕆, so ℍ really is the top-4 of 𝕆 under the shared "
     "cocycle. "
     "SIBLINGS — ``cd_project`` is the exact inverse and the one that can "
     "refuse; ``carrier_ladder.poly_promote`` / ``qpoly_promote`` are the "
     "same MOVE on the VARIABLE ladder (Poly→BiPoly→TriPoly), a different "
     "ladder entirely — do not reach for one expecting the other; "
     "``cd_register(dim)`` chooses a rung at construction rather than "
     "moving between them.",
     "Zero-padding up is a subalgebra embedding, not a reshape: i·j "
     "computed in ℍ and then promoted equals i·j computed in 𝕆, exactly."),

    ("srmech.cascade.cd_project", [
        ("1", "cd_project([1, 0, 0, 0])"),
        ("2", "cd_project(cd_project([1, 0, 0, 0]))"),
        ("3", "cd_project(cd_promote([0, 1, 0, 0], 8))"),
        ("4", "_err(lambda: cd_project([0, 0, 0, 0, 0, 0, 0, 1]))[:214]"),
    ],
     "WHAT — project DOWN one doubling (dim → dim/2) by REALIFYING iff the "
     "higher imaginary half all vanishes; the inverse of ``cd_promote``. "
     "WHEN — reach for it to get back to the smallest rung that honestly "
     "holds a value, after promoting for an operation. THE BEHAVIOUR THAT "
     "MATTERS IS THE REFUSAL: if a higher component is genuinely present it "
     "RAISES and NAMES that component, rather than truncating. What you "
     "would otherwise wrongly hand-roll is ``x[:len(x)//2]``, which silently "
     "discards real content — that silent truncation is the defect this op "
     "exists to make unreachable. ONE CALL DROPS ONE DOUBLING: calls 1–2 "
     "walk the identity ℍ → ℂ → ℝ in two steps, so 𝕆 → ℝ is three calls, "
     "not one. "
     "SIBLINGS — ``cd_promote`` is the total inverse direction; "
     "``carrier_ladder.poly_project`` / ``qpoly_project`` are the "
     "VARIABLE-ladder peers, not this ladder; ``cd_register.element`` reads "
     "a register's element at its own fixed rung and never moves it.",
     "It realifies only when the higher half is genuinely zero and "
     "otherwise raises NAMING the offending component — the round trip with "
     "cd_promote is exact, and truncation is not reachable."),

    # ── the Hurwitz wall ──────────────────────────────────────────────
    ("srmech.cascade.sedenion_zero_divisor_witness", [
        ("1", "{k: ZD[k] for k in ('dim','x_form','y_form','x_norm_sq',"
              "'y_norm_sq','product_is_zero')}"),
        ("2", "cd_mult(ZD['x'], ZD['y'])"),
        ("3", "left_mult_is_invertible(ZD['x'])"),
        ("4", "sedenion_register(D=8192).is_navigable(ZD['x'])"),
    ],
     "WHAT — a CONCRETE sedenion zero divisor: x = e1 + e10 and "
     "y = e4 − e15, both of norm 2, whose product is exactly zero — found "
     "by searching OUR OWN multiplication table, not transcribed from the "
     "literature. Zero arguments; it is a constant of the algebra. "
     "WHEN — reach for it whenever you need the executable form of 'zero "
     "divisors first appear at 16 and never heal': as a fixture for a test, "
     "as the input that makes ``left_mult_kernel`` non-empty, or as the "
     "non-navigable composite direction a register refuses. What you would "
     "otherwise wrongly hand-roll is a brute-force search over dim-16 pairs "
     "— which is also the wrong shape of search, because zero divisors are "
     "MEASURE-ZERO (``left_mult_is_invertible`` returned True on 300/300 "
     "random dim-16 elements), so a random hunt finds nothing. "
     "SIBLINGS — ``is_division_algebra_dim`` states the same boundary as a "
     "predicate over dims; ``left_mult_kernel`` / "
     "``left_mult_is_invertible`` test an element you supply; "
     "``algebra_table(8, gammas=[1,-1,-1])`` exhibits zero divisors at dim "
     "8 instead, which is the honest way to get one BELOW the wall.",
     "The wall, executed and reusable: two norm-2 sedenions with product "
     "zero, and the same x is both the non-invertible left multiplier and "
     "the direction a sedenion register declines to navigate."),

    ("srmech.cascade.left_mult_kernel", [
        ("1", "len(left_mult_kernel(ZD['x'])), left_mult_kernel(ZD['x'])[0]"),
        ("2", "left_mult_kernel([1,0,0,0,0,0,0,1])"),
        ("3", "len(left_mult_kernel([1,0,0,0,0,0,0,1], table=SPLIT8))"),
        ("4", "left_mult_kernel([1,0,0,0,0,0,0,1], table=SPLIT8)[0]"),
    ],
     "WHAT — the exact-rational kernel basis of the linear map u ↦ x·u. "
     "Non-empty ⟺ x is a left zero divisor ⟺ multiply-by-x is non-injective "
     "⟺ no inverse map exists. Empty for every nonzero element of a "
     "division algebra (dims ≤ 8 on the definite ladder). "
     "WHEN — reach for it to EXHIBIT the failure, not just report it: the "
     "kernel vectors are the concrete u that x annihilates. Pass "
     "``table=`` and it becomes a zero-divisor witness on any algebra a "
     "table can express — split-𝕆 exhibits a 4-dimensional kernel at dim 8, "
     "where the shipped ladder has none at all. What you would otherwise "
     "wrongly hand-roll is building L(x) as a matrix and calling a "
     "null-space routine; that is what this op IS, over exact ℚ, and its C "
     "route (``srmech_qmat_nullspace`` over the table-composed L(x)) is "
     "exact at any magnitude. "
     "WITNESS HALF ONLY — it answers 'is THIS x a zero divisor'. FINDING a "
     "candidate is a different problem it does not solve, and a random "
     "search will not: see ``sedenion_zero_divisor_witness`` for a "
     "constructed one. "
     "SIBLINGS — ``left_mult_is_invertible`` is the bool peer (cheaper: it "
     "can take a modular-rank fast path on the shipped ladder); "
     "``sedenion_zero_divisor_witness`` supplies the x; "
     "``is_division_algebra_dim`` is the dimension-level statement.",
     "Non-empty kernel = no backward direction: 4 basis vectors for the "
     "sedenion witness, empty for 1+e7 on 𝕆, and 4 again for that same "
     "1+e7 once the split-𝕆 table is named."),

    ("srmech.cascade.left_mult_is_invertible", [
        ("1", "left_mult_is_invertible([1,0,0,0,0,0,0,1])"),
        ("2", "left_mult_is_invertible([1,0,0,0,0,0,0,1], table=SPLIT8)"),
        ("3", "left_mult_is_invertible(ZD['x'])"),
        ("4", "[(d, is_division_algebra_dim(d), cd_navmap_is_signed_permutation(d))"
              " for d in (4, 8, 16, 32, 64)]"),
    ],
     "WHAT — True iff u ↦ x·u is a bijection, i.e. iff a backward direction "
     "exists. Always True for nonzero x at dims ≤ 8 ON THE DEFINITE LADDER; "
     "False for a zero divisor at dim ≥ 16. "
     "WHEN — reach for it as the reversibility GATE before doing something "
     "that must be undoable: composite-direction navigation, an unbind, a "
     "round trip. Hand it a SPLIT table and False appears at dim 2 already, "
     "which is the honest answer — the ladder's own wall is not the only "
     "wall. What you would otherwise wrongly hand-roll is a determinant or "
     "a rank of a hand-built L(x): with a table this op takes the exact "
     "kernel route (C the whole way down, exact at any magnitude), which is "
     "a different C route, not a decline. "
     "READ THE FOURTH CALL CAREFULLY — invertibility and ADDRESSABILITY are "
     "different properties with different boundaries. Composition dies at "
     "dim 16 while ``cd_navmap_is_signed_permutation`` stays True at 16, 32 "
     "and 64, because zero divisors are built from SUMS of basis elements "
     "and addressing is about a SINGLE basis pair. "
     "SIBLINGS — ``left_mult_kernel`` returns the witnessing vectors this "
     "op reduces to a bool; ``is_division_algebra_dim`` answers for a "
     "DIMENSION where this answers for an ELEMENT; "
     "``SedenionRegister.is_navigable`` / ``CDRegister.is_navigable`` are "
     "this op wearing the register's clothes.",
     "The reversibility gate, and the fourth call is the disambiguation: "
     "composition fails past dim 8 while addressing (signed-permutation "
     "navmaps) survives at 16, 32 and 64."),

    ("srmech.cascade.is_division_algebra_dim", [
        ("1", "[(d, is_division_algebra_dim(d)) for d in (1, 2, 4, 8, 16, 32, 64)]"),
        ("2", "left_mult_is_invertible(ZD['x'])"),
        ("3", "cd_navmap_is_signed_permutation(16)"),
        ("4", "len(left_mult_kernel([1,0,0,0,0,0,0,1], table=SPLIT8))"),
    ],
     "WHAT — Hurwitz's 1898 theorem as a predicate: the normed division "
     "algebras over ℝ are exactly dims 1, 2, 4, 8. The boundary between the "
     "reversible interior (≤ 𝕆) and the open exterior (≥ 16). "
     "WHEN — reach for it for a cheap structural precondition when you have "
     "a dimension and no element. What you would otherwise wrongly hand-roll "
     "is ``dim in (1,2,4,8)`` — identical bytes, and still worth the call, "
     "because the op is the place the THEOREM is cited and the place the "
     "three adjacent boundaries are kept apart. "
     "IT IS A STATEMENT ABOUT THE DEFINITE LADDER'S DIMENSION AND NOTHING "
     "ELSE. It does not answer for a specific element (dim-16 elements are "
     "overwhelmingly invertible — 300/300 random ones were), it does not "
     "answer for a SPLIT algebra of the same dimension (split-𝕆 is dim 8 "
     "and has zero divisors, call 4), and it is NOT the addressing boundary "
     "(call 3: the navmap is still a signed permutation at 16). "
     "SIBLINGS — ``left_mult_is_invertible(x)`` is the per-element "
     "question; ``cd_navmap_is_signed_permutation(dim)`` is the per-rung "
     "ADDRESSING question, which answers True where this answers False; "
     "``inertia_signature`` answers a third, independent question about the "
     "quadratic form and certifies nothing about division.",
     "Hurwitz's dims 1/2/4/8 — and the three calls beside it keep the three "
     "boundaries apart: element-invertibility, addressability, and the "
     "split algebras that break at dim 8."),

    # ── addressing (the h-genome carrier) ─────────────────────────────
    ("srmech.cascade.cd_navmap", [
        ("1", "len(cd_navmap(64, 63))"),
        ("2", "[cd_navmap(64, 63)[i] for i in (0, 21, 42, 63)]"),
        ("3", "sorted(v[0] for v in cd_navmap(64, 63).values()) == list(range(64))"),
        ("4", "sum(1 for v in cd_navmap(64, 63).values() if v[1] < 0)"),
        ("5", "cd_navmap(8, 1)"),
    ],
     "WHAT — the whole signed pointer-advance permutation for "
     "right-multiply-by-e_j over dim slots: slot i ↦ (k, sign) where "
     "e_i·e_j = sign·e_k. Integer-only, with a JPL-clean C peer "
     "(``srmech_cd_navmap``) returning the identical map. "
     "WHEN — reach for it when you need the ROUTE for a whole register at "
     "once rather than one basis pair: a permutation table to apply, an "
     "audit of how many slots pick up a sign, an addressing plan. Grounded "
     "here on the attested Standard Genetic Code — 64 codons at 6-bit "
     "addresses, and j = 63 is the Rumer direction, so this single map is "
     "the T↔G / C↔A involution over the entire code with a Class-C sign "
     "attached to each of the 64 moves (32 of them negative). What you "
     "would otherwise wrongly hand-roll is a loop over "
     "``cd_basis_product(dim, i, j)`` — which is exactly what this is, "
     "already C-dispatched. "
     "SIBLINGS — ``cd_basis_product`` is one entry of this map; "
     "``cd_navigate`` APPLIES it to occupied (slot, sign) records and "
     "composes the signs; ``cd_navmap_is_signed_permutation`` checks the "
     "bijection+sign-domain premise over every j; "
     "``CDRegister.navmap`` / ``.navigate`` are the register-bound forms.",
     "One call gives the entire ×e_j route: at dim 64 with j = 63 it is the "
     "attested code's own Rumer involution, a bijection over all 64 codon "
     "slots, 32 of which carry a negative Class-C sign."),

    ("srmech.cascade.cd_navigate", [
        ("1", "cd_navigate(64, 63, [0, 21, 42, 63], [1, 1, 1, 1])"),
        ("2", "[codon(i) for i in (0, 21, 42, 63)]"),
        ("3", "[codon(i) for i in cd_navigate(64, 63, [0,21,42,63], [1,1,1,1])[0]]"),
        ("4", "cd_navigate(64, 63, *cd_navigate(64, 63, [0,21,42,63], [1,1,1,1]))"),
    ],
     "WHAT — route occupied ``(slot, sign)`` records through the ×e_j "
     "permutation and COMPOSE the Class-C signs: "
     "``out_signs[m] = signs[m] · s`` where "
     "``e_{slots[m]}·e_j = s·e_{out_slots[m]}``. Integer-only, C peer "
     "``srmech_cd_navigate``. No ``abs()`` — the sign is composed, never "
     "dropped. "
     "WHEN — reach for it to move a sparse occupancy, not a dense element: "
     "you have the few slots that are actually filled and you want them "
     "advanced with their orientation intact. This is the numeric core of "
     "``CDRegister.navigate``; the key strings ride alongside in the "
     "caller. "
     "WHAT THE FOURTH CALL TEACHES — navigating twice by e63 returns every "
     "codon to its own slot and brings the WHOLE occupancy back with sign "
     "−1, because e63·e63 = −1. Rumer is an order-2 involution on the INDEX "
     "lane and not on the sign lane; a hand-rolled index-only permutation "
     "would report an identity here and lose exactly that residue. "
     "SIBLINGS — ``cd_navmap`` is the map this applies (use it when you "
     "want the route itself); ``cd_basis_product`` is the per-pair atom; "
     "``cascade.net_chirality`` reduces a sequence of orientations to one "
     "net sign but knows nothing about slots.",
     "Sparse occupancy in, routed occupancy out with signs composed: "
     "TTT/CCC/AAA/GGG map to GGG/AAA/CCC/TTT, and going round twice "
     "restores the slots while leaving every sign flipped."),

    ("srmech.cascade.cd_navmap_is_signed_permutation", [
        ("1", "[(d, cd_navmap_is_signed_permutation(d)) for d in (2, 4, 8, 16, 32, 64)]"),
        ("2", "[(d, is_division_algebra_dim(d)) for d in (2, 4, 8, 16, 32, 64)]"),
        ("3", "left_mult_is_invertible(ZD['x'])"),
        ("4", "sorted(v[0] for v in cd_navmap(32, 17).values()) == list(range(32))"),
    ],
     "WHAT — THE STRUCTURAL INVARIANT ADDRESSING RIDES ON, checked rather "
     "than assumed: for EVERY direction j in [0, dim), is i ↦ (dest, sign) "
     "a bijection on [0, dim) with every sign in {+1, −1}? "
     "WHEN — reach for it before trusting an N-slot register past dim 8, "
     "and reach for it INSTEAD OF assuming that the Hurwitz wall bounds "
     "addressing. The first two calls are the whole point side by side: "
     "``is_division_algebra_dim`` goes False at 16 while this stays True at "
     "16, 32 and 64. Composition fails past the wall — for ~95% of generic "
     "pairs at dim 32 — and addressing is untouched, because zero divisors "
     "are built from SUMS of basis elements and this property is about a "
     "SINGLE basis pair. That is why ``cd_register(64)`` is legitimate. "
     "SCOPE — it verifies the bijection and sign-domain of the navmap AS "
     "COMPUTED BY the ``cd_basis_product`` cocycle. It does NOT "
     "independently re-derive e_i·e_j from a full Cayley–Dickson multiply; "
     "that cross-path check (cocycle vs ``cd_mult``, 4096/4096 pairs at dim "
     "64) lives in the Python test suite. The C peer "
     "``srmech_cd_navmap_is_signed_permutation`` returns the identical "
     "bool, so a bare-C host can verify its own address layer. "
     "SIBLINGS — ``cd_navmap`` is the map being checked; "
     "``left_mult_is_invertible`` is the COMPOSITION-side gate that "
     "genuinely fails past 8; ``is_division_algebra_dim`` is the "
     "dimension-level statement of that other boundary.",
     "Checked, not assumed: the addressing premise holds at 16, 32 and 64 "
     "— exactly the rungs where is_division_algebra_dim is False and the "
     "sedenion witness has no inverse."),

    ("srmech.cascade.cd_register", [
        ("1", "_reg1.working_block(), len(_reg1.carry_block())"),
        ("2", "_reg1.slots()"),
        ("3", "_reg1.navigate(63).slots()"),
        ("4", "_reg1.norm(), _reg1.read(21)"),
        ("5", "_sed_faithful()"),
    ],
     "WHAT — the GENERAL N-slot Cayley–Dickson addressable RBS-HDC "
     "register: ``dim`` named slots e0..e{dim−1} for any power of two in "
     "[1, 64], with e0..e7 the octonion reversible working block at EVERY "
     "rung and the remainder the carry/EC block. More slots buy ADDRESS "
     "SPACE, never a longer reversible word — the Hurwitz cap stays 7. "
     "WHEN — reach for it when a named-slot store must respect an algebra: "
     "writing is HDC (bind + nearest-codebook clean, classical), while "
     "``.navigate(j)`` is the address ↔ Cayley–Dickson homomorphism, so "
     "moving the register moves every stored key BY THE ALGEBRA. Grounded "
     "here on the attested Standard Genetic Code: dim 64 = one slot per "
     "codon at its own 16·b0+4·b1+b2 address, and ``navigate(63)`` applies "
     "the Rumer involution to the whole occupancy with signs attached. "
     "WHY IT IS LEGITIMATE PAST dim 8 — addressing rides on the basis "
     "product being a SIGNED PERMUTATION, which "
     "``cd_navmap_is_signed_permutation`` verifies at every rung; zero "
     "divisors are built from SUMS and break composition, not addressing. "
     "Capacity is D-bounded: a shortfall at fixed D is a capacity fact, not "
     "an algebra fact — sweep D. "
     "SIBLINGS — ``sedenion_register()`` is the dim-16 oracle this is gated "
     "against, and ``namespace='SEDENION'`` at dim 16 reproduces it "
     "BIT-EXACTLY (call 5) while the default 'CD16' namespace does not — "
     "that difference is the faithfulness gate, not a bug. "
     "``.element/.norm/.conjugate/.multiply`` are the method forms of "
     "``cd_mult`` / ``cd_norm_sq`` / ``cd_conjugate`` over the held signed "
     "element; ``.couple_working`` / ``.carry`` are the two OPT-IN layers "
     "(``coupling=`` / ``error_correction=``), whose free functions are "
     "``cd_couple_working`` / ``cd_carry``.",
     "A 64-slot register addressing the attested genetic code one codon per "
     "slot: navigate(63) is Rumer over the whole occupancy, and at dim 16 "
     "namespace='SEDENION' is byte-identical to the shipped "
     "sedenion_register while the default namespace is not."),

    ("srmech.cascade.sedenion_register", [
        ("1", "_sed1.slots()"),
        ("2", "_sed1.navigate(4).slots()"),
        ("3", "_sed1.is_navigable([0,0,0,0,1] + [0]*11)"),
        ("4", "_sed1.is_navigable(ZD['x'])"),
        ("5", "_sed_faithful()"),
    ],
     "WHAT — the dim-16 sedenion addressable RBS-HDC instrument: 16 slots "
     "e0..e15, with e0..e7 the ≤7-value REVERSIBLE working word "
     "(bit-exact ≤ 𝕆) and e8..e15 the Hamming EC/carry block. "
     "WHEN — reach for it when you specifically want the sedenion box, and "
     "keep reaching for it as the ORACLE: it deliberately remains an "
     "independent class rather than an n=16 alias of ``CDRegister``, "
     "because it is what the general register's faithfulness is gated "
     "against (call 5 — byte-identical materialisation). For any other "
     "rung, and for new work at 16, prefer ``cd_register(dim, …)``. "
     "THE GENUINELY-NEW SURFACE IS NAVIGATION, and calls 3–4 are the whole "
     "story: navigating by a SINGLE basis direction always works (signed "
     "permutation, every rung), while navigating by the COMPOSITE direction "
     "e1 + e10 — which is exactly ``sedenion_zero_divisor_witness()['x']`` "
     "— is refused, because that direction has no inverse. The Hurwitz "
     "horizon shows up as a navigability answer, not as a crash. "
     "SIBLINGS — ``cd_register(16, namespace='SEDENION')`` is the "
     "bit-exact general-register form; ``cd_navmap`` / ``cd_navigate`` are "
     "the free-function numeric core of ``.navigate``; "
     "``left_mult_is_invertible`` is what ``.is_navigable`` consults; "
     "``cd_couple_working`` / ``cd_carry`` are the free-function forms of "
     "``.couple_working`` / ``.carry``.",
     "Single-basis navigation always works; navigating by the zero-divisor "
     "direction e1+e10 is refused — and the general cd_register at dim 16 "
     "with namespace='SEDENION' materialises byte-identically to this."),

    # ── the two optional layers ───────────────────────────────────────
    ("srmech.cascade.cd_couple_working", [
        ("1", "cd_couple_working([8.0, 2.0, 128.0], dim=8)"),
        ("2", "cd_uncouple_working(cd_couple_working([8.0, 2.0, 128.0], dim=8))"),
        ("3", "len(cd_couple_working([5.0], dim=2)), len(cd_couple_working([], dim=1))"),
        ("4", "_err(lambda: cd_couple_working([1.0]*8, dim=16))"),
    ],
     "WHAT — bind ≤ min(dim, 8) − 1 real streams into ONE reversible "
     "working word: the canonical Class-M bind on the Cayley–Dickson "
     "register. The cap is DERIVED from Hurwitz, never a hardcoded 7 — dim "
     "2 couples 1 slot, dim 4 couples 3, dim 8 and every rung above it "
     "couples 7 (the e0..e7 octonion subalgebra of every higher rung), dim "
     "1 couples nothing. "
     "WHEN — reach for it to fold several real streams into one carrier you "
     "can still take apart. Grounded here on the attested Standard Genetic "
     "Code's own redundancy profile: synonymous single substitutions by "
     "codon position are 8, 2 and 128 out of 192 each — redundancy is "
     "CONCENTRATED in the third base, not spread — and those three "
     "measured streams bind into one quaternion word and come back exactly. "
     "MORE SLOTS DO NOT BUY A LONGER WORD (call 4): asking dim 16 for 8 "
     "streams raises rather than silently spilling, because reversibility "
     "is capped at 𝕆 and the overflow belongs in the EC/carry block via "
     "``cd_carry``. "
     "SIBLINGS — ``cd_uncouple_working`` is the exact inverse; "
     "``hypercomplex_couple`` is the general coupler underneath (this fixes "
     "``axis='diagonal'`` and derives the cap from the rung); ``hdc.bind`` "
     "is the BINARY-hypervector bind, a different carrier entirely; "
     "``cd_carry`` is where anything past the cap goes.",
     "The attested code's per-position synonymous counts (8, 2, 128) fold "
     "into one quaternion word and unbind exactly — and the cap is derived "
     "from the rung, so dim 16 still refuses an 8th stream."),

    ("srmech.cascade.cd_uncouple_working", [
        ("1", "cd_couple_working([8.0, 2.0, 128.0], dim=8)"),
        ("2", "cd_uncouple_working(cd_couple_working([8.0, 2.0, 128.0], dim=8))"),
        ("3", "len(cd_uncouple_working(cd_couple_working([1.0]*7, dim=8)))"),
        ("4", "cd_uncouple_working([])"),
    ],
     "WHAT — recover the streams bound by ``cd_couple_working``: apply the "
     "CONJUGATE twiddle and drop the anchor slot, returning the carrier's "
     "imaginary components (7 for an octonion word, 3 for a quaternion "
     "word). "
     "WHEN — reach for it as the read half of the working word. Recovery is "
     "exact to float round-off by the division-algebra identity "
     "T̄·(T·q) = ‖T‖²·q, which is precisely why the working word stops at 𝕆: "
     "past the Hurwitz wall that identity has no inverse to lean on. The "
     "example round-trips the attested genetic code's per-position "
     "synonymous-substitution counts (8, 2, 128) and gets them back to ~1e-15. "
     "What you would otherwise wrongly hand-roll is a conjugate-multiply and "
     "a slot drop — the same op, minus the derived cap and the empty-in / "
     "empty-out boundary. "
     "SIBLINGS — ``cd_couple_working`` is the bind; "
     "``hypercomplex_couple(word, sigma=-1)`` is the general form this "
     "specialises (it returns the FULL carrier including the anchor slot, "
     "where this drops it); ``hdc.bind`` is self-inverse on binary "
     "hypervectors and needs no separate unbind at all — do not assume the "
     "same shape across the two carriers.",
     "The exact inverse of the bind: the three attested codon-position "
     "redundancy counts come back from one quaternion word, and empty in is "
     "empty out."),

    ("srmech.cascade.cd_carry", [
        ("1", "cd_carry([0, 1, 1, 1], n=3)"),
        ("2", "cd_correct(cd_carry([0, 1, 1, 1], n=3))"),
        ("3", "len(cd_carry([1]*11, n=4))"),
        ("4", "_err(lambda: cd_carry([0, 1, 1], n=3))[:96]"),
    ],
     "WHAT — encode overflow bits (everything past the reversible working "
     "set) into a Hamming(2ⁿ−1) single-error-correcting GF(2) codeword. "
     "Lean-ALU XOR only: GF(2) add is parity is XOR — no float, no libm, no "
     "``abs()``. "
     "WHEN — reach for it for whatever will not fit in the ≤7-value working "
     "word. THE EC AXIS IS INDEPENDENT OF THE REGISTER'S dim: block size is "
     "set by n (codeword 2ⁿ−1, data 2ⁿ−1−n), NOT by the slot count, so a "
     "dim-64 register and a dim-16 register carry identically. The example "
     "encodes a dinucleotide root of the attested genetic code — 2 bases × "
     "2 bits = exactly Hamming(7,4)'s payload width — so a single-bit "
     "transcription error in the root is recoverable. "
     "SIBLINGS — ``cd_correct`` is the read; ``hamming_encode`` / "
     "``hamming_syndrome`` / ``hamming_decode_correct`` are the same code "
     "as free primitives (this is ``hamming_encode`` with the register's "
     "default n=3, the octonion's own Fano plane), so do not implement a "
     "third Hamming; ``cd_couple_working`` is the OTHER, reversible layer — "
     "coupling is lossless and capped at 7, carrying is lossy-free but "
     "spends parity bits.",
     "Overflow past the ≤7 working word becomes a Hamming codeword: the "
     "4-bit dinucleotide root [0,1,1,1] = 'CG' encodes to 7 bits and decodes "
     "back, on an axis set by n and not by the register's dim."),

    ("srmech.cascade.cd_correct", [
        ("1", "cd_carry([0, 1, 1, 1], n=3)"),
        ("2", "cd_correct([0, 0, 0, 1, 1, 1, 1])"),
        ("3", "cd_correct([0, 0, 0, 1, 0, 1, 1])"),
        ("4", "cd_correct([1, 0, 0, 1, 1, 1, 1])"),
    ],
     "WHAT — locate and correct a single-bit error in an EC-block codeword "
     "and recover the carried payload: "
     "``{'data', 'error_position' (1-indexed, 0 = clean), "
     "'corrected_codeword'}``. "
     "WHEN — reach for it as the read half of ``cd_carry``. "
     "SINGLE-ERROR-CORRECTING, minimum distance 3 — a clean or "
     "single-error word recovers exactly, and the example shows all three "
     "cases: clean (position 0), a flipped DATA bit (position 5), a flipped "
     "PARITY bit (position 1). Both flips recover the same payload, which "
     "is the property that makes the code useful and the reason "
     "``error_position`` is worth returning rather than swallowing. Two "
     "errors are OUT OF SCOPE and will mis-correct silently — that is the "
     "code's contract, not a defect. "
     "SIBLINGS — ``cd_carry`` is the encode; ``hamming_syndrome`` returns "
     "just the position, ``hamming_decode_correct`` is this op's free-"
     "function twin — the Hamming code ships once and is reached three "
     "ways, so do not add a fourth; ``cd_uncouple_working`` is the read of "
     "the OTHER layer (reversible, no parity, capped at 7).",
     "Clean, data-bit flip and parity-bit flip all recover the same 4-bit "
     "payload, with the 1-indexed error position reported rather than "
     "swallowed."),

    # ── the continuous coupler ────────────────────────────────────────
    ("srmech.cascade.hypercomplex_couple", [
        ("1", "hypercomplex_couple([8.0, 2.0, 128.0])"),
        ("2", "hypercomplex_couple(hypercomplex_couple([8.0, 2.0, 128.0]), sigma=-1)"),
        ("3", "[round(v, 12) for v in hypercomplex_couple([1.0, 1.0, 1.0])]"),
        ("4", "[round(v, 12) for v in hypercomplex_couple([1.0, -1.0, 1.0])]"),
    ],
     "WHAT — the bidirectional (σ, θ, μ) hypercomplex coupler: pack "
     "``streams`` into the imaginary slots of a quaternion (≤3) or octonion "
     "(4–7) carrier and apply T = exp(σ·μ·θ). Where ``quaternion_dft`` / "
     "``octonion_dft`` CARRY N streams along named single axes, this "
     "COUPLES them. "
     "WHEN — reach for it to bind several real streams reversibly, and "
     "reach for the DIAGONAL axis (the default μ = (i+j+k)/√3 for ℍ, "
     "(Σeₙ)/√7 for 𝕆) when you want a COHERENCE DETECTOR: a diagonal fold "
     "sends coherent streams into the real/anchor channel (calls 3–4 — "
     "[1,1,1] lands entirely on the anchor at −√3 with all three imaginary "
     "slots vanishing to 0.0 at 12 decimals, while [1,−1,1] leaves real "
     "residue in them). "
     "REVERSIBILITY IS GUARANTEED ONLY UP TO 𝕆 — bind with sigma=+1, unbind "
     "with sigma=−1 (the conjugate twiddle), recovered by the "
     "division-algebra identity x̄·(x·y) = ‖x‖²·y; sedenion zero divisors "
     "break it, which is why the cap is 7 streams and not more. "
     "SIBLINGS — ``cd_couple_working`` is this op with axis fixed to "
     "diagonal and the cap derived from a register rung; "
     "``cd_uncouple_working`` is its unbind with the anchor slot dropped; "
     "``hypercomplex_exp`` is the literal exp(μθ) twiddle if you want the "
     "rotor itself rather than an applied coupling; ``hdc.bind`` is the "
     "binary-hypervector bind and is self-inverse, which this is not.",
     "Bind then unbind recovers the attested codon-position counts "
     "(8, 2, 128) exactly, and the diagonal axis makes the anchor slot a "
     "coherence detector: [1,1,1] folds entirely onto it, [1,−1,1] does "
     "not."),

    ("srmech.cascade.hypercomplex_exp", [
        ("1", "hypercomplex_exp(0.7853981633974483, 1)[:2]"),
        ("2", "[round(float(v), 12) for v in hypercomplex_exp(0.7853981633974483, 3)]"),
        ("3", "round(float(cd_norm_sq(list(hypercomplex_exp(0.7853981633974483, 7)))), 15)"),
        ("4", "[round(float(v), 12) for v in"
              " cd_mult(list(hypercomplex_exp(1.5707963267948966, 1))[:4], [0,1,0,0])]"),
    ],
     "WHAT — the literal exp(μθ) = cos θ + μ·sin θ unit hypercomplex "
     "twiddle as an exact Q61 8-tuple. μ is the equal-weight UNIT "
     "pure-imaginary over the first ``k_axes`` octonion axes, so "
     "k_axes ∈ {1, 3, 7} selects the ℂ / ℍ / 𝕆 rung. Returns "
     "[cos θ, sin θ/√k × k, 0 × (7−k)] with |q| = 1 (call 3: 1.0 to 15 "
     "decimals at k = 7). "
     "WHEN — reach for it when you want the ROTOR itself, to feed into "
     "``cd_mult`` and rotate a value IN the algebra, then project once — "
     "which beats composing scalar phase-binds on an already-projected "
     "carrier. Call 4 does the smallest honest version: exp(iπ/2) times e1 "
     "is −1, in ℍ, through the shipped product. "
     "WHAT YOU WOULD OTHERWISE WRONGLY HAND-ROLL — ``math.cos``/``math.sin`` "
     "into a float 4-tuple. srmech has no libm and takes no float path here: "
     "this is fixed-width Q61, no bignum, with a byte-exact C peer "
     "``srmech_hypercomplex_exp_q61``. "
     "SIBLINGS — ``hypercomplex_couple`` APPLIES a twiddle of this family to "
     "streams (use it when you want the coupling, not the rotor); "
     "``qm.quaternion.quaternion_exp`` / ``qm.octonion.octonion_exp`` are "
     "the general (non-unit-μ) exponentials at fixed rungs; "
     "``rational.cos``/``sin`` are the Class-N scalar series underneath; "
     "``the_one`` builds the whole 1+3+7 ladder of such epicycles at once "
     "rather than one rotor.",
     "One rotor, three rungs: k_axes 1/3/7 gives the ℂ/ℍ/𝕆 unit twiddle as "
     "exact Q61 with |q| = 1, and multiplying e1 by exp(iπ/2) through "
     "cd_mult returns −1."),

    # ── the generator ─────────────────────────────────────────────────
    ("srmech.cascade.the_one", [
        ("1", "the_one(1, 1, 4)"),
        ("2", "the_one(1, 1, 4).partition, the_one(1, 1, 4).imag_dims,"
              " the_one(1, 1, 4).grammar_slots"),
        ("3", "the_one(1, 1, 4, w=(1, 0, 1)).unwrapped_phase()"),
        ("4", "[(w, the_one(1, 1, 4, w=w).spinor_sign,"
              " the_one(1, 1, 4, w=w).sigma_effective())"
              " for w in ((0,0,0), (1,0,1), (1,1,1))]"),
        ("5", "the_one(-1, 1, 4).sigma_effective()"),
    ],
     "WHAT — the One, S(σ, θ, w): the single generator of the 1+3+7+3 = 14 "
     "substrate, built as the Hurwitz ladder "
     "⨁ₙ (ℝ·1 ⊕ σ·e^{Îₙθ}·Im 𝔸ₙ) over 𝔸₁ = ℂ, 𝔸₂ = ℍ, 𝔸₃ = 𝕆 — three "
     "Blocks of real dims 2 + 4 + 8 = 14 whose imaginary dims 1 / 3 / 7 "
     "carry A, then I/C/J, then D/E/F/G/K/L/M, and whose three ℝ·1 reals "
     "are the +3 grammar slots B/H/N. "
     "WHEN — reach for it when you want the substrate's partition as an "
     "OBJECT rather than a diagram: σ is Class-K sign ∘ Class-C apply "
     "(never ``abs()``), (θ_num/θ_den) is the exact-rational Class-N "
     "epicycle, and w = (Saros, Metonic, Callippic) is the METACYCLE "
     "winding triad — the Antikythera back-panel dials, which is where the "
     "+3 grammar anchors come from. Call 4 is the load-bearing one: the "
     "spinor sign is (−1)^Σw, so an odd total winding flips "
     "``sigma_effective()`` even with σ = +1 — the two chiralities are one "
     "object read at different windings, not two objects. "
     "WHAT YOU WOULD OTHERWISE WRONGLY HAND-ROLL — a float "
     "cos/sin epicycle. This is exact rational throughout (the float "
     "``to_matrix()`` / ``to_numpy()`` realisations are the opt-in "
     "scientific tier). "
     "SIBLINGS — ``hypercomplex_exp`` is ONE rotor at ONE rung, where this "
     "is the whole 1/3/7 ladder; ``winding_fold`` produces the w this "
     "consumes by dividing an accumulated angle into turns + residue; "
     "``cd_promote`` moves an ELEMENT up the same ladder this TILES; "
     "``qm.hurwitz.hurwitz_planes`` reads the plane structure of the same "
     "tower.",
     "The 14 = 1+3+7+3 partition as one object, with the Antikythera "
     "metacycle triad as its winding: spinor_sign = (−1)^Σw, so w = (1,1,1) "
     "flips sigma_effective to −1 while σ is still +1."),
]


def _err(fn):
    """Run ``fn`` and return ``'<ExcType>: <message>'`` — a REAL raise
    captured as text, so an example can ship the refusal an op is designed
    to make without the probe dying on it."""
    try:
        fn()
    except Exception as exc:                                # noqa: BLE001
        return f"{type(exc).__name__}: {exc}"
    raise AssertionError("expected a raise, got none")


def probe_worked(rows=None):
    """Execute every WORKED row and return its ``{name: entry}`` curation.

    Each source is ``eval``'d in a fresh copy of :func:`_worked_ns`; the
    real ``repr`` of the result becomes that step's output. A repr longer
    than :data:`_WORKED_MAX` RAISES — narrowing the expression is the fix,
    never truncating, because a truncated output is a fabricated one.
    """
    rows = WORKED if rows is None else rows
    ns = _worked_ns()
    ns["_err"] = _err
    # Shared register fixtures the register rows read (built once so the
    # example is a coherent SESSION, not four unrelated constructions).
    reg1 = ns["cd_register"](64, D=8192)
    for slot, key in ((0, "TTT"), (21, "CCC"), (42, "AAA")):
        reg1.write(slot, key)
    ns["_reg1"] = reg1
    sed1 = ns["sedenion_register"](D=8192)
    sed1.write(1, "e1")
    sed1.write(10, "e10")
    ns["_sed1"] = sed1

    def _sed_faithful():
        """Materialised-byte comparison of the three registers at dim 16."""
        same = ns["cd_register"](16, D=8192, namespace="SEDENION")
        other = ns["cd_register"](16, D=8192)
        for r in (same, other):
            r.write(1, "e1")
            r.write(10, "e10")
        ref = sed1.materialize()
        return {"namespace='SEDENION'": same.materialize() == ref,
                "namespace default 'CD16'": other.materialize() == ref}

    ns["_sed_faithful"] = _sed_faithful

    out = {}
    for name, calls, expl, why in rows:
        inp, outp = {}, {}
        for label, src in calls:
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                res = eval(src, ns)                      # noqa: S307 dev tool
            rendered = repr(res)
            if len(rendered) > _WORKED_MAX:
                raise SystemExit(
                    f"{name} step {label}: output is {len(rendered)} chars "
                    f"(> {_WORKED_MAX}). NARROW THE EXPRESSION — truncating "
                    f"would ship a fabricated output.\n  {src}\n  {rendered[:120]}…")
            inp[label] = src
            outp[label] = rendered
        out[name] = {"explanation": expl,
                     "example": {"input": inp, "output": outp, "why": why}}
        print(f"OK  {name}  ({len(calls)} calls worked)")
    return out


def merge_curated(existing, probed):
    """``existing`` curation with ``probed`` rows laid OVER it, per field.

    The whole point is what it does NOT do: no key in ``existing`` is ever
    dropped because ``probed`` (i.e. ``CENTRAL``) fails to mention it. That
    wholesale-rebuild was the rc291 #T916 defect on this side.
    """
    merged = {k: dict(v) for k, v in existing.items()}
    for name, entry in probed.items():
        merged.setdefault(name, {}).update(entry)
    return merged


def main():
    out = {}
    for name, (args, kwargs), expl in CENTRAL:
        try:
            fn = _resolve(name)
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                res = fn(*args, **kwargs)
            inp = {f"arg{i}": _rs(a) for i, a in enumerate(args)}
            inp.update({k: _rs(v) for k, v in kwargs.items()})
            entry = {}
            if expl:
                entry["explanation"] = expl
            entry["example"] = {"input": inp, "output": _rs(res)}
            out[name] = entry
            print(f"OK  {name}  -> {_rs(res)[:60]}")
        except Exception as e:  # noqa: BLE001
            print(f"SKIP {name}: {type(e).__name__}: {e}")
    # The WORKED rows are NOT wrapped in try/except: a single-call probe
    # that fails degrades to a signature snippet, but a worked sequence
    # that fails has nothing honest to fall back to, so it must be loud.
    out.update(probe_worked())
    import json
    # MERGE over the existing curation — never rebuild the file from CENTRAL
    # alone (rc291 #T916). CENTRAL is a probe list, not the curation SSoT: most
    # curated entries (the genome / plasmid / text explanations) are not in it
    # and a wholesale rewrite would delete every one of them.
    try:
        from srmech.introspect._tool_docs_curated import CURATED as _existing
    except Exception:  # noqa: BLE001 — first run / syntactically broken file
        _existing = {}
    merged = merge_curated(_existing, out)
    preserved = sorted(set(merged) - set(out))

    lines = ['"""_tool_docs_curated.py — HAND-CURATED introspection docs for the',
             "central ops (rc240 #T838). Merged OVER the docstring-seeded floor by",
             "tools/gen_tool_docs.py (curation wins). Every EXAMPLE here is a REAL",
             "executed result (probed by tools/gen_curated_probe.py), never typed.",
             "",
             "THIS is the file to hand-edit. ``_tool_docs.py`` is GENERATED —",
             "text written there is destroyed by the next tools/gen_tool_docs.py",
             "run, which is what happened to the genome/plasmid explanations",
             "between rc274 and rc290 (rc291 migrated them here). The generator",
             "now refuses to write when it would clobber prose it cannot",
             're-derive from a docstring, so that failure mode is loud."""',
             "from __future__ import annotations", "",
             "from typing import Any, Dict", "",
             "CURATED: Dict[str, Dict[str, Any]] = {"]
    for name in sorted(merged):
        lines.append(f"    {json.dumps(name)}: "
                     f"{json.dumps(merged[name], sort_keys=True, ensure_ascii=False)},")
    lines.append("}")
    lines.append("")
    dest = Path(__file__).resolve().parent.parent / "srmech" / "introspect" / "_tool_docs_curated.py"
    dest.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"\nwrote {dest} — {len(merged)} curated entries "
          f"({len(out)} refreshed by this probe, {len(preserved)} preserved)")


if __name__ == "__main__":
    main()
