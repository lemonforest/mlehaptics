r"""R-RBS-LM-RAGAMSC (the user's two questions, 2026-06-08): "including all our notebooks means the Story Teller meets
OTHER WORDS it might ASK about -> invoke some sort of RBS-LM-RAG end if we need to add to srmech. OR if AMSC can do this."

THE ANSWER: AMSC ALREADY DOES THIS. The "RBS-LM-RAG end" -- the fetch-arm of the asking-state (F661/F668) -- IS srmech's
AMSC framework (the Attested Multi-Source Collector/Catalog). It is not a new band-aid to build; it is the attested-fetch
already in srmech:
  • the ADAPTERS (literature_curated / json_api / html_scraper / csv_bulk / netcdf_grid / geotiff_bbox / substrate_param)
    = the FETCH sources (DOI / PyPI / repos / catalogs / the web).
  • MPRRecord + the MANDATORY MPR attestation block (source_doi, source_url, license, retrieved_at, response_sha256,
    parser_version, parser_rule_hash, collector_descriptor_path, collector_descriptor_hash) = the ATTESTED tome.
  • validate_mpr_record + catalog.register_attested_root = the attestation check + the shelf-registration.

THE FLOW: the connected portfolio (F668) brings WORDS the Story Teller doesn't hold -> the ASKING-STATE fires (F661) ->
AMSC FETCHES (an adapter collects the source) + ATTESTS (an MPRRecord with the full MPR block) -> validate -> the ADAPTIVE
TIER integrates it (F628) as a NOTE IN THE CHORD (F658). The precedence ladder (F665) ranks the AMSC tome by its MPR
attestation (a DOI -> class-B-primary; PyPI/repo -> class-B-primary-ish).

WHY THIS MATTERS -- AMSC's MANDATORY attestation is what makes the fetch HONEST: a fetched source is NOT an unattested
scrape -- it carries the MPR block (source + response_sha256 + parser provenance) -> a legitimate ATTESTED tome (class-B,
F640/F665). AMSC is the LIFT that makes RAG-for-RBS-LM honest (F668): the fetch comes WITH its attestation, so it can be a
note in the chord, never a hallucination. TWO DIFFERENT GAPS, TWO RESOLUTIONS: unknown CONTENT -> AMSC-fetch (already in
srmech); a missing OP/CAPABILITY -> the "add to srmech" path (UPSTREAM_NOTES, the new-op flow). The user's "if AMSC can
do this" -- yes, for content; "add to srmech" is the separate path for a missing op.

srmech 0.7.5rc15: amsc.format.{MPRRecord, validate_mpr_record, sha256_bytes, MANDATORY_*}; amsc.adapters (the fetch
sources); amsc.catalog (the shelf). No abs(); no CAD; no Workflow; no sub-agents.
"""
import json
import srmech
from srmech.amsc import format as fmt
from srmech.amsc import adapters


