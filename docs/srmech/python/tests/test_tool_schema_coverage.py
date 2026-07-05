"""Coverage audit: every public callable in srmech.amsc.* and srmech.qm.*
has a registered tool-schema entry.

Task #220 — every operation surfaces via ``srmech.amsc.tool_schema`` so an
LLM consumer can discover the full callable surface without reading the
implementation. This test is the ratchet that keeps the tool-schema
extension in sync with the operations layer.

Exempt modules (intentionally not surfaced via tool-schema):

- ``srmech.amsc.tool_schema`` — the schema-API itself.
- ``srmech.amsc._native`` — ctypes shim (covered indirectly via
  ``srmech.amsc.format.sha256_bytes`` and ``read_ndjson``).
- ``srmech.amsc.gap_suggester`` — profile-loader internals; not a
  primitive operation.
- ``srmech.amsc.adapters`` — adapter package (per-source, surfaced via
  the bridge entries, not per-callable).
- ``srmech.amsc.attested`` — data subtree, not callables.
- ``srmech.profile_loader`` — profile-system internals.

Plus a small allowlist of catalog/descriptor helpers that the original
``_register_amsc_tools()`` already surfaces under their primary bridge
entries (``list_attested_sources``, ``get_attested_dataset``, etc.).
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Set

import pytest

import srmech.amsc
import srmech.qm
from srmech.amsc.tool_schema import get_tool_schema


# Modules / submodule prefixes intentionally not audited.
_EXEMPT_MODULE_PREFIXES = (
    "srmech.amsc.tool_schema",
    "srmech.amsc._native",
    "srmech.amsc.gap_suggester",
    "srmech.amsc.adapters",
    "srmech.amsc.attested",
)

# Specific functions that exist for backwards compatibility, profile-loader
# wiring, or as helpers that wrap a primary entry already registered.
_EXEMPT_FUNCTION_NAMES = frozenset({
    # catalog.* — additional helpers that compose `list_attested_sources`,
    # `get_attested_dataset`, `register_attested_root` (already registered).
    "srmech.amsc.catalog.list_registered_roots",
    "srmech.amsc.catalog.use_local_kernel",
    "srmech.amsc.catalog.clear_local_kernel",
    "srmech.amsc.catalog.get_local_kernel_state",
    "srmech.amsc.catalog.get_attested_descriptor",
    "srmech.amsc.catalog.attestation_audit",
    "srmech.amsc.catalog.iter_attested_dataset",
    # descriptor.* — TOML loader helpers around descriptor_hash (registered).
    "srmech.amsc.descriptor.load_descriptor",
    "srmech.amsc.descriptor.render_template",
    "srmech.amsc.descriptor.discover_descriptors",
    # format.* — validate / write helpers around sha256_bytes + read_ndjson
    # (already registered).
    "srmech.amsc.format.validate_mpr_record",
    "srmech.amsc.format.write_ndjson",
    # format.sha256_hex / sha256_raw (v0.7.5rc1; W4 / RBS-LM bugfix wishlist) —
    # the name-says-return alias and the raw-32-byte companion of
    # ``sha256_bytes`` (which IS registered). Same value, same native dispatch
    # (sha256_raw is bytes.fromhex(sha256_bytes(...))); exempt exactly like the
    # validate_mpr_record / write_ndjson helpers that wrap a registered entry.
    "srmech.amsc.format.sha256_hex",
    "srmech.amsc.format.sha256_raw",
    # ellbase.elliptic_lagrange_basis (v0.9.0rc66) — the degree-d elliptic Lagrange
    # interpolation basis, a CARRIER FOUNDATION peer of the EllMonomial / Theta /
    # EllRatio carriers (which are classes, not walked here). Like those carriers it
    # is exact-ℚ theta-product algebra, NOT a user-facing engine ToolEntry (the
    # engine ops — elliptic_gosper etc. — ARE registered); exempt exactly like the
    # other carrier-foundation surface. C peer owed (everything-mirrors); classified
    # `bignum_reference` in rosetta_classification.ndjson.
    "srmech.amsc.ellbase.elliptic_lagrange_basis",
    # eta_quotient.eta_quotient (v0.9.0rc82) — the public constructor of the
    # WEIGHT-axis EtaQuotient CARRIER (Q(τ) = ∏_d η(dτ)^{r_d}), a peer of the
    # UnaryTheta / RiemannTheta / EllRatio / ThetaSum carriers (which are classes,
    # NOT walked here). It CONSTRUCTS the carrier (q-series + weight + the exact
    # Ligozat modularity decision) — it is NOT a user-facing engine ToolEntry, so
    # the carrier adds NO tool (tools.total stays 340), exactly like the
    # elliptic_lagrange_basis carrier-foundation surface above. C peer
    # srmech_eta_quotient_qseries; classified `c_dispatched` in
    # rosetta_classification.ndjson.
    "srmech.amsc.eta_quotient.eta_quotient",
    # eisenstein.eisenstein (v0.9.0rc83) — the public constructor of the SECOND
    # WEIGHT-axis carrier Eisenstein (E_k(τ) = 1 − (2k/B_k)·Σ σ_{k−1}(n) qⁿ), a peer
    # of the EtaQuotient / UnaryTheta / RiemannTheta / ThetaSum carriers (which are
    # classes, NOT walked here). It CONSTRUCTS the carrier (exact-rational q-series +
    # even integer weight, computed from Bernoulli + divisor power sum) — it is NOT a
    # user-facing engine ToolEntry, so the carrier adds NO tool (tools.total stays
    # 340), exactly like the eta_quotient / elliptic_lagrange_basis carrier surfaces
    # above. C peer srmech_eisenstein_qseries; classified `c_dispatched` in
    # rosetta_classification.ndjson.
    "srmech.amsc.eisenstein.eisenstein",
    # modular_forms_ring.modular_forms_ring (v0.9.0rc84) — the public CONSTRUCTOR of
    # the stateless level-1 ℂ[E₄,E₆] ModularFormsRing CARRIER (the THIRD WEIGHT-axis
    # rung). It returns the carrier (whose weight_monomials/dim are pure accessors,
    # NOT walked here as they are class methods); it is NOT a user-facing engine
    # ToolEntry, exactly like the eta_quotient / eisenstein carrier constructors
    # above. classified `non_compute` in rosetta_classification.ndjson. NOTE: the
    # carrier's REDUCER, modular_forms_ring_represent, IS a registered ToolEntry (the
    # WEIGHT-axis analog of the Σ-row gosper/zeilberger/wz_certificate reducers) —
    # only the bare constructor is exempt.
    "srmech.amsc.modular_forms_ring.modular_forms_ring",
    # quasimodular_forms_ring.quasimodular_forms_ring (v0.9.0rc89) — the public
    # CONSTRUCTOR of the stateless level-1 ℂ[E₂,E₄,E₆] QuasiModularFormsRing CARRIER
    # (the FOURTH WEIGHT-axis rung). It returns the carrier (whose weight_monomials/
    # dim are pure accessors, NOT walked here as they are class methods); it is NOT a
    # user-facing engine ToolEntry, exactly like the modular_forms_ring constructor
    # above. classified `non_compute` in rosetta_classification.ndjson. NOTE: the
    # carrier's REDUCER, quasimodular_represent, IS a registered ToolEntry
    # (the WEIGHT-axis analog of the Σ-row reducers, one generator up from rc84) —
    # only the bare constructor + the E₂ series fn are exempt.
    "srmech.amsc.quasimodular_forms_ring.quasimodular_forms_ring",
    # quasimodular_forms_ring.eisenstein_e2 (v0.9.0rc89) — the WEIGHT-2 QUASIMODULAR
    # generator E₂ = 1 − 24·Σσ₁(n)qⁿ as an exact-ℚ q-series fn. A CARRIER-FOUNDATION
    # surface (the E₂ series the quasimodular ring is built on; the rc83 Eisenstein
    # carrier keeps its k≥4 contract and rejects k=2, so E₂ lives here) — NOT a
    # user-facing engine ToolEntry, exempt exactly like the carrier q-series surfaces.
    # C peer srmech_eisenstein_qseries (k=2 quasimodular branch); classified
    # `c_dispatched` in rosetta_classification.ndjson.
    "srmech.amsc.quasimodular_forms_ring.eisenstein_e2",
    # cascade.* — back-compat aliases of canonical names already registered
    # (the precursor's call-site names; see srmech.amsc.cascade).
    "srmech.amsc.cascade.class_k_pin_slot_at_zero",  # = pin_slot_at_zero
    "srmech.amsc.cascade.class_c_reorient",          # = reorient
    "srmech.amsc.cascade.best_rat_signed",           # = best_rational_signed
    # cascade.atoms.* / cascade.compose.* — the two-tier split (#751 / F208).
    # These submodules are the new canonical *homes* of the cascade ops, but
    # the tool-schema registers each op under its STABLE flat public name
    # ``srmech.amsc.cascade.<op>`` (introspection stability per #751) — which
    # IS registered. The submodule-dotted names are the same objects re-
    # exported flat, so they are exempt here exactly like the aliases above.
    "srmech.amsc.cascade.atoms.pin_slot_at_zero",
    "srmech.amsc.cascade.atoms.reorient",
    "srmech.amsc.cascade.atoms.magnitude",
    "srmech.amsc.cascade.atoms.chiral_flip",
    "srmech.amsc.cascade.atoms.chiral_dual",
    "srmech.amsc.cascade.atoms.net_chirality",
    "srmech.amsc.cascade.compose.cyclic_gcd",
    "srmech.amsc.cascade.compose.best_rational_signed",
    "srmech.amsc.cascade.compose.kuramoto_step",
    # cascade.compose.autocorrelation (v0.7.0rc8) — the Class-L circular
    # autocorrelation, registered under its flat public name
    # ``srmech.amsc.cascade.autocorrelation`` (which IS registered); the
    # submodule-dotted name is the same object re-exported flat, exempt
    # exactly like cyclic_gcd / kuramoto_step above.
    "srmech.amsc.cascade.compose.autocorrelation",
    # cascade.cayley_dickson.{cd_promote,cd_project} (rc116; #1248) — the
    # Hurwitz-ladder carrier conversions, registered under their flat public
    # names ``srmech.amsc.cascade.cd_promote`` / ``cd_project`` (which ARE
    # registered); the submodule-dotted names are the same objects re-exported
    # flat, exempt exactly like the atoms/compose entries above.
    "srmech.amsc.cascade.cayley_dickson.cd_promote",
    "srmech.amsc.cascade.cayley_dickson.cd_project",
    # cascade.compose.{signed_sum_squared,top_k_by_score} (v0.7.4rc2; PR #687
    # §1.2/§1.3). Registered under their flat ``srmech.amsc.cascade.*`` names
    # (which ARE registered); the submodule-dotted names are the same objects
    # re-exported flat, exempt exactly like cyclic_gcd / autocorrelation above.
    "srmech.amsc.cascade.compose.signed_sum_squared",
    "srmech.amsc.cascade.compose.top_k_by_score",
    # cascade.hypercomplex_dft.* — the quaternion/octonion DFT composites
    # (v0.7.0rc31 / #863). Registered under their STABLE flat public names
    # ``srmech.amsc.cascade.quaternion_dft`` / ``octonion_dft`` (which ARE
    # registered); the submodule-dotted names are the same objects re-exported
    # flat, exempt exactly like autocorrelation above.
    "srmech.amsc.cascade.hypercomplex_dft.quaternion_dft",
    "srmech.amsc.cascade.hypercomplex_dft.octonion_dft",
    # cascade.hypercomplex_dft.phase_coherent_peak (v0.9.0rc112 / #1234 Item 1d).
    # The lightweight matched-filter PEAK READ (the READ counterpart to the full
    # DFT transforms). Registered under its STABLE flat public name
    # ``srmech.amsc.cascade.phase_coherent_peak`` (which IS registered); the
    # submodule-dotted name is the same object re-exported flat, exempt exactly
    # like the quaternion_dft / octonion_dft peers above.
    "srmech.amsc.cascade.hypercomplex_dft.phase_coherent_peak",
    # cascade.hypercomplex_dft.hypercomplex_couple (v0.7.2rc1 / #908). Registered
    # under its STABLE flat public name ``srmech.amsc.cascade.hypercomplex_couple``
    # (which IS registered); the submodule-dotted name is the same object
    # re-exported flat, exempt exactly like the DFT peers above.
    "srmech.amsc.cascade.hypercomplex_dft.hypercomplex_couple",
    # cascade.hypercomplex_dft.hypercomplex_exp (v0.9.0rc10 / F882, srmech #205).
    # The literal exp(μθ) hypercomplex twiddle. Registered under its STABLE flat
    # public name ``srmech.amsc.cascade.hypercomplex_exp`` (which IS registered);
    # the submodule-dotted name is the same object re-exported flat.
    "srmech.amsc.cascade.hypercomplex_dft.hypercomplex_exp",
    # cascade.hamming.* — the Hamming/GF(2) block-code family (v0.7.2rc2 / #910
    # §30). Registered under their STABLE flat public names
    # ``srmech.amsc.cascade.hamming_{encode,syndrome,decode_correct}`` (which ARE
    # registered); the submodule-dotted names are the same objects re-exported
    # flat, exempt exactly like the hypercomplex_dft peers above.
    "srmech.amsc.cascade.hamming.hamming_encode",
    "srmech.amsc.cascade.hamming.hamming_syndrome",
    "srmech.amsc.cascade.hamming.hamming_decode_correct",
    # cascade.parallel.* — the Klein-4 four-sector dispatch (v0.6.0rc6 / F233).
    # Registered under its STABLE flat public name
    # ``srmech.amsc.cascade.parallel_sector_dispatch`` (which IS registered);
    # the submodule-dotted name is the same object re-exported flat, exempt
    # exactly like the atoms/compose submodule ops above.
    "srmech.amsc.cascade.parallel.parallel_sector_dispatch",
    # cascade.parallel.sectorize (v0.6.0rc12) — a thin convenience wrapper
    # that runs `parallel_sector_dispatch` with a recombine and returns the
    # `combined` value (a unary nesting callable). It exposes NO capability
    # beyond `parallel_sector_dispatch` (which IS registered) — it is sugar
    # for nesting, exempt exactly like the helpers that wrap a primary entry.
    "srmech.amsc.cascade.parallel.sectorize",
    # compose.greedy_bipartite_alignment (v0.7.0rc12 / §2.2) — takes a Python
    # `similarity_fn` callable that cannot cross the JSON-RPC boundary, so it
    # is NOT an MCP tool (no coercer for an arbitrary callable param). It is a
    # public, tested composition utility surfaced via srmech.amsc.compose, not
    # via MCP — exempt from tool-schema coverage on the callable-arg rationale.
    "srmech.amsc.compose.greedy_bipartite_alignment",
    # coupling.fold_identity (0.9.0rc125 / task #723) — the RECOVERABLE-FOLD
    # identity verdict (EQUAL / NOT_EQUAL / UNKNOWN). Both operands are
    # in-process RecoverableFold pair CARRIERS (a lossy bundle dict + the exact
    # seed Poly) that cannot be constructed from JSON, so it is NOT an MCP tool
    # (no meaningful JSON grammar for a RecoverableFold param) — exempt on the
    # SAME "cannot cross the JSON-RPC boundary" rationale as
    # greedy_bipartite_alignment / one.to_scalar above. It is a public, tested
    # verdict op reachable via Python (`non_compute` in the Rosetta ledger). The
    # PAIR CONSTRUCTOR (fold_encode_recoverable) IS a registered ToolEntry;
    # only the carrier-param verdict is exempt.
    "srmech.amsc.coupling.fold_identity",
    # cascade.one.* — "the One" S(σ,θ) generator (#887). Registered under its
    # STABLE FLAT public name ``srmech.amsc.cascade.the_one`` (which IS
    # registered); ``one.the_one`` is the same object re-exported flat, and
    # ``one.s_generator`` is the S(σ,θ) formula-name alias — exempt exactly
    # like the hypercomplex_dft / parallel re-exports above.
    "srmech.amsc.cascade.one.the_one",
    "srmech.amsc.cascade.one.s_generator",
    # cascade.one.to_scalar (v0.7.5rc76, #564) — the matrix/vector→scalar export
    # of the exact One: takes a structured ``One`` object (no MCP coercer for a
    # One param, so it cannot cross the JSON-RPC boundary) → NOT an MCP tool,
    # exempt on the callable/structured-arg rationale (like greedy_bipartite_
    # alignment above). It is a public, tested ``c_dispatched`` exact-rational
    # projection (its cos comes from the rc138 srmech_the_one adjoint peer),
    # reachable via Python AND dotted-path TOML-class binding
    # (op = "srmech.amsc.cascade.to_scalar"), not via the MCP tool list.
    "srmech.amsc.cascade.one.to_scalar",
    # cascade.one.one_* (v0.7.5rc138, #564 / [[feedback_prefer_config_driven_toml_classes]])
    # — the flat cascade-op accessor layer that the packaged ``one.toml``
    # ([class] One) binds its methods to (the genome two-layer pattern: ship each
    # accessor as a flat op, bind in the [class] TOML). Each takes a structured
    # ``One`` object → no MCP coercer for a One param, reachable ONLY via the
    # make_class class surface, NOT the MCP tool list — exempt exactly like
    # ``one.to_scalar`` above.
    "srmech.amsc.cascade.one.one_dim",
    "srmech.amsc.cascade.one.one_imag_dims",
    "srmech.amsc.cascade.one.one_partition",
    "srmech.amsc.cascade.one.one_plane_counts",
    "srmech.amsc.cascade.one.one_grammar_slots",
    "srmech.amsc.cascade.one.one_flat_rational",
    "srmech.amsc.cascade.one.one_matrix",
    # cascade.one.winding_tower (v0.9.0rc137, gh#1276) — the divmod-recursive
    # binary-tower chirality grading of a WHOLE winding ``w`` (the (ℤ/2)^d
    # Cayley–Dickson doubling coordinate; the anti-collapse of ``w mod 2``). A
    # structural exact-ℤ readout of the One's winding surface, reachable via
    # Python (and the One winding readouts), NOT via the MCP tool list — exempt
    # exactly like the ``one.to_scalar`` / ``one.one_*`` accessors above.
    # Dispatches to the same-rc BYTE-IDENTICAL C peer ``srmech_winding_tower``
    # (classified ``c_dispatched`` in the Rosetta ledger).
    "srmech.amsc.cascade.one.winding_tower",
    # cascade.sedenion_register.sed_* (v0.7.5rc140, #564 / PR #687 §31 /
    # [[feedback_prefer_config_driven_toml_classes]]) — the flat cascade-op
    # adapter layer that the packaged ``sedenion_register.toml`` ([class]
    # SedenionRegister) binds its methods to (the genome two-layer pattern: each
    # adapter rehydrates a transient register from the declarative D/codebook/slots
    # fields + delegates to the existing method, no logic duplication). Each takes
    # structured ``slots``/``codebook``/``D`` args → no MCP coercer, reachable ONLY
    # via the make_class class surface, NOT the MCP tool list — exempt exactly like
    # the ``one.one_*`` accessors above.
    "srmech.amsc.cascade.sedenion_register.sed_write",
    "srmech.amsc.cascade.sedenion_register.sed_materialize",
    "srmech.amsc.cascade.sedenion_register.sed_read_unbind",
    "srmech.amsc.cascade.sedenion_register.sed_clean",
    "srmech.amsc.cascade.sedenion_register.sed_slots",
    "srmech.amsc.cascade.sedenion_register.sed_couple_working",
    "srmech.amsc.cascade.sedenion_register.sed_uncouple_working",
    "srmech.amsc.cascade.sedenion_register.sed_carry",
    "srmech.amsc.cascade.sedenion_register.sed_correct",
    "srmech.amsc.cascade.sedenion_register.sed_navmap",
    "srmech.amsc.cascade.sedenion_register.sed_navigate",
    "srmech.amsc.cascade.sedenion_register.sed_is_navigable",
    # cascade.cayley_dickson.* — the open-exterior boundary-demonstrator
    # (v0.7.3rc1 / #915 / MFO §VII.6.23). The discoverable surface is registered
    # under STABLE flat names ``srmech.amsc.cascade.{cd_mult,cd_conjugate,
    # cd_norm_sq,cd_basis_product,sedenion_zero_divisor_witness,left_mult_kernel,
    # left_mult_is_invertible,is_division_algebra_dim}`` (which ARE registered);
    # the submodule-dotted names are the same objects re-exported flat, and the
    # building-block helpers (cd_add / cd_basis / left_mult_matrix) are sugar
    # around registered entries — exempt exactly like the one.* re-exports above.
    "srmech.amsc.cascade.cayley_dickson.cd_mult",
    "srmech.amsc.cascade.cayley_dickson.cd_conjugate",
    "srmech.amsc.cascade.cayley_dickson.cd_add",
    "srmech.amsc.cascade.cayley_dickson.cd_norm_sq",
    "srmech.amsc.cascade.cayley_dickson.cd_basis",
    "srmech.amsc.cascade.cayley_dickson.cd_basis_product",
    "srmech.amsc.cascade.cayley_dickson.is_division_algebra_dim",
    "srmech.amsc.cascade.cayley_dickson.sedenion_zero_divisor_witness",
    "srmech.amsc.cascade.cayley_dickson.left_mult_matrix",
    "srmech.amsc.cascade.cayley_dickson.left_mult_kernel",
    "srmech.amsc.cascade.cayley_dickson.left_mult_is_invertible",
    # cayley_dickson loop-navigation helpers (v0.7.5rc1; W15 / RBS-LM bugfix
    # wishlist) — closure / left_orbit / min_generating_set are the
    # combinatorial layer built entirely on the registered ``cd_basis_product``
    # cocycle (the loop analogues of the cyclic-group orbit machinery). Sugar
    # around a registered entry — exempt exactly like cd_add / cd_basis /
    # left_mult_matrix above.
    "srmech.amsc.cascade.cayley_dickson.closure",
    "srmech.amsc.cascade.cayley_dickson.left_orbit",
    "srmech.amsc.cascade.cayley_dickson.min_generating_set",
    # cascade.sedenion_register.* — the sedenion-addressable RBS-HDC instrument
    # (v0.7.4rc1 / #687 §31 / F465 / F468). The factory is registered under the
    # STABLE flat name ``srmech.amsc.cascade.sedenion_register`` (which IS
    # registered); the submodule-dotted name is the same object re-exported flat.
    # ``SedenionRegister`` is a class (not coverage-walked). Exempt exactly like
    # the cayley_dickson re-exports above.
    "srmech.amsc.cascade.sedenion_register.sedenion_register",
    # matrix_cascades.eigvec_exact / eigvec_exact_float (v0.9.0rc23 — rc-D exact
    # eigenvectors). These RETURN ``Qalg`` components (the exact ℚ(α) number-field
    # carrier), which is NOT MCP-serializable — exactly like the ``Qalg`` carrier
    # itself is not registered. They are package-level exact ops reachable via
    # Python (and consumed by the exact eigenproblem), not via the MCP tool list,
    # so they are exempt on the same "cannot cross the JSON-RPC boundary"
    # rationale as ``one.to_scalar`` / ``greedy_bipartite_alignment`` above. The
    # exact eigenVALUES (``eigvals_exact`` / ``char_poly``) ARE registered (they
    # return list/float); only the eigenVECTOR ops (Qalg return) are exempt.
    "srmech.amsc.cascade.matrix_cascades.eigvec_exact",
    "srmech.amsc.cascade.matrix_cascades.eigvec_exact_float",
    # matrix_cascades.factor_integer_poly / eig_exact (v0.9.0rc25 — rc-F). Exempt on
    # the SAME "package-level exact algebra, returns non-JSON-RPC types" rationale as
    # the eigvec ops above. ``eig_exact`` returns dicts carrying ``complex`` /
    # ``Qalg`` eigenpairs (and ``project=False`` returns ``Qalg`` objects outright);
    # ``factor_integer_poly`` returns list[tuple[tuple[int], int]] (an exact
    # arbitrary-precision factorisation oracle, ``bignum_reference`` in the Rosetta
    # ledger). Both are reachable via Python, not the MCP tool list, exactly like the
    # ``Qalg`` carrier itself is not registered.
    "srmech.amsc.cascade.matrix_cascades.factor_integer_poly",
    "srmech.amsc.cascade.matrix_cascades.eig_exact",
    # matrix_cascades.jordan_chains_exact / jordan_form_exact (v0.9.0rc27 — rc-G,
    # exact generalized eigenvectors / Jordan canonical form). Exempt on the SAME
    # "package-level exact algebra, returns non-JSON-RPC types" rationale as the
    # eigvec / eig_exact ops above. ``jordan_chains_exact`` returns ``Qalg`` chains;
    # ``jordan_form_exact`` returns dicts carrying ``Qalg`` / ``complex`` P, J and
    # block eigenvalues (``project=False`` is all ``Qalg``). Both reachable via
    # Python, not the MCP tool list, exactly like the ``Qalg`` carrier itself.
    "srmech.amsc.cascade.matrix_cascades.jordan_chains_exact",
    "srmech.amsc.cascade.matrix_cascades.jordan_form_exact",
})


def _walk_public_callables(pkg) -> Set[str]:
    """Return dotted-path names of every public top-level callable in
    `pkg` and its submodules."""
    out: Set[str] = set()
    prefix = pkg.__name__ + "."
    for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, prefix):
        if any(name.startswith(p) for p in _EXEMPT_MODULE_PREFIXES):
            continue
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        for fn_name, fn in inspect.getmembers(mod, inspect.isfunction):
            if fn_name.startswith("_"):
                continue
            # Skip re-exports: only count if the function is defined here.
            if getattr(fn, "__module__", None) != mod.__name__:
                continue
            dotted = f"{mod.__name__}.{fn_name}"
            out.add(dotted)
    return out


def test_amsc_public_callables_have_tool_entries():
    """Every public function in srmech.amsc.* (minus exemptions) is
    registered in the tool schema."""
    schema = get_tool_schema()
    registered = {t.name for t in schema.tools}
    callables = _walk_public_callables(srmech.amsc)
    missing = sorted(callables - registered - _EXEMPT_FUNCTION_NAMES)
    assert not missing, f"Missing tool-schema entries for srmech.amsc:\n  " + "\n  ".join(missing)


def test_qm_public_callables_have_tool_entries():
    """Every public function in srmech.qm.* is registered in the tool schema."""
    schema = get_tool_schema()
    registered = {t.name for t in schema.tools}
    callables = _walk_public_callables(srmech.qm)
    missing = sorted(callables - registered)
    assert not missing, f"Missing tool-schema entries for srmech.qm:\n  " + "\n  ".join(missing)


def test_tool_schema_entries_have_required_fields():
    """Every entry has non-empty name / owner / summary, and a parameters
    tuple that is well-typed."""
    schema = get_tool_schema()
    for t in schema.tools:
        assert t.name and "." in t.name, f"empty/invalid name: {t.name!r}"
        assert t.owner, f"empty owner in {t.name}"
        assert t.summary, f"empty summary in {t.name}"
        assert isinstance(t.parameters, tuple), (
            f"parameters not tuple in {t.name}: {type(t.parameters)}"
        )
        for p in t.parameters:
            assert p.name, f"empty param name in {t.name}"
            assert p.type, f"empty param type in {t.name}.{p.name}"


def test_tool_schema_owner_is_srmech_for_builtins():
    """All builtin entries have owner='srmech' (profile entries would
    have a different owner; we only register srmech-owned here)."""
    schema = get_tool_schema()
    for t in schema.tools:
        assert t.owner == "srmech", (
            f"Unexpected owner {t.owner!r} on builtin entry {t.name}"
        )


def test_tool_schema_view_is_jsonable():
    """The view dict is JSON-serialisable round-trip clean."""
    import json
    from srmech.amsc.tool_schema import tool_schema_view

    view = tool_schema_view()
    s = json.dumps(view, sort_keys=True)
    assert len(s) > 1000  # non-trivial registry
    round_trip = json.loads(s)
    assert round_trip == view


def test_tool_schema_total_count_meets_floor():
    """Coverage floor: at least ~80 entries (14-class primitives + qm ops
    + bridge entries). Ratchet test — count is allowed to grow but not
    silently drop."""
    schema = get_tool_schema()
    assert len(schema.tools) >= 80, (
        f"Tool-schema count fell below floor: {len(schema.tools)} < 80"
    )


def test_no_duplicate_tool_names():
    """Each tool entry has a unique dotted name."""
    schema = get_tool_schema()
    names = [t.name for t in schema.tools]
    duplicates = {n for n in names if names.count(n) > 1}
    assert not duplicates, f"Duplicate tool entries: {sorted(duplicates)}"


def test_tool_schema_categories_match_module_structure():
    """Sanity-check that categories track the module they belong to."""
    schema = get_tool_schema()
    for t in schema.tools:
        # name is e.g. 'srmech.amsc.cyclic.gcd' or 'srmech.qm.spin.pauli_matrices'
        parts = t.name.split(".")
        # category is a free-form taxonomy hint; just ensure it's a
        # plausible match for one of the path components or a known
        # bridge category.
        plausible = (
            t.category in parts
            or t.category.startswith("qm.")  # qm.* operations layer
            or t.category in ("format", "descriptor", "catalog")
        )
        assert plausible, (
            f"category {t.category!r} doesn't match module path "
            f"{t.name!r}"
        )
