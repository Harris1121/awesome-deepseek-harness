#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/"data/categories.json").read_text());CFG=json.loads((ROOT/"config/ecosystem.json").read_text());R=ROOT/"README.md"
EM={"Coding & Development":"💻","Research & Search":"🔎","Writing & Content":"✍️","Image & Design":"🎨","Video & Audio":"🎬","Browser & Web":"🌐","Memory & Context":"🧠","Agents & Automation":"🤖","Data & Analytics":"📊","Documents & Office":"📄","Communication":"💬","Developer Experience":"🛠"}
STATUS={"Official":"🟢 Official","DSH Native":"🔌 DSH Native","Verified Compatible":"✓ Compatible","Community":"Community"}
parts=[]
for cat in CFG["use_cases"]:
 rows=[p for p in D["projects"] if p.get("primary_category")==cat]
 rows.sort(key=lambda p:(-p.get("popularity_score_v24",0),-p.get("stars",0)))
 if len(rows)<CFG["minimum_display"]:continue
 selected=[]
 for idx,p in enumerate(rows[:CFG["maximum_display"]],1):
  if idx>CFG["hide_after_rank"] and p.get("stars",0)<CFG["min_stars_after_rank"]:continue
  selected.append(p)
 if not selected:continue
 parts += [f"### {EM[cat]} {cat}","",f"*{len(rows)} projects classified · showing {len(selected)}*","",
 "| Rank | Project | Stars | 3d Gain | Status |","|---:|---|---:|---:|---|"]
 for i,p in enumerate(selected,1):
  gain="—" if p.get("gain_3d") is None else f"{p['gain_3d']:+,}"
  parts.append(f"| {i} | [{p['full_name']}]({p['html_url']}) | {p.get('stars',0):,} | {gain} | {STATUS.get(p.get('ecosystem_status'),p.get('ecosystem_status',''))} |")
 parts.append("")
block="\n".join(parts)
text=R.read_text()
# Remove old category sections from prior versions.
text=re.sub(r"\n*##\s+🧭\s+Popular by (?:Use Case|Category).*?<!-- CATEGORIES_START -->.*?<!-- CATEGORIES_END -->\s*","\n",text,flags=re.S)
section="\n## 🧭 Popular by Category\n\n<!-- CATEGORIES_START -->\n"+block+"\n<!-- CATEGORIES_END -->\n"
# Insert before Data pipeline, then License naturally remains at bottom.
m=re.search(r"\n##\s+Data pipeline\b",text,re.I)
if m:text=text[:m.start()]+section+"\n"+text[m.start():]
else:
 m=re.search(r"\n##\s+License\b",text,re.I)
 text=(text[:m.start()]+section+"\n"+text[m.start():]) if m else text.rstrip()+"\n"+section
text=re.sub(r"\n{4,}","\n\n\n",text)
R.write_text(text)
print("Rendered V2.4 category rankings.",flush=True)
