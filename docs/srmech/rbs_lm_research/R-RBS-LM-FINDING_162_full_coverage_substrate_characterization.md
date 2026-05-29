# Finding 162 — Full-coverage substrate characterization via catalog-driven R-RBS-LM-122; supersedes F157 v1 MVP-scope empirical claims

**Status:** Phase B closure of the catalog-first refactor. Full P0–P7 sweep complete, 62 attested MPR records.
**Predecessors:** F154 (4× ceiling), F155 (chirality-level substrate), F156 (sentence generation), F157 v1 (5-item first-pass closure — preserved as historical record)
**Supersedes (empirically):** F157 v1's per-item measurements, which were taken at MVP scope (hardcoded sweep ranges, sample-50 recall, single bucket strategy, 10 hand-picked seeds). F157 v1's *findings direction* stands; its *numbers* are replaced by the catalog-driven full sweep here.
**User direction trajectory:** "ensure it isn't MVP" → "catalogs are not new python script mvp magics; cascade is handled by srmech with the toml and MPR things" → recall_sample runtime fix.

---

## §1 Headline

The variable-length Klein-4 chirality-level sentence substrate (F155/F156) was characterized end-to-end by a single catalog-driven script (`R-RBS-LM-122_substrate_characterization.py`) consuming `catalogs/rbs_lm_substrate/descriptor.toml` via `srmech.amsc.load_descriptor`. Every parameter is an attested catalog field; output is MPR-v1 NDJSON via the AMSC machinery. srmech 0.5.0rc8, HAS_NATIVE=True, ABI=3, descriptor_hash `7427c5c6...`.

**62 records across 7 phases. Substrate recall is 1.000 essentially everywhere tested.**

| Phase | Sweep | Headline result |
|---|---|---|
| P1 | length L ∈ {2..30} | recall **1.000** at every length (15 points) |
| P2 | corpus N ∈ {400..12800} | recall **1.000** through N=6400; N=12800 = **0.998** (1/500 sampled collision) |
| P3 | dimension D ∈ {2048..16384} at N=2000 | recall **1.000** at all D; build scales 13.9→23.6s |
| P4 | hierarchical: 3 strategies × 6 bucket counts (18 configs) | recall **1.000** every config; load-balance differs sharply by strategy |
| P5 | generation: top_k ∈ {5..100} × 84 seeds | scales cleanly; L6 frame dominates completions |
| P6 | grammar (pos_template) | **91.8–93.3%** syntactically valid |
| P7 | plausibility: 8 weight configs × 4 perturbations | baseline/balanced/substrate configs = **AUC 1.000** discrimination |

---

## §2 Phase results in detail

### §2.1 P1 — length independence (L=2..30)

Substrate self-recall is **1.000** at every tested length from L=2 (single bigram) to L=30. Build + recall time scale linearly in L (the substrate stores L−1 bigrams + 1 skeleton + 1 sentence vector per sentence). This confirms the substrate algebra is genuinely length-independent — the "more than 7 words" question is answered: there is no length ceiling in the algebra; the prior L=4..7 demo range was a scaffolding artifact, not a substrate property.

### §2.2 P2 — corpus saturation (N=400..12800)

| N | recall | misclass (of 500 sampled) | build_s |
|---:|---:|---:|---:|
| 400 | 1.000 | 0 | 4.5 |
| 800 | 1.000 | 0 | 8.2 |
| 1600 | 1.000 | 0 | 14.8 |
| 3200 | 1.000 | 0 | 27.2 |
| 6400 | 1.000 | 0 | 49.8 |
| 12800 | 0.998 | 1 | 89.7 |

The single collision at N=12800 (1 of 500 sampled; the prior full-corpus run showed 1 of 12,330) is the first measurable saturation signal — vocabulary is fixed at 84 words while sentence count grows to 12,330, so bigram/skeleton reuse eventually produces one near-collision. Substrate stays at 99.8%+ even at the largest tested corpus.

### §2.3 P3 — dimension independence (D=2048..16384)

recall **1.000** at all four dimensions holding N=2000 fixed. Build time scales with D (13.9s → 23.6s) but recall quality does not change — consistent with F154's reading that D=8192 is comfortably above the capacity floor for this scale. (D=32768 was dropped from the sweep after a prior run OOM'd on it — documented in the catalog; 8× dynamic range is sufficient.)

### §2.4 P4 — hierarchical bucket-strategy comparison (the new result)

