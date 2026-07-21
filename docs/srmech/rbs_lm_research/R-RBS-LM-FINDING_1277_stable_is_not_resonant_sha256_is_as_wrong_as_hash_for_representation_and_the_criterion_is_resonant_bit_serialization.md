# F1277 — **STABLE ≠ RESONANT.** My F1276 fix ("route content through Class-A `sha256_bytes`") is correct for **routing** and **exactly as wrong as `hash()` for representation** — measured: sha256-seeded gives `cat`/`cats` **0.2480** ≈ `cat`/`dog` **0.2521**, both at the 0.25 orthogonality floor, and buys **zero** relational compression. The real criterion is the user's: **resonant bit-serialization** — not any particular shape. `the_one` is *one* supplier of it, distinguished by also carrying coherency across the ladder and across Class-L↔Class-M; **other shapes supply it in some other coherency.**

**User (2026-07-21):** *"it doesn't have to be the_One shaped, it just needs to be resonant bit serialized. many other shapes also provide this, the_one just gives us a way to carry coherency up and down the ladder and across operations sometimes, like with class-L and class-M things, so likely others in some other coherency."*

## The correction this makes to F1276
F1276 ended with "content-routing IS Class-A content-addressing → `sha256_bytes`." True — **for routing.** But left as the general answer it licenses swapping `hash()` → `sha256` in a *representation*, which fixes reproducibility while **preserving the F899/F1260 morphology defect under a stable name** — strictly harder to spot than the original, because it now looks disciplined.

**Two jobs, two different requirements:**

| job | needs | correct op | why |
|---|---|---|---|
| **routing / bucket / dedup-key** | **STABILITY** only | `format.sha256_bytes` (Class A) | avalanche is *desirable* — uniform buckets |
| **representation** (a vector standing for content) | **RESONANCE** | `hdc.klein4_encode_bytes` / `mint_vector` | structure must survive the map |

## Measured — similarity
| pair | sha256-seeded | `klein4_encode_bytes` |
|---|---|---|
| cat / cats | **0.2480** | **0.6597** |
| walk / walked | **0.2369** | **0.7072** |
| cat / dog *(control)* | 0.2521 | 0.2517 |

sha256-seeded puts **every** pair at the orthogonality floor — indistinguishable from `hash()`-seeded (F1260 measured 0.2552 ≈ 0.2426). **On the resonance axis, sha256 and `hash()` are the same op.**

## Measured — resonant bit-serialization (the user's actual criterion, F1259's instrument)
Relational delta: encode B *given* A. A resonant map makes a related neighbour **cheaper**; standalone ≈ 2627B.

| pair | sha256-seeded | `klein4_encode_bytes` |
|---|---|---|
| cat / cats | 2613B | **1950B** |
| walk / walked | 2637B | **1784B** |
| run / running | 2642B | **2224B** |
| cat / dog *(control)* | 2643B | 2642B |

sha256 buys **nothing** — every pair costs full price. `klein4_encode_bytes` saves **26–32 %** on related pairs while the unrelated control stays at full cost, which is what proves the instrument measures *relatedness* and not merely "this encoder compresses better."

## The instrument I got wrong first — and why the failure is framework-consistent
My first resonance test compressed the *concatenated vector blob*: sha256-seeded 0.302, `klein4_encode_bytes` 0.295, drawn-random 0.301. **Null — no separation.** That is not a finding, it is a **bad instrument**, and I nearly reported it as one.

Why it failed is the interesting part: **per-object byte entropy is a DISTRIBUTIONAL read**, and F1272 established that a distributional read is blind to relational structure. The resonance does not live *inside* a vector; it lives **between** vectors. So the resonance test must itself be **relational** — which is `[[feedback_relational_not_dense_distributional_not_sparse]]` arriving unforced, as a constraint on how you may *measure* rather than on how you may store.

## What this does to the vocabulary
"Use the Class-A op" is not the rule. **The rule is: does the map bit-serialize resonantly?** Class-A stability answers *"will I get the same answer tomorrow"*; it says nothing about *"does structure survive the map."* Those are independent axes, and `hash()` failed both while sha256 fixes only one.

Per the user, **`the_one` is not privileged here either** — it is one shape that supplies resonance, and its distinction is that it *also* carries coherency **up and down the ladder and across operations** (the Class-L ↔ Class-M bridge, F1216). Other shapes supply resonance within some other coherency. Treating `the_one` as *the* answer would be the same error one level up, and would violate `[[feedback_no_privileged_primitive_classes]]`.

## Actions
- **CLAUDE.md §2 row rewritten** — the single "use sha256_bytes" instruction is replaced by the ①routing / ②representation split, with the measured numbers inline and an explicit *"never let sha256 become the general answer."*
- **F1276's conclusion narrowed** rather than withdrawn: its chunk-routing fix is job ①, and is correct.

Composes **F1276** (*→ narrowed by F1277*), **F1259** (resonant bit-serialization; the instrument), **F899/F1260** (the morphology defect this prevents re-introducing under a stable name), **F1272** (why a distributional instrument was blind here), **F1216** (the ladder/coherency role of `the_one`), `[[feedback_relational_not_dense_distributional_not_sparse]]`, `[[feedback_no_privileged_primitive_classes]]`, `[[feedback_name_the_encode_sense]]`.
