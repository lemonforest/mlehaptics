"""``srmech.cascade`` — the COMPOSITION layer, and ADR-0010's structure-home.

ADR-0010 (*namespace declustering*) splits ``srmech`` into **domains** (named by
field), **structure-homes** (named by what they *are*), **provenance**
(``amsc``, shrunk back to attestation), and **cross-cutting meta**
(``introspect``). ``srmech.cascade`` is a *structure* home: it owns
composition — how the 14 A–N primitives are chained into ops, classes and
pipelines — as distinct from the primitives themselves.

**This package was the arc's first executed namespace (rc364), so it also set
the pattern.** Three rules were established here and are meant to be applied to
every later slice:

1. **A slice relocates a PARENT; it does not rename the LEAF.** ``class_catalog``
   / ``cascade_catalog`` / ``worked_instances`` kept their directory names
   verbatim across the move. One slice changes exactly one thing — *where* a
   thing lives — so a red gate has exactly one possible cause. Renaming while
   moving makes every red ambiguous between "the move broke it" and "the rename
   broke it", which is the same unattributable-red hazard ADR-0010's own
   prerequisite section forbids one level up ("an instrument built in the same
   arc as the change it detects has no green baseline"). rc377 (Amendment N)
   is the ONE sanctioned exception to this rule (ADR B.1 rule-1): the incoming
   ``amsc/cascade/compose.py`` (the lean-ISA COMPOSITES) had to be renamed to
   ``composites.py`` because a ``compose.py`` already lived here — the
   ADR-0002 chain ENGINE (``run_chain`` / ``parse_chain_spec``). Two disjoint
   modules cannot share one leaf name; the rename is the minimal resolution and
   is documented as the exception, not the norm. The chosen leaf name is
   docstring-derived: the incoming module's own docstring opens "Cascade
   **composites** — iterative algorithms over the atoms".
2. **Declarative descriptors live under ``catalogs/``; imperative modules live
   beside it.** rc377 (the FINAL ADR-0010 slice) folds the former
   ``amsc/cascade/`` imperative modules in beside ``catalogs/`` — they land at
   ``srmech/cascade/*.py`` and the TOML stays under ``srmech/cascade/catalogs/``.
   The two kinds of content are visually separated at the top of the package
   rather than interleaved.
3. **Every catalog directory carries an ``__init__.py`` marker.** The marker is
   what makes wheel inclusion unconditional under BOTH build backends rather
   than resting on each one's package-data heuristics, and it is where the
   directory documents itself. It also rules out naming a catalog directory
   after a Python keyword — which is why the leaf is ``class_catalog`` and not
   ``class``.

What lives here
---------------
``catalogs/`` — the **built-in** descriptor catalogs, moved out of
``srmech/amsc/_research/`` where ADR-0010 found them buried:

* ``catalogs/class_catalog/`` — ``[class]`` descriptors (``srmech.dsl.make_class``)
* ``catalogs/cascade_catalog/`` — ``[cascade]`` op descriptors (the DSL chain runner)
* ``catalogs/alias_catalog/`` — ``[[alias]]`` / ``[genome.type_aliases]`` descriptors
* ``catalogs/worked_instances/`` — worked-instance descriptors

The imperative cascade **modules** (rc377, the FINAL ADR-0010 slice — the former
``srmech.amsc.cascade`` subpackage): ``atoms`` (the silicon-able 1:1 ISA
intrinsics), ``composites`` (the iterative algorithms over the atoms — Euclid's
``cyclic_gcd``, the Class K∘N∘C ``best_rational_signed``), ``parallel``,
``coupled``, ``hypercomplex_dft``, ``hamming``, ``one`` (the S(σ,θ) 1+3+7+3 = 14
generator), ``cayley_dickson``, ``sedenion_register``, ``cd_register``,
``exact_dft``, ``spectral_cascades``, ``matrix_cascades``, ``frame_carrier``.
The ADR-0002 chain ENGINE ``compose`` (``run_chain`` / ``parse_chain_spec``)
also lives here and is UNRELATED to ``composites`` — see rule 1 above.

The **user-supplied** descriptor counterparts are NOT here: ``register_class_dir``
/ ``register_catalog_dir`` / ``register_alias_dir`` and their ``SRMECH_*_PATH``
env-vars are the extension point ADR-0010 assigns to ``srmech.external.*``.
Built-in descriptors ship inside the wheel; user descriptors are registered at
runtime and attested to the user's own descriptor hash.

The DSL **loaders** stay at :mod:`srmech.dsl` — ADR-0010 §"``make_class``
re-homed" moves the *descriptors*, not the functions, and ``srmech.dsl`` was
already their correct home. The DSL flat resolver
(``srmech.dsl._catalog.lookup_cascade_op``) resolves a stage op by
``getattr(srmech.cascade, op_name)``, which is why the flat re-exports below are
load-bearing: every ``from srmech.cascade import <op>`` consumer and that
resolver rely on ``srmech.cascade.<op>`` resolving. The ``catalogs/`` TOML is
still reached by PATH (``CLASS_CATALOG_DIR`` and peers), never by import.

**No new primitive class** — every callable is a *composition* of the existing
14-class A–N primitives (the vocabulary is intact per
``[[feedback_no_privileged_primitive_classes]]``). **No ``abs()``** anywhere —
sign is handled as the canonical Class K pin-slot + Class C re-orientation per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``.

Naming: the clean public names (``pin_slot_at_zero``, ``reorient``,
``magnitude``, ``best_rational_signed``, ``cyclic_gcd``) are canonical; the
precursor's ``class_<X>_<name>`` call-site names are kept as back-compat
aliases so existing cascade scripts migrate with a pure import swap.
"""

