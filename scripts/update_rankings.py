#!/usr/bin/env python3
import datetime as dt, json, math, os, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; CONFIG=ROOT/'config'; DATA=ROOT/'data'; HISTORY=DATA/'history'; README=ROOT/'README.md'
API='https://api.github.com'; TOKEN=os.environ.get('GITHUB_TOKEN','')
HEAD={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'awesome-deepseek-harness-radar'}
if TOKEN: HEAD['Authorization']=f'Bearer {TOKEN}'

def get_json(url, headers=None):
    req=urllib.request.Request(url,headers=headers or {'User-Agent':'awesome-deepseek-harness-radar'})
    for i in range(5):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode())
        except Exception:
            if i==4: raise
            time.sleep(2**i)

def get_text(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'awesome-deepseek-harness-radar'})
        with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode('utf-8','replace')
    except Exception:return ''

def api(path,params=None):
    u=API+path
    if params:u+='?'+urllib.parse.urlencode(params)
    return get_json(u,HEAD)

def load(p,d):
    try:return json.loads(Path(p).read_text())
    except Exception:return d

def discover():
    c=load(CONFIG/'sources.json',{}); repos={}
    for q in c.get('github_searches',[]):
        try:
            x=api('/search/repositories',{'q':q,'sort':'stars','order':'desc','per_page':min(c.get('per_search',100),100)})
            for r in x.get('items',[]):repos[r['full_name']]=r
        except Exception as e: print('search failed',q,e)
    try:
        x=api('/search/repositories',{'q':'topic:'+c.get('github_topic','dsh-plugin'),'sort':'stars','order':'desc','per_page':100})
        for r in x.get('items',[]):repos[r['full_name']]=r
    except Exception as e: print('topic failed',e)
    # Public catalogs are discovery seeds; we do not trust their metadata.
    pat=re.compile(r'https?://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)')
    for url in c.get('competitor_catalogs',[]):
        for full in set(pat.findall(get_text(url))):
            if full in repos:continue
            if full.lower() in {'github/github'}:continue
            try:repos[full]=api('/repos/'+full)
            except Exception:pass
    inc=load(CONFIG/'overrides.json',{}).get('include',[])
    for full in inc:
        if full not in repos:
            try:repos[full]=api('/repos/'+full)
            except Exception:pass
    exc=set(load(CONFIG/'overrides.json',{}).get('exclude',[]))
    return {k:v for k,v in repos.items() if k not in exc}

def snapshots():
    out=[]
    for p in sorted(HISTORY.glob('*.json')):
        try:out.append(json.loads(p.read_text()))
        except Exception:pass
    return out

def past(snaps,name,days):
    target=dt.date.today()-dt.timedelta(days=days); best=None; dist=999
    for s in snaps:
        try:d=dt.date.fromisoformat(s['date'])
        except Exception:continue
        n=abs((d-target).days)
        if n<dist and n<=max(days+3,3) and name in s.get('projects',{}):best=s['projects'][name];dist=n
    return best

def pct(now,old):return None if old in (None,0) else (now-old)/old*100

def category(r):
    t=' '.join([r.get('name',''),r.get('description') or '',' '.join(r.get('topics') or [])]).lower()
    if 'dsh-plugin' in r.get('topics',[]) or 'plugin' in t:return 'Plugins'
    if any(x in t for x in ['desktop','electron']):return 'Desktop'
    if any(x in t for x in ['tui','terminal ui']):return 'TUI'
    if 'mcp' in t:return 'MCP'
    if any(x in t for x in ['browser','playwright','puppeteer']):return 'Browser'
    if 'skill' in t:return 'Skills'
    if any(x in t for x in ['guide','tutorial','awesome','docs']):return 'Guides & Resources'
    if any(x in t for x in ['web','frontend','ui']):return 'Web'
    return 'Projects'

def packages(r):
    # Limited to the most-starred candidates to keep the daily run cheap.
    owner=r['owner']['login']; name=r['name']; branch=urllib.parse.quote(r.get('default_branch') or 'main')
    out={'npm':None,'pypi':None}
    raw=get_text(f'https://raw.githubusercontent.com/{owner}/{name}/{branch}/package.json')
    if raw:
        try:
            p=json.loads(raw); n=p.get('name')
            if n:
                reg=get_json('https://registry.npmjs.org/'+urllib.parse.quote(n,safe='@/'))
                dl=get_json('https://api.npmjs.org/downloads/point/last-week/'+urllib.parse.quote(n,safe='@/'))
                out['npm']={'name':n,'version':(reg.get('dist-tags') or {}).get('latest'),'weekly_downloads':dl.get('downloads')}
        except Exception:pass
    py=get_text(f'https://raw.githubusercontent.com/{owner}/{name}/{branch}/pyproject.toml')
    m=re.search(r'(?m)^\s*name\s*=\s*["\']([^"\']+)["\']',py or '')
    if m:
        try:
            x=get_json('https://pypi.org/pypi/'+urllib.parse.quote(m.group(1))+'/json');out['pypi']={'name':m.group(1),'version':(x.get('info') or {}).get('version')}
        except Exception:pass
    return out

