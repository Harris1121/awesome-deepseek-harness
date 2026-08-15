#!/usr/bin/env python3
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/"data/categories.json").read_text(encoding="utf-8"))
README=ROOT/"README.md"

def row(i,p):
    g=p.get("growth_7d")
    gt="—" if g is None else f"{g:+.1f}%"
    return f"| {i} | [{p['full_name']}]({p['html_url']}) | {p.get('stars',0):,} | {gt} |"

projects=DATA["projects"]
parts=[]
for meta in DATA["summary"]:
    cid=meta["id"]
    rows=[p for p in projects if p.get("primary_category")==cid]
    rows.sort(key=lambda p:(-p.get("popularity_score",0),-p.get("stars",0)))
    rows=rows[:DATA["maximum_display"]]
    if len(rows) < DATA["minimum"]:
        continue
    parts += [
        f"### {meta['emoji']} {meta['name']}",
        "",
        f"*{len([p for p in projects if p.get('primary_category')==cid])} projects classified · showing top {len(rows)}*",
        "",
        "| Rank | Project | Stars | 7d Growth |",
        "|---:|---|---:|---:|",
        *[row(i,p) for i,p in enumerate(rows,1)],
        ""
    ]

block="\n".join(parts) if parts else "_No category has reached the minimum coverage threshold yet._"
text=README.read_text(encoding="utf-8")
start="<!-- CATEGORIES_START -->"; end="<!-- CATEGORIES_END -->"
if start not in text:
    text += "\n\n## 🧭 Popular by Use Case\n\n"+start+"\n"+end+"\n"
text=re.sub(r"(<!-- CATEGORIES_START -->)(.*?)(<!-- CATEGORIES_END -->)",rf"\1\n{block}\n\3",text,flags=re.S)
README.write_text(text,encoding="utf-8")
print("README category rankings updated.", flush=True)
