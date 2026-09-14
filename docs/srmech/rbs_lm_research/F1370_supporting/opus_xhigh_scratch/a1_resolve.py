"""A1: resolve every dotted path the book tells the reader to run, against srmech rc472 main checkout, pure cell.
Instrument: importlib + getattr walk (no hand-rolled maths)."""
import sys, importlib, json
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
print("srmech", srmech.__version__, srmech.__file__)
try:
    from srmech import _native; print("HAS_NATIVE", _native.HAS_NATIVE)
except Exception as e: print("native?", e)
PATHS = [
 "srmech.__version__","srmech.amsc","srmech.amsc._native","srmech.amsc._native.HAS_NATIVE",
 "srmech.amsc.antikythera","srmech.amsc.antikythera.lunar_dial","srmech.amsc.cascade","srmech.amsc.catalog",
 "srmech.amsc.catalog.register_attested_root","srmech.amsc.catalog.list_attested_sources","srmech.amsc.catalog.get_attested_dataset",
 "srmech.amsc.class","srmech.amsc.cmb_residual","srmech.amsc.cmb_residual.smica_nilc_compare","srmech.amsc.cyclic",
 "srmech.amsc.cyclic.mod_add","srmech.amsc.cyclic.mod_mul","srmech.amsc.cyclic.mod_pow","srmech.amsc.cyclic.mod_inv","srmech.amsc.cyclic.gcd","srmech.amsc.cyclic.lcm",
 "srmech.amsc.dispatch","srmech.amsc.dispatch.match","srmech.amsc.dna","srmech.amsc.factorise","srmech.amsc.format",
 "srmech.amsc.format.sha256_bytes","srmech.amsc.format.read_ndjson","srmech.amsc.gap_suggester","srmech.amsc.hdc",
 "srmech.amsc.hdc.bind","srmech.amsc.hdc.bundle","srmech.amsc.hdc.permute","srmech.amsc.hdc.similarity",
 "srmech.amsc.introspect","srmech.amsc.kepler","srmech.amsc.kepler.kepler_solve","srmech.amsc.kepler.equation_of_centre","srmech.amsc.kepler.pin_slot",
 "srmech.amsc.laplacian","srmech.amsc.laplacian.dense_laplacian","srmech.amsc.laplacian.hermitian_eigendecompose","srmech.amsc.laplacian.jacobi_eigvals",
 "srmech.amsc.mtheory","srmech.amsc.mtheory.bipartite_modes","srmech.amsc.mycorrhizal","srmech.amsc.mycorrhizal.band_membership",
 "srmech.amsc.naming","srmech.amsc.naming.lookup","srmech.amsc.ndjson","srmech.amsc.octopus","srmech.amsc.physarum",
 "srmech.amsc.primes","srmech.amsc.primes.is_prime","srmech.amsc.primes.factor","srmech.amsc.primes.cyclic_period",
 "srmech.amsc.protein","srmech.amsc.protein.ramachandran","srmech.amsc.rational","srmech.amsc.rational.continued_fraction","srmech.amsc.rational.best_rational",
 "srmech.amsc.search","srmech.amsc.search.byte_search","srmech.amsc.template","srmech.amsc.template.render","srmech.amsc.tlv","srmech.amsc.tlv.tlv_pack",
 "srmech.amsc.tool_schema","srmech.amsc.tool_schema.get_tool_schema","srmech.amsc.tool_schema.tool_schema_view",
 "srmech.amsc.verify_attestation","srmech.amsc.verify_attestation.bytes",
 "srmech.asymptotic_dof","srmech.asymptotic_dof.toy_modulation_time","srmech.calculus","srmech.calculus.cycle_derivative",
 "srmech.cascade","srmech.cascade.cauchy_kernel","srmech.cascade.fft_decomposition","srmech.cascade.recursive_hopf_signs",
 "srmech.cascade.ring_equilibrium_attractor","srmech.cascade.shifted_circle_eigenvalues","srmech.catalogue","srmech.catalogue.class_frequency",
 "srmech.cognition","srmech.cognition.proof_check_cascade","srmech.cosmology","srmech.cosmology.dark_ratio_trajectory","srmech.cosmology.hubble_tension",
 "srmech.dark_sector","srmech.dark_sector.coupling_intensity","srmech.geometry","srmech.geometry.hopf","srmech.geometry.hopf.complex_project","srmech.geometry.hopf.octonionic_project",
 "srmech.gr","srmech.gr.isco","srmech.gr.isco.efficiency","srmech.kepler","srmech.kepler.solve","srmech.list_profiles","srmech.profile",
 "srmech.precession","srmech.precession.omega_sub","srmech.qm","srmech.qm.bell","srmech.qm.bell.chsh_operator_norm","srmech.qm.propagators",
 "srmech.qm.qft","srmech.qm.qft.decompose","srmech.qm.relativistic","srmech.qm.relativistic.schwarzschild_isco_efficiency","srmech.qm.single_particle","srmech.qm.spin",
 "srmech.shadows","srmech.signal_processing","srmech.signal_processing.fft","srmech.signal_processing.ifft","srmech.signal_processing.sign_quantise",
 "srmech.signal_processing.matched_filter","srmech.signal_processing.wiener","srmech.signal_processing.hdc_truncation",
 "srmech.spectral","srmech.spectral.decompose","srmech.spectral.delta","srmech.spectral.predict","srmech.spectral.recompose","srmech.spectral.truncate_sparse",
]
def resolve(p):
    parts = p.split(".")
    obj=None; last_mod=None
    for i in range(len(parts),0,-1):
        mod=".".join(parts[:i])
        try:
            obj=importlib.import_module(mod); last_mod=mod; rest=parts[i:]; break
        except ModuleNotFoundError as e:
            continue
        except Exception as e:
            return ("IMPORT-ERROR", f"{mod}: {type(e).__name__}: {e}")
    if obj is None: return ("MISSING", "no importable prefix")
    for r in rest:
        if hasattr(obj, r): obj=getattr(obj,r)
        else: return ("MISSING", f"deepest importable: {last_mod}; missing attr {r!r} after {'.'.join(parts[:parts.index(r)])}")
    return ("EXISTS", f"{type(obj).__name__} {getattr(obj,'__module__','') or getattr(obj,'__name__','')}")
res={}
for p in PATHS:
    s,d = resolve(p); res[p]=(s,d); print(f"{s:12s} {p:55s} {d}")
json.dump(res, open("a1_resolve.json","w"), indent=1)
print(sum(1 for v in res.values() if v[0]=="EXISTS"), "exist of", len(res))