def build(raw,snaps):
    ps=[]
    for name,r in raw.items():
        stars=int(r.get('stargazers_count',0)); forks=int(r.get('forks_count',0)); watch=int(r.get('subscribers_count',r.get('watchers_count',0)))
        a=past(snaps,name,1); b=past(snaps,name,7); c=past(snaps,name,30)
        s1=a.get('stars') if a else None;s7=b.get('stars') if b else None;s30=c.get('stars') if c else None
        ps.append({'full_name':name,'name':r.get('name'),'owner':(r.get('owner') or {}).get('login'),'html_url':r.get('html_url'),'description':r.get('description') or '', 'homepage':r.get('homepage'),'stars':stars,'forks':forks,'watchers':watch,'open_issues':int(r.get('open_issues_count',0)),'language':r.get('language'),'license':(r.get('license') or {}).get('spdx_id'),'topics':r.get('topics') or [],'size_kb':int(r.get('size',0)),'default_branch':r.get('default_branch'),'created_at':r.get('created_at'),'updated_at':r.get('updated_at'),'pushed_at':r.get('pushed_at'),'archived':bool(r.get('archived')),'fork':bool(r.get('fork')),'category':category(r),'stars_1d_delta':None if s1 is None else stars-s1,'stars_7d_delta':None if s7 is None else stars-s7,'stars_30d_delta':None if s30 is None else stars-s30,'stars_1d_growth_pct':pct(stars,s1),'stars_7d_growth_pct':pct(stars,s7),'stars_30d_growth_pct':pct(stars,s30),'discovery':['github-search']+(['github-topic:dsh-plugin'] if 'dsh-plugin' in r.get('topics',[]) else []),'packages':None})
    return ps

def ln(v,m):return 0 if v is None or v<=0 or m<=0 else math.log1p(v)/math.log1p(m)

def rank(ps):
    mx=max([p['stars'] for p in ps] or [1]); gains=[max(0,p['stars_7d_delta']) for p in ps if p['stars_7d_delta'] is not None];mg=max(gains or [1])
    for p in ps:
        sc=ln(p['stars'],mx)
        if p['stars_7d_delta'] is not None and gains:sc=.70*sc+.30*ln(max(0,p['stars_7d_delta']),mg)
        p['popularity_score']=round(sc*100,2)
        d=max(0,p['stars_7d_delta'] or 0);g=min(max(0,p['stars_7d_growth_pct'] or 0),500)/500
        p['trending_score']=round((.65*ln(d,mg)+.35*g)*100,2)
        p['rising_score']=round(p['trending_score']/(1+.08*math.log10(max(p['stars'],1))),2)
    return ps

def table(items):
    rows=[]
    for i,p in enumerate(items[:10],1):
        g=p['stars_7d_growth_pct']; gt='—' if g is None else f'{g:+.1f}%'; d=re.sub(r'\s+',' ',p['description']).strip();d=(d[:85]+'...') if len(d)>88 else d
        rows.append(f"| {i} | [{p['full_name']}]({p['html_url']}) | {p['stars']:,} | {gt} | {d or '—'} |")
    return '| Rank | Project | Stars | 7d Growth | Description |\n|---:|---|---:|---:|---|\n'+'\n'.join(rows) if rows else '_No data yet._'

def write_readme(ps):
    sets={'POPULAR':sorted(ps,key=lambda p:(-p['popularity_score'],-p['stars'],p['full_name'])),'TRENDING':sorted(ps,key=lambda p:(-p['trending_score'],-(p['stars_7d_delta'] or -1),-p['stars'])),'RISING':sorted(ps,key=lambda p:(-p['rising_score'],-(p['stars_7d_delta'] or -1),p['stars']))}
    text=README.read_text()
    for key,items in sets.items():
        text,n=re.subn(rf'(<!-- {key}_START -->)(.*?)(<!-- {key}_END -->)',rf'\1\n{table(items)}\n\3',text,flags=re.S)
        if not n:raise RuntimeError('missing README marker '+key)
    README.write_text(text)

def save(ps):
    today=dt.date.today().isoformat();now=dt.datetime.now(dt.timezone.utc).isoformat();HISTORY.mkdir(exist_ok=True)
    snap={'date':today,'generated_at':now,'projects':{p['full_name']:{'stars':p['stars'],'forks':p['forks'],'watchers':p['watchers'],'updated_at':p['updated_at'],'pushed_at':p['pushed_at']} for p in ps}}
    (HISTORY/f'{today}.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n')
    (DATA/'projects.json').write_text(json.dumps({'generated_at':now,'schema_version':2,'projects':ps},ensure_ascii=False,indent=2)+'\n')

def main():
    print('1/6 Discovering...');raw=discover();print(' candidates:',len(raw))
    snaps=snapshots();print('2/6 Historical snapshots:',len(snaps))
    ps=rank(build(raw,snaps))
    print('3/6 Package metadata for top 200 by stars...')
    for p in sorted(ps,key=lambda x:-x['stars'])[:200]:
        try:p['packages']=packages(raw[p['full_name']])
        except Exception:p['packages']={'npm':None,'pypi':None}
    print('4/6 Saving snapshot');save(ps)
    print('5/6 Updating README');write_readme(ps)
    print('6/6 Done:',len(ps),'projects')
    for i,p in enumerate(sorted(ps,key=lambda x:(-x['popularity_score'],-x['stars']))[:10],1):print(f"{i:2}. {p['full_name']:<48} stars={p['stars']:<6} score={p['popularity_score']}")
if __name__=='__main__':main()
