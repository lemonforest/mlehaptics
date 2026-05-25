"""R-RBS-LM-23 — RBS-LM tool_schema profile registrations.

Defines ToolEntry registrations for the RBS-LM research-subtree callables,
following the existing srmech.amsc.tool_schema pattern (R-RBS-LM-12 §2.2
surveyed in R-RBS-LM-23 §3).

Registers as an `owner="rbs_lm"` profile via register_profile_tools, which
keeps RBS-LM entries cleanly separable from srmech's own tools + allows
clean unregister if needed.

Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`: this module
lives in the research subtree for now. When the srmech-fix session lands
v0.5.0rc with the `srmech.rbs_lm` subpackage (per R-RBS-LM-12 §6), the
same ToolEntry definitions move into the package; the `owner` switches
from "rbs_lm" (profile-contributed) to "srmech" (first-party).

Usage:
    sys.path.insert(0, "docs/srmech/python")
    sys.path.insert(0, "docs/srmech/rbs_lm_research")
    from rbs_lm_tools import register_rbs_lm_profile
    register_rbs_lm_profile()

    from srmech.amsc.tool_schema import tool_schema_view
    print(tool_schema_view())
"""

import sys
from pathlib import Path

# Path setup — research-subtree imports
HERE = Path(__file__).parent
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))   # srmech package
sys.path.insert(0, str(HERE))                                       # research scripts

from srmech.amsc.tool_schema import (  # noqa: E402
    ToolEntry,
    ToolParameter,
    ToolReturn,
    register_profile_tools,
)


PROFILE_NAME = "rbs_lm"


