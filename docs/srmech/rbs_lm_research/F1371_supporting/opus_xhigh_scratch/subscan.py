import json, re, sys, io, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
root = r"C:/Users/sckir/.claude/projects/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/subagents"
pat = re.compile(r'anisotrop', re.I)
ctx = re.compile(r'resonat|respons|asymmetr|asymptot|curvature|substrate|universe', re.I)
cut = sys.argv[1] if len(sys.argv)>1 else '2026-09-07T17:38'
files = glob.glob(root+'/**/*.jsonl', recursive=True)
for fp in sorted(files):
    with open(fp,'rb') as f:
        for ln, raw in enumerate(f,1):
            s = raw.decode('utf-8','replace')
            if not pat.search(s): continue
            try: o=json.loads(s)
            except Exception: continue
            ts=o.get('timestamp','') or ''
            if ts and ts >= cut: continue
            msg=o.get('message') or {}; role=msg.get('role',o.get('type')); c=msg.get('content')
            parts=[]
            if isinstance(c,str): parts.append(('text',c))
            elif isinstance(c,list):
                for x in c:
                    if not isinstance(x,dict): continue
                    t=x.get('type')
                    if t=='text': parts.append(('text',x.get('text','')))
                    elif t=='tool_result':
                        cc=x.get('content'); 
                        if isinstance(cc,list): cc=' '.join(y.get('text','') for y in cc if isinstance(y,dict))
                        parts.append(('tool_result',str(cc)))
                    elif t=='tool_use': parts.append(('tool_use',json.dumps(x.get('input',''))))
            else: parts.append(('raw',s))
            for k,txt in parts:
                for m in pat.finditer(txt):
                    w=txt[max(0,m.start()-220):m.end()+220]
                    if not ctx.search(w): continue
                    print(f"{os.path.relpath(fp,root)} L{ln} {ts} {role}:{k} :: "+w.replace('\n',' | '))
