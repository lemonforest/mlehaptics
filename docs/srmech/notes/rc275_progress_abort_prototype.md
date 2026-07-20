# rc275 (§101) — progress + graceful abort for long encodes — BUILD-READY prototype

**Status:** design + prototype note (NOT the build). No version bump / branch / PR here.
**Scope (PR#687 UPSTREAM §101, commit 66de7c5f):** give the long, currently-BLIND,
un-cancellable srmech encode ops a caller **progress callback** — heartbeat + exact
%-in/out + **nonzero-return-to-cancel** (the libcurl `XFERINFOFUNCTION` / SQLite
`progress_handler` / libgit2 `transfer_progress` pattern), called INLINE (zero
concurrency), working on C / Python(ctypes) / microcontroller hosts, via a **versioned
struct** so the ABI extends cleanly. NOT a task registry (threads/RTOS; breaks
bare-C/MCU + JPL determinism). The same primitive doubles as graceful abort: a nonzero
return aborts and returns a CLEAN partial/decline, never a crash.

---

## 0. TL;DR (the exec summary a build subagent needs first)

1. **The existing `srmech_progress_cb_t` (rc242 / #840) is NOT reusable as-is and NOT
   extendable in place.** It is `void (*)(const char *event_json, void *user_data)`,
   process-global (`srmech_set_progress_cb`), fired **once per dispatched tool** from
   `iv_dispatch`. Three disqualifiers for §101: (a) **void return → no cancel channel**;
   (b) **per-tool-dispatch granularity** (one `genome_from_graph` is ONE dispatch, so it
   would fire once, at the end — useless as a heartbeat); (c) **process-global single
   slot** (two concurrent encodes clash; doesn't match a per-call `progress=`). It also
   has **no struct, no `cbSize`, no done/total** — there is nothing to `cbSize`-extend.
2. **Decision: introduce a NEW, ADDITIVE per-call primitive** — a versioned event struct
   `srmech_progress_ev_t` (first field `struct_size` = the `cbSize`/statx/Vulkan gate,
   with a `phase` enum from day one) passed by const-pointer to a **new** callback typedef
   `srmech_progress_tick_cb_t` returning **`int` (0 = continue, nonzero = cancel)**, plus
   `void *user_data`. The rc242 observer stays **untouched and orthogonal** (this is
   exactly how libcurl/SQLite/libgit2 keep the progress handler distinct from the
   trace/verbose observer). "Reuse" is honored at the **design-DNA** level (opaque
   `user_data`, NULL-gated off-by-default, the #840 CFUNCTYPE ABI-bump discipline), not by
   overloading the observer symbol.
3. **Cancel-return shape (derived from the `telomere_tick` honest-decline):** a nonzero
   tick makes the op unwind via its normal early-return path having written **only
   COMPLETE units**. C returns a new **`SRMECH_CANCELLED = 7`** status (a clean decline,
   NOT an error) with the out-count set to the complete-so-far units. Python **dict-returning**
   ops (`recursive_cut`, `genome_partition`, `genome_from_graph`) gain a `"status"` key
   (`"ok"` default / `"cancelled"`) + a valid **partial** payload; **bare-strand-returning**
   ops (`mint`/`genome()`, `mint_strand`) return the valid **partial / unmodified** strand
   (the caller owns the callable, so it already KNOWS it cancelled — same reason
   libcurl returns `CURLE_ABORTED_BY_CALLBACK` and the app just knows). Never a
   half-written strand.
4. **Encode ops + hook points:** `recursive_cut` (Python `while pending`, per-bisection),
   `genome_partition` (forwards recursive_cut + per-edge participation), `genome_from_graph`
   (partition phase → per-group mint loop → save phase), `mint`/`genome()` (per-kernel),
   `mint_strand` (pre-splice check). The one heavy **C** loop is `fiedler_file_iterate`
   inside `srmech_laplacian_fiedler_sparse_file` — hooked via an additive
   `..._progress` overload symbol.
5. **Riskiest part:** the ctypes **CFUNCTYPE trampoline** for the native fiedler
   `_progress` overload — a Python exception raised inside the user callable must **never**
   cross the C frames (UB/crash). The trampoline catches everything, stashes it, returns
   `1` (cancel) to unwind C cleanly, and re-raises on the Python side after the call
   returns. This is the C-side analog of the rc273 macOS-red Callable lesson and is the
   likeliest thing to turn CI red.
6. **ABI:** the new callback typedef bumps **`SRMECH_ABI_VERSION` 5 → 6** (the #840 /
   v2→v3→v4→v5 callback-typedef precedent: a new callback typedef carries a CFUNCTYPE
   wire implication for the ctypes shim). Ripple `EXPECTED_ABI_VERSION` in `_native.py`
   in lockstep + the 5 version-SSOT files. **Later** struct growth via `cbSize` does NOT
   bump ABI — that is the whole point of the versioned struct.
7. **Registry ripple is CHEAP and the Callable-not-a-wire-param rule is why:** `progress=`
   is a Python-only kwarg → it MUST NOT appear in any `ToolEntry.parameters` (a `Callable`
   has no coercer; `test_all_param_types_json_coercible` would reject it — the rc273
   macOS-red mechanism). No new public callable, no new `P()` row, no
   `describe()["tools"]["total"]` change, no carrier_registry / Rosetta ripple. Only the
   ToolEntry **summaries** document the in-process affordance (+ the C symbol/ABI ripple).

**Note path:** `docs/srmech/notes/rc275_progress_abort_prototype.md` (this file).

---

## 1. Ground truth (introspection results — read before asserting)

### 1.1 The existing rc242 progress primitive (`#840`, ABI v5)

`docs/srmech/c/include/srmech.h` (≈L4614-4660) + `docs/srmech/c/src/srmech_progress.c`:

```c
/* rc242 / #840 — the DISPATCH-OBSERVER. NOT a heartbeat, NOT cancellable. */
typedef void (*srmech_progress_cb_t)(const char *event_json, void *user_data);
srmech_progress_cb_t srmech_set_progress_cb(srmech_progress_cb_t cb, void *user_data);
```

- **Return type `void`** → there is no path for the callee to signal "cancel" back to the
  library. The `int`-return-to-cancel that §101 REQUIRES cannot be retrofitted onto this
  typedef without changing an exported typedef's wire format (breaks the live observer
  binding). Confirmed by `srmech_progress.c:102` — `cb(out, g_progress_userdata);` (result
  discarded).
- **Process-global slot** — `srmech_progress.c:48` `static srmech_progress_cb_t
  g_progress_cb`. One observer per process; set before spinning threads.
- **Per-tool-dispatch granularity** — fired from `iv_dispatch` via
  `srmech_progress_emit_dispatch` once per successfully-dispatched tool with a canonical-JSON
  op event `{"category","mpr_version","op_name"}`. It is a **Class-H introspection**
  projection to bare-C, not a per-iteration progress meter.
- **No struct / no `cbSize` / no done/total.** The task's mental model of "an existing
  versioned struct with a progress fraction" does not exist. There is nothing to
  `cbSize`-extend; the versioned struct is CREATED fresh in rc275.

Conclusion: **new additive primitive**, observer untouched. (Falsification: anyone insisting
on literal reuse must explain how a `void` return cancels — it cannot.)

### 1.2 Current status enum (`srmech.h:139-146`) — no cancel code yet

```c
typedef enum srmech_status {
    SRMECH_OK=0, SRMECH_ERR_NULL_ARG=1, SRMECH_ERR_BAD_INPUT=2, SRMECH_ERR_IO=3,
    SRMECH_ERR_OVERFLOW=4, SRMECH_ERR_NOT_IMPL=5, SRMECH_ERR_INTERNAL=6
} srmech_status_t;
```
rc275 appends **`SRMECH_CANCELLED = 7`** (a clean decline, semantically distinct from the
errors — the C mirror of `telomere_tick`'s `TELOMERE_SENESCENT`). Appending an enum value is
additive (does not change any existing function's wire format on its own).

### 1.3 The honest-decline pattern to mirror (`genome.py telomere_tick`, L4634-4702)

`telomere_tick` returns a **status dict** and never crashes: `count>0 → {"status":
"divided", …, "daughter": <strand>}`; `count==0 → {"status": "senescent", …, "daughter":
None}`. `integrate` (L3718) likewise validates then returns a well-formed strand or raises a
`ValueError` on malformed input (not mid-op). rc275's cancel path reproduces this: **a
distinct status + a well-formed (partial) result**.

### 1.4 The encode paths + their natural heartbeat/cancel points

| Op (Python) | File / loop | Natural tick point | Exact total | C hot loop |
|---|---|---|---|---|
| `recursive_cut` | `laplacian.py:5978` `while pending:` | per popped sub-graph (per bisection) | `n` nodes (resolved = Σ finalized tome sizes) | — (Python driver; calls fiedler C per bisection) |
| `fiedler_sparse_file` | `laplacian.py:5768` → C | per power-iteration | `max_iters` | **`fiedler_file_iterate`** `srmech_laplacian.c:1642` `for(it<max_iters)` |
| `genome_partition` | `genome.py:4367` | forwards recursive_cut; then `_partition_participation` per-edge (`4457`), classify per-node (`4463`) | `n`, `n_edges`, `n` | (via recursive_cut/fiedler) |
| `genome_from_graph` | `genome.py:4544` | phase 1 = `genome_partition`; phase 2 = `for gi,g in enumerate(part["groups"])` (`4605`) mint loop; phase 3 = `genome_save` (`4628`) | `n`; `len(groups)`; `1` | (via genome_partition) + `srmech_genome_mint` |
| `mint` / `genome()` | `genome.py:3517` (`mint`=alias `3573`) | per-kernel `for label,leaves in items` (`3562`); native path = ONE `_native.genome_mint_c` call | `n_kernels` | **`srmech_genome_mint`** `srmech_genome.c:1032` `for(k<n_kernels)` |
| `mint_strand` | `genome.py:4096` | pre-op check before the `recall` decode (`4171`) — short op, one gate | `1` | — (Python splice over `srmech_genome_centromere`) |

Name-collision caveat for the builder: the Python **graph** `genome_partition(n, edges, …)`
has **no** direct C peer. `srmech_genome_partition(strand, …)` (`srmech_genome.c:1337`) is the
STRAND-recovery op (inverse of `genome`), a different function that shares the name. The
graph partition is a Python composition over `recursive_cut` → `fiedler_sparse_file` (C). So
the only heavy **C** loops in §101 scope are `fiedler_file_iterate` and
`srmech_genome_mint`.

### 1.5 The MCP coercion ratchet (why `progress=` can't be a wire param)

`test_mcp.py::test_all_param_types_json_coercible` (L1345) asserts every
`ToolEntry.parameters` type-string has a handler in
`srmech.mcp._coercion._PARAM_COERCERS` (`has_coercer`, `_coercion.py:1036`). A `Callable`
has **no** coercer and cannot cross JSON-RPC. Declaring `progress` in any ToolEntry turns
macOS CI red exactly as rc273 did. **Every touched op's `progress=` is a Python-only kwarg,
absent from `ToolEntry.parameters`, documented only in the summary prose.**

---

## 2. The callback-flow diagram (aphantasia: draw it)

```
   caller (host app / Python / MCU firmware)
     │  owns  progress_tick_cb  +  user_data (its cancel decision lives here)
     ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ENCODE OP  (genome_from_graph / recursive_cut / mint / …)            │
│                                                                        │
│   for each UNIT of work  (bisection / kernel / group / power-iter):    │
│      … do the complete unit …            ◄── only COMPLETE units land  │
│      ┌─ heartbeat tick ────────────────────────────────────────────┐  │
│      │  if tick != NULL:                                            │  │
│      │     ev = { struct_size, phase, done, total }   (exact ints)  │  │
│      │     rc = tick(&ev, user_data)   ── INLINE, same thread ──────┼──┼─► caller
│      │     if rc != 0:            ◄── nonzero == CANCEL              │  │   returns
│      │        return SRMECH_CANCELLED  (C) / partial+status (Py)    │  │   0 or !=0
│      └──────────────────────────────────────────────────────────────┘  │
│                     │ continue (rc == 0)                                │
│                     ▼                                                   │
│   … next unit …                                                        │
│                                                                        │
│   on cancel  ──►  CLEAN ABORT:                                         │
│        • C:  early-return SRMECH_CANCELLED, *out_count = units_done    │
│              (out buffer holds a VALID PARTIAL of units_done units)    │
│        • Py dict-op:   return { …partial…, "status": "cancelled" }     │
│        • Py strand-op: return the VALID partial / unmodified strand    │
│        • never a half-written unit; never a crash                     │
└──────────────────────────────────────────────────────────────────────┘
```

Key invariants the diagram encodes: (1) the tick fires **between** complete units, so a
cancel can only truncate at a valid boundary; (2) the tick is **inline** on the encode
thread — zero concurrency, MCU-safe, JPL-deterministic; (3) `done/total` are **exact
integers**, never a float accumulator.

---

## 3. The versioned struct + typedef (C) — the new primitive

Add to `srmech.h` (a new section, mirroring the rc242 block's doc style). **Additive
symbols; ABI 5→6 for the new callback typedef.**

```c
/* ------------------------------------------------------------------ *
 * ENCODE PROGRESS + GRACEFUL ABORT (0.9.0rc275, §101 / PR#687) — the
 * caller HEARTBEAT + nonzero-return-to-CANCEL primitive. Distinct from the
 * rc242 srmech_progress_cb_t dispatch-OBSERVER (void return, once-per-tool,
 * process-global): this is a PER-CALL, PER-ITERATION heartbeat WITH a cancel
 * channel, passed as a parameter to a long encode op (libcurl XFERINFOFUNCTION
 * / SQLite progress_handler / libgit2 transfer_progress). Fires INLINE on the
 * encode thread — zero concurrency, MCU-safe, JPL-deterministic.
 *
 * VERSIONED STRUCT (statx stx_mask / Vulkan sType / Win32 cbSize): the first
 * field is struct_size. rc276+ fields APPEND after the current tail; the emitter
 * sets struct_size to what IT knows, the callback reads a field only if
 * struct_size covers it. So the struct extends WITHOUT an ABI bump — only this
 * first introduction bumps (the new callback typedef → CFUNCTYPE implication).
 *
 * OFF BY DEFAULT: a NULL tick pointer means the op runs exactly as today (one
 * pointer test per unit — the hot path pays ~nothing).
 * ------------------------------------------------------------------ */

typedef enum srmech_encode_phase {
    SRMECH_PHASE_PARTITIONING = 0,  /* recursive_cut / fiedler bisection      */
    SRMECH_PHASE_MINTING      = 1,  /* mint / mint_strand / centromere splice */
    SRMECH_PHASE_RENDERING    = 2   /* genome_save / manifest write           */
} srmech_encode_phase_t;

typedef struct srmech_progress_ev {
    uint32_t struct_size;   /* == sizeof(srmech_progress_ev_t); the cbSize gate    */
    uint32_t phase;         /* srmech_encode_phase_t                               */
    uint64_t done;          /* EXACT numerator   (cardinality; always >= 0)        */
    uint64_t total;         /* EXACT denominator (0 == indeterminate; else > 0)    */
    /* rc276+ APPEND-ONLY fields go HERE. Older callbacks (struct_size-gated) skip. */
} srmech_progress_ev_t;

/* Return 0 to CONTINUE, nonzero to CANCEL. Fires inline; MUST be cheap and MUST
 * NOT re-enter srmech_* (it runs inside the encode). */
typedef int (*srmech_progress_tick_cb_t)(const srmech_progress_ev_t *ev,
                                          void *user_data);
```

And append the clean-decline status:

```c
    SRMECH_CANCELLED = 7   /* a tick returned nonzero: clean abort, NOT an error.
                              The out-count reflects the COMPLETE units written. */
```

`%`-fraction is `done/total`, computed by the OBSERVER if it wants a percentage — the
library never divides and never accumulates a float (Class-N discipline: report the exact
integer pair). `done` and `total` are cardinalities (node/kernel/group/iter counts), so they
are non-negative by construction — **no `abs()` anywhere** (there is no sign to strip; this
is not a Class-K pin-slot site).

---

## 4. Exact hook insertions

### 4.1 C — `fiedler_file_iterate` (`srmech_laplacian.c:1635-1660`)

The hot power-iteration. Thread the tick through an **additive overload** symbol so the
existing exported `srmech_laplacian_fiedler_sparse_file` signature is untouched (its ABI is
unchanged; the new symbol is `hasattr`-gated in `_native.py`).

```c
/* NEW additive symbol — the plain one calls this with tick==NULL. */
static srmech_status_t fiedler_file_iterate(const char *path, uint32_t n,
    const double *s, const double *p, double *v, double *u, double *t,
    double *y, double *prev, uint32_t max_iters,
    srmech_progress_tick_cb_t tick, void *tick_user)   /* + two params */
{
    assert(s != NULL && p != NULL);
    assert(v != NULL && prev != NULL);
    uint32_t stable = 0u;
    for (uint32_t it = 0; it < max_iters; it++) {
        if (tick != NULL) {
            srmech_progress_ev_t ev = { (uint32_t)sizeof ev,
                                        (uint32_t)SRMECH_PHASE_PARTITIONING,
                                        (uint64_t)it + 1u, (uint64_t)max_iters };
            if (tick(&ev, tick_user) != 0) {
                return SRMECH_CANCELLED;      /* clean abort, JPL Rule-1 return */
            }
        }
        srmech_status_t st = fiedler_step_file(path, n, s, p, v, t, y, u);
        if (st != SRMECH_OK) { return st; }
        if (fiedler_rescale(n, u, v) == 0) { break; }
        if (fiedler_update_sign(n, v, prev) && it >= 20u) {
            stable++; if (stable >= 5u) { break; }
        } else { stable = 0u; }
    }
    return SRMECH_OK;
}

/* Public: the plain symbol keeps its exact signature (ABI-stable) and forwards. */
srmech_status_t srmech_laplacian_fiedler_sparse_file(uint32_t n, const char *path,
    uint32_t max_iters, double *out_vec, double *ws, size_t ws_len)
{ return srmech_laplacian_fiedler_sparse_file_progress(
        n, path, max_iters, out_vec, ws, ws_len, NULL, NULL); }

/* NEW public overload — carries the tick. Body = today's function + the two
 * params forwarded into fiedler_file_iterate (which now returns SRMECH_CANCELLED
 * up through this frame unchanged). Keep each helper <=60 lines (JPL Rule 4);
 * the current entry already splits scan/build/iterate, so no function grows. */
srmech_status_t srmech_laplacian_fiedler_sparse_file_progress(
    uint32_t n, const char *path, uint32_t max_iters,
    double *out_vec, double *ws, size_t ws_len,
    srmech_progress_tick_cb_t tick, void *tick_user);
```

The `SRMECH_CANCELLED` return propagates up `srmech_laplacian_fiedler_sparse_file_progress`
to its caller with `out_vec` left as the zeroed init (a valid "no cut" vector), so a
cancelled bisection is indistinguishable from an edgeless one at the byte level — the driver
above treats it as a clean stop.

### 4.2 C — `srmech_genome_mint` (`srmech_genome.c:1015-1047`)

Per-kernel loop; the out buffer accumulates COMPLETE chromosomes. Additive overload.

```c
srmech_status_t srmech_genome_mint_progress(
    const unsigned char *labels, const size_t *label_lens,
    const unsigned char *coupling, uint32_t leaf_dim, const unsigned char *leaves,
    const size_t *leaf_counts, size_t n_kernels,
    unsigned char *out, size_t out_cap, size_t *n_blocks_out,
    srmech_progress_tick_cb_t tick, void *tick_user)
{
    /* … identical arg-validation as srmech_genome_mint … */
    size_t label_off=0u, leaf_off=0u, out_off=0u, blocks=0u;
    for (size_t k = 0; k < n_kernels; k++) {
        if (tick != NULL) {
            srmech_progress_ev_t ev = { (uint32_t)sizeof ev,
                                        (uint32_t)SRMECH_PHASE_MINTING,
                                        (uint64_t)k, (uint64_t)n_kernels };
            if (tick(&ev, tick_user) != 0) {
                *n_blocks_out = blocks;      /* VALID PARTIAL: k complete chromosomes */
                return SRMECH_CANCELLED;
            }
        }
        /* … genome_mint_chromosome(...) as today; on OK bump out_off/blocks/offs … */
    }
    *n_blocks_out = blocks;
    return SRMECH_OK;
}
/* srmech_genome_mint keeps its signature and forwards with (NULL, NULL). */
```

Note the tick fires at the TOP of the unit (`done = k` before minting kernel `k`), so a
cancel truncates at exactly `k` complete chromosomes — the out buffer is a valid
`blocks`-block partial genome.

### 4.3 Python — `recursive_cut` (`laplacian.py:5906-6010`)

Python driver; hook the `while pending` loop. Keep an exact `resolved` counter.

```python
def recursive_cut(n, edges, weights=None, *, max_tome=256, work_dir=None,
                  max_iters=250, max_depth=64, progress=None):   # + progress (Py-only)
    ...
    resolved = 0                       # Σ sizes of finalized tomes — exact, monotone
    while pending:
        if progress is not None:
            ev = {"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_PARTITIONING,
                  "done": resolved, "total": int(n)}
            if progress(ev):                       # truthy / nonzero == CANCEL
                # CLEAN PARTIAL: finalized tomes + every still-pending set as a
                # (coarser, uncut) tome — the union still covers all n nodes, so the
                # return is a VALID partition + a status, never a torn strand.
                for sp, _d in pending:
                    dest = os.path.join(tomes_dir, "tome_%d.bin" % len(tome_paths))
                    os.replace(sp, dest); tome_paths.append(dest)
                return {"n_tomes": len(tome_paths), "tome_paths": tome_paths,
                        "tomes": [_read_node_set(t) for t in tome_paths],
                        "work_dir": work_dir, "status": "cancelled"}
        set_path, depth = pending.pop()
        ids = _read_node_set(set_path)
        if len(ids) <= int(max_tome) or len(ids) < 2 or depth >= int(max_depth):
            ...                                    # finalize a tome
            resolved += len(ids)                   # ← the ONLY new bookkeeping line
            continue
        ...
        fv = fiedler_sparse_file(len(ids), sub_path, max_iters=int(max_iters))
        ...
        if not left or not right:
            ...
            resolved += len(ids); continue
        ...
    return {..., "status": "ok"}                   # existing keys + status
```

`resolved/n` is monotone non-decreasing (each finalized tome adds its size; a split adds 0
now, its children resolve later) and reaches `n` exactly when `pending` empties → the
monotonic-and-reaches-100% test is satisfied by construction. No float.

### 4.4 Python — `genome_partition` (`genome.py:4367-4518`)

Forward a phase-tagged progress into `recursive_cut`, then tick the pure reads. On a
cancelled `recursive_cut`, short-circuit to a clean partial.

```python
def genome_partition(n, edges, weights=None, charges=None, *, work_dir=None,
                     max_tome=256, n_bins=_PARTITION_DEFAULT_BINS, max_iters=250,
                     progress=None):                              # + progress
    ...
    cut = recursive_cut(n, edge_list, weight_list, max_tome=max_tome,
                        work_dir=work_dir, max_iters=max_iters, progress=progress)
    if cut.get("status") == "cancelled":
        return {"n": n, "n_communities": cut["n_tomes"], "communities": cut["tomes"],
                "work_dir": cut["work_dir"], "status": "cancelled",
                "groups": [], "counts": {"nuclear": 0, "plasmid": 0},
                "node_counts": {"nuclear": 0, "plasmid": 0}}
    ...
    # participation loop (4457) may also tick per-edge for very large |E|:
    #   if progress and (e & 0xFFF)==0: ev={..._PHASE_PARTITIONING, done=e, total=n_edges}
    ...
    return {..., "status": "ok"}
```

### 4.5 Python — `genome_from_graph` (`genome.py:4544-4631`)

Three phases; forward into `genome_partition`, tick the per-group mint loop, tick around
`genome_save`.

```python
def genome_from_graph(n, edges, weights=None, charges=None, *, coupling, path=None,
                      leaf_dim=None, max_tome=256, n_bins=_PARTITION_DEFAULT_BINS,
                      centromere_at=None, progress=None):         # + progress
    ...
    part = genome_partition(n, edge_list, weight_list, charge_list,
                            max_tome=max_tome, n_bins=n_bins, progress=progress)
    if part.get("status") == "cancelled":
        return {"strand": [], "chromosomes": [], "partition": part,
                "counts": {"nuclear": 0, "plasmid": 0}, "status": "cancelled"}
    strand, chromosomes = [], []
    groups = part["groups"]
    for gi, g in enumerate(groups):
        if progress is not None:
            ev = {"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_MINTING,
                  "done": gi, "total": len(groups)}
            if progress(ev):
                # CLEAN PARTIAL: whole chromosomes minted so far == a valid (shorter)
                # genome strand. Do NOT genome_save on cancel (no half-written body).
                return {"strand": strand, "chromosomes": chromosomes,
                        "partition": part, "counts": _count(chromosomes),
                        "status": "cancelled"}
        ...                                       # graph_to_kernel + mint_strand as today
    ...
    if path is not None and strand:
        if progress is not None:
            progress({"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_RENDERING,
                      "done": 0, "total": 1})     # a cancel here just skips the save
        genome_save(strand, path, coupling)
        ...
    return {..., "status": "ok"}
```

### 4.6 Python — `mint` / `genome()` (`genome.py:3517-3581`) and `mint_strand` (`4096`)

`genome()`: tick the per-kernel pure loop; on the native path pass the tick to
`srmech_genome_mint_progress` (via the ctypes trampoline §5). Cancel returns the valid
partial strand (whole chromosomes assembled so far).

```python
def genome(kernels=None, coupling=None, *, chromosomes=None, progress=None):   # + progress
    ...
    # native path: _native.genome_mint_c(..., progress=progress) — the shim installs the
    # CFUNCTYPE trampoline and, on SRMECH_CANCELLED, returns the blocks-so-far bytes.
    ...
    strand = []
    for i, (label, leaves) in enumerate(items):
        if progress is not None:
            ev = {"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_MINTING,
                  "done": i, "total": len(items)}
            if progress(ev):
                return strand                      # valid partial: i complete chromosomes
        ...                                        # chromosome(...) as today
    return strand
```

`mint_strand` is a single splice (its cost is the `recall` decode at L4171). One
**pre-op** gate is the honest hook — nothing partial is meaningful for a splice, so cancel
returns the **unmodified** input strand (a valid, un-minted strand):

```python
def mint_strand(strand, coupling, *, orientation=None, centromere_at=None,
                repeats=CENTROMERE_DEFAULT_REPEATS, handle="cen", progress=None):
    strand = list(strand)
    ...                                            # existing validation
    if progress is not None:
        ev = {"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_MINTING,
              "done": 0, "total": 1}
        if progress(ev):
            return strand                          # declined: the valid pre-mint strand
    ...                                            # recall + splice as today
```

`mint` (alias) forwards `progress=` to `genome()`.

---

## 5. C ↔ Python parity — the ctypes trampoline (THE risk site)

The pure-Python path builds the event as a **dict** and calls `progress(ev)` directly (§4).
The native path must pass a C function pointer that, when invoked from inside the C loop,
calls the Python `progress` callable. In `_native.py`:

```python
import ctypes

class _ProgressEv(ctypes.Structure):            # byte-identical to srmech_progress_ev_t
    _fields_ = [("struct_size", ctypes.c_uint32), ("phase", ctypes.c_uint32),
                ("done", ctypes.c_uint64), ("total", ctypes.c_uint64)]

_TICK_CFUNCTYPE = ctypes.CFUNCTYPE(ctypes.c_int,           # int return (0/!=0)
                                   ctypes.POINTER(_ProgressEv), ctypes.c_void_p)

def _make_tick_trampoline(py_progress, box):
    """Wrap a Python callable so a raised exception NEVER crosses C frames.
    On ANY exception, stash it in box and return 1 (cancel) to unwind C cleanly;
    the caller re-raises after the C call returns. This is the rc273 lesson on the
    C side: a Callable cannot cross a boundary that has no way to carry it."""
    def _tramp(ev_ptr, _user):
        try:
            ev = ev_ptr.contents
            rc = py_progress({"struct_size": ev.struct_size, "phase": ev.phase,
                              "done": ev.done, "total": ev.total})
            return 1 if rc else 0
        except BaseException as exc:              # noqa: BLE001 — MUST NOT propagate
            box["exc"] = exc
            return 1                              # force a clean C-side cancel
    return _TICK_CFUNCTYPE(_tramp)
```

Contract on the wrappers (`genome_mint_c`, `fiedler_sparse_file_native`): keep a strong
reference to the `_TICK_CFUNCTYPE` object for the whole call (else it is GC'd and the C call
jumps into freed memory), pass `None`→`NULL` when `progress is None`, and after the C call
returns re-raise `box["exc"]` if set. **This trampoline is the single most likely CI-red
source** (GC of the callback object; an exception crossing the boundary; a non-int return).
The parity test asserts the native and pure paths emit the **same (phase, done, total)
sequence** for the same input.

`fiedler_sparse_file` gains a Python-only `progress=` that it forwards to
`fiedler_sparse_file_native` (native → the `_progress` overload) or, on the pure path,
threads into `_fiedler_sparse_py`'s power loop with the same event shape. `recursive_cut`
does NOT need to pass `progress` into `fiedler_sparse_file` for its OWN cancellation (it
checks between bisections at the `while pending` granularity); forwarding is optional for
finer-grained promptness within one huge top-level bisection.

---

## 6. Cancel-return shapes (the derived clean partial/decline), per op

| Op | On cancel returns | Why it is well-formed |
|---|---|---|
| `recursive_cut` | dict with `"status":"cancelled"`; finalized tomes + each pending set promoted to a coarse tome | union still partitions all `n` nodes → a valid (coarser) partition |
| `genome_partition` | dict `"status":"cancelled"`, `communities` from the partial cut, empty `groups`/`counts` | the community assignment is valid; the pure read simply wasn't run |
| `genome_from_graph` | dict `"status":"cancelled"`, `strand` = whole chromosomes minted so far, matching `chromosomes`; **no `genome_save`** | each chromosome is a complete self-describing region; concatenation is a valid shorter genome; nothing written to disk |
| `mint` / `genome()` | the partial strand (whole chromosomes so far) | bare-strand return; caller owns the cancel decision so it knows it is partial (libcurl `CURLE_ABORTED_BY_CALLBACK` semantics) |
| `mint_strand` | the **unmodified** input strand | a splice has no meaningful partial; declining leaves a valid un-minted strand |
| C ops (`*_progress`) | `SRMECH_CANCELLED (=7)`; `*out_count` = complete units written | out buffer holds a valid partial of `out_count` complete units; not an error code |

Rationale trail: this mirrors `telomere_tick` (a distinct clean status + a well-formed
result, `daughter=None` for the decline) one scale up. "Return a clean partial genome, not a
half-written strand" resolves to **truncate only at a complete-unit boundary** — which the
between-units tick placement guarantees.

---

## 7. Test shapes (build-ready)

Add `python/tests/test_genome_progress.py` (+ a C test `c/test/test_srmech_progress_tick.c`).

1. **Monotonic + reaches 100%.** Collect events into a list; assert `done` is non-decreasing
   within a phase and the final event of the terminal phase has `done == total` (e.g.
   `recursive_cut` last partitioning event `done == n`). Run on a graph big enough to force
   several bisections.
2. **Cancel at X% aborts promptly + returns the derived clean result.** A callback returning
   `1` once `done*100 >= X*total`. Assert: (a) no further events fire after the cancel; (b)
   the return has `status=="cancelled"` (dict ops) or is the valid partial/unmodified strand
   (bare-strand ops); (c) for `genome_from_graph(path=…)` **no genome dir is written**; (d)
   for the C op, status `== SRMECH_CANCELLED` and `out_count` = a valid partial that
   `genome_load`/`kernel_to_graph` can still read for the complete units.
3. **C↔Python parity — same callback sequence.** Record `(phase, done, total)` tuples from
   the pure path and the native path for the same input; assert equal lists. (Covers
   `fiedler_sparse_file` and `mint`.)
4. **Bare-C / native-absent both honor the contract.** Run the whole suite once with
   `HAS_NATIVE=True` and once forced pure (numpy-absent venv per project discipline); both
   must pass the same assertions. Plus a standalone C test that registers a tick that cancels
   at iteration 3 of `fiedler_file_iterate` and asserts `SRMECH_CANCELLED` + the zeroed
   `out_vec`.
5. **JPL-clean C.** `test_jpl_audit.py` must still pass: the new `*_progress` functions and
   the trampoline-free C loops are ≤60 lines, ≥2 asserts each (the tick block adds none of
   its own asserts but the host functions already carry theirs), no `goto`, no `malloc` (the
   `srmech_progress_ev_t` is a stack struct). Add the two new public symbols to the audit's
   expected-symbol inventory if it enumerates one.
6. **No float drift / no `abs()`.** Grep the diff: the progress code contains no `float(`,
   no `/ total`, no `abs(`. `done`/`total` are ints end to end. A unit test asserts the
   emitted `total` equals the exact known work count (`n`, `n_kernels`, `len(groups)`,
   `max_iters`).
7. **The wire-param guard stays green.** `test_all_param_types_json_coercible` and the
   tool-count tests pass unchanged — proving `progress=` never leaked into a `ToolEntry`.
   Add an explicit assertion that `"progress"` is not among any genome/laplacian ToolEntry's
   `parameters` names.

---

## 8. Registry-ripple implications

**Because `progress=` is a Python-only kwarg (never a wire param) and no public callable is
added or removed, the ripple is minimal:**

- **NO** new `ToolEntry`, **NO** new `P()` param row, **NO** change to
  `describe()["tools"]["total"]` (the five duplicated count-tests are untouched), **NO**
  carrier_registry regen, **NO** new Rosetta bucket. The "public-callable rc ripple gate"
  (carrier_registry + Rosetta) does **not** fire — that gate is for new/changed public
  callables, and a kwarg-only addition is neither.
- **DO** update the `ToolEntry.summary` prose for the five registered ops (`mint`,
  `mint_strand`, `genome_partition`, `genome_from_graph`, `recursive_cut`) to mention the
  in-process `progress=` heartbeat/abort affordance (so an MCP user learns it exists even
  though it is not callable over the wire). Keep it to one clause each.
- **DO** ripple the C side: add the new typedef + struct + `SRMECH_CANCELLED` + the two
  `*_progress` symbols to `srmech.h`; bind the `*_progress` symbols in `_native.py` behind
  `hasattr` (so an old lib silently uses the plain path); **bump `SRMECH_ABI_VERSION` 5→6**
  and `EXPECTED_ABI_VERSION` 5→6 in lockstep; update the 5 version-SSOT files
  (`pyproject.toml`, `pyproject-pure.toml`, `srmech/version.py`, `c/include/srmech.h`
  `SRMECH_VERSION*`, and the hard-pinned version test) to `0.9.0rc275`; add the CHANGELOG
  entry + the ABI-history bullet.
- **The Callable-not-a-wire-param rule, stated for every touched op:** `genome_from_graph`,
  `recursive_cut`, `mint`, `mint_strand`, `genome_partition`, `fiedler_sparse_file`,
  `genome()`/`mint` each gain a Python-only `progress=`/on-cancel kwarg that is **absent
  from `ToolEntry.parameters`**. On the C side the tick is a function pointer in the ABI —
  fine for C, never an MCP surface.

---

## 9. Underdetermination flags (leading candidates)

1. **Does `recursive_cut` forward `progress` into `fiedler_sparse_file`?** LEADING: **no**,
   for cancellation — the `while pending` granularity is enough and is the exact-%-reportable
   point; forwarding is an OPTIONAL promptness refinement for a single huge top-level
   bisection. A build subagent may ship the forward if a test shows a single bisection can
   run long enough to matter; otherwise defer it (the C `_progress` overload still exists for
   bare-C hosts). Falsifiable by timing one top-level bisection on the largest in-scope
   graph.
2. **Cancel granularity for the participation loop in `genome_partition`.** LEADING: tick
   every `0xFFF` edges (a cheap mask, not per-edge) — the loop is `O(|E|)` and fast relative
   to `recursive_cut`, so a coarse tick avoids callback overhead. Underdetermined only in the
   mask size; pick 4096 unless a profile says otherwise.
3. **ABI bump strictly required?** The literal ADR-0007 rule ("bump only if an existing
   function's wire format changes") would say a new typedef + new symbols is additive → **no
   bump**. The STANDING PRECEDENT (v2→v3, v3→v4, v4→v5 all bumped on a new callback typedef
   because the ctypes shim constructs a CFUNCTYPE and `_native` gates on ABI) says **bump**.
   LEADING: **bump 5→6** for consistency with #840; a build subagent that instead keeps ABI 5
   must justify the divergence and confirm `_native` still loads the new symbols by `hasattr`
   alone. Not a free choice — pick the precedent unless the user rules otherwise.

---

## 10. One-line file-touch manifest for the build subagent

- `docs/srmech/c/include/srmech.h` — new struct/enum/typedef/`SRMECH_CANCELLED`; two
  `*_progress` prototypes; ABI 5→6 + history bullet; `SRMECH_VERSION*` → rc275.
- `docs/srmech/c/src/srmech_laplacian.c` — `fiedler_file_iterate` + two params;
  `..._fiedler_sparse_file_progress` overload; plain symbol forwards.
- `docs/srmech/c/src/srmech_genome.c` — `srmech_genome_mint_progress` overload; plain
  forwards.
- `docs/srmech/python/srmech/amsc/laplacian.py` — `recursive_cut` + `fiedler_sparse_file`
  `progress=`.
- `docs/srmech/python/srmech/amsc/genome.py` — `genome_partition`, `genome_from_graph`,
  `genome()`/`mint`, `mint_strand` `progress=`; `_PROGRESS_STRUCT_SIZE`/`_PHASE_*` consts.
- `docs/srmech/python/srmech/amsc/_native.py` — `_ProgressEv`, `_TICK_CFUNCTYPE`,
  `_make_tick_trampoline`, `*_progress` bindings (`hasattr`-gated); `EXPECTED_ABI_VERSION`
  5→6.
- `docs/srmech/python/srmech/amsc/tool_schema.py` — summary-prose only for the five ops (NO
  new `P()` rows).
- `docs/srmech/python/tests/test_genome_progress.py` + `c/test/test_srmech_progress_tick.c`
  — the §7 tests.
- version-SSOT: `pyproject.toml`, `pyproject-pure.toml`, `srmech/version.py`, the pinned
  version test; `CHANGELOG.md`.
