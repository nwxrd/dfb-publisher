#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f .venv/bin/activate ]]; then
  echo "Ejecute scripts/setup.sh primero."
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH=src
exec python -m dfb_publisher "$@"
