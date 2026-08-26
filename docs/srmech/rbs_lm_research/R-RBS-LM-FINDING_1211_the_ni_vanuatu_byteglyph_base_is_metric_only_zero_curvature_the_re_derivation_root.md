# F1211 — The ni-Vanuatu byte-glyph BASE is metric-only (ZERO curvature): the re-derivation root. Direction was never carried at the root, so F1209/F1210 re-discovered it from wiki

**User (2026-07-14), root-first:** *"audit the ni-Vanuatu / sandroing core — does glyph-order / position-bind carry winding? … fix the re-derivation at its root."* Audit script: `R-RBS-LM-BYTEGLYPH_DIRECTION_AUDIT_…py` (srmech 0.9.0rc238, klein4 HDC).

## Measured — the base carries the METRIC but has ZERO CURVATURE
The ni-Vanuatu byte-glyph base (F761: the abstract translation layer every language kernel builds FROM; `_word_hv` = `klein4_bundle` of adjacent-glyph bigram binds). Splitting the two channels (the F1209/F1210 metric-vs-curvature split, at the glyph level):

| channel | test | result |
|---|---|---|
| **CURVATURE (direction/order)** | word vs its REVERSE (same adjacency, opposite direction) | `abc/cba`, `cat/tac`, `listen/netsil`, `stressed/desserts`, `draw/ward` all **sim 1.000** — bit-equal |
| **METRIC (undirected adjacency)** | ANAGRAM (changes adjacency; F1013's test) | `cat/act` 0.252, `listen/silent` 0.663 — distinguishable (BUT `stop/pots` = 1.000: they're *reverses*) |
| cause | `klein4_bind(a,b)` vs `bind(b,a)` | **sim 1.000 — ABELIAN** |

**The base cannot tell a word from its reverse.** It has the SAME bag-at-the-curvature-channel as the wiki kernel (F1210 B2: symmetric = zero curvature), **at the root**. The unused `_posrole` ("order-preserving bind", line 78 of the genepool — defined, never called by `_word_hv`) *also* collapses reverse to 1.000, because the klein4 similarity is itself order-blind (sector-occupancy) and the bind is abelian.

## Why — Klein-4 is the k=2 metric; direction is the non-abelian k=3/winding channel
`klein4_bind` is the abelian group op (Z₂×Z₂). An abelian bind is the **even/metric** structure — it carries which glyphs neighbor which (adjacency), never which came first (direction). Order/walk lives in the **non-abelian** channel: `[[feedback_reach_for_the_one_for_phase_crank_navigation]]` — *"the θ-crank is ABELIAN (a dial); walk-ORDER lives in non-commutative cd_mult."* There is **no klein4-native order primitive**: `hdc.permute` is a raw **bit-rotation on bytes**, not a sector-permute, so it doesn't compose with the klein4 bundle. So direction needs `the_one` winding / `cd_mult` / the sandroing directed walk — not the Klein-4 bind.

## F1013's "clean bag audit" checked only the even/metric channel
F1013 (2026-07-02) certified the byteglyph *"order-carrying, never bag-equal (anagrams 0.55–0.57)"* — but anagrams probe the **metric** (adjacency), not the **curvature** (direction). It never tested word-vs-reverse. So it measured the even part and passed, missing the odd part — the exact **F552 false-clean** (the odd/which-way channel the metric read provably can't see). The audit was right about the channel it tested and blind to the one it didn't.

## Sandroing carries the COUNT, not the directed WALK
`siona.story.sandroing_strokes` returns the closability count (Euler `max(1, odd_degree//2)`), NOT the ordered Eulerian traversal (the actual unicursal edge-sequence). So even the sandroing "core" doesn't currently materialize the directed walk — the order-native carrier is a topological predicate, not a stored path.

## The unification (why this is the re-derivation ROOT)
**A word IS a directed glyph-walk** (`c→a→t`) — a sandroing at the glyph scale (F1080: the unicursal Eulerian circuit). The **directed-edge object (F1210) is the SAME primitive at every scale**: glyph→glyph within a word, word→word in a corpus. Direction/curvature/winding is one thing, and it was **never carried at the ni-Vanuatu root** — so F1209/F1210 re-discovered the need from wiki co-occurrence. That is TRIALITY §5 / F552 "we keep re-deriving the same structure at a different coherence," made concrete: the gap is at the base, and the wiki directed re-encode was a symptom, not the source.

## Fix direction (the root fix — a real arc, not this audit)
Give the base the non-abelian direction channel, one object at every scale:
- **`the_one` winding** — a word's glyph-sequence → a winding coord (the sandroing walk); `separate_winding_curvature` reads it. The canonical home.
- **`cd_mult` non-commutative fold** — left-fold octonion glyph carriers (`abc ≠ cba` by non-commutativity).
- **directed glyph-graph per word** — F1210's directed-edge object applied at glyph scale (word = a tiny directed Class-L; metric = adjacency, charge = which-first).
- **`sandroing_strokes` → emit the actual Eulerian WALK** (Hierholzer), not just the count.
- **Upstream candidate:** a `klein4_permute` (sector-permutation order role) — currently missing (`permute` is byte-bit-rotation).

Composes **F761** (the base), **F1013** (the prior metric-only audit — corrected: order-carrying only in the metric channel), **F1080/F1079** (sandroing = Eulerian circuit / winding tower), **F1209/F1210** (curvature = the responsion; directed edges; the re-encode), **F552** (the odd channel the metric can't see), `[[feedback_never_bag_of_words_even_for_testing]]`, `[[feedback_reach_for_the_one_for_phase_crank_navigation]]` (abelian crank vs non-abelian walk), `[[project_ni_vanuatu_byteglyph_is_the_order_native_base_of_all_kernels]]`.
