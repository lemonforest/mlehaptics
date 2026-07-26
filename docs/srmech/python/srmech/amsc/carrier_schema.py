"""srmech.amsc.carrier_schema — the CARRIER (operand) introspection surface
(rc205; gh #1293) — the noun-side DUAL of :mod:`srmech.amsc.tool_schema`.

``tool_schema`` exposes the **ops** (the verbs — the A–N operator vocabulary)
richly; this module exposes the **carrier TYPES** (the nouns — the operand
vocabulary) the ops consume and produce. Before rc205 a consumer discovering
the carriers had to scrape :func:`srmech.amsc.carrier_ladder.
carrier_ladder_descriptor` (ladder/rung ints + ``adds_variable``) with no
human-readable description per carrier, so introspection could not say *what a
``TriPoly`` IS* beyond "rung 3" (the Siona / RBS-LM self-hosting finding —
``docs/srmech/rbs_lm_research/R-RBS-LM-FINDING_1110_*``; UPSTREAM_NOTES §91).

:func:`carrier_schema` returns, per carrier::

    {
      "<name>": {
        "name":        "<name>",
        "description": "<one line: what it is / variable semantics / when>",
        "ladder":      "variable" | "variable_q" | "cayley_dickson" | None,
        "rung":        <int> | None,
        "variables":   ["k", ...],        # shift variables (poly ladders)
        "capability": {                   # rc339 — what the carrier can DO
          "product":     "<the closed binary op the verdicts describe>" | None,
          "address":     "exact" | None,
          "compose":     "full" | "zero_divisors" | "unclassified" | None,
          "turn":        "non_commuting" | "abelian_only" | "unclassified" | None,
          "commutative": True | False | None,
          "varies_with": "dim" | "element_type" | None,
        },
        "ops": {                          # back-index into tool_schema
          "consumes": ["srmech....", ...],   # full ToolEntry names
          "produces": ["srmech....", ...],
        },
      },
      ...
    }

The ``capability`` block (rc339, `#T967`)
----------------------------------------
Before rc339 the registry said what each carrier IS and never what it can DO,
and the only ceilings :func:`srmech.introspect.describe` published were
``cd_max_dim`` 256 and ``cd_dense_max_dim`` 64 — **both ADDRESSING bounds**. A
caller reading 256 and reaching for a TURN there was reading a permissive number
with no capability attached; non-commuting turn composition has been dead since
dim 8. This block is the missing half. The measured ontology behind it lives in
``docs/srmech/notes/carrier_capability_ontology_rc339.py`` (generating code) and
its NDJSON; the dimension ceilings are
:data:`~srmech.amsc.cascade.cayley_dickson.CD_COMPOSE_MAX_DIM` and
:data:`~srmech.amsc.cascade.cayley_dickson.CD_TURN_MAX_DIM`.

**The three capabilities.**

``address``
    ``"exact"`` — an index / key / degree / slot recovers an individual element
    bit-exactly. Every carrier srmech ships is exactly addressed; the field is
    kept anyway so a carrier that ever is NOT has to say so out loud rather
    than inherit silence. On the Cayley–Dickson ladder this is the signed
    permutation ``e_i·e_j = ±e_{i XOR j}``, measured exact with zero failures
    through dim 64.

``compose``
    ``"full"`` — the ``product`` is closed with NO zero divisors.
    ``"zero_divisors"`` — closed, but ``x·y == 0`` is reachable with ``x ≠ 0``
    and ``y ≠ 0``. ``"unclassified"`` — srmech has not established which, and
    says so rather than guessing. ``None`` — the carrier has no closed binary
    product on srmech's surface, so the question does not apply.

``turn``
    Does a turn FOLD? A turn composes iff left multiplication is a
    representation, ``L_x ∘ L_y == L_{x·y}``. ``"non_commuting"`` — it holds
    AND the product is non-commutative, so a which-way turn survives being
    folded (ℍ / Q₈ / matmul). ``"abelian_only"`` — only the commuting pairs
    compose. Read that together with ``commutative``: for a commutative carrier
    it is vacuous; for a NON-commutative one (``commutative`` False) it is a
    genuine DEGRADATION, and it is exactly what happens at 𝕆, where the
    turn-composing set and the commuting set were measured to be THE SAME SET.

**The worst-case rule.** A carrier's published capability is the guarantee that
holds across EVERYTHING the carrier admits — not its best case. ``CDRegister``
admits any power-of-two dim in ``[1, CD_MAX_DIM]``, so it publishes the dim-256
answer (``zero_divisors`` / ``abelian_only``), not the dim-4 one; ``HV`` publishes
the weakest of its three genome ``element_type`` rungs. ``varies_with`` names the
knob that can improve it, and points the caller at
``describe()["limits"]["element_types"]`` for the per-rung answer. Publishing the
best case is the failure mode this whole block exists to remove.

The ``ops`` back-index is **DERIVED, never hand-maintained**: it unions

* a word-boundary token scan of every registered ToolEntry's declared
  ``parameters[].type`` / ``returns.type`` strings (the tool_schema SSoT), and
* the rc120 per-op CARRIER CONTRACT (:data:`srmech.amsc.carrier_ladder.
  _OP_CONTRACTS`) resolved through the ladder rung → carrier-name map (so the
  Cayley–Dickson ops — whose ToolEntry type strings say ``list[float]`` — still
  index under ``quaternion`` / ``octonion`` / ``sedenion``).

The ``ladder`` / ``rung`` values agree with ``carrier_ladder_descriptor()``
(tested); the Cayley–Dickson rungs surface under their value-carrier names
(``float``/``complex``/``quaternion``/``octonion``/``sedenion`` = the
descriptor's R/C/H/O/S keys at dims 1/2/4/8/16).

Scope: the registry covers the carriers ON the public op surface — every
srmech carrier type a registered ToolEntry consumes or produces, plus the
three promote/project ladders' rungs. Internal exact representations no
public op surfaces (``QMat`` / ``Qalg`` / the genus-``RiemannTheta`` family)
join when an op surfaces them (the drift ratchet in
``tests/test_carrier_schema_rc205.py`` forces the addition).

Native dispatch: when the rc205 C peer is loaded (``srmech_carrier_schema``
over the compiled-in ``srmech_carrier_registry`` const table — GENERATED by
``c/tools/gen_carrier_registry.py``, the rc184/rc202 codegen model) and no
profile tools are registered, :func:`carrier_schema` parses the C canonical
JSON — BYTE-IDENTICAL to ``json.dumps(<pure>, sort_keys=True,
separators=(",", ":"))`` (the sha256 hash-ratchet contract locking the C table
to this Python SSoT). A profile tool, a stale/absent lib, or a non-OK status
falls back to the pure path (never a wrong answer).

Pure data + a derivation over the live registry — no numerical kernel; no
float math, no numpy, no ``abs()``.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .carrier_ladder import _OP_CONTRACTS

# rc241 (#839) — the generated per-carrier CONSTRUCTION example (the operand-side
# peer of _tool_docs.py). Guarded so a stripped/missing module never breaks import.
try:  # pragma: no cover - trivial import guard
    from ._carrier_examples import CARRIER_EXAMPLES as _CARRIER_EXAMPLES
except Exception:  # noqa: BLE001
    _CARRIER_EXAMPLES: Dict[str, Dict[str, Any]] = {}

__all__ = ["carrier_schema"]


# ── the authored per-carrier metadata (the human-readable half) ───────────────
#
# name -> {description, ladder, rung, variables}. The ops back-index is DERIVED
# (below), never authored. ladder/rung must agree with
# carrier_ladder_descriptor() — tests/test_carrier_schema_rc205.py pins it.

_CARRIERS: Dict[str, Dict[str, Any]] = {
    # ── the ordinary variable ladder (Poly → BiPoly → TriPoly) ───────────────
    "Poly": {
        "description": (
            "Exact-ℚ univariate polynomial in the summation variable k — a "
            "trimmed tuple of exact Q coefficients in ascending degree, "
            "immutable. Rung 1 of the ordinary variable ladder: the operand "
            "gosper telescopes over; promote (trivial embedding) to BiPoly "
            "to feed zeilberger."),
        "ladder": "variable", "rung": 1, "variables": ["k"],
    },
    "BiPoly": {
        "description": (
            "Exact-ℚ bivariate polynomial in (n, k) — a polynomial in k "
            "whose coefficients are Poly in n. Rung 2 of the ordinary "
            "variable ladder: the substrate the zeilberger / wz_certificate "
            "term-ratios r_n(n,k) / r_k(n,k) ride."),
        "ladder": "variable", "rung": 2, "variables": ["n", "k"],
    },
    "TriPoly": {
        "description": (
            "Exact-ℚ trivariate polynomial in (n, j, k) — a trimmed tuple of "
            "BiPoly in (n,k) indexed by j-degree, immutable. Rung 3 of the "
            "ordinary variable ladder: the operand of apagodu_zeilberger "
            "(multivariate sums-of-sums creative telescoping)."),
        "ladder": "variable", "rung": 3, "variables": ["n", "j", "k"],
    },
    # ── the q variable ladder (QPoly → QBiPoly) ───────────────────────────────
    "QPoly": {
        "description": (
            "Exact q-shift carrier: a Laurent polynomial in x = qⁿ with "
            "exact ℚ[q] (Poly-in-q) coefficients, immutable — the q-analog "
            "of Poly. Rung 1 of the q variable ladder: the operand of "
            "q_gosper; promote to QBiPoly to feed q_zeilberger."),
        "ladder": "variable_q", "rung": 1, "variables": ["x=qⁿ"],
    },
    "QBiPoly": {
        "description": (
            "Exact bivariate-q polynomial in (X, Y) = (qⁿ, qᵏ) — a "
            "polynomial in Y whose coefficients are QPoly in X (Laurent "
            "over ℚ[q]). Rung 2 of the q variable ladder: the substrate of "
            "q_zeilberger / q_wz_certificate."),
        "ladder": "variable_q", "rung": 2, "variables": ["X=qⁿ", "Y=qᵏ"],
    },
    # ── the Cayley–Dickson ladder (ℝ ↪ ℂ ↪ ℍ ↪ 𝕆 ↪ 𝕊, keyed by dim) ──────────
    "float": {
        "description": (
            "The float64 scalar — rung 1 (R) of the Cayley–Dickson ladder "
            "and the FPU last-mile carrier: numeric results collapse to "
            "float only at the observed-frame read-out (exact carriers stay "
            "rational in the fiber; frame rotation is the terminal op)."),
        "ladder": "cayley_dickson", "rung": 1, "variables": [],
    },
    "complex": {
        "description": (
            "The complex scalar — rung 2 (C) of the Cayley–Dickson ladder, "
            "carried as (re, im) float pairs (interleaved on the native "
            "side, C99 double _Complex layout): the spectral / "
            "eigendecomposition read-out scalar."),
        "ladder": "cayley_dickson", "rung": 2, "variables": [],
    },
    "quaternion": {
        "description": (
            "A quaternion as a length-4 float sequence (1, i, j, k basis) — "
            "rung 4 (H) of the Cayley–Dickson ladder: the operand of the "
            "qm.quaternion.* family and the generic cascade cd_* ops."),
        "ladder": "cayley_dickson", "rung": 4, "variables": [],
    },
    "octonion": {
        "description": (
            "An octonion as a length-8 float sequence (e0..e7 basis) — rung "
            "8 (O) of the Cayley–Dickson ladder, the LAST division algebra "
            "(Hurwitz): the operand of the qm.octonion.* family, the "
            "octonion DFT, and the generic cascade cd_* ops."),
        "ladder": "cayley_dickson", "rung": 8, "variables": [],
    },
    "sedenion": {
        "description": (
            "A sedenion as a length-16 float sequence (e0..e15 basis) — "
            "rung 16 (S) of the Cayley–Dickson ladder, PAST Hurwitz (zero "
            "divisors appear — the open-exterior boundary): the "
            "SedenionRegister's address space and the cd_* boundary "
            "demonstrator operand."),
        "ladder": "cayley_dickson", "rung": 16, "variables": [],
    },
    # ── scalar carriers off the ladders ───────────────────────────────────────
    "int": {
        "description": (
            "The bit-exact integer — Python arbitrary-precision int, "
            "mirrored by srmech_bigint in C: the fiber-side carrier every "
            "exact cascade accumulates in (add/sub/shift; no float until "
            "the terminal read-out)."),
        "ladder": None, "rung": None, "variables": [],
    },
    "Q": {
        "description": (
            "srmech's exact rational scalar — a reduced (num, den) integer "
            "pair that compares like a float and collapses to one only via "
            "float(q): THE exact-rational carrier across srmech (#845 — it "
            "subsumed the former stdlib-Fraction interchange carrier). It is "
            "the return carrier of the exact-LA boundaries (dense_solve "
            "exact=True, schur_complement, cd_norm_sq), the Class-N series-"
            "truncate trig/exp/log surface, and the HDC similarity scores. A "
            "stdlib fractions.Fraction is still ACCEPTED on input (numeric "
            "protocol), it is simply never the emitted carrier."),
        "ladder": None, "rung": None, "variables": [],
    },
    # ── the float-LA carriers (numpy-free array('d') family) ─────────────────
    "Mat": {
        "description": (
            "Numpy-free dense matrix: a flat array('d') + (n_rows, n_cols); "
            "complex entries stored interleaved (re, im). THE float linear-"
            "algebra carrier — fed zero-copy to the native dense kernels "
            "(mat_matmul / mat_solve / mat_eigvals / mat_svd / "
            "hermitian_eigendecompose). As the graph Laplacian L "
            "(dense_laplacian / magnetic_laplacian) it is the F1216 Class-L "
            "LONG-TERM relational STORE: exact, addressed, directional, "
            "reconstructible, GROWS with knowledge (the genome / disk)."),
        "ladder": None, "rung": None, "variables": [],
    },
    "Vec": {
        "description": (
            "Numpy-free dense vector: a flat array('d') + a length n; "
            "complex interleaved. The 1-D peer of Mat for matvec / dot / "
            "eigenvector read-outs."),
        "ladder": None, "rung": None, "variables": [],
    },
    "HV": {
        "description": (
            "Numpy-free Klein-4 hypervector: an array('B') sector buffer + "
            "a sectors count. The Class-M HDC carrier (bind / bundle / "
            "permute / similarity and the klein4_* sector ops). F1216: "
            "Class-M = WORKING MEMORY / active context — fuzzy, composable, "
            "BOUNDED (the ~24-bind span), gracefully decays; a transient "
            "holographic READ of the relational store (bundle is a lossy "
            "sketch), never the store itself. Bridge L↔M = the reversible "
            "spectral basis-change (eigen / Walsh-Hadamard)."),
        "ladder": None, "rung": None, "variables": [],
    },
    # ── the elliptic row carriers ─────────────────────────────────────────────
    "EllMonomial": {
        "description": (
            "Exact signed Laurent monomial coeff·∏symᵉ over the elliptic "
            "argument lattice (symbols q / p / parameters), immutable — the "
            "argument-carrier of the elliptic row: the thing a theta factor "
            "is taken of."),
        "ladder": None, "rung": None, "variables": [],
    },
    "EllRatio": {
        "description": (
            "Exact elliptic-hypergeometric TERM-RATIO: a product "
            "prefactor·∏(num θ)/∏(den θ) of theta factors over an "
            "EllMonomial prefactor, immutable — the multiplicative carrier "
            "the elliptic engine (elliptic_gosper → elliptic_zeilberger → "
            "elliptic_wz_certificate) telescopes over."),
        "ladder": None, "rung": None, "variables": [],
    },
    "ThetaSum": {
        "description": (
            "Exact cleared rational theta-function: a ℚ(q,p)-linear SUM of "
            "theta-products over one theta-product denominator — the "
            "ADDITIVE layer above EllRatio that genuine elliptic creative "
            "telescoping needs (theta-quotients are not additively "
            "closed)."),
        "ladder": None, "rung": None, "variables": [],
    },
    "ThetaBracketSum": {
        "description": (
            "Exact free commutative ℤ-algebra of genus-g odd Riemann-theta "
            "BRACKET products coeff·∏[u_i] ([-u]=-[u], the pure Class-K "
            "antisymmetry) — the GENUS-AXIS additive carrier the higher-genus "
            "(Spiridonov math/0408366) theta-multisum reduction row lives in; "
            "the genus-g peer of ThetaSum."),
        "ladder": None, "rung": None, "variables": [],
    },
    # ── the weight-axis / harmonic-Maass carriers ─────────────────────────────
    "UnaryTheta": {
        "description": (
            "Exact unary theta series as a finite generating rule emitting "
            "integer q-power coefficients to any depth — the weight-axis "
            "theta carrier and the SHADOW slot of a harmonic-Maass pair."),
        "ladder": None, "rung": None, "variables": [],
    },
    "MockQSeries": {
        "description": (
            "Thin exact q-series carrier for the HOLOMORPHIC mock part f⁺ "
            "of a harmonic Maass form: a leading rational q-power + a "
            "finite generating rule emitting exact coefficients to any "
            "depth, immutable."),
        "ladder": None, "rung": None, "variables": [],
    },
    "HarmonicMaass": {
        "description": (
            "A harmonic (weak) Maass form as the FINITE EXACT PAIR "
            "(hol, shadow) that determines it (the Bruinier–Funke shadow "
            "map); the non-holomorphic completion is recoverable, not "
            "stored — the operand-irrepresentable boundary made explicit."),
        "ladder": None, "rung": None, "variables": [],
    },
    # ── the HDC domain-object carriers surfaced by cascade factories ─────────
    "One": {
        "description": (
            "The One S(σ,θ) — the single generator of the 14-D substrate as "
            "an addressable HDC object (σ rotation × θ grading): produced "
            "by cascade.the_one, read by the one_* accessors / to_scalar."),
        "ladder": None, "rung": None, "variables": [],
    },
    "SedenionRegister": {
        "description": (
            "Sedenion (dim-16) addressable RBS-HDC register: 16 named "
            "slots, an octonion reversible working word, a Hamming EC/carry "
            "block, and a CD-respecting navigate — produced by "
            "cascade.sedenion_register, driven via the sed_* class "
            "surface."),
        "ladder": None, "rung": None, "variables": [],
    },
    "CDRegister": {
        "description": (
            "General N-slot addressable RBS-HDC register over a "
            "Cayley–Dickson algebra of dimension n (any power of two in "
            "[1, CD_MAX_DIM]): n content-keyed slots e0..e{n-1} addressed by "
            "minted hypervectors, the octonion block e0..e7 as the reversible "
            "working set at every rung and the remainder as the carry/EC "
            "block, plus a CD-respecting navigate whose slot routing is the "
            "signed permutation e_i·e_j = ±e_k. Carries the SAME operand as "
            "SedenionRegister with the slot bound as a parameter rather than "
            "a constant — SedenionRegister is its n=16 special case, retained "
            "as the independent oracle the general form is gated against "
            "(namespace='SEDENION' at dim 16 reproduces it bit-exactly). "
            "Produced by cascade.cd_register."),
        "ladder": None, "rung": None, "variables": [],
    },
}


# ── the per-carrier CAPABILITY table (rc339, `#T967`) ─────────────────────────
#
# What each carrier can DO, as opposed to what it IS. Held as its own table
# rather than folded into _CARRIERS so the whole ontology reads as ONE object,
# and so the key-set assertion below FORCES a new carrier to declare capability
# instead of inheriting silence. Vocabulary + the worst-case rule: module
# docstring. Measured ontology + generating code:
# docs/srmech/notes/carrier_capability_ontology_rc339.py.
#
# "compose"/"turn" describe the carrier's `product` — the closed binary op under
# which it is an algebra. Where a carrier has two closed products (Mat: `@`
# matmul AND `*` elementwise) the ALGEBRA product is the one named; where it has
# none (One, HarmonicMaass) every verdict is None, because the question does not
# apply and a False would read as a measured negative.

_CAP_EXACT = "exact"
_CAP_FULL = "full"
_CAP_ZERO_DIVISORS = "zero_divisors"
_CAP_NON_COMMUTING = "non_commuting"
_CAP_ABELIAN_ONLY = "abelian_only"
_CAP_UNCLASSIFIED = "unclassified"


def _cap(product, compose, turn, commutative, varies_with=None):
    """One capability row. ``address`` is ``"exact"`` iff the carrier has any
    structure at all — every srmech carrier is exactly addressed, and the field
    exists so a future one that is not must say so."""
    return {
        "product": product,
        "address": _CAP_EXACT,
        "compose": compose,
        "turn": turn,
        "commutative": commutative,
        "varies_with": varies_with,
    }


#: No closed binary product on srmech's surface → the compose / turn question
#: does not apply. Distinct from ``"unclassified"`` (it applies; we have not
#: established the answer).
_CAP_NO_PRODUCT = _cap(None, None, None, None)

_CAPABILITY: Dict[str, Dict[str, Any]] = {
    # ── the polynomial ladders: commutative integral domains over ℚ ──────────
    "Poly": _cap("polynomial multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    "BiPoly": _cap("polynomial multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    "TriPoly": _cap("polynomial multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    "QPoly": _cap("Laurent multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    "QBiPoly": _cap("Laurent multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    # ── the Cayley–Dickson ladder: THE capability ladder ─────────────────────
    # Hurwitz (1898): 1, 2, 4, 8 are the only normed division algebras, so
    # `compose` dies between octonion and sedenion. `turn` dies one rung
    # EARLIER, between quaternion and octonion — the two ceilings are NOT the
    # same wall, and conflating them is how "cd_max_dim: 256" came to imply a
    # turn that does not exist.
    "float": _cap("field multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    "complex": _cap("field multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    # ℍ — the LAST rung whose non-commuting turns fold: measured 16/16 basis
    # pairs compose while only 10/16 commute, so 6 non-commuting pairs survive.
    "quaternion": _cap("cd_mult (H)", _CAP_FULL, _CAP_NON_COMMUTING, False),
    # 𝕆 — still a division algebra (compose survives, and this rung exists to
    # reach e₄..e₇), but turn-composing == commuting AS SETS (88 == 88, both
    # differences empty). Non-commuting turn composition is gone.
    "octonion": _cap("cd_mult (O)", _CAP_FULL, _CAP_ABELIAN_ONLY, False),
    # 𝕊 — past Hurwitz. srmech ships the witness: cascade.sedenion_zero_divisor_witness.
    "sedenion": _cap("cd_mult (S)", _CAP_ZERO_DIVISORS, _CAP_ABELIAN_ONLY, False),
    # ── the exact scalars ────────────────────────────────────────────────────
    "int": _cap("integer multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    "Q": _cap("rational multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    # ── the float-LA carriers ────────────────────────────────────────────────
    # Mat's ALGEBRA product is `@` (mat_matmul): associative and NON-commutative,
    # so turns fold with their which-way intact — and it has zero divisors
    # (any singular pair), so it composes turns without being a composition
    # algebra. That combination is exactly why the two verdicts are separate
    # fields: `turn` is not downstream of `compose`.
    "Mat": _cap("mat_matmul (@)", _CAP_ZERO_DIVISORS, _CAP_NON_COMMUTING, False),
    # Vec has no closed non-commutative product — `@` is the dot and leaves the
    # carrier (Vec × Vec → scalar). Its closed op is the elementwise Hadamard
    # product: commutative, associative, and full of zero divisors (any two
    # complementary support patterns).
    "Vec": _cap("elementwise (*)", _CAP_ZERO_DIVISORS, _CAP_ABELIAN_ONLY, True),
    # HV's product IS the genome coupling, and WHICH coupling is set by the
    # §60 header's element_type — klein4 (abelian XOR) / Q8 (non-abelian, turns
    # fold) / octonion (abelian-only turns). Per the worst-case rule the row
    # publishes the weakest of the three; `varies_with` points at the knob and
    # at describe()["limits"]["element_types"] for the per-rung answer. All
    # three are group / loop products, so none of them has zero divisors.
    "HV": _cap("genome coupling (quad_turn)", _CAP_FULL, _CAP_ABELIAN_ONLY,
               False, varies_with="element_type"),
    # ── the elliptic row ─────────────────────────────────────────────────────
    # A monomial / theta-quotient product is zero only if a coefficient is:
    # the symbol part is a free abelian group, so no zero divisors.
    "EllMonomial": _cap("monomial multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    "EllRatio": _cap("theta-quotient multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True),
    # ThetaSum.__mul__ is commutative and associative by construction, but
    # whether the cleared theta ring is an integral domain is NOT established
    # in-tree. UNCLASSIFIED is the honest verdict; a guess here would be
    # precisely the kind of unearned claim the attestation discipline exists to
    # stop.
    "ThetaSum": _cap("ThetaSum multiply", _CAP_UNCLASSIFIED,
                     _CAP_ABELIAN_ONLY, True),
    # A FREE commutative ℤ-algebra on the bracket generators is a polynomial
    # ring, hence an integral domain.
    "ThetaBracketSum": _cap("bracket-product multiply", _CAP_FULL,
                            _CAP_ABELIAN_ONLY, True),
    # ── carriers with no closed binary product ───────────────────────────────
    "UnaryTheta": _CAP_NO_PRODUCT,
    "MockQSeries": _CAP_NO_PRODUCT,
    "HarmonicMaass": _CAP_NO_PRODUCT,
    "One": _CAP_NO_PRODUCT,
    # ── the addressable registers ────────────────────────────────────────────
    # The register's product is its CD-respecting navigate — routing a slot
    # through ×e_j. At dim 16 the ambient algebra is 𝕊, which is why the
    # register's REVERSIBLE working set is the octonion block e₀..e₇ and the
    # remainder is carry/EC: the design already encodes this ceiling, and rc339
    # makes introspection say so.
    "SedenionRegister": _cap("cd_navigate (S, dim 16)", _CAP_ZERO_DIVISORS,
                             _CAP_ABELIAN_ONLY, False),
    # Worst case over every dim in [1, CD_MAX_DIM] — NOT the dim-4 best case.
    # This row is the direct answer to the rc339 defect: a caller who read
    # cd_max_dim 256 and reached for a turn gets told here that at the dims this
    # register admits, turns are abelian-only and the product has zero divisors.
    "CDRegister": _cap("cd_navigate (CD dim n <= CD_MAX_DIM)",
                       _CAP_ZERO_DIVISORS, _CAP_ABELIAN_ONLY, False,
                       varies_with="dim"),
}

# A new carrier MUST declare its capability. Without this, adding a carrier
# would silently publish a capability-less row and re-open exactly the gap
# rc339 closed. An explicit raise, not an `assert` — `python -O` strips asserts,
# and a published-surface guard that evaporates under an interpreter flag is the
# false-green shape this rc exists to remove. Cheap: one set compare at import.
if set(_CAPABILITY) != set(_CARRIERS):  # pragma: no cover — import-time guard
    raise RuntimeError(
        "carrier/capability drift: "
        f"{sorted(set(_CARRIERS) ^ set(_CAPABILITY))} — every registered "
        "carrier must declare {product, address, compose, turn, commutative, "
        "varies_with}")


# The ladder rung → carrier-name maps (the value-carrier names of the
# carrier_ladder_descriptor rung tables; cayley_dickson keys R/C/H/O/S surface
# under their Python value-carrier names). Tested against the descriptor.
_LADDER_RUNG_CARRIERS: Dict[str, Dict[int, str]] = {
    "variable": {1: "Poly", 2: "BiPoly", 3: "TriPoly"},
    "variable_q": {1: "QPoly", 2: "QBiPoly"},
    "cayley_dickson": {
        1: "float", 2: "complex", 4: "quaternion", 8: "octonion",
        16: "sedenion",
    },
}


def _token_re(name: str) -> "re.Pattern[str]":
    """A word-boundary regex for carrier token ``name`` inside a free-form
    ToolEntry type string ('Poly | BiPoly', 'list[list[Fraction]]', …).
    Identifier-boundary lookarounds so 'Poly' never matches inside 'QPoly'
    and 'int' never matches inside 'uint32'."""
    return re.compile(
        r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])")


#: An ``array.array`` typecode as it appears in a ToolEntry type string —
#: ``array('I')``, ``array('Q')``, ``array('d')``. The quoted character is a
#: STDLIB TYPECODE, not a carrier name, but the identifier-boundary lookarounds
#: in :func:`_token_re` treat a quote as a boundary, so a bare single-letter
#: carrier name matches straight through the quotes.
#:
#: rc295 tripped this for real: ``hdc.klein4_bundle_sector_scores`` returns
#: ``array('Q')`` (uint64 — the agreement product reaches n², past uint32), and
#: the scan read that ``'Q'`` as srmech's exact-rational **Q** carrier and filed
#: the op under ``Q.produces``. It produces no ``Q``. Before rc295 no registered
#: ToolEntry type carried ``array('Q')``, so the hazard was latent, not benign —
#: ``I`` is the only other typecode in the corpus and no carrier is named ``I``.
#: Stripping the typecode before the scan is a no-op on every pre-rc295 entry.
_ARRAY_TYPECODE_RE = re.compile(r"array\((['\"])[A-Za-z](['\"])\)")


def _strip_array_typecodes(type_str: str) -> str:
    """Blank out ``array('X')`` typecodes so the carrier scan cannot read a
    stdlib typecode letter as a single-letter carrier name (see
    :data:`_ARRAY_TYPECODE_RE`). The ``array`` token itself is kept — it is not
    a carrier name, so keeping it costs nothing and keeps the string legible."""
    return _ARRAY_TYPECODE_RE.sub("array", type_str)


def _ladder_slot_carriers(slot: Dict[str, Any], *, produces: bool) -> List[str]:
    """The carrier names a rc120 contract SLOT touches. A non-ladder slot
    contributes nothing here (the ToolEntry token scan covers it); a ladder
    slot resolves through :data:`_LADDER_RUNG_CARRIERS`:

    * a fixed int rung → that rung's carrier;
    * ``"any"`` (consume) / ``"same"`` / ``"arg:<param>"`` (produce) → every
      rung of the ladder (variadic — e.g. ``poly_promote(p, n_vars=cur)``
      returns the input rung unchanged);
    * ``"step_down"`` (produce) → every rung EXCEPT the highest (project
      always descends)."""
    ladder = slot.get("ladder")
    if ladder is None:
        return []
    rungs = _LADDER_RUNG_CARRIERS[ladder]
    rung = slot.get("rung")
    if isinstance(rung, int) and not isinstance(rung, bool):
        return [rungs[rung]]
    if rung == "step_down":
        top = max(rungs)
        return [name for r, name in rungs.items() if r != top]
    # "any" / "same" / "arg:<param>" — variadic over the whole ladder.
    assert produces or rung == "any", f"unexpected consume rung {rung!r}"
    return list(rungs.values())


def _derive_ops_index() -> Dict[str, Dict[str, List[str]]]:
    """The DERIVED per-carrier ops back-index: carrier name →
    ``{"consumes": [tool names], "produces": [tool names]}`` (each sorted,
    deduped). Union of the ToolEntry type-token scan and the rc120 carrier
    contract (see module docstring). Calls ``warmup_all()`` first so the
    registry is fully populated regardless of entry path (the rc9 orphan
    lesson) — this also makes the pure path deterministic against the
    compiled-in C table."""
    from .tool_schema import get_tool_schema, warmup_all

    warmup_all()
    consumes: Dict[str, set] = {name: set() for name in _CARRIERS}
    produces: Dict[str, set] = {name: set() for name in _CARRIERS}
    patterns = {name: _token_re(name) for name in _CARRIERS}

    for tool in get_tool_schema().tools:
        param_types = _strip_array_typecodes(
            " ".join(p.type for p in tool.parameters))
        ret_type = _strip_array_typecodes(
            tool.returns.type if tool.returns is not None else "")
        for name, pat in patterns.items():
            if param_types and pat.search(param_types):
                consumes[name].add(tool.name)
            if ret_type and pat.search(ret_type):
                produces[name].add(tool.name)

    for spec in _OP_CONTRACTS.values():
        for name in _ladder_slot_carriers(spec["consumes"], produces=False):
            consumes[name].add(spec["tool"])
        for name in _ladder_slot_carriers(spec["produces"], produces=True):
            produces[name].add(spec["tool"])

    return {
        name: {
            "consumes": sorted(consumes[name]),
            "produces": sorted(produces[name]),
        }
        for name in _CARRIERS
    }


def _pure_carrier_schema() -> Dict[str, Dict[str, Any]]:
    """The pure-Python carrier schema (the SSoT the C const table is
    generated from and hash-ratcheted against). Fresh (mutation-safe)
    structures each call."""
    ops_index = _derive_ops_index()
    out: Dict[str, Dict[str, Any]] = {}
    for name, meta in _CARRIERS.items():
        out[name] = {
            "name": name,
            "description": meta["description"],
            "ladder": meta["ladder"],
            "rung": meta["rung"],
            "variables": list(meta["variables"]),
            # rc339 (`#T967`) — what the carrier can DO, not only what it is.
            "capability": dict(_CAPABILITY[name]),
            "ops": ops_index[name],
        }
        # rc241 (#839) — the per-carrier construction example, when present.
        ex = _CARRIER_EXAMPLES.get(name)
        if ex:
            out[name]["example"] = dict(ex)
    return out


def _native_carrier_schema() -> Optional[Dict[str, Dict[str, Any]]]:
    """The rc205 C ``srmech_carrier_schema`` canonical JSON parsed to a
    dict, or ``None`` when the native peer is unavailable / returns non-OK
    (caller falls back to the pure path)."""
    try:
        from . import _native
    except Exception:  # pragma: no cover — defensive; _native always imports
        return None
    raw = _native.carrier_schema_json_c()
    if raw is None:
        return None
    return json.loads(raw.decode("utf-8"))


def carrier_schema() -> Dict[str, Dict[str, Any]]:
    """The CARRIER introspection registry (rc205; gh #1293) — per carrier
    ``{"name", "description", "ladder", "rung", "variables", "capability",
    "ops"}`` keyed by carrier name; the operand-side dual of ``tool_schema``
    (see the module docstring for the full shape + the derivation of ``ops``).

    ``capability`` (rc339, `#T967`) is what the carrier can DO —
    ``{product, address, compose, turn, commutative, varies_with}``. It reports
    the WORST case over everything the carrier admits, so a permissive number
    elsewhere can never be read as a capability the carrier does not have.

    Native-dispatched: when the rc205 C peer is loaded AND no profile tools
    are registered (a profile tool could extend the live ops back-index the
    compiled-in table cannot know), the payload comes from the bare-C-host
    ``srmech_carrier_schema`` over the ``srmech_carrier_registry`` const
    table — VALUE-identical to the pure path (byte-identical in canonical
    form; the sha256 hash-ratchet in tests locks the two). Otherwise the
    pure path derives it live."""
    from .tool_schema import _REGISTRY

    if not any(e.owner != "srmech" for e in _REGISTRY.values()):
        native = _native_carrier_schema()
        if native is not None:
            return native
    return _pure_carrier_schema()
