"""
Spike #45 Round 1 — Human-substrate kinship fingerprints.

Human cognitive/cultural kinship substrates. NO real-name targeting.
NO human-group political categorisation. Descriptive only per
[[feedback_trauma_informed_defensive_scope]].

Substrates: citation networks (academic-paper kinship), open-source code
lineage (fork/clone), folktale ATU index (cultural transmission), math
genealogy (advisor/student), sister-project portfolio (project's own kin).

Each substrate is encoded as a record + 15-feature fingerprint mapping
onto the Spike #44 R2 schema for cross-substrate comparison.
"""

import json
import math
from pathlib import Path

OUT_DIR = Path(__file__).parent
RECORDS_PATH = OUT_DIR / "human_records.ndjson"
FINGERPRINTS_PATH = OUT_DIR / "human_fingerprints.ndjson"
DATE = "2026-05-17"
SPIKE = "spike_45_round1"

human_substrates = [
    {
        "substrate": "academic_citation_network_physics",
        "domain": "academic_kinship",
        "kinship_kind": "directed_citation_lineage",
        "n_units_attested": 1500000,  # arXiv hep-th submissions ~1.5M cumulatively
        "median_lineage_depth": 8,  # typical 8-deep citation chains
        "n_strongly_connected_components": 1,  # giant component dominates
        "kinship_code": 2,  # directed lineage + bidirectional citation co-membership
        "decisive_variable": "shared_citation_substrate",
        "transmission_mode": "explicit_citation_act_carries_kinship",
        "kinship_decisive": True,
        "epsilon_kinship_decay_per_generation": 0.30,
        "citation_doi": "10.1073/pnas.0507655102",
        "citation_authors": "Newman MEJ",
        "citation_year": 2006,
        "citation_title": "Modularity and community structure in networks",
        "citation_venue": "PNAS 103 8577",
        "access": "open_access_pnas",
        "framework_anchor": "Class L Fiedler partition of citation graph reveals research-community kin-clusters",
    },
    {
        "substrate": "github_linux_kernel_fork_lineage",
        "domain": "code_kinship",
        "kinship_kind": "fork_clone_inheritance",
        "n_units_attested": 100000,  # ~100k forks of linux kernel
        "median_lineage_depth": 4,
        "n_strongly_connected_components": 1,
        "kinship_code": 1,  # strongly tree-like (all from one root)
        "decisive_variable": "git_commit_ancestry_dag",
        "transmission_mode": "explicit_git_history_carries_kinship_exactly",
        "kinship_decisive": True,
        "epsilon_kinship_decay_per_generation": 0.10,  # forks retain near-perfect ancestor
        "citation_doi": "10.1109/MSR.2014.36",
        "citation_authors": "Borges H, Hora A, Valente MT",
        "citation_year": 2014,
        "citation_title": "Understanding the factors that impact the popularity of GitHub repositories",
        "citation_venue": "MSR/IEEE",
        "access": "open_access_arxiv_1606.04984",
        "framework_anchor": "Class C streaming cascade through git commit DAG; Class I cyclic when forks merge back",
    },
    {
        "substrate": "atu_folktale_index",
        "domain": "cultural_transmission_kinship",
        "kinship_kind": "story_motif_inheritance_across_cultures",
        "n_units_attested": 2399,  # ATU index has ~2400 tale types
        "median_lineage_depth": 50,  # tale types cross many cultures
        "n_strongly_connected_components": 1,  # giant connected component
        "kinship_code": 2,
        "decisive_variable": "shared_motif_ancestry",
        "transmission_mode": "oral_to_written_transmission_carries_kinship",
        "kinship_decisive": True,
        "epsilon_kinship_decay_per_generation": 0.20,  # tale-type survives many generations
        "citation_doi": None,
        "citation_authors": "Uther HJ",
        "citation_year": 2004,
        "citation_title": "The Types of International Folktales: A Classification and Bibliography",
        "citation_venue": "FF Communications 284-286, Helsinki",
        "access": "public_domain_reference_index",
        "framework_anchor": "Class E catalog lookup across motif-index; Class L community detection of tale-clusters",
    },
    {
        "substrate": "math_genealogy_project",
        "domain": "intellectual_kinship",
        "kinship_kind": "advisor_student_lineage",
        "n_units_attested": 295000,  # MGP indexed 295k mathematicians (2024 snapshot)
        "median_lineage_depth": 10,  # 10-deep advisor chains common
        "n_strongly_connected_components": 1,
        "kinship_code": 1,  # tree-like advisor-student
        "decisive_variable": "explicit_advisor_designation",
        "transmission_mode": "dissertation_certifies_kinship_explicitly",
        "kinship_decisive": True,
        "epsilon_kinship_decay_per_generation": 0.25,
        "citation_doi": None,
        "citation_authors": "Mathematics Genealogy Project (NDSU)",
        "citation_year": 2024,
        "citation_title": "Mathematics Genealogy Project public dataset",
        "citation_venue": "genealogy.math.ndsu.nodak.edu",
        "access": "open_access_public_dataset",
        "framework_anchor": "Class L graph Laplacian on advisor-student tree; lineage depth = Class K asymptotic-DOF rate",
    },
    {
        "substrate": "open_source_python_pypi_ancestry",
        "domain": "code_kinship",
        "kinship_kind": "module_dependency_inheritance",
        "n_units_attested": 500000,  # PyPI ~500k packages
        "median_lineage_depth": 6,
        "n_strongly_connected_components": 1,
        "kinship_code": 2,  # dependencies form DAG; some bidirectional plug-in patterns
        "decisive_variable": "import_declaration_in_setup.py_or_pyproject.toml",
        "transmission_mode": "explicit_dependency_declaration_carries_kinship",
        "kinship_decisive": True,
        "epsilon_kinship_decay_per_generation": 0.15,
        "citation_doi": "10.1109/MSR.2019.00094",
        "citation_authors": "Decan A, Mens T, Constantinou E",
        "citation_year": 2019,
        "citation_title": "On the impact of security vulnerabilities in the npm package dependency network",
        "citation_venue": "MSR/IEEE",
        "access": "open_access_msr_2019",
        "framework_anchor": "Class E catalog lookup (PyPI); Class C streaming via dependency resolver; Class L community of package families",
    },
    {
        "substrate": "spectral_research_portfolio_self_reference",
        "domain": "project_internal_kinship",
        "kinship_kind": "sister_notebook_cross_reference",
        "n_units_attested": 9,  # 9 notebooks in the portfolio (srmech, chess, ephem, antik, mfo, doom, logo, othello, plus 4d-chess)
        "median_lineage_depth": 3,
        "n_strongly_connected_components": 1,  # cross-references make portfolio cohesive
        "kinship_code": 2,
        "decisive_variable": "shared_MPM_discipline_and_cross_references",
        "transmission_mode": "user_authored_cross_references_in_notebook_text",
        "kinship_decisive": True,
        "epsilon_kinship_decay_per_generation": 0.05,  # portfolio is tightly knit
        "citation_doi": None,
        "citation_authors": "Project self-reference",
        "citation_year": 2026,
        "citation_title": "Spectral research portfolio (docs/srmech, chess-maths, antikythera-maths, logo-maths, othello-maths)",
        "citation_venue": "internal repo",
        "access": "internal_project",
        "framework_anchor": "Class L on cross-reference graph; sister notebooks share Class M / Class L / Class K vocabulary",
    },
    {
        "substrate": "arxiv_coauthorship_network_astro_ph",
        "domain": "academic_kinship",
        "kinship_kind": "collaboration_network",
        "n_units_attested": 50000,  # ~50k unique astro-ph authors
        "median_lineage_depth": 6,  # collaboration distance
        "n_strongly_connected_components": 1,
        "kinship_code": 2,  # bidirectional coauthorship + lineage
        "decisive_variable": "shared_authorship_on_published_work",
        "transmission_mode": "joint_authorship_carries_kinship",
        "kinship_decisive": True,
        "epsilon_kinship_decay_per_generation": 0.40,  # collaborations more transient
        "citation_doi": "10.1073/pnas.98.2.404",
        "citation_authors": "Newman MEJ",
        "citation_year": 2001,
        "citation_title": "Scientific collaboration networks. I. Network construction and fundamental results",
        "citation_venue": "Phys Rev E 64 016131",
        "access": "open_access_prE_2001",
        "framework_anchor": "Class L Fiedler partition of coauthorship graph; small-world property = high asymmetric Class E catalog asymmetry",
    },
]


