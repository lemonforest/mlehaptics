import pypdf, re, json
r = pypdf.PdfReader("D:/GitHub/mlehaptics/docs/srmech/metric-field-and-its-primitives.pdf")
out = open("book.txt","w",encoding="utf-8")
for i,p in enumerate(r.pages):
    t = p.extract_text() or ""
    out.write(f"\n=====PAGE {i+1}=====\n"+t)
out.close()
print(len(r.pages))
