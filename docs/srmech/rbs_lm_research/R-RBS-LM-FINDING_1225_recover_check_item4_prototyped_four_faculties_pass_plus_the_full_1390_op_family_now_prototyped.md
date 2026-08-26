# F1225 — `recover_check` (#1390 item 4) prototyped: the four-faculty Class-L genome-integrity op PASSES (word kernels 5/5, full genome round-trip OK, synthetic 3/3) — and with it the WHOLE #1390 op family (items 1–4) is now prototyped/filed

**User (2026-07-14):** *"prototype item 4, then update #1390."* Done — item 4 PASS; #1390 updated.

## `recover_check(vocab_size, edges, weights, charges=None)` — PASS
`R-RBS-LM-RECOVERCHECK_…py`: the packaged round-trip integrity check — a **domain-free composition** of already-shipped ops (`dense_laplacian` / `symmetric_eigendecompose` / `responsion` / `magnetic_laplacian` / `cycle_holonomy`) that verifies the FOUR faculties a stored directed Class-L genome must recover (else it was silently truncated / flattened — F1210/F1216):
- **op** — `L = D − A` builds + eigendecomposes (PSD, a ~0 null mode).
- **operand** — weighted edges present + non-degenerate + uncapped (not a top-K amputation).
- **responsion** — the propagator `e^{−zL}` is excitable (reach > 0) = the EPH read-out.
- **curvature** — the DIRECTIONAL faculty, reported honestly (not a hard gate — so a legit acyclic/coherent graph is never a false fail).

**Results:**
- **(A) real word kernels 5/5 ok** — and the curvature report is honest per-word: `cat`/`banana` **acyclic → structurally flat** (F1218, a tree has nowhere for curvature); `mississippi`/`committee` **carry nonzero holonomy** (genuine order-curvature); `order` **coherent net-zero holonomy** (F1146 — the direction nets to an integer phase around its one cycle, legitimately flat).
- **(B) full genome round-trip OK** — store a directed `committee` kernel via the item-2 codec → `genome_save` → `genome_load` → `kernel_to_graph` → `recover_check`: all four faculties survive persist (curvature nonzero recovered from disk). This is the end-to-end #231 integrity proof: the directed Laplacian round-trips a real content-addressed genome with its curvature intact.
- **(C) synthetic 3/3** — directed cyclic (single non-cancelling charge → nonzero holonomy), symmetric bag (charges 0 → metric faculties PASS, **flagged directionless**, F1210), amputated operand (empty weights → **honest FAIL**, `ok=False`).

**Verdict `ok = op and operand and responsion`** (integrity); curvature is a reported diagnostic with a `directed` flag a caller storing the directed Laplacian can assert on.

## Measured gotcha worth documenting (curvature caveat)
`cycle_holonomy` treats `charges` as a **phase (turns)** → **INTEGER edge_charge aliases to 0 mod 1** (a cycle whose charge-sum is an integer reports holonomy 0). So any curvature read over an integer-charged directed store must **phase-scale** first (the prototype uses `q = 1/(2·max|charge|+1)` to expose it). This is exactly why `[1,1,−1]` around a triangle looked flat (sum = 3 → 0 mod 1) while a lone `[1,0,0]` does not. Filed as a caveat on #1390 (relevant to items 1 + 4); worth a one-line doc note upstream so callers don't read a directed store as flat.

## #1390 — the whole op family is now prototyped/filed
| item | op | status |
|---|---|---|
| 1 | `cooccurrence_edges(directed=True)` | filed (UPSTREAM §, F1210) — ready to escalate |
| 2 | `graph_to_kernel` / `kernel_to_graph` | **prototyped 8/8** (F1223) |
| 3 | `eulerian_path` / `eulerian_circuit` | **prototyped 11/11 + 6/6** (F1224) |
| 4 | `recover_check` | **prototyped 5/5 + round-trip + 3/3** (this finding) |
| 5 | `klein4_permute` | withdrawn — `klein4_phase_bind` covers it (F1223) |

Every live op now has a working, behavior-exact prototype with a drafted signature — the maintainer has a complete, verified reference implementation to port (each with the C-mirror follow-through). Proposed signature: `recover_check(vocab_size, edges, weights, charges=None) -> {ok, op, operand, responsion, curvature:{directed,n_cycles,holonomy_nonzero,verdict}, diagnostics}`, under `srmech.amsc.laplacian`.

Composes **F1224** (item 3; the directed kernels + genome codec it round-trips), **F1223** (item 2 codec + the klein4 review), **F1210** (the recover-ratchet tier + magnetic Laplacian; the F1210 flat-bag flag), **F1216** (L-store integrity), **F1218** (acyclic = structurally flat), **F1146** (coherent net-zero re-flattens), **F1222** (the op family → #1390), #231/PKG-3, [[feedback_computational_provenance_discipline]] (prototype committed + measured), [[feedback_read_independent_structure_check_first]] (the four faculties ARE the intrinsic structural check on a stored genome).
