"""rc7 Rosetta-completeness — consolidate the 5-classifier verdicts into one
committed classification NDJSON, reconciled against the authoritative inventory.

The classification text below is grouped by bucket; each line is an op's
`exposed_as`. The reconcile matches every inventory op to exactly one verdict
(exact exposed_as, else unique last-2/last-3 dotted-segment match) and reports
any inventory op left unclassified, any verdict matching no inventory op, and
any double-match. Run until 348/348 clean, then it writes the committed file.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

NOTES = Path(__file__).resolve().parent
INV = NOTES / "_rosetta_inventory.ndjson"
OUT = NOTES / "_rosetta_classification.ndjson"

# ---- the verdicts (bucket -> exposed_as lines) -------------------------
CLASSIFICATION = """
### c_dispatched
srmech.qm.bell.operator_norm
srmech.amsc.cyclic.gcd
srmech.amsc.cyclic.lcm
srmech.amsc.cyclic.mod_add
srmech.amsc.cyclic.mod_inv
srmech.amsc.cyclic.mod_mul
srmech.amsc.cyclic.mod_pow
srmech.amsc.cyclic.three_cycle
srmech.amsc.descriptor_hash
srmech.amsc.dispatch.match
srmech.amsc.dispatch.mirror_pattern
srmech.amsc.read_ndjson
srmech.amsc.format.sha256_batch
srmech.amsc.sha256_bytes
srmech.amsc.sha256_hex
srmech.amsc.sha256_raw
srmech.amsc.hdc.bind
srmech.amsc.hdc.bundle
srmech.amsc.hdc.cross7
srmech.amsc.hdc.g2_three_form
srmech.amsc.hdc.loop_associator
srmech.amsc.hdc.loop_bind
srmech.amsc.hdc.loop_bind_hd
srmech.amsc.hdc.loop_conj
srmech.amsc.hdc.loop_conj_hd
srmech.amsc.hdc.loop_inv
srmech.amsc.hdc.loop_inv_hd
srmech.amsc.hdc.loop_left_op
srmech.amsc.hdc.loop_right_op
srmech.amsc.hdc.loop_runbind_hd
srmech.amsc.hdc.loop_unbind_hd
srmech.amsc.hdc.permute
srmech.amsc.hdc.polar_bind
srmech.amsc.hdc.polar_bundle
srmech.amsc.hdc.polar_density
srmech.amsc.hdc.similarity
srmech.amsc.kepler.equation_of_centre
srmech.amsc.kepler.kepler_solve
srmech.amsc.kepler.pin_slot
srmech.amsc.laplacian.dense_adjacency
srmech.amsc.laplacian.dense_laplacian
srmech.amsc.laplacian.dense_matmul_complex
srmech.amsc.laplacian.dense_matvec_complex
srmech.amsc.laplacian.dense_solve
srmech.amsc.laplacian.elementwise_multiply_complex
srmech.amsc.laplacian.elementwise_transcendental
srmech.amsc.laplacian.hermitian_eigendecompose
srmech.amsc.laplacian.jacobi_eigvals
srmech.amsc.laplacian.normalized_laplacian
srmech.amsc.naming.lookup
srmech.amsc.naming.reverse_order
srmech.amsc.primes.cyclic_period
srmech.amsc.primes.factor
srmech.amsc.primes.is_prime
srmech.amsc.rational.atan
srmech.amsc.rational.atan2
srmech.amsc.rational.best_rational
srmech.amsc.rational.continued_fraction
srmech.amsc.rational.continued_fraction_convergents
srmech.amsc.rational.cos
srmech.amsc.rational.exp
srmech.amsc.rational.log
srmech.amsc.rational.rational_add
srmech.amsc.rational.rational_div
srmech.amsc.rational.rational_mul
srmech.amsc.rational.rational_pow_uint
srmech.amsc.rational.sin
srmech.amsc.rational.sqrt
srmech.amsc.search.byte_search
srmech.amsc.search.byte_search_backward
srmech.amsc.template.render
srmech.amsc.tlv.tlv_pack
srmech.amsc.cascade.chiral_dual
srmech.amsc.cascade.chiral_flip
srmech.amsc.cascade.magnitude
srmech.amsc.cascade.net_chirality
srmech.amsc.cascade.pin_slot_at_zero
srmech.amsc.cascade.reorient
srmech.amsc.cascade.autocorrelation
srmech.amsc.cascade.best_rational_signed
srmech.amsc.cascade.cyclic_gcd
srmech.amsc.cascade.kuramoto_step
srmech.amsc.cascade.cd_basis_product
srmech.amsc.cascade.hamming_encode
srmech.amsc.cascade.hamming_syndrome

