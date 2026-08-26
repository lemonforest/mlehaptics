<!-- R-RBS-LM plan doc. Produced by two ultracode workflows (design: 11 agents; verify: 9 agents), then main-loop-checked. -->

> **STATUS (F1303): SAFE TO LODGE as a research + action plan, with §7 as its checked-not-asserted guarantee. NOT safe to BUILD from as written.** Three HARD BLOCKERS gate any build (§7.4): (1) the plan's headline citation-fix is itself wrong — Liddell & Johnson 1989 is the *Movement-Hold* model, NOT a 5-parameter model; (2) the 2,723 ASL-LEX count is attached to the wrong DOI (an MPM violation) — it is a separate 2021 publication; (3) `corpus_store.py` is non-runnable — a second undeclared `1080` seed AND a call to `klein4_random`, DELETED in rc297. Every external citation was web-verified; several §5.1 attestations were CORRECTED (see §7.2). Read §7 before acting on any claim.

---

# Research + Action Plan — An ASL Bridge for the ni-Vanuatu Order-Native Glyph Primitive

*Framework-reading-only. Question-shaping, not answer-machine. Every external claim carries an attestation flag; illustrative structural placeholders are marked as such and handed to a Deaf / sign-linguistics expert (F282).*

---

## 1. STRUCTURAL THESIS — what the bridge IS (a reading, not an extension)

The bridge is not a new artifact bolted onto ASL or onto ni-Vanuatu sand drawing. It is the framework READING three things that already structurally sit in one stack, and wiring the read-out that the genome currently only *represents* but does not yet *run through*:

- **ni-Vanuatu byte/glyph base = the order-native, language-agnostic bottom layer** (F761). A word is a glyph-composition; the *native* form of that composition is a **directed unicursal walk** — sandroing, attested as an Eulerian circuit (start = end, never repeat a path; UNESCO ICH 00073 / F1080). Order/winding is intrinsic here, at every scale (glyph→glyph in a word = word→word in a corpus; F1211/F1213).
- **ASL = the glyph→concept anchor, the BIT-EXACT op(x)operand form** (F1128). A sign is a discrete **chord** over a small finite phonological parameter alphabet (F608, `bundle([bind(role_p, val_p)])`); the **sense is the determinative made primary** — the classifier handshape is a meaning-CLASS, not an English token (σ_B); the second axis is literal 3D motion (σ_E). This is what a *logographic-shaped* language needs: for it the FORM axis IS the glyph-concept, exactly the anchor English resources cannot supply (F1140).
- **English = a lossy Wick-float PROJECTION** of that glyph-concept layer (F1128), never the anchor. English→ASL is "comprehend UP to the bit-exact form" (`b = B(A⁻¹(a))`); ASL→English is the easy projection DOWN.

SignWriting is ASL/ni-Vanuatu's **same-level, language-agnostic sibling** on the 2D-spatial "draw-it"/FIELD pole, opposite speech's 1D-linear "talk-it" pole (F735/F737).

**The bridge is therefore three coordinated read-outs over ONE order-native base:** (A) a *missing-glyph escape ladder* that reads what ASL already does with a missing sign; (B) a *glyph-sequence → English read-out DOWN* through the ASL concept spine, with the reverse escape UP; (C) an *escapable, glyph-form, standardized naming standard* that keeps every escaped name inside the base as a walk, never a flat ASCII drop.

**Load-bearing structural fact the whole bridge must honor (F1211, the re-derivation root):** the *live* ni-Vanuatu base as shipped is the **abelian Klein-4 bind — metric-only, zero-curvature** (it cannot tell `cat` from `tac`; sim 1.000). Direction lives only in the **non-abelian channel** (the directed magnetic-Laplacian charge / `the_one` winding / `cd_mult`), prototyped in F1213 but **not yet swapped into the live language layer**. Any bridge that flattens a glyph-sequence to raw bytes/ASCII **inherits zero-curvature and discards the sandroing winding**. This is the single most important constraint below.

---

## 2. CURRENT STATE — what exists (from the maps)

### 2.1 Shipped srmech surface (order-native ingest + walk; the base the bridge rides)
- `text.glyph_stream` — UAX #29 grapheme-cluster segmentation, lossless `''.join` round-trip, the **one genuinely domain-agnostic** segmenter (F1258); native C peer.
- `text.fold_marks` — combining-mark drop by Unicode category, a **separate lossy op** (never a `glyph_stream` mode).
- `text.cooccurrence_edges` → `laplacian.dense_laplacian` / `symmetric_eigendecompose` — the Class-L USAGE/relationship spectral kernel (F920).
- `laplacian.eulerian_path` / `eulerian_circuit` — node-agnostic Hierholzer, the sandroing unicursal walk; **honest `None`-refusal** on infeasible/disconnected graphs, never a lying partial (F1080/F1224); C peer `srmech_eulerian_walk`.
- `laplacian.magnetic_laplacian` / `signed_laplacian` / `fiedler_vector` / `hermitian_eigendecompose` / `jacobi_eigvals` — the directed/charge Laplacian carrying `edge_charge` = the DIRECTION channel the abelian base lacks. **Route every Zipfian co-occurrence eigen-read through these, NEVER `mat_eigvals`** (F1255 hub-contraction bug).
- `cascade.one` (`S(σ,θ)` + `winding_tower`), `cascade.cayley_dickson` (`cd_mult`) — the non-abelian order channel.
- `hdc.klein4_bind/bundle/similarity/klein4_encode_bytes` — the **metric-only, abelian, zero-curvature** glyph composition (F1211); `klein4_encode_bytes` is the morphology-preserving content encoder.
- `genome.kernel_pack/genome_save/genome_load/kernel_unpack` — content-addressed, TLV, demand-loadable persistence.
- `format.sha256_bytes` (Class-A content-address).

### 2.2 Genome language layer (representation only — inference does NOT yet run through it, F761)
- `ni-vanuatu(29)` chromosome — one Klein-4 vector per glyph (a–z + apostrophe/hyphen/space) = the abstract translation base.
- `signwriting(7)` chromosome — the 7 ISWA classes as genes, exact round-trip; the same-level signed sibling.
- `markup(13)` — the "understand, not strip" sublanguage kernel.
- English = a surface projection built FROM the base (shared-letter words share substrate; verified `sim(nice,mice)=0.62` vs `sim(nice,xyzqw)=0.17`).

### 2.3 Research-tree / siona-only (NOT in shipped srmech — the packaging-parity gap)
- `siona/asl.py` — `render`/`sign_chord`/`disambiguate`/`gloss_signs`, `CHORD_PARAMS`, attested to ASL-LEX. **Keyed on English lemmas**; fingerspell escape emits raw ASCII `fs:C-A-R` at `asl.py:167` (the flatten-defect).
- `siona/story.py sandroing_strokes` — Euler closability count `max(1, odd_degree//2)`.
- `asl_sign_kernel.toml` — "LaTeX-for-signs" 5-parameter-tier + σ_B/σ_E sub-language kernel.
- `asl_gloss_notation.md` + `asl_corpus.json` — slash-notation spec + 74 English↔ASL-gloss pairs.
- F1213 `word_to_kernel` — directed glyph-graph word encoder (weight = metric, charge = direction); steps 1–4 PASS, **step-5 live swap gated/not done**.

### 2.4 Discipline scaffolding (the "surface-and-build, never strip" precedent, already in three realizations)
- `understand_markup(text, gaps=)` — unwrap content, extract edges, remove only form; ranked **missing-kernel MAP** (F764/F817/F819).
- `# srmech-allow: <reason>` — the standardized, in-band, reason-carrying escape token honored **identically** by `check_srmech_discipline.py` (AST ratchet) + `git-hook-srmech-discipline.sh`. The model for a first-class escape marker.
- `siona/asl.py` fingerspell — the ASL-native "keep a missing sign inside the language" precedent (F1125), but currently flattens to ASCII.

