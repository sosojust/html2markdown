#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)" || true
fi
conda activate md
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