### c_exists_unbound
srmech.amsc.hdc.klein4_bind
srmech.amsc.hdc.klein4_bundle
srmech.amsc.hdc.klein4_similarity
srmech.amsc.hdc.klein4_triality_cycle
srmech.amsc.hdc.klein4_unbind

### composition_of_c
srmech.signal_processing.closed_form_ops.lmmse.op
srmech.qm.gauge.gauge_connection_matrix
srmech.qm.gauge.su2_generators
srmech.qm.gauge.su2_structure_constants
srmech.qm.gauge.su3_gell_mann_matrices
srmech.qm.gauge.su3_generators
srmech.qm.gauge.su3_structure_constants
srmech.qm.potentials.harmonic_oscillator_ladder
srmech.qm.potentials.hydrogen_radial
srmech.qm.propagators.feynman_fermion_propagator
srmech.qm.propagators.feynman_massive_vector_propagator
srmech.qm.propagators.feynman_photon_propagator
srmech.qm.propagators.feynman_scalar_propagator
srmech.qm.pseudo_hermitian.expectation_eta
srmech.qm.pseudo_hermitian.inner_product_eta
srmech.qm.relativistic.dirac_operator_momentum_space
srmech.qm.relativistic.four_momentum_squared
srmech.qm.relativistic.gamma_matrices
srmech.qm.relativistic.klein_gordon_dispersion
srmech.qm.relativistic.minkowski_metric
srmech.qm.single_particle.density_matrix
srmech.qm.single_particle.lattice_momentum
srmech.qm.single_particle.tdse_evolve
srmech.qm.single_particle.tise_solve
srmech.qm.sm.ckm_matrix
srmech.qm.sm.electroweak_summary
srmech.qm.sm.fermion_mass_from_yukawa
srmech.qm.sm.higgs_potential
srmech.qm.sm.higgs_vev
srmech.qm.sm.w_boson_mass
srmech.qm.sm.weak_mixing_angle
srmech.qm.sm.weinberg_relation_residual
srmech.qm.sm.z_boson_mass
srmech.qm.spin.pauli_identity
srmech.qm.spin.pauli_matrices
srmech.qm.spin.pauli_spin_operator
srmech.qm.octonion.octonion_norm
srmech.qm.octonion.octonion_conjugate
srmech.qm.octonion.octonion_left_mult
srmech.qm.octonion.octonion_right_mult
srmech.qm.octonion.octonion_mult_table
srmech.qm.hurwitz.hurwitz_matrix
srmech.qm.hurwitz.hurwitz_planes
srmech.qm.triality.triality_apply
srmech.qm.triality.triality_cycle
srmech.qm.triality.triality_relation_residual
srmech.signal_processing.closed_form_ops.hdc_truncation.op
srmech.signal_processing.closed_form_ops.heat_kernel.op
srmech.signal_processing.closed_form_ops.music.op
srmech.signal_processing.cascade_compose_rotations
srmech.signal_processing.form_function_rotate
srmech.signal_processing.inverse_form_function_rotate
srmech.signal_processing.verify_rotation_class_n_cycle_order
srmech.signal_processing.path_b_ops.hdc_truncation.op
srmech.signal_processing.decode_loe_fingerprint
srmech.signal_processing.compute_content_stride
srmech.signal_processing.encode_loe_content
srmech.signal_processing.mint_cascade_composition
srmech.signal_processing.mint_class_operator
srmech.signal_processing.mint_stance_fingerprint
srmech.signal_processing.mint_vector
srmech.amsc.rational.cexp
srmech.amsc.rational.complex_exp
srmech.amsc.rational.hypot
srmech.amsc.rational.tan
srmech.amsc.laplacian.dirichlet_to_neumann
srmech.amsc.laplacian.schur_complement
srmech.amsc.cascade.signed_sum_squared
srmech.amsc.cascade.coupled_wave
srmech.amsc.cascade.multiplex_streams
srmech.amsc.cascade.parallel_sector_dispatch
srmech.amsc.cascade.sectorize
srmech.amsc.cascade.hamming_decode_correct

