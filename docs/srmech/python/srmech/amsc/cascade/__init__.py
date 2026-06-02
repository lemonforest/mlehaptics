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
    # back-compat aliases
    "class_k_pin_slot_at_zero",
    "class_c_reorient",
    "best_rat_signed",
    # submodules (new canonical homes)
    "atoms",
    "compose",
    "parallel",
]
