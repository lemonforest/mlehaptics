# F1298 — **the simplewiki re-encode is an axis-1 Class-L store job; it is NOT gated on the CDRegister (axis 2).** The wiki encoders touch the register **zero times** — they are pure `magnetic_laplacian` / `dense_laplacian` / `cooccurrence_edges` / Fiedler. Two concrete "latest-srmech" improvements ARE pending and ready now, both Class-L: (1) `magnetic_laplacian(charges=…)` — the per-edge chiral dual-sense Laplacian the DIRECTED encoder currently only approximates with a uniform `q=`; (2) **genome-native persistence** (`genome_pack`/`kernel_pack`), replacing the loose `json.dumps` it still uses. The only real blocker is the **corpus**, not srmech.

**User (2026-07-21):** *"do we have pending simplewiki re-encode with latest srmech updates or do we wait for cdregister as our polarized/phased/whatever axis-2 surface?"*

## The dependency answer: don't wait for the CDRegister
Checked, not assumed. The wiki/genome encoders (`WIKIWEIGHTED_DIRECTED`, `FULLCLUMP`, `WIKIKERNEL`, `WIKIBIGENCODE`) use **only Class-L**: `dense_laplacian`, `magnetic_laplacian`, `cooccurrence_edges`, `jacobi_eigvals`, `fiedler_vector`. **Grep for `cd_register`/`sedenion`/`cd_navigate` across all of them: zero hits.**

This is F1294/F1216 in practice:
- The genome **is** the Class-L store (the relational object that grows, holds the edges, is exact and addressed). That is **axis 1** — the operation/where-it-lives.
- The CDRegister is an **axis-2** addressing/working layer — a query-time read/navigate surface. The store does not consume it.

**Waiting for the CDRegister (#1461) would gate a Class-L store on a Class-M/register capability it never uses.** And #1461's pending work is specifically the *reversible-coupling + EC* methods (`couple_working`/`carry`/`correct`) — the genome store touches none of them. The register is already **address-complete** for the query-time role it will eventually play. So the wait is an axis-conflation (the F1293 slip), not a real dependency.

## What IS pending — two Class-L improvements, ready on rc299
1. **`magnetic_laplacian(charges=…)` — the per-edge chiral dual-sense Laplacian.** The DIRECTED encoder currently calls `magnetic_laplacian(N, se, sw, q=0.25)` — a *uniform* phase — and its own comment flags the forward-window count as **"interim"**. srmech now ships a per-edge `charges=` parameter (the rc105 chiral dual-sense update). Directional co-occurrence with a per-edge charge is exactly the "polarized/phased" directional sense the wiki genome wants — and it is a Class-L op, available now.
2. **Genome-native persistence.** The encoder still does `OUT.write_text(json.dumps(payload))` — the loose-JSON anti-pattern (`[[feedback_persist_genome_native_not_loose_json]]`). srmech ships `genome_pack` / `genome_save` / `kernel_pack` / `chromosome` / `graph_to_kernel`. Switch the persist step to genome-native (content-addressed, TLV, demand-loadable), per F1207.

## The actual blocker (and it is not srmech)
The simplewiki dump lives at an absolute `~/corpora/wikipedia/…` path — the uncommitted-corpus condition (#1454 §3). So the re-encode is **operationally** gated on the dump being present, not on any srmech surface. The encoders run clean on rc299 otherwise (no numpy, no `klein4_random`).

## Recommendation
**Re-encode now on Class-L**, with (1) the `charges=` directed Laplacian and (2) genome-native persistence — when the dump is available. **Do not wait for the CDRegister**: it is the wrong axis for a store, its store-relevant surface (addressing) is already complete, and its pending work is a working-memory capability the genome never uses. The register matters later, at *query time*, as the phased/addressed **read** layer over the store — a decoupled, subsequent step.

Composes **F1294** (axis-1 cascade vs axis-2 layer — the whole basis of this decision), **F1216** (Class-L store vs Class-M/register working-memory), **F1207** (the WIKIWEIGHTED encoder + genome-native persistence), **F1296** (the CDRegister is address-complete; its gaps are the reversible/EC surface), `[[feedback_persist_genome_native_not_loose_json]]`, #1454 §3 (the corpus-availability caveat).
