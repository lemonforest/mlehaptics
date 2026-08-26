# R-RBS-LM Finding 422 (ALU-C) — the whole 14-class A–N vocabulary runs on `{add, sub, shift, sign, compare, xor/and}`: 7 arithmetic classes (A,C,I,J,K,M,N) reconstructed BIT-EXACT against the shipped srmech 0.7.1 primitives on the lean-ALU op-set; 6 (B,D,E,F,G,H) are concat/compare/index (no arithmetic to reduce); L = CORDIC (ALU-D)

**Date:** 2026-06-06
**Arc:** RBS-LM · ALU-native A–N thread (F392/F393 → ALU-A/F407 → ALU-D/F402 → **ALU-C/F422**); **srmech-RUN (sanctioned: live 0.7.1, hold satisfied)**
**Provenance:** `R-RBS-LM-ALU-C_thirteen_classes_add_sub_shift_sign_provenance.py` (committed; 9/9 checks, honesty-self-audited for `*`/`/`/`abs`/`math`)
**Composes:** **F393** (the per-class reduction map / ALU-B spec; the hypothesis) · **F392** (divide = shift-subtract + handedness; no divide primitive) · **F407 / ALU-A** (CORDIC/Booth/**Stein binary-GCD**/FIPS SHA-256 attested by k=3 triality — *reducibility, not actuality*) · **F402 / ALU-D** (Class-L eigendecomp = Jacobi = CORDIC = shift-add+sign, numpy-free) · **F404** (2:4:8 = 2ⁿ shift-exact; 1:3:7 = 2ⁿ−1 Mersenne — *why* the substrate is add/shift) · the **lean-ISA arc** #751/F208 (6 atom intrinsics), #761/F220 (6 order-2 + 1 order-3 = chirality-complete core), F206/F217 (the Klein-4 2-bit lane is the only genuinely-new silicon) — *convergent rederivation, cross-referenced not re-derived*
**→ closes ALU-C (the last walkable leg of the ALU-native thread); with ALU-A/B/D this completes the F393 hypothesis empirically.**

---

## The hypothesis (F393) and what ALU-C tests
F393: every A–N class reduces to **{add, subtract, shift, sign(handedness=C/K), compare, xor·and}** — **no multiply unit, no divide unit, no FPU transcendental.** ALU-A attested the CS reductions (CORDIC/Booth/Stein/FIPS) as *reducibility* (real FPUs ship FMA — the claim is "can be built from," not "is built from"). ALU-D demonstrated the hard one (Class L = Jacobi = CORDIC). **ALU-C is the remaining empirical leg: take the shipped srmech 0.7.1 primitive for each class and reproduce its output bit-exact using ONLY the lean-ALU op-set.**

## Method (no-leaning, falsifiable)
The **srmech op is the ground truth**; the **ALU cascade is the claim**; assert **bit-exact equality**. The reconstruction is restricted to `+ - << >> & | ^ ~ == < >` (+ `bit_length` = count-leading-zeros, a shift atom) — **honesty-self-audited**: no `*`, `/`, `abs()`, or `math.*` appears in any reconstruction function (the audit is in the provenance run). A class **falsifies** if its srmech output cannot be reproduced on that op-set.

## Result — 7 arithmetic classes, BIT-EXACT (9/9 checks)
| Class | Shipped srmech 0.7.1 op | Lean-ALU reconstruction | Atoms used |
|---|---|---|---|
| **A** content-hash | `format.sha256_bytes` | FIPS 180-4 vectors (`""`, `"abc"`) match; compression = add mod 2³² / rotr / shr / xor / and / not | add · shift · xor · and · not |
| **C** chirality | `cascade.net_chirality`, `reorient` | product-of-signs = **XOR-reduce of sign bits**; reorient(−1) = `(~x)+1` | xor · add · compare |
| **I** cyclic | `cyclic.gcd` | **Stein 1967 binary GCD** (F407-attested) | shift · subtract · compare |
| **J** primes | `primes.is_prime`, `factor` | trial division; **mod = restoring shift-subtract remainder**; bound = bit-by-bit `isqrt` | shift · subtract · compare |
| **K** pin-slot | `cascade.magnitude`, `pin_slot_at_zero` | `\|x\| = (x ^ s) − s`, `s = sign(x)` — **never `abs()`** (Class-K honesty) | sign · xor · subtract |
| **M** HDC bind | `hdc.bind`, `similarity` | bind **IS** byte-wise XOR (bit-exact); similarity ← `popcount(xor)` = shift-add tree | xor · add · shift |
| **N** rational | `rational.best_rational` | reduce = **binary-GCD (I)** + exact **shift-subtract division** | shift · subtract · compare |

