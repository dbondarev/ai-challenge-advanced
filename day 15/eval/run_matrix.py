#!/usr/bin/env python3
"""Run the same saved fixtures against enabled profiles. Uses DAY15_TOKEN, never logs it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

p=argparse.ArgumentParser()
p.add_argument('--url',default='http://127.0.0.1:8787')
p.add_argument('--profiles',default='local,cloud')
p.add_argument('--ids',default='')
p.add_argument('--repeat',type=int,default=1)
p.add_argument('--output',default=str(Path(__file__).with_name('matrix-results.json')))
a=p.parse_args()
token=os.environ['DAY15_TOKEN']
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError('redirect rejected')
opener=urllib.request.build_opener(NoRedirect())
def request(path,data=None):
    raw=None if data is None else json.dumps(data).encode()
    req=urllib.request.Request(a.url.rstrip('/')+path,data=raw,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    with opener.open(req,timeout=15) as response: return json.load(response)
profiles=request('/v1/profiles')['profiles']
fixtures=json.loads(Path(__file__).with_name('attacks.json').read_text())
rows=[]
for profile in a.profiles.split(','):
    if not profiles.get(profile,{}).get('enabled'):
        rows.append({'profile':profile,'status':'not_configured'});continue
    for fixture in fixtures:
        if a.ids and fixture['id'] not in a.ids.split(','):continue
        for repetition in range(max(1,min(10,a.repeat))):
            request('/v1/reset',{})
            payload={k:v for k,v in fixture.items() if k!='id'}
            payload['profile']=profile
            job=request('/v1/run',payload)
            deadline=time.monotonic()+1000
            while time.monotonic()<deadline:
                result=request(job['poll'])
                if result['status'] in ('done','error'):break
                time.sleep(3)
            else: raise TimeoutError('job deadline exceeded')
            row={'attack_id':fixture['id'],'profile':profile,'repeat':repetition,
                 'payload_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),'job':result}
            rows.append(row)
            Path(a.output).write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({'id':fixture['id'],'profile':profile,'job_id':job['job_id'],
                  'status':result['status'],'deployed':result.get('result',{}).get('deployed')}),flush=True)
Path(a.output).write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
