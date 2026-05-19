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

from srmech.qm import (
    bell,
    gauge,
    potentials,
    propagators,
    pseudo_hermitian,
    relativistic,
    single_particle,
    sm,
    spin,
)

__all__ = [
    "bell",
    "gauge",
    "potentials",
    "propagators",
    "pseudo_hermitian",
    "relativistic",
    "single_particle",
    "sm",
    "spin",
]
