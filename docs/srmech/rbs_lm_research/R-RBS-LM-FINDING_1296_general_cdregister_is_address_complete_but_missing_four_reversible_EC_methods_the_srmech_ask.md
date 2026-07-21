# F1296 — the CDRegister op-coverage audit (for the srmech ask): the general `cd_register` is **address-complete at every rung 2→256**, but it **drops four methods** the dim-16 `sedenion_register` has — `couple_working`, `uncouple_working`, `carry`, `correct` — and its **`working_block` is frozen at 8 slots at every dim.** So it can *address* any rung but cannot do the *reversible-coupling + error-corrected* work the SedenionRegister was built for.

**User (2026-07-21):** *"what you said earlier about not all ops available for cdregister … make sure, before we bring it up to srmech, of what operations don't work yet with general purpose cdregister."*

## What works — addressing, completely
Audited every method × every CD dim on rc299:

| method | 2 | 4 | 8 | 16 | 32 | 64 | 128 | 256 |
|---|---|---|---|---|---|---|---|---|
| `write` / `read` / `slots` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `navmap` / `navigate` / `is_navigable` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `materialize` / `carry_block` / `working_block` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Addressing is **complete and correct to dim 256** (F1285's 100 % round-trip). *(The one apparent dim-2 `write` failure in the first pass was my test writing to slot 2 in a 2-slot register — correctly rejected, not a bug.)*

## What is missing — the reversible + EC surface
Set-difference of the two registers' methods:
```
on SedenionRegister, ABSENT on general CDRegister:  carry, correct, couple_working, uncouple_working
```
| missing method | role |
|---|---|
| `couple_working(vals)` | bind ≤7 values into one octonion working word — **bit-exact reversible** |
| `uncouple_working(octonion)` | the exact inverse |
| `carry(overflow_bits, n=3)` | encode overflow past the ≤7 set into a **Hamming(2ⁿ−1) EC block** |
| `correct(codeword)` | locate + correct a single-bit error in the EC block |

## The subtler gap — the working block does not scale
`working_block` returns `(0,1,…,7)` at **every** dim — 8 at dim 16, still 8 at dim 256 — while `carry_block` absorbs everything above 7. So the reversible-working-word is pinned to the **octonion 8** no matter how wide the register is. Porting `couple_working` verbatim would still cap it at ≤7 values. **The addressing generalised to 256; the reversible-coupling concept did not.** Whether that pin is a design choice or an oversight is not stated anywhere — which is itself worth surfacing.

## The two asks (UPSTREAM §111)
1. **Port the four methods** onto the general `CDRegister` — they are shipped, just only on the dim-16 class.
2. **Decide and document** whether the working/carry split should scale with dim or stay pinned at 8 by design. Right now it is pinned silently.

Neither blocks addressing; both block the general register being a **drop-in for the SedenionRegister's full role**. Filing precisely so the srmech ask names exactly what is absent, not "the register feels incomplete."

Composes **F1285** (round-trip to 256), **F1275** (the register arc), **F1286** (which deleted our hand-rolled copy in favour of the shipped one — this is the follow-up gap-list), UPSTREAM §111.
