#!/usr/bin/env python3
import datetime as dt
import json, os, time, urllib.request, urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOKEN=os.environ.get('GITHUB_TOKEN','')
if not TOKEN: raise RuntimeError('GITHUB_TOKEN is required')
URL='https://api.github.com/graphql'
HEADERS={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json','Accept':'application/vnd.github+json','User-Agent':'awesome-deepseek-harness-ranking'}
BATCH_SIZE=50

def gql(query):
    req=urllib.request.Request(URL,data=json.dumps({'query':query}).encode(),headers=HEADERS,method='POST')
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req,timeout=45) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body=e.read().decode(errors='replace')
            if e.code in (403,429) and attempt<4:
                wait=min(5*(2**attempt),60); print(f'HTTP {e.code}; retry in {wait}s',flush=True); time.sleep(wait); continue
            raise RuntimeError(f'GraphQL HTTP {e.code}: {body[:500]}') from e

def snapshots():
    d=ROOT/'data/history'
    if not d.exists(): return []
    out=[]
    for p in sorted(d.glob('*.json')):
        try: out.append(json.loads(p.read_text()))
        except Exception: pass
    return out

def prior(ss,name,days):
    target=dt.date.today()-dt.timedelta(days=days); cand=[]
    for s in ss:
        try: day=dt.date.fromisoformat(s['date'])
        except Exception: continue
        item=s.get('projects',{}).get(name)
        if item: cand.append((abs((day-target).days),item))
    if not cand: return None
    cand.sort(key=lambda x:x[0]); dist,item=cand[0]
    if days==3: return item if dist<=1 else None
    return item if dist<=max(2,days//2) else None

def gain(now,before): return None if not before else now-before.get('stars',0)
def growth(now,before):
    if not before or before.get('stars',0)<=0: return None
    return (now-before['stars'])/before['stars']*100

def pctile(vals,x): return 0 if not vals else sum(v<=x for v in vals)/len(vals)

def batch_query(batch):
    blocks=[]
    for i,e in enumerate(batch):
        owner,name=e['full_name'].split('/',1)
        blocks.append(f'''r{i}: repository(owner:{json.dumps(owner)}, name:{json.dumps(name)}) {{
          nameWithOwner url description stargazerCount forkCount pushedAt updatedAt createdAt isArchived isFork
          watchers {{ totalCount }} issues(states:OPEN) {{ totalCount }}
          primaryLanguage {{ name }} licenseInfo {{ spdxId }}
          repositoryTopics(first:20) {{ nodes {{ topic {{ name }} }} }}
        }}''')
    return 'query {\n'+'\n'.join(blocks)+'\nrateLimit { cost remaining resetAt }\n}'

def fetch(pool):
    allp=[]; failures=[]; total=(len(pool)+BATCH_SIZE-1)//BATCH_SIZE
    print(f'[1/4] GraphQL: {len(pool)} repos, {total} batches of {BATCH_SIZE}',flush=True)
    for b in range(total):
        chunk=pool[b*BATCH_SIZE:(b+1)*BATCH_SIZE]
        payload=gql(batch_query(chunk)); data=payload.get('data') or {}
        for i,e in enumerate(chunk):
            r=data.get(f'r{i}')
            if not r:
                failures.append({'repo':e['full_name'],'error':'not returned by GraphQL'}); continue
            topics=[]
            for n in (r.get('repositoryTopics') or {}).get('nodes') or []:
                t=((n or {}).get('topic') or {}).get('name')
                if t: topics.append(t)
            allp.append({'full_name':r.get('nameWithOwner') or e['full_name'],'html_url':r.get('url'),'description':r.get('description') or '',
                         'stars':int(r.get('stargazerCount') or 0),'forks':int(r.get('forkCount') or 0),
                         'watchers':int((r.get('watchers') or {}).get('totalCount') or 0),'open_issues':int((r.get('issues') or {}).get('totalCount') or 0),
                         'language':(r.get('primaryLanguage') or {}).get('name'),'license':(r.get('licenseInfo') or {}).get('spdxId'),
                         'created_at':r.get('createdAt'),'updated_at':r.get('updatedAt'),'pushed_at':r.get('pushedAt'),'topics':topics,
                         'archived':bool(r.get('isArchived')),'fork':bool(r.get('isFork')),'sources':e.get('sources',[]),'first_seen':e.get('first_seen')})
        rate=data.get('rateLimit') or {}; rem=rate.get('remaining')
        print(f"  batch {b+1}/{total}: fetched={len(allp)} failures={len(failures)} cost={rate.get('cost')} remaining={rem}",flush=True)
        if rem is not None and rem<50: raise RuntimeError(f"GraphQL quota low: remaining={rem}, resetAt={rate.get('resetAt')}")
        time.sleep(.15)
    return allp,failures

def main():
    pool=json.loads((ROOT/'data/repositories.json').read_text()).get('repositories',[])
    ss=snapshots(); projects,failures=fetch(pool)
    print('[2/4] Computing 3d/30d history',flush=True)
    for p in projects:
        p3=prior(ss,p['full_name'],3); p30=prior(ss,p['full_name'],30)
        p['gain_3d']=gain(p['stars'],p3); p['growth_3d']=growth(p['stars'],p3)
        p['gain_30d']=gain(p['stars'],p30); p['growth_30d']=growth(p['stars'],p30)
    print('[3/4] Computing star-first popularity',flush=True)
    stars=sorted(p['stars'] for p in projects); gains=sorted(max(p.get('gain_3d') or 0,0) for p in projects); grows=sorted(max(p.get('growth_3d') or 0,0) for p in projects)
    has3=any(p.get('gain_3d') is not None for p in projects)
    for p in projects:
        s=pctile(stars,p['stars'])
        if has3:
            g=pctile(gains,max(p.get('gain_3d') or 0,0)); r=pctile(grows,max(p.get('growth_3d') or 0,0)); score=.70*s+.20*g+.10*r
        else: score=s
        p['popularity_score']=round(score*100,2)
    print('[4/4] Saving projects + daily snapshot',flush=True)
    data=ROOT/'data'; hist=data/'history'; hist.mkdir(parents=True,exist_ok=True)
    now=dt.datetime.now(dt.timezone.utc).isoformat(); today=dt.date.today().isoformat()
    (data/'projects.json').write_text(json.dumps({'generated_at':now,'collector':'github-graphql','batch_size':BATCH_SIZE,'projects':projects,'failures':failures},ensure_ascii=False,indent=2)+'\n')
    snap={'date':today,'generated_at':now,'projects':{p['full_name']:{'stars':p['stars'],'forks':p['forks']} for p in projects}}
    (hist/f'{today}.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n')
    print(f'Done: {len(projects)} updated, {len(failures)} failures',flush=True)
if __name__=='__main__': main()