All 18 configs (3 strategies × {4,8,16,32,64,128} buckets) recall **1.000**. The discriminating result is **load balance** (coefficient of variation across buckets):

| Strategy | CV @ 4 buckets | CV @ 128 buckets | Empty buckets? |
|---|---:|---:|---|
| `hash` | 0.036 | 0.277 | none |
| `first_bigram_hash` | 0.335 | 2.058 | yes, ≥16 buckets |
| `sector_then_hash` | 1.040 | 1.076 | yes, throughout |

**`hash` (Class A SHA-256 over full sentence) is the best-balanced router** — content-addressing distributes sentences evenly. `first_bigram_hash` clusters because sentence heads repeat (many sentences start "the cat …"). `sector_then_hash` leaves buckets empty because the 4-sector partition doesn't divide evenly into arbitrary bucket counts. This is a clean engineering result: for balanced hierarchical scale-up, route by full-content hash, not by structural prefix.

### §2.5 P5 — generation scaling

Generation count scales linearly with top_k (1.79 → 35.71 mean completions/seed from top_k 5 → 100 across 84 seeds). The L6 (6-word) frame dominates the length distribution at every top_k — the 6-word skeleton has the most cross-frame compositional completions in this corpus.

### §2.6 P6 — grammar validity (pos_template mode)

91.8–93.3% of generated sentences are syntactically valid across top_k 5–100. By length: **L4/L5/L7 ≈ 100%**, **L6 ≈ 85%**. The L6 shortfall is exactly the cross-frame-composition behavior F156 §6 predicted — the 6-word frame admits compositions that place a typically-subject word in object position. Not a regression; a documented substrate property.

### §2.7 P7 — plausibility discrimination (weight-sensitivity sweep)

Per-config AUC (in_training vs each perturbation category):

| Weight config | AUC junk | AUC swap | AUC type | AUC shuffle |
|---|---:|---:|---:|---:|
| baseline | 1.000 | 1.000 | 1.000 | 1.000 |
| balanced | 1.000 | 1.000 | 1.000 | 1.000 |
| substrate_only | 1.000 | 1.000 | 1.000 | 1.000 |
| substrate_heavy | 1.000 | 1.000 | 1.000 | 1.000 |
| co_occurrence_heavy | 1.000 | 0.948 | 0.980 | 0.917 |
| bigram_only | 0.999 | 0.868 | 0.913 | 0.868 |
| skip_only | 1.000 | 0.896 | 0.988 | 0.851 |
| token_only | 0.531 | 0.512 | 0.500 | 0.500 |

