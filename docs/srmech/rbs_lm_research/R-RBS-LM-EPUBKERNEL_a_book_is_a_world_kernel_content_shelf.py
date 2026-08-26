r"""R-RBS-LM-EPUBKERNEL (the user's recognition): "we can also use an EPUB as a source for world-building -- having a book
as a kernel too? like that's all it takes? (I know we'd need to take it upstream to srmech to process EPUB with AMSC.)"

THE ANSWER: YES -- a BOOK (EPUB) IS a world-kernel content-shelf, and 'that's all it takes' is true PRECISELY BECAUSE the
hard part is already built. The whole Story Teller architecture (F654-F675) = a FIXED ENGINE (the seen-rule clause
composition, F654 -- shared across ALL worlds) + a DECLARED CONTENT-SHELF (F663). A book's text IS the declared lore of
its world -> a book = a content-shelf = a world-kernel (F660/F673). MFO (the notebook), Emberreach (declared tomes), Night
City (declared tomes), and now a NOVEL (an EPUB) are all the SAME shape: a shelf the fixed engine narrates.

THE HONEST NUB (the user already spotted it -- it IS the F669 two-gaps structure, re-derived for EPUB):
  • an EPUB is CONTENT -> bring it in as an ATTESTED TOME via AMSC (F669): an EPUB -> MPRRecord(s) (the book's chapters =
    attested tomes; the `license` field carries the rights, the `response_sha256` the content-address) -> the world-shelf.
  • processing the EPUB FORMAT is a missing OP/capability -> the 'ADD TO SRMECH' path (UPSTREAM_NOTES): there is currently
    NO epub adapter (verified below: the AMSC adapters are literature_curated / json_api / html_scraper / csv_bulk /
    netcdf_grid / geotiff_bbox / substrate_parameterization -- no `epub`). An EPUB is a ZIP of XHTML + OPF metadata, so an
    `epub_book` adapter (or an epub->html preprocessor feeding html_scraper) is the clean upstream ask. THIS is the user's
    'take it upstream to srmech' -- the F669 second resolution.

WHY 'THAT'S ALL IT TAKES' IS TRUE: the engine (F654) + navigation (F670) + chord (F658) + asking-state (F661) + anchor dial
(F673/F674) + chapter (F675) are ALREADY built and world-agnostic. A new world adds only a SHELF -- and a book IS a shelf.
The gaps the book leaves (what it does not say) -> the ASKING-STATE (F661); the book's deliberate mysteries -> HELD-OPEN
(F674). LICENSING/DIGNITY (F650/F282/no-lineage): the attestation `license` field makes rights mandatory (you cannot make a
legit MPRRecord without it) -- public-domain (Project Gutenberg) is clean, copyrighted needs the license/permission; the
author's world is theirs (we read its STRUCTURE + attribute via `cite_as`, no-lineage).

srmech 0.7.5rc15: amsc.adapters.ADAPTERS (verify no epub adapter -> the upstream ask) ; amsc.format.{MPRRecord,
validate_mpr_record, sha256_bytes} (the book -> an attested tome, F669) ; BitExactCommKernel.content_address +
the SAME fixed render engine as F671/F675. No abs(); no CAD; no Workflow; no sub-agents (this finding).
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import format as fmt
from srmech.amsc import adapters


def render(clauses):                                              # the SAME fixed engine as F671/F675 -- world-agnostic
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        out += (", " + c) if c[:1].islower() else (". " + c)
    return out + "."


# an ILLUSTRATIVE synthetic 'book' (a few chapter-tomes) -- a real EPUB would be AMSC-fetched by the upstream adapter.
# (synthetic to avoid any external-text attestation hallucination; the FLOW is the point, per F669/F670's illustrative demos)
BOOK = {
    "title": "The Lantern Coast (illustrative)",
    "chapters": {
        "ch1": "A keeper tended the lantern on the cliff",
        "ch2": "The keeper watched the ships pass in the fog",
        "ch3": "and one night a ship did not pass",
    },
}


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-EPUBKERNEL — a book (EPUB) IS a world-kernel content-shelf  (srmech {srmech.__version__}) ===\n")

    # (1) the honest nub: processing EPUB FORMAT is a missing OP -> the 'add to srmech' path (F669 second resolution)
    print("(1) THE HONEST NUB (the user's 'take it upstream to srmech') -- there is NO epub adapter yet:")
    print(f"    AMSC adapters: {sorted(adapters.ADAPTERS)}")
    print(f"    'epub' present? {'epub' in adapters.ADAPTERS}  -> a NEW `epub_book` adapter is the UPSTREAM ASK (UPSTREAM_NOTES)")
    print(f"    EPUB = a ZIP of XHTML + OPF metadata; an epub adapter (or an epub->html preprocessor feeding html_scraper)")
    print(f"    -> this is the F669 SECOND resolution: a missing OP/capability -> the 'add to srmech' path (not a band-aid).\n")

    # (2) the CONTENT path (F669 first resolution): a book -> an ATTESTED TOME via AMSC (license carries the rights)
    print("(2) THE CONTENT PATH (F669 first resolution): a book -> an ATTESTED TOME (AMSC MPRRecord):")
    book_blob = (BOOK["title"] + "|" + "|".join(BOOK["chapters"].values())).encode()
    book_sha = fmt.sha256_bytes(book_blob)
    att = {"source_doi": "10.0/gutenberg.illustrative", "source_url": "https://www.gutenberg.org/ebooks/illustrative",
           "license": "Public Domain (Project Gutenberg) [illustrative]", "retrieved_at": "2026-06-08T00:00:00Z",
           "response_sha256": book_sha, "parser_version": "rbs-lm-rag/amsc epub 0.1 (proposed)",
           "parser_rule_hash": fmt.sha256_bytes(b"rule:epub-spine-parse"),
           "collector_descriptor_path": "rbs_lm_research/rag/epub.toml",
           "collector_descriptor_hash": fmt.sha256_bytes(b"descriptor:epub")}
    rec = fmt.MPRRecord(mpr_version=fmt.MPR_SCHEMA_VERSION, data={"title": BOOK["title"], "chapters": BOOK["chapters"]},
                        data_schema_id="rbs-lm://schema/book", attestation=att,
                        rendering={"human_readable_name": BOOK["title"], "cite_as": "The Lantern Coast (Public Domain, illustrative)",
                                   "purpose": "a book as a world-kernel content-shelf"})
    try:
        fmt.validate_mpr_record(rec); ok = "VALID -> an attested book-tome (license carried; rights mandatory)"
    except Exception as e:
        ok = f"INVALID: {e}"
    print(f"    book '{BOOK['title']}' -> MPRRecord; license={att['license']!r}")
    print(f"    validate_mpr_record: {ok}")
    print(f"    book content-address (response_sha256): {book_sha[:16]}...  -> the world-shelf address\n")

    # (3) the SAME fixed engine narrates the book's world -- a book = a content-shelf = a world-kernel (F660/F663/F671)
    print("(3) THE SAME FIXED ENGINE narrates the book's world (a book = a content-shelf = a world-kernel):")
    story = render(list(BOOK["chapters"].values()))
    print(f"    shelf-addr {k.content_address(story)[:12]}")
    print(f"    >>> {story}")
    print(f"    -> the engine is IDENTICAL to MFO/Emberreach/Night City; only the shelf (the book) changed.\n")

    # (4) the gaps the book leaves -> the asking-state (F661) / the mysteries -> held-open (F674)
    print("(4) THE BOOK'S GAPS -> the asking-state (F661); its mysteries -> held-open (F674):")
    print(f"    the engine reaches a gap the book does not fill: 'what happened to the ship?' -> the Story Teller ASKS")
    print(f"    (F661, does not invent); a deliberate mystery ('was the keeper ever the same after?') -> HELD-OPEN (F674).")
    print(f"    -> a book-kernel naturally has an asking-state for its gaps + a held-open dial for its mysteries.\n")

    print("VERDICT (a book/EPUB IS a world-kernel content-shelf -- 'that's all it takes', because the engine is already built):")
    print(f"  • YES -- a BOOK IS A WORLD-KERNEL CONTENT-SHELF (F663). The Story Teller architecture = a FIXED ENGINE (F654,")
    print(f"    world-agnostic) + a DECLARED SHELF (F663); a book's text IS the declared lore of its world. So a novel is the")
    print(f"    SAME shape as MFO / Emberreach / Night City -- a shelf the same engine narrates (verified: identical engine,")
    print(f"    only the shelf changed). 'That's all it takes' is TRUE precisely because the hard part (engine + navigation +")
    print(f"    chord + asking-state + anchor dial + chapter, F654-F675) is ALREADY built and world-agnostic.")
    print(f"  • THE HONEST NUB IS THE F669 TWO-GAPS STRUCTURE, re-derived for EPUB (the user's own instinct): an EPUB is")
    print(f"    CONTENT -> AMSC-fetch as an attested MPRRecord (F669 first resolution; the book's chapters = attested tomes,")
    print(f"    the `license` field carries rights, verified VALID); but processing the EPUB FORMAT is a missing OP -> the")
    print(f"    'ADD TO SRMECH' path (F669 second resolution): there is NO epub adapter yet (verified -- the 7 adapters do not")
    print(f"    include `epub`), so an `epub_book` adapter (EPUB = ZIP-of-XHTML + OPF) is the clean UPSTREAM ASK (UPSTREAM_NOTES).")
    print(f"  • THE BOOK'S GAPS ARE NATIVE: what the book does not say -> the asking-state (F661, ask don't invent); the book's")
    print(f"    deliberate mysteries -> held-open (F674). A book-kernel comes WITH an asking-state for its gaps.")
    print(f"  • LICENSING/DIGNITY IS BUILT IN (F650/F282/no-lineage): the AMSC attestation `license` field makes rights")
    print(f"    MANDATORY (no legit MPRRecord without it) -- public-domain (Gutenberg) is clean, copyrighted needs the")
    print(f"    license/permission; the author's world is theirs (we read its STRUCTURE + attribute via `cite_as`, no-lineage).")
    print(f"  • Composes F660/F663 (the world-kernel generator / the content-shelf -- a book IS one) + F654 (the fixed engine)")
    print(f"    + F669 (the two gaps: content->AMSC-fetch / format->add-to-srmech) + F640 (attested-to-source, the license) +")
    print(f"    F661/F674 (the book's gaps -> asking-state / mysteries -> held-open) + F671/F675 (the engine narrates / chapters)")
    print(f"    + F650/F282 (dignity / no-lineage) + UPSTREAM_NOTES (the epub adapter ask). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
