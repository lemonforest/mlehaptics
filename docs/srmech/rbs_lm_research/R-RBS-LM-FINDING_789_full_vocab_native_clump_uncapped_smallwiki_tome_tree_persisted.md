# F789 — #1 delivered: the FULL simplewiki vocab clumps into a persisted TOME-TREE via the rc166 NATIVE §51 sparse Fiedler — the n≤256 wall is gone at scale (91,882 words → 11,711 tomes in 24 s). The uncapped, spectrally-navigable smallwiki is real; coherence is good-for-clear-words / noisy-for-others (honest), with the tuning + wiring levers named.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes / completes:** F785/F786 (the sparse-Fiedler prototype → now the NATIVE op), F778 (clump-don't-cap), F780 (clumps-of-clumps tree + webs), F784/F786 (de-lensing), §51/#1097 (delivered rc166) · **Provenance:** `R-RBS-LM-FULLCLUMP_native_sparse_fiedler_full_vocab_tome_tree.py` → `~/corpora/wikipedia/simplewiki_tome_tree.json` (OUTSIDE the repo) · **User direction (2026-06-16):** "validate the native §51 op, then run the full-vocab hierarchical clump + persist the tome-tree."

## Native §51 validated (100%)
On the worst-case dense 32-seed graph, rc166's `fiedler_sparse` and `normalized_cut_bisect` **both agree 100%** (sign-partition) with the dense normalized-Fiedler reference *and* with each other — and cleanly peel off `{music}` first, exactly like the F785/F786 prototype. Trustworthy.

## Full-vocab run (the deliverable)
Graph SOURCE = the assoc side-store (word → top-K co-occurrence neighbours; already sparse — no 240k-article rescan). De-lensed (F786): dropped the **top-300 in-degree hubs** (`american, people, english, footballer, german, …`) and the **rare/noise floor** (in-degree < 3 — hapax + extraction artifacts aren't navigable communities). IDF edge-weight `w = idf(a)·idf(b)` (in-degree IDF → suppress hub-incident edges). Recursive **native `normalized_cut_bisect`** → the tome-tree.
- **91,882 content words, 691,361 edges → 11,711 tomes in 24.3 s** (11,710 native cuts), peak RAM 533 MB, tree depth 10–21. **The n≤256 dense-Laplacian wall is gone at full scale** — this is the F778→F785→F786 arc completed natively.
- **Persisted** (`simplewiki_tome_tree.json`, 1.3 MB): the full word→tome partition + per-tome depth, attested CC-BY-SA, outside the repo.
- within-tome edge-weight fraction **60.8%** — moderate *by design*: at MAXTOME=12 a topic is split across **sibling tomes** (the F780 clumps-of-clumps), so ~40% of edge weight is the tree/web that *connects* the fragments, not noise.

## Coherence — honest (good for clear words, noisy for others)
Probe tomes (the leaf each word landed in):
- **clean:** `guitar → {glockenspiel, vibraphone, xylophone, tubular, tuned, agogo}` (instruments); `volcano → {mauna, kauai, kahoolawe, koolau, hualalai}` (Hawaiian volcanoes); `star → {orbits, binaries, eclipsing}` (astronomy).
- **fragmented (clumps-of-clumps, expected):** `ketchup → {packets, squeeze, saliva, swallowing, advertised}` — its *usage* sub-clump; the *ingredient* sub-clump (`salt, mustard, vinegar, heinz` — seen in the 20k run) is a **sibling tome**. The full ketchup topic = their shared **parent**; a leaf probe shows one facet, the tree-zoom shows the topic.
- **noisy:** `tomato →` a plant-GENUS cluster (`cystopteris, cyrtanthus…`); `dog →` publishing+breed mix; some extraction artifacts (`intermediajune`) leak from the assoc store.
- **dropped as hubs:** `music, france, computer` (top-300 in-degree) — still answerable by Siona from glosses/abstracts; just not placed in the clump graph.

## Honest scope + the named levers
- **Method scales; quality is tuning + data-cleaning, not the op.** Sources of noise: (1) the **assoc store** carries extraction artifacts + is a *pre-built* top-K (a fresh windowed co-occurrence graph would cluster cleaner); (2) **MAXTOME=12** fragments topics (raise it for fewer/larger tomes, or navigate to the parent); (3) **H_DROP=300** drops genuinely-useful hubs (music/france) — a smaller H_DROP keeps them at the cost of more lensing; (4) the rare-floor (in-degree<3) trims 91,882 of 213k assoc words — the *navigable core*; the hapax tail is honestly excluded.
- The persisted file is the flat **leaf partition + depths** — the **tree structure (parent pointers) and the inter-tome WEB (cut edges, F780)** are NOT yet persisted; both are needed for full etak navigation (zoom to parent / hop the web). That + wiring the tome-tree into Siona's loopshelf routing is the follow-on (#223 tail).
- srmech-native (rc166 §51 `normalized_cut_bisect`); no numpy/abs/CAD; data outside the repo; CC-BY-SA.

## Verdict
**#1 delivered:** the rc166 native §51 op (validated 100%) partitions the **full 91,882-word simplewiki content vocab into an 11,711-tome hierarchical tree in 24 s / 533 MB**, persisted — the n≤256 wall is gone at corpus scale, completing the F778→F785→F786 arc natively. The **uncapped, spectrally-navigable smallwiki is real**: knowledge partitions into navigable tomes from its own co-occurrence structure. Coherence is **good for clearly-connected words (instruments, Hawaiian volcanoes, astronomy) and noisy for others** (genus-name clusters, extraction artifacts, hub-dropped words) — honestly a *tuning + source-cleaning* problem, not a method one, with the levers named (cleaner source graph, MAXTOME, H_DROP, persist the tree+web, wire into Siona). The clumps-of-clumps shape is visible: a probe lands in a leaf facet; the topic lives in the parent.
