# F1345 — **neither. The 𝔽₂ rank ships as `srmech.math.modular_linalg.gf_rref`, and I hand-rolled it in F1342.** The user asked whether we could identify a chain order for a branchless fixed-size elimination, or whether we needed a carrier-type change. The answer is **neither**: `gf_rref(rows, 2)["rank"]` is a shipped op, it returns **4** for the stiff-string square classes (the same k my hand-rolled XOR elimination produced in F1342) and **2 of 3** for the degenerate case, and it is **reachable from a declared chain by dotted path** — verified. The branchlessness question never arises, because the branching lives inside a compiled op rather than inside the chain. **This is the third consecutive turn where the thing I called missing was already shipped**, and this one is worse than the other two: F1342 presented a hand-rolled 𝔽₂ Gaussian elimination as the *measurement*, which is precisely the failure `[[feedback_introspect_srmech_before_python_dispatch]]` exists to prevent.

**User (2026-08-15):** *"we should be able to identify the chain order for doing the branchless fixed-sized or we need to have some change to carrier types?"*

srmech 0.9.0rc432. Verified live. Descriptor: `cascade_catalog/f2_rank.toml`.

## 1 — the op `[DEMONSTRABLE]`

```
srmech.math.modular_linalg.gf_rref(rows, p) -> {"rref", "rank", "pivots"}
srmech.math.modular_linalg.gf_nullspace(A, p)
srmech.math.modular_linalg.gf_solve(...)
```

On F1342's four stiff-string square classes over the prime support `[2,5,7,11,13,127,251,1009]`:

```
  rows = [[1,1,1,1,1,0,0,0],      # 1001000 -> 2*5*7*11*13
          [1,1,0,0,0,0,1,0],      # 62750   -> 2*5*251
          [1,1,0,0,0,0,0,1],      # 9081000 -> 2*5*1009
          [0,1,0,0,0,1,0,0]]      # 254000  -> 5*127
  gf_rref(rows, 2)["rank"]  ->  4        (compositum degree 2^4 = 16)

  degenerate control [[1,1,0],[1,1,0],[0,0,1]]  ->  rank 2 of 3 rows
```

**Identical to F1342's hand-rolled result.** F1342's elimination was not a measurement of anything srmech lacked — it was a re-implementation of this op.

## 2 — and it is chain-reachable `[DEMONSTRABLE]`

```toml
[[cascade.chain.steps]]
class = "I"
op    = "srmech.math.modular_linalg.gf_rref"
args  = { rows = "@input.rows", p = 2 }

[[cascade.chain.steps]]
class = "E"
op    = "srmech.cascade.leaves.seq_get"
args  = { seq = "@step[0].output", i = "rank" }
```
→ **4**. (`seq_get` is a generic getter and indexes the returned dict by key.)

## 3 — so the question dissolves

| the question asked | the answer |
|---|---|
| identify a chain order for a branchless fixed-size elimination? | **not needed** — the elimination is inside a compiled op, so the chain never branches |
| change the carrier types? | **not needed** — `rows` is a list of int lists, which the chain already passes |

The `data-SIZED, never data-DEPENDENT` invariant is a constraint on **what the chain itself does**, not on what an op it calls may do internally. A chain calling `gf_rref` performs **one** step regardless of the data; all the branching is the op's business. **That is the general lesson: the totality guarantee is preserved by delegating to a registered op, not by making the algorithm branchless.**

## 4 — what is genuinely still unbuilt

**Assembling the row matrix.** Going from *a set of integers* to *aligned parity vectors over a common prime support* is a join: take the union of the supports, then emit one vector per input over that union. I have **not** built it, in a chain or otherwise. It is the only remaining piece between `square_class` (F1344, declared) and `frame_change_group` (F1342's ask). I am not going to guess whether it is expressible — the last three guesses were all wrong in the same direction.

## Honest scope — and the pattern I should name

- `[DEMONSTRABLE]`: §1, §2. Live, this rc.
- **Three consecutive misses, all the same shape.** F1343: "needs a bit-gate leaf" — `rational_pow_uint` was it, and `dead_band` was a Class-K integer gate sitting in a list I printed. F1344: "the chain is limited to 13 leaves" — my own descriptor already called a dotted path. F1345 (this): "the rank needs branchless composition" — `gf_rref` ships. **In every case I reasoned from an incomplete surface read instead of searching, and in every case the disproof was one `search()` call away.**
- **F1342 is the one that needs amending, not just noting.** It presented hand-rolled 𝔽₂ Gaussian elimination as its method. The *numbers* are right (k=4, degree 16, and the B=1/4 degeneracy all reproduce under `gf_rref`), so no conclusion changes — but the **method** was a hand-roll of a shipped op, which is the exact defect `[[feedback_introspect_srmech_before_python_dispatch]]` records. Its §4 "ask" for `square_class_basis` should be read as **already satisfied** by `gf_rref`.
- **What actually remains of F1342's ask:** `square_class` — **built** (F1344, declared TOML). `square_class_basis` / the 𝔽₂ rank — **already shipped** (`gf_rref`). `frame_change_group` — needs only the **support-alignment join**, which is unbuilt and unassessed.
- **The corrective for me is procedural, not conceptual:** run `srmech.introspect.search.search(...)` on the operation *before* claiming absence. It found `gf_rref` on the first query. I had used that surface earlier this session and did not use it here.

Composes **F1342** (*method amended: its elimination re-implements `gf_rref`; its numbers stand*), **F1344** (the declared `square_class`), **F1343** (retracted), **F1341**, `[[feedback_introspect_srmech_before_python_dispatch]]`, gh **#1530 §L**.
