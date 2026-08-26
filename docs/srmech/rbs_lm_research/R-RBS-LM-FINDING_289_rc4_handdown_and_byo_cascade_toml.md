# F289 — dev hand-down (F281-style): rc4 block-octonion HD tiling (#811) + capacity-free vs Klein-4 (#812), AND bring-your-own cascade-TOML extensibility (framework reading + mechanism rec)

**Headline:** Two deliverables for the srmech v0.7.0 loop-bind arc, every operator anchor **computed from the shipped native `loop_bind`** (the rc1 Cayley–Dickson recursion = the parity oracle), so rc4 ports with no new math. **D1:** the block-octonion HD tiling at D=2048 is the **direct sum of 256 independent dim-8 `loop_bind`s** (block-diagonal, no coupling — verified block err **0.0**), unbind recovers to **2.9e-15**, and it is **capacity-free vs Klein-4** (loop-bind ≥ klein4 at matched D; owned verdict below). **D2:** a user cascade-TOML "following srmech naming" IS a **pure-TOML composite op** (config-not-code); validate at load; recommended mechanism = **`SRMECH_CASCADE_PATH`** (config-driven search path) + a composite-resolver extension to `lookup_cascade_op`, with entry-points reserved for the rarer code-primitive case; user ops surface in tool-schema with a **provenance flag** (not an attested srmech primitive). Lineage: F271/F272/F273/F276/F277/F278–F281; #811/#812/#813/#814. Verified srmech v0.7.0rc2; anchors in `rc4_groundtruth.py` + `loop_bind_capacity_812.py`.

---

## DELIVERABLE 1 — rc4: block-octonion HD tiling (#811) + capacity-free vs Klein-4 (#812)

### 1. The tiling construction at D=2048 (closed form, no new math)
- **D = 2048 = 256 blocks × 8.** `loop_bind_hd(x, y)`: reshape `x,y` → `(256, 8)`; for each block `k`, the block product is the **shipped** `srmech.amsc.hdc.loop_bind(x_k, y_k)`; reassemble to D.
- **Block-DIAGONAL — no inter-block coupling.** `loop_bind_hd = ⊕_{k=0..255} loop_bind` (direct sum of 256 independent dim-8 binds). **Verified:** block `k` of `loop_bind_hd(x,y)` == `loop_bind(x_k, y_k)` exactly, err **0.0e+00**. Nothing couples blocks; the bind is a parallel array of the shipped dim-8 product.
- **The per-block product IS the shipped table.** Native `loop_bind` == oracle (`loop_bind_moufang.py` rc1 cd) == the batched `cd_b` (the fast HD path), all 64 basis pairs, atol 1e-12. So the dev composes **256 calls to the shipped `loop_bind`** (or the verified-equal batched form) — zero new multiplication.
- **Unbind = per-block Moufang left-division.** `unbind_hd(a, y)`: per block, `loop_conj(a_k) ⊗ y_k` (each block is a unit octonion → invertible; `conj(a)·(a·x) = x` by alternativity). Uses the shipped `loop_conj` + `loop_bind`, per block.
- **Anchor vectors are unit-per-block** (each 8-block normalized to a unit octonion) so per-block inverse = `loop_conj`.

### 2. Class attribution (NO new class; Class O stays dissolved)
- `loop_bind_hd` = **Class M (per-block `loop_bind`, = M∘C with a Class-K associator residue, per F272/F281) applied over a direct-sum TILE layout** (256 independent blocks). The tiling is a **structural packaging** of M (a direct sum), exactly as klein4's high-D realization packages its sector op — it adds **no** A-N class. Cascade label in `compose.run_chain`: `class="M", op="loop_bind"`, applied block-wise (block-size a param), or a thin `loop_bind_hd` wrapper registered as class M. The 14 A-N hold.

