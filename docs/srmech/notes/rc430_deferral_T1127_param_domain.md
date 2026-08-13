# rc430 — why the `ToolParameter` domain field is DEFERRED to rc431 (`#T1127`)

rc430 shipped the **frame axis** (`ToolEntry.frame_scope` / `.frame_axis`) and the
**(op, param)-keyed valid-argument provider** that closes `#T1094`. It did **not** ship the
per-parameter domain-constraint field that `#T1127` was opened for. This note records why, so the
decision can be judged rather than inherited, and so rc431 does not re-derive it.

The short version: **the field's stated justification did not survive measurement, and its price is
an ABI bump.** Neither fact alone would defer it. Together they do.

---

## 1. The headline justification is RETRACTED

`#T1127` opened on the claim that the semigroup census — how many srmech ops actually destroy
information — is permanently bounded by `ToolParameter` publishing no domain constraint. Census
instrument v1 was refuted by its own negative control: `cyclic_mod_add`, provably a permutation,
classified `SEMIGROUP_NOT_GROUP` because the sweep bound a modulus **smaller than the carrier it
enumerated**.

That is a defect **in the instrument**, not in the registry.

| Measurement (rc430 scope round S2, 913 records, 9 pre-registered falsifiers, all PASS) | Result |
|---|---|
| Tier A measurable self-maps, rc427 carrier ladder | **15 / 245** |
| Tier A under window-free **orbit closure** over arguments already in `example["worked"]` | **30** |
| Tier B, same repair | **UNSUPPORTED → 50 / 289** |
| `cyclic_mod_add` — the control that refuted v1 | **returns GROUP** |

**The largest available step needs no registry change at all.** It needs the ladder replaced by orbit
closure over exemplars srmech already ships.

What a domain field would add on top: **+8 ops on a denominator of 245** (the 59 `NO_VALID_ARG` ops at
the observed recovery rate). The optimistic projection (133) rests entirely on **domain
enumeration** — and the blocking `VACUOUS` bucket is dominated by `list` / `Mat` / `HV`, with **2**
typed `int` cases. A scalar min/max bound, the easiest thing such a vocabulary expresses, addresses
almost none of it. What that bucket needs is a **constructor** (element type + length + structure),
which is a different object than a constraint.

## 2. The inter-parameter relation claim does not survive either

Two independent extractors agree, and the answer is negative where it matters:

- **S1** (own-body AST, depth ≤ 2): 24 relational constraints extract, **17** of them the
  `len(a) != len(b)` shape-agreement guard. **Exactly two ordering relations exist in the entire
  registry** (`log1p` / `atan_series_truncate`, the Taylor radius) and **neither is a
  modulus-vs-carrier-size bound**.
- **S2** (delegation depth 3): **40 / 655** ops carry any true inter-parameter relation.

The vocabulary *can* express `le_param`. **The constraint the census needed is not in the code.**
rc431's docstring must carry that sentence in substance.

## 3. The price: an ABI bump, and 602 of 655 entries moving

`frame_scope` was ABI-additive; a `ToolParameter` field is **not**, and the difference was measured
rather than assumed.

`srmech_tool_entry_t` holds `const srmech_tool_param_t *params` + `param_count` — but **the caller
strides that array itself**: `srmech_invoke.c:1589`, `:1606`, `:1612` all do `e->params[i]`, and there
is **no `srmech_tool_param_get()` accessor** in the public header.

```
sizeof(param_old)  = 32     {name, type, required, summary}
sizeof(param_newA) = 40     + one const char *
sizeof(param_newB) = 56     + ptr/array/count  (the reads_lane shape)
old header computes params[1] at byte 32; new table lays it at 40 / 56
offsetof(entry, params)  old 8  new 8      <- why frame_scope IS additive
```

**A wire-format change to exported data. `SRMECH_ABI_VERSION` must go 14 → 15.**

Ripple of that bump: `c/include/srmech.h:280`; `srmech/_native/__init__.py:191`; and **15 test files**
pinning `== 14` — `test_bus.py` (×2), `test_bus_cipher_transport_c_rc179`, `test_bus_pubsub_c_rc180`,
`test_cooccurrence_directed_rc248`, `test_dsl_chain_c_rc181`, `test_dsl_combinators_c_rc182`,
`test_eulerian_rc250`, `test_genome_cap_foundation_c_rc196`, `test_genome_catalog_body_bound_rc337`,
`test_genome_multikernel_c_rc198`, `test_genome_read_bound_global_rc342`, `test_graph_to_kernel_rc249`,
`test_json_read_selfhost_rc401`, `test_klein4_regime_split_rc290`, `test_lightweight_parity`.

