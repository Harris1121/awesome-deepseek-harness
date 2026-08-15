#!/usr/bin/env python3
import json,re
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP=json.loads((ROOT/"config/competitor-category-map.json").read_text())
SEED=json.loads((ROOT/"data/competitor-categories.json").read_text()).get("projects",{})
P=json.loads((ROOT/"data/projects.json").read_text())
OUT=ROOT/"data/categories.json"

USE_CASES=[
"Coding & Development","Research & Search","Writing & Content","Image & Design",
"Video & Audio","Browser & Web","Memory & Context","Agents & Automation",
"Data & Analytics","Documents & Office","Communication","Developer Experience"
]

KW={
"Coding & Development":["code","coding","git","github","test","debug","developer","devops"],
"Research & Search":["research","search","rag","retrieval","zotero","paper","news"],
"Writing & Content":["writing","writer","article","blog","report","markdown","novel","content"],
"Image & Design":["image","vision","ocr","design","figma","canvas","screenshot"],
"Video & Audio":["video","audio","voice","speech","tts","ffmpeg","subtitle","youtube","media"],
"Browser & Web":["browser","chrome","playwright","puppeteer","web search","crawler","scrape"],
"Memory & Context":["memory","context","session","recall","knowledge"],
"Agents & Automation":["agent","workflow","automation","subagent","orchestration","task"],
"Data & Analytics":["data","database","sql","csv","analytics","spreadsheet","chart"],
"Documents & Office":["pdf","docx","office","document","word","powerpoint","file"],
"Communication":["slack","telegram","discord","wechat","feishu","lark","email","notification"],
"Developer Experience":["desktop","tui","cli","ide","vscode","client","theme","ui","marketplace"]
}

def n(s):return re.sub(r"[^a-z0-9+#.-]+"," ",(s or "").lower())

def keyword_scores(p):
 text=n(" ".join([p.get("full_name",""),p.get("description","")," ".join(p.get("topics",[]))]))
 scores={}
 for cat,kws in KW.items():
  scores[cat]=sum(1 for k in kws if n(k).strip() in text)
 return scores

def map_source_category(cat):
 if not cat:return None
 if cat in MAP["use_case_map"]:return MAP["use_case_map"][cat]
 low=cat.lower()
 for src,dst in MAP["use_case_map"].items():
  if src.lower() in low:return dst

 hints={
  "workflow":"Agents & Automation","agent":"Agents & Automation",
  "context":"Memory & Context","session":"Memory & Context","memory":"Memory & Context",
  "browser":"Browser & Web","visual":"Image & Design","vision":"Image & Design",
  "client":"Developer Experience","desktop":"Developer Experience","tui":"Developer Experience",
  "developer":"Coding & Development","git":"Coding & Development",
  "research":"Research & Search","search":"Research & Search",
  "office":"Documents & Office","document":"Documents & Office",
  "notification":"Communication","channel":"Communication",
  "writing":"Writing & Content","content":"Writing & Content",
  "video":"Video & Audio","audio":"Video & Audio"
 }
 for k,v in hints.items():
  if k in low:return v
 return None

def classify(p):
 src=SEED.get(p["full_name"],{}).get("source_categories",{})
 votes=[]; evidence=[]
 for source,cats in src.items():
  mapped=[]
  for c in cats:
   m=map_source_category(c)
   if m:
    mapped.append(m); evidence.append(f"{source}:{c}->{m}")
  votes.extend(sorted(set(mapped)))

 counts=Counter(votes)
 if counts:
  top=counts.most_common()
  if top[0][1]>=2 and (len(top)==1 or top[0][1]>top[1][1]):
   return top[0][0],"competitor-consensus",0.98,evidence,src

  distinct=set(votes)
  if len(src)==1 and len(distinct)==1:
   return next(iter(distinct)),"competitor-single-source",0.90,evidence,src

  if len(distinct)==1:
   return next(iter(distinct)),"competitor-consensus",0.96,evidence,src

  scores=keyword_scores(p)
  for cat,count in counts.items():
   scores[cat]=scores.get(cat,0)+count*2
  best=max(scores,key=scores.get)
  return best,"competitor-conflict-resolved",0.78,evidence+[f"metadata-score:{best}={scores[best]}"],src

 scores=keyword_scores(p)
 best=max(scores,key=scores.get)
 if scores[best]>0:
  return best,"metadata-fallback",0.60,[f"metadata-score:{best}={scores[best]}"],src

 return "Unclassified","unclassified",0.0,[],src

def percentile(vals,x):
 if not vals:return 0
 return sum(v<=x for v in vals)/len(vals)

def main():
 projects=P.get("projects",[])
 stars=sorted([p.get("stars",0) for p in projects])
 gains=sorted([max(p.get("gain_3d") or 0,0) for p in projects])
 growths=sorted([max(p.get("growth_3d") or 0,0) for p in projects])

 out=[];summary=defaultdict(int);methods=Counter()

 for p in projects:
  cat,method,conf,ev,src=classify(p)
  q=dict(p)
  q["primary_category"]=cat
  q["category_method"]=method
  q["category_confidence"]=conf
  q["classification_evidence"]=ev
  q["source_categories"]=src

  s=percentile(stars,q.get("stars",0))
  g=percentile(gains,max(q.get("gain_3d") or 0,0))
  r=percentile(growths,max(q.get("growth_3d") or 0,0))

  w=MAP["popular_weights"]
  q["popularity_score_v231"]=round(
      100*(
          w["stars"]*s
          + w["star_gain_3d"]*g
          + w["growth_rate_3d"]*r
      ),
      2
  )

  out.append(q)
  summary[cat]+=1
  methods[method]+=1

 OUT.write_text(json.dumps({
  "generated_at":P.get("generated_at"),
  "ranking_model":"v2.3.1-star-first-3d",
  "weights":MAP["popular_weights"],
  "summary":dict(summary),
  "methods":dict(methods),
  "projects":out
 },ensure_ascii=False,indent=2)+"\n")

 print("Classification methods:",dict(methods),flush=True)
 print("Category coverage:",flush=True)
 for c in USE_CASES:print(f"  {c}: {summary[c]}",flush=True)
 print(f"  Unclassified: {summary['Unclassified']}",flush=True)

if __name__=="__main__":main()
