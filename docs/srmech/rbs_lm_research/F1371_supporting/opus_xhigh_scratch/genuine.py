import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
path=sys.argv[1]; pat=re.compile(sys.argv[2], re.I); lo=sys.argv[3]; hi=sys.argv[4]; roles=sys.argv[5].split(',')
with open(path,'rb') as f:
    for ln, raw in enumerate(f,1):
        s=raw.decode('utf-8','replace')
        if not pat.search(s): continue
        try: o=json.loads(s)
        except Exception: continue
        ts=o.get('timestamp') or ''
        if not (lo <= ts <= hi): continue
        msg=o.get('message') or {}; role=msg.get('role'); c=msg.get('content')
        if role not in roles: continue
        texts=[]
        if isinstance(c,str): texts=[c]
        elif isinstance(c,list): texts=[x.get('text','') for x in c if isinstance(x,dict) and x.get('type')=='text']
        for t in texts:
            if role=='user' and (t.lstrip().startswith('<task-notification>') or t.startswith('This session is being continued') or t.lstrip().startswith('<')): continue
            for m in pat.finditer(t):
                print(f"L{ln} {ts} {role} :: "+t[max(0,m.start()-220):m.end()+220].replace('\n',' | '))
