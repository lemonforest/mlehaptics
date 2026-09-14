"""A2: AST index of every def/class/assignment name in every tracked .py under docs/ (srmech + sister packages + notes/spike scripts).
Instrument: git ls-files + ast (hand-rolled indexer; no maths)."""
import ast, subprocess, json, collections, os
root="D:/GitHub/mlehaptics"
files=subprocess.run(["git","-C",root,"ls-files","docs/*.py","docs/**/*.py"],capture_output=True,text=True).stdout.split()
files=sorted(set(files))
idx=collections.defaultdict(list); stems=collections.defaultdict(list); bad=0
for f in files:
    p=os.path.join(root,f)
    stems[os.path.splitext(os.path.basename(f))[0]].append(f)
    try: tree=ast.parse(open(p,encoding="utf-8",errors="replace").read())
    except Exception: bad+=1; continue
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            idx[node.name].append(f"{f}:{node.lineno}")
        elif isinstance(node,ast.Assign) and isinstance(getattr(node,'targets',[None])[0],ast.Name) and node.col_offset==0:
            idx[node.targets[0].id].append(f"{f}:{node.lineno}=")
json.dump({"defs":idx,"stems":stems},open("a2_index.json","w"))
print(len(files),"files",bad,"unparsed")
LEAVES="""_native HAS_NATIVE antikythera lunar_dial cascade class cmb_residual smica_nilc_compare cyclic mod_add mod_mul mod_pow mod_inv gcd lcm dispatch match dna factorise factor factorize hdc bind bundle permute similarity introspect kepler kepler_solve equation_of_centre equation_of_center pin_slot laplacian dense_laplacian hermitian_eigendecompose jacobi_eigvals mtheory bipartite_modes mycorrhizal band_membership naming lookup ndjson octopus physarum primes is_prime cyclic_period protein ramachandran rational continued_fraction best_rational search byte_search template render tlv tlv_pack tool_schema get_tool_schema tool_schema_view verify_attestation asymptotic_dof toy_modulation_time cycle_derivative cauchy_kernel fft_decomposition recursive_hopf_signs ring_equilibrium_attractor shifted_circle_eigenvalues catalogue class_frequency cognition proof_check_cascade cosmology dark_ratio_trajectory hubble_tension dark_sector coupling_intensity geometry hopf complex_project octonionic_project gr isco efficiency isco_efficiency precession omega_sub qm bell chsh_operator_norm propagators qft decompose relativistic schwarzschild_isco_efficiency kerr_isco_efficiency single_particle spin shadows fft ifft solve""".split()
for L in LEAVES:
    d=idx.get(L,[]); s=stems.get(L,[])
    print(f"## {L}: defs={len(d)} stems={len(s)}")
    for x in d[:12]: print("   def", x)
    for x in s[:12]: print("   file", x)
