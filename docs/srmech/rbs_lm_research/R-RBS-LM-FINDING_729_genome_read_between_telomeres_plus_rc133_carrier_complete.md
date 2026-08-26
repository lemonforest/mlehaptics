# F729 — rc133 closes the carrier gap (17/17 numpy idioms) + how the genome of kernels is READ (between the telomeres)

**Date:** 2026-06-13 · **srmech:** 0.7.5rc133 (test.pypi.org; native dispatching, numpy OPTIONAL/absent) · **Composes:** F728 (the 9-idiom reflex-bail gap → now closed), F727 (`Mat`/`Vec` carriers), F715 (genome/chromosome/telomere), F721 (DNA-bookshelf), §42 (genome disk-persist) · **Provenance:** `R-RBS-LM-CARRIERAUDIT_…` (rc133: 17/17) + value-correctness spot-check (11/11) + `R-RBS-LM-APIDIFF_…` (rc132→rc133 = 0/0/0) + `R-RBS-LM-REGRESSION_…` (49/0) + `R-RBS-LM-GENOMEDISK_…` (VERIFIED ✓) + `R-RBS-LM-GENOMEREAD_introspect_between_telomeres.py`

## Part 1 — rc133 closes the carrier gap (the numpy-reflex sink is complete)
The 9 idioms that raised in rc132 (elementwise/scalar `+ - *`, slicing `m[:2]`/`m[:,j]`/`v[:2]`, negative indices) **all work in rc133, with correct values** — verified not just "didn't raise": `m+m`→`[[2,4],[6,8]]`, `m*2`/`2*m` correct, `m[-1,-1]`→4, `m[:,0]`→`[1,3]`, `m[:1]`→`[[1,2]]`, `v+v`→`[2,4,6]`, `v[-1]`→3, `v[:2]`→`[1,2]`. **Carrier audit: 17/17 idioms absorbed, 0 reflex-bail gaps.** So `Mat`/`Vec` is now a *near-total numpy-reflex sink* — an LLM's reflexive `m + n`, `m[:,0]`, `m @ n` all route through srmech instead of bailing to numpy. This realises the §2 srmech-first reflex-override **at the data-type level** (the type enforces the discipline, not willpower). **No breakage:** rc132→rc133 API diff = 0/0/0 (dunder additions); `R-RBS-LM-REGRESSION` 49 OK / 0 BREAK; `genome→disk` VERIFIED ✓.

## Part 2 — how the genome of kernels is READ (the "between the telomeres" introspection)
A genome is a flat **helix** (one strand) of fixed-width Klein-4 leaves. Each **kernel** is one **chromosome**, and each chromosome is delimited by a **telomere** — biology's repetitive non-coding chromosome-end cap, here a content-address marker. **Reading the genome = walk the strand; every telomere cap is a boundary; the leaves between two telomeres are one kernel's tomes; the chromosome's LABEL is what that stretch MEANS.** Two read paths, both demonstrated by `R-RBS-LM-GENOMEREAD_…`:

1. **`genome_catalog(path)` — the introspection** (the Class-H "what is stored + what it means" answer, body untouched). For a 3-kernel bookshelf it prints:
   ```
   GENOME  format v1  leaf_dim=64  n_turns=13   body_sha256 4f66585…   the_one cap 9c00306…
   BETWEEN THE TELOMERES — each row is one chromosome (= one kernel):
     telomere cap   label            tomes  byte range   meaning
     1858dda8…      siona_identity       5  0..384       who Siona is — her self-identity shelf
     fe5aec8e…      mfo_the_one          3  384..640     the MFO 'the one is the held invariant' kernel
     dd60ca11…      dragon_taught        2  640..832     a tome taught at runtime via build-by-dialogue
   ```
2. **Walk the raw strand** to *show* the telomere-delimited helix physically (○ = telomere cap, · = a tome leaf):
   ```
   ○siona_identity · · · · ·  ○mfo_the_one · · ·  ○dragon_taught · ·
   leaf-counts between telomeres: {siona_identity:5, mfo_the_one:3, dragon_taught:2}  (matches the manifest)
   ```
3. **Targeted read:** `genome_window(path, label)` pages exactly one chromosome by byte-offset (+ `cap_sha256` integrity-check); `recall` / `klein4_unbind(·, the_one)` decodes its bound leaves back to the raw tomes (verified `decode==stored`).

**Honest scope:** the genome stores **label + leaves** per chromosome — so the *machine-readable* meaning is the **label** (the meaning-key) and the *content* is the tome-leaves (content-addressed by the telomere cap). The human-readable gloss ("who Siona is…") is the researcher's annotation keyed by label, not a field the genome itself stores. A future ask (if wanted): an optional per-chromosome `description` in the manifest so the gloss travels with the genome.

## Verdict
rc133 is **on track — gap closed, nothing broken.** The carrier is a complete numpy-shaped reflex sink (17/17, correct values), and the genome reads cleanly as a telomere-delimited helix: `genome_catalog` is the simple introspection that says what each between-telomere stretch is (label + tome-count + cap + byte-range), `genome_window` pages one, `recall` decodes the tomes.