def _entries() -> list[ToolEntry]:
    """The RBS-LM ToolEntry list."""
    return [
        # ---- Encoding (Path B + Path C; R-RBS-LM-2/-4/-17) -------------
        ToolEntry(
            name="rbs_lm.encoder.mint_vector",
            owner=PROFILE_NAME,
            category="encoder",
            summary="Class A content-mint: deterministic D-bit hypervector from a "
                    "name string via SHA-256 chain (Spike #170 invariant 1). "
                    "Used for token IDs, position vectors, and sentinels.",
            parameters=(
                ToolParameter("name", "str", required=True,
                              summary="Name string; same name → same vector"),
                ToolParameter("D", "int", required=False,
                              summary="Hypervector dimension (default 8192 per Spike #170)"),
            ),
            returns=ToolReturn(type="bytes", shape="D/8 bytes; binary BSC representation"),
            smoke_test_hint={"name": "'test'", "D": "8192"},
        ),
        ToolEntry(
            name="rbs_lm.encoder.encode_context",
            owner=PROFILE_NAME,
            category="encoder",
            summary="Kanerva sequence representation per R-RBS-NN-5 §3.1: "
                    "bind(token_k, P_k) for each position k; bundle into a "
                    "single context hypervector. Used by both Path B "
                    "(srmech-native vocab) and Path C (WTE-projected vocab) "
                    "with the appropriate vocab table.",
            parameters=(
                ToolParameter("token_ids", "Sequence[int]", required=True,
                              summary="Token IDs (truncated to last CONTEXT_WINDOW)"),
                ToolParameter("D", "int", required=False,
                              summary="Hypervector dimension (default 8192)"),
            ),
            returns=ToolReturn(type="bytes", shape="D/8 bytes context hypervector"),
        ),
        ToolEntry(
            name="rbs_lm.encoder.encode_observation",
            owner=PROFILE_NAME,
            category="encoder",
            summary="One Path B observation: bind(context_vec, next_token_vec). "
                    "The canonical Path B binding per R-RBS-LM-2 §6.1.",
            parameters=(
                ToolParameter("context_tokens", "Sequence[int]", required=True),
                ToolParameter("next_token", "int", required=True),
                ToolParameter("D", "int", required=False),
            ),
            returns=ToolReturn(type="bytes", shape="D/8 bytes; one binding"),
        ),
        ToolEntry(
            name="rbs_lm.encoder.hierarchical_bundle",
            owner=PROFILE_NAME,
            category="encoder",
            summary="Bundle vectors hierarchically for n > srmech MAX_BUNDLE_N=257 "
                    "per R-RBS-NN-7 §3.2. Splits into sub-groups of ≤257, bundles "
                    "each, then recurses on sub-bundles. Each hierarchy level "
                    "carries an additional bundle-projection cost (MFO §VII.1.3 "
                    "line 741 ~6.9% per layer); R-RBS-LM-19 §5 nuances this as "
                    "ALSO providing context-integration.",
            parameters=(
                ToolParameter("vectors", "Sequence[bytes]", required=True),
                ToolParameter("group_size", "int", required=False,
                              summary="Cap before sub-bundling (default 257 = MAX_BUNDLE_N)"),
            ),
            returns=ToolReturn(type="bytes", shape="D/8 bytes; combined instrument"),
        ),

        # ---- Path C — WTE-projected vocab (R-RBS-LM-17) ----------------
        ToolEntry(
            name="rbs_lm.path_c.compute_vocab_table",
            owner=PROFILE_NAME,
            category="path_c",
            summary="Path C: project source-model WTE matrix (50257 × 768 for "
                    "GPT-2-small) to D dimensions via Johnson-Lindenstrauss random "
                    "Gaussian projection, then bipolar-quantize. Preserves "
                    "semantic structure: ' the' vs ' The' cosine ≈ +0.49 at D=8192 "
                    "(R-RBS-LM-17 §3.2). First non-zero RBS-LM result lift per "
                    "R-RBS-LM-17.",
            parameters=(
                ToolParameter("model", "GPT2LMHeadModel", required=True,
                              summary="Source HuggingFace transformer model"),
                ToolParameter("D", "int", required=False,
                              summary="Target hypervector dim (default 8192)"),
                ToolParameter("seed", "int", required=False,
                              summary="Random projection seed (default 42)"),
            ),
            returns=ToolReturn(
                type="numpy.ndarray",
                shape="(vocab_size, D/8) uint8; vocab table with preserved semantic structure",
            ),
        ),

        # ---- Inference (R-RBS-LM-6 + R-RBS-LM-17 Path C variant) ------
        ToolEntry(
            name="rbs_lm.inference.vectorised_cleanup",
            owner=PROFILE_NAME,
            category="inference",
            summary="Class K cleanup: argmin Hamming over vocab table. "
                    "Vectorised via np.bitwise_count (POPCNT primitive per "
                    "R-RBS-NN-8 §4.4). Returns top-k (token_id, similarity) "
                    "tuples.",
            parameters=(
                ToolParameter("candidate", "bytes", required=True),
                ToolParameter("vocab_table", "numpy.ndarray", required=True,
                              summary="(vocab_size, D/8) uint8 table"),
                ToolParameter("D", "int", required=False),
                ToolParameter("top_k", "int", required=False,
                              summary="Number of top matches to return (default 1)"),
            ),
            returns=ToolReturn(
                type="List[Tuple[int, float]]",
                shape="[(token_id, similarity), ...] sorted by similarity descending",
            ),
        ),
        ToolEntry(
            name="rbs_lm.inference.generate",
            owner=PROFILE_NAME,
            category="inference",
            summary="Iterative generation per R-RBS-NN-3b §6 4-class Level-1 "
                    "recipe (A mint → I cyclic → M bind → K argmax). Loads "
                    "saved instrument; produces next-token sequence given a "
                    "prompt. Per-token latency ~170-190 ms on the 2009 Xeon "
                    "E5530 with D=8192 (R-RBS-LM-6 §5.1).",
            parameters=(
                ToolParameter("instrument", "bytes", required=True,
                              summary="The encoded instrument hypervector"),
                ToolParameter("prompt_tokens", "List[int]", required=True),
                ToolParameter("max_new_tokens", "int", required=True),
                ToolParameter("vocab_table", "numpy.ndarray", required=True),
            ),
            returns=ToolReturn(
                type="Tuple[List[int], List[float]]",
                shape="(token_sequence, per_token_latencies_ms)",
            ),
        ),

        # ---- Storage (R-RBS-LM-22) -------------------------------------
        ToolEntry(
            name="rbs_lm.storage.disk_summary",
            owner=PROFILE_NAME,
            category="storage",
            summary="Read-only report of disk usage + research artefact sizes. "
                    "Flags ≥85% used as warning; ≥95% as critical. Used before "
                    "fetch operations to inform precheck decisions.",
            parameters=(
                ToolParameter("verbose", "bool", required=False,
                              summary="Print human-readable summary (default True)"),
            ),
            returns=ToolReturn(
                type="dict",
                shape="{'disk_free_bytes', 'disk_pct_used', 'artefacts', ...}",
            ),
        ),
        ToolEntry(
            name="rbs_lm.storage.cleanup_caches",
            owner=PROFILE_NAME,
            category="storage",
            summary="Remove regenerable caches (vocab_table.npy first; optional "
                    "HF model caches by name). vocab_table regenerates in ~4s.",
            parameters=(
                ToolParameter("remove_vocab_table", "bool", required=False,
                              summary="Delete vocab_table.npy (default True)"),
                ToolParameter("hf_models", "List[str]", required=False,
                              summary="HF model names to remove from cache"),
            ),
            returns=ToolReturn(type="int", shape="Total bytes freed"),
        ),
        ToolEntry(
            name="rbs_lm.storage.precheck_fetch",
            owner=PROFILE_NAME,
            category="storage",
            summary="Verify free disk >= estimated_bytes + safety_margin before "
                    "fetching a model or large file. Raises StorageInsufficientError "
                    "on insufficient space. Called by encode/harvest scripts.",
            parameters=(
                ToolParameter("estimated_bytes", "int", required=True),
                ToolParameter("safety_margin_gb", "float", required=False,
                              summary="Headroom beyond fetch (default 1.0 GB)"),
                ToolParameter("label", "str", required=False),
            ),
            returns=ToolReturn(
                type="dict",
                shape="{'disk_free_bytes', 'estimated_bytes', 'headroom_after_fetch_bytes', ...}",
            ),
        ),

        # ---- Validation (R-RBS-LM-7) -----------------------------------
        ToolEntry(
            name="rbs_lm.validation.run_against_baseline",
            owner=PROFILE_NAME,
            category="validation",
            summary="Run RBS-HDC inference on a fixed prompt corpus; compare "
                    "token-by-token against source-model argmax. Reports overall "
                    "agreement % + per-position trajectory + scenario mapping "
                    "per R-RBS-LM-1 §7 four-scenario reading.",
            parameters=(
                ToolParameter("instrument", "bytes", required=True),
                ToolParameter("vocab_table", "numpy.ndarray", required=True),
                ToolParameter("source_model_name", "str", required=False,
                              summary="HF model identifier (default 'gpt2')"),
                ToolParameter("prompts", "Optional[List[str]]", required=False,
                              summary="If None, uses R-RBS-LM-3 §6.3 hallucination corpus"),
            ),
            returns=ToolReturn(
                type="dict",
                shape="{'overall_agreement_pct', 'per_prompt_results', 'scenario', ...}",
            ),
        ),

        # ---- Catalog (R-RBS-LM-12 + R-RBS-LM-13) -----------------------
        ToolEntry(
            name="rbs_lm.catalog.validate",
            owner=PROFILE_NAME,
            category="catalog",
            summary="Validate the docs/srmech/catalogs/rbs_lm/ catalog: 6 "
                    "mandatory AMSC sections; compute_from_source schema; "
                    "research_notes.ndjson; adapter-resolution status (GATED "
                    "until srmech v0.5.0rc per R-RBS-LM-13 §5).",
            parameters=(),
            returns=ToolReturn(
                type="dict",
                shape="{'sections_ok': bool, 'adapter_status': 'GATED'|'IMPLEMENTED', ...}",
            ),
        ),
    ]


def register_rbs_lm_profile():
    """Register all RBS-LM tools as an 'rbs_lm' profile. Idempotent."""
    register_profile_tools(PROFILE_NAME, _entries())
    return len(_entries())


if __name__ == "__main__":
    # Self-test: register + report
    n = register_rbs_lm_profile()
    print(f"Registered {n} RBS-LM tool entries.")

    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    by_category = {}
    for tool in schema.by_owner(PROFILE_NAME):
        by_category.setdefault(tool.category, []).append(tool.name.split(".")[-1])
    print(f"\nRBS-LM tool registry ({len(schema.by_owner(PROFILE_NAME))} entries):")
    for category, names in sorted(by_category.items()):
        print(f"  {category}: {', '.join(names)}")
    print(f"\nTotal srmech tool registry: {len(schema.tools)} entries "
          f"({len(schema.by_owner('srmech'))} srmech + "
          f"{len(schema.by_owner('rbs_lm'))} rbs_lm)")
