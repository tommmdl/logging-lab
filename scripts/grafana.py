#!/usr/bin/env python3
import json
import sys
from client import ROOT,api,forward,optional,password
with forward('monitoring-lab','grafana',3000) as base:
    auth=password()
    source=json.loads((ROOT/'grafana/datasource.json').read_text())
    dashboard=json.loads((ROOT/'grafana/dashboard.json').read_text())
    existing=optional(base,'/api/datasources/uid/logging-loki',auth)
    saved=optional(base,'/api/dashboards/uid/notes-logs',auth)
    if existing and (existing['type']!='loki' or existing['name']!=source['name']):
        raise SystemExit('Datasource UID belongs to another resource; refusing to overwrite it.')
    if saved and 'logging-lab' not in saved['dashboard'].get('tags',[]):
        raise SystemExit('Dashboard UID belongs to another resource; refusing to overwrite it.')
    if sys.argv[1]=='apply':
        api(base,'/api/datasources/uid/logging-loki' if existing else '/api/datasources','PUT' if existing else 'POST',source,auth)
        if not optional(base,'/api/folders/logging-lab',auth):
            api(base,'/api/folders','POST',{'uid':'logging-lab','title':'Logging Labs'},auth)
        api(base,'/api/dashboards/db','POST',{'dashboard':dashboard,'folderUid':'logging-lab','overwrite':True},auth)
        print('Loki datasource and notes logs dashboard applied; Prometheus configuration preserved.')
    elif sys.argv[1]=='remove':
        if saved:api(base,'/api/dashboards/uid/notes-logs','DELETE',auth=auth)
        if existing:api(base,'/api/datasources/uid/logging-loki','DELETE',auth=auth)
        print('Logging datasource and dashboard removed. Shared Grafana and folder kept.')
    else:raise SystemExit('Use: python3 scripts/grafana.py apply|remove')
