# Q₈ quaternion-substrate migration — what to nix locally, and how to pick back up

> **Premise (user, 2026-07-23):** the genome was found **not cascade-faithful** and is being made faithful — a breaking change **still in progress** upstream. *"The genome no longer has a quaternion **reader** — it is a quaternion **substrate**, exactly the bar you set with 'cascade faithful, and that means the substrate as well.'"*
>
> This note is the changelog preview + surface introspection + the local-side action list. **No local code is changed here** — it records what needs nixing and how to resume. Introspected against a fresh **rc312** venv (`/tmp/srmech_312`); our working venv is still **rc299** (13 rcs behind — the arc landed in rc308–rc312). Composes F1306 / F1302 / F1213 / F1304, and the gauge asks (`R-RBS-LM-SRMECHASKS_…`, `bc6e643c`).

---

## 1 — What changed upstream (rc308 → rc312, the Q₈ arc)

| rc | change | on-disk break? |
|---|---|---|
| rc308 | `quaternion_left_mult` etc. — continuous-ℍ Class-L compositions | no |
| rc309 | `srmech_quaternion_conjugate` + **quaternion cycle holonomy** + the **re-gauge-invariance proof gate** (only the *conjugacy class* of a non-abelian cycle product is gauge-invariant) | no |
| **rc310** | **`amsc.q8`** — the discrete quaternion group Q₈={±1,±i,±j,±k} as 3-bit bytes: `q8_mult`/`q8_conjugate`/`q8_bind`/`q8_project_v4`. **THE contract: π:Q₈→V4 exact** — `(q8_mult(a,b)&3)==((a&3)^(b&3))` for all 64 pairs; V4=`q&3` is the F380/R21 homomorphism. Genuinely non-abelian (`q8_mult(1,2)=3 ≠ q8_mult(2,1)=7`). | no (VERSION stays 15) |
| **rc311** | wire Q₈ into the genome as `element_type=Q8 (=1)` beside `klein4 (=0)`. Q₈ = the non-abelian central extension `1→Z₂→Q₈→V4→1`; a helix turn is **right-coupled by the group product** `stored=q8_mult(turn, one)`, recall is the **group inverse** `q8_mult(stored, q8_conjugate(one))` — **not** klein4's XOR self-inverse. No self-inverse safety net → wrong coupling **side** corrupts silently → **hard runtime assert** `_q8_side_ok`. Q₈ turns are **sectors=8 (OCT)**; klein4 stays sectors=4. New C peers `srmech_genome_recall_q8`/`…recover_diploid_q8`. | no (VERSION stays 15; the Q₈ `one` is passed via `element_type=`, not stored) |
| **rc312** | **`GENOME_FORMAT_VERSION 15→16` — the breaking on-disk migration.** §55 packed-turn layer gains a 2nd codec: Q₈ 3-bit-packs under marker **`0x38`** ('8'), klein4 2-bit under **`0x51`** ('Q'). Manifest gains a **`carrier`** field ("klein4"/"q8") derived from the body scan. **klein4 body is BYTE-IDENTICAL to v15** — only the manifest `format_version`+`carrier` move. `upgrade_v15_to_v16(path, *, coupling=None)` re-stamps a v15 klein4 genome to v16 with **no body repack** (a v15 klein4 turn IS the winding-0 slice of a v16 Q₈ turn; `q8_project_v4(turn)==turn`, all sign bits 0). ABI stays 10 (data format, not C signature). | **YES — v15→v16** |

Confirmed live at rc312: `GENOME_FORMAT_VERSION==16`, markers `0x51`/`0x38`, `ELEMENT_TYPE_KLEIN4/Q8 = 0/1`, `upgrade_v15_to_v16` present, `amsc.q8` = {q8_mult, q8_conjugate, q8_bind, q8_project_v4}. Every genome op gained `element_type=0` (default klein4): `quad_turn`, `chromosome`, `recall`, `genome_save`, `recover_diploid`.

**Citations (already in-package, DERIVED not attested-new):** Baez, *The Octonions* (Bull. AMS 39, 2002; arXiv:math/0105155 §1) for the Q₈/Cayley–Dickson convention; the in-repo R21 proof `R-RBS-LM-R21_klein4_is_quaternion_units_mod_sign.py` for `Q₈/{±1} ≅ ℤ₂×ℤ₂`.

---

## 2 — The conceptual shift (why "reader → substrate" is the right words)

klein4 = ℤ₂×ℤ₂ = V4 is **abelian** — `klein4_bind` commutes (cat=tac, F1211/F1255; measured at F1306 §3.8). Per R21, klein4 is exactly **"quaternion units mod sign"**: it holds the coset `q&3∈{1,i,j,k}` but **discards the sign bit** `q>>2∈{+,−}`. So a klein4 genome was a **quaternion *reader*** — it stored the abelian V4 *shadow* and you read quaternion-shaped structure back out of it, but the substrate itself could not hold the winding. That is precisely the F1306 finding: **the live base carries no walk-order curvature.**

