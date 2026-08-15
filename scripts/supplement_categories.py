#!/usr/bin/env python3
import json, urllib.parse, urllib.request, os, datetime as dt
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/categories.json").read_text())
CATS=json.loads((ROOT/"data/categories.json").read_text())
REPOS=ROOT/"data/repositories.json"
TOKEN=os.environ.get("GITHUB_TOKEN","")
HEADERS={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"dsh-category-coverage"}
if TOKEN: HEADERS["Authorization"]=f"Bearer {TOKEN}"

def search(q,per_page=30):
    url="https://api.github.com/search/repositories?"+urllib.parse.urlencode({"q":q,"sort":"stars","order":"desc","per_page":per_page})
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read().decode()).get("items",[])

def main():
    repo_payload=json.loads(REPOS.read_text())
    known={r["full_name"]:r for r in repo_payload.get("repositories",[])}
    meta={x["id"]:x for x in CATS["summary"]}
    today=dt.date.today().isoformat()
    added=0
    for c in CFG["categories"]:
        count=meta.get(c["id"],{}).get("count",0)
        if count >= CFG["target_projects_per_category"]:
            continue
        # Only supplement categories below target. Use a few high-signal keywords to keep API cost low.
        kws=c["keywords"][:4]
        query=f'"DeepSeek Harness" ({ " OR ".join(kws) })'
        try:
            items=search(query,30)
        except Exception as e:
            print(f"WARN supplement {c['name']}: {e}",flush=True); continue
        for item in items:
            name=item["full_name"]
            if name not in known:
                known[name]={"full_name":name,"sources":[f"coverage-search:{c['id']}"],"first_seen":today,"last_seen":today}
                added+=1
            else:
                src=set(known[name].get("sources",[])); src.add(f"coverage-search:{c['id']}")
                known[name]["sources"]=sorted(src); known[name]["last_seen"]=today
        print(f"{c['name']}: coverage={count}, supplemental candidates={len(items)}",flush=True)
    repo_payload["repositories"]=sorted(known.values(),key=lambda x:x["full_name"].lower())
    repo_payload["generated_at"]=dt.datetime.now(dt.timezone.utc).isoformat()
    REPOS.write_text(json.dumps(repo_payload,ensure_ascii=False,indent=2)+"\n")
    print(f"Coverage supplement done. New candidates: {added}",flush=True)

if __name__=="__main__":
    main()