### 3. Capacity-free vs Klein-4 (the #812/F277 claim, quantified + owned verdict)
- **Metric:** bind `K` `key⊗val` pairs with `loop_bind_hd`, superpose (sum), unbind each key, clean up by nearest-cosine over an `M`-item value codebook; **accuracy = fraction retrieved.** Compared against `klein4_bind`/`klein4_bundle`/`klein4_similarity` at the **same D=2048, M, seed**.
- **Numbers (seed 23, M=128, 5 trials):**

  | K | loop-bind | klein4 | source |
  |---|---|---|---|
  | 2 | 1.000 | 1.000 | rc4_groundtruth.py (native path) |
  | 8 | 1.000 | 1.000 | " |
  | 32 | 1.000 | 1.000 | " |
  | 64 | 0.997 | 0.997 | " |
  | **128** | **0.923** | **0.867** | F277 / loop_bind_capacity_812.py (full curve) |

  capacity knee (first K<0.9): **loop-bind >128, klein4 =128.**
- **OWNED VERDICT:** at matched D, the block-octonion loop bind's retrieval capacity is **≥ Klein-4** — identical through K=64, and loop-bind ≥ klein4 at K=128. So the loop bind carries **order + tree + direction (F274)** at **no capacity cost** vs the commutative XOR bind: **capacity-free, confirmed.** *Honest scope:* the small K=128 edge (0.923 vs 0.867) is one regime/seed — **not** asserted as a general advantage; the load-bearing claim is the **null cost.**

### 4. Self-test anchors (bit-exact, seeded — assert against these)
- **Parity (the pin):** `native loop_bind == oracle == batched cd_b` on all 64 basis pairs (atol 1e-12). [`True/True`]
- **Block products** (within one block, from native `loop_bind`): `e1⊗e2 = +e3`, `e2⊗e4 = +e6`, `e4⊗e1 = −e5`, `e3⊗e5 = −e6`, `e1⊗e1 = −e0` (imaginary units square to −1·e0). *(Full 7×7 cross7 table + the 7 Fano triples: see F281 — unchanged, the HD per-block product is that table.)*
- **Block-diagonal:** `block_k(loop_bind_hd(x,y)) == loop_bind(x_k, y_k)`, err **0.0e+00** (seed 811).
- **Unbind recovery:** `unbind_hd(a, loop_bind_hd(a, v)) == v`, err **2.92e-15** (seed 811).
- **Capacity** (seed 23, M=128): K=2/8/32/64 → loop **1.0/1.0/1.0/0.997**, klein4 **1.0/1.0/1.0/0.997**; K=128 → loop **0.923** ≥ klein4 **0.867** (F277).

