import json, sys, urllib.parse, urllib.request
import time
for q in sys.argv[1:]:
    time.sleep(3)
    u = "https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(q)
    d = json.load(urllib.request.urlopen(u, timeout=30))
    print("Q:", q)
    for it in d["message"]["items"]:
        a = ", ".join(x.get("family", "") for x in it.get("author", [])[:4])
        y = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
        print("  ", it.get("DOI"), "|", (it.get("title") or [""])[0][:110], "|", (it.get("container-title") or [""])[0][:50], "|", a, "|", y)
