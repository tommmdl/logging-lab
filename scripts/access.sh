#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
case "${1:-grafana}" in
  grafana) exec bash scripts/k.sh -n monitoring-lab port-forward --address 127.0.0.1 service/grafana 8008:3000 ;;
  loki) exec bash scripts/k.sh port-forward --address 127.0.0.1 service/loki 8009:3100 ;;
  *) echo 'Use: bash scripts/access.sh grafana|loki' >&2; exit 1 ;;
esac