All seven pass exactly against the live surface. The two structurally-deepest reductions are **K** (the magnitude that the whole no-`abs()` discipline rests on — it really is just sign-test + conditional two's-complement negate) and **N** (best-rational = `gcd` + exact-divide, both shift-subtract — so the Class-N "continuous" rational anchor bottoms out in the same shift-subtract as everything else, consistent with F404's π-as-cascade).

## The other 6 + L (no arithmetic to reduce)
| Class | Op | Why it's already lean |
|---|---|---|
| **B** TLV-framing | `tlv.tlv_pack` | length-prefix = byte **concat** + a length **add**; no arithmetic beyond an offset add |
| **D** pattern-match | `dispatch` | equality = **subtract + test-zero** (compare) |
| **E** catalog | `catalog` | enumeration = **index-add** (base + offset; fixed 2ⁿ stride = shift) |
| **F** render | `template` | serialization = **shift + mask + concat** |
| **G** byte-search | `search` | scan = **compare** (subtract + test) |
| **H** introspect | structural | graph/struct walk = **pointer-add**; no numeric op |
| **L** Laplacian | `laplacian.*` | eigendecomp = **Jacobi = CORDIC = shift-add+sign** (ALU-D / F402, numpy-free) |

These six carry no multiply/divide to begin with — there is nothing to *reduce*; they are concat/compare/index by construction. L is the one that *looks* like it needs an FPU (eigenvalues) and is exactly where CORDIC earns its keep (ALU-D).

## Why this matters (and what it is NOT)
- **It is REDUCIBILITY, not actuality (F407 discipline carried forward).** The claim is "the entire A–N vocabulary *can* run with no multiply/divide unit and no FPU" — not that srmech's C library avoids `*` (it ships fast paths). The lean-ALU op-set is the **substrate floor**: a machine with only add/sub/shift/sign/compare/xor computes all 14 classes. This is the silicon reading of F404 (2:4:8 = 2ⁿ shift-exact; 1:3:7 = Mersenne) — the framework's "no divide/multiply primitive" (CLAUDE.md §0) made concrete on the live surface.
- **Convergent, not novel.** The lean-ISA arc already reached "6 atoms + a Klein-4 2-bit lane" from the silicon side (#751/F208, #761/F220, F206/F217). ALU-C **cross-references** that; what F392/F393/ALU-C add is the **CORDIC reduction of the continuous/transcendental ops** (trig/rotation/sqrt → Class-L) — the part the lean-ISA arc didn't close. This finding closes it empirically.
- **Class-K honesty in action.** The `K` row is the discipline's own foundation reduced to its atoms: `|x|` is sign + conditional-negate, never `abs()`. The demo *is* the rule.

## Falsifiable form (pre-stated; not leaning — F394)
- **Bit-exactness:** any of the 7 arithmetic classes whose srmech output a lean-ALU reconstruction cannot reproduce → that class needs an op outside `{add,sub,shift,sign,compare,xor/and}` → the F393 hypothesis is falsified for it. (0/7 falsified here; falsify by counterexample input.)
- **Coverage honesty:** the demo uses small/representative inputs (test vectors, modest integers, 32-byte HVs), not exhaustive ranges; a fuzz over wide input ranges would harden the bit-exact claim (flagged, not claimed exhaustive).
- **"No arithmetic" for B/D/E/F/G/H** is argued structurally, not reconstructed — if any of those six is shown to require a multiply/divide in its srmech implementation's *essential* output (not a fast-path), the structural argument weakens for it.

## Verdict
**The whole 14-class A–N vocabulary runs on the lean-ALU op-set `{add, sub, shift, sign, compare, xor/and}`.** Seven arithmetic-bearing classes (**A, C, I, J, K, M, N**) are reconstructed **bit-exact** against the shipped srmech 0.7.1 primitives using only those atoms (9/9 checks, honesty-self-audited); six (**B, D, E, F, G, H**) are concat/compare/index with no arithmetic to reduce; **L** is CORDIC (ALU-D/F402). This **completes the F393 hypothesis empirically** (ALU-A attested, ALU-B mapped, ALU-D demonstrated L, ALU-C now demonstrates the rest) and is the silicon reading of **F404** (2ⁿ shift-exact / Mersenne) — *no divide/multiply primitive, no FPU transcendental, the framework's substrate floor made concrete on the live surface.* Reducibility not actuality (F407); convergent with the lean-ISA arc, not novel. Favored, not privileged (F398); wide-range fuzz is the honest residue.