### python_only_irreducible
srmech.qm.gauge.casimir_eigenvalue
srmech.qm.gauge.casimir_operator
srmech.qm.gauge.gauge_path_segment
srmech.qm.gauge.lie_algebra_residual
srmech.qm.gauge.wilson_loop_from_segments
srmech.qm.potentials.harmonic_oscillator_hamiltonian
srmech.qm.pseudo_hermitian.construct_eta_from_eigendecomposition
srmech.qm.pseudo_hermitian.is_pseudo_hermitian
srmech.qm.pseudo_hermitian.pseudo_hermitian_eigenvalues_real
srmech.qm.relativistic.charge_conjugation_matrix
srmech.qm.relativistic.clifford_residuals
srmech.qm.relativistic.gamma_5
srmech.qm.relativistic.weyl_left_projector
srmech.qm.relativistic.weyl_right_projector
srmech.qm.single_particle.commutator
srmech.qm.single_particle.heisenberg_evolve
srmech.qm.single_particle.liouville_evolve
srmech.qm.sm.ckm_unitarity_residual
srmech.qm.spin.pauli_clifford_residuals
srmech.qm.bell.chsh_operator
srmech.qm.bell.chsh_operator_norm
srmech.qm.bell.chsh_pauli_combination
srmech.qm.bell.chsh_pauli_combination_norm
srmech.qm.bell.verify_chsh
srmech.qm.so8.an_embedding
srmech.qm.so8.g2_subalgebra
srmech.qm.so8.quaternion_subalgebra_stabilizer
srmech.qm.so8.so7_subalgebra
srmech.qm.so8.so8_adjoint_basis
srmech.qm.triality.lean_isa_seventh_primitive
srmech.qm.triality.triality_automorphism
srmech.qm.triality.triality_companions
srmech.qm.triality.triality_swap
srmech.signal_processing.closed_form_ops.allpass.op
srmech.signal_processing.closed_form_ops.arithmetic_coding.op
srmech.signal_processing.closed_form_ops.beamforming_fixed.op
srmech.signal_processing.closed_form_ops.cross_spectral.op
srmech.signal_processing.closed_form_ops.dct.op
srmech.signal_processing.closed_form_ops.esprit.op
srmech.signal_processing.closed_form_ops.farrow.op
srmech.signal_processing.closed_form_ops.fft.op
srmech.signal_processing.closed_form_ops.fir.op
srmech.signal_processing.closed_form_ops.fsk.op
srmech.signal_processing.closed_form_ops.huffman.op
srmech.signal_processing.closed_form_ops.ica_jade.op
srmech.signal_processing.closed_form_ops.ifft.op
srmech.signal_processing.closed_form_ops.iir.op
srmech.signal_processing.closed_form_ops.jpeg.op
srmech.signal_processing.closed_form_ops.lz77.op
srmech.signal_processing.closed_form_ops.map_ml.op
srmech.signal_processing.closed_form_ops.matched_filter.op
srmech.signal_processing.closed_form_ops.mimo_svd.op
srmech.signal_processing.closed_form_ops.mlse.op
srmech.signal_processing.closed_form_ops.multirate.op
srmech.signal_processing.closed_form_ops.multitaper.op
srmech.signal_processing.closed_form_ops.ofdm.op
srmech.signal_processing.closed_form_ops.polyphase.decompose
srmech.signal_processing.closed_form_ops.polyphase.op
srmech.signal_processing.closed_form_ops.psk_qam.op
srmech.signal_processing.closed_form_ops.rfft.op
srmech.signal_processing.closed_form_ops.rle.op
srmech.signal_processing.closed_form_ops.sign_quantise.op
srmech.signal_processing.closed_form_ops.sinc_interp.op
srmech.signal_processing.closed_form_ops.spectral_subtraction.op
srmech.signal_processing.closed_form_ops.spectrogram.op
srmech.signal_processing.closed_form_ops.spectrogram.stft_op
srmech.signal_processing.closed_form_ops.vector_quantisation.op
srmech.signal_processing.closed_form_ops.mlse.viterbi_op
srmech.signal_processing.closed_form_ops.wavelet.op
srmech.signal_processing.closed_form_ops.wiener.op
srmech.signal_processing.path_b_ops.fft.op
srmech.signal_processing.path_b_ops.ifft.op
srmech.signal_processing.path_b_ops.matched_filter.op
srmech.signal_processing.path_b_ops.rfft.op
srmech.signal_processing.path_b_ops.sign_quantise.op
srmech.signal_processing.path_b_ops.wiener.op
srmech.amsc.hdc.bundle_with_ties
srmech.amsc.hdc.klein4_chirality_flip_gamma5
srmech.amsc.hdc.klein4_chirality_flip_omega7
srmech.amsc.hdc.klein4_cpt_mirror
srmech.amsc.hdc.klein4_holographic_decode
srmech.amsc.hdc.klein4_holographic_encode
srmech.amsc.hdc.klein4_random
srmech.amsc.hdc.klein4_sector_count
srmech.amsc.hdc.klein4_triality_correct
srmech.amsc.hdc.klein4_triality_encode
srmech.amsc.hdc.polar_from_real
srmech.amsc.hdc.polar_random
srmech.amsc.hdc.polar_similarity
srmech.amsc.hdc.polar_unbind
srmech.amsc.laplacian.symmetric_eigendecompose
srmech.amsc.laplacian.three_fold_eigvec_groups
srmech.amsc.coupling.signed_sum_squared
srmech.amsc.harmonics.classify_chirality_harmonic
srmech.amsc.compose.greedy_bipartite_alignment
srmech.amsc.cascade.hypercomplex_couple
srmech.amsc.cascade.octonion_dft
srmech.amsc.cascade.quaternion_dft
srmech.amsc.cascade.matrix_cascades.eigvals
srmech.amsc.cascade.matrix_cascades.einsum
srmech.amsc.cascade.matrix_cascades.lstsq
srmech.amsc.cascade.matrix_cascades.qr
srmech.amsc.cascade.matrix_cascades.svd
srmech.amsc.cascade.spectral_cascades.dft
srmech.amsc.cascade.spectral_cascades.fft
srmech.amsc.cascade.spectral_cascades.idft
srmech.amsc.cascade.spectral_cascades.ifft
srmech.amsc.cascade.spectral_cascades.kron

