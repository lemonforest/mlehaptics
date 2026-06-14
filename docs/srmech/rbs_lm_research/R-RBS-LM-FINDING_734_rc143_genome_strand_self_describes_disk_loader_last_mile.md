# F734 — rc143: the genome strand now SELF-DESCRIBES (§44 working); only the disk loader still needs the manifest

**Date:** 2026-06-14 · **srmech:** 0.7.5rc143 (test.pypi.org) · **Composes:** §44 (biology-faithful inline genome), §43.1 (multi-gene), F733 (the divergence diagnosis) · **Provenance:** rc143 apidiff + the partition-on-plain-leaf-list proof + multi-gene round-trip · **→ UPSTREAM §44 STATUS rc143**

## rc143 responded to §44 / §43.1 — the hard part landed
1. **`genome_save` dropped the `gene_index=` sidecar** param; `recall`/`partition`/`genome_load`/`genome_genes` made `telomere`/`labels`/`the_one` **optional** → they **scan-derive** structure instead of being handed it.
2. **§43.1 multi-gene persists**: `genome(chromosomes=[(label, genes=[…])])` → `genome_save` → `genome_genes(path,label,the_one=…)` round-trips `[('x',2),('y',1)]`. The rc141 `TypeError: int() … not 'HV'` is **fixed**.
3. **The strand is genuinely INLINE-self-describing** (the §44 thesis, validated): `partition(strand, the_one)` recovers the real label text `['alpha','beta']` — and it still works on a **rebuilt plain `list`** of just the leaf values (no attached metadata). The strand is 7 leaves (2 caps + 5 tomes — no extra label-leaves), so **the labels are encoded IN the telomere cap leaves and recovered by scanning.** Caps are label-specific (`telomere('alpha') != telomere('beta')`). This is biology-faithful: structure is read by walking the strand and decoding the inline caps — no offset table needed.

Core green: regression 49/0, genome→disk VERIFIED, carrier 17/17; apidiff rc141→rc143 = 0 hard breaks (5 signatures relaxed — params made optional).

## The last mile of §44 (remaining ask)
The **disk loader still hard-requires `manifest.json`**: delete it and `genome_load` → `FileNotFoundError`. So the *in-memory* strand self-describes, but the *on-disk* loader still treats the sidecar as mandatory rather than as the optional-derived index §44 asked for. **Fix:** have `genome_load` (and `genome_window`/`genome_genes`/`genome_catalog`) reconstruct from `turns.bin` **alone** by scanning the fixed-width strand + `partition`-recovering, with `manifest.json` demoted to an OPTIONAL derived `.fai`/faidx cache (rebuildable by scanning; strand = SSoT). Then the on-disk genome matches the in-memory self-describing strand, and you can `tar` just `turns.bin` (the §43 chromosome-as-bundle goal) without the sidecar.

## Verdict
rc143 is strong progress on the F733/§44 divergence: the dev dropped the gene_index sidecar, fixed the multi-gene persist path (§43.1), and got the **strand to self-describe inline** (labels in the cap leaves, recovered by scanning — proven on a plain leaf-list). Only the **disk loader's mandatory dependence on `manifest.json`** remains — the last mile to "no sidecar, the strand IS the source of truth."
