# F830 — VERIFIED (against the shipped srmech==0.7.5rc173 wheel, clean venv): the srmech dev's verdict holds — the four remaining open UPSTREAM asks (§39 class-generator, §50 streaming Klein-4 accumulate, §51 sparse Fiedler #1097, §52 low-RAM encode) are ALL delivered, present + callable + native-where-spec'd. So the entire open upstream scaffolding queue is DRAINED — and combined with the already-landed genome file-management (§41–45, F829), native klein4 (§53), native triality (F826), and `klein4_unbundle` (§54), EVERY srmech capability siona depends on is live on rc173. The srmech v0.7.5 graduation gate — "no more upstream scaffolding requests of srmech" — is MET; it is now verify-and-cut.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc173 (TestPyPI; verified in a fresh venv, not from notes) · **Provenance:** present+callable+native-flag checks on the rc173 wheel · **Composes:** F828/F829 (the dep + graduation thread), [[project_siona_package_takeover_unmirror]], UPSTREAM §39/§50/§51/§52 (now marked LANDED) · **User direction (2026-06-17):** "I asked srmech dev to check these issues and says they are already delivered … all four items are already delivered to srmech — live on the shipped rc173 wheel. please check."

## Verified against ground truth (rc173 wheel)
| § | shipped surface | functional check | native |
|---|---|---|---|
| §39 class generator | `dsl.generate_class_descriptor(name, *, fields, methods, doc, kind) -> str` | returns a 358-char TOML | Python (spec: no new primitive class) — rc49 |
| §50 streaming accumulate | `hdc.klein4_bundle_accumulate`/`klein4_bundle_resolve` + `hdc.cooccurrence_fold` | accumulate→resolve OK (len 64) | `has_native_klein4_fold()`=**True** — rc155+rc165 |
| §51 sparse Fiedler (#1097) | `laplacian.fiedler_sparse` + `normalized_cut_bisect(n,edges,weights)` | 2-triangles+bridge → clean `{0,1,2}\|{3,4,5}` | `has_native_fiedler_sparse()`=**True** — rc166 |
| §52 low-RAM encode | `text.cooccurrence_topk(docs,*,window,k,…)` + `laplacian.recursive_cut(…, max_tome, work_dir)` + `fiedler_sparse_file` | topk → 5 nodes; recursive_cut pages out-of-core tome `.bin` files | `has_native_fiedler_sparse_file()`=**True** — rc167+rc168/169 |

(`recursive_cut` returned 1 tome for the 6-node graph — correct: 6 < `max_tome=256`, so no cut; it pages to disk only when a tome exceeds the cap.)

## Conclusion — the 0.7.5 graduation gate is MET
The open upstream scaffolding queue is **drained**. There are no remaining open ASKs of srmech: §39/50/51/52 delivered (this finding); §41/43/44/45 genome file-management delivered (F829, `srmech.amsc.genome`); §53 native klein4 (F823); native `klein4_triality_cycle` (F826); §54 `klein4_unbundle` (rc173). **Everything siona — and any downstream package — needs from srmech is live on the rc173 wheel.** So graduating **srmech v0.7.5** is now a verify-and-cut: clean-verify the wheel in a fresh venv (native dispatching, the four version-SSOT files agree), then cut the clean `srmech-v0.7.5` tag → production PyPI (the maintainer's human gate).

## What it unblocks (the downstream chain)
Once srmech v0.7.5 is on production PyPI, the siona package floor rises to `srmech>=0.7.5` and these become production-shippable in one go:
- **PKG-3** — native-genome recall (`srmech.amsc.genome` to package the full-body instrument, no loose NDJSON+index, F829).
- **EC-recall** — the rc171-native `klein4_triality_cycle` 2-of-3 over the de Bruijn non-unique tail (F826, PKG-2).
- the **C-native de Bruijn** accelerator (F824) as its own platform-wheel tier.

## Honest scope
- Verified present + callable + native-flag-True; the dev's "shipped-in rcN" attributions are taken on report (the rc173 wheel is the ground truth, and all four are IN it).
- Marked §39/50/51/52 **✅ LANDED** in UPSTREAM_NOTES (with the rc173 verification). I did NOT close GH #1097 — the maintainer closes the issue ([[feedback_create_upstream_issues_never_close_them]]).

## Verdict
The dev is right — all four are delivered + live + (where spec'd) native on rc173. The upstream scaffolding queue is empty; srmech v0.7.5 is ready to graduate (verify-and-cut). That graduation is the single gate that unblocks native-genome siona recall, the EC-recall, and the C-native de Bruijn — the user's gated tag/publish.
