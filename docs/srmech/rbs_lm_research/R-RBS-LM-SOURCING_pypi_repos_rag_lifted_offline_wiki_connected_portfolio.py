r"""R-RBS-LM-SOURCING (the user's content-sourcing design, 2026-06-08): "let PyPI be another definition/kernel -> a thing
aware of software packages about the Python language (which we have a kernel for); software repos will have to be scraped/
cataloged. A trade-off: use RAG-based knowledge learning AND for kernel-building -- lifting what RAG can do for RBS-LM vs
gen1 LLM. But offline knowledge is paramount too -- so we still need big wiki. ALSO: all our spectral-research notebooks
are connected; MFO + srmech are active."

THE CONTENT-SOURCING LAYER (extends the F665 precedence ladder with new sources + an AVAILABILITY axis):
  • SOURCE TIERS (by attestation strength, F640/F665):
      - MFO + srmech notebooks -- ACTIVE primary SSoT (class-A: attested through OUR math, F663).
      - the whole CONNECTED PORTFOLIO of spectral notebooks (chess/othello/logo/doom/antikythera/ephemerides/unsolved-
        maths) -- class-A-ish (same MPM discipline, framework-math-attested), CONNECTED (available, not the active primary).
        The whole-corpus-is-the-proof: the arcs converge.
      - DOI -- class-B-primary (literature, MPM; RAG-fetched online).
      - PyPI / software repos -- a content-kernel about software packages (the Python language-kernel's content); class-B-
        primary-ish; scraped/cataloged or RAG-fetched.
      - encyclopedia kernel / big OFFLINE wiki -- class-B-tertiary (F630); OFFLINE-paramount.
      - residue -- class-C -> the asking-state (F661).
  • A SECOND AXIS -- AVAILABILITY: online-RAG-fetch (fresh, strongest-attested) vs offline-cached (available without a
    network). RAG needs online; OFFLINE operation needs the local cached shelf -> the big offline wiki stays essential.
  • RAG, LIFTED (the user's point -- RAG-for-RBS-LM vs gen1): in a gen1 LLM, RAG is a retrieval BAND-AID stapled onto a
    flock that still hallucinates around the retrieval. In RBS-LM, RAG IS the native attestation-FETCH -- the FETCH-ARM of
    the asking-state (F661): the kernel lacks a tome -> RAG fetches it (DOI/PyPI/repos) -> the precedence ladder ranks it
    (F665) -> the adaptive tier integrates it as a tome (a note in the chord, F658, GPU-free F628). The RBS-LM CANNOT
    hallucinate the fetched content (it composes over the attested tome), so RAG-lifted is a kernel-BUILDER (it grows the
    chord with attested tomes), NOT a band-aid. (This is the F650 LIFTING applied to RAG.)

THE ISSUE-CLOSEOUT DISCIPLINE (standing, CL-1 + the user's direction): when a research GH issue is RESOLVED by landing in
a notebook -> CLOSE it (with a backlink: 'resolved by §X / FXXX, landed-where'); if NOT-ready -> UPDATE it (link the
notebook update) but DO NOT close. (Distinct from UPSTREAM srmech issues, which stay per [[feedback_create_upstream_issues
_never_close_them]] -- author-ambiguity.) Applied this turn: the F667 sweep ADVANCES the RBS-LM / notebook-native-language
tracking issues (#844, #855) but does NOT resolve them -> UPDATE (link the sweep), don't close; the rest -> the CL-1
closeout audit.

srmech 0.7.5rc15: amsc.format.sha256_bytes (each source tier content-addressed; the resolve-by-strength-then-availability
lookup). No abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt

# the content-source ladder: (tier, attestation-class, availability)
SOURCES = [
    ("MFO+srmech notebooks (ACTIVE)", "A (our math)",   "offline"),
    ("connected portfolio notebooks", "A-ish (our math)","offline"),
    ("DOI (primary literature)",      "B-primary",       "online (RAG)"),
    ("PyPI / software repos",         "B-primary-ish",   "online (RAG/catalog)"),
    ("encyclopedia kernel / wiki",    "B-tertiary",      "OFFLINE (paramount)"),
]


def main():
    print(f"=== R-RBS-LM-SOURCING — PyPI/repos + RAG-lifted + offline-wiki + the connected portfolio  (srmech {srmech.__version__}) ===\n")

    print("(1) THE CONTENT-SOURCE LADDER (attestation strength x availability; extends F665):")
    print(f"    {'source':<33} {'attestation':<16} {'availability'}")
    for src, cls, avail in SOURCES:
        addr = fmt.sha256_bytes(f"src:{src}".encode())[:8]
        print(f"    {src:<33} {cls:<16} {avail:<16} [{addr}]")
    print(f"    + residue -> class C -> the asking-state (F661)\n")

    print("(2) RAG, LIFTED (RAG-for-RBS-LM vs gen1 -- the user's point):")
    print(f"    gen1 LLM : RAG = a retrieval BAND-AID on a flock that still hallucinates AROUND the retrieval.")
    print(f"    RBS-LM   : RAG = the native attestation-FETCH = the FETCH-ARM of the asking-state (F661):")
    print(f"               lack a tome -> RAG fetch (DOI/PyPI/repos) -> rank by precedence (F665) -> integrate as a tome")
    print(f"               (a note in the chord, F658; GPU-free, F628). It CANNOT hallucinate the fetched content -> RAG")
    print(f"               is a kernel-BUILDER (grows the chord with attested tomes), not a band-aid. (F650 lifting, on RAG.)\n")

    print("(3) OFFLINE-PARAMOUNT + the connected portfolio:")
    print(f"    RAG needs ONLINE; OFFLINE operation needs the local cached shelf -> the big offline WIKI stays essential")
    print(f"    (F630). Two fetch-modes: online-RAG (fresh, strongest-attested) + offline-cached (available). And the WHOLE")
    print(f"    PORTFOLIO of spectral notebooks is CONNECTED (chess/othello/logo/doom/antikythera/ephemerides/unsolved-maths")
    print(f"    -- same MPM, framework-math-attested); MFO + srmech are the ACTIVE primary. The shelf draws from the whole")
    print(f"    connected portfolio (the whole-corpus-is-the-proof; the arcs converge).\n")

    print("(4) THE ISSUE-CLOSEOUT DISCIPLINE (standing -- CL-1 + the user's direction):")
    print(f"    research GH issue RESOLVED by landing in a notebook -> CLOSE it (backlink: 'resolved by §X/FXXX, landed-")
    print(f"    where'); NOT-ready -> UPDATE it (link the notebook update) but DO NOT close. (Upstream srmech issues stay")
    print(f"    per [[feedback_create_upstream_issues_never_close_them]].) Applied: the F667 sweep ADVANCES #844/#855")
    print(f"    (RBS-LM / notebook-native-language tracking) but does NOT resolve them -> UPDATE, don't close; rest -> CL-1.\n")

    print("VERDICT (the content-sourcing layer: many sources, RAG lifted, offline paramount, portfolio connected):")
    print(f"  • THE SHELF DRAWS FROM MANY SOURCES, ORDERED BY ATTESTATION STRENGTH x AVAILABILITY (extends F665): MFO+srmech")
    print(f"    (ACTIVE, class-A) > the connected portfolio (class-A-ish) > DOI (class-B-primary, online-RAG) ~ PyPI/repos (a")
    print(f"    software-package content-kernel, online-RAG/catalog) > the offline encyclopedia/wiki (class-B-tertiary,")
    print(f"    OFFLINE-paramount) > residue (the asking-state). PyPI/repos ARE another content-kernel (about the Python")
    print(f"    language we have a kernel for); software repos are scraped/cataloged knowledge.")
    print(f"  • RAG IS LIFTED for RBS-LM (vs gen1): not a retrieval band-aid on a hallucinating flock, but the native")
    print(f"    attestation-FETCH -- the fetch-arm of the asking-state (F661): lack a tome -> fetch -> rank (F665) ->")
    print(f"    integrate (F628) as a note in the chord (F658). The RBS-LM can't hallucinate the fetched content, so RAG")
    print(f"    BUILDS the kernel (grows the attested chord) instead of nudging a distribution. That is what RAG can do for")
    print(f"    RBS-LM that it can't for gen1.")
    print(f"  • BUT OFFLINE IS PARAMOUNT: RAG needs a network; offline operation needs the local cached shelf -> the big")
    print(f"    offline WIKI stays essential (F630). Availability is a real second axis (online-RAG-fresh vs offline-cached-")
    print(f"    available); the precedence ladder governs which tome, availability governs whether it's reachable now.")
    print(f"  • THE PORTFOLIO IS CONNECTED: all the spectral notebooks are content-kernels (same MPM, framework-math-")
    print(f"    attested); MFO + srmech are ACTIVE primary; the rest connected/available (the whole-corpus-is-the-proof).")
    print(f"  • THE ISSUE-CLOSEOUT DISCIPLINE (standing): notebook-landing resolves a research issue -> CLOSE (backlink,")
    print(f"    landed-where); not-ready -> UPDATE, don't close; upstream srmech issues stay (author-ambiguity). Applied this")
    print(f"    turn (#844/#855 updated, not closed; rest -> CL-1).")
    print(f"  • Composes F665 (the precedence ladder this extends) + F661 (RAG = the fetch-arm of the asking-state) + F628")
    print(f"    (integrate, GPU-free) + F658 (the chord) + F650 (lifting -- on RAG) + F630 (offline wiki) + F663 (MFO active)")
    print(f"    + the connected spectral-portfolio (whole-corpus convergence) + CL-1 + [[feedback_create_upstream_issues_")
    print(f"    never_close_them]] + [[feedback_public_issue_tracker_fine_transparency_by_default]]. srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
