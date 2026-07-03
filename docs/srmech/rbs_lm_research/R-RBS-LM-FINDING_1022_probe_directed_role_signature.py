"""F1022 probe (F1019's declared next) — the DIRECTED signature of operator ROLES: word-order asymmetry
(the flux-generating precursor of the magnetic Laplacian, F1007). Directed window-1 edges prev->next;
directionality d(w) = (out-in)/(out+in). DECLARED predictions (before running):
  P1 determiners share OUT-bias sign cross-language: the/a (eng) <-> ol/wan (bis) -- they PRECEDE nouns
  P2 prepositions share OUT-bias sign: of/in (eng) <-> blong/long (bis) -- they precede their objects
  P3 the Bislama predicate marker 'i' (subject -- i -- verb) is NEAR-BALANCED (|d| < the det/prep bias)
If the SIGN structure transfers, operator ROLE substructure is readable from direction -- the piece the
undirected spectral shape (F1019) could not see. No thresholds; the table IS the result."""
import json, re
import xml.etree.ElementTree as ET
def toks(s): return [w for w in re.split(r'[^a-z0-9]+',(s or '').lower()) if w]
eng_docs=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        eng_docs.append(toks(json.loads(line)['s'])[:200])
        if len(eng_docs)>=200: break
NS='{http://efele.net/udhr}'
root=ET.parse('/home/skirklan/corpora/udhr/udhr_bis.xml').getroot()
bis_docs=[toks(' '.join(p.text or '' for p in a.iter(NS+'para'))) for a in root.iter(NS+'article')]
def directionality(docs):
    out={}; inn={}
    for d in docs:
        for a,b in zip(d,d[1:]):
            out[a]=out.get(a,0)+1; inn[b]=inn.get(b,0)+1
    def dval(w):
        o,i=out.get(w,0),inn.get(w,0)
        return (o-i)/(o+i) if o+i else 0.0, o+i
    return dval
de=directionality(eng_docs); db=directionality(bis_docs)
print("DIRECTED operator-ROLE signature (word-order asymmetry; the magnetic-flux precursor):")
print("  role          english word  d       n     | bislama word  d       n")
ROWS=[("determiner",  "the","ol"),("determiner","a","wan"),
      ("preposition", "of","blong"),("preposition","in","long"),
      ("conjunction", "and","mo"),
      ("predicate-mk", "-","i"),
      ("content(ctrl)","water","wota"),("content(ctrl)","man","man")]
for role,ew,bw in ROWS:
    if ew!='-':
        d1,n1=de(ew); print("  %-13s %-12s %+0.3f %5d  |"%(role,ew,d1,n1), end=" ")
    else:
        print("  %-13s %-12s %6s %5s  |"%(role,'-','-','-'), end=" ")
    d2,n2=db(bw); print("%-12s %+0.3f %5d"%(bw,d2,n2))
d_the,_=de('the'); d_of,_=de('of'); d_ol,_=db('ol'); d_blong,_=db('blong'); d_i,_=db('i'); d_wan,_=db('wan'); d_long,_=db('long')
p1 = d_the>0 and d_ol>0 and d_wan>0
p2 = d_of>0 and d_blong>0 and d_long>0
import math
p3 = (d_i*d_i)**0.5 < min((d_ol*d_ol)**0.5,(d_blong*d_blong)**0.5)
print("  P1 determiners share OUT-bias sign (the/a <-> ol/wan): %s"%p1)
print("  P2 prepositions share OUT-bias sign (of <-> blong/long): %s"%p2)
print("  P3 'i' (predicate marker) nearer balance than det/prep: %s"%p3)
print("=> if the SIGN structure transfers, role SUBSTRUCTURE is readable from DIRECTION -- the piece the")
print("   undirected spectral shape (F1019 null) could not see; full magnetic-mode analysis = the follow-on.")
