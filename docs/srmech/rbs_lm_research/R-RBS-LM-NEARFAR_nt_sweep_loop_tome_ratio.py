r"""R-RBS-LM-NEARFAR (F747 add-on) — near:far ratio of the loop-tome bookshelf at NT=11/14/16 on a wiki kernel.
NT=11 = the 11D observer-frame reading (3D_s+7D_g+1D_t) AND odd -> the conjugation mirror is frustrated/live
(F540/F544: odd rings have no fixed antipode pairs, the chirality never lands). near = a word's true neighbours in
its own+adjacent tome (local recall); far = words whose strongest neighbour is a non-adjacent tome (cross-ring chord).
Reuses R-RBS-LM-TOMECMP. WIKI_KERNEL env selects the kernel (default: simplewiki_kernel_256.json). No re-encode."""
import importlib.util as U, json, os
from pathlib import Path
_s = U.spec_from_file_location("tc", "docs/srmech/rbs_lm_research/R-RBS-LM-TOMECMP_14_loop_vs_16_sedenion_register_with_storyteller.py")
tc = U.module_from_spec(_s); _s.loader.exec_module(tc)
K = Path(os.environ.get("WIKI_KERNEL", str(Path.home() / "corpora/wikipedia/simplewiki_kernel_256.json")))
kernel = json.loads(K.read_text())
vocab, V, edges, weights, n = tc.eigvecs(kernel)
nbr = tc.neighbours(n, edges, weights)
print(f"=== loop-tome near:far sweep on {K.name} ({n} vocab, {len(edges)} edges) ===")
for NT in (11, 14, 16):
    t = tc.route(V, n, NT)
    near, far = tc.locality(t, nbr, NT), tc.far_chords(t, nbr, NT)
    ratio = (near / far) if far else float("inf")
    parity = "ODD  -> live/frustrated mirror (F544)" if NT % 2 else "even -> static antipode mirror"
    print(f"  NT={NT:2d}: near(own+adj) {near:.0%}  far-chords {far:.0%}  near:far {ratio:4.1f}  | "
          f"{len(set(t))}/{NT} tomes | {parity}")
