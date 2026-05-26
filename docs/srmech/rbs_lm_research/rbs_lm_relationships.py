"""R-RBS-LM-47 — Pure-Python relationship extractor for cross-substrate input-form tests.

Per user direction 2026-05-26: *"what if we can send relationships to the
LLM instead of all the text tokens? ... this would also be a layer of
depersonalizing all LLM but only on the wire/in flight because inference
will know it."*

Converts natural text into depersonalized S-V-O triples for the
relationship-form cascade-distill test (47b) and LLM-input-format test
(47a). No external NLP deps — uses curated verb patterns + regex NER
heuristics. Lossy but honest first test of the substrate-form hypothesis.

Per R-RBS-LM-43 two-substrate framework: relationships ARE the M1-native
form (discrete-cyclic-algebra); proper-noun naming layer is the
M2-instantiation cost. This module strips the M2 cost; a local entity_map
allows re-personalization at endpoint.

Usage:
    from rbs_lm_relationships import extract_relationships, serialize_triples

    triples, entity_map = extract_relationships(text, depersonalize=True)
    rel_corpus = serialize_triples(triples)
    # entity_map: OrderedDict[original_name -> token]
    # rel_corpus contains no PII; entity_map is kept locally to re-personalize
"""

import re
from collections import OrderedDict


# Curated common-English verb forms (regular + irregular conjugations).
# Used to anchor S-V-O parsing. Not exhaustive — lossy by design.
COMMON_VERBS = set("""
is are was were be been being am
have has had having
do does did doing done
say said says saying
tell told telling tells
get got gotten getting gets
make made making makes
go went gone going goes
know knew known knowing knows
think thought thinking thinks
take took taken taking takes
see saw seen seeing sees
come came coming comes
give gave given giving gives
find found finding finds
work worked working works
call called calling calls
try tried trying tries
ask asked asking asks
need needed needing needs
feel felt feeling feels
become became becoming becomes
leave left leaving leaves
put putting puts
mean meant meaning means
keep kept keeping keeps
let letting lets
begin began begun beginning begins
seem seemed seeming seems
help helped helping helps
talk talked talking talks
turn turned turning turns
start started starting starts
show showed shown showing shows
hear heard hearing hears
play played playing plays
run ran running runs
move moved moving moves
like liked liking likes
live lived living lives
believe believed believing believes
hold held holding holds
bring brought bringing brings
happen happened happening happens
write wrote written writing writes
provide provided providing provides
sit sat sitting sits
stand stood standing stands
lose lost losing loses
pay paid paying pays
meet met meeting meets
include included including includes
continue continued continuing continues
set setting sets
learn learned learning learns
change changed changing changes
lead led leading leads
understand understood understanding understands
watch watched watching watches
follow followed following follows
stop stopped stopping stops
create created creating creates
speak spoke spoken speaking speaks
read reading reads
allow allowed allowing allows
add added adding adds
spend spent spending spends
grow grew grown growing grows
open opened opening opens
walk walked walking walks
win won winning wins
offer offered offering offers
remember remembered remembering remembers
love loved loving loves
consider considered considering considers
appear appeared appearing appears
buy bought buying buys
wait waited waiting waits
serve served serving serves
die died dying dies
send sent sending sends
expect expected expecting expects
build built building builds
stay stayed staying stays
fall fell fallen falling falls
cut cutting cuts
reach reached reaching reaches
remain remained remaining remains
suggest suggested suggesting suggests
raise raised raising raises
pass passed passing passes
sell sold selling sells
require required requiring requires
report reported reporting reports
decide decided deciding decides
pull pulled pulling pulls
return returned returning returns
explain explained explaining explains
hope hoped hoping hopes
develop developed developing develops
carry carried carrying carries
break broke broken breaking breaks
receive received receiving receives
agree agreed agreeing agrees
support supported supporting supports
hit hitting hits
produce produced producing produces
eat ate eaten eating eats
cover covered covering covers
catch caught catching catches
draw drew drawn drawing draws
choose chose chosen choosing chooses
convert converted converting converts
study studied studying studies
study studies studied
process processed processing processes
contain contains contained containing
manage managed managing manages
generate generated generating generates
test tested testing tests
enable enabled enabling enables
implement implemented implementing implements
analyze analyzed analyzing analyzes
compute computed computing computes
encode encoded encoding encodes
decode decoded decoding decodes
""".split())


# Type hints for entity classification via lexical patterns.
NER_HINTS = {
    "ORG":   ["inc", "corp", "company", "group", "foundation",
              "society", "institute", "university", "school",
              "department", "ministry", "agency", "office"],
    "PLACE": ["street", "city", "state", "country", "park",
              "river", "ocean", "sea", "mountain", "island",
              "valley", "forest", "town", "village", "highway", "road"],
    "TIME":  ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december",
              "monday", "tuesday", "wednesday", "thursday", "friday",
              "saturday", "sunday"],
}


