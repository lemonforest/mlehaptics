# RE-REVIEW REGISTER — findings measured on the 3-sentence LEAD slice, pending re-review against the ENTIRE article

Per user direction (2026-06-17): the lead-only stores (`wiki·definition` = lead sentence; `wiki·abstract-full` = lead ≤3 sentences) are a **manually-quantized slice** of simplewiki — they were treated as "the wiki," and empirical claims were measured on uniform ~30–50-token inputs. The entire article body must be the RBS-HDC instrument. F812 confirmed the slice distorts the results (k* and choice-bits SCALE with length; "length-independent" was an artifact). These findings are **PENDING RE-REVIEW** against the entire-article source (`articles.jsonl`, full bodies):

| Finding | Claim made on the slice | Re-review status |
|---|---|---|
| **F805** | article = Eulerian-path fiber; k = the dial | MECHANISM holds; "k* small / cheap" → re-measure on bodies (F812: k* scales 3.5→9+) |
| **F806** | fiber unique at finite k* (3–5); bundle fails, ctx-addr reads it | k* 3–5 was the slice; on bodies k* scales with length, ~15% of long articles have no unique walk ≤k14 |
| **F807** | input=output eigenstate at k_res 3–6 | k_res 3–6 was the slice; re-measure k_res on full bodies |
| **F808** | bundle-record key → (C) monotone 100% | key fix holds structurally; re-verify on full-length contexts (longer ctx, more repeats) |
| **F809** | storage-by-seed; article own-info "length-INDEPENDENT < 2 bits"; ~4× vs prose | **FALSE on bodies** (F812: choice-bits scale with length, corr +0.50, range 0–201); the ~4× was inflated by uniform slices |
| F788 / F745 / F760 | the lead/abstract stores | valid as LEAD stores; must NOT be presented as "the wiki encode" |
| F810 / F811 | article route + working-memory cap fix | behavioural fixes (less affected); included in the "yesterday" band per user direction |
| **F767 → F811 band** | any empirical claim resting on the lead slice | flagged; re-review where it rests on leads rather than entire articles |

**What stands** (not slice-dependent): the MECHANISMS — de Bruijn fiber, bundle-record context key (F808), context-addressed walk, resonance/eigenstate framing (F804), the operators/operands + surgical-graft + never-compact context discipline (F799/F801/F810/F811), the brute-force-π / harmonic-coupling readings (F803/F804). What does NOT stand: the MAGNITUDES claimed on the slice (small constant k_res, length-independence, ~4× compression, "an article's own info is tiny").

**Resolution:** `R-RBS-LM-FULLENCODE` — encode the ENTIRE article (full body) as the RBS-HDC instrument; re-measure k*, reconstruction, and storage-by-seed on entire bodies; scale to all 240,881 via §52 streaming + #225 markup form-kernels. Update each finding's numbers from the full-body re-runs. No slicing-and-calling-it-everything.
