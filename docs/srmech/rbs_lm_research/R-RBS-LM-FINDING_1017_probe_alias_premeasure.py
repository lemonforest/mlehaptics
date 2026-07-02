"""PKG-2 hardening: alias/morphology PRE-MEASUREMENT (read_independent_structure_check_first).
Candidate fixes for 'cosine'->cos: (a) byte/glyph unigrams in Grounding.vec (spelling-soft, index-wide);
(b) targeted PREFIX-COVER in the name-coverage promotion (suffixation morphology, rule-based).
Measure BEFORE choosing: (A) read-independent tool-index Gram cross-talk (baseline vs byteglyph);
(B) the F1008 18-utterance eval under each; (C) the alias cases under each."""
import siona
from siona.infer import Grounding, _toks

class BGGrounding(Grounding):                      # candidate (a): byte/glyph word vectors
    def vec(self, w):
        if w not in self._vec_cache: self._vec_cache[w] = self.cs.enc(w)
        return self._vec_cache[w]

def gram(g, n=40):
    names=list(g.tools)[:n]; vs=[g._byname[m] for m in names]
    tot=cnt=0.0
    for i in range(len(vs)):
        for j in range(len(vs)):
            if i!=j: tot+=g.sim(vs[i],vs[j]); cnt+=1
    return tot/cnt

EVAL=[("hash these bytes with sha256","sha256_bytes"),("hash many messages at once with simd","sha256_batch"),
 ("compute the greatest common divisor of two integers","gcd"),("best rational approximation with a bounded denominator","best_rational"),
 ("factor this number into primes","factor"),("the magnetic laplacian of a directed graph","magnetic_laplacian"),
 ("signed laplacian with positive and negative edges","signed_laplacian"),("symmetric jacobi eigenvalues of a matrix","jacobi_eigvals"),
 ("hermitian eigendecomposition of a complex matrix","hermitian_eigendecompose"),("the fiedler vector for graph bisection","fiedler_vector"),
 ("bundle these klein-4 hypervectors by majority","klein4_bundle"),("recover a bound value from a klein-4 bundle","klein4_unbundle"),
 ("similarity between two klein-4 vectors","klein4_similarity"),("generate a random klein-4 hypervector","klein4_random"),
 ("cyclic bit rotation of a hypervector","permute"),("weighted co-occurrence graph from documents","cooccurrence_edges"),
 ("three-fold spectral eigenvector grouping","three_fold_eigvec_groups"),("polar hypervector with minus one zero and plus one","polar_random")]
ALIAS=[("compute the cosine of 1.5","cos"),("the sine of 0.5","sin"),("laplacians of this graph","dense_laplacian"),
 ("the tangent of 0.3","tan"),("exponential of 2.0","exp")]
def acc(g, cases, prefix=False):
    if prefix:                                     # candidate (b): prefix-cover promotion (monkey-layer, read-only test)
        orig=g.ground
        def ground2(u,k=5,owner=None):
            top=orig(u,k,owner)
            qt=set(_toks(u))
            def covers(t): return any(q==t or (len(t)>=3 and q.startswith(t) and len(q)-len(t)<=4) for q in qt)
            pool=[n for n in g._byname if (owner is None or g.tools[n].owner==owner)
                  and g._nm[n] and all(covers(t) for t in g._nm[n])]
            if pool:
                n0=max(pool, key=lambda n: sum(len(t) for t in g._nm[n]))
                top=[(0.0,n0)]+[(s,n) for s,n in top if n!=n0]
            return top[:k]
        G=ground2
    else: G=g.ground
    t1=t3=0
    for u,want in cases:
        names=[n.split('.')[-1] for _,n in G(u,3,owner='srmech')]
        t1+= names[0]==want; t3+= want in names
    return t1,t3,len(cases)
print("ALIAS/MORPHOLOGY PRE-MEASUREMENT:")
g0=Grounding()
print("  (A) read-independent Gram (40 tools): baseline(random-token vecs) = %.3f"%gram(g0))
b=acc(g0,EVAL); a=acc(g0,ALIAS)
print("  (B) baseline eval: %d/%d top-1, %d/%d top-3 | alias cases: %d/%d top-1"%(b[0],b[2],b[1],b[2],a[0],a[2]))
bp=acc(g0,EVAL,prefix=True); ap=acc(g0,ALIAS,prefix=True)
print("  (b) PREFIX-COVER: eval %d/%d top-1, %d/%d top-3 | alias %d/%d top-1  <- targeted, no re-encode"%(bp[0],bp[2],bp[1],bp[2],ap[0],ap[2]))
g1=BGGrounding()
print("  (A) read-independent Gram (40 tools): byteglyph vecs = %.3f  (cross-talk delta = %+0.3f)"%(gram(g1), gram(g1)-gram(g0)))
b1=acc(g1,EVAL); a1=acc(g1,ALIAS)
print("  (a) BYTEGLYPH: eval %d/%d top-1, %d/%d top-3 | alias %d/%d top-1"%(b1[0],b1[2],b1[1],b1[2],a1[0],a1[2]))
print("=> choose by measurement: keep eval accuracy, gain alias coverage, minimize read-independent cross-talk.")
