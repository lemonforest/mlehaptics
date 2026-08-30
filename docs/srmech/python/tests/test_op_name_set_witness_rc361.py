"""rc361 (`#T1034`) — the op-name-SET witness: the instrument a rename trips.

WHY THIS EXISTS. ADR-0010 declustering moves ~73 modules between top-level
namespaces. Before rc361 the tree had **no gate that detects a rename**. It had
54 test files / 60 assertions pinning the op COUNT, and a count is the wrong
quantity: a rename relocates names and leaves cardinality untouched. Measured
2026-07-29 by simulating this ADR's own example move (``rational`` from
``srmech.amsc`` to ``srmech.math`` — the move rc373 has since actually made):
28 of 516 dotted names relocate, the total stays **516**, and every one of those
60 pins stays GREEN.

That is an **EMPTY** null about the pins, not a defect — `len(...)` measures
cardinality and measures it correctly. It is a real gap about the arc. This file
closes it by pinning the SET, not the size.

⚠️ THE MANIFEST IS HAND-COMMITTED ON PURPOSE — DO NOT WIRE IT INTO CODEGEN.
`tests/registered_op_names.txt` is NOT emitted by `tools/regen_all.py` or by
`tools/codegen_manifest.py`, and `test_the_manifest_is_not_codegen_emitted`
below asserts that it stays that way. The reason is the whole point of the
instrument: a rename arc runs `python tools/gen_*.py` as a matter of course, so
a codegen-emitted manifest would be rewritten by the very change it is meant to
detect and go green unconditionally — reproducing the exact failure mode
(a probe that cannot come out otherwise) that this file was written to fix.

TO CHANGE THE NAME SET DELIBERATELY, two edits are required, in the same commit:
  1. rewrite the manifest:
       python -c "from srmech.introspect.tool_schema import get_tool_schema; \
                  ns=sorted(e.name for e in get_tool_schema().tools); \
                  open('tests/registered_op_names.txt','w',encoding='utf-8', \
                       newline='\\n').write('\\n'.join(ns)+'\\n')"
  2. update `EXPECTED_NAME_SET_SHA256` and `EXPECTED_N` below to what the failure
     message prints.
Needing TWO edits is deliberate: a careless single-file regen cannot silently
pass, because the digest is pinned in source and the names are pinned on disk.
"""
from __future__ import annotations

from pathlib import Path

from srmech.amsc.format import sha256_bytes
from srmech.introspect.tool_schema import get_tool_schema

MANIFEST = Path(__file__).resolve().parent / "registered_op_names.txt"

