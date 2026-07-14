# F1224 — `word_to_kernel` now keeps self-loops (double letters round-trip: 5/8→8/8); and `eulerian_path`/`eulerian_circuit` (#1390 item 3) prototyped — a node-agnostic Hierholzer that reproduces `eulerian_word` 11/11 and HONESTLY refuses degree-infeasible / disconnected graphs (6/6)

**User (2026-07-14):** *"fix word_to_kernel to keep self-loops, then prototype item 3."* Both done, both PASS.

## The self-loop fix (double letters now round-trip)
`word_to_kernel` had `if u == v: continue` — it **dropped self-adjacencies**, so a consecutive repeated glyph (`ss`/`pp`/`tt`/`ee`) was lost before serialization (mississippi→misisipi). Fix: record a self-loop as a **forward-in-time, direction-neutral** edge (`fwd[(u,u)] += 1`), so metric = count and charge = count → the eulerian `(w±c)//2` split gives `f=count, r=0` (exact). Effect (GRAPH2KERNEL word-reconstruct): **5/8 → 8/8** — `reappear`/`committee` now EXACT; `mississippi`→`misssisippi` (the `ss`/`pp` doubles restored; the residual order difference is genuine **F1079** Euler-path ambiguity, not loss — the glyph multiset is now correct). **No regression:** NIVDIRECTED's own ratchet unchanged (direction 11/11, metric 11/11, genome 11/11, Eulerian 10/11 — its word list has no consecutive doubles); the codec struct/persist stay 8/8 (a self-loop is just an edge with `i==j`).

## Item 3 — `eulerian_path` / `eulerian_circuit` prototyped (PASS)
`R-RBS-LM-EULERWALK_…py`: the Hierholzer walk-reconstruction srmech lacks (it ships `magnetic_`/`signed_laplacian` but **no Eulerian primitive**), abstracted out of NIVDIRECTED's domain-bound `eulerian_word` into a clean, **node-type-agnostic** graph op.
- **(A) Equivalence — 11/11:** `eulerian_path(directed_edges(k), start=k["start"])` reproduces `eulerian_word(k)` **exactly** on every real directed word kernel (cat, listen, level, banana, sandroing, vanuatu, mississippi, reappear, committee, order, ocean) — same Hierholzer, same start logic, now node-agnostic.
- **(B) Synthetic — 6/6:** triangle **circuit** `[0,1,2,0]`, simple **path** `[0,1,2,3]`, **self-loop** `[0,1,0,0]`, **figure-eight** `[0,2,0,1,0]` all walk correctly; the **degree-infeasible** `[(0,1),(0,2)]` (node 0 out−in=+2) and the **disconnected** `[(0,1),(2,3)]` both **honestly return `None`** — feasibility is CHECKED (degree balance + full-edge-consumption connectivity), never a partial/lying walk.
- **Proposed signatures (for #1390 item 3, under `srmech.amsc.laplacian`):**
  - `eulerian_path(edges, start=None) -> [node,...] (len=|edges|+1)  or None`
  - `eulerian_circuit(edges, start=None) -> [node,...] (start==end)   or None`
  - `edges`: a directed multiset `[(u,v),...]` (repeats ok; nodes any hashable; self-loops ok). Deterministic start (min out>in node for a path; min out-bearing node for a circuit). O(|E|).
- The `(w±c)//2` **magnetic-Laplacian edge recovery** that feeds it (signed graph → directed multiset) is item-1's exact inverse — domain-agnostic; it belongs beside `magnetic_laplacian`.

## #1390 status after this pass
- **item 2** (`graph_to_kernel`/`kernel_to_graph`) — prototyped 8/8 (F1223).
- **item 3** (`eulerian_path`/`eulerian_circuit`) — prototyped 11/11 + 6/6 (this finding).
- **item 1** (directed cooccurrence) — filed, ready to escalate.
- **item 4** (recover-check) — not yet prototyped.
- **item 5** (klein4_permute) — WITHDRAWN (phase_bind covers it, F1223).
Two of the four remaining ops now have working, byte/behavior-exact prototypes with drafted signatures + a C-mirror follow-through.

Composes **F1223** (item 2 codec + the klein4 review), **F1213/F1080** (the directed word kernel + sandroing = the Eulerian circuit), **F1079** (commensurate/incommensurate closability — the residual mississippi order ambiguity), **F1210** (magnetic Laplacian; the `(w±c)//2` edge recovery), **F1222** (the op family → #1390), #231/PKG-3, [[feedback_computational_provenance_discipline]] (both prototypes committed + measured).