### 5. Scope rec for rc4
- **Python-only**; the co-equal **C peer deferred** to the arc's end transpile-to-C step (consistent with the voxel-first cadence).
- **Pin every convention to the shipped `loop_bind`** Cayley–Dickson table `[a·c − conj(d)·b, d·a + b·conj(c)]`, `e0` = real anchor. The HD tiling introduces **no new multiplication** — it is the shipped dim-8 product, block-diagonal. cross7/g2 (rc2) are unaffected (they're per-block).
- Surface as `class="M", op="loop_bind"` applied per-block (block-size a param), **not** a new class.

---

## DELIVERABLE 2 — bring-your-own cascade-TOML extensibility (framework reading + mechanism rec)

### 1. Framework reading: a user descriptor IS a pure-TOML composite op — **YES**
srmech's commitments are **config-driven plugin architecture** + **open by tooling-architecture** + **form = function / config-not-code**. Under those, a cascade's *behavior* **is** its named-op composition — so a third-party descriptor whose behavior is a **validated chain of already-named A–N / cascade ops** is a first-class op **with no Python callable required.** The behavior *is* the TOML. That is exactly what the user means by "behavior DEFINED BY THE TOML." **Yes** — the right model is the **pure-TOML composite op**.
- **Two extension kinds, kept distinct:** (a) a **composite** op = a chain of *named* ops → pure TOML, no code (the common case, the user's intent); (b) a **new primitive** = new math → needs a Python/C callable (the rare case). Only (b) needs code; (a) is config.

### 2. Validation discipline ("following srmech naming", enforced)
A user descriptor is valid iff, checked **at load** (loudly, not at run):
- every step's **class ∈ {A..N}** (the 14; **no Class O**);
- every referenced **op resolves** — a shipped callable in `srmech.amsc.cascade` / the class module, **or** another validated composite;
- the **composition is a valid chain** — arg/shape contracts satisfied, no cycles, terminating.
A typo (unknown op, bad class, broken arg) **fails at `load_catalog` / `build_chain_from_toml`**, not silently at run. This is the F281 "follow srmech naming" rule made into a load-time gate.

### 3. Mechanism recommendation — **`SRMECH_CASCADE_PATH`** (primary) + composite-resolver; entry-points for the code-primitive case
The three candidates: (a) `SRMECH_CASCADE_PATH` env-var search-path of catalog dirs; (b) `register_catalog_dir(path)` API; (c) the ADR-0001 profile-plugin entry-point loader.
- **Recommend `SRMECH_CASCADE_PATH`** (a path-list; `load_catalog()` merges the packaged dir **+** the user dirs; drop the `lru_cache`-over-only-packaged limitation) as the **primary** mechanism, because it **best honors config-not-code**: a specialist **drops a TOML in a dir on the path** — no Python, no packaging, no entry-point ceremony. That is the lowest-ceremony "open by architecture" extension and matches the user's intent literally ("use their own TOML"). It also **composes with the existing catalog-TOML-driven tool-schema + CLI** (v0.5.0rc12): user dirs auto-surface identically to shipped.
- **Pair with a thin `register_catalog_dir(path)`** programmatic API (the env-var simply calls it at import) for embedded/test use — same registry, two entry points (env + API).
- **The ADR-0001 entry-point loader is RIGHT for the rarer CODE-primitive case** (a user shipping a new Python/C op as an installable package) — but it is **over-ceremony for a pure-TOML composite** (which needs no Python). **Two tiers:** entry-points for code primitives; `SRMECH_CASCADE_PATH` for TOML composites.
- **Load-bearing extension to `lookup_cascade_op`:** today it only does `getattr(srmech.amsc.cascade, name)`. To enable the **pure-TOML composite** (gap ii), make it resolve **(a)** a shipped callable **OR (b)** a registered composite descriptor (a `[composite]` whose body is a validated `[[stage]]` chain) → **run the sub-chain.** That single resolver change is what turns "behavior defined by the TOML" from impossible into a load-time-validated composition.

### 4. tool-schema / CLI + the attestation caveat
- **Yes** — user-registered ops **should** surface in `tool-schema` + CLI **identically** to shipped ops (the whole point; auto-surfacing via the catalog-TOML-driven schema is already the mechanism).
- **Attestation caveat (load-bearing, MPM):** a user op is **not an attested srmech primitive.** The schema entry must carry a **provenance flag** — e.g. `provenance: "user"` + the user descriptor's hash — so a user composite is attested **to the user's descriptor (B-tier)**, *not* to srmech's verified ground-proof (A-tier). This keeps "a citation without attestation is not real" intact for third-party ops: the op is real + usable + surfaced, but its attestation chain is the user's, not srmech's. (No-magic discipline preserved across the open boundary.)

---

### Status / discipline
HAND-DOWN (F281-style). **D1** anchors all **computed from the shipped native `loop_bind`** (rc4_groundtruth.py: parity, block products, block-diagonal err 0.0, unbind 2.9e-15, capacity K≤64; F277/loop_bind_capacity_812.py: the full curve incl. K=128) — bit-exact, rc1/rc2-consistent by construction; the capacity-free verdict is **owned** (loop-bind ≥ klein4). **D2** is a framework-grounded architecture call (the dev makes the final mechanism choice; the recommendation is principled, not arbitrary). NO new class (M∘C∘K hold; Class O dissolved). Class-K (norms/inner products; no `abs()`). CAD-ban. No-lineage. Citations: none load-bearing — the ground-truth is the bind-derived table (MPM). Builds on F271/F272 (the ops), F273 (28D/14DoF/G₂), F276 (the gate), F277 (#812 capacity), F278–F281 (the chemistry/voxel arc), #811/#812/#813/#814. Verified srmech v0.7.0rc2, `/tmp/srmech_v070rc2_venv`. `[[feedback_upstream_srmech_fixes_as_research_notes]]`; `[[feedback_no_mvp_framing]]` (full-coverage, not minimal); `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`.
