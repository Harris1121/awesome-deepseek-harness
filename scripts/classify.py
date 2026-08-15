#!/usr/bin/env python3
import json,re
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/ecosystem.json").read_text())
SEED=json.loads((ROOT/"data/competitor-categories.json").read_text()).get("projects",{})
P=json.loads((ROOT/"data/projects.json").read_text())
OUT=ROOT/"data/categories.json"
KW={
"Coding & Development":["code","coding","git","github","test","debug","developer","devops"],
"Research & Search":["research","search","rag","retrieval","paper","news"],
"Writing & Content":["writing","writer","article","blog","report","markdown","novel","content"],
"Image & Design":["image","vision","ocr","design","figma","canvas","screenshot"],
"Video & Audio":["video","audio","voice","speech","tts","ffmpeg","subtitle","youtube","media"],
"Browser & Web":["browser","chrome","playwright","puppeteer","crawler","scrape"],
"Memory & Context":["memory","context","session","recall","knowledge"],
"Agents & Automation":["agent","workflow","automation","subagent","orchestration","task"],
"Data & Analytics":["data","database","sql","csv","analytics","spreadsheet","chart"],
"Documents & Office":["pdf","docx","office","document","word","powerpoint","file"],
"Communication":["slack","telegram","discord","wechat","feishu","lark","email","notification"],
"Developer Experience":["desktop","tui","cli","ide","vscode","client","theme","ui","marketplace"]
}
def norm(s):return re.sub(r"[^a-z0-9+#.-]+"," ",(s or "").lower())
def mapcat(cat):
 if not cat:return None
 if cat in CFG["use_case_map"]:return CFG["use_case_map"][cat]
 low=cat.lower()
 for a,b in CFG["use_case_map"].items():
  if a.lower() in low:return b
 hints={"workflow":"Agents & Automation","agent":"Agents & Automation","context":"Memory & Context","session":"Memory & Context","memory":"Memory & Context","browser":"Browser & Web","visual":"Image & Design","vision":"Image & Design","client":"Developer Experience","desktop":"Developer Experience","tui":"Developer Experience","developer":"Coding & Development","git":"Coding & Development","research":"Research & Search","search":"Research & Search","office":"Documents & Office","document":"Documents & Office","notification":"Communication","channel":"Communication","writing":"Writing & Content","content":"Writing & Content","video":"Video & Audio","audio":"Video & Audio","data":"Data & Analytics"}
 for k,v in hints.items():
  if k in low:return v
 return None
def metadata_scores(p):
 text=norm(" ".join([p.get("full_name",""),p.get("description","")," ".join(p.get("topics",[]))]))
 return {cat:sum(1 for k in kws if norm(k).strip() in text) for cat,kws in KW.items()}
def category(p):
 src=SEED.get(p["full_name"],{}).get("source_categories",{})
 votes=[];ev=[]
 for source,cats in src.items():
  mapped=set()
  for c in cats:
   m=mapcat(c)
   if m:mapped.add(m);ev.append(f"{source}:{c}->{m}")
  votes.extend(mapped)
 counts=Counter(votes)
 if counts:
  top=counts.most_common()
  if top[0][1]>=2 and (len(top)==1 or top[0][1]>top[1][1]):return top[0][0],"competitor-consensus",.98,ev,src
  if len(set(votes))==1:return votes[0],"competitor-inherited",.92,ev,src
  scores=metadata_scores(p)
  for c,n in counts.items():scores[c]+=2*n
  best=max(scores,key=scores.get)
  return best,"competitor-conflict-resolved",.80,ev+[f"metadata:{best}={scores[best]}"],src
 scores=metadata_scores(p);best=max(scores,key=scores.get)
 if scores[best]>0:return best,"metadata-fallback",.60,[f"metadata:{best}={scores[best]}"],src
 return "Unclassified","unclassified",0,[],src
def status(p):
 full=p["full_name"];owner=full.split("/")[0].lower()
 src=SEED.get(full,{}).get("source_categories",{})
 text=norm(" ".join([full,p.get("description","")," ".join(p.get("topics",[]))]))
 if full in CFG["official_repos"] or owner in [x.lower() for x in CFG["official_orgs"]]:
  return "Official",["official-owner/repo"]
 # Presence in competitor catalogs is community evidence, not official endorsement.
 if any(x in text for x in CFG["native_evidence"]):
  return "DSH Native",["native-evidence"]
 if any(x in text for x in CFG["compatible_evidence"]):
  return "Verified Compatible",["compatibility-evidence"]
 if src:
  return "Community",["ecosystem-catalog"]
 return "Community",["discovery"]
def percentile(vals,x):
 if not vals:return 0
 return sum(v<=x for v in vals)/len(vals)
def main():
 ps=P.get("projects",[])
 stars=sorted([p.get("stars",0) for p in ps]);gains=sorted([max(p.get("gain_3d") or 0,0) for p in ps]);growth=sorted([max(p.get("growth_3d") or 0,0) for p in ps])
 out=[];summary=defaultdict(int);methods=Counter();statuses=Counter()
 for p in ps:
  q=dict(p);cat,method,conf,ev,src=category(p);st,stev=status(p)
  q.update({"primary_category":cat,"category_method":method,"category_confidence":conf,"classification_evidence":ev,"source_categories":src,"ecosystem_status":st,"status_evidence":stev})
  s=percentile(stars,q.get("stars",0));g=percentile(gains,max(q.get("gain_3d") or 0,0));r=percentile(growth,max(q.get("growth_3d") or 0,0));w=CFG["popular_weights"]
  q["popularity_score_v24"]=round(100*(w["stars"]*s+w["star_gain_3d"]*g+w["growth_rate_3d"]*r),2)
  out.append(q);summary[cat]+=1;methods[method]+=1;statuses[st]+=1
 OUT.write_text(json.dumps({"generated_at":P.get("generated_at"),"ranking_model":"v2.4-star-first-3d","weights":CFG["popular_weights"],"summary":dict(summary),"methods":dict(methods),"statuses":dict(statuses),"projects":out},ensure_ascii=False,indent=2)+"\n")
 print("Categories:",dict(summary),flush=True);print("Statuses:",dict(statuses),flush=True);print("Methods:",dict(methods),flush=True)
if __name__=="__main__":main()
