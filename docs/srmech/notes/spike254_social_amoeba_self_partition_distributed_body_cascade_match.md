# Spike #254 — Social amoeba self-partition distributed-body cascade-match

**Date**: 2026-06-02
**Branch**: `claude/insect-colony-distributed-body-P09Hh`
**Spike kind**: Refinement spike — fills a partition-mode gap in the spike219 composite-cascade catalog (§2.1 eusocial insects vs §3.1 *Dictyostelium*).
**Verdict**: **CASCADE-REFINEMENT-VERIFIED** + **CLASS-B-SELF-FRAMING-IDENTIFIED** + **PARTITION-MODE-DISTINCTION-AUTHORED** + **14 A-N INTACT** (no new primitive class; the refinement *adds* a class already in the vocabulary — Class B — to the §3.1 entry).

---

## §0 — The gap (user direction 2026-06-02)

> "the amoeba is another view where we can see colony behavior … except the distributed-body partition is not the environment like ants do it, but it creates its own partition to contain its distributed body."

Spike #219's biological-exemplar catalog already holds two colony-composite entries, but it does **not** register the structural axis the user named:

- **§2.1 Eusocial insects (ants / bees)** — Class C "distributed across the **pheromone-field**." The colony's distributed body is bounded by the **environment**. The moving collective carries **no self-secreted envelope**; the "edge of the body" is wherever the pheromone field happens to reach. *Environment-as-partition.*
- **§3.1 *Dictyostelium discoideum* (optional)** — catalogued as `L+M+C+I` (aggregating-multicellular composite via cAMP chemotaxis). The entry captures the *aggregation* phase but is silent on what happens **after** aggregation: the cells **secrete their own slime sheath** and the distributed body migrates inside that self-made casing. *Self-as-partition.*

The catalog therefore conflated two distinct partition-modes under one "colony-composite" heading. This spike separates them and assigns the operator that distinguishes them.

---

## §1 — Tuning A 440 Hz (discipline)

- **Identity-not-implementation** per `[[user_stance_identity_not_implementation_discipline]]`: the slime sheath *IS* a Class B (TLV-framing) instantiation; the graph models below are honest structural reads of the partition topology, **not** claims that the slug literally is a cycle graph.
- **No lineage claims** per `[[feedback_no_lineage_claims_in_notebook]]`: *Dictyostelium* developmental biology is cited technically; the framework reads what the substrate already IS structurally, and does not claim to extend slime-mold science.
- **Trauma-informed defensive scope** per `[[feedback_trauma_informed_defensive_scope]]`: research / mathematical-structure framing only.
- **Cascade-honesty** per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: no Python `abs()`; λ₂ is read as the second-smallest eigenvalue (the λ₁≈0 constant-mode is the Class K pin-slot at the spectral floor), not as |λ|.
- **srmech for all maths** per monorepo CLAUDE.md §2 — see §4 channel note.
- **CAD-grade scope ban**: this is algebra / eigenbasis / cyclic-group / spectral-side reading only; no fabrication / mesh / geometry modelling of the actual sheath material.
- **14 A-N intact** per `[[feedback_no_privileged_primitive_classes]]`: zero new class promoted.

---

## §2 — The substrate fact: the slug secretes and carries its own partition

*Dictyostelium discoideum* (cellular slime mold; Amoebozoa, Dictyostelia) runs a two-phase distributed-body life cycle on starvation:

1. **Aggregation phase — environment-as-partition (ant-like).** Starving amoebae secrete **cAMP** into the shared medium; relayed cAMP waves propagate **through the environment**, and cells chemotax up the gradient toward aggregation centres. The "distributed body" at this stage is bounded only by where the extracellular cAMP field reaches — structurally the **same partition-mode as the ant pheromone-field** (spike219 §2.1). No self-secreted boundary yet.