### 2.5 Key gaps the bridge closes
1. **Root direction not live** — the shipped base is abelian metric-only (`cat=tac`); the F1213 directed encoder is built but not swapped in (gated step 5).
2. **No ni-Vanuatu↔ASL manual-alphabet correspondence** — no manual-alphabet handshape-chord chromosome exists.
3. **The fingerspell escape flattens to ASCII** — violates no-flatten.
4. **No ASL surface in shipped srmech** — chord/gloss live siona-only; a bridge needs an attested, config-driven `[class]` TOML + an ASL-LEX AMSC catalog.
5. **Encode still runs on English CAPS-gloss BYTES**, the lossy projection, not the bit-exact chord (F1128 "next", unbuilt).
6. **WSD is weak** — determinative-first overlap only; deeper-gloss scorer came back NULL (gloss-quality-bound, F1125).
7. **`glyph_stream` `len>2` strip-defect** must be removed before any re-encode (F1258) or the retired floor bakes into the new genome.

---

## 3. ACTION PLAN — three tracks (sharpened, discipline-passed steps)

**Track verdicts (from design review):** Track A **SURVIVES** · Track B **NEEDS-REWORK** (three load-bearing ops do not exist on disk; a covert English-word flatten hides inside its concept-resolution step) · Track C **SURVIVES**.

**Sequencing consequence:** Track A and Track C are buildable now on the F1213 prototype. **Track B is blocked** until its prerequisite ops are *actually built as attested srmech surface* — the sharpened plan converts B's overclaims into explicit build-first prerequisites and honest gates. Do A/C first; B rides on their output.

Each step is tagged **[PROTOTYPE-HERE]** (build in the research tree first, upstream later) or **[SRMECH-ASK]** (belongs in shipped srmech with a C peer + MPM block + DSL-class-vs-Python equivalence test).

---

### TRACK A — ASL bridge for MISSING glyphs (the fingerspelling-analogue) — *SURVIVES*

A **two-tier escape ladder** reading what ASL already does: lexical sign → classifier meaning-class (σ_B, coupled to graph) → fingerspell (glyph-form walk, coupled to graph). Never a silent drop; the fingerspelled chord is never presented as the concept anchor (the F1128 FORM≠MEANING anti-trap).

