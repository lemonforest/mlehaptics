"""Split tools/ripple_gates.txt into N part-manifests of roughly equal cost,
preserving every target exactly once. Costs are the seconds the manifest's own
comments quote for the slow gates; everything else is taken as 5 s.

Usage: python m_ripple_split.py <ripple_gates.txt> <N> <out_dir>
"""
import sys
from pathlib import Path

src = Path(sys.argv[1]); n = int(sys.argv[2]); out = Path(sys.argv[3])
KNOWN = {
    "test_native_contract_parity_rc431": 200, "test_content_address_class_rc462": 124,
    "test_frame_scope_rc430": 120, "test_g2_certificate_rc462": 88,
    "test_regen_all_rc346": 78, "test_frame_action_rc461": 55,
    "test_registry_completeness_rc416": 46, "test_catalog_chain_infer_c_rc175": 45,
    "test_jpl_audit": 43, "test_chain_run_c_rc174": 42,
    "test_adr_citation_integrity_rc415": 39, "test_cd_register_engine_c_rc464": 31,
    "test_op_name_set_witness_rc361": 30, "test_citation_contradiction_rc436": 30,
    "test_dsl": 30, "test_dsl_tools": 30, "test_dsl_tool_surface_descriptions": 30,
    "test_dsl_op_naming_boundaries": 30, "test_introspect": 25,
    "test_composes_population_rc423": 25, "test_affine_kac_walton_rc461": 25,
    "test_genome_carrier_coverage_rc340": 25, "test_preserves_taxonomy_rc423": 20,
    "test_citation_manifest_rc428": 20, "test_ledger_freshness_hook_rc468": 19,
    "test_walsh_hadamard_rc437": 18, "test_gamma_zero_kernel_rc462": 16,
}
targets = []
for line in src.read_text(encoding="utf-8").replace("\r", "").split("\n"):
    s = line.strip()
    if s and not s.startswith("#"):
        targets.append(s)


def cost(t):
    stem = t.split("::")[0].split("/")[-1].removesuffix(".py")
    return KNOWN.get(stem, 5)


parts = [[] for _ in range(n)]
load = [0] * n
for t in sorted(targets, key=cost, reverse=True):
    i = load.index(min(load))
    parts[i].append(t)
    load[i] += cost(t)
out.mkdir(parents=True, exist_ok=True)
seen = []
for i, p in enumerate(parts, 1):
    order = [t for t in targets if t in p]          # keep manifest order inside a part
    (out / f"ripple_part{i}.txt").write_text("\n".join(order) + "\n", encoding="utf-8")
    seen.extend(order)
    print(f"part {i}: {len(order)} targets, estimated {load[i-1]} s")
assert sorted(seen) == sorted(targets) and len(seen) == len(set(seen)) == len(targets)
print(f"total targets {len(targets)}; every target in exactly one part: True")
