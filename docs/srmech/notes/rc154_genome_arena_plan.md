# rc154 — genome C caller-arena scratch (standalone-complete, no caps, no Python fallback)

**Why.** rc153 (PR #1084) shipped a bounds-gated genome native-dispatch: a genome
`> 16 MiB body` or `> 256 chromosomes` fell back to pure-Python. User correction
(2026-06-15), three messages: *"this is not a 1:1 Python:C mirror"* / *"never assume
target is embedded only — we write agnostic scaffolding first"* / *"there should never
be such a thing as fall back to python. if the C path is ran without python, then
what?"* See **[[feedback_c_must_be_standalone_complete_no_python_fallback]]**.

**Principle.** The C is **standalone-complete** (runs with no Python — MCU / C-only
host). So: (1) NO Python fallback; (2) NO compiled-in caps — carve scratch from the
caller `ws` arena so the bound is the caller's RAM; (3) dispatch = "native authoritative
when present" (Python validates cheap inputs → precise `ValueError`, calls C for the
heavy work + integrity → translate C bad-input → `GenomeBoundingError`; pure-Python is
the COMPLETE ALTERNATIVE only when no C at all). We are the only consumer → change the
public header freely, **no deprecated leftovers**.

**Root cause (verified).** `srmech_genome.c` caps are STATIC array dimensions baked into
the binary, NOT bound-checks against `ws`:
- `static SRMECH_THREAD_LOCAL unsigned char genome_body_scratch[16 MiB]`
- `static ... char manifest[256 KiB]` / `manbuf[256 KiB]`
- `genome_strings_t` struct-of-arrays: `cap_sha[256][65]`, `byte_offset[256]`,
  `byte_len[256]`, `label[256][256]`, `leaf_count[256]`, + `chrom_items[256]` (in
  `genome_build_data`), `labels[256][..]`/`names[256][..]` (in explode/pack)
- `static ... genome_chr_region[1 MiB]` + `genome_chr_hex[2 MiB]` + `genome_chr_io`
The caller `ws` arena currently feeds ONLY the `srmech_json` builder/parser.
`SRMECH_GENOME_MAX_CHROMS` (256) + `SRMECH_GENOME_MAX_LABEL` (256) are PUBLIC
(`srmech.h` 1999/2002) + referenced in its doc comments (2029, 2276). **Keep
`MAX_LABEL`** (a label lives inline in a `leaf_dim`-byte cap block → a format width like
`PATH_MAX`, not a count cap). **Delete** `MAX_CHROMS` + `BODY_MAX` + `MANIFEST_MAX` +
`CHR_REGION_MAX`.

---

## C edits (`docs/srmech/c/src/srmech_genome.c`)

### 1. Arena scaffolding — insert after `genome_read_region` (the agnostic scaffolding):

```c
/* Byte length of file `path` (for arena-sizing a body / manifest read).
 * SRMECH_ERR_IO on a missing / unstattable file; *size gets the length. */
static srmech_status_t genome_file_size(const char *path, size_t *size)
{
    assert(path != NULL);
    assert(size != NULL);
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) { return SRMECH_ERR_IO; }
    int sk = fseek(fp, 0L, SEEK_END);
    long n = (sk == 0) ? ftell(fp) : -1L;
    fclose(fp);
    if (sk != 0 || n < 0L) { return SRMECH_ERR_IO; }
    *size = (size_t)n;
    return SRMECH_OK;
}

/* ----- Caller-arena bump allocator — the size-AGNOSTIC scaffolding. ALL
 * genome scratch is carved from the caller `ws` arena, so the only bound is
 * the CALLER'S RAM (host large / MCU small) — never a compiled-in cap. The C
 * is standalone-complete: any genome the caller's arena fits, no Python
 * fallback. JPL Rule 3 bans malloc, not a bump-pointer over a caller buffer.
 * The srmech_json builder/parser runs on the arena's untouched TAIL. ----- */
typedef struct { unsigned char *base; size_t cap; size_t off; } genome_arena_t;

static void genome_arena_init(genome_arena_t *a, void *ws, size_t ws_len)
{
    assert(a != NULL);
    assert(ws != NULL || ws_len == 0u);
    a->base = (unsigned char *)ws; a->cap = ws_len; a->off = 0u;
}
static void *genome_arena_alloc(genome_arena_t *a, size_t n)   /* 16-aligned; NULL on overflow */
{
    assert(a != NULL);
    assert(a->off <= a->cap);
    size_t off = (a->off + 15u) & ~(size_t)15u;
    if (off > a->cap || n > a->cap - off) { return NULL; }
    void *p = a->base + off; a->off = off + n; return p;
}
static void genome_arena_tail(const genome_arena_t *a, void **ws, size_t *ws_len)
{
    assert(a != NULL);
    assert(ws != NULL && ws_len != NULL);
    size_t off = (a->off + 15u) & ~(size_t)15u;
    if (off > a->cap) { off = a->cap; }
    *ws = a->base + off; *ws_len = a->cap - off;
}
```