from __future__ import annotations

from typing import Tuple

# Expose the two tiers as submodules so ``cascade.atoms`` / ``cascade.composites``
# resolve as attribute access (and so ``import srmech.cascade.atoms`` works).
from . import atoms
from . import composites
from . import parallel

# Flat re-export — the public surface stays byte-identical to the pre-move
# ``srmech.amsc.cascade`` package. ``atoms`` ships the 6 silicon-able 1:1 ISA
# intrinsics; ``composites`` ships the iterative algorithms + the 2 module
# constants. These are the canonical homes; the flat names below are
# retained as deprecated-for-one-release aliases.
#
# ⚠️ ORDERING IS LOAD-BEARING: the ``atoms`` re-exports (``chiral_flip`` /
# ``hypercomplex_couple`` / ``magnitude``) MUST precede the ``cd_register`` /
# ``sedenion_register`` imports below — those modules do ``from . import
# chiral_flip`` (etc.) at import time and need the name already bound here.
from .atoms import (
    pin_slot_at_zero,
    reorient,
    magnitude,
    chiral_flip,
    chiral_dual,
    net_chirality,
)
from .composites import (
    DEFAULT_MAX_DENOMINATOR,
    DEFAULT_FINE_SCALE,
    cyclic_gcd,
    cyclic_mod_mul,
    cyclic_mod_add,
    cyclic_mod_pow,
    cyclic_mod_inv,
    cyclic_mod_mul_wide,
    best_rational_signed,
    kuramoto_step,
    autocorrelation,
    signed_sum_squared,
    top_k_by_score,
)
# The Klein-4 four-sector PARALLEL dispatch (v0.6.0rc6; F233). A Python
# *orchestration* layer over the C-parity'd cascade.atoms — runs one cascade
# body across its ≤4 Klein-4 chirality sectors concurrently. C-orchestration
# parity tracked by issue #771.
from .parallel import (
    COMBINE_REDUCERS,
    KLEIN4_SECTOR_CAP,
    Z4_DISPATCH_SLOTS,
    parallel_sector_dispatch,
    sectorize,
)
# Coupled-wave (EM quadrature) driver + multi-stream multiplex (v0.7.5rc6;
# #928 W17/W18, F573/F577). The full-chirality (E,B) drive (handedness a
# settable convention, never hardcoded) + the role-bound N-stream multiplex.
# COMPOSITION of calculus.{sin,cos} + Class-K pin_slot_at_zero + Class-M hdc —
# no new primitive class, no new C kernel.
from .coupled import (
    coupled_wave,
    multiplex_streams,
)
# Quaternion / octonion DFT composites (v0.7.0rc31; #863, F380). The native
# transform for a Klein-4 object — its ℍ/𝕆 coefficient algebra resolves both
# Z₂ chirality axes the complex FFT collapses (the flat shadow). COMPOSITES
# over the qm.octonion left/right-mult atoms — no new primitive class. Scientific
# tier (§22): numpy is imported lazily INSIDE each op, so this import stays
# numpy-free (the rc30 numpy-absent-safe core is intact); the transforms use
# numpy on call.
from .hypercomplex_dft import (
    quaternion_dft,
    octonion_dft,
    phase_coherent_peak,
    hypercomplex_couple,
    hypercomplex_exp,
)
# Hamming / GF(2) linear block-code family — the CARRY/EC half of the
# sedenion front-loader (#910 / §30; F442/F449). Lean-ALU XOR-native; the
# Rosetta C peer (srmech_hamming_*) is attested bit-exact by the parity test.
from .hamming import (
    hamming_encode,
    hamming_syndrome,
    hamming_decode_correct,
)
# The One — S(σ,θ), the single generator of the 1+3+7+3 = 14 substrate
# (#887; "the One"). The Hurwitz division-algebra ladder ℂ/ℍ/𝕆 as one
# (σ, θ)-parameterised exact-rational object: ℝ·1 anchors (the B/H/N
# grammar) ⊕ σ e^{Î_nθ} Im 𝔸_n (the 1:3:7 imaginary, rotated by the
# epicycle). Numpy-free at import (the e^{Îθ} = cos+Î·sin is built from the
# Class-N rational series); float realisations (.to_numpy / .to_matrix) are
# the opt-in scientific tier. The qm-matrix Rosetta peer lives in
# srmech.physics.qm.hurwitz.
from .one import (
    Block,
    One,
    the_one,
    s_generator,
    to_scalar,
    winding_tower,
    winding_fold,
)
# Cayley–Dickson open-exterior boundary-demonstrator (v0.7.3rc1; #915 / MFO
# §VII.6.23). The deliberately NON-reversible object on the far side of the
# Hurwitz wall: generic ℝ→ℂ→ℍ→𝕆→𝕊(16)→… doubling, exact-rational + numpy-free.
# NOT a substrate extension — the closed sim stays ≤𝕆; this exhibits the wall
# (zero divisors at 16, no inverse map) so §VII.6.23's open-exterior claims are
# own-code-attested. The integer cocycle cd_basis_product has a JPL-clean C peer.
from .cayley_dickson import (
    CD_MAX_DIM,
    CD_DENSE_MAX_DIM,
    CD_COMPOSE_MAX_DIM,
    CD_TURN_MAX_DIM,
    CD_ADDRESS_VERIFIED_DIM,
    ALGEBRA_TABLE_MAX_DIM,
    CD_DIMS,
    DIVISION_ALGEBRA_DIMS,
    ASSOCIATIVE_ALGEBRA_DIMS,
    ALGEBRA_NAMES,
    cd_mult,
    cd_conjugate,
    cd_add,
    cd_norm_sq,
    cd_basis,
    cd_basis_product,
    cd_promote,
    cd_project,
    is_division_algebra_dim,
    cd_zero_divisor_witness,
    cd_zero_divisor_witnesses,
    left_mult_matrix,
    left_mult_kernel,
    left_mult_is_invertible,
    inertia_signature,
    algebra_table,
    flip_pair,
    group_algebra_table,
    table_product,
    associator,
    cd_commutator,
    cd_cycle_holonomy,
    cd_three_form,
    defect_ladder,
    octonion_frame_read,
    OCTONION_FRAME_SEAM,
    moufang_residue,
    is_moufang,
    malcev_defect,
    unit_loop,
    loop_invariants,
)
# The octonion CAYLEY PLANE 𝕆P² surface (rc399; `#T1064` Tier 2) — the n=3
# Moufang plane built carrier-native, one rung above octonion_frame_read's
# ℍP¹≅S⁴: the Albert-algebra Jordan product, 𝕆P² points, the trace-form
# incidence pairing, and the 𝕆P¹≅S⁸ octonionic Hopf base.
from .cayley_plane import (
    jordan_product,
    cayley_plane_point,
    cayley_plane_incidence,
    octonion_hopf_base,
)
# Sedenion-addressable hyper-loop RBS-HDC instrument (v0.7.4rc1; UPSTREAM §31 of
# PR #687; F465 + F468). The sedenion box made into an addressable instrument:
# 16 named slots (octonion working block e0..e7 + EC/carry block e8..e15), HDC
# storage, the ≤7 reversible coupler working word, the Hamming carry, and the
# address↔Cayley–Dickson `navigate` homomorphism + `is_navigable` gate (the
# genuinely-new piece). Pure composition of shipped primitives — no new algebra.
from .sedenion_register import (
    SedenionRegister,
    sedenion_register,
    NUM_SLOTS,
    OCT_BLOCK,
    EC_BLOCK,
    WORKING_WORD_CAP,
)

