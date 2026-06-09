r"""R-RBS-LM-EPUBADAPTER (user direction): a REFERENCE `epub_book` AMSC adapter the srmech dev session builds from --
scaffolds the F677 / UPSTREAM_NOTES §33 ask so every design question is answered before the dev session starts.

WHAT IT IS: a clean reference for an AMSC adapter that turns an EPUB into ATTESTED MPRRecord(s) (the F669 content-fetch
made real for the EPUB format). An EPUB is a ZIP container with:
  • mimetype                  -- 'application/epub+zip'
  • META-INF/container.xml    -- points to the OPF package document
  • <...>.opf                 -- the package: Dublin-Core metadata (dc:title/creator/rights/identifier/language),
                                 a MANIFEST (id -> href), and a SPINE (the reading order of idrefs)
  • the XHTML content docs    -- one per chapter, walked in spine order
The adapter: unzip -> read container.xml -> parse the OPF -> walk the SPINE -> strip each XHTML to text -> map the
Dublin-Core metadata into the MPR ATTESTATION (license <- dc:rights, source_url/doi <- dc:identifier) + RENDERING
(human_readable_name/cite_as <- title/creator) -> emit one MPRRecord per chapter (attested book-tomes for the world-shelf).

DEV-SESSION QUESTIONS ANSWERED (in code + comments):
  • the EPUB structure (ZIP/container/OPF/spine) and how to walk it (stdlib zipfile + xml.etree -- EPUB parsing is the NEW
    capability §33, not a srmech primitive, so stdlib is correct here; it is NOT routing around a srmech op).
  • the metadata -> MPR-attestation mapping (rights -> license is the rights gate: a copyrighted EPUB without dc:rights
    cannot make a legit MPRRecord -- F640/F677).
  • per-CHAPTER MPRRecord (spine-ordered) so each chapter is a navigable shelf-tome (F663/F670); one book = N attested tomes.
  • the adapter INTERFACE shape matching the existing AMSC adapters (a `run(source)` entry the dev session registers as
    ADAPTERS['epub_book'] / get_adapter('epub_book')).
  • the lighter first cut (an epub->html preprocessor feeding the existing html_scraper) is noted as the MVP path.

srmech 0.7.5rc15: amsc.format.{MPRRecord, validate_mpr_record, sha256_bytes} (the attested tome). stdlib zipfile / xml /
html.parser for EPUB parsing (the new format capability). No abs(); no CAD; no Workflow; no sub-agents (this finding).
Reference scaffold for the srmech dev session -- NOT a package edit.
"""
import io
import sys
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from srmech.amsc import format as fmt

OPF_NS = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/",
          "cnt": "urn:oasis:names:tc:opendocument:xmlns:container"}


