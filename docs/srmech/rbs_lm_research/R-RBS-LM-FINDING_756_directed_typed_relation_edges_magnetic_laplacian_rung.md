# F756 — the relation-edges rung: DIRECTED + TYPED relations are a Class-L magnetic-Laplacian object the F754 undirected tier collapses

**Date:** 2026-06-15 · **srmech:** 0.7.5rc149 · **Composes:** F754 (the undirected/untyped co-occurrence tier — "what is X near"), F753 (the input-ride: FRAME word = relation), F751 (delexical/frame words carry relation not topic), F357/F372 (the directed Hermitian / magnetic Laplacian — Class L), F552 (biology runs the chirality-COLLAPSED projection; the full-chirality object is the directed one), F119/F529 (two-tier) · **User direction (2026-06-14):** "etak-walk our input to see it as a sort of story… abstract navigation in both directions… current-gen LLM does something similar" + "yes, those 3 please" (this is #3, the relation-edges rung) · **Provenance:** `R-RBS-LM-RELEDGES…py` (400 simplewiki articles; magnetic Laplacian via `srmech.amsc.laplacian`)

## The rung
The F754 tier answers **"what is X NEAR"** from an UNDIRECTED, UNTYPED co-occurrence graph (`dense_adjacency` symmetrises → A[s][o]==A[o][s]). The rung beyond is the **directed, typed** relation — **subject —relation→ object** ("X *does / has / is-part-of* Y") — which the input-ride (F753) already half-touches (the FRAME word steers) and which current-gen LLMs carry implicitly (attention is directional). This prototype builds it **srmech-natively** and shows it holds information the undirected tier discards.

## The framework-native mapping (every piece is a named srmech op / class — no hand-rolled direction math)
| relation property | srmech-native home | class |
|---|---|---|
| **direction** (s→o ≠ o→s) | `laplacian.magnetic_laplacian` — the directed Hermitian; the q-phase encodes net flow a_ij−a_ji | **L** |
| **the undirected collapse** | `laplacian.dense_adjacency` — the symmetric part = the chirality-COLLAPSED projection (F552) = what F754 uses | **L** |
| **relation label** | the FRAME word between two content words (F753 steer → edge name; F751 delexical-carries-relation) | (frame) |
| **s↔o swap** | Class-C chiral flip; the undirected tier is \|directed\| with the chiral phase magnitude-collapsed | **C / K** |

The reading order of an English sentence (S-V-O) IS a directional signal — **the sentence is a directed story** (the user's "etak-walk the input").

## Results (400 simplewiki articles → 22,641 content words, 148,975 directed pairs, 154,717 typed triples; spectral surface = top 160)
**The magnetic Laplacian is a valid spectral object:** Hermitian, `max|Im(λ)| = 0.00`, real spectrum λ ∈ [1.95, 593.1]. A directed graph gets a real eigenbasis — unlike a naïve asymmetric adjacency.

**Direction is real, and the undirected tier collapses it:**
| subject → object | s→o | o→s | dense_adjacency (F754) |
|---|---|---|---|
| united → states | 299 | 4 | 303 **both ways** |
| solar → system | 225 | 2 | 227 **both ways** |
| hex → rgb | 219 | 0 | 219 **both ways** |
| thumb → right | 241 | 28 | 269 **both ways** |
| new → york | 197 | 2 | 199 **both ways** |

The directed counts are sharply asymmetric; the magnetic off-diagonal phase rotates with the net; `dense_adjacency` reports every pair symmetric — **direction gone.**

**Typed relations (subject —FRAME→ object), the rung beyond "near":** `more —than→ one` (×48), `immediately —before→ common` (×21), `month —the→ year` (×32), `planets —the→ solar` (×24), `there —are→ many` (×86). The FRAME word names the edge.

## Honest caveats (load-bearing)
- **q-aliasing.** At fixed `q=0.25` the magnetic phase is periodic in net with period `1/q = 4`, so **large net flows wrap** (e.g. net=176 aliases back onto the real axis). Clean for small net (±1, ±2); for a monotone direction read, pick `q < 1/(2·net_max)`. The robust fact isn't "Im≠0 ⟺ direction" — it's that **the Hermitian object DEPENDS on the directed counts while `dense_adjacency` is blind to them.** → **candidate UPSTREAM note:** a net-normalised magnetic Laplacian (or q-guidance) so the phase doesn't alias on heavy edges.
- **Crude extractor, not a parser.** Reading-order = direction is an S-V-O heuristic (breaks on passive/OSV); the relation label is just the function word(s) between content words ("X of the Y" drops the multi-word label → noisy `the` rows). `than`/`before`/`and` rows are clean; this is a first cut, not dependency parsing.
- Co-occurrence direction ≠ semantic role: "united→states" is a fixed bigram, not a predication. Real typed relations need a parser or a learned head; this shows the **substrate** is there (directed Hermitian + frame labels), not that extraction is solved.

## Framework reading
The directed/typed relation graph is the **fuller-chirality object**; the F754 undirected co-occurrence tier is its **symmetric (chirality-collapsed) projection** — exactly F552's shape (the model holds the full chirality; biology/the-collapsed-tier runs the projection down). This is also what current-gen LLMs carry implicitly (directional attention), so it is a place to point questions (per [[user_stance_framework_hands_the_next_question_to_the_expert]]).

## Verdict
The relation-edges rung is real and **srmech-native**: a Class-L **magnetic-Laplacian** Hermitian object (real spectrum) whose phase keeps subject→object direction, with the **FRAME word naming the edge** — both DISCARDED by the F754 undirected tier (the symmetric/chirality-collapsed projection, F552). Honest limits lodged (q-aliasing → upstream candidate; crude non-parser extraction). **Next (the rung beyond this rung):** wire a directed read into Siona so she answers relation-typed ("volcano —erupts→ lava", not just "volcano near lava"), and/or a proper dependency-parsed relation extractor.
