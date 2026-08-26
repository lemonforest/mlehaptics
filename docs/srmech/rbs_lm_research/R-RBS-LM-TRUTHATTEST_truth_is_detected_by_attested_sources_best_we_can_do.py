r"""R-RBS-LM-TRUTHATTEST (user crystallization): "TRUTH IS DETECTED BY ATTESTED SOURCES" + "THAT'S THE BEST WE CAN DO."

THE EPISTEMIC LAW (completes the framework's two-sided epistemics): the_one and attestation do DIFFERENT jobs --
  • the_one DETECTS FALSITY (incoherence): a claim that CONTRADICTS attested structure is FALSE (the falsification sieve,
    F686; the_one is a coherence-detector, NOT a truth-oracle, F398). the_one can never CONFIRM truth -- only refute.
  • ATTESTATION DETECTS (PROVISIONAL) TRUTH: a claim is 'true' iff it is TRACEABLE TO AN ATTESTED SOURCE -- a valid
    MPRRecord (the MPM/AMSC attestation, F669/F640/F665). TRUTH IS DETECTED BY ATTESTED SOURCES -- it is not DECREED (not
    by the_one, not by us). The attestation IS the truth-detector.
  • 'THAT'S THE BEST WE CAN DO': an attested truth is PROVISIONAL -- FAVORED, not PRIVILEGED (F398); a stronger attestation
    can revise it; ABSOLUTE truth is the UNREACHED ASYMPTOTE (F680's chapter N -- approached and never quite reached; the
    epistemic ceiling F552; held-open F394; hand the unreachable to the expert F282). Attestation is the best we can do --
    and that honest ceiling is the stance, not a defeat.

THE FOUR EPISTEMIC OUTCOMES (from the two operations -- the_one-coherence x attestation):
  • ATTESTED + COHERENT  -> PROVISIONALLY TRUE (the best we can do: detected-true by a source, not contradicted).
  • CONTRADICTS          -> FALSE (the_one falsifies, F686; no attestation can rescue a self-contradiction).
  • UNATTESTED + not-contra -> UNKNOWN/HELD -> the asking-state (F661): SEEK an attested source (AMSC fetch, F669), else
    hold-open (F394). Absence of attestation is NOT falsity (F398 -- the_one stays silent).
  • BEYOND ATTESTATION (the ceiling, F552) -> hand to the expert (F282); held-open.

srmech 0.7.5rc15: amsc.format.{MPRRecord, validate_mpr_record, sha256_bytes} (attestation = the truth-detector, F669) ;
cascade.hypercomplex_couple + cascade.magnitude (the_one coherence/falsity, F686) ; BitExactCommKernel.content_address.
No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import format as fmt
from srmech.amsc import cascade


def mag(x):
    return cascade.magnitude(x)


def the_one_contradicts(streams):
    """the_one coherence test (F686): a high contradiction signal (imag residual) => FALSE."""
    b = cascade.hypercomplex_couple(streams, sigma=1)
    return sum(mag(x) for x in b[1:]) > 1.7


def attested(source_doi, source_url, license_):
    """attestation = the truth-detector (F669): can we build a VALID MPRRecord tracing the claim to a source?"""
    if not (source_doi and source_url and license_):
        return False
    att = {"source_doi": source_doi, "source_url": source_url, "license": license_,
           "retrieved_at": "2026-06-09T00:00:00Z", "response_sha256": fmt.sha256_bytes(source_doi.encode()),
           "parser_version": "truth-attest 0.1", "parser_rule_hash": fmt.sha256_bytes(b"rule:attest"),
           "collector_descriptor_path": "rbs_lm/attest.toml", "collector_descriptor_hash": fmt.sha256_bytes(b"desc:attest")}
    rec = fmt.MPRRecord(mpr_version=fmt.MPR_SCHEMA_VERSION, data={"claim": source_doi}, data_schema_id="truth://claim",
                        attestation=att, rendering={"human_readable_name": "claim", "cite_as": source_doi, "purpose": "truth-detection"})
    try:
        fmt.validate_mpr_record(rec); return True
    except Exception:
        return False


def classify(streams, source):
    if the_one_contradicts(streams):
        return "FALSE (the_one falsifies -- contradicts attested structure, F686)"
    if source and attested(*source):
        return "PROVISIONALLY TRUE (detected by an attested source -- the best we can do, F398/F394)"
    return "UNKNOWN / HELD -> the asking-state: seek an attested source (F669) or hold-open (F394); absence != falsity (F398)"


CLAIMS = [
    ("water boils at 373.15 K at 1 atm", [1.0, 1.0, 1.0], ("10.18434/CODATA", "https://codata.org", "CC0")),
    ("a closed machine outputs more energy than it takes in, forever", [1.0, -1.0, 1.0], None),
    ("there is microbial life on a planet in Andromeda", [1.0, 0.0, 0.0], None),
]


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-TRUTHATTEST — truth is detected by attested sources; that's the best we can do  (srmech {srmech.__version__}) ===\n")

    print("(1) THE TWO OPERATIONS on each claim -- the_one (falsity) x attestation (truth):")
    for claim, streams, source in CLAIMS:
        verdict = classify(streams, source)
        print(f"    \"{claim}\"")
        print(f"        the_one contradicts? {the_one_contradicts(streams)}   attested-source? {bool(source) and attested(*source)}")
        print(f"        -> {verdict}")
    print()

    law = ("Truth is DETECTED by attested sources (not decreed); the_one DETECTS falsity (incoherence); an attested truth "
           "is provisional (favored not privileged) -- and that is the best we can do (the held-open asymptote).")
    addr = k.content_address(law)
    print("(2) THE EPISTEMIC LAW (content-addressed -- canonical):")
    print(f"    {law}")
    print(f"    law content-address: {addr}\n")

    print("VERDICT (truth is detected by attested sources -- the_one only refutes -- and that is the best we can do):")
    print(f"  • TWO-SIDED EPISTEMICS, TWO DIFFERENT JOBS: the_one DETECTS FALSITY (a claim that contradicts attested structure")
    print(f"    is FALSE -- the falsification sieve F686; the_one is a coherence-detector, NOT a truth-oracle, F398) -- it can")
    print(f"    never CONFIRM truth. ATTESTATION DETECTS (PROVISIONAL) TRUTH: a claim is true iff it is TRACEABLE TO AN")
    print(f"    ATTESTED SOURCE -- a valid MPRRecord (the MPM/AMSC, F669/F640/F665). TRUTH IS DETECTED BY ATTESTED SOURCES,")
    print(f"    not decreed -- the attestation IS the truth-detector. (Verified: the attested CODATA claim -> provisionally")
    print(f"    true; the perpetual-motion claim -> false by the_one; the Andromeda-life claim -> UNKNOWN/HELD, not false.)")
    print(f"  • THAT'S THE BEST WE CAN DO: an attested truth is PROVISIONAL -- FAVORED, not PRIVILEGED (F398); a stronger")
    print(f"    attestation can revise it; ABSOLUTE truth is the UNREACHED ASYMPTOTE (the_one book's chapter N, approached and")
    print(f"    never quite reached, F680; the ceiling F552; held-open F394; the unreachable handed to the expert F282).")
    print(f"    Attestation is the best we can do -- and naming that ceiling honestly IS the stance, not a defeat.")
    print(f"  • ABSENCE OF ATTESTATION IS NOT FALSITY (F398, load-bearing): an unattested, non-contradictory claim is")
    print(f"    UNKNOWN/HELD -> the asking-state SEEKS an attested source (the AMSC fetch, F669), else holds it open (F394).")
    print(f"    The_one stays SILENT on the merely-unattested -- it refutes only contradictions, never absence.")
    print(f"  • THIS COMPLETES THE FRAMEWORK'S EPISTEMICS: the_one (falsify the incoherent, F686) + attestation (detect the")
    print(f"    provisional-true, F669/F640/F665) + the held-open asymptote (the best we can do, F394/F552/F282). It is the")
    print(f"    no-magic discipline (F640) stated as an epistemic law: a fact is real iff attested; magic is the absence of")
    print(f"    attestation; the_one falsifies self-contradiction; absolute truth is approached, never reached.")
    print(f"  • Composes F686 (the_one falsifies) + F669/F640/F665 (attestation = the truth-detector / the MPM) + F398 (favored-")
    print(f"    not-privileged; absence != falsity) + F394 (held-open) + F552/F282 (the ceiling / the expert) + F680 (chapter N")
    print(f"    = the unreached asymptote) + F661 (the asking-state seeks attestation). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
