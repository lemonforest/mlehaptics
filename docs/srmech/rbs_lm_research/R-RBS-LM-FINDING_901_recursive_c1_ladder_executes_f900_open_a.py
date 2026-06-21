"""F901 — execute F900 Open(a): the recursive C1 ladder (byte->word->phrase->sentence) as ONE
scale-invariant compositor, with the atom/compose DUAL and a scale_signature introspection, measured +
run through the packaged RBSLMInferenceSubstrate. C1 = compose(parts) = bundle_i bind(part_i, pos_key(i)),
the SAME operator at every rung (parts at level n+1 = composed vectors of level n). srmech rc13; Klein-4;
numpy-free; no bag. Reproduces F900's D=2048 band at D=8192 and extends it through inference."""
import json, statistics as st
from srmech.amsc import hdc, format as fmt
from srmech.rbs_lm import RBSLMInferenceSubstrate, ContextSubstrate

D = 8192                                  # klein4 chance ~= 0.25 (4 sectors), any D
def fl(q): return q.as_float() if hasattr(q, "as_float") else q
def sim(a, b): return fl(hdc.klein4_similarity(a, b))
_cs = ContextSubstrate(D=D, hex_chars=16)     # reuse its odd-count bundle (the F166 pad fix)
def bundle_odd(vecs): return _cs.bundle_odd(list(vecs))

# ---- the ONE operator (C1) + the two duals, at every scale ----
def pos_key(i): return hdc.klein4_random(D, seed=0x70000000 + i)     # role/position key
def byte_atom(b): return hdc.klein4_random(D, seed=b)                # bounded 256 codebook
def compose(parts):                                                 # C1: role-filler bundle
    return bundle_odd([hdc.klein4_bind(p, pos_key(i)) for i, p in enumerate(parts)])
def atom(s):                                                        # DUAL: content-address (identity)
    return hdc.klein4_random(D, seed=int(fmt.sha256_bytes(s.encode())[:16], 16))
def chained_bind(parts):                                            # the BROKEN op (no positions/bundle)
    acc = parts[0]
    for p in parts[1:]: acc = hdc.klein4_bind(acc, p)
    return acc

# recursive C1 ladder: parts at level n+1 are the composed vectors of level n
def word_C1(w):     return compose([byte_atom(b) for b in w.encode("utf-8")])
def phrase_C1(ws):  return compose([word_C1(w) for w in ws])
def sentence_C1(ps):return compose([phrase_C1(p) for p in ps])

print("=== F901 the recursive C1 ladder — one scale-invariant operator at every rung (D=%d) ===" % D)

# (1) C1 IS SELF-SIMILAR: change ONE of n parts; similarity stays in a graceful band at EVERY scale
def band(make, base_parts, alt_parts):
    whole = make(base_parts); out = []
    for i in range(len(base_parts)):
        p = list(base_parts); p[i] = alt_parts[i % len(alt_parts)]
        out.append(sim(whole, make(p)))
    return st.mean(out)
W8 = list("computer".encode()); A8 = list("XYZ".encode())
ws5 = ["the","cat","sat","on","mat"]; wa5 = ["dog","ran","big","red","sun"]
ps3 = [["the","cat"],["sat","down"],["very","fast"]]; pa3 = [["a","dog"],["ran","up"],["so","slow"]]
b_bw = band(lambda P: compose([byte_atom(b) for b in P]), W8, A8)
b_wp = band(lambda P: compose([word_C1(w) for w in P]), ws5, wa5)
b_ps = band(lambda P: compose([phrase_C1(p) for p in P]), ps3, pa3)
print("\n(1) C1 self-similar graceful band (sim of whole vs 1-of-n-part-changed) — should be ~0.6-0.73 EVERY scale:")
print(f"    byte->word   (n=8): {b_bw:.3f}")
print(f"    word->phrase (n=5): {b_wp:.3f}")
print(f"    phrase->sentence(n=3): {b_ps:.3f}   [self-similar => scale-invariant compositor]")

