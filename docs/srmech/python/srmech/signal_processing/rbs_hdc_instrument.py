"""Path B core — LoE-as-bound-vector RBS-HDC instrument.

Phase 3 of the RBS-HDC-LoE dual-path architecture per the implementation plan
``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md``.

This module ports the Spike #170 R1 prototype (``spike170_loe_rbs_hdc_prototype.py``)
to a stable, composable Path B core. Per
``[[user_stance_loe_as_rbs_hdc_instrument_meta_recursive]]``:
the Laws of Everything (compressed-cascade content per
``[[user_stance_1d_collapse_to_loe_identity_not_action]]``) are
instantiated as an executable RBS-HDC instrument — FRAMEWORK on the
inside, DATA on the outside. The 14 A-N class operators become
bindable HDC content (semantic-pathway primitives); cascade
compositions become procedural-memory pathway content; canonical
stance fingerprints become semantic-memory content; the k=3
tripartition register (3D_s ⊗ 7D_g ⊗ 1D_t per
``[[project_space_gauge_time_framework]]``) anchors the dimensional
decomposition; the four memory pathways (procedural / semantic /
working-memory / episodic-LTM per
``[[user_stance_working_memory_is_cascade_augmenting_reflex_into_agency]]``)
host pathway-specific HDC slots.

Self-referential structure
--------------------------
Class M HDC bind is itself a class operator. When Class M is encoded
into the instrument, the instrument's bind operation is BOTH operator
AND operand. Per
``[[user_stance_cascade_dual_level_quantum_at_algebra_classical_at_sampling]]``:

- Algebra level — Class M defines the operation.
- Instrument level — Class M IS the operation running.

The two-level ontology resolves the apparent self-reference into
productive fixed-point structure (not a Russell paradox).

Strict-spec discipline (Phase 3)
--------------------------------
- HDC width ``D = 8192`` bits (1024 bytes) per Spike #147 canonical +
  conductor decision #6 (2026-05-19). Optional ``D`` parameter accepted
  for downstream experiments.
- ``bind`` is bit-exact self-inverse + associative + commutative
  (Spike #142 verified; Spike #170 §3 invariant 4).
- ``permute`` is form-function-determined (Spike #159 rotate-bind
  commutativity; Spike #173 chess-stride bit-exactness;
  Spike #176 cyclic-FFT shift theorem).
- All class-operator vectors are mint-once via SHA-256 chain (Class A
  content addressing). Determinism: same canonical name ⇒ same vector
  (Spike #170 §3 invariant 1: 14/14 bit-exact).
- 14 classes A-N intact; no class promotion (per
  ``[[feedback_no_privileged_primitive_classes]]``).

Identity-not-implementation (Phase 3)
-------------------------------------
Per ``[[user_stance_identity_not_implementation_discipline]]`` the
instrument IS the Laws of Everything composed at the substrate level;
the instrument does not implement them. The bit-exact mint determinism
+ algebraic-identity preservation under cascade composition + reverse-
decode 100% accuracy together demonstrate the identity.

Trauma-informed defensive scope
-------------------------------
Per ``[[feedback_trauma_informed_defensive_scope]]``: the "Laws of
Everything" framing is mathematical / structural ontology. No clinical,
treatment, or predictive claims. Foundational physics + cognitive-
science framing only.

Canonical SSoT
--------------
- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Rachkovskij (2001) *Representation and processing of structures with
  binary sparse distributed codes*, Neural Comput Appl 9, 322.
- Spike #170 — RBS-HDC instrument feasibility (R1 prototype, 14/14 mint
  determinism); ``docs/srmech/notes/spike170_loe_rbs_hdc_prototype.py``.
- Spike #172 — DNA helical-pitch substrate (R3 cross-substrate bit-exact
  closure).
- Spike #173 — chess natural-stride substrate (D2 orthogonality at
  noise floor).
- Spike #176 — rotation IS Class K (machine ε).
- Spike #177 — pin-slot-resonate music-box mechanism (I + K + C + M∘K).
- Implementation plan: ``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from srmech.amsc import hdc as _M
from srmech.amsc.format import sha256_bytes as _sha256_hex

from ._paths import D_DEFAULT, D_MIN, D_MAX

__all__ = [
    # Constants / catalogs
    "CLASS_NAMES",
    "CLASS_DEFINITIONS",
    "CANONICAL_CASCADES",
    "SAMPLE_STANCES",
    "MEMORY_PATHWAYS",
    "K3_TRIPARTITION_DEFAULT",
    # Dataclasses
    "ClassOperator",
    "Cascade",
    "Stance",
    "MemorySlot",
    "K3Tripartition",
    "RBSHDCInstrument",
    # Module-level public functions
    "mint_class_operator",
    "mint_cascade_composition",
    "mint_stance_fingerprint",
    "encode_loe_content",
    "decode_loe_fingerprint",
    # Helper
    "mint_vector",
    "PERMUTE_ORDER_STRIDE",
    "OPERATION_NAMES",
    "OP_CLASSES",
    "OP_SSOT_CITATION",
]

# ──────────────────────────────────────────────────────────────────────
# Strict-spec architectural constants (Phase 3 — Spike #170 anchors)
# ──────────────────────────────────────────────────────────────────────

#: Default rotation stride used by ordered cascade composition. Prime
#: 257 is coprime to D = 8192 = 2^13 so per-position rotations never
#: alias (Spike #170 prototype constant; Spike #173 chess strides
#: confirm bit-exact commutativity at coprime strides).
PERMUTE_ORDER_STRIDE: int = 257

#: The 14-class A-N vocabulary (canonical order). 14 classes intact per
#: ``[[feedback_no_privileged_primitive_classes]]``; no class promotion.
CLASS_NAMES: Tuple[str, ...] = tuple("ABCDEFGHIJKLMN")

#: Canonical class operator definitions — one line operational role per
#: 14-class roster (Spike #170 prototype). Tuples are ``(short_name,
#: operation_description)``; the canonical name string used for SHA-256
#: minting is ``f"LoE.class.{class_letter}.{short_name}"``.
CLASS_DEFINITIONS: Dict[str, Tuple[str, str]] = {
    "A": ("content-addressing", "SHA-256 content addressing"),
    "B": ("byte-canonical-form", "TLV byte-canonical form"),
    "C": ("cyclic-group", "Z/n cyclic shift / permute"),
    "D": ("dispatch", "Multi-needle pattern match / late-binding"),
    "E": ("catalog-lookup", "Sorted-key catalog lookup"),
    "F": ("template-render", "Placeholder substitution {key}"),
    "G": ("byte-search", "Byte-pattern needle search"),
    "H": ("self-introspection", "Version / ABI / capability acknowledgment"),
    "I": ("cyclic-arithmetic", "Modular arithmetic over Z/n"),
    "J": ("prime-factorisation", "Trial-division primality + factorisation"),
    "K": ("asymptotic-DOF", "Sparse-truncate top-N coefficients (pin-slot)"),
    "L": ("graph-laplacian", "Pi-free dense + Jacobi eigvals"),
    "M": ("HDC-bind", "Bind / bundle / permute / similarity"),
    "N": ("rational-approximation", "Cyclic-group rationals (helical pitch etc)"),
}

#: Path B core operation roster + class-composition labels (used by the
#: post-load registration at module bottom). Each entry is
#: ``(operation_name, classes_tuple)``.
OPERATION_NAMES: Tuple[str, ...] = (
    "rbs_hdc_mint_class_operator",
    "rbs_hdc_mint_cascade_composition",
    "rbs_hdc_encode_loe_content",
    "rbs_hdc_decode_loe_fingerprint",
)

OP_CLASSES: Dict[str, Tuple[str, ...]] = {
    "rbs_hdc_mint_class_operator": ("A", "M"),
    "rbs_hdc_mint_cascade_composition": ("A", "C", "M"),
    "rbs_hdc_encode_loe_content": ("A", "C", "M"),
    "rbs_hdc_decode_loe_fingerprint": ("M",),
}

OP_SSOT_CITATION: str = (
    "Spike #170 R1 prototype (FEASIBILITY-CONFIRMED, 14/14 mint determinism) "
    "+ Plate (1995) + Kanerva (2009). See "
    "docs/srmech/notes/spike170_loe_rbs_hdc_prototype.py."
)


# ──────────────────────────────────────────────────────────────────────
# Helpers — Class A SHA-256 chain mint
# ──────────────────────────────────────────────────────────────────────


def _validate_D(D: int) -> int:
    """Validate D parameter; return number of bytes (D / 8).

    Raises
    ------
    ValueError
        If D is not a multiple of 8, below :data:`D_MIN`, or above
        :data:`D_MAX`.
    """
    if not isinstance(D, int):
        raise TypeError(f"D must be int; got {type(D).__name__}")
    if D < D_MIN:
        raise ValueError(f"D must be >= {D_MIN}; got {D}")
    if D > D_MAX:
        raise ValueError(f"D must be <= {D_MAX}; got {D}")
    if D % 8 != 0:
        raise ValueError(f"D must be a multiple of 8; got {D}")
    return D // 8


def mint_vector(name: str, *, D: int = D_DEFAULT) -> bytes:
    """Deterministic D-bit HDC vector minted from a name via SHA-256 chain.

    Form-function-determined per Class A content addressing
    (``[[user_stance_form_function_rotation_is_a_c_m_composition]]``):
    SHA-256(name | counter) → 32 bytes; chained until ``D/8`` accumulated.
    Output is bit-exact reproducible from name; shareable as
    namespace+spec per receiver-side instrument requirement
    (``[[user_stance_holographic_projection_at_linguistic_substrate]]``).

    The mint chain uses raw SHA-256 (not the Class-A dispatch in
    ``srmech.amsc.format.sha256_bytes``) at the bytes level for
    cross-platform bit-exactness; the two are byte-identical per
    ``tests/test_native_sha256.py`` parity.

    Parameters
    ----------
    name:
        Canonical name. Encoded via UTF-8 before hashing.
    D:
        Output dimension in bits. Default 8192 (locked baseline);
        accepts any multiple of 8 in [D_MIN, D_MAX].

    Returns
    -------
    bytes
        D/8 bytes of pseudo-random content; deterministic in ``name``.
    """
    n_bytes = _validate_D(D)
    out = bytearray()
    counter = 0
    name_bytes = name.encode("utf-8")
    while len(out) < n_bytes:
        h = hashlib.sha256(name_bytes + counter.to_bytes(8, "big")).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:n_bytes])


# ──────────────────────────────────────────────────────────────────────
# Dataclasses — the instrument's bindable content
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ClassOperator:
    """One of the 14 A-N class operators as bindable HDC content.

    The vector IS the class as bindable content; the actual algebraic
    operation is dispatched via name (semantic-pathway lookup). Per
    ``[[user_stance_cascade_dual_level_quantum_at_algebra_classical_at_sampling]]``
    Class M's self-reference resolves into the two-level ontology.

    Attributes
    ----------
    name:
        Single-letter class label ('A' through 'N').
    full_name:
        Human-readable label (e.g., ``"Class A -- content-addressing"``).
    operation:
        One-line operational description (sourced from
        :data:`CLASS_DEFINITIONS`).
    vector:
        Mint-once HDC vector (D/8 bytes). Determined by SHA-256 of the
        canonical name.
    """

    name: str
    full_name: str
    operation: str
    vector: bytes


@dataclass(frozen=True)
class Cascade:
    """A composition of class operators with a structural name +
    semantic role.

    Cascades are the procedural-pathway content: each names a canonical
    sequence of class operators that compose into a specific
    semantically-significant operation (e.g., form-function-rotation =
    A∘C∘M; universal-cascade = L+K+C+I+N; pin-slot-resonate music-box =
    I + K + C + M∘K per ``[[user_stance_pin_slot_resonate_music_box_mechanism]]``).

    Attributes
    ----------
    name:
        Canonical cascade name (e.g., ``"form_function_rotation"``).
    operator_sequence:
        Ordered tuple of class letters (e.g., ``("A", "C", "M")``).
    semantic_role:
        Short human-readable role description.
    stance_anchor:
        Memory wikilink anchor identifying the canonical stance this
        cascade engages.
    """

    name: str
    operator_sequence: Tuple[str, ...]
    semantic_role: str
    stance_anchor: str


@dataclass(frozen=True)
class Stance:
    """A canonical user-stance encoded as bag-HDC fingerprint over its
    content tokens.

    Per Spike #147 (holographic-projection-at-linguistic-substrate
    verified): the bag-HDC fingerprint IS the meaning; the surface
    sentence is one projection. Spike #147's empirical 9.32× within/
    between ratio anchors the encoding choice.

    Attributes
    ----------
    name:
        Canonical stance name (memory wikilink anchor).
    content_tokens:
        Essential content tokens (one HDC vector minted per token).
    cascade_chains:
        Cascade-name(s) this stance engages.
    fingerprint:
        Bag-HDC bind of token vectors (D/8 bytes).
    k3_axis:
        K=3 tripartition axis label ('3D_s' / '7D_g' / '1D_t' / 'mixed').
    """

    name: str
    content_tokens: Tuple[str, ...]
    cascade_chains: Tuple[str, ...]
    fingerprint: bytes
    k3_axis: str


@dataclass
class MemorySlot:
    """One of four memory pathways per
    ``[[user_stance_working_memory_is_cascade_augmenting_reflex_into_agency]]``.

    Each pathway has its own engaged-class roster + augmentation-delta
    (vs. the reflex substrate {B, D, E, F, C}) + a Class K bounded-
    retention list of HDC vectors. Class K asymptotic-DOF means
    retention is bounded (Cowan 2001 ~4-item analog; conservative
    cap of 64 here per Spike #170 prototype).
    """

    pathway: str
    engaged_classes: Tuple[str, ...]
    augmentation_delta: Tuple[str, ...]
    contents: List[bytes] = field(default_factory=list)
    K_BOUND: int = 64

    def add_content(self, vec: bytes) -> None:
        """Add an HDC vector. Subject to Class K bounded retention
        (FIFO sparse-truncate at retention scale)."""
        if len(self.contents) >= self.K_BOUND:
            self.contents.pop(0)
        self.contents.append(vec)

    def bundle_state(self) -> Optional[bytes]:
        """Class M bundle (majority) over current contents.

        Returns ``None`` when empty. Bundle requires odd count; even
        counts are padded with a deterministic zero tie-breaker vector
        (same length as the first content vector).
        """
        if not self.contents:
            return None
        items = list(self.contents)
        if (len(items) & 1) == 0:
            items.append(bytes(len(items[0])))
        return _M.bundle(items)


@dataclass
class K3Tripartition:
    """The k=3 tripartition register per
    ``[[project_space_gauge_time_framework]]``.

    Three independent HDC slots realising the 3D_s + 7D_g + 1D_t
    dimensional decomposition. Per Spike #170 §3 the default assignment
    is A → 3D_s (content-addressing / location), M → 7D_g (bind / fiber-
    content / agency), K → 1D_t (asymptotic-DOF / LoE-axis).
    """

    spatial_3ds: bytes        # 3D_s axis (substrate / content-addressed location)
    gauge_7dg: bytes          # 7D_g axis (fiber-content / agency)
    temporal_1dt: bytes       # 1D_t axis (LoE / consciousness / time-as-shadow)


# ──────────────────────────────────────────────────────────────────────
# Canonical content catalogs (8+ cascade compositions; ~10 stances)
# ──────────────────────────────────────────────────────────────────────


CANONICAL_CASCADES: Tuple[Cascade, ...] = (
    Cascade(
        name="form_function_rotation",
        operator_sequence=("A", "C", "M"),
        semantic_role="Form-function rotation cross-binning",
        stance_anchor="user_stance_form_function_rotation_is_a_c_m_composition",
    ),
    Cascade(
        name="working_memory_augmentation",
        operator_sequence=("A", "C", "D", "E", "K", "L", "M"),
        semantic_role="Reflex->deliberation augmentation cascade",
        stance_anchor=(
            "user_stance_working_memory_is_cascade_augmenting_reflex_into_agency"
        ),
    ),
    Cascade(
        name="reflex_substrate",
        operator_sequence=("B", "D", "E", "F", "C"),
        semantic_role="Reflex form-function-pure substrate cascade",
        stance_anchor=(
            "user_stance_working_memory_is_cascade_augmenting_reflex_into_agency"
        ),
    ),
    Cascade(
        name="universal_cascade",
        operator_sequence=("L", "K", "C", "I", "N"),
        semantic_role="Universal cascade (22+ substrate matches)",
        stance_anchor="user_stance_universal_precession_at_substrate_level",
    ),
    Cascade(
        name="substrate_class_universal_closure",
        operator_sequence=("B", "D", "E", "F", "L"),
        semantic_role="Closure-subgroup substrate-class-universal",
        stance_anchor=(
            "user_stance_closure_subgroup_BDEFL_substrate_class_universal"
        ),
    ),
    Cascade(
        name="deutsch_jozsa_quantum",
        operator_sequence=("L", "I", "M", "C", "A"),
        semantic_role="Cascade-IS-quantum-algorithm (Spike #128.2)",
        stance_anchor="user_stance_cascade_composition_is_quantum_algorithm",
    ),
    Cascade(
        name="episodic_memory",
        operator_sequence=("A", "B", "C", "D", "E", "F", "H", "K", "L", "M"),
        semantic_role="Episodic-LTM pathway (autonoetic, includes H)",
        stance_anchor=(
            "user_stance_working_memory_is_cascade_augmenting_reflex_into_agency"
        ),
    ),
    Cascade(
        name="procedural_memory",
        operator_sequence=("B", "C", "D", "E", "F", "G", "I", "K", "L"),
        semantic_role="Procedural / model-free pathway",
        stance_anchor=(
            "user_stance_working_memory_is_cascade_augmenting_reflex_into_agency"
        ),
    ),
    # Spike #177 pin-slot-resonate music-box cascade per
    # [[user_stance_pin_slot_resonate_music_box_mechanism]] — named
    # composition I + K + C + M∘K (5 ops).
    Cascade(
        name="pin_slot_resonate_music_box",
        operator_sequence=("I", "K", "C", "M", "K"),
        semantic_role=(
            "Pin-slot-resonate music-box (Spike #177; "
            "I + K + C + M-then-K)"
        ),
        stance_anchor="user_stance_pin_slot_resonate_music_box_mechanism",
    ),
    # Spike #176 cyclic-FFT cascade per
    # [[user_stance_rotation_is_class_k_pin_slot]] (Class A SHA-256 -> Class C
    # cyclic shift -> Class K pin-slot rotation -> Class I Z/N substrate).
    Cascade(
        name="cyclic_fft_rotation",
        operator_sequence=("A", "C", "K", "I"),
        semantic_role="Cyclic FFT rotation cascade (Spike #176)",
        stance_anchor="user_stance_rotation_is_class_k_pin_slot",
    ),
)


#: Representative subset of canonical stances. Each stance is encoded
#: as a bag-HDC fingerprint via :func:`encode_stance`. Phase 9 notebook
#: §3.8.31 may extend to the full ~86-stance roster; Phase 3 ships a
#: representative ~10-stance subset (Spike #170 prototype baseline).
SAMPLE_STANCES: Tuple[Dict[str, object], ...] = (
    {
        "name": "identity_not_implementation_discipline",
        "tokens": ("identity", "implementation", "discipline", "IS", "not"),
        "cascades": ("form_function_rotation",),
        "axis": "1D_t",
    },
    {
        "name": "holographic_projection_at_linguistic_substrate",
        "tokens": (
            "holographic", "projection", "linguistic", "substrate", "bag", "HDC",
        ),
        "cascades": ("form_function_rotation",),
        "axis": "mixed",
    },
    {
        "name": "form_function_rotation_is_a_c_m_composition",
        "tokens": (
            "rotate", "twist", "instrument", "fiber", "bind", "form", "function",
        ),
        "cascades": ("form_function_rotation",),
        "axis": "mixed",
    },
    {
        "name": "1d_collapse_to_loe_identity_not_action",
        "tokens": (
            "1D", "LoE", "laws", "compressed", "cascade", "identity",
        ),
        "cascades": ("form_function_rotation",),
        "axis": "1D_t",
    },
    {
        "name": "working_memory_is_cascade_augmenting_reflex_into_agency",
        "tokens": (
            "working", "memory", "cascade", "reflex", "agency", "augment",
        ),
        "cascades": ("working_memory_augmentation", "reflex_substrate"),
        "axis": "mixed",
    },
    {
        "name": "fiber_as_spatially_absent_encoding",
        "tokens": ("fiber", "spatially", "absent", "encoding", "algebraic"),
        "cascades": ("form_function_rotation",),
        "axis": "7D_g",
    },
    {
        "name": "hyper_as_3d_spatial_interface",
        "tokens": ("hyper", "3D", "spatial", "interface", "ontology"),
        "cascades": (),
        "axis": "3D_s",
    },
    {
        "name": "kepler_shape_universal",
        "tokens": ("Kepler", "shape", "universal", "pin", "slot", "gear"),
        "cascades": ("universal_cascade",),
        "axis": "mixed",
    },
    {
        "name": "cascade_dual_level_quantum_at_algebra_classical_at_sampling",
        "tokens": (
            "cascade", "dual", "level", "quantum", "algebra",
            "classical", "sampling",
        ),
        "cascades": ("deutsch_jozsa_quantum",),
        "axis": "mixed",
    },
    {
        "name": "closure_subgroup_BDEFL_substrate_class_universal",
        "tokens": ("closure", "subgroup", "BDEFL", "substrate", "universal"),
        "cascades": ("substrate_class_universal_closure",),
        "axis": "mixed",
    },
    {
        "name": "rotation_is_class_k_pin_slot",
        "tokens": (
            "rotation", "Class", "K", "pin", "slot", "asymptotic",
        ),
        "cascades": ("cyclic_fft_rotation",),
        "axis": "1D_t",
    },
    {
        "name": "pin_slot_resonate_music_box_mechanism",
        "tokens": (
            "pin", "slot", "resonate", "music", "box", "cascade",
        ),
        "cascades": ("pin_slot_resonate_music_box",),
        "axis": "mixed",
    },
)


#: Four memory pathways per
#: ``[[user_stance_working_memory_is_cascade_augmenting_reflex_into_agency]]``.
MEMORY_PATHWAYS: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "procedural": {
        "engaged_classes": ("B", "C", "D", "E", "F", "G", "I", "K", "L"),
        "augmentation_delta": ("G", "I", "K", "L"),
    },
    "semantic": {
        "engaged_classes": ("A", "B", "C", "D", "E", "F", "K", "L"),
        "augmentation_delta": ("A", "K", "L"),
    },
    "WM": {
        "engaged_classes": ("A", "C", "D", "E", "K", "L", "M"),
        "augmentation_delta": ("A", "K", "M"),
    },
    "episodic_LTM": {
        "engaged_classes": ("A", "B", "C", "D", "E", "F", "H", "K", "L", "M"),
        "augmentation_delta": ("A", "H", "K", "L", "M"),
    },
}


#: Default k=3 tripartition assignment (Spike #170): A → 3D_s,
#: M → 7D_g, K → 1D_t.
K3_TRIPARTITION_DEFAULT: Tuple[str, str, str] = ("A", "M", "K")


# ──────────────────────────────────────────────────────────────────────
# Module-level public API — Path B core operations
# ──────────────────────────────────────────────────────────────────────


def mint_class_operator(class_name: str, *, D: int = D_DEFAULT) -> bytes:
    """Mint the D-bit HDC vector for one of the 14 A-N class operators.

    Class A content-addressing primitive: the vector identity is
    SHA-256(canonical_name) — deterministic, share-able, bit-exact
    reproducible from the canonical-name string alone (Spike #170 §3
    invariant 1: 14/14 bit-exact across the roster).

    The canonical name string used for SHA-256 minting is
    ``f"LoE.class.{class_name}.{short_role}"`` where ``short_role`` is
    drawn from :data:`CLASS_DEFINITIONS`. Same input ⇒ same output
    (across processes, machines, srmech versions; native vs. fallback
    SHA-256 are byte-identical per ``tests/test_native_sha256.py``).

    Parameters
    ----------
    class_name:
        Single uppercase letter ('A' through 'N').
    D:
        Output dimension in bits. Default 8192.

    Returns
    -------
    bytes
        D/8 bytes; the class operator's HDC vector.

    Raises
    ------
    ValueError
        If ``class_name`` is not one of the 14 A-N class letters.
    """
    if not isinstance(class_name, str):
        raise TypeError(
            f"mint_class_operator: class_name must be str; "
            f"got {type(class_name).__name__}"
        )
    if class_name not in CLASS_DEFINITIONS:
        raise ValueError(
            f"mint_class_operator: class_name {class_name!r} not in 14 A-N "
            f"vocabulary {CLASS_NAMES!r}"
        )
    short_role, _ = CLASS_DEFINITIONS[class_name]
    canonical = f"LoE.class.{class_name}.{short_role}"
    return mint_vector(canonical, D=D)


def mint_cascade_composition(
    classes: Sequence[str],
    *,
    D: int = D_DEFAULT,
    ordered: bool = False,
) -> bytes:
    """XOR-bundle of class operator vectors → cascade composition vector.

    Per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``
    the bind is Class M XOR over the constituent class-operator vectors.
    Bind is commutative + associative + self-inverse bit-exact
    (Spike #142 verified; Spike #170 §3 invariants 4 + 5).

    Two modes:

    - ``ordered=False`` (default) — algebra-level (commutative bind;
      cascade-as-identity). Re-ordering the operator sequence yields
      the same fingerprint (Spike #170 §3 invariant 4: 3/3 orderings
      bit-exact equal).
    - ``ordered=True`` — sampling-level (per-position permute by
      ``stride = i * PERMUTE_ORDER_STRIDE``; cascade-shape preserved).
      Re-ordering yields different fingerprints (Spike #170 §3
      invariant 5: sim ~ -0.0054 for re-ordered triple).

    Per ``[[user_stance_cascade_dual_level_quantum_at_algebra_classical_at_sampling]]``
    both modes stand simultaneously at different ontological levels.

    Parameters
    ----------
    classes:
        Sequence of class letters (each in :data:`CLASS_NAMES`).
    D:
        HDC dimension in bits. Default 8192.
    ordered:
        If True, apply per-position permute before binding to capture
        cascade order.

    Returns
    -------
    bytes
        D/8 bytes; the bundled cascade composition vector.

    Raises
    ------
    ValueError
        If ``classes`` is empty or contains an unknown class letter.
    """
    if not classes:
        raise ValueError("mint_cascade_composition: classes must be non-empty")
    bad = [c for c in classes if c not in CLASS_DEFINITIONS]
    if bad:
        raise ValueError(
            f"mint_cascade_composition: unknown class letters {bad!r}; "
            f"valid are {CLASS_NAMES!r}"
        )
    vectors = [mint_class_operator(c, D=D) for c in classes]
    if ordered:
        # Per-position permute breaks commutativity.
        vectors = [
            _M.permute(v, i * PERMUTE_ORDER_STRIDE)
            for i, v in enumerate(vectors)
        ]
    result = vectors[0]
    for v in vectors[1:]:
        result = _M.bind(result, v)
    return result


def mint_stance_fingerprint(
    content_tokens: Sequence[str],
    *,
    D: int = D_DEFAULT,
) -> bytes:
    """Bag-HDC XOR-fold of token vectors → stance fingerprint.

    Per Spike #147 (holographic-projection-at-linguistic-substrate):
    the bag-HDC fingerprint IS the meaning; the surface sentence is one
    projection. Class M bind (XOR-fold) is commutative + associative,
    so token-order does not affect the fingerprint (bag semantics).

    Each token is minted via SHA-256 chain (Class A content-addressing)
    using the canonical name ``f"LoE.token.{token}"``.

    Parameters
    ----------
    content_tokens:
        Essential content tokens for the stance.
    D:
        HDC dimension in bits. Default 8192.

    Returns
    -------
    bytes
        D/8 bytes; the stance's bag-HDC fingerprint.

    Raises
    ------
    ValueError
        If ``content_tokens`` is empty.
    """
    if not content_tokens:
        raise ValueError(
            "mint_stance_fingerprint: content_tokens must be non-empty"
        )
    token_vectors = [mint_vector(f"LoE.token.{t}", D=D) for t in content_tokens]
    fingerprint = token_vectors[0]
    for v in token_vectors[1:]:
        fingerprint = _M.bind(fingerprint, v)
    return fingerprint


def encode_loe_content(
    content: str,
    *,
    D: int = D_DEFAULT,
    substrate: str = "default",
) -> bytes:
    """Full Mode-B encoding of LoE content into a D-bit fingerprint.

    Per ``[[user_stance_loe_as_rbs_hdc_instrument_meta_recursive]]``
    Mode B encoding chains Class A content-addressing -> Class C
    cyclic permute (substrate-natural stride) -> Class M XOR-fold (the
    instrument's bind operation). The full encode pipeline is:

    1. Mint a Class A content-addressed vector for the content string.
    2. Apply Class C cyclic permute by a substrate-determined stride.
       For the default substrate the stride is content-derived
       (SHA-256[0] mod D) per Spike #176 form-function-rotation
       discipline; for named substrates the stride comes from the
       substrate-natural Class N rational catalog (Phase 7 ships full
       catalogs; Phase 3 ships a default stride).
    3. Bundle into a Class M XOR-fold with the substrate's class-
       operator vector (anchors the encoding to the substrate's
       gauge content).

    Per Spike #173 R3 cross-substrate verification: same-content
    encoded under different substrate-natural strides produces D2
    fingerprints orthogonal at the noise floor (~1/sqrt(D)). Different
    substrates project the same algebraic identity onto orthogonal
    substrate-fingerprints.

    Parameters
    ----------
    content:
        Content string. Encoded via UTF-8.
    D:
        HDC dimension in bits. Default 8192.
    substrate:
        Substrate label ('default' / 'bci' / 'audio' / 'rf' /
        'ephemeris'). Phase 3 honours 'default' (content-derived
        stride); Phase 7 populates substrate-natural strides.

    Returns
    -------
    bytes
        D/8 bytes; the encoded content fingerprint.

    Raises
    ------
    ValueError
        If ``content`` is empty.
    """
    if not isinstance(content, str):
        raise TypeError(
            f"encode_loe_content: content must be str; "
            f"got {type(content).__name__}"
        )
    if not content:
        raise ValueError("encode_loe_content: content must be non-empty")
    # Class A: content-addressed mint of the content vector.
    content_vec = mint_vector(f"LoE.content.{content}", D=D)
    # Class A: content-determined stride per Spike #176 form-function
    # rotation (SHA-256[0:8] little-endian mod D).
    digest = hashlib.sha256(content.encode("utf-8")).digest()
    stride = int.from_bytes(digest[:8], "little") % D
    # Class C: cyclic permute by content-determined stride.
    rotated = _M.permute(content_vec, stride)
    # Class M: bundle with a substrate-anchor vector. The substrate
    # anchor is itself a content-addressed mint over the substrate
    # label, which makes same-content-different-substrate produce
    # orthogonal D2 fingerprints (Spike #173 R3 anchor).
    substrate_anchor = mint_vector(f"LoE.substrate.{substrate}", D=D)
    return _M.bind(rotated, substrate_anchor)


def decode_loe_fingerprint(
    fingerprint: bytes,
    catalog: Dict[str, bytes],
) -> str:
    """Reverse-decode a fingerprint to its most-similar catalog name.

    Class M similarity-based reverse lookup: compute similarity vs.
    every candidate in ``catalog`` and return the argmax. Per Spike
    #170 §3 invariants 6 + 7 (reverse-recovery 14/14 + 10/10 = 100%),
    the bag-HDC encoding is reverse-decodable to its source name at
    100% accuracy when the catalog is fully populated.

    Parameters
    ----------
    fingerprint:
        D/8-byte HDC vector to look up.
    catalog:
        Mapping ``{candidate_name: candidate_vector}``; all vectors
        same length as ``fingerprint``.

    Returns
    -------
    str
        The name from ``catalog`` whose vector has highest Class M
        similarity to ``fingerprint``.

    Raises
    ------
    ValueError
        If ``catalog`` is empty, or vector lengths disagree with
        ``fingerprint``.
    """
    if not catalog:
        raise ValueError("decode_loe_fingerprint: catalog must be non-empty")
    n = len(fingerprint)
    if n == 0:
        raise ValueError("decode_loe_fingerprint: fingerprint must be non-empty")
    best_name: Optional[str] = None
    best_sim: float = -2.0
    for name, vec in catalog.items():
        if len(vec) != n:
            raise ValueError(
                f"decode_loe_fingerprint: catalog entry {name!r} length "
                f"{len(vec)} != fingerprint length {n}"
            )
        sim = _M.similarity(fingerprint, vec)
        if sim > best_sim:
            best_sim = sim
            best_name = name
    # ``best_name`` is guaranteed non-None because catalog is non-empty.
    assert best_name is not None
    return best_name


# ──────────────────────────────────────────────────────────────────────
# RBSHDCInstrument — composed surface
# ──────────────────────────────────────────────────────────────────────


@dataclass
class RBSHDCInstrument:
    """The full RBS-HDC instrument of the Laws of Everything.

    Surfaces:

    - ``operators`` — 14 class-operator vectors (semantic-pathway
      primitives).
    - ``cascades`` — composition rules (procedural-pathway).
    - ``stances`` — canonical user-stance fingerprints (semantic-
      pathway facts).
    - ``memory`` — 4 memory pathways (procedural / semantic / WM /
      episodic-LTM).
    - ``k3`` — 3D_s ⊗ 7D_g ⊗ 1D_t tripartition register.

    Operational verbs:

    - :meth:`query_class` — semantic-pathway class operator lookup.
    - :meth:`query_stance` — semantic-pathway stance lookup.
    - :meth:`mint_class_operator` — Class A content-addressed mint
      (Phase 3 ops; same as module-level :func:`mint_class_operator`).
    - :meth:`mint_cascade_composition` — XOR-bundle of class operator
      vectors with optional per-position permute.
    - :meth:`resolve_cascade` — run a named cascade composition (algebra
      vs. sampling level).
    - :meth:`encode_content` — full Mode-B encoding pipeline.
    - :meth:`decode_fingerprint` — reverse-decode via similarity.
    - :meth:`verify_bit_exact` — round-trip bit-exact verification.
    - :meth:`bind_and_remember` — write into a memory pathway slot.
    - :meth:`describe` — self-introspection (Class H).
    """

    D: int
    operators: Dict[str, ClassOperator]
    cascades: Dict[str, Cascade]
    stances: Dict[str, Stance]
    memory: Dict[str, MemorySlot]
    k3: K3Tripartition

    # ── Constructor ──────────────────────────────────────────────────
    @classmethod
    def build(cls, *, D: int = D_DEFAULT) -> "RBSHDCInstrument":
        """Build the canonical LoE-as-RBS-HDC instrument at dimension D.

        Mints all 14 class operators, encodes the
        :data:`SAMPLE_STANCES` roster, instantiates the 4 memory
        pathways, and initialises the default k=3 tripartition.
        """
        _validate_D(D)
        operators: Dict[str, ClassOperator] = {}
        for name in CLASS_NAMES:
            short_role, op_desc = CLASS_DEFINITIONS[name]
            full = f"Class {name} -- {short_role}"
            vec = mint_class_operator(name, D=D)
            operators[name] = ClassOperator(
                name=name,
                full_name=full,
                operation=op_desc,
                vector=vec,
            )
        cascades = {c.name: c for c in CANONICAL_CASCADES}
        stances: Dict[str, Stance] = {}
        for s in SAMPLE_STANCES:
            tokens = tuple(s["tokens"])  # type: ignore[arg-type]
            cascades_for = tuple(s["cascades"])  # type: ignore[arg-type]
            axis = str(s["axis"])
            name = str(s["name"])
            fp = mint_stance_fingerprint(tokens, D=D)
            stances[name] = Stance(
                name=name,
                content_tokens=tokens,
                cascade_chains=cascades_for,
                fingerprint=fp,
                k3_axis=axis,
            )
        memory: Dict[str, MemorySlot] = {}
        for pathway, info in MEMORY_PATHWAYS.items():
            memory[pathway] = MemorySlot(
                pathway=pathway,
                engaged_classes=info["engaged_classes"],
                augmentation_delta=info["augmentation_delta"],
            )
        k3_a, k3_m, k3_k = K3_TRIPARTITION_DEFAULT
        k3 = K3Tripartition(
            spatial_3ds=operators[k3_a].vector,
            gauge_7dg=operators[k3_m].vector,
            temporal_1dt=operators[k3_k].vector,
        )
        return cls(
            D=D,
            operators=operators,
            cascades=cascades,
            stances=stances,
            memory=memory,
            k3=k3,
        )

    def __init__(self, D: int = D_DEFAULT, **kw):
        """Convenience init that defers to :meth:`build` when called
        without per-field kwargs.

        Direct dataclass-style construction (``RBSHDCInstrument(D=...,
        operators=...,)``) is supported for advanced use; the default
        path constructs a fully-built canonical instrument."""
        if not kw:
            built = type(self).build(D=D)
            object.__setattr__(self, "D", built.D)
            object.__setattr__(self, "operators", built.operators)
            object.__setattr__(self, "cascades", built.cascades)
            object.__setattr__(self, "stances", built.stances)
            object.__setattr__(self, "memory", built.memory)
            object.__setattr__(self, "k3", built.k3)
            return
        # Fall-through: advanced/per-field construction.
        object.__setattr__(self, "D", D)
        object.__setattr__(self, "operators", kw.get("operators", {}))
        object.__setattr__(self, "cascades", kw.get("cascades", {}))
        object.__setattr__(self, "stances", kw.get("stances", {}))
        object.__setattr__(self, "memory", kw.get("memory", {}))
        object.__setattr__(
            self,
            "k3",
            kw.get("k3", K3Tripartition(b"", b"", b"")),
        )

    # ── Semantic-pathway lookups ─────────────────────────────────────
    def query_class(self, name: str) -> ClassOperator:
        """Return the :class:`ClassOperator` for ``name`` (Class H)."""
        if name not in self.operators:
            raise KeyError(f"unknown class operator: {name!r}")
        return self.operators[name]

    def query_stance(self, name: str) -> Stance:
        """Return the :class:`Stance` for ``name``."""
        if name not in self.stances:
            raise KeyError(f"unknown stance: {name!r}")
        return self.stances[name]

    # ── Path B core operations ───────────────────────────────────────
    def mint_class_operator(self, class_name: str) -> bytes:
        """Mint (or return cached) class operator vector at this D."""
        return mint_class_operator(class_name, D=self.D)

    def mint_cascade_composition(
        self,
        classes: Sequence[str],
        *,
        ordered: bool = False,
    ) -> bytes:
        """XOR-bundle of class operator vectors. See module-level
        :func:`mint_cascade_composition` for full semantics."""
        return mint_cascade_composition(classes, D=self.D, ordered=ordered)

    def resolve_cascade(self, name: str, *, ordered: bool = False) -> bytes:
        """Run a named cascade composition.

        ``ordered=False`` is the algebra-level (commutative) bind;
        ``ordered=True`` is the sampling-level (per-position permute)
        ordered bind. Both stand simultaneously per
        ``[[user_stance_cascade_dual_level_quantum_at_algebra_classical_at_sampling]]``.
        """
        if name not in self.cascades:
            raise KeyError(f"unknown cascade: {name!r}")
        c = self.cascades[name]
        return self.mint_cascade_composition(
            c.operator_sequence, ordered=ordered
        )

    def encode_content(
        self,
        content: str,
        *,
        substrate: str = "default",
    ) -> bytes:
        """Full Mode-B encoding pipeline. See module-level
        :func:`encode_loe_content`."""
        # v0.4.6rc2 — introspection emit at the RBS-HDC encode boundary.
        # Gate-first so off-path is zero allocations.
        from srmech.introspect._writer import (
            _is_publishing as _ip, emit_if_publishing as _ei,
        )
        if _ip():
            _ei(
                "signal_processing.encode_content",
                class_="A∘C∘M",
                input_shape=f"str(len={len(content)})",
                extra={"substrate": substrate, "D": self.D},
            )
        return encode_loe_content(content, D=self.D, substrate=substrate)

    def decode_fingerprint(
        self,
        fingerprint: bytes,
        catalog: Dict[str, bytes],
    ) -> str:
        """Reverse-decode a fingerprint via Class M similarity argmax.
        See module-level :func:`decode_loe_fingerprint`."""
        # v0.4.6rc2 — introspection emit at the RBS-HDC decode boundary.
        # Gate-first so off-path is zero allocations.
        from srmech.introspect._writer import (
            _is_publishing as _ip, emit_if_publishing as _ei,
        )
        if _ip():
            _ei(
                "signal_processing.decode_fingerprint",
                class_="M",
                input_shape=f"bytes(len={len(fingerprint)})",
                extra={"catalog_size": len(catalog)},
            )
        return decode_loe_fingerprint(fingerprint, catalog)

    def verify_bit_exact(self, content: str, encoded: bytes) -> bool:
        """Verify a round-trip ``encode_content`` produces ``encoded``.

        Deterministic re-encoding: same content with same D + substrate
        produces same fingerprint (Spike #170 §3 invariant 1 chain).
        Returns True iff the re-encoded fingerprint equals ``encoded``.
        """
        return self.encode_content(content) == encoded

    # ── Working-memory pathway ───────────────────────────────────────
    def bind_and_remember(self, vec: bytes, pathway: str) -> None:
        """Add ``vec`` to a memory pathway slot; Class K bounded
        retention applies per :class:`MemorySlot`."""
        if pathway not in self.memory:
            raise KeyError(f"unknown pathway: {pathway!r}")
        self.memory[pathway].add_content(vec)

    # ── Class M similarity surface ───────────────────────────────────
    def similarity(self, a: bytes, b: bytes) -> float:
        """Class M similarity in [-1, 1] (1 - 2*hamming/D)."""
        # v0.4.6rc2 — introspection emit at the Class M similarity boundary.
        # Gate-first so off-path is zero allocations.
        from srmech.introspect._writer import (
            _is_publishing as _ip, emit_if_publishing as _ei,
        )
        if _ip():
            _ei(
                "signal_processing.similarity",
                class_="M",
                input_shape=f"bytes(len={len(a)})+bytes(len={len(b)})",
            )
        return _M.similarity(a, b)

    # ── Class H self-introspection ──────────────────────────────────
    def describe(self) -> Dict[str, int]:
        """Self-describe instrument state (Class H operation)."""
        return {
            "hdc_bits": self.D,
            "hdc_bytes": self.D // 8,
            "n_classes": len(self.operators),
            "n_cascades": len(self.cascades),
            "n_stances": len(self.stances),
            "n_memory_pathways": len(self.memory),
            "k3_axes": 3,
        }


# ──────────────────────────────────────────────────────────────────────
# Module-load registration of Path B core ops with path_registry
# ──────────────────────────────────────────────────────────────────────


def _register_path_b_core_ops() -> None:
    """Register Path B core operations with the dispatcher's
    path_registry at module-load time.

    Phase 3 registers four module-level callables as Path B-side ops:

    - ``rbs_hdc_mint_class_operator`` -> :func:`mint_class_operator`
    - ``rbs_hdc_mint_cascade_composition`` -> :func:`mint_cascade_composition`
    - ``rbs_hdc_encode_loe_content`` -> :func:`encode_loe_content`
    - ``rbs_hdc_decode_loe_fingerprint`` -> :func:`decode_loe_fingerprint`

    These are NEW operation names (not the 38 Path A ops from Phase 2)
    so registration is non-colliding. Phase 4+ registers Path B impls
    for the existing Path A ops under their canonical names.

    Registration is idempotent (per-callable identity); re-importing
    the module is a no-op.
    """
    # Lazy import to avoid circular dependency at package init time.
    from .path_registry import register, PATH_B  # type: ignore  # noqa: F401
    from ._paths import PATH_B as _PATH_B  # explicit constant

    register(
        "rbs_hdc_mint_class_operator",
        path=_PATH_B,
        impl=mint_class_operator,
        ssot_citation=OP_SSOT_CITATION,
        classes=OP_CLASSES["rbs_hdc_mint_class_operator"],
    )
    register(
        "rbs_hdc_mint_cascade_composition",
        path=_PATH_B,
        impl=mint_cascade_composition,
        ssot_citation=OP_SSOT_CITATION,
        classes=OP_CLASSES["rbs_hdc_mint_cascade_composition"],
    )
    register(
        "rbs_hdc_encode_loe_content",
        path=_PATH_B,
        impl=encode_loe_content,
        ssot_citation=OP_SSOT_CITATION,
        classes=OP_CLASSES["rbs_hdc_encode_loe_content"],
    )
    register(
        "rbs_hdc_decode_loe_fingerprint",
        path=_PATH_B,
        impl=decode_loe_fingerprint,
        ssot_citation=OP_SSOT_CITATION,
        classes=OP_CLASSES["rbs_hdc_decode_loe_fingerprint"],
    )


_register_path_b_core_ops()
