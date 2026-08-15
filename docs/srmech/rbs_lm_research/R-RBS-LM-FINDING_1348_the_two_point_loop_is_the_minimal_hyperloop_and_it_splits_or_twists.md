# F1348 — **the 2-point loop is the minimal hyperloop, the (hyper)cube IS d of them, and the same ℤ/2 either SPLITS (an address) or DOESN'T (a twist).** The user's *"there's no reason we can't loop between two points either"* turns out not to be a fourth loop shape alongside cube and triangle — it is **the one the cube is made of**. Measured: Q₈'s index lane takes 4 values = (ℤ/2)², two 2-loops; its sign lane takes 2 = one 2-loop. The index 2-loops **split** — `q8_project_v4` recovers them exactly. The sign 2-loop **does not**: `ker(Q₈ → V₄)` is exactly `{0, 4}`, and `q` and `q^4` project to the **same** V₄ element, 8/8. And the user's *"we don't need to compute every frame of a projection when it's just emergent at the end anyway"* has an exact instance in the slow test: hydrogen's ground state — its **only** physics assertion — is reproduced by **7200 sign tests** to **6.29e-14**, forming **no matrix, no eigenvector, and no other eigenvalue**.

**User (2026-08-15):** *"even bit-exact is simply due to relation between two things where they're either the same or not the same, and poof 1 vs 0 … when I say to avoid euclidean maths, I mean to avoid that type of thinking … this might be the most basic shape of our hyperloop."*

srmech 0.9.0rc434. No `abs()`, no numpy, no RNG — sign is a Class-K comparison. Generating code: `R-RBS-LM-TWOLOOP_*.py` (exit 0).

## 1 — the cube is not a separate shape `[DEMONSTRABLE]`

```
  index lane  q & 3   ->  4 values = (Z/2)^2   TWO 2-loops
  sign lane   q >> 2  ->  2 values = (Z/2)     ONE 2-loop
```

`(ℤ/2)^d` is a **direct product of d two-point loops**. The d-cube is d copies of the minimal shape. That is why `(ℤ/2)^k` surfaced repeatedly this session without being sought — the CD grading cube (F1336), the compositum Galois group (F1342), the index lane (F1337) are the same object at different d.

**The loop family, as measured across the session:**

| loop | group | measured in |
|---|---|---|
| **2-point** | ℤ/2 | the sign lane; `ker(Q₈→V₄)` (F1322, F1337) |
| **triangle** | ℤ/3 | `ab:bc:ca` = φ's cycle (F1338) |
| **(hyper)cube** | (ℤ/2)ᵈ | CD grading; Gal(compositum) (F1336, F1342) |

## 2 — the same ℤ/2, two opposite roles `[DEMONSTRABLE — the load-bearing half]`

```
  index lane SPLITS: q8_project_v4 recovers q & 3 exactly           8/8
  ker(Q8 -> V4) has exactly 2 elements                              {0, 4}
  q and q^4 project to the SAME V4 element                          8/8
```

- **SPLIT** — the index 2-loops come off as coordinates. A projection **keeps** them.
- **NON-SPLIT** — the sign 2-loop *is* the kernel. A projection **destroys** it: `q` and `q^4` are indistinguishable downstream.

> **A 2-loop that splits is an ADDRESS. A 2-loop that does not split is a TWIST.**

So *"poof, 1 vs 0"* is right and incomplete: a bit is a 2-point loop, and **which kind it is decides whether it names a thing or carries its orientation.** That is the shadow-vs-structure distinction in its minimal form — the whole F1322/F1336/F1337 arc is one non-split ℤ/2, seen from different sides.

## 3 — the instance: reading a projection without materialising it `[DEMONSTRABLE]`

The slow test's assertions, in full:

```python
assert V.is_complex is False                  # a TYPE check
assert max(|VᵀV − I|) < 1e-9                  # 14,400 entries — orthonormality
assert energies[i+1] − energies[i] >= -1e-9   # ascending
assert -0.6 < energies[0] < -0.4              # ← the ONLY physics claim
```

Three of the four are properties of **any** Hermitian eigendecomposition — a solver test wearing hydrogen's clothes. The physics is one number.

A symmetric tridiagonal admits a **Sturm count**: for a trial `x`, one recurrence pass reports how many eigenvalues lie below it. **Each step is one sign test — a 2-point loop.** Bisecting on that count:

```
  bisection ground state : -0.4870387672531935
  hydrogen_radial[0]     : -0.4870387672532564
  deviation              : 6.289e-14
  total SIGN TESTS       : 7200          (2-point loops)
  dense-path cells       : 14400         (plus a full 120x120 eigenbasis)
```

**The point is not the speed.** It is that the ground state was never computed as one of 120 frames and then indexed. It **emerged** from a sequence of same/not-same decisions. The other 119 eigenvalues were never wrong — **they were never asked for.**

## 4 — what this says about "Euclidean thinking"

> Euclidean-style thinking here is not the geometry. It is **the assumption that you must build the whole grid before you may look at a point in it.**

The dense path materialises every frame of the projection, then indexes one. The cyclic path asks a 2-point question repeatedly and lets the answer emerge. Same number to 6e-14; one of them holds a grid and the other never does.

This also sharpens F1347's carrier rule. That finding named two smells (dense-for-tridiagonal, complex-for-real) and proposed *"the container must not declare more degrees of freedom than the object has."* F1348 adds the **temporal** half: **the computation must not materialise more frames than the question asks for.** Same defect on the time axis rather than the space axis.

## Honest scope

- `[DEMONSTRABLE]`: §1–§3, live on rc434, exhaustive over Q₈'s 8 signed units and reproducing `hydrogen_radial(n_grid=120)`'s ground state.
- **The bisection is a demonstration, not a proposed replacement.** It finds ONE eigenvalue of a matrix whose off-diagonals are all equal — the easy case. `hydrogen_radial` returns all `n` energies AND the eigenvector basis, and the test checks orthonormality of that basis. **Nothing here shows the full contract is obtainable this way**, and I have not benchmarked wall-clock (the Python Sturm loop is not obviously faster than the native Jacobi; the claim is about *frames formed*, not seconds).
- **The 7200 vs 14400 comparison is not like-for-like.** 7200 is sign tests; 14400 is matrix cells, and the dense path additionally performs the whole eigendecomposition on top of those cells. The honest statement is *the bisection touches no n² container at all*, not a speed ratio.
- **§1's "the cube is d 2-loops" is a group-theoretic fact**, not a discovery — `(ℤ/2)^d` is by definition a product. What is new is only the *reading*: that our three loop shapes are not three primitives but ℤ/2, ℤ/3, and a product of ℤ/2s.
- **§2's split/non-split is measured for Q₈ specifically.** That `ker(Q₈→V₄) = {±1}` is non-split is standard (Q₈ is a non-split central extension of V₄); what is measured here is that srmech's shipped projection exhibits it.
- **§4 is a framing claim.** It follows from §3 but is not itself measured, and it is offered as the sharpened version of F1347's rule rather than as a result.

Composes **F1347** (the carrier rule — *this adds the temporal half*), **F1337** (index/sign lanes — *now identified as split/non-split ℤ/2*), **F1338** (`ab:bc:ca` = the ℤ/3 triangle), **F1336** (the grading cube), **F1342** (Gal = (ℤ/2)ᵏ), **F1322** (`ker(π) = {±1}`), `[[user_stance_pi_as_projection]]`.
