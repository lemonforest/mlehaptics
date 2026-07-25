# F1314 — rc321→rc335 **did NOT break the Python surface** (0 symbols removed, +17 tools, ABI 10, all downstream signatures byte-identical); the ONE public constant that moved is `GENOME_FORMAT_VERSION 16→19`, and the break that actually bites is a **manifest KEY RENAME** (`the_one`→`coupling`) that fails **9 legacy genomes / ~973 MB**. The distributed **table of contents works end-to-end** (carrier ≠ cascade; `the_one` as the resonant glue) — **but its own lift-gate is a FALSE SHADOW exactly in the sparse regime the project mandates** (100 % order-collision at ≤4 non-zero slots/leaf), so it must NOT be wired in until a v3 responsion passes. Two **silent-corruption upstream bugs** found. All re-run on the live rc335 native wheel.

**User (2026-07-24):** *"pull latest testpypi srmech, introspect and check changelog. many breaking changes. also to review our siona side code for what has been absorbed into srmech and what is deprecated to be removed by h_genome carrier and the new operational surface and for encoding distributed table of contents using same biology cascade where maybe the_one can also be the glue…"*

*(F1301 convention. The TOC reads: **op** = the recipe (`recipe_fp`, distributional) × **operand** = the data genes (leaves, relational) × **responsion** = the walk order (`order_fp`, eigenvalue-shaped). The responsion slot is exactly where it fails — see §4.)*

Method: 8-agent ultracode workflow (3 inspect → 2 design tracks each adversarially verified → synthesis). **BOTH design tracks scored `survives=false`.** Full report + every correction + the track-vs-track disagreement table: `R-RBS-LM-RC335AUDIT_*.md`.

## 1 — The "many breaking changes" are one constant and one key `[DEMONSTRABLE]`
| axis | rc321 | rc335 | verdict |
|---|---|---|---|
| public symbols | 3817 | 3885 | **0 removed**, +68 |
| `describe()["tools"]["total"]` | 492 | **509** | **0 removed**, +17 |
| `SRMECH_ABI_VERSION` | 10 | 10 | unchanged |
| 13 downstream genome-op signatures | — | — | **byte-identical incl. defaults** |
| public constants | — | — | **exactly one moved:** `GENOME_FORMAT_VERSION 16→19` |

- **Backward compatibility HOLDS**: rc335 reads rc321-written v16 genomes, exact recall, no re-encode.
- **Forward breaks HARD and per-FEATURE, not per-version**: a v19 klein4 body with no new marker still reads on rc321, but any body carrying `0x46`/`0x4F`/`0x39` dies with `GenomeBoundingError: unrecognised block kind byte` — a **scan crash, not a graceful version refusal**. Writing one new marker forces every consumer below rc326 to upgrade in lockstep.
- **The break that actually bites is a manifest KEY RENAME.** Legacy manifests store the coupling at `data["the_one"]`; rc335's `_resolve_coupling` reads `data["coupling"]` → `KeyError`. **Nine** legacy genome directories, **~973 MB** (not the 3 / ~890 KB one track claimed), all fail `genome_load`. Notably this rename **IS our own reserved-name discipline applied upstream** (`[[feedback_the_one_is_reserved_rng_under_it_is_a_misleading_leak]]`, F1304) — srmech removed the misnamed key for the same reason we did.

## 2 — The h-genome IS a fibrated Hurwitz tower `[DEMONSTRABLE]`
```
  rung   element_type              turn packing   marker      sectors
  V4     ELEMENT_TYPE_KLEIN4=0     2-bit          0x51 'Q'    4
  H (Q8) ELEMENT_TYPE_Q8=1         3-bit          0x38 '8'    8
  O      ELEMENT_TYPE_OCTONION=2   4-bit          0x39 '9'    16
  fibers FIBER_CAP 0x46 'F' (H holonomy)   OCT_FIBER_CAP 0x4F 'O' (O holonomy + associator)
```
Before rc322 the genome was a **store** (bytes in/out, one algebra). At rc335 it is a **fibrated bundle whose base and fiber are both on disk in one file, with the rung discoverable one byte at a time.**