#: Registered public-callable count, srmech-owned. Pinned here only so the
#: failure message can say "N -> N+1" instead of dumping every name; the SET
#: below is the actual contract.
#: (This illustrated the message with the frozen literals "516 -> 517" from
#: rc361 until rc410 (`#T1085`) — stale by 40 ops, in a comment whose only job
#: was to show the CURRENT value, sitting two lines above the real one. Written
#: symbolically now so it cannot go stale a second time.)
EXPECTED_N = 700  # rc461 (part 3, `#T1183`): 695 -> 700, the AFFINE / KAC-WALTON layer -- five srmech.math.weight_lattice ops closing a census that returned ZERO across ten terms (affine Weyl, level, alcove, Kac-Walton, Verlinde, S-matrix, modular data, fusion ring, truncation, orbit Lie algebra). THE FRAMING: Racah-Speiser is a SIGNED INTEGER COUNT, not an integral; the affine case adds exactly ONE reflection to the classical fold rc460 shipped. The infinite affine Weyl group is handled by an ITERATIVE fold with an EXACT INTEGER TERMINATION CERTIFICATE, never by enumeration: in affine labels every generator collapses to a_j -> a_j - a_i*C^aff_ij, the monovariant sum-of-squares falls by EXACTLY quantum*a_i per step (2*kappa for A2, 4*kappa for A1, both DERIVED from the affine Cartan), a step fires only when a_i < 0 so the drop is negative and integer-quantised, and Q >= kappa^2/(r+1) gives a step bound computed BEFORE the loop. The per-step law is checked on EVERY step. integrable_weights (Class E; marks DERIVED from the highest root -- D4's (1,2,1,1) is why level 1 has FOUR primaries, and the centre P/Q comes off the Cartan's Smith normal form as (2,2), the Klein four-group, DERIVED not recalled). alcove_fold (Class K; A1/A2 only, and the MATHEMATICS enforces the scope -- _monovariant_quantum raises where the collapse identity fails, so the refusal a D4 caller sees is the termination reason). affine_fusion_multiplicities (Class K; Kac-Walton, deliberately NOT named fusion_multiplicities because srmech.math.groups.fusion_multiplicities is the FINITE-GROUP Class-L object and coincidence at level 1 is not identity; non-integrable operands RAISE, a guard added because two of four such pairs previously returned an empty set SILENTLY). affine_modular_s_matrix (Class I; the Kac-Peterson finite Weyl sum exact over Z[zeta_e], carries D4 because it runs no fold -- the ring is MEASURED by gcd-reducing the exponents and lands on zeta_14, not the zeta_28 of the raw scaling nor the zeta_7 of a kappa reading, and the normalisation is READ off A*A^dagger = n*I rather than substituted from kappa^rank*|P/Q|, which becomes a cross-check). verlinde_fusion_multiplicities (Class I; the SAME coefficients by a disjoint instrument -- 199 operand pairs agree with the fold route, and it reaches D4 where the fold refuses, returning the Klein-four group ring). Zeta values ride the INTEGER coordinate-vector dialect character_table already mints and zeta_mul already reads: no new carrier TYPE, no C symbol, ABI stays 24.  # was: 695    # rc461 (part 2): 692 -> 695, the AUTOMORPHISM-side triad -- the frame the DERIVATION pair reads in, given an address and a detector. epq_frame_address (Class A, srmech.physics.qm.so8): the shared E_pq 28-dim frame gets a content address covering BOTH halves of what makes it that frame -- the pair ORDER and the octonion multiplication TABLE. Pinned by DECLARATION plus that address, never a frame= parameter: rc460 ruled a single-value pin no producer can vary MINTS A DIALECT. so8_bracket_certificate (Class D + Class C): phi([X,Y]) == [phi X, phi Y] over all C(28,2) = 378 generator pairs, on the INTEGER ALU (2*tau and 2*S_B are integer, so the exact predicate is d*M([X,Y]) == [MX,MY]). It is also the only shipped op that can SEE a wrong-frame matrix: measured, P^-1 S_B P fails 161/378 and P^-1 tau P 214/378, against 0/378 for both generators read in their own frame -- while triality_frame_action ANSWERS P^-1 S_B P with the identity permutation, because it is still an involution with trace 14 that preserves the Cartan span. g2_membership (Class D + Class K + Class C + Class A): Aut(O) = G2 decided by octonion multiplicativity over the 64 basis pairs, with the commutator verdict shipped as fixed_mod_center and NOT as anything spelling 'fixed' -- Ad(-I) = I_28 exactly, so the commutators see PSO(8) and cannot separate g from -g, and 1344 monomial non-automorphisms pass both. BOTH residuals are computed and the impossible cell RAISES as a theorem check on the shipped tau / S_B, proved firable by fault injection. No new carrier TYPE (Q leaves as int pairs), no C symbol; ABI stays 24.  # rc461: 690 -> 692, the DERIVATION pair -- two ops that each replace a claim the tree ASSERTED with one it MEASURES. triality_frame_action (Class D + Class C, srmech.physics.qm.triality): which of 8v/8s/8c a 28x28 so(8) automorphism sends each frame to, read off the matrix in exact Q. Through rc460 that was a pair of hard-coded module dicts whose only independent derivation lived in a note script and a test -- neither of which ships -- while triality_rep_dictionary emitted the value into describe(), the MCP tool list and the compiled-in C registry. Cheap because all three shipped maps PRESERVE the standard Cartan span exactly (measured, entries in {-1/2, 0, +1/2}), so the read is 4x4 exact-rational arithmetic: 5.2 ms against ~4.3 s for one exact companion solve. The 8s/8c split is decided by the PARITY of the half-integer weights' minus signs, and that parity is READ off the shipped S_B / S_C (8s odd, 8c even), not chosen. cyclic_laplacian_spectrum (Class L + Class I + Class N, srmech.math.laplacian): the cycle graph's Laplacian spectrum as elements of Q(zeta_n) rather than as floats -- the exact peer of generalized_ngon's example="ordinary_k", which reads the SAME graph C_2k through jacobi_eigvals. Neither op mints a carrier TYPE (Q leaves as int pairs), so no discriminator widening, no C symbol; ABI stays 24.  # rc460: 687 -> 690, the exact A2 WEIGHT-LATTICE stratum -- three srmech.math.weight_lattice ops in a NEW module that is a PEER of groups.py, not a part of it. groups' instrument is a count off a Cayley table, indexed by ELEMENTS; this one is a SIGNED count off a lattice, indexed by WEIGHTS. dominant_weight (Class A, the label+gauge content-address mint -- the Cartan matrix is invariant under the diagram flip, so it cannot tell 3 from 3bar, and the two bits it does not fix ride INSIDE the address); weight_multiplicities (Class E, the Freudenthal weight system over a 3-scaled Gram matrix so the recursion never leaves Z -- explicitly NOT Class K, the recursion is sign-free); tensor_product_multiplicities (Class K, the Racah-Speiser +-1 Weyl ledger -- explicitly NOT Class L, it builds no eigenbasis, which is the rc's load-bearing correction: Lie fusion is a SIGNED INTEGER COUNT, not "a convolution of orbital measures against Haar"). No new carrier TYPE (plain int / tuple-of-int, QMat for the six integer 2x2 Weyl reflections), so no discriminator widening, no C symbol; ABI stays 24. The same rc closes B1, the replicated silent wrong answer -- character_table now emits cayley_sha256 and the tier-4 consumers BIND on it -- which adds no op.  # rc458: 679 -> 687, the representation stratum tier 4 -- the rho stratum: eight srmech.math.groups ops. zeta_mul (Class I, the public promotion of the private ZZ[zeta_e] ring kernel rc456 promised and rc457 deferred -- the first registered exact zeta-vector atom); permutation_representation (Class L, mints rho: G -> GL(V) as a REP PAYLOAD dict -- the object whose absence rc457's central_idempotents ruling recorded, now retired); character_of (the trace bridge back to tiers 2-3); decompose_representation (the irrep-eigenbasis projection); isotypic_projector (THE op rc457 declined -- the rho(e_chi) evaluation central_idempotents' docstring promised the caller would perform, now shipped); tensor_product_representation (Class M, argued: decompose/isotypic ARE the unbind fusion_multiplicities said was missing); direct_sum_representation (Class B, blocks recoverable); intertwiner_space (the Schur readout over the exact-Q QMat.nullspace, C-backed through its carrier). All Python-first under the ADR-0009 noted-disparity ruling; no new C symbol; ABI stays 24.  # rc457: 676 -> 679, the representation stratum tier 3 -- the FINAL slice: three srmech.math.groups readouts over the character_table payload dict (frobenius_schur_indicator, Class K three-point pin at the reality phase boundary; fusion_multiplicities, Class L projection onto the class-algebra eigenbasis; central_idempotents, Class L -- the isotypic ruling shipped object (a), the primitive central idempotents, under the name of what it actually is, because object (b) needs rho(g) matrices srmech does not carry). Each body's only registered-op call is the Class-A content address, so all three are forced-order singletons; ABI stays 24; the _zeta_mul public promotion is deliberately deferred (its own rc must rule on the srmech_riemann_theta_cyc_mul dispatch).  # rc456: 666 -> 676, the representation stratum tiers 1-2 -- nine srmech.math.groups ops (cyclic_group / semidirect_product / conjugacy_classes / derived_subgroup / quotient_group / abelianization / cayley_graph / character_table / irrep_dimensions) + srmech.math.poly.cyclotomic_polynomial. The founding measurement: the tree scored 0/10 on the representation stratum and an external oracle had to be reached for; C7xC3 (direct) is abelian with degrees [1]*21 while C7:C3 (semidirect) carries degrees [1,1,1,3,3] at the same order -- Class K acting BETWEEN two Class-I operands is the non-abelianiser, and semidirect_product is that coupling made into an operand. All ten are composition_of_c over already-C-dispatched kernels; ABI stays 24.  # rc452 (gh #1653): 663 -> 666, the cascade-chain registration triple -- srmech.amsc.descriptor.render_template (Class F; klein4_from_one's declared serialisation step), srmech.amsc.format.sha256_raw (Class A raw-digest companion; encode_loe_content's mint stride) and srmech.signal_processing.mint_vector (the counter-mode SHA-256 HDC mint, previously registered under NO spelling at all). All three are named by shipped [[cascade.chain]] step lists, and the C run loop's cr_args_keyset_ok refuses BY DESIGN to dispatch an op with no ToolEntry -- so these registrations are the hard prerequisite for closing those chains' C-projection gap, not documentation after the fact.  # rc442 (local task T1150): 661 -> 663, the GROUP/v20 nesting pair (genome_groups walks a strand's nesting and reports every group; genome_group mints one). Both were ADDED to genome.__all__ in the same rc, which is what makes registering them mandatory rather than optional -- test_registry_completeness_rc416 fails a public __all__ callable that resolves to no ToolEntry, and taking the allowlist route instead would raise a down-only ceiling, i.e. record a regression rather than fix one.  # rc437 (local task T1142): 656 -> 661, the CD division PAIR (cascade.cd_left_divide / cd_right_divide -- two named Class-C ops, never one with a side= flag, because past dim 2 they are different maps) + the (Z/2)^n Walsh-Hadamard transform (cascade.walsh_hadamard.walsh_hadamard_transform -- a different GROUP from exact_dft's cyclic Z/N, exact in plain integers because the cube's characters are +-1). Plus the two REGULAR REPRESENTATIONS the pair inverts: right_mult_matrix is new (nothing on the CD ladder held R(x)) and left_mult_matrix had carried an OPEN_REGISTRATION gap row since rc160 -- registering both CLOSES that gap and is what lets the division ops resolve to a registered sub-op at depth 1 instead of sitting in the composes residual.  # rc436 (local task T1141): 655 -> 656, cascade.octonion_associator_support -- the associator SUPPORT as a SET + the Fano predicate that reproduces it. The COUNT 168 was already pinned at five sites (associator 512-344, cd_cycle_holonomy 168/512, oct_mult 168/343, octonion_frame_read, group_algebra_table) and is REPRODUCED, not moved; the SET and the closed form are what is new.  # rc427 (local task T1130): 649 -> 655, the ARROW + CENSUS registration (math.cyclic.mod_mul_arrow + cascade.finite_semiflow / conjugacy_census / reversal_law_census / anti_automorphism_witnesses / dihedral_group; unit_loop + loop_invariants gained table= and add NO row)  # rc425 (local task T1112): 612 -> 649, the 37 remaining Path-A closed_form_ops (fft / ifft / pi_cascade excluded as bit-exact duplicates of ops the registry already ships)  # rc424 (local task T1113): 605 -> 612, the 6 srmech.music relational ops + the first registration of srmech.signal_processing.music_doa  # rc422 (local task T1123): 598 -> 605, the centre/covering layer (5 srmech.math.covering ops) + the 2 Z(Spin(8)) rep-kernel anchor ops  # rc420 (local task T1114): 569 -> 598, the 29 cascade-catalog leaf-inventory + runner registrations

