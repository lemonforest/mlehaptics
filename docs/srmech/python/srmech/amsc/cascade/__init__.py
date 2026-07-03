"""Foundational cross-domain cascade catalog.

The cascades that recur across **every / most** domains the framework has
examined — promoted into srmech so a named cascade is the default and a
math-library call is the exception. Per the project discipline: *being
forced to reach for a math library is the signal that a cascade is waiting
to be found.* `abs()` told us to find the Class-K pin-slot; `fractions`
told us to find the Class-N rational anchor; `math.gcd` told us to find the
Class-I cyclic gcd. This module is where those answers live.

Scale-invariance is the load-bearing reason these belong in srmech: the
A–N class operators are substrate-universal vocabulary that applies at
every discipline and every scale (per
``[[user_stance_cross_substrate_cascade_matching_as_research_method]]``).
The same **Class K pin-slot at zero** operates at bronze-gear engagement
(Antikythera), atomic shell-boundary sign-flip, biological membrane
zero-crossing, quantum tunnelling, and prime-cyclic Laplacian residue
exclusion. The same **Class N** rational anchor lands the GUE spacing-ratio
at 20/17, the Balmer line-ratios, the CMB peak spacing. This catalog is the
explicit home of that recurrence — the precursor
``docs/unsolved-maths/_cascade_helpers.py`` (imported across 20+ cascade
scripts spanning mandelbrot / chromatic / atomic / nuclear / QCD /
planetary / turbulence / black-hole / biomacromolecule / large-scale-
structure domains) graduates here.

**Two-tier split (v0.6.0; F208 / MS #20 forward-architecture).** The
catalog is split into two submodules along the lean A–N ISA boundary:

- :mod:`srmech.amsc.cascade.atoms` — the **6 silicon-able 1:1 ISA
  intrinsics** (``pin_slot_at_zero``, ``reorient``, ``magnitude``,
  ``chiral_flip``, ``chiral_dual``, ``net_chirality``). Each maps 1:1
  onto a single (future) ISA intrinsic.
- :mod:`srmech.amsc.cascade.compose` — the **2 iterative algorithms**
  built over the atoms (``cyclic_gcd`` = Euclid's remainder loop;
  ``best_rational_signed`` = the Class K ∘ N ∘ C continued-fraction
  loop).

``atoms.*`` and ``compose.*`` are the **new canonical homes**. The flat
``srmech.amsc.cascade.<op>`` names (and the ``class_<X>_<name>`` /
``best_rat_signed`` back-compat aliases) are **retained as deprecated
aliases for one release** — they remain importable here with NO runtime
``DeprecationWarning`` this release (the deprecation is documentary for
now; runtime-warn + removal follow in a future release). Existing cascade
scripts need no edits.

**Full C/Python parity** — each cascade op carries a dedicated C symbol in
``libsrmech.{so,dll,dylib}`` (the cascade catalog is no longer Python-only
per the v0.4.5rc1 carve-out correction) AND a TOML descriptor under
``srmech/amsc/_research/cascade_catalog/`` declaring the cascade structure
declaratively. The Python module dispatches through native when ``HAS_NATIVE``
is True and the input shape matches a typed C variant; falls back to Python
for sequence types the C ABI doesn't cover (strings, mixed-type lists, etc).

**No new primitive class** — every callable is a *composition* of the
existing 14-class A–N primitives (the vocabulary is intact per
``[[feedback_no_privileged_primitive_classes]]``). Class I
(``srmech.amsc.cyclic.gcd``) and Class N
(``srmech.amsc.rational.best_rational``) supply the cyclic / rational
anchor primitives; the cascades sequence them in Python (with inline
Class K / Class C signed arithmetic) plus the dedicated cascade-op C
symbols for the hot value-sequence cascades (``chiral_flip`` in
v0.4.5rc1; the remaining ops follow in subsequent rcs). **No ``abs()``**
anywhere — sign is handled as the canonical Class K pin-slot + Class C
re-orientation per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``.

Naming: the clean public names (``pin_slot_at_zero``, ``reorient``,
``magnitude``, ``best_rational_signed``, ``cyclic_gcd``) are canonical; the
precursor's ``class_<X>_<name>`` call-site names are kept as back-compat
aliases so existing cascade scripts migrate with a pure import swap.

Canonical SSoT:
- ``[[user_stance_epicycle_via_gear_plus_pin]]`` — sign-flip IS the Class K
  pin-slot phase-boundary.
- Khinchin (1964), *Continued Fractions* — the Class N best-rational anchor
  (via ``srmech.amsc.rational.best_rational``).
- Euclid, *Elements* VII.1–2 — the Class I gcd (via ``srmech.amsc.cyclic.gcd``).
"""