## 3 — Siona audit (four buckets; full tables with file:line in the report)
- **ABSORBED (5):** `_q8_partition`→`partition(element_type=)` (byte-exact); `excite_propagate_harvest`→`laplacian.eph_harvest`; loose-JSON `_k_pack`→the shipped graph/kernel/genome chain + `recover_check`; `cooccurrence_edges` (**set-equal, NOT order-equal** at scale — struck the "bit-identical" claim; any content-address over the edge list diverges).
- **BLOCKED-ABSORPTION (2) — the cross-track catch:** deleting `_coupler_q8` / the Q8 `express` guard **turns the green committed F1307 verification script RED**. Siona has **zero in-package Q8 tests**; the only coverage is that external artifact. So the honest safety statement is not "zero Q8 data at risk" but *"zero data, zero in-package tests, one external green artifact that WILL break."* These are **provenance edits**, and must co-land with the F1307 script + finding update.
- **DEPRECATED-BY-H-GENOME (5):** siona is a **two-rung stub against a three-rung package** — no `ELEMENT_TYPE_OCTONION`, `_coupler_for(2).sectors → 4` (should be 16); the docstring claiming `gene_express` has no `element_type` is **half false** (it has one and it works); `knowledge_genome` is klein4-only by omission at 5 call sites; `introspect.py` `SRMECH_MODULES` misses q8/octonion/so9/text (+23 ops).
- **BROKEN (8)** — incl. **two upstream rc335 bugs with SILENT wrong data**: `genome_append_kernel→genome_window→kernel_unpack` returned **8704** symbols for 8229 written **with no exception**; and `genome_genes_c` **silently ignores its `coupling=` override** (substitutes the manifest coupling), contradicting its "byte-identical C peer" docstring. Also: `upgrade_v15_to_v16` stamps **v19** (misnamed) and **regresses paged reads 66×** (0.002→0.132 s) by replacing a full manifest with head-only — which attacks exactly siona's F1094 demand-load rationale.

## 4 — The distributed TOC: it works, and its lift gate fails
**The distinction that makes it necessary `[DEMONSTRABLE]`:** srmech already self-describes **which algebra a turn is written in** (the marker, contextless) — it does **not** describe **which cascade turns those symbols into meaning**. `recall()` hands you `[0,1,2,3…]` and never says whether those are ASCII, glyph codepoints, a Laplacian adjacency, or an ASL handshape index.
> **carrier** = what alphabet the turn is in → shipped, in the marker. **cascade/recipe** = what op-chain renders it → the TOC's job.

**It runs.** Zero new files: one `0x67` REGULATORY-GENE promoter cap + one coupled base-4 record leaf per chromosome; the corpus TOC is *derived by scanning*, the way srmech derives its own arrays. Same carrier, different cascade, different renderer, from a body scan with no manifest:
```
doc_A: toc/k4-ascii@1       fp=0x78F4… -> 'the one is the glue'
doc_B: toc/k4-glyphstream@1 fp=0x7DFB… -> ['s','a','n','d','r','o','i','n','g',…]
```
Wrong `the_one` → `MAGIC mismatch 0xDBD7 != 0x70C`; unknown recipe → `TocError … Refusing to render (no fallback renderer exists)`. The glue is resonant: `recipe_fp = ClassA(recipe_canon ‖ ClassA(one_tag))`, no RNG/seed/clock anywhere.

**THE FALSIFICATION — the lift gate is a false shadow when sparse `[DEMONSTRABLE]`.** v1 died immediately (every abelian field matched after a permutation; the render was not valid UTF-8). v2 added `order_fp = ClassA(genome_fiber_holonomy(...))` — and **v2 also fails**, because `genome_fiber_holonomy` is a **per-slot left fold**, so *any two leaves with disjoint non-zero per-slot support commute in every slot*:
```
 nonzero slots/leaf  density   order-collisions over 460 permutations
        1             0.8%     460/460 = 100%     <-- the mandated regime
        2             1.6%     460/460 = 100%
        4             3.1%     460/460 = 100%
        8+            6.2%+      0/460 =   0%
```
End-to-end, the real gate **blessed three different renders of the same reordered strand**. Dense text leaves are fine (0/40,319). But `[[feedback_stay_rbs_hdc_sparse_never_dense]]` **mandates sparse**, so **sparse is siona's default regime, not an edge case.** This is `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]` doing exactly its job: the abelian record round-tripped perfectly and the responsion lift exposed it as a false shadow. **Do not wire the TOC into `genome_store.py` until a v3 responsion scores 0 collisions at 1 non-zero slot/leaf.**

