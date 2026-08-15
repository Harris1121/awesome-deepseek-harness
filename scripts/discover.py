#!/usr/bin/env python3
import datetime as dt, json, os, re, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOKEN=os.environ.get('GITHUB_TOKEN','')
HEADERS={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'awesome-deepseek-harness-discovery'}
if TOKEN: HEADERS['Authorization']=f'Bearer {TOKEN}'
GH_REPO_RE=re.compile(r'https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)')

def fetch_text(url):
    req=urllib.request.Request(url,headers={'User-Agent':HEADERS['User-Agent']})
    with urllib.request.urlopen(req,timeout=15) as r: return r.read().decode('utf-8',errors='replace')

def api_get(path,params=None):
    url='https://api.github.com'+path
    if params: url+='?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read().decode())

def norm(owner,repo):
    repo=repo.rstrip(').,;#')
    if repo.endswith('.git'): repo=repo[:-4]
    return f'{owner}/{repo}'

def extract(text):
    out=set()
    for owner,repo in GH_REPO_RE.findall(text):
        if owner in {'topics','orgs','marketplace','features','settings'}: continue
        out.add(norm(owner,repo))
    return out

def main():
    cfg=json.loads((ROOT/'config/sources.json').read_text())
    ov=json.loads((ROOT/'config/overrides.json').read_text())
    include,exclude=set(ov.get('include',[])),set(ov.get('exclude',[]))
    old=json.loads((ROOT/'data/repositories.json').read_text())
    known={x['full_name']:x for x in old.get('repositories',[])}
    found={}
    def add(repo,source):
        if repo in exclude: return
        found.setdefault(repo,set()).add(source)
    print('[1/3] Reading competitor catalogs...',flush=True)
    for src in cfg['competitor_sources']:
        for url in src['urls']:
            try:
                repos=extract(fetch_text(url)); print(f"  {src['name']}: {len(repos)}",flush=True)
                for repo in repos: add(repo,'competitor:'+src['name'])
            except Exception as e: print(f"  WARN {src['name']}: {e}",flush=True)
    print('[2/3] GitHub topic/search discovery...',flush=True)
    for q in cfg['github_searches']:
        try:
            data=api_get('/search/repositories',{'q':q,'sort':'stars','order':'desc','per_page':min(int(cfg.get('max_search_results_per_query',100)),100)})
            items=data.get('items',[]); print(f'  {q}: {len(items)}',flush=True)
            for item in items: add(item['full_name'],'github-search:'+q)
        except Exception as e: print(f'  WARN search {q}: {e}',flush=True)
    for repo in include: add(repo,'manual-include')
    print('[3/3] Merging candidate pool...',flush=True)
    today=dt.date.today().isoformat(); merged={}
    for repo,e in known.items(): merged[repo]={'sources':set(e.get('sources',[])),'first_seen':e.get('first_seen',today),'last_seen':e.get('last_seen',today)}
    for repo,sources in found.items():
        merged.setdefault(repo,{'sources':set(),'first_seen':today,'last_seen':today})
        merged[repo]['sources'].update(sources); merged[repo]['last_seen']=today
    rows=[{'full_name':r,'sources':sorted(e['sources']),'first_seen':e['first_seen'],'last_seen':e['last_seen']} for r,e in sorted(merged.items()) if r not in exclude]
    payload={'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'repositories':rows}
    (ROOT/'data/repositories.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(f'Done. Candidate pool: {len(rows)} repositories.',flush=True)
if __name__=='__main__': main()