# ── The GENERAL N-slot Cayley–Dickson register (rc297; `#934`) ─────────
# The 16-slot instrument above generalised to any power-of-two dim in
# [1, CD_MAX_DIM]. The slot bound is the ONLY generalisation — every sign and
# index rule is shared through `cd_basis_product`, so there is no second
# algebra. `SedenionRegister` remains the independent oracle the general
# register's faithfulness is gated against (`CDRegister(16, namespace=
# "SEDENION")` reproduces it bit-exactly at every D); it is deliberately NOT
# collapsed into an n=16 alias.
from .cd_register import (
    CDRegister,
    cd_register,
    cd_navmap,
    cd_navigate,
    cd_navmap_is_signed_permutation,
    cd_couple_working,
    cd_uncouple_working,
    cd_carry,
    cd_correct,
    WORKING_BLOCK_DIM,
)

# ── Class-L DSL re-export: schur_complement / Dirichlet-to-Neumann ─────
# ``schur_complement`` lives canonically in ``srmech.math.laplacian`` (its
# A–N home is Class L; the tool-schema entry is registered there). The DSL
# chain runner resolves stage ops via ``getattr(srmech.cascade, name)``
# (srmech.dsl._catalog.lookup_cascade_op), so the cascade-catalog descriptor
# schur_complement.toml needs the callable reachable at this flat name.
# Re-exported here for that resolution only — deliberately NOT added to
# ``__all__`` (it is the laplacian-registered op reached for the chain
# contract, not a second cascade-native primitive). It is numpy-absent-safe
# (exact-rational path), so this import keeps the rc30 numpy-free core intact.
# See tests/test_schur_complement_dsl_stage.py.
from ..math.laplacian import schur_complement  # noqa: F401  (DSL resolution alias)

