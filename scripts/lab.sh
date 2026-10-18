#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
case "${1:-status}" in
  up)
    bash scripts/k.sh -n notes-lab get deployment notes-api >/dev/null
    bash scripts/k.sh -n monitoring-lab get deployment grafana >/dev/null
    bash scripts/k.sh apply -f manifests/namespace.yaml
    # RBAC spans two namespaces; do not put it under namespace-transforming Kustomize.
    bash scripts/k.sh -n notes-lab apply -f manifests/rbac.yaml
    bash scripts/k.sh apply -k .
    for name in loki alloy; do
      bash scripts/k.sh rollout status "deployment/$name" --timeout=240s
    done
    python3 scripts/grafana.py apply
    ;;
  status) bash scripts/k.sh get deployments,pods,services,pvc ;;
  down)
    python3 scripts/grafana.py remove
    bash scripts/k.sh -n notes-lab delete -f manifests/rbac.yaml --ignore-not-found
    bash scripts/k.sh delete namespace logging-lab --ignore-not-found
    ;;
  *) echo 'Use: bash scripts/lab.sh up|status|down' >&2; exit 1 ;;
esac
