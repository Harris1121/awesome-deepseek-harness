#!/usr/bin/env python3
import datetime as dt, json, math, os, re, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOKEN=os.environ.get('GITHUB_TOKEN','')
HEADERS={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'awesome-deepseek-harness-ranking'}
if TOKEN: HEADERS['Authorization']=f'Bearer {TOKEN}'

def api_repo(name):
    req=urllib.request.Request('https://api.github.com/repos/'+name,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=15) as r:return json.loads(r.read().decode())

def load_snaps():
    out=[]
    for p in sorted((ROOT/'data/history').glob('*.json')):
        try: out.append(json.loads(p.read_text()))
        except: pass
    return out

def prior(snaps,name,days):
    target=dt.date.today()-dt.timedelta(days=days); c=[]
    for s in snaps:
        try:d=dt.date.fromisoformat(s['date'])
        except:continue
        item=s.get('projects',{}).get(name)
        if item:c.append((abs((d-target).days),item))
    if not c:return None
    c.sort(key=lambda x:x[0]); return c[0][1] if c[0][0] <= max(2,days//2) else None

def gain(now,b): return None if not b else now-b.get('stars',0)
def pct(now,b): return None if not b or b.get('stars',0)<=0 else (now-b['stars'])/b['stars']*100

def table(items):
    if not items:return '_Not enough history yet._'
    lines=['| Rank | Project | Stars | 7d Gain | 7d Growth |','|---:|---|---:|---:|---:|']
    for i,p in enumerate(items[:10],1):
        g=p.get('gain_7d'); gr=p.get('growth_7d')
        lines.append(f"| {i} | [{p['full_name']}]({p['html_url']}) | {p['stars']:,} | {'—' if g is None else f'{g:+,}'} | {'—' if gr is None else f'{gr:+.1f}%'} |")
    return '\n'.join(lines)

def update_readme(projects):
    popular=sorted(projects,key=lambda p:(-p['popularity_score'],-p['stars']))
    trending=sorted([p for p in projects if (p.get('gain_7d') or 0)>0],key=lambda p:(-p['gain_7d'],-(p.get('growth_7d') or 0),-p['stars']))
    rising=sorted([p for p in projects if (p.get('growth_7d') or 0)>0],key=lambda p:(-p['rising_score'],-p['stars']))
    text=(ROOT/'README.md').read_text()
    for key,val in [('POPULAR',table(popular)),('TRENDING',table(trending)),('RISING',table(rising))]:
        text=re.sub(rf'(<!-- {key}_START -->)(.*?)(<!-- {key}_END -->)',rf'\1\n{val}\n\3',text,flags=re.S)
    (ROOT/'README.md').write_text(text)

def main():
    pool=json.loads((ROOT/'data/repositories.json').read_text()).get('repositories',[])
    snaps=load_snaps(); projects=[]; failures=[]
    print(f'[1/4] Updating {len(pool)} repositories...',flush=True)
    for i,e in enumerate(pool,1):
        name=e['full_name']
        try:
            r=api_repo(name); stars=int(r.get('stargazers_count',0)); p7=prior(snaps,name,7); p30=prior(snaps,name,30)
            projects.append({'full_name':name,'html_url':r.get('html_url'),'description':r.get('description') or '','stars':stars,'forks':int(r.get('forks_count',0)),'watchers':int(r.get('subscribers_count',0)),'open_issues':int(r.get('open_issues_count',0)),'language':r.get('language'),'license':(r.get('license') or {}).get('spdx_id'),'created_at':r.get('created_at'),'updated_at':r.get('updated_at'),'pushed_at':r.get('pushed_at'),'topics':r.get('topics') or [],'sources':e.get('sources',[]),'first_seen':e.get('first_seen'),'gain_7d':gain(stars,p7),'growth_7d':pct(stars,p7),'gain_30d':gain(stars,p30),'growth_30d':pct(stars,p30)})
        except Exception as ex: failures.append({'repo':name,'error':str(ex)})
        if i%25==0 or i==len(pool): print(f'  {i}/{len(pool)} complete; failures={len(failures)}',flush=True)
    print('[2/4] Computing scores...',flush=True)
    max_stars=max([p['stars'] for p in projects] or [1]); max_gain=max([max(p.get('gain_7d') or 0,0) for p in projects] or [1])
    for p in projects:
        s=math.log1p(p['stars'])/math.log1p(max_stars) if max_stars else 0
        if p.get('gain_7d') is None: pop=s
        else:
            gs=math.log1p(max(p['gain_7d'],0))/math.log1p(max_gain) if max_gain>0 else 0
            pop=.70*s+.30*gs
        p['popularity_score']=round(pop*100,2); p['rising_score']=round(math.log1p(max(p.get('gain_7d') or 0,0))*max(p.get('growth_7d') or 0,0),3)
    print('[3/4] Saving data...',flush=True)
    now=dt.datetime.now(dt.timezone.utc).isoformat(); today=dt.date.today().isoformat()
    (ROOT/'data/projects.json').write_text(json.dumps({'generated_at':now,'projects':projects,'failures':failures},ensure_ascii=False,indent=2)+'\n')
    snap={'date':today,'generated_at':now,'projects':{p['full_name']:{'stars':p['stars'],'forks':p['forks']} for p in projects}}
    (ROOT/'data/history'/f'{today}.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n')
    print('[4/4] Updating README...',flush=True); update_readme(projects)
    print(f'Done. Updated {len(projects)}; failures={len(failures)}.',flush=True)
if __name__=='__main__': main()