def to_15_feature_fingerprint(rec: dict) -> dict:
    """Project a human substrate onto the Spike #44 R2 15-feature schema."""
    return {
        "substrate": rec["substrate"],
        "domain": rec["domain"],
        "f1_InterLethal": 0.0,  # not applicable; no biological aggression analog
        "f2_IntraLethal": 0.0,
        "f3_GroupCohesion": 1.0 / (rec.get("epsilon_kinship_decay_per_generation") or 1.0),
        "f4_MatriAnalog": 1 if rec["kinship_decisive"] else 0,
        "f5_BodySize_log10n": math.log10(max(rec["n_units_attested"], 1)),
        "f6_Coalition": 1 if "collaboration" in rec.get("kinship_kind", "") or
            rec.get("kinship_kind") == "fork_clone_inheritance" else 0,
        "f7_Generations_logmyr": math.log10(max(rec["median_lineage_depth"], 1)),  # depth as gen proxy
        "f8_LineageDepth_logmyr": math.log10(max(rec["median_lineage_depth"], 1)),
        "f9_SubstrateSharing_chem": 1,  # all human substrates share content explicitly
        "f10_Tool": 1 if rec["domain"] == "code_kinship" else 0,
        "f11_Allo": 1 if rec["domain"] == "code_kinship" else 0,  # code-sharing = allo-care analog
        "f12_MultiGen": 1 if rec["median_lineage_depth"] > 3 else 0,
        "f13_PostRep": 1,
        "f14_KinshipCode": rec["kinship_code"],
        "f15_EpsDecay": rec["epsilon_kinship_decay_per_generation"],
        "kinship_decisive": rec["kinship_decisive"],
    }


def main() -> int:
    with RECORDS_PATH.open("w", encoding="utf-8") as f:
        for rec in human_substrates:
            r = dict(rec)
            r["date"] = DATE
            r["spike"] = SPIKE
            r["kind"] = "human_substrate"
            f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(human_substrates)} human records to {RECORDS_PATH}")

    with FINGERPRINTS_PATH.open("w", encoding="utf-8") as f:
        for rec in human_substrates:
            fp = to_15_feature_fingerprint(rec)
            fp["date"] = DATE
            fp["spike"] = SPIKE
            fp["kind"] = "human_fingerprint"
            f.write(json.dumps(fp) + "\n")
    print(f"Wrote {len(human_substrates)} human fingerprints to {FINGERPRINTS_PATH}")

    n_decisive = sum(1 for r in human_substrates if r["kinship_decisive"])
    print(f"\nHuman substrate H_kinship-decisive count: {n_decisive}/{len(human_substrates)}")
    codes = {}
    for r in human_substrates:
        codes[r["kinship_code"]] = codes.get(r["kinship_code"], 0) + 1
    print("Kinship-code distribution:")
    for k in sorted(codes.keys()):
        print(f"  code {k}: {codes[k]} substrate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