#: sha256 over the NORMALISED manifest body — "\n".join(sorted names) + "\n",
#: UTF-8. Normalised rather than raw-file-bytes so a CRLF checkout cannot make
#: the digest disagree between the Windows and Linux CI cells; that would be a
#: platform artifact masquerading as a rename.
# v0.9.0rc381 (`#T1052`) — regenerated for the ADR-0010 physics rename: the 99
# ``srmech.qm.*`` op names became ``srmech.physics.qm.*`` (the qm subpackage moved
# under the new srmech.physics domain). EXPECTED_N stayed 532 — a pure rename, the
# exact SAME-COUNT set change no count-pin can see and this witness exists to catch.
# v0.9.0rc383 (`#T1054`) — one genuinely NEW op: srmech.cascade.defect_ladder (the
# rung-indexed property-loss ladder + per-rung projector). 532 -> 533, digest below.
# v0.9.0rc384 (`#T957`) — two genuinely NEW ops: srmech.cascade.octonion_frame_read
# (the 𝕆 frame-committed quaternionic-Hopf coherence read) and
# srmech.math.laplacian.octonion_laplacian (the 𝕆 gain Laplacian measuring the
# frame-committed coherence ceiling). 533 -> 535, digest below.
# v0.9.0rc385 (`#T1048`) — two genuinely NEW ops: srmech.physics.qm.quaternion.quaternion_log
# (the INVERSE of quaternion_exp — the unit-quaternion log map) and
# srmech.physics.qm.quaternion.quaternion_slerp (the exp/log geodesic
# interpolation on S³). 535 -> 537, digest below.
# v0.9.0rc386 (`#T1062`) — one genuinely NEW op: srmech.cascade.cd_three_form (the
# exact-ℚ G₂ associative 3-form φ = Re(x̄·(y·z)), the scalar Re-twin of the vector
# associator). 537 -> 538, digest below.
# v0.9.0rc387 (`#T1037`, closing `#T1032`) — two genuinely NEW ops:
# srmech.cascade.flip_pair (the one-named-bit flexibility control) and
# srmech.cascade.group_algebra_table (the wrong-quotient group ring ℝ[ℤ/dim] metric
# control) — rc360's declared STRUCTURED-negative-control residual, promoted from
# hand-rolled test code to registered ops. 538 -> 540, digest below.
# v0.9.0rc388 (`#T963`) — two genuinely NEW ops: srmech.math.octonion.oct_torsor_act
# (the RIGHT ℍ-torsor action t <| g = oct_mult(t, g) of the quaternion group on a
# seam coset) and srmech.math.octonion.oct_torsor_div (the unique g with t1 <| g == t2,
# = oct_mult(t1^8, t2)). 540 -> 542, digest below.
# v0.9.0rc390 (`#T961`) — one genuinely NEW op: srmech.biology.genome.split_defect
# (the ORDER-carrying octonion associativity read — the complement of the order-BLIND
# genome_octonion_associator; signbit(fold(word)) ^ signbit(fold(word[:k]).fold(word[k:]))).
# 542 -> 543, digest below.
# v0.9.0rc395 (`#T1000`) — REPLACE, net +1: removed the hardwired
# srmech.cascade.sedenion_zero_divisor_witness and added the two dim-general
# ops srmech.cascade.cd_zero_divisor_witness (the first witness at any rung — at
# dim 16 the identical e1+e10 / e4−e15 payload) and
# srmech.cascade.cd_zero_divisor_witnesses (the complete basis-pair set, 168 at
# dim 16). 543 -> 544, digest below.
# v0.9.0rc396 (`#T1031`, position-operator half) — two genuinely NEW ops:
# srmech.physics.qm.single_particle.clock_operator (the Weyl clock U = diag(ω^k) —
# the fenced position x̂ on a ring) and srmech.physics.qm.single_particle.shift_operator
# (the cyclic shift V — the group-level momentum), obeying U V = ω V U. 544 -> 546,
# digest below.
# v0.9.0rc398 (`#T1064`) — five genuinely NEW ops: the octonion MOUFANG LOOP surface,
# srmech.cascade.{moufang_residue, is_moufang, malcev_defect, unit_loop, loop_invariants}
# (the loop 𝕆 already IS, promoted from a test-only proof + the unnamed closure(8,[1..7])
# data to queryable exact-ℚ ops). 546 -> 551, digest below.
# v0.9.0rc399 (`#T1064` Tier 2/3) — five genuinely NEW ops: the octonion CAYLEY
# PLANE 𝕆P² surface, srmech.cascade.{jordan_product, cayley_plane_point,
# cayley_plane_incidence, octonion_hopf_base} (the Albert-algebra Jordan product,
# 𝕆P² rank-1 idempotent points, the trace-form incidence pairing, the 𝕆P¹≅S⁸
# octonionic Hopf base), plus srmech.math.laplacian.generalized_ngon (the guarded
# generalized-n-gon incidence-graph / Feit–Higman spectral read). 551 -> 556,
# digest below.
# rc411 (`#T1086`): +3 — the introspect INDEX and the registry's own front door.
# srmech.introspect.search.search (the need-shaped ranked index over the tool +
# carrier registries) plus srmech.introspect.tool_schema.{get_tool_schema,
# tool_schema_view}, which were the functions that RETURN the registry and were
# not IN it: before this rc the name `get_tool_schema` matched 0 of 556 rows.
# 556 -> 559, digest below.
# rc414 (`#T1092`): +1 — srmech.biology.coupling.fold_identity. NOT a new op: it
# has been shipped and `coupling.__all__`-exported since task #723, and is named
# in RecoverableFold's own class docstring. It simply never carried a ToolEntry,
# while all seven of its `coupling` siblings did — so it was absent from
# describe(), from the MCP tool list, and from every registry-driven census.
# That invisibility has a measured cost: a research leg reading the coupling
# module concluded RecoverableFold "cannot be gated" while its purpose-built
# three-valued gate (EQUAL / NOT_EQUAL / UNKNOWN) sat 215 lines below the line
# it was reading. This witness could not have caught that, because an op absent
# from the registry is absent from the live set too — the gap was in what got
# REGISTERED, not in what drifted. 559 -> 560, digest below.
# rc419 (`#T1110`): +9 — the srmech.signal_processing DISPATCHER + PATH-REGISTRY
# read surface: cascade_dispatcher.{dispatch, begin_cascade, end_cascade,
# current_cascade, resolve_path, is_dispatch_table_locked} and
# path_registry.{has_path, lookup, registered_ops}. Same shape as rc414's
# fold_identity and not new code either — README.md demonstrates these BY NAME
# as the package's entry point, and every one of them was unregistered, so the
# MCP tool list carried 559 definitions of which ZERO mentioned
# signal_processing and introspect.search returned the op for 0 of 41 target
# queries (8/8 positive controls passed, so that null is REFUTED, not
# unsupported). These are the FIRST nine signal_processing rows in the registry.
# 560 -> 569, digest below.
# v0.9.0rc422 (`#T1123`) — the CENTRE / COVERING layer. Seven new names: the five
# srmech.math.covering ops (center_parity / center_lift / lift_fibre /
# linking_number_cwf / covering_catalog) and the two Z(Spin(8)) rep-kernel anchor
# ops (srmech.physics.qm.triality.spin8_center / triality_rep_dictionary). All
# ADDITIONS, no rename: srmech carried algebras and finite groups (local /
# quotient objects) with no way to hold the global (pi_1 / centre) datum, and six
# shipped ops had each hand-rolled the same centre-parity shadow. 598 -> 605,
# digest below.
# v0.9.0rc424 (`#T1113`) — the music RELATIONS lane plus the MUSIC DOA
# registration. Seven new names: six srmech.music relational ops (just_limit /
# comma_of_chain / tempers_out / interval_vector / normal_order / prime_form)
# and srmech.signal_processing.music_doa. All ADDITIONS at the registry level.
# The seventh is worth naming precisely because it LOOKS like a rename and is
# not: the DOA op had NO ToolEntry through rc423, so it was ABSENT from
# search() rather than out-ranked by the srmech.music acoustics ops, and this
# is its first registration (+1). Its MODULE was separately renamed
# closed_form_ops.music -> closed_form_ops.music_doa, which moves no registry
# name because no registry name pointed at it. 605 -> 612, digest below.
#
# v0.9.0rc425 (`#T1112`) — 612 -> 649: the 37 remaining Path-A
# ``closed_form_ops``. ALL ADDITIONS, zero renames — every one of the 612
# rc424 names survives verbatim, which is exactly what this witness exists to
# confirm, since a bulk registration is precisely the kind of change under
# which a quiet rename would be invisible in the count alone.
#
# The population was measured by DEFINING MODULE (some ToolEntry's resolved
# callable has that ``__module__``), not by leaf name: name matching cannot see
# the defining module and read ``closed_form_ops/fft.py`` as already registered
# because a DIFFERENT function, ``srmech.cascade.spectral_cascades.fft``, holds
# that leaf name. Three earlier counts of this same population (38 / 39 / 41)
# were all that artifact.
#
# 40 modules were unregistered; 37 are registered here. ``fft``, ``ifft`` and
# ``pi_cascade`` are excluded because each was EXECUTED against the op it
# shadows and agreed BIT-EXACTLY (max component deviation 0.0) over integer,
# float, complex, power-of-two, non-power-of-two and length-1 inputs — the same
# values under a second name, so a row would advertise a duplicate rather than a
# surface. Had a probe disagreed this would read 650.
#
# v0.9.0rc427 (`#T1130`) — 649 -> 655. Six ops: the closed-form directional
# generator `srmech.math.cyclic.mod_mul_arrow`, its tabulated peer
# `srmech.cascade.finite_semiflow`, and four table-eating carriers/censuses
# `conjugacy_census` / `reversal_law_census` / `anti_automorphism_witnesses` /
# `dihedral_group`. `unit_loop` and `loop_invariants` each gained a `table=`
# parameter in the same rc and add NO row — a parameter extension is exactly
# the change this SET witness is blind to by design, and the count pin next
# door is blind to it too, so it is recorded here in prose deliberately.
#
# v0.9.0rc452 (gh #1653) — 663 -> 666: the cascade-chain registration triple
# (render_template / sha256_raw / mint_vector — see the EXPECTED_N note).
# ALL ADDITIONS, zero renames; digest below.
#
# v0.9.0rc457 — 676 -> 679: the representation-stratum tier-3 triple
# (central_idempotents / frobenius_schur_indicator / fusion_multiplicities
# — see the EXPECTED_N note). ALL ADDITIONS, zero renames; digest below.
#
# v0.9.0rc458 — 679 -> 687: the representation-stratum tier-4 octet — the
# rho stratum (zeta_mul / permutation_representation / character_of /
# decompose_representation / isotypic_projector /
# tensor_product_representation / direct_sum_representation /
# intertwiner_space — see the EXPECTED_N note). ALL ADDITIONS, zero
# renames; digest below.
#
# v0.9.0rc460 — 687 -> 690: the exact A2 weight-lattice triple, in a NEW
# module `srmech.math.weight_lattice` that is a PEER of `groups.py`
# (`dominant_weight` / `weight_multiplicities` /
# `tensor_product_multiplicities` — see the EXPECTED_N note). ALL
# ADDITIONS, zero renames; digest below.  ⚠️ The same rc changes the
# character_table PAYLOAD (a new `cayley_sha256` field, the group bind)
# without changing any op NAME — the exact class of change this SET
# witness is blind to by design, and the count pin next door is blind to
# it too, so it is recorded here in prose deliberately.
#
# v0.9.0rc461 — 690 -> 692: the DERIVATION pair (see the EXPECTED_N note).
# `srmech.physics.qm.triality.triality_frame_action` re-derives the two label
# actions the module carried as hard-coded dicts, and
# `srmech.math.laplacian.cyclic_laplacian_spectrum` returns the cycle
# Laplacian's spectrum in Q(zeta_n) instead of in float. ALL ADDITIONS, zero
# renames.
#
# v0.9.0rc461 — 692 -> 695: the AUTOMORPHISM-side triad, same rc, same PR.
# The DERIVATION pair reads the 28x28 generators; nothing bound the frame they
# are written in. `srmech.physics.qm.so8.epq_frame_address` (Class A) gives the
# shared E_pq frame a content address covering the pair ORDER and the octonion
# TABLE; `so8_bracket_certificate` (Class D + C) decides bracket-preservation
# over all C(28,2) = 378 generator pairs on the integer ALU and is, measured,
# the only shipped op that SEES a wrong-frame matrix (P^-1 S_B P fails 161/378
# while triality_frame_action answers it with the identity); `g2_membership`
# (Class D + K + C + A) decides Aut(O) = G2 by octonion multiplicativity and
# reports the commutator verdict under `fixed_mod_center`, because Ad(-I) = I_28
# means the commutators cannot separate g from -g -- measured, 1344 monomial
# non-automorphisms pass both. ALL ADDITIONS, zero renames; digest below.
# v0.9.0rc461 — 695 -> 700: the AFFINE / KAC-WALTON layer (see the
# EXPECTED_N note). Five srmech.math.weight_lattice additions —
# `integrable_weights`, `alcove_fold`, `affine_fusion_multiplicities`,
# `affine_modular_s_matrix`, `verlinde_fusion_multiplicities`. ALL
# ADDITIONS, zero renames; digest below.
EXPECTED_NAME_SET_SHA256 = (
    "b9a7d24d8b7ad68bd681efb5d6201bed806776ea0f16d5b954ddeddf81fa6d1e")


