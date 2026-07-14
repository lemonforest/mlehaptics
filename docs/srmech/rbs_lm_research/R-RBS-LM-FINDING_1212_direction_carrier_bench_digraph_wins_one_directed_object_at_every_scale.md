# F1212 — Direction-carrier bench for the ni-Vanuatu base: the DIGRAPH (F1210 one scale down) wins — one directed-edge object at every scale, round-trips as the sandroing walk

**User (2026-07-14), after F1211:** *"compare carriers first (winding vs cd_mult vs glyph-graph) … pick the canonical direction carrier for the base, then build the root fix on the winner."* Bench: `R-RBS-LM-DIRECTION_CARRIER_BENCH_…py` (srmech 0.9.0rc238). The base is metric-only (F1211); all three candidates are non-abelian, so all carry direction — the pick is decided by capacity + round-trip + genome-packability.

## Measured (41-word list, 6 genuine reverse pairs)
| carrier | direction (word≠reverse) | capacity (distinct sigs / 41) | round-trip | genome-composable |
|---|---|---|---|---|
| **A) winding** (net signed winding of the glyph-index walk) | 6/6 | **27** (14 collisions) | **NO** — a scalar can't recover glyphs | no (a summary) |
| **B) cd_mult** (octonion left-fold) | 6/6 | **40** (only the literal dup collides) | in principle (division algebra; `left_mult_is_invertible`=True) | opaque octonion (not sparse) |
| **C) digraph** (word = directed glyph-graph, F1210 scale-down) | 6/6 | 37 | **YES — 41/41 words recovered via the Eulerian walk** | **YES — the F1210 directed-edge object; packs as a kernel chromosome** |

Worked example `cat` vs `tac` (reverse): winding `-12` vs `+12`; cd_mult L2 `0.141` (≠0); digraph `((c,a),-1),((c,t),+1)` vs the sign-flipped `((c,a),+1),((c,t),-1)`, and it round-trips `cat→'cat'`, `tac→'tac'`.

## Verdict — pick C (digraph)
- **A winding** is directional but ~1 scalar → massive collisions (27/41) and no round-trip. It is a **derived read** — the sandroing closability / holonomy summary (F1079), the winding tower — not the base *store*. Keep it as a read-out, not the encoding.
- **B cd_mult** has the best raw discrimination (40/41, invertible) but the signature is an **opaque octonion** — not a sparse edge object you can pack as a chromosome or compose with the wiki digraph. Good as an optional high-capacity fingerprint; wrong as the base store.
- **C digraph WINS** — the only carrier that is directional **AND** round-trips concretely (41/41 via the Eulerian/**sandroing** walk, F1080) **AND** is genome-native (the same F1210 `edge_list + edge_weights[metric] + edge_charge[direction]` object, one scale down). It makes **"a word IS a directed glyph-walk"** literal and gives **one directed-edge object at every scale** — glyph→glyph in a word, word→word in a corpus — so wiki/dict-en project up on the identical primitive.

**Honest caveat:** digraph's capacity (37/41) is below cd_mult's (40/41) — window-1 directed consecutive-pairs collide for a few words with the same directed-adjacency multiset. This is **the same window knob as the wiki kernel**: widen the glyph window (window-2 directed edges) to lift capacity, exactly as WINDOW tunes the co-occurrence kernel. The collisions are a resolution setting, not a wall.

## The build (root fix, on C)
`_word_hv` → a directed glyph-graph: **metric** = the adjacency bundle we already have (keeps F1013's anagram discrimination), **charge** = which-glyph-first (the direction the base lacked). Persist genome-native ([[feedback_persist_genome_native_not_loose_json]]) as a `kernel_pack` chromosome. `winding` becomes the derived holonomy read; `sandroing_strokes` should emit the actual Eulerian walk (the round-trip already proves the reconstruction). Then wiki/dict-en project up from the direction-carrying base.

Composes **F1211** (the base is metric-only — this picks the fix), **F1210** (the directed-edge object — now shown to be the base primitive too), **F1080/F1079** (sandroing Eulerian walk / winding tower — the round-trip IS the sandroing reconstruction), **F1013** (metric channel kept), [[feedback_reach_for_the_one_for_phase_crank_navigation]] (winding = derived, not the store), [[project_ni_vanuatu_byteglyph_is_the_order_native_base_of_all_kernels]].
