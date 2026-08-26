# F1300 — **the JSON was a red herring; removed.** The genome directory (`turns.bin` + an MPR `manifest.json`) IS the SSOT — a separate flat JSON is a **non-attested, structure-flattened duplicate** of what the genome already holds. And the answer to *"should the genome do the same quad turn as the Cayley-Dickson register?"* is **yes — and it already does**: both wind **`the_one`** (dim 14, partition **1:3:7:3**). `turns.bin` **is** the coupled turns (`element_type='klein4'`, `coupling=the_one`); the CD register's `navigate` is the same `the_one` CD basis product. **The JSON was the flattened shadow of that shared winding — which is exactly why it never should have existed.** Corrects F1299 (which kept the JSON "for back-compat" — the sidecar mistake).

**User (2026-07-22):** *"there should not be sidecar files for genome and this JSON is a red herring"* + *"so genome should be doing the same quad turn as cayley-dickson register?"*

## The sidecar was the mistake — removed
F1299 added the genome-native persist but **kept the loose JSON alongside**, calling it back-compat. That is precisely the sidecar anti-pattern the record has stated repeatedly (`[[feedback_persist_genome_native_not_loose_json]]`, `[[feedback_no_doctoring_ssot_use_sublanguage_kernels]]`). The genome directory already carries everything the JSON did, **better**:

| the genome directory (SSOT) | the JSON sidecar (removed) |
|---|---|
| `turns.bin` — the **coupled turns** (the winding) | `edge_list` + `edge_weights` + `edge_charge` — **flat arrays** |
| `manifest.json` — a **full MPR** (`attestation`+`data`+`rendering`+`data_schema_id`, format v15) | a hand-built `attestation` dict, non-schematized |
| content-addressed (`body_sha256`) | no content address |

The JSON is a **flattening** of the genome — it discards the coupled-turn/winding structure and stores flat lists. Per F1278, flattening removes exactly the structure that makes it the genome. So it isn't merely redundant; it is a **degraded projection presented as data** — the definition of a red herring. The encoder now writes the genome directory and **nothing else**.

## The quad-turn answer: genome and register are one winding, two roles
Verified on rc299:
- **`the_one`** (`cascade.the_one`) is dim **14**, partition **(1, 3, 7, 3)**, carrying `separate_winding_curvature` — the shared generator.
- **Genome**: `kernel_pack`/`graph_to_kernel` pack leaves as `element_type='klein4'` with `coupling=the_one`; the persisted `turns.bin` is literally the **coupled turns**.
- **CD register**: `cd_navmap(4,1) = {0:(1,1), 1:(0,−1), 2:(3,−1), 3:(2,1)}` — the signed permutation of the **CD basis product**, and `e1·e2 = +e3`, `e2·e1 = −e3` (the non-commutative quad turn). `hdc.klein4_from_one` derives it from the same `the_one`.

**So they are the same quad turn.** The genome uses it in the **store** role (pack the relational graph as coupled turns); the register uses it in the **addressing** role (navigate slots by the CD product). This is F1294 axis-2 made literal: **one winding (`the_one`), two layer-roles.** There should be exactly one representation, read two ways — which is *why* a JSON sidecar is wrong on principle, not just on tidiness: it is a **third, structureless** representation of a thing that already has its native one.

## Honest gap surfaced — attestation should ride IN the genome, caller-supplied
The genome's `manifest.json` is already a proper MPR — but `genome_from_graph` fills it with srmech's **default** attestation (`source_url: srmech.net/genome/persistence`, `license: CC0`, `retrieved_at: 1970-01-01`), **not** the caller's source (`dumps.wikimedia.org`, `CC-BY-SA-4.0`, the real retrieval date). The one-op path exposes **no `attestation=` parameter**. So the correct provenance can't yet ride *in* the genome — and since there must be **no sidecar**, the fix is not a JSON beside it but an **`attestation=` / `source=` parameter on `genome_from_graph`** that writes the caller's MPR into the manifest. Filed as a small ask (UPSTREAM, alongside the composition issue). Until then the encoder records the source MPR in a comment, not a sidecar.

## Actions
- **Encoder**: `OUT` is now the `.genome` directory; the JSON payload + `write_text` are gone; `persist()` calls `genome_from_graph(charges=…, path=OUT)` and only that. Verified genome-only on a synthetic directed+charged graph (`turns.bin` + `manifest.json`, **no** `.json` sidecar).
- **Composition/invariant issue** filed (#1465) — the introspection layer that lets Siona compose the cascade over this genome.
- **Attestation-in-genome** ask noted for filing.

Composes **F1299** (corrected — sidecar removed), **F1294** (one winding / two layer-roles), **F1278** (flattening removes structure — why the JSON is degraded), **F1223/F1224** (klein4 IS the carrier; order is the winding), **F1250/F1251** (the genome partition), `[[feedback_persist_genome_native_not_loose_json]]`, `[[feedback_no_doctoring_ssot_use_sublanguage_kernels]]`.

**→ extended by F1301** — F1301 locates the quad turn in the triple: the **edges/operand/relational** slot is the held multi-perspective SUPERSET (metric + curvature + chirality coherently together; the op/responsion reads are single-Laplacian projections of it), and the perspective-count scales as the imaginary dimension up the fractal tower (1,3,7,15).
