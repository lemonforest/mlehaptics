"""srmech.introspect.carrier_schema — the CARRIER (operand) introspection surface
(rc205; gh #1293) — the noun-side DUAL of :mod:`srmech.introspect.tool_schema`.

``tool_schema`` exposes the **ops** (the verbs — the A–N operator vocabulary)
richly; this module exposes the **carrier TYPES** (the nouns — the operand
vocabulary) the ops consume and produce. Before rc205 a consumer discovering
the carriers had to scrape :func:`srmech.math.carrier_ladder.
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
          "max_dim":     <int> | None,     # rc343 — largest algebra dim this
                                           # carrier admits; None = UNBOUNDED
          "bounded_by":  "<mechanism>" | None,   # rc343 — WHY it stops there
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
:data:`~srmech.cascade.cayley_dickson.CD_COMPOSE_MAX_DIM` and
:data:`~srmech.cascade.cayley_dickson.CD_TURN_MAX_DIM`.

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

``max_dim`` / ``bounded_by`` — the ceiling is PER-CARRIER (rc343, `#T972`)
--------------------------------------------------------------------------
rc339 published ONE ``turn`` ceiling — dim 4 — in
``describe()["limits"]["capabilities"]``, with no carrier attached. **That number
is a Cayley–Dickson fact stated as a universal one, and two rows in this very
table contradict it.**

* ``Mat``'s product is ``mat_matmul``, which is associative at EVERY dim. Its
  turns compose, with the which-way intact, as far as you care to build:
  MEASURED over the matrix units of ``M_n(ℝ)`` — 81/81 turn-composing pairs at
  ``n=3`` (algebra dim 9), of which 42 are NON-commuting, and 256/256 at
  ``n=4`` (dim 16), of which 108 are non-commuting. Both are above 4.
* ``Poly`` (with ``BiPoly`` / ``TriPoly`` / ``QPoly`` / ``QBiPoly``) is an
  integral domain at unbounded degree — ``deg(p·q) == deg p + deg q``, so
  ``compose`` is ``"full"`` arbitrarily far above the ``compose`` ceiling of 8.

So each row now carries its OWN ceiling:

``max_dim``
    The largest algebra dim (REAL dimension, so ℍ is 4 and ``M_n(ℝ)`` is ``n²``)
    at which this row's verdicts hold. ``None`` means **unbounded in dim** — the
    verdicts hold at every dim the carrier can be built at.

``bounded_by``
    WHY it stops there, drawn from :data:`CEILING_MECHANISMS`. Not free text: a
    mechanism is admissible only if it can be MEASURED SEPARATELY from the
    capability's own definition and independently predicts the ceiling. That
    admission rule is the whole point — see below.

**Why ``bounded_by`` is not "associativity".** rc339 gave the ``turn`` ceiling
``bounded_by: "associativity"``. But ``turn`` is DEFINED as ``x·(y·z) ==
(x·y)·z for every z`` — so "bounded by associativity" restates the definition.
Anything associative turns; anything that turns is associative. The field could
not discriminate between two carriers and no measurement could falsify it, which
is the same false-green shape rc339 itself was written to remove.

The replacement has content. The Cayley–Dickson product FACTORS into two halves,
and MEASURED over the shipped ``cd_basis_product`` they behave completely
differently::

    dim | index == a XOR b | negative signs (C(d,2)) | SIGN COCYCLE associative
      2 |       4/4        |        1  (1)           |     8/8       100%
      4 |      16/16       |        6  (6)           |    64/64      100%
      8 |      64/64       |       28  (28)          |   344/512      67%
     16 |     256/256      |      120  (120)         |  2248/4096     55%
     32 |    1024/1024     |      496  (496)         | 16808/32768    51%

The INDEX lane is ``e_i·e_j → e_{i XOR j}``, exact at every rung with no
exceptions. The SIGN is a cocycle over it, and the sign is what stops being
associative — abruptly, at dim 8. Every doubling adds one index bit and extends
the sign cocycle; ℝ is value-with-no-index, ℂ is value plus the first index bit.

So: **addressing is unbounded because XOR is associative at every dim forever;
turns and composition break because THE SIGN COCYCLE stops being associative.**
The wall was never in the addressing — which is also why rc298 (`#T933`) could
lift ``CD_MAX_DIM`` 64 → 256 by DECOUPLING the caps, and why ``Mat`` (whose sign
handling is trivial) turns at any dim. "Bounded by the sign cocycle, not by the
index" is falsifiable and predicts new carriers; "bounded by associativity" is
neither.

*Honest label:* ``index == XOR`` is close to DEFINITIONAL for a Cayley–Dickson
basis — the basis product IS ``±e_{i^j}`` by construction — so that column is a
CHECK, not a discovery. What is NOT definitional is the READING: that the ladder
splits into a FREE index and a LOAD-BEARING sign, and that every ceiling srmech
publishes lives on one side of that split. The ``C(d,2)`` regularity and the
100% → 67% → 55% cocycle drop are the support. It is not stronger than that.

The ``ops`` back-index is **DERIVED, never hand-maintained**: it unions

* a word-boundary token scan of every registered ToolEntry's declared
  ``parameters[].type`` / ``returns.type`` strings (the tool_schema SSoT), and
* the rc120 per-op CARRIER CONTRACT (:data:`srmech.math.carrier_ladder.
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
public op surfaces (``QMat`` at ``srmech/amsc/qmat.py:148`` / the
genus-``RiemannTheta`` family at ``srmech/apokatastasis/riemann_theta.py``) join when
an op surfaces them (the drift ratchet in
``tests/test_carrier_schema_rc205.py`` forces the addition).

⚠️ ``Qalg`` WAS THE THIRD NAME IN THAT LIST until v0.9.0rc362, and it is now
REGISTERED — the sentence became false the moment the ``srmech.music`` spectra
ops began consuming it, so it is corrected here rather than left to age.
Recording HOW it stayed hidden matters more than the addition, because the
mechanism outlived the example. ``Qalg`` shipped in rc22 and was correctly
unregistered for as long as no public op took one. rc362 changed that, and the
ratchet named above still passed — it scans ``p.type`` / ``returns.type`` for
capitalised tokens, and the three spectra ops originally declared ``partials``
as a bare ``"Sequence"``, which is ALLOWLISTED. Measured at the time: the
string ``"Qalg"`` occurred in **0 of 525** declared type strings tree-wide,
while ``srmech_tool_registry.c`` already carried "each Q, Qalg, int or an
(int, int) pair" in its human descriptions. The prose knew; the machine-
readable field did not, so the gate passed by SELECTING NOTHING — a pass that
was not a measurement. Note that C parity was green on the identical hole
(``Qalg`` absent from ``srmech_carrier_registry.c`` in both the as-text and
decoded-byte channels, counts agreeing), which is the dual construction
certifying MUTUAL REALIZABILITY and not correctness: both projections were
consistently wrong together. The repair is therefore in two halves — register
the carrier, AND make the declared types name it (the ops now declare
``Sequence[int | Q | Qalg]``) so the ratchet can actually fire. A fix that
left the gate unable to select the token would have been half a fix.

⚠️ rc363 — THE ADMISSION RULE NOW HAS A SECOND INSTRUMENT, AND IT FOUND TWO MORE.
The paragraph above ends by saying the repair needs the declared types to name
the carrier "so the ratchet can actually fire". True, and not enough: that makes
the ratchet fire only for authors who *remember* to widen the type. rc363 adds
``tests/test_carrier_use_derivation_rc363.py``, which derives the same question
from the op's OWN SOURCE (``tests/coercion_boundary.py``: an ``isinstance``
guard on a value tracked from the op's parameters) instead of from the declared
string. Run against the tree, it registered two carriers the declared channel
could not see:

* ``Theta`` — accepted DIRECTLY by five ops (``elliptic_gosper`` /
  ``elliptic_recurrence_8w7`` / ``elliptic_zeilberger`` /
  ``elliptic_wz_certificate`` / ``carrier_spectrum``), each of which declared
  ``EllRatio`` alone while its own ``description`` prose read "an EllMonomial /
  Theta is lifted". The union was documented for humans in the same tuple that
  withheld it from machines.
* ``CarrierSpectrum`` — built on ``carrier_spectrum``'s return path and handed
  back under ``'spectrum'``; its own docstring already called it "a first-class
  carrier object (not a diagnostic dict)".

ADR-0012 §3.1 C3 recorded ONE such precedent (``CarrierSpectrum``) against a
"24 of 25" baseline. There were two, because that baseline was itself measured
on the declared channel — a measurement inherits the blindness of its
instrument. Both are registered here (25 -> 26 at rc362, 26 -> 28 at rc363), and
the five ops now declare ``EllRatio | EllMonomial | Theta``, so the rc205
declared-channel ratchet and the rc363 use-channel gate agree.

Native dispatch: when the rc205 C peer is loaded (``srmech_carrier_schema``
over the compiled-in ``srmech_carrier_registry`` const table — GENERATED by
``c/tools/gen_carrier_registry.py``, the rc184/rc202 codegen model) and no
profile tools are registered, :func:`carrier_schema` parses the C canonical
JSON — BYTE-IDENTICAL to ``json.dumps(<pure>, sort_keys=True,
separators=(",", ":"))`` (the sha256 hash-ratchet contract locking the C table
to this Python SSoT). A profile tool, a stale/absent lib, or a non-OK status
falls back to the pure path (never a wrong answer).

Pure data + a derivation over the live registry — no numerical kernel; no
float math, no ``abs()``.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ..math.carrier_ladder import _OP_CONTRACTS
# rc343 (`#T972`) — CDRegister's per-carrier ceiling IS the addressing cap, read
# from the one SSoT rather than re-typed here (cayley_dickson imports nothing
# from this module, so there is no cycle).
from ..cascade.cayley_dickson import CD_MAX_DIM as _CD_MAX_DIM
from srmech import _json as _srmech_json

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
            "float(q): THE exact-rational carrier across srmech (#T845 — it "
            "subsumed the former stdlib-Fraction interchange carrier). It is "
            "the return carrier of the exact-LA boundaries (dense_solve "
            "exact=True, schur_complement, cd_norm_sq), the Class-N series-"
            "truncate trig/exp/log surface, and the HDC similarity scores. A "
            "stdlib fractions.Fraction is still ACCEPTED on input (numeric "
            "protocol), it is simply never the emitted carrier."),
        "ladder": None, "rung": None, "variables": [],
    },
    "Qalg": {
        "description": (
            "srmech's exact ALGEBRAIC-IRRATIONAL scalar — an element "
            "Σ coords[i]·αⁱ of the number field ℚ[x]/(m), where α is a root of "
            "a monic minimal polynomial m in ℤ[x]. The exact peer of Q one rung "
            "out: α²==2 holds IN THE FIELD, so an irrational is CARRIED rather "
            "than approximated, and Qi is simply Qalg over x²+1. Its "
            "is_rational() is a DECIDABLE ℚ-membership oracle and a genuine "
            "invariant — ℚ is the unique degree-1 subfield of ℚ(α), so the "
            "answer survives any change of ℚ-basis and is not a presentation "
            "count. It REFUSES a non-integer minimal polynomial (measured: "
            "Qalg.alpha([Q(-1, 2), 0, 1]) raises 'm coefficients must be plain "
            "ints (monic ℤ[x])'), which is the barrier that makes a "
            "transcendental impossible to smuggle in as though it were exact — "
            "and therefore why the acoustic tier layer DECLARES Tier 3 instead "
            "of inferring it. Surfaced on the public op surface at v0.9.0rc362 "
            "by the srmech.music spectra ops, which decide Tier 1 vs Tier 2 "
            "entirely by whether a partial arrives as Q or as Qalg."),
        "ladder": None, "rung": None, "variables": ["α"],
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
    "QMat": {
        "description": (
            "Numpy-free EXACT-ℚ dense matrix: a tuple-of-tuples of reduced Q "
            "entries + (n_rows, n_cols), immutable — the bigint-exact peer of "
            "the float64 Mat (Q is to float as QMat is to Mat). THE exact "
            "linear-algebra operand: its .nullspace / .rank / .rref / .solve / "
            ".det run the exact Gauss–Jordan over ℚ (bigint, no float, no "
            "tolerance), and it is what the srmech.chemistry reaction ops ride "
            "— balance_reaction reduces a QMat kernel column to integer "
            "stoichiometric coefficients, conservation_laws reads its "
            "left-nullspace, deficiency reads QMat.rank. Collapses to a float64 "
            "Mat only via .to_mat (the terminal ALU→FPU read-out)."),
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
            "spectral basis-change (eigen / Walsh-Hadamard). rc437 "
            "(local task T1142): that sentence had named an op that did not "
            "exist — a reader of describe()[\"carriers\"][\"HV\"] was told the "
            "Walsh-Hadamard half of the bridge was reachable while zero "
            "public callables implemented it. It is now "
            "srmech.cascade.walsh_hadamard.walsh_hadamard_transform (exact "
            "integers on the boolean cube (Z/2)^n, its own inverse up to the "
            "2^n scale); the eigen half is the Class-L eigendecompose family. "
            "Neither half is auto-applied to an HV — this names the bridge, "
            "it does not wire it."),
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
    "Theta": {
        "description": (
            "The exact modified-theta SYMBOL θ(z; p) over an EllMonomial "
            "argument z (the nome p is the global modulus), immutable — the "
            "ATOM of the elliptic row: EllRatio is a quotient of these, and "
            "canonicalize() applies the quasi-periodicity + inversion rewrites "
            "that reduce z to a p-exponent-0 orientation-fixed representative. "
            "Accepted directly by elliptic_gosper / elliptic_recurrence_8w7 / "
            "elliptic_zeilberger / elliptic_wz_certificate / carrier_spectrum, "
            "which lift it to EllRatio."),
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
    "CarrierSpectrum": {
        "description": (
            "The harmonic OCCUPANCY of an elliptic carrier element under the "
            "shift-Laplacian L = σ−1, in two orthogonal channels (the cyclic "
            "Class-I σ-eigenspectrum + the quasi-periodic Class-L p-character "
            "blocks), immutable — the operand-side dual of the One: a "
            "first-class carrier object (not a diagnostic dict) that carries "
            "the block-decomposed key-equation solve. Produced by "
            "carrier_spectrum from an EllRatio."),
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

# ── the CEILING MECHANISM vocabulary (rc343, `#T972`) ─────────────────────────
#
# The admissible values of `bounded_by`, here and in
# describe()["limits"]["capabilities"]. A CLOSED set, not free text, and the
# admission rule is strict:
#
#   a mechanism is admissible only if it can be MEASURED SEPARATELY from the
#   capability's own definition, and that measurement independently predicts
#   the ceiling.
#
# That rule is what rc339's `bounded_by: "associativity"` failed. `turn` is
# DEFINED as associativity, so no measurement of "associativity" is separable
# from the definition of the thing it claims to bound: the field restated the
# definition and nothing could contradict it. Every value below names a
# mechanism `tests/test_carrier_ceiling_rc343.py` measures on its own terms and
# checks against the ceiling it is claimed to produce.
#
#: ``{mechanism: what it asserts}`` — the closed `bounded_by` vocabulary.
CEILING_MECHANISMS: Dict[str, str] = {
    "index_xor": (
        "the index lane e_i*e_j -> e_(i XOR j) is associative at every dim, so "
        "nothing mathematical bounds this capability; measured exact 4/4, "
        "16/16, 64/64, 256/256, 1024/1024 at dims 2..32"),
    "sign_cocycle": (
        "the SIGN half of the Cayley-Dickson product stops being associative: "
        "measured 100% at dims 2 and 4, 67% (344/512) at dim 8, 55% "
        "(2248/4096) at dim 16 — which is what puts the ceiling at 4"),
    "hurwitz": (
        "Hurwitz (1898): the normed composition algebras over R are exactly "
        "dims 1, 2, 4, 8; past dim 8 srmech ships the explicit counterexample "
        "(cascade.cd_zero_divisor_witness)"),
    "tooling": (
        "a build constant — verification cost, not a mathematical wall; "
        "liftable, and rc298 (`#T933`) did lift it 64 -> 256"),
    "definition": (
        "the carrier IS this dim; the number is the carrier's identity, not a "
        "wall it runs into (a quaternion is dim 4 the way a byte is 8 bits)"),
}


def _cap(product, compose, turn, commutative, varies_with=None,
         max_dim=None, bounded_by=None):
    """One capability row. ``address`` is ``"exact"`` iff the carrier has any
    structure at all — every srmech carrier is exactly addressed, and the field
    exists so a future one that is not must say so.

    ``max_dim`` (rc343) is the largest algebra dim — REAL dimension — at which
    the verdicts hold, ``None`` for **unbounded in dim**; ``bounded_by`` names
    the mechanism from :data:`CEILING_MECHANISMS`. The default is the honest one
    for a carrier with no dimensional wall: unbounded, no mechanism."""
    assert max_dim is None or max_dim >= 1, "max_dim: a dim or None"
    assert bounded_by is None or bounded_by in CEILING_MECHANISMS, (
        f"bounded_by {bounded_by!r} is not in CEILING_MECHANISMS — a ceiling "
        "reason must be a mechanism that can be measured apart from the "
        "capability it bounds")
    return {
        "product": product,
        "address": _CAP_EXACT,
        "compose": compose,
        "turn": turn,
        "commutative": commutative,
        "varies_with": varies_with,
        "max_dim": max_dim,
        "bounded_by": bounded_by,
    }


#: No closed binary product on srmech's surface → the compose / turn question
#: does not apply. Distinct from ``"unclassified"`` (it applies; we have not
#: established the answer).
_CAP_NO_PRODUCT = _cap(None, None, None, None)

_CAPABILITY: Dict[str, Dict[str, Any]] = {
    # ── the polynomial ladders: commutative integral domains over ℚ ──────────
    # UNBOUNDED in dim, and this is one of the two rows that falsify a GLOBAL
    # `compose` ceiling of 8: deg(p·q) == deg p + deg q, so a product of nonzero
    # polynomials is nonzero at ANY degree. `compose: full` here is not a
    # Cayley–Dickson claim and the Hurwitz bound has no jurisdiction over it.
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
    # Each CD rung IS its dim, so `bounded_by` is "definition", not a wall.
    "float": _cap("field multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True,
                  max_dim=1, bounded_by="definition"),
    "complex": _cap("field multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True,
                    max_dim=2, bounded_by="definition"),
    # ℍ — the LAST rung whose non-commuting turns fold: measured 16/16 basis
    # pairs compose while only 10/16 commute, so 6 non-commuting pairs survive.
    "quaternion": _cap("cd_mult (H)", _CAP_FULL, _CAP_NON_COMMUTING, False,
                       max_dim=4, bounded_by="definition"),
    # 𝕆 — still a division algebra (compose survives, and this rung exists to
    # reach e₄..e₇), but turn-composing == commuting AS SETS (88 == 88, both
    # differences empty). Non-commuting turn composition is gone.
    "octonion": _cap("cd_mult (O)", _CAP_FULL, _CAP_ABELIAN_ONLY, False,
                     max_dim=8, bounded_by="definition"),
    # 𝕊 — past Hurwitz. srmech ships the witness: cascade.cd_zero_divisor_witness.
    "sedenion": _cap("cd_mult (S)", _CAP_ZERO_DIVISORS, _CAP_ABELIAN_ONLY,
                     False, max_dim=16, bounded_by="definition"),
    # ── the exact scalars ────────────────────────────────────────────────────
    "int": _cap("integer multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True,
                max_dim=1, bounded_by="definition"),
    "Q": _cap("rational multiply", _CAP_FULL, _CAP_ABELIAN_ONLY, True,
              max_dim=1, bounded_by="definition"),
    # Qalg is ℚ[x]/(m), which is a FIELD only when m is irreducible — and
    # Qalg.alpha does not check irreducibility (the caller does; see
    # music.equal_temperament_partials, which applies Lang VI §9 Thm 9.1 before
    # constructing). Per the same worst-case rule the HV row follows, this
    # publishes the WEAKEST case and points `varies_with` at the knob.
    #
    # MEASURED, not assumed — the reducible witness, via the shipped carrier:
    #   m = x²−1 = (x−1)(x+1) is ACCEPTED by Qalg.alpha; then (α−1) has coords
    #   (−1, 1) and (α+1) has coords (1, 1), both nonzero, and their product has
    #   coords (0, 0). A genuine zero-divisor pair, so `compose` is not full.
    # With an irreducible m there are none (x²−2: α·α == 2, α.inverse() exists),
    # which is exactly what `varies_with: minimal_polynomial` records.
    #
    # UNBOUNDED in dim: the field degree is the length of m, and a degree-31
    # field builds fine — so no max_dim and no ceiling mechanism. The dim here
    # is a ℚ-vector-space dimension, not a Cayley–Dickson rung; Hurwitz has no
    # jurisdiction over it, the same reasoning as the polynomial-ladder rows.
    "Qalg": _cap("field multiply (mod m)", _CAP_ZERO_DIVISORS,
                 _CAP_ABELIAN_ONLY, True, varies_with="minimal_polynomial"),
    # ── the float-LA carriers ────────────────────────────────────────────────
    # Mat's ALGEBRA product is `@` (mat_matmul): associative and NON-commutative,
    # so turns fold with their which-way intact — and it has zero divisors
    # (any singular pair), so it composes turns without being a composition
    # algebra. That combination is exactly why the two verdicts are separate
    # fields: `turn` is not downstream of `compose`.
    #
    # rc343: this is THE row that falsifies a GLOBAL `turn` ceiling of 4.
    # mat_matmul is associative at EVERY dim, so Mat's turns keep folding with
    # their which-way intact as far as you build. MEASURED over the matrix units
    # of M_n(ℝ): n=2 (algebra dim 4) 16/16 compose, 10 non-commuting; n=3
    # (dim 9) 81/81 compose, 42 non-commuting; n=4 (dim 16) 256/256 compose, 108
    # non-commuting. Both n=3 and n=4 sit ABOVE CD_TURN_MAX_DIM. Hence max_dim
    # None with no mechanism: there is no wall here to name.
    # (`varies_with` stays None on purpose — it names a knob that can IMPROVE a
    # worst-case verdict, and Mat's verdicts do not improve with dim: they keep
    # holding.)
    "Mat": _cap("mat_matmul (@)", _CAP_ZERO_DIVISORS, _CAP_NON_COMMUTING, False),
    # QMat is the exact-ℚ peer of Mat: SAME algebra product (@ = matmul,
    # associative + non-commutative), SAME zero divisors (any singular pair,
    # exact over ℚ), and the SAME absence of a dimensional wall — matmul is
    # associative at every dim, so its turns keep folding as far as you build.
    "QMat": _cap("QMat matmul (@)", _CAP_ZERO_DIVISORS, _CAP_NON_COMMUTING, False),
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
    # Theta has NO closed binary product: θ(z)·θ(w) is a theta PRODUCT, which
    # leaves the carrier (it is an EllRatio with two numerator factors). There is
    # no `Theta.__mul__` to describe, so the compose / turn question does not
    # apply — distinct from "unclassified", which would mean it applies and
    # srmech has not established the answer.
    "Theta": _CAP_NO_PRODUCT,
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
    # A CarrierSpectrum is a READ of an element, not an element: there is no
    # spectrum·spectrum on srmech's surface (the closed op the two channels
    # support is solve_key_equation, which is not a binary product of spectra).
    "CarrierSpectrum": _CAP_NO_PRODUCT,
    "HarmonicMaass": _CAP_NO_PRODUCT,
    "One": _CAP_NO_PRODUCT,
    # ── the addressable registers ────────────────────────────────────────────
    # The register's product is its CD-respecting navigate — routing a slot
    # through ×e_j. At dim 16 the ambient algebra is 𝕊, which is why the
    # register's REVERSIBLE working set is the octonion block e₀..e₇ and the
    # remainder is carry/EC: the design already encodes this ceiling, and rc339
    # makes introspection say so.
    "SedenionRegister": _cap("cd_navigate (S, dim 16)", _CAP_ZERO_DIVISORS,
                             _CAP_ABELIAN_ONLY, False,
                             max_dim=16, bounded_by="definition"),
    # Worst case over every dim in [1, CD_MAX_DIM] — NOT the dim-4 best case.
    # This row is the direct answer to the rc339 defect: a caller who read
    # cd_max_dim 256 and reached for a turn gets told here that at the dims this
    # register admits, turns are abelian-only and the product has zero divisors.
    "CDRegister": _cap("cd_navigate (CD dim n <= CD_MAX_DIM)",
                       _CAP_ZERO_DIVISORS, _CAP_ABELIAN_ONLY, False,
                       varies_with="dim", max_dim=_CD_MAX_DIM,
                       bounded_by="tooling"),
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
        from .. import _native
    except Exception:  # pragma: no cover — defensive; _native always imports
        return None
    raw = _native.carrier_schema_json_c()
    if raw is None:
        return None
    return _srmech_json.loads(raw.decode("utf-8"))


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


# -- the DOMAIN-MATCHING vocabulary (rc354, F1336) ----------------------------
#
# A NULL, SHIPPED AS A NULL. A four-word vocabulary was proposed for picking a
# carrier by what a domain needs -- MAGNITUDE / PHASE / ORIENTATION / PATH, read
# as the Cayley-Dickson ladder R -> C -> H -> O. The question put to the shipped
# surface was: can a planner DERIVE that word from the published capability row?
#
# MEASURED ANSWER: NO. The row determines the word for 3 of 26 carriers.
# (3 of 25 until v0.9.0rc362 registered ``Qalg``. The NUMERATOR did not move --
# the new carrier is one more the vocabulary cannot label, which widens the gap
# rather than narrowing it. Every count in this block is a LIVE property of
# ``_CAPABILITY``; re-measure them when a carrier lands, and see
# ``tests/test_unit_label_and_domain_word_rc354.py`` for why a carrier is never
# excluded to hold a number still.)
#
# The decisive measurement is one line long. ``float`` (which the vocabulary
# calls MAGNITUDE) and ``complex`` (PHASE) differ in EXACTLY ONE published
# field, and it is not a capability:
#
#     float    {address: exact, compose: full, turn: abelian_only,
#               commutative: True, varies_with: None, bounded_by: definition,
#               product: "field multiply", max_dim: 1}
#     complex  {... every verdict identical ...,                  max_dim: 2}
#
# ``max_dim`` is a real DIMENSION, not "is it orderable". It only correlates
# with the word because R and C happen to sit at dims 1 and 2, and it is None
# for 19 of the 28 carriers, so it cannot generalise. ``address`` is "exact" for
# all 28 (a zero-entropy column), and ``turn`` is constant "abelian_only" across
# all 15 commutative carriers -- no discriminating power in exactly the half
#
# ⚠️ THE "None for N" FIGURE WAS ALREADY WRONG BEFORE rc362, and that is the
# more useful finding than the +1. This line read "None for 13 of the 25"; the
# measured pre-``Qalg`` value was SIXTEEN, not thirteen. So the drift was 3, it
# predates this rc, and nothing caught it -- because no test reads these prose
# counts. The two figures beside it (25 exact, 14 commutative) WERE right, so
# the block was partially stale, which is the hardest kind to notice. If you
# change ``_CAPABILITY``, re-derive all three here; they are one-liners over
# the dict and are not asserted anywhere.
#
# v0.9.0rc363 re-derived all three per the instruction above, after registering
# ``Theta`` and ``CarrierSpectrum`` (26 -> 28): max_dim None 17 -> 19, address
# "exact" 28/28, commutative rows still 15 (both new carriers have no closed
# product, so ``commutative`` is None for each and neither joins that count).
# The chain from the original defect is now complete and each link is measured:
# 16 (pre-rc362, the true value the shipped "13" missed) -> 17 (Qalg) -> 19.
# where MAGNITUDE and PHASE must be told apart.
#
# rc363: this paragraph carried the literal counts "13 of the 25" / "all 25" /
# "all 14 commutative". Re-measured on the rc363 tree (28 carriers): max_dim is
# None for 19, address is "exact" for 28/28, turn is "abelian_only" for 15/15
# commutative rows.
#
# THE max_dim FIGURE WAS ALREADY WRONG BEFORE EITHER rc TOUCHED IT, and the
# arithmetic says so independently: the measured pre-Qalg value was 16, so the
# shipped "13" was stale by 3 while the registry was still at 25. The chain is
# then exact -- 16 (pre-rc362) +1 (Qalg) = 17 at rc362, +2 (Theta,
# CarrierSpectrum, both no-product rows with no ceiling) = 19 at rc363. That
# 13-vs-16 is the hardest kind of stale to spot, because THE TWO FIGURES BESIDE
# IT WERE CORRECT: a paragraph that is right twice reads as right three times.
# Nothing catches it, because no test reads prose counts -- the ADR-0012 §1.1
# pattern (a number goes stale because nobody owns the thing it counts) inside a
# shipped module comment.
#
# So the counts are replaced by the QUANTIFIERS they were standing in for. The
# ARGUMENT never depended on the digits: what matters is "most", "every" and
# "every", and those three claims are recomputed live by `_domain_word_gap()`
# and pinned by tests/test_unit_label_and_domain_word_rc354.py -- which is the
# difference between a number a test owns and a number only prose asserts.
#
# THE MISSING FIELD IS AN ORDER PREDICATE, and it is missing for a structural
# reason: of the ladder's loss steps, the capability block measures three and
# never measures the first one.
#
#     R -> C loses TOTAL ORDER      -- no published field        <- THE GAP
#     C -> H loses COMMUTATIVITY    -- ``commutative``
#     H -> O loses ASSOCIATIVITY    -- ``turn``
#     O -> S loses DIVISION         -- ``compose``, but the four-word vocabulary
#                                      has NO WORD for this loss at all
#
# TWO FURTHER REASONS the four words cannot label this surface injectively, both
# readable off the shipped rows:
#
#   * THE VERDICT SPACE IS A LATTICE, NOT A CHAIN. ``Mat`` is
#     (zero_divisors, non_commuting); ``octonion`` is (full, abelian_only).
#     NEITHER DOMINATES THE OTHER, so ``Mat`` sits at no rung of R->C->H->O.
#     This file already says so at the ``Mat`` row above: "`turn` is not
#     downstream of `compose`". A 4-word chain asserts a chain over two
#     independent axes.
#   * ``Vec`` FITS ZERO BUCKETS, derivably: commutative (so not ORIENTATION or
#     PATH), zero divisors (so not orderable, hence not MAGNITUDE), and not a
#     cycle (not PHASE). R^n under Hadamard is a genuine fifth thing.
#     rc362: ``Qalg`` JOINS IT, by the identical derivation -- commutative, and
#     zero divisors in the worst case (a reducible minimal polynomial makes
#     Q[x]/(m) a non-domain). Two carriers now fit zero buckets, so the fifth
#     thing is not a singleton curiosity.
#
# WHAT WOULD CLOSE IT -- a field in the same closed-vocabulary shape as
# ``compose`` and ``turn``:
#
#     "order": "total" | "none" | "unclassified" | None
#
# It satisfies the rc343 admission rule (measurable SEPARATELY from the
# capability it decides): a field is formally real iff -1 is not a sum of
# squares, and C/H/O all give -1 = i^2 in ONE square while R/Q/Z do not. For the
# zero-divisor carriers the witness is an exhibited pair, the pattern
# ``cascade.cd_zero_divisor_witness`` already ships. So ``order: "none"``
# would be falsifiable rather than asserted.
#
# NOT SHIPPED, DELIBERATELY: the four words are NOT attached to any carrier row.
# Asserting a word next to data that does not determine it is the rc339 defect
# one level up -- a planner would read ``HV -> PATH`` and reach for a q8 bind.
# Three things must land TOGETHER or the gap reopens: (a) the ``order`` field;
# (b) a fifth word for the published-but-unnamed O -> S loss; (c) a worst-case
# label on every ``varies_with`` row.

#: the domain-word verdicts a capability row can carry. ``undecidable`` is a
#: first-class verdict here, not a failure to try.
DOMAIN_WORD_VERDICTS = ("ORIENTATION", "PATH", "none_of_the_four",
                        "not_applicable", "undecidable")


def _domain_word(capability: Dict[str, Any]) -> str:
    """The domain word a single published capability row DETERMINES -- or
    ``"undecidable"`` when the row does not determine one.

    This is the honest half of the four-word MAGNITUDE / PHASE / ORIENTATION /
    PATH proposal: the two words the row CAN decide are returned, and the two it
    cannot are refused rather than guessed. See the block comment above for the
    measurement, and :func:`_domain_word_gap` for the derived ledger.
    """
    commutative = capability.get("commutative")
    if commutative is None:                      # no closed product at all
        return "not_applicable"
    if commutative is False:
        # the swap axis IS published, so ORIENTATION vs PATH is decidable.
        return ("ORIENTATION" if capability.get("turn") == _CAP_NON_COMMUTING
                else "PATH")
    if capability.get("compose") == _CAP_ZERO_DIVISORS:
        # an ordered ring is an integral domain, so zero divisors PROVE
        # not-orderable; and a commutative zero-divisor product is not a cycle.
        # Neither MAGNITUDE nor PHASE nor ORIENTATION nor PATH. (``Vec``.)
        return "none_of_the_four"
    # commutative, no zero divisors: MAGNITUDE and PHASE are indistinguishable
    # on the published fields. The converse of the rule above fails -- C has no
    # zero divisors and is not orderable -- so ``compose`` cannot separate them.
    return "undecidable"


def _domain_word_gap(capabilities: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The DERIVED statement of what the four-word domain vocabulary can and
    cannot be read off the shipped carrier registry.

    Recomputed live, never authored, so it cannot drift from the rows it
    describes. ``capabilities`` lets a caller that has already built the
    ``{name: capability}`` mapping (``describe()``) hand it over instead of
    paying for a second :func:`carrier_schema` build; omit it and the registry
    is read here.
    """
    caps = capabilities if capabilities is not None else {
        name: spec["capability"] for name, spec in carrier_schema().items()}
    by_verdict: Dict[str, List[str]] = {v: [] for v in DOMAIN_WORD_VERDICTS}
    for name, cap in caps.items():
        by_verdict[_domain_word(cap)].append(name)
    worst_case_only = sorted(n for n, c in caps.items() if c.get("varies_with"))
    # A word that comes back is not automatically USABLE. Two disqualifiers,
    # both read off the row, and both counted separately so the headline number
    # is the honest one:
    #   * `varies_with` set  -> the word is the WORST CASE over a knob, so a
    #     planner reading it for a different knob value gets the wrong word
    #     (CDRegister spans all four across dim 1..8; HV spans q8 and octonion);
    #   * PATH with zero divisors -> the row is PAST Hurwitz, and the four words
    #     have no name for the O->S loss, so PATH collides with the octonion's.
    qualified, unambiguous = [], []
    for name in by_verdict["ORIENTATION"] + by_verdict["PATH"]:
        cap = caps[name]
        if cap.get("varies_with"):
            qualified.append(name)
        elif (_domain_word(cap) == "PATH"
              and cap.get("compose") == _CAP_ZERO_DIVISORS):
            qualified.append(name)
        else:
            unambiguous.append(name)
    return {
        "verdict": "NOT DERIVABLE from the published capability row",
        "determined_unambiguous": len(unambiguous),
        "of": len(caps),
        "unambiguous": sorted(unambiguous),
        "word_returned_but_qualified": sorted(qualified),
        "by_verdict": {k: sorted(v) for k, v in by_verdict.items()},
        "missing_field": {
            "name": "order",
            "asks": "does a total order compatible with `product` exist "
                    "(x<y => x+z<y+z; 0<x,0<y => 0<xy)",
            "vocabulary": ["total", "none", "unclassified", None],
            "witness": "a field is formally real iff -1 is not a sum of "
                       "squares -- C/H/O give -1 = i^2 in ONE square, R/Q/Z do "
                       "not; for zero-divisor carriers, an exhibited pair",
            "why_it_is_admissible": "measurable separately from the capability "
                                    "it decides (the rc343 admission rule)",
        },
        "why": (
            "of the ladder's four loss steps the block measures three and never "
            "the first: R->C loses TOTAL ORDER (unpublished), C->H loses "
            "commutativity (`commutative`), H->O loses associativity (`turn`), "
            "O->S loses division (`compose`, and the four words have no name "
            "for it). `float` and `complex` differ in exactly one published "
            "field, `max_dim` -- a dimension, not an order predicate."),
        "not_a_chain": (
            "the verdict space is a LATTICE: Mat is (zero_divisors, "
            "non_commuting) and octonion is (full, abelian_only), and NEITHER "
            "DOMINATES -- so Mat sits at no rung of R->C->H->O and no 4-word "
            "chain labels this surface injectively"),
        "word_is_worst_case_only_for": worst_case_only,
        "not_shipped": (
            "MAGNITUDE and PHASE are NOT attached to any carrier row. Asserting "
            "a word beside data that does not determine it is the rc339 defect "
            "one level up. Closing this needs three things TOGETHER: the "
            "`order` field, a FIFTH word for the O->S loss, and a worst-case "
            "label on every `varies_with` row."),
    }