def _live_names() -> list[str]:
    """The op names SRMECH ITSELF registers.

    v0.9.0rc410 (`#T1085`) — this read `get_tool_schema().tools`, the UNFILTERED
    view, which deliberately publishes `srmech_tools + profile_tools`. The
    manifest next door is a witness to SRMECH's op names, so comparing it
    against a set that can contain a third party's rows is a basis mismatch:
    with any profile active, `test_the_live_name_SET_matches_the_manifest` fails
    on `added(1): ['<profile>.op']` — a false rename report.

    Note this is NOT reachable by repointing `EXPECTED_N`: the SET assertion
    fires first, so the count pin never gets a say. The count is the weaker
    check here; the SET is the contract.
    """
    return sorted(e.name for e in get_tool_schema().by_owner("srmech"))


def _manifest_names() -> list[str]:
    text = MANIFEST.read_text(encoding="utf-8")
    return [ln for ln in text.splitlines() if ln.strip()]


def _normalised(names: list[str]) -> bytes:
    return ("\n".join(names) + "\n").encode("utf-8")


def test_manifest_exists_and_is_line_per_name() -> None:
    assert MANIFEST.exists(), (
        f"{MANIFEST.name} is missing — it is the rename witness and it is "
        f"HAND-COMMITTED, so nothing regenerates it for you. See this module's "
        f"docstring for the two-edit procedure.")
    names = _manifest_names()
    assert names == sorted(names), "the manifest must be sorted"
    assert len(names) == len(set(names)), "the manifest has duplicate names"


