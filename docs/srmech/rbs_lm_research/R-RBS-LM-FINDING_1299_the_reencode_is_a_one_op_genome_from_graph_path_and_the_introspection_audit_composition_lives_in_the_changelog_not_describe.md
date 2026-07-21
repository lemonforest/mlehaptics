# F1299 — **the charges= + genome-native re-encode is a SINGLE shipped op — `genome_from_graph(edges, weights, charges=…, path=…)`** — staged into the DIRECTED encoder and verified on a synthetic directed+charged graph (both JSON back-compat and genome-native emitted, `status=ok`). And the introspection audit the user asked for lands a nuanced result: **the re-encode ops are EXCELLENTLY introspected** (`charges=` in summary AND example, the return *shape* in `returns`, param semantics, full explanation) — so my §112 "summaries hide the need" worry does **not** apply here; it applies to *older* ops. But there is a deeper gap that matters for the whole goal: **op COMPOSITION and byte-exact INVARIANTS live in the CHANGELOG (prose), not in `describe`/`example` (per-op structured) — and composition is exactly what Siona needs to build a cascade.**

**User (2026-07-21):** *"re-encode with charges= and genome-native persistence when the dump lands. introspect encoding changes from srmech and check if related changelog gives information srmech misses in describe/example use."*

## Part A — the re-encode, staged and verified
The encoder already **computes** `edge_charge = fwd − bwd` (signed net direction) but only stored it in loose JSON and used a *uniform* `q=0.25` in its self-check. srmech now ships the op that does the whole thing:

```python
genome.genome_from_graph(n, edges, weights=metric, charges=signed_direction,
                         coupling=genome._default_coupling(52), path=GENOME_OUT)
```

One call: partitions **nuclear vs plasmid by the graph's own structure** (F1250/F1251), threads the per-edge **charge** through, and persists **content-addressed TLV** — retiring the loose-JSON anti-pattern (`[[feedback_persist_genome_native_not_loose_json]]`) *and* using the charge, not just storing it. Verified on a synthetic 6-node directed+charged graph: `counts={nuclear:1, plasmid:0}`, `status=ok`, 80 B persisted, and the JSON path unaffected (949 B, back-compat). **Staged behind `GENOME_OUT` so a JSON-only run is unchanged; ready to run when the dump lands.**

## Part B — the introspection / changelog audit

### What is NOT missing (contra the §112 worry)
The re-encode ops are **well-introspected**. For `genome_from_graph` / `genome_partition` / `graph_to_kernel` / `magnetic_laplacian`, `describe()` carries:
- **summary** naming "directed" / "signed" / "charge",
- **example** as a call template that shows `charges=<list>` explicitly,
- **`returns`** with the full dict *shape* (`{strand, chromosomes:[…], partition, counts:{nuclear,plasmid}, path?, census?}`),
- **`parameters`** with per-arg semantics, and a multi-sentence **explanation**.

`charges=` is discoverable from introspection alone. **So the §112 ask ("summaries describe implementation not need") is UNEVEN by op age** — the older ops (`mod_mul` = *"russian-peasant doubling"*, `magnitude` = *"pin-slot at zero"*) are the offenders; the recent genome surface is the **model of good introspection to hold the others to.** Scoped this into issue #1462.

### What the CHANGELOG carries that `describe` structurally cannot
Even for these well-documented ops, the changelog uniquely holds:
- **Composition** — `genome_from_graph` = `genome_partition` → `graph_to_kernel` per group → `mint_strand` nuclear / keep plasmid → `genome_save`. `describe` is **per-op**; this is **cross-op**.
- **Invariants** — `kernel_to_graph` recovers `{vocab_size, edges, weights, charges, node_ids, extras}` **byte-exact**, incl. after `genome_save`, with an interior centromere transparent to the payload.
- **Cross-op guarantees** — format v15 / ABI 5 stability; the asymmetric-minority-never-50/50 partition shape.

### Why this is the load-bearing gap for the goal
The overarching target (#1460/#1461/#1462) is **Siona composing a TOML cascade for a desired operation.** `describe`/`example` tells Siona **what each op does**; composing a cascade needs **how ops CHAIN** — and that knowledge (op A feeds op B, this preserves that invariant) lives in the changelog as *prose Siona cannot read as structured data.* **A per-op introspection surface cannot, by construction, express cross-op composition** — which is precisely the knowledge a cascade is made of. So the "srmech misses" answer is: not the per-op fields (those are good on recent ops), but a **composition/invariant layer** in the introspection surface — a machine-readable "op A → op B, preserving X" — that today exists only in the changelog.

## The concrete asks (refining #1462)
1. **Scope the summary-ergonomics fix to older ops** (`mod_mul`, `magnitude`, …); use the genome surface as the reference.
2. **Add a composition/invariant layer to introspection** — even a `composes` field on `ToolEntry` (`genome_from_graph` → `[genome_partition, graph_to_kernel, mint_strand, genome_save]`) + a `preserves` note (byte-exact round-trip) — so the knowledge Siona needs to *chain* ops is queryable, not only in the changelog. This is what turns "ask Siona which op" (F1297) into "ask Siona to compose the cascade" (the goal).

Composes **F1298** (the re-encode decision this implements), **F1207** (the encoder + genome-native persistence), **F1297/#1462** (Siona grounding — refined here), **F1294** (compose-the-cascade), `[[feedback_persist_genome_native_not_loose_json]]`, `[[feedback_introspect_srmech_before_python_dispatch]]`.
