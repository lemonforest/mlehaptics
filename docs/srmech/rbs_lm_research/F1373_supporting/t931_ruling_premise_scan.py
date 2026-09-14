"""F1373, maintainer ruling 2026-09-14: the premise check for the 19 `#T931` sites.

The ruling puts `klein4_address` at these sites because the vector made there is an ADDRESS:
bound into a pair, superposed into a memory, and retrieved by exact identity, with no code
comparing two different tokens' vectors. This script checks that on each file's AST.

For each file it:
  * finds the site: the dict comprehension that calls `klein4_address` or `klein4_encode_bytes`;
  * lists every other use of that dict's name, and reports any use that is not a lookup
    (`vec[t]`) or a membership test (`t in vec`);
  * classifies every `klein4_similarity(x, y)` call. A call counts as comparing two tokens'
    vectors when BOTH arguments use the dict and neither is a probe (built from the memory `M`,
    or named `probe` / `p` / `multiprobe` / `views`);
  * lists every comparison node (`==`, `<`, ...) with a use of the dict on either side.

It makes no git calls. Run it from anywhere; it reads the 19 scripts in the parent directory
(or the directory given as the first argument) and prints one NDJSON record per file.
Committed output: `t931_ruling_premise_scan.ndjson`, run on the tree of the commit that applied
the ruling. The site line is the only line that commit changed in these files, so every use,
read and comparison the record lists is also what `4db9932dd` had.
"""
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
FILES = [
    'R-RBS-LM-FINDING_976_multi_time_read_buys_sqrtk_altitude_but_the_rung_rate_is_invariant_ground_truth_of_loss.py',
    'R-RBS-LM-FINDING_981_etak_deeper_at_heavy_real_corpus_load_recovers_where_fast_fails.py',
    'R-RBS-LM-FINDING_982_de_lens_at_runtime_not_write_time_write_time_drop_doctors_the_ssot_and_destroys_shapes.py',
    'R-RBS-LM-FINDING_983_full_plus_runtime_delens_rebuild_raw_idf_too_blunt_needs_function_ness_not_frequency.py',
    'R-RBS-LM-FINDING_984_aboutness_gate_is_document_frequency_one_sided_suppression_the_correct_runtime_delens.py',
    'R-RBS-LM-FINDING_985_end_to_end_gate_wired_into_cut_and_emission_doubles_content_recall.py',
    'R-RBS-LM-FINDING_986_etak_deeper_on_gated_pipeline_lifts_buried_recall_57_to_82.py',
    'R-RBS-LM-FINDING_991_measure_R_on_real_gated_tomes_capacity_lever_pushes_it_wider_context_does_not.py',
    'R-RBS-LM-FINDING_992_low_load_landmarks_confirmed_the_wall_is_artificial_multi_perspective_breaks_it_soft_beats_hard.py',
    'R-RBS-LM-FINDING_993_chirality_frame_perspectives_collapse_on_identity_stored_M_you_cannot_read_a_chirality_you_didnt_write.py',
    'R-RBS-LM-FINDING_994_symmetric_chirality_is_useless_write_or_generate_the_storage_smart_lever_is_the_asymmetric_fractal_fold.py',
    'R-RBS-LM-FINDING_995_asymmetric_fold_encoder_separates_the_distribution_at_1x_storage_oracle_rung_76_vs_58.py',
    'R-RBS-LM-FINDING_997_resonant_spectral_store_beats_discrete_bundle_55_vs_42_but_subharmonic_only_fails_fine_edges_are_high_modes.py',
    'R-RBS-LM-FINDING_998b_two_tier_resonant_translation_bridge_grounded_bounded_high_band_kernel_resolves_fine_content.py',
    'R-RBS-LM-FINDING_998c_distributional_read_lifts_recall_to_92_top5_but_discrete_bundle_distributes_better_than_resonant_complementary.py',
    'R-RBS-LM-FINDING_998d_propose_resolve_pipeline_beats_both_alone_sparse_proposes_resonant_resolves_60_vs_53_vs_47.py',
    'R-RBS-LM-FINDING_999_elliptic_minus_z_inverse_rung_keys_MATCH_not_beat_independent_keys_on_discrete_read_structure_pays_off_in_resonant_read.py',
    'R-RBS-LM-FINDING_1000_QDFT_peak_read_closes_rung_selection_and_elliptic_BEATS_independent_on_the_phase_coherent_read_F999_prediction_confirmed.py',
    'R-RBS-LM-FINDING_1001_full_complex_QDFT_does_NOT_amplify_peak_is_optimal_for_the_single_rung_spike_elliptic_win_is_noise_floor_not_coherence.py',
]
PROBE_NAMES = {'M', 'probe', 'p', 'multiprobe', 'views'}


def main():
    for name in FILES:
        tree = ast.parse(open(os.path.join(ROOT, name), encoding='utf-8').read())
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        sites = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Assign) and isinstance(n.value, ast.DictComp)
                 and ('klein4_address' in ast.unparse(n.value) or 'klein4_encode_bytes' in ast.unparse(n.value))]
        assert len(sites) == 1, (name, len(sites))
        site = sites[0]
        dname = site.targets[0].id

        def uses(node):
            return [x for x in ast.walk(node) if isinstance(x, ast.Name) and x.id == dname]

        def is_token_vector(arg):
            names = {x.id for x in ast.walk(arg) if isinstance(x, ast.Name)}
            return bool(uses(arg)) and not (names & PROBE_NAMES)

        other_uses = []
        use_lines = set()
        for ref in uses(tree):
            if ref.lineno == site.lineno:
                continue
            use_lines.add(ref.lineno)
            parent = parents.get(ref)
            lookup = isinstance(parent, ast.Subscript) and parent.value is ref
            member = isinstance(parent, ast.Compare) and isinstance(parent.ops[0], (ast.In, ast.NotIn))
            if not (lookup or member):
                other_uses.append({'line': ref.lineno, 'expr': ast.unparse(parent)})
        sims = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and ast.unparse(node.func).endswith('klein4_similarity'):
                a, b = node.args[0], node.args[1]
                sims.append({'line': node.lineno, 'call': ast.unparse(node),
                             'uses_dict': [bool(uses(a)), bool(uses(b))],
                             'two_token_vectors': is_token_vector(a) and is_token_vector(b)})
        compares = [{'line': n.lineno, 'expr': ast.unparse(n)} for n in ast.walk(tree)
                    if isinstance(n, ast.Compare) and not isinstance(n.ops[0], (ast.In, ast.NotIn))
                    and any(uses(s) for s in [n.left] + n.comparators)]
        print(json.dumps({
            'file': name, 'dict': dname, 'site_line': site.lineno, 'site': ast.unparse(site),
            'use_lines': sorted(use_lines), 'uses_not_lookup_or_membership': other_uses,
            'similarity_calls': sorted(sims, key=lambda s: s['line']),
            'similarity_calls_on_two_token_vectors': sum(s['two_token_vectors'] for s in sims),
            'comparisons_on_a_dict_use': compares,
        }, ensure_ascii=False))


if __name__ == '__main__':
    main()