### 2. `genome_strings_t` → arena pointers (consumers index `s->cap_sha[i]` unchanged):

```c
    char parser_version[16 + sizeof(SRMECH_VERSION)];
    char (*cap_sha)[65];                       /* [cap_chroms] */
    uint32_t *byte_offset; uint32_t *byte_len;
    char (*label)[SRMECH_GENOME_MAX_LABEL];
    uint32_t *leaf_count;
    uint32_t cap_chroms;                       /* arena-allocated capacity */
    uint32_t n_chroms;
```

### 3. Insert `genome_count_chroms` + `genome_strings_alloc` (before `genome_scan_chroms`):

```c
static srmech_status_t genome_count_chroms(const unsigned char *body,
        size_t body_len, uint32_t leaf_dim, uint32_t *out_n)
{
    assert(out_n != NULL);
    assert(body != NULL || body_len == 0u);
    if (leaf_dim == 0u || body_len % (size_t)leaf_dim != 0u) { return SRMECH_ERR_BAD_INPUT; }
    uint32_t n = 0u;
    for (size_t off = 0u; off < body_len; off += leaf_dim) {
        if (body[off] == SRMECH_GENOME_CHROM_CAP_MARKER) {
            if (n == 0xFFFFFFFFu) { return SRMECH_ERR_OVERFLOW; }
            n++;
        }
    }
    *out_n = n; return SRMECH_OK;
}
static srmech_status_t genome_strings_alloc(genome_strings_t *s, genome_arena_t *a, uint32_t n)
{
    assert(s != NULL && a != NULL);
    assert(n != 0xFFFFFFFFu);
    s->cap_sha = genome_arena_alloc(a, (size_t)n * 65u);
    s->byte_offset = genome_arena_alloc(a, (size_t)n * sizeof(uint32_t));
    s->byte_len = genome_arena_alloc(a, (size_t)n * sizeof(uint32_t));
    s->label = genome_arena_alloc(a, (size_t)n * SRMECH_GENOME_MAX_LABEL);
    s->leaf_count = genome_arena_alloc(a, (size_t)n * sizeof(uint32_t));
    if (s->cap_sha == NULL || s->byte_offset == NULL || s->byte_len == NULL ||
        s->label == NULL || s->leaf_count == NULL) { return SRMECH_ERR_OVERFLOW; }
    s->cap_chroms = n; s->n_chroms = 0u; return SRMECH_OK;
}
```

### 4. `genome_scan_chroms` — `>= SRMECH_GENOME_MAX_CHROMS` → `>= s->cap_chroms`.

### 5. `genome_fill_strings(s, body, body_len, leaf_dim, the_one)` → add `genome_arena_t *a`:
count → `genome_strings_alloc(s, a, n)` → fill hashes (unchanged) → `genome_scan_chroms`.

### 6. `genome_build_chrom` — `assert(idx < SRMECH_GENOME_MAX_CHROMS)` → `assert(idx < s->cap_chroms)`.

### 7. `genome_build_data(b, s, leaf_dim, body_len)` → take `srmech_json_value_t **chrom_items`
param (caller-carved); drop the `chrom_items[256]` stack array; assert `n_chroms <= cap_chroms`.

### 8. `genome_build_manifest_tree(s, leaf_dim, body_len, ws, ws_len, out)`:
init a local arena over `(ws,ws_len)`, carve `chrom_items = arena_alloc(n_chroms * sizeof(ptr))`
(OVERFLOW if NULL && n>0), `genome_arena_tail` → `srmech_json_builder_init`, pass `chrom_items`
to `genome_build_data`. (`new_array` COPIES the items array — header 1921-1923 — so it may live
in the arena front.)

