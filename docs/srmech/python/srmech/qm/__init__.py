"""srmech.qm — canonical QM/QFT/SM operations layer.

Per ``[[feedback_science_is_ssot_not_project]]``: each operation is
sourced from canonical physics literature, **not** from any project
instantiation. Chess-spectral / ephemerides-spectral / antikythera-spectral
become *substrate-consumers* of these primitives, not their authors.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]``: these
operations are the **substrate-coupling operations** that uncompress
LoE-content into event-stream. The 1D_t Laws-content (per MFO §VII.1.2)
is content; these are how content becomes events. Each operation
dissolves into the 14-class primitive vocabulary per
``[[feedback_no_privileged_primitive_classes]]``:

- **TDSE / TISE / Heisenberg / Liouville-vN** — Class L (spectral evolution)
- **[x̂, p̂] commutator** — Class C (lattice gradient) ∘ Class L (commutator)
- **Pauli matrices** — Class M (Clifford binding via Cl(0,3))
- **Hydrogen radial** — Class L (radial-Laplacian eigendecomp)
- **Harmonic oscillator** — Class M (HDC binding for a, a†)

Submodules:

- :mod:`srmech.qm.single_particle` — TDSE, TISE, Heisenberg, commutator,
  density matrix, Liouville-vN, lattice momentum.
- :mod:`srmech.qm.spin` — Pauli matrices, Clifford-algebra checks.
- :mod:`srmech.qm.bell` — Bell-CHSH inequality + Tsirelson bound ``2√2``
  as bit-exact framework identity (Class L ∘ I ∘ M ∘ C ∘ A cascade).
  Per ``[[user_stance_bell_inequality_as_canonical_identity_signature]]``:
  the framework's strongest single identity-not-implementation signature.
- :mod:`srmech.qm.potentials` — Hydrogen radial, harmonic-oscillator
  ladder operators.
- :mod:`srmech.qm.relativistic` — Dirac γ-matrices (Cl(1,3)), Klein-
  Gordon, Weyl projectors, charge conjugation (Majorana).
- :mod:`srmech.qm.propagators` — Feynman propagators (scalar / fermion /
  photon / massive vector).
- :mod:`srmech.qm.pseudo_hermitian` — η-deformed inner product, PT-
  symmetric QM framework (Bender-Boettcher / Mostafazadeh).
- :mod:`srmech.qm.gauge` — Yang-Mills generators (SU(2), SU(3) Gell-Mann),
  structure constants, Casimirs, Wilson-loop holonomy.
- :mod:`srmech.qm.sm` — Electroweak unification, Higgs mechanism, Yukawa
  fermion masses, CKM matrix.
- :mod:`srmech.qm.quaternion` — the QDFT/ODFT foundation (#1234 Item 1a /
  #863, F380): the 4×4 ``L_q`` / ``R_q`` quaternion multiplication
  operators (ℍ = the dim-4 Cayley-Dickson rung, so ``Q₈/{±1} ≅ Klein-4``)
  + the hypercomplex ``exp(μθ)`` twiddle (Euler formula; series-truncate
  exact tier + the float64 boundary) + the DFT twiddle ``exp(σμ2πjk/N)``.
- :mod:`srmech.qm.octonion` — the MPR-attested Cayley-Dickson-from-H
  octonion multiplication table + ``L_a`` / ``R_a`` binders, conjugate,
  norm (Class K ∘ C, never ``abs()``).
- :mod:`srmech.qm.so8` — the 28-generator ``so(8)`` adjoint partitioned
  ``14 (g2 = Der O) + 7 (L-type) + 7 (R-type)``; ``g2_subalgebra`` (the 14),
  ``so7_subalgebra`` (the 21; ``D4 -> B3`` fold).
- :mod:`srmech.qm.triality` — the Spin(8) triality engine: the ``28×28``
  order-3 outer automorphism ``τ = S_B ∘ S_C`` (``τ³ = I``,
  ``Fix(τ) = g2`` dim 14 = the A-N ``1+3+7+3`` partition), the ``Z2`` swap,
  Cartan companions + residual.

Canonical SSoT:

- Sakurai, J.J. (2017) *Modern Quantum Mechanics* (3rd ed.), Cambridge.
- Cohen-Tannoudji, C., Diu, B., Laloë, F. (1977/1991) *Quantum Mechanics*
  (Vols. I-II), Wiley.
- Griffiths, D.J. (2017) *Introduction to Quantum Mechanics* (2nd ed.),
  Cambridge.
- Schrödinger, E. (1926) *Annalen der Physik* 79, 361-376 / 489-527.
- Heisenberg, W. (1925) *Zeitschrift für Physik* 33, 879-893.
- Pauli, W. (1927) *Zeitschrift für Physik* 43, 601-623.
- von Neumann, J. (1932) *Mathematische Grundlagen der Quantenmechanik*,
  Springer.
- Bohr, N. (1913) *Philosophical Magazine* 26, 1-25 / 476-502.
"""

# Scientific tier: numpy is optional as of v0.7.0 (the cascade core is numpy-
# free). The qm submodules are flipping numpy-free one-by-one (#564 carrier arc:
# rc115 spin/bell, rc116+ the rest). Rather than an EAGER subpackage-wide
# `_require_numpy("srmech.qm")` gate (which would block the already-numpy-free
# modules from importing on a numpy-absent install — the rc70 runnable≠loadable
# trap / [[feedback_carrier_ratchet_misses_require_numpy_subpackage_gates]]),
# each submodule is loaded LAZILY on first access (the rc71 signal_processing
# precedent): a flipped module imports numpy-free; an as-yet-numpy module still
# surfaces the actionable [scientific] hint (not a bare numpy ImportError).

import importlib

__all__ = [
    "bell",
    "gauge",
    "hurwitz",
    "octonion",
    "potentials",
    "propagators",
    "pseudo_hermitian",
    "quaternion",
    "relativistic",
    "single_particle",
    "sm",
    "so8",
    "spin",
    "triality",
]

_SUBMODULES = frozenset(__all__)


def __getattr__(name):
    """Lazily import a qm submodule on first attribute access (PEP 562).

    The whole ``srmech.qm`` subpackage is numpy-free (#564), so this is a plain
    lazy import — no ``[scientific]`` gate.
    """
    if name in _SUBMODULES:
        mod = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | _SUBMODULES)
