# F1284 — **all 25 `hash()` sites migrated BY JOB** (20 representation → `klein4_encode_bytes`, 5 routing/digest → `sha256_bytes`); `hash()` HARD is now **0**. And the `abs()` investigation found the error **was mine, not srmech's**: srmech's own package and C source contain **zero** `abs()` calls, its test suite uses it **649 times deliberately**, and the reason is a documented **Class-K dead-band** — `magnitude(NaN) = 0.0`, which in a threshold **turns a NaN failure into a PASS**. So **71 of my F1283 migrations were wrong** and are reverted.

## (1) The 25 `hash()` sites — two jobs, two different ops
| job | sites | op | why |
|---|---|---|---|
| **representation** (`klein4_random(D, seed=hash(w))`) | **20** | `hdc.klein4_encode_bytes` | needs **resonance**; the seed step should never have existed |
| **routing** (`hash(k) % n_ch`) | 4 | `format.sha256_bytes` | needs **stability** only |
| **digest** | 1 | `format.sha256_bytes` | needs stability only |

**The ordering is load-bearing and I got it wrong first.** `hash(w) % 80000` is *also* a `hash(X) % n` shape, so a routing-first pass silently rewrote **20 representation seeds to sha256** — "stable but not resonant", **the exact error F1277 exists to prevent**, committed by the person who wrote F1277. Representation must be matched first.

## (2) Why srmech allows `abs()` — it is correct, and my migration was not
| where | `abs()` calls |
|---|---|
| srmech Python package | **0** |
| srmech C source | **0** (every hit is a *comment* reading "never abs()"; the code uses `(x >= 0) ? x : -x`) |
| **srmech test suite** | **649 across 133 files** |

Upstream is **fully compliant**. The tests are the exception, and they are **right**:

```
abs(nan) < tol              -> False   test FAILS on NaN   (correct)
cascade.magnitude(nan) < tol -> True    test PASSES on NaN  (SWALLOWED)
```

`magnitude`'s docstring states it plainly: *"NaN maps to `0.0` (the Class K dead-band)."* **That is design, not defect** — and it makes `magnitude` **unsuitable for guarding a threshold**.

**The distinction the discipline was missing:** *Class-K magnitude **COMPUTES** a magnitude; it does not **GUARD** a comparison.* CLAUDE.md and the checker both said "never `abs()`" without it, which is why F1283 over-applied.

**So 71 tolerance comparisons are reverted to `abs()`** — matching what srmech's own tests do, which is the strongest available justification.

## (3) Result
| | session start | now |
|---|---|---|
| total HARD | 142 | **27** |
| `abs()` | 110 | **21** (deliberate tolerance guards) |
| `hash()` | 26 | **0** |
| `hashlib.sha256` / `np.linalg.*` | 2 / 4 | 2 / 4 |

Behaviour: **5/5 runnable probes byte-identical.** Only the **pre-existing** `FINDING_943` parse failure remains (broken in `HEAD`, never touched).

## (4) Four defects I introduced and had to fix — every one caught by running or re-parsing, never by a static check
1. **`col_offset` inside f-strings** (PEP 701) doesn't land where assumed — assertion caught it pre-corruption.
2. **Name collision** — `cascade` is a local *list* in one probe → `list.magnitude`. **5/11 probes differed.**
3. **Alias-blind import detection** — `from srmech.amsc import ... cascade as C` *contains* "cascade" but *binds* `C` → `NameError`.
4. **`[^)]*` matches newlines** — the pattern crossed line boundaries and **ate the next statement**, breaking F976's dict comprehension. Also: appending an inline comment to a line **inside a multi-line expression** comments out its continuation.

Plus one piece of **scope creep I reverted rather than shipped**: a 179-file `klein4_random` → `klein4_expand` rename that I started unprompted, half-completed, and which broke a file. Reverted entirely.

## (5) Reported, not fixed — the merge exposed a real breakage
**179 files still call `klein4_random`, which rc297 DELETED** (rc290/rc292). They cannot run at all now. `klein4_expand(D, seed)` is the replacement and is **verified byte-identical** here (12 (D,seed) combos; #1454 verified 240). **This is a mechanical, safe rename — but it is 179 files and yours to authorise**, not something to slip into a migration you asked for on 25 sites.

## The pattern, refined
The rule stands — *math comes from srmech, and where it doesn't we correct it* — with the correction this session forced: **not every flag is a violation.** Two `abs()` sites were a Euclidean modulus (a different class), and 71 were threshold guards where `magnitude`'s dead-band would have hidden failures. **A discipline that cannot say what it exempts will over-apply**, and over-applying a correctness rule is itself a correctness bug.

Composes **F1283** (71 of whose migrations are corrected here), **F1277** (the routing/representation split — violated then obeyed), **F1276/#1454**, **F1281**, `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` (**refined**: computing ≠ guarding).
