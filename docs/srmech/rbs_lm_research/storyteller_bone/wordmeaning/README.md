# `wordmeaning/` — the dictionary (word-level grounding map)

**Reference implementation:** F699 (R-RBS-LM-WORDMEANING)

**Lands in srmech:** `srmech/storyteller/wordmeaning.py` + `srmech.amsc` Wiktionary/WordNet adapter

This is the **word rung** of the three-rung grounding ladder (sibling to `wordassoc/`, the relation rung):

| layer | the map | grounds… | reference |
|---|---|---|---|
| char | the Unicode map (`unicodedata`) | what a character **is** | F698 |
| **word** | **a dictionary** (word → meaning) | what a word **means** | **F699 (here)** |
| relation | the big-wiki kernel (word → associations) | what a word is **seen with** | F690 (`wordassoc/`) |

**The shape:** each entry is an attested `MPRRecord` — `data={word, gloss, part_of_speech, attested}`, with a full
attestation block. **Meaning is DETECTED via an attested source, never DECREED** (F640/F688): glosses for the framework's
own vocabulary are class-A (our notebooks); general-English glosses are class-B from an **attested Wiktionary/WordNet dump**
— the reference does NOT fabricate English definitions. A word with no entry → the **asking-state** (F661).

**MPR note:** Wiktionary and internal notebooks have no DOI; the honest **source locator** (wiki URL / notebook anchor)
goes in `source_doi` (a URL/path-located source is still class-A/B, not class-C). See F699.

**Dev session:** load the real attested dump, write `descriptors/word_meaning.descriptor.toml`, wire `word_meaning()`
alongside `assoc()` in `storyteller.infer`'s gap-fill so a gap consults *meaning* + *associations* before it asks.