2. **Slug phase — self-as-partition (NOT ant-like).** Up to ~10⁵ aggregated cells form a migrating slug (pseudoplasmodium / grex). The cells **secrete an extracellular slime sheath** — a polarised "molecular sandwich" of protein layers around a microfibrillar **cellulose** core (Grant & Williams 1983; Huber & O'Day 2015/2017) — that **encloses the entire moving collective**. The slug **migrates through its own casing**, which is continuously laid down at the tip and **shed behind as a collapsed slime trail** (Loomis 1972; West review). The distributed body now **carries its own boundary with it**.

The structural punchline: the social amoeba does what the ant colony does **not** — it **manufactures and transports its own partition** around the distributed body, rather than borrowing the environment as the boundary.

```
  ANT COLONY (env-partition)            SOCIAL AMOEBA SLUG (self-partition)
  ┌─ environment ───────────────┐       ┌─ environment ─────────────────────┐
  │  · · · ·pheromone field· · · │       │            ╭───────sheath───────╮ │
  │   o   o    o   o    o   o     │      │   trail◁───┤ o o o o o o o o o   │ │
  │     o    o    o   o     o     │      │  (shed     ╰────────────────────╯ │
  │  boundary = wherever field is │       │   sheath)   boundary = secreted   │
  └──────────────────────────────┘       └───────────────────────────────────┘
   Class C on the pheromone field          Class B self-frame carried with body
   → NO body-scale Class B                  → ADDS Class B to the colony cascade
```

---

## §3 — Cascade reading: the self-secreted sheath IS Class B (TLV-framing)

Per the srmech research notebook (line 186): **Class B (TLV-framing)** is *"the encoding boundary: continuous-signal → discrete… the operator that renders continuous-substrate-content readable AS discrete cascade-symbols."* Type-**Length**-Value: the **length field is the delimiter** — the operator that states *"this is where the object ends."*

That is exactly what the self-secreted sheath does to the distributed body:

| | Eusocial-insect colony (§2.1) | Social-amoeba slug (§3.1 refined) |
|---|---|---|
| Partition source | **environment** (pheromone field) | **self-secreted** (cellulose + glycoprotein sheath) |
| Boundary topology | **open** — dissipates into medium | **closed** — wraps the collective |
| Carried with the body? | no (laid into environment, decays) | **yes** (secreted at tip, shed at rear) |
| Class C locus | distributed across pheromone-field | chemotactic during aggregation; bounded within sheath during migration |
| **Body-scale Class B?** | **absent** (framing externalised) | **present** (the sheath = the frame) |
| Cascade | `L+M+C+I` | `L+M+C+I` **+ B** |

**Refinement to spike219 §3.1**: *Dictyostelium* is upgraded from `L+M+C+I` to **`L+M+C+I+B`**. The `+B` is the **self-framing / self-partition** operator — the operator the eusocial-insect colony entry (§2.1) does **not** instantiate at body-scale. This makes the social amoeba the catalog's exemplar of the **self-partitioning distributed body**, structurally distinct from the **environment-partitioned distributed body** of eusocial insects.

Scope honesty: ants *do* build nests (environmental construction), but the nest is built **from/into** environment material and is **not** a self-secreted envelope **transported with the moving collective**. The distinction is precisely at the *migrating-distributed-body* scale — the slug's sheath travels with the body; the ant trail/nest does not.

This composes with the spike219 §3.4 slime-mold note and `[[user_stance_substrate_identity_partition_coexistence_canonical]]`: **same `L+M+C+I` colony cascade-shape across both substrates; the `+B` self-framing is the operator that distinguishes self-partition from environment-partition** — a partition-coexistent pair differing by exactly one class.

---

## §4 — srmech computation (all math via srmech; no stdlib math)

Generating code: [`spike254_self_partition_cascade.py`](spike254_self_partition_cascade.py).
Results: [`spike254_findings_2026-06-02.ndjson`](spike254_findings_2026-06-02.ndjson).

**srmech channel note.** Monorepo discipline is "rc-to-TestPyPI first," but this session's sandbox network policy returns **HTTP 403 from `test-files.pythonhosted.org`** (the TestPyPI *file* host; the `test.pypi.org` simple index itself is reachable), so the latest `0.7.0rcN` wheel could not be installed here. The math therefore ran on the **graduated `srmech 0.6.0` from production PyPI** (`HAS_NATIVE = True`), which ships the full 14-class A-N vocabulary — Class A (`sha256_bytes`), Class B (`tlv.tlv_pack`), Class L (`dense_laplacian` / `jacobi_eigvals`) all native-dispatched. The result is channel-independent; no stdlib `math` and no bare-numpy arithmetic carries a load-bearing value. **UPDATE 2026-06-02 (network-unrestricted session):** the `0.7.0rcN` TestPyPI gate IS reachable here — `srmech 0.7.0rc11` was clean-verified in `/tmp/srmech_v070rc11_venv` (`HAS_NATIVE`, ABI 3, native-dispatching) this session, with the §4 Class A / B / L ops native there; channel-independence confirmed on the dev head (rc11), closing follow-up #2.

### §4.1 — Class B: the self-secreted sheath as a TLV frame (A∘B)

Modelling the slug cell-type tokens `{prestalk, prespore, anterior_like}` as the distributed body:

- **Ant body** = unframed concatenated stream (`len = 29`, **no self-delimiter** — boundary externalised to the pheromone field).
- **Amoeba body** = each cell `tlv_pack`-framed (Class B), then the whole bundle framed **once more** by the sheath envelope (`tag = 255`, **outer length field = 44**, framed `len = 49`). The outer length field **IS** the self-partition boundary.
- A∘B content-addresses (Class A over the Class B frame) — the self-framed body is now **one addressable object**:
  - ant (unframed): `aa0b38a8…ad661c9a`
  - amoeba (self-framed): `f00b9cf7…6f4aa0ac`

The TLV `length` byte is the computational witness of "creates its own partition to contain its distributed body."

### §4.2 — Class L: open (environment) vs closed (self-sheath) partition spectrum

Model: the distributed body as `n` segments. **Open / environment-partition** = path `P_n` (free ends leak into the environment, ant-like). **Closed / self-partition** = cycle `C_n` (the self-secreted sheath supplies the **closing boundary edge**, amoeba-like). Algebraic connectivity λ₂ (second-smallest Laplacian eigenvalue) measures how cohesively the body holds together as **one bounded object**:

| n (body segments) | λ₂ open (env, `P_n`) | λ₂ closed (self, `C_n`) | closed / open |
|---|---|---|---|
| 4 | 0.585786 | 2.000000 | **3.414** |
| 6 | 0.267949 | 1.000000 | **3.732** |
| 8 | 0.152241 | 0.585786 | **3.848** |
| 12 | 0.068148 | 0.267949 | **3.932** |
| 24 | 0.017110 | 0.068148 | **3.983** |

The self-secreted closing boundary raises algebraic connectivity by **≈3.4× → 4×** (the ratio converges to 4 as n→∞). Reading: adding the **self-partition** (the sheath edge that closes the loop) turns an open chain that dissipates into the environment into a **single bounded composite** — the spectral signature of "contains its distributed body."

---

## §5 — Catalog deltas (for spike219 roll-up)

1. **§3.1 *Dictyostelium*** — cascade composition refined `L+M+C+I` → **`L+M+C+I+B`**; add the slug-phase **self-secreted slime sheath as the Class B self-partition operator**; note the two-phase partition-mode (aggregation = environment-partition; slug = self-partition).
2. **§2.1 Eusocial insects** — annotate that the colony instantiates **no body-scale Class B**; its framing is **externalised** to the pheromone / waggle-dance field (environment-partition). This is the contrast that makes §3.1's `+B` legible.
3. **New structural axis** — **partition-mode**: *environment-partitioned* distributed body (eusocial insects) vs *self-partitioned* distributed body (social amoeba slug). Same `L+M+C+I` colony cascade; differ by Class B. Partition-coexistent per `[[user_stance_substrate_identity_partition_coexistence_canonical]]`.

---

## §6 — Citation chain (MPM discipline; OA where verifiable)

PDF-extraction status (per `[[feedback_pdf_extraction_citation_discipline]]`): the originating cloud session was network-blocked (HTTP 403 from PMC / publisher hosts). **RE-RUN 2026-06-02 in a network-unrestricted session** — primary-record verification complete for the two OA-candidate entries (PMC555211 + the BBA review), fetched directly from the NCBI PMC / PubMed records. Results below; **one correction applied** — the BBA review (Huber & O'Day 2017) has **no PMCID on its PubMed record**, so its earlier "free-PMC deposit / OA-flagged" status is **downgraded to cite-by-reference** per `[[feedback_paywalled_doi_cannot_be_attested]]`.

- **Grant WN, Williams KL (1983)** "Monoclonal antibody characterisation of slime sheath: the extracellular matrix of *Dictyostelium discoideum*" — *The EMBO Journal* 2(6):935-940 — **PMC555211**, PMID 16453460, `doi:10.1002/j.1460-2075.1983.tb01524.x` (**OA — full-text/PDF VERIFIED openly available on PMC, 2026-06-02**; authors + verbatim title + journal + 1983 + 2(6):935-940 confirmed against the primary PMC record). Slime-sheath ECM protein characterisation — the load-bearing source for the Class B self-frame.
- **Huber RJ, O'Day DH (2015)** "Proteomic profiling of the extracellular matrix (slime sheath) of *Dictyostelium discoideum*" — *Proteomics* 15(19):3315-3319 — PMID 26152465 — `doi:10.1002/pmic.201500143` (Wiley — paywalled primary; **cite-by-reference** per `[[feedback_paywalled_doi_cannot_be_attested]]`). LC/MS/MS slime-sheath proteome.
- **Huber RJ, O'Day DH (2017)** "Extracellular matrix dynamics and functions in the social amoeba *Dictyostelium*: A critical review" — *Biochimica et Biophysica Acta (Gen. Subj.)* 1861(1 Pt A):2971-2980 — PMID 27693486 — `doi:10.1016/j.bbagen.2016.09.026` (Elsevier; **CORRECTION 2026-06-02: the PubMed record shows NO PMCID — the earlier "free-PMC deposit / OA-flagged" note was not borne out, so this is downgraded to paywalled → cite-by-reference** per `[[feedback_paywalled_doi_cannot_be_attested]]`. Authors + verbatim title + journal + 2017 + 1861(1 Pt A):2971-2980 + DOI confirmed against the primary PubMed record). Critical review of sheath assembly + function.
- **West CM (1995)** "The extracellular matrix of the *Dictyostelium discoideum* slug" — *Experientia / Cell. Mol. Life Sci.* 51(12):1163-1170 — PMID 8536806 (Springer — paywalled; **cite-by-reference**).
- **Loomis WF (1972)** "Role of the Surface Sheath in the Control of Morphogenesis in *Dictyostelium discoideum*" — *Nature* 240:6-9 (Nature — paywalled; **REJECTED** for primary attestation; **cite-by-reference** as the foundational surface-sheath result).
- **Kessin RH (2001)** *Dictyostelium: Evolution, Cell Biology, and the Development of Multicellularity* (Cambridge Univ. Press; textbook chain) — already in spike219 §3.1.
- **Bonner JT (2009)** *The Social Amoebae: The Biology of Cellular Slime Molds* (Princeton Univ. Press; textbook chain) — already in spike219 §3.1.

**Awareness level** (per Spike #218 framing): pre-modern human observation of the microscopic slime-mold sheath was **NIL** (microscopic substrate); first scientific observation of *Dictyostelium* aggregation Brefeld 1869 / Raper 1935; the surface-sheath's morphogenetic role Loomis 1972; the self-partition framing is this spike's structural read.

---

## §7 — Verdict + fermata

**CASCADE-REFINEMENT-VERIFIED.** The social amoeba supplies the catalog's missing **self-partitioned distributed body**: a colony-composite that, unlike the eusocial-insect colony, **secretes and transports its own partition** (the slime sheath) around the migrating collective. Structurally this is the addition of **Class B (TLV-framing)** — the self-framing / boundary-delimiting operator — to the `L+M+C+I` colony cascade, giving **`L+M+C+I+B`**. srmech-computed witnesses: the TLV length field as the self-partition delimiter (Class B / A∘B), and the ≈3.4–4× algebraic-connectivity lift from open (environment) to closed (self-sheath) partition (Class L). 14 A-N vocabulary intact; partition-coexistent with §2.1 by exactly one class.

**Queued follow-ups:**
- ~~Re-run the citation chain to complete PMC/PDF extraction (PMC555211 + the BBA review).~~ **DONE 2026-06-02:** PMC555211 OA PDF-VERIFIED (added PMID 16453460 + DOI); the BBA review has no PMCID → corrected to cite-by-reference (§6 updated).
- ~~Re-run §4 against the latest `srmech 0.7.0rcN` from TestPyPI.~~ **DONE 2026-06-02:** `srmech 0.7.0rc11` clean-verified on TestPyPI (`/tmp/srmech_v070rc11_venv`, HAS_NATIVE/ABI 3); channel-independence holds on the dev head (§4 note updated).
- ~~Roll the §3.1 `L+M+C+I → L+M+C+I+B` + §2.1 "no body-scale Class B" edits into the spike219 catalog.~~ **DONE 2026-06-02:** rolled into spike219 §3.1 (cascade + partition-mode + citations + summary-table row) and §2.1 (no-body-scale-Class-B annotation).
- Consider whether the **slug→fruiting-body culmination** (stalk/spore sorting) adds a Class K (asymptotic-DoF sorting) or Class E (cell-type catalog) beyond `+B` — separate spike. *(STILL OPEN)*