# ── Back-compat aliases (the precursor's call-site names) ──────────────
# Existing cascade scripts in docs/unsolved-maths/ import these names; the
# alias lets them migrate to ``from srmech.cascade import ...`` without
# changing call sites.
class_k_pin_slot_at_zero = pin_slot_at_zero
class_c_reorient = reorient
best_rat_signed = best_rational_signed

#: Registry of the foundational cascade op names (documentary; consumers
#: iterate by name). Each maps to its A–N class composition in the docs.
CASCADE_OPS: Tuple[str, ...] = (
    "pin_slot_at_zero",        # Class K
    "reorient",                # Class C
    "magnitude",               # Class K (magnitude-only)
    "best_rational_signed",    # Class K ∘ N ∘ C
    "cyclic_gcd",              # Class I
    "chiral_flip",             # Class C (orientation reversal)
    "chiral_dual",             # Class C ∘ op ∘ Class C (chiral-dual conjugation)
    "net_chirality",           # Class C (net handedness invariant)
)

__all__ = [
    "DEFAULT_MAX_DENOMINATOR",
    "DEFAULT_FINE_SCALE",
    "CASCADE_OPS",
    "pin_slot_at_zero",
    "reorient",
    "magnitude",
    "best_rational_signed",
    "cyclic_gcd",
    "cyclic_mod_mul",
    "cyclic_mod_add",
    "cyclic_mod_pow",
    "cyclic_mod_inv",
    "cyclic_mod_mul_wide",
    "kuramoto_step",
    "autocorrelation",
    "signed_sum_squared",
    "top_k_by_score",
    "chiral_flip",
    "chiral_dual",
    "net_chirality",
    # Klein-4 four-sector parallel dispatch (v0.6.0rc6; F233)
    "KLEIN4_SECTOR_CAP",
    "Z4_DISPATCH_SLOTS",
    "parallel_sector_dispatch",
    # rc12 composability (§11.3): recombine + nesting wrapper
    "COMBINE_REDUCERS",
    "sectorize",
    # rc6 coupled-wave + multiplex (#928 W17/W18, F573/F577)
    "coupled_wave",
    "multiplex_streams",
    # Quaternion/octonion DFT composites (v0.7.0rc31; #863)
    "quaternion_dft",
    "octonion_dft",
    # The lightweight matched-filter PEAK READ (v0.9.0rc112; #1234 Item 1d,
    # F1000→F1001→F1002) — the READ counterpart to the full transforms above
    "phase_coherent_peak",
    # Bidirectional (σ,θ,μ) hypercomplex coupler (v0.7.2rc1; #908, F436/F437)
    "hypercomplex_couple",
    # Literal exp(μθ) unit hypercomplex twiddle (v0.9.0rc10; F882, srmech #205)
    "hypercomplex_exp",
    # Hamming / GF(2) block-code family (v0.7.2rc2; #910, §30 / F442/F449)
    "hamming_encode",
    "hamming_syndrome",
    "hamming_decode_correct",
    # The One — S(σ,θ,w), the 1+3+7+3 = 14 generator (#887; winding rc137 / gh#1276)
    "Block",
    "One",
    "the_one",
    "s_generator",
    "to_scalar",
    "winding_tower",
    "winding_fold",
    # Cayley–Dickson open-exterior demonstrator (v0.7.3rc1; #915 / MFO §VII.6.23)
    "CD_MAX_DIM",
    "CD_DENSE_MAX_DIM",
    "CD_COMPOSE_MAX_DIM",
    "CD_TURN_MAX_DIM",
    "CD_ADDRESS_VERIFIED_DIM",
    "CD_DIMS",
    "DIVISION_ALGEBRA_DIMS",
    "ASSOCIATIVE_ALGEBRA_DIMS",
    "ALGEBRA_NAMES",
    "cd_mult",
    "cd_conjugate",
    "cd_add",
    "cd_norm_sq",
    "cd_basis",
    "cd_basis_product",
    "cd_promote",
    "cd_project",
    "is_division_algebra_dim",
    "cd_zero_divisor_witness",
    "cd_zero_divisor_witnesses",
    "left_mult_matrix",
    "left_mult_kernel",
    "left_mult_is_invertible",
    "inertia_signature",
    # The gamma-parameterised CD control constructor (rc352; `#T997`)
    "ALGEBRA_TABLE_MAX_DIM",
    "algebra_table",
    # The two STRUCTURED negative controls — one-named-bit flexibility break +
    # the wrong-quotient group ring ℝ[ℤ/dim] (rc387; `#T1037`, closing `#T1032`)
    "flip_pair",
    "group_algebra_table",
    "table_product",
    # The associativity DEFECT (rc360; `#T1032`)
    "associator",
    # The k=2 / k=3 loop-defect ladder — commutator + 3-cycle holonomy (rc380; `#T1055`)
    "cd_commutator",
    "cd_cycle_holonomy",
    # The G₂ associative 3-form φ = Re(x̄·(y·z)) — the scalar Re-twin of associator (rc386; `#T1062`)
    "cd_three_form",
    # The RUNG-indexed property-loss ladder + per-rung projector (rc383; `#T1054`)
    "defect_ladder",
    # The 𝕆 frame-committed quaternionic-Hopf coherence read (rc384; `#T957`)
    "octonion_frame_read",
    "OCTONION_FRAME_SEAM",
    # The octonion MOUFANG LOOP surface (rc398; `#T1064`) — the loop 𝕆 already
    # IS, promoted from test-only proof + unnamed closure() data to queryable
    # ops: the Moufang-identity checker + Mal'cev tangent + M16 + loop invariants
    "moufang_residue",
    "is_moufang",
    "malcev_defect",
    "unit_loop",
    "loop_invariants",
    # The octonion CAYLEY PLANE 𝕆P² surface (rc399; `#T1064` Tier 2) — the n=3
    # Moufang plane carrier-native (Albert-algebra Jordan product, 𝕆P² points,
    # the trace-form incidence pairing, the 𝕆P¹≅S⁸ octonionic Hopf base)
    "jordan_product",
    "cayley_plane_point",
    "cayley_plane_incidence",
    "octonion_hopf_base",
    # Sedenion-addressable RBS-HDC instrument (v0.7.4rc1; UPSTREAM §31; F465/F468)
    "SedenionRegister",
    "sedenion_register",
    "NUM_SLOTS",
    "OCT_BLOCK",
    "EC_BLOCK",
    "WORKING_WORD_CAP",
    # General N-slot Cayley–Dickson register (v0.9.0rc297; `#934`)
    "CDRegister",
    "cd_register",
    "cd_navmap",
    "cd_navigate",
    "cd_navmap_is_signed_permutation",
    # the OPT layers as pure functions (v0.9.0rc301; `#T938`)
    "cd_couple_working",
    "cd_uncouple_working",
    "cd_carry",
    "cd_correct",
    "WORKING_BLOCK_DIM",
    # back-compat aliases
    "class_k_pin_slot_at_zero",
    "class_c_reorient",
    "best_rat_signed",
    # submodules (canonical homes)
    "atoms",
    "composites",
    "parallel",
]
