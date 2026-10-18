#!/usr/bin/env python3
"""Follow application access logs into Loki and Grafana, then restart Loki."""
import json
import sys
import time
import urllib.error
import urllib.parse
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from client import ROOT,api,forward,k,obj,password,wait
import fcntl
(ROOT/'.local').mkdir(exist_ok=True)
lock=(ROOT/'.local/verification.lock').open('w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit('Another logging verification is already running in this checkout.')
checks=[]
start=time.time_ns()-60_000_000_000
marker='logging-lab-'+uuid.uuid4().hex
expr='{namespace="notes-lab",app="notes-api"} |= "'+marker+'"'
def check(label,result):
    assert result,label
    checks.append(label);print('OK:',label,flush=True)
def logs(base,expression=expr):
    query=urllib.parse.urlencode({'query':expression,'start':str(time.time_ns()-86_400_000_000_000 if 'notes-db' in expression else start),'end':str(time.time_ns()),'limit':1000,'direction':'forward'})
    result=api(base,'/loki/api/v1/query_range?'+query)
    assert result['status']=='success'
    return result['data']['result']
def lines(streams):return [v[1] for s in streams for v in s['values']]
def access(base,path,expected):
    try:api(base,path)
    except urllib.error.HTTPError as error:
        assert error.code==expected
    else:assert expected==200
with forward('notes-lab','notes-api',80) as app,forward('logging-lab','loki',3100) as loki,forward('monitoring-lab','grafana',3000) as grafana:
    wait(lambda:api(loki,'/ready'))
    # A unique marker in the request path is logged by Gunicorn, not pushed to Loki by this test.
    access(app,'/healthz?trace='+marker,200)
    access(app,'/__logging_missing__/'+marker,404)
    wait(lambda:len(lines(logs(loki)))>=2)
    collected=logs(loki)
    check('Real API requests collected through Alloy',any('/healthz?trace='+marker in line for line in lines(collected)))
    check('Controlled 404 appears in application logs',any('/__logging_missing__/'+marker in line and ' 404 ' in line for line in lines(collected)))
    check('Logs carry namespace, app, pod and container labels',all(s['stream'].get('namespace')=='notes-lab' and s['stream'].get('app')=='notes-api' and s['stream'].get('pod') and s['stream'].get('container') for s in collected))
    check('Marker is not an indexed label',all(marker not in str(s['stream']) for s in collected))
    k('-n','notes-lab','exec','statefulset/postgres','--','psql','-U','lab','-d','notes','-c',"DO $$ BEGIN RAISE LOG '"+marker+"'; END $$;")
    wait(lambda:marker in '\n'.join(lines(logs(loki,'{namespace="notes-lab",app="notes-db"}'))))
    check('PostgreSQL log message also collected',marker in '\n'.join(lines(logs(loki,'{namespace="notes-lab",app="notes-db"}'))))
    auth=password()
    check('Grafana Loki datasource is healthy',api(grafana,'/api/datasources/uid/logging-loki/health',auth=auth)['status']=='OK')
    now=int(time.time()*1000)
    result=api(grafana,'/api/ds/query','POST',{'from':str(now-60000),'to':str(now),'queries':[{'refId':'A','datasource':{'type':'loki','uid':'logging-loki'},'expr':expr,'queryType':'range','maxLines':100}]},auth)['results']['A']
    check('Grafana query returns the request marker',not result.get('error') and marker in json.dumps(result.get('frames',[])))
    check('Logging dashboard contains four panels',len(api(grafana,'/api/dashboards/uid/notes-logs',auth=auth)['dashboard']['panels'])==4)
    check('Existing Prometheus datasource remains healthy',api(grafana,'/api/datasources/uid/prometheus/health',auth=auth)['status']=='OK')
    check('Existing metrics dashboard remains present',api(grafana,'/api/dashboards/uid/notes-monitoring',auth=auth)['dashboard']['uid']=='notes-monitoring')
claim=obj('get','pvc','loki-data')['metadata']['uid']
old_pods={p['metadata']['uid'] for p in obj('get','pods','-l','app=loki')['items']}
k('rollout','restart','deployment/loki')
k('rollout','status','deployment/loki','--timeout=240s')
with forward('logging-lab','loki',3100) as loki:
    wait(lambda:api(loki,'/ready'))
    wait(lambda:marker in '\n'.join(lines(logs(loki))))
    check('Collected logs remain queryable after Loki Pod replacement',marker in '\n'.join(lines(logs(loki))))
    check('Loki PVC identity is preserved',obj('get','pvc','loki-data')['metadata']['uid']==claim)
    check('Loki Pod was actually replaced',not old_pods.intersection(p['metadata']['uid'] for p in obj('get','pods','-l','app=loki')['items']))
# The collector identity may read Pod logs, but not Secrets or other namespaces.
identity='system:serviceaccount:logging-lab:alloy'
check('Collector may read application Pod logs',k('auth','can-i','get','pods/log','-n','notes-lab','--as='+identity).strip()=='yes')
# kubectl auth can-i exits 1 for a denial, so check the return code directly.
import subprocess
for resource,namespace in [('secrets','notes-lab'),('pods/log','monitoring-lab')]:
    response=subprocess.run(['bash',str(ROOT/'scripts/k.sh'),'auth','can-i','get',resource,'-n',namespace,'--as='+identity],capture_output=True,text=True)
    check('Collector denied '+resource+' in '+namespace,response.returncode==1 and response.stdout.strip()=='no')
output={'executed_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'checks_passed':len(checks),'checks':checks,'marker':marker,'versions':json.loads((ROOT/'config/images.json').read_text()),'scope':'API and PostgreSQL stdout/stderr from notes-lab; API discovery and tailing through Alloy; actual Grafana query; Loki Pod replacement with same PVC; no changes to application manifests','final_state':'Loki and Alloy running; existing Grafana metrics datasource and dashboard preserved'}
(ROOT/'.local').mkdir(exist_ok=True)
(ROOT/'.local/verification.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
