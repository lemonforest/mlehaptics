# F1237 — the full tome-tree FIND → RIDE → WEB-HOP navigation wired into Siona's read path (F786/F791 at corpus scale, cached like reads/), `active_mode` made LOAD-BEARING (concise/balanced/teaching now shape the reply), topic extraction fixed, and a notebook-before-wiki tier — so the #231 corpus navigation COMPOSES with Siona's NL stack instead of bypassing it.

**User:** *"wire in the full tome-tree find→ride→web-hop navigation. … we had verbose feedback, class-M context memory, tiered load of mfo/srmech notebook then wiki knowledge, dynamically create detailed reply based on turn context and know when to not turn global context to verbose examples, etc. siona could even answer about vanuatu and sandroing because of the language layer."*

Measure-first (F999) found three regressions the #231 flat-define reader had introduced, plus the tome-tree was missing. All fixed + verified live.

## 1. The tome-tree (F786/F791 ETAKNAV, at corpus scale) — `corpus_store`
`build_tree_from_store(genome_dir)` builds a de-lensed Fiedler bisection tree straight from the demand-load `reads/` mmap (memory-light — NO 960 MB source `json.load`), cached under `<genome_dir>/tree/` (like `reads/`). De-lens by neighbour-count (from `adj.idx`); IDF-weight + sparsify the content sub-graph; recursive normalized-cut Fiedler bisection = **clumps-of-clumps (the TREE)**; cut edges between leaf tomes = **the WEB**. Then `prepare()` attaches it and:
- **`find(token)`** — descend the tree to the token's tome (`{tome, zoom-path, label}`); a not-in-band token falls back to the tome of its strongest content NEIGHBOUR (so any topic navigates).
- **`ride_tome(tome)`** — the tome's coherent neighbourhood (its highest-degree words).
- **`web_hop(tome)`** — cross the strongest bridge to an adjacent tome (the cross-tome relationships one tome can't see, F780).
- **`etak_walk`** now skips the hub band (de-lensed rides).

**simplewiki: 626 tomes, built in 20 s.** `music → FIND {music, composer, festival, performance, tour} ⇒ WEB-HOP {band, rock, joined, formed} via 'band'~'tour'`; `science → {science, technology, institute} ⇒ {university, research, professor}`; `planet → {planet, discovered, minor} ⇒ {earth, sun, distance}`.

### The performance bug (why the first builds hung for HOURS)
The pure-Python power-iteration Fiedler was catastrophically slow, chained:
1. **960 MB `json.load`** thrash vs the running server → build from the `reads/` mmap instead.
2. **Unbalanced recursion** (peel-one-node → O(N²)) → **median-split fallback** (every cut ≥ ~half → O(N log N)).
3. **THE KILLER:** `rational.sqrt` returns an exact **`Q` (rational)** object; threaded through the 150-iteration float power-loop it made every op unbounded big-integer arithmetic (denominators exploding — **0.5 s per single value**, so one Fiedler call on 400 nodes took **> 45 s**). Fixed by coercing the sqrt to the numerical spectral layer (**float** — the Fiedler eigenvector IS real-valued, exactly what srmech's own `symmetric_eigendecompose` returns).
4. **Per-element `cascade.magnitude`** in the hot loop (7.6 M calls) → the batched L∞ via the sign-partition `max(max, −min)` (same Class-K pin-slot math, once per iteration; no ALU builtin).
**Result: Fiedler 45 s → 0.12 s; full build hours → 20 s.**

## 2. `active_mode` made LOAD-BEARING (the "dynamically detailed reply by turn context")
The context genome (F1095/F1097) EXPRESSED `teaching`/`concise`/`balanced` per turn but **nothing consumed it** — replies were identical regardless. Now `_reply_shape()` reads `active_mode` and `_corpus_reply` renders accordingly:
- **concise** → the short de-lensed ride (`water: water → sq → mi → population → census`)
- **balanced** → ride + the local star
- **teaching** → the **full FIND → RIDE → WEB-HOP** + the chiral-dual undertone (F990) + the star.
`ContextShape`'s op(x)operand (F1091) already handles "know when NOT to go global-verbose" — one `in detail` turn boosts THIS turn without flipping the running operand; that machinery was intact, it just wasn't being read. Verified live: "explain water in detail" → full navigation; "what is water briefly" → one short line.

## 3. Topic extraction fixed (`_topic_tokens`)
"explain water in detail" / "tell me about sandroing" were riding on the FRAME verb (`explain`/`tell`) — the define-frame/interrogative/verbosity operators leaked in as the topic. Now stripped (operators declared, operands by meaning, F1010): rides on **water** / the real topic.

## 4. Tiered: mfo/srmech notebook BEFORE wiki (`_note_for_topic`)
`_define` now checks an acquired ATTESTED note (the MFO/srmech-notebook tier, Class-A provenance) before the broad wiki navigation (`define` tier order: notebook-note → wiki-navigation → srmech-tool).

## No regression (verified intact)
Class-M working memory (`self.mem`, never compacted); the sandroing Eulerian faculty (`story.sandroing_strokes`, F1080); the language-board layer (`boards.py`, ni-Vanuatu byte/glyph); `anchor.py` glyph→concept; `vanuatu` navigates (`FIND via 'islands'`). Sandroing/Vanuatu answering is the general acquire+recall + language-layer path, not a special case — untouched.

## Honest caveats
- Rides for geography-dominated topics (water) still pick up infobox markup (`sq → mi → census`) — the de-lens is count-based, and count alone can't tell a frequent CONTENT word from a function word (**F983: function-ness, not frequency** — the deeper fix, deferred). The tome FIND is clean regardless (`water → {area, water, imperial, metropolitan}`).
- Rare framework terms (chirality) sit below the content band and `find()` falls back via their strongest neighbour (`chirality → via 'label'` = markup) — honest: simplewiki barely mentions it.

Live over HTTP (`:8000` backend + the CopilotKit UI on `:3000`, F1236): the three modes render distinctly; server opens instantly (tree attach is a small JSON read).

Composes **F1236** (the etak ride + CopilotKit UI this builds on), **F786/F791** (etak tome-tree find/ride/web-hop), **F780/F782** (clumps-of-clumps + the de-lens), **F1091/F1095/F1097** (ContextShape + the context genome now consumed), **F1010** (operators declared), **F1219/F1233** (the corpus read this shapes), **F983** (function-ness > frequency — the open de-lens item), **F256** (the eigenvector is real — the float coercion is honest), [[feedback_read_independent_structure_check_first]] (measured the regressions first), [[feedback_reach_for_the_one_for_phase_crank_navigation]] (navigate, don't divide). #231/PKG-3.