### bignum_reference
srmech.qm.bell.tsirelson_bound
srmech.amsc.rational.atan_series_truncate
srmech.amsc.rational.cos_series_truncate
srmech.amsc.rational.exp_series_truncate
srmech.amsc.rational.log1p_series_truncate
srmech.amsc.rational.pi_cascade_digits
srmech.amsc.rational.sin_series_truncate
srmech.signal_processing.closed_form_ops.pi_cascade.op
srmech.signal_processing.path_b_ops.pi_cascade.op
srmech.amsc.cascade.cd_add
srmech.amsc.cascade.cd_basis
srmech.amsc.cascade.cd_conjugate
srmech.amsc.cascade.cd_mult
srmech.amsc.cascade.cd_norm_sq
srmech.amsc.cascade.cayley_dickson.closure
srmech.amsc.cascade.left_mult_is_invertible
srmech.amsc.cascade.left_mult_kernel
srmech.amsc.cascade.left_mult_matrix
srmech.amsc.cascade.cayley_dickson.left_orbit
srmech.amsc.cascade.cayley_dickson.min_generating_set
srmech.amsc.cascade.sedenion_zero_divisor_witness
srmech.amsc.cascade.the_one

### non_compute
srmech.qm.bell.classical_chsh_bound
srmech.qm.octonion.octonion_table_attestation
srmech.signal_processing.begin_cascade
srmech.signal_processing.current_cascade
srmech.signal_processing.dispatch
srmech.signal_processing.end_cascade
srmech.signal_processing.is_dispatch_table_locked
srmech.signal_processing.lock_dispatch_table
srmech.signal_processing.resolve_path
srmech.signal_processing.unlock_dispatch_table
srmech.signal_processing.clear_registry
srmech.signal_processing.has_path
srmech.signal_processing.lookup
srmech.signal_processing.register
srmech.signal_processing.registered_ops
srmech.signal_processing.cell_grid
srmech.signal_processing.clear_records
srmech.signal_processing.iter_records
srmech.signal_processing.profile_op
srmech.signal_processing.record_profile
srmech.signal_processing.update_dispatch_table
srmech.amsc.attestation_audit
srmech.amsc.clear_local_kernel
srmech.amsc.get_attested_dataset
srmech.amsc.get_attested_descriptor
srmech.amsc.get_local_kernel_state
srmech.amsc.iter_attested_dataset
srmech.amsc.list_attested_sources
srmech.amsc.catalog.list_catalog_chains
srmech.amsc.list_registered_roots
srmech.amsc.register_attested_root
srmech.amsc.catalog.run_catalog_chain
srmech.amsc.use_local_kernel
srmech.amsc.compose.parse_catalog_chains
srmech.amsc.compose.parse_chain_spec
srmech.amsc.compose.resolve_chain
srmech.amsc.compose.run_chain
srmech.amsc.discover_descriptors
srmech.amsc.load_descriptor
srmech.amsc.render_template
srmech.amsc.validate_mpr_record
srmech.amsc.write_ndjson
srmech.amsc.gap_suggester.register_classifier
srmech.amsc.gap_suggester.register_probes
srmech.amsc.gap_suggester.suggest_gap_collections
srmech.amsc.harmonics.classify_harmonic
srmech.amsc.tool_schema.get_tool_schema
srmech.amsc.tool_schema.load_extension_file
srmech.amsc.tool_schema.register_profile_tools
srmech.amsc.tool_schema.register_tool
srmech.amsc.tool_schema.tool_schema_view
srmech.amsc.tool_schema.unregister_profile_tools
srmech.amsc.tool_schema.warmup_all
srmech.amsc.cascade.is_division_algebra_dim
srmech.amsc.cascade.top_k_by_score
srmech.amsc.cascade.sedenion_register
"""


def parse_classification():
    bucket = None
    out = {}  # exposed_as -> bucket
    dups = []
    for raw in CLASSIFICATION.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("###"):
            bucket = line[3:].strip()
            continue
        if line in out:
            dups.append(line)
        out[line] = bucket
    return out, dups


def seg_key(exposed_as, n):
    return ".".join(exposed_as.split(".")[-n:])


def main():
    inv = [json.loads(l) for l in INV.read_text(encoding="utf-8").splitlines()
           if l.strip()]
    inv_exposed = [r["exposed_as"] for r in inv]
    inv_set = set(inv_exposed)
    cls, dups = parse_classification()

    # build leaf indexes of the inventory for fuzzy match
    inv_by_leaf2, inv_by_leaf3 = {}, {}
    for e in inv_exposed:
        inv_by_leaf2.setdefault(seg_key(e, 2), []).append(e)
        inv_by_leaf3.setdefault(seg_key(e, 3), []).append(e)

    matched = {}   # inventory exposed_as -> bucket
    unmatched_cls = []
    for c_exposed, bucket in cls.items():
        if c_exposed in inv_set:
            matched[c_exposed] = bucket
            continue
        cands = inv_by_leaf3.get(seg_key(c_exposed, 3), [])
        if len(cands) != 1:
            cands = inv_by_leaf2.get(seg_key(c_exposed, 2), [])
        if len(cands) == 1:
            matched[cands[0]] = bucket
        else:
            unmatched_cls.append((c_exposed, len(cands)))

    unclassified = [e for e in inv_exposed if e not in matched]

    print(f"inventory ops:        {len(inv_exposed)}")
    print(f"classification lines: {len(cls)} (dups: {dups})")
    print(f"matched:              {len(matched)}")
    print(f"UNCLASSIFIED inv ops ({len(unclassified)}):")
    for e in sorted(unclassified):
        print(f"   - {e}")
    print(f"UNMATCHED cls lines ({len(unmatched_cls)}):")
    for e, n in sorted(unmatched_cls):
        print(f"   - {e}   (inv candidates: {n})")

    if not unclassified and not unmatched_cls and not dups:
        # write committed classification joined to defined_at
        inv_by_exposed = {r["exposed_as"]: r for r in inv}
        rows = []
        for e in inv_exposed:
            r = inv_by_exposed[e]
            rows.append({"exposed_as": e, "defined_at": r["defined_at"],
                         "bucket": matched[e]})
        rows.sort(key=lambda r: (r["bucket"], r["exposed_as"]))
        with OUT.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        from collections import Counter
        c = Counter(r["bucket"] for r in rows)
        print("\nCLEAN -> wrote", OUT.name)
        for b in sorted(c):
            print(f"   {c[b]:4d}  {b}")
        return 0
    print("\nNOT CLEAN — fix the lists above and rerun.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
