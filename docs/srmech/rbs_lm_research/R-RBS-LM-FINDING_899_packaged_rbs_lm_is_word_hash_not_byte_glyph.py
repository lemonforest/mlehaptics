"""Decisive: (1) the packaged RBSLMInferenceSubstrate (F166) learn/infer RUNS — the RBS-LM object IS
in srmech. (2) BUT its encode is WORD-HASH, not byte/glyph: two words differing by one byte are
orthogonal (chance), whereas the byte-composed word_k4 (F865/F612, my research probes) shares
structure. So the 'LM kernel = glyph/byte LM object' the user wants is NOT what the package encodes."""
from srmech.rbs_lm import RBSLMInferenceSubstrate, ContextSubstrate, encode_word_k4
from srmech.amsc import hdc, format as fmt

D, HEX = 8192, 16
cs = ContextSubstrate(D=D, hex_chars=HEX)
def fl(q): return q.as_float() if hasattr(q, "as_float") else q

# (1) does the PACKAGED object learn + infer? (the thing we forgot)
params = {"substrate": {"D": D, "token_seed_hex_chars": HEX},
          "inference": {"instrument": {"operating_k": 2, "operating_temperature": 0.0,
                        "memory_capacity": 256, "default_max_tokens": 8, "learn_seed": 1}}}
sub = RBSLMInferenceSubstrate.from_params(params)
stream = "the cat sat on the mat the cat ran to the cat".split()
sub.learn(stream)
gen = sub.infer(["the", "cat"], max_tokens=4)
print("(1) PACKAGED RBSLMInferenceSubstrate.learn/infer RUNS")
print("    vocab:", sub.vocab)
print("    infer(['the','cat']) ->", gen)
print("    attestation keys:", list(sub.attestation().keys()))

# (2) is the packaged ENCODE byte/glyph, or word-hash?  cat vs cot share 2 of 3 bytes.
def byte_k4(b): return hdc.klein4_random(D, seed=b)
def word_k4_byteglyph(w):  # F865/F612 byte/glyph core — a word BUILT UP from its bytes
    return cs.bundle_odd([hdc.klein4_bind(byte_k4(b), cs.pos_key(i))
                          for i, b in enumerate(w.encode("utf-8"))])

pairs = [("cat","cot"), ("cat","car"), ("cat","dog"), ("walk","walked"), ("run","running")]
print("\n(2) encode comparison — similarity of near-words (D=8192; chance ~0.25 for klein4):")
print(f"    {'pair':<18}{'packaged (word-hash)':>22}{'byte/glyph (research)':>24}")
for a, b in pairs:
    sp = fl(hdc.klein4_similarity(encode_word_k4(a, D=D, sector=0, hex_chars=HEX),
                                  encode_word_k4(b, D=D, sector=0, hex_chars=HEX)))
    sg = fl(hdc.klein4_similarity(word_k4_byteglyph(a), word_k4_byteglyph(b)))
    print(f"    {a+'/'+b:<18}{sp:>22.4f}{sg:>24.4f}")
print("\n  packaged encode_word_k4 = klein4_random(seed=sha256(WHOLE WORD)) -> near-words ORTHOGONAL (~chance):")
print("  it is WORD-ATOM HASHING, NOT the byte/glyph LM object. The byte/glyph core (shared sub-word")
print("  structure, language-agnostic from UTF-8 bytes) lives ONLY in the research probes (F879+), never")
print("  graduated into the packaged RBS-LM object. THAT is the 'LM kernel = glyph/byte LM object' gap.")
