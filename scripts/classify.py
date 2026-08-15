#!/usr/bin/env python3
import json, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/"config/categories.json").read_text(encoding="utf-8"))
PROJECTS = ROOT/"data/projects.json"
REPOS = ROOT/"data/repositories.json"
OUT = ROOT/"data/categories.json"

def norm(s):
    return re.sub(r"[^a-z0-9+#.-]+"," ",(s or "").lower())

def phrase_score(text, phrase):
    p = norm(phrase).strip()
    if not p: return 0
    if " " in p:
        return 4 if p in text else 0
    return 2 if re.search(rf"(?<![a-z0-9]){re.escape(p)}(?![a-z0-9])", text) else 0

def classify_type(text):
    scores={}
    for t in CFG["types"]:
        scores[t["id"]] = sum(phrase_score(text,k) for k in t["keywords"])
    best=max(scores, key=scores.get)
    return best if scores[best] > 0 else "tool"

def classify_category(project):
    text=norm(" ".join([
        project.get("full_name",""),
        project.get("description",""),
        " ".join(project.get("topics",[]))
    ]))
    scores={}
    evidence=defaultdict(list)
    for c in CFG["categories"]:
        s=0
        for kw in c["keywords"]:
            hit=phrase_score(text,kw)
            if hit:
                s+=hit
                evidence[c["id"]].append(f"keyword:{kw}")
        scores[c["id"]]=s

    # Source consensus is useful evidence, but never enough by itself to invent a use case.
    source_count=len(project.get("sources",[]))
    if source_count >= 2:
        for cid in scores:
            if scores[cid] > 0:
                scores[cid] += min(source_count-1, 2)

    ranked=sorted(scores.items(), key=lambda x:(-x[1],x[0]))
    best_id,best_score=ranked[0]
    second=ranked[1][1] if len(ranked)>1 else 0
    if best_score <= 0:
        return "unclassified", 0.0, []
    confidence=min(0.99, 0.50 + min(best_score,12)/24 + min(max(best_score-second,0),6)/20)
    return best_id, round(confidence,2), evidence[best_id][:6]

def main():
    payload=json.loads(PROJECTS.read_text(encoding="utf-8"))
    projects=payload.get("projects",[])
    by_cat=defaultdict(list)
    classified=[]
    for p in projects:
        cid,conf,evidence=classify_category(p)
        typ=classify_type(norm(" ".join([p.get("full_name",""),p.get("description","")," ".join(p.get("topics",[]))])))
        item=dict(p)
        item["type"]=typ
        item["primary_category"]=cid
        item["category_confidence"]=conf
        item["classification_evidence"]=evidence
        classified.append(item)
        by_cat[cid].append(item)

    cat_meta={c["id"]:c for c in CFG["categories"]}
    summary=[]
    for cid,c in cat_meta.items():
        rows=sorted(by_cat.get(cid,[]), key=lambda p:(-p.get("popularity_score",0),-p.get("stars",0)))
        summary.append({
            "id":cid,"name":c["name"],"emoji":c["emoji"],
            "count":len(rows),
            "meets_minimum":len(rows)>=CFG["min_projects_per_category"],
            "top_projects":[p["full_name"] for p in rows[:CFG["max_projects_per_category"]]]
        })

    OUT.write_text(json.dumps({
        "generated_at":payload.get("generated_at"),
        "minimum":CFG["min_projects_per_category"],
        "target":CFG["target_projects_per_category"],
        "maximum_display":CFG["max_projects_per_category"],
        "summary":summary,
        "unclassified_count":len(by_cat.get("unclassified",[])),
        "projects":classified
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Category coverage:", flush=True)
    for x in summary:
        flag="OK" if x["meets_minimum"] else "LOW"
        print(f"  [{flag}] {x['name']}: {x['count']}", flush=True)
    print(f"  Unclassified: {len(by_cat.get('unclassified',[]))}", flush=True)

if __name__=="__main__":
    main()