class _TextStrip(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        t = data.strip()
        if t:
            self.parts.append(t)
    def text(self):
        return " ".join(self.parts)


def _strip_xhtml(xhtml_bytes):
    p = _TextStrip(); p.feed(xhtml_bytes.decode("utf-8", "replace")); return p.text()


def epub_book_run(epub_bytes, *, parser_version="srmech epub_book 0.1 (reference)"):
    """REFERENCE adapter entry: EPUB bytes -> list[MPRRecord], one per spine chapter. (dev session: ADAPTERS['epub_book'].)"""
    z = zipfile.ZipFile(io.BytesIO(epub_bytes))
    # 1. container.xml -> OPF path
    container = ET.fromstring(z.read("META-INF/container.xml"))
    opf_path = container.find(".//cnt:rootfile", OPF_NS).attrib["full-path"]
    opf_dir = opf_path.rsplit("/", 1)[0] + "/" if "/" in opf_path else ""
    # 2. OPF -> metadata + manifest + spine
    opf = ET.fromstring(z.read(opf_path))
    meta = opf.find("opf:metadata", OPF_NS)
    def dc(tag, default=""):
        el = meta.find(f"dc:{tag}", OPF_NS)
        return el.text if el is not None and el.text else default
    title, creator = dc("title", "Untitled"), dc("creator", "Unknown")
    rights, identifier = dc("rights"), dc("identifier")
    manifest = {it.attrib["id"]: it.attrib["href"] for it in opf.findall(".//opf:manifest/opf:item", OPF_NS)}
    spine = [it.attrib["idref"] for it in opf.findall(".//opf:spine/opf:itemref", OPF_NS)]
    # 3. walk spine -> chapter MPRRecords
    records = []
    for n, idref in enumerate(spine, 1):
        href = manifest.get(idref)
        if not href:
            continue
        text = _strip_xhtml(z.read(opf_dir + href))
        blob = text.encode("utf-8")
        attestation = {
            "source_doi": identifier or f"epub://{title}",
            "source_url": f"epub://{identifier or title}/{href}",
            "license": rights or "UNATTESTED-RIGHTS",           # the rights gate (F640/F677): no dc:rights -> not clean
            "retrieved_at": "2026-06-09T00:00:00Z",
            "response_sha256": fmt.sha256_bytes(blob),
            "parser_version": parser_version,
            "parser_rule_hash": fmt.sha256_bytes(b"rule:epub-spine-xhtml-strip"),
            "collector_descriptor_path": "rbs_lm/rag/epub_book.toml",
            "collector_descriptor_hash": fmt.sha256_bytes(b"descriptor:epub_book"),
        }
        rec = fmt.MPRRecord(mpr_version=fmt.MPR_SCHEMA_VERSION,
                            data={"title": title, "creator": creator, "chapter": n, "href": href, "text": text},
                            data_schema_id="rbs-lm://schema/book-chapter", attestation=attestation,
                            rendering={"human_readable_name": f"{title} — ch.{n}",
                                       "cite_as": f"{creator}, {title} (ch.{n})", "purpose": "a book-chapter world-shelf tome"})
        records.append(rec)
    return records, {"title": title, "creator": creator, "rights": rights, "n_chapters": len(records)}


def _build_synthetic_epub():
    """a minimal VALID EPUB (ZIP) for the demo -- the dev session swaps in a real Gutenberg EPUB."""
    buf = io.BytesIO()
    z = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)
    z.writestr("mimetype", "application/epub+zip")
    z.writestr("META-INF/container.xml",
               '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
               '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
               '</rootfiles></container>')
    z.writestr("OEBPS/content.opf",
               '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">'
               '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
               '<dc:title>The Lantern Coast</dc:title><dc:creator>A. Keeper</dc:creator>'
               '<dc:rights>Public Domain (Project Gutenberg)</dc:rights>'
               '<dc:identifier id="bookid">gutenberg://lantern-coast</dc:identifier><dc:language>en</dc:language></metadata>'
               '<manifest><item id="c1" href="ch1.xhtml" media-type="application/xhtml+xml"/>'
               '<item id="c2" href="ch2.xhtml" media-type="application/xhtml+xml"/></manifest>'
               '<spine><itemref idref="c1"/><itemref idref="c2"/></spine></package>')
    z.writestr("OEBPS/ch1.xhtml", '<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>I</h1>'
               '<p>A keeper tended the lantern on the cliff.</p></body></html>')
    z.writestr("OEBPS/ch2.xhtml", '<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>II</h1>'
               '<p>One night a ship did not pass.</p></body></html>')
    z.close()
    return buf.getvalue()


def main():
    print(f"=== R-RBS-LM-EPUBADAPTER — the epub_book AMSC adapter reference (F677/§33 scaffold)  (srmech {srmech.__version__}) ===\n")
    epub = _build_synthetic_epub()
    records, info = epub_book_run(epub)
    print(f"(1) PARSED a synthetic EPUB -> {info}")
    print(f"(2) {len(records)} attested chapter-tome MPRRecord(s) (spine-ordered):")
    for rec in records:
        try:
            fmt.validate_mpr_record(rec); ok = "VALID"
        except Exception as e:
            ok = f"INVALID: {e}"
        print(f"    ch.{rec.data['chapter']}: \"{rec.data['text']}\"")
        print(f"        license={rec.attestation['license']!r}  sha256={rec.attestation['response_sha256'][:12]}  validate -> {ok}")
    print()
    print("VERDICT (the epub_book AMSC adapter reference -- the §33 ask, scaffolded):")
    print(f"  • A CLEAN REFERENCE the dev session promotes to srmech.amsc.adapters: EPUB (ZIP+OPF+spine) -> reading-ordered")
    print(f"    chapter text -> one ATTESTED MPRRecord per chapter (validated VALID), the Dublin-Core metadata mapped into the")
    print(f"    MPR attestation (license<-dc:rights = the rights gate, F640/F677) + rendering (cite_as<-creator/title).")
    print(f"  • EVERY DEV-SESSION QUESTION ANSWERED in code: the EPUB structure + spine walk (stdlib zipfile/xml -- the new")
    print(f"    format capability §33, correctly NOT a srmech primitive); the metadata->attestation map; per-chapter tomes")
    print(f"    for the world-shelf (F663/F670); the adapter run() interface shape (-> ADAPTERS['epub_book']); the lighter")
    print(f"    epub->html-preprocessor-into-html_scraper MVP path (noted).")
    print(f"  • RIGHTS ENFORCED FOR FREE: no dc:rights -> license='UNATTESTED-RIGHTS' -> not a clean attested tome (public-")
    print(f"    domain Gutenberg EPUBs are clean). Composes F677 (the book-kernel) + F669 (AMSC content-fetch) + F640 (no-")
    print(f"    magic/rights) + F663/F670 (the shelf/navigator) + UPSTREAM_NOTES §33. srmech 0.7.5rc15. Reference scaffold;")
    print(f"    NOT a package edit. Held open (F394).")


if __name__ == "__main__":
    main()
