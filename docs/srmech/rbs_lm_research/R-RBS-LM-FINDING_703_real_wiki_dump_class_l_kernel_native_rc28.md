# Finding 703 — the real big-wiki encode on srmech 0.7.5rc28 (numpy-free native C path)

**Script:** `R-RBS-LM-WIKIBIGENCODE_real_wiki_dump_class_l_kernel_native_rc28.py`
**Status:** VERIFIED on real data (5k slice); full simplewiki encode in progress (srmech 0.7.5rc28)
**User direction:** *"pull latest srmech 0.7.5rc28, should have native encode all removed from numpy now also with full c
path. can we do the big wiki encode now?"*

## Yes — and it runs on real Wikipedia, on the rc28 numpy-free native path

- **srmech 0.7.5rc28 pulled + verified** (TestPyPI, clean venv outside the source tree): `native_status` →
  `has_native=True, dispatching=True, native_version=0.7.5rc28`, and **`numpy present in env? False`**. The Class-L
  eigendecomp storage signature (F172) runs in **C, with no numpy** — exactly the "native encode, numpy removed, full C
  path" the user described.
- **Real dumps are cached locally** at `~/corpora/wikipedia/` (CC BY-SA, outside the repo, attested-not-committed per
  F690): `simplewiki` (350 MB bz2) and the full `enwiki` (24 GB bz2).
- The encode streams the dump (`WikiDump`, a re-iterable bz2/`iterparse` reader — RAM-flat, re-opens per pass, clears each
  element) through the **F702-re-encoded build path** (`strip_wiki_markup_hardened` + `content_words`) → top-256 Class-L
  co-occurrence kernel → native `dense_laplacian`/`jacobi_eigvals` → content-addressed, persisted (build-once,
  query-forever, GPU-free).

## The real data surfaced new markup-leak classes — fixed (the F573 lesson, again)

The first 5k-article run **worked end-to-end** but exposed leak classes the synthetic F700/F702 tests never contained:
`ndash` (the `&ndash;` HTML entity — it was the *#1 token*), `category`/`file` residue (`thumb`, `px`), `redirect`,
`style`, `align`. So the hardened stripper was **extended** (in F690) for real-wiki markup:
- **HTML entities** (`&ndash;`/`&nbsp;`/`&#NNN;`) → stripped
- **namespace links** (`[[Category:]]`/`[[File:]]`/`[[Image:]]`/interwiki `[[xx:]]`) → dropped entirely (before the ordinary
  `[[a|b]]→b` rule)
- **`#REDIRECT`** pages → dropped
- **residual HTML attributes** (`style=`/`align=`/`colspan=`/`Npx`) → stripped
- template-before-table ordering fixed (so tables containing templates clear)
- plus an expanded English function-word **stoplist** (~130 words) so the top-256 surfaces content, not `his`/`when`/`one`.

**Re-validated on 5k real articles:** junk tokens in vocab → **NONE ✅**, top-20 now real content words, and the
associations are meaningful:

| word | top real associations |
|---|---|
| `water` | air, earth, ice, river, found |
| `government` | united, states, state, president, country |
| `language` | english, languages, official, words |
| `war` | world, ii, battle, united |
| `earth` | water, around, system, years |
| `city` | capital, york, largest, world, united |
| `science` | things, world, different, computer |

`planet`/`church` → **None** (not in top-256 → the asking-state, F661) — honest.

## Honest scale + observations (F640)

- **top-256** is the native eigvals bound (`MAX_NATIVE_NODES`). On the 5k slice that's the top-256 of ~111k content words;
  the **~111k dropped are counted + logged**, never silent. Full-vocabulary coverage is F690's documented-not-demoed
  **bucketed path** (B blocks ≤256) — the dev session builds it. This is *not* the F579/F607 wiki-formatting-language
  kernel either; it's a reference-grade cleaner that handles the dominant leak classes.
- **Timing** (5k slice, 16-core box): `build_edges_topk` 2 streaming passes ≈ 30–36 s; the **Class-L store step ≈ 49 s**
  for n=256 (`dense_laplacian` + `dense_adjacency` + `jacobi_eigvals` + `fiedler_vector` + content-address). That store
  step is **fixed cost** (independent of corpus size) but slower than expected for native C at n=256 — logged as a perf
  observation for UPSTREAM_NOTES (not a correctness issue).
- **Full simplewiki** (~all articles): in progress as a background run (~30 min at this rate); numbers appended on
  completion. **enwiki (24 GB)**: a two-pass stream is multi-hour — a deliberate background/dev-session job, not
  interactive.

**Composes:** F690/F702 (the re-encoded pipeline) · F698 (Unicode `content_words`) · F172 (eigenspectrum = storage) · F628
(build-once) · F640/F658 (grounding honesty + honest cap) · F573 (the real data caught new leaks) · F661 (asking-state on
out-of-vocab) · F630 (the dump = class-B-tertiary attested) · F579/F607 (the real cleaner target) · srmech 0.7.5rc28
(numpy-free native C). Backlinks F702 (`→ run on real wiki by F703`).

*Held open (F394). Reference scaffold; not a package edit. The dump + kernel live outside the repo (attested-not-committed).*