def test_the_live_name_SET_matches_the_manifest() -> None:
    """⚠️ THE RENAME GATE. Set equality, not cardinality.

    A rename shows up here as one name in `added` and one in `removed` while the
    counts are identical — which is precisely the case every count-pin in the
    tree is blind to.
    """
    live, pinned = _live_names(), _manifest_names()
    added = sorted(set(live) - set(pinned))
    removed = sorted(set(pinned) - set(live))
    assert not (added or removed), (
        "the registered op-name SET changed.\n"
        f"  live {len(live)}  pinned {len(pinned)}"
        f"{'  (SAME COUNT — a rename, which no count-pin can see)' if len(live) == len(pinned) else ''}\n"
        f"  added({len(added)}):   {added[:12]}\n"
        f"  removed({len(removed)}): {removed[:12]}\n"
        "If this is a DELIBERATE rename or an intended new op, follow the "
        "two-edit procedure in this module's docstring — rewrite the manifest "
        "AND update EXPECTED_NAME_SET_SHA256 / EXPECTED_N in the same commit.")
    assert len(live) == EXPECTED_N, (
        f"count moved {EXPECTED_N} -> {len(live)}; update EXPECTED_N")


def test_the_manifest_digest_is_pinned_in_source() -> None:
    """The second of the two required edits. Pinning the digest in SOURCE means
    a rewrite of the data file alone cannot pass."""
    got = sha256_bytes(_normalised(_manifest_names()))
    assert got == EXPECTED_NAME_SET_SHA256, (
        f"manifest digest drifted.\n  expected {EXPECTED_NAME_SET_SHA256}\n"
        f"  got      {got}\n"
        "Update EXPECTED_NAME_SET_SHA256 to the 'got' value IN THE SAME COMMIT "
        "as the manifest rewrite.")


