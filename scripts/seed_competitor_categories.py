#!/usr/bin/env python3
import json,re,urllib.request
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/competitor-categories.json"

SOURCES=[
 ("0xsline","https://raw.githubusercontent.com/0xsline/awesome-deepseek-harness/main/README.md"),
 ("awesome-dsh-plugin","https://raw.githubusercontent.com/awesome-dsh-plugin/awesome-dsh-plugin/main/README.md"),
 ("libukai","https://raw.githubusercontent.com/libukai/awesome-deepseek-harness/main/README.md"),
]
repo_re=re.compile(r'https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)')
heading_re=re.compile(r'^##+\s+(.*)$')

def fetch(url):
 req=urllib.request.Request(url,headers={"User-Agent":"dsh-category-seeder"})
 with urllib.request.urlopen(req,timeout=20) as r:return r.read().decode("utf-8","replace")

def clean_heading(s):
 s=re.sub(r'<[^>]+>','',s)
 s=re.sub(r'[*_`#]','',s)
 return s.strip()

def parse(text,source):
 current=None; out=[]
 for line in text.splitlines():
  m=heading_re.match(line.strip())
  if m:
   current=clean_heading(m.group(1))
   continue
  for owner,repo in repo_re.findall(line):
   repo=repo.rstrip(").,;#")
   if repo.endswith(".git"):repo=repo[:-4]
   if owner in {"topics","orgs","features","settings"}:continue
   out.append((f"{owner}/{repo}",current))
 return out

def main():
 by_repo=defaultdict(lambda:defaultdict(list))
 stats={}
 for name,url in SOURCES:
  try:
   rows=parse(fetch(url),name);stats[name]=len(rows)
   for repo,cat in rows:
    if cat and cat not in by_repo[repo][name]:by_repo[repo][name].append(cat)
  except Exception as e:
   stats[name]=f"ERROR: {e}"
 payload={"sources":stats,"projects":{}}
 for repo,sources in by_repo.items():
  payload["projects"][repo]={"source_categories":dict(sources)}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
 print("Competitor category seed:",flush=True)
 for k,v in stats.items():print(f"  {k}: {v}",flush=True)
 print(f"  unique repos: {len(by_repo)}",flush=True)
if __name__=="__main__":main()