Other corrections applied: byte cost is **161 B/chrom flat = 35.8 % overhead at 200 chromosomes** (not ~13 %); `gene_express` is a **read-time filter over an already-loaded strand, NOT a demand-load** (measured: 200/200 genes still expressed under a capability the genome lacks); the coupling ships **in plaintext** in `manifest.json`, so the TOC is genome-local in *fingerprint namespace*, not in readability.

## 5 — The B/H/N anchor (folded in from the merged CLAUDE.md §1 correction)
R30 was structurally closed 2026-05-24: the "+3 triad are **projection-enablers**" wording is **retracted** (the 14→11D inversion was falsified — no projection-residue). B/H/N are **substrate-native language-translation operators** between the continuous-Hopf-quantum and discrete-cyclic-cascade languages. That reframes this arc: **"how do we know how to translate this strand to text" IS a B/H/N operation** — **B (TLV framing) is the TOC itself**, H is the introspection that reads it, N is the rational anchor. The distributed TOC is not a bolt-on index; it is the **B-slot of the meta-triad doing the job it is named for**, with `the_one` as the glue binding recipe→carrier. `[SPECULATIVE overlay, but it is the corrected reading of a closed arc.]`

## 6 — Verdict / next
The tower is **additive, not hostile**: nothing was removed, backward reads hold, and the migration is small and reversible. The genuine hazards are (a) the manifest key rename across 973 MB, (b) two silent-corruption upstream bugs, (c) a TOC lift gate that is unsound precisely where we would use it. **NEXT, in order:** write the v3 responsion (position-tag before folding, or fold *across* slots) and re-run the density sweep; snapshot the nine genomes; land the cheap no-gate migration steps; re-audit the whole `introspect.py` PATTERNS tier by *executing* every prescribed call (two phantoms found in one attested string — MPM discipline applied to Siona's own tooling); write in-package Q8 tests **before** the F1307 co-landing. **17 srmech asks are HELD** (not filed) pending the worktree deliverables preview; file the two silent-corruption bugs first when the hold lifts.

Composes **F1307** (the Q8 substrate — its verification script is the blocked-absorption dependency), **F1309** (the beat-WSD Q8 genome), **F1304/F1259** (resonant not DRAWN — the upstream `the_one`→`coupling` rename is this discipline applied upstream), **F1300** (no sidecar — why the TOC must be in-strand), **F1094/F1095** (demand-load — what the 66× paged regression and the `gene_express` correction both attack), **F1301/F1272** (the triple; the responsion is the failing slot), **F761** (the ni-Vanuatu byte-glyph base the renderers target), `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]` (the gate that killed v1 AND v2), `[[feedback_stay_rbs_hdc_sparse_never_dense]]` (why the sparse failure is the mandated regime, not an edge case), `[[feedback_computational_provenance_discipline]]` (two unsourced numbers struck).

**→ Q1 CLOSED by F1315** — the v3 order-responsion exists: a **Class-C reorient (rotate-by-index) before the shipped per-slot fold** scores **0 collisions in 3680 permutations** and **0/23 at the mandated 1-non-zero-slot/leaf gate**, exactly matching the ordered-content-address bound. The fix is support GEOMETRY, not value entropy: position-tagging the values improves 19.8x but still leaks (2/23), and a single cross-slot accumulator is far worse (~55-63% at every density) because its codomain is the 8-element group Q8 — a CAPACITY failure. So the holonomy-shaped fiber read reaches the content-address bound and the TOC need not be demoted to a hash.