Q₈ is the **non-abelian** central extension; the extra bit `b^4` is the **over/under-winding sign** that is **invisible to the V4 coset** (rc311 P3: klein4 could not even *represent* that error mode). So a Q₈ genome is a quaternion **substrate** — the walk-order / chirality / winding is **native**, and klein4 is recovered as the exact abelian projection `π:Q₈→V4`. That is "cascade-faithful **substrate**": the non-commutativity is stored, not read back out of a commutative shadow.

**This is the same object as the F1306 curvature block.** F1213's "directed channel" and F1306 §5 step 4 ("swap the directed glyph Class-L into the live base — the one remaining piece of the block, user-gated") are now **superseded by the shipped Q₈ substrate**: we no longer hand-roll a directed encoder; `element_type=Q8` IS the directed, curvature-bearing base. And rc309's non-abelian cycle holonomy + re-gauge-invariance is the **combined-shadow / gauge-connection** structure of the gauge asks doc — **Ask A is partly shipping**. `so9`/`spin9` stays deferred behind this.

---

## 3 — What local stuff needs NIXED (prioritised)

### N1 — the genome's `the_one` was a MISLEADING name over an RNG, removed (→ `coupling`); OUR CODE WAS BROKEN — ✅ **RESOLVED 2026-07-23**

**✅ Un-break landed:** the four srmech-boundary kwargs renamed `the_one=`→`coupling=` (`genome_store.py:98`, `corpus_store.py:47/50`, `knowledge_genome.py:130`); both edited paths verified **bit-exact on rc312** — the `genome()` pack/load path (`pack_instrument`/`load_instrument`/`load_kernel`) AND the `chromosome(coupling=)` + `express` path (epigenetic gating: love↔0b01, revolution↔0b10, the op⊗operand theorem). Our internal `the_one=` params were **kept** (genuinely resonant per F1304 — not the misleading case). The dozens of `the_one=` sites in `rbs_lm_research/*.py` are historical probe scripts — a separate, larger sweep, NOT the running baseline.

**Why it was renamed (user 2026-07-23) — NOT cosmetic.** The genome parameter called `the_one` **was not the real `the_one`** (the σ,θ resonant generator `cascade.the_one`); it **routed through an RNG**. So the name was not merely wrong but **misleading** — a stochastic/DRAWN coupling wearing the name of the resonant instrument, which *hides* the defect. srmech removed it (→ `coupling`) for that reason. This is the **same leak class as F1304** (our own `_coupler` was *documented* `the_one` but *implemented* as `klein4_random(seed=0)`) and exactly what the **F1259 DRAWN/DERIVED/STOCHASTIC** guard names: an RNG in a coupling is a defect, and the resonant name conceals it. **The name leaked from srmech's genome API into our siona code — our `the_one=` kwargs ARE that leak's footprint.**

Verified break: at rc299 `chromosome`/`genome_load`/`gene_express` take `coupling`, **not** `the_one` (no alias, no `**kwargs`) → `TypeError: unexpected keyword argument 'the_one'` **today**, independent of the Q₈ arc. F1304 already fixed *what we pass* (our `one` is now the real `klein4_from_one(the_one)`, genuinely resonant), but the kwarg **name** `the_one=` still leaks. The fix is therefore two-part: rename the kwarg to `coupling=` **AND** keep what we pass genuinely resonant (never re-admit an RNG under any name). Sites to fix:
- `siona/siona/genome_store.py:98` `chromosome(genes=genes, the_one=one, …)` → `coupling=one`
- `siona/siona/genome_store.py` (`genome_save`/`genome_load` positional uses are fine; audit every `the_one=` kwarg)
- `siona/siona/knowledge_genome.py:130` `chromosome(genes=genes, the_one=one, …)` → `coupling=one`
- `siona/siona/corpus_store.py:47,50` `genome_load(…, the_one=the_one)` → `coupling=the_one`
- `siona/siona/introspect.py:106` — stale help/doc string `the_one=COUPLE` (prose, not a call; update for accuracy)
- grep the whole subtree for `the_one=` before claiming done.

### N2 — `.siona_genepool` is PRE-format-version → RE-ENCODE, don't upgrade
`rbs_lm_research/.siona_genepool/manifest.json` reads `format_version: None`, no `carrier`. `upgrade_v15_to_v16` **fails** on it (`KeyError 'coupling'`) — it predates the versioned format, so the no-repack upgrade path cannot re-stamp it. **Reliable path = re-encode from source** (the streaming encoder), which we want anyway for the substrate move (N3). Do not depend on auto-migrate for this artifact.

### N3 — the coupler is klein4 (the abelian SHADOW), and the Q₈ `one` minter is missing — ✅ **RESOLVED 2026-07-23 (F1307)**

