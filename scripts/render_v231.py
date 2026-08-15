#!/usr/bin/env python3
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/"data/categories.json").read_text())
M=json.loads((ROOT/"config/competitor-category-map.json").read_text())
R=ROOT/"README.md"

emoji={
"Coding & Development":"💻",
"Research & Search":"🔎",
"Writing & Content":"✍️",
"Image & Design":"🎨",
"Video & Audio":"🎬",
"Browser & Web":"🌐",
"Memory & Context":"🧠",
"Agents & Automation":"🤖",
"Data & Analytics":"📊",
"Documents & Office":"📄",
"Communication":"💬",
"Developer Experience":"🛠"
}
order=list(emoji)

parts=[]

for cat in order:
 rows=[p for p in D["projects"] if p["primary_category"]==cat]
 rows.sort(key=lambda p:(-p.get("popularity_score_v231",0),-p.get("stars",0)))

 if len(rows)<M["minimum_display"]:
  continue

 rows=rows[:M["maximum_display"]]

 parts += [
  f"### {emoji[cat]} {cat}",
  "",
  f"*{len([p for p in D['projects'] if p['primary_category']==cat])} projects · Top {len(rows)} by star-first popularity*",
  "",
  "| Rank | Project | Stars | 3d Gain | 3d Growth | Source |",
  "|---:|---|---:|---:|---:|---|"
 ]

 for i,p in enumerate(rows,1):
  gain="—" if p.get("gain_3d") is None else f"{p['gain_3d']:+,}"
  growth="—" if p.get("growth_3d") is None else f"{p['growth_3d']:+.1f}%"
  method=p.get("category_method","")
  parts.append(
      f"| {i} | [{p['full_name']}]({p['html_url']}) | "
      f"{p.get('stars',0):,} | {gain} | {growth} | {method} |"
  )

 parts.append("")

block="\n".join(parts)

text=R.read_text()
start="<!-- CATEGORIES_START -->"
end="<!-- CATEGORIES_END -->"

if start not in text:
 text+="\n\n## 🧭 Popular by Use Case\n\n"+start+"\n"+end+"\n"

text=re.sub(
    r"(<!-- CATEGORIES_START -->)(.*?)(<!-- CATEGORIES_END -->)",
    rf"\1\n{block}\n\3",
    text,
    flags=re.S
)

R.write_text(text)
print("README updated with 3-day star-first category rankings.",flush=True)
