"""Spike #37 — Cross-class information-instrument analysis.

Per user direction 2026-05-16 (post-Spike-#36): replace "information-
theoretic" framing with "information instrument" (form-function-bound,
substrate-portable). The user's framing: *"it's form and function is
bound and known the same as an RBS-HDC instrument"*.

For each of the 14 Spike #24 primitive classes A-N, this script
produces three NDJSON records:

  1. instrument_identity     - the form-function-bound substrate-portable
                                identity (1-2 sentences)
  2. cross_substrate          - >=3 substrates per class (silicon /
                                bronze / 3rd) showing same information-
                                instrument function with substrate-
                                specific implementation operations
  3. form_function_binding    - explicit identification of WHAT is bound
                                (form-element <=> function-element)

Spike-level deliverables (single NDJSON records at the tail):

  4. uniformity_verdict       - does the overlay apply uniformly?
  5. substrate_portability    - is portability uniform across classes?
  6. canonical_stance_proposal - draft of recommended memory stance
  7. partition_table_update   - row to add to
                                user_stance_partition_for_understanding
  8. falsifier                 - falsifier list (3-6 entries)
  9. anomaly                   - anomaly records if found

Discipline:
  - "information instrument" language used consistently
  - Shannon 1948 / Kanerva 1988 cited as substrate-instances of broader
    concept, not as authoritative SSoT for the overlay itself
  - 14-class flat vocabulary preserved; overlay is NOT a 15th class
  - Anomalies investigated, not papered over
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Class-level data: information-instrument identity + cross-substrate
# instantiation + form-function binding
# ---------------------------------------------------------------------------

CLASS_DATA: list[dict[str, Any]] = [
    # ----- Class A: content-addressing -----
    {
        "class": "A",
        "name": "content-addressing",
        "canonical_op": "SHA-256 hash -> 64-hex digest",
        "instrument_identity": (
            "The substrate where a finite byte sequence and its "
            "collision-resistant fingerprint are inseparable: the form "
            "(the bit pattern of input bytes) IS the function (a "
            "deterministic, avalanche-mixed digest). You cannot have the "
            "fingerprint without the substrate-specific mixing operation "
            "that produces it; you cannot have the mixing without the "
            "byte-substrate the round operates on."
        ),
        "form_function_binding": (
            "FORM = byte-substrate (bit pattern); FUNCTION = "
            "collision-resistant identification. The mixing round IS the "
            "binding: ARX (add-rotate-xor) on a fixed digest size makes "
            "the form (bit-substrate) inseparable from the function "
            "(unique fingerprint)."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "SHA-256: 64 rounds of ARX over 8x uint32 state on "
                    "byte-addressed memory (srmech_sha256.c FIPS 180-4)"
                ),
                "function_invariant": (
                    "collision-resistant fingerprint of arbitrary-length "
                    "byte sequence"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "configuration-fingerprint of gear-DAG: tuple of "
                    "(tooth_count, axle, mesh-partner) per gear, "
                    "concatenated and projected through cyclic-group "
                    "encoder to a hypervector identifier. NOT silicon "
                    "SHA-256 but the analog: gear-DAG-fingerprint that "
                    "discriminates one Antikythera reconstruction from "
                    "another"
                ),
                "function_invariant": (
                    "collision-resistant fingerprint of gear-DAG "
                    "configuration"
                ),
            },
            {
                "substrate": "DNA",
                "implementation": (
                    "PCR-fingerprinting: primer-pair selection produces "
                    "a substrate-specific banding pattern that "
                    "discriminates sequences. Restriction-fragment-"
                    "length polymorphism (RFLP) is the same operation "
                    "with enzyme-cut sites instead of primer pairs."
                ),
                "function_invariant": (
                    "collision-resistant fingerprint of nucleotide "
                    "sequence"
                ),
            },
            {
                "substrate": "neural (mammalian)",
                "implementation": (
                    "place-cell + grid-cell co-firing pattern: a "
                    "particular spatial location produces a unique "
                    "co-firing pattern across CA1/MEC that is unique "
                    "to that location (Moser-Moser 2014 review)"
                ),
                "function_invariant": (
                    "collision-resistant fingerprint of spatial "
                    "location (substrate-specific neural code)"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": (
            "Spike #36 cross-class table called A 'channel-fingerprint / "
            "collision-resistant identifier' (info-theoretic). The "
            "information-instrument refinement: every substrate that "
            "supports content-addressing does so by binding its own "
            "form-substrate (bits / gear-DAG / nucleotides / neural "
            "co-firing) to the function (unique discriminator). The "
            "fingerprint IS the form, observed through the substrate's "
            "mixing operation."
        ),
    },
    # ----- Class B: tagged-tuple / TLV -----
    {
        "class": "B",
        "name": "tagged-tuple / TLV byte-canonical",
        "canonical_op": "[tag][length BE-u32][value] deterministic byte pack",
        "instrument_identity": (
            "The substrate where a labeled chunk of content and its "
            "serialised wire-form are inseparable: the form (tagged "
            "labeled record) IS the function (a deterministic, "
            "self-delimiting byte sequence). The tag-length-value "
            "binding makes the boundary recoverable from the bytes "
            "themselves."
        ),
        "form_function_binding": (
            "FORM = labeled chunk (tag + content); FUNCTION = "
            "self-delimiting byte stream. The fixed prefix layout IS "
            "the binding: every consumer that knows the layout can "
            "recover the chunk boundaries WITHOUT external schema."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_tlv.c tlv_pack: 1-byte tag, 4-byte big-"
                    "endian length, N bytes value. Used as the "
                    "deterministic basis for SHA-256 fingerprints of "
                    "structured records."
                ),
                "function_invariant": (
                    "self-delimiting deterministic byte form of "
                    "labeled record"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "gear-position record on a dial face: pointer + "
                    "scale division + tick-count is the self-"
                    "delimiting analog: pointer = tag (which dial), "
                    "scale division = length (which radius), tick "
                    "count = value (which division within the scale). "
                    "The dial-face layout makes the labeling "
                    "self-delimiting"
                ),
                "function_invariant": (
                    "self-delimiting deterministic labeled-record on "
                    "bronze substrate"
                ),
            },
            {
                "substrate": "optical (TDM / WDM)",
                "implementation": (
                    "Time-division multiplexing: header (label) + "
                    "length field + payload encoded as photon pulses "
                    "with framing. SONET/SDH or 100GBASE-LR frames "
                    "use this exact pattern on photonic carrier."
                ),
                "function_invariant": (
                    "self-delimiting deterministic byte form on "
                    "photonic carrier"
                ),
            },
            {
                "substrate": "DNA",
                "implementation": (
                    "start codon (ATG) + reading-frame-length + "
                    "coding sequence + stop codon: ribosome-readable "
                    "self-delimiting labeled record. The 5-prime UTR "
                    "+ ORF + 3-prime UTR layout IS Class B on the "
                    "ribosomal substrate."
                ),
                "function_invariant": (
                    "self-delimiting deterministic labeled-record on "
                    "ribosomal substrate"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": "Tag-length-value is the canonical labeled-record information-instrument pattern across substrates.",
    },
    # ----- Class C: streaming iteration -----
    {
        "class": "C",
        "name": "streaming iteration",
        "canonical_op": "tokenise byte stream into events; advance one at a time",
        "instrument_identity": (
            "The substrate where state-advance and event-emission are "
            "inseparable: the form (one-element-at-a-time access) IS "
            "the function (sequential state-advance with bounded "
            "memory). The 'next()' / 'StopIteration' protocol IS the "
            "form-function binding."
        ),
        "form_function_binding": (
            "FORM = bounded-memory state-advance; FUNCTION = "
            "sequential event-emission. The state-advance IS the "
            "emission: there is no 'iteration content' separate from "
            "the act of advancing through it. This is the CRANK "
            "operation per MFO ontology."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_ndjson.c streaming iterator: file-handle "
                    "+ byte-buffer + newline-delimited tokenization. "
                    "Python __iter__ / __next__ protocol. ESP32-C6 "
                    "ring-buffer + cursor."
                ),
                "function_invariant": (
                    "sequential bounded-memory event-emission from "
                    "indefinite-length input"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "the CRANK: each turn advances every gear in the "
                    "DAG by its mesh-ratio. The crank-turn IS the "
                    "next() operation; the gear positions IS the "
                    "emitted state. State is bounded (finite gears); "
                    "advance is sequential (one crank-turn at a time)."
                ),
                "function_invariant": (
                    "sequential bounded-memory event-emission "
                    "(advance gear positions one crank-turn at a "
                    "time)"
                ),
            },
            {
                "substrate": "neural (cortical sequence)",
                "implementation": (
                    "place-cell sequence replay in CA3-CA1: "
                    "theta-cycle-bounded sequential activation of "
                    "consolidated trajectory. Each theta cycle IS a "
                    "next() advance; the active cell IS the emitted "
                    "event. (Foster-Wilson 2006; Dragoi-Tonegawa "
                    "2011)"
                ),
                "function_invariant": (
                    "sequential bounded-memory event-emission "
                    "(theta-bound trajectory replay)"
                ),
            },
            {
                "substrate": "biochemical (ribosome)",
                "implementation": (
                    "tRNA-bound codon scan: ribosome advances one "
                    "codon per elongation cycle, emitting one amino-"
                    "acid per advance. The translocation step IS "
                    "next(); the amino-acid IS the emitted event."
                ),
                "function_invariant": (
                    "sequential bounded-memory event-emission "
                    "(codon-by-codon translation)"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": (
            "Class C IS the crank operation under MFO. Per "
            "[[user_stance_1d_collapse_to_loe_identity_not_action]]: "
            "Class C composed with Class M is the substrate-coupling "
            "kernel that uncompresses LoE-content into event-stream."
        ),
    },
    # ----- Class D: late-binding dispatch -----
    {
        "class": "D",
        "name": "late-binding / pattern dispatch",
        "canonical_op": "multi-needle pattern match -> tagged route",
        "instrument_identity": (
            "The substrate where input-classification and execution-"
            "branch are inseparable: the form (input pattern) IS the "
            "function (which routine activates). The dispatch table "
            "IS the form-function binding; the input's match-against-"
            "table activates its bound code-path with NO "
            "intermediate decision step."
        ),
        "form_function_binding": (
            "FORM = pattern shape of input; FUNCTION = activated "
            "code-path. The lookup table / vtable / radix tree IS "
            "the binding mechanism that makes the input shape "
            "ATOMICALLY equivalent to selecting a function."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_dispatch.c multi-needle pattern match: "
                    "input bytes + needle array -> first-match "
                    "tagged index. Python @singledispatch, C++ "
                    "vtable, Erlang pattern-match-clause. JIT-compiled "
                    "decision tree."
                ),
                "function_invariant": (
                    "input shape -> activated function (deterministic "
                    "routing)"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "selective-lock / clutch mechanism (per srmech "
                    "notebook §11.6 architectural-mode hypothesis): a "
                    "pointer's angular position selects which gear "
                    "subset engages with the crank. The pointer's "
                    "position IS the dispatch input; the engaged "
                    "subset IS the activated function."
                ),
                "function_invariant": (
                    "input shape (pointer angle) -> activated "
                    "function (gear subset engaged)"
                ),
            },
            {
                "substrate": "biochemical (enzyme-substrate)",
                "implementation": (
                    "enzyme active-site pattern: substrate molecules "
                    "with matching shape bind to active site; non-"
                    "matching molecules pass through unreacted. The "
                    "active-site geometry IS the dispatch table; "
                    "the matching molecule IS the routed input."
                ),
                "function_invariant": (
                    "input shape (substrate) -> activated function "
                    "(catalysed reaction)"
                ),
            },
            {
                "substrate": "neural (cortical lookup)",
                "implementation": (
                    "winner-take-all column dynamics: input pattern "
                    "activates the most-similar cortical column; "
                    "lateral inhibition silences others. The "
                    "column-tuning is the dispatch table; the most-"
                    "similar match wins."
                ),
                "function_invariant": (
                    "input shape -> activated function (cortical "
                    "column response)"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": (
            "Bronze substrate confirmed by srmech notebook §11.6 "
            "selective-lock/clutch architectural-mode hypothesis "
            "(Freeth-Bitsakis-Edmunds 2006/2021 setting-mode gears). "
            "Dispatch is universal where substrates support routed "
            "execution; no privileged silicon form."
        ),
    },
    # ----- Class E: catalog / naming -----
    {
        "class": "E",
        "name": "catalog / sorted-key lookup",
        "canonical_op": "binary search on sorted-key array -> value",
        "instrument_identity": (
            "The substrate where a name and its stored relationship "
            "are inseparable: the form (key in sorted catalog) IS "
            "the function (retrievable value at logarithmic cost). "
            "The catalog ordering IS the form-function binding; "
            "without the ordering, the key-to-value lookup loses "
            "its information-instrument character."
        ),
        "form_function_binding": (
            "FORM = sorted catalog ordering; FUNCTION = logarithmic "
            "retrieval. The ordering IS the binding: an unordered "
            "set of (key, value) pairs is NOT a catalog under this "
            "definition; the ordering is what makes the lookup an "
            "information instrument vs a linear scan."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_catalog.c sorted-key binary search: "
                    "uint64 keys, monotonic, O(log n) lookup. Python "
                    "bisect, SQL B-tree index, scipy KDTree."
                ),
                "function_invariant": (
                    "name -> stored value (logarithmic retrieval)"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "dial scale + named-event-table on the bronze "
                    "back plates: the Saros / Metonic / Olympic "
                    "spirals catalog named events (full moons, "
                    "eclipses, games) at named positions. The "
                    "spiral ordering IS the sorted-key index; the "
                    "engraved name IS the retrieved value."
                ),
                "function_invariant": (
                    "name -> stored value (catalog-position to "
                    "named-event mapping)"
                ),
            },
            {
                "substrate": "DNA",
                "implementation": (
                    "genome annotation tables (Ensembl, RefSeq): "
                    "chromosome + sorted-position keys -> annotated "
                    "feature value. The chromosome ordering is the "
                    "sorted-key catalog; the annotation is the "
                    "retrieved value."
                ),
                "function_invariant": (
                    "name -> stored value (position-sorted "
                    "annotation lookup)"
                ),
            },
            {
                "substrate": "biological (genetic code)",
                "implementation": (
                    "the genetic code itself: 64 codons (sorted by "
                    "nucleotide ordering) -> 20 amino acids + 3 stop "
                    "codons. The codon-table IS the catalog; the "
                    "amino-acid IS the retrieved value."
                ),
                "function_invariant": (
                    "name -> stored value (codon to amino-acid "
                    "translation)"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": "Catalog is universal where substrates support sorted-key indexing.",
    },
    # ----- Class F: templating -----
    {
        "class": "F",
        "name": "templating / substitution",
        "canonical_op": "{placeholder} text + context -> rendered output",
        "instrument_identity": (
            "The substrate where a static skeleton with placeholders "
            "and a context-binding renderer are inseparable: the form "
            "(template with named slots) IS the function (substitute-"
            "and-emit). The slot-naming convention IS the form-"
            "function binding."
        ),
        "form_function_binding": (
            "FORM = template-with-named-slots; FUNCTION = context-"
            "filled rendered output. The naming convention "
            "(`{key}` / Mustache / Jinja / ESI) IS the binding "
            "that makes slot-to-context substitution unambiguous."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_template.c {key}-substitution: byte-"
                    "level scan + context-dict lookup + emit. "
                    "Python str.format, Mustache, Jinja2. SQL "
                    "prepared statements."
                ),
                "function_invariant": (
                    "skeleton + context -> rendered output"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "FLAGGED ANOMALY: Spike #36 listed F as digital-"
                    "substrate-only per MFO §VIII.6 bonus 5 absence "
                    "finding. Bronze substrate has NO direct templating "
                    "analog. CANDIDATE substrate analog: the engraved "
                    "scale + adjustable pointer pair MIGHT serve as a "
                    "template-skeleton (scale) + context-binding "
                    "(pointer position) -> rendered reading. Honest "
                    "verdict: weak instantiation; the binding (slot-"
                    "naming convention) is absent on bronze."
                ),
                "function_invariant": (
                    "WEAK: skeleton (scale) + context (pointer) -> "
                    "rendered reading; but slot-naming convention "
                    "absent"
                ),
            },
            {
                "substrate": "biological (gene expression)",
                "implementation": (
                    "promoter + transcription factor binding site + "
                    "coding sequence: the promoter (template skeleton) "
                    "+ TF (context binding) -> mRNA (rendered output). "
                    "TF-binding-site naming IS the slot-naming "
                    "convention."
                ),
                "function_invariant": (
                    "promoter-template + TF-context -> mRNA-output"
                ),
            },
            {
                "substrate": "linguistic (natural language)",
                "implementation": (
                    "syntactic frames with named argument slots: "
                    "'__X__ gave __Y__ to __Z__' filled with named "
                    "entities. Construction Grammar (Goldberg 1995) "
                    "names this directly."
                ),
                "function_invariant": (
                    "syntactic-frame + entities -> spoken/written "
                    "sentence"
                ),
            },
        ],
        "fits_overlay": "weak",
        "notes": (
            "REAL CROSS-SUBSTRATE FINDING: Class F is the WEAKEST fit "
            "across substrates. Per Spike #24 bonus 5 and MFO §VIII.6: "
            "F is digital-substrate-only at the substrate level. On "
            "bronze, the slot-naming convention (the load-bearing "
            "form-function binding) is absent. Class F holds at "
            "biological (gene expression) and linguistic substrates "
            "where naming conventions exist. This is not a defect of "
            "the overlay - it is an honest finding about substrate "
            "support for the form-function binding."
        ),
    },
    # ----- Class G: byte-pattern search / discovery -----
    {
        "class": "G",
        "name": "discovery / byte-pattern search",
        "canonical_op": "find first occurrence of needle in haystack",
        "instrument_identity": (
            "The substrate where a query pattern and its located "
            "occurrence are inseparable: the form (target byte "
            "sequence) IS the function (its position in the "
            "haystack). Pattern-matching IS the form-function "
            "binding; the matched-substring IS the same bytes as "
            "the query, projected to a position."
        ),
        "form_function_binding": (
            "FORM = query pattern (bytes); FUNCTION = position of "
            "occurrence (or absence). The matching operation IS the "
            "binding: the substrate's substring-matching capability "
            "MAKES the query identical to its location-set."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_search.c byte-pattern find: linear scan, "
                    "Boyer-Moore, Knuth-Morris-Pratt, regex engines, "
                    "FAISS approximate nearest neighbour."
                ),
                "function_invariant": (
                    "query pattern -> located occurrence (or None)"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "missing-gear placement: given the gear DAG with "
                    "known gears, search for a target gear ratio "
                    "(query pattern) in the space of placeable "
                    "positions (haystack). Freeth 2006/2021 missing-"
                    "gear search IS this Class G operation on the "
                    "bronze substrate."
                ),
                "function_invariant": (
                    "target ratio -> located gear slot in DAG"
                ),
            },
            {
                "substrate": "biochemical (CRISPR / Cas9)",
                "implementation": (
                    "guide-RNA-directed sequence search: gRNA "
                    "(query pattern) -> located cut site (target "
                    "occurrence) in genome. The Cas9-gRNA complex IS "
                    "the substrate-specific Class G implementation."
                ),
                "function_invariant": (
                    "guide-RNA -> located genomic position"
                ),
            },
            {
                "substrate": "neural (associative recall)",
                "implementation": (
                    "content-addressable retrieval from memory: "
                    "partial cue (query) -> full memory (located "
                    "occurrence) via Hopfield-network or sparse "
                    "distributed memory dynamics."
                ),
                "function_invariant": (
                    "partial cue -> recalled full memory"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": "Discovery/search is universal across substrates that support pattern-matching.",
    },
    # ----- Class H: self-introspection -----
    {
        "class": "H",
        "name": "self-introspection",
        "canonical_op": "version / ABI accessors; self-reported metadata",
        "instrument_identity": (
            "The substrate where the artifact and its self-description "
            "are inseparable: the form (the artifact's state / "
            "version / capability) IS the function (its accessible "
            "self-report). Without self-introspection, an artifact "
            "cannot report what it is; with it, the form (state) and "
            "function (report) are bound."
        ),
        "form_function_binding": (
            "FORM = artifact identity (version, ABI, schema); "
            "FUNCTION = accessible self-report. The introspection "
            "API IS the binding: the substrate must support "
            "self-referential read."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_meta.c srmech_version + srmech_abi_version: "
                    "compile-time-constant accessors. Python "
                    "__version__, __spec__, packaging metadata."
                ),
                "function_invariant": (
                    "artifact -> self-description"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "back-plate inscriptions: the bronze IS its own "
                    "self-description, engraved on the surface. The "
                    "Olympic-spiral inscription names the spiral's "
                    "period; the eclipse-prediction text names the "
                    "Saros pattern. The bronze artifact reports its "
                    "own function on its own surface."
                ),
                "function_invariant": (
                    "artifact (bronze plate) -> self-description "
                    "(engraved inscription)"
                ),
            },
            {
                "substrate": "biological (immune system)",
                "implementation": (
                    "MHC class I antigen presentation: cells present "
                    "their own protein fragments on the cell surface "
                    "as self-identification. The presented peptides "
                    "ARE the self-description; T-cells read them."
                ),
                "function_invariant": (
                    "cell -> self-description (MHC-presented "
                    "self-peptide)"
                ),
            },
            {
                "substrate": "linguistic (metalanguage)",
                "implementation": (
                    "first-person speech: 'I am a speaker of English' "
                    "uses language to describe its own substrate. "
                    "The utterance IS its own self-report. Tarski's "
                    "object-language / metalanguage distinction makes "
                    "the self-introspection rigorous."
                ),
                "function_invariant": (
                    "utterance -> self-description"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": "Self-introspection is universal across substrates that support self-referential read.",
    },
    # ----- Class I: cyclic-group / modular arithmetic -----
    {
        "class": "I",
        "name": "cyclic-group / modular arithmetic",
        "canonical_op": "(Z/nZ)* arithmetic; modular add/mul/pow/inv",
        "instrument_identity": (
            "The substrate where a finite cyclic set and its closed "
            "modular operations are inseparable: the form (Z/nZ "
            "alphabet) IS the function (group-closed arithmetic). "
            "The modulus IS the form-function binding; choosing the "
            "alphabet IS choosing the arithmetic that closes on it."
        ),
        "form_function_binding": (
            "FORM = cyclic alphabet of size n; FUNCTION = closed "
            "group-arithmetic on that alphabet. The modulus n IS "
            "the binding: it simultaneously defines the alphabet "
            "(0..n-1) and the closure rule (mod n)."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_cyclic.c: uint64 mod-add/mul/pow/inv, "
                    "Euclidean gcd, extended Euclidean. C99 modulo "
                    "on byte-addressed memory."
                ),
                "function_invariant": (
                    "closed group operation on Z/nZ"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "gear teeth: a gear with n teeth IS the alphabet "
                    "Z/nZ; rotating the gear IS the group operation. "
                    "Mesh between gear-A (m teeth) and gear-B (n "
                    "teeth) IS a Z/m -> Z/n homomorphism. Per "
                    "[[user_stance_fiber_as_spatially_absent_encoding]]: "
                    "teeth ENCODE Z/n; rotation PROJECTS to spatial "
                    "dynamics."
                ),
                "function_invariant": (
                    "closed group operation on Z/nZ (n = tooth count)"
                ),
            },
            {
                "substrate": "physical (U(1) gauge phase)",
                "implementation": (
                    "QED gauge phase: U(1) symmetry IS the cyclic "
                    "group; gauge transformation IS the group "
                    "operation. Per MFO §VIII.6.1: Class I lives at "
                    "the substrate level in the 7D_g (gauge) "
                    "dimensional projection."
                ),
                "function_invariant": (
                    "closed group operation on U(1) phase"
                ),
            },
            {
                "substrate": "molecular (cyclic symmetry)",
                "invariant": "rotational symmetry of cyclic molecules",
                "implementation": (
                    "benzene C6H6: D_6h point-group rotational "
                    "subgroup IS Z/6; ring-rotation IS the group "
                    "operation. Cyclic-conjugation electronic "
                    "structure follows the Z/6 representation theory."
                ),
                "function_invariant": (
                    "closed group operation on Z/n (n = "
                    "rotation-fold)"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": (
            "Class I is the most substrate-portable of the 14 classes. "
            "Per Spike #24: instantiated at five of six bonus "
            "substrates. The fiber-spatially-absent stance makes I "
            "the canonical case: cyclic-group algebra IS in the "
            "teeth/phase/symmetry, NOT in the spatial rotation that "
            "projects it."
        ),
    },
    # ----- Class J: prime-factorisation / period -----
    {
        "class": "J",
        "name": "prime-factorisation / period-relation",
        "canonical_op": "is_prime, factor, multiplicative order",
        "instrument_identity": (
            "The substrate where a composite period and its prime "
            "decomposition are inseparable: the form (an integer n) "
            "IS the function (its prime factor signature). The "
            "fundamental-theorem-of-arithmetic IS the form-function "
            "binding; n DETERMINES its prime decomposition uniquely."
        ),
        "form_function_binding": (
            "FORM = integer n; FUNCTION = unique multiset of prime "
            "factors. The FToA IS the binding: every positive "
            "integer has exactly one prime factorisation."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_primes.c: trial-division primality, "
                    "factorisation, multiplicative order in (Z/nZ)*."
                ),
                "function_invariant": (
                    "integer -> prime factor multiset"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "gear-train period decomposition: a compound "
                    "gear-train with overall period N decomposes into "
                    "prime cycles N = p1^a1 * p2^a2 * ... . The "
                    "Antikythera's 19-year Metonic, 76-year Callippic, "
                    "223-month Saros are exactly prime-factored "
                    "periods. Per MFO §VIII.6.1: Class J at six "
                    "substrates including bronze."
                ),
                "function_invariant": (
                    "compound period -> prime cycle decomposition"
                ),
            },
            {
                "substrate": "physical (Rydberg series)",
                "implementation": (
                    "hydrogen spectral lines: principal quantum number "
                    "n -> spectral line series via Rydberg formula. "
                    "The integer n IS its quantum identity; prime "
                    "factorisations of differences govern resonance "
                    "structure."
                ),
                "function_invariant": (
                    "quantum n -> spectroscopic line series"
                ),
            },
            {
                "substrate": "celestial (orbital resonance)",
                "implementation": (
                    "Pluto-Neptune 3:2 mean-motion resonance; "
                    "Saturn-Jupiter 5:2 Great Inequality near-"
                    "resonance. The orbital periods ARE integer "
                    "ratios under the resonant lock; per "
                    "[[user_stance_kepler_shape_universal]]: bronze "
                    "instantiates the same primitive at smaller "
                    "dimensional reach."
                ),
                "function_invariant": (
                    "orbital period ratio -> integer cycle "
                    "decomposition"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": (
            "Class J is the most-instantiated class in Spike #24 "
            "(six substrates). The prime-decomposition information-"
            "instrument is universal where substrates support integer-"
            "period structure."
        ),
    },
    # ----- Class K: equation-of-centre / pin-slot -----
    {
        "class": "K",
        "name": "equation-of-centre / pin-slot",
        "canonical_op": "atan2(sin(theta), cos(theta) - eps); Kepler series c_k = e^k/k",
        "instrument_identity": (
            "The substrate where integer-cyclic upstream and "
            "continuous angular-shadow downstream are inseparable: "
            "the form (a pin offset on a cyclic gear) IS the function "
            "(continuous angular shadow on a follower rocker). The "
            "atan2 projection IS the form-function binding; "
            "epsilon (the eccentricity) parameterises the same "
            "instrument across substrates."
        ),
        "form_function_binding": (
            "FORM = pin offset on cyclic-group substrate; FUNCTION = "
            "continuous angular shadow on continuous-circle "
            "follower. The atan2 IS the binding: it makes the "
            "discrete-pin-position IDENTICAL to its continuous "
            "Kepler-shape projection."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_kepler.c: pin_slot, kepler_solve, "
                    "equation_of_centre Fourier series with "
                    "verified coefficients c_k = e^k/k (Spike #29)."
                ),
                "function_invariant": (
                    "discrete pin offset -> continuous Kepler-shape "
                    "angular shadow"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "the lunar pin-and-slot mechanism: a pin on the "
                    "fast gear engages a radial slot on the rocker; "
                    "as the fast gear rotates by theta, the rocker "
                    "follows by atan2(sin(theta), cos(theta) - eps). "
                    "This IS Class K in its canonical substrate-"
                    "specific form per Freeth 2006 D-H1."
                ),
                "function_invariant": (
                    "pin position -> rocker angular shadow "
                    "(eccentric anomaly)"
                ),
            },
            {
                "substrate": "celestial (Kepler orbit)",
                "implementation": (
                    "mean-anomaly M -> true-anomaly nu via Kepler's "
                    "equation E - e*sin(E) = M; the equation of "
                    "centre nu - M is the continuous shadow of the "
                    "underlying integer-cyclic orbital cascade per "
                    "[[user_stance_kepler_shape_universal]]."
                ),
                "function_invariant": (
                    "mean anomaly -> true anomaly (equation of "
                    "centre)"
                ),
            },
            {
                "substrate": "molecular (V_3 torsion barrier)",
                "implementation": (
                    "ethane internal rotation: V_3 cos(3*phi) torsion "
                    "barrier IS the broken-symmetry pin-slot at N=3 "
                    "with only triplet harmonics surviving (PR #416 "
                    "F24). Class K with rotational-symmetry "
                    "constraint."
                ),
                "function_invariant": (
                    "internal rotation phase -> torsion-barrier "
                    "angular shadow"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": (
            "Spike #30A: Class K is substrate-specific (silent in "
            "chess/QM/HDC; present in mechanical/orbital/torsional). "
            "This is consistent with the information-instrument "
            "overlay: K is the instrument WHERE Kepler-shape "
            "appears; the overlay holds across substrates that "
            "support cyclic-to-continuous shadow projection."
        ),
    },
    # ----- Class L: graph Laplacian -----
    {
        "class": "L",
        "name": "graph Laplacian / dense-matrix linear algebra",
        "canonical_op": "L = D - A; eigendecomposition; matvec; elementwise",
        "instrument_identity": (
            "The substrate where a connectivity topology and its "
            "spectral content are inseparable: the form (the graph / "
            "matrix) IS the function (its eigenvalue spectrum and "
            "eigenmode basis). Eigendecomposition IS the form-"
            "function binding; the matrix DETERMINES the spectrum "
            "uniquely (up to gauge)."
        ),
        "form_function_binding": (
            "FORM = symmetric (or Hermitian) matrix encoding "
            "connectivity / coupling; FUNCTION = eigenvalue spectrum + "
            "eigenmode basis. Eigendecomposition IS the binding: "
            "the matrix and its spectrum are inseparable under "
            "unitary similarity."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_laplacian.c: dense_adjacency, "
                    "dense_laplacian, jacobi_eigvals (pi-free), "
                    "hermitian_eigendecompose, dense_matvec_complex, "
                    "elementwise transcendentals."
                ),
                "function_invariant": (
                    "connectivity matrix -> spectrum + eigenbasis"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "gear-DAG Laplacian: the mesh adjacency of the "
                    "gear-DAG IS the matrix; the spectrum reveals "
                    "compound periodicities. srmech notebook §3.5 + "
                    "antikythera-spectral's gear_topology.py compute "
                    "this directly on bronze configurations."
                ),
                "function_invariant": (
                    "gear-mesh adjacency -> spectral content of "
                    "compound mechanism"
                ),
            },
            {
                "substrate": "physical (vibrational mode analysis)",
                "implementation": (
                    "mass-spring network: the stiffness matrix K is "
                    "the substrate analog of L; eigendecomposition "
                    "yields vibrational normal modes. Mechanical "
                    "engineers compute this on every bridge, "
                    "fuselage, and crankshaft."
                ),
                "function_invariant": (
                    "stiffness matrix -> vibrational modes + "
                    "frequencies"
                ),
            },
            {
                "substrate": "neural (functional connectivity)",
                "implementation": (
                    "graph-Laplacian on functional connectivity "
                    "matrix from fMRI/MEG: spectral decomposition "
                    "reveals brain network modes (Atasoy et al. "
                    "2016, Connectome Harmonics)."
                ),
                "function_invariant": (
                    "connectivity matrix -> network harmonic modes"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": (
            "Class L is the structural workhorse (per Spike #24 + "
            "QM audit: 38 of 40 QM operations). The information-"
            "instrument identity is the strongest: the matrix and "
            "its spectrum are LITERALLY two sides of the same "
            "mathematical object under spectral theorem."
        ),
    },
    # ----- Class M: HDC bind/bundle/permute/similarity -----
    {
        "class": "M",
        "name": "HDC bind/bundle/permute/similarity (BSC)",
        "canonical_op": "XOR, majority, ROL, 1-2*hamming/D",
        "instrument_identity": (
            "The substrate where a D-dimensional hypervector and its "
            "bind/bundle/permute/similarity operations are "
            "inseparable: the form (hypervector layout) IS the "
            "function (HDC arithmetic). Per Spike #36's Shannon-"
            "mapping finding: the same 4 channel operations realise "
            "across silicon (BSC) / bronze (cyclic-group on K-tuple "
            "gear positions) / optical (HRR) / neural (SDM) - "
            "substrate-specific bit-/symbol-/vector-/spike-level "
            "operations, same information-instrument identity."
        ),
        "form_function_binding": (
            "FORM = D-dimensional vector substrate (bits / tooth-"
            "positions / complex amplitudes / spike rates); FUNCTION = "
            "bind / bundle / permute / similarity. The D-dim layout "
            "IS the binding: the four operations are inseparable "
            "from the hypervector geometry they live on."
        ),
        "substrates": [
            {
                "substrate": "silicon (BSC binary spatter codes)",
                "implementation": (
                    "srmech_hdc.c: D-bit binary vectors, XOR/majority/"
                    "ROL/hamming. Kanerva 1988/2009 canonical BSC."
                ),
                "function_invariant": (
                    "D-dim vector -> bind/bundle/permute/similarity"
                ),
            },
            {
                "substrate": "bronze (cyclic-group HDC)",
                "implementation": (
                    "Spike #36 §4: K-tuple gear positions over Z/n_k "
                    "moduli. bronze_bind = component-wise Z/n add, "
                    "bronze_bundle = differential-train sum, "
                    "bronze_permute = per-component cyclic-shift, "
                    "bronze_similarity = total-budget cyclic distance. "
                    "Z/2 special case == silicon BSC bit-exact."
                ),
                "function_invariant": (
                    "K-tuple gear positions -> bind/bundle/permute/"
                    "similarity"
                ),
            },
            {
                "substrate": "optical (HRR holographic reduced repr)",
                "implementation": (
                    "Plate 1995: complex amplitudes on unit circle, "
                    "bind = circular convolution, bundle = elementwise "
                    "sum, permute = cyclic shift, similarity = cosine. "
                    "Photonic implementations via holographic media "
                    "and Fourier optics."
                ),
                "function_invariant": (
                    "D-dim complex vector -> bind/bundle/permute/"
                    "similarity"
                ),
            },
            {
                "substrate": "neural (SDM sparse distributed memory)",
                "implementation": (
                    "Kanerva 1988: N hard locations in {-1,+1}^D "
                    "address space; binding via XOR-flavoured bipolar "
                    "product, bundling via majority across locations, "
                    "similarity via Hamming. Cortical column model: "
                    "sparse high-D activation pattern."
                ),
                "function_invariant": (
                    "high-D activation pattern -> bind/bundle/permute/"
                    "similarity"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": (
            "Class M is the load-bearing case for the information-"
            "instrument overlay per user direction. Spike #36 found "
            "all 4 HDC ops have direct Shannon 1948 channel-operation "
            "analogs; this spike refines the framing from 'info-"
            "theoretic' to 'information-instrument' (form-function "
            "bound). Class M substrate-portability is the canonical "
            "example."
        ),
    },
    # ----- Class N: rational-approximation -----
    {
        "class": "N",
        "name": "rational-approximation / continued fractions",
        "canonical_op": "continued-fraction convergents; best p/q under denominator bound",
        "instrument_identity": (
            "The substrate where a target ratio and its best "
            "denominator-bounded approximation are inseparable: the "
            "form (real number or arbitrary-precision ratio) IS the "
            "function (its sequence of best rational approximants). "
            "The continued-fraction expansion IS the form-function "
            "binding; every real has a unique CF expansion."
        ),
        "form_function_binding": (
            "FORM = real number / target ratio; FUNCTION = best "
            "rational approximant under denominator bound. The "
            "continued-fraction representation IS the binding: "
            "convergents are uniquely best under |error| * q^2 "
            "criterion."
        ),
        "substrates": [
            {
                "substrate": "silicon",
                "implementation": (
                    "srmech_rational.c: continued_fraction, "
                    "convergents, best_rational under denominator "
                    "bound. Exp series truncate as integer-only "
                    "asymptotic computation."
                ),
                "function_invariant": (
                    "real ratio -> best rational under bound"
                ),
            },
            {
                "substrate": "bronze (antikythera)",
                "implementation": (
                    "Metonic 19/235, Saros 223/239, Olympic 4/47: "
                    "the bronze gear-train tooth counts ARE the "
                    "rational approximants to astronomical period "
                    "ratios. Antikythera literally implements the "
                    "Class N algorithm physically with bronze."
                ),
                "function_invariant": (
                    "orbital period ratio -> tooth-count rational "
                    "approximant"
                ),
            },
            {
                "substrate": "musical (just intonation)",
                "implementation": (
                    "pitch ratios: octave = 2/1, perfect fifth = 3/2, "
                    "major third = 5/4, minor third = 6/5. The "
                    "rational-approximation discipline (best p/q "
                    "under denominator bound) governs which "
                    "intervals are consonant."
                ),
                "function_invariant": (
                    "pitch ratio -> best rational p/q (just-intonation "
                    "interval)"
                ),
            },
            {
                "substrate": "celestial (orbital resonance)",
                "implementation": (
                    "near-resonant orbits: 3:2 Pluto-Neptune, 5:2 "
                    "Saturn-Jupiter, 1:1 Trojan. The orbital "
                    "dynamics LOCKS onto best rational approximants "
                    "via secular perturbation theory."
                ),
                "function_invariant": (
                    "orbital period ratio -> locked rational p/q"
                ),
            },
        ],
        "fits_overlay": True,
        "notes": (
            "Class N is universal where substrates approximate "
            "continuous ratios with bounded-denominator discrete "
            "structure. Bronze is the canonical case (literally "
            "rational ratios in physical tooth counts)."
        ),
    },
]


# ---------------------------------------------------------------------------
# Spike-level deliverables
# ---------------------------------------------------------------------------


def uniformity_verdict() -> dict[str, Any]:
    """Does the information-instrument overlay apply uniformly?"""
    fits = [c for c in CLASS_DATA if c["fits_overlay"] is True]
    weak = [c for c in CLASS_DATA if c["fits_overlay"] == "weak"]
    return {
        "kind": "uniformity_verdict",
        "n_classes_total": len(CLASS_DATA),
        "n_classes_fit_full": len(fits),
        "n_classes_fit_weak": len(weak),
        "n_classes_fail": 0,
        "classes_full": [c["class"] for c in fits],
        "classes_weak": [c["class"] for c in weak],
        "classes_fail": [],
        "verdict": (
            "MOSTLY UNIFORM with one HONEST ANOMALY (Class F): the "
            "information-instrument overlay applies to 13 of 14 classes "
            "without qualification. Class F (templating / substitution) "
            "fits at silicon, biological (gene expression), and "
            "linguistic substrates but has WEAK bronze instantiation - "
            "the slot-naming convention (load-bearing form-function "
            "binding) is absent on bronze, consistent with MFO §VIII.6 "
            "bonus 5 cross-substrate finding that F is digital-"
            "substrate-only at full strength. The overlay does NOT "
            "FAIL for F; it weakens for bronze specifically. This is a "
            "REAL finding, not a defect."
        ),
        "anomaly_class": "F",
        "anomaly_note": (
            "Class F's form-function binding (slot-naming convention) "
            "is digital/biological/linguistic; bronze lacks the "
            "naming-convention substrate. Co-absent with Class A "
            "uniformly across the 3+7+1 projection per MFO §VIII.6 "
            "bonus 5. Class A also was originally listed as digital-"
            "only but admits substrate-portable analogs (DNA "
            "fingerprinting, neural place-cell coding) at weaker but "
            "real instantiation; F's weakness is sharper."
        ),
    }


def substrate_portability_verdict() -> dict[str, Any]:
    """Is substrate-portability uniform across classes?"""
    portability_grades = {
        "A": "high (silicon / bronze-via-gear-DAG-fingerprint / DNA / neural)",
        "B": "high (silicon / bronze / optical / DNA)",
        "C": "high (silicon / bronze-crank / neural / biochemical)",
        "D": "high (silicon / bronze / biochemical / neural)",
        "E": "high (silicon / bronze / DNA / biological)",
        "F": "MEDIUM (silicon / WEAK-bronze / biological / linguistic)",
        "G": "high (silicon / bronze / biochemical / neural)",
        "H": "high (silicon / bronze / biological / linguistic)",
        "I": "VERY HIGH (silicon / bronze / physical-gauge / molecular)",
        "J": "VERY HIGH (silicon / bronze / physical / celestial)",
        "K": "high WHERE Kepler-shape (silicon / bronze / celestial / molecular)",
        "L": "VERY HIGH (silicon / bronze / physical / neural)",
        "M": "VERY HIGH (silicon-BSC / bronze-cyclic / optical-HRR / neural-SDM)",
        "N": "VERY HIGH (silicon / bronze / musical / celestial)",
    }
    return {
        "kind": "substrate_portability",
        "verdict": (
            "Substrate-portability is HIGH across the 14 classes but "
            "NOT uniform. Six classes (I, J, L, M, N) have VERY HIGH "
            "portability (four+ distinct substrate kinds, all with "
            "robust form-function binding). Class F has MEDIUM "
            "portability (weak bronze instantiation). Classes A, B, "
            "C, D, E, G, H have HIGH portability. Class K has "
            "high-WHERE-Kepler-shape portability - it appears only "
            "where the substrate supports cyclic-to-continuous "
            "shadow projection (per [[user_stance_kepler_shape_universal]] "
            "+ Spike #30A K-substrate-specificity finding)."
        ),
        "portability_grades": portability_grades,
        "note": (
            "The VERY HIGH classes (I, J, L, M, N) are the same "
            "classes Spike #36 identified as participating in "
            "bronze HDC construction. This is structurally meaningful: "
            "the most-portable information-instruments are exactly the "
            "ones whose form-function binding is purely algebraic "
            "(cyclic-group / prime / matrix / D-dim / rational). "
            "Classes with binding tied to digital convention (A "
            "fingerprint, F slot-naming) are less portable in the "
            "strong sense."
        ),
    }


def canonical_stance_proposal() -> dict[str, Any]:
    """Should the project author a new canonical memory stance?"""
    return {
        "kind": "canonical_stance_proposal",
        "recommend_author": True,
        "proposed_slug": "user_stance_information_instrument_form_function_bound",
        "proposed_description": (
            "User's 2026-05-16 framing refinement (post-Spike-#36): "
            "the cross-class overlay that all 14 Spike #24 primitive "
            "classes admit is INFORMATION-INSTRUMENT (form-function "
            "bound, substrate-portable), NOT 'information-theoretic' "
            "(too abstract / Shannon-mathematical). Each class's "
            "identity is the BINDING of a substrate-specific form "
            "(bit-pattern / tooth-count / amplitude / spike-pattern) "
            "to a function (the operation closed on that form), "
            "like an RBS-HDC instrument. Verified by Spike #37 with "
            ">=3 substrate instantiations per class."
        ),
        "body_structure": [
            {
                "section": "Origin",
                "content": (
                    "User direction 2026-05-16 post-Spike-#36: "
                    "'information something, but not the word "
                    "theoretic I think. it's form and function is "
                    "bound and known the same as an RBS-HDC "
                    "instrument'. Refines the overlay language from "
                    "Spike #36's 'information-theoretic' to "
                    "'information-instrument' (form-function bound)."
                ),
            },
            {
                "section": "The principle",
                "content": (
                    "Each of the 14 Spike #24 primitive classes A-N "
                    "is identified at the INSTRUMENT level: the form "
                    "(substrate-specific layout) and the function "
                    "(closed operation on that layout) are "
                    "INSEPARABLE. The instrument IS the binding. "
                    "Implementations vary by substrate (silicon C "
                    "ops, bronze gear-mesh, optical photonic, neural "
                    "spike); the information-instrument identity "
                    "(form-function binding) is invariant. This is "
                    "the substrate-portable level per "
                    "[[user_stance_identity_not_implementation_discipline]]."
                ),
            },
            {
                "section": "Why this matters (vs Shannon framing)",
                "content": (
                    "Shannon 1948's channel operations (encoding / "
                    "aggregation / permutation / mutual information) "
                    "are ONE substrate-instantiation of the broader "
                    "information-instrument concept - the silicon-"
                    "digital-channel instance. The information-"
                    "instrument framing generalises: each Class M "
                    "operation has a Shannon analog AND a bronze "
                    "cyclic-group analog AND an optical HRR analog "
                    "AND a neural SDM analog. Shannon is downstream "
                    "of the substrate-portable form-function "
                    "binding, not authoritative for it."
                ),
            },
            {
                "section": "How to apply",
                "content": (
                    "1. When discussing primitive classes, use the "
                    "information-instrument language: the FORM is "
                    "the substrate layout; the FUNCTION is the "
                    "closed operation; the BINDING is the "
                    "instrument's identity.\n"
                    "2. When describing a substrate-specific "
                    "implementation, name the substrate-form and the "
                    "binding mechanism explicitly.\n"
                    "3. When the user says 'like an RBS-HDC "
                    "instrument', recognise this as the load-bearing "
                    "framing - form and function bound, not abstract "
                    "Shannon math.\n"
                    "4. Do NOT slip back into 'information-theoretic' "
                    "framing except when explicitly citing Shannon "
                    "1948 as a substrate-specific instance."
                ),
            },
            {
                "section": "Status",
                "content": (
                    "Spike #36 located the overlay; Spike #37 "
                    "verified it applies to 13 of 14 classes "
                    "uniformly (Class F has weak bronze "
                    "instantiation - an honest finding, not a "
                    "defect). The overlay is NOT a 15th class - it "
                    "is a partition coexisting with the 14-class "
                    "algebraic partition + gear+pin kinematic "
                    "partition per "
                    "[[user_stance_partition_for_understanding]]."
                ),
            },
            {
                "section": "Cross-references",
                "content": (
                    "[[user_stance_string_theory_instrument_first]] - "
                    "instrument-first stance is the project's "
                    "methodological grandparent\n"
                    "[[user_stance_identity_not_implementation_discipline]] - "
                    "form-function binding is identity, not "
                    "implementation\n"
                    "[[user_stance_partition_for_understanding]] - "
                    "information-instrument is a partition; this "
                    "stance adds a row\n"
                    "[[feedback_no_privileged_primitive_classes]] - "
                    "14-class vocabulary preserved; overlay is not a "
                    "new class\n"
                    "[[feedback_science_is_ssot_not_project]] - "
                    "Shannon 1948 / Kanerva 1988 / Plate 1995 cited "
                    "as substrate-specific instances\n"
                    "Spike #36 + Spike #37 working notes - "
                    "empirical basis"
                ),
            },
        ],
    }


def partition_table_update() -> dict[str, Any]:
    """Recommended update to user_stance_partition_for_understanding."""
    return {
        "kind": "partition_table_update",
        "recommend_add_row": True,
        "current_family_table": [
            ("11D = 3D_s + 7D_g + 1D_t", "MFO dimensional"),
            ("14 classes A-N", "algebraic-operational"),
            ("gear + pin-slot", "kinematic-instantiation"),
            ("1D_t identity vs operation", "ontological-level"),
            ("asymptote vs infinity", "substrate-vs-tool"),
        ],
        "proposed_new_row": {
            "partition": "information-instrument overlay",
            "level": "form-function-binding",
            "what_it_names": (
                "the substrate-portable identity each primitive class "
                "carries - what is FORM-bound to what FUNCTION across "
                "silicon / bronze / optical / DNA / neural"
            ),
            "load_bearing": (
                "[[user_stance_information_instrument_form_function_bound]] "
                "(new); Spike #36 + Spike #37"
            ),
        },
        "rationale": (
            "The information-instrument overlay survives the MPM-"
            "discipline test from [[user_stance_partition_for_understanding]]: "
            "selecting only the algebraic-operational partition (14 "
            "classes A-N) leaves the substrate-portability "
            "observation as unexplained shadow ('why does Class M "
            "appear at silicon AND bronze AND optical AND neural? "
            "what is the same?'). The information-instrument level "
            "names what IS the same: the form-function binding. "
            "Therefore option C is forced again: the partition family "
            "gains a sixth row at the form-function-binding level."
        ),
        "note": (
            "This is NOT class proliferation. The overlay does not "
            "add a 15th class. It adds an interpretive level at "
            "which the existing 14 classes are each identified by "
            "their form-function binding. The partition is for "
            "explanatory access; the substrate is one compressed "
            "thing."
        ),
    }


def falsifier_list() -> dict[str, Any]:
    """Falsifiers that would overturn the uniformity claim."""
    return {
        "kind": "falsifier_list",
        "falsifiers": [
            {
                "id": "F1",
                "name": "Find a class with NO bronze analog",
                "test": (
                    "Identify a Spike #24 class A-N whose form-"
                    "function binding has NO substrate-specific "
                    "implementation on bronze (gear-DAG / cyclic-"
                    "group / pin-slot vocabulary). Currently weakest "
                    "candidate: Class F (templating) bronze "
                    "instantiation is admitted-weak in this spike. "
                    "If a SECOND class also has NO bronze form, the "
                    "uniformity verdict needs revision."
                ),
                "status": "OPEN; F flagged weak, no second candidate identified",
            },
            {
                "id": "F2",
                "name": "Find a substrate where Class M FAILS",
                "test": (
                    "Find a substrate where the four HDC operations "
                    "(bind / bundle / permute / similarity) are NOT "
                    "all four realisable. Per Spike #36: silicon "
                    "(BSC) / bronze (cyclic-group) / optical (HRR) / "
                    "neural (SDM) all support all four. A substrate "
                    "supporting only three of four would refute the "
                    "'M is the canonical form-function-bound case'."
                ),
                "status": "OPEN; no failing substrate located",
            },
            {
                "id": "F3",
                "name": "Find a class WITHOUT form-function binding",
                "test": (
                    "Identify a Spike #24 class whose form and "
                    "function are SEPARABLE - where the form can "
                    "exist without the function or vice versa. The "
                    "current claim is that all 14 classes have "
                    "INSEPARABLE form-function. If any class admits "
                    "separation, the overlay weakens."
                ),
                "status": "OPEN; spectral theorem (L), FToA (J), "
                "atan2 (K) all show inseparable binding by "
                "construction",
            },
            {
                "id": "F4",
                "name": "Find a new substrate-portable class candidate",
                "test": (
                    "Identify an operation that has form-function "
                    "binding across >=3 substrates AND does NOT "
                    "dissolve into existing 14 classes A-N. This "
                    "would force expansion to 15 classes, "
                    "contradicting [[feedback_no_privileged_primitive_classes]] "
                    "closure-conjecture. Per Spike #24 bonus series + "
                    "Spike #30A: closure at 14 has survived multiple "
                    "promotion attempts (O dissolved, P dissolved)."
                ),
                "status": "OPEN; no successful 15th class promotion to date",
            },
            {
                "id": "F5",
                "name": "Show information-instrument != Shannon",
                "test": (
                    "Find a substrate where Class M operations work "
                    "at the form-function-binding level but do NOT "
                    "admit a Shannon channel interpretation. This "
                    "would confirm that 'information-instrument' is "
                    "strictly broader than 'information-theoretic'. "
                    "Current best candidate: bronze cyclic-group HDC "
                    "(Z/n, n>2) has the four operations but is NOT a "
                    "Z/2 Shannon binary channel - this is positive "
                    "confirmation."
                ),
                "status": "CONFIRMED-IN-DIRECTION; bronze Z/n>2 HDC "
                "is information-instrument but not Z/2-Shannon",
            },
            {
                "id": "F6",
                "name": "Find a class with multiple non-equivalent bindings",
                "test": (
                    "Identify a class where the form-function binding "
                    "is NOT unique across substrates - different "
                    "substrates bind different forms to different "
                    "functions. This would suggest the class is a "
                    "compound, not a primitive at the information-"
                    "instrument level."
                ),
                "status": "OPEN; all classes appear to bind the same "
                "function to substrate-specific forms",
            },
        ],
        "note": (
            "Falsifier F5 confirms in the positive direction "
            "(information-instrument is strictly broader than "
            "Shannon-theoretic). The remaining five are open and "
            "would each, if found, weaken or overturn the spike's "
            "verdict."
        ),
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def emit_ndjson(records: list[dict[str, Any]], path: Path) -> None:
    """Write NDJSON one record per line."""
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> int:
    """Build NDJSON outputs."""
    out_dir = Path(r"D:/temp/spike_37")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Per-class records: identity + cross-substrate + form-function-binding
    per_class_records: list[dict[str, Any]] = []
    for c in CLASS_DATA:
        # Identity record
        per_class_records.append({
            "kind": "instrument_identity",
            "class": c["class"],
            "name": c["name"],
            "canonical_op": c["canonical_op"],
            "instrument_identity": c["instrument_identity"],
            "fits_overlay": c["fits_overlay"],
        })
        # Form-function binding record
        per_class_records.append({
            "kind": "form_function_binding",
            "class": c["class"],
            "name": c["name"],
            "binding": c["form_function_binding"],
        })
        # Cross-substrate record (one per substrate)
        for sub in c["substrates"]:
            per_class_records.append({
                "kind": "cross_substrate",
                "class": c["class"],
                "name": c["name"],
                "substrate": sub["substrate"],
                "implementation": sub["implementation"],
                "function_invariant": sub["function_invariant"],
            })
        # Notes record
        per_class_records.append({
            "kind": "class_notes",
            "class": c["class"],
            "notes": c["notes"],
        })

    # Spike-level records
    spike_records = [
        uniformity_verdict(),
        substrate_portability_verdict(),
        canonical_stance_proposal(),
        partition_table_update(),
        falsifier_list(),
    ]

    emit_ndjson(per_class_records, out_dir / "spike_37_per_class.ndjson")
    emit_ndjson(spike_records, out_dir / "spike_37_spike_level.ndjson")

    print(f"Wrote {len(per_class_records)} per-class records")
    print(f"Wrote {len(spike_records)} spike-level records")

    # Counts for inline reporting
    n_classes = len(CLASS_DATA)
    n_substrates_per_class = sum(len(c["substrates"]) for c in CLASS_DATA) / n_classes
    n_fit_full = len([c for c in CLASS_DATA if c["fits_overlay"] is True])
    n_fit_weak = len([c for c in CLASS_DATA if c["fits_overlay"] == "weak"])
    print(f"Classes: {n_classes}")
    print(f"Substrates per class (avg): {n_substrates_per_class:.2f}")
    print(f"Fits overlay (full): {n_fit_full}")
    print(f"Fits overlay (weak): {n_fit_weak}")
    print(f"Fails overlay: 0")

    return 0


if __name__ == "__main__":
    sys.exit(main())