**A-1. [PROTOTYPE-HERE] Read-independent structure FIRST** (`feedback_read_independent_structure_check_first`). Before any selection/recall number: (a) build each manual-alphabet letter as an F608 role-filler handshape-chord `bundle([klein4_bind(role_p, val_p)])` and measure the **intrinsic Gram / cross-correlation + orthogonality** across parameter axes (does the manual alphabet form a distinct closed sub-lattice, like `signwriting(7)`'s inter-class sim ~0.26?); (b) encode a batch of fingerspelled names via `word_to_kernel` (nodes = handshape-chords) and measure **Eulerian round-trip fidelity** + the **direction ratchet** (`name ≠ reverse` via `edge_charge`). All eigen-reads → `hermitian_eigendecompose`/`jacobi_eigvals`, never `mat_eigvals`. This intrinsic signature settles before any recall number is reported.

**A-2. [SRMECH-ASK] Build the `manual_alphabet` chromosome** as the ASL-native sibling of `ni-vanuatu(29)`/`signwriting(7)` (F761/F735/F737). Each letter (+ number/loan handshapes as the expert dictates) = a handshape-chord (F608), content-addressed via Class-A `sha256_bytes` seeds. **BLOCKING precondition — de-magick the coupling seed:** the live `COUPLE = hdc.klein4_expand(LEAF, 1080)` bakes the DRAWN magic number `1080` as an undeclared pin; derive it as `sha256_bytes` of a *named attested source descriptor* and record it, **before** the chromosome ships (prove round-trip equivalence before/after the seed change). Exact round-trip, genome-native (`kernel_pack`/`genome_save`), like `signwriting(7)`.

**A-3. [PROTOTYPE-HERE → SRMECH-ASK] Fingerspell escape as a directed sandroing walk, NOT flat ASCII** (the direct deliverable). Replace `asl.py:167`'s `fs:C-A-R` ASCII render with the F1213 directed glyph-graph over the `manual_alphabet` handshape-chord nodes: `edge_weights = w_fwd+w_bwd` (metric/adjacency), `edge_charge = w_fwd−w_bwd` (direction), round-tripped as the sandroing Eulerian walk (`eulerian_word`/`eulerian_path`), reversible and order-preserved. Persist genome-native, never loose JSON. **Order-honesty (sharpened):** state explicitly that this is **order-PRESERVING/reversible but its node-sequence is English-orthography-DERIVED — a borrowed order, not substrate-native.** Do NOT assert it maps onto sandroing structure; hand that to the expert (A-7 Q1).

**A-4. [PROTOTYPE-HERE] The classifier / σ_B tier ABOVE fingerspell** (the concept-CLASS anchor without English). For a missing glyph WITH a resolvable meaning-class, anchor via the classifier handshape = σ_B made primary (F608/F609/F610) + the σ_E spatial axis — a meaning-CLASS (`CL:1` person / `CL:3` vehicle / `CL:B` flat / `CL:C` cylindrical), never an English token. This is the F609 axis-alignment (meaning-class-explicit source selects 100% vs English 26%). Selection is **structure-supplied and handed to the expert**; WSD is measured weak (F1125 NULL) — **do not claim reliable automatic sense selection.**

**A-5. [SRMECH-ASK] Standardized in-band escape token + surface-not-strip ratchet.** Promote `asl_gloss_notation.md §1.3`'s `[fs:...]` bracket into a first-class, in-band, reason-carrying escape token registered against `manual_alphabet` and honored by a discipline ratchet — the exact model of `# srmech-allow: <reason>` honored identically by two guards. Every escape emits a ranked missing-kernel MAP event (F819/F764/F817): "a missing sign/glyph is a missing KERNEL to build." **The ratchet FAILS if a missing sign is silently DROPPED** rather than escaped — the ASL analogue of the markup strip-guard.

**A-6. [PROTOTYPE-HERE] Couple the escaped form to the concept graph** (the F1128 anti-trap). Bind every escaped chord (classifier or fingerspell) INTO the Class-L relationship graph rather than treating the chord as the anchor: iconicity was refuted read-independently; the chord carries only ~6× byte-signal (~0.02 abs). The concept anchor is **chord-COUPLED-to-graph, never bare chord.** Co-occurrence spectra → `hermitian_eigendecompose`/`jacobi_eigvals`/`fiedler_vector`.

**A-7. [ATTEST + EXPERT HANDOFF]** Attest every external claim (see §5) with full MPR records — **do not recall from memory.** Correct the citation defect (5-param chord = Battison 1978 / Liddell & Johnson 1989, NOT Stokoe 1960's 3 params). Flag as UNATTESTED illustrative placeholders: the manual-alphabet inventory, the ni-Vanuatu↔manual-alphabet correspondence, all classifier routings. Hand the shaped questions to a Deaf / sign-linguistics expert.

**A-8. [GATE — do NOT cross in this track]** The live base is still abelian metric-only (F1211). This escape rides the F1213 *prototype* directed encoder; swapping the **live** `_word_hv`/`build_genepool` (F1213 step 5) is a separate gated live-genome mutation + re-encode, **out of scope here.** F1255 caveat: the directed re-base buys genuine curvature (irremovable holonomy) **only where the glyph-walk CLOSES** (betti₁>0, repeated-glyph tail); short escape names on the acyclic function-word spine stay **endianness (removable gauge)** — so an escape name carries real which-way only on repeated-glyph tails, orientation-only elsewhere.

---

### TRACK B — glyph-SEQUENCE → English (read-out DOWN + reverse escape UP) — *NEEDS-REWORK → gated*

The disciplined *precursor* to the north-star (inference-through-the-abstract-layer, F761/R-RBS-LM-25/54), NOT that north star itself. **Three load-bearing ops the original design leaned on do not exist on disk** (`text.glyph_stream`, `word_to_kernel`, `laplacian.eulerian_path/circuit` were all absent at review — verify current status before relying on them), and the shipped concept-resolution path (`sign_chord`/`gloss_signs`) is **English-lemma keyed**, which is a covert flatten. The steps below are rewritten so B **cannot silently collapse onto the flatten baseline (Candidate A) it claims to reject.**

**B-0. [SRMECH-ASK — BLOCKING PREREQUISITES, build FIRST]** Do not claim ops that do not exist. **Build** (a) `text.glyph_stream` (UAX #29 grapheme clusters, lossless join round-trip) with the F1258 `len>2` strip-defect deleted; (b) `word_to_kernel` (`edge_weights = w_fwd+w_bwd` metric; `edge_charge = w_fwd−w_bwd` direction); (c) `laplacian.eulerian_path`/`eulerian_circuit` (Hierholzer, honest `None`-refusal). *(Several of these are described elsewhere in the maps as graduated/shipped — reconcile the actual on-disk status before proceeding; if genuinely absent, they are blocking builds.)* **Until they land, Track B has no order-native ingest and must not run.** Safety: all eigen-reads → `hermitian_eigendecompose`/`jacobi_eigvals`/`fiedler_vector`, never `mat_eigvals` (F1255).

**B-1. [PROTOTYPE-HERE] Ingest, keep order.** Segment with `glyph_stream`. Build each unit as a directed glyph Class-L via `word_to_kernel`. At corpus scale use `cooccurrence_edges` → `magnetic_laplacian` so the SAME charge carrier operates one scale up (glyph→glyph = word→word). **Never `klein4_bind` alone** (abelian, zero-curvature).

**B-2. [SRMECH-ASK — sharpened: remove the covert English-word flatten] Glyph-sequence → concept, chord COUPLED to the relationship graph.** The shipped `sign_chord(word)`/`disambiguate(word,context)` are English-lemma keyed — using them keys the chord *through an English word*, a flatten inside the very step claimed order-native. **Rewrite:** resolve a directed glyph-unit to a sign-chord via a **glyph-keyed index** (chord keyed by glyph-sequence kernel, NOT English lemma), OR explicitly declare this coupling op **UNBUILT and gate the step.** Keep F1128 discipline: couple the 7-tuple chord (FORM) to its Class-L usage neighborhood (F920 MEANING); the chord is not the anchor. The classifier/determinative σ_B is the meaning-class gate (F609: 100% vs 26%). Output per unit: `(concept-id, sign-chord, σ_B class, σ_E slot)`.

**B-3. [PROTOTYPE-HERE] Assemble the ordered concept SPINE (never a bag).** Chain resolved concepts as a directed walk — an Eulerian trail/circuit via `eulerian_path`/`eulerian_circuit` (honest `None`-refusal, never a lying partial). Order carried by the non-abelian channel (`cd_mult`/`one`), NEVER the abelian metric (F864 never-a-bag; F865). Measure closability with `sandroing_strokes` (`max(1, odd_degree//2)`) + `best_rational` commensurability (F1079). *(If `eulerian_path` is genuinely unbuilt, assemble via `sandroing_strokes` — which exists — plus an explicitly-flagged prototype walk.)*

**B-4. [EXPERT HANDOFF] Sense-fix each node — WEAK, shape the question.** Apply `disambiguate(word, context)` (F1125) to fix σ_B per node. **Flag honestly:** weak meaning-set-overlap first pass; deeper-gloss WSD came back NULL (gloss-quality-bound, not mechanism-bound). Do NOT silently auto-resolve polysemy. Frame as the coupling-character question — "which sign is the correct coupling of concept-to-context?" — hand to a Deaf expert + a collocation-rich sense source (F966 phrase-level ASL-gloss corpus).

**B-5. [PROTOTYPE-HERE] Project the spine DOWN to English (the easy, acknowledged-lossy direction).** Two sub-passes over the SAME concept-graph: (a) topic-comment → SVO reorder (ASL is topic-comment, not source-order; the `[topic]` marker already exists in `asl_gloss_notation.md`); (b) re-insert dropped function words and collapse σ_B + σ_E into English tokens. **Label the output EXPLICITLY as the lossy Wick-float projection** (polysemy re-introduced, σ_E flattened, order-slack restored). English is a READ-OUT, never the anchor (no F398 English-privilege residue).

**B-6. [PROTOTYPE-HERE → SRMECH-ASK] The reverse escape (stays glyph-form) + round-trip UP check.** A unit with no lexical sign escapes to glyph-form fingerspelling — a directed sandroing walk over `manual_alphabet` via `word_to_kernel` weight+charge with an Eulerian round-trip. **NEVER `fs:C-A-R` raw ASCII.** Keep `[fs:...]` first-class/in-band (the `# srmech-allow` model); surface the missing sign as a missing KERNEL (F819), never a strip. The reverse recovery (English → chord → glyph) is the **integrity check**: comprehend English UP to the bit-exact chord (`b = B(A⁻¹(a))`), re-derive the glyph-sequence, verify direction charge (`cat` `[-1,+1]` ≠ `tac` `[+1,-1]`) + Eulerian round-trip held.

**B-7. [PROTOTYPE-HERE] Read-independent structure check FIRST** (before any recall/accuracy number, F999-1002): chord-lattice Gram/orthogonality, directed round-trip integrity (`cat≠tac`), Eulerian closability + `best_rational` commensurability. Only AFTER intrinsic structure checks out do you report a read-out fidelity number.

**B-8. [SRMECH-ASK] Package + north-star handoff.** Ship as a config-driven `[class]` TOML read-out + an ASL-LEX AMSC catalog with the full MPM block — NOT a siona-local dict. Prove with a DSL-class-vs-Python equivalence test. **Scope honesty:** frame B as the tractable precursor to inference-through-the-abstract-layer (the SAME abstract HV read out as English OR ASL-chord OR SignWriting; Rosetta triangulation F610) — today only the genome REPRESENTATION is layered; **inference does not yet run through the abstract layer.** Over-claiming otherwise violates F761's honest scope.

**B-ATTEST. [BLOCKING, new mandatory step]** Web-verify EVERY external citation with real author+title+venue+year+DOI/OA-URL + MPM block **before any load-bearing use** — do NOT recall the ASL-LEX DOI/pages from memory; fetch and confirm. Any citation not web-verified stays flagged UNATTESTED and cannot support a claim. Scope "iconicity refuted" to the **measured local subset**, not a field-level refutation.

---

### TRACK C — ESCAPABLE, GLYPH-FORM, STANDARDIZED names — *SURVIVES*

The **glyph-form escape standard**: a four-layer composition — MARKER (in-band token modeled 1:1 on `# srmech-allow: <reason>`) wrapping a WALK payload (F1213 directed glyph-graph over the `manual_alphabet` chromosome, round-tripped as the F1080/F1224 sandroing Eulerian walk), content-addressed + ATTESTED genome-native (Class-A `sha256` key + AMSC MPR v1 block), enforced by a two-guard RATCHET. The synthesis of the three existing "surface-and-build, never strip" realizations, each at its strongest point.

**C-1. [PROTOTYPE-HERE] Read-independent audit FIRST.** MEASURE the flatten: confirm `asl.py:167` emits `fs:` + hyphen-joined uppercase ASCII; confirm `ni-vanuatu(29)`/`signwriting(7)` have NO manual-alphabet sibling. Emit the F819 `understand_markup(gaps=)` ranked missing-kernel MAP over a token sample = the currently-escaped-but-flattened names. Deliverable is the intrinsic **"flatten census"** (how many escapes, which base-glyphs missing), NOT a recall number. (FIG-C5, FIG-C9.)

**C-2. [SRMECH-ASK] Build the missing base-glyph inventory as an ATTESTED chromosome** (shared with A-2 — build once). Each manual-alphabet letter-glyph = a handshape-chord over the `CHORD_PARAMS` role axes (F608). Content-address via `klein4_encode_bytes` + Class-A `sha256` seed — **NEVER `klein4_random(seed=hash(word))`, NEVER the drawn `1080` pin.** Wrap in an AMSC MPR v1 block: source = ASL-LEX (see §5) for handshape *values*; **correct** the parameter-model attribution to Battison 1978 / Liddell & Johnson 1989 (NOT Stokoe 1960's 3 params); flag every constructed chord ILLUSTRATIVE/expert-verify (dignity-first F282). Register the ni-Vanuatu-glyph ↔ manual-alphabet correspondence map. (FIG-C4, FIG-C7.)

**C-3. [SRMECH-ASK] Specify the escape grammar** as a bounded, no-nested-escape token (a config-driven `[class]` TOML, `asl_sign_kernel.toml` is the sibling model), five-field anatomy:
1. **MARKER** — standardized, in-band, first-class opener modeled 1:1 on `# srmech-allow: <reason>` (the `check_srmech_discipline.py _allowed` + git-hook `grep -vE 'srmech-allow'` agreement is the exact model); reuse the `[fs:...]` bracket surface but **redefine its payload.**
2. **BASE-TAG** — which order-native inventory the walk draws from: `nv:` ni-Vanuatu glyphs / `fs:` manual-alphabet handshape-chords / `u8:` a UTF-8 **byte-glyph walk** for codepoints outside every base (never a raw hex drop; F864/F1128).
3. **WALK** — the glyph-form payload (C-4).
4. **CONTENT-ADDRESS** — Class-A `sha256` digest of token content = the STABLE naming key (the "standardized naming scheme" requirement) + the content-address of the referenced chromosome.
5. **REASON/PROVENANCE** — WHY this is an escape, which SURFACES the missing kernel (F819) — the direct analog of the `srmech-allow` reason field.
(FIG-C2, FIG-C1.)

**C-4. [PROTOTYPE-HERE → SRMECH-ASK] Realize the payload as an order-native sandroing walk (the no-flatten core).** Compose each escaped name via the F1213 directed glyph-graph over the C-2 chromosome (`weight = w_fwd+w_bwd`, `charge = w_fwd−w_bwd`), round-tripped via `eulerian_path`/`eulerian_circuit`, keeping self-loops so double letters round-trip. **This is what keeps the escape GLYPH-FORM:** `C-A-R` is a directed walk `C→A→R` carrying weight+charge (reversible, order-preserved), NOT a flat string — and it **MUST use the directed/charge channel**, because `klein4_bind` alone cannot tell `C-A-R` from `R-A-C` (F1211). Recover per-edge metric+direction via `magnetic_laplacian`/`signed_laplacian` (`(w±c)//2`). Prove round-trip bit-exact (`decode(escape)==token`) and prove the honest REFUSAL (infeasible/disconnected → `None`, never a lying partial). Remove the `len>2` strip-defect and base segmentation on `glyph_stream` BEFORE encoding. (FIG-C3, FIG-C6, FIG-C8.)

**C-5. [SRMECH-ASK] Wire content-address + attestation genome-native** (not loose JSON). Persist each escape token + base-glyph chromosome via `kernel_pack`/`genome_save` (content-addressed, TLV, demand-loadable). The escape's STABILITY = its Class-A content-address (same token → same escape composition deterministically), replacing any drawn/stochastic pin. Attach the C-2 AMSC MPR v1 block. Run a no-magic-numbers A/B/C pass over every constant introduced; the irreducible C-residue is the honest flag. `sha256` is the **routing/naming key only, never the content representation.** (FIG-C7.)

**C-6. [SRMECH-ASK] Build the two-guard ratchet** (the standardized enforcement; the missing ASL-side discipline). Ship a checker PAIR analogous to `check_srmech_discipline.py` + `git-hook-srmech-discipline.sh` that both honor the MARKER identically and enforce three invariants: (a) never silently DROP a missing sign/glyph — a missing token MUST be escaped; (b) every escape is GLYPH-FORM — payload references **base-glyph-chromosome indices, never raw ASCII bytes** (structural check, not a mere string test — this is the guard that FAILS today's `asl.py:167`); (c) every escape carries a content-address + reason. Emit the F819 ranked missing-kernel MAP as ratchet output on a JPL-style **down-only baseline** (each escape = a build-me candidate driving toward zero). Prove with a DSL-class-vs-Python equivalence test. (FIG-C1, FIG-C5, FIG-C9.)

**C-7. [EXPERT HANDOFF] Hand the next questions to a Deaf / sign-linguistics expert** (question-shaping, F282) — see §6.

---

## 4. FIGURES (aphantasia accommodation — the plan ships MORE, not fewer; the user cannot visualize)

**Cross-track ladder (the spine of the whole bridge):**
- **FIG-0 — Three-layer stack:** ni-Vanuatu order-native glyph base (2D field pole) → ASL glyph→concept chord anchor (bit-exact op(x)operand) → English lossy Wick-float projection (1D talk-it pole). Arrows: "comprehend UP" (English→ASL) vs "project DOWN" (ASL→English), marking which hops are bit-exact vs lossy.
- **FIG-LADDER — Three-column surface-and-build-never-strip ladder:** `[markup understand_markup | srmech # srmech-allow | ASL glyph-form escape]` side by side, the SAME shape across all three (surface the gap → escape in-band → NEVER strip).

**Track A:**
- **FIG-A1** Escape-ladder decision-flow: concept → has lexical glyph/sign? → emit | else has resolvable meaning-CLASS (classifier σ_B)? → classifier-chord anchor coupled to graph | else → fingerspell as directed glyph-walk; **NEVER silently drop**; each escape emits a build-the-kernel MAP event.
- **FIG-A2** Fingerspelled name as a directed glyph-graph / sandroing Eulerian walk: `fs:C-A-R` as three handshape-chord NODES with directed edges, each annotated weight (metric) vs charge (direction), start=end anchor marked — beside the flat ASCII `C-A-R` string it replaces.
- **FIG-A3** Manual-alphabet handshape-chord vs a lexical sign-chord as role-filler bundles — fingerspelling composes from the SAME chord alphabet, a sparser sub-lattice.
- **FIG-A5** FORM≠MEANING coupling (anti-trap): the chord (FORM) coupled by a binding edge to the concept/relationship Class-L graph (MEANING); annotated "chord alone ~6× byte-signal, weak; meaning stays in the graph."
- **FIG-A6** Duality-pole placement: ni-Vanuatu sandroing walk AND the ASL manual-alphabet handshape-walk both on the 2D "draw-it"/FIELD pole; the fingerspelled English word on the 1D "talk-it"/projection pole.
- **FIG-A7** Classifier σ_B meaning-class anchor: a missing concept fanning to `CL:1`/`CL:3`/`CL:B`/`CL:C` (meaning-CLASSES, not English tokens), with the σ_E spatial axis; selection gated by a context axis, handed to the expert.

**Track B:**
- **FIG-B1** DOWN-and-UP pipeline schematic on one page: top lane glyph-sequence(directed) → concept spine → English (labeled "lossy projection DOWN"); bottom lane English → sign-chord → glyph-sequence (labeled "comprehend UP to bit-exact, `b=B(A⁻¹(a))`"). Mark bit-exact vs lossy hops.
- **FIG-B2** Two-panel direction figure (the ROOT): panel A the abelian bind with `cat`/`tac` collapsed to ONE point (zero curvature); panel B the directed digraph with `cat`/`tac` as opposite-charge edge-sets; inset: glyph-scale sandroing trail `c→a→t` with charge arrows.
- **FIG-B3** Sign-as-CHORD "staff" (7 parallel parameter staves sounded simultaneously = bit-exact) vs English "melody" (letters left-to-right = lossy).
- **FIG-B5** The ordered concept SPINE as an Eulerian walk (odd-degree nodes flagged, stroke count = `odd_degree//2`), beside a crossed-out "bag of concepts" labeled "NEVER a bag."
- **FIG-B6** Topic-comment vs SVO: the SAME concept-graph walked two ways.
- **FIG-B7** "beat" fanning to distinct sign-chords, each gated by a context axis, stamped **WEAK / EXPERT-HANDOFF**.

**Track C:**
- **FIG-C2** Escape-token ANATOMY: one token dissected into its five fields (MARKER | BASE-TAG nv/fs/u8 | WALK | CONTENT-ADDRESS | REASON), each annotated against its `# srmech-allow` counterpart.
- **FIG-C3** Directed WALK of `C-A-R` as a sandroing walk over base-glyph nodes, edges labeled weight vs charge; companion panel: the abelian bind collapsing `C-A-R` and `R-A-C` to ONE point (F1211) — proving the walk, not the bind, carries order.
- **FIG-C6** Round-trip + honest-refusal: escape → decode → base-glyph walk → Eulerian round-trip back to the EXACT token; parallel branch where an infeasible walk hits the `None` REFUSAL, never a lying partial.
- **FIG-C7** Content-address / three-things-called-random: DERIVED Class-A `sha256` of token content (in-cascade, OK) contrasted with the DRAWN `1080` pin (✗) and STOCHASTIC live-rng seed (✗ defect); AMSC MPR v1 envelope beside genome-native TLV persistence, loose-JSON dump crossed out.
- **FIG-C8** Scale-recursion: the SAME directed-walk escape at glyph-scale (a name's base-glyphs) and token-scale (a name in a corpus), with the `u8:` byte-glyph walk as the deepest recursion for an out-of-base codepoint.
- **FIG-C9** Missing-kernel MAP ratchet: a ranked table of escaped tokens as surfaced build-me candidates on a JPL-style down-only baseline.

---

## 5. NON-CLAIMS / ATTESTATION-TO-VERIFY (every external claim carries a flag; a citation without attestation is not real)

### 5.1 ATTESTED (web-verified in prior passes — carry with retrieved-at + response hash so "verified" is re-verifiable, not asserted)
- **ASL-LEX** — Caselli, N.K., Sevcikova Sehyr, Z., Cohen-Goldberg, A.M., & Emmorey, K. (2017), "ASL-LEX: A lexical database of American Sign Language," *Behavior Research Methods* 49(2):784–801, DOI `10.3758/s13428-016-0742-0`; OA (Chapman/UConn). **v1 ≈ 1,000 signs; ASL-LEX 2.0 (2021) = 2,723 signs.**
- **UNESCO ICH 00073** Vanuatu sand drawings — proclaimed 2003, inscribed 2008, **~80 language groups**, one finger tracing a continuous line. `https://ich.unesco.org/en/RL/vanuatu-sand-drawings-00073`. *(This is the one anchor that bounds the whole bridge.)*
- **Devylder, S. (2022)** "The archipelago of meaning: Methodological contributions to the study of Vanuatu sand drawing," *The Australian Journal of Anthropology* 33(3):279–327, DOI `10.1111/taja.12428`; OA at Munin (`munin.uit.no/handle/10037/28235`) — paywalled DOI has an OA source, so acceptable.
- **Sutton SignWriting Unicode block** U+1D800..U+1DAAF, introduced Unicode 8.0 (2015); SignWriting developed by Valerie Sutton, 1974.
- **Parameter-model chain (citation-defect correction):** Stokoe (1960), "Sign Language Structure," *Studies in Linguistics Occasional Papers* 8, University of Buffalo — gave **THREE** parameters (handshape/location/movement). The 4th (orientation) is **Battison (1978)**; the 5-parameter model is **Liddell & Johnson (1989)**. **DO NOT credit 5 parameters to Stokoe 1960.**

### 5.2 UNATTESTED — MUST be web-verified before entering the record as load-bearing
- **Battison, R. (1978)** "Lexical Borrowing in American Sign Language" (Linstok Press) and **Liddell, S. & Johnson, R. (1989)** "American Sign Language: The Phonological Base," *Sign Language Studies* 64:195–277 — the 3-vs-5-param split is confirmed, but these two must be **carried as full MPR records, not bare recalled names**; verify author/title/venue/year/DOI before ship.
- **In-tree ASL-LEX sign-count (2297 / 2280)** — matches **neither** attested release (~1,000 v1 / 2,723 v2.0). Unattested provenance; make count-reconciliation an explicit MAP action — re-source against a **named** attested release before any count is quoted as data.
- **Parameter cardinalities** (56 handshapes / 37 minor-loc / 12 selected-fingers / 8 movements / 7 flexions / 6 sign-types / 6 major-loc) — **framework-measured from the local loaded subset (Class B), NOT published inventory sizes.** The ~50M lattice / bit-exact claim rests on these local counts. Re-derive against the pinned ASL-LEX release; ASL-LEX codes selected-fingers+flexion rather than a 56-value "Handshape" axis — reconcile against the actual data columns.
- **ISWA "652 symbols in exactly 7 classes"** (F735) — rests on the Wikipedia SignWriting article (secondary). Sutton 1974 + the Unicode block are attested, but **verify the 652 count + 7-class partition against Sutton/ISWA primary documentation**; the ordering/naming of categories 6–7 differs across secondary sources.
- **Scientific American "An Ancient Art Form Topples Assumptions about Mathematics"** (cited F1080 for the Eulerian reading) — title/existence not web-checked; the Euler's-theorem reading is the framework's OWN, this is a supporting secondary source only. Pin exact title/author/date/URL or drop.
- **HamNoSys** (Hamburg Notation System) as a candidate surface in `asl_sign_kernel.toml` — named but not attested (low-stakes; a candidate surface the expert would choose among).
- **Warlpiri sand-drawing symbol semantics** (U = seated person; concentric circles = place/waterhole) attributed to "Nancy Munn ethnographic record" via gallery summaries — Munn primary NOT verified; **these are living cultural / often-sacred meanings belonging to the Warlpiri community.** Framework reads structure only — verify the Munn citation and do NOT treat the meanings as framework data.
- **Language-count inconsistency** — UNESCO 00073 (attested) says ~80 language groups; other records say "~130 spoken languages." **Use the UNESCO ~80 figure; the ~130 is unattested — reconcile or drop.**
- **Foot-flagging-frog cross-species gesture claim** (F1125) — external ethology claim used as a universality anecdote, not load-bearing; verify before any citation.

### 5.3 INTERNAL non-claims (illustrative structural placeholders — NOT asserted ASL data; NOT external, but flag)
- The **manual-alphabet handshape inventory**, the **ni-Vanuatu↔manual-alphabet correspondence**, and **all classifier routings** (F608/F609/F616) are constructed **ILLUSTRATIVE STRUCTURAL PLACEHOLDERS**, dignity-first (F282). The accuracy figures (100% vs 26%, 5/5 recovery, 10/10, `bank`→2 chords) are computed on constructed chords — **not measurements on real ASL; must not be read as empirical ASL results.**
- The **`1080` coupling seed** (`COUPLE = hdc.klein4_expand(LEAF, 1080)`) is a **DRAWN magic number** (three-things-called-random). **Blocking precondition:** de-magick to a Class-A content-address (`sha256_bytes` of a named source descriptor) before it becomes an undeclared pin baked into the new chromosome. Prove round-trip equivalence before/after.
- **"Iconicity refuted"** must be scoped to the **measured local subset** (chord-alone carries ~0.02 abs signal on the loaded subset), NOT asserted as a field-level refutation of sign-linguistics iconicity scholarship.

---

## 6. THE NEXT QUESTION — handed to the expert (F282: shape it, do not answer it)

The framework's deliverable is the next **question**, handed to a Deaf / sign-linguistics expert (with a collocation-rich sense source), framed as coupling-character questions the framework supplies structure for but does not answer:

1. **Is a fingerspelled name a directed glyph-walk over the manual alphabet that maps onto the sandroing Eulerian structure — or is the manual-alphabet base flat/linear?** (F735's falsifiable spatial-vs-linear question, one scale down.) The framework provides the order-PRESERVING/reversible directed encoder but flags that its node-order is **English-orthography-derived (borrowed), not substrate-native** — this question decides whether the mapping is real.
2. **Which surface — Sutton SignWriting Unicode (attested) / HamNoSys (UNATTESTED) / gloss — best preserves the chord + spatial σ_E axis for a Deaf reader** without collapsing to an English token?
3. **Which sign is the correct coupling of concept-to-context** for a polysemous English word (`beat` → ~a dozen signs)? The framework's WSD is measured **weak** (deeper-gloss NULL, gloss-quality-bound); a richer collocation / phrase-level ASL-gloss sense source is required — this is the expert's call, not the framework's.
4. **Does ni-Vanuatu sandroing land on the SignWriting (2D-spatial) side or the linear-text side** when a real sand-drawing kernel and a linear-text kernel are built and measured? (Currently posited structurally, unmeasured.) The companion runnable sub-question: run `sandroing_strokes` + `best_rational` on a real attested multi-character narrative's character-graph — **is the story one-line-drawable** (connected + all-even-degree) or does it need `odd_degree//2` strokes?
5. **Verify the manual-alphabet handshape inventory + the corrected Battison/Liddell-Johnson parameter-model citation, and pin any ASL-LEX sign-count to a named release** (~1,000 v1 / 2,723 v2.0 — not the in-tree 2,297/2,280).

The north star past all three tracks: **inference-through-the-abstract-layer** (R-RBS-LM-25/54) — routing inference through the abstract HV so the SAME translation reads out as English OR ASL-chord OR SignWriting (Rosetta triangulation). Today only the genome REPRESENTATION is layered; **inference does not yet run through the abstract layer.** Tracks A and C are buildable now; Track B is the tractable precursor once its prerequisite ops exist as attested srmech surface; C is the north star.

---

*Scope discipline honored throughout: algebra / eigenbasis / glyph / spectral side only — no CAD/fabrication/handshape geometry. No lineage claims — every step reads what ASL / ni-Vanuatu sandroing / SignWriting ALREADY IS structurally. ASL is a complete living language of the Deaf community; the ni-Vanuatu tradition's meaning belongs to the Ni-Vanuatu community — the framework reads structure only.*

---

The plan proper (lines 1-222) and all verdicts are in hand; I don't need the maps JSON below line 223. Here is the section, returned verbatim as the deliverable.

---

## 7. VERIFICATION PASS (ultracode)

*This section is the record's guarantee that §1–§6 were CHECKED against code and web-verified sources, not asserted. It reconciles the plan as written (lines 1–222) with the code verdicts, the attestation (sources) verdicts, and the structure verdicts. A REFUTED claim is stated as refuted, not softened. No item below may be treated as settled until its precondition is cleared.*

### 7.1 CODE-CLAIMS table (claim → verdict + file:line)

| # | Claim as the plan uses it | Verdict | Evidence (file:line) |
|---|---|---|---|
| 1 | Fingerspell escape emits raw ASCII `fs:C-A-R` — the no-flatten violation, "at `asl.py:167`" (§2.3 L43, A-3 L83, C-1 L127, C-6 L143) | **CONFIRMED — load-bearing defect** | `docs/srmech/siona/siona/asl.py:167` — `out.append("fs:" + "-".join(w.upper()))`, gloss_signs else-branch. Line number exact; `'fs:C-A-R'` also in docstrings L23, L153. |
| 2 | The `1080` coupling seed is a DRAWN magic number, blocking precondition (A-2 L81, C-2 L129, §5.3 L203) | **CONFIRMED — but INCOMPLETE as scoped** | `R-RBS-LM-SIONA231…py:32` `COUPLE = hdc.klein4_expand(LEAF, 1080)`. Labelled DRAWN/unattested in F1259 L13, F1260 L27. Plan names ONLY this site — see #3. |
| 3 | `corpus_store.py` coupling / persistence spine (implicit under A-2, C-5 genome-native steps) | **CONFIRMED DEFECT the plan never states** | `docs/srmech/siona/siona/corpus_store.py:24` `COUPLE = _H.klein4_random(LEAF, seed=1080)` — a SECOND 1080 pin **and** `klein4_random` was **DELETED in rc297** (F1284 L51: "179 files still call klein4_random, which rc297 DELETED … cannot run at all"; F1285 L16). The store spine is **doubly stale: undeclared magic seed + deleted function. It cannot run.** |
| 4 | `siona/asl.py` defines `render`/`sign_chord`/`disambiguate`/`gloss_signs`/`CHORD_PARAMS` (§2.3) | CONFIRMED | asl.py: `CHORD_PARAMS` L32 (7-tuple), `sign_chord` L102, `disambiguate` L108, `gloss_signs` L150, `render` L171; `__all__` L29–30. |
| 5 | `sandroing_strokes` uses Euler closability `max(1, odd_degree//2)` (§2.3 L44, B-3 L107) | CONFIRMED | `docs/srmech/siona/siona/story.py:125` `strokes = max(1, len(odd)//2)`; docstring L117–118. |
| 6 | `asl_sign_kernel.toml` (5-param tier + σ_B/σ_E), `asl_gloss_notation.md`, `asl_corpus.json` (~74 pairs) exist (§2.3 L45–46) | CONFIRMED | All three under `docs/srmech/rbs_lm_research/`. `asl_sign_kernel.toml` has exactly 5 `[[parameter]]` tiers + `[axis.meaning_class]`/`[axis.spatial]`; `asl_corpus.json` `pairs` length 74. |
| 7 | F1213 `word_to_kernel` directed encoder: weight=metric, charge=direction; steps 1–4 PASS, step-5 live swap gated/NOT done (§2.3 L47, A-8 L93) | CONFIRMED | `R-RBS-LM-NIVDIRECTED…py:32,48,49`; finding doc "steps_1_4_PASS" L11–14; step-5 gating L19–20. |
| 8 | The in-tree ASL-LEX count is **"2,297 / 2,280"**, matching neither attested release (§2.3 implied, §5.2 L192, Q5 L216) | **PARTIAL — the numbers exist but the "two readings" framing is REFUTED** | Bundled `asl_lex.json` is **uniformly 2297** by every measure. **2280 is an iconicity-rated subset from `R-RBS-LM-FINDING_1128…md:18`, NOT a second reading of the bundled file — no "2280" appears anywhere in the siona subtree.** Conflating them as "2297/2280 two readings" is wrong (Breakage 10b). |

**Net:** the three defects the plan leans on (asl.py:167 flatten; the 1080 DRAWN seed; corpus_store.py on the deleted `klein4_random`) are all CONFIRMED. The single code claim whose *framing* the verdicts refute is the "2297/2280 two readings" count.

### 7.2 ATTESTATION table — §5.1 / §5.2 reconciled with what web-verification ACTUALLY found

| Citation (as the plan states it) | Reconciled status | Verified MPR / correction |
|---|---|---|
| ASL-LEX 2017 (§5.1 L184) | **ATTESTED** | Caselli, Sevcikova Sehyr, Cohen-Goldberg, Emmorey (2017), *Behavior Research Methods* 49(2):784–801, DOI `10.3758/s13428-016-0742-0`; OA Chapman DigitalCommons; PubMed 27193158. Journal name "Behavior Research Methods" is correct. **Count corrected:** v1 is "nearly 1,000" (~993), not literal 1000. |
| "ASL-LEX 2.0 (2021) = 2,723 signs" attached to the 2017 record (§5.1 L184) | **CORRECTED — wrong record (MPM violation)** | 2,723 is REAL but comes from a **separate 2021 publication**: Sehyr, Caselli, Cohen-Goldberg, Emmorey, *Journal of Deaf Studies and Deaf Education* 26(2):263–277 (different venue, year, lead author). It does **not** live under DOI `10.3758/s13428-016-0742-0`. **Split into its own MPR before any count is re-pinned** (fixes Q5 L216 / §5.2 L192). |
| Stokoe (1960), THREE parameters (§5.1 L188) | **ATTESTED** | Stokoe, *Sign Language Structure*, Studies in Linguistics Occasional Papers 8, Univ. of Buffalo, 1960. tab/dez/sig = 3 params confirmed via secondary sources (1960 monograph, no DOI). Plan's "3 not 5" is correct. |
| Battison (1978), 4th param = orientation (§5.1 L188, §5.2 L191) | **ATTESTED** | Battison, *Lexical Borrowing in American Sign Language*, Linstok Press (Silver Spring, MD), 1978; ERIC ED163785; ISBN 093213002X. Orientation-as-4th confirmed. |
| **"the 5-parameter model is Liddell & Johnson (1989)"** (§5.1 L188, A-7 L91, C-2 L129) | **CORRECTED — the plan's headline "fix" is itself wrong** | L&J (1989), *Sign Language Studies* 64:195–277 (ERIC EJ395282) is the **Movement-Hold segmental model**, NOT a 5-parameter model; it does **not** add a 5th parameter. The 5th parameter (nonmanual/facial) is a distinct lineage. **Keep "movement-hold" for L&J; drop the "5-parameter" attribution.** (Breakage 1.) |
| Sutton SignWriting Unicode block U+1D800..U+1DAAF, Unicode 8.0 (2015); Sutton 1974 (§5.1 L187) | **ATTESTED** | Block range, version 8.0 (June 2015), and 1974 authorship all verified. Precision note: 672 assigned code points of 688. 1974 = application to sign; do not conflate with 1966 DanceWriting origin. |
| Devylder (2022), TAJA "33(3):279–327" (§5.1 L186) | **CORRECTED** | Volume/issue is **33(2)**:279–327 (Wiley TOC + Munin agree), not 33(3). DOI `10.1111/taja.12428` paywalled (HTTP 402); OA Munin `hdl.handle.net/10037/28235` holds. **Attestation holds once the issue number is fixed.** (Breakage 7.) |
| ISWA "652 symbols in exactly 7 classes" (§5.2 L194, C-2/C-3 framing) | **CORRECTED** | Primary source is the **IETF draft `draft-slevinski-iswa-2010-00`** (Sutton & Slevinski, 2011), NOT Wikipedia. Verbatim: "7 categories … 30 groups … 652 **bases**." **652 is the count of BASE symbols; the full set is 37,811.** Say "652 **base** symbols in 7 categories." 7 categories corroborated at signbank.org/iswa. (Breakage 10a.) |
| UNESCO ICH 00073 (§5.1 L185) | **ATTESTED** | Proclaimed 2003 / inscribed 2008; "~80 language groups" scoped to the central/northern islands; one-finger continuous line. |
| Munn, *Walbiri Iconography* (1973) (§5.2 L197) | **ATTESTED (citation) — meanings NOT framework data** | Munn, Cornell Univ. Press, 1973; ISBN 9780801407390; Internet Archive scan. Title spelling "Walbiri" verbatim; use "Warlpiri" for the people. **Cultural-meaning guard holds: the symbol semantics are Warlpiri cultural knowledge, cited ethnographically only, never imported as substrate values.** |
| Scientific American (Da Silva) (§5.2 L195) | **CORRECTED (exists, wrong date)** | Alban Da Silva, ed. Daisy Yuhas, published **Nov 27, 2023** (not Feb 2024). Popular-science piece — cite as journalism, not a primary source. Supplies the national figure of **138** vernacular languages. |
| In-tree count 2297 (and phantom 2280); parameter cardinalities (56 handshapes / 37 minor-loc / …); HamNoSys; foot-flagging-frog claim (§5.2 L192–L199) | **UNATTESTED — MUST NOT enter the record as load-bearing** | 2297 has no attested provenance and 2280 is a mislabelled iconicity subset; the cardinalities are framework-measured from the local loaded subset (Class B), **not** published inventory sizes; HamNoSys and the ethology anecdote are named-not-verified. None may support a data claim until re-sourced against a **named** attested release. |
| "UNESCO ~80 vs ~130 languages — reconcile or drop" (§5.2 L198) | **CORRECTED — the framing itself is the error** | The two figures are **not contradictory**: ~80 = the central/northern **sand-drawing region**; the **national** figure is **138** (not 130). Do not frame as a discrepancy; state both scopes. (Breakage 10d.) |

### 7.3 STRUCTURAL-claims verdicts (with F-number basis)

| Structural claim | Verdict | Basis / where it breaks |
|---|---|---|
| **Abelian base = zero curvature** (§1 L19, FIG-B2/FIG-C3): the live ni-Vanuatu base is the abelian Klein-4 bind, metric-only, `cat`==`tac` (sim ~1.000); direction lives only in the non-abelian channel (magnetic-Laplacian charge / `the_one` winding / `cd_mult`), prototyped not swapped in | **CONFIRMED (structure) — provenance tags un-attestable** | Durable basis: F861 (Klein-4 order-free), F761 (glyph-bundle base), F862 (order in non-commutative `cd_mult`), F1079 (winding curvature), `magnetic_laplacian(charges=)` rc105/rc107. **But the cited ledger numbers F1211 / F1213 / F1255 appear NOWHERE in the repo or auto-memory** — they are session-ledger findings; the structure holds, the tags do not attest. |
| **7-class heptad** (§1 L15, CLAIM 2): SignWriting's 7 ISWA classes = the framework heptad (the 7 of 1:3:7:3); same duality pole as ni-Vanuatu | **PARTIAL** | Durable: the heptad (D–M cascade-detection heptad, the "7" of 1:3:7:3) is established; "SignWriting = same pole as ni-Vanuatu" holds (F761, F737). **NOVEL / un-recorded:** the specific identity "the 7 ISWA categories map onto the framework heptad" is the **plan's own hypothesis** — "ISWA" appears in NEITHER repo nor auto-memory and **F735 appears nowhere**. Present the ISWA-7=heptad mapping as a conjecture for the expert, not settled structure. (Breakage 9.) |
| **ASL-as-op/operand; English a lossy projection OF ASL** (§1 L12–13, CLAIM 3) | **PARTIAL — directionality REFUTED** | Supported: op(x)operand is the bit-exact transcription unit (F1154); ASL is order-native/article-free as its own substrate (F982). **REFUTED:** the record's projection direction is **byte/glyph-BASE → English**, with **ASL a PEER of the base** (F761: SignWriting/ASL "at the same level" as ni-Vanuatu; R-RBS-LM-27 treats English↔ASL as a parallel-corpus translation pair). "English is a lossy projection OF ASL specifically" is **not attested and cuts against F761**. **F1128 is a session-ledger number absent from the durable record.** Defensible restatement: "English is a lossy projection of the order-native byte/glyph base, at which ASL is a peer." (Breakage 4.) |

*Provenance note (Breakage 8):* the plan's most load-bearing tags — **F1211, F1213, F1255, F1128, F735, F737, F735** — are session-ledger findings; F735 in particular appears nowhere. The *structure* each describes is confirmed against durable sources, but under MPM the tags themselves are the internal analogue of a bare recalled citation: **mark them as session-ledger provenance, not durable findings.**

> **[main-loop correction, 2026-07-22]** The verification agent wrote that F735 "appears nowhere" and F1128 is "absent from the durable record." Checked: **both findings DO exist** as research-tree files (`R-RBS-LM-FINDING_735_signwriting_seven_class_kernel_2d_spatial_pole.md`, `R-RBS-LM-FINDING_1128_*.md`; 9 files reference F735). The agent's *substantive* point stands — these are **session-ledger** (research-tree) findings, NOT durable srmech-package / auto-memory records, and should be marked as such — but "appears nowhere" is an overstatement. The meta-lesson: the verification pass itself needed a check, and got one.


### 7.4 CORRECTIONS REQUIRED BEFORE BUILD (adversarial breakages, most-severe first)

1. **[SEVERE — refuted "correction" shipped as authoritative] Drop the "L&J 1989 = 5-parameter model" claim.** L&J 1989 is the Movement-Hold segmental model; it adds no 5th parameter. Fix §5.1 L188, A-7 L91, C-2 L129 to keep "movement-hold" for L&J; the 5th parameter (nonmanual) is a distinct lineage. Battison 1978 = orientation (4th) stays.
2. **[SEVERE — unattested count on the wrong record] Split the 2,723 count into its own MPR.** It belongs to Sehyr et al. 2021, *J. Deaf Studies and Deaf Education* 26(2):263–277 — not the 2017 DOI. Fix §5.1 L184, §5.2 L192, Q5 L216 before any in-tree count is re-pinned "against 2,723 v2.0."
3. **[SEVERE — incomplete de-magick + non-runnable spine] De-magick BOTH 1080 sites and migrate off the deleted function.** The precondition (A-2, C-2, §5.3) names only `klein4_expand(LEAF,1080)`. It must also cover `corpus_store.py:24` `klein4_random(LEAF, seed=1080)` — which additionally calls the **rc297-deleted** `klein4_random`. Migrate `corpus_store.py` to `klein4_expand(D, seed)` and derive the seed from a named attested Class-A descriptor **before any chromosome ships**. Until then the persistence layer (A-2/C-5) is non-runnable.
4. **[HIGH — structural directionality refuted] Restate §1 L12–13.** Replace "English is a lossy projection OF that glyph-concept layer [ASL]" with "English is a lossy projection of the order-native byte/glyph base, at which ASL is a **peer**" (F761/F982/R-RBS-LM-27). Remove the ASL-as-unique-source framing.
5. **[HIGH — placeholder figures presented as fact in-line] Flag every accuracy number at its use site.** "100% vs 26%" (A-4 L85, B-2 L105), "5/5, 10/10, bank→2 chords," "~6× byte-signal / ~0.02 abs" (A-6 L89) are computed on constructed chords. The disclosure is siloed in §5.3; each in-line use must carry the ILLUSTRATIVE / expert-verify flag inline, not only in the appendix.
6. **[MEDIUM — residual English-orthography flatten survives the fix] Flag the fingerspell path as a known residual, not solved.** A-3 (L83) concedes the replacement walk's node-sequence is English-orthography-derived — a borrowed order, not substrate-native. The no-flatten guarantee is therefore **not met** for the fingerspell path; the whole `manual_alphabet` chromosome is English-alphabet-indexed. Mark it a known residual (Q1), not a closed item.
7. **[MEDIUM — issue number wrong] Fix Devylder to 33(2):279–327** (§5.1 L186). Attestation holds via OA Munin once corrected; the Wiley DOI is paywalled (402).
8. **[MEDIUM — internal F-tags unverifiable] Mark F1211/F1213/F1255/F1128/F735/F737 as session-ledger provenance.** The structure they describe is confirmed; the tags are not durable findings and cannot be cited as attestation.
9. **[MEDIUM — novel hypothesis as recorded finding] Present "ISWA-7 = framework heptad" as a conjecture handed to the expert.** The heptad and same-pole placement are durable; the ISWA-7 mapping and F735 are novel/unverified.
10. **[LOW/MEDIUM — count mis-descriptions] Fix four data descriptions:** (a) "652 **base** symbols in 7 categories" (full set 37,811); (b) drop "2297/2280 two readings" — the bundled file is uniformly 2297 and 2280 is a mislabelled iconicity subset; (c) v1 = "nearly 1,000" (~993); (d) the UNESCO "~80 vs ~130" is not a discrepancy — ~80 = sand-drawing region, national = **138**.
11. **[LOW — self-flagged internal contradiction] Reconcile op availability before Track B is scheduled.** §2.1 lists `glyph_stream` / `eulerian_path` / `eulerian_circuit` as shipped while B-0 (L101) says they "do not exist on disk." Resolve the on-disk status (the maps say Eulerian graduated in via F1224); B must not run on ops asserted-but-absent.

*Cultural-meaning discipline (Warlpiri/Vanuatu semantics as community knowledge, not framework data) is correctly honored in the plan (§5.2 L197, §5.3, footer) and is NOT a breakage.*

### 7.5 BOTTOM LINE

The plan is **safe to lodge as a research + action plan, with the §7.4 items as explicit preconditions** — its structural thesis survives verification (the abelian-base/zero-curvature reading is CONFIRMED, the heptad and same-pole placement are durable), its three named code defects are all real (asl.py:167 flatten, the 1080 DRAWN seed, corpus_store.py on deleted `klein4_random`), and its scope discipline and cultural-meaning guards are honored. It is **NOT safe to build from as written.** The hard blockers, all of which must clear before any chromosome or persistence step ships, are: (1) the headline citation "correction" is itself wrong — L&J 1989 is Movement-Hold, not a 5-parameter model, so the plan currently ships a false fact dressed as the authoritative fix (Breakage 1); (2) the 2,723 count is attached to the wrong record, an MPM attestation violation that propagates into the expert handoff (Breakage 2); and (3) the de-magick precondition is incomplete and the persistence spine is non-runnable — `corpus_store.py` carries a second undeclared 1080 pin **and** calls a function deleted in rc297, so the store the genome-native steps ride on cannot execute (Breakage 3). Everything else (directionality restatement, in-line placeholder flags, Devylder issue number, session-ledger tag marking, ISWA conjecture framing, the four count fixes, the Track B op-availability contradiction) is a correction-before-build, not a lodge blocker. Lodge the plan with §7 attached as its checked-not-asserted guarantee; gate the build on Breakages 1–3.
