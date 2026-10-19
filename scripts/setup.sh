#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo
echo "Listo. Copie .env.example a .env y config/settings.example.toml a config/settings.toml"
