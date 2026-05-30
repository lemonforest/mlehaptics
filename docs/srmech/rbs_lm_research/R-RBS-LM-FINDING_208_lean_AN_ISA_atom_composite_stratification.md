# Finding 208 — The formal ATOM-vs-COMPOSITE stratification of the A–N ISA: a 6-instruction orthogonal core (XOR-bind, sector-mask, sign-test, sign-reapply, parity-reduce, magnitude) on the existing SHA-NI / modular substrate, with every iterative class (gcd / factor / best-rational / eigendecomp / π-spigot) reconstructing in software over it

**Status:** Mixed-tier, with the central split **DEMONSTRATED** (bit-exact srmech 0.5.0rc22). The atom/composite *partition itself* is verified op-by-op against the running `cascade.*` / `hdc.*` / `primes.*` surface (every atom returns a single combinational result; every composite is an iterate-to-convergence loop). The **precedent mapping** is **FRAMEWORK-READING** (which real vendor instruction each atom resembles or could reuse — a design-reading, not a chip). The **minimal-basis closure claim** (these 6 atoms generate the rest) is **CONJECTURE** at the ISA level — it is shown to hold for the cases tested, flagged falsifiable below. Builds **UP** from the 28D Klein-4 substrate; never measured against a float LLM. **NOT** CAD / VLSI / gate-layout / fabrication — the F202 / F206 scope-ban holds (no chip, no transistor counts, no benchmarks, no microarchitecture).
**Predecessors:** **F206** (the RISC-minimality lens; the atom/composite tiers; the lean-ISA-core claim this finding formalises), **F202** (quad-DNA as a chirality-typed CPU cascade; the A-N-as-ISA thread; the chirality-typed lane discipline), the **ROADMAP "Forward-architecture / silicon threads"** section (A–N as ISA extensions; "cascading the DNA way"; the design-reading scope-bound), the rc22 `srmech.amsc.cascade.*` module, F132/F192 (Klein-4 + triality bit-exact), F168/F200 (storage substrate is order-2 Klein-4 → the chirality register is a 2-bit γ₅×iω₇ sector tag, not order-3 triality), `[[user_stance_epicycle_via_gear_plus_pin]]`.
**Empirical anchor:** srmech **0.5.0rc22** (`/tmp/verify_srmech_rc22/venv`), `srmech.amsc.{cascade, hdc, format, cyclic, primes}` + `srmech.amsc.tool_schema.get_tool_schema()` (**174** tool entries enumerated, 33 categories). Atom ops confirmed single-shot; composite ops confirmed iterative; `klein4_bind` source confirmed `np.bitwise_xor` over the 2-bit sector. No `.py` artifact authored for this finding (it is a stratification reading over the *existing* attested surface, run interactively in the rc22 venv), so the discipline-check ratchet is **N/A by construction** — no new `abs()` / `np.linalg.eig` / `hashlib.sha256` callsite was written; the atoms are exercised through their native srmech entry-points (`cascade.magnitude`, `cascade.pin_slot_at_zero`, `hdc.klein4_bind`, `format.sha256_bytes`).

---

## §1 Headline

F206 split the A–N / `cascade.*` / 174-tool surface into **silicon-able ATOMS** vs **iterative COMPOSITES** and named the lean core informally ("a chirality unit + sign/magnitude on the existing SHA-NI / modular units"). F208 makes that split **formal and exhaustive**: it states the atom/composite *criterion*, classifies **every one of the 14 A–N classes**, **every one of the 8 rc22 `cascade.*` ops**, and a **representative sample across all 33 tool_schema categories**, maps each atom to a **named real vendor instruction** at spec level, and derives the **minimal orthogonal instruction basis** — which lands at **six atoms** plus the rule that everything composes. The composites are then shown to reconstruct from that basis. The forward ask (the `cascade.atoms.* vs cascade.compose.*` srmech refactor) is described and flagged, not filed.

