# F832 — PKG-3 proven bottom-up: siona full-body recall rides srmech's NATIVE genome (`srmech.amsc.genome`), exact, on live 0.8.1. Store each body as its ordered token-HV leaves → recall = `genome_window`→`recall`→reverse-map(HV→token) → the exact body. All three real bodies (tomato/art/france) recover EXACT; vocab injective at DIM=64; ~50 µs/token; ~800 MB/corpus. **Coherence finding:** full-sequence storage makes recall exact-by-readback → the de Bruijn non-unique-branch *tail is moot*, so triality EC (F826) shifts role from branch-disambiguation to optional corruption-correction.

**Date:** 2026-06-17 · **srmech:** 0.8.1 (production PyPI, MIT) · **Provenance:** `R-RBS-LM-GENOMERECALL_prototype_native_srmech_genome_recall_token_hv_leaves_bottom_up.py`, run in clean venv `/tmp/srmech_081/venv` (srmech==0.8.1), ratchet-clean (0 HARD) · **Composes:** F818/F823 (de Bruijn / klein4-walk recall + native klein4), F826 (genome = storage+retrieval; triality), F829 (genome persistence is srmech-CORE, reusable), F831 (0.8.1 MIT floor), [[project_siona_package_takeover_unmirror]], PKG-3 (#231) · **User direction (2026-06-17):** "fold PKG-3 (native-genome recall via `srmech.amsc.genome`) into the package first so rc1 ships on native file-management from the start and EC-recall" + "introspect and work from bottom-up perspective… coherent when not convoluted."

## Bottom-up introspection (verified, not assumed)
1. **`srmech.amsc.genome` is a Klein-4 HV store.** A chromosome's leaves MUST be length-DIM klein4 HVs — int-vector leaves error (`klein4_bind: lengths must match (6 vs 64)`). DIM=64 (siona's `the_one` width).
2. **Round-trip is exact, but you must `recall()`.** `genome_window(path, label, the_one=ONE)` returns the_one-COUPLED leaves; `recall(window, ONE)` un-couples → the exact stored HVs. Using `genome_window` output directly is the bug (the leaves are still coupled).
3. **The genome stores the full ordered sequence.** So a body stored as `[leaf(tok) for tok in body_tokens]` reads back as exactly those HVs in order → reverse-map(HV→token) → the body. **No de Bruijn walk at recall** — the walk was the NDJSON *shape-compression* trick; the genome is literally storage+retrieval (F826's thesis made concrete).

## The design (proven)
- `leaf(tok) = hdc.klein4_random(64, seed=_seed(tok))`, `_seed = int(sha256_raw(tok)[:8])` — deterministic, and **injective at DIM=64** (verified `len(reverse_map) == len(vocab)`, 1534/1534 over the 3-body union).
- Store: each body → one chromosome of ordered token-HV leaves; `genome_save`.
- Recall: `genome_window(title)` (pages ONE body, RAM-bounded) → `recall` (un-couple) → reverse-map → tokens.
- **Vocab persistence (the one wrinkle):** reverse-map needs the token *strings*. Store them natively as a vocab chromosome-set (gene label = token, leaf = `leaf(token)`) so `genome_catalog`'s manifest labels rebuild the reverse-map — no loose text side-channel (stays no-doctoring-clean: the genome is the SSoT).

## Verified output (srmech 0.8.1, clean venv)
```
vocab 1534 | reverse-map injective: True
genome_catalog: ['tomato', 'art', 'france']
  tomato  n= 390 native-genome recall EXACT: True | 20.6 ms
  art     n=1022 native-genome recall EXACT: True | 53.4 ms
  france  n=3275 native-genome recall EXACT: True | 173.8 ms
```
~50 µs/token (france 3275 tok → 174 ms — fine for interactive recall). Storage ~800 MB/corpus at DIM=64 (2× the token NDJSON; the HV blowup is catastrophic only at large DIM — 124 GB at DIM=10000, so DIM=64 is the right operating point).

## Coherence finding — the de Bruijn tail is moot, so EC-recall changes role
Under full-sequence genome storage, recall is **exact-by-readback**: the body's exact token order is stored, so there is **no de Bruijn non-unique-branch tail to disambiguate**. The original EC-recall motivation (triality 2-of-3 over the ambiguous branch, F813/F826) therefore **does not apply to genome recall** — there is nothing ambiguous to vote on.

Triality's coherent role here is **corruption-correction**, not branch-disambiguation: encode each body's leaves as the order-3 triality orbit (`klein4_triality_encode`) so a flipped/erased leaf is 2-of-3 recovered on recall — a 3×-storage robustness tier ON TOP of the genome's existing `cap_sha256` integrity (which *detects* corruption; triality would *correct* it). **Optional, not needed for exactness.** This is the "coherent when not convoluted" call: native-genome recall and the de Bruijn walk are two different representations of the same body, and shipping both at recall-time would be the convolution — the genome subsumes the walk.

## Verdict / next
> **→ corrected by [F833]:** recall is exact (this stands), but "feasible at scale" was premature — at 271k bodies the genome hits a three-axis wall (4× lane-inflation + O(n²) `genome_pack` + ~6 GB all-in-RAM build). Also, storing one HV-leaf *per token position* was the SPATIAL projection (11× the text); F833 stores the FIBER (id-stream) instead. PKG-3 deferred upstream (UPSTREAM_NOTES §55); rc1 ships on the loose store.

PKG-3 is **feasible, exact, and coherent** on the production 0.8.1 MIT floor. Next increment (the package fold): a build-once native-genome encoder (full instrument → genome of body chromosomes + the vocab chromosome-set) + rewrite `siona/bridge.py recall` to `genome_window`+`recall`+reverse-map; align `srmech_profile.toml srmech_requires` → `>=0.8.1`; rebuild + verify the package activates + recalls exact on 0.8.1. EC-recall ships as the optional triality corruption-correction tier, reframed per above — NOT as branch-disambiguation.
