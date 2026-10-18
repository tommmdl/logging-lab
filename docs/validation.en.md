# What was exercised

English · [Português](validation.md) · [Back](../README.en.md)

The test sends real API requests with a unique marker, finds their records in Loki and queries the marker through Grafana. Both the valid request and expected 404 follow Gunicorn stdout → Kubernetes logs API → Alloy → Loki → Grafana. PostgreSQL collection is checked through a `RAISE LOG` message without changing its data.

Checks also cover labels, keeping the marker out of labels, the four-panel dashboard and preservation of the Prometheus datasource and metrics dashboard. Loki Pod replacement verifies earlier records and the same PVC. Authorization checks allow application logs in notes-lab while denying Secrets and monitoring-lab logs.

The [local evidence](../evidence/local-results.json) records UTC time, versions, marker and passed checks. CI repeats the test in a fresh cluster using fixed revisions of Kubernetes and monitoring-lab. It does not install Argo CD; the local test uses the existing cluster where Argo CD is already present.

The 24-hour retention setting has not been verified through a day-long test. Node loss, backup restore, load, extended outages, protection against cluster administrators and lossless/exactly-once delivery were not tested. Logs remain on local storage with one replica. The test does not push log lines directly to Loki's ingestion API.

The GitHub Actions result will be recorded after the first run.
