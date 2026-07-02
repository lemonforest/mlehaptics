"""CODE-SWITCHING probe (user question): do mixed Bislama+English inputs work? Test on the ENGLISH
board, the BISLAMA board, and the MERGED bilingual board -- incl. the attested 'save' homograph
(eng->remember vs bis->recall; merged: dropped to grounding = operands decide) and cross-language
CONTENT recall ('water' vs the stored 'wota')."""
import os, siona
DESC=os.path.join(os.path.dirname(siona.__file__),'descriptors','bislama_udhr.toml')
ENG=siona.ENGLISH; BIS=siona.load_board(DESC)
MIX,conf=siona.merge_boards(ENG,BIS)
print("MERGED board '%s': %d self-verbs, %d imperatives; CONFLICTS -> grounding: %s"%(
      MIX.name, len(MIX.self_verbs), len(MIX.imperatives), conf))
MIXED=[("siona soem the working memory","self"),          # bis verb + eng content
       ("mekem the gcd blong 48 and 36","tool"),          # bis imperative + eng/bis function words
       ("wanem is the fiedler vector","define"),          # bis interrogative + eng content
       ("siona remember that wota i boela long 100 selsius","self"),  # eng verb + bis content
       ("compute the gcd blong 1071 mo 462","tool")]      # eng imperative + bis connectives
for label,board in (("ENGLISH",ENG),("BISLAMA",BIS),("MERGED",MIX)):
    s=siona.Session(board=board)
    got=[s.route(u) for u,_ in MIXED]
    ok=sum((r=='self-command')==(w=='self') and (r=='tool-call')==(w=='tool') and (r=='define')==(w=='define')
           for r,(_,w) in zip(got,MIXED))
    print("  %-8s routes mixed input %d/5: %s"%(label,ok,got))
print("MERGED session -- the full mixed dialogue:")
s=siona.Session(board=MIX)
for u in ["siona remember that wota i boela long 100 selsius",
          "mekem the gcd blong 48 and 36",
          "wanem is the fiedler vector",
          "siona soem the working memory"]:
    r,tag,out=s.turn(u); print("   '%s'\n      -> %-13s %s"%(u,tag,str(out)[:95]))
print("the 'save' HOMOGRAPH (conflict -> grounding; operands decide):")
r,tag,out=s.turn("siona save the note that chess is a game")
print("   'siona save the note that chess is a game' -> %s -> %s"%(tag,str(out)[:70]))
r,tag,out=s.turn("siona save wota")
print("   'siona save wota'                          -> %s -> %s"%(tag,str(out)[:70]))
print("cross-language CONTENT recall ('water' vs stored 'wota' -- token vecs are exact, so honest measure):")
r,tag,out=s.turn("siona luksave water")
print("   'siona luksave water' -> %s -> %s"%(tag,str(out)[:80]))