> Two of those carry **stale messages** saying "should be 12" while asserting 14
> (`test_bus.py:1060`, `test_bus_cipher_transport_c_rc179.py:64`). Fix the prose when rc431 touches
> them; do not propagate it.

**A second cost the entry route does not have.** `ToolEntry.to_jsonable` renders params as bare
`asdict(p)`, which has **no key omission** — measured, a default-valued field lands on every param:

```
registry 655 entries | 1655 params | 602 entries with >=1 param
entries whose canonical JSON moves : 602 / 655      (frame_scope moved: 9)
tool_schema_sha256 pre-image  2,888,518 -> 2,908,378 bytes  (+19,860)
```

Getting rc347's cheapness requires restructuring `to_jsonable` **and** mirroring the omission in
`ts_emit_param` (`srmech_tool_schema.c:208-220`, sorted `name/required/summary/type`).
**Key-sort position depends on the field name chosen** — `domain`/`constraint`/`bounds` sort before
`name`; `spec`/`requires` between `required` and `summary`; `valid` after `type`. That is a design
constraint, not an afterthought.

## 4. Soundness: derive at depth 0; delegated constraints are ADVISORY

`derived, therefore safe` is measurably false.

| Derivation | Soundness (witness violating the bound while satisfying every other bound) |
|---|---|
| depth-0 only | **20 / 20 CONFIRMED (1.000)**, 399 constraints |
| all depths (delegated) | **34 / 35 (0.971)** — one **VIOLATED**, 632 constraints |

The violation is the finding. `pi_cascade_digits` derived `gt(num_digits, 0)` from an `assert` inside
`_native.pi_archimedes_c` — a **conditionally reached** callee. The op legitimately returns `"3."` for
`0` and never calls it. Delegation is **path-insensitive**: it attributes a callee's guard as
unconditional, producing a bound **stricter than the truth** — the same failure direction as the
census's too-small modulus.

Extraction ceiling, for planning: 396/655 ops carry a guard at depth ≤ 2; 1408 guard sites; 757
(53.8%) lift into a closed vocabulary, but **510 (36.2%) are net-new** — 247 yield only `is_type`,
which restates what `ToolParameter.type` already publishes.

**Neither extractor suffices alone.** Measured over the 59 int-only-param ops: AST-and-runtime agree
on 38; **16 are recovered by runtime refusal only** (their guard lives past the op's own body —
`cyclic_mod_add`'s is in `srmech.math.cyclic.mod_add`, and its bound is stated only in the
*docstring*); and **2 carry a guard on an axis the probe did not perturb**. Verdict: **BOUNDED**.

## 5. What rc431 inherits

1. **Derive at depth 0** (sound); treat the 632 delegated constraints as **advisory** until path
   sensitivity exists.
2. **Gate on a probe that EXECUTES the candidate bound** — feed a violating value, require the
   refusal. A derived field is not self-maintaining by being derived.
3. **Ship the retraction with the field.** The docstring must say the field cannot fix the semigroup
   census, and why.
4. **Isolate the ABI bump** so the header record names one cause.
5. **Do not write a relation vocabulary** (§2).
6. `#T1094`'s provider (`tools/example_args.py`) already exists and is the natural probe substrate.

## 6. And one thing rc430 measured that changes the shape of the problem

The rc430 harvest found that **`example["worked"]` does not bind every parameter it appears to**.
Only **3 of 33 path-ish parameters** got a harvested value, because the genome snippets deliberately
leave `path` unbound — the shipped `tests/worked_examples_result.ndjson` has been recording that as
`NameError: name 'path' is not defined` all along, under rc354's ceiling.

So the exemplar corpus is a **weaker** argument source than the scope round assumed (368 of 655 ops
yield a JSON-carriable binding; 440 yield any binding at all). rc431 should price its probe against
those numbers, not against the 570 entries that merely *have* a snippet.
