import sys, importlib
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE, "numpy", "present" if importlib.util.find_spec("numpy") else "ABSENT")
paths = """srmech.__version__
srmech.amsc
srmech.amsc._native
srmech.amsc.antikythera
srmech.amsc.antikythera.lunar_dial
srmech.amsc.cascade
srmech.amsc.catalog
srmech.amsc.catalog.register_attested_root
srmech.amsc.cmb_residual.smica_nilc_compare
srmech.amsc.cyclic
srmech.amsc.dispatch
srmech.amsc.dna
srmech.amsc.factorise
srmech.amsc.format
srmech.amsc.format.sha256_bytes
srmech.amsc.gap_suggester
srmech.amsc.hdc
srmech.amsc.introspect
srmech.amsc.kepler
srmech.amsc.laplacian
srmech.amsc.laplacian.dense_laplacian
srmech.amsc.laplacian.hermitian_eigendecompose
srmech.amsc.laplacian.jacobi_eigvals
srmech.amsc.hdc.bind
srmech.amsc.hdc.bundle
srmech.amsc.hdc.permute
srmech.amsc.hdc.similarity
srmech.amsc.rational.continued_fraction
srmech.amsc.rational.best_rational
srmech.amsc.mtheory.bipartite_modes
srmech.amsc.mycorrhizal.band_membership
srmech.amsc.ndjson
srmech.amsc.octopus
srmech.amsc.physarum
srmech.amsc.protein.ramachandran
srmech.amsc.rational
srmech.amsc.search
srmech.amsc.template
srmech.amsc.tlv
srmech.amsc.tool_schema
srmech.amsc.tool_schema.get_tool_schema
srmech.amsc.tool_schema.tool_schema_view
srmech.amsc.verify_attestation
srmech.amsc.verify_attestation.bytes
srmech.asymptotic_dof.toy_modulation_time
srmech.calculus.cycle_derivative
srmech.cascade
srmech.cascade.cauchy_kernel
srmech.cascade.fft_decomposition
srmech.cascade.recursive_hopf_signs
srmech.cascade.ring_equilibrium_attractor
srmech.cascade.shifted_circle_eigenvalues
srmech.catalogue.class_frequency
srmech.cognition.proof_check_cascade
srmech.cosmology.dark_ratio_trajectory
srmech.cosmology.hubble_tension
srmech.dark_sector.coupling_intensity
srmech.geometry.hopf.complex_project
srmech.geometry.hopf.octonionic_project
srmech.gr.isco.efficiency
srmech.kepler.solve
srmech.list_profiles
srmech.profile
srmech.precession.omega_sub
srmech.qm
srmech.qm.bell
srmech.qm.bell.chsh_operator_norm
srmech.qm.propagators
srmech.qm.qft.decompose
srmech.qm.relativistic
srmech.qm.relativistic.schwarzschild_isco_efficiency
srmech.qm.single_particle
srmech.qm.spin
srmech.shadows
srmech.signal_processing
srmech.spectral
srmech.math.cyclic
srmech.math.dispatch
srmech.math.primes
srmech.math.hdc
srmech.math.kepler
srmech.math.kepler.kepler_solve
srmech.math.kepler.pin_slot
srmech.math.laplacian
srmech.math.rational
srmech.math.search
srmech.math.template
srmech.math.tlv
srmech.introspect.tool_schema.get_tool_schema
srmech.introspect.tool_schema.tool_schema_view
srmech._native
srmech._native.HAS_NATIVE
srmech.physics.qm
srmech.physics.qm.bell
srmech.physics.qm.bell.chsh_operator_norm
srmech.physics.qm.relativistic
srmech.physics.qm.relativistic.schwarzschild_isco_efficiency
srmech.physics.qm.single_particle
srmech.physics.qm.spin
srmech.physics.qm.propagators
srmech.amsc.format.verify_attestation
srmech.amsc.catalog.verify_attestation
srmech.amsc.descriptor
srmech.cascade.compose
srmech.spectral.decompose
srmech.signal_processing.closed_form_ops.pi_cascade
srmech.cascade.one.winding_fold
srmech.music.bessel_j_fixed
srmech.music.commensurability_verdict
srmech.music.spectrum_tier
srmech.math.laplacian.cyclic_laplacian_spectrum
srmech.asymptotic_calculus
srmech.calculus
""".split()
def resolve(p):
    parts = p.split('.')
    # try longest importable module prefix
    for i in range(len(parts), 0, -1):
        modname = '.'.join(parts[:i])
        try:
            m = importlib.import_module(modname)
        except Exception as ex:
            continue
        obj = m
        for attr in parts[i:]:
            if not hasattr(obj, attr):
                return ("PARTIAL", modname, attr)
            obj = getattr(obj, attr)
        return ("OK", modname, type(obj).__name__)
    return ("MISSING", None, None)
for p in paths:
    st, mod, extra = resolve(p)
    print(f"{p:60s} {st:8s} mod={mod} {extra}")