**✅ Substrate move landed.** siona's `genome_store` now threads `element_type=` (default klein4, byte-untouched); `element_type=ELEMENT_TYPE_Q8` couples through a RESONANT Q₈ `one` (`_coupler_q8` — the `klein4_from_one` coset + a Class-A sign channel, a declared function of `the_one`, NEVER an RNG — rejecting the rc311 test's seeded `_rand_q8_one`). Verified bit-exact on rc313 (five checks, `R-RBS-LM-Q8SUBSTRATEVERIFY_*.py`, exit 0): Q₈ round-trip exact with genuine winding · backward-faithful (`q8_project_v4(Q8 recall)==klein4 recall`) · klein4 default byte-identical to the raw srmech `genome()` path. DEFERRED (fail-loud, not blocking): Q₈ `express`/`add_kernel` + high-level `genome()`/`partition()` `element_type=` — three upstream asks in `UPSTREAM_NOTES.md §Q8-siona`.

- `genome_store._coupler` → `klein4_from_one(_ONE)` (sectors=4) and `corpus_store.COUPLE` → `klein4_encode_bytes(…)` (sectors=4) are the **V4 shadow** coupling (correct for a klein4 genome; F1304). For the **substrate**, thread `element_type=ELEMENT_TYPE_Q8` through `chromosome`/`recall`/`genome_save`/`recover_diploid`/`gene_express` **and** supply a **Q₈ (sectors=8) coupling `one`**.
- **GAP (open):** rc312 ships no obvious `q8_from_one` / the_one→Q₈ lift. Minters found are klein4-only (`klein4_from_one`, `klein4_expand`, both sectors=4). The rc311 P1 test constructs a Q₈ `one` somehow — **read `tests/test_genome_q8_coupling_rc311.py` for the minter, or file the ask** (§6).

---

## 4 — How to pick back up (the premise, in order)

1. **Un-break first (N1 + N2), stay on klein4 default.** Rename `the_one=`→`coupling=`; re-encode `.siona_genepool`. This restores a *running* baseline on rc312 — the **abelian projection** genome (`element_type=0`), byte-identical to what we had. Prove it: `recall(...) == leaves` and the test suite green on rc312.
2. **Bump the working venv to the arc.** We're on rc299; the substrate is rc308–rc312. Pull rc312 (or the clean tag when it lands) into the working venv; re-introspect (`[[feedback_introspect_srmech_before_python_dispatch]]`).
3. **Make the substrate move (N3).** Identify/mint the Q₈ `one`; thread `element_type=Q8`; re-encode with the winding native. Prove: Q₈ round-trip exact (rc311 P1 shape), and **backward-faithful** — `q8_project_v4(Q8 recall) == klein4 recall` bit-for-bit (rc311 P2) so nothing downstream that reads the V4 projection regresses.
4. **This clears the F1306 curvature block.** With `element_type=Q8`, the non-abelian coupling carries walk-order natively; the winding sign bit is the directional/chirality info klein4 couldn't hold. Re-run the F1306 beat-WSD separation with the Q₈-coupled genome as the derived (not hand-set) charge (F1259: corpus-derived, not DRAWN) — this is F1306 §5 steps 4+5, now via the shipped substrate rather than a hand-rolled directed channel.
5. **Fold into the gauge asks.** rc309's quaternion cycle holonomy + conjugacy-class gauge-invariance is Ask A's combined-shadow structure, now shipping — update `R-RBS-LM-SRMECHASKS_…` to note Ask A is partly realised by the Q₈ genome. `so9`/`spin9` remains queued behind the substrate landing cleanly.

---

## 5 — Verify-first checklist (before claiming "migrated")

- [ ] `grep -rn "the_one=" docs/srmech/siona docs/srmech/rbs_lm_research` → **zero** call-site hits (N1).
- [ ] `.siona_genepool` re-encoded; `genome_load` succeeds on rc312; manifest shows `format_version:16`, `carrier:"klein4"` (N2).
- [ ] klein4-default round-trip exact on rc312; suite green (baseline restored).
- [ ] Q₈ `one` minter identified (or ask filed) (N3).
- [ ] `element_type=Q8` round-trip exact **and** `q8_project_v4(Q8 recall)==klein4 recall` (backward-faithful).
- [ ] no `abs()` introduced (the winding sign is a group-encoding BIT via `⊕`, never `abs()` — the upstream discipline holds here too).

---

## 6 — srmech asks that may fall out

- **Q₈ coupling-`one` minter** — a sectors=8 `q8_from_one(one, D)` (the Q₈ analogue of `klein4_from_one`), if `tests/test_genome_q8_coupling_rc311.py` shows there is genuinely no public minter. Needed for any downstream to build a substrate genome without hand-constructing the OCT `one`.
- **`gene_express` under `element_type=Q8`** — confirm the epigenetic-reader path (`gene_express`/`gene_express_levels`) threads `element_type` (the rc311 note lists `chromosome`/`recall`/`diploid`/`recover_diploid`; verify `gene_express` too, since our demand-load read path depends on it — `corpus_store.py`, `knowledge_genome.py`).
- (Both are cheap to resolve by reading the rc311/rc312 tests first; file only if genuinely missing.)