def split_sentences(text):
    """Heuristic sentence split on .!? followed by whitespace."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def classify_entity(name):
    """Heuristic NER. Returns one of {PERSON, ORG, PLACE, TIME}."""
    lower = name.lower()
    for kind, hints in NER_HINTS.items():
        for h in hints:
            if h in lower.split() or lower.endswith(" " + h) or lower == h:
                return kind
    return "PERSON"  # default for capitalized proper nouns


def depersonalize_text(text, entity_map, counters):
    """Replace capitalized phrases (other than sentence-initial) with type tokens.

    Args:
        text: input sentence
        entity_map: OrderedDict[original_name -> depersonalized_token]
                    (mutated in-place; preserves order of first appearance)
        counters: dict {kind -> int} — incremented per new entity per kind

    Returns: text with capitalized proper-noun phrases replaced.
    """
    parts = text.split(" ", 1)
    if len(parts) < 2:
        return text
    first = parts[0]
    rest = parts[1]

    def replace(m):
        name = m.group(0)
        if name not in entity_map:
            kind = classify_entity(name)
            counters[kind] += 1
            entity_map[name] = f"{kind}_{counters[kind]}"
        return entity_map[name]

    rest_dp = re.sub(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b', replace, rest)
    return first + " " + rest_dp


def parse_sentence(sent, entity_map, counters, depersonalize=True):
    """Extract a single S-V-O triple from a sentence (or fallback to assertion).

    Returns: list of (subj, verb, obj) tuples — possibly empty.
    """
    if depersonalize:
        sent = depersonalize_text(sent, entity_map, counters)

    words = sent.split()
    if len(words) < 3:
        return []

    # Find first known verb (skip position 0; first word is usually subject)
    first_verb = None
    for i in range(1, len(words)):
        w_clean = re.sub(r'[^a-zA-Z]', '', words[i]).lower()
        if w_clean in COMMON_VERBS:
            first_verb = i
            break

    if first_verb is None:
        # No recognizable verb; emit as bare assertion (no SVO structure)
        sent_clean = re.sub(r'[.,;:!?\'"]$', '', sent).lower()
        return [("", "_assert_", sent_clean.strip())]

    if first_verb >= len(words) - 1:
        # Verb at end; no object
        return []

    subj = " ".join(words[:first_verb]).strip()
    verb = re.sub(r'[.,;:!?\'"]', '', words[first_verb]).lower()
    obj = " ".join(words[first_verb + 1:]).strip()
    obj = re.sub(r'[.,;:!?]$', '', obj).strip()

    return [(subj.lower(), verb, obj.lower())]


def extract_relationships(text, depersonalize=True):
    """Convert raw text into list of S-V-O triples + entity map.

    Args:
        text: raw text
        depersonalize: if True, replace capitalized proper nouns with type tokens

    Returns: (triples, entity_map)
        triples: list of (subj, verb, obj) — may include ("", "_assert_", text)
                 for sentences without identifiable verbs
        entity_map: OrderedDict[original_name -> depersonalized_token]
    """
    entity_map = OrderedDict()
    counters = {"PERSON": 0, "PLACE": 0, "ORG": 0, "TIME": 0}
    triples = []

    for sent in split_sentences(text):
        triples.extend(parse_sentence(sent, entity_map, counters, depersonalize))

    return triples, entity_map


def serialize_triples(triples, sep="\n"):
    """Serialize triples one per line. Bare assertions are emitted as-is."""
    lines = []
    for s, v, o in triples:
        if v == "_assert_":
            lines.append(o.strip())
        elif s and o:
            lines.append(f"{s} {v} {o}".strip())
        elif s or o:
            lines.append(f"{s} {v} {o}".strip())
    return sep.join(lines)


def repersonalize(text, entity_map):
    """Reverse the depersonalization given the local entity map.

    Used at inference endpoint to recover PII-bearing form. The wire only
    sees depersonalized form; only the endpoint that holds the entity_map
    can re-personalize.
    """
    # Build reverse map; replace longest-token first to avoid partial overlap
    reverse = {tok: name for name, tok in entity_map.items()}
    tokens_by_len = sorted(reverse.keys(), key=len, reverse=True)
    for tok in tokens_by_len:
        text = text.replace(tok, reverse[tok])
    return text


def pii_audit(text):
    """Scan text for likely PII tokens. Returns list of suspect substrings.

    Heuristic: capitalized multi-word sequences (PERSON-name-like patterns).
    For depersonalization audit: feed the wire-form text; if this returns
    empty, no obvious PII is leaking.

    Note: this is NOT a comprehensive PII detector. It catches the common
    cases (capitalized names) but not e.g. email addresses, phone numbers,
    SSNs. Treat as a first-line check, not a guarantee.
    """
    # Match capitalized 1-3 word sequences (excluding common sentence-initial words)
    candidates = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b', text)
    # Filter sentence-initial single words
    suspects = [c for c in candidates if " " in c or len(c) > 12]
    return suspects


if __name__ == "__main__":
    # Self-test
    sample = (
        "Steven Kirkland wrote the research notebook. "
        "Algorithms for sorting have been studied for decades. "
        "Public-key cryptography enables secure communication between Alice and Bob. "
        "The chef tasted the soup. "
        "Hello, world!"
    )
    print("=== R-RBS-LM-47 relationship extractor self-test ===\n")
    print(f"Input ({len(sample)} bytes):\n  {sample!r}\n")

    triples, ent_map = extract_relationships(sample, depersonalize=True)
    print(f"Extracted {len(triples)} triples:")
    for t in triples:
        print(f"  {t}")
    print(f"\nEntity map ({len(ent_map)} entities):")
    for orig, tok in ent_map.items():
        print(f"  {orig!r:30s} -> {tok}")

    rel_corpus = serialize_triples(triples)
    print(f"\nSerialized relationship corpus ({len(rel_corpus.encode('utf-8'))} bytes):")
    print(rel_corpus)

    # PII audit on the wire form
    leaks = pii_audit(rel_corpus)
    print(f"\nPII audit on wire form: {len(leaks)} suspects")
    for s in leaks:
        print(f"  ⚠ {s}")

    # Re-personalization
    recovered = repersonalize(rel_corpus, ent_map)
    print(f"\nRepersonalized recovery:")
    print(recovered)
