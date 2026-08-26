# F926 — pressing the additional kernel encoding types (rc33 carriers): the **C/K directional** kernel (`magnetic_laplacian` + `Qarg`) and the **J multiplicative** kernel (`Qprime`) are **specialist lenses, not general word-relationship kernels**. The directional kernel is carrier-real (F924's clean 3-cycle: θ flips exactly with edge direction), but on the corpus neither the raw off-diagonal phase (convention/index-confounded) nor the principal eigenvector-phase embedding (93s at n=120; mixed poles) gives a clean directional word-relationship read — because word-order **direction is LOCAL/sequential** (already carried by the resonator's position-keys, F901/F912), **not a global-spectral property** (parallels F915: local structure ≠ global-spectral). J (`Qprime`) reads multiplicative/factor/period structure, which language relationships don't have (F909/F915 distributional) — so J's home is numeric/period data, not word-relatedness. The general word-relationship stack stays **M (form) + L (undirected usage, F920)**; C/K-directional and J are ready (rc33) for their native domains.

**Date:** 2026-06-22 · **srmech:** 0.9.0rc33 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probes:** `R-RBS-LM-FINDING_926_directional_kernel_C_K_is_a_specialist_lens.py`, `..._926_directional_kernel_embedding.py` · **Composes:** F925 (rc33 carriers shipped), F924 (Qarg + magnetic clean chirality), F920 (the L undirected kernel), F915/F909 (structure is local/distributional, not global-spectral/multiplicative), F901/F912 (position-keys carry order) · **User direction (2026-06-22):** "press the additional kernel encoding types."

## C/K directional kernel (`magnetic_laplacian` + `Qarg`)
- **Carrier-real (F924):** on a clean directed 3-cycle, θ_fwd + θ_rev = exact `Q(0,1)` — the phase flips exactly with direction; modulus is direction-blind. The structure is genuinely read.
- **On the corpus (12k simplewiki sentences, directed adjacency):** the directed structure is present (the magnetic Laplacian is complex; phases are nonzero), but **no clean directional word-relationship read** emerges:
  - raw off-diagonal phase is convention/index-confounded — `united→states` θ=π/2, `north→south` θ=π, `more→than` θ=0, despite all being ~fully directed (net-asym ≥ 0.95). The phase mixes srmech's q-flux/normalization with index order.
  - the principal eigenvector-phase embedding (n=120, complex `hermitian_eigendecompose`, **93.1s**) has mixed poles (`television, north, like, musician…` vs `i, italian, writer, water…`) — not a sentence-position flow.
- **Honest reading:** word-order **direction is a LOCAL/sequential property**, already carried by the resonator's position-keys (F901/F912) — it is **not** a global-spectral mode. This parallels F915 (constituency is distributional, not spectral-strain). The magnetic-spectral directional kernel's **home is globally-directed-flow graphs** (citation, food-web, dependency networks), where direction *is* a global property — not local word-order.

## J multiplicative kernel (`Qprime`)
- Carrier verified (F925: `sim²(12,18)=16/25`, factor-relatedness exact). But the lens reads **multiplicative/factor/period** structure, which **word relationships don't possess** (F909/F915: language is distributional/local). Encoding a word via the prime-factorisation of any derived integer is arbitrary. So **J is a specialist lens** for genuinely-numeric/period data (e.g., `cyclic_period` recurrence, counts), not general word-relatedness.

## The integrated kernel map (what each lens reads, for LANGUAGE)
| lens | class | reads (language) | role |
|---|---|---|---|
| byte/glyph C1 | M | local **form** (`cat~cot`) | general |
| spectral | L | global **undirected relatedness/usage** (`king~emperor`, F920) | general |
| position-keys (resonator) | — | local **order/direction** | general (already carries direction) |
| directional magnetic-spectral | C/K | **global directed flow** — *specialist* (flow graphs, not word-order) | specialist |
| prime-coordinate | J | **multiplicative/period** — *specialist* (numeric, not word-relatedness) | specialist |

## Verdict / next
**Pressed both new kernel types; honest outcome:** the completeness program (all 14 carriers, rc33) lets us *enumerate* every encode-lens, and pressing them shows **which apply to language** (M form + L undirected usage + position-key order) **vs which are specialists** (C/K-directional → directed-flow graphs; J → numeric/period). The carriers are ready for those native domains. **Cost note:** the complex `hermitian_eigendecompose` is ~93s at n=120 — the directional kernel is eigensolver-bound (a perf opportunity, like the `sim_k4_batch` float-batch). **Next:** (i) the C/K directional kernel on a genuinely-directed-flow graph (its home domain) to show it shines there; (ii) wire the L spectral neighbour-set (F920) as the resonator re-rank — the general-kernel payoff.