# (2) the THREE operators at the word scale: C1 graded; atom-mint avalanche; chained-bind collapses
print("\n(2) word-scale operator contrast (morphology; chance ~0.25):")
print(f"    {'pair':<16}{'C1 compose':>12}{'atom-mint':>12}{'chained-bind':>14}")
for a,b in [("cat","cot"),("walk","walked"),("run","running"),("cat","dog")]:
    c  = sim(word_C1(a), word_C1(b))
    am = sim(atom(a), atom(b))
    cb = sim(chained_bind([byte_atom(x) for x in a.encode()]), chained_bind([byte_atom(x) for x in b.encode()]))
    print(f"    {a+'/'+b:<16}{c:>12.3f}{am:>12.3f}{cb:>14.3f}")

# (3) the DUAL coexists: atom = exact identity channel; compose = graded similarity channel
print("\n(3) the atom/compose DUAL (two channels riding together):")
print(f"    atom identity : atom(cat)==atom(cat) -> {sim(atom('cat'),atom('cat')):.3f} (exact) | atom(cat) vs atom(cot) -> {sim(atom('cat'),atom('cot')):.3f} (address, avalanche)")
print(f"    compose simil.: word_C1(cat) vs word_C1(cot) -> {sim(word_C1('cat'),word_C1('cot')):.3f} (graded generalization)")

# (4) scale_signature introspection: (a) the 1-part band detects the COMPOSITOR; (b) neighbor-density detects ON-MANIFOLD coherence
def sig_band(make, parts, alts):    # the operator self-similarity signature
    return band(make, parts, alts)
c1_sig  = sig_band(lambda P: compose([byte_atom(b) for b in P]), W8, A8)
cb_sig  = band(lambda P: chained_bind([byte_atom(b) for b in P]), W8, A8)
real_words = ["cat","dog","run","walk","computer","science","water","light","house","tree"]
def neighbor_density(w, vocab):     # max sim to the rung's vocabulary (on-manifold-ness)
    v = word_C1(w); return max(sim(v, word_C1(u)) for u in vocab if u != w)
coherent = [neighbor_density(w, real_words) for w in ["cats","runner","walking","lighthouse"]]   # real morphology, OOV
gibberish = [neighbor_density(w, real_words) for w in ["xqzwk","vmbgp","zzxqj","kfwpd"]]          # off-manifold
print("\n(4) scale_signature introspection:")
print(f"    (a) compositor signature: C1 band {c1_sig:.3f} (graceful) vs chained-bind {cb_sig:.3f} (collapsed) -> the signature IDs the operator")
print(f"    (b) on-manifold coherence (max-sim to real-word rung): real-morphology OOV {st.mean(coherent):.3f}  vs  gibberish {st.mean(gibberish):.3f}")
print(f"        -> coherent units sit ON the self-similar manifold (have neighbors); gibberish falls off it")

# (5) the recursive C1 ladder THROUGH the packaged RBSLMInferenceSubstrate (learn/infer runs on it)
class C1Context(ContextSubstrate):
    def __init__(self, *, D, hex_chars, sector=0):
        self._pad = hdc.klein4_random(int(D), seed=0x7FFFFFFF); super().__init__(D=D, hex_chars=hex_chars, sector=sector)
    def enc(self, tok, sector=None):      # the bottom rung of the C1 ladder = the word
        return compose([byte_atom(b) for b in tok.encode("utf-8")])
PARAMS = {"substrate":{"D":D,"token_seed_hex_chars":16},
          "inference":{"instrument":{"operating_k":2,"operating_temperature":0.0,"memory_capacity":512,"default_max_tokens":5,"learn_seed":1}}}
path = "/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson"
stream = []
with open(path) as f:
    for line in f:
        stream += json.loads(line)["s"].split()
        if len(stream) >= 400: break
stream = stream[:400]
sub = RBSLMInferenceSubstrate.from_params(PARAMS); sub.ctx = C1Context(D=D, hex_chars=16); sub.learn(stream)
print("\n(5) recursive C1 ladder through the PACKAGED RBSLMInferenceSubstrate:")
print(f"    learn({len(stream)} tok) + infer runs on the C1 word rung -> {sub.infer(stream[:2], max_tokens=4)}")
print("\n  ONE operator (C1 role-filler bundle) at byte/word/phrase/sentence; atom-mint is its identity dual;")
print("  the broken chained-bind ladder is replaced. Coherent units are scale-self-similar + on-manifold. Sparse, numpy-free.")
