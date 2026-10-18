# What was exercised

English · [Português](validation.md) · [Back](../README.en.md)

The test sends real API requests with a unique marker, finds their records in Loki and queries the marker through Grafana. Both the valid request and expected 404 follow Gunicorn stdout → Kubernetes logs API → Alloy → Loki → Grafana. PostgreSQL collection is checked through a `RAISE LOG` message without changing its data.

Checks also cover labels, keeping the marker out of labels, the four-panel dashboard and preservation of the Prometheus datasource and metrics dashboard. Loki Pod replacement verifies earlier records and the same PVC. Authorization checks allow application logs in notes-lab while denying Secrets and monitoring-lab logs.

The [local evidence](../evidence/local-results.json) records UTC time, versions, marker and passed checks. CI repeats the test in a fresh cluster using fixed revisions of Kubernetes and monitoring-lab. It does not install Argo CD; the local test uses the existing cluster where Argo CD is already present.

The 24-hour retention setting has not been verified through a day-long test. Node loss, backup restore, load, extended outages, protection against cluster administrators and lossless/exactly-once delivery were not tested. Logs remain on local storage with one replica. The test does not push log lines directly to Loki's ingestion API.

All **16 checks passed locally and in [GitHub Actions](https://github.com/tommmdl/logging-lab/actions/runs/39127209979)**. See the [CI results](../evidence/ci-results.json) and [tested revision](../evidence/ci-run.json). Later documentation and evidence commits do not change the tested code.

All four panel queries were also executed through Grafana: [results](../evidence/dashboard-queries.json). The [local snapshot](../evidence/local-state.json) records healthy Argo CD state and two API replicas.
