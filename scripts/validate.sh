#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
loki=$(python3 -c 'import json; print(json.load(open("config/images.json"))["loki"]["pinned"])')
alloy=$(python3 -c 'import json; print(json.load(open("config/images.json"))["alloy"]["pinned"])')
docker run --rm --volume "$PWD/config:/etc/loki:ro" "$loki" -config.file=/etc/loki/loki.yaml -verify-config=true
docker run --rm --volume "$PWD/config:/etc/alloy:ro" "$alloy" validate /etc/alloy/config.alloy
bash scripts/k.sh kustomize . > /dev/null
