# F1232 — #1390 DELIVERED NATIVE in srmech v0.9.0rc253: the whole directed-genome-storage op family (items 1–4 + the structural/spectral split + the octonion order faculty) landed, verified 7/7 behaving as our prototypes. #231 is now a native consumer.

**User (2026-07-15):** *"pull latest srmech from TestPyPI. slight snafu — the srmech agent ignored all the additional comments from #1390, so we yanked some rcN and redid; small rc gap now. #1390 delivered in rc253."* Pulled rc241→**rc253**, verified.

## The delivery (verified in a clean venv outside the source tree)
srmech **0.9.0rc253**, `HAS_NATIVE=True`, **ABI 3→5** (new C symbols — full C/Python parity delivered, not just Python). The version list confirms the snafu: rc242 then a **gap (rc243–247 yanked)**, resuming rc248→rc253 — the redo that picked up the review comments the first pass ignored.

**All of #1390 is native, and the signatures match our prototypes near-exactly:**
| # | delivered op (rc253) | our prototype | verified |
|---|---|---|---|
| 1 | `text.cooccurrence_edges(…, directed=False)` → 3- or 4-tuple `(n,edges,metric,charge)` | F1226 (`R-RBS-LM-DIRCOOCCUR`) — **identical** | metric == undirected weights (superset), charge nonzero ✓ |
| 2 | `genome.graph_to_kernel(vocab_size, edges, weights, charges=None, *, node_ids=None, extras=(), leaf_dim, label, the_one)` + `kernel_to_graph(chroms, the_one, n_syms)` | F1223 (`R-RBS-LM-GRAPH2KERNEL`) — **identical signature** | round-trip byte-exact ✓ |
| 3 | `laplacian.eulerian_path(edges, start=None)` + `eulerian_circuit(edges, start=None)` | F1224 (`R-RBS-LM-EULERWALK`) — **identical** | path/circuit + honest `None` on disconnected ✓ |
| 4 | `laplacian.recover_check(…)` **+ `recover_check_structural(…, cycle_sample=48)` + `recover_check_spectral(…, max_dim=256)`** | F1225 + the **#231 scale-split** I flagged from F1227 | all three run ✓ — **the comment-driven split landed** |
| 5 | `laplacian.order_fingerprint(fiber_ids)` + `recover_check_order(true_fingerprint, recovered_fiber_ids)` | F1231 (`R-RBS-LM-OCTRECOVER`) — the octonion order faculty | catches the figure-eight reorder the ℂ-grade is blind to ✓ — **and their internal octonion generator is non-degenerate** (my F1231 generic-not-uniform note held) |

**7/7 native ops behave as prototyped** (smoke committed). The two additions that came from my #1390 *comments* — the `recover_check_structural`/`_spectral` scale-split (from #231's dense-eigendecompose wall, F1227) and the octonion `order_fingerprint`/`recover_check_order` faculty (F1230/F1231) — are both present, i.e. the redo (rc248→253) consumed the comment thread the first attempt (yanked rc243–247) had ignored.

## Consequence
- **#231/PKG-3 is now a real native consumer** — `R-RBS-LM-SIONA231` can drop its five prototype-imports (`R-RBS-LM-{DIRCOOCCUR,GRAPH2KERNEL,EULERWALK,RECOVERCHECK,OCTRECOVER}`) and route straight through `srmech.amsc.{text,genome,laplacian}`. The store spine is now stdlib-of-srmech, not local scaffolding.
- The five prototype scripts become the **attestation record** of what was specified + delivered (like the research-triality artifacts) — kept for provenance, no longer the engine.
- The octonion Laplacian resolved exactly as scoped (F1230): a **verifier faculty** (`order_fingerprint`/`recover_check_order`), NOT a storage-codec change. Items 1–2 unaffected, as intended.

## Next
Re-point `R-RBS-LM-SIONA231` to the native ops + re-run (a drop-in swap; the 7/7 smoke says behavior is identical) → then the real simplewiki genome build (stream the 916 MB kernel → genome, now with `recover_check_spectral(max_dim=…)` for the bounded spectral faculty) and the Siona read-path wiring (F1219).

Composes **F1222–F1231** (the whole op-family arc — filed, prototyped, escalated, scale-learned, octonion-scoped — now all delivered), **F1227** (the scale-split that became `recover_check_structural`/`_spectral`), **F1230/F1231** (the octonion faculty that became `order_fingerprint`/`recover_check_order`), #231/PKG-3 (unblocked, native), [[feedback_always_rc_first_for_downstream_publishes]] (rc253 on TestPyPI; the yank/redo is the rc-gate working), [[feedback_introspect_srmech_before_python_dispatch]] (re-introspected each rc; verified the delivery).