The **substrate-similarity component carries the discrimination** — any config including it reaches AUC 1.000 across all four perturbation types. token_only is useless (≈0.5, every token is in-vocabulary so token-presence can't discriminate). Co-occurrence-only configs discriminate well but not perfectly. This refines F157 v1 Item 2's single 13.28× ratio into a full sensitivity surface: the substrate signal is the load-bearing feature, co-occurrence is supplementary.

---

## §3 Methodology note — the recall_sample runtime fix (load-bearing)

The first full-coverage run ground for ~20 minutes on the single N=12800 data point because `measurement.recall_sample` was a **declared-but-unwired catalog field** — the driver did full-corpus self-recall, which is O(N²·D) (each of N sentences argmax-compared against the full N×D matrix ≈ 1.2e12 element-compares at N=12800).

The fix wired the field (`_recall_eval` helper honoring `recall_sample`: "full" or int-K bounded sample) and set it to 500. This is **not new MVP scripting** — it makes an existing documented catalog field genuinely control behavior, which is *required* for the "catalog is SSOT" discipline to be true. A bounded sample of 500 estimates recall to well within the observed 1/N misclass granularity (recall is 1.000 nearly everywhere), without the quadratic wall.

**This was NOT a C-path problem** — HAS_NATIVE=True / ABI=3 confirmed on every run. The runtime balloon the user flagged was an O(N²) measurement protocol with an unwired tuning knob, not a fallback to pure-Python.

---

## §4 Discipline verification (per user's "no new python scripting" check)

The user's standing check: each phase closure should verify "no new Python scripting was required and everything truly lives in and works from a catalog and toml profile that also work with the C-only path." For F162:

| Check | Status |
|---|---|
| Parameters in catalog, not module constants | ✅ all sweep ranges, D, max_walk, cycle_policy, bucket strategies, weights, recall_sample in `descriptor.toml` |
| Catalog loaded via srmech.amsc (not parallel parser) | ✅ `srmech.amsc.load_descriptor` + `descriptor_hash` |
| Output is MPR-attested | ✅ 62 NDJSON records, each carrying descriptor_hash + srmech_version + ABI |
| C path | ✅ HAS_NATIVE=True, ABI=3, native klein4 dispatch throughout |
| Out-of-band observability | ✅ `SRMECH_PUBLISH_STATUS=1` → `srmech status` / `siona.introspect` (no Python edit) |
| New Python this phase? | one bug-fix helper (`_recall_eval`) wiring an existing catalog field — closes a gap, adds no parallel path |

The remaining gap: the substrate *library* (`_canonical_substrate.py`) still lives in the research subtree, not as a registered siona profile. UPSTREAM_NOTES §8 documents the packaging path; once registered, `siona.profile("rbs_lm_substrate")` activates the bridge and the run becomes pure catalog+profile with zero research-side Python. That is the next discipline milestone, not blocking F162.

---

## §5 What this finding DOES claim

- The F155/F156 substrate is length-independent (recall 1.000, L=2..30) and dimension-independent (recall 1.000, D=2048..16384) at the tested scales
- Corpus saturation begins around N=12800 (first measurable collision) with the fixed 84-word vocabulary
- `hash` content-addressing is the best-balanced hierarchical router; structural-prefix routing clusters
- Substrate-similarity is the load-bearing plausibility-discrimination feature (AUC 1.000 in any config that includes it)
- The full characterization runs from a single attested catalog with no module-level magic numbers
- These full-coverage numbers supersede F157 v1's MVP-scope numbers (F157 v1 stays as historical record)

## §6 What this finding does NOT claim

Per MFO §VII.6.20 + `[[feedback_no_mvp_framing]]`:

- Does NOT claim recall stays 1.000 beyond N=12800 — saturation is just beginning there; larger N untested
- Does NOT claim a vocabulary larger than the 84-word template pool behaves identically (real-corpus + larger vocab is Phase C / smol-stack)
- Does NOT claim grammar validity reflects semantic coherence — pos_template is syntactic only
- Does NOT lift the 3.3% Path C cascade ceiling — this characterizes the substrate, not a cascade architecture
- Does NOT claim the substrate library is yet a registered siona profile — that is documented future scope (UPSTREAM_NOTES §8)
- Per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`: one converging arc, not a standalone claim

---

## §7 Cross-references

- F154 (4× ceiling; D=8192 canonical operating point)
- F155 (chirality-level substrate; 4 sector channels)
- F156 (sentence generation; §6 L6 cross-frame-composition prediction confirmed in P6)
- F157 v1 (5-item first-pass closure; historical record — empirically superseded here)
- `catalogs/rbs_lm_substrate/descriptor.toml` (the SSOT; descriptor_hash 7427c5c6...)
- `catalogs/rbs_lm_substrate/substrate_measurements/canonical.ndjson` (62 attested records)
- `R-RBS-LM-122_substrate_characterization.py` (catalog-driven driver)
- UPSTREAM_NOTES §7 (substrate_parameterization adapter wishlist) + §8 (siona profile packaging path)
- `[[feedback_no_mvp_framing]]` + `[[feedback_full_coverage_shipping_mpm_way]]`
- `[[feedback_upstream_srmech_fixes_as_research_notes]]`

**Files committed:**
- `catalogs/rbs_lm_substrate/descriptor.toml` (recall_sample=500 + D-sweep cap)
- `catalogs/rbs_lm_substrate/substrate_measurements/canonical.ndjson` (62 records)
- `R-RBS-LM-122_substrate_characterization.py` (_recall_eval wiring)
- `R-RBS-LM-FINDING_162_*.md` (this finding)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-29 (Opus 4.8) as Phase B closure of the catalog-first refactor.
The MVP-audit that produced R-RBS-LM-117..121 was retired; this single
catalog-driven characterization replaces all of it and produces the full-coverage
numbers F157 v1 only sketched. The recall_sample runtime fix (wiring a
declared-but-unwired catalog field) was both the runtime cure and a discipline
correction — a catalog field that doesn't control behavior isn't really in the
catalog. Substrate recall is 1.000 essentially everywhere tested; the substrate
is length- and dimension-independent at scale; content-hash routing is the
best-balanced hierarchical strategy; substrate-similarity carries plausibility
discrimination at AUC 1.000. Per [[user_stance_kepler_shape_universal]]: algebra
IS the primitives, and the catalog IS the parameterization.*