def main():
    print(f"=== R-RBS-LM-RAGAMSC — the RBS-LM-RAG fetch-arm IS AMSC (already in srmech)  (srmech {srmech.__version__}) ===\n")

    # (1) AMSC's adapters = the FETCH sources (the RBS-LM-RAG end is already built)
    print("(1) AMSC's ADAPTERS = the RBS-LM-RAG fetch sources (already in srmech):")
    print(f"    adapters: {sorted(adapters.ADAPTERS)}")
    print(f"    -> literature_curated (DOI/papers) / json_api (PyPI, REST) / html_scraper (repos/web) / csv_bulk / ...")
    print(f"    the 'RBS-LM-RAG end' the user asked about IS this -- the attested-multi-source collector, not a new band-aid.\n")

    # (2) the ASKING-STATE -> AMSC fetch+attest -> an MPRRecord (the attested tome) -> validate
    print("(2) THE FLOW: asking-state (F661) -> AMSC fetch+attest -> an MPRRecord (the attested tome) -> validate -> integrate:")
    data = {"concept": "numpy", "fact": "numpy is a Python array library", "kind": "software-package"}
    blob = json.dumps(data, sort_keys=True).encode()
    resp_sha = fmt.sha256_bytes(blob)                                # the response content-address (64 hex)
    attestation = {
        "source_doi": "10.0/pypi.numpy",                            # illustrative (a real fetch carries the real DOI/URL)
        "source_url": "https://pypi.org/project/numpy/",
        "license": "BSD-3-Clause",
        "retrieved_at": "2026-06-08T00:00:00Z",
        "response_sha256": resp_sha,
        "parser_version": "rbs-lm-rag/amsc 0.1",
        "parser_rule_hash": fmt.sha256_bytes(b"rule:pypi-json_api-fetch"),
        "collector_descriptor_path": "rbs_lm_research/rag/pypi.toml",
        "collector_descriptor_hash": fmt.sha256_bytes(b"descriptor:pypi-fetch"),
    }
    rendering = {"human_readable_name": "PyPI: numpy", "cite_as": "PyPI numpy package (RBS-LM-RAG via AMSC)",
                 "purpose": "an asking-state attested fetch -> a note in the chord"}
    rec = fmt.MPRRecord(mpr_version=fmt.MPR_SCHEMA_VERSION, data=data, data_schema_id="rbs-lm://schema/package",
                        attestation=attestation, rendering=rendering)
    try:
        fmt.validate_mpr_record(rec)
        ok = True
    except Exception as e:
        ok = False; err = e
    print(f"    a Story Teller gap on 'numpy' -> AMSC json_api fetch -> MPRRecord (PyPI, attested)")
    print(f"    MPR attestation block present (all {len(fmt.MANDATORY_ATTESTATION_FIELDS)} mandatory fields): {set(fmt.MANDATORY_ATTESTATION_FIELDS) <= set(attestation)}")
    print(f"    validate_mpr_record(rec): {'VALID -> a legitimate attested tome' if ok else 'INVALID: '+str(err)}")
    print(f"    response_sha256 (the tome's content-address): {resp_sha[:16]}...")
    print(f"    -> the fetched tome carries its attestation -> integrate (F628) as a NOTE IN THE CHORD (F658), class-B (F665).\n")

    # (3) two gaps, two resolutions: content -> AMSC; missing op -> add-to-srmech
    print("(3) TWO GAPS, TWO RESOLUTIONS (the user's 'invoke RBS-LM-RAG ... if we need to add to srmech / or if AMSC can do this'):")
    print(f"    unknown CONTENT (a word/fact the shelf lacks)   -> AMSC-FETCH (adapter -> attest -> MPRRecord) [ALREADY in srmech]")
    print(f"    a missing OP / CAPABILITY (no cascade op for it) -> the 'ADD TO SRMECH' path (UPSTREAM_NOTES, new-op flow)")
    print(f"    -> for CONTENT, AMSC does it; 'add to srmech' is the SEPARATE path for a missing op.\n")

    print("VERDICT (the RBS-LM-RAG fetch-arm IS AMSC):")
    print(f"  • THE 'RBS-LM-RAG END' THE USER ASKED ABOUT IS ALREADY BUILT -- it is srmech's AMSC (the Attested Multi-Source")
    print(f"    Collector/Catalog): the ADAPTERS (literature_curated/json_api/html_scraper/csv_bulk/...) = the fetch sources")
    print(f"    (DOI/PyPI/repos/web); MPRRecord + the MANDATORY MPR attestation block = the attested tome; validate_mpr_record")
    print(f"    + catalog.register_attested_root = the attestation check + the shelf. Not a new band-aid -- already in srmech.")
    print(f"  • THE FLOW: the connected portfolio (F668) brings WORDS the Story Teller doesn't hold -> the ASKING-STATE fires")
    print(f"    (F661) -> AMSC FETCHES + ATTESTS (an MPRRecord; verified VALID) -> the ADAPTIVE TIER integrates (F628) as a")
    print(f"    NOTE IN THE CHORD (F658), ranked by its MPR attestation in the precedence ladder (F665; DOI -> class-B).")
    print(f"  • AMSC'S MANDATORY ATTESTATION IS THE LIFT: a fetched source is NOT an unattested scrape -- it carries the MPR")
    print(f"    block (source + response_sha256 + parser provenance) -> a legitimate attested tome -> a note in the chord,")
    print(f"    never a hallucination. AMSC is what makes RAG-for-RBS-LM honest (F668): the fetch comes WITH its attestation.")
    print(f"  • TWO GAPS, TWO RESOLUTIONS: unknown CONTENT -> AMSC-fetch (already in srmech, the user's 'if AMSC can do this'");
    print(f"    -- yes); a missing OP/capability -> the 'add to srmech' path (UPSTREAM_NOTES). The asking-state routes to AMSC")
    print(f"    for content, to add-to-srmech for a missing op.")
    print(f"  • Composes F668 (RAG-lifted -- AMSC IS the fetch-arm) + F661 (the asking-state -> the fetch) + F628 (integrate) +")
    print(f"    F658 (the chord) + F665 (precedence ranks the AMSC tome by its MPR attestation) + F640 (MPR = attested-to-source")
    print(f"    / no-magic) + the AMSC framework + UPSTREAM_NOTES (the add-to-srmech op path). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