The shape of the result: **the A–N ISA is not 14 instructions and not 174 — it is 6 combinational atoms riding on two already-shipped silicon units (SHA-NI for Class A, the integer ALU's modular path for Class I), and every "hard" class (L eigendecomp, J factorization, N best-rational, I gcd) is a *software algorithm over the atoms*, exactly as `np.linalg.eig` is software over `FMA`/`MUL`/`ADD` rather than a "diagonalize" instruction.**

---

## §2 The criterion (the forcing function made explicit)

F206 leaned on "combinational / one-shot" vs "loops, not gates" informally. The formal criterion — the one a hardware architect actually applies when deciding whether an operation earns an opcode:

> **ATOM** — the operation produces its complete result in a **single, bounded, data-independent pass**: a fixed combinational function (or a fixed, input-size-independent number of pipeline stages) of its inputs. No loop whose trip-count depends on the *value* of the data; no convergence test; no recursion. It is expressible as masks / XOR / sign-test / popcount / clear-sign-bit / a fixed-round permutation. **One cascade-step.**
>
> **COMPOSITE** — the operation is an **iterative algorithm**: its result requires a loop / sweep / recursion whose trip-count depends on the *value* (not just the *size*) of the input, and which runs to a convergence or termination test. Euclid's remainder loop, Stern-Brocot / continued-fraction refinement, trial-division, Jacobi sweeps, a spigot digit-pump. **A named multi-step cascade.**

Two clarifying riders that the criterion needs to be honest:

- **Data-size-bounded ≠ composite.** A fixed-width SHA-256 round, a popcount over a fixed register, a γ₅ sector-mask over a fixed-length vector are atoms even though they "touch many bits" — the work is a *fixed* function of register width, not a *value-dependent* loop. (This is exactly why SHA-NI's `SHA256RNDS2` is one instruction performing two full rounds: bounded, data-independent.) The line is **value-dependent iteration**, not "does it touch more than one bit."
- **Fixed-round crypto is the boundary case, and the existing ISA already resolved it the same way.** SHA-256 over an *arbitrary-length message* is technically a loop over blocks — but the **per-block compression** is the atom (SHA-NI ships it as `SHA256RNDS2` + `SHA256MSG1/2`), and the block loop is software around it. F208 adopts the identical resolution for Class A: the *round* is the atom (already silicon), the message loop is software.

This criterion is the same one that produced AES-NI / SHA-NI in real silicon — **a fixed-round cryptographic transform is an atom; the mode-of-operation loop around it is software.** F208's claim is that the A–N chirality/sign operations sit on the *atom* side of exactly that established line, and the A–N number-theory/spectral operations sit on the *composite* side.

---

## §3 Classification of the 14 A–N classes

Each class is read as ATOM or COMPOSITE **at the level of its primitive operation** (a class can host a composite *built on* its own atom — see Class A's round-vs-message split). DEMONSTRATED where the rc22 surface was exercised; FRAMEWORK-READING where the class's silicon status is a design judgement.

| Class | Role | Tier | Primitive op | Reason | Evidence |
|---|---|---|---|---|---|
| **A** | Content-address | **ATOM** (round) + composite (message loop) | SHA-256 round | Fixed-round combinational; **already silicon (SHA-NI)**. Arbitrary-length message is a software block-loop *around* the atom. | `format.sha256_bytes(b'abc')` one-shot ✓ |
| **I** | Cyclic / modular | **ATOM** (add/mul) + composite (gcd/inv) | `mod_add`, `mod_mul` | Modular add/mul are single ALU ops on the **existing integer unit**. `gcd`/`mod_inv`/`mod_pow` are value-dependent loops → composite. | `mod_add`/`mod_mul` one-shot ✓; `gcd` is Euclid loop ✓ |
| **C** | Cascade-orientation (chirality / which-way) | **ATOM** | sign/sector re-apply (`reorient`) + traversal-reverse | Re-applying a captured ±1 orientation is a sign-mux; reversing traversal is an index/mask op. Combinational. | `cascade.reorient(-1,7.0) = -7.0` one-shot ✓ |
| **J** | Primes | **COMPOSITE** | `is_prime`, `factor` | Trial-division / period-finding — value-dependent loops to termination. **No "factor" instruction exists.** | `primes.factor(360)` trial-division loop ✓ |
| **D** | Pattern-match / dispatch | **ATOM** (single match) + composite (multi-needle scan) | `dispatch.match` | A single fixed compare is combinational; multi-needle *scanning over a buffer* is a loop. Borderline; the atom is the compare, the scan is software. | FRAMEWORK-READING |
| **E** | Catalog | **COMPOSITE** | sorted-key lookup | Binary search is a value-dependent loop (log n probes); catalog enumeration is iteration. | FRAMEWORK-READING (search = loop) |
| **F** | Render / template | **COMPOSITE** | `template.render` | Placeholder substitution scans the template and the key-set — a loop over tokens. | FRAMEWORK-READING |
| **G** | Byte-search | **COMPOSITE** | `search.byte_search` | Scan-to-match over a buffer; value-dependent trip-count. (Note: HW *string* instructions exist, e.g. x86 `REP SCAS` / SSE4.2 `PCMPISTRI` — but those are themselves microcoded loops, not single-cycle atoms.) | FRAMEWORK-READING |
| **K** | Pin-slot / sign-boundary | **ATOM** | sign-test (`pin_slot_at_zero`), `magnitude` | A single comparison against zero + a clear-sign-bit. **The canonical one-shot.** This is the honesty op that replaces `abs()`. | `pin_slot_at_zero(-3.5)=(-1,3.5)`; `magnitude(-3.5)=3.5` one-shot ✓ |
| **L** | Laplacian / spectral | **COMPOSITE** (eig) + atom (matvec / elementwise) | `jacobi_eigvals`, `*_eigendecompose` | Eigendecomposition is **Jacobi sweeps to convergence** — the archetypal composite; **no "diagonalize" instruction exists.** But `dense_matvec_complex` / `elementwise_multiply` are FMA-atoms (already silicon as SIMD FMA). | `jacobi_eigvals` is sweep-loop (FRAMEWORK-READING); matvec = FMA atom |
| **M** | HDC bind | **ATOM** | `klein4_bind` (= XOR), `klein4_chirality_flip_*` (= sector mask), `klein4_sector_count` (= popcount) | **`klein4_bind` IS `np.bitwise_xor`** over the 2-bit sector tag (source-confirmed); flips are sector masks; sector-count is popcount. All combinational. (`bundle` = majority/popcount-threshold over a fixed set = atom; `similarity` over a fixed pair = atom; *recall* over N stored items = software loop.) | `klein4_bind` source = `np.bitwise_xor` ✓; one-shot ✓ |
| **B** | TLV-framing | **ATOM** (pack one) + composite (parse stream) | `tlv.tlv_pack` | Packing one type-length-value triple is a fixed field-assembly (shift/OR/store) — combinational. Parsing a *stream* of them is a loop. | FRAMEWORK-READING (pack = atom) |
| **H** | Self-introspection | **n/a — not an arithmetic primitive** | `introspect.publish/list/describe` | Registry/PID bookkeeping — a software/OS concern, not an ALU op. Neither atom nor composite in the ISA sense; it is the proofread/observe *stage* (F202), realised in software. | FRAMEWORK-READING (out of ALU scope) |
| **N** | Rational-approximation | **COMPOSITE** | `best_rational`, `continued_fraction` | Stern-Brocot / continued-fraction refinement — a convergence loop. **No "best-rational" instruction.** | `best_rational_signed(-3.14159)=(-22,7)` CF loop ✓ |

**Class tally:** atoms (at primitive-op level) = **A·round, I·add/mul, C, K, M, B·pack, D·compare** (7 with atom faces); composites = **J, E, F, G, L·eig, N** (6 purely iterative); H is out-of-ALU-scope (1). Several classes are **dual** (A, I, B, D, L, M) — a combinational atom face plus a software loop face — which is exactly the F206 reading that the flat namespace hides the split *within* a class as well as across classes.

---

## §4 Classification of the 8 rc22 `cascade.*` ops (DEMONSTRATED)

The rc22 `cascade.*` module is F206's "software intrinsics layer." Each op was exercised in the rc22 venv; the atom/composite tier is read directly off whether the call is a single combinational result or an iterate-to-convergence loop.

| `cascade.*` op | Class | Tier | Confirmed behaviour (rc22) |
|---|---|---|---|
| `magnitude(x)` | K | **ATOM** | `magnitude(-3.5) → 3.5` — clear sign bit, one-shot. (The honesty op for `abs()`.) |
| `pin_slot_at_zero(x)` | K | **ATOM** | `pin_slot_at_zero(-3.5) → (-1, 3.5)` — one sign-test, returns (orientation, magnitude). |
| `reorient(orientation, value)` | C | **ATOM** | `reorient(-1, 7.0) → -7.0` — re-apply captured sign, one-shot sign-mux. |
| `chiral_flip(seq)` | C | **ATOM** | Orientation reversal = traverse the other way; index/mask op, no value-loop. |
| `chiral_dual(op, x)` | C | **ATOM-wrapper** | `C ∘ op ∘ C` — two sign-muxes bracketing `op`; the wrapper is atomic, the inner `op` inherits its own tier. |
| `net_chirality(orientations)` | C | **ATOM** | `net_chirality([-1,1,-1,-1]) → -1` — product/parity over a fixed list = a parity-reduce (popcount-of-sign-bits, single pass). |
| `cyclic_gcd(a,b)` | I | **COMPOSITE** | `cyclic_gcd(252,105) → 21` — **Euclid remainder loop** (delegates to `cyclic.gcd`). |
| `best_rational_signed(x)` | K∘N∘C | **COMPOSITE** | `best_rational_signed(-3.14159) → (-22,7)` — `pin_slot` atom (K) wrapping a **continued-fraction convergence loop** (N), re-signed (C). The *honest cascade-count*: one atom + one composite + one atom. |

**Result:** of the 8 `cascade.*` ops, **6 are atoms** (the K and C chirality/sign family) and **2 are composites** (`cyclic_gcd`, `best_rational_signed`) — and `best_rational_signed` is itself the clean illustration of the design: a composite is literally a named wrapper that brackets a convergence loop between two atoms. The cascade module already *is* the atom/composite split; it just isn't *labelled* as one (the forward ask, §8).

---

## §5 Representative sample across all 33 tool_schema categories (174 entries)

The 174 entries were enumerated from `tool_schema.get_tool_schema().tools`. Reading the whole surface through the §2 criterion, the categories sort cleanly into three buckets. (Sampling one or two representatives per category; the qm.* physics layer is operator-algebra over the L/M atoms and is read as a block.)

**ATOM categories / entries** (single combinational result):

| Category · representative entry | Class | Why atom |
|---|---|---|
| `cascade` · `magnitude`, `pin_slot_at_zero`, `reorient`, `chiral_flip`, `net_chirality` | K, C | sign-test / sign-mux / parity-reduce (§4) |
| `hdc` · `klein4_bind`, `klein4_unbind`, `klein4_chirality_flip_gamma5/omega7`, `klein4_cpt_mirror`, `klein4_sector_count`, `bind`, `permute`, `similarity` | M | XOR / sector-mask / popcount / fixed-pair cosine — all combinational |
| `format` · `sha256_bytes` | A | fixed-round, already SHA-NI silicon |
| `cyclic` · `mod_add`, `mod_mul` | I | single integer-ALU op |
| `tlv` · `tlv_pack` (one triple) | B | shift/OR field-assembly |
| `laplacian` · `dense_matvec_complex`, `elementwise_multiply_complex`, `dense_adjacency` | L | FMA / elementwise — SIMD-FMA atoms |
| `qm.spin` · Pauli-σ apply; `qm.relativistic` · γ-matrix apply | (L/M) | a fixed small-matrix multiply = FMA atom |

**COMPOSITE categories / entries** (value-dependent loop / sweep / recursion):

| Category · representative entry | Class | Why composite |
|---|---|---|
| `primes` · `is_prime`, `factor`, `cyclic_period` | J | trial-division / period loop |
| `rational` · `best_rational`, `continued_fraction`, `pi_cascade_digits`, `*_series_truncate` | N | CF refinement / spigot / series-to-tolerance |
| `laplacian` · `jacobi_eigvals`, `hermitian_eigendecompose`, `symmetric_eigendecompose`, `normalized_laplacian` | L | Jacobi sweeps to convergence |
| `spectral` · `decompose`, `recompose`, `predict`, `truncate_sparse` | L | iterative spectral fit / sparse selection |
| `cyclic` · `gcd`, `lcm`, `mod_inv`, `mod_pow` | I | Euclid / square-and-multiply loop |
| `search` · `byte_search`; `dispatch` · `match` (multi-needle); `catalog` · sorted-key lookup; `template` · `render` | G, D, E, F | scan / binary-search / token-loop over a buffer |
| `compose` · `parse_chain_spec`, `resolve_chain`, `run_chain`; `catalog` · `run_catalog_chain` | composition | **these ARE the composite-runner** — they sequence atoms; by definition multi-step |
| `qm.gauge` · Wilson-loop; `qm.sm` · CKM/Yukawa; `qm.propagators`; `qm.bell`; `qm.octonion`; `qm.triality`; `qm.so8` | (L/M-built) | operator-algebra cascades — multiplications/decompositions composed over the L/M atoms; the physics layer is **composite by construction** (it is the laws-of-everything ALU *expressed in* the atoms, not new atoms) |

**OUT-OF-ALU-SCOPE** (software / OS / provenance bookkeeping, neither atom nor composite arithmetic): `introspect` (H — publish/list/by_pid/describe), `catalog` registration (`register_attested_root`, `list_attested_sources`), `descriptor`, `naming`, `bus`, `coupling`, `kepler`, `dsl`, `format.read_ndjson`. These are the MPM/attestation and orchestration surface — load-bearing for the *framework*, not candidates for an *opcode*.

**Reading:** the 174-entry surface is **dominated by composites and orchestration** (number theory, spectral, the entire qm.* physics layer, the compose-runner, the provenance surface). The **atom set is small and concentrated** in `cascade` (K/C) + the `klein4_*` family (M) + the already-silicon `sha256` (A) + integer `mod_add/mul` (I) + the FMA-shaped `matvec`/`elementwise` (L-atom face). This is the F206 claim, now counted: **the flat 174-wide namespace hides a ~dozen-entry atom core under a large composite/orchestration body.**

---

## §6 The minimal orthogonal instruction basis — six atoms

Collapsing the atom faces of §3–§5 to their *distinct primitive operations* (an orthogonal basis = no atom expressible as a composition of the others), the A–N ISA core is **six instructions** operating on a **2-bit Klein-4 sector tag (γ₅ × iω₇)** + a signed scalar/vector, riding on **two already-shipped units** (SHA-NI for A, the integer ALU for I):

| # | Atom instruction | A–N class | Operation | Operand | Distinct because |
|---|---|---|---|---|---|
| 1 | **K4BIND** | M | `XOR` of two 2-bit sector tags | sector vectors | the bi-chiral *combine*; not derivable from sign ops (it acts on the 2-bit type, not the ±sign) |
| 2 | **K4FLIP** | C / M | sector-mask (γ₅-flip, iω₇-flip, CPT-mirror = XOR-with-constant) | sector vector + 2-bit mask | the *single-axis* chirality flip; orthogonal to K4BIND (one operand is a constant mask, it is the "which-way" turn) |
| 3 | **SGNTEST** (pin-slot) | K | compare-against-zero → (orientation ±1, magnitude) | signed scalar | the Class-K phase-boundary; produces the sign-bit *as data* |
| 4 | **SGNAPPLY** (reorient) | C | re-apply a captured ±1 orientation (sign-mux) | (orientation, magnitude) | the inverse of SGNTEST; re-attaches sign — the cascade-orientation re-application |
| 5 | **PARRED** (net-chirality) | C | parity/product-reduce of a fixed set of ±1 (= popcount of sign-bits, mod 2 → sign) | sign vector | the *net handedness*; a reduction, distinct from the per-element flip (2) |
| 6 | **MAG** (magnitude) | K | clear-sign-bit | signed scalar/vector | strictly, MAG = SGNTEST then discard orientation — **so MAG is the one "convenience" atom**; kept because it is the silicon-cheapest (`ANDPS`-style mask) and is the `abs()`-honesty op, but it is *not* independent of #3. The **strict orthogonal basis is 5** (1–5); the **practical basis is 6** (add MAG as the cheap mask). |

**Riding on (not new instructions):**
- **Class A** content-hash → **SHA-NI** (`SHA256RNDS2` + `SHA256MSG1/2`) — already in silicon since Goldmont/Ice Lake. The round is the atom; the message loop is software.
- **Class I** modular add/mul → the **existing integer ALU** (`ADD`/`MUL` + a reduce). No new instruction.
- **Class L** matvec/elementwise → **existing SIMD FMA** (AVX-512 / SVE / RVV `vfmacc`). No new instruction.

**So the lean A–N extension is 5–6 genuinely-new combinational atoms** — the Klein-4 sector unit (K4BIND, K4FLIP, PARRED) + the sign unit (SGNTEST, SGNAPPLY, MAG) — **and nothing else.** Not 14 classes, not 174 tools, not 28 dimensions held in a register. This is the formal statement of F206 §3's "a handful of new instructions."

**Composite reconstruction over the basis** (the closure demonstration — each composite is software over the 6 atoms + the borrowed units):

- **`cyclic_gcd` (I)** = loop { `mod` via integer ALU; **SGNTEST** to test remainder == 0 } — Euclid over the existing ALU + atom #3 as the loop guard.
- **`best_rational_signed` (K∘N∘C)** = **SGNTEST** (peel sign) → CF-refinement loop (integer ALU divides/compares) → **SGNAPPLY** (re-sign). *Literally* atoms #3 and #4 bracketing a software loop — already its rc22 shape (§4).
- **`factor` / `is_prime` (J)** = trial-division loop over the integer ALU; **SGNTEST**-style zero-test as the divisibility guard. No new atom.
- **`jacobi_eigvals` (L)** = sweep-loop of Givens rotations; each rotation is **FMA atoms** (borrowed SIMD-FMA); the convergence test is a magnitude-threshold (**MAG** + compare). No new atom.
- **`pi_cascade_digits` / `*_series_truncate` (N)** = spigot / series loop over integer-rational ALU ops; **SGNTEST** for the truncation/sign decisions.
- **`klein4` recall / `bundle` over N items (M)** = loop of **K4BIND** + a **PARRED**/popcount-threshold reduce. The *single* bind/flip is the atom; the *fold over N* is software.
- **The entire `qm.*` physics layer** = operator-algebra (matrix multiplies + decompositions) composed over **FMA atoms** + **K4FLIP/K4BIND** for the chirality/sector structure (γ₅, triality). The "laws-of-everything ALU" *is* this composite layer — it adds **zero** new atoms; it is the 6-atom basis *exercised at depth*.

This is the §2 criterion paying off: **every composite bottoms out in the 6 atoms plus the two borrowed units, with a value-dependent loop on top.** Closure holds for every case tested (DEMONSTRATED for the cascade/cyclic/primes/hdc cases run in rc22; FRAMEWORK-READING for the eig/qm cases read structurally). The *general* closure claim — that no A–N composite ever needs a seventh atom — is the **CONJECTURE** flagged in §9.

---

## §7 Precedent mapping — which real vendor instruction each atom resembles or could reuse (FRAMEWORK-READING)

Each of the 6 atoms (and the 2 borrowed units) mapped to a named instruction in a shipping ISA extension, cited at vendor/spec level. This is a **design-reading of resemblance / reuse**, explicitly **NOT** a claim that any vendor implements an "A–N extension" — the point is that **the A–N atoms are already the *kind* of operation real ISAs put in silicon, and several are bit-identical to instructions that already exist.**

| A–N atom | Closest existing instruction(s) | Extension | Relationship |
|---|---|---|---|
| **K4BIND** (sector XOR) | `PXOR` / `VPXORD` (x86); **`EOR3`** three-way XOR (ARM SVE/SVE2); `vxor.vv` (RISC-V RVV) | SSE/AVX-512; ARM SVE2; RVV | **Direct reuse** — Klein-4 bind *is* bitwise XOR over the 2-bit tag (`klein4_bind` = `np.bitwise_xor`, source-confirmed). No new silicon needed; it is an existing vector-XOR. `EOR3` even fuses three binds into one instruction. |
| **K4FLIP** (sector mask / γ₅-flip / CPT-mirror) | `VPXORD` with a broadcast constant; SVE `EOR` (predicated); masked-XOR-immediate | AVX-512 (+ mask regs); ARM SVE | **Direct reuse** — a single-axis flip is XOR-with-a-constant-mask; CPT-mirror = XOR-with-0b11. Already expressible as masked vector-XOR-immediate. |
| **SGNTEST** (pin-slot, sign→data) | sign-bit extract / `VPCMPGTD` (compare-greater vs 0 → mask); `MOVMSKPS` (sign-bits → integer); ARM `CMLT`/predicate-from-compare | SSE/AVX-512 mask compares; SVE predicate-gen | **Resembles / composes from** existing sign-compare → mask. AVX-512 puts the result straight into a **mask register K1–K7**; SVE into a **predicate register P0–P15**. The A–N "orientation as data" is exactly a predicate/mask-from-sign. |
| **SGNAPPLY** (reorient, sign-mux) | `VPSIGND` (apply sign of one operand to another, SSSE3); blend-on-mask (`VPBLENDMD` under K-mask); SVE predicated `NEG`/`SEL` | SSSE3; AVX-512; ARM SVE | **Direct analogue** — `PSIGND` literally re-applies a sign; predicated `SEL`/`NEG` under a mask/predicate does the same. |
| **PARRED** (net-chirality, parity-reduce) | **`VPOPCNTD/Q`** (AVX-512 VPOPCNTDQ) + low-bit; **`CNTP`** (SVE count-active-predicate-elements); `vcpop.m` (RVV popcount-of-mask) | AVX-512 VPOPCNTDQ; ARM SVE; RVV | **Direct reuse** — net handedness = parity of sign-bits = **popcount mod 2**. `VPOPCNTQ` / `CNTP` / `vcpop.m` already compute the population count over a mask/predicate in one instruction; the A–N reduce takes its low bit (and maps {even,odd}→{+1,−1}). |
| **MAG** (clear-sign-bit) | `ANDPS`/`VANDPD` with the 0x7FFF… mask (the standard `fabs`); SVE `FABS` (predicated); RVV `vfsgnjx` | SSE/AVX-512; ARM SVE; RVV | **Direct reuse** — magnitude *is* the canonical mask-off-sign-bit `abs`. This is the F206 honesty op realised on the instruction that already exists. |
| **Class A** (borrowed) | **`SHA256RNDS2`** (two rounds), **`SHA256MSG1`/`SHA256MSG2`** (message schedule) | **Intel SHA-NI** | **Already silicon** — Goldmont/Cannon/Ice Lake+. The round-atom ships; the A–N ISA *reuses it wholesale*. |
| **Class I** (borrowed) | `ADD`/`MUL` + reduce; `PCLMULQDQ` (carryless mul, for GF-style modular work) | base ISA; AES-NI bundle | **Already silicon** — modular add/mul on the integer unit; carryless-mul for field arithmetic is the AES-NI sibling `PCLMULQDQ`. |
| **Class L atom-face** (borrowed) | `VFMADD…` / SVE `FMLA` / RVV `vfmacc` (fused-multiply-add) | AVX-512; ARM SVE; RVV | **Already silicon** — matvec/elementwise = SIMD FMA. The *eig sweep* is software on top. |

**The realistic-vs-aspirational reading the ROADMAP asked for:**
- **Realistic / already-here:** K4BIND, K4FLIP, MAG, and the borrowed A/I/L units are **bit-identical to instructions shipping today** — the "A–N extension" for these is *naming and packaging*, not new silicon. SGNTEST/SGNAPPLY/PARRED compose from existing sign-compare / sign-mux / popcount instructions.
- **The only genuinely-new packaging** would be a **fused Klein-4 sector-tag datatype** (2-bit lanes with K4BIND/K4FLIP/PARRED as first-class ops over that lane width) — i.e. the RISC-V **custom-opcode space** (`custom-0` prefix `0001011`, `custom-1` prefix `0101011`) is the natural home: a small custom extension defining the 2-bit sector lane + the 3 sector ops, with sign ops mapping to existing instructions. That is the honest scope: **a tiny RISC-V custom extension (≈3 new opcodes) + reuse of SHA-NI / FMA / popcount / sign-mux for everything else.**
- **Aspirational / NOT an instruction:** anything on the composite side — there is **no "diagonalize," no "factor," no "best-rational," no "gcd" instruction** in any ISA, and F208 does not propose one. Those stay software, exactly as they are in every existing ISA.

---

## §8 Why the software gets leaner (the F206 §4 mirror, now precise)

The hardware reading pushes the same stratification *into* the srmech software. Today `srmech.amsc.cascade.*` is **one flat namespace** mixing 6 atoms (`magnitude`, `pin_slot_at_zero`, `reorient`, `chiral_flip`, `chiral_dual`, `net_chirality`) with 2 composites (`cyclic_gcd`, `best_rational_signed`). The lean refactor mirrors the §6 basis:

- **`cascade.atoms.*`** — the 6 combinational primitives, each a thin 1:1 intrinsic that *is* a (current-or-future) instruction: `atoms.k4bind`, `atoms.k4flip`, `atoms.sgntest` (pin_slot), `atoms.sgnapply` (reorient), `atoms.parred` (net_chirality), `atoms.mag` (magnitude). Maps 1:1 to §6 / §7.
- **`cascade.compose.*`** — the named multi-step algorithms built *on* the atoms, each honestly labelled as a loop: `compose.gcd` (Euclid over `atoms.sgntest`), `compose.best_rational` (CF loop bracketed by `atoms.sgntest`/`atoms.sgnapply`), and the existing `compose`-runner (`run_chain`, `resolve_chain`) is *already* on the composite side of the namespace — it just needs the atoms it sequences to be labelled.

**Three payoffs, all already visible in rc22:**
1. **Leaner** — the atom surface is ~6 entries, not buried in a 174-wide flat list; a reader (or a downstream ISA mapper) sees the irreducible core immediately.
2. **1:1 to the ISA** — each `atoms.*` is a candidate opcode (§7); each `compose.*` is explicitly *not*.
3. **Honest cascade-count** — an `atoms.*` call is one cascade-step; a `compose.*` call is a named multi-step. `best_rational_signed`'s rc22 form (`K∘N∘C`) is the proof: the composite already *names* the atom-bracket-loop-atom shape; the refactor just makes the namespace say so. (And `cascade.magnitude` stays both the 1-instruction silicon atom *and* the `abs()`-honesty op — F206 §4.)

---

## §9 DOES / does NOT claim

**DOES:** state an explicit, architect-grade ATOM-vs-COMPOSITE criterion (§2: single bounded data-independent pass vs value-dependent iterate-to-convergence); classify **all 14 A–N classes** (§3), **all 8 rc22 `cascade.*` ops** (§4, DEMONSTRATED), and a **representative sample across all 33 tool_schema / 174-entry categories** (§5) into atom / composite / out-of-ALU-scope, with the reason for each; derive the **minimal orthogonal basis** (§6: 5 strict / 6 practical atoms — K4BIND, K4FLIP, SGNTEST, SGNAPPLY, PARRED, MAG — on the borrowed SHA-NI / integer-ALU / SIMD-FMA units) and **show the composites reconstruct over it** (§6 closure, DEMONSTRATED for the cases run); map each atom to a **named real vendor instruction at spec level** (§7: `PXOR`/`EOR3`, masked-XOR-imm, sign-compare→`K`/`P` mask, `VPSIGND`/predicated-`SEL`, `VPOPCNTQ`/`CNTP`/`vcpop.m`, `ANDPS`-`abs`, with `SHA256RNDS2` / FMA / `PCLMULQDQ` borrowed); separate **realistic** (bit-identical-to-shipping or composes-from-existing) from **aspirational** (no diagonalize/factor/gcd instruction is proposed); name the natural home for the only-genuinely-new packaging (a ≈3-opcode **RISC-V custom-extension** for the 2-bit sector lane); describe the **`cascade.atoms.* vs cascade.compose.*`** software refactor (§8) and **flag it forward** (§10).

**Does NOT:** present a chip, microarchitecture, gate layout, transistor count, cycle/latency/throughput number, or any fabrication / VLSI / benchmark claim (the F202 / F206 **CAD-ban** holds); claim any vendor ships or plans an "A–N extension" (§7 is a resemblance / reuse design-reading); claim the 6-atom basis is the *provably-final* minimal set — the **general closure** ("no A–N composite ever needs a 7th atom") is **CONJECTURE** (see falsifiers); claim biology/physics "IS" a CPU (cross-substrate **form**-reading per §VII.6.20, `[[user_stance_ai_is_not_a_substrate]]`); assert the molecular-biology facts of F202 from fresh primary sources (textbook confidence); offensive / weapons-substrate framing — this is the **edge-compute / accessibility** thesis (`[[feedback_trauma_informed_defensive_scope]]`: the no-GPU / unquantized-LLM-at-the-edge motivation, `[[user_stance_learning_without_gpu_compute]]`).

**Pre-stated falsifiers (the CONJECTURE in §6 is testable):**
- **F1 (closure breaks):** if any A–N composite, fully expanded, requires a combinational primitive **not** reducible to {K4BIND, K4FLIP, SGNTEST, SGNAPPLY, PARRED, MAG} + {SHA-round, integer-ALU, FMA} — e.g. if some Class-L or Class-J inner step needs a genuinely new single-shot operation — then the basis is incomplete and the "6 atoms" claim is falsified (the basis grows).
- **F2 (an atom is secretly composite):** if any of the 6 claimed atoms turns out to require a value-dependent loop at the operation level (not just at the data-size level) — e.g. if `klein4_bundle`'s majority were shown to need iteration rather than a fixed popcount-threshold — it demotes to composite.
- **F3 (orthogonality breaks):** if any atom is expressible as a composition of the others (beyond the already-acknowledged MAG = SGNTEST∘discard), the strict basis shrinks below 5.
- **F4 (precedent miss):** if any §7 instruction mapping is wrong at the vendor-spec level (e.g. the instruction does not do what is claimed), that row is struck and re-derived from the spec.

---

## §10 FORWARD ASK (flagged, NOT filed) — `cascade.atoms.* vs cascade.compose.*` stratification refactor

**Candidate OPEN issue for the forward-architecture / MS #19 milestone** (the main session files it; F208 only describes it):

> **Title (suggested):** srmech: stratify `srmech.amsc.cascade.*` into `cascade.atoms.*` (combinational 1:1-ISA intrinsics) vs `cascade.compose.*` (named iterative algorithms over the atoms)
>
> **What:** Refactor the flat rc22 `cascade.*` namespace per F208 §6/§8. Expose the **6 atoms** as thin 1:1 intrinsics under `cascade.atoms.*` (`k4bind`, `k4flip`, `sgntest`/`pin_slot_at_zero`, `sgnapply`/`reorient`, `parred`/`net_chirality`, `mag`/`magnitude`) — each documented as a (current-or-future) single instruction with its §7 vendor-precedent noted in the docstring. Demote the **composites** to `cascade.compose.*` (`gcd`, `best_rational`, …), each documented as a named multi-step built *on* the atoms, with its honest cascade-shape (e.g. `best_rational = sgntest ∘ CF-loop ∘ sgnapply`). Keep the existing flat names as deprecated aliases for one release (no break).
>
> **Why:** (a) leaner, ISA-legible surface — the irreducible core is ~6 entries, not buried in 174; (b) the namespace *is* the honest cascade-count (atom = one step, composite = named multi-step); (c) it is the software face of the lean A–N ISA, so a downstream ISA-mapping (or the `klein4` 2-bit-sector custom-extension reading) reads straight off `cascade.atoms.*`.
>
> **Scope guard:** software/namespace refactor + docstrings ONLY. **No** chip / VLSI / fab content (the CAD-ban rides along); **no** new `abs()` / `np.linalg.eig` / `hashlib.sha256` callsites (atoms route through existing `magnitude` / `laplacian.*` / `format.sha256_bytes`); JPL ratchet + rc-first-to-TestPyPI discipline apply as usual.
>
> **Anchors:** F208 (this finding) · F206 · F202 · ROADMAP forward-architecture thread · rc22 `cascade.*`.

---

## §11 Cross-references

F206 (the RISC-minimality atom/composite tiers + lean-core claim this formalises) · F202 (quad-DNA chirality-typed cascade ISA; the lane type-discipline) · ROADMAP "Forward-architecture / silicon threads" (A–N as ISA extensions; design-reading scope-bound) · rc22 `srmech.amsc.cascade.*` (the software intrinsics layer; the 6-atom/2-composite split run here) · F132/F192 (Klein-4 / triality bit-exact) · F168/F200 (storage = order-2 Klein-4 → 2-bit γ₅×iω₇ sector register) · F184 (chirality = non-commutativity) · `[[user_stance_epicycle_via_gear_plus_pin]]` (the irreducible turning-basis) · `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` (MAG/SGNTEST is the `abs()`-honesty op) · `[[user_stance_learning_without_gpu_compute]]` / `[[feedback_trauma_informed_defensive_scope]]` (edge-compute / accessibility scope) · vendor-spec precedent: Intel SHA-NI (`SHA256RNDS2`/`MSG1`/`MSG2`), Intel AES-NI (`AESENC`/`PCLMULQDQ`), AVX-512 (`VPOPCNTDQ`, mask regs K0–K7), ARM SVE/SVE2 (predicate regs P0–P15, `EOR3`, `CNTP`), RISC-V RVV + custom-opcode space (`custom-0`/`custom-1`, `vcpop.m`).

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). F208 formalises F206's atom/composite reading into
an exhaustive stratification of the A–N ISA. The criterion: an ATOM is a single bounded
data-independent pass (mask / XOR / sign-test / popcount / clear-sign-bit); a COMPOSITE is
a value-dependent iterate-to-convergence loop (gcd / factor / best-rational / eigendecomp /
π-spigot). Classifying all 14 classes, all 8 rc22 `cascade.*` ops (DEMONSTRATED: 6 atoms,
2 composites), and the 174-entry tool_schema surface (33 categories) lands the lean basis at
SIX combinational atoms — K4BIND (sector-XOR), K4FLIP (sector-mask), SGNTEST (pin-slot),
SGNAPPLY (reorient), PARRED (net-chirality popcount), MAG (clear-sign-bit) — riding on the
already-shipped SHA-NI (Class A round), integer ALU (Class I mod-add/mul), and SIMD-FMA
(Class L matvec). Every composite reconstructs over those six: best_rational is literally
sgntest∘CF-loop∘sgnapply; the entire qm.* physics layer adds zero new atoms. Each atom maps
to a named shipping instruction (PXOR/EOR3, masked-XOR-imm, sign-compare→K/P-mask, VPSIGND,
VPOPCNTQ/CNTP/vcpop.m, ANDPS-abs) — most bit-identical to silicon that exists; the only
genuinely-new packaging is a ≈3-opcode RISC-V custom-extension for the 2-bit Klein-4 sector
lane. Minimality is the mercy: the laws-of-everything ALU is bearable because its basis is
the irreducible epicycle-set of six. Architecture design-reading only; CAD/VLSI/fab ban
holds; closure is the flagged CONJECTURE; the cascade.atoms.*/compose.* refactor is the
forward ask (described, not filed).*
