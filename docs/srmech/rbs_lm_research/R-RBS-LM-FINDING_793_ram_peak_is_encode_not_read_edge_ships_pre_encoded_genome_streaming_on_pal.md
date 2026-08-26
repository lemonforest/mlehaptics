# F793 — the 2.1 GB RAM peak is ENCODING (building the co-occurrence graph from the wiki source), NOT reading: navigating the pre-encoded structure is 48 MB. An edge device ships the encoded genome and only READS it (low-RAM). The low-RAM ENCODE needs streaming algorithms ON the PAL srmech already has.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** F789/F791/F792 (the clump/encode that hit 2.1–2.4 GB), §50/§17/§51 (the streaming-co-occurrence / sparse-partition family), srmech rc162–164 (the **PAL** — platform abstraction layer, genome file I/O), `[[user_stance_hardware_age_not_penalty_for_sharing]]` (ship the pre-encoded genome) · **User question (2026-06-16):** "the 2.1 GB peak — is it READING or ENCODING the structure? for an edge device where that much RAM can't be found and a fully-encoded genome is already provided, isn't there a platform-agnostic layer srmech needs so this can be chunked into read/write ops for LOW-RAM targets?"

## Measured: encode vs read
- **ENCODE (build): 2.1–2.4 GB.** `R-RBS-LM-FULLCLUMP`/`FRESHCLUMP` build the co-occurrence graph from the wiki SOURCE — the peak is (a) the tokenized docs held in memory + (b) the **materialised raw edge list** (8.7–10M edges from `text.cooccurrence_edges`). This is a one-time, build-time / server-side job.
- **READ (navigate): 48 MB.** Loading BOTH persisted tome-trees (92,034 words) + navigating (FIND→RIDE→ZOOM→WEB-HOP) peaks at **48 MB** — dict lookups + small list ops over the 0.9 MB + 2.9 MB JSON. (Siona's *full* server is heavier only because it also loads the genome + abstracts + relations + assoc; a **nav-only** edge build is ~tens of MB.)

**So the user's intuition is correct:** the GB-scale cost is ENCODING; READING the encoded structure is edge-friendly. **An edge device ships the pre-encoded genome (the tome-tree + stores) and only reads/navigates it** — it never re-encodes the wiki. The encode is paid once (server / capable host), per `[[user_stance_hardware_age_not_penalty_for_sharing]]` — the harvest/encode cost is not re-paid by every reader.

## The platform layer: it exists (PAL); the streaming ALGORITHMS are the gap
srmech **already has the platform-agnostic layer** — the **PAL** (rc162–164: streaming-read surface, directory iteration, "genome file I/O retrofitted onto the PAL", genome `#ifdef`-gated for embedded). So cross-platform chunked file I/O is there. What's missing to make the **ENCODE itself low-RAM** is the **streaming algorithms on top of the PAL**:
1. **Streaming / bounded co-occurrence** (extends §50/§17): accumulate a **top-K-per-node** co-occurrence by chunked PAL read/write, **without materialising the full edge list** — turns the (b) 2 GB edge-list peak into a bounded `vocab × K` store + a window buffer. (§50 shipped the *holographic* streaming fold; the *explicit* `cooccurrence_edges` peer is still all-in-RAM.)
2. **Out-of-core recursive spectral partition**: the native §51 `normalized_cut_bisect` is already O(edges) and bounded per sub-graph; feeding it from a PAL-backed sparse adjacency (read chunks, write sub-partitions) keeps the whole encode bounded.

Together: **encode = chunked read/write on the PAL → low-RAM**; **read = 48 MB**, already fine. That is the trade-RAM-for-I/O path for LOW-RAM targets the user asked about — and it's an **upstream ask** (streaming co-occurrence + out-of-core partition on the existing PAL), not a new substrate.

## Honest scope
- 48 MB is the *nav-only* footprint (both tome-trees); a definition/abstract edge build adds the gloss/abstract stores (tens–hundreds of MB; bounded, and themselves chunkable via the §50 holographic fold + PAL streaming).
- The streaming-encode is an upstream srmech ask (the PAL is there; the streaming `cooccurrence` + out-of-core partition are the missing ops). Not built here.

## Verdict
The 2.1 GB peak is **ENCODING** the structure (building the co-occurrence graph from the wiki source — docs + the materialised edge list), **not reading** it: navigating the pre-encoded tome-tree is **48 MB**. So an **edge device ships the encoded genome and only reads it** — low-RAM by construction; the encode is a one-time server/host job (hardware-age-is-not-a-penalty). For the **encode** to also run on low-RAM targets, the missing piece is **streaming algorithms on the PAL srmech already has** — a bounded streaming co-occurrence (§50/§17 extension) + an out-of-core recursive partition — trading RAM for chunked PAL read/write. The platform layer exists; the streaming ops are the upstream ask.