def test_the_witness_can_actually_fail_on_a_rename() -> None:
    """⚠️ NON-VACUITY. A gate that cannot fail is not evidence.

    Mutate one name with the SAME cardinality — exactly what declustering does —
    and prove (a) the set comparison catches it and (b) a count comparison does
    NOT. The second half is the measured indictment of the count-pins, asserted
    rather than asserted-about.
    """
    pinned = _manifest_names()
    renamed = sorted(
        ["srmech.zzzns.rational" + n[len("srmech.math.rational"):]
         if n.startswith("srmech.math.rational") else n
         for n in pinned])

    assert len(renamed) == len(pinned), "the simulation must preserve cardinality"
    moved = sum(1 for n in pinned if n.startswith("srmech.math.rational"))
    assert moved > 0, "the simulated prefix matches nothing — probe is inert"

    # (a) the SET witness sees it
    assert set(renamed) != set(pinned)
    assert sha256_bytes(_normalised(renamed)) != EXPECTED_NAME_SET_SHA256
    # (b) a COUNT witness is blind to it — this is why this file exists
    assert len(renamed) == EXPECTED_N


def test_the_manifest_is_not_codegen_emitted() -> None:
    """⚠️ If codegen ever writes this file, the witness dies silently.

    The rename arc runs the generators as routine work. A generated manifest
    would be rewritten by the change it is meant to detect and go green
    unconditionally. Keep it hand-committed.
    """
    tools = Path(__file__).resolve().parents[1] / "tools"
    assert tools.is_dir(), tools
    writers = [p.name for p in sorted(tools.glob("*.py"))
               if MANIFEST.name in p.read_text(encoding="utf-8", errors="replace")]
    assert writers == [], (
        f"{MANIFEST.name} is referenced by codegen tool(s) {writers}. If a "
        f"generator now writes it, this witness can no longer detect a rename — "
        f"it would be regenerated by the same command the rename arc runs. Keep "
        f"the manifest hand-committed and review-gated.")
