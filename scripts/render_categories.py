#!/usr/bin/env python3
import json, re, datetime as dt
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/"data/categories.json").read_text(encoding="utf-8"))
CFG=json.loads((ROOT/"config/ecosystem.json").read_text(encoding="utf-8"))
R=ROOT/"README.md"
EM={"Coding & Development":"💻","Research & Search":"🔎","Writing & Content":"✍️","Image & Design":"🎨","Video & Audio":"🎬","Browser & Web":"🌐","Memory & Context":"🧠","Agents & Automation":"🤖","Data & Analytics":"📊","Documents & Office":"📄","Communication":"💬","Developer Experience":"🛠"}
STATUS={"Official":"🟢 Official","DSH Native":"🔌 DSH Native","Verified Compatible":"✓ Compatible","Community":"Community"}
def ks(n):
    return (f"{n/1000:.1f}".rstrip("0").rstrip(".")+"k") if n>=1000 else str(n)
def desc(s):
    s=re.sub(r"\\s+"," ",s or "").strip()
    if not s:return "No description available yet."
    return s[:177].rstrip()+"..." if len(s)>180 else s
def popular():
    rows=sorted(D["projects"],key=lambda p:(-p.get("popularity_score_v24",0),-p.get("stars",0)))[:10]
    a=["| Rank | Project | Stars | 3d Gain | Status |","|---:|---|---:|---:|---|"]
    for i,p in enumerate(rows,1):
        g="—" if p.get("gain_3d") is None else f"{p['gain_3d']:+,}"
        a.append(f"| {i} | [{p['full_name']}]({p['html_url']}) | {p.get('stars',0):,} | {g} | {STATUS.get(p.get('ecosystem_status'),p.get('ecosystem_status',''))} |")
    return "\n".join(a)
def categories():
    a=[]
    for cat in CFG["use_cases"]:
        rows=[p for p in D["projects"] if p.get("primary_category")==cat]
        rows.sort(key=lambda p:(-p.get("popularity_score_v24",0),-p.get("stars",0)))
        if len(rows)<CFG["minimum_display"]:continue
        sel=[]
        for i,p in enumerate(rows[:CFG["maximum_display"]],1):
            if i>CFG["hide_after_rank"] and p.get("stars",0)<CFG["min_stars_after_rank"]:continue
            sel.append(p)
        if not sel:continue
        a += [f"### {EM[cat]} {cat}",""]
        for i,p in enumerate(sel,1):
            gain="" if p.get("gain_3d") is None else f" · 📈 {p['gain_3d']:+,} / 3d"
            a += [f"**{i}. [{p['full_name']}]({p['html_url']})** · ⭐ {ks(p.get('stars',0))}{gain} · {STATUS.get(p.get('ecosystem_status'),p.get('ecosystem_status',''))}",desc(p.get("description")),""]
    return "\n".join(a)
def trends():
    blocks=[]; ps=D["projects"]
    t=[p for p in ps if (p.get("gain_3d") or 0)>0]
    if t:
        t.sort(key=lambda p:(-p["gain_3d"],-(p.get("growth_3d") or 0),-p.get("stars",0)))
        a=["## 🔥 Trending","","| Rank | Project | Stars | 3d Gain |","|---:|---|---:|---:|"]
        for i,p in enumerate(t[:10],1):a.append(f"| {i} | [{p['full_name']}]({p['html_url']}) | {p['stars']:,} | {p['gain_3d']:+,} |")
        blocks.append("\n".join(a))
    r=[p for p in ps if (p.get("growth_3d") or 0)>0]
    if r:
        r.sort(key=lambda p:(-(p.get("growth_3d") or 0),-(p.get("gain_3d") or 0),-p.get("stars",0)))
        a=["## 🌱 Rising","","| Rank | Project | Stars | 3d Growth |","|---:|---|---:|---:|"]
        for i,p in enumerate(r[:10],1):a.append(f"| {i} | [{p['full_name']}]({p['html_url']}) | {p['stars']:,} | {p['growth_3d']:+.1f}% |")
        blocks.append("\n".join(a))
    return "\n\n".join(blocks)
def main():
    tracked=len(D["projects"])
    cats=sum(1 for c in CFG["use_cases"] if len([p for p in D["projects"] if p.get("primary_category")==c])>=CFG["minimum_display"])
    updated=(D.get("generated_at") or "")[:10] or dt.date.today().isoformat()
    text=f"""# Awesome DeepSeek Harness

> Discover the most popular and fastest-growing projects in the DeepSeek Harness ecosystem.

Awesome DeepSeek Harness is a curated, data-driven guide to plugins, clients, integrations, tools and resources that work with **DeepSeek Harness**. It tracks community adoption and short-term momentum so you can quickly find the projects that matter instead of digging through hundreds of repositories.

**{tracked:,} projects tracked · {cats} categories · Updated daily · Last data refresh: {updated}**

## Why this list?

- ⭐ **Star-first rankings** — GitHub Stars are the primary popularity signal.
- 📈 **3-day momentum** — Short-term Star gains and growth highlight what's heating up now.
- 🔄 **Updated daily** — Projects, Stars, classifications and rankings refresh automatically every day.
- 🧭 **Practical categories** — Browse by what you want DeepSeek Harness to do.
- 🟢 **Ecosystem status** — Distinguishes Official, DSH Native, Compatible and Community projects.
- 🔍 **Broad discovery** — Projects are discovered across the public DeepSeek Harness ecosystem and GitHub.

> This is an independent community project and is not affiliated with or endorsed by DeepSeek.

## DeepSeek Harness

DeepSeek Harness (`dsh`) is DeepSeek AI's open-source agent harness. Its architecture follows the idea that **everything is a plugin**, making the model, tools, sessions, UI and agent behavior extensible.

> **Developer Preview:** DeepSeek notes that Harness is evolving rapidly and may introduce compatibility-breaking changes.

### Quick Start

Install **Node.js**, then start the official Web UI:

```bash
npx @deepseek-ai/dsh web
```

By default, the Web UI is served at `http://127.0.0.1:3080`.

To run from source:

```bash
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
pnpm install
pnpm run build
pnpm dsh web
```

**Official resources:** [DeepSeek Harness repository](https://github.com/deepseek-ai/deepseek-harness) · [DeepSeek Harness website](https://deepseek.com/harness)

## 🔥 Popular

{popular()}

## 🧭 Popular by Category

{categories()}
"""
    tr=trends()
    if tr:text+="\n"+tr+"\n\n"
    text+="""## 📊 How Rankings Work

**Popular** uses a Star-first model:

- **70%** GitHub Stars
- **20%** 3-day Star gain
- **10%** 3-day Star growth rate

When there is not yet enough 3-day history, the ranking naturally relies more heavily on current Stars. Trending and Rising are hidden until real historical data is available.

## 🔄 Update Cycle

This repository updates automatically **every day**:

`Discover → Track → Classify → Rank → Publish`

Historical snapshots are retained so short-term growth is calculated from actual Star changes.

## 🤝 Contributing

Found a useful DeepSeek Harness project that is missing, misclassified or incorrectly marked? Open an issue or pull request. For DSH plugins, adding the `dsh-plugin` GitHub topic also improves discoverability.

## License

CC0 1.0
"""
    R.write_text(text,encoding="utf-8")
    print(f"README rebuilt: {tracked} projects, {cats} categories.",flush=True)
if __name__=="__main__":main()