### 9. `genome_save`: no body scratch (body is an arg). `genome_arena_init(&a, ws, ws_len)` →
`genome_fill_strings(&strs, &a, body, ...)` → carve `manifest` buffer
`= arena_alloc(4096 + n_chroms*(MAX_LABEL+600) + 1)` (OVERFLOW if NULL) →
`genome_arena_tail` → `genome_build_manifest(..., tail_ws, tail_len, manifest, man_cap, &mlen)`.
`genome_strings_t strs;` is now stack-ok (small).

### 10. `genome_obtain_manifest`: `arena_init`. Parse path: `genome_file_size(man_path)` →
`manbuf = arena_alloc(sz+1)` → tail → `genome_parse_manifest`. Rebuild path:
`genome_file_size(body_path)` → `body = arena_alloc(bsz)` → `genome_read_file(body, bsz)` →
`genome_fill_strings(&rstrs, &a, body, ...)` → tail → `genome_build_manifest_tree`.

### 11. `genome_read_bound_body` (778) + `genome_grow_body` (800): replace `genome_body_scratch`
with `arena_alloc(genome_file_size(body))` (the read+verify path for append/remove/replace).
Each takes `(ws, ws_len)` already → init arena inside.

### 12. `.chr` export/import (`genome_chr_region`/`hex`/`io`): arena-carve sized to the region /
.chr file (`genome_file_size`). region hex = 2*region+1; io = file_size+slop.

### 13. explode/pack `labels[256][..]` / `names[256][..]`: arena-carve to n_chroms / n_files.

### 14. DELETE `#define SRMECH_GENOME_BODY_MAX / _MANIFEST_MAX / _CHR_REGION_MAX` (src) +
`SRMECH_GENOME_MAX_CHROMS` (header 1997-1999) + fix the header doc comments (2028-2029 "more
than SRMECH_GENOME_MAX_CHROMS", 2276 ".chr") + the `genome_save` ws doc (says "for the JSON
tree only" → now "for ALL scratch; size it to the genome"). Keep `SRMECH_GENOME_MAX_LABEL`.

---

## Python edits

### `_native.py`
- Drop the fixed lazy 16-MiB `_genome_ws` arena. Add `_genome_ws_for(nbytes)` that allocs a
  `(c_char * nbytes)()` sized to the call (rounded up, e.g. `max(64*1024, nbytes)`), reused/grown.
- Each `genome_*_c` wrapper computes the arena size from what it knows:
  save/append/replace: `~ 2*len(body|region) + n_chroms_est*(512) + 256*1024`;
  load/window/catalog/remove/export/import/explode/pack: size from `os.path.getsize(turns.bin)`
  (or the .chr / loose-dir total) `* 2 + slack`. Pass that arena.
- Drop `GENOME_NATIVE_BODY_MAX` / `GENOME_NATIVE_MAX_CHROMS` (no longer caps). `NativeGenomeError`
  carries `.status`; keep it but genome.py translates, not retries.

### `genome.py` — NO fallback. Per op:
```
if _native.has_native_genome():
    <Python validates the cheap inputs that produce ValueError — label exists / the_one dim>
    <single authoritative native call>
    <on NativeGenomeError(status==BAD_INPUT) → raise GenomeBoundingError; else re-raise>
    return <derive return from disk via _read_manifest/_read_chr/_hv_from_block>
# else: pure-Python is THE implementation (no native at all)
<existing pure-Python body>
```
Remove every `except _native.NativeGenomeError: pass` that falls through to pure-Python. The
`genome_pack` scratch-dir-then-adopt stays (multi-step), but on native error it RAISES (translated),
not falls back.

---

## Verification (the proof)
- `tests/test_genome_native_dispatch_rc153.py` → extend with a **>16 MiB body AND >256
  chromosomes** case: build it, save native vs forced-pure, assert `turns.bin` + `manifest.json`
  byte-identical + returns equal. This is a size the OLD C literally could not run.
- WSL2: build `libsrmech.so`, run the differential + full 129-genome suite under native.
- C smoke `test_srmech_genome.c`: add a large-genome (>256 chrom) case; pedantic `-Werror` 3-cell.
- JPL ratchet 6/6 (every new fn ≥2 asserts, ≤60 lines, no goto/malloc/multiline-macro).
- 5-SSOT bump rc153→rc154 + CHANGELOG. Ship: PR → 8 CI checks → `gh pr merge --merge` →
  tag `srmech-v0.7.5rc154` → publish → TestPyPI numpy-absent + native verify (incl. the large
  genome on the shipped wheel).

ABI stays 3 (genome C still not bound into the carrier-op ABI; `_native.py` binds via hasattr).
tools.total stays 300 (no new public callable).