from __future__ import annotations

from typing import Tuple

# Expose the two tiers as submodules so ``cascade.atoms`` / ``cascade.compose``
# resolve as attribute access (and so ``import srmech.amsc.cascade.atoms`` works).
from . import atoms
from . import compose
from . import parallel

# Flat re-export — the public surface stays byte-identical to the
# pre-split single module. ``atoms`` ships the 6 silicon-able 1:1 ISA
# intrinsics; ``compose`` ships the 2 iterative algorithms + the 2 module
# constants. These are the canonical homes; the flat names below are
# retained as deprecated-for-one-release aliases.
from .atoms import (
    pin_slot_at_zero,
    reorient,
    magnitude,
    chiral_flip,
    chiral_dual,
    net_chirality,
)
from .compose import (
    DEFAULT_MAX_DENOMINATOR,
    DEFAULT_FINE_SCALE,
    cyclic_gcd,
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
# srmech.qm.hurwitz.
from .one import (
    Block,
    One,
    the_one,
    s_generator,
    to_scalar,
)
# Cayley–Dickson open-exterior boundary-demonstrator (v0.7.3rc1; #915 / MFO
# §VII.6.23). The deliberately NON-reversible object on the far side of the
# Hurwitz wall: generic ℝ→ℂ→ℍ→𝕆→𝕊(16)→… doubling, exact-rational + numpy-free.
# NOT a substrate extension — the closed sim stays ≤𝕆; this exhibits the wall
# (zero divisors at 16, no inverse map) so §VII.6.23's open-exterior claims are
# own-code-attested. The integer cocycle cd_basis_product has a JPL-clean C peer.
from .cayley_dickson import (
    CD_MAX_DIM,
    CD_DIMS,
    DIVISION_ALGEBRA_DIMS,
    ALGEBRA_NAMES,
    cd_mult,
    cd_conjugate,
    cd_add,
    cd_norm_sq,
    cd_basis,
    cd_basis_product,
    is_division_algebra_dim,
    sedenion_zero_divisor_witness,
    left_mult_matrix,
    left_mult_kernel,
    left_mult_is_invertible,
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

# ── Class-L DSL re-export: schur_complement / Dirichlet-to-Neumann ─────
# ``schur_complement`` lives canonically in ``srmech.amsc.laplacian`` (its
# A–N home is Class L; the tool-schema entry is registered there). The DSL
# chain runner resolves stage ops via ``getattr(srmech.amsc.cascade, name)``
# (srmech.dsl._catalog.lookup_cascade_op), so the cascade-catalog descriptor
# schur_complement.toml needs the callable reachable at this flat name.
# Re-exported here for that resolution only — deliberately NOT added to
# ``__all__`` (it is the laplacian-registered op reached for the chain
# contract, not a second cascade-native primitive). It is numpy-absent-safe
# (exact-rational path), so this import keeps the rc30 numpy-free core intact.
# See tests/test_schur_complement_dsl_stage.py.
from ..laplacian import schur_complement  # noqa: F401  (DSL resolution alias)

# ── Back-compat aliases (the precursor's call-site names) ──────────────
# Existing cascade scripts in docs/unsolved-maths/ import these names from
# the local _cascade_helpers; the alias lets them migrate to
# ``from srmech.amsc.cascade import ...`` without changing call sites.
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
    # The One — S(σ,θ), the 1+3+7+3 = 14 generator (#887)
    "Block",
    "One",
    "the_one",
    "s_generator",
    "to_scalar",
    # Cayley–Dickson open-exterior demonstrator (v0.7.3rc1; #915 / MFO §VII.6.23)
    "CD_MAX_DIM",
    "CD_DIMS",
    "DIVISION_ALGEBRA_DIMS",
    "ALGEBRA_NAMES",
    "cd_mult",
    "cd_conjugate",
    "cd_add",
    "cd_norm_sq",
    "cd_basis",
    "cd_basis_product",
    "is_division_algebra_dim",
    "sedenion_zero_divisor_witness",
    "left_mult_matrix",
    "left_mult_kernel",
    "left_mult_is_invertible",
    # Sedenion-addressable RBS-HDC instrument (v0.7.4rc1; UPSTREAM §31; F465/F468)
    "SedenionRegister",
    "sedenion_register",
    "NUM_SLOTS",
    "OCT_BLOCK",
    "EC_BLOCK",
    "WORKING_WORD_CAP",
    # back-compat aliases
    "class_k_pin_slot_at_zero",
    "class_c_reorient",
    "best_rat_signed",
    # submodules (new canonical homes)
    "atoms",
    "compose",
    "parallel",
]
